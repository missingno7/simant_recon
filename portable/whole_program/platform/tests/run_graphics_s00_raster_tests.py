#!/usr/bin/env python3
"""Build and run isolated native S00 raster extent controls."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[4]
GCC_DEFAULT = Path(r"C:\msys64\mingw64\bin\gcc.exe")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True,
                        help="fresh experiment directory below this worktree")
    parser.add_argument("--gcc", default=str(GCC_DEFAULT))
    args = parser.parse_args()

    out = Path(args.out)
    if not out.is_absolute():
        out = ROOT / out
    out = out.resolve()
    try:
        out.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise SystemExit("test output must stay inside this worktree") from exc
    if out.exists():
        raise SystemExit(f"test output must be fresh: {out}")
    out.mkdir(parents=True)

    gcc = Path(args.gcc).resolve()
    exe = out / "graphics-s00-raster-tests.exe"
    source = ROOT / "portable/whole_program/platform/graphics_s00_raster_source.c"
    test = ROOT / "portable/whole_program/platform/tests/graphics_s00_raster_source_test.c"
    command = [str(gcc), "-std=c11", "-Wall", "-Wextra", "-Werror", "-O0",
               "-I", str(ROOT), str(source), str(test), "-o", str(exe)]
    if not gcc.is_file():
        raise SystemExit(f"GCC not found: {gcc}")
    compiled = subprocess.run(command, capture_output=True, text=True)
    (out / "compile.stdout.txt").write_text(compiled.stdout, encoding="utf-8")
    (out / "compile.stderr.txt").write_text(compiled.stderr, encoding="utf-8")
    if compiled.returncode:
        raise SystemExit(f"raster test compile failed ({compiled.returncode})")

    run = subprocess.run([str(exe)], capture_output=True, text=True)
    (out / "run.stdout.txt").write_text(run.stdout, encoding="utf-8")
    (out / "run.stderr.txt").write_text(run.stderr, encoding="utf-8")
    if run.returncode:
        raise SystemExit(f"raster tests failed ({run.returncode}): {run.stderr}")

    report = {
        "schema": "simant-native-s00-raster-extents-v1",
        "status": "PASS",
        "test_output": run.stdout.strip(),
        "compile_command": command,
        "python": {"version": sys.version, "platform": sys.platform},
    }
    (out / "report.json").write_text(json.dumps(report, indent=2) + "\n",
                                      encoding="utf-8")
    print(json.dumps({"status": report["status"], "test": report["test_output"],
                      "report": out.relative_to(ROOT).as_posix()}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
