#!/usr/bin/env python3
"""Differentially exercise S00 0647's absolute planar-aperture tile source."""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[4]
sys.path[:0] = [str(ROOT / "tools"), str(ROOT / "build/behavior/deps")]
import behavior  # noqa: E402
import functions  # noqa: E402
import match  # noqa: E402

DOS_FB = 0xA0000
VIDEO_SEGMENT = 0xA000
CLIP_SEGMENT = 0x7000
CLIP_LINEAR = CLIP_SEGMENT * 16
SCREEN_WIDTH = 640
SCREEN_HEIGHT = 480
SCREEN_STRIDE = 80
TILE_BYTES = 32
PLANAR_BYTES = 128
PIXELS = 256

INPUTS = [
    ROOT / "src/S00/m31AD.asm",
    ROOT / "src/S00/m31AD_2AB4.asm",
    ROOT / "src/root/m1B4E.asm",
    ROOT / "layout/oracle.lock.json",
    ROOT / "layout/functions.json",
    ROOT / "layout/symbols.json",
    ROOT / "layout/manifest.json",
    ROOT / "tools/behavior.py",
    ROOT / "tools/functions.py",
    ROOT / "tools/match.py",
    ROOT / "tools/exe.py",
    ROOT / "tools/modules.py",
    ROOT / "tools/modctx.py",
    ROOT / "portable/whole_program/platform/graphics.h",
    ROOT / "portable/whole_program/platform/graphics.c",
    ROOT / "portable/whole_program/platform/graphics_source_clip.h",
    ROOT / "portable/whole_program/platform/graphics_source_clip.c",
    ROOT / "portable/whole_program/platform/graphics_bitmap_source.h",
    ROOT / "portable/whole_program/platform/graphics_bitmap_source.c",
    ROOT / "portable/whole_program/platform/graphics_line_1499.h",
    ROOT / "portable/whole_program/platform/graphics_line_1499.c",
    ROOT / "portable/whole_program/platform/graphics_cursor_hooks.h",
    ROOT / "portable/whole_program/platform/graphics_cursor_hooks.c",
    ROOT / "portable/whole_program/platform/m1b73_mouse_state.h",
    ROOT / "portable/whole_program/platform/m1b73_mouse_state.c",
    ROOT / "portable/whole_program/platform/graphics_tile_upload.h",
    ROOT / "portable/whole_program/platform/graphics_tile_upload.c",
    ROOT / "portable/whole_program/window_source_rects.h",
    ROOT / "portable/whole_program/window_source_globals.h",
    ROOT / "portable/whole_program/window_source_globals.c",
    ROOT / "portable/whole_program/state/asm_display_data_v1.h",
    ROOT / "portable/whole_program/state/asm_display_data_v1.c",
    ROOT / "portable/render/primitives.h",
    ROOT / "portable/render/primitives.c",
    ROOT / "portable/tests/whole_program/platform/graphics_tile_cache_blit_probe.c",
    Path(__file__),
]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def addr(name: str) -> int:
    symbols = match.symbols()
    symbol = symbols.get(name) or symbols.get("_" + name)
    if symbol is None:
        raise KeyError(name)
    return symbol["seg"] * 16 + symbol["off"]


def original_machine():
    target = functions.get("o00_31AD_0647")
    pair = SimpleNamespace(function=target, sequence_targets=frozenset(),
                           sequence_function=lambda n: functions.get(n), vectors={})
    return behavior.Machine(pair)


def native_library(path: Path, compiler: str):
    command = [
        compiler, "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
        "-pedantic", "-shared", "-fPIC", "-I", str(ROOT),
        str(ROOT / "portable/whole_program/platform/graphics.c"),
        str(ROOT / "portable/whole_program/platform/graphics_source_clip.c"),
        str(ROOT / "portable/whole_program/platform/graphics_bitmap_source.c"),
        str(ROOT / "portable/whole_program/platform/graphics_line_1499.c"),
        str(ROOT / "portable/whole_program/platform/graphics_cursor_hooks.c"),
        str(ROOT / "portable/whole_program/platform/m1b73_mouse_state.c"),
        str(ROOT / "portable/whole_program/platform/graphics_tile_upload.c"),
        str(ROOT / "portable/whole_program/window_source_globals.c"),
        str(ROOT / "portable/whole_program/state/asm_display_data_v1.c"),
        str(ROOT / "portable/render/primitives.c"),
        str(ROOT / "portable/tests/whole_program/platform/graphics_tile_cache_blit_probe.c"),
        "-o", str(path),
    ]
    subprocess.run(command, cwd=ROOT, check=True, capture_output=True, text=True)
    lib = ctypes.CDLL(str(path.resolve()))
    lib.sim_tile0647_native_probe.argtypes = [
        ctypes.c_int16, ctypes.c_int16, ctypes.c_uint16, ctypes.c_int,
        ctypes.POINTER(ctypes.c_uint8), ctypes.POINTER(ctypes.c_uint8),
        ctypes.c_size_t, ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_int32),
    ]
    lib.sim_tile0647_native_probe.restype = ctypes.c_int
    return lib, command


def native_case(lib, x: int, y: int, offset: int, clip_mode: int,
                rows: bytes):
    rows_buf = (ctypes.c_uint8 * len(rows)).from_buffer_copy(rows)
    pixels = (ctypes.c_uint8 * PIXELS)()
    callback = (ctypes.c_uint8 * PLANAR_BYTES)()
    meta = (ctypes.c_int32 * 8)()
    result = lib.sim_tile0647_native_probe(
        x, y, offset, clip_mode, rows_buf, pixels, PIXELS,
        callback, PLANAR_BYTES, meta)
    if result != 0:
        raise RuntimeError(f"native probe failed result={result}, meta={list(meta)}")
    return {"pixels": bytes(pixels), "callback": bytes(callback),
            "meta": list(meta)}


def dos_case(x: int, y: int, offset: int, clip_mode: int, rows: bytes):
    machine = original_machine()
    dgroup = match.DGROUP_SEG * 16
    clip_words = ((x - 1, y - 1, x + 16, y + 16) if clip_mode == 2 else
                  (x + 4, y + 4, x + 11, y + 11))
    table = b"".join(struct.pack("<H", yy * SCREEN_STRIDE)
                     for yy in range(SCREEN_HEIGHT))
    writes = [
        (addr("g_3DB0"), struct.pack("<H", VIDEO_SEGMENT)),
        (addr("g_3DB4"), struct.pack("<H", SCREEN_HEIGHT)),
        (addr("g_3DB6"), struct.pack("<H", SCREEN_STRIDE)),
        (addr("g_3DD4"), b"\x00\x00"),
        (addr("g_4333"), b"\x01"),  # cursor callbacks excluded from this contract
        (addr("g_4365"), b"\x00"),
        (addr("g_4366"), b"\x01"),
        (addr("g_3DFC"), table),
        (DOS_FB + offset, rows),
    ]
    if clip_mode != 0:
        writes += [
            (addr("g_5AAC"), struct.pack("<HH", 0, CLIP_SEGMENT)),
            (addr("g_5AAE"), struct.pack("<H", CLIP_SEGMENT)),
            (CLIP_LINEAR, struct.pack("<4H", *clip_words)),
        ]
    else:
        writes += [
            (addr("g_5AAC"), bytes(4)),
            (addr("g_5AAE"), b"\x00\x00"),
        ]

    trace_projection = []
    def project(machine, args):
        trace_projection.append(list(args))
        # `_0647` near-calls 0CF9 with a saved CS word followed by x,y,
        # far SS:offset bitmap, and width/height. 0CF9 then far-calls this
        # leaf, so its stack also contains 0CF9's near return IP.
        (_near_return, _saved_cs, call_x, call_y,
         bits_off, bits_seg, width, height) = args
        payload = machine.read((bits_seg << 4) + bits_off, PLANAR_BYTES)
        item = {"x": call_x, "y": call_y, "width": width,
                "height": height, "payload": payload.hex()}
        trace_projection.append(item)
        return item

    callback = behavior.Callback(stack_words=8,
                                 handler=lambda _machine, _args: None,
                                 project=project)
    screen_at = DOS_FB + y * SCREEN_STRIDE + (x >> 3)
    case = behavior.Case(
        label=f"0647-x{x}-y{y}-off{offset:04X}-clipmode{clip_mode}",
        args=[x, y, offset], writes=writes,
        callbacks={"f_1D8E_07F6": callback},
        observe=[behavior.Range("screen", screen_at, 15 * SCREEN_STRIDE + 2),
                 behavior.Range("lock", addr("g_3DD4"), 2)],
        return_kind="void", max_instructions=1_000_000,
    )
    result = machine.run(case)
    screen = bytes.fromhex(result["ranges"]["screen"])
    packed = bytearray()
    for row in range(16):
        packed += screen[row * SCREEN_STRIDE:row * SCREEN_STRIDE + 2]
    screen_addrs = {DOS_FB + yy * SCREEN_STRIDE + (x >> 3) + xx
                    for yy in range(y, y + 16) for xx in range(2)}
    screen_write_count = sum(at in screen_addrs for at in result["written_addresses"])
    if screen_write_count:
        route = ("0CF9-0D06-blit-to-vram" if (x & 7) != 0 else
                 "direct-vram")
    elif result["trace"]:
        route = "0CF9-clip-callback"
    else:
        route = "0CF9-no-list-no-draw"
    return {"packed": bytes(packed), "trace": result["trace"],
            "raw_callback_args": trace_projection,
            "io": result["io"], "lock": result["ranges"]["lock"],
            "screen_write_count": screen_write_count, "route": route,
            "written_addresses": result["written_addresses"]}


def packed_native(pixels: bytes) -> bytes:
    output = bytearray()
    for row in range(16):
        for byte in range(2):
            value = 0
            for bit in range(8):
                if pixels[row * 16 + byte * 8 + bit] & 1:
                    value |= 0x80 >> bit
            output.append(value)
    return bytes(output)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--samples", type=int, default=24)
    parser.add_argument("--route-controls", action="store_true",
                        help="run only unaligned/no-list and fully-contained-list route controls")
    args = parser.parse_args()
    report_path = args.report if args.report.is_absolute() else ROOT / args.report
    if report_path.exists():
        raise SystemExit(f"refusing to overwrite report: {report_path}")
    if not 1 <= args.samples <= 100:
        raise SystemExit("samples must be in 1..100")
    compiler = os.environ.get("CC", "gcc")
    compiler_path = shutil.which(compiler)
    before = {str(p.relative_to(ROOT)): sha(p.read_bytes()) for p in INPUTS}
    cases = []
    mismatches = []
    seed = 0x6407A000
    with tempfile.TemporaryDirectory(prefix="simant-0647-diff-") as temp:
        dll_path = Path(temp) / "graphics_tile_cache_blit_probe.dll"
        lib, command = native_library(dll_path, compiler)
        native_object_hash = sha(dll_path.read_bytes())
        if args.route_controls:
            plans = [(0xC000, 67, 0, "unaligned-no-cliplist"),
                     (0xC000, 64, 2, "aligned-fully-contained-cliplist")]
            sample_limit = 1
        else:
            plans = [(0xA000, 64, 0, "unclipped-aligned"),
                     (0xB5C0, 64, 0, "unclipped-aligned"),
                     (0xC000, 64, 0, "unclipped-aligned"),
                     (0xA000, 64, 1, "clipped-aligned"),
                     (0xB5C0, 64, 1, "clipped-aligned"),
                     (0xC000, 67, 1, "clipped-unaligned")]
            sample_limit = args.samples
        for offset, x, clip_mode, path_name in plans:
            for sample in range(sample_limit):
                seed = (seed * 1664525 + 1013904223) & 0xffffffff
                rows = bytes((((seed >> ((i & 3) * 8)) ^ (i * 29) ^
                               (sample * 11)) & 0xff) for i in range(TILE_BYTES))
                y = 41
                original = dos_case(x, y, offset, clip_mode, rows)
                native = native_case(lib, x, y, offset, clip_mode, rows)
                if args.route_controls:
                    native_route = ("g914C-callback" if native["meta"][1] == 2 else
                                    "native-direct/no-callback")
                    route_match = original["route"] == native_route
                    item = {
                        "path": path_name, "offset": offset, "x": x, "y": y,
                        "oracle_route": original["route"],
                        "oracle_screen_write_count": original["screen_write_count"],
                        "oracle_clip_callback_count": len(original["trace"]),
                        "oracle_port_io_count": len(original["io"]),
                        "native_route": native_route,
                        "native_callback_x": native["meta"][2],
                        "native_callback_y": native["meta"][3],
                        "native_callback_width": native["meta"][4],
                        "native_callback_height": native["meta"][5],
                        "route_match": route_match,
                        "match": route_match,
                        "scope": "Route diagnostics only; the probe intercepts g914C and intentionally does not perform a production raster draw.",
                    }
                    equal = route_match
                elif clip_mode != 0:
                    original_draw = original["trace"][-1] if original["trace"] else None
                    native_draw = {
                        "kind": native["meta"][1], "x": native["meta"][2],
                        "y": native["meta"][3], "width": native["meta"][4],
                        "height": native["meta"][5],
                        "payload": native["callback"].hex(),
                    }
                    original_semantic = (original_draw or {}).get("args")
                    equal = original_semantic is not None and all(
                        original_semantic.get(k) == native_draw[k]
                        for k in ("x", "y", "width", "height", "payload"))
                    item = {
                        "path": path_name, "offset": offset, "x": x, "y": y,
                        "tile_rows_sha256": sha(rows),
                        "oracle_draw": original_semantic,
                        "native_draw": native_draw,
                        "oracle_lock": original["lock"],
                        "native_lock": native["meta"][6], "match": equal,
                        "boundary": "normalized g914C/f_1D8E_07F6 draw command and pointed 128-byte planar payload",
                    }
                else:
                    expected = original["packed"]
                    actual = packed_native(native["pixels"])
                    equal = expected == actual
                    item = {
                        "path": path_name, "offset": offset, "x": x, "y": y,
                        "tile_rows_sha256": sha(rows),
                        "oracle_packed_screen_sha256": sha(expected),
                        "native_packed_screen_sha256": sha(actual),
                        "oracle_lock": original["lock"],
                        "native_lock": native["meta"][6], "match": equal,
                        "boundary": "16x16 indexed native output packed back to the single-plane byte view observed in flat Unicorn VRAM; all four input planes are equal",
                    }
                cases.append(item)
                if not equal:
                    mismatches.append(item)
        ctypes.windll.kernel32.FreeLibrary(ctypes.c_void_p(lib._handle))
        del lib
    after = {str(p.relative_to(ROOT)): sha(p.read_bytes()) for p in INPUTS}
    passed = not mismatches and before == after
    report = {
        "schema": "simant-s00-0647-aperture-dos-native-v1",
        "status": (("PASS" if not mismatches else "ROUTE_DIFFERENCE") if args.route_controls else "PASS" if passed else "MISMATCH" if mismatches else "INPUTS_CHANGED"),
        "scope": ("Route-only diagnostics for unaligned x with g5AAE zero and aligned x fully contained by an installed clip rectangle. Route differences are recorded as explicit debt, not pixel acceptance; the native probe intercepts g914C without rasterizing." if args.route_controls else "Direct original S00 o00_31AD_0647 DOS assembly versus the native tile aperture provider. Clipped cases compare normalized draw coordinates/dimensions and all 128 pointed planar payload bytes. Unclipped cases compare the 16x16 packed single-plane screen bytes with native indexed pixels converted back to packed bits; these cases intentionally use four identical source planes because Unicorn does not model EGA read-map latches. This is not an EGA/VGA hardware framebuffer proof."),
        "source_contract": {
            "entry": "src/S00/m31AD.asm:_o00_31AD_0647 lines 894-1139 reads [bp+0Ah] directly into SI in both the scratch/clipped and direct paths; it does not add C000h.",
            "unaligned": "The initial TEST AX,7 routes unaligned x through the 0CF9 clipped callback path without rounding x in the DOS arguments.",
            "no_clip_fallback": "When the unaligned-x path calls 0CF9 with g5AAE zero, 0CF9 enters genuine ASM _0D06, which can blit to VRAM; it does not simply return without drawing.",
            "clip_switch": "g5AAE is the segment word of the far clip-list pointer at g5AAC, not a count. On aligned x, zero selects the direct path and nonzero makes _0647 scan the installed valid list; unaligned x always takes the scratch/0CF9 path. The native fixture represents the admitted valid installed-list state with g5AAC != NULL. Malformed far-pointer combinations are outside this comparison.",
            "destination": "The aligned direct path computes the display row from g3DFC[y], adds x>>3, and writes the 16 row pairs using 80-byte stride.",
        },
        "compiler": compiler,
        "compiler_resolved_path": compiler_path,
        "compiler_sha256": sha(Path(compiler_path).read_bytes()) if compiler_path else None,
        "native_compile_command": command,
        "native_probe_sha256": native_object_hash,
        "original_module_identity": functions.get("o00_31AD_0647"),
        "sample_limit_per_plan": sample_limit,
        "case_count": len(cases),
        "match_count": sum(bool(c["match"]) for c in cases),
        "mismatch_count": len(mismatches),
        "cases": cases,
        "mismatches": mismatches,
        "inputs_before_sha256": before,
        "inputs_after_sha256": after,
        "inputs_stable": before == after,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"S00 0647 DOS/native: {report['status']} cases={len(cases)} matched={report['match_count']} mismatches={len(mismatches)}")
    if mismatches:
        print(json.dumps(mismatches[:3], indent=2))
    return 0 if passed or (args.route_controls and before == after) else 1


if __name__ == "__main__":
    raise SystemExit(main())
