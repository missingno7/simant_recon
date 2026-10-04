"""Read-only FAR_BSS evidence sweep for the five open words.

Run from the repository root with:
    python build/workers/dos_readonly_bss_semantics_v33/sweep_v33.py

The script reads the locked original image and current evidence. It writes only
disasm-sweep-v33.json beside this file. It never serializes original bytes.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "tools"))

import dataref  # noqa: E402
import exe  # noqa: E402
import farbss  # noqa: E402
import functions  # noqa: E402
import match  # noqa: E402
import modules  # noqa: E402

try:
    from capstone import Cs, CS_ARCH_X86, CS_MODE_16  # noqa: E402
except ImportError:
    sys.path.insert(0, "C:/tools/capstone-5.0.3")
    from capstone import Cs, CS_ARCH_X86, CS_MODE_16  # noqa: E402


TARGETS = {
    "fd_50F6_04C0": 0x04C0,
    "fd_50F6_0B20": 0x0B20,
    "fd_50F6_0F38": 0x0F38,
    "fd_50F6_0FB6": 0x0FB6,
    "fd_50F6_0FFA": 0x0FFA,
}
FRAME = 0x50F6
MEMORY_DEST_WRITES = {
    "mov", "add", "adc", "sub", "sbb", "and", "or", "xor", "inc", "dec",
    "not", "neg", "shl", "sal", "shr", "sar", "rol", "ror", "rcl", "rcr",
    "xchg", "xadd", "cmpxchg", "btc", "btr", "bts",
}
DIRECT_ES = re.compile(r"es:\[(?:0x([0-9a-f]+)|([0-9]+))\]", re.I)
MEMORY_OPERAND = re.compile(r"^(?:(?:byte|word|dword|qword) ptr )?es:\[", re.I)


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def access_kind(mnemonic: str, operands: str) -> str:
    first = operands.split(",", 1)[0].strip()
    if MEMORY_OPERAND.match(first) and mnemonic in MEMORY_DEST_WRITES:
        return "write"
    if mnemonic in {"cmp", "test", "push", "bt"} or not MEMORY_OPERAND.match(first):
        return "read"
    return "unknown"


def main() -> int:
    image = exe.load()
    start = farbss.FAR_BSS_SEG * 16
    end = match.DGROUP_SEG * 16
    region = image.read("S27", start, end - start)

    symbols_doc = json.loads((ROOT / "layout/symbols.json").read_text(encoding="utf-8"))
    symbols = symbols_doc["data"]
    manifest = modules.load_manifest()
    source_texts = {
        key: (ROOT / m["source"]).read_text(encoding="latin1")
        for key, m in manifest["modules"].items()
        if m.get("lang", "c") == "c"
    }
    farbss_result = farbss.account(sources=source_texts)
    farbss_rows = {row["name"].lstrip("_"): row for row in farbss_result["rows"]}

    rows = functions.table()["functions"]
    units = sorted({row["unit"] for row in rows})
    md = Cs(CS_ARCH_X86, CS_MODE_16)
    references: dict[int, list[dict]] = defaultdict(list)
    unclassified: list[dict] = []

    for unit in units:
        unit_rows = [row for row in rows if row["unit"] == unit]
        frame_refs, _ = dataref.far_refs(unit, unit_rows)
        base, code = image.unit_bytes(unit)
        for row in unit_rows:
            linear = row["seg"] * 16 + row["off"]
            function_name = functions.name_of(unit, row["seg"], row["off"])
            listing = code[linear - base : linear - base + row["size"]]
            for insn in md.disasm(listing, linear):
                for found in DIRECT_ES.finditer(insn.op_str):
                    off = int(found.group(1), 16) if found.group(1) else int(found.group(2), 10)
                    if off not in TARGETS.values():
                        continue
                    frame_ref = frame_refs.get((FRAME, off))
                    frame_confirmed = bool(frame_ref and function_name in frame_ref["users"])
                    direction = access_kind(insn.mnemonic, insn.op_str)
                    item = {
                        "unit": unit,
                        "function": function_name,
                        "function_address": f"{row['seg']:04X}:{row['off']:04X}",
                        "instruction_offset": f"{insn.address - linear:04X}",
                        "mnemonic": insn.mnemonic,
                        "operands": insn.op_str,
                        "access": direction,
                        "frame_50F6_confirmed_by_dataref": frame_confirmed,
                    }
                    references[off].append(item)
                    if direction == "unknown" or not frame_confirmed:
                        unclassified.append(item)

    target_rows = {}
    for name, off in TARGETS.items():
        same_offset = sorted(
            symbol_name
            for symbol_name, symbol in symbols.items()
            if symbol.get("seg") == FRAME and symbol.get("off") == off
        )
        next_starts = sorted(
            symbol.get("off")
            for symbol in symbols.values()
            if symbol.get("seg") == FRAME and isinstance(symbol.get("off"), int) and symbol["off"] > off
        )
        next_off = next_starts[0] if next_starts else None
        bss_row = farbss_rows.get(name)
        refs = references.get(off, [])
        target_rows[name] = {
            "address": f"{FRAME:04X}:{off:04X}",
            "initial_image_bytes_hex": region[off : off + 2].hex(),
            "registered_names_at_offset": same_offset,
            "next_registered_offset": f"{next_off:04X}" if next_off is not None else None,
            "next_registered_gap_bytes": next_off - off if next_off is not None else None,
            "farbss_size_status": bss_row.get("status") if bss_row else None,
            "farbss_size_evidence": bss_row.get("evidence") if bss_row else [],
            "direct_reference_count": len(refs),
            "direct_reference_reads": sum(ref["access"] == "read" for ref in refs),
            "direct_reference_writes": sum(ref["access"] == "write" for ref in refs),
            "direct_reference_unknowns": sum(ref["access"] == "unknown" for ref in refs),
            "direct_references": refs,
        }

    result = {
        "schema": "simant-dos-farbss-zero-owner-disassembly-sweep-v33",
        "read_only": True,
        "original_bytes_serialized": False,
        "original_image": {
            "path_from_oracle_lock": "assets/SIMANT.EXE",
            "oracle_lock_sha256": json.loads((ROOT / "layout/oracle.lock.json").read_text(encoding="utf-8"))["executable"]["sha256"],
            "far_bss_frame": f"{farbss.FAR_BSS_SEG:04X}",
            "far_bss_region_start_linear": f"{start:05X}",
            "far_bss_region_end_linear": f"{end:05X}",
            "far_bss_region_bytes": len(region),
            "far_bss_region_all_zero": not any(region),
            "zero_region_sha256": sha256(region),
        },
        "disassembly_scope": {
            "function_table": "layout/functions.json",
            "function_rows": len(rows),
            "units": len(units),
            "scan": "all direct ES:[immediate] operands at target offsets; frame cross-check via dataref.far_refs",
            "unclassified_or_unframed_references": unclassified,
        },
        "farbss_accounting": {
            "region_accounted": farbss_result["accounted"],
            "all_zero_failures": [failure for failure in farbss_result["failures"] if "not all zero" in failure],
            "target_classification_source": "declaration parsed by farbss.py; no compiler --probe run",
        },
        "targets": target_rows,
    }
    out_path = OUT / "disasm-sweep-v33.json"
    out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {out_path.relative_to(ROOT)}")
    print(f"FAR_BSS all zero: {result['original_image']['far_bss_region_all_zero']} ({len(region)} bytes)")
    print(f"function rows: {len(rows)} across {len(units)} units")
    for name, row in target_rows.items():
        print(
            f"{name}: bytes={row['initial_image_bytes_hex']} gap={row['next_registered_gap_bytes']} "
            f"status={row['farbss_size_status']} direct_refs={row['direct_reference_count']} "
            f"writes={row['direct_reference_writes']} unknown={row['direct_reference_unknowns']}"
        )
    return 0 if result["original_image"]["far_bss_region_all_zero"] and not unclassified else 1


if __name__ == "__main__":
    raise SystemExit(main())
