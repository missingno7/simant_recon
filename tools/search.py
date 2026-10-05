"""Compile candidate source and compare it strictly with an oracle function.

    python tools/search.py FUNCTION candidate.c [more.c ...] [--profile msc600] [--flags /AL /Gs]
                           [--public NAME] [--placement SEG=OFF ...] [--quiet]

FUNCTION is a registered code name (layout/symbols.json) or ``UNIT:SEG:OFF``.
The target extent comes from layout/functions.json.  A ``.asm`` candidate is
assembled (profile ``masm510`` unless --profile names another assembler profile)
and bound exactly like a C object.  Output: the strict result
plus diagnostics (first differing instruction, aligned opcode similarity,
fixup/relocation differences).  The best draft per function (strict exact
first, then aligned-opcode score) is kept under build/search/FUNCTION/.

Search never publishes; use promote.py for canonical source.
Defaults come from the target object's manifest profile, flags and private-data
placements. Explicit options override them; an unrecorded object uses profile defaults.
"""
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import shutil
import sys
from pathlib import Path

try:
    import capstone  # noqa: F401
except ImportError:  # sandboxed users cannot see the per-user site-packages
    import sys as _sys
    _sys.path.insert(0, "C:/tools/capstone-5.0.3")
from capstone import Cs, CS_ARCH_X86, CS_MODE_16

sys.path.insert(0, str(Path(__file__).resolve().parent))
import compiler  # noqa: E402
import exe as exemod  # noqa: E402
import match  # noqa: E402
import functions as fnmod  # noqa: E402
import modctx  # noqa: E402
import modules as modmod  # noqa: E402

ROOT = exemod.ROOT
md = Cs(CS_ARCH_X86, CS_MODE_16)


def disasm(b: bytes, org: int):
    out = []
    for i in md.disasm(b, org):
        out.append((i.address, i.bytes.hex(), f"{i.mnemonic} {i.op_str}".strip()))
    return out


def opcode_seq(rows):
    return [r[2].split(" ")[0] for r in rows]


def diagnose(res: match.MatchResult, org: int) -> dict:
    a = disasm(res.candidate, org)
    b = disasm(res.original, org)
    sm = difflib.SequenceMatcher(a=opcode_seq(a), b=opcode_seq(b), autojunk=False)
    first = None
    for i, (x, y) in enumerate(zip(a, b)):
        if x[1] != y[1]:
            first = i
            break
    return {"opcode_ratio": round(sm.ratio(), 4), "cand_insns": len(a), "orig_insns": len(b),
            "first_diff_insn": first, "cand": a, "orig": b}


def print_side_by_side(d: dict, limit: int = 400):
    a, b = d["cand"], d["orig"]
    sm = difflib.SequenceMatcher(a=[r[1] for r in a], b=[r[1] for r in b], autojunk=False)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            if i2 - i1 > 4:
                print(f"      ... {i2 - i1} equal instructions ...")
                continue
        for k in range(max(i2 - i1, j2 - j1)):
            ca = a[i1 + k] if i1 + k < i2 else None
            ob = b[j1 + k] if j1 + k < j2 else None
            mark = " " if tag == "equal" else "!"
            left = f"{ca[0]:04X} {ca[2]}" if ca else ""
            right = f"{ob[0]:04X} {ob[2]}" if ob else ""
            print(f"  {mark} {left:<40} | {right}")
            limit -= 1
            if limit <= 0:
                print("  ...")
                return


def options(f: dict, asm: bool, profile: str | None, flags, placements: dict) -> dict:
    """Use the same object context as whole-module verification, retaining CLI overrides."""
    man = modmod.load_manifest()
    key = modctx.key_for_function(f, man)
    rec = man["modules"].get(key, {})
    # A C experiment in an assembly-owned object must still go through a compiler.
    compatible = rec.get("lang", "c") == ("asm" if asm else "c")
    recorded = rec.get("profile") if compatible else None
    if asm:
        prof = profile if profile and profile.startswith("masm") else recorded or "masm510"
    else:
        prof = profile or recorded or f.get("profile") or fnmod.DEFAULT_PROFILE
    if flags is not None:
        fl = list(flags)
    elif compatible and "flags" in rec:
        fl = list(rec["flags"])
    else:
        fl = fnmod.profile_flags(prof)
    pl = {name: {"seg": p["seg"], "off": p["off"]}
          for name, p in rec.get("placements", {}).items()}
    pl.update(placements)
    return {"module": key, "profile": prof, "flags": fl, "placements": pl}


def run(func: str, sources: list[Path], profile: str | None, flags, public: str | None,
        placements: dict, quiet: bool = False) -> list[dict]:
    f = fnmod.get(func)
    target = match.Target(f["unit"], f["seg"], f["off"], f["size"])
    pub = "_" + (public or f["name"])
    outdir = ROOT / "build" / "scratch" / "search" / f["name"]
    outdir.mkdir(parents=True, exist_ok=True)
    results = []
    for src in sources:
        text = src.read_text(encoding="latin1")
        asm = src.suffix.lower() == ".asm"
        context = options(f, asm, profile, flags, placements)
        prof, fl = context["profile"], context["flags"]
        r = compiler.assemble(text, prof, fl) if asm else compiler.compile_c(text, prof, fl)
        row = {"source": str(src), **context,
               "source_sha256": hashlib.sha256(text.encode("latin1")).hexdigest()}
        if not r.ok:
            row["status"] = "COMPILER_ERROR"
            row["log"] = r.log[-800:]
            print(f"[{src.name}] COMPILER_ERROR\n{r.log[-800:]}")
            results.append(row)
            continue
        # the public as the module check sees it (match.public_in: _cdecl, @fastcall, pascal
        # names registered with convention pascal, older alias spellings)
        obj = match.OmfReader(communals=True).read(r.obj)
        pname, prec = match.public_in(obj, pub[1:])
        if prec is None:
            hint = [p["name"] for p in obj.publics if p["name"] == pub[1:].upper()]
            if hint:
                print(f"  note: pascal public {hint[0]}: bind it by registering the convention "
                      f"(python tools/symbols.py set-convention {pub[1:]} pascal --why ...)")
        res = match.Binder(target, obj, prec["segment"] if prec else fnmod.code_segment(r.obj, pub),
                           pname or pub, context["placements"]).bind()
        d = diagnose(res, f["off"])
        row.update({"status": "EXACT" if res.exact else "MISMATCH", "reasons": res.reasons,
                    "opcode_ratio": d["opcode_ratio"], "first_diff_insn": d["first_diff_insn"],
                    "unbound": sorted(set(res.unbound))})
        print(f"[{src.name}] {res.summary()}  (opcode similarity {d['opcode_ratio']:.3f}, "
              f"{d['cand_insns']} vs {d['orig_insns']} insns)")
        if not res.exact and not quiet:
            print_side_by_side(d)
            if res.relocs_expected != res.relocs_candidate:
                print(f"  relocations expected {[hex(v) for v in res.relocs_expected]}")
                print(f"  relocations candidate {[hex(v) for v in res.relocs_candidate]}")
        results.append(row)
        # keep best draft
        best = outdir / "best.json"
        score = (1 if res.exact else 0, d["opcode_ratio"])
        prev = json.loads(best.read_text()) if best.exists() else None
        if prev is None or tuple(prev["score"]) < score:
            shutil.copyfile(src, outdir / ("best.asm" if asm else "best.c"))
            best.write_text(json.dumps({"score": score, **row}, indent=1))
    log = outdir / "history.jsonl"
    with log.open("a") as fh:
        for row in results:
            fh.write(json.dumps({k: v for k, v in row.items() if k != "log"}) + "\n")
    return results


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("function")
    ap.add_argument("sources", nargs="+", type=Path)
    ap.add_argument("--profile", default=None)
    ap.add_argument("--flags", nargs="*", default=None)
    ap.add_argument("--public", default=None)
    ap.add_argument("--placement", action="append", default=[],
                    help="SEGNAME=SEG:OFF placement of a private data segment, e.g. CONST=55B3:1234")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()
    placements = {}
    for p in a.placement:
        name, addr = p.split("=")
        s, o = addr.replace(";", ":").split(":")  # undo MSYS path-list conversion
        placements[name] = {"seg": int(s, 16), "off": int(o, 16)}
    rows = run(a.function, a.sources, a.profile, a.flags, a.public, placements, a.quiet)
    return 0 if any(r["status"] == "EXACT" for r in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
