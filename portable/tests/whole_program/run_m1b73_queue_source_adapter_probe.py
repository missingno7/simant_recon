#!/usr/bin/env python3
"""Compile the true adapted root:m1FD2 TU and test its borrowed queue views."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "portable/tools"))
from portable.tools.whole_program import (  # noqa: E402
    centralize_io, convert_words, function_heads,
)
from portable.whole_program.conversions.timer import adapt as adapt_timer  # noqa: E402
from portable.whole_program.conversions.m1b73_queue_source import (  # noqa: E402
    adapt as adapt_queue_source,
)

INPUTS = [
    "src/root/m1FD2.c",
    "src/root/m1B73.asm",
    "portable/tools/whole_program.py",
    "portable/tools/word_spelling.py",
    "portable/whole_program/conversions/timer.py",
    "portable/whole_program/conversions/m1b73_queue_source.py",
    "portable/whole_program/platform/m1b73_queue_source.h",
    "portable/whole_program/platform/m1b73_queue_source.c",
    "portable/whole_program/platform/m1b73_queue_source.md",
    "portable/whole_program/platform/m1b73_queues.h",
    "portable/whole_program/platform/m1b73_queues.c",
    "portable/whole_program/platform/m1b73_mouse_state.h",
    "portable/whole_program/platform/m1b73_mouse_state.c",
    "portable/whole_program/types/timer.h",
    "portable/whole_program/platform/dos_memory.h",
    "portable/whole_program/platform/dos_io.h",
    "portable/tests/recovered/whole_program_asm_state/fixtures/v1-generated/dos_types.h",
    "portable/tests/whole_program/m1b73_queue_source_view_probe.c",
    "portable/tests/whole_program/run_m1b73_queue_source_adapter_probe.py",
]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def identity(path: Path) -> dict[str, object]:
    data = path.read_bytes()
    return {"sha256": sha(data), "size": len(data)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--exe", required=True, type=Path)
    parser.add_argument("--candidate", required=True, type=Path)
    args = parser.parse_args()
    report = args.report if args.report.is_absolute() else ROOT / args.report
    output = args.exe if args.exe.is_absolute() else ROOT / args.exe
    candidate = args.candidate if args.candidate.is_absolute() else ROOT / args.candidate
    for path in (report, output, candidate):
        if path.exists():
            raise SystemExit(f"refusing to overwrite immutable artifact: {path}")
        path.parent.mkdir(parents=True, exist_ok=True)

    source_path = ROOT / "src/root/m1FD2.c"
    source = source_path.read_text(encoding="utf-8")
    source_order = [row["name"] for row in function_heads(source)]
    before = {item: identity(ROOT / item) for item in INPUTS}
    timer_source, timer_ledger = adapt_timer(source)
    queue_source, queue_ledger = adapt_queue_source(timer_source)
    word_source, word_ledger = convert_words(queue_source)
    word_source, far_memory_declarations_removed = re.subn(
        r"(?m)^\s*extern\s+[^;]*\b_f(?:mem\w+|str\w+)\s*\([^;]*;",
        "", word_source)
    word_source, dos_io_declarations_removed = centralize_io(word_source)
    adapted_order = [row["name"] for row in function_heads(word_source)]
    if source_order != adapted_order:
        raise SystemExit("m1FD2 adapter changed source function membership/order")
    if "g_9120" in queue_source or "fd_5071_" in queue_source:
        raise SystemExit("old source byte/queue symbols remain after typed adapter")
    expected_slots = {
        1: queue_source.count("portable_m1b73_queue_slot(1)"),
        2: queue_source.count("portable_m1b73_queue_slot(2)"),
        3: queue_source.count("portable_m1b73_queue_slot(3)"),
    }
    if expected_slots != {1: 3, 2: 5, 3: 5}:
        raise SystemExit(f"unexpected transformed queue-slot callsites: {expected_slots}")
    candidate_source = (
        '#include "dos_types.h"\n'
        '#include "portable/whole_program/platform/dos_memory.h"\n'
        '#include "portable/whole_program/platform/dos_io.h"\n'
        "#pragma pack(push, 2)\n" + word_source + "\n#pragma pack(pop)\n"
    )
    candidate.write_text(candidate_source, encoding="utf-8", newline="\n")

    compiler_name = shutil.which("gcc") or r"C:\msys64\mingw64\bin\gcc.exe"
    compiler = Path(compiler_name).resolve()
    if not compiler.is_file():
        raise SystemExit(f"GCC not found: {compiler}")
    version = subprocess.run([str(compiler), "--version"], cwd=ROOT, check=True,
                             capture_output=True, text=True).stdout.splitlines()[0]
    work = output.parent
    dos_types = work / "dos_types.h"
    dos_types_source = ROOT / "portable/tests/recovered/whole_program_asm_state/fixtures/v1-generated/dos_types.h"
    dos_types.write_bytes(dos_types_source.read_bytes())
    compile_command = [
        str(compiler), "-std=c11", "-fsyntax-only", "-fno-builtin",
        "-Werror=implicit-function-declaration", "-Werror=incompatible-pointer-types",
        "-I", str(ROOT), "-I", str(work), str(candidate),
    ]
    syntax = subprocess.run(compile_command, cwd=ROOT, capture_output=True,
                            text=True, timeout=40)
    if syntax.returncode:
        raise SystemExit(f"adapted m1FD2 whole-TU compile failed:\n{syntax.stderr}")

    bounds_command = [
        str(compiler), "-std=c11", "-Wall", "-Wextra", "-Wconversion",
        "-Wno-sign-conversion", "-Werror", "-pedantic",
        "-D__USE_MINGW_SETJMP_NON_SEH",
        "portable/tests/whole_program/m1b73_queue_source_view_probe.c",
        "portable/whole_program/platform/m1b73_queue_source.c",
        "portable/whole_program/platform/m1b73_queues.c",
        "portable/whole_program/platform/m1b73_mouse_state.c",
        "-o", str(output),
    ]
    bounds_build = subprocess.run(bounds_command, cwd=ROOT, capture_output=True,
                                  text=True, timeout=40)
    if bounds_build.returncode:
        raise SystemExit(f"queue view bounds control did not compile:\n{bounds_build.stderr}")
    run = subprocess.run([str(output)], cwd=ROOT, capture_output=True, text=True,
                         timeout=10)
    if run.returncode:
        raise SystemExit(f"queue view bounds control failed ({run.returncode}): {run.stderr}")
    after = {item: identity(ROOT / item) for item in INPUTS}
    if before != after:
        raise SystemExit("source or converter inputs changed during probe")

    result = {
        "schema": "whole-program-m1b73-queue-source-adapter-v1",
        "status": "PASS_ADAPTED_ROOT_M1FD2_SYNTAX_AND_QUEUE_OWNER_BOUNDS",
        "scope": "strict syntax compile of the full actual root:m1FD2 translation unit after the existing Timer lift, new pre-word mouse/queue adapter, and whole-program word converter; separate native getter bounds test; no function behavioral equivalence claim",
        "inputs_before": before,
        "inputs_after": after,
        "timer_ledger": timer_ledger,
        "queue_adapter_ledger": queue_ledger,
        "word_conversion_ledger": word_ledger,
        "shared_runtime_declaration_normalization": {
            "far_memory_declarations_removed": far_memory_declarations_removed,
            "dos_io_declarations_removed": dos_io_declarations_removed,
            "basis": "same narrow post-word declaration centralization used by portable/tools/whole_program.py",
        },
        "source_function_count": len(source_order),
        "source_function_order": source_order,
        "adapted_function_order": adapted_order,
        "source_function_order_preserved": source_order == adapted_order,
        "typed_queue_slot_callsite_counts": expected_slots,
        "native_queue_view_bounds": {
            "status": "PASS" if run.returncode == 0 else "FAIL",
            "coverage": "slot indices 0..3 return their exact canonical queue member addresses; 0xff returns NULL; queue row spans point to their exact 5/48/48/10 source-derived arrays; g_9120 byte accessor returns the low byte of the one 16-bit owner",
            "compile_command": bounds_command,
            "compile_stderr": bounds_build.stderr,
            "run_returncode": run.returncode,
            "run_stdout": run.stdout,
            "run_stderr": run.stderr,
        },
        "whole_tu_compile": {
            "returncode": syntax.returncode,
            "command": compile_command,
            "diagnostics": syntax.stderr,
            "candidate": candidate.relative_to(ROOT).as_posix(),
            "candidate_sha256": sha(candidate.read_bytes()),
        },
        "asm_abi_notes": {
            "f_1B73_0B5B": "stack arguments: signed ticks word, far queue pointer; C slot arguments now use typed borrowed queue views",
            "f_1B73_0B00": "stack arguments: far Timer pointer, far queue pointer; native Timer pointer then typed queue view",
            "f_1B73_0AC3": "same far Timer/far queue stack order as 0B00",
            "f_1B73_0BC5": "signed ID/ticks word plus far queue pointer; ASM returns AX while root C declaration/caller ignores it",
            "f_1B73_0C42": "ID word, far queue pointer, output far pointer represented by two words; high-level caller pointer normalization remains an integration boundary",
            "f_1B73_09E9": "two signed coordinate words in BP+6/BP+8",
            "f_1B73_030F": "ASM reads five words at BP+6..BP+0E, but source callsites pass varying four/five argument lists through an empty prototype; this adapter does not normalize them",
        },
        "limits": [
            "The adapted C TU was syntax-compiled, not linked or executed; the native queue operation exports for 0B5B/0B00/0AC3/0BC5/0C42 are separate unresolved integration work.",
            "No DOS far queue pointers or interrupt stack behavior are preserved; slots resolve to host-side typed queue views.",
            "f_1B73_0C42's source split output pointer words and f_1B73_030F's varying argument counts are explicitly not represented as native pointer/callback equivalence.",
            "m1FD2 does not reference g_4366; its source byte type is not widened or aliased by this adapter.",
        ],
        "compiler": {"path": str(compiler), "sha256": identity(compiler)["sha256"],
                     "version": version},
        "executable": output.relative_to(ROOT).as_posix(),
        "executable_sha256": sha(output.read_bytes()),
    }
    with report.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(json.dumps({"status": result["status"], "functions": len(source_order),
                      "queue_slots": expected_slots,
                      "report": str(report)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
