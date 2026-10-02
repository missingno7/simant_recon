"""Compare tile raster composition with original 2B1A under a normalized readback.

The DOS helper reads its base through EGA graphics-controller read-map state.
Unicorn has no EGA device model, so the fixture places the bytes that the
selected read plane would return at DS:g3DB0+col. This validates the original
helper's mask/plane byte contract and the portable decoding/composition; it
does not validate physical EGA register or map-atlas behavior.
"""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import random
import subprocess
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[5]
sys.path[:0] = [str(ROOT / "tools")]
import behavior  # noqa: E402
import exe  # noqa: E402
import functions  # noqa: E402
import symbols  # noqa: E402
import unicorn  # noqa: E402


class Database(ctypes.Structure):
    _fields_ = [("index_file", ctypes.POINTER(ctypes.c_uint8)),
                ("index_file_size", ctypes.c_size_t),
                ("data_file", ctypes.POINTER(ctypes.c_uint8)),
                ("data_file_size", ctypes.c_size_t),
                ("entries", ctypes.c_void_p), ("entry_count", ctypes.c_size_t),
                ("error", ctypes.c_char * 192)]


class Record(ctypes.Structure):
    _fields_ = [("id", ctypes.c_int16), ("kind", ctypes.c_uint8),
                ("index_flags", ctypes.c_uint8), ("data_offset", ctypes.c_uint32),
                ("data", ctypes.POINTER(ctypes.c_uint8)), ("size", ctypes.c_size_t)]


def original_machine(name: str):
    first = functions.get(name)
    vectors = {exe.MANAGER_SEG * 16 + vector.offset: vector for vector in exe.load().vectors}
    pair = SimpleNamespace(function=first, sequence_targets=frozenset(),
                           sequence_function=lambda n: functions.get(n), vectors=vectors)
    return behavior.Machine(pair)


def compile_portable(path: Path) -> ctypes.CDLL:
    sources = ["portable/game/resources/database.c", "portable/render/primitives.c",
               "portable/render/tile_raster.c"]
    subprocess.run(["gcc", "-std=c11", "-Wall", "-Wextra", "-Wconversion", "-Werror",
                    "-pedantic", "-shared", *sources, "-o", str(path)],
                   cwd=ROOT, check=True, capture_output=True, text=True)
    lib = ctypes.CDLL(str(path.resolve()))
    byte_ptr = ctypes.POINTER(ctypes.c_uint8)
    lib.portable_ega_tile_decode.argtypes = [byte_ptr, ctypes.c_size_t, ctypes.c_uint16, byte_ptr]
    lib.portable_ega_tile_decode.restype = ctypes.c_int
    lib.portable_ega_life_composite.argtypes = [byte_ptr, byte_ptr, ctypes.c_size_t,
                                                ctypes.c_uint16]
    lib.portable_ega_life_composite.restype = ctypes.c_int
    lib.portable_db_open.argtypes = [ctypes.POINTER(Database), ctypes.c_char_p]
    lib.portable_db_open.restype = ctypes.c_int
    lib.portable_db_close.argtypes = [ctypes.POINTER(Database)]
    lib.portable_db_load.argtypes = [ctypes.POINTER(Database), ctypes.c_int16, ctypes.c_int16,
                                     ctypes.POINTER(Record)]
    lib.portable_db_load.restype = ctypes.c_int
    lib.portable_db_record_free.argtypes = [ctypes.POINTER(Record)]
    return lib


def as_c_bytes(value: bytes):
    return (ctypes.c_uint8 * len(value)).from_buffer_copy(value)


def pack_pixels(pixels: bytes) -> bytes:
    output = bytearray(128)
    for y in range(16):
        for plane in range(4):
            for x in range(16):
                if (pixels[y * 16 + x] >> plane) & 1:
                    output[y * 8 + plane * 2 + (x >> 3)] |= 0x80 >> (x & 7)
    return bytes(output)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    parser.add_argument("--cases", type=int, default=128)
    args = parser.parse_args()
    rng = random.Random(0x2B1A_31AD)
    data = symbols.load()["data"]
    g3db0 = data["g_3DB0"]
    g3d20 = data["g_3D20"]
    base_seg, base_off, life_seg, life_off = 0xA000, 0x2400, 0xA100, 0x3100
    g3db0_address = g3db0["seg"] * 16 + g3db0["off"]
    g3d20_address = g3d20["seg"] * 16 + g3d20["off"]

    with tempfile.TemporaryDirectory(prefix="simant-tile-dos-",
                                     ignore_cleanup_errors=True) as temporary:
        lib = compile_portable(Path(temporary) / ("tile.dll" if sys.platform == "win32"
                                                  else "libtile.so"))
        mismatches = []
        inputs = [(f"random-{i}", bytes(rng.randrange(256) for _ in range(128)),
                   bytes(rng.randrange(256) for _ in range(160)))
                  for i in range(args.cases)]
        db = Database()
        if lib.portable_db_open(ctypes.byref(db), str(ROOT / "assets" / "HCEGANT").encode()):
            raise AssertionError("could not open HCEGANT for actual life frames")
        actual_samples = []
        try:
            for ident in range(15, 21):
                record = Record()
                if lib.portable_db_load(ctypes.byref(db), ident, 9, ctypes.byref(record)):
                    raise AssertionError(f"could not load kind-9 life resource {ident}")
                try:
                    frames = ctypes.string_at(record.data, record.size)
                finally:
                    lib.portable_db_record_free(ctypes.byref(record))
                frame_count = len(frames) // 160
                for frame_index in sorted({0, frame_count - 1}):
                    start = frame_index * 160
                    actual_samples.append((f"resource-{ident}-frame-{frame_index}",
                                           bytes(rng.randrange(256) for _ in range(128)),
                                           frames[start:start + 160]))
        finally:
            lib.portable_db_close(ctypes.byref(db))
        inputs.extend(actual_samples)

        for case_name, base, life in inputs:
            original = original_machine("o00_31AD_2B1A")
            writes = [(g3db0_address, base_seg.to_bytes(2, "little")),
                      (base_seg * 16 + base_off, base),
                      (life_seg * 16 + life_off, life)]
            result = original.run(
                behavior.Case(label=f"tile-life-{case_name}",
                              args=[base_off, 0, life_off, life_seg],
                              writes=writes,
                              observe=[behavior.Range("composite", g3d20_address, 128)]),
                function="o00_31AD_2B1A")
            dos_bytes = original.read(g3d20_address, 128)

            base_c, life_c = as_c_bytes(base), as_c_bytes(life)
            pixels = (ctypes.c_uint8 * 256)()
            if lib.portable_ega_tile_decode(base_c, len(base), 0, pixels) != 0:
                raise AssertionError("portable tile decode rejected normalized DOS base bytes")
            if lib.portable_ega_life_composite(pixels, life_c, len(life), 0) != 0:
                raise AssertionError("portable life composite rejected DOS frame bytes")
            portable_bytes = pack_pixels(bytes(pixels))
            if dos_bytes != portable_bytes:
                first = next(i for i, (a, b) in enumerate(zip(dos_bytes, portable_bytes))
                             if a != b)
                mismatches.append({"case": case_name, "first_byte": first,
                                   "dos": dos_bytes[first], "portable": portable_bytes[first]})
                break

        report = {
            "schema": "portable-kind9-life-dos-differential-v1",
            "status": "DIAGNOSTIC_PASS_NORMALIZED_READBACK_ONLY" if not mismatches else "FAIL",
            "function": "o00_31AD_2B1A",
            "cases": len(inputs),
            "random_cases": args.cases,
            "actual_resource_samples": [name for name, _, _ in actual_samples],
            "mismatch_count": len(mismatches),
            "first_mismatches": mismatches[:8],
            "oracle_exe_sha256": exe.load().sha256,
            "ground_raw_contract": "128 bytes, 16 rows of four two-byte EGA planes",
            "life_raw_contract": "160 bytes, 16 rows of one mask and four two-byte EGA planes",
            "compared_effect": "all 128 bytes written to g_3D20",
            "excluded_effects": ["physical EGA read-map device behavior",
                                 "tile atlas address calculation/placement",
                                 "_o00_31AD_2FDA screen blit and clipping"],
            "unicorn_version": unicorn.__version__,
            "portable_sha256": hashlib.sha256(Path("portable/render/tile_raster.c").read_bytes()).hexdigest(),
        }
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(__import__("json").dumps(report, indent=2) + "\n")
        print(__import__("json").dumps(report, indent=2))
        if mismatches:
            raise SystemExit(1)


if __name__ == "__main__":
    main()
