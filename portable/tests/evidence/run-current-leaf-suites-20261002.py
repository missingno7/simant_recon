#!/usr/bin/env python3
"""Run current terrain/water/feeding/scent DOS suites with pinned closures."""
from __future__ import annotations
import hashlib, json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
GCC = Path("C:/msys64/mingw64/bin/gcc.exe")
CURRENT = ROOT / "portable/tests/evidence/current/20261002"
COMMON = ["assets/SIMANT.EXE", "layout/manifest.json", "layout/functions.json",
          "layout/symbols.json", "layout/oracle.lock.json", "tools/behavior.py",
          "tools/exe.py", "tools/functions.py", "tools/match.py", "tools/modules.py",
          "tools/modctx.py", "tools/symbols.py"]
RUNS = [
    ("terrain", "portable/tests/terrain/run_dos_diff.py", "portable/tests/terrain/evidence/current/20261002/terrain-950-rerun3.json", "build/portable/current-20261002/terrain-probe-rerun3.dll", [
        "portable/game/simulation/terrain.c", "portable/game/simulation/terrain.h", "portable/game/simulation/rng.c", "portable/game/simulation/rng.h", "portable/game/state/world.h", "portable/game/simulation/movement.h", "portable/tests/terrain/native_probe.c", "portable/tests/terrain/test_terrain.c", "assets/HCEGANT.NDX", "assets/HCEGANT.DAT", "assets/SHARED.NDX", "assets/SHARED.DAT"]),
    ("water", "portable/tests/water/run_dos_diff.py", "portable/tests/water/evidence/current/20261002/water-50-rerun3.json", "build/portable/current-20261002/water-probe-rerun3.dll", [
        "portable/game/simulation/water.c", "portable/game/simulation/water.h", "portable/game/simulation/rng.c", "portable/game/simulation/rng.h", "portable/game/state/world.h", "portable/game/simulation/movement.h", "portable/tests/water/native_probe.c", "portable/tests/water/test_water.c"]),
    ("feeding", "portable/tests/feeding/run_dos_diff.py", "portable/tests/feeding/evidence/current/20261002/feeding-126-rerun3.json", "build/portable/current-20261002/feeding-probe-rerun3.dll", [
        "portable/game/simulation/feeding.c", "portable/game/simulation/feeding.h", "portable/game/simulation/rng.c", "portable/game/simulation/rng.h", "portable/game/state/world.h", "portable/game/simulation/movement.h", "portable/game/simulation/spider.h", "portable/tests/feeding/native_probe.c", "portable/tests/feeding/test_feeding.c", "assets/SHARED.NDX", "assets/SHARED.DAT"]),
    ("scent", "portable/tests/scent/run_dos_diff.py", "portable/tests/scent/evidence/current/20261002/scent-360-rerun3.json", "build/portable/current-20261002/scent-probe-rerun3.dll", [
        "portable/game/simulation/scent.c", "portable/game/simulation/scent.h", "portable/game/state/world.h", "portable/game/simulation/movement.h", "portable/tests/scent/native_probe.c", "portable/tests/scent/test_scent.c"]),
]

def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    CURRENT.mkdir(parents=True, exist_ok=True)
    rows=[]
    for ident, runner, report_rel, library_rel, native_inputs in RUNS:
        report=ROOT/report_rel; library=ROOT/library_rel
        if report.exists() or library.exists(): raise SystemExit(f"refusing overwrite: {ident}")
        paths=[ROOT/p for p in sorted(set(COMMON+native_inputs+[runner]))]+[GCC]
        before={str(p):digest(p) for p in paths}
        command=[sys.executable,runner,"--report",str(report),"--library",str(library)]
        proc=subprocess.run(command,cwd=ROOT,check=False)
        after={str(p):digest(p) for p in paths}
        row={"id":ident,"command":command,"runner_exit_code":proc.returncode,
             "source_stability":"stable" if before==after else "changed",
             "inputs_before":before,"inputs_after":after,
             "report":report_rel,"report_sha256":digest(report) if report.exists() else None,
             "library":library_rel,"library_sha256":digest(library) if library.exists() else None}
        rows.append(row)
        if proc.returncode or before!=after or not report.exists() or not library.exists():
            raise SystemExit(f"{ident} failed or input hashes changed")
    receipt={"schema":"current-native-dos-leaf-suite-reruns-v1","date":"2026-10-02",
             "producer":"portable/tests/evidence/run-current-leaf-suites-20261002.py",
             "producer_sha256":digest(Path(__file__)),"oracle_sha256":digest(ROOT/"assets/SIMANT.EXE"),
             "compiler_sha256":digest(GCC),"runs":rows}
    path=CURRENT/"leaf-suite-source-stability-receipt-rerun3.json"
    path.write_text(json.dumps(receipt,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"receipt":str(path.relative_to(ROOT)),"runs":[
        {"id":r["id"],"report":r["report"],"stable":r["source_stability"],"exit":r["runner_exit_code"]} for r in rows]},indent=2))

if __name__=="__main__": raise SystemExit(main())
