#!/usr/bin/env python3
"""Run the original EndGameDialog with explicit UI/audio/lifecycle boundaries."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))
import behavior  # noqa: E402

SCORE_RUNNER = ROOT / "portable/tests/dialogs/run_calcscore_dos_differential.py"
spec = importlib.util.spec_from_file_location("calcscore_fixture", SCORE_RUNNER)
assert spec and spec.loader
score = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = score
spec.loader.exec_module(score)

SOURCE = ROOT / "src/S14/m384C.c"
OUTPUT = ROOT / "portable/tests/dialogs/evidence/end-game-original-dos-controls-20261002.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def far_pointer(linear: int) -> bytes:
    segment = 0xA000
    offset = linear - segment * 16
    return offset.to_bytes(2, "little") + segment.to_bytes(2, "little")


def common_writes(state: score.GameOverInput):
    case = score.dos_case("end-game-control", state)
    writes = list(case.writes)
    # EndGameDialog indexes the string tables, loaded by PrepareStrings in the
    # real session. Point this DOS control at stable synthetic far-pointer
    # tables; PrintfAtObj is intercepted, so pointed-to bytes are not rendered.
    for symbol, table_linear, count in (
        ("fd_50F6_0324", 0xA2000, 4),
        ("fd_50F6_0328", 0xA2100, 10),
    ):
        writes.append((behavior.symbol_address(symbol), far_pointer(table_linear)))
        entries = b"".join(far_pointer(0xA3000) for _ in range(count))
        writes.append((table_linear, entries))
    writes.append((0xA3000, b"End game test\0"))
    return writes


def callback_case(label: str, sound_enabled: int, losing_side: int,
                  event_value: int, abort_value: int, new_game_result: int):
    state = score.GameOverInput()
    state.history_cursor = 0
    state.history_count = 0
    state.scenario = 0
    state.health = 100
    state.world_ticks = 4100
    state.losing_side = losing_side
    state.sound_enabled = sound_enabled
    state.screen_width = 320
    traces = {"original": [], "candidate": []}
    mocks = {}

    def lane(machine):
        name = "candidate" if machine.candidate else "original"
        if name not in mocks:
            mocks[name] = {"open": 0, "events": [event_value],
                           "abort": [abort_value],
                           "new_game_result": new_game_result,
                           "event_index": 0, "abort_index": 0}
        return name, mocks[name]

    def log(machine, name, args):
        lane_name, _ = lane(machine)
        traces[lane_name].append({"name": name, "args": list(args)})

    def open_window(_machine, args):
        _, mock = lane(_machine)
        log(_machine, "win_Open", args)
        mock["open"] = 1

    def window_open(_machine, args):
        _, mock = lane(_machine)
        log(_machine, "win_IsWinOpen", args)
        return mock["open"]

    def window_events(_machine, args):
        _, mock = lane(_machine)
        log(_machine, "win_Events", args)
        result = mock["events"][mock["event_index"]]
        mock["event_index"] += 1
        return result

    def dialog_abort(_machine, args):
        _, mock = lane(_machine)
        log(_machine, "DialogAbortOrCont", args)
        result = mock["abort"][mock["abort_index"]]
        mock["abort_index"] += 1
        return result

    def close_window(_machine, args):
        _, mock = lane(_machine)
        log(_machine, "win_Close", args)
        mock["open"] = 0

    def song_done(_machine, args):
        log(_machine, "mySongIsDone", args)
        return 1

    def begin_song(_machine, args):
        log(_machine, "myBeginSong", args)

    def set_text(_machine, args):
        log(_machine, "win_PrintfAtObj", args)

    def set_font(_machine, args):
        log(_machine, "set_font", args)

    def wait_init(_machine, args):
        log(_machine, "DialogWaitInit", args)

    def new_game(_machine, args):
        _, mock = lane(_machine)
        log(_machine, "NewGame", args)
        return mock["new_game_result"]

    def menu_quit(_machine, args):
        log(_machine, "MenuQuit", args)

    callbacks = {
        "f_20E8_04B6": behavior.Callback(0, open_window,
                                          register_args=("ax",)),
        "f_20E8_0635": behavior.Callback(0, close_window,
                                          register_args=("ax",)),
        "f_22BF_09B0": behavior.Callback(0, window_open,
                                          register_args=("ax",)),
        "f_218D_03E8": behavior.Callback(0, window_events),
        "f_00F8_05F2": behavior.Callback(0, dialog_abort),
        "f_00DF_0138": behavior.Callback(0, song_done),
        "f_00DF_00B1": behavior.Callback(2, begin_song),
        "f_22BF_0D53": behavior.Callback(5, set_text),
        "f_24AB_02AD": behavior.Callback(1, set_font),
        "f_00F8_02F7": behavior.Callback(1, wait_init),
        "o15_384C_03C6": behavior.Callback(1, new_game),
        "o15_384C_01EE": behavior.Callback(0, menu_quit),
    }
    case = behavior.Case(
        label=label, args=[], writes=common_writes(state), callbacks=callbacks,
        return_kind="void",
        metadata={"scope": "original DOS EndGameDialog with explicit source UI/audio/NewGame/MenuQuit boundaries",
                  "sound_option_07AA": sound_enabled,
                  "losing_side_0366": losing_side,
                  "win_events_return": event_value,
                  "DialogAbortOrCont_return": abort_value,
                  "NewGame_return": new_game_result})
    return case, traces


def main() -> None:
    pair = behavior.PreparedPair("EndGameDialog", source=SOURCE)
    source_paths = [SOURCE, ROOT / "layout/symbols.json", SCORE_RUNNER,
                    ROOT / "tools/behavior.py", ROOT / "tools/functions.py",
                    ROOT / "tools/match.py", ROOT / "tools/exe.py",
                    ROOT / "tools/modules.py", ROOT / "tools/modctx.py",
                    ROOT / "tools/autosearch.py"]
    before = {path.relative_to(ROOT).as_posix(): digest(path)
              for path in source_paths}
    rows = []
    for args in (
        ("events-close/initial-song-and-quit", 1, 1, 1, 0, -1),
        ("abort-close/audio-disabled-and-newgame", 0, 0, 0, 1, 0),
    ):
        case, callback_trace = callback_case(*args)
        comparison = pair.compare(case)
        rows.append({"label": case.label, "equal": comparison.equal,
                     "metadata": case.metadata,
                     "original_return": comparison.original["return"],
                     "original_trace": comparison.original["trace"],
                     "candidate_trace": comparison.candidate["trace"],
                     "callback_trace": callback_trace,
                     "difference": comparison.diff})

    after = {path.relative_to(ROOT).as_posix(): digest(path)
             for path in source_paths}
    if before != after:
        raise SystemExit("source inputs changed during DOS EndGameDialog control")
    report = {
        "schema": "end-game-original-dos-controls-v1",
        "status": "PASS" if all(row["equal"] for row in rows) else "FAIL",
        "scope": "Actual 16-bit DOS EndGameDialog callback-order controls. Window, audio/song-done, text/resource rendering, WaitInit, NewGame, and MenuQuit are explicit host boundaries. It does not prove these services' native implementations or complete resource rendering.",
        "prepared_pair": pair.identity,
        "source_pins": before,
        "source_pins_after": after,
        "cases": rows,
        "source_aliases": {
            "f_00DF_0138": "mySongIsDone",
            "f_218D_03E8": "win_Events",
            "f_00F8_05F2": "DialogAbortOrCont",
            "f_00F8_02F7": "DialogWaitInit",
            "f_20E8_04B6": "win_Open",
            "f_20E8_0635": "win_Close",
            "o15_384C_03C6": "NewGame",
            "o15_384C_01EE": "MenuQuit"
        }
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"original DOS EndGameDialog controls: {len(rows)}")
    print(f"whole-module candidate controls: {sum(row['equal'] for row in rows)}/{len(rows)}")
    print(f"evidence: {OUTPUT.relative_to(ROOT)}")
    if report["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
