#!/usr/bin/env python3
"""Compare the native window model with frozen original DOS window helpers."""
from __future__ import annotations

import argparse
import ctypes as ct
import hashlib
import importlib.util
import json
import struct
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[4]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))
import behavior  # noqa: E402
import exe  # noqa: E402
import functions  # noqa: E402
import match  # noqa: E402

MEMORY_FIXTURE = ROOT / "tools/behavior_suites/archive/window-memory-fixture-dda4f6dd.py"
spec = importlib.util.spec_from_file_location("window_memory_fixture", MEMORY_FIXTURE)
memory_fixture = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = memory_fixture
spec.loader.exec_module(memory_fixture)

from behavior_suites import lists  # noqa: E402

HERE = Path(__file__).resolve().parent
ADAPTER_SOURCE = HERE / "native_window_adapter.c"
NATIVE_LIBRARY = HERE / "native_window_adapter.dll"
REPORT_PATH = HERE / "differential_window_report.json"
GCC = Path("C:/msys64/mingw64/bin/gcc.exe")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def resource_payload(database: str, resource_id: int, kind: int) -> tuple[bytes, int]:
    index = (ROOT / "assets" / f"{database}.NDX").read_bytes()
    data = (ROOT / "assets" / f"{database}.DAT").read_bytes()
    count = struct.unpack_from("<H", index, 0)[0]
    found = []
    for i in range(count):
        offset, object_id, object_kind, flags = struct.unpack_from("<IhBB", index, 20 + 8 * i)
        if object_id == resource_id and object_kind == kind:
            found.append((offset, flags))
    if len(found) != 1:
        raise RuntimeError(f"expected one {database} id={resource_id:#x} kind={kind} record")
    offset, flags = found[0]
    if flags != 8:
        raise RuntimeError(f"resource {resource_id:#x}/{kind} is not raw DOS resource data: {flags:#x}")
    header_at = 14 + offset
    stored_size = struct.unpack_from("<H", data, header_at + 6)[0]
    payload = data[header_at + 10:header_at + 10 + stored_size]
    if len(payload) != stored_size:
        raise RuntimeError("resource payload truncated")
    return payload, flags


def with_raw_rect_poison(payload: bytes, poison: int) -> bytes:
    result = bytearray(payload)
    count = struct.unpack_from("<H", result, 0x0c)[0]
    for i in range(count):
        offset = struct.unpack_from("<H", result, 0x2c + i * 4)[0]
        values = [((poison + i * 977 + axis * 7919) & 0xffff) for axis in range(4)]
        struct.pack_into("<4H", result, offset, *values)
    return bytes(result)


def with_valid_offset_shift(payload: bytes, shift: int) -> bytes:
    """Translate every object by an in-window delta without changing links."""
    result = bytearray(payload)
    count = struct.unpack_from("<H", result, 0x0c)[0]
    for i in range(count):
        offset = struct.unpack_from("<H", result, 0x2c + i * 4)[0]
        left, top, right, bottom = struct.unpack_from("<4h", result, offset + 8)
        if i == 0:
            left = max(0, min(180, left + shift))
            top = max(0, min(90, top + shift))
        else:
            left = max(-20, min(322, left + shift))
            top = max(-20, min(258, top + shift))
        struct.pack_into("<4h", result, offset + 8, left, top, right, bottom)
    return bytes(result)


def build_native_library() -> str:
    command = [str(GCC), "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror", "-shared",
               str(ADAPTER_SOURCE), str(ROOT / "portable/ui_model/windows/window.c"),
               str(ROOT / "portable/game/resources/database.c"), "-o", str(NATIVE_LIBRARY)]
    subprocess.run(command, check=True, cwd=ROOT)
    return sha(NATIVE_LIBRARY.read_bytes())


def configure_native(path: Path):
    library = ct.CDLL(str(path))
    library.native_window_prepare.argtypes = [ct.c_int16, ct.POINTER(ct.c_uint8), ct.c_size_t]
    library.native_window_prepare.restype = ct.c_int
    library.native_window_profile.argtypes = [ct.POINTER(ct.c_uint8), ct.c_size_t]
    library.native_window_profile.restype = ct.c_int
    library.native_window_recalculate.argtypes = []
    library.native_window_recalculate.restype = ct.c_int
    library.native_window_count.argtypes = []
    library.native_window_count.restype = ct.c_int
    library.native_window_object.argtypes = [ct.c_int, ct.POINTER(ct.c_int16), ct.POINTER(ct.c_uint16)]
    library.native_window_object.restype = ct.c_int
    library.native_window_rect.argtypes = [ct.POINTER(ct.c_int16)]
    library.native_window_rect.restype = ct.c_int
    library.native_window_hit.argtypes = [ct.c_int16, ct.c_int16]
    library.native_window_hit.restype = ct.c_int
    return library


def make_machine():
    class OriginalOnlyPair:
        function = functions.get("win_Recalc")
        vectors = {exe.MANAGER_SEG * 16 + v.offset: v for v in exe.load().vectors}
        delegate = {}
        candidate_entries = {}
        sequence_targets = set()

        @staticmethod
        def sequence_function(name):
            return functions.get(name)

    return behavior.Machine(OriginalOnlyPair())


def make_fixture(resource_id: int, payload: bytes, profile: bytes | None):
    old_seg, old_paras = memory_fixture.HEAP_SEG, memory_fixture.HEAP_PARAS
    memory_fixture.HEAP_SEG = lists.DATA[1] - 2
    memory_fixture.HEAP_PARAS = 0x100
    text = b"x"
    text_paras = (len(text) + 47) // 16
    window_paras = (len(payload) + 47) // 16
    free_paras = 0x100 - text_paras - window_paras
    try:
        arena = memory_fixture.heap_case(
            f"window/{resource_id:02x}/source-resource",
            [(text_paras, 0, {"size": len(text), "name": b"fixture-text"}),
             (window_paras, 1, {"size": len(payload), "name": b"window-resource"}),
             (free_paras, 0x80, {"name": b"free-tail"})],
            handles=[0, 1], contract="actual original record in a valid Ralloc handle arena")
    finally:
        memory_fixture.HEAP_SEG, memory_fixture.HEAP_PARAS = old_seg, old_paras

    window_data_seg = lists.DATA[1] + text_paras
    window_handle_slot = lists.HANDLE[0] - 4
    offsets = bytearray(struct.pack("<4h", -32768, -32768, -32768, -32768) * 45)
    if profile is not None:
        offsets[:min(len(offsets), len(profile))] = profile[:len(offsets)]
    window_handles = behavior.symbol_address("win_handles")
    zorder = behavior.symbol_address("g_5702")
    writes = list(arena.writes)
    writes += [(window_data_seg * 16, payload),
               (window_handles + resource_id * 4, behavior.words(window_handle_slot, lists.HANDLE[1])),
               (behavior.symbol_address("win_numOfWindows"), behavior.words(45)),
               (behavior.symbol_address("win_offsets"), bytes(offsets)),
               (behavior.symbol_address("g_6300"), behavior.words(0)),
               (zorder, behavior.words(resource_id << 8, 0x8000, *([0x8000] * 30)))]
    observe = [behavior.Range("actual_window_payload", window_data_seg * 16, len(payload)),
               behavior.Range("actual_window_handle", lists.HANDLE[1] * 16 + window_handle_slot, 4),
               behavior.Range("actual_window_offsets", behavior.symbol_address("win_offsets"), len(offsets)),
               behavior.Range("actual_window_stack", zorder, 64)]
    handle_off, handle_seg = window_handle_slot, lists.HANDLE[1]

    def resource_service(machine, args):
        if (args[0], args[1], args[2]) != (resource_id, 0, 1):
            raise AssertionError(f"unexpected win_LoadWindow resource request: {args}")
        machine.state.setdefault("resource_requests", []).append(list(args))
        return handle_off, handle_seg

    case = behavior.Case(
        label=f"original-load-window/{resource_id:02x}", args=[resource_id << 8],
        writes=writes, observe=observe, callbacks={
            "f_1A53_00F0": behavior.Callback(3, resource_service)},
        return_kind="void", metadata={"resource_id": resource_id,
            "window_data_seg": window_data_seg, "window_handle_slot": window_handle_slot,
            "text_paras": text_paras, "window_paras": window_paras,
            "free_paras": free_paras, "profile": profile is not None})
    return case, window_data_seg


def run_original_recalc(machine, resource_id: int, payload: bytes,
                        profile: bytes | None, label: str):
    case, window_seg = make_fixture(resource_id, payload, profile)
    machine.run(behavior.Case(f"{label}/LockInit", return_kind="void"), function="win_LockInit")
    machine.run(case, function="win_LoadWindow")
    machine.run(behavior.Case(f"{label}/Recalc", registers={"ax": resource_id << 8},
                              return_kind="void"), preserve=True, function="win_Recalc")
    machine.run(behavior.Case(f"{label}/Unlock", registers={"ax": resource_id << 8},
                              return_kind="void"), preserve=True, function="win_UnlockWin")

    base = window_seg * 16
    count = machine.word(base + 0x0c)
    window_rect = struct.unpack("<4h", machine.read(base, 8))
    objects = []
    for i in range(count):
        off, seg = struct.unpack("<HH", machine.read(base + 0x2c + 4 * i, 4))
        at = seg * 16 + off
        rect = struct.unpack("<4h", machine.read(at, 8))
        flags = machine.word(at + 0x24)
        objects.append({"rect": list(rect), "flags": flags, "address": at})
    return {"window_rect": list(window_rect), "objects": objects,
            "window_base": base, "window_seg": window_seg, "count": count,
            "request_state": machine.state.get("resource_requests", [])}


def run_original_hit(machine, resource_id: int, x: int, y: int) -> int:
    machine.set_word(behavior.symbol_address("g_9122"), x)
    machine.set_word(behavior.symbol_address("g_9124"), y)
    result = machine.run(behavior.Case(f"hit/{resource_id:02x}/{x}/{y}", return_kind="s16"),
                        preserve=True, function="f_218D_052F")
    return result["return"]


def native_setup(library, resource_id: int, payload: bytes, profile: bytes | None):
    storage = (ct.c_uint8 * len(payload)).from_buffer_copy(payload)
    status = library.native_window_prepare(resource_id, storage, len(payload))
    if status != 0:
        raise RuntimeError(f"native decode failed: {status}")
    if profile is not None:
        profile_storage = (ct.c_uint8 * len(profile)).from_buffer_copy(profile)
        status = library.native_window_profile(profile_storage, len(profile))
        if status != 0:
            raise RuntimeError(f"native profile setup failed: {status}")
    status = library.native_window_recalculate()
    if status != 0:
        raise RuntimeError(f"native recalc failed: {status}")
    count = library.native_window_count()
    objects = []
    for i in range(count):
        rect = (ct.c_int16 * 4)()
        flags = ct.c_uint16()
        if not library.native_window_object(i, rect, ct.byref(flags)):
            raise RuntimeError("native object read failed")
        objects.append({"rect": list(rect), "flags": flags.value})
    window_rect = (ct.c_int16 * 4)()
    library.native_window_rect(window_rect)
    return {"window_rect": list(window_rect), "objects": objects,
            "payload_buffer": storage}


def compare_recalc(native, original):
    if native["window_rect"] != original["window_rect"]:
        return {"window_rect": {"native": native["window_rect"],
                                 "original": original["window_rect"]}}
    if len(native["objects"]) != len(original["objects"]):
        return {"object_count": {"native": len(native["objects"]),
                                  "original": len(original["objects"])} }
    mismatches = []
    for i, (a, b) in enumerate(zip(native["objects"], original["objects"])):
        if a["rect"] != b["rect"] or a["flags"] != b["flags"]:
            mismatches.append({"index": i, "native": a, "original": b})
    return {"objects": mismatches} if mismatches else {}


def hit_grid(resource_id: int, width_rect, native, machine, native_library, *, all_pixels: bool):
    if all_pixels:
        # Keep lazy-generator bounds independent from the loop's object bounds.
        # Reusing these names silently truncated the scan to the last object.
        frame_left, frame_top, frame_right, frame_bottom = width_rect
        points = ((x, y) for y in range(frame_top - 1, frame_bottom + 1)
                  for x in range(frame_left - 1, frame_right + 1))
    else:
        points = []
        for obj in native["objects"][1:]:
            if not obj["flags"] & 2:
                continue
            left, top, right, bottom = obj["rect"]
            points.extend(((left, top), (right - 1, top), (left, bottom - 1),
                           (right - 1, bottom - 1), (right, top), (left - 1, top),
                           (left, bottom), (left, top - 1)))
    compared = 0
    mismatches = []
    started = time.monotonic()
    for x, y in points:
        expected_index = native_library.native_window_hit(x, y)
        expected = -1 if expected_index < 0 else (resource_id << 8) + expected_index
        actual = run_original_hit(machine, resource_id, x, y)
        compared += 1
        if actual != expected:
            mismatches.append({"point": [x, y], "native": expected, "original": actual})
            if len(mismatches) >= 20:
                break
    return {"points": compared, "mismatches": mismatches,
            "seconds": round(time.monotonic() - started, 3), "full_window": all_pixels}


def run(full_scan: bool):
    native_hash = build_native_library()
    native = configure_native(NATIVE_LIBRARY)
    profile, profile_flags = resource_payload("HCEGANT", 0, 9)
    payloads = {2: resource_payload("HCEGANT", 2, 0)[0],
                0x21: resource_payload("HCEGANT", 0x21, 0)[0]}
    machine = make_machine()
    results = []
    started = time.monotonic()

    for resource_id, raw_payload in payloads.items():
        for variant, payload, use_profile in (
            ("actual-no-profile", raw_payload, False),
            ("poison-raw-rectangles", with_raw_rect_poison(raw_payload, 0x7fff), False),
            ("poison-sentinel-and-low", with_raw_rect_poison(raw_payload, 0x8000), False),
            ("valid-offset-minus-8", with_valid_offset_shift(raw_payload, -8), False),
            ("valid-offset-plus-8", with_valid_offset_shift(raw_payload, 8), False),
            ("initialized-kind9-profile", raw_payload, True),
        ):
            profile_input = profile if use_profile and resource_id == 2 else None
            native_observation = native_setup(native, resource_id, payload, profile_input)
            original_observation = run_original_recalc(
                machine, resource_id, payload, profile_input,
                f"{resource_id:02x}/{variant}")
            diff = compare_recalc(native_observation, original_observation)
            results.append({"resource_id": resource_id, "variant": variant,
                            "payload_sha256": sha(payload), "profile_applied": profile_input is not None,
                            "native_window_rect": native_observation["window_rect"],
                            "original_window_rect": original_observation["window_rect"],
                            "native_objects": native_observation["objects"],
                            "original_objects": [{"rect": x["rect"], "flags": x["flags"]}
                                                 for x in original_observation["objects"]],
                            "recalc_mismatches": diff,
                            "actual_resource_service": original_observation["request_state"]})
            if diff:
                continue
            if variant == "actual-no-profile":
                hit = hit_grid(resource_id, original_observation["window_rect"],
                               native_observation, machine, native,
                               all_pixels=full_scan)
                results[-1]["hit_grid"] = hit

    return {"schema": "portable-window-dos-differential-v1",
            "original_oracle_sha256": exe.load().sha256,
            "machine_harness_sha256": behavior.digest(behavior.HARNESS_SOURCE),
            "native_adapter_sha256": sha(ADAPTER_SOURCE.read_bytes()),
            "native_library_sha256": native_hash,
            "ndx_sha256": sha((ROOT / "assets/HCEGANT.NDX").read_bytes()),
            "dat_sha256": sha((ROOT / "assets/HCEGANT.DAT").read_bytes()),
            "kind9_profile_id": 0, "kind9_profile_flags": profile_flags,
            "kind9_profile_sha256": sha(profile),
            "resources": {str(k): {"sha256": sha(v), "size": len(v)}
                          for k, v in payloads.items()},
            "comparisons": results,
            "mismatch_count": sum(bool(r["recalc_mismatches"]) or
                                  bool(r.get("hit_grid", {}).get("mismatches")) for r in results),
            "boundaries": "frozen original win_LoadWindow (f_1A53_00F0 is only the explicit resource provider), win_LockInit/win_LockWin/RepointObjects/win_Recalc/win_UnlockWin and f_218D_052F execute from original DOS image; native decoder/recalc/hit test execute from C DLL; actual HCEGANT records and kind-9 origin profile; no historical source or object changes",
            "full_window_scan": full_scan,
            "elapsed_seconds": round(time.monotonic() - started, 3)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--full-scan", action="store_true",
                        help="compare every pixel in both decoded window rectangles")
    args = parser.parse_args()
    report = run(args.full_scan)
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(REPORT_PATH), "mismatch_count": report["mismatch_count"],
                      "elapsed_seconds": report["elapsed_seconds"],
                      "hit_grids": [r.get("hit_grid") for r in report["comparisons"]
                                    if r.get("hit_grid") is not None]}, indent=2))
    if report["mismatch_count"]:
        raise SystemExit(1)
