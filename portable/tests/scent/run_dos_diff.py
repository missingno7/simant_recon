#!/usr/bin/env python3
"""Differentially execute original DOS pheromone routines and native ports."""
from __future__ import annotations

import ctypes as ct
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
LIBRARY = ROOT / "build/portable/scent-probe.dll"
REPORT = ROOT / "build/portable/scent-dos-diff.json"
PHER = 64 * 32
PHEROMONES = ("PherMapA", "PherMapBN", "PherMapBT", "PherMapRN", "PherMapRT",
              "fd_3E1D_D89F", "fd_3E1D_C89F")
OPERATIONS = ("ColonySmellBN", "ColonySmellRN", "ColonySmellBT",
              "ColonySmellRT", "SmoothAlarm")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def address(name: str) -> int:
    symbol = behavior.symbol(name)
    return symbol["seg"] * 16 + symbol["off"]


def build_native():
    command = [str(GCC), "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
               "-shared", "-I", str(ROOT / "portable"),
               str(ROOT / "portable/game/simulation/scent.c"),
               str(ROOT / "portable/tests/scent/native_probe.c"),
               "-o", str(LIBRARY)]
    LIBRARY.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(command, cwd=ROOT, check=True)
    library = ct.CDLL(str(LIBRARY))
    library.sim_scent_probe.argtypes = [ct.POINTER(ct.c_uint8), ct.c_size_t,
                                        ct.POINTER(ct.c_uint8), ct.c_size_t]
    library.sim_scent_probe.restype = ct.c_int
    return library, command


def fixture(seed: int, directed: bool):
    rng = random.Random(seed)
    if directed:
        values = [0, 1, 7, 8, 9, 15, 127, 128, 254, 255]
        arrays = [bytearray(rng.choice(values) for _ in range(PHER)) for _ in PHEROMONES]
        # Exercise all four smoothing edges and corners with concentrated maxima.
        for x, y, value in ((0, 0, 255), (63, 0, 9), (0, 31, 8),
                            (63, 31, 7), (1, 0, 255), (0, 1, 255),
                            (62, 31, 255), (63, 30, 255)):
            arrays[0][x * 32 + y] = value
    else:
        arrays = [bytearray(rng.randrange(256) for _ in range(PHER))
                  for _ in PHEROMONES]
    op = seed % len(OPERATIONS)
    payload = op.to_bytes(2, "little") + b"".join(arrays)
    writes = [(address(name), bytes(data)) for name, data in zip(PHEROMONES, arrays)]
    return op, payload, writes


def ranges_to_bytes(ranges):
    return b"".join(bytes.fromhex(ranges[name]) for name in
                    ("pher_a", "pher_bn", "pher_bt", "pher_rn", "pher_rt",
                     "pher_aux_d89f", "smooth_work_c89f"))


def make_ranges():
    keys = ("pher_a", "pher_bn", "pher_bt", "pher_rn", "pher_rt",
            "pher_aux_d89f", "smooth_work_c89f")
    return [behavior.Range(key, address(symbol), PHER)
            for key, symbol in zip(keys, PHEROMONES)]


def native_call(library, payload):
    inp = (ct.c_uint8 * len(payload)).from_buffer_copy(payload)
    out = (ct.c_uint8 * (1 + 7 * PHER))()
    length = library.sim_scent_probe(inp, len(payload), out, len(out))
    if length < 0:
        raise RuntimeError(f"native probe rejected input with {length}")
    data = bytes(out[:length])
    return data[0], data[1:]


def main():
    library, command = build_native()
    image = exe.load()
    vectors = {exe.MANAGER_SEG * 16 + vector.offset: vector
               for vector in image.vectors}
    pairs = {}
    machines = {}
    for name in OPERATIONS:
        target = functions.get(name)
        pair = SimpleNamespace(function=target, vectors=vectors)
        pair.sequence_function = lambda symbol: functions.get(symbol)
        pairs[name] = pair
        machines[name] = behavior.Machine(pair)

    cases = []
    for op in range(len(OPERATIONS)):
        # Make directed rows map one-to-one to each function before random cases.
        for i in range(8):
            seed = op + len(OPERATIONS) * i
            cases.append((f"directed/{OPERATIONS[op]}/{i}", op, seed, True))
    for i in range(320):
        seed = 0x5CE17 + i * 97
        cases.append((f"random/{i:03d}", seed % len(OPERATIONS), seed, False))

    failures = []
    executed = 0
    coverage = {name: 0 for name in OPERATIONS}
    for label, op, seed, directed in cases:
        payload_op, payload, writes = fixture(seed, directed)
        if payload_op != op:
            # Directed inputs use a seed selected to produce the requested op.
            seed += (op - payload_op) % len(OPERATIONS)
            payload_op, payload, writes = fixture(seed, directed)
        native_status, native_state = native_call(library, payload)
        name = OPERATIONS[op]
        machine = machines[name]
        result = machine.run(behavior.Case(label, writes=writes, observe=make_ranges(),
                                           return_kind="void"), function=name)
        original_state = ranges_to_bytes(result["ranges"])
        coverage[name] += 1
        if native_status != 0 or native_state != original_state:
            first = next((i for i, (a, b) in enumerate(zip(native_state, original_state))
                          if a != b), min(len(native_state), len(original_state)))
            failures.append({"case": label, "function": name,
                             "native_status": native_status,
                             "first_mismatch": first,
                             "native_sha256": hashlib.sha256(native_state).hexdigest(),
                             "original_sha256": hashlib.sha256(original_state).hexdigest(),
                             "native_length": len(native_state),
                             "original_length": len(original_state)})
        executed += 1

    report = {"schema": "portable-scent-dos-diff-v1",
              "oracle_execution": "original DOS only",
              "runner_sha256": digest(Path(__file__)),
              "oracle_exe_sha256": digest(exe.EXE_PATH),
              "harness_sha256": {name: digest(ROOT / "tools" / f"{name}.py")
                                  for name in ("behavior", "exe", "functions", "match")},
              "native_source_sha256": {
                  "scent.c": digest(ROOT / "portable/game/simulation/scent.c"),
                  "scent.h": digest(ROOT / "portable/game/simulation/scent.h"),
                  "native_probe.c": digest(ROOT / "portable/tests/scent/native_probe.c")},
              "unit_test_sha256": digest(ROOT / "portable/tests/scent/test_scent.c"),
              "native_library_sha256": digest(LIBRARY), "native_command": command,
              "case_count": len(cases), "executed_count": executed,
              "passed": executed - len(failures), "failures": failures,
              "coverage": coverage,
              "input_seed_algorithm": "directed boundaries plus seed = 0x5CE17 + caseIndex*97",
              "compared_state": ["PherMapA", "PherMapBN", "PherMapBT", "PherMapRN",
                                 "PherMapRT", "fd_3E1D_D89F untouched aux", "fd_3E1D_C89F SmoothAlarm work"],
              "services": {},
              "limitations": ["Tests the exact pheromone child bodies only; it does not claim full DoSmells dispatch, CompactList, FullCount, or history-window behavior."]}
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"scent DOS differential: {report['passed']}/{executed} pass; report {REPORT}")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
