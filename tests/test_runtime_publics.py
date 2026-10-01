"""Historical data-only member acceptance must keep independent public anchors.

Controls use the actual pinned syserr.c object: neither removing an anchor,
moving one public nor moving both publics can make incorrect data acceptable.
"""
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import match
import runtime


class RegisteredRuntimePublics(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.results, cls.derived, _, _ = runtime.verify_all()

    def syserr(self):
        return [r for r in runtime.verify_data(self.results, self.derived)
                if r["member"] == "syserr.c"]

    def test_exact_pinned_member(self):
        rows = self.syserr()
        self.assertEqual(len(rows), 1)
        self.assertTrue(rows[0]["exact"], rows)
        self.assertEqual((rows[0]["linear"], rows[0]["size"], rows[0]["rule"]),
                         (0x5D70E, 462, "REGISTERED_PUBLICS"))

    def test_missing_or_conflicting_anchor(self):
        lookup = match.obj_name_lookup
        for missing in (True, False):
            def altered(name):
                r = lookup(name)
                if name == "_sys_nerr":
                    return None if missing else {**r, "off": r["off"] + 2}
                return r
            with self.subTest(missing=missing), mock.patch.object(match, "obj_name_lookup", altered):
                rows = self.syserr()
                self.assertEqual(len(rows), 1)
                self.assertFalse(rows[0]["exact"], rows)
                self.assertIn("no symbolic placement", rows[0]["reasons"][0])

    def test_agreeing_wrong_placement_still_fails_bytes(self):
        lookup = match.obj_name_lookup
        def shifted(name):
            r = lookup(name)
            return {**r, "off": r["off"] + 2} if name in ("_sys_nerr", "_sys_errlist") else r
        with mock.patch.object(match, "obj_name_lookup", shifted):
            rows = self.syserr()
            self.assertFalse(rows[0]["exact"], rows)
            self.assertTrue(any("bytes differ" in r for r in rows[0]["reasons"]), rows)


if __name__ == "__main__":
    unittest.main()
