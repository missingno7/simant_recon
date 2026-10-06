"""Original stack mutation/AX controls and the reviewed nominal coverage guard.

No image/source mutation. Unrelated inventory metadata and unrelated storage
owners do not participate. Source, alias, Open-root or registration changes in
this proof's subgraph require review rather than silently extending its domain.
"""
from pathlib import Path
from types import SimpleNamespace
import hashlib
import importlib.util
import json
import re
import struct
import sys

sys.dont_write_bytecode = True
ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'src/program.json').is_file())
FACTS = Path(__file__).with_name('stack-facts.json')
CODE_ROOTS = {
    'win_Open', 'win_Close', 'win_Swap', 'win_DoProxMenu', 'f_20E8_0725',
    'f_20E8_0776', 'f_1E57_0043', 'f_1E57_00B1', 'f_1E57_0052', 'clip_KillWin',
    'win_SetWinDrawHook', 'f_20E8_088B', 'f_20E8_089F', 'f_20E8_08B3',
    'f_20E8_08C7', 'f_20E8_08DB', 'f_20E8_08EF', 'win_LoadWindow',
    'win_LoadAllWindows', 'win_IsWinOpen', 'win_Recalc', 'f_2505_0006',
    'ShowIntro', 'LoadGame', 'MenuQuit', 'o15_384C_0239', 'NewGame',
    'f_22BF_0A65', 'o26_39C7_0000', 'SetMapPlane', 'UpdateEdit', 'clip_Off',
    'IBMInitStuff', 'initStuff', 'o19_384C_0000', 'ProcMenu',
    'f_00F8_01BE', 'f_00F8_017D', 'myButton',
}
STATE_ROOTS = {'g_5702', 'win_handles', 'g_62E0', 'g_62E4', 'g_62E8',
               'g_62EC', 'g_62F0', 'g_62F4'}
OPEN_ROOTS = {'win_Open', 'win_Swap', 'win_DoProxMenu', 'f_20E8_0725'}


def coverage_snapshot(root=ROOT, source_overrides=None, symbols_override=None,
                      program_aliases_override=None):
    """Collect only the reviewed subgraph; overrides support in-memory negatives."""
    source_overrides = source_overrides or {}
    registry = symbols_override if symbols_override is not None else json.loads(
        (root / 'layout/symbols.json').read_text())['code']
    relevant = set(CODE_ROOTS)
    while True:
        added = {n for n, row in registry.items() if row.get('alias_of') in relevant}
        if added <= relevant:
            break
        relevant |= added
    code_subset = {n: {k: registry[n][k] for k in ('unit', 'seg', 'off', 'alias_of')
                      if k in registry[n]} for n in sorted(relevant) if n in registry}
    aliases = program_aliases_override if program_aliases_override is not None else json.loads(
        (root / 'src/program.json').read_text())['aliases']
    program_subset = sorted(({k: row[k] for k in ('alias', 'target', 'offset', 'kind')
                              if k in row} for row in aliases
                             if row.get('target', '').lstrip('_@') in relevant or
                             row.get('alias', '').lstrip('_@') in relevant),
                            key=lambda row: row['alias'])
    tokens = relevant | STATE_ROOTS
    token_rx = re.compile(r'\b(?:' + '|'.join(re.escape(n) for n in sorted(tokens)) + r')\b')
    names = {n for n, row in registry.items()
             if n in OPEN_ROOTS or row.get('alias_of') in OPEN_ROOTS}
    call_rx = re.compile(r'\b(' + '|'.join(re.escape(n) for n in sorted(names)) + r')\s*\(([^()]*)\)')
    sources = {p.relative_to(root).as_posix(): p.read_bytes() for p in (root / 'src').rglob('*')
               if p.suffix.lower() in ('.c', '.asm')}
    sources.update({p: text.encode() if isinstance(text, str) else text
                    for p, text in source_overrides.items()})
    pins, calls = [], []
    for path, raw in sorted(sources.items()):
        text = raw.decode()
        if token_rx.search(text):
            pins.append({'path': path, 'sha256': hashlib.sha256(raw).hexdigest()})
        for number, line in enumerate(text.splitlines(), 1):
            if re.match(r'\s*(extern|void|int|char)\b', line):
                continue
            for match in call_rx.finditer(line):
                name, args = match.groups()
                calls.append([path, number, name, args.split(',')[0].strip()])
    return {'source_pins': pins, 'code_alias_subset': code_subset,
            'program_alias_subset': program_subset, 'open_root_calls': calls}


def active_bound(facts):
    possible = set(facts['possible_open_ids'])
    pair = set(facts['noncoexisting_pair'])
    if len(pair) != 2 or not pair <= possible:
        raise ValueError('reviewed lifetime exclusion is absent')
    bound = len(possible) - 1
    if bound > 31:
        raise ValueError('open destination bound permits stack truncation')
    return bound


def validate_coverage(facts=None, **overrides):
    facts = facts or json.loads(FACTS.read_text())
    observed = coverage_snapshot(**overrides)
    if observed != facts['coverage']:
        changed = [k for k in observed if observed[k] != facts['coverage'].get(k)]
        raise ValueError('window stack coverage changed: ' + ', '.join(changed))
    return active_bound(facts)


def run_controls(facts=None):
    facts = facts or json.loads(FACTS.read_text())
    validate_coverage(facts)
    sys.path.insert(0, str(ROOT / 'tools'))
    import behavior as b
    import exe
    import functions
    image = exe.load()
    if image.sha256 != facts['original_image_sha256']:
        raise ValueError('oracle identity changed')
    vectors = {exe.MANAGER_SEG * 16 + v.offset: v for v in image.vectors}
    for row in facts['resource_pins']:
        if hashlib.sha256((ROOT / row['path']).read_bytes()).hexdigest() != row['sha256']:
            raise ValueError('shipped resource identity changed: ' + row['path'])
    decoder_path = ROOT / 'evidence/canonical/audio-track-owner/shipped_domain.py'
    spec = importlib.util.spec_from_file_location('stack_shipped_decoder', decoder_path)
    decoder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(decoder)
    _, resources = decoder.parse_records('HCEGANT')
    windows = [r for r in resources if r['kind'] == 0 and 0 <= r['id'] < 128]
    assert sorted(r['id'] for r in windows) == list(range(34))
    assert all(not struct.unpack_from('<H', r['payload'], 28)[0] & 0x200 for r in windows)
    stack = 0x55B3 * 16 + 0x5702
    rows = []
    for count in (0, 1, 2, 30, 31):
        entries = [i << 8 for i in range(count)]
        arguments = sorted({33 << 8} | ({entries[0], entries[-1]} if entries else set()))
        for name in ('f_1E57_00B1', 'f_1E57_0052', 'clip_KillWin'):
            for win in arguments:
                pair = SimpleNamespace(function=functions.get(name), vectors=vectors)
                machine = b.Machine(pair)

                def copy(m, args):
                    m.write(args[1] * 16 + args[0], m.read(args[3] * 16 + args[2], args[4]))
                    return args[0], args[1]

                machine.run(b.Case('original stack mutation', args=[win], writes=[
                    (stack, b.words(*(entries + [0x8000] + [0x5555] * (31-count)), 0xBEEF))],
                    callbacks={'f_1E57_038E': b.Callback(0, lambda m, a: (0, 0)),
                               '_fmemcpy': b.Callback(5, copy),
                               'WinPrintf': b.Callback(3, lambda m, a: (0, 0))}, return_kind='void'))
                words = list(struct.unpack('<33H', machine.read(stack, 66)))
                end = words.index(0x8000) if 0x8000 in words else None
                active = words[:end] if end is not None else words
                helper_preconditions = name != 'f_1E57_0052' or (count >= 2 and win == entries[0])
                full_new_front = name == 'f_1E57_00B1' and count == 31 and win not in entries
                nominal = helper_preconditions and not full_new_front
                if nominal:
                    if name == 'f_1E57_00B1':
                        expected = ([win] + [v for v in entries if v != win])[:31]
                    elif name == 'f_1E57_0052':
                        expected = [v for v in entries if v != win] + [win]
                    else:
                        expected = [v for v in entries if v != win]
                    assert active == expected and end <= 31 and words[32] == 0xBEEF
                    assert len(active) == len(set(active)) and all(v in entries + [win] for v in active)
                if name == 'f_1E57_0052' and count == 31 and win not in entries:
                    assert end == 32 and words[32] == 0x8000  # excluded caller state overflows
                if name == 'f_1E57_0052' and count == 1 and win == entries[0]:
                    assert end == 0 and words[32] == 0x8000  # excluded last-entry tail traversal
                if full_new_front:
                    assert active == ([win] + entries)[:31] and entries[-1] not in active
                    assert end == 31 and words[32] == 0xBEEF  # lifetime theorem must exclude this truncation
                rows.append({'function': name, 'count': count, 'argument': win,
                             'nominal_preconditions': nominal, 'sentinel_index': end,
                             'following_guard_word': words[32],
                             'dropped_window': entries[-1] if full_new_front else None})
    ax_rows = []
    for opened in (0, 1):
        machine = b.Machine(SimpleNamespace(function=functions.get('UpdateEdit'), vectors=vectors))
        machine.run(b.Case('implicit window0 forwarding', writes=[(0x55B3 * 16 + 0x5742, bytes(12))],
            callbacks={'win_IsWinOpen': b.Callback(0, lambda m, a: (opened, 0)),
                       'clip_SetWin': b.Callback(1, lambda m, a: (0xFFFF, 0)),
                       'f_0250_13A6': b.Callback(0, lambda m, a: (0xFFFF, 0)),
                       'DrawEditGraphs': b.Callback(0, lambda m, a: (0xFFFF, 0))}, return_kind='void'))
        assert machine.reg('ax') == 0
        ax_rows.append({'edit_open': opened, 'AX': machine.reg('ax')})
    resident = image.sections[27]
    table = 0x4E4B * 16 - resident.load_linear
    overlap = []
    for index in range(308):
        size, count, lo, seg = struct.unpack_from('<4H', resident.data, table + index * 8)
        if not count:
            break
        start = seg * 16 + lo
        if start < stack + 64 and stack < start + size * count:
            overlap.append(index)
    assert index == 307 and not overlap
    return {'passed': True, 'active_bound': active_bound(facts), 'mutations': rows,
            'supported_precondition_count': sum(r['nominal_preconditions'] for r in rows),
            'excluded_precondition_count': sum(not r['nominal_preconditions'] for r in rows),
            'implicit_AX': ax_rows, 'save_record_count': index, 'stack_save_overlap': overlap,
            'shipped_windows': len(windows), 'initially_open_windows': 0,
            'scope': facts['control_scope']}


if __name__ == '__main__':
    print(json.dumps(run_controls(), indent=2))
