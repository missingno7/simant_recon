from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[3]
GENERATOR = ROOT / "portable/tools/recover_source.py"
SPEC = importlib.util.spec_from_file_location("recover_source_init_views", GENERATOR)
assert SPEC and SPEC.loader
recover_source = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(recover_source)


class SourceInitializerViewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tmp = tempfile.TemporaryDirectory(dir=ROOT / "build/workers")
        cls.out = Path(cls.tmp.name) / "generated"
        subprocess.run(["python", str(GENERATOR), "--out", str(cls.out), "--compile"],
                       cwd=ROOT, check=True, capture_output=True, text=True)
        cls.report = json.loads((cls.out / "provenance.json").read_text(encoding="utf-8"))
        cls.fields = {row["name"]: row for row in cls.report["recovered_state"]["fields"]}

    @classmethod
    def tearDownClass(cls) -> None:
        cls.tmp.cleanup()

    def test_full_data_extents_have_source_backed_shapes_and_initializers(self) -> None:
        expected_bytes = {
            "Dx9": 10, "Dy9": 10, "TurnTab": 72, "IdealCaste": 14,
            "ModeTabB": 48, "PherMapRT": 0x800, "fd_3D57_0B14": 16,
            "fd_3D57_0B24": 18, "fd_3D57_0C1A": 4,
            "fd_3D57_02C2": 76, "fd_3D57_0798": 8, "fd_3D57_07C8": 4,
            "AlistM": 1001, "AlistS": 1001, "AlistT": 1001,
            "BlistM": 501, "BlistS": 501, "BlistT": 501,
            "RlistM": 501, "RlistS": 501, "RlistT": 501,
        }
        self.assertEqual(self.report["recovered_state"]["source_data_initializer_mismatches"], [])
        for name, byte_count in expected_bytes.items():
            with self.subTest(name=name):
                rows, mismatches = recover_source.source_data_initializers([self.fields[name]])
                self.assertEqual(mismatches, [])
                self.assertEqual(len(rows), 1)
                self.assertEqual(rows[0]["source_bytes"], byte_count)
        self.assertEqual(self.fields["Dx9"]["dims"], ["10"])
        self.assertEqual(self.fields["Dy9"]["dims"], ["10"])
        self.assertEqual(self.fields["TurnTab"]["dims"], ["9", "8"])
        self.assertEqual(self.fields["IdealCaste"]["dims"], ["7"])
        self.assertEqual(self.fields["ModeTabB"]["dims"], ["24"])

    def test_adjacent_map_views_have_one_backing_and_exact_data_spans(self) -> None:
        rows = self.report["recovered_state"]["adjacent_source_data_views"]
        row = next(view for view in rows if view["base"] == "fd_3D57_0164")
        self.assertEqual((row["address"], row["bytes"]), ("3D57:0164", 192))
        self.assertEqual([(x["symbol"], x["address"], x["offset"], x["source_bytes"])
                          for x in row["initializers"]], [
            ("fd_3D57_0164", "3D57:0164", 0, 32),
            ("fd_3D57_0184", "3D57:0184", 32, 160),
        ])
        header = (self.out / "recovered_state.h").read_text(encoding="utf-8")
        self.assertIn("uint8_t fd_3D57_0164[12][16];", header)
        self.assertNotIn("uint8_t fd_3D57_0184[10][16];", header)
        self.assertEqual(sum("fd_3D57_0184" in line for line in header.splitlines()), 0)
        translated = (self.out / "root_m0BE8.c").read_text(encoding="utf-8")
        self.assertIn("fd_3D57_0164[2 + (SRand1(6))][0]", translated)
        self.assertNotIn("fd_3D57_0184[", translated)

    def test_narrow_data_candidate_fails_closed(self) -> None:
        short = dict(self.fields["Dx9"], dims=["9"])
        rows, mismatches = recover_source.source_data_initializers([short])
        self.assertEqual(rows, [])
        self.assertEqual(len(mismatches), 1)
        self.assertEqual(mismatches[0]["source_bytes"], 10)
        self.assertEqual(mismatches[0]["candidate_state_bytes"], 9)
        self.assertEqual(mismatches[0]["status"], "NOT_INITIALIZED_TYPE_OR_EXTENT_MISMATCH")

    def test_next_profile_has_exactly_one_hash_pinned_reviewed_body(self) -> None:
        module = next(row for row in self.report["modules"] if row["name"] == "root_m0E2E")
        rows = module["reviewed_behavior_scaffold_bodies"]
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row["function"], "LessonDone")
        self.assertEqual(row["source_sha256"],
                         "c611660dde4da7117c3232aa06e597871394cc4112466d46559705b235424359")
        self.assertEqual(row["review_sha256"],
                         "1930667ce288db35aec4227619534a06b3a6e4e990e4a460f6f247818db96b32")
        self.assertEqual(row["replacement_scope"], "one named scaffold body only")
        self.assertEqual(row["function_aliases_applied"], {
            "f_00F8_02BE": "MacTickCount", "f_22BF_0A22": "win_IsWinInFront"})
        generated = (self.out / Path(module["generated"]).name).read_text(encoding="utf-8")
        self.assertIn("int16_t  LessonDone(int16_t lesson)", generated)
        self.assertNotIn("SCAFFOLD BEGIN: LessonDone", generated)
        # Whitelisting does not make unrelated scaffold bodies eligible.
        self.assertEqual(set(recover_source.REVIEWED_BEHAVIOR_SCAFFOLD_WHITELIST), {"root_m0E2E"})

    def test_reviewed_body_whitelist_rejects_stale_source_pin(self) -> None:
        source = (ROOT / "src/root/m0E2E.c").read_text(encoding="utf-8")
        spec = dict(recover_source.REVIEWED_BEHAVIOR_SCAFFOLD_WHITELIST["root_m0E2E"])
        spec["source_sha256"] = "0" * 64
        with mock.patch.dict(recover_source.REVIEWED_BEHAVIOR_SCAFFOLD_WHITELIST,
                             {"root_m0E2E": spec}):
            with self.assertRaisesRegex(ValueError, "source/evidence hash changed"):
                recover_source.restore_reviewed_behavior_scaffold("root_m0E2E", source)

    def test_navigation_globals_have_source_widths_and_full_edit_mode_table(self) -> None:
        expected = {
            "fd_50F6_0332": ("int16_t", []),
            "fd_50F6_0F36": ("int16_t", []),
            "fd_50F6_0AA6": ("int16_t", []),
            "fd_50F6_10E0": ("int16_t", []),
            "fd_50F6_10DE": ("int16_t", []),
            "fd_50F6_0D70": ("int16_t", []),
            "fd_3D57_07C0": ("int16_t", ["4"]),
        }
        for name, shape in expected.items():
            with self.subTest(name=name):
                self.assertEqual((self.fields[name]["type"], self.fields[name]["dims"]), shape)
        rows, mismatches = recover_source.source_data_initializers([self.fields["fd_3D57_07C0"]])
        self.assertEqual(mismatches, [])
        self.assertEqual(rows[0]["source_bytes"], 8)
        self.assertIn("root_m015B", {row["name"] for row in self.report["modules"]})

    def test_two_byte_source_array_initializes_scalar_word_view(self) -> None:
        field = self.fields["fd_3D57_07BE"]
        self.assertEqual((field["type"], field["dims"]), ("int16_t", []))
        rows, mismatches = recover_source.source_data_initializers([field])
        self.assertEqual(mismatches, [])
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["source_type"], "uint8_t")
        self.assertEqual(rows[0]["source_dims"], ["2"])
        self.assertEqual(rows[0]["source_bytes"], 2)
        self.assertTrue(rows[0]["byte_view"])
        self.assertIn("fd_3D57_07BE", {
            row["field"]["name"] for row in self.report["recovered_state"]["source_defined_initializers"]})

    def test_array_to_scalar_initialization_rejects_nonmatching_full_extent(self) -> None:
        narrow = dict(self.fields["fd_3D57_07BE"], type="int32_t")
        rows, mismatches = recover_source.source_data_initializers([narrow])
        self.assertEqual(rows, [])
        self.assertEqual(len(mismatches), 1)
        self.assertEqual(mismatches[0]["source_bytes"], 2)
        self.assertEqual(mismatches[0]["candidate_state_bytes"], 4)
        self.assertEqual(mismatches[0]["status"], "NOT_INITIALIZED_TYPE_OR_EXTENT_MISMATCH")

    def test_init_preserves_nonzero_tables_point_views_and_all_adjacent_bytes(self) -> None:
        source = r'''#include "recovered_state.h"
int main(void) {
    RecoveredState state;
    recovered_state_init(&state);
    if (sizeof(state.Dx9) != 10 || state.Dx9[9] != 0) return 1;
    if (sizeof(state.Dy9) != 10 || state.Dy9[9] != 0) return 2;
    if (sizeof(state.TurnTab) != 72 || state.TurnTab[8][2] != -2) return 3;
    if (sizeof(state.IdealCaste) != 14 || state.IdealCaste[6] != 2) return 4;
    if (sizeof(state.ModeTabB) != 48) return 5;
    if (sizeof(state.PherMapRT) != 0x800) return 6;
    if (sizeof(state.fd_3D57_0B14) != 16 || state.fd_3D57_0B14[1].x != 38) return 7;
    if (sizeof(state.fd_3D57_0B24[0].bytes) != 18) return 8;
    if (state.fd_3D57_0B24[0].point.x != 0x48 || state.fd_3D57_0B24[0].point.y != 0x3e) return 9;
    if (sizeof(state.fd_3D57_0C1A) != 4 || state.fd_3D57_0C1A[0] != 40) return 10;
    if (state.fd_3D57_0164[11][15] != 0) return 11;
    if (sizeof(state.AlistM) != 1001 || sizeof(state.BlistM) != 501 || sizeof(state.RlistM) != 501) return 12;
    if (state.fd_3D57_07BE != -1) return 13;
    if (state.fd_3D57_0828 != 0x003f || state.CurGndTileID != 1000) return 14;
    if (state.fd_3D57_0C22 != 0x00fd || state.fd_3D57_0C2C != 180) return 15;
    return 0;
}
'''
        with tempfile.TemporaryDirectory(dir=ROOT / "build/workers") as tmp:
            src = Path(tmp) / "init_control.c"
            exe = Path(tmp) / "init_control.exe"
            src.write_text(source, encoding="utf-8")
            subprocess.run(["gcc", "-std=c11", "-Wall", "-Wextra", "-Werror",
                            "-I", str(self.out), str(src),
                            str(self.out / "recovered_state.c"), "-o", str(exe)],
                           cwd=ROOT, check=True, capture_output=True, text=True)
            subprocess.run([str(exe)], cwd=ROOT, check=True, capture_output=True, text=True)


if __name__ == "__main__":
    unittest.main()
