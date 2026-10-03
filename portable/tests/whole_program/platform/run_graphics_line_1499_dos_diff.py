#!/usr/bin/env python3
"""Compare the S00 1499 line walk with a source-derived native implementation."""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import os
from pathlib import Path
import random
import shutil
import subprocess
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[4]
sys.path[:0] = [str(ROOT / "tools"), str(ROOT / "build" / "behavior" / "deps")]
import behavior  # noqa: E402
import functions  # noqa: E402
import unicorn  # noqa: E402
from unicorn.x86_const import UC_X86_INS_OUT  # noqa: E402

DOS_FB = 0xA0000
FB_WIDTH = 640
FB_HEIGHT = 480
ROW_BYTES = 80


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def addr(name: str) -> int:
    symbols = json.loads((ROOT / "layout/symbols.json").read_text(encoding="utf-8"))["data"]
    symbol = symbols[name]
    return symbol["seg"] * 16 + symbol["off"]


def original_machine():
    target = functions.get("o00_31AD_1499")
    pair = SimpleNamespace(function=target, sequence_targets=frozenset(),
                           sequence_function=lambda name: functions.get(name), vectors={})
    return behavior.Machine(pair)


def compile_native(output: Path):
    command = [os.environ.get("CC", "gcc"), "-std=c11", "-Wall", "-Wextra",
               "-Werror", "-pedantic", "-shared", "-fPIC", "-I", str(ROOT),
               str(ROOT / "portable/whole_program/platform/graphics_line_1499.c"),
               "-o", str(output)]
    subprocess.run(command, cwd=ROOT, check=True, capture_output=True, text=True)
    return command


def bind_native(path: Path):
    lib = ctypes.CDLL(str(path.resolve()))
    callback_type = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_int16, ctypes.c_int16)
    lib.sim_graphics_line_1499_pixels.argtypes = [ctypes.c_int16, ctypes.c_int16,
        ctypes.c_int16, ctypes.c_int16, callback_type, ctypes.c_void_p]
    lib.sim_graphics_line_1499_pixels.restype = ctypes.c_int
    return lib, callback_type


def native_events(lib, callback_type, points):
    events = []
    @callback_type
    def sink(_context, x, y):
        events.append((int(x), int(y)))
    x0, y0, x1, y1 = points
    count = lib.sim_graphics_line_1499_pixels(x0, y0, x1, y1, sink, None)
    if count != len(events):
        raise RuntimeError(f"native sink count {len(events)} != returned {count}")
    return events


def source_line(machine, points, color, rop, cursor_case=False):
    x0, y0, x1, y1 = points
    # Source row offsets are DATA, initialized by the display-driver setup;
    # provide the valid EGA/VGA linear row table as a controlled fixture.
    row_table = b"".join((y * ROW_BYTES).to_bytes(2, "little")
                          for y in range(FB_HEIGHT + 2))
    writes = [(addr("g_3DFC"), row_table),
              (addr("g_3DB4"), FB_HEIGHT.to_bytes(2, "little")),
              (addr("g_3DD2"), (rop & 0xff).to_bytes(2, "little")),
              (addr("g_4333"), bytes([0 if cursor_case else 1])),
              (addr("g_4366"), b"\x01"),
              (addr("g_4332"), b"\x00"),
              (addr("g_3DD4"), b"\x00\x00")]
    if cursor_case:
        # The source pretest uses this rectangle only to hide the cursor when
        # the line bounds overlap; it does not clip the line geometry.
        writes.extend([(addr("g_4340"), (100).to_bytes(2, "little")),
                       (addr("g_4342"), (100).to_bytes(2, "little")),
                       (addr("g_4344"), (200).to_bytes(2, "little")),
                       (addr("g_4346"), (200).to_bytes(2, "little")),
                       (addr("g_4365"), b"\x00")])

    gc_index = 0
    gc_regs = [0] * 9
    seq_index = 0
    seq_regs = [0] * 8
    pixel_events = []

    def on_out(cpu, port, size, value, _userdata):
        nonlocal gc_index, seq_index
        value &= (1 << (size * 8)) - 1
        if port == 0x3CE:
            gc_index = value & 0xff
        elif port == 0x3CF and gc_index < len(gc_regs):
            gc_regs[gc_index] = value & 0xff
        elif port == 0x3C4:
            seq_index = value & 0xff
        elif port == 0x3C5 and seq_index < len(seq_regs):
            seq_regs[seq_index] = value & 0xff

    def on_vram_write(_cpu, _access, address, size, _value, _userdata):
        if DOS_FB <= address < DOS_FB + 0x10000:
            offset = address - DOS_FB
            mask = gc_regs[8]
            if size != 1 or mask == 0 or mask & (mask - 1):
                raise RuntimeError(f"unexpected source VGA write: size={size} mask={mask:02x}")
            bit = mask.bit_length() - 1
            x = (offset % ROW_BYTES) * 8 + (7 - bit)
            y = offset // ROW_BYTES
            pixel_events.append((x, y, gc_regs[0] & 0x0f, gc_regs[3] & 0x18))

    out_hook = machine.cpu.hook_add(unicorn.UC_HOOK_INSN, on_out, None, 1, 0, UC_X86_INS_OUT)
    vram_hook = machine.cpu.hook_add(unicorn.UC_HOOK_MEM_WRITE, on_vram_write)
    case = behavior.Case(
        label=f"line-{points}-{rop:02x}", args=[x0, y0, x1, y1, color],
        writes=writes,
        observe=[behavior.Range("line_depth", addr("g_3DD4"), 2),
                 behavior.Range("cursor_hide_lock", addr("g_4332"), 1)],
        max_instructions=200000)
    try:
        result = machine.run(case)
    finally:
        machine.cpu.hook_del(out_hook)
        machine.cpu.hook_del(vram_hook)
    return pixel_events, result


def apply_logical_frame(events, color, rop):
    frame = bytearray(FB_WIDTH * FB_HEIGHT)
    for x, y, value, operation in events:
        if not (0 <= x < FB_WIDTH and 0 <= y < FB_HEIGHT):
            raise RuntimeError(f"source emitted off-screen normalized pixel {(x, y)}")
        offset = y * FB_WIDTH + x
        old = frame[offset]
        if operation == 0:
            frame[offset] = value
        elif operation == 0x08:
            frame[offset] = old & value
        elif operation == 0x10:
            frame[offset] = old | value
        elif operation == 0x18:
            frame[offset] = old ^ value
        else:
            raise RuntimeError(f"unreviewed VGA ROP {operation:02x}")
    return frame


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--native-output", type=Path,
                        default=Path("build/workers/recovered_tick_proof/graphics_line_1499.dll"))
    args = parser.parse_args()
    report_path = args.report if args.report.is_absolute() else ROOT / args.report
    dll = args.native_output if args.native_output.is_absolute() else ROOT / args.native_output
    report_path.parent.mkdir(parents=True, exist_ok=True)
    dll.parent.mkdir(parents=True, exist_ok=True)
    if report_path.exists() or dll.exists():
        raise SystemExit("refusing to overwrite an existing line differential artifact")

    source_inputs = [
        "portable/tests/whole_program/platform/run_graphics_line_1499_dos_diff.py",
        "portable/whole_program/platform/graphics_line_1499.c",
        "portable/whole_program/platform/graphics_line_1499.h",
        "tools/behavior.py", "tools/exe.py", "tools/functions.py", "tools/match.py",
        "tools/modctx.py", "tools/modules.py", "tools/omf.py",
        "layout/functions.json", "layout/symbols.json", "layout/manifest.json",
        "layout/oracle.lock.json", "src/S00/m31AD.asm", "src/S00/m3126.asm",
        "src/root/m1B4E.asm", "src/root/m1B73.asm"]
    input_hashes_before = {name: sha((ROOT / name).read_bytes()) for name in source_inputs}
    compiler_name = os.environ.get("CC", "gcc")
    compiler_path = shutil.which(compiler_name) or compiler_name
    compiler_version = subprocess.run([compiler_name, "--version"], check=True,
                                      capture_output=True, text=True).stdout.splitlines()[0]
    compiler_sha256 = sha(Path(compiler_path).read_bytes()) if Path(compiler_path).is_file() else None
    compile_command = compile_native(dll)
    lib, callback_type = bind_native(dll)
    common = [(320, 240, 329, 244), (320, 240, 324, 249),
              (320, 240, 316, 249), (320, 240, 311, 244),
              (320, 240, 311, 236), (320, 240, 316, 231),
              (320, 240, 324, 231), (320, 240, 329, 236),
              (320, 240, 328, 244), (328, 244, 320, 240),
              (320, 240, 324, 242), (320, 240, 328, 244),
              (320, 240, 320, 240), (0, 0, 8, 3),
              (639, 470, 630, 472), (320, 240, 320, 247),
              (320, 247, 320, 240), (100, 100, 180, 160),
              (300, 300, 340, 320)]
    rng = random.Random(0x1499_2026)
    random_points = [(rng.randrange(FB_WIDTH), rng.randrange(FB_HEIGHT),
                      rng.randrange(FB_WIDTH), rng.randrange(FB_HEIGHT))
                     for _ in range(64)]
    all_points = common + random_points
    cases = [(points, (index * 3 + 1) & 0x0f,
              (0, 0x08, 0x10, 0x18)[index % 4], index in (17, 18))
             for index, points in enumerate(all_points)]
    source = original_machine()
    rows, mismatches = [], []
    for index, (points, color, rop, cursor_case) in enumerate(cases):
        actual, result = source_line(source, points, color, rop, cursor_case)
        expected_xy = native_events(lib, callback_type, points)
        expected = [(x, y, color & 0x0f, rop) for x, y in expected_xy]
        expected_frame = apply_logical_frame(expected, color, rop)
        actual_frame = apply_logical_frame(actual, color, rop)
        x0, y0, x1, y1 = points
        cursor_overlap_expected = not (
            min(x0, x1) > 200 or max(x0, x1) < 100 or
            min(y0, y1) > 200 or max(y0, y1) < 100)
        expected_lock = "01" if cursor_case and cursor_overlap_expected else "00"
        row = {"index": index, "points": points, "color": color, "rop": rop,
               "cursor_pretest_enabled": cursor_case,
               "cursor_bounds_overlap_expected": cursor_overlap_expected,
               "pixel_write_count_original": len(actual),
               "pixel_write_count_native": len(expected),
               "pixel_writes_equal": actual == expected,
               "frame_sha256_original_normalized": sha(actual_frame),
               "frame_sha256_native_normalized": sha(expected_frame),
               "frame_equal": actual_frame == expected_frame,
               "observed_line_depth": result["ranges"]["line_depth"],
               "observed_cursor_lock": result["ranges"]["cursor_hide_lock"],
               "cursor_lock_matches_overlap": result["ranges"]["cursor_hide_lock"] == expected_lock,
               "source_vga_register_write_count": len(result["io"]),
               "pixel_writes_original": actual,
               "pixel_writes_native": expected}
        rows.append(row)
        if (not row["pixel_writes_equal"] or not row["frame_equal"] or
                not row["cursor_lock_matches_overlap"]):
            mismatch = {"row": row, "original_prefix": actual[:12],
                        "native_prefix": expected[:12]}
            mismatches.append(mismatch)

    input_hashes_after = {name: sha((ROOT / name).read_bytes()) for name in source_inputs}
    inputs_stable = input_hashes_before == input_hashes_after
    report = {
        "schema": "simant-s00-line-1499-dos-normalized-write-differential-v1",
        "status": "PASS" if not mismatches else "MISMATCH",
        "target": "o00_31AD_1499",
        "original_oracle": {"sha256": __import__("exe").load().sha256,
                            "emulator": f"Unicorn {unicorn.__version__}"},
        "native": {"command": compile_command, "compiler": compiler_name,
                   "compiler_path": compiler_path, "compiler_version": compiler_version,
                   "compiler_sha256": compiler_sha256, "dll_sha256": sha(dll.read_bytes())},
        "case_count": len(rows), "equal_count": sum(r["pixel_writes_equal"] and r["frame_equal"] for r in rows),
        "mismatch_count": len(mismatches),
        "inputs_before_sha256": input_hashes_before,
        "inputs_after_sha256": input_hashes_after,
        "inputs_stable": inputs_stable,
        "random_seed": "0x14992026", "random_case_count": len(random_points),
        "line_semantics": {
            "direction": "source swaps complete endpoints when x0>x1; emits left-to-right",
            "x_major_tie": "advance minor y only when accumulated minor exceeds floor(major/2)",
            "y_major_tie": "advance minor x only when accumulated minor exceeds floor(major/2)",
            "degenerate": "one pixel; vertical lines use the source dedicated byte-column loop",
            "cursor_pretest": "g_4333=0 may hide cursor for a bounding-box overlap; it does not clip the line",
            "framebuffer": "normalized VGA write stream is replayed into a zero-origin 640x480 indexed buffer; no VGA planar hardware is emulated",
        },
        "controlled_fixture": {
            "row_table": "g_3DFC initialized with 482 little-endian row offsets y*80",
            "row_table_sha256": sha(b"".join((y * ROW_BYTES).to_bytes(2, "little")
                                              for y in range(FB_HEIGHT + 2))),
            "video_segment": "A000h from original DATA initialization",
            "source_mode": "VGA mode 12h, g_3DB2=640, g_3DB4=480, g_3DB6=80",
            "planar_stride": "80 bytes from original DATA initialization",
            "cursor_test_rectangle": [100, 100, 200, 200],
            "initial_logical_pixel": 0,
        },
        "rows": rows, "mismatches": mismatches,
    }
    if not inputs_stable:
        report["status"] = "INVALID_INPUT_CHANGED"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"S00 line 1499 differential: {report['status']} ({report['equal_count']}/{len(rows)})")
    return 0 if not mismatches and inputs_stable else 1


if __name__ == "__main__":
    raise SystemExit(main())
