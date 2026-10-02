#!/usr/bin/env python3
"""Bounded DOS differential for native balloon queue submission.

The original module is invoked directly for AddMsgBalloon. A small ctypes
binding invokes the actual portable queue model on the same typed fixture.
"""
from __future__ import annotations

import ctypes
import hashlib
import json
import random
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))
import behavior
import behavior_ledger

SOURCE = ROOT / "evidence/behavior/functions/DrawBalloons/contracts/logical-render-v1/module.c"
MODEL = ROOT / "portable/ui_model/windows/balloon_queue.c"
MODEL_H = ROOT / "portable/ui_model/windows/balloon_queue.h"
OUT = ROOT / "build/workers/behavior_text_card/balloon_queue_addmsg"
TEXT_SEG = 0xA800
TEXT_BASE = 0x0100
TEXT_STRIDE = 0x20
CALLER_TABLE = 5


class Viewport(ctypes.Structure):
    _fields_ = [(name, ctypes.c_int16) for name in
                ("plane", "left", "top", "columns", "rows")]


class MessageId(ctypes.Structure):
    _fields_ = [("table", ctypes.c_uint16), ("index", ctypes.c_uint16),
                ("is_null", ctypes.c_uint8)]


class QueueEntry(ctypes.Structure):
    _fields_ = [("id", MessageId), ("borrowed_text", ctypes.c_char_p),
                ("x_pixels", ctypes.c_int16), ("y_pixels", ctypes.c_int16),
                ("plane", ctypes.c_int16), ("style", ctypes.c_int16)]


class Queue(ctypes.Structure):
    _fields_ = [("viewport", Viewport), ("pixel_width", ctypes.c_int16),
                ("pixel_height", ctypes.c_int16), ("count", ctypes.c_uint16),
                ("entries", QueueEntry * 6)]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def word(value: int) -> bytes:
    return struct.pack("<H", value & 0xFFFF)


def words(*values: int) -> bytes:
    return b"".join(word(value) for value in values)


def write_words(name: str, *values: int):
    return behavior.symbol_address(name), words(*values)


def write_at(address: int, data: bytes):
    return address, data


def cstring(value: str) -> bytes:
    return value.encode("ascii") + b"\0"


def far_pointer(index: int) -> tuple[int, int]:
    return TEXT_BASE + index * TEXT_STRIDE, TEXT_SEG


def make_case(label: str, args, viewport, pixel_size, initial_entries):
    x, y, plane, style, msg_index = args
    left, top, columns, rows, view_plane = viewport
    width, height = pixel_size
    writes = [
        write_words("MapPlane", view_plane),
        write_words("fd_50F6_0508", left, top),
        write_words("fd_50F6_10E0", columns),
        write_words("fd_50F6_10DE", rows),
        write_words("fd_55B3_19BE", width),
        write_words("fd_55B3_19C0", height),
        write_words("fd_50F6_1092", len(initial_entries)),
    ]
    queue_positions = bytearray()
    queue_planes = bytearray()
    queue_styles = bytearray()
    queue_pointers = bytearray()
    for entry_index in range(6):
        if entry_index < len(initial_entries):
            ex, ey, ep, es, em = initial_entries[entry_index]
        else:
            ex, ey, ep, es, em = (0x5A00 + entry_index,
                                  -100 - entry_index, 3, 9, 6)
        queue_positions += words(ex, ey)
        queue_planes += word(ep)
        queue_styles += word(es)
        queue_pointers += words(*far_pointer(em))
    writes += [
        write_at(behavior.symbol_address("fd_50F6_04C8"), queue_positions),
        write_at(behavior.symbol_address("fd_50F6_04F6"), queue_planes),
        write_at(behavior.symbol_address("fd_50F6_04E6"), queue_styles),
        write_at(behavior.symbol_address("fd_50F6_04A6"), queue_pointers),
    ]
    strings = bytearray()
    for index in range(8):
        strings.extend(cstring(f"fixture message {index}"))
        strings.extend(bytes(max(0, TEXT_STRIDE - len(cstring(f"fixture message {index}")))))
    writes.append(write_at(TEXT_SEG * 16 + TEXT_BASE, strings))
    off, seg = far_pointer(msg_index)
    case = behavior.Case(
        label, args=[x, y, plane, style, off, seg], writes=writes,
        observe=[
            behavior.Range("balloon_queue_count", behavior.symbol_address("fd_50F6_1092"), 2),
            behavior.Range("balloon_queue_positions", behavior.symbol_address("fd_50F6_04C8"), 24),
            behavior.Range("balloon_queue_planes", behavior.symbol_address("fd_50F6_04F6"), 12),
            behavior.Range("balloon_queue_styles", behavior.symbol_address("fd_50F6_04E6"), 12),
            behavior.Range("balloon_queue_message_ptrs", behavior.symbol_address("fd_50F6_04A6"), 24),
        ], return_kind="void", metadata={
            "suite": "balloon_queue_addmsg_v1",
            "contract": "AddMsgBalloon normalized six-slot queue: identity, pixel position, plane, style",
            "host_boundary": "the message pointer is a typed borrowed fixture resource",
        })
    return case


def model_queue(library, case_args, viewport, pixel_size, initial_entries):
    left, top, columns, rows, plane = viewport
    width, height = pixel_size
    queue = Queue()
    queue.viewport = Viewport(plane, left, top, columns, rows)
    queue.pixel_width = width
    queue.pixel_height = height
    queue.count = len(initial_entries)
    text_buffers = []
    def borrowed(index):
        raw = ctypes.create_string_buffer(f"fixture message {index}".encode("ascii"))
        text_buffers.append(raw)
        return ctypes.cast(raw, ctypes.c_char_p)
    for i, (x, y, p, style, text_index) in enumerate(initial_entries):
        queue.entries[i] = QueueEntry(MessageId(CALLER_TABLE, text_index, 0),
                                      borrowed(text_index), x, y, p, style)
    x, y, p, style, index = case_args
    status = library.portable_balloon_queue_add(
        ctypes.byref(queue), x, y, p, style,
        MessageId(CALLER_TABLE, index, 0), borrowed(index))
    return int(status), queue


def source_pointer(machine, index: int) -> tuple[int, int]:
    at = behavior.symbol_address("fd_50F6_04A6") + index * 4
    return machine.word(at), machine.word(at + 2)


def signed16(value: int) -> int:
    value &= 0xFFFF
    return value - 0x10000 if value & 0x8000 else value


def normalized_queue(machine, count: int):
    output = []
    for i in range(min(count, 6)):
        x = signed16(machine.word(behavior.symbol_address("fd_50F6_04C8") + i * 4))
        y = signed16(machine.word(behavior.symbol_address("fd_50F6_04C8") + i * 4 + 2))
        plane = signed16(machine.word(behavior.symbol_address("fd_50F6_04F6") + i * 2))
        style = signed16(machine.word(behavior.symbol_address("fd_50F6_04E6") + i * 2))
        pointer = source_pointer(machine, i)
        expected = {far_pointer(n): n for n in range(8)}
        if pointer not in expected:
            raise ValueError(f"queue pointer has no fixture identity: {pointer}")
        output.append((x, y, plane, style, CALLER_TABLE, expected[pointer], 0))
    return output


def native_queue(queue: Queue):
    return [(int(queue.entries[i].x_pixels), int(queue.entries[i].y_pixels),
             int(queue.entries[i].plane), int(queue.entries[i].style),
             int(queue.entries[i].id.table), int(queue.entries[i].id.index),
             int(queue.entries[i].id.is_null)) for i in range(queue.count)]


def directed_cases():
    cases = []
    viewport = (10, 20, 32, 24, 2)
    for style, args in [
        (0, (10, 23, 2, 0, 0)),
        (1, (11, 23, 2, 1, 1)),
        (2, (12, 24, 2, 2, 2)),
        (10, (224, 368, 2, 10, 3)),
        (0, (42, 23, 2, 0, 4)),
        (0, (11, 22, 2, 0, 5)),
        (0, (11, 23, 1, 0, 6)),
    ]:
        cases.append((f"directed/style-{style}/{len(cases)}", args, viewport,
                      (16, 16), []))
    cases.append(("directed/queue-full", (12, 24, 2, 2, 0), viewport,
                  (16, 16), [(12+i, 24, 2, i, i) for i in range(6)]))
    cases.append(("directed/queue-five-visible", (15, 25, 2, 0, 6), viewport,
                  (16, 16), [(12+i, 24, 2, i, i) for i in range(5)]))
    cases.append(("directed/style10-negative-trunc", (-17, -17, 2, 10, 2),
                  (-2, -4, 12, 12, 2), (16, 16), []))
    cases.append(("directed/pixel-word-wrap", (2048, 2048, 2, 1, 1),
                  (0, 0, 3000, 3000, 2), (32, 32), []))
    return cases


def random_cases(count=96, seed=0xBA110A):
    rng = random.Random(seed)
    for i in range(count):
        width, height = rng.choice((8, 12, 16, 24, 32)), rng.choice((8, 12, 16, 24, 32))
        left, top = rng.randrange(-32, 32), rng.randrange(-32, 32)
        columns, rows = rng.randrange(1, 48), rng.randrange(1, 36)
        plane = rng.randrange(4)
        style = rng.choice((0, 1, 2, 10))
        x = rng.randrange(-300, 700) if style == 10 else rng.randrange(-50, 90)
        y = rng.randrange(-300, 700) if style == 10 else rng.randrange(-50, 80)
        count_seed = rng.randrange(7)
        initial = [(rng.randrange(-1000, 1000), rng.randrange(-1000, 1000),
                    rng.randrange(4), rng.randrange(-3, 13), rng.randrange(8))
                   for _ in range(count_seed)]
        yield (f"random/{i:04d}", (x, y, plane, style, rng.randrange(8)),
               (left, top, columns, rows, rng.randrange(4)), (width, height), initial)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    dll = OUT / "balloon_queue_model.dll"
    subprocess = __import__("subprocess")
    subprocess.run(["C:/msys64/mingw64/bin/gcc.exe", "-std=c11", "-O2",
                    "-Wall", "-Wextra", "-Werror", "-shared", "-I",
                    str(ROOT / "portable"), str(MODEL),
                    str(ROOT / "portable/ui_model/balloons/balloons.c"),
                    "-o", str(dll)], cwd=ROOT, check=True)
    library = ctypes.CDLL(str(dll))
    library.portable_balloon_queue_add.argtypes = [
        ctypes.POINTER(Queue), ctypes.c_int16, ctypes.c_int16, ctypes.c_int16,
        ctypes.c_int16, MessageId, ctypes.c_char_p]
    library.portable_balloon_queue_add.restype = ctypes.c_int
    pair = behavior.PreparedPair(
        "AddMsgBalloon", source=SOURCE,
        out=Path("build/workers/behavior_text_card/balloon_queue_addmsg/prepared"))
    ledger = behavior_ledger.CaseLedger(
        OUT / "addmsg-cases.jsonl.gz", pair,
        ["return and caller ABI", "source visibility and queue-cap behavior",
         "normalized queue count/identity/pixel position/plane/style",
         "original DOS versus whole-module candidate"])
    rows = []
    totals = {"dos_candidate_equal": 0, "native_dos_equal": 0,
              "negative_controls_detected": 0, "errors": 0}
    cases = list(directed_cases()) + list(random_cases())
    for case_index, (label, args, viewport, pixel_size, initial) in enumerate(cases):
        case = make_case(label, args, viewport, pixel_size, initial)
        try:
            result = pair.compare(case)
            lane = "directed" if label.startswith("directed/") else "randomized"
            ledger.record(case, result, lane=lane)
            count = pair.original_machine.word(behavior.symbol_address("fd_50F6_1092"))
            oracle = normalized_queue(pair.original_machine, count)
            model_status, model = model_queue(library, args, viewport, pixel_size, initial)
            native = native_queue(model)
            model_equal = model_status == 0 and native == oracle
            totals["dos_candidate_equal"] += int(result.equal)
            totals["native_dos_equal"] += int(model_equal)
            negative_detected = None
            if label == "directed/style-0/0":
                mutant_args = (args[0] + 1, *args[1:])
                _, mutant = model_queue(library, mutant_args, viewport, pixel_size, initial)
                negative_detected = native_queue(mutant) != oracle
                totals["negative_controls_detected"] += int(negative_detected)
            rows.append({"id": label, "input": {"args": args, "viewport": viewport,
                         "pixel_size": pixel_size, "initial_queue": initial},
                         "oracle_queue": oracle, "native_queue": native,
                         "native_status": model_status, "native_equals_dos": model_equal,
                         "dos_candidate_equal": bool(result.equal),
                         "x_plus_one_negative_detected": negative_detected,
                         "pair_diff": result.diff})
        except Exception as exc:
            totals["errors"] += 1
            rows.append({"id": label, "error": str(exc)})
    ledger_pin = ledger.finalize()
    report = {
        "schema": "balloon-queue-addmsg-differential-v1",
        "status": "PASS_BOUNDED_COMPARISON" if
                  totals["dos_candidate_equal"] == len(cases) and
                  totals["native_dos_equal"] == len(cases) and
                  totals["negative_controls_detected"] == 1 and
                  totals["errors"] == 0 else "FAIL",
        "target": "root:m0250 AddMsgBalloon plus portable logical queue model",
        "case_count": len(cases), "directed_count": len(directed_cases()),
        "random_count": len(cases) - len(directed_cases()),
        "random_seed": 0xBA110A, "totals": totals,
        "source": {"path": SOURCE.relative_to(ROOT).as_posix(), "sha256": digest(SOURCE)},
        "native_model": {"path": MODEL.relative_to(ROOT).as_posix(), "sha256": digest(MODEL),
                         "header": MODEL_H.relative_to(ROOT).as_posix(),
                         "header_sha256": digest(MODEL_H)},
        "candidate_identity": pair.identity,
        "native_model_binary": {"path": dll.relative_to(ROOT).as_posix(), "sha256": digest(dll)},
        "case_ledger": ledger_pin,
        "limits": ["AddMsgBalloon only; DrawCurBalloons is not yet differentially closed.",
                   "Borrowed text identity is a controlled fixture table/index, not a production resource binding.",
                   "Finite source geometry domain; no visual pixel claim."],
        "cases": rows,
    }
    path = OUT / "report.json"
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": report["status"], "cases": len(cases),
                      "totals": totals, "report": str(path)}, indent=2))
    if report["status"] != "PASS_BOUNDED_COMPARISON":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
