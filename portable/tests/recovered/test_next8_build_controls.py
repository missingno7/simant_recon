"""Fail-closed portable build checks for the NEXT8 diagnostic profile."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[3]
PROFILE = ROOT / "build/workers/recovered_source_next8/generated"


def load_build_module():
    spec = importlib.util.spec_from_file_location("simant_build_next8_controls",
                                                  ROOT / "portable/build.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class Next8BuildControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.build_module = load_build_module()
        cls.base = json.loads((PROFILE / "provenance.json").read_text(encoding="utf-8"))

    def assert_rejected_before_compile(self, label, mutate, expected):
        with tempfile.TemporaryDirectory(prefix="next8-build-control-",
                                         dir=ROOT / "build/workers") as temp:
            scratch = Path(temp)
            profile = scratch / "profile"
            profile.mkdir()
            provenance = json.loads(json.dumps(self.base))
            mutate(provenance)
            (profile / "provenance.json").write_text(json.dumps(provenance), encoding="utf-8")
            output = scratch / "rejected.exe"

            def no_compile(command, *args, **kwargs):
                if any(Path(str(part)).name == "oracle_checkpoint.py" for part in command):
                    frozen = Path(command[command.index("--output") + 1])
                    frozen.write_text(json.dumps({"ready": True}), encoding="utf-8")
                    return mock.Mock(returncode=0, stdout="", stderr="")
                raise AssertionError(f"invalid profile reached compilation or another subprocess: {command}")

            with mock.patch.object(self.build_module.subprocess, "run", side_effect=no_compile):
                with self.assertRaises(SystemExit) as caught:
                    self.build_module.build(ROOT / "portable/main.c", output, [], profile)
            self.assertIn(expected, str(caught.exception), label)
            self.assertFalse(output.exists(), label)

    def test_wrong_event_member_type_rejected(self):
        self.assert_rejected_before_compile(
            "wrong-member-type",
            lambda p: p["versioned_profile_extension_next8"]["lowering"].update(
                host_member_type="uint32_t (incorrect host width)"),
            "Unreviewed history-event word ABI")

    def test_unexpected_changed_function_rejected(self):
        self.assert_rejected_before_compile(
            "wrong-function",
            lambda p: p["versioned_profile_extension_next8"]["lowering"].update(
                changed_function="OtherFunction"),
            "Unreviewed history-event word ABI")

    def test_parent_state_hash_drift_rejected(self):
        self.assert_rejected_before_compile(
            "parent-state-drift",
            lambda p: p["versioned_profile_extension_next8"]["parent_profile"][
                "state_hashes"].update({"recovered_state.h": "0" * 64}),
            "History-event lowering changed its profile boundary")

    def test_unknown_extension_key_rejected(self):
        self.assert_rejected_before_compile(
            "unknown-extension",
            lambda p: p.update(versioned_profile_extension_next10={"id": "unreviewed"}),
            "Unreviewed recovered profile generation")


if __name__ == "__main__":
    unittest.main()
