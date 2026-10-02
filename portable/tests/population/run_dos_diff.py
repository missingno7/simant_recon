#!/usr/bin/env python3
"""Compare native population accounting/effects with original DOS CountAnts."""
from __future__ import annotations

import ctypes as ct
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))
import behavior  # noqa: E402

GCC = Path("C:/msys64/mingw64/bin/gcc.exe")
OUTPUT = ROOT / "build/portable/population-probe.dll"
REPORT = ROOT / "build/portable/population-dos-diff.json"
EVIDENCE = ROOT / "portable/tests/population/evidence"
POPULATION_C = ROOT / "portable/game/simulation/population.c"
POPULATION_H = ROOT / "portable/game/simulation/population.h"
PROBE_C = ROOT / "portable/tests/population/probe.c"
RUNNER = Path(__file__)


class SimPopulationInput(ct.Structure):
    _fields_ = [
        ("ants_a", ct.c_uint8 * 1000), ("ants_b", ct.c_uint8 * 500),
        ("ants_r", ct.c_uint8 * 500),
        ("count_a", ct.c_int16), ("count_b", ct.c_int16), ("count_r", ct.c_int16),
        ("player_mode", ct.c_int16), ("player_caste_type", ct.c_int16),
        ("player_death_plane", ct.c_int16), ("scenario", ct.c_int16),
        ("new_game", ct.c_int16), ("graph_enabled", ct.c_int16),
        ("graph_preset", ct.c_int16 * 2), ("selection_pending", ct.c_int16),
        ("selection_colony", ct.c_int16), ("previous_black_queen", ct.c_int16),
        ("previous_red_queen", ct.c_int16), ("lifetime_graph", ct.c_uint8 * 160),
        ("rng_seed", ct.c_uint16), ("effect_count", ct.c_uint16),
    ]


class PopulationEffect(ct.Structure):
    _fields_ = [("kind", ct.c_uint16), ("values", ct.c_int16 * 3)]


class PopulationEffects(ct.Structure):
    _fields_ = [("count", ct.c_uint16), ("overflow", ct.c_uint8),
                ("events", PopulationEffect * 8)]


class SimPopulationOutput(ct.Structure):
    _fields_ = [
        ("status", ct.c_int16), ("ants_by_type", ct.c_int16 * 32),
        ("population_black", ct.c_int16 * 6), ("population_red", ct.c_int16 * 6),
        ("total_black", ct.c_int16), ("total_red", ct.c_int16),
        ("new_game", ct.c_int16), ("selection_pending", ct.c_int16),
        ("selection_colony", ct.c_int16), ("lifetime_graph", ct.c_uint8 * 160),
        ("rng_seed", ct.c_uint16), ("effects", PopulationEffects),
    ]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_native():
    command = [str(GCC), "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror", "-shared",
               "-I", str(ROOT / "portable"), str(POPULATION_C),
               str(ROOT / "portable/game/simulation/rng.c"), str(PROBE_C), "-o", str(OUTPUT)]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(command, check=True, cwd=ROOT)
    lib = ct.CDLL(str(OUTPUT))
    lib.sim_population_probe.argtypes = [ct.POINTER(SimPopulationInput),
                                         ct.POINTER(SimPopulationOutput)]
    lib.sim_population_probe.restype = None
    return lib, command


def raw_global(name: str, size=2):
    address = behavior.symbol_address(name)
    return behavior.Range(name, address, size)


def short(value: int) -> bytes:
    return behavior.words(value)


def manifest_seed_address():
    manifest = json.loads((ROOT / "layout/manifest.json").read_text())
    placement = manifest["modules"]["root:0093"]["placements"]["_BSS"]
    if placement["size"] != 2:
        raise RuntimeError("expected private SRand seed to be the only 2-byte _BSS item")
    return placement["seg"] * 16 + placement["off"], placement


def callback_specs():
    # Audio/UI services are captured as ordered host requests. The actual
    # CountAnts and SRand1 original functions continue executing in DOS.
    return {
        "myBeginSong": behavior.Callback(2, handler=lambda _m, _a: None),
        "o14_384C_0B6A": behavior.Callback(3, handler=lambda _m, _a: None),
    }


def cases():
    all_bins = [1 if b == 0 else (b << 3) | 1 for b in range(32)]
    yield "all-bins-player-normal-newgame", {
        "a": all_bins[:11], "b": all_bins[11:22], "r": all_bins[22:],
        "player_mode": 0, "player_caste_type": 0x40, "player_death_plane": 0,
        "scenario": 0, "new_game": 1, "previous_black_queen": 1,
        "previous_red_queen": 1,
    }
    yield "player-death-plane-and-mode-gate", {
        "a": [], "b": [], "r": [], "player_mode": 0,
        "player_caste_type": 0x40, "player_death_plane": 1, "scenario": 1,
        "new_game": 1,
    }
    yield "both-queen-loss-tutorial-order", {
        "a": [], "b": [], "r": [], "player_mode": 1,
        "player_caste_type": 0x10, "scenario": 0, "new_game": 0,
        "previous_black_queen": 2, "previous_red_queen": 3,
        "selection_pending": 4, "selection_colony": 7,
    }
    yield "red-queen-loss-scenario-two-graph", {
        "a": [], "b": [0x61], "r": [], "player_mode": 1,
        "player_caste_type": 0x10, "scenario": 2, "new_game": 0,
        "previous_black_queen": 1, "previous_red_queen": 1,
        "graph_enabled": 1, "graph_preset": [11, 8], "rng_seed": 0x8001,
    }
    yield "red-queen-loss-without-graph-gates", {
        "a": [], "b": [0x61], "r": [], "player_mode": 1,
        "player_caste_type": 0x10, "scenario": 2, "new_game": 0,
        "previous_black_queen": 1, "previous_red_queen": 1,
        "graph_enabled": 0, "graph_preset": [11, 8], "rng_seed": 0x8001,
    }
    yield "red-queen-loss-scenario-one", {
        "a": [], "b": [0x61], "r": [], "player_mode": 1,
        "player_caste_type": 0x10, "scenario": 1, "new_game": 0,
        "previous_black_queen": 1, "previous_red_queen": 1,
    }
    yield "black-loss-no-previous-queen", {
        "a": [], "b": [], "r": [0xe1], "player_mode": 1,
        "player_caste_type": 0x10, "scenario": 0, "new_game": 0,
        "previous_black_queen": 0, "previous_red_queen": 1,
    }


def make_native_input(values):
    inp = SimPopulationInput()
    for key, data in (("ants_a", values["a"]), ("ants_b", values["b"]),
                      ("ants_r", values["r"])):
        getattr(inp, key)[:len(data)] = data
    inp.count_a, inp.count_b, inp.count_r = len(values["a"]), len(values["b"]), len(values["r"])
    for key in ("player_mode", "player_caste_type", "player_death_plane", "scenario",
                "new_game", "graph_enabled", "selection_pending", "selection_colony",
                "previous_black_queen", "previous_red_queen", "rng_seed"):
        setattr(inp, key, values.get(key, 0))
    inp.graph_preset[:] = values.get("graph_preset", (0, 0))
    for i in range(160):
        inp.lifetime_graph[i] = (0x40 + i) & 0xff
    return inp


def make_dos_case(label, values, seed_address):
    writes = []
    observe = []
    list_specs = (("a", "ListIndexA", "AlistT"),
                  ("b", "ListIndexB", "BlistT"),
                  ("r", "ListIndexR", "RlistT"))
    for key, count_name, types_name in list_specs:
        types = values[key]
        writes.append((behavior.symbol_address(count_name), short(len(types))))
        if types:
            writes.append((behavior.symbol_address(types_name), bytes(types)))
    initial_bins = bytes([0x55] * 64)
    writes.append((behavior.symbol_address("fd_50F6_0EB6"), initial_bins))
    observe.append(raw_global("fd_50F6_0EB6", 64))
    black_old = [0x100 + i for i in range(6)]
    red_old = [0x200 + i for i in range(6)]
    black_old[5] = values.get("previous_black_queen", 0)
    red_old[5] = values.get("previous_red_queen", 0)
    writes.append((behavior.symbol_address("fd_50F6_0AEC"), behavior.words(*black_old)))
    writes.append((behavior.symbol_address("fd_50F6_0AFA"), behavior.words(*red_old)))
    observe.extend((raw_global("fd_50F6_0AEC", 12), raw_global("fd_50F6_0AFA", 12)))
    for name, value in (("BpopT", 0x1234), ("RpopT", 0x2345)):
        writes.append((behavior.symbol_address(name), short(value)))
        observe.append(raw_global(name, 2))
    scalar_values = {
        "fd_50F6_0A06": values.get("player_mode", 0),
        "fd_50F6_04C2": values.get("player_caste_type", 0),
        "fd_50F6_04E2": values.get("player_death_plane", 0),
        "fd_50F6_0EAC": values.get("scenario", 0),
        "fd_50F6_0354": values.get("new_game", 0),
        "fd_50F6_0400": values.get("graph_enabled", 0),
        "fd_50F6_0376": values.get("selection_pending", 0),
        "fd_50F6_0366": values.get("selection_colony", 0),
    }
    for name, value in scalar_values.items():
        writes.append((behavior.symbol_address(name), short(value)))
        observe.append(raw_global(name, 2))
    preset = values.get("graph_preset", (0, 0))
    writes.append((behavior.symbol_address("fd_50F6_07CA"), behavior.words(*preset)))
    observe.append(raw_global("fd_50F6_07CA", 4))
    graph_initial = bytes((0x40 + i) & 0xff for i in range(160))
    writes.append((behavior.symbol_address("fd_3D57_0184"), graph_initial))
    observe.append(raw_global("fd_3D57_0184", 160))
    seed = values.get("rng_seed", 0)
    writes.append((seed_address, short(seed)))
    observe.append(behavior.Range("private_srand_seed", seed_address, 2))
    return behavior.Case(label, writes=writes, observe=observe, callbacks=callback_specs(),
                         return_kind="void", metadata={"input": values})


def normalize_events(trace):
    events = []
    for item in trace:
        if item["name"] == "myBeginSong":
            events.append((1, tuple(item["args"][:2]) + (0,)))
        elif item["name"] == "o14_384C_0B6A":
            events.append((2, tuple(item["args"][:3])))
    return events


def native_events(out):
    return [(int(out.effects.events[i].kind),
             tuple(int(v) for v in out.effects.events[i].values))
            for i in range(out.effects.count)]


def compare_case(lib, pair, seed_address, label, values):
    dos = pair.original_machine.run(make_dos_case(label, values, seed_address))
    inp = make_native_input(values)
    native = SimPopulationOutput()
    lib.sim_population_probe(ct.byref(inp), ct.byref(native))
    ranges = dos["ranges"]
    actual = {
        "ants_by_type": bytes.fromhex(ranges["fd_50F6_0EB6"]),
        "population_black": bytes.fromhex(ranges["fd_50F6_0AEC"]),
        "population_red": bytes.fromhex(ranges["fd_50F6_0AFA"]),
        "total_black": bytes.fromhex(ranges["BpopT"]),
        "total_red": bytes.fromhex(ranges["RpopT"]),
        "new_game": bytes.fromhex(ranges["fd_50F6_0354"]),
        "selection_pending": bytes.fromhex(ranges["fd_50F6_0376"]),
        "selection_colony": bytes.fromhex(ranges["fd_50F6_0366"]),
        "lifetime_graph": bytes.fromhex(ranges["fd_3D57_0184"]),
        "rng_seed": bytes.fromhex(ranges["private_srand_seed"]),
        "events": normalize_events(dos["trace"]),
    }
    expected = {
        "ants_by_type": bytes(native.ants_by_type),
        "population_black": bytes(native.population_black),
        "population_red": bytes(native.population_red),
        "total_black": short(native.total_black),
        "total_red": short(native.total_red),
        "new_game": short(native.new_game),
        "selection_pending": short(native.selection_pending),
        "selection_colony": short(native.selection_colony),
        "lifetime_graph": bytes(native.lifetime_graph),
        "rng_seed": short(native.rng_seed),
        "events": native_events(native),
    }
    mismatches = []
    for key in expected:
        if expected[key] != actual[key]:
            if isinstance(expected[key], bytes):
                expect = expected[key].hex()
                got = actual[key].hex()
            else:
                expect, got = expected[key], actual[key]
            mismatches.append({"field": key, "native": expect, "dos": got})
    return {"case": label, "mismatches": mismatches, "events": actual["events"],
            "native_events": expected["events"],
            "expected_effect_count": native.effects.count,
            "oracle_callback_count": len(normalize_events(dos["trace"]))}


def main():
    lib, command = build_native()
    pair = behavior.PreparedPair("CountAnts", source=ROOT / "src/root/m0BE8.c")
    seed_address, seed_placement = manifest_seed_address()
    rows = [compare_case(lib, pair, seed_address, label, values)
            for label, values in cases()]
    report = {
        "schema": "portable-population-dos-diff-v1",
        "target": "CountAnts",
        "identity": pair.identity,
        "oracle_sha256": behavior.exe.load().sha256,
        "seed_storage": {"module": "root:0093", "placement": seed_placement,
                         "meaning": "the module's sole 2-byte _BSS item, static SRand1 seed"},
        "callbacks": "CountAnts and SRand1 execute as original DOS code; only myBeginSong and o14_384C_0B6A are explicit captured host-boundary callbacks.",
        "callback_limits": "Captured callback arguments/order are compared; sound playback and modal report presentation are not executed.",
        "native_build_command": command,
        "native_compiler": subprocess.check_output([str(GCC), "--version"],
                                                    text=True).splitlines()[0],
        "pinned_sources": {str(p.relative_to(ROOT)): digest(p) for p in
                           (POPULATION_C, POPULATION_H, PROBE_C, RUNNER,
                            ROOT / "portable/game/simulation/rng.c",
                            ROOT / "portable/game/state/world.h",
                            ROOT / "src/root/m0BE8.c", ROOT / "src/root/m0093.c",
                            ROOT / "layout/manifest.json")},
        "cases": rows,
        "case_count": len(rows),
        "mismatch_count": sum(len(row["mismatches"]) for row in rows),
        "status": "PASS" if all(not row["mismatches"] for row in rows) else "FAIL",
        "coverage": "32 raw caste bins across lists and player state; new-game flag 0354 suppressing prior-queen loss; black/red ordered queen-loss music/report/selection callbacks; scenario-two graph gates, real SRand1 seed mutation, and lifetime graph cell write.",
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    (EVIDENCE / "countants-dos-diff.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(REPORT), "cases": report["case_count"],
                      "mismatches": report["mismatch_count"], "status": report["status"]}, indent=2))
    if report["mismatch_count"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
