"""Run deterministic dual-clock controls without an SDL DLL dependency."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
INPUTS = [
    "portable/whole_program/platform/sdl3/input_time_host.c",
    "portable/whole_program/platform/sdl3/input_time_host.h",
    "portable/whole_program/platform/m1b73_main_input.c",
    "portable/whole_program/platform/m1b73_main_input.h",
    "portable/whole_program/platform/m1b73_events.c",
    "portable/whole_program/platform/m1b73_events.h",
    "portable/whole_program/platform/m1b73_timer_view.c",
    "portable/whole_program/platform/m1b73_timer_view.h",
    "portable/whole_program/types/timer.h",
    "portable/whole_program/platform/input_time.c",
    "portable/whole_program/platform/input_time.h",
    "portable/game/timing.c",
    "portable/game/timing.h",
    "portable/platform/host.h",
    "portable/tests/whole_program/m1b73_dual_clock_native_probe.c",
    "portable/tests/whole_program/run_m1b73_dual_clock_native_probe.py",
    "portable/tests/whole_program/m1b73_dual_clock_probe_sdl_loader_hang.c",
    "portable/tests/whole_program/run_m1b73_dual_clock_probe.py",
    "src/root/m1B73.asm",
    "src/root/m1F58.asm",
    "src/root/m1FD2.c",
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
        raise SystemExit("refusing to overwrite immutable native receipt or executable")
    report.parent.mkdir(parents=True, exist_ok=True)
    output.parent.mkdir(parents=True, exist_ok=True)
    before = {item: sha((ROOT / item).read_bytes()) for item in INPUTS}
    compiler = shutil.which("gcc")
    if compiler is None:
        raise SystemExit("gcc not found")
    version = subprocess.run([compiler, "--version"], cwd=ROOT, check=True,
                             capture_output=True, text=True).stdout.splitlines()[0]
    command = [
        compiler, "-std=c11", "-Wall", "-Wextra", "-Wconversion", "-Werror",
        "-Wno-error=sign-conversion", "-pedantic", "-D__USE_MINGW_SETJMP_NON_SEH",
        "portable/tests/whole_program/m1b73_dual_clock_native_probe.c",
        "portable/whole_program/platform/m1b73_main_input.c",
        "portable/whole_program/platform/m1b73_events.c",
        "portable/whole_program/platform/m1b73_timer_view.c",
        "portable/whole_program/platform/sdl3/input_time_host.c",
        "portable/whole_program/platform/input_time.c",
        "portable/game/timing.c", "-o", str(output),
    ]
    compiled = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    if compiled.returncode:
        raise SystemExit(compiled.stderr)
    ran = subprocess.run([str(output)], cwd=ROOT, capture_output=True, text=True,
                         timeout=10)
    after = {item: sha((ROOT / item).read_bytes()) for item in INPUTS}
    if before != after:
        raise SystemExit("native dual-clock inputs changed during execution")
    result = {
        "schema": "whole-program-m1b73-dual-clock-native-v2",
        "status": "PASS" if ran.returncode == 0 else "FAIL",
        "scope": "deterministic native contract test of real input_time_host/m1b73 providers with fake monotonic source; no SDL DLL, DOS differential, or PIT cadence acceptance claim",
        "controls": [
            "distinct audio-cadence game and BIOS clock objects are required",
            "dual binding forces BIOS counting enabled",
            "source TickCount disabled while elapsed time advances: private count stays fixed and f_1F58_0006 BIOS ticks advance",
            "reenabling private TickCount advances both clocks only for the newly elapsed interval",
            "both clock counters wrap modulo 2^32",
            "same-object and mismatched-cadence dual clock initialization are rejected",
            "test Host pointer is an opaque nonnull token; host interaction functions abort if unexpectedly called",
        ],
        "input_sha256_before": before,
        "input_sha256_after": after,
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
        "prior_sdl_probe_loader_issue": "m1b73_dual_clock_probe_v1.exe and debug build hung without reaching the first statement marker, including with the SDL SDK DLL directory on PATH; this is preserved as a loader/setup issue and is not counted as a semantic failure",
    }
    with report.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(json.dumps({"status": result["status"], "report": str(report),
                      "executable_sha256": result["executable_sha256"]}, indent=2))
    return 0 if ran.returncode == 0 else ran.returncode


if __name__ == "__main__":
    raise SystemExit(main())
