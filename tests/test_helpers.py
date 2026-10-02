"""Positive and negative controls for the shared analysis helpers (slots, records, variants,
idscan).  They compile with the pinned profiles of the modules involved (msc600ax: headless
DOSBox-X), so the whole file takes about a minute.  Cases that depend on the current state of
a canonical module skip themselves when that state has moved on."""
import contextlib
import copy
import io
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import idscan  # noqa: E402
import modctx  # noqa: E402
import records  # noqa: E402
import slots  # noqa: E402
import variants  # noqa: E402

TMP = ROOT / "build" / "helpers" / "tests"


def run_main(fn, argv):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = fn(argv)
    return code, buf.getvalue()


def src(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="latin1")


def write(name: str, text: str) -> Path:
    TMP.mkdir(parents=True, exist_ok=True)
    p = TMP / name
    p.write_text(text, encoding="latin1")
    return p


# root:1383 -- GetForageDir.  One more line entry (the loop initialiser on its own line: same
# code) moves the fifth /Zi line-number flush from 0C25 to 0C0B, into the interval that the
# oracle's _SRand8 relocation order forbids (worker zifix: object offsets (0B70,0C0C]).
FOR_LOOP = "    for (i = 0; i < 8; ++i) {\n"
FOR_SPLIT = "    i = 0;\n    for (; i < 8; ++i) {\n"


class Arguments(unittest.TestCase):
    def test_placements_and_keys(self):
        self.assertEqual(modctx.parse_placements(["CONST=55B3;7E28;2"]),
                         {"CONST": {"seg": 0x55B3, "off": 0x7E28, "size": 2}})
        ctx = modctx.resolve(target="root;1383")
        self.assertEqual(ctx.key, "root:1383")
        self.assertEqual(ctx.span, (0x0002, 0x1136))
        self.assertEqual(modctx.infer_module(ctx.text), "root:1383")

    def test_mangled_refused(self):
        with self.assertRaises(SystemExit):
            modctx.check_arg("C:/Program Files/Git/AL", "flag")
        with self.assertRaises(SystemExit):
            modctx.resolve(target="root:1383", flags=["C:/Program Files/Git/AL"])
        with self.assertRaises(SystemExit):
            modctx.under_build(ROOT / "src" / "x.json")


class SlotAlignment(unittest.TestCase):
    """Pure alignment logic: a slot swap vs a local operand-order exchange."""

    def rows(self, texts):
        return [(i * 3, f"{i:02x}{t}", t) for i, t in enumerate(texts)]

    def test_swap_and_exchange(self):
        cand = self.rows(["lea ax, [bp - 0xc]", "push ax", "lea ax, [bp - 0xa]", "push ax"] + ["nop"] * 6 +
                         ["mov al, byte ptr [bp - 0xc]", "nop", "nop", "nop", "nop", "nop", "nop",
                          "les bx, ptr [bp - 0x24]", "mov ax, word ptr es:[bx]", "les bx, ptr [bp - 0x14]",
                          "cmp word ptr es:[bx], ax"])
        orig = self.rows(["lea ax, [bp - 0xa]", "push ax", "lea ax, [bp - 0xc]", "push ax"] + ["nop"] * 6 +
                         ["mov al, byte ptr [bp - 0xa]", "nop", "nop", "nop", "nop", "nop", "nop",
                          "les bx, ptr [bp - 0x14]", "mov ax, word ptr es:[bx]", "les bx, ptr [bp - 0x24]",
                          "cmp word ptr es:[bx], ax"])
        M, R, other, pairs, where = slots.correspond(cand, orig)
        self.assertEqual(other, [])
        self.assertEqual(M[-0xC][-0xA], 2)
        self.assertEqual(slots.exchange_kind(where, -0xC, -0xA), "swap")
        self.assertEqual(slots.exchange_kind(where, -0x24, -0x14), "operand-order exchange")

    def test_listing(self):
        cod = ("_f\tPROC FAR\n;\ttattr = -12\n;\tregister si = y\n"
               "\t*** 00003a\t8d 46 f4 \t\tlea\tax,WORD PTR [bp-12]\t;tattr\n"
               "\t*** 00003d\t8b 46 f0 \t\tmov\tax,WORD PTR [bp-16]\t;tstate\n_f\tENDP\n")
        lst = slots.parse_listing(cod, "_f")
        self.assertEqual(lst["slots"], {"tattr": -12})
        self.assertEqual(lst["regs"], [("si", "y")])
        self.assertEqual(lst["bpnames"][-16], {"tstate"})


class SlotsS25(unittest.TestCase):
    """S25 DoAntMoveY: the best draft (kept under #if 0 in the canonical file) differs from the
    original only by the frame slots of tx and tattr."""

    def test_tx_tattr_swap(self):
        s = src("src/S25/m3BA4.c")
        stand = "void far DoAntMoveY(void)\n{\n    volatile int t;"
        if stand not in s or "#endif\n/* SCAFFOLD END */" not in s:
            self.skipTest("S25 DoAntMoveY stand-in/draft layout changed")
        a = s.index(stand)
        b = s.index("#if 0\n", a)
        c = s.index("#endif\n/* SCAFFOLD END */", b)
        p = write("moveY.c", s[:a] + s[b + len("#if 0\n"):c] + s[c + len("#endif\n"):])
        code, out = run_main(slots.main, ["DoAntMoveY", str(p)])
        self.assertEqual(code, 1, out)
        self.assertIn("swap tattr -0x0c <-> tx -0x0a", out)
        self.assertIn("non-BP differences: 0", out)

    def test_exact_function_maps_to_itself(self):
        code, out = run_main(slots.main, ["DoAntSimY", str(ROOT / "src/S25/m3BA4.c")])
        self.assertEqual(code, 0, out)
        self.assertNotIn("MOVED", out)
        self.assertNotIn("swap", out)
        self.assertIn("non-BP differences: 0", out)


class Records1383(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ctx = modctx.resolve(module="root:1383")
        if FOR_LOOP not in cls.ctx.text:
            raise unittest.SkipTest("root:1383 source changed")
        cls.base = records.Analysis(cls.ctx)
        c = copy.copy(cls.ctx)
        c.text = cls.ctx.text.replace(FOR_LOOP, FOR_SPLIT, 1)
        cls.plus1 = records.Analysis(c)

    def forbid(self, an):
        return [c for c in an.constraints if (c.kind, c.lo, c.hi) == ("FORBID", 0x0B72, 0x0C0E)]

    def test_canonical_has_no_violation(self):
        an = self.base
        self.assertEqual(an.violations(an.current_breaks()), [])
        (c,) = self.forbid(an)
        self.assertEqual((c.fa, c.scope, an.fm.to_obj(c.lo), an.fm.to_obj(c.hi)),
                         ("GetForageDir", "within", 0x0B70, 0x0C0C))
        self.assertIn(0x0C25, [e.frame for e in an.flushes])

    def test_one_more_line_entry_violates(self):
        an = self.plus1
        self.assertEqual(an.obj.segments[an.fm.segment], self.base.obj.segments[self.base.fm.segment],
                         "the edit must not change code")
        v = an.violations(an.current_breaks())
        self.assertEqual([(c.kind, c.lo, c.hi) for c in v], [("FORBID", 0x0B72, 0x0C0E)])
        self.assertIn(0x0C0B, [e.frame for e in an.flushes])

    def test_simulation_predicts_the_compiled_flushes(self):
        p0 = self.base.insert_point("GetForageDir")
        self.assertEqual(self.base.sim(p0, 1), [e.frame for e in self.plus1.flushes])
        self.assertEqual(self.base.sim(p0, 0), [e.frame for e in self.base.flushes])

    def test_plan_removes_the_entry(self):
        plan = records.make_plan(self.plus1, 6)
        self.assertEqual([p[3] for p in plan][4], -1)

    def test_cli_git_bash_key(self):
        code, out = run_main(records.main, ["root;1383", "--obj", "--all"])
        self.assertEqual(code, 0, out)
        self.assertIn("(0B72,0C0E] obj (0B70,0C0C]", out)


class RecordsS06(unittest.TestCase):
    """S06 o06_35F5_14CC / 1803 are byte-exact in-place drafts whose within-group relocation
    order fails; the cause is a /Zi line-number flush inside a FORBID interval (on 2026-09-30:
    14CC (1629,17AF] broken at 1665, 1803 (18F1,19CC] broken at 1998)."""

    def test_flush_violations(self):
        ctx = modctx.resolve(module="S06:35F5")
        names = ("o06_35F5_14CC", "o06_35F5_1803")
        if {c["name"] for c in ctx.claims} & set(names):
            self.skipTest("S06 14CC/1803 are claimed now")
        an = records.Analysis(ctx)
        for n in names:
            r = an.results.get(n)
            if r is None or r.reloc_order != "WITHIN_GROUP_MISMATCH" or r.candidate != r.original:
                self.skipTest(f"{n} is no longer a byte-exact draft with a within-group order mismatch")
        causes = {rc.frame: rc.cause for rc in an.recs}
        br = an.current_breaks()
        for n in names:
            v = [c for c in an.violations(br) if c.fa == n and c.fb == n]
            self.assertTrue(v, n)
            for c in v:
                self.assertEqual(c.kind, "FORBID")
                self.assertEqual({causes[q] for q in br if c.lo < q <= c.hi}, {"flush"}, c.text())


class Variants218D(unittest.TestCase):
    """218D:0656: 'cur = start = f()' is exact, 'start = cur = f()' is not (codegen-rules)."""

    def test_one_line_fix(self):
        base = ROOT / "src/root/m218D.c"
        if "    cur = start = f_218D_052F();" not in base.read_text(encoding="latin1"):
            self.skipTest("m218D.c changed")
        spec = write("v218D.json", json.dumps({
            "swapped": [["    cur = start = f_218D_052F();", "    start = cur = f_218D_052F();"]],
            "Swapped": [["    cur = start = f_218D_052F();", "    start = cur = f_218D_052F();"]],
            "missing": [["no such text", "x"]]}))
        out_dir = TMP / "v218D"
        code, out = run_main(variants.main, ["--base", str(base), "--spec", str(spec), "--module", "root;218D",
                                             "--out", str(out_dir), "--jobs", "3"])
        self.assertEqual(code, 0, out)
        res = {r["name"]: r for r in json.loads((out_dir / "results.json").read_text())["variants"]}
        self.assertTrue(res["base"]["result"]["exact"])
        bad = [n for n, c in res["swapped"]["result"]["claims"].items() if not c["exact"]]
        self.assertEqual(bad, ["f_218D_0656"])
        self.assertIn("MISSING", res["missing"]["result"]["log"])
        files = [r["file"] for r in res.values() if r["file"]]
        self.assertEqual(len({f.lower() for f in files}), len(files), "names must differ case-insensitively")


class IdScan(unittest.TestCase):
    def test_position(self):
        t = "/* c */\nint a;\nextern int b;\nvoid far f(void)\n{\n}\n"
        self.assertEqual(idscan.position(t), t.index("extern"))
        self.assertEqual(idscan.position(t, top=True), 0)
        self.assertEqual(idscan.position(t, before="f"), t.index("void far f"))
        self.assertEqual(idscan.position(t, at="int a;\\n"), t.index("int a;"))
        self.assertEqual(idscan.padded(t, 0, 2).count("idscan_pad"), 2)

    def test_count_sensitivity_is_periodic(self):
        """root:2505 is exact as promoted (N=0); one dummy extern changes some claims, and
        17 dummies give the N=0 result again (the 17-bucket symbol hash)."""
        ctx = modctx.resolve(module="root:2505")
        pos = idscan.position(ctx.text, top=True)
        rows = variants.run(ctx, [(f"N={n}", idscan.padded(ctx.text, pos, n), "") for n in (0, 1, 17)],
                            claims_only=True, jobs=3)
        st = [{k: modctx.status_char(v) for k, v in r["result"]["claims"].items()} for r in rows]
        self.assertTrue(all(ch == "E" for ch in st[0].values()), st[0])
        self.assertNotEqual(st[0], st[1])
        self.assertEqual(st[0], st[2])


if __name__ == "__main__":
    unittest.main()
