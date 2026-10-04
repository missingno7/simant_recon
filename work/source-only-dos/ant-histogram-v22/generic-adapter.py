#!/usr/bin/env python3
"""Build a root-false generic storage-contract candidate from preserved v22 receipts.

This adapter does not invoke the compiler, linker, runner, emulator, or promotion tools.
It verifies and copies only the already-recorded text inputs/receipts, verifies the
existing raw case artifact pins, and emits a new scratch-only JSON candidate.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
WORKER = ROOT / "build/workers/dos_ant_histogram_v22"
RUN_ID = "run-20261004T031319Z-ca15a6bce736"
RUN = WORKER / RUN_ID
DEST = WORKER / "proposed-durable-v22-20261004-03"
CONTRACT_NAME = "storage-contract-candidate-v22.json"

REQUIRED_CASES = {
    "positive_crt_zero_all_32_signed_words_raw_bytes": "PASS",
    "wrong_test_base_plus_one_word": "REJECTED_BASE",
    "wrong_initialized_data_owner": "REJECTED_CRT_ZERO",
    "wrong_unsigned_consumer_view": "REJECTED_UNSIGNED_VIEW",
}
TARGET = "_fd_50f6_0eb6"
ALIAS = "_histogramprobealias"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def pin_file(path: Path) -> dict:
    data = path.read_bytes()
    return {"path": path.relative_to(ROOT).as_posix(), "sha256": sha(data), "size": len(data)}


def check_pin(row: dict, *, rewrite: str | None = None) -> dict:
    path = ROOT / row["path"]
    data = path.read_bytes()
    if len(data) != row["size"] or sha(data) != row["sha256"]:
        raise ValueError(f"pinned artifact changed: {row['path']}")
    return {
        "path": rewrite or row["path"],
        "sha256": row["sha256"],
        "size": row["size"],
    }


def copy_pinned(source_rel: str, durable_rel: str) -> dict:
    source = ROOT / source_rel
    data = source.read_bytes()
    target = DEST / durable_rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    if target.read_bytes() != data:
        raise ValueError(f"copy mismatch: {source_rel}")
    return {"path": (DEST / durable_rel).relative_to(ROOT).as_posix(),
            "sha256": sha(data), "size": len(data)}


def address(row: dict) -> tuple[int, int]:
    return int(row["segment"], 16), int(row["offset"], 16)


def address_text(row: dict) -> str:
    segment, offset = address(row)
    return f"{segment:04X}:{offset:04X}"


def main() -> None:
    if DEST.exists():
        raise SystemExit(f"refusing to overwrite existing proposed durable tree: {DEST}")
    raw_receipt_path = RUN / "candidate-receipt.json"
    normalized_path = WORKER / "parent-admission-normalized-v22.json"
    raw_receipt = json.loads(raw_receipt_path.read_text(encoding="utf-8"))
    normalized = json.loads(normalized_path.read_text(encoding="utf-8"))

    if raw_receipt.get("run_id") != RUN_ID or not raw_receipt.get("case_summary", {}).get("all_required_cases_passed"):
        raise ValueError("unexpected or incomplete preserved runtime receipt")
    if normalized.get("root_reviewed") is not False or normalized.get("all_technical_checks_pass") is not True:
        raise ValueError("normalized check-only receipt is not the expected root-false technical pass")
    if len(raw_receipt.get("runtime_cases", [])) != 8:
        raise ValueError("expected exactly eight preserved linker/runtime rows")

    # Proposed durable copies. Raw evidence stays byte-identical; path rewrites
    # appear only in the new generic contract below.
    copied = {
        "provider": copy_pinned(
            "work/source-only-dos/providers/ant-class-histogram.c",
            "work/source-only-dos/providers/ant-class-histogram.c"),
        "probe": copy_pinned(
            "work/source-only-dos/ant-histogram-owner-probe-v22.py",
            "work/source-only-dos/ant-histogram-owner-probe-v22.py"),
        "source_review_json": copy_pinned(
            "work/source-only-dos/ant-histogram-owner-candidate-v22.json",
            "work/source-only-dos/ant-histogram-owner-candidate-v22.json"),
        "source_review_markdown": copy_pinned(
            "work/source-only-dos/ant-histogram-owner-candidate-v22.md",
            "work/source-only-dos/ant-histogram-owner-candidate-v22.md"),
        "source_audit": copy_pinned(
            f"build/workers/dos_ant_histogram_v22/{RUN_ID}/source-audit.json",
            "evidence/source-audit-v22.json"),
        "research_receipt": copy_pinned(
            f"build/workers/dos_ant_histogram_v22/{RUN_ID}/candidate-receipt.json",
            "evidence/candidate-receipt-v22.json"),
        "normalized_receipt": copy_pinned(
            "build/workers/dos_ant_histogram_v22/parent-admission-normalized-v22.json",
            "evidence/parent-admission-normalized-v22.json"),
        "normalizer": copy_pinned(
            "build/workers/dos_ant_histogram_v22/parent-admission-check-v22.py",
            "evidence/parent-admission-check-v22.py"),
    }

    provider_source = (DEST / "work/source-only-dos/providers/ant-class-histogram.c").read_text(encoding="utf-8")
    declaration = provider_source.split("*/", 1)[-1].strip()
    if declaration != "int far fd_50F6_0EB6[32];":
        raise ValueError("provider source does not match reviewed natural-C declaration")

    # Verify each recorded raw runtime file against the receipt and preserve a
    # compact file pin set. This is read-only and does not re-run any tools.
    raw_file_index: dict[tuple[str, str, str], dict] = {}
    for runtime in raw_receipt["runtime_cases"]:
        for row in runtime["files"]:
            verified = check_pin(row)
            key = (runtime["linker"], runtime["case"], Path(row["path"]).name.upper())
            raw_file_index[key] = verified

    # All historical immutable source/toolchain pins represented by the
    # check-only normalizer are rechecked before being copied into the contract.
    tool_pins = normalized["input_pins"]["toolchain"]["verified_external_and_workspace_pins"]
    checked_tool_pins = [check_pin(p) for p in tool_pins]
    source_scope = normalized["input_pins"]["source_scope"]
    strict_source_pins = [check_pin(p) for p in source_scope["registry_pins"].values()]
    strict_receipt_pins = [check_pin(p) for p in source_scope["strict_receipt_pins"].values()]
    selected_inputs = [
        {**copied["provider"], "kind": "provider_source"},
        {**copied["probe"], "kind": "probe_source"},
        {**copied["source_review_json"], "kind": "source_review"},
        {**copied["source_review_markdown"], "kind": "source_review_markdown"},
        {**copied["source_audit"], "kind": "source_audit_receipt"},
        {**copied["research_receipt"], "kind": "runtime_research_receipt"},
        {**copied["normalized_receipt"], "kind": "check_only_normalized_receipt"},
        {**copied["normalizer"], "kind": "check_only_normalizer"},
    ]
    selected_inputs.extend({**p, "kind": "toolchain_or_runtime_pin"} for p in checked_tool_pins)
    selected_inputs.extend({**p, "kind": "canonical_or_strict_source_pin"} for p in strict_source_pins)
    selected_inputs.extend({**p, "kind": "strict_effective_receipt_pin"} for p in strict_receipt_pins)

    expected_owner_publics = [TARGET]
    case_rows = []
    for runtime in raw_receipt["runtime_cases"]:
        linker = runtime["linker"]
        case_name = runtime["case"]
        expected_marker = REQUIRED_CASES[case_name]
        if runtime["expected_output"] != expected_marker or runtime["actual_output"] != expected_marker:
            raise ValueError(f"runtime output mismatch: {linker}/{case_name}")
        run_file = next(row for row in runtime["files"] if Path(row["path"]).name.upper() == "RUN.LOG")
        run_bytes = (ROOT / run_file["path"]).read_bytes()
        expected_bytes = (expected_marker + "\r\n").encode("ascii")
        if run_bytes != expected_bytes:
            raise ValueError(f"raw RUN.LOG bytes mismatch: {linker}/{case_name}")

        map_row = normalized["maps"][linker][case_name]
        if map_row["sections_verified"] != ["Publics by Name", "Publics by Value"]:
            raise ValueError(f"missing verified Name/Value sections: {linker}/{case_name}")
        if map_row["run_log"]["sha256"] != run_file["sha256"] or map_row["run_log"]["size"] != run_file["size"]:
            raise ValueError(f"normalized/raw RUN.LOG pin mismatch: {linker}/{case_name}")

        section_addresses = {}
        map_sections = {}
        for section_key, section_title in (("name", "Name"), ("value", "Value")):
            symbols = map_row["publics"][section_key]
            folded_symbols = {name.lower(): value for name, value in symbols.items()}
            missing = [name for name in expected_owner_publics if name not in folded_symbols]
            if missing:
                raise ValueError(f"owner public absent from {section_title} map: {linker}/{case_name}: {missing}")
            if ALIAS not in folded_symbols:
                raise ValueError(f"test alias absent from {section_title} map: {linker}/{case_name}")
            section_addresses[section_title] = {
                name.lower(): address_text(value)
                for name, value in sorted(symbols.items(), key=lambda item: item[0].lower())
            }
            map_sections[section_title] = {
                "heading_present": True,
                "missing_required_publics": [],
                "owner_publics_found": expected_owner_publics,
                "test_alias_found": True,
                "map_pin": check_pin(map_row["map_input"]),
            }

        alias_relations = []
        for section_key, section_title in (("name", "Name"), ("value", "Value")):
            symbols = {name.lower(): value for name, value in map_row["publics"][section_key].items()}
            target_seg, target_off = address(symbols[TARGET])
            alias_seg, alias_off = address(symbols[ALIAS])
            observed_delta = alias_off - target_off if alias_seg == target_seg else None
            expected_delta = runtime["test_alias_delta_bytes"]
            passed = alias_seg == target_seg and observed_delta == expected_delta
            if not passed:
                raise ValueError(f"test alias geometry mismatch: {linker}/{case_name}/{section_title}")
            alias_relations.append({
                "alias": ALIAS,
                "target": TARGET,
                "section": section_title,
                "expected_offset_delta": expected_delta,
                "observed_offset_delta": observed_delta,
                "alias_address": address_text(symbols[ALIAS]),
                "target_address": address_text(symbols[TARGET]),
                "same_segment": True,
                "passed": True,
                "claim_limit": "relative test-owned alias geometry only; no historical placement or adjacency claim",
            })

        link_pin = check_pin(map_row["link_log"])
        map_pin = check_pin(map_row["map_input"])
        raw_case_pins = [check_pin(row) for row in runtime["files"]]
        if not runtime["link_clean"] or not runtime["exe_created"] or runtime["timed_out"]:
            raise ValueError(f"link/run status failed: {linker}/{case_name}")
        case_rows.append({
            "linker": linker,
            "case": case_name,
            "expected": expected_marker,
            "actual": expected_marker,
            "passed": True,
            "timed_out": False,
            "runner_returncode": runtime.get("host_returncode"),
            "linker_diagnostics": [],
            "linker_produced_executable": True,
            "linker_produced_map": True,
            "expected_owner_publics": expected_owner_publics,
            "owner_publics_found_in_map": expected_owner_publics,
            "map_public_sections": map_sections,
            "all_required_publics_in_both_sections": True,
            "public_address_matrix": section_addresses,
            "alias_map_relations": alias_relations,
            "expected_marker_verbatim": expected_bytes.decode("ascii"),
            "actual_marker_verbatim": run_bytes.decode("ascii"),
            "expected_marker_bytes_hex": expected_bytes.hex(),
            "actual_marker_bytes_hex": run_bytes.hex(),
            "expected_marker_sha256": sha(expected_bytes),
            "actual_marker_sha256": sha(run_bytes),
            "run_log_pin": check_pin(run_file),
            "link_log_pin": link_pin,
            "map_input_pin": map_pin,
            "raw_case_artifact_pins": raw_case_pins,
            "runtime_claim_limit": runtime["claim_limit"],
        })

    if len(case_rows) != 8:
        raise ValueError("candidate must contain four required cases per linker")

    provider_spec = {
        "module": "source-owned:ant-class-histogram",
        "basename": "ANTCOUNT",
        "owner": None,
        "profile": "msc600ax",
        "flags": ["/AL", "/Os", "/Gs"],
        "source": copied["provider"],
        "normalized_source": "int far fd_50F6_0EB6[32];",
        "communals": [{
            "name": "_fd_50F6_0EB6", "kind": "far", "count": 32,
            "element_size": 2, "length": 64,
        }],
        "historical_owner_or_tu_order_claimed": False,
        "historical_absolute_placement_claimed": False,
        "original_initializer_claimed": False,
        "single_data_only_object": True,
    }

    candidate = {
        "schema": "simant-dos-source-storage-contract-candidate-v22",
        "category": "CANDIDATE_SOURCE_STORAGE_CONTRACT",
        "status": "PARENT_REVIEW_PENDING_UNADMITTED",
        "root_reviewed": False,
        "admitted": False,
        "all_required_checks_pass": True,
        "module": "source-owned:ant-class-histogram",
        "communals": provider_spec["communals"],
        "required_cases": REQUIRED_CASES,
        "cases": case_rows,
        "inputs": selected_inputs,
        "probe_source": copied["probe"],
        "research_receipt": copied["research_receipt"],
        "source_review": copied["source_audit"],
        "source_review_markdown": copied["source_review_markdown"],
        "source_review_json": copied["source_review_json"],
        "normalized_check_only_receipt": copied["normalized_receipt"],
        "provider_spec": provider_spec,
        "source_coverage": {
            "canonical_source_count": source_scope["canonical_source_count"],
            "strict_effective_source_count": source_scope["strict_effective_source_count"],
            "strict_receipt_count": source_scope["strict_receipt_count"],
            "unique_source_count": source_scope["unique_source_count"],
            "strict_receipts_verified": source_scope["strict_receipts_verified"],
            "source_pin_set_sha256": source_scope["source_pin_set_sha256"],
            "registry_source_pins": strict_source_pins,
            "strict_receipt_pins": strict_receipt_pins,
        },
        "toolchain_and_runtime_pins": checked_tool_pins,
        "compiler_controls": normalized["compiler_controls"],
        "omf_controls": normalized["compiler_controls"]["omf"],
        "source_limits": {
            "separate_overflow_frontier": normalized["separate_overflow_frontier"],
            "claims": [
                "one source-functional signed int far[32] object only",
                "no historical defining TU, object order, original absolute placement, or initializer claim",
                "no malformed-index safety or bound claim for fd_50F6_04C2-derived expressions",
                "OMF common records do not encode signedness; natural-C provider declaration pins signed int",
            ],
        },
        "gate_proposal": {
            "provider_spec_registration": {
                "module": "source-owned:ant-class-histogram",
                "tuple_basename_owner": ["ANTCOUNT", None],
                "expected_owner_publics": expected_owner_publics,
                "communals": provider_spec["communals"],
                "far_word_array_names": ["_fd_50F6_0EB6"],
            },
            "reviewed_storage_gate": {
                "contract_key": "ant_class_histogram_contract",
                "required_cases": REQUIRED_CASES,
                "root_reviewed_required_for_acceptance": True,
                "all_required_checks_pass_required": True,
                "exact_communals_required": True,
                "four_cases_per_selected_linker_required": True,
                "input_component_hashes_must_match_selected_tool_and_runtime_components": True,
            },
            "clean_owner_map_gate": {
                "require_no_linker_diagnostics": True,
                "require_executable_and_map": True,
                "require_exact_owner_publics_in_both_name_and_value_sections": expected_owner_publics,
                "test_alias_is_geometry_evidence_only": ALIAS,
                "require_alias_target_delta_per_case": True,
            },
            "automatic_admission": False,
        },
    }

    contract_path = DEST / CONTRACT_NAME
    contract_path.parent.mkdir(parents=True, exist_ok=True)
    contract_path.write_text(json.dumps(candidate, indent=2) + "\n", encoding="utf-8")
    report = {
        "status": "PASS_ROOT_REVIEW_PENDING_UNADMITTED",
        "root_reviewed": False,
        "contract": contract_path.relative_to(ROOT).as_posix(),
        "contract_sha256": sha(contract_path.read_bytes()),
        "durable_tree": DEST.relative_to(ROOT).as_posix(),
        "copied_inputs": copied,
        "runtime_case_count": len(case_rows),
        "raw_case_file_pin_count": sum(len(c["raw_case_artifact_pins"]) for c in case_rows),
        "case_markers_verified_from_raw_RUN_LOG": True,
        "name_value_maps_verified_from_check_only_receipt": True,
        "all_eight_raw_case_artifact_sets_rehashed": True,
        "compiler_linker_runner_invoked": False,
        "production_or_canonical_files_modified": False,
    }
    report_path = DEST / "adapter-report-v22.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
