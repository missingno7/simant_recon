#!/usr/bin/env python3
"""Strict native regression gate. DOS differential proofs are separate suites."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
PORT = ROOT / "portable"
BUILD = ROOT / "build/portable/tests"
UNITS = {
    "ants": ("ants/test_ants.c", []),
    "audio": ("audio/audio_test.c", ["assets/SOUND"]),
    "database": ("resources/database_test.c", ["assets"]),
    "population": ("population/test_population.c", []),
    "render": ("render/test_render.c", ["assets"]),
    "setup": ("setup/test_setup.c", []),
    "session": ("session/test_session.c", ["assets"]),
    "terrain": ("terrain/test_terrain.c", []),
    "water": ("water/test_water.c", []),
    "feeding": ("feeding/test_feeding.c", []),
    "scent": ("scent/test_scent.c", []),
    "tick": ("tick/test_tick.c", []),
    "timing": ("timing/test_timing.c", []),
    "tiles": ("resources/tiles_test.c", ["assets"]),
    "windows": ("windows/test_window.c", []),
    "registry": ("windows/test_registry.c", ["assets"]),
    "map": ("map/test_map.c", ["assets"]),
    "game_view": ("game_view/test_game_view.c", ["assets"]),
    "tile_raster": ("render/tile/test_tile_raster.c", ["assets"]),
    "worldgen": ("worldgen/test_worldgen.c", []),
    "yard": ("yard/test_yard.c", []),
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", choices=sorted(UNITS), action="append")
    parser.add_argument("--host", action="store_true", help="also exercise the real SDL3 host")
    args = parser.parse_args()
    compiler = os.environ.get("SIMANT_CC") or shutil.which("gcc")
    if not compiler:
        fallback = Path("C:/msys64/mingw64/bin/gcc.exe")
        compiler = str(fallback) if fallback.exists() else None
    if not compiler:
        raise SystemExit("Native C compiler missing; set SIMANT_CC")
    # Source-reuse research is deliberately outside this production gate. Its
    # generated modules have their own compile/proof boundary until reviewed.
    sources = sorted([* (PORT / "game").glob("*.c"),
                      *(p for folder in ("game/simulation", "game/state", "game/resources", "game/render",
                                         "render", "ui_model", "audio")
                        for p in (PORT / folder).rglob("*.c"))])
    headers = sorted(PORT.rglob("*.h"))
    BUILD.mkdir(parents=True, exist_ok=True)
    frozen_check = BUILD / "frozen-oracle-check.json"
    subprocess.run([sys.executable,str(ROOT / "tools/oracle_checkpoint.py"),
                    "--output",str(frozen_check)],cwd=ROOT,check=True)
    frozen_receipt = json.loads(frozen_check.read_text())
    if not frozen_receipt.get("ready"):
        raise SystemExit("Frozen historical input identity check failed")
    receipt = {"scope": "native unit/integration checks; not DOS differential acceptance",
               "frozen_oracle_inputs": {"status":"PASS", "receipt_sha256":sha(frozen_check)},
               "status": "RUNNING", "compiler": subprocess.check_output(
                   [compiler, "--version"], text=True).splitlines()[0],
               "inputs": {p.relative_to(ROOT).as_posix(): sha(p) for p in sources + headers},
               "tests": []}
    report = BUILD / "native-unit-report.json"
    for name in args.suite or sorted(UNITS):
        relative, test_args = UNITS[name]
        test = PORT / "tests" / relative
        output = BUILD / f"{name}-test.exe"
        command = [compiler, "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
                   "-I", str(PORT), str(test), *(str(p) for p in sources), "-o", str(output)]
        print(f"[{name}] strict native compile and run", flush=True)
        compiled = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
        if compiled.returncode:
            receipt["status"] = "FAIL"
            receipt["tests"].append({"name": name, "stage": "compile", "exit_code": compiled.returncode,
                                     "diagnostic": compiled.stdout + compiled.stderr})
            report.write_text(json.dumps(receipt, indent=2) + "\n")
            raise SystemExit(compiled.stdout + compiled.stderr)
        ran = subprocess.run([str(output), *test_args], cwd=ROOT, text=True, capture_output=True)
        result = {"name": name, "test_sha256": sha(test), "executable_sha256": sha(output),
                  "exit_code": ran.returncode, "output": ran.stdout + ran.stderr}
        receipt["tests"].append(result)
        print(result["output"].strip(), flush=True)
        if ran.returncode:
            receipt["status"] = "FAIL"
            report.write_text(json.dumps(receipt, indent=2) + "\n")
            raise SystemExit(ran.returncode)
    if args.host:
        subprocess.run([sys.executable, str(PORT / "tests/host/run.py")], cwd=ROOT, check=True)
    changed = [name for name,expected in receipt["inputs"].items()
               if sha(ROOT / name)!=expected]
    if changed:
        receipt["status"]="STALE"
        receipt["changed_during_run"]=changed
        report.write_text(json.dumps(receipt,indent=2)+"\n")
        raise SystemExit(f"Sources changed during the regression gate; rerun required: {changed}")
    receipt["status"] = "PASS"
    report.write_text(json.dumps(receipt, indent=2) + "\n")
    print(f"PASS: {len(receipt['tests'])} native suites; {report}")


if __name__ == "__main__":
    main()
