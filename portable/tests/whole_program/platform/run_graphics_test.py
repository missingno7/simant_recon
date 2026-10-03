#!/usr/bin/env python3
"""Compile and run the bounded whole-program graphics ABI contract test."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
INPUTS = [
    ROOT / "portable/whole_program/platform/graphics.h",
    ROOT / "portable/whole_program/platform/graphics_source_fields.h",
    ROOT / "portable/whole_program/platform/graphics_source_convert.py",
    ROOT / "portable/whole_program/platform/graphics.c",
    ROOT / "portable/whole_program/platform/graphics_source_clip.h",
    ROOT / "portable/whole_program/platform/graphics_source_clip.c",
    ROOT / "portable/whole_program/platform/graphics_line_1499.h",
    ROOT / "portable/whole_program/platform/graphics_line_1499.c",
    ROOT / "portable/render/primitives.h",
    ROOT / "portable/render/primitives.c",
    HERE / "graphics_test.c",
    HERE / "graphics_source_fields_test.c",
    HERE / "graphics_s00_rect_probe.c",
    ROOT / "src/root/m1B4E.asm",
    ROOT / "src/S00/m3126.asm",
    ROOT / "src/S00/m31AD.asm",
    ROOT / "src/S00/m31AD_2AB4.asm",
    ROOT / "src/S01/m3126.asm",
    ROOT / "src/S20/m39F1.c",
    ROOT / "src/S24/m39C7.c",
]
INPUTS.extend(sorted((ROOT / "src").rglob("*.c")))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    cc = os.environ.get("CC", "gcc")
    before = {str(path.relative_to(ROOT)): sha256(path) for path in INPUTS}
    converter_test = subprocess.run(
        [sys.executable, str(ROOT / "portable/whole_program/platform/graphics_source_convert.py"), "--self-test"],
        cwd=ROOT, capture_output=True, text=True,
    )
    if converter_test.returncode != 0:
        print(converter_test.stdout, end="")
        print(converter_test.stderr, end="")
        return converter_test.returncode
    with tempfile.TemporaryDirectory(prefix="simant-graphics-contract-") as temp:
        exe = Path(temp) / "graphics_test.exe"
        command = [
            cc,
            "-std=c11",
            "-Wall",
            "-Wextra",
            "-Werror",
            "-pedantic",
            "-I",
            str(ROOT),
            str(ROOT / "portable/whole_program/platform/graphics.c"),
            str(ROOT / "portable/whole_program/platform/graphics_source_clip.c"),
            str(ROOT / "portable/whole_program/platform/graphics_line_1499.c"),
            str(ROOT / "portable/render/primitives.c"),
            str(HERE / "graphics_test.c"),
            str(HERE / "graphics_source_fields_test.c"),
            "-o",
            str(exe),
        ]
        built = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        if built.returncode != 0:
            print(built.stdout, end="")
            print(built.stderr, end="")
            return built.returncode
        try:
            run = subprocess.run([str(exe)], cwd=ROOT, capture_output=True, text=True, timeout=15)
        except subprocess.TimeoutExpired as error:
            print(error.stdout or "", end="")
            print(error.stderr or "", end="")
            raise SystemExit("graphics contract executable exceeded 15 seconds")
    after = {str(path.relative_to(ROOT)): sha256(path) for path in INPUTS}
    report = {
        "schema": "simant-whole-program-graphics-contract-v1",
        "status": "PASS" if run.returncode == 0 else "FAIL",
        "scope": [
            "640x350 EGA default plus 640x480 VGA mode boundary and source dimensions",
            "bounded S00 attribute, fill, axis-line, bitmap, and 1bpp glyph contracts",
        "source table-installed S00 font callbacks, pattern rectangle, and XOR rectangle",
            "clip stack, single-application color mapping, text pen, and explicit unprovided slots",
            "source field converter controls across all 98 original C translation units",
        ],
        "compiler": cc,
        "source_converter_test": converter_test.stdout.strip(),
        "command": command,
        "inputs_before_sha256": before,
        "inputs_after_sha256": after,
        "inputs_stable": before == after,
        "stdout": run.stdout,
        "stderr": run.stderr,
        "exit_code": run.returncode,
    }
    if args.report is not None:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        if args.report.exists():
            raise SystemExit(f"refusing to overwrite report: {args.report}")
        args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(run.stdout, end="")
    print(f"graphics contract runner: {'PASS' if run.returncode == 0 else 'FAIL'}")
    return run.returncode


if __name__ == "__main__":
    raise SystemExit(main())
