"""DGROUP references of a module: helps choose private data placements.

    python tools/dataref.py root:0894            # all DS offsets used by the module's functions
    python tools/dataref.py root:0894 --strings  # only immediates that address strings
    python tools/dataref.py root:0894 --far      # far-frame references (ES via CONST words, SEG immediates)

For every function in the module it collects
  * memory operands  [imm]            (DGROUP variables, DS-relative)
  * immediates       mov r16,imm/push  that address a NUL-terminated string (literal pool)
  * CONST segment words  mov es,[imm]  whose word carries a data relocation (extern far data)
and prints them sorted by DGROUP offset with the functions using them, the byte
class (initialised data < 0x8BA0 <= BSS) and a preview.  Contiguous runs of
literals used only by this module are the likely private `_DATA` block.

``--far`` follows ES through each function: loaded from a CONST segment word
(``mov es,[w]`` or via a register), from a relocated SEG immediate (``mov ax,SEG x;
mov es,ax``) or from a DGROUP far pointer (``les``); every ``es:[...+disp]`` operand is
then a reference to FRAME:disp.  It prints the references per far frame (with the
registered name, or nearest name+delta) and, per CONST word, the far offsets reached
through it.  A module that *defines* a far frame reaches all its variables through its
own segment (FARSEG-1): many offsets behind one word are the signature.
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


def far_refs(unit: str, rows: list) -> tuple[dict, dict]:
    """(refs, words): refs {(frame, off): {"via": set, "users": set}}; words {DG offset: {"frame",
    "offs": set, "users": set}} for the CONST segment words used to load ES."""
    x = exemod.load()
    base, data = x.unit_bytes(unit)
    relsites = x.reloc_sites(unit)
    dg, dreloc = dgroup_bytes()
    refs = defaultdict(lambda: {"via": set(), "users": set()})
    words = defaultdict(lambda: {"frame": None, "offs": set(), "users": set()})
    for r in rows:
        name = fnmod.name_of(unit, r["seg"], r["off"])
        lin = r["seg"] * 16 + r["off"]
        es = None                          # (frame, via, DG word or None)
        regs = {}                          # register -> (frame, via, word)
        for i in md.disasm(data[lin - base:lin - base + r["size"]], lin):
            mn, ops = i.mnemonic, i.op_str
            if mn in ("call", "lcall", "ret", "retf", "int", "iret"):
                es, regs = None, {}
                continue
            m = re.match(r"(ax|bx|cx|dx|si|di|bp), (0x[0-9a-f]+|\d+)$", ops)
            if mn == "mov" and m:
                if i.address + 1 in relsites:
                    v = struct.unpack_from("<H", data, i.address + 1 - base)[0]
                    regs[m.group(1)] = (v, "SEG", None)
                else:
                    regs.pop(m.group(1), None)
                continue
            m = re.match(r"(ax|bx|cx|dx|si|di|bp), word ptr \[(0x[0-9a-f]+|\d+)\]$", ops)
            if mn == "mov" and m:
                w = int(m.group(2), 0)
                if w in dreloc and w + 2 <= len(dg):
                    regs[m.group(1)] = (struct.unpack_from("<H", dg, w)[0], f"CONST DG:{w:04X}", w)
                else:
                    regs.pop(m.group(1), None)
                continue
            if mn == "mov" and ops.startswith("es, "):
                src = ops[4:]
                mm = re.match(r"word ptr \[(0x[0-9a-f]+|\d+)\]$", src)
                if mm and int(mm.group(1), 0) in dreloc:
                    w = int(mm.group(1), 0)
                    es = (struct.unpack_from("<H", dg, w)[0], f"CONST DG:{w:04X}", w)
                else:
                    es = regs.get(src)
                if es and es[2] is not None:
                    words[es[2]]["frame"] = es[0]
                    words[es[2]]["users"].add(name)
                continue
            if mn == "les":
                mm = re.search(r"dword ptr \[(0x[0-9a-f]+|\d+)\]$", ops)
                w = int(mm.group(1), 0) + 2 if mm else None
                es = (struct.unpack_from("<H", dg, w)[0], f"far ptr DG:{w - 2:04X}", None) \
                    if w is not None and w in dreloc else None
                continue
            if mn == "pop" and ops == "es":
                es = None
                continue
            dst = ops.split(",")[0]
            if mn not in ("cmp", "test", "push") and re.match(r"(ax|bx|cx|dx|si|di|bp)$", dst):
                regs.pop(dst, None)
            mm = re.search(r"es:\[(?:(?:bx|si|di|bp)(?: \+ (?:si|di))?(?: [+-] )?)?(0x[0-9a-f]+|\d+)?\]", ops)
            if mm and es is not None and 0x3D57 <= es[0] < 0x55B3 and mn != "lea":
                off = int(mm.group(1), 0) if mm.group(1) else 0
                if "- " + (mm.group(1) or "") in ops:
                    off = -off & 0xFFFF
                refs[(es[0], off)]["via"].add(es[1])
                refs[(es[0], off)]["users"].add(name)
                if es[2] is not None:
                    words[es[2]]["offs"].add(off)
    return refs, words


def far_name(frame: int, off: int) -> str:
    import symbols as symmod
    best = None
    for n, r in symmod.load()["data"].items():
        if r["seg"] == frame and r["off"] <= off and not r.get("alias_of"):
            if best is None or r["off"] > best[1]["off"] or (r["off"] == best[1]["off"] and best[0].startswith("fd_")):
                best = (n, r)
    if best is None:
        return "?"
    return best[0] + (f"+{off - best[1]['off']:X}" if off != best[1]["off"] else "")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("module")
    ap.add_argument("--strings", action="store_true")
    ap.add_argument("--far", action="store_true", help="far-frame references (ES) instead of DGROUP")
    a = ap.parse_args()
    import modules as modmod
    unit, seg, origin = modmod.parse_key(a.module)   # UNIT:SEG or UNIT:SEG@OFF
    lo, hi = modmod.object_range(modmod.load_manifest(), unit, seg, origin)
    x = exemod.load()
    base, data = x.unit_bytes(unit)
    dg, dreloc = dgroup_bytes()
    refs = defaultdict(lambda: {"kinds": set(), "users": set()})
    rows = sorted((r for r in fnmod.table()["functions"]
                   if r["unit"] == unit and r["seg"] == seg and lo <= r["off"] < hi),
                  key=lambda r: r["off"])
    if a.far:
        frefs, words = far_refs(unit, rows)
        print(f"{a.module}: {len(rows)} functions, {len(frefs)} far references in "
              f"{len({f for f, _ in frefs})} frames, {len(words)} CONST segment words")
        for (fr, off) in sorted(frefs):
            r = frefs[(fr, off)]
            print(f"  {fr:04X}:{off:04X} {far_name(fr, off):<24} via {', '.join(sorted(r['via'])):<22} "
                  f"{', '.join(sorted(r['users']))[:60]}")
        for w in sorted(words):
            r = words[w]
            offs = sorted(r["offs"])
            print(f"  CONST DG:{w:04X} -> {r['frame']:04X}: {len(offs)} offsets "
                  f"{' '.join(f'{o:04X}' for o in offs[:12])}{' ...' if len(offs) > 12 else ''}  "
                  f"({', '.join(sorted(r['users']))[:50]})")
        return 0
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
