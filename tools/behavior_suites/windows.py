"""Bounded DOS window/object differential fixtures.

The suite executes original DOS routines against a separately compiled whole
module. Small deterministic window services stand in for the window manager;
their contracts are recorded in each case and are not proof of manager behavior.
"""
from __future__ import annotations

import argparse
import json
import random
import struct
import sys
import time
from pathlib import Path
from dataclasses import replace

_HERE = Path(__file__).resolve()
ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'layout/functions.json').is_file())

import behavior

from behavior_suites import memory as memory_suite
from behavior_ledger import CaseLedger

SUITE = "windows_v1"
DATA_SEG = 0xA000
OBJ_OFF = 0x1000
RECT_OFF = 0x2000
WIN_OFF = 0x3000
WIN_ID = 0x0100


def w(*values):
    return struct.pack("<" + "H" * len(values), *(x & 0xFFFF for x in values))


def farptr(off, seg=DATA_SEG):
    return struct.pack("<HH", off & 0xFFFF, seg & 0xFFFF)


def rng(name, size):
    return behavior.Range(name, behavior.symbol_address(name), size)


def _write_word(address, value):
    return address, w(value)


def _registers(ax=0, dx=0, bx=0xA51E, cx=0xC3D2, si=0x5A17, di=0xD1A0):
    return {"ax": ax, "dx": dx, "bx": bx, "cx": cx,
            "si": si, "di": di, "bp": 0xBEEF, "es": 0xCAFE}


def _window_services():
    """Synthetic lock/object services. AX is the fastcall word argument."""
    def lock(machine, args):
        machine.state["lock_depth"] = machine.state.get("lock_depth", 0) + 1

    def unlock(machine, args):
        machine.state["lock_depth"] = machine.state.get("lock_depth", 0) - 1

    def object_addr(machine, args):
        return (OBJ_OFF + 0x100, DATA_SEG)

    def window_addr(machine, args):
        return (WIN_OFF, DATA_SEG)

    def recalc(machine, args):
        # Record ordered recalculation requests. Actual layout constraints and
        # dependency resolution in the DOS window manager remain out of scope.
        machine.state.setdefault("recalc", []).append(args[0] & 0xFFFF)

    return {
        "win_LockWin": behavior.Callback(0, lock, ("ax",)),
        "win_UnlockWin": behavior.Callback(0, unlock, ("ax",)),
        "f_2505_02D7": behavior.Callback(0, object_addr, ("ax",)),
        "win_ObjAddr": behavior.Callback(0, object_addr, ("ax",)),
        "f_2505_0006": behavior.Callback(1, window_addr),
        "win_Recalc": behavior.Callback(0, recalc, ("ax",)),
    }


def coordinate_case(label, modes, refs, initial, rect, obj=WIN_ID):
    obj_linear = DATA_SEG * 16 + OBJ_OFF + 0x100
    rect_linear = DATA_SEG * 16 + RECT_OFF
    # f_20E8_0903 treats obj[0..3], origin[0..3], ref[0..3], mode[0..3]
    # as four words each. Initialize extra object bytes to expose accidental
    # unrelated writes as part of the full object-state boundary.
    fields = list(initial) + [0x1111] * 4 + list(refs) + list(modes) + [0x5A5A] * 20
    return behavior.Case(
        label=label, args=[RECT_OFF, DATA_SEG],
        writes=[(obj_linear, w(*fields)), (rect_linear, w(*rect))],
        observe=[behavior.Range("object", obj_linear, 64),
                 behavior.Range("input_rect", rect_linear, 8)],
        callbacks=_window_services(), return_kind="void", callee_pop=4,
        registers=_registers(ax=obj), state={"lock_depth": 0, "recalc": []},
        metadata={"suite": SUITE, "contract": "f_20E8_0903 origin fields, complete object bytes, input rectangle, ordered recalculations and lock balance",
                  "abi": "AX=obj; stack far pointer rect; observed original retf 4",
                  "helper_policy": "win_LockWin/win_UnlockWin/win_ObjAddr/win_Recalc use deterministic synthetic services; callback traces expose all calls; recalc only records the request and does not implement dependency resolution",
                  "validity": "object/window index 1, fixed in-range 4-word object and rectangle"})


def coordinate_cases(random_count=1500, seed=0x20080903):
    cases = []
    # Cover all edge modes, self references, non-self references, and the
    # special mode 5 that suppresses the first conditional.
    mode_values = (0, 1, 2, 4, 5, 6, 0x7FFF, 0xFFFF)
    for i, modes in enumerate((
        (0, 0, 0, 0), (1, 2, 5, 6), (5, 5, 5, 5),
        (1, 1, 1, 1), (0xFFFF, 2, 0, 5),
    )):
        refs = (WIN_ID, WIN_ID, WIN_ID, WIN_ID)
        initial = (10, 20, 210, 220)
        rect = (0, 0, 320, 200)
        cases.append(coordinate_case(f"directed/{i}", modes, refs, initial, rect))
    # Full Cartesian sweep of a compact semantic domain for every edge slot.
    for edge in range(4):
        for mode in mode_values:
            modes = [0, 0, 0, 0]; modes[edge] = mode
            for self_ref in (False, True):
                refs = [WIN_ID + 1] * 4
                refs[edge] = WIN_ID if self_ref else WIN_ID + 1
                for delta in (-32768, -1, 0, 1, 32767):
                    initial = [32, 24, 256, 176]
                    rect = [0, 0, 0, 0]
                    rect[edge] = (initial[edge] + delta) & 0xFFFF
                    rect[edge] = rect[edge] - 0x10000 if rect[edge] & 0x8000 else rect[edge]
                    cases.append(coordinate_case(
                        f"grid/e{edge}/m{mode:04x}/self{int(self_ref)}/d{delta}",
                        modes, refs, initial, rect))
    rngg = random.Random(seed)
    for i in range(random_count):
        modes = tuple(rngg.choice(mode_values) for _ in range(4))
        refs = tuple(WIN_ID if rngg.randrange(2) else WIN_ID + rngg.randrange(1, 8)
                     for _ in range(4))
        initial = tuple(rngg.randrange(-2048, 2049) for _ in range(4))
        rect = tuple(rngg.randrange(-2048, 2049) for _ in range(4))
        cases.append(coordinate_case(f"random/{seed:08x}/{i}", modes, refs, initial, rect))
    return cases


def _field_service_fixture(label, obj_index, kind, count, fields):
    win_linear = DATA_SEG * 16 + WIN_OFF
    table_off = WIN_OFF + 0x100
    values_off = WIN_OFF + 0x200
    # Window header count at +0x0c, far object-pointer list at +0x2c.
    win = bytearray(0x100)
    win[0x0C:0x0E] = w(count)
    win[0x2C:0x30] = farptr(table_off)
    table = bytearray(max(count, 1) * 4)
    object_data = bytearray(max(count, 1) * 0x40)
    for idx in range(max(count, 1)):
        off = values_off + idx * 0x40
        table[idx * 4:idx * 4 + 4] = farptr(off)
        source = fields[idx * 16:(idx + 1) * 16]
        encoded = w(*source)
        object_data[idx * 0x40:idx * 0x40 + len(encoded)] = encoded
    return behavior.Case(
        label=label, args=[],
        writes=[(win_linear, bytes(win)), (DATA_SEG * 16 + table_off, bytes(table)),
                (DATA_SEG * 16 + values_off, bytes(object_data)),
                _write_word(behavior.symbol_address("win_numOfWindows"), 8)],
        observe=[behavior.Range("window_header", win_linear, 0x40),
                 behavior.Range("object_pointer_table", DATA_SEG * 16 + table_off, len(table)),
                 behavior.Range("field_values", DATA_SEG * 16 + values_off, len(object_data))],
        callbacks=_window_services(), return_kind="s16", registers=_registers(
            ax=(WIN_ID | obj_index), dx=kind),
        state={"lock_depth": 0},
        metadata={"suite": SUITE, "contract": "f_2505_0453 indexed word result or 0x8000 sentinel, complete synthetic window header and lock trace",
                  "abi": "fastcall: AX=obj, DX=kind; target retf with no immediate stack pop",
                  "helper_policy": "win_LockWin/win_UnlockWin and f_2505_0006 are deterministic synthetic host services; candidate/original field dereference runs normally",
                  "validity": "window 1 with a valid object pointer table; count and index selected by case"})


def field_cases(random_count=600, seed=0x25050453):
    cases = []
    for count in range(0, 5):
        for idx in range(0, 6):
            for kind in range(0, 4):
                values = [((n * 997 + 0x80FF) & 0xFFFF)
                          for n in range(16 * max(count, 1))]
                cases.append(_field_service_fixture(
                    f"directed/n{count}/i{idx}/k{kind}", idx, kind, count, values))
    rngg = random.Random(seed)
    for i in range(random_count):
        count = rngg.randrange(0, 12)
        idx = rngg.randrange(0, 16)
        kind = rngg.randrange(0, 4)
        fields = [rngg.randrange(65536) for _ in range(16 * max(count, 1))]
        cases.append(_field_service_fixture(f"random/{seed:08x}/{i}", idx, kind, count, fields))
    return cases


def unlock_case(label, lock_depth, flags, count=0):
    # This suite currently exercises the non-final nested-unlock path. It does
    # not assert behavior of the release/update branch, which needs valid heap
    # handles, allocator state, object arrays, and the window-offset DGROUP.
    # These are private DGROUP words whose absolute offsets are directly used
    # by the original disassembly: g_8DA6=8DA6, g_8CF2=8CF2,
    # win_handles=9230. Keep them as named fixture constants here.
    dgroup = behavior.match.DGROUP_SEG * 16
    locks = dgroup + 0x8DA6
    handles = dgroup + 0x9230
    g8cf2 = dgroup + 0x8CF2
    return behavior.Case(
        label=label, args=[], writes=[(dgroup + 0x644C, w(1)),
                                      (dgroup + 0x644E, w(0)),
                                      (locks + 1, bytes([lock_depth & 0xFF])),
                                      (handles + 4, farptr(WIN_OFF)),
                                      (DATA_SEG * 16 + WIN_OFF, farptr(OBJ_OFF))],
        observe=[behavior.Range("g_644C", dgroup + 0x644C, 2),
                 behavior.Range("g_644E", dgroup + 0x644E, 2),
                 behavior.Range("g_8DA6", locks, 45),
                 behavior.Range("g_8CF2", g8cf2, 90),
                 behavior.Range("win_handles", handles, 180)],
        callbacks={"f_171C_1686": behavior.Callback(2, lambda m, a: 0),
                   "f_171C_2086": behavior.Callback(2, lambda m, a: None)},
        return_kind="void", registers=_registers(ax=WIN_ID), state={},
        metadata={"suite": SUITE, "contract": "nested unlock decrements lock count without entering final release branch",
                  "abi": "fastcall: AX=window; target retf with no immediate stack pop",
                  "helper_policy": "f_171C_1686 reports non-discarded handle; f_171C_2086 is trace-only; only depth > 1 is a valid bounded fixture",
                  "validity": "g_644C enabled; lock byte starts above one; final release path intentionally not reached"})


def unlock_live_case(label, object_types=(0,), window_flags=0x800, redraw_pending=0):
    """Final-release unlock over a real Ralloc tree and supported object slots."""
    arena_seg, master_seg, master_top, heap_paras = 0xA100, 0xA000, 0x0100, 0x700
    rows = [(16, 1, {"size": 224, "lock": 1, "name": b"window"})]
    rows.extend((4, 1, {"size": 32, "lock": 0, "name": f"child{i}".encode()})
                for i in range(len(object_types)))
    rows.append((heap_paras - 16 - 4 * len(object_types), 0x80))
    handle_ids = list(range(1 + len(object_types)))
    old = (memory_suite.HEAP_SEG, memory_suite.HANDLE_SEG,
           memory_suite.MASTER_FIRST, memory_suite.MASTER_ONE_PAST,
           memory_suite.HEAP_PARAS)
    memory_suite.HEAP_SEG, memory_suite.HANDLE_SEG = arena_seg, master_seg
    memory_suite.MASTER_FIRST, memory_suite.MASTER_ONE_PAST = master_top, master_top + 4
    memory_suite.HEAP_PARAS = heap_paras
    try:
        arena = memory_suite.heap_case(
            f"{label}/real-ralloc-tree", rows, handles=handle_ids,
            contract="valid window handle, optional nested object handles, and linked free-list tail")
    finally:
        (memory_suite.HEAP_SEG, memory_suite.HANDLE_SEG,
         memory_suite.MASTER_FIRST, memory_suite.MASTER_ONE_PAST,
         memory_suite.HEAP_PARAS) = old
    dg = behavior.match.DGROUP_SEG * 16
    handle_entry = dg + 0x9230 + 4  # win_handles[1]
    lock_entry = dg + 0x8DA6 + 1   # window 1 lock depth
    block_data_seg = arena_seg + 2
    window_data = bytearray(max(0x40, 0x2C + 4 * len(object_types)))
    window_data[0:8] = w(0, 0, 640, 400)
    window_data[0x0C:0x0E] = w(len(object_types))
    # The DOS field is a word at +1C; the release branch tests its high byte
    # at +1D for flags 0x0200/0x0800.
    window_data[0x1C:0x1E] = w(window_flags)
    # The first live handle is the master-table slot at MASTER_FIRST (0100);
    # subsequent object handles descend through 00FC, 00F8, ... .
    window_handle = farptr(master_top, master_seg)
    object_map = bytearray(0x100)
    object_writes = []
    for i, kind in enumerate(object_types):
        obj_off = 0x4100 + i * 0x60
        window_data[0x2C + i * 4:0x30 + i * 4] = farptr(obj_off, master_seg)
        object_map[i * 4:i * 4 + 4] = farptr(obj_off, master_seg)
        obj = bytearray(0x40)
        obj[0x21] = kind & 0xFF
        obj[8:16] = w(0x1111 + i, 0x2222 + i, 0x3333 + i, 0x4444 + i)
        if kind in (4, 10):
            ptr_off = 0x34
        elif kind in (16, 17, 18):
            ptr_off = 0x2A
        else:
            ptr_off = None
        if ptr_off is not None:
            # Ralloc object handle is the actual master slot pointer.
            hslot = master_top - 4 * (i + 1)
            obj[ptr_off:ptr_off + 4] = farptr(hslot, master_seg)
        object_writes.append((master_seg * 16 + obj_off, bytes(obj)))
    object_map[0x40:0x48] = w(0x1111, 0x2222, 0x3333, 0x4444)
    writes = list(arena.writes) + [
        (dg + 0x644C, w(1)), (dg + 0x644E, w(redraw_pending)),
        (lock_entry, bytes([1])), (handle_entry, window_handle),
        (dg + 0x8A3A, w(master_seg)),
        (block_data_seg * 16, bytes(window_data)),
        (master_seg * 16 + 0x3000, bytes(object_map)),
    ] + object_writes
    return behavior.Case(
        label=label, args=[], writes=writes,
        observe=[r for r in arena.observe if r.name not in ("heap", "handle_table")] + [
            behavior.Range("win_unlock_globals", dg + 0x644C, 4),
            behavior.Range("window_lock_counts", dg + 0x8DA6, 45),
            behavior.Range("window_handles", dg + 0x9230, 180),
            behavior.Range("window_data", block_data_seg * 16, len(window_data)),
            behavior.Range("map_copy", master_seg * 16 + 0x4892, 16),
            behavior.Range("object_array_map", master_seg * 16 + 0x3000, 0x100),
            behavior.Range("objects", master_seg * 16 + 0x4100, max(0x40, 0x60 * len(object_types))),
            behavior.Range("all_clip_handles", behavior.symbol_address("fd_50F6_3B60"), 45 * 4),
        ], callbacks={}, return_kind="void", registers=_registers(ax=WIN_ID),
        metadata={"suite": SUITE,
                  "contract": "final-release win_UnlockWin branch with original Ralloc type lookup, lock decrement, free, unlock, type update, globals, and map copy",
                  "abi": "fastcall AX=window; target retf with no immediate stack pop",
                  "helper_policy": "f_171C_1686, f_171C_13E4, f_171C_2086 and f_171C_20E2 execute actual DOS code; no mocked allocator callbacks",
                  "validity": {"handle": "real master slot pointer A000:00FC",
                               "block_data": f"{block_data_seg:04x}:0000", "window": 1,
                               "Ralloc_block": "firm type 1, lock count 1, valid linked free tail",
                               "object_types": list(object_types), "window_flags": window_flags,
                               "redraw_pending": redraw_pending, "window_map_source": "A000:3000"}})


def randomized_unlock_cases(count=200, seed=0x23AE01DB):
    rr = random.Random(seed)
    supported = (4, 10, 16, 17, 18)
    flags = (0, 0x200, 0x800, 0xA00)
    return [unlock_live_case(
        f"random/{seed:08x}/{i}",
        tuple(rr.choice((*supported, 0, 2, 19)) for _ in range(rr.randrange(1, 9))),
        window_flags=rr.choice(flags), redraw_pending=rr.randrange(2))
        for i in range(count)]


def clip_empty_case(label):
    # A valid empty stack takes the original early return after freeing/resetting
    # any current clip handles. Seed the handles to null so no allocator calls
    # are needed and compare the full window stack plus clip globals.
    g5702 = behavior.symbol_address("g_5702")
    g5742 = behavior.symbol_address("g_5742")
    g5746 = behavior.symbol_address("g_5746")
    g574a = behavior.symbol_address("g_574A")
    g5aac = behavior.symbol_address("g_5AAC")
    g574e = behavior.symbol_address("g_574E")
    writes = [(g5702, w(0x8000) + w(*([0xA55A] * 31))),
              (g5742, w(0)), (g5746, w(0)), (g574a, w(0)), (g5aac, farptr(0x4444))]
    return behavior.Case(
        label=label, args=[], writes=writes,
        observe=[behavior.Range("window_stack", g5702, 64),
                 behavior.Range("clip_handles", g5742, 12),
                 behavior.Range("clip_list_pointer", g5aac, 4)],
        callbacks={}, return_kind="void", registers=_registers(),
        metadata={"suite": SUITE, "contract": "empty window stack sets g_574A to the default clip list and clears active clipping pointer",
                  "abi": "void far function; no parameters; retf",
                  "helper_policy": "original f_1E57_0009 executes; null handles avoid allocator dependencies",
                  "validity": "g_5702[0] is the empty-stack sentinel; no window objects or clip handles are live",
                  "coverage_limit": "does not exercise rectangle subtraction, per-window clip lists, handle allocation, 45-entry cache pressure, or window lock state"})


def clip_live_case(label, rects, seed=0x1E57038E, win_ids=None, cache_pressure=False):
    """Run live clipping with real Ralloc and real rectangle subtraction.

    Only win_GetObjRect is a deterministic boundary: it writes the valid object
    rectangle associated with the requested window into the far out parameter.
    Allocator, handle locking, resize/free, clip composition, and copy helpers
    execute in the original DOS image in both machines.
    """
    if not rects or len(rects) > 31:
        raise ValueError("the DOS window stack supports 1..31 live window IDs")
    # Put the heap and master table outside both DGROUP and the 55B3:xxxx
    # stack window. The default memory-suite arena at 6000 overlaps that stack
    # in linear memory (60000..65B30), which made stack locals appear as heap
    # mutations and could corrupt allocator fixtures.
    dga = memory_suite.dga
    arena_seg, master_seg, master_top, heap_paras = 0xA100, 0xA000, 0x0100, 0x700
    old = (memory_suite.HEAP_SEG, memory_suite.HANDLE_SEG,
           memory_suite.MASTER_FIRST, memory_suite.MASTER_ONE_PAST,
           memory_suite.HEAP_PARAS)
    if cache_pressure:
        rows = [(3, 1, {"size": 16, "name": f"oldclip{i}".encode()}) for i in range(45)]
        rows.append((heap_paras - 45 * 3, 0x80))
        existing_handles = list(range(45))
    else:
        rows = [(heap_paras, 0x80)]
        existing_handles = []
    memory_suite.HEAP_SEG, memory_suite.HANDLE_SEG = arena_seg, master_seg
    memory_suite.MASTER_FIRST, memory_suite.MASTER_ONE_PAST = master_top, master_top + 4
    memory_suite.HEAP_PARAS = heap_paras
    try:
        arena = memory_suite.heap_case(
            f"{label}/ralloc-arena", rows, handles=existing_handles,
            contract=("45 allocated unlocked firm Ralloc blocks plus a valid free tail" if cache_pressure
                      else "one large valid free Ralloc block for the clip routine's real allocations"))
    finally:
        (memory_suite.HEAP_SEG, memory_suite.HANDLE_SEG,
         memory_suite.MASTER_FIRST, memory_suite.MASTER_ONE_PAST,
         memory_suite.HEAP_PARAS) = old

    screen = (0, 0, 640, 400)
    for r in rects:
        if (len(r) != 4 or r[0] > r[2] or r[1] > r[3]
                or any(x < -128 or x > 768 for x in (r[0], r[2]))
                or any(y < -80 or y > 480 for y in (r[1], r[3]))):
            raise ValueError(f"rectangle outside the normalized signed clip fixture domain: {r}")
    wins = list(win_ids) if win_ids is not None else [WIN_ID + i * 0x100 for i in range(len(rects))]
    if len(wins) != len(rects) or len(set(wins)) != len(wins) or any(
            win < 0x0100 or win > 0x2C00 or win & 0x00FF for win in wins):
        raise ValueError("window IDs must be unique valid high-byte indices 1..44")
    stack_data = w(*wins, 0x8000, *([0xA55A] * (31 - len(wins))))
    g5702 = behavior.symbol_address("g_5702")
    g5a9c = behavior.symbol_address("g_5A9C")
    g5742 = behavior.symbol_address("g_5742")
    g5746 = behavior.symbol_address("g_5746")
    g574a = behavior.symbol_address("g_574A")
    g5aac = behavior.symbol_address("g_5AAC")
    clip_handles = behavior.symbol_address("fd_50F6_3B60")
    writes = list(arena.writes) + [
        (g5702, stack_data), (g5a9c, w(*screen)),
        (g5742, w(0)), (g5746, w(0)), (g574a, w(0)),
        (g5aac, farptr(0)),
        (clip_handles, b"".join(farptr(i, 0x0F0F) for i in range(45))
         if cache_pressure else bytes(45 * 4)),
        (behavior.symbol_address("g_584C"), w(1 if cache_pressure else 0)),
    ]

    def get_rect(machine, args):
        win, off, seg = args
        try:
            index = wins.index(win & 0xFFFF)
        except ValueError:
            raise behavior.ExecutionError(f"unexpected win_GetObjRect id {win:04x}")
        machine.write(seg * 16 + off, w(*rects[index]))
        machine.state.setdefault("rect_provider_calls", []).append(
            {"window": win & 0xFFFF, "rect": list(rects[index])})

    # The pointer is to a compiler-owned local Rect whose BP offset differs
    # between target and candidate. Project it to the logical output parameter
    # while the handler still writes through the real far pointer.
    cb = behavior.Callback(2, get_rect, ("ax",), pop=4,
                          project=lambda machine, args: [args[0], "logical-rect-output"])

    return behavior.Case(
        label=label, args=[], writes=writes,
        observe=list(arena.observe) + [
            behavior.Range("window_stack", g5702, 64),
            behavior.Range("screen_rect", g5a9c, 8),
            behavior.Range("clip_handles_45", clip_handles, 45 * 4),
            behavior.Range("clip_globals", g5742, 12),
            behavior.Range("active_clip_pointer", g5aac, 4),
            behavior.Range("master_handle_slots", master_seg * 16, master_top),
        ],
        callbacks={"win_GetObjRect": cb}, return_kind="void",
        registers=_registers(), state={"rect_provider_calls": []}, observe_at_calls=False,
        metadata={"suite": SUITE, "contract": "ordered per-window clip lists and all allocator-backed rectangle bytes after rebuilding the active window stack",
                  "abi": "void far f_1E57_038E(void); win_GetObjRect fastcall AX=window, stack far rect, callback pop=4",
                  "helper_policy": "actual original Ralloc allocation/lock/unlock/resize/free, _fmemcpy/_fmemset, and actual original f_1D8E_02BD rectangle subtraction; only win_GetObjRect supplies deterministic window geometry",
                  "validity": {"windows": wins, "rectangles": [list(r) for r in rects], "screen": list(screen),
                              "screen_bounds": "normalized signed rectangles within bounded DOS logical coordinates; zero-width/height and partial/off-screen spans are allowed against the 640x400 clip screen",
                  "allocator": {"segment": f"{arena_seg:04x}", "paragraphs": heap_paras,
                                "master_table": f"{master_seg:04x}:{master_top:04x}",
                                "fixture": "45 valid cache handles and free tail" if cache_pressure
                                           else "single free block; no preexisting handles"}},
                  "seed": seed})


def clip_live_cases():
    return [
        clip_live_case("clip/single-fullscreen", [(0, 0, 640, 400)]),
        clip_live_case("clip/overlap", [(30, 30, 330, 230), (180, 100, 520, 340)]),
        clip_live_case("clip/disjoint", [(20, 20, 100, 100), (400, 260, 600, 380)]),
        clip_live_case("clip/nested", [(30, 30, 610, 370), (80, 80, 560, 320),
                                       (160, 120, 480, 280)]),
        clip_live_case("clip/edge-touch", [(0, 0, 640, 400), (0, 0, 100, 100),
                                           (100, 100, 240, 240)]),
        clip_live_case("clip/31-window-stack", [(0, 0, 640, 400)] * 31),
        clip_live_case("clip/last-of-45-window-indices", [(0, 0, 640, 400)],
                       win_ids=[0x2C00]),
        clip_live_case("clip/release-all-45-valid-cache-handles", [(0, 0, 640, 400)],
                       cache_pressure=True),
    ]


def randomized_clip_cases(count=5000, seed=0x1E57038E):
    """Generate valid 0..31-window stacks with bounded list fragmentation."""
    rr = random.Random(seed)
    out = []
    for i in range(count):
        n = rr.randrange(32)
        label = f"random/{seed:08x}/{i}"
        if n == 0:
            case = clip_empty_case(label)
            case.metadata.update({"lane": "randomized", "seed": seed, "stack_length": 0})
            out.append(case)
            continue
        family = rr.choice(("nested", "nested", "stripes", "general" if n <= 7 else "nested"))
        rects = []
        if family == "nested":
            left = rr.randrange(-64, 220); top = rr.randrange(-40, 140)
            right = rr.randrange(max(left, 300), 705); bottom = rr.randrange(max(top, 180), 449)
            rects.append((left, top, right, bottom))
            for _ in range(1, n):
                xlo, xhi = sorted((rr.randrange(left, right + 1), rr.randrange(left, right + 1)))
                ylo, yhi = sorted((rr.randrange(top, bottom + 1), rr.randrange(top, bottom + 1)))
                if rr.randrange(10) == 0:
                    xhi = xlo
                if rr.randrange(10) == 0:
                    yhi = ylo
                rects.append((xlo, ylo, xhi, yhi))
                left, top, right, bottom = xlo, ylo, xhi, yhi
        elif family == "stripes":
            for _ in range(n):
                ylo, yhi = sorted((rr.randrange(-80, 481), rr.randrange(-80, 481)))
                if rr.randrange(8) == 0:
                    yhi = ylo
                rects.append((-64, ylo, 704, yhi))
        else:
            for _ in range(n):
                xlo, xhi = sorted((rr.randrange(-128, 769), rr.randrange(-128, 769)))
                ylo, yhi = sorted((rr.randrange(-80, 481), rr.randrange(-80, 481)))
                if rr.randrange(12) == 0:
                    xhi = xlo
                if rr.randrange(12) == 0:
                    yhi = ylo
                rects.append((xlo, ylo, xhi, yhi))
        ids = [x * 0x100 for x in rr.sample(range(1, 45), n)]
        case = clip_live_case(label, rects, seed=seed, win_ids=ids)
        case.metadata.update({"lane": "randomized", "seed": seed, "stack_length": n,
                              "geometry_family": family})
        out.append(case)
    return out












