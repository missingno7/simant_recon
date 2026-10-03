"""Write-once native controls for the source m1B73 logical mouse provider."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
INPUTS = [
    "portable/whole_program/platform/m1b73_mouse.c",
    "portable/whole_program/platform/m1b73_mouse.h",
    "portable/whole_program/platform/m1b73_mouse_state.c",
    "portable/whole_program/platform/m1b73_mouse_state.h",
    "portable/whole_program/platform/m1b73_mouse.md",
    "portable/whole_program/platform/sdl3/input_time_host.c",
    "portable/whole_program/platform/sdl3/input_time_host.h",
    "portable/whole_program/platform/input_time.c",
    "portable/whole_program/platform/input_time.h",
    "portable/game/timing.c",
    "portable/game/timing.h",
    "portable/platform/host.h",
    "portable/tests/whole_program/m1b73_mouse_probe.c",
    "portable/tests/whole_program/run_m1b73_mouse_probe.py",
    "src/root/m1B73.asm",
    "src/root/m1B28.c",
    "src/root/m1FD2.c",
    "src/root/m1C62.c",
    "src/S17/m384C.c",
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
        raise SystemExit("refusing to overwrite immutable m1B73 mouse receipt or executable")
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
        "portable/tests/whole_program/m1b73_mouse_probe.c",
        "portable/whole_program/platform/m1b73_mouse.c",
        "portable/whole_program/platform/m1b73_mouse_state.c",
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
        raise SystemExit("m1B73 mouse inputs changed during execution")
    result = {
        "schema": "whole-program-m1b73-mouse-native-v1",
        "status": "PASS" if ran.returncode == 0 else "FAIL",
        "scope": "controlled native provider/alias contract test; no DOS behavioral differential or physical cursor raster equivalence claim",
        "source_anchors": {
            "f_1B73_0025": "src/root/m1B73.asm:239-251",
            "f_1B73_0046": "src/root/m1B73.asm:254-312",
            "f_1B73_00D9": "src/root/m1B73.asm:314-346",
            "f_1B73_01E1": "src/root/m1B73.asm:434-457",
            "f_1B73_0218": "src/root/m1B73.asm:459-468",
            "f_1B73_0235": "src/root/m1B73.asm:481-524",
            "f_1B73_02A9": "src/root/m1B73.asm:526-564",
            "callers": ["src/root/m1B28.c:f_1B28_006A", "src/S17/m384C.c:o17_384C_0000", "src/root/m1C62.c:f_1C62_00A1"],
        },
        "controls": [
            "source 0046 swapped center assignments are retained and warped through identity source/host map",
            "0218 preserves both Mickey-to-pixel ratio words",
            "0235/02A9 save and restore logical NumLock bit, toggle ordered event consumer, and mutate the same source nesting byte",
            "01E1 stores borrowed image/mask pointers after validating their width/height header",
            "00D9 ordered hit-test query FFFFh then render-show callback and source counters/show level",
            "native mouse down/up event query words preserve button status and dispatch hide, hit-test, show order",
            "0025 does not claim DOS IVT behavior; native fallback stub remains absent",
            "missing hit-test/render services fail closed through the helper status; source void entrypoints abort on this error",
        ],
        "retired_hardware": [
            "DOS IVT INT 33h fallback/vector manipulation is not performed",
            "DOS INT 33h/08h/09h/15h hooks are replaced by the application-owned SDL event pump",
            "cursor drawing requires the actual active resource provider and renderer callback; no raster fallback is supplied",
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
