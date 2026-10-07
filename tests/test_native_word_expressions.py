"""Declaration typing, macro expansion, and compiler-dependent negative controls."""
import unittest
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'portable'))
from canonical_native_abi.integer_frontend import convert,literal_type


def analyze(source):
    return convert('#include <stdint.h>\n'+source,'integer-unit.c',
                   'C:/msys64/mingw64/bin/gcc.exe',[])


class NativeWordExpressions(unittest.TestCase):
    def test_declarations_members_indexes_and_macro_products(self):
        source='#define MUL(x) ((x)*257)\nstruct S { uint16_t x; }; uint16_t f(struct S *s, uint16_t i) { return MUL(s[i].x)/3; }'
        out,receipt=analyze(source)
        product=[r for r in receipt['expressions'] if r['operator']=='*']
        self.assertEqual(product[0]['msc16_type'],'u16')
        self.assertEqual(product[0]['status'],'LOWERED')
        self.assertTrue(any(r['node']=='StructRef' and r['msc16_type']=='u16' for r in receipt['expressions']))
        self.assertNotIn('MUL(',out)

    def test_msc_signed_overflow_counterexample_is_rejected(self):
        out,receipt=analyze('int32_t f(int16_t a) { return (a*9)/3; }')
        ops=[r for r in receipt['expressions'] if r['operator'] in {'*','/'}]
        self.assertTrue(all(r['status']=='UNRESOLVED' for r in ops))
        self.assertIn('signed-overflow-domain',ops[0]['categories'])
        self.assertIn('unresolved-child',ops[1]['categories'])

    def test_msc_unsigned_contraction_withholds_the_entire_product(self):
        _,receipt=analyze('uint32_t f(uint16_t a) { return (a*9)/3; }')
        ops=[r for r in receipt['expressions'] if r['operator'] in {'*','/'}]
        self.assertTrue(all(r['status']=='UNRESOLVED' for r in ops))
        self.assertIn('msc-algebra-parent',ops[0]['categories'])
        self.assertIn('msc-constant-algebra-domain',ops[1]['categories'])

    def test_byte_bounds_and_long_literal_are_mechanical_proofs(self):
        _,receipt=analyze('int32_t f(uint8_t a, uint16_t b) { return (a*127)+(b+40000); }')
        product=next(r for r in receipt['expressions'] if r['operator']=='*')
        self.assertEqual(product['status'],'PROVEN_EQUAL')
        self.assertEqual(product['msc16_bound'],[0,32385])
        self.assertEqual(literal_type('40000')[0],'s32')
        self.assertEqual(literal_type('0xffff')[0],'u16')
        self.assertEqual(literal_type('0100000')[0],'u16')
        for literal in ('4000000000','4000000000L'):
            _,receipt=analyze('int16_t f(int16_t a) { return a < '+literal+'; }')
            node=next(r for r in receipt['expressions'] if r['node']=='Constant')
            self.assertEqual((node['msc16_type'],node['native_type']),('unknown' if literal=='4000000000' else 'u32','s64'))
            self.assertEqual(node['status'],'UNRESOLVED' if literal=='4000000000' else 'LOWERED')

    def test_shift_invalid_count_and_unknown_names_stay_explicit(self):
        _,receipt=analyze('uint16_t f(uint16_t a, uint16_t b) { return (a<<b)+unknown; }')
        shift=next(r for r in receipt['expressions'] if r['operator']=='<<')
        self.assertEqual(shift['status'],'UNRESOLVED')
        self.assertIn('shift-count-domain',shift['categories'])
        self.assertGreater(receipt['counts']['UNRESOLVED'],0)

    def test_anonymous_union_and_old_style_parameters(self):
        _,receipt=analyze('struct S { union { uint16_t x; int16_t y; }; }; uint16_t f(s) struct S *s; { return s->x+2; }')
        op=next(r for r in receipt['expressions'] if r['operator']=='+')
        self.assertEqual(op['status'],'LOWERED')
        self.assertEqual(op['msc16_type'],'u16')

    def test_local_typedef_and_tag_shadowing_never_escape_their_scope(self):
        source='''typedef uint16_t Word; struct S {uint16_t x;};
        uint16_t local(void) { typedef int16_t Word; struct S {int16_t x;};
          Word a; struct S b; return a+2+b.x; }
        uint16_t global(Word a,struct S *b) { return a+2+b->x; }'''
        _,receipt=analyze(source)
        ops=[r for r in receipt['expressions'] if r['operator']=='+']
        self.assertTrue(all(r['msc16_type']=='s16' and r['status']=='UNRESOLVED' for r in ops if r['function']=='local'))
        self.assertTrue(all(r['msc16_type']=='u16' and r['status']=='LOWERED' for r in ops if r['function']=='global'))

    def test_compound_helper_rejects_effectful_address_rhs_interference(self):
        prefix='uint16_t cells[2],global; uint16_t index(void); uint16_t next(void); '
        for rhs in ('global','next()'):
            _,receipt=analyze(prefix+'void f(void) {cells[index()] /= '+rhs+';}')
            row=next(r for r in receipt['expressions'] if r['operator']=='/=')
            self.assertEqual(row['status'],'UNRESOLVED')
            self.assertIn('operand-order-domain',row['categories'])
        _,receipt=analyze(prefix+'void f(int16_t local) {cells[index()] /= local;}')
        row=next(r for r in receipt['expressions'] if r['operator']=='/=')
        self.assertEqual(row['status'],'LOWERED')

    def test_fake_offsetof_never_reaches_game_code_or_layout_assertions(self):
        prefix='#include <stddef.h>\nstruct S {int16_t a; int32_t b;}; '
        for body in ('_Static_assert(offsetof(struct S,b)==4,"layout"); int16_t f(void) {return 1;}',
                     'int16_t f(void) {_Static_assert(offsetof(struct S,b)==4,"layout"); return 1;}'):
            out,_=analyze(prefix+body)
            self.assertIn('offsetof(struct S,b)==4',out)
            self.assertNotIn('__simant_parse_only_offsetof',out)
        out,receipt=analyze(prefix+'uint16_t f(void) {return offsetof(struct S,b);}')
        self.assertIn('offsetof(struct S, b)',out)
        self.assertNotIn('__simant_parse_only_offsetof',out)
        row=next(r for r in receipt['expressions'] if r.get('intrinsic')=='offsetof')
        self.assertEqual(row['status'],'UNRESOLVED')
        self.assertIn('offsetof-layout',row['categories'])

    def test_counting_loop_and_guard_proofs_reject_mutation_and_aliases(self):
        _,receipt=analyze('int16_t f(void) { int16_t i,x; for(i=0;i<16;i++) { x=i*17; } return x; }')
        op=next(r for r in receipt['expressions'] if r['operator']=='*')
        self.assertEqual(op['status'],'PROVEN_EQUAL')
        self.assertEqual(op['msc16_bound'],[0,255])
        for body in ('i=32767; x=i*17;', 'int16_t *p=&i; x=i*17;'):
            _,receipt=analyze('int16_t f(void) { int16_t i,x; for(i=0;i<16;i++) {'+body+'} return x; }')
            op=next(r for r in receipt['expressions'] if r['operator']=='*')
            self.assertEqual(op['status'],'UNRESOLVED')
        _,receipt=analyze('int16_t f(int16_t x) { if(x>=0 && x<100) return x*127; return 0; }')
        op=next(r for r in receipt['expressions'] if r['operator']=='*')
        self.assertEqual(op['status'],'PROVEN_EQUAL')

    def test_switch_goto_and_while_never_reuse_stale_local_constants(self):
        bodies=('int16_t x=1; while(c) { x=x*127; }',
                'int16_t x=1; switch(c) {case 0: x=30000; break; default: x=x*127;}',
                'int16_t x=1; again: x=x*127; if(c) goto again;')
        for body in bodies:
            _,receipt=analyze('int16_t f(int16_t c) {'+body+' return 0;}')
            op=next(r for r in receipt['expressions'] if r['operator']=='*')
            self.assertEqual(op['status'],'UNRESOLVED')

    def test_static_state_mutable_loop_limits_and_compound_invalid_domains(self):
        bodies=('static int16_t x=1; return x++*127;',
                'int16_t i,limit=16,x=0; for(i=0;i<limit;i++) {limit=30000; x=i*127;} return x;',
                'int16_t i,x=0; for(i=0;i<i+16;i++) {x=i*127;} return x;')
        for body in bodies:
            _,receipt=analyze('int16_t f(void) {'+body+'}')
            op=next(r for r in receipt['expressions'] if r['operator']=='*')
            self.assertEqual(op['status'],'UNRESOLVED')
        for op,category in (('/=','division-overflow-domain'),('%=','division-overflow-domain'),('<<=','shift-negative-domain')):
            _,receipt=analyze('int16_t f(int16_t x,int16_t y) { x'+op+'y; return x; }')
            row=next(r for r in receipt['expressions'] if r['operator']==op)
            self.assertEqual(row['status'],'UNRESOLVED')
            self.assertIn(category,row['categories'])


if __name__=='__main__':unittest.main()
