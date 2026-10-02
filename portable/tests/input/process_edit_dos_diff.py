#!/usr/bin/env python3
"""Compare native click DTO translation and processEdit against DOS code."""
from __future__ import annotations

import argparse
import ctypes as ct
import hashlib
import json
import struct
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))
import behavior

GCC = Path("C:/msys64/mingw64/bin/gcc.exe")
DTO_SOURCE = ROOT / "portable/tests/input/process_edit_event_dto.c"
DTO_HEADER = ROOT / "portable/tests/input/process_edit_event_dto.h"
MAPAREA_SOURCE = ROOT / "src/S04/m35F5.c"
EDIT_SOURCE = ROOT / "src/S22/m39C7.c"
EVENT_LINEAR = 0x40000
EVENT_SEG = EVENT_LINEAR >> 4
EVENT_OFF = EVENT_LINEAR & 0xF


class Event8(ct.Structure):
    _fields_ = [(name, ct.c_int16) for name in
                ("what", "message", "x4", "modifiers", "h", "v", "code", "xE")]


class Rect(ct.Structure):
    _fields_ = [(name, ct.c_int16) for name in ("left", "top", "right", "bottom")]


class Geometry(ct.Structure):
    _fields_ = [("map_rect", Rect), ("edit_rect", Rect)] + [
        (name, ct.c_int16) for name in
        ("map_step_x", "map_step_y", "view_x", "view_y", "edit_step_x", "edit_step_y")]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def signed_word(value: int) -> bytes:
    return struct.pack("<h", value)


def words(*values: int) -> bytes:
    return struct.pack("<" + "h" * len(values), *values)


def event_words(event: Event8) -> list[int]:
    return list(struct.unpack("<8h", bytes(event)))


def write_global(name: str, data: bytes) -> tuple[int, bytes]:
    return behavior.symbol_address(name), data


def make_dto() -> tuple[ct.CDLL, Path, list[str]]:
    out = ROOT / "build/behavior/process-edit-dto.dll"
    out.parent.mkdir(parents=True, exist_ok=True)
    command = [str(GCC), "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
               "-shared", "-I", str(ROOT / "portable/tests/input"),
               str(DTO_SOURCE), "-o", str(out)]
    subprocess.run(command, check=True, cwd=ROOT)
    dll = ct.CDLL(str(out))
    dll.sim_maparea_release_to_process_edit.argtypes = [
        ct.POINTER(Event8), ct.POINTER(Geometry), ct.POINTER(Event8)]
    dll.sim_maparea_release_to_process_edit.restype = ct.c_int
    return dll, out, command


def native_dto(dll, event: Event8, geometry: Geometry) -> Event8:
    output = Event8()
    accepted = dll.sim_maparea_release_to_process_edit(
        ct.byref(event), ct.byref(geometry), ct.byref(output))
    if accepted != 1:
        raise AssertionError("native DTO rejected a directed in-rect release")
    return output


def callback_preserving(handler):
    def wrapped(machine, args):
        saved = {name: machine.reg(name) for name in ("si", "di", "bp", "ds")}
        result = handler(machine, args)
        for name, value in saved.items():
            machine.set_reg(name, value)
        return result
    return wrapped


def capture_process_event(machine, args):
    offset, segment = args[:2]
    machine.state["process_edit_event_hex"] = machine.read(segment * 16 + offset, 16).hex()


def event_machine_case(event: Event8, geometry: Geometry, state=None):
    writes = [(EVENT_LINEAR, bytes(event))]
    m = geometry.map_rect
    e = geometry.edit_rect
    writes += [
        write_global("fd_50F6_10D2", words(m.left, m.top, m.right, m.bottom)),
        write_global("fd_50F6_110C", words(e.left, e.top, e.right, e.bottom)),
        write_global("fd_50F6_0508", words(geometry.view_x, geometry.view_y)),
        write_global("fd_50F6_3856", signed_word(geometry.map_step_x)),
        write_global("fd_50F6_3858", signed_word(geometry.map_step_y)),
        write_global("fd_55B3_19BE", signed_word(geometry.edit_step_x)),
        write_global("fd_55B3_19C0", signed_word(geometry.edit_step_y)),
    ]
    callbacks = {
        "processEdit": behavior.Callback(
            2, callback_preserving(capture_process_event), pop=0),
        "WinPrintf": behavior.Callback(0, callback_preserving(lambda m, a: None)),
    }
    return behavior.Case(
        "MapAreaEvent-release-DTO", args=[EVENT_OFF, EVENT_SEG], writes=writes,
        callbacks=callbacks, return_kind="void", state=state or {})


def edit_callbacks():
    def tick(machine, _args):
        value = machine.state["tick"]
        machine.state["tick"] = (value + 1) & 0xFFFFFFFF
        return value & 0xFFFF, (value >> 16) & 0xFFFF

    def ret(value):
        return callback_preserving(lambda _machine, _args: value)

    return {
        "WinPrintf": behavior.Callback(0, callback_preserving(lambda m, a: None)),
        "win_IsWinInFront": behavior.Callback(0, ret(1), register_args=("ax",)),
        "TickCount": behavior.Callback(0, callback_preserving(tick)),
        "win_GetEvent": behavior.Callback(2, ret(0), pop=4),
        "myButton": behavior.Callback(0, ret(0)),
    }


OBSERVED_GLOBALS = (
    ("MapPlane", 2), ("fd_50F6_0F44", 2), ("fd_50F6_0A8E", 2),
    ("fd_50F6_0AA0", 2), ("fd_50F6_0AF8", 2), ("fd_50F6_0AD6", 2),
    ("fd_50F6_0AE8", 2), ("fd_50F6_0D6C", 2), ("fd_50F6_0508", 4),
)


def edit_case(name: str, normalized_event: Event8, geometry: Geometry,
              plane: int, scenario: int, tile_kind: str,
              target_x: int, target_y: int):
    # processEdit consumes logical edit pixels and converts them back to map
    # coordinates using 110C, 19BE/19C0, and the current view origin.
    event_address = EVENT_LINEAR
    writes = [(event_address, bytes(normalized_event))]
    edit_rect = geometry.edit_rect
    writes += [
        write_global("MapPlane", signed_word(plane)),
        write_global("fd_50F6_0EAC", signed_word(scenario)),
        write_global("fd_50F6_105E", signed_word(-1)),
        write_global("fd_50F6_048C", signed_word(1 if plane == 0 else plane)),
        write_global("fd_50F6_0A06", signed_word(0)),
        write_global("fd_50F6_0F44", signed_word(1)),
        write_global("fd_50F6_04C2", signed_word(0)),
        write_global("fd_50F6_04E2", signed_word(0)),
        write_global("fd_50F6_0508", words(geometry.view_x, geometry.view_y)),
        write_global("fd_50F6_110C", words(edit_rect.left, edit_rect.top,
                                             edit_rect.right, edit_rect.bottom)),
        write_global("fd_55B3_19BE", signed_word(geometry.edit_step_x)),
        write_global("fd_55B3_19C0", signed_word(geometry.edit_step_y)),
    ]
    # Tile data for the actual original IsItDigable/GetMap/IsThisGrass/
    # IsLiftable helpers: dirt, grass, pebble, or ordinary solid terrain.
    tile = {"dirt": 0x20, "grass": 0x1C, "pebble": 0x30,
            "solid": 0x40, "empty": 0}.get(tile_kind, 0)
    if plane >= 2:
        map_name = "MapB" if plane == 2 else "MapR"
        map_address = behavior.symbol_address(map_name) + target_x * 64 + target_y
        writes.append((map_address, bytes([tile])))
    ranges = [behavior.Range(n, behavior.symbol_address(n), size)
              for n, size in OBSERVED_GLOBALS]
    callbacks = edit_callbacks()
    case = behavior.Case(name, args=[EVENT_OFF, EVENT_SEG], writes=writes,
                         observe=ranges, callbacks=callbacks,
                         return_kind="void", state={"tick": 100})
    return case


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="portable/tests/input/evidence/process-edit-dos-diff.json")
    args = parser.parse_args()
    dto_dll, dto_path, dto_command = make_dto()
    geometry = Geometry(Rect(100, 80, 600, 400), Rect(18, 24, 640, 400),
                        2, 2, 12, 8, 4, 4)
    map_pair = behavior.PreparedPair("MapAreaEvent", source=MAPAREA_SOURCE,
                                     out=ROOT / "build/behavior/process-edit-maparea")
    edit_pair = behavior.PreparedPair("processEdit", source=EDIT_SOURCE,
                                      out=ROOT / "build/behavior/process-edit")
    rows = []
    for plane in range(4):
        target = [(40, 20), (42, 21), (30, 1), (62, 10)][plane]
        tile_kinds = {
            0: ("empty",), 1: ("empty",),
            2: ("dirt", "pebble", "solid"),
            3: ("grass", "pebble", "solid"),
        }[plane]
        for scenario in (1, 2):
            for tile in tile_kinds:
                for source_modifiers, branch in ((0x0800, "normal"),
                                                   (0x4000, "source-shift"),
                                                   (0x6000, "source-shift-combined")):
                    raw = Event8(0x0102, 0x0001, 0x0042, source_modifiers,
                                 100 + target[0] * geometry.map_step_x,
                                 80 + target[1] * geometry.map_step_y,
                                 0x0102, 0)
                    normalized = native_dto(dto_dll, raw, geometry)
                    map_result = map_pair.compare(
                        event_machine_case(raw, geometry, {"expected_event": ""}))
                    if not map_result.equal:
                        raise AssertionError(f"MapAreaEvent candidate differs: {map_result.diff}")
                    actual_event_hex = map_result.original["state"].get("process_edit_event_hex")
                    if actual_event_hex != bytes(normalized).hex():
                        raise AssertionError(
                            f"native DTO/source MapAreaEvent mismatch: {actual_event_hex} != {bytes(normalized).hex()}")
                    case_id = f"plane-{plane}-scenario-{scenario}-{branch}-{tile}"
                    edit_result = edit_pair.compare(edit_case(
                        case_id, normalized, geometry, plane, scenario, tile,
                        target[0], target[1]))
                    if not edit_result.equal:
                        raise AssertionError(f"processEdit candidate differs: {edit_result.diff}")
                    observed = edit_result.original["ranges"]
                    if observed["fd_50F6_0AA0"] != "0100":
                        raise AssertionError(f"{case_id}: goal-present flag was not set")
                    if observed["fd_50F6_0AD6"] != signed_word(target[0]).hex():
                        raise AssertionError(f"{case_id}: unexpected goal x {observed['fd_50F6_0AD6']}")
                    if observed["fd_50F6_0AE8"] != signed_word(target[1]).hex():
                        raise AssertionError(f"{case_id}: unexpected goal y {observed['fd_50F6_0AE8']}")
                    rows.append({
                        "id": case_id,
                        "plane": plane, "scenario": scenario, "branch": branch,
                        "tile_fixture": tile,
                        "source_event_words": event_words(raw),
                        "processEdit_event_words": event_words(normalized),
                        "maparea_original_candidate_equal": map_result.equal,
                        "processEdit_original_candidate_equal": edit_result.equal,
                        "processEdit_original_ranges": observed,
                        "processEdit_callback_order": [x["name"] for x in edit_result.original["trace"]],
                        "tick_count_after": edit_result.original["state"].get("tick"),
                    })
    # An actual yellow ant with sentinel life FE takes the source's ant-hit
    # early return, proving clicks on ant cells do not become movement goals.
    ant_case = Event8(0x0102, 1, 0x0042, 0x0200,
                      geometry.edit_rect.left + (25 - geometry.view_x) * 4,
                      geometry.edit_rect.top + (20 - geometry.view_y) * 4,
                      0x0102, 0)
    ant_tile_case = edit_case("yellow-ant-sentinel-hit", ant_case, geometry,
                              1, 1, "empty", 25, 20)
    # Add the source LifeA[x][y] sentinel; IsItYellow/GetLife execute original.
    life_a = behavior.symbol_address("LifeA")
    ant_tile_case.writes.append((life_a + 25 * 64 + 20, b"\xfe"))
    ant_result = edit_pair.compare(ant_tile_case)
    if not ant_result.equal:
        raise AssertionError(f"ant-hit processEdit candidate differs: {ant_result.diff}")
    if ant_result.original["ranges"]["fd_50F6_0AA0"] != "0000":
        raise AssertionError("yellow-ant hit unexpectedly created a goal")
    rows.append({"id": "yellow-ant-sentinel-hit", "plane": 1, "scenario": 1,
                 "branch": "ant-hit-early-return", "event_words": event_words(ant_case),
                 "processEdit_original_candidate_equal": ant_result.equal,
                 "processEdit_original_ranges": ant_result.original["ranges"],
                 "processEdit_callback_order": [x["name"] for x in ant_result.original["trace"]]})

    report = {
        "schema": "process-edit-dos-click-differential-v1",
        "status": "PASS",
        "proof_lanes": {
            "DOS_candidate_differential": "original DOS MapAreaEvent/processEdit versus source-authored C compiled by MSC 6.00AX in Unicorn",
            "portable_native_C": "not exercised; native DTO tests verify Event8 field transformation only",
        },
        "scope": "Original DOS MapAreaEvent and processEdit execute in Unicorn against MSC-compiled historical C candidates. A separate native DTO transformation is compared byte-for-byte with the actual MapAreaEvent callback event. External window/timer/button services are controlled fixtures; simulation helpers run from the original DOS image.",
        "oracle_identity": map_pair.identity["oracle_sha256"],
        "pairs": {"MapAreaEvent": map_pair.identity, "processEdit": edit_pair.identity},
        "native_dto": {"source": str(DTO_SOURCE.relative_to(ROOT)),
                        "source_sha256": sha(DTO_SOURCE),
                        "header_sha256": sha(DTO_HEADER),
                        "binary_sha256": sha(dto_path),
                        "compile_command": dto_command},
        "environment": {"win_IsWinInFront": 1, "queued_events": 0,
                        "myButton": 0, "tick_start": 100,
                        "tick_policy": "returns then increments by one; six-tick wait ends at 106"},
        "event_producer": {
            "words": ["what", "message", "x4", "modifiers", "h", "v", "code", "xE"],
            "m1B73_036E_word_sources": {"modifiers": "AX", "h": "CX", "v": "DX",
                                         "code": "BX", "xE": "ES",
                                         "message": "BIOS 0040:0017", "x4": "BIOS 0040:006C",
                                         "what": "not written by this enqueue routine"},
            "ordinary_release_input_modifier": "0x0800",
            "MapAreaEvent_accept_mask": "0x4800",
            "ordinary_release_processEdit_modifier": "0x0200",
            "source_shift_raw_modifier": "0x4000 -> 0x2000"},
        "case_count": len(rows),
        "cases": rows,
        "proof_limitations": [
            "The MSC candidate lane is not a comparison against the SDL/native C implementation; the native DTO lane tests only event-field transformation.",
            "The exercise proves the mapped click event and the original processEdit behavior over these controlled states; it does not claim all window dispatcher routes or every possible game state.",
            "All generated records use code 0x0102 and exercise MapAreaEvent -> processEdit. They do not exercise Edit-object code 4 through ProcEditEvent.",
            "The 0x0800, 0x4000, and 0x6000 modifier values are controlled MapAreaEvent inputs, not a differential trace from a physical mouse button/keyboard event producer.",
            "The real enqueue routine _f_1B73_036E writes Event words +2 through +14 but leaves word +0 (what) untouched; this suite does not assert a value for what beyond its controlled fixture.",
            "The native DTO is test-only. Production input code remains owned by the engine/window agent.",
        ],
    }
    out = (ROOT / args.out).resolve()
    out.relative_to(ROOT)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"processEdit DOS click differential: PASS ({len(rows)} cases); {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
