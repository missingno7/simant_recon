#!/usr/bin/env python3
"""Compare native default-yard RandWorld with a fresh original DOS invocation.

The only modeled boundaries are the player-selection/UI and map-invalidation
requests. All RandWorld game helpers and S-RNG bodies execute from the original
DOS image. The current corpus is a bounded valid seed/terrain domain, not a
claim of universal equivalence.
"""
from __future__ import annotations

import argparse
import ctypes as ct
import hashlib
import json
import random
import shutil
import struct
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[3]
TOOLS = ROOT / "tools"
OUT = ROOT / "build/portable/worldgen-dos-diff"
GCC = Path("C:/msys64/mingw64/bin/gcc.exe")
LIB = OUT / "worldgen_snapshot.dll"
sys.path.insert(0, str(TOOLS))
import behavior  # noqa: E402
import functions  # noqa: E402

SINE = [0, 804, 1607, 2410, 3211, 4011, 4807, 5601, 6392, 7179, 7961,
        8739, 9511, 10278, 11038, 11792, 12539, 13278, 14009, 14732,
        15446, 16150, 16845, 17530, 18204, 18867, 19519, 20159, 20787,
        21402, 22004, 22594, 23169, 23731, 24278, 24811, 25329, 25831,
        26318, 26789, 27244, 27683, 28105, 28510, 28897, 29268, 29621,
        29955, 30272, 30571, 30851, 31113, 31356, 31580, 31785, 31970,
        32137, 32284, 32412, 32520, 32609, 32678, 32727, 32757]

ARRAYS = [
    ("MapA", 128 * 64), ("MapB", 64 * 64), ("MapR", 64 * 64),
    ("ExitMapB", 64 * 64), ("ExitMapR", 64 * 64),
    ("LifeA", 128 * 64), ("LifeB", 64 * 64), ("LifeR", 64 * 64),
    ("fd_3E1D_D89F", 64 * 32), ("PherMapA", 64 * 32),
    ("PherMapBN", 64 * 32), ("PherMapBT", 64 * 32),
    ("PherMapRN", 64 * 32), ("PherMapRT", 64 * 32),
    ("HoleMapB", 64), ("HoleMapR", 64),
]
LISTS = [(f"{prefix}list{field}", count) for prefix, count in
         (("A", 1000), ("B", 500), ("R", 500))
         for field in ("X", "Y", "M", "T", "S")]
SCALARS = [
    ("fd_50F6_0242", 2), ("fd_50F6_0472", 4), ("fd_50F6_09FA", 2),
    ("fd_50F6_0A00", 2), ("fd_50F6_035E", 2), ("fd_50F6_036C", 2),
    ("FoodB", 2), ("FoodR", 2), ("fd_50F6_1040", 2),
    ("HealthB", 2), ("HealthR", 2), ("Cycle", 2),
    ("fd_50F6_0508", 4), ("fd_50F6_0596", 4),
    ("fd_50F6_06A6", 4), ("fd_50F6_072E", 4),
    ("fd_50F6_0F0E", 2), ("fd_50F6_0F26", 2),
    ("MePlane", 2), ("MeLocX", 2), ("MeLocY", 2),
    ("fd_50F6_04C2", 2), ("fd_50F6_0496", 2),
    ("fd_50F6_04C4", 2),
    ("fd_50F6_0AFA", 12), ("fd_50F6_0AEC", 12),
    ("fd_50F6_0EB6", 64), ("BpopT", 2), ("RpopT", 2),
    ("fd_50F6_0354", 2), ("fd_50F6_0366", 2),
    ("fd_50F6_0376", 2),
    ("fd_50F6_105E", 2), ("fd_50F6_0214", 4),
    ("fd_50F6_0204", 4), ("fd_50F6_0228", 2),
    ("fd_50F6_0478", 2), ("fd_50F6_0504", 2),
    ("fd_3D57_0C44", 2), ("fd_3D57_0C18", 2),
    ("fd_3D57_0C16", 2), ("fd_3D57_0C14", 2),
    ("fd_50F6_0C26", 4),
    ("fd_50F6_049A", 2), ("fd_3D57_0C22", 2),
    ("fd_50F6_104E", 2), ("fd_3D57_07BE", 2),
    ("fd_3D57_02BC", 4),
    ("CurGndTileID", 2), ("DROPdir", 2), ("fd_50F6_0480", 2),
    ("TERRAINset", 2), ("g_1A2E", 2),
    ("LionIndex", 2), ("InitialLions", 2), ("AntsEatenByLions", 2),
    ("LionListX", 10), ("LionListY", 10), ("LionListM", 10),
    ("LionListS", 10), ("LionListT", 10),
    ("SowX", 6), ("SowY", 6), ("SowDir", 6), ("SowSave", 6),
    ("PillarState", 2), ("PillarX", 2), ("PillarY", 2),
    ("PillarSeg", 2), ("PillDir", 2), ("PillarMap", 12),
]
COUNTS = [("ListIndexA", 2), ("ListIndexB", 2), ("ListIndexR", 2)]
RANGES = ARRAYS + LISTS + COUNTS + SCALARS


def word(value: int) -> bytes:
    return struct.pack("<H", value & 0xffff)


def range_of(name: str, size: int):
    return behavior.Range(name, source_address(name), size)


def source_address(name: str) -> int:
    if name == "g_1A2E":
        return behavior.match.DGROUP_SEG * 16 + 0x1A2E
    return behavior.symbol_address(name)


def build_native():
    OUT.mkdir(parents=True, exist_ok=True)
    sources = [
        "portable/tests/worldgen/native_snapshot.c",
        "portable/game/simulation/worldgen.c",
        "portable/game/simulation/rng.c",
        "portable/game/simulation/terrain.c",
        "portable/game/simulation/ants.c",
        "portable/game/simulation/population.c",
        "portable/game/simulation/spider.c",
        "portable/game/simulation/nest.c",
        "portable/game/simulation/setup.c",
        "portable/game/simulation/yard.c",
        "portable/game/state/world.c",
        "portable/game/simulation/movement.c",
    ]
    command = [str(GCC), "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
               "-shared", "-I", str(ROOT / "portable/game/simulation"),
               "-I", str(ROOT / "portable/game/state"),
               *(str(ROOT / p) for p in sources), "-o", str(LIB)]
    subprocess = __import__("subprocess")
    subprocess.run(command, check=True, cwd=ROOT)
    lib = ct.CDLL(str(LIB))
    lib.sim_worldgen_native_snapshot.argtypes = [ct.c_uint16, ct.c_int16, ct.c_int16,
                                                  ct.c_int16, ct.c_int16,
                                                  ct.POINTER(ct.c_uint8), ct.c_size_t]
    lib.sim_worldgen_native_snapshot.restype = ct.c_size_t
    return lib, command


def case_for(seed: int, scenario: int = 0, black_size: int = 1, red_size: int = 1):
    writes = []
    for name, size in ARRAYS:
        cleared_by_rand_yard = name not in {"HoleMapB", "HoleMapR"}
        writes.append((behavior.symbol_address(name),
                       bytes(size) if cleared_by_rand_yard else bytes([0xA5]) * size))
    for name, size in LISTS:
        # ClrArrays clears type/mode/state only. Coordinates and inactive slots
        # retain prior memory and are intentionally poisoned.
        clear = name.endswith(("M", "T", "S"))
        writes.append((behavior.symbol_address(name),
                       bytes(size) if clear else bytes([0xA5]) * size))
    for name, size in COUNTS + SCALARS:
        writes.append((source_address(name), bytes([0xA5]) * size))
    for name in ("fd_3D57_02BC", "CurGndTileID", "DROPdir", "fd_50F6_0480",
                 "TERRAINset", "g_1A2E", "LionIndex", "InitialLions", "AntsEatenByLions",
                 "LionListX", "LionListY", "LionListM", "LionListS", "LionListT",
                 "SowX", "SowY", "SowDir", "SowSave", "PillarState", "PillarX",
                 "PillarY", "PillarSeg", "PillDir", "PillarMap"):
        size = next(n for symbol, n in SCALARS if symbol == name)
        writes.append((source_address(name), bytes(size)))
    scalar_initial = {
        "TERRAINset": 0, "fd_50F6_0EAC": scenario, "fd_50F6_0354": 1,
        "fd_50F6_0A06": 0, "fd_50F6_04E2": 0, "fd_50F6_0400": 0,
        "fd_50F6_07CA": 11, "fd_50F6_07BC": 11,
        "fd_50F6_0F0E": 0, "fd_50F6_0F26": 0,
        "fd_50F6_0FB6": 128, "fd_50F6_0FFA": 64,
        "fd_3D57_0C24": 0 if scenario == 2 else 1,
        "ListIndexA": 17, "ListIndexB": 3, "ListIndexR": 2,
        "fd_50F6_035E": 0, "fd_50F6_036C": 0,
        "fd_50F6_0366": 0, "fd_50F6_0376": 0,
        "fd_50F6_0242": 0, "fd_50F6_0472": 0,
        "fd_50F6_09FA": 0, "fd_50F6_0A00": 0,
        "fd_50F6_049A": 0x4567, "fd_3D57_0C22": 0x4567,
        "fd_50F6_104E": 1, "fd_3D57_07BE": 0x2345,
        "fd_50F6_105E": -1, "fd_50F6_0214": 0,
        "fd_50F6_0204": 0, "fd_50F6_0228": 0,
        "fd_50F6_0478": 0, "fd_50F6_0504": 0,
        "fd_3D57_0C44": 0, "fd_3D57_0C18": 0,
        "fd_3D57_0C16": 0, "fd_3D57_0C14": 0,
        "fd_50F6_0C26": 0,
    }
    for name, value in scalar_initial.items():
        size = dict(SCALARS).get(name, 2)
        initial = struct.pack("<I", value & 0xffffffff) if size == 4 else word(value)
        writes.append((source_address(name), initial))
    writes.append((behavior.symbol_address("fd_50F6_07CA") + 2, word(8)))
    writes.append((behavior.symbol_address("fd_50F6_07BC") + 2, word(8)))
    sine_arena = 0xD0000
    writes.append((behavior.symbol_address("fd_50F6_0B22"),
                   word(0) + word(0xD000)))
    writes.append((sine_arena, b"".join(word(v) for v in SINE)))
    state = {}

    def host_boundary(machine, args):
        machine.state.setdefault("host_boundaries", []).append(list(args))
        return None

    callbacks = {
        "o22_39C7_07FD": behavior.Callback(3, host_boundary),
        "InvalEuMap": behavior.Callback(4, host_boundary),
    }
    case = behavior.Case(
        label=f"scenario-{scenario}-seed-{seed:04x}",
        args=[seed, black_size, red_size, 11, 8],
        writes=writes,
        observe=[range_of(name, size) for name, size in RANGES],
        callbacks=callbacks, return_kind="void", callee_pop=0,
        state=state, metadata={"scenario": scenario, "terrain_set": 0,
                               "sizes": [black_size, red_size], "map": [11, 8],
                               "host_boundaries": ["o22_39C7_07FD",
                                                   "InvalEuMap"]})
    return case


def native_snapshot(lib, seed: int, scenario: int = 0, terrain_set: int = 0,
                    black_size: int = 1, red_size: int = 1):
    buf = (ct.c_uint8 * 100000)()
    size = lib.sim_worldgen_native_snapshot(seed, scenario, terrain_set,
                                            black_size, red_size, buf, len(buf))
    if not size:
        raise RuntimeError("native snapshot returned failure/overflow")
    data = bytes(buf[:size])
    cursor = 0

    def take(size):
        nonlocal cursor
        value = data[cursor:cursor + size]
        if len(value) != size:
            raise RuntimeError("short native snapshot")
        cursor += size
        return value

    def i16():
        return struct.unpack("<h", take(2))[0]

    result = {"status": i16(), "s_state": i16(), "c_state": struct.unpack("<I", take(4))[0],
              "ranges": {}}
    for name, size in ARRAYS:
        result["ranges"][name] = take(size)
    for name, size in LISTS:
        result["ranges"][name] = take(size)
    for name in ("ListIndexA", "ListIndexB", "ListIndexR"):
        result["ranges"][name] = take(2)
    scalar_bytes = {}
    for name, size in [
        ("fd_50F6_0242", 2), ("fd_50F6_0472", 4), ("fd_50F6_09FA", 2),
        ("fd_50F6_0A00", 2), ("fd_50F6_035E", 2), ("fd_50F6_036C", 2),
        ("FoodB", 2), ("FoodR", 2), ("fd_50F6_1040", 2),
        ("HealthB", 2), ("HealthR", 2), ("Cycle", 2),
        ("fd_50F6_0508", 4), ("fd_50F6_0596", 4),
        ("fd_50F6_06A6", 4), ("fd_50F6_072E", 4),
        ("fd_50F6_0F0E", 2), ("fd_50F6_0F26", 2),
        ("MePlane", 2), ("MeLocX", 2), ("MeLocY", 2),
        ("fd_50F6_04C2", 2), ("fd_50F6_0496", 2),
        ("fd_50F6_04C4", 2),
        ("fd_50F6_0AFA", 12), ("fd_50F6_0AEC", 12),
        ("fd_50F6_0EB6", 64), ("BpopT", 2), ("RpopT", 2),
        ("fd_50F6_0354", 2), ("fd_50F6_0366", 2),
        ("fd_50F6_0376", 2),
        ("fd_50F6_105E", 2), ("fd_50F6_0214", 4),
        ("fd_50F6_0204", 4), ("fd_50F6_0228", 2),
        ("fd_50F6_0478", 2), ("fd_50F6_0504", 2),
        ("fd_3D57_0C44", 2), ("fd_3D57_0C18", 2),
        ("fd_3D57_0C16", 2), ("fd_3D57_0C14", 2),
        ("fd_50F6_0C26", 4),
        ("fd_50F6_049A", 2), ("fd_3D57_0C22", 2),
        ("fd_50F6_104E", 2), ("fd_3D57_07BE", 2),
        ("fd_3D57_02BC", 4),
        ("CurGndTileID", 2), ("DROPdir", 2), ("fd_50F6_0480", 2),
        ("TERRAINset", 2), ("g_1A2E", 2),
        ("LionIndex", 2), ("InitialLions", 2), ("AntsEatenByLions", 2),
        ("LionListX", 10), ("LionListY", 10), ("LionListM", 10),
        ("LionListS", 10), ("LionListT", 10),
        ("SowX", 6), ("SowY", 6), ("SowDir", 6), ("SowSave", 6),
        ("PillarState", 2), ("PillarX", 2), ("PillarY", 2),
        ("PillarSeg", 2), ("PillDir", 2), ("PillarMap", 12),
    ]:
        scalar_bytes[name] = take(size)
    for name, raw in scalar_bytes.items():
        result["ranges"][name] = raw
    result["private"] = {
        "total_population_black": i16(), "total_population_red": i16(),
        "dug_b_x_sum": i16(), "dug_b_y_sum": i16(), "dug_b_count": i16(),
        "dug_b_x_average": i16(), "dug_b_y_average": i16(),
        "dug_r_x_sum": i16(), "dug_r_y_sum": i16(), "dug_r_count": i16(),
        "dug_r_x_average": i16(), "dug_r_y_average": i16(),
        "worldgen_effect_count": i16(), "population_effect_count": i16(),
    }
    if cursor != len(data):
        raise RuntimeError(f"snapshot parser consumed {cursor}/{len(data)}")
    return result


def run_case(machine, lib, seed, scenario=0, black_size=1, red_size=1):
    case = case_for(seed, scenario, black_size, red_size)
    input_hash = hashlib.sha256()
    input_hash.update(json.dumps({
        "label": case.label, "args": case.args,
        "registers": case.registers, "state": case.state,
        "observe": [(r.name, r.address, r.size) for r in case.observe],
        "callbacks": {name: {"stack_words": cb.stack_words,
                             "has_handler": cb.handler is not None}
                      for name, cb in case.callbacks.items()},
    }, sort_keys=True, separators=(",", ":")).encode())
    for address, data in case.writes:
        input_hash.update(struct.pack("<II", address, len(data)))
        input_hash.update(data)
    machine.final_s_state = None
    machine.query_done = False
    try:
        oracle = machine.run(case)
    except Exception as exc:
        print(f"oracle failed after {machine.blocks} blocks; recent PCs="
              f"{[hex(pc) for pc in getattr(machine, 'recent_pcs', [])]}",
              flush=True)
        raise
    native = native_snapshot(lib, seed, scenario, 0, black_size, red_size)
    native_s_state = native["s_state"] & 0xffff
    diffs = {}
    for name, _size in RANGES:
        expected = bytes.fromhex(oracle["ranges"][name])
        actual = native["ranges"][name]
        if expected != actual:
            # Keep concise diagnostics while retaining first differing bytes.
            offsets = [i for i, (a, b) in enumerate(zip(expected, actual)) if a != b]
            diffs[name] = {"expected_size": len(expected), "actual_size": len(actual),
                           "mismatch_count": len(offsets),
                           "first_offsets": offsets[:16],
                           "first_byte_pairs": [
                               {"offset": i,
                                "x": i // 64 if name == "MapA" else None,
                                "y": i % 64 if name == "MapA" else None,
                                "oracle": expected[i], "native": actual[i]}
                               for i in offsets[:32]],
                           "expected_prefix": expected[:32].hex(),
                           "actual_prefix": actual[:32].hex()}
    original_boundaries = oracle["state"].get("host_boundaries", [])
    original_s_state = getattr(machine, "final_s_state", None)
    if original_s_state is not None and original_s_state != native_s_state:
        diffs["S-RNG final state"] = {"oracle": original_s_state,
                                      "native": native_s_state}
    if native["status"] != 0:
        diffs["native status"] = native["status"]
    oracle_ranges = {name: oracle["ranges"][name] for name, _ in RANGES}
    native_ranges = {name: native["ranges"][name].hex() for name, _ in RANGES}
    def digest_ranges(ranges):
        payload = json.dumps(ranges, sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(payload).hexdigest()
    return {"label": case.label, "seed": seed, "mismatches": diffs,
            "input_sha256": input_hash.hexdigest(),
            "oracle_host_boundaries": original_boundaries,
            "oracle_s_state": original_s_state,
            "native_s_state": native_s_state,
            "oracle_return": oracle["return"], "native_return": None,
            "oracle_observation_sha256": digest_ranges(oracle_ranges),
            "native_observation_sha256": digest_ranges(native_ranges),
            "native_event_counts": native["private"]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=lambda value: int(value, 0), default=0x5a31)
    parser.add_argument("--scenarios", default="0", help="comma-separated scenario IDs")
    parser.add_argument("--random-count", type=int, default=0)
    parser.add_argument("--random-seed", type=lambda value: int(value, 0), default=0x523157)
    parser.add_argument("--report", type=Path, default=OUT / "report.json")
    args = parser.parse_args()

    lib, command = build_native()
    x = behavior.exe.load()
    pair = SimpleNamespace(function=functions.get("RandWorld"),
                           vectors={behavior.exe.MANAGER_SEG * 16 + v.offset: v
                                    for v in x.vectors})
    class TracedMachine(behavior.Machine):
        def __init__(self, pair):
            self.recent_pcs = []
            self.final_s_state = None
            self.query_s_state = True
            self.query_done = False
            super().__init__(pair)

        def _on_block(self, cpu, address, size, userdata):
            self.recent_pcs.append(address)
            if len(self.recent_pcs) > 80:
                del self.recent_pcs[0]
            return super()._on_block(cpu, address, size, userdata)

        def run(self, case, *, preserve=False, function=None):
            result = super().run(case, preserve=preserve, function=function)
            if function is not None or preserve or not self.query_s_state:
                return result
            # The normal `until` stop occurs before the sentinel block hook.
            # Make a second far call in the same oracle memory image to read
            # the actual private LFSR seed via the original getter.
            saved_sp = self.reg("sp")
            query_sp = saved_sp - 4
            self.cpu.mem_write(self.reg("ss") * 16 + query_sp,
                               behavior.words(behavior.SENTINEL[1],
                                              behavior.SENTINEL[0]))
            getter = functions.get("GetSRandSeed")
            self.set_reg("sp", query_sp)
            self.set_reg("cs", getter["seg"])
            self.set_reg("ip", getter["off"])
            self.active = True
            self.completed = False
            self.error = None
            self.blocks = 0
            self.cpu.emu_start(getter["seg"] * 16 + getter["off"],
                               behavior.SENTINEL_LINEAR,
                               count=case.max_instructions)
            self.final_s_state = self.reg("ax")
            self.set_reg("sp", saved_sp)
            self.active = False
            return result

    machine = TracedMachine(pair)
    seeds = [args.seed]
    rng = random.Random(args.random_seed)
    seeds.extend(rng.randrange(0x8000) for _ in range(args.random_count))
    scenarios = [int(value, 0) for value in args.scenarios.split(",")]
    inputs = [(seed, scenario) for scenario in scenarios for seed in seeds]
    rows = []
    for index, (seed, scenario) in enumerate(inputs, 1):
        print(f"DOS/native RandWorld case {index}/{len(inputs)} scenario={scenario} "
              f"seed=0x{seed:04x}", flush=True)
        rows.append(run_case(machine, lib, seed, scenario))
    mismatches = [row for row in rows if row["mismatches"]]
    report = {
        "schema": "native-dos-randworld-differential-v1",
        "oracle_identity": {"path": "assets/SIMANT.EXE",
                            "sha256": x.sha256},
        "oracle_sha256": x.sha256,
        "harness_sha256": hashlib.sha256((TOOLS / "behavior.py").read_bytes()).hexdigest(),
        "source_sha256": hashlib.sha256((ROOT / "portable/game/simulation/worldgen.c").read_bytes()).hexdigest(),
        "header_sha256": hashlib.sha256((ROOT / "portable/game/simulation/worldgen.h").read_bytes()).hexdigest(),
        "native_bridge_sha256": hashlib.sha256((ROOT / "portable/tests/worldgen/native_snapshot.c").read_bytes()).hexdigest(),
        "native_library_sha256": hashlib.sha256(LIB.read_bytes()).hexdigest(),
        "native_source_hashes": {
            path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
            for path in [
                "portable/game/simulation/worldgen.c",
                "portable/game/simulation/worldgen.h",
                "portable/game/simulation/rng.c",
                "portable/game/simulation/rng.h",
                "portable/game/simulation/terrain.c",
                "portable/game/simulation/terrain.h",
                "portable/game/simulation/ants.c",
                "portable/game/simulation/ants.h",
                "portable/game/simulation/population.c",
                "portable/game/simulation/population.h",
                "portable/game/simulation/spider.c",
                "portable/game/simulation/spider.h",
                "portable/game/simulation/nest.c",
                "portable/game/simulation/nest.h",
                "portable/game/simulation/setup.c",
                "portable/game/simulation/setup.h",
                "portable/game/simulation/yard.c",
                "portable/game/simulation/yard.h",
                "portable/game/state/world.c",
                "portable/game/state/world.h",
                "portable/game/simulation/movement.c",
                "portable/game/simulation/movement.h",
            ]
        },
        "compiler_sha256": hashlib.sha256(GCC.read_bytes()).hexdigest(),
        "compared_ranges": [{"name": name, "size": size} for name, size in RANGES],
        "build_command": command,
        "domain": {"scenarios": scenarios, "terrain_set": 0, "black_size": 1,
                   "red_size": 1, "map_width": 11, "map_kind": 8,
                   "seed_range": "0..0x7fff", "game_helpers": "original DOS bodies",
                   "modeled_boundaries": ["o22_39C7_07FD", "InvalEuMap"]},
        "prestate_contract": {
            "phase": "RandYard immediately after ClrArrays and before RandWorld",
            "cleared_arrays": ["MapA", "MapB/R", "ExitMapB/R", "LifeA/B/R",
                               "all pheromone planes", "ant M/T/S lists"],
            "preserved_poison": ["inactive ant-list coordinate slots",
                                 "InitYelloAnt condition globals 104E/07BE"],
            "sine_table": "test-owned far arena D000:0000 via fd_50F6_0B22 far pointer",
            "rng": "original SetSRandSeed input and post-call original GetSRandSeed comparison",
        },
        "limits": ["bounded seed/scenario domain", "black/red size fixed to 1",
                   "terrain selector fixed to 0", "map fixed to 11x8",
                   "player-selection and map-invalidation are explicit host boundaries"],
        "case_count": len(rows), "random_count": args.random_count,
        "random_seed": args.random_seed, "mismatch_count": len(mismatches),
        "first_mismatch": mismatches[0] if mismatches else None,
        "rows": rows,
        "status": "MISMATCH" if mismatches else "PASS",
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "case_count": len(rows),
                      "mismatch_count": len(mismatches),
                      "first_mismatch": report["first_mismatch"],
                      "report": str(args.report)}, indent=2))
    return 1 if mismatches else 0


if __name__ == "__main__":
    raise SystemExit(main())
