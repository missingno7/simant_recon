#!/usr/bin/env python3
"""Compile and run the native f_1FBD_0000 source-ABI bridge test."""
from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[4]
BUILD = ROOT / "build/workers/whole_program/text_bitmap"


def main() -> None:
    compiler = os.environ.get("SIMANT_CC") or shutil.which("gcc")
    if not compiler:
        raise SystemExit("GCC not found; set SIMANT_CC")
    BUILD.mkdir(parents=True, exist_ok=True)
    executable = BUILD / "text-bitmap-bridge-test.exe"
    sources = [
        ROOT / "portable/tests/whole_program/text_bitmap/text_bitmap_bridge_test.c",
        ROOT / "portable/whole_program/text_bitmap_bridge.c",
        ROOT / "portable/whole_program/text_bitmap.c",
        ROOT / "portable/whole_program/platform/graphics.c",
        ROOT / "portable/whole_program/platform/graphics_line_1499.c",
        ROOT / "portable/render/primitives.c",
    ]
    command = [compiler, "-std=c11", "-O2", "-Wall", "-Wextra",
               "-Wconversion", "-Werror", "-I", str(ROOT), "-I",
               str(ROOT / "portable"), *(str(path) for path in sources),
               "-o", str(executable)]
    subprocess.run(command, cwd=ROOT, check=True)
    subprocess.run([str(executable)], cwd=ROOT, check=True)
    print(f"native f_1FBD_0000 bridge contract PASS: {executable.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
