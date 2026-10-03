#!/usr/bin/env python3
"""Differential-check the original DOS key wrapper's AH=08 normalization."""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / "tools"), str(ROOT / "build" / "behavior" / "deps")]
import behavior  # noqa: E402
import exe  # noqa: E402
import functions  # noqa: E402
import unicorn  # noqa: E402

REPORT = ROOT / "portable/tests/whole_program/evidence/input-time-key-ah-override-v1.json"
SEED = 0x1F580090
SEG = 0x3000
BASE = SEG * 16


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def symbol_address(name: str) -> int:
    symbol = behavior.symbol(name)
    return symbol["seg"] * 16 + symbol["off"]


def make_dos_machine(keys: list[int]):
    target = functions.get("f_1F58_0090")
    pair = SimpleNamespace(function=target, sequence_targets=frozenset(),
        sequence_function=lambda name: functions.get(name), vectors={})
    vm = behavior.Machine(pair)
    vm.test_bios_keys = list(keys)
    return vm


def direct_dos_key(vm, label: str, writes: list[tuple[int, bytes]]):
    return vm.run(behavior.Case(label, args=[], writes=writes,
        observe=[behavior.Range("pending", symbol_address("g_5A2A"), 4)],
        return_kind="s16"), function="f_1F58_0090")


def configure_interrupt_model():
    original = behavior.Machine._on_interrupt

    def service_bios_keyboard(self, cpu, number, userdata):
        if number == 0x16:
            queue = getattr(self, "test_bios_keys", None)
            if not queue:
                self.error = "DOS test BIOS keyboard queue exhausted"
                cpu.emu_stop()
                return
            # INT 16h/AH=00h returns BIOS AX. The original function itself is
            # still executed from the frozen DOS image under Unicorn.
            self.set_reg("ax", queue.pop(0))
            return
        return original(self, cpu, number, userdata)

    behavior.Machine._on_interrupt = service_bios_keyboard
    return original


def bind_native(path: Path):
    lib = ctypes.CDLL(str(path.resolve()))
    u16p = ctypes.POINTER(ctypes.c_uint16)
    lib.input_time_key_read_bios.argtypes = [u16p, ctypes.c_size_t]
    lib.input_time_key_read_bios.restype = ctypes.c_int16
    lib.input_time_key_read_seeded.argtypes = [ctypes.c_uint16, ctypes.c_uint16]
    lib.input_time_key_read_seeded.restype = ctypes.c_int16
    lib.input_time_key_provider_calls.argtypes = []
    lib.input_time_key_provider_calls.restype = ctypes.c_uint
    lib.input_time_key_pending.argtypes = [ctypes.c_uint]
    lib.input_time_key_pending.restype = ctypes.c_uint16
    lib.input_time_key_unbind.argtypes = []
    return lib


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, default=REPORT)
    parser.add_argument("--native-output", type=Path,
                        default=Path("build/workers/input_time_key_dos_v2.dll"))
    args = parser.parse_args()
    report_path = args.report if args.report.is_absolute() else ROOT / args.report
    dll = args.native_output if args.native_output.is_absolute() else ROOT / args.native_output
    native_probe = ROOT / "build/workers/input_time_key_dos_v2_native_probe.exe"
    if report_path.exists() or dll.exists() or native_probe.exists():
        raise SystemExit("refusing to overwrite immutable input-key differential artifacts")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    dll.parent.mkdir(parents=True, exist_ok=True)
    compiler = shutil.which("gcc")
    if compiler is None:
        raise SystemExit("GCC is required for input-time key controls")
    compiler_path = Path(compiler).resolve()
    compiler_before = sha(compiler_path)
    compiler_version = subprocess.check_output([compiler, "--version"], text=True).splitlines()[0]

    input_paths = [
        "portable/tests/whole_program/run_input_time_key_dos_v2.py",
        "portable/tests/whole_program/input_time_key_dos_shim.c",
        "portable/tests/whole_program/input_time_probe.c",
        "portable/whole_program/platform/input_time.c",
        "portable/whole_program/platform/input_time.h",
        "src/root/m1F58.asm",
        "tools/behavior.py", "tools/exe.py", "tools/functions.py", "tools/match.py",
        "layout/functions.json", "layout/symbols.json", "layout/manifest.json",
        "layout/oracle.lock.json",
    ]
    before = {path: sha(ROOT / path) for path in input_paths}

    compile_cmd = [compiler, "-std=c11", "-Wall", "-Wextra", "-Wconversion", "-Werror",
                   "-pedantic", "-shared",
                   "portable/whole_program/platform/input_time.c",
                   "portable/tests/whole_program/input_time_key_dos_shim.c",
                   "-o", str(dll)]
    subprocess.run(compile_cmd, cwd=ROOT, check=True, capture_output=True, text=True)
    native_probe_cmd = [compiler, "-std=c11", "-Wall", "-Wextra", "-Wconversion", "-Werror",
                        "-pedantic", "-I", str(ROOT),
                        "portable/whole_program/platform/input_time.c",
                        "portable/tests/whole_program/input_time_probe.c",
                        "-o", str(native_probe)]
    subprocess.run(native_probe_cmd, cwd=ROOT, check=True,
                   capture_output=True, text=True)
    probe = subprocess.run([str(native_probe)], cwd=ROOT, capture_output=True,
                           text=True)
    if probe.returncode:
        raise SystemExit(f"native input-time controls failed: {probe.stdout}{probe.stderr}")
    lib = bind_native(dll)

    p1 = symbol_address("g_5A2A")
    p2 = symbol_address("g_5A2C")
    cases = [
        {"name": "ascii-A", "bios": [0x1e41], "initial": (0, 0), "expected": 0x0041},
        {"name": "extended-F2", "bios": [0x3c00], "initial": (0, 0), "expected": 0x083c},
        {"name": "extended-up", "bios": [0x4800], "initial": (0, 0), "expected": 0x0848},
        {"name": "second-zero", "bios": [], "initial": (0x1200, 0x3400), "expected": 0x0800},
        {"name": "second-high-byte-overridden", "bios": [],
         "initial": (0x1200, 0xab41), "expected": 0x0841},
    ]
    rows, mismatches = [], []
    original_interrupt_handler = configure_interrupt_model()
    try:
        for case in cases:
            first, second = case["initial"]
            writes = [(p1, first.to_bytes(2, "little")),
                      (p2, second.to_bytes(2, "little"))]
            vm = make_dos_machine(case["bios"])
            dos = direct_dos_key(vm, case["name"], writes)
            dos_value = dos["return"] & 0xffff
            dos_pending = bytes.fromhex(dos["ranges"]["pending"])

            if case["bios"]:
                queue = (ctypes.c_uint16 * len(case["bios"]))(*case["bios"])
                native_value = lib.input_time_key_read_bios(queue, len(case["bios"])) & 0xffff
                provider_calls = lib.input_time_key_provider_calls()
            else:
                native_value = lib.input_time_key_read_seeded(first, second) & 0xffff
                provider_calls = 0
            native_pending = (lib.input_time_key_pending(0),
                              lib.input_time_key_pending(1))
            dos_words = (int.from_bytes(dos_pending[:2], "little"),
                         int.from_bytes(dos_pending[2:], "little"))
            equal = (dos_value == native_value == case["expected"] and
                     dos_words == native_pending and
                     provider_calls == len(case["bios"]))
            row = {"case": case["name"], "equal": equal,
                   "expected_ax": case["expected"], "dos_ax": dos_value,
                   "native_ax": native_value, "dos_pending": dos_words,
                   "native_pending": native_pending,
                   "bios_words": case["bios"], "provider_calls": provider_calls}
            rows.append(row)
            if not equal:
                mismatches.append(row)
            lib.input_time_key_unbind()
    finally:
        behavior.Machine._on_interrupt = original_interrupt_handler

    after = {path: sha(ROOT / path) for path in input_paths}
    compiler_after = sha(compiler_path)
    if before != after or compiler_before != compiler_after:
        raise SystemExit("source or compiler identity changed during key differential")
    report = {
        "schema": "whole-program-input-time-key-ah-override-v1",
        "status": "PASS" if not mismatches else "MISMATCH",
        "oracle": {"sha256": exe.load().sha256, "unicorn": unicorn.__version__},
        "native_dll_sha256": sha(dll),
        "native_probe_sha256": sha(native_probe),
        "compile_commands": [compile_cmd, native_probe_cmd],
        "compiler": {"path": str(compiler_path), "sha256_before": compiler_before,
                     "sha256_after": compiler_after, "version": compiler_version},
        "seed": SEED,
        "case_count": len(rows),
        "equal_count": sum(row["equal"] for row in rows),
        "mismatch_count": len(mismatches),
        "rows": rows,
        "mismatches": mismatches,
        "input_sha256_before": before,
        "input_sha256_after": after,
        "scope": {
            "oracle_execution": "Original f_1F58_0090 and f_1F58_005A machine code executes in Unicorn. INT 16h/AH=00h is a deterministic BIOS key provider; seeded g_5A2A/g_5A2C cases exercise the original pending-key path without interrupt substitution.",
            "compared": ["AX return", "g_5A2A/g_5A2C pending state", "BIOS read-call count"],
            "domain": "ASCII A; BIOS extended F2 and Up; second read zero; second-read low byte with nonzero high byte overwritten by original MOV AH,8.",
            "claim_limit": "Direct key-wrapper behavior only; no SDL key translation or broader BIOS keyboard behavior is claimed.",
        },
        "native_existing_probe": probe.stdout.strip(),
    }
    with report_path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(report, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(json.dumps({"status": report["status"], "cases": len(rows),
                      "equal": report["equal_count"], "mismatches": len(mismatches),
                      "report": str(report_path)}, indent=2))
    return 0 if not mismatches else 1


if __name__ == "__main__":
    raise SystemExit(main())
