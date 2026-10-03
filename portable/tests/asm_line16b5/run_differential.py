#!/usr/bin/env python3
"""Compare the native line provider with frozen root:m16B5 machine code."""
from __future__ import annotations

import ctypes as ct
import _ctypes
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import random
import shutil
import struct
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
PORT = ROOT / "portable"
sys.path[:0] = [str(ROOT / "tools"), str(ROOT / "build" / "behavior" / "deps")]
import exe
import functions
import unicorn
from unicorn import x86_const as xr
import unicorn.unicorn_py3.unicorn as unicorn_impl

SOURCE = PORT / "whole_program/algorithms/line16b5.c"
HEADER = PORT / "whole_program/algorithms/line16b5.h"
ASM_SOURCE = ROOT / "src/root/m16B5.asm"
ORACLE_PATH = ROOT / "assets/SIMANT.EXE"
CS = 0x16B5
DS = 0x55B3
SS = 0x8000
SP = 0x8000
BITMAP_SEG = 0x6000
BITMAP_OFF = 0x0100
RETURN = (0xF000, 0x8000)
RETURN_LINEAR = RETURN[0] * 16 + RETURN[1]
MEMORY_SIZE = 0x110000


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def digest(path: Path) -> str:
    return sha(path.read_bytes())


def identity_name(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return "external:" + str(path)


def gcc_dependencies(compiler: Path) -> tuple[list[str], list[Path]]:
    command = [str(compiler), "-M", "-std=c11", "-I", str(PORT), str(SOURCE)]
    result = subprocess.run(command, cwd=ROOT, check=True, capture_output=True, text=True)
    flattened = result.stdout.replace("\\\n", " ").replace("\\\r\n", " ")
    if ":" not in flattened:
        raise RuntimeError("gcc -M returned no dependency rule")
    paths = []
    for token in flattened.split(":", 1)[1].split():
        path = Path(token)
        if not path.is_absolute():
            path = ROOT / path
        path = path.resolve()
        if not path.is_file():
            raise RuntimeError(f"gcc -M dependency is missing: {path}")
        paths.append(path)
    return command, sorted(set(paths))


class NativeState(ct.Structure):
    _fields_ = [
        ("width", ct.c_uint16), ("height", ct.c_uint16),
        ("mode", ct.c_uint16), ("row_offset", ct.c_uint16 * 200),
        ("plane_stride", ct.c_uint16),
        ("pixels", ct.POINTER(ct.c_uint8)), ("pixels_size", ct.c_size_t),
        ("initialized", ct.c_int),
    ]


def compiler_path() -> Path:
    compiler = os.environ.get("SIMANT_CC") or shutil.which("gcc")
    if compiler is None:
        raise RuntimeError("gcc was not found; set SIMANT_CC to the configured compiler")
    return Path(compiler).resolve()


def load_native(compiler: Path, temp: Path):
    output = temp / ("line16b5.dll" if os.name == "nt" else "line16b5.so")
    command = [str(compiler), "-std=c11", "-O2", "-Wall", "-Wextra",
               "-Wconversion", "-Werror", "-shared", "-I", str(PORT),
               str(SOURCE), "-o", str(output)]
    subprocess.run(command, cwd=ROOT, check=True)
    lib = ct.CDLL(str(output))
    init = lib.portable_line16b5_init
    init.argtypes = [ct.POINTER(NativeState), ct.c_uint16, ct.c_uint16,
                     ct.c_uint16, ct.POINTER(ct.c_uint8), ct.c_size_t]
    init.restype = ct.c_int
    draw = lib.portable_line16b5_draw
    draw.argtypes = [ct.POINTER(NativeState), ct.c_int16, ct.c_int16,
                     ct.c_int16, ct.c_int16, ct.c_int16]
    draw.restype = ct.c_int
    return lib, output, command


class DosLineOracle:
    def __init__(self):
        self.image = exe.load()
        self.entry_init = functions.get("f_16B5_0033")
        self.entry_draw = functions.get("f_16B5_0008")
        if (self.entry_init["unit"], self.entry_init["seg"], self.entry_init["off"]) != \
                ("root", CS, 0x33):
            raise RuntimeError("f_16B5_0033 address changed from frozen root entry")
        if (self.entry_draw["unit"], self.entry_draw["seg"], self.entry_draw["off"]) != \
                ("root", CS, 8):
            raise RuntimeError("f_16B5_0008 address changed from frozen root entry")

    def render(self, width: int, height: int, mode: int, initial: bytes,
               lines: list[tuple[int, int, int, int, int]]) -> bytes:
        cpu = unicorn.Uc(unicorn.UC_ARCH_X86, unicorn.UC_MODE_16)
        cpu.mem_map(0, MEMORY_SIZE)
        cpu.mem_write(0, self.image.image)
        for section in self.image.sections:
            cpu.mem_write(section.load_linear, section.data)

        data = DS * 16
        # The source object's code-offset tables live in its mutable DGROUP.
        # Values are named MASM procedures from m16B5.asm, not lifted code.
        cpu.mem_write(data + 0x1E00, struct.pack("<3H", 0x007F, 0x00AB, 0x00A5))
        cpu.mem_write(data + 0x1F98, struct.pack("<3H", 0x00B1, 0x03B5, 0x01D4))
        base = BITMAP_SEG * 16 + BITMAP_OFF
        cpu.mem_write(base, struct.pack("<HH", width, height) + initial)

        def call(entry: int, args: tuple[int, ...]) -> None:
            frame = struct.pack("<2H" + "H" * len(args), RETURN[1], RETURN[0],
                                *(value & 0xFFFF for value in args))
            cpu.mem_write(SS * 16 + SP, frame)
            regs = ((xr.UC_X86_REG_SS, SS), (xr.UC_X86_REG_SP, SP),
                    (xr.UC_X86_REG_CS, CS), (xr.UC_X86_REG_IP, entry),
                    (xr.UC_X86_REG_DS, DS), (xr.UC_X86_REG_ES, BITMAP_SEG),
                    (xr.UC_X86_REG_EFLAGS, 2))
            for reg, value in regs:
                cpu.reg_write(reg, value)
            cpu.emu_start(CS * 16 + entry, RETURN_LINEAR, count=1_000_000)
            if (cpu.reg_read(xr.UC_X86_REG_CS), cpu.reg_read(xr.UC_X86_REG_IP)) != RETURN:
                raise RuntimeError(f"DOS entry {entry:04X} did not return within budget")

        call(0x0033, (BITMAP_OFF, BITMAP_SEG, mode))
        for line in lines:
            call(0x0008, line)
        return bytes(cpu.mem_read(base + 4, len(initial)))


def native_render(lib, width: int, height: int, mode: int, initial: bytes,
                  lines: list[tuple[int, int, int, int, int]]) -> bytes:
    pixels = (ct.c_uint8 * len(initial)).from_buffer_copy(initial)
    state = NativeState()
    if not lib.portable_line16b5_init(ct.byref(state), width, height, mode,
                                      pixels, len(initial)):
        raise RuntimeError("native line-state initialization rejected source case")
    for line in lines:
        if not lib.portable_line16b5_draw(ct.byref(state), *line):
            raise RuntimeError(f"native draw rejected source case: {line!r}")
    return bytes(pixels)


def negative_controls(lib) -> dict[str, bool]:
    state = NativeState()
    pixels = (ct.c_uint8 * 1)()
    checks = {
        "null_state": lib.portable_line16b5_init(None, 1, 1, 0, pixels, 1) == 0,
        "zero_width": lib.portable_line16b5_init(ct.byref(state), 0, 1, 0,
                                                  pixels, 1) == 0,
        "bad_mode": lib.portable_line16b5_init(ct.byref(state), 1, 1, 3,
                                                pixels, 1) == 0,
        "non_square_source_clipper": lib.portable_line16b5_init(
            ct.byref(state), 112, 84, 1, pixels, 1) == 0,
        "undersized_mode1": lib.portable_line16b5_init(ct.byref(state), 84, 84, 1,
                                                        pixels, 1) == 0,
        "height_over_row_table": lib.portable_line16b5_init(
            ct.byref(state), 8, 201, 0, pixels, 201) == 0,
    }
    if not all(checks.values()):
        raise RuntimeError("native line source-domain negative control failed")
    return checks


def cases():
    fixed = [
        (0, 112, 112, [(0, 0, 111, 111, 1)]),
        (0, 112, 112, [(111, 0, 0, 111, 0)]),
        (1, 84, 84, [(0, 83, 83, 0, 15)]),
        (1, 84, 84, [(-40, 18, 121, 65, 9)]),
        (2, 112, 112, [(111, 111, 0, 0, 6)]),
        (2, 112, 112, [(-19, -13, 125, 126, 12)]),
        (2, 84, 84, [(42, -200, 42, 300, 7)]),
        (1, 112, 112, [(0, 0, 111, 0, 0), (111, 111, 0, 111, 10)]),
    ]
    yield from ((mode, width, height, lines, "directed")
                for mode, width, height, lines in fixed)
    rng = random.Random(0x16B50008)
    for mode, width, height in ((0, 112, 112), (1, 84, 84), (2, 112, 112),
                                (1, 112, 112)):
        for _ in range(64):
            lines = []
            for _ in range(4):
                lines.append((rng.randrange(-24, width + 25),
                              rng.randrange(-24, height + 25),
                              rng.randrange(-24, width + 25),
                              rng.randrange(-24, height + 25),
                              rng.randrange(-32768, 32768)))
            yield mode, width, height, lines, "random"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", default="portable/tests/asm_line16b5/evidence/dos-native-v2.json")
    args = parser.parse_args()
    report_path = (ROOT / args.report).resolve()
    if report_path.exists():
        raise SystemExit(f"refusing to overwrite immutable report: {report_path}")
    compiler = compiler_path()
    oracle = DosLineOracle()
    compared = 0
    mismatches = []
    identity_paths = [SOURCE, HEADER, ASM_SOURCE, ORACLE_PATH,
        ROOT / "src/root/m0250.c", ROOT / "src/root/m1B4E.asm",
        PORT / "whole_program/types/fonts.h",
        ROOT / "tools/exe.py", ROOT / "tools/functions.py", ROOT / "tools/symbols.py",
        ROOT / "layout/functions.json", ROOT / "layout/symbols.json",
        Path(__file__).resolve(), Path(unicorn.__file__).resolve(),
        Path(unicorn_impl.__file__).resolve(), Path(unicorn_impl.uclib._name).resolve()]
    identity_paths.extend(sorted(Path(unicorn.__file__).resolve().parent.rglob("*.py")))
    identity_paths.append(Path(sys.executable).resolve())
    for module_name in ("argparse", "ctypes", "hashlib", "json", "os", "pathlib",
                        "platform", "random", "shutil", "struct", "subprocess",
                        "sys", "tempfile"):
        module = sys.modules.get(module_name)
        module_path = Path(getattr(module, "__file__", "")) if module else None
        if module_path is not None and module_path.is_file():
            identity_paths.append(module_path.resolve())
    dependency_command, compile_dependencies = gcc_dependencies(compiler)
    identity_paths.extend(compile_dependencies)
    identity_paths = sorted(set(path.resolve() for path in identity_paths))
    compiler_tools = {}
    for tool_name in ("cc1", "collect2", "as", "ld"):
        value = subprocess.check_output([str(compiler), f"-print-prog-name={tool_name}"],
                                        text=True).strip()
        tool_path = Path(value)
        if not tool_path.is_absolute():
            tool_path = (compiler.parent / tool_path).resolve()
        if tool_path.is_file():
            compiler_tools[tool_name] = {"path": str(tool_path), "sha256": digest(tool_path)}
            identity_paths.append(tool_path.resolve())
    identity_paths.append(compiler)
    identity_paths = sorted(set(identity_paths))
    before = {identity_name(path): digest(path)
              for path in identity_paths}
    with tempfile.TemporaryDirectory(prefix="simant-line16b5-",
                                     ignore_cleanup_errors=True) as directory:
        lib, output, compile_command = load_native(compiler, Path(directory))
        negatives = negative_controls(lib)
        for mode, width, height, lines, category in cases():
            row_step = (width >> 3) if mode == 0 else (width >> 1)
            initial = bytes(((n * 37 + mode * 11 + width) & 0xFF)
                            for n in range(row_step * height))
            expected = oracle.render(width, height, mode, initial, lines)
            actual = native_render(lib, width, height, mode, initial, lines)
            if expected != actual:
                first = next((i for i, (a, b) in enumerate(zip(expected, actual))
                              if a != b), min(len(expected), len(actual)))
                diagnosis = None
                for line_index in range(len(lines)):
                    prefix = lines[:line_index + 1]
                    dos_prefix = oracle.render(width, height, mode, initial, prefix)
                    native_prefix = native_render(lib, width, height, mode, initial, prefix)
                    if dos_prefix != native_prefix:
                        diagnosis = {"line_index": line_index,
                                     "line": prefix[-1],
                                     "prefix": prefix}
                        break
                mismatches.append({"category": category, "mode": mode,
                    "width": width, "height": height, "lines": lines,
                    "first_mismatch_line": diagnosis,
                    "first_byte": first,
                    "dos": expected[first] if first < len(expected) else None,
                    "native": actual[first] if first < len(actual) else None})
                break
            compared += 1

        if mismatches:
            _ctypes.FreeLibrary(lib._handle)
            raise RuntimeError("native/original m16B5 mismatch: " +
                               json.dumps(mismatches[0], sort_keys=True))

        # Adapter controls use m0250's exact two-word prefix plus inline bytes.
        lib.f_16B5_0033.argtypes = [ct.c_void_p, ct.c_int16]
        lib.f_16B5_0008.argtypes = [ct.c_int16] * 5
        adapter_cases = [(0, 112, 112, [(0, 111, 111, 0, 1)]),
                         (1, 84, 84, [(0, 0, 83, 83, 13)]),
                         (2, 112, 112, [(111, 0, 0, 111, 7)])]
        for mode, width, height, lines in adapter_cases:
            row_step = (width >> 3) if mode == 0 else (width >> 1)
            inline = (ct.c_uint8 * (4 + row_step * height))()
            struct.pack_into("<HH", inline, 0, width, height)
            lib.f_16B5_0033(ct.cast(inline, ct.c_void_p), mode)
            for line in lines:
                lib.f_16B5_0008(*line)
            adapter_bytes = bytes(inline)[4:]
            expected_adapter = oracle.render(width, height, mode,
                                              bytes(row_step * height), lines)
            if adapter_bytes != expected_adapter:
                _ctypes.FreeLibrary(lib._handle)
                raise RuntimeError(f"legacy inline adapter differs from typed view mode={mode}")
            lib.portable_line16b5_unbind()

        after = {identity_name(path): digest(path)
                 for path in identity_paths}
        if before != after:
            _ctypes.FreeLibrary(lib._handle)
            raise RuntimeError("source/test/oracle/runtime closure changed during comparison")
        gcc_version = subprocess.check_output([str(compiler), "--version"], text=True).splitlines()[0]
        report = {
            "schema": "root-m16b5-line-provider-dos-native-v1",
            "status": "pass",
            "receipt_path": identity_name(report_path),
            "proof_boundary": "frozen 16-bit root machine code at f_16B5_0033/f_16B5_0008, direct Unicorn execution; native C pixels compared byte-for-byte",
            "runner": {"python": sys.version.split()[0], "platform": platform.platform(),
                       "unicorn": unicorn.__version__, "compiler": gcc_version,
                       "compiler_path": str(compiler), "compiler_sha256": digest(compiler),
                       "compiler_tools": compiler_tools,
                       "preprocessor_dependency_command": dependency_command,
                       "preprocessor_dependencies": [identity_name(p) for p in compile_dependencies],
                       "compile_command": compile_command},
            "oracle": {"path": "assets/SIMANT.EXE", "sha256": oracle.image.sha256,
                       "asm_source": {"path": "src/root/m16B5.asm",
                                      "sha256": digest(ASM_SOURCE)},
                       "caller_source": {"path": "src/root/m0250.c",
                                         "sha256": digest(ROOT / "src/root/m0250.c")},
                       "bitmap_adapter_source": {"path": "src/root/m1B4E.asm",
                                                 "sha256": digest(ROOT / "src/root/m1B4E.asm")},
                       "entries": {"f_16B5_0033": oracle.entry_init,
                                   "f_16B5_0008": oracle.entry_draw}},
            "runtime": {"native_library_sha256": digest(output),
                        "unicorn_package": str(Path(unicorn.__file__).resolve()),
                        "unicorn_package_sha256": digest(Path(unicorn.__file__).resolve()),
                        "unicorn_loaded_library": str(Path(unicorn_impl.uclib._name).resolve()),
                        "unicorn_loaded_library_sha256": digest(Path(unicorn_impl.uclib._name).resolve())},
            "current_inputs_before": before,
            "current_inputs_after": after,
            "current_inputs_unchanged": True,
            "native_inputs": {"portable/whole_program/algorithms/line16b5.c": digest(SOURCE),
                              "portable/whole_program/algorithms/line16b5.h": digest(HEADER)},
            "case_count": compared,
            "all_native_pixels_equal": True,
            "negative_controls": negatives,
            "legacy_inline_adapter_matches_typed_view": len(adapter_cases),
            "case_scope": "mode 0/1/2; square 84/112 source geometries (mode/size cross-combinations where payload span is safe); signed-word endpoints sampled within [-4096,4096]; fixed-seed randomized line sets; typed API rejects nonsquare source geometry and checks payload capacity",
            "source_domain": {"inline_width_max": 112, "inline_height_max": 112,
                              "max_inline_allocation_bytes": 6276,
                              "payload_max_bytes": 6272,
                              "draw_spider_dimensions": "m0250 sets width=7*g_19BE and height=7*g_19C0; g_19BE/g_19C0 initialize to 16 and are both set to 12 in g_5A97 case 2",
                              "mode_geometry": {"mode_0": "g_5A97 odd; 112x112 at default tile size; 1bpp", "mode_1": "g_5A97==2; 84x84; packed 4bpp", "mode_2": "otherwise; 112x112 at default tile size; four 1bpp planes"},
                              "nonsquare_geometry": "excluded: source clipper compares y against width-1 and x against height-1 while init builds height row entries; rectangular inputs can exceed the initialized row table",
                              "historic_inline_object_extent": "not recovered; 6276-byte native owner upper bound derives from m0250 DrawSpider dimensions and m16B5 write-address formulas"},
        }
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(
            json.dumps(report, indent=2) + "\n", encoding="utf-8")
        _ctypes.FreeLibrary(lib._handle)
    print(f"PASS original DOS m16B5 line provider cases={compared} inline_adapters=3")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
