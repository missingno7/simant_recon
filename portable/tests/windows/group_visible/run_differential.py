#!/usr/bin/env python3
"""Exhaustive bounded DOS/native comparison for group visibility changes."""
from __future__ import annotations

import argparse
import ctypes as ct
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[4]
PORT = ROOT / "portable"
HERE = PORT / "tests/windows/group_visible"
TOOLS = ROOT / "tools"
PROFILED_GROUPS = (0, 7, 255)
TYPES = (0, 1, 5, 6, 13, 17, 255)
WINDOW_ID = 0x1200
WINDOW_SEG = 0x6000
WINDOW_OFF = 0x0100
OBJECT_BASE_OFF = 0x1000
OBJECT_STRIDE = 0x0040
MAX_OBJECTS = 16
MAX_EFFECTS = 16

sys.path.insert(0, str(TOOLS))
sys.path.insert(0, str(ROOT / "build/behavior/deps"))
import behavior  # noqa: E402
import exe  # noqa: E402
import functions  # noqa: E402
import match  # noqa: E402

ORIGINAL_SOURCE = ROOT / "src/root/m22BF.c"
NATIVE_SOURCE = HERE / "native_probe.c"
OPERATIONS_C = PORT / "ui_model/windows/operations.c"
OPERATIONS_H = PORT / "ui_model/windows/operations.h"
REPORT_DEFAULT = HERE / "evidence/group-visible-dos-native-final-20261002.json"
BUILD = ROOT / "build/portable/tests/windows/group-visible"
GCC_DEFAULT = Path("C:/msys64/mingw64/bin/gcc.exe")


class NativeTrace(ct.Structure):
    _fields_ = [("count", ct.c_uint16),
                ("ids", ct.c_uint16 * MAX_EFFECTS),
                ("kinds", ct.c_uint16 * MAX_EFFECTS)]


class OriginalPair:
    function = functions.get("win_SetGroupVisibleState")
    vectors = {exe.MANAGER_SEG * 16 + vector.offset: vector
               for vector in exe.load().vectors}
    delegate = {}
    candidate_entries = {}
    sequence_targets = set()

    @staticmethod
    def sequence_function(name: str):
        return functions.get(name)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def input_key(path: Path) -> str:
    path = path.resolve()
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def digest_object(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True,
                                     separators=(",", ":")).encode()).hexdigest()


def dependency_closure(compiler: Path) -> list[Path]:
    sources = [NATIVE_SOURCE, OPERATIONS_C]
    found: set[Path] = set()
    for source in sources:
        proc = subprocess.run([str(compiler), "-std=c11", "-MM", f"-I{ROOT}",
                               f"-I{PORT}", str(source)], cwd=ROOT,
                              text=True, capture_output=True, check=True, timeout=15)
        text = proc.stdout.split(":", 1)[1].replace("\\\r\n", " ").replace("\\\n", " ")
        for token in text.split():
            path = Path(token)
            if not path.is_absolute():
                path = ROOT / path
            path = path.resolve()
            if path.is_relative_to(ROOT):
                found.add(path)
        found.add(source.resolve())
    return sorted(found)


def build_native(compiler: Path) -> tuple[Path, dict[str, str], list[str]]:
    BUILD.mkdir(parents=True, exist_ok=True)
    output = BUILD / "group-visible-probe.dll"
    closure = dependency_closure(compiler)
    command = [str(compiler), "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
               "-shared", f"-I{ROOT}", f"-I{PORT}", str(NATIVE_SOURCE),
               str(OPERATIONS_C), "-o", str(output)]
    subprocess.run(command, cwd=ROOT, check=True, timeout=30)
    return output, {path.relative_to(ROOT).as_posix(): sha(path) for path in closure}, command


def native_function(path: Path):
    lib = ct.CDLL(str(path))
    run = lib.group_visible_native_run
    run.argtypes = [ct.c_uint16, ct.c_uint8, ct.c_int, ct.c_uint16,
                    ct.POINTER(ct.c_uint8), ct.POINTER(ct.c_uint8),
                    ct.POINTER(ct.c_uint16), ct.POINTER(ct.c_uint16),
                    ct.POINTER(NativeTrace)]
    run.restype = ct.c_int
    return lib, run


def pinned_input_paths(compiler: Path, c_closure: list[Path], wheel: Path) -> list[Path]:
    unicorn_root = Path(behavior.uc.__file__).resolve().parent
    unicorn_files = [path for path in unicorn_root.rglob("*") if path.is_file()]
    paths = [
        Path(__file__).resolve(), NATIVE_SOURCE.resolve(), OPERATIONS_C.resolve(),
        OPERATIONS_H.resolve(), ORIGINAL_SOURCE.resolve(),
        ROOT / "portable/ui_model/windows/registry.h",
        ROOT / "portable/ui_model/windows/window.h",
        ROOT / "portable/game/resources/database.h",
        ROOT / "tools/behavior.py", ROOT / "tools/exe.py", ROOT / "tools/functions.py",
        ROOT / "tools/match.py", ROOT / "tools/modctx.py", ROOT / "tools/modules.py",
        ROOT / "tools/compiler.py", ROOT / "tools/symbols.py", ROOT / "tools/omf.py",
        ROOT / "layout/functions.json", ROOT / "layout/symbols.json",
        ROOT / "layout/manifest.json", ROOT / "layout/oracle.lock.json",
        ROOT / "layout/toolchain.json", ROOT / "docs/behavioral-proof.md",
        ROOT / "assets/SIMANT.EXE", compiler.resolve(), wheel.resolve(),
        *c_closure, *unicorn_files,
    ]
    return sorted(set(path.resolve() for path in paths))


def empty_callback(machine, args):
    del machine, args
    return None


def window_pointer(machine, args):
    wanted = machine.case.metadata["window_id"]
    if len(args) != 1 or args[0] != wanted:
        raise AssertionError(f"f_2505_0006 received {args}, expected window {wanted:#x}")
    return machine.case.metadata["window_off"], machine.case.metadata["window_seg"]


def capture_inversion(machine, args):
    if len(args) != 2:
        raise AssertionError(f"f_1CE2_0430 pointer words differ: {args}")
    address = ((args[1] & 0xffff) << 4) + (args[0] & 0xffff)
    addresses = machine.case.metadata["object_addresses"]
    try:
        index = addresses.index(address)
    except ValueError as exc:
        raise AssertionError(f"inversion pointer {address:#x} is not a fixture object") from exc
    machine.state.setdefault("inversions", []).append({
        "object_index": index,
        "object_id": (machine.case.metadata["window_id"] + index) & 0xffff,
        "pointer_words": [args[0] & 0xffff, args[1] & 0xffff],
    })
    return None


def original_machine():
    return behavior.Machine(OriginalPair())


def make_original_case(groups: tuple[int, ...], types: tuple[int, ...],
                       flags: tuple[int, ...], selected_group: int,
                       visible: int, label: str) -> behavior.Case:
    count = len(groups)
    if not (0 < count <= MAX_OBJECTS and len(types) == count and len(flags) == count):
        raise ValueError("invalid fixture dimensions")
    window_linear = WINDOW_SEG * 16 + WINDOW_OFF
    addresses = [WINDOW_SEG * 16 + OBJECT_BASE_OFF + i * OBJECT_STRIDE
                 for i in range(count)]
    writes: list[tuple[int, bytes]] = []
    window_data = bytearray(0x2c + count * 4)
    struct.pack_into("<H", window_data, 0x0c, count)
    for i, address in enumerate(addresses):
        object_off = OBJECT_BASE_OFF + i * OBJECT_STRIDE
        struct.pack_into("<HH", window_data, 0x2c + i * 4, object_off, WINDOW_SEG)
        object_data = bytearray(0x26)
        object_data[0x20] = groups[i] & 0xff
        object_data[0x21] = types[i] & 0xff
        struct.pack_into("<H", object_data, 0x24, flags[i] & 0xffff)
        writes.append((address, bytes(object_data)))
    writes.insert(0, (window_linear, bytes(window_data)))
    observe = [behavior.Range(f"object_{i}_flags", address + 0x24, 2)
               for i, address in enumerate(addresses)]
    callbacks = {
        "win_LockWin": behavior.Callback(0, empty_callback,
                                           register_args=("ax",)),
        "f_2505_0006": behavior.Callback(1, window_pointer),
        "win_UnlockWin": behavior.Callback(0, empty_callback,
                                             register_args=("ax",)),
        "f_1CE2_0430": behavior.Callback(2, capture_inversion),
    }
    return behavior.Case(
        label=label,
        registers={"ax": WINDOW_ID, "dx": selected_group, "bx": visible},
        writes=writes, observe=observe, callbacks=callbacks, return_kind="void",
        metadata={"window_id": WINDOW_ID, "window_seg": WINDOW_SEG,
                  "window_off": WINDOW_OFF, "object_addresses": addresses,
                  "input_groups": list(groups), "input_types": list(types),
                  "input_flags": list(flags), "selected_group": selected_group,
                  "visible": visible})


def original_result(machine, groups: tuple[int, ...], types: tuple[int, ...],
                    flags: tuple[int, ...], selected_group: int,
                    visible: int, label: str) -> dict[str, object]:
    result = machine.run(make_original_case(groups, types, flags,
                                            selected_group, visible, label))
    final_flags = [int.from_bytes(bytes.fromhex(result["ranges"][f"object_{i}_flags"]),
                                  "little") for i in range(len(groups))]
    inversions = result["state"].get("inversions", [])
    raw_order = [entry["name"] for entry in result["raw_trace"]]
    return {"final_flags": final_flags, "inversions": inversions,
            "callback_order": raw_order,
            "return": result["return"]}


def native_result(run, groups: tuple[int, ...], types: tuple[int, ...],
                  flags: tuple[int, ...], selected_group: int,
                  visible: int) -> dict[str, object]:
    n = len(groups)
    group_array = (ct.c_uint8 * n)(*groups)
    type_array = (ct.c_uint8 * n)(*types)
    flags_array = (ct.c_uint16 * n)(*flags)
    output_flags = (ct.c_uint16 * n)()
    trace = NativeTrace()
    status = run(WINDOW_ID, selected_group, visible, n, group_array,
                 type_array, flags_array, output_flags, ct.byref(trace))
    return {"status": status, "final_flags": list(output_flags),
            "inversions": [{"object_index": (trace.ids[i] - WINDOW_ID) & 0xffff,
                             "object_id": trace.ids[i], "kind": trace.kinds[i]}
                            for i in range(trace.count)]}


def cases():
    for group in PROFILED_GROUPS:
        mismatch_group = (group + 1) & 0xff
        for object_type in TYPES:
            for flags in range(64):
                for visible in (0, 1):
                    for matches in (False, True):
                        object_group = group if matches else mismatch_group
                        yield (f"single/g{group:02x}/t{object_type:02x}/f{flags:02x}/"
                               f"v{visible}/match{int(matches)}",
                               (object_group,), (object_type,), (flags,), group, visible)
    mixed = [
        ("mixed/order-show", (7, 7, 0, 7, 7, 8),
         (1, 5, 13, 17, 6, 255),
         (0x8124, 0xF025, 0x5124, 0x1D24, 0x9E24, 0xA025), 7, 1),
        ("mixed/order-hide", (255, 255, 0, 255, 255, 0),
         (255, 13, 6, 5, 17, 1),
         (0x8025, 0xFC25, 0x5625, 0xA825, 0x7F25, 0xC125), 255, 0),
        ("mixed/unchanged-and-other-group", (0, 0, 7, 0, 0, 7),
         (1, 5, 13, 17, 6, 255),
         (0x8125, 0xFF24, 0xAC25, 0x3F24, 0xEE25, 0xD124), 0, 1),
        ("mixed/all-visible-already", (0, 0, 0, 0, 0, 0),
         (1, 5, 13, 17, 6, 255),
         (0x8125, 0xFF25, 0xAC25, 0x3F25, 0xEE25, 0xD125), 0, 1),
    ]
    yield from mixed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, default=REPORT_DEFAULT)
    args = parser.parse_args()
    report_path = args.report.resolve()
    if report_path.exists():
        print(f"refusing to overwrite report: {report_path}", file=sys.stderr)
        return 2
    report_path.parent.mkdir(parents=True, exist_ok=True)
    compiler_text = os.environ.get("SIMANT_CC") or shutil.which("gcc") or str(GCC_DEFAULT)
    compiler = Path(compiler_text)
    if not compiler.is_file():
        print(f"native compiler not found: {compiler}", file=sys.stderr)
        return 2
    started = time.monotonic()
    c_paths = dependency_closure(compiler)
    wheel = ROOT / "build/behavior/dependencies/unicorn-2.1.4-cp37-abi3-win_amd64.whl"
    input_paths = pinned_input_paths(compiler, c_paths, wheel)
    inputs_before = {input_key(path): sha(path)
                     for path in input_paths}
    native_path, c_closure, command = build_native(compiler)
    library, native_run = native_function(native_path)
    machine = original_machine()
    summaries = []
    mismatches = []
    total = 0
    effect_count = 0
    callback_order_counts: dict[str, int] = {}
    for label, groups, types, flags, selected_group, visible in cases():
        total += 1
        original = original_result(machine, groups, types, flags,
                                   selected_group, visible, label)
        native = native_result(native_run, groups, types, flags,
                               selected_group, visible)
        original_inversions = [{"object_index": e["object_index"],
                                "object_id": e["object_id"], "kind": 0}
                               for e in original["inversions"]]
        equal = (original["return"] is None and native["status"] == 0 and
                 original["final_flags"] == native["final_flags"] and
                 original_inversions == native["inversions"] and
                 original["callback_order"] == (
                     ["win_LockWin", "f_2505_0006"] +
                     ["f_1CE2_0430"] * len(original_inversions) +
                     ["win_UnlockWin"]))
        case_result = {
            "label": label,
            "inputs": {"groups": list(groups), "types": list(types),
                       "flags": list(flags), "selected_group": selected_group,
                       "visible": visible},
            "original": {"final_flags": original["final_flags"],
                         "inversions": original_inversions,
                         "callback_order": original["callback_order"]},
            "native": native,
            "equal": equal,
        }
        summaries.append(case_result)
        effect_count += len(original_inversions)
        callback_key = ",".join(original["callback_order"])
        callback_order_counts[callback_key] = callback_order_counts.get(callback_key, 0) + 1
        if not equal:
            mismatches.append(case_result)

    inputs_after = {input_key(path): sha(path)
                    for path in input_paths}
    inputs_unchanged = inputs_before == inputs_after
    changed_inputs = sorted(path for path in inputs_before
                            if inputs_before[path] != inputs_after[path])
    wheel = ROOT / "build/behavior/dependencies/unicorn-2.1.4-cp37-abi3-win_amd64.whl"
    report = {
        "schema": "portable-object-group-visible-dos-native-v1",
        "status": "PASS" if not mismatches and inputs_unchanged else "FAIL",
        "claim": "Native portable_object_group_visible matches the frozen original DOS win_SetGroupVisibleState for the recorded finite object type, low-six-bit flag, group equality, and target-visibility domain; ordered original f_1CE2_0430 pointers normalize to the same native object IDs.",
        "boundaries": "The original m22BF function executes in the frozen behavior.Machine. win_LockWin, f_2505_0006 and win_UnlockWin are controlled window-structure services; f_1CE2_0430 is captured as a normalized inversion event. No renderer pixels are observed, and this does not claim physical DOS rendering equivalence.",
        "domain": {"single_object_cases": len(PROFILED_GROUPS) * len(TYPES) * 64 * 2 * 2,
                   "mixed_order_cases": 4, "types": list(TYPES),
                   "flags": "all low-six-bit values 0x00..0x3f; additional upper-bit preservation cases",
                   "selected_group_values": list(PROFILED_GROUPS),
                   "matching_and_nonmatching_group": True,
                   "visible_argument_values": [0, 1],
                   "inversion_effect_kinds": {"original": "f_1CE2_0430 object pointer",
                                              "native": "PORTABLE_OBJECT_INVERT"}},
        "case_count": total,
        "mismatch_count": len(mismatches),
        "input_stability": {"unchanged": inputs_unchanged,
                            "changed_paths": changed_inputs,
                            "input_sha256_before": inputs_before,
                            "input_sha256_after": inputs_after},
        "inversion_event_count": effect_count,
        "callback_order_counts": callback_order_counts,
        "case_digest_sha256": digest_object(summaries),
        "mismatches": mismatches,
        "toolchain": {"native_compiler": str(compiler),
                      "native_compiler_sha256": sha(compiler),
                      "native_compiler_version": subprocess.run(
                          [str(compiler), "--version"], text=True,
                          capture_output=True, check=True).stdout.splitlines()[0],
                      "native_flags": command[1:command.index("-o")],
                      "native_dependency_closure": c_closure,
                      "native_probe_sha256": sha(native_path)},
        "original_execution": {
            "oracle_sha256": exe.load().sha256,
            "behavior_harness_sha256": behavior.digest(behavior.HARNESS_SOURCE),
            "unicorn_version": behavior.uc.__version__,
            "unicorn_wheel_sha256": sha(wheel) if wheel.is_file() else None,
            "source_anchor_sha256": sha(ORIGINAL_SOURCE),
            "modeled_services": ["win_LockWin", "f_2505_0006", "win_UnlockWin",
                                  "f_1CE2_0430 capture only"],
        },
        "elapsed_seconds": round(time.monotonic() - started, 3),
    }
    if report_path.exists():
        raise FileExistsError(f"refusing to overwrite report: {report_path}")
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "report": str(report_path),
                      "case_count": total, "mismatch_count": len(mismatches),
                      "inversion_event_count": effect_count,
                      "elapsed_seconds": report["elapsed_seconds"]}, indent=2))
    return 0 if not mismatches and inputs_unchanged else 1


if __name__ == "__main__":
    raise SystemExit(main())
