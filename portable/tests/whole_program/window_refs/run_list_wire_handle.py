#!/usr/bin/env python3
"""Exercise actual root:m23E6 List.text accesses through its Handle sidecar."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import time

ROOT = Path(__file__).resolve().parents[4]
GEN = ROOT / "build/workers/whole_program/generated"
HERE = ROOT / "portable/tests/whole_program/window_refs"
CONVERTER = ROOT / "portable/whole_program/conversions/list_text_handle.py"
BASE_SOURCES = [
    "build/workers/whole_program/generated/root_m1986.c",
    "build/workers/whole_program/generated/root_m19A9.c",
    "build/workers/whole_program/generated/root_m19DC.c",
    "build/workers/whole_program/generated/root_m1A28.c",
    "build/workers/whole_program/generated/root_m1A53.c",
    "build/workers/whole_program/generated/root_m1A96.c",
    "build/workers/whole_program/generated/root_m1B28.c",
    "build/workers/whole_program/generated/root_m20E8.c",
    "build/workers/whole_program/generated/root_m23AE.c",
    "build/workers/whole_program/generated/root_m2505.c",
    "portable/whole_program/state/database.c",
    "portable/whole_program/conversions/pointer_globals.c",
    "portable/whole_program/window_source_globals.c",
    "portable/whole_program/window_refs.c",
    "portable/whole_program/window_runtime_owner.c",
    "portable/whole_program/window_list_refs.c",
    "portable/whole_program/platform/handles.c",
    "portable/whole_program/platform/dos_io.c",
    "portable/whole_program/platform/dos_format.c",
    "portable/whole_program/platform/dos_memory.c",
    "portable/whole_program/platform/crt_abi.c",
    "portable/platform/memory.c",
    "portable/whole_program/algorithms/lzss.c",
    "portable/tests/whole_program/window_refs/list_wire_handle_driver.c",
]
INPUTS = [
    *BASE_SOURCES,
    "build/workers/whole_program/generated/root_m23E6.c",
    "build/workers/whole_program/generated/dos_types.h",
    "build/workers/whole_program/generated/migration.json",
    "portable/whole_program/conversions/list_text_handle.py",
    "portable/whole_program/window_refs.h",
    "portable/whole_program/window_runtime_owner.h",
    "portable/whole_program/window_list_refs.h",
    "portable/whole_program/window_source_globals.h",
    "portable/whole_program/window_source_rects.h",
    "portable/whole_program/conversions/pointer_globals.h",
    "portable/whole_program/types/database.h",
    "portable/whole_program/platform/handles.h",
    "portable/whole_program/platform/dos_io.h",
    "portable/whole_program/platform/dos_files.h",
    "portable/whole_program/platform/dos_memory.h",
    "portable/whole_program/platform/dos_format.h",
    "portable/whole_program/platform/crt_abi.h",
    "portable/whole_program/algorithms/lzss.h",
    "portable/tests/whole_program/window_refs/run_list_wire_handle.py",
    "assets/HCEGANT.NDX", "assets/HCEGANT.DAT",
]


def identity(path: Path) -> dict:
    data = path.read_bytes()
    return {"sha256": hashlib.sha256(data).hexdigest(), "size": len(data)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", required=True)
    ap.add_argument("--gcc", default=shutil.which("gcc"))
    args = ap.parse_args()
    report = (ROOT / args.report).resolve()
    if report.exists():
        raise SystemExit(f"refusing to overwrite report: {report}")
    gcc = Path(args.gcc).resolve() if args.gcc else None
    if gcc is None or not gcc.is_file(): raise SystemExit("GCC not found")
    pins_before = {p: identity(ROOT / p) for p in INPUTS}
    spec = importlib.util.spec_from_file_location("list_text_handle_adapter", CONVERTER)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    original = (GEN / "root_m23E6.c").read_text(encoding="utf-8")
    adapted, replacement_count = module.adapt(original)
    work_root = ROOT / "build/workers/behavior_window/list-handle"
    work_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="list-handle-", dir=work_root) as td:
        tmp = Path(td)
        adapted_source = tmp / "root_m23E6_adapted.c"
        adapted_source.write_text(adapted, encoding="utf-8")
        compile_flags = ["-std=c11", "-O0", "-fsigned-char", "-fno-builtin-sprintf",
                         "-ffunction-sections", "-fdata-sections",
                         "-Werror=implicit-function-declaration", "-I", str(ROOT),
                         "-I", str(GEN)]
        def build_and_run(name: str, list_source: Path):
            exe_path = tmp / f"{name}.exe"
            cmdline = [str(gcc), *compile_flags,
                       *(str(ROOT / p) for p in BASE_SOURCES), str(list_source),
                       "-Wl,--gc-sections", "-o", str(exe_path)]
            compile_result = subprocess.run(cmdline, cwd=ROOT, capture_output=True,
                                            text=True, timeout=120)
            if compile_result.returncode:
                raise SystemExit(f"{name} compile failed:\n{compile_result.stderr[-8000:]}")
            run_result = subprocess.run([str(exe_path), str((ROOT / "assets").resolve())],
                                        cwd=ROOT, capture_output=True, text=True, timeout=20)
            return cmdline, compile_result, run_result, identity(exe_path)
        cmd, built, ran, exe_id = build_and_run("list-wire-handle-adapted",
                                                adapted_source)
        if ran.returncode:
            raise SystemExit(f"adapted runtime failed ({ran.returncode}):\n{ran.stdout}\n{ran.stderr}")
    pins_after = {p: identity(ROOT / p) for p in INPUTS}
    if pins_before != pins_after: raise SystemExit("a pinned input changed during the test")
    fields = ran.stdout.strip().split(",")
    if len(fields) != 7 or fields[0] != "LIST" or fields[1:4] != ["5641", "4", "2"] or fields[5] != "Alpha" or fields[6] != "00000000":
        raise SystemExit(f"unexpected List.text observation: {ran.stdout!r}")
    report_doc = {
        "schema": "simant-list-wire-handle-adapter-v1",
        "created_unix_ns": time.time_ns(),
        "result": "PASS",
        "classification": "native actual-source consumer integration; no DOS differential",
        "source_contract": {
            "source": "root:m23E6; List begins at WinObj+0x2a; text is the sixth source word/far Handle at WinObj+0x34",
            "native_hazard": "a host char** is 8 bytes on this target; directly reading/writing struct List.text at wire +0x34 would overwrite bytes +0x38..+0x3b and bypass the Handle sidecar",
            "adapter": "20 source List.text expressions are replaced by an lvalue to sim_window_list_text_slot(list), which resolves only a live type-4/10 +0x34 slot in the sole window registry",
        },
        "fixture": "actual HCEGANT kind-0 window 22, object 9 (type 4, size 56); loaded through generated DB/handle/window services; source win_LoadWindow zeroes its runtime Handle bytes before setter",
        "host_service_limits": {
            "f_24AB_030B": "bounded fixture returns 10 source-font pixels so original list draw updates visible/endOff before line lookup",
            "clip_text_rect_primitives": "test-only no-op callbacks; they are not used as render proof",
            "unsupported_paths": "slider, bitmap, clip drawing, Punt, and unrelated EMS paths abort or fail closed if entered",
        },
        "adapter_replacements": replacement_count,
        "observation": ran.stdout.strip(),
        "compile_command": cmd,
        "compile_stdout": built.stdout,
        "compile_stderr": built.stderr,
        "executable": exe_id,
        "inputs_before": pins_before,
        "inputs_after": pins_after,
    }
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(report_doc, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report": report.relative_to(ROOT).as_posix(), "result": "PASS",
                      "adapter_replacements": replacement_count,
                      "exe_sha256": exe_id["sha256"]}))
    return 0


if __name__ == "__main__": raise SystemExit(main())
