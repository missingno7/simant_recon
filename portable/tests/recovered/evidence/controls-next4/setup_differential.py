#!/usr/bin/env python3
"""Run original DOS initControls beside native setup using actual HCEGANT data."""
from __future__ import annotations

import ctypes as ct
import hashlib
import importlib.util
import json
import struct
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "tools"))
import behavior  # noqa: E402
import exe  # noqa: E402
import functions  # noqa: E402

WINDOW_EVIDENCE = ROOT / "portable/tests/windows/evidence/differential_window.py"
spec = importlib.util.spec_from_file_location("setup_window_helpers", WINDOW_EVIDENCE)
helpers = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = helpers
spec.loader.exec_module(helpers)
from behavior_suites import lists  # noqa: E402

EVIDENCE = Path(__file__).resolve().parent
NATIVE_SOURCE = EVIDENCE / "setup_native_adapter.c"
NATIVE_LIBRARY = EVIDENCE / "setup_native_adapter.dll"
REPORT_PATH = EVIDENCE / "setup_differential_report.json"
GCC = Path("C:/msys64/mingw64/bin/gcc.exe")

SNAPSHOT_FIELDS = [
    ("knob_size", 2), ("controls", 8), ("mode_level", 3), ("caste_level", 3),
    ("mode_presets", 12), ("caste_presets", 12), ("ideal_caste", 4),
    ("mode_rect", 4), ("caste_rect", 4), ("mode_point", 2), ("caste_point", 2),
    ("mode_triangle_dimensions", 3), ("caste_triangle_dimensions", 3),
]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


PINNED_PATHS = [
    "portable/game/simulation/setup.c", "portable/game/simulation/setup.h",
    "portable/tests/setup/evidence/setup_native_adapter.c",
    "portable/tests/setup/evidence/setup_differential.py",
    "tools/behavior.py", "tools/exe.py", "tools/functions.py", "tools/symbols.py",
    "tools/match.py", "tools/modctx.py", "tools/modules.py", "tools/compiler.py",
    "layout/functions.json", "layout/symbols.json", "assets/SIMANT.EXE",
    "assets/HCEGANT.NDX", "assets/HCEGANT.DAT",
]


def source_pins() -> dict[str, str]:
    return {name: sha((ROOT / name).read_bytes()) for name in PINNED_PATHS}


def build_native() -> str:
    command = [str(GCC), "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
               "-shared", str(NATIVE_SOURCE),
               str(ROOT / "portable/game/simulation/setup.c"),
               str(ROOT / "portable/ui_model/windows/registry.c"),
               str(ROOT / "portable/ui_model/windows/window.c"),
               str(ROOT / "portable/game/resources/database.c"),
               str(ROOT / "portable/render/bitmap.c"),
               str(ROOT / "portable/render/primitives.c"),
               "-o", str(NATIVE_LIBRARY)]
    subprocess.run(command, check=True, cwd=ROOT)
    return sha(NATIVE_LIBRARY.read_bytes())


def configure_native():
    lib = ct.CDLL(str(NATIVE_LIBRARY))
    lib.setup_native_init.argtypes = [ct.c_char_p, ct.c_int16]
    lib.setup_native_init.restype = ct.c_int
    lib.setup_native_snapshot.argtypes = [ct.POINTER(ct.c_int32), ct.c_size_t]
    lib.setup_native_snapshot.restype = ct.c_size_t
    lib.setup_native_event_count.argtypes = []
    lib.setup_native_event_count.restype = ct.c_size_t
    lib.setup_native_event.argtypes = [ct.c_size_t]
    lib.setup_native_event.restype = ct.c_int
    lib.setup_native_close.argtypes = []
    lib.setup_native_close.restype = None
    return lib


class OriginalOnlyPair:
    function = functions.get("win_Recalc")
    vectors = {exe.MANAGER_SEG * 16 + v.offset: v for v in exe.load().vectors}
    delegate = {}
    candidate_entries = {}
    sequence_targets = set()

    @staticmethod
    def sequence_function(name):
        return functions.get(name)


def dual_window_fixture():
    profile, _ = helpers.resource_payload("HCEGANT", 0, 9)
    payloads = {18: helpers.resource_payload("HCEGANT", 18, 0)[0],
                19: helpers.resource_payload("HCEGANT", 19, 0)[0]}
    text = b"setup-fixture"
    text_paras = (len(text) + 47) // 16
    win18_paras = (len(payloads[18]) + 47) // 16
    win19_paras = (len(payloads[19]) + 47) // 16
    free_paras = helpers.memory_fixture.HEAP_PARAS - text_paras - win18_paras - win19_paras
    if free_paras <= 0:
        raise RuntimeError("insufficient fixture heap capacity")
    old_heap_seg, old_heap_paras = (helpers.memory_fixture.HEAP_SEG,
                                   helpers.memory_fixture.HEAP_PARAS)
    helpers.memory_fixture.HEAP_SEG = lists.DATA[1] - 2
    helpers.memory_fixture.HEAP_PARAS = 0x100
    try:
        arena = helpers.memory_fixture.heap_case(
            "setup/initControls/two-loaded-windows",
        [(text_paras, 0, {"size": len(text), "name": b"fixture-text"}),
         (win18_paras, 1, {"size": len(payloads[18]), "name": b"window-18"}),
         (win19_paras, 1, {"size": len(payloads[19]), "name": b"window-19"}),
         (free_paras, 0x80, {"name": b"free-tail"})],
        handles=[0, 1, 2],
            contract="actual startup kind-0 records in a valid original Ralloc arena")
    finally:
        helpers.memory_fixture.HEAP_SEG = old_heap_seg
        helpers.memory_fixture.HEAP_PARAS = old_heap_paras

    win18_seg = lists.DATA[1] + text_paras
    win19_seg = lists.DATA[1] + text_paras + win18_paras
    offsets = bytearray(struct.pack("<4h", -32768, -32768, -32768, -32768) * 45)
    offsets[:len(profile)] = profile
    handle_seg = lists.HANDLE[1]
    handle_slot_18 = lists.HANDLE[0] - 4
    handle_slot_19 = lists.HANDLE[0] - 8
    writes = list(arena.writes)
    writes += [(win18_seg * 16, payloads[18]), (win19_seg * 16, payloads[19]),
               (helpers.behavior.symbol_address("win_handles") + 18 * 4,
                helpers.behavior.words(handle_slot_18, handle_seg)),
               (helpers.behavior.symbol_address("win_numOfWindows"),
                helpers.behavior.words(45)),
               (helpers.behavior.symbol_address("win_offsets"), bytes(offsets)),
               (helpers.behavior.symbol_address("g_5702"),
                helpers.behavior.words(*([0x8000] * 32))),
               (helpers.behavior.symbol_address("g_6300"), helpers.behavior.words(0))]
    return {"writes": writes, "payloads": payloads, "profile": profile,
            "win18_seg": win18_seg, "win19_seg": win19_seg,
            "handles": {18: (handle_slot_18, handle_seg),
                        19: (handle_slot_19, handle_seg)},
            "root": helpers.memory_fixture.HEAP_SEG}


def read_words(machine, name, count, *, signed=False):
    address = behavior.symbol_address(name)
    fmt = "<" + ("h" if signed else "H") * count
    return list(struct.unpack(fmt, machine.read(address, count * 2)))


def read_dword(machine, name, *, signed=False):
    value = int.from_bytes(machine.read(behavior.symbol_address(name), 4), "little")
    if signed and value >= 0x80000000:
        value -= 0x100000000
    return value


def read_object_rect(machine, base_seg: int, index: int):
    window_base = base_seg * 16
    off, seg = struct.unpack("<HH", machine.read(window_base + 0x2c + 4 * index, 4))
    return list(struct.unpack("<4h", machine.read(seg * 16 + off, 8)))


def original_run():
    pair = OriginalOnlyPair()
    machine = behavior.Machine(pair)
    fixture = dual_window_fixture()
    machine.run(behavior.Case("setup/LockInit", return_kind="void"),
                function="win_LockInit")
    for address, data in fixture["writes"]:
        machine.write(address, data)

    for window_index, window_id in enumerate((18, 19)):
        offset, segment = fixture["handles"][window_id]
        if window_index == 1:
            machine.write(behavior.symbol_address("win_handles") + 19 * 4,
                          behavior.words(fixture["handles"][19][0],
                                         fixture["handles"][19][1]))

        def resource_service(vm, args, expected=window_id,
                             result=(offset, segment)):
            if args != [expected, 0, 1]:
                raise AssertionError(f"unexpected resource provider call: {args}")
            vm.state.setdefault("window_resource_requests", []).append(args)
            return result

        load_case = behavior.Case(
            f"setup/LoadWindow/{window_id:02x}",
            args=[window_id << 8], callbacks={
                "f_1A53_00F0": behavior.Callback(3, resource_service)},
            return_kind="void")
        machine.run(load_case, preserve=True, function="win_LoadWindow")

    close_events = []

    def resource_size_service(vm, args):
        if args[2] != 0x578:
            raise AssertionError(f"unexpected DOS size query: {args}")
        data, flags = helpers.resource_payload("HCEGANT", args[2], 2)
        if flags != 8 or len(data) < 12 or struct.unpack_from("<h", data, 0)[0] not in (0, 3):
            raise AssertionError("knob resource is not an ordinary measured bitmap")
        width, height = struct.unpack_from("<HH", data, 8)
        vm.write(args[1] * 16 + args[0], struct.pack("<hh", width, height))
        vm.state["knob_size_source"] = {"object_id": args[2], "kind": 2,
                                        "flags": flags, "record_sha256": sha(data),
                                        "width": width, "height": height}
        return 1

    def closed_service(name):
        def handler(vm, args):
            handle_name = "fd_50F6_37F6" if name == "mode" else "fd_50F6_37F2"
            pointer = vm.read(behavior.symbol_address(handle_name), 4)
            if pointer != b"\0\0\0\0":
                raise AssertionError(f"{name} animation handle was unexpectedly live")
            close_events.append(name)
        return handler

    callbacks = {
        "f_208F_0419": behavior.Callback(3, resource_size_service),
        "win_ModeControlClosed": behavior.Callback(0, closed_service("mode")),
        "win_CasteControlClosed": behavior.Callback(0, closed_service("caste")),
    }
    init_case = behavior.Case("setup/initControls/direct-original",
                              callbacks=callbacks, return_kind="void",
                              observe_at_calls=False)
    init_observation = machine.run(init_case, preserve=True, function="initControls")

    rects = {"mode": read_object_rect(machine, fixture["win18_seg"], 13),
             "caste": read_object_rect(machine, fixture["win19_seg"], 13)}
    source = {
        "knob_size": read_words(machine, "knobSize", 2),
        "controls": [read_words(machine, "ModeAuto", 1)[0],
                     read_words(machine, "CasteAuto", 1)[0],
                     read_words(machine, "fd_50F6_0468", 1)[0],
                     read_words(machine, "fd_3D57_07EA", 1)[0], 0, 0,
                     read_words(machine, "fd_50F6_0370", 1, signed=True)[0],
                     read_words(machine, "fd_50F6_024E", 1, signed=True)[0]],
        "mode_level": read_words(machine, "modeLevels", 3),
        "caste_level": read_words(machine, "casteLevels", 3),
        "mode_presets": read_words(machine, "fd_3D57_0810", 12),
        "caste_presets": read_words(machine, "fd_3D57_07F2", 12),
        "ideal_caste": read_words(machine, "IdealCaste", 4),
        "mode_rect": rects["mode"], "caste_rect": rects["caste"],
        "mode_point": read_words(machine, "fd_50F6_0358", 2, signed=True),
        "caste_point": read_words(machine, "fd_50F6_022E", 2, signed=True),
        "mode_triangle_dimensions": [
            rects["mode"][2] - rects["mode"][0],
            rects["mode"][3] - rects["mode"][1],
            ((rects["mode"][2] - rects["mode"][0]) >> 1) * 256 //
            (rects["mode"][3] - rects["mode"][1])],
        "caste_triangle_dimensions": [
            read_words(machine, "triWidth", 1)[0],
            read_words(machine, "triHeight", 1)[0],
            read_dword(machine, "fd_50F6_382E", signed=True)],
        "mode_triangle_points": read_words(machine, "fd_50F6_3816", 6, signed=True),
        "caste_triangle_points": read_words(machine, "fd_50F6_3822", 6, signed=True),
        "resource_size_calls": machine.state.get("knob_size_source"),
        "window_resource_requests": machine.state.get("window_resource_requests", []),
        "closed_ui_calls": close_events,
        "raw_callback_trace": init_observation["raw_trace"]
    }
    return source, machine, fixture


def native_run():
    library_hash = build_native()
    lib = configure_native()
    root = str(ROOT / "assets" / "HCEGANT").encode("utf-8")
    status = lib.setup_native_init(root, 0)
    if status != 0:
        raise RuntimeError(f"native setup init failed: {status}")
    try:
        values = (ct.c_int32 * 128)()
        count = lib.setup_native_snapshot(values, len(values))
        flat = list(values[:count])
        if count != 62:
            raise RuntimeError(f"unexpected native snapshot size {count}")
        at = 0
        result = {}
        for name, size in SNAPSHOT_FIELDS:
            result[name] = flat[at:at + size]
            at += size
        events = [lib.setup_native_event(i) for i in range(lib.setup_native_event_count())]
        result["events"] = events
        return result, library_hash
    finally:
        lib.setup_native_close()


def run():
    pins_before = source_pins()
    native, native_hash = native_run()
    source, machine, fixture = original_run()
    pins_after = source_pins()

    mapping = {
        "knob_size": source["knob_size"], "controls": source["controls"],
        "mode_level": source["mode_level"], "caste_level": source["caste_level"],
        "mode_presets": source["mode_presets"], "caste_presets": source["caste_presets"],
        "ideal_caste": source["ideal_caste"], "mode_rect": source["mode_rect"],
        "caste_rect": source["caste_rect"], "mode_point": source["mode_point"],
        "caste_point": source["caste_point"],
        "mode_triangle_dimensions": source["mode_triangle_dimensions"],
        "caste_triangle_dimensions": source["caste_triangle_dimensions"],
    }
    diffs = {key: {"native": native[key], "original": original}
             for key, original in mapping.items() if native[key] != original}
    native_events = native["events"]
    expected_native_events = [0x10000 | (0x578 << 8) | 2,
                              0x20000 | 0x120d, 0x20000 | 0x120d,
                              0x30000 | 0,
                              0x20000 | 0x130d, 0x30000 | 1]
    if native_events != expected_native_events:
        diffs["native_events"] = {"native": native_events,
                                   "expected": expected_native_events}
    if pins_before != pins_after:
        diffs["source_pins"] = {"before": pins_before, "after": pins_after}

    report = {
        "schema": "portable-init-controls-dos-differential-v1",
        "original_oracle_sha256": exe.load().sha256,
        "machine_harness_sha256": behavior.digest(behavior.HARNESS_SOURCE),
        "original_initControls_address": {
            k: functions.get("initControls")[k]
            for k in ("unit", "seg", "off", "size", "name")},
        "native_adapter_sha256": sha(NATIVE_SOURCE.read_bytes()),
        "native_library_sha256": native_hash,
        "database_ndx_sha256": sha((ROOT / "assets/HCEGANT.NDX").read_bytes()),
        "database_dat_sha256": sha((ROOT / "assets/HCEGANT.DAT").read_bytes()),
        "window_fixture": {
            "window18_payload_sha256": sha(fixture["payloads"][18]),
            "window19_payload_sha256": sha(fixture["payloads"][19]),
            "profile0_sha256": sha(fixture["profile"]),
            "mode_rect_0x120d": source["mode_rect"],
            "caste_rect_0x130d": source["caste_rect"],
            "loaded_records": [18, 19],
        },
        "source_pins_before": pins_before,
        "source_pins_after": pins_after,
        "source_pins_stable": pins_before == pins_after,
        "knob_resource": source["resource_size_calls"],
        "source_query_order": ["resource size 0x578 kind2", "unused rect 0x120d",
                                "mode rect 0x120d", "caste rect 0x130d"],
        "native_callback_events": native_events,
        "original_render_close_callbacks": source["closed_ui_calls"],
        "original_machine_callbacks": source["raw_callback_trace"],
        "native_snapshot": native,
        "original_snapshot": source,
        "mismatches": diffs,
        "mismatch_count": len(diffs),
        "boundaries": (
            "The frozen original initControls, win_LoadWindow, win_GetObjRect, "
            "InitTriVars, win_ModeControlChanged, win_CasteControlChanged, "
            "SetTriLatPoint, and cvtLevels2IdealCaste execute in behavior.Machine. "
            "The DOS f_208F_0419 resource-size boundary is supplied from the actual "
            "HCEGANT 0x578 kind-2 bitmap header; animation-close services are "
            "captured only when source state would call them. Native setup uses the "
            "actual window registry and bitmap decoder; it does not call SDL."
        )
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    report = run()
    print(json.dumps({"report": str(REPORT_PATH),
                      "mismatch_count": report["mismatch_count"],
                      "mismatches": report["mismatches"],
                      "window_fixture": report["window_fixture"],
                      "knob_resource": report["knob_resource"],
                      "native_events": report["native_callback_events"],
                      "original_callbacks": report["original_machine_callbacks"]}, indent=2))
    if report["mismatch_count"]:
        raise SystemExit(1)
