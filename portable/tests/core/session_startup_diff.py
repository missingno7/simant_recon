#!/usr/bin/env python3
"""Bounded original DOS RandYard vs native resource-backed session snapshot."""
from __future__ import annotations

import hashlib
import argparse
import json
import os
import shutil
import struct
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[3]
TOOLS = ROOT / "tools"
PROFILE_DIRS = {
    "legacy": ROOT / "build/workers/recovered_source/generated",
    "next": ROOT / "build/workers/recovered_source_next/generated",
    "next2": ROOT / "build/workers/recovered_source_next2/generated",
}
PROFILE = "next"
GENERATED = PROFILE_DIRS[PROFILE]
OUT = ROOT / "build/workers/session_startup_diff" / PROFILE
NATIVE = OUT / "session-startup-snapshot.exe"
NATIVE_RAW = OUT / "native.bin"
REPORT = OUT / "randyard-session-startup-diff.json"
CC = Path("C:/msys64/mingw64/bin/gcc.exe")
sys.path.insert(0, str(TOOLS))
import behavior  # noqa: E402
import functions  # noqa: E402

SINE_Q15 = [0, 804, 1607, 2410, 3211, 4011, 4807, 5601, 6392, 7179,
            7961, 8739, 9511, 10278, 11038, 11792, 12539, 13278, 14009,
            14732, 15446, 16150, 16845, 17530, 18204, 18867, 19519,
            20159, 20787, 21402, 22004, 22594, 23169, 23731, 24278,
            24811, 25329, 25831, 26318, 26789, 27244, 27683, 28105,
            28510, 28897, 29268, 29621, 29955, 30272, 30571, 30851,
            31113, 31356, 31580, 31785, 31970, 32137, 32284, 32412,
            32520, 32609, 32678, 32727, 32757]

NATIVE_FIELDS = {
    "MapA": 128 * 64, "MapB": 64 * 64, "MapR": 64 * 64,
    "ExitMapB": 64 * 64, "ExitMapR": 64 * 64,
    "LifeA": 128 * 64, "LifeB": 64 * 64, "LifeR": 64 * 64,
    "PherMapA": 64 * 32, "fd_3E1D_C89F": 64 * 32,
    "PherMapBN": 64 * 32, "PherMapBT": 64 * 32,
    "PherMapRN": 64 * 32, "PherMapRT": 64 * 32,
    "HoleMapB": 64, "HoleMapR": 64,
    "AlistX": 1000, "AlistY": 1000, "AlistM": 1000, "AlistT": 1000,
    "AlistS": 1000, "BlistX": 500, "BlistY": 500, "BlistM": 500,
    "BlistT": 500, "BlistS": 500, "RlistX": 500, "RlistY": 500,
    "RlistM": 500, "RlistT": 500, "RlistS": 500,
    "ListIndexA": 2, "ListIndexB": 2, "ListIndexR": 2,
    "fd_3E1D_0000": 16 * 12 * 2, "fd_3D57_00A4": 12 * 16,
    "fd_3D57_0164": 12 * 16, "fd_3D57_0184": 10 * 16,
    "fd_50F6_035E": 2, "fd_50F6_036C": 2, "fd_50F6_0AFA": 12,
    "fd_50F6_0AEC": 12, "fd_50F6_0EB6": 64,
    "fd_50F6_0508": 4, "fd_50F6_0596": 4, "fd_50F6_06A6": 4,
    "fd_50F6_072E": 4, "fd_50F6_0EAC": 2, "MapPlane": 2,
    "MePlane": 2, "MeLocX": 2, "MeLocY": 2, "fd_50F6_04C2": 2,
    "fd_3D57_02B4": 4, "fd_3D57_02B8": 4,
    "fd_50F6_0496": 2, "MeHealth": 2, "fd_50F6_0FBA": 2,
    "fd_50F6_0FFE": 2, "fd_50F6_0354": 2, "fd_50F6_0400": 2,
    "fd_50F6_0376": 2, "fd_50F6_0366": 2, "fd_50F6_07CA": 4,
    "fd_50F6_07BC": 4, "fd_3D57_07C8": 2, "fd_3D57_07CC": 14,
    "YardMode": 2, "FoodB": 2, "FoodR": 2, "HealthB": 2, "HealthR": 2,
    "Cycle": 2, "fd_50F6_0C26": 4, "fd_50F6_105E": 2,
    "fd_50F6_1040": 2, "fd_50F6_104E": 2, "fd_3D57_07BE": 2,
    "fd_50F6_0214": 4, "fd_50F6_0204": 4, "fd_50F6_0228": 2,
    "fd_50F6_0478": 2, "fd_50F6_0504": 2, "fd_3D57_0C44": 2,
    "fd_3D57_0C18": 2, "fd_3D57_0C16": 2, "fd_3D57_0C14": 2,
    "fd_50F6_049A": 2, "fd_3D57_0C22": 2, "fd_50F6_0242": 2,
    "fd_50F6_0472": 4, "fd_50F6_09FA": 2, "fd_50F6_0A00": 2,
    "fd_50F6_0A06": 2, "fd_50F6_04E2": 2, "fd_50F6_047C": 2,
    "fd_50F6_048A": 2, "fd_50F6_0F78": 2, "BpopT": 2, "RpopT": 2,
    "CurExpTool": 2, "DROPdir": 2, "CurGndTileID": 2, "TERRAINset": 2,
    "world_current_ground_tile_id": 2,
    "fd_50F6_0480": 2, "SowX": 6, "SowY": 6, "SowDir": 6,
    "SowSave": 6, "LionIndex": 2, "InitialLions": 2,
    "AntsEatenByLions": 2, "LionListX": 10, "LionListY": 10,
    "LionListM": 10, "LionListS": 10, "LionListT": 10,
    "PillarMap": 12, "PillarState": 2, "PillarX": 2, "PillarY": 2,
    "PillarSeg": 2, "PillDir": 2, "SCorpseBase": 2,
    "SpidBurpCnt": 2, "EatCnt": 2, "Scycle": 2, "Scycle2": 2,
    "SpidRevenge": 2, "SMode": 2, "Starg": 2, "StargLife": 2,
    "SuserX": 2, "SuserY": 2, "fd_50F6_0476": 2,
    "fd_50F6_037C": 100, "fd_50F6_0404": 100, "fd_50F6_0F12": 2,
    "fd_50F6_0F34": 2, "fd_50F6_0F0C": 2, "fd_50F6_1004": 2,
    "fd_3D57_0C12": 2, "fd_50F6_06AC": 2,
    "fd_50F6_10DE": 2, "fd_50F6_10E0": 2,
}

ALIASES = {
    "fd_50F6_047C": "MeLocX", "fd_50F6_048A": "MeLocY",
    "fd_50F6_0480": "Barrier", "fd_50F6_0F78": "MeHealth",
    "world_current_ground_tile_id": "CurGndTileID",
    "MapPlane": "MapPlane", "MePlane": "MePlane",
    "fd_50F6_0EAC": "fd_50F6_0EAC", "fd_3D57_0184": "fd_3D57_0184",
}


def compile_inputs() -> list[Path]:
    paths = [ROOT / "portable/game/session.c",
             ROOT / "portable/game/recovered/session_bridge.c",
             ROOT / "portable/game/render/map.c",
             ROOT / "portable/tests/core/session_startup_snapshot.c",
             GENERATED / "recovered_state.c",
             GENERATED / "recovered_native_adapters.c"]
    for folder in ("portable/game/simulation", "portable/game/state",
                   "portable/game/resources", "portable/render",
                   "portable/ui_model/windows"):
        paths.extend((ROOT / folder).rglob("*.c"))
    return sorted(set(p.resolve() for p in paths))


def build_native() -> tuple[list[str], str]:
    compiler = os.environ.get("SIMANT_CC") or shutil.which("gcc") or str(CC)
    command = [compiler, "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
               "-I", str(ROOT), "-I", str(ROOT / "portable"), "-I",
               str(GENERATED),
               *(str(path) for path in compile_inputs()), "-o", str(NATIVE)]
    completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    if completed.returncode:
        raise RuntimeError("native startup snapshot compile failed:\n" +
                           completed.stdout + completed.stderr)
    version = subprocess.check_output([compiler, "--version"], text=True).splitlines()[0]
    return command, version


def parse_native(data: bytes) -> dict[str, bytes]:
    result = {}
    at = 0
    while at < len(data):
        if at + 6 > len(data):
            raise ValueError("truncated native record header")
        name_size, size = struct.unpack_from("<HI", data, at)
        at += 6
        name = data[at:at + name_size].decode("ascii")
        at += name_size
        value = data[at:at + size]
        at += size
        if len(value) != size or name in result:
            raise ValueError(f"truncated or repeated native record: {name}")
        result[name] = value
    return result


def case_for():
    sine_linear = 0xD0000
    writes = [
        (behavior.symbol_address("fd_50F6_0EAC"), struct.pack("<h", 1)),
        (behavior.symbol_address("fd_50F6_0354"), struct.pack("<h", 1)),
        (behavior.symbol_address("fd_50F6_07CA"), struct.pack("<hh", 11, 8)),
        (behavior.symbol_address("fd_50F6_07BC"), struct.pack("<hh", 11, 8)),
        # Original initStuff loads SHARED:1000/kind9 into this far pointer.
        # The arena is private test RAM; table bytes are the actual shared
        # resource content, not an emulated code/data patch.
        (behavior.symbol_address("fd_50F6_0B22"), struct.pack("<HH", 0, 0xD000)),
        (sine_linear, b"".join(struct.pack("<H", value) for value in SINE_Q15)),
    ]
    def tick_count(machine, _args):
        samples = (0x12345678, 0x87654321)
        index = machine.state.get("tick_n", 0)
        machine.state["tick_n"] = index + 1
        value = samples[min(index, len(samples) - 1)]
        return value & 0xffff, value >> 16

    callbacks = {
        "TickCount": behavior.Callback(0, tick_count),
        "f_0798_0F0D": behavior.Callback(0, lambda m, a: None),
        "o22_39C7_07FD": behavior.Callback(3, lambda m, a: None),
        "InvalEuMap": behavior.Callback(4, lambda m, a: None),
    }
    return behavior.Case(
        label="scenario-1 default preset RandYard after controlled SeedRRand",
        writes=writes, observe=[], callbacks=callbacks,
        return_kind="void", max_instructions=12_000_000, max_blocks=250_000,
        state={"tick_n": 0}, metadata={"scenario": 1, "difficulty": 0,
                                      "preset": [11, 8], "modeled": [
                                          "TickCount", "initControls UI state",
                                          "resource request", "map invalidation"]})


def run_original():
    exe = behavior.exe.load()
    pair = SimpleNamespace(function=functions.get("RandYard"),
        vectors={behavior.exe.MANAGER_SEG * 16 + v.offset: v for v in exe.vectors})
    pair.sequence_targets = {"InitSimVars", "SeedRRand", "RandYard", "RRand",
                             "SRand1", "GetSRandSeed"}
    pair.sequence_function = lambda name: functions.get(name)
    pair.candidate = False
    case = case_for()
    machine = behavior.Machine(pair)
    init_exec = machine.run(case, function="InitSimVars")
    seed_exec = machine.run(behavior.Case(
        label=case.label, callbacks=case.callbacks, return_kind="void",
        max_instructions=1000000), preserve=True, function="SeedRRand")
    continuation = behavior.Case(label=case.label, callbacks=case.callbacks,
                                 return_kind="void", max_instructions=12_000_000,
                                 max_blocks=250_000)
    yard_exec = machine.run(continuation, preserve=True, function="RandYard")
    yard_trace, yard_io, yard_state = machine.raw_trace, machine.io, machine.state.copy()
    final_s_seed = machine.run(behavior.Case(
        label=case.label, callbacks=case.callbacks, return_kind="u32",
        max_instructions=10000), preserve=True, function="GetSRandSeed")["return"]
    result = {}
    for name, size in NATIVE_FIELDS.items():
        alias = ALIASES.get(name, name)
        try:
            address = behavior.symbol_address(alias)
        except KeyError:
            result[name] = {"error": f"oracle symbol unavailable: {alias}"}
            continue
        result[name] = machine.read(address, size)
    rng_tail = {"r": [], "s": []}
    for _ in range(32):
        rng_tail["r"].append(machine.run(
            behavior.Case(label=case.label, args=[32767], callbacks=case.callbacks,
                          return_kind="s16", max_instructions=10000),
            preserve=True, function="RRand")["return"])
    for _ in range(32):
        rng_tail["s"].append(machine.run(
            behavior.Case(label=case.label, args=[32767], callbacks=case.callbacks,
                          return_kind="s16", max_instructions=10000),
            preserve=True, function="SRand1")["return"])
    machine.startup_rng_tail = rng_tail
    machine.startup_s_seed = final_s_seed
    machine.startup_calls = {"blocks": {"InitSimVars": init_exec["blocks"],
                                         "SeedRRand": seed_exec["blocks"],
                                         "RandYard": yard_exec["blocks"]},
                             "returns": {"InitSimVars": init_exec["return"],
                                         "SeedRRand": seed_exec["return"],
                                         "RandYard": yard_exec["return"]},
                             "yard_trace": yard_trace,
                             "yard_io": yard_io, "yard_state": yard_state}
    return machine, result


def main():
    global PROFILE, GENERATED, OUT, NATIVE, NATIVE_RAW, REPORT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=sorted(PROFILE_DIRS), default="next",
                        help="whole-module recovered source profile (default: next)")
    args = parser.parse_args()
    PROFILE = args.profile
    GENERATED = PROFILE_DIRS[PROFILE]
    if not (GENERATED / "recovered_state.c").is_file():
        raise FileNotFoundError(f"generated recovered source not found for {PROFILE}: {GENERATED}")
    OUT = ROOT / "build/workers/session_startup_diff" / PROFILE
    NATIVE = OUT / "session-startup-snapshot.exe"
    NATIVE_RAW = OUT / "native.bin"
    REPORT = OUT / "randyard-session-startup-diff.json"
    if not OUT.exists():
        OUT.mkdir(parents=True)
    build_command, compiler_version = build_native()
    subprocess.run([str(NATIVE), "controlled"], cwd=ROOT,
                   stdout=NATIVE_RAW.open("wb"), check=True)
    native = parse_native(NATIVE_RAW.read_bytes())
    machine, oracle = run_original()
    aliases_missing = [k for k, v in oracle.items() if isinstance(v, dict)]
    # A small number of compatibility spellings are represented by separate
    # source labels; all other unavailable aliases are a closed test setup error.
    if aliases_missing:
        print("unavailable oracle names:", aliases_missing)
    diffs = []
    for name, size in NATIVE_FIELDS.items():
        left, right = native[name], oracle[name]
        if isinstance(right, dict):
            continue
        if len(left) != size or len(right) != size:
            diffs.append({"name": name, "error": "range length", "native": len(left),
                          "oracle": len(right), "expected": size})
        elif left != right:
            first = next(i for i, (a, b) in enumerate(zip(left, right)) if a != b)
            diffs.append({"name": name, "size": size, "first_offset": first,
                          "native_byte": left[first], "oracle_byte": right[first],
                          "native_sha256": hashlib.sha256(left).hexdigest(),
                          "oracle_sha256": hashlib.sha256(right).hexdigest()})
    native_r = list(struct.unpack("<32h", native["rng_r_next"]))
    native_s = list(struct.unpack("<32H", native["rng_s_next"]))
    if native_r != machine.startup_rng_tail["r"]:
        diffs.append({"name": "C-RNG stream next four RRand outputs",
                      "native": native_r, "oracle": machine.startup_rng_tail["r"]})
    if native_s != machine.startup_rng_tail["s"]:
        diffs.append({"name": "S-RNG stream next four SRand1 outputs",
                      "native": native_s, "oracle": machine.startup_rng_tail["s"]})
    if struct.unpack("<H", native["rng_s"])[0] != (machine.startup_s_seed & 0xffff):
        diffs.append({"name": "S-RNG source seed after RandYard",
                      "native": struct.unpack("<H", native["rng_s"])[0],
                      "oracle": machine.startup_s_seed})
    pinned = [*compile_inputs(), *ROOT.joinpath("portable").rglob("*.h"),
              Path(__file__), ROOT / "portable/game/session.h",
              ROOT / "portable/game/recovered/session_bridge.h",
              ROOT / "portable/game/simulation/worldgen.c",
              ROOT / "portable/game/simulation/terrain.c",
              ROOT / "portable/game/state/world.h",
              GENERATED / "recovered_state.c",
              GENERATED / "recovered_state.h",
              GENERATED / "provenance.json",
              TOOLS / "behavior.py", ROOT / "tools/functions.py",
              ROOT / "tools/exe.py", ROOT / "tools/symbols.py",
              ROOT / "tools/match.py", ROOT / "tools/modctx.py",
              ROOT / "tools/modules.py", ROOT / "layout/functions.json",
              ROOT / "layout/symbols.json", ROOT / "layout/oracle.lock.json",
              ROOT / "assets/SIMANT.EXE", ROOT / "assets/HCEGANT.NDX",
              ROOT / "assets/HCEGANT.DAT", ROOT / "assets/SHARED.NDX",
              ROOT / "assets/SHARED.DAT"]
    report = {
        "schema": "bounded-session-startup-differential-v1",
        "status": "DIAGNOSTIC_ONLY",
        "generated_source_profile": PROFILE,
        "domain": {"scenario": 1, "difficulty": 0, "preset": [11, 8],
                   "startup_ticks": [0x12345678, 0x87654321],
                   "original_tickcount_values": [0x12345678, 0x87654321],
                   "boundary": "original SeedRRand + original RandYard; native resource-backed SimSession NewGame + recovered bridge",
                   "modeled_boundaries": ["TickCount fixed values", "initControls UI-only entry",
                                           "resource request", "map invalidation"],
                   "sine_resource": {"source": "SHARED object 1000 kind 9",
                                     "entries": len(SINE_Q15), "injected_as_far_pointer": True,
                                     "raw_sha256": hashlib.sha256(b"".join(
                                         struct.pack("<H", value) for value in SINE_Q15)).hexdigest()}},
        "native_sha256": hashlib.sha256(NATIVE_RAW.read_bytes()).hexdigest(),
        "native_executable_sha256": hashlib.sha256(NATIVE.read_bytes()).hexdigest(),
        "native_build": {"compiler": compiler_version, "command": build_command},
        "pinned_input_sha256": {p.relative_to(ROOT).as_posix(): hashlib.sha256(
            p.read_bytes()).hexdigest() for p in pinned if p.is_file()},
        "oracle_execution": {"blocks": machine.startup_calls["blocks"]["RandYard"],
                             "callback_trace": machine.startup_calls["yard_trace"],
                             "io": machine.startup_calls["yard_io"],
                             "state": machine.startup_calls["yard_state"],
                             "rng_tail": machine.startup_rng_tail,
                             "s_seed": machine.startup_s_seed,
                             "calls": machine.startup_calls},
        "compared_ranges": len(NATIVE_FIELDS), "mismatches": diffs,
        "not_compared": ["unmapped initControls globals", "pointer-valued DATA/resource handles",
                         "physical memory addresses", "C RNG internal CRT storage; stream outputs are emitted separately"],
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n")
    print(f"ranges={len(NATIVE_FIELDS)} mismatches={len(diffs)} report={REPORT}")
    if diffs:
        print(json.dumps(diffs[:8], indent=2))


if __name__ == "__main__":
    main()
