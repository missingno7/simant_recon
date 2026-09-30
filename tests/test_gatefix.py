"""Gate hardening (worker gatefix, audit build/workers/audit/REPORT.md F-1..F-12).

Unit tests of the new rules, and every audit negative (tests/negatives/T*.c|.asm, plus the
gatefix additions G*) as a regression test: each must be REFUSED by promote.py --verify-only
against the canonical tree, for the documented reason.  The positive controls re-verify the
canonical modules the negatives are derived from.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import compiler  # noqa: E402
import functions  # noqa: E402
import match  # noqa: E402
import modules  # noqa: E402

NEG = ROOT / "tests" / "negatives"


def lint(text, lang="c"):
    return modules.source_lint(text, lang)


class SourceLint(unittest.TestCase):
    """F-3: source-content rules (modules.source_lint, enforced by verify_module)."""

    def test_emit_refused(self):
        self.assertTrue(lint("void far f(void)\n{\n    _asm _emit 0xFA\n}\n")["refused"])
        self.assertTrue(lint("void far f(void) { __asm { __emit 0FAh } }\n")["refused"])

    def test_emit_in_comment_or_string_admitted(self):
        r = lint('/* no _emit here */\nchar s[] = "_emit";\nvoid far f(void) { _asm cli }\n')
        self.assertEqual(r["refused"], [])

    def test_include_traversal_refused(self):
        self.assertTrue(lint('#include "../layout/x.h"\n')["refused"])
        self.assertTrue(lint("#include <C:\\\\X.H>\n")["refused"])
        self.assertTrue(lint("#include </etc/x.h>\n")["refused"])
        self.assertEqual(lint("#include <sys/types.h>\n")["refused"], [])

    def test_asm_db_in_proc_refused(self):
        asm = "T segment word public 'CODE'\nf proc far\n db 0CBh\nf endp\nT ends\n end\n"
        self.assertTrue(any("inside proc" in r for r in lint(asm, "asm")["refused"]))

    def test_capsule_after_empty_proc_refused(self):
        asm = "T segment word public 'CODE'\nf proc far\nf endp\n db 055h, 0CBh\nT ends\n end\n"
        self.assertTrue(any("no instructions" in r for r in lint(asm, "asm")["refused"]))

    def test_c_data_in_code_segment_refused(self):
        self.assertTrue(lint('unsigned char _based(_segname("_CODE")) f[] = { 0xCB };\n')["refused"])
        self.assertEqual(lint("#define P(o) ((unsigned char _based(g_8DFC) *)(o))\n")["refused"], [])

    def test_asm_data_outside_proc_admitted(self):
        asm = "T segment word public 'CODE'\ntab db 1, 2, 3\nf proc far\n ret\nf endp\nT ends\n end\n"
        self.assertEqual(lint(asm, "asm")["refused"], [])

    def test_asm_org_include_refused(self):
        self.assertTrue(lint("T segment\n org 100h\nT ends\n", "asm")["refused"])
        self.assertTrue(lint(" include macros.inc\n", "asm")["refused"])

    def test_asm_numeric_targets(self):
        for line in (" call 1234h", " jmp far ptr 0F000h:0FFF0h", " jne 12", "L1: jmp short 0Ah"):
            self.assertTrue(lint(f"f proc far\n{line}\nf endp\n", "asm")["refused"], line)
        for line in (" call far ptr _g", " jmp short $+2", " loop L0013", " call word ptr [bx]", " jmp es:[di]"):
            self.assertEqual(lint(f"f proc far\n{line}\nf endp\n", "asm")["refused"], [], line)

    def test_opaque_c_initialiser_flagged(self):
        body = ", ".join(["0x12"] * 64)
        r = lint(f"unsigned char t[64] = {{ {body} }};\n")
        self.assertEqual(r["opaque_unmarked_bytes"], 64)
        r = lint(f"/* OPAQUE-DATA: MacBinary header as stored */\nunsigned char t[64] = {{ {body} }};\n")
        self.assertEqual(r["opaque_unmarked_bytes"], 0)
        self.assertEqual(len(r["opaque"]), 1)
        self.assertEqual(lint(f"int t[32] = {{ {', '.join(['1'] * 31)} }};\n")["opaque_unmarked_bytes"], 0)
        self.assertEqual(lint(f"long t[16] = {{ {', '.join(['1'] * 16)} }};\n")["opaque_unmarked_bytes"], 64)

    def test_opaque_c_string_escapes_flagged(self):
        r = lint('char s[] = "' + "\\x12" * 70 + '";\n')
        self.assertEqual(r["opaque_unmarked_bytes"], 70)

    def test_opaque_asm_flagged(self):
        rows = "\n".join(" db " + ", ".join(["0FFh"] * 16) for _ in range(4))
        r = lint(f"_DATA segment\n_g_1 {rows[1:]}\n_DATA ends\n", "asm")
        self.assertEqual(r["opaque_unmarked_bytes"], 64)
        r = lint(f"_DATA segment\n; OPAQUE-DATA: dither table\n_g_1 {rows[1:]}\n_DATA ends\n", "asm")
        self.assertEqual(r["opaque_unmarked_bytes"], 0)
        self.assertEqual(lint("_DATA segment\nbuf db 320 dup (0)\n_DATA ends\n", "asm")["opaque"], [])

    def test_canonical_sources_clean(self):
        for f in sorted((ROOT / "src").rglob("*")):
            if f.suffix.lower() in (".c", ".asm"):
                r = lint(f.read_text(encoding="latin1"), "asm" if f.suffix.lower() == ".asm" else "c")
                self.assertEqual(r["refused"], [], str(f))


class Provenance(unittest.TestCase):
    """F-4: source_origin values and asm_evidence paths."""

    def test_source_origin(self):
        self.assertEqual(modules.source_origin_reasons("hand-written C", "c"), [])
        self.assertEqual(modules.source_origin_reasons("hand-written asm", "asm"), [])
        self.assertEqual(modules.source_origin_reasons("asm-transcribed: tools/d2a.py@" + "a" * 64, "asm"), [])
        self.assertTrue(modules.source_origin_reasons(None, "asm"))
        self.assertEqual(modules.source_origin_reasons(None, "c"), [])
        self.assertTrue(modules.source_origin_reasons("asm-transcribed: tools/d2a.py", "asm"))

    def test_evidence_paths(self):
        self.assertEqual(modules.evidence_paths("see docs/codegen-rules.md and p/x.c"), ["docs/codegen-rules.md"])
        self.assertEqual(modules.evidence_path_reasons("rule ASM-1 (docs/codegen-rules.md)"), [])
        self.assertTrue(modules.evidence_path_reasons("probe evidence/codegen/NO-SUCH-PROBE.json"))


class PascalBinding(unittest.TestCase):
    """F-11: an upper-case undecorated name binds only to a symbol registered as pascal."""

    def setUp(self):
        self.saved = match.symbols

    def tearDown(self):
        match.symbols = self.saved

    def fake(self, conv):
        rec = {"kind": "code", "unit": "root", "seg": 0x15D9, "off": 0}
        if conv:
            rec["convention"] = conv
        match.symbols = lambda: {"_TickCount": rec, "_f_00DE_000A": {"kind": "code", "unit": "root", "seg": 0xDE,
                                                                     "off": 0xA, "convention": "pascal"}}

    def test_cdecl_symbol_not_bound_by_pascal_name(self):
        self.fake(None)
        self.assertIsNone(match.obj_name_lookup("TICKCOUNT"))
        self.assertEqual(match.c_name("TICKCOUNT"), "TICKCOUNT")

    def test_pascal_symbol_bound(self):
        self.fake("pascal")
        self.assertEqual(match.obj_name_lookup("TICKCOUNT")["seg"], 0x15D9)
        self.assertEqual(match.c_name("F_00DE_000A"), "f_00DE_000A")
        self.assertEqual(match.c_name("_x"), "x")
        self.assertEqual(match.c_name("@x"), "x")

    def test_pascal_extent_and_search(self):
        """root:00DE (one pascal function, public F_00DE_000A) verifies as a complete TU, and
        search.py binds the pascal public through the same normaliser."""
        m = modules.load_manifest()["modules"]["root:00DE"]
        rc, out = promote(ROOT / m["source"], "--module", "root:00DE", "--extent", "00DEA:00DF4")
        self.assertEqual(rc, 0, out[-1500:])
        env = dict(os.environ, MSYS_NO_PATHCONV="1", MSYS2_ARG_CONV_EXCL="*")
        r = subprocess.run([sys.executable, str(ROOT / "tools" / "search.py"), "f_00DE_000A", str(ROOT / m["source"]),
                            "--profile", m["profile"], "--flags", *m["flags"], "--quiet"],
                           capture_output=True, text=True, cwd=ROOT, env=env)
        self.assertIn("EXACT", r.stdout, r.stdout + r.stderr)

    def test_registry_records_pascal_function(self):
        import symbols
        rec = symbols.load()["code"].get("f_00DE_000A")
        self.assertIsNotNone(rec)
        self.assertEqual(rec.get("convention"), "pascal", "run the gatefix migration (symbols.py set-convention)")


class Placement(unittest.TestCase):
    """F-5 alignment, F-2 extent boundaries, F-12 code-segment data."""

    def test_alignment(self):
        self.assertTrue(modules.alignment_reasons({"alignment": "word"}, 0x55B30 + 0x1C49))
        self.assertEqual(modules.alignment_reasons({"alignment": "word"}, 0x55B30 + 0x1C48), [])
        self.assertTrue(modules.alignment_reasons({"alignment": "paragraph"}, 0x3D578))
        self.assertEqual(modules.alignment_reasons({"alignment": "byte"}, 0x3D579), [])

    def test_extent_rows(self):
        man = modules.load_manifest()
        m = man["modules"]["root:29F0"]
        self.assertEqual(modules.extent_row_reasons(man, m, 0x29F0A, 0x29F4C), [])
        self.assertTrue(modules.extent_row_reasons(man, m, 0x29F0A, 0x29F38))      # tail trimmed (T6)
        self.assertTrue(modules.extent_row_reasons(man, m, 0x29F12, 0x29F4C))      # head trimmed (T6b)

    def test_extent_rows_later_object(self):
        man = modules.load_manifest()
        if "S00:31AD@2AB4" not in man["modules"]:
            self.skipTest("no multi-object frame in the manifest")
        first = man["modules"]["S00:31AD"]
        ext = first["extent"]
        self.assertEqual(modules.extent_row_reasons(man, first, ext["start"], ext["end"]), [])
        # without the second object, the rows of 2AB4.. would be unowned
        alone = {"modules": {k: v for k, v in man["modules"].items() if k != "S00:31AD@2AB4"}}
        self.assertTrue(modules.extent_row_reasons(alone, first, ext["start"], ext["end"]))

    def test_tail_at_extent_end(self):
        self.assertTrue(modules.extent_tail_reasons("root", 0x29F38, 0x29F0))
        self.assertEqual(modules.extent_tail_reasons("root", 0x29F38, 0x29F0, hi_lin=0x29F38), [])

    def test_code_data_overlaps(self):
        man = modules.load_manifest()
        dic = [c for m in man["modules"].values() for c in m["claims"] if c.get("kind") == modules.DATA_KIND]
        if not dic:
            self.skipTest("no DATA_IN_CODE claims")
        c = dic[0]
        lin = c["seg"] * 16 + c["off"]
        self.assertEqual(modules.row_overlaps(c["unit"], lin, c["size"]), [])
        self.assertTrue(functions.claim_overlaps(c["unit"], lin + 1, 2))


class IncludePins(unittest.TestCase):
    """F-10: every header reached must be pinned; traversal refused; DOSBox mounts pinned files."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="gatefix"))
        (self.tmp / "INCLUDE" / "SYS").mkdir(parents=True)
        (self.tmp / "INCLUDE" / "A.H").write_bytes(b"int a;\n#include <sys/b.h>\n")
        (self.tmp / "INCLUDE" / "SYS" / "B.H").write_bytes(b"int b;\n")
        self.prof = {"directory": str(self.tmp), "include": "INCLUDE",
                     "include_files": {"a.h": self.h(b"int a;\n#include <sys/b.h>\n"), "sys/b.h": self.h(b"int b;\n")}}

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    @staticmethod
    def h(b):
        return hashlib.sha256(b).hexdigest()

    def test_pinned(self):
        out = compiler.expand_includes("#include <a.h>\n", self.prof)
        self.assertIn("int a;", out)
        self.assertIn("int b;", out)

    def test_unpinned_or_changed(self):
        del self.prof["include_files"]["sys/b.h"]
        with self.assertRaises(compiler.CompileError):
            compiler.expand_includes("#include <a.h>\n", self.prof)
        self.prof["include_files"]["sys/b.h"] = self.h(b"int c;\n")
        with self.assertRaises(compiler.CompileError):
            compiler.expand_includes("#include <a.h>\n", self.prof)

    def test_traversal(self):
        for name in ("<../INCLUDE/A.H>", '"../layout/x.h"', "<C:/x.h>", "</x.h>"):
            with self.assertRaises(compiler.CompileError, msg=name):
                compiler.expand_includes(f"#include {name}\n", self.prof)

    def test_pinned_tree(self):
        (self.tmp / "BIN").mkdir()
        (self.tmp / "BIN" / "CL.EXE").write_bytes(b"MZ-test-" + os.urandom(8))
        (self.tmp / "BIN" / "EXTRA.EXE").write_bytes(b"not pinned")
        prof = {"directory": str(self.tmp), "files": {"BIN/CL.EXE": self.h((self.tmp / "BIN" / "CL.EXE").read_bytes())}}
        d = compiler.pinned_tree(prof)
        try:
            self.assertEqual(sorted(p.relative_to(d).as_posix() for p in d.rglob("*") if p.is_file()), ["BIN/CL.EXE"])
            (d / "BIN" / "CL.EXE").write_bytes(b"tampered")
            compiler._pinned_ok.discard(str(d))
            with self.assertRaises(compiler.CompileError):
                compiler.pinned_tree(prof)
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_toolchain_pins_cover_sources(self):
        tc = compiler.toolchain()
        for name, prof in tc["profiles"].items():
            if prof.get("include_directory") or prof.get("include"):
                self.assertIn("include_files", prof, f"{name}: run the gatefix migration (pin_includes.py)")


class HelperInputs(unittest.TestCase):
    """variants.py takes directories and list files; records.py --all-lines dumps line entries."""

    def test_variants_sources(self):
        import variants
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            (d / "v").mkdir()
            for n in ("b.c", "a.c", "x.txt", "c.asm"):
                (d / "v" / n).write_text("x")
            (d / "list.txt").write_text("# variants\nv/a.c\n\n" + str(d / "v" / "b.c") + "\n")
            got = variants.expand_sources([d / "v"], d / "list.txt")
            self.assertEqual([p.name for p in got], ["a.c", "b.c", "c.asm", "a.c", "b.c"])
            self.assertEqual(got[3], d / "v" / "a.c")

    def test_records_all_lines(self):
        env = dict(os.environ, MSYS_NO_PATHCONV="1", MSYS2_ARG_CONV_EXCL="*")
        r = subprocess.run([sys.executable, str(ROOT / "tools" / "records.py"), "root:29F0", "--all-lines"],
                           capture_output=True, text=True, cwd=ROOT, env=env)
        self.assertEqual(r.returncode, 0, r.stderr[-1500:])
        self.assertIn("line entries (", r.stdout)
        self.assertIn("f_29F0_0038", r.stdout.split("line entries (")[-1])


def promote(*args):
    env = dict(os.environ, MSYS_NO_PATHCONV="1", MSYS2_ARG_CONV_EXCL="*")
    r = subprocess.run([sys.executable, str(ROOT / "tools" / "promote.py"), *map(str, args), "--verify-only"],
                       capture_output=True, text=True, cwd=ROOT, env=env)
    return r.returncode, r.stdout + r.stderr


class AuditNegatives(unittest.TestCase):
    """Every negative of the adversarial audit is refused, for its reason (F-1..F-11)."""

    def refused(self, why, *args):
        rc, out = promote(*args)
        self.assertNotEqual(rc, 0, f"ACCEPTED: {args}\n{out[-1500:]}")
        self.assertIn(why, out, out[-1500:])

    def test_positive_controls(self):
        for key in ("root:277D", "root:29F0", "root:1959"):
            m = modules.load_manifest()["modules"][key]
            rc, out = promote(ROOT / m["source"], "--module", key)
            self.assertEqual(rc, 0, out[-1500:])

    def test_T1_permutation(self):
        self.refused("not one object placement", NEG / "T1_m277D_permuted.c", "--module", "root:277D")
        self.refused("not one object placement", NEG / "T1c_m29F0_reversed.c", "--module", "root:29F0")
        self.refused("not one object placement", NEG / "T1b_m15D9_swapped.c", "--module", "root:15D9")

    def test_T2_foreign_and_duplicate_data(self):
        self.refused("alignment", NEG / "T2_m277D_foreign_data.c", "--module", "root:277D",
                     "--placement", "_DATA=55B3:1C49:41")
        self.refused("overlaps", NEG / "T2b_m277D_duplicate_data.c", "--module", "root:277D",
                     "--placement", "_DATA=55B3:7564:2")
        self.refused("overlaps", NEG / "T12_m277D_permuted_dupdata.c", "--module", "root:277D",
                     "--placement", "_DATA=55B3:7564:2")

    def test_T4_opcode_capsules(self):
        self.refused("inside proc", NEG / "T4_m1959_db_capsule.asm", "--module", "root:1959")
        self.refused("_emit", NEG / "T4b_m29F0_emit.c", "--module", "root:29F0")

    def test_T5_unsteer_unchanged(self):
        man = modules.load_manifest()
        hit = next(((k, c["name"]) for k, m in man["modules"].items() for c in m["claims"]
                    if c.get("provenance") == "EXACT_STEERED"), None)
        if hit is None:
            self.skipTest("no steered claim")
        key, name = hit
        self.refused("unchanged", ROOT / man["modules"][key]["source"], "--module", key,
                     "--unsteer", f"{name}=audit: false assertion")

    def test_T6_trimmed_extents(self):
        self.refused("outside the extent", NEG / "T6_m29F0_trimmed.c", "--module", "root:29F0",
                     "--release", "f_29F0_0038=audit", "--extent", "29F0A:29F38")
        self.refused("outside the extent", NEG / "T6b_m29F0_head_trimmed.c", "--module", "root:29F0",
                     "--release", "f_29F0_000A=audit", "--extent", "29F12:29F4C")

    def test_T7_pascal_declaration_of_cdecl(self):
        self.refused("TICKCOUNT", NEG / "T7_m15D9_pascal.c", "--module", "root:15D9")

    def test_T8_invented_object(self):
        args = (NEG / "T8_m29F0_at0038_split.c", "--module", "root:29F0@0038", "--claim", "f_29F0_0038",
                "--profile", "msc600ax", "--flags", "/AL", "/Os", "/Gs", "/Zi", "--extent", "29F38:29F4C")
        self.refused("--origin-evidence", *args)
        self.refused("beyond frame offset", *args, "--origin-evidence", "audit: invented")

    def test_G_asm_and_include_rules(self):
        self.refused("numeric branch target", NEG / "G1_m1959_numeric_target.asm", "--module", "root:1959")
        self.refused("path traversal", NEG / "G2_m29F0_include_traversal.c", "--module", "root:29F0")
        self.refused("'org'", NEG / "G3_m1959_org.asm", "--module", "root:1959")


if __name__ == "__main__":
    unittest.main()
