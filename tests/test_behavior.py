"""Differential-runner controls using invented tiny programs, not game claims.

The instruction fixtures below only exercise the VM plumbing. Historical
negative controls instead compile deliberate source mutants in scratch TUs.
"""
import sys
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
try:
    import behavior as b
except RuntimeError:
    b = None


@unittest.skipIf(b is None, 'workspace Unicorn dependency absent')
class ExecutionControls(unittest.TestCase):
    def pair(self, original, candidate=None, helper=None):
        p = SimpleNamespace(function={'unit':'root','seg':0x7000,'off':0},
                            code=bytes.fromhex(candidate or original),
                            candidate_entry=(0x9000,0), delegate={},
                            vectors={}, candidate_entries={})
        p.identity = {'oracle_sha256':b.exe.load().sha256}
        p.original_machine = b.Machine(p)
        p.original_machine.cpu.mem_write(0x70000, bytes.fromhex(original))
        p.candidate_machine = b.Machine(p,True)
        if helper:
            for m in (p.original_machine,p.candidate_machine):
                m.cpu.mem_write(0x71000,bytes.fromhex(helper))
        p.compare = lambda c: b.PreparedPair.compare(p,c)
        return p

    def test_equal_runs_and_case_state_are_independent(self):
        p = self.pair('b80700cb')
        c = b.Case('constant',state={'items':[]})
        self.assertTrue(p.compare(c).equal)
        p.original_machine.state['items'].append(3)
        self.assertTrue(p.compare(c).equal)
        self.assertEqual(c.state, {'items':[]})

    def test_return_mutation_detected(self):
        r = self.pair('b80700cb','b80800cb').compare(b.Case('wrong-return'))
        self.assertFalse(r.equal)
        self.assertIn('return',r.diff)

    def test_live_sequence_retains_global_and_model_state(self):
        # Invented counter: increment the same word on each invocation.
        p = self.pair('ff060010a10010cb')
        p.sequence_targets = frozenset()
        p.sequence_function = lambda name:p.function
        steps=[('counter',b.Case('first',writes=[(b.match.DGROUP_SEG*16+0x1000,b.words(0))],state={'live':True})),
               ('counter',b.Case('second'))]
        results=list(b.PreparedPair.compare_sequence(p,steps))
        self.assertEqual([r.original['return'] for r in results],[1,2])
        self.assertTrue(all(r.equal for r in results))
        self.assertEqual(results[1].candidate['state'],{'live':True})
        self.assertEqual(p.compare(b.Case('independent')).original['return'],
                         p.compare(b.Case('independent')).candidate['return'])

    def test_live_sequence_detects_later_divergence(self):
        p = self.pair('ff060010a10010cb','8306001002a10010cb')
        p.sequence_targets=frozenset()
        p.sequence_function=lambda name:p.function
        results=list(b.PreparedPair.compare_sequence(p,[('counter',b.Case('first')),
                                                        ('counter',b.Case('second'))]))
        self.assertTrue(all(not r.equal for r in results))
        self.assertIn('nonstack_memory',results[-1].diff)

    def test_live_sequence_rejects_fixture_reinitialization(self):
        p=self.pair('cb')
        p.sequence_targets=frozenset()
        p.sequence_function=lambda name:p.function
        for case in (b.Case('reinit',writes=[(0x1000,b'x')]),b.Case('reinit',state={'bad':True})):
            with self.assertRaisesRegex(b.ExecutionError,'cannot reinitialize'):
                list(b.PreparedPair.compare_sequence(p,[('entry',b.Case('first')),('entry',case)]))

    def test_all_nonstack_writes_observed_without_named_ranges(self):
        # mov ax,N; mov [es:1000],ax; retf.
        r = self.pair('b8010026a30010cb','b8020026a30010cb').compare(b.Case('write'))
        self.assertIn('nonstack_memory',r.diff)

    def test_stack_dead_store_is_outside_contract(self):
        r = self.pair('b80100cb','558becc746fe34125db80100cb').compare(b.Case('dead-local'))
        self.assertTrue(r.equal)

    def test_shared_stack_data_segment_does_not_hide_global_writes(self):
        r = self.pair('b8010026a30010cb','b8020026a30010cb').compare(
            b.Case('shared-ss-ds', registers={'ss': b.match.DGROUP_SEG}))
        self.assertIn('nonstack_memory', r.diff)

    def test_old_stack_segment_can_be_observable_heap(self):
        r = self.pair('b80100bb00808ec326a30010cb',
                      'b80200bb00808ec326a30010cb').compare(b.Case('old-stack-as-heap'))
        self.assertIn('nonstack_memory', r.diff)

    def test_fixture_cannot_alias_reserved_stack(self):
        p = self.pair('cb')
        with self.assertRaisesRegex(b.ExecutionError, 'overlaps reserved call stack'):
            p.compare(b.Case('stack-alias', writes=[(b.match.DGROUP_SEG*16+0xA000,b'bad')]))

    def cursor_program(self, cursor, remaining, base):
        # Invented stream writes used only to test typed-view plumbing.
        values=(cursor,b.match.DGROUP_SEG,remaining,base,b.match.DGROUP_SEG)
        return ''.join('c706'+(0x8E06+i*2).to_bytes(2,'little').hex()+v.to_bytes(2,'little').hex()
                       for i,v in enumerate(values))+'cb'

    def cursor_case(self, root):
        rel='evidence/behavior/runtime/unit-cursor.json'
        path=root/rel;path.parent.mkdir(parents=True)
        raw=json.dumps({'schema':'behavior-format-cursor-proof-v1',
            'oracle_sha256':b.exe.load().sha256,'review':{'status':'APPROVED','reviewer':'root'},
            'records':[{'name':'unit-cursor','address':b.match.DGROUP_SEG*16+0x8E06,
                        'size':10,'private_owner':'sprintf.c','overwrite_before_read_proven':True}]}).encode()
        path.write_bytes(raw)
        return b.Case('typed-cursor',format_cursor_views=[b.FormatCursorView('unit-cursor',
            b.match.DGROUP_SEG*16+0x8E06,rel,b.digest(raw))])

    def test_formatter_view_preserves_raw_difference_and_cursor_advance(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(b,'ROOT',Path(folder)):
            case=self.cursor_case(Path(folder))
            p=self.pair(self.cursor_program(0xA3C7,0x7FFC,0xA3C4),
                        self.cursor_program(0xA3BB,0x7FFC,0xA3B8))
            result=p.compare(case)
            self.assertTrue(result.equal)
            self.assertTrue(result.implementation_differences['raw_nonstack_memory'])
            self.assertEqual(result.original['private_formatter_views']['unit-cursor']['cursor_advance'],3)
            p=self.pair(self.cursor_program(0xA3C7,0x7FFC,0xA3C4),
                        self.cursor_program(0xA3BC,0x7FFB,0xA3B8))
            self.assertFalse(p.compare(case).equal)

    def test_formatter_view_cannot_hide_unrelated_global_or_escaped_pointer(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(b,'ROOT',Path(folder)):
            case=self.cursor_case(Path(folder))
            original=self.cursor_program(0xA3C7,0x7FFC,0xA3C4)
            candidate=self.cursor_program(0xA3BB,0x7FFC,0xA3B8)
            candidate=candidate[:-2]+'c70600104200cb'
            self.assertIn('nonstack_memory',self.pair(original,candidate).compare(case).diff)
            result=self.pair(original,self.cursor_program(0x1003,0x7FFC,0x1000)).compare(case)
            self.assertIn('nonstack_memory',result.diff)
            self.assertIn('private_formatter_views',result.diff)

    def test_formatter_heap_record_keeps_pointer_bytes_observable(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(b,'ROOT',Path(folder)):
            case=self.cursor_case(Path(folder))
            result=self.pair(self.cursor_program(0x1003,0x7FFC,0x1000),
                             self.cursor_program(0x2003,0x7FFC,0x2000)).compare(case)
            self.assertIn('nonstack_memory',result.diff)
            self.assertEqual(result.original['private_formatter_views'],{})
            equal=self.pair(self.cursor_program(0x1003,0x7FFC,0x1000)).compare(case)
            self.assertTrue(equal.equal)

    def test_formatter_view_requires_unchanged_reviewed_proof(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(b,'ROOT',Path(folder)):
            case=self.cursor_case(Path(folder))
            (Path(folder)/case.format_cursor_views[0].proof_path).write_text('{}')
            with self.assertRaisesRegex(b.ExecutionError,'proof changed'):
                self.pair(self.cursor_program(0xA3C7,0x7FFC,0xA3C4)).compare(case)

    def test_abi_fault_fails_even_if_both_sides_do_same_fault(self):
        for code in ('be0100cb','ca0200'):
            with self.subTest(code=code), self.assertRaisesRegex(b.ExecutionError,'ABI violated'):
                self.pair(code).compare(b.Case('bad-abi'))

    def test_explicit_callee_cleanup_is_supported(self):
        self.assertTrue(self.pair('ca0200').compare(b.Case('pascal',args=[7],callee_pop=2)).equal)

    def test_reset_restores_case_initialization_and_program_writes(self):
        p = self.pair('26a10010cb')
        base = b.match.DGROUP_SEG*16+0x1000
        initial = p.original_machine.read(base,2)
        p.compare(b.Case('first',writes=[(base,b.words(0x4321))]))
        r = p.compare(b.Case('next'))
        self.assertTrue(r.equal)
        self.assertEqual(p.original_machine.read(base,2),initial)

    def test_out_order_detected(self):
        r = self.pair('b001e605b002e605cb','b002e605b001e605cb').compare(b.Case('out',return_kind='void'))
        self.assertIn('io',r.diff)

    def test_unmodeled_in_and_interrupt_fail_closed(self):
        for code, reason in [('e405cb','unmodeled IN'),('cd21cb','unmodeled interrupt')]:
            with self.subTest(code=code),self.assertRaisesRegex(b.ExecutionError,reason):
                self.pair(code).compare(b.Case('host'))

    def test_modeled_callback_state_is_fresh_and_abi_checked(self):
        # Far call invented helper 7100:0000, then retf.
        p = self.pair('9a00000071cb')
        def cb(m,args):
            m.state['values'].append(len(m.state['values']))
            return 3
        c = b.Case('callback',state={'values':[]},callbacks={'fixture':b.Callback(0,cb)})
        with patch.object(b,'symbol',return_value={'seg':0x7100,'off':0,'unit':'root'}):
            self.assertTrue(p.compare(c).equal)
            self.assertTrue(p.compare(c).equal)
            c.callbacks['fixture'] = b.Callback(0,cb,pop=2)
            with self.assertRaises(b.ExecutionError):
                p.compare(c)

    def test_watch_callback_executes_real_helper(self):
        p = self.pair('9a00000071cb',helper='b84200cb')
        c = b.Case('watch',callbacks={'fixture':b.Callback(0)})
        with patch.object(b,'symbol',return_value={'seg':0x7100,'off':0,'unit':'root'}):
            r = p.compare(c)
        self.assertTrue(r.equal)
        self.assertEqual(r.original['return'],0x42)
        self.assertEqual(len(r.original['trace']),1)

    def test_intermediate_global_difference_before_callback_detected(self):
        # Both finally restore the global and return 3; callback sees a difference.
        tail = '26a300109a00000071b8000026a30010b80300cb'
        p = self.pair('b80100'+tail,'b80200'+tail)
        c = b.Case('intermediate',callbacks={'fixture':b.Callback(0,lambda m,a:None)})
        with patch.object(b,'symbol',return_value={'seg':0x7100,'off':0,'unit':'root'}):
            r = p.compare(c)
        self.assertIn('trace',r.diff)
        self.assertNotIn('return',r.diff)
        self.assertNotIn('nonstack_memory',r.diff)

    def test_overlapping_overlay_is_restored_after_interrupted_case(self):
        p = self.pair('cb')
        m = p.original_machine
        x = b.exe.load()
        base,data = x.unit_bytes('S25')
        m.cpu.mem_write(base,data)
        m.loaded_units = {'S25'}
        m.set_reg('ss',b.STACK_SEG); m.set_reg('sp',0xF000)
        m.cpu.mem_write(b.STACK_SEG*16+0xF000,b.words(0x1234,0x7000))
        m._load_overlay('S22')
        self.assertTrue(m.overlay_frames)
        self.assertNotEqual(m.read(base,len(data)),data)
        m._reset()
        self.assertEqual(m.read(base,len(data)),data)
        self.assertEqual(m.loaded_units,{'S25'})
        self.assertFalse(m.overlay_frames)


if __name__ == '__main__': unittest.main()
