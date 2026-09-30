"""Positive and negative controls for DGROUP-only data modules (data:55B3@OFF), near link order
and alignment link fill, the runtime data rules ENDCODE / BRACKETED / COMDEF_ANCHORS, runtime
data registrations and the compile-only FAR_BSS declaration probes (pinned MSC 6.00 / 6.00AX)."""
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import exe  # noqa: E402
import match  # noqa: E402
import modules  # noqa: E402

DG = match.DGROUP_SEG
VERSION = 'char g_0042[] = "Ver 1.00 Fri Dec 06 14:51:14 1991";\n'
NEAR_MODULE = {"unit": "data", "seg": DG, "origin": 0x42, "profile": "msc600", "flags": ["/AL", "/Os"],
               "placements": {"_DATA": {"seg": DG, "off": 0x42, "size": 34}}, "link_after": ""}
_lookup = match.obj_name_lookup


def registered(name):
    """g_0042 as registered by the install step, independent of layout/symbols.json."""
    return {"kind": "data", "seg": DG, "off": 0x42} if name == "_g_0042" else _lookup(name)


def man_with(**mods):
    rt = {"members": [{"member": "chksum.asm", "data_segments": [
        {"segment": "NULL", "linear": DG * 16, "size": 66, "rule": "DOSSEG_BEGDATA"}]}]}
    return {"modules": mods, "runtime": rt}


class NearDataModule(unittest.TestCase):
    def test_keys(self):
        self.assertEqual(modules.parse_key("data:55B3@0042"), ("data", DG, 0x42))
        self.assertEqual(modules.parse_key("data;55B3@0042"), ("data", DG, 0x42))       # MSYS-mangled
        self.assertEqual(modules.module_key("data", DG, 0x42), "data:55B3@0042")
        self.assertEqual(modules.module_source("data", DG, 0x42, "c"), "src/data/d55B3_0042.c")
        self.assertEqual(modules.module_source("data", 0x3D57, None, "c"), "src/data/d3D57.c")
        for bad in ("data:55B3", "data:3D57@0042"):
            with self.assertRaises(SystemExit):
                modules.parse_key(bad)

    def test_positive_and_wrong_byte(self):
        with mock.patch.object(match, "obj_name_lookup", registered):
            res = modules.verify_module(VERSION, NEAR_MODULE, [])
            self.assertTrue(res["exact"], res)
            self.assertFalse(res["data"]["_DATA"]["far"])
            bad = modules.verify_module(VERSION.replace("1.00", "1.01"), NEAR_MODULE, [])
            self.assertIn("data bytes differ", bad["data"]["_DATA"]["reasons"])

    def test_key_must_match_placement(self):
        with mock.patch.object(match, "obj_name_lookup", registered):
            res = modules.verify_module(VERSION, dict(NEAR_MODULE, origin=0x44), [])
            self.assertTrue(any("key origin 0044" in r for r in res["module_reasons"]), res)
            far = dict(NEAR_MODULE, placements={**NEAR_MODULE["placements"],
                                                "UNIT5_DATA": {"seg": 0x3D57, "off": 0, "size": 0}})
            self.assertTrue(any("keyed by its first far frame" in r
                                for r in modules.data_module_reasons(SimpleNamespace(segment_defs=[]), far, [])))

    def test_unregistered_public(self):
        res = modules.verify_module(VERSION.replace("g_0042", "Version"), NEAR_MODULE, [])
        self.assertTrue(any("_Version" in r and "not a registered" in r for r in res["module_reasons"]))


class NearLinkOrder(unittest.TestCase):
    A = NEAR_MODULE
    P = {"unit": "root", "seg": 0, "placements": {"_DATA": {"seg": DG, "off": 0x1812, "size": 31}}}   # ends 1831

    def near(self, off, la, size=4):
        return {"unit": "data", "seg": DG, "origin": off, "link_after": la,
                "placements": {"_DATA": {"seg": DG, "off": off, "size": size}}}

    def test_first(self):
        man = man_with(**{"data:55B3@0042": self.A})
        self.assertEqual(modules.link_after_reasons(man, "data:55B3@0042", self.A), [])
        moved = self.near(0x44, "")
        self.assertTrue(modules.link_after_reasons(man, "k", moved))
        # FIRST needs the accepted BEGDATA segment
        self.assertTrue(any("BEGDATA" in r for r in modules.link_after_reasons({"modules": {}}, "k", self.A)))

    def test_after_module_word_fill(self):
        man = man_with(**{"root:0000": self.P})
        ok = self.near(0x1832, "root:0000")            # 1831 is a zero fill byte (word alignment)
        self.assertEqual(modules.link_after_reasons(man, "k", ok), [])
        self.assertTrue(modules.link_after_reasons(man, "k", ok, {"_DATA": "byte"}))   # byte aligned: no fill
        self.assertTrue(modules.link_after_reasons(man, "k", self.near(0x1834, "root:0000")))
        self.assertTrue(modules.link_after_reasons(man, "k", self.near(0x1832, "root:004A")))  # not in manifest
        self.assertTrue(modules.link_after_reasons(man, "k", self.near(0x1832, "data:55B3@0042")))

    def test_nonzero_gap(self):
        # 0065-0067 (inside fd_55B3_0064 = 0042:55B3) are not fill: a module ending at 0065 cannot be
        # followed by a dword-aligned one at 0068
        man = man_with(**{"p": {"unit": "data", "seg": DG, "placements": {"_DATA": {"seg": DG, "off": 0x61, "size": 4}}}})
        r = modules.link_after_reasons(man, "k", self.near(0x68, "p"), {"_DATA": "dword"})
        self.assertTrue(any("not link fill" in s for s in r), r)


class AlignmentFill(unittest.TestCase):
    def test_word_fill(self):
        placed = [(DG * 16 + 0x1812, 31, "root:0000", "_DATA", False, "word"),
                  (DG * 16 + 0x1832, 32, "root:004A", "_DATA", False, "word")]
        self.assertEqual(modules.placement_link_fill(placed), (1, 1, []))
        byte = [placed[0], placed[1][:5] + ("byte",)]
        self.assertEqual(modules.placement_link_fill(byte), (0, 0, []))       # not explained: stays debt

    def test_nonzero_gap_and_overlap(self):
        # DGROUP 0064..0067 holds a far pointer: never fill
        placed = [(DG * 16 + 0x42, 34 - 2, "a", "_DATA", False, "word"),
                  (DG * 16 + 0x64, 4, "b", "_DATA", False, "dword")]
        fill, _, fails = modules.placement_link_fill(placed)
        self.assertEqual(fill, 0)
        self.assertTrue(any("not link fill" in f for f in fails), fails)
        over = [(DG * 16 + 0x42, 34, "a", "_DATA", False, "word"), (DG * 16 + 0x62, 4, "b", "_DATA", False, "word")]
        self.assertTrue(any("overlapping" in f for f in modules.placement_link_fill(over)[2]))

    def test_far_paragraph_fill(self):
        placed = [(0x3D570, 3162, "data:3D57", "UNIT7_DATA", True, "paragraph"),
                  (0x3E1D0, 63647, "data:3E1D", "UNIT7_DATA", True, "paragraph")]
        self.assertEqual(modules.placement_link_fill(placed), (6, 0, []))


class RuntimeDataRules(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import runtime
        cls.rt = runtime
        cls.res, cls.derived, _, _ = runtime.verify_all()
        cls.comm = {}
        cls.rows = {(r["member"], r["segment"]): r for r in runtime.verify_data(cls.res, cls.derived,
                                                                                    communals=cls.comm)}

    def test_endcode(self):
        lin, why = self.rt.endcode_linear()
        self.assertEqual((lin, why), (exe.load().sections[27].load_linear, []))
        self.assertTrue(self.rows[("dos\\crt0.asm", "DBDATA")]["exact"])
        with mock.patch.object(self.rt, "endcode_linear", lambda x=None: (lin + 16, [])):
            rows = {(r["member"], r["segment"]): r for r in self.rt.verify_data(self.res, self.derived)}
        self.assertFalse(rows[("dos\\crt0.asm", "DBDATA")]["exact"])

    def test_bracketed(self):
        xp = self.rows[("_cflush.asm", "XP")]
        self.assertEqual((xp["rule"], xp["exact"]), ("BRACKETED", True))
        bad = {k: v for k, v in self.derived.items()}
        key = "seg:dos\\crt0dat.asm:XPE:DGROUP"
        bad[key] = {next(iter(self.derived[key])) + 2: [("x", 0)]}          # XPE two bytes later
        members = self.rt._data_members(self.res, self.derived)
        self.assertNotIn(("_cflush.asm", "XP"), self.rt._place_data(members, bad))

    def test_comdef_anchors(self):
        c = self.comm["__bufin"]
        self.assertTrue(c["exact"], c)
        self.assertEqual((c["linear"] - DG * 16, c["size"], len(c["anchors"])), (0x92E4, 512, 2))
        self.assertTrue(self.rows[("_file.c", "_DATA")]["exact"])

        def fx(off):
            return {"target_kind": "external", "target": "_c", "segment": "_DATA", "offset": off, "loc": "pointer32",
                    "self_relative": False, "encoded_addend": "00000000"}
        start = self.rows[("_file.c", "_DATA")]["linear"]
        place = {("m", "_DATA"): (start, "REFERENCED")}

        def run(offs):
            obj = SimpleNamespace(communals=[{"name": "_c", "kind": "near", "length": 4}],
                                  linker_fixups=[fx(o) for o in offs])
            return self.rt.communal_placements([{"row": {"member": "m", "library": "l"}, "obj": obj}], place)["_c"]
        self.assertTrue(run([0, 6])["exact"])
        self.assertIn("single anchor", " ".join(run([0])["reasons"]))
        self.assertIn("disagree", " ".join(run([0, 2])["reasons"]))            # 92E4 vs 55B3


class RuntimeDataRegistry(unittest.TestCase):
    def test_add_runtime_data(self):
        import symbols
        store = symbols.load()
        saved = {}
        with mock.patch.object(symbols, "load", lambda: store), \
                mock.patch.object(symbols, "save", lambda d: saved.update(d)):
            symbols.add_runtime([{"name": "__iob", "seg": DG, "off": 0x779C, "why": "test"},
                                 {"name": "__bufin", "seg": DG, "off": 0x92E4, "why": "test"}])
            self.assertEqual(saved["runtime"]["__iob"]["kind"], "data")
            self.assertIn("COMDEF_ANCHORS", saved["runtime"]["__bufin"]["grounding"])
            with self.assertRaises(SystemExit):
                symbols.add_runtime([{"name": "__iob2", "seg": DG, "off": 0x7790, "why": "wrong address"}])


class FarBssProbe(unittest.TestCase):
    """fd_50F6_3B60 is registered with a 180-byte gap to the next FAR_BSS variable."""
    MAN = {"modules": {"t": {"profile": "msc600", "flags": ["/AL", "/Os"], "lang": "c"}}}

    def probe(self, src):
        import farbss
        return farbss.probe_declarations(self.MAN, {"t": src}, jobs=1)

    def test_pinned_by_code(self):
        import farbss
        p = self.probe("extern unsigned char far fd_50F6_3B60[180];\n"
                       "unsigned far f(void) { return sizeof(fd_50F6_3B60); }\n")
        self.assertEqual(p["pinned"], {"fd_50F6_3B60": [(180, "t")]})
        row = next(r for r in farbss.account({}, probed=p)["rows"] if r["name"] == "fd_50F6_3B60")
        self.assertEqual(row["status"], "pinned")
        big = self.probe("extern unsigned char far fd_50F6_3B60[200];\n"
                         "unsigned far f(void) { return sizeof(fd_50F6_3B60); }\n")
        self.assertFalse(farbss.account({}, probed=big)["accounted"])      # pinned size exceeds the gap

    def test_measured_not_pinned(self):
        import farbss
        p = self.probe("typedef struct { int a[45]; } T;\nextern T far fd_50F6_3B60[2];\n"
                       "char far g(void) { return (char)fd_50F6_3B60[1].a[3]; }\n")
        self.assertEqual(p["declaration"], {"fd_50F6_3B60": [(180, "t")]})    # typedef: the parser cannot
        self.assertEqual(p["pinned"], {})
        self.assertEqual(farbss.declared_sizes({"t": "typedef struct { int a[45]; } T;\n"
                                                "extern T far fd_50F6_3B60[2];\n"}), {})
        row = next(r for r in farbss.account({}, probed=p)["rows"] if r["name"] == "fd_50F6_3B60")
        self.assertEqual(row["status"], "consistent")

    def test_parameters_are_not_declarations(self):
        import farbss
        names = {"fd_A", "W", "Z"}
        self.assertEqual(farbss._declared_names("extern void (far * far fd_A)(char far *Z);\n"
                                                "extern void (far * far W[])(int Z);\nextern int f(int Z);\n", names),
                         {"fd_A": None, "W": ""})


if __name__ == "__main__":
    unittest.main()
