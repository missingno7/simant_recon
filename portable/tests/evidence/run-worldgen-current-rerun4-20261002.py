#!/usr/bin/env python3
"""Repeat the current RandWorld sweep and edge suites into rerun4 artifacts."""
from __future__ import annotations
import hashlib, json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
GCC = Path("C:/msys64/mingw64/bin/gcc.exe")
OUT = ROOT / "portable/tests/worldgen/evidence/current/20261002"
INPUTS = [
    "portable/game/simulation/worldgen.c", "portable/game/simulation/worldgen.h",
    "portable/game/simulation/rng.c", "portable/game/simulation/rng.h",
    "portable/game/simulation/terrain.c", "portable/game/simulation/terrain.h",
    "portable/game/simulation/ants.c", "portable/game/simulation/ants.h",
    "portable/game/simulation/population.c", "portable/game/simulation/population.h",
    "portable/game/simulation/spider.c", "portable/game/simulation/spider.h",
    "portable/game/simulation/nest.c", "portable/game/simulation/nest.h",
    "portable/game/simulation/setup.c", "portable/game/simulation/setup.h",
    "portable/game/simulation/yard.c", "portable/game/simulation/yard.h",
    "portable/game/state/world.c", "portable/game/state/world.h",
    "portable/game/simulation/movement.c", "portable/game/simulation/movement.h",
    "portable/tests/worldgen/native_snapshot.c", "portable/tests/worldgen/run_dos_diff.py",
    "tools/behavior.py", "tools/functions.py", "tools/exe.py", "tools/match.py",
    "tools/modules.py", "tools/modctx.py", "tools/symbols.py",
    "layout/manifest.json", "layout/functions.json", "layout/symbols.json",
    "layout/oracle.lock.json", "assets/SIMANT.EXE",
]
RUNS = [
    ("sweep", "0x5a31", "0,1", "3"),
    ("edge-8000", "0x8000", "0,1", "0"),
    ("edge-ffff", "0xffff", "0,1", "0"),
]

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    rows = []
    for label, seed, scenarios, random_count in RUNS:
        report = OUT / f"randworld-union-current-{label}-rerun4-20261002.json"
        if report.exists() or report.with_suffix(".dll").exists():
            raise SystemExit(f"refusing to overwrite {report.name}")
        paths = [ROOT / item for item in INPUTS] + [GCC]
        before = {str(path): digest(path) for path in paths}
        command = [sys.executable, "portable/tests/worldgen/run_dos_diff.py",
                   "--seed", seed, "--scenarios", scenarios,
                   "--random-count", random_count, "--random-seed", "0x523157",
                   "--report", str(report)]
        process = subprocess.run(command, cwd=ROOT, check=False)
        after = {str(path): digest(path) for path in paths}
        if process.returncode or before != after or not report.is_file():
            raise SystemExit(f"{label} failed or inputs changed")
        result = json.loads(report.read_text(encoding="utf-8"))
        rows.append({"id": label, "command": command, "runner_exit_code": process.returncode,
                     "source_stability": "stable", "inputs_before": before,
                     "inputs_after": after, "report": str(report.relative_to(ROOT)),
                     "report_sha256": digest(report),
                     "library": str(report.with_suffix(".dll").relative_to(ROOT)),
                     "library_sha256": digest(report.with_suffix(".dll")),
                     "case_count": result["case_count"], "mismatch_count": result["mismatch_count"]})
    receipt = {"schema": "current-native-dos-worldgen-reruns-v1", "date": "2026-10-02",
               "producer": str(Path(__file__).relative_to(ROOT)),
               "producer_sha256": digest(Path(__file__)),
               "oracle_sha256": digest(ROOT / "assets/SIMANT.EXE"),
               "compiler_sha256": digest(GCC), "runs": rows}
    receipt_path = OUT / "source-stability-receipt-rerun4.json"
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"receipt": str(receipt_path.relative_to(ROOT)),
                      "runs": [{"id": row["id"], "cases": row["case_count"],
                                "mismatches": row["mismatch_count"],
                                "source_stability": row["source_stability"]} for row in rows]}, indent=2))

if __name__ == "__main__":
    main()
