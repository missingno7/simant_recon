#!/usr/bin/env python3
"""Compare native DoScenario state flow to the frozen original DOS function."""
from __future__ import annotations

import ctypes
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))
import behavior

FIXTURE_C = ROOT / "portable/tests/dialogs/scenario_flow_fixture.c"
FIXTURE_H = ROOT / "portable/tests/dialogs/scenario_flow_fixture.h"
FLOW_C = ROOT / "portable/ui_model/dialogs/scenario_flow.c"
FLOW_H = ROOT / "portable/ui_model/dialogs/scenario_flow.h"
SOURCE = ROOT / "src/S14/m384C.c"
BUILD = ROOT / "build/portable/scenario-flow-differential"
EVIDENCE = ROOT / "portable/tests/dialogs/evidence/scenario-flow-differential.json"


class TraceRow(ctypes.Structure):
    _fields_ = [("kind", ctypes.c_uint16), ("reserved", ctypes.c_uint16),
                ("value", ctypes.c_uint32)]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def native_run(lib, events, ticks, keys):
    event_array = (ctypes.c_uint16 * max(1, len(events)))(*(events or [0]))
    tick_array = (ctypes.c_uint32 * max(1, len(ticks)))(*(ticks or [0]))
    key_array = (ctypes.c_uint16 * max(1, len(keys)))(*(keys or [0]))
    trace = (TraceRow * 2048)()
    count = ctypes.c_size_t()
    result = ctypes.c_uint16()
    status = lib.portable_scenario_flow_fixture_run(
        event_array, len(events), tick_array, len(ticks), key_array, len(keys),
        512, trace, len(trace), ctypes.byref(count), ctypes.byref(result))
    if status != 0:
        raise RuntimeError(f"native scenario fixture failed with status {status}")
    return result.value, [(trace[i].kind, trace[i].reserved, trace[i].value)
                          for i in range(count.value)]


def make_case(label, events, ticks, keys):
    state = {"events": list(events), "event_index": 0,
             "ticks": list(ticks), "tick_index": 0,
             "keys": list(keys), "key_index": 0, "trace": []}

    def record(machine, kind, value, reserved=0):
        machine.state["trace"].append((kind, reserved, value))

    def open_window(machine, args):
        record(machine, 1, args[0])

    def flush(machine, args):
        record(machine, 2, 0)

    def get_event(machine, args):
        current = machine.state
        index = current["event_index"]
        if index >= len(current["events"]):
            record(machine, 3, 0, 0)
            return 0
        code = current["events"][index]
        current["event_index"] += 1
        off, seg = args
        machine.write(seg * 16 + off + 12, (code & 0xffff).to_bytes(2, "little"))
        record(machine, 3, code, 1)
        return 1

    def tick_count(machine, args):
        current = machine.state
        index = current["tick_index"]
        if not current["ticks"]:
            value = 0
        else:
            value = current["ticks"][min(index, len(current["ticks"]) - 1)]
        current["tick_index"] += 1
        record(machine, 4, value)
        return value & 0xffff, (value >> 16) & 0xffff

    def key_available(machine, args):
        available = int(machine.state["key_index"] < len(machine.state["keys"]))
        record(machine, 5, available)
        return available

    def read_key(machine, args):
        current = machine.state
        index = current["key_index"]
        key = current["keys"][index] if index < len(current["keys"]) else 0
        if index < len(current["keys"]):
            current["key_index"] += 1
        record(machine, 6, key)
        return key

    def close_window(machine, args):
        record(machine, 7, args[0])

    def scenario_message(machine, args):
        # WinPrintf(format, code) receives far format pointer then variadic code.
        record(machine, 8, args[2])
        return 0

    callbacks = {
        "win_Open": behavior.Callback(1, open_window),
        "f_218D_042B": behavior.Callback(0, flush),
        "win_GetEvent": behavior.Callback(2, get_event),
        "TickCount": behavior.Callback(0, tick_count),
        "f_1F58_0038": behavior.Callback(0, key_available),
        "f_1F58_0090": behavior.Callback(0, read_key),
        "win_Close": behavior.Callback(0, close_window, register_args=("ax",)),
        "WinPrintf": behavior.Callback(3, scenario_message),
    }
    case = behavior.Case(label=label, callbacks=callbacks, state=state,
                         return_kind="s16", metadata={
                             "contract": "DoScenario event-code selection, 5400-tick per-poll timeout and Escape abort ordering",
                             "validity": "event code is uint16; deterministic TickCount/key host inputs; UI window callbacks are explicit host boundaries",
                             "no_fake_selection": True})
    return case


def main():
    BUILD.mkdir(parents=True, exist_ok=True)
    compiler = "gcc"
    dll = BUILD / "scenario-flow-fixture.dll"
    subprocess.run([compiler, "-std=c11", "-O2", "-Wall", "-Wextra",
                    "-Wconversion", "-Werror", "-shared", "-I", str(ROOT / "portable"),
                    str(FLOW_C), str(FIXTURE_C), "-o", str(dll)],
                   cwd=ROOT, check=True)
    lib = ctypes.CDLL(str(dll))
    run = lib.portable_scenario_flow_fixture_run
    run.argtypes = [ctypes.POINTER(ctypes.c_uint16), ctypes.c_size_t,
                    ctypes.POINTER(ctypes.c_uint32), ctypes.c_size_t,
                    ctypes.POINTER(ctypes.c_uint16), ctypes.c_size_t,
                    ctypes.c_uint, ctypes.POINTER(TraceRow), ctypes.c_size_t,
                    ctypes.POINTER(ctypes.c_size_t), ctypes.POINTER(ctypes.c_uint16)]
    run.restype = ctypes.c_int

    # This pair loads the immutable DOS function. The compiler-produced source
    # is the frozen S14 TU used to establish the verified member/module context;
    # comparisons below are original VM versus the independent native API.
    pair = behavior.PreparedPair("DoScenario", source=SOURCE)
    cases = []
    stable = [100] * 32
    for code in range(0x0200, 0x0300):
        cases.append((f"recognized/{code:04x}", [code], [], [0x1b]))
    for code in (0x0000, 0x0001, 0x01ff, 0x0300, 0x7fff, 0x8000,
                 0x8202, 0xff00, 0xffff):
        cases.append((f"ignored-then-selected/{code:04x}", [code, 0x02ff], stable, []))
    cases += [
        ("escape-without-event", [], stable, [0x1b]),
        ("non-escape-then-escape", [0x0101, 0x0300], stable, [ord("x"), 0x1b]),
        ("timeout-exact-5400", [0x0001], [100, 100, 100, 101, 101, 5501], []),
        ("timeout-one-before-continues", [0x0001, 0x0206],
         [101, 101, 5500], []),
        ("signed-backwards-refreshes-baseline", [0x0001],
         [100, 99, 77], []),
        ("signed-high-to-low-is-backwards", [0x0001],
         [0x7fffffff, 0x80000000, 0x80000001], []),
        ("signed-low-to-high-is-forward", [0x0001, 0x0206],
         [0x80000000, 0x7fffffff, 0x7fffffff], []),
        ("accepted-0205-priority-over-abort", [0x0205], [100, 100, 5500], [0x1b]),
        ("newgame-file-load-selector-0207", [0x0207], [], []),
    ]
    rows = []
    for label, events, ticks, keys in cases:
        native_result, native_trace = native_run(lib, events, ticks, keys)
        case = make_case(label, events, ticks, keys)
        original = pair.original_machine.run(case)
        oracle_trace = pair.original_machine.state["trace"]
        equal = original["return"] == native_result and oracle_trace == native_trace
        rows.append({"label": label, "events": events, "tick_script": ticks,
                     "keys": keys, "equal": equal,
                     "oracle_return": original["return"], "native_return": native_result,
                     "oracle_trace": oracle_trace, "native_trace": native_trace})
        if not equal:
            raise SystemExit(json.dumps(rows[-1], indent=2))

    report = {
        "schema": "scenario-flow-differential-v1",
        "status": "PASS",
        "claim": "actual frozen DOS DoScenario versus native C scenario flow; host window/input/clock/key callbacks are explicitly modeled",
        "source": {"path": "src/S14/m384C.c", "sha256": digest(SOURCE)},
        "native_api": {"source": "portable/ui_model/dialogs/scenario_flow.c",
                       "source_sha256": digest(FLOW_C), "header_sha256": digest(FLOW_H)},
        "original_pair_identity": pair.identity,
        "suite_inputs_sha256": {path.relative_to(ROOT).as_posix(): digest(path)
                                  for path in (FIXTURE_C, FIXTURE_H, FLOW_C, FLOW_H,
                                               SOURCE, Path(__file__))},
        "cases": {"directed": len(rows), "executed_original": len(rows),
                  "executed_native": len(rows), "mismatches": 0,
                  "event_codes_exhaustive": "0x0200..0x02ff"},
        "compared_effects": ["returned scenario/cancel code", "ordered open/flush/event/clock/key/close/message callback trace"],
        "modelled_boundaries": {
            "window/input": "open 0x0200, explicit win_FlushEvents, win_GetEvent, close 0x0200, WinPrintf message",
            "clock": "TickCount returns deterministic DWORD sequence; original DialogClearWait/WaitedEnough/DialogAbort execute unchanged",
            "keyboard": "f_1F58_0038/f_1F58_0090 model only BIOS key availability/dequeue; original DialogAbort executes unchanged",
        },
        "limits": ["No SDL window or real BIOS keyboard is used in this finite differential.",
                   "The source passes 0x0207 unchanged; NewGame's file-load action remains a higher-level service."],
        "results": rows,
    }
    EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items()
                      if key not in {"results", "original_pair_identity", "suite_inputs_sha256"}}, indent=2))
    print(f"evidence: {EVIDENCE.relative_to(ROOT).as_posix()}")


if __name__ == "__main__":
    main()
