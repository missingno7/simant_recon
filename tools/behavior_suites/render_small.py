"""Bounded original-DOS differential contracts for small rendering routines.

All candidate code is compiled from the current canonical whole module and runs beside
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

ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'layout/functions.json').is_file())

import behavior
import behavior_ledger
from behavior_suites import lists as lists_suite
from behavior_suites import memory as memory_suite

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
    writes = [
        (b.symbol_address("fd_50F6_0508"), _w(xorigin) + _w(yorigin)),
        (b.symbol_address("fd_50F6_10D2"), _w(left) + _w(top) + _w(left + 320) + _w(top + 200)),
        (b.symbol_address("fd_50F6_3856"), _w(sx)),
        (b.symbol_address("fd_50F6_3858"), _w(sy)),
        (b.symbol_address("fd_50F6_38C0"), _w(offset)),
        (b.symbol_address("fd_50F6_10E0"), _w(width)),
        (b.symbol_address("fd_50F6_10DE"), _w(height)),
    ]
    callbacks = {
        "f_22BF_09B0": _callback(handler=_window, regs=("cx",)),
        "clip_Push": _callback(handler=_noop),
        "clip_SetWin": _callback(1, _noop),
        "clip_Pop": _callback(handler=_noop),
        "f_1CE2_0410": _callback(3, _noop, project=_capture_rect),
    }
    return b.Case(label, writes=writes,
                  observe=[_range("fd_50F6_38C2", 8)],
                  callbacks=callbacks, return_kind="void",
                  state={"window_open": window},
                  metadata={"suite": SUITE, "contract": "DrawMapCursor ordered clip/draw boundary trace, semantic Rect pointer and cursor state", "host_boundary": "f_22BF_09B0 window query; clip calls; f_1CE2_0410 XOR rectangle"})


def map_cursor_cases(random_count=1000, seed=0xC012):
    cases = []
    for draw in (True,):
        for window in (False, True):
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
            rng.randrange(-500, 501), rng.randrange(-500, 501), rng.randrange(-32768, 32768), bool(rng.randrange(2)), bool(rng.randrange(2))))
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
    next_linear = machine.state.get("malloc_next_linear", 0xC1000)
    linear = (next_linear + 15) & ~15
    if linear + size >= 0xD0000:
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
    handle_off = memory_suite.MASTER_FIRST
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
        b.Range("handle_table", memory_suite.HANDLE_SEG * 16 + memory_suite.MASTER_START,
                memory_suite.MASTER_CAPACITY * 4),
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
    handle = (memory_suite.MASTER_FIRST, memory_suite.HANDLE_SEG)
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
            b.Range("handle_table", memory_suite.HANDLE_SEG * 16 + memory_suite.MASTER_START,
                    memory_suite.MASTER_CAPACITY * 4),
            _range("g_5A97", 1), b.Range("screen_size_callback", b.symbol_address("g_9140"), 4),
            b.Range("screen_copy_callback", b.symbol_address("g_9148"), 4)],
        callbacks=callbacks, return_kind="s16",
        state={"resource_handle": handle, "resource_available": available, "display": display,
               "picture_bytes": picture.hex(), "picture_length": len(picture), "pixel_length": len(pixels),
               "format_commands": [], "resource_requests": [], "resource_releases": [],
               "screen_read_rectangles": [], "screen_pixel_captures": [],
               "scratch_allocations": [], "scratch_releases": [],
               "temp_buffer": None, "temp_buffer_size": 0, "malloc_next_linear": 0xC1000},
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
















