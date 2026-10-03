#!/usr/bin/env python3
"""Compile pinned original C caller bodies against the explicit no-EMS host API."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[4]
GCC_DEFAULT = Path(r"C:\msys64\mingw64\bin\gcc.exe")
MARKER = "/* RUNNER_INSERTS_ACTUAL_CALLER_FUNCTIONS_HERE */"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def function_body(source: str, signature: str) -> str:
    occurrences = []
    offset = 0
    while True:
        start = source.find(signature, offset)
        if start < 0: break
        after = start + len(signature)
        while after < len(source) and source[after].isspace(): after += 1
        if after < len(source) and source[after] == "{": occurrences.append(start)
        offset = start + 1
    if len(occurrences) != 1:
        raise ValueError(f"expected one exact caller definition for {signature}")
    start = occurrences[0]
    brace = source.index("{", start)
    depth = 0
    for i in range(brace, len(source)):
        if source[i] == "{": depth += 1
        elif source[i] == "}":
            depth -= 1
            if depth == 0:
                return source[start:i + 1]
    raise ValueError(f"unterminated function: {signature}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--gcc", default=str(GCC_DEFAULT))
    args = ap.parse_args()
    out = (ROOT / args.out).resolve()
    workers = (ROOT / "build/workers").resolve()
    if workers not in out.parents or out.exists():
        raise SystemExit("--out must be a new directory below build/workers")
    out.mkdir(parents=True)
    gcc = Path(args.gcc).resolve()
    if not gcc.is_file(): raise SystemExit(f"missing compiler {gcc}")
    gcc_before = sha(gcc)
    version_before = subprocess.run([str(gcc), "--version"], check=True,
                                    capture_output=True, text=True).stdout.splitlines()[0]
    pins = [
        "src/root/m195A.asm", "src/root/m0250.c", "src/root/m19DC.c",
        "portable/whole_program/platform/ems_host.h",
        "portable/whole_program/platform/ems_host.c",
        "portable/whole_program/platform/ems_dos_abi.h",
        "portable/whole_program/platform/ems_dos_abi.c",
        "portable/whole_program/platform/dos_io.h",
        "portable/whole_program/platform/dos_io.c",
        "portable/whole_program/platform/tests/ems_noems_callers_test.c",
        "portable/whole_program/platform/tests/run_ems_noems_tests.py",
        "assets/SHARED.DAT", "layout/oracle.lock.json",
    ]
    before = {p: sha(ROOT / p) for p in pins}
    asm = (ROOT / "src/root/m195A.asm").read_text()
    asm_functions = [
        "_f_195A_000C", "_f_195A_001D", "_f_195A_0035", "_f_195A_004B",
        "_f_195A_0062", "_f_195A_007D", "_f_195A_00F8", "_f_195A_010D",
        "_f_195A_0122", "_f_195A_01CB", "_f_195A_0260",
    ]
    if not all(name in asm for name in asm_functions):
        raise SystemExit("m195A assembly API anchors changed")
    m0250 = (ROOT / "src/root/m0250.c").read_text()
    m19dc = (ROOT / "src/root/m19DC.c").read_text()
    bodies = [
        function_body(m0250, "int far f_0250_012D(void)"),
        function_body(m19dc, "int far f_19DC_001A(long size)"),
        function_body(m19dc, "int far f_19DC_02FB(int file, long offset, char far *buffer, long count)"),
    ]
    test = (ROOT / "portable/whole_program/platform/tests/ems_noems_callers_test.c").read_text()
    if test.count(MARKER) != 1: raise SystemExit("caller insertion point changed")
    generated = test.replace(MARKER, "\n\n".join(bodies), 1)
    generated_path = out / "ems_noems_actual_callers.c"
    generated_path.write_text(generated)
    compile_cmd = [
        str(gcc), "-std=c11", "-Dfar=", "-Dnear=", "-D_fastcall=",
        "-Wall", "-Wextra", "-Werror", "-Wno-return-type", "-Wno-unused-variable",
        "-Wno-sign-compare",
        "-I", str(ROOT / "portable/whole_program/platform"),
        str(generated_path),
        str(ROOT / "portable/whole_program/platform/ems_host.c"),
        str(ROOT / "portable/whole_program/platform/ems_dos_abi.c"),
        str(ROOT / "portable/whole_program/platform/dos_io.c"),
        "-o", str(out / "ems_noems_callers_test.exe"),
    ]
    build = subprocess.run(compile_cmd, cwd=ROOT, capture_output=True, text=True)
    (out / "compile.stdout.txt").write_text(build.stdout)
    (out / "compile.stderr.txt").write_text(build.stderr)
    if build.returncode: raise SystemExit(f"native compile failed ({build.returncode})")
    run = subprocess.run([str(out / "ems_noems_callers_test.exe")], cwd=ROOT,
                         capture_output=True, text=True)
    (out / "run.stdout.txt").write_text(run.stdout)
    (out / "run.stderr.txt").write_text(run.stderr)
    if run.returncode: raise SystemExit(f"native no-EMS test failed ({run.returncode})")
    nonreturn_controls = {}
    for operation in ("frame", "pages", "allocate", "map", "free", "save",
                      "restore", "map-list", "name"):
        fault = subprocess.run([str(out / "ems_noems_callers_test.exe"), operation],
                                cwd=ROOT, capture_output=True, text=True)
        nonreturn_controls[operation] = {
            "returned_nonzero": fault.returncode != 0,
            "returncode": fault.returncode,
        }
        if fault.returncode in (0, 91):
            raise SystemExit(f"EMS operation {operation} did not fail nonreturn")
    (out / "nonreturn.stdout.txt").write_text("")
    (out / "nonreturn.stderr.txt").write_text("")
    after = {p: sha(ROOT / p) for p in pins}
    if before != after: raise SystemExit("pinned source or asset changed during run")
    gcc_after = sha(gcc)
    version_after = subprocess.run([str(gcc), "--version"], check=True,
                                   capture_output=True, text=True).stdout.splitlines()[0]
    if gcc_before != gcc_after or version_before != version_after:
        raise SystemExit("compiler identity changed during run")
    receipt = {
        "schema": "native-ems-noems-caller-contract-v2",
        "status": "PASS",
        "source_pins_before_after": before,
        "source_pins_stable": True,
        "extracted_caller_body_sha256": {
            "f_0250_012D": hashlib.sha256(bodies[0].encode()).hexdigest(),
            "f_19DC_001A": hashlib.sha256(bodies[1].encode()).hexdigest(),
            "f_19DC_02FB": hashlib.sha256(bodies[2].encode()).hexdigest(),
        },
        "assembled_api_anchors": asm_functions,
        "gcc": {"path": str(gcc), "sha256_before": gcc_before,
                "sha256_after": gcc_after, "version_before": version_before,
                "version_after": version_after, "stable": True},
        "controls": {
            "public_f_195A_0260_returns_zero_and_exports_initialized_null_dgroup_state": True,
            "capability_probe_unavailable_and_zeroes_fields": True,
            "page_and_frame_queries_unavailable_and_zero_outputs": True,
            "alloc_map_free_and_name_operations_fail_explicitly": True,
            "invalid_handles_and_arguments_distinguished": True,
            "actual_m0250_tile_ems_gate_returns_noems_fallback": True,
            "actual_m19dc_ems_cache_gate_returns_plain_path": True,
            "actual_m19dc_plain_file_read_matches_same_file_bytes": True,
            "no_ems_map_or_page_cache_path_reached": True,
            "public_device_operations_fail_nonreturn": nonreturn_controls,
        },
        "oracle_service_note": "No fresh Unicorn DOS INT 21h/67h run: tools/behavior.py deliberately rejects unmodeled interrupts. The no-device file-open failure path is source-traced from m195A.asm; no EMS interrupt result is invented.",
        "claim_limit": "Native no-EMS host contract, public adapter entry points, and actual caller fallback only; not EMS hardware emulation or a DOS differential claim.",
    }
    (out / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
