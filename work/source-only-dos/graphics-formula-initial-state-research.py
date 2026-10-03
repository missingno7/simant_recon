#!/usr/bin/env python3
"""Original-only typed checks for the graphics formulas before guest execution.

This is separate from every guarded source-only probe.  It loads the locked
original image into the research VM, reads only the 18 candidate table entries
before any guest instruction, and emits predicate results without raw values.
It neither assigns a source owner nor proves startup write/layout closure.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "tools"))

import behavior
import functions
import match


CONSUMERS = {
    "o00_31AD_013A": {
        "source": "src/S00/m31AD.asm", "lines": [2884, 2886],
        "read_family": "selector", "operand": "symbolic _g_2100",
        "expected": (0x31AD, 0x013A, 578),
    },
    "o01_3126_0C87": {
        "source": "src/S01/m3126.asm", "lines": [1710, 1711],
        "read_family": "selector", "operand": "symbolic _g_2100",
        "expected": (0x3126, 0x0C87, 684),
    },
    "o01_32B5_00AA": {
        "source": "src/S01/m32B5.asm", "lines": [119, 121],
        "read_family": "byte_residue_masks", "operand": "SS:[BX+68AC]",
        "expected": (0x32B5, 0x00AA, 168),
    },
    "o03_3258_04CE": {
        "source": "src/S03/m3258.asm", "lines": [189, 191],
        "read_family": "packed_parity_masks", "operand": "SS:[BX+68B4]",
        "expected": (0x3258, 0x04CE, 217),
    },
}


def sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def pin(path: Path) -> dict:
    return {"path": path.relative_to(ROOT).as_posix(),
            "sha256": sha_file(path), "size": path.stat().st_size}


def data_byte(machine, offset: int) -> int:
    # Intentionally return only an in-memory value to the predicate checker;
    # neither the value nor any byte span is serialized or printed.
    return machine.read(match.DGROUP_SEG * 16 + offset, 1)[0]


def consumer_intervals() -> list[dict]:
    rows = []
    for name, spec in CONSUMERS.items():
        fn = functions.get(name)
        actual = (fn["seg"], fn["off"], fn["size"])
        if actual != spec["expected"]:
            raise RuntimeError(f"consumer interval changed: {name}")
        path = ROOT / spec["source"]
        lines = path.read_text(encoding="latin1").splitlines()
        first, last = spec["lines"]
        if not 1 <= first <= last <= len(lines):
            raise RuntimeError(f"consumer source lines are outside {spec['source']}")
        source_slice = "\n".join(lines[first - 1:last])
        if spec["operand"] == "symbolic _g_2100":
            if "_g_2100" not in source_slice:
                raise RuntimeError(f"symbolic consumer anchor changed: {name}")
        elif spec["operand"] == "SS:[BX+68AC]":
            if "68AC" not in source_slice.upper():
                raise RuntimeError(f"byte-mask consumer anchor changed: {name}")
        elif spec["operand"] == "SS:[BX+68B4]":
            if "68B4" not in source_slice.upper():
                raise RuntimeError(f"packed-mask consumer anchor changed: {name}")
        rows.append({
            "function": name, "unit": fn["unit"],
            "code_interval": {"segment": f"{fn['seg']:04X}",
                              "start_offset": f"{fn['off']:04X}",
                              "end_offset_exclusive": f"{fn['off'] + fn['size']:04X}",
                              "extent": fn["size"]},
            "source_anchor": {"path": spec["source"], "lines": spec["lines"]},
            "operand": spec["operand"],
            "target_family": spec["read_family"],
        })
    return rows


def main() -> int:
    lock_path = ROOT / "layout/oracle.lock.json"
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    oracle_pin = lock["inputs"]["SIMANT.EXE"]
    image_path = ROOT / "assets/SIMANT.EXE"
    if sha_file(image_path) != oracle_pin["sha256"]:
        raise SystemExit("original executable does not match layout/oracle.lock.json")
    if image_path.stat().st_size != oracle_pin["size"]:
        raise SystemExit("original executable size does not match layout/oracle.lock.json")
    if match.DGROUP_SEG != 0x55B3:
        raise SystemExit("unexpected locked DGROUP segment")

    consumer_rows = consumer_intervals()
    machine = behavior.Machine(SimpleNamespace(function=functions.get("main")))

    selectors = [data_byte(machine, 0x2100 + i) for i in range(8)]
    byte_masks = [data_byte(machine, 0x68AC + i) for i in range(8)]
    packed_masks = [data_byte(machine, 0x68B4 + i) for i in range(2)]

    positive = []
    for phase, observed in enumerate(selectors):
        positive.append({"family": "high_bit_selector", "index": phase,
                         "predicate": "one high-bit-first plane selector for phase",
                         "result": "PASS" if observed == (0x80 >> phase) else "FAIL"})
    for residue, observed in enumerate(byte_masks):
        expected = 0xFF if residue == 0 else (0xFF << (8 - residue)) & 0xFF
        positive.append({"family": "one_bit_byte_tail_mask", "index": residue,
                         "predicate": "retain full byte at residue zero; otherwise retain high residue bits",
                         "result": "PASS" if observed == expected else "FAIL"})
    for odd, observed in enumerate(packed_masks):
        expected = 0xF0 if odd else 0xFF
        positive.append({"family": "packed_nibble_tail_mask", "index": odd,
                         "predicate": "retain both nibbles for even width; high nibble for odd width",
                         "result": "PASS" if observed == expected else "FAIL"})

    reversed_plane_rejected = all(
        observed != (1 << phase) for phase, observed in enumerate(selectors))
    low_bit_byte_tail_rejected = all(
        byte_masks[r] != (0xFF if r == 0 else (0xFF >> (8 - r)))
        for r in range(1, 8))
    packed_low_nibble_rejected = packed_masks[1] != 0x0F
    negative = [
        {"contrast": "reversed_plane_order", "result": "PASS" if reversed_plane_rejected else "FAIL"},
        {"contrast": "low_bit_byte_tail_masks", "result": "PASS" if low_bit_byte_tail_rejected else "FAIL"},
        {"contrast": "packed_odd_low_nibble", "result": "PASS" if packed_low_nibble_rejected else "FAIL"},
    ]

    tool_paths = [
        Path(__file__), lock_path, ROOT / "layout/functions.json",
        ROOT / "layout/symbols.json", ROOT / "layout/manifest.json",
        ROOT / "tools/behavior.py", ROOT / "tools/exe.py", ROOT / "tools/functions.py",
        ROOT / "tools/match.py", ROOT / "tools/modctx.py", ROOT / "tools/modules.py",
        *[ROOT / spec["source"] for spec in CONSUMERS.values()],
    ]
    result = {
        "schema": "simant-graphics-formula-initial-state-research-v1",
        "purpose": "typed original-image formula predicates before guest instructions",
        "original_input": {"path": "assets/SIMANT.EXE", "sha256": oracle_pin["sha256"],
                           "size": oracle_pin["size"],
                           "identity_source": "layout/oracle.lock.json"},
        "boundary": "image loaded into research VM; no guest instruction, DOS startup, RTLink, or CRT startup executed",
        "original_values_emitted": False,
        "data_intervals": [
            {"family": "high_bit_selector", "segment": "DGROUP", "offset": "2100", "count": 8,
             "symbolic_consumer_name": "_g_2100"},
            {"family": "one_bit_byte_tail_mask", "segment": "DGROUP", "offset": "68AC", "count": 8,
             "consumer_binding": "absolute SS displacement in S01"},
            {"family": "packed_nibble_tail_mask", "segment": "DGROUP", "offset": "68B4", "count": 2,
             "consumer_binding": "absolute SS displacement in S03"},
        ],
        "consumer_intervals": consumer_rows,
        "positive_formula_checks": positive,
        "negative_formula_contrasts": negative,
        "all_positive_checks_pass": all(row["result"] == "PASS" for row in positive),
        "all_negative_contrasts_reject": all(row["result"] == "PASS" for row in negative),
        "pins": [pin(path) for path in tool_paths],
        "limits": [
            "This observes original loaded-image initial values only; no historical declaration, initializer TU, or physical owner is asserted.",
            "Symbolic normal reads are named for _g_2100; 68AC and 68B4 remain absolute SS-displacement consumers.",
            "This does not prove source-only startup initialization, post-startup mutability, arbitrary alias closure, or copy/write layout bounds.",
        ],
    }
    out = ROOT / "work/source-only-dos/graphics-formula-initial-state-research-v1.json"
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    # Keep stdout limited to pass/fail predicate results.  No original value or
    # byte span is printed here or saved in the research report.
    print(json.dumps({"positive_formula_checks": positive,
                      "negative_formula_contrasts": negative,
                      "all_positive_checks_pass": result["all_positive_checks_pass"],
                      "all_negative_contrasts_reject": result["all_negative_contrasts_reject"]},
                     indent=2))
    return 0 if result["all_positive_checks_pass"] and result["all_negative_contrasts_reject"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
