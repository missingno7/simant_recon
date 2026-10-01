import struct
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import rtlink


class RTLinkSectionFormatTests(unittest.TestCase):
    def fixture(self, size):
        raw = bytearray(0x100)
        raw[:2] = b'MZ'
        struct.pack_into('<H', raw, 8, 2)
        # Deliberately use header/count offsets different from both historical
        # releases; the parser must follow the published pointers.
        struct.pack_into('<HHB', raw, 0x30, 0x18, 0x40, size)
        struct.pack_into('<H', raw, 0x38, 2)
        for i, fpos in enumerate((0xA0, 0xD0)):
            at = 0x60 + size * i
            struct.pack_into('<HHHBBHHHH', raw, at, 0x100, 0, fpos // 16, 0, 4, 2, 1, 0xFFFF, i + 2)
            if size == 18:
                struct.pack_into('<H', raw, at + 16, 2)
        return raw, '0000:0010 Res $$OVLPBLOCK'

    def test_old_and_new_formats_follow_parameter_block(self):
        for size in (16, 18):
            with self.subTest(entry_size=size):
                raw, map_text = self.fixture(size)
                hdr, rows = rtlink.read_trial_sections(raw, map_text)
                self.assertEqual(hdr, 0x20)
                self.assertEqual([r['section_id'] for r in rows], [2, 3])
                self.assertEqual([r['image_start'] for r in rows], [0xB0, 0xE0])
                self.assertEqual([r['image_end'] for r in rows], [0xD0, 0x100])
                self.assertEqual(rows[0]['file_paras'], 2 if size == 18 else None)

    def test_refuses_missing_map_public_and_unsupported_record_size(self):
        raw, map_text = self.fixture(16)
        with self.assertRaisesRegex(ValueError, 'no resident'):
            rtlink.read_trial_sections(raw, '')
        raw[0x34] = 20
        with self.assertRaisesRegex(ValueError, 'entry size'):
            rtlink.read_trial_sections(raw, map_text)

    def test_refuses_truncated_table_and_out_of_file_section(self):
        raw, map_text = self.fixture(18)
        with self.assertRaisesRegex(ValueError, 'table'):
            rtlink.read_trial_sections(raw[:0x70], map_text)
        struct.pack_into('<H', raw, 0x60 + 4, 0xFFFF)
        with self.assertRaisesRegex(ValueError, 'file bounds'):
            rtlink.read_trial_sections(raw, map_text)

    def test_final_partial_paragraph_is_reported_without_filling_it(self):
        raw, map_text = self.fixture(18)
        _, rows = rtlink.read_trial_sections(raw[:-3], map_text)
        self.assertEqual(rows[-1]['image_end'], len(raw) - 3)
        self.assertEqual(rows[-1]['unwritten_final_paragraph_bytes'], 3)
        with self.assertRaisesRegex(ValueError, 'file bounds'):
            rtlink.read_trial_sections(raw[:-17], map_text)


if __name__ == '__main__':
    unittest.main()
