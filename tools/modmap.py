"""Per-module (code segment) map: size, predicted profile signals, ASM indicators, status.

    python tools/modmap.py                 # table of all modules
    python tools/modmap.py --json OUT      # machine-readable (default build/modmap.json)
    python tools/modmap.py root:0093       # one module in detail

Signals are evidence for choosing a module profile before writing source; they
never grant acceptance.  Kinds:
  C?      MSC-shaped frames (push bp/mov bp,sp; stack check or sub sp; mov sp,bp)
  ASM?    frameless code with string/port/IVT idioms, cs: data, register calling
  MIXED   both present (candidate for a TU split, or C with inline asm)
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
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
import modules as modmod  # noqa: E402

ROOT = exemod.ROOT
md = Cs(CS_ARCH_X86, CS_MODE_16)
ASM_MNEMS = {"lodsb", "lodsw", "stosb", "stosw", "xlatb", "loop", "in", "out", "iret", "cli", "sti", "rep movsb",
             "rep movsw", "rep stosw", "rep stosb", "repne scasb", "cmc", "rcr", "rcl"}


def function_signals(data: bytes) -> dict:
    s = {"bp_frame": data[:3] == b"\x55\x8b\xec", "stack_check": False, "mov_sp_bp": False,
         "retf_n": False, "asm_idioms": 0, "cs_data": 0, "fastcall_hint": False, "pads_90": 0}
    if s["bp_frame"]:
        r = data[3:]
        s["stack_check"] = (r[:1] == b"\xb8" and r[3:4] == b"\x9a") or r[:3] == b"\x33\xc0\x9a"
    elif data[:3] == b"\x33\xc0\x9a":
        s["stack_check"] = True
    prev = None
    for i in md.disasm(data, 0):
        m = i.mnemonic if not i.mnemonic.startswith("rep") else f"{i.mnemonic} {i.op_str.split()[0] if i.op_str else ''}".strip()
        if i.mnemonic in ASM_MNEMS or m in ASM_MNEMS:
            s["asm_idioms"] += 1
        if "cs:" in i.op_str and "cs:[bx +" not in i.op_str:
            s["cs_data"] += 1
        if i.mnemonic == "mov" and i.op_str == "sp, bp":
            s["mov_sp_bp"] = True
        if i.mnemonic == "retf" and i.op_str:
            s["retf_n"] = True
        if i.mnemonic == "nop":
            s["pads_90"] += 1
        prev = i
    if s["bp_frame"] and s["retf_n"] and re.search(rb"\x52|\x89\x56|\x8b\xf0|\x8b\xf8", data[3:12]):
        s["fastcall_hint"] = True
    return s


def build() -> list[dict]:
    x = exemod.load()
    man = modmod.load_manifest()
    claimed = {c["name"]: k for k, m in man["modules"].items() for c in m["claims"]}
    rows = defaultdict(list)
    for r in fnmod.table()["functions"]:
        if r["region"] != "game_or_library":
            continue
        rows[(r["unit"], r["seg"])].append(r)
    out = []
    for (unit, seg), fs in sorted(rows.items(), key=lambda kv: (kv[0][0] != "root", kv[0][0], kv[0][1])):
        fs.sort(key=lambda r: r["off"])
        base, data = x.unit_bytes(unit)
        sig = defaultdict(int)
        names = []
        nclaimed = 0
        bclaimed = 0
        for f in fs:
            lin = f["seg"] * 16 + f["off"]
            s = function_signals(data[lin - base:lin - base + f["size"]])
            for k, v in s.items():
                sig[k] += int(v)
            n = fnmod.name_of(unit, seg, f["off"])
            if not re.match(r"^(f|o\d\d)_[0-9A-F]{4}_[0-9A-F]{4}$", n):
                names.append(n)
            if n in claimed:
                nclaimed += 1
                bclaimed += f["size"]
        n = len(fs)
        size = sum(f["size"] for f in fs)
        c_like = sig["bp_frame"]
        kind = "C?" if c_like >= 0.8 * n and sig["asm_idioms"] < 3 else \
               "ASM?" if c_like <= 0.2 * n or sig["cs_data"] else "MIXED"
        prof = ["/AL", "/Os"]
        if sig["stack_check"] == 0 and c_like:
            prof.append("/Gs")
        elif 0 < sig["stack_check"] < c_like:
            prof.append("/Gs?mixed")
        if sig["fastcall_hint"]:
            prof.append("_fastcall?")
        out.append({"module": f"{unit}:{seg:04X}", "functions": n, "bytes": size,
                    "kind": kind, "profile_guess": " ".join(prof),
                    "signals": dict(sig), "named": names[:12], "named_count": len(names),
                    "claimed": nclaimed, "claimed_bytes": bclaimed,
                    "manifest": f"{unit}:{seg:04X}" in man["modules"]})
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("module", nargs="?")
    ap.add_argument("--json", type=Path, default=ROOT / "build" / "modmap.json")
    a = ap.parse_args()
    rows = build()
    a.json.parent.mkdir(parents=True, exist_ok=True)
    a.json.write_text(json.dumps(rows, indent=1))
    if a.module:
        for r in rows:
            if r["module"] == a.module:
                print(json.dumps(r, indent=1))
                for f in sorted((f for f in fnmod.table()["functions"] if f"{f['unit']}:{f['seg']:04X}" == a.module),
                                key=lambda f: f["off"]):
                    print(f"  {fnmod.name_of(f['unit'], f['seg'], f['off']):<28} {f['off']:04X} {f['size']:5d}")
        return 0
    print(f"{'module':<11} {'fn':>4} {'bytes':>6} {'kind':<6} {'claimed':>8} {'profile guess':<28} named")
    for r in rows:
        print(f"{r['module']:<11} {r['functions']:4d} {r['bytes']:6d} {r['kind']:<6} "
              f"{r['claimed']:3d}/{r['functions']:<4d} {r['profile_guess']:<28} {', '.join(r['named'][:4])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
