#!/usr/bin/env python3
"""Capture source-facing MSC CRT values from the actual initialized DOS image.

The output records decoded strings and the observed ASCII lowercase set, never
copies the original table's raw bytes into a C source file.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[4]
sys.path[:0] = [str(ROOT / "tools"), str(ROOT / "tools/behavior_suites")]
import behavior  # noqa: E402
import exe  # noqa: E402
import functions  # noqa: E402


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def capture() -> dict:
    machine = behavior.Machine(SimpleNamespace(function=functions.get("f_1C62_06A6")))
    memory = machine.cpu.mem_read
    dgroup = 0x55B3 * 16
    table_address = dgroup + 0x7D12
    rows = []
    for index in range(38):
        pointer = bytes(memory(table_address + index * 4, 4))
        offset = int.from_bytes(pointer[:2], "little")
        segment = int.from_bytes(pointer[2:], "little")
        raw = bytes(memory(segment * 16 + offset, 256))
        value = raw.split(b"\0", 1)[0].decode("latin1")
        rows.append({"errno": index, "far_pointer": [segment, offset], "text": value})
    sys_nerr = int.from_bytes(bytes(memory(dgroup + 0x7DAA, 2)), "little", signed=True)
    ctype = bytes(memory(dgroup + 0x7A1E, 257))
    ascii_lower = [chr(value) for value in range(128) if ctype[value + 1] & 0x02]
    pins = [
        "portable/tests/whole_program/platform/capture_crt_abi_observation.py",
        "tools/behavior.py", "tools/exe.py", "tools/functions.py", "tools/match.py",
        "tools/modctx.py", "tools/modules.py", "tools/omf.py", "tools/symbols.py",
        "src/root/m208F.c", "src/S20/m39F1.c",
        "evidence/runtime-data-registered-publics.json", "evidence/toolchain/runtime-location.json",
        "layout/symbols.json", "layout/oracle.lock.json",
    ]
    return {
        "schema": "simant-native-crt-observation-v1",
        "oracle_executable_sha256": exe.EXPECTED_SHA256,
        "observation_method": "behavior.Machine loads the immutable original DOS image and initialized resident DGROUP; values are read directly from original DGROUP addresses, without invoking host libc or a DOS function substitute",
        "unicorn_version": behavior.uc.__version__,
        "sys_errlist": {"dgroup_offset": "0x7D12", "entry_count": 38, "entries": rows},
        "sys_nerr": {"dgroup_offset": "0x7DAA", "value": sys_nerr},
        "ctype": {
            "dgroup_offset": "0x7A1E", "observed_span_bytes": 257,
            "raw_span_sha256_not_embedded": hashlib.sha256(ctype).hexdigest(),
            "lower_bit_mask": "0x02", "ascii_lowercase_bytes": ascii_lower,
            "scope": "source uses only _LOWER bit 0x02 in two text routines; native adapter admits ASCII and fails closed outside that proven input domain",
        },
        "harderr": {
            "registration_call": "IBMInitStuff registers f_208F_058B with _harderr",
            "handler_source": "src/root/m208F.c",
            "handler": "int far f_208F_058B(void) { return 3; }",
            "symbol_grounding": "layout/symbols.json identifies return value 3 as _HARDERR_FAIL",
            "native_contract": "store the registered source policy; no native INT 24 delivery is claimed, and host filesystem operations return mapped errors directly",
        },
        "input_pins": {p: sha(ROOT / p) for p in pins},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    out = args.out if args.out.is_absolute() else ROOT / args.out
    if out.exists():
        raise SystemExit(f"refusing to overwrite {out}")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(capture(), indent=2) + "\n", encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
