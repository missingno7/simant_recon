"""Immutable native controls for m1B73's two remaining queue operations."""
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
    "src/S26/m39C7.c",
    "src/S19/m384C.c",
    "src/S10/m35F5.c",
    "portable/whole_program/platform/m1b73_queue_source.c",
    "portable/whole_program/platform/m1b73_queue_source.h",
    "portable/whole_program/platform/m1b73_queues.c",
    "portable/whole_program/platform/m1b73_queues.h",
    "portable/whole_program/platform/m1b73_events.c",
    "portable/whole_program/platform/m1b73_events.h",
    "portable/whole_program/platform/m1b73_event_enqueue.h",
    "portable/whole_program/platform/sdl3/input_time_host.h",
    "portable/whole_program/platform/input_time.h",
    "portable/platform/host.h",
    "portable/game/timing.h",
    "portable/whole_program/types/timer.h",
    "portable/tests/whole_program/m1b73_queue_operations_probe.c",
    "portable/tests/whole_program/run_m1b73_queue_operations_probe.py",
    "portable/whole_program/conversions/m1b73_queue_source.py",
    "portable/whole_program/conversions/m1b73_event_source.py",
    "portable/tests/whole_program/test_m1b73_queue_source_lexing.py",
    "portable/tests/whole_program/test_m1b73_event_source.py",
]


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--exe", required=True, type=Path)
    args = parser.parse_args()
    report = args.report if args.report.is_absolute() else ROOT / args.report
    exe = args.exe if args.exe.is_absolute() else ROOT / args.exe
    if report.exists() or exe.exists():
        raise SystemExit("refusing to overwrite queue operation evidence")
    report.parent.mkdir(parents=True, exist_ok=True)
    exe.parent.mkdir(parents=True, exist_ok=True)
    before = {path: digest((ROOT / path).read_bytes()) for path in INPUTS}

    lexical = subprocess.run(
        [shutil.which("python") or "python", "portable/tests/whole_program/test_m1b73_queue_source_lexing.py"], cwd=ROOT,
        capture_output=True, text=True, timeout=20)
    callsites = subprocess.run(
        [shutil.which("python") or "python", "portable/tests/whole_program/test_m1b73_event_source.py"], cwd=ROOT,
        capture_output=True, text=True, timeout=20)
    compiler_name = shutil.which("gcc")
    if compiler_name is None:
        raise SystemExit("gcc not found")
    compiler = Path(compiler_name).resolve()
    compiler_version = subprocess.run(
        [str(compiler), "--version"], cwd=ROOT, check=True,
        capture_output=True, text=True).stdout.splitlines()[0]
    command = [
        str(compiler), "-std=c11", "-Wall", "-Wextra", "-Wconversion",
        "-Werror", "-Wno-error=sign-conversion", "-pedantic",
        "-D__USE_MINGW_SETJMP_NON_SEH",
        "-I", str(ROOT / "build/sdl3-sdk/SDL3-3.4.16/x86_64-w64-mingw32/include"),
        "portable/tests/whole_program/m1b73_queue_operations_probe.c",
        "portable/whole_program/platform/m1b73_queue_source.c",
        "portable/whole_program/platform/m1b73_queues.c",
        "portable/whole_program/platform/m1b73_events.c",
        "-o", str(exe),
    ]
    build = subprocess.run(command, cwd=ROOT, capture_output=True,
                           text=True, timeout=40)
    run = None
    if build.returncode == 0 and lexical.returncode == 0 and callsites.returncode == 0:
        run = subprocess.run([str(exe)], cwd=ROOT, capture_output=True,
                             text=True, timeout=20)
    after = {path: digest((ROOT / path).read_bytes()) for path in INPUTS}
    calls = {
        "src/S19/m384C.c": {"four_word": 1, "five_word": 1},
        "src/S10/m35F5.c": {"four_word": 2, "five_word": 1},
    }
    passed = (lexical.returncode == 0 and callsites.returncode == 0 and build.returncode == 0 and
              run is not None and run.returncode == 0 and before == after)
    payload = {
        "schema": "whole-program-m1b73-queue-operations-v1",
        "status": "PASS_TYPED_NATIVE_CONTROLS" if passed else "FAIL",
        "scope": "native typed provider controls; no DOS execution or source-module whole-program run",
        "inputs": before,
        "inputs_unchanged_during_run": before == after,
        "compiler": {
            "path": str(compiler), "sha256": digest(compiler.read_bytes()),
            "version": compiler_version, "command": command,
        },
        "lexical_rewrite_control": {
            "exit_code": lexical.returncode,
            "stdout": lexical.stdout, "stderr": lexical.stderr,
            "covers": "identifiers in C code change while comments and string/character literals remain untouched",
        },
        "source_callsite_adapter_control": {
            "exit_code": callsites.returncode,
            "stdout": callsites.stdout, "stderr": callsites.stderr,
            "covers": "actual frozen S19 and S10 source callsites, four/five word split, and removal of the old-style declaration",
        },
        "native_build": {
            "exit_code": build.returncode,
            "stdout": build.stdout, "stderr": build.stderr,
        },
        "native_run": None if run is None else {
            "exit_code": run.returncode,
            "stdout": run.stdout, "stderr": run.stderr,
            "exe_sha256": digest(exe.read_bytes()),
        },
        "source_callsite_inventory": calls,
        "controls": {
            "f_1B73_0C42": [
                "typed native Rect* output receives words +0,+2,+4,+6 on found ID",
                "not-found returns zero and leaves all output words unchanged",
            ],
            "f_1B73_030F": [
                "five explicit int16_t words map BX,ES,AX,CX,DX into original event fields",
                "four-word command helper supplies DX=0 only for audited command consumers that do not read Event.v",
            ],
        },
        "four_word_event_v_audit": {
            "src/S19/m384C.c": "the four-word calls enqueue command codes; o19_384C_0000 dispatches on ev.code, and ProcMenu/o19_384C_0383 read code/message only; no event.v reads in the TU",
            "src/S10/m35F5.c": "the two four-word calls are command/selection returns; o10_35F5_0384 checks ev.code, with no ev.v reads in this TU",
            "limit": "source-consumer audit only; not a whole-program reachability proof and not DOS stack-value equivalence",
        },
        "limitations": [
            "Native tests use typed providers and controlled BIOS modifiers/ticks; no original DOS runner was executed.",
            "The missing fifth stack word at four-word DOS callsites is not recovered; the named native helper sets only the consumer-unobserved Event.v to zero.",
            "f_1B73_0C42 far-pointer mechanics are replaced by a native Rect* at the source wrapper boundary; DOS segmented pointer behavior is not emulated.",
        ],
    }
    report.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": payload["status"], "report": str(report)}, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
