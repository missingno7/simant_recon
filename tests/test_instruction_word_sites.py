"""Instruction overrides are local, exact and fail closed on source drift."""
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'portable'))
from canonical_native_abi import integer_frontend as frontend


def analyze(source,sites):
    with patch.object(frontend,'instruction_sites',return_value=sites):
        return frontend.convert('#include <stdint.h>\n'+source,'word-sites.c',
                                'C:/msys64/mingw64/bin/gcc.exe',[],canonical_source='fixture')


SITE=dict(function='f',expression='a * 100',count=1,
          contract='unit-word-product',instructions=['IMUL word; CWD; IDIV word'])


class InstructionWordSites(unittest.TestCase):
    def test_proved_product_lowers_before_division_and_is_local(self):
        source='int16_t f(int16_t a,int16_t n) {return a*100/n;} int16_t other(int16_t a) {return a*100;}'
        out,receipt=analyze(source,[SITE])
        products=[r for r in receipt['expressions'] if r['operator']=='*']
        self.assertEqual([r['status'] for r in products],['LOWERED','UNRESOLVED'])
        self.assertEqual(products[0]['instruction_evidence'],SITE['instructions'])
        self.assertIn('int64_t',out)
        self.assertNotIn('signed-overflow-domain',products[0]['categories'])

    def test_changed_expression_and_duplicate_occurrences_fail(self):
        for expr in ('a*99','a*100+a*100'):
            with self.subTest(expr=expr),self.assertRaisesRegex(ValueError,'expression drift'):
                analyze('int16_t f(int16_t a) {return '+expr+';}',[SITE])

    def test_changed_operand_width_fails(self):
        with self.assertRaisesRegex(ValueError,'operand/type drift'):
            analyze('int32_t f(int32_t a) {return a*100;}',[SITE])

    def test_unreviewed_msc_contraction_is_still_unresolved(self):
        _,receipt=analyze('int32_t f(int16_t a) {return (a*9)/3;}',[])
        ops=[r for r in receipt['expressions'] if r['operator'] in {'*','/'}]
        self.assertTrue(all(r['status']=='UNRESOLVED' for r in ops))
        self.assertTrue(all('instruction_evidence' not in r for r in ops))


if __name__=='__main__':unittest.main()
