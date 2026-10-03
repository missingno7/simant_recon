#!/usr/bin/env python3
"""Strict native test for source S00 captures crossing the display bottom."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[4]
sys.path[:0] = [str(ROOT / "tools"), str(ROOT / "build" / "behavior" / "deps")]
import behavior  # noqa: E402
import functions  # noqa: E402
import unicorn  # noqa: E402
from unicorn.x86_const import UC_X86_INS_OUT  # noqa: E402

SOURCES = [
    "portable/whole_program/platform/graphics.c",
    "portable/whole_program/platform/graphics_capture_source.c",
    "portable/whole_program/platform/graphics_cursor_hooks.c",
    "portable/whole_program/platform/graphics_line_1499.c",
    "portable/whole_program/platform/graphics_source_clip.c",
    "portable/whole_program/platform/graphics_bitmap_source.c",
    "portable/whole_program/platform/graphics_tile_upload.c",
    "portable/whole_program/platform/m1b73_mouse_state.c",
    "portable/whole_program/window_source_globals.c",
    "portable/whole_program/platform/handles.c",
    "portable/whole_program/state/asm_display_data_v1.c",
    "portable/render/primitives.c",
    "portable/tests/whole_program/platform/graphics_capture_aperture_test.c",
]
INPUTS = SOURCES + [
    "portable/tests/whole_program/platform/run_graphics_capture_aperture_test.py",
    "portable/whole_program/platform/graphics_capture_source.h",
    "portable/whole_program/platform/graphics_tile_upload.h",
    "portable/whole_program/platform/graphics.h",
    "portable/whole_program/platform/handles.h",
    "portable/whole_program/platform/graphics_cursor_hooks.h",
    "portable/whole_program/platform/graphics_source_clip.h",
    "portable/whole_program/state/asm_display_data_v1.h",
    "portable/render/primitives.h",
    "tools/behavior.py", "tools/exe.py", "tools/functions.py", "tools/modctx.py",
    "layout/functions.json", "layout/symbols.json", "layout/manifest.json",
    "layout/oracle.lock.json", "src/S00/m31AD.asm", "src/root/m1B4E.asm",
    "src/root/m1B73.asm",
]

DOS_RECTS = {
    "capture-345-355": (424, 345, 448, 355),
    "capture-431-445": (424, 431, 448, 445),
    "capture-510-516": (424, 510, 448, 516),
    "capture-614-616": (424, 614, 448, 616),
}


def original_address(name: str) -> int:
    item = json.loads((ROOT / "layout/symbols.json").read_text(encoding="utf-8"))["data"][name]
    return item["seg"] * 16 + item["off"]


def source_planes() -> list[bytearray]:
    planes = [bytearray(0x10000) for _ in range(4)]
    for y in range(350):
        for x in range(640):
            color = (x * 3 + y * 5 + (x >> 2) + (y >> 1)) & 15
            offset = y * 80 + (x >> 3)
            mask = 0x80 >> (x & 7)
            for plane in range(4):
                if color & (1 << plane):
                    planes[plane][offset] |= mask
    map_source = bytes((0x43 ^ (i * 29)) & 0xff for i in range(0x8000))
    for row in range(0x100):
        row_source = map_source[row * 128:(row + 1) * 128]
        for plane in range(4):
            for out_byte in range(32):
                planes[plane][0xA000 + row * 32 + out_byte] = row_source[
                    (out_byte // 2) * 8 + plane * 2 + (out_byte & 1)]
    for plane in range(4):
        for offset in range(0x2000):
            planes[plane][0xC000 + offset] = (
                0x81 ^ plane * 0x35 ^ offset * 13) & 0xff
    return planes


def source_capture(rect: tuple[int, int, int, int], planes: list[bytearray]) -> bytes:
    pair = SimpleNamespace(function=functions.get("o00_31AD_0550"),
        sequence_targets=frozenset(),
        sequence_function=lambda target: functions.get(target), vectors={})
    machine = behavior.Machine(pair)
    gc_index = [0]
    plane_order: list[int] = []

    def on_out(cpu, port, size, value, _userdata):
        value &= (1 << (size * 8)) - 1
        if port == 0x3CE:
            gc_index[0] = value & 0xff
        elif port == 0x3CF and gc_index[0] == 4:
            selected = value & 3
            plane_order.append(selected)
            cpu.mem_write(0xA0000, bytes(planes[selected]))

    hook = machine.cpu.hook_add(unicorn.UC_HOOK_INSN, on_out, None, 1, 0,
                                UC_X86_INS_OUT)
    destination_segment, destination_offset = 0x7000, 0x0100
    left, top, right, bottom = rect
    writes = [
        (original_address("g_3DB0"), b"\x00\xa0"),
        (original_address("g_3DB6"), (80).to_bytes(2, "little")),
        (original_address("g_3DD4"), b"\x00\x00"),
        (original_address("g_4333"), b"\x01"),
        (original_address("g_4331"), b"\x00"),
        (original_address("g_4365"), b"\x00"),
        (original_address("g_4366"), b"\x01"),
    ]
    size = 4 + 4 * (((right - 1) >> 3) - (left >> 3) + 1) * (bottom - top)
    case = behavior.Case(label=f"source-aperture-{rect}",
        args=[left, top, right, bottom, destination_offset, destination_segment],
        writes=writes,
        observe=[behavior.Range("busy", original_address("g_3DD4"), 2)],
        return_kind="void", max_instructions=800000)
    try:
        machine.cpu.mem_write(0xA0000, bytes(planes[0]))
        result = machine.run(case)
        captured = bytes(machine.cpu.mem_read(destination_segment * 16 + destination_offset,
                                              size))
    finally:
        machine.cpu.hook_del(hook)
    if result["ranges"]["busy"] != "0000":
        raise RuntimeError("original _0550 leaked display busy depth")
    if plane_order != [p for _ in range(bottom - top) for p in range(4)]:
        raise RuntimeError(f"original _0550 plane order changed: {plane_order}")
    return captured


def fnv1a(data: bytes) -> str:
    value = 14695981039346656037
    for byte in data:
        value = ((value ^ byte) * 1099511628211) & 0xffffffffffffffff
    return f"{value:016x}"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--native-output", type=Path, required=True)
    args = parser.parse_args()
    report = args.report if args.report.is_absolute() else ROOT / args.report
    binary = args.native_output if args.native_output.is_absolute() else ROOT / args.native_output
    if report.exists() or binary.exists():
        raise SystemExit("refusing to overwrite capture-aperture evidence")
    report.parent.mkdir(parents=True, exist_ok=True)
    binary.parent.mkdir(parents=True, exist_ok=True)
    before = {name: sha(ROOT / name) for name in INPUTS}
    command = [os.environ.get("CC", "gcc"), "-std=c11", "-O2", "-Wall", "-Wextra",
               "-Wconversion", "-Werror", "-pedantic", "-I", str(ROOT),
               *[str(ROOT / name) for name in SOURCES], "-o", str(binary)]
    built = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    executed = None
    if built.returncode == 0:
        executed = subprocess.run([str(binary)], cwd=ROOT, capture_output=True,
                                  text=True, timeout=60)
    original_hashes: dict[str, str] = {}
    native_hashes: dict[str, str] = {}
    if executed is not None and executed.returncode == 0:
        planes = source_planes()
        original_hashes = {name: fnv1a(source_capture(rect, planes))
                           for name, rect in DOS_RECTS.items()}
        for line in executed.stdout.splitlines():
            if line.startswith("capture-") and "=" in line:
                name, value = line.split("=", 1)
                native_hashes[name] = value.strip()
    oracle_match = original_hashes == native_hashes
    after = {name: sha(ROOT / name) for name in INPUTS}
    passed = (built.returncode == 0 and executed is not None and
              executed.returncode == 0 and oracle_match and before == after)
    result = {
        "schema": "simant-s00-source-aperture-capture-test-v1",
        "status": "PASS" if passed else "FAIL",
        "scope": [
            "actual graphics_tile_upload 4x64KiB backing zeroes on source-video bind and receives real S00 page upload writes",
            "visible capture rows are reconstructed from the single SimGraphicsDriver indexed framebuffer",
            "off-visible rows are captured from the same source planar backing, including a visible/hidden crossing rectangle",
            "source g9148 uses handle-measured remaining capacity for an interior payload pointer",
            "generic checked capture remains display-bounded; bad capacity, owner, and aperture-end controls reject",
            "no claim that generic VGA/EGA hardware or historical uninitialized off-screen VRAM is emulated",
        ],
        "compiler": command[0],
        "compile_command": command,
        "compiler_stdout": built.stdout,
        "compiler_stderr": built.stderr,
        "native_stdout": executed.stdout if executed else "",
        "native_stderr": executed.stderr if executed else "",
        "native_exit_code": executed.returncode if executed else None,
        "original_dos_capture_fnv1a": original_hashes,
        "native_capture_fnv1a": native_hashes,
        "original_native_capture_match": oracle_match,
        "input_hashes_before": before,
        "input_hashes_after": after,
        "inputs_stable": before == after,
    }
    report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(result["status"])
    print(executed.stdout if executed else built.stderr)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
