#!/usr/bin/env python3
"""Compare native DoAntMoveY against a fresh execution of frozen DOS S25."""
from __future__ import annotations

import argparse
import ctypes as ct
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[3]
TOOLS = ROOT / "tools"
LIBRARY = ROOT / "build/portable/yellow.dll"
GCC = Path("C:/msys64/mingw64/bin/gcc.exe")
sys.path.insert(0, str(TOOLS))
import behavior  # noqa: E402
import exe  # noqa: E402
import functions  # noqa: E402


class SimWorldTiles(ct.Structure):
    _fields_ = [("surface", (ct.c_uint8 * 64) * 128),
                ("nest_b", (ct.c_uint8 * 64) * 64),
                ("nest_r", (ct.c_uint8 * 64) * 64),
                ("terrain_set", ct.c_int16)]


class SimAntList(ct.Structure):
    _fields_ = [(name, ct.c_uint8 * 1001) for name in
                ("x", "y", "mode", "type", "state")]
    _fields_ += [("count", ct.c_int16)]


class SimSmallAntList(ct.Structure):
    _fields_ = [(name, ct.c_uint8 * 501) for name in
                ("x", "y", "mode", "type", "state")]
    _fields_ += [("count", ct.c_int16)]


class SimYellowWorld(ct.Structure):
    _fields_ = [
        ("tiles", SimWorldTiles), ("exit_b", (ct.c_uint8 * 64) * 64),
        ("exit_r", (ct.c_uint8 * 64) * 64),
        ("life_a", (ct.c_uint8 * 64) * 128),
        ("life_b", (ct.c_uint8 * 64) * 64),
        ("life_r", (ct.c_uint8 * 64) * 64),
        ("hole_b", ct.c_uint8 * 64), ("hole_r", ct.c_uint8 * 64),
        ("ants_a", SimAntList), ("ants_b", SimSmallAntList),
        ("ants_r", SimSmallAntList),
        ("current_ant_plane", ct.c_int16), ("me_x", ct.c_int16),
        ("me_y", ct.c_int16), ("me_type", ct.c_int16),
        ("me_direction", ct.c_int16), ("me_health", ct.c_int16),
        ("health_warning_threshold", ct.c_int16),
        ("health_warning", ct.c_uint8), ("health_death", ct.c_uint8),
        ("health_force_full", ct.c_uint8), ("_padding", ct.c_uint8),
        ("source_counter_0472", ct.c_uint32),
    ]


class SimRng(ct.Structure):
    _fields_ = [("s_state", ct.c_uint16), ("c_state", ct.c_uint32)]


class SimGridPos(ct.Structure):
    _fields_ = [("x", ct.c_int16), ("y", ct.c_int16)]


class SimNestRuntime(ct.Structure):
    _fields_ = [(name, ct.c_int16) for name in
                ("alarm_drop_state", "alarm_indicator", "theme_index")]
    _fields_ += [("theme_last_tick", ct.c_int32)]
    _fields_ += [(name, ct.c_int16) for name in
                ("invalidate_right", "invalidate_bottom")]
    _fields_ += [(name, ct.c_int32) for name in
                ("dug_b_x_sum", "dug_b_y_sum", "dug_r_x_sum", "dug_r_y_sum")]
    _fields_ += [(name, ct.c_int16) for name in (
        "dug_b_count", "dug_r_count", "dug_b_x_average", "dug_b_y_average",
        "dug_r_x_average", "dug_r_y_average", "entrance_b_surface_x",
        "entrance_b_surface_y", "entrance_r_surface_x", "entrance_r_surface_y",
        "entrance_b_nest_x", "entrance_b_nest_y", "entrance_r_nest_x",
        "entrance_r_nest_y")]


class SimYellowState(ct.Structure):
    _fields_ = [(name, ct.c_int16) for name in (
        "move_enabled", "movement_mode", "target_list", "target_index",
        "caste_mask", "target_plane", "target_x", "target_y", "previous_x",
        "previous_y", "rotation", "preferred_direction", "map_plane",
        "health_tick_count", "carried_food", "player_caste", "alarm_drop_state",
        "movement_count", "current_penalty", "target_mode_active",
        "target_window_open", "map_warning_enabled", "overlay_underfoot",
        "food_motion_gate", "food_stock_mode", "food_stock", "message_resource",
        "sound_disabled", "path_delay")]
    _fields_ += [("nest_ticks", ct.c_int32 * 2), ("nest_tick_count", ct.c_uint8),
                 ("_padding", ct.c_uint8), ("landmark_02A4", SimGridPos),
                 ("landmark_02A8", SimGridPos), ("landmark_02AC", SimGridPos),
                 ("landmark_02B0", SimGridPos)]


class SimTileQuery(ct.Structure):
    _fields_ = [(name, ct.c_int16) for name in
                ("plane", "x", "y", "from_plane", "from_x", "from_y", "digging", "result")]


class SimMoveTrace(ct.Structure):
    _fields_ = [("tile_query_count", ct.c_uint16), ("tile_queries", SimTileQuery * 8)]


class SimNestEvent(ct.Structure):
    _fields_ = [("kind", ct.c_uint16), ("argument_count", ct.c_uint16),
                ("arguments", ct.c_int32 * 6)]


class SimNestTrace(ct.Structure):
    _fields_ = [("count", ct.c_uint16), ("overflow", ct.c_uint8),
                ("events", SimNestEvent * 256)]


class SimYellowEvent(ct.Structure):
    _fields_ = [("kind", ct.c_uint16), ("argument_count", ct.c_uint16),
                ("arguments", ct.c_int32 * 6)]


class SimYellowTrace(ct.Structure):
    _fields_ = [("count", ct.c_uint16), ("overflow", ct.c_uint8),
                ("result", ct.c_int16), ("missing_service", ct.c_int16),
                ("movement", SimMoveTrace), ("nest", SimNestTrace),
                ("events", SimYellowEvent * 64)]


def original_machine():
    row = functions.get("DoAntMoveY")
    pair = SimpleNamespace(function=row,
        vectors={exe.MANAGER_SEG * 16 + v.offset: v for v in exe.load().vectors},
        delegate={})
    return behavior.Machine(pair)


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
    lib.sim_yellow_test_run.argtypes = [ct.POINTER(SimYellowWorld), ct.POINTER(SimRng),
        ct.POINTER(SimNestRuntime), ct.POINTER(SimYellowState), ct.POINTER(SimYellowTrace)]
    lib.sim_yellow_test_run.restype = ct.c_int
    return lib, command, hashlib.sha256(LIBRARY.read_bytes()).hexdigest()


def word_write(name, value, size=2):
    data = int(value & ((1 << (size * 8)) - 1)).to_bytes(size, "little")
    return behavior.symbol_address(name), data


def map_write(name, cells):
    return behavior.symbol_address(name), cells


def write_grid(name, cells, width, height):
    out = bytearray(width * height)
    for x, y, value in cells:
        out[x * height + y] = value & 0xff
    return behavior.symbol_address(name), bytes(out)


def case_for(seed, mode, x, y, goal_x, goal_y, terrain=0, obstacles=(),
             occupied=(), ant_type=0x10, move_count=0, path_delay=-1,
             plane=1, hole_b_entries=(), hole_r_entries=(), tick_start=7162,
             theme_last=0, theme_index=0):
    import random
    rng = random.Random(seed)
    surface = bytearray(128 * 64)
    nest_b = bytearray(64 * 64)
    nest_r = bytearray(64 * 64)
    active_map = surface if plane == 1 else nest_b if plane == 2 else nest_r
    for ox, oy, tile in obstacles:
        active_map[ox * 64 + oy] = tile
    life = bytearray(128 * 64)
    life[x * 64 + y] = 0xff
    for ox, oy, value in occupied:
        life[ox * 64 + oy] = value
    life_b = bytearray(64 * 64)
    life_r = bytearray(64 * 64)
    active_life = life if plane == 1 else life_b if plane == 2 else life_r
    active_life[x * 64 + y] = 0xff
    if plane != 1:
        life[x * 64 + y] = 0
    callbacks = {
        name: behavior.Callback(stack_words=words, handler=lambda machine, args: None)
        for name, words in (("DoEditUpdateDraw", 0), ("f_015B_06A2", 0),
            ("f_00DF_00E8", 3), ("myBeginSound", 3),
            ("o22_39C7_07FD", 3), ("o22_39C7_0D21", 1),
            ("myBeginSong", 2), ("EditMessage", 3))
    }
    def tick_count(machine, _args):
        tick = (machine.state.get("tick", 0) + 37) & 0xffffffff
        machine.state["tick"] = tick
        machine.state.setdefault("tick_results", []).append(tick)
        return tick & 0xffff, tick >> 16
    callbacks["TickCount"] = behavior.Callback(stack_words=0, handler=tick_count)
    writes = [
        word_write("fd_50F6_0AA0", 1), word_write("fd_50F6_0A8E", mode),
        word_write("MePlane", plane), word_write("MeLocX", x), word_write("MeLocY", y),
        word_write("fd_50F6_04C2", ant_type), word_write("fd_50F6_0496", 0),
        word_write("fd_50F6_0AF8", 1), word_write("fd_50F6_0AD6", goal_x),
        word_write("fd_50F6_0AE8", goal_y), word_write("fd_50F6_0AB6", (x + 17) & 127),
        word_write("fd_50F6_0AC6", (y + 19) & 63), word_write("fd_50F6_0EFA", seed & 7),
        word_write("fd_50F6_0EF8", (seed >> 3) & 7), word_write("fd_50F6_0D6C", path_delay),
        word_write("fd_50F6_0C3E", move_count), word_write("MeHealth", 63),
        word_write("fd_50F6_0FBA", 45), word_write("fd_3D57_0C16", 0),
        word_write("fd_50F6_104E", 0), word_write("fd_50F6_04C4", 0),
        word_write("fd_50F6_04E2", 0), word_write("MapPlane", plane),
        word_write("TERRAINset", terrain), word_write("fd_50F6_0F24", 0),
        word_write("fd_3D57_07A8", 0), word_write("fd_50F6_08DA", 2),
        word_write("fd_50F6_07C0", 0), word_write("fd_50F6_084E", 0),
        word_write("fd_50F6_08E2", goal_x), word_write("fd_50F6_09F0", goal_y),
        word_write("fd_3D57_0C24", 0), word_write("fd_3D57_0C18", 0),
        word_write("fd_50F6_10BE", 0),
        word_write("fd_50F6_0214", theme_last, 4),
        word_write("fd_50F6_0228", theme_index),
        map_write("HoleMapB", bytes(64)), map_write("HoleMapR", bytes(64)),
        word_write("g_8BA2", 0xbeef),
        map_write("MapA", bytes(surface)), map_write("MapB", bytes(nest_b)),
        map_write("MapR", bytes(nest_r)), map_write("LifeA", bytes(life)),
        map_write("LifeB", bytes(life_b)), map_write("LifeR", bytes(life_r)),
        map_write("ExitMapB", bytes(64 * 64)), map_write("ExitMapR", bytes(64 * 64)),
        word_write("TERRAINset", terrain),
    ]
    if mode >= 3:
        target_x, target_y = (x + 7) % 128, (y + 9) % 64
        if plane != 1:
            target_x = (x + 7) % 64
        target_type = 0x18
        caste_mask = 0x10 if mode == 4 else 0
        for i, (address, data) in enumerate(writes):
            if address == behavior.symbol_address("fd_50F6_084E"):
                writes[i] = (address, int(caste_mask).to_bytes(2, "little"))
                break
        active_life[target_x * 64 + target_y] = target_type
        # Replace the previous active-life image after inserting the target ant.
        active_life_write = ("LifeA" if plane == 1 else "LifeB" if plane == 2 else "LifeR")
        for i, (address, data) in enumerate(writes):
            if address == behavior.symbol_address(active_life_write):
                writes[i] = (address, bytes(active_life))
                break
        writes.extend([
            word_write("ListIndexB", 1),
            write_grid("BlistX", [(0, 0, target_x)], 501, 1),
            write_grid("BlistY", [(0, 0, target_y)], 501, 1),
            write_grid("BlistT", [(0, 0, target_type)], 501, 1),
            write_grid("BlistM", [(0, 0, 2)], 501, 1),
            write_grid("BlistS", [(0, 0, 4)], 501, 1),
        ])
    else:
        target_x, target_y, target_type = goal_x, goal_y, 0
        caste_mask = 0
    for name, entries in (("HoleMapB", hole_b_entries), ("HoleMapR", hole_r_entries)):
        if entries:
            hole_map = bytearray(64)
            for index, value in entries:
                hole_map[index & 63] = value & 0xff
            writes.append(map_write(name, bytes(hole_map)))
    # Set the directional distance landmarks used when target plane differs.
    for name, px, py in (("fd_3D57_02A4", 5, 1), ("fd_3D57_02A8", 58, 1),
                         ("fd_3D57_02AC", 5, 62), ("fd_3D57_02B0", 58, 62)):
        writes.append((behavior.symbol_address(name),
                       int(px).to_bytes(2, "little") + int(py).to_bytes(2, "little")))
    writes.extend([word_write("fd_50F6_048C", plane),
                   word_write("fd_50F6_0A8E", mode),
                   word_write("fd_50F6_0AA0", 1)])
    observe_names = ["fd_50F6_0AA0", "fd_50F6_0A8E", "MePlane", "MeLocX", "MeLocY",
        "fd_50F6_04C2", "fd_50F6_0496", "fd_50F6_0AF8", "fd_50F6_0AD6",
        "fd_50F6_0AE8", "fd_50F6_0AB6", "fd_50F6_0AC6", "fd_50F6_0EFA",
        "fd_50F6_0EF8", "fd_50F6_0D6C", "fd_50F6_0C3E", "MeHealth",
        "fd_50F6_1044", "fd_50F6_08DA", "fd_50F6_07C0", "fd_50F6_084E",
        "fd_50F6_0228", "g_8BA2", "MapPlane"]
    observe = [behavior.Range(n, behavior.symbol_address(n), 2) for n in observe_names]
    observe.append(behavior.Range("fd_50F6_0214", behavior.symbol_address("fd_50F6_0214"), 4))
    observe += [behavior.Range(name, behavior.symbol_address(name), size) for name, size in
        (("MapA", 128 * 64), ("MapB", 64 * 64), ("MapR", 64 * 64),
         ("LifeA", 128 * 64), ("LifeB", 64 * 64), ("LifeR", 64 * 64),
         ("ExitMapB", 64 * 64), ("ExitMapR", 64 * 64),
         ("HoleMapB", 64), ("HoleMapR", 64),
         ("BlistX", 501), ("BlistY", 501), ("BlistT", 501),
         ("BlistM", 501), ("BlistS", 501), ("ListIndexB", 2))]
    case = behavior.Case(f"seed{seed:04x}-m{mode}-xy{x}-{y}-goal{goal_x}-{goal_y}",
        writes=writes, observe=observe, callbacks=callbacks, return_kind="void")
    case.metadata["input"] = {"seed": seed, "mode": mode, "pos": [x,y],
                              "goal": [goal_x,goal_y], "target_ant": [target_x,target_y,target_type],
                              "terrain": terrain, "caste_mask": caste_mask,
                              "obstacles": list(obstacles), "occupied": list(occupied),
                              "ant_type": ant_type, "move_count": move_count,
                              "plane": plane,
                              "path_delay": path_delay, "tick_start": tick_start,
                              "theme_last": theme_last, "theme_index": theme_index}
    case.state["tick"] = tick_start
    return case


def native_world(case):
    world = SimYellowWorld()
    fields = {
        "MapA": (world.tiles.surface, 128, 64), "MapB": (world.tiles.nest_b, 64, 64),
        "MapR": (world.tiles.nest_r, 64, 64), "LifeA": (world.life_a, 128, 64),
        "LifeB": (world.life_b, 64, 64), "LifeR": (world.life_r, 64, 64),
        "ExitMapB": (world.exit_b, 64, 64), "ExitMapR": (world.exit_r, 64, 64),
        "HoleMapB": (world.hole_b, 64, 1), "HoleMapR": (world.hole_r, 64, 1),
    }
    for address, data in case.writes:
        for name, (array, width, height) in fields.items():
            base = behavior.symbol_address(name)
            if base <= address and address + len(data) <= base + width * height:
                offset = address - base
                if len(data) == width * height:
                    ct.memmove(ct.addressof(array), data, len(data))
                else:
                    ct.memmove(ct.addressof(array) + offset, data, len(data))
                break
    for source_name, field_name in (("BlistX", "x"), ("BlistY", "y"),
                                    ("BlistT", "type"), ("BlistM", "mode"),
                                    ("BlistS", "state")):
        base = behavior.symbol_address(source_name)
        for address, data in case.writes:
            if base <= address and address + len(data) <= base + 501:
                ct.memmove(ct.addressof(world.ants_b) +
                           getattr(SimSmallAntList, field_name).offset + address - base,
                           data, len(data))
    count_address = behavior.symbol_address("ListIndexB")
    for address, data in case.writes:
        if address == count_address:
            world.ants_b.count = int.from_bytes(data[:2], "little", signed=True)
    domain = case.metadata["input"]
    world.tiles.terrain_set = domain["terrain"]
    world.current_ant_plane = domain["plane"]
    world.me_x, world.me_y = domain["pos"]
    world.me_type = domain["ant_type"]
    world.me_direction = 0
    world.me_health = 63
    world.health_warning_threshold = 45
    return world


def native_state(case):
    d = case.metadata["input"]
    state = SimYellowState()
    state.move_enabled = 1
    state.movement_mode = d["mode"]
    state.target_list = 2
    state.target_index = 0
    state.caste_mask = d["caste_mask"]
    state.target_plane = 1
    state.target_x, state.target_y = d["goal"]
    state.previous_x, state.previous_y = ((d["pos"][0] + 17) & 127,
                                           (d["pos"][1] + 19) & 63)
    state.rotation = d["seed"] & 7
    state.preferred_direction = (d["seed"] >> 3) & 7
    state.map_plane = d["plane"]
    state.movement_count = d["move_count"]
    state.path_delay = d["path_delay"]
    state.nest_ticks[0] = (d["tick_start"] + 37) & 0xffffffff
    state.nest_ticks[1] = (d["tick_start"] + 74) & 0xffffffff
    state.nest_tick_count = 2
    state.landmark_02A4 = SimGridPos(5, 1)
    state.landmark_02A8 = SimGridPos(58, 1)
    state.landmark_02AC = SimGridPos(5, 62)
    state.landmark_02B0 = SimGridPos(58, 62)
    return state


def native_events(trace):
    names = {1: "DoEditUpdateDraw", 2: "f_015B_06A2", 3: "f_00DF_00E8",
             4: "o22_39C7_07FD", 5: "EditMessage"}
    # The oracle hook f_00DF_00E8 is also identified by the historical
    # callback name myBeginSound.  The native intent is the same logical
    # sound request, so compare its ordered arguments under that contract.
    return [(names.get(int(e.kind), "unknown"),
             tuple(int(v) & 0xffff for v in e.arguments[:e.argument_count]))
            for e in trace.events[:trace.count]]


def scalar(data, name, signed=True):
    raw = bytes.fromhex(data["ranges"][name])
    return int.from_bytes(raw, "little", signed=signed)


def compare(machine, lib, case):
    oracle = machine.run(case)
    world = native_world(case)
    rng = SimRng(0xbeef, 0)
    nest_runtime = SimNestRuntime()
    nest_runtime.theme_last_tick = case.metadata["input"]["theme_last"]
    nest_runtime.theme_index = case.metadata["input"]["theme_index"]
    state = native_state(case)
    trace = SimYellowTrace()
    status = lib.sim_yellow_test_run(ct.byref(world), ct.byref(rng),
        ct.byref(nest_runtime), ct.byref(state), ct.byref(trace))
    if status != 0:
        return {"case": case.label, "native_status": status,
                "missing_service": trace.missing_service,
                "inputs": case.metadata["input"]}
    diffs = {}
    fields = {
        "MapA": (world.tiles.surface, 128*64), "MapB": (world.tiles.nest_b, 64*64),
        "MapR": (world.tiles.nest_r, 64*64), "LifeA": (world.life_a, 128*64),
        "LifeB": (world.life_b, 64*64), "LifeR": (world.life_r, 64*64),
        "ExitMapB": (world.exit_b, 64*64), "ExitMapR": (world.exit_r, 64*64),
        "BlistX": (world.ants_b.x, 501), "BlistY": (world.ants_b.y, 501),
        "BlistT": (world.ants_b.type, 501), "BlistM": (world.ants_b.mode, 501),
        "BlistS": (world.ants_b.state, 501),
    }
    for name, (array, size) in fields.items():
        expected = bytes.fromhex(oracle["ranges"][name])
        actual = ct.string_at(ct.addressof(array), size)
        if expected != actual:
            offset = next(i for i,(a,b) in enumerate(zip(expected,actual)) if a != b)
            diffs[name] = {"offset": offset, "oracle": expected[offset], "native": actual[offset]}
    native_scalars = {
        "MePlane": world.current_ant_plane, "MeLocX": world.me_x, "MeLocY": world.me_y,
        "fd_50F6_04C2": world.me_type, "fd_50F6_0496": world.me_direction,
        "fd_50F6_0AB6": state.previous_x, "fd_50F6_0AC6": state.previous_y,
        "fd_50F6_0EFA": state.rotation, "fd_50F6_0EF8": state.preferred_direction,
        "fd_50F6_0D6C": state.path_delay, "fd_50F6_0C3E": state.movement_count,
        "fd_50F6_0AA0": state.move_enabled, "fd_50F6_0A8E": state.movement_mode,
        "fd_50F6_0AF8": state.target_plane, "fd_50F6_0AD6": state.target_x,
        "fd_50F6_0AE8": state.target_y, "fd_50F6_08DA": state.target_list,
        "fd_50F6_07C0": state.target_index, "ListIndexB": world.ants_b.count,
        "fd_50F6_084E": state.caste_mask,
        "MeHealth": world.me_health, "fd_50F6_1044": world.health_warning,
        "g_8BA2": ct.c_int16(rng.s_state).value, "MapPlane": case.metadata["input"]["plane"],
    }
    for name, actual in native_scalars.items():
        if name in oracle["ranges"] and scalar(oracle, name) != actual:
            diffs[name] = {"oracle": scalar(oracle, name), "native": actual}
    aliases = {"myBeginSound": "f_00DF_00E8"}
    expected_events = [(aliases.get(e["name"], e["name"]), tuple(e["args"]))
        for e in oracle["trace"]
        if e["name"] in {"DoEditUpdateDraw", "f_015B_06A2", "f_00DF_00E8",
                          "myBeginSound", "o22_39C7_07FD", "o22_39C7_0D21"}]
    actual_events = native_events(trace)
    if expected_events != actual_events:
        diffs["events"] = {"oracle": expected_events, "native": actual_events}
    expected_theme = [(e["name"], tuple(e["args"])) for e in oracle["trace"]
        if e["name"] in {"TickCount", "myBeginSong"}]
    native_theme = []
    for event in trace.nest.events[:trace.nest.count]:
        if event.kind == 1:
            native_theme.append(("TickCount", ()))
        elif event.kind == 2:
            native_theme.append(("myBeginSong", tuple(int(v) & 0xffff
                for v in event.arguments[:event.argument_count])))
    if expected_theme != native_theme:
        diffs["theme_callbacks"] = {"oracle": expected_theme, "native": native_theme}
    if diffs:
        return {"case": case.label, "inputs": case.metadata["input"], "diffs": diffs,
                "oracle_trace": [(e["name"], e["args"]) for e in oracle["trace"]],
                "native_trace": actual_events}
    return None


def cases(count, seed):
    import random
    r = random.Random(seed)
    # Exercise the newly integrated exit transition before the broad movement
    # corpus. These cases cross both nest planes, queen/single-ant geometry,
    # existing and synthesized surface holes, and both sides of TryAntTheme's
    # 0x1c20 tick threshold.
    directed = []
    for plane in (2, 3):
        for x, ant_type, has_hole, tick_start in (
                (32, 0x10, True, 7162), (32, 0x60, False, 7163),
                (50, 0x10, False, 0), (50, 0x60, True, 7163)):
            kwargs = {
                "seed": seed ^ (plane << 12) ^ (x << 3) ^ ant_type ^ tick_start,
                "mode": 0, "x": x, "y": 1, "goal_x": x, "goal_y": 0,
                "plane": plane, "ant_type": ant_type, "tick_start": tick_start,
                "theme_last": 0, "theme_index": 2,
            }
            if has_hole:
                kwargs["hole_b_entries" if plane == 2 else "hole_r_entries"] = [(x, x + 3)]
            directed.append(case_for(**kwargs))
    for case in directed[:count]:
        yield case
    for i in range(max(0, count - len(directed))):
        i += len(directed)
        plane = 1 if i % 2 == 0 else 2
        x_max = 127 if plane == 1 else 63
        x = (i % 2 and r.randrange(1, x_max)) or r.choice(
            [0, 1, 2, min(63, x_max), x_max - 1, x_max])
        y = r.choice([2, 3, 30, 31, 62, 63]) if i % 3 == 0 else r.randrange(2, 64)
        mode = i % 5
        angle = r.randrange(8)
        dx = (0,1,1,1,0,-1,-1,-1)[angle]
        dy = (-1,-1,0,1,1,1,0,-1)[angle]
        distance = r.randrange(3, 10)
        goal_x = min(x_max, max(0, x + dx * distance))
        goal_y = min(63, max(0, y + dy * distance))
        if mode == 1 and max(abs(goal_x - x), abs(goal_y - y)) <= 1:
            if x >= 3: goal_x, goal_y = x - 3, y
            elif x <= 124: goal_x, goal_y = x + 3, y
            elif y >= 3: goal_x, goal_y = x, y - 3
            else: goal_x, goal_y = x, y + 3
        obstacles = []
        occupied = []
        for _ in range(r.randrange(0, 6)):
            ox, oy = r.randrange(x_max + 1), r.randrange(64)
            obstacles.append((ox, oy, r.choice([0x80, 0x90, 0xa0, 0xff])))
        for _ in range(r.randrange(0, 4)):
            ox, oy = r.randrange(x_max + 1), r.randrange(64)
            if (ox, oy) != (x, y): occupied.append((ox, oy, r.choice([0x18, 0x28, 0x48, 0x60])))
        yield case_for(seed + i, mode, x, y, goal_x, goal_y,
                       terrain=i & 1, obstacles=obstacles, occupied=occupied,
                       ant_type=r.choice([0x08,0x10,0x20,0x30,0x40,0x60]),
                       move_count=i & 1, path_delay=r.choice([-2,-1,0,1,4]),
                       plane=plane)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=100)
    parser.add_argument("--seed", type=lambda s: int(s, 0), default=0xD04A)
    parser.add_argument("--report", type=Path, default=ROOT / "build/portable/yellow-dos-diff.json")
    args = parser.parse_args()
    machine = original_machine()
    lib, command, library_hash = build_native()
    passed = 0
    mismatch = None
    unsupported = []
    for case in cases(args.count, args.seed):
        result = compare(machine, lib, case)
        if result and "native_status" in result:
            unsupported.append(result)
            if len(unsupported) == 1:
                mismatch = result
                break
        elif result:
            mismatch = result
            break
        passed += 1
        if passed % 100 == 0:
            print(f"native-vs-DOS DoAntMoveY cases={passed}", flush=True)
    source_paths = ["portable/game/simulation/yellow.c", "portable/game/simulation/yellow.h",
                    "portable/game/simulation/nest.c", "portable/game/simulation/exit_nest.c",
                    "portable/game/simulation/exit_nest.h", "portable/game/simulation/movement.c",
                    "portable/game/simulation/ants.c", "portable/game/simulation/rng.c",
                    "portable/game/simulation/nest.h", "portable/game/simulation/movement.h",
                    "portable/game/simulation/ants.h", "portable/game/simulation/rng.h",
                    "portable/game/state/world.h", "portable/tests/yellow/native_adapter.c",
                    "portable/tests/yellow/native_adapter.h", "portable/tests/yellow/run_dos_diff.py"]
    report = {
        "schema": "native-dos-doantmovey-differential-v1",
        "oracle_sha256": exe.load().sha256,
        "historical_manifest_sha256": hashlib.sha256((ROOT / "layout/manifest.json").read_bytes()).hexdigest(),
        "target": {"name": "DoAntMoveY", "address": "S25:3BA4:0008"},
        "executed": passed + (1 if mismatch else 0), "matched": passed,
        "unmatched": int(mismatch is not None), "first_unmatched": mismatch,
        "unsupported_cases": unsupported,
        "domain": {"count_requested": args.count, "seed": args.seed,
                   "movement_modes": [0,1,2,3,4], "planes": [1,2],
                   "fixture_description": "random valid obstacles/occupied Life maps; surface and B-nest planes"},
        "native": {"library_sha256": library_hash, "build_command": command,
                   "source_sha256": {p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
                                     for p in source_paths}},
        "status": "PASS" if mismatch is None else "MISMATCH_OR_UNSUPPORTED",
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "matched": passed,
                      "unmatched": report["unmatched"], "report": str(args.report),
                      "first": mismatch}, indent=2))
    return int(mismatch is not None)


if __name__ == "__main__":
    raise SystemExit(main())
