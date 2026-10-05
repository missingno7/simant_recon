"""Bounded DOS DoAntMoveY fixture writes, independent of retired native models."""
import behavior

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

