#!/usr/bin/env python3
"""Bounded native ant-list/player helper comparison with frozen DOS originals."""
from __future__ import annotations

import ctypes as ct
import hashlib
import json
from pathlib import Path
import random
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))
import behavior  # noqa: E402

GCC = Path("C:/msys64/mingw64/bin/gcc.exe")
OUTPUT = ROOT / "build/portable/ants-probe.dll"
REPORT = ROOT / "build/portable/ants-dos-diff.json"
EVIDENCE = ROOT / "portable/tests/ants/evidence"
ANT_SOURCE = ROOT / "portable/game/simulation/ants.c"
PROBE_SOURCE = ROOT / "portable/tests/ants/probe.c"


class AntProbeResult(ct.Structure):
    _fields_ = [("count", ct.c_int16), ("success", ct.c_int16)] + [
        (name, ct.c_uint8) for name in ("x", "y", "type", "mode", "state", "life")
    ]


class PlayerProbeResult(ct.Structure):
    _fields_ = [(name, ct.c_int16) for name in
                ("x", "y", "plane", "type", "direction", "health")] + [
        (name, ct.c_uint8) for name in ("life", "tail_life", "warning", "death")
    ]


class AntRebuildResult(ct.Structure):
    _fields_ = [("count", ct.c_int16)] + [
        (name, ct.c_uint8 * 1000) for name in ("x", "y", "type", "mode", "state")
    ]


class AntClearResult(ct.Structure):
    _fields_ = [(name, ct.c_int16) for name in ("count_a", "count_b", "count_r")] + [
        (name, ct.c_uint8) for name in ("marker_a", "marker_b", "marker_r")
    ]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_native():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    command = [str(GCC), "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror", "-shared",
               "-I", str(ROOT / "portable"), str(ANT_SOURCE), str(PROBE_SOURCE),
               "-o", str(OUTPUT)]
    subprocess.run(command, check=True, cwd=ROOT)
    lib = ct.CDLL(str(OUTPUT))
    lib.sim_ant_probe_add.argtypes = [ct.c_int16, ct.c_int16, ct.c_int16, ct.c_int16,
                                      ct.c_uint8, ct.c_uint8, ct.c_uint8,
                                      ct.POINTER(AntProbeResult)]
    lib.sim_ant_probe_add.restype = None
    lib.sim_ant_probe_set_life.argtypes = [ct.c_int16] * 6 + [ct.POINTER(PlayerProbeResult)]
    lib.sim_ant_probe_set_life.restype = None
    lib.sim_ant_probe_set_health.argtypes = [ct.c_int16, ct.c_int16, ct.c_uint8,
                                             ct.c_uint8, ct.POINTER(PlayerProbeResult)]
    lib.sim_ant_probe_set_health.restype = None
    lib.sim_ant_probe_rebuild_a.argtypes = [ct.POINTER(ct.c_uint8), ct.POINTER(AntRebuildResult)]
    lib.sim_ant_probe_rebuild_a.restype = None
    lib.sim_ant_probe_clear.argtypes = [ct.c_int16, ct.c_int16, ct.c_int16, ct.c_int16,
                                        ct.POINTER(AntClearResult)]
    lib.sim_ant_probe_clear.restype = None
    return lib, command


def short(value: int) -> bytes:
    return behavior.words(value)


def long_byte_range(name: str, address: int, size: int = 1) -> behavior.Range:
    return behavior.Range(name, address, size)


def case_for_add(target, list_prefix, life_name, capacity, plane_width, plane_height,
                 count, x, y, typ, mode, state):
    idx = behavior.symbol_address("ListIndex" + list_prefix)
    slot = count if 0 <= count <= capacity else 0
    writes = [(idx, short(count))]
    observe = [long_byte_range("count", idx, 2)]
    write_slot = count < capacity
    # Root globals have distinct spellings for A/B/R lists.
    arrays = {"A": ["AlistX", "AlistY", "AlistT", "AlistM", "AlistS"],
              "B": ["BlistX", "BlistY", "BlistT", "BlistM", "BlistS"],
              "R": ["RlistX", "RlistY", "RlistT", "RlistM", "RlistS"]}[list_prefix]
    sentinels = [0xa1, 0xa2, 0xa3, 0xa4, 0xa5]
    if write_slot:
        for array, sentinel in zip(arrays, sentinels):
            address = behavior.symbol_address(array) + slot
            writes.append((address, bytes([sentinel])))
            observe.append(long_byte_range(array, address))
    life_base = behavior.symbol_address(life_name)
    life_address = life_base + x * plane_height + y
    writes.append((life_address, b"\xa6"))
    observe.append(long_byte_range("life", life_address))
    return behavior.Case(
        f"{target}/count-{count}/xy-{x}-{y}/type-{typ:02x}",
        args=[x, y, typ, mode, state], writes=writes, observe=observe,
        return_kind="void", metadata={"target": target, "count": count,
                                       "slot": slot if write_slot else None,
                                       "coordinates": [x, y], "capacity": capacity,
                                       "plane_width": plane_width,
                                       "plane_height": plane_height})


def run_add_cases(lib):
    rng = random.Random(0x0EC1A175)
    specs = [
        ("AddAntToAList", "A", "LifeA", 1000, 128, 64,
         [(0, 0, 0, 0x81, 3, 0x78), (999, 127, 63, 0x40, 9, 0),
          (1000, 3, 4, 0x60, 6, 0xff)]),
        ("AddAntToBList", "B", "LifeB", 500, 64, 64,
         [(0, 0, 0, 0x60, 9, 0), (499, 63, 63, 0x68, 9, 0),
          (500, 4, 5, 0x61, 6, 0xff)]),
        ("AddAntToRList", "R", "LifeR", 500, 64, 64,
         [(0, 63, 63, 0xe0, 9, 0), (499, 0, 0, 0xe8, 9, 0),
          (500, 4, 5, 0xe1, 6, 0xff)]),
    ]
    observations = []
    mismatches = []
    pairs = {}
    for target, prefix, life_name, cap, width, height, rows in specs:
        pair = behavior.PreparedPair(target, source=ROOT / "src/root/m0EC1.c")
        pairs[target] = pair
        random_rows = []
        for _ in range(1000):
            count = rng.randrange(cap + 1)
            x = rng.randrange(width)
            y = rng.randrange(height)
            typ, mode, state = (rng.randrange(256) for _ in range(3))
            random_rows.append((count, x, y, typ, mode, state))
        for case_kind, row in [("directed", row) for row in rows] + [
                ("seeded-random", row) for row in random_rows]:
            count, x, y, typ, mode, state = row
            case = case_for_add(target, prefix, life_name, cap, width, height,
                                count, x, y, typ, mode, state)
            case.metadata["lane"] = case_kind
            oracle = pair.original_machine.run(case)
            native = AntProbeResult()
            lib.sim_ant_probe_add("ABR".index(prefix), count, x, y, typ, mode, state,
                                  ct.byref(native))
            expected = {key: oracle["ranges"][key] for key in oracle["ranges"]}
            actual = {"count": short(native.count).hex(), "life": bytes([native.life]).hex()}
            if case.metadata["slot"] is not None:
                for field, attr in zip(("AlistX", "AlistY", "AlistT", "AlistM", "AlistS")
                                       if prefix == "A" else
                                       (("BlistX", "BlistY", "BlistT", "BlistM", "BlistS")
                                        if prefix == "B" else
                                        ("RlistX", "RlistY", "RlistT", "RlistM", "RlistS")),
                                       ("x", "y", "type", "mode", "state")):
                    actual[field] = bytes([getattr(native, attr)]).hex()
            else:
                expected.pop("life", None)
                actual.pop("life", None)
            if expected != actual:
                mismatches.append({"case": case.label, "expected": expected, "actual": actual})
            observations.append({"case": case.label, "lane": case_kind,
                                 "expected": expected, "actual": actual})
    return observations, mismatches, pairs


def run_life_cases(lib):
    target = "SetMyLife"
    pair = behavior.PreparedPair(target, source=ROOT / "src/root/m10F7.c")
    rng = random.Random(0x1A1FE)
    directed = [(1, 20, 20, 0x40, 2, 0xff), (1, 20, 20, 0x60, 2, 0xff),
                (1, 21, 20, 0x40, 7, 0), (1, 127, 63, 0x40, 0, 0xff),
                (1, 0, 0, 0x60, 6, 0xfe), (1, 0, 63, 0x60, 7, 0xff),
                (1, 127, 0, 0x60, 4, 1), (1, 127, 63, 0x60, 2, 0),
                (1, 1, 1, 0x40, 4, 0), (1, 126, 62, 0x60, 0, 0xff)]
    random_rows = [(1, rng.randrange(128), rng.randrange(64),
                    rng.choice((0x10, 0x40, 0x60, rng.randrange(256))),
                    rng.randrange(8), rng.choice((0, 1, 0xfe, 0xff, rng.randrange(256))))
                   for _ in range(1000)]
    rows = [("directed", row) for row in directed] + [("seeded-random", row) for row in random_rows]
    observations, mismatches = [], []
    globals_by_field = [("MeLocX", "x"), ("MeLocY", "y"), ("MePlane", "plane"),
                        ("fd_50F6_04C2", "type"), ("fd_50F6_0496", "direction")]
    for lane, (plane, x, y, typ, direction, value) in rows:
        writes = [(behavior.symbol_address("MeLocX"), short(-7)),
                  (behavior.symbol_address("MeLocY"), short(-8)),
                  (behavior.symbol_address("MePlane"), short(3)),
                  (behavior.symbol_address("fd_50F6_04C2"), short(0x20)),
                  (behavior.symbol_address("fd_50F6_0496"), short(5))]
        observe = [long_byte_range(field, behavior.symbol_address(field), 2)
                   for field, _ in globals_by_field]
        life_address = behavior.symbol_address("LifeA") + x * 64 + y
        writes.append((life_address, b"\x6e"))
        observe.append(long_byte_range("life", life_address))
        dx8 = (0, 1, 1, 1, 0, -1, -1, -1)
        dy8 = (-1, -1, 0, 1, 1, 1, 0, -1)
        tail_x = tail_y = None
        if typ == 0x60:
            d = direction ^ 4
            tail_x, tail_y = x + dx8[d], y + dy8[d]
            if not (0 <= tail_x < 128 and 0 <= tail_y < 64):
                tail_x = tail_y = None
        tail_address = None
        if tail_x is not None:
            tail_address = behavior.symbol_address("LifeA") + tail_x * 64 + tail_y
            writes.append((tail_address, b"\x7d"))
            observe.append(long_byte_range("tail_life", tail_address))
        case = behavior.Case(f"SetMyLife/{plane}/{x}/{y}/{typ:02x}/{value:02x}",
                             args=[plane, x, y, typ, direction, value], writes=writes,
                             observe=observe, return_kind="void")
        oracle = pair.original_machine.run(case)
        native = PlayerProbeResult()
        lib.sim_ant_probe_set_life(plane, x, y, typ, direction, value, ct.byref(native))
        expected = dict(oracle["ranges"])
        actual = {"MeLocX": short(native.x).hex(), "MeLocY": short(native.y).hex(),
                  "MePlane": short(native.plane).hex(), "fd_50F6_04C2": short(native.type).hex(),
                  "fd_50F6_0496": short(native.direction).hex(), "life": bytes([native.life]).hex()}
        if tail_address is not None:
            actual["tail_life"] = bytes([native.tail_life]).hex()
        if expected != actual:
            mismatches.append({"case": case.label, "expected": expected, "actual": actual})
        observations.append({"case": case.label, "lane": lane,
                             "expected": expected, "actual": actual})
    return observations, mismatches, pair


def run_health_cases(lib):
    target = "SetMyHealth"
    pair = behavior.PreparedPair(target, source=ROOT / "src/root/m10F7.c")
    rng = random.Random(0x5E7A17)
    directed = [(-32768, 50, 0, 1), (-1, 50, 0, 1), (0, 50, 0, 1),
                (7, 7, 0, 1), (8, 7, 0, 1), (15, 15, 0, 1), (16, 15, 0, 1),
                (31, 31, 0, 1), (32, 31, 0, 1), (100, 50, 0, 1),
                (101, 100, 0, 1), (32767, 100, 0, 1), (0, 50, 1, 1),
                (8, 8, 1, 1), (16, 15, 0, 0)]
    random_rows = [(rng.choice((-32768, -1, 0, 7, 8, 15, 16, 31, 32, 100, 101,
                                32767, rng.randrange(-32768, 32768))),
                    rng.choice((-32768, 0, 7, 8, 15, 16, 31, 32, 50, 100, 32767)),
                    rng.randrange(2), rng.randrange(2)) for _ in range(1000)]
    rows = [("directed", row) for row in directed] + [("seeded-random", row) for row in random_rows]
    observations, mismatches = [], []
    health_global = behavior.symbol_address("MeHealth")
    warning_global = behavior.symbol_address("fd_50F6_1044")
    death_global = behavior.symbol_address("fd_50F6_1006")
    threshold_global = behavior.symbol_address("fd_50F6_0FBA")
    force_global = behavior.symbol_address("fd_3D57_0C16")
    for lane, (health, threshold, force, death) in rows:
        writes = [(health_global, short(-1)), (warning_global, short(1)),
                  (death_global, short(death)), (threshold_global, short(threshold)),
                  (force_global, short(force))]
        observe = [long_byte_range(name, address, 2) for name, address in
                   (("MeHealth", health_global), ("fd_50F6_1044", warning_global),
                    ("fd_50F6_1006", death_global))]
        case = behavior.Case(f"SetMyHealth/{health}/{threshold}/{force}/{death}",
                             args=[health], writes=writes, observe=observe,
                             return_kind="void")
        oracle = pair.original_machine.run(case)
        native = PlayerProbeResult()
        lib.sim_ant_probe_set_health(health, threshold, force, death, ct.byref(native))
        expected = dict(oracle["ranges"])
        actual = {"MeHealth": short(native.health).hex(),
                  "fd_50F6_1044": short(native.warning).hex(),
                  "fd_50F6_1006": short(native.death).hex()}
        if expected != actual:
            mismatches.append({"case": case.label, "expected": expected, "actual": actual})
        observations.append({"case": case.label, "lane": lane,
                             "expected": expected, "actual": actual})
    return observations, mismatches, pair


def run_rebuild_cases(lib):
    target = "BuildAntListA"
    pair = behavior.PreparedPair(target, source=ROOT / "src/root/m0EC1.c")
    rng = random.Random(0xB017D)
    grids = []
    grids.append(("empty", bytearray(128 * 64)))
    yellow = bytearray(128 * 64)
    for at, value in ((0, 0xff), (63, 0xfe), (64 * 7 + 63, 0xff), (8191, 0xfe)):
        yellow[at] = value
    grids.append(("yellow-only", yellow))
    sparse = bytearray(128 * 64)
    for _ in range(32):
        sparse[rng.randrange(128 * 64)] = rng.choice((0x10, 0x40, 0x81, 0xfe, 0xff))
    grids.append(("sparse-mixed", sparse))
    exact = bytearray(128 * 64)
    exact[:997] = bytes([0x40]) * 997
    grids.append(("997-active", exact))
    one_extra = bytearray(128 * 64)
    one_extra[:998] = bytes([0x81]) * 998
    grids.append(("998-active", one_extra))
    dense = bytearray([0x60]) * (128 * 64)
    grids.append(("dense-over-cap", dense))
    randomized = bytearray(128 * 64)
    for _ in range(750):
        randomized[rng.randrange(128 * 64)] = rng.choice((0, 0x10, 0x40, 0x81, 0xfe, 0xff))
    grids.append(("seeded-random", randomized))

    observations, mismatches = [], []
    array_names = ("AlistX", "AlistY", "AlistT", "AlistM", "AlistS")
    probe_names = ("x", "y", "type", "mode", "state")
    for label, grid in grids:
        count_address = behavior.symbol_address("ListIndexA")
        life_address = behavior.symbol_address("LifeA")
        # Expected active entries are derived from the input only to size the
        # observation ranges. Values themselves come from the frozen DOS run.
        total = sum(value != 0 and value not in (0xfe, 0xff) for value in grid)
        count = min(total, 997)
        observed_slots = min(1000, count + (1 if count == 997 else 0))
        observe = [long_byte_range("count", count_address, 2)]
        observe.extend(long_byte_range(name, behavior.symbol_address(name), observed_slots)
                       for name in array_names if observed_slots)
        case = behavior.Case(f"BuildAntListA/{label}", writes=[
            (count_address, short(-17)), (life_address, bytes(grid))],
            observe=observe, return_kind="void",
            metadata={"non_yellow_cells": total, "expected_count": count,
                      "observed_slots": observed_slots})
        oracle = pair.original_machine.run(case)
        native = AntRebuildResult()
        native_grid = (ct.c_uint8 * len(grid)).from_buffer_copy(grid)
        lib.sim_ant_probe_rebuild_a(native_grid, ct.byref(native))
        expected = dict(oracle["ranges"])
        actual = {"count": short(native.count).hex()}
        for array, field in zip(array_names, probe_names):
            if observed_slots:
                actual[array] = bytes(getattr(native, field)[:observed_slots]).hex()
        if expected != actual:
            mismatches.append({"case": case.label, "expected": expected, "actual": actual})
        observations.append({"case": case.label, "expected": expected, "actual": actual})
    return observations, mismatches, pair


def run_clear_cases(lib):
    observations, mismatches, pairs = [], [], {}
    for which, target in ((0, "ClearListB"), (1, "ClearListR")):
        pair = behavior.PreparedPair(target, source=ROOT / "src/root/m0EC1.c")
        pairs[target] = pair
        count_addresses = [behavior.symbol_address(name) for name in
                           ("ListIndexA", "ListIndexB", "ListIndexR")]
        type_addresses = [behavior.symbol_address(name) for name in
                          ("AlistT", "BlistT", "RlistT")]
        counts = (17, 33, 49)
        markers = (0xa1, 0xb2, 0xc3)
        writes = [(address, short(value)) for address, value in zip(count_addresses, counts)]
        writes.extend((address, bytes([value])) for address, value in zip(type_addresses, markers))
        observe = [long_byte_range(name, address, 2) for name, address in
                   zip(("count_a", "count_b", "count_r"), count_addresses)]
        observe.extend(long_byte_range(name, address) for name, address in
                       zip(("marker_a", "marker_b", "marker_r"), type_addresses))
        case = behavior.Case(f"{target}/count-only", writes=writes,
                             observe=observe, return_kind="void")
        oracle = pair.original_machine.run(case)
        native = AntClearResult()
        lib.sim_ant_probe_clear(which, *counts, ct.byref(native))
        actual = {name: short(getattr(native, name)).hex() for name in
                  ("count_a", "count_b", "count_r")}
        actual.update({name: bytes([getattr(native, name)]).hex() for name in
                       ("marker_a", "marker_b", "marker_r")})
        expected = dict(oracle["ranges"])
        if expected != actual:
            mismatches.append({"case": case.label, "expected": expected, "actual": actual})
        observations.append({"case": case.label, "expected": expected, "actual": actual})
    return observations, mismatches, pairs


def main():
    lib, command = build_native()
    add_observations, add_mismatches, add_pairs = run_add_cases(lib)
    life_observations, life_mismatches, life_pair = run_life_cases(lib)
    health_observations, health_mismatches, health_pair = run_health_cases(lib)
    rebuild_observations, rebuild_mismatches, rebuild_pair = run_rebuild_cases(lib)
    clear_observations, clear_mismatches, clear_pairs = run_clear_cases(lib)
    mismatches = (add_mismatches + life_mismatches + health_mismatches +
                  rebuild_mismatches + clear_mismatches)
    report = {
        "schema": "portable-ant-dos-diff-v1",
        "oracle_sha256": behavior.exe.load().sha256,
        "original_execution_only": True,
        "native_probe_sha256": digest(OUTPUT),
        "sources": {str(p.relative_to(ROOT)): digest(p) for p in
                    (ANT_SOURCE, ROOT / "portable/game/simulation/ants.h",
                     ROOT / "portable/game/state/world.h",
                     ROOT / "portable/game/simulation/movement.h",
                     PROBE_SOURCE, Path(__file__),
                     ROOT / "src/root/m0EC1.c", ROOT / "src/root/m10F7.c")},
        "prepared_pairs": {name: pair.identity for name, pair in add_pairs.items()},
        "life_pair": life_pair.identity,
        "health_pair": health_pair.identity,
        "rebuild_pair": rebuild_pair.identity,
        "clear_pairs": {name: pair.identity for name, pair in clear_pairs.items()},
        "native_build_command": command,
        "native_compiler": subprocess.check_output([str(GCC), "--version"],
                                                    text=True).splitlines()[0],
        "targets": {
            "AddAntToAList/AddAntToBList/AddAntToRList": add_observations,
            "SetMyLife": life_observations,
            "SetMyHealth": health_observations,
            "BuildAntListA": rebuild_observations,
            "ClearListB/ClearListR": clear_observations,
        },
        "case_count": len(add_observations) + len(life_observations) +
                      len(health_observations) + len(rebuild_observations) + len(clear_observations),
        "random_seed": {"lists": "0x0EC1A175", "life": "0x1A1FE", "health": "0x5E7A17"},
        "mismatches": mismatches,
        "coverage": "3 direct list-write targets at empty/last-slot/full counts plus 1,000 seeded valid calls per target; BuildAntListA empty, yellow-only, sparse, 997/998 and dense-cap cases; SetMyLife queen-tail boundary/occupied-state cases plus 1,000 seeded valid states; SetMyHealth signed clamps/threshold/forced-full boundaries plus 1,000 seeded states.",
        "limits": "Does not claim world-generation equivalence; only these native list/player helpers and selected original effects are compared.",
        "status": "PASS" if not mismatches else "FAIL",
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    (EVIDENCE / "ants-dos-diff-final.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(REPORT), "case_count": report["case_count"],
                      "mismatches": len(mismatches), "status": report["status"]}, indent=2))
    if mismatches:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
