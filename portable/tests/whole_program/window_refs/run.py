#!/usr/bin/env python3
"""Strictly compile and exercise the source-window sidecar adapter."""
from __future__ import annotations

import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[4]
HERE = pathlib.Path(__file__).resolve().parent


def main() -> int:
    cc = shutil.which("gcc") or shutil.which("cc")
    if not cc:
        raise SystemExit("a host C compiler (gcc or cc) is required")
    with tempfile.TemporaryDirectory(prefix="simant-window-refs-") as temp:
        exe = pathlib.Path(temp) / "window-refs-test.exe"
        subprocess.run([
            cc, "-std=c11", "-Wall", "-Wextra", "-Werror", "-O2",
            str(ROOT / "portable/whole_program/window_refs.c"),
            str(HERE / "test_window_refs.c"), "-o", str(exe),
        ], cwd=ROOT, check=True)
        subprocess.run([str(exe)], cwd=ROOT, check=True)
    subprocess.run([sys.executable, str(HERE / "test_converter.py")],
                   cwd=ROOT, check=True)
    print("PASS: sequential DOS RepointObjects layout maps to isolated native sidecars")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
