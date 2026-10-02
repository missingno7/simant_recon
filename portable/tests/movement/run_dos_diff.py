#!/usr/bin/env python3
"""Run frozen-DOS GetMyRandDirs cases against the native movement library.

The archived scenario generator is hash-pinned. Each expected outcome is
produced by a fresh invocation of the original DOS function in the retained
Unicorn runner; no historical candidate lane is used as the expected result.
"""
from __future__ import annotations

import argparse
import ctypes as ct
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[3]
TOOLS = ROOT / "tools"
ARCHIVED_SUITE = ROOT / "tools/behavior_suites/archive/randdirs-20261002-current-runner-ledger-final.py"
ARCHIVED_SUITE_SHA256 = "f7aad88da70befc902bcc4b8f48670f43df38e90f81e45a59ef4c584090dd360"
LIBRARY = ROOT / "build/portable/movement.dll"
REPORT = ROOT / "build/portable/movement-dos-diff.json"
GCC = Path("C:/msys64/mingw64/bin/gcc.exe")

sys.path.insert(0, str(TOOLS))
import behavior  # noqa: E402
import functions  # noqa: E402


def load_suite():
    raw = ARCHIVED_SUITE.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != ARCHIVED_SUITE_SHA256:
        raise RuntimeError(f"archived scenario generator hash changed: {digest}")
    spec = importlib.util.spec_from_file_location("archived_randdirs", ARCHIVED_SUITE)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module, digest


class GridPos(ct.Structure):
    _fields_ = [("x", ct.c_int16), ("y", ct.c_int16)]


class RandDirBias(ct.Structure):
    _fields_ = [("rot", ct.c_int16), ("direction", ct.c_int16)]


class MoveContext(ct.Structure):
    _fields_ = [("mode", ct.c_int16), ("from_plane", ct.c_int16),
                ("from", GridPos), ("previous", GridPos)]


class WorldTiles(ct.Structure):
    _fields_ = [("surface", (ct.c_uint8 * 64) * 128),
                ("nest_b", (ct.c_uint8 * 64) * 64),
                ("nest_r", (ct.c_uint8 * 64) * 64),
                ("terrain_set", ct.c_int16)]


class TileQuery(ct.Structure):
    _fields_ = [(name, ct.c_int16) for name in
                ("plane", "x", "y", "from_plane", "from_x", "from_y", "digging", "result")]


class MoveTrace(ct.Structure):
    _fields_ = [("tile_query_count", ct.c_uint16), ("tile_queries", TileQuery * 8)]


def build_library():
    LIBRARY.parent.mkdir(parents=True, exist_ok=True)
    command = [str(GCC), "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror", "-shared",
               "-I", str(ROOT / "portable/game/simulation"),
               str(ROOT / "portable/game/simulation/movement.c"), "-o", str(LIBRARY)]
    subprocess.run(command, check=True, cwd=ROOT)
    return hashlib.sha256(LIBRARY.read_bytes()).hexdigest(), command


def signed16(value: int) -> int:
    value &= 0xffff
    return value - 65536 if value >= 32768 else value


def prepare_native_case(case, suite, lib):
    scenario = suite._case_scenario(case)
    world = native_world_from_case(case)
    ctx = MoveContext(scenario.mode, scenario.from_plane,
                      GridPos(scenario.from_x, scenario.from_y),
                      GridPos(scenario.previous_x, scenario.previous_y))
    bias = RandDirBias(scenario.rot, scenario.direction)
    trace = MoveTrace()
    result = lib.sim_get_my_rand_dirs(ct.byref(world), ct.byref(ctx), scenario.plane,
                                      GridPos(scenario.x, scenario.y),
                                      GridPos(scenario.a, scenario.b), ct.byref(bias),
                                      ct.byref(trace))
    native_queries = []
    for query in trace.tile_queries[:trace.tile_query_count]:
        native_queries.append((query.plane, query.x, query.y, query.from_plane,
                               query.from_x, query.from_y, query.digging))
    return scenario, int(result), int(bias.rot), int(bias.direction), native_queries


def native_world_from_case(case):
    world = WorldTiles()
    map_bases = {
        "surface": behavior.symbol_address("MapA"),
        "nest_b": behavior.symbol_address("MapB"),
        "nest_r": behavior.symbol_address("MapR"),
    }
    arrays = {
        "surface": (world.surface, 128 * 64),
        "nest_b": (world.nest_b, 64 * 64),
        "nest_r": (world.nest_r, 64 * 64),
    }
    terrain_address = behavior.symbol_address("TERRAINset")
    for address, data in case.writes:
        if address == terrain_address:
            world.terrain_set = int.from_bytes(data[:2], "little", signed=True)
            continue
        for name, base in map_bases.items():
            size = arrays[name][1]
            if base <= address < base + size:
                offset = address - base
                x, y = divmod(offset, 64)
                arrays[name][0][x][y] = data[0]
                break

    return world


def configure_library(lib):
    lib.sim_get_my_rand_dirs.argtypes = [ct.POINTER(WorldTiles), ct.POINTER(MoveContext),
                                         ct.c_int16, GridPos, GridPos,
                                         ct.POINTER(RandDirBias), ct.POINTER(MoveTrace)]
    lib.sim_get_my_rand_dirs.restype = ct.c_int16
    lib.sim_tile_can_be_moved_on.argtypes = [ct.POINTER(WorldTiles), ct.c_int16,
                                              ct.c_int16, ct.c_int16, ct.c_int16,
                                              ct.c_int16, ct.c_int16, ct.c_int16]
    lib.sim_tile_can_be_moved_on.restype = ct.c_int16


def run_tile_helper(machine, lib, suite, random_count, seed, limit):
    cases = suite.direct_tile_cases()
    if limit is not None:
        cases = (case for i, case in enumerate(cases) if i < limit)
    count = 0
    mismatch = None
    for case in cases:
        oracle = machine.run(case)
        world = native_world_from_case(case)
        plane, x, y, from_plane, from_x, from_y, digging = case.args
        native = int(lib.sim_tile_can_be_moved_on(ct.byref(world), plane, x, y,
                                                   from_plane, from_x, from_y, digging))
        count += 1
        if native != oracle["return"]:
            mismatch = {"case": case.label, "args": list(case.args),
                        "oracle": oracle["return"], "native": native,
                        "metadata": case.metadata}
            break
        if count % 1000 == 0:
            print(f"native-vs-DOS TileCanBeMovedOn cases={count}", flush=True)
    if mismatch is None and random_count:
        random_cases = suite.randomized_direct_tile_cases(count=random_count, seed=seed)
        for case in random_cases:
            oracle = machine.run(case)
            world = native_world_from_case(case)
            plane, x, y, from_plane, from_x, from_y, digging = case.args
            native = int(lib.sim_tile_can_be_moved_on(ct.byref(world), plane, x, y,
                                                       from_plane, from_x, from_y, digging))
            count += 1
            if native != oracle["return"]:
                mismatch = {"case": case.label, "args": list(case.args),
                            "oracle": oracle["return"], "native": native,
                            "metadata": case.metadata}
                break
            if count % 1000 == 0:
                print(f"native-vs-DOS TileCanBeMovedOn cases={count}", flush=True)
    return count, mismatch


def compare_one(machine, lib, suite, case):
    oracle = machine.run(case)
    scenario, native_return, native_rot, native_dir, native_queries = prepare_native_case(case, suite, lib)
    oracle_rot = int.from_bytes(bytes.fromhex(oracle["ranges"]["fd_50F6_0EFA"]), "little", signed=True)
    oracle_dir = int.from_bytes(bytes.fromhex(oracle["ranges"]["fd_50F6_0EF8"]), "little", signed=True)
    oracle_queries = []
    for item in oracle["trace"]:
        if item["name"] == "TileCanBeMovedOn":
            oracle_queries.append(tuple(signed16(v) for v in item["args"]))
    actual = {"return": native_return, "rot": native_rot, "dir": native_dir,
              "tile_queries": native_queries}
    expected = {"return": oracle["return"], "rot": oracle_rot, "dir": oracle_dir,
                "tile_queries": oracle_queries}
    return scenario, expected, actual, expected == actual


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--random-count", type=int, default=0)
    parser.add_argument("--random-only", action="store_true")
    parser.add_argument("--tile-helper", action="store_true",
                        help="test native TileCanBeMovedOn against original helper fixtures")
    parser.add_argument("--limit", type=int, default=None,
                        help="stop after this many generated cases; useful for smoke runs")
    parser.add_argument("--seed", type=lambda s: int(s, 0), default=0x1686)
    parser.add_argument("--report", type=Path, default=REPORT)
    args = parser.parse_args()

    suite, suite_hash = load_suite()
    lib_hash, command = build_library()
    lib = ct.CDLL(str(LIBRARY))
    configure_library(lib)

    # PreparedPair supplies the retained original-machine setup and address map,
    # but only its ORIGINAL machine is run. The compiled candidate is never a
    # source of expected outcomes.
    pair = behavior.PreparedPair("o25_3BA4_1686")
    machine = pair.original_machine
    if args.tile_helper:
        tile_pair = SimpleNamespace(function=functions.get("TileCanBeMovedOn"),
                                    vectors={behavior.exe.MANAGER_SEG * 16 + v.offset: v
                                             for v in behavior.exe.load().vectors})
        tile_machine = behavior.Machine(tile_pair)
        count, mismatch = run_tile_helper(tile_machine, lib, suite, args.random_count,
                                          args.seed, args.limit)
        report = {
            "schema": "native-dos-movement-differential-v1",
            "oracle_sha256": behavior.exe.load().sha256,
            "historical_manifest_sha256": hashlib.sha256((ROOT / "layout/manifest.json").read_bytes()).hexdigest(),
            "archived_suite": str(ARCHIVED_SUITE.relative_to(ROOT)),
            "suite_sha256": suite_hash,
            "runner_sha256": hashlib.sha256((TOOLS / "behavior.py").read_bytes()).hexdigest(),
            "native_sources": {
                "header_sha256": hashlib.sha256((ROOT / "portable/game/simulation/movement.h").read_bytes()).hexdigest(),
                "source_sha256": hashlib.sha256((ROOT / "portable/game/simulation/movement.c").read_bytes()).hexdigest(),
                "library_sha256": lib_hash,
                "build_command": command,
            },
            "lane": "original DOS TileCanBeMovedOn invocation vs native call",
            "executed": count,
            "randomized_tile_cases_requested": args.random_count,
            "random_seed": args.seed,
            "mismatches": int(mismatch is not None),
            "first_mismatch": mismatch,
            "status": "MISMATCH" if mismatch else "PASS",
        }
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"status": report["status"], "executed": count,
                          "report": str(args.report), "mismatch": mismatch}, indent=2))
        return 1 if mismatch else 0
    cases = suite.iter_cases(directed=not args.random_only, random_seed=args.seed,
                             random_count=args.random_count, limit_total=args.limit,
                             actual_tile=True)
    count = 0
    mismatch = None
    for case in cases:
        scenario, expected, actual, equal = compare_one(machine, lib, suite, case)
        count += 1
        if not equal:
            mismatch = {"case_id": scenario.case_id, "input": scenario.as_dict(),
                        "expected": expected, "actual": actual}
            break
        if count % 1000 == 0:
            print(f"native-vs-DOS cases={count}", flush=True)

    report = {
        "schema": "native-dos-movement-differential-v1",
        "oracle_sha256": behavior.exe.load().sha256,
        "historical_manifest_sha256": hashlib.sha256((ROOT / "layout/manifest.json").read_bytes()).hexdigest(),
        "archived_suite": str(ARCHIVED_SUITE.relative_to(ROOT)),
        "suite_sha256": suite_hash,
        "runner_sha256": hashlib.sha256((TOOLS / "behavior.py").read_bytes()).hexdigest(),
        "native_sources": {
            "header_sha256": hashlib.sha256((ROOT / "portable/game/simulation/movement.h").read_bytes()).hexdigest(),
            "source_sha256": hashlib.sha256((ROOT / "portable/game/simulation/movement.c").read_bytes()).hexdigest(),
            "library_sha256": lib_hash,
            "build_command": command,
        },
        "lane": "original DOS invocation vs native shared-library call",
        "directed": not args.random_only,
        "random_count_requested": args.random_count,
        "random_seed": args.seed,
        "executed": count,
        "mismatches": 1 if mismatch else 0,
        "first_mismatch": mismatch,
        "status": "MISMATCH" if mismatch else "PASS",
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "executed": count,
                      "report": str(args.report), "mismatch": mismatch}, indent=2))
    return 1 if mismatch else 0


if __name__ == "__main__":
    raise SystemExit(main())
