#!/usr/bin/env python3
"""Compare original DOS EndGameDialog callbacks with the native flow model."""
from __future__ import annotations

import ctypes
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))
import behavior  # noqa: E402

SCORE_RUNNER = ROOT / "portable/tests/dialogs/run_calcscore_dos_differential.py"
spec = importlib.util.spec_from_file_location("calcscore_fixture_flow_diff", SCORE_RUNNER)
assert spec and spec.loader
score = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = score
spec.loader.exec_module(score)

SOURCE = ROOT / "src/S14/m384C.c"
MODEL = ROOT / "portable/ui_model/dialogs/end_game_flow.c"
MODEL_HEADER = ROOT / "portable/ui_model/dialogs/end_game_flow.h"
ADAPTER = ROOT / "portable/tests/dialogs/end_game_flow_native_adapter.c"
RUNNER = Path(__file__).resolve()
OUTPUT = ROOT / "portable/tests/dialogs/evidence/end-game-dos-native-flow-20261002.json"
INPUT_CAPACITY = 8
TRACE_CAPACITY = 256
DOS_C_RNG_DGROUP_OFFSET = 0x7BBE

NORMALIZED_NAMES = {
    "f_00DF_00B1": "begin_song",
    "f_20E8_04B6": "open_window",
    "f_24AB_02AD": "set_font",
    "f_22BF_0D53": "formatted_object",
    "f_00F8_02F7": "dialog_wait_init",
    "f_22BF_09B0": "window_is_open",
    "f_218D_03E8": "window_events",
    "f_00F8_05F2": "dialog_abort_or_continue",
    "f_20E8_0635": "close_window",
    "f_00DF_0138": "song_done",
    "o15_384C_03C6": "new_game",
    "o15_384C_01EE": "menu_quit",
}
NATIVE_NAMES = {
    1: "begin_song", 2: "open_window", 3: "set_font",
    4: "scenario_text", 5: "score_text", 6: "level_text",
    7: "dialog_wait_init", 8: "window_is_open", 9: "window_events",
    10: "dialog_abort_or_continue", 11: "close_window", 12: "song_done",
    13: "new_game", 14: "menu_quit",
}


class NativeConfig(ctypes.Structure):
    _fields_ = [
        ("input", score.GameOverInput),
        ("s_seed", ctypes.c_uint16),
        ("c_seed", ctypes.c_uint32),
        ("start_open_after_open", ctypes.c_int16),
        ("new_game_result", ctypes.c_int16),
        ("event_count", ctypes.c_uint16),
        ("events", ctypes.c_int16 * INPUT_CAPACITY),
        ("abort_count", ctypes.c_uint16),
        ("aborts", ctypes.c_int16 * INPUT_CAPACITY),
        ("song_done_count", ctypes.c_uint16),
        ("song_done", ctypes.c_int16 * INPUT_CAPACITY),
    ]


class NativeEvent(ctypes.Structure):
    _fields_ = [("kind", ctypes.c_int16), ("argc", ctypes.c_int16),
                ("args", ctypes.c_int32 * 4)]


class NativeResult(ctypes.Structure):
    _fields_ = [
        ("status", ctypes.c_int16), ("phase", ctypes.c_int16),
        ("outcome", ctypes.c_int16), ("new_game_result", ctypes.c_int16),
        ("s_before", ctypes.c_uint16), ("s_after", ctypes.c_uint16),
        ("c_before", ctypes.c_uint32), ("c_after", ctypes.c_uint32),
        ("event_count", ctypes.c_uint16),
        ("events", NativeEvent * TRACE_CAPACITY),
    ]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def word(value: int) -> bytes:
    return struct.pack("<H", value & 0xffff)


def far_pointer(linear: int) -> bytes:
    segment = 0xA000
    return struct.pack("<HH", linear - segment * 16, segment)


def game_state(scenario: int, sound: int, losing_side: int,
               screen_width: int = 320) -> score.GameOverInput:
    state = score.GameOverInput()
    state.history_cursor = 0
    state.history_count = 0
    state.scenario = scenario
    state.health = 100
    state.food_total = 100
    state.blue_workers = 2
    state.red_workers = 1
    state.world_ticks = 4100 if scenario != 2 else 8100
    state.sound_enabled = sound
    state.screen_width = screen_width
    state.losing_side = losing_side
    return state


def dos_writes(state: score.GameOverInput, s_seed: int,
               s_seed_address: int, c_seed_address: int,
               c_seed: int) -> list[tuple[int, bytes]]:
    case = score.dos_case("flow-control", state)
    writes = list(case.writes)
    for symbol, table_linear, count in (
        ("fd_50F6_0324", 0xA2000, 4),
        ("fd_50F6_0328", 0xA2100, 10),
    ):
        writes.append((behavior.symbol_address(symbol), far_pointer(table_linear)))
        strings_base = 0xA3000 if table_linear == 0xA2000 else 0xA3200
        entries = b"".join(far_pointer(strings_base + index * 0x20)
                            for index in range(count))
        writes.append((table_linear, entries))
        for index in range(count):
            writes.append((strings_base + index * 0x20,
                           f"table-{table_linear:x}-{index}\0".encode()))
    writes.append((0xA1000, b"\xA5" * 16))
    writes.append((s_seed_address, word(s_seed)))
    writes.append((c_seed_address, struct.pack("<I", c_seed & 0xffffffff)))
    return writes


def make_case(case_data: dict, native_function):
    state = game_state(case_data["scenario"], case_data["sound_enabled"],
                       case_data["losing_side"], case_data["screen_width"])
    native = NativeConfig()
    native.input = state
    native.s_seed = case_data["s_seed"]
    native.c_seed = case_data["c_seed"]
    native.start_open_after_open = int(case_data["start_open_after_open"])
    native.new_game_result = case_data["new_game_result"]
    for key, field in (("events", "event_count"),
                       ("aborts", "abort_count"),
                       ("song_done", "song_done_count")):
        values = case_data[key]
        setattr(native, field, len(values))
        array_name = {"events": "events", "aborts": "aborts",
                      "song_done": "song_done"}[key]
        array = getattr(native, array_name)
        for index, value in enumerate(values):
            array[index] = value
    native_result = NativeResult()
    if not native_function(ctypes.byref(native), ctypes.byref(native_result)):
        raise RuntimeError(f"native flow failed for {case_data['name']}: status={native_result.status}")
    native_trace = [normalize_native_event(native_result.events[i])
                    for i in range(native_result.event_count)]

    pair = make_case.pair
    trace_by_lane = {"original": [], "candidate": []}
    lane_state = {}

    def lane(machine):
        name = "candidate" if machine.candidate else "original"
        if name not in lane_state:
            lane_state[name] = {"open": 0, "event_index": 0,
                                "abort_index": 0, "song_done_index": 0,
                                "rrand_calls": 0}
        return name, lane_state[name]

    def append(machine, name, args, output=None):
        lane_name, _ = lane(machine)
        entry = {"name": name, "args": list(args)}
        if output is not None:
            entry["output"] = output
        trace_by_lane[lane_name].append(entry)

    def open_window(machine, args):
        lane_name, mock = lane(machine)
        mock["open"] = int(case_data["start_open_after_open"])
        append(machine, "open_window", args)

    def query_open(machine, args):
        _, mock = lane(machine)
        append(machine, "window_is_open", args, mock["open"])
        return mock["open"]

    def query_events(machine, args):
        _, mock = lane(machine)
        index = mock["event_index"]
        value = case_data["events"][index] if index < len(case_data["events"]) else 0
        mock["event_index"] += 1
        append(machine, "window_events", args, value)
        return value

    def query_abort(machine, args):
        _, mock = lane(machine)
        index = mock["abort_index"]
        value = case_data["aborts"][index] if index < len(case_data["aborts"]) else 0
        mock["abort_index"] += 1
        append(machine, "dialog_abort_or_continue", args, value)
        return value

    def close_window(machine, args):
        _, mock = lane(machine)
        mock["open"] = 0
        append(machine, "close_window", args)

    def query_song_done(machine, args):
        _, mock = lane(machine)
        index = mock["song_done_index"]
        values = case_data["song_done"]
        value = values[index] if index < len(values) else 0
        mock["song_done_index"] += 1
        append(machine, "song_done", args, value)
        return value

    def resource_or_score(machine, args):
        obj = args[0]
        if obj == 0x403:
            bits = (args[3] & 0xffff) | ((args[4] & 0xffff) << 16)
            value = bits - 0x100000000 if bits & 0x80000000 else bits
            append(machine, "score_text", [obj, value])
            return
        pointer = (args[2] << 4) + args[1]
        if obj == 0x402:
            index = (pointer - 0xA3000) // 0x20
            append(machine, "scenario_text", [obj, 1001, index])
        elif obj == 0x404:
            index = (pointer - 0xA3200) // 0x20
            append(machine, "level_text", [obj, 1900, index])
        else:
            raise RuntimeError(f"unexpected formatted object {obj:#x}")

    def count_rrand(machine, args):
        _, mock = lane(machine)
        mock["rrand_calls"] += 1
        append(machine, "RRand", args)
        return 0

    callbacks = {
        "f_00DF_00B1": behavior.Callback(2, lambda m, a: append(m, "begin_song", a)),
        "f_20E8_04B6": behavior.Callback(0, open_window, register_args=("ax",)),
        "f_24AB_02AD": behavior.Callback(1, lambda m, a: append(m, "set_font", a)),
        "f_22BF_0D53": behavior.Callback(5, resource_or_score),
        "f_00F8_02F7": behavior.Callback(1, lambda m, a: append(m, "dialog_wait_init", a)),
        "f_22BF_09B0": behavior.Callback(0, query_open, register_args=("ax",)),
        "f_218D_03E8": behavior.Callback(0, query_events),
        "f_00F8_05F2": behavior.Callback(0, query_abort),
        "f_20E8_0635": behavior.Callback(0, close_window, register_args=("ax",)),
        "f_00DF_0138": behavior.Callback(0, query_song_done),
        "o15_384C_03C6": behavior.Callback(1, lambda m, a: (append(m, "new_game", a, case_data["new_game_result"]), case_data["new_game_result"])[1]),
        "o15_384C_01EE": behavior.Callback(0, lambda m, a: append(m, "menu_quit", a)),
        "RRand": behavior.Callback(1, count_rrand),
    }
    before_by_lane = {}
    after_by_lane = {}
    for lane_name, machine in (("original", pair.original_machine),
                               ("candidate", pair.candidate_machine)):
        live = behavior.Case(
            label=case_data["name"], args=[],
            writes=dos_writes(state, case_data["s_seed"], pair.s_seed_address,
                              pair.c_seed_address, case_data["c_seed"]),
            callbacks=callbacks, return_kind="void",
            observe=[behavior.Range("s_rng", pair.s_seed_address, 2),
                     behavior.Range("c_rng", pair.c_seed_address, 4)])
        before_by_lane[lane_name] = case_data["s_seed"]
        machine.run(live)
        after_by_lane[lane_name] = int.from_bytes(
            machine.read(pair.s_seed_address, 2), "little")
        c_after = int.from_bytes(machine.read(pair.c_seed_address, 4), "little")
        if lane_name == "original":
            original_c_after = c_after
        else:
            candidate_c_after = c_after

    result = {
        "name": case_data["name"],
        "native_trace": native_trace,
        "original_trace": trace_by_lane["original"],
        "candidate_trace": trace_by_lane["candidate"],
        "native_s_rng": {"before": native_result.s_before,
                         "after": native_result.s_after},
        "original_s_rng": {"before": before_by_lane["original"],
                           "after": after_by_lane["original"]},
        "candidate_s_rng": {"before": before_by_lane["candidate"],
                            "after": after_by_lane["candidate"]},
        "native_c_rng": {"before": native_result.c_before,
                         "after": native_result.c_after},
        "original_c_rng": {"before": case_data["c_seed"],
                           "after": original_c_after},
        "candidate_c_rng": {"before": case_data["c_seed"],
                            "after": candidate_c_after},
        "original_rrand_calls": lane_state["original"]["rrand_calls"],
        "candidate_rrand_calls": lane_state["candidate"]["rrand_calls"],
        "native_status": native_result.status,
        "native_outcome": native_result.outcome,
        "new_game_result": native_result.new_game_result,
        "trace_equal": native_trace == trace_by_lane["original"] ==
                       trace_by_lane["candidate"],
        "s_rng_equal": (native_result.s_before == before_by_lane["original"] ==
                        before_by_lane["candidate"] and
                        native_result.s_after == after_by_lane["original"] ==
                        after_by_lane["candidate"]),
        "c_rng_unchanged": (native_result.c_before == native_result.c_after and
                            original_c_after == case_data["c_seed"] and
                            candidate_c_after == case_data["c_seed"]),
    }
    return result


def normalize_native_event(event: NativeEvent) -> dict:
    args = list(event.args[:event.argc])
    if event.kind == 8:
        output = args[1]
        args = [args[0]]
    elif event.kind in (9, 10, 12):
        output = args[0]
        args = []
    elif event.kind == 13:
        output = args[1]
        args = [args[0]]
    else:
        output = None
    entry = {"name": NATIVE_NAMES[event.kind], "args": args}
    if output is not None:
        entry["output"] = output
    return entry


def cases() -> list[dict]:
    return [
        {"name": "event-close-negative-newgame", "scenario": 0,
         "sound_enabled": 1, "losing_side": 1, "screen_width": 320,
         "start_open_after_open": 1, "events": [1], "aborts": [],
         "song_done": [1], "new_game_result": -1,
         "s_seed": 0x4a31, "c_seed": 0x53a7c921},
        {"name": "abort-close-audio-disabled", "scenario": 0,
         "sound_enabled": 0, "losing_side": 0, "screen_width": 320,
         "start_open_after_open": 1, "events": [0], "aborts": [1],
         "song_done": [1], "new_game_result": 0,
         "s_seed": 0x91e3, "c_seed": 0x19c412e7},
        {"name": "initially-closed-negative-newgame", "scenario": 0,
         "sound_enabled": 1, "losing_side": 1, "screen_width": 320,
         "start_open_after_open": 0, "events": [], "aborts": [],
         "song_done": [], "new_game_result": -1,
         "s_seed": 0x77b5, "c_seed": 0xa1059c33},
        {"name": "delayed-song-done-once", "scenario": 2,
         "sound_enabled": 1, "losing_side": 1, "screen_width": 640,
         "start_open_after_open": 1, "events": [0, 0, 0, 1],
         "aborts": [0, 0, 0], "song_done": [0, 0, 1, 1],
         "new_game_result": 1, "s_seed": 0x256b,
         "c_seed": 0x6f3b2771},
        {"name": "opening-win-song", "scenario": 1,
         "sound_enabled": 1, "losing_side": 0, "screen_width": 320,
         "start_open_after_open": 1, "events": [1], "aborts": [],
         "song_done": [0], "new_game_result": 0,
         "s_seed": 0xc351, "c_seed": 0x0f0e1d2c},
    ]


def main() -> None:
    compiler = os.environ.get("SIMANT_CC") or shutil.which("gcc")
    if not compiler:
        fallback = Path("C:/msys64/mingw64/bin/gcc.exe")
        compiler = str(fallback) if fallback.exists() else None
    if not compiler:
        raise SystemExit("Native C compiler missing; set SIMANT_CC")

    source_paths = [SOURCE, MODEL, MODEL_HEADER, ADAPTER, RUNNER,
                    SCORE_RUNNER, ROOT / "portable/ui_model/dialogs/game_over.c",
                    ROOT / "portable/ui_model/dialogs/game_over.h",
                    ROOT / "portable/game/simulation/rng.c",
                    ROOT / "portable/game/simulation/rng.h",
                    ROOT / "tools/behavior.py", ROOT / "tools/functions.py",
                    ROOT / "tools/match.py", ROOT / "tools/exe.py",
                    ROOT / "tools/modules.py", ROOT / "tools/modctx.py",
                    ROOT / "tools/autosearch.py", ROOT / "layout/symbols.json",
                    ROOT / "layout/functions.json",
                    ROOT / "src/root/m0093.c", ROOT / "assets/SIMANT.EXE",
                    ROOT / "assets/SHARED.NDX",
                    ROOT / "assets/SHARED.DAT"]
    before = {path.relative_to(ROOT).as_posix(): digest(path)
              for path in source_paths}
    pair = behavior.PreparedPair("EndGameDialog", source=SOURCE)
    seed_function = behavior.functions.get("SetSRandSeed")
    seed_code = pair.original_machine.read(
        seed_function["seg"] * 16 + seed_function["off"], seed_function["size"])
    seed_store = seed_code.find(b"\xA3")
    if seed_store < 0 or seed_store + 2 >= len(seed_code):
        raise SystemExit("could not derive source SRand storage from SetSRandSeed")
    pair.s_seed_address = behavior.match.DGROUP_SEG * 16 + int.from_bytes(
        seed_code[seed_store + 1:seed_store + 3], "little")
    pair.c_seed_address = behavior.match.DGROUP_SEG * 16 + DOS_C_RNG_DGROUP_OFFSET
    pair.seed_store_evidence = {
        "function": "SetSRandSeed", "function_entry": seed_function,
        "function_bytes": seed_code.hex(), "store_opcode_offset": seed_store,
        "DGROUP_segment": behavior.match.DGROUP_SEG,
        "DGROUP_offset": pair.s_seed_address - behavior.match.DGROUP_SEG * 16,
        "C_RNG_DGROUP_offset": DOS_C_RNG_DGROUP_OFFSET,
    }
    make_case.pair = pair
    dll_name = "end-game-flow-native.dll" if os.name == "nt" else "libend-game-flow-native.so"
    build_root = ROOT / "build/portable/tests"
    build_root.mkdir(parents=True, exist_ok=True)
    rows = []
    native = None
    with tempfile.TemporaryDirectory(prefix="end-game-flow-diff-",
                                     dir=build_root) as temporary:
        library_path = Path(temporary) / dll_name
        command = [compiler, "-shared", "-std=c11", "-O0", "-Wall", "-Wextra",
                   "-Werror", "-I", str(ROOT / "portable"), str(MODEL),
                   str(ROOT / "portable/ui_model/dialogs/game_over.c"),
                   str(ROOT / "portable/game/simulation/rng.c"), str(ADAPTER),
                   "-o", str(library_path)]
        built = subprocess.run(command, cwd=ROOT, text=True,
                               capture_output=True, timeout=60)
        if built.returncode:
            raise SystemExit(built.stdout + built.stderr)
        native = ctypes.CDLL(str(library_path))
        native.sim_end_game_flow_run_control.argtypes = [
            ctypes.POINTER(NativeConfig), ctypes.POINTER(NativeResult)]
        native.sim_end_game_flow_run_control.restype = ctypes.c_int
        try:
            rows = [make_case(case, native.sim_end_game_flow_run_control)
                    for case in cases()]
        finally:
            if os.name == "nt" and native is not None:
                free_library = ctypes.windll.kernel32.FreeLibrary
                free_library.argtypes = [ctypes.c_void_p]
                free_library.restype = ctypes.c_int
                free_library(ctypes.c_void_p(native._handle))
            del native
    after = {path.relative_to(ROOT).as_posix(): digest(path)
             for path in source_paths}
    if before != after:
        raise SystemExit("source inputs changed during DOS/native EndGame flow comparison")
    report = {
        "schema": "end-game-original-dos-native-flow-v1",
        "status": "PASS" if all(row["trace_equal"] and row["s_rng_equal"] and
                                 row["c_rng_unchanged"] and
                                 row["original_rrand_calls"] == 0 and
                                 row["candidate_rrand_calls"] == 0
                                 for row in rows) else "FAIL",
        "scope": "Original 16-bit DOS EndGameDialog versus native SimEndGameFlow using identical initial score input and controlled host query scripts. The original source and whole-module candidate run in Unicorn with actual SetSRandSeed/GetSRandSeed/SRand2; resource strings, window/events, wait, audio/song status, NewGame, and MenuQuit are explicit callbacks. Native host callbacks are adapter controls. This is modal ordering/RNG parity only; not resource rendering, menu persistence, or live-window service proof.",
        "prepared_pair": pair.identity,
        "s_rng_storage_derivation": pair.seed_store_evidence,
        "source_pins": before,
        "source_pins_after": after,
        "cases": rows,
        "c_rng_note": "Original and candidate DOS DGROUP:7BBE C-runtime seed dword is captured before/after and unchanged; native SimRng c_state is also unchanged. Instrumented RRand entry count is zero on both DOS lanes.",
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"original DOS vs native EndGame flow: {sum(r['trace_equal'] for r in rows)}/{len(rows)} traces")
    print(f"S-RNG parity: {sum(r['s_rng_equal'] for r in rows)}/{len(rows)}; report: {OUTPUT.relative_to(ROOT)}")
    if report["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
