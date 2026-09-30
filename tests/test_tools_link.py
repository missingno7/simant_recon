"""Unit tests of the whole-build harness core on a synthetic file geometry (no compiler, no oracle).

    python -m unittest discover -s build/workers/link/tests -q
"""
import struct
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import link as tl  # noqa: E402


def geometry(entries=((0x0001, 0x0004), (0x0001, 0x0010))):
    """64-byte file: 4-byte header, 2 relocation entries, 4 bytes pad, 32-byte image (unit
    'root', linear 0..32), 16-byte tail."""
    regs = [tl.Region("mz_header", 0, 4), tl.Region("mz_relocs", 4, 12, table="root"),
            tl.Region("header_pad", 12, 16), tl.Region("image", 16, 48, "root", 0), tl.Region("tail", 48, 64)]
    return tl.Geometry(64, regs, {"root": (4, list(entries), "root")}, lambda u, lin: "debt:game_code")


def oracle(entries=((0x0001, 0x0004), (0x0001, 0x0010))):
    b = bytearray(64)
    b[0:4] = b"MZ\x01\x02"
    for i, (seg, off) in enumerate(entries):
        struct.pack_into("<HH", b, 4 + 4 * i, off, seg)
    b[16:48] = bytes(range(0x40, 0x60))
    b[48:64] = b"T" * 16
    return bytes(b)


def contrib(lin, data, owner="m1", relocs=(), obj=None, cls="C"):
    return tl.Contribution(cls, owner, owner + "f", "root", lin, bytes(data), obj or owner, True, list(relocs))


class HybridTests(unittest.TestCase):
    def test_equal_and_classified(self):
        o = oracle()
        pm = tl.ProvMap(geometry())
        pm.put(16 + 8, o[24:32], "C", "m1")
        hyb, gaps, diffs = tl.finish(pm, o)
        self.assertEqual(hyb, o)
        self.assertEqual(gaps, [])
        t = pm.totals()
        self.assertEqual(t["C"], 8)
        self.assertEqual(t["FORMAT_FILL"], 4)          # generated, not copied
        self.assertEqual(t["debt:game_code"], 24)
        self.assertEqual(t["debt:common_tail"], 16)
        self.assertEqual(t["debt:mz_header"], 4)
        self.assertEqual(sum(t.values()), 64)

    def test_wrong_own_byte_pinpointed(self):
        o = oracle()
        pm = tl.ProvMap(geometry())
        bad = bytearray(o[24:32])
        bad[3] ^= 0xFF
        pm.put(24, bytes(bad), "C", "m1|f")
        hyb, _, diffs = tl.finish(pm, o)
        self.assertNotEqual(hyb, o)
        self.assertEqual(len(diffs), 1)
        self.assertIn("file 0x1b-0x1c: C m1|f", diffs[0])

    def test_overlap_refused(self):
        pm = tl.ProvMap(geometry())
        self.assertTrue(pm.put(20, b"\0" * 4, "C", "a"))
        self.assertFalse(pm.put(22, b"\0" * 4, "ASM", "b"))
        self.assertTrue(pm.overlaps and "b and a" in pm.overlaps[0])

    def test_gap_reported(self):
        g = geometry()
        g.regions = [r for r in g.regions if r.kind != "tail"]       # 16 bytes in no region
        pm = tl.ProvMap(g)
        _, gaps, _ = tl.finish(pm, oracle())
        self.assertTrue(any("GAP" in x for x in gaps))

    def test_fill_is_generated_not_copied(self):
        o = bytearray(oracle())
        o[13] = 0x55                                   # non-zero padding in the "original"
        pm = tl.ProvMap(geometry())
        hyb, _, diffs = tl.finish(pm, bytes(o))
        self.assertNotEqual(hyb, bytes(o))
        self.assertIn("FORMAT_FILL", diffs[0])

    def test_unknown_debt_category_is_gap(self):
        g = geometry()
        g.debt_of = lambda u, lin: "mystery"
        _, gaps, _ = tl.finish(tl.ProvMap(g), oracle())
        self.assertTrue(any("unknown category" in x for x in gaps))


class LinkFillTests(unittest.TestCase):
    def test_odd_end_word_fill(self):
        cs = [contrib(0, b"\1" * 5, "a"), contrib(6, b"\1" * 2, "b")]
        self.assertEqual(tl.link_fill_gaps(cs, {}), [("root", 5, 6)])

    def test_same_object_not_fill(self):
        cs = [contrib(0, b"\1" * 5, "a"), contrib(6, b"\1" * 2, "a")]
        self.assertEqual(tl.link_fill_gaps(cs, {}), [])

    def test_paragraph_and_boundary(self):
        cs = [contrib(0, b"\1" * 3, "a"), contrib(16, b"\1" * 3, "b")]
        self.assertEqual(tl.link_fill_gaps(cs, {"root": 32}), [("root", 3, 16), ("root", 19, 32)])
        self.assertEqual(tl.link_fill_gaps(cs[:1], {}, {"root": [16]}), [("root", 3, 16)])

    def test_large_gap_is_debt(self):
        cs = [contrib(0, b"\1" * 3, "a"), contrib(32, b"\1" * 3, "b")]
        self.assertEqual(tl.link_fill_gaps(cs, {}), [])


class OrderTests(unittest.TestCase):
    def test_exact(self):
        self.assertEqual(tl.order_status([(0, 1, "A"), (0, 2, "B"), (0, 3, "A")])[0], "EXACT")

    def test_grouped(self):
        # group B (fixup 2) listed before group A (fixups 1, 3): only the group order differs
        st, bad = tl.order_status([(0, 2, "B"), (0, 1, "A"), (0, 3, "A")])
        self.assertEqual((st, bad), ("GROUPED", set()))

    def test_grouped_across_objects(self):
        # two objects of one frame interleave by group; inside a group object order then FIXUPP
        items = [(0, 5, "X"), (10, 1, "X"), (0, 1, "Y"), (10, 7, "Y")]
        self.assertEqual(tl.order_status(items)[0], "GROUPED")

    def test_diff(self):
        st, bad = tl.order_status([(0, 3, "A"), (0, 1, "A")])
        self.assertEqual((st, bad), ("DIFF", {"A"}))


class RelocationTests(unittest.TestCase):
    def test_own_entry_written_with_our_frame(self):
        o = oracle()
        pm = tl.ProvMap(geometry())
        c = contrib(0x14, o[36:40], relocs=[tl.Reloc(0x14, "external:_f", 0, 0x0001)])
        pm.put(16 + 0x14, c.data, "C", "m1")
        rep = tl.place_relocations(pm, [c])
        self.assertEqual(rep["root"]["own"], 1)
        self.assertEqual(pm.img[4:8], o[4:8])          # entry 0 = site 0x14, frame 0001
        hyb, gaps, _ = tl.finish(pm, o)
        self.assertEqual(hyb, o)
        self.assertEqual(pm.totals()["debt:reloc_entry.game_code"], 4)

    def test_frame_mismatch_is_error(self):
        pm = tl.ProvMap(geometry())
        c = contrib(0x14, b"\0" * 4, relocs=[tl.Reloc(0x14, "k", 0, 0x0000)])
        tl.place_relocations(pm, [c])
        self.assertTrue(any("our frame 0000, original 0001" in e for e in pm.errors))

    def test_extra_site_is_error(self):
        pm = tl.ProvMap(geometry())
        c = contrib(0x2, b"\0" * 4, relocs=[tl.Reloc(0x2, "k", 0, 0x0000)])
        tl.place_relocations(pm, [c])
        self.assertTrue(any("not in the original tables" in e for e in pm.errors))

    def test_layout_frame_taken_and_counted(self):
        pm = tl.ProvMap(geometry())
        c = contrib(0x14, b"\0" * 4, relocs=[tl.Reloc(0x14, "k", 0, None)])
        c.segname = "_DATA"
        rep = tl.place_relocations(pm, [c])
        self.assertEqual(rep["root"]["frame_from_layout"], 1)
        self.assertEqual(rep["_layout_frames"], {"root/_DATA": ["0001"]})


class CacheTests(unittest.TestCase):
    def test_roundtrip(self):
        v = {"a": b"\1\2", ("m", 5): [(1, "k", None)], "s": {"x": [b"\0"]}}
        self.assertEqual(tl._dec(tl._enc(v)), {"a": b"\1\2", ("m", 5): [[1, "k", None]], "s": {"x": [b"\0"]}})


if __name__ == "__main__":
    unittest.main()
