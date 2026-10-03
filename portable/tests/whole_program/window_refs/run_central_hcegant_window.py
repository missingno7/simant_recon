#!/usr/bin/env python3
"""Load one real HCEGANT window through the original DB/handle/window bodies.

The test builds generated source TUs against the existing whole-program DB,
handle, DOS-file and window-reference owners.  It does not substitute a
PortableDatabase loader or a fake resource/handle callback.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
import time

ROOT = Path(__file__).resolve().parents[4]
GEN = ROOT / "build/workers/whole_program/generated"
SOURCES = [
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
    "portable/whole_program/platform/handles.c",
    "portable/whole_program/platform/dos_io.c",
    "portable/whole_program/platform/dos_format.c",
    "portable/whole_program/platform/dos_memory.c",
    "portable/whole_program/platform/crt_abi.c",
    "portable/platform/memory.c",
    "portable/whole_program/algorithms/lzss.c",
    "portable/tests/whole_program/window_refs/central_hcegant_window_driver.c",
]
DEPENDENCIES = [
    *SOURCES,
    "build/workers/whole_program/generated/dos_types.h",
    "build/workers/whole_program/generated/migration.json",
    "portable/whole_program/window_refs.h",
    "portable/whole_program/window_runtime_owner.h",
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
    "portable/tests/whole_program/window_refs/run_central_hcegant_window.py",
    "assets/HCEGANT.NDX", "assets/HCEGANT.DAT",
]


def file_id(path: Path) -> dict:
    data = path.read_bytes()
    return {"sha256": hashlib.sha256(data).hexdigest(), "size": len(data)}


def expected_window0() -> dict:
    index = (ROOT / "assets/HCEGANT.NDX").read_bytes()
    data = (ROOT / "assets/HCEGANT.DAT").read_bytes()
    rows = struct.unpack_from("<H", index, 0)[0]
    found = []
    for row in range(rows):
        offset, ident, kind, flags = struct.unpack_from("<IhBB", index, 20 + 8 * row)
        if ident == 0 and kind == 0 and flags & 8:
            found.append(offset)
    if len(found) != 1:
        raise RuntimeError("expected exactly one active HCEGANT window-0 index row")
    header = 14 + found[0]
    stored = struct.unpack_from("<H", data, header + 6)[0]
    payload = data[header + 10:header + 10 + stored]
    if len(payload) != stored or len(payload) < 0x30:
        raise RuntimeError("HCEGANT window-0 payload truncated")
    count = struct.unpack_from("<H", payload, 0x0c)[0]
    cursor = 0x2c + count * 4
    objects = []
    for i in range(count):
        size = struct.unpack_from("<h", payload, cursor + 0x22)[0]
        if size < 0x28 or cursor + size > len(payload):
            raise RuntimeError(f"invalid window object {i} in independent parser")
        objects.append([i, cursor, payload[cursor + 0x21], size])
        cursor += size
    if cursor > len(payload):
        raise RuntimeError("window object sequential walk exceeds actual payload")
    return {"payload_size": len(payload), "count": count, "objects": objects,
            "payload_sha256": hashlib.sha256(payload).hexdigest()}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", required=True)
    ap.add_argument("--gcc", default=shutil.which("gcc"))
    args = ap.parse_args()
    report = (ROOT / args.report).resolve()
    if report.exists():
        raise SystemExit(f"refusing to overwrite existing report: {report}")
    gcc = Path(args.gcc).resolve() if args.gcc else None
    if gcc is None or not gcc.is_file():
        raise SystemExit("GCC not found")
    files = [ROOT / item for item in DEPENDENCIES]
    missing = [str(p) for p in files if not p.is_file()]
    if missing:
        raise SystemExit("missing input(s): " + ", ".join(missing))
    before = {p.relative_to(ROOT).as_posix(): file_id(p) for p in files}
    compiler = file_id(gcc)
    version = subprocess.run([str(gcc), "--version"], check=True,
                             capture_output=True, text=True, timeout=15).stdout.splitlines()[0]
    expected = expected_window0()
    work_root = ROOT / "build/workers/behavior_window/central-window"
    work_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="hcegant-window-", dir=work_root) as tmp:
        exe = Path(tmp) / "central-hcegant-window.exe"
        cmd = [str(gcc), "-std=c11", "-O0", "-fsigned-char", "-fno-builtin-sprintf",
               "-ffunction-sections", "-fdata-sections", "-Werror=implicit-function-declaration",
               "-I", str(ROOT), *(str(ROOT / p) for p in SOURCES),
               "-Wl,--gc-sections", "-o", str(exe)]
        built = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=120)
        if built.returncode:
            raise SystemExit("compile failed:\n" + built.stderr[-8000:])
        ran = subprocess.run([str(exe), str((ROOT / "assets").resolve())], cwd=ROOT,
                             capture_output=True, text=True, timeout=20)
        if ran.returncode:
            raise SystemExit(f"runtime failed ({ran.returncode}):\n{ran.stdout}\n{ran.stderr}")
        exe_hash = file_id(exe)
        stdout = ran.stdout
    after = {p.relative_to(ROOT).as_posix(): file_id(p) for p in files}
    if before != after or compiler != file_id(gcc):
        raise SystemExit("pinned source or compiler changed during run")
    lines = [line.split(",") for line in stdout.splitlines()]
    summary = next((line for line in lines if line[0] == "WINDOW"), None)
    objs = [[int(v) for v in line[1:]] for line in lines if line[0] == "OBJECT"]
    unlock = next((line for line in lines if line[0] == "UNLOCK"), None)
    if summary is None or unlock is None:
        raise SystemExit("incomplete source observation output")
    observed_summary = [int(v) for v in summary[1:]]
    if observed_summary != [0, expected["count"], expected["payload_size"], 1, 0]:
        raise SystemExit(f"unexpected locked source state: {observed_summary}")
    if objs != expected["objects"]:
        raise SystemExit(f"object projection mismatch: {objs} != {expected['objects']}")
    report_doc = {
        "schema": "simant-whole-program-central-hcegant-window-v1",
        "created_unix_ns": time.time_ns(),
        "result": "PASS",
        "classification": "native actual-source integration; not DOS differential",
        "claim_scope": (
            "The actual source OpenDB/OpenIndex/DBRecall/db_LoadObject and source allocator "
            "provide HCEGANT window 0; generated win_LockWin/win_LoadWindow/RepointObjects/"
            "win_Recalc/win_UnlockWin use one process-wide registry owner. Punt/WinPrintf and "
            "unavailable EMS are the bounded host-service edges. The original SetDefaultWindows "
            "resource orchestration is outside this call path. No PortableDatabase duplicate or "
            "test resource callback is used."),
        "expected_from_independent_resource_parser": expected,
        "observed_locked_state": observed_summary,
        "observed_objects": objs,
        "observed_after_unlock": [int(v) for v in unlock[1:]],
        "runtime_stdout": stdout,
        "compile_command": cmd,
        "compile_stdout": built.stdout,
        "compile_stderr": built.stderr,
        "executable": exe_hash,
        "compiler": {"path": str(gcc), "identity": compiler, "version": version},
        "inputs_before": before,
        "inputs_after": after,
    }
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(report_doc, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report": report.relative_to(ROOT).as_posix(), "result": "PASS",
                      "object_count": expected["count"], "exe_sha256": exe_hash["sha256"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
