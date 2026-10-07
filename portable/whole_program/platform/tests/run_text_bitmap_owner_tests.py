#!/usr/bin/env python3
"""Build and run canonical text bitmap owner and duplicate-backing controls."""
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
    parser.add_argument("--abi-build", required=True,
                        help="fresh or accepted portable build with generated ABI headers")
    parser.add_argument("--out", required=True,
                        help="fresh experiment directory below this worktree")
    parser.add_argument("--gcc", default=str(GCC_DEFAULT))
    args = parser.parse_args()

    abi_build = Path(args.abi_build)
    if not abi_build.is_absolute():
        abi_build = ROOT / abi_build
    abi_build = abi_build.resolve()
    try:
        abi_build.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise SystemExit("ABI build must stay inside this worktree") from exc
    if not (abi_build / "canonical_graphics_data.h").is_file():
        raise SystemExit(f"generated canonical ABI header missing: {abi_build}")

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
    exe = out / "text-bitmap-owner-tests.exe"
    sources = [
        ROOT / "portable/whole_program/platform/tests/text_bitmap_owner_test.c",
        abi_build / "canonical_asm_numeric_data.c",
        ROOT / "portable/whole_program/text_bitmap.c",
        ROOT / "portable/whole_program/text_bitmap_bridge.c",
        ROOT / "portable/whole_program/platform/font_blit.c",
    ]
    command = [str(gcc), "-std=c11", "-Wall", "-Wextra", "-Werror", "-O0",
               "-I", str(ROOT), "-I", str(abi_build),
               "-I", str(ROOT / "portable/whole_program/platform"),
               "-I", str(ROOT / "portable/whole_program"), *map(str, sources),
               "-o", str(exe)]
    if not gcc.is_file():
        raise SystemExit(f"GCC not found: {gcc}")
    compiled = subprocess.run(command, capture_output=True, text=True)
    (out / "compile.stdout.txt").write_text(compiled.stdout, encoding="utf-8")
    (out / "compile.stderr.txt").write_text(compiled.stderr, encoding="utf-8")
    if compiled.returncode:
        raise SystemExit(f"owner test compile failed ({compiled.returncode})")

    positive = subprocess.run([str(exe)], capture_output=True, text=True)
    (out / "positive.stdout.txt").write_text(positive.stdout, encoding="utf-8")
    (out / "positive.stderr.txt").write_text(positive.stderr, encoding="utf-8")
    if positive.returncode:
        raise SystemExit(f"canonical owner regression failed ({positive.returncode})")

    negative = subprocess.run([str(exe), "--negative-control"],
                              capture_output=True, text=True)
    (out / "negative.stdout.txt").write_text(negative.stdout, encoding="utf-8")
    (out / "negative.stderr.txt").write_text(negative.stderr, encoding="utf-8")
    expected_failure = "canonical owner check failed: g_5ABE[0] stayed zero"
    if negative.returncode != 2 or expected_failure not in negative.stderr:
        raise SystemExit("negative control did not fail on the canonical owner assertion")

    report = {
        "schema": "simant-canonical-text-bitmap-owner-v1",
        "status": "PASS",
        "positive": "f_1FBD writes pixel/string/terminator owners; font_MakeImage writes the same canonical span",
        "negative_control": "PASS_EXPECTED_FAILURE: font_MakeImage redirected to sidecar leaves g_5ABE zero",
        "negative_exit_code": negative.returncode,
        "compile_command": command,
        "abi_build": str(abi_build),
        "python": {"version": sys.version, "platform": sys.platform},
    }
    (out / "report.json").write_text(json.dumps(report, indent=2) + "\n",
                                      encoding="utf-8")
    print(json.dumps({"status": report["status"],
                      "negative_exit_code": report["negative_exit_code"],
                      "report": out.relative_to(ROOT).as_posix()}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
