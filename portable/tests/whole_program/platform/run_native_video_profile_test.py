#!/usr/bin/env python3
"""Build the bounded native host-selected video-profile provider contract."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
INPUTS = [
    ROOT / "portable/whole_program/platform/native_video_profile.h",
    ROOT / "portable/whole_program/platform/native_video_profile.c",
    ROOT / "portable/whole_program/platform/graphics.h",
    ROOT / "portable/whole_program/platform/graphics.c",
    ROOT / "portable/whole_program/platform/graphics_source_clip.h",
    ROOT / "portable/whole_program/platform/graphics_source_clip.c",
    ROOT / "portable/whole_program/platform/graphics_line_1499.h",
    ROOT / "portable/whole_program/platform/graphics_line_1499.c",
    ROOT / "portable/render/primitives.h",
    ROOT / "portable/render/primitives.c",
    HERE / "native_video_profile_test.c",
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    compiler = os.environ.get("CC", "gcc")
    before = {str(path.relative_to(ROOT)): sha(path) for path in INPUTS}
    with tempfile.TemporaryDirectory(prefix="simant-native-video-profile-") as temp:
        exe = Path(temp) / "native_video_profile_test.exe"
        command = [
            compiler, "-std=c11", "-Wall", "-Wextra", "-Werror", "-pedantic",
            "-I", str(ROOT),
            "-I", str(ROOT / "portable/whole_program"),
            str(ROOT / "portable/whole_program/platform/native_video_profile.c"),
            str(ROOT / "portable/whole_program/platform/graphics.c"),
            str(ROOT / "portable/whole_program/platform/graphics_source_clip.c"),
            str(ROOT / "portable/whole_program/platform/graphics_line_1499.c"),
            str(ROOT / "portable/render/primitives.c"),
            str(HERE / "native_video_profile_test.c"), "-o", str(exe),
        ]
        built = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        if built.returncode != 0:
            print(built.stdout, end="")
            print(built.stderr, end="")
            return built.returncode
        run = subprocess.run([str(exe)], cwd=ROOT, capture_output=True, text=True,
                             timeout=20)
        exe_hash = sha(exe)
    after = {str(path.relative_to(ROOT)): sha(path) for path in INPUTS}
    report = {
        "schema": "simant-native-video-profile-contract-v1",
        "status": "PASS" if run.returncode == 0 and before == after else "FAIL",
        "scope": "Native host-intent descriptor and public source-mode adapter only; no DOS hardware detection, BIOS emulation, or full f_205F startup proof.",
        "profiles": {
            "EGA profile 0": {"source descriptor": "adapter 3/display 3 (0x0303)",
                              "source mode": "INT 10h 0x10"},
            "VGA profile 8": {"source descriptor": "adapter 5/display 3 (0x0305)",
                              "source mode": "INT 10h 0x12"},
            "unsupported": "source profile indices 1..7 and values outside the two admitted profiles are rejected",
        },
        "inputs_before_sha256": before,
        "inputs_after_sha256": after,
        "inputs_stable": before == after,
        "command": command,
        "compiler": compiler,
        "executable_sha256": exe_hash,
        "compile_stdout": built.stdout,
        "compile_stderr": built.stderr,
        "run_stdout": run.stdout,
        "run_stderr": run.stderr,
        "exit_code": run.returncode,
    }
    if args.report is not None:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        if args.report.exists():
            raise SystemExit(f"refusing to overwrite report: {args.report}")
        args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(run.stdout, end="")
    print(f"native video profile contract runner: {report['status']}")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
