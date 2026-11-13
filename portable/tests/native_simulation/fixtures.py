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
        word_write("MeMoveMe", 1), word_write("MeCmd", mode),
        word_write("MePlane", plane), word_write("MeLocX", x), word_write("MeLocY", y),
        word_write("MeType", ant_type), word_write("MeDir", 0),
        word_write("MeGoalPlane", 1), word_write("MeGoalX", goal_x),
        word_write("MeGoalY", goal_y), word_write("MeLastX", (x + 17) & 127),
        word_write("MeLastY", (y + 19) & 63), word_write("MeCrazyRot", seed & 7),
        word_write("MeCrazyDir", (seed >> 3) & 7), word_write("MeCrazyCnt", path_delay),
        word_write("MeSteps", move_count), word_write("MeHealth", 63),
        word_write("MeWarnHealth", 45), word_write("NeverHungry", 0),
        word_write("MeDropAlarm", 0), word_write("MeScent", 0),
        word_write("MeColor", 0), word_write("MapPlane", plane),
        word_write("TERRAINset", terrain), word_write("fd_50F6_0F24", 0),
        word_write("OptionStates", 0), word_write("MeTargLifePlane", 2),
        word_write("MeTargIndex", 0), word_write("MeTargLife", 0),
        word_write("MeTargLifeX", goal_x), word_write("MeTargLifeY", goal_y),
        word_write("MeNestStarted", 0), word_write("AlwaysHealthy", 0),
        word_write("fd_50F6_10BE", 0),
        word_write("LastThemeTime", theme_last, 4),
        word_write("LastThemeSong", theme_index),
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
            if address == behavior.symbol_address("MeTargLife"):
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
    for name, px, py in (("LastNewExitB", 5, 1), ("LastNewExitR", 58, 1),
                         ("LastNewHoleB", 5, 62), ("LastNewHoleR", 58, 62)):
        writes.append((behavior.symbol_address(name),
                       int(px).to_bytes(2, "little") + int(py).to_bytes(2, "little")))
    writes.extend([word_write("fd_50F6_048C", plane),
                   word_write("MeCmd", mode),
                   word_write("MeMoveMe", 1)])
    observe_names = ["MeMoveMe", "MeCmd", "MePlane", "MeLocX", "MeLocY",
        "MeType", "MeDir", "MeGoalPlane", "MeGoalX",
        "MeGoalY", "MeLastX", "MeLastY", "MeCrazyRot",
        "MeCrazyDir", "MeCrazyCnt", "MeSteps", "MeHealth",
        "MeWantFood", "MeTargLifePlane", "MeTargIndex", "MeTargLife",
        "LastThemeSong", "g_8BA2", "MapPlane"]
    observe = [behavior.Range(n, behavior.symbol_address(n), 2) for n in observe_names]
    observe.append(behavior.Range("LastThemeTime", behavior.symbol_address("LastThemeTime"), 4))
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

