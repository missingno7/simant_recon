from pathlib import Path
import json,subprocess,sys,unittest,tempfile
ROOT=Path(__file__).resolve().parents[3];sys.path[:0]=[str(ROOT),str(ROOT/'portable')]
from canonical_native_abi import integer_frontend as f,uninitialised_locals as u
from portable.tests.uninitialised_locals.census import canonical_census
from pycparser import c_parser
CC='C:/msys64/mingw64/bin/gcc.exe'
EVIDENCE=ROOT/'evidence/canonical/uninitialised-locals/census.json'
class CensusTests(unittest.TestCase):
    def scan(self,source):return u.census(c_parser.CParser().parse(source))[0]
    def test_scalar_member_array_and_address_blind_spot(self):
        rows=self.scan('void use(int*); int f(void){ int x; int a[2]; struct P{int x,y;} p; a[0]=2;p.x=1;use(&x);return a[1]+p.y+x; }')
        self.assertEqual({'x','a[1]','p.y'},{r['object'] for r in rows})
        self.assertIn('address-exposure',{r['kind'] for r in rows})
    def test_typedef_pointer_store_reads_pointer_and_queue_count_is_not_boolean_success(self):
        self.assertTrue(self.scan('typedef int *Handle; void f(){Handle h;h[0]=1;}'))
        self.assertTrue(self.scan('int input_pop_event(int*);int f(){int x;if(input_pop_event(&x))return x;return 0;}'))
    def test_definite_stores_gotos_and_switch_fallthrough(self):
        self.assertEqual([],self.scan('int f(int k){int x; switch(k){case 0:x=1;break;default:x=2;} goto out; out:return x;}'))
        self.assertEqual([],self.scan('int f(int k){int x; do{x=2;}while(k);return x;}'))
        self.assertTrue(self.scan('int f(int k){int x;while(k){x=2;}return x;}'))
    def test_short_circuit_and_unevaluated_operand(self):
        self.assertEqual([],self.scan('int g(void); int f(int k){int x;if(k&&(x=g())>0)return x;return sizeof(x);}'))
        self.assertTrue(self.scan('int f(int k){int x;k&&(x=2);return x;}'))
    def test_partial_aggregate_does_not_become_complete(self):
        self.assertTrue(self.scan('void use(void*);void f(){struct P{int x,y;} p;p.x=1;use(&p);}'))
        self.assertEqual([],self.scan('void use(void*);void f(){struct P{int x,y;} p;p.x=1;p.y=2;use(&p);}'))
    def test_changed_index_invalidates_element_fact(self):
        self.assertTrue(self.scan('int f(){int a[3],i;i=0;a[i]=1;i++;return a[i];}'))
    def test_canonical_census_and_rejection(self):
        expected=json.loads(EVIDENCE.read_text());rows,units=canonical_census(CC)
        u.verify(rows,expected['sites'])
        self.assertEqual(units,expected['units'])
        with self.assertRaisesRegex(ValueError,'unclassified'):u.verify(rows+rows[:1],expected['sites'])
    def test_reference_conversion_and_disabled_control(self):
        source='int32_t stamp; void f(){WaitedEnough(&stamp, 0x48);}'
        text,receipt=u.adapt_reference_residue(source,'src/startup/main.c')
        self.assertIn('stamp = 2145517568L',text)
        self.assertEqual(0x7fe20000,receipt['reference_value'])
        self.assertEqual(source,u.adapt_reference_residue(source,'src/startup/main.c',False)[0])
        with self.assertRaisesRegex(ValueError,'anchor drift'):u.adapt_reference_residue(source.replace('stamp;','other;'),'src/startup/main.c')
    def test_actual_waited_enough_negative_native_residue(self):
        # Compile the canonical body with the port's scalar declaration widths.
        # No test executes an indeterminate native C read: the disabled value is
        # the concrete negative residue observed in the original GDB failure.
        from canonical_native_abi import scalar
        source=(ROOT/'src/window/alerts.c').read_text(encoding='latin1')
        body=source[source.index('\nint far WaitedEnough(long far *timer, int delay)\n{'):]
        body=body[:body.index('\n}')+2];body=scalar.convert(body)
        code='''#include <stdint.h>
static int calls;
int32_t TickCount(void){return 100 + calls++;}
'''+body+'''
int main(void){int32_t reference=2145517568L, native=-1373232089L;
calls=0;if(WaitedEnough(&reference,72)!=1||calls!=2||reference!=101)return 1;
calls=0;if(WaitedEnough(&native,72)!=1||calls!=3||native!=102)return 2;
return 0;}
'''
        out=ROOT/'build/workers/uninit/unit';out.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=out) as d:
            p=Path(d)/'control.c';p.write_text(code);exe=p.with_suffix('.exe')
            for opt in ('-O0','-O2'):
                r=subprocess.run([CC,opt,str(p),'-o',str(exe)],capture_output=True,text=True,timeout=30);self.assertEqual(0,r.returncode,r.stderr)
                r=subprocess.run([str(exe)],capture_output=True,text=True,timeout=10);self.assertEqual(0,r.returncode,r.stdout+r.stderr)
if __name__=='__main__':unittest.main()
