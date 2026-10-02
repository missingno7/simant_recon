#!/usr/bin/env python3
"""Compare native shortcut intents with the original DOS key-event router."""
from __future__ import annotations

import ctypes as ct
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))
import behavior

SOURCE = ROOT / "src/S19/m384C.c"
INPUT_C = ROOT / "portable/ui_model/input/input.c"
INPUT_H = ROOT / "portable/ui_model/input/input.h"
TEST_C = ROOT / "portable/tests/input/test_input.c"
OUTPUT = ROOT / "portable/tests/input/evidence/key-routing-dos-diff.json"
DLL = ROOT / "build/portable/tests/input-key-routing-diff.dll"


class Effect(ct.Structure):
    _fields_ = [("kind", ct.c_int), ("value", ct.c_int16)]


class Effects(ct.Structure):
    _fields_ = [("items", Effect * 3), ("count", ct.c_size_t)]


EFFECT_NAMES = {
    1: "set_paused", 2: "set_speed", 3: "set_map_plane",
    4: "set_yard_mode", 5: "open_edit", 6: "open_map_yard",
    7: "open_mode", 8: "open_caste", 9: "ensure_yard_view",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def native_api():
    subprocess.run([
        "gcc", "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror", "-shared",
        "-I", str(ROOT / "portable"), str(INPUT_C), "-o", str(DLL),
    ], check=True, cwd=ROOT)
    lib = ct.CDLL(str(DLL))
    fn = lib.portable_input_key
    fn.argtypes = [ct.c_uint16, ct.c_int16, ct.c_int16, ct.c_int16,
                   ct.c_int16, ct.POINTER(Effects)]
    fn.restype = ct.c_int
    menu = lib.portable_input_menu_item
    menu.argtypes = [ct.c_uint8, ct.c_int16, ct.c_int16, ct.c_int16,
                     ct.c_int16, ct.POINTER(Effects)]
    menu.restype = ct.c_int
    return fn, menu


def effect_rows(effects: Effects):
    return [{"kind": EFFECT_NAMES[effects.items[i].kind],
             "value": int(effects.items[i].value)}
            for i in range(effects.count)]


def main():
    key_to_source = {
        0x29: 0xFD41, 0x21: 0xFD43, 0x40: 0xFD44,
        0x23: 0xFD45, 0x24: 0xFD46, 0x05: 0xFD11,
        0x0D: 0xFD12, 0x02: 0xFD13, 0x03: 0xFD14,
        0x19: 0xFD21,
    }
    expected_effects = {
        0x29: [("set_paused", 1)],
        0x21: [("set_speed", 0)], 0x40: [("set_speed", 1)],
        0x23: [("set_speed", 2)], 0x24: [("set_speed", 3)],
        0x05: [("open_edit", 0)], 0x0D: [("open_map_yard", 0)],
        0x02: [("open_mode", 0)], 0x03: [("open_caste", 0)],
        0x19: [("set_yard_mode", 0)],
    }
    pair = behavior.PreparedPair("o19_384C_0246", source=SOURCE)
    key_fn, menu_fn = native_api()
    rows = []
    for key, expected_code in key_to_source.items():
        callbacks = {
            "f_1F58_0090": behavior.Callback(0, handler=lambda _m, _a, k=key: k),
            "CheatKeys": behavior.Callback(1, handler=lambda _m, _a: None),
            "f_1B73_0A30": behavior.Callback(1, handler=lambda _m, _a: 0),
            "WinPrintf": behavior.Callback(3, handler=lambda _m, _a: 0),
            "f_1B73_030F": behavior.Callback(4, handler=lambda _m, _a: None),
            "YellowCommandKey": behavior.Callback(1, handler=lambda _m, _a: 0),
        }
        result = pair.original_machine.run(behavior.Case(
            f"key-{key:04x}", callbacks=callbacks, return_kind="void"))
        routed = [item for item in result["trace"] if item["name"] == "f_1B73_030F"]
        actual_code = routed[-1]["args"][0] if routed else None
        key_effects = Effects()
        status = key_fn(key, 0, 0, 1, 1, ct.byref(key_effects))
        menu_effects = Effects()
        menu_status = menu_fn(actual_code & 0xff, 0, 0, 1, 1,
                              ct.byref(menu_effects)) if actual_code is not None else -1
        row = {
            "key": key,
            "expected_source_event": expected_code,
            "original_dispatched_event": actual_code,
            "native_key_status": status,
            "native_key_effects": effect_rows(key_effects),
            "effects_from_original_event_code_status": menu_status,
            "effects_from_original_event_code": effect_rows(menu_effects),
            "expected_effects": [{"kind": kind, "value": value}
                                 for kind, value in expected_effects[key]],
            "mismatch": (actual_code != expected_code or status != 0 or
                         effect_rows(key_effects) != effect_rows(menu_effects) or
                         effect_rows(key_effects) != [
                             {"kind": kind, "value": value}
                             for kind, value in expected_effects[key]]),
        }
        rows.append(row)
    report = {
        "schema": "portable-input-key-routing-dos-diff-v1",
        "status": "PASS" if not any(r["mismatch"] for r in rows) else "FAIL",
        "scope": "o19_384C_0246 original key-to-FD-event routing and matching native intents for pause, four speed settings, and four window commands; ProcMenu service effects are source-mapped separately in the C API/tests.",
        "limitations": [
            "Key service, diagnostic printing, and f_1B73_030F event dispatch are explicit deterministic callbacks.",
            "This does not execute Win16 window services, SetPause, SetMapPlane, gameplay commands, or physical keyboard/BIOS devices.",
            "Held-key and mouse edge-pan paths are source-mapped and covered by native directed tests, but no original VM device-state differential is claimed."
        ],
        "identity": pair.identity,
        "pinned_sources": {
            "src/S19/m384C.c": sha(SOURCE),
            "portable/ui_model/input/input.c": sha(INPUT_C),
            "portable/ui_model/input/input.h": sha(INPUT_H),
            "portable/tests/input/test_input.c": sha(TEST_C),
            "tools/behavior.py": sha(ROOT / "tools/behavior.py"),
            "layout/manifest.json": sha(ROOT / "layout/manifest.json"),
        },
        "oracle_sha256": behavior.exe.load().sha256,
        "case_count": len(rows),
        "mismatch_count": sum(int(r["mismatch"]) for r in rows),
        "cases": rows,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(OUTPUT.relative_to(ROOT)),
                      "cases": report["case_count"],
                      "mismatches": report["mismatch_count"],
                      "status": report["status"]}, indent=2))
    return 1 if report["mismatch_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
