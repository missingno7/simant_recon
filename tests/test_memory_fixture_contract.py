"""Original allocator history checks for the shared bounded DOS heap fixture."""
from pathlib import Path
from types import SimpleNamespace
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import behavior as b
import exe
import functions
from behavior_suites import memory as m


class HeapFixturePremise(unittest.TestCase):
    def original_machine(self, target='f_171C_2136'):
        return b.Machine(SimpleNamespace(function=functions.get(target),
            vectors={exe.MANAGER_SEG * 16 + v.offset: v for v in exe.load().vectors},
            candidate_entries={}))

    def test_seeded_slots_use_raw_offsets_and_the_observation_covers_them(self):
        case = m.heap_case('seeded-slot-recovery',
            [(8,1),(8,3),(32,0x80)], handles=[0,1], result='farptr')
        table = next(r for r in case.observe if r.name == 'handle_table')
        vm = self.original_machine()
        for index in range(2):
            payload_seg = m.HEAP_SEG + index * 8 + 2
            call = case if index == 0 else b.Case(label='second-seeded-slot', return_kind='farptr')
            call.args = [0,payload_seg]
            recovered = vm.run(call, preserve=index > 0)['return']
            expected = (m.HANDLE_SEG << 16) | (m.MASTER_FIRST - index * 4)
            self.assertEqual(recovered, expected)
            slot = m.HANDLE_SEG * 16 + (recovered & 65535)
            self.assertLessEqual(table.address, slot)
            self.assertLessEqual(slot + 4, table.address + table.size)
            self.assertEqual(vm.word((payload_seg - 2) * 16), recovered & 65535)

    def test_original_allocation_rejects_the_old_nonzero_master_premise(self):
        writes = m.memory_globals_writes(heap_start=m.HEAP_SEG,
            heap_end=m.HEAP_SEG + 64, free_head=m.HEAP_SEG,
            master_off=0x104, master_seg=0xA000, free_paras=64)
        writes += [(m.HEAP_SEG * 16,m.header(64,0x80) + bytes(64*16-32)),
                   (0xA000 * 16 + 4,bytes(64*4)), (0xB2000,b'new-live\0')]
        vm = self.original_machine('f_171C_125C')
        allocated = vm.run(b.Case(label='old-base-actual-allocation',
            args=[160,0,1,0,0xB200], writes=writes, return_kind='farptr'))['return']
        payload = int.from_bytes(vm.read(0xA000 * 16 + 0x100,4),'little')
        self.assertEqual(allocated,0xA0000100)
        self.assertEqual(vm.word((payload >> 16)*16-32),allocated & 65535)

        def reached_punt(machine, args):
            raise AssertionError('bad-handle Punt reached')

        with self.assertRaisesRegex(b.ExecutionError,'bad-handle Punt reached'):
            vm.run(b.Case(label='old-base-pointer-recovery', args=[payload & 65535,payload >> 16],
                return_kind='farptr', callbacks={'Punt':b.Callback(2,reached_punt)}),
                preserve=True, original_entry=functions.get('f_171C_2136'))

    def test_completed_original_allocations_survive_candidate_compaction(self):
        pair = b.PreparedPair('f_171C_0CF4', sequence_targets=m.TARGETS,
            out=ROOT / 'build/workers/heap_fixture_contract_tests/completed-history')
        steps = m.completed_allocation_sequence('test/completed-history')
        results = list(pair.compare_sequence(steps))
        for result in results:
            self.assertTrue(result.equal,result.diff)
        expected = (m.HANDLE_SEG << 16) | (m.MASTER_FIRST - 4)
        for index,offset,handle_offset in ((0,0,m.MASTER_FIRST),(1,12*16,m.MASTER_FIRST-4),
                                          (3,0,m.MASTER_FIRST-4)):
            heap = bytes.fromhex(results[index].original['ranges']['heap'])
            self.assertEqual(int.from_bytes(heap[offset:offset+2],'little'),handle_offset)
        self.assertEqual(results[1].original['return'],expected)
        self.assertEqual(results[4].original['return'],expected)
        for vm in (pair.original_machine,pair.candidate_machine):
            self.assertEqual(vm.word(m.dga(0x2F44)),0)
            table = next(r for r in steps[0][1].observe if r.name == 'handle_table')
            self.assertEqual(vm.read(table.address,table.size),bytes(table.size))

    def test_raw_high_allocation_is_the_terminal_helper_boundary(self):
        steps = m.make_sequence('test/raw-helper')
        self.assertEqual(steps[-1][0],'f_171C_0FBC')
        self.assertIn('caller handle installation has not executed',
            steps[-1][1].metadata['sequence']['terminal_boundary'])
        self.assertTrue(all(not case.writes for _,case in steps[1:]))

    def test_fixture_rejects_missing_duplicate_out_of_range_or_overlapping_slots(self):
        for handles in ([],[0,0],[63],[64],[-1]):
            rows = [(8,1),(8,3)] if len(handles) == 2 else [(8,1)]
            with self.subTest(handles=handles), self.assertRaises(ValueError):
                m.heap_case('invalid-slot-premise',rows,handles=handles)
        with self.assertRaisesRegex(ValueError,'overlaps'):
            m.heap_case('overlapping-master',[(8,1)],handles=[0],heap_seg=0xA0FE)
        old = m.MASTER_ONE_PAST
        try:
            m.MASTER_ONE_PAST = 0x104
            with self.assertRaisesRegex(ValueError,'offset-zero'):
                m.heap_case('nonzero-master',[(8,0x80)])
        finally:
            m.MASTER_ONE_PAST = old

    def test_sparse_handle_history_preserves_high_water_counter(self):
        case = m.heap_case('sparse-live-slot',[(8,1,{"lock":1}),(32,0x80)],handles=[2],
            args=[m.MASTER_FIRST-8,m.HANDLE_SEG],result='farptr')
        vm = self.original_machine('f_171C_1BBA')
        vm.run(case)
        self.assertEqual(vm.word(m.dga(0x2F42)),3)
        self.assertEqual(vm.word(m.dga(0x2F44)),1)

    def test_reclaimed_handle_resolves_type_five_template_and_free_skips_heap(self):
        case = m.heap_case('actual-reclaim',[(8,3,{"age":7}),(32,0x80)],handles=[0],args=[0])
        vm = self.original_machine('f_171C_0BE2')
        self.assertEqual(vm.run(case)['return'],1)
        slot = m.HANDLE_SEG*16+m.MASTER_FIRST
        self.assertEqual(int.from_bytes(vm.read(slot,4),'little'),m.DISCARD_DATA_SEG<<16)
        self.assertEqual(int.from_bytes(vm.read(b.symbol_address('fd_50F6_3948'),4),'little'),
                         m.DISCARD_HEADER_SEG<<16)
        for target,expected in (('f_171C_1686',5),('f_171C_1794',1)):
            result = vm.run(b.Case(label=target,args=[m.MASTER_FIRST,m.HANDLE_SEG]),
                preserve=True,original_entry=functions.get(target))
            self.assertEqual(result['return'],expected)
        heap_before = vm.read(m.HEAP_SEG*16,40*16)
        counters_before = vm.read(m.dga(0x2F36),12)
        vm.run(b.Case(label='free-discarded',args=[m.MASTER_FIRST,m.HANDLE_SEG],return_kind='void'),
            preserve=True,original_entry=functions.get('f_171C_13E4'))
        self.assertEqual(vm.read(m.HEAP_SEG*16,40*16),heap_before)
        self.assertEqual(vm.read(m.dga(0x2F36),12),counters_before)
        self.assertEqual(vm.word(m.dga(0x2F44)),0)
        self.assertEqual(vm.read(slot,4),bytes(4))

    def test_original_lock_rejects_a_reclaimed_handle(self):
        case = m.heap_case('reclaim-before-lock',[(8,3),(32,0x80)],handles=[0],args=[0])
        vm = self.original_machine('f_171C_0BE2')
        vm.run(case)

        def rejected_discard(machine,args):
            raise AssertionError('original discarded-lock Punt reached')

        with self.assertRaisesRegex(b.ExecutionError,'original discarded-lock Punt reached'):
            vm.run(b.Case(label='lock-discarded',args=[m.MASTER_FIRST,m.HANDLE_SEG],
                return_kind='farptr',callbacks={'Punt':b.Callback(2,rejected_discard)}),
                preserve=True,original_entry=functions.get('f_171C_1B84'))


if __name__ == '__main__':
    unittest.main()
