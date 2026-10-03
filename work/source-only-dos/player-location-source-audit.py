"""Pinned source-only ownership audit for the six point/location words.

Research scratch only. Reads the canonical 127 TUs and the 29 effective
whole-module sources selected by static-completeness/index-v1.json, using the
corrected DrawBalloons audit.source. It does not load original executable or
object bytes and does not edit canonical files.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path
import hashlib
import json
import re
import sys


def find_root() -> Path:
    for candidate in Path(__file__).resolve().parents:
        if (candidate / 'layout/manifest.json').is_file():
            return candidate
    raise RuntimeError('cannot locate repository root')


ROOT = find_root()
OUT = ROOT / 'build/workers/dos_player_location_owners/runtime-v2'
OUT.mkdir(parents=True, exist_ok=True)
NAMES = ('MeLocX', 'MeLocY', 'MePlane', 'RedLocX', 'RedLocY', 'RedPlane')
EXPECTED_ALIASES = {'MeLocX': 'fd_50F6_047C', 'MeLocY': 'fd_50F6_048A',
                    'MePlane': 'fd_50F6_048C'}
SAVE_PATH = 'src/S09/m35F5.c'
FRAME = 0x50F6
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / 'tools'))
import source_only_dos as dos  # noqa: E402


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def pin(path: Path, expected: str | None = None):
    raw = path.read_bytes()
    digest = sha(raw)
    if expected is not None and digest != expected:
        raise RuntimeError(f'hash drift: {path}: {digest} != {expected}')
    if digest == dos.ORIGINAL_SHA:
        raise RuntimeError(f'original executable disguised as source: {path}')
    try:
        rel = path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        rel = str(path.resolve()).replace('\\', '/')
    return raw, {'path': rel, 'sha256': digest, 'size': len(raw)}


def visible_lines(lines: list[str], assembly: bool):
    """Mask comments and literals while preserving line positions and columns."""
    visible = []
    in_block = False
    for line in lines:
        if assembly:
            visible.append(line.split(';', 1)[0])
            continue
        out = []
        i = 0
        quote = None
        escaped = False
        while i < len(line):
            c = line[i]
            nxt = line[i + 1] if i + 1 < len(line) else ''
            if in_block:
                out.append(' ')
                if c == '*' and nxt == '/':
                    out.append(' ')
                    i += 2
                    in_block = False
                    continue
            elif quote:
                out.append(' ')
                if escaped:
                    escaped = False
                elif c == '\\':
                    escaped = True
                elif c == quote:
                    quote = None
            elif c == '/' and nxt == '*':
                out.extend('  ')
                i += 2
                in_block = True
                continue
            elif c == '/' and nxt == '/':
                out.extend(' ' * (len(line) - i))
                break
            elif c in ('"', "'"):
                quote = c
                out.append(' ')
            else:
                out.append(c)
            i += 1
        visible.append(''.join(out))
    return visible


def effective_sources():
    manifest_path = ROOT / 'layout/manifest.json'
    index_path = ROOT / 'work/source-only-dos/static-completeness/index-v1.json'
    manifest_raw, manifest_pin = pin(manifest_path)
    manifest = json.loads(manifest_raw)
    index_raw, index_pin = pin(index_path)
    index = json.loads(index_raw)
    if len(manifest.get('modules', {})) != 127:
        raise RuntimeError('expected exactly 127 canonical modules')
    if index.get('schema') != 'simant-dos-strict-static-index-v1' or len(index.get('entries', {})) != 29:
        raise RuntimeError('expected the reviewed strict 29-entry index')
    rows = []
    receipt_pins = [index_pin]
    for module, item in sorted(manifest['modules'].items()):
        rows.append({'path': item['source'], 'sha256': item['source_sha256'],
                     'role': 'canonical:' + module})
    behavior = []
    for function, ref in sorted(index['entries'].items()):
        receipt_path = ROOT / ref['path']
        receipt_raw, receipt_pin = pin(receipt_path, ref['sha256'])
        receipt_pins.append(receipt_pin)
        receipt = json.loads(receipt_raw)
        source = (receipt.get('audit', {}).get('source', {}) if function == 'DrawBalloons'
                  else receipt.get('registered_source', {}))
        if not source.get('whole_module') or not source.get('path') or not source.get('sha256'):
            raise RuntimeError(f'{function} lacks an effective whole-module source')
        row = {'path': source['path'], 'sha256': source['sha256'],
               'role': 'effective:' + function}
        rows.append(row)
        behavior.append({'function': function, 'path': source['path'],
                         'sha256': source['sha256']})
    merged = {}
    for row in rows:
        old = merged.get(row['path'])
        if old and old['sha256'] != row['sha256']:
            raise RuntimeError('source hash conflict: ' + row['path'])
        if not old:
            merged[row['path']] = {'path': row['path'], 'sha256': row['sha256'], 'roles': []}
        merged[row['path']]['roles'].append(row['role'])
    result = sorted(merged.values(), key=lambda row: row['path'])
    if len(result) != 156:
        raise RuntimeError(f'expected 156 unique canonical/effective source paths, got {len(result)}')
    return manifest, manifest_pin, index_pin, receipt_pins, behavior, result


def classify(path: str, code: str, name: str):
    s = code.strip()
    if re.search(r'\bextern\b', s):
        if re.fullmatch(r'extern\s+int\s+far\s+' + re.escape(name) + r'\s*;', s):
            return 'extern_signed_int_far'
        if (path == SAVE_PATH and re.fullmatch(
                r'extern\s+unsigned\s+char\s+far\s+' + re.escape(name) + r'\s*\[\s*\]\s*;', s)):
            return 'SaveRec_unsigned_byte_far_address_view'
        return 'other_extern_declaration'
    if path == SAVE_PATH and re.fullmatch(
            r'\{\s*2\s*,\s*1\s*,\s*\(void\s+far\s+\*\)\s*&' +
            re.escape(name) + r'\s*\},?', s):
        return 'SaveRec_direct_base_address'
    if re.search(r'(?<!&)&(?!&)\s*' + re.escape(name) + r'\b', s):
        return 'address_escape'
    if re.search(r'\b' + re.escape(name) + r'\s*\[', s):
        return 'aggregate_or_pointer_arithmetic'
    if re.search(r'^\s*' + re.escape(name) +
                 r'\s*(?:\+\+|--|(?:\+=|-=|\*=|/=|%=|&=|\|=|\^=|=(?!=)))', s):
        return 'direct_word_write'
    return 'direct_word_read_or_expression'


def direct_save_rows(lines: list[str]):
    pat = re.compile(r'^\s*\{\s*(\d+)\s*,\s*(\d+)\s*,\s*\(void\s+far\s+\*\)\s*&'
                     r'([A-Za-z_]\w*)\s*\},\s*$')
    found = {name: [] for name in NAMES}
    for no, line in enumerate(lines, 1):
        m = pat.fullmatch(line)
        if m and m.group(3) in found:
            size, count, name = int(m.group(1)), int(m.group(2)), m.group(3)
            found[name].append({'source': SAVE_PATH, 'line': no, 'text': line.strip(),
                                'size': size, 'count': count, 'byte_extent': size * count})
    return found


def main():
    denied_oracle_reads = dos.install_input_guard()
    manifest, manifest_pin, index_pin, receipt_pins, behavior, sources = effective_sources()
    symbols_path = ROOT / 'layout/symbols.json'
    symbols_raw, symbols_pin = pin(symbols_path)
    symbols = json.loads(symbols_raw)['data']
    registry = {}
    name_set = set(NAMES)
    for name in NAMES:
        row = symbols.get(name)
        if not isinstance(row, dict) or row.get('seg') != FRAME:
            raise RuntimeError(name + ' is not registered in FAR_BSS 50F6')
        start = row['off']
        exact = sorted(key for key, value in symbols.items()
                       if isinstance(value, dict) and value.get('seg') == FRAME and value.get('off') == start)
        interiors = sorted((key, value['off']) for key, value in symbols.items()
                           if isinstance(value, dict) and value.get('seg') == FRAME and
                           start < value.get('off', -1) < start + 2)
        declared_aliases = sorted(key for key, value in symbols.items()
                                  if isinstance(value, dict) and value.get('alias_of') == name)
        expected_aliases = [EXPECTED_ALIASES[name]] if name in EXPECTED_ALIASES else []
        if declared_aliases != expected_aliases or interiors:
            raise RuntimeError(f'alias/interior mismatch for {name}: {declared_aliases}, {interiors}')
        expected_exact = sorted([name] + expected_aliases)
        if exact != expected_exact:
            raise RuntimeError(f'unexpected registered same-base names for {name}: {exact}')
        registry[name] = {'segment': f'{FRAME:04X}', 'offset': f'{start:04X}',
                          'extent': 2, 'registered_exact_base_names': exact,
                          'registered_aliases': declared_aliases,
                          'registered_interior_symbols': interiors,
                          'grounding': row.get('grounding')}

    targets = list(NAMES) + [EXPECTED_ALIASES[name] for name in EXPECTED_ALIASES]
    refs = {name: [] for name in targets}
    source_pins = []
    for row in sources:
        path = ROOT / row['path']
        raw, source_pin = pin(path, row['sha256'])
        source_pin['roles'] = row['roles']
        source_pins.append(source_pin)
        lines = raw.decode('latin1').splitlines()
        visible = visible_lines(lines, path.suffix.lower() in ('.asm', '.s'))
        for line_no, (raw_line, code_line) in enumerate(zip(lines, visible), 1):
            for name in targets:
                if re.search(r'(?<![A-Za-z0-9_])' + re.escape(name) + r'(?![A-Za-z0-9_])', code_line):
                    refs[name].append({'source': row['path'], 'line': line_no,
                                       'text': raw_line.strip(), 'category': classify(row['path'], code_line, name),
                                       'roles': row['roles']})

    save_raw, save_pin = pin(ROOT / SAVE_PATH)
    save_lines = save_raw.decode('latin1').splitlines()
    save_rows = direct_save_rows(save_lines)
    for name, rows in save_rows.items():
        if len(rows) != 1 or (rows[0]['size'], rows[0]['count'], rows[0]['byte_extent']) != (2, 1, 2):
            raise RuntimeError(f'{name}: expected exactly one direct 2-byte singleton SaveRec view: {rows}')

    summary = {}
    for name in NAMES:
        cats = Counter(item['category'] for item in refs[name])
        other_extern = [item for item in refs[name] if item['category'] == 'other_extern_declaration']
        escapes = [item for item in refs[name] if item['category'] in
                   ('address_escape', 'aggregate_or_pointer_arithmetic')]
        typed = [item for item in refs[name] if item['category'] == 'extern_signed_int_far']
        if not typed:
            raise RuntimeError(f'{name}: no source-typed signed int far declaration')
        if other_extern or escapes:
            raise RuntimeError(f'{name}: unreviewed declarations/escapes: {other_extern + escapes}')
        if not any(item['category'] == 'SaveRec_direct_base_address' for item in refs[name]):
            raise RuntimeError(f'{name}: the effective-source scan did not see its direct SaveRec address')
        if name.startswith('Red'):
            byte_views = [item for item in refs[name]
                          if item['category'] == 'SaveRec_unsigned_byte_far_address_view']
            if len(byte_views) != 1:
                raise RuntimeError(f'{name}: expected one S09 unsigned-byte SaveRec address view')
        summary[name] = {'line_reference_count': len(refs[name]),
                         'categories': dict(sorted(cats.items())),
                         'references': refs[name],
                         'SaveRec_rows': save_rows[name],
                         'typed_declarations': typed,
                         'signed_storage_type': 'int; MSC 6.00AX int is signed 16-bit under the pinned DOS ABI'}
    for alias in EXPECTED_ALIASES.values():
        for item in refs[alias]:
            if item['category'] not in ('extern_signed_int_far', 'direct_word_read_or_expression',
                                        'direct_word_write', 'SaveRec_direct_base_address'):
                raise RuntimeError(f'unreviewed source alias use: {alias}: {item}')
    for name, alias in EXPECTED_ALIASES.items():
        registry[name]['alias_source_references'] = refs[alias]

    # Save/load is a raw table walk. Preserve the exact source anchors and do
    # not infer behavior for partial reads.
    load_range = function_range(save_lines, 'LoadGame')
    save_range = function_range(save_lines, 'o09_35F5_0188')
    load_code = save_lines[load_range[0]-1:load_range[1]]
    save_code = save_lines[save_range[0]-1:save_range[1]]
    load_calls = [{'line': n, 'text': line.strip()} for n, line in
                  enumerate(load_code, load_range[0]) if 'o09_35F5_0D7A();' in line]
    load_reads = [{'line': n, 'text': line.strip()} for n, line in
                  enumerate(load_code, load_range[0]) if 'read(fd, p->data' in line]
    save_writes = [{'line': n, 'text': line.strip()} for n, line in
                   enumerate(save_code, save_range[0]) if 'write(fd, p->data' in line]
    if len(load_calls) != 1 or len(load_reads) != 1 or len(save_writes) != 1 or load_calls[0]['line'] >= load_reads[0]['line']:
        raise RuntimeError('SaveRec reset/read/write anchors drifted')

    def function_evidence(path: str, name: str):
        raw, _ = pin(ROOT / path)
        lines = raw.decode('latin1').splitlines()
        start, end = function_range(lines, name)
        selected = []
        for number in range(start, end + 1):
            line = lines[number - 1]
            if any(re.search(r'\b' + re.escape(word) + r'\b', line)
                   for word in (*NAMES, *EXPECTED_ALIASES.values())):
                selected.append({'line': number, 'text': line.strip()})
        return {'source': path, 'line_start': start, 'line_end': end,
                'target_state_lines': selected}

    init_sim = function_evidence('src/S08/m35F5.c', 'InitSimVars')
    init_yellow = function_evidence('src/S08/m35F5.c', 'InitYelloAnt')
    set_player_life = function_evidence('src/root/m10F7.c', 'SetMyLife')
    red_step = function_evidence('src/root/m0DEF.c', 'f_0DEF_006B')
    red_direction = function_evidence('src/root/m1383.c', 'GetRedDefendDir')
    if init_sim['target_state_lines']:
        raise RuntimeError('InitSimVars unexpectedly writes or reads one of the six words')

    direct_red_direction_mentions = []
    direct_map_index = []
    for row in sources:
        raw, _ = pin(ROOT / row['path'], row['sha256'])
        lines = raw.decode('latin1').splitlines()
        visible = visible_lines(lines, Path(row['path']).suffix.lower() in ('.asm', '.s'))
        for number, (raw_line, code_line) in enumerate(zip(lines, visible), 1):
            if re.search(r'\bGetRedDefendDir\s*\(', code_line):
                direct_red_direction_mentions.append({'source': row['path'], 'line': number,
                                                       'text': raw_line.strip()})
            if 'MapA[MeLocX][MeLocY]' in code_line:
                direct_map_index.append({'source': row['path'], 'line': number,
                                         'text': raw_line.strip()})
    red_call_sites = [row for row in direct_red_direction_mentions
                      if not re.fullmatch(r'\s*(?:int|void|char|long|unsigned(?:\s+\w+)?)\s+far\s+'
                                          r'GetRedDefendDir\s*\([^;]*\)\s*;?\s*', row['text'])]
    if len(direct_red_direction_mentions) != 1 or red_call_sites:
        raise RuntimeError('GetRedDefendDir textual call inventory changed; review this candidate again')

    root_manifest = {
        'layout_manifest': manifest_pin,
        'symbols_registry': symbols_pin,
        'strict_index': index_pin,
        'strict_receipts': receipt_pins,
        'SaveRec_source': save_pin,
        'source_set': {'canonical_module_count': 127, 'strict_effective_function_count': 29,
                       'unique_source_path_count': len(sources),
                       'corrected_DrawBalloons_selected_from_audit_source': True,
                       'strict_effective_modules': behavior},
        'registry': registry,
        'SaveRec_schema': {'record_type': 'struct SaveRec', 'byte_size': 2,
                           'count': 1, 'data': 'void far *',
                           'load_reset_helper_calls': load_calls,
                           'raw_read_calls': load_reads,
                           'raw_write_calls': save_writes,
                           'all_six_direct_base_views_are_two_byte_singletons': True},
        'lifecycle': {
            'InitSimVars': init_sim,
            'InitYelloAnt': init_yellow,
            'SetMyLife': set_player_life,
            'red_ant_step': red_step,
            'GetRedDefendDir': red_direction,
            'GetRedDefendDir_source_call_sites': red_call_sites,
            'direct_player_map_index_sites': direct_map_index,
            'interpretation': {
                'InitSimVars_does_not_initialize_any_of_the_six': True,
                'MeLocX_MeLocY_and_MePlane_have_other_world_or_action_writers': True,
                'SetMyLife_writes_player_triple_only_after_valid_location_and_nonzero_life': True,
                'Red_triple_is_assigned_from_AlistX_Y_index_and_plane_1_before_red_direction_helper': True,
                'Red_direction_has_no_textual_direct_caller_in_scanned_effective_sources': True,
                'raw_SaveRec_load_can_restore_values_without_per_word_validation': True,
                'unchecked_indices_or_loaded_coordinate_values_are_not_proven_safe': True,
            },
        },
        'members': summary,
        'source_pins': source_pins,
        'source_only_guard': {'denied_oracle_reads': denied_oracle_reads,
                              'original_image_sha256_rejected_by_pin': True},
        'conclusions': {
            'single_two_byte_signed_scalar_candidates': True,
            'no_non_save_address_escape_or_pointer_arithmetic_observed': True,
            'no_registered_interior_symbol_observed': True,
            'source_only_word_owner_does_not_claim_original_COMDEF_TU_order_or_padding': True,
            'coordinate_or_plane_range_safety_proven': False,
            'unchecked_loaded_coordinates_and_indices_remain_outside_scope': True,
        },
    }
    output = OUT / 'player-location-source-audit.json'
    output.write_text(json.dumps(root_manifest, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'output': str(output), 'canonical_modules': 127,
                      'strict_effective_sources': 29, 'unique_source_paths': len(sources),
                      'reference_counts': {name: len(refs[name]) for name in NAMES},
                      'categories': {name: summary[name]['categories'] for name in NAMES},
                      'source_audit_only': True}, indent=2))


def function_range(lines, name):
    pattern = re.compile(r'^\s*(?:int|void|char|long|unsigned(?:\s+\w+)?)\s+far\s+' +
                         re.escape(name) + r'\s*\([^;]*\)\s*$')
    headers = [i for i, line in enumerate(lines) if pattern.fullmatch(line)]
    if len(headers) != 1:
        raise RuntimeError(f'cannot uniquely find {name}: {headers}')
    start = headers[0]
    opening = next((i for i in range(start, len(lines)) if '{' in lines[i]), None)
    if opening is None:
        raise RuntimeError('no body for ' + name)
    depth = 0
    for end in range(opening, len(lines)):
        depth += lines[end].count('{') - lines[end].count('}')
        if depth == 0:
            return start + 1, end + 1
    raise RuntimeError('unterminated function ' + name)


if __name__ == '__main__':
    main()
