#!/usr/bin/env python3
"""Compare the portable S26 constraint model to original DOS o26_39C7_022F."""
from __future__ import annotations

import ctypes
import hashlib
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))
import behavior  # noqa: E402
import exe  # noqa: E402
import functions  # noqa: E402


class Rect(ctypes.Structure):
    _fields_ = [(name, ctypes.c_int16) for name in ("left", "top", "right", "bottom")]


class ZoomState(ctypes.Structure):
    _fields_ = [("window_rect", Rect), ("frame_rect", Rect), ("zoom_rect", Rect),
                ("flags", ctypes.c_uint16), ("min_width", ctypes.c_int16),
                ("min_height", ctypes.c_int16), ("grid_x", ctypes.c_int16),
                ("grid_y", ctypes.c_int16), ("has_zoom_rect", ctypes.c_uint8)]


class Bounds(ctypes.Structure):
    _fields_ = [(name, ctypes.c_int16)
                for name in ("desktop_top", "screen_right", "screen_bottom")]


def words(*values: int) -> bytes:
    return struct.pack("<" + "H" * len(values), *(v & 0xFFFF for v in values))


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def run_case(lib, case: dict) -> dict:
    fn = functions.get("o26_39C7_022F")
    pair = type("Pair", (), {})()
    pair.function = fn
    pair.vectors = {exe.MANAGER_SEG * 16 + v.offset: v for v in exe.load().vectors}
    pair.candidate = False
    pair.sequence_targets = set()
    pair.sequence_function = lambda name: functions.get(name)
    machine = behavior.Machine(pair)
    faddr = functions.get("f_22BF_0B5B")
    entry_args = []
    writes_trace = []
    call_args = []
    flinear = faddr["seg"] * 16 + faddr["off"]
    def on_code(uc, address, _size, _user):
        if address == flinear:
            sp = uc.reg_read(behavior.REGS["sp"])
            ss = uc.reg_read(behavior.REGS["ss"])
            stack = machine.read(ss * 16 + sp + 4, 8)
            call_args.append({"ax": uc.reg_read(behavior.REGS["ax"]),
                              "dx": uc.reg_read(behavior.REGS["dx"]),
                              "bx": uc.reg_read(behavior.REGS["bx"]),
                              "cx": uc.reg_read(behavior.REGS["cx"]),
                              "si": uc.reg_read(behavior.REGS["si"]),
                              "di": uc.reg_read(behavior.REGS["di"]),
                              "stack": stack.hex()})
    machine.cpu.hook_add(behavior.uc.UC_HOOK_CODE, on_code)
    entry = fn["seg"] * 16 + fn["off"]
    def on_entry(uc, address, _size, _user):
        if address == entry:
            sp = uc.reg_read(behavior.REGS["sp"])
            ss = uc.reg_read(behavior.REGS["ss"])
            entry_args.append({"ax": uc.reg_read(behavior.REGS["ax"]),
                               "dx": uc.reg_read(behavior.REGS["dx"]),
                               "stack": machine.read(ss * 16 + sp + 4, 8).hex()})
    machine.cpu.hook_add(behavior.uc.UC_HOOK_CODE, on_entry)
    def on_mem_write(_uc, _access, address, size, value, _user):
        if rect_addr <= address < rect_addr + 8:
            writes_trace.append({"address": address, "size": size, "value": value})
    machine.cpu.hook_add(behavior.uc.UC_HOOK_MEM_WRITE, on_mem_write)

    win_addr, rect_addr = 0xD0100, 0xD0200
    callbacks = {
        "win_WinAddr": behavior.Callback(0, lambda _m, _a: (win_addr & 15, win_addr >> 4), ("ax",)),
        "win_WinRectAddr": behavior.Callback(0, lambda _m, _a: (win_addr & 15, win_addr >> 4), ("ax",)),
    }
    source_win = words(*case["window_rect"]) + bytes(4) + words(0) + bytes(10) + \
        words(case["min_width"], case["min_height"], case["flags"]) + bytes(2) + \
        words(case["grid_x"], case["grid_y"]) + bytes(8)
    writes = [
        (win_addr, source_win),
        (rect_addr, words(*case["rect"])),
        (behavior.symbol_address("fd_50F6_393C"), words(0, 0, 0, case["desktop_top"])),
        (behavior.symbol_address("g_3DB2"), words(case["screen_right"])),
        (behavior.symbol_address("g_3DB4"), words(case["screen_bottom"])),
    ]
    vm_case = behavior.Case(
        label=case["id"], args=[rect_addr & 0x000F, rect_addr >> 4], writes=writes,
        callbacks=callbacks, return_kind="void", registers={"ax": 7, "dx": case["mode"]},
        observe=[behavior.Range("win", win_addr, 0x2c), behavior.Range("rect", rect_addr, 8)],
        max_instructions=2_000_000, callee_pop=4,
    )
    result = machine.run(vm_case)
    dos_rect = struct.unpack("<4h", machine.read(rect_addr, 8))
    dos_win_rect = struct.unpack("<4h", machine.read(win_addr, 8))

    state = ZoomState()
    state.window_rect = Rect(*case["window_rect"])
    state.flags, state.min_width, state.min_height = case["flags"], case["min_width"], case["min_height"]
    state.grid_x, state.grid_y = case["grid_x"], case["grid_y"]
    bounds = Bounds(case["desktop_top"], case["screen_right"], case["screen_bottom"])
    model_rect = Rect(*case["rect"])
    model_status = lib.portable_window_zoom_constrain(
        ctypes.byref(state), ctypes.byref(bounds), case["mode"], ctypes.byref(model_rect), 10000)
    model = (model_rect.left, model_rect.top, model_rect.right, model_rect.bottom)
    expected_win_rect = tuple(case["window_rect"])
    ok = model_status == 0 and model == dos_rect and dos_win_rect == expected_win_rect
    return {"input": case, "dos_rect": dos_rect, "model_status": model_status,
            "model_rect": model, "dos_window_rect": dos_win_rect, "equal": ok,
            "blocks": result["blocks"], "trace": result["trace"], "entry": entry_args,
            "f_22bf_calls": call_args, "written_addresses": result["written_addresses"],
            "writes_trace": writes_trace}


def main() -> None:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "build/portable/windows_zoom/constrain-report.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        raise SystemExit(f"refusing to overwrite {out}")
    compiler = ROOT / "build/portable/tests/zoom_model.dll"
    compiler.parent.mkdir(parents=True, exist_ok=True)
    import shutil
    import subprocess
    cc = shutil.which("gcc")
    if not cc: raise SystemExit("gcc unavailable")
    subprocess.run([cc, "-std=c11", "-Wall", "-Wextra", "-Werror", "-shared", "-fPIC",
                    "-I", str(ROOT / "portable/ui_model/windows"),
                    str(ROOT / "portable/ui_model/windows/zoom.c"), "-o", str(compiler)], check=True)
    lib = ctypes.CDLL(str(compiler))
    lib.portable_window_zoom_constrain.argtypes = [ctypes.POINTER(ZoomState), ctypes.POINTER(Bounds),
                                                   ctypes.c_int, ctypes.POINTER(Rect), ctypes.c_size_t]
    lib.portable_window_zoom_constrain.restype = ctypes.c_int
    cases = []
    base = {"window_rect": (20, 40, 180, 150), "min_width": 40, "min_height": 30,
            "flags": 0x0100, "grid_x": 8, "grid_y": 8, "desktop_top": 24,
            "screen_right": 640, "screen_bottom": 400}
    # Mode 0 derives top/left movement; mode 1 derives right/bottom growth.
    for mode, rect in ((0, (0, 24, 120, 110)), (0, (7, 24, 0, 0)),
                       (1, (20, 40, 640, 400)), (1, (20, 40, 0, 0))):
        cases.append({**base, "id": f"mode{mode}-{len(cases)}", "mode": mode, "rect": rect})
    # Edge-, grid-, movable-, and minimum-size contrasts.
    for grid_x, grid_y, flags, rect in (
        (0, 0, 0x0100, (0, 24, 640, 400)),
        (16, 12, 0x1100, (0, 24, 640, 400)),
        (0, 10, 0x1100, (-5, 30, 636, 399)),
        (24, 18, 0x0100, (639, 399, 640, 400)),
    ):
        cases.append({**base, "id": f"edge-{len(cases)}", "mode": len(cases) % 2,
                      "grid_x": grid_x, "grid_y": grid_y, "flags": flags, "rect": rect})
    results = [run_case(lib, case) for case in cases]
    report = {"schema": "portable-window-zoom-constrain-dos-diff-v1",
              "status": "DIAGNOSTIC_ONLY", "source_sha256": sha((ROOT / "src/S26/m39C7.c").read_bytes()),
              "runner_sha256": sha(Path(__file__).read_bytes()),
              "model_source_sha256": sha((ROOT / "portable/ui_model/windows/zoom.c").read_bytes()),
              "model_header_sha256": sha((ROOT / "portable/ui_model/windows/zoom.h").read_bytes()),
              "native_test_source_sha256": sha((ROOT / "portable/tests/windows_zoom/test_zoom.c").read_bytes()),
              "native_model_library_sha256": sha(compiler.read_bytes()),
              "oracle_sha256": behavior.exe.load().sha256,
              "harness_sha256": sha(behavior.HARNESS_SOURCE), "cases": results,
              "case_count": len(results), "mismatches": sum(not row["equal"] for row in results),
              "boundary": "Original o26_39C7_022F and f_22BF_0B5B execute as DOS bytes; only Win-address and WinRect-address services return fixture pointers."}
    out.write_text(json.dumps(report, indent=2) + "\n")
    print(f"{out}: {report['case_count']} cases, {report['mismatches']} mismatches")
    if report["mismatches"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
