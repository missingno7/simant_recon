"""Positive and negative controls for the data gates: data-only modules, far pointers in data,
far segment order and link fill, 64K segments, runtime DGROUP data, FAR_BSS, probe segment
expectations and far-frame references (they compile with the pinned MSC 6.00 / MASM 5.10)."""
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import compiler  # noqa: E402
import exe  # noqa: E402
import match  # noqa: E402
import modules  # noqa: E402
from omf import OmfReader  # noqa: E402

DX8 = "0x00, 0x01, 0x01, 0x01, 0x00, 0xFF, 0xFF, 0xFF"
DY8 = "0xFF, 0xFF, 0x00, 0x01, 0x01, 0x01, 0x00, 0xFF"
TABLES = f"unsigned char far Dx8[8] = {{ {DX8} }};\nunsigned char far Dy8[8] = {{ {DY8} }};\n"
DATA_MODULE = {"unit": "data", "seg": 0x3D57, "profile": "msc600", "flags": ["/AL", "/Os"],
               "placements": {"UNIT5_DATA": {"seg": 0x3D57, "off": 0, "size": 16}}, "link_after": ""}

# S01's dispatch table (DGROUP:211A) starts with far pointers to 3126:0167 and 3126:019A, labels of
# the object's own code segment; S00's (DGROUP:2098) with 31AD:1659, a proc of another object of
# the same overlay section.
OWN_CODE_ASM = """_DATA\tsegment word public 'DATA'
Tbl\tdd\tL1, L2
_DATA\tends
DGROUP\tgroup\t_DATA
S01A_TEXT\tsegment word public 'CODE'
\tassume\tcs:S01A_TEXT
\torg\t{l1}h
L1:\tretf
\torg\t19Ah
L2:\tretf
S01A_TEXT\tends
\tend
"""
OVERLAY_ASM = """_DATA\tsegment word public 'DATA'
\textrn\t{target}:far
Tbl\tdd\t{target}
_DATA\tends
DGROUP\tgroup\t_DATA
\tend
"""


def c_obj(src, flags=("/AL", "/Os")):
    r = compiler.compile_c(src, "msc600", list(flags))
    assert r.ok, r.log
    return OmfReader(communals=True).read(r.obj)


def asm_obj(src):
    r = compiler.assemble(src, "masm510", ["/Mx"])
    assert r.ok, r.log
    return OmfReader(communals=True).read(r.obj)


class DataModule(unittest.TestCase):
    def test_keys(self):
        self.assertEqual(modules.parse_key("data:3D57"), ("data", 0x3D57, None))
        self.assertEqual(modules.parse_key("data;3E1D"), ("data", 0x3E1D, None))    # MSYS-mangled
        self.assertEqual(modules.module_source("data", 0x3D57, None, "c"), "src/data/d3D57.c")
        with self.assertRaises(SystemExit):
            modules.parse_key("data:3D57@0010")

    def test_positive(self):
        res = modules.verify_module(TABLES, DATA_MODULE, [])
        self.assertTrue(res["exact"], res)
        self.assertTrue(res["data_only"])
        self.assertTrue(res["data"]["UNIT5_DATA"]["far"])

    def test_wrong_byte(self):
        res = modules.verify_module(TABLES.replace("0x00, 0x01, 0x01, 0x01", "0x00, 0x02, 0x01, 0x01", 1),
                                    DATA_MODULE, [])
        self.assertFalse(res["exact"])
        self.assertIn("data bytes differ", res["data"]["UNIT5_DATA"]["reasons"])

    def test_public_at_wrong_address(self):
        # same bytes, names swapped: Dx8 would be defined at Dy8's registered address
        swapped = f"unsigned char far Dy8[8] = {{ {DX8} }};\nunsigned char far Dx8[8] = {{ {DY8} }};\n"
        res = modules.verify_module(swapped, DATA_MODULE, [])
        self.assertTrue(res["data"]["UNIT5_DATA"]["exact"])
        self.assertFalse(res["exact"])
        self.assertTrue(any("registered at" in r for r in res["module_reasons"]))

    def test_code_refused(self):
        res = modules.verify_module(TABLES + "int far f(void) { return Dx8[1]; }\n", DATA_MODULE, [])
        self.assertFalse(res["exact"])
        self.assertTrue(any("has code" in r for r in res["module_reasons"]))

    def test_unplaced_segment_refused(self):
        res = modules.verify_module(TABLES + "int near dn = 5;\n", DATA_MODULE, [])
        self.assertFalse(res["exact"])
        self.assertTrue(any("_DATA" in r and "not placed" in r for r in res["module_reasons"]))

    def test_claims_and_link_position_required(self):
        claim = {"name": "Dx8", "unit": "data", "seg": 0x3D57, "off": 0, "size": 8, "target_sha256": ""}
        self.assertFalse(modules.verify_module(TABLES, DATA_MODULE, [claim])["exact"])
        no_link = {k: v for k, v in DATA_MODULE.items() if k != "link_after"}
        res = modules.verify_module(TABLES, no_link, [])
        self.assertTrue(any("link_after" in r for r in res["module_reasons"]))

    def test_64k_segment(self):
        o = c_obj("unsigned char far a[0xF000] = {0};\nunsigned char far b[0x1000] = {0};\n"
                  "char far h[256] = \"pSimAnt\";\n")
        sd = modules.segment_def(o, "UNIT5_DATA")
        self.assertTrue(sd["big"])
        self.assertEqual(sd["length"], 0)
        self.assertEqual(modules.segment_length(o, "UNIT5_DATA"), 0x10000)
        self.assertEqual(modules.segment_length(o, "UNIT6_DATA"), 256)


class SegmentOrder(unittest.TestCase):
    """Far segments of one object follow SEGDEF order, paragraph-contiguous."""
    obj = SimpleNamespace(segment_defs=[{"index": 1, "name": "U7_DATA", "class": "FAR_DATA", "length": 0x1F},
                                        {"index": 2, "name": "U8_DATA", "class": "FAR_DATA", "length": 0x10}],
                          segments={"U7_DATA": b"\0" * 0x1F, "U8_DATA": b"\0" * 0x10})

    def test_order(self):
        good = {"U7_DATA": {"seg": 0x4000, "off": 0, "size": 0x1F}, "U8_DATA": {"seg": 0x4002, "off": 0, "size": 0x10}}
        self.assertEqual(modules.placement_order_reasons(self.obj, good), [])
        swapped = {"U7_DATA": {"seg": 0x4001, "off": 0, "size": 0x1F}, "U8_DATA": {"seg": 0x4000, "off": 0, "size": 0x10}}
        self.assertTrue(modules.placement_order_reasons(self.obj, swapped))
        gap = {"U7_DATA": {"seg": 0x4000, "off": 0, "size": 0x1F}, "U8_DATA": {"seg": 0x4003, "off": 0, "size": 0x10}}
        self.assertTrue(modules.placement_order_reasons(self.obj, gap))

    def test_link_after(self):
        a = {"unit": "data", "seg": 0x3D57, "link_after": "",
             "placements": {"UNIT7_DATA": {"seg": 0x3D57, "off": 0, "size": 3162}}}
        b = {"unit": "data", "seg": 0x3E1D, "link_after": "data:3D57",
             "placements": {"UNIT7_DATA": {"seg": 0x3E1D, "off": 0, "size": 63647}}}
        man = {"modules": {"data:3D57": a, "data:3E1D": b}}
        self.assertEqual(modules.link_after_reasons(man, "data:3D57", a), [])
        self.assertEqual(modules.link_after_reasons(man, "data:3E1D", b), [])
        self.assertTrue(modules.link_after_reasons(man, "data:3E1D", dict(b, link_after="")))
        self.assertTrue(modules.link_after_reasons(man, "data:3E1D", dict(b, link_after="data:4E37")))
        moved = dict(b, placements={"UNIT7_DATA": {"seg": 0x3E1E, "off": 0, "size": 63647}})
        self.assertTrue(modules.link_after_reasons(man, "data:3E1D", moved))

    def test_overlap(self):
        man = {"modules": {"a": {"placements": {"_DATA": {"seg": 0x55B3, "off": 0x100, "size": 4}}},
                           "b": {"placements": {"_DATA": {"seg": 0x55B3, "off": 0x102, "size": 4}}},
                           "c": {"placements": {"_DATA": {"seg": 0x55B3, "off": 0x104, "size": 4}}}}}
        self.assertTrue(modules.placement_overlap_reasons(man, "a"))
        self.assertEqual(modules.placement_overlap_reasons({"modules": {k: man["modules"][k] for k in "ac"}}, "a"), [])


class DataPointers(unittest.TestCase):
    """Rule DATAPTR-1: own code segment and same-section overlay procedures are addressed directly."""
    PL = {"seg": 0x55B3, "off": 0x211A, "size": 8}
    OWN = {"S01A_TEXT": {"seg": 0x3126, "off": 0}}

    def test_own_code_segment(self):
        o = asm_obj(OWN_CODE_ASM.format(l1="167"))
        r = modules.verify_data_segment(o, "_DATA", self.PL, own_code=self.OWN, unit="S01")
        self.assertTrue(r["exact"], r)

    def test_own_code_wrong_target(self):
        o = asm_obj(OWN_CODE_ASM.format(l1="168"))
        self.assertFalse(modules.verify_data_segment(o, "_DATA", self.PL, own_code=self.OWN, unit="S01")["exact"])

    def test_own_code_wrong_origin_or_unbound(self):
        o = asm_obj(OWN_CODE_ASM.format(l1="167"))
        shifted = {"S01A_TEXT": {"seg": 0x3126, "off": 2}}
        self.assertFalse(modules.verify_data_segment(o, "_DATA", self.PL, own_code=shifted, unit="S01")["exact"])
        r = modules.verify_data_segment(o, "_DATA", self.PL, unit="S01")
        self.assertTrue(any("unsupported data fixup" in s for s in r["reasons"]))

    def test_same_section_overlay_proc(self):
        pl = {"seg": 0x55B3, "off": 0x2098, "size": 4}
        o = asm_obj(OVERLAY_ASM.format(target="_o00_31AD_1659"))
        self.assertTrue(modules.verify_data_segment(o, "_DATA", pl, unit="S00")["exact"])
        wrong = asm_obj(OVERLAY_ASM.format(target="_o00_31AD_166A"))
        self.assertFalse(modules.verify_data_segment(wrong, "_DATA", pl, unit="S00")["exact"])

    def test_vector_for_every_data_pointer(self):
        # rule VEC-1: a data pointer is never a call, so a vectored procedure (overlay or root)
        # is addressed through its vector from any unit; unvectored procedures directly
        x = exe.load()
        for v in (next(v for v in x.vectors if v.section != 0xFFFF),
                  next(v for v in x.vectors if v.section == 0xFFFF)):
            name = next(n for n, s in match.symbols().items() if s["kind"] == "code"
                        and s.get("unit", "root") == v.unit and s["seg"] == v.target_seg
                        and s["off"] == v.target_off)
            f = {"target_kind": "external", "target": name}
            for unit in (v.unit, "S26" if v.unit != "S26" else "S25"):
                self.assertEqual(modules._data_target(f, {}, unit=unit), (exe.MANAGER_SEG, v.offset))
        f = {"target_kind": "external", "target": "_f_0250_0114"}    # atexit hook, no vector
        self.assertEqual(modules._data_target(f, {}, unit="root"), (0x0250, 0x0114))


class NearOwnCodeOffsets(unittest.TestCase):
    """offset16 data fixups to the module's own code segment (root:16B5's near dispatch table at
    DGROUP 1E00 = 007F, 00AB: near procs of LINE_TEXT, which starts at frame offset 8)."""
    ASM = """_DATA	segment word public 'DATA'
Tbl	dw	L1, L2
_DATA	ends
DGROUP	group	_DATA
LINE_TEXT	segment word public 'CODE'
	assume	cs:LINE_TEXT
	org	{l1}h
L1:	ret
	org	0A3h
L2:	ret
LINE_TEXT	ends
	end
"""
    PL = {"seg": 0x55B3, "off": 0x1E00, "size": 4}

    def test_near_offsets(self):
        o = asm_obj(self.ASM.format(l1="77"))
        own = {"LINE_TEXT": {"seg": 0x16B5, "off": 8}}
        self.assertTrue(modules.verify_data_segment(o, "_DATA", self.PL, own_code=own, unit="root")["exact"])
        # wrong origin of the code object in its frame, wrong target, no own-code binding
        self.assertFalse(modules.verify_data_segment(o, "_DATA", self.PL, own_code={"LINE_TEXT": {"seg": 0x16B5, "off": 0}},
                                                     unit="root")["exact"])
        wrong = asm_obj(self.ASM.format(l1="78"))
        self.assertFalse(modules.verify_data_segment(wrong, "_DATA", self.PL, own_code=own, unit="root")["exact"])
        r = modules.verify_data_segment(o, "_DATA", self.PL, unit="root")
        self.assertTrue(any("unsupported data fixup offset16 segment:LINE_TEXT" in s for s in r["reasons"]))


class RuntimeData(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import runtime
        cls.rt = runtime
        res, derived, _, _ = runtime.verify_all()
        cls.res, cls.derived = res, derived
        cls.rows = {(r["member"], r["segment"]): r for r in runtime.verify_data(res, derived)}

    def test_rules(self):
        null = self.rows[("chksum.asm", "NULL")]
        self.assertTrue(null["exact"])
        self.assertEqual((null["rule"], null["linear"]), ("DOSSEG_BEGDATA", match.DGROUP_SEG * 16))
        ctype = self.rows[("ctype.asm", "_DATA")]       # data-only member, placed through __ctype_
        self.assertTrue(ctype["exact"])
        self.assertFalse(ctype["code_member"])
        self.assertEqual(self.rows[("dos\\crt0msg.asm", "MSG")]["rule"], "CLASS_SEQUENCE")
        self.assertTrue(self.rows[("dos\\crt0msg.asm", "MSG")]["exact"])

    def test_shifted_placement_fails(self):
        x = exe.load()
        members = self.rt._data_members(self.res, self.derived)
        m = next(m for m in members if m["row"]["member"] == "ctype.asm")
        good = self.rows[("ctype.asm", "_DATA")]["linear"]
        for start, ok in ((good, True), (good + 2, False)):
            r = self.rt.bind_data_segment(m["obj"], "_DATA", 257, start, "ctype.asm", {}, {}, self.derived,
                                          x, x.sections[27])
            self.assertEqual(r["exact"], ok)


class FarBss(unittest.TestCase):
    def test_accounted(self):
        import farbss
        r = farbss.account({})
        self.assertTrue(r["accounted"], r["failures"])
        self.assertEqual(r["size"], 0x55B3 * 16 - 0x50F6 * 16)

    def test_comdef_conflict_and_placement_inside(self):
        import farbss
        self.assertFalse(farbss.account({}, {"HealthR": [(4096, "test")]})["accounted"])
        self.assertFalse(farbss.account({}, placements=[(0x50F6 * 16 + 0x100, 4)])["accounted"])
        r = farbss.account({"k": "extern int far HealthR;\n"})
        self.assertTrue(any("declaration:2@k" in e for row in r["rows"] for e in row["evidence"]))


class ProbeSegments(unittest.TestCase):
    def test_checks(self):
        import probe
        row = {"segments": {"UNIT7_DATA": {"class": "FAR_DATA", "align": "paragraph", "length": 0x10000,
                                           "combine": "public", "big": True}}, "communals": {"_ga": 8}}
        ok = probe.segment_checks("v@0", row, {"UNIT7_DATA": {"class": "FAR_DATA", "length": 65536, "note": "x"},
                                               "UNIT8_DATA": None, "communals": {"_ga": 8}})
        self.assertTrue(all(c["ok"] for c in ok))
        bad = probe.segment_checks("v@0", row, {"UNIT7_DATA": {"length": 20}, "communals": ["_gb"]})
        self.assertFalse(any(c["ok"] for c in bad))
        self.assertFalse(probe.segment_checks("v@0", row, {"UNIT7_DATA": None})[0]["ok"])


class FarRefs(unittest.TestCase):
    def test_const_word(self):
        import dataref
        import functions as fnmod
        rows = [r for r in fnmod.table()["functions"] if r["unit"] == "root" and r["seg"] == 0x10F7]
        refs, words = dataref.far_refs("root", rows)
        self.assertIn((0x3D57, 0x0000), refs)                      # Dx8 through a CONST segment word
        self.assertTrue(any(v.startswith("CONST DG:") for v in refs[(0x3D57, 0)]["via"]))
        self.assertTrue(any(w["frame"] == 0x3E1D and len(w["offs"]) >= 1 for w in words.values()))


if __name__ == "__main__":
    unittest.main()
