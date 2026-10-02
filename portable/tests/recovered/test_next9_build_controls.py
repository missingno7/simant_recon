"""Reject changes to the reviewed save-state extension before compilation."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from portable.tools.profile_next9 import validate_next9

ROOT = Path(__file__).resolve().parents[3]


class Next9BuildControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = json.loads((ROOT / "build/workers/recovered_source_next9/generated/provenance.json").read_text())

    def test_reviewed_profile(self):
        pins, inherited = validate_next9(self.base)
        self.assertEqual(len(pins), 4)
        self.assertEqual(inherited, self.base["versioned_profile_extension_next8"]["parent_profile"]["state_hashes"])

    def reject(self, change, reason):
        p = copy.deepcopy(self.base)
        change(p)
        with self.assertRaisesRegex(SystemExit, reason):
            validate_next9(p)

    def test_changed_parent(self):
        self.reject(lambda p: p["versioned_profile_extension_next9"].update(parent_wrapper_sha256="0" * 64), "ancestry")

    def test_changed_producer(self):
        self.reject(lambda p: p["versioned_profile_extension_next9"].update(producer_sha256="0" * 64), "ancestry")

    def test_missing_projection_proof(self):
        self.reject(lambda p: p["versioned_profile_extension_next9"].update(inherited_state_projection_byte_identical=False), "ancestry")

    def test_reordered_state(self):
        self.reject(lambda p: p["recovered_state"]["next9_added_members"].reverse(), "layout")

    def test_changed_state_identity(self):
        self.reject(lambda p: p["recovered_state"].update(header_sha256="0" * 64), "layout")

    def test_changed_inherited_module(self):
        self.reject(lambda p: p["modules"][0].update(generated_sha256="0" * 64), "simulation modules")

    def test_stale_object_generation(self):
        self.reject(lambda p: p["modules"][0]["compile"].update(next9_recompiled=False), "simulation modules")

    def test_wrong_row29_byte_policy(self):
        self.reject(lambda p: p["versioned_profile_extension_next9"]["binding_schema"]["storage_exceptions"][0].update(policy="RAW_BYTES"), "save binding")

    def test_wrong_row99_numeric_policy(self):
        self.reject(lambda p: p["versioned_profile_extension_next9"]["binding_schema"]["storage_exceptions"][1].update(policy="NATIVE_NUMERIC_16"), "save binding")

    def test_wrong_initializer(self):
        self.reject(lambda p: p["versioned_profile_extension_next9"]["source_initializer_check"].update(initialized_slice_hex="00" * 20), "initializer")

    def test_build_rejects_before_compilation(self):
        spec = importlib.util.spec_from_file_location("next9_builder", ROOT / "portable/build.py")
        builder = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(builder)
        changes = (
            (lambda p: p["recovered_state"].update(header_sha256="0" * 64), "layout"),
            (lambda p: p["modules"][0].update(generated_sha256="0" * 64), "simulation modules"),
            (lambda p: p["versioned_profile_extension_next9"].update(producer_sha256="0" * 64), "ancestry"),
        )
        for change, reason in changes:
            with self.subTest(reason=reason), tempfile.TemporaryDirectory(dir=ROOT / "build/workers") as temp:
                profile = Path(temp)
                p = copy.deepcopy(self.base)
                change(p)
                (profile / "provenance.json").write_text(json.dumps(p))
                output = profile / "must-not-exist.exe"

                def no_compile(command, *args, **kwargs):
                    if any(Path(str(part)).name == "oracle_checkpoint.py" for part in command):
                        Path(command[command.index("--output") + 1]).write_text('{"ready":true}')
                        return mock.Mock(returncode=0)
                    raise AssertionError(f"invalid profile reached subprocess: {command}")

                with mock.patch.object(builder.subprocess, "run", side_effect=no_compile):
                    with self.assertRaisesRegex(SystemExit, reason):
                        builder.build(ROOT / "portable/main.c", output, [], profile)
                self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
