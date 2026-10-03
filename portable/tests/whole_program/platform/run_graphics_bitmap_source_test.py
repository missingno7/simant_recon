#!/usr/bin/env python3
"""Compile the native S00 bitmap callbacks against generated root m1D8E."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import argparse
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
GEN = ROOT / "build/workers/recovered_tick_proof/generated"
INPUTS = [
    ROOT / "portable/whole_program/platform/graphics.h",
    ROOT / "portable/whole_program/platform/graphics.c",
    ROOT / "portable/whole_program/platform/graphics_line_1499.c",
    ROOT / "portable/whole_program/platform/graphics_line_1499.h",
    ROOT / "portable/whole_program/platform/graphics_source_clip.h",
    ROOT / "portable/whole_program/platform/graphics_source_clip.c",
    ROOT / "portable/whole_program/platform/graphics_bitmap_source.h",
    ROOT / "portable/whole_program/platform/graphics_bitmap_source.c",
    ROOT / "portable/whole_program/platform/graphics_clip_source_convert.py",
    ROOT / "portable/whole_program/window_source_rects.h",
    ROOT / "portable/whole_program/window_source_globals.h",
    ROOT / "portable/whole_program/window_source_rects.h",
    ROOT / "portable/whole_program/window_source_globals.c",
    ROOT / "portable/whole_program/platform/dos_memory.h",
    ROOT / "portable/whole_program/platform/dos_io.h",
    ROOT / "portable/whole_program/platform/graphics_source_fields.h",
    ROOT / "portable/render/primitives.c",
    ROOT / "portable/render/primitives.h",
    ROOT / "portable/tests/whole_program/platform/graphics_bitmap_source_test.c",
    ROOT / "portable/tools/whole_program.py",
    ROOT / "src/root/m1D8E.c",
    ROOT / "src/S00/m31AD.asm",
    ROOT / "src/root/m1B4E.asm",
    GEN / "migration.json",
    GEN / "root_m1D8E.c",
    GEN / "dos_types.h",
]

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    compiler = os.environ.get("CC", "gcc")
    before = {str(p.relative_to(ROOT)): sha(p) for p in INPUTS}
    spec = importlib.util.spec_from_file_location(
        "graphics_clip_source_convert",
        ROOT / "portable/whole_program/platform/graphics_clip_source_convert.py")
    clip_converter = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(clip_converter)
    clip_converter.self_test()
    with tempfile.TemporaryDirectory(prefix="simant-g914c-") as tmp:
        temp = Path(tmp)
        exe = temp / "bitmap-source-test.exe"
        converted_root = temp / "root_m1D8E.converted.c"
        converted_root.write_text(
            clip_converter.convert_source("root_m1D8E.c",
                                          (GEN / "root_m1D8E.c").read_text(encoding="utf-8")),
            encoding="utf-8")
        command = [
            compiler, "-std=c11", "-Wall", "-Wextra", "-Werror", "-pedantic",
            "-ffunction-sections", "-fdata-sections", "-I", str(ROOT), "-I", str(GEN),
            str(ROOT / "portable/whole_program/platform/graphics.c"),
            str(ROOT / "portable/whole_program/platform/graphics_line_1499.c"),
            str(ROOT / "portable/whole_program/platform/graphics_source_clip.c"),
            str(ROOT / "portable/whole_program/platform/graphics_bitmap_source.c"),
            str(ROOT / "portable/whole_program/window_source_globals.c"),
            str(ROOT / "portable/render/primitives.c"),
            "-Wno-unused-parameter", "-Wno-unused-variable",
            str(converted_root),
            str(ROOT / "portable/tests/whole_program/platform/graphics_bitmap_source_test.c"),
            "-Wl,--gc-sections", "-o", str(exe),
        ]
        built = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        if built.returncode:
            print(built.stdout, end="")
            print(built.stderr, end="")
            return built.returncode
        run = subprocess.run([str(exe)], cwd=ROOT, capture_output=True, text=True, timeout=15)
        converted_root_sha256 = sha(converted_root)
    after = {str(p.relative_to(ROOT)): sha(p) for p in INPUTS}
    if before != after:
        raise SystemExit("source inputs changed during bitmap source test")
    report = {
        "schema": "simant-whole-program-s00-bitmap-native-v1",
        "status": "PASS" if run.returncode == 0 else "FAIL",
        "scope": [
            "native g9150 ordinary four-plane 640x350 pixel writes",
            "native g914C null-pointer direct path",
            "native g914C non-null g5AAC path through actual generated root f_1D8E_07F6",
            "two disjoint half-open clip rectangles, source offsets, and offset reset",
        ],
        "compiler": compiler,
        "command": command,
        "converted_root_m1D8E_sha256": converted_root_sha256,
        "inputs_before_sha256": before,
        "inputs_after_sha256": after,
        "inputs_stable": True,
        "stdout": run.stdout,
        "stderr": run.stderr,
        "exit_code": run.returncode,
    }
    report_path = args.report or ROOT / "portable/tests/whole_program/platform/evidence/graphics-s00-bitmap-native-v6-20261003.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    if report_path.exists():
        raise SystemExit(f"refusing to overwrite report: {report_path}")
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(run.stdout, end="")
    print("S00 bitmap native test: " + ("PASS" if run.returncode == 0 else "FAIL"))
    return run.returncode

if __name__ == "__main__":
    raise SystemExit(main())
