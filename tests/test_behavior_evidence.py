"""Adversarial tests for the isolated behavioral evidence registration gate."""
from __future__ import annotations

import copy
import gzip
import hashlib
import json
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import behavior_promote
import behavior_validate
import behavior_ledger


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class EvidenceFixture:
    def __init__(self, *, function="FindIndex", helper_mode=None):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.registry = self.root / "evidence/behavior/manifest.json"
        self.function = function
        for rel in ("assets", "layout", "tools/behavior_suites", "evidence/behavior",
                    "evidence/behavior/runs", "build"):
            (self.root / rel).mkdir(parents=True, exist_ok=True)
        (self.root / "layout/manifest.json").write_text(json.dumps({"schema": "simant-manifest-v1", "modules": {}}))
        (self.root / "assets/SIMANT.EXE").write_bytes(b"oracle fixture executable")
        lock = {"executable": {"sha256": digest(b"oracle fixture executable")}}
        (self.root / "layout/oracle.lock.json").write_text(json.dumps(lock))
        (self.root / "candidate/module.c").parent.mkdir(parents=True, exist_ok=True)
        (self.root / "candidate/module.c").write_text("void module_function(void) {}\n")
        (self.root / "tools/behavior_suites/suite.py").write_text("SUITE = 'fixture-v1'\n")
        (self.root / "tools/behavior.py").write_text("# imported runner snapshot fixture\n")
        for rel in behavior_validate.HARNESS_COMPONENTS:
            path = self.root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f"# pinned fixture: {rel}\n")

        entry = {"status": "UNRESOLVED", "evidence_path": None,
                 "evidence_sha256": None}
        registry = {"schema": "simant-behavior-evidence-manifest-v1",
                    "entries": {function: entry}}
        self.registry.write_text(json.dumps(registry))

        source_sha = digest((self.root / "candidate/module.c").read_bytes())
        suite_sha = digest((self.root / "tools/behavior_suites/suite.py").read_bytes())
        harness_sha = digest((self.root / "tools/behavior.py").read_bytes())
        oracle_sha = digest((self.root / "assets/SIMANT.EXE").read_bytes())
        manifest_sha = digest((self.root / "layout/manifest.json").read_bytes())
        self.function_address = {"unit": "root:fixture", "seg": 1, "off": 2, "size": 3}
        components = {rel: {"path": rel, "sha256": digest((self.root / rel).read_bytes())}
                      for rel in behavior_validate.HARNESS_COMPONENTS}

        mode = helper_mode or "ORIGINAL_EXE"
        helper_name = "modeled_helper" if mode != "ORIGINAL_EXE" else "real_helper"
        self.contract_helper = {"name": helper_name, "must_execute": True}
        helpers = [{"name": helper_name, "execution_mode": mode,
                    "observed_call_count": 1,
                    "executed_from_original": mode == "ORIGINAL_EXE"}]
        self.positive = {"id": "pc-main", "executed": True,
                         "matched": True, "execution_errors": 0,
                         "original_executed": True, "candidate_executed": True,
                         "compared_effects": ["return", "global cursor", "pointed result"],
                         "source_sha256": source_sha, "object_sha256": digest(b"compiled object"),
                         "oracle_sha256": oracle_sha,
                         "original_observation_sha256": digest(b"positive same"),
                         "candidate_observation_sha256": digest(b"positive same")}
        self.negative = {"id": "nc-mutant", "executed": True,
                         "detected_mismatch": True, "execution_errors": 0}
        mutant_source = self.root / "evidence/behavior/runs/mutant.c"
        mutant_source.write_bytes(b"void mutant(void) { return; }\n")
        mutant_object = self.root / "evidence/behavior/runs/mutant.obj"
        mutant_object.write_bytes(b"compiled mutant fixture object")
        self.negative["mutant_source_sha256"] = digest(mutant_source.read_bytes())
        self.negative["mutant_source"] = {"path": "evidence/behavior/runs/mutant.c",
                                           "sha256": digest(mutant_source.read_bytes())}
        self.negative["mutant_object"] = {"path": "evidence/behavior/runs/mutant.obj",
                                           "sha256": digest(mutant_object.read_bytes())}

        self.cert_path = None
        if mode in ("MODELED", "TRACE_ONLY"):
            cert = {"schema": "behavior-helper-cert-v1", "helper": helper_name,
                    "status": "CERTIFIED",
                    "review": {"status": "APPROVED", "reviewer": "reviewer", "reviewed_at": "2026-10-01"},
                    "input_domain": ["bounded one-word inputs"],
                    "compared_effects": ["return value", "state word"],
                    "positive_control_id": "pc-main", "negative_control_id": "nc-mutant",
                    "limitations": "fixture domain only",
                    "source_hashes": {"candidate/module.c": source_sha}}
            self.cert_path = self.root / "evidence/behavior/helper-cert.json"
            self.cert_path.write_text(json.dumps(cert))
            helpers[0]["certification"] = {
                "path": "evidence/behavior/helper-cert.json",
                "sha256": digest(self.cert_path.read_bytes())}

        self.report_path = self.root / "evidence/behavior/runs/run.json"
        self.ledger_path = self.root / "evidence/behavior/runs/cases.jsonl"
        rows = []
        for lane, count, prefix in (("directed", 2, "d"), ("randomized", 2, "r")):
            for i in range(count):
                rows.append({"case_id": f"{prefix}{i}", "lane": lane,
                             "original_executed": True, "candidate_executed": True,
                             "equal": True,
                             "input_sha256": digest(f"input-{prefix}-{i}".encode()),
                             "compared_effects": ["return", "global cursor", "pointed result"],
                             "original_observation_sha256": digest(f"same-{prefix}-{i}".encode()),
                             "candidate_observation_sha256": digest(f"same-{prefix}-{i}".encode()),
                             "function": function, "oracle_sha256": oracle_sha})
        self.ledger_path.write_text("".join(json.dumps(row) + "\n" for row in rows))
        self.report = {
            "schema": "behavior-run-evidence-v1", "completion": "COMPLETE",
            "identity": {"function": function, "suite_id": "fixture-v1",
                         "address": self.function_address,
                         "module": "root:fixture", "source_sha256": source_sha,
                         "suite_sha256": suite_sha, "harness_sha256": harness_sha,
                         "oracle_sha256": oracle_sha,
                         "historical_manifest_sha256": manifest_sha,
                         "object_sha256": digest(b"compiled object"),
                         "compiled_source_sha256": digest(b"compiled source"),
                         "profile": "fixture-profile", "flags": ["/AL", "/Os"]},
            "execution": {"engine": "PreparedPair.compare",
                          "actual_original_execution": True,
                          "actual_candidate_execution": True,
                          "original_exe_sha256": oracle_sha},
            "cases": {
                "directed": {"generated": 2, "executed": 2,
                             "actual_original_invocations": 2,
                             "actual_candidate_invocations": 2, "seeds": []},
                "randomized": {"generated": 2, "executed": 2,
                               "actual_original_invocations": 2,
                               "actual_candidate_invocations": 2, "seeds": [123]},
            },
            "errors": 0, "mismatches": 0,
            "compared_effects": ["return", "global cursor", "pointed result"],
            "case_ledger": {"path": "evidence/behavior/runs/cases.jsonl",
                            "sha256": digest(self.ledger_path.read_bytes()), "row_count": 4,
                            "lane_counts": {"directed": 2, "randomized": 2}, "compression": "none",
                            "identity": {"function": function, "source_sha256": source_sha,
                                "address": self.function_address,
                                "object_sha256": digest(b"compiled object"), "oracle_sha256": oracle_sha,
                                "harness_sha256": harness_sha, "manifest_sha256": manifest_sha}},
            "unmodeled_boundaries": 0, "peer_data_gates": "PASS",
            "positive_controls": [self.positive], "helper_boundaries": helpers,
        }
        self.report_path.write_text(json.dumps(self.report))
        self.negative_path = self.root / "evidence/behavior/runs/negative.json"
        self.negative_path.write_text(json.dumps({
            "schema": "behavior-negative-controls-v1", "function": function,
            "suite_id": "fixture-v1", "identity": {"source_sha256": source_sha,
                "oracle_sha256": oracle_sha, "harness_sha256": harness_sha,
                "historical_manifest_sha256": manifest_sha}, "errors": 0,
            "mismatches_detected": 1, "controls": [{**self.negative,
            "original_executed": True, "mutant_executed": True,
            "baseline_matches": True, "mutant_differs": True,
            "mutant_source_sha256": self.negative["mutant_source_sha256"],
            "mutant_source": self.negative["mutant_source"],
            "mutant_object": self.negative["mutant_object"],
            "mismatch_categories": ["return value"]}]}))
        self.evidence = {
            "schema": "simant-behavior-evidence-v1", "function": function,
            "status": "BEHAVIOR_EXACT",
            "source": {"path": "candidate/module.c", "sha256": source_sha,
                       "whole_module": True, "module": "root:fixture"},
            "suite": {"path": "tools/behavior_suites/suite.py", "sha256": suite_sha,
                      "id": "fixture-v1"},
            "harness": {"runner": {"path": "tools/behavior.py", "sha256": harness_sha},
                        "components": components},
            "oracle": {"path": "assets/SIMANT.EXE", "sha256": oracle_sha,
                       "lock_sha256": digest((self.root / "layout/oracle.lock.json").read_bytes())},
            "historical_manifest_sha256": manifest_sha,
            "checkpoint": {"commit": "a" * 40, "date": "2026-10-01"},
            "contract": {
                "id": "fixture-contract-v1", "input_domain": {"values": "bounded"},
                "limits": ["fixture only"],
                "required_effects": ["return", "global cursor"],
                "excluded_effects": [{"effect": "stack padding", "reason": "outside function contract"}],
                "required_helpers": [self.contract_helper],
                "review": {"status": "APPROVED", "reviewer": "reviewer", "reviewed_at": "2026-10-01"},
            },
            "run_report": {"path": "evidence/behavior/runs/run.json",
                           "sha256": digest(self.report_path.read_bytes())},
            "negative_controls": {"path": "evidence/behavior/runs/negative.json",
                                  "sha256": digest(self.negative_path.read_bytes())},
            "historical_difference": {"description": "fixture codegen difference",
                                       "reason_exact_stopped": "historical experiment disproportionate",
                                       "evidence_refs": ["work/takeover/fixture.md"]},
            "semantic_evidence": ["source review fixture"],
            "evidence_date": "2026-10-01",
        }
        self.evidence_path = self.root / "evidence/behavior/runs/evidence.json"
        self.evidence_path.write_text(json.dumps(self.evidence))
        self.receipt_path = self.root / "build/verified.json"

    def close(self):
        self.temp.cleanup()

    def pin_runtime_graph(self, view):
        inputs = []
        for role, rel, payload in (
            ("producer", "evidence/behavior/runtime/producer.py", b"producer"),
            ("source", "candidate/module.c", (self.root / "candidate/module.c").read_bytes()),
            ("suite", "tools/behavior_suites/suite.py", (self.root / "tools/behavior_suites/suite.py").read_bytes()),
            ("runner", "evidence/behavior/harnesses/fixture/tools/behavior.py", b"runner"),
            ("component", "evidence/behavior/harnesses/fixture/tools/ledger.py", b"component"),
            ("observation", "evidence/behavior/runs/cases.jsonl", self.ledger_path.read_bytes()),
        ):
            path = self.root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)
            inputs.append({"role": role, "path": rel, "sha256": digest(payload)})
        graph = {"schema": "behavior-runtime-proof-graph-v1",
                 "review": {"status": "APPROVED", "reviewer": "root",
                            "reviewed_at": "2026-10-02", "reason": "fixture"},
                 "proof": {"path": view["proof_path"], "sha256": view["proof_sha256"]},
                 "inputs": inputs}
        graph_path = self.root / "evidence/behavior/runtime/fixture-graph.json"
        graph_path.parent.mkdir(parents=True, exist_ok=True)
        graph_path.write_text(json.dumps(graph))
        self.evidence["contract"]["review"]["runtime_proof_graphs"] = [{
            "proof_path": view["proof_path"], "proof_sha256": view["proof_sha256"],
            "graph_path": "evidence/behavior/runtime/fixture-graph.json",
            "graph_sha256": digest(graph_path.read_bytes())}]


class BehaviorEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.fx = EvidenceFixture()
        self.compile_replay = patch.object(behavior_validate, "_compile_candidate", return_value={
            "ok": True, "object_sha256": self.fx.report["identity"]["object_sha256"],
            "compiled_source_sha256": digest(b"compiled source"),
            "profile": "fixture-profile", "flags": ["/AL", "/Os"],
            "address": self.fx.function_address,
            "sequence_targets": [],
            "peer_data_gates": "PASS"})
        self.compile_mock = self.compile_replay.start()
        self.addCleanup(self.compile_replay.stop)

    def tearDown(self):
        self.fx.close()

    def check(self, evidence=None, registry=None):
        return behavior_validate.validate_evidence(
            self.fx.evidence if evidence is None else evidence,
            root=self.fx.root,
            registry_path=self.fx.registry if registry is None else registry,
        )

    def test_complete_pinned_packet_passes_without_registration(self):
        result = self.check()
        self.assertTrue(result["valid"], result["errors"])
        self.assertEqual(result["status"], "BEHAVIOR_EXACT")
        self.assertEqual(json.loads(self.fx.registry.read_text())["entries"][self.fx.function]["status"], "UNRESOLVED")

    def test_sequence_targets_are_replayed_by_fresh_whole_module_compile(self):
        targets = ["FindIndex", "SetupIndex"]
        self.fx.report["identity"]["sequence_targets"] = targets
        self.fx.report["case_ledger"]["identity"]["sequence_targets"] = targets
        self.fx.report_path.write_text(json.dumps(self.fx.report))
        self.fx.evidence["run_report"]["sha256"] = digest(self.fx.report_path.read_bytes())
        self.compile_mock.return_value["sequence_targets"] = targets
        result = self.check()
        self.assertTrue(result["valid"], result["errors"])
        self.assertEqual(self.compile_mock.call_args.args[2], targets)

    def test_sequence_target_set_must_match_fresh_compile(self):
        targets = ["FindIndex", "SetupIndex"]
        self.fx.report["identity"]["sequence_targets"] = targets
        self.fx.report["case_ledger"]["identity"]["sequence_targets"] = targets
        self.fx.report_path.write_text(json.dumps(self.fx.report))
        self.fx.evidence["run_report"]["sha256"] = digest(self.fx.report_path.read_bytes())
        self.compile_mock.return_value["sequence_targets"] = ["FindIndex"]
        result = self.check()
        self.assertFalse(result["valid"])
        self.assertTrue(any("identity.sequence_targets" in error for error in result["errors"]))

    def test_malformed_sequence_target_set_fails_closed(self):
        self.fx.report["identity"]["sequence_targets"] = ["SetupIndex", "FindIndex", "SetupIndex"]
        self.fx.report_path.write_text(json.dumps(self.fx.report))
        self.fx.evidence["run_report"]["sha256"] = digest(self.fx.report_path.read_bytes())
        result = self.check()
        self.assertFalse(result["valid"])
        self.assertTrue(any("sorted unique list" in error for error in result["errors"]))

    def _make_sequence_report(self):
        targets = [self.fx.function, "SetupIndex"]
        self.fx.report["identity"]["sequence_targets"] = targets
        self.fx.report["execution"]["engine"] = "PreparedPair.compare_sequence"
        plan = {"steps": [
            {"index": 0, "entry": "SetupIndex or FindIndex"},
            {"index": 1, "entry": "SetupIndex"},
        ]}
        plan_path = self.fx.root / "evidence/behavior/runs/ordered-plan.json"
        plan_path.write_text(json.dumps(plan))
        self.fx.report["sequence_campaign"] = {
            "ordered_plan_path": "evidence/behavior/runs/ordered-plan.json",
            "ordered_plan_sha256": digest(plan_path.read_bytes()),
        }
        rows = [json.loads(line) for line in self.fx.ledger_path.read_text().splitlines()]
        labels = ["d0/00-FindIndex", "d1/00-FindIndex",
                  "r0/00-FindIndex", "r1/00-FindIndex"]
        for row, label in zip(rows, labels):
            row["case_id"] = label
        self.fx.ledger_path.write_text("".join(json.dumps(row) + "\n" for row in rows))
        ledger_identity = self.fx.report["case_ledger"]["identity"]
        ledger_identity["sequence_targets"] = targets
        self.fx.report["case_ledger"]["sha256"] = digest(self.fx.ledger_path.read_bytes())
        self.fx.report_path.write_text(json.dumps(self.fx.report))
        self.fx.evidence["run_report"]["sha256"] = digest(self.fx.report_path.read_bytes())
        self.compile_mock.return_value["sequence_targets"] = targets

    def test_compare_sequence_requires_and_validates_pinned_ordered_plan(self):
        self._make_sequence_report()
        result = self.check()
        self.assertTrue(result["valid"], result["errors"])

    def test_compare_sequence_rejects_missing_target_or_plan_pin(self):
        self._make_sequence_report()
        self.fx.report["identity"]["sequence_targets"] = ["SetupIndex"]
        self.fx.report["case_ledger"]["identity"]["sequence_targets"] = ["SetupIndex"]
        self.compile_mock.return_value["sequence_targets"] = ["SetupIndex"]
        self.rewrite_report()
        errors = " ".join(self.check()["errors"])
        self.assertIn("containing the evidence target", errors)

        self._make_sequence_report()
        self.fx.report.pop("sequence_campaign")
        self.rewrite_report()
        self.assertIn("requires a sequence_campaign pin", " ".join(self.check()["errors"]))

    def test_compare_sequence_rejects_case_step_outside_pinned_plan(self):
        self._make_sequence_report()
        rows = [json.loads(line) for line in self.fx.ledger_path.read_text().splitlines()]
        rows[0]["case_id"] = "d0/01-FindIndex"
        self.fx.ledger_path.write_text("".join(json.dumps(row) + "\n" for row in rows))
        self.fx.report["case_ledger"]["sha256"] = digest(self.fx.ledger_path.read_bytes())
        self.rewrite_report()
        errors = " ".join(self.check()["errors"])
        self.assertIn("does not match pinned ordered plan", errors)

    def test_compare_sequence_rejects_another_target_label_even_at_valid_step(self):
        self._make_sequence_report()
        rows = [json.loads(line) for line in self.fx.ledger_path.read_text().splitlines()]
        rows[0]["case_id"] = "d0/01-SetupIndex"
        self.fx.ledger_path.write_text("".join(json.dumps(row) + "\n" for row in rows))
        self.fx.report["case_ledger"]["sha256"] = digest(self.fx.ledger_path.read_bytes())
        self.rewrite_report()
        self.assertIn("case_id target does not match run identity", " ".join(self.check()["errors"]))

    def test_stale_source_suite_harness_oracle_and_manifest_fail_closed(self):
        cases = (
            ("source", self.fx.root / "candidate/module.c"),
            ("suite", self.fx.root / "tools/behavior_suites/suite.py"),
            ("harness", self.fx.root / "tools/behavior.py"),
            ("oracle", self.fx.root / "assets/SIMANT.EXE"),
            ("manifest", self.fx.root / "layout/manifest.json"),
        )
        for label, path in cases:
            with self.subTest(label=label):
                original = path.read_bytes()
                path.write_bytes(original + b"changed")
                self.assertFalse(self.check()["valid"])
                path.write_bytes(original)

    def test_retained_runner_snapshot_requires_explicit_review_and_accepts_old_imported_bytes(self):
        runner = self.fx.root / "tools/behavior.py"
        old = runner.read_bytes()
        snapshot = self.fx.root / "evidence/behavior/harnesses/run-001/tools/behavior.py"
        snapshot.parent.mkdir(parents=True, exist_ok=True)
        snapshot.write_bytes(old)
        runner.write_bytes(old + b"post-run hardening change")
        self.fx.evidence["harness"]["runner"] = {
            "path": "evidence/behavior/harnesses/run-001/tools/behavior.py",
            "sha256": digest(old)}
        self.fx.evidence["run_report"]["sha256"] = digest(self.fx.report_path.read_bytes())
        self.assertFalse(self.check()["valid"])
        self.fx.evidence["harness"]["runner_snapshot_review"] = {
            "status": "APPROVED", "reviewer": "root", "reviewed_at": "2026-10-01",
            "reason": "retained bytes match the HARNESS_SOURCE imported for the run",
            "runner_snapshot_reviewed": True, "archived_components": []}
        result = self.check()
        self.assertTrue(result["valid"], result["errors"])

    def test_current_harness_dependency_must_match_or_be_archived(self):
        rel = behavior_validate.HARNESS_COMPONENTS[0]
        path = self.fx.root / rel
        path.write_text("changed after run")
        result = self.check()
        self.assertIn("current file hash is stale", " ".join(result["errors"]))

    def test_report_object_hash_must_match_fresh_whole_module_compile(self):
        self.compile_mock.return_value = {"ok": True, "object_sha256": digest(b"other object"),
            "compiled_source_sha256": digest(b"compiled source"), "profile": "fixture-profile",
            "flags": ["/AL", "/Os"], "peer_data_gates": "PASS"}
        self.assertIn("does not match fresh whole-module compilation", " ".join(self.check()["errors"]))

    def test_report_and_ledger_addresses_must_match_fresh_compiled_target(self):
        wrong_report = dict(self.fx.function_address, off=99)
        self.fx.report["identity"]["address"] = wrong_report
        self.rewrite_report()
        self.assertIn("run report identity.address does not match the fresh compiled function target",
                      " ".join(self.check()["errors"]))

        self.fx.report["identity"]["address"] = self.fx.function_address
        self.fx.report["case_ledger"]["identity"]["address"] = dict(self.fx.function_address, unit="other:target")
        self.rewrite_report()
        self.assertIn("case ledger identity.address does not match the fresh compiled function target",
                      " ".join(self.check()["errors"]))

    def test_formatter_view_requires_root_reviewed_runtime_proof_and_scoped_raw_differences(self):
        proof_path = self.fx.root / "evidence/behavior/runtime/format-cursor-fixture.json"
        proof_path.parent.mkdir(parents=True)
        proof = {
            "schema": "behavior-format-cursor-proof-v1",
            "oracle_sha256": self.fx.evidence["oracle"]["sha256"],
            "review": {"status": "APPROVED", "reviewer": "root", "reviewed_at": "2026-10-02"},
            "records": [{"name": "format_stream", "address": 0x1200, "size": 10,
                         "private_owner": "sprintf.c", "overwrite_before_read_proven": True}],
        }
        proof_path.write_text(json.dumps(proof))
        view = {"name": "format_stream", "address": 0x1200,
                "proof_path": "evidence/behavior/runtime/format-cursor-fixture.json",
                "proof_sha256": digest(proof_path.read_bytes())}

        rows = [json.loads(x) for x in self.fx.ledger_path.read_text().splitlines()]
        rows[0].update({
            "implementation_view_proofs": [view],
            "raw_original_observation_sha256": digest(b"raw original"),
            "raw_candidate_observation_sha256": digest(b"raw candidate"),
            "implementation_differences": {"raw_nonstack_memory": [
                {"address": 0x1205, "oracle": 0, "candidate": 1}]},
            "private_formatter_views": {"format_stream": {
                "cursor_advance": 5, "remaining_capacity": 20,
                "buffer_lifetime": "private formatter invocation"}},
        })
        self.fx.ledger_path.write_text("".join(json.dumps(row) + "\n" for row in rows))
        self.fx.report["case_ledger"]["sha256"] = digest(self.fx.ledger_path.read_bytes())
        self.fx.report["identity"].pop("implementation_views", None)
        self.fx.report["implementation_views"] = [view]
        self.fx.evidence["contract"]["implementation_views"] = [view]
        self.fx.evidence["contract"]["review"] = {
            "status": "APPROVED", "reviewer": "root", "reviewed_at": "2026-10-02"}
        self.fx.pin_runtime_graph(view)
        self.rewrite_report()
        result = self.check()
        self.assertTrue(result["valid"], result["errors"])

        graph_path = self.fx.root / self.fx.evidence["contract"]["review"]["runtime_proof_graphs"][0]["graph_path"]
        graph_bytes = graph_path.read_bytes()
        graph_path.write_bytes(graph_bytes + b"tampered")
        self.assertIn("graph SHA-256 is stale", " ".join(self.check()["errors"]))
        graph_path.write_bytes(graph_bytes)

        rows[0]["implementation_differences"]["raw_nonstack_memory"][0]["address"] = 0x120A
        self.fx.ledger_path.write_text("".join(json.dumps(row) + "\n" for row in rows))
        self.fx.report["case_ledger"]["sha256"] = digest(self.fx.ledger_path.read_bytes())
        self.rewrite_report()
        self.assertIn("raw memory difference lies outside approved implementation views",
                      " ".join(self.check()["errors"]))

    def test_pinned_formatter_audit_is_recursively_hash_and_record_checked(self):
        audit_path = self.fx.root / "evidence/behavior/runtime/format-cursor-audit.json"
        audit_path.parent.mkdir(parents=True)
        owner = "llibcr.lib:sprintf.c:_BSS:DGROUP:8e06"
        audit_record = {"name": "format_stream", "address": 0x1200,
                        "size": 10, "private_owner": owner,
                        "overwrite_before_read_proven": True}
        audit = {"schema": "runtime-format-cursor-audit-v1",
                 "all_negative_controls_passed": True,
                 "runtime_member": {"sha256": digest(b"sprintf member")},
                 "vsprintf_runtime_member": {"sha256": digest(b"vsprintf member")},
                 "dynamic_proof": {"negative_control_passed": True},
                 "vsprintf_dynamic_proof": {"negative_control_passed": True},
                 "retained_raw_mismatch": {"raw_nonstack_memory_differences": [
                     {"address": "0x1200", "oracle": 0, "candidate": 1}]},
                 "typed_view_proposal": {"schema": "behavior-format-cursor-proof-v1",
                     "oracle_sha256": self.fx.evidence["oracle"]["sha256"],
                     "records": [audit_record]}}
        material = {"oracle_sha256": self.fx.evidence["oracle"]["sha256"],
            "runtime_members": [audit["runtime_member"], audit["vsprintf_runtime_member"]],
            "records": [audit_record], "sprintf_negative_control": True,
            "vsprintf_negative_control": True,
            "raw_diffs_preserved": audit["retained_raw_mismatch"]["raw_nonstack_memory_differences"]}
        audit["typed_view_proposal"]["proof_digest"] = digest(json.dumps(
            material, sort_keys=True, separators=(",", ":")).encode())
        audit_path.write_text(json.dumps(audit))
        proof = {"schema": "behavior-format-cursor-proof-v1",
                 "oracle_sha256": self.fx.evidence["oracle"]["sha256"],
                 "audit": {"path": "evidence/behavior/runtime/format-cursor-audit.json",
                           "sha256": digest(audit_path.read_bytes())},
                 "records": [{"name": "format_stream", "address": 0x1200,
                     "size": 10, "private_owner": "sprintf.c",
                     "overwrite_before_read_proven": True}]}
        errors = []
        behavior_validate._validate_cursor_audit(self.fx.root, proof, "format_stream",
            0x1200, self.fx.evidence["oracle"]["sha256"], "fixture view", errors)
        self.assertEqual(errors, [])

        audit["all_negative_controls_passed"] = False
        audit_path.write_text(json.dumps(audit))
        errors = []
        behavior_validate._validate_cursor_audit(self.fx.root, proof, "format_stream",
            0x1200, self.fx.evidence["oracle"]["sha256"], "fixture view", errors)
        self.assertTrue(any("audit SHA-256 is stale" in error for error in errors))

    def test_unreviewed_or_undeclared_formatter_normalization_is_rejected(self):
        proof_path = self.fx.root / "evidence/behavior/runtime/format-cursor-fixture.json"
        proof_path.parent.mkdir(parents=True)
        proof = {
            "schema": "behavior-format-cursor-proof-v1",
            "oracle_sha256": self.fx.evidence["oracle"]["sha256"],
            "review": {"status": "APPROVED", "reviewer": "root", "reviewed_at": "2026-10-02"},
            "records": [{"name": "format_stream", "address": 0x1200, "size": 10,
                         "private_owner": "vsprintf.c", "overwrite_before_read_proven": True}],
        }
        proof_path.write_text(json.dumps(proof))
        view = {"name": "format_stream", "address": 0x1200,
                "proof_path": "evidence/behavior/runtime/format-cursor-fixture.json",
                "proof_sha256": digest(proof_path.read_bytes())}
        rows = [json.loads(x) for x in self.fx.ledger_path.read_text().splitlines()]
        rows[0].update({"implementation_view_proofs": [view],
            "raw_original_observation_sha256": digest(b"raw original"),
            "raw_candidate_observation_sha256": digest(b"raw candidate"),
            "implementation_differences": {},
            "private_formatter_views": {}})
        self.fx.ledger_path.write_text("".join(json.dumps(row) + "\n" for row in rows))
        self.fx.report["case_ledger"]["sha256"] = digest(self.fx.ledger_path.read_bytes())
        self.fx.report["implementation_views"] = [view]
        self.fx.evidence["contract"]["implementation_views"] = [view]
        self.fx.evidence["contract"]["review"] = {
            "status": "APPROVED", "reviewer": "root", "reviewed_at": "2026-10-02"}

        proof["review"]["reviewer"] = "someone-else"
        proof_path.write_text(json.dumps(proof))
        new_view = dict(view, proof_sha256=digest(proof_path.read_bytes()))
        self.fx.report["implementation_views"] = [new_view]
        self.fx.evidence["contract"]["implementation_views"] = [new_view]
        rows[0]["implementation_view_proofs"] = [new_view]
        self.fx.ledger_path.write_text("".join(json.dumps(row) + "\n" for row in rows))
        self.fx.report["case_ledger"]["sha256"] = digest(self.fx.ledger_path.read_bytes())
        self.rewrite_report()
        self.assertIn("runtime proof lacks explicit root review", " ".join(self.check()["errors"]))

        self.fx.report["implementation_views"] = []
        self.fx.evidence["contract"]["implementation_views"] = []
        self.rewrite_report()
        errors = " ".join(self.check()["errors"])
        self.assertTrue("implementation view is undeclared" in errors
                        or "implementation_views must exactly match" in errors)

    def test_no_actual_original_execution_rejected(self):
        self.fx.report["execution"]["actual_original_execution"] = False
        self.rewrite_report()
        self.assertIn("run report must attest actual original DOS and candidate execution", " ".join(self.check()["errors"]))

    def test_incomplete_cases_errors_mismatch_and_missing_effects_rejected(self):
        self.fx.report["cases"]["randomized"]["executed"] = 1
        self.fx.report["errors"] = 1
        self.fx.report["mismatches"] = 1
        self.fx.report["compared_effects"] = ["return"]
        self.rewrite_report()
        errors = " ".join(self.check()["errors"])
        for phrase in ("incomplete run", "zero execution errors", "zero mismatches", "does not compare every"):
            self.assertIn(phrase, errors)

    def test_negative_control_missing_or_not_detected_rejected(self):
        self.fx.negative_path.write_text(json.dumps({"schema": "behavior-negative-controls-v1",
            "function": self.fx.function, "suite_id": "fixture-v1",
            "identity": {"source_sha256": "a" * 64, "oracle_sha256": "b" * 64,
                         "harness_sha256": "c" * 64, "historical_manifest_sha256": "d" * 64},
            "errors": 0, "mismatches_detected": 0, "controls": [{"id": "nc-mutant",
            "executed": True, "detected_mismatch": False, "execution_errors": 0}]}))
        self.repin_negative()
        self.assertFalse(self.check()["valid"])

    def test_negative_control_identity_must_match_pinned_source_and_oracle(self):
        report = json.loads(self.fx.negative_path.read_text())
        report["identity"]["oracle_sha256"] = digest(b"different oracle")
        self.fx.negative_path.write_text(json.dumps(report))
        self.repin_negative()
        self.assertIn("identity.oracle_sha256 does not match evidence pins",
                      " ".join(self.check()["errors"]))

    def test_exact_historical_function_cannot_enter_behavior_registry(self):
        journal = self.fx.root / "evidence/promotions.jsonl"
        journal.write_text(json.dumps({"new_claims": [self.fx.function]}) + "\n")
        result = self.check()
        self.assertFalse(result["valid"])
        self.assertIn("historical EXACT promotion exists", " ".join(result["errors"]))

    def test_modeled_simulation_helper_without_certification_is_rejected(self):
        fx = EvidenceFixture(function="SpiderScan", helper_mode="MODELED")
        try:
            fx.report["helper_boundaries"][0].pop("certification")
            fx.rewrite_report = lambda: None
            fx.report_path.write_text(json.dumps(fx.report))
            fx.evidence["run_report"]["sha256"] = digest(fx.report_path.read_bytes())
            result = behavior_validate.validate_evidence(fx.evidence, root=fx.root,
                                                          registry_path=fx.registry)
            self.assertFalse(result["valid"])
            self.assertIn("modeled/trace boundary is uncertified", " ".join(result["errors"]))
        finally:
            fx.close()

    def test_modeled_simulation_helper_requires_review_and_positive_negative_controls(self):
        fx = EvidenceFixture(function="SpiderScan", helper_mode="MODELED")
        try:
            cert = json.loads(fx.cert_path.read_text())
            cert["review"]["status"] = "PENDING"
            cert["positive_control_id"] = "missing"
            fx.cert_path.write_text(json.dumps(cert))
            fx.evidence["run_report"]["sha256"] = digest(fx.report_path.read_bytes())
            fx.evidence["run_report"]["sha256"] = digest(fx.report_path.read_bytes())
            fx.report_path.write_text(json.dumps(fx.report))
            # Re-pin the certification and evidence run report after the mutation.
            fx.evidence["run_report"]["sha256"] = digest(fx.report_path.read_bytes())
            fx.report["helper_boundaries"][0]["certification"]["sha256"] = digest(fx.cert_path.read_bytes())
            fx.report_path.write_text(json.dumps(fx.report))
            fx.evidence["run_report"]["sha256"] = digest(fx.report_path.read_bytes())
            result = behavior_validate.validate_evidence(fx.evidence, root=fx.root,
                                                          registry_path=fx.registry)
            errors = " ".join(result["errors"])
            self.assertIn("lacks independent review", errors)
            self.assertIn("positive control is not in the run report", errors)
        finally:
            fx.close()

    def test_missing_contract_effect_and_excluded_effect_reason_rejected(self):
        evidence = copy.deepcopy(self.fx.evidence)
        evidence["contract"]["excluded_effects"] = [{"effect": "DOS address"}]
        evidence["contract"]["required_effects"] = []
        result = self.check(evidence)
        errors = " ".join(result["errors"])
        self.assertIn("required_effects", errors)
        self.assertIn("excluded_effects", errors)

    def test_stale_report_hash_rejected(self):
        self.fx.report_path.write_text(self.fx.report_path.read_text() + " ")
        self.assertIn("stale SHA-256", " ".join(self.check()["errors"]))

    def test_case_ledger_detects_omitted_original_runs_and_missing_effects(self):
        rows = [json.loads(x) for x in self.fx.ledger_path.read_text().splitlines()]
        rows[0]["original_executed"] = False
        rows[1]["compared_effects"] = ["return"]
        self.fx.ledger_path.write_text("".join(json.dumps(row) + "\n" for row in rows))
        self.fx.report["case_ledger"]["sha256"] = digest(self.fx.ledger_path.read_bytes())
        self.rewrite_report()
        errors = " ".join(self.check()["errors"])
        self.assertIn("both original and candidate must execute", errors)
        self.assertIn("required effects were not compared", errors)

    def test_equal_case_with_different_normalized_observations_is_rejected(self):
        rows = [json.loads(x) for x in self.fx.ledger_path.read_text().splitlines()]
        rows[0]["candidate_observation_sha256"] = digest(b"different observation")
        self.fx.ledger_path.write_text("".join(json.dumps(row) + "\n" for row in rows))
        self.fx.report["case_ledger"]["sha256"] = digest(self.fx.ledger_path.read_bytes())
        self.rewrite_report()
        self.assertIn("equal case has different normalized observation hashes", " ".join(self.check()["errors"]))

    def test_case_ledger_rejects_wrong_function_and_oracle_identity(self):
        rows = [json.loads(x) for x in self.fx.ledger_path.read_text().splitlines()]
        rows[0]["oracle_sha256"] = digest(b"other oracle")
        self.fx.ledger_path.write_text("".join(json.dumps(row) + "\n" for row in rows))
        self.fx.report["case_ledger"]["sha256"] = digest(self.fx.ledger_path.read_bytes())
        self.rewrite_report()
        self.assertIn("oracle does not match run identity", " ".join(self.check()["errors"]))

    def test_case_ledger_gzip_is_supported(self):
        import gzip
        compressed = self.fx.root / "evidence/behavior/runs/cases.jsonl.gz"
        with compressed.open("wb") as raw:
            with gzip.GzipFile(fileobj=raw, mode="wb", filename="", mtime=0) as zipped:
                zipped.write(self.fx.ledger_path.read_text().encode())
        self.fx.report["case_ledger"].update({"path": "evidence/behavior/runs/cases.jsonl.gz",
            "sha256": digest(compressed.read_bytes()), "compression": "gzip"})
        self.rewrite_report()
        self.assertTrue(self.check()["valid"], self.check()["errors"])

    def test_case_ledger_report_hashes_contract_observations_and_inputs(self):
        class Machine:
            def __init__(self, memory): self.memory = memory
            def read(self, address, size): return bytes(self.memory.get(address + i, 0) for i in range(size))
            def semantic_effects(self, addresses):
                return ([(at, self.read(at, 1)[0]) for at in sorted(set(addresses))], {})
        pair = SimpleNamespace(
            identity={"function": "FindIndex", "source_sha256": "a" * 64,
                      "object_sha256": "b" * 64, "oracle_sha256": "c" * 64,
                      "harness_sha256": "d" * 64, "manifest_sha256": "e" * 64},
            original_machine=Machine({0x200: 7}), candidate_machine=Machine({0x200: 7}))
        base = {"return": 3, "ranges": [], "trace": [], "io": [], "state": {},
                "preserved_registers": {}, "written_addresses": [0x200]}
        comparison = SimpleNamespace(equal=True, original=dict(base), candidate=dict(base), diff={})
        case = SimpleNamespace(label="case-1", args=[], writes=[(0x200, b"\x07")], observe=[],
            callbacks={}, return_kind="word", registers={}, state={}, metadata={}, io_reads={},
            max_instructions=100, max_blocks=20, observe_at_calls=[], callee_pop=None,
            stack_bytes=0xF00, format_cursor_views=[])
        with tempfile.TemporaryDirectory() as td:
            ledger = behavior_ledger.CaseLedger(Path(td) / "cases.jsonl.gz", pair, ["return", "memory"])
            row = ledger.record(case, comparison, lane="directed")
            report = ledger.finalize()
            self.assertTrue(row["equal"])
            self.assertEqual(row["original_observation_sha256"], row["candidate_observation_sha256"])
            self.assertEqual(report["row_count"], 1)
            self.assertEqual(report["lane_counts"], {"directed": 1, "randomized": 0})
            with gzip.open(Path(td) / "cases.jsonl.gz", "rt", encoding="utf-8") as stream:
                saved = json.loads(stream.readline())
            self.assertEqual(saved, row)

    def test_verify_receipt_then_explicit_registration_only(self):
        result = behavior_validate.validate_evidence(self.fx.evidence, root=self.fx.root,
                                                      registry_path=self.fx.registry)
        self.assertTrue(result["valid"], result["errors"])
        receipt = behavior_validate.validation_receipt(result,
            evidence_path=self.fx.evidence_path, registry_path=self.fx.registry, root=self.fx.root)
        self.fx.receipt_path.write_text(json.dumps(receipt))
        failed = behavior_promote.register(self.fx.evidence_path, self.fx.receipt_path,
            reviewed_by="", review_note="", registry_path=self.fx.registry, root=self.fx.root)
        self.assertFalse(failed["registered"])
        self.assertEqual(json.loads(self.fx.registry.read_text())["entries"][self.fx.function]["status"], "UNRESOLVED")
        ok = behavior_promote.register(self.fx.evidence_path, self.fx.receipt_path,
            reviewed_by="root-reviewer", review_note="reviewed fixture proof", registry_path=self.fx.registry, root=self.fx.root)
        self.assertTrue(ok["registered"], ok.get("errors"))
        self.assertEqual(json.loads(self.fx.registry.read_text())["entries"][self.fx.function]["status"], "BEHAVIOR_EXACT")

    def test_registry_change_after_verify_requires_new_receipt(self):
        result = behavior_validate.validate_evidence(self.fx.evidence, root=self.fx.root,
                                                      registry_path=self.fx.registry)
        receipt = behavior_validate.validation_receipt(result,
            evidence_path=self.fx.evidence_path, registry_path=self.fx.registry, root=self.fx.root)
        self.fx.receipt_path.write_text(json.dumps(receipt))
        self.fx.registry.write_text(self.fx.registry.read_text() + " ")
        result = behavior_promote.register(self.fx.evidence_path, self.fx.receipt_path,
            reviewed_by="reviewer", review_note="checked", registry_path=self.fx.registry, root=self.fx.root)
        self.assertFalse(result["registered"])
        self.assertIn("registry changed", " ".join(result["errors"]))

    def test_revision_is_append_only_reviewed_and_receipt_bound(self):
        initial = behavior_validate.validate_evidence(self.fx.evidence, root=self.fx.root,
            registry_path=self.fx.registry)
        initial_receipt = behavior_validate.validation_receipt(initial,
            evidence_path=self.fx.evidence_path, registry_path=self.fx.registry, root=self.fx.root)
        self.fx.receipt_path.write_text(json.dumps(initial_receipt))
        registered = behavior_promote.register(self.fx.evidence_path, self.fx.receipt_path,
            reviewed_by="root-reviewer", review_note="initial fixture proof",
            registry_path=self.fx.registry, root=self.fx.root)
        self.assertTrue(registered["registered"], registered.get("errors"))
        prior_bytes = self.fx.evidence_path.read_bytes()
        prior_hash = digest(prior_bytes)

        packet = copy.deepcopy(self.fx.evidence)
        packet["revision"] = {
            "previous_evidence": {"path": "evidence/behavior/runs/evidence.json",
                                  "sha256": prior_hash},
            "review": {"status": "APPROVED", "reviewer": "root",
                       "reviewed_at": "2026-10-02", "reason": "stack-window ledger correction"},
        }
        revision_path = self.fx.root / "evidence/behavior/runs/evidence-revision-1.json"
        revision_path.write_text(json.dumps(packet))
        receipt_path = self.fx.root / "build/revision-1.json"
        missing_receipt = behavior_promote.revise(revision_path, receipt_path,
            reviewed_by="root", review_reason="stack-window ledger correction",
            registry_path=self.fx.registry, root=self.fx.root)
        self.assertFalse(missing_receipt["registered"])
        self.assertIn("receipt", " ".join(missing_receipt["errors"]))

        checked = behavior_promote.verify_revision(revision_path, receipt_path,
            registry_path=self.fx.registry, root=self.fx.root)
        self.assertTrue(checked["valid"], checked.get("errors"))
        revised = behavior_promote.revise(revision_path, receipt_path,
            reviewed_by="root", review_reason="stack-window ledger correction",
            registry_path=self.fx.registry, root=self.fx.root)
        self.assertTrue(revised["registered"], revised.get("errors"))
        self.assertEqual(self.fx.evidence_path.read_bytes(), prior_bytes)
        registry = json.loads(self.fx.registry.read_text())
        row = registry["entries"][self.fx.function]
        self.assertEqual(row["initial_evidence_sha256"], prior_hash)
        self.assertEqual(row["evidence_path"], "evidence/behavior/runs/evidence-revision-1.json")
        self.assertEqual(row["evidence_sha256"], digest(revision_path.read_bytes()))
        self.assertEqual(len(row["revisions"]), 1)
        self.assertEqual(row["revisions"][0]["from_sha256"], prior_hash)
        self.assertEqual(row["revisions"][0]["to_sha256"], row["evidence_sha256"])
        self.assertEqual(behavior_validate._validate_revision_history(self.fx.root, row), [])
        self.fx.evidence_path.write_bytes(prior_bytes + b"tamper")
        self.assertIn("predecessor packet hash is stale",
            " ".join(behavior_validate._validate_revision_history(self.fx.root, row)))
        self.fx.evidence_path.write_bytes(prior_bytes)
        latest = behavior_validate.validate_evidence(packet, root=self.fx.root,
            registry_path=self.fx.registry, allow_registered=True, evidence_path=revision_path)
        self.assertTrue(latest["valid"], latest.get("errors"))

    def test_revision_cannot_reuse_prior_packet_path_or_revise_exact(self):
        initial = behavior_validate.validate_evidence(self.fx.evidence, root=self.fx.root,
            registry_path=self.fx.registry)
        self.fx.receipt_path.write_text(json.dumps(behavior_validate.validation_receipt(initial,
            evidence_path=self.fx.evidence_path, registry_path=self.fx.registry, root=self.fx.root)))
        self.assertTrue(behavior_promote.register(self.fx.evidence_path, self.fx.receipt_path,
            reviewed_by="root-reviewer", review_note="initial fixture proof",
            registry_path=self.fx.registry, root=self.fx.root)["registered"])
        packet = copy.deepcopy(self.fx.evidence)
        packet["revision"] = {
            "previous_evidence": {"path": "evidence/behavior/runs/evidence.json",
                                  "sha256": digest(self.fx.evidence_path.read_bytes())},
            "review": {"status": "APPROVED", "reviewer": "root",
                       "reviewed_at": "2026-10-02", "reason": "correction"},
        }
        reused = behavior_validate.validate_evidence(packet, root=self.fx.root,
            registry_path=self.fx.registry, allow_revision=True, evidence_path=self.fx.evidence_path)
        self.assertIn("packet path must be new", " ".join(reused["errors"]))
        registry = json.loads(self.fx.registry.read_text())
        registry["entries"][self.fx.function]["status"] = "EXACT"
        self.fx.registry.write_text(json.dumps(registry))
        new_path = self.fx.root / "evidence/behavior/runs/evidence-new.json"
        new_path.write_text(json.dumps(packet))
        exact = behavior_validate.validate_evidence(packet, root=self.fx.root,
            registry_path=self.fx.registry, allow_revision=True, evidence_path=new_path)
        self.assertFalse(exact["valid"])
        self.assertIn("exact claims are immutable", " ".join(exact["errors"]))

    def test_revision_source_change_requires_explicit_root_review(self):
        initial = behavior_validate.validate_evidence(self.fx.evidence, root=self.fx.root,
            registry_path=self.fx.registry)
        self.fx.receipt_path.write_text(json.dumps(behavior_validate.validation_receipt(initial,
            evidence_path=self.fx.evidence_path, registry_path=self.fx.registry, root=self.fx.root)))
        self.assertTrue(behavior_promote.register(self.fx.evidence_path, self.fx.receipt_path,
            reviewed_by="root-reviewer", review_note="initial fixture proof",
            registry_path=self.fx.registry, root=self.fx.root)["registered"])
        packet = copy.deepcopy(self.fx.evidence)
        changed_source = b"void module_function(void) { return; }\n"
        source_path = self.fx.root / "candidate/module.c"
        source_path.write_bytes(changed_source)
        source_hash = digest(changed_source)
        packet["source"]["sha256"] = source_hash
        packet["revision"] = {
            "previous_evidence": {"path": "evidence/behavior/runs/evidence.json",
                                  "sha256": digest(self.fx.evidence_path.read_bytes())},
            "review": {"status": "APPROVED", "reviewer": "root",
                       "reviewed_at": "2026-10-02", "reason": "source correction"},
        }
        revision_path = self.fx.root / "evidence/behavior/runs/evidence-revision-source.json"
        revision_path.write_text(json.dumps(packet))
        result = behavior_validate.validate_evidence(packet, root=self.fx.root,
            registry_path=self.fx.registry, allow_revision=True, evidence_path=revision_path)
        self.assertIn("requires explicit root review of that source change", " ".join(result["errors"]))

    def rewrite_report(self):
        self.fx.report_path.write_text(json.dumps(self.fx.report))
        self.fx.evidence["run_report"]["sha256"] = digest(self.fx.report_path.read_bytes())

    def repin_negative(self):
        self.fx.evidence["negative_controls"]["sha256"] = digest(self.fx.negative_path.read_bytes())


if __name__ == "__main__":
    unittest.main()
