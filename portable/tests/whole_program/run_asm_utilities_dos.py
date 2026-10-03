"""Paired DOS-oracle/native controls for the root assembly utility adapters."""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import random
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / "tools"), str(ROOT / "build" / "behavior" / "deps")]
import behavior  # noqa: E402
import exe  # noqa: E402
import functions  # noqa: E402
import unicorn  # noqa: E402

SEED = 0x24FA1959
DOS_SEG = 0x3000
DOS_BASE = DOS_SEG * 16
CANARY = 0xA7


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def original_machine(name: str):
    target = functions.get(name)
    pair = SimpleNamespace(function=target, sequence_targets=frozenset(),
                           sequence_function=lambda n: functions.get(n),
                           vectors={})
    return behavior.Machine(pair)


def bind_native(path: Path):
    lib = ctypes.CDLL(str(path.resolve()))
    lib.f_1959_0002.argtypes = [ctypes.c_uint16]
    lib.f_1959_0002.restype = ctypes.c_uint16
    lib.f_1959_000C.argtypes = [ctypes.c_uint32]
    lib.f_1959_000C.restype = ctypes.c_uint32
    byte_ptr = ctypes.POINTER(ctypes.c_uint8)
    lib.f_24FA_0004.argtypes = [byte_ptr, ctypes.c_uint8, ctypes.c_uint16]
    lib.f_24FA_0004.restype = byte_ptr
    lib.f_24FA_0029.argtypes = [byte_ptr, byte_ptr, ctypes.c_int16, ctypes.c_int16]
    lib.f_24FA_0029.restype = None
    lib.f_24FA_00A0.argtypes = [byte_ptr, ctypes.c_int16]
    lib.f_24FA_00A0.restype = None
    lib.f_2650_0107.argtypes = [byte_ptr, ctypes.c_int16]
    lib.f_2650_0107.restype = None
    return lib


def compile_native(out: Path):
    command = ["gcc", "-std=c11", "-Wall", "-Wextra", "-Wconversion", "-Werror",
               "-pedantic", "-shared",
               "portable/whole_program/algorithms/asm_utilities.c", "-o", str(out)]
    subprocess.run(command, cwd=ROOT, check=True, capture_output=True, text=True)
    return command


def range_bytes(address: int, size: int, data: bytes, name: str):
    return behavior.Range(name, address, size), data


def case_run(machine, name, args, writes, observe, return_kind="void", max_instructions=1_000_000):
    return machine.run(behavior.Case(name, args=args, writes=writes, observe=observe,
                                    return_kind=return_kind,
                                    max_instructions=max_instructions))


def record(rows, name, oracle, native, actual_bytes=None):
    def encode_obj(value):
        return value.hex() if isinstance(value, bytes) else repr(value)
    equal = oracle == native
    row = {"case": name, "equal": equal,
           "oracle_sha256": sha(oracle if isinstance(oracle, bytes) else
                                json.dumps(oracle, sort_keys=True, default=encode_obj).encode()),
           "native_sha256": sha(native if isinstance(native, bytes) else
                                json.dumps(native, sort_keys=True, default=encode_obj).encode())}
    if actual_bytes is not None:
        row["compared_bytes"] = actual_bytes
    rows.append(row)
    return equal


def run_word_dword(lib, rows, mismatches, rng):
    machine16 = original_machine("f_1959_0002")
    values16 = [0, 1, 0xff, 0x100, 0x1234, 0x8000, 0xffff]
    values16 += [rng.randrange(0x10000) for _ in range(96)]
    for i, v in enumerate(values16):
        dos = case_run(machine16, f"swap16-{i}", [v], [], [], "s16")["return"] & 0xffff
        native = int(lib.f_1959_0002(v))
        if not record(rows, f"f_1959_0002/{i}", dos, native):
            mismatches.append({"case": f"f_1959_0002/{i}", "input": v,
                               "oracle": dos, "native": native})

    machine32 = original_machine("f_1959_000C")
    values32 = [0, 1, 0xff, 0x100, 0x12345678, 0x80000000, 0xffffffff]
    values32 += [rng.getrandbits(32) for _ in range(96)]
    for i, v in enumerate(values32):
        dos = case_run(machine32, f"swap32-{i}", [v & 0xffff, v >> 16], [], [], "u32")["return"]
        native = int(lib.f_1959_000C(v))
        if not record(rows, f"f_1959_000C/{i}", dos, native):
            mismatches.append({"case": f"f_1959_000C/{i}", "input": v,
                               "oracle": dos, "native": native})


def run_reverse_search(lib, rows, mismatches, rng):
    machine = original_machine("f_24FA_0004")
    cases = [(n, 0x55, p) for n in (1, 2, 3, 7, 16, 255) for p in (0, n // 2, n - 1)]
    cases += [(rng.randrange(1, 129), rng.randrange(256), -1) for _ in range(96)]
    for i, (count, needle, placement) in enumerate(cases):
        payload = bytearray(rng.randrange(256) for _ in range(count))
        if placement >= 0:
            payload[placement] = needle
        elif i % 3 == 0:
            payload[rng.randrange(count)] = needle
        # Far pointer starts at the final item; scanning descends within this span.
        start = count - 1
        offset = 0x1000 + start
        storage = bytes([CANARY] * 2) + bytes(payload) + bytes([CANARY] * 2)
        storage_off = offset - start - 2
        seg = DOS_SEG
        observe = [behavior.Range("search_storage", DOS_BASE + storage_off, len(storage))]
        dos = case_run(machine, f"reverse-find-{i}", [offset, seg, needle, count],
                       [(DOS_BASE + storage_off, storage)], observe, "farptr")
        dos_raw = dos["return"]
        dos_delta = None if dos_raw == 0 else ((dos_raw >> 16) == seg and
                                                (dos_raw & 0xffff) - offset)

        native_buf = (ctypes.c_uint8 * len(storage)).from_buffer_copy(storage)
        native_start = ctypes.addressof(native_buf) + 2 + start
        native_ptr = lib.f_24FA_0004(ctypes.cast(native_start, ctypes.POINTER(ctypes.c_uint8)),
                                     needle, count)
        native_addr = ctypes.cast(native_ptr, ctypes.c_void_p).value
        native_delta = None if not native_addr else native_addr - native_start
        oracle_view = {"delta": dos_delta,
                       "storage": bytes.fromhex(dos["ranges"]["search_storage"])}
        native_view = {"delta": native_delta,
                       "storage": bytes(native_buf)}
        if not record(rows, f"f_24FA_0004/{i}", oracle_view, native_view, len(storage)):
            mismatches.append({"case": f"f_24FA_0004/{i}", "count": count,
                               "needle": needle,
                               "oracle_delta": dos_delta,
                               "native_delta": native_delta,
                               "oracle_storage": oracle_view["storage"].hex(),
                               "native_storage": native_view["storage"].hex()})


def run_expand(lib, rows, mismatches, rng):
    machine = original_machine("f_24FA_0029")
    dimensions = [(w, h) for w in range(1, 18) for h in (1, 2, 3)]
    dimensions += [(rng.randrange(1, 128), rng.randrange(1, 8)) for _ in range(80)]
    for i, (width, height) in enumerate(dimensions):
        out_row = (width + 1) // 2
        src_row = (out_row + 3) // 4
        output_size, source_size = out_row * height, src_row * height
        source = bytes(rng.randrange(256) for _ in range(source_size))
        target = bytes([CANARY] * 3 + [0x5c] * output_size + [CANARY] * 3)
        src_off, dst_off = 0x3000, 0x1800
        dos = case_run(machine, f"expand-{i}",
                       [dst_off + 3, DOS_SEG, src_off, DOS_SEG, width, height],
                       [(DOS_BASE + dst_off, target), (DOS_BASE + src_off, source)],
                       [behavior.Range("dst_guarded", DOS_BASE + dst_off, len(target))])
        dos_bytes = bytes.fromhex(dos["ranges"]["dst_guarded"])
        native_dst = (ctypes.c_uint8 * len(target)).from_buffer_copy(target)
        native_src = (ctypes.c_uint8 * len(source)).from_buffer_copy(source)
        lib.f_24FA_0029(ctypes.cast(ctypes.addressof(native_dst) + 3,
                                    ctypes.POINTER(ctypes.c_uint8)), native_src,
                        width, height)
        native_bytes = bytes(native_dst)
        if not record(rows, f"f_24FA_0029/{i}", dos_bytes, native_bytes, len(target)):
            mismatches.append({"case": f"f_24FA_0029/{i}", "width": width,
                               "height": height, "oracle": dos_bytes.hex(),
                               "native": native_bytes.hex()})


def run_invert_and_clear(lib, rows, mismatches, rng):
    machine = original_machine("f_24FA_00A0")
    counts = [1, 2, 3, 255, 256, 257, 1024]
    counts += [rng.randrange(1, 4097) for _ in range(32)]
    for i, count in enumerate(counts):
        initial = bytes(rng.randrange(256) for _ in range(count + 8))
        pointer_off = 0x2000
        observe = [behavior.Range("invert", DOS_BASE + pointer_off, len(initial))]
        dos = case_run(machine, f"invert-{i}", [pointer_off, DOS_SEG, count],
                       [(DOS_BASE + pointer_off, initial)], observe, "void")
        dos_bytes = bytes.fromhex(dos["ranges"]["invert"])
        native_buf = (ctypes.c_uint8 * len(initial)).from_buffer_copy(initial)
        lib.f_24FA_00A0(native_buf, count)
        native_bytes = bytes(native_buf)
        if not record(rows, f"f_24FA_00A0/{i}", dos_bytes, native_bytes, len(initial)):
            mismatches.append({"case": f"f_24FA_00A0/{i}", "count": count,
                               "oracle": dos_bytes.hex(), "native": native_bytes.hex()})

    # A zero CX really executes 65,536 LOOP iterations. Use exactly one full
    # segment-sized backing span so the target's 16-bit DI wrap is represented.
    initial = bytes((i * 29 + 7) & 255 for i in range(65536))
    observe = [behavior.Range("full_segment", DOS_BASE, 65536)]
    dos = case_run(machine, "invert-zero-count-65536", [0, DOS_SEG, 0],
                   [(DOS_BASE, initial)], observe, "void", 400000)
    dos_bytes = bytes.fromhex(dos["ranges"]["full_segment"])
    native_buf = (ctypes.c_uint8 * 65536).from_buffer_copy(initial)
    lib.f_24FA_00A0(native_buf, 0)
    native_bytes = bytes(native_buf)
    if not record(rows, "f_24FA_00A0/zero-count-65536", dos_bytes, native_bytes, 65536):
        mismatches.append({"case": "f_24FA_00A0/zero-count-65536",
                           "oracle_sha256": sha(dos_bytes), "native_sha256": sha(native_bytes)})

    machine_clear = original_machine("f_2650_0107")
    for i, count in enumerate((1, 2, 3, 4, 31, 256)):
        initial = bytes(rng.randrange(256) for _ in range(count + 8))
        off = 0x2200
        dos = case_run(machine_clear, f"clear-{i}", [off, DOS_SEG, count],
                       [(DOS_BASE + off, initial)],
                       [behavior.Range("clear", DOS_BASE + off, len(initial))])
        dos_bytes = bytes.fromhex(dos["ranges"]["clear"])
        native_buf = (ctypes.c_uint8 * len(initial)).from_buffer_copy(initial)
        lib.f_2650_0107(native_buf, count)
        native_bytes = bytes(native_buf)
        if not record(rows, f"f_2650_0107/{i}", dos_bytes, native_bytes, len(initial)):
            mismatches.append({"case": f"f_2650_0107/{i}", "count": count,
                               "oracle": dos_bytes.hex(), "native": native_bytes.hex()})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--native-output", type=Path,
                        default=Path("build/workers/asm_utilities_dos_native_v1.dll"))
    args = parser.parse_args()
    report_path = args.report if args.report.is_absolute() else ROOT / args.report
    report_path.parent.mkdir(parents=True, exist_ok=True)
    if report_path.exists():
        raise SystemExit(f"refusing to overwrite immutable report: {report_path}")

    rng = random.Random(SEED)
    rows, mismatches = [], []
    dll = args.native_output if args.native_output.is_absolute() else ROOT / args.native_output
    dll.parent.mkdir(parents=True, exist_ok=True)
    if dll.exists():
        raise SystemExit(f"refusing to overwrite native DLL: {dll}")
    compile_command = compile_native(dll)
    lib = bind_native(dll)
    run_word_dword(lib, rows, mismatches, rng)
    run_reverse_search(lib, rows, mismatches, rng)
    run_expand(lib, rows, mismatches, rng)
    run_invert_and_clear(lib, rows, mismatches, rng)
    native_dll_sha = sha(dll.read_bytes())

    files = ["portable/tests/whole_program/run_asm_utilities_dos.py",
             "portable/whole_program/algorithms/asm_utilities.c",
             "portable/whole_program/algorithms/asm_utilities.h",
             "portable/tests/whole_program/asm_utilities_probe.c",
             "tools/behavior.py", "tools/exe.py", "tools/functions.py", "tools/match.py",
             "tools/modctx.py", "tools/modules.py", "tools/omf.py", "layout/functions.json",
             "layout/symbols.json", "layout/manifest.json", "layout/oracle.lock.json",
             "src/root/m1959.asm", "src/root/m24FA.asm", "src/root/m2650.asm",
             "src/root/m0000.c", "src/root/m23E6.c", "src/root/m24AB.c",
             "src/root/m25E7.c"]
    inputs = {p: sha((ROOT / p).read_bytes()) for p in files}
    report = {
        "schema": "whole-program-asm-utilities-dos-differential-v1",
        "status": "PASS" if not mismatches else "MISMATCH",
        "oracle": {"sha256": exe.load().sha256, "unicorn": unicorn.__version__},
        "native": {"dll_sha256": native_dll_sha, "compiler": subprocess.run(
            ["gcc", "--version"], check=True, capture_output=True, text=True).stdout.splitlines()[0],
            "command": compile_command},
        "seed": SEED,
        "case_count": len(rows),
        "equal_count": sum(1 for r in rows if r["equal"]),
        "mismatch_count": len(mismatches),
        "target_counts": {name: sum(1 for r in rows if r["case"].startswith(name + "/"))
                          for name in ("f_1959_0002", "f_1959_000C", "f_24FA_0004",
                                       "f_24FA_0029", "f_24FA_00A0", "f_2650_0107")},
        "rows": rows,
        "mismatches": mismatches,
        "invalid_controls": {
            "status": "SOURCE_DOMAIN_REVIEWED_NOT_EXECUTED",
            "cases": [
                "f_24FA_0004 count=0 and null start abort at native public adapter; DOS ZF is input-dependent",
                "f_24FA_0029 null pointers or nonpositive dimensions abort at native public adapter",
                "f_2650_0107 count<=0 aborts because zero's original write-before-pointer is excluded"
            ]
        },
        "input_sha256": inputs,
        "clarification": "m1959 f_1959_000C assembly loads argument high word at [bp+8] into AX and low word at [bp+6] into DX, byte-swaps both, and returns DX:AX. The resulting scalar is the conventional 32-bit byte swap. This corrects the imprecise wording in the preserved native-v1 source_contracts text; no implementation change was made.",
        "limits": [
            "Direct original-DOS execution is compared to the native public adapters using the same argument words and initialized bytes.",
            "Reverse search uses valid contiguous spans without DOS segment wrap; returned far pointers are normalized to offset delta.",
            "Expansion compares destination bytes and canaries only; it asserts no visible pixel geometry.",
            "Zero-count inversion uses an exact 64 KiB segment-sized span and directly exercises the 65,536-iteration LOOP behavior.",
            "Invalid public-domain calls are documented but not executed in this paired DOS run."
        ]
    }
    raw = json.dumps(report, indent=2, sort_keys=True) + "\n"
    with report_path.open("x", encoding="utf-8", newline="\n") as f:
        f.write(raw)
    print(json.dumps({"status": report["status"], "report": str(report_path),
                      "case_count": len(rows), "equal_count": report["equal_count"],
                      "mismatch_count": len(mismatches), "target_counts": report["target_counts"]},
                     indent=2))
    return 0 if not mismatches else 1


if __name__ == "__main__":
    raise SystemExit(main())
