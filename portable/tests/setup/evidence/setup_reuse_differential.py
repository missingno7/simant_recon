#!/usr/bin/env python3
"""DOS-vs-native repeated initControls with nonfresh defaults and presets.

This is a new sidecar: the earlier default-only pinned report is intentionally
left untouched. Source TU-static selectors are recovered from their direct
DS displacements in the original ProcModeEvent/ProcCasteEvent code and are
mutated in the original VM before the repeated call.
"""
from __future__ import annotations

import ctypes as ct
import hashlib
import importlib.util
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "tools"))
import behavior  # noqa: E402

BASE = Path(__file__).with_name("setup_differential.py")
spec = importlib.util.spec_from_file_location("setup_default_diff", BASE)
base = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = base
spec.loader.exec_module(base)

REPORT = Path(__file__).with_name("setup_reuse_differential_report.json")
MODE_DEFAULT = (0x1234, 0x5678, 0x9ABC)
CASTE_DEFAULT = (0x2345, 0x6789, 0xABCD)
MODE_ROWS = ((0x1111, 0x2222, 0x3333),
             (0x4444, 0x5555, 0x6666),
             (0x7777, 0x8888, 0x9999))
CASTE_ROWS = ((0xAAAA, 0xBBBB, 0xCCCC),
              (0xDDDD, 0xEEEE, 0xFFFF),
              (0x0101, 0x0202, 0x0303))
INPUT = list(MODE_DEFAULT + CASTE_DEFAULT + (2, 3) +
             tuple(x for row in MODE_ROWS + CASTE_ROWS for x in row))


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


PINNED_PATHS = [
    "portable/game/simulation/setup.c", "portable/game/simulation/setup.h",
    "portable/tests/setup/evidence/setup_native_adapter.c",
    "portable/tests/setup/evidence/setup_differential.py",
    "portable/tests/setup/evidence/setup_reuse_differential.py",
    "tools/behavior.py", "tools/exe.py", "tools/functions.py", "tools/symbols.py",
    "tools/match.py", "tools/modctx.py", "tools/modules.py", "tools/compiler.py",
    "layout/functions.json", "layout/symbols.json", "assets/SIMANT.EXE",
    "assets/HCEGANT.NDX", "assets/HCEGANT.DAT",
]


def source_pins() -> dict[str, str]:
    return {name: sha((ROOT / name).read_bytes()) for name in PINNED_PATHS}


def write_words(machine, symbol: str, words: tuple[int, ...]) -> None:
    machine.write(behavior.symbol_address(symbol), struct.pack("<" + "H" * len(words), *words))


def write_words_at(machine, address: int, words: tuple[int, ...]) -> None:
    machine.write(address, struct.pack("<" + "H" * len(words), *words))


def original_reinit():
    source, machine, fixture = base.original_run()
    write_words(machine, "fd_3D57_080A", MODE_DEFAULT)
    write_words(machine, "fd_3D57_07EC", CASTE_DEFAULT)
    # The rows here are the three nondefault presets: start at byte offset +6
    # because source initControls replaces preset row zero with DATA defaults.
    write_words_at(machine, behavior.symbol_address("fd_3D57_0810") + 6,
                   tuple(x for row in MODE_ROWS for x in row))
    write_words_at(machine, behavior.symbol_address("fd_3D57_07F2") + 6,
                   tuple(x for row in CASTE_ROWS for x in row))
    dgroup = machine.reg("ds")
    selector_addresses = {"mode": dgroup * 16 + 0x1B50,
                          "caste": dgroup * 16 + 0x1B4E}
    selector_before = {name: int.from_bytes(machine.read(address, 2), "little")
                       for name, address in selector_addresses.items()}
    machine.write(selector_addresses["mode"], struct.pack("<H", 2))
    machine.write(selector_addresses["caste"], struct.pack("<H", 3))
    source_before = {
        "mode_defaults": base.read_words(machine, "fd_3D57_080A", 3),
        "caste_defaults": base.read_words(machine, "fd_3D57_07EC", 3),
        "mode_presets": base.read_words(machine, "fd_3D57_0810", 12),
        "caste_presets": base.read_words(machine, "fd_3D57_07F2", 12),
    }
    table_writes = []
    mode_table = behavior.symbol_address("fd_3D57_0810")
    caste_table = behavior.symbol_address("fd_3D57_07F2")
    def record_table_write(_uc, _access, address, size, value, _user):
        if (mode_table <= address < mode_table + 24 or
                caste_table <= address < caste_table + 24):
            table_writes.append({"linear": address, "size": size,
                                 "value": value,
                                 "cs_ip": [machine.reg("cs"), machine.reg("ip")]})
    machine.cpu.hook_add(behavior.uc.UC_HOOK_MEM_WRITE, record_table_write)
    def resource_size_service(vm, args):
        if args[2] != 0x578:
            raise AssertionError(f"unexpected resource-size object: {args}")
        data, flags = base.helpers.resource_payload("HCEGANT", args[2], 2)
        if flags != 8 or len(data) < 12:
            raise AssertionError("unexpected knob bitmap resource")
        width, height = struct.unpack_from("<HH", data, 8)
        vm.write(args[1] * 16 + args[0], struct.pack("<hh", width, height))
        return 1

    def closed_service(name):
        def handler(vm, args):
            handle_name = "fd_50F6_37F6" if name == "mode" else "fd_50F6_37F2"
            if vm.read(behavior.symbol_address(handle_name), 4) != b"\0" * 4:
                raise AssertionError(f"unexpected live {name} animation handle")
        return handler

    callbacks = {
        "f_208F_0419": behavior.Callback(3, resource_size_service),
        "win_ModeControlClosed": behavior.Callback(0, closed_service("mode")),
        "win_CasteControlClosed": behavior.Callback(0, closed_service("caste")),
    }
    observation = machine.run(behavior.Case(
        "setup/initControls/reuse-mutated-defaults-and-presets",
        callbacks=callbacks, return_kind="void", observe_at_calls=False),
        preserve=True, function="initControls")
    result = {
        "mode_level": base.read_words(machine, "modeLevels", 3),
        "caste_level": base.read_words(machine, "casteLevels", 3),
        "mode_presets": base.read_words(machine, "fd_3D57_0810", 12),
        "caste_presets": base.read_words(machine, "fd_3D57_07F2", 12),
        "ideal_caste": base.read_words(machine, "IdealCaste", 4),
        "controls": [base.read_words(machine, "ModeAuto", 1)[0],
                     base.read_words(machine, "CasteAuto", 1)[0],
                     base.read_words(machine, "fd_50F6_0468", 1)[0],
                     base.read_words(machine, "fd_3D57_07EA", 1)[0],
                     int.from_bytes(machine.read(selector_addresses["mode"], 2), "little"),
                     int.from_bytes(machine.read(selector_addresses["caste"], 2), "little"),
                     base.read_words(machine, "fd_50F6_0370", 1, signed=True)[0],
                     base.read_words(machine, "fd_50F6_024E", 1, signed=True)[0]],
        "callback_trace": observation["raw_trace"],
        "post_default_words": {
            "mode": base.read_words(machine, "fd_3D57_080A", 3),
            "caste": base.read_words(machine, "fd_3D57_07EC", 3),
        },
        "injected_before_second_call": source_before,
        "selectors_before_second_call": selector_before,
        "selector_addresses_linear": selector_addresses,
        "selectors_after_second_call": {
            name: int.from_bytes(machine.read(address, 2), "little")
            for name, address in selector_addresses.items()},
        "preset_table_write_trace": table_writes,
    }
    return result, machine, fixture, source


def native_reinit():
    library_hash = base.build_native()
    lib = base.configure_native()
    root = str(ROOT / "assets" / "HCEGANT").encode("utf-8")
    status = lib.setup_native_init(root, 0)
    if status:
        raise RuntimeError(f"native initial controls setup failed: {status}")
    mutate = lib.setup_native_mutate_reinit
    mutate.argtypes = [ct.POINTER(ct.c_int32)]
    mutate.restype = ct.c_int
    values = (ct.c_int32 * len(INPUT))(*INPUT)
    status = mutate(values)
    if status:
        raise RuntimeError(f"native repeated initControls failed: {status}")
    try:
        snapshot = (ct.c_int32 * 128)()
        count = lib.setup_native_snapshot(snapshot, len(snapshot))
        if count != 62:
            raise RuntimeError(f"unexpected native snapshot size {count}")
        at = 0
        parsed = {}
        for name, size in base.SNAPSHOT_FIELDS:
            parsed[name] = list(snapshot[at:at + size])
            at += size
        parsed["events"] = [lib.setup_native_event(i)
                            for i in range(lib.setup_native_event_count())]
        return parsed, library_hash
    finally:
        lib.setup_native_close()


def main():
    pins_before = source_pins()
    native, native_hash = native_reinit()
    original, machine, fixture, first_source = original_reinit()
    pins_after = source_pins()
    expected = {
        "mode_level": list(MODE_DEFAULT),
        "caste_level": list(CASTE_DEFAULT),
        "mode_presets": list(MODE_DEFAULT) + [x for row in MODE_ROWS for x in row],
        "caste_presets": list(CASTE_DEFAULT) + [x for row in CASTE_ROWS for x in row],
        "ideal_caste": original["ideal_caste"],
        "controls": original["controls"],
    }
    # Native snapshot names map onto the original source observables.
    mapping = {"mode_level": "mode_level", "caste_level": "caste_level",
               "mode_presets": "mode_presets", "caste_presets": "caste_presets",
               "ideal_caste": "ideal_caste", "controls": "controls"}
    mismatches = {field: {"native": native[field], "original": original[field]}
                  for field in mapping if native[field] != original[field]}
    for field in ("mode_level", "caste_level", "mode_presets", "caste_presets"):
        if original[field] != expected[field]:
            mismatches[f"original_expected_{field}"] = {
                "actual": original[field], "expected": expected[field]}
    report = {
        "schema": "portable-init-controls-reuse-dos-differential-v1",
        "original_exe_sha256": base.exe.load().sha256,
        "behavior_harness_sha256": behavior.digest(behavior.HARNESS_SOURCE),
        "setup_source_sha256": sha((ROOT / "portable/game/simulation/setup.c").read_bytes()),
        "setup_header_sha256": sha((ROOT / "portable/game/simulation/setup.h").read_bytes()),
        "native_adapter_sha256": sha(base.NATIVE_SOURCE.read_bytes()),
        "native_library_sha256": native_hash,
        "ndx_sha256": sha((ROOT / "assets/HCEGANT.NDX").read_bytes()),
        "dat_sha256": sha((ROOT / "assets/HCEGANT.DAT").read_bytes()),
        "original_initControls_address": base.functions.get("initControls"),
        "reuse_producer_sha256": sha(Path(__file__).read_bytes()),
        "default_producer_sha256": sha(BASE.read_bytes()),
        "source_pins_before": pins_before,
        "source_pins_after": pins_after,
        "source_pins_stable": pins_before == pins_after,
        "fixture_windows": [18, 19],
        "initial_fresh_snapshot": first_source,
        "mutation": {"mode_defaults": MODE_DEFAULT, "caste_defaults": CASTE_DEFAULT,
                     "mode_rows_1_3": MODE_ROWS, "caste_rows_1_3": CASTE_ROWS,
                     "selectors": {"mode": 2, "caste": 3,
                                   "basis": "ProcModeEvent DS:[1B50], ProcCasteEvent DS:[1B4E] original-code displacements"}},
        "original_snapshot": original,
        "native_snapshot": native,
        "mismatches": mismatches,
        "mismatch_count": len(mismatches),
        "selector_scope": "The original DOS lane writes selector words through the source TU's DGROUP offsets 1B50/1B4E, derived from original ProcModeEvent/ProcCasteEvent direct DS operands; the second initControls call preserves nonzero values 2/3. The native lane receives the same typed selectors.",
        "claim_boundary": "This checks repeated initControls on an initialized pair of real HCEGANT windows. It does not claim a full RandYard/NewGame restart sequence.",
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(REPORT), "mismatch_count": len(mismatches),
                      "mismatches": mismatches}, indent=2))
    return 1 if mismatches or pins_before != pins_after else 0


if __name__ == "__main__":
    raise SystemExit(main())
