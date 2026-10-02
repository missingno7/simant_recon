#!/usr/bin/env python3
"""Compare the native menu selector to original DOS S10 behavior."""
from __future__ import annotations

import ctypes
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
PORT = ROOT / "portable"
BUILD = ROOT / "build/portable/menu-interaction-differential"
SOURCE = ROOT / "portable/ui_model/menus/interaction.c"
MENU_SOURCE = ROOT / "portable/ui_model/menus/menu.c"
DATABASE_SOURCE = ROOT / "portable/game/resources/database.c"
FIXTURE = ROOT / "portable/tests/menus/menu_interaction_fixture.c"
ASSET_TEST = ROOT / "portable/tests/menus/test_menu_interaction.c"
MENU_SOURCE = ROOT / "portable/ui_model/menus/menu.c"
DATABASE_SOURCE = ROOT / "portable/game/resources/database.c"
REPORT = ROOT / "portable/tests/menus/evidence/menu-interaction-differential.json"

sys.path.insert(0, str(ROOT / "tools"))
import behavior as b
from behavior_suites import tutorial_menu as source_fixtures


class Span(ctypes.Structure):
    _fields_ = [("bytes", ctypes.POINTER(ctypes.c_uint8)),
                ("length", ctypes.c_size_t)]


class Input(ctypes.Structure):
    _fields_ = [("kind", ctypes.c_int), ("x", ctypes.c_int32),
                ("y", ctypes.c_int32), ("button_down", ctypes.c_int),
                ("key", ctypes.c_uint16), ("event_code", ctypes.c_uint16),
                ("event_xe", ctypes.c_uint16), ("event_h", ctypes.c_uint16),
                ("event_v", ctypes.c_uint16)]


class Result(ctypes.Structure):
    _fields_ = [("saved_rect", ctypes.c_int32 * 4),
                ("inner_rect", ctypes.c_int32 * 4),
                ("current_item", ctypes.c_int16),
                ("command_id", ctypes.c_int16),
                ("flushed_key", ctypes.c_int16),
                ("warp_x", ctypes.c_int16), ("warp_y", ctypes.c_int16),
                ("init_status", ctypes.c_uint16),
                ("final_status", ctypes.c_uint16),
                ("returned", ctypes.c_uint16),
                ("selection_written", ctypes.c_uint16),
                ("selection", ctypes.c_uint16),
                ("command_dispatched", ctypes.c_uint16),
                ("forwarded_event", ctypes.c_uint16),
                ("warped_pointer", ctypes.c_uint16),
                ("forwarded_event_words", ctypes.c_uint16 * 5)]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_native():
    BUILD.mkdir(parents=True, exist_ok=True)
    dll = BUILD / "menu-interaction.dll"
    subprocess.run(["gcc", "-std=c11", "-O2", "-Wall", "-Wextra",
                    "-Wconversion", "-Werror", "-shared", "-I", str(PORT),
                    str(SOURCE), str(MENU_SOURCE), str(DATABASE_SOURCE),
                    str(FIXTURE), "-o", str(dll)],
                   cwd=ROOT, check=True)
    lib = ctypes.CDLL(str(dll))
    run = lib.portable_menu_interaction_fixture_run
    run.argtypes = [ctypes.POINTER(Span), ctypes.c_size_t, ctypes.c_int16,
                    ctypes.c_int32, ctypes.c_size_t, ctypes.c_int16,
                    ctypes.c_int16, ctypes.c_int16, ctypes.c_int16,
                    ctypes.c_uint8, ctypes.POINTER(Input), ctypes.c_size_t,
                    ctypes.POINTER(Result)]
    run.restype = ctypes.c_int
    return lib, dll


def native_case(lib, items, *, menu=0, title_x=30, title_length=12,
                screen=(640, 400), line=12, char=8, selected=1, inputs=()):
    owners = [ctypes.create_string_buffer(item + b"\0") for item in items]
    spans = (Span * len(items))(*[
        Span(ctypes.cast(owner, ctypes.POINTER(ctypes.c_uint8)), len(item))
        for owner, item in zip(owners, items)])
    native_inputs = (Input * max(1, len(inputs)))(*(inputs or [Input()]))
    result = Result()
    status = lib.portable_menu_interaction_fixture_run(
        spans, len(items), menu, title_x, title_length,
        screen[0], screen[1], line, char, selected,
        native_inputs, len(inputs), ctypes.byref(result))
    if status != 0:
        raise RuntimeError(f"native menu fixture failed: {status}")
    return result


def make_inputs(case, result):
    state = case.state
    inputs = []
    for event in state.get("events", []):
        code = event[6]
        if (code >> 8) == 0xFE and (code & 0xFF) != 0:
            inputs.append(Input(3, 0, 0, 0, 0, code, event[7], event[4], event[5]))
        else:
            inputs.append(Input(3, 0, 0, 0, 0, code, event[7], event[4], event[5]))
    keys = list(state.get("keys", []))
    points = list(state.get("points", []))[1:]
    down = list(state.get("down", []))[1:]
    if points or down:
        n = max(len(points), len(down))
        for i in range(n):
            p = points[i] if i < len(points) else (0, 0)
            d = int(bool(down[i])) if i < len(down) else 0
            inputs.append(Input(1, p[0], p[1], d, 0, 0, 0, 0, 0))
    inputs.extend(Input(2, 0, 0, 0, key, 0, 0, 0, 0) for key in keys)
    return inputs


def original_outcome(pair, case):
    result = pair.original_machine.run(case)
    selection = bytes.fromhex(result["ranges"]["selection"])
    command = None
    rect = None
    forwarded = None
    for row in result["state"]["host_trace"]:
        if row[0] == "dispatch-event":
            if row[1] and (row[1][0] & 0xff00) == 0xfd00:
                command = row[1][0] & 0xffff
            elif row[1]:
                forwarded = row[1]
        elif row[0] == "save-screen-rect":
            rect = row[1]
    machine = pair.original_machine
    title_x = int.from_bytes(machine.read(b.symbol_address("fd_50F6_46A8"), 2), "little", signed=True)
    title_length = int.from_bytes(machine.read(b.symbol_address("fd_50F6_46BC"), 2), "little", signed=True)
    return result, selection, command, rect, forwarded, title_x, title_length


def main():
    lib, dll = load_native()
    asset_exe = BUILD / "menu-interaction-assets.exe"
    subprocess.run(["gcc", "-std=c11", "-O2", "-Wall", "-Wextra",
                    "-Wconversion", "-Werror", "-I", str(PORT),
                    str(ASSET_TEST), str(SOURCE), str(MENU_SOURCE),
                    str(DATABASE_SOURCE), "-o", str(asset_exe)],
                   cwd=ROOT, check=True)
    asset_result = subprocess.run([str(asset_exe), str(ROOT / "assets/SHARED")],
                                  cwd=ROOT, check=True, text=True,
                                  capture_output=True)
    pair = b.PreparedPair("o10_35F5_0384", out=BUILD / "oracle")
    cases = []
    default = [b" Alpha", b" Beta", b" Gamma"]
    cases.extend([
        source_fixtures.menu_case("key-next-enter", [ord("+"), 13],
                                  curmenu=0, items=default),
        source_fixtures.menu_case("key-previous-enter", [ord("-"), 13],
                                  curmenu=0, items=default),
        source_fixtures.menu_case("key-down-enter", [0x850, 13],
                                  curmenu=0, items=default),
        source_fixtures.menu_case("hotkey-second-character", [ord("B"), 13],
                                  curmenu=0, items=default),
        source_fixtures.menu_case("separator-skip", [ord("+"), ord("+"), 13],
                                  curmenu=0, items=[b" Alpha", b" -", b" Beta"]),
        source_fixtures.menu_case("disabled-skip", [ord("+"), ord("+"), 13],
                                  curmenu=0, items=[b" Alpha", b"\x80Beta", b" Gamma"]),
        source_fixtures.menu_case("disabled-hotkey-source-quirk", [ord("B"), 13],
                                  curmenu=0, items=[b" Alpha", b"\x80Beta", b" Gamma"]),
        source_fixtures.menu_case("escape-cancels-current", [27],
                                  curmenu=0, items=default, selected=2),
        source_fixtures.menu_case("other-menu-event-forwarded", [], curmenu=0,
            events=[(1, 0x1234, 0x2345, 0x3456, 11, 12, 0xFE01, 13)]),
        source_fixtures.menu_case("same-menu-event-ignored", [13], curmenu=0,
            events=[(2, 0x2234, 0x3345, 0x4456, 21, 22, 0xFE00, 23)]),
    ])
    # Derive directed mouse coordinates from the original saved rectangle so
    # the tests hit real item rows rather than a guessed screen location.
    probe = source_fixtures.menu_case("mouse-geometry-probe", [13],
                                     curmenu=0, items=default)
    _, _, _, probe_rect, _, _, _ = original_outcome(pair, probe)
    if probe_rect is None:
        raise RuntimeError("original selector did not save its pull-down rectangle")
    row_x = probe_rect[0] + 8 + 8
    row_y = probe_rect[1] + 3 + 6
    cases.extend([
        source_fixtures.menu_case("mouse-first-row", [], curmenu=0,
            items=default, points=[(0, 0), (row_x, row_y)],
            down=[False, True, False]),
        source_fixtures.menu_case("mouse-disabled-row", [], curmenu=0,
            items=[b" Alpha", b"\x80Beta", b" Gamma"],
            points=[(0, 0), (row_x, row_y + 12)], down=[False, True, False]),
        source_fixtures.menu_case("mouse-outside-dropdown", [], curmenu=0,
            items=default, points=[(0, 0), (4, 200)],
            down=[False, True, False]),
    ])
    rows = []
    for case in cases:
        initial_state = case.state.copy()
        original, selection, command, rect, forwarded, title_x, title_length = original_outcome(pair, case)
        items = initial_state["items"] if "items" in initial_state else case.metadata["validity"]["item_table"]
        curmenu = case.metadata["validity"]["current_menu"]
        native = native_case(lib, items, menu=curmenu,
            title_x=title_x,
            title_length=title_length,
            screen=tuple(case.metadata["validity"]["screen"]),
            line=case.metadata["validity"]["line_height"],
            char=case.metadata["validity"]["char_width"],
            selected=case.metadata["validity"]["initial_selection"],
            inputs=make_inputs(case, None))
        expected_ret = original["return"]
        native_ret = native.returned
        observed_selection = selection[0] if selection else None
        native_selection = native.selection
        native_command = native.command_id & 0xffff if native.command_dispatched else None
        native_rect = list(native.saved_rect)
        rect_matches = rect == native_rect if rect is not None else True
        event_matches = ((forwarded[0] & 0xffff) == native.forwarded_event_words[0]
                         if forwarded is not None else not native.forwarded_event)
        equal = (expected_ret == native_ret and observed_selection == native_selection and
                 command == native_command and rect_matches and event_matches)
        rows.append({"case": case.label, "equal": equal,
            "original_return": expected_ret, "native_return": native_ret,
            "original_selection": observed_selection, "native_selection": native_selection,
            "original_command_id": command, "native_command_id": native_command,
            "original_saved_rect": rect, "native_saved_rect": native_rect,
            "forwarded_event_match": event_matches})
        if not equal:
            raise SystemExit(json.dumps(rows[-1], indent=2))
    report = {
        "schema": "portable-menu-interaction-differential-v1",
        "status": "PASS",
        "target": pair.identity,
        "native": {"source": SOURCE.relative_to(ROOT).as_posix(),
                   "source_sha256": sha(SOURCE), "fixture": FIXTURE.relative_to(ROOT).as_posix(),
                   "fixture_sha256": sha(FIXTURE), "shared_library_sha256": sha(dll),
                   "resource_harness": ASSET_TEST.relative_to(ROOT).as_posix(),
                   "resource_harness_sha256": sha(ASSET_TEST),
                   "asset_test_observation": asset_result.stdout.strip()},
        "cases": {"directed": len(rows), "executed_original": len(rows),
                  "executed_native": len(rows), "mismatches": 0},
        "compared_effects": ["return code", "selected byte", "menu command ID",
                             "saved pull-down rectangle", "forwarded full event ID"],
        "domains": ["title-targeted menu index 0; valid menu strings in far pointer-table layout",
                    "+/- and DOS scan-key navigation", "second-byte letter accelerator",
                    "disabled and separator navigation; original hotkey quirk for disabled entries",
                    "mouse hit, disabled/outside-row, release and other-menu event"],
        "limits": ["Popup/context menu geometry with menu_index=-1 is unsupported.",
                   "SDL event collection and raster drawing remain host boundaries.",
                   "This finite UI interaction proof does not establish complete menu-system equivalence."],
        "results": rows,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k not in ("results", "target")}, indent=2))
    print(f"evidence: {REPORT.relative_to(ROOT).as_posix()}")


if __name__ == "__main__":
    main()
