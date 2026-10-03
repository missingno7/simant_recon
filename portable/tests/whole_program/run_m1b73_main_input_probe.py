"""Run a write-once native probe of source C input aliases and main binding."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from portable.whole_program.conversions.timer import adapt as adapt_timer_source  # noqa: E402

SDK = ROOT / "build/sdl3-sdk/SDL3-3.4.16/x86_64-w64-mingw32"
INPUTS = [
    "portable/whole_program/platform/m1b73_main_input.c",
    "portable/whole_program/platform/m1b73_main_input.h",
    "portable/whole_program/platform/m1b73_events.md",
    "portable/whole_program/platform/m1b73_events.c",
    "portable/whole_program/platform/m1b73_events.h",
    "portable/whole_program/platform/m1b73_timer_view.c",
    "portable/whole_program/platform/m1b73_timer_view.h",
    "portable/whole_program/types/timer.h",
    "portable/whole_program/conversions/timer.py",
    "portable/whole_program/platform/sdl3/input_time_host.c",
    "portable/whole_program/platform/sdl3/input_time_host.h",
    "portable/whole_program/platform/input_time.c",
    "portable/whole_program/platform/input_time.h",
    "portable/game/timing.c",
    "portable/game/timing.h",
    "portable/platform/sdl3/host.c",
    "portable/platform/host.h",
    "portable/tests/whole_program/m1b73_main_input_probe.c",
    "portable/tests/whole_program/run_m1b73_main_input_probe.py",
    "src/root/m1B73.asm",
    "src/root/m1FD2.c",
    "src/root/m1F58.asm",
    "src/S10/m35F5.c",
    "src/S19/m384C.c",
]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--exe", required=True, type=Path)
    args = parser.parse_args()
    report = args.report if args.report.is_absolute() else ROOT / args.report
    output = args.exe if args.exe.is_absolute() else ROOT / args.exe
    if report.exists() or output.exists():
        raise SystemExit("refusing to overwrite immutable main-input receipt or executable")
    report.parent.mkdir(parents=True, exist_ok=True)
    output.parent.mkdir(parents=True, exist_ok=True)
    before = {item: sha((ROOT / item).read_bytes()) for item in INPUTS}
    adapted_timer, timer_ledger = adapt_timer_source(
        (ROOT / "src/root/m1FD2.c").read_text(encoding="utf-8"))
    compiler = shutil.which("gcc")
    if compiler is None:
        raise SystemExit("gcc not found")
    version = subprocess.run([compiler, "--version"], cwd=ROOT, check=True,
                             capture_output=True, text=True).stdout.splitlines()[0]
    command = [
        compiler, "-std=c11", "-Wall", "-Wextra", "-Wconversion", "-Werror",
        "-Wno-error=sign-conversion", "-pedantic", "-D__USE_MINGW_SETJMP_NON_SEH",
        "-I", str(SDK / "include"),
        "portable/tests/whole_program/m1b73_main_input_probe.c",
        "portable/whole_program/platform/m1b73_main_input.c",
        "portable/whole_program/platform/m1b73_events.c",
        "portable/whole_program/platform/m1b73_timer_view.c",
        "portable/whole_program/platform/sdl3/input_time_host.c",
        "portable/whole_program/platform/input_time.c",
        "portable/game/timing.c", "portable/platform/sdl3/host.c",
        "-L", str(SDK / "lib"), "-lSDL3", "-o", str(output),
    ]
    compiled = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    if compiled.returncode != 0:
        raise SystemExit(compiled.stderr)
    env = os.environ.copy()
    env["PATH"] = str(SDK / "bin") + os.pathsep + env.get("PATH", "")
    env["SDL_VIDEODRIVER"] = "dummy"
    ran = subprocess.run([str(output)], cwd=ROOT, env=env,
                         capture_output=True, text=True)
    after = {item: sha((ROOT / item).read_bytes()) for item in INPUTS}
    if before != after:
        raise SystemExit("main-input probe inputs changed during execution")
    result = {
        "schema": "whole-program-m1b73-main-input-native-v1",
        "status": "PASS" if ran.returncode == 0 else "FAIL",
        "scope": "native SDL dummy-driver binding control; not a DOS differential or full hardware mouse emulation",
        "covered_source_exports": [
            "TickCount", "f_1B73_032A", "f_1B73_032E", "f_1B73_0511",
            "f_1B73_0518", "f_1B73_0A30", "f_1B73_0EEE",
        ],
        "source_callers": [
            "src/S10/m35F5.c:o10_35F5_0384 consumes f_1B73_032A/f_1B73_032E",
            "src/S19/m384C.c:o19_384C_0246 uses f_1B73_0A30 and posts source commands via f_1B73_030F",
            "src/root/m1FD2.c owns g_5FF2 Timer and g_5FF0 ring capacity",
        ],
        "hardware_retirement": [
            "INT 33h registration/callback delivery in m1B73 f_0235/f_03EE/f_0445 is not installed or synthesized",
            "cursor save-under/display callback and hot-box processing remain unprovided; SDL mouse transitions remain ordered HostEvents",
            "f_1B73_030F caller-specific far stack form is not aliased as a variadic native C function",
        ],
        "input_sha256_before": before,
        "input_sha256_after": after,
        "timer_conversion": timer_ledger,
        "adapted_m1FD2_sha256": sha(adapted_timer.encode("utf-8")),
        "compiler": {"path": compiler, "sha256": sha(Path(compiler).read_bytes()),
                     "version": version},
        "compile_command": command,
        "compile_stderr": compiled.stderr,
        "executable": str(output.relative_to(ROOT)),
        "executable_sha256": sha(output.read_bytes()),
        "execution_returncode": ran.returncode,
        "execution_stdout": ran.stdout,
        "execution_stderr": ran.stderr,
        "executed_output_sha256": sha(ran.stdout.encode() + ran.stderr.encode()),
    }
    with report.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(json.dumps({"status": result["status"], "report": str(report),
                      "executable_sha256": result["executable_sha256"]}, indent=2))
    return 0 if ran.returncode == 0 else ran.returncode


if __name__ == "__main__":
    raise SystemExit(main())
