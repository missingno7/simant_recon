"""Replay original SOUND index allocation followed by an original neighbor allocation.

The sole initialized heap is the existing ownership-probe fixture. All subsequent
headers come from original instructions; no reserved row, sentinel or extra index
capacity is installed. File/format boundaries reuse the prior reviewed model.
The native negative executes the current converted whole TU with exactly count
rows, retaining its documented safety guard.
"""
from pathlib import Path
from types import SimpleNamespace
import argparse
import collections
import hashlib
import importlib.util
import json
import struct
import subprocess
import sys

SOURCE = Path(__file__).resolve()
ROOT = next(p for p in SOURCE.parents if (p / 'src/program.json').is_file())
OUT = SOURCE.parent
PRIOR = ROOT / 'evidence/canonical/native-findindex-boundary/probe.py'
spec = importlib.util.spec_from_file_location('prior_findindex_ownership', PRIOR)
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)
b, memory, exe, functions = p.b, p.memory, p.exe, p.functions


def pin(path):
    path = Path(path).resolve()
    raw = path.read_bytes()
    return {'path': path.relative_to(ROOT).as_posix(),
            'sha256': hashlib.sha256(raw).hexdigest(), 'size': len(raw)}


def far(v):
    return {'raw': v, 'hex': f'{v >> 16:04X}:{v & 65535:04X}',
            'linear': p.far_linear(v)}


def header(machine, at):
    raw = machine.read(at, 32)
    handle, size, paras, kind, lock, age, nxt, prev, attr = struct.unpack_from('<hI HBBI HHB', raw)
    return {'linear': at, 'bytes': raw.hex(), 'master_slot_offset': handle,
            'requested_bytes': size, 'paras': paras, 'type': kind,
            'lock': lock, 'age': age, 'next_segment': nxt, 'prev_segment': prev,
            'attributes': attr, 'name': raw[19:].split(b'\0')[0].decode('ascii'),
            'as_index_id': struct.unpack_from('<h', raw, 4)[0],
            'as_index_kind': raw[6], 'as_index_flags': raw[7]}


def original_history(allocation_size, fill, release=False):
    raw = (ROOT / 'assets/SOUND.NDX').read_bytes()
    count = struct.unpack_from('<h', raw)[0]
    size = count * 8
    heap_seg, heap_paras, master_seg, master_end = 0xA100, 0x400, 0x90FF, 0
    # Offset-zero master base and 64 descending slots follow original startup.
    master_start = master_seg * 16 + 0x10000 - 64 * 4
    machine = b.Machine(SimpleNamespace(function=p.entry('OpenIndex'),
        vectors={exe.MANAGER_SEG * 16 + v.offset: v for v in exe.load().vectors},
        candidate_entries={}))
    writes = memory.memory_globals_writes(heap_start=heap_seg,
        heap_end=heap_seg + heap_paras, free_head=heap_seg,
        master_off=master_end, master_seg=master_seg, free_paras=heap_paras)
    writes += [(heap_seg * 16, memory.header(heap_paras, 0x80, size=0, name=b'free') +
                bytes([fill]) * (heap_paras * 16 - 32)),
               (master_start, bytes(64 * 4)),
               (0xA6000, b'sound\0'), (0xA6040, b'neighbor\0')]
    sequence = []
    visited = []
    tracked = {r['seg'] * 16 + r['off']: name for name in
        ('OpenIndex', 'FindIndex', 'f_171C_13CA', 'f_171C_125C',
         'f_171C_0EEA', 'f_171C_0A5C', 'f_171C_068C', 'f_171C_13E4',
         'f_171C_0160', 'f_171C_1246') for r in (p.entry(name),)}

    def code(cpu, address, length, user):
        if address in tracked:
            visited.append({'name': tracked[address],
                'at': f'{machine.reg("cs"):04X}:{machine.reg("ip"):04X}'})

    code_hook = machine.cpu.hook_add(b.uc.UC_HOOK_CODE, code)
    opened = machine.run(b.Case(label='SOUND/OpenIndex',
        args=[0, 0xA600, 0], writes=writes, callbacks=p.callbacks,
        state={'file_bytes': raw, 'file_cursor': 0, 'file_reads': []},
        return_kind='void'))
    pointer = int.from_bytes(machine.read(b.symbol_address('fd_50F6_3958') + 0x50, 4), 'little')
    start = p.far_linear(pointer)
    tail = start + size
    index_header = header(machine, start - 32)
    assert index_header['requested_bytes'] == size
    assert tail == start - 32 + index_header['paras'] * 16
    assert opened['state']['file_reads'] == [
        {'cursor': 0, 'requested': 20, 'returned': 20},
        {'cursor': 20, 'requested': size, 'returned': size}]
    assert machine.read(start, size) == raw[20:20 + size]
    assert opened['state']['file_cursor'] == 20 + size
    sequence.append({'name': 'OpenIndex', 'args': [0, 0xA600, 0],
        'return': None, 'actual_entries': visited.copy(),
        'modeled_callbacks': opened['raw_trace'],
        'index_pointer': far(pointer), 'index_header': index_header,
        'tail_owner_after': header(machine, tail)})
    visited.clear()
    recovered = machine.run(b.Case(label='recover index handle',
        args=[pointer & 65535, pointer >> 16], return_kind='farptr'),
        preserve=True, original_entry=p.entry('f_171C_2136'))
    assert recovered['return'] == (master_seg << 16) | (index_header['master_slot_offset'] & 65535)
    assert int.from_bytes(machine.read(p.far_linear(recovered['return']), 4), 'little') == pointer
    sequence.append({'name': 'f_171C_2136', 'payload': far(pointer), 'return_handle': far(recovered['return'])})
    allocated = machine.run(b.Case(label='original neighbor Ralloc',
        args=[allocation_size & 65535, allocation_size >> 16, 0, 0x40, 0xA600],
        callbacks=p.callbacks, return_kind='farptr'), preserve=True,
        original_entry=p.entry('f_171C_13CA'))
    handle = allocated['return']
    neighbor_pointer = int.from_bytes(machine.read(p.far_linear(handle), 4), 'little')
    assert p.far_linear(neighbor_pointer) - 32 == tail
    neighbor = header(machine, tail)
    assert neighbor['requested_bytes'] == allocation_size
    sequence.append({'name': 'f_171C_13CA',
        'args': {'size': allocation_size, 'flags': 0, 'name': 'neighbor'},
        'actual_stack_words': [allocation_size & 65535, allocation_size >> 16, 0, 0x40, 0xA600],
        'return_handle': far(handle), 'payload_pointer': far(neighbor_pointer),
        'actual_entries': visited.copy(), 'modeled_callbacks': allocated['raw_trace'],
        'tail_owner_after': neighbor})
    visited.clear()
    recovered = machine.run(b.Case(label='recover neighbor handle',
        args=[neighbor_pointer & 65535, neighbor_pointer >> 16], return_kind='farptr'),
        preserve=True, original_entry=p.entry('f_171C_2136'))
    assert recovered['return'] == handle
    sequence.append({'name': 'f_171C_2136', 'payload': far(neighbor_pointer), 'return_handle': far(handle)})
    if release:
        freed = machine.run(b.Case(label='original neighbor free',
            args=[handle & 65535, handle >> 16], callbacks=p.callbacks,
            return_kind='void'), preserve=True,
            original_entry=p.entry('f_171C_13E4'))
        sequence.append({'name': 'f_171C_13E4', 'args': far(handle),
            'return': None, 'actual_entries': visited.copy(),
            'modeled_callbacks': freed['raw_trace'],
            'tail_owner_after': header(machine, tail)})
        visited.clear()
    queries = []
    for ident, kind in ((0, 22), (1, 22), (0, 23), (10000, 22), (10010, 22), (0, 5)):
        reads = []

        def observe(cpu, access, address, length, value, user):
            if address < tail + 8 and address + length > tail:
                reads.append({'at': f'{machine.reg("cs"):04X}:{machine.reg("ip"):04X}',
                    'address': address, 'relative_to_index_end': address - tail,
                    'length': length, 'bytes': machine.read(address, length).hex()})

        hook = machine.cpu.hook_add(b.uc.UC_HOOK_MEM_READ, observe)
        found = machine.run(b.Case(label=f'FindIndex({ident},{kind})',
            args=[0, ident, kind], return_kind='farptr'), preserve=True,
            original_entry=p.entry('FindIndex'))
        machine.cpu.hook_del(hook)
        cursor = machine.word(b.symbol_address('fd_50F6_3956'))
        candidate = int.from_bytes(machine.read(b.symbol_address('fd_50F6_3952'), 4), 'little')
        expected_hit = not release and allocation_size == 320 and (ident, kind) == (0, 22)
        if kind >= 22:
            assert cursor == count
            assert candidate == pointer + size
            assert bool(found['return']) == expected_hit
            assert [r['at'] for r in reads] == (['1986:0209', '1986:0215'] if ident == 0 else ['1986:0209'])
            if expected_hit:
                assert found['return'] == candidate
                assert p.far_linear(found['return']) == tail
        else:
            assert cursor == 0 and found['return'] == pointer and not reads
        queries.append({'id': ident, 'kind': kind, 'cursor': cursor,
            'original_return': far(found['return']), 'global_candidate': far(candidate),
            'onepast_reads': reads, 'actual_entries': visited.copy()})
        visited.clear()
    machine.cpu.hook_del(code_hook)
    return {'fill': fill, 'allocated_neighbor_bytes': allocation_size,
        'released_neighbor': release, 'count': count, 'loaded_bytes': size,
        'file_reads': opened['state']['file_reads'], 'index_payload': far(pointer),
        'master_base': far(master_seg << 16), 'master_table_start_linear': master_start,
        'index_end_linear': tail, 'sequence': sequence, 'queries': queries}


NATIVE_DRIVER = r'''#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include "portable/whole_program/types/database.h"
extern IndexEntry *FindIndex(int16_t db, int16_t id, int16_t kind);
/* Link traps for unused peers in the complete TU. No trap may execute. */
int16_t dos_sprintf(char *dst, const char *format, ...) { (void)dst; (void)format; abort(); }
int16_t dos_open(char *path, int16_t flags, ...) { (void)path; (void)flags; abort(); }
int16_t dos_read(int16_t fd, void *buffer, uint16_t count) { (void)fd; (void)buffer; (void)count; abort(); }
int16_t dos_close(int16_t fd) { (void)fd; abort(); }
void DosPunt(char *message) { (void)message; abort(); }
void Punt(char *format, ...) { (void)format; abort(); }
void **f_171C_13CA(int32_t size, int16_t flags, char *name) { (void)size; (void)flags; (void)name; abort(); }
void dos_free(void *data) { (void)data; abort(); }
int main(int argc, char **argv) {
    FILE *f;
    IndexHeader h;
    IndexEntry *rows, *got;
    const int16_t queries[][2] = {{0,22},{1,22},{0,23},{10000,22},{10010,22},{0,5}};
    unsigned i;
    if (argc != 2 || !(f = fopen(argv[1], "rb"))) return 2;
    if (fread(&h, sizeof h, 1, f) != 1 || h.count != 120) return 3;
    rows = malloc((size_t)h.count * sizeof *rows);
    if (!rows || fread(rows, sizeof *rows, (size_t)h.count, f) != (size_t)h.count) return 4;
    fclose(f);
    fd_50F6_3958[0].indexHeader = h;
    fd_50F6_3958[0].index = rows;
    for (i = 0; i < sizeof queries / sizeof queries[0]; ++i) {
        got = FindIndex(0, queries[i][0], queries[i][1]);
        printf("%d,%d,%d,%td,%td\n", queries[i][0], queries[i][1], fd_50F6_3956,
            got ? got-rows : -1, fd_50F6_3952-rows);
    }
    free(rows);
    return 0;
}
'''


def native_guard(conversion):
    report_path = conversion / 'report.json'
    report = json.loads(report_path.read_text())
    rows = {r['module']: r for r in report['canonical_TUs']}
    keys = ('root:1986', 'source-owned:database-record-state', 'source-owned:database-index-state')
    for rel in ('src/root/m1986.c', 'src/state/database-record-state.c',
                'src/state/database-index-state.c',
                'portable/canonical_native_abi/findindex_native_guard.py',
                'portable/whole_program/types/database.h'):
        assert report['input_pins'][rel] == pin(ROOT / rel)['sha256'], rel
    inputs = [report_path]
    sources = []
    for key in keys:
        row = rows[key]
        assert row['status'] == 'WHOLE_CANONICAL_TU_CONVERTED' and row['compile']['passed']
        source = Path(row['generated']).resolve()
        assert source.is_relative_to(conversion)
        inputs += [ROOT / row['source'], source]
        copied = OUT / source.name
        copied.write_bytes(source.read_bytes())
        sources.append(copied)
    body = sources[0].read_text()
    guard = 'if (fd_50F6_3956 == fd_50F6_3958[db].indexHeader.count) return 0L;'
    assert body.count(guard) == 1
    driver = OUT / 'native_guard_driver.c'
    driver.write_text(NATIVE_DRIVER, encoding='utf-8')
    cmd = rows['root:1986']['compile']['command']
    gcc = cmd[0]
    flags = cmd[1:cmd.index('-c')] + ['-O0', '-ffunction-sections', '-fdata-sections']
    commands, objects = [], []
    for i, source in enumerate([*sources, driver]):
        obj = OUT / f'guard-{i}.o'
        argv = [gcc, *flags, '-c', str(source), '-o', str(obj)]
        ran = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True, timeout=45)
        commands.append({'argv': argv, 'returncode': ran.returncode,
            'stdout': ran.stdout, 'stderr': ran.stderr})
        if ran.returncode:
            raise RuntimeError(ran.stderr)
        objects.append(str(obj))
    executable = OUT / 'native_guard.exe'
    argv = [gcc, *objects, '-Wl,--gc-sections', '-o', str(executable)]
    ran = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True, timeout=45)
    commands.append({'argv': argv, 'returncode': ran.returncode, 'stdout': ran.stdout, 'stderr': ran.stderr})
    if ran.returncode:
        raise RuntimeError(ran.stderr)
    argv = [str(executable), str(ROOT / 'assets/SOUND.NDX')]
    ran = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True, timeout=45)
    commands.append({'argv': argv, 'returncode': ran.returncode, 'stdout': ran.stdout, 'stderr': ran.stderr})
    assert ran.returncode == 0
    actual = [list(map(int, line.split(','))) for line in ran.stdout.splitlines()]
    assert actual == [[0,22,120,-1,120],[1,22,120,-1,120],[0,23,120,-1,120],
                      [10000,22,120,-1,120],[10010,22,120,-1,120],[0,5,0,0,0]]
    (OUT / 'native-guard-commands.json').write_text(json.dumps(commands, indent=2) + '\n')
    return {'status': 'EXECUTED_CURRENT_WHOLE_TU_GUARD_NEGATIVE',
        'guard': guard, 'index_capacity_rows': 120, 'loaded_rows': 120,
        'neighbor_headers_installed': False, 'reserved_rows_installed': False,
        'columns': ['id', 'kind', 'cursor', 'returned_rank_or_minus_one', 'global_candidate_rank'],
        'observations': actual, 'inputs': [pin(x) for x in [*inputs, driver]],
        'compiler': {'path': gcc, 'sha256': hashlib.sha256(Path(gcc).read_bytes()).hexdigest()},
        'commands': 'native-guard-commands.json',
        'limit': 'This verifies the existing guard result with the same loaded rows/query. Native platform handles do not preserve the original DOS adjacency; no native allocator equivalence is claimed.'}


def main():
    global OUT
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out', type=Path, default=ROOT / 'build/workers/findindex_neighbor_replay')
    ap.add_argument('--conversion', type=Path, required=True)
    args = ap.parse_args()
    OUT = args.out.resolve()
    assert OUT.is_relative_to(ROOT / 'build') and OUT != ROOT / 'build'
    OUT.mkdir(parents=True, exist_ok=True)
    raw = (ROOT / 'assets/SOUND.NDX').read_bytes()
    count = struct.unpack_from('<h', raw)[0]
    entries = [struct.unpack_from('<IhBB', raw, 20+i*8) for i in range(count)]
    assert [(e[2], e[1]) for e in entries] == sorted((e[2], e[1]) for e in entries)
    results = [original_history(320, fill) for fill in (0xA7, 0xB9)]
    results += [original_history(304, 0xA7), original_history(320, 0xA7, release=True)]
    negative = native_guard(args.conversion.resolve())
    contexts = []
    for name in ('OpenIndex', 'FindIndex', 'f_171C_13CA', 'f_171C_125C',
                 'f_171C_068C', 'f_171C_13E4', 'f_171C_0160', 'f_171C_2136'):
        ran = subprocess.run([sys.executable, 'tools/context.py', name], cwd=ROOT,
            text=True, capture_output=True, check=True, timeout=45)
        context = OUT / f'{name}.disasm.txt'
        context.write_text(ran.stdout, encoding='utf-8')
        contexts.append(pin(context))
    report = {'schema': 'simant-findindex-original-allocator-neighbor-v1',
        'status': 'ORIGINAL_HEADER_FALSE_HIT_WITNESS_BOUNDED',
        'scope': 'Original instruction execution after a valid initialized free-heap fixture. No full-game reachability, original allocator startup, or native allocator-equivalence claim.',
        'actual_top_level_original_calls': sum(len(r['sequence'])+len(r['queries']) for r in results),
        'unicorn_version': b.uc.__version__,
        'asset': {'count': count, 'loaded_bytes': count*8,
            'max_kind': max(e[2] for e in entries),
            'last_key': {'id': entries[-1][1], 'kind': entries[-1][2]},
            'kind_counts': dict(collections.Counter(e[2] for e in entries))},
        'results': results, 'native_guard_negative': negative,
        'constraints': [
            'SOUND maxkind20 makes query0/kind22 lower-bound rank120, regardless of its id.',
            '320-byte original allocation has paras22 including its 32-byte header. Header+4 is the high size word0; header+6 is low paras byte22.',
            'FindIndex returns the retained-index-segment far pointer A102:03C0, physically identical to neighbor Block A13E:0000, rather than neighbor payload A140:0000.',
            'Direct production FindIndex caller DBRecall forwards object/type without a local range restriction, and db_LoadObject forwards its int object/kind on cache misses.',
            'Known original kind22 LoadMonoPats calls use IDs10000 and10010, so neither matches this small-allocation header ID0. Both original negative queries execute rank120 id reads and return NULL.',
            'No observed source call requesting ID0/kind22 has been established. Generic wrappers accepting caller-supplied object/kind do not prove that pair reachable.',
            'A large long allocation can store a nonzero high size word while paragraph arithmetic uses low16; this probe does not supply such unsupported capacity histories.'],
        'handling_assessment': {
            'remove_native_guard': False,
            'add_reserved_or_sentinel_row': False,
            'mechanical_canonical_source_correction_supported': False,
            'reason': 'The index bytes do not own the candidate. Returning a Block header is a real DOS arena alias depending on allocator history; host malloc blocks and widened runtime pointers cannot reconstruct it from index rows.',
            'supported_direction_only': 'A source-driven DOS arena preserving original Block fields, allocator state/history and paragraph addresses could expose an explicit address view at a platform boundary. It must retain canonical allocator algorithms and represent cross-object dereference/DBRecall offset interpretation. This witness alone does not prove such a design or initial heap contents.'},
        'limits': [
            'Master base has original startup offset zero;64descending slots end one paragraph before heap. Both original pointer-to-handle recoveries pass in every history. Free heap/header/counters remain test-owned; full original _dos_allocmem startup is not executed.',
            'Neighbor size320 and synthetic query0/kind22 are deliberately controlled API inputs, not an asserted game allocation/query sequence.',
            'No table padding, reserved row or fake sentinel is installed; original allocation/split/free instructions produce every header observed after initialization.',
            'Negative native guarded whole-TU execution uses exactly count rows and no modeled neighbor. Its NULL result demonstrates the guard semantic contrast, not equality of native/DOS heaps.',
            'Original instructions execute unchanged from the hash-locked EXE. No canonical or production source was edited, and no claim was promoted.'],
        'contexts': contexts,
        'inputs': [pin(ROOT / rel) for rel in [SOURCE.relative_to(ROOT).as_posix(),
            PRIOR.relative_to(ROOT).as_posix(), 'tools/behavior.py', 'tools/behavior_suites/memory.py',
            'tools/functions.py', 'tools/exe.py', 'tools/match.py', 'assets/SIMANT.EXE',
            'assets/SOUND.NDX', 'layout/oracle.lock.json', 'layout/functions.json',
            'layout/symbols.json', 'src/root/m1986.c', 'src/root/m171C.c',
            'src/root/m19A9.c', 'src/root/m1A53.c', 'src/root/m15F8.c',
            'src/S15/m384C.c', 'portable/whole_program/platform/handles.c',
            'portable/canonical_native_abi/findindex_native_guard.py',
            'portable/whole_program/types/database.h']],
        'parent_review_required': True, 'production_edits': 0}
    path = OUT / 'allocator-neighbor-probe.json'
    path.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'report': str(path), 'status': report['status'],
        'actual_original_calls': report['actual_top_level_original_calls'],
        'histories': [{'size': r['allocated_neighbor_bytes'], 'fill': r['fill'],
            'free': r['released_neighbor'], 'query0_22': r['queries'][0]} for r in results],
        'native_guard_negative': negative['observations']}, indent=2))


if __name__ == '__main__':
    main()
