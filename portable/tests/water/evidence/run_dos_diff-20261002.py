#!/usr/bin/env python3
"""Compare native water state against original DOS water routines."""
from __future__ import annotations

import ctypes as ct
import hashlib
import json
from pathlib import Path
import random
import struct
import subprocess
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))
import behavior  # noqa: E402
import exe  # noqa: E402
import functions  # noqa: E402
import match  # noqa: E402

GCC = Path("C:/msys64/mingw64/bin/gcc.exe")
LIBRARY = ROOT / "build/portable/water-probe.dll"
REPORT = ROOT / "build/portable/water-dos-diff.json"
DG = match.DGROUP_SEG
MAX_OPS = 16
SURFACE = 128 * 64
NEST = 64 * 64
PHER = 64 * 32
ANT = 500
WATER_DROPS = 100
SNAPSHOT_BYTES = (SURFACE + 4 * NEST + 6 * PHER +
                  2 * (2 + 5 * ANT) + 2 * WATER_DROPS + 10)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def address(name: str) -> int:
    s = behavior.symbol(name)
    return s["seg"] * 16 + s["off"]


def u16(value: int) -> bytes:
    return struct.pack("<H", value & 0xffff)


def u32(value: int) -> bytes:
    return struct.pack("<I", value & 0xffffffff)


def build_native():
    LIBRARY.parent.mkdir(parents=True, exist_ok=True)
    command = [str(GCC), "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror", "-shared",
               "-I", str(ROOT / "portable"),
               str(ROOT / "portable/game/simulation/water.c"),
               str(ROOT / "portable/game/simulation/rng.c"),
               str(ROOT / "portable/tests/water/native_probe.c"), "-o", str(LIBRARY)]
    subprocess.run(command, cwd=ROOT, check=True)
    library = ct.CDLL(str(LIBRARY))
    library.sim_water_probe.argtypes = [ct.POINTER(ct.c_uint8), ct.c_size_t,
                                        ct.POINTER(ct.c_uint8), ct.c_size_t]
    library.sim_water_probe.restype = ct.c_int
    return library, command


def make_input(seed_a: int, seed_b: int, terrain: int, height: int,
               transition: int, operations: list[tuple[int, int, int]], rng_seed: int):
    randomizer = random.Random(rng_seed)
    records = bytearray(struct.pack("<IIhhhh", seed_a, seed_b, terrain, height,
                                    transition, len(operations)))
    for kind, arg, rain in operations:
        records += struct.pack("<Bhh", kind, arg, rain)
    map_a = bytearray(randomizer.choices([0, 3, 0x0d, 0x0e, 0x20, 0x73, 0x74,
                                          0x75, 0x76, 0x77, 0x78], k=SURFACE))
    map_b = bytearray(randomizer.randrange(256) for _ in range(NEST))
    map_r = bytearray(randomizer.randrange(256) for _ in range(NEST))
    life_b = bytearray(randomizer.randrange(256) for _ in range(NEST))
    life_r = bytearray(randomizer.randrange(256) for _ in range(NEST))
    pher = [bytearray(randomizer.randrange(0x50) for _ in range(PHER)) for _ in range(6)]
    drops_x = bytearray(randomizer.randrange(128) for _ in range(WATER_DROPS))
    drops_y = bytearray(randomizer.randrange(64) for _ in range(WATER_DROPS))
    # Place frequent running-water stages at a deterministic subset of the
    # tracked cells so rain-on/off transitions hit every branch in DoWater.
    for i in range(0, WATER_DROPS, 4):
        x, y = drops_x[i], drops_y[i]
        map_a[x * 64 + y] = (0x74, 0x75, 0x76, 0x77)[(i // 4) & 3]

    def list_payload(count: int, salt: int):
        values = [bytearray(ANT) for _ in range(5)]  # type, x, y, mode, state
        for i in range(count):
            values[0][i] = randomizer.choice([0, 8, 0x18, 0x20, 0x58, 0x60, 0x80, 0x88])
            values[1][i] = (i * 7 + salt) & 63
            values[2][i] = (i * 3 + salt) & 63
            values[3][i] = randomizer.randrange(256)
            values[4][i] = randomizer.randrange(256)
        return count, values

    b_count, b_list = list_payload(17, 9)
    r_count, r_list = list_payload(13, 9)
    records += map_a + map_b + map_r + life_b + life_r
    records += b"".join(pher) + drops_x + drops_y
    for count, values in ((b_count, b_list), (r_count, r_list)):
        records += u16(count) + b"".join(values)

    writes = [
        (address("MapA"), bytes(map_a)), (address("MapB"), bytes(map_b)),
        (address("MapR"), bytes(map_r)), (address("LifeB"), bytes(life_b)),
        (address("LifeR"), bytes(life_r)),
        (address("PherMapA"), bytes(pher[0])),
        (address("fd_3E1D_D89F"), bytes(pher[1])),
        (address("PherMapBN"), bytes(pher[2])),
        (address("PherMapBT"), bytes(pher[3])),
        (address("PherMapRN"), bytes(pher[4])),
        (address("PherMapRT"), bytes(pher[5])),
        (address("fd_50F6_0256"), bytes(drops_x)),
        (address("fd_50F6_02C0"), bytes(drops_y)),
        (address("TERRAINset"), u16(terrain)),
        (address("fd_50F6_0242"), u16(height)),
        (address("fd_3D57_0C1E"), u16(transition)),
        (address("ListIndexB"), u16(b_count)), (address("ListIndexR"), u16(r_count)),
    ]
    for name, values in zip(("BlistT", "BlistX", "BlistY", "BlistM", "BlistS"), b_list):
        writes.append((address(name), bytes(values)))
    for name, values in zip(("RlistT", "RlistX", "RlistY", "RlistM", "RlistS"), r_list):
        writes.append((address(name), bytes(values)))
    return bytes(records), writes


def ranges_to_bytes(ranges: dict[str, str]) -> bytes:
    chunks = [bytes.fromhex(ranges[name]) for name in (
        "surface", "nest_b", "nest_r", "life_b", "life_r", "pher_a", "pher_aux",
        "pher_bn", "pher_bt", "pher_rn", "pher_rt")]
    for side in ("b", "r"):
        chunks.extend(bytes.fromhex(ranges[f"list_{side}_{name}"]) for name in
                      ("count", "type", "x", "y", "mode", "state"))
    chunks += [bytes.fromhex(ranges["drop_x"]), bytes.fromhex(ranges["drop_y"]),
               bytes.fromhex(ranges["scan_transition"]), bytes.fromhex(ranges["water_height"]),
               bytes.fromhex(ranges["s_rng"]), bytes.fromhex(ranges["c_rng"])]
    return b"".join(chunks)


def make_ranges():
    items = [("surface", "MapA", SURFACE), ("nest_b", "MapB", NEST),
             ("nest_r", "MapR", NEST), ("life_b", "LifeB", NEST),
             ("life_r", "LifeR", NEST), ("pher_a", "PherMapA", PHER),
             ("pher_aux", "fd_3E1D_D89F", PHER), ("pher_bn", "PherMapBN", PHER),
             ("pher_bt", "PherMapBT", PHER), ("pher_rn", "PherMapRN", PHER),
             ("pher_rt", "PherMapRT", PHER), ("drop_x", "fd_50F6_0256", 100),
             ("drop_y", "fd_50F6_02C0", 100), ("scan_transition", "fd_3D57_0C1E", 2),
             ("water_height", "fd_50F6_0242", 2), ("s_rng", "", 2),
             ("c_rng", "", 4)]
    for side, prefix in (("b", "Blist"), ("r", "Rlist")):
        items.append((f"list_{side}_count", f"ListIndex{side.upper()}", 2))
        for key, suffix in (("type", "T"), ("x", "X"), ("y", "Y"),
                            ("mode", "M"), ("state", "S")):
            items.append((f"list_{side}_{key}", prefix + suffix, ANT))
    return [behavior.Range(name, DG * 16 + 0x8BA2 if name == "s_rng" else
                           DG * 16 + 0x7BBE if name == "c_rng" else address(symbol), size)
            for name, symbol, size in items]


def callback_tick(machine, _args):
    values = machine.state["ticks"]
    index = machine.state.get("tick_index", 0)
    if index >= len(values):
        raise behavior.ExecutionError("unexpected extra TickCount")
    machine.state["tick_index"] = index + 1
    tick = values[index]
    return tick & 0xffff, (tick >> 16) & 0xffff


def callback_sound(machine, args):
    machine.state["host_intents"].append([1, *args])


def callback_zap(machine, args):
    machine.state["host_intents"].append([2, *args])


def parse_native(raw: bytes, op_count: int):
    offset = 0
    statuses = []
    traces = []
    snapshots = []
    for _ in range(op_count):
        statuses.append(raw[offset])
        offset += 1
        count = struct.unpack_from("<H", raw, offset)[0]
        offset += 2
        events = []
        for _ in range(count):
            events.append(list(struct.unpack_from("<Hhhh", raw, offset)))
            offset += 8
        traces.append(events)
        snapshots.append(raw[offset:offset + SNAPSHOT_BYTES])
        offset += SNAPSHOT_BYTES
    return statuses, traces, snapshots


def build_cases():
    rng = random.Random(0x0BE8)
    cases = []
    for index, (terrain, height, transition, rains) in enumerate([
        (0, 0, 0, [0]), (0, 4, 1, [0]), (0, 5, 0, [1]), (0, 63, 1, [0]),
        (0, 64, 0, [1, 0]), (1, 5, 1, [1, 0]), (2, 0, 0, [1]),
        (0, 24, 0, [1, 1, 0, 0]), (0, 4, 1, [1, 0, 1]),
    ]):
        a, b = rng.randrange(1, 0x100000000), rng.randrange(1, 0x100000000)
        ops = [(0, 0, rain) for rain in rains]
        if index in (2, 5):
            ops.insert(0, (1, 0, 0))  # InitWater followed by source rain-state ticks
        if index == 6:
            ops = [(3, height, 0), (4, height, 0)]
        cases.append({"label": f"edge/{index}", "seed_a": a, "seed_b": b,
                      "terrain": terrain, "height": height, "transition": transition,
                      "operations": ops, "fixture_seed": rng.randrange(0x100000000)})
    sound_seed = None
    for tick in range(0x10000):
        state = tick ^ 0x3751
        state = ((state << 1) & 0xffff) ^ (0x1bf5 if state & 0x8000 else 0)
        sound_draw = ((state << 1) & 0xffff) ^ (0x1bf5 if state & 0x8000 else 0)
        state = sound_draw
        add_draw = ((state << 1) & 0xffff) ^ (0x1bf5 if state & 0x8000 else 0)
        if sound_draw % 50 == 0 and add_draw % 10 == 0:
            sound_seed = tick
            break
    if sound_seed is None:
        raise RuntimeError("no LFSR seed found for directed rain-sound/AddWater path")
    cases.append({"label": "directed/rain-sound-add-water", "seed_a": sound_seed,
                  "seed_b": 0x4a72, "terrain": 0, "height": 8, "transition": 0,
                  "operations": [(0, 0, 1)], "fixture_seed": 0x0be8cafe})
    for index in range(40):
        a, b = rng.randrange(1, 0x100000000), rng.randrange(1, 0x100000000)
        terrain = rng.choice([0, 1, 2])
        height = rng.choice([0, 1, 4, 5, 31, 62, 63, 64])
        rains = [rng.randrange(2) for _ in range(rng.randrange(1, 5))]
        ops = [(0, 0, rain) for rain in rains]
        if index % 7 == 0:
            ops.insert(0, (1, 0, 0))
        cases.append({"label": f"random/{index:03d}", "seed_a": a, "seed_b": b,
                      "terrain": terrain, "height": height,
                      "transition": rng.randrange(2), "operations": ops,
                      "fixture_seed": rng.randrange(0x100000000)})
    return cases


def main():
    library, command = build_native()
    target = functions.get("DoWater")
    image = exe.load()
    pair = SimpleNamespace(function=target,
                           vectors={exe.MANAGER_SEG * 16 + vector.offset: vector
                                    for vector in image.vectors})
    pair.sequence_function = lambda name: functions.get(name)
    machine = behavior.Machine(pair)
    observations = make_ranges()
    cases = build_cases()
    failures = []
    executed = 0
    coverage = {"InitWater_calls": 0, "PlaceDrop_calls": 0, "AddWater_calls": 0,
                "DropWater_calls": 0, "DoWater_calls": 0, "DoWater_rain_on": 0,
                "DoWater_rain_off": 0, "nonzero_terrain_DoWater_calls": 0,
                "sound_intents": 0, "map_invalidation_intents": 0}
    for case_spec in cases:
        op_data, writes = make_input(case_spec["seed_a"], case_spec["seed_b"],
                                     case_spec["terrain"], case_spec["height"],
                                     case_spec["transition"], case_spec["operations"],
                                     case_spec["fixture_seed"])
        # Operation bytes are part of the C probe input after the fixed header;
        # the remaining fixture is the deterministic complete state snapshot.
        header = op_data[:16]
        ops = op_data[16:16 + 5 * len(case_spec["operations"])]
        fixture = op_data[16 + 5 * len(case_spec["operations"]):]
        input_bytes = header + ops + fixture
        input_buf = (ct.c_uint8 * len(input_bytes)).from_buffer_copy(input_bytes)
        output_buf = (ct.c_uint8 * (1024 * 1024))()
        out_len = library.sim_water_probe(input_buf, len(input_bytes), output_buf, len(output_buf))
        if out_len < 0:
            raise RuntimeError(f"native probe rejected {case_spec['label']}: {out_len}")
        native_status, native_traces, native_states = parse_native(bytes(output_buf[:out_len]),
                                                                   len(case_spec["operations"]))

        ticks = [case_spec["seed_a"], case_spec["seed_b"]]
        setup = behavior.Case(f"{case_spec['label']}/seed-crt", writes=writes,
                              callbacks={"TickCount": behavior.Callback(0, callback_tick)},
                              return_kind="void", state={"ticks": ticks, "tick_index": 0,
                                                           "host_intents": []})
        machine.run(setup, function="SeedRRand")
        outputs = []
        expected_traces = []
        for op_index, (kind, arg, rain) in enumerate(case_spec["operations"]):
            machine.state["host_intents"] = []
            if kind == 0:
                coverage["DoWater_calls"] += 1
                coverage["DoWater_rain_on" if rain else "DoWater_rain_off"] += 1
                if case_spec["terrain"] != 0:
                    coverage["nonzero_terrain_DoWater_calls"] += 1
                machine.write(address("fd_50F6_0352"), u16(rain))
                function, args = "DoWater", []
            elif kind == 1:
                coverage["InitWater_calls"] += 1
                coverage["PlaceDrop_calls"] += WATER_DROPS
                function, args = "InitWater", []
            elif kind == 2:
                coverage["PlaceDrop_calls"] += 1
                function, args = "PlaceDrop", [arg]
            elif kind == 3:
                coverage["AddWater_calls"] += 1
                function, args = "AddWater", [arg]
            else:
                coverage["DropWater_calls"] += 1
                function, args = "DropWater", [arg]
            original = machine.run(behavior.Case(
                f"{case_spec['label']}/op{op_index}/{function}", args=args,
                observe=observations, callbacks={
                    "myBeginSound": behavior.Callback(3, callback_sound),
                    "ZapEuMapAt": behavior.Callback(3, callback_zap)},
                return_kind="void"), preserve=True, function=function)
            outputs.append(original)
            expected_traces.append(machine.state["host_intents"][:])
            for intent in machine.state["host_intents"]:
                coverage["sound_intents" if intent[0] == 1 else "map_invalidation_intents"] += 1

        original_trace_rows = [[list((kind, *args)) for kind, *args in events]
                               for events in expected_traces]
        for op_index, original in enumerate(outputs):
            native_state = native_states[op_index]
            original_state = ranges_to_bytes(original["ranges"])
            if native_status[op_index] != 0:
                failures.append({"case": case_spec["label"], "operation": op_index,
                                 "kind": "native_status", "status": native_status[op_index]})
                break
            if native_traces[op_index] != original_trace_rows[op_index]:
                failures.append({"case": case_spec["label"], "operation": op_index,
                                 "kind": "intent_trace",
                                 "native": native_traces[op_index],
                                 "original": original_trace_rows[op_index]})
                break
            if native_state != original_state:
                mismatch = next((i for i, (left, right) in enumerate(zip(native_state, original_state))
                                 if left != right), min(len(native_state), len(original_state)))
                failures.append({"case": case_spec["label"], "operation": op_index,
                                 "kind": "state", "first_mismatch_offset": mismatch,
                                 "native_length": len(native_state),
                                 "original_length": len(original_state),
                                 "native_sha256": hashlib.sha256(native_state).hexdigest(),
                                 "original_sha256": hashlib.sha256(original_state).hexdigest(),
                                 "native_hex": native_state.hex(),
                                 "original_hex": original_state.hex()})
                break
        executed += 1

    report = {"schema": "portable-water-dos-diff-v1", "oracle_execution": "original DOS only",
              "runner_sha256": digest(Path(__file__)), "oracle_exe_sha256": digest(exe.EXE_PATH),
              "harness_sha256": {name: digest(ROOT / "tools" / f"{name}.py")
                                  for name in ("behavior", "exe", "functions", "match")},
              "native_source_sha256": {
                  "water.c": digest(ROOT / "portable/game/simulation/water.c"),
                  "water.h": digest(ROOT / "portable/game/simulation/water.h"),
                  "rng.c": digest(ROOT / "portable/game/simulation/rng.c"),
                  "native_probe.c": digest(ROOT / "portable/tests/water/native_probe.c")},
              "unit_test_sha256": digest(ROOT / "portable/tests/water/test_water.c"),
              "unit_test_command": [str(GCC), "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
                                    "-I", str(ROOT / "portable"),
                                    str(ROOT / "portable/game/simulation/water.c"),
                                    str(ROOT / "portable/game/simulation/rng.c"),
                                    str(ROOT / "portable/tests/water/test_water.c")],
              "native_library_sha256": digest(LIBRARY), "native_command": command,
              "case_count": len(cases), "executed_count": executed,
              "passed": executed - len(failures), "failures": failures,
              "coverage": coverage,
              "case_inputs": [{k: v for k, v in spec.items() if k != "fixture_seed"} |
                              {"fixture_seed": spec["fixture_seed"]} for spec in cases],
              "state_boundary": ["surface/nest maps", "LifeB/LifeR", "six pheromone arrays",
                                 "B/R ant lists and modes", "drop-coordinate arrays",
                                 "drop scan transition", "water height", "LFSR seed",
                                 "MSC C rand state", "ordered sound and map-invalidation intents"],
              "sequence_observation": "Compare every state snapshot and ordered effect trace after each operation, including each DoWater tick within a sequence.",
              "services": {"myBeginSound": "typed audio intent boundary",
                           "ZapEuMapAt": "typed map-invalidation boundary",
                           "DrownBList/DrownRList": "actual original DOS helpers during oracle runs"},
              "limitations": ["Timer input was fixed per run through TickCount; the original SeedRRand and CRT RNG executed.",
                              "The host audio and map invalidation sinks are modeled as ordered intents; simulation state and RNG are compared exactly."]}
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"case_count": len(cases), "executed_count": executed,
                      "passed": report["passed"], "mismatch_count": len(failures),
                      "report_path": str(REPORT)}))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
