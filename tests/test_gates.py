"""Negative and positive controls for the acceptance gate (they compile with the pinned MSC 6.00)."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import compiler  # noqa: E402
import exe  # noqa: E402
import match  # noqa: E402
import modules  # noqa: E402

ABS_OK = """int far f_00F8_0459(int value)
{
    if (value < 0)
        return -value;
    return value;
}
"""
ABS_TERNARY = "int far f_00F8_0459(int value) { return value < 0 ? -value : value; }\n"
ABS_WRONG = """int far f_00F8_0459(int value)
{
    if (value <= 0)
        return -value;
    return value;
}
"""
STORE = "extern int near g_8BA2;\nvoid far f_0093_008F(int value) { g_8BA2 = value; }\n"
ABS_T = match.Target("root", 0x00F8, 0x0459, 30)
STORE_T = match.Target("root", 0x0093, 0x008F, 20)


def obj(src, flags=("/AL", "/Os")):
    r = compiler.compile_c(src, "msc600", list(flags))
    assert r.ok, r.log
    return r.obj


class ExecutableFormat(unittest.TestCase):
    def test_structure(self):
        x = exe.load()
        self.assertEqual(len(x.sections), 28)
        self.assertEqual(len(x.vectors), 136)
        self.assertEqual(len(x.relocs), 3683)
        self.assertEqual(x.sections[27].flags, 0x100)
        self.assertEqual(len(x.raw) - (x.sections[27].data_file_offset + len(x.sections[27].data)), 253)


class Gate(unittest.TestCase):
    def test_positive(self):
        self.assertTrue(match.match_object(obj(ABS_OK), ABS_T, "UNIT_TEXT", "_f_00F8_0459").exact)

    def test_wrong_optimisation_profile(self):
        r = match.match_object(obj(ABS_OK, ("/AL", "/Ot")), ABS_T, "UNIT_TEXT", "_f_00F8_0459")
        self.assertFalse(r.exact)
        self.assertTrue(any("length" in s for s in r.reasons))

    def test_wrong_semantics_same_length(self):
        r = match.match_object(obj(ABS_WRONG), ABS_T, "UNIT_TEXT", "_f_00F8_0459")
        self.assertFalse(r.exact)

    def test_ternary_not_equivalent_codegen(self):
        self.assertFalse(match.match_object(obj(ABS_TERNARY), ABS_T, "UNIT_TEXT", "_f_00F8_0459").exact)

    def test_fixup_bound_symbolically(self):
        o = obj(STORE)
        self.assertTrue(match.match_object(o, STORE_T, "UNIT_TEXT", "_f_0093_008F").exact)
        saved = match.symbols()
        try:
            patched = dict(saved)
            patched["_g_8BA2"] = {**saved["_g_8BA2"], "off": 0x8BA4}
            match.symbols.cache_clear()
            match.symbols.__wrapped__  # noqa: B018
            orig = match.symbols
            match.symbols = lambda: patched
            r = match.match_object(o, STORE_T, "UNIT_TEXT", "_f_0093_008F")
            self.assertFalse(r.exact, "a wrong data address must not match")
        finally:
            match.symbols = orig
            match.symbols.cache_clear()

    def test_unregistered_external_refused(self):
        src = "extern int near unknown_name;\nvoid far f_0093_008F(int value) { unknown_name = value; }\n"
        r = match.match_object(obj(src), STORE_T, "UNIT_TEXT", "_f_0093_008F")
        self.assertFalse(r.exact)
        self.assertTrue(r.unbound)

    def test_scaffold_claim_refused(self):
        text = ("void far f_00DF_00E8(int a, int b, int c);\n"
                "void far f_00DF_0112(int a, int b, int c) { f_00DF_00E8(a, b, c); }\n"
                "/* SCAFFOLD BEGIN: context */\nvoid far f_00DF_00E8(int a, int b, int c) { }\n/* SCAFFOLD END */\n")
        module = {"profile": "msc600", "flags": ["/AL", "/Os"], "placements": {}}
        x = exe.load()
        import hashlib
        claims = [{"name": "f_00DF_00E8", "unit": "root", "seg": 0xDF, "off": 0xE8, "size": 42,
                   "target_sha256": hashlib.sha256(x.read("root", 0xDF * 16 + 0xE8, 42)).hexdigest()}]
        res = modules.verify_module(text, module, claims)
        self.assertFalse(res["exact"])


if __name__ == "__main__":
    unittest.main()
