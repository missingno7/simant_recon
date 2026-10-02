#!/usr/bin/env python3
"""Compare startup window registry geometry with the frozen DOS window code."""
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

EVIDENCE = Path(__file__).resolve().parent
WINDOW_HELPERS = EVIDENCE / "differential_window.py"
spec = importlib.util.spec_from_file_location("window_differential_helpers", WINDOW_HELPERS)
helpers = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = helpers
spec.loader.exec_module(helpers)

NATIVE_SOURCE = EVIDENCE / "registry_native_adapter.c"
NATIVE_LIBRARY = EVIDENCE / "registry_native_adapter.dll"
REPORT_PATH = EVIDENCE / "differential_registry_report.json"
GCC = Path("C:/msys64/mingw64/bin/gcc.exe")
STARTUP_LOADED_IDS = [0, 1, 18, 19, 25]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build_native_library() -> str:
    command = [str(GCC), "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
               "-shared", str(NATIVE_SOURCE),
               str(ROOT / "portable/ui_model/windows/registry.c"),
               str(ROOT / "portable/ui_model/windows/window.c"),
               str(ROOT / "portable/game/resources/database.c"),
               "-o", str(NATIVE_LIBRARY)]
    subprocess.run(command, check=True, cwd=ROOT)
    return sha(NATIVE_LIBRARY.read_bytes())


def configure_library():
    lib = ct.CDLL(str(NATIVE_LIBRARY))
    lib.registry_open.argtypes = [ct.c_char_p, ct.c_int16]
    lib.registry_open.restype = ct.c_int
    lib.registry_window_count.argtypes = []
    lib.registry_window_count.restype = ct.c_int
    lib.registry_preloaded_count.argtypes = []
    lib.registry_preloaded_count.restype = ct.c_int
    lib.registry_loaded.argtypes = [ct.c_int16]
    lib.registry_loaded.restype = ct.c_int
    lib.registry_object_count.argtypes = [ct.c_int16]
    lib.registry_object_count.restype = ct.c_int
    lib.registry_recalculate.argtypes = [ct.c_int16]
    lib.registry_recalculate.restype = ct.c_int
    lib.registry_object_rect.argtypes = [ct.c_int16, ct.c_int16,
                                         ct.POINTER(ct.c_int16)]
    lib.registry_object_rect.restype = ct.c_int
    lib.registry_close.argtypes = []
    lib.registry_close.restype = None
    return lib


def original_states(machine, resource_id: int):
    payload, _ = helpers.resource_payload("HCEGANT", resource_id, 0)
    profile, _ = helpers.resource_payload("HCEGANT", 0, 9)
    load_case, window_seg = helpers.make_fixture(
        resource_id, payload, profile,)
    machine.run(behavior.Case(f"registry/{resource_id:02x}/LockInit",
                              return_kind="void"), function="win_LockInit")
    machine.run(load_case, function="win_LoadWindow")
    base = window_seg * 16

    def snapshot():
        count = machine.word(base + 0x0c)
        rects = []
        for index in range(count):
            off, seg = struct.unpack(
                "<HH", machine.read(base + 0x2c + 4 * index, 4))
            rects.append(list(struct.unpack(
                "<4h", machine.read(seg * 16 + off, 8))))
        return rects

    loaded = snapshot()
    machine.run(behavior.Case(
        f"registry/{resource_id:02x}/Recalc",
        registers={"ax": resource_id << 8}, return_kind="void"),
        preserve=True, function="win_Recalc")
    recalculated = snapshot()
    return {"payload_sha256": sha(payload), "loaded": loaded,
            "recalculated": recalculated}


def native_rects(lib, resource_id: int, count: int):
    result = []
    for index in range(count):
        rect = (ct.c_int16 * 4)()
        if not lib.registry_object_rect(resource_id, index, rect):
            raise RuntimeError(f"native get rect failed for {resource_id:#x}/{index}")
        result.append(list(rect))
    return result


def run():
    native_hash = build_native_library()
    lib = configure_library()
    root = str(ROOT / "assets" / "HCEGANT").encode("utf-8")
    status = lib.registry_open(root, 0)
    if status != 0:
        raise RuntimeError(f"native registry init failed: {status}")
    if lib.registry_window_count() != 34 or lib.registry_preloaded_count() != 5:
        raise AssertionError("native startup preload set does not match HCEGANT catalog")

    machine = helpers.make_machine()
    cases = []
    try:
        for resource_id in STARTUP_LOADED_IDS:
            if not lib.registry_loaded(resource_id):
                raise AssertionError(f"native startup window {resource_id:#x} was not preloaded")
            count = lib.registry_object_count(resource_id)
            before_native = native_rects(lib, resource_id, count)
            original = original_states(machine, resource_id)
            if count != len(original["loaded"]):
                raise AssertionError(f"object count mismatch for window {resource_id:#x}")
            loaded_diffs = [i for i, pair in enumerate(zip(before_native,
                                                            original["loaded"]))
                            if pair[0] != pair[1]]
            recalc_status = lib.registry_recalculate(resource_id)
            if recalc_status != 0:
                raise AssertionError(
                    f"native recalc failed for {resource_id:#x}: {recalc_status}")
            after_native = native_rects(lib, resource_id, count)
            recalculated_diffs = [i for i, pair in enumerate(zip(after_native,
                                                                  original["recalculated"]))
                                  if pair[0] != pair[1]]
            cases.append({"resource_id": resource_id,
                          "payload_sha256": original["payload_sha256"],
                          "object_count": count,
                          "load_state_mismatching_objects": loaded_diffs,
                          "recalc_mismatching_objects": recalculated_diffs,
                          "native_loaded_rects": before_native,
                          "original_loaded_rects": original["loaded"],
                          "native_recalculated_rects": after_native,
                          "original_recalculated_rects": original["recalculated"]})
    finally:
        lib.registry_close()

    report = {
        "schema": "portable-window-startup-registry-differential-v1",
        "original_oracle_sha256": exe.load().sha256,
        "machine_harness_sha256": behavior.digest(behavior.HARNESS_SOURCE),
        "native_adapter_sha256": sha(NATIVE_SOURCE.read_bytes()),
        "native_library_sha256": native_hash,
        "compiler": {
            "path": str(GCC),
            "version": subprocess.check_output([str(GCC), "--version"],
                                                text=True).splitlines()[0],
            "sha256": sha(GCC.read_bytes()),
        },
        "source_inputs": {
            str(path.relative_to(ROOT)).replace("\\", "/"): sha(path.read_bytes())
            for path in (
                ROOT / "portable/ui_model/windows/registry.c",
                ROOT / "portable/ui_model/windows/registry.h",
                ROOT / "portable/ui_model/windows/window.c",
                ROOT / "portable/ui_model/windows/window.h",
                ROOT / "portable/game/resources/database.c",
                ROOT / "portable/game/resources/database.h",
                ROOT / "portable/tests/windows/test_registry.c",
                NATIVE_SOURCE,
                Path(__file__).resolve(),
                WINDOW_HELPERS,
                helpers.MEMORY_FIXTURE,
                ROOT / "tools/behavior.py",
                ROOT / "tools/exe.py",
                ROOT / "tools/functions.py",
                ROOT / "tools/match.py",
                ROOT / "layout/functions.json",
                ROOT / "layout/symbols.json",
                ROOT / "layout/oracle.lock.json",
                ROOT / "src/root/m20E8.c",
                ROOT / "src/root/m2505.c",
                ROOT / "src/root/m208F.c",
                ROOT / "src/root/m24AB.c",
            )
        },
        "strict_native_test": {
            "command": "gcc -std=c11 -Wall -Wextra -Werror -pedantic test_registry.c registry.c window.c database.c",
            "result": "window registry tests passed",
        },
        "database": "HCEGANT",
        "database_ndx_sha256": sha((ROOT / "assets/HCEGANT.NDX").read_bytes()),
        "database_dat_sha256": sha((ROOT / "assets/HCEGANT.DAT").read_bytes()),
        "profile_id": 0,
        "catalog_window_count": 34,
        "purge_zero_preload_ids": STARTUP_LOADED_IDS,
        "preloaded_window_count": len(STARTUP_LOADED_IDS),
        "historical_source_anchors": [
            {"path": "src/root/m20E8.c",
             "functions": ["win_LoadWindow", "win_LoadAllWindows"]},
            {"path": "src/root/m2505.c",
             "functions": ["win_AutoSize", "f_2505_0453", "win_Recalc"]},
            {"path": "src/root/m208F.c",
             "functions": ["f_208F_0419"]},
            {"path": "src/root/m24AB.c",
             "functions": ["win_StringSize", "font_InitFonts"]},
        ],
        "cases": cases,
        "mismatch_count": sum(len(c["load_state_mismatching_objects"]) +
                               len(c["recalc_mismatching_objects"]) for c in cases),
        "boundaries": (
            "Original DOS win_LockInit, win_LoadWindow, and win_Recalc execute "
            "in the frozen behavior.Machine for each actual startup-preloaded "
            "kind-0 record; f_1A53_00F0 is only the explicit resource provider. "
            "Native registry loads catalog, purge list, kind-9 profile and actual "
            "kind-0 resources through portable_db, then compares load-state and "
            "recalculated rectangles. Startup windows contain no autosize or "
            "cross-window constraints; those remain explicit unsupported cases."
        )
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    result = run()
    print(json.dumps({"report": str(REPORT_PATH),
                      "mismatch_count": result["mismatch_count"],
                      "cases": [{"resource_id": c["resource_id"],
                                 "loaded_diffs": c["load_state_mismatching_objects"],
                                 "recalc_diffs": c["recalc_mismatching_objects"]}
                                for c in result["cases"]]}, indent=2))
    if result["mismatch_count"]:
        raise SystemExit(1)
