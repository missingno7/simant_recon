import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import codecfg
import hardtail


class SwitchRecognitionTests(unittest.TestCase):
    # Guarded two-entry table at +15; both destinations are RETs at +19/+20.
    def fixture(self, base=0):
        return (bytes.fromhex('3d01007602eb0d d1e0 93 2effa7'.replace(' ', '')) +
                (base+15).to_bytes(2, 'little') +
                (base+19).to_bytes(2, 'little') + (base+20).to_bytes(2, 'little') + b'\xc3\xc3')

    def test_guarded_word_table_and_all_case_edges(self):
        value = codecfg.decode(self.fixture())
        self.assertTrue(value['complete'])
        self.assertEqual(value['tables'][0]['targets'], [19, 20])
        self.assertEqual(sum(len(bytes.fromhex(r['bytes'])) for r in value['instructions']), 17)
        graph = hardtail.cfg(value['instructions'], len(self.fixture()), value['tables'])
        self.assertTrue(graph['complete'])
        self.assertEqual([e['case_index'] for e in graph['edges'] if e['kind'] == 'switch'], [0, 1])

    def test_real_segment_offsets_translate_without_trimming(self):
        value = codecfg.decode(self.fixture(0x600), 0x600)
        self.assertTrue(value['complete'])
        self.assertEqual(value['covered_bytes'], len(self.fixture()))
        self.assertEqual(value['tables'][0]['start'], 15)

    def test_out_of_range_table_target_is_not_recognized(self):
        data = bytearray(self.fixture())
        data[15:17] = b'\xff\xff'
        self.assertEqual(codecfg.decode(data)['tables'], [])

    def test_wrong_bound_or_unguarded_indirect_jump_stays_unknown(self):
        data = bytearray(self.fixture())
        data[1] = 7
        self.assertEqual(codecfg.decode(data)['tables'], [])
        unguarded = codecfg.decode(bytes.fromhex('2effa70f00c3'))
        graph = hardtail.cfg(unguarded['instructions'], 6)
        self.assertFalse(graph['complete'])


if __name__ == '__main__':
    unittest.main()
