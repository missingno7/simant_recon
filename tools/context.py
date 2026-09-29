"""Compact evidence packet for one function.

    python tools/context.py FUNCTION [--raw] [--no-asm]
    python tools/context.py --list [SUBSTRING] [--open] [--max-size N]

FUNCTION is a registered name or UNIT:SEG:OFF.  Shows the extent, module
(code segment frame), frame/argument shape, disassembly with relocated far
calls and DGROUP operands named from layout/symbols.json, string references,
callers/callees, neighbours, Win16 correspondence candidates and the best
search draft.  --raw adds hex bytes.
"""
from __future__ import annotations

import argparse
import json
import re
import struct
import sys
from pathlib import Path

try:
    import capstone  # noqa: F401
except ImportError:  # sandboxed users cannot see the per-user site-packages
    import sys as _sys
    _sys.path.insert(0, "C:/tools/capstone-5.0.3")
from capstone import Cs, CS_ARCH_X86, CS_MODE_16

sys.path.insert(0, str(Path(__file__).resolve().parent))
import exe as exemod  # noqa: E402
import functions as fnmod  # noqa: E402
import symbols as symmod  # noqa: E402

ROOT = exemod.ROOT
DGROUP = 0x55B3
md = Cs(CS_ARCH_X86, CS_MODE_16)


def name_maps():
    s = symmod.load()
    code = {(r["unit"], r["seg"], r["off"]): n for n, r in s["code"].items()}
    for n, r in s["runtime"].items():
        code.setdefault((r["unit"], r["seg"], r["off"]), n)
    data = {(r["seg"], r["off"]): n for n, r in s["data"].items()}
    return code, data


def dgroup_string(off: int, maxlen: int = 60) -> str | None:
    x = exemod.load()
    s27 = x.sections[27]
    lin = DGROUP * 16 + off - s27.load_linear
    if not (0 <= lin < len(s27.data)):
        return None
    b = s27.data[lin:lin + maxlen]
    m = re.match(rb"[\x20-\x7e\t\r\n]{4,}", b)
    if m and (len(m.group()) == len(b) or b[len(m.group())] == 0):
        return m.group().decode("latin1")
    return None


def annotate(f: dict, code_names, data_names) -> list[str]:
    x = exemod.load()
    base, data = x.unit_bytes(f["unit"])
    lin = f["seg"] * 16 + f["off"]
    b = data[lin - base:lin - base + f["size"]]
    relocs = x.reloc_sites(f["unit"])
    vec = {v.offset: v for v in x.vectors}
    rows = []
    for i in md.disasm(b, f["off"]):
        text = f"{i.mnemonic} {i.op_str}".strip()
        note = ""
        site = f["seg"] * 16 + i.address
        if i.bytes[0] == 0x9A:
            off, seg = struct.unpack_from("<HH", i.bytes, 1)
            if seg == exemod.MANAGER_SEG and off in vec:
                v = vec[off]
                u = v.unit
                note = f"-> {code_names.get((u, v.target_seg, v.target_off), f'{u}:{v.target_seg:04X}:{v.target_off:04X}')} (vector {off:04X})"
            else:
                u = "root" if seg < 0x3126 else f["unit"]
                note = "-> " + code_names.get((u, seg, off), f"{u}:{seg:04X}:{off:04X}")
        elif i.bytes[0] == 0xE8:
            tgt = (i.address + 3 + struct.unpack_from("<h", i.bytes, 1)[0]) & 0xFFFF
            note = "-> " + code_names.get((f["unit"], f["seg"], tgt), f"{f['seg']:04X}:{tgt:04X}")
        else:
            for k in range(1, len(i.bytes) - 1):
                if site + k in relocs:
                    v = struct.unpack_from("<H", i.bytes, k)[0]
                    note = f"[seg {v:04X}{' DGROUP' if v == DGROUP else ''}]"
            m = re.search(r"\[(0x[0-9a-f]+)\]", text)
            if m and "bp" not in text:
                off = int(m.group(1), 16)
                seg_override = "es:" in text or "cs:" in text or "ss:" in text
                if not seg_override:
                    n = data_names.get((DGROUP, off))
                    note = f"DS:{off:04X}" + (f" {n}" if n else "")
            m2 = re.match(r"(mov|push)\s+\w*,?\s*(0x[0-9a-f]+)$", text)
            if m2 and not note:
                v = int(m2.group(2), 16)
                s = dgroup_string(v) if v >= 0x100 else None
                if s:
                    note = f'"{s}"'
        rows.append(f"  {i.address:04X}  {text:<34} {note}".rstrip())
    return rows


def frame_info(f: dict) -> dict:
    x = exemod.load()
    base, data = x.unit_bytes(f["unit"])
    lin = f["seg"] * 16 + f["off"]
    b = data[lin - base:lin - base + f["size"]]
    info = {}
    if b[:3] == b"\x55\x8b\xec":
        info["frame"] = "bp"
        rest = b[3:]
        if rest[:1] == b"\xb8" and rest[3:4] == b"\x9a":
            info["locals"] = struct.unpack_from("<H", rest, 1)[0]
            info["stack_check"] = True
        elif rest[:3] == b"\x33\xc0\x9a":
            info["locals"] = 0
            info["stack_check"] = True
        elif rest[:2] == b"\x83\xec":
            info["locals"] = rest[2]
            info["stack_check"] = False
        elif rest[:2] == b"\x81\xec":
            info["locals"] = struct.unpack_from("<H", rest, 2)[0]
            info["stack_check"] = False
        else:
            info["stack_check"] = False
    else:
        info["frame"] = "none"
    args = [int(m, 16) for m in re.findall(r"\[bp \+ (0x[0-9a-f]+)\]", " ".join(
        f"{i.op_str}" for i in md.disasm(b, 0)))]
    if args:
        info["arg_bytes_min"] = max(args) - 6 + 2
    return info


def inventory_edges():
    p = ROOT / "build" / "inventory" / "functions.json"
    if not p.exists():
        return {}
    return {f"{r['unit']}:{r['linear']:05X}": r for r in json.loads(p.read_text())["functions"]}


def show(func: str, raw: bool, no_asm: bool):
    f = fnmod.get(func)
    code_names, data_names = name_maps()
    x = exemod.load()
    lin = f["seg"] * 16 + f["off"]
    print(f"{f['name']}  {f['unit']}:{f['seg']:04X}:{f['off']:04X}  linear {lin:05X}  size {f['size']}  "
          f"extent {f['extent']}  region {f['region']}")
    print(f"  entry evidence: {', '.join(f['evidence'])}")
    same = [r for r in fnmod.table()["functions"] if r["unit"] == f["unit"] and r["seg"] == f["seg"]]
    same.sort(key=lambda r: r["off"])
    idx = next(i for i, r in enumerate(same) if r["off"] == f["off"])
    print(f"  module frame {f['seg']:04X}: function {idx + 1}/{len(same)}; "
          f"neighbours: " + ", ".join(fnmod.name_of(r["unit"], r["seg"], r["off"]) for r in same[max(0, idx - 2):idx + 3]
                                      if r["off"] != f["off"]))
    print(f"  frame: {frame_info(f)}")
    edges = inventory_edges().get(f"{f['unit']}:{lin:05X}")
    if edges:
        def nm(k):
            u, l = k.split(":")
            l = int(l, 16)
            for key, n in code_names.items():
                if key[0] == u and key[1] * 16 + key[2] == l:
                    return n
            return k
        print(f"  callers ({len(edges['callers'])}): " + ", ".join(nm(c) for c in edges["callers"][:12]))
        print(f"  callees ({len(edges['callees'])}): " + ", ".join(nm(c) for c in edges["callees"][:16]))
    corr = ROOT / "evidence" / "cross_version" / "simantw_correspondence.json"
    if corr.exists():
        c = json.loads(corr.read_text())
        pairs = [p for p in c.get("pairs", []) if p["dos"] == f["name"] or p.get("dos_address") ==
                 f"{f['unit']}:{f['seg']:04X}:{f['off']:04X}"]
        for p in pairs[:5]:
            print(f"  win16: {p['win16']} [{p['confidence']}] {'; '.join(p.get('evidence', [])[:3])}")
    best = ROOT / "build" / "search" / f["name"] / "best.json"
    if best.exists():
        b = json.loads(best.read_text())
        print(f"  best draft: build/search/{f['name']}/best.c  {b['status']} ratio {b.get('opcode_ratio')}")
    if not no_asm:
        for line in annotate(f, code_names, data_names):
            print(line)
    if raw:
        base, data = x.unit_bytes(f["unit"])
        print("  bytes:", data[lin - base:lin - base + f["size"]].hex())


def list_functions(sub: str | None, max_size: int | None):
    code_names, _ = name_maps()
    for r in fnmod.table()["functions"]:
        n = fnmod.name_of(r["unit"], r["seg"], r["off"])
        if sub and sub.lower() not in n.lower():
            continue
        if max_size and r["size"] > max_size:
            continue
        print(f"{n:<28} {r['unit']}:{r['seg']:04X}:{r['off']:04X} {r['size']:6d} {r['region']}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("function", nargs="?")
    ap.add_argument("--list", nargs="?", const="", default=None)
    ap.add_argument("--max-size", type=int)
    ap.add_argument("--raw", action="store_true")
    ap.add_argument("--no-asm", action="store_true")
    a = ap.parse_args()
    if a.list is not None:
        list_functions(a.list, a.max_size)
        return 0
    show(a.function, a.raw, a.no_asm)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
