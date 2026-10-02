from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "portable/tools/verify_evidence.py"
SPEC = importlib.util.spec_from_file_location("verify_evidence_under_test", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
verify = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(verify)


class VerifyEvidenceTests(unittest.TestCase):
    def test_compiled_object_digest_is_not_a_source_identity(self) -> None:
        with tempfile.TemporaryDirectory(prefix="verify-evidence-objects-") as temp:
            source = Path(temp) / "model.c"
            source.write_bytes(b"int model(void) { return 1; }\n")
            source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
            object_hash = hashlib.sha256(b"compiled COFF artifact").hexdigest()

            checks: list[dict] = []
            missing: list[str] = []
            verify.check_path_map(checks, missing,
                                  {"source_inputs": {str(source): source_hash}},
                                  "source_inputs")
            self.assertFalse(missing)
            self.assertEqual(checks[0]["result"], "MATCH")

            artifact, issues = verify.validate_opaque_artifact_map(
                {"objects": {str(source): object_hash}}, "objects", expected_entries=1)
            self.assertFalse(issues)
            self.assertEqual(artifact["entries"], 1)

            wrong_checks: list[dict] = []
            wrong_missing: list[str] = []
            verify.check_path_map(wrong_checks, wrong_missing,
                                  {"mistaken_source_inputs": {str(source): object_hash}},
                                  "mistaken_source_inputs")
            self.assertEqual(wrong_checks[0]["result"], "MISMATCH")

    def test_path_hash_row_verifier_checks_explicit_source_inputs(self) -> None:
        with tempfile.TemporaryDirectory(prefix="verify-evidence-input-rows-") as temp:
            source = Path(temp) / "input.c"
            source.write_bytes(b"int input(void) { return 2; }\n")
            digest = hashlib.sha256(source.read_bytes()).hexdigest()
            checks: list[dict] = []
            missing: list[str] = []
            verify.check_path_hash_rows(
                checks, missing,
                {"inputs": [{"path": str(source), "sha256": digest}]},
                "fixture.json",
                {"field": "inputs", "path_field": "path", "hash_field": "sha256"})
            self.assertFalse(missing)
            self.assertEqual(checks[0]["result"], "MATCH")

    def test_original_save_write_callbacks_are_not_counted_as_calls(self) -> None:
        report = {"save": {"function": "o09_35F5_0188", "write_calls": 307}}
        count, basis = verify.dos_comparison_count(
            {"dos_count": {"single_function_invocation": {
                "field": "save", "function": "o09_35F5_0188", "positive_field": "write_calls"}}},
            report)
        self.assertEqual(count, 1)
        self.assertIn("307 nested callbacks", basis)

        malformed = {"save": {"function": "o09_35F5_0188", "write_calls": 0}}
        count, _ = verify.dos_comparison_count(
            {"dos_count": {"single_function_invocation": {
                "field": "save", "function": "o09_35F5_0188", "positive_field": "write_calls"}}},
            malformed)
        self.assertIsNone(count)

    def test_top_level_save_function_and_nested_callback_count_are_separate(self) -> None:
        report = {"function": "o09_35F5_0188", "write_calls": 307}
        count, basis = verify.dos_comparison_count(
            {"dos_count": {"single_function_invocation": {
                "function_field": "function", "function": "o09_35F5_0188",
                "positive_field": "write_calls"}}},
            report)
        self.assertEqual(count, 1)
        self.assertIn("307 nested callbacks", basis)

        wrong_entry = {"function": "o09_35F5_0001", "write_calls": 307}
        count, _ = verify.dos_comparison_count(
            {"dos_count": {"single_function_invocation": {
                "function_field": "function", "function": "o09_35F5_0188",
                "positive_field": "write_calls"}}},
            wrong_entry)
        self.assertIsNone(count)

    def test_registrations_keep_artifact_and_archived_receipts_separate(self) -> None:
        by_id = {spec["id"]: spec for spec in verify.REPORTS}
        gate = by_id["native_gate_49_next9_state_only_20261002"]
        self.assertIn("inputs", gate["path_hash_maps"])
        self.assertNotIn("common_objects", gate["path_hash_maps"])
        self.assertEqual(gate["opaque_artifact_maps"][0]["field"], "common_objects")
        self.assertEqual(gate["opaque_artifact_maps"][0]["expected_entries"], 61)
        self.assertTrue(by_id["physical_menu_fast_description_prior_archived_20261002"]["archived"])
        self.assertTrue(by_id["native_gate_49_menu_controls_final_superseded_archived_20261002"]["archived"])
        self.assertEqual(by_id["next8_event_width_source_recipe_20261002"]["dos_count"],
                         {"sum": ["suite.directed_count"]})
        self.assertEqual(by_id["procmenu_next7_dos_native_84_complete_closure_20261002"]["dos_count"],
                         "case_count")
        self.assertEqual(by_id["engine_procmenu_next7_21_selected_closure_20261002"]["scope_only"], True)
        paired = by_id["paired_control_events_34_dos_native_20261002"]
        self.assertEqual(paired["dos_count"], "case_count")
        self.assertIn("transitive_source_pins_before", paired["path_hash_maps"])
        self.assertEqual(set(paired["native_tus"]), {
            "portable/tests/setup/control_events/native_adapter.c",
            "portable/ui_model/windows/control_events.c",
            "portable/game/simulation/setup.c",
        })
        group = by_id["group_visible_5380_dos_native_20261002"]
        self.assertEqual(group["dos_count"], "case_count")
        save_v3 = by_id["next9_v3_save_source_sentinels_1dos_20261002"]
        self.assertEqual(save_v3["hash_fields"].count(("harness_sha256", "tools/behavior.py")), 1)
        self.assertEqual(save_v3["dos_count"]["single_function_invocation"]["function_field"], "function")
        self.assertIn("requires_missing", save_v3)
        self.assertFalse(any("executable_sha256" in str(item) for item in save_v3.get("hash_fields", [])))
        preselect = by_id["control_preselect_type1_all_flags_20261002"]
        self.assertEqual(preselect["dos_count"], "case_count")
        self.assertIn("toolchain.native_dependency_closure", preselect["path_hash_maps"])
        self.assertEqual(preselect["metrics"][1]["field"], "unsupported_type_checks")
        engine = by_id["engine_procmenu_next7_control_model_21_20261002"]
        self.assertTrue(engine["skip_dependency_closure"])
        self.assertEqual(engine["partitioned_path_hash_maps"][0]["artifact_suffixes"], [".o"])
        self.assertIn("compiler_dependency_method", [field for field, _ in engine["assert_fields"]])
        self.assertTrue(by_id["historical_integrity_controls_frozen_20261002"]["scope_only"])
        control_engine = by_id["control_engine_next9_175047_archived_20261002"]
        self.assertTrue(control_engine["archived"])
        self.assertTrue(control_engine["report"].endswith("control-engine-next9-20261002T175047Z.json"))
        refreshed = by_id["control_engine_next9_181619_15_boundaries_20261002"]
        self.assertEqual(refreshed["assert_fields"][1], ("compile.local_transitive_dependency_count", 115))
        self.assertEqual(refreshed["assert_fields"][2], ("counts.engine_boundary_cases", 15))
        self.assertTrue(by_id["native_gate_50_mouse_controls_20261002"]["scope_only"])
        self.assertEqual(by_id["engine_procmenu_next7_mouse_control_21_20261002"]["assert_fields"][1],
                         ("profile", "NEXT7 generated recovered source"))
        self.assertTrue(by_id["frozen_hybrid_reuse_provenance_identity_20261002"]["scope_only"])
        self.assertEqual(by_id["frozen_hybrid_reuse_provenance_identity_20261002"]["compare_json_documents"][0]["ignore_fields"], ["timing"])
        hotbox = by_id["mouse_hotbox_original_asm_native_222_20261002"]
        self.assertEqual(hotbox["dos_count"], "domain.count")
        self.assertEqual(hotbox["assert_fields"][2], ("result.status", "PASS"))
        save_v5 = by_id["next9_v5_save_stream_sentinels_1dos_20261002"]
        self.assertEqual(save_v5["dos_count"]["single_function_invocation"]["function"], "o09_35F5_0188")
        self.assertEqual(save_v5["related_documents"][1]["path_hash_maps"][-1], "gcc_mm_local_dependency_union")
        self.assertIn("not production", save_v5["scope"].lower())
        save_v4 = by_id["next9_v4_save_post_probe_execution_identity_limited_20261002"]
        self.assertIn("recomputed after the original DOS probe", save_v4["requires_missing"][0])
        self.assertEqual(save_v4["audit_class"], "incomplete_execution_identity_limited_next9_v4")
        history = by_id["history_render_transitive_closure_448_20261002"]
        self.assertEqual(history["dos_count"], "checked")
        self.assertEqual(history["metrics"][1]["field"], "resource_window_commands_asserted")
        self.assertEqual(history["metrics"][2]["field"], "resource_window_pixels_touched")
        history_events = by_id["history_event_lowering_next10_closure_29_20261002"]
        self.assertEqual(history_events["dos_count"], "scope.cases")
        self.assertIn(("next10_compiled_profile.gcc_mm_commands", 25), history_events["list_lengths"])
        physical = by_id["physical_controls_source_geometry_native_sequence_20261002"]
        self.assertTrue(physical["skip_dependency_closure"])
        self.assertEqual(physical["dos_count"]["literal"], 0)
        self.assertEqual(physical["list_lengths"][-1], ("source_control_input_trace.records", 18))
        regeneration = by_id["next9_profile_regeneration_review_identity_20261002"]
        self.assertTrue(regeneration["scope_only"])
        module_hashes = regeneration["related_documents"][0]["path_hash_lists"]
        self.assertEqual(len(module_hashes), 2)
        self.assertEqual(regeneration["related_documents"][0]["assertions"][0],
                         ("status", "DIAGNOSTIC_ONLY_NOT_PRODUCTION"))
        self.assertEqual(control_engine["path_list_hash_map_membership"][0]["list_field"],
                         "compile.local_transitive_dependencies")

    def test_related_documents_check_recorded_path_hash_maps(self) -> None:
        with tempfile.TemporaryDirectory(prefix="verify-evidence-related-map-") as temp:
            root = Path(temp)
            dependency = root / "dependency.c"
            dependency.write_text("int dependency(void) { return 3; }\n", encoding="utf-8")
            dependency_hash = hashlib.sha256(dependency.read_bytes()).hexdigest()
            related = root / "related.json"
            related.write_text(json.dumps({"pins": {str(dependency): dependency_hash}}), encoding="utf-8")
            report = root / "report.json"
            report.write_text(json.dumps({"status": "PASS"}), encoding="utf-8")
            row = verify.audit({
                "id": "related-map-test", "report": str(report), "scope_only": True,
                "related_documents": [{"path": str(related), "path_hash_maps": ["pins"]}],
            })
            self.assertEqual(row["status"], "CURRENT")
            self.assertTrue(any(check["label"].startswith("pins:") and check["result"] == "MATCH"
                                for check in row["checks"]))
            report.write_text(json.dumps({"status": "PASS", "inputs": [
                {"path": str(dependency), "sha256": dependency_hash}]}), encoding="utf-8")
            row_list = verify.audit({
                "id": "related-row-test", "report": str(report), "scope_only": True,
                "path_hash_lists": [{"field": "inputs", "path_field": "path", "hash_field": "sha256"}],
            })
            self.assertEqual(row_list["status"], "CURRENT")
            self.assertTrue(any(check["result"] == "MATCH" for check in row_list["checks"]))
            one_item = verify.audit({
                "id": "list-length-test", "report": str(report), "scope_only": True,
                "list_lengths": [("inputs", 1)],
            })
            self.assertEqual(one_item["status"], "CURRENT")
            wrong_length = verify.audit({
                "id": "list-length-negative-test", "report": str(report), "scope_only": True,
                "list_lengths": [("inputs", 2)],
            })
            self.assertEqual(wrong_length["status"], "STALE")

    def test_json_document_comparison_ignores_only_named_metadata(self) -> None:
        left = {"verdict": "PASS", "hybrid": "same", "timing": {"seconds": 1}}
        right = {"verdict": "PASS", "hybrid": "same", "timing": {"reused": True}}
        self.assertTrue(verify.json_equal_except_fields(left, right, ["timing"]))
        right["hybrid"] = "different"
        self.assertFalse(verify.json_equal_except_fields(left, right, ["timing"]))

    def test_dynamic_path_hash_uses_the_recorded_path_and_digest(self) -> None:
        with tempfile.TemporaryDirectory(prefix="verify-evidence-dynamic-pin-") as temp:
            source = Path(temp) / "artifact.bin"
            source.write_bytes(b"retained receipt object")
            digest = hashlib.sha256(source.read_bytes()).hexdigest()
            report = {"artifact": {"path": str(source), "sha256": digest}}
            checks: list[dict] = []
            missing: list[str] = []
            path, expected = verify.get_field(report, "artifact.path"), verify.get_field(report, "artifact.sha256")
            verify.check_hash(checks, missing, label="dynamic", expected=expected, path=path)
            self.assertFalse(missing)
            self.assertEqual(checks[0]["result"], "MATCH")

    def test_v3_harness_hash_binds_python_harness_and_source_separately(self) -> None:
        report_path = ROOT / "portable/tests/save/evidence/legacy-save-codec-v3/original-dos-sentinel-report.json"
        report = json.loads(report_path.read_text(encoding="utf-8"))
        behavior_hash = hashlib.sha256((ROOT / "tools/behavior.py").read_bytes()).hexdigest()
        source_hash = hashlib.sha256((ROOT / "src/S09/m35F5.c").read_bytes()).hexdigest()
        self.assertEqual(report["harness_sha256"], behavior_hash)
        self.assertEqual(report["source_sha256"], source_hash)
        self.assertEqual(report["harness_sha256"], "2c0799048057f59eae61a48be4d695278635594484adf0c70bf46c51b4e0c799")


if __name__ == "__main__":
    unittest.main()
