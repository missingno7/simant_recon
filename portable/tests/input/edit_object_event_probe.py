#!/usr/bin/env python3
"""Trace the original DOS Edit-object mouse hot-box registration and callback."""
from __future__ import annotations

import hashlib
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))
import behavior

M1FD2_SOURCE = ROOT / "src/root/m1FD2.c"
PAIR_OUT = ROOT / "build/behavior/edit-object-event-probe"
RECT_LINEAR = 0x70000
RECT_SEG, RECT_OFF = RECT_LINEAR >> 4, RECT_LINEAR & 0xF


def u16(data: bytes, at: int = 0) -> int:
    return struct.unpack_from("<H", data, at)[0]


def i16(data: bytes, at: int = 0) -> int:
    return struct.unpack_from("<h", data, at)[0]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def invoke_symbol(pair, machine, name: str, case: behavior.Case):
    saved = pair.function
    pair.function = behavior.symbol(name)
    try:
        return machine.run(case, preserve=case.label != "initialize-mouse-event-callback")
    finally:
        pair.function = saved


def run_bios_variant(pair, *, flags: int, tick: int):
    """Run a fresh original callback with explicit BIOS keyboard/tick words."""
    machine = behavior.Machine(pair)
    pair.original_machine = machine
    rect = struct.pack("<4h", 100, 100, 200, 200)
    invoke_symbol(pair, machine, "_f_1B73_0AA3", behavior.Case(
        "initialize-mouse-event-callback", writes=[
            (RECT_LINEAR, rect),
            (0x417, struct.pack("<H", flags)),
            (0x46C, struct.pack("<H", tick)),
        ], return_kind="void"))
    machine.run(behavior.Case(
        f"register-edit-object-4-bios-{flags:04x}-{tick:04x}",
        args=[RECT_OFF, RECT_SEG, 4], return_kind="void"), preserve=True)
    saved = pair.function
    pair.function = behavior.symbol("_f_1B73_03EE")
    try:
        machine.run(behavior.Case(
            f"int33-left-press-bios-{flags:04x}-{tick:04x}", return_kind="void",
            registers={"ax": 0x0002, "bx": 0x0001, "cx": 150, "dx": 150}),
            preserve=True)
    finally:
        pair.function = saved
    ring_offset = u16(machine.read(behavior.symbol_address("g_5FFE"), 2))
    ring_base = behavior.symbol("g_5FFE")["seg"] * 16 + ring_offset
    words = list(struct.unpack("<8H", machine.read(ring_base, 16)))
    return {
        "bios_flags_word": flags,
        "bios_tick_low_word": tick,
        "event_words": words,
        "event_signed_words": list(struct.unpack("<8h", struct.pack("<8H", *words))),
        "message_matches_bios_flags": words[1] == flags,
        "x4_matches_bios_tick_low_word": words[2] == tick,
        "code": words[6],
        "xE": words[7],
    }


def main():
    pair = behavior.PreparedPair("f_1FD2_03EB", source=M1FD2_SOURCE, out=PAIR_OUT)
    machine = pair.original_machine
    rect = struct.pack("<4h", 100, 100, 200, 200)

    invoke_symbol(pair, machine, "_f_1B73_0AA3", behavior.Case(
        "initialize-mouse-event-callback", writes=[
            (RECT_LINEAR, rect),
            (0x417, b"\x00\x00"),
            (0x46C, b"\x34\x12"),
        ],
        return_kind="void"))

    registration = machine.run(behavior.Case(
        "register-edit-object-4", args=[RECT_OFF, RECT_SEG, 4], return_kind="void"),
        preserve=True)
    hotbox_address = behavior.symbol_address("fd_5071_03C4")
    hotbox = machine.read(hotbox_address, 2 + 18)
    hotbox_count = u16(hotbox)
    record = hotbox[2:20]
    registered = {
        "count": hotbox_count,
        "rect": list(struct.unpack_from("<4h", record, 0)),
        "callback_farptr_words": list(struct.unpack_from("<2H", record, 8)),
        "event_code": u16(record, 12),
        "xE": u16(record, 14),
        "mouse_condition_mask": u16(record, 16),
    }

    machine_pair_function = pair.function
    pair.function = behavior.symbol("_f_1B73_03EE")
    try:
        left_press = machine.run(behavior.Case(
            "int33-left-button-press", return_kind="void",
            registers={"ax": 0x0002, "bx": 0x0001,
                       "cx": 150, "dx": 150}), preserve=True)
        count_after_press = u16(machine.read(behavior.symbol_address("g_5FF2"), 2))
        left_release = machine.run(behavior.Case(
            "int33-left-button-release", return_kind="void",
            registers={"ax": 0x0004, "bx": 0x0000,
                       "cx": 150, "dx": 150}), preserve=True)
        count_after_release = u16(machine.read(behavior.symbol_address("g_5FF2"), 2))
    finally:
        pair.function = machine_pair_function

    ring_offset = u16(machine.read(behavior.symbol_address("g_5FFE"), 2))
    ring_base = behavior.symbol("g_5FFE")["seg"] * 16 + ring_offset
    event = machine.read(ring_base, 16)
    queue = {
        "count": u16(machine.read(behavior.symbol_address("g_5FF2"), 2)),
        "write_index": u16(machine.read(behavior.symbol_address("g_5FF4"), 2)),
        "read_index": u16(machine.read(behavior.symbol_address("g_5FF6"), 2)),
        "event_words": list(struct.unpack("<8H", event)),
        "event_signed_words": list(struct.unpack("<8h", event)),
    }
    bios_variants = [run_bios_variant(pair, flags=0x0003, tick=0x0007)]
    report = {
        "schema": "edit-object-dos-hotbox-event-probe-v1",
        "status": "PASS" if (
            registered["count"] >= 1
            and registered["rect"] == [100, 100, 200, 200]
            and registered["event_code"] == 4
            and registered["xE"] == 0x0101
            and registered["mouse_condition_mask"] == 0x0A00
            and queue["count"] == 1
            and count_after_press == 1
            and count_after_release == 1
            and queue["event_signed_words"][6] == 4
            and queue["event_signed_words"][7] == 0x0101
            and queue["event_signed_words"][1] == 0
            and queue["event_signed_words"][2] == 0x1234
            and queue["event_signed_words"][3] == 0x0201
            and queue["event_signed_words"][4:6] == [150, 150]
            and bios_variants[0]["message_matches_bios_flags"]
            and bios_variants[0]["x4_matches_bios_tick_low_word"]
            and bios_variants[0]["code"] == 4
            and bios_variants[0]["xE"] == 0x0101
        ) else "FAIL",
        "source_identity": {
            "pair": pair.identity,
            "m1FD2_sha256": sha(M1FD2_SOURCE),
            "asm_source": "src/root/m1B73.asm",
            "asm_source_sha256": sha(ROOT / "src/root/m1B73.asm"),
        },
        "steps": {
            "initialize_callback": "original _f_1B73_0AA3 sets g5FFA=_f_1B73_0CB3 and g5FF9=0x1F",
            "controlled_bios_inputs": "0040:0017 word=0x0000; 0040:006C word=0x1234",
            "register_object": "original f_1FD2_03EB(object rect, object id 4) calls _f_1B73_0B5B then _f_1B73_0B00 with g_6004",
            "mouse_callback": "original _f_1B73_03EE invoked with INT33 event AX=0x0002, BX=0x0001 (left press/down), CX=150, DX=150",
            "output_event_writer": "original _f_1B73_030F -> _f_1B73_036E",
        },
        "registered_hotbox": registered,
        "mouse_callback": {
            "left_press_return": left_press["return"],
            "left_press_written_addresses": len(left_press["written_addresses"]),
            "left_release_return": left_release["return"],
            "left_release_written_addresses": len(left_release["written_addresses"]),
            "queue_count_after_left_press": count_after_press,
            "queue_count_after_left_release": count_after_release,
        },
        "queued_event": queue,
        "controlled_bios_variants": bios_variants,
        "interpretation": {
            "word_order": ["what", "message", "x4", "modifiers", "h", "v", "code", "xE"],
            "code4_event_is_emitted_on_left_press": queue["event_signed_words"][6] == 4,
            "left_press_AX_at_callback": "0x0201 (INT33 condition 0x02 in AH; BX bit0 left-down in AL after _0445)",
            "left_press_event_message_x4": [0, 0x1234],
            "release_enabled_by_hotbox_mask": count_after_release > count_after_press,
            "what_initialized_by_enqueue": False,
            "controlled_variant_confirms_bios_keyboard_and_tick_words": True,
            "proof_limitations": [
                "This executes the real descriptor register and original INT33 callback body with its physical-state registers controlled; it does not emulate hardware timing, DOS scheduling, or a live screen/window stack.",
                "Object 4's actual application activation state is represented by supplying its source-proven rectangle/object ID to the same registration API; the probe does not claim all sessions make object 4 selectable at this point.",
                "The mouse-down and event condition semantics follow the Microsoft DOS INT33/0Ch callback ABI; the native input adapter still needs to preserve this event contract.",
            ],
        },
    }
    out = ROOT / "portable/tests/input/evidence/edit-object-dos-hotbox-event-probe.json"
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Edit object 4 original DOS hot-box probe: {report['status']}; {out.relative_to(ROOT)}")
    if report["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
