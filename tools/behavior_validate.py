#!/usr/bin/env python3
"""Fail-closed validation for separate BEHAVIOR_EXACT evidence.

This tool never edits the historical EXACT manifest or promotions journal. It
validates a review packet and can emit a read-only receipt for behavior_promote.py.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "evidence/behavior/manifest.json"
ORACLE_LOCK = "layout/oracle.lock.json"
HISTORICAL_MANIFEST = "layout/manifest.json"
RUNNER = "tools/behavior.py"
HARNESS_COMPONENTS = (
    "tools/exe.py", "tools/functions.py", "tools/match.py", "tools/modctx.py",
    "tools/modules.py", "tools/autosearch.py", "tools/compiler.py", "tools/omf.py",
    "tools/symbols.py", "tools/lockfile.py", "tools/csrc.py", "tools/srcrules.py",
    "tools/variants.py", "layout/toolchain.json",
    "tools/behavior_ledger.py",
)
SIMULATION_FUNCTIONS = {"SpiderScan", "o25_3BA4_1035", "o25_3BA4_1686"}
HEX64 = re.compile(r"^[0-9a-f]{64}$")
HEX40 = re.compile(r"^[0-9a-f]{40}$")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _compile_candidate(function: str, source_path: Path, sequence_targets: list[str] | None = None) -> dict:
    """Rebuild the submitted whole module through the actual PreparedPair path."""
    tools_dir = str(ROOT / "tools")
    if tools_dir not in sys.path:
        sys.path.insert(0, tools_dir)
    try:
        import behavior
        targets = sequence_targets or []
        pair = behavior.PreparedPair(function, source=source_path, sequence_targets=targets)
        strict = pair.strict
        if strict.get("compile_ok") is not True:
            return {"ok": False, "error": "whole-module historical compiler replay failed"}
        return {"ok": True, "object_sha256": pair.identity["object_sha256"],
                "compiled_source_sha256": pair.identity["compiled_source_sha256"],
                "profile": pair.identity["profile"], "flags": pair.identity["flags"],
                "address": pair.identity.get("address"),
                "sequence_targets": pair.identity.get("sequence_targets", []),
                "peer_data_gates": "PASS"}
    except Exception as exc:
        return {"ok": False, "error": f"whole-module historical compiler replay failed: {exc}"}


def _load_json(path: Path, label: str) -> tuple[Any | None, list[str]]:
    try:
        return json.loads(path.read_text(encoding="utf-8")), []
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return None, [f"{label}: cannot read valid JSON ({exc})"]


def _validate_revision_history(root: Path, row: Any) -> list[str]:
    """Check every retained behavior packet and the append-only predecessor chain."""
    errors: list[str] = []
    if not isinstance(row, dict):
        return ["behavior registry row is not an object"]
    revisions = row.get("revisions", [])
    if not isinstance(revisions, list):
        return ["behavior registry revisions must be an append-only list"]
    if not revisions:
        return errors
    initial_path, initial_hash = row.get("initial_evidence_path"), row.get("initial_evidence_sha256")
    current_path, current_hash = initial_path, initial_hash
    seen = set()
    for index, revision in enumerate(revisions):
        label = f"revision {index + 1}"
        if not isinstance(revision, dict):
            errors.append(f"{label}: entry is not an object")
            continue
        from_path, from_hash = revision.get("from_path"), revision.get("from_sha256")
        to_path, to_hash = revision.get("to_path"), revision.get("to_sha256")
        if (from_path, from_hash) != (current_path, current_hash):
            errors.append(f"{label}: predecessor does not continue the immutable packet chain")
        for value, digest, side in ((from_path, from_hash, "predecessor"),
                                    (to_path, to_hash, "revision packet")):
            path = _repo_file(root, value, f"{label} {side}", errors)
            if not isinstance(digest, str) or not HEX64.fullmatch(digest):
                errors.append(f"{label}: {side} hash is malformed")
            elif path is not None and sha256_file(path) != digest:
                errors.append(f"{label}: {side} packet hash is stale")
        if to_path in seen or to_path == from_path:
            errors.append(f"{label}: packet path is duplicated; registered packets are immutable")
        if isinstance(to_path, str):
            seen.add(to_path)
        review = revision.get("review")
        if (not isinstance(review, dict) or review.get("reviewer") != "root"
                or not review.get("reason") or not review.get("reviewed_at")):
            errors.append(f"{label}: explicit root review record is missing")
        current_path, current_hash = to_path, to_hash
    if (row.get("evidence_path"), row.get("evidence_sha256")) != (current_path, current_hash):
        errors.append("current registry packet does not match the end of its immutable revision chain")
    return errors


def _repo_file(root: Path, value: Any, label: str, errors: list[str]) -> Path | None:
    if not isinstance(value, str) or not value:
        errors.append(f"{label}: missing repository-relative path")
        return None
    candidate = (root / value).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError:
        errors.append(f"{label}: path escapes repository")
        return None
    if not candidate.is_file():
        errors.append(f"{label}: file does not exist: {value}")
        return None
    return candidate


def _pin_file(root: Path, record: dict, field: str, expected_path: str | None,
              label: str, errors: list[str]) -> str | None:
    if not isinstance(record, dict):
        errors.append(f"{label}: missing pin object")
        return None
    path_text = record.get("path")
    if expected_path is not None and path_text != expected_path:
        errors.append(f"{label}: path must be {expected_path}")
    path = _repo_file(root, path_text, label, errors)
    digest = record.get(field)
    if not isinstance(digest, str) or not HEX64.fullmatch(digest):
        errors.append(f"{label}: malformed {field}")
    elif path is not None:
        actual = sha256_file(path)
        if actual != digest:
            errors.append(f"{label}: stale SHA-256 (recorded {digest}, current {actual})")
    return digest if isinstance(digest, str) else None


def _nonempty_strings(value: Any, label: str, errors: list[str]) -> list[str]:
    if not isinstance(value, list) or not value or any(not isinstance(x, str) or not x.strip() for x in value):
        errors.append(f"{label}: must be a non-empty list of non-empty strings")
        return []
    if len(set(value)) != len(value):
        errors.append(f"{label}: duplicate entries")
    return value


def _validate_registry_target(root: Path, function: str, registry_path: Path,
                              errors: list[str], *, allow_revision: bool = False,
                              evidence: dict | None = None) -> dict | None:
    registry, load_errors = _load_json(registry_path, "behavior registry")
    errors.extend(load_errors)
    if not isinstance(registry, dict) or registry.get("schema") != "simant-behavior-evidence-manifest-v1":
        errors.append("behavior registry: unsupported or missing schema")
        return None
    entries = registry.get("entries")
    if not isinstance(entries, dict) or function not in entries:
        errors.append(f"{function}: not an open function in the separate behavior registry")
        return None
    row = entries[function]
    if isinstance(row, dict) and row.get("status") == "BEHAVIOR_EXACT" and allow_revision:
        journal = root / "evidence/promotions.jsonl"
        if journal.exists():
            try:
                for line in journal.read_text(encoding="utf-8").splitlines():
                    if line.strip() and function in json.loads(line).get("new_claims", []):
                        errors.append(f"{function}: historical EXACT promotion exists; revision is forbidden")
                        break
            except (OSError, json.JSONDecodeError) as exc:
                errors.append(f"historical promotion journal cannot be audited: {exc}")
        historical, hist_errors = _load_json(root / HISTORICAL_MANIFEST, "historical manifest")
        errors.extend(hist_errors)
        if isinstance(historical, dict) and any(
                isinstance(claim, dict) and claim.get("name") == function
                for module in historical.get("modules", {}).values() if isinstance(module, dict)
                for claim in module.get("claims", [])):
            errors.append(f"{function}: historical EXACT manifest claim exists; revision is forbidden")
        revision = evidence.get("revision") if isinstance(evidence, dict) else None
        previous = revision.get("previous_evidence") if isinstance(revision, dict) else None
        if not isinstance(previous, dict):
            errors.append(f"{function}: revision must identify the currently registered packet")
        else:
            if previous.get("path") != row.get("evidence_path") or previous.get("sha256") != row.get("evidence_sha256"):
                errors.append(f"{function}: revision predecessor does not match current immutable registry packet")
            old_path = _repo_file(root, previous.get("path"), "revision predecessor", errors)
            if old_path is not None and sha256_file(old_path) != previous.get("sha256"):
                errors.append(f"{function}: revision predecessor packet has changed")
            review = revision.get("review") if isinstance(revision, dict) else None
            if not isinstance(review, dict) or review.get("status") != "APPROVED" or review.get("reviewer") != "root" or not review.get("reviewed_at") or not review.get("reason"):
                errors.append(f"{function}: revision requires explicit root review and reason")
        return row
    if not isinstance(row, dict) or row.get("status") != "UNRESOLVED":
        errors.append(f"{function}: registry status is not UNRESOLVED; exact claims are immutable here")
        return None
    if row.get("evidence_sha256") not in (None, ""):
        errors.append(f"{function}: registry already has evidence; this tool will not replace it")
    # Defense in depth: no function with an existing historical promotion can be
    # reclassified through this separate registry.
    journal = root / "evidence/promotions.jsonl"
    if journal.exists():
        try:
            for line in journal.read_text(encoding="utf-8").splitlines():
                if line.strip() and function in json.loads(line).get("new_claims", []):
                    errors.append(f"{function}: historical EXACT promotion exists; behavior registration is forbidden")
                    break
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"historical promotion journal cannot be audited: {exc}")
    historical_path = root / HISTORICAL_MANIFEST
    historical, hist_errors = _load_json(historical_path, "historical manifest")
    errors.extend(hist_errors)
    if isinstance(historical, dict):
        for module in historical.get("modules", {}).values():
            for claim in module.get("claims", []) if isinstance(module, dict) else []:
                if isinstance(claim, dict) and claim.get("name") == function:
                    errors.append(f"{function}: historical EXACT manifest claim exists; behavior registration is forbidden")
                    return row
    return row


def validate_evidence(evidence: dict, *, root: Path = ROOT,
                      registry_path: Path = REGISTRY,
                      allow_registered: bool = False,
                      allow_revision: bool = False,
                      evidence_path: Path | None = None) -> dict:
    """Return a deterministic fail-closed validation result without writing files."""
    root = root.resolve()
    errors: list[str] = []
    if not isinstance(evidence, dict) or evidence.get("schema") != "simant-behavior-evidence-v1":
        return {"valid": False, "errors": ["unsupported evidence schema"]}
    function = evidence.get("function")
    if not isinstance(function, str) or not function:
        errors.append("function: missing name")
        function = ""
    if evidence.get("status") != "BEHAVIOR_EXACT":
        errors.append("status must explicitly propose BEHAVIOR_EXACT")
    registered_row = None
    if function:
        registry, reg_errors = _load_json(registry_path, "behavior registry")
        errors.extend(reg_errors)
        entry = registry.get("entries", {}).get(function) if isinstance(registry, dict) else None
        if allow_revision:
            prior_paths = set()
            if isinstance(entry, dict):
                for value in (entry.get("evidence_path"), entry.get("initial_evidence_path")):
                    if isinstance(value, str) and value:
                        prior_paths.add(value)
                for rev in entry.get("revisions", []) if isinstance(entry.get("revisions"), list) else []:
                    if isinstance(rev, dict):
                        for key in ("from_path", "to_path"):
                            if isinstance(rev.get(key), str):
                                prior_paths.add(rev[key])
            if evidence_path is not None:
                try:
                    packet_rel = str(evidence_path.resolve().relative_to(root)).replace("\\", "/")
                    if packet_rel in prior_paths:
                        errors.append(f"{function}: revision packet path must be new; prior evidence files are immutable")
                except ValueError:
                    errors.append("revision evidence path must be repository-local")
            elif not isinstance(evidence.get("revision"), dict):
                errors.append(f"{function}: revision metadata is required")
        if allow_registered and isinstance(entry, dict) and entry.get("status") == "BEHAVIOR_EXACT":
            registered_row = entry
            if not isinstance(entry.get("evidence_path"), str) or not isinstance(entry.get("evidence_sha256"), str):
                errors.append(f"{function}: registered evidence path/hash is missing")
            else:
                registered_path = _repo_file(root, entry["evidence_path"], "registered evidence", errors)
                if registered_path is not None:
                    if sha256_file(registered_path) != entry["evidence_sha256"]:
                        errors.append(f"{function}: registered evidence packet hash is stale")
                    if evidence_path is None or registered_path.resolve() != evidence_path.resolve():
                        errors.append(f"{function}: supplied packet is not the immutable registered packet")
        else:
            _validate_registry_target(root, function, registry_path, errors,
                                      allow_revision=allow_revision, evidence=evidence)
        if allow_registered:
            historical, hist_errors = _load_json(root / HISTORICAL_MANIFEST, "historical manifest")
            errors.extend(hist_errors)
            if isinstance(historical, dict) and any(
                    isinstance(claim, dict) and claim.get("name") == function
                    for module in historical.get("modules", {}).values() if isinstance(module, dict)
                    for claim in module.get("claims", [])):
                errors.append(f"{function}: historical EXACT manifest claim now exists; behavior status conflicts")

    source_hash = _pin_file(root, evidence.get("source"), "sha256", None, "source", errors)
    source_path = _repo_file(root, evidence.get("source", {}).get("path")
                              if isinstance(evidence.get("source"), dict) else None,
                              "source", errors)
    if not isinstance(evidence.get("source"), dict) or evidence.get("source", {}).get("whole_module") is not True:
        errors.append("source: whole_module must be true")
    if not isinstance(evidence.get("source", {}).get("module"), str) or not evidence["source"].get("module"):
        errors.append("source: module identity is required")

    suite = evidence.get("suite")
    suite_hash = _pin_file(root, suite, "sha256", None, "suite", errors)
    if isinstance(suite, dict):
        suite_path = suite.get("path", "")
        if not suite_path.startswith("tools/behavior_suites/"):
            errors.append("suite: must identify a source under tools/behavior_suites/")
        if not isinstance(suite.get("id"), str) or not suite.get("id"):
            errors.append("suite: id is required")

    harness = evidence.get("harness")
    if not isinstance(harness, dict):
        errors.append("harness: missing pin set")
        harness = {}
    runner_hash = _pin_file(root, harness.get("runner"), "sha256", None, "harness runner", errors)
    runner_pin = harness.get("runner") if isinstance(harness.get("runner"), dict) else {}
    runner_path = runner_pin.get("path")
    archived_runner = isinstance(runner_path, str) and runner_path != RUNNER
    runner_snapshot_id = None
    if runner_path != RUNNER and not (isinstance(runner_path, str) and re.fullmatch(
            r"evidence/behavior/harnesses/[A-Za-z0-9._-]+/tools/behavior\.py", runner_path)):
        errors.append("harness runner must be tools/behavior.py or a retained evidence/behavior/harnesses/<id>/tools/behavior.py snapshot")
    elif archived_runner:
        runner_snapshot_id = runner_path.split("/")[3]
    current_runner_hash = sha256_file(root / RUNNER) if (root / RUNNER).is_file() else None
    if runner_path == RUNNER and runner_hash != current_runner_hash:
        errors.append("current harness runner SHA-256 is stale")
    component_pins = harness.get("components")
    if not isinstance(component_pins, dict) or set(component_pins) != set(HARNESS_COMPONENTS):
        errors.append("harness: components must pin exactly the execution dependencies listed by behavior_validate.py")
        component_pins = component_pins if isinstance(component_pins, dict) else {}
    archived_components = []
    archived_snapshot_ids = set()
    for rel in HARNESS_COMPONENTS:
        pin = component_pins.get(rel)
        pin_path = pin.get("path") if isinstance(pin, dict) else None
        if pin_path != rel:
            match_snapshot = re.fullmatch(r"evidence/behavior/harnesses/([A-Za-z0-9._-]+)/" + re.escape(rel), pin_path) if isinstance(pin_path, str) else None
            expected_archived = match_snapshot is not None
            if not expected_archived:
                errors.append(f"harness component {rel}: must be current {rel} or archived at its matching path in evidence/behavior/harnesses/<id>/")
            else:
                archived_snapshot_ids.add(match_snapshot.group(1))
                archived_components.append({"component": rel, "path": pin_path,
                                            "sha256": pin.get("sha256")})
        _pin_file(root, pin, "sha256", pin_path, f"harness component {rel}", errors)
        if pin_path == rel:
            current_component_hash = sha256_file(root / rel) if (root / rel).is_file() else None
            if isinstance(pin, dict) and pin.get("sha256") != current_component_hash:
                errors.append(f"harness component {rel}: current file hash is stale")
    if archived_runner or archived_components:
        if runner_snapshot_id and archived_snapshot_ids - {runner_snapshot_id}:
            errors.append("archived runner and component files must come from the same harness snapshot bundle")
        if not runner_snapshot_id and len(archived_snapshot_ids) > 1:
            errors.append("archived harness components must come from one snapshot bundle")
        _validate_snapshot_review(harness.get("runner_snapshot_review"), archived_runner,
                                  archived_components, errors)

    oracle = evidence.get("oracle")
    oracle_hash = _pin_file(root, oracle, "sha256", "assets/SIMANT.EXE", "oracle executable", errors)
    lock_path = root / ORACLE_LOCK
    if not lock_path.is_file():
        errors.append("oracle lock file missing")
        lock_hash = None
    else:
        lock_hash = sha256_file(lock_path)
        if not isinstance(oracle, dict) or oracle.get("lock_sha256") != lock_hash:
            errors.append("oracle: stale or missing oracle-lock SHA-256")
        lock, lock_errors = _load_json(lock_path, "oracle lock")
        errors.extend(lock_errors)
        locked = lock.get("executable", {}).get("sha256") if isinstance(lock, dict) else None
        if oracle_hash != locked:
            errors.append("oracle: executable hash does not match layout/oracle.lock.json")

    manifest_path = root / HISTORICAL_MANIFEST
    manifest_hash = sha256_file(manifest_path) if manifest_path.is_file() else None
    if manifest_hash is None:
        errors.append("historical manifest missing")
    if evidence.get("historical_manifest_sha256") != manifest_hash:
        errors.append("historical manifest SHA-256 is stale or missing")

    checkpoint = evidence.get("checkpoint")
    if not isinstance(checkpoint, dict) or not isinstance(checkpoint.get("commit"), str) or not HEX40.fullmatch(checkpoint.get("commit", "")):
        errors.append("checkpoint: full 40-character source commit is required")
    if not isinstance(checkpoint, dict) or not isinstance(checkpoint.get("date"), str):
        errors.append("checkpoint: ISO date is required")
    else:
        try:
            date.fromisoformat(checkpoint["date"])
        except ValueError:
            errors.append("checkpoint: date must be ISO YYYY-MM-DD")

    contract = evidence.get("contract")
    if not isinstance(contract, dict):
        errors.append("contract: missing reviewed contract")
        contract = {}
    for field in ("id", "input_domain", "limits"):
        if not contract.get(field):
            errors.append(f"contract: {field} is required")
    if not isinstance(contract.get("input_domain"), (dict, list, str)) or contract.get("input_domain") in ({}, [], ""):
        errors.append("contract.input_domain must describe a non-empty tested domain")
    if not isinstance(contract.get("limits"), (list, str)) or not contract.get("limits"):
        errors.append("contract.limits must state proof limitations")
    required_effects = _nonempty_strings(contract.get("required_effects"), "contract.required_effects", errors)
    excluded = contract.get("excluded_effects")
    if not isinstance(excluded, list) or any(not isinstance(x, dict) or not x.get("effect") or not x.get("reason") for x in excluded):
        errors.append("contract.excluded_effects must explain every excluded observable effect")
    review = contract.get("review")
    if not isinstance(review, dict) or review.get("status") != "APPROVED" or not review.get("reviewer") or not review.get("reviewed_at"):
        errors.append("contract: supervisor review must be APPROVED with reviewer and date")

    run_ref = evidence.get("run_report")
    report_hash = _pin_file(root, run_ref, "sha256", None, "run report", errors)
    run_report = None
    if isinstance(run_ref, dict):
        report_path = _repo_file(root, run_ref.get("path"), "run report", errors)
        if report_path:
            run_report, report_errors = _load_json(report_path, "run report")
            errors.extend(report_errors)
    if not isinstance(run_report, dict) or run_report.get("schema") != "behavior-run-evidence-v1":
        errors.append("run report: unsupported or missing behavior-run-evidence-v1 schema")
        run_report = {}
    identity = run_report.get("identity", {}) if isinstance(run_report.get("identity"), dict) else {}
    for field, expected in (("function", function), ("suite_id", suite.get("id") if isinstance(suite, dict) else None),
                            ("source_sha256", source_hash), ("suite_sha256", suite_hash),
                            ("harness_sha256", runner_hash), ("oracle_sha256", oracle_hash),
                            ("historical_manifest_sha256", manifest_hash)):
        if identity.get(field) != expected:
            errors.append(f"run report identity.{field} does not match current pinned evidence")
    if not identity.get("object_sha256") or not HEX64.fullmatch(str(identity.get("object_sha256"))):
        errors.append("run report identity.object_sha256 is required")
    if not isinstance(identity.get("profile"), str) or not identity.get("profile"):
        errors.append("run report must pin the historical compiler profile")
    if not isinstance(identity.get("flags"), list) or not identity.get("flags"):
        errors.append("run report must pin the actual compiler flags")
    source_record = evidence.get("source", {})
    if identity.get("module") != source_record.get("module"):
        errors.append("run report identity.module does not match the whole-module source")
    if allow_revision:
        revision = evidence.get("revision")
        previous = revision.get("previous_evidence") if isinstance(revision, dict) else None
        old_path = _repo_file(root, previous.get("path") if isinstance(previous, dict) else None,
                              "revision predecessor", errors)
        old_packet, old_errors = _load_json(old_path, "revision predecessor") if old_path else (None, [])
        errors.extend(old_errors)
        old_source = old_packet.get("source", {}) if isinstance(old_packet, dict) else {}
        if isinstance(old_source, dict) and old_source.get("sha256") != source_hash:
            review = revision.get("source_change_review") if isinstance(revision, dict) else None
            if not isinstance(review, dict) or review.get("status") != "APPROVED" or review.get("reviewer") != "root" or not review.get("reviewed_at") or not review.get("reason"):
                errors.append("revision changes the reconstructed source and requires explicit root review of that source change")
    sequence_targets = identity.get("sequence_targets", [])
    if (not isinstance(sequence_targets, list)
            or any(not isinstance(name, str) or not name for name in sequence_targets)
            or sequence_targets != sorted(set(sequence_targets))):
        errors.append("run report identity.sequence_targets must be a sorted unique list of function names")
        sequence_targets = []
    compile_audit = (_compile_candidate(function, source_path, sequence_targets)
                     if source_path is not None else {"ok": False})
    canonical_address = compile_audit.get("address")
    address_keys = ("unit", "seg", "off", "size")
    if (not isinstance(canonical_address, dict)
            or not isinstance(canonical_address.get("unit"), str)
            or not canonical_address.get("unit")
            or any(not isinstance(canonical_address.get(key), int)
                   or isinstance(canonical_address.get(key), bool)
                   or canonical_address[key] < 0 for key in ("seg", "off", "size"))):
        errors.append("fresh whole-module compilation did not resolve a canonical function address")
        canonical_address = None
    report_address = identity.get("address")
    if report_address is not None and report_address != canonical_address:
        errors.append("run report identity.address does not match the fresh compiled function target")
    if compile_audit.get("ok") is not True:
        errors.append(compile_audit.get("error", "whole-module compiler replay did not succeed"))
    else:
        for field, actual in (("object_sha256", compile_audit.get("object_sha256")),
                              ("compiled_source_sha256", compile_audit.get("compiled_source_sha256")),
                              ("profile", compile_audit.get("profile")),
                              ("flags", compile_audit.get("flags"))):
            if identity.get(field) != actual:
                errors.append(f"run report identity.{field} does not match fresh whole-module compilation")
        if identity.get("sequence_targets", []) != compile_audit.get("sequence_targets", []):
            errors.append("run report identity.sequence_targets does not match fresh whole-module compilation")
        if compile_audit.get("peer_data_gates") != "PASS":
            errors.append("fresh whole-module peer/private-data verification did not pass")
    if run_report.get("completion") != "COMPLETE":
        errors.append("run report is not complete")
    execution = run_report.get("execution", {})
    engine = execution.get("engine") if isinstance(execution, dict) else None
    sequence_plan = None
    if engine == "PreparedPair.compare_sequence":
        if not sequence_targets or function not in sequence_targets:
            errors.append("compare_sequence requires non-empty identity.sequence_targets containing the evidence target")
        sequence_plan = _validate_sequence_campaign(root, run_report.get("sequence_campaign"), errors)
    elif engine != "PreparedPair.compare":
        errors.append("run report must identify PreparedPair.compare or a pinned PreparedPair.compare_sequence campaign")
    if not isinstance(execution, dict) or execution.get("actual_original_execution") is not True or execution.get("actual_candidate_execution") is not True:
        errors.append("run report must attest actual original DOS and candidate execution")
    if not isinstance(execution, dict) or execution.get("original_exe_sha256") != oracle_hash:
        errors.append("run report does not attest execution of the pinned original EXE")
    cases = run_report.get("cases", {})
    if not isinstance(cases, dict):
        errors.append("run report cases object is missing")
        cases = {}
    total_run = 0
    for lane in ("directed", "randomized"):
        lane_data = cases.get(lane)
        if not isinstance(lane_data, dict):
            errors.append(f"run report cases.{lane} is required")
            continue
        generated, executed = lane_data.get("generated"), lane_data.get("executed")
        if not isinstance(generated, int) or not isinstance(executed, int) or generated < 0 or executed < 0:
            errors.append(f"run report cases.{lane}: generated/executed must be non-negative integers")
            continue
        if generated != executed:
            errors.append(f"run report cases.{lane}: incomplete run ({executed}/{generated})")
        if lane == "directed" and generated == 0:
            errors.append("run report: at least one directed case is required")
        if lane == "randomized" and generated > 0 and not lane_data.get("seeds"):
            errors.append("run report: randomized cases require recorded seed(s)")
        if lane_data.get("actual_original_invocations") != executed or lane_data.get("actual_candidate_invocations") != executed:
            errors.append(f"run report cases.{lane}: original/candidate invocation count does not equal executed cases")
        total_run += executed
    if not isinstance(run_report.get("errors"), int) or run_report.get("errors") != 0:
        errors.append("run report must have zero execution errors")
    if not isinstance(run_report.get("mismatches"), int) or run_report.get("mismatches") != 0:
        errors.append("run report must have zero mismatches")
    compared = run_report.get("compared_effects")
    if not isinstance(compared, list) or not set(required_effects).issubset(set(compared)):
        errors.append("run report does not compare every contract.required_effects item")
    if run_report.get("unmodeled_boundaries") != 0:
        errors.append("run report must have zero unmodeled boundaries")
    if run_report.get("peer_data_gates") != "PASS":
        errors.append("run report whole-module peer/private-data gate must be PASS")

    approved_views = _validate_implementation_view_pins(
        root, contract, run_report, oracle_hash, errors)
    case_ledger = run_report.get("case_ledger")
    ledger_result = _validate_case_ledger(root, case_ledger, total_run, required_effects, errors,
                                          expected_identity=identity,
                                          approved_views=approved_views,
                                          sequence_plan=sequence_plan if engine == "PreparedPair.compare_sequence" else None)
    ledger_rows = ledger_result.get("lane_counts") if isinstance(ledger_result, dict) else None
    ledger_address = ledger_result.get("identity", {}).get("address") if isinstance(ledger_result, dict) else None
    if ledger_address is not None and ledger_address != canonical_address:
        errors.append("case ledger identity.address does not match the fresh compiled function target")
    if report_address is None and ledger_address is None:
        errors.append("run report or case ledger must pin the canonical target address")
    if ledger_rows is not None:
        for lane in ("directed", "randomized"):
            expected = cases.get(lane, {}).get("executed", 0) if isinstance(cases.get(lane), dict) else 0
            actual = ledger_rows.get(lane, 0)
            if actual != expected:
                errors.append(f"case ledger {lane} rows do not match executed count")

    helper_specs = contract.get("required_helpers", [])
    if not isinstance(helper_specs, list) or any(not isinstance(x, dict) or not x.get("name") for x in helper_specs):
        errors.append("contract.required_helpers must list each helper boundary by name")
        helper_specs = []
    helpers = run_report.get("helper_boundaries")
    if not isinstance(helpers, list):
        errors.append("run report helper_boundaries is required")
        helpers = []
    required_names = {h["name"] for h in helper_specs}
    helper_rows = {h.get("name"): h for h in helpers if isinstance(h, dict) and isinstance(h.get("name"), str)}
    if set(helper_rows) != required_names:
        errors.append("run report helper boundaries do not exactly cover contract.required_helpers")
    negative = evidence.get("negative_controls")
    neg_controls, neg_ids = _validate_negative_controls(
        root, negative, function, suite.get("id") if isinstance(suite, dict) else None,
        {"source_sha256": source_hash, "oracle_sha256": oracle_hash,
         "harness_sha256": runner_hash, "historical_manifest_sha256": manifest_hash}, errors)
    positive = run_report.get("positive_controls")
    positive_ids: set[str] = set()
    if not isinstance(positive, list) or not positive:
        errors.append("run report must include executed positive controls")
        positive = []
    for control in positive:
        if not isinstance(control, dict) or not isinstance(control.get("id"), str):
            errors.append("positive control is missing id")
            continue
        positive_ids.add(control["id"])
        if (control.get("executed") is not True or control.get("matched") is not True
                or control.get("original_executed") is not True
                or control.get("candidate_executed") is not True
                or control.get("execution_errors", 0) != 0
                or control.get("source_sha256") != source_hash
                or control.get("object_sha256") != identity.get("object_sha256")
                or control.get("oracle_sha256") != oracle_hash
                or not set(required_effects).issubset(set(control.get("compared_effects", [])))
                or not HEX64.fullmatch(str(control.get("original_observation_sha256", "")))
                or not HEX64.fullmatch(str(control.get("candidate_observation_sha256", "")))
                or control.get("original_observation_sha256") != control.get("candidate_observation_sha256")):
            errors.append(f"positive control {control['id']}: did not execute and match cleanly")
    for spec in helper_specs:
        name = spec["name"]
        row = helper_rows.get(name)
        if not row:
            continue
        if not isinstance(row.get("observed_call_count"), int) or row["observed_call_count"] < 0:
            errors.append(f"helper {name}: observed_call_count must be recorded")
        if spec.get("must_execute") is True and not (row.get("observed_call_count", 0) > 0):
            errors.append(f"helper {name}: required test domain did not execute this helper")
        mode = row.get("execution_mode")
        if mode not in ("ORIGINAL_EXE", "MODELED", "TRACE_ONLY"):
            errors.append(f"helper {name}: unknown execution_mode")
        if mode == "ORIGINAL_EXE" and row.get("executed_from_original") is not True:
            errors.append(f"helper {name}: ORIGINAL_EXE mode lacks original-execution evidence")
        if mode in ("MODELED", "TRACE_ONLY"):
            if function in SIMULATION_FUNCTIONS and row.get("certification") is None:
                errors.append(f"simulation helper {name}: modeled/trace boundary is uncertified")
            _validate_helper_cert(root, name, row.get("certification"), positive_ids, neg_ids, errors)

    historical = evidence.get("historical_difference")
    if not isinstance(historical, dict):
        errors.append("historical_difference: required")
    else:
        for field in ("description", "reason_exact_stopped", "evidence_refs"):
            if not historical.get(field):
                errors.append(f"historical_difference.{field} is required")
    semantic = evidence.get("semantic_evidence")
    if not isinstance(semantic, list) or not semantic:
        errors.append("semantic_evidence must contain at least one reviewed source/evidence reference")
    if not evidence.get("evidence_date"):
        errors.append("evidence_date is required")
    else:
        try:
            date.fromisoformat(evidence["evidence_date"])
        except (TypeError, ValueError):
            errors.append("evidence_date must be ISO YYYY-MM-DD")

    return {
        "schema": "simant-behavior-validation-v1", "valid": not errors,
        "function": function, "status": "BEHAVIOR_EXACT" if not errors else "UNRESOLVED",
        "function_address": canonical_address,
        "evidence_sha256": sha256_bytes(json.dumps(evidence, sort_keys=True, separators=(",", ":")).encode("utf-8")),
        "file_pins": {"source": source_hash, "suite": suite_hash, "harness": runner_hash,
                      "oracle": oracle_hash, "oracle_lock": lock_hash,
                      "historical_manifest": manifest_hash, "run_report": report_hash},
        "cases_executed": total_run, "errors": errors,
    }


def _validate_negative_controls(root: Path, record: Any, function: str,
                                suite_id: str | None, expected_identity: dict,
                                errors: list[str]) -> tuple[dict, set[str]]:
    if not isinstance(record, dict):
        errors.append("negative_controls: required")
        return {}, set()
    path = _repo_file(root, record.get("path"), "negative-controls report", errors)
    digest = record.get("sha256")
    if path is None or not isinstance(digest, str) or not HEX64.fullmatch(digest):
        errors.append("negative_controls: valid path and sha256 are required")
        return {}, set()
    actual = sha256_file(path)
    if digest != actual:
        errors.append("negative_controls: stale SHA-256")
    report, load_errors = _load_json(path, "negative-controls report")
    errors.extend(load_errors)
    if not isinstance(report, dict) or report.get("schema") != "behavior-negative-controls-v1":
        errors.append("negative-controls report schema is invalid")
        return {}, set()
    if report.get("function") != function or report.get("suite_id") != suite_id:
        errors.append("negative-controls report does not identify this function and suite")
    ident = report.get("identity")
    if not isinstance(ident, dict):
        errors.append("negative-controls report identity pins are required")
        ident = {}
    for field in ("source_sha256", "oracle_sha256", "harness_sha256", "historical_manifest_sha256"):
        value = ident.get(field)
        if not isinstance(value, str) or not HEX64.fullmatch(value):
            errors.append(f"negative-controls report identity.{field} is required")
        elif value != expected_identity.get(field):
            errors.append(f"negative-controls report identity.{field} does not match evidence pins")
    controls = report.get("controls")
    if not isinstance(controls, list) or not controls:
        errors.append("negative-controls report has no executed controls")
        controls = []
    ids: set[str] = set()
    for control in controls:
        if not isinstance(control, dict) or not isinstance(control.get("id"), str):
            errors.append("negative control is missing id")
            continue
        ids.add(control["id"])
        if (control.get("executed") is not True or control.get("detected_mismatch") is not True
                or control.get("original_executed") is not True or control.get("mutant_executed") is not True
                or control.get("baseline_matches") is not True or control.get("mutant_differs") is not True):
            errors.append(f"negative control {control['id']}: expected mutant mismatch was not detected")
        if control.get("execution_errors", 0) != 0:
            errors.append(f"negative control {control['id']}: execution error")
        if not control.get("mismatch_categories"):
            errors.append(f"negative control {control['id']}: detected difference needs a category")
        if not HEX64.fullmatch(str(control.get("mutant_source_sha256", ""))):
            errors.append(f"negative control {control['id']}: mutant source hash is required")
        for prefix in ("mutant_source", "mutant_object"):
            pin = control.get(prefix)
            pin_path = _repo_file(root, pin.get("path") if isinstance(pin, dict) else None,
                                  f"negative control {control['id']} {prefix}", errors)
            pin_hash = pin.get("sha256") if isinstance(pin, dict) else None
            if pin_path is None or not isinstance(pin_hash, str) or not HEX64.fullmatch(pin_hash):
                errors.append(f"negative control {control['id']}: {prefix} path/hash is required")
            elif sha256_file(pin_path) != pin_hash:
                errors.append(f"negative control {control['id']}: {prefix} hash is stale")
            elif prefix == "mutant_source" and pin_hash != control.get("mutant_source_sha256"):
                errors.append(f"negative control {control['id']}: mutant source identity hash disagrees")
    if report.get("errors") != 0 or report.get("mismatches_detected") != len(controls):
        errors.append("negative-controls report counts are incomplete or inconsistent")
    return report, ids


def _validate_snapshot_review(review: Any, archived_runner: bool,
                              archived_components: list[dict], errors: list[str]) -> None:
    if not isinstance(review, dict) or review.get("status") != "APPROVED":
        errors.append("archived harness inputs require an explicitly approved runner_snapshot_review")
        return
    if not review.get("reviewer") or not review.get("reason"):
        errors.append("runner_snapshot_review requires reviewer and relevance reason")
    try:
        date.fromisoformat(review.get("reviewed_at", ""))
    except (TypeError, ValueError):
        errors.append("runner_snapshot_review.reviewed_at must be an ISO date")
    if archived_runner and review.get("runner_snapshot_reviewed") is not True:
        errors.append("runner_snapshot_review must explicitly review the retained imported runner snapshot")
    reviewed_components = review.get("archived_components", [])
    if not isinstance(reviewed_components, list):
        errors.append("runner_snapshot_review.archived_components must be a list")
        reviewed_components = []
    actual = {(x.get("component"), x.get("path"), x.get("sha256")) for x in archived_components}
    claimed = {(x.get("component"), x.get("path"), x.get("sha256"))
               for x in reviewed_components if isinstance(x, dict)}
    if actual != claimed:
        errors.append("runner_snapshot_review does not cover the exact archived harness component pins")


def _validate_sequence_campaign(root: Path, campaign: Any, errors: list[str]) -> dict[int, set[str]] | None:
    """Load a pinned ordered call plan for genuine compare_sequence evidence."""
    if not isinstance(campaign, dict):
        errors.append("compare_sequence requires a sequence_campaign pin")
        return None
    path_text = campaign.get("ordered_plan_path")
    path = _repo_file(root, path_text, "sequence campaign ordered plan", errors)
    expected_hash = campaign.get("ordered_plan_sha256")
    if not isinstance(expected_hash, str) or not HEX64.fullmatch(expected_hash):
        errors.append("sequence campaign ordered_plan_sha256 must be a SHA-256")
        return None
    if path is None:
        return None
    if sha256_file(path) != expected_hash:
        errors.append("sequence campaign ordered plan SHA-256 is stale")
        return None
    plan, plan_errors = _load_json(path, "sequence campaign ordered plan")
    errors.extend(plan_errors)
    steps = plan.get("steps") if isinstance(plan, dict) else None
    if not isinstance(steps, list) or not steps:
        errors.append("sequence campaign ordered plan must contain non-empty steps")
        return None
    permitted: dict[int, set[str]] = {}
    for ordinal, step in enumerate(steps):
        if not isinstance(step, dict) or step.get("index") != ordinal:
            errors.append("sequence campaign steps must have unique contiguous zero-based indexes")
            return None
        entry = step.get("entry")
        if not isinstance(entry, str) or not entry.strip():
            errors.append(f"sequence campaign step {ordinal} lacks an entry")
            return None
        # The checked-in memory sequence plan uses a literal " or " only for
        # the first alternative entry. Do not interpret general expressions.
        names = {name.strip() for name in entry.split(" or ")}
        if any(not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name) for name in names):
            errors.append(f"sequence campaign step {ordinal} has an invalid entry name")
            return None
        permitted[ordinal] = names
    return permitted


def _validate_case_ledger(root: Path, ref: Any, expected_rows: int,
                          required_effects: list[str], errors: list[str],
                          expected_identity: dict | None = None,
                          approved_views: list[dict] | None = None,
                          sequence_plan: dict[int, set[str]] | None = None) -> dict[str, Any] | None:
    if not isinstance(ref, dict):
        errors.append("run report case_ledger is required to audit every original/candidate invocation")
        return None
    path = _repo_file(root, ref.get("path"), "case ledger", errors)
    expected_hash = ref.get("sha256")
    if path is None or not isinstance(expected_hash, str) or not HEX64.fullmatch(expected_hash):
        errors.append("case ledger requires a valid path and SHA-256")
        return None
    if sha256_file(path) != expected_hash:
        errors.append("case ledger SHA-256 is stale")
        return None
    compression = "gzip" if path.name.endswith(".gz") else "none"
    if ref.get("compression") != compression:
        errors.append("case ledger compression declaration does not match its file")
    ledger_identity = ref.get("identity")
    if not isinstance(ledger_identity, dict):
        errors.append("case ledger identity pins are required")
        ledger_identity = {}
    if expected_identity:
        pairs = (("function", "function"), ("source_sha256", "source_sha256"),
                 ("object_sha256", "object_sha256"), ("oracle_sha256", "oracle_sha256"),
                 ("harness_sha256", "harness_sha256"),
                 ("manifest_sha256", "historical_manifest_sha256"))
        for ledger_key, report_key in pairs:
            if ledger_identity.get(ledger_key) != expected_identity.get(report_key):
                errors.append(f"case ledger identity.{ledger_key} does not match run identity")
        if ledger_identity.get("sequence_targets", []) != expected_identity.get("sequence_targets", []):
            errors.append("case ledger identity.sequence_targets does not match run identity")
    seen: set[str] = set()
    seen_sequence_steps: set[tuple[str, int]] = set()
    lane_counts = {"directed": 0, "randomized": 0}
    approved_by_key = {(v.get("name"), v.get("address")): v
                       for v in (approved_views or []) if isinstance(v, dict)}
    seen_view_keys: set[tuple] = set()
    row_count = 0
    try:
        opener = gzip.open if path.name.endswith(".gz") else open
        with opener(path, "rt", encoding="utf-8") as stream:
            for line_no, line in enumerate(stream, 1):
                if not line.strip():
                    errors.append(f"case ledger line {line_no}: blank lines are not allowed")
                    continue
                row = json.loads(line)
                if not isinstance(row, dict):
                    errors.append(f"case ledger line {line_no}: row must be an object")
                    continue
                row_count += 1
                case_id = row.get("case_id")
                if not isinstance(case_id, str) or not case_id or case_id in seen:
                    errors.append(f"case ledger line {line_no}: missing or duplicate case_id")
                else:
                    seen.add(case_id)
                if sequence_plan is not None:
                    match = re.fullmatch(r"(?P<sequence>.+)/(?P<index>\d{2})-(?P<function>[A-Za-z_][A-Za-z0-9_]*)", case_id or "")
                    if match is None:
                        errors.append(f"case ledger line {line_no}: compare_sequence case_id must end in /NN-function")
                    else:
                        sequence_id = match.group("sequence")
                        step_index = int(match.group("index"))
                        step_function = match.group("function")
                        if expected_identity and step_function != expected_identity.get("function"):
                            errors.append(f"case ledger line {line_no}: sequence case_id target does not match run identity")
                        key = (sequence_id, step_index)
                        if key in seen_sequence_steps:
                            errors.append(f"case ledger line {line_no}: duplicate sequence_id/index")
                        seen_sequence_steps.add(key)
                        allowed = sequence_plan.get(step_index)
                        if allowed is None or step_function not in allowed:
                            errors.append(f"case ledger line {line_no}: case_id step does not match pinned ordered plan")
                lane = row.get("lane")
                if lane not in ("directed", "randomized"):
                    errors.append(f"case ledger line {line_no}: invalid lane")
                else:
                    lane_counts[lane] += 1
                if row.get("original_executed") is not True or row.get("candidate_executed") is not True:
                    errors.append(f"case ledger line {line_no}: both original and candidate must execute")
                if row.get("equal") is not True:
                    errors.append(f"case ledger line {line_no}: comparison did not pass")
                if row.get("original_observation_sha256") != row.get("candidate_observation_sha256"):
                    errors.append(f"case ledger line {line_no}: equal case has different normalized observation hashes")
                if not isinstance(row.get("input_sha256"), str) or not HEX64.fullmatch(row["input_sha256"]):
                    errors.append(f"case ledger line {line_no}: input_sha256 missing or malformed")
                effects = row.get("compared_effects")
                if not isinstance(effects, list) or not set(required_effects).issubset(set(effects)):
                    errors.append(f"case ledger line {line_no}: required effects were not compared")
                for field in ("original_observation_sha256", "candidate_observation_sha256"):
                    if not isinstance(row.get(field), str) or not HEX64.fullmatch(row[field]):
                        errors.append(f"case ledger line {line_no}: {field} missing or malformed")
                if expected_identity and row.get("function") != expected_identity.get("function"):
                    errors.append(f"case ledger line {line_no}: function does not match run identity")
                if expected_identity and row.get("oracle_sha256") != expected_identity.get("oracle_sha256"):
                    errors.append(f"case ledger line {line_no}: oracle does not match run identity")
                if "implementation_view_proofs" in row:
                    declared = row.get("implementation_view_proofs")
                    if not isinstance(declared, list) or not declared:
                        errors.append(f"case ledger line {line_no}: implementation_view_proofs must be a non-empty list")
                        declared = []
                    row_keys = set()
                    for view in declared:
                        if not isinstance(view, dict):
                            errors.append(f"case ledger line {line_no}: implementation view proof row must be an object")
                            continue
                        key = (view.get("name"), view.get("address"))
                        if key in row_keys:
                            errors.append(f"case ledger line {line_no}: duplicate implementation view")
                        row_keys.add(key)
                        approved = approved_by_key.get(key)
                        if approved is None or view != approved:
                            errors.append(f"case ledger line {line_no}: implementation view is undeclared or differs from approved contract pins")
                        else:
                            seen_view_keys.add(key)
                    if not all(isinstance(row.get(k), str) and HEX64.fullmatch(row[k])
                               for k in ("raw_original_observation_sha256", "raw_candidate_observation_sha256")):
                        errors.append(f"case ledger line {line_no}: raw implementation observation hashes are required")
                    if not isinstance(row.get("implementation_differences"), dict):
                        errors.append(f"case ledger line {line_no}: implementation_differences must be retained as an object")
                    semantic_views = row.get("private_formatter_views")
                    if not isinstance(semantic_views, dict):
                        errors.append(f"case ledger line {line_no}: private_formatter_views semantic effects are required")
                    else:
                        if not set(semantic_views).issubset({key[0] for key in row_keys}):
                            errors.append(f"case ledger line {line_no}: semantic formatter view is not declared for this case")
                        for name, semantic in semantic_views.items():
                            if (not isinstance(semantic, dict)
                                    or not isinstance(semantic.get("cursor_advance"), int)
                                    or not isinstance(semantic.get("remaining_capacity"), int)
                                    or semantic.get("cursor_advance", -1) < 0
                                    or semantic.get("remaining_capacity", -1) < 0
                                    or semantic.get("buffer_lifetime") != "private formatter invocation"):
                                errors.append(f"case ledger line {line_no}: {name} lacks typed cursor advancement/capacity effects")
                    differences = row.get("implementation_differences", {})
                    if isinstance(differences, dict) and not set(differences).issubset({"raw_nonstack_memory", "raw_effect_trace"}):
                        errors.append(f"case ledger line {line_no}: unexpected implementation difference category")
                    if isinstance(differences, dict) and "raw_effect_trace" in differences and not isinstance(differences["raw_effect_trace"], dict):
                        errors.append(f"case ledger line {line_no}: raw_effect_trace difference must retain both traces")
                    raw_memory = differences.get("raw_nonstack_memory", []) if isinstance(differences, dict) else []
                    if not isinstance(raw_memory, list):
                        errors.append(f"case ledger line {line_no}: raw_nonstack_memory differences must be a list")
                    else:
                        spans = [(v.get("address"), v.get("address", -1) + 10)
                                 for v in declared if isinstance(v, dict)
                                 and isinstance(v.get("address"), int) and not isinstance(v.get("address"), bool)]
                        for diff in raw_memory:
                            address = diff.get("address") if isinstance(diff, dict) else None
                            if (not isinstance(address, int) or isinstance(address, bool)
                                    or not any(lo <= address < hi for lo, hi in spans)):
                                errors.append(f"case ledger line {line_no}: raw memory difference lies outside approved implementation views")
                                break
                    raw_hashes = (row.get("raw_original_observation_sha256"),
                                  row.get("raw_candidate_observation_sha256"))
                    if ((raw_memory or (isinstance(differences, dict) and "raw_effect_trace" in differences))
                            and raw_hashes[0] == raw_hashes[1]):
                        errors.append(f"case ledger line {line_no}: raw implementation difference is not reflected by raw observation hashes")
                elif any(field in row for field in ("implementation_differences",
                                "raw_original_observation_sha256", "raw_candidate_observation_sha256",
                                "private_formatter_views")):
                    errors.append(f"case ledger line {line_no}: implementation differences lack an approved implementation view declaration")
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        errors.append(f"case ledger cannot be read: {exc}")
        return None
    if row_count != expected_rows or ref.get("row_count") != expected_rows:
        errors.append(f"case ledger row count {row_count} does not equal completed invocation count {expected_rows}")
    reported_lane_counts = ref.get("lane_counts")
    if not isinstance(reported_lane_counts, dict) or any(reported_lane_counts.get(lane) != lane_counts[lane]
                                                         for lane in ("directed", "randomized")):
        errors.append("case ledger lane_counts do not match its rows")
    if approved_by_key and seen_view_keys != set(approved_by_key):
        errors.append("case ledger does not exercise every approved implementation view")
    return {"lane_counts": lane_counts, "identity": ledger_identity}


def _validate_implementation_view_pins(root: Path, contract: dict, run_report: dict,
                                       oracle_hash: str | None, errors: list[str]) -> list[dict]:
    """Validate the narrowly reviewed format-cursor view contract, if present."""
    contract_views = contract.get("implementation_views", [])
    report_views = run_report.get("implementation_views", [])
    if not isinstance(contract_views, list):
        errors.append("contract.implementation_views must be a list")
        contract_views = []
    if not isinstance(report_views, list):
        errors.append("run report implementation_views must be a list")
        report_views = []
    if not contract_views and not report_views:
        return []
    review = contract.get("review")
    if (not isinstance(review, dict) or review.get("status") != "APPROVED"
            or review.get("reviewer") != "root" or not review.get("reviewed_at")):
        errors.append("implementation views require root-approved contract review")
    if contract_views != report_views:
        errors.append("run report implementation_views must exactly match approved contract pins")
    _validate_runtime_proof_graphs(root, review, contract_views, errors)
    required = {"name", "address", "proof_path", "proof_sha256"}
    keys = set()
    address_spans = []
    validated = []
    for index, view in enumerate(contract_views):
        label = f"implementation view {index + 1}"
        if not isinstance(view, dict) or set(view) != required:
            errors.append(f"{label}: requires exactly name, address, proof_path, and proof_sha256")
            continue
        name, address = view.get("name"), view.get("address")
        proof_path = view.get("proof_path")
        proof_hash = view.get("proof_sha256")
        if not isinstance(name, str) or not name:
            errors.append(f"{label}: name is required")
        if not isinstance(address, int) or isinstance(address, bool) or not 0 <= address <= 0xFFFFF - 10:
            errors.append(f"{label}: address must identify a 10-byte record in the real-mode linear range")
        key = (name, address)
        if key in keys:
            errors.append(f"{label}: duplicate name/address")
        keys.add(key)
        if isinstance(address, int) and not isinstance(address, bool):
            if any(address < high and address + 10 > low for low, high in address_spans):
                errors.append(f"{label}: formatter view overlaps another approved private record")
            address_spans.append((address, address + 10))
        if not isinstance(proof_path, str) or not proof_path.startswith("evidence/behavior/runtime/"):
            errors.append(f"{label}: proof must be retained under evidence/behavior/runtime/")
        proof_file = _repo_file(root, proof_path, f"{label} proof", errors)
        if not isinstance(proof_hash, str) or not HEX64.fullmatch(proof_hash):
            errors.append(f"{label}: proof SHA-256 is malformed")
        elif proof_file is not None and sha256_file(proof_file) != proof_hash:
            errors.append(f"{label}: proof SHA-256 is stale")
        if proof_file is None or not isinstance(proof_hash, str) or not HEX64.fullmatch(proof_hash):
            continue
        proof, proof_errors = _load_json(proof_file, f"{label} runtime proof")
        errors.extend(proof_errors)
        if not isinstance(proof, dict) or proof.get("schema") != "behavior-format-cursor-proof-v1":
            errors.append(f"{label}: runtime proof schema is invalid")
            continue
        proof_review = proof.get("review")
        if (not isinstance(proof_review, dict) or proof_review.get("status") != "APPROVED"
                or proof_review.get("reviewer") != "root" or not proof_review.get("reviewed_at")):
            errors.append(f"{label}: runtime proof lacks explicit root review")
        else:
            try:
                date.fromisoformat(proof_review["reviewed_at"])
            except (TypeError, ValueError):
                errors.append(f"{label}: runtime proof review date must be ISO YYYY-MM-DD")
        if proof.get("oracle_sha256") != oracle_hash:
            errors.append(f"{label}: runtime proof does not pin this original oracle")
        records = proof.get("records")
        match = next((record for record in records if isinstance(record, dict)
                      and record.get("name") == name and record.get("address") == address), None) if isinstance(records, list) else None
        if (match is None or match.get("size") != 10
                or match.get("private_owner") not in ("sprintf.c", "vsprintf.c")
                or match.get("overwrite_before_read_proven") is not True):
            errors.append(f"{label}: runtime proof does not establish the matching private 10-byte formatter record")
        if "audit" in proof:
            _validate_cursor_audit(root, proof, name, address, oracle_hash, label, errors)
        validated.append(view)
    return validated


def _validate_runtime_proof_graphs(root: Path, review: Any, views: list,
                                   errors: list[str]) -> None:
    """Require a reviewed, content-addressed replay graph for normalized views."""
    if not views:
        return
    rows = review.get("runtime_proof_graphs") if isinstance(review, dict) else None
    if not isinstance(rows, list) or not rows:
        errors.append("implementation views require reviewed runtime_proof_graphs pins")
        return
    expected = {(view.get("proof_path"), view.get("proof_sha256"))
                for view in views if isinstance(view, dict)}
    seen = set()
    for index, row in enumerate(rows):
        label = f"runtime proof graph {index + 1}"
        required = {"proof_path", "proof_sha256", "graph_path", "graph_sha256"}
        if not isinstance(row, dict) or set(row) != required:
            errors.append(f"{label}: requires exactly proof_path/proof_sha256/graph_path/graph_sha256")
            continue
        proof_key = (row.get("proof_path"), row.get("proof_sha256"))
        if proof_key not in expected:
            errors.append(f"{label}: does not correspond to a declared implementation view proof")
        if proof_key in seen:
            errors.append(f"{label}: duplicate proof graph pin")
        seen.add(proof_key)
        graph_path = _repo_file(root, row.get("graph_path"), f"{label} file", errors)
        graph_hash = row.get("graph_sha256")
        if not isinstance(graph_hash, str) or not HEX64.fullmatch(graph_hash):
            errors.append(f"{label}: graph SHA-256 is malformed")
        elif graph_path is not None and sha256_file(graph_path) != graph_hash:
            errors.append(f"{label}: graph SHA-256 is stale")
        if graph_path is None or not isinstance(graph_hash, str) or not HEX64.fullmatch(graph_hash):
            continue
        graph, graph_errors = _load_json(graph_path, label)
        errors.extend(graph_errors)
        if not isinstance(graph, dict) or graph.get("schema") != "behavior-runtime-proof-graph-v1":
            errors.append(f"{label}: unsupported schema")
            continue
        graph_review = graph.get("review")
        if (not isinstance(graph_review, dict) or graph_review.get("status") != "APPROVED"
                or graph_review.get("reviewer") != "root" or not graph_review.get("reason")):
            errors.append(f"{label}: explicit root review and reason are required")
        else:
            try:
                date.fromisoformat(graph_review.get("reviewed_at", ""))
            except (TypeError, ValueError):
                errors.append(f"{label}: review date must be ISO YYYY-MM-DD")
        proof_pin = graph.get("proof")
        if (not isinstance(proof_pin, dict)
                or proof_pin.get("path") != row.get("proof_path")
                or proof_pin.get("sha256") != row.get("proof_sha256")):
            errors.append(f"{label}: graph proof pin does not match the implementation-view certificate")
        inputs = graph.get("inputs")
        if not isinstance(inputs, list) or not inputs:
            errors.append(f"{label}: input dependency pins are required")
            continue
        roles = set()
        for input_index, pin in enumerate(inputs):
            input_label = f"{label} input {input_index + 1}"
            if not isinstance(pin, dict) or set(pin) != {"role", "path", "sha256"}:
                errors.append(f"{input_label}: requires exactly role/path/sha256")
                continue
            role = pin.get("role")
            if not isinstance(role, str) or not role.strip():
                errors.append(f"{input_label}: role is required")
            else:
                roles.add(role)
            _pin_file(root, pin, "sha256", None, input_label, errors)
        if not {"producer", "source", "suite", "runner", "component", "observation"}.issubset(roles):
            errors.append(f"{label}: graph must pin producer, source, suite, runner, component, and observation inputs")
    if seen != expected:
        errors.append("every implementation-view certificate must have exactly one reviewed proof graph pin")


def _validate_cursor_audit(root: Path, proof: dict, name: str, address: int,
                           oracle_hash: str | None, label: str, errors: list[str]) -> None:
    """Validate the reviewed cursor certificate's retained audit and replay inputs."""
    audit_ref = proof.get("audit")
    if not isinstance(audit_ref, dict) or set(audit_ref) != {"path", "sha256"}:
        errors.append(f"{label}: audit must pin a path and SHA-256")
        return
    audit_path = audit_ref.get("path")
    if not isinstance(audit_path, str) or not audit_path.startswith("evidence/behavior/runtime/"):
        errors.append(f"{label}: audit must be retained under evidence/behavior/runtime/")
    audit_file = _repo_file(root, audit_path, f"{label} audit", errors)
    audit_hash = audit_ref.get("sha256")
    if not isinstance(audit_hash, str) or not HEX64.fullmatch(audit_hash):
        errors.append(f"{label}: audit SHA-256 is malformed")
    elif audit_file is not None and sha256_file(audit_file) != audit_hash:
        errors.append(f"{label}: audit SHA-256 is stale")
    if audit_file is None or not isinstance(audit_hash, str) or not HEX64.fullmatch(audit_hash):
        return
    audit, load_errors = _load_json(audit_file, f"{label} audit")
    errors.extend(load_errors)
    if not isinstance(audit, dict) or audit.get("schema") != "runtime-format-cursor-audit-v1":
        errors.append(f"{label}: unsupported cursor audit schema")
        return
    if audit.get("oracle_sha256", audit.get("typed_view_proposal", {}).get("oracle_sha256")) != oracle_hash:
        errors.append(f"{label}: audit does not pin the original oracle")
    if audit.get("all_negative_controls_passed") is not True:
        errors.append(f"{label}: audit negative controls are incomplete or failed")
    proposal = audit.get("typed_view_proposal")
    if not isinstance(proposal, dict) or proposal.get("schema") != "behavior-format-cursor-proof-v1":
        errors.append(f"{label}: audit lacks its typed-view proposal")
        proposal = {}
    if proposal.get("oracle_sha256") != oracle_hash:
        errors.append(f"{label}: audit proposal oracle does not match")
    retained = audit.get("retained_raw_mismatch")
    dynamic = audit.get("dynamic_proof")
    vsdynamic = audit.get("vsprintf_dynamic_proof")
    if (not isinstance(retained, dict) or not isinstance(dynamic, dict)
            or not isinstance(vsdynamic, dict)):
        errors.append(f"{label}: audit lacks retained raw mismatch or dynamic proof records")
    else:
        digest_material = {
            "oracle_sha256": oracle_hash,
            "runtime_members": [audit.get("runtime_member"), audit.get("vsprintf_runtime_member")],
            "records": proposal.get("records", []),
            "sprintf_negative_control": dynamic.get("negative_control_passed"),
            "vsprintf_negative_control": vsdynamic.get("negative_control_passed"),
            "raw_diffs_preserved": retained.get("raw_nonstack_memory_differences"),
        }
        serialized = json.dumps(digest_material, sort_keys=True, separators=(",", ":")).encode("utf-8")
        if proposal.get("proof_digest") != sha256_bytes(serialized):
            errors.append(f"{label}: audit typed-view proof digest does not match its evidence records")
    audit_record = next((row for row in proposal.get("records", []) if isinstance(row, dict)
                         and row.get("name") == name and row.get("address") == address), None) \
        if isinstance(proposal.get("records"), list) else None
    proof_record = next((row for row in proof.get("records", []) if isinstance(row, dict)
                         and row.get("name") == name and row.get("address") == address), None) \
        if isinstance(proof.get("records"), list) else None
    if (audit_record is None or proof_record is None
            or audit_record.get("size") != 10 or proof_record.get("size") != 10
            or audit_record.get("overwrite_before_read_proven") is not True
            or proof_record.get("overwrite_before_read_proven") is not True
            or f"{proof_record.get('private_owner', '')}:" not in str(audit_record.get("private_owner", ""))):
        errors.append(f"{label}: certificate record is not corroborated by the pinned audit")
    # New certificates can pin their full reproduction graph. Older immutable
    # certificates remain valid based on their reviewed audit-byte pin; when
    # a graph is present, validate every leaf instead of trusting declarations.
    reproduction = audit.get("reproduction")
    required_roles = {"producer", "target_source", "suite", "harness_snapshot"}
    if reproduction is not None:
        if not isinstance(reproduction, dict) or set(reproduction) != required_roles | {"observations"}:
            errors.append(f"{label}: audit reproduction must pin producer/source/suite/harness_snapshot/observations")
            return
        for role in sorted(required_roles):
            _pin_file(root, reproduction.get(role), "sha256", None,
                      f"{label} audit {role}", errors)
        observations = reproduction.get("observations")
        if not isinstance(observations, list) or not observations:
            errors.append(f"{label}: audit reproduction must pin retained observations")
        else:
            for index, pin in enumerate(observations):
                _pin_file(root, pin, "sha256", None, f"{label} audit observation {index + 1}", errors)


def _validate_helper_cert(root: Path, name: str, cert: Any, positive_ids: set[str],
                          negative_ids: set[str], errors: list[str]) -> None:
    if not isinstance(cert, dict):
        errors.append(f"helper {name}: modeled/trace boundary requires a reviewed certification")
        return
    path = _repo_file(root, cert.get("path"), f"helper {name} certification", errors)
    digest = cert.get("sha256")
    if path is None or not isinstance(digest, str) or not HEX64.fullmatch(digest):
        errors.append(f"helper {name}: certification path/hash required")
        return
    if sha256_file(path) != digest:
        errors.append(f"helper {name}: stale certification hash")
    detail, load_errors = _load_json(path, f"helper {name} certification")
    errors.extend(load_errors)
    if not isinstance(detail, dict) or detail.get("schema") != "behavior-helper-cert-v1":
        errors.append(f"helper {name}: certification schema invalid")
        return
    if detail.get("helper") != name or detail.get("status") != "CERTIFIED":
        errors.append(f"helper {name}: certification identity/status invalid")
    review = detail.get("review")
    if not isinstance(review, dict) or review.get("status") != "APPROVED" or not review.get("reviewer") or not review.get("reviewed_at"):
        errors.append(f"helper {name}: certification lacks independent review")
    _nonempty_strings(detail.get("input_domain"), f"helper {name} certification input_domain", errors)
    _nonempty_strings(detail.get("compared_effects"), f"helper {name} certification compared_effects", errors)
    for field in ("positive_control_id", "negative_control_id", "limitations", "source_hashes"):
        if not detail.get(field):
            errors.append(f"helper {name}: certification missing {field}")
    if detail.get("positive_control_id") not in positive_ids:
        errors.append(f"helper {name}: certification positive control is not in the run report")
    if detail.get("negative_control_id") not in negative_ids:
        errors.append(f"helper {name}: certification negative control is not in the validated report")
    source_hashes = detail.get("source_hashes")
    if isinstance(source_hashes, dict):
        for rel, expected in source_hashes.items():
            path = _repo_file(root, rel, f"helper {name} source pin", errors)
            if not isinstance(expected, str) or not HEX64.fullmatch(expected):
                errors.append(f"helper {name}: malformed source hash for {rel}")
            elif path is not None and sha256_file(path) != expected:
                errors.append(f"helper {name}: stale source hash for {rel}")


def validation_receipt(result: dict, *, evidence_path: Path, registry_path: Path,
                       root: Path = ROOT) -> dict:
    if not result.get("valid"):
        raise ValueError("cannot create receipt for invalid evidence")
    return {
        "schema": "simant-behavior-validation-receipt-v1",
        "valid": True,
        "evidence_path": str(evidence_path.resolve().relative_to(root.resolve())).replace("\\", "/"),
        "evidence_file_sha256": sha256_file(evidence_path),
        "registry_sha256": sha256_file(registry_path),
        "validation": result,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evidence", type=Path, nargs="?")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--verify-only", action="store_true",
                      help="validate one unregistered packet without changing the registry")
    mode.add_argument("--all", action="store_true",
                      help="validate every registered behavior packet and print separate proof-category counts")
    parser.add_argument("--receipt", type=Path,
                        help="optional repository-local receipt for a later explicit registration")
    args = parser.parse_args(argv)
    if args.all:
        if args.evidence is not None or args.receipt:
            parser.error("--all does not take an evidence packet or receipt")
        registry, load_errors = _load_json(REGISTRY, "behavior registry")
        if load_errors or not isinstance(registry, dict):
            print(json.dumps({"valid": False, "errors": load_errors or ["invalid registry"]}, indent=2))
            return 1
        results = {}
        entries = registry.get("entries", {})
        if not isinstance(entries, dict):
            print(json.dumps({"valid": False, "errors": ["behavior registry entries must be an object"]}, indent=2))
            return 1
        for function, row in entries.items():
            if not isinstance(row, dict):
                results[function] = {"valid": False, "errors": ["registry row must be an object"]}
                continue
            if row.get("status") != "BEHAVIOR_EXACT":
                continue
            history_errors = _validate_revision_history(ROOT, row)
            packet_path = ROOT / row.get("evidence_path", "")
            packet, packet_errors = _load_json(packet_path, f"{function} evidence")
            if packet_errors:
                results[function] = {"valid": False, "errors": packet_errors}
                continue
            results[function] = validate_evidence(packet, allow_registered=True,
                                                   evidence_path=packet_path)
            if history_errors:
                results[function]["valid"] = False
                results[function].setdefault("errors", []).extend(history_errors)
        hist, hist_errors = _load_json(ROOT / HISTORICAL_MANIFEST, "historical manifest")
        funcs, func_errors = _load_json(ROOT / "layout/functions.json", "function inventory")
        game_functions = set()
        if isinstance(hist, dict):
            exact_claims = {(claim.get("unit"), claim.get("seg"), claim.get("off"), claim.get("size"))
                            for module in hist.get("modules", {}).values() if isinstance(module, dict)
                            for claim in module.get("claims", []) if isinstance(claim, dict)}
        else:
            exact_claims = set()
        if isinstance(funcs, dict):
            game_functions = {(fn.get("unit"), fn.get("seg"), fn.get("off"), fn.get("size"))
                              for fn in funcs.get("functions", []) if isinstance(fn, dict)
                              and fn.get("region") == "game_or_library"}
        exact_functions = exact_claims & game_functions
        behavior_addresses = set()
        for function, detail in results.items():
            if not detail.get("valid"):
                continue
            packet = json.loads((ROOT / entries[function]["evidence_path"]).read_text(encoding="utf-8"))
            report_path = ROOT / packet["run_report"]["path"]
            report = json.loads(report_path.read_text(encoding="utf-8"))
            address = detail.get("function_address")
            if not isinstance(address, dict):
                detail["valid"] = False
                detail.setdefault("errors", []).append("freshly validated function address is unavailable")
                continue
            key = (address.get("unit"), address.get("seg"), address.get("off"), address.get("size"))
            if key not in game_functions:
                detail["valid"] = False
                detail.setdefault("errors", []).append("registered behavior address is absent from the game function inventory")
                continue
            if key in exact_functions:
                detail["valid"] = False
                detail.setdefault("errors", []).append("behavior function address is already owned as EXACT")
                continue
            behavior_addresses.add(key)
        behavior_count = len(behavior_addresses)
        unresolved_count = len(game_functions - exact_functions - behavior_addresses)
        nonfunction_claims = len(exact_claims - game_functions)
        output = {"valid": not load_errors and not hist_errors and not func_errors and all(r.get("valid") for r in results.values()),
                  "categories": {"EXACT": len(exact_functions), "BEHAVIOR_EXACT": behavior_count,
                                 "UNRESOLVED": unresolved_count,
                                 "historical_nonfunction_claims": nonfunction_claims},
                  "registered_behavior": results, "errors": load_errors + hist_errors + func_errors}
        print(json.dumps(output, indent=2))
        return 0 if output["valid"] else 1
    if args.evidence is None:
        parser.error("--verify-only requires an evidence packet")
    evidence_path = args.evidence if args.evidence.is_absolute() else ROOT / args.evidence
    evidence, load_errors = _load_json(evidence_path, "evidence")
    if load_errors:
        print(json.dumps({"valid": False, "errors": load_errors}, indent=2))
        return 1
    result = validate_evidence(evidence)
    if result["valid"] and args.receipt:
        receipt_path = args.receipt if args.receipt.is_absolute() else ROOT / args.receipt
        try:
            receipt_path.resolve().relative_to(ROOT.resolve())
            receipt_path.parent.mkdir(parents=True, exist_ok=True)
            receipt_path.write_text(json.dumps(validation_receipt(result, evidence_path=evidence_path,
                                                                  registry_path=REGISTRY), indent=2) + "\n", encoding="utf-8")
        except (ValueError, OSError) as exc:
            result["valid"] = False
            result["errors"].append(f"cannot write repository-local receipt: {exc}")
    print(json.dumps(result, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
