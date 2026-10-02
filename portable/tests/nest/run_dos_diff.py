#!/usr/bin/env python3
"""Compare native EnterNest transitions with fresh frozen-DOS executions."""
from __future__ import annotations

import argparse
import ctypes as ct
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TOOLS = ROOT / "tools"
SUITE_PATH = ROOT / "tools/behavior_suites/archive/spider_nest-20261002-current-runner-ledger-final.py"
LIBRARY = ROOT / "build/portable/nest.dll"
REPORT = ROOT / "build/portable/nest-dos-diff.json"
GCC = Path("C:/msys64/mingw64/bin/gcc.exe")
sys.path.insert(0, str(TOOLS))
import behavior  # noqa: E402
import functions  # noqa: E402


class SimNestTestWorld(ct.Structure):
    _fields_ = [
        ("surface", (ct.c_uint8 * 64) * 128),
        ("nest_b", (ct.c_uint8 * 64) * 64),
        ("nest_r", (ct.c_uint8 * 64) * 64),
        ("exit_b", (ct.c_uint8 * 64) * 64),
        ("exit_r", (ct.c_uint8 * 64) * 64),
        ("life_a", (ct.c_uint8 * 64) * 128),
        ("life_b", (ct.c_uint8 * 64) * 64),
        ("life_r", (ct.c_uint8 * 64) * 64),
        ("hole_b", ct.c_uint8 * 64),
        ("hole_r", ct.c_uint8 * 64),
        ("terrain_set", ct.c_int16),
        ("current_ant_plane", ct.c_int16),
        ("me_x", ct.c_int16), ("me_y", ct.c_int16),
        ("me_type", ct.c_int16), ("me_direction", ct.c_int16),
    ]


class SimRng(ct.Structure):
    _fields_ = [("s_state", ct.c_uint16), ("c_state", ct.c_uint32)]


class SimNestRuntime(ct.Structure):
    _fields_ = [(n, ct.c_int16) for n in (
        "alarm_drop_state", "alarm_indicator", "theme_index")]
    _fields_ += [("theme_last_tick", ct.c_int32)]
    _fields_ += [(n, ct.c_int16) for n in ("invalidate_right", "invalidate_bottom")]
    _fields_ += [(n, ct.c_int32) for n in (
        "dug_b_x_sum", "dug_b_y_sum", "dug_r_x_sum", "dug_r_y_sum")]
    _fields_ += [(n, ct.c_int16) for n in (
        "dug_b_count", "dug_r_count", "dug_b_x_average", "dug_b_y_average",
        "dug_r_x_average", "dug_r_y_average", "entrance_b_surface_x",
        "entrance_b_surface_y", "entrance_r_surface_x", "entrance_r_surface_y",
        "entrance_b_nest_x", "entrance_b_nest_y", "entrance_r_nest_x",
        "entrance_r_nest_y")]


class SimNestRequest(ct.Structure):
    _fields_ = [("tick_values", ct.c_int32 * 2), ("tick_count", ct.c_uint8)]


class SimNestEvent(ct.Structure):
    _fields_ = [("kind", ct.c_uint16), ("argument_count", ct.c_uint16),
                ("arguments", ct.c_int32 * 6)]


class SimNestTrace(ct.Structure):
    _fields_ = [("count", ct.c_uint16), ("overflow", ct.c_uint8),
                ("events", SimNestEvent * 256)]


def read_suite():
    spec = importlib.util.spec_from_file_location("archived_spider_nest", SUITE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def build_library():
    LIBRARY.parent.mkdir(parents=True, exist_ok=True)
    command = [str(GCC), "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror", "-shared",
               "-I", str(ROOT / "portable/game/simulation"),
               str(ROOT / "portable/tests/nest/native_adapter.c"),
               str(ROOT / "portable/game/simulation/nest.c"),
               str(ROOT / "portable/game/simulation/rng.c"), "-o", str(LIBRARY)]
    subprocess.run(command, check=True, cwd=ROOT)
    return command, hashlib.sha256(LIBRARY.read_bytes()).hexdigest()


def append_write(case, name, value, size=2):
    data = int(value & ((1 << (8 * size)) - 1)).to_bytes(size, "little")
    case.writes.append((behavior.symbol_address(name), data))


def append_blob(case, name, data):
    case.writes.append((behavior.symbol_address(name), bytes(data)))


def ranges(case, *names):
    for name, size in names:
        case.observe.append(behavior.Range(name, behavior.symbol_address(name), size))


def controlled_case(case, index, dirt_mode="source"):
    domain = case.metadata["domain"]
    old_y = domain["initial_y"]
    destination_x = old_y
    destination_y = 2 if domain["ant_type"] == 0x60 else 1
    destination_plane = 3 if domain["initial_x"] > 0x40 else 2

    # Use controlled input values for all additional state that the native
    # transition owns. Alternating cases exercise theme expiry and track wrap.
    tick_start = 0
    if index % 4 == 0:
        tick_start = 7162  # first TickCount is 7199
    elif index % 4 == 1:
        tick_start = 7163  # first TickCount is exactly 7200
    case.state["tick"] = tick_start
    first_tick = (tick_start + 37) & 0xffff
    theme_last = 0 if index % 2 == 0 else -7199
    theme_index = index % 3
    append_write(case, "fd_50F6_0214", theme_last, size=4)
    append_write(case, "fd_50F6_0228", theme_index)
    append_write(case, "fd_50F6_104E", domain["alarm"])
    append_write(case, "fd_3D57_07BE", 7)
    append_write(case, "fd_50F6_0FB6", 64)
    append_write(case, "fd_50F6_0FFA", 32)
    append_write(case, "TERRAINset", index % 2)
    case.writes[-1] = (case.writes[-1][0], int(index % 2).to_bytes(2, "little"))
    # Explicit zero state for the arrays the recovered entrance/dig helpers
    # consult. Existing source-case map/life fills are retained, then target
    # tile fixtures are applied below.
    for name, size in (("LifeA", 128 * 64), ("ExitMapB", 64 * 64),
                       ("ExitMapR", 64 * 64), ("HoleMapB", 64), ("HoleMapR", 64)):
        append_blob(case, name, bytes(size))
    for name, size in (("fd_50F6_1068", 4), ("fd_50F6_1082", 4),
                       ("fd_50F6_0224", 2), ("fd_50F6_10B2", 2),
                       ("fd_50F6_10C0", 2), ("fd_50F6_108E", 4),
                       ("fd_50F6_10A2", 4), ("TilesDugR", 2),
                       ("fd_50F6_0200", 2), ("fd_50F6_020E", 2),
                       ("fd_3D57_02AC", 4), ("fd_3D57_02A4", 4),
                       ("fd_3D57_02B0", 4), ("fd_3D57_02A8", 4)):
        append_blob(case, name, bytes(size))

    if dirt_mode != "source":
        map_name = "MapB" if destination_plane == 2 else "MapR"
        if dirt_mode == "dirt": tile = 0x20 + (index % 15)
        elif dirt_mode == "grass": tile = 0x1c + (index % 4)
        else: tile = int(dirt_mode)
        append_blob(case, map_name, b"")
        cell = behavior.symbol_address(map_name) + destination_x * 64 + destination_y
        case.writes.append((cell, bytes([tile])))

    case.metadata["native_port_case"] = {
        "index": index, "target_tile_mode": dirt_mode,
        "destination": [destination_plane, destination_x, destination_y],
        "tick_start": tick_start, "tick_values": [first_tick, (tick_start + 74) & 0xffff],
        "theme_last": theme_last, "theme_index": theme_index,
    }
    ranges(case,
        ("LifeA", 128 * 64), ("ExitMapB", 64 * 64), ("ExitMapR", 64 * 64),
        ("fd_50F6_0214", 4), ("fd_50F6_0228", 2), ("fd_3D57_07BE", 2),
        ("fd_50F6_1068", 4), ("fd_50F6_1082", 4), ("fd_50F6_0224", 2),
        ("fd_50F6_10B2", 2), ("fd_50F6_10C0", 2), ("fd_50F6_108E", 4),
        ("fd_50F6_10A2", 4), ("TilesDugR", 2), ("fd_50F6_0200", 2),
        ("fd_50F6_020E", 2), ("fd_3D57_02AC", 4), ("fd_3D57_02A4", 4),
        ("fd_3D57_02B0", 4), ("fd_3D57_02A8", 4),
    )
    return case


def build_native_world(case):
    native = SimNestTestWorld()
    maps = {
        "MapA": ("surface", 128 * 64), "MapB": ("nest_b", 64 * 64),
        "MapR": ("nest_r", 64 * 64), "ExitMapB": ("exit_b", 64 * 64),
        "ExitMapR": ("exit_r", 64 * 64), "LifeA": ("life_a", 128 * 64),
        "LifeB": ("life_b", 64 * 64), "LifeR": ("life_r", 64 * 64),
        "HoleMapB": ("hole_b", 64), "HoleMapR": ("hole_r", 64),
    }
    for address, data in case.writes:
        for name, (field, size) in maps.items():
            base = behavior.symbol_address(name)
            if base <= address and address + len(data) <= base + size:
                offset = address - base
                ct.memmove(ct.addressof(native) + getattr(SimNestTestWorld, field).offset + offset,
                           data, len(data))
                break
    domain = case.metadata["domain"]
    native.terrain_set = next((int.from_bytes(data[:2], "little", signed=True)
                               for address, data in reversed(case.writes)
                               if address == behavior.symbol_address("TERRAINset")), 0)
    native.current_ant_plane = domain["initial_plane"]
    native.me_x = domain["initial_x"]
    native.me_y = domain["initial_y"]
    native.me_type = domain["ant_type"]
    native.me_direction = domain["initial_direction"]
    return native


def signed16(value):
    value &= 0xffff
    return value - 0x10000 if value >= 0x8000 else value


def native_call(lib, case):
    domain = case.metadata["native_port_case"]
    runtime = SimNestRuntime()
    runtime.alarm_drop_state = domain["alarm"] if "alarm" in domain else case.metadata["domain"]["alarm"]
    runtime.alarm_indicator = 7
    runtime.theme_index = domain["theme_index"]
    runtime.theme_last_tick = domain["theme_last"]
    runtime.invalidate_right = 64
    runtime.invalidate_bottom = 32
    request = SimNestRequest()
    request.tick_values[0] = domain["tick_values"][0]
    request.tick_values[1] = domain["tick_values"][1]
    request.tick_count = 2
    rng = SimRng(0xBEEF, 0)
    trace = SimNestTrace()
    world = build_native_world(case)
    status = lib.sim_nest_test_run(ct.byref(world), ct.byref(rng),
                                   ct.byref(runtime), ct.byref(request), ct.byref(trace))
    return int(status), world, rng, runtime, trace


def range_bytes(oracle, name):
    return bytes.fromhex(oracle["ranges"][name])


def expected_callbacks(oracle):
    expected_names = {"TickCount", "myBeginSong", "SetAlarmDropState",
                      "win_SetObjSelectedState", "InvalEuMap", "myBeginSound", "SRand1"}
    return [(entry["name"], tuple(entry["args"])) for entry in oracle["trace"]
            if entry["name"] in expected_names]


def native_callbacks(trace):
    output = []
    kind_names = {
        1: None, 2: "myBeginSong", 3: "SetAlarmDropState", 4: "win_SetObjSelectedState",
        5: "InvalEuMap", 6: "myBeginSound", 11: "SRand1",
    }
    for event in trace.events[:trace.count]:
        kind = int(event.kind)
        name = kind_names.get(kind)
        if kind == 1:
            output.append(("TickCount", ()))
            continue
        if name is None:
            continue
        args = tuple(int(v) & 0xffff for v in event.arguments[:event.argument_count])
        output.append((name, args))
    return output


def compare_case(machine, lib, suite, case):
    oracle = machine.run(case)
    status, world, rng, runtime, trace = native_call(lib, case)
    if status != 0:
        return {"status": status, "case": case.label}
    ranges_to_native = {
        "MapA": ("surface", 128 * 64), "MapB": ("nest_b", 64 * 64),
        "MapR": ("nest_r", 64 * 64), "LifeA": ("life_a", 128 * 64),
        "LifeB": ("life_b", 64 * 64), "LifeR": ("life_r", 64 * 64),
        "ExitMapB": ("exit_b", 64 * 64), "ExitMapR": ("exit_r", 64 * 64),
        "HoleMapB": ("hole_b", 64), "HoleMapR": ("hole_r", 64),
    }
    diffs = {}
    for oracle_name, (field, size) in ranges_to_native.items():
        oracle_bytes = range_bytes(oracle, oracle_name)
        native_bytes = ct.string_at(ct.addressof(world) + getattr(SimNestTestWorld, field).offset, size)
        if oracle_bytes != native_bytes:
            first = next(i for i, (a, b) in enumerate(zip(oracle_bytes, native_bytes)) if a != b)
            diffs[oracle_name] = {"first_offset": first, "oracle": oracle_bytes[first],
                                  "native": native_bytes[first]}
    scalar_native = {
        "MePlane": world.current_ant_plane, "MeLocX": world.me_x,
        "MeLocY": world.me_y, "fd_50F6_0496": 4,
        "fd_50F6_04C2": case.metadata["domain"]["ant_type"],
        "fd_50F6_104E": runtime.alarm_drop_state,
        "g_8BA2": rng.s_state,
        "fd_50F6_0214": runtime.theme_last_tick,
        "fd_50F6_0228": runtime.theme_index,
        "fd_3D57_07BE": runtime.alarm_indicator,
        "fd_50F6_1068": runtime.dug_b_x_sum,
        "fd_50F6_1082": runtime.dug_b_y_sum,
        "fd_50F6_0224": runtime.dug_b_count,
        "fd_50F6_10B2": runtime.dug_b_x_average,
        "fd_50F6_10C0": runtime.dug_b_y_average,
        "fd_50F6_108E": runtime.dug_r_x_sum,
        "fd_50F6_10A2": runtime.dug_r_y_sum,
        "TilesDugR": runtime.dug_r_count,
        "fd_50F6_0200": runtime.dug_r_x_average,
        "fd_50F6_020E": runtime.dug_r_y_average,
    }
    for name, native_value in scalar_native.items():
        if name not in oracle["ranges"]: continue
        expected_bytes = range_bytes(oracle, name)
        size = len(expected_bytes)
        actual_bytes = (int(native_value) & ((1 << (size * 8)) - 1)).to_bytes(size, "little")
        if expected_bytes != actual_bytes:
            diffs[name] = {"oracle": expected_bytes.hex(), "native": actual_bytes.hex()}
    native_events = native_callbacks(trace)
    original_events = expected_callbacks(oracle)
    if native_events != original_events:
        diffs["event_trace"] = {"oracle": original_events, "native": native_events}
    if trace.overflow:
        diffs["trace_overflow"] = True
    if diffs:
        return {"case": case.label, "input": case.metadata.get("native_port_case"),
                "oracle_return": oracle["return"], "diffs": diffs,
                "native_trace": [{"kind": int(e.kind), "args": list(e.arguments[:e.argument_count])}
                                 for e in trace.events[:trace.count]],
                "oracle_trace": oracle["trace"]}
    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--random-count", type=int, default=0)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--dirt-cases", type=int, default=128,
                        help="additional dirt/grass target cases following source suite cases")
    parser.add_argument("--report", type=Path, default=REPORT)
    args = parser.parse_args()
    suite = read_suite()
    command, library_hash = build_library()
    lib = ct.CDLL(str(LIBRARY))
    lib.sim_nest_test_run.argtypes = [ct.POINTER(SimNestTestWorld), ct.POINTER(SimRng),
                                     ct.POINTER(SimNestRuntime), ct.POINTER(SimNestRequest),
                                     ct.POINTER(SimNestTrace)]
    lib.sim_nest_test_run.restype = ct.c_int

    pair = behavior.PreparedPair("o25_3BA4_1035")
    machine = pair.original_machine
    def cases():
        index = 0
        for case in suite.make_cases("EnterNest", directed=True, random_count=args.random_count,
                                     original_helpers=("SRand1", "SRand4")):
            case.callbacks["myBeginSound"] = behavior.Callback(
                stack_words=3, handler=suite._noop, pop=0)
            yield controlled_case(case, index)
            index += 1
        for i in range(args.dirt_cases):
            tile_mode = "dirt" if i % 2 == 0 else "grass"
            case = next(suite.make_cases("EnterNest", directed=True, random_count=0,
                                         original_helpers=("SRand1", "SRand4")))
            case.callbacks["myBeginSound"] = behavior.Callback(
                stack_words=3, handler=suite._noop, pop=0)
            case.label = f"native-dig-{tile_mode}-{i:04d}"
            case.metadata["domain"].update({"initial_plane": 2 + (i & 1),
                                            "initial_x": (i % 2) * 65 + (1 if i % 4 < 2 else 64),
                                            "initial_y": (i * 7) % 64,
                                            "ant_type": 0x60 if i % 3 == 0 else 0x20,
                                            "initial_direction": i & 7,
                                            "alarm": i & 1})
            # Replace the source scenario's initial globals with this additional
            # deterministic dirt/grass case domain.
            for name, value in (("MePlane", case.metadata["domain"]["initial_plane"]),
                                ("MeLocX", case.metadata["domain"]["initial_x"]),
                                ("MeLocY", case.metadata["domain"]["initial_y"]),
                                ("fd_50F6_0496", case.metadata["domain"]["initial_direction"]),
                                ("fd_50F6_04C2", case.metadata["domain"]["ant_type"]),
                                ("fd_50F6_104E", case.metadata["domain"]["alarm"])):
                append_write(case, name, value)
            yield controlled_case(case, index + i, tile_mode)

    count = 0
    first_failure = None
    for case in cases():
        if args.limit is not None and count >= args.limit:
            break
        failure = compare_case(machine, lib, suite, case)
        count += 1
        if failure:
            first_failure = failure
            break
        if count % 1000 == 0:
            print(f"native-vs-DOS EnterNest cases={count}", flush=True)
    report = {
        "schema": "native-dos-nest-differential-v1",
        "oracle_sha256": behavior.exe.load().sha256,
        "historical_manifest_sha256": hashlib.sha256((ROOT / "layout/manifest.json").read_bytes()).hexdigest(),
        "suite": str(SUITE_PATH.relative_to(ROOT)),
        "suite_sha256": hashlib.sha256(SUITE_PATH.read_bytes()).hexdigest(),
        "runner_sha256": hashlib.sha256((TOOLS / "behavior.py").read_bytes()).hexdigest(),
        "native": {"source_sha256": hashlib.sha256((ROOT / "portable/game/simulation/nest.c").read_bytes()).hexdigest(),
                   "header_sha256": hashlib.sha256((ROOT / "portable/game/simulation/nest.h").read_bytes()).hexdigest(),
                   "adapter_sha256": hashlib.sha256((ROOT / "portable/tests/nest/native_adapter.c").read_bytes()).hexdigest(),
                   "library_sha256": library_hash, "build_command": command},
        "case_generator_domain": "archived spider_nest EnterNest cases plus dirt/grass overrides; original SRand1/SRand4 helpers execute",
        "executed": count,
        "random_count_requested": args.random_count,
        "dirt_cases_requested": args.dirt_cases,
        "mismatches": int(first_failure is not None),
        "first_mismatch": first_failure,
        "status": "MISMATCH" if first_failure else "PASS",
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "executed": count,
                      "report": str(args.report), "mismatch": first_failure}, indent=2))
    return int(first_failure is not None)


if __name__ == "__main__":
    raise SystemExit(main())
