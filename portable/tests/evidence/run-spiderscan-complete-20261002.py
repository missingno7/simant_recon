#!/usr/bin/env python3
"""Re-run SpiderScan with the complete project-header dependency closure pinned."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
GCC = Path("C:/msys64/mingw64/bin/gcc.exe")
OUT = ROOT / "portable/tests/evidence/current/20261002"
REPORT = OUT / "spiderscan-10146-complete.json"
INPUTS = [
    "tools/behavior.py", "tools/exe.py", "tools/functions.py", "tools/match.py",
    "assets/SIMANT.EXE", "assets/SHARED.NDX", "assets/SHARED.DAT",
    "portable/game/simulation/spider.c", "portable/game/simulation/spider.h",
    "portable/game/simulation/rng.c", "portable/game/simulation/rng.h",
    "portable/game/state/world.h", "portable/game/simulation/movement.h",
    "portable/tests/spider/native_bridge.c", "portable/tests/spider/run_dos_diff.py",
    "tools/behavior_suites/archive/spider_nest-20261002-current-runner-ledger-final.py",
]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    before = {str(ROOT / p): digest(ROOT / p) for p in INPUTS}
    before[str(GCC)] = digest(GCC)
    command = [sys.executable, "portable/tests/spider/run_dos_diff.py",
               "--random-count", "10000", "--seed", "0x5A17E2",
               "--report", str(REPORT)]
    process = subprocess.run(command, cwd=ROOT, check=False)
    after = {str(ROOT / p): digest(ROOT / p) for p in INPUTS}
    after[str(GCC)] = digest(GCC)
    receipt = {
        "schema": "native-dos-spiderscan-source-stability-v1",
        "date": "2026-10-02", "producer": str(Path(__file__).relative_to(ROOT)),
        "producer_sha256": digest(Path(__file__)),
        "oracle_sha256": digest(ROOT / "assets/SIMANT.EXE"),
        "command": command, "runner_exit_code": process.returncode,
        "source_stability": "stable" if before == after else "changed",
        "inputs_before": before, "inputs_after": after,
        "report": str(REPORT.relative_to(ROOT)),
        "report_sha256": digest(REPORT) if REPORT.exists() else None,
    }
    receipt_path = OUT / "spiderscan-source-stability.json"
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    if process.returncode or before != after or not REPORT.exists():
        raise SystemExit("SpiderScan run failed or inputs changed; see receipt")
    print(json.dumps({"report": receipt["report"], "report_sha256": receipt["report_sha256"],
                      "receipt": str(receipt_path.relative_to(ROOT)),
                      "source_stability": receipt["source_stability"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
