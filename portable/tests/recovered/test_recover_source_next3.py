from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
BASE_GENERATOR = ROOT / "portable/tools/recover_source.py"
NEXT3_GENERATOR = ROOT / "portable/tools/recover_source_next3.py"
NEXT2_RECIPE = ROOT / "portable/docs/recovered-source-next2-recipe.md"

EXPECTED_ADDITIONS = {
    "fd_50F6_08DE": ("RecoveredXY", "08DE", "extern Pnt far fd_50F6_08DE;"),
    "fd_50F6_0AD8": ("int16_t", "0AD8", "extern int far fd_50F6_0AD8;"),
    "fd_50F6_09F2": ("RecoveredXY", "09F2", "extern Pnt far fd_50F6_09F2;"),
    "fd_50F6_0B06": ("int16_t", "0B06", "extern int far fd_50F6_0B06;"),
    "fd_50F6_0A8A": ("RecoveredXY", "0A8A", "extern Pnt far fd_50F6_0A8A;"),
    "fd_50F6_0C3A": ("int16_t", "0C3A", "extern int far fd_50F6_0C3A;"),
    "fd_50F6_0AB2": ("RecoveredXY", "0AB2", "extern Pnt far fd_50F6_0AB2;"),
    "fd_50F6_0D9A": ("int16_t", "0D9A", "extern int far fd_50F6_0D9A;"),
    "fd_50F6_0ACA": ("int16_t", "0ACA", "extern int far fd_50F6_0ACA;"),
    "fd_50F6_0AEA": ("int16_t", "0AEA", "extern int far fd_50F6_0AEA;"),
    "fd_50F6_0B08": ("int16_t", "0B08", "extern int far fd_50F6_0B08;"),
    "fd_50F6_0D68": ("int16_t", "0D68", "extern int far fd_50F6_0D68;"),
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class RecoveredSourceNext3Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tmp = tempfile.TemporaryDirectory(dir=ROOT / "build/workers")
        cls.temp_root = Path(cls.tmp.name)
        cls.base_out = cls.temp_root / "next2-base" / "generated"
        cls.next3_out = cls.temp_root / "next3" / "generated"
        subprocess.run(["python", str(BASE_GENERATOR), "--out", str(cls.base_out), "--compile"],
                       cwd=ROOT, check=True, capture_output=True, text=True)
        subprocess.run(["python", str(NEXT3_GENERATOR), "--out", str(cls.next3_out), "--compile"],
                       cwd=ROOT, check=True, capture_output=True, text=True)
        cls.base_report = json.loads((cls.base_out / "provenance.json").read_text(encoding="utf-8"))
        cls.next3_report = json.loads((cls.next3_out / "provenance.json").read_text(encoding="utf-8"))

    @classmethod
    def tearDownClass(cls) -> None:
        cls.tmp.cleanup()

    def test_only_twelve_layout_and_source_pinned_balloon_fields_are_added(self) -> None:
        base_state = self.base_report["recovered_state"]
        next_state = self.next3_report["recovered_state"]
        base_fields = {row["name"]: row for row in base_state["fields"]}
        next_fields = {row["name"]: row for row in next_state["fields"]}
        self.assertEqual(set(next_fields) - set(base_fields), set(EXPECTED_ADDITIONS))
        self.assertEqual(set(base_fields) - set(next_fields), set())
        evidence = self.next3_report["versioned_profile_extension"]["added_fields"]
        data_symbols = json.loads((ROOT / "layout/symbols.json").read_text(encoding="utf-8"))["data"]
        source = (ROOT / "src/root/m0250.c").read_text(encoding="utf-8")
        for name, (expected_type, expected_off, declaration) in EXPECTED_ADDITIONS.items():
            with self.subTest(field=name):
                row = next_fields[name]
                ev = evidence[name]
                seg, off = ev["layout_segment"], ev["layout_offset"]
                self.assertEqual((row["type"], row["dims"]), (expected_type, []))
                self.assertEqual((seg, f"{off:04X}"), (0x50F6, expected_off))
                self.assertEqual((int(data_symbols[name]["seg"]), int(data_symbols[name]["off"])), (seg, off))
                self.assertEqual(ev["source_path"], "src/root/m0250.c")
                self.assertEqual(ev["source_declaration"], declaration)
                self.assertEqual(source.splitlines()[ev["source_line"] - 1].strip(), declaration)
                self.assertEqual(ev["source_sha256"], sha(ROOT / "src/root/m0250.c"))
                self.assertEqual(ev["layout_sha256"], sha(ROOT / "layout/symbols.json"))
                self.assertEqual(ev["storage_bytes"], 4 if expected_type == "RecoveredXY" else 2)

    def test_all_old_state_initial_values_are_byte_identical_and_bodies_match_next2(self) -> None:
        base_state = self.base_report["recovered_state"]
        next_state = self.next3_report["recovered_state"]
        base_fields = {row["name"]: row for row in base_state["fields"]}
        next_fields = {row["name"]: row for row in next_state["fields"]}
        for name, old in base_fields.items():
            self.assertEqual((next_fields[name]["type"], next_fields[name]["dims"]),
                             (old["type"], old["dims"]), name)
        base_initializers = {row["field"]["name"]: row for row in base_state["source_defined_initializers"]}
        next_initializers = {row["field"]["name"]: row for row in next_state["source_defined_initializers"]}
        self.assertEqual(set(base_initializers), set(next_initializers))
        for name, old in base_initializers.items():
            new = next_initializers[name]
            for key in ("source_type", "source_dims", "source_bytes", "initializer_sha256", "source_sha256"):
                self.assertEqual(new[key], old[key], f"{name}.{key}")

        # Compare runtime object-representation defaults field by field, thereby
        # excluding only the twelve new fields and ignoring changed struct offsets.
        old_names = list(base_fields)
        program = """#include <stdio.h>\n#include "recovered_state.h"\nint main(void) {\n    RecoveredState s;\n    recovered_state_init(&s);\n"""
        program += "".join(f"    if (fwrite(&s.{name}, sizeof(s.{name}), 1, stdout) != 1) return 2;\n"
                            for name in old_names)
        program += "    return 0;\n}\n"
        outputs = []
        for label, out in (("next2", self.base_out), ("next3", self.next3_out)):
            source_path = self.temp_root / f"defaults-{label}.c"
            executable = self.temp_root / f"defaults-{label}.exe"
            source_path.write_text(program, encoding="utf-8")
            subprocess.run(["gcc", "-std=c11", "-Wall", "-Wextra", "-Werror",
                            "-I", str(out), str(source_path), str(out / "recovered_state.c"),
                            "-o", str(executable)], cwd=ROOT, check=True,
                           capture_output=True, text=True)
            outputs.append(subprocess.run([str(executable)], cwd=ROOT, check=True,
                                           capture_output=True).stdout)
        self.assertEqual(outputs[0], outputs[1])

        expected_body_hashes = {}
        for line in NEXT2_RECIPE.read_text(encoding="utf-8").splitlines():
            match = re.match(r"\| `([^`]+)` \| `[0-9a-f]{64}` \| `([0-9a-f]{64})` \|", line)
            if match:
                expected_body_hashes[match.group(1)] = match.group(2)
        self.assertEqual(len(expected_body_hashes), 23)
        next3_modules = {row["name"]: row for row in self.next3_report["modules"]}
        base_modules = {row["name"]: row for row in self.base_report["modules"]}
        self.assertEqual(set(next3_modules), set(expected_body_hashes))
        for name, expected_hash in expected_body_hashes.items():
            generated_name = Path(next3_modules[name]["generated"]).name
            self.assertEqual(sha(self.next3_out / generated_name), expected_hash, name)
            self.assertEqual(sha(self.base_out / generated_name), expected_hash, name)
            self.assertEqual((self.base_out / generated_name).read_bytes(),
                             (self.next3_out / generated_name).read_bytes(), name)
            self.assertTrue(next3_modules[name]["compile"]["passed"], name)
        self.assertTrue(self.next3_report["support_compile"]["passed"])

    def test_extension_identity_does_not_masquerade_as_base_generator_identity(self) -> None:
        extension = self.next3_report["versioned_profile_extension"]
        self.assertEqual(extension["id"], "balloon-source-state-next3-v1")
        self.assertEqual(extension["base_generator_sha256"],
                         "c1fd7616c392d39ebe4574e6ccde85b4e7f79205d21afcfbcb7ead249d5ffc50")
        self.assertEqual(extension["wrapper_sha256"], sha(NEXT3_GENERATOR))
        self.assertEqual(self.next3_report["generator_sha256"], extension["base_generator_sha256"])
        self.assertEqual(self.next3_report["status"], "DIAGNOSTIC_ONLY_NOT_PRODUCTION")


if __name__ == "__main__":
    unittest.main()
