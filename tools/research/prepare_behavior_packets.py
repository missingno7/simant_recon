#!/usr/bin/env python3
"""Package a root-approved batch of standard behavioral evidence proposals.

The adapter never approves semantics, verifies/registers claims, or edits the
behavior registry. Its manifest and each review file must already carry root
approval; outputs are immutable, unregistered packets under each function's
behavior evidence directory.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import behavior_packet
import behavior_validate as bv

SCHEMA = "behavior-review-package-batch-v1"
HEX64 = re.compile(r"^[0-9a-f]{64}$")


def repo_file(root: Path, pin: dict, label: str) -> Path:
    if not isinstance(pin, dict) or not isinstance(pin.get("path"), str):
        raise ValueError(f"{label}: repository path pin required")
    path = (root / pin["path"]).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(f"{label}: path escapes repository") from exc
    if not path.is_file():
        raise ValueError(f"{label}: file does not exist: {pin['path']}")
    digest = pin.get("sha256")
    if not isinstance(digest, str) or not HEX64.fullmatch(digest):
        raise ValueError(f"{label}: valid SHA-256 pin required")
    if bv.sha256_file(path) != digest:
        raise ValueError(f"{label}: stale SHA-256 for {pin['path']}")
    return path


def is_root(reviewer: object) -> bool:
    if not isinstance(reviewer, str):
        return False
    value = reviewer.strip().lower()
    return value == "root" or value.endswith("/root")


def approved(review: dict, label: str) -> None:
    """Require explicit root approval of the contract, never infer approval."""
    if review.get("status") not in (None, "APPROVED"):
        raise ValueError(f"{label}: review status is not APPROVED")
    contract = review.get("contract")
    contract_review = contract.get("review") if isinstance(contract, dict) else None
    if not isinstance(contract_review, dict) or contract_review.get("status") != "APPROVED":
        raise ValueError(f"{label}: contract.review must already be APPROVED")
    if not is_root(contract_review.get("reviewer")):
        raise ValueError(f"{label}: contract reviewer must be root")
    reviewed_at = contract_review.get("reviewed_at")
    try:
        date.fromisoformat(reviewed_at)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label}: contract review date must be ISO YYYY-MM-DD") from exc
    if review.get("reviewer") is not None and not is_root(review.get("reviewer")):
        raise ValueError(f"{label}: top-level reviewer conflicts with root approval")
    if "date" in review:
        try:
            date.fromisoformat(review["date"])
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{label}: packet date must be ISO YYYY-MM-DD") from exc


def preflight(root: Path, entry: dict) -> tuple[Path, Path, Path]:
    function = entry.get("function")
    if not isinstance(function, str) or not function:
        raise ValueError("batch entry requires a function name")
    review_path = repo_file(root, entry.get("review"), f"{function} review")
    run_path = repo_file(root, entry.get("run"), f"{function} run")
    review = json.loads(review_path.read_text(encoding="utf-8"))
    run = json.loads(run_path.read_text(encoding="utf-8"))
    if review.get("function") != function:
        raise ValueError(f"{function}: approved review names another function")
    approved(review, function)
    if not isinstance(review.get("source"), str) or not isinstance(review.get("suite"), str):
        raise ValueError(f"{function}: normalized approved review must name source and suite as paths")
    if run.get("schema") != "behavior-run-evidence-v1" or run.get("completion") != "COMPLETE":
        raise ValueError(f"{function}: run must be a complete behavior-run-evidence-v1 report")
    identity = run.get("identity")
    if not isinstance(identity, dict) or identity.get("function") != function:
        raise ValueError(f"{function}: run identity does not name the batch function")
    if run.get("errors") != 0 or run.get("mismatches") != 0:
        raise ValueError(f"{function}: run has errors or mismatches")
    source_path = (root / review["source"]).resolve()
    suite_path = (root / review["suite"]).resolve()
    for path, label in ((source_path, "source"), (suite_path, "suite")):
        try:
            path.relative_to(root.resolve())
        except ValueError as exc:
            raise ValueError(f"{function}: {label} path escapes repository") from exc
        if not path.is_file():
            raise ValueError(f"{function}: {label} file is missing")
    suite_rel = suite_path.relative_to(root.resolve()).as_posix()
    if not (suite_rel.startswith("tools/behavior_suites/")
            or suite_rel.startswith("evidence/behavior/")):
        raise ValueError(f"{function}: suite must be archived in tools/behavior_suites or evidence/behavior")
    if bv.sha256_file(source_path) != identity.get("source_sha256"):
        raise ValueError(f"{function}: approved source differs from run identity")
    if bv.sha256_file(suite_path) != identity.get("suite_sha256"):
        raise ValueError(f"{function}: approved suite differs from run identity")
    ledger = run.get("case_ledger")
    if not isinstance(ledger, dict) or not isinstance(ledger.get("path"), str):
        raise ValueError(f"{function}: complete run must pin its per-case ledger")
    ledger_path = Path(ledger["path"])
    if not ledger_path.is_absolute():
        candidate = root / ledger_path
        ledger_path = candidate if candidate.is_file() else run_path.parent / ledger_path
    ledger_path = ledger_path.resolve()
    try:
        ledger_path.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(f"{function}: ledger path escapes repository") from exc
    if not ledger_path.is_file() or bv.sha256_file(ledger_path) != ledger.get("sha256"):
        raise ValueError(f"{function}: per-case ledger is missing or stale")
    ledger_identity = ledger.get("identity")
    if not isinstance(ledger_identity, dict):
        raise ValueError(f"{function}: per-case ledger identity is absent")
    for key in ("source_sha256", "object_sha256", "oracle_sha256", "harness_sha256", "manifest_sha256"):
        # Standard reports spell this pin historical_manifest_sha256; raw
        # PreparedPair identities and ledgers spell it manifest_sha256.
        report_value = identity.get(key)
        if key == "manifest_sha256" and report_value is None:
            report_value = identity.get("historical_manifest_sha256")
        if ledger_identity.get(key) != report_value:
            raise ValueError(f"{function}: per-case ledger identity.{key} differs from run identity")
    negative = review.get("negative_controls")
    if isinstance(negative, str):
        negpath = (root / negative).resolve()
        try:
            negpath.relative_to(root.resolve())
        except ValueError as exc:
            raise ValueError(f"{function}: negative-control path escapes repository") from exc
        if not negpath.is_file():
            raise ValueError(f"{function}: negative-controls file is missing")
    else:
        raise ValueError(f"{function}: normalized approved review must name negative controls as a path")
    artifacts = review.get("artifacts", [])
    if not isinstance(artifacts, list):
        raise ValueError(f"{function}: approved artifacts must be a list")
    artifact_names = set()
    for artifact in artifacts:
        if not isinstance(artifact, dict) or not isinstance(artifact.get("name"), str):
            raise ValueError(f"{function}: malformed approved artifact record")
        if artifact["name"] in artifact_names:
            raise ValueError(f"{function}: approved artifact names must be unique")
        artifact_names.add(artifact["name"])
        repo_file(root, {"path": artifact.get("path"), "sha256": artifact.get("sha256")},
                  f"{function} approved artifact {artifact['name']}")
    helpers = review.get("helper_boundaries", [])
    if not isinstance(helpers, list):
        raise ValueError(f"{function}: helper_boundaries must be a list")
    for helper in helpers:
        if not isinstance(helper, dict):
            raise ValueError(f"{function}: malformed helper boundary")
        if helper.get("execution_mode") in ("MODELED", "TRACE_ONLY"):
            cert = helper.get("certification")
            if not isinstance(cert, dict):
                raise ValueError(f"{function}: {helper.get('name')} requires an approved certification, not a proposal")
            if not isinstance(cert.get("path"), str) or not cert["path"].startswith("evidence/behavior/helpers/"):
                raise ValueError(f"{function}: helper certification must be archived under evidence/behavior/helpers")
            cert_path = repo_file(root, cert, f"{function} helper {helper.get('name')} certification")
            cert_body = json.loads(cert_path.read_text(encoding="utf-8"))
            cert_review = cert_body.get("review") if isinstance(cert_body, dict) else None
            if (not isinstance(cert_body, dict) or cert_body.get("schema") != "behavior-helper-cert-v1"
                    or cert_body.get("status") != "CERTIFIED"
                    or not isinstance(cert_review, dict) or cert_review.get("status") != "APPROVED"
                    or not is_root(cert_review.get("reviewer"))):
                raise ValueError(f"{function}: helper {helper.get('name')} certification is not root-approved CERTIFIED evidence")
    destination = entry.get("destination")
    if not isinstance(destination, str) or not destination:
        raise ValueError(f"{function}: immutable packet destination required")
    out = (root / destination).resolve()
    try:
        out.relative_to((root / "evidence/behavior/functions" / function).resolve())
    except ValueError as exc:
        raise ValueError(f"{function}: destination must be below its behavior evidence directory") from exc
    if out.exists():
        raise ValueError(f"{function}: destination already exists; packets are immutable")
    return review_path, run_path, out


def package_batch(manifest_path: Path, *, root: Path = ROOT) -> dict:
    root = root.resolve()
    manifest_path = manifest_path if manifest_path.is_absolute() else root / manifest_path
    try:
        manifest_path.resolve().relative_to(root)
    except ValueError as exc:
        raise ValueError("batch manifest must be repository-local") from exc
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict) or manifest.get("schema") != SCHEMA:
        raise ValueError(f"manifest schema must be {SCHEMA}")
    batch_review = manifest.get("review")
    if (not isinstance(batch_review, dict) or batch_review.get("status") != "APPROVED"
            or not is_root(batch_review.get("reviewer")) or not batch_review.get("reason")):
        raise ValueError("batch manifest requires explicit root APPROVED review and reason")
    try:
        date.fromisoformat(batch_review.get("reviewed_at", ""))
    except (TypeError, ValueError) as exc:
        raise ValueError("batch review date must be ISO YYYY-MM-DD") from exc
    entries = manifest.get("entries")
    if not isinstance(entries, list) or not entries:
        raise ValueError("batch manifest entries must be a non-empty list")
    prepared = []
    functions = set()
    destinations = set()
    for entry in entries:
        review_path, run_path, out = preflight(root, entry)
        if entry["function"] in functions or out in destinations:
            raise ValueError("batch functions and destinations must be unique")
        functions.add(entry["function"])
        destinations.add(out)
        prepared.append((entry, review_path, run_path, out))
    results = []
    for entry, review_path, run_path, out in prepared:
        evidence_path = behavior_packet.package(run_path, review_path,
            out.relative_to(root).as_posix())
        results.append({"function": entry["function"],
                        "evidence": evidence_path.relative_to(root).as_posix(),
                        "evidence_sha256": bv.sha256_file(evidence_path),
                        "status": "PACKAGED_UNREGISTERED"})
    return {"schema": "behavior-review-package-result-v1", "packaged": results,
            "registry_mutated": False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    try:
        result = package_batch(args.manifest)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(json.dumps({"packaged": [], "error": str(exc), "registry_mutated": False}, indent=2))
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
