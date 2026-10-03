#!/usr/bin/env python3
"""Direct original-DOS and native whole-program LZSS state-machine comparison.

Outputs and DLLs are write-once scratch. The JSON receipt is likewise refused
if it already exists. No original object or executable is modified.
"""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
import time
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tools" / "behavior_suites"))
sys.path.insert(0, str(ROOT / "portable" / "tests" / "resources" / "evidence"))
import behavior
import exe
import functions
import database_dos_differential as prior_db

GCC_DEFAULT = Path(r"C:\msys64\mingw64\bin\gcc.exe")
DOS_DS = 0xA000
SRC_OFF = 0x3000
DST_OFF = 0x5000
GUARD = 16
CANARY = 0xA7
CHUNKS_VARIABLE = (1, 2, 3, 7, 16, 31, 255, 1024, 17, 64, 511)
DOS_CHUNK_SIZES = (1, 2, 3, 7, 16)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def identity(path: Path) -> dict:
    try:
        label = path.relative_to(ROOT).as_posix()
    except ValueError:
        label = str(path)
    return {"path": label, "size": path.stat().st_size, "sha256": sha(path)}


def parse_records() -> list[dict]:
    records: list[dict] = []
    for stem in ("HCEGANT", "SHARED", "SOUND"):
        ndx = (ROOT / "assets" / f"{stem}.NDX").read_bytes()
        dat = (ROOT / "assets" / f"{stem}.DAT").read_bytes()
        if len(ndx) < 20 or len(dat) < 14 or struct.unpack_from("<I", dat)[0] != 0x12345678:
            raise ValueError(f"{stem}: unexpected DB header")
        count = struct.unpack_from("<H", ndx)[0]
        for i in range(count):
            entry = ndx[20 + i * 8:28 + i * 8]
            offset, ident, kind, flags = struct.unpack("<IhBB", entry)
            if not (flags & 1) or (flags & 4):
                continue
            header_at = 14 + offset
            if header_at + 10 > len(dat):
                raise ValueError(f"{stem} entry {i}: DAT header outside file")
            marker, reserved = struct.unpack_from("<IH", dat, header_at)
            if marker != 0x12345678 or reserved != 0:
                raise ValueError(f"{stem} entry {i}: invalid DAT record marker")
            stored_size = struct.unpack_from("<H", dat, header_at + 6)[0]
            packed_at = header_at + 10
            if stored_size < 2 or packed_at + stored_size > len(dat):
                raise ValueError(f"{stem} entry {i}: compressed extent outside DAT")
            stored = dat[packed_at:packed_at + stored_size]
            output_size = struct.unpack_from("<H", stored)[0]
            packed = stored[2:]
            if output_size == 0 or len(packed) > 0x7fff:
                raise ValueError(f"{stem} entry {i}: outside decoder ABI domain")
            records.append({"stem": stem, "index": i, "id": ident, "kind": kind,
                            "flags": flags, "offset": offset, "packed": packed,
                            "output_size": output_size})
    if len(records) != 205:
        raise AssertionError(f"expected 205 compressed DB records, found {len(records)}")
    return records


def native_bind(path: Path):
    lib = ctypes.CDLL(str(path.resolve()))
    lib.f_1B05_0008.argtypes = [ctypes.POINTER(ctypes.c_uint8), ctypes.c_int16]
    lib.f_1B05_0008.restype = None
    lib.f_1B05_0046.argtypes = [ctypes.POINTER(ctypes.c_uint8), ctypes.c_uint16]
    lib.f_1B05_0046.restype = ctypes.c_uint16
    return lib


def native_decode(lib, rec: dict, chunks: tuple[int, ...]) -> tuple[bytes, list[int], bytes, bytes]:
    packed = rec["packed"]
    packed_array = (ctypes.c_uint8 * max(1, len(packed)))()
    if packed:
        ctypes.memmove(packed_array, packed, len(packed))
    lib.f_1B05_0008(packed_array, len(packed))
    out_size = rec["output_size"]
    slab = (ctypes.c_uint8 * (GUARD + out_size + GUARD))()
    ctypes.memset(slab, CANARY, ctypes.sizeof(slab))
    produced = 0
    returns: list[int] = []
    k = 0
    while produced < out_size:
        request = min(chunks[k % len(chunks)], out_size - produced)
        target = ctypes.cast(ctypes.byref(slab, GUARD + produced),
                             ctypes.POINTER(ctypes.c_uint8))
        got = int(lib.f_1B05_0046(target, request))
        returns.append(got)
        if got != request:
            raise AssertionError({"lane": "native", "record": rec_label(rec),
                                  "chunk_index": k, "requested": request, "returned": got})
        produced += got
        k += 1
    raw = bytes(slab)
    pre = raw[:GUARD]
    decoded = raw[GUARD:GUARD + out_size]
    post = raw[GUARD + out_size:]
    if pre != bytes([CANARY]) * GUARD or post != bytes([CANARY]) * GUARD:
        raise AssertionError({"lane": "native", "record": rec_label(rec), "canary": "changed"})
    return decoded, returns, pre, post


def rec_label(rec: dict) -> str:
    return f"{rec['stem']}/{rec['id']}/{rec['kind']}"


def make_oracle_machine():
    first = functions.get("f_1B05_0008")
    vectors = {exe.MANAGER_SEG * 16 + v.offset: v for v in exe.load().vectors}
    pair = SimpleNamespace(function=first, sequence_targets=frozenset(),
                           sequence_function=lambda name: functions.get(name), vectors=vectors)
    return behavior.Machine(pair)


def oracle_stream(machine, rec: dict, chunks: tuple[int, ...], ordinal: int,
                  first_call: bool) -> tuple[bytes, list[int], bytes, bytes]:
    packed = rec["packed"]
    out_size = rec["output_size"]
    slab = bytes([CANARY]) * (GUARD + out_size + GUARD)
    writes = [(DOS_DS * 16 + SRC_OFF, packed),
              (DOS_DS * 16 + DST_OFF - GUARD, slab)]
    init = behavior.Case(label=f"lzss-init/{ordinal}",
                         args=[SRC_OFF, DOS_DS, len(packed)], writes=writes,
                         return_kind="void")
    if first_call:
        machine.run(init, function="f_1B05_0008")
    else:
        machine.write(DOS_DS * 16 + SRC_OFF, packed)
        machine.write(DOS_DS * 16 + DST_OFF - GUARD, slab)
        machine.run(behavior.Case(label=init.label, args=init.args, return_kind="void"),
                    preserve=True, function="f_1B05_0008")

    produced = 0
    returns: list[int] = []
    k = 0
    while produced < out_size:
        request = min(chunks[k % len(chunks)], out_size - produced)
        case = behavior.Case(label=f"lzss-expand/{ordinal}/{k}",
                             args=[DST_OFF + produced, DOS_DS, request],
                             return_kind="u16")
        result = machine.run(case, preserve=True, function="f_1B05_0046")
        got = int(result["return"])
        returns.append(got)
        if got != request:
            raise AssertionError({"lane": "original_dos", "record": rec_label(rec),
                                  "chunk_index": k, "requested": request, "returned": got})
        produced += got
        k += 1
    base = DOS_DS * 16 + DST_OFF
    decoded = machine.read(base, out_size)
    pre = machine.read(base - GUARD, GUARD)
    post = machine.read(base + out_size, GUARD)
    expected_guard = bytes([CANARY]) * GUARD
    if pre != expected_guard or post != expected_guard:
        raise AssertionError({"lane": "original_dos", "record": rec_label(rec),
                              "canary": "changed"})
    return decoded, returns, pre, post


def feed_digest(digest, rec: dict, output: bytes) -> None:
    digest.update(rec["stem"].encode("ascii") + b"\0")
    digest.update(struct.pack("<hBH", rec["id"], rec["kind"], len(output)))
    digest.update(output)


def choose_representatives(records: list[dict]) -> list[dict]:
    by_output = max(records, key=lambda r: r["output_size"])
    by_input = max(records, key=lambda r: len(r["packed"]))
    by_ratio = max(records, key=lambda r: r["output_size"] / max(1, len(r["packed"])))
    by_short = min(records, key=lambda r: r["output_size"])
    selected = []
    seen = set()
    for rec in (by_short, by_input, by_output, by_ratio):
        key = rec_label(rec)
        if key not in seen:
            selected.append(rec)
            seen.add(key)
    return selected


def directed_ring_controls(dll_path: Path, mutant_dll_path: Path) -> dict:
    """Prove initial-zero versus retained top-18 ring bytes in both lanes."""
    literal = {"stem": "synthetic", "id": 1, "kind": 0, "packed": b"\x07ABC",
               "output_size": 3}
    backref = {"stem": "synthetic", "id": 2, "kind": 0, "packed": b"\x00\xEE\xF0",
               "output_size": 3}
    expected_cold = b"\x00\x00\x00"
    expected_retained = b"ABC"

    cold_lib = native_bind(dll_path)
    cold, _, _, _ = native_decode(cold_lib, backref, (3,))
    if cold != expected_cold:
        raise AssertionError({"lane": "native-cold-ring", "expected": expected_cold.hex(),
                              "actual": cold.hex()})
    native = native_bind(dll_path)
    literal_out, _, _, _ = native_decode(native, literal, (3,))
    retained, _, _, _ = native_decode(native, backref, (3,))
    if literal_out != expected_retained or retained != expected_retained:
        raise AssertionError({"lane": "native-retained-ring", "literal": literal_out.hex(),
                              "actual": retained.hex()})

    cold_machine = make_oracle_machine()
    dos_cold, _, _, _ = oracle_stream(cold_machine, backref, (3,), 0, True)
    if dos_cold != expected_cold:
        raise AssertionError({"lane": "dos-cold-ring", "expected": expected_cold.hex(),
                              "actual": dos_cold.hex()})
    machine = make_oracle_machine()
    dos_literal, _, _, _ = oracle_stream(machine, literal, (3,), 0, True)
    dos_retained, _, _, _ = oracle_stream(machine, backref, (3,), 1, False)
    if dos_literal != expected_retained or dos_retained != expected_retained:
        raise AssertionError({"lane": "dos-retained-ring", "literal": dos_literal.hex(),
                              "actual": dos_retained.hex()})

    wrong_full_ring_reset = b" " * 3
    if wrong_full_ring_reset in (expected_cold, expected_retained):
        raise AssertionError("negative-control construction is not discriminating")
    mutant = native_bind(mutant_dll_path)
    mutant_cold, _, _, _ = native_decode(mutant, backref, (3,))
    if mutant_cold != wrong_full_ring_reset or mutant_cold == expected_cold:
        raise AssertionError({"lane": "wrong-full-ring-init-negative-control",
                              "expected": wrong_full_ring_reset.hex(),
                              "actual": mutant_cold.hex()})
    return {"cold_backreference_dos_hex": dos_cold.hex(),
            "cold_backreference_native_hex": cold.hex(),
            "literal_then_reinit_dos_hex": dos_retained.hex(),
            "literal_then_reinit_native_hex": retained.hex(),
            "wrong_full_ring_spaces_reset_hex": wrong_full_ring_reset.hex(),
            "mutant_full_ring_init_hex": mutant_cold.hex(),
            "mutant_full_ring_init_detected": True,
            "ring_position": "0xFEE", "literal_seed": "ABC",
            "backreference_stream_hex": backref["packed"].hex(), "mismatches": 0}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--work", required=True, help="new isolated directory under build/workers")
    ap.add_argument("--receipt", default="portable/tests/whole_program/lzss-dos-native-v3.json")
    ap.add_argument("--gcc", default=str(GCC_DEFAULT))
    args = ap.parse_args()
    work = (ROOT / args.work).resolve()
    workers = (ROOT / "build/workers").resolve()
    if workers not in work.parents:
        raise SystemExit("--work must be a new directory under build/workers")
    receipt = ROOT / args.receipt
    if receipt.exists():
        raise SystemExit(f"refusing to overwrite receipt {receipt}")
    if work.exists():
        raise SystemExit(f"refusing to overwrite work directory {work}")
    work.mkdir(parents=True)
    receipt.parent.mkdir(parents=True, exist_ok=True)

    gcc = Path(args.gcc).resolve()
    asm = ROOT / "src/root/m1B05.asm"
    native_c = ROOT / "portable/whole_program/algorithms/lzss.c"
    native_h = ROOT / "portable/whole_program/algorithms/lzss.h"
    suite = Path(__file__).resolve()
    prior_suite = ROOT / "portable/tests/resources/evidence/database_dos_differential.py"
    pin_rel = ["src/root/m1B05.asm", "portable/whole_program/algorithms/lzss.c",
               "portable/whole_program/algorithms/lzss.h",
               "portable/tests/whole_program/run_lzss_dos_differential.py",
               "portable/tests/resources/evidence/database_dos_differential.py",
               "tools/behavior.py", "tools/exe.py", "tools/functions.py",
               "tools/match.py", "tools/modctx.py", "tools/modules.py",
               "tools/symbols.py", "tools/omf.py",
               "tools/behavior_suites/small_contracts.py",
               "layout/oracle.lock.json", "layout/toolchain.json",
               "evidence/toolchain/runtime-location.json"]
    for stem in ("HCEGANT", "SHARED", "SOUND"):
        pin_rel.extend([f"assets/{stem}.NDX", f"assets/{stem}.DAT"])
    pins_before = {rel: identity(ROOT / rel) for rel in pin_rel}
    if not gcc.is_file():
        raise SystemExit(f"GCC does not exist: {gcc}")
    gcc_before = identity(gcc)
    gcc_version = subprocess.run([str(gcc), "--version"], check=True,
                                 capture_output=True, text=True).stdout.splitlines()[0]
    tool_id = {"gcc": gcc_before, "gcc_version": gcc_version,
               "python": sys.version, "platform": sys.platform,
               "unicorn": behavior.uc.__version__}
    oracle = exe.load()
    records = parse_records()

    dlls: dict[str, Path] = {}
    compile_records = {}
    for lane in ("full", "chunk1", "chunkvar"):
        dll = work / f"lzss-{lane}.dll"
        cmd = [str(gcc), "-std=c11", "-O0", "-Wall", "-Wextra", "-Werror",
               "-shared", "-I", str(ROOT / "portable/whole_program/algorithms"),
               str(native_c), "-o", str(dll)]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        (work / f"compile-{lane}.stdout.txt").write_text(proc.stdout, encoding="utf-8")
        (work / f"compile-{lane}.stderr.txt").write_text(proc.stderr, encoding="utf-8")
        if proc.returncode:
            raise SystemExit(f"native {lane} compile failed: {proc.stderr}")
        dlls[lane] = dll
        compile_records[lane] = {"command": cmd, "returncode": proc.returncode,
                                 "dll_sha256": sha(dll),
                                 "stdout_sha256": sha(work / f"compile-{lane}.stdout.txt"),
                                 "stderr_sha256": sha(work / f"compile-{lane}.stderr.txt")}

    source_text = native_c.read_text(encoding="utf-8")
    original_fill = "memset(ring, 0x20, 0xfee);"
    if source_text.count(original_fill) != 1:
        raise SystemExit("cannot make bounded full-ring-init negative control")
    mutant_source = work / "lzss-full-ring-mutant.c"
    mutant_source.write_text(source_text.replace(original_fill,
                                                  "memset(ring, 0x20, sizeof(ring));"),
                             encoding="utf-8")
    mutant_dll = work / "lzss-full-ring-mutant.dll"
    mutant_cmd = [str(gcc), "-std=c11", "-O0", "-Wall", "-Wextra", "-Werror",
                  "-shared", "-I", str(native_c.parent), str(mutant_source),
                  "-o", str(mutant_dll)]
    mutant_proc = subprocess.run(mutant_cmd, capture_output=True, text=True)
    (work / "compile-mutant.stdout.txt").write_text(mutant_proc.stdout, encoding="utf-8")
    (work / "compile-mutant.stderr.txt").write_text(mutant_proc.stderr, encoding="utf-8")
    if mutant_proc.returncode:
        raise SystemExit(f"ring-init negative-control compile failed: {mutant_proc.stderr}")
    compile_records["wrong_full_ring_init_negative_control"] = {
        "command": mutant_cmd, "source_sha256": sha(mutant_source),
        "returncode": mutant_proc.returncode, "dll_sha256": sha(mutant_dll),
        "stdout_sha256": sha(work / "compile-mutant.stdout.txt"),
        "stderr_sha256": sha(work / "compile-mutant.stderr.txt")}

    # Direct DOS baseline and independently loaded whole-record native baseline.
    machine = make_oracle_machine()
    native_full = native_bind(dlls["full"])
    baseline_outputs: list[bytes] = []
    baseline_counts: list[int] = []
    digest_dos = hashlib.sha256()
    digest_native = hashlib.sha256()
    started = time.time()
    for i, rec in enumerate(records):
        oracle_out, oracle_returns, _, _ = oracle_stream(machine, rec,
                                                         (rec["output_size"],), i,
                                                         first_call=(i == 0))
        native_out, native_returns, _, _ = native_decode(native_full, rec,
                                                         (rec["output_size"],))
        if oracle_returns != [rec["output_size"]] or native_returns != [rec["output_size"]]:
            raise AssertionError(f"{rec_label(rec)}: whole-call return count differs")
        if oracle_out != native_out:
            mismatch = next((j for j, (a, b) in enumerate(zip(oracle_out, native_out)) if a != b), None)
            raise AssertionError({"record": rec_label(rec), "lane": "whole-call", "first_mismatch": mismatch,
                                  "dos_len": len(oracle_out), "native_len": len(native_out),
                                  "dos_prefix": oracle_out[:32].hex(), "native_prefix": native_out[:32].hex()})
        baseline_outputs.append(oracle_out)
        baseline_counts.append(oracle_returns[0])
        feed_digest(digest_dos, rec, oracle_out)
        feed_digest(digest_native, rec, native_out)
        if (i + 1) % 50 == 0:
            (work / "progress.txt").write_text(
                f"paired whole-record: {i+1}/{len(records)}\nelapsed={time.time()-started:.2f}s\n",
                encoding="utf-8")
    if digest_dos.digest() != digest_native.digest():
        raise AssertionError("whole-record ordered DOS/native digest differs")

    helper_machine = prior_db.original_lzss_machine()
    helper_digest = hashlib.sha256()
    for i, rec in enumerate(records):
        returned, decoded = prior_db.original_lzss_decode(
            helper_machine, rec["packed"], rec["output_size"], i)
        if returned != rec["output_size"] or decoded != baseline_outputs[i]:
            mismatch = next((j for j, (a, b) in enumerate(zip(decoded, baseline_outputs[i]))
                             if a != b), None)
            raise AssertionError({"record": rec_label(rec), "lane": "shared-original-helper",
                                  "return": returned, "first_mismatch": mismatch})
        feed_digest(helper_digest, rec, decoded)
    # chunkvar has not been called yet and is a fresh process-static ring.
    ring_controls = directed_ring_controls(dlls["chunkvar"], mutant_dll)

    # Native full corpus through one-byte output calls.
    native_one = native_bind(dlls["chunk1"])
    native_chunk1_digest = hashlib.sha256()
    native_chunk1_calls = 0
    for i, rec in enumerate(records):
        got, returns, _, _ = native_decode(native_one, rec, (1,))
        if got != baseline_outputs[i]:
            raise AssertionError({"record": rec_label(rec), "lane": "native-chunk1",
                                  "first_mismatch": next((j for j, (a, b) in enumerate(zip(got, baseline_outputs[i])) if a != b), None)})
        feed_digest(native_chunk1_digest, rec, got)
        native_chunk1_calls += len(returns)

    # Native full corpus across irregular output boundaries (including sizes
    # that repeatedly interrupt active back-references).
    native_var = native_bind(dlls["chunkvar"])
    native_var_digest = hashlib.sha256()
    native_var_calls = 0
    for i, rec in enumerate(records):
        got, returns, _, _ = native_decode(native_var, rec, CHUNKS_VARIABLE)
        if got != baseline_outputs[i]:
            raise AssertionError({"record": rec_label(rec), "lane": "native-variable-chunks",
                                  "first_mismatch": next((j for j, (a, b) in enumerate(zip(got, baseline_outputs[i])) if a != b), None)})
        feed_digest(native_var_digest, rec, got)
        native_var_calls += len(returns)

    # Fresh DOS resumes on selected records. Each partition size gets a new
    # original machine so its initial ring contents match static-zero native
    # process state; selected records retain their local previous-stream order.
    representatives = choose_representatives(records)
    dos_partition_results = []
    dos_partition_calls = 0
    for chunk_size in DOS_CHUNK_SIZES:
        part_machine = make_oracle_machine()
        part_digest = hashlib.sha256()
        for j, rec in enumerate(representatives):
            out, returns, _, _ = oracle_stream(part_machine, rec, (chunk_size,), j,
                                                first_call=(j == 0))
            if out != baseline_outputs[records.index(rec)]:
                raise AssertionError({"record": rec_label(rec), "lane": f"dos-chunk-{chunk_size}",
                                      "first_mismatch": next((k for k, (a, b) in enumerate(zip(out, baseline_outputs[records.index(rec)])) if a != b), None)})
            feed_digest(part_digest, rec, out)
            dos_partition_calls += len(returns)
        dos_partition_results.append({"chunk_size": chunk_size,
                                      "records": len(representatives),
                                      "decoder_calls": sum((r["output_size"] + chunk_size - 1) // chunk_size
                                                           for r in representatives),
                                      "output_sha256": part_digest.hexdigest(),
                                      "mismatches": 0})

    pins_after = {rel: identity(ROOT / rel) for rel in pin_rel}
    gcc_after = identity(gcc)
    if pins_before != pins_after or gcc_before != gcc_after:
        raise SystemExit("a pinned source, oracle, asset, or compiler changed during run")
    count_by_asset = {stem: sum(rec["stem"] == stem for rec in records)
                      for stem in ("HCEGANT", "SHARED", "SOUND")}
    report = {
        "schema": "simant-direct-dos-lzss-state-machine-v1",
        "status": "PASS_DIAGNOSTIC_NO_ACCEPTANCE_CLAIM",
        "oracle": {"sha256": oracle.sha256, "unicorn": behavior.uc.__version__},
        "whole_record_direct_dos_native": {
            "records": len(records), "records_by_asset": count_by_asset,
            "total_output_bytes": sum(map(len, baseline_outputs)),
            "dos_decoder_calls": len(records), "native_decoder_calls": len(records),
            "dos_sha256": digest_dos.hexdigest(), "native_sha256": digest_native.hexdigest(),
            "byte_mismatches": 0, "return_count_mismatches": 0,
            "canary_mismatches": 0},
        "shared_original_lzss_decode_helper": {
            "records": len(records), "dos_decoder_calls": len(records),
            "ordered_output_sha256": helper_digest.hexdigest(),
            "matches_canary_guarded_direct_dos": helper_digest.digest() == digest_dos.digest(),
            "return_mismatches": 0, "output_mismatches": 0,
            "note": "Uses original_lzss_machine/original_lzss_decode from the existing DB DOS differential harness; the primary direct lane adds guard canaries and partitioned calls."},
        "directed_ring_retention_controls": ring_controls,
        "native_partition_resume": {
            "all_205_chunk_size_1": {"decoder_calls": native_chunk1_calls,
                                      "ordered_output_sha256": native_chunk1_digest.hexdigest(),
                                      "matches_direct_dos": native_chunk1_digest.digest() == digest_dos.digest(),
                                      "mismatches": 0},
            "all_205_irregular_sizes": list(CHUNKS_VARIABLE),
            "irregular_decoder_calls": native_var_calls,
            "irregular_ordered_output_sha256": native_var_digest.hexdigest(),
            "irregular_matches_direct_dos": native_var_digest.digest() == digest_dos.digest(),
            "mismatches": 0, "canary_mismatches": 0},
        "fresh_dos_partition_resume": {
            "records": [{"label": rec_label(r), "packed_bytes": len(r["packed"]),
                         "output_bytes": r["output_size"]} for r in representatives],
            "partition_sizes": dos_partition_results,
            "decoder_calls_total": dos_partition_calls,
            "canary_mismatches": 0, "output_mismatches": 0},
        "assembly_state_notes": {
            "init_ring_fill": "Original f_1B05_0008 fills exactly 0xFEE bytes with spaces and leaves the top 18 bytes of the 4096-byte ring unchanged. Native conversion mirrors that; full-corpus ordering begins from static-zero ring storage and keeps ordering in each lane.",
            "match_resume": "Original saves State=5 when output ends immediately after a match byte; the following call decrements MatchLen before the next match byte. Paired tests partition output at sizes 1,2,3,7,16 and irregular native sizes.",
            "input_exhaustion": "Every compressed-record request fully decodes the DAT-declared output size; no truncated-input zero-length or malformed-stream behavior is claimed.",
        },
        "native_compile": compile_records,
        "native_sources_and_harness_before_after": {"before": pins_before, "after": pins_after},
        "toolchain": {"before": tool_id, "after": {"gcc": gcc_after,
                    "gcc_version": gcc_version, "python": sys.version,
                    "platform": sys.platform, "unicorn": behavior.uc.__version__}},
        "scope": "Fresh original-DOS calls execute only f_1B05_0008/f_1B05_0046 on asset-derived packed bytes. No DBRecall, allocator, or decoder precomputation is used. Diagnostic evidence only; no proof-category claim.",
    }
    receipt.parent.mkdir(parents=True, exist_ok=True)
    receipt.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "records": len(records),
                      "bytes": report["whole_record_direct_dos_native"]["total_output_bytes"],
                      "native_chunk1_calls": native_chunk1_calls,
                      "native_variable_calls": native_var_calls,
                      "fresh_dos_chunk_calls": dos_partition_calls,
                      "receipt": receipt.relative_to(ROOT).as_posix()}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
