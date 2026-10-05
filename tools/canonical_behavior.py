"""Rerun the 29 reviewed DOS contracts against the current canonical program.

python tools/canonical_behavior.py --count 16 --out build/behavior/current

Finite caller domains corroborate the static receipts. Original helpers remain
explicit parametric boundaries; these runs do not prove driver/backend integration.
Every candidate is the complete current TU from src/program.json, compiled and
symbolically linked without source substitution or archived execution code.
"""
from __future__ import annotations

import argparse
from collections import Counter
import itertools
import json
from pathlib import Path
import struct
import sys
import time

ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'layout/functions.json').is_file())
sys.path.insert(0, str(ROOT / 'tools'))
# This also lets the proposed scratch runner exercise its proposed peer modules.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import behavior as b
import canonical
from behavior_ledger import CaseLedger
from behavior_suites import (adlib, dialog, lists, memory, randdirs, render_small,
    small_contracts, spider_nest, text_card, tutorial_menu,
    window_recalc_integration as live_windows, windows)

MEMORY_TARGETS = memory.TARGETS
EFFECTS = ['declared return', 'observed state/ranges', 'ordered callback arguments',
           'actual IN/OUT', 'union of all nonstack memory writes', 'caller ABI']


def cases_only(rows):
    for row in rows:
        yield row[1] if isinstance(row, tuple) else row


def spread(rows, limit):
    """A deterministic sample spanning a directed corpus, not its prefix."""
    rows = list(rows)
    if len(rows) <= limit:
        return rows
    indices = sorted({i * (len(rows) - 1) // (limit - 1) for i in range(limit)})
    return [rows[i] for i in indices]


def randdir_cases(count, seed, full):
    if full:
        yield from randdirs.make_cases(random_count=count, random_seed=seed, actual_tile=True)
        return
    # All incoming directions and rot classes with none/all/single/checkerboard
    # neighbors, coincident/axial/diagonal targets and representative modes.
    for mode, delta, rot, direction, mask in itertools.product(
            (0, 2), ((0, 0), (4, 0), (-3, 3)), (-1, 0, 1), range(8),
            (0, 0xFF, 1, 0x55)):
        scenario = randdirs._scenario(
            f'directed/m{mode}/delta{delta}/r{rot}/d{direction}/mask{mask:02x}',
            x=64, y=32, a=64 + delta[0], b=32 + delta[1], rot=rot,
            direction=direction, mode=mode, plane=1, from_plane=1,
            from_x=64, from_y=32, previous_x=-100, previous_y=-100,
            movable_mask=mask, seed_group='canonical-directed')
        yield randdirs.to_case(scenario, actual_tile=True)
    yield from randdirs.make_cases(directed=False, random_count=count,
                                  random_seed=seed, actual_tile=True)


def balloon_queue_cases():
    for index in range(6):
        case = render_small._balloon_case(f'queue/visible-index-{index}')
        entries = [(640, 480)] * index + [(80, 80)]
        case.writes.extend([
            (b.symbol_address('fd_50F6_1092'), b.words(index + 1)),
            (b.symbol_address('fd_50F6_04C8'), b''.join(b.words(x, y) for x, y in entries)),
            (b.symbol_address('fd_50F6_04F6'), b.words(0) * (index + 1)),
            (b.symbol_address('fd_50F6_04E6'), b.words(0) * (index + 1)),
            (b.symbol_address('fd_50F6_04A6'), struct.pack('<HH', *render_small.BALLOON_TEXT) * (index + 1)),
        ])
        yield case


def domains(count, seed, full):
    """Target -> iterable factory, retaining the reviewed original helper tier."""
    return {
        'f_0250_1018': lambda: render_small.map_cell_cases('f_0250_1018', count, seed),
        'f_0250_129E': lambda: render_small.map_cell_cases('f_0250_129E', count, seed),
        'DrawBalloons': lambda: itertools.chain(render_small.balloon_cases(count, seed), balloon_queue_cases()),
        'SpiderScan': lambda: spider_nest.make_cases('SpiderScan', random_count=count,
            random_seed=seed, original_helpers=('SRand1', 'SRand4', 'fracSIN', 'fracCOS', 'FindAntIndex', 'DeadAntHere')),
        'LessonDone': lambda: tutorial_menu.tutorial_cases(count, seed),
        'FindIndex': lambda: (small_contracts.find_cases(count, seed) if full else
            itertools.chain(spread(small_contracts.find_cases(0, seed), 256),
                            [c for c in small_contracts.find_cases(count, seed) if c.label.startswith(('signed-', 'lookahead/', 'random/'))])),
        'f_1C62_0415': lambda: tutorial_menu.question_cases(count, seed),
        'f_1E57_038E': lambda: itertools.chain([windows.clip_empty_case('empty')],
            windows.clip_live_cases(), windows.randomized_clip_cases(count, seed)),
        'f_20E8_0903': lambda: itertools.chain(windows.coordinate_cases(count, seed),
            live_windows.randomized_cases(max(8, count), seed)),
        'win_UnlockWin': lambda: live_windows.unlock_cases(count, seed),
        'f_23E6_0000': lambda: cases_only(lists.cases(count, seed)),
        'f_2505_0453': lambda: itertools.chain(windows.field_cases(count, seed),
            live_windows.field_cases(max(8, count), seed)),
        'win_DrawBitMap': lambda: render_small.bitmap_cases(count, seed),
        'f_2815_0165': lambda: itertools.chain(adlib.directed_cases(), adlib.random_cases(count, seed)),
        'f_284A_0138': lambda: small_contracts.midi_cases(count, seed),
        'f_29D6_000A': lambda: (small_contracts.tandy_cases(count, seed) if full else (
            small_contracts.tandy_case(f'grid/n{note}/v{vol}/c{chan}', 0x55AA, note, vol, chan)
            for note, vol, chan in itertools.product((0, 1, 11, 12, 59, 60, 61, 119, 126, 127),
                                                      (0, 1, 15, 16, 127, 128, 254, 255), range(3)))),
        'o10_35F5_0384': lambda: tutorial_menu.menu_cases(count, seed),
        'DrawMapCursor': lambda: render_small.map_cursor_cases(count, seed),
        'InvertPatch': lambda: render_small.invert_cases(count, seed),
        'o15_384C_0239': lambda: cases_only(dialog.cases(count, seed)),
        'win_PrintStyleTextInRect': lambda: cases_only(text_card.cases(count, seed)),
        'DisplayCard': lambda: cases_only(text_card.card_cases(count, seed)),
        'drawHistGraph': lambda: cases_only(text_card.history_cases(count, seed)),
        'o25_3BA4_1035': lambda: spider_nest.make_cases('o25_3BA4_1035', random_count=count,
            random_seed=seed, original_helpers=('SRand1', 'SRand4', 'ClearMyLife', 'SetMyLife',
                                                'DigMyTile', 'TryAntTheme', 'SetAlarmDropState')),
        'o25_3BA4_1686': lambda: randdir_cases(count, seed, full),
    }


MUTATIONS = {
    'f_0250_1018': ('if (v > 0x10)', 'if (v >= 0x10)'),
    'f_0250_129E': ('if (g_9126)\n            f_0250_0721', 'if (!g_9126)\n            f_0250_0721'),
    'DrawBalloons': ('wpix = g_19BE * wt;', 'wpix = g_19BE * wt + 1;'),
    'SpiderScan': ('DeadAntHere(x, y, life & 0x80);', '/* negative control: omit corpse */;'),
    'LessonDone': ('case 3:\n        if (fd_50F6_0224 > fd_50F6_0204 && fd_50F6_0AA0 == 0)',
                   'case 3:\n        if (fd_50F6_0224 >= fd_50F6_0204 && fd_50F6_0AA0 == 0)'),
    'FindIndex': ('return fd_50F6_3952;', 'return 0L;'),
    'f_1C62_0415': ('labels[i][0] == c || labels[i][1] == c', 'labels[i][0] == c'),
    'f_1E57_038E': ('win_GetObjRect(win, &r);\n    fd_50F6_3B60[win >> 8]',
                   'win_GetObjRect(win, &r);\n    r.right++;\n    fd_50F6_3B60[win >> 8]'),
    'f_20E8_0903': ('else\n            origin[i] = rect[i] - o[i];',
                   'else\n            origin[i] = rect[(i + 1) & 3] - o[i];'),
    'win_UnlockWin': ('if (--g_8DA6[n] == 0) {', 'if (--g_8DA6[n] == 1) {'),
    'f_23E6_0000': ('s++;\n        n++;', 's++;\n        n += 2;'),
    'f_2505_0453': ('return r[kind];', 'return r[kind] ^ 1;'),
    'win_DrawBitMap': ('f_1B4E_003B(x, y, (char far *)pic + 8);', 'f_1B4E_003B(x, y, (char far *)pic + 9);'),
    'f_2815_0165': ('f_283E_000A(voice + 0xa0, g_6924[note % 12]);',
                   'f_283E_000A(voice + 0xa1, g_6924[note % 12]);'),
    'f_284A_0138': ('return SONG(off) << 8 | SONG(off + 1);', 'return SONG(off + 1) << 8 | SONG(off);'),
    'f_29D6_000A': ('f_29F0_002A(0x205, f >> 4);', 'f_29F0_002A(0x205, (f >> 4) ^ 1);'),
    'o10_35F5_0384': ('k = (k + 1) % nItems;', 'k = (k + 2) % nItems;'),
    'DrawMapCursor': ('fd_50F6_3856 * fd_50F6_0508[0]', 'fd_50F6_3856 * fd_50F6_0508[1]'),
    'InvertPatch': ('h = (h >> 1) + fd_50F6_10D2.left + 4;', 'h = (h >> 1) + fd_50F6_10D2.left + 5;'),
    'o15_384C_0239': ("case 's':\n                result = 1;", "case 's':\n                result = 2;"),
    'win_PrintStyleTextInRect': ('x = rect->left + 1;', 'x = rect->left + 2;'),
    'DisplayCard': ('win_DrawBitMap(pic.left + r.left, pic.top + r.top, pic.id);',
                    'win_DrawBitMap(pic.left + r.left + 1, pic.top + r.top, pic.id);'),
    'drawHistGraph': ('x = n * width / 64 + slot + r.left;', 'x = n * width / 64 + slot + r.left + 1;'),
    'o25_3BA4_1035': ('if (MeLocX > 0x40)', 'if (MeLocX >= 0x40)'),
    'o25_3BA4_1686': ('*rot = 1;', '*rot = -1;'),
    'f_171C_09CC': ('if (b->paras < paras + 0x20)', 'if (b->paras <= paras + 0x20)'),
    'f_171C_0ADC': ('(unsigned long)b + 0x20000L', '(unsigned long)b + 0x30000L'),
    'f_171C_0CF4': ('return (int)moved;', 'return 0;'),
    'f_171C_0FBC': ('return n;', 'return 0L;'),
}


def negative(target, pair, candidates, out):
    mutant = b.PreparedPair(target, out=out / 'negative', mutation=MUTATIONS[target])
    ledger = CaseLedger(out / 'negative-cases.jsonl.gz', mutant, EFFECTS)
    detected = None
    tested = 0
    if target == 'f_1C62_0415':
        # Both versions terminate: the altered hotkey path falls back to a
        # valid queued dialog event, so an execution timeout is not evidence.
        candidates = [tutorial_menu.question_case('negative/second-byte-hotkey',
            b'Question?', 0, [ord('Y')],
            events=[(1, 0x1234, 0x2345, 0x3456, 11, 12, 0x0901, 13)])]
    for case in candidates:
        baseline_pair = prepare_case(target, pair, case)
        original = baseline_pair.compare(case)
        if not original.equal:
            raise AssertionError(f'negative fixture baseline differs: {target}/{case.label}')
        active_pair = prepare_case(target, mutant, case)
        result = active_pair.compare(case)
        ledger.pair = active_pair
        tested += 1
        ledger.record(case, result, lane='directed')
        if not result.equal:
            detected = {'case': case.label, 'mismatch_categories': sorted(result.diff)}
            break
    pin = ledger.finalize()
    if not detected:
        raise AssertionError(f'negative mutation escaped {tested} cases: {target}')
    return {'baseline_matches': True, 'detected': detected, 'cases': tested,
            'identity': mutant.identity, 'ledger': pin, 'execution_errors': 0}


def prepare_case(target, pair, case):
    if target == 'win_DrawBitMap':
        unit = {0: 'S00', 1: 'S01', 2: 'S03'}[case.state['display']]
        if not hasattr(pair, 'driver_pairs'):
            pair.driver_pairs = {}
        if unit not in pair.driver_pairs:
            active = b.PreparedPair(target, mutation=pair.mutation)
            active.original_machine._load_overlay(unit)
            active.candidate_machine._load_overlay(unit)
            pair.driver_pairs[unit] = active
        return pair.driver_pairs[unit]
    if target == 'o15_384C_0239':
        if not hasattr(pair, 'dialog_setup'):
            pair.dialog_setup, proof = dialog._actual_lock_init_writes(pair, case)
            pair.identity['fixture_initializer'] = proof
        case.writes.extend(pair.dialog_setup)
    return pair


def balloon_width_controls(pair, out):
    """Compare allocator argument words before the service body at wide sums.

    These are explicitly entry-boundary observations. Complete normal-size
    executions and all six legal queue indices are checked by the main corpus.
    """
    # Entry hooks are installed on fresh VMs before the allocator has any
    # translated code, keeping this deliberate partial execution independent
    # of the complete-call corpus and Unicorn's existing translation cache.
    pair = b.PreparedPair('DrawBalloons', out=out / 'width-positive')
    mutant = b.PreparedPair('DrawBalloons', out=out / 'width-negative',
        mutation=('(long)(int)(n + 4)', '(long)(n + 4)'))
    address = b.symbol_address('f_171C_1A9E')

    def capture(prepared, case):
        rows = []
        marker = 'intentional allocator-entry observation'
        for side, machine in (('original', prepared.original_machine),
                              ('candidate', prepared.candidate_machine)):
            def hook(cpu, at, size, userdata):
                if at != address:
                    return
                stack = machine.reg('ss') * 16 + machine.reg('sp') + 4
                args = list(struct.unpack('<5H', machine.read(stack, 10)))
                rows.append({'side': side, 'argument_words': args,
                             'size_u32': args[0] | args[1] << 16,
                             'service_body_executed': False})
                machine.error = marker
                cpu.emu_stop()
            handle = machine.cpu.hook_add(b.uc.UC_HOOK_CODE, hook, begin=address, end=address)
            try:
                machine.run(case)
            except b.ExecutionError as exc:
                if marker not in str(exc):
                    raise
            else:
                raise AssertionError('allocator entry observation did not stop')
            finally:
                machine.cpu.hook_del(handle)
        if len(rows) != 2:
            raise AssertionError('missing paired allocator entry')
        return rows

    rows = []
    for index in (0, 4):
        for mode, width, expected_low in ((2, 7280, 0x7FFC), (1, 4096, 0x8004)):
            case = render_small._balloon_case(f'width/index-{index}/sum-{expected_low:04x}',
                mode=mode, plane=0, x=76, y=85, picw=8, pich=1)
            picture_at = (render_small.memory_suite.HEAP_SEG + 2) * 16
            for i, (at, data) in enumerate(case.writes):
                if at == picture_at:
                    case.writes[i] = (at, struct.pack('<hB5sHH', 0, 0, bytes(5), width, 1) + data[12:])
                    break
            if index:
                case.writes.extend([
                    (b.symbol_address('fd_50F6_1092'), b.words(index + 1)),
                    (b.symbol_address('fd_50F6_04C8'), b.words(640, 480) * index + b.words(76, 85)),
                    (b.symbol_address('fd_50F6_04F6'), b.words(0) * (index + 1)),
                    (b.symbol_address('fd_50F6_04E6'), b.words(0) * (index + 1)),
                    (b.symbol_address('fd_50F6_04A6'), struct.pack('<HH', *render_small.BALLOON_TEXT) * (index + 1)),
                ])
            positive, negative = capture(pair, case), capture(mutant, case)
            expected = expected_low if expected_low < 0x8000 else 0xFFFF0000 | expected_low
            if [r['size_u32'] for r in positive] != [expected, expected]:
                raise AssertionError('canonical signed allocation argument differs')
            differs = negative[0]['size_u32'] != negative[1]['size_u32']
            if differs != (expected_low >= 0x8000):
                raise AssertionError('unsigned allocation mutation was not discriminated')
            rows.append({'case': case.label, 'positive': positive, 'unsigned_mutant': negative,
                         'unsigned_mutation_detected': differs})
    result = {'scope': 'allocator entry argument boundary; service body intentionally not executed',
              'positive_identity': pair.identity,
              'negative_identity': mutant.identity, 'observations': rows, 'execution_errors': 0}
    (out / 'width-boundary.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


def run_target(target, make_cases, out, do_negative):
    started = time.monotonic()
    out.mkdir(parents=True, exist_ok=True)
    pair = b.PreparedPair(target, out=out)
    ledger = CaseLedger(out / 'cases.jsonl.gz', pair, EFFECTS)
    row = {'identity': pair.identity, 'cases': 0, 'errors': 0, 'mismatches': 0,
           'actual_helpers': {}, 'modeled_boundaries': {}, 'failures': []}
    actual, modeled = Counter(), Counter()
    for index, case in enumerate(make_cases()):
        case.label = f'{index:06d}/{case.label}'
        try:
            active_pair = prepare_case(target, pair, case)
            result = active_pair.compare(case)
        except Exception as exc:
            row['errors'] += 1
            row['failures'].append({'case': case.label, 'error': repr(exc)})
            break
        row['cases'] += 1
        ledger.pair = active_pair
        ledger.record(case, result, lane='randomized' if case.label.split('/', 1)[-1].startswith(('random', 'seed')) else 'directed')
        for event in result.original['trace']:
            spec = case.callbacks[event['name']]
            (actual if spec.handler is None else modeled)[event['name']] += 1
        if not result.equal:
            row['mismatches'] += 1
            row['failures'].append({'case': case.label, 'diff': result.diff})
            break
    row['ledger'] = ledger.finalize()
    row['actual_helpers'], row['modeled_boundaries'] = dict(actual), dict(modeled)
    if do_negative and not row['failures']:
        try:
            row['negative'] = negative(target, pair, make_cases(), out)
            if target == 'DrawBalloons':
                row['allocation_width'] = balloon_width_controls(pair, out)
        except Exception as exc:
            row['errors'] += 1
            row['failures'].append({'negative_error': repr(exc)})
    row['elapsed_seconds'] = round(time.monotonic() - started, 3)
    row['pass'] = not row['failures'] and row['cases'] > 0
    (out / 'report.json').write_text(json.dumps(row, indent=2) + '\n')
    return row


def sequences(count, seed):
    yield memory.completed_allocation_sequence()
    yield memory.operation_plan('directed/basic', seed=seed)
    for label, kwargs in (
        ('locked', {'soft_lock': 1}), ('pinned', {'pinned': True}),
        ('resize-31', {'resize_delta': 31}), ('resize-32', {'resize_delta': 32}),
        ('resize-33', {'resize_delta': 33}),
        ('alloc-exact', {'allocation_mode': 'exact-fit'}),
        ('alloc-four', {'allocation_mode': 'threshold-plus-four'}),
        ('alloc-five', {'allocation_mode': 'split-plus-five'})):
        yield memory.make_sequence('directed/' + label, seed=seed, **kwargs)
    for i in range(count):
        yield memory.operation_plan(f'random/{seed}/{i}', seed=seed + i + 1, random_case=True)


def run_memory(count, seed, out, do_negative):
    out.mkdir(parents=True, exist_ok=True)
    pair = b.PreparedPair(MEMORY_TARGETS[0], out=out, sequence_targets=MEMORY_TARGETS)
    ledgers = {target: CaseLedger(out / f'{target}-cases.jsonl.gz', memory._StepIdentity(pair, target), EFFECTS)
               for target in MEMORY_TARGETS}
    rows = {target: {'identity': memory._StepIdentity(pair, target).identity,
                    'cases': 0, 'errors': 0, 'mismatches': 0, 'failures': []}
            for target in MEMORY_TARGETS}
    for steps in sequences(count, seed):
        try:
            for (target, case), result in zip(steps, pair.compare_sequence(steps)):
                if target not in rows:
                    if not result.equal:
                        raise AssertionError('original setup/helper differs in live sequence')
                    continue
                row = rows[target]
                row['cases'] += 1
                ledgers[target].record(case, result, lane='randomized' if case.label.startswith('random') else 'directed')
                if not result.equal:
                    row['mismatches'] += 1
                    row['failures'].append({'case': case.label, 'diff': result.diff})
                    break
        except Exception as exc:
            row = rows[target] if target in rows else rows[MEMORY_TARGETS[0]]
            row['errors'] += 1
            row['failures'].append({'error': repr(exc)})
    for target, row in rows.items():
        row['ledger'] = ledgers[target].finalize()
        row['pass'] = not row['failures'] and row['cases'] > 0
        if do_negative and row['pass']:
            try:
                mutant = b.PreparedPair(MEMORY_TARGETS[0], out=out / ('negative-' + target),
                    sequence_targets=MEMORY_TARGETS, mutation=(target, *MUTATIONS[target]))
                detected = None
                for steps in sequences(count, seed):
                    for (called, case), result in zip(steps, mutant.compare_sequence(steps)):
                        if not result.equal:
                            detected = {'case': case.label, 'called': called, 'categories': sorted(result.diff)}
                            break
                    if detected:
                        break
                if not detected:
                    raise AssertionError('live sequence mutation escaped')
                row['negative'] = {'detected': detected, 'identity': mutant.identity, 'execution_errors': 0}
            except Exception as exc:
                row['errors'] += 1
                row['failures'].append({'negative_error': repr(exc)})
                row['pass'] = False
    (out / 'report.json').write_text(json.dumps(rows, indent=2) + '\n')
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--count', type=int, default=16, help='seeded random cases/sequences per domain')
    ap.add_argument('--seed', type=lambda x: int(x, 0), default=0xC0DE29)
    ap.add_argument('--full', action='store_true', help='include complete retained finite enumerations')
    ap.add_argument('--no-negative-controls', action='store_true')
    ap.add_argument('--targets', nargs='+')
    ap.add_argument('--out', type=Path, default=ROOT / 'build/behavior/current')
    args = ap.parse_args()
    out = b.modctx.under_build(args.out)
    out.mkdir(parents=True, exist_ok=True)
    requested = set(args.targets or [r['function'] for r in canonical.load()['semantics']])
    available = domains(args.count, args.seed, args.full)
    if requested - (set(available) | set(MEMORY_TARGETS)):
        ap.error('no live domain for ' + ', '.join(sorted(requested - (set(available) | set(MEMORY_TARGETS)))))
    report = {'schema': 'simant-current-canonical-behavior-v1', 'program_sha256': b.digest(canonical.PROGRAM.read_bytes()),
              'seed': args.seed, 'random_count': args.count, 'full': args.full,
              'live_tools': {str(Path(module.__file__).resolve().relative_to(ROOT)): b.digest(Path(module.__file__).read_bytes())
                  for module in (b, sys.modules[__name__], adlib, dialog, lists, memory, randdirs,
                                 render_small, small_contracts, spider_nest, text_card, tutorial_menu,
                                 live_windows, windows)},
              'scope': 'Finite current caller contracts; same-module non-target entries and actual helpers execute original DOS code. Named modeled boundaries, graphics intent and reviewed CRT cursor projection are explicit. Backend/storage integration remains separate.',
              'targets': {}}
    if requested.intersection(MEMORY_TARGETS):
        print('Running live memory sequences', flush=True)
        report['targets'].update(run_memory(args.count, args.seed, out / 'memory', not args.no_negative_controls))
        for target, row in report['targets'].items():
            print(target, 'PASS' if row['pass'] else 'FAIL', row['cases'], 'cases', flush=True)
    for target, make_cases in available.items():
        if target not in requested:
            continue
        print('Running', target, flush=True)
        try:
            row = run_target(target, make_cases, out / target, not args.no_negative_controls)
        except Exception as exc:
            row = {'pass': False, 'cases': 0, 'errors': 1, 'mismatches': 0, 'failures': [{'error': repr(exc)}]}
        report['targets'][target] = row
        print(target, 'PASS' if row['pass'] else 'FAIL', row['cases'], 'cases', flush=True)
        (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    report['pass'] = all(r['pass'] for r in report['targets'].values()) and requested <= report['targets'].keys()
    report['cases'] = sum(r['cases'] for r in report['targets'].values())
    if report['program_sha256'] != b.digest(canonical.PROGRAM.read_bytes()):
        raise RuntimeError('canonical program changed during behavior run')
    for path, pin in report['live_tools'].items():
        if pin != b.digest((ROOT / path).read_bytes()):
            raise RuntimeError('live harness changed during behavior run: ' + path)
    (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print('PASS' if report['pass'] else 'FAIL', len(report['targets']), 'domains', report['cases'], 'paired cases', flush=True)
    return 0 if report['pass'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
