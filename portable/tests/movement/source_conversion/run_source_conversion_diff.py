#!/usr/bin/env python3
"""Compare mechanically converted S25 GetMyRandDirs scaffold to original DOS."""
from __future__ import annotations

import argparse
import ctypes as ct
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
TOOLS = ROOT / "tools"
ARCHIVED_SUITE = ROOT / "tools/behavior_suites/archive/randdirs-20261002-current-runner-ledger-final.py"
ARCHIVED_SUITE_SHA256 = "f7aad88da70befc902bcc4b8f48670f43df38e90f81e45a59ef4c584090dd360"
LIBRARY = ROOT / "build/portable/movement/source_conversion/get-my-rand-dirs-converted-v1.dll"
GCC = Path("C:/msys64/mingw64/bin/gcc.exe")
FUNCTION = "o25_3BA4_1686"

sys.path.insert(0, str(TOOLS))
import behavior
import functions


class Scenario(ct.Structure):
    pass


class SourceConversionWorld(ct.Structure):
    _fields_ = [
        ("surface", (ct.c_uint8 * 64) * 128),
        ("nest_b", (ct.c_uint8 * 64) * 64),
        ("nest_r", (ct.c_uint8 * 64) * 64),
        ("terrain_set", ct.c_int16),
    ]


class SourceConversionCall(ct.Structure):
    _fields_ = [("kind", ct.c_int16), ("args", ct.c_int16 * 7)]


class SourceConversionResult(ct.Structure):
    _fields_ = [("result", ct.c_int16), ("rot", ct.c_int16),
                ("direction", ct.c_int16), ("call_count", ct.c_int16),
                ("calls", SourceConversionCall * 32)]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_suite():
    digest = sha(ARCHIVED_SUITE)
    if digest != ARCHIVED_SUITE_SHA256:
        raise RuntimeError(f"archived case suite hash mismatch: {digest}")
    spec = importlib.util.spec_from_file_location("source_conversion_randdirs", ARCHIVED_SUITE)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load the pinned archived scenario suite")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module, digest


def require_extracted_sources() -> dict:
    identity_path = HERE / "source_identity_v1.json"
    identity = json.loads(identity_path.read_text(encoding="utf-8"))
    outputs = identity["outputs"]
    for key in ("target_path", "helper_path", "identity_path"):
        path = ROOT / outputs[key]
        if not path.is_file():
            raise RuntimeError(f"missing extracted source artifact: {path}")
    target_source = HERE / "get_my_rand_dirs_extracted.c"
    helper_source = HERE / "get_dir_dis_extracted.c"
    if sha(target_source) != identity["conversion"]["target_converted_sha256"]:
        raise RuntimeError("extracted target source hash differs from its immutable identity record")
    return identity


def build_library() -> tuple[str, list[str]]:
    LIBRARY.parent.mkdir(parents=True, exist_ok=True)
    command = [str(GCC), "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
               "-Wno-unused-but-set-variable", "-shared",
               "-I", str(ROOT), "-I", str(HERE),
               str(HERE / "get_my_rand_dirs_extracted.c"),
               str(HERE / "get_dir_dis_extracted.c"),
               str(HERE / "conversion_fixture.c"),
               str(ROOT / "portable/game/simulation/movement.c"), "-o", str(LIBRARY)]
    subprocess.run(command, check=True, cwd=ROOT, capture_output=True, text=True)
    return sha(LIBRARY), command


def configure_library(lib):
    lib.source_conversion_run.argtypes = [
        ct.POINTER(SourceConversionWorld), ct.POINTER(ct.c_int8), ct.POINTER(ct.c_int8),
        ct.c_int16, ct.c_int16, ct.c_int16, ct.c_int16, ct.c_int16, ct.c_int16,
        ct.c_int16, ct.c_int16, ct.c_int16, ct.c_int16, ct.c_int16,
        ct.c_int16, ct.c_int16, ct.POINTER(SourceConversionResult),
    ]
    lib.source_conversion_run.restype = None


def signed16(value: int) -> int:
    value &= 0xffff
    return value - 0x10000 if value >= 0x8000 else value


def native_world_from_case(case) -> SourceConversionWorld:
    world = SourceConversionWorld()
    bases = {name: behavior.symbol_address(name) for name in ("MapA", "MapB", "MapR")}
    sizes = {"MapA": 128 * 64, "MapB": 64 * 64, "MapR": 64 * 64}
    buffers = {"MapA": ct.cast(world.surface, ct.POINTER(ct.c_uint8)),
               "MapB": ct.cast(world.nest_b, ct.POINTER(ct.c_uint8)),
               "MapR": ct.cast(world.nest_r, ct.POINTER(ct.c_uint8))}
    terrain_address = behavior.symbol_address("TERRAINset")
    for address, data in case.writes:
        if address == terrain_address:
            world.terrain_set = int.from_bytes(data[:2], "little", signed=True)
            continue
        for name, base in bases.items():
            if base <= address < base + sizes[name]:
                buffers[name][address - base] = data[0]
                break
    return world


def original_direction_tables() -> tuple[ct.Array, ct.Array]:
    image = behavior.exe.load()
    result = []
    for name in ("fd_3D57_0000", "fd_3D57_0008"):
        address = behavior.symbol_address(name)
        units = image.unit_for_linear(address)
        if len(units) != 1:
            raise RuntimeError(f"direction table does not have one original-data owner: {name} {units}")
        raw = image.read(units[0], address, 8)
        result.append((ct.c_int8 * 8)(*(int.from_bytes(bytes((byte,)), "little", signed=True)
                                      for byte in raw)))
    return result[0], result[1]


def native_call(lib, case, suite, dx, dy):
    scenario = suite._case_scenario(case)
    world = native_world_from_case(case)
    result = SourceConversionResult()
    lib.source_conversion_run(
        ct.byref(world), dx, dy,
        scenario.mode, scenario.from_plane, scenario.from_x, scenario.from_y,
        scenario.previous_x, scenario.previous_y,
        scenario.plane, scenario.x, scenario.y, scenario.a, scenario.b,
        scenario.rot, scenario.direction, ct.byref(result))
    calls = {1: [], 2: [], 3: []}
    for item in result.calls[:result.call_count]:
        count = 7 if item.kind == 3 else 4
        calls[int(item.kind)].append(tuple(signed16(v) for v in item.args[:count]))
    return scenario, result, calls


def original_outputs(oracle: dict) -> tuple[int, int, int]:
    rot = int.from_bytes(bytes.fromhex(oracle["ranges"]["fd_50F6_0EFA"]), "little", signed=True)
    direction = int.from_bytes(bytes.fromhex(oracle["ranges"]["fd_50F6_0EF8"]), "little", signed=True)
    return int(oracle["return"]), rot, direction


def model_calls(model: dict) -> dict[int, list[tuple[int, ...]]]:
    trace = model["helper_trace"]
    return {
        1: [tuple(map(signed16, item)) for item in trace["direction"]],
        2: [tuple(map(signed16, item)) for item in trace["distance"]],
        3: [tuple(map(signed16, item)) for item in trace["move"]],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--random-count", type=int, default=100000)
    parser.add_argument("--random-only", action="store_true")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--seed", type=lambda value: int(value, 0), default=0x1686)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    report_path = args.report if args.report.is_absolute() else ROOT / args.report
    if report_path.exists():
        raise SystemExit(f"refusing to overwrite existing report: {report_path}")

    identity = require_extracted_sources()
    suite, suite_hash = load_suite()
    source_files = [
        HERE / "extract_source.py", HERE / "source_identity_v1.json",
        HERE / "get_my_rand_dirs_extracted.c", HERE / "get_dir_dis_extracted.c",
        HERE / "recovered_state.h", HERE / "conversion_fixture.h", HERE / "conversion_fixture.c",
        Path(__file__).resolve(), ARCHIVED_SUITE, ROOT / "portable/tools/recover_source.py",
        ROOT / "src/S25/m3BA4.c", ROOT / "src/root/m0BE8.c",
        ROOT / "portable/game/simulation/movement.c", ROOT / "portable/game/simulation/movement.h",
        ROOT / "evidence/behavior/functions/o25_3BA4_1686/evidence.json",
        ROOT / "evidence/behavior/functions/o25_3BA4_1686/module.c",
        ROOT / "evidence/behavior/manifest.json", ROOT / "layout/manifest.json",
    ]
    before = {p.relative_to(ROOT).as_posix(): sha(p) for p in source_files}
    oracle_exe_sha = behavior.exe.load().sha256
    lib_sha, build_command = build_library()
    lib = ct.CDLL(str(LIBRARY))
    configure_library(lib)
    dx, dy = original_direction_tables()

    pair = behavior.PreparedPair(FUNCTION)
    machine = pair.original_machine
    count = 0
    output_mismatches = 0
    helper_model_mismatches = 0
    first_mismatch = None
    cases = suite.iter_cases(directed=not args.random_only, random_seed=args.seed,
                             random_count=args.random_count, limit_total=args.limit,
                             actual_tile=True)
    for case in cases:
        oracle = machine.run(case)
        scenario, native, native_helper_calls = native_call(lib, case, suite, dx, dy)
        expected_outputs = original_outputs(oracle)
        actual_outputs = (int(native.result), int(native.rot), int(native.direction))
        source_model = suite.source_contract_model(scenario)
        helper_expected = model_calls(source_model)
        # The model is only an independent source-contract check for the native
        # helper trace. DOS function output remains the pass/fail oracle.
        mismatch = expected_outputs != actual_outputs
        helper_mismatch = helper_expected != native_helper_calls
        count += 1
        output_mismatches += int(mismatch)
        helper_model_mismatches += int(helper_mismatch)
        if mismatch or helper_mismatch:
            first_mismatch = {
                "case_id": scenario.case_id,
                "input": scenario.as_dict(),
                "original_dos": {"return_rot_direction": expected_outputs},
                "converted_native": {"return_rot_direction": actual_outputs,
                                     "helper_calls": native_helper_calls},
                "source_model_helper_trace": helper_expected,
                "dos_trace_capture_note": "The DOS helper bodies execute directly and are not VM callback traces.",
            }
            break
        if count % 1000 == 0:
            print(f"source-converted-vs-original-DOS cases={count}", flush=True)

    after = {p.relative_to(ROOT).as_posix(): sha(p) for p in source_files}
    status = "PASS" if count and output_mismatches == 0 and helper_model_mismatches == 0 else "MISMATCH"
    report = {
        "schema": "get-my-rand-dirs-source-conversion-dos-diff-v1",
        "status": status,
        "scope": {
            "function": FUNCTION,
            "lane": "mechanically converted current historical scaffold vs original DOS function",
            "compared_outputs": ["return", "rot pointed word", "direction pointed word"],
            "native_tile_helper": "portable sim_tile_can_be_moved_on; separate original-DOS helper differential exists",
            "original_lane": "actual original function with actual DOS GetDir/GetDis/TileCanBeMovedOn helper bodies",
            "native_helper_trace_check": "per-helper call arguments compared with existing source_contract_model; cross-kind ordering is not inferred from its split trace lists and is not claimed as DOS trace",
            "behavioral_status_context": "The frozen BEHAVIOR_EXACT packet describes a separately reviewed module.c source; this extracted src/S25/m3BA4.c body is the SCAFFOLD draft and is not that candidate.",
            "historical_exact_context": "S25:3BA4 manifest lists o25_3BA4_1686 in scaffold, with no per-function EXACT claim.",
        },
        "corpus": {
            "directed_enabled": not args.random_only,
            "random_count_requested": args.random_count,
            "random_seed": args.seed,
            "case_limit": args.limit,
            "cases_executed": count,
            "dos_output_mismatches": output_mismatches,
            "native_helper_trace_vs_model_mismatches": helper_model_mismatches,
            "first_mismatch": first_mismatch,
        },
        "identities": {
            "source_identity": identity,
            "source_inputs_sha256_before": before,
            "source_inputs_sha256_after": after,
            "source_inputs_unchanged": before == after,
            "original_exe_sha256": oracle_exe_sha,
            "historical_manifest_sha256": sha(ROOT / "layout/manifest.json"),
            "archived_suite_sha256": suite_hash,
            "runner_sha256": sha(Path(__file__).resolve()),
            "native_library_sha256": lib_sha,
            "build_command": build_command,
            "compiler_sha256": sha(GCC),
            "compiler_version": subprocess.run([str(GCC), "--version"], check=True,
                                                 capture_output=True, text=True).stdout.splitlines()[0],
            "direction_table_bytes_from_original_image": {
                "fd_3D57_0000": [int(v) for v in dx],
                "fd_3D57_0008": [int(v) for v in dy],
            },
        },
        "limits": [
            "This is a finite test of the current SCAFFOLD body and typed fixture bridge; it does not change the reviewed BEHAVIOR_EXACT packet.",
            "The native TileCanBeMovedOn implementation is independently tested against DOS, but is not the extracted DOS helper body.",
            "This test does not establish whole simulation integration, invalid caller pointer behavior, or unsupported malformed map histories.",
        ],
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("x", encoding="utf-8", newline="") as stream:
        stream.write(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"status": status, "cases": count,
                      "dos_output_mismatches": output_mismatches,
                      "helper_trace_model_mismatches": helper_model_mismatches,
                      "report": str(report_path.relative_to(ROOT))}, indent=2))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
