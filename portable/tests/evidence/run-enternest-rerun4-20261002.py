#!/usr/bin/env python3
"""Repeat the current EnterNest DOS differential with full before/after pins."""
from __future__ import annotations
import hashlib, json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
GCC = Path("C:/msys64/mingw64/bin/gcc.exe")
OUT = ROOT / "portable/tests/evidence/current/20261002"
REPORT = OUT / "enternest-5937-rerun4.json"
LIBRARY = ROOT / "build/portable/current-20261002/nest-rerun4.dll"
INPUTS = [
    "portable/game/simulation/nest.c", "portable/game/simulation/nest.h",
    "portable/game/simulation/rng.c", "portable/game/simulation/rng.h",
    "portable/game/simulation/movement.h", "portable/game/state/world.h",
    "portable/tests/nest/native_adapter.c", "portable/tests/nest/native_adapter.h",
    "portable/tests/nest/run_dos_diff.py",
    "tools/behavior_suites/archive/spider_nest-20261002-current-runner-ledger-final.py",
    "tools/behavior.py", "tools/exe.py", "tools/functions.py", "tools/match.py",
    "layout/manifest.json", "layout/functions.json", "layout/symbols.json",
    "layout/oracle.lock.json", "assets/SIMANT.EXE",
]

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    if REPORT.exists() or LIBRARY.exists():
        raise SystemExit("refusing to overwrite rerun4 artifact")
    paths = [ROOT / p for p in INPUTS] + [GCC]
    before = {str(p): digest(p) for p in paths}
    command = [sys.executable, "portable/tests/nest/run_dos_diff.py",
               "--random-count", "5000", "--dirt-cases", "128",
               "--report", str(REPORT), "--library", str(LIBRARY)]
    result = subprocess.run(command, cwd=ROOT, check=False)
    after = {str(p): digest(p) for p in paths}
    if result.returncode or before != after or not REPORT.is_file() or not LIBRARY.is_file():
        raise SystemExit("EnterNest rerun failed or inputs changed")
    receipt = {
        "schema": "current-enternest-rerun-v1", "date": "2026-10-02",
        "producer": str(Path(__file__).relative_to(ROOT)),
        "producer_sha256": digest(Path(__file__)),
        "oracle_sha256": digest(ROOT / "assets/SIMANT.EXE"),
        "compiler_sha256": digest(GCC), "runner_exit_code": result.returncode,
        "source_stability": "stable", "inputs_before": before, "inputs_after": after,
        "report": str(REPORT.relative_to(ROOT)), "report_sha256": digest(REPORT),
        "library": str(LIBRARY.relative_to(ROOT)), "library_sha256": digest(LIBRARY),
    }
    receipt_path = OUT / "enternest-source-stability-rerun4.json"
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report": receipt["report"], "cases": json.loads(REPORT.read_text())["executed"],
                      "receipt": str(receipt_path.relative_to(ROOT)),
                      "source_stability": "stable"}, indent=2))

if __name__ == "__main__":
    main()
