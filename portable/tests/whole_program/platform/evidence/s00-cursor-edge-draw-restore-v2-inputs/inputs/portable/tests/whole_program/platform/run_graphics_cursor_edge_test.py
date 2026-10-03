#!/usr/bin/env python3
"""Exercise cursor save-under and clipped restore at the logical screen edge."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
GEN = ROOT / "build/workers/whole_program/generated"
PLATFORM = ROOT / "portable/whole_program/platform"
INPUTS = [
    HERE / "run_graphics_cursor_edge_test.py",
    HERE / "graphics_cursor_edge_test.c",
    PLATFORM / "graphics.h", PLATFORM / "graphics.c",
    PLATFORM / "graphics_line_1499.c", PLATFORM / "graphics_line_1499.h",
    PLATFORM / "graphics_source_clip.h", PLATFORM / "graphics_source_clip.c",
    PLATFORM / "graphics_bitmap_source.h", PLATFORM / "graphics_bitmap_source.c",
    PLATFORM / "graphics_capture_source.h", PLATFORM / "graphics_capture_source.c",
    PLATFORM / "graphics_cursor_hooks.h", PLATFORM / "graphics_cursor_hooks.c",
    PLATFORM / "graphics_entry_source.h", PLATFORM / "graphics_entry_source.c",
    PLATFORM / "graphics_cursor_source.h", PLATFORM / "graphics_cursor_source.c",
    PLATFORM / "m1b73_mouse_state.h", PLATFORM / "m1b73_mouse_state.c",
    ROOT / "portable/whole_program/state/asm_display_data_v1.h",
    ROOT / "portable/whole_program/state/asm_display_data_v1.c",
    ROOT / "portable/whole_program/window_source_rects.h",
    ROOT / "portable/render/primitives.h", ROOT / "portable/render/primitives.c",
    PLATFORM / "graphics_clip_source_convert.py",
    ROOT / "src/root/m1D8E.c", ROOT / "src/S00/m31AD.asm",
    GEN / "root_m1D8E.c", GEN / "dos_types.h",
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    report = args.report if args.report.is_absolute() else ROOT / args.report
    if report.exists():
        raise SystemExit(f"refusing to overwrite report: {report}")
    report.parent.mkdir(parents=True, exist_ok=True)
    compiler = os.environ.get("CC", "gcc")
    before = {str(path.relative_to(ROOT)): sha(path) for path in INPUTS}
    spec = importlib.util.spec_from_file_location(
        "graphics_clip_source_convert", PLATFORM / "graphics_clip_source_convert.py")
    converter = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(converter)
    converter.self_test()
    with tempfile.TemporaryDirectory(prefix="simant-cursor-edge-") as tmp:
        temp = Path(tmp)
        exe = temp / "graphics-cursor-edge-test.exe"
        converted = temp / "root_m1D8E.converted.c"
        converted.write_text(converter.convert_source(
            "root_m1D8E.c", (GEN / "root_m1D8E.c").read_text(encoding="utf-8")),
            encoding="utf-8")
        source_names = [
            "graphics.c", "graphics_line_1499.c", "graphics_source_clip.c",
            "graphics_bitmap_source.c", "graphics_capture_source.c",
            "graphics_cursor_hooks.c", "graphics_entry_source.c",
            "graphics_cursor_source.c", "m1b73_mouse_state.c",
        ]
        sources = [PLATFORM / name for name in source_names] + [
            ROOT / "portable/render/primitives.c",
            ROOT / "portable/whole_program/state/asm_display_data_v1.c",
            HERE / "graphics_cursor_edge_test.c"]
        common = [compiler, "-std=c11", "-Wall", "-Wextra", "-Wconversion",
                  "-Werror", "-pedantic", "-ffunction-sections", "-fdata-sections",
                  "-I", str(ROOT), "-Wno-unused-parameter", "-Wno-unused-variable"]
        objects = []
        commands = []
        for index, source in enumerate(sources):
            obj = temp / f"native-{index}.o"
            objects.append(obj)
            commands.append(common + ["-c", str(source), "-o", str(obj)])
        generated_obj = temp / "m1d8e.o"
        objects.append(generated_obj)
        commands.append([compiler, "-std=c11", "-Wall", "-Wextra", "-Werror",
            "-pedantic", "-ffunction-sections", "-fdata-sections", "-I", str(ROOT),
            "-I", str(GEN), "-Wno-unused-parameter", "-Wno-unused-variable",
            "-Wno-conversion", "-c", str(converted), "-o", str(generated_obj)])
        commands.append([compiler, *[str(obj) for obj in objects],
                         "-Wl,--gc-sections", "-o", str(exe)])
        built = None
        for command in commands:
            built = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
            if built.returncode:
                break
        run = None
        if built is not None and built.returncode == 0:
            run = subprocess.run([str(exe)], cwd=ROOT, capture_output=True,
                                 text=True, timeout=20)
        converted_sha = sha(converted)
    after = {str(path.relative_to(ROOT)): sha(path) for path in INPUTS}
    passed = (built is not None and built.returncode == 0 and run is not None and
              run.returncode == 0 and before == after)
    result = {
        "schema": "simant-native-cursor-edge-draw-restore-v1",
        "status": "PASS" if passed else "FAIL",
        "scope": [
            "actual cursor save-under registration and full-size source buffer",
            "show and restore at right+bottom edge on 640x480 indexed framebuffer",
            "source m1D8E half-open full-screen clipping via top=0x8000 sentinel",
            "negative screen-clip guard proves no visible pixels change when disjoint",
            "native control only; DOS pixel equivalence is separately bounded to capture data",
        ],
        "compiler": compiler,
        "commands": commands,
        "converted_root_m1D8E_sha256": converted_sha,
        "inputs_before_sha256": before,
        "inputs_after_sha256": after,
        "inputs_stable": before == after,
        "stdout": run.stdout if run else (built.stdout if built else ""),
        "stderr": run.stderr if run else (built.stderr if built else ""),
        "exit_code": run.returncode if run else (built.returncode if built else None),
    }
    report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(result["status"])
    print(result["stdout"], end="")
    print(result["stderr"], end="")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
