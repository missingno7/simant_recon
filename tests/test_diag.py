"""Strict verdicts and runtime ownership are independent of diagnostic grouping."""
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
import diag


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

if __name__=='__main__':
    unittest.main()
