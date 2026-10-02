#!/usr/bin/env python3
"""Explicit registration and append-only revision for BEHAVIOR_EXACT evidence.

Historical sources, EXACT manifests and promotions are never edited. Registration
requires a prior behavior_validate.py --verify-only receipt. Revisions require a
fresh receipt, an unchanged registered predecessor, and explicit root review.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import behavior_validate as bv

ROOT = bv.ROOT
REGISTRY = bv.REGISTRY


def _digest(path: Path) -> str:
    return bv.sha256_file(path)


def _write_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_name, path)
    except Exception:
        try:
            os.unlink(temp_name)
        except OSError:
            pass
        raise


def verify_only(evidence_path: Path, receipt_path: Path | None = None) -> dict:
    evidence_path = evidence_path if evidence_path.is_absolute() else ROOT / evidence_path
    evidence, errors = bv._load_json(evidence_path, "evidence")
    if errors:
        return {"valid": False, "errors": errors}
    result = bv.validate_evidence(evidence)
    if result.get("valid") and receipt_path:
        receipt_path = receipt_path if receipt_path.is_absolute() else ROOT / receipt_path
        try:
            receipt_path.resolve().relative_to(ROOT.resolve())
            receipt = bv.validation_receipt(result, evidence_path=evidence_path,
                                            registry_path=REGISTRY)
            _write_atomic(receipt_path, json.dumps(receipt, indent=2) + "\n")
            result["receipt"] = str(receipt_path.relative_to(ROOT)).replace("\\", "/")
        except (OSError, ValueError) as exc:
            result["valid"] = False
            result.setdefault("errors", []).append(f"cannot write local verification receipt: {exc}")
    return result


def verify_revision(evidence_path: Path, receipt_path: Path | None = None, *,
                    registry_path: Path = REGISTRY, root: Path = ROOT) -> dict:
    """Validate a new packet against the current registered version and pin a receipt."""
    root = root.resolve()
    registry_path = registry_path.resolve()
    evidence_path = evidence_path if evidence_path.is_absolute() else root / evidence_path
    evidence, errors = bv._load_json(evidence_path, "revision evidence")
    if errors:
        return {"valid": False, "errors": errors}
    result = bv.validate_evidence(evidence, root=root, registry_path=registry_path,
                                  allow_revision=True, evidence_path=evidence_path)
    if result.get("valid") and receipt_path:
        receipt_path = receipt_path if receipt_path.is_absolute() else root / receipt_path
        try:
            receipt_path.resolve().relative_to(root)
            row = json.loads(registry_path.read_text(encoding="utf-8"))["entries"][evidence["function"]]
            receipt = {
                "schema": "simant-behavior-revision-receipt-v1", "valid": True,
                "function": evidence["function"],
                "evidence_path": str(evidence_path.resolve().relative_to(root)).replace("\\", "/"),
                "evidence_file_sha256": _digest(evidence_path),
                "registry_sha256": _digest(registry_path),
                "previous_evidence_path": row["evidence_path"],
                "previous_evidence_sha256": row["evidence_sha256"],
                "validation": result,
            }
            _write_atomic(receipt_path, json.dumps(receipt, indent=2) + "\n")
            result["receipt"] = str(receipt_path.relative_to(root)).replace("\\", "/")
        except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
            result["valid"] = False
            result.setdefault("errors", []).append(f"cannot write repository-local revision receipt: {exc}")
    return result


def revise(evidence_path: Path, receipt_path: Path, *, reviewed_by: str,
           review_reason: str, registry_path: Path = REGISTRY, root: Path = ROOT) -> dict:
    """Append a reviewed behavior-evidence revision without replacing prior packets."""
    root = root.resolve()
    registry_path = registry_path.resolve()
    evidence_path = evidence_path if evidence_path.is_absolute() else root / evidence_path
    receipt_path = receipt_path if receipt_path.is_absolute() else root / receipt_path
    errors = []
    if reviewed_by.strip() != "root":
        errors.append("revision requires explicit supervisory reviewer 'root'")
    if not review_reason.strip():
        errors.append("revision reason is required")
    receipt, load_errors = bv._load_json(receipt_path, "revision receipt")
    errors.extend(load_errors)
    registry, registry_errors = bv._load_json(registry_path, "behavior registry")
    errors.extend(registry_errors)
    if not isinstance(receipt, dict):
        return {"registered": False, "errors": [*errors, "a valid revision receipt object is required"]}
    if errors:
        return {"registered": False, "errors": errors}
    if not isinstance(receipt, dict) or receipt.get("schema") != "simant-behavior-revision-receipt-v1" or receipt.get("valid") is not True:
        errors.append("a successful revision verification receipt is required")
    if not isinstance(registry, dict):
        errors.append("invalid behavior registry")
        return {"registered": False, "errors": errors}
    if receipt.get("registry_sha256") != _digest(registry_path):
        errors.append("behavior registry changed after revision verification; rerun revision validation")
    try:
        evidence_path.relative_to(root)
    except ValueError:
        errors.append("revision evidence packet must be repository-local")
    if not evidence_path.is_file() or receipt.get("evidence_file_sha256") != _digest(evidence_path):
        errors.append("revision evidence changed after verification; rerun revision validation")
    if receipt.get("evidence_path") != str(evidence_path.resolve().relative_to(root)).replace("\\", "/"):
        errors.append("revision receipt names a different evidence packet")
    evidence, evidence_errors = bv._load_json(evidence_path, "revision evidence")
    errors.extend(evidence_errors)
    function = evidence.get("function") if isinstance(evidence, dict) else None
    row = registry.get("entries", {}).get(function) if isinstance(function, str) else None
    if not isinstance(row, dict) or row.get("status") != "BEHAVIOR_EXACT":
        errors.append("revision target must already have a BEHAVIOR_EXACT registration")
    elif bv._validate_revision_history(root, row):
        errors.extend(bv._validate_revision_history(root, row))
    elif (receipt.get("previous_evidence_path") != row.get("evidence_path")
          or receipt.get("previous_evidence_sha256") != row.get("evidence_sha256")):
        errors.append("registered predecessor changed after revision verification")
    if errors:
        return {"registered": False, "errors": errors}
    previous_path = row["evidence_path"]
    previous_sha = row["evidence_sha256"]
    new_path = str(evidence_path.resolve().relative_to(root)).replace("\\", "/")
    prior_paths = {row.get("evidence_path"), row.get("initial_evidence_path")}
    for rev in row.get("revisions", []) if isinstance(row.get("revisions"), list) else []:
        if isinstance(rev, dict):
            prior_paths.update(rev.get(k) for k in ("from_path", "to_path"))
    if new_path in prior_paths:
        return {"registered": False, "errors": ["revision packet path has already been used; immutable evidence cannot be overwritten"]}
    previous_file = root / previous_path
    if not previous_file.is_file() or _digest(previous_file) != previous_sha:
        return {"registered": False, "errors": ["previous evidence packet is missing or changed; revision cannot proceed"]}
    fresh = bv.validate_evidence(evidence, root=root, registry_path=registry_path,
                                allow_revision=True, evidence_path=evidence_path)
    if not fresh.get("valid"):
        return {"registered": False, "errors": ["fresh revision validation failed", *fresh.get("errors", [])]}
    if receipt.get("validation", {}).get("evidence_sha256") != fresh.get("evidence_sha256"):
        return {"registered": False, "errors": ["revision receipt does not identify freshly validated evidence"]}
    revision = evidence.get("revision", {})
    review = revision.get("review", {}) if isinstance(revision, dict) else {}
    if review.get("reviewer") != "root" or review.get("reason") != review_reason.strip():
        return {"registered": False, "errors": ["packet review record must match the explicit root reviewer and reason"]}
    row.setdefault("initial_evidence_path", previous_path)
    row.setdefault("initial_evidence_sha256", previous_sha)
    row.setdefault("revisions", []).append({
        "from_path": previous_path, "from_sha256": previous_sha,
        "to_path": new_path, "to_sha256": _digest(evidence_path),
        "receipt_sha256": _digest(receipt_path),
        "review": {"reviewer": "root", "reason": review_reason.strip(),
                   "reviewed_at": review.get("reviewed_at")},
    })
    row["evidence_path"] = new_path
    row["evidence_sha256"] = _digest(evidence_path)
    row["last_revision_receipt_sha256"] = _digest(receipt_path)
    registry["updated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    _write_atomic(registry_path, json.dumps(registry, indent=2, ensure_ascii=False) + "\n")
    return {"registered": True, "revised": True, "function": function,
            "previous_evidence_sha256": previous_sha, "evidence_sha256": row["evidence_sha256"],
            "revisions": len(row["revisions"])}


def register(evidence_path: Path, receipt_path: Path, *, reviewed_by: str,
             review_note: str, registry_path: Path = REGISTRY,
             root: Path = ROOT) -> dict:
    root = root.resolve()
    registry_path = registry_path.resolve()
    evidence_path = evidence_path if evidence_path.is_absolute() else root / evidence_path
    receipt_path = receipt_path if receipt_path.is_absolute() else root / receipt_path
    if evidence_path.is_file() and registry_path.is_file():
        try:
            early_evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
            early_registry = json.loads(registry_path.read_text(encoding="utf-8"))
            early_name = early_evidence.get("function")
            early_row = early_registry.get("entries", {}).get(early_name)
            if isinstance(early_row, dict) and early_row.get("status") == "BEHAVIOR_EXACT":
                if early_row.get("evidence_sha256") == _digest(evidence_path):
                    return {"registered": True, "idempotent": True, "function": early_name,
                            "status": "BEHAVIOR_EXACT", "evidence_sha256": early_row["evidence_sha256"]}
                return {"registered": False, "errors": ["BEHAVIOR_EXACT evidence is immutable; replacement needs a new reviewed procedure"]}
        except (OSError, json.JSONDecodeError):
            pass
    errors: list[str] = []
    receipt, load_errors = bv._load_json(receipt_path, "validation receipt")
    errors.extend(load_errors)
    if isinstance(receipt, dict):
        if receipt.get("schema") != "simant-behavior-validation-receipt-v1" or receipt.get("valid") is not True:
            errors.append("a successful behavior validation receipt is required")
        if receipt.get("registry_sha256") != _digest(registry_path):
            errors.append("behavior registry changed after verify-only; rerun validation")
        if not evidence_path.is_file() or receipt.get("evidence_file_sha256") != _digest(evidence_path):
            errors.append("evidence changed after verify-only; rerun validation")
        expected_evidence_path = str(evidence_path.resolve().relative_to(root)).replace("\\", "/")
        if receipt.get("evidence_path") != expected_evidence_path:
            errors.append("validation receipt names a different evidence file")
    if not reviewed_by.strip() or not review_note.strip():
        errors.append("explicit --reviewed-by and --review-note are required for registration")
    if errors:
        return {"registered": False, "errors": errors}

    evidence, load_errors = bv._load_json(evidence_path, "evidence")
    errors.extend(load_errors)
    if errors:
        return {"registered": False, "errors": errors}
    result = bv.validate_evidence(evidence, root=root, registry_path=registry_path)
    if not result.get("valid"):
        return {"registered": False, "errors": ["fresh evidence validation failed", *result.get("errors", [])]}
    if receipt.get("validation", {}).get("evidence_sha256") != result.get("evidence_sha256"):
        return {"registered": False, "errors": ["receipt validation identity does not match fresh validation"]}

    registry, load_errors = bv._load_json(registry_path, "behavior registry")
    if load_errors or not isinstance(registry, dict):
        return {"registered": False, "errors": load_errors or ["invalid behavior registry"]}
    function = evidence["function"]
    row = registry.get("entries", {}).get(function)
    if not isinstance(row, dict):
        return {"registered": False, "errors": ["function is not registered as open behavioral debt"]}
    evidence_sha = _digest(evidence_path)
    if row.get("status") == "BEHAVIOR_EXACT":
        if row.get("evidence_sha256") == evidence_sha:
            return {"registered": True, "idempotent": True, "function": function,
                    "status": "BEHAVIOR_EXACT", "evidence_sha256": evidence_sha}
        return {"registered": False, "errors": ["BEHAVIOR_EXACT evidence is immutable; replacement needs a new reviewed procedure"]}
    if row.get("status") != "UNRESOLVED":
        return {"registered": False, "errors": ["registry row is not UNRESOLVED"]}

    row.update({
        "status": "BEHAVIOR_EXACT",
        "evidence_path": str(evidence_path.resolve().relative_to(root)).replace("\\", "/"),
        "evidence_sha256": evidence_sha,
        "registered_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "registration_review": {"reviewer": reviewed_by.strip(), "note": review_note.strip()},
        "validation_receipt_sha256": _digest(receipt_path),
    })
    registry["updated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    _write_atomic(registry_path, json.dumps(registry, indent=2, ensure_ascii=False) + "\n")
    return {"registered": True, "function": function, "status": "BEHAVIOR_EXACT",
            "evidence_sha256": evidence_sha, "registry": str(registry_path.relative_to(root)).replace("\\", "/")}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--verify-only", action="store_true")
    mode.add_argument("--register", action="store_true")
    mode.add_argument("--verify-revision", action="store_true",
                      help="verify a new append-only packet for an already registered BEHAVIOR_EXACT function")
    mode.add_argument("--revise", action="store_true",
                      help="append a reviewed packet revision after --verify-revision")
    parser.add_argument("evidence", type=Path)
    parser.add_argument("--receipt", type=Path, required=True,
                        help="write a receipt for --verify-only; consume that receipt for --register")
    parser.add_argument("--reviewed-by", default="")
    parser.add_argument("--review-note", default="")
    parser.add_argument("--review-reason", default="")
    args = parser.parse_args(argv)
    if args.verify_only:
        result = verify_only(args.evidence, args.receipt)
    elif args.verify_revision:
        result = verify_revision(args.evidence, args.receipt)
    elif args.revise:
        result = revise(args.evidence, args.receipt, reviewed_by=args.reviewed_by,
                        review_reason=args.review_reason)
    else:
        result = register(args.evidence, args.receipt, reviewed_by=args.reviewed_by,
                          review_note=args.review_note)
    print(json.dumps(result, indent=2))
    return 0 if result.get("valid", result.get("registered", False)) else 1


if __name__ == "__main__":
    raise SystemExit(main())
