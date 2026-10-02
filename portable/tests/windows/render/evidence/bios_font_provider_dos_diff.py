#!/usr/bin/env python3
"""Compare the portable BIOS glyph provider to original f_1B4E_0110 input."""
from __future__ import annotations

import hashlib
import json
import struct
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parents[1]
OUT = HERE / "evidence" / "bios_font_provider_dos_diff.json"
BUILD = ROOT / "build" / "workers" / "behavior_tutorial_menu"
sys.path.insert(0, str(ROOT / "tools"))
import behavior

FONT_CODE = 0xA5
FONT_DATA_LINEAR = 0xA8000 + 0x0100


def w(value: int) -> bytes:
    return struct.pack("<H", value & 0xffff)


def far(offset: int, segment: int) -> bytes:
    return struct.pack("<HH", offset & 0xffff, segment & 0xffff)


def glyph_row(code: int, row: int) -> int:
    return ((code * 29 + row * 71) ^ ((code >> (row % 5)) * 11) ^
            (0x81 >> (row % 8))) & 0xff


def glyph_table(height: int) -> bytes:
    return bytes(glyph_row(code, row) for code in range(256)
                 for row in range(height))


def capture(machine, args):
    x, y, offset, segment, width, height = args
    data = machine.read(segment * 16 + offset, height)
    return {"x": x, "y": y, "width": width, "height": height,
            "glyph_rows_hex": data.hex()}


def noop(machine, args):
    return None


def dos_glyph(machine, height: int):
    offset, segment = 0x0100, 0xA800
    table = glyph_table(height)
    callback_code = behavior.symbol("f_1B4E_000C")
    callback_ptr = far(callback_code["off"], callback_code["seg"])
    writes = [
        (FONT_DATA_LINEAR, table),
        (behavior.symbol_address("g_3DD6"), far(offset, segment)),
        (behavior.symbol_address("g_3DDA"), w(height)),
        (behavior.symbol_address("g_3DDC"), w(height)),
        (behavior.symbol_address("g_3DDE"), w(8)),
        (behavior.symbol_address("g_9154"), callback_ptr),
    ]
    case = behavior.Case(
        f"controlled-font/{height}x8/{FONT_CODE:02x}",
        args=[5, 7, FONT_CODE], writes=writes,
        callbacks={"f_1B4E_000C": behavior.Callback(
            stack_words=6, handler=noop, project=capture)},
        return_kind="void",
        metadata={"contract": "original f_1B4E_0110 selects character*height and forwards exact BIOS bitmap pointer/8xheight geometry to g_9154"},
    )
    result = machine.run(case, function="f_1B4E_0110")
    assert len(result["trace"]) == 1
    row = result["trace"][0]["args"]
    assert (row["x"], row["y"], row["width"], row["height"]) == (5, 7, 8, height)
    expected = table[FONT_CODE * height:(FONT_CODE + 1) * height]
    assert bytes.fromhex(row["glyph_rows_hex"]) == expected
    return {"height": height, "x": row["x"], "y": row["y"],
            "width": row["width"], "glyph_rows_hex": row["glyph_rows_hex"],
            "original_callback": "g_9154", "helper": "f_1B4E_0110"}


def main() -> int:
    BUILD.mkdir(parents=True, exist_ok=True)
    executable = behavior.exe.load()
    original_pair = SimpleNamespace(
        function=behavior.functions.get("f_1B4E_0110"),
        vectors={behavior.exe.MANAGER_SEG*16+v.offset:v for v in executable.vectors},
        identity={"oracle_sha256": executable.sha256},
        delegate={},
        sequence_function=lambda name: behavior.functions.get(name),
    )
    machine = behavior.Machine(original_pair)
    oracle = {height: dos_glyph(machine, height) for height in (8, 14)}
    exe = BUILD / "bios_font_provider_contract.exe"
    sources = [
        "portable/tests/windows/render/test_bios_font_provider.c",
        "portable/ui_model/windows/render.c",
        "portable/ui_model/windows/window.c",
        "portable/game/resources/database.c",
        "portable/render/bitmap.c",
        "portable/render/font.c",
        "portable/render/primitives.c",
    ]
    command = ["gcc", "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
               "-Iportable", *sources, "-o", str(exe)]
    subprocess.run(command, cwd=ROOT, check=True)
    completed = subprocess.run([str(exe)], cwd=ROOT, check=True,
                               text=True, capture_output=True)
    rows = {}
    for line in completed.stdout.splitlines():
        if not line.startswith("font_id="):
            continue
        fields = dict(item.split("=", 1) for item in line.split())
        key = (int(fields["font_id"]), int(fields["screen_width"]))
        rows[key] = fields
    expected_height = {(0, 640): 14, (1, 640): 8,
                       (0, 320): 8, (1, 320): 14}
    cases = []
    for (font_id, screen_width), height in expected_height.items():
        fields = rows[(font_id, screen_width)]
        glyph = bytes.fromhex(fields["glyph_rows"])
        original = bytes.fromhex(oracle[height]["glyph_rows_hex"])
        assert glyph == original
        pixels = bytes(3 if bits & (0x80 >> col) else 0
                       for bits in glyph for col in range(8))
        fnv = 2166136261
        for value in pixels:
            fnv = ((fnv ^ value) * 16777619) & 0xffffffff
        assert int(fields["pixel_fnv1a"], 16) == fnv
        cases.append({"font_id": font_id, "screen_width": screen_width,
                      "height": height, "dos_glyph_rows_sha256": hashlib.sha256(original).hexdigest(),
                      "native_pixel_fnv1a": f"{fnv:08x}",
                      "status": "matched controlled provider contract"})
    reverse = bytes.fromhex(oracle[14]["glyph_rows_hex"])[::-1]
    assert reverse != bytes.fromhex(oracle[14]["glyph_rows_hex"])
    inputs = [*sources, "portable/ui_model/windows/render.h",
              "portable/ui_model/windows/window.h",
              "portable/game/resources/database.h", "portable/render/bitmap.h",
              "portable/render/font.h", "portable/render/primitives.h",
              "src/S00/m31AD.asm", "src/root/m1B4E.asm",
              "src/root/m1FBD.asm", "src/root/m24AB.c",
              "tools/behavior.py", "tools/exe.py", "tools/functions.py",
              "tools/match.py", "tools/modctx.py", "tools/symbols.py",
              "tools/behavior_suites/tutorial_menu.py", "layout/oracle.lock.json",
              "assets/SIMANT.EXE"]
    report = {
        "schema": "bios-bitmap-provider-original-glyph-v1",
        "status": "DIAGNOSTIC_PASS_NO_HISTORICAL_ACCEPTANCE_CLAIM",
        "oracle": {"function": "f_1B4E_0110", "address": {
            key: original_pair.function[key] for key in ("unit", "seg", "off", "size")},
            "oracle_sha256": executable.sha256,
            "unicorn_version": behavior.uc.__version__,
            "harness_sha256": behavior.digest(behavior.HARNESS_SOURCE)},
        "direct_oracle_call": "Original SIMANT.EXE f_1B4E_0110; g_9154 is intercepted only at its graphics callback boundary and its exact bitmap pointer/geometry are projected.",
        "font_selection_source": "src/root/m24AB.c:f_24AB_02AD and src/S00/m31AD.asm:o00_31AD_166A/o00_31AD_168C",
        "glyph_source_contract": "src/root/m1B4E.asm:f_1B4E_0110 uses byte offset character*height and forwards width then height to g_9154. The original callback is deliberately intercepted: the test proves table selection and byte forwarding, while the native provider contract interprets each row MSB-first.",
        "fixture": {"kind": "deterministic generated provider bytes, not ROM/game bytes",
                    "glyph_code": FONT_CODE, "heights": [8, 14],
                    "table_formula": "((code*29 + row*71) ^ ((code >> (row%5))*11) ^ (0x81 >> (row%8))) & 0xff"},
        "cases": cases,
        "negative_control": {"wrong_row_order": "reversed 8x14 glyph differs from original selected row sequence"},
        "native_stdout": completed.stdout.strip(),
        "host_reference_limit": "This proves the provider layout/selection and glyph bit interpretation for controlled bytes. g_9154 is a modeled graphics boundary, so the test does not establish physical DOS display pixels. It also does not establish that any real BIOS ROM or DOSBox font is historical SIMANT display output.",
        "producer": {"path": str(Path(__file__).resolve().relative_to(ROOT)),
                     "sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},
        "input_sha256": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                         for name in inputs},
        "build": {"command": command, "compiler": "gcc", "flags": command[1:7],
                  "native_test_stdout": completed.stdout.strip()},
    }
    OUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(OUT),
                      "sha256": hashlib.sha256(OUT.read_bytes()).hexdigest(),
                      "oracle": "f_1B4E_0110", "cases": len(cases)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
