"""Bounded original allocator premise checks; fresh build-only outputs required."""
from pathlib import Path
from types import SimpleNamespace
import argparse
import hashlib
import json
import struct
import subprocess
import sys

ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'src/program.json').is_file())
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'tools'))
import behavior as b
import canonical_behavior as runner
import exe
import functions
import discard_probe
from behavior_suites import memory as m


def pin(path):
    raw = path.read_bytes()
    return {'path': path.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(raw).hexdigest()}


def contexts():
    for name in ('f_171C_07BE', 'f_171C_0A5C', 'f_171C_125C', 'f_171C_18A6',
                 'f_171C_2136', 'f_171C_0ADC', 'f_171C_0CF4', 'f_171C_0FBC', 'f_171C_1D40',
                 'f_171C_0BE2','f_171C_1686','f_171C_1794'):
        result = subprocess.run([sys.executable, 'tools/context.py', name], cwd=ROOT,
                                capture_output=True, text=True, check=True)
        (OUT / (name + '.disasm.txt')).write_text(result.stdout, encoding='utf-8')


def machine():
    return b.Machine(SimpleNamespace(function=functions.get('f_171C_125C'),
        vectors={exe.MANAGER_SEG * 16 + v.offset: v for v in exe.load().vectors},
        candidate_entries={}))


def failed_punt(machine, args):
    raise AssertionError('original Punt reached')


def original_allocation(base_off, master_seg):
    initial = b.Case(label='offset-base-allocation',
        writes=m.memory_globals_writes(heap_start=m.HEAP_SEG,
            heap_end=m.HEAP_SEG + 256, free_head=m.HEAP_SEG,
            master_off=base_off, master_seg=master_seg, free_paras=256) +
            [(m.HEAP_SEG * 16, m.header(256, 0x80, size=0) + bytes(256 * 16 - 32))])
    # Initialize the actual bounded descending master table explicitly for both
    # old and corrected premises, independent of the tested fixture's clear range.
    first = (base_off - 64 * 4) & 65535
    initial.writes += [(master_seg * 16 + first, bytes(64 * 4)), (0xB2000, b'new-live\0')]
    initial.args = [160, 0, 1, 0, 0xB200]
    initial.return_kind = 'farptr'
    vm = machine()
    allocated = vm.run(initial)
    handle = allocated['return']
    payload = int.from_bytes(vm.read((handle >> 16) * 16 + (handle & 65535), 4), 'little')
    at = (payload >> 16) * 16 - 32
    stored = vm.word(at)
    assert stored == handle & 65535
    recovered = None
    failure = None
    try:
        result = vm.run(b.Case(label='original raw-OFF pointer recovery',
            args=[payload & 65535, payload >> 16], return_kind='farptr',
            callbacks={'Punt': b.Callback(2, failed_punt)}), preserve=True,
            original_entry=functions.get('f_171C_2136'))
        recovered = result['return']
        assert recovered == handle
    except b.ExecutionError as exc:
        failure = str(exc)
    assert (failure is None) == (base_off == 0)
    return {'base_offset': base_off, 'master_segment': master_seg,
        'allocated_handle': handle, 'payload': payload, 'stored_block_handle': stored,
        'raw_OFF_matches': stored == handle & 65535,
        'recovered_handle': recovered, 'failure': failure}


def old_sequence_tail():
    pair = b.PreparedPair(m.TARGETS[0], out=OUT / 'old-tail', sequence_targets=m.TARGETS)
    steps = m.make_sequence('old-tail')
    # Deliberately reproduce the retired invalid continuation, with the corrected
    # offset-zero base. The invalid domain is an explicit premise negative.
    steps.append(('f_171C_0CF4',b.Case(label='old-tail/08-invalid-continuation',
        args=[0],observe=steps[0][1].observe,return_kind='s16',registers={'ds':m.DG,'ss':m.DG})))
    rows = []
    for (name, case), result in zip(steps, pair.compare_sequence(steps)):
        assert result.equal, result.diff
        vm = pair.original_machine
        blocks = []
        seg = m.HEAP_SEG
        end = vm.word(m.dga(0x91AA))
        while seg < end:
            at = seg * 16
            paras, kind = vm.word(at + 6), vm.read(at + 8, 1)[0]
            assert paras
            if kind in (0, 1, 3):
                h = vm.word(at)
                recovered_off = (m.MASTER_ONE_PAST + struct.unpack('<h', vm.read(at, 2))[0]) & 65535
                slot_value = int.from_bytes(vm.read(m.HANDLE_SEG * 16 + recovered_off, 4), 'little')
                expected = (seg + 2) << 16
                blocks.append({'block_segment': seg, 'type': kind, 'handle_word': h,
                    'slot_offset': recovered_off, 'slot_payload': slot_value,
                    'expected_payload': expected, 'handle_matches': slot_value == expected})
            seg += paras
        rows.append({'function': name, 'paired_equal': result.equal,
            'return': result.original['return'], 'live_blocks': blocks})
    raw = rows[-2]
    returned_seg = raw['return'] >> 16
    returned_block = next(block for block in raw['live_blocks'] if block['block_segment'] == returned_seg)
    assert not returned_block['handle_matches']
    return {'status':'INVALID_PERSISTENT_HEAP_PREMISE_CONFIRMED',
        'meaning':'0FBC raw Block return still lacks caller installation; paired equality cannot establish a valid live ownership history',
        'returned_block':returned_block,'steps':rows}


def completed_history():
    pair = b.PreparedPair(m.TARGETS[0],out=OUT / 'completed-history',sequence_targets=m.TARGETS)
    steps = m.completed_allocation_sequence('regression/completed-public-history')
    rows = []
    for index,((name,case),result) in enumerate(zip(steps,pair.compare_sequence(steps))):
        assert result.equal,result.diff
        vm = pair.original_machine
        rows.append({'function':name,'return':result.original['return'],'equal':result.equal,
            'block0_handle':vm.word(m.HEAP_SEG * 16),'block0_type':vm.read(m.HEAP_SEG*16+8,1)[0],
            'allocated_handle_high_water':vm.word(m.dga(0x2F42)),
            'live_handles':vm.word(m.dga(0x2F44)),
            'observed_first_two_slots':vm.read(m.HANDLE_SEG*16+m.MASTER_FIRST-4,8).hex()})
        if index in (0,1):
            h = result.original['return']
            slot = (h >> 16)*16+(h&65535)
            data = int.from_bytes(vm.read(slot,4),'little')
            assert vm.word((data >> 16)*16-32) == h&65535
        if index == 3:
            assert vm.word(m.HEAP_SEG*16) == m.MASTER_FIRST-4
    expected = (m.HANDLE_SEG<<16)|(m.MASTER_FIRST-4)
    assert rows[1]['return'] == rows[4]['return'] == expected
    assert rows[-1]['live_handles'] == 0
    table = next(r for r in steps[0][1].observe if r.name=='handle_table')
    assert pair.original_machine.read(table.address,table.size) == bytes(table.size)
    return {'identity':pair.identity,'steps':rows,
        'raw_OFF_allocation_assertions':2,'relocated_handle_recovery':expected,
        'observed_table':{'address':table.address,'size':table.size},
        'final_slots_empty':True}


def main():
    global OUT
    parser = argparse.ArgumentParser()
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--count',type=int,default=16)
    args = parser.parse_args()
    OUT = (ROOT / args.out).resolve()
    if OUT == ROOT / 'build' or not OUT.is_relative_to(ROOT / 'build') or OUT.exists():
        raise ValueError('fresh output strictly beneath build required')
    OUT.mkdir(parents=True)
    changed = ['tools/behavior_suites/memory.py','tools/behavior_suites/windows.py',
        'tools/behavior_suites/window_recalc_integration.py','tools/behavior_suites/lists.py',
        'tools/behavior_suites/dialog.py','tools/behavior_suites/render_small.py',
        'tools/canonical_behavior.py','tests/test_memory_fixture_contract.py',
        'evidence/canonical/viewport-layout/resize_probe.py']
    inputs = [pin(ROOT / p) for p in changed + ['src/root/m171C.c','src/program.json',
        'layout/manifest.json','assets/SIMANT.EXE','layout/oracle.lock.json',
        'tools/behavior.py','tools/behavior_ledger.py']]
    inputs.append(pin(Path(__file__).resolve()))
    inputs.append(pin(Path(discard_probe.__file__).resolve()))
    contexts()
    receipt = {
        'schema':'simant-allocator-fixture-premise-replay-v1',
        'status':'FIXTURE_REPAIR_VERIFIED_PENDING_PARENT_ACCEPTANCE',
        'suite':m.SUITE,'inputs':inputs,
        'static_premise':[
            {'entry':'171C:0830','fact':'Original startup writes zero to s_2F46.offset; segment is separately calculated.'},
            {'entry':'171C:0A91,0AAC','fact':'Handle allocation subtracts four in the same segment, starting at FFFC below the zero base.'},
            {'entry':'171C:1343,19DB','fact':'Original allocation/reallocation stores raw OFF(h), without subtracting the master base.'},
            {'entry':'171C:214F-2156','fact':'Pointer recovery adds Block.handle word to s_2F46.offset, retaining the master segment.'},
            {'entry':'171C:0B3B,0E94','fact':'Movement/compaction uses this same offset-base-plus-header-handle slot convention.'},
            {'entry':'171C:1E0F-1E5E','fact':'The 0FBC caller subsequently copies header/payload and installs the live master pointer.'},
            {'entry':'171C:07BE,0BE2,13E4','fact':'Startup copies zero Block fields except type5 to fd3948; reclaim stores fd3948+2 paragraphs, so HDR reads the copied template at fd3948 and free skips heap release for type5.'}],
        'base_controls':[original_allocation(0,0x90FF),original_allocation(0x104,0xA000)],
        'retired_sequence_negative':old_sequence_tail(),
        'completed_public_history':completed_history(),
        'discard_pointer_controls':[discard_probe.original_discard(False),discard_probe.original_discard(True)],
        'original_discarded_resize':discard_probe.original_discard_resize(),
        'focused_differential':runner.run_memory(args.count,0xC0DE29,OUT / 'differential',True),
        'changed_tests':changed,
        'supersession':{
            'old_suite':'ralloc_memory_v2_stateful',
            'old_claim_invalid':'Nine-step success does not establish valid persistent heap history; nonzero master base differs from startup and final compaction consumed an unfinished raw helper allocation.',
            'historical_receipts':'Four existing strict-static semantic receipts remain intact; the fixture repair changes finite corroboration, not reconstructed algorithms or their accepted status.',
            'new_scope':'Seeded live blocks follow raw OFF(h), a completed public allocation history validates pointer recovery after movement, discarded handles resolve the actual copied type5 template, and raw 0FBC cases end at their transitional helper boundary.'},
        'limits':[
            'Original _dos_allocmem/EMS startup and full-game reachability are not executed; initialized arena placement, header topology, counters and discard proxy remain explicit bounded test premises.',
            'The original 125C/13E4/2136 public setup/recovery helpers execute on both sides; only the four confirmed memory definitions compile and execute as active candidate targets.',
            'The old-base and raw-helper continuation are intentionally invalid-premise negative controls; matching execution there does not establish a valid live heap.',
            'No canonical algorithm, src/program.json, layout/manifest.json, proof category or oracle checkpoint is changed. Shared UI consumers use the corrected fixture without a second allocator model.',
            'The compact replay is finite caller-domain corroboration; all29/unit/viewport acceptance remains parent-owned.']}
    for row in receipt['focused_differential'].values():
        assert row['pass'] and not row['errors'] and not row['mismatches']
        assert row['negative']['detected']
    assert inputs == [pin(ROOT / i['path']) for i in inputs], 'pinned input changed during replay'
    path = OUT / 'receipt.json'
    path.write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({'report':str(path),'base_controls':receipt['base_controls'],
        'completed_history_equal':all(r['equal'] for r in receipt['completed_public_history']['steps']),
        'targets':{name:{'cases':row['cases'],'pass':row['pass'],
            'negative':row['negative']['detected']} for name,row in receipt['focused_differential'].items()}},indent=2))


if __name__ == '__main__':
    main()
