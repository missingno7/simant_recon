#!/usr/bin/env python3
"""Verify the generated-RecoveredState EnterNest binding against DOS."""
from __future__ import annotations

import ctypes as ct
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
GENERATED = ROOT / "build/workers/recovered_source/generated"
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))
import behavior  # noqa: E402

NEST_RUNNER_PATH = ROOT / "portable/tests/nest/run_dos_diff.py"
spec = importlib.util.spec_from_file_location("nest_diff_adapter", NEST_RUNNER_PATH)
assert spec and spec.loader
nest = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = nest
spec.loader.exec_module(nest)

LIBRARY = ROOT / "build/portable/recovered-nest-adapter.dll"
GCC = Path("C:/msys64/mingw64/bin/gcc.exe")


def build_native():
    LIBRARY.parent.mkdir(parents=True, exist_ok=True)
    command = [str(GCC), "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror", "-shared",
        "-I", str(ROOT), "-I", str(GENERATED),
        "-I", str(ROOT / "portable/game/simulation"),
        "-I", str(ROOT / "portable/game/recovered"),
        "-I", str(ROOT / "portable/tests/nest"),
        str(ROOT / "portable/tests/recovered/nest_adapter_test.c"),
        str(ROOT / "portable/game/recovered/nest_adapter.c"),
        str(GENERATED / "recovered_state.c"),
        str(ROOT / "portable/game/simulation/nest.c"),
        str(ROOT / "portable/game/simulation/rng.c"), "-o", str(LIBRARY)]
    subprocess.run(command, check=True, cwd=ROOT)
    library = ct.CDLL(str(LIBRARY))
    library.sim_recovered_nest_test_run.argtypes = [
        ct.POINTER(nest.SimNestTestWorld), ct.POINTER(nest.SimRng),
        ct.POINTER(nest.SimNestRuntime), ct.POINTER(nest.SimNestRequest),
        ct.POINTER(nest.SimNestTrace)]
    library.sim_recovered_nest_test_run.restype = ct.c_int
    library.sim_recovered_nest_test_run_with_live_clock.argtypes = [
        ct.POINTER(nest.SimNestTestWorld), ct.POINTER(nest.SimRng),
        ct.POINTER(nest.SimNestRuntime), ct.POINTER(nest.SimNestTrace),
        ct.POINTER(ct.c_int32), ct.c_uint32, ct.POINTER(ct.c_uint32)]
    library.sim_recovered_nest_test_run_with_live_clock.restype = ct.c_int
    return library, command, hashlib.sha256(LIBRARY.read_bytes()).hexdigest()


def native_call(library, case):
    domain = case.metadata["native_port_case"]
    runtime = nest.SimNestRuntime()
    runtime.alarm_drop_state = domain.get("alarm", case.metadata["domain"]["alarm"])
    runtime.alarm_indicator = 7
    runtime.theme_index = domain["theme_index"]
    runtime.theme_last_tick = domain["theme_last"]
    runtime.invalidate_right = 64
    runtime.invalidate_bottom = 32
    request = nest.SimNestRequest()
    request.tick_values[0] = domain["tick_values"][0]
    request.tick_values[1] = domain["tick_values"][1]
    request.tick_count = 2
    rng = nest.SimRng(0xBEEF, 0)
    trace = nest.SimNestTrace()
    world = nest.build_native_world(case)
    status = library.sim_recovered_nest_test_run(
        ct.byref(world), ct.byref(rng), ct.byref(runtime),
        ct.byref(request), ct.byref(trace))
    return int(status), world, rng, runtime, trace


def run_live_provider_controls(library):
    results = []
    for label, ticks, fail_on_call, expected_status, expected_calls in (
        ("success-two-samples", (7200, 7205), 0, 0, 2),
        ("success-one-sample", (7199, 7205), 0, 0, 1),
        ("second-sample-fails", (7200, 7205), 2, 5, 2),
    ):
        world = nest.SimNestTestWorld()
        world.current_ant_plane = 1
        world.me_x = 10
        world.me_y = 10
        world.me_type = 0x20
        world.me_direction = 0
        runtime = nest.SimNestRuntime()
        runtime.theme_last_tick = 0
        rng = nest.SimRng(0xBEEF, 0)
        trace = nest.SimNestTrace()
        tick_values = (ct.c_int32 * 2)(*ticks)
        calls = ct.c_uint32()
        status = library.sim_recovered_nest_test_run_with_live_clock(
            ct.byref(world), ct.byref(rng), ct.byref(runtime),
            ct.byref(trace), tick_values, fail_on_call, ct.byref(calls))
        ok = int(status) == expected_status and calls.value == expected_calls
        if expected_status == 0:
            if expected_calls == 2:
                ok = ok and runtime.theme_last_tick == 7205 and runtime.theme_index == 1
            else:
                ok = ok and runtime.theme_last_tick == 0 and runtime.theme_index == 0
        else:
            ok = ok and runtime.theme_last_tick == 0 and runtime.theme_index == 0
        results.append({"label": label, "status": int(status),
                        "provider_calls": int(calls.value),
                        "theme_last_tick": int(runtime.theme_last_tick),
                        "theme_index": int(runtime.theme_index), "pass": bool(ok)})
    return results


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--random-count", type=int, default=0)
    parser.add_argument("--dirt-cases", type=int, default=128)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--report", type=Path,
        default=ROOT / "build/portable/recovered-nest-adapter-diff.json")
    args = parser.parse_args()
    library, command, library_hash = build_native()
    suite = nest.read_suite()
    pair = behavior.PreparedPair("o25_3BA4_1035")
    machine = pair.original_machine

    def cases():
        index = 0
        for case in suite.make_cases("EnterNest", directed=True,
                                     random_count=args.random_count,
                                     original_helpers=("SRand1", "SRand4")):
            case.callbacks["myBeginSound"] = behavior.Callback(
                stack_words=3, handler=suite._noop, pop=0)
            yield nest.controlled_case(case, index)
            index += 1
        for i in range(args.dirt_cases):
            tile_mode = "dirt" if i % 2 == 0 else "grass"
            case = next(suite.make_cases("EnterNest", directed=True,
                                         random_count=0,
                                         original_helpers=("SRand1", "SRand4")))
            case.callbacks["myBeginSound"] = behavior.Callback(
                stack_words=3, handler=suite._noop, pop=0)
            case.label = f"recovered-adapter-{tile_mode}-{i:04d}"
            case.metadata["domain"].update({
                "initial_plane": 2 + (i & 1),
                "initial_x": (i % 2) * 65 + (1 if i % 4 < 2 else 64),
                "initial_y": (i * 7) % 64,
                "ant_type": 0x60 if i % 3 == 0 else 0x20,
                "initial_direction": i & 7,
                "alarm": i & 1,
            })
            for name, value in (
                ("MePlane", case.metadata["domain"]["initial_plane"]),
                ("MeLocX", case.metadata["domain"]["initial_x"]),
                ("MeLocY", case.metadata["domain"]["initial_y"]),
                ("fd_50F6_0496", case.metadata["domain"]["initial_direction"]),
                ("fd_50F6_04C2", case.metadata["domain"]["ant_type"]),
                ("fd_50F6_104E", case.metadata["domain"]["alarm"])):
                nest.append_write(case, name, value)
            yield nest.controlled_case(case, index + i, tile_mode)

    # Reuse the established per-case DOS contract comparison, substituting only
    # the adapter execution lane. Oracle source/helper execution is unchanged.
    nest.native_call = native_call
    failures = None
    count = 0
    for case in cases():
        if args.limit is not None and count >= args.limit:
            break
        failures = nest.compare_case(machine, library, suite, case)
        count += 1
        if failures:
            break
        if count % 100 == 0:
            print(f"RecoveredState EnterNest adapter cases={count}", flush=True)

    live_provider_controls = run_live_provider_controls(library)
    if not all(control["pass"] for control in live_provider_controls):
        failures = failures or {"kind": "live TickCount provider control mismatch",
                               "cases": live_provider_controls}

    source_paths = [
        "portable/game/recovered/nest_adapter.c",
        "portable/game/recovered/nest_adapter.h",
        "portable/tests/recovered/nest_adapter_test.c",
        "portable/tests/recovered/run_nest_adapter_diff.py",
        "portable/game/simulation/nest.c",
        "portable/game/simulation/nest.h",
        "portable/tests/nest/live_clock_test.c",
        "portable/tests/nest/run_live_clock_test.py",
        "build/workers/recovered_source/generated/recovered_state.c",
        "build/workers/recovered_source/generated/recovered_state.h",
        "build/workers/recovered_source/generated/recovered_native_adapters.c",
        "build/workers/recovered_source/generated/S25_m3BA4.c",
        "build/workers/recovered_source/generated/provenance.json",
        "portable/tests/nest/run_dos_diff.py",
    ]
    report = {
        "schema": "recovered-state-enter-nest-adapter-diff-v1",
        "oracle_sha256": behavior.exe.load().sha256,
        "historical_manifest_sha256": hashlib.sha256(
            (ROOT / "layout/manifest.json").read_bytes()).hexdigest(),
        "generated_state_sha256": hashlib.sha256(
            (GENERATED / "recovered_state.h").read_bytes()).hexdigest(),
        "entry": "o25_3BA4_1035 -> sim_recovered_nest_apply -> sim_enter_nest",
        "executed": count,
        "matched": count - int(failures is not None),
        "mismatches": int(failures is not None),
        "first_mismatch": failures,
        "domain": {"archived_enter_nest_cases": True,
                   "random_count": args.random_count,
                   "dirt_and_grass_cases": args.dirt_cases,
                   "live_tick_provider_controls": live_provider_controls,
                   "source_helpers": ["SRand1", "SRand4"]},
        "native": {"library_sha256": library_hash,
                   "build_command": command,
                   "source_sha256": {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
                                     for p in source_paths}},
        "status": "PASS" if failures is None else "MISMATCH",
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "executed": count,
                      "report": str(args.report), "first_mismatch": failures}, indent=2))
    return int(failures is not None)


if __name__ == "__main__":
    raise SystemExit(main())
