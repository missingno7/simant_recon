"""Consumed register-return conversions and front-end negative controls."""
from pathlib import Path
import importlib.util
import json
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'portable'))
sys.path.insert(0,str(ROOT/'tools'))
from workspace import retire
from canonical_native_abi import register_returns,scalar
spec=importlib.util.spec_from_file_location('return_census',ROOT/'portable/tests/return_abi/census.py')
census=importlib.util.module_from_spec(spec); spec.loader.exec_module(census)

class RegisterReturns(unittest.TestCase):
    def test_each_proven_definition_has_an_explicit_result(self):
        contracts=json.loads(register_returns.CONTRACT_PATH.read_text())['repairs']
        self.assertEqual({r['function'] for r in contracts},{'f_00F8_02EF','myButton','o25_3BA4_19AD'})
        for path in {r['source'] for r in contracts}:
            original=scalar.convert((ROOT/path).read_text(encoding='latin1'))
            converted,receipt=register_returns.adapt(original,path)
            self.assertEqual(len(receipt),sum(r['source']==path for r in contracts))
            for row in contracts:
                if row['source']!=path: continue
                head=next(h for h in register_returns.function_heads(converted) if h['name']==row['function'])
                function=converted[head['start']:head['end']]
                prelude='typedef short int16_t; typedef unsigned short uint16_t;\n#line 1 "test.c"\n'
                tree=census.c_parser.CParser().parse(prelude+function,filename='test.c')
                d=census.analyze(tree,'test.c',function,False)['definitions'][row['function']]
                self.assertNotEqual(d['return_type'],'void')
                self.assertFalse(d['fallthrough'] or d['bare_return'])
                returns=[n for n in census.nodes(tree) if isinstance(n,census.C.Return)]
                self.assertEqual(len(returns),1)
                if row['function']=='f_00F8_02EF':
                    self.assertEqual(census.constant(returns[0].expr),0)
                else:
                    expected={'myButton':'StillDown','o25_3BA4_19AD':'o25_3BA4_1686'}[row['function']]
                    self.assertIsInstance(returns[0].expr,census.C.FuncCall)
                    self.assertEqual(returns[0].expr.name.name,expected)

    def test_source_drift_rejected_and_unreviewed_void_not_guessed(self):
        rows=json.loads(register_returns.CONTRACT_PATH.read_text())['repairs']
        first=rows[0]
        with self.assertRaisesRegex(ValueError,'drift'):
            register_returns.adapt(first['native_before'].replace('{','{ side_effect();',1),first['source'],[first])
        source='void unknown(void) {}'
        self.assertEqual(register_returns.adapt(source,'unknown.c',rows),(source,[]))

    def test_old_void_result_is_a_frontend_violation(self):
        caller='int hook(void); int start(void) { return hook()==0; }'
        body='void hook(void) {}'
        c=census.analyze(census.c_parser.CParser().parse(caller,filename='caller.c'),'caller.c',caller,False)
        d=census.analyze(census.c_parser.CParser().parse(body,filename='callee.c'),'callee.c',body,False)['definitions']['hook']
        finding=dict(kind='native',compiled_native=True,definition=d,categories=['return-type-mismatch'],**c['calls'][0])
        self.assertEqual(len(census.unspecified_native(dict(findings=[finding]))),1)
        repaired='short hook(void) { return 0; }'
        finding['definition']=census.analyze(census.c_parser.CParser().parse(repaired,filename='callee.c'),'callee.c',repaired,False)['definitions']['hook']
        self.assertEqual(census.unspecified_native(dict(findings=[finding])),[])

    def test_indirect_table_targets_remain_in_the_unspecified_gate(self):
        source='int partial(int n) { if(n) return 1; } int (*table[1])(int)={partial}; int use(void) { return table[0](0); }'
        tree=census.c_parser.CParser().parse(source,filename='test.c')
        result=census.analyze(tree,'test.c',source,False)
        self.assertEqual(result['pointer_targets']['table'],['partial'])
        self.assertEqual(result['indirect'][0]['pointer_name'],'table')
        finding=dict(kind='native',compiled_native=True,definition=result['definitions']['partial'],categories=['unspecified-return-path'])
        self.assertEqual(len(census.unspecified_native(dict(findings=[],indirect_findings=[finding]))),1)

    def test_knr_implicit_int_and_bare_return_are_not_specified(self):
        source='old() {}\nstatic older() {}\nint bare(void) { return; }\n'
        tree=census.c_parser.CParser().parse(source,filename='test.c')
        result=census.analyze(tree,'test.c',source,True)
        self.assertEqual(result['implicit_int'],['old','older'])
        self.assertTrue(result['definitions']['old']['fallthrough'])
        self.assertTrue(result['definitions']['bare']['bare_return'])

    def test_control_flow_and_discarded_return_negative_controls(self):
        source='''int read(void); void ignored(void);
int partial(int n) { if(n) return 1; }
int full(int n) { if(n) return 1; else return 0; }
int loop(void) { for(;;) {} }
int labels(int n) { if(n) goto done; return 0; done: return 1; }
int sw(int n) { switch(n) { case 1: return 1; default: return 0; } }
int use(int n) { if(n) read(); while(n) read(); ignored(); return read(); }
'''
        tree=census.c_parser.CParser().parse(source,filename='test.c')
        result=census.analyze(tree,'test.c',source,False)
        self.assertTrue(result['definitions']['partial']['fallthrough'])
        for name in ('full','loop','labels','sw'):
            self.assertFalse(result['definitions'][name]['fallthrough'])
        self.assertEqual([r['callee'] for r in result['calls']],['read'])

if __name__=='__main__': unittest.main()
