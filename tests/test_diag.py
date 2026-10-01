"""Strict verdicts and runtime ownership are independent of diagnostic grouping."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
import diag
import match


class TriageTests(unittest.TestCase):
    def test_runtime_primary_and_extra_segments_excluded(self):
        manifest={'modules':{'x':{'claims':[{'unit':'root','seg':1,'off':0}]}},
                  'runtime':{'members':[{'linear':32,'size':4,
                                        'extra_segments':[{'linear':48,'size':4}]}]}}
        rows=[{'unit':'root','seg':i,'off':0} for i in range(1,5)]
        rows.append({'unit':'S00','seg':2,'off':0})
        with patch.object(diag.modules,'load_manifest',return_value=manifest), \
             patch.object(diag.functions,'table',return_value={'functions':rows}), \
             patch.object(diag.functions,'name_of',side_effect=lambda u,s,o:f'{u}:{s}'):
            self.assertEqual(diag.open_functions(),['root:4','S00:2'])

    def test_failed_decoder_preserves_strict_verdict(self):
        ctx=SimpleNamespace(text='void f(void) {}',key='root:1',profile='test',flags=[],claims=[],
                            module_dict=lambda:{},function=lambda n:{})
        verdict={'compile_ok':True,'exact':False,'claims':{'f':{'exact':False,'reasons':['wrong bytes']}}}
        def verify(*args,**kwargs):
            kwargs['collect']['object']=b'fixture'
            return verdict
        with tempfile.TemporaryDirectory() as d, \
             patch.object(diag.modctx,'resolve',return_value=ctx), \
             patch.object(diag.variants,'check_set',return_value=[]), \
             patch.object(diag.modules,'verify_module',side_effect=verify), \
             patch.object(diag.modctx,'read_obj',return_value=None), \
             patch.object(diag.modctx,'bind_function',return_value=(SimpleNamespace(unbound=[],original=b'',candidate=b''),None)), \
             patch.object(diag.mismatch,'compare_streams',side_effect=ValueError('decoder unavailable')):
            row=diag.analyze_module(['f'],Path(d))[0]
        self.assertFalse(row['strict_target_exact'])
        self.assertFalse(row['strict_module_exact'])
        self.assertEqual(row['reasons'],['wrong bytes'])
        self.assertIn('decoder unavailable',row['diagnostic_error'])

    def test_longer_identical_prefix_is_reported_as_incomplete_and_rejected(self):
        self.check_extent(b'\x55\xcb\xcc', 3, 2, False)

    def test_shorter_candidate_keeps_actual_extent(self):
        self.check_extent(b'\x55', 1, 1, False)

    def test_complete_equal_payload_is_distinguished(self):
        self.check_extent(b'\x55\xcb', 2, 2, True)

    def check_extent(self, candidate, extent_size, compared_size, exact):
        oracle = SimpleNamespace(unit_bytes=lambda u:(0,b'\x55\xcb'), unit_relocs=lambda u:[])
        obj = SimpleNamespace(segments={'CODE':candidate},
                              publics=[{'name':'_f','segment':'CODE','offset':0}], linker_fixups=[])
        with patch.object(match.exemod,'load',return_value=oracle):
            bound = match.Binder(match.Target('root',0,0,2),obj,'CODE','_f').bind()
        self.assertEqual(bound.exact, exact)
        self.assertEqual(bound.candidate_extent_size, extent_size)
        self.assertEqual(len(bound.candidate), compared_size)
        if extent_size != 2:
            self.assertIn(f'length {extent_size} != target 2',bound.reasons)
        ctx=SimpleNamespace(text='void f(void) {}',key='root:0',profile='test',flags=[],claims=[],
                            module_dict=lambda:{},function=lambda n:{'size':2})
        verdict={'compile_ok':True,'exact':exact,
                 'claims':{'f':{'exact':exact,'reasons':bound.reasons}}}
        def verify(*args,**kwargs):
            kwargs['collect']['object']=b'fixture'
            return verdict
        with tempfile.TemporaryDirectory() as d, \
             patch.object(diag.modctx,'resolve',return_value=ctx), \
             patch.object(diag.variants,'check_set',return_value=[]), \
             patch.object(diag.modules,'verify_module',side_effect=verify), \
             patch.object(diag.modctx,'read_obj',return_value=obj), \
             patch.object(diag.modctx,'bind_function',return_value=(bound,None)):
            row=diag.analyze_module(['f'],Path(d))[0]
            report=json.loads(Path(row['full_diagnostic']).read_text())
        self.assertEqual(row['strict_target_exact'],exact)
        self.assertEqual(row['strict_module_exact'],exact)
        self.assertEqual(row['candidate_bytes'],extent_size)
        self.assertEqual(row['compared_candidate_bytes'],compared_size)
        self.assertEqual(row['candidate_payload_complete'],extent_size==compared_size)
        self.assertEqual(report['function_extent']['candidate_bytes'],extent_size)
        self.assertIn(f'Function extents target/candidate: 2/{extent_size}',row['summary'])
        if extent_size > compared_size:
            self.assertIn('Candidate tail is outside',row['summary'])

    def test_alignment_pad_stays_outside_accepted_extent(self):
        oracle=SimpleNamespace(unit_bytes=lambda u:(0,b'\x55\x5d\xcb'),unit_relocs=lambda u:[])
        obj=SimpleNamespace(segments={'CODE':b'\x55\x5d\xcb\x90'},
                            publics=[{'name':'_f','segment':'CODE','offset':0}],linker_fixups=[])
        with patch.object(match.exemod,'load',return_value=oracle):
            bound=match.Binder(match.Target('root',0,0,3),obj,'CODE','_f').bind()
        self.assertTrue(bound.exact)
        self.assertEqual(bound.candidate_extent_size,3)
        self.assertEqual(len(bound.candidate),3)

if __name__=='__main__':
    unittest.main()
