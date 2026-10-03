"""Build and run the source-event/timer SDL boundary probe."""
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
    "portable/tests/whole_program/m1b73_event_probe.c",
    "portable/tests/whole_program/run_m1b73_event_probe.py",
    "src/root/m1B73.asm",
    "src/root/m1FD2.c",
    "src/root/m1F58.asm",
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
        raise SystemExit("refusing to overwrite native event receipt or executable")
    report.parent.mkdir(parents=True, exist_ok=True)
    output.parent.mkdir(parents=True, exist_ok=True)
    before = {item: sha((ROOT / item).read_bytes()) for item in INPUTS}
    timer_source = (ROOT / "src/root/m1FD2.c").read_text(encoding="utf-8")
    adapted_timer_source, timer_ledger = adapt_timer_source(timer_source)
    compiler = shutil.which("gcc")
    if compiler is None:
        raise SystemExit("gcc not found")
    compiler_version = subprocess.run([compiler, "--version"], cwd=ROOT,
        check=True, capture_output=True, text=True).stdout.splitlines()[0]
    command = [
        compiler, "-std=c11", "-Wall", "-Wextra", "-Wconversion", "-Werror",
        "-Wno-error=sign-conversion", "-pedantic", "-D__USE_MINGW_SETJMP_NON_SEH",
        "-I", str(SDK / "include"),
        "portable/tests/whole_program/m1b73_event_probe.c",
        "portable/whole_program/platform/m1b73_events.c",
        "portable/whole_program/platform/m1b73_timer_view.c",
        "portable/whole_program/platform/sdl3/input_time_host.c",
        "portable/whole_program/platform/input_time.c",
        "portable/game/timing.c", "portable/platform/sdl3/host.c",
        "-L", str(SDK / "lib"), "-lSDL3", "-o", str(output),
    ]
    compile_result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    if compile_result.returncode != 0:
        raise SystemExit(compile_result.stderr)
    env = os.environ.copy()
    env["PATH"] = str(SDK / "bin") + os.pathsep + env.get("PATH", "")
    env["SDL_VIDEODRIVER"] = "dummy"
    execution = subprocess.run([str(output)], cwd=ROOT, env=env,
                               capture_output=True, text=True)
    after = {item: sha((ROOT / item).read_bytes()) for item in INPUTS}
    if before != after:
        raise SystemExit("input changed during event probe run")
    report_data = {
        "schema": "whole-program-m1b73-native-boundary-v1",
        "status": "PASS" if execution.returncode == 0 else "FAIL",
        "scope": "native SDL dummy-driver controls only; no DOS oracle was run",
        "contracts": [
            "typed Timer queue aliases use g_5FF2.r.left/top/right and g_5FF0",
            "event records use separately supplied native storage; DOS ring offset 0x91B0 is not dereferenced",
            "m1B73 TickCount is the application SimTimingClock counter; enqueue x4 reads f_1F58_0006 BIOS ticks",
            "SDL HostEvent order is consumed through PortableInputTimeHost; mouse events are not converted into DOS Event records",
            "event fields, one-slot-reserved ring, shift_state bit handling, and empty dequeue return are checked by the native fixture",
        ],
        "input_sha256_before": before,
        "input_sha256_after": after,
        "timer_conversion": timer_ledger,
        "adapted_m1FD2_sha256": sha(adapted_timer_source.encode("utf-8")),
        "compiler": {"path": compiler, "sha256": sha(Path(compiler).read_bytes()),
                     "version": compiler_version},
        "compile_command": command,
        "compile_stderr": compile_result.stderr,
        "executable": str(output.relative_to(ROOT)),
        "executable_sha256": sha(output.read_bytes()),
        "execution_returncode": execution.returncode,
        "execution_stdout": execution.stdout,
        "execution_stderr": execution.stderr,
        "executed_output_sha256": sha(execution.stdout.encode("utf-8") +
                                      execution.stderr.encode("utf-8")),
    }
    with report.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(report_data, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(json.dumps({"status": report_data["status"], "report": str(report),
                      "executable_sha256": report_data["executable_sha256"]}, indent=2))
    return 0 if execution.returncode == 0 else execution.returncode


if __name__ == "__main__":
    raise SystemExit(main())
