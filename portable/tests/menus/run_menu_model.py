#!/usr/bin/env python3
"""Strict source-derived menu model test on the actual SHARED database."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[3]
BUILD = ROOT / "build/portable/menu-model"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    compiler = os.environ.get("SIMANT_CC") or shutil.which("gcc")
    if not compiler:
        raise SystemExit("GCC missing; set SIMANT_CC")
    test = ROOT / "portable/tests/menus/test_menu.c"
    menu_c = ROOT / "portable/ui_model/menus/menu.c"
    menu_h = ROOT / "portable/ui_model/menus/menu.h"
    db_c = ROOT / "portable/game/resources/database.c"
    db_h = ROOT / "portable/game/resources/database.h"
    runner = Path(__file__).resolve()
    source_anchors = [ROOT / "src/root/m1FD2.c",
                      ROOT / "src/S17/m384C.c",
                      ROOT / "src/S20/m39F1.c"]
    assets = [ROOT / "assets/SHARED.NDX", ROOT / "assets/SHARED.DAT"]
    inputs = [test, menu_c, menu_h, db_c, db_h, runner, *source_anchors, *assets]
    BUILD.mkdir(parents=True, exist_ok=True)
    executable = BUILD / "menu-model-test.exe"
    command = [compiler, "-std=c11", "-O2", "-Wall", "-Wextra",
               "-Wconversion", "-Werror", "-I", str(ROOT / "portable"),
               str(db_c), str(menu_c), str(test), "-o", str(executable)]
    input_hashes = {path.relative_to(ROOT).as_posix(): sha(path) for path in inputs}
    subprocess.run(command, cwd=ROOT, check=True)
    result = subprocess.run([str(executable), str(ROOT / "assets")],
                            cwd=ROOT, check=True, text=True, capture_output=True)
    changed = [path for path in inputs
               if sha(path) != input_hashes[path.relative_to(ROOT).as_posix()]]
    if changed:
        raise SystemExit(f"inputs changed during test: {changed}")
    report = {
        "status": "PASS",
        "claim": "source-derived portable menu model test; not an original-DOS differential",
        "compiler": subprocess.check_output([compiler, "--version"], text=True).splitlines()[0],
        "command": command,
        "output": result.stdout.strip(),
        "test_domains": ["SHARED kind-6 resource selection and id-0 fallback",
                         "actual five title/item tables and counts",
                         "direct SetMenuItemState indexing vs id-minus-one text indexing",
                         "bounded in-place text mutation/high-bit highlight state",
                         "f_1FD2_0663 gap, bar and title geometry; ordered draw commands",
                         "screen width 320 and 640 source load selection"],
        "source_anchors": {
            "src/root/m1FD2.c": "SetMenuItemState, f_1FD2_0135, f_1FD2_0198/021B, f_1FD2_0663",
            "src/S17/m384C.c": "o17_384C_0039 loads kind 6; o17_384C_0184 title region IDs",
            "src/S20/m39F1.c": "tries id 1 at non-320 widths, then falls back to id 0",
        },
        "inputs_sha256": input_hashes,
        "executable_sha256": sha(executable),
    }
    output = BUILD / "menu-model-test.json"
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: value for key, value in report.items()
                      if key not in {"inputs_sha256", "command"}}, indent=2))
    print(f"receipt: {output.relative_to(ROOT).as_posix()}")


if __name__ == "__main__":
    main()
