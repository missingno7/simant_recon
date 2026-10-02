"""Direct original-DOS checks for portable large-model memory adapters."""
from __future__ import annotations

import argparse
import ctypes
import gc
import hashlib
import json
import random
import sys
import tempfile
from functools import lru_cache
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[4]
sys.path[:0] = [str(ROOT / "tools")]
import behavior  # noqa: E402
import exe  # noqa: E402
import functions  # noqa: E402
import symbols  # noqa: E402
import unicorn  # noqa: E402


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def portable_library(path: Path):
    import subprocess

    subprocess.run(["gcc", "-std=c11", "-Wall", "-Wextra", "-Wconversion", "-Werror",
                    "-pedantic", "-shared", "portable/platform/memory.c",
                    "portable/game/recovered/memory_adapter.c", "-o", str(path)],
                   cwd=ROOT, check=True, capture_output=True, text=True)
    lib = ctypes.CDLL(str(path.resolve()))
    lib.portable_fmemcpy.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint16]
    lib.portable_fmemcpy.restype = ctypes.c_void_p
    lib.portable_fmemmove.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint16]
    lib.portable_fmemmove.restype = ctypes.c_void_p
    lib.portable_block_move.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint16]
    lib.portable_block_move.restype = None
    lib.portable_abs16.argtypes = [ctypes.c_int16]
    lib.portable_abs16.restype = ctypes.c_int16
    lib.BlockMove.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int32]
    lib.BlockMove.restype = None
    return lib


@lru_cache(maxsize=8)
def original_machine(name: str):
    first = functions.get(name)
    vectors = {exe.MANAGER_SEG * 16 + vector.offset: vector for vector in exe.load().vectors}
    pair = SimpleNamespace(function=first, sequence_targets=frozenset(),
                           sequence_function=lambda n: functions.get(n), vectors=vectors)
    return behavior.Machine(pair)


def original_copy(function: str, source: bytes, dst_offset: int, src_offset: int,
                  count: int) -> dict:
    segment, base = 0xA000, 0x2000
    initial = bytearray(source)
    machine = original_machine(function)
    args = [dst_offset, segment, src_offset, segment, count]
    result = machine.run(behavior.Case(
        label=f"{function}-{dst_offset:04x}-{src_offset:04x}-{count}",
        args=args,
        writes=[(segment * 16 + base, bytes(initial))],
        observe=[behavior.Range("buffer", segment * 16 + base, len(initial))],
        return_kind="farptr"), function=function)
    return {"result": result, "bytes": machine.read(segment * 16 + base, len(initial)),
            "segment": segment}


def call_portable_copy(lib, function: str, source: bytes, dst_offset: int,
                       src_offset: int, count: int) -> tuple[bytes, int]:
    buf = (ctypes.c_uint8 * len(source)).from_buffer_copy(source)
    dst = ctypes.addressof(buf) + (dst_offset - 0x2000)
    src = ctypes.addressof(buf) + (src_offset - 0x2000)
    if function == "fmemcpy":
        returned = lib.portable_fmemcpy(dst, src, count)
    elif function == "fmemmove":
        returned = lib.portable_fmemmove(dst, src, count)
    else:
        raise AssertionError(function)
    return bytes(buf), int(returned or 0)


def machine_call(name: str, args: list[int], writes: list[tuple[int, bytes]],
                 observe: list[behavior.Range], return_kind: str = "s16"):
    machine = original_machine(name)
    result = machine.run(behavior.Case(label=f"{name}-oracle", args=args,
                                       writes=writes, observe=observe,
                                       return_kind=return_kind), function=name)
    return machine, result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    rng = random.Random(0xF3E0_0244)
    errors = []
    copy_cases = 0
    overlap_difference_seen = False
    segment = 0xA000
    base = 0x2000
    cases = [
        ("fmemcpy", 0x2040, 0x2010, 27),
        ("fmemcpy", 0x2003, 0x2000, 20),
        ("fmemcpy", 0x2000, 0x2003, 20),
        ("fmemcpy", 0x2030, 0x2010, 0),
        ("fmemmove", 0x2040, 0x2010, 27),
        ("fmemmove", 0x2003, 0x2000, 20),
        ("fmemmove", 0x2000, 0x2003, 20),
        ("fmemmove", 0x2030, 0x2010, 0),
    ]
    for _ in range(8):
        src = base + rng.randrange(8, 40)
        dst = base + rng.randrange(8, 40)
        count = rng.randrange(0, 26)
        method = "fmemcpy" if rng.randrange(2) == 0 else "fmemmove"
        cases.append((method, dst, src, count))

    with tempfile.TemporaryDirectory(prefix="simant-memory-oracle-",
                                     ignore_cleanup_errors=True) as temp:
        lib = portable_library(Path(temp) / ("memory.dll" if sys.platform == "win32"
                                             else "libmemory.so"))
        for index, (method, dst, src, count) in enumerate(cases):
            if args.verbose:
                print(f"copy case {index}/{len(cases)} {method} {dst:04x} {src:04x} {count}",
                      file=sys.stderr, flush=True)
            initial = bytes((i * 29 + 17 + index * 7) & 0xff for i in range(96))
            function = "root:29F4:281A" if method == "fmemcpy" else "root:29F4:26F4"
            oracle = original_copy(function, initial, dst, src, count)
            portable, returned = call_portable_copy(lib, method, initial, dst, src, count)
            expected_return = (segment << 16) | dst
            if oracle["bytes"] != portable or oracle["result"]["return"] != expected_return:
                errors.append({"case": index, "method": method, "dst": dst, "src": src,
                               "count": count,
                               "oracle_return": oracle["result"]["return"],
                               "expected_return": expected_return,
                               "portable_return_pointer": returned,
                               "first_byte_mismatch": next((i for i, (a, b) in
                                                             enumerate(zip(oracle["bytes"], portable))
                                                             if a != b), None)})
                break
            copy_cases += 1

            if method == "fmemcpy" and dst > src and dst - src < count:
                move_case = ("fmemmove", dst, src, count)
                move_oracle = original_copy("root:29F4:26F4", initial, dst, src, count)
                move_portable, _ = call_portable_copy(lib, "fmemmove", initial,
                                                       dst, src, count)
                overlap_difference_seen = move_oracle["bytes"] != oracle["bytes"] and \
                    move_portable != portable

        abs_values = [-32768, -32767, -1024, -2, -1, 0, 1, 2, 1024, 32766, 32767]
        abs_cases = 0
        for value in abs_values:
            if args.verbose:
                print(f"ABS case {value}", file=sys.stderr, flush=True)
            _, oracle = machine_call("ABS", [value & 0xffff], [], [], "s16")
            portable = lib.portable_abs16(value)
            if oracle["return"] != portable:
                errors.append({"function": "ABS", "input": value,
                               "oracle": oracle["return"], "portable": portable})
                break
            abs_cases += 1

        # Exercise the recovered BlockMove wrapper's (source,destination,count)
        # order, which internally invokes runtime _fmemcpy(dst,src,count).
        initial = bytes((i * 13 + 9) & 0xff for i in range(64))
        if args.verbose:
            print("BlockMove case", file=sys.stderr, flush=True)
        src_offset, dst_offset, count = 0x2010, 0x2040, 0x10013
        machine, _ = machine_call(
            "BlockMove", [src_offset, segment, dst_offset, segment,
                          count & 0xffff, (count >> 16) & 0xffff],
            [(segment * 16 + base, initial)],
            [behavior.Range("buffer", segment * 16 + base, len(initial))], "void")
        block_oracle = machine.read(segment * 16 + base, len(initial))
        block_initial = (ctypes.c_uint8 * len(initial)).from_buffer_copy(initial)
        lib.BlockMove(ctypes.addressof(block_initial) + src_offset - base,
                      ctypes.addressof(block_initial) + dst_offset - base, count)
        block_portable = bytes(block_initial)
        if block_oracle != block_portable:
            errors.append({"function": "BlockMove", "first_byte_mismatch": next(
                (i for i, (a, b) in enumerate(zip(block_oracle, block_portable)) if a != b), None)})

        if args.verbose:
            print("BlockMove compared; clearing DOS machine cache", file=sys.stderr, flush=True)
        original_machine.cache_clear()
        gc.collect()
        if args.verbose:
            print("DOS machine cache cleared", file=sys.stderr, flush=True)
        runtime = symbols.load()["runtime"]
        report = {
            "schema": "portable-memory-dos-differential-v1",
            "status": "DIAGNOSTIC_PASS" if not errors else "FAIL",
            "oracle_exe_sha256": exe.load().sha256,
            "source_anchors": {
                "BlockMove": "root:0244:0000; wrapper calls __fmemcpy(destination,source,[bp+0E]); root:m0EC1 caller passes a long but the wrapper reads only its low count word",
                "ABS": "root:00F8:0459; signed 16-bit compare and NEG, so INT16_MIN returns INT16_MIN",
            },
            "runtime_entries": {
                "fmemcpy": {"alias": "__fmemcpy", **runtime["__fmemcpy"]},
                "fmemmove": {"alias": "__fmemmove", **runtime["__fmemmove"]},
                "fmemcpy_disassembly": "root:29F4:281A, 94 bytes; forward REP MOVSW/MOVSB, far return AX:DX=destination",
                "fmemmove_disassembly": "root:29F4:26F4, 202 bytes; overlap-distance branch uses STD/REP MOVSB then CLD, forward path otherwise; far return AX:DX=destination"
            },
            "fmemcpy_fmemmove": {"cases": copy_cases, "mismatches": errors[:8],
                                  "overlap_direction_distinguished": overlap_difference_seen},
            "ABS": {"cases": abs_cases, "inputs_include_int16_min": True,
                    "int16_min_result": lib.portable_abs16(-32768)},
            "BlockMove": {"tested": True, "source_destination_order": "source,destination,count",
                           "adapter_count_width": "int32_t caller value; low uint16_t matches original callee stack read",
                           "test_caller_count": 0x10013, "effective_dos_count": 19},
            "excluded": ["DOS far-pointer segment wrap normalization beyond a native contiguous span",
                         "invalid native pointers with nonzero count"],
            "unicorn_version": unicorn.__version__,
            "portable_source_sha256": sha256((ROOT / "portable/platform/memory.c").read_bytes()),
            "adapter_source_sha256": sha256((ROOT / "portable/game/recovered/memory_adapter.c").read_bytes()),
            "runner_sha256": sha256(Path(__file__).read_bytes()),
        }
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps(report, indent=2))
        if errors:
            raise SystemExit(1)


if __name__ == "__main__":
    main()
