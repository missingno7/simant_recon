"""Bounded original-DOS ownership probe; no source/native equivalence claim.

Run original OpenIndex and its actual original Ralloc code, modeling only
formatting and file-service boundaries. Seed a valid initialized free heap with
two nonzero fills to determine the index tail's owner. No NDX reserved row is
read or installed. Then run original FindIndex and observe real memory reads.
"""
from pathlib import Path
from types import SimpleNamespace
import hashlib
import argparse
import json
import struct
import subprocess
import sys

SOURCE = Path(__file__).resolve()
ROOT = next(p for p in SOURCE.parents if (p / 'src/program.json').is_file())
OUT = SOURCE.parent
sys.path[:0] = [str(ROOT / 'tools'), str(ROOT / 'tools/behavior_suites')]
import behavior as b
import functions
import exe
import memory


def pin(rel):
    raw = (ROOT / rel).read_bytes()
    return {'path': rel, 'sha256': hashlib.sha256(raw).hexdigest(), 'size': len(raw)}


def entry(name):
    return functions.get(name)


def far_linear(v):
    return (v >> 16) * 16 + (v & 65535)


def format_name(machine, args):
    # File-name formatting is unrelated to the storage question under test.
    off, seg = args[:2]
    machine.write(seg * 16 + off, b'ownership.ndx\0')
    return 13


def read_file(machine, args):
    fd, off, seg, count = args
    data = machine.state['file_bytes']
    at = machine.state['file_cursor']
    got = data[at:at + count]
    machine.write(seg * 16 + off, got)
    machine.state['file_cursor'] += len(got)
    machine.state['file_reads'].append({'cursor': at, 'requested': count, 'returned': len(got)})
    return len(got)


def fail(machine, args):
    raise RuntimeError('unexpected fatal allocator or index path')


callbacks = {
    'sprintf': b.Callback(8, format_name),
    'open': b.Callback(3, lambda machine, args: 3),
    'read': b.Callback(4, read_file),
    'close': b.Callback(1, lambda machine, args: 0),
    'Punt': b.Callback(2, fail),
    'DosPunt': b.Callback(2, fail),
}


def probe(stem, fill, ident, kind):
    raw = (ROOT / f'assets/{stem}.NDX').read_bytes()
    count = struct.unpack_from('<h', raw)[0]
    size = count * 8
    heap_seg, heap_paras, master_seg, master_end = 0xA100, 0x400, 0x90FF, 0
    # Original startup uses an offset-zero master base. Slots wrap below it
    # in the same segment; 64 slots end one paragraph before this heap.
    master_start = master_seg * 16 + 0x10000 - 64 * 4
    pair = SimpleNamespace(function=entry('OpenIndex'),
        vectors={exe.MANAGER_SEG * 16 + v.offset: v for v in exe.load().vectors},
        candidate_entries={})
    machine = b.Machine(pair)
    writes = memory.memory_globals_writes(heap_start=heap_seg,
        heap_end=heap_seg + heap_paras, free_head=heap_seg,
        master_off=master_end, master_seg=master_seg, free_paras=heap_paras)
    writes += [(heap_seg * 16, memory.header(heap_paras, 0x80, size=0, name=b'free') +
                bytes([fill]) * (heap_paras * 16 - 32)),
               (master_start, bytes(64 * 4)),
               (0xA6000, stem.encode() + b'\0')]
    opened = machine.run(b.Case(label=f'{stem}/fill{fill:02x}/OpenIndex',
        args=[0, 0xA600, 0], writes=writes, callbacks=callbacks,
        state={'file_bytes': raw, 'file_cursor': 0, 'file_reads': []},
        return_kind='void'))
    db = b.symbol_address('fd_50F6_3958')
    pointer = int.from_bytes(machine.read(db + 0x50, 4), 'little')
    start = far_linear(pointer)
    block = start - 32
    block_paras = machine.word(block + 6)
    tail = start + size
    boundary = block + block_paras * 16
    recovered = machine.run(b.Case(label=f'{stem}/recover index handle',
        args=[pointer & 65535, pointer >> 16], return_kind='farptr'),
        preserve=True, original_entry=entry('f_171C_2136'))
    slot = machine.word(block)
    assert recovered['return'] == (master_seg << 16) | slot
    assert int.from_bytes(machine.read(far_linear(recovered['return']), 4), 'little') == pointer
    reads = []

    def observe_read(cpu, access, address, length, value, user):
        if address < tail + 8 and address + length > tail:
            reads.append({'address': address, 'relative_to_end': address - tail, 'length': length})

    hook = machine.cpu.hook_add(b.uc.UC_HOOK_MEM_READ, observe_read)
    found = machine.run(b.Case(label=f'{stem}/fill{fill:02x}/FindIndex',
        args=[0, ident, kind], return_kind='farptr'), preserve=True,
        original_entry=entry('FindIndex'))
    machine.cpu.hook_del(hook)
    assert opened['state']['file_cursor'] == 20 + size
    assert machine.read(start, size) == raw[20:20 + size]
    assert machine.word(b.symbol_address('fd_50F6_3956')) == count
    assert found['return'] == 0  # reached read, without a false-hit result
    assert reads == [{'address': tail + 4, 'relative_to_end': 4, 'length': 2}]
    if count & 1:
        assert machine.read(tail, 8) == bytes([fill]) * 8
    else:
        assert tail == boundary
    return {'database': stem, 'fill': fill, 'count': count, 'requested_bytes': size,
        'physical_payload_bytes': block_paras * 16 - 32,
        'payload_pointer': pointer, 'query': {'id': ident, 'kind': kind},
        'original_return': found['return'],
        'cursor': machine.word(b.symbol_address('fd_50F6_3956')),
        'global_candidate': int.from_bytes(machine.read(b.symbol_address('fd_50F6_3952'), 4), 'little'),
        'file_reads': opened['state']['file_reads'],
        'onepast_8_bytes': machine.read(tail, 8).hex(),
        'tail_owner': 'allocated paragraph padding' if tail < boundary else 'next free Block header',
        'next_header_relative_to_end': boundary - tail,
        'next_header': machine.read(boundary, 32).hex(),
        'onepast_reads': reads,
        'master_base': {'segment': master_seg, 'offset': master_end},
        'original_pointer_to_handle_recovery': recovered['return'],
        'allocator_trace_callbacks': sorted({r['name'] for r in opened['raw_trace']})}


def main():
    global OUT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    default = SOURCE.parent if SOURCE.is_relative_to(ROOT / 'build') else ROOT / 'build/workers/native_findindex_boundary_replay'
    OUT = (args.out or default).resolve()
    if not OUT.is_relative_to(ROOT / 'build'):
        raise ValueError('Probe outputs must stay in build scratch')
    OUT.mkdir(parents=True, exist_ok=True)
    results = [probe(stem, fill, ident, kind)
        for stem, ident, kind in [('HCEGANT', 10010, 18), ('SHARED', 10000, 22), ('SOUND', 10000, 22)]
        for fill in (0xA7, 0xB9)]
    for name in ('FindIndex', 'OpenIndex', 'f_171C_125C', 'f_171C_068C'):
        run = subprocess.run([sys.executable, 'tools/context.py', name], cwd=ROOT,
            text=True, capture_output=True, check=True)
        (OUT / f'{name}.disasm.txt').write_text(run.stdout, encoding='utf-8')
    report = {'schema': 'simant-findindex-native-boundary-investigation-v1',
        'status': 'UNRESOLVED_SEMANTIC_PORT_BLOCKER',
        'scope': 'Original DOS allocator/index ownership and reads with modeled file/format service boundaries; no native/original equivalence or full-game heap-reachability acceptance.',
        'actual_original_calls': len(results) * 3,
        'unicorn_version': b.uc.__version__,
        'inputs': [pin(rel) for rel in [SOURCE.relative_to(ROOT).as_posix(),
            'tools/behavior.py', 'tools/behavior_suites/memory.py', 'assets/SIMANT.EXE',
            'layout/oracle.lock.json', 'layout/functions.json', 'layout/symbols.json',
            'src/root/m1986.c', 'src/root/m171C.c', 'src/root/m19A9.c', 'src/root/m1A53.c',
            'src/root/m0000.c', 'src/root/m15F8.c', 'src/S20/m39F1.c', 'src/S15/m384C.c',
            'assets/HCEGANT.NDX', 'assets/SHARED.NDX', 'assets/SOUND.NDX']],
        'results': results,
        'dependencies': {'active_tools': ['tools/behavior.py', 'tools/behavior_suites/memory.py',
            'tools/functions.py', 'tools/exe.py', 'tools/match.py'],
            'historical_or_archived_sources_read': [],
            'prepared_pair_or_candidate_compiler_used': False,
            'runtime': 'Pinned Unicorn available through tools/behavior.py; current layout registry and original hash-locked assets.'},
        'limits': ['Heap starts in a valid initialized free-list fixture; original _dos_allocmem startup and full game allocation history were not executed.',
            'The nonzero fill varies preexisting free payload contents and does not create a sentinel. No reserved NDX row is loaded.',
            'The query arguments use ordinary source caller kinds; a passing NULL result under two fills cannot establish NULL under all reachable original histories.',
            'Original FindIndex and original allocator helpers execute directly. There is no newly compiled candidate or promoted claim.']}
    (OUT / 'ownership-probe.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'report': str(OUT / 'ownership-probe.json'),
        'cases': [{'database': r['database'], 'fill': r['fill'], 'owner': r['tail_owner'],
            'cursor': r['cursor'], 'tail': r['onepast_8_bytes'], 'reads': r['onepast_reads']} for r in results]}, indent=2))


if __name__ == '__main__':
    main()
