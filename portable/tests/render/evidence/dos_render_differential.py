"""Direct frozen-DOS renderer probes against portable bitmap/font routines.

This is diagnostic evidence only. It calls original LZSS decode, EGA masked
merge, and font width entry points in the DOS image; it does not run a DOS
display driver or claim full VGA/framebuffer equivalence.
"""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import random
import struct
import subprocess
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[4]
sys.path[:0] = [str(ROOT / "tools"), str(ROOT / "tools" / "behavior_suites")]
import behavior
import exe
import functions
import symbols
import unicorn


class PortableDatabase(ctypes.Structure):
    _fields_ = [("index_file", ctypes.c_void_p), ("index_file_size", ctypes.c_size_t),
                ("data_file", ctypes.c_void_p), ("data_file_size", ctypes.c_size_t),
                ("entries", ctypes.c_void_p), ("entry_count", ctypes.c_size_t),
                ("error", ctypes.c_char * 192)]


class PortableDbRecord(ctypes.Structure):
    _fields_ = [("id", ctypes.c_int16), ("kind", ctypes.c_uint8),
                ("index_flags", ctypes.c_uint8), ("data_offset", ctypes.c_uint32),
                ("data", ctypes.POINTER(ctypes.c_uint8)), ("size", ctypes.c_size_t)]


class PortableFramebuffer(ctypes.Structure):
    _fields_ = [("width", ctypes.c_int32), ("height", ctypes.c_int32),
                ("stride", ctypes.c_size_t), ("pixels", ctypes.POINTER(ctypes.c_uint8)),
                ("clip", ctypes.c_int32 * 4)]


class PortableFont(ctypes.Structure):
    _fields_ = [("metrics", ctypes.c_int16 * 13), ("first_char", ctypes.c_uint16),
                ("last_char", ctypes.c_uint16), ("table_count", ctypes.c_size_t),
                ("image_size", ctypes.c_size_t), ("image", ctypes.POINTER(ctypes.c_uint8)),
                ("loc_table", ctypes.POINTER(ctypes.c_int16)),
                ("ow_table", ctypes.POINTER(ctypes.c_int16)),
                ("proportional", ctypes.c_int), ("missing_char", ctypes.c_uint16)]


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def compile_library(output: Path) -> None:
    sources = ["portable/game/resources/database.c", "portable/render/primitives.c",
               "portable/render/bitmap.c", "portable/render/font.c"]
    command = ["gcc", "-std=c11", "-Wall", "-Wextra", "-Wconversion", "-Werror",
               "-pedantic", "-shared", *sources, "-o", str(output)]
    subprocess.run(command, cwd=ROOT, check=True, capture_output=True, text=True)


def bind_library(path: Path):
    lib = ctypes.CDLL(str(path.resolve()))
    lib.portable_db_open_files.argtypes = [ctypes.POINTER(PortableDatabase), ctypes.c_char_p,
                                           ctypes.c_char_p]
    lib.portable_db_open_files.restype = ctypes.c_int
    lib.portable_db_close.argtypes = [ctypes.POINTER(PortableDatabase)]
    lib.portable_db_load.argtypes = [ctypes.POINTER(PortableDatabase), ctypes.c_int16,
                                     ctypes.c_int16, ctypes.POINTER(PortableDbRecord)]
    lib.portable_db_load.restype = ctypes.c_int
    lib.portable_db_record_free.argtypes = [ctypes.POINTER(PortableDbRecord)]
    lib.portable_bitmap_decode_packed.argtypes = [ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t,
                                                  ctypes.POINTER(ctypes.POINTER(ctypes.c_uint8)),
                                                  ctypes.POINTER(ctypes.c_size_t)]
    lib.portable_bitmap_decode_packed.restype = ctypes.c_int
    lib.portable_bitmap_release_decoded.argtypes = [ctypes.POINTER(ctypes.c_uint8)]
    lib.portable_bitmap_draw_resource.argtypes = [ctypes.POINTER(PortableFramebuffer),
                                                  ctypes.c_int32, ctypes.c_int32,
                                                  ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t]
    lib.portable_bitmap_draw_resource.restype = ctypes.c_int
    lib.portable_framebuffer_init.argtypes = [ctypes.POINTER(PortableFramebuffer), ctypes.c_int32,
                                              ctypes.c_int32, ctypes.c_size_t,
                                              ctypes.POINTER(ctypes.c_uint8)]
    lib.portable_framebuffer_init.restype = ctypes.c_int
    lib.portable_font_init.argtypes = [ctypes.POINTER(PortableFont)]
    lib.portable_font_load.argtypes = [ctypes.POINTER(PortableFont), ctypes.POINTER(ctypes.c_uint8),
                                       ctypes.c_size_t]
    lib.portable_font_load.restype = ctypes.c_int
    lib.portable_font_destroy.argtypes = [ctypes.POINTER(PortableFont)]
    lib.portable_font_char_width.argtypes = [ctypes.POINTER(PortableFont), ctypes.c_uint8]
    lib.portable_font_char_width.restype = ctypes.c_int32
    lib.portable_font_string_width.argtypes = [ctypes.POINTER(PortableFont),
                                               ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t]
    lib.portable_font_string_width.restype = ctypes.c_int32
    lib.portable_font_draw.argtypes = [ctypes.POINTER(PortableFramebuffer),
                                       ctypes.POINTER(PortableFont), ctypes.c_int32,
                                       ctypes.c_int32, ctypes.POINTER(ctypes.c_uint8),
                                       ctypes.c_size_t, ctypes.c_uint8,
                                       ctypes.POINTER(ctypes.c_int32)]
    lib.portable_font_draw.restype = ctypes.c_int
    return lib


def open_database(lib):
    db = PortableDatabase()
    stem = ROOT / "assets" / "HCEGANT"
    status = lib.portable_db_open_files(ctypes.byref(db), str(stem.with_suffix(".NDX")).encode(),
                                        str(stem.with_suffix(".DAT")).encode())
    if status:
        raise RuntimeError(f"database open failed: {status} {db.error!r}")
    return db


def load_record(lib, db, ident: int, kind: int) -> bytes:
    record = PortableDbRecord()
    status = lib.portable_db_load(ctypes.byref(db), ident, kind, ctypes.byref(record))
    if status:
        raise RuntimeError(f"record {ident}/{kind} failed: {status}")
    try:
        return ctypes.string_at(record.data, record.size)
    finally:
        lib.portable_db_record_free(ctypes.byref(record))


def original_machine(name: str):
    first = functions.get(name)
    vectors = {exe.MANAGER_SEG * 16 + v.offset: v for v in exe.load().vectors}
    pair = SimpleNamespace(function=first, sequence_targets=frozenset(),
                           sequence_function=lambda n: functions.get(n), vectors=vectors)
    return behavior.Machine(pair)


def case_call(machine, function: str, label: str, args: list[int], writes=(), observe=(),
              return_kind="void", preserve=False):
    return machine.run(behavior.Case(label=label, args=args, writes=list(writes),
                                     observe=list(observe), return_kind=return_kind),
                       preserve=preserve, function=function)


def original_lzss_decode(resource: bytes, expected_size: int) -> bytes:
    source = resource[4:]
    src_off, dst_off, src_seg, dst_seg = 0x3000, 0x5000, 0xA000, 0xB000
    machine = original_machine("f_1B05_0008")
    signed_count = struct.unpack_from("<h", resource, 2)[0]
    case_call(machine, "f_1B05_0008", "packed-2500-init",
              [src_off, src_seg, signed_count], writes=[(src_seg * 16 + src_off, source)])
    header = bytearray()
    result = case_call(machine, "f_1B05_0046", "packed-2500-header",
                       [dst_off, dst_seg, 12],
                       observe=[behavior.Range("header", dst_seg * 16 + dst_off, 12)],
                       return_kind="u16", preserve=True)
    if result["return"] != 12:
        raise AssertionError(f"DOS LZSS header read returned {result['return']}")
    header.extend(machine.read(dst_seg * 16 + dst_off, 12))
    width, height = struct.unpack_from("<HH", header, 8)
    output_size = 12 + 4 * ((width + 7) // 8) * height
    if output_size != expected_size:
        raise AssertionError(f"DOS pack header implies {output_size}, C returned {expected_size}")
    row_bytes = (width + 7) // 8
    block_size = 4 * row_bytes * 8
    total = 12
    while total < output_size:
        count = min(block_size, output_size - total)
        result = case_call(machine, "f_1B05_0046", f"packed-2500-block-{total}",
                           [dst_off + total, dst_seg, count],
                           observe=[behavior.Range("decoded", dst_seg * 16 + dst_off + total,
                                                   count)],
                           return_kind="u16", preserve=True)
        if result["return"] != count:
            raise AssertionError(f"DOS LZSS block at {total} returned {result['return']} != {count}")
        total += count
    return machine.read(dst_seg * 16 + dst_off, output_size)


def reference_lzss_decode(resource: bytes, output_size: int) -> bytes:
    source = resource[4:]
    pos = 0
    flags = bits_left = 0
    ring = bytearray(b" " * 0xFEE + b"\0" * (4096 - 0xFEE))
    ring_pos = 0xFEE
    output = bytearray()
    while len(output) < output_size:
        if bits_left == 0:
            flags = source[pos]
            pos += 1
            bits_left = 8
        if flags & 1:
            value = source[pos]
            pos += 1
            ring[ring_pos] = value
            ring_pos = (ring_pos + 1) & 0xFFF
            output.append(value)
        else:
            lo, hi = source[pos], source[pos + 1]
            pos += 2
            match_pos = lo | ((hi & 0xF0) << 4)
            for _ in range((hi & 0x0F) + 3):
                value = ring[match_pos]
                match_pos = (match_pos + 1) & 0xFFF
                ring[ring_pos] = value
                ring_pos = (ring_pos + 1) & 0xFFF
                output.append(value)
                if len(output) == output_size:
                    break
        flags >>= 1
        bits_left -= 1
    return bytes(output)


def pixel_to_planes(pixels: bytes, width: int, height: int) -> bytes:
    row_bytes = (width + 7) // 8
    output = bytearray(row_bytes * height * 4)
    for y in range(height):
        for x in range(width):
            color = pixels[y * width + x]
            bit = 0x80 >> (x & 7)
            base = y * row_bytes * 4 + (x >> 3)
            for plane in range(4):
                if color & (1 << plane):
                    output[base + plane * row_bytes] |= bit
    return bytes(output)


def planes_to_pixels(data: bytes, width: int, height: int) -> bytes:
    row_bytes = (width + 7) // 8
    output = bytearray(width * height)
    for y in range(height):
        for x in range(width):
            bit = 0x80 >> (x & 7)
            base = y * row_bytes * 4 + (x >> 3)
            output[y * width + x] = sum(((data[base + plane * row_bytes] & bit) != 0) << plane
                                        for plane in range(4))
    return bytes(output)


def type3_shift_probe(lib, machine, record: bytes):
    width, height = struct.unpack_from("<HH", record, 8)
    dest_width, dest_height = ((width + 7) & ~7) + 8, height
    rng = random.Random(0x35A60007)
    initial = bytes(rng.randrange(16) for _ in range(dest_width * dest_height))
    source_with_dims = record[8:12] + record[12:]
    src_off, dst_off, seg = 0x3000, 0x5000, 0xA000
    counts = 0
    digest = hashlib.sha256()
    for shift in range(8):
        dest = struct.pack("<HH", dest_width, dest_height) + pixel_to_planes(
            initial, dest_width, dest_height)
        case_call(machine, "o00_35A6_0007", f"type3-1200-shift-{shift}",
                  [src_off, seg, dst_off, seg, shift, 0],
                  writes=[(seg * 16 + src_off, source_with_dims),
                          (seg * 16 + dst_off, dest)],
                  observe=[behavior.Range("destination", seg * 16 + dst_off, len(dest))])
        original_bytes = machine.read(seg * 16 + dst_off, len(dest))
        original_pixels = planes_to_pixels(original_bytes[4:], dest_width, dest_height)

        pixels = (ctypes.c_uint8 * len(initial)).from_buffer_copy(initial)
        fb = PortableFramebuffer()
        status = lib.portable_framebuffer_init(ctypes.byref(fb), dest_width, dest_height,
                                               dest_width, pixels)
        if status:
            raise AssertionError(f"portable framebuffer init {status}")
        source = (ctypes.c_uint8 * len(record)).from_buffer_copy(record)
        status = lib.portable_bitmap_draw_resource(ctypes.byref(fb), shift, 0, source,
                                                   len(record))
        if status:
            raise AssertionError(f"portable type-3 draw {status} at shift {shift}")
        portable_pixels = bytes(pixels)
        if portable_pixels != original_pixels:
            mismatch = next(i for i, (a, b) in enumerate(zip(portable_pixels, original_pixels))
                            if a != b)
            raise AssertionError({"shift": shift, "first_pixel_mismatch": mismatch,
                                  "portable": portable_pixels[mismatch],
                                  "original": original_pixels[mismatch]})
        digest.update(bytes([shift]))
        digest.update(original_pixels)
        counts += 1
    return {"shift_cases": counts, "width": width, "height": height,
            "destination_width": dest_width, "matched_pixels": counts * dest_width * dest_height,
            "ordered_original_pixel_sha256": digest.hexdigest(), "mismatches": 0}


def parse_font(raw: bytes):
    metrics = struct.unpack_from(">13h", raw, 0)
    first, last = metrics[1], metrics[2]
    count = last - first + 3
    image_size = metrics[12] * metrics[7] * 2
    image = raw[26:26 + image_size]
    table_start = 26 + image_size
    loc = struct.unpack_from(">" + "h" * count, raw, table_start)
    ow = struct.unpack_from(">" + "h" * count, raw, table_start + 2 * count)
    return metrics, image, loc, ow, count


def original_font_probe(raw: bytes):
    metrics, image, loc, ow, count = parse_font(raw)
    seg, font_off, image_off, loc_off, ow_off, string_off = 0xA000, 0x3000, 0x4000, 0x6000, 0x6400, 0x6800
    font = bytearray(42)
    font[:26] = struct.pack("<13h", *metrics)
    font[26:30] = struct.pack("<HH", image_off, seg)
    font[30:34] = struct.pack("<HH", loc_off, seg)
    font[34:38] = struct.pack("<HH", ow_off, seg)
    font[38:42] = struct.pack("<hh", int((metrics[0] & 0x2000) == 0), last_missing(metrics))
    writes = [(seg * 16 + font_off, bytes(font)), (seg * 16 + image_off, image),
              (seg * 16 + loc_off, struct.pack("<" + "h" * count, *loc)),
              (seg * 16 + ow_off, struct.pack("<" + "h" * count, *ow))]
    machine = original_machine("_font_StringWidth")
    width_cases = []
    chars = [ord(" "), ord("A"), ord("m"), ord("0"), ord("?"), 255]
    for ch in chars:
        result = case_call(machine, "_font_CharWidth", f"font2-char-{ch}",
                           [ch, font_off, seg], writes=writes, return_kind="s16")
        width_cases.append((ch, result["return"]))
    transcript = hashlib.sha256()
    string_cases = [b"SimAnt 123", b"A m?0", bytes([32, 65, 109, 48, 63, 255])]
    for i, text in enumerate(string_cases):
        payload = text + b"\0"
        result = case_call(machine, "_font_StringWidth", f"font2-string-{i}",
                           [string_off, seg, font_off, seg],
                           writes=[*writes, (seg * 16 + string_off, payload)],
                           return_kind="s16")
        transcript.update(struct.pack("<h", result["return"]))
        transcript.update(payload)
    return {"font": "FONT2", "chars": width_cases, "string_cases": len(string_cases),
            "ordered_string_widths_sha256": transcript.hexdigest(), "table_count": count}


def last_missing(metrics):
    return metrics[2] - metrics[1] + 1


def portable_font_probe(lib, raw: bytes):
    font = PortableFont()
    lib.portable_font_init(ctypes.byref(font))
    source = (ctypes.c_uint8 * len(raw)).from_buffer_copy(raw)
    status = lib.portable_font_load(ctypes.byref(font), source, len(raw))
    if status:
        raise AssertionError(f"portable FONT2 load failed {status}")
    chars = [32, 65, 109, 48, 63, 255]
    widths = [(ch, lib.portable_font_char_width(ctypes.byref(font), ch)) for ch in chars]
    strings = [b"SimAnt 123", b"A m?0", bytes([32, 65, 109, 48, 63, 255])]
    string_widths = []
    for text in strings:
        chars_buf = (ctypes.c_uint8 * len(text)).from_buffer_copy(text)
        string_widths.append(lib.portable_font_string_width(ctypes.byref(font), chars_buf,
                                                            len(text)))
    lib.portable_font_destroy(ctypes.byref(font))
    return widths, string_widths


def original_font_raster_probe(raw: bytes, text: bytes):
    metrics, image, loc, ow, count = parse_font(raw)
    seg, font_off, image_off, loc_off, ow_off, string_off, bits_off = (
        0xA000, 0x3000, 0x4000, 0x6000, 0x6400, 0x6800, 0x7000)
    font = bytearray(42)
    font[:26] = struct.pack("<13h", *metrics)
    font[26:30] = struct.pack("<HH", image_off, seg)
    font[30:34] = struct.pack("<HH", loc_off, seg)
    font[34:38] = struct.pack("<HH", ow_off, seg)
    font[38:42] = struct.pack("<hh", int((metrics[0] & 0x2000) == 0), last_missing(metrics))
    bitmap_symbol = symbols.load()["data"]["fd_50F6_392C"]
    bitmap_address = bitmap_symbol["seg"] * 16 + bitmap_symbol["off"]
    bitmap = struct.pack("<HHHH", 0, 0, bits_off, seg)
    writes = [(seg * 16 + font_off, bytes(font)), (seg * 16 + image_off, image),
              (seg * 16 + loc_off, struct.pack("<" + "h" * count, *loc)),
              (seg * 16 + ow_off, struct.pack("<" + "h" * count, *ow)),
              (seg * 16 + string_off, text + b"\0"),
              (bitmap_address, bitmap), (seg * 16 + bits_off, bytes(1280))]
    machine = original_machine("font_MakeImage")
    result = case_call(machine, "font_MakeImage", "font2-makeimage-SimAnt123",
                       [string_off, seg, 0, font_off, seg], writes=writes,
                       observe=[behavior.Range("bitmap", bitmap_address, 8),
                                behavior.Range("glyph_bits", seg * 16 + bits_off, 1280)],
                       return_kind="farptr")
    object_bytes = machine.read(bitmap_address, 8)
    width, height, returned_bits_off, returned_bits_seg = struct.unpack("<HHHH", object_bytes)
    if returned_bits_off != bits_off or returned_bits_seg != seg:
        raise AssertionError({"font_bitmap_pointer": (returned_bits_off, returned_bits_seg)})
    row_bytes = (width + 7) // 8
    dos_bits = machine.read(seg * 16 + bits_off, row_bytes * height)
    return {"width": width, "height": height, "row_bytes": row_bytes,
            "bits": dos_bits, "bitmap_farptr": result["return"],
            "sha256": sha256(dos_bits)}


def portable_font_raster_probe(lib, raw: bytes, text: bytes, width: int, height: int):
    font = PortableFont()
    lib.portable_font_init(ctypes.byref(font))
    source = (ctypes.c_uint8 * len(raw)).from_buffer_copy(raw)
    if lib.portable_font_load(ctypes.byref(font), source, len(raw)):
        raise AssertionError("portable FONT2 load failed before raster comparison")
    pixels = (ctypes.c_uint8 * (width * height))()
    fb = PortableFramebuffer()
    if lib.portable_framebuffer_init(ctypes.byref(fb), width, height, width, pixels):
        raise AssertionError("portable font framebuffer init failed")
    chars = (ctypes.c_uint8 * len(text)).from_buffer_copy(text)
    end_x = ctypes.c_int32()
    if lib.portable_font_draw(ctypes.byref(fb), ctypes.byref(font), 0, 0, chars,
                              len(text), 1, ctypes.byref(end_x)):
        raise AssertionError("portable FONT2 glyph draw failed")
    row_bytes = (width + 7) // 8
    bits = bytearray(row_bytes * height)
    for y in range(height):
        for x in range(width):
            if pixels[y * width + x]:
                bits[y * row_bytes + (x >> 3)] |= 0x80 >> (x & 7)
    lib.portable_font_destroy(ctypes.byref(font))
    return {"width": end_x.value, "bits": bytes(bits), "sha256": sha256(bytes(bits))}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="simant-render-diff-",
                                     ignore_cleanup_errors=True) as tmp:
        lib_path = Path(tmp) / ("render.dll" if sys.platform == "win32" else "librender.so")
        compile_library(lib_path)
        lib = bind_library(lib_path)
        db = open_database(lib)
        try:
            packed = load_record(lib, db, 2500, 2)
            decoded = ctypes.POINTER(ctypes.c_uint8)()
            decoded_size = ctypes.c_size_t()
            packed_buf = (ctypes.c_uint8 * len(packed)).from_buffer_copy(packed)
            status = lib.portable_bitmap_decode_packed(packed_buf, len(packed),
                                                       ctypes.byref(decoded),
                                                       ctypes.byref(decoded_size))
            if status:
                raise AssertionError(f"portable packed decode failed: {status}")
            try:
                portable_decoded = ctypes.string_at(decoded, decoded_size.value)
            finally:
                lib.portable_bitmap_release_decoded(decoded)
            original_decoded = original_lzss_decode(packed, len(portable_decoded))
            reference = reference_lzss_decode(packed, len(portable_decoded))
            if reference != original_decoded:
                raise AssertionError("independent LZSS decode did not match the original DOS helper")
            if reference != portable_decoded:
                raise AssertionError("portable packed decoder did not match the independent decoder")
            if original_decoded != portable_decoded:
                mismatch = next(i for i, (a, b) in enumerate(zip(original_decoded,
                                                                 portable_decoded)) if a != b)
                raise AssertionError({"packed_first_byte_mismatch": mismatch,
                                      "original": original_decoded[mismatch],
                                      "portable": portable_decoded[mismatch],
                                      "original_context": original_decoded[mismatch - 8:mismatch + 8].hex(),
                                      "portable_context": portable_decoded[mismatch - 8:mismatch + 8].hex(),
                                      "reference_equal_original": reference == original_decoded,
                                      "reference_equal_portable": reference == portable_decoded})
            truncated = (ctypes.c_uint8 * (len(packed) - 128)).from_buffer_copy(packed[:-128])
            rejected_ptr = ctypes.POINTER(ctypes.c_uint8)()
            rejected_size = ctypes.c_size_t()
            rejected_status = lib.portable_bitmap_decode_packed(
                truncated, len(packed) - 128, ctypes.byref(rejected_ptr),
                ctypes.byref(rejected_size))
            if rejected_status != 2 or bool(rejected_ptr) or rejected_size.value != 0:
                raise AssertionError({"truncated_negative_control": rejected_status,
                                      "returned_size": rejected_size.value})
            type3 = load_record(lib, db, 1200, 2)
        finally:
            lib.portable_db_close(ctypes.byref(db))

        type3_report = type3_shift_probe(lib, original_machine("o00_35A6_0007"), type3)
        font_raw = (ROOT / "assets" / "FONT2").read_bytes()
        original_font = original_font_probe(font_raw)
        portable_widths, portable_strings = portable_font_probe(lib, font_raw)
        if original_font["chars"] != portable_widths:
            raise AssertionError({"font_char_widths": original_font["chars"],
                                  "portable": portable_widths})
        # Oracle hashes preserve exact ordered return values; compare by replaying
        # each value below rather than inferring from the hash.
        metrics, _, _, _, _ = parse_font(font_raw)
        text_cases = [b"SimAnt 123", b"A m?0", bytes([32, 65, 109, 48, 63, 255])]
        oracle_widths = []
        # Re-run with capture values so the byte-for-byte portable comparison is explicit.
        _, font_image, loc, ow, count = parse_font(font_raw)
        seg, font_off, image_off, loc_off, ow_off, string_off = 0xA000, 0x3000, 0x4000, 0x6000, 0x6400, 0x6800
        font = bytearray(42)
        font[:26] = struct.pack("<13h", *metrics)
        font[26:30] = struct.pack("<HH", image_off, seg)
        font[30:34] = struct.pack("<HH", loc_off, seg)
        font[34:38] = struct.pack("<HH", ow_off, seg)
        font[38:42] = struct.pack("<hh", int((metrics[0] & 0x2000) == 0), last_missing(metrics))
        writes = [(seg * 16 + font_off, bytes(font)), (seg * 16 + image_off, font_image),
                  (seg * 16 + loc_off, struct.pack("<" + "h" * count, *loc)),
                  (seg * 16 + ow_off, struct.pack("<" + "h" * count, *ow))]
        machine = original_machine("_font_StringWidth")
        for i, text in enumerate(text_cases):
            result = case_call(machine, "_font_StringWidth", f"font2-string-check-{i}",
                               [string_off, seg, font_off, seg],
                               writes=[*writes, (seg * 16 + string_off, text + b"\0")],
                               return_kind="s16")
            oracle_widths.append(result["return"])
        if oracle_widths != portable_strings:
            raise AssertionError({"font_string_widths": oracle_widths,
                                  "portable": portable_strings})
        raster_text = b"SimAnt 123"
        original_raster = original_font_raster_probe(font_raw, raster_text)
        portable_raster = portable_font_raster_probe(
            lib, font_raw, raster_text, original_raster["width"], original_raster["height"])
        if (portable_raster["width"] != original_raster["width"] or
                portable_raster["bits"] != original_raster["bits"]):
            mismatch = next((i for i, (a, b) in enumerate(zip(original_raster["bits"],
                                                              portable_raster["bits"]))
                             if a != b), None)
            raise AssertionError({"font_raster_first_byte_mismatch": mismatch,
                                  "original_sha256": original_raster["sha256"],
                                  "portable_sha256": portable_raster["sha256"]})

        report = {
            "schema": "portable-render-dos-differential-v1",
            "status": "DIAGNOSTIC_PASS_NO_ACCEPTANCE_CLAIM",
            "packed_resource_2500": {
                "record_bytes": len(packed), "decoded_bytes": len(original_decoded),
                "width": struct.unpack_from("<H", original_decoded, 8)[0],
                "height": struct.unpack_from("<H", original_decoded, 10)[0],
                "original_dos_sha256": sha256(original_decoded),
                "portable_sha256": sha256(portable_decoded), "mismatches": 0,
                "decoder": "f_1B05_0008 + f_1B05_0046; exact 12-byte header then 8-row blocks"},
            "type3_resource_1200": type3_report,
            "font_FONT2": {**original_font, "oracle_string_widths": oracle_widths,
                            "portable_string_widths": portable_strings,
                            "glyph_raster": {"entry": "font_MakeImage + f_2650_000F",
                                             "text": raster_text.decode("ascii"),
                                             "width": original_raster["width"],
                                             "height": original_raster["height"],
                                             "compared_bytes": len(original_raster["bits"]),
                                             "original_sha256": original_raster["sha256"],
                                             "portable_sha256": portable_raster["sha256"],
                                             "mismatches": 0},
                            "mismatches": 0},
            "negative_controls": {"packed_record_truncated_by_128_bytes": {
                "portable_status": "TRUNCATED_DATA", "allocated_output": False,
                "expected": True}},
            "source_contract_limits": [
                "Packed evidence compares decompressed PackHdr and payload bytes. It excludes Win16 display callbacks and physical VGA state.",
                "Type-3 evidence compares the complete planar destination buffer after original o00_35A6_0007 against indexed portable pixels converted to EGA planes; shifts 0 through 7 use the actual type-3 asset.",
                "Font evidence compares original _font_CharWidth and _font_StringWidth plus font_MakeImage/f_2650_000F glyph rasterization on loaded FONT2. Full physical display presentation is excluded.",
            ],
            "original_runtime": {"unicorn_version": unicorn.__version__,
                                 "dos_executable_sha256": sha256((ROOT / "assets/SIMANT.EXE").read_bytes()),
                                 "oracle_sha256": exe.EXPECTED_SHA256},
            "pins": {
                "packed_record_sha256": sha256(packed), "type3_record_sha256": sha256(type3),
                "font2_sha256": sha256(font_raw),
                "sources": {p: sha256((ROOT / p).read_bytes()) for p in [
                    "src/root/m1B05.asm", "src/root/m1CE2.c", "src/S00/m35A6.asm",
                    "src/root/m25E7.c", "src/root/m2650.asm",
                    "portable/game/resources/database.c", "portable/game/resources/database.h",
                    "portable/render/bitmap.c", "portable/render/bitmap.h",
                    "portable/render/font.c", "portable/render/font.h",
                    "portable/render/primitives.c", "portable/render/primitives.h",
                    "portable/tests/render/test_render.c",
                    "portable/tests/render/evidence/dos_render_differential.py",
                    "tools/behavior.py", "tools/functions.py", "tools/exe.py", "tools/symbols.py",
                    "layout/oracle.lock.json", "assets/SIMANT.EXE", "assets/HCEGANT.NDX",
                    "assets/HCEGANT.DAT", "assets/FONT2"]},
            },
        }
        rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8")
        print(rendered, end="")


if __name__ == "__main__":
    main()
