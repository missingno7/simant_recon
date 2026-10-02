#!/usr/bin/env python3
"""Refresh the three stale union/world-header RandWorld DOS differentials."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
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
    ("randworld-union-current-sweep-20261002.json", "0x5a31", "0,1", "3"),
    ("randworld-union-current-edge-8000-20261002.json", "0x8000", "0,1", "0"),
    ("randworld-union-current-edge-ffff-20261002.json", "0xffff", "0,1", "0"),
]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    run_rows = []
    for name, seed, scenarios, random_count in RUNS:
        report = OUT / name
        before = {str(ROOT / p): digest(ROOT / p) for p in INPUTS}
        before[str(GCC)] = digest(GCC)
        command = [sys.executable, "portable/tests/worldgen/run_dos_diff.py",
                   "--seed", seed, "--scenarios", scenarios,
                   "--random-count", random_count, "--random-seed", "0x523157",
                   "--report", str(report)]
        process = subprocess.run(command, cwd=ROOT, check=False)
        after = {str(ROOT / p): digest(ROOT / p) for p in INPUTS}
        after[str(GCC)] = digest(GCC)
        row = {
            "report": str(report.relative_to(ROOT)), "command": command,
            "runner_exit_code": process.returncode,
            "source_stability": "stable" if before == after else "changed",
            "inputs_before": before, "inputs_after": after,
            "report_sha256": digest(report) if report.exists() else None,
        }
        run_rows.append(row)
        if process.returncode or before != after or not report.exists():
            raise SystemExit(f"{name}: run failed or source changed; inspect receipt")
    receipt = {
        "schema": "current-native-dos-worldgen-reruns-v1",
        "date": "2026-10-02", "producer": str(Path(__file__).relative_to(ROOT)),
        "producer_sha256": digest(Path(__file__)),
        "oracle_sha256": digest(ROOT / "assets/SIMANT.EXE"),
        "compiler_sha256": digest(GCC), "runs": run_rows,
    }
    path = OUT / "source-stability-receipt.json"
    path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"receipt": str(path.relative_to(ROOT)),
                      "runs": [{"report": row["report"], "sha256": row["report_sha256"],
                                "source_stability": row["source_stability"]}
                               for row in run_rows]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
