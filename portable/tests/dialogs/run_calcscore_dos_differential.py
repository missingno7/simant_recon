#!/usr/bin/env python3
"""Compare pure portable CalcScore results with the original DOS entrypoint."""
from __future__ import annotations

import ctypes
import hashlib
import json
import os
from pathlib import Path
import random
import shutil
import struct
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))
import behavior

MODEL = ROOT / "portable/ui_model/dialogs/game_over.c"
MODEL_HEADER = ROOT / "portable/ui_model/dialogs/game_over.h"
ADAPTER = ROOT / "portable/tests/dialogs/game_over_native_adapter.c"
RUNNER = Path(__file__).resolve()
SOURCE = ROOT / "src/S14/m384C.c"
SHARED_IDS = {
    "history_cursor": "fd_50F6_04F4",
    "history_count": "fd_3D57_0828",
    "health_history": "fd_50F6_073C",
    "blue_food_history": "fd_50F6_0626",
    "red_food_history": "fd_50F6_06AE",
    "food_total": "fd_50F6_0FC2",
    "food_used": "fd_50F6_1000",
    "blue_workers": "fd_50F6_09FA",
    "red_workers": "fd_50F6_0A00",
    "scenario": "fd_50F6_0EAC",
    "blue_colony_score": "fd_50F6_0A90",
    "colony_score_a": "fd_50F6_0AC4",
    "colony_score_b": "fd_50F6_0A9E",
    "tutorial_marks": "fd_3D57_00A4",
    "health": "MeHealth",
    "world_ticks": "fd_50F6_0C26",
    "losing_side": "fd_50F6_0366",
    "sound_word": "fd_3D57_07A8",
    "screen_width": "g_3DB2",
}


class GameOverInput(ctypes.Structure):
    _fields_ = [
        ("history_cursor", ctypes.c_int16),
        ("history_count", ctypes.c_int16),
        ("health_history", ctypes.c_int16 * 64),
        ("blue_food_history", ctypes.c_int16 * 64),
        ("red_food_history", ctypes.c_int16 * 64),
        ("food_total", ctypes.c_int32),
        ("food_used", ctypes.c_int32),
        ("blue_workers", ctypes.c_int16),
        ("red_workers", ctypes.c_int16),
        ("scenario", ctypes.c_int16),
        ("blue_colony_score", ctypes.c_int16),
        ("colony_score_a", ctypes.c_int16),
        ("colony_score_b", ctypes.c_int16),
        ("tutorial_marks", (ctypes.c_uint8 * 16) * 12),
        ("health", ctypes.c_int16),
        ("world_ticks", ctypes.c_int32),
        ("losing_side", ctypes.c_int16),
        ("sound_enabled", ctypes.c_uint8),
        ("screen_width", ctypes.c_uint16),
    ]


class GameOverResult(ctypes.Structure):
    _fields_ = [
        ("components", ctypes.c_int16 * 8),
        ("score", ctypes.c_int32),
        ("rank_score", ctypes.c_int32),
        ("level_index", ctypes.c_uint8),
        ("opening_sound_id", ctypes.c_int16),
        ("sound_argument", ctypes.c_int16),
        ("font_id", ctypes.c_int16),
        ("scenario_index", ctypes.c_int16),
        ("scenario_resource_id", ctypes.c_int16),
        ("level_resource_id", ctypes.c_int16),
        ("window_id", ctypes.c_int16),
        ("scenario_object_id", ctypes.c_int16),
        ("score_object_id", ctypes.c_int16),
        ("level_object_id", ctypes.c_int16),
    ]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def word(value: int) -> bytes:
    return struct.pack("<H", value & 0xffff)


def longword(value: int) -> bytes:
    return struct.pack("<I", value & 0xffffffff)


def build_input(label: str, rng: random.Random) -> GameOverInput:
    state = GameOverInput()
    state.history_cursor = rng.choice((0, 1, 31, 62, 63))
    state.history_count = rng.choice((0, 1, 2, 31, 62, 63))
    for index in range(64):
        state.health_history[index] = rng.choice((0, 10, 100, 1000, 30000, -32768, 32767))
        state.blue_food_history[index] = rng.choice((0, 1, 100, 1000, 30000, -1, 32767))
        state.red_food_history[index] = rng.choice((0, 1, 100, 1000, 30000, -1, 32767))
    state.food_total = rng.choice((0, 1, 100, 4100, 0x7fffffff, 0x7fff0000))
    state.food_used = rng.choice((0, 1, 50, 4099, 0x7fffffff, -1))
    state.blue_workers = rng.choice((0, 1, 100, 1000, 32767, -32768))
    state.red_workers = rng.choice((0, 1, 100, 1000, 32767, -32768))
    state.scenario = rng.randrange(4)
    state.blue_colony_score = rng.choice((0, 1, 100, 32767, -32768))
    state.colony_score_a = rng.choice((0, 1, 100, 32767, -32768))
    state.colony_score_b = rng.choice((0, 1, 100, 32767, -32768))
    for x in range(12):
        for y in range(16):
            state.tutorial_marks[x][y] = rng.choice((0, 0, 0, 1, 4, 255))
    state.health = rng.choice((0, 1, 10, 100, 32767, -32768))
    state.world_ticks = rng.choice((0, 1, 99, 100, 4099, 4100, 8099, 8100,
                                    2147483647, -1))
    state.losing_side = rng.randrange(2)
    state.sound_enabled = rng.randrange(2)
    state.screen_width = rng.choice((320, 640))
    return state


def fixtures() -> list[tuple[str, GameOverInput]]:
    directed = []
    for scenario in range(4):
        state = GameOverInput()
        state.history_cursor = 0
        state.history_count = 0
        state.scenario = scenario
        state.health = 100
        state.food_total = 100
        state.blue_workers = 2
        state.red_workers = 1
        state.world_ticks = (4099 if scenario != 2 else 8099)
        state.sound_enabled = 1
        state.screen_width = 320
        state.losing_side = scenario & 1
        directed.append((f"directed/scenario-{scenario}/near-time", state))
    for cursor, count in ((0, 0), (0, 63), (1, 1), (63, 63), (62, 2)):
        rng = random.Random((cursor << 8) | count | 0xC4A1)
        state = build_input(f"ring-{cursor}-{count}", rng)
        state.history_cursor, state.history_count = cursor, count
        directed.append((f"ring/cursor-{cursor}/count-{count}", state))
    for total, used in ((0, 0), (1, 0), (100, 100), (100, 101),
                        (0x7fffffff, -1), (0x7fff0000, 0x7fffffff)):
        state = GameOverInput()
        state.food_total, state.food_used = total, used
        state.scenario = 0
        state.health = 100
        state.blue_workers, state.red_workers = 1, 1
        state.world_ticks = 4100
        directed.append((f"food-long/{total}-{used}", state))
    random_source = random.Random(0xC45C0AE)
    for index in range(48):
        directed.append((f"seeded/{index}", build_input(str(index), random_source)))
    return directed


def add_write(writes: list[tuple[int, bytes]], symbol: str, value: bytes) -> None:
    writes.append((behavior.symbol_address(symbol), value))


def dos_case(label: str, state: GameOverInput) -> behavior.Case:
    writes: list[tuple[int, bytes]] = []
    add_write(writes, SHARED_IDS["history_cursor"], word(state.history_cursor))
    add_write(writes, SHARED_IDS["history_count"], word(state.history_count))
    add_write(writes, SHARED_IDS["health_history"],
              b"".join(word(value) for value in state.health_history))
    add_write(writes, SHARED_IDS["blue_food_history"],
              b"".join(word(value) for value in state.blue_food_history))
    add_write(writes, SHARED_IDS["red_food_history"],
              b"".join(word(value) for value in state.red_food_history))
    add_write(writes, SHARED_IDS["food_total"], longword(state.food_total))
    add_write(writes, SHARED_IDS["food_used"], longword(state.food_used))
    add_write(writes, SHARED_IDS["blue_workers"], word(state.blue_workers))
    add_write(writes, SHARED_IDS["red_workers"], word(state.red_workers))
    add_write(writes, SHARED_IDS["scenario"], word(state.scenario))
    add_write(writes, SHARED_IDS["blue_colony_score"], word(state.blue_colony_score))
    add_write(writes, SHARED_IDS["colony_score_a"], word(state.colony_score_a))
    add_write(writes, SHARED_IDS["colony_score_b"], word(state.colony_score_b))
    add_write(writes, SHARED_IDS["tutorial_marks"], bytes(state.tutorial_marks))
    add_write(writes, SHARED_IDS["health"], word(state.health))
    add_write(writes, SHARED_IDS["world_ticks"], longword(state.world_ticks))
    add_write(writes, SHARED_IDS["losing_side"], word(state.losing_side))
    sound_word = behavior.symbol_address(SHARED_IDS["sound_word"]) + 2
    writes.append((sound_word, word(state.sound_enabled)))
    add_write(writes, SHARED_IDS["screen_width"], word(state.screen_width))
    score_address = 0xA1000
    writes.append((score_address, b"\xA5" * 16))
    return behavior.Case(
        label=label,
        args=[0x1000, 0xA000],
        writes=writes,
        observe=[behavior.Range("scores", score_address, 16)],
        return_kind="s32",
        metadata={"suite": "calcscore_dos_model_v1",
                  "oracle": "hash-locked original DOS CalcScore",
                  "portable_scope": "pure CalcScore numeric contract only; no EndGameDialog modal or NewGame/MenuQuit flow proof"})


def main() -> None:
    compiler = os.environ.get("SIMANT_CC") or shutil.which("gcc")
    if not compiler:
        fallback = Path("C:/msys64/mingw64/bin/gcc.exe")
        compiler = str(fallback) if fallback.exists() else None
    if not compiler:
        raise SystemExit("Native C compiler missing; set SIMANT_CC")

    pair = behavior.PreparedPair("CalcScore", source=SOURCE)
    dll_name = "game-over-native.dll" if os.name == "nt" else "libgame-over-native.so"
    source_paths = [MODEL, MODEL_HEADER, ADAPTER, RUNNER, SOURCE,
                    ROOT / "tools/behavior.py", ROOT / "tools/functions.py",
                    ROOT / "tools/match.py", ROOT / "tools/exe.py",
                    ROOT / "tools/modules.py", ROOT / "tools/modctx.py",
                    ROOT / "tools/autosearch.py",
                    ROOT / "assets/SHARED.NDX", ROOT / "assets/SHARED.DAT"]
    hashes_before = {path.relative_to(ROOT).as_posix(): digest(path)
                     for path in source_paths}

    with tempfile.TemporaryDirectory(prefix="calcscore-dos-model-",
                                     dir=ROOT / "build/portable/tests") as temp:
        library_path = Path(temp) / dll_name
        command = [compiler, "-shared", "-std=c11", "-O0", "-Wall", "-Wextra",
                   "-Werror", str(MODEL), str(ADAPTER), "-o", str(library_path)]
        built = subprocess.run(command, cwd=ROOT, text=True, capture_output=True,
                               timeout=60)
        if built.returncode:
            print(built.stdout, end="")
            print(built.stderr, end="")
            raise SystemExit(built.returncode)
        native = ctypes.CDLL(str(library_path))
        native.sim_game_over_native_calculate.argtypes = [
            ctypes.POINTER(GameOverInput), ctypes.POINTER(GameOverResult)]
        native.sim_game_over_native_calculate.restype = ctypes.c_int
        native_hash = digest(library_path)

        comparisons = []
        source_control_mismatches = []
        model_mismatches = []
        rows = fixtures()
        for label, state in rows:
            case = dos_case(label, state)
            compared = pair.compare(case)
            if not compared.equal:
                source_control_mismatches.append({"label": label,
                                                  "diff": compared.diff})
                continue
            oracle_score_values = struct.unpack(
                "<8h", bytes.fromhex(compared.original["ranges"]["scores"]))
            oracle = {"score": compared.original["return"],
                      "components": list(oracle_score_values)}
            result = GameOverResult()
            model_status = native.sim_game_over_native_calculate(
                ctypes.byref(state), ctypes.byref(result))
            model = {"status": model_status, "score": result.score,
                     "components": list(result.components),
                     "rank_score": result.rank_score,
                     "level_index": result.level_index,
                     "opening_sound_id": result.opening_sound_id}
            actual = {"score": oracle["score"],
                      "components": oracle["components"]}
            expected = {"score": model["score"],
                        "components": model["components"]}
            row = {"label": label, "equal": model_status == 0 and actual == expected,
                   "original_dos": actual, "portable": expected,
                   "plan": {"rank_score": model["rank_score"],
                            "level_index": model["level_index"],
                            "opening_sound_id": model["opening_sound_id"]}}
            comparisons.append(row)
            if not row["equal"]:
                model_mismatches.append(row)

        hashes_after = {path.relative_to(ROOT).as_posix(): digest(path)
                        for path in source_paths}
        if hashes_before != hashes_after:
            raise SystemExit("source inputs changed during DOS/model differential")
        report = {
            "schema": "calcscore-original-dos-portable-model-v1",
            "status": "PASS" if not source_control_mismatches and not model_mismatches else "FAIL",
            "scope": "Original 16-bit DOS CalcScore return and eight score-array values versus portable native model. This does not prove EndGameDialog modal behavior, text rendering, audio completion, or the subsequent NewGame(0)/MenuQuit flow.",
            "prepared_pair": pair.identity,
            "native_shared_library_sha256": native_hash,
            "native_adapter": ADAPTER.relative_to(ROOT).as_posix(),
            "native_adapter_sha256": hashes_before[ADAPTER.relative_to(ROOT).as_posix()],
            "source_pins": hashes_before,
            "source_pins_after": hashes_after,
            "case_count": len(rows),
            "compared_count": len(comparisons),
            "source_candidate_control_mismatch_count": len(source_control_mismatches),
            "portable_model_mismatch_count": len(model_mismatches),
            "cases": comparisons,
            "source_candidate_control_mismatches": source_control_mismatches,
            "portable_model_mismatches": model_mismatches,
            "notes": [
                "DOS globals were initialized at their named original addresses; CalcScore ran in the pinned 16-bit Machine.",
                "Same-module source-compiled CalcScore is an independent candidate control; all compared cases must pass it before model comparison.",
                "Rank bands are checked by pure source tests, not by executing modal EndGameDialog in DOS.",
                "SHARED kind-4 resources 1001 and 1900 were parsed by the companion unit test; live resource pointer tables are not model state.",
                "layout/symbols.json confirms o15_384C_03C6 aliases NewGame and o15_384C_01EE aliases MenuQuit. EndGameDialog calls NewGame(0) after the modal closes and calls MenuQuit only when NewGame returns negative; no high-score registration or name-entry behavior is claimed."
            ]
        }
        evidence_dir = ROOT / "portable/tests/dialogs/evidence"
        evidence_dir.mkdir(parents=True, exist_ok=True)
        evidence_path = evidence_dir / "calcscore-original-dos-portable-20261002-corrected.json"
        evidence_path.write_text(json.dumps(report, indent=2) + "\n",
                                 encoding="utf-8")
        print(f"CalcScore DOS/native model cases: {len(comparisons)}/{len(rows)}")
        print(f"source candidate controls: {len(source_control_mismatches)} mismatches")
        print(f"portable model: {len(model_mismatches)} mismatches")
        print(f"evidence: {evidence_path.relative_to(ROOT)}")
        # Windows keeps loaded DLL images locked until FreeLibrary is called;
        # release the temporary build before TemporaryDirectory cleanup.
        if os.name == "nt":
            free_library = ctypes.windll.kernel32.FreeLibrary
            free_library.argtypes = [ctypes.c_void_p]
            free_library.restype = ctypes.c_int
            free_library(ctypes.c_void_p(native._handle))
        del native
        if source_control_mismatches or model_mismatches:
            raise SystemExit(1)


if __name__ == "__main__":
    main()
