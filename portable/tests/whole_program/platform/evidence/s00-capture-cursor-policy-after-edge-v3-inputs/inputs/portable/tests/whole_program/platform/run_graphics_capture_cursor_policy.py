#!/usr/bin/env python3
"""Bound S00 capture cursor ordering against source m31AD and native hooks."""
from __future__ import annotations

import argparse
import ctypes
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

FB = 0xA0000
W, H, STRIDE = 640, 480, 80


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def address(name: str) -> int:
    symbols = json.loads((ROOT / "layout/symbols.json").read_text(encoding="utf-8"))["data"]
    symbol = symbols[name]
    return symbol["seg"] * 16 + symbol["off"]


def source_machine(name: str):
    pair = SimpleNamespace(function=functions.get(name), sequence_targets=frozenset(),
                           sequence_function=lambda target: functions.get(target), vectors={})
    return behavior.Machine(pair)


def compile_native(path: Path) -> list[str]:
    command = [os.environ.get("CC", "gcc"), "-std=c11", "-Wall", "-Wextra", "-Werror",
               "-pedantic", "-I", str(ROOT),
               str(ROOT / "portable/whole_program/platform/graphics.c"),
               str(ROOT / "portable/whole_program/platform/graphics_capture_source.c"),
               str(ROOT / "portable/whole_program/platform/graphics_cursor_hooks.c"),
               str(ROOT / "portable/whole_program/platform/graphics_line_1499.c"),
               str(ROOT / "portable/whole_program/platform/graphics_source_clip.c"),
               str(ROOT / "portable/whole_program/platform/m1b73_mouse_state.c"),
               str(ROOT / "portable/render/primitives.c"),
               str(ROOT / "portable/tests/whole_program/platform/graphics_capture_cursor_probe.c"),
               "-o", str(path)]
    subprocess.run(command, cwd=ROOT, check=True, capture_output=True, text=True)
    return command


def source_capture(machine, rect, *, lock, show, drawn, mouse_busy):
    left, top, right, bottom = rect
    trace: list[str] = []
    current_gc_index = 0
    planes = [bytearray(((((x * 3 + y * 5) ^ (x >> 2) ^ (y >> 1)) & 1)
                         << (plane % 4))
              for y in range(H) for x in range(W)) for plane in range(4)]

    def on_out(cpu, port, size, value, _userdata):
        nonlocal current_gc_index
        value &= (1 << (size * 8)) - 1
        if port == 0x3CE:
            current_gc_index = value & 0xff
        elif port == 0x3CF and current_gc_index == 4:
            cpu.mem_write(FB, bytes(planes[value & 3]))

    hook = machine.cpu.hook_add(unicorn.UC_HOOK_INSN, on_out, None, 1, 0,
                                UC_X86_INS_OUT)

    def source_hide(cpu, _args):
        trace.append("hide")
        cpu.cpu.mem_write(address("g_4332"), b"\x01")
        if show_state[0] > 0:
            show_state[0] -= 1
            cpu.cpu.mem_write(address("g_4365"), bytes((show_state[0],)))

    def source_update(cpu, _args):
        trace.append("update")
        cpu.cpu.mem_write(address("g_4332"), b"\x00")
        cpu.cpu.mem_write(address("g_4331"), b"\x00")
        show_state[0] = 1
        cpu.cpu.mem_write(address("g_4365"), b"\x01")

    def source_redraw(cpu, _args):
        trace.append("redraw")

    show_state = [show]
    callback_defs = {
        "f_1B73_0196": behavior.Callback(stack_words=0, handler=source_hide),
        "f_1B73_00D9": behavior.Callback(stack_words=0, handler=source_update),
        "f_1B73_04BB": behavior.Callback(stack_words=0, handler=source_redraw),
    }
    destination_segment, destination_offset = 0x7000, 0x0100
    writes = [
        (address("g_3DB0"), (FB >> 4).to_bytes(2, "little")),
        (address("g_3DB6"), STRIDE.to_bytes(2, "little")),
        (address("g_3DD4"), b"\x07\x5a"),
        (address("g_4333"), bytes((lock,))),
        (address("g_4331"), bytes((drawn,))),
        (address("g_4332"), b"\x00"),
        (address("g_4365"), bytes((show,))),
        (address("g_4366"), bytes((mouse_busy,))),
        (address("g_4340"), (10).to_bytes(2, "little")),
        (address("g_4342"), (20).to_bytes(2, "little")),
        (address("g_4344"), (30).to_bytes(2, "little")),
        (address("g_4346"), (25).to_bytes(2, "little")),
    ]
    observes = [
        behavior.Range("line_depth", address("g_3DD4"), 2),
        behavior.Range("cursor_state", address("g_4331"), 1),
        behavior.Range("pending", address("g_4332"), 1),
        behavior.Range("show_level", address("g_4365"), 1),
    ]
    case = behavior.Case(label=f"capture-policy-{rect}-lock{lock}-show{show}-drawn{drawn}-busy{mouse_busy}",
        args=[left, top, right, bottom, destination_offset, destination_segment],
        writes=writes, observe=observes, callbacks=callback_defs,
        return_kind="void", max_instructions=500000)
    try:
        result = machine.run(case)
    finally:
        machine.cpu.hook_del(hook)
    return {
        "rect": rect,
        "initial": {"lock": lock, "show": show, "drawn": drawn,
                    "mouse_busy": mouse_busy, "line_depth_word": "075a"},
        "calls": trace,
        "final": result["ranges"],
        "source_effect_trace": result["trace"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--native-output", type=Path,
                        default=Path("build/workers/recovered_tick_proof/graphics_capture_cursor_policy.exe"))
    args = parser.parse_args()
    report = args.report if args.report.is_absolute() else ROOT / args.report
    binary = args.native_output if args.native_output.is_absolute() else ROOT / args.native_output
    if report.exists() or binary.exists():
        raise SystemExit("refusing to overwrite capture cursor-policy evidence")
    report.parent.mkdir(parents=True, exist_ok=True)
    binary.parent.mkdir(parents=True, exist_ok=True)
    inputs = [
        "portable/tests/whole_program/platform/run_graphics_capture_cursor_policy.py",
        "portable/tests/whole_program/platform/graphics_capture_cursor_probe.c",
        "portable/whole_program/platform/graphics_capture_source.h",
        "portable/whole_program/platform/graphics_capture_source.c",
        "portable/whole_program/platform/graphics_cursor_hooks.h",
        "portable/whole_program/platform/graphics_cursor_hooks.c",
        "portable/whole_program/platform/graphics.h",
        "portable/whole_program/platform/graphics.c",
        "portable/whole_program/platform/graphics_line_1499.h",
        "portable/whole_program/platform/graphics_line_1499.c",
        "portable/whole_program/platform/graphics_source_clip.h",
        "portable/whole_program/platform/graphics_source_clip.c",
        "portable/whole_program/platform/m1b73_mouse_state.h",
        "portable/whole_program/platform/m1b73_mouse_state.c",
        "portable/whole_program/window_source_rects.h",
        "portable/render/primitives.h", "portable/render/primitives.c",
        "tools/behavior.py", "tools/exe.py", "tools/functions.py", "tools/match.py",
        "tools/modctx.py", "tools/modules.py", "layout/functions.json", "layout/symbols.json",
        "layout/manifest.json", "layout/oracle.lock.json", "src/S00/m31AD.asm",
        "src/S00/m3126.asm", "src/root/m1B4E.asm", "src/root/m1B73.asm",
    ]
    before = {p: sha((ROOT / p).read_bytes()) for p in inputs}
    source = source_machine("o00_31AD_0550")
    cases = [
        source_capture(source, (25, 30, 33, 32), lock=0, show=1, drawn=1, mouse_busy=0),
        source_capture(source, (100, 100, 108, 102), lock=0, show=1, drawn=1, mouse_busy=0),
        source_capture(source, (10, 20, 18, 22), lock=1, show=1, drawn=1, mouse_busy=0),
        source_capture(source, (100, 100, 108, 102), lock=0, show=0, drawn=0, mouse_busy=0),
        source_capture(source, (100, 100, 108, 102), lock=0, show=0, drawn=0, mouse_busy=1),
    ]
    expected_calls = [["hide", "update"], ["redraw"], [], ["update"], []]
    source_pass = [row["calls"] == expected for row, expected in zip(cases, expected_calls)]
    expected_state = [
        {"line_depth": "075a", "cursor_state": "00", "pending": "00", "show_level": "01"},
        {"line_depth": "075a", "cursor_state": "01", "pending": "00", "show_level": "01"},
        {"line_depth": "075a", "cursor_state": "01", "pending": "00", "show_level": "01"},
        {"line_depth": "075a", "cursor_state": "00", "pending": "00", "show_level": "01"},
        {"line_depth": "075a", "cursor_state": "00", "pending": "00", "show_level": "00"},
    ]
    source_state_pass = [row["final"] == expected
                         for row, expected in zip(cases, expected_state)]
    command = compile_native(binary)
    native = subprocess.run([str(binary)], cwd=ROOT, capture_output=True, text=True)
    if native.returncode != 0:
        raise SystemExit(f"native positive controls failed ({native.returncode}): {native.stderr}")
    missing = subprocess.run([str(binary), "--missing-hook"], cwd=ROOT,
                             capture_output=True, text=True)
    if missing.returncode != 70 or "requires bound source cursor-hide service" not in missing.stderr:
        raise SystemExit("missing cursor-hide service did not fail closed")
    after = {p: sha((ROOT / p).read_bytes()) for p in inputs}
    if before != after:
        raise SystemExit("pinned source inputs changed during capture policy run")
    report_data = {
        "schema": "portable-s00-capture-cursor-policy-v1",
        "scope": "Original o00_31AD_0550 call-site ordering against native g9148 cursor-hook ordering; mouse hook internals are existing separately reviewed m1B73 providers.",
        "source_entry": "src/S00/m31AD.asm:_o00_31AD_0550",
        "source_callback_order": ["optional f_1B73_0196 before planar copy", "planar copy", "conditional f_1B73_04BB or f_1B73_00D9 after copy", "decrement low byte g_3DD4"],
        "coordinate_aliases": {"g_4344": "cursor bottom", "g_4346": "cursor right", "basis": "m1B73.asm _0DA4 stores y+height at g4344 and aligned x+width+7 at g4346; m31AD.asm _0550 compares top/bottom and left/right in that order"},
        "source_controls": cases,
        "source_expected_calls": expected_calls,
        "source_controls_pass": source_pass,
        "source_expected_final_state": expected_state,
        "source_final_state_pass": source_state_pass,
        "native_controls": {"passed": native.returncode == 0, "stdout": native.stdout.strip(), "missing_service_exit": missing.returncode, "missing_service_stderr": missing.stderr.strip()},
        "native_compile_command": command,
        "inputs_sha256_before": before,
        "inputs_sha256_after": after,
    }
    if not all(source_pass) or not all(source_state_pass):
        raise SystemExit("original source capture cursor order/final-state control mismatch")
    report.write_text(json.dumps(report_data, indent=2) + "\n", encoding="utf-8")
    print(f"source/native capture cursor policy PASS ({len(cases)} source controls; 5 native controls; missing-service fail-closed)")
    print(f"report: {report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
