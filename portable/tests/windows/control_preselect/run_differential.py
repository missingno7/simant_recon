#!/usr/bin/env python3
"""Finite DOS/native proof for the type-1 common-control preselection path."""
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
HERE = PORT / "tests/windows/control_preselect"
TOOLS = ROOT / "tools"
OBJECT_ID = 0x1200
EVENT_SEG = 0x6000
EVENT_OFF = 0x0200
OBJECT_SEG = 0x6000
OBJECT_OFF = 0x1000
MAX_EVENTS = 8
EVENT_CLIP_PUSH = 1
EVENT_TOP_WINDOW_CLIP = 2
EVENT_SET_SELECTED = 3
EVENT_WAIT_TICKS = 4
EVENT_CLIP_POP = 5
STATUS_OK = 0
STATUS_INVALID_ARGUMENT = 1
STATUS_OUT_OF_RANGE = 2
STATUS_NOT_LOADED = 3
STATUS_UNSUPPORTED_TYPE = 4
STATUS_CALLBACK_REJECTED = 5

sys.path.insert(0, str(TOOLS))
sys.path.insert(0, str(ROOT / "build/behavior/deps"))
import behavior  # noqa: E402
import exe  # noqa: E402
import functions  # noqa: E402
import match  # noqa: E402

ORIGINAL_SOURCE = ROOT / "src/root/m218D.c"
NATIVE_SOURCE = HERE / "native_probe.c"
PROVIDER_C = PORT / "ui_model/windows/control_preselect.c"
PROVIDER_H = PORT / "ui_model/windows/control_preselect.h"
REGISTRY_H = PORT / "ui_model/windows/registry.h"
WINDOW_H = PORT / "ui_model/windows/window.h"
REPORT_DEFAULT = HERE / "evidence/control-preselect-dos-native-final-20261002.json"
BUILD = ROOT / "build/portable/tests/windows/control-preselect"
GCC_DEFAULT = Path("C:/msys64/mingw64/bin/gcc.exe")


class NativeEvent(ct.Structure):
    _fields_ = [("kind", ct.c_uint16), ("object_id", ct.c_uint16),
                ("value", ct.c_uint16)]


class NativeTrace(ct.Structure):
    _fields_ = [("count", ct.c_uint16),
                ("events", NativeEvent * MAX_EVENTS),
                ("callback_count", ct.c_uint16)]


class OriginalPair:
    function = functions.get("f_218D_000C")
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
    found: set[Path] = set()
    for source in (NATIVE_SOURCE, PROVIDER_C):
        proc = subprocess.run([str(compiler), "-std=c11", "-MM", f"-I{ROOT}",
                               f"-I{PORT}", str(source)], cwd=ROOT,
                              text=True, capture_output=True, check=True, timeout=15)
        dependencies = proc.stdout.split(":", 1)[1].replace("\\\r\n", " ").replace("\\\n", " ")
        for token in dependencies.split():
            path = Path(token)
            if not path.is_absolute(): path = ROOT / path
            path = path.resolve()
            if path.is_relative_to(ROOT): found.add(path)
        found.add(source.resolve())
    return sorted(found)


def build_native(compiler: Path) -> tuple[Path, dict[str, str], list[str]]:
    BUILD.mkdir(parents=True, exist_ok=True)
    output = BUILD / "control-preselect-probe.dll"
    closure = dependency_closure(compiler)
    command = [str(compiler), "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
               "-shared", f"-I{ROOT}", f"-I{PORT}", str(NATIVE_SOURCE),
               str(PROVIDER_C), "-o", str(output)]
    subprocess.run(command, cwd=ROOT, check=True, timeout=30)
    return output, {input_key(path): sha(path) for path in closure}, command


def native_function(path: Path):
    library = ct.CDLL(str(path))
    run = library.control_preselect_native_run
    run.argtypes = [ct.c_uint16, ct.c_uint8, ct.c_uint16, ct.c_int, ct.c_int,
                    ct.c_uint16, ct.c_uint16, ct.POINTER(ct.c_uint16),
                    ct.POINTER(NativeTrace)]
    run.restype = ct.c_int
    return library, run


def pinned_input_paths(compiler: Path, c_closure: list[Path], wheel: Path) -> list[Path]:
    unicorn_root = Path(behavior.uc.__file__).resolve().parent
    unicorn_files = [path for path in unicorn_root.rglob("*") if path.is_file()]
    paths = [
        Path(__file__).resolve(), NATIVE_SOURCE.resolve(), PROVIDER_C.resolve(),
        PROVIDER_H.resolve(), ORIGINAL_SOURCE.resolve(), REGISTRY_H.resolve(),
        WINDOW_H.resolve(), ROOT / "tools/behavior.py", ROOT / "tools/exe.py",
        ROOT / "tools/functions.py", ROOT / "tools/match.py", ROOT / "tools/modctx.py",
        ROOT / "tools/modules.py", ROOT / "tools/compiler.py", ROOT / "tools/symbols.py",
        ROOT / "tools/omf.py", ROOT / "layout/functions.json",
        ROOT / "layout/symbols.json", ROOT / "layout/manifest.json",
        ROOT / "layout/oracle.lock.json", ROOT / "layout/toolchain.json",
        ROOT / "docs/behavioral-proof.md", ROOT / "assets/SIMANT.EXE",
        compiler.resolve(), wheel.resolve(), *c_closure, *unicorn_files,
    ]
    return sorted(set(path.resolve() for path in paths))


def event_address(name: str) -> int:
    symbols = match.symbols()
    symbol = symbols.get(name, symbols.get("_" + name))
    if symbol is None: raise KeyError(name)
    return symbol["seg"] * 16 + symbol["off"]


def callback_append(machine, key: str, item: list[object]) -> None:
    machine.state[key].append(item)


def require_registers(args: list[int], expected: list[int], name: str) -> None:
    if args != expected:
        raise AssertionError(f"{name} args {args} != {expected}")


def make_original_case(flags: int, label: str) -> behavior.Case:
    event_linear = EVENT_SEG * 16 + EVENT_OFF
    object_linear = OBJECT_SEG * 16 + OBJECT_OFF
    event = bytearray(16)
    struct.pack_into("<H", event, 0x0c, OBJECT_ID)
    obj = bytearray(0x26)
    obj[0x21] = 1
    struct.pack_into("<H", obj, 0x24, flags)
    # Different codes deliberately keep the double-click comparison outside
    # this control-handler contract; TickCount remains a controlled service.
    previous_event = bytearray(16)
    struct.pack_into("<H", previous_event, 0x0c, 0x3300)
    event_address_now = event_address("fd_50F6_49FA")
    event_address_previous = event_address("fd_50F6_4A0A")
    callbacks = {
        "win_LockWin": behavior.Callback(0, lambda m, a: require_registers(
            a, [OBJECT_ID], "win_LockWin"), register_args=("ax",)),
        "win_ObjAddr": behavior.Callback(0, win_obj_addr,
                                         register_args=("ax",)),
        "clip_Push": behavior.Callback(0, lambda m, a: callback_append(
            m, "control_trace", [EVENT_CLIP_PUSH, 0, 0])),
        "f_1E57_0351": behavior.Callback(0, lambda m, a: callback_append(
            m, "control_trace", [EVENT_TOP_WINDOW_CLIP, 0, 0])),
        "win_SetObjSelectedState": behavior.Callback(0, lambda m, a: set_selected_handler(m, a),
                                                       register_args=("ax", "dx")),
        "f_208F_0530": behavior.Callback(1, lambda m, a: wait_handler(m, a)),
        "clip_Pop": behavior.Callback(0, lambda m, a: callback_append(
            m, "control_trace", [EVENT_CLIP_POP, 0, 0])),
        "TickCount": behavior.Callback(0, tick_handler),
        "win_UnlockWin": behavior.Callback(0, lambda m, a: require_registers(
            a, [OBJECT_ID], "win_UnlockWin"), register_args=("ax",)),
    }
    return behavior.Case(
        label=label, args=[EVENT_OFF, EVENT_SEG],
        writes=[(event_linear, bytes(event)), (object_linear, bytes(obj)),
                (event_address_now, bytes(event)),
                (event_address_previous, bytes(previous_event))],
        observe=[behavior.Range("object_flags", object_linear + 0x24, 2)],
        callbacks=callbacks, return_kind="void",
        callee_pop=4,
        state={"control_trace": [], "tick_calls": 0},
        metadata={"object_id": OBJECT_ID, "object_seg": OBJECT_SEG,
                  "object_off": OBJECT_OFF, "object_linear": object_linear,
                  "event_seg": EVENT_SEG, "event_off": EVENT_OFF,
                  "event_linear": event_linear, "flags": flags,
                  "tick_name": "TickCount"})


def win_obj_addr(machine, args):
    require_registers(args, [OBJECT_ID], "win_ObjAddr")
    return OBJECT_OFF, OBJECT_SEG


def set_selected_handler(machine, args):
    require_registers(args, [OBJECT_ID, args[1] if len(args) == 2 else -1],
                      "win_SetObjSelectedState")
    if len(args) != 2 or args[1] not in (0, 1):
        raise AssertionError(f"invalid selection args: {args}")
    callback_append(machine, "control_trace", [EVENT_SET_SELECTED, args[0], args[1]])
    address = machine.case.metadata["object_linear"] + 0x24
    flags = machine.word(address)
    machine.set_word(address, (flags & ~4) | (4 if args[1] else 0))


def wait_handler(machine, args):
    if args != [5]: raise AssertionError(f"f_208F_0530 args {args}, expected [5]")
    callback_append(machine, "control_trace", [EVENT_WAIT_TICKS, 0, args[0]])


def tick_handler(machine, args):
    del args
    machine.state["tick_calls"] += 1
    return 0, 0


def original_result(machine, flags: int, label: str) -> dict[str, object]:
    result = machine.run(make_original_case(flags, label))
    final_flags = int.from_bytes(bytes.fromhex(result["ranges"]["object_flags"]), "little")
    return {"final_flags": final_flags, "events": result["state"]["control_trace"],
            "tick_calls": result["state"]["tick_calls"],
            "raw_order": [entry["name"] for entry in result["raw_trace"]],
            "return": result["return"]}


def native_result(run, flags: int, *, object_id: int = OBJECT_ID, type_: int = 1,
                  initialized: int = 1, loaded: int = 1, reject_nth: int = 0,
                  missing_mask: int = 0) -> dict[str, object]:
    final_flags = ct.c_uint16()
    trace = NativeTrace()
    status = run(object_id, type_, flags, initialized, loaded, reject_nth,
                 missing_mask, ct.byref(final_flags), ct.byref(trace))
    events = [[trace.events[i].kind, trace.events[i].object_id,
               trace.events[i].value] for i in range(trace.count)]
    return {"status": status, "final_flags": final_flags.value,
            "events": events, "callback_count": trace.callback_count}


def expected_events(flags: int) -> list[list[int]]:
    events = [[EVENT_CLIP_PUSH, 0, 0], [EVENT_TOP_WINDOW_CLIP, 0, 0]]
    current = flags
    if flags & 8:
        if not (flags & 0x20 and flags & 0x400 and flags & 4):
            selected = int(not (current & 4))
            events.append([EVENT_SET_SELECTED, OBJECT_ID, selected])
    elif flags & 1:
        selected = int(not (current & 4))
        events.append([EVENT_SET_SELECTED, OBJECT_ID, selected])
        current = (current & ~4) | (4 if selected else 0)
        events.append([EVENT_WAIT_TICKS, 0, 5])
        selected = int(not (current & 4))
        events.append([EVENT_SET_SELECTED, OBJECT_ID, selected])
    events.append([EVENT_CLIP_POP, 0, 0])
    return events


def expected_flags(flags: int) -> int:
    current = flags
    if not (flags & 0x800): return flags
    if flags & 8:
        if not (flags & 0x20 and flags & 0x400 and flags & 4):
            current = (current & ~4) | (0 if current & 4 else 4)
    elif flags & 1:
        current = (current & ~4) | (0 if current & 4 else 4)
        current = (current & ~4) | (0 if current & 4 else 4)
    return current


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
    inputs_before = {input_key(path): sha(path) for path in input_paths}
    native_path, c_closure, command = build_native(compiler)
    library, native_run = native_function(native_path)
    del library
    machine = behavior.Machine(OriginalPair())
    mismatches = []
    case_digest_rows = []
    event_count = 0
    raw_order_counts: dict[str, int] = {}

    for flags in range(0x10000):
        label = f"type1/flags-{flags:04x}"
        original = original_result(machine, flags, label)
        native = native_result(native_run, flags)
        exp_events = expected_events(flags) if flags & 0x800 else []
        exp_flags = expected_flags(flags)
        equal = (original["return"] is None and original["final_flags"] == exp_flags and
                 native["status"] == STATUS_OK and native["final_flags"] == exp_flags and
                 original["events"] == exp_events and native["events"] == exp_events and
                 original["tick_calls"] == 1 and
                 original["raw_order"][0:2] == ["win_LockWin", "win_ObjAddr"] and
                 original["raw_order"][-2:] == ["TickCount", "win_UnlockWin"])
        if not equal:
            mismatches.append({"label": label, "flags": flags,
                               "original": original, "native": native,
                               "expected_flags": exp_flags,
                               "expected_events": exp_events})
        event_count += len(exp_events)
        key = ",".join(str(event[0]) for event in exp_events)
        raw_order_counts[key] = raw_order_counts.get(key, 0) + 1
        case_digest_rows.append([flags, original["final_flags"], native["final_flags"],
                                 original["events"], native["events"], equal])

    # Explicitly reject frame/slider and all other custom object-handler types
    # without pretending their DOS handler effects belong to this boundary.
    unsupported_types = [0, 4, 5, 6, 7, 8, 12, 13, 17, 18, 255]
    unsupported = []
    for type_ in unsupported_types:
        native = native_result(native_run, 0x0800 | 1, type_=type_)
        ok = native["status"] == STATUS_UNSUPPORTED_TYPE and native["events"] == []
        unsupported.append({"type": type_, "result": native, "passed": ok})
        if not ok: mismatches.append({"unsupported_type": type_, "native": native})

    fault_cases = [
        ("uninitialized", dict(initialized=0), STATUS_INVALID_ARGUMENT),
        ("unloaded", dict(loaded=0), STATUS_NOT_LOADED),
        ("object-out-of-range", dict(object_id=0x1201), STATUS_OUT_OF_RANGE),
        ("window-slot-out-of-range", dict(object_id=0x2D00), STATUS_OUT_OF_RANGE),
        ("missing-required-callback", dict(missing_mask=0x04), STATUS_INVALID_ARGUMENT),
        ("reject-clip-push", dict(reject_nth=1), STATUS_CALLBACK_REJECTED),
        ("reject-top-clip-restores", dict(reject_nth=2), STATUS_CALLBACK_REJECTED),
        ("reject-first-selection-restores", dict(reject_nth=3), STATUS_CALLBACK_REJECTED),
        ("reject-wait-restores", dict(reject_nth=4), STATUS_CALLBACK_REJECTED),
        ("reject-second-selection-restores", dict(reject_nth=5), STATUS_CALLBACK_REJECTED),
        ("reject-clip-pop", dict(reject_nth=6), STATUS_CALLBACK_REJECTED),
    ]
    fault_results = []
    for label, kwargs, expected_status in fault_cases:
        native = native_result(native_run, 0x0801, **kwargs)
        passed = native["status"] == expected_status
        fault_results.append({"label": label, "expected_status": expected_status,
                              "result": native, "passed": passed})
        if not passed: mismatches.append({"fault": label, "native": native})

    inputs_after = {input_key(path): sha(path) for path in input_paths}
    inputs_unchanged = inputs_before == inputs_after
    changed_inputs = sorted(key for key in inputs_before
                            if inputs_before[key] != inputs_after[key])
    report = {
        "schema": "portable-control-preselect-dos-native-v1",
        "status": "PASS" if not mismatches and inputs_unchanged else "FAIL",
        "claim": "For the finite type-1 loaded-control domain, native portable_control_preselect matches original root:m218D f_218D_000C final flags and the ordered clip/top-clip/selection/wait callbacks. Every 16-bit object flag value is covered.",
        "boundaries": "The original function and its type-1 common-control path execute in frozen behavior.Machine. win_LockWin, win_ObjAddr, win_SetObjSelectedState, TickCount, and win_UnlockWin are controlled state/window services; clip_Push, f_1E57_0351, f_208F_0530, and clip_Pop are captured typed host effects. Double-click bookkeeping is excluded from the claim. Unsupported frame/slider/custom handlers are checked for explicit native rejection, not treated as paired behavior. No pixels are observed.",
        "domain": {"type1_flags": "all 0x0000..0xffff", "paired_case_count": 65536,
                   "unsupported_types_rejected": unsupported_types,
                   "unsupported_flag_fixture": "0x0801", "callback_fault_cases": len(fault_cases)},
        "case_count": 65536,
        "mismatch_count": len(mismatches),
        "input_stability": {"unchanged": inputs_unchanged,
                            "changed_paths": changed_inputs,
                            "input_sha256_before": inputs_before,
                            "input_sha256_after": inputs_after},
        "control_event_count": event_count,
        "control_event_order_counts": raw_order_counts,
        "case_digest_sha256": digest_object(case_digest_rows),
        "unsupported_type_checks": unsupported,
        "provider_fault_checks": fault_results,
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
            "modeled_services": ["win_LockWin", "win_ObjAddr", "win_SetObjSelectedState",
                                  "TickCount", "win_UnlockWin"],
        },
        "elapsed_seconds": round(time.monotonic() - started, 3),
    }
    if report_path.exists():
        raise FileExistsError(f"refusing to overwrite report: {report_path}")
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "report": str(report_path),
                      "case_count": report["case_count"],
                      "mismatch_count": report["mismatch_count"],
                      "control_event_count": event_count,
                      "elapsed_seconds": report["elapsed_seconds"]}, indent=2))
    return 0 if not mismatches and inputs_unchanged else 1


if __name__ == "__main__":
    raise SystemExit(main())
