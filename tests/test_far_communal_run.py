"""The named far data at 50F6:01FE..10C1 fits one MSC emission run (rule COMDEF-1).

A recovered name with the wrong spelling, or a wrong address, in this range would add a
checksum descent, so this also checks every name there against the original layout.
"""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools' / 'research'))
import communal_runs as c


class FarCommunalRun(unittest.TestCase):
    def test_named_objects_form_exactly_64_checksum_runs(self):
        rows = c.objects()
        named = [name for _, name, ok in rows if ok]
        self.assertGreaterEqual(len(named), 268)
        self.assertEqual(c.run_count(named), 64)

    def test_every_unnamed_object_has_a_bucket_constraint(self):
        for row in c.buckets(c.objects()):
            if row['bucket'] is None:
                lo, hi = row['bucket_range']
                self.assertLessEqual(lo, hi)
                self.assertLessEqual(hi - lo, 1, row)


if __name__ == '__main__':
    unittest.main()
