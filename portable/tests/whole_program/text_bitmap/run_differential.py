#!/usr/bin/env python3
"""Compare native text-bitmap preparation with original root:m1FBD ASM."""
from __future__ import annotations

import hashlib
import json
import random
import struct
import subprocess
import sys
from types import SimpleNamespace
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "tools"))
import behavior as b

HERE = Path(__file__).resolve().parent
OUT = HERE / "evidence" / "text-bitmap-original-dos-v1.json"
BUILD = ROOT / "build/workers/whole_program/text_bitmap"
FONT_LINEAR = 0xA8100
FONT_SEG, FONT_OFF = 0xA810, 0
TEXT_LINEAR = 0xA9000
TEXT_SEG, TEXT_OFF = 0xA900, 0
INITIAL_STATE = {
    "width": 0xCDEF,
    "height": 0xABCD,
    "pen_x": 0x1234,
    "pen_y": 0x5678,
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def word(value: int) -> bytes:
    return struct.pack("<H", value & 0xffff)


def far(offset: int, segment: int) -> bytes:
    return struct.pack("<HH", offset & 0xffff, segment & 0xffff)


def glyph_data(height: int) -> bytes:
    return bytes(((code * 29 + row * 71) ^
                  ((code >> (row % 5)) * 11) ^
                  (0x81 >> (row % 8))) & 0xff
                 for code in range(256) for row in range(height))


def initial_pixels(seed: int) -> bytes:
    rng = random.Random(seed)
    return bytes(rng.randrange(256) for _ in range(1040))


def callback_bitmap(machine, args):
    x, y, offset, segment = args
    address = segment * 16 + offset
    header = machine.read(address, 4)
    width, height = struct.unpack("<HH", header)
    machine.state["text_bitmap_callbacks"].append({
        "kind": "bitmap", "x": x, "y": y, "width": width, "height": height,
        "pixels_hex": machine.read(address + 4, 1040).hex(),
    })


def callback_direct(machine, args):
    x, y, offset, segment = args
    text = bytearray()
    address = segment * 16 + offset
    for i in range(256):
        ch = machine.read(address + i, 1)[0]
        text.append(ch)
        if ch == 0:
            break
    machine.state["text_bitmap_callbacks"].append({
        "kind": "direct", "x": x, "y": y, "text_hex": bytes(text).hex(),
    })


def dos_case(pair, index, profile, char_width, cell_height, glyph_height,
             text, x, y, pixels):
    source_machine = pair.original_machine
    if not text:
        memory_text = b"\0"
    elif b"\0" not in text and len(text) < 80:
        memory_text = text + b"\0"
    else:
        memory_text = text[:80]
    font = glyph_data(glyph_height)
    fold_window = source_machine.read(b.symbol_address("g_5FBE"), 256)
    writes = [
        (FONT_LINEAR, font),
        (TEXT_LINEAR, memory_text),
        (b.symbol_address("g_3DD6"), far(FONT_OFF, FONT_SEG)),
        (b.symbol_address("g_3DDA"), word(glyph_height)),
        (b.symbol_address("g_3DDC"), bytes([cell_height])),
        (b.symbol_address("g_3DDE"), bytes([char_width])),
        (b.symbol_address("g_5A97"), bytes([profile])),
        (b.symbol_address("g_5ABA"), word(INITIAL_STATE["width"])),
        (b.symbol_address("g_5ABC"), word(INITIAL_STATE["height"])),
        (b.symbol_address("g_5ABE"), pixels),
        (b.symbol_address("g_5ECE"), b"\xa5" * 79),
        (b.symbol_address("g_5F1D"), b"\xa5"),
        (b.symbol_address("g_3DA0"), word(INITIAL_STATE["pen_x"])),
        (b.symbol_address("g_3DA2"), word(INITIAL_STATE["pen_y"])),
    ]
    case = b.Case(
        f"whole-program/text-bitmap/{index}",
        args=[x, y, TEXT_OFF, TEXT_SEG], writes=writes,
        callbacks={
            "f_1B4E_005E": b.Callback(4, callback_bitmap),
            "f_1B4E_0081": b.Callback(4, callback_direct),
        },
        return_kind="void",
        metadata={"contract": "original root:m1FBD text bitmap software path; original drawing helpers intercepted only as ordered sinks"},
    )
    case.state["text_bitmap_callbacks"] = []
    result = source_machine.run(case)
    final = {
        "width": struct.unpack("<H", source_machine.read(b.symbol_address("g_5ABA"), 2))[0],
        "height": struct.unpack("<H", source_machine.read(b.symbol_address("g_5ABC"), 2))[0],
        "pixels_hex": source_machine.read(b.symbol_address("g_5ABE"), 1040).hex(),
        "copied_text_hex": (source_machine.read(b.symbol_address("g_5ECE"), 79) +
                            source_machine.read(b.symbol_address("g_5F1D"), 1)).hex(),
        "pen_x": struct.unpack("<H", source_machine.read(b.symbol_address("g_3DA0"), 2))[0],
        "pen_y": struct.unpack("<H", source_machine.read(b.symbol_address("g_3DA2"), 2))[0],
        "callbacks": source_machine.state["text_bitmap_callbacks"],
        "return": result.get("return"),
    }
    return case, final, font, fold_window


def compile_native() -> tuple[Path, list[str]]:
    BUILD.mkdir(parents=True, exist_ok=True)
    executable = BUILD / "text-bitmap-native.exe"
    sources = [HERE / "text_bitmap_driver.c",
               ROOT / "portable/whole_program/text_bitmap.c"]
    command = ["gcc", "-std=c11", "-O2", "-Wall", "-Wextra", "-Wconversion",
               "-Werror", "-I", str(ROOT), *(str(p) for p in sources),
               "-o", str(executable)]
    subprocess.run(command, cwd=ROOT, check=True, capture_output=True, text=True)
    return executable, command


def native_case(executable, profile, width, cell_height, glyph_height,
                text, x, y, font, fold_window, pixels):
    args = [str(executable), str(profile), str(width), str(cell_height),
            str(glyph_height), str(x & 0xffff), str(y & 0xffff),
            text.hex(), font.hex(), fold_window.hex(), pixels.hex()]
    run = subprocess.run(args, cwd=ROOT, check=True, capture_output=True, text=True)
    return json.loads(run.stdout)


def cases():
    directed = [
        (0, 8, 8, 8, b"A", 11, 13),
        (0, 8, 14, 14, b"ABCD", 0x7fff, 0xfffe),
        (0, 4, 6, 6, b"AB", 3, 4),
        (0, 4, 6, 6, b"ABC", 7, 9),
        (0, 4, 6, 6, bytes([0x80, 0xa7]), 15, 17),
        (0, 4, 6, 6, bytes([ord("Z"), 0x81, ord("x")]), 19, 21),
        (8, 4, 6, 6, b"A", 1, 2),
        (6, 8, 14, 14, b"direct font 6", 22, 24),
        (0, 8, 14, 14, b"", 31, 32),
        (0, 8, 14, 14, b"Z" * 74, 41, 43),
        (0, 4, 6, 6, b"Q" * 79, 51, 53),
    ]
    rng = random.Random(0x1FBD0000)
    random_cases = []
    for _ in range(120):
        mode = rng.randrange(3)
        if mode == 0:
            width, cell, height = 8, 14, 14
            text = bytes(rng.randrange(1, 128) for _ in range(rng.randrange(1, 40)))
        elif mode == 1:
            width, cell, height = 8, 8, 8
            text = bytes(rng.randrange(1, 128) for _ in range(rng.randrange(1, 60)))
        else:
            width, cell, height = 4, 6, 6
            alphabet = list(range(1, 128)) + list(range(0x80, 0xa8))
            text = bytes(rng.choice(alphabet) for _ in range(rng.randrange(1, 80)))
        random_cases.append((0, width, cell, height, text,
                             rng.randrange(0x10000), rng.randrange(0x10000)))
    return directed + random_cases


def main() -> int:
    if OUT.exists():
        raise SystemExit(f"refusing to overwrite differential report: {OUT}")
    native_exe, command = compile_native()
    executable = b.exe.load()
    function = b.functions.get("f_1FBD_0000")
    fixture_pair = SimpleNamespace(
        function=function,
        vectors={b.exe.MANAGER_SEG * 16 + vector.offset: vector
                 for vector in executable.vectors},
        identity={"oracle_sha256": executable.sha256},
        delegate={},
        sequence_function=lambda name: b.functions.get(name),
    )
    pair = SimpleNamespace(original_machine=b.Machine(fixture_pair),
                           identity={"oracle_sha256": executable.sha256,
                                     "harness_sha256": b.digest(b.HARNESS_SOURCE)},
                           function=function)
    fold_table = pair.original_machine.read(b.symbol_address("g_5FBE"), 40)
    expected_fold = b"cueaaaaceeeiiiAAEaAooouuyoucLYPfaiounNao"
    if fold_table != expected_fold:
        raise RuntimeError(f"original initialized fold bytes changed: {fold_table!r}")

    rows = []
    mismatches = []
    for index, (profile, width, cell, height, text, x, y) in enumerate(cases()):
        pixels = initial_pixels(index * 17 + 9)
        case, original, font, fold_window = dos_case(
            pair, index, profile, width, cell, height, text, x, y, pixels)
        memory_text = text if b"\0" in text or len(text) >= 80 else text + b"\0"
        native = native_case(native_exe, profile, width, cell, height, memory_text,
                             x, y, font, fold_window, pixels)
        compare = {
            "status": native["status"] == 0,
            "pixels": native["pixels_hex"] == original["pixels_hex"],
            "copy": native["text_copy_hex"] == original["copied_text_hex"],
            "width": native["width"] == original["width"],
            "height": native["height"] == original["height"],
            "pen": (native["pen_x"], native["pen_y"]) ==
                   (original["pen_x"], original["pen_y"]),
        }
        expected_kind = (2 if profile == 6 else
                         (0 if not text else 1))
        compare["draw_kind"] = native["draw_kind"] == expected_kind
        if profile == 6:
            callback_equal = original["callbacks"] == [{
                "kind": "direct", "x": x & 0xffff, "y": y & 0xffff,
                "text_hex": (text if b"\0" in text else text + b"\0").hex(),
            }]
            compare["ordered_sink"] = callback_equal
        elif text:
            callback = original["callbacks"]
            compare["ordered_sink"] = (len(callback) == 1 and
                callback[0]["kind"] == "bitmap" and callback[0]["x"] == (x & 0xffff) and
                callback[0]["y"] == (y & 0xffff) and
                callback[0]["width"] == original["width"] and
                callback[0]["height"] == original["height"])
        else:
            compare["ordered_sink"] = original["callbacks"] == []
        equal = all(compare.values())
        row = {"case": case.label, "mode": [profile, width, cell, height],
               "text_hex": text.hex(), "x": x & 0xffff, "y": y & 0xffff,
               "equal": equal, "comparison": compare,
               "native_status": native["status"],
               "native_draw_kind": native["draw_kind"],
               "oracle_callbacks": original["callbacks"]}
        rows.append(row)
        if not equal:
            mismatches.append({"index": index, "row": row,
                               "native": native, "oracle": original})
    if mismatches:
        bad = BUILD / "text-bitmap-mismatches.json"
        bad.write_text(json.dumps(mismatches, indent=2) + "\n", encoding="utf-8")
        raise RuntimeError(f"{len(mismatches)} source differential mismatches; minimized details: {bad}")

    source_paths = ["src/root/m1FBD.asm", "src/root/m1B4E.asm",
                    "portable/whole_program/text_bitmap.h",
                    "portable/whole_program/text_bitmap.c",
                    "portable/tests/whole_program/text_bitmap/text_bitmap_driver.c",
                    "portable/tests/whole_program/text_bitmap/run_differential.py",
                    "tools/behavior.py", "tools/exe.py", "tools/functions.py",
                    "tools/match.py", "tools/modctx.py", "tools/modules.py",
                    "layout/oracle.lock.json", "assets/SIMANT.EXE"]
    report = {
        "schema": "whole-program-text-bitmap-dos-differential-v1",
        "status": "PASS_BOUNDED_ORIGINAL_ASM_CONTRACT",
        "claim_scope": "Native software raster preparation matches the original root:m1FBD assembly for the recorded controlled glyph/font/text domain. f_1B4E_005E and f_1B4E_0081 remain explicit draw sinks; this does not claim framebuffer/device pixel equivalence.",
        "original": {"target": "f_1FBD_0000", "address": {
                         key: pair.function[key] for key in ("unit", "seg", "off", "size")},
                     "oracle_sha256": pair.identity["oracle_sha256"],
                     "harness_sha256": pair.identity["harness_sha256"],
                     "unicorn_version": b.uc.__version__},
        "abi": {"source": "src/root/m1FBD.asm: _f_1FBD_0000 proc far reads x/y/far-string at BP+6/+8/+0A; retf pops no args",
                "stack_words": 4, "callee_pop_bytes": 0},
        "source_contract": {
            "profile6": "Direct f_1B4E_0081(x,y,text) path; bitmap globals and pen remain untouched.",
            "other_profiles": "Copies at most 79 text bytes; g5ABC receives g3DDC; empty strings stop before raster call; g3DDE==8 copies complete glyph bytes into one byte per cell; other supported profile width 4 folds source bytes 80h..A7h and combines two glyph nibbles per output byte.",
            "statefulness": "The assembly writes only covered output bytes. The native state accepts an existing 1040-byte pixel buffer so stale low nibbles, odd final cells, and untouched tail are preserved exactly.",
            "fold_table": {"literal_bytes_hex": fold_table.hex(), "length": len(fold_table),
                           "source_anchor": "m1FBD.asm `_g_5FBE db` literal; high characters index the live 256-byte DGROUP window at raw byte value, as encoded by `mov bl,al; mov al,[bx+_g_5FBE]`.",
                           "runtime_lookup_window_sha256": sha(fold_window)},
            "sink_boundary": "f_1B4E_005E is intercepted after original bitmap preparation; f_1B4E_0081 is intercepted on profile 6. Exact sink x/y/payload are compared, not physical rendering.",
        },
        "cases": rows,
        "case_count": len(rows),
        "random_seed": "0x1FBD0000",
        "negative_controls": [
            "Directed odd-width-4 case starts from nonzero destination bytes; clearing rather than preserving the final low nibble/tail would mismatch the original.",
            "Accented 80h/A7h case compares the source raw-index lookup window; a normalized index-minus-80 fold-table mutant produces different bitmap bytes.",
        ],
        "native": {"command": command, "executable_sha256": sha(native_exe.read_bytes())},
        "input_sha256": {name: sha((ROOT / name).read_bytes()) for name in source_paths},
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(OUT), "cases": len(rows),
                      "mismatches": 0, "status": report["status"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
