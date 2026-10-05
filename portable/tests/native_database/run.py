"""Current canonical native database/resource integration, with no old owner.

Consumes a current conversion report; all target TUs are compiled whole.
Old fixture/parser logic is retained only as independent test logic.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import sys

ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'src/program.json').is_file())
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import index_fixture_logic as fixture_logic
import resource_fixture_logic as resource_logic


def pin(path):
    raw = path.read_bytes()
    return {'path': path.resolve().relative_to(ROOT).as_posix(),
            'sha256': hashlib.sha256(raw).hexdigest(), 'size': len(raw)}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--conversion', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    conversion = (ROOT / args.conversion).resolve()
    out = (ROOT / args.out).resolve()
    if out.exists():
        raise ValueError('refusing to overwrite result directory')
    out.mkdir(parents=True)
    report_path = conversion / 'report.json'
    conversion_report = json.loads(report_path.read_text())
    if (not conversion_report.get('passed') or
            not conversion_report['input_stability']['at_end']):
        raise ValueError('successful stable current native build required')
    for name, expected in conversion_report['input_pins'].items():
        if pin(ROOT / name)['sha256'] != expected:
            raise ValueError('native build input changed: ' + name)
    bykey = {r['module']: r for r in conversion_report['canonical_TUs']}
    native = {r['source']: r for r in conversion_report['native_services']}
    program = json.loads((ROOT / 'src/program.json').read_text())
    canonical = {r['key']: r for r in program['modules']}
    inputs = {report_path, ROOT / 'src/program.json', Path(__file__).resolve(),
              Path(fixture_logic.__file__).resolve(), Path(resource_logic.__file__).resolve(),
              HERE / 'recall_driver.c'}
    commands = []
    base_command = bykey['root:1986']['compile']['command']
    gcc = Path(base_command[0])
    flags = base_command[1:base_command.index('-c')]
    flags += ['-O0', '-ffunction-sections', '-fdata-sections']

    def source(key):
        row = bykey[key]
        if row.get('status') != 'WHOLE_CANONICAL_TU_CONVERTED' or not row['compile']['passed']:
            raise ValueError('requested canonical TU did not convert/compile: ' + key)
        old = canonical[key]
        if row['source'] != old['source'] or pin(ROOT / old['source'])['sha256'] != old['source_sha256']:
            raise ValueError('conversion/current canonical source authority differs: ' + key)
        generated = Path(row['generated'])
        if not generated.resolve().is_relative_to(conversion):
            raise ValueError('generated source outside current conversion')
        inputs.update((ROOT / old['source'], generated))
        return generated

    def service(name):
        row = native[name]
        generated = Path(row['generated'])
        compile_source = row['compile']['command'][row['compile']['command'].index('-c') + 1]
        if (not row['compile']['passed'] or not generated.resolve().is_relative_to(ROOT) or
                Path(compile_source).resolve() != generated.resolve()):
            raise ValueError('native service not compiled/current: ' + name)
        inputs.add(generated)
        return generated

    def command(cmd, label):
        result = subprocess.run([str(x) for x in cmd], cwd=ROOT, capture_output=True, text=True, timeout=45)
        commands.append({'label': label, 'argv': [str(x) for x in cmd], 'returncode': result.returncode,
                         'stdout': result.stdout, 'stderr': result.stderr})
        (out / 'commands.json').write_text(json.dumps(commands, indent=2) + '\n')
        return result

    def compile_sources(paths, label):
        objects = []
        for index, path in enumerate(paths):
            obj = out / f'{label}-{index}.o'
            deps = out / f'{label}-{index}.d'
            result = command([gcc, *flags, '-MMD', '-MF', deps, '-c', path, '-o', obj], label)
            if result.returncode:
                raise ValueError('compile failed: ' + str(path) + '\n' + result.stderr[-5000:])
            dependency_text = deps.read_text().replace('\\\n', '').split(': ', 1)[1]
            for name in dependency_text.split():
                dep = Path(name.replace('\\ ', ' ')).resolve()
                if dep.is_relative_to(ROOT):
                    inputs.add(dep)
            objects.append(obj)
        return objects

    def link(objects, label):
        exe = out / (label + '.exe')
        result = command([gcc, *objects, '-Wl,--gc-sections', '-o', exe], label + '-link')
        if result.returncode:
            raise ValueError('link failed: ' + result.stderr[-6500:])
        return exe

    # Whole canonical module and source-owned storage; no portable state/database.c.
    index_sources = [source(k) for k in ('root:1986', 'source-owned:database-record-state',
                                        'source-owned:database-index-state')]
    driver = HERE / 'index_driver.c'
    traps = HERE / 'index_traps.c'
    inputs.update((driver, traps))
    common_services = [service('portable/' + n) for n in (
        'whole_program/platform/handles.c', 'whole_program/platform/dos_io.c',
        'whole_program/platform/dos_format.c', 'whole_program/platform/dos_memory.c',
        'whole_program/platform/crt_abi.c', 'platform/memory.c',
        'whole_program/algorithms/lzss.c')]
    index_objects = compile_sources(index_sources + common_services + [driver, traps], 'index')
    exe = link(index_objects, 'index')
    datasets, fixture = [], bytearray(struct.pack('<IH', 0x31424457, 3))
    for stem in ('HCEGANT', 'SHARED', 'SOUND'):
        for ext in ('NDX', 'DAT'):
            inputs.add(ROOT / f'assets/{stem}.{ext}')
        count, wire, decoded = fixture_logic.parse_index(ROOT / f'assets/{stem}.NDX')
        queries = fixture_logic.queries(count, decoded)
        datasets.append((stem, count, decoded, queries))
        fixture.extend(struct.pack('<h', count) + b''.join(wire) + struct.pack('<I', len(queries)))
        for ident, kind in queries:
            fixture.extend(struct.pack('<hh', ident, kind))
    fixture_path = out / 'index-fixture.bin'
    fixture_path.write_bytes(fixture)
    ran = command([exe, fixture_path], 'index-run')
    if ran.returncode:
        raise ValueError('index run failed: ' + ran.stderr)
    actual = [tuple(map(int, line.split(','))) for line in ran.stdout.splitlines()]
    at, onepast, reserved_guard_changes = 0, 0, 0
    for di, (stem, count, rows, queries) in enumerate(datasets):
        for qi, (ident, kind) in enumerate(queries):
            got = actual[at]
            at += 1
            rank = fixture_logic.lower_bound(rows, count, ident, kind)
            historical_hit = rows[rank][1:3] == (ident, kind)
            hit = rank < count and historical_hit
            expected_rank = rank if hit else -1
            expected = rows[rank] if hit else (-1, -1, 0, 0)
            home = rows[rank]
            wanted = (di, qi, rank, ident, kind, expected_rank, *expected, rank, *home)
            if got != wanted:
                raise ValueError(f'index comparison mismatch {stem} {ident}/{kind}: {got} != {wanted}')
            onepast += rank == count
            reserved_guard_changes += rank == count and historical_hit
    if at != len(actual):
        raise ValueError('unexpected index output rows')

    # Compare the same complete converted TU without the native guard. Both
    # runners use a fixture-owned reserved row; no out-of-allocation read occurs.
    index_body = index_sources[0].read_text()
    guard = '    if (fd_50F6_3956 == fd_50F6_3958[db].indexHeader.count) return 0L;\n'
    if index_body.count(guard) != 1:
        raise ValueError('native FindIndex guard anchor not unique')
    unguarded = out / 'root_1986-without-native-guard.c'
    unguarded.write_text(index_body.replace(guard, ''))
    old_obj = compile_sources([unguarded], 'unguarded')[0]
    objects = [old_obj, *index_objects[1:]]
    unguarded_exe = link(objects, 'unguarded')
    old_ran = command([unguarded_exe, fixture_path], 'unguarded-asset-index-run')
    if old_ran.returncode:
        raise ValueError('guardless asset index comparison failed')
    guard_asset_differences = [i for i, (a, z) in enumerate(zip(
        ran.stdout.splitlines(), old_ran.stdout.splitlines())) if a != z]
    old_actual = [tuple(map(int, line.split(','))) for line in old_ran.stdout.splitlines()]
    if len(old_actual) != len(actual):
        raise ValueError('guardless asset observation count differs')
    asset_deltas = []
    cursor = 0
    for di, (stem, count, rows, queries) in enumerate(datasets):
        for qi, (ident, kind) in enumerate(queries):
            rank = fixture_logic.lower_bound(rows, count, ident, kind)
            hit = rows[rank][1:3] == (ident, kind)
            returned = rows[rank] if hit else (-1, -1, 0, 0)
            wanted = (di, qi, rank, ident, kind, rank if hit else -1, *returned, rank, *rows[rank])
            if old_actual[cursor] != wanted:
                raise ValueError('guardless source differs from original-predicate fixture expectation')
            if cursor in guard_asset_differences:
                asset_deltas.append({'database': stem, 'query_id': ident, 'query_kind': kind,
                    'active_count': count, 'guarded': actual[cursor], 'unguarded': old_actual[cursor]})
            cursor += 1
    synthetic = out / 'defined-lookahead-hit.bin'
    synthetic.write_bytes(struct.pack('<IHh', 0x31424457, 1, 2) +
        b''.join(struct.pack('<IhBB', off, ident, 2, 0) for off, ident in ((0, 1), (1, 4), (2, 9))) +
        struct.pack('<Ihhhh', 2, 9, 2, 10, 2))
    guarded_case = command([exe, synthetic], 'guarded-defined-lookahead-run')
    old_case = command([unguarded_exe, synthetic], 'unguarded-defined-lookahead-run')
    if guarded_case.returncode or old_case.returncode or guarded_case.stdout == old_case.stdout:
        raise ValueError('defined lookahead hit did not expose the guard semantic delta')
    guarded_rows = [tuple(map(int, line.split(','))) for line in guarded_case.stdout.splitlines()]
    old_rows = [tuple(map(int, line.split(','))) for line in old_case.stdout.splitlines()]
    if (guarded_rows[0][5], old_rows[0][5], guarded_rows[0][2], old_rows[0][2],
        guarded_rows[0][10], old_rows[0][10]) != (-1, 2, 2, 2, 2, 2):
        raise ValueError('lookahead-hit return/cursor/home relation unexpected')
    recall_sources = [source(k) for k in ('root:19A9', 'root:19DC', 'root:1A28',
        'source-owned:memory-far-state', 'source-owned:ui-resource-scalars')]
    recall_objects = compile_sources(index_sources + recall_sources + common_services +
                                      [HERE / 'recall_driver.c'], 'recall')
    recall_exe = link(recall_objects, 'recall')
    expected_payloads = out / 'expected-resource-payloads.bin'
    expected_payload_identity = resource_logic.write_expected_payloads(ROOT / 'assets', expected_payloads)
    inputs.add(expected_payloads)
    before = {p.resolve().relative_to(ROOT).as_posix(): pin(p) for p in inputs}
    ran = command([recall_exe, ROOT / 'assets', expected_payloads], 'recall-run')
    if ran.returncode:
        raise ValueError('recall failed: ' + ran.stdout[-2500:] + ran.stderr)
    records = [line.split(',') for line in ran.stdout.splitlines() if line.startswith('RECORD,')]
    if len(records) != 840:
        raise ValueError('expected 840 resource records')
    # Actual source creation and dirty-header close write the DOS 14-byte wire
    # format. Isolate them from prior source CloseIndex pointer residue by using
    # a fresh process and scratch files; shipped resources are read-only inputs.
    wire_dir = out / 'database-wire'
    wire_dir.mkdir()
    (wire_dir / 'EXIST.NDX').write_bytes(struct.pack('<hhiiihh', 1, 0, 0, 0, 0, 0, 0) +
                                      struct.pack('<IhBB', 0, 0, 0, 8))
    (wire_dir / 'EXIST.DAT').write_bytes(struct.pack('<Ihii', 0x12345678, -2, 0x11223344, 0x33445566))
    wire_run = command([recall_exe, '--wire', wire_dir], 'database-header-wire-run')
    expected_writes = {'NEW': struct.pack('<Ihii', 0x12345678, 0, 0, 0),
                       'EXIST': struct.pack('<Ihii', 0x12345678, -7, 0x01020304, 0x05060708)}
    if wire_run.returncode:
        raise ValueError('database header wire run failed: ' + wire_run.stderr)
    wire_rows = [line.split(',') for line in wire_run.stdout.splitlines() if line.startswith('WRITE,')]
    if len(wire_rows) != 2 or any(bytes.fromhex(row[2]) != expected_writes[row[1]] or int(row[3]) != 14
                                 for row in wire_rows):
        raise ValueError('database header write differs from independently encoded wire fields')

    # Whole-TU negative: moving the real DAT header read by one byte must fail.
    recall_path = source('root:19A9')
    body = recall_path.read_text()
    anchor = 'entry->offset + 14, &header, 10L'
    if body.count(anchor) != 1:
        raise ValueError('record header offset negative anchor not unique')
    mutant = out / 'root_19A9-header-offset-negative.c'
    mutant.write_text(body.replace(anchor, 'entry->offset + 15, &header, 10L'))
    mutant_obj = compile_sources([mutant], 'negative')[0]
    target_index = len(index_sources)
    negative_objects = list(recall_objects)
    negative_objects[target_index] = mutant_obj
    negative_exe = link(negative_objects, 'negative')
    negative = command([negative_exe, ROOT / 'assets', expected_payloads], 'header-offset-negative-run')
    if negative.returncode == 0:
        raise ValueError('wrong record header offset escaped the fixture')
    reject = HERE / 'reject_legacy_pointer.c'
    inputs.add(reject)
    rejected = command([gcc, '-std=c11', '-c', reject, '-o', out / 'reject.o'], 'pointer-wire-negative')
    if rejected.returncode == 0:
        raise ValueError('legacy pointer-bearing wire entry unexpectedly compiled')
    # New negative dependencies are included; stable earlier pins must not drift.
    after = {p.resolve().relative_to(ROOT).as_posix(): pin(p) for p in inputs}
    if any(after.get(path) != identity for path, identity in before.items()):
        raise ValueError('current source/dependency changed during validation')
    result = {'schema': 'simant-current-canonical-native-database-v1',
        'status': 'PASS_NATIVE_INTEGRATION_WITH_PORT_BLOCKING_GUARD_EXCEPTION',
        'classification': 'native current-source integration; zero fresh original-DOS calls',
        'conversion_report': pin(report_path), 'index': {'queries': len(actual),
            'onepast_cursor_positions': onepast, 'guarded_reserved_hits_vs_old_fixture': reserved_guard_changes,
            'pointer_and_entry_observations_match': True},
        'findindex_guard_exception': {'status': 'SEMANTIC_PORT_BLOCKING',
            'asset_query_differences': asset_deltas,
            'defined_lookahead_positive': {'guarded': guarded_rows, 'unguarded': old_rows},
            'actual_delta': 'At insertion rank count, both preserve cursor and global one-past pointer; guard skips comparison/read and returns NULL instead of matching reserved-row entry.',
            'successful_asset_recall_domain': '840 in-range existing records use ranks below count; the guard is not reached for these lookup hits.',
            'reachability_gap': 'No general original caller/resource/heap invariant excludes a matching one-past row on misses; this conditional fixture proves the observable delta but is not a shipped-resource witness.',
            'asset_fixture_allocation': 'Native query fixture allocates count+1 rows and copies the first reserved row from each NDX. Original source OpenIndex reads and allocates only count*8 bytes, so the reserved file row does not establish original adjacent heap contents.',
            'fresh_dos_calls': 0, 'mechanical_guard_removal_is_safe_general_port': False},
        'recall': {'records': len(records), 'lzss_records': sum(int(r[4]) & 1 != 0 and int(r[4]) & 4 == 0 for r in records),
                   'bytewise_payload_comparisons': len(records), 'databases_closed': 3,
                   'fixture_sentinel_installations': 0, 'records_observed': records,
                   'independent_expected_payloads': expected_payload_identity},
        'database_header_wire_save': {'status': 'PASS', 'bytes_per_header': 14,
            'actual_created_and_dirty_close_headers': wire_rows,
            'fresh_process': True, 'isolated_native_slot_domain': 'Fresh NEW slot has zero index pointer; EXIST has valid one-row source-allocated index.',
            'game_savegame_or_saverec_claim': False},
        'negative_controls': {'header_offset_plus_one_exit': negative.returncode,
                              'legacy_pointer_wire_compile_exit': rejected.returncode},
        'boundaries': ['EMS unavailable with fail-fast traps for other EMS operations.',
            'FindIndex native count guard deliberately differs from DOS reserved-row hits.',
            'Independent resource parser is a test oracle, not the recalled payload provider.',
            'No FileSelect/SaveRec/selectedsim v7 source or harness changed.'],
        'gaps': ['No native-vs-original-DOS equivalence claim or independent DOS link.',
                 'Fatal DB OpenDB[-1] and db_handles[4] gates remain unresolved.',
                 'Full SaveGame/UI FileSelect and all 307 save records are outside this DB fixture.'],
        'inputs': after, 'gcc': {'path': str(gcc), 'sha256': hashlib.sha256(gcc.read_bytes()).hexdigest()},
        'commands': commands}
    (out / 'report.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'status': result['status'], 'index_queries': len(actual), 'recall_records': len(records),
                      'report': (out / 'report.json').relative_to(ROOT).as_posix()}, indent=2))


if __name__ == '__main__':
    main()
