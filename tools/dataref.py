"""DGROUP references of a module: helps choose private data placements.

    python tools/dataref.py root:0894            # all DS offsets used by the module's functions
    python tools/dataref.py root:0894 --strings  # only immediates that address strings

For every function in the module it collects
  * memory operands  [imm]            (DGROUP variables, DS-relative)
  * immediates       mov r16,imm/push  that address a NUL-terminated string (literal pool)
  * CONST segment words  mov es,[imm]  whose word carries a data relocation (extern far data)
and prints them sorted by DGROUP offset with the functions using them, the byte
class (initialised data < 0x8BA0 <= BSS) and a preview.  Contiguous runs of
literals used only by this module are the likely private `_DATA` block.
"""
from __future__ import annotations

import argparse
import re
import struct
import sys
from collections import defaultdict
from pathlib import Path

try:
    import capstone  # noqa: F401
except ImportError:
    import sys as _sys
    _sys.path.insert(0, "C:/tools/capstone-5.0.3")
from capstone import Cs, CS_ARCH_X86, CS_MODE_16

sys.path.insert(0, str(Path(__file__).resolve().parent))
import exe as exemod  # noqa: E402
import functions as fnmod  # noqa: E402

DGROUP = 0x55B3
INIT_END = 0x8BA0
md = Cs(CS_ARCH_X86, CS_MODE_16)


def dgroup_bytes():
    x = exemod.load()
    s27 = x.sections[27]
    return s27.data[DGROUP * 16 - s27.load_linear:], {sg * 16 + o - DGROUP * 16 for sg, o in s27.relocs}


def preview(dg: bytes, off: int) -> str:
    if off >= len(dg):
        return "(bss)"
    b = dg[off:off + 40]
    m = re.match(rb"[\x20-\x7e\t\r\n]{3,}", b)
    if m and (len(m.group()) == len(b) or b[len(m.group())] == 0) and (off == 0 or not 0x20 <= dg[off - 1] < 0x7F):
        return '"' + m.group().decode("latin1").replace("\n", "\\n") + '"'
    return b[:8].hex()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("module")
    ap.add_argument("--strings", action="store_true")
    a = ap.parse_args()
    unit, seg = a.module.split(":")
    seg = int(seg, 16)
    x = exemod.load()
    base, data = x.unit_bytes(unit)
    dg, dreloc = dgroup_bytes()
    refs = defaultdict(lambda: {"kinds": set(), "users": set()})
    rows = sorted((r for r in fnmod.table()["functions"] if r["unit"] == unit and r["seg"] == seg),
                  key=lambda r: r["off"])
    for r in rows:
        name = fnmod.name_of(unit, seg, r["off"])
        lin = r["seg"] * 16 + r["off"]
        for i in md.disasm(data[lin - base:lin - base + r["size"]], r["off"]):
            ops = i.op_str
            if any(p in ops for p in ("cs:", "es:", "ss:", "bp", "[bx", "[si", "[di")) and "[0x" not in ops:
                pass
            m = re.search(r"(?<![:\w])\[(0x[0-9a-f]+)\]", ops)
            if m and not re.search(r"(cs|es|ss):\[", ops):
                off = int(m.group(1), 16)
                kind = "CONSTSEG" if (i.mnemonic == "mov" and ops.startswith("es,") and off in dreloc) else "var"
                refs[off]["kinds"].add(kind)
                refs[off]["users"].add(name)
            # DS-relative tables indexed by a register: [bx + 0x1b72], [bx + di + 0x1b82]
            m3 = re.search(r"(?<![:\w])\[(?:bx|si|di)(?: \+ (?:si|di))? \+ (0x[0-9a-f]+)\]", ops)
            if m3 and not re.search(r"(cs|es|ss):\[", ops):
                off = int(m3.group(1), 16)
                if off >= 0x100:
                    refs[off]["kinds"].add("table")
                    refs[off]["users"].add(name)
            m2 = re.match(r"(?:mov (?:ax|bx|cx|dx|si|di), |push )(0x[0-9a-f]+)$", ops if i.mnemonic != "push" else "push " + ops)
            if i.mnemonic == "mov":
                m2 = re.match(r"(?:ax|bx|cx|dx|si|di), (0x[0-9a-f]+)$", ops)
            if m2:
                off = int(m2.group(1), 16)
                if 0x40 <= off < len(dg) and preview(dg, off).startswith('"'):
                    refs[off]["kinds"].add("string")
                    refs[off]["users"].add(name)
    print(f"{a.module}: {len(rows)} functions, {len(refs)} DGROUP references (init data ends at {INIT_END:04X})")
    for off in sorted(refs):
        r = refs[off]
        if a.strings and "string" not in r["kinds"]:
            continue
        cls = "BSS " if off >= INIT_END else "DATA"
        print(f"  {off:04X} {cls} {'/'.join(sorted(r['kinds'])):<14} {preview(dg, off):<44} "
              f"{', '.join(sorted(r['users']))[:70]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
