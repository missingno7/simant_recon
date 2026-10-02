#!/usr/bin/env python3
"""Compare generated NEXT7 ProcMenu to the original DOS S11 entry."""
from __future__ import annotations

import ctypes as ct
import hashlib
import json
import shutil
import struct
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[3]
PORT = ROOT / "portable"
PROFILE = ROOT / "build/workers/recovered_source_next7/generated"
BUILD = ROOT / "build/workers/procmenu_differential"
NATIVE_SOURCE = PORT / "tests/menus/procmenu_native_probe.c"
NATIVE_ADAPTER = PORT / "game/recovered/menu_adapter.c"
SHARED_SOURCE = PORT / "tests/menus/procmenu_shared_ids.c"
MENU_INTERACTION = PORT / "ui_model/menus/interaction.c"
MENU_MODEL = PORT / "ui_model/menus/menu.c"
DB_SOURCE = PORT / "game/resources/database.c"
REPORT = PORT / "tests/menus/evidence/procmenu-next7-dos-differential-adapter-complete-closure-20261002.json"

sys.path.insert(0, str(ROOT / "tools"))
import behavior as b
import exe as exe_mod
import functions

HOST_NAMES = {
    1: "AboutDialog", 2: "myBeginSong", 3: "NewGame", 4: "OpenEditWindow",
    5: "OpenMapYard", 6: "OpenModeWindow", 7: "OpenCasteWindow",
    8: "OpenHistoryWindow", 9: "OpenInfoWindow", 10: "ScoreDialog",
    11: "SetYardMode", 12: "SetMapPlane", 13: "win_IsWinOpen",
    14: "MapToYard", 15: "StopSong", 16: "SetMenuItemState",
    17: "f_1FD2_0135", 18: "EditMessage", 19: "clip_SetWin",
    20: "win_SetObjSelectedState", 21: "clip_Off",
    22: "EndLifeTransferMode", 23: "EndTargetMode",
}
HOST_ARG_COUNTS = {
    1: 0, 2: 2, 3: 1, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0, 10: 0,
    11: 1, 12: 1, 13: 1, 14: 0, 15: 0, 16: 2, 17: 2, 18: 3,
    19: 1, 20: 2, 21: 0, 22: 0, 23: 0,
}


class NativeInput(ct.Structure):
    _fields_ = [(name, ct.c_int16) for name in (
        "command_id", "scenario_state", "paused", "current_tool",
        "map_plane", "yard_mode", "speed", "yard_window_open",
        "new_game_return")]
    _fields_.append(("option_states", ct.c_int16 * 7))


class NativeHostEvent(ct.Structure):
    _fields_ = [("kind", ct.c_int16), ("args", ct.c_int32 * 4)]


class NativeOutput(ct.Structure):
    _fields_ = [(name, ct.c_int16) for name in (
        "scenario_state", "paused", "current_tool", "map_plane",
        "yard_mode", "speed")]
    _fields_ += [("option_states", ct.c_int16 * 7),
                 ("host_count", ct.c_uint16),
                 ("host", NativeHostEvent * 32)]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def native_dependency_closure(compiler: str) -> list[Path]:
    """Capture the actual non-system headers reached by the C compiler."""
    sources = [PROFILE / "S11_m35F5.c", PROFILE / "recovered_state.c",
               NATIVE_SOURCE, NATIVE_ADAPTER, SHARED_SOURCE, MENU_MODEL, DB_SOURCE]
    found: set[Path] = set()
    for source in sources:
        result = subprocess.run([
            compiler, "-std=c11", "-MM", f"-I{ROOT}", f"-I{PORT}",
            f"-I{PROFILE}", str(source),
        ], cwd=ROOT, text=True, capture_output=True, check=True, timeout=15)
        # GCC's make target appears first; remove only that target's colon so
        # drive letters in absolute dependency paths remain intact.
        dependency_text = result.stdout.split(":", 1)[1]
        dependency_text = dependency_text.replace("\\\r\n", " ").replace("\\\n", " ")
        # GCC emits native backslash paths on Windows; plain whitespace split
        # preserves those path separators (shlex would consume them).
        for token in dependency_text.split():
            path = Path(token)
            if not path.is_absolute(): path = ROOT / path
            found.add(path.resolve())
        found.add(source.resolve())
    # Python oracle/metadata code that chooses the original instructions,
    # symbols, vectors, and VM execution path, plus exact input resource bytes.
    found.update(path.resolve() for path in [
        Path(__file__),
        ROOT / "tools/behavior.py", ROOT / "tools/exe.py", ROOT / "tools/functions.py",
        ROOT / "tools/match.py", ROOT / "tools/modctx.py", ROOT / "tools/modules.py",
        ROOT / "tools/symbols.py", ROOT / "layout/functions.json",
        ROOT / "layout/manifest.json", ROOT / "layout/symbols.json",
        ROOT / "assets/SIMANT.EXE", ROOT / "assets/SHARED.DAT", ROOT / "assets/SHARED.NDX",
        PROFILE / "provenance.json",
        MENU_INTERACTION,
    ])
    return sorted(found)


def input_snapshot(paths: list[Path]) -> dict[str, str]:
    return {path.relative_to(ROOT).as_posix(): sha(path) for path in paths}


def binary_metadata(path: Path) -> dict[str, object]:
    data = path.read_bytes()
    if data[:2] != b"MZ" or len(data) < 0x40:
        raise RuntimeError("fresh native ProcMenu DLL is not a PE image")
    pe_offset = struct.unpack_from("<I", data, 0x3c)[0]
    if data[pe_offset:pe_offset + 4] != b"PE\0\0":
        raise RuntimeError("fresh native ProcMenu DLL has no PE signature")
    machine, sections = struct.unpack_from("<HH", data, pe_offset + 4)
    optional_magic = struct.unpack_from("<H", data, pe_offset + 24)[0]
    return {"path": path.relative_to(ROOT).as_posix(),
            "sha256": sha(path), "size_bytes": len(data),
            "pe_machine": f"0x{machine:04x}",
            "pe_sections": sections,
            "optional_header_magic": f"0x{optional_magic:04x}"}


def native_api():
    compiler = shutil.which("gcc") or "C:/msys64/mingw64/bin/gcc.exe"
    dll = BUILD / "procmenu-next7.dll"
    BUILD.mkdir(parents=True, exist_ok=True)
    subprocess.run([
        compiler, "-std=c11", "-Wall", "-Wextra", "-Werror", "-shared",
        f"-I{ROOT}", f"-I{PORT}", f"-I{PROFILE}",
        str(PROFILE / "S11_m35F5.c"), str(PROFILE / "recovered_state.c"),
        str(NATIVE_ADAPTER), str(NATIVE_SOURCE), "-o", str(dll),
    ], cwd=ROOT, check=True, timeout=30)
    lib = ct.CDLL(str(dll))
    run = lib.procmenu_native_run
    run.argtypes = [ct.POINTER(NativeInput), ct.POINTER(NativeOutput)]
    run.restype = ct.c_int
    negative = lib.procmenu_native_s22_layout_negative
    negative.argtypes = [ct.POINTER(NativeInput), ct.POINTER(NativeOutput)]
    negative.restype = ct.c_int
    return lib, run, negative, dll, compiler


def load_menu_map(compiler: str):
    exe_path = BUILD / "procmenu-shared-ids.exe"
    subprocess.run([
        compiler, "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
        f"-I{PORT}", str(SHARED_SOURCE), str(MENU_MODEL), str(DB_SOURCE),
        "-o", str(exe_path),
    ], cwd=ROOT, check=True, timeout=30)
    result = subprocess.run([str(exe_path), str(ROOT / "assets/SHARED")],
                            cwd=ROOT, text=True, capture_output=True,
                            check=True, timeout=10)
    menus = []
    titles = {}
    items = []
    for line in result.stdout.splitlines():
        pieces = line.split("|")
        if pieces[0] == "title":
            index = int(pieces[1])
            titles[index] = bytes.fromhex(pieces[2]).decode("latin1").lstrip(" ")
        elif pieces[0] == "item":
            menu, index, command = map(int, pieces[1:4])
            label = bytes.fromhex(pieces[4]).decode("latin1").lstrip(" ")
            items.append({"menu_index": menu, "item_index": index,
                          "command_id": command, "label": label})
    for row in items:
        row["title"] = titles[row["menu_index"]]
    return result.stdout, items


def initial_cases(menu_items):
    base = {
        "scenario_state": 0x1234, "paused": 0, "current_tool": -1,
        "map_plane": 1, "yard_mode": 2, "speed": 1,
        "yard_window_open": 0, "new_game_return": -7,
        "option_states": [0, 1, 0, 1, 0, 1, 0],
    }
    cases = []
    for item in menu_items:
        cases.append({"label": f"shared-{item['title']}-{item['item_index']}-{item['label']}",
                      "menu_item": item, **base})
        encoded = 0xFD00 | item["command_id"]
        signed_encoded = encoded - 0x10000
        cases.append({"label": f"shared-{item['title']}-{item['item_index']}-fd-high-byte",
                      "menu_item": item, "event_word": signed_encoded, **base})
    # Exercise each conditional in the yard-mode dispatch with a matched-mode,
    # map-plane zero, open-window state in addition to the default closed path.
    for menu_item in menu_items:
        command = menu_item["command_id"]
        if 0x21 <= command <= 0x24:
            cases.append({"label": f"yard-mode-{command:02x}-already-set-window-open",
                          "menu_item": menu_item, **base,
                          "yard_mode": command - 0x21, "map_plane": 0,
                          "yard_window_open": 1})
    # Pause/Unpause runs SetPause and SetMenuEntries, including both active
    # tool exit edges and each source AdviceStrs slot.
    pause_item = next(item for item in menu_items if item["command_id"] == 0x41)
    for paused in (0, 1):
        for current_tool in (-1, 10, 11):
            cases.append({"label": f"pause-state-{paused}-tool-{current_tool}",
                          "menu_item": pause_item, **base,
                          "paused": paused, "current_tool": current_tool})
    # Four speed choices need a different active choice to verify the selected
    # SetMenuItemState intents emitted by the actual SetMenuEntries body.
    for menu_item in menu_items:
        command = menu_item["command_id"]
        if 0x43 <= command <= 0x46:
            cases.append({"label": f"speed-{command:02x}-active-other",
                          "menu_item": menu_item, **base,
                          "speed": ((command - 0x43 + 1) % 4)})
    return cases


def source_ranges():
    return [
        ("scenario_state", b.symbol_address("fd_55B3_2CBC"), 2),
        ("paused", b.symbol_address("fd_50F6_047E"), 2),
        ("current_tool", b.symbol_address("fd_50F6_105E"), 2),
        ("map_plane", b.symbol_address("MapPlane"), 2),
        ("yard_mode", b.symbol_address("YardMode"), 2),
        ("speed", b.symbol_address("fd_3D57_07CC"), 2),
        ("option_states", b.symbol_address("fd_3D57_07A8"), 14),
    ]


def source_fixture(case):
    event_address = 0xA0100
    event_off, event_seg = event_address & 0xF, event_address >> 4
    table_address = 0xA2000
    table_off, table_seg = table_address & 0xF, table_address >> 4
    strings_address = 0xA3000
    table = bytearray()
    strings = bytearray()
    for index in range(18):
        address = strings_address + index * 32
        table.extend(struct.pack("<HH", address & 0xF, address >> 4))
        text = f"AdviceSlot{index}".encode("ascii") + b"\0"
        strings.extend(text + bytes(32 - len(text)))
    writes = [
        (event_address, struct.pack("<7h", 0x1234, 0x2345, 0x3456,
                                    0x4567, 0x5678, 0x6789,
                                    case.get("event_word", case["menu_item"]["command_id"]))),
        (b.symbol_address("fd_50F6_034C"), struct.pack("<HH", table_off, table_seg)),
        (table_address, bytes(table)),
        (strings_address, bytes(strings)),
        (b.symbol_address("fd_55B3_2CBC"), struct.pack("<h", case["scenario_state"])),
        (b.symbol_address("fd_50F6_047E"), struct.pack("<h", case["paused"])),
        (b.symbol_address("fd_50F6_105E"), struct.pack("<h", case["current_tool"])),
        (b.symbol_address("MapPlane"), struct.pack("<h", case["map_plane"])),
        (b.symbol_address("YardMode"), struct.pack("<h", case["yard_mode"])),
        (b.symbol_address("fd_3D57_07CC"), struct.pack("<h", case["speed"])),
        (b.symbol_address("fd_3D57_07A8"), struct.pack("<7h", *case["option_states"])),
    ]
    return [event_off, event_seg], writes, {"event_linear": event_address,
        "event_message_offset": 12, "pointer_table_linear": table_address,
        "message_table": strings_address}


def callback_rows(machine):
    rows = []
    for entry in machine.trace:
        name, args = entry["name"], list(entry["args"])
        if name == "EditMessage":
            off, seg, ticks_lo, ticks_hi, mode = args
            address = seg * 16 + off if off or seg else 0
            slot = (address - 0xA3000) // 32 if 0xA3000 <= address < 0xA3000 + 18 * 32 else -1
            ticks = (ticks_hi << 16) | ticks_lo
            if ticks & 0x80000000: ticks -= 0x100000000
            args = [slot if address else -1, ticks, mode]
        elif name == "f_1FD2_0135":
            ident, off, seg = args
            address = seg * 16 + off
            raw = machine.read(address, 20).split(b"\0", 1)[0]
            args = [ident, raw.decode("latin1")]
        rows.append({"name": name, "args": args})
    return rows


def dos_case(pair, case):
    args, writes, meta = source_fixture(case)
    callbacks = {}
    noargs = ["AboutDialog", "OpenEditWindow", "OpenMapYard", "OpenModeWindow",
              "OpenCasteWindow", "OpenHistoryWindow", "OpenInfoWindow",
              "ScoreDialog", "MapToYard", "StopSong", "clip_Off",
              "EndLifeTransferMode", "EndTargetMode"]
    for name in noargs:
        callbacks[name] = b.Callback(0, lambda _m, _a: None)
    callbacks["myBeginSong"] = b.Callback(2, lambda _m, _a: None)
    callbacks["NewGame"] = b.Callback(1, lambda _m, _a: -7)
    callbacks["SetYardMode"] = b.Callback(1, lambda _m, _a: None)
    callbacks["SetMapPlane"] = b.Callback(1, lambda _m, _a: None)
    callbacks["win_IsWinOpen"] = b.Callback(0,
        lambda _m, _a: case["yard_window_open"], register_args=("ax",))
    callbacks["SetMenuItemState"] = b.Callback(2, lambda _m, _a: None)
    callbacks["f_1FD2_0135"] = b.Callback(3, lambda _m, _a: None)
    callbacks["EditMessage"] = b.Callback(5, lambda _m, _a: None)
    callbacks["clip_SetWin"] = b.Callback(1, lambda _m, _a: None)
    callbacks["win_SetObjSelectedState"] = b.Callback(0, lambda _m, _a: None,
                                                       register_args=("ax", "dx"))
    machine = b.Machine(pair)
    result = machine.run(b.Case(case["label"], args=args, writes=writes,
        callbacks=callbacks, return_kind="void",
        observe=[b.Range(name, address, size)
                 for name, address, size in source_ranges()],
        state={"fixture": meta}))
    state = b"".join(bytes.fromhex(result["ranges"][name])
                     for name, _, _ in source_ranges())
    return {"return": result["return"], "state_hex": state.hex(),
            "host": callback_rows(machine), "trace": result["trace"],
            "fixture": meta}


def native_case(run, case):
    data = NativeInput()
    for field in ("scenario_state", "paused", "current_tool", "map_plane",
                  "yard_mode", "speed", "yard_window_open", "new_game_return"):
        setattr(data, field, case[field])
    data.command_id = case.get("event_word", case["menu_item"]["command_id"])
    for i, value in enumerate(case["option_states"]): data.option_states[i] = value
    output = NativeOutput()
    if run(ct.byref(data), ct.byref(output)) != 0:
        raise RuntimeError(f"native ProcMenu failed: {case['label']}")
    state = struct.pack("<6h7h", output.scenario_state, output.paused,
        output.current_tool, output.map_plane, output.yard_mode, output.speed,
        *output.option_states)
    host = []
    for i in range(output.host_count):
        kind = int(output.host[i].kind)
        args = [int(output.host[i].args[j]) for j in range(HOST_ARG_COUNTS[kind])]
        if kind == 17:
            args[1] = {1: " Pause", 2: " Unpause"}.get(args[1], "<unknown>")
        host.append({"name": HOST_NAMES[kind], "args": args})
    return {"return": None, "state_hex": state.hex(), "host": host}


def main():
    compiler = shutil.which("gcc") or "C:/msys64/mingw64/bin/gcc.exe"
    dependencies = native_dependency_closure(compiler)
    inputs_before = input_snapshot(dependencies)
    dll_context = native_api()
    run, negative, dll, compiler = dll_context[1], dll_context[2], dll_context[3], dll_context[4]
    menu_stdout, menu_items = load_menu_map(compiler)
    pair = SimpleNamespace(function=functions.get("o11_35F5_018D"),
        vectors={b.exe.MANAGER_SEG * 16 + v.offset: v
                 for v in b.exe.load().vectors}, candidate=False)
    rows = []
    cases = initial_cases(menu_items)
    for case in cases:
        dos = dos_case(pair, case)
        native = native_case(run, case)
        equal = (dos["return"] is None and native["return"] is None and
                 dos["state_hex"] == native["state_hex"] and dos["host"] == native["host"])
        row = {"case": case["label"], "command_id": case["menu_item"]["command_id"],
               "menu_title": case["menu_item"]["title"],
               "menu_item": case["menu_item"]["label"], "equal": equal,
               "return": {"dos": dos["return"], "native": native["return"]},
               "touched_globals_equal": dos["state_hex"] == native["state_hex"],
               "dos_state_hex": dos["state_hex"], "native_state_hex": native["state_hex"],
               "ordered_host_effects_equal": dos["host"] == native["host"],
               "dos_host_effects": dos["host"], "native_host_effects": native["host"],
               "dos_entry_trace": dos["trace"]}
        rows.append(row)
        if not equal:
            print(json.dumps(row, indent=2))
            return 1

    about = next(case for case in cases if case["menu_item"]["command_id"] == 1
                 and "fd-high-byte" not in case["label"])
    negative_input = NativeInput()
    for field in ("scenario_state", "paused", "current_tool", "map_plane",
                  "yard_mode", "speed", "yard_window_open", "new_game_return"):
        setattr(negative_input, field, about[field])
    negative_input.command_id = 1
    for i, value in enumerate(about["option_states"]): negative_input.option_states[i] = value
    negative_output = NativeOutput()
    if negative(ct.byref(negative_input), ct.byref(negative_output)) != 0 or negative_output.host_count != 0:
        raise RuntimeError("negative S22-layout control unexpectedly dispatched S11 About")

    inputs_after = input_snapshot(dependencies)
    if inputs_after != inputs_before:
        raise RuntimeError("an input changed during the ProcMenu differential run")
    compiler_version = subprocess.run([compiler, "--version"], cwd=ROOT,
        text=True, capture_output=True, check=True, timeout=10).stdout.splitlines()[0]
    original_proc = b.exe.load().sections[11].data[397:397 + 18]

    output = {
        "schema": "generated-procmenu-dos-differential-v1",
        "status": "PASS",
        "claim": "Original DOS S11 ProcMenu compared with generated NEXT7 S11 ProcMenu for all command IDs present in SHARED resource 0, FD-prefixed signed event words proving low-byte dispatch, plus conditional yard-mode/pause/speed variants.",
        "scope": "Return (void), seven directly touched/global-observed fields, and ordered typed host leaves; SetPause and SetMenuEntries execute their actual source bodies for pause/toggle/speed branches.",
        "event_abi": {
            "DOS_instruction_bytes_hex": bytes(original_proc).hex(" "),
            "DOS_instruction_bytes": "S11 entry LES BX,[BP+6] followed by MOV SI,ES:[BX+0x0C]; the event command word is read at byte offset 12.",
            "historical_C_event_declaration": "src/S11/m35F5.c struct Event uses 16-bit DOS int fields and lays message after what, where[2], when[2], modifiers: byte offset 12; generated NEXT7 retains the explicit int16_t shape.",
            "source_event_size": 14,
            "source_event_message_offset": 12,
            "engine_SimRecoveredEvent_size": 16,
            "engine_SimRecoveredEvent_message_offset": 2,
            "implemented_public_bridge": "sim_recovered_source_proc_menu_command(uint16_t command) in portable/game/recovered/menu_adapter.c; public engine entry can be sim_recovered_engine_proc_menu_command(engine, uint16_t command, ...), forwarding to this bridge inside active state/host scope.",
            "negative_control": "For command 1, directly passing SimRecoveredEvent to ProcMenu yields no callback because S11 reads the zero code word at +12; the exact S11 adapter dispatches AboutDialog.",
        },
        "SHARED_menu_mapping": {
            "resource": "assets/SHARED, kind 6, resource id 0 at 640px (id 1 absent, source fallback selected)",
            "dropdown_formula": "command_id = ((menu_index << 4) + current_item - 0x2ff) & 0xff; current_item is zero-based, so IDs are (menu_index*16 + item_index + 1) mod 256.",
            "actual_items": menu_items,
            "resource_dump": menu_stdout,
        },
        "case_count": len(rows),
        "mismatch_count": 0,
        "cases": rows,
        "native": {"dll": binary_metadata(dll),
                   "dll_sha256": sha(dll),
                   "compiler": compiler,
                   "compiler_version": compiler_version,
                   "compiler_flags": ["-std=c11", "-Wall", "-Wextra", "-Werror", "-shared"],
                   "S11_sha256": sha(PROFILE / "S11_m35F5.c"),
                   "state_header_sha256": sha(PROFILE / "recovered_state.h"),
                   "state_source_sha256": sha(PROFILE / "recovered_state.c"),
                   "probe_sha256": sha(NATIVE_SOURCE),
                   "menu_adapter_sha256": sha(NATIVE_ADAPTER),
                   "menu_map_probe_sha256": sha(SHARED_SOURCE),
                   "menu_interaction_source_sha256": sha(MENU_INTERACTION)},
        "input_stability": {
            "stable_before_after": True,
            "hashed_inputs": inputs_after,
            "compiler_dependency_method": "GCC -MM non-system transitive dependencies for all seven linked C translation units; plus DOS oracle/parser/metadata/profile provenance and actual SHARED resource files.",
        },
        "oracle": {"exe_sha256": b.exe.load().sha256,
                   "target": functions.get("o11_35F5_018D"),
                   "harness_sha256": b.digest(b.HARNESS_SOURCE)},
        "boundaries": [
            "Dialogs, audio, open-window commands, yard/plane mutation services, StopSong, menu state/text, and pause UI effects are deterministic typed host leaves.",
            "win_IsWinOpen returns the configured deterministic value; SetYardMode/SetMapPlane/MapToYard are recorded leaves and do not run their own bodies.",
            "No live SDL/UI/full-game claim is made.",
        ],
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": output["status"], "cases": len(rows),
        "mismatches": 0, "negative_s22_control_callbacks": int(negative_output.host_count),
        "report": REPORT.relative_to(ROOT).as_posix()}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
