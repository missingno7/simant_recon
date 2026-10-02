"""Boundary tests for root-approved batch packaging (never registry mutation)."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools/research/prepare_behavior_packets.py"
spec = importlib.util.spec_from_file_location("prepare_behavior_packets", SCRIPT)
package_batch_module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = package_batch_module
spec.loader.exec_module(package_batch_module)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class BatchPackageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.function = "FixtureFn"
        self.source = self.root / "src/module.c"
        self.source.parent.mkdir(parents=True)
        self.source.write_bytes(b"void FixtureFn(void) {}")
        self.suite = self.root / "evidence/behavior/suites/suite.py"
        self.suite.parent.mkdir(parents=True, exist_ok=True)
        self.suite.write_bytes(b"SUITE='v1'\n")
        self.contract_review = {"status": "APPROVED", "reviewer": "root",
                                "reviewed_at": "2026-10-02", "reason": "fixture review"}
        self.review_path = self.root / "approved-review.json"
        self.review = {"function": self.function, "source": "src/module.c", "suite": "evidence/behavior/suites/suite.py",
                       "suite_id": "fixture-v1", "module": "root:fixture",
                       "date": "2026-10-02", "checkpoint": {"commit": "a" * 40, "date": "2026-10-02"},
                       "contract": {"id": "fixture", "review": dict(self.contract_review)},
                       "negative_controls": "negative.json",
                       "positive_controls": [], "helper_boundaries": [],
                       "historical_difference": {"description": "fixture", "reason_exact_stopped": "fixture", "evidence_refs": ["fixture"]},
                       "semantic_evidence": ["fixture"]}
        (self.root / "negative.json").write_text(json.dumps({"errors": 0, "mismatches_detected": 1}))
        self.review_path.write_text(json.dumps(self.review))
        self.ledger_path = self.root / "cases.jsonl"
        self.ledger_path.write_text("{}\n")
        self.run_path = self.root / "run.json"
        self.identity = {"function": self.function,
            "source_sha256": sha(self.source.read_bytes()),
            "suite_sha256": sha(self.suite.read_bytes()),
            "object_sha256": sha(b"fixture object"), "oracle_sha256": sha(b"fixture oracle"),
            "harness_sha256": sha(b"fixture harness"), "manifest_sha256": sha(b"fixture manifest")}
        self.run = {"schema": "behavior-run-evidence-v1", "completion": "COMPLETE",
                    "identity": self.identity,
                    "case_ledger": {"path": "cases.jsonl", "sha256": sha(self.ledger_path.read_bytes()),
                        "identity": {"source_sha256": self.identity["source_sha256"],
                            "object_sha256": self.identity["object_sha256"],
                            "oracle_sha256": self.identity["oracle_sha256"],
                            "harness_sha256": self.identity["harness_sha256"],
                            "manifest_sha256": self.identity["manifest_sha256"]}},
                    "errors": 0, "mismatches": 0}
        self.run_path.write_text(json.dumps(self.run))
        self.dest = "evidence/behavior/functions/FixtureFn/review-batch-test"
        self.manifest_path = self.root / "batch.json"
        self.entry = {"function": self.function,
            "review": {"path": "approved-review.json", "sha256": sha(self.review_path.read_bytes())},
            "run": {"path": "run.json", "sha256": sha(self.run_path.read_bytes())},
            "destination": self.dest}
        self.write_manifest()
        self.package_mock = patch.object(package_batch_module.behavior_packet, "package")
        self.mock = self.package_mock.start()
        self.addCleanup(self.package_mock.stop)

    def write_manifest(self, *, review=None):
        self.manifest_path.write_text(json.dumps({"schema": package_batch_module.SCHEMA,
            "review": {"status": "APPROVED", "reviewer": "root",
                       "reviewed_at": "2026-10-02", "reason": "explicit fixture batch"},
            "entries": [self.entry if review is None else review]}))

    def tearDown(self):
        self.temp.cleanup()

    def test_pending_contract_is_rejected_before_packaging(self):
        self.review["contract"]["review"]["status"] = "PENDING_ROOT_REVIEW"
        self.review_path.write_text(json.dumps(self.review))
        self.entry["review"]["sha256"] = sha(self.review_path.read_bytes())
        self.write_manifest()
        with self.assertRaisesRegex(ValueError, "must already be APPROVED"):
            package_batch_module.package_batch(self.manifest_path, root=self.root)
        self.mock.assert_not_called()

    def test_conflicting_top_level_reviewer_is_rejected(self):
        self.review["reviewer"] = "not-root"
        self.review_path.write_text(json.dumps(self.review))
        self.entry["review"]["sha256"] = sha(self.review_path.read_bytes())
        self.write_manifest()
        with self.assertRaisesRegex(ValueError, "top-level reviewer conflicts"):
            package_batch_module.package_batch(self.manifest_path, root=self.root)
        self.mock.assert_not_called()

    def test_approved_pinned_batch_packages_without_registry_mutation(self):
        registry = self.root / "evidence/behavior/manifest.json"
        registry.parent.mkdir(parents=True, exist_ok=True)
        registry.write_bytes(b"registry immutable")
        before = registry.read_bytes()
        destination = self.root / self.dest
        def package(*args):
            destination.mkdir(parents=True)
            evidence = destination / "evidence.json"
            evidence.write_text("{}")
            return evidence
        self.mock.side_effect = package
        result = package_batch_module.package_batch(self.manifest_path, root=self.root)
        self.assertEqual(result["packaged"][0]["status"], "PACKAGED_UNREGISTERED")
        self.assertFalse(result["registry_mutated"])
        self.assertEqual(registry.read_bytes(), before)
        self.mock.assert_called_once()

    def test_stale_run_pin_fails_before_any_package(self):
        self.run_path.write_text(json.dumps({**self.run, "mismatches": 1}))
        with self.assertRaisesRegex(ValueError, "stale SHA-256"):
            package_batch_module.package_batch(self.manifest_path, root=self.root)
        self.mock.assert_not_called()

    def test_standard_manifest_spelling_preserves_ledger_pin(self):
        manifest_sha = self.identity.pop("manifest_sha256")
        self.identity["historical_manifest_sha256"] = manifest_sha
        self.run_path.write_text(json.dumps(self.run))
        self.entry["run"]["sha256"] = sha(self.run_path.read_bytes())
        self.write_manifest()
        result = package_batch_module.preflight(self.root, self.entry)
        self.assertEqual(result[1], self.run_path)
        self.identity["historical_manifest_sha256"] = "0" * 64
        self.run_path.write_text(json.dumps(self.run))
        self.entry["run"]["sha256"] = sha(self.run_path.read_bytes())
        with self.assertRaisesRegex(ValueError, "identity.manifest_sha256 differs"):
            package_batch_module.preflight(self.root, self.entry)

    def test_split_source_pin_proposal_shape_is_not_guessed(self):
        self.review["source"] = {"path": "src/module.c", "sha256": sha(self.source.read_bytes())}
        self.review_path.write_text(json.dumps(self.review))
        self.entry["review"]["sha256"] = sha(self.review_path.read_bytes())
        self.write_manifest()
        with self.assertRaisesRegex(ValueError, "source and suite as paths"):
            package_batch_module.package_batch(self.manifest_path, root=self.root)
        self.mock.assert_not_called()

    def test_modeled_helper_proposal_is_not_mistaken_for_certification(self):
        self.review["helper_boundaries"] = [{"name": "helper", "execution_mode": "MODELED",
                                             "certification_proposal": {"path": "pending.json", "sha256": "0" * 64}}]
        self.review_path.write_text(json.dumps(self.review))
        self.entry["review"]["sha256"] = sha(self.review_path.read_bytes())
        self.write_manifest()
        with self.assertRaisesRegex(ValueError, "requires an approved certification"):
            package_batch_module.package_batch(self.manifest_path, root=self.root)
        self.mock.assert_not_called()

    def test_reviewed_artifact_hash_is_rechecked_before_packaging(self):
        artifact = self.root / "artifacts/trace.bin"
        artifact.parent.mkdir()
        artifact.write_bytes(b"approved bytes")
        self.review["artifacts"] = [{"path": "artifacts/trace.bin", "name": "trace.bin",
                                     "sha256": sha(artifact.read_bytes())}]
        self.review_path.write_text(json.dumps(self.review))
        self.entry["review"]["sha256"] = sha(self.review_path.read_bytes())
        self.write_manifest()
        artifact.write_bytes(b"changed after review")
        with self.assertRaisesRegex(ValueError, "stale SHA-256"):
            package_batch_module.package_batch(self.manifest_path, root=self.root)
        self.mock.assert_not_called()

    def test_duplicate_target_or_destination_fails_as_batch_preflight(self):
        duplicate = dict(self.entry)
        manifest = {"schema": package_batch_module.SCHEMA,
            "review": {"status": "APPROVED", "reviewer": "root",
                       "reviewed_at": "2026-10-02", "reason": "explicit fixture batch"},
            "entries": [self.entry, duplicate]}
        self.manifest_path.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError, "must be unique"):
            package_batch_module.package_batch(self.manifest_path, root=self.root)
        self.mock.assert_not_called()


if __name__ == "__main__":
    unittest.main()
