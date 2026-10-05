"""Closed expression types must determine edits, independent of function names."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'portable'))
from canonical_native_abi import word_islands


class NativeWordExpressions(unittest.TestCase):
    def test_complete_addition_owns_comparison_rhs_and_nested_wraps(self):
        source = 'if ((unsigned)a + 2 <= (unsigned)b) use();'
        output, receipt = word_islands.convert(source)
        self.assertEqual(output, 'if (((uint16_t)((unsigned)a + 2)) <= (unsigned)b) use();')
        self.assertEqual([row['source'] for row in receipt['operators']], ['(unsigned)a + 2'])
        nested, receipt = word_islands.convert('result = ((unsigned)next() + 2) - 0x100;')
        self.assertEqual(nested.count('next()'), 1)
        self.assertEqual(len(receipt['operators']), 2)
        compared, receipt = word_islands.convert('result = (unsigned)a < (int)b;')
        self.assertEqual(compared, 'result = ((uint16_t)((unsigned)a) < (uint16_t)((int)b));')
        self.assertEqual(receipt['operators'][0]['action'], 'word-comparison-operands')

    def test_unknown_types_long_peers_and_opaque_regions_do_not_gain_word_types(self):
        for source in ('(unsigned)a + unknown <= (unsigned)b',
                       '(unsigned)a + 2L <= (unsigned)b',
                       '(unsigned)a * 2 <= (unsigned)b',
                       '(unsigned)a << 2 <= (unsigned)b',
                       '(int)a + 2 < (int)b',
                       '(unsigned char)a + 2 < (unsigned char)b',
                       '(unsigned)a >= 0',
                       '#define ADD(x) ((unsigned)(x) + 2)\n',
                       '_asm { mov ax,2 }\n'):
            with self.subTest(source=source):
                output, receipt = word_islands.convert(source)
                self.assertEqual(output, source)
                self.assertEqual(receipt['operators'], [])
        self.assertEqual(word_islands.literal_type('32768')[0], 's32')
        self.assertEqual(word_islands.literal_type('0x8000')[0], 'u16')


if __name__ == '__main__':
    unittest.main()
