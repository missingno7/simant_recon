"""Fail-closed read-only verification for the v32 database terminal-closure receipt."""
from __future__ import annotations
import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RECEIPT_PATH = HERE / "receipt.json"

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def disk_path(text: str) -> Path:
    return ROOT / text.replace("\\", "/")

def main() -> int:
    receipt = json.loads(RECEIPT_PATH.read_text(encoding="utf-8-sig"))
    failures: list[str] = []
    obs = receipt["workspace"]
    report_pin = obs["build_report"]
    report_path = disk_path(report_pin["path"])
    if sha(report_path) != report_pin["sha256"]:
        failures.append("current build-report SHA-256 changed")
    report = json.loads(report_path.read_text(encoding="utf-8-sig"))
    tus = report["translation_units"]
    src_ok = obj_ok = 0
    for row in tus:
        for key, label, counter in (("generated_source", "generated-source", "src"), ("object", "object", "obj")):
            pin = row.get(key)
            if not pin or not pin.get("path"):
                failures.append(f"missing {label} pin for {row.get('basename')}")
                continue
            if sha(disk_path(pin["path"])) != pin["sha256"]:
                failures.append(f"{label} mismatch for {row.get('basename')}")
            elif counter == "src":
                src_ok += 1
            else:
                obj_ok += 1
    strict = report.get("strict_static_audit", {})
    strict_names = sorted(strict)
    if set(strict_names) != set(report_pin["strict_effective_names"]):
        failures.append("strict effective-name set changed")
    if len(strict_names) != report_pin["strict_effective_count"]:
        failures.append("strict effective count changed")
    if any(strict[name].get("status") != "BEHAVIOR_EXACT_CONFIRMED" for name in strict_names):
        failures.append("strict effective status changed")
    for pin in receipt["direct_tu_pins"]:
        src = pin["source"]
        if sha(disk_path(src["path"])) != src["sha256"]:
            failures.append(f"direct source mismatch: {src['path']}")
        for key in ("generated_source", "object"):
            value = pin.get(key)
            if value and sha(disk_path(value["path"])) != value["sha256"]:
                failures.append(f"direct {key} mismatch: {value['path']}")
    for pin in receipt["historical_input_pins"]:
        if sha(disk_path(pin["path"])) != pin["sha256"]:
            failures.append(f"historical input mismatch: {pin['path']}")
    if len(tus) != report_pin["translation_units"] or src_ok != len(tus) or obj_ok != len(tus):
        failures.append("translation-unit/source/object census differs from receipt")
    if receipt["verdict"] != "UNRESOLVED":
        failures.append("unexpected verdict")
    summary = {
        "verdict": receipt["verdict"], "translation_units": len(tus),
        "generated_sources_verified": src_ok, "objects_verified": obj_ok,
        "strict_effective_count": len(strict_names), "mismatches": failures,
    }
    print(json.dumps(summary, indent=2))
    return 1 if failures else 0

if __name__ == "__main__":
    raise SystemExit(main())

