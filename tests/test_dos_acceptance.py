from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from dos import acceptance


class SaveComparisonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = acceptance.save_schema()
        cls.size = cls.schema[-1][1] + cls.schema[-1][2]
        cls.offsets = {row[4]: row[1] for row in cls.schema}

    def test_schema_matches_canonical_save_layout(self):
        self.assertEqual(len(self.schema), 307)
        self.assertEqual(self.size, 48386)
        self.assertEqual(self.schema[0][4], "MapA")
        self.assertIn("fd_50F6_109C", self.offsets)

    def test_state_record_difference_fails(self):
        a = bytearray(self.size)
        b = bytearray(self.size)
        b[self.offsets["MapA"] + 7] = 1
        result = acceptance.compare_saves(bytes(a), bytes(b))
        self.assertEqual(result["status"], "DIFFERS")
        self.assertEqual(result["differences"][0]["name"], "MapA")

    def test_virtual_save_reads_records_relative_to_runtime_base(self):
        addresses = {row[4]: 0x2000 + 0x40 * i for i, row in enumerate(self.schema)}
        addresses["g_5A9C"] = 0x100
        for row in self.schema:
            if row[4].startswith("("):
                addresses[row[4][1:].split(" ")[0]] = addresses[row[4]] - int(row[4].split("+")[1].rstrip(") "))
        base = 0x8240
        memory = bytearray(0x40000)
        memory[base + 0x100:base + 0x110] = acceptance.SCREEN_CLIP_PATTERN
        memory[base + addresses["MapA"]] = 0x5A
        save = acceptance.virtual_save(bytes(memory), addresses)
        self.assertEqual(len(save), self.size)
        self.assertEqual(save[0], 0x5A)
        memory[0x30000:0x30010] = acceptance.SCREEN_CLIP_PATTERN
        with self.assertRaisesRegex(ValueError, "not unique"):
            acceptance.virtual_save(bytes(memory), addresses)

    def test_truncated_save_is_rejected(self):
        result = acceptance.compare_saves(bytes(self.size), bytes(self.size - 1))
        self.assertEqual(result["status"], "SIZE_MISMATCH")


if __name__ == "__main__":
    unittest.main()
