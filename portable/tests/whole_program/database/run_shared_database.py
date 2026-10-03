#!/usr/bin/env python3
"""Bounded actual-TU integration check for whole-program DB owner/layout.

Write-once: --out must name a new directory. The DOS behavior comparison is
inherited only from the separately pinned database-dos-differential packet.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "portable" / "tests" / "whole_program" / "database"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def le16(b: bytes, o: int) -> int:
    return struct.unpack_from("<h", b, o)[0]


def leu16(b: bytes, o: int) -> int:
    return struct.unpack_from("<H", b, o)[0]


def parse_index(path: Path) -> tuple[int, list[bytes], list[tuple[int, int, int, int]]]:
    raw = path.read_bytes()
    if len(raw) < 20:
        raise ValueError(f"{path.name}: truncated NDX header")
    count = leu16(raw, 0)
    if len(raw) != 20 + (count + 32) * 8:
        raise ValueError(f"{path.name}: NDX extent/count mismatch")
    rows = [raw[20 + 8 * i:28 + 8 * i] for i in range(count + 1)]
    decoded = []
    for i, row in enumerate(rows):
        off = struct.unpack_from("<I", row, 0)[0]
        ident = le16(row, 4)
        kind, flags = row[6], row[7]
        decoded.append((off, ident, kind, flags))
        if i < count and i and (decoded[i - 1][2], decoded[i - 1][1]) > (kind, ident):
            raise ValueError(f"{path.name}: active entries not sorted at {i}")
    return count, rows, decoded


def queries(count: int, decoded: list[tuple[int, int, int, int]]) -> list[tuple[int, int]]:
    keys = [(ident, kind) for _, ident, kind, _ in decoded[:count]]
    result: set[tuple[int, int]] = set(keys)
    for ident, kind in keys:
        if ident > -32768:
            result.add((ident - 1, kind))
        if ident < 32767:
            result.add((ident + 1, kind))
    kinds = sorted({kind for _, kind in keys})
    for kind in kinds:
        result.update({(-32768, kind), (-1, kind), (0, kind), (32767, kind)})
    result.update({(-32768, -1), (-1, -1), (0, -1), (32767, -1),
                   (-32768, 256), (-1, 256), (0, 256), (32767, 256)})
    # Expose the reserved row and the precise active_count one-past read.
    _, look_id, look_kind, _ = decoded[count]
    result.add((look_id, look_kind))
    last_id, last_kind = keys[-1]
    if last_id < 32767:
        result.add((last_id + 1, last_kind))
    elif last_kind < 255:
        result.add((-32768, last_kind + 1))
    return sorted(result)


def lower_bound(rows: list[tuple[int, int, int, int]], count: int,
                ident: int, kind: int) -> int:
    lo, hi = 0, count
    while lo < hi:
        mid = lo + (hi - lo) // 2
        row_kind, row_id = rows[mid][2], rows[mid][1]
        if row_kind < kind or (row_kind == kind and row_id < ident):
            lo = mid + 1
        else:
            hi = mid
    return lo


def file_identity(path: Path) -> dict:
    try:
        display = path.relative_to(ROOT).as_posix()
    except ValueError:
        display = str(path)
    return {"path": display, "sha256": sha(path),
            "size": path.stat().st_size}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, help="new write-once evidence directory")
    ap.add_argument("--gcc", default=r"C:\msys64\mingw64\bin\gcc.exe")
    args = ap.parse_args()
    out = (ROOT / args.out).resolve()
    if out.exists():
        raise SystemExit(f"refusing to overwrite evidence directory: {out}")
    out.mkdir(parents=True)
    gcc = Path(args.gcc).resolve()
    if not gcc.is_file():
        raise SystemExit(f"GCC not found: {gcc}")

    fixed = [
        "portable/tests/whole_program/database/run_shared_database.py",
        "portable/tests/whole_program/database/README.md",
        "portable/tests/whole_program/database/native_driver.c",
        "portable/tests/whole_program/database/unreachable_dependency_traps.c",
        "portable/tests/whole_program/database/reject_legacy_pointer.c",
        "portable/tools/whole_program.py",
        "portable/whole_program/types/database.h",
        "portable/whole_program/state/database.c",
        "build/workers/whole_program/generated/root_m1986.c",
        "build/workers/whole_program/generated/dos_types.h",
        "build/workers/whole_program/generated/migration.json",
        "src/root/m1986.c",
        "evidence/behavior/functions/FindIndex/module.c",
        "portable/research/whole_program_behavior_sources.json",
        "portable/tests/resources/evidence/database-dos-differential.json",
    ]
    assets = [f"assets/{stem}.{ext}" for stem in ("HCEGANT", "SHARED", "SOUND")
              for ext in ("NDX", "DAT")]
    inputs = [ROOT / p for p in fixed + assets]
    if any(not p.is_file() for p in inputs):
        raise SystemExit("one or more required source/evidence/assets are absent")
    pins_before = {p.relative_to(ROOT).as_posix(): file_identity(p) for p in inputs}
    gcc_version = subprocess.run([str(gcc), "--version"], check=True,
                                 capture_output=True, text=True).stdout.splitlines()[0]
    tool_before = {"gcc": file_identity(gcc), "gcc_version": gcc_version,
                   "python": sys.version, "platform": sys.platform}

    datasets = []
    total_cases = 0
    fixture = bytearray(struct.pack("<IH", 0x31424457, 3))
    for stem in ("HCEGANT", "SHARED", "SOUND"):
        count, wire_rows, decoded = parse_index(ROOT / f"assets/{stem}.NDX")
        qs = queries(count, decoded)
        datasets.append({"name": stem, "count": count, "rows": wire_rows,
                         "decoded": decoded, "queries": qs})
        fixture.extend(struct.pack("<h", count))
        fixture.extend(b"".join(wire_rows))
        fixture.extend(struct.pack("<I", len(qs)))
        for ident, kind in qs:
            fixture.extend(struct.pack("<hh", ident, kind))
        total_cases += len(qs)
    fixture_path = out / "fixture.bin"
    fixture_path.write_bytes(fixture)
    fixture_pin = sha(fixture_path)

    driver = ROOT / "portable/tests/whole_program/database/native_driver.c"
    generated = ROOT / "build/workers/whole_program/generated/root_m1986.c"
    owner = ROOT / "portable/whole_program/state/database.c"
    executable = out / "database-actual-tu.exe"
    compile_cmd = [str(gcc), "-std=c11", "-O0", "-fsigned-char", "-fno-builtin-sprintf",
                   "-ffunction-sections", "-fdata-sections", "-Werror=implicit-function-declaration",
                   "-I", str(ROOT), str(generated), str(owner), str(driver),
                   str(ROOT / "portable/tests/whole_program/database/unreachable_dependency_traps.c"),
                   "-Wl,--gc-sections", "-o", str(executable)]
    compile_run = subprocess.run(compile_cmd, capture_output=True, text=True)
    (out / "compile.stdout.txt").write_text(compile_run.stdout, encoding="utf-8")
    (out / "compile.stderr.txt").write_text(compile_run.stderr, encoding="utf-8")
    if compile_run.returncode:
        raise SystemExit(f"actual generated TU compile failed ({compile_run.returncode})")

    exe_run = subprocess.run([str(executable), str(fixture_path)], capture_output=True,
                              text=True, check=True)
    (out / "native-observations.csv").write_text(exe_run.stdout, encoding="ascii")
    actual = [tuple(map(int, line.split(","))) for line in exe_run.stdout.splitlines()]
    if len(actual) != total_cases:
        raise SystemExit(f"native emitted {len(actual)} rows; expected {total_cases}")

    cursor_mismatches = return_mismatches = home_mismatches = 0
    hits = misses = onepast_reads = lookahead_hits = 0
    index = 0
    transcripts = hashlib.sha256()
    for di, dataset in enumerate(datasets):
        count, rows, qs = dataset["count"], dataset["decoded"], dataset["queries"]
        for qi, (ident, kind) in enumerate(qs):
            (d, q, cursor, got_id, got_kind, ret_rank, ret_offset, ret_id,
             ret_kind, ret_flags, home_rank, home_offset, home_id,
             home_kind, home_flags) = actual[index]
            index += 1
            expected_low = lower_bound(rows, count, ident, kind)
            expected_rank = expected_low if (
                rows[expected_low][1] == ident and rows[expected_low][2] == kind
            ) else -1
            if expected_rank >= 0:
                hits += 1
                expected_return = rows[expected_rank]
                expected_return_fields = (expected_return[0], expected_return[1],
                                          expected_return[2], expected_return[3])
            else:
                misses += 1
                expected_return_fields = (-1, -1, 0, 0)
            expected_home = rows[expected_low]
            expected_home_fields = (expected_home[0], expected_home[1],
                                     expected_home[2], expected_home[3])
            if expected_low == count:
                onepast_reads += 1
            if expected_rank == count:
                lookahead_hits += 1
            cursor_mismatches += cursor != expected_low
            return_mismatches += ret_rank != expected_rank
            home_mismatches += home_rank != expected_low
            return_mismatches += (ret_offset, ret_id, ret_kind, ret_flags) != expected_return_fields
            home_mismatches += (home_offset, home_id, home_kind, home_flags) != expected_home_fields
            if (d, q, got_id, got_kind) != (di, qi, ident, kind):
                raise SystemExit(f"misassociated output row at dataset {di}, query {qi}")
            transcripts.update(struct.pack("<HhhhhhIhBBIhBB", cursor, ident, kind,
                                           expected_rank, home_rank, expected_low,
                                           ret_offset & 0xffffffff, ret_id, ret_kind,
                                           ret_flags, home_offset & 0xffffffff,
                                           home_id, home_kind, home_flags))
    if cursor_mismatches or return_mismatches or home_mismatches:
        raise SystemExit({"cursor_mismatches": cursor_mismatches,
                          "return_mismatches": return_mismatches,
                          "home_mismatches": home_mismatches})

    # A host-pointer-bearing row is expected to fail the DOS wire-size assertion.
    neg_src = ROOT / "portable/tests/whole_program/database/reject_legacy_pointer.c"
    neg_obj = out / "legacy-pointer-negative.o"
    neg = subprocess.run([str(gcc), "-std=c11", "-c", str(neg_src), "-o", str(neg_obj)],
                         capture_output=True, text=True)
    (out / "legacy-pointer-negative.stderr.txt").write_text(neg.stderr, encoding="utf-8")
    if neg.returncode == 0 or neg_obj.exists():
        raise SystemExit("negative pointer-layout control unexpectedly compiled")

    pins_after = {p.relative_to(ROOT).as_posix(): file_identity(p) for p in inputs}
    tool_after = {"gcc": file_identity(gcc), "gcc_version": gcc_version,
                  "python": sys.version, "platform": sys.platform}
    if pins_before != pins_after or tool_before != tool_after:
        raise SystemExit("source, asset, or tool identity changed during run")
    report = {
        "schema": "simant-whole-program-db-integration-v1",
        "status": "PASS_DIAGNOSTIC_NO_ACCEPTANCE_CLAIM",
        "actual_body": "generated root_m1986.c::FindIndex, linked with actual shared state/database.c",
        "unreached_dependencies": "OpenIndex/CloseIndex-only Punt, DosPunt, f_171C_13CA and dos_free references have fail-fast abort traps; these are not successful behavioral stubs and are not called by FindIndex.",
        "compile": {"command": compile_cmd, "returncode": compile_run.returncode,
                    "stdout_sha256": sha(out / "compile.stdout.txt"),
                    "stderr_sha256": sha(out / "compile.stderr.txt"),
                    "binary_sha256": sha(executable)},
        "fixture": {"path": fixture_path.name, "sha256": fixture_pin,
                    "size": fixture_path.stat().st_size},
        "native_observations": {"path": "native-observations.csv",
                                "sha256": sha(out / "native-observations.csv"),
                                "rows": len(actual)},
        "tables": [{"asset": d["name"], "active_entries": d["count"],
                    "wire_rows_including_reserved_lookahead": d["count"] + 1,
                    "queries": len(d["queries"]),
                    "ndx_sha256": pins_before[f"assets/{d['name']}.NDX"]["sha256"]}
                   for d in datasets],
        "cases": {"count": total_cases, "hits": hits, "misses": misses,
                  "low_equals_active_count_reads": onepast_reads,
                  "reserved_lookahead_matches": lookahead_hits,
                  "cursor_mismatches": cursor_mismatches,
                  "return_pointer_mismatches": return_mismatches,
                  "global_pointer_home_mismatches": home_mismatches,
                  "returned_entry_fields_and_home_entry_fields_compared": True,
                  "expected_observation_sha256": transcripts.hexdigest()},
        "wire_layout": {"IndexEntry_size": 8, "IndexEntry_offsets":
                        {"offset": 0, "id": 4, "kind": 6, "flags": 7},
                        "every_fixture_row_is_copied_from_asset_wire_bytes": True,
                        "legacy_host_pointer_negative_control": "compile rejected as expected"},
        "domain_hazard": "For a miss whose insertion rank equals active count, FindIndex dereferences index[count]. The fixture supplies the asset's actual first reserved NDX row. This validates the historical behavior only for the captured reserved row; it does not make arbitrary one-past pointers safe.",
        "dos_comparison": {"fresh_dos_call": False,
                           "prior_original_dos_evidence": "portable/tests/resources/evidence/database-dos-differential.json",
                           "prior_cases": 1454, "prior_mismatches": 0,
                           "prior_oracle_sha256": "aa0596c6766322a8229ee3c36e57048c92adc82d50fbe2ef37afb8b85fcf4f11"},
        "source_and_asset_pins": pins_before,
        "toolchain_before_after": {"before": tool_before, "after": tool_after},
        "replay": f"python portable/tests/whole_program/database/run_shared_database.py --out {out.relative_to(ROOT).as_posix()}"
    }
    (out / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "cases": total_cases,
                      "hits": hits, "misses": misses,
                      "onepast": onepast_reads, "lookahead_hits": lookahead_hits,
                      "observation_sha256": transcripts.hexdigest(),
                      "report": str((out / "report.json").relative_to(ROOT).as_posix())},
                     indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
