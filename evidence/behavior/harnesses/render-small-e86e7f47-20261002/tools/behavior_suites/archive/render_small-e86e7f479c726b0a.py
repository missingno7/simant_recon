"""Bounded original-DOS differential contracts for small rendering routines.

All candidate code is compiled from retained whole-module seeds and runs beside
the hash-locked EXE through tools.behavior.PreparedPair.  Graphics operations
are modeled only at named host boundaries; pointer arguments are projected into
semantic rectangles/points before comparison.
"""
from __future__ import annotations

import argparse
import json
import random
import shutil
import struct
import sys
import time
from pathlib import Path
import importlib.util

ROOT = next(p for p in Path(__file__).resolve().parents
            if (p / "tools" / "behavior.py").is_file() and
               (p / "layout" / "manifest.json").is_file())
SUITE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "tools"))
import behavior

def _load_archived_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

behavior_ledger = _load_archived_module(
    "behavior_ledger", SUITE_DIR / "deps" / "behavior_ledger.py")
memory_suite = _load_archived_module(
    "render_small_pinned_memory_fixture",
    SUITE_DIR / "deps" / "behavior_suites" / "memory.py")
memory_suite.ROOT = ROOT

SUITE = "render_small_v1"
OUT = ROOT / "build/workers/behavior_render_small"
BALLOON_TEXT = (0xA800, 0x0100)
BALLOON_MESSAGE = b"A deterministic message balloon"


def _w(v):
    return struct.pack("<H", v & 0xffff)


def _range(name, size):
    return behavior.Range(name, behavior.symbol_address(name), size)


def _callback(stack_words=0, handler=None, regs=(), project=None):
    return behavior.Callback(stack_words=stack_words, handler=handler,
                             register_args=tuple(regs), pop=0, project=project)


def _noop(machine, args):
    return None


def _window(machine, args):
    return 1 if machine.state.get("window_open", True) else 0


def _capture_rect(machine, args):
    off, seg, width = args
    at = seg * 16 + off
    raw = machine.read(at, 8)
    rect = list(struct.unpack("<hhhh", raw))
    return [rect, width]


def _capture_quad(machine, args):
    off, seg, a, b = args
    at = seg * 16 + off
    points = [list(struct.unpack("<hh", machine.read(at + i * 4, 4))) for i in range(4)]
    return [points, a, b]


def _map_cursor_case(label, xorigin, yorigin, width, height, sx, sy,
                     left, top, offset, draw=True, window=True):
    b = behavior
    # Exercise the real root:22BF win_IsWinOpen body. Its window handle table
    # uses the valid shared Ralloc fixture; the stale case points at a real
    # zero master-table slot so the original failed-lock cleanup is safe.
    if window in ("open", "closed"):
        arena = memory_suite.heap_case(label + "/ralloc", [(16, 1, {"size": 64}), (0xF0, 0x80)],
            handles=[0], contract="valid Ralloc-backed window record for original win_IsWinOpen")
        handle_off = memory_suite.MASTER_FIRST
        win_handle = (handle_off, memory_suite.HANDLE_SEG)
        flag = 0x0200 if window == "open" else 0
        win_data = (memory_suite.HEAP_SEG + 2) * 16
        window_writes = list(arena.writes) + [(win_data + 0x1C, _w(flag))]
    elif window == "invalid":
        arena = memory_suite.heap_case(label + "/ralloc", [(16, 1, {"size": 64}), (0xF0, 0x80)],
            handles=[], contract="empty Ralloc master slot for original failed-lock cleanup")
        handle_off = memory_suite.MASTER_ONE_PAST
        win_handle = (handle_off, memory_suite.HANDLE_SEG)
        window_writes = list(arena.writes) + [(memory_suite.HANDLE_SEG * 16 + handle_off, bytes(4))]
    else:
        arena = memory_suite.heap_case(label + "/ralloc", [(16, 1, {"size": 64}), (0xF0, 0x80)],
            handles=[], contract="absent window handle entry")
        win_handle = (0, 0)
        window_writes = list(arena.writes)
    win_table = b.symbol_address("win_handles")
    writes = window_writes + [
        (win_table + 4, struct.pack("<HH", *win_handle)),
        (b.symbol_address("fd_50F6_0508"), _w(xorigin) + _w(yorigin)),
        (b.symbol_address("fd_50F6_10D2"), _w(left) + _w(top) + _w(left + 320) + _w(top + 200)),
        (b.symbol_address("fd_50F6_3856"), _w(sx)),
        (b.symbol_address("fd_50F6_3858"), _w(sy)),
        (b.symbol_address("fd_50F6_38C0"), _w(offset)),
        (b.symbol_address("fd_50F6_10E0"), _w(width)),
        (b.symbol_address("fd_50F6_10DE"), _w(height)),
    ]
    callbacks = {
        "f_22BF_09B0": _callback(regs=("ax",)),
        "clip_Push": _callback(handler=_noop),
        "clip_SetWin": _callback(1, _noop),
        "clip_Pop": _callback(handler=_noop),
        "f_1CE2_0410": _callback(3, _noop, project=_capture_rect),
    }
    return b.Case(label, writes=writes,
                  observe=[_range("fd_50F6_38C2", 8), b.Range("window_handles", win_table, 8),
                           b.Range("ralloc_globals", memory_suite.dga(0x2F2A), 0x28),
                           b.Range("heap", memory_suite.HEAP_SEG * 16, 0x100 * 16),
                           b.Range("handle_table", memory_suite.HANDLE_SEG * 16 + 0xF00, 0x100)],
                  callbacks=callbacks, return_kind="void",
                  metadata={"suite": SUITE, "contract": "DrawMapCursor ordered clip/draw boundary trace, semantic Rect pointer and cursor state", "host_boundary": "clip calls and f_1CE2_0410 XOR rectangle; original f_22BF_09B0 win_IsWinOpen executes"})


def map_cursor_cases(random_count=1000, seed=0xC012):
    cases = []
    for draw in (True,):
        for window in ("absent", "open", "closed", "invalid"):
            for values in ((0, 0, 40, 30, 16, 16, 0, 0, 0),
                           (127, 63, 40, 30, 16, 16, 9, 11, -7),
                           (-1, -1, 0, 0, 0, 0, -300, 280, 32767),
                           (64, 32, 17, 13, 8, 12, -20, -30, -160)):
                cases.append(_map_cursor_case(f"directed/{draw}/{window}/{len(cases)}", *values, draw, window))
    rng = random.Random(seed)
    for i in range(random_count):
        cases.append(_map_cursor_case(f"random/{i}", rng.choice([-1, 0, 1, 63, 64, 127, rng.randrange(-128, 256)]),
            rng.choice([-1, 0, 1, 31, 32, 63, rng.randrange(-64, 128)]), rng.randrange(0, 65), rng.randrange(0, 41),
            rng.choice([1, 2, 4, 8, 16, rng.randrange(1, 33)]), rng.choice([1, 2, 4, 8, 16, rng.randrange(1, 33)]),
            rng.randrange(-500, 501), rng.randrange(-500, 501), rng.randrange(-32768, 32768), bool(rng.randrange(2)),
            rng.choice(("absent", "open", "closed", "invalid"))))
    return cases


def _invert_case(label, x, y, left, top, resolution):
    b = behavior
    # Point offset constants vary by run to test pointer dereferences, not just
    # the output's translation. Four signed h/v pairs match g_2A42's contract.
    shape = [(0, 0), (28, 0), (28, 20), (0, 20)]
    writes = [(b.symbol_address("fd_50F6_10D2"), _w(left) + _w(top) + _w(left + 320) + _w(top + 200)),
              (b.symbol_address("g_3DB2"), _w(resolution)),
              (b.symbol_address("fd_55B3_2A42"), b"".join(_w(q) for pt in shape for q in pt))]
    callbacks = {"clip_Push": _callback(handler=_noop), "clip_SetWin": _callback(1, _noop),
                 "clip_Pop": _callback(handler=_noop), "f_1FAA_0006": _callback(4, _noop, project=_capture_quad)}
    return b.Case(label, args=[x, y], writes=writes,
        callbacks=callbacks, observe=[_range("fd_50F6_10D2", 8)], return_kind="void",
        metadata={"suite": SUITE, "contract": "InvertPatch semantic four-point polygon and ordered clip/draw trace", "host_boundary": "clip calls and f_1FAA_0006 polygon XOR"})


def invert_cases(random_count=1000, seed=0x1A7E):
    cases = []
    for resolution in (320, 640):
        for x in (-1, 0, 1, 2, 31, 63, 127):
            for y in (-1, 0, 1, 2, 31, 63):
                cases.append(_invert_case(f"directed/r{resolution}/{x}/{y}", x, y, -12, 9, resolution))
    rng = random.Random(seed)
    for i in range(random_count):
        cases.append(_invert_case(f"random/{i}", rng.randrange(-32768, 32768), rng.randrange(-32768, 32768),
                                  rng.randrange(-32768, 32768), rng.randrange(-32768, 32768), rng.choice([320, 640, rng.randrange(65536)])))
    return cases


def _project_map_draw_intent(machine, args):
    """Project draw arguments together with all implicit helper input globals."""
    word = lambda name: machine.word(behavior.symbol_address(name))
    clip = list(struct.unpack("<4h", machine.read(behavior.symbol_address("fd_50F6_110C"), 8)))
    return {"xy": list(args), "tile": word("g_94E4"), "life_or_draw_code": word("g_9126"),
            "plane": word("MapPlane"), "mode": word("fd_50F6_1102"),
            "display_family": machine.read(behavior.symbol_address("g_5A97"), 1)[0],
            "tile_scale": [word("fd_55B3_19BE"), word("fd_55B3_19C0")], "clip_rect": clip,
            "g_19D0": machine.word(memory_suite.dga(0x19D0)),
            "tile_buffer_pointers": machine.read(behavior.symbol_address("fd_50F6_10E6"), 8).hex(),
            "tile_source_pointer": machine.read(behavior.symbol_address("fd_50F6_10EE"), 4).hex(),
            "draw_functions": {"g_914C": machine.read(behavior.symbol_address("g_914C"), 4).hex(),
                               "g_917C": machine.read(behavior.symbol_address("g_917C"), 4).hex()}}


def _mapdata_case(label, target, x, y, plane, view, tile, life, cache=-1, tilecache=0, topflag=0, pher=0x20):
    b = behavior
    # Arrays in DOS are row-major with the first subscript outermost.
    xcell, ycell = (x & (0x7f if plane < 2 else 0x3f)), y & 0x3f
    writes = [
        (b.symbol_address("MapPlane"), _w(plane)), (b.symbol_address("fd_3D57_07BE"), _w(view)),
        (b.symbol_address("fd_50F6_0508"), _w(0) + _w(0)),
        (b.symbol_address("g_94E4"), _w(0x7777)), (b.symbol_address("g_9126"), _w(0x6666)),
        (b.symbol_address("fd_50F6_049A"), _w(2)), (b.symbol_address("fd_50F6_04C2"), _w(3)),
        (b.symbol_address("fd_50F6_0502"), _w(4)), (b.symbol_address("fd_50F6_0496"), _w(5)),
        (b.symbol_address("fd_55B3_19BE"), _w(16)), (b.symbol_address("fd_55B3_19C0"), _w(16)),
        (b.symbol_address("fd_55B3_19CE"), _w(topflag)),
        (b.symbol_address("fd_50F6_15C4"), _w(cache) * 1200),
        (b.symbol_address("fd_50F6_1114"), bytes([tilecache & 255]) * 1200),
    ]
    if target == "f_0250_129E":
        # Run the original/candidate helper bodies for their caller-visible
        # state effects, while selecting the source's no-render mode so no
        # physical graphics driver is needed. f_0250_0721 reads the selected
        # base pointer even in this mode, so provide a valid disjoint buffer.
        safe_base = 0xA300
        writes += [
            (b.symbol_address("fd_50F6_1102"), _w(0)),
            (b.symbol_address("g_5A97"), b"\0"),
            (memory_suite.dga(0x19D0), _w(0)),
            (b.symbol_address("fd_50F6_10E6"), _w(0) + _w(safe_base) + _w(0) + _w(safe_base)),
            (b.symbol_address("fd_50F6_10EE"), _w(0) + _w(safe_base)),
            (b.symbol_address("fd_50F6_110C"), _w(0) + _w(0) + _w(640) + _w(480)),
            (b.symbol_address("g_914C"), b"\0" * 4),
            (b.symbol_address("g_917C"), b"\0" * 4),
            (safe_base * 16, bytes(0x2000)),
        ]
    # Set a single selected tile/life cell and make every nearby pheromone
    # table deterministic. Array extents follow declarations in the module.
    if plane < 2:
        idxa = (xcell * 64 + ycell)
        writes += [(b.symbol_address("MapA") + idxa, bytes([tile & 255])),
                   (b.symbol_address("LifeA") + idxa, bytes([life & 255]))]
        for name in ("PherMapA", "PherMapBN", "PherMapBT", "PherMapRN", "PherMapRT"):
            writes.append((b.symbol_address(name) + ((xcell >> 1) * 32 + (ycell >> 1)), bytes([pher if view == ("PherMapA PherMapBN PherMapBT PherMapRN PherMapRT".split().index(name)) else 0])))
    else:
        idx = xcell * 64 + ycell
        writes += [(b.symbol_address("MapB" if plane == 2 else "MapR") + idx, bytes([tile & 255]),),
                   (b.symbol_address("LifeB" if plane == 2 else "LifeR") + idx, bytes([life & 255]))]
    callbacks = {"Punt": _callback(1, _noop)}
    if target == "f_0250_129E":
        # Register without a handler: PreparedPair traces the original helper
        # entry and then continues into original EXE code. Candidate calls use
        # candidate whole-module entries and execute their natural C bodies.
        callbacks.update({"f_0250_0721": b.Callback(2, project=_project_map_draw_intent),
                          "f_0250_0ADB": b.Callback(2, project=_project_map_draw_intent)})
    else:
        callbacks.update({"f_0250_0721": _callback(2, _noop), "f_0250_0ADB": _callback(2, _noop)})
    observe = [_range("g_94E4", 2), _range("g_9126", 2), _range("MapPlane", 2),
               _range("fd_50F6_1102", 2), _range("g_5A97", 1),
               b.Range("g_19D0", memory_suite.dga(0x19D0), 2),
               _range("fd_50F6_10E6", 8), _range("fd_50F6_10EE", 4),
               _range("fd_50F6_110C", 8), _range("g_914C", 4), _range("g_917C", 4),
               _range("fd_50F6_15C4", 2400), _range("fd_50F6_1114", 1200)]
    return b.Case(label, args=[x, y], writes=writes, observe=observe, callbacks=callbacks,
        return_kind="void", metadata={"suite": SUITE,
        "contract": (f"{target} selected cell and cache effects; f_0250_129E executes original helper bodies and captures normalized draw intent from x/y plus pre-entry g_94E4, g_9126, plane, mode and render globals" if target == "f_0250_129E" else f"{target} selected cell, life/view partitions and map state effects"),
        "host_boundary": ("f_0250_0721/f_0250_0ADB trace-and-pass-through; mode 0 avoids hardware dispatch, not helper state transitions; Punt guarded by safe domain" if target == "f_0250_129E" else "Punt invalid-state boundary guarded by safe directed/randomized domain")})


def map_cell_cases(target, random_count=500, seed=0x1018):
    cases = []
    vals = (0, 1, 0x10, 0x11, 0x20, 0x7f, 0xfe, 0xff)
    for plane in range(4):
        for life in vals:
            for view in (0, 1, 2, 3, 4, 5, 0xffff):
                cases.append(_mapdata_case(f"directed/p{plane}/l{life:02x}/v{view:04x}", target, 3, 4, plane, view, 0x42, life,
                                           cache=-2 if life == 0xff else -1, topflag=(life & 1)))
    if target == "f_0250_1018":
        for pher in (0x0f, 0x10, 0x11):
            cases.append(_mapdata_case(f"pheromone-boundary/{pher:02x}", target, 3, 4, 0, 0, 0x42, 1, pher=pher))
    if target == "f_0250_129E":
        # Cache hits, dirty cells, top row and argument guards; cache starts at
        # -2 and must be incremented without touching draw helpers.
        for x, y in [(-1, 0), (40, 1), (0, -1), (0, 30), (0, 0), (39, 29), (17, 0)]:
            cases.append(_mapdata_case(f"boundary/{x}/{y}", target, x, y, 0, 0, 0x20, 1, cache=-2, topflag=1 if y == 0 else 0))
    rng = random.Random(seed)
    for i in range(random_count):
        plane = rng.randrange(4); life = rng.choice(vals)
        cases.append(_mapdata_case(f"random/{i}", target, rng.randrange(40), rng.randrange(30), plane,
                                   rng.randrange(7), rng.randrange(256), life, cache=rng.choice([-2, -1, 0, 1, 0x100]),
                                   tilecache=rng.randrange(256), topflag=rng.randrange(2)))
    return cases


def _read_cstring(machine, args, index=0, limit=512):
    off, seg = args[index:index + 2]
    data = bytearray()
    for i in range(limit):
        value = machine.read(seg * 16 + off + i, 1)[0]
        if value == 0:
            return bytes(data)
        data.append(value)
    raise behavior.ExecutionError("unterminated resource text in fixture")


def _balloon_load(machine, args):
    # Acquisition is the host resource boundary. The returned handle points at
    # a fixture block, while all lock/pointer/free operations are the original
    # DOS Ralloc functions operating on a lists.py-compatible handle table.
    machine.state.setdefault("resource_requests", []).append(
        {"message": _read_cstring(machine, args), "flags": args[2]})
    return machine.state["resource_handle"]


def _bitmap_load(machine, args):
    machine.state.setdefault("resource_requests", []).append(
        {"object": args[0], "kind": args[1], "resource_available": machine.state["resource_available"]})
    return machine.state["resource_handle"] if machine.state["resource_available"] else (0, 0)


def _release_resource(machine, args):
    machine.state.setdefault("resource_releases", []).append(args)


def _tile_resource_load(machine, args):
    object_id, kind = args
    handle = (0xF100 + object_id, 0x7200)
    machine.state.setdefault("tile_resource_acquisitions", []).append(
        {"object": object_id, "kind": kind, "handle": list(handle)})
    return handle


def _tile_resource_release(machine, args):
    machine.state.setdefault("tile_resource_releases", []).append(args)


def _pic_transfer_project(machine, args, *, header):
    off, seg = args[-2:]
    pointer = (off, seg)
    if pointer == machine.state.get("temp_buffer"):
        size = machine.state["temp_buffer_size"]
    elif header:
        size = machine.state["picture_length"]
    else:
        size = machine.state["pixel_length"]
    return {"x": args[0], "y": args[1], "pointed_bytes": machine.read(seg * 16 + off, size).hex()}


def _screen_size(machine, args):
    x0, y0, x1, y1 = (v - 0x10000 if v & 0x8000 else v for v in args)
    width, height = x1 - x0, y1 - y0
    if not 0 <= width <= 0x7fff or not 0 <= height <= 0x7fff:
        raise behavior.ExecutionError(f"invalid modeled screen read rectangle {args}")
    row_bytes = {0: 3 * ((width + 7) // 8),
                 1: 2 * ((width + 7) // 8),
                 2: (width + 1) // 2}[machine.state["display"]]
    size = 4 + row_bytes * height
    machine.state.setdefault("screen_read_rectangles", []).append(
        {"rect": args, "width": width, "height": height, "bytes": size})
    return size


def _screen_copy(machine, args):
    x0, y0, x1, y1, off, seg = args
    x0, y0, x1, y1 = (v - 0x10000 if v & 0x8000 else v for v in (x0, y0, x1, y1))
    width, height = x1 - x0, y1 - y0
    row_bytes = {0: 3 * ((width + 7) // 8),
                 1: 2 * ((width + 7) // 8),
                 2: (width + 1) // 2}[machine.state["display"]]
    header = struct.pack("<HH", width, height)
    pixels = bytes(((x0 * 3 + y0 * 5 + i * 13) & 0xff) for i in range(row_bytes * height))
    data = header + pixels
    machine.write(seg * 16 + off, data)
    machine.state["temp_buffer"] = (off, seg)
    machine.state["temp_buffer_size"] = len(data)
    machine.state.setdefault("screen_pixel_captures", []).append(
        {"rect": [x0, y0, x1, y1], "buffer": data.hex()})


def _screen_copy_project(machine, args):
    return {"rect": args[:4], "destination": args[4:]}


def _malloc_buffer(machine, args):
    size = args[0]
    # 0x9000 is the PreparedPair candidate code segment. Keep host scratch at
    # a disjoint high-memory arena, away from the code, Ralloc blocks and stack.
    next_linear = machine.state.get("malloc_next_linear", 0xA1000)
    linear = (next_linear + 15) & ~15
    if linear + size >= 0xB0000:
        raise behavior.ExecutionError("modeled graphics scratch arena exhausted")
    machine.state["malloc_next_linear"] = linear + size
    pointer = (linear & 0xF, linear >> 4)
    machine.state["temp_buffer"] = pointer
    machine.state["temp_buffer_size"] = size
    machine.state.setdefault("scratch_allocations", []).append(
        {"size": size, "pointer": list(pointer)})
    return pointer


def _free_buffer(machine, args):
    machine.state.setdefault("scratch_releases", []).append(args)


def _bitmap_printf_project(machine, args):
    return {"format": _read_cstring(machine, args).hex()}


def _render_tile(machine, args):
    tile = {"tile": machine.word(behavior.symbol_address("g_94E4")),
            "life": machine.word(behavior.symbol_address("g_9126")),
            "plane": machine.word(behavior.symbol_address("MapPlane"))}
    machine.state.setdefault("tile_render_requests", []).append(tile)
    bpp = machine.state["tile_bytes"]
    seed = (tile["tile"] + tile["life"] + tile["plane"] * 13) & 255
    machine.state["tile_pixels"] = bytes((seed + i * 17) & 255 for i in range(bpp)).hex()


def _copy_tile(machine, args):
    off, seg, stride = args
    linear = seg * 16 + off
    if machine.state.get("buffer_linear") is None:
        # The first transfer follows the composition buffer's two-word size header.
        machine.state["buffer_linear"] = linear - 4
    dest = linear - machine.state["buffer_linear"]
    before = machine.read(linear, machine.state["tile_bytes"])
    pixels = bytes.fromhex(machine.state.get("tile_pixels", "00" * machine.state["tile_bytes"]))
    machine.write(linear, pixels)
    after = machine.read(linear, len(pixels))
    machine.state.setdefault("tile_pixel_transfers", []).append(
        {"buffer_offset": dest, "stride": stride, "before": before.hex(), "after": after.hex()})


def _capture_clipcopy(machine, args):
    ptrs = [(args[i], args[i + 1]) for i in range(0, 8, 2)]
    at = lambda p: p[1] * 16 + p[0]
    size = machine.state["buffer_size"]
    return {"rect1": list(struct.unpack("<4h", machine.read(at(ptrs[0]), 8))),
            "size": list(struct.unpack("<2h", machine.read(at(ptrs[1]), 4))),
            "rect2": list(struct.unpack("<4h", machine.read(at(ptrs[2]), 8))),
            "buffer": machine.read(at(ptrs[3]), size).hex()}


def _message_blit(machine, args):
    src = args[1] * 16 + args[0]
    dst = args[3] * 16 + args[2]
    length = machine.state["resource_pixel_length"]
    machine.state.setdefault("message_blits", []).append(
        {"source_with_dimensions": machine.read(src, length).hex(),
         "buffer_before": machine.read(dst, machine.state["buffer_size"]).hex(),
         "x_offset": args[4], "y_offset": args[5]})


def _winprintf(machine, args):
    fmt = _read_cstring(machine, args)
    if fmt.startswith(b"Vis message"):
        machine.state.setdefault("format_commands", []).append(
            {"format": fmt.hex(), "message": _read_cstring(machine, args, 2).hex(),
             "x": args[4], "y": args[5]})


def _font_select(machine, args):
    machine.state["selected_font"] = args[0]


def _window_clip_setup(machine, args):
    machine.state.setdefault("window_clip_setups", []).append(
        machine.read(behavior.symbol_address("fd_50F6_110C"), 8).hex())


def _balloon_printf_project(machine, args):
    fmt = _read_cstring(machine, args)
    if fmt.startswith(b"Vis message"):
        return {"format": fmt.hex(), "message": _read_cstring(machine, args, 2).hex(),
                "x": args[4], "y": args[5]}
    # Ralloc emits diagnostic printf calls while traversing the no-EMS path.
    # They are outside the rendering contract; keep only their literal format.
    return {"internal_format": fmt.hex()}


def _balloon_case(label, *, mode=1, plane=0, x=80, y=80, picw=8, pich=8,
                  spider_clip=False):
    b = behavior
    # One real firm Ralloc block is the message picture; the remaining free
    # paragraphs back the real f_171C_1A9E/f_171C_1B84/f_171C_1BBA/f_171C_1C0A
    # allocation lifecycle for the temporary composition buffer.
    rows = [(16, 1, {"size": 224, "age": 1}), (0xF0, 0x80)]
    arena = memory_suite.heap_case(label + "/ralloc", rows, handles=[0],
        contract="one message picture handle and a valid free block for DrawBalloons temporary buffers")
    handle_off = memory_suite.HANDLE_TOP - 4
    handle = (handle_off, memory_suite.HANDLE_SEG)
    resource_ptr = (memory_suite.HEAP_SEG + 2, 0)
    # Picture bytes begin with width/height at byte 8, as read by the original
    # Pic contract; remaining bytes are deterministic opaque source pixels.
    pixels = bytes((i * 29 + 3) & 255 for i in range(picw * pich))
    picture = struct.pack("<hB5sHH", 0, 0, b"\0" * 5, picw, pich) + pixels
    if len(picture) > 224:
        raise ValueError("balloon picture exceeds its Ralloc block")
    text_linear = BALLOON_TEXT[1] * 16 + BALLOON_TEXT[0]
    # BalloonIsVisible checks tile coordinates. The source cell follows the
    # same pixel-to-tile conversion used by AddMsgBalloon(style != 10).
    tx, ty = x // 16, y // 16
    writes = list(arena.writes) + [
        (resource_ptr[0] * 16 + resource_ptr[1], picture + bytes(224 - len(picture))),
        (text_linear, BALLOON_MESSAGE + b"\0"),
        (b.symbol_address("fd_50F6_1092"), _w(1)),
        (b.symbol_address("fd_50F6_04C8"), _w(x) + _w(y)),
        (b.symbol_address("fd_50F6_04F6"), _w(plane)),
        (b.symbol_address("fd_50F6_04E6"), _w(0)),
        (b.symbol_address("fd_50F6_04A6"), struct.pack("<HH", *BALLOON_TEXT)),
        (b.symbol_address("MapPlane"), _w(plane)),
        (b.symbol_address("fd_50F6_0508"), _w(0) + _w(0)),
        (b.symbol_address("fd_50F6_10E0"), _w(40)), (b.symbol_address("fd_50F6_10DE"), _w(30)),
        (b.symbol_address("fd_50F6_110C"), _w(0) + _w(0) + _w(640) + _w(480)),
        (b.symbol_address("fd_50F6_1102"), _w(mode)),
        (b.symbol_address("fd_50F6_37D2"), _w(0 if spider_clip else 500)),
        (b.symbol_address("fd_50F6_37D4"), _w(0 if spider_clip else 500)),
        # noems allocations compare free-block segments with this DOS limit;
        # keep the entire deterministic arena below the boundary.
        (b.symbol_address("fd_50F6_3950"), _w(memory_suite.HEAP_SEG + 0x100)),
        (b.symbol_address("fd_50F6_37D6"), _w(22) + _w(28) + _w(36) + _w(42)),
        (b.symbol_address("fd_50F6_1F26"), _w(14) + _w(14)),
        (b.symbol_address("fd_50F6_15C4"), _w(-1) * 1200),
        (b.symbol_address("fd_50F6_1114"), bytes(1200)),
        (b.symbol_address("fd_50F6_37E6"), struct.pack("<HH", b.symbol("f_0250_0ADB")["off"], b.symbol("f_0250_0ADB")["seg"])),
        (b.symbol_address("fd_50F6_37EA"), struct.pack("<HH", b.symbol("f_0250_0721")["off"], b.symbol("f_0250_0721")["seg"])),
        (b.symbol_address("fd_50F6_37EE"), struct.pack("<HH", b.symbol("f_0250_0D10")["off"], b.symbol("f_0250_0D10")["seg"])),
        (b.symbol_address("fd_55B3_19BE"), _w(16)), (b.symbol_address("fd_55B3_19C0"), _w(16)),
        (b.symbol_address("fd_50F6_10E6"), b"\0" * 4),
        (b.symbol_address("fd_50F6_10EA"), b"\0" * 4),
        (memory_suite.dga(0x19D0), _w(0)),
        (b.symbol_address("fd_50F6_3950"), _w(memory_suite.HEAP_SEG + 0x100)),
    ]
    if 0 <= tx < 128 and 0 <= ty < 64:
        writes += [(b.symbol_address("MapA") + tx * 64 + ty, b"\x42"),
                   (b.symbol_address("LifeA") + tx * 64 + ty, b"\x01")]
    # Function callback pointers refer to registered, otherwise-unused DOS
    # entries. The common runner hooks those addresses in both machines.
    bpp, rowbytes = ({1: (2, 0x80), 2: (6, 0x48), 3: (2, 0x20)}[mode])
    bx, by = x + 4, y - pich - 4
    wt = (bx % 16 + picw + 15) // 16
    ht = (by % 16 + pich + 15) // 16
    buf_size = ht * wt * rowbytes + 4
    callbacks = {
        "f_1629_000C": b.Callback(3, _balloon_load, project=lambda m, a: {"message": _read_cstring(m, a), "flags": a[2]}),
        "f_1A53_00BA": b.Callback(2, _tile_resource_load),
        "db_ReleaseHandle": b.Callback(2, _tile_resource_release),
        "f_0250_062A": b.Callback(0, project=lambda m, a: a),
        "f_0250_0643": b.Callback(1, project=lambda m, a: a),
        "f_171C_1B84": b.Callback(2), "f_171C_1BBA": b.Callback(2),
        "f_171C_1C0A": b.Callback(2),
        "f_171C_1A9E": b.Callback(5),
        "f_24AB_02AD": b.Callback(1, _font_select), "WinPrintf": b.Callback(6, _winprintf, project=_balloon_printf_project),
        "f_0250_5058": b.Callback(0, _window_clip_setup),
        "f_0250_0915": b.Callback(0, _render_tile), "f_0250_0B86": b.Callback(0, _render_tile),
        "f_0250_0ADB": b.Callback(3, _copy_tile),
        "f_0250_0721": b.Callback(6, _message_blit),
        "f_0250_0D10": b.Callback(8, _noop, project=_capture_clipcopy),
    }
    observed = [
        _range("fd_50F6_1092", 2), _range("fd_50F6_04C8", 6 * 4),
        _range("fd_50F6_04F6", 6 * 2), _range("fd_50F6_04E6", 6 * 2),
        _range("fd_50F6_04A6", 6 * 4), _range("fd_50F6_15C4", 1200 * 2),
        _range("fd_50F6_1114", 1200), _range("LifeA", 128 * 64),
        _range("MapA", 128 * 64),
        _range("fd_50F6_10E6", 8),
        b.Range("ralloc_globals", memory_suite.dga(0x2F2A), 0x28),
        b.Range("heap", memory_suite.HEAP_SEG * 16, 0x100 * 16),
        b.Range("handle_table", memory_suite.HANDLE_SEG * 16 + 0xF00, 0x100),
    ]
    return b.Case(label, writes=writes, observe=observed, callbacks=callbacks, return_kind="void",
        state={"resource_handle": handle, "message": BALLOON_MESSAGE.hex(), "resource_bytes": picture.hex(),
               "resource_pixel_length": len(picture) - 8, "buffer_linear": None,
               "buffer_size": buf_size, "tile_bytes": bpp, "tile_pixels": bytes(bpp).hex(),
               "resource_requests": [], "resource_releases": [], "tile_render_requests": [],
               "tile_resource_acquisitions": [], "tile_resource_releases": [],
               "tile_pixel_transfers": [], "message_blits": [], "format_commands": [],
               "selected_font": None, "window_clip_setups": [], "spider_clip": spider_clip},
        metadata={"suite": SUITE, "contract": "DrawBalloons one queued message, real Ralloc lock/buffer lifecycle, ordered host pixel commands and pointed picture/buffer bytes",
                  "resource_picture": {"type": 0, "width": picw, "height": pich, "pixel_bytes": len(pixels), "handle": list(handle), "plane": plane},
                  "coordinates": {"x": x, "y": y},
                  "buffer_layout": {"mode": mode, "bytes_per_tile": bpp, "rowbytes_per_tile": rowbytes, "width_tiles": wt, "height_tiles": ht, "allocation_bytes": buf_size},
                  "host_boundaries": ["f_1629_000C resource acquisition", "f_0250_0643 tile-set switch", "f_0250_0915/f_0250_0B86 source tile renderer", "fd_50F6_37E6 tile pixel transfer", "fd_50F6_37EA picture overlay", "fd_50F6_37EE clipping save/restore"],
                  "helper_policy": "f_171C_1A9E/1B84/1BBA/1C0A execute original Ralloc code over the memory_suite valid arena; resource acquisition and host pixel/render calls are explicit callbacks",
                  "limits": "normalized render/copy traces and complete pointed source/destination bytes; no display framebuffer is modeled or claimed"})


def balloon_cases(random_count=0, seed=0xBA1100):
    # Coordinate values exercise each display mode, nonzero clipping path,
    # positive/negative picture phase, and multiple planes with a visible cell.
    cases = [
        _balloon_case("directed/mode1/no-spider", mode=1, x=80, y=80),
        _balloon_case("directed/mode2/no-spider", mode=2, x=96, y=96),
        _balloon_case("directed/mode3/no-spider", mode=3, x=112, y=112, plane=2),
        _balloon_case("directed/mode1/spider-clip", mode=1, x=128, y=128, spider_clip=True),
        _balloon_case("directed/pixel-phase", mode=1, x=85, y=91, picw=11, pich=9),
        _balloon_case("directed/visible-left-top", mode=1, x=0, y=48, picw=1, pich=1),
        _balloon_case("directed/visible-right-bottom", mode=3, x=624, y=464, picw=13, pich=11),
        _balloon_case("directed/outside-right-bottom", mode=2, x=640, y=480),
        _balloon_case("directed/outside-negative", mode=1, x=-16, y=48),
    ]
    rng = random.Random(seed)
    for i in range(random_count):
        mode = rng.choice((1, 2, 3))
        width, height = rng.randrange(1, 14), rng.randrange(1, 13)
        cases.append(_balloon_case(
            f"random/{i}", mode=mode, plane=rng.choice((0, 1, 2, 3)),
            x=rng.randrange(64, 500), y=rng.randrange(96, 420),
            picw=width, pich=height, spider_clip=(rng.randrange(4) == 0)))
    return cases


def _pic_case(label, pic_type, mode, x, y, width, height, *, available=True, display=0):
    b = behavior
    rows = [(16, 1, {"size": 224, "age": 1}), (0xF0, 0x80)]
    arena = memory_suite.heap_case(label + "/ralloc", rows, handles=[0],
        contract="one valid Ralloc-owned picture handle with a free block and real lock/unlock helpers")
    handle = (memory_suite.HANDLE_TOP - 4, memory_suite.HANDLE_SEG)
    pic_seg, pic_off = memory_suite.HEAP_SEG + 2, 0
    if pic_type == 3:
        if display == 2:
            row_bytes = (width + 1) // 2
            pixels = bytes((((i * 7) & 0x0f) << 4) | ((i * 11 + 3) & 0x0f)
                           for i in range(row_bytes * height))
        elif display & 1:
            row_bytes = (width + 7) // 8
            pixels = bytes((0xA5 ^ (i * 13)) & 255 for i in range(2 * row_bytes * height))
        else:
            row_bytes = (width + 7) // 8
            pixels = bytes((0x5A ^ (i * 19)) & 255 for i in range(4 * row_bytes * height))
        pixels = struct.pack("<HH", width, height) + pixels
    else:
        pixels = bytes((i * 31 + 7) & 255 for i in range(width * height))
    picture = struct.pack("<hB5sHH", pic_type, mode & 255, b"\0" * 5, width, height) + pixels
    if len(picture) > 224:
        raise ValueError(f"bitmap fixture exceeds picture Ralloc block ({len(picture)} bytes)")
    writes = list(arena.writes) + [
        (pic_seg * 16 + pic_off, picture + bytes(224 - len(picture))),
        (b.symbol_address("g_5A97"), bytes([display & 255])),
        (b.symbol_address("g_9140"), struct.pack("<HH", b.symbol("f_0250_0721")["off"], b.symbol("f_0250_0721")["seg"])),
        (b.symbol_address("g_9148"), struct.pack("<HH", b.symbol("f_0250_0D10")["off"], b.symbol("f_0250_0D10")["seg"])),
    ]
    callbacks = {
        "db_LoadObject": b.Callback(2, _bitmap_load),
        "db_ReleaseObject": b.Callback(2, _release_resource),
        "GPutPacked": b.Callback(4, _noop, project=lambda m, a: _pic_transfer_project(m, a, header=True)),
        "f_1B4E_003B": b.Callback(4, _noop, project=lambda m, a: _pic_transfer_project(m, a, header=False)),
        "f_1B4E_005E": b.Callback(4, _noop, project=lambda m, a: _pic_transfer_project(m, a, header=False)),
        # These callbacks are used as the documented g_9140/g_9148 function
        # pointer services only in type-3 contracts added below.
        "f_0250_0721": b.Callback(4, _screen_size),
        "f_0250_0D10": b.Callback(6, _screen_copy, project=_screen_copy_project),
        "WinPrintf": b.Callback(6, _noop, project=_bitmap_printf_project),
        "o03_3258_040D": b.Callback(4), "o01_32B5_000F": b.Callback(4),
        "o00_35A6_0007": b.Callback(4),
        "malloc": b.Callback(1, _malloc_buffer), "free": b.Callback(2, _free_buffer),
    }
    return b.Case(label, registers={"ax": x, "dx": y, "bx": 0x2345},
        # The original far _fastcall ABI places x,y,id in AX,DX,BX.
        writes=writes, observe=[b.Range("resource_picture", pic_seg * 16 + pic_off, len(picture)),
            b.Range("heap", memory_suite.HEAP_SEG * 16, 0x100 * 16),
            b.Range("handle_table", memory_suite.HANDLE_SEG * 16 + 0xF00, 0x100),
            _range("g_5A97", 1), b.Range("screen_size_callback", b.symbol_address("g_9140"), 4),
            b.Range("screen_copy_callback", b.symbol_address("g_9148"), 4)],
        callbacks=callbacks, return_kind="s16",
        state={"resource_handle": handle, "resource_available": available, "display": display,
               "picture_bytes": picture.hex(), "picture_length": len(picture), "pixel_length": len(pixels),
               "format_commands": [], "resource_requests": [], "resource_releases": [],
               "screen_read_rectangles": [], "screen_pixel_captures": [],
               "scratch_allocations": [], "scratch_releases": [],
               "temp_buffer": None, "temp_buffer_size": 0, "malloc_next_linear": 0xA1000},
        metadata={"suite": SUITE, "contract": "win_DrawBitMap resource type dispatch, output result, ordered host render/release calls and complete pointed picture data",
                  "resource_picture": {"type": pic_type, "mode": mode, "width": width, "height": height, "pixel_bytes": len(pixels), "resource_available": available},
                  "calling_convention": "_fastcall: CX=x, DX=y, AX=id; far return; original Ralloc arena supports the handle pointer",
                  "helper_policy": "db_LoadObject acquisition/db_ReleaseObject host database lifetime are modeled; Ralloc fixtures remain real list-compatible handle/data blocks; host render services are traced; compressed decode functions are original when reached",
                  "limits": "host drawing commands and picture resource bytes compared; no final display framebuffer claimed"})


def bitmap_cases(random_count=0, seed=0xB17B17):
    cases = [
        _pic_case("directed/missing", 0, 0, 17, 21, 8, 8, available=False),
        _pic_case("directed/packed-minus1", -1, 0, 17, 21, 8, 8),
        _pic_case("directed/packed-8000", -32768, 0, 17, 21, 8, 8),
        _pic_case("directed/type0-copy", 0, 0, 17, 21, 8, 8),
        _pic_case("directed/type0-xor", 0, 1, 31, 41, 11, 9),
        _pic_case("directed/type0-minimum", 0, 0, 0, 0, 1, 1),
        _pic_case("directed/type0-negative-clip", 0, 1, -1, -1, 13, 11),
        _pic_case("directed/type3-display2-even", 3, 0, 24, 30, 15, 8, display=2),
        _pic_case("directed/type3-display2-odd", 3, 0, 25, 31, 13, 7, display=2),
        _pic_case("directed/type3-display2-edgewidth", 3, 0, 7, 0, 9, 15, display=2),
        _pic_case("directed/type3-mask-plane", 3, 0, 19, 40, 17, 9, display=1),
        _pic_case("directed/type3-mask-alignment", 3, 0, 7, 1, 8, 8, display=1),
        _pic_case("directed/type3-four-plane", 3, 0, 21, 42, 16, 8, display=0),
        _pic_case("directed/type3-four-plane-alignment", 3, 0, 8, 1, 17, 12, display=0),
        _pic_case("directed/type3-no-resource", 3, 0, 21, 42, 16, 8, display=2, available=False),
    ]
    rng = random.Random(seed)
    for i in range(random_count):
        typ = rng.choice((0, 3))
        display = rng.choice((0, 1, 2))
        if typ == 0:
            width, height = rng.randrange(1, 15), rng.randrange(1, 14)
        else:
            width, height = rng.randrange(1, 25), rng.randrange(1, 15)
        cases.append(_pic_case(f"random/{i}", typ, rng.randrange(2),
                               rng.randrange(-3, 641), rng.randrange(-3, 481),
                               width, height, display=display))
    return cases


def _helper_boundary_specs(target, pair, counts, positive):
    """Describe the execution boundary actually used by this suite.

    Original DOS callees without a handler execute from the pinned EXE. A
    callback with a handler is an explicit deterministic host/resource model.
    The output is deliberately a boundary inventory, not a certification.
    """
    if target == "DrawMapCursor":
        modeled = {
            "clip_Push": "ordered clipping stack command trace; clip geometry is not simulated",
            "clip_SetWin": "ordered clipping window command trace; clip geometry is not simulated",
            "clip_Pop": "ordered clipping stack command trace; clip geometry is not simulated",
            "f_1CE2_0410": "host XOR draw boundary with semantic Rect fields and width projected from the pointed record",
        }
        original = {
            "f_22BF_09B0": "original root:22BF win_IsWinOpen body with AX argument; valid/open, valid/closed, absent, and stale-handle fixtures exercise Ralloc lock/unlock and failed-lock table clearing",
        }
    elif target == "InvertPatch":
        modeled = {
            "clip_Push": "ordered clipping stack command trace; clip geometry is not simulated",
            "clip_SetWin": "ordered clipping window command trace; clip geometry is not simulated",
            "f_1FAA_0006": "host polygon draw boundary with four pointed semantic vertices and two draw arguments",
            "clip_Pop": "ordered clipping stack command trace; clip geometry is not simulated",
        }
        original = {}
    elif target == "f_0250_1018":
        modeled = {
            "f_0250_0721": "available drawing boundary callback; no raster is modeled and this target does not normally dispatch it",
            "f_0250_0ADB": "available drawing boundary callback; no raster is modeled and this target does not normally dispatch it",
            "Punt": "invalid-state diagnostic boundary; valid directed/random domains avoid it",
        }
        original = {}
    elif target == "f_0250_129E":
        modeled = {"Punt": "invalid-state diagnostic boundary; valid directed/random domains avoid it"}
        original = {
            "f_0250_0721": "unhandled trace-and-pass-through to the original helper body; mode 0 executes caller-visible g_9126 transition and avoids hardware renderer dispatch",
            "f_0250_0ADB": "unhandled trace-and-pass-through to the original helper body; mode 0 avoids hardware function-pointer dispatch",
        }
    elif target == "DrawBalloons":
        modeled = {
            "f_1629_000C": "message database resource acquisition and message bytes",
            "f_1A53_00BA": "tile resource handle acquisition fixture",
            "db_ReleaseHandle": "tile resource handle release fixture",
            "f_24AB_02AD": "font selection state",
            "WinPrintf": "formatted text command projection",
            "f_0250_5058": "window clipping state setup",
            "f_0250_0915": "tile raster request and deterministic tile pixels",
            "f_0250_0B86": "alternate tile raster request and deterministic tile pixels",
            "f_0250_0ADB": "tile pixel transfer into the composition buffer",
            "f_0250_0721": "synthetic function-pointer slot fd_50F6_37EA: message picture host blit trace; this is not execution of the original two-argument f_0250_0721 body",
            "f_0250_0D10": "clipping save/restore copy trace",
        }
        original = {
            "f_0250_062A": "original tile-set lookup helper; entry arguments traced",
            "f_0250_0643": "original tile-set selection helper; entry arguments traced",
            "f_171C_1A9E": "original Ralloc allocation helper over valid fixture arena",
            "f_171C_1B84": "original Ralloc lock helper over valid fixture handle table",
            "f_171C_1BBA": "original Ralloc unlock helper over valid fixture handle table",
            "f_171C_1C0A": "original Ralloc free helper over valid fixture arena",
        }
    else:
        modeled = {
            "db_LoadObject": "picture resource acquisition and valid-handle fixture selection",
            "db_ReleaseObject": "picture resource lifetime release trace",
            "GPutPacked": "packed-pixel host draw command and pointed picture projection",
            "f_1B4E_003B": "mode-0 pixel host draw command and pointed pixel projection",
            "f_1B4E_005E": "mode-1 pixel host draw command and pointed pixel projection",
            "f_0250_0721": "synthetic g_9140 function-pointer slot: display buffer-size contract; its address reuses this symbol but its four-argument ABI does not execute the original two-argument root helper",
            "f_0250_0D10": "synthetic g_9148 function-pointer slot: host pixel readback into deterministic packed buffer",
            "WinPrintf": "debug format string projection",
            "malloc": "deterministic disjoint host scratch-buffer arena",
            "free": "host scratch-buffer release trace",
        }
        original = {
            "o03_3258_040D": "original S03 4bpp packed decoder",
            "o01_32B5_000F": "original S01 two-plane 1bpp decoder",
            "o00_35A6_0007": "original S00 four-plane 1bpp decoder",
        }
    rows = []
    for name, contract in sorted({**original, **modeled}.items()):
        is_original = name in original
        rows.append({"name": name,
                     "execution_mode": "ORIGINAL_EXE" if is_original else "MODELED",
                     "observed_call_count": counts["original"].get(name, 0),
                     "executed_from_original": is_original,
                     "contract": contract,
                     "binding_role": ("original DOS helper body" if is_original else
                         "modeled callback slot; address/name reuse does not assert execution of a same-named DOS helper body"),
                     "certification": None if is_original else {
                         "status": "PENDING_SUPERVISOR_REVIEW",
                         "positive_control_id": positive["id"] if positive else None,
                         "negative_control_ids": []}})
    return rows


def _coverage_summary(target, cases):
    summary = {"directed_labels": [c.label for c in cases if not c.label.startswith("random/")],
               "randomized_labels_sha256": behavior.digest("\n".join(
                   c.label for c in cases if c.label.startswith("random/")).encode("utf-8")),
               "domain_values": {}}
    if target == "DrawBalloons":
        meta = [c.metadata["resource_picture"] for c in cases]
        summary["domain_values"] = {
            "modes": sorted({c.metadata["buffer_layout"]["mode"] for c in cases}),
            "planes": sorted({c.metadata["resource_picture"].get("plane", 0) for c in cases}),
            "picture_widths": sorted({x["width"] for x in meta}),
            "picture_heights": sorted({x["height"] for x in meta}),
            "coordinate_ranges": {"x": [min(c.metadata["coordinates"]["x"] for c in cases),
                                         max(c.metadata["coordinates"]["x"] for c in cases)],
                                  "y": [min(c.metadata["coordinates"]["y"] for c in cases),
                                         max(c.metadata["coordinates"]["y"] for c in cases)]},
            "spider_clip_cases": sum(bool(c.state.get("spider_clip")) for c in cases),
        }
    elif target == "win_DrawBitMap":
        pictures = [c.metadata["resource_picture"] for c in cases]
        summary["domain_values"] = {
            "resource_types": sorted({x["type"] for x in pictures}),
            "display_modes": sorted({x["mode"] for x in pictures}),
            "display_families": sorted({c.state["display"] for c in cases}),
            "picture_widths": sorted({x["width"] for x in pictures}),
            "picture_heights": sorted({x["height"] for x in pictures}),
            "missing_resource_cases": sum(not x["resource_available"] for x in pictures),
            "pixel_encodings": {"type3/display0": "four one-bit planes, row bytes ceil(width/8)",
                                "type3/display1": "two one-bit planes, row bytes ceil(width/8)",
                                "type3/display2": "four-bit packed pixels, row bytes ceil(width/2)"},
        }
    else:
        summary["domain_values"] = {
            "directed_labels": [c.label for c in cases if not c.label.startswith("random/")],
            "randomized_count": sum(c.label.startswith("random/") for c in cases),
            "argument_domains_from_case_generator": "See the target-specific case generator in this pinned suite snapshot; case labels and input_sha256 are preserved in the per-case ledger.",
        }
    return summary


def _write_helper_plan(target, run_evidence, outdir, negative_reports=None):
    plan = {"schema": "behavior-helper-boundary-plan-v1",
            "function": target, "suite_id": SUITE,
            "status": "PENDING_SUPERVISOR_REVIEW",
            "source_pins": {key: run_evidence["identity"][key] for key in
                            ("source_sha256", "compiled_source_sha256", "suite_sha256",
                             "harness_sha256", "oracle_sha256", "historical_manifest_sha256",
                             "object_sha256")},
            "case_ledger": run_evidence["case_ledger"],
            "helpers": run_evidence["helper_boundaries"],
            "coverage": run_evidence["coverage"],
            "positive_control_ids": [x["id"] for x in run_evidence["positive_controls"]],
            "negative_control_reports": negative_reports or [],
            "limits": ["host render/resource services are deterministic explicit callbacks",
                       "the suite observes ordered calls, semantic pointer contents, and modeled buffer writes",
                       "it does not claim a final display framebuffer"]}
    path = outdir / f"{target}.helper-boundary-plan.json"
    path.write_text(json.dumps(plan, indent=2) + "\n")
    return path


def _run_target(target, casegen, count, seed, outdir, source=None):
    pair = behavior.PreparedPair(target, source=source, out=outdir / target)
    cases = casegen(count, seed)
    effects = ["return and caller ABI", "ordered helper/render commands and arguments",
               "global/map/cache writes", "projected far-pointer data and nonstack memory"]
    ledger = behavior_ledger.CaseLedger(outdir / f"{target}.cases.jsonl.gz", pair, effects)
    driver_pairs = {}
    failures = []
    lane_counts = {"directed": 0, "randomized": 0}
    helper_counts = {"original": {}, "candidate": {}}
    first_positive = None
    started = time.time()
    for i, case in enumerate(cases):
        active_pair = pair
        if target == "win_DrawBitMap":
            display = case.state.get("display", 0)
            unit = {0: "S00", 1: "S01", 2: "S03"}.get(display)
            if unit is None:
                raise behavior.ExecutionError(f"uncovered bitmap display type {display}")
            if unit not in driver_pairs:
                active_pair = behavior.PreparedPair(target, source=source,
                    out=outdir / target / f"driver-{unit}")
                active_pair.original_machine._load_overlay(unit)
                active_pair.candidate_machine._load_overlay(unit)
                driver_pairs[unit] = active_pair
            else:
                active_pair = driver_pairs[unit]
            ledger.pair = active_pair
        cmp = active_pair.compare(case)
        lane = "randomized" if case.label.startswith("random/") else "directed"
        row = ledger.record(case, cmp, lane=lane)
        lane_counts[lane] += 1
        for side, result in (("original", cmp.original), ("candidate", cmp.candidate)):
            for call in result["trace"]:
                helper_counts[side][call["name"]] = helper_counts[side].get(call["name"], 0) + 1
        if cmp.equal and first_positive is None:
            first_positive = {"id": case.label, "executed": True, "matched": True,
                "execution_errors": 0, "original_executed": True, "candidate_executed": True,
                "source_sha256": pair.identity["source_sha256"],
                "object_sha256": pair.identity["object_sha256"],
                "oracle_sha256": pair.identity["oracle_sha256"],
                "compared_effects": row["compared_effects"],
                "original_observation_sha256": row["original_observation_sha256"],
                "candidate_observation_sha256": row["candidate_observation_sha256"]}
        if not cmp.equal:
            failures.append(behavior_ledger._json_value({"index": i, "label": case.label, "diff": cmp.diff,
                             "original": cmp.original, "candidate": cmp.candidate}))
            if len(failures) >= 20:
                break
    ran = failures[-1]["index"] + 1 if failures else len(cases)
    ledger_report = ledger.finalize()
    result = {"schema": "behavior-suite-run-v1", "suite": SUITE, "function": target,
        **pair.identity, "candidate_strict": pair.strict.get("claims", {}).get(target, {}),
        "module_peers_and_data": "passed PreparedPair strict whole-module peer/private-data gates",
        "cases_generated": len(cases), "cases_run": ran, "directed_cases": sum(c.label.startswith(("directed/", "boundary/")) for c in cases[:ran]),
        "randomized_cases": sum(c.label.startswith("random/") for c in cases[:ran]), "mismatches": len(failures), "failures": failures,
        "compared_effects": effects, "case_ledger": ledger_report,
        "helper_call_counts": helper_counts,
        "seed": seed, "elapsed_seconds": round(time.time() - started, 3),
        "behavioral_status": "UNRESOLVED; evidence pending supervisor contract review"}
    if target in ("DrawMapCursor", "InvertPatch", "f_0250_1018", "f_0250_129E", "DrawBalloons", "win_DrawBitMap"):
        snapshot_dir = outdir / "source-snapshots"
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        snapshot = snapshot_dir / ("DrawBalloons.c" if target == "DrawBalloons" else
            "m259D.c" if target == "win_DrawBitMap" else f"{target}.c")
        shutil.copyfile(pair.source, snapshot)
        suite_hash = behavior.digest(Path(__file__).read_bytes())
        module = f'{pair.identity["address"]["unit"]}:{pair.identity["address"]["seg"]:04X}'
        helper_specs = _helper_boundary_specs(target, pair, helper_counts, first_positive)
        ledger_identity = {"path": (outdir / f"{target}.cases.jsonl.gz").resolve().relative_to(ROOT).as_posix(),
            "sha256": ledger_report["sha256"], "row_count": ledger_report["row_count"],
            "lane_counts": ledger_report["lane_counts"], "compression": ledger_report["compression"],
            "identity": ledger_report["identity"]}
        run_evidence = {
            "schema": "behavior-run-evidence-v1",
            "completion": "COMPLETE" if ran == len(cases) and not failures else "INCOMPLETE",
            "identity": {"function": target, "suite_id": SUITE, "module": module,
                "address": pair.identity["address"], "source_sha256": pair.identity["source_sha256"],
                "compiled_source_sha256": pair.identity["compiled_source_sha256"],
                "suite_sha256": suite_hash, "harness_sha256": pair.identity["harness_sha256"],
                "oracle_sha256": pair.identity["oracle_sha256"],
                "historical_manifest_sha256": pair.identity["manifest_sha256"],
                "object_sha256": pair.identity["object_sha256"],
                "profile": pair.identity["profile"], "flags": pair.identity["flags"]},
            "execution": {"engine": "PreparedPair.compare", "actual_original_execution": True,
                "actual_candidate_execution": True, "original_exe_sha256": pair.identity["oracle_sha256"]},
            "cases": {lane: {"generated": sum(1 for c in cases if
                    (c.label.startswith("random/") if lane == "randomized" else not c.label.startswith("random/"))),
                    "executed": lane_counts[lane], "actual_original_invocations": lane_counts[lane],
                    "actual_candidate_invocations": lane_counts[lane],
                    "seeds": [seed] if lane == "randomized" and count else []}
                    for lane in ("directed", "randomized")},
            "errors": 0, "mismatches": len(failures), "compared_effects": effects,
            "case_ledger": ledger_identity, "unmodeled_boundaries": 0,
            "peer_data_gates": "PASS", "positive_controls": [first_positive] if first_positive else [],
            "helper_boundaries": helper_specs,
            "source_snapshot": {"path": snapshot.resolve().relative_to(ROOT).as_posix(),
                                "sha256": behavior.digest(snapshot.read_bytes())},
            "helper_boundary_plan": f"{target}.helper-boundary-plan.json",
            "coverage": _coverage_summary(target, cases),
        }
        plan_path = _write_helper_plan(target, run_evidence, outdir)
        run_evidence["helper_boundary_plan_sha256"] = behavior.digest(plan_path.read_bytes())
        evidence_path = outdir / f"{target}.run-evidence.json"
        evidence_path.write_text(json.dumps(run_evidence, indent=2) + "\n")
        result["suite_sha256"] = suite_hash
        result["run_evidence"] = evidence_path.resolve().relative_to(ROOT).as_posix()
        result["helper_boundary_plan"] = run_evidence["helper_boundary_plan"]
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / f"{target}.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def negative_controls(outdir, targets=None):
    """Compile one-source mutants and require the paired oracle to detect each."""
    seed_dir = ROOT / "work/takeover/hardtail/seeds"
    specs = [
        ("DrawMapCursor", "S12_384C_daa607847c4c.c",
         "fd_50F6_38C2.left = fd_50F6_3856 * fd_50F6_0508[0] + fd_50F6_10D2.left + fd_50F6_38C0;",
         "fd_50F6_38C2.left = fd_50F6_3856 * fd_50F6_0508[1] + fd_50F6_10D2.left + fd_50F6_38C0;",
         _map_cursor_case("negative/cursor-offset", 5, 9, 21, 17, 4, 8, 11, -7, 23,
                          window="open")),
        ("InvertPatch", "S13_384C_1ace9a298569.c",
         "h = (h >> 1) + fd_50F6_10D2.left + 4;",
         "h = (h >> 1) + fd_50F6_10D2.left + 5;",
         _invert_case("negative/patch-point", 4, 7, -12, 9, 320)),
        ("f_0250_1018", "root_0250_e41a4ab8c56c.c",
         "if (v > 0x10)",
         "if (v >= 0x10)",
         _mapdata_case("negative/life-zero", "f_0250_1018", 3, 4, 0, 0, 0x42, 0, pher=0x10)),
        ("f_0250_129E", "root_0250_e41a4ab8c56c.c",
         "if (g_9126)\n            f_0250_0721",
         "if (!g_9126)\n            f_0250_0721",
         _mapdata_case("negative/draw-kind", "f_0250_129E", 3, 4, 0, 0, 0x42, 1, cache=-1)),
    ]
    if targets is not None:
        specs = [spec for spec in specs if spec[0] in set(targets)]
    rows = []
    by_target = {}
    baselines = {}
    for target, filename, old, new, case in specs:
        source_path = seed_dir / filename
        source = source_path.read_text(encoding="latin1")
        baseline_pair = baselines.get(target)
        if baseline_pair is None:
            baseline_pair = behavior.PreparedPair(target, source=source_path,
                out=outdir / "negative" / f"{target}-baseline")
            baselines[target] = baseline_pair
        baseline = baseline_pair.compare(case)
        if not baseline.equal:
            raise AssertionError(f"negative-control baseline did not match {target}: {baseline.diff}")
        if source.count(old) != 1:
            raise RuntimeError(f"negative-control source anchor not unique for {target}: {source.count(old)}")
        mutant = outdir / "negative" / f"{target}.c"
        mutant.parent.mkdir(parents=True, exist_ok=True)
        mutant.write_text(source.replace(old, new, 1), encoding="latin1")
        pair = behavior.PreparedPair(target, source=mutant, out=outdir / "negative" / target)
        cmp = pair.compare(case)
        mutant_hash = behavior.digest(mutant.read_bytes())
        object_path = outdir / "negative" / target / "candidate.obj"
        row = {"id": case.label, "target": target,
               "executed": True, "detected_mismatch": not cmp.equal,
               "original_executed": True, "mutant_executed": True,
               "baseline_matches": baseline.equal, "mutant_differs": not cmp.equal,
               "execution_errors": 0, "mismatch_categories": sorted(cmp.diff.keys()),
               "mutant_source_sha256": mutant_hash,
               "mutant_source": {"path": mutant.resolve().relative_to(ROOT).as_posix(), "sha256": mutant_hash},
               "mutant_object": {"path": object_path.resolve().relative_to(ROOT).as_posix(),
                                 "sha256": behavior.digest(object_path.read_bytes())},
               "baseline_object_sha256": baseline_pair.identity["object_sha256"],
               "diff": behavior_ledger._json_value(cmp.diff)}
        rows.append(row)
        by_target.setdefault(target, []).append(row)
        if cmp.equal:
            raise AssertionError(f"behavior observations failed to detect negative control: {target}")
    (outdir / "negative-controls.json").write_text(json.dumps(rows, indent=2) + "\n")
    for target, controls in by_target.items():
        baseline_pair = baselines[target]
        report = {"schema": "behavior-negative-controls-v1", "function": target,
                  "suite_id": SUITE, "errors": 0,
                  "mismatches_detected": sum(c["detected_mismatch"] for c in controls),
                  "identity": {"source_sha256": baseline_pair.identity["source_sha256"],
                               "oracle_sha256": baseline_pair.identity["oracle_sha256"],
                               "harness_sha256": baseline_pair.identity["harness_sha256"],
                               "historical_manifest_sha256": baseline_pair.identity["manifest_sha256"]},
                  "baseline": {"equal": True, "source_sha256": baseline_pair.identity["source_sha256"],
                               "object_sha256": baseline_pair.identity["object_sha256"],
                               "oracle_sha256": baseline_pair.identity["oracle_sha256"]},
                  "controls": controls}
        neg_path = outdir / f"{target}.negative-controls.json"
        neg_path.write_text(json.dumps(report, indent=2) + "\n")
        evidence_path = outdir / f"{target}.run-evidence.json"
        evidence = json.loads(evidence_path.read_text())
        report_ref = {"path": neg_path.resolve().relative_to(ROOT).as_posix(),
                      "sha256": behavior.digest(neg_path.read_bytes())}
        evidence["negative_controls"] = report_ref
        plan = json.loads((outdir / evidence["helper_boundary_plan"]).read_text())
        plan["negative_control_reports"] = [report_ref]
        ids = [c["id"] for c in controls]
        for helper in evidence["helper_boundaries"]:
            cert = helper.get("certification")
            if isinstance(cert, dict) and cert.get("status") == "PENDING_SUPERVISOR_REVIEW":
                cert["negative_control_ids"] = ids
        plan["helpers"] = evidence["helper_boundaries"]
        plan_path = outdir / evidence["helper_boundary_plan"]
        plan_path.write_text(json.dumps(plan, indent=2) + "\n")
        evidence["helper_boundary_plan_sha256"] = behavior.digest(plan_path.read_bytes())
        evidence_path.write_text(json.dumps(evidence, indent=2) + "\n")
    return rows


def resource_negative_controls(outdir):
    """Exercise width, pixel-address, and host-call-order sensitivities."""
    catalog = json.loads((ROOT / "work/takeover/hardtail/catalog.json").read_text())
    balloon_source = ROOT / next(r["best_source"] for r in catalog["records"]
                                 if r["function"] == "DrawBalloons")
    bitmap_source = ROOT / "src/root/m259D.c"
    specs = [
        ("DrawBalloons", "width-increment", balloon_source,
         "wpix = g_19BE * wt;", "wpix = g_19BE * wt + 1;",
         balloon_cases()[0]),
        ("DrawBalloons", "buffer-destination-offset", balloon_source,
         "dst = bufp + 4;", "dst = bufp + 6;",
         balloon_cases()[0]),
        ("win_DrawBitMap", "pixel-source-offset", bitmap_source,
        "f_1B4E_003B(x, y, (char far *)pic + 8);", "f_1B4E_003B(x, y, (char far *)pic + 9);",
         bitmap_cases()[3]),
        ("win_DrawBitMap", "draw-release-order", bitmap_source,
         "GPutPacked(x, y, (char far *)pic);\n            db_ReleaseObject(id, 2);",
         "db_ReleaseObject(id, 2);\n            GPutPacked(x, y, (char far *)pic);",
         bitmap_cases()[1]),
    ]
    rows = []
    baselines = {}
    by_target = {}
    for index, (target, control_name, source_path, old, new, case) in enumerate(specs):
        base_pair = baselines.get(target)
        if base_pair is None:
            base_pair = behavior.PreparedPair(target, source=source_path,
                out=outdir / "negative" / f"{target}-baseline")
            baselines[target] = base_pair
        baseline = base_pair.compare(case)
        if not baseline.equal:
            raise AssertionError(f"resource negative baseline did not match {target}: {baseline.diff}")
        source = source_path.read_text(encoding="latin1")
        import re
        sig = re.search(r"^[^\n;]*\b" + re.escape(target) + r"\s*\([^;]*?\)\s*\{", source, re.M)
        if not sig:
            raise RuntimeError(f"cannot locate resource negative definition {target}")
        start = sig.end() - 1
        depth = 0
        end = None
        for pos in range(start, len(source)):
            if source[pos] == "{": depth += 1
            elif source[pos] == "}":
                depth -= 1
                if depth == 0:
                    end = pos + 1
                    break
        if end is None:
            raise RuntimeError(f"unterminated resource negative definition {target}")
        body = source[start:end]
        if body.count(old) != 1:
            raise RuntimeError(f"resource negative anchor not unique in {target}: {body.count(old)} {old!r}")
        mutant = outdir / "negative" / f"{target}-resource-{index}.c"
        mutant.parent.mkdir(parents=True, exist_ok=True)
        mutant.write_text(source[:start] + body.replace(old, new, 1) + source[end:], encoding="latin1")
        pair = behavior.PreparedPair(target, source=mutant, out=outdir / "negative" / f"{target}-resource-{index}")
        cmp = pair.compare(case)
        source_hash = behavior.digest(mutant.read_bytes())
        obj_path = outdir / "negative" / f"{target}-resource-{index}" / "candidate.obj"
        if not obj_path.is_file():
            raise RuntimeError(f"negative-control object was not retained for {target}: {obj_path}")
        row = {"id": f"{target}/{control_name}", "target": target,
               "executed": True, "detected_mismatch": not cmp.equal,
               "original_executed": True, "mutant_executed": True,
               "baseline_matches": baseline.equal, "mutant_differs": not cmp.equal,
               "execution_errors": 0, "mismatch_categories": sorted(cmp.diff.keys()),
               "mutant_source_sha256": source_hash,
               "mutant_source": {"path": mutant.resolve().relative_to(ROOT).as_posix(), "sha256": source_hash},
               "mutant_object": {"path": obj_path.resolve().relative_to(ROOT).as_posix(),
                                 "sha256": behavior.digest(obj_path.read_bytes())},
               "baseline_object_sha256": base_pair.identity["object_sha256"],
               "diff": behavior_ledger._json_value(cmp.diff)}
        rows.append(row)
        by_target.setdefault(target, []).append(row)
        if cmp.equal:
            raise AssertionError(f"resource behavior observations missed negative control: {target} {case.label}")
    (outdir / "resource-negative-controls.json").write_text(json.dumps(rows, indent=2) + "\n")
    for target, controls in by_target.items():
        baseline_pair = baselines[target]
        report = {"schema": "behavior-negative-controls-v1", "function": target,
                  "suite_id": SUITE, "errors": 0,
                  "mismatches_detected": sum(c["detected_mismatch"] for c in controls),
                  "identity": {"source_sha256": baseline_pair.identity["source_sha256"],
                               "oracle_sha256": baseline_pair.identity["oracle_sha256"],
                               "harness_sha256": baseline_pair.identity["harness_sha256"],
                               "historical_manifest_sha256": baseline_pair.identity["manifest_sha256"]},
                  "baseline": {"equal": True, "source_sha256": baseline_pair.identity["source_sha256"],
                               "object_sha256": baseline_pair.identity["object_sha256"],
                               "oracle_sha256": baseline_pair.identity["oracle_sha256"]},
                  "controls": controls}
        neg_path = outdir / f"{target}.negative-controls.json"
        neg_path.write_text(json.dumps(report, indent=2) + "\n")
        evidence_path = outdir / f"{target}.run-evidence.json"
        evidence = json.loads(evidence_path.read_text())
        report_ref = {"path": neg_path.resolve().relative_to(ROOT).as_posix(),
                      "sha256": behavior.digest(neg_path.read_bytes())}
        evidence["negative_controls"] = report_ref
        plan = json.loads((outdir / evidence["helper_boundary_plan"]).read_text())
        plan["negative_control_reports"] = [report_ref]
        ids = [c["id"] for c in controls]
        for helper in evidence["helper_boundaries"]:
            cert = helper.get("certification")
            if isinstance(cert, dict) and cert.get("status") == "PENDING_SUPERVISOR_REVIEW":
                cert["negative_control_ids"] = ids
        plan["helpers"] = evidence["helper_boundaries"]
        plan_path = outdir / evidence["helper_boundary_plan"]
        plan_path.write_text(json.dumps(plan, indent=2) + "\n")
        evidence["helper_boundary_plan_sha256"] = behavior.digest(plan_path.read_bytes())
        evidence_path.write_text(json.dumps(evidence, indent=2) + "\n")
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", type=int, default=500)
    ap.add_argument("--seed", type=lambda x: int(x, 0), default=0xBEEF)
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--targets", nargs="+", choices=["DrawMapCursor", "InvertPatch", "f_0250_1018", "f_0250_129E", "DrawBalloons", "win_DrawBitMap"],
                    default=["DrawMapCursor", "InvertPatch", "f_0250_1018", "f_0250_129E"])
    args = ap.parse_args()
    outdir = args.out if args.out.is_absolute() else ROOT / args.out
    outdir.mkdir(parents=True, exist_ok=True)
    gens = {"DrawMapCursor": map_cursor_cases, "InvertPatch": invert_cases,
            "f_0250_1018": lambda n, s: map_cell_cases("f_0250_1018", n, s),
            "f_0250_129E": lambda n, s: map_cell_cases("f_0250_129E", n, s),
            "DrawBalloons": balloon_cases,
            "win_DrawBitMap": bitmap_cases}
    results = []
    for target in args.targets:
        source = ROOT / "src/root/m259D.c" if target == "win_DrawBitMap" else None
        results.append(_run_target(target, gens[target], args.count, args.seed, outdir, source))
    negatives = negative_controls(outdir) if all(t in args.targets for t in ("DrawMapCursor", "InvertPatch", "f_0250_1018", "f_0250_129E")) else []
    resource_negatives = resource_negative_controls(outdir) if all(t in args.targets for t in ("DrawBalloons", "win_DrawBitMap")) else []
    (outdir / "summary.json").write_text(json.dumps({"suite": SUITE, "results": results,
                                                    "negative_controls": negatives,
                                                    "resource_negative_controls": resource_negatives}, indent=2) + "\n")
    print(json.dumps({"functions": len(results), "cases_run": sum(r["cases_run"] for r in results),
                      "mismatches": sum(r["mismatches"] for r in results),
                      "negative_controls_detected": sum(r.get("detected", r.get("detected_mismatch", False))
                                                          for r in negatives + resource_negatives),
                      "reports": [str((outdir / (r["function"] + ".json")).relative_to(ROOT)) for r in results]}, indent=2))


if __name__ == "__main__":
    main()
