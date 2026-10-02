#!/usr/bin/env python3
"""Differentially execute original DOS FeedAnts/AddFood and native port."""
from __future__ import annotations

import ctypes as ct
import hashlib
import json
from pathlib import Path
import random
import struct
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
LIBRARY = ROOT / "build/portable/feeding-probe.dll"
REPORT = ROOT / "build/portable/feeding-dos-diff.json"
SURFACE = 128 * 64
HEADER = 22
SINE = [0,804,1607,2410,3211,4011,4807,5601,6392,7179,7961,8739,9511,10278,
        11038,11792,12539,13278,14009,14732,15446,16150,16845,17530,18204,
        18867,19519,20159,20787,21402,22004,22594,23169,23731,24278,24811,
        25329,25831,26318,26789,27244,27683,28105,28510,28897,29268,29621,
        29955,30272,30571,30851,31113,31356,31580,31785,31970,32137,32284,
        32412,32520,32609,32678,32727,32757]
SINE_BYTES = struct.pack("<64h", *SINE)
DG = match.DGROUP_SEG


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def address(name: str) -> int:
    item = behavior.symbol(name)
    return item["seg"] * 16 + item["off"]


def u16(value: int) -> bytes:
    return struct.pack("<H", value & 0xffff)


def build_native():
    command = [str(GCC), "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
               "-shared", "-I", str(ROOT / "portable"),
               str(ROOT / "portable/game/simulation/feeding.c"),
               str(ROOT / "portable/game/simulation/rng.c"),
               str(ROOT / "portable/tests/feeding/native_probe.c"),
               "-o", str(LIBRARY)]
    LIBRARY.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(command, cwd=ROOT, check=True)
    library = ct.CDLL(str(LIBRARY))
    library.sim_feeding_probe.argtypes = [ct.POINTER(ct.c_uint8), ct.c_size_t,
                                          ct.POINTER(ct.c_uint8), ct.c_size_t]
    library.sim_feeding_probe.restype = ct.c_int
    return library, command


def make_cases():
    rng = random.Random(0xFEE_DA)
    cases = []
    for terrain in range(3):
        for i in range(20):
            cases.append({"label": f"add/{terrain}/{i}", "op": 0,
                          "count": 150, "sound": 1, "terrain": terrain,
                          "scenario": rng.randrange(4), "health_b": rng.randrange(40),
                          "health_r": rng.randrange(40), "source_0c18": rng.randrange(2),
                          "threshold": rng.randrange(1, 51),
                          "food_added": rng.randrange(40), "seed": rng.randrange(1, 65536),
                          "fixture_seed": rng.randrange(0x100000000)})
    for i in range(18):
        cases.append({"label": f"add-negative/{i}", "op": 0, "count": -1,
                      "sound": i % 2, "terrain": i % 3, "scenario": 0,
                      "health_b": 0, "health_r": 0, "source_0c18": 0,
                      "threshold": 1, "food_added": 0,
                      "seed": rng.randrange(1, 65536),
                      "fixture_seed": rng.randrange(0x100000000)})
    for i in range(48):
        if i % 4 == 0:
            scenario, threshold, food_added = 3, 1, 0
        elif i % 4 == 1:
            scenario, threshold, food_added = 0, 20, 20
        else:
            scenario, threshold, food_added = 0, rng.randrange(2, 51), 0
        cases.append({"label": f"feed/{i}", "op": 1, "count": 150,
                      "sound": 0, "terrain": i % 3, "scenario": scenario,
                      "health_b": rng.randrange(0, 5), "health_r": rng.randrange(0, 5),
                      "source_0c18": i % 2, "threshold": threshold,
                      "food_added": food_added, "seed": rng.randrange(1, 65536),
                      "fixture_seed": rng.randrange(0x100000000)})
    return cases


def make_fixture(case):
    rng = random.Random(case["fixture_seed"])
    tiles = [0x01, 0x03, 0x04, 0x0d, 0x17, 0x18, 0x1b, 0x24, 0x27,
             0x48, 0x49, 0x4a, 0x4b, 0x50]
    surface = bytes(rng.choice(tiles) for _ in range(SURFACE))
    life = bytes(rng.choices([0, 0, 0, 0, 0x20], k=SURFACE))
    header = b"".join(u16(case[name]) for name in
                      ("op", "count", "sound", "terrain", "scenario", "health_b",
                       "health_r", "source_0c18", "threshold", "food_added", "seed"))
    return header + surface + life + SINE_BYTES, surface, life


def callback_sound(machine, args):
    machine.state["host_intents"].append([1, *args])


def original_writes(case, surface, life):
    writes = [(address("MapA"), surface), (address("LifeA"), life),
              (address("TERRAINset"), u16(case["terrain"])),
              (address("fd_50F6_0EAC"), u16(case["scenario"])),
              (address("HealthB"), u16(case["health_b"])),
              (address("HealthR"), u16(case["health_r"])),
              (address("fd_3D57_0C18"), u16(case["source_0c18"])),
              (address("fd_3D57_0C1A"), u16(case["threshold"])),
              (address("fd_50F6_1040"), u16(case["food_added"])),
              (DG * 16 + 0x8BA2, u16(case["seed"])),
              (address("fd_50F6_0B22"), struct.pack("<HH", 0, 0xD000)),
              (0xD0000, SINE_BYTES)]
    return writes


def ranges_to_bytes(ranges):
    return b"".join(bytes.fromhex(ranges[name]) for name in
                    ("surface", "health_b", "health_r", "threshold", "food_added",
                     "center", "s_rng"))


def make_ranges():
    return [behavior.Range("surface", address("MapA"), SURFACE),
            behavior.Range("health_b", address("HealthB"), 2),
            behavior.Range("health_r", address("HealthR"), 2),
            behavior.Range("threshold", address("fd_3D57_0C1A"), 2),
            behavior.Range("food_added", address("fd_50F6_1040"), 2),
            behavior.Range("center", address("fd_3D57_02BC"), 4),
            behavior.Range("s_rng", DG * 16 + 0x8BA2, 2)]


def native_call(library, payload):
    inp = (ct.c_uint8 * len(payload)).from_buffer_copy(payload)
    out = (ct.c_uint8 * 20000)()
    length = library.sim_feeding_probe(inp, len(payload), out, len(out))
    if length < 0:
        raise RuntimeError(f"native fixture rejected with status {length}")
    data = bytes(out[:length])
    status = data[0]
    count = struct.unpack_from("<H", data, 1)[0]
    cursor = 3
    events = []
    for _ in range(count):
        values = struct.unpack_from("<4H", data, cursor)
        events.append([values[0], *[v if v < 0x8000 else v - 0x10000 for v in values[1:]]])
        cursor += 8
    state = data[cursor:]
    return status, events, state


def main():
    library, command = build_native()
    image = exe.load()
    vectors = {exe.MANAGER_SEG * 16 + vector.offset: vector
               for vector in image.vectors}
    machines = {}
    ranges = make_ranges()
    cases = make_cases()
    failures = []
    executed = 0
    coverage = {"FeedAnts": 0, "AddFood": 0, "sound_intents": 0}
    for case in cases:
        payload, surface, life = make_fixture(case)
        native_status, native_events, native_state = native_call(library, payload)
        function = "FeedAnts" if case["op"] == 1 else "AddFood"
        if function not in machines:
            pair = SimpleNamespace(function=functions.get(function), vectors=vectors)
            pair.sequence_function = lambda name: functions.get(name)
            machines[function] = behavior.Machine(pair)
        machine = machines[function]
        args = [] if case["op"] == 1 else [case["count"], case["sound"]]
        callback = {"myBeginSound": behavior.Callback(3, callback_sound)}
        result = machine.run(behavior.Case(case["label"], args=args,
                                           writes=original_writes(case, surface, life),
                                           observe=ranges, callbacks=callback,
                                           return_kind="void",
                                           state={"host_intents": []}),
                             function=function)
        original_events = machine.state["host_intents"][:]
        original_state = ranges_to_bytes(result["ranges"])
        coverage[function] += 1
        coverage["sound_intents"] += len(original_events)
        if native_status != 0 or native_events != original_events or native_state != original_state:
            mismatch = next((i for i, (a, b) in enumerate(zip(native_state, original_state))
                             if a != b), min(len(native_state), len(original_state)))
            failures.append({"case": case["label"], "native_status": native_status,
                             "native_events": native_events, "original_events": original_events,
                             "native_length": len(native_state),
                             "original_length": len(original_state),
                             "first_state_mismatch": mismatch,
                             "native_state_sha256": hashlib.sha256(native_state).hexdigest(),
                             "original_state_sha256": hashlib.sha256(original_state).hexdigest()})
        executed += 1

    report = {"schema": "portable-feeding-dos-diff-v1",
              "oracle_execution": "original DOS only",
              "runner_sha256": digest(Path(__file__)),
              "oracle_exe_sha256": digest(exe.EXE_PATH),
              "harness_sha256": {name: digest(ROOT / "tools" / f"{name}.py")
                                  for name in ("behavior", "exe", "functions", "match")},
              "native_source_sha256": {
                  "feeding.c": digest(ROOT / "portable/game/simulation/feeding.c"),
                  "feeding.h": digest(ROOT / "portable/game/simulation/feeding.h"),
                  "rng.c": digest(ROOT / "portable/game/simulation/rng.c"),
                  "native_probe.c": digest(ROOT / "portable/tests/feeding/native_probe.c")},
              "unit_test_sha256": digest(ROOT / "portable/tests/feeding/test_feeding.c"),
              "native_library_sha256": digest(LIBRARY), "native_command": command,
              "case_count": len(cases), "executed_count": executed,
              "passed": executed - len(failures), "failures": failures,
              "coverage": coverage, "case_inputs": cases,
              "compared_state": ["MapA", "HealthB/HealthR", "food threshold/count/center",
                                 "source S-RNG"],
              "services": {"myBeginSound": "typed host audio intent"},
              "limitations": ["Presentation audio is compared as an ordered intent; all game-state and S-RNG outputs are compared exactly."]}
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"feeding DOS differential: {report['passed']}/{report['executed_count']} pass; report {REPORT}")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
