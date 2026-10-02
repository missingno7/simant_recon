#!/usr/bin/env python3
"""Differentially execute ExitNest in DOS and its typed native transition."""
from __future__ import annotations

import ctypes as ct
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "portable/tests/yellow"))
import behavior  # noqa: E402
import exe  # noqa: E402
import functions  # noqa: E402
import run_dos_diff as yd  # noqa: E402

LIBRARY = ROOT / "build/portable/exit_nest.dll"
GCC = Path("C:/msys64/mingw64/bin/gcc.exe")


class SimExitNestContext(ct.Structure):
    _fields_ = [(n, ct.c_int16) for n in (
        "target_plane",)] + [("target", yd.SimGridPos), ("previous", yd.SimGridPos)] + [
        (n, ct.c_int16) for n in (
            "movement_mode", "rotation", "preferred_direction", "map_plane")
    ] + [("tick_values", ct.c_int32 * 2), ("tick_count", ct.c_uint8)]


def build_native():
    LIBRARY.parent.mkdir(parents=True, exist_ok=True)
    command = [str(GCC), "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror", "-shared",
        "-I", str(ROOT / "portable/game/simulation"),
        "-I", str(ROOT / "portable/game/state"),
        "-I", str(ROOT / "portable/tests/yellow"),
        str(ROOT / "portable/tests/yellow/native_adapter.c"),
        str(ROOT / "portable/game/simulation/yellow.c"),
        str(ROOT / "portable/game/simulation/exit_nest.c"),
        str(ROOT / "portable/game/simulation/nest.c"),
        str(ROOT / "portable/game/simulation/ants.c"),
        str(ROOT / "portable/game/simulation/movement.c"),
        str(ROOT / "portable/game/simulation/rng.c"), "-o", str(LIBRARY)]
    subprocess.run(command, check=True, cwd=ROOT)
    lib = ct.CDLL(str(LIBRARY))
    lib.sim_exit_nest_test_run.argtypes = [ct.POINTER(yd.SimYellowWorld),
        ct.POINTER(yd.SimRng), ct.POINTER(yd.SimNestRuntime),
        ct.POINTER(SimExitNestContext), ct.POINTER(yd.SimMoveTrace),
        ct.POINTER(yd.SimNestTrace)]
    lib.sim_exit_nest_test_run.restype = ct.c_int
    return lib, command, hashlib.sha256(LIBRARY.read_bytes()).hexdigest()


def original_machine():
    pair = SimpleNamespace(function=functions.get("ExitNest"),
        vectors={exe.MANAGER_SEG * 16 + v.offset: v for v in exe.load().vectors},
        delegate={})
    return behavior.Machine(pair)


def tick_count(machine, _args):
    tick = (machine.state.get("tick", 0) + 37) & 0xffffffff
    machine.state["tick"] = tick
    machine.state.setdefault("tick_results", []).append(tick)
    return tick & 0xffff, tick >> 16


def case_for(i, *, current_plane=2, x=32, ant_type=0x10, target=(35, 31),
             target_plane=1, terrain=0, obstacles=(), theme_last=0,
             theme_index=0, tick_start=7162, seed=0xbeef,
             preexisting_hole=True):
    hole = bytearray(64)
    if preexisting_hole:
        hole[x & 63] = 35
    surface = bytearray(128 * 64)
    for ox, oy, tile in obstacles:
        surface[ox * 64 + oy] = tile
    nest_b = bytearray(64 * 64)
    nest_r = bytearray(64 * 64)
    life_b = bytearray(64 * 64)
    life_r = bytearray(64 * 64)
    if current_plane == 2:
        life_b[x * 64] = 0xff
    else:
        life_r[x * 64] = 0xff
    callbacks = {
        "TickCount": behavior.Callback(stack_words=0, handler=tick_count),
        "myBeginSong": behavior.Callback(stack_words=2,
            handler=lambda _machine, _args: None),
    }
    writes = [
        yd.word_write("MePlane", current_plane), yd.word_write("MeLocX", x),
        yd.word_write("MeLocY", 0), yd.word_write("fd_50F6_04C2", ant_type),
        yd.word_write("fd_50F6_0496", 4), yd.word_write("TERRAINset", terrain),
        yd.word_write("fd_50F6_0AF8", target_plane),
        yd.word_write("fd_50F6_0AD6", target[0]), yd.word_write("fd_50F6_0AE8", target[1]),
        yd.word_write("fd_50F6_0A8E", 0),
        yd.word_write("fd_50F6_0AB6", 31), yd.word_write("fd_50F6_0AC6", 1),
        yd.word_write("fd_50F6_0EFA", 0), yd.word_write("fd_50F6_0EF8", 2),
        yd.word_write("fd_50F6_0214", theme_last, 4),
        yd.word_write("fd_50F6_0228", theme_index),
        yd.word_write("g_8BA2", seed),
        yd.map_write("MapA", bytes(surface)), yd.map_write("MapB", bytes(nest_b)),
        yd.map_write("MapR", bytes(nest_r)), yd.map_write("LifeA", bytes(128 * 64)),
        yd.map_write("LifeB", bytes(life_b)), yd.map_write("LifeR", bytes(life_r)),
        yd.map_write("ExitMapB", bytes(64 * 64)), yd.map_write("ExitMapR", bytes(64 * 64)),
        yd.map_write("HoleMapB", bytes(hole)), yd.map_write("HoleMapR", bytes(64)),
    ]
    for name, px, py in (("fd_3D57_02A4", 35, 0), ("fd_3D57_02A8", 50, 0),
                         ("fd_3D57_02AC", 35, 32), ("fd_3D57_02B0", 50, 32)):
        writes.append((behavior.symbol_address(name),
                       px.to_bytes(2, "little") + py.to_bytes(2, "little")))
    observed = [
        ("MapA", 128 * 64), ("MapB", 64 * 64), ("MapR", 64 * 64),
        ("LifeA", 128 * 64), ("LifeB", 64 * 64), ("LifeR", 64 * 64),
        ("ExitMapB", 64 * 64), ("ExitMapR", 64 * 64), ("HoleMapB", 64),
        ("HoleMapR", 64), ("MePlane", 2), ("MeLocX", 2), ("MeLocY", 2),
        ("fd_50F6_04C2", 2), ("fd_50F6_0496", 2),
        ("fd_50F6_0AF8", 2), ("fd_50F6_0AD6", 2), ("fd_50F6_0AE8", 2),
        ("fd_50F6_0EFA", 2), ("fd_50F6_0EF8", 2),
        ("fd_50F6_0214", 4), ("fd_50F6_0228", 2), ("g_8BA2", 2),
        ("fd_3D57_02A4", 4), ("fd_3D57_02A8", 4),
        ("fd_3D57_02AC", 4), ("fd_3D57_02B0", 4),
    ]
    case = behavior.Case(f"exit-nest-{i:04d}", writes=writes,
        observe=[behavior.Range(n, behavior.symbol_address(n), size) for n, size in observed],
        callbacks=callbacks, return_kind="void")
    case.state["tick"] = tick_start
    case.metadata["input"] = {"plane": current_plane, "x": x, "type": ant_type,
        "target_plane": target_plane, "target": list(target), "terrain": terrain,
        "obstacles": list(obstacles), "theme_last": theme_last,
        "theme_index": theme_index, "tick_start": tick_start, "seed": seed}
    case.metadata["native_ticks"] = [(tick_start + 37) & 0xffffffff,
                                      (tick_start + 74) & 0xffffffff]
    return case


def native_call(lib, case):
    world = yd.SimYellowWorld()
    fields = {
        "MapA": (world.tiles.surface, 128 * 64),
        "MapB": (world.tiles.nest_b, 64 * 64),
        "MapR": (world.tiles.nest_r, 64 * 64),
        "LifeA": (world.life_a, 128 * 64),
        "LifeB": (world.life_b, 64 * 64),
        "LifeR": (world.life_r, 64 * 64),
        "ExitMapB": (world.exit_b, 64 * 64),
        "ExitMapR": (world.exit_r, 64 * 64),
        "HoleMapB": (world.hole_b, 64), "HoleMapR": (world.hole_r, 64),
    }
    for name, (array, size) in fields.items():
        base = behavior.symbol_address(name)
        for address, data in case.writes:
            if base <= address and address + len(data) <= base + size:
                ct.memmove(ct.addressof(array) + address - base, data, len(data))
    world.current_ant_plane = case.metadata["input"]["plane"]
    world.me_x = case.metadata["input"]["x"]
    world.me_y = 0
    world.me_type = case.metadata["input"]["type"]
    world.me_direction = 4
    world.tiles.terrain_set = case.metadata["input"]["terrain"]
    rng = yd.SimRng(case.metadata["input"]["seed"], 0)
    runtime = yd.SimNestRuntime()
    runtime.theme_last_tick = case.metadata["input"]["theme_last"]
    runtime.theme_index = case.metadata["input"]["theme_index"]
    runtime.entrance_b_nest_x, runtime.entrance_b_nest_y = 35, 0
    runtime.entrance_b_surface_x, runtime.entrance_b_surface_y = 35, 32
    runtime.entrance_r_nest_x, runtime.entrance_r_nest_y = 50, 0
    runtime.entrance_r_surface_x, runtime.entrance_r_surface_y = 50, 32
    context = SimExitNestContext()
    context.target_plane = case.metadata["input"]["target_plane"]
    context.target = yd.SimGridPos(*case.metadata["input"]["target"])
    context.previous = yd.SimGridPos(31, 1)
    context.movement_mode = 0
    context.rotation = 0
    context.preferred_direction = 2
    context.map_plane = 2
    context.tick_values[0], context.tick_values[1] = case.metadata["native_ticks"]
    context.tick_count = 2
    move_trace, nest_trace = yd.SimMoveTrace(), yd.SimNestTrace()
    status = lib.sim_exit_nest_test_run(ct.byref(world), ct.byref(rng),
        ct.byref(runtime), ct.byref(context), ct.byref(move_trace), ct.byref(nest_trace))
    return status, world, rng, runtime, context, move_trace, nest_trace


def compare(machine, lib, case):
    original = machine.run(case)
    status, world, rng, runtime, context, move_trace, nest_trace = native_call(lib, case)
    if status:
        return {"case": case.label, "native_status": status, "input": case.metadata["input"]}
    diffs = {}
    arrays = {
        "MapA": (world.tiles.surface, 128 * 64), "MapB": (world.tiles.nest_b, 64 * 64),
        "MapR": (world.tiles.nest_r, 64 * 64), "LifeA": (world.life_a, 128 * 64),
        "LifeB": (world.life_b, 64 * 64), "LifeR": (world.life_r, 64 * 64),
        "ExitMapB": (world.exit_b, 64 * 64), "ExitMapR": (world.exit_r, 64 * 64),
        "HoleMapB": (world.hole_b, 64), "HoleMapR": (world.hole_r, 64),
    }
    for name, (array, size) in arrays.items():
        expected = bytes.fromhex(original["ranges"][name])
        actual = ct.string_at(ct.addressof(array), size)
        if expected != actual:
            at = next(j for j, (a, b) in enumerate(zip(expected, actual)) if a != b)
            diffs[name] = {"offset": at, "oracle": expected[at], "native": actual[at]}
    scalars = {
        "MePlane": world.current_ant_plane, "MeLocX": world.me_x,
        "MeLocY": world.me_y, "fd_50F6_04C2": world.me_type,
        "fd_50F6_0496": world.me_direction, "fd_50F6_0214": runtime.theme_last_tick,
        "fd_50F6_0228": runtime.theme_index, "g_8BA2": rng.s_state,
        "fd_3D57_02A4": (runtime.entrance_b_nest_x, runtime.entrance_b_nest_y),
        "fd_3D57_02AC": (runtime.entrance_b_surface_x, runtime.entrance_b_surface_y),
        "fd_3D57_02A8": (runtime.entrance_r_nest_x, runtime.entrance_r_nest_y),
        "fd_3D57_02B0": (runtime.entrance_r_surface_x, runtime.entrance_r_surface_y),
    }
    for name, value in scalars.items():
        expected = bytes.fromhex(original["ranges"][name])
        if isinstance(value, tuple):
            actual = b"".join((int(v) & 0xffff).to_bytes(2, "little") for v in value)
            if expected != actual:
                diffs[name] = {"oracle": expected.hex(), "native": actual.hex()}
            continue
        actual = (int(value) & ((1 << (len(expected) * 8)) - 1)).to_bytes(len(expected), "little")
        if expected != actual:
            diffs[name] = {"oracle": expected.hex(), "native": actual.hex()}
    oracle_callbacks = [(item["name"], tuple(item["args"]))
        for item in original["trace"] if item["name"] in {"TickCount", "myBeginSong"}]
    native_callbacks = []
    for event in nest_trace.events[:nest_trace.count]:
        if event.kind == 1:
            native_callbacks.append(("TickCount", ()))
        elif event.kind == 2:
            native_callbacks.append(("myBeginSong", tuple(event.arguments[:event.argument_count])))
    if oracle_callbacks != native_callbacks:
        diffs["callbacks"] = {"oracle": oracle_callbacks, "native": native_callbacks}
    if diffs:
        return {"case": case.label, "input": case.metadata["input"], "diffs": diffs,
                "oracle_callbacks": oracle_callbacks, "native_callbacks": native_callbacks}
    return None


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=128)
    parser.add_argument("--report", type=Path,
                        default=ROOT / "build/portable/exit-nest-dos-diff.json")
    args = parser.parse_args()
    machine = original_machine()
    lib, command, library_hash = build_native()
    mismatches = []
    matched = 0
    for i in range(args.count):
        # Two sides of the documented 7,200-tick theme threshold, then vary
        # turning obstacles and queen movement stride deterministically.
        start_tick = (7162, 7163, 0, 10000)[i % 4]
        plane = 2 if i % 2 == 0 else 3
        x = 32 if plane == 2 else 50
        target = ((35 + i % 7), 31 + (i % 3))
        ant_type = 0x60 if i % 5 == 0 else 0x10
        obstacles = [] if i % 4 < 2 else [(35, 31, 0x55), (36, 32, 0x50)]
        case = case_for(i, current_plane=plane, x=x, ant_type=ant_type,
                        target=target, terrain=i & 1, theme_last=0,
                        theme_index=i % 3, tick_start=start_tick,
                        obstacles=obstacles, preexisting_hole=(i % 8 != 7))
        result = compare(machine, lib, case)
        if result:
            mismatches.append(result)
            break
        matched += 1
        if matched % 50 == 0:
            print(f"ExitNest native-vs-DOS cases={matched}", flush=True)
    sources = ["portable/game/simulation/exit_nest.c", "portable/game/simulation/exit_nest.h",
        "portable/game/simulation/nest.c", "portable/game/simulation/ants.c",
        "portable/game/simulation/movement.c", "portable/game/simulation/rng.c",
        "portable/tests/yellow/native_adapter.c", "portable/tests/yellow/run_exit_nest_diff.py"]
    report = {"schema": "native-dos-exit-nest-differential-v1",
        "oracle_sha256": exe.load().sha256,
        "historical_manifest_sha256": hashlib.sha256((ROOT / "layout/manifest.json").read_bytes()).hexdigest(),
        "target": {"name": "ExitNest", "address": "S25:3BA4:114E"},
        "executed": matched + len(mismatches), "matched": matched,
        "unmatched": len(mismatches), "first_unmatched": mismatches[0] if mismatches else None,
        "domain": {"count_requested": args.count, "theme_ticks": "controlled TickCount; 7199/7200 boundary",
            "planes": [2, 3], "hole_map": "preexisting and generated entrances", "ant_types": [0x10, 0x60]},
        "native": {"library_sha256": library_hash, "build_command": command,
            "source_sha256": {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in sources}},
        "status": "PASS" if not mismatches else "MISMATCH"}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "matched": matched,
        "mismatch": report["first_unmatched"], "report": str(args.report)}, indent=2))
    return int(bool(mismatches))


if __name__ == "__main__":
    raise SystemExit(main())
