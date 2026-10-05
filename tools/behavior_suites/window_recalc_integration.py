"""Actual win_Recalc integration controls for f_20E8_0903.

This supplements the bounded coordinate corpus, whose manager callback is kept
as diagnostic evidence.  These cases use valid Ralloc-backed windows and run
the DOS lock/object/recalc helpers from the original image.
"""
from __future__ import annotations

import json
import random
import struct
import sys
import time
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'layout/functions.json').is_file())



import behavior
from behavior_suites import memory as memory_suite
from behavior_suites import windows as window_suite
from behavior_ledger import CaseLedger

SUITE = "window_recalc_integration_v1"
TARGET = "f_20E8_0903"
WIN_ID = 0x0100
HEAP_SEG = 0xA100
MASTER_SEG = 0x90FF
MASTER_TOP = 0xFFFC
HEAP_PARAS = 0x700
RECT_SEG = 0xB000
RECT_OFF = 0x0100


def w(*values):
    return struct.pack("<" + "H" * len(values), *(int(v) & 0xFFFF for v in values))


def far(off, seg):
    return struct.pack("<HH", off & 0xFFFF, seg & 0xFFFF)


def _rect(rng):
    x0, x1 = sorted((rng.randrange(0, 641), rng.randrange(0, 641)))
    y0, y1 = sorted((rng.randrange(0, 401), rng.randrange(0, 401)))
    if x0 == x1:
        x1 = min(640, x0 + 1)
    if y0 == y1:
        y1 = min(400, y0 + 1)
    return x0, y0, x1, y1


def live_case(label, seed, *, count=None, target_index=None, forced_modes=None,
              forced_rect=(17, 29, 401, 283), object_rects=None):
    rng = random.Random(seed)
    count = count or rng.randrange(1, 5)
    target_index = rng.randrange(count) if target_index is None else target_index
    if not 1 <= count <= 6 or not 0 <= target_index < count:
        raise ValueError("window object count/index outside bounded valid fixture")

    # One firm Ralloc window owns its DOS Win header and packed object records.
    # RepointObjects will populate the in-header pointer table exactly as the
    # original lock path does when this window is first locked.
    block_paras = 64
    free_paras = HEAP_PARAS - block_paras
    arena = memory_suite.heap_case(
        f"{label}/ralloc-window",
        [(block_paras, 1, {"size": block_paras * 16 - 32, "lock": 0,
                           "name": b"recalc-window"}),
         (free_paras, 0x80)],
        handles=[0], heap_seg=HEAP_SEG, heap_paras=HEAP_PARAS, handle_seg=MASTER_SEG,
        contract="one valid firm Ralloc window handle with linked free tail and packed DOS object records")

    data_seg = HEAP_SEG + 2
    object_table_off = 0x2C
    objects_off = object_table_off + count * 4
    object_bytes = bytearray(0x2C + count * 4 + count * 0x28)
    object_bytes[0x0C:0x0E] = w(count)
    object_bytes[0x1C:0x1E] = w(0)  # disable deferred object-handle destruction
    for index in range(count):
        obj_off = objects_off + index * 0x28
        obj = bytearray(0x28)
        obj[0x21] = 0  # default supported object class; no autosize resources
        obj[0x22:0x24] = w(0x28)  # original RepointObjects record stride
        if forced_modes is not None and index == target_index:
            modes = list(forced_modes)
        elif index == 0:
            modes = [0, 0, 0, 0]
        else:
            modes = [rng.randrange(6) for _ in range(4)]
        refs = []
        for axis, mode in enumerate(modes):
            if mode == 0:
                refs.append(WIN_ID)
            elif mode == 5:
                # Mode 5 selects a bounded window-relative field index.
                refs.append(rng.randrange(4))
            elif index == 0:
                modes[axis] = 0
                refs.append(WIN_ID)
            else:
                # Backward-only object references form a convergent DAG.
                refs.append(WIN_ID + rng.randrange(index))
        origins = [rng.randrange(-80, 81) for _ in range(4)]
        initial_rect = object_rects[index] if object_rects is not None else _rect(rng)
        obj[0:8] = w(*initial_rect)
        obj[8:16] = w(*origins)
        obj[16:24] = w(*refs)
        obj[24:32] = w(*modes)
        object_bytes[obj_off:obj_off + len(obj)] = obj

    # Window header points inline at the table; table entries are set by the
    # original RepointObjects helper on the first win_LockWin.
    object_bytes[0:8] = w(0, 0, 640, 400)
    object_bytes[0x2C:0x2C + count * 4] = bytes(count * 4)
    # win_Recalc mode 5 reads these four window-relative parameters.
    object_bytes[0x10:0x18] = w(0, 0, 640, 400)

    dg = behavior.match.DGROUP_SEG * 16
    master_slot = MASTER_TOP
    writes = list(arena.writes) + [
        (data_seg * 16, bytes(object_bytes)),
        (dg + 0x644C, w(1)), (dg + 0x644E, w(0)),
        (dg + 0x8DA6, bytes(45)), (dg + 0x8CF2, bytes(45 * 4)),
        (behavior.symbol_address("win_handles") + 4,
         far(master_slot, MASTER_SEG)),
        (behavior.symbol_address("win_numOfWindows"), w(45)),
        (behavior.symbol_address("g_6300"), w(0)),
        (RECT_SEG * 16 + RECT_OFF, w(*forced_rect if label.endswith("positive") else _rect(rng))),
    ]
    window_rect = tuple(struct.unpack("<4h", writes[-1][1]))
    objid = WIN_ID + target_index
    effect_ranges = [r for r in arena.observe if r.name not in ("heap", "handle_table")] + [
        behavior.Range("recalc_window_heap", HEAP_SEG * 16, (HEAP_PARAS + 2) * 16),
        behavior.Range("recalc_master_slots", MASTER_SEG * 16 + memory_suite.MASTER_START,
                       memory_suite.MASTER_CAPACITY * 4),
        behavior.Range("window_lock_helpers", dg + 0x644C, 4),
        behavior.Range("window_lock_state", dg + 0x8CF2, 45 * 4 + 45),
        behavior.Range("window_handles", behavior.symbol_address("win_handles"), 45 * 4),
        behavior.Range("window_count", behavior.symbol_address("win_numOfWindows"), 2),
        behavior.Range("g_6300", behavior.symbol_address("g_6300"), 2),
        behavior.Range("requested_rectangle", RECT_SEG * 16 + RECT_OFF, 8),
    ]
    actual_helpers = {
        name: behavior.Callback(0, None, ("ax",))
        for name in ("win_LockWin", "win_UnlockWin", "win_Recalc", "f_2505_02D7")
    }
    actual_helpers["f_2505_0006"] = behavior.Callback(1, None)
    case = behavior.Case(
        label=label,
        args=[RECT_OFF, RECT_SEG],
        writes=writes,
        observe=effect_ranges,
        callbacks=actual_helpers,
        return_kind="void",
        registers=window_suite._registers(ax=objid),
        callee_pop=4,
        state={},
        metadata={
            "suite": SUITE,
            "contract": "f_20E8_0903 using actual DOS Ralloc window lock, object lookup, iterative win_Recalc, and final unlock",
            "abi": "AX=window-object id; stack far pointer to normalized logical-screen rectangle; target retf 4",
            "actual_original_helpers": ["win_LockWin", "f_2505_02D7", "win_Recalc", "win_UnlockWin",
                                        "f_171C_1686", "f_171C_1B84", "f_171C_1BBA", "f_171C_2086"],
            "validity": {
                "window_id": WIN_ID,
                "object_count": count,
                "target_object_index": target_index,
                "rect": list(window_rect),
                "ralloc": "firm type-1 header, master slot 90FF:FFFC, offset-zero base 90FF:0000, payload A102:0000, linked free tail",
                "object_records": "packed 0x28-byte type-0 records; original win_LockWin calls RepointObjects",
                "reference_graph": "modes 0..4 use absolute/bounded edges and backward-only object dependencies; mode 5 reads four initialized window-relative fields",
                "geometry_domain": "normalized signed 16-bit logical-screen rectangles with coordinates within 0..640 by 0..400",
            },
        })
    return case


def randomized_cases(count=100, seed=0x2505ECA1):
    rng = random.Random(seed)
    cases = [live_case("recalc/positive", seed ^ 0x5A17, count=2, target_index=1,
                       forced_modes=(0, 0, 0, 0), forced_rect=(17, 29, 401, 283))]
    for index in range(count - 1):
        case_seed = rng.randrange(0x100000000)
        cases.append(live_case(f"random/{seed:08x}/{index}", case_seed))
    return cases




def field_cases(count=64, seed=0x25050453):
    rng = random.Random(seed)
    cases = []
    for index in range(count):
        n = 1 + rng.randrange(6)
        target_index = rng.randrange(n)
        rects = [_rect(rng) for _ in range(n)]
        label = "field/positive" if index == 0 else f"random/{seed:08x}/{index - 1}"
        case = live_case(label, rng.randrange(0x100000000), count=n,
                         target_index=target_index, object_rects=rects)
        case.args = []
        case.callee_pop = 0
        case.return_kind = "s16"
        case.registers["dx"] = index % 4
        cases.append(case)
    return cases


def unlock_cases(count=500, seed=0x23AE01DB):
    """Final and nested unlock paths with valid Ralloc-backed window state."""
    # The non-final depth controls retain the same fully valid tree as final
    # release. Only the live lock byte varies, so the early decrement path is
    # compared without the old synthetic helper callbacks.
    cases = []
    actual_helpers = {
        name: behavior.Callback(2, None)
        for name in ("f_171C_1686", "f_171C_13E4", "f_171C_2086", "f_171C_20E2")
    }
    for depth in (2, 3, 255):
        case = window_suite.unlock_live_case(f"nested-depth-{depth}", (4, 18))
        dg = behavior.match.DGROUP_SEG * 16
        case.writes.append((dg + 0x8DA6 + 1, bytes([depth])))
        case.label = f"unlock/nested-depth-{depth}"
        case.metadata["contract"] = "nested decrement using valid Ralloc window/object tree and original unlock helpers"
        case.metadata["validity"]["initial_lock_depth"] = depth
        case.callbacks = dict(actual_helpers)
        cases.append(case)
    cases.extend([
        window_suite.unlock_live_case("unlock/positive", (4, 10, 16, 17, 18)),
        window_suite.unlock_live_case("final-release/nonhandle-object", (0,)),
        window_suite.unlock_live_case("deferred-redraw/flag-200", (4, 18), window_flags=0xA00),
        window_suite.unlock_live_case("deferred-redraw/pending-update", (10, 17), redraw_pending=1),
        window_suite.unlock_live_case("final-release/no-auto-update-flag", (16,), window_flags=0),
    ])
    cases.extend(window_suite.randomized_unlock_cases(count, seed))
    for case in cases:
        case.callbacks = dict(actual_helpers)
    return cases






