#!/usr/bin/env python3
"""Run actual generated root:m205F startup for the two admitted host profiles."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
GEN = ROOT / "build/workers/whole_program/generated"
INPUTS = [
    ROOT / "src/root/m205F.c",
    ROOT / "src/root/m1B28.c",
    ROOT / "src/S20/m39C7.c",
    GEN / "root_m205F.c",
    GEN / "root_m1B28.c",
    GEN / "S20_m39C7.c",
    ROOT / "portable/whole_program/platform/native_video_profile.h",
    ROOT / "portable/whole_program/platform/native_video_profile.c",
    ROOT / "portable/whole_program/platform/graphics.h",
    ROOT / "portable/whole_program/platform/graphics.c",
    ROOT / "portable/whole_program/platform/graphics_source_clip.h",
    ROOT / "portable/whole_program/platform/graphics_source_clip.c",
    ROOT / "portable/whole_program/platform/graphics_bitmap_source.h",
    ROOT / "portable/whole_program/platform/graphics_bitmap_source.c",
    ROOT / "portable/whole_program/platform/graphics_line_1499.h",
    ROOT / "portable/whole_program/platform/graphics_line_1499.c",
    ROOT / "portable/whole_program/window_source_globals.h",
    ROOT / "portable/whole_program/window_source_rects.h",
    ROOT / "portable/render/primitives.h",
    ROOT / "portable/render/primitives.c",
    HERE / "native_video_startup_test.c",
    HERE / "run_native_video_startup_test.py",
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compiler_subtools(compiler: str) -> dict:
    result = {}
    for name in ("cc1", "collect2", "as", "ld"):
        proc = subprocess.run([compiler, f"-print-prog-name={name}"],
                              capture_output=True, text=True, timeout=10)
        path = Path(proc.stdout.strip())
        result[name] = {"path": str(path),
                        "sha256": sha(path) if path.is_file() else None}
    return result


def extract_empty_source_entries(path: Path, names: tuple[str, ...], out: Path) -> str:
    """Copy only verified empty generated bodies into this focused harness."""
    text = path.read_text(encoding="latin1")
    snippets = []
    for name in names:
        pattern = rf"(?m)^void\s+{re.escape(name)}\s*\(\s*void\s*\)\s*\{{\s*\}}"
        match = re.search(pattern, text)
        if not match:
            raise RuntimeError(f"generated empty body missing or non-empty: {name}")
        snippets.append(match.group(0))
    out.write_text("\n\n".join(snippets) + "\n", encoding="latin1", newline="\n")
    return sha(out)


def run() -> tuple[dict, int]:
    compiler = os.environ.get("CC", "gcc")
    compiler_path = shutil.which(compiler)
    before = {str(p.relative_to(ROOT)): sha(p) for p in INPUTS}
    with tempfile.TemporaryDirectory(prefix="simant-video-startup-") as temp:
        empty_entries = Path(temp) / "source_empty_entries.c"
        empty_entries_sha = extract_empty_source_entries(
            GEN / "S20_m39C7.c",
            ("o20_39C7_0211", "o20_39C7_0005"), empty_entries)
        exe = Path(temp) / "native_video_startup_test.exe"
        command = [
            compiler, "-std=c11", "-Wall", "-Wextra", "-Werror", "-pedantic",
            "-Wno-builtin-declaration-mismatch", "-Wno-char-subscripts",
            "-Wno-implicit-fallthrough",
            "-ffunction-sections", "-fdata-sections", "-I", str(ROOT),
            "-I", str(ROOT / "portable/whole_program"),
            "-I", str(GEN),
            str(GEN / "root_m205F.c"), str(GEN / "root_m1B28.c"),
            str(empty_entries),
            str(ROOT / "portable/whole_program/platform/native_video_profile.c"),
            str(ROOT / "portable/whole_program/platform/graphics.c"),
            str(ROOT / "portable/whole_program/platform/graphics_source_clip.c"),
            str(ROOT / "portable/whole_program/platform/graphics_bitmap_source.c"),
            str(ROOT / "portable/whole_program/platform/graphics_line_1499.c"),
            str(ROOT / "portable/render/primitives.c"),
            str(HERE / "native_video_startup_test.c"),
            "-Wl,--gc-sections", "-o", str(exe),
        ]
        built = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        if built.returncode:
            return ({"command": command, "compile_stdout": built.stdout,
                     "compile_stderr": built.stderr}, built.returncode)
        profiles = {}
        status = 0
        for profile in ("0", "8"):
            result = subprocess.run([str(exe), profile], cwd=ROOT,
                                    capture_output=True, text=True, timeout=20)
            profiles[profile] = {"exit_code": result.returncode,
                                 "stdout": result.stdout, "stderr": result.stderr}
            status |= result.returncode
        exe_hash = sha(exe)
    after = {str(p.relative_to(ROOT)): sha(p) for p in INPUTS}
    return ({"command": command, "compiler": compiler,
             "compiler_resolved_path": compiler_path,
             "compiler_binary_sha256": sha(Path(compiler_path)) if compiler_path else None,
             "compiler_version": subprocess.run([compiler, "--version"], capture_output=True,
                                                  text=True, timeout=10).stdout.splitlines()[:1],
             "compiler_subtools": compiler_subtools(compiler),
             "source_empty_entries_sha256": empty_entries_sha,
             "compile_stdout": built.stdout,
             "compile_stderr": built.stderr, "profiles": profiles,
             "executable_sha256": exe_hash, "inputs_before_sha256": before,
             "inputs_after_sha256": after, "inputs_stable": before == after}, status)


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    details, exit_code = run()
    report = {
        "schema": "simant-native-video-generated-startup-v1",
        "status": "PASS" if exit_code == 0 and details.get("inputs_stable") else "FAIL",
        "scope": "Actual unmodified central generated root:m205F f_205F_0004 and root:m1B28 f_1B28_0006 execute for selected EGA/VGA profiles. Database object load/unhook and S21 descriptor are controlled host boundaries. Unsupported hardware branches trap. This is not DOS equivalence or full graphics-driver support.",
        "selected_profiles": [0, 8],
        "native_only_checks": ["startup order", "database prefix", "cursor object load/unhook sequence", "mode, bounds, and installed supported callbacks"],
        "details": details,
    }
    if args.report:
        if args.report.exists():
            raise SystemExit(f"refusing to overwrite report: {args.report}")
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    for profile, result in details.get("profiles", {}).items():
        print(f"profile {profile}: exit {result['exit_code']}")
        print(result["stdout"], end="")
        print(result["stderr"], end="")
    if "compile_stderr" in details and not details.get("profiles"):
        print(details["compile_stdout"], end="")
        print(details["compile_stderr"], end="")
    print(f"generated native video startup: {report['status']}")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
