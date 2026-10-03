"""Compare pure byte-copy and pending-key paths to the frozen DOS image."""
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

SEED = 0x1F580017
SEG = 0x3000
BASE = SEG * 16


def sha(data):
    return hashlib.sha256(data).hexdigest()


def symbol_address(name):
    item = behavior.symbol(name)
    return item["seg"] * 16 + item["off"]


def machine(name):
    target = functions.get(name)
    pair = SimpleNamespace(function=target, sequence_targets=frozenset(),
                           sequence_function=lambda n: functions.get(n), vectors={})
    return behavior.Machine(pair)


def bind(path):
    lib = ctypes.CDLL(str(path.resolve()))
    lib.input_time_test_init.argtypes = []
    lib.input_time_test_unbind.argtypes = []
    lib.input_time_test_pending.argtypes = [ctypes.c_uint]
    lib.input_time_test_pending.restype = ctypes.c_uint16
    byte_ptr = ctypes.POINTER(ctypes.c_uint8)
    lib.input_time_test_exchange.argtypes = [byte_ptr, byte_ptr, ctypes.c_uint16]
    lib.input_time_test_exchange.restype = None
    lib.input_time_test_pushback.argtypes = [ctypes.c_uint16]
    lib.input_time_test_pushback.restype = ctypes.c_int16
    lib.input_time_test_available.argtypes = []
    lib.input_time_test_available.restype = ctypes.c_int16
    lib.input_time_test_read_char.argtypes = []
    lib.input_time_test_read_char.restype = ctypes.c_int16
    return lib


def direct_call(vm, label, name, args, writes, observed, preserve=False):
    return vm.run(behavior.Case(label, args=args, writes=writes, observe=observed,
                                return_kind="void" if name in ("f_1F58_0017",) else "s16"),
                  preserve=preserve, function=name)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--native-output", type=Path,
                        default=Path("build/workers/input_time_dos_native_v1.dll"))
    args = parser.parse_args()
    report_path = args.report if args.report.is_absolute() else ROOT / args.report
    dll = args.native_output if args.native_output.is_absolute() else ROOT / args.native_output
    if report_path.exists() or dll.exists():
        raise SystemExit("refusing to overwrite immutable input-time differential artifacts")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    dll.parent.mkdir(parents=True, exist_ok=True)
    compile_cmd = ["gcc", "-std=c11", "-Wall", "-Wextra", "-Wconversion", "-Werror",
                   "-pedantic", "-shared", "portable/whole_program/platform/input_time.c",
                   "portable/tests/whole_program/input_time_dos_shim.c", "-o", str(dll)]
    subprocess.run(compile_cmd, cwd=ROOT, check=True, capture_output=True, text=True)
    lib = bind(dll)
    rng = random.Random(SEED)
    rows, mismatches = [], []

    # Original f_1F58_0017 swaps every byte pair in order, not memcpy/memmove.
    vm = machine("f_1F58_0017")
    for case_no, count in enumerate([0, 1, 2, 3, 16, 31] +
                                    [rng.randrange(0, 65) for _ in range(48)]):
        left = bytes(rng.randrange(256) for _ in range(count + 6))
        right = bytes(rng.randrange(256) for _ in range(count + 6))
        dst_off, src_off = 0x1000, 0x1200
        write = [(BASE + dst_off, left), (BASE + src_off, right)]
        ranges = [behavior.Range("dst", BASE + dst_off, len(left)),
                  behavior.Range("src", BASE + src_off, len(right))]
        dos = direct_call(vm, f"exchange-{case_no}", "f_1F58_0017",
                          [dst_off, SEG, src_off, SEG, count], write, ranges)
        dos_effect = (bytes.fromhex(dos["ranges"]["dst"]),
                      bytes.fromhex(dos["ranges"]["src"]))
        native_left = (ctypes.c_uint8 * len(left)).from_buffer_copy(left)
        native_right = (ctypes.c_uint8 * len(right)).from_buffer_copy(right)
        lib.input_time_test_exchange(native_left, native_right, count)
        native_effect = (bytes(native_left), bytes(native_right))
        equal = dos_effect == native_effect
        rows.append({"case": f"f_1F58_0017/{case_no}", "equal": equal,
                     "count": count,
                     "oracle_sha256": sha(dos_effect[0] + dos_effect[1]),
                     "native_sha256": sha(native_effect[0] + native_effect[1]),
                     "compared_bytes": len(left) + len(right)})
        if not equal:
            mismatches.append({"case": rows[-1]["case"], "count": count,
                               "oracle": [x.hex() for x in dos_effect],
                               "native": [x.hex() for x in native_effect]})

    # Follow original pending slots through pushback, availability and read.
    p1, p2, p53 = map(symbol_address, ("g_5A2A", "g_5A2C", "g_53BD"))
    writes = [(p1, b"\0\0"), (p2, b"\0\0"), (p53, b"\0")]
    observed = [behavior.Range("pending", p1, 4)]
    dos_vm = machine("f_1F58_007F")
    lib.input_time_test_init()
    dos = direct_call(dos_vm, "push-A", "f_1F58_007F", [ord("A")], writes,
                      observed)
    lib.input_time_test_pushback(ord("A"))
    state = (lib.input_time_test_pending(0), lib.input_time_test_pending(1))
    dos_words = tuple(int.from_bytes(bytes.fromhex(dos["ranges"]["pending"])[i:i + 2],
                                     "little") for i in (0, 2))
    equal = state == dos_words
    rows.append({"case": "pushback/A", "equal": equal, "oracle": dos_words,
                 "native": state})
    if not equal:
        mismatches.append({"case": "pushback/A", "oracle": dos_words, "native": state})

    dos = direct_call(dos_vm, "push-B", "f_1F58_007F", [ord("B")], [], observed, True)
    lib.input_time_test_pushback(ord("B"))
    state = (lib.input_time_test_pending(0), lib.input_time_test_pending(1))
    dos_words = tuple(int.from_bytes(bytes.fromhex(dos["ranges"]["pending"])[i:i + 2],
                                     "little") for i in (0, 2))
    equal = state == dos_words
    rows.append({"case": "pushback/B-over-A", "equal": equal, "oracle": dos_words,
                 "native": state})
    if not equal:
        mismatches.append({"case": "pushback/B-over-A", "oracle": dos_words, "native": state})

    dos = direct_call(dos_vm, "available-B", "f_1F58_0038", [], [], observed, True)
    dos_available = dos["return"] & 0xffff
    native_available = lib.input_time_test_available() & 0xffff
    equal = dos_available == native_available
    rows.append({"case": "availability/B", "equal": equal,
                 "oracle": dos_available, "native": native_available})
    if not equal:
        mismatches.append({"case": "availability/B", "oracle": dos_available,
                           "native": native_available})

    dos = direct_call(dos_vm, "read-B", "f_1F58_005A", [], [], observed, True)
    dos_char = dos["return"] & 0xffff
    native_char = lib.input_time_test_read_char() & 0xffff
    state = (lib.input_time_test_pending(0), lib.input_time_test_pending(1))
    dos_words = tuple(int.from_bytes(bytes.fromhex(dos["ranges"]["pending"])[i:i + 2],
                                     "little") for i in (0, 2))
    equal = (dos_char, dos_words) == (native_char, state)
    rows.append({"case": "read-B-retain-A", "equal": equal,
                 "oracle": {"char": dos_char, "pending": dos_words},
                 "native": {"char": native_char, "pending": state}})
    if not equal:
        mismatches.append({"case": "read-B-retain-A", "oracle": [dos_char, dos_words],
                           "native": [native_char, state]})
    lib.input_time_test_unbind()

    input_paths = ["portable/tests/whole_program/run_input_time_dos.py",
                   "portable/tests/whole_program/input_time_dos_shim.c",
                   "portable/tests/whole_program/input_time_probe.c",
                   "portable/whole_program/platform/input_time.c",
                   "portable/whole_program/platform/input_time.h",
                   "src/root/m1F58.asm", "src/root/m1B73.asm", "src/root/m00F8.c",
                   "src/root/m1C62.c", "src/root/m208F.c", "src/root/m1FD2.c",
                   "src/S09/m35F5.c", "tools/behavior.py", "tools/exe.py",
                   "tools/functions.py", "tools/match.py", "layout/functions.json",
                   "layout/symbols.json", "layout/manifest.json", "layout/oracle.lock.json"]
    report = {
        "schema": "whole-program-input-time-dos-differential-v1",
        "status": "PASS" if not mismatches else "MISMATCH",
        "oracle": {"sha256": exe.load().sha256, "unicorn": unicorn.__version__},
        "native_dll_sha256": sha(dll.read_bytes()),
        "compile_command": compile_cmd,
        "seed": SEED,
        "case_count": len(rows),
        "equal_count": sum(1 for row in rows if row["equal"]),
        "mismatch_count": len(mismatches),
        "rows": rows,
        "mismatches": mismatches,
        "input_sha256": {p: sha((ROOT / p).read_bytes()) for p in input_paths},
        "scope": [
            "Direct DOS comparisons cover f_1F58_0017 ordered byte exchange and f_1F58_007F/0038/005A pending-key paths with BIOS NumLock policy disabled for the latter.",
            "Tick cadence, actual SDL event translation, NumLock host service, and real IVT/atexit installation remain callback-boundary controls; they are not DOS-differential claims here.",
            "Native public entrypoints still require the application to configure actual logical tick and host input/vector services."
        ]
    }
    with report_path.open("x", encoding="utf-8", newline="\n") as f:
        json.dump(report, f, indent=2, sort_keys=True)
        f.write("\n")
    print(json.dumps({"status": report["status"], "cases": len(rows),
                      "equal": report["equal_count"], "mismatches": len(mismatches),
                      "report": str(report_path)}, indent=2))
    return 0 if not mismatches else 1


if __name__ == "__main__":
    raise SystemExit(main())
