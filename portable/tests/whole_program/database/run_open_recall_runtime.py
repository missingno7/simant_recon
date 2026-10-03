#!/usr/bin/env python3
"""Bounded actual-source DB open/read/decode/close integration probe.

This is a native integration receipt, not DOS-vs-native equivalence evidence.
It invokes converted source bodies for OpenDB, OpenIndex, FindIndex, DBRecall,
f_19DC_02FB and CloseDB and checks returned payloads against the independent
portable resource parser. A fixture-owned zero sentinel makes FindIndex's
above-maximum one-past probe defined without changing the active index count.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time
import sys

ROOT = Path(__file__).resolve().parents[4]

SOURCES = [
    "build/workers/whole_program/generated/root_m1986.c",
    "build/workers/whole_program/generated/root_m19A9.c",
    "build/workers/whole_program/generated/root_m19DC.c",
    "build/workers/whole_program/generated/root_m1A28.c",
    "portable/whole_program/state/database.c",
    "portable/whole_program/conversions/pointer_globals.c",
    "portable/whole_program/platform/handles.c",
    "portable/whole_program/platform/dos_io.c",
    "portable/whole_program/platform/dos_format.c",
    "portable/whole_program/platform/dos_memory.c",
    "portable/platform/memory.c",
    "portable/whole_program/algorithms/lzss.c",
    "portable/game/resources/database.c",
    "portable/tests/whole_program/database/native_open_recall_driver.c",
    "portable/tests/whole_program/database/native_open_recall_error_symbols.c",
]
DEPENDENCIES = [
    "portable/whole_program/types/database.h",
    "portable/whole_program/platform/dos_io.h",
    "portable/whole_program/platform/dos_files.h",
    "portable/whole_program/platform/dos_format.h",
    "portable/whole_program/platform/dos_memory.h",
    "portable/whole_program/platform/handles.h",
    "portable/whole_program/algorithms/lzss.h",
    "portable/game/resources/database.h",
    "portable/platform/memory.h",
    "build/workers/whole_program/generated/dos_types.h",
    "build/workers/whole_program/generated/migration.json",
    "src/root/m1986.c",
    "src/root/m19A9.c",
    "src/root/m19DC.c",
    "src/root/m1A28.c",
    "assets/HCEGANT.NDX", "assets/HCEGANT.DAT",
    "assets/SHARED.NDX", "assets/SHARED.DAT",
    "assets/SOUND.NDX", "assets/SOUND.DAT",
]


def file_id(path: Path) -> dict:
    raw = path.read_bytes()
    return {"sha256": hashlib.sha256(raw).hexdigest(), "size": len(raw)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", required=True, help="new report JSON path; overwrite is refused")
    ap.add_argument("--gcc", default=r"C:\msys64\mingw64\bin\gcc.exe")
    args = ap.parse_args()
    report_path = (ROOT / args.report).resolve()
    if report_path.exists():
        raise SystemExit(f"refusing to overwrite report: {report_path}")
    gcc = Path(args.gcc).resolve()
    required = [ROOT / p for p in SOURCES + DEPENDENCIES]
    if not gcc.is_file() or any(not p.is_file() for p in required):
        raise SystemExit("compiler or pinned runtime dependency is missing")
    before = {p.relative_to(ROOT).as_posix(): file_id(p) for p in required}
    compiler_id = file_id(gcc)
    version = subprocess.run([str(gcc), "--version"], check=True, capture_output=True,
                             text=True, timeout=15).stdout.splitlines()[0]
    work_root = ROOT / "build/workers/behavior_memory/db-runtime"
    work_root.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix=f"run-{time.time_ns()}-", dir=work_root))
    exe = work / "native-open-recall.exe"
    cmd = [str(gcc), "-std=c11", "-O0", "-fsigned-char", "-fno-builtin-sprintf",
           "-ffunction-sections", "-fdata-sections", "-Werror=implicit-function-declaration",
           "-I", str(ROOT)] + [str(ROOT / p) for p in SOURCES] + [
               "-Wl,--gc-sections", "-o", str(exe)]
    compile_run = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True,
                                 timeout=90)
    if compile_run.returncode:
        raise SystemExit(f"native integration compile failed: {compile_run.stderr[-4000:]}")
    run = subprocess.run([str(exe), str((ROOT / "assets").resolve())], cwd=ROOT,
                         capture_output=True, text=True, timeout=30)
    after = {p.relative_to(ROOT).as_posix(): file_id(p) for p in required}
    if before != after or file_id(gcc) != compiler_id:
        raise SystemExit("a pinned source/toolchain input changed during the probe")
    if run.returncode:
        raise SystemExit(f"runtime integration failed ({run.returncode}): {run.stderr}")
    rows = [line.split(",") for line in run.stdout.splitlines() if line.count(",") == 5]
    if len(rows) != 4:
        raise SystemExit(f"expected four resource observations, found {len(rows)}")
    report = {
        "schema": "simant-whole-program-database-open-recall-runtime-v1",
        "created_unix_ns": time.time_ns(),
        "result": "PASS",
        "classification": "native actual-source integration; not original-DOS differential evidence",
        "source_entry_calls": {
            "OpenDB": 4, "OpenIndex": 4, "FindIndex": 8,
            "DBRecall": 4, "CloseDB": 4, "f_19DC_02FB": 9,
        },
        "record_cases": [
            {"database": r[0], "id": int(r[1]), "kind": int(r[2]),
             "returned_size": int(r[3]), "fnv1a32": r[4], "first_four_bytes": r[5]}
            for r in rows
        ],
        "coverage": {
            "raw_and_lzss_records": True,
            "payloads_compared_bytewise_to_portable_db_load": 4,
            "handle_alloc_lock_unlock_free": "source DBRecall handles; lock/read/unlock/free exercised",
            "index_hits": 4,
            "above_max_misses": 4,
            "active_index_count_changed": False,
            "native_sentinel": "fixture installs one zero IndexEntry after active rows; DOS heap residue is not modeled",
            "ems": "explicitly unavailable host boundary; source f_195A_0260 returns unavailable; other EMS functions trap if reached",
            "database_close": "all four real source CloseDB calls complete and clear slot name",
        },
        "one_past_hazard": {
            "status": "bounded by initialized native sentinel",
            "source_openindex_allocates": "indexHeader.count * 8 bytes",
            "source_openindex_reads": "indexHeader.count * 8 bytes",
            "source_findindex_forms": "index[fd_50F6_3956] after binary search, including insertion rank == count",
            "fixture_policy": "native test extends storage with one zero row after source OpenIndex; misses are chosen above each final key and confirmed NULL",
            "limit": "the native sentinel result does not establish the original DOS heap byte at this one-past address",
        },
        "oracle_calls": 0,
        "proof_claim": None,
        "compiler": {"path": str(gcc), "identity": compiler_id, "version": version},
        "compile_command": cmd,
        "compile_stdout": compile_run.stdout,
        "compile_stderr": compile_run.stderr,
        "runtime_stdout": run.stdout,
        "runtime_stderr": run.stderr,
        "inputs_before": before,
        "inputs_after": after,
        "temporary_executable_sha256": file_id(exe)["sha256"],
        "temporary_executable_size": exe.stat().st_size,
        "build_directory": work.relative_to(ROOT).as_posix(),
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report": report_path.relative_to(ROOT).as_posix(),
                      "result": "PASS", "records": len(rows),
                      "build": work.relative_to(ROOT).as_posix()}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
