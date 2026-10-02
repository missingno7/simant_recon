#!/usr/bin/env python3
"""Compare native MakeMap output and source state with original DOS calls."""
from __future__ import annotations

import ctypes as ct
import argparse
import hashlib
import json
from pathlib import Path
import random
import subprocess
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))
import behavior  # noqa: E402
import exe  # noqa: E402
import functions  # noqa: E402
import match  # noqa: E402

GCC = Path("C:/msys64/mingw64/bin/gcc.exe")
LIBRARY = ROOT / "build/portable/terrain-probe.dll"
REPORT = ROOT / "build/portable/terrain-dos-diff.json"
PROBE_BYTES = 8192 + 14 + 6 + 50 + 24 + 22 + 2


def address(name: str) -> int:
    symbol = behavior.symbol(name)
    return symbol["seg"] * 16 + symbol["off"]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_native(library_path: Path):
    library_path.parent.mkdir(parents=True, exist_ok=True)
    command = [str(GCC), "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror", "-shared",
               "-I", str(ROOT / "portable"),
               str(ROOT / "portable/game/simulation/terrain.c"),
               str(ROOT / "portable/game/simulation/rng.c"),
               str(ROOT / "portable/tests/terrain/native_probe.c"), "-o", str(library_path)]
    subprocess.run(command, cwd=ROOT, check=True)
    library = ct.CDLL(str(LIBRARY))
    library.sim_terrain_probe.argtypes = [ct.c_uint16, ct.c_int16, ct.c_int16,
                                          ct.c_int16, ct.POINTER(ct.c_uint8), ct.c_size_t]
    library.sim_terrain_probe.restype = ct.c_int
    return library, command


def probe_native(library, seed: int, terrain_set: int, x: int, y: int) -> bytes:
    output = (ct.c_uint8 * PROBE_BYTES)()
    status = library.sim_terrain_probe(seed, terrain_set, x, y, output, PROBE_BYTES)
    if status != 0:
        raise RuntimeError(f"native terrain probe rejected {(seed, terrain_set, x, y)}: {status}")
    return bytes(output)


def zero_state_writes(terrain_set: int):
    writes = [(address("MapA"), bytes(128 * 64)),
              (address("LifeA"), bytes(128 * 64)),
              (address("TERRAINset"), behavior.words(terrain_set)),
              (address("fd_50F6_0480"), behavior.words(0)),
              (match.DGROUP_SEG * 16 + 0x1A2E, behavior.words(0))]
    globals_to_zero = {
        "DROPdir": 2, "CurGndTileID": 2, "LionIndex": 2,
        "InitialLions": 2, "AntsEatenByLions": 2,
        "LionListX": 10, "LionListY": 10, "LionListM": 10,
        "LionListS": 10, "LionListT": 10,
        "SowX": 6, "SowY": 6, "SowDir": 6, "SowSave": 6,
        "PillarState": 2, "PillarX": 2, "PillarY": 2,
        "PillarSeg": 2, "PillDir": 2, "PillarMap": 12,
    }
    writes.extend((address(name), bytes(size)) for name, size in globals_to_zero.items())
    return writes


def observe_ranges():
    names = [("surface", "MapA", 128 * 64),
             ("ground", "CurGndTileID", 2), ("drop", "DROPdir", 2),
             ("terrain_set", "TERRAINset", 2),
             ("overlay_width", "fd_50F6_0480", 2),
             ("overlay_resource_set", "g_1A2E", 2),
             ("lion_count", "LionIndex", 2), ("initial_lions", "InitialLions", 2),
             ("eaten", "AntsEatenByLions", 2),
             ("lion_x", "LionListX", 10), ("lion_y", "LionListY", 10),
             ("lion_m", "LionListM", 10), ("lion_s", "LionListS", 10),
             ("lion_t", "LionListT", 10),
             ("sow_x", "SowX", 6), ("sow_y", "SowY", 6),
             ("sow_dir", "SowDir", 6), ("sow_save", "SowSave", 6),
             ("pillar_state", "PillarState", 2), ("pillar_x", "PillarX", 2),
             ("pillar_y", "PillarY", 2), ("pillar_seg", "PillarSeg", 2),
             ("pillar_dir", "PillDir", 2), ("pillar_map", "PillarMap", 12)]
    # The unregistered near static g_1A2E is DGROUP:1A2E, as shown by the
    # original f_0250_0256 compare/store operands at 0250:0266/026F.
    return [behavior.Range(name,
                           match.DGROUP_SEG * 16 + 0x1A2E if symbol == "g_1A2E" else address(symbol),
                           size) for name, symbol, size in names]


def oracle_bytes(result):
    ranges = result["ranges"]
    ground = bytes.fromhex(ranges["ground"])
    overlay_id = ground if int.from_bytes(ground, "little") in (0x3e8, 0x3e9) else bytes(2)
    head = b"".join(bytes.fromhex(ranges[name]) for name in
                    ("surface", "ground", "drop", "terrain_set"))
    head += bytes(2) + overlay_id + bytes.fromhex(ranges["overlay_resource_set"])
    head += bytes.fromhex(ranges["overlay_width"])
    lion_arrays = [bytes.fromhex(ranges[name]) for name in
                   ("lion_x", "lion_y", "lion_m", "lion_s", "lion_t")]
    lions = b"".join(bytes(values[index] for values in lion_arrays) for index in range(10))
    tail = b"".join(bytes.fromhex(ranges[name]) for name in
                    ("lion_count", "initial_lions", "eaten"))
    tail += lions
    tail += b"".join(bytes.fromhex(ranges[name]) for name in
                     ("sow_x", "sow_y", "sow_dir", "sow_save",
                      "pillar_state", "pillar_x", "pillar_y", "pillar_seg", "pillar_dir",
                      "pillar_map"))
    return head + tail


def overlay_tileset(machine, args):
    tile_type, tile_id = args
    if tile_type != 0 or tile_id not in (0x3e8, 0x3e9):
        raise behavior.ExecutionError(f"unexpected OverlayTileSet request {(tile_type, tile_id)}")
    resource_set = 1 if tile_id == 0x3e9 else 0
    width = 0x90 if resource_set else 0x50
    # This is the documented logical resource boundary: actual acquisition is
    # kind 9; the original helper selects the resource set, terrain selector,
    # and bitmap width before handing pages to the video/EMS transfer layer.
    machine.write(match.DGROUP_SEG * 16 + 0x1A2E, behavior.words(resource_set))
    machine.write(address("TERRAINset"), behavior.words(resource_set))
    machine.write(address("fd_50F6_0480"), behavior.words(width))
    machine.state.setdefault("overlay_resource_intents", []).append(
        {"object": 10 - resource_set, "kind": 9, "resource_set": resource_set,
         "ground_tile_id": tile_id, "bitmap_width": width})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, default=REPORT)
    parser.add_argument("--library", type=Path, default=LIBRARY)
    args = parser.parse_args()
    library, command = build_native(args.library)
    target = functions.get("MakeMap")
    image = exe.load()
    pair = SimpleNamespace(function=target,
                           vectors={exe.MANAGER_SEG * 16 + vector.offset: vector
                                    for vector in image.vectors})
    pair.sequence_function = lambda name: functions.get(name)
    machine = behavior.Machine(pair)
    cases = [(seed, terrain_set, n >> 4, n & 15)
             for seed in (0x1234, 0xACE1)
             for terrain_set in (0, 1)
             for n in range(38)]
    cases += [(seed, terrain_set, x, y)
              for seed in (1, 0x1234, 0xACE1, 0xffff)
              for terrain_set in (0, 1, 2)
              for x, y in ((2, 6), (11, 8))]
    edge_seeds = {0, 1, 0x7fff, 0x8000, 0xffff}
    already_covered = {1, 0x1234, 0xACE1, 0xffff}
    randomizer = random.Random(0x18384c)
    random_seeds = set()
    while len(random_seeds) < 256:
        candidate = randomizer.randrange(0x10000)
        if candidate not in edge_seeds and candidate not in already_covered:
            random_seeds.add(candidate)
    yard_seeds = (edge_seeds | random_seeds) - already_covered
    cases += [(seed, terrain_set, 11, 8)
              for seed in sorted(yard_seeds)
              for terrain_set in (0, 1, 2)]
    failures = []
    oracle_execution_failures = []
    executed_count = 0
    for seed, terrain_set, x, y in cases:
        setup = behavior.Case(f"setup/{seed:04x}/{terrain_set}/{x}/{y}",
                              args=[seed], writes=zero_state_writes(terrain_set), return_kind="void")
        machine.run(setup, function="SetSRandSeed")
        call = behavior.Case(f"map/{seed:04x}/{terrain_set}/{x}/{y}",
                             args=[x, y], observe=observe_ranges(), return_kind="void",
                             callbacks={"OverlayTileSet": behavior.Callback(2, overlay_tileset)},
                             metadata={"case_class": "MakeMap original-DOS direct call",
                                       "overlay_boundary": "logical OverlayTileSet kind-9 resource intent; video/EMS pages excluded"})
        try:
            oracle = machine.run(call, preserve=True)
        except behavior.ExecutionError as error:
            executed_count += 1
            oracle_execution_failures.append({"case": call.label, "seed": seed,
                                              "terrain_set": terrain_set, "x": x, "y": y,
                                              "error": str(error),
                                              "classification": "original DOS did not complete; no native comparison"})
            continue
        seed_after = machine.run(behavior.Case(call.label + "/seed", return_kind="u32"),
                                 preserve=True, function="GetSRandSeed")
        expected = oracle_bytes(oracle) + (int(seed_after["return"]) & 0xffff).to_bytes(2, "little")
        actual = probe_native(library, seed, terrain_set, x, y)
        executed_count += 1
        if expected != actual:
            mismatch = next((index for index, (a, b) in enumerate(zip(expected, actual)) if a != b),
                            min(len(expected), len(actual)))
            failures.append({"case": call.label, "seed": seed, "terrain_set": terrain_set,
                             "x": x, "y": y, "first_mismatch_offset": mismatch,
                             "expected_length": len(expected), "actual_length": len(actual),
                             "expected_byte": expected[mismatch] if mismatch < len(expected) else None,
                             "actual_byte": actual[mismatch] if mismatch < len(actual) else None,
                             "expected_sha256": hashlib.sha256(expected).hexdigest(),
                             "actual_sha256": hashlib.sha256(actual).hexdigest(),
                             "expected_hex": expected.hex(), "actual_hex": actual.hex()})
    native_paths = [
        "portable/game/simulation/terrain.c", "portable/game/simulation/terrain.h",
        "portable/game/simulation/rng.c", "portable/game/simulation/rng.h",
        "portable/game/state/world.h", "portable/game/simulation/movement.h",
        "portable/tests/terrain/native_probe.c", "portable/tests/terrain/test_terrain.c",
    ]
    oracle_inputs = ["assets/SIMANT.EXE", "assets/HCEGANT.NDX", "assets/HCEGANT.DAT",
                     "assets/SHARED.NDX", "assets/SHARED.DAT", "layout/manifest.json",
                     "layout/functions.json", "layout/symbols.json", "layout/oracle.lock.json",
                     "tools/behavior.py", "tools/exe.py", "tools/functions.py", "tools/match.py",
                     "tools/modules.py", "tools/modctx.py", "tools/symbols.py"]
    report = {"schema": "portable-terrain-dos-diff-v1", "oracle_execution": "original DOS only",
              "runner_sha256": digest(Path(__file__)),
              "oracle_exe_sha256": digest(exe.EXE_PATH),
              "harness_sha256": {name: digest(ROOT / "tools" / f"{name}.py")
                                  for name in ("behavior", "exe", "functions", "match")},
              "native_source_hashes": {path: digest(ROOT / path) for path in native_paths},
              "oracle_input_hashes": {path: digest(ROOT / path) for path in oracle_inputs},
              "compiler_sha256": digest(GCC), "native_library_path": str(args.library),
              "native_source_sha256": {"terrain.c": digest(ROOT / "portable/game/simulation/terrain.c"),
                                       "terrain.h": digest(ROOT / "portable/game/simulation/terrain.h"),
                                       "rng.c": digest(ROOT / "portable/game/simulation/rng.c"),
                                       "native_probe.c": digest(ROOT / "portable/tests/terrain/native_probe.c"),
                                       "test_terrain.c": digest(ROOT / "portable/tests/terrain/test_terrain.c")},
              "native_library_sha256": digest(args.library), "native_command": command,
              "case_count": len(cases), "executed_count": executed_count,
              "compared_count": executed_count - len(oracle_execution_failures),
              "passed": executed_count - len(failures) - len(oracle_execution_failures),
              "case_inputs": [{"seed": seed, "terrain_set": terrain_set, "x": x, "y": y}
                              for seed, terrain_set, x, y in cases],
              "coverage": {"all_map_slots": "n=0..37 for two seeds and initial TERRAINset 0/1",
                           "high_level_yard": "(11,8), x=11,y=8 across edge and 256 deterministic random seeds; initial TERRAINset 0/1/2",
                           "edge_seeds": [0, 1, 0x7fff, 0x8000, 0xffff],
                           "random_seed_algorithm": "Python random.Random(0x18384c), unique uint16 values excluding previously covered seeds"},
              "initial_state": {"MapA": "all zero", "LifeA": "all zero",
                                "TERRAINset": "case input", "g_1A2E": 0,
                                "fd_50F6_0480": 0, "lion/sow/pillar state": "all zero"},
              "failures": failures,
              "oracle_execution_failures": oracle_execution_failures,
              "overlay_boundary": {"entry": "OverlayTileSet", "resource_kind": 9,
                                   "modeled_effects": ["resource object 10 or 9", "g_1A2E selected set",
                                                       "TERRAINset selected set", "fd_50F6_0480 bitmap width"],
                                   "excluded": "physical EGA/EMS page copies and allocator-owned resource heap"},
              "limitations": ["The compared boundary is surface tiles, drop direction, ant-lion/sow/pillar state, overlay selection globals, and source S-RNG state."]}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(args.report), "executed": executed_count,
                      "compared": report["compared_count"], "passed": report["passed"],
                      "mismatches": len(failures)}, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
