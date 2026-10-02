#!/usr/bin/env python3
"""Original DOS versus native model differential for DrawCurBalloons."""
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
from balloon_queue_differential import (Queue, Viewport, MessageId, QueueEntry,
                                        native_queue, signed16, TEXT_SEG,
                                        TEXT_BASE, TEXT_STRIDE, cstring, word,
                                        words)

SOURCE = ROOT / "evidence/behavior/functions/DrawBalloons/contracts/logical-render-v1/module.c"
MODEL = ROOT / "portable/ui_model/windows/balloon_queue.c"
OUT = ROOT / "build/workers/behavior_text_card/balloon_draw_current"
TABLE_VARIABLES = ("fd_50F6_020A", "fd_50F6_0218", "fd_50F6_021C",
                   "fd_50F6_0234", "fd_50F6_023A")
TABLE_BASE = 0x0200
TABLE_STRIDE = 0x0040
STRING_BASE = 0x0500
STRING_STRIDE = 0x0020


class ViewportPoint(ctypes.Structure):
    _fields_ = [("x", ctypes.c_int16), ("y", ctypes.c_int16)]


class CueState(ctypes.Structure):
    _fields_ = [("active", ctypes.c_int16), ("displayed", ViewportPoint),
                ("displayed_plane", ctypes.c_int16), ("pending", ViewportPoint),
                ("pending_plane", ctypes.c_int16)]


class CueTimers(ctypes.Structure):
    _fields_ = [(name, ctypes.c_int32) for name in
                ("fight_first", "fight_second", "egg", "queen", "rest")]


class CueMessages(ctypes.Structure):
    _fields_ = [(name, ctypes.c_int16) for name in
                ("fight_first_enabled", "fight_second_enabled", "egg_enabled",
                 "queen_enabled", "rest_enabled")] + [
        (name, ctypes.c_uint16) for name in
        ("fight_first_index", "fight_second_index", "egg_index",
         "queen_index", "rest_index")]


class BalloonFrame(ctypes.Structure):
    _fields_ = [("cue", CueState * 4), ("timers", CueTimers),
                ("messages", CueMessages), ("queue", Queue),
                ("updates_enabled", ctypes.c_int16),
                ("sprite_state", ctypes.c_int16), ("cue_pause", ctypes.c_int16)]


TextCallback = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_void_p,
                                ctypes.POINTER(MessageId),
                                ctypes.POINTER(ctypes.c_char_p))
TickCallback = ctypes.CFUNCTYPE(ctypes.c_uint32, ctypes.c_void_p)
RandomCallback = ctypes.CFUNCTYPE(ctypes.c_int16, ctypes.c_void_p, ctypes.c_int)


class Services(ctypes.Structure):
    _fields_ = [("context", ctypes.c_void_p), ("tick_count", TickCallback),
                ("random", RandomCallback), ("lookup_text", TextCallback)]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def addr(name: str) -> int:
    return behavior.symbol_address(name)


def w(name: str, *values: int):
    return addr(name), words(*values)


def s32(value: int) -> bytes:
    return struct.pack("<I", value & 0xFFFFFFFF)


def cell(table: int, index: int) -> int:
    return STRING_BASE + (table * 4 + index) * STRING_STRIDE


CUES = [
    ("fd_50F6_0F06", "fd_50F6_09F2", "fd_50F6_0B06", "fd_50F6_08EC", "fd_50F6_0AEA"),
    ("fd_50F6_0EF6", "fd_50F6_08DE", "fd_50F6_0AD8", "fd_50F6_0852", "fd_50F6_0ACA"),
    ("fd_50F6_0F10", "fd_50F6_0A8A", "fd_50F6_0C3A", "fd_50F6_0A02", "fd_50F6_0B08"),
    ("fd_50F6_0F2E", "fd_50F6_0AB2", "fd_50F6_0D9A", "fd_50F6_0AA2", "fd_50F6_0D68"),
]
TIMER_NAMES = ("fd_50F6_050C", "fd_50F6_0732", "fd_50F6_059A",
               "fd_50F6_0620", "fd_50F6_07C4")
MESSAGE_FLAGS = ("fd_50F6_1046", "fd_50F6_1064", "fd_50F6_104A",
                 "fd_50F6_1062", "fd_50F6_107C")
MESSAGE_INDEXES = ("fd_50F6_0F3C", "fd_50F6_0FF8", "fd_50F6_0F7A",
                   "fd_50F6_0FC0", "fd_50F6_103A")


def make_case(label, seed, rng):
    writes = [w("fd_3D57_07B2", seed["updates_enabled"]),
              w("fd_3D57_07BE", seed["sprite_state"]),
              w("fd_50F6_047E", seed["cue_pause"]),
              w("MapPlane", seed["view_plane"]),
              w("fd_50F6_0508", seed["view_left"], seed["view_top"]),
              w("fd_50F6_10E0", seed["view_columns"]),
              w("fd_50F6_10DE", seed["view_rows"]),
              w("fd_55B3_19BE", seed["pixel_width"]),
              w("fd_55B3_19C0", seed["pixel_height"]),
              w("fd_50F6_1092", 0)]
    cue_seed = []
    for i, names in enumerate(CUES):
        active, displayed, displayed_plane, pending, pending_plane = names
        cue = seed["cue"][i]
        cue_seed.append(cue)
        writes += [w(active, cue["active"]),
                   w(displayed, cue["displayed_x"], cue["displayed_y"]),
                   w(displayed_plane, cue["displayed_plane"]),
                   w(pending, cue["pending_x"], cue["pending_y"]),
                   w(pending_plane, cue["pending_plane"])]
    for names, vals, size in ((TIMER_NAMES, seed["timers"], 4),
                              (MESSAGE_FLAGS, seed["flags"], 2),
                              (MESSAGE_INDEXES, seed["indexes"], 2)):
        for name, value in zip(names, vals):
            writes.append((addr(name), s32(value) if size == 4 else word(value)))
    table_ptrs = []
    string_bytes = bytearray(5 * 4 * STRING_STRIDE)
    pointer_map = {}
    table_values = seed["tables"]
    for table_id, entries in enumerate(table_values):
        table_at = TABLE_BASE + table_id * TABLE_STRIDE
        table_ptrs.append(table_at)
        pointers = []
        for index, text in enumerate(entries):
            if text is None:
                pointers.append((0, 0))
            else:
                off = cell(table_id, index)
                pointers.append((off, TEXT_SEG))
                data = cstring(text)
                begin = (table_id * 4 + index) * STRING_STRIDE
                string_bytes[begin:begin + len(data)] = data
                pointer_map[(TEXT_SEG, off)] = (table_id, index, text)
        pointers += [(0, 0)] * (4 - len(pointers))
        table_data = b"".join(words(off, seg) for off, seg in pointers)
        writes.append((TEXT_SEG * 16 + table_at, table_data))
        writes.append((addr(TABLE_VARIABLES[table_id]), words(table_at, TEXT_SEG)))
    writes.append((TEXT_SEG * 16 + STRING_BASE, bytes(string_bytes)))
    observes = [behavior.Range("cue_and_balloon_state", addr("fd_50F6_0F06"), 0xA0),
                behavior.Range("queue_count", addr("fd_50F6_1092"), 2),
                behavior.Range("queue_position", addr("fd_50F6_04C8"), 24),
                behavior.Range("queue_plane", addr("fd_50F6_04F6"), 12),
                behavior.Range("queue_style", addr("fd_50F6_04E6"), 12),
                behavior.Range("queue_pointer", addr("fd_50F6_04A6"), 24)]
    case = behavior.Case(label, writes=writes, observe=observes,
                         callbacks=clock_random_callbacks(), return_kind="void",
                         state={"ticks": seed.get("ticks", [1000] * 64),
                                "rand": seed.get("rand_values",
                                         {"SRand2": [0, 1, 0, 1, 0, 0],
                                          "SRand4": [0, 1, 2, 3, 0, 1],
                                          "SRand32": [3, 7, 11, 13, 17, 19, 23, 29],
                                          "SRand64": [5, 9, 13, 17]}),
                                "tick_at": 0, "rand_at": {}, "service_log": []},
                         metadata={"suite": "balloon_draw_current_v1",
                                   "contract": "DrawCurBalloons state, timer selection, typed message table identity and AddMsg queue",
                                   "host_boundary": "deterministic TickCount/SRand providers and borrowed terminated source string tables"})
    return case, pointer_map


def clock_random_callbacks():
    def tick(machine, args):
        state = machine.state
        index = state["tick_at"]
        value = state["ticks"][index]
        state["tick_at"] += 1
        state["service_log"].append(["TickCount", value])
        return value & 0xFFFF, (value >> 16) & 0xFFFF
    def rand_named(name):
        def call(machine, args):
            state = machine.state
            index = state["rand_at"].get(name, 0)
            value = state["rand"][name][index]
            state["rand_at"][name] = index + 1
            state["service_log"].append([name, value])
            return value
        return call
    cb = {"TickCount": behavior.Callback(stack_words=0, handler=tick)}
    for name in ("SRand2", "SRand4", "SRand32", "SRand64"):
        cb[name] = behavior.Callback(stack_words=0, handler=rand_named(name))
    return cb


def native_frame(seed):
    frame = BalloonFrame()
    frame.updates_enabled = seed["updates_enabled"]
    frame.sprite_state = seed["sprite_state"]
    frame.cue_pause = seed["cue_pause"]
    frame.queue.viewport = Viewport(seed["view_plane"], seed["view_left"],
                                    seed["view_top"], seed["view_columns"],
                                    seed["view_rows"])
    frame.queue.pixel_width = seed["pixel_width"]
    frame.queue.pixel_height = seed["pixel_height"]
    for i, cue in enumerate(seed["cue"]):
        target = frame.cue[i]
        target.active = cue["active"]
        target.displayed = ViewportPoint(cue["displayed_x"], cue["displayed_y"])
        target.displayed_plane = cue["displayed_plane"]
        target.pending = ViewportPoint(cue["pending_x"], cue["pending_y"])
        target.pending_plane = cue["pending_plane"]
    frame.timers = CueTimers(*seed["timers"])
    frame.messages = CueMessages(*seed["flags"], *seed["indexes"])
    return frame


def native_draw(library, seed, pointer_map, state):
    frame = native_frame(seed)
    buffers = []
    tick_values = state["ticks"]
    tick_at = [0]
    tick_log = []
    rand_values = state["rand"]
    rand_at = {name: 0 for name in rand_values}
    service_log = []
    owned_text = {}
    for key, (_, _, text) in pointer_map.items():
        owned_text[key] = ctypes.create_string_buffer(text.encode("ascii"))
        buffers.append(owned_text[key])
    table_text = {(table, index): (entries[index] if index < len(entries) else None)
                  for table, entries in enumerate(seed["tables"])
                  for index in range(4)}
    def tick(context):
        value = tick_values[tick_at[0]]
        tick_at[0] += 1
        tick_log.append(value)
        service_log.append(["TickCount", value])
        return value
    def random_call(context, family):
        name = ("SRand2", "SRand4", "SRand32", "SRand64")[family]
        index = rand_at[name]
        value = rand_values[name][index]
        rand_at[name] += 1
        service_log.append([name, value])
        return value
    def lookup(context, ident, out_text):
        if not ident or ident.contents.table > 4:
            return 0
        key = (int(ident.contents.table), int(ident.contents.index))
        if key not in table_text:
            return 0
        text = table_text[key]
        ident.contents.is_null = int(text is None)
        out_text[0] = None if text is None else ctypes.cast(owned_text[(TEXT_SEG,
            cell(key[0], key[1]))], ctypes.c_char_p)
        return 1
    tick_cb = TickCallback(tick)
    random_cb = RandomCallback(random_call)
    text_cb = TextCallback(lookup)
    services = Services(None, tick_cb, random_cb, text_cb)
    status = library.portable_balloon_draw_current(ctypes.byref(frame),
                                                    ctypes.byref(services))
    return int(status), frame, service_log, buffers


def oracle_state(machine, pointer_map):
    def word_at(name, index=0):
        return signed16(machine.word(addr(name) + index * 2))
    def long_at(name):
        value = int.from_bytes(machine.read(addr(name), 4), "little")
        return value - 0x100000000 if value & 0x80000000 else value
    cue = []
    for names in CUES:
        active, display, dplane, pending, pplane = names
        cue.append({"active": word_at(active),
                    "displayed_x": word_at(display),
                    "displayed_y": word_at(display, 1),
                    "displayed_plane": word_at(dplane),
                    "pending_x": word_at(pending),
                    "pending_y": word_at(pending, 1),
                    "pending_plane": word_at(pplane)})
    timers = [long_at(n) for n in TIMER_NAMES]
    flags = [word_at(n) for n in MESSAGE_FLAGS]
    indexes = [word_at(n) & 0xFFFF for n in MESSAGE_INDEXES]
    count = machine.word(addr("fd_50F6_1092"))
    queue = []
    for i in range(min(count, 6)):
        px = word_at("fd_50F6_04C8", i * 2)
        py = word_at("fd_50F6_04C8", i * 2 + 1)
        plane = word_at("fd_50F6_04F6", i)
        style = word_at("fd_50F6_04E6", i)
        ptr_at = addr("fd_50F6_04A6") + i * 4
        key = (machine.word(ptr_at + 2), machine.word(ptr_at))
        if key == (0, 0):
            table, index, is_null = 0xFFFF, 0xFFFF, 1
        elif key not in pointer_map:
            raise ValueError(f"unrecognized balloon string pointer {key}")
        else:
            table, index, _ = pointer_map[key]
            is_null = 0
        queue.append((px, py, plane, style, table, index, is_null))
    return {"cue": cue, "timers": timers, "flags": flags, "indexes": indexes,
            "queue": queue, "queue_count": count}


def native_state(frame):
    cue = []
    for c in frame.cue:
        cue.append({"active": int(c.active), "displayed_x": int(c.displayed.x),
                    "displayed_y": int(c.displayed.y),
                    "displayed_plane": int(c.displayed_plane),
                    "pending_x": int(c.pending.x), "pending_y": int(c.pending.y),
                    "pending_plane": int(c.pending_plane)})
    timers = [int(frame.timers.fight_first), int(frame.timers.fight_second),
              int(frame.timers.egg), int(frame.timers.queen), int(frame.timers.rest)]
    flags = [int(frame.messages.fight_first_enabled),
             int(frame.messages.fight_second_enabled), int(frame.messages.egg_enabled),
             int(frame.messages.queen_enabled), int(frame.messages.rest_enabled)]
    indexes = [int(frame.messages.fight_first_index),
               int(frame.messages.fight_second_index), int(frame.messages.egg_index),
               int(frame.messages.queen_index), int(frame.messages.rest_index)]
    queue = []
    for entry in native_queue(frame.queue):
        if entry[6]:
            entry = (*entry[:4], 0xFFFF, 0xFFFF, 1)
        queue.append(entry)
    return {"cue": cue, "timers": timers, "flags": flags, "indexes": indexes,
            "queue": queue, "queue_count": int(frame.queue.count)}


def fixture_cases():
    empty = [["fight one", "fight two", None], ["fight alt", None],
             ["egg line", "egg next", None], ["queen line", None],
             ["rest line", "rest next", None]]
    all_pending = [{"active": 0, "displayed_x": 4, "displayed_y": 5,
                    "displayed_plane": 1, "pending_x": 11+i,
                    "pending_y": 27, "pending_plane": 2} for i in range(4)]
    all_active = [{"active": 1, "displayed_x": 11+i, "displayed_y": 27,
                   "displayed_plane": 2, "pending_x": -1, "pending_y": -1,
                   "pending_plane": 3} for i in range(4)]
    base = {"updates_enabled": 1, "sprite_state": -1, "cue_pause": 0,
            "view_plane": 2, "view_left": 0, "view_top": 0,
            "view_columns": 40, "view_rows": 30, "pixel_width": 16,
            "pixel_height": 16, "timers": [0, 0, 0, 0, 0],
            "flags": [0, 0, 0, 0, 0], "indexes": [0, 0, 0, 0, 0],
            "tables": empty}
    fixtures = []
    s = dict(base, cue=all_pending)
    fixtures.append(("directed/all-pending-all-types", s))
    s = dict(base, cue=all_active, cue_pause=1, flags=[1, 1, 1, 1, 1])
    fixtures.append(("directed/pause-still-queues", s))
    s = dict(base, cue=all_pending, updates_enabled=0)
    fixtures.append(("directed/update-disabled", s))
    s = dict(base, cue=all_pending, sprite_state=0)
    fixtures.append(("directed/sprite-gate", s))
    s = dict(base, cue=all_active, timers=[2000]*5,
             flags=[1, 0, 1, 0, 1], indexes=[0, 1, 1, 0, 0])
    fixtures.append(("directed/timers-not-due-existing-flags", s))
    s = dict(base, cue=all_active, timers=[0]*5, indexes=[0, 0, 0, 0, 0])
    fixtures.append(("directed/timer-select-wrap-terminated-tables", s))
    s = dict(base, cue=all_active, timers=[-0x80000000] * 5,
             ticks=[0x7FFFFFF0] * 64,
             rand_values={"SRand2": [1, 1, 1], "SRand4": [1, 1],
                          "SRand32": [31, 31, 31, 31], "SRand64": [63]})
    fixtures.append(("directed/long-timer-signed-wrap", s))
    rng = random.Random(0xB41100)
    for i in range(48):
        cue = []
        for n in range(4):
            active = rng.choice([0, 0, 1, 2])
            pending = rng.choice([True, False])
            px = rng.randrange(6, 36) if pending else -1
            py = rng.randrange(5, 28) if pending else -1
            cue.append({"active": active, "displayed_x": rng.randrange(6, 36),
                        "displayed_y": rng.randrange(5, 28),
                        "displayed_plane": rng.randrange(4),
                        "pending_x": px, "pending_y": py,
                        "pending_plane": rng.randrange(4)})
        tables = []
        for table in range(5):
            length = rng.randrange(1, 3)
            tables.append([f"t{table}-m{j}" for j in range(length)] + [None])
        s = dict(base, cue=cue, cue_pause=rng.randrange(2),
                 updates_enabled=rng.choice([0, 1]),
                 sprite_state=rng.choice([-1, 0, 1]),
                 timers=[rng.choice([0, 500, 1500, 2000]) for _ in range(5)],
                 flags=[rng.randrange(2) for _ in range(5)],
                 indexes=[rng.randrange(3) for _ in range(5)], tables=tables,
                 view_plane=rng.randrange(4))
        fixtures.append((f"random/{i:03d}", s))
    return fixtures


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    dll = OUT / "balloon_queue_model.dll"
    import subprocess
    subprocess.run(["C:/msys64/mingw64/bin/gcc.exe", "-std=c11", "-O2",
                    "-Wall", "-Wextra", "-Werror", "-shared", "-I",
                    str(ROOT / "portable"), str(MODEL),
                    str(ROOT / "portable/ui_model/balloons/balloons.c"),
                    "-o", str(dll)], cwd=ROOT, check=True)
    library = ctypes.CDLL(str(dll))
    library.portable_balloon_draw_current.argtypes = [ctypes.POINTER(BalloonFrame),
                                                       ctypes.POINTER(Services)]
    library.portable_balloon_draw_current.restype = ctypes.c_int
    pair = behavior.PreparedPair("DrawCurBalloons", source=SOURCE,
        out=Path("build/workers/behavior_text_card/balloon_draw_current/prepared"))
    ledger = behavior_ledger.CaseLedger(
        OUT / "drawcur-cases.jsonl.gz", pair,
        ["return and caller ABI", "cue points/active flags", "timer/message/index state",
         "ordered TickCount/SRand family service calls", "typed message table/index identity",
         "AddMsgBalloon six-entry queue normalized state"])
    rows = []
    totals = {"dos_candidate_equal": 0, "native_dos_equal": 0,
              "service_order_equal": 0, "errors": 0}
    fixtures = fixture_cases()
    for label, seed in fixtures:
        try:
            case, pointer_map = make_case(label, seed, None)
            result = pair.compare(case)
            ledger.record(case, result, lane="directed" if label.startswith("directed/") else "randomized")
            expected = oracle_state(pair.original_machine, pointer_map)
            status, frame, native_calls, keepalive = native_draw(
                library, seed, pointer_map, case.state)
            actual = native_state(frame)
            native_equal = status == 0 and actual == expected
            original_calls = [[x["name"], x["args"]] for x in result.original["raw_trace"]]
            simplified_original = []
            original_tick_at = 0
            for name, args in original_calls:
                if name == "TickCount":
                    value = case.state["ticks"][original_tick_at]
                    original_tick_at += 1
                    simplified_original.append([name, value])
                else:
                    key = name
                    index = sum(1 for q in simplified_original if q[0] == name)
                    value = case.state["rand"][key][index]
                    simplified_original.append([name, value])
            service_equal = native_calls == simplified_original
            totals["dos_candidate_equal"] += int(result.equal)
            totals["native_dos_equal"] += int(native_equal)
            totals["service_order_equal"] += int(service_equal)
            rows.append({"id": label, "input": seed, "oracle_state": expected,
                         "native_state": actual, "native_status": status,
                         "native_equals_dos": native_equal,
                         "dos_candidate_equal": bool(result.equal),
                         "oracle_calls": simplified_original,
                         "native_calls": native_calls,
                         "service_order_equal": service_equal,
                         "candidate_diff": result.diff})
        except Exception as exc:
            totals["errors"] += 1
            rows.append({"id": label, "error": str(exc)})
    ledger_pin = ledger.finalize()
    count = len(fixtures)
    report = {"schema": "balloon-draw-current-differential-v1",
              "status": "PASS_BOUNDED_COMPARISON" if
                  totals["native_dos_equal"] == count and
                  totals["service_order_equal"] == count and totals["errors"] == 0
                  else "FAIL",
              "target": "root:m0250 DrawCurBalloons plus native balloon queue model",
              "case_count": count, "directed_count": 7, "random_count": count-7,
              "random_seed": 0xB41100, "totals": totals,
              "source": {"path": SOURCE.relative_to(ROOT).as_posix(), "sha256": sha(SOURCE)},
              "model": {"path": MODEL.relative_to(ROOT).as_posix(), "sha256": sha(MODEL)},
              "candidate_identity": pair.identity,
              "case_ledger": ledger_pin,
              "limits": ["Finite fixture text tables with borrowed strings; no caption inventing.",
                         "Logical cue selection and queue only; no physical balloon rendering.",
                         "Original DOS helper outputs are controlled TickCount/SRand providers.",
                         "DrawBalloons rendering contract is separate and pinned in its evidence packet."],
              "cases": rows}
    path = OUT / "report.json"
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": report["status"], "cases": count,
                      "totals": totals, "report": str(path)}, indent=2))
    if report["status"] != "PASS_BOUNDED_COMPARISON":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
