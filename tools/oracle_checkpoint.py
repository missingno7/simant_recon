#!/usr/bin/env python3
"""Read-only readiness audit for a frozen DOS semantic-oracle checkpoint.

The report is deliberately stricter than a progress summary: every ephemeral
validation run must be supplied as an immutable, hash-pinned input packet.
This tool never changes the registry, historical manifest, sources, or Git.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
HEX64 = re.compile(r"^[0-9a-f]{64}$")
DEFAULT_INPUTS = "work/takeover/behavioral-oracle/checkpoint-inputs.json"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def load_json(root: Path, rel: str, label: str, errors: list[str]) -> tuple[Any, Path | None]:
    if not isinstance(rel, str) or not rel:
        errors.append(f"{label}: path is missing")
        return None, None
    path = (root / rel).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError:
        errors.append(f"{label}: path escapes repository")
        return None, None
    try:
        return json.loads(path.read_text(encoding="utf-8")), path
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        errors.append(f"{label}: cannot read JSON ({exc})")
        return None, path


def check_pin(root: Path, pin: Any, label: str, errors: list[str]) -> tuple[Path | None, str | None]:
    if not isinstance(pin, dict):
        errors.append(f"{label}: required path/hash pin is missing")
        return None, None
    rel, expected = pin.get("path"), pin.get("sha256")
    if not isinstance(rel, str) or not rel:
        errors.append(f"{label}: path is missing")
        return None, None
    path = (root / rel).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError:
        errors.append(f"{label}: path escapes repository")
        return None, None
    if not path.is_file():
        errors.append(f"{label}: file does not exist: {rel}")
        return None, None
    if not isinstance(expected, str) or not HEX64.fullmatch(expected):
        errors.append(f"{label}: malformed SHA-256")
        return path, None
    actual = sha256_file(path)
    if actual != expected:
        errors.append(f"{label}: stale SHA-256")
    return path, actual


def address_key(row: Any) -> tuple | None:
    if not isinstance(row, dict):
        return None
    unit, seg, off, size = (row.get(k) for k in ("unit", "seg", "off", "size"))
    if (not isinstance(unit, str) or not unit or
            any(not isinstance(v, int) or isinstance(v, bool) or v < 0 for v in (seg, off, size))):
        return None
    return unit, seg, off, size


def _tree_inventory(root: Path, paths: list[Path]) -> tuple[str, dict[str, str]]:
    records = {}
    for path in paths:
        rel = path.resolve().relative_to(root.resolve()).as_posix()
        records[rel] = sha256_file(path)
    digest = hashlib.sha256()
    for rel in sorted(records):
        digest.update(rel.encode("utf-8"))
        digest.update(b"\0")
        digest.update(records[rel].encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest(), records


def current_validation_inputs(root: Path) -> dict[str, Any]:
    """Return deterministic tree digests that a completed validation packet pins."""
    source_files = sorted(p for p in (root / "src").rglob("*") if p.is_file()) if (root / "src").is_dir() else []
    validation_files = []
    if (root / ".gitattributes").is_file():
        validation_files.append(root / ".gitattributes")
    for folder, suffixes in (("tools", {".py"}), ("tests", {".py"}), ("layout", {".json"})):
        directory = root / folder
        if directory.is_dir():
            validation_files.extend(p for p in directory.rglob("*") if p.is_file() and p.suffix.lower() in suffixes)
    source_hash, source_map = _tree_inventory(root, source_files)
    validation_hash, validation_map = _tree_inventory(root, validation_files)
    return {"source_tree_sha256": source_hash, "source_files": source_map,
            "validation_inputs_sha256": validation_hash, "validation_files": validation_map}


def _validate_historical_run(root: Path, packet: Any, errors: list[str]) -> dict[str, Any]:
    if not isinstance(packet, dict) or packet.get("schema") != "simant-historical-validation-pin-v1":
        errors.append("historical validation pin packet has unsupported schema")
        return {}
    if packet.get("status") != "PASS":
        errors.append("historical validation packet does not record PASS")
    review = packet.get("review")
    if (not isinstance(review, dict) or review.get("status") != "APPROVED"
            or review.get("reviewer") != "root" or not review.get("reviewed_at") or not review.get("reason")):
        errors.append("historical validation packet lacks explicit root review")
    log, _ = check_pin(root, packet.get("log"), "historical validation log", errors)
    if log is not None:
        try:
            text = log.read_text(encoding="utf-8", errors="replace")
            if "VALIDATION PASS" not in text and "VALIDATION: PASS" not in text:
                errors.append("historical validation log does not contain a PASS marker")
        except OSError as exc:
            errors.append(f"historical validation log cannot be read: {exc}")
    tool_pins = packet.get("tools")
    required = ("tools/validate.py", "tools/link.py", "layout/toolchain.json")
    if not isinstance(tool_pins, dict):
        errors.append("historical validation packet must pin current validation/link/toolchain inputs")
        tool_pins = {}
    for rel in required:
        pin = tool_pins.get(rel)
        if not isinstance(pin, dict) or pin.get("path") != rel:
            errors.append(f"historical validation packet lacks current tool pin {rel}")
        else:
            check_pin(root, pin, f"historical validation tool {rel}", errors)
    manifest_hash = packet.get("manifest_sha256")
    manifest = root / "layout/manifest.json"
    if not isinstance(manifest_hash, str) or not HEX64.fullmatch(manifest_hash):
        errors.append("historical validation packet manifest_sha256 is malformed")
    elif not manifest.is_file() or sha256_file(manifest) != manifest_hash:
        errors.append("historical validation packet is stale for the current historical manifest")
    current_trees = current_validation_inputs(root)
    for field in ("source_tree_sha256", "validation_inputs_sha256"):
        if packet.get(field) != current_trees[field]:
            errors.append(f"historical validation packet is stale for current {field}")
    return {"status": packet.get("status"), "log": packet.get("log"), "manifest_sha256": manifest_hash}


def build_report(root: Path = ROOT, inputs_path: str = DEFAULT_INPUTS) -> dict[str, Any]:
    root = root.resolve()
    errors: list[str] = []
    inputs, ipath = load_json(root, inputs_path, "checkpoint inputs", errors)
    if not isinstance(inputs, dict) or inputs.get("schema") != "simant-oracle-checkpoint-inputs-v1":
        errors.append("checkpoint inputs have unsupported schema")
        inputs = {}
    review = inputs.get("review")
    if (not isinstance(review, dict) or review.get("status") != "APPROVED"
            or review.get("reviewer") != "root" or not review.get("reason") or not review.get("reviewed_at")):
        errors.append("checkpoint inputs need an explicit root-reviewed freeze packet")

    progress, progress_path = load_json(root, "docs/progress.json", "progress", errors)
    registry, registry_path = load_json(root, "evidence/behavior/manifest.json", "behavior registry", errors)
    historical, historical_path = load_json(root, "layout/manifest.json", "historical manifest", errors)
    functions, functions_path = load_json(root, "layout/functions.json", "function inventory", errors)
    debt, debt_path = load_json(root, "work/takeover/behavioral-oracle/data-debt.json", "data debt inventory", errors)
    provenance, provenance_path = load_json(root, "build/link/provenance.json", "hybrid provenance", errors)

    hashes = {}
    for name, path in (("progress", progress_path), ("registry", registry_path),
                       ("historical_manifest", historical_path), ("function_inventory", functions_path),
                       ("data_debt", debt_path), ("hybrid_provenance", provenance_path),
                       ("oracle", root / "assets/SIMANT.EXE"),
                       ("validator", root / "tools/behavior_validate.py")):
        if path is not None and path.is_file():
            hashes[name] = sha256_file(path)

    game_rows = [row for row in functions.get("functions", []) if isinstance(row, dict)
                 and row.get("region") == "game_or_library"] if isinstance(functions, dict) else []
    game_keys = {key for row in game_rows if (key := address_key(row)) is not None}
    exact_keys = set()
    if isinstance(historical, dict):
        for module in historical.get("modules", {}).values():
            if isinstance(module, dict):
                for claim in module.get("claims", []):
                    key = address_key(claim)
                    if key in game_keys:
                        exact_keys.add(key)
    entries = registry.get("entries", {}) if isinstance(registry, dict) else {}
    if not isinstance(entries, dict):
        errors.append("behavior registry entries must be an object")
        entries = {}
    states = {"EXACT": len(exact_keys), "BEHAVIOR_EXACT": 0, "UNRESOLVED": 0}
    for name, row in entries.items():
        if not isinstance(row, dict) or row.get("status") not in ("BEHAVIOR_EXACT", "UNRESOLVED"):
            errors.append(f"behavior registry row {name} has invalid status")
            continue
        states[row["status"]] += 1
    target_code_bytes = 0
    for name, row in entries.items():
        size = row.get("initial_target_bytes") if isinstance(row, dict) else None
        if not isinstance(size, int) or isinstance(size, bool) or size <= 0:
            errors.append(f"behavior registry row {name} lacks a positive initial_target_bytes extent")
        else:
            target_code_bytes += size
    if states["EXACT"] + len(entries) != len(game_rows):
        errors.append("historical EXACT plus behavioral-registry rows do not reconcile to game function inventory")

    behavior_input = inputs.get("behavior_validation")
    behavior_report_path, _ = check_pin(root, behavior_input, "behavior --all validation report", errors)
    behavior_report = None
    if behavior_report_path:
        try:
            behavior_report = json.loads(behavior_report_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            errors.append(f"behavior --all validation report is invalid JSON: {exc}")
    if not isinstance(behavior_report, dict) or behavior_report.get("valid") is not True:
        errors.append("behavior --all validation report is missing or not valid")
    else:
        cats = behavior_report.get("categories", {})
        if not isinstance(cats, dict):
            errors.append("behavior --all report categories are missing")
            cats = {}
        report_states = {k: cats.get(k) for k in states}
        if report_states != states:
            errors.append("behavior --all category counts do not match current registry and historical claims")
        results = behavior_report.get("registered_behavior")
        if not isinstance(results, dict) or set(results) != {
                name for name, row in entries.items() if isinstance(row, dict) and row.get("status") == "BEHAVIOR_EXACT"}:
            errors.append("behavior --all results do not cover exactly the registered BEHAVIOR_EXACT rows")
        elif any(not isinstance(result, dict) or result.get("valid") is not True for result in results.values()):
            errors.append("behavior --all contains an invalid registered packet")
        pins = {
            "registry_sha256": hashes.get("registry"),
            "historical_manifest_sha256": hashes.get("historical_manifest"),
            "validator_sha256": hashes.get("validator"),
        }
        for field, expected in pins.items():
            if behavior_input.get(field) != expected:
                errors.append(f"behavior validation receipt is not pinned to current {field}")
        current_trees = current_validation_inputs(root)
        for field in ("source_tree_sha256", "validation_inputs_sha256"):
            if behavior_input.get(field) != current_trees[field]:
                errors.append(f"behavior validation receipt is stale for current {field}")

    historical_input = inputs.get("historical_validation")
    historical_summary = _validate_historical_run(root, historical_input, errors)

    oracle_path = root / "assets/SIMANT.EXE"
    oracle_hash = sha256_file(oracle_path) if oracle_path.is_file() else None
    if isinstance(provenance, dict):
        if provenance.get("hybrid_equal") is not True:
            errors.append("current hybrid provenance does not report byte equality")
        if provenance.get("oracle_sha256") != oracle_hash or provenance.get("hybrid_sha256") != oracle_hash:
            errors.append("hybrid provenance/oracle hashes do not equal the current original EXE")
    else:
        errors.append("hybrid provenance is unavailable")
    hybrid_path = root / "build/link/SIMANT.HYBRID.EXE"
    if not hybrid_path.is_file():
        errors.append("hybrid image file is missing")
    else:
        hybrid_hash = sha256_file(hybrid_path)
        if hybrid_hash != oracle_hash:
            errors.append("hybrid image bytes/hash differ from the original EXE")

    debt_summary = {"unresolved_bytes": None, "explicit_spans": 0, "literal_span_bytes": 0,
                    "section27_tail_overlap_bytes": None}
    if isinstance(debt, dict):
        reconciliation = debt.get("reconciliation", {})
        spans = debt.get("literal_spans", [])
        debt_summary.update({
            "unresolved_bytes": reconciliation.get("progress_residual"),
            "explicit_spans": len(spans) if isinstance(spans, list) else 0,
            "literal_span_bytes": sum(s.get("size", 0) for s in spans if isinstance(s, dict)),
            "section27_tail_overlap_bytes": reconciliation.get("section27_common_tail_overlap_bytes"),
        })
        if debt.get("oracle_sha256") != oracle_hash:
            errors.append("data debt inventory oracle pin does not match current original EXE")
        if not isinstance(spans, list):
            errors.append("data debt literal_spans must be a list")
            spans = []
        for span in spans:
            if not isinstance(span, dict) or not isinstance(span.get("ownership"), str) or not span["ownership"].strip():
                errors.append("each unresolved data span must retain an explicit ownership disposition")
                continue
            raw_hex = span.get("bytes_hex")
            try:
                raw = bytes.fromhex(raw_hex) if isinstance(raw_hex, str) else b""
            except ValueError:
                raw = b""
            if len(raw) != span.get("size") or hashlib.sha256(raw).hexdigest() != span.get("sha256"):
                errors.append(f"data debt span {span.get('id')} bytes/hash/size do not agree")
            file_range = span.get("original_exe_file_range")
            if (not isinstance(file_range, list) or len(file_range) != 2
                    or any(not isinstance(x, int) for x in file_range)
                    or file_range[0] < 0 or file_range[1] < file_range[0]):
                errors.append(f"data debt span {span.get('id')} has an invalid original file range")
            elif oracle_path.is_file():
                original = oracle_path.read_bytes()[file_range[0]:file_range[1]]
                if original != raw:
                    errors.append(f"data debt span {span.get('id')} does not match the pinned original bytes")
        data_review = inputs.get("data_review")
        if (not isinstance(data_review, dict) or data_review.get("status") != "APPROVED"
                or data_review.get("reviewer") != "root" or not data_review.get("reviewed_at")
                or not data_review.get("reason")
                or data_review.get("data_debt_sha256") != hashes.get("data_debt")):
            errors.append("remaining data debt requires an explicit root-reviewed disposition pinned to the current inventory")
        for pin in debt.get("source_pins", []) if isinstance(debt.get("source_pins"), list) else []:
            check_pin(root, pin, "data debt source", errors)
        if progress.get("unresolved_data_bytes") != debt_summary["unresolved_bytes"]:
            errors.append("data debt residual does not match current progress")
        total = debt_summary["literal_span_bytes"] + (debt_summary["section27_tail_overlap_bytes"] or 0)
        if total != debt_summary["unresolved_bytes"]:
            errors.append("explicit data-debt spans/tail do not reconcile to unresolved data bytes")
        if isinstance(reconciliation, dict) and reconciliation.get("progress_matches_provenance") is not True:
            errors.append("data debt inventory lacks progress/provenance reconciliation")
    else:
        errors.append("data debt inventory is unavailable")

    if not isinstance(progress, dict) or progress.get("validation") != "PASS":
        errors.append("docs/progress.json does not report historical validation PASS")
    if isinstance(progress, dict) and progress.get("oracle_sha256") != oracle_hash:
        errors.append("progress report oracle pin is stale")

    rtlink = progress.get("rtlink_manager_bytes_unaccepted") if isinstance(progress, dict) else None
    total_code_debt = progress.get("unresolved_code_bytes") if isinstance(progress, dict) else None
    orphan_code_debt = (total_code_debt - target_code_bytes
                        if isinstance(total_code_debt, int) and total_code_debt >= target_code_bytes else None)
    if orphan_code_debt is None:
        errors.append("historical unresolved code does not reconcile to registered open-function extents")
    gap_bundle = inputs.get("gap_review_bundle")
    covered_gap_bytes = 0
    gap_count = 0
    if not isinstance(gap_bundle, dict) or gap_bundle.get("status") != "APPROVED" or gap_bundle.get("reviewer") != "root" or not gap_bundle.get("reason"):
        errors.append("supplemental addresses require an explicit root-approved gap-review bundle")
    else:
        gap_path, _ = check_pin(root, gap_bundle.get("artifact"), "supplemental gap review bundle", errors)
        if gap_path is not None:
            bundle, _ = load_json(root, gap_bundle["artifact"].get("path"), "supplemental gap bundle", errors)
            if not isinstance(bundle, dict) or bundle.get("schema") != "simant-code-gap-review-bundle-v1":
                errors.append("supplemental gap bundle has unsupported schema")
            elif not isinstance(bundle.get("contracts"), list) or not bundle["contracts"]:
                errors.append("supplemental gap bundle must enumerate reviewed address contracts")
            else:
                gap_count = len(bundle["contracts"])
                gap_ranges: dict[tuple[str, int], list[tuple[int, int]]] = {}
                for index, contract in enumerate(bundle["contracts"]):
                    amount = contract.get("covered_bytes") if isinstance(contract, dict) else None
                    if (not isinstance(contract, dict) or contract.get("status") != "APPROVED"
                            or not contract.get("address") or not contract.get("reason")
                            or not isinstance(amount, int) or isinstance(amount, bool) or amount <= 0):
                        errors.append(f"supplemental gap contract {index} is incomplete")
                    else:
                        covered_gap_bytes += amount
                        ranges = contract.get("ranges")
                        range_bytes = 0
                        if not isinstance(ranges, list) or not ranges:
                            errors.append(f"supplemental gap contract {index} needs structured address ranges")
                            ranges = []
                        for row in ranges:
                            if (not isinstance(row, dict) or not isinstance(row.get("unit"), str)
                                    or not row["unit"] or any(not isinstance(row.get(k), int)
                                    or isinstance(row.get(k), bool) for k in ("seg", "start", "end"))
                                    or row["seg"] < 0 or row["start"] < 0
                                    or row["end"] <= row["start"] or row["end"] > 65536):
                                errors.append(f"supplemental gap contract {index} has an invalid address range")
                                continue
                            range_bytes += row["end"] - row["start"]
                            key = (row["unit"], row["seg"])
                            prior = gap_ranges.setdefault(key, [])
                            if any(row["start"] < end and start < row["end"] for start, end in prior):
                                errors.append(f"supplemental gap contract {index} overlaps another covered range")
                            prior.append((row["start"], row["end"]))
                        if range_bytes != amount:
                            errors.append(f"supplemental gap contract {index} range lengths do not match covered_bytes")
                        for pin in contract.get("evidence", []):
                            check_pin(root, pin, f"supplemental gap contract {index} evidence", errors)
                if bundle.get("review", {}).get("status") != "APPROVED" or bundle["review"].get("reviewer") != "root":
                    errors.append("supplemental gap bundle itself lacks root review")
    if orphan_code_debt is not None and covered_gap_bytes != orphan_code_debt:
        errors.append("root-reviewed supplemental gap bundle does not cover the code bytes outside open function extents")
    debt_summary["supplemental_gap_contracts"] = gap_count

    directed_total = 0
    randomized_total = 0
    if isinstance(behavior_report, dict) and isinstance(entries, dict):
        suite_totals: dict[str, dict[str, int]] = {}
        for name, row in entries.items():
            if not isinstance(row, dict) or row.get("status") != "BEHAVIOR_EXACT":
                continue
            packet_path = root / row.get("evidence_path", "")
            try:
                packet_bytes = packet_path.read_bytes()
                packet = json.loads(packet_bytes)
            except (OSError, UnicodeError, json.JSONDecodeError):
                errors.append(f"{name}: registered evidence packet cannot be read for case totals")
                continue
            if hashlib.sha256(packet_bytes).hexdigest() != row.get("evidence_sha256"):
                errors.append(f"{name}: registered evidence packet hash changed during checkpoint audit")
                continue
            run_pin = packet.get("run_report", {}) if isinstance(packet, dict) else {}
            run_path, _ = check_pin(root, run_pin, f"{name} run report", errors)
            if run_path is None:
                continue
            try:
                run = json.loads(run_path.read_text(encoding="utf-8"))
            except (OSError, UnicodeError, json.JSONDecodeError):
                errors.append(f"{name}: run report cannot be read for case totals")
                continue
            cases = run.get("cases", {}) if isinstance(run, dict) else {}
            suite_id = packet.get("suite", {}).get("id") if isinstance(packet.get("suite"), dict) else None
            if not isinstance(suite_id, str) or not suite_id:
                errors.append(f"{name}: registered packet lacks a suite identity")
                suite_id = "UNKNOWN"
            totals = suite_totals.setdefault(suite_id, {"functions": 0, "directed": 0, "randomized": 0})
            totals["functions"] += 1
            for lane in ("directed", "randomized"):
                detail = cases.get(lane) if isinstance(cases, dict) else None
                generated = detail.get("generated") if isinstance(detail, dict) else None
                executed = detail.get("executed") if isinstance(detail, dict) else None
                if not isinstance(generated, int) or generated != executed:
                    errors.append(f"{name}: {lane} case counts are absent or incomplete")
                elif lane == "directed":
                    directed_total += executed
                    totals["directed"] += executed
                else:
                    randomized_total += executed
                    totals["randomized"] += executed
        for totals in suite_totals.values():
            totals["total"] = totals["directed"] + totals["randomized"]
    else:
        suite_totals = {}

    exact_c_functions = progress.get("exact_c_functions") if isinstance(progress, dict) else None
    exact_asm_functions = progress.get("exact_asm_functions") if isinstance(progress, dict) else None
    if (not isinstance(exact_c_functions, int) or not isinstance(exact_asm_functions, int)
            or exact_c_functions + exact_asm_functions != states["EXACT"]):
        errors.append("progress C/ASM EXACT function counts do not reconcile to historical manifest claims")
    report = {
        "schema": "simant-oracle-checkpoint-readiness-v1",
        "ready": not errors and states["UNRESOLVED"] == 0,
        "proof_categories": states,
        "historical_exact_detail": {
            "C_functions": exact_c_functions,
            "ASM_functions": exact_asm_functions,
            "C_bytes": progress.get("exact_c_bytes") if isinstance(progress, dict) else None,
            "ASM_bytes": progress.get("exact_asm_bytes") if isinstance(progress, dict) else None,
        },
        "behavior_case_totals": {"directed": directed_total, "randomized": randomized_total,
                                 "total": directed_total + randomized_total},
        "behavior_suite_totals": suite_totals,
        "game_function_count": len(game_rows),
        "registry_function_count": len(entries),
        "historical_code_debt_bytes": total_code_debt,
        "open_function_code_extents_bytes": target_code_bytes,
        "unowned_code_outside_open_functions_bytes": orphan_code_debt,
        "supplemental_gap_contract_bytes": covered_gap_bytes,
        "historical_data_debt": debt_summary,
        "rtlink_debt_bytes_separate_nonblocking": rtlink,
        "oracle": {"path": "assets/SIMANT.EXE", "sha256": oracle_hash,
                   "hybrid_sha256": provenance.get("hybrid_sha256") if isinstance(provenance, dict) else None,
                   "hybrid_equal": (hybrid_path.is_file() and oracle_hash is not None
                                    and sha256_file(hybrid_path) == oracle_hash)},
        "historical_validation": historical_summary,
        "source_sha256": hashes,
        "current_rebuild_inputs": current_validation_inputs(root),
        "inputs_sha256": sha256_file(ipath) if ipath and ipath.is_file() else None,
        "residual_proof_debt": {
            "unresolved_behavior_functions": states["UNRESOLVED"],
            "historical_unresolved_game_code_bytes": total_code_debt,
            "code_bytes_outside_open_function_extents": orphan_code_debt,
            "historical_unresolved_data_bytes": debt_summary["unresolved_bytes"],
            "rtlink_manager_linker_bytes": rtlink,
        },
        "errors": errors,
    }
    return report


def markdown(report: dict[str, Any]) -> str:
    categories = report.get("proof_categories", {})
    debt = report.get("historical_data_debt", {})
    oracle = report.get("oracle", {})
    lines = ["# DOS semantic-oracle checkpoint readiness", "",
             f"**Ready:** {'YES' if report.get('ready') else 'NO'}", "",
             "| Proof category | Functions |", "|---|---:|",
             f"| EXACT | {categories.get('EXACT')} |",
             f"| BEHAVIOR_EXACT | {categories.get('BEHAVIOR_EXACT')} |",
             f"| UNRESOLVED | {categories.get('UNRESOLVED')} |", "",
             f"Historical EXACT detail: {report.get('historical_exact_detail')}; behavior cases: {report.get('behavior_case_totals')} across {len(report.get('behavior_suite_totals', {}))} suites.",
             f"Game function inventory: {report.get('game_function_count')}; registry rows: {report.get('registry_function_count')}.",
             f"Oracle/hybrid SHA-256: `{oracle.get('sha256')}` / `{oracle.get('hybrid_sha256')}`; equal: `{oracle.get('hybrid_equal')}`.",
             f"Historical code debt: {report.get('historical_code_debt_bytes')} bytes ({report.get('open_function_code_extents_bytes')} in open function extents; {report.get('unowned_code_outside_open_functions_bytes')} outside those extents, with {report.get('supplemental_gap_contract_bytes')} bytes in root-reviewed gap contracts). Data debt: {debt.get('unresolved_bytes')} bytes in {debt.get('explicit_spans')} explicit spans ({debt.get('literal_span_bytes')} literal bytes plus section-tail overlap {debt.get('section27_tail_overlap_bytes')}).",
             f"RTLink debt: {report.get('rtlink_debt_bytes_separate_nonblocking')} bytes, tracked separately.", "",
             "## Residual proof debt", "",
             "The report distinguishes historical code/data identity from behavioral closure. RTLink debt is a separate proof level and does not affect the game-semantic category counts.", ""]
    errors = report.get("errors", [])
    if errors:
        lines += ["## Readiness failures", ""] + [f"- {error}" for error in errors] + [""]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", default=DEFAULT_INPUTS, help="root-reviewed checkpoint input packet")
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    parser.add_argument("--output", type=Path, help="optional output path; omitted means stdout only")
    args = parser.parse_args(argv)
    report = build_report(ROOT, args.inputs)
    rendered = json.dumps(report, indent=2) + "\n" if args.format == "json" else markdown(report)
    if args.output:
        output = args.output if args.output.is_absolute() else ROOT / args.output
        try:
            output.resolve().relative_to(ROOT.resolve())
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(rendered, encoding="utf-8")
        except (OSError, ValueError) as exc:
            print(json.dumps({"ready": False, "errors": [f"cannot write report: {exc}"]}, indent=2))
            return 1
    else:
        print(rendered, end="")
    return 0 if report.get("ready") else 1


if __name__ == "__main__":
    raise SystemExit(main())
