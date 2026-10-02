"""Compare the profile-0/8 S00 selector raster to the original DOS converter."""
from __future__ import annotations

import ctypes
import hashlib
import json
import random
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "tools"))
import behavior
import exe
import functions


class Rect(ctypes.Structure):
    _fields_ = [("left", ctypes.c_int32), ("top", ctypes.c_int32),
                ("right", ctypes.c_int32), ("bottom", ctypes.c_int32)]


class Framebuffer(ctypes.Structure):
    _fields_ = [("width", ctypes.c_int32), ("height", ctypes.c_int32),
                ("stride", ctypes.c_size_t), ("pixels", ctypes.POINTER(ctypes.c_uint8)),
                ("clip", Rect)]


class OverviewImage(ctypes.Structure):
    _fields_ = [("pixels", ctypes.c_uint8 * 8192), ("width", ctypes.c_uint16),
                ("height", ctypes.c_uint16), ("stride", ctypes.c_uint16),
                ("scale_x", ctypes.c_uint8), ("scale_y", ctypes.c_uint8),
                ("left_margin", ctypes.c_uint16), ("mode", ctypes.c_uint8),
                ("hardware_profile", ctypes.c_int16)]


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def run_converter(function_name: str, source: bytes, output_size: int, label: str) -> bytes:
    function = functions.get(function_name)
    vectors = {exe.MANAGER_SEG * 16 + v.offset: v for v in exe.load().vectors}
    pair = SimpleNamespace(function=function, sequence_targets=frozenset(),
                           sequence_function=lambda name: functions.get(name),
                           vectors=vectors)
    machine = behavior.Machine(pair)
    case = behavior.Case(
        label=label,
        args=[0x0200, 0xA100, 0x0100, 0xB000],
        writes=[(0xA100 * 16 + 0x0200, source),
                (0xB000 * 16 + 0x0100, bytes(output_size))],
        observe=[behavior.Range("planar", 0xB000 * 16 + 0x0100, output_size)],
        return_kind="void")
    result = machine.run(case, function=function_name)
    return bytes.fromhex(result["ranges"]["planar"])


def normalize_planar(planar: bytes, width: int, plane_span: int,
                     row_stride: int) -> bytes:
    pixel_width = width * 4
    pixels = bytearray(pixel_width * 4)
    for y in range(4):
        for x in range(pixel_width):
            group, bit = divmod(x, 8)
            mask = 1 << (7 - bit)
            color = 0
            for plane in range(4):
                if planar[plane * plane_span + y * row_stride + group] & mask:
                    color |= 1 << plane
            pixels[y * pixel_width + x] = color
    return bytes(pixels)


def native_raster(library, selectors: bytes, profile: int) -> bytes:
    image = OverviewImage()
    image.pixels[:len(selectors)] = selectors
    image.width = len(selectors)
    image.height = 1
    image.stride = len(selectors)
    image.scale_x = image.scale_y = 4
    image.mode = 1
    image.hardware_profile = profile
    fb_width = len(selectors) * 4
    pixels = (ctypes.c_uint8 * (fb_width * 4))()
    fb = Framebuffer()
    assert library.portable_framebuffer_init(ctypes.byref(fb), fb_width, 4,
                                             fb_width, pixels) == 0
    status = library.sim_overview_blit(ctypes.byref(image), ctypes.byref(fb), 0, 0)
    if status != 0:
        raise AssertionError(f"native blit status {status}")
    return bytes(pixels)


def main() -> None:
    rng = random.Random(0x31260137)
    library_path = ROOT / "build/workers/behavior_render_small/overview_raster.dll"
    library_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["gcc", "-std=c11", "-Wall", "-Wextra", "-Werror", "-shared",
                    "-Iportable", "portable/game/render/overview.c",
                    "portable/render/primitives.c", "-o", str(library_path)],
                   cwd=ROOT, check=True, capture_output=True, text=True)
    library = ctypes.CDLL(str(library_path))
    library.portable_framebuffer_init.argtypes = [ctypes.POINTER(Framebuffer),
        ctypes.c_int32, ctypes.c_int32, ctypes.c_size_t, ctypes.POINTER(ctypes.c_uint8)]
    library.portable_framebuffer_init.restype = ctypes.c_int
    library.sim_overview_blit.argtypes = [ctypes.POINTER(OverviewImage),
        ctypes.POINTER(Framebuffer), ctypes.c_int32, ctypes.c_int32]
    library.sim_overview_blit.restype = ctypes.c_int

    cases = []
    for width, fn, span, stride, out_size in (
        (128, "o00_3126_0000", 0x100, 0x40, 0x400),
        (64, "o00_3126_0137", 0x80, 0x20, 0x200)):
        # All table entries 0..23 appear in each positive corpus before random fill.
        selectors = bytes([i % 24 for i in range(width)])
        selectors = selectors[:24] + bytes(rng.randrange(24) for _ in range(width - 24))
        for profile in (0, 8):
            planar = run_converter(fn, selectors, out_size,
                                   f"{fn}-profile-{profile}")
            dos_pixels = normalize_planar(planar, width, span, stride)
            portable_pixels = native_raster(library, selectors, profile)
            equal = portable_pixels == dos_pixels
            cases.append({
                "case_id": f"{fn}-profile-{profile}",
                "function": fn,
                "input_sha256": sha256(selectors),
                "planar_output_sha256": sha256(planar),
                "normalized_dos_pixel_sha256": sha256(dos_pixels),
                "portable_pixel_sha256": sha256(portable_pixels),
                "equal": equal,
                "selector_coverage": sorted(set(selectors)),
            })
            if not equal:
                mismatch = next(i for i, (a, b) in enumerate(zip(portable_pixels, dos_pixels))
                                if a != b)
                raise AssertionError(f"{fn} profile {profile} differs at pixel {mismatch}: "
                    f"portable={portable_pixels[mismatch]:02x}, DOS={dos_pixels[mismatch]:02x}")

    # Negative contrast verifies the portable boundary refuses an unmapped selector.
    image = OverviewImage()
    image.pixels[0] = 24
    image.width = image.height = image.stride = 1
    image.scale_x = image.scale_y = 4
    image.hardware_profile = 0
    pixels = (ctypes.c_uint8 * 16)()
    fb = Framebuffer()
    library.portable_framebuffer_init(ctypes.byref(fb), 4, 4, 4, pixels)
    negative_status = library.sim_overview_blit(ctypes.byref(image), ctypes.byref(fb), 0, 0)
    assert negative_status == 4  # SIM_OVERVIEW_UNSUPPORTED_SELECTOR

    source_paths = ("src/S00/m3126.asm", "src/S12/m384C.c", "src/data/d3D57.c",
                    "tools/behavior.py", "portable/game/render/overview.c",
                    "portable/game/render/overview.h",
                    "portable/render/primitives.c", "portable/render/primitives.h",
                    "portable/tests/render/evidence/dos_overview_selector_raster_diff.py")
    report = {
        "schema": "portable-overview-selector-raster-differential-v1",
        "status": "PASS" if all(c["equal"] for c in cases) else "FAIL",
        "scope": "S00 m3126 g_1F9E profile-0/8 selector conversion to normalized 4x4 indexed pixels; no physical VGA claim",
        "cases": cases,
        "positive_case_count": len(cases),
        "negative_control": {"selector": 24, "portable_status": negative_status,
                              "expected_status": 4, "passed": negative_status == 4},
        "normalization": "Decode the original DOS helper's four planar output regions into 4-bit indexed pixels; each helper-produced source cell is 4x4. Compare all normalized pixels against the portable blitter.",
        "source_hashes": {path: sha256((ROOT / path).read_bytes()) for path in source_paths},
        "oracle_sha256": exe.load().sha256,
        "unicorn_version": behavior.uc.__version__,
        "source_regions": {
            "128-cell": "S00 m3126.asm _o00_3126_0000, 64 selector pairs, 4x4 tile per selector",
            "64-cell": "S00 m3126.asm _o00_3126_0137, 32 selector pairs, 4x4 tile per selector",
            "selector_dispatch": "S12 m384C.c InitMapFunctions profile 0/8 selects S00 dispatch entries 0 and 1",
        },
        "limitations": ["RGB palette conversion and physical EGA/VGA memory effects are outside this comparison.",
                        "Only S00 profiles 0 and 8 are accepted by sim_overview_blit; other profiles fail closed."],
    }
    out = ROOT / "portable/tests/render/evidence/dos-overview-selector-raster-differential.json"
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Original DOS raster differential matched {len(cases)}/{len(cases)} cases.")


if __name__ == "__main__":
    main()
