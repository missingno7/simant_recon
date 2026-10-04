#!/usr/bin/env python3
"""Recheck path/SHA-256 pins in the four completed DOS v36 worker packets.

Read-only with respect to packet inputs. Writes inventory.json and
inventory-report.md beside this script. It never updates a receipt or pin.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
OUT_DIR = Path(__file__).resolve().parent
WORKERS = (
    "dos_tail_clear_v36",
    "dos_ctype_sequence_v36",
    "dos_database_exit_v36",
    "dos_clip_owner_v36",
)

PACKET_ARTIFACTS = {
    "dos_tail_clear_v36": (
        "functional-tail-candidate.json",
        "review.md",
        "pre-clear-prefix-review.json",
        "stock-crt-controls.json",
        "full-dos-execution.json",
    ),
    "dos_ctype_sequence_v36": (
        "review.md",
        "audit.json",
        "packet-index.json",
        "probe.py",
    ),
    "dos_database_exit_v36": (
        "REPORT.md",
        "receipt.json",
        "review_exit_v36.py",
    ),
    "dos_clip_owner_v36": (
        "ownership-report.md",
        "ownership-review.json",
        "extent-controls.json",
    ),
}

TEXT_EXTENSIONS = {
    ".asm", ".bat", ".c", ".cfg", ".conf", ".h", ".inc", ".json",
    ".log", ".map", ".md", ".py", ".ps1", ".txt",
}
BINARY_EXTENSIONS = {
    ".com", ".dat", ".dll", ".exe", ".lib", ".obj", ".o", ".pdb",
}
ORIGINAL_ASSET_PARTS = {"assets", "originals", "oracle-assets"}


def sha256_file(path: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as stream:
        while True:
            block = stream.read(1024 * 1024)
            if not block:
                break
            size += len(block)
            digest.update(block)
    return digest.hexdigest(), size


def rel_or_text(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except (OSError, ValueError):
        return str(path)


def resolve_pin(raw: Any) -> Path | None:
    if not isinstance(raw, str) or not raw.strip():
        return None
    candidate = Path(os.path.expandvars(raw))
    if candidate.is_absolute():
        return candidate
    # Receipts use both slash conventions. Path handles either on Windows;
    # replacing separators also keeps relative pins usable if run elsewhere.
    return ROOT / raw.replace("\\", os.sep).replace("/", os.sep)


def json_pointer_part(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


def pin_role(path_text: str, ext: str, inside_packet: bool) -> str:
    if ext in BINARY_EXTENSIONS:
        return "binary_pin_only"
    if inside_packet and ext in {".log", ".map"}:
        return "diagnostic_output"
    return "source_or_reference"


def is_inside(path: Path, directory: Path) -> bool:
    try:
        path.resolve().relative_to(directory.resolve())
        return True
    except (OSError, ValueError):
        return False


def load_pin_occurrences() -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    occurrences: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    for worker in WORKERS:
        worker_root = ROOT / "build" / "workers" / worker
        if not worker_root.is_dir():
            errors.append({"path": rel_or_text(worker_root), "error": "worker directory missing"})
            continue
        for json_path in sorted(worker_root.rglob("*.json"), key=lambda p: p.as_posix().casefold()):
            try:
                document = json.loads(json_path.read_text(encoding="utf-8-sig"))
            except Exception as exc:  # Keep the packet inventory complete if one input is malformed.
                errors.append({"path": rel_or_text(json_path), "error": f"JSON read/parse failed: {exc}"})
                continue

            def visit(value: Any, pointer: str = "$") -> None:
                if isinstance(value, dict):
                    if "path" in value and "sha256" in value:
                        raw_path = value.get("path")
                        expected_hash = value.get("sha256")
                        resolved = resolve_pin(raw_path)
                        expected_size = value.get("size")
                        ext = Path(str(raw_path)).suffix.casefold() if isinstance(raw_path, str) else ""
                        inside_packet = bool(resolved and any(
                            is_inside(resolved, ROOT / "build" / "workers" / name)
                            for name in WORKERS
                        ))

                        row: dict[str, Any] = {
                            "packet": worker,
                            "receipt_json": rel_or_text(json_path),
                            "json_pointer": pointer,
                            "path": raw_path,
                            "expected_sha256": expected_hash,
                            "role": pin_role(str(raw_path), ext, inside_packet),
                            "archive_candidate": bool(
                                resolved
                                and inside_packet
                                and ext in TEXT_EXTENSIONS
                                and not (ORIGINAL_ASSET_PARTS & {part.casefold() for part in Path(str(raw_path)).parts})
                            ),
                        }
                        if isinstance(expected_size, int) and not isinstance(expected_size, bool):
                            row["expected_size"] = expected_size

                        if resolved is None or not isinstance(expected_hash, str) or len(expected_hash) != 64:
                            row["status"] = "malformed"
                            row["current_path"] = str(raw_path)
                        elif not resolved.is_file():
                            row["status"] = "missing"
                            row["current_path"] = rel_or_text(resolved)
                        else:
                            row["current_path"] = rel_or_text(resolved)
                            try:
                                actual_hash, actual_size = sha256_file(resolved)
                                row["current_sha256"] = actual_hash
                                row["current_size"] = actual_size
                                size_matches = expected_size is None or expected_size == actual_size
                                row["status"] = "exact" if actual_hash.casefold() == expected_hash.casefold() and size_matches else "drift"
                            except OSError as exc:
                                row["status"] = "unreadable"
                                row["read_error"] = str(exc)

                        if row["status"] == "drift" and row["role"] == "diagnostic_output":
                            row["drift_note"] = "stale diagnostic-only pin; observed bytes recorded, receipt left unchanged"
                        if row["role"] == "binary_pin_only":
                            row["archive_candidate"] = False
                        occurrences.append(row)

                    for key, child in value.items():
                        visit(child, f"{pointer}/{json_pointer_part(str(key))}")
                elif isinstance(value, list):
                    for index, child in enumerate(value):
                        visit(child, f"{pointer}/{index}")

            visit(document)
    return occurrences, errors


def observe_packet_artifacts() -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    rows: list[dict[str, Any]] = []
    missing: list[dict[str, str]] = []
    for worker, names in PACKET_ARTIFACTS.items():
        for name in names:
            path = ROOT / "build" / "workers" / worker / name
            if not path.is_file():
                missing.append({"worker": worker, "path": rel_or_text(path), "status": "missing"})
                continue
            digest, size = sha256_file(path)
            rows.append({
                "worker": worker,
                "path": rel_or_text(path),
                "current_sha256": digest,
                "current_size": size,
                "status": "current_snapshot",
            })
    return rows, missing


def build_preservation_list(occurrences: list[dict[str, Any]], packet_artifacts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates: dict[str, dict[str, Any]] = {}
    by_path: dict[str, list[dict[str, Any]]] = {}
    for pin in occurrences:
        current = pin.get("current_path")
        if pin.get("archive_candidate") and current and pin.get("status") in {"exact", "drift"}:
            try:
                resolved = resolve_pin(pin.get("path"))
                if resolved is None or not resolved.is_file():
                    continue
                key = rel_or_text(resolved)
                by_path.setdefault(key, []).append(pin)
            except OSError:
                continue

    for key, pins in by_path.items():
        resolved = ROOT / Path(key)
        try:
            digest, size = sha256_file(resolved)
        except OSError:
            continue
        candidates[key] = {
            "path": key,
            "current_sha256": digest,
            "current_size": size,
            "pin_occurrences": len(pins),
            "pin_statuses": sorted({p["status"] for p in pins}),
            "workers": sorted({p["packet"] for p in pins}),
            "evidence_kind": "pinned text source, report, control, raw log, or map",
        }

    for artifact in packet_artifacts:
        key = artifact["path"]
        if key in candidates:
            candidates[key]["explicit_packet_artifact"] = True
            continue
        path = ROOT / Path(key)
        ext = path.suffix.casefold()
        if ext not in TEXT_EXTENSIONS or not any(is_inside(path, ROOT / "build" / "workers" / worker) for worker in WORKERS):
            continue
        candidates[key] = {
            "path": key,
            "current_sha256": artifact["current_sha256"],
            "current_size": artifact["current_size"],
            "pin_occurrences": 0,
            "pin_statuses": ["no path/hash pin occurrence found"],
            "workers": [artifact["worker"]],
            "evidence_kind": "explicit packet report, receipt, index, or script",
            "explicit_packet_artifact": True,
        }

    # Some useful worker-root run logs and source scripts have no path/hash
    # dictionary in a receipt. Include their current hashes as unpinned
    # preservation candidates without implying an older expected hash.
    for worker in WORKERS:
        worker_root = ROOT / "build" / "workers" / worker
        for path in sorted(worker_root.iterdir(), key=lambda p: p.name.casefold()):
            if not path.is_file() or path.suffix.casefold() not in TEXT_EXTENSIONS:
                continue
            key = rel_or_text(path)
            if key in candidates or (ORIGINAL_ASSET_PARTS & {part.casefold() for part in path.parts}):
                continue
            try:
                digest, size = sha256_file(path)
            except OSError:
                continue
            candidates[key] = {
                "path": key,
                "current_sha256": digest,
                "current_size": size,
                "pin_occurrences": 0,
                "pin_statuses": ["no path/hash pin occurrence found"],
                "workers": [worker],
                "evidence_kind": "current packet-root text source, report, or control output; no prior pin found",
            }

    return [candidates[key] for key in sorted(candidates, key=str.casefold)]


def write_report(data: dict[str, Any]) -> None:
    summary = data["summary"]
    lines = [
        "# DOS v36 worker receipt inventory",
        "",
        "Read-only byte bookkeeping for the four named v36 worker packets. No acceptance decision or functional claim is made.",
        "",
        f"Scanned {summary['json_files_scanned']} JSON files and enumerated {summary['pin_occurrences']} nested dictionaries with `path` plus `sha256`.",
        "",
        f"Pin checks: {summary['exact']} exact, {summary['drift']} drift, {summary['missing']} missing, {summary['unreadable']} unreadable, {summary['malformed']} malformed.",
        f"Drifted diagnostic output pins: {summary['stale_diagnostic_only']} (observed hashes remain in `inventory.json`; no pins were changed).",
        f"Binary files pinned only: {summary['binary_pin_only']} occurrences. They are excluded from the preservation list.",
        f"Current text preservation candidates: {summary['preservation_candidates']} unique files.",
        "",
        "## Preservation candidates by worker",
        "",
        "These are current text files referenced by packet pins inside the four worker directories, plus the requested packet reports/scripts and unpinned text evidence at packet roots. Each row carries its pin status; unpinned files have only a current snapshot hash and drifted files stay visibly marked. No files were copied or archived.",
        "",
    ]
    for worker in WORKERS:
        rows = [r for r in data["preservation_candidates"] if worker in r["workers"]]
        logs_maps = sum(Path(r["path"]).suffix.casefold() in {".log", ".map"} for r in rows)
        ext_counts: dict[str, int] = {}
        for row in rows:
            ext = Path(row["path"]).suffix.casefold() or "[no extension]"
            ext_counts[ext] = ext_counts.get(ext, 0) + 1
        ext_summary = ", ".join(f"{ext} {count}" for ext, count in sorted(ext_counts.items()))
        lines.append(f"- `{worker}`: {len(rows)} files ({logs_maps} raw `.log`/`.map`; {ext_summary}).")
    lines.extend([
        "",
        "## Drifted diagnostic-only pins",
        "",
    ])
    diagnostic_drifts = [r for r in data["pin_occurrences"] if r.get("drift_note")]
    if diagnostic_drifts:
        for row in diagnostic_drifts:
            lines.append(
                f"- `{row['receipt_json']}` `{row['json_pointer']}` pins `{row['path']}`; "
                f"expected `{row['expected_sha256']}`, current `{row.get('current_sha256', 'unavailable')}`."
            )
    else:
        lines.append("- None detected in the scanned pin dictionaries.")
    other_drifts = [r for r in data["pin_occurrences"] if r["status"] == "drift" and not r.get("drift_note")]
    lines.extend([
        "",
        "## Other drifted pins",
        "",
    ])
    if other_drifts:
        for row in other_drifts:
            lines.append(
                f"- `{row['receipt_json']}` `{row['json_pointer']}` pins `{row['path']}`; "
                f"expected `{row['expected_sha256']}`, current `{row.get('current_sha256', 'unavailable')}` "
                f"({row['role']}). The recorded pin was left unchanged."
            )
    else:
        lines.append("- None detected.")
    lines.extend([
        "",
        "The JSON inventory retains every pin occurrence, expected hash/size, current hash/size when readable, source JSON pointer, and status. Binary `.OBJ`/`.EXE`/`.LIB` and similar artifacts remain hash-pinned only; original assets are never preservation candidates.",
        "",
    ])
    (OUT_DIR / "inventory-report.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    occurrences, scan_errors = load_pin_occurrences()
    packet_artifacts, missing_artifacts = observe_packet_artifacts()
    preservation = build_preservation_list(occurrences, packet_artifacts)
    scanned_json_files = sum(
        sum(1 for _ in (ROOT / "build" / "workers" / worker).rglob("*.json"))
        for worker in WORKERS
        if (ROOT / "build" / "workers" / worker).is_dir()
    )
    statuses = {name: sum(row.get("status") == name for row in occurrences) for name in (
        "exact", "drift", "missing", "unreadable", "malformed"
    )}
    data: dict[str, Any] = {
        "schema": "dos-v36-worker-byte-inventory/v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "scope": {
            "workers": list(WORKERS),
            "scan": "Every .json file recursively under the four packet directories; every dictionary with path and sha256 is a separate pin occurrence.",
            "purpose": "Byte-for-byte bookkeeping only; no acceptance decision and no functional claim.",
            "pin_policy": "Existing expected hashes and sizes are preserved as found. The checker never repins.",
        },
        "packet_artifact_snapshots": packet_artifacts,
        "missing_packet_artifacts": missing_artifacts,
        "scan_errors": scan_errors,
        "summary": {
            "json_files_scanned": scanned_json_files,
            "pin_occurrences": len(occurrences),
            **statuses,
            "stale_diagnostic_only": sum(bool(row.get("drift_note")) for row in occurrences),
            "binary_pin_only": sum(row.get("role") == "binary_pin_only" for row in occurrences),
            "preservation_candidates": len(preservation),
            "missing_packet_artifacts": len(missing_artifacts),
            "scan_errors": len(scan_errors),
        },
        "pin_occurrences": occurrences,
        "preservation_candidates": preservation,
    }
    inventory_path = OUT_DIR / "inventory.json"
    inventory_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_report(data)
    print(json.dumps(data["summary"], sort_keys=True))
    return 0 if not missing_artifacts else 1


if __name__ == "__main__":
    raise SystemExit(main())
