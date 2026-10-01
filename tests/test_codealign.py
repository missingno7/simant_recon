"""Rule CODEALIGN-1: an object's code segment starts at a multiple of its SEGDEF alignment
(worker align, work/align/FINDINGS.json).

Unit tests of modules.code_alignment_reasons, the oracle invariant behind it, a negative control
on real data (the pre-correction root:19A9 source placed at the odd 0x19A95 is refused by the
alignment check alone), its positive contrast (the corrected object at 0x19A98), and the
promote.py --drop-extent refusals.
"""
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import exe  # noqa: E402
import functions  # noqa: E402
import modules  # noqa: E402

NEG = ROOT / "tests" / "negatives"


class Rule(unittest.TestCase):
    def test_reasons(self):
        word = {"name": "X_TEXT", "alignment": "word"}
        self.assertTrue(modules.code_alignment_reasons(word, 0x19A95))
        self.assertIn("CODEALIGN-1", modules.code_alignment_reasons(word, 0x19A95)[0])
        self.assertEqual(modules.code_alignment_reasons(word, 0x19A98), [])
        self.assertEqual(modules.code_alignment_reasons(word, 0x19A96), [])
        # a BYTE segment (MASM 'segment byte') may start anywhere: the rule reads the SEGDEF
        self.assertEqual(modules.code_alignment_reasons({"name": "X_TEXT", "alignment": "byte"}, 0x19A95), [])
        self.assertTrue(modules.code_alignment_reasons({"name": "X_TEXT", "alignment": "paragraph"}, 0x19A98))
        self.assertTrue(modules.code_alignment_reasons(None, 0x19A98))

    def test_oracle_frame_transitions(self):
        """Every code frame that begins directly at the previous frame's last function-table row
        (no gap) begins at an even address: an odd end is always followed by LINK fill."""
        rows = functions.table()["functions"]
        bad = []
        for unit in sorted({r["unit"] for r in rows}):
            rs = sorted((r for r in rows if r["unit"] == unit), key=lambda r: r["seg"] * 16 + r["off"])
            for p, r in zip(rs, rs[1:]):
                end, lin = p["seg"] * 16 + p["off"] + p["size"], r["seg"] * 16 + r["off"]
                if r["seg"] != p["seg"] and lin == end and lin % 2:
                    bad.append(f"{unit}:{r['seg']:04X} at {lin:05X}")
        self.assertEqual(bad, [])


def _module_19a9(start: int, extra_claims: list[dict]) -> tuple[dict, list[dict]]:
    man = modules.load_manifest()
    m = dict(man["modules"]["root:19A9"])
    m["extent"] = {"start": start, "end": m["extent"]["end"]}
    have = {c["name"] for c in m["claims"]}
    claims = [c for c in extra_claims if c["name"] not in have] + [dict(c) for c in m["claims"]]
    return man, m, claims


def _stub_claims():
    x = exe.load()
    out = []
    for off in (5, 6, 7):
        lin = 0x19A90 + off
        out.append({"name": f"f_19A9_{off:04X}", "unit": "root", "seg": 0x19A9, "off": off, "size": 1,
                    "target_sha256": modules.sha(x.read("root", lin, 1)), "kind": "C",
                    "provenance": "EXACT_NATURAL"})
    return out


class RealData(unittest.TestCase):
    """The 1986/19A9 boundary: the old 19A9 file (three empty functions first) is byte-exact at the
    odd 0x19A95, and only CODEALIGN-1 refuses it; the corrected file is exact at 0x19A98."""

    def test_negative_odd_start(self):
        text = (NEG / "T13_m19A9_odd_start.c").read_text(encoding="latin1")
        man, m, claims = _module_19a9(0x19A95, _stub_claims())
        res = modules.verify_module(text, m, claims, man=man)
        self.assertFalse(res["exact"])
        ext = res["extent"]["reasons"]
        self.assertTrue(any("CODEALIGN-1" in r for r in ext), ext)
        # every claim is individually exact: the alignment rule alone refuses the placement
        self.assertTrue(all(c["exact"] for c in res["claims"].values()), res["claims"])
        others = [r for r in ext if "CODEALIGN-1" not in r and "function-table rows" not in r]
        self.assertEqual(others, [])

    def test_positive_corrected(self):
        man = modules.load_manifest()
        m = man["modules"]["root:19A9"]
        if m["extent"]["start"] != 0x19A98:
            self.skipTest("root:19A9 not yet re-promoted at 19A98 (work/align/FINDINGS.txt, migrate.sh)")
        text = (ROOT / m["source"]).read_text(encoding="latin1")
        res = modules.verify_module(text, m, m["claims"], man=man)
        self.assertTrue(res["exact"], res.get("extent"))


def promote(*args):
    env = dict(os.environ, MSYS_NO_PATHCONV="1", MSYS2_ARG_CONV_EXCL="*")
    r = subprocess.run([sys.executable, str(ROOT / "tools" / "promote.py"), *map(str, args), "--verify-only"],
                       capture_output=True, text=True, cwd=ROOT, env=env)
    return r.returncode, r.stdout + r.stderr


class DropExtent(unittest.TestCase):
    def refused(self, *args):
        rc, out = promote(*args)
        self.assertNotEqual(rc, 0, out[-1500:])
        self.assertIn("--drop-extent", out, out[-1500:])

    def test_refusals(self):
        man = modules.load_manifest()["modules"]
        src = ROOT / man["root:277D"]["source"]
        self.refused(src, "--module", "root:277D", "--drop-extent", " ")                 # no evidence
        self.refused(src, "--module", "root:277D", "--drop-extent", "why", "--extent", "277DA:277E0")
        partial = next(k for k, m in man.items() if not m.get("extent") and m["claims"] and m.get("lang") == "c")
        self.refused(ROOT / man[partial]["source"], "--module", partial, "--drop-extent", "why")

    def test_verify_only_positive(self):
        man = modules.load_manifest()["modules"]
        rc, out = promote(ROOT / man["root:277D"]["source"], "--module", "root:277D", "--drop-extent",
                          "control: a complete TU verifies as a partial module")
        self.assertEqual(rc, 0, out[-1500:])
        self.assertNotIn("extent:", out)


if __name__ == "__main__":
    unittest.main()
