"""Current whole-TU selection and source-based controls, with no frozen drafts."""
import json
from pathlib import Path
import sys
import unittest

ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'layout/functions.json').is_file())
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import behavior as b
import canonical
import csrc
from behavior_suites.small_contracts import midi_case


class CurrentCandidateControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out = ROOT / 'build/workers/canonical_behavior_tests'
        cls.pair = b.PreparedPair('f_284A_0138', out=cls.out / 'positive')
        cls.mutant = b.PreparedPair('f_284A_0138', out=cls.out / 'negative', mutation=(
            'return SONG(off) << 8 | SONG(off + 1);',
            'return SONG(off + 1) << 8 | SONG(off);'))

    def test_current_canonical_whole_tu_is_the_compiler_input(self):
        program = canonical.load()
        semantic = next(r for r in program['semantics'] if r['function'] == 'f_284A_0138')
        module = next(r for r in program['modules'] if r['key'] == semantic['module'])
        self.assertEqual(self.pair.source, (ROOT / module['source']).resolve())
        self.assertEqual(self.pair.identity['source_sha256'], module['source_sha256'])
        self.assertEqual(self.pair.identity['compiled_source_sha256'], module['source_sha256'])
        self.assertEqual(self.pair.identity['definition_sha256'], semantic['definition_sha256'])
        self.assertNotIn('source_override', self.pair.identity)

    def test_arbitrary_candidate_source_argument_is_removed(self):
        with self.assertRaises(TypeError):
            b.PreparedPair('f_284A_0138', source=self.pair.source)

    def test_msc_based_pointer_wrap_and_byte_order(self):
        for off in (0, 0xFFFE, 0xFFFF):
            case = midi_case(f'wrap/{off:04x}', off, 0x12, 0x34)
            case.writes.append((0xB0000, b'\x56'))
            comparison = self.pair.compare(case)
            self.assertTrue(comparison.equal, comparison.diff)
            self.assertEqual(comparison.original['return'], 0x1234)
            changed = self.mutant.compare(case)
            self.assertFalse(changed.equal)
            self.assertEqual(changed.candidate['return'], 0x3412)
            self.assertEqual(sorted(changed.diff), ['return'])

    def test_mutation_preserves_the_rest_of_the_current_module(self):
        original = self.pair.source.read_bytes().decode('latin1')
        changed = (self.out / 'negative/mutant.c').read_bytes().decode('latin1')
        a = csrc.Source(original).function('f_284A_0138')
        z = csrc.Source(changed).function('f_284A_0138')
        self.assertEqual(original[:a.body.s], changed[:z.body.s])
        self.assertEqual(original[a.body.e:], changed[z.body.e:])
        self.assertNotEqual(original[a.body.s:a.body.e], changed[z.body.s:z.body.e])
        self.assertEqual(self.mutant.identity['source_sha256'], self.pair.identity['source_sha256'])
        self.assertNotEqual(self.mutant.identity['compiled_source_sha256'], self.pair.identity['compiled_source_sha256'])


if __name__ == '__main__':
    unittest.main()
