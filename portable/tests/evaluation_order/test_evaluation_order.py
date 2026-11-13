from pathlib import Path
from collections import Counter
import json
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'portable'))
from canonical_native_abi import integer_frontend as f,evaluation_order as e
from pycparser import c_ast as C
from portable.tests.evaluation_order.census import canonical_census,verify_census

CC='C:/msys64/mingw64/bin/gcc.exe'
PAIR='''#include <stdint.h>
extern int16_t SRand1(int16_t);
void AddRandAntLion(void) { int16_t x,y;
x = SRand1(0x40) + SRand1(0x41);
y = SRand1(0x20) + SRand1(0x21); }
'''


class CensusTests(unittest.TestCase):
    def parse(self,s):return f.c_parser.CParser().parse(s)

    def test_c_sequence_points_and_unevaluated_operands(self):
        tree=self.parse('int f(void); int g(void); int h(void); void p(int c) { f() && g(); f() || g(); c ? f() : g(); (f(),g()); sizeof(f()+g()); f(); g(); }')
        self.assertEqual([],e.census(tree))

    def test_every_unsequenced_operator_family(self):
        tree=self.parse('int f(); int g(void); void p(int **a,int *b,int i) { f()+g(); f()-g(); f(g(),g()); b[i++]=g(); a[i++][i++]; int v[2]={f(),g()}; }')
        self.assertEqual(Counter({'binary:+':1,'binary:-':1,'arguments':1,'assignment':1,'subscript':1,'initializer':1}),Counter(r['kind'] for r in e.census(tree)))

    def test_full_canonical_census_and_new_site_rejection(self):
        rows,units=canonical_census(CC);contracts=json.loads(e.CONTRACT_PATH.read_text())
        self.assertEqual(171,len(units));self.assertEqual(55,len(rows));verify_census(rows,contracts)
        with self.assertRaisesRegex(ValueError,'census changed'):verify_census(rows+[rows[0]],contracts)

    def test_frontend_rejects_uncovered_source(self):
        with self.assertRaisesRegex(ValueError,'uncovered unsequenced'):
            f.convert(PAIR,'probe.c',CC,[],canonical_source='src/graphics/font_output.c')

    def test_site_types_fail_closed(self):
        with self.assertRaisesRegex(ValueError,'type drift'):
            f.convert(PAIR.replace('extern int16_t','extern uint16_t'),'probe.c',CC,[],canonical_source='src/simulation/yard_creatures.c')

    def test_receipts_and_disabled_control(self):
        for enabled in (True,False):
            text,receipt=f.convert(PAIR,'probe.c',CC,[],canonical_source='src/simulation/yard_creatures.c',sequence_effects=enabled)
            self.assertEqual(enabled,'simant_eval_' in text)
            self.assertEqual([1,0],receipt['evaluation_order']['regions'][0]['order'])
            self.assertTrue(all(r.get('reason') for r in receipt['evaluation_order']['sites']))

    def test_scheduled_effects_preserve_laziness_types_and_store_interleaving(self):
        source='''#include <stdint.h>
int16_t trace[8], count, x, y, z;
int16_t cells[8][8];
int16_t emit(int16_t v) { trace[count++] = v; return v; }
int16_t lazy(int16_t c) { return c && (emit(1) + emit(2)); }
int16_t conditional(int16_t c) { return c ? (emit(3)+emit(4)) : emit(5); }
void stores(void) { cells[x=z][y=2]=(z=3); }
void deferred(void) { cells[0][x++]=(y=7); }
int main(void) {
 if (lazy(0)!=0 || count!=0) return 1;
 if (lazy(1)!=1 || trace[0]!=2 || trace[1]!=1) return 2;
 if (conditional(0)!=5 || count!=3) return 3;
 if (conditional(1)!=7 || trace[3]!=4 || trace[4]!=3) return 4;
 stores(); if (x!=3 || y!=2 || cells[3][2]!=3) return 5;
 x=0; deferred(); if (x!=1 || cells[0][0]!=7) return 6;
 return 0; }
'''
        pp,_=f.preprocess(source,'probe.c',CC,[]);tree=f.c_parser.CParser().parse(pp,filename='probe.c')
        a=f.Analyzer('probe.c');a.walk(tree);a.reserved_identifiers=set();a.evaluation_plans={}
        orders={'lazy':[1,0],'conditional':[1,0],'stores':[1,2,0,3],'deferred':[1,2,0]}
        for index,r in enumerate(e.regions(e.census(tree,a.active))):
            nodes=e.effects(r['_node']);plan=dict(id='test'+str(index),order=orders[r['function']])
            a.evaluation_plans[id(r['_node'])]=(plan,nodes)
        gen=f.Generator(a,{})
        text='#include <stdint.h>\n'+'\n'.join(gen.visit(n)+('' if isinstance(n,C.FuncDef) else ';') for n in tree.ext if a.active(n))
        out=ROOT/'build/workers/eval-order/unit';out.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=out) as work:
            c=Path(work)/'test.c';binary=c.with_suffix('.exe');c.write_text(text)
            result=subprocess.run([CC,'-std=c11',str(c),'-o',str(binary)],capture_output=True,text=True,timeout=30)
            self.assertEqual(0,result.returncode,result.stderr)
            result=subprocess.run([str(binary)],capture_output=True,text=True,timeout=10)
            self.assertEqual(0,result.returncode,result.stdout+result.stderr)


if __name__=='__main__':unittest.main()
