#!/usr/bin/env python3
"""Fresh bounded proof of the native FindIndex one-past guard.

Runs original DOS FindIndex against a same-compiler guard candidate on bounded
sentinel controls, plus guarded native page-boundary and actual DB-runtime
checks. It never rewrites the original source, generated profile, or prior
database reports. The nonmatching sentinel lanes are returned-equivalent; a
matching sentinel is intentionally changed from a DOS heap-residue-dependent
hit to a defined native miss.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tools" / "behavior_suites"))

import autosearch  # noqa: E402
import behavior  # noqa: E402
import exe  # noqa: E402
import functions  # noqa: E402
import match  # noqa: E402
import modctx  # noqa: E402
import modules  # noqa: E402
import small_contracts  # noqa: E402
from portable.whole_program.conversions.findindex_native_guard import (  # noqa: E402
    GUARD, REVIEWED_BODY_SHA256, REVIEWED_MODULE_SHA256, adapt_dos_source,
    adapt_host_source,
)

GCC_DEFAULT = Path(r"C:\msys64\mingw64\bin\gcc.exe")
NATIVE_TEST = "portable/tests/whole_program/database/findindex_guard_native_test.c"
RUNTIME_TEST = "portable/tests/whole_program/database/findindex_guard_open_recall_driver.c"
ERROR_SYMBOLS = "portable/tests/whole_program/database/native_open_recall_error_symbols.c"
GENERATED = "build/workers/whole_program/generated/"
ROOT_MODULES = ["root_m1986.c", "root_m19A9.c", "root_m19DC.c", "root_m1A28.c"]
INPUTS = [
    "evidence/behavior/functions/FindIndex/module.c",
    "src/root/m1986.c",
    "portable/whole_program/conversions/findindex_native_guard.py",
    "portable/whole_program/types/database.h",
    "portable/whole_program/state/database.c",
    "portable/whole_program/platform/handles.c",
    "portable/whole_program/platform/handles.h",
    "portable/whole_program/platform/dos_io.c",
    "portable/whole_program/platform/dos_io.h",
    "portable/whole_program/platform/dos_format.c",
    "portable/whole_program/platform/dos_format.h",
    "portable/whole_program/platform/dos_memory.c",
    "portable/whole_program/platform/dos_memory.h",
    "portable/platform/memory.c",
    "portable/platform/memory.h",
    "portable/whole_program/conversions/pointer_globals.c",
    "portable/whole_program/conversions/pointer_globals.h",
    "portable/whole_program/algorithms/lzss.c",
    "portable/whole_program/algorithms/lzss.h",
    "portable/game/resources/database.c",
    "portable/game/resources/database.h",
    NATIVE_TEST, RUNTIME_TEST, ERROR_SYMBOLS,
    "portable/tests/resources/evidence/database_dos_differential.py",
    "portable/tests/resources/evidence/database-dos-differential.json",
    "portable/tests/whole_program/database/run_findindex_guard.py",
    "portable/tests/whole_program/conversions/test_findindex_native_guard.py",
    "portable/tools/whole_program.py",
    "tools/behavior.py", "tools/behavior_ledger.py", "tools/modules.py", "tools/modctx.py",
    "tools/match.py", "tools/exe.py", "tools/functions.py", "tools/autosearch.py", "tools/mismatch.py",
    "tools/omf.py", "tools/symbols.py", "tools/behavior_suites/small_contracts.py",
    "layout/oracle.lock.json", "layout/toolchain.json", "layout/manifest.json", "layout/symbols.json",
    "evidence/toolchain/runtime-location.json",
    "build/workers/whole_program/generated/dos_types.h",
    "build/workers/whole_program/generated/migration.json",
] + [GENERATED + f for f in ROOT_MODULES]
for stem in ("HCEGANT", "SHARED", "SOUND"):
    INPUTS.extend([f"assets/{stem}.NDX", f"assets/{stem}.DAT"])


def identity(path: Path) -> dict:
    raw = path.read_bytes()
    try:
        label = path.relative_to(ROOT).as_posix()
    except ValueError:
        label = str(path)
    return {"path": label, "size": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def build_behavior_pair(candidate_source: Path):
    """Run the standard Unicorn Machine with an isolated target-only C object.

    The reviewed module contains unrelated historical private CONST data whose
    whole-module compiler layout remains inexact. This comparison uses the
    actual target function object and standard Machine/ExecutionBinder, while
    not claiming the absent peers or private-data gate.
    """
    name = "FindIndex"
    target = functions.get(name)
    context = modctx.resolve(func=name, source=candidate_source)
    text = autosearch.unscaffold(candidate_source.read_text(encoding="latin1"), name)
    claims = list(context.claims)
    if not any(c["name"] == name for c in claims):
        claims.append(target)
    collected = {}
    strict = modules.verify_module(text, context.module_dict(), claims, collect=collected)
    if not strict.get("compile_ok") or "object" not in collected:
        raise RuntimeError(f"guarded DOS function failed to compile: {strict.get('log', '')}")
    obj = modctx.read_obj(collected["object"])
    _public, record = match.public_in(obj, name)
    if record is None:
        raise RuntimeError("compiled candidate lacks FindIndex")
    segment = record["segment"]
    raw = obj.segments[segment]
    if len(raw) > 65536:
        raise RuntimeError("candidate code exceeds real-mode scratch segment")
    bound = behavior.ExecutionBinder(
        match.Target(target["unit"], behavior.CODE_SEG, 0, len(raw)), obj, segment,
        None, context.placements_bind, span=(0, len(raw))).bind()
    if bound.unbound or len(bound.candidate) != len(raw):
        raise RuntimeError(f"candidate link is incomplete: {bound.unbound}")
    entries = {}
    for public in obj.publics + getattr(obj, "local_publics", []):
        if public["segment"] == segment:
            public_name = public["name"][1:] if public["name"].startswith(("_", "@")) else public["name"]
            entries[public_name] = behavior.CODE_SEG * 16 + public["offset"]
    if name not in entries:
        raise RuntimeError("candidate symbol entry was not enumerated")
    executable = exe.load()
    pair = SimpleNamespace(
        function=target,
        sequence_targets=frozenset(),
        code=bound.candidate,
        candidate_entry=(behavior.CODE_SEG, record["offset"]),
        candidate_entries=entries,
        delegate={},
        vectors={exe.MANAGER_SEG * 16 + v.offset: v for v in executable.vectors},
        identity={"function": name, "address": {k: target[k] for k in ("unit", "seg", "off", "size")},
                  "oracle_sha256": executable.sha256},
        object_sha256=hashlib.sha256(collected["object"]).hexdigest(),
        strict=strict,
    )
    pair.original_machine = behavior.Machine(pair)
    pair.candidate_machine = behavior.Machine(pair, True)
    return pair, text


def compare_dos_controls(candidate_source: Path) -> dict:
    pair, compiled_text = build_behavior_pair(candidate_source)
    cases = [
        ("empty-early-return", [], 0, 0, (0, 0x1357, 0xD6, 0)),
        ("singleton-last-hit", [(0x1000, 32767, 255, 0)], 32767, 255,
         (0, -32768, 0, 0)),
        ("singleton-above-max-unmatched", [(0x1000, 32766, 255, 0)], 32767, 255,
         (0x2000, -32768, 0, 0)),
        ("singleton-above-max-matching-sentinel", [(0x1000, 32766, 255, 0)], 32767, 255,
         (0x2000, 32767, 255, 0)),
        ("multirow-last-hit", [(0x1000, -3, 2, 0), (0x1008, 4, 2, 0),
                               (0x1010, 300, 2, 0)], 300, 2, (0, -32768, 0, 0)),
        ("multirow-above-max-unmatched", [(0x1000, -3, 2, 0), (0x1008, 4, 2, 0),
                                          (0x1010, 300, 2, 0)], 301, 2,
         (0x2000, -32768, 0, 0)),
        ("multirow-above-max-matching-sentinel", [(0x1000, -3, 2, 0),
                                                   (0x1008, 4, 2, 0),
                                                   (0x1010, 300, 2, 0)], 301, 2,
         (0x2000, 301, 2, 0)),
        ("invalid-kind-outside-byte-domain", [(0x1000, 1, 2, 0),
                                               (0x1008, 4, 2, 0)], 4, 256,
         (0x2000, -32768, 0, 0)),
    ]
    results = []
    equivalence = 0
    intentional_heap_residue_boundary = 0
    for label, entries, ident, kind, sentinel in cases:
        case = small_contracts.find_case(label, entries, ident, kind, sentinel=sentinel)
        original = pair.original_machine.run(case)
        candidate = pair.candidate_machine.run(case)
        comparison = behavior.PreparedPair._comparison(pair, case, original, candidate)
        expected_difference = "matching-sentinel" in label
        if expected_difference:
            if comparison.equal or set(comparison.diff) != {"return"}:
                raise AssertionError({"case": label, "expected_only_return_difference": True,
                                      "equal": comparison.equal, "diff": comparison.diff})
            if original["return"] == 0:
                raise AssertionError("original matching sentinel did not return its one-past pointer")
            intentional_heap_residue_boundary += 1
        else:
            if not comparison.equal:
                raise AssertionError({"case": label, "unexpected DOS candidate diff": comparison.diff})
            equivalence += 1
        results.append({"label": label, "entries": len(entries), "query": [ident, kind],
                        "sentinel": list(sentinel), "equal": comparison.equal,
                        "difference": comparison.diff,
                        "original_return": original["return"],
                        "candidate_return": candidate["return"],
                        "original_cursor": original["ranges"]["fd_50F6_3956"],
                        "candidate_cursor": candidate["ranges"]["fd_50F6_3956"]})
    return {"cases": results, "equal_nonmatching_controls": equivalence,
            "intentional_matching_sentinel_differences": intentional_heap_residue_boundary,
            "candidate_object_sha256": pair.object_sha256,
            "compiler_warnings_or_unrelated_data_diagnostics": pair.strict.get("data"),
            "candidate_source_sha256": hashlib.sha256(candidate_source.read_bytes()).hexdigest(),
            "compiled_text_sha256": hashlib.sha256(compiled_text.encode("latin1")).hexdigest(),
            "scope": "Fresh original DOS vs separately compiled guarded FindIndex function; other module peers/data are not claimed."}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, help="new evidence directory under build/workers")
    ap.add_argument("--gcc", default=str(GCC_DEFAULT))
    args = ap.parse_args()
    out = (ROOT / args.out).resolve()
    workers = (ROOT / "build/workers").resolve()
    if workers not in out.parents:
        raise SystemExit("--out must be a new directory under build/workers")
    if out.exists():
        raise SystemExit(f"refusing to overwrite {out}")
    gcc = Path(args.gcc).resolve()
    if not gcc.is_file():
        raise SystemExit(f"GCC not found: {gcc}")
    required = [ROOT / p for p in INPUTS]
    if any(not p.is_file() for p in required):
        missing = [p.as_posix() for p in required if not p.is_file()]
        raise SystemExit(f"missing pinned inputs: {missing}")
    before = {p.relative_to(ROOT).as_posix(): identity(p) for p in required}
    gcc_before = identity(gcc)
    gcc_version = subprocess.run([str(gcc), "--version"], check=True,
                                 capture_output=True, text=True, timeout=15).stdout.splitlines()[0]
    out.mkdir(parents=True)
    temp = ROOT / "build/workers/behavior_memory"
    temp.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix=f"findindex-guard-{time.time_ns()}-", dir=temp))
    reviewed = ROOT / "evidence/behavior/functions/FindIndex/module.c"
    reviewed_text = reviewed.read_text(encoding="latin1")
    dos_text, dos_provenance = adapt_dos_source(reviewed_text)
    host_text, host_provenance = adapt_host_source(reviewed_text)
    dos_candidate = work / "findindex-guard-dos-function.c"
    host_candidate = work / "findindex-guard-native.c"
    dos_candidate.write_text(dos_text, encoding="latin1")
    host_candidate.write_text(host_text, encoding="latin1")
    dos_controls = compare_dos_controls(dos_candidate)

    native_exe = work / "findindex-guard-native-test.exe"
    native_cmd = [str(gcc), "-std=c11", "-O0", "-Wall", "-Wextra", "-Werror",
                  "-I", str(ROOT), str(host_candidate),
                  str(ROOT / "portable/whole_program/state/database.c"),
                  str(ROOT / NATIVE_TEST), "-o", str(native_exe)]
    native_compile = subprocess.run(native_cmd, cwd=ROOT, capture_output=True,
                                     text=True, timeout=60)
    if native_compile.returncode:
        raise SystemExit(f"native guard test compile failed: {native_compile.stderr}")
    native_run = subprocess.run([str(native_exe)], cwd=ROOT, capture_output=True,
                                text=True, timeout=15)
    if native_run.returncode or "passed" not in native_run.stdout:
        raise SystemExit(f"native guarded test failed: rc={native_run.returncode} {native_run.stderr}")

    unguarded_candidate = work / "findindex-native-unguarded.c"
    if host_text.count(GUARD) != 1:
        raise SystemExit("guard source does not have exactly one guard to mutate")
    unguarded_candidate.write_text(host_text.replace(GUARD, "/* omitted guard negative control */", 1),
                                   encoding="latin1")
    unguarded_exe = work / "findindex-native-unguarded.exe"
    unguarded_cmd = [str(gcc), "-std=c11", "-O0", "-Wall", "-Wextra", "-Werror",
                     "-DEXPECT_UNGUARDED_CRASH", "-I", str(ROOT), str(unguarded_candidate),
                     str(ROOT / "portable/whole_program/state/database.c"),
                     str(ROOT / NATIVE_TEST), "-o", str(unguarded_exe)]
    unguarded_compile = subprocess.run(unguarded_cmd, cwd=ROOT, capture_output=True,
                                       text=True, timeout=60)
    if unguarded_compile.returncode:
        raise SystemExit(f"unguarded negative-control compile failed: {unguarded_compile.stderr}")
    unguarded_run = subprocess.run([str(unguarded_exe)], cwd=ROOT, capture_output=True,
                                   text=True, timeout=15)
    if unguarded_run.returncode != 86:
        raise SystemExit(f"unguarded FindIndex did not trigger expected protected-page AV control: rc={unguarded_run.returncode}")

    generated_m1986_obj = work / "root_m1986_unpatched.o"
    compile_generated_obj = [str(gcc), "-std=c11", "-O0", "-fsigned-char",
        "-fno-builtin-sprintf", "-ffunction-sections", "-fdata-sections",
        "-Werror=implicit-function-declaration", "-I", str(ROOT),
        "-DFindIndex=FindIndex_generated_unpatched", "-c",
        str(ROOT / f"{GENERATED}root_m1986.c"), "-o", str(generated_m1986_obj)]
    generated_compile = subprocess.run(compile_generated_obj, cwd=ROOT,
                                       capture_output=True, text=True, timeout=60)
    if generated_compile.returncode:
        raise SystemExit(f"generated OpenIndex module compile failed: {generated_compile.stderr}")
    runtime_exe = work / "guarded-open-recall.exe"
    runtime_sources = [str(ROOT / f"{GENERATED}{n}") for n in ROOT_MODULES if n != "root_m1986.c"]
    runtime_sources += [str(host_candidate),
        str(ROOT / "portable/whole_program/state/database.c"),
        str(ROOT / "portable/whole_program/conversions/pointer_globals.c"),
        str(ROOT / "portable/whole_program/platform/handles.c"),
        str(ROOT / "portable/whole_program/platform/dos_io.c"),
        str(ROOT / "portable/whole_program/platform/dos_format.c"),
        str(ROOT / "portable/whole_program/platform/dos_memory.c"),
        str(ROOT / "portable/platform/memory.c"),
        str(ROOT / "portable/whole_program/algorithms/lzss.c"),
        str(ROOT / "portable/game/resources/database.c"),
        str(ROOT / RUNTIME_TEST), str(ROOT / ERROR_SYMBOLS)]
    runtime_cmd = [str(gcc), "-std=c11", "-O0", "-fsigned-char", "-fno-builtin-sprintf",
                   "-ffunction-sections", "-fdata-sections", "-Werror=implicit-function-declaration",
                   "-I", str(ROOT), str(generated_m1986_obj)] + runtime_sources + [
                   "-Wl,--gc-sections", "-o", str(runtime_exe)]
    runtime_compile = subprocess.run(runtime_cmd, cwd=ROOT, capture_output=True,
                                     text=True, timeout=90)
    if runtime_compile.returncode:
        raise SystemExit(f"actual OpenDB runtime compile failed: {runtime_compile.stderr[-4000:]}")
    runtime_run = subprocess.run([str(runtime_exe), str((ROOT / "assets").resolve())],
                                 cwd=ROOT, capture_output=True, text=True, timeout=30)
    if runtime_run.returncode:
        raise SystemExit(f"actual OpenDB runtime failed rc={runtime_run.returncode}: {runtime_run.stderr}")
    actual_rows = [line for line in runtime_run.stdout.splitlines() if line.startswith("PASS,")]
    if len(actual_rows) != 4:
        raise SystemExit(f"actual runtime returned {len(actual_rows)} DB cases, expected four")
    after = {p.relative_to(ROOT).as_posix(): identity(p) for p in required}
    gcc_after = identity(gcc)
    if before != after or gcc_before != gcc_after:
        raise SystemExit("source, profile, asset, or compiler inputs changed during the run")
    oracle = exe.load()
    report = {
        "schema": "simant-findindex-native-onepast-guard-v1",
        "created_unix_ns": time.time_ns(),
        "status": "PASS_BOUNDED_NATIVE_SAFETY_ADAPTATION",
        "proof_category_claim": None,
        "source_scope": {
            "reviewed_function_module": "evidence/behavior/functions/FindIndex/module.c",
            "reviewed_module_sha256": REVIEWED_MODULE_SHA256,
            "reviewed_body_sha256": REVIEWED_BODY_SHA256,
            "source_change": "native guard after preserved cursor pointer assignment and before terminal one-past field reads",
            "historical_source_or_manifest_modified": False,
        },
        "host_adaptation": host_provenance,
        "dos_control_adaptation": dos_provenance,
        "fresh_original_dos_controls": dos_controls,
        "native_guarded_page_boundary": {
            "result": "PASS",
            "stdout": native_run.stdout,
            "stderr": native_run.stderr,
            "command": native_cmd,
        },
        "unguarded_protected_page_negative_control": {
            "result": "EXPECTED_ACCESS_VIOLATION_CAUGHT_BY_TEST_HANDLER",
            "returncode": unguarded_run.returncode,
            "stdout": unguarded_run.stdout,
            "stderr": unguarded_run.stderr,
            "command": unguarded_cmd,
        },
        "actual_database_runtime": {
            "result": "PASS",
            "database_calls": {"OpenDB": 4, "OpenIndex": 4, "FindIndex": 24,
                                "DBRecall": 16, "CloseDB": 4},
            "cases": actual_rows,
            "stdout": runtime_run.stdout,
            "stderr": runtime_run.stderr,
            "command": runtime_cmd,
            "scope": "Generated actual OpenDB/OpenIndex/DBRecall/LZSS/CloseDB with only FindIndex provided by the guard helper; validates last-row hits, above-maximum and invalid-kind misses, empty table early return, real raw/compressed resource payloads compared to portable_db_load.",
        },
        "boundary_semantics": {
            "preserved": ["binary-search updates", "fd_50F6_3956 cursor", "fd_50F6_3952 cursor pointer assignment"],
            "changed_native_case": "if lower-bound insertion rank equals active count, return NULL before reading id/kind",
            "excluded": "original DOS heap residue at index[count]; a matching initialized DOS sentinel still returns its pointer in the original and is intentionally changed by the native safety adapter",
            "empty_table": "original early return with cursor=0 and no cursor-pointer reassignment; retained",
            "actual_onepast_native": "forms and preserves legal C one-past pointer, then returns before dereference",
        },
        "oracle": {"sha256": oracle.sha256, "unicorn": behavior.uc.__version__,
                   "fresh_dos_target_invocations": len(dos_controls["cases"]),
                   "original_dos_calls_in_actual_database_runtime": 0},
        "compiler": {"path": str(gcc), "version": gcc_version,
                     "identity_before": gcc_before, "identity_after": gcc_after},
        "inputs_before": before,
        "inputs_after": after,
        "native_binary_hashes": {
            "guarded_test": identity(native_exe),
            "unguarded_negative": identity(unguarded_exe),
            "actual_runtime": identity(runtime_exe),
            "dos_candidate_object": dos_controls["candidate_object_sha256"],
        },
        "build_work_directory": work.relative_to(ROOT).as_posix(),
    }
    (out / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (out / "findindex-guard-dos-function.c").write_text(dos_text, encoding="latin1")
    (out / "findindex-guard-native.c").write_text(host_text, encoding="latin1")
    (out / "native-stdout.txt").write_text(native_run.stdout, encoding="utf-8")
    (out / "runtime-stdout.txt").write_text(runtime_run.stdout, encoding="utf-8")
    (out / "compile-diagnostics.json").write_text(json.dumps({
        "native_guarded": {"returncode": native_compile.returncode,
                           "stdout": native_compile.stdout, "stderr": native_compile.stderr},
        "unguarded_negative": {"returncode": unguarded_compile.returncode,
                               "stdout": unguarded_compile.stdout, "stderr": unguarded_compile.stderr},
        "generated_m1986": {"returncode": generated_compile.returncode,
                             "stdout": generated_compile.stdout, "stderr": generated_compile.stderr},
        "actual_runtime": {"returncode": runtime_compile.returncode,
                           "stdout": runtime_compile.stdout, "stderr": runtime_compile.stderr},
    }, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "out": out.relative_to(ROOT).as_posix(),
                      "dos_equal": dos_controls["equal_nonmatching_controls"],
                      "dos_expected_residue_differences": dos_controls["intentional_matching_sentinel_differences"],
                      "runtime_databases": len(actual_rows)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
