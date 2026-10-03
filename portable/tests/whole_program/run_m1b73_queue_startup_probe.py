#!/usr/bin/env python3
"""Write-once native controls for ASM queue init and real S17 startup caller."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
INPUTS = [
    "src/root/m1B73.asm",
    "src/root/m1FD2.c",
    "src/S17/m384C.c",
    "portable/whole_program/types/timer.h",
    "portable/whole_program/platform/m1b73_queues.h",
    "portable/whole_program/platform/m1b73_queues.c",
    "portable/whole_program/platform/m1b73_mouse_state.h",
    "portable/whole_program/platform/m1b73_mouse_state.c",
    "portable/tests/whole_program/m1b73_queue_startup_probe.c",
    "portable/tests/whole_program/run_m1b73_queue_startup_probe.py",
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
        raise SystemExit("refusing to overwrite immutable queue startup report or executable")
    report.parent.mkdir(parents=True, exist_ok=True)
    output.parent.mkdir(parents=True, exist_ok=True)
    before = {item: sha((ROOT / item).read_bytes()) for item in INPUTS}
    compiler = shutil.which("gcc")
    if compiler is None:
        raise SystemExit("gcc not found")
    version = subprocess.run([compiler, "--version"], cwd=ROOT, check=True,
                             capture_output=True, text=True).stdout.splitlines()[0]
    command = [
        compiler, "-std=c11", "-Wall", "-Wextra", "-Wconversion",
        "-Wno-sign-conversion", "-pedantic", "-D__USE_MINGW_SETJMP_NON_SEH",
        "-ffunction-sections", "-fdata-sections",
        "portable/tests/whole_program/m1b73_queue_startup_probe.c",
        "portable/whole_program/platform/m1b73_queues.c",
        "portable/whole_program/platform/m1b73_mouse_state.c",
        "-Wl,--gc-sections", "-o", str(output),
    ]
    compiled = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    if compiled.returncode:
        raise SystemExit(compiled.stderr)
    ran = subprocess.run([str(output)], cwd=ROOT, capture_output=True,
                         text=True, timeout=10)
    after = {item: sha((ROOT / item).read_bytes()) for item in INPUTS}
    if before != after:
        raise SystemExit("queue startup probe inputs changed during execution")
    result = {
        "schema": "whole-program-m1b73-queue-startup-native-v1",
        "status": "PASS" if ran.returncode == 0 else "FAIL",
        "scope": "native contract controls for f_1B73_0AA3/f_1B73_0CB3, including the actual src/S17/m384C.c o17_384C_0000 caller; startup's other services are ordered test providers; no DOS event-loop or hardware emulation claim",
        "source_anchors": {
            "queue_data": "src/root/m1B73.asm:122-151",
            "queue_initializer": "src/root/m1B73.asm:f_1B73_0AA3",
            "dispatcher": "src/root/m1B73.asm:f_1B73_0CB3/f_1B73_0CEF",
            "actual_startup_caller": "src/S17/m384C.c:o17_384C_0000",
            "canonical_timer_owner": "src/root/m1FD2.c g_5FF2; typed in portable/whole_program/types/timer.h",
        },
        "controls": [
            "source-derived queue counts, capacities, row extents, and descriptor masks",
            "actual o17_384C_0000 call order reaches f0AA3 before the 0x10/0x10 mouse-ratio provider, which inspects canonical Timer state",
            "f0AA3 clears only Queue0 and fd_5071_0060 count; other queue counts are sentinels and must remain intact",
            "Timer.r.bottom receives the source byte pair 00h/1Fh through typed member value 1F00h, and Timer.fn receives f0CB3",
            "dispatcher source-order filter uses descriptor mask, signed inclusive rectangle, full status condition, per-queue callback stop/continue behavior, and a callback-mutated coordinate positive control proves shared state reload",
            "opaque far callback bytes are not cast; a matching record without an explicit native resolver returns PROVIDER_MISSING",
            "bad native count bounds fail explicitly instead of reading beyond typed record storage",
            "the ASM-owned g_9120 word is read through an explicit low-byte accessor for C code that historically declared only unsigned char",
        ],
        "limitations": [
            "The actual S17 startup function is compiled from source with 16-bit int and far/near keyword mappings; adjacent startup dependencies are controlled observers, not full platform services.",
            "The callback resolver owns application-specific function-pointer resolution and side effects; no DOS far call, interrupt timing, raw 18-byte far-queue address, or physical mouse hardware is emulated.",
            "No original DOS differential was run in this focused provider test.",
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
    }
    with report.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(json.dumps({"status": result["status"], "report": str(report),
                      "executable_sha256": result["executable_sha256"]}, indent=2))
    return 0 if ran.returncode == 0 else ran.returncode


if __name__ == "__main__":
    raise SystemExit(main())
