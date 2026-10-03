#!/usr/bin/env python3
"""Compare the original S00 edge capture with bounded native cursor padding."""
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

WIDTH, HEIGHT, STRIDE = 640, 480, 80
LEFT, TOP, RIGHT, BOTTOM = 632, 478, 655, 510
BUFFER_SEGMENT, BUFFER_OFFSET = 0x7000, 0x0100
BUFFER_SIZE = 4 + 3 * 32 * 4

NATIVE_SOURCES = [
    "portable/whole_program/platform/graphics.c",
    "portable/whole_program/platform/graphics_capture_source.c",
    "portable/whole_program/platform/graphics_cursor_hooks.c",
    "portable/whole_program/platform/graphics_line_1499.c",
    "portable/whole_program/platform/graphics_source_clip.c",
    "portable/whole_program/platform/m1b73_mouse_state.c",
    "portable/render/primitives.c",
    "portable/tests/whole_program/platform/graphics_capture_edge_test.c",
]
SOURCE_INPUTS = [
    "portable/tests/whole_program/platform/run_graphics_capture_edge_test.py",
    *NATIVE_SOURCES,
    "portable/whole_program/platform/graphics_capture_source.h",
    "portable/whole_program/platform/graphics_entry_source.h",
    "portable/whole_program/platform/graphics_source_clip.h",
    "portable/whole_program/platform/graphics_cursor_hooks.h",
    "portable/whole_program/platform/m1b73_mouse_state.h",
    "portable/whole_program/platform/graphics.h",
    "portable/render/primitives.h",
    "tools/behavior.py", "tools/exe.py", "tools/functions.py", "tools/match.py",
    "tools/modctx.py", "tools/modules.py",
    "layout/functions.json", "layout/symbols.json", "layout/manifest.json",
    "layout/oracle.lock.json", "src/S00/m31AD.asm", "src/S00/m3126.asm",
    "src/root/m1B4E.asm", "src/root/m1B73.asm", "src/root/m1D8E.c",
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def address(name: str) -> int:
    symbols = json.loads((ROOT / "layout/symbols.json").read_text(encoding="utf-8"))["data"]
    item = symbols[name]
    return item["seg"] * 16 + item["off"]


def pixel(x: int, y: int) -> int:
    return (x * 3 + y * 5 + (x >> 2) + (y >> 1)) & 15


def source_capture() -> bytes:
    pair = SimpleNamespace(function=functions.get("o00_31AD_0550"),
        sequence_targets=frozenset(),
        sequence_function=lambda target: functions.get(target), vectors={})
    machine = behavior.Machine(pair)
    planes = []
    for plane in range(4):
        plane_bytes = bytearray(STRIDE * HEIGHT)
        for y in range(HEIGHT):
            for byte_x in range(STRIDE):
                packed = 0
                for bit in range(8):
                    if pixel(byte_x * 8 + bit, y) & (1 << plane):
                        packed |= 0x80 >> bit
                plane_bytes[y * STRIDE + byte_x] = packed
        planes.append(plane_bytes)
    gc_index = [0]

    def on_out(cpu, port, size, value, _userdata):
        value &= (1 << (size * 8)) - 1
        if port == 0x3CE:
            gc_index[0] = value & 0xff
        elif port == 0x3CF and gc_index[0] == 4:
            cpu.mem_write(0xA0000, bytes(planes[value & 3]))

    hook = machine.cpu.hook_add(unicorn.UC_HOOK_INSN, on_out, None, 1, 0,
                                UC_X86_INS_OUT)
    dest = BUFFER_SEGMENT * 16 + BUFFER_OFFSET
    writes = [
        (address("g_3DB0"), (0xA000).to_bytes(2, "little")),
        (address("g_3DB6"), STRIDE.to_bytes(2, "little")),
        (address("g_3DD4"), b"\x07\x5a"),
        (address("g_4333"), b"\x01"), # source update lock: no cursor callbacks
        (address("g_4331"), b"\x00"), (address("g_4365"), b"\x00"),
        (address("g_4366"), b"\x01"),
    ]
    case = behavior.Case(label="cursor-capture-edge-right-bottom",
        args=[LEFT, TOP, RIGHT, BOTTOM, BUFFER_OFFSET, BUFFER_SEGMENT],
        writes=writes,
        observe=[behavior.Range("saved", dest, BUFFER_SIZE),
                 behavior.Range("busy", address("g_3DD4"), 2)],
        callbacks={}, return_kind="void", max_instructions=800000)
    try:
        result = machine.run(case)
    finally:
        machine.cpu.hook_del(hook)
    if result["ranges"]["busy"] != "075a":
        raise RuntimeError("DOS capture did not restore the source busy word")
    return bytes.fromhex(result["ranges"]["saved"])


def check_visible_dos_capture(capture: bytes) -> tuple[int, int]:
    if capture[:4] != bytes((24, 0, 32, 0)) or len(capture) != BUFFER_SIZE:
        raise RuntimeError("DOS save-under header/size differs from S00 byte geometry")
    compared = 0
    for row in range(2):
        y = TOP + row
        for plane in range(4):
            actual = capture[4 + row * 12 + plane * 3]
            expected = 0
            for bit in range(8):
                if pixel(LEFT + bit, y) & (1 << plane):
                    expected |= 0x80 >> bit
            if actual != expected:
                raise RuntimeError(f"visible DOS plane mismatch row={row} plane={plane}")
            compared += 8
    return compared, sum(byte != 0 for byte in capture[4:])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--native-output", type=Path,
        default=Path("build/workers/recovered_tick_proof/graphics_capture_edge_test_v1.exe"))
    args = parser.parse_args()
    report = args.report if args.report.is_absolute() else ROOT / args.report
    binary = args.native_output if args.native_output.is_absolute() else ROOT / args.native_output
    if report.exists() or binary.exists():
        raise SystemExit("refusing to overwrite graphics capture edge artifacts")
    report.parent.mkdir(parents=True, exist_ok=True)
    binary.parent.mkdir(parents=True, exist_ok=True)
    before = {name: sha(ROOT / name) for name in SOURCE_INPUTS}
    compiler = os.environ.get("CC", "gcc")
    command = [compiler, "-std=c11", "-Wall", "-Wextra", "-Wconversion",
        "-Werror", "-pedantic", "-I", str(ROOT),
        *[str(ROOT / name) for name in NATIVE_SOURCES], "-o", str(binary)]
    built = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    native = None
    if built.returncode == 0:
        native = subprocess.run([str(binary)], cwd=ROOT,
                                capture_output=True, text=True, timeout=20)
    dos_capture = source_capture()
    visible_bits, source_nonzero_payload_bytes = check_visible_dos_capture(dos_capture)
    after = {name: sha(ROOT / name) for name in SOURCE_INPUTS}
    passed = (built.returncode == 0 and native is not None and
              native.returncode == 0 and before == after)
    result = {
        "schema": "simant-s00-cursor-edge-capture-v1",
        "status": "PASS" if passed else "FAIL",
        "scope": [
            "original DOS o00_31AD_0550 capture at right and bottom screen edges",
            "native cursor-only pointer/capacity authorization for exterior padding",
            "generic capture validation remains screen-bounded",
            "visible DOS plane bits checked against the same source pixel fixture",
            "native cursor show/hide full-draw restore is tested separately",
            "sourceclip behavior is derived from f_1D8E_07F6/070E sentinel loop; no pixel claim here",
        ],
        "rectangle": [LEFT, TOP, RIGHT, BOTTOM],
        "screen": [WIDTH, HEIGHT],
        "source_capture_header": [24, 32],
        "source_capture_bytes": BUFFER_SIZE,
        "visible_dos_bits_checked": visible_bits,
        "nonzero_dos_payload_bytes_including_exterior": source_nonzero_payload_bytes,
        "native_stdout": native.stdout if native else "",
        "native_stderr": native.stderr if native else "",
        "native_exit_code": native.returncode if native else None,
        "compiler_stdout": built.stdout,
        "compiler_stderr": built.stderr,
        "compile_command": command,
        "source_hashes_before": before,
        "source_hashes_after": after,
        "inputs_stable": before == after,
    }
    report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(result["status"])
    print(native.stdout if native else built.stderr)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
