#!/usr/bin/env python3
"""Compare the native Spider scan with the original DOS entry point."""
from __future__ import annotations

import argparse
import ctypes as ct
import hashlib
import importlib.util
import json
import struct
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ARCHIVED_SUITE = ROOT / "tools/behavior_suites/archive/spider_nest-20261002-current-runner-ledger-final.py"
ARCHIVED_SUITE_SHA256 = "41fa2c46acdc8c74d033d07d4d2afcf13abd77cd9cdee80e5060a61649aa8f67"
LIBRARY = ROOT / "build/portable/spider-test.dll"
REPORT = ROOT / "build/portable/spider-dos-diff.json"
GCC = Path("C:/msys64/mingw64/bin/gcc.exe")
sys.path.insert(0, str(ROOT / "tools"))
import behavior  # noqa: E402


def load_suite():
    raw = ARCHIVED_SUITE.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != ARCHIVED_SUITE_SHA256:
        raise RuntimeError(f"archived scenario generator hash changed: {digest}")
    spec = importlib.util.spec_from_file_location("archived_spider_suite", ARCHIVED_SUITE)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module, digest


class SpiderState(ct.Structure):
    _fields_ = [(n, ct.c_int16) for n in (
        "direction", "x16", "y16", "burp_count", "eat_count", "corpse_base",
        "cycle", "cycle2", "revenge", "target_mode", "mode", "target",
        "target_life", "user_x", "user_y")]


def build_library():
    LIBRARY.parent.mkdir(parents=True, exist_ok=True)
    command = [str(GCC), "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror", "-shared",
               "-I", str(ROOT / "portable/game/simulation"),
               "-I", str(ROOT / "portable/game/state"),
               str(ROOT / "portable/tests/spider/native_bridge.c"),
               str(ROOT / "portable/game/simulation/spider.c"),
               str(ROOT / "portable/game/simulation/rng.c"), "-o", str(LIBRARY)]
    subprocess.run(command, check=True, cwd=ROOT)
    return hashlib.sha256(LIBRARY.read_bytes()).hexdigest(), command


def c_bytes(data: bytes):
    return (ct.c_uint8 * len(data)).from_buffer_copy(data)


def table_values():
    index_path = ROOT / "assets/SHARED.NDX"
    data_path = ROOT / "assets/SHARED.DAT"
    index = index_path.read_bytes()
    data = data_path.read_bytes()
    count = struct.unpack_from("<H", index, 0)[0]
    entry_at = len(index) - count * 8
    matches = []
    for i in range(count):
        offset, object_id, kind, flags = struct.unpack_from("<IHBB", index, entry_at + i * 8)
        if object_id == 0x3e8 and kind == 9:
            header = struct.unpack_from("<HHHHH", data, offset + 14)
            payload = data[offset + 24:offset + 24 + header[3]]
            matches.append((offset, flags, header, payload))
    if len(matches) != 1:
        raise RuntimeError("expected one shared sine resource 0x3e8/type 9")
    offset, flags, header, payload = matches[0]
    if len(payload) != 128 or flags != 0:
        raise RuntimeError("unexpected sine resource record format")
    # InitStuff calls f_0244_0022, which swaps each resource word before
    # assigning its handle data pointer to fd_50F6_0B22.
    values = [int.from_bytes(payload[i:i + 2], "big", signed=True)
              for i in range(0, len(payload), 2)]
    return values, {
        "database_index": str(index_path.relative_to(ROOT)),
        "database_index_sha256": hashlib.sha256(index).hexdigest(),
        "database_data": str(data_path.relative_to(ROOT)),
        "database_data_sha256": hashlib.sha256(data).hexdigest(),
        "object_id": 0x3e8, "kind": 9, "flags": flags,
        "record_offset": offset, "record_header": list(header),
        "payload_size": len(payload), "word_transform": "f_0244_0022 byte-swaps each 16-bit word",
    }


def set_range(dst, base, address, data):
    offset = address - base
    if offset >= 0 and offset + len(data) <= len(dst):
        dst[offset:offset + len(data)] = data
        return True
    return False


def input_from_case(case, sine_table):
    life = bytearray(128 * 64)
    map_a = bytearray(128 * 64)
    ant_x = bytearray(1000)
    ant_y = bytearray(1000)
    ant_type = bytearray(1000)
    corpse_x = bytearray(100)
    corpse_y = bytearray(100)
    values = {"direction": 0, "x16": 0x400, "y16": 0x200,
              "count": 0, "seed": 0xACE1, "terrain": 0, "base": 0, "ring": 0}
    ranges = [("life", behavior.symbol_address("LifeA"), life),
              ("map", behavior.symbol_address("MapA"), map_a),
              ("ant_x", behavior.symbol_address("AlistX"), ant_x),
              ("ant_y", behavior.symbol_address("AlistY"), ant_y),
              ("ant_type", behavior.symbol_address("AlistT"), ant_type),
              ("corpse_x", behavior.symbol_address("fd_50F6_037C"), corpse_x),
              ("corpse_y", behavior.symbol_address("fd_50F6_0404"), corpse_y)]
    words = {behavior.symbol_address("fd_50F6_1004"): "direction",
             behavior.symbol_address("fd_50F6_0F12"): "x16",
             behavior.symbol_address("fd_50F6_0F34"): "y16",
             behavior.symbol_address("ListIndexA"): "count",
             behavior.symbol_address("g_8BA2"): "seed",
             behavior.symbol_address("SCorpseBase"): "base",
             behavior.symbol_address("fd_50F6_0476"): "ring",
             behavior.symbol_address("TERRAINset"): "terrain"}
    for address, data in case.writes:
        for name, base, dst in ranges:
            if set_range(dst, base, address, data):
                break
        else:
            name = words.get(address)
            if name is not None and len(data) >= 2:
                values[name] = int.from_bytes(data[:2], "little", signed=True)
    return values, life, map_a, ant_x, ant_y, ant_type, corpse_x, corpse_y


def attach_resource(case, sine_table):
    # A controlled far table in otherwise unused conventional-memory space lets
    # the original fracSIN/fracCOS helpers execute normally with known inputs.
    linear = 0xD0100
    pointer = behavior.symbol_address("fd_50F6_0B22")
    case.writes.extend([
        (pointer, (0x0100).to_bytes(2, "little") + (0xD000).to_bytes(2, "little")),
        (linear, b"".join((v & 0xffff).to_bytes(2, "little") for v in sine_table)),
    ])


def oracle_bytes(oracle, name):
    value = oracle["ranges"][name]
    return bytes.fromhex(value)


def signed16(value):
    value &= 0xffff
    return value - 65536 if value >= 32768 else value


def compare_one(machine, lib, case, sine_table):
    attach_resource(case, sine_table)
    v, life, map_a, ax, ay, at, corpse_x, corpse_y = input_from_case(case, sine_table)
    out_life = (ct.c_uint8 * len(life))()
    out_map = (ct.c_uint8 * len(map_a))()
    out_at = (ct.c_uint8 * len(at))()
    out_cx = (ct.c_uint8 * len(corpse_x))()
    out_cy = (ct.c_uint8 * len(corpse_y))()
    out_base, out_ring, out_seed = ct.c_int16(), ct.c_int16(), ct.c_uint16()
    out_laser = (ct.c_int16 * 8)()
    native_ret = int(lib.spider_test_scan(
        v["direction"], v["x16"], v["y16"], v["seed"] & 0xffff, v["count"],
        v["terrain"] & 0xff, c_bytes(life), c_bytes(map_a), c_bytes(ax), c_bytes(ay),
        c_bytes(at), c_bytes(corpse_x), c_bytes(corpse_y), v["base"], v["ring"],
        out_life, out_map, out_at, out_cx, out_cy,
        ct.byref(out_base), ct.byref(out_ring), ct.byref(out_seed), out_laser))
    if not any(r.name == "SCorpseBase" for r in case.observe):
        case.observe = tuple(case.observe) + (behavior.Range(
            "SCorpseBase", behavior.symbol_address("SCorpseBase"), 2),)
    oracle = machine.run(case)
    expected_laser = [tuple(signed16(value) for value in item["args"])
                      for item in oracle["trace"]
                      if item["name"] == "DoLaserFire"]
    actual_laser = [] if out_laser[4] == 0 else [(out_laser[0], out_laser[1],
                                                  out_laser[2], out_laser[3])]
    comparisons = {
        "return": (native_ret, oracle["return"]),
        "lfsr": (int(out_seed.value), int.from_bytes(oracle_bytes(oracle, "g_8BA2"), "little")),
        "life": (bytes(out_life), oracle_bytes(oracle, "LifeA")),
        "map": (bytes(out_map), oracle_bytes(oracle, "MapA")),
        "ant_type": (bytes(out_at), oracle_bytes(oracle, "AlistT")),
        "corpse_x": (bytes(out_cx), oracle_bytes(oracle, "fd_50F6_037C")),
        "corpse_y": (bytes(out_cy), oracle_bytes(oracle, "fd_50F6_0404")),
        "corpse_base": (int(out_base.value), int.from_bytes(oracle_bytes(oracle, "SCorpseBase"), "little", signed=True)),
        "corpse_index": (int(out_ring.value), int.from_bytes(oracle_bytes(oracle, "fd_50F6_0476"), "little", signed=True)),
        "laser": (actual_laser, expected_laser),
    }
    mismatch = next((name for name, (actual, expected) in comparisons.items()
                     if actual != expected), None)
    if mismatch:
        return {"case": case.label, "mismatch": mismatch,
                "native": str(comparisons[mismatch][0])[:256],
                "oracle": str(comparisons[mismatch][1])[:256]}
    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--random-count", type=int, default=10000)
    parser.add_argument("--seed", type=lambda x: int(x, 0), default=0x5A17E2)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--report", type=Path, default=REPORT)
    args = parser.parse_args()
    suite, suite_hash = load_suite()
    library_hash, command = build_library()
    lib = ct.CDLL(str(LIBRARY))
    lib.spider_test_scan.argtypes = [ct.c_int16, ct.c_int16, ct.c_int16, ct.c_uint16,
        ct.c_int16, ct.c_uint8] + [ct.POINTER(ct.c_uint8)] * 7 + [ct.c_int16, ct.c_int16,
        ct.POINTER(ct.c_uint8), ct.POINTER(ct.c_uint8), ct.POINTER(ct.c_uint8),
        ct.POINTER(ct.c_uint8), ct.POINTER(ct.c_uint8),
        ct.POINTER(ct.c_int16), ct.POINTER(ct.c_int16), ct.POINTER(ct.c_uint16), ct.POINTER(ct.c_int16)]
    lib.spider_test_scan.restype = ct.c_int16
    pair = behavior.PreparedPair("SpiderScan")
    machine = pair.original_machine
    table, table_source = table_values()
    lib.sim_spider_sine_table.argtypes = []
    lib.sim_spider_sine_table.restype = ct.POINTER(ct.c_int16)
    native_table = [int(lib.sim_spider_sine_table()[i]) for i in range(64)]
    if native_table != table:
        raise RuntimeError("native sine table differs from the decoded game resource")
    cases = list(suite.make_cases("SpiderScan", directed=True,
                random_seed=args.seed, random_count=args.random_count,
                original_helpers=("SRand1", "SRand4", "fracSIN", "fracCOS",
                                  "FindAntIndex", "DeadAntHere")))
    if args.limit is not None:
        cases = cases[:args.limit]
    mismatches = []
    for i, case in enumerate(cases):
        failure = compare_one(machine, lib, case, table)
        if failure:
            mismatches.append(failure)
            break
        if (i + 1) % 25 == 0:
            print(f"original-DOS SpiderScan cases={i + 1}", flush=True)
    report = {
        "schema": "native-dos-spider-differential-v1",
        "oracle_sha256": behavior.exe.load().sha256,
        "archived_suite": str(ARCHIVED_SUITE.relative_to(ROOT)),
        "suite_sha256": suite_hash,
        "runner_sha256": hashlib.sha256((ROOT / "tools/behavior.py").read_bytes()).hexdigest(),
        "native_source_sha256": hashlib.sha256((ROOT / "portable/game/simulation/spider.c").read_bytes()).hexdigest(),
        "native_header_sha256": hashlib.sha256((ROOT / "portable/game/simulation/spider.h").read_bytes()).hexdigest(),
        "native_bridge_sha256": hashlib.sha256((ROOT / "portable/tests/spider/native_bridge.c").read_bytes()).hexdigest(),
        "native_library_sha256": library_hash,
        "compile_command": command,
        "seed": args.seed,
        "sin_table_q15": table,
        "sin_table_source": table_source,
        "cases": len(cases),
        "passed": len(cases) - len(mismatches),
        "mismatches": mismatches,
        "expected_source": "original SpiderScan in retained DOS image with actual original helper entries",
        "modeled_resource": "known 64-entry q15 table installed through the original far-pointer global",
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"cases": report["cases"], "passed": report["passed"],
                      "mismatches": mismatches[:1], "report": str(args.report)}, indent=2))
    if mismatches:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
