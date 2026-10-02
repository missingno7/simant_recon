#!/usr/bin/env python3
"""Run current DOS differentials for EnterNest, SpiderScan, and MoveSpider.

Outputs go to dated evidence paths; earlier reports are retained unchanged.
The receipt pins all source, harness, suite, game-data, and compiler inputs
before and after each run so source drift cannot be mistaken for fresh proof.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
GCC = Path("C:/msys64/mingw64/bin/gcc.exe")
OUT = ROOT / "portable/tests/evidence/current/20261002"

COMMON = ["tools/behavior.py", "tools/exe.py", "tools/functions.py", "tools/match.py",
          "assets/SIMANT.EXE", str(GCC)]
RUNS = [
    {
        "id": "enternest",
        "command": [sys.executable, "portable/tests/nest/run_dos_diff.py",
                    "--random-count", "5000", "--dirt-cases", "128",
                    "--report", str(OUT / "enternest-5937.json")],
        "inputs": COMMON + [
            "portable/game/simulation/nest.c", "portable/game/simulation/nest.h",
            "portable/game/simulation/rng.c", "portable/game/simulation/rng.h",
            "portable/game/simulation/movement.h", "portable/game/state/world.h",
            "portable/tests/nest/native_adapter.c", "portable/tests/nest/native_adapter.h",
            "portable/tests/nest/run_dos_diff.py",
            "tools/behavior_suites/archive/spider_nest-20261002-current-runner-ledger-final.py",
        ],
    },
    {
        "id": "spiderscan",
        "command": [sys.executable, "portable/tests/spider/run_dos_diff.py",
                    "--random-count", "10000", "--seed", "0x5A17E2",
                    "--report", str(OUT / "spiderscan-10146.json")],
        "inputs": COMMON + [
            "portable/game/simulation/spider.c", "portable/game/simulation/spider.h",
            "portable/game/simulation/rng.c", "portable/game/simulation/rng.h",
            "portable/game/state/world.h", "portable/tests/spider/native_bridge.c",
            "portable/tests/spider/run_dos_diff.py",
            "tools/behavior_suites/archive/spider_nest-20261002-current-runner-ledger-final.py",
            "assets/SHARED.NDX", "assets/SHARED.DAT",
        ],
    },
    {
        "id": "movespider",
        "command": [sys.executable, "portable/tests/spider_sim/run_dos_diff.py",
                    "--random-count", "10134", "--report",
                    str(OUT / "movespider-10146.json")],
        "inputs": COMMON + [
            "portable/game/simulation/spider_sim.c", "portable/game/simulation/spider_sim.h",
            "portable/game/simulation/spider.c", "portable/game/simulation/spider.h",
            "portable/game/simulation/movement.c", "portable/game/simulation/movement.h",
            "portable/game/simulation/rng.c", "portable/game/simulation/rng.h",
            "portable/game/state/world.h", "portable/tests/spider_sim/native_bridge.c",
            "portable/tests/spider_sim/run_dos_diff.py",
            "portable/tests/spider_sim/evidence/run-pinned-current-world.py",
            "tools/behavior_suites/archive/spider_nest-20261002-current-runner-ledger-final.py",
            "assets/SHARED.NDX", "assets/SHARED.DAT",
        ],
    },
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    wrapper_sha = sha(Path(__file__))
    results = []
    for run in RUNS:
        paths = [ROOT / item if not Path(item).is_absolute() else Path(item)
                 for item in run["inputs"]]
        before = {str(path): sha(path) for path in paths}
        process = subprocess.run(run["command"], cwd=ROOT, check=False)
        after = {str(path): sha(path) for path in paths}
        report_path = Path(run["command"][-1])
        report_path = report_path if report_path.is_absolute() else ROOT / report_path
        result = {
            "id": run["id"], "command": run["command"],
            "runner_exit_code": process.returncode,
            "source_stability": "stable" if before == after else "changed",
            "inputs_before": before, "inputs_after": after,
            "report_path": str(report_path.relative_to(ROOT)),
            "report_sha256": sha(report_path) if report_path.exists() else None,
        }
        results.append(result)
        if process.returncode or before != after or not report_path.exists():
            raise SystemExit(f"{run['id']} failed; see receipt details")
    receipt = {
        "schema": "current-native-dos-core-reruns-v1",
        "date": "2026-10-02", "wrapper_sha256": wrapper_sha,
        "oracle_sha256": sha(ROOT / "assets/SIMANT.EXE"),
        "compiler_sha256": sha(GCC), "runs": results,
    }
    receipt_path = OUT / "source-stability-receipt.json"
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"receipt": str(receipt_path.relative_to(ROOT)),
                      "runs": [{"id": r["id"], "report": r["report_path"],
                                "sha256": r["report_sha256"],
                                "source_stability": r["source_stability"]}
                               for r in results]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
