"""Fail-closed tests for the read-only DOS oracle checkpoint audit."""
from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from tools import oracle_checkpoint


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class CheckpointFixture:
    def __init__(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        for rel in ("assets", "build/link", "docs", "evidence/behavior", "layout",
                    "tools", "work/takeover/behavioral-oracle"):
            (self.root / rel).mkdir(parents=True, exist_ok=True)
        self.oracle = b"original executable"
        (self.root / "assets/SIMANT.EXE").write_bytes(self.oracle)
        (self.root / "build/link/SIMANT.HYBRID.EXE").write_bytes(self.oracle)
        (self.root / "tools/validate.py").write_text("validator\n")
        (self.root / "tools/link.py").write_text("linker\n")
        (self.root / "layout/toolchain.json").write_text("{}\n")
        (self.root / "tools/behavior_validate.py").write_text("behavior gate\n")
        self.exact = {"unit": "root:test", "seg": 1, "off": 2, "size": 3}
        self.behavior = {"unit": "root:test", "seg": 1, "off": 5, "size": 4}
        (self.root / "layout/functions.json").write_text(json.dumps({"functions": [
            {**self.exact, "region": "game_or_library", "name": "exact_fn"},
            {**self.behavior, "region": "game_or_library", "name": "behavior_fn"},
        ]}))
        (self.root / "layout/manifest.json").write_text(json.dumps({"modules": {
            "root:test": {"claims": [{**self.exact, "name": "exact_fn"}]}}}))
        self.evidence_path = self.root / "evidence/behavior/evidence.json"
        self.run_path = self.root / "evidence/behavior/run.json"
        self.run = {"cases": {"directed": {"generated": 3, "executed": 3},
                              "randomized": {"generated": 5, "executed": 5}}}
        self.run_path.write_text(json.dumps(self.run))
        self.evidence_path.write_text(json.dumps({"suite": {"id": "fixture-suite"}, "run_report": {
            "path": "evidence/behavior/run.json", "sha256": digest(self.run_path.read_bytes())}}))
        (self.root / "evidence/behavior/manifest.json").write_text(json.dumps({"entries": {
            "behavior_fn": {"status": "BEHAVIOR_EXACT", "initial_target_bytes": 4,
                            "evidence_path": "evidence/behavior/evidence.json",
                            "evidence_sha256": digest(self.evidence_path.read_bytes())}}}))
        self.data = {"schema": "simant-behavior-data-debt-v1",
                     "oracle_sha256": digest(self.oracle),
                     "source_pins": [], "literal_spans": [],
                     "reconciliation": {"progress_residual": 0,
                         "literal_debt_bytes": 0, "section27_common_tail_overlap_bytes": 0,
                         "progress_matches_provenance": True}}
        (self.root / "work/takeover/behavioral-oracle/data-debt.json").write_text(json.dumps(self.data))
        self.progress = {"validation": "PASS", "oracle_sha256": digest(self.oracle),
                         "known_game_functions": 2, "unresolved_code_bytes": 6,
                         "unresolved_data_bytes": 0, "rtlink_manager_bytes_unaccepted": 17001,
                         "exact_c_functions": 1, "exact_asm_functions": 0,
                         "exact_c_bytes": 10, "exact_asm_bytes": 0}
        (self.root / "docs/progress.json").write_text(json.dumps(self.progress))
        provenance = {"oracle_sha256": digest(self.oracle), "hybrid_sha256": digest(self.oracle),
                      "hybrid_equal": True}
        (self.root / "build/link/provenance.json").write_text(json.dumps(provenance))
        self.validation = {"valid": True,
            "categories": {"EXACT": 1, "BEHAVIOR_EXACT": 1, "UNRESOLVED": 0},
            "registered_behavior": {"behavior_fn": {"valid": True}}}
        (self.root / "evidence/behavior/all.json").write_text(json.dumps(self.validation))
        (self.root / "work/takeover/behavioral-oracle/historical.log").write_text("VALIDATION PASS\n")
        self.gap_path = self.root / "evidence/gap-review.json"
        self.gap_path.write_text(json.dumps({"schema": "simant-code-gap-review-bundle-v1",
            "review": {"status": "APPROVED", "reviewer": "root"},
            "contracts": [{"address": "root:test+0x8", "covered_bytes": 2,
                           "ranges": [{"unit": "root:test", "seg": 1, "start": 8, "end": 10}],
                           "status": "APPROVED", "reason": "fixture gap"}]}))
        trees = oracle_checkpoint.current_validation_inputs(self.root)
        self.inputs_path = "work/takeover/behavioral-oracle/checkpoint-inputs.json"
        self.inputs = {
            "schema": "simant-oracle-checkpoint-inputs-v1",
            "review": {"status": "APPROVED", "reviewer": "root", "reviewed_at": "2026-10-02", "reason": "fixture"},
            "behavior_validation": {"path": "evidence/behavior/all.json",
                "sha256": digest((self.root / "evidence/behavior/all.json").read_bytes()),
                "registry_sha256": digest((self.root / "evidence/behavior/manifest.json").read_bytes()),
                "historical_manifest_sha256": digest((self.root / "layout/manifest.json").read_bytes()),
                "validator_sha256": digest((self.root / "tools/behavior_validate.py").read_bytes()),
                "source_tree_sha256": trees["source_tree_sha256"],
                "validation_inputs_sha256": trees["validation_inputs_sha256"]},
            "historical_validation": {"schema": "simant-historical-validation-pin-v1", "status": "PASS",
                "review": {"status": "APPROVED", "reviewer": "root", "reviewed_at": "2026-10-02", "reason": "fixture"},
                "log": {"path": "work/takeover/behavioral-oracle/historical.log",
                        "sha256": digest((self.root / "work/takeover/behavioral-oracle/historical.log").read_bytes())},
                "tools": {rel: {"path": rel, "sha256": digest((self.root / rel).read_bytes())}
                          for rel in ("tools/validate.py", "tools/link.py", "layout/toolchain.json")},
                "manifest_sha256": digest((self.root / "layout/manifest.json").read_bytes()),
                "source_tree_sha256": trees["source_tree_sha256"],
                "validation_inputs_sha256": trees["validation_inputs_sha256"]},
            "data_review": {"status": "APPROVED", "reviewer": "root", "reviewed_at": "2026-10-02",
                            "reason": "fixture disposition", "data_debt_sha256": digest((self.root / "work/takeover/behavioral-oracle/data-debt.json").read_bytes())},
            "gap_review_bundle": {"status": "APPROVED", "reviewer": "root", "reason": "fixture gap disposition",
                "artifact": {"path": "evidence/gap-review.json", "sha256": digest(self.gap_path.read_bytes())}},
        }
        (self.root / self.inputs_path).write_text(json.dumps(self.inputs))

    def write_inputs(self):
        (self.root / self.inputs_path).write_text(json.dumps(self.inputs))

    def close(self):
        self.temp.cleanup()


class OracleCheckpointTests(unittest.TestCase):
    def setUp(self):
        self.fx = CheckpointFixture()

    def tearDown(self):
        self.fx.close()

    def report(self):
        return oracle_checkpoint.build_report(self.fx.root, self.fx.inputs_path)

    def test_valid_fixture_is_ready_with_separate_rtlink_debt(self):
        result = self.report()
        self.assertTrue(result["ready"], result["errors"])
        self.assertEqual(result["proof_categories"], {"EXACT": 1, "BEHAVIOR_EXACT": 1, "UNRESOLVED": 0})
        self.assertEqual(result["rtlink_debt_bytes_separate_nonblocking"], 17001)
        self.assertEqual(result["behavior_case_totals"], {"directed": 3, "randomized": 5, "total": 8})
        self.assertEqual(result["behavior_suite_totals"]["fixture-suite"]["functions"], 1)

    def test_unresolved_registry_row_prevents_ready(self):
        registry_path = self.fx.root / "evidence/behavior/manifest.json"
        registry_path.write_text(json.dumps({"entries": {"behavior_fn": {"status": "UNRESOLVED"}}}))
        self.fx.validation["categories"]["BEHAVIOR_EXACT"] = 0
        self.fx.validation["categories"]["UNRESOLVED"] = 1
        self.fx.validation["registered_behavior"] = {}
        validation_path = self.fx.root / "evidence/behavior/all.json"
        validation_path.write_text(json.dumps(self.fx.validation))
        self.fx.inputs["behavior_validation"].update({
            "sha256": digest(validation_path.read_bytes()),
            "registry_sha256": digest(registry_path.read_bytes())})
        self.fx.write_inputs()
        result = self.report()
        self.assertFalse(result["ready"])
        self.assertEqual(result["proof_categories"]["UNRESOLVED"], 1)

    def test_hybrid_byte_mismatch_prevents_ready(self):
        (self.fx.root / "build/link/SIMANT.HYBRID.EXE").write_bytes(b"different hybrid")
        result = self.report()
        self.assertFalse(result["ready"])
        self.assertTrue(any("hybrid image bytes/hash differ" in error for error in result["errors"]))

    def test_stale_behavior_all_report_prevents_ready(self):
        path = self.fx.root / "evidence/behavior/all.json"
        path.write_text(path.read_text() + " ")
        result = self.report()
        self.assertFalse(result["ready"])
        self.assertTrue(any("behavior --all validation report: stale" in error for error in result["errors"]))

    def test_source_change_after_historical_validation_prevents_ready(self):
        (self.fx.root / "tools/validate.py").write_text("changed validator\n")
        result = self.report()
        self.assertFalse(result["ready"])
        self.assertTrue(any("stale for current validation_inputs_sha256" in error for error in result["errors"]))

    def test_duplicate_gap_ranges_cannot_fake_coverage(self):
        bundle = json.loads(self.fx.gap_path.read_text())
        contract = bundle["contracts"][0]
        contract["ranges"] = [{"unit": "root:test", "seg": 1, "start": 8, "end": 9}] * 2
        self.fx.gap_path.write_text(json.dumps(bundle))
        self.fx.inputs["gap_review_bundle"]["artifact"]["sha256"] = digest(self.fx.gap_path.read_bytes())
        self.fx.write_inputs()
        result = self.report()
        self.assertFalse(result["ready"])
        self.assertTrue(any("overlaps another" in error for error in result["errors"]))

    def test_gap_extent_must_match_covered_bytes(self):
        bundle = json.loads(self.fx.gap_path.read_text())
        bundle["contracts"][0]["ranges"][0]["end"] = 11
        self.fx.gap_path.write_text(json.dumps(bundle))
        self.fx.inputs["gap_review_bundle"]["artifact"]["sha256"] = digest(self.fx.gap_path.read_bytes())
        self.fx.write_inputs()
        result = self.report()
        self.assertFalse(result["ready"])
        self.assertTrue(any("range lengths" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
