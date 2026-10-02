#!/usr/bin/env python3
"""Original-DOS double-click coalescer cases for the Edit-object event."""
from __future__ import annotations

import hashlib
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))
import behavior

SOURCE = ROOT / "src/root/m218D.c"
EVENT_NAME = "fd_50F6_49FA"
PREVIOUS_NAME = "fd_50F6_4A0A"
OBJECT_LINEAR = 0x70000
OBJECT_SEG, OBJECT_OFF = OBJECT_LINEAR >> 4, OBJECT_LINEAR & 0xF


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def event_bytes(code: int, modifiers: int, *, h: int = 150, v: int = 150,
                what: int = 0, message: int = 0, tick: int = 0x1234,
                xE: int = 0x0101) -> bytes:
    return struct.pack("<8h", what, message, tick, modifiers, h, v, code, xE)


def case_for(pair, label, *, previous, current, last_tick, now):
    event_sym = behavior.symbol(EVENT_NAME)
    prev_sym = behavior.symbol(PREVIOUS_NAME)
    data = pair.ctx.module_dict()["placements"]["_DATA"]
    tick_address = data["seg"] * 16 + data["off"]
    prev_bytes = event_bytes(previous[0], previous[1])
    current_bytes = event_bytes(current[0], current[1])
    obj = bytearray(0x40)
    # Valid source object record with no list dispatch and no draw-on-update flag.
    obj[0x21] = 0
    obj[0x24:0x26] = b"\x00\x00"

    def lock(machine, args):
        machine.state["object_lock_ids"].append(args[0])

    def object_address(machine, args):
        machine.state["object_lookup_ids"].append(args[0])
        return OBJECT_OFF, OBJECT_SEG

    def unlock(machine, args):
        machine.state["object_unlock_ids"].append(args[0])

    def tick_count(machine, _args):
        i = machine.state["tick_index"]
        values = machine.state["tick_values"]
        value = values[min(i, len(values) - 1)]
        machine.state["tick_index"] = i + 1
        return value & 0xFFFF, (value >> 16) & 0xFFFF

    callbacks = {
        "win_LockWin": behavior.Callback(0, lock, register_args=("ax",)),
        "win_ObjAddr": behavior.Callback(0, object_address, register_args=("ax",)),
        "win_UnlockWin": behavior.Callback(0, unlock, register_args=("ax",)),
        "TickCount": behavior.Callback(0, tick_count),
    }
    ranges = [
        behavior.Range(EVENT_NAME, behavior.symbol_address(EVENT_NAME), 16),
        behavior.Range(PREVIOUS_NAME, behavior.symbol_address(PREVIOUS_NAME), 16),
        behavior.Range("double_click_tick", tick_address, 4),
    ]
    event_segment = event_sym["seg"]
    event_offset = event_sym["off"]
    return behavior.Case(
        label,
        writes=[
            (behavior.symbol_address(EVENT_NAME), current_bytes),
            (behavior.symbol_address(PREVIOUS_NAME), prev_bytes),
            (tick_address, struct.pack("<i", last_tick)),
            (OBJECT_LINEAR, bytes(obj)),
        ],
        observe=ranges,
        callbacks=callbacks,
        return_kind="void",
        args=[event_offset, event_segment],
        callee_pop=4,
        state={"tick_values": now, "tick_index": 0,
               "object_lock_ids": [], "object_lookup_ids": [], "object_unlock_ids": []},
    )


def main():
    pair = behavior.PreparedPair(
        "f_218D_000C", source=SOURCE,
        out=ROOT / "build/behavior/edit-event-coalescer-probe")
    cases = [
        ("first-left-press", (3, 0), (4, 0x0201), -1, [105, 105], 0x0201),
        ("same-code-left-double-press-under-10", (4, 0x0201), (4, 0x0201),
         100, [105], 0x2001),
        ("same-code-right-double-press-under-10", (4, 0x0802), (4, 0x0802),
         100, [105], 0x4002),
        ("different-code-no-coalesce", (3, 0x0201), (4, 0x0201),
         100, [105, 105], 0x0201),
        ("same-code-outside-10-tick-window", (4, 0x0201), (4, 0x0201),
         90, [105, 106], 0x0201),
        ("left-right-edge-mismatch-no-coalesce", (4, 0x0201), (4, 0x0802),
         100, [105, 106], 0x0802),
    ]
    rows = []
    for label, previous, current, last_tick, now, expected in cases:
        result = pair.compare(case_for(
            pair, label, previous=previous, current=current,
            last_tick=last_tick, now=now))
        if not result.equal:
            raise AssertionError(f"{label}: source candidate mismatch {result.diff}")
        raw = bytes.fromhex(result.original["ranges"][EVENT_NAME])
        actual = struct.unpack("<8h", raw)
        actual_modifiers = actual[3] & 0xFFFF
        if actual_modifiers != expected:
            raise AssertionError(f"{label}: modifiers {actual_modifiers:#06x}, expected {expected:#06x}")
        rows.append({
            "id": label,
            "previous_code_modifiers": list(previous),
            "current_code_modifiers": list(current),
            "last_tick": last_tick,
            "tick_reads": now,
            "result_event_words": list(actual),
            "result_modifiers_hex": f"0x{actual_modifiers:04X}",
            "original_candidate_equal": result.equal,
            "callback_order": [item["name"] for item in result.original["trace"]],
            "callback_state": result.original["state"],
            "global_ranges": result.original["ranges"],
        })

    report = {
        "schema": "edit-object-dos-click-coalescer-probe-v1",
        "status": "PASS",
        "scope": "Original f_218D_000C executes its click coalescing logic against initialized 16-byte current/previous Event records. Lock/lookup/unlock and TickCount are explicit boundary fixtures; the object record uses a source-layout-valid no-draw/no-list record.",
        "call_abi": {
            "event_far_pointer": "stack words [offset,segment]",
            "callee_stack_pop_bytes": 4,
            "object_id": "AX at win_LockWin/win_ObjAddr/win_UnlockWin calls",
            "win_ObjAddr_return": "AX:DX as offset:segment",
        },
        "pair_identity": pair.identity,
        "source_sha256": sha(SOURCE),
        "events": rows,
        "rule": {
            "same code plus same edge mask 0x0A00 within 10 ticks": "clear 0x0A00 and convert previous left press 0x0200 to 0x2000, previous right press 0x0800 to 0x4000",
            "left double press": "0x0201 -> 0x2001",
            "right double press": "0x0802 -> 0x4002",
            "release conditions": "left release 0x0400 and right release 0x1000 are not in g_6004's 0x0A00 registration mask",
        },
        "limitations": [
            "The probe tests f_218D_000C with a controlled, valid object record; it does not read the live session's Edit object 4 flags or prove object activation timing.",
            "No keyboard Shift state is simulated. The output high flags are same-code double-click markers derived from prior mouse-edge flags.",
        ],
    }
    out = ROOT / "portable/tests/input/evidence/edit-object-dos-click-coalescer-probe.json"
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Edit-object DOS coalescer probe: PASS ({len(rows)} cases); {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
