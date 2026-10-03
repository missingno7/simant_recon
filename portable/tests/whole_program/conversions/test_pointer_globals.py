from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from portable.whole_program.conversions.pointer_globals import adapt


class PointerGlobalsConversionTests(unittest.TestCase):
    def source(self, relative: str) -> str:
        return (ROOT / relative).read_text(encoding="utf-8")

    def test_proved_table_declarations_share_native_owner(self):
        for path, token in [
            ("src/root/m20E8.c", "win_handles"),
            ("src/root/m23AE.c", "win_handles"),
            ("src/root/m22BF.c", "win_handles"),
            ("src/root/m2505.c", "win_handles"),
            ("src/root/m1A53.c", "db_handles"),
        ]:
            original = self.source(path)
            converted, ledger = adapt(path, original)
            self.assertIsNotNone(ledger)
            self.assertIn("pointer_globals.h", converted)
            self.assertNotIn("extern char far * far * near win_handles[];", converted)
            if token == "db_handles":
                self.assertNotIn("extern int far db_handles[];", converted)

    def test_font_selector_has_one_typed_source_owner(self):
        converted, ledger = adapt("src/root/m24AB.c", self.source("src/root/m24AB.c"))
        self.assertIsNotNone(ledger)
        self.assertEqual(converted.count("struct Font *fd_55B3_65A4 = 0;"), 1)
        self.assertNotIn("extern void far *fd_50F6_4A1A[];", converted)
        peer, peer_ledger = adapt("src/root/m1629.c", self.source("src/root/m1629.c"))
        self.assertIsNotNone(peer_ledger)
        self.assertNotIn("extern void far * far fd_55B3_65A4;", peer)

    def test_changed_source_shape_fails_closed(self):
        with self.assertRaises(ValueError):
            adapt("src/root/m24AB.c", self.source("src/root/m24AB.c").replace(
                "void far *fd_55B3_65A4 = 0;", "void far *some_other_pointer = 0;"))


if __name__ == "__main__":
    unittest.main()
