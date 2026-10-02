#!/usr/bin/env python3
"""Fresh compile + original-DOS differential for mechanically adapted bodies."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import run_differential_v2 as reference  # noqa: E402
import behavior  # noqa: E402
import exe  # noqa: E402
import functions  # noqa: E402
import match  # noqa: E402

REPORT_REFERENCE = ROOT / "portable/tests/windows/decorations/decoration-differential-v2.json"
NATIVE = HERE / "test_source_bodies.exe"
NATIVE_SOURCES = [
    "portable/tests/windows/decorations/source_conversion/test_source_bodies.c",
    "portable/game/resources/database.c",
]
PIN_PATHS = [
    "src/root/m2505.c", "src/root/m1FD2.c", "src/root/m208F.c",
    "assets/HCEGANT.DAT", "assets/HCEGANT.NDX", "assets/SHARED.DAT", "assets/SHARED.NDX",
    "portable/game/resources/database.c", "portable/game/resources/database.h",
    "portable/ui_model/windows/window.h",
    "portable/tests/windows/decorations/source_conversion/extract_bodies.py",
    "portable/tests/windows/decorations/source_conversion/README.md",
    "portable/tests/windows/decorations/source_conversion/source-conversion.json",
    "portable/tests/windows/decorations/source_conversion/test_source_bodies.c",
    "portable/tests/windows/decorations/source_conversion/run_source_conversion.py",
    "portable/tests/windows/decorations/source_conversion/extracted_bodies.inc",
    "portable/tests/windows/decorations/archive/v1_135/run_differential.py",
    "portable/tests/windows/decorations/archive/v1_135/decoration-differential.json",
    "portable/tests/windows/decorations/run_differential_v2.py",
    "portable/tests/windows/decorations/decoration-differential-v2.json",
    "portable/research/window_decorations_contract.md",
    "portable/tests/windows/mouse_hotbox/evidence/mouse-hotbox-differential-v5.json",
    "tools/behavior.py", "tools/exe.py", "tools/functions.py", "tools/match.py",
    "tools/modctx.py", "tools/modules.py", "tools/autosearch.py",
    "layout/oracle.lock.json", "layout/manifest.json", "layout/functions.json", "layout/symbols.json",
]


def parse_report_path(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", required=True,
                        help="new report path; existing reports are never overwritten")
    args = parser.parse_args(argv)
    path = Path(args.report)
    if not path.is_absolute():
        path = ROOT / path
    path = path.resolve()
    try:
        path.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise SystemExit("--report must be inside the workspace") from exc
    if path.exists():
        raise SystemExit(f"refusing to overwrite existing report: {path}")
    return path


def source_case_matrix():
    cases = [
        ("all-flags-maximized", 0x059C, 1, 3),
        ("all-flags-normal", 0x051C, 1, 3),
        ("all-flags-unregister", 0x059C, 0, 3),
    ]
    for combination in range(32):
        flags = ((0x0004 if combination & 1 else 0) |
                 (0x0008 if combination & 2 else 0) |
                 (0x0100 if combination & 4 else 0) |
                 (0x0010 if combination & 8 else 0) |
                 (0x0400 if combination & 16 else 0))
        for maximized in range(2):
            for show in range(2):
                cases.append((f"matrix-{combination:02x}-{maximized}-{show}",
                              flags | (0x0080 if maximized else 0), show, 3))
    cases.extend([
        ("margin-neg128", 0x0004, 1, -128), ("margin-neg1", 0x0004, 1, -1),
        ("margin-zero", 0x0004, 1, 0), ("margin-pos127", 0x0004, 1, 127),
    ])
    return cases


def native_compile_command():
    return ["gcc", "-std=c11", "-Wall", "-Wextra", "-Werror",
            "-Iportable/game/resources",
            "-Iportable/tests/windows/decorations/source_conversion",
            *NATIVE_SOURCES, "-o", str(NATIVE.relative_to(ROOT))]


def native_dependencies():
    args = ["gcc", "-MM", "-Iportable/game/resources",
            "-Iportable/tests/windows/decorations/source_conversion", *NATIVE_SOURCES]
    result = subprocess.run(args, cwd=ROOT, check=True, capture_output=True, text=True)
    import re
    dep_text = re.sub(r"\\\r?\n\s*", " ", result.stdout)
    deps = set()
    for line in dep_text.splitlines():
        if ":" not in line:
            continue
        _, raw = line.split(":", 1)
        for token in raw.split():
            path = Path(token)
            path = path.resolve() if path.is_absolute() else (ROOT / path).resolve()
            deps.add(str(path.relative_to(ROOT.resolve())).replace("\\", "/"))
    return args, sorted(deps)


def input_hashes(dependencies):
    return {path: reference.sha(ROOT / path)
            for path in sorted(set(PIN_PATHS) | set(dependencies))}


def read_native():
    rows = subprocess.run([str(NATIVE)], cwd=ROOT, check=True,
                          capture_output=True, text=True).stdout.splitlines()
    decoded = [json.loads(row) for row in rows if row.strip()]
    return {row["label"]: row["steps"] for row in decoded}


def main(argv=None):
    report_path = parse_report_path(argv)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    # Generate the checked source-body extraction before dependency hashing.
    extract = ROOT / "portable/tests/windows/decorations/source_conversion/extract_bodies.py"
    subprocess.run([sys.executable, str(extract)], cwd=ROOT, check=True,
                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    toolchain_before = {"gcc": reference.gcc_provenance(),
                        "python": reference.python_provenance(),
                        "unicorn": reference.unicorn_provenance()}
    mm_command, dependencies = native_dependencies()
    before = input_hashes(dependencies)
    subprocess.run(native_compile_command(), cwd=ROOT, check=True,
                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    native = read_native()

    reference_rows = json.loads(REPORT_REFERENCE.read_text(encoding="utf-8"))
    if reference_rows.get("status") != "PASS" or len(reference_rows.get("cases", [])) != 135:
        raise RuntimeError("v2 actual-DOS reference receipt is absent or does not contain 135 PASS cases")
    reference_by_label = {row["label"]: row["trace"] for row in reference_rows["cases"]}
    metrics = {row[0]: (row[1], row[2]) for row in reference_rows["metrics"]}
    cases = source_case_matrix()
    if len(cases) != 135 or set(native) != {case[0] for case in cases}:
        raise RuntimeError("native source-body test did not emit the full expected 135-case corpus")
    results = []
    for label, flags, show, margin in cases:
        oracle_trace, machine = reference.run_original(label, flags, show, metrics, margin)
        if oracle_trace != reference_by_label[label]:
            raise RuntimeError(f"fresh DOS oracle trace differs from frozen v2 case {label}")
        if native[label] != oracle_trace:
            raise AssertionError(f"source-body conversion mismatch in {label}:\n"
                                 f"native={native[label]}\nDOS={oracle_trace}")
        results.append({"label": label, "flags": flags, "show": show, "margin": margin,
                        "events": len(oracle_trace), "source_body_equal": True,
                        "oracle_trace_equal_to_v2": True,
                        "oracle_nonstack_writes": len(machine.written)})

    after = input_hashes(dependencies)
    toolchain_after = {"gcc": reference.gcc_provenance(),
                       "python": reference.python_provenance(),
                       "unicorn": reference.unicorn_provenance()}
    if before != after or toolchain_before != toolchain_after:
        raise RuntimeError("source, dependencies, or execution toolchain changed during the differential")
    conversions = json.loads((HERE / "source-conversion.json").read_text(encoding="utf-8"))
    report = {
        "schema": "window-decoration-source-body-differential-v1",
        "status": "PASS",
        "approach": "function bodies extracted from original C, narrowly transformed by the checked conversion spec, and compiled directly; no native planner is called",
        "reference_report": str(REPORT_REFERENCE.relative_to(ROOT)).replace("\\", "/"),
        "reference_report_sha256": reference.sha(REPORT_REFERENCE),
        "conversion_spec": conversions,
        "generated_body_sha256": reference.sha(HERE / "extracted_bodies.inc"),
        "compiler_command": native_compile_command(),
        "gcc_mm_command": mm_command,
        "gcc_mm_dependencies": dependencies,
        "input_sha256_before": before,
        "input_sha256_after": after,
        "inputs_stable_through_run": True,
        "toolchain_sha256_before": toolchain_before,
        "toolchain_sha256_after": toolchain_after,
        "native_test_binary_sha256": reference.sha(NATIVE),
        "case_count": len(results),
        "event_count": sum(row["events"] for row in results),
        "cases": results,
        "limits": [
            "The conversion covers these two bodies only; actual f_208F_0419 object dimensions are supplied by the HCEGANT metric callback.",
            "The actual source f_1FD2_0883 body is compiled and calls the metric, registration, and unregister sinks in its original order.",
            "The hotbox sink captures the source-produced rectangle/mode but does not emulate allocator-backed scanner-list mutation or callback dispatch.",
            "No production file or historical canonical source was modified.",
        ],
    }
    with report_path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"status": "PASS", "cases": len(results),
                      "events": report["event_count"],
                      "report": str(report_path.relative_to(ROOT)).replace("\\", "/")}, indent=2))


if __name__ == "__main__":
    main()
