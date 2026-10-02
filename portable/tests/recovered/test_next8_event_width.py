"""Regression for the versioned next8 native Event.code width correction."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
WRAPPER = ROOT / "portable/tools/recover_source_next8.py"
NEXT7_WRAPPER_SHA256 = "0cbdcc6d904f704cf3627742d88fa87f157aaaae9ccf9f8b828df2fc3a01b5af"
NEXT8 = ROOT / "build/workers/recovered_source_next8/generated"
NEXT7 = ROOT / "build/workers/recovered_source_next7/generated"
ARCHIVE = ROOT / "portable/tests/recovered/evidence/next8-event-width-v1"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Next8EventWidthTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.build = subprocess.run([sys.executable, str(WRAPPER)], cwd=ROOT,
                                   text=True, capture_output=True)
        if cls.build.returncode:
            raise RuntimeError(cls.build.stdout + cls.build.stderr)
        cls.provenance = json.loads((NEXT8 / "provenance.json").read_text(encoding="utf-8"))
        cls.extension = cls.provenance["versioned_profile_extension_next8"]
        cls.parent = json.loads((NEXT7 / "provenance.json").read_text(encoding="utf-8"))

    def test_profile_changes_only_s24_and_compiles_all_translation_units(self):
        self.assertEqual(sha(WRAPPER), self.extension["wrapper_sha256"])
        self.assertEqual(sha(ROOT / "portable/tools/recover_source_next7.py"), NEXT7_WRAPPER_SHA256)
        parent_hashes = {row["name"]: row["generated_sha256"] for row in self.parent["modules"]}
        child_hashes = {row["name"]: row["generated_sha256"] for row in self.provenance["modules"]}
        changed = {name for name in parent_hashes if parent_hashes[name] != child_hashes[name]}
        self.assertEqual(changed, {"S24_m39C7"})
        self.assertEqual(len(child_hashes), 25)
        self.assertTrue(all(row["compile"]["passed"] for row in self.provenance["modules"]))
        self.assertEqual(self.extension["lowering"]["before_generated_sha256"], parent_hashes["S24_m39C7"])
        self.assertEqual(self.extension["lowering"]["after_generated_sha256"], child_hashes["S24_m39C7"])
        for name in ("recovered_state.h", "recovered_state.c"):
            self.assertEqual(sha(NEXT7 / name), sha(NEXT8 / name))
        self.assertIn("uint16_t code;", (NEXT8 / "S24_m39C7.c").read_text(encoding="utf-8"))
        self.assertNotIn("unsigned code;", (NEXT8 / "S24_m39C7.c").read_text(encoding="utf-8"))

    def test_actual_dos_directed_cases_match_native_function_trace(self):
        evidence = self.extension["directed_dos_native_cases"]
        self.assertTrue(self.extension["directed_dos_native_cases"]["candidate_strict_exact"]["exact"])
        self.assertEqual(evidence["directed_count"], 64)
        self.assertEqual(evidence["mismatches"], 0)
        self.assertEqual(evidence["errors"], 0)
        self.assertEqual(evidence["native_vs_original_trace_mismatches"], 0)
        self.assertEqual(len(evidence["cases"]), 64)
        for row in evidence["cases"]:
            self.assertTrue(row["exact_candidate_match"], row["case"])
            self.assertTrue(row["native_matches_oracle_trace"], row["case"])
        domains = {(row["code"], row["xE"]) for row in evidence["cases"]}
        for code in range(0x1503, 0x150f):
            for xE in (0, 1, 0x7fff, 0x8000):
                self.assertIn((code, xE), domains)

    def test_old_host_width_is_a_negative_control(self):
        controls = self.extension["directed_dos_native_cases"]["negative_old_width_control"]
        self.assertEqual(controls["150d/0000"], [[1, 0x150f, 0, 0]])
        self.assertEqual(controls["150d/0001"], [])
        self.assertEqual(controls["150e/0001"], [])
        self.assertEqual(controls["1503/0001"], [])
        self.assertEqual(self.extension["host_width_controls"]["input_contract"],
                         "DOS-layout 16-byte Event record; code word at +0x0c; following xE word at +0x0e")

    def test_archived_packet_hashes_and_excludes_binaries(self):
        sums = json.loads((ARCHIVE / "SHA256SUMS.json").read_text(encoding="utf-8"))
        self.assertEqual(sums["schema"], "simant-evidence-file-hashes-v1")
        for relative, expected in sums["files"].items():
            path = ARCHIVE / relative
            self.assertTrue(path.is_file(), relative)
            self.assertEqual(sha(path), expected, relative)
            self.assertFalse(path.suffix.lower() in {".exe", ".o", ".obj", ".dll"}, relative)
        archived = json.loads((ARCHIVE / "evidence.json").read_text(encoding="utf-8"))
        self.assertEqual(archived["suite"]["directed_count"], 64)
        self.assertEqual(len(archived["suite"]["cases"]), 64)
        self.assertEqual(sha(ARCHIVE / "producer/recover_source_next8.py"),
                         self.extension["wrapper_sha256"])


if __name__ == "__main__":
    unittest.main()
