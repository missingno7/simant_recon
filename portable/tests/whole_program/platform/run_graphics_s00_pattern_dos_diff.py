#!/usr/bin/env python3
"""Bounded original S00 patterned-rectangle vs native framebuffer differential."""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[4]
sys.path[:0] = [str(ROOT / "tools"), str(ROOT / "build" / "behavior" / "deps")]
import behavior  # noqa: E402
import functions  # noqa: E402
import unicorn  # noqa: E402
from unicorn.x86_const import UC_X86_INS_OUT  # noqa: E402

DOS_FB = 0xA0000
WIDTH = 640
HEIGHT = 480
ROW_BYTES = 80


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def addr(name: str) -> int:
    symbol = json.loads((ROOT / "layout/symbols.json").read_text(encoding="utf-8"))["data"][name]
    return symbol["seg"] * 16 + symbol["off"]


def compile_native(output: Path) -> list[str]:
    command = [os.environ.get("CC", "gcc"), "-std=c11", "-Wall", "-Wextra",
               "-Werror", "-pedantic", "-shared", "-fPIC", "-I", str(ROOT),
               str(ROOT / "portable/whole_program/platform/graphics.c"),
               str(ROOT / "portable/whole_program/platform/graphics_line_1499.c"),
               str(ROOT / "portable/render/primitives.c"),
               str(ROOT / "portable/tests/whole_program/platform/graphics_s00_rect_probe.c"),
               "-o", str(output)]
    subprocess.run(command, cwd=ROOT, check=True, capture_output=True, text=True)
    return command


def bind_native(path: Path):
    lib = ctypes.CDLL(str(path.resolve()))
    lib.sim_graphics_s00_pattern_probe.argtypes = [
        ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t,
        ctypes.c_int16, ctypes.c_int16, ctypes.c_int16, ctypes.c_int16,
        ctypes.c_int16, ctypes.c_uint8, ctypes.c_uint8,
        ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t,
    ]
    lib.sim_graphics_s00_pattern_probe.restype = ctypes.c_int
    lib.sim_graphics_s00_xor_probe.argtypes = [
        ctypes.c_int16, ctypes.c_int16, ctypes.c_int16, ctypes.c_int16,
        ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t,
    ]
    lib.sim_graphics_s00_xor_probe.restype = ctypes.c_int
    return lib


def original_machine():
    target = functions.get("o00_31AD_0122")
    pair = SimpleNamespace(function=target, sequence_targets=frozenset(),
                           sequence_function=lambda name: functions.get(name), vectors={})
    return behavior.Machine(pair)


def source_xor_machine():
    target = functions.get("o00_31AD_037C")
    pair = SimpleNamespace(function=target, sequence_targets=frozenset(),
                           sequence_function=lambda name: functions.get(name), vectors={})
    return behavior.Machine(pair)


def source_pattern_case(machine, rect, pattern_word, foreground, background):
    left, top, right, bottom = rect
    row_table = b"".join((y * ROW_BYTES).to_bytes(2, "little") for y in range(HEIGHT + 2))
    writes = [
        (addr("g_3DFC"), row_table),
        (addr("g_3DB4"), HEIGHT.to_bytes(2, "little")),
        (addr("g_3DE0"), bytes((foreground, 0))),
        (addr("g_3DE2"), bytes((background,))),
        (addr("g_4333"), b"\x01"),  # cursor-hide pretest is disabled, not geometry clipping
        (addr("g_4366"), b"\x01"),
        (addr("g_3DD4"), b"\x00\x00"),
        (addr("g_5AAE"), b"\x00\x00"),  # select the real local S00 body
    ]
    gc_index = 0
    seq_index = 0
    gc = [0] * 9
    seq = [0] * 8
    pixel_writes = []

    def on_out(_cpu, port, size, value, _userdata):
        nonlocal gc_index, seq_index
        value &= (1 << (size * 8)) - 1
        if port == 0x3CE:
            gc_index = value & 0xff
        elif port == 0x3CF and gc_index < len(gc):
            gc[gc_index] = value & 0xff
        elif port == 0x3C4:
            seq_index = value & 0xff
        elif port == 0x3C5 and seq_index < len(seq):
            seq[seq_index] = value & 0xff

    def on_vram_write(_cpu, _access, address_value, size, value, _userdata):
        if not DOS_FB <= address_value < DOS_FB + 0x10000:
            return
        if size != 1:
            raise RuntimeError(f"unexpected VRAM write size {size}")
        if gc[5] != 0 or gc[1] != 0x0f or seq[2] != 0x0f:
            raise RuntimeError(f"pattern body used unsupported VGA state: gc={gc}, seq={seq}")
        offset = address_value - DOS_FB
        bit_mask = gc[8]
        byte_x = offset % ROW_BYTES
        y = offset // ROW_BYTES
        color = gc[0] & 0x0f
        for bit in range(8):
            if bit_mask & (1 << bit):
                x = byte_x * 8 + (7 - bit)
                pixel_writes.append((x, y, color))

    out_hook = machine.cpu.hook_add(unicorn.UC_HOOK_INSN, on_out, None, 1, 0,
                                    UC_X86_INS_OUT)
    vram_hook = machine.cpu.hook_add(unicorn.UC_HOOK_MEM_WRITE, on_vram_write)
    machine.cpu.mem_write(DOS_FB, bytes(0x10000))
    case = behavior.Case(label=f"rect-{rect}-pattern-{pattern_word & 0x0f}",
                         args=[left, top, right, bottom, pattern_word], writes=writes,
                         observe=[behavior.Range("depth", addr("g_3DD4"), 2)],
                         max_instructions=500000)
    try:
        result = machine.run(case)
    finally:
        machine.cpu.hook_del(out_hook)
        machine.cpu.hook_del(vram_hook)
    if result["ranges"]["depth"] != "0000":
        raise RuntimeError(f"source primitive leaked line depth: {result['ranges']}")
    frame = bytearray(WIDTH * HEIGHT)
    for x, y, color in pixel_writes:
        if not (0 <= x < WIDTH and 0 <= y < HEIGHT):
            raise RuntimeError(f"source emitted out-of-range pixel {(x, y)}")
        frame[y * WIDTH + x] = color
    return bytes(frame), pixel_writes, result


def native_pattern_case(lib, patterns, rect, pattern_word, foreground, background):
    pattern_buffer = (ctypes.c_uint8 * len(patterns)).from_buffer_copy(patterns)
    output = (ctypes.c_uint8 * (WIDTH * HEIGHT))()
    status = lib.sim_graphics_s00_pattern_probe(
        pattern_buffer, len(patterns), *rect, pattern_word,
        foreground, background, output, len(output))
    if status != 0:
        raise RuntimeError(f"native pattern provider returned status {status}")
    return bytes(output)


def source_xor_case(machine, rect):
    left, top, right, bottom = rect
    row_table = b"".join((y * ROW_BYTES).to_bytes(2, "little") for y in range(HEIGHT + 2))
    writes = [
        (addr("g_3DFC"), row_table),
        (addr("g_3DB4"), HEIGHT.to_bytes(2, "little")),
        (addr("g_4333"), b"\x01"),
        (addr("g_4366"), b"\x01"),
        (addr("g_3DD4"), b"\x00\x00"),
        (addr("g_5AAE"), b"\x00\x00"),
    ]
    gc_index = 0
    seq_index = 0
    gc = [0] * 9
    seq = [0] * 8
    pixel_writes = []

    def on_out(_cpu, port, size, value, _userdata):
        nonlocal gc_index, seq_index
        value &= (1 << (size * 8)) - 1
        if port == 0x3CE:
            gc_index = value & 0xff
        elif port == 0x3CF and gc_index < len(gc):
            gc[gc_index] = value & 0xff
        elif port == 0x3C4:
            seq_index = value & 0xff
        elif port == 0x3C5 and seq_index < len(seq):
            seq[seq_index] = value & 0xff

    def on_vram_write(_cpu, _access, address_value, size, _value, _userdata):
        if not DOS_FB <= address_value < DOS_FB + 0x10000:
            return
        if size != 1:
            raise RuntimeError(f"unexpected VRAM write size {size}")
        if gc[5] != 0 or gc[1] != 0x0f or gc[3] != 0x18 or seq[2] != 0x0f:
            raise RuntimeError(f"rect body used unsupported VGA state: gc={gc}, seq={seq}")
        offset = address_value - DOS_FB
        bit_mask = gc[8]
        color = gc[0] & 0x0f
        for bit in range(8):
            if bit_mask & (1 << bit):
                pixel_writes.append(((offset % ROW_BYTES) * 8 + (7 - bit),
                                     offset // ROW_BYTES, color))

    out_hook = machine.cpu.hook_add(unicorn.UC_HOOK_INSN, on_out, None, 1, 0,
                                    UC_X86_INS_OUT)
    vram_hook = machine.cpu.hook_add(unicorn.UC_HOOK_MEM_WRITE, on_vram_write)
    machine.cpu.mem_write(DOS_FB, bytes(0x10000))
    case = behavior.Case(label=f"xor-rect-{rect}", args=[left, top, right, bottom],
                         writes=writes,
                         observe=[behavior.Range("depth", addr("g_3DD4"), 2)],
                         max_instructions=500000)
    try:
        result = machine.run(case)
    finally:
        machine.cpu.hook_del(out_hook)
        machine.cpu.hook_del(vram_hook)
    frame = bytearray(WIDTH * HEIGHT)
    for x, y, mask in pixel_writes:
        if not (0 <= x < WIDTH and 0 <= y < HEIGHT):
            raise RuntimeError(f"source emitted out-of-range XOR pixel {(x, y)}")
        frame[y * WIDTH + x] ^= mask
    return bytes(frame), pixel_writes, result


def native_xor_case(lib, rect):
    output = (ctypes.c_uint8 * (WIDTH * HEIGHT))()
    status = lib.sim_graphics_s00_xor_probe(*rect, output, len(output))
    if status != 0:
        raise RuntimeError(f"native XOR provider returned status {status}")
    return bytes(output)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--native-output", type=Path,
                        default=Path("build/workers/recovered_tick_proof/graphics_s00_pattern.dll"))
    args = parser.parse_args()
    report = args.report if args.report.is_absolute() else ROOT / args.report
    dll = args.native_output if args.native_output.is_absolute() else ROOT / args.native_output
    report.parent.mkdir(parents=True, exist_ok=True)
    dll.parent.mkdir(parents=True, exist_ok=True)
    if report.exists() or dll.exists():
        raise SystemExit("refusing to overwrite a pattern differential artifact")

    source_names = [
        "portable/tests/whole_program/platform/run_graphics_s00_pattern_dos_diff.py",
        "portable/tests/whole_program/platform/graphics_s00_rect_probe.c",
        "portable/whole_program/platform/graphics.h",
        "portable/whole_program/platform/graphics.c",
        "portable/whole_program/platform/graphics_line_1499.h",
        "portable/whole_program/platform/graphics_line_1499.c",
        "portable/render/primitives.h", "portable/render/primitives.c",
        "tools/behavior.py", "tools/exe.py", "tools/functions.py", "tools/match.py",
        "tools/modctx.py", "tools/modules.py", "tools/omf.py",
        "layout/functions.json", "layout/symbols.json", "layout/manifest.json",
        "layout/oracle.lock.json", "src/S00/m31AD.asm", "src/S00/m3126.asm",
        "src/root/m1B4E.asm", "src/root/m1B73.asm",
    ]
    before = {name: sha((ROOT / name).read_bytes()) for name in source_names}
    compiler = os.environ.get("CC", "gcc")
    compiler_path = shutil.which(compiler) or compiler
    compiler_version = subprocess.run([compiler, "--version"], check=True,
                                      capture_output=True, text=True).stdout.splitlines()[0]
    compiler_sha = sha(Path(compiler_path).read_bytes()) if Path(compiler_path).is_file() else None
    command = compile_native(dll)
    lib = bind_native(dll)
    source = original_machine()
    pattern_view = bytes(source.cpu.mem_read(addr("g_41C0") + 16, 256))
    cases = [
        ((1, 2, 5, 4), 0x20, 5, 2),
        ((7, 0, 19, 8), 0x23, 5, 2),
        ((0, 0, 16, 8), 0x2a, 9, 1),
        ((13, 6, 2, 1), 0x2f, 12, 3),
        ((639, 478, 640, 480), 0x21, 4, 6),
    ]
    cases.extend(((1, 1, 23, 11), pattern | 0x20, (pattern + 3) & 0x0f,
                  (pattern * 7 + 2) & 0x0f) for pattern in range(16))
    rows = []
    for rect, pattern_word, foreground, background in cases:
        original_frame, source_events, source_result = source_pattern_case(
            source, rect, pattern_word, foreground, background)
        native_frame = native_pattern_case(lib, pattern_view, rect, pattern_word,
                                           foreground, background)
        row = {
            "rect": rect,
            "pattern_word": pattern_word,
            "pattern_index": pattern_word & 0x0f,
            "foreground": foreground,
            "background": background,
            "source_pixel_write_count": len(source_events),
            "source_first_pixel_writes": source_events[:24],
            "normalized_frame_sha256_source": sha(original_frame),
            "normalized_frame_sha256_native": sha(native_frame),
            "frame_equal": original_frame == native_frame,
            "source_depth_after": source_result["ranges"]["depth"],
        }
        rows.append(row)
    xor_cases = [(1, 2, 5, 4), (7, 0, 19, 8), (13, 6, 2, 1),
                 (639, 478, 640, 480), (20, 20, 20, 24), (30, 31, 38, 31)]
    xor_source = source_xor_machine()
    xor_rows = []
    for rect in xor_cases:
        original_frame, source_events, source_result = source_xor_case(xor_source, rect)
        native_frame = native_xor_case(lib, rect)
        xor_rows.append({
            "rect": rect,
            "xor_color": 15,
            "source_pixel_write_count": len(source_events),
            "source_first_pixel_writes": source_events[:24],
            "normalized_frame_sha256_source": sha(original_frame),
            "normalized_frame_sha256_native": sha(native_frame),
            "frame_equal": original_frame == native_frame,
            "source_depth_after": source_result["ranges"]["depth"],
        })
    after = {name: sha((ROOT / name).read_bytes()) for name in source_names}
    mismatches = [row for row in rows + xor_rows if not row["frame_equal"]]
    result = {
        "schema": "simant-s00-patterned-rectangle-dos-native-v1",
        "status": "PASS" if not mismatches and before == after else "FAIL",
        "scope": [
            "source body o00_31AD_0122 through its no-overlay local _013A path",
            "pattern data is read from original DATA g_41C0+16 in the DOS VM and passed as a view to native code",
            "source VGA plane writes are normalized to indexed pixels only for this accepted GC mode/set-reset mask",
            "bounded nonnegative 640x480 half-open rectangle fixtures and source pattern indices 0..15",
            "source body o00_31AD_037C through its no-overlay local _0394 path, with GFX XOR/set-reset semantics",
            "does not claim overlay-resident rendering or a complete VGA device model",
        ],
        "compiler": compiler,
        "compiler_version": compiler_version,
        "compiler_sha256": compiler_sha,
        "compile_command": command,
        "original_pattern_view_sha256": sha(pattern_view),
        "inputs_before_sha256": before,
        "inputs_after_sha256": after,
        "inputs_stable": before == after,
        "case_count": len(rows),
        "cases": rows,
        "xor_case_count": len(xor_rows),
        "xor_cases": xor_rows,
        "mismatches": mismatches[:4],
    }
    report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"original S00 pattern rectangle differential: {result['status']} ({len(rows)} cases)")
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
