"""Direct frozen-DOS probes for database lookup and LZSS record expansion.

The oracle calls original DOS entry points in isolated Unicorn machines. The
portable side calls database.c through its C ABI; this is a diagnostic harness,
not an acceptance registration.
"""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import random
import struct
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tools" / "behavior_suites"))
import behavior
import exe
import functions
import small_contracts


class PortableDatabase(ctypes.Structure):
    _fields_ = [
        ("index_file", ctypes.c_void_p),
        ("index_file_size", ctypes.c_size_t),
        ("data_file", ctypes.c_void_p),
        ("data_file_size", ctypes.c_size_t),
        ("entries", ctypes.c_void_p),
        ("entry_count", ctypes.c_size_t),
        ("error", ctypes.c_char * 192),
    ]


class PortableDbIndexEntry(ctypes.Structure):
    _fields_ = [
        ("data_offset", ctypes.c_uint32),
        ("id", ctypes.c_int16),
        ("kind", ctypes.c_uint8),
        ("flags", ctypes.c_uint8),
    ]


class PortableDbRecord(ctypes.Structure):
    _fields_ = [
        ("id", ctypes.c_int16),
        ("kind", ctypes.c_uint8),
        ("index_flags", ctypes.c_uint8),
        ("data_offset", ctypes.c_uint32),
        ("data", ctypes.POINTER(ctypes.c_uint8)),
        ("size", ctypes.c_size_t),
    ]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bind_library(path: Path):
    lib = ctypes.CDLL(str(path.resolve()))
    lib.portable_db_open_files.argtypes = [ctypes.POINTER(PortableDatabase), ctypes.c_char_p, ctypes.c_char_p]
    lib.portable_db_open_files.restype = ctypes.c_int
    lib.portable_db_close.argtypes = [ctypes.POINTER(PortableDatabase)]
    lib.portable_db_load.argtypes = [ctypes.POINTER(PortableDatabase), ctypes.c_int16,
                                     ctypes.c_int16, ctypes.POINTER(PortableDbRecord)]
    lib.portable_db_load.restype = ctypes.c_int
    lib.portable_db_record_free.argtypes = [ctypes.POINTER(PortableDbRecord)]
    lib.portable_db_lookup.argtypes = [ctypes.POINTER(PortableDatabase), ctypes.c_int16,
                                       ctypes.c_int16, ctypes.POINTER(ctypes.POINTER(PortableDbIndexEntry)),
                                       ctypes.POINTER(ctypes.c_size_t)]
    lib.portable_db_lookup.restype = ctypes.c_int
    lib.portable_db_find_index_compat.argtypes = [
        ctypes.POINTER(PortableDbIndexEntry), ctypes.c_size_t,
        ctypes.POINTER(PortableDbIndexEntry), ctypes.c_int16, ctypes.c_int16,
        ctypes.POINTER(ctypes.POINTER(PortableDbIndexEntry)), ctypes.POINTER(ctypes.c_size_t),
    ]
    lib.portable_db_find_index_compat.restype = ctypes.c_int
    return lib


def open_db(lib, stem: str):
    db = PortableDatabase()
    ndx = str(ROOT / "assets" / f"{stem}.NDX").encode()
    dat = str(ROOT / "assets" / f"{stem}.DAT").encode()
    status = lib.portable_db_open_files(ctypes.byref(db), ndx, dat)
    if status != 0:
        raise RuntimeError(f"portable open {stem} failed status={status} error={db.error!r}")
    return db


def record_bytes(lib, db, ident: int, kind: int) -> bytes:
    record = PortableDbRecord()
    status = lib.portable_db_load(ctypes.byref(db), ident, kind, ctypes.byref(record))
    if status != 0:
        raise RuntimeError(f"portable load id={ident} kind={kind} failed status={status}")
    try:
        return bytes(record.data[:record.size]) if record.size else b""
    finally:
        lib.portable_db_record_free(ctypes.byref(record))


def original_lzss_machine():
    first = functions.get("f_1B05_0008")
    vectors = {exe.MANAGER_SEG * 16 + v.offset: v for v in exe.load().vectors}
    pair = SimpleNamespace(
        function=first,
        sequence_targets=frozenset(),
        sequence_function=lambda name: functions.get(name),
        vectors=vectors,
    )
    return behavior.Machine(pair)


def original_lzss_decode(machine, packed: bytes, output_size: int, slot: int):
    src_off = 0x3000
    dst_off = 0x5000
    machine.run(behavior.Case(
        label=f"lzss-init/{slot}",
        args=[src_off, 0xA000, len(packed)],
        writes=[(0xA0000 + src_off, packed)],
        return_kind="void",
    ), function="f_1B05_0008")
    result = machine.run(behavior.Case(
        label=f"lzss-expand/{slot}",
        args=[dst_off, 0xA000, output_size],
        observe=[behavior.Range("decoded", 0xA0000 + dst_off, output_size)],
        return_kind="u16",
    ), preserve=True, function="f_1B05_0046")
    return result["return"], machine.read(0xA0000 + dst_off, output_size)


def run_lzss(lib):
    machine = original_lzss_machine()
    checked = 0
    total_output = 0
    digest = hashlib.sha256()
    largest_input = largest_output = 0
    for stem in ("HCEGANT", "SHARED", "SOUND"):
        db = open_db(lib, stem)
        try:
            entries = ctypes.cast(db.entries, ctypes.POINTER(PortableDbIndexEntry))
            raw = ctypes.string_at(db.data_file, db.data_file_size)
            for i in range(db.entry_count):
                entry = entries[i]
                if not (entry.flags & 1) or (entry.flags & 4):
                    continue
                decoded = record_bytes(lib, db, entry.id, entry.kind)
                # DBRecall strips the two-byte output size before calling the
                # original f_1B05_0008; these bytes remain in the DAT record.
                header = 14 + entry.data_offset
                stored_size = struct.unpack_from("<H", raw, header + 6)[0]
                stored = raw[header + 10:header + 10 + stored_size]
                output_size = struct.unpack_from("<H", stored)[0]
                packed = stored[2:]
                if output_size != len(decoded):
                    raise AssertionError(f"{stem} id={entry.id} output length differs from prefix")
                actual_count, oracle = original_lzss_decode(machine, packed, output_size, checked)
                if actual_count != output_size or oracle != decoded:
                    mismatch = next((j for j, (a, b) in enumerate(zip(oracle, decoded)) if a != b), None)
                    raise AssertionError({
                        "stem": stem, "id": int(entry.id), "kind": int(entry.kind),
                        "declared": output_size, "oracle_count": actual_count,
                        "first_mismatch": mismatch,
                        "oracle_prefix": oracle[:32].hex(), "portable_prefix": decoded[:32].hex(),
                    })
                digest.update(struct.pack("<hB", entry.id, entry.kind))
                digest.update(struct.pack("<I", output_size))
                digest.update(oracle)
                checked += 1
                total_output += output_size
                largest_input = max(largest_input, len(packed))
                largest_output = max(largest_output, output_size)
        finally:
            lib.portable_db_close(ctypes.byref(db))
    return {
        "records_compared": checked,
        "bytes_compared": total_output,
        "max_compressed_input_bytes": largest_input,
        "max_output_bytes": largest_output,
        "ordered_record_output_sha256": digest.hexdigest(),
        "mismatches": 0,
    }


def run_findindex(lib):
    f = functions.get("FindIndex")
    vectors = {exe.MANAGER_SEG * 16 + v.offset: v for v in exe.load().vectors}
    pair = SimpleNamespace(function=f, sequence_targets=frozenset(), vectors=vectors)
    machine = behavior.Machine(pair)
    cases = 0
    found = missing = one_past = bounded_lookahead_matches = 0
    transcript = hashlib.sha256()

    for stem in ("HCEGANT", "SHARED", "SOUND"):
        db = open_db(lib, stem)
        try:
            raw_ndx = Path(ROOT / "assets" / f"{stem}.NDX").read_bytes()
            count = db.entry_count
            parsed = ctypes.cast(db.entries, ctypes.POINTER(PortableDbIndexEntry))
            rows = [(0x1000 + i * 8, int(parsed[i].id), int(parsed[i].kind))
                    for i in range(count)]
            reserved = raw_ndx[20 + count * 8:20 + count * 8 + 8]
            sentinel = (struct.unpack_from("<I", reserved)[0],
                        struct.unpack_from("<h", reserved, 4)[0], reserved[6], reserved[7])

            queries = set()
            for _, ident, kind in rows:
                queries.add((ident, kind))
                if ident > -32768:
                    queries.add((ident - 1, kind))
                if ident < 32767:
                    queries.add((ident + 1, kind))
            kinds = sorted({kind for _, _, kind in rows})
            for kind in kinds:
                queries.update({(-32768, kind), (32767, kind)})
            queries.update({(-32768, -1), (0, -1), (32767, -1),
                            (-32768, 256), (0, 256), (32767, 256)})
            # Probe the actual reserved entry as a prospective lookahead, plus
            # a strictly-after-last key to exercise low == active_count.
            queries.add((sentinel[1], sentinel[2]))
            last_kind = rows[-1][2]
            last_id = rows[-1][1]
            if last_id < 32767:
                queries.add((last_id + 1, last_kind))
            elif last_kind < 255:
                queries.add((-32768, last_kind + 1))

            for ident, kind in sorted(queries):
                case = small_contracts.find_case(
                    f"dataset/{stem}/id{ident}/kind{kind}", rows, ident, kind,
                    sentinel=sentinel,
                )
                observed = machine.run(case)
                low = struct.unpack("<H", bytes.fromhex(observed["ranges"]["fd_50F6_3956"]))[0]
                returned = observed["return"]
                entry_ptr = ctypes.POINTER(PortableDbIndexEntry)()
                rank = ctypes.c_size_t()
                status = lib.portable_db_lookup(ctypes.byref(db), ident, kind,
                                                ctypes.byref(entry_ptr), ctypes.byref(rank))
                if int(rank.value) != low:
                    raise AssertionError(f"{stem} id={ident} kind={kind}: low {low} != portable {rank.value}")
                native_sentinel = PortableDbIndexEntry(
                    struct.unpack_from("<I", reserved)[0],
                    struct.unpack_from("<h", reserved, 4)[0], reserved[6], reserved[7]
                )
                compat_entry = ctypes.POINTER(PortableDbIndexEntry)()
                compat_rank = ctypes.c_size_t()
                compat_status = lib.portable_db_find_index_compat(
                    ctypes.cast(db.entries, ctypes.POINTER(PortableDbIndexEntry)), count,
                    ctypes.byref(native_sentinel), ident, kind,
                    ctypes.byref(compat_entry), ctypes.byref(compat_rank))
                if compat_rank.value != low:
                    raise AssertionError(f"{stem} id={ident} kind={kind}: compat rank differs")
                if status != 0 and compat_status == 0:
                    bounded_lookahead_matches += 1
                if compat_status == 0:
                    expected_ptr = (0xA000 << 16) | (0x1000 + 8 * low)
                    if returned != expected_ptr:
                        raise AssertionError(f"{stem} hit id={ident} kind={kind}: return {returned:#x} != {expected_ptr:#x}")
                    found += 1
                else:
                    if returned != 0:
                        raise AssertionError(f"{stem} miss id={ident} kind={kind}: DOS returned {returned:#x}")
                    missing += 1
                if low == count:
                    one_past += 1
                transcript.update(stem.encode() + struct.pack("<hhH", ident, kind, low))
                transcript.update(struct.pack("<I", returned or 0))
                cases += 1
        finally:
            lib.portable_db_close(ctypes.byref(db))

    return {"cases": cases, "hits_including_reserved_lookahead": found, "misses": missing,
            "low_equals_active_count": one_past, "mismatches": 0,
            "bounded_lookup_differences_from_original_lookahead": bounded_lookahead_matches,
            "normalized_transcript_sha256": transcript.hexdigest()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--library", type=Path,
                        default=ROOT / "build/workers/database_dos_differential/database.dll")
    parser.add_argument("--output", type=Path,
                        default=ROOT / "portable/tests/resources/evidence/database-dos-differential.json")
    args = parser.parse_args()
    lib = bind_library(args.library)
    result = {
        "suite": "portable_database_dos_differential_v1",
        "status": "DIAGNOSTIC_PASS_NO_ACCEPTANCE_CLAIM",
        "oracle": {"sha256": exe.load().sha256, "unicorn": behavior.uc.__version__},
        "harness_sha256": behavior.digest(behavior.HARNESS_SOURCE),
        "suite_sha256": sha256(Path(__file__)),
        "native_sources": {
            "database_h": sha256(ROOT / "portable/game/resources/database.h"),
            "database_c": sha256(ROOT / "portable/game/resources/database.c"),
            "test_c": sha256(ROOT / "portable/tests/resources/database_test.c"),
        },
        "assets": {name: {
            "ndx_sha256": sha256(ROOT / "assets" / f"{name}.NDX"),
            "dat_sha256": sha256(ROOT / "assets" / f"{name}.DAT"),
        } for name in ("HCEGANT", "SHARED", "SOUND")},
        "lzss_original_dos": run_lzss(lib),
        "findindex_original_dos": run_findindex(lib),
        "scope": {
            "lzss": "Original f_1B05_0008 and f_1B05_0046 DOS entry points compared decoded bytes to portable DBRecall storage expansion; DBRecall's DOS file/heap setup is excluded.",
            "findindex": "Original FindIndex DOS entry point compared return pointer and binary-search cursor against portable lookup on actual NDX active entries and the actual first reserved lookahead row.",
            "not_acceptance": "This report is a porting diagnostic only. It does not mark any historical function BEHAVIOR_EXACT or EXACT.",
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
