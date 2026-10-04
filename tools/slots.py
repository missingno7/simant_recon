"""Stack-slot / register correspondence between a candidate function and the original.

    python tools/slots.py FUNC SOURCE [--module KEY] [--profile P] [--flags /AL /Os ...]
                          [--placement SEG=SSSS:OOOO ...] [--listing fc|fa] [--sbs] [-n N] [--json OUT]

Compiles SOURCE once with a listing (``/Fc`` by default; ``/Fa`` with ``--listing fa``; neither
changes the object), binds FUNC exactly like search.py (tools/match.py) and aligns candidate
and original instructions with ``[bp+N]`` offsets and branch targets masked.  It prints

  * the strict match summary and both frame sizes;
  * the candidate's slot map from the listing: ``name = -N`` locals/parameters,
    ``register si = name`` register variables, and the names MSC writes after each
    ``[bp+N]`` operand (so CSE temporaries show up as unnamed slots);
  * the slot correspondence ``our slot (names) -> original slot xCOUNT`` with a verdict
    (same / MOVED / SPLIT) and detected swaps, e.g. ``swap tx -0x0a <-> tattr -0x0c``;
  * original slots that no candidate slot maps to (often a CSE temporary the draft lacks);
  * register substitutions (``si -> di x12``) on otherwise identical instructions;
  * the remaining *non-BP* differences (operand order, extra/missing instructions);
  * with ``--sbs`` the full side-by-side (candidate | original) with slot names.

Options default to the module's manifest record (profile, flags, placements), so a draft of a
module in the manifest usually needs no flags.  The listing and object are scratch output
under build/cc (removed afterwards); ``--json`` writes under build/ only.

Examples (Git Bash: ``export MSYS_NO_PATHCONV=1`` first):

    python tools/slots.py DoAntMoveY build/workers/slots-doantmovey/e4.c
    python tools/slots.py DoAntMoveY build/workers/slots-doantmovey/e4.c --flags /AL /Os /Oe /Og /Zd --sbs
    python tools/slots.py S25:3BA4:0008 draft.c --module "S25;3BA4" --placement CONST=55B3:8942

Analysis only: a slot map explains a mismatch; acceptance is still promote.py.
"""
from __future__ import annotations

import argparse
import difflib
import re
import shutil
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import functions as fnmod  # noqa: E402
import modctx  # noqa: E402
import search  # noqa: E402

BP_RE = re.compile(r"\[bp ([-+]) (0x[0-9a-f]+|\d+)\]")
BRANCH = {"jmp", "je", "jne", "jz", "jnz", "jl", "jle", "jg", "jge", "jb", "jbe", "ja", "jae", "js", "jns",
          "jo", "jno", "jp", "jnp", "jcxz", "loop", "loope", "loopne", "call"}
REGS = {"ax", "bx", "cx", "dx", "si", "di", "al", "ah", "bl", "bh", "cl", "ch", "dl", "dh", "es", "ds"}
# /Fc: "\t*** 00003a\t8d 46 f4 \t\tlea\tax,WORD PTR [bp-12]\t;tattr"
COD_INSN = re.compile(r"^\s*\*\*\* ([0-9a-fA-F]{6})\s+(?:[0-9a-f]{2} )+\s*(.*?)\s*$")
SLOT_RE = re.compile(r"^;\t(?:register (\w+) = (\w+)|(\w+) = (-?\d+))\s*$")
OPERAND_BP = re.compile(r"\[bp([-+]\d+)\]")


def bp_offsets(text: str) -> list[int]:
    return [(-1 if m.group(1) == "-" else 1) * int(m.group(2), 0) for m in BP_RE.finditer(text)]


def normalise(text: str) -> str:
    """Instruction key for alignment: BP offsets and branch targets masked."""
    t = BP_RE.sub("[bp+?]", text)
    mn = t.split(" ")[0]
    if mn in BRANCH and re.match(r"^\S+ 0x[0-9a-f]+$", t):
        t = mn + " L"
    return t


def parse_listing(text: str, public: str) -> dict:
    """Slot declarations and per-instruction BP names of one PROC of a /Fc or /Fa listing.
    Returns {"slots": {name: off}, "regs": [(reg, name)], "names": {obj_off: [(bp_off, name)]},
    "bpnames": {bp_off: set(names)}}."""
    i = text.find(f"{public}\tPROC")
    if i < 0:
        return {"slots": {}, "regs": [], "names": {}, "bpnames": {}}
    j = text.find(f"{public}\tENDP", i)
    body = text[i:j if j > 0 else len(text)]
    slots, regs, names, bpnames = {}, [], {}, defaultdict(set)
    for line in body.splitlines():
        m = SLOT_RE.match(line)
        if m:
            if m.group(1):
                regs.append((m.group(1), m.group(2)))
            else:
                slots[m.group(3)] = int(m.group(4))
                bpnames[int(m.group(4))].add(m.group(3))
            continue
        m = COD_INSN.match(line)
        if m and ";" in m.group(2):
            ins, _, comment = m.group(2).rpartition(";")
            offs = [int(v) for v in OPERAND_BP.findall(ins)]
            nm = comment.strip()
            if offs and re.match(r"^\w+$", nm):
                names.setdefault(int(m.group(1), 16), []).append((offs[0], nm))
                bpnames[offs[0]].add(nm)
    return {"slots": slots, "regs": regs, "names": names, "bpnames": dict(bpnames)}


def frame_size(rows) -> int | None:
    """``mov ax,N`` before ``__aFchkstk`` or ``sub sp,N`` in the prologue."""
    for k, (_, _, t) in enumerate(rows[:8]):
        m = re.match(r"^(?:mov ax|sub sp), (0x[0-9a-f]+|\d+)$", t)
        if m:
            return int(m.group(1), 0)
    return None


def fmt(off: int) -> str:
    return f"{'-' if off < 0 else '+'}0x{abs(off):02x}"


def correspond(cand, orig):
    """Align and tally.  Returns (M, R, other, pairs, where): M[our_bp][orig_bp] counts over all
    aligned instructions (identical ones included), R[our_reg][orig_reg] counts, other = non-BP
    differences, pairs = aligned rows, where[(our_bp, orig_bp)] = aligned row indices."""
    sm = difflib.SequenceMatcher(a=[normalise(r[2]) for r in cand], b=[normalise(r[2]) for r in orig],
                                 autojunk=False)
    M, R = defaultdict(Counter), defaultdict(Counter)
    where = defaultdict(list)
    other, pairs = [], []

    def tally(x, y):
        for a, b in zip(bp_offsets(x[2]), bp_offsets(y[2])):
            M[a][b] += 1
            where[(a, b)].append(len(pairs) - 1)

    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal" or (tag == "replace" and i2 - i1 == j2 - j1):
            for k in range(i2 - i1):
                x, y = cand[i1 + k], orig[j1 + k]
                pairs.append((x, y))
                if x[1] == y[1] or normalise(x[2]) == normalise(y[2]):
                    tally(x, y)
                    continue
                xt, yt = re.split(r"[ ,]+", BP_RE.sub("BP", x[2])), re.split(r"[ ,]+", BP_RE.sub("BP", y[2]))
                subs = [(p, q) for p, q in zip(xt, yt) if p != q]
                if len(xt) == len(yt) and subs and all(p in REGS and q in REGS for p, q in subs):
                    for p, q in subs:
                        R[p][q] += 1
                    tally(x, y)
                    continue
                if len(xt) == len(yt) and not subs:     # BP-only difference inside a replace block
                    tally(x, y)
                    continue
                other.append((x, y))
        else:
            for k in range(max(i2 - i1, j2 - j1)):
                x = cand[i1 + k] if i1 + k < i2 else None
                y = orig[j1 + k] if j1 + k < j2 else None
                pairs.append((x, y))
                other.append((x, y))
    return M, R, other, pairs, where


def exchange_kind(where, a: int, b: int, window: int = 4) -> str:
    """A mutual mapping a->b, b->a is a *slot swap* when at least one use is isolated; when
    every use has its mirror within a few aligned instructions it is a local operand-order
    exchange (commutative operands, argument order), not a slot assignment."""
    ab, ba = where.get((a, b), []), where.get((b, a), [])
    isolated = [i for i in ab if not any(abs(i - j) <= window for j in ba)] +                [j for j in ba if not any(abs(i - j) <= window for i in ab)]
    return "swap" if isolated else "operand-order exchange"


def report(func: str, source: str, ctx, res, cand, orig, lst: dict, M, R, other, pairs, where, a) -> dict:
    names = lst["bpnames"]

    def label(off):
        return ",".join(sorted(names.get(off, []))) or "(unnamed)"

    print(f"{func} [{ctx.key}] {source}  {ctx.profile} {' '.join(ctx.flags)}")
    print(f"  {res.summary()}")
    print(f"  frame: candidate {frame_size(cand)}  original {frame_size(orig)}   "
          f"instructions {len(cand)} vs {len(orig)}")
    print("candidate slots (listing):")
    for off in sorted(names, key=lambda v: (v > 0, -v if v < 0 else v)):
        print(f"  [bp{fmt(off)}] {label(off)}")
    for reg, nm in lst["regs"]:
        print(f"  register {reg} = {nm}")
    print("slot correspondence (our slot -> original slot xN):")
    out = {"func": func, "summary": res.summary(), "map": {}, "swaps": [], "exchanges": [],
           "unmatched_orig": [], "regs": {}, "other": []}
    for off in sorted(set(M) | set(names)):
        tgt = M.get(off, Counter())
        if not tgt:
            continue
        same = tgt.get(off, 0)
        moved = {b: n for b, n in tgt.items() if b != off}
        verdict = "same" if not moved else ("MOVED" if len(tgt) == 1 else "SPLIT")
        out["map"][fmt(off)] = {"names": sorted(names.get(off, [])), "to": {fmt(b): n for b, n in tgt.items()},
                                "verdict": verdict}
        if verdict == "same" and not a.all:
            continue
        print(f"  [bp{fmt(off)}] {label(off):<22} -> " +
              ", ".join(f"{fmt(b)}x{n}" for b, n in tgt.most_common()) + f"   {verdict}")
    unchanged = sum(1 for v in out["map"].values() if v["verdict"] == "same")
    if unchanged and not a.all:
        print(f"  ({unchanged} slots map to themselves; --all lists them)")
    explained = set()
    for x, y in sorted({tuple(sorted((p, q))) for p, t in M.items() for q in t if q != p and M.get(q, {}).get(p)}):
        kind = exchange_kind(where, x, y)
        s = (f"{kind} {label(x)} {fmt(x)} <-> {label(y)} {fmt(y)}  "
             f"({M[x][y]}+{M[y][x]} uses of {sum(M[x].values())}+{sum(M[y].values())})")
        print(f"  {s}")
        out["swaps" if kind == "swap" else "exchanges"].append(s)
        if kind != "swap":
            explained |= {(x, y), (y, x)}
    targets = defaultdict(set)
    for p, t in M.items():
        for b in t:
            if (p, b) not in explained:
                targets[b].add(p)
    for b, ps in sorted(targets.items()):
        if len(ps) > 1:
            print(f"  original [bp{fmt(b)}] receives several candidate slots: "
                  + ", ".join(f"{fmt(p)} {label(p)}" for p in sorted(ps)) + "  MERGED")
    orig_used = Counter(o for _, y in pairs if y for o in bp_offsets(y[2]))
    mapped = {b for t in M.values() for b in t}
    lone = sorted(o for o in orig_used if o not in mapped)
    if lone:
        print("original slots with no candidate counterpart: "
              + ", ".join(f"[bp{fmt(o)}] x{orig_used[o]}" for o in lone))
        out["unmatched_orig"] = [fmt(o) for o in lone]
    if R:
        regname = defaultdict(list)
        for reg, nm in lst["regs"]:
            regname[reg].append(nm)
        print("register substitutions (our -> original, otherwise identical instructions):")
        for p, t in sorted(R.items()):
            print(f"  {p} ({','.join(regname.get(p, [])) or '-'}) -> " + ", ".join(f"{q}x{n}" for q, n in t.most_common()))
            out["regs"][p] = dict(t)
    print(f"non-BP differences: {len(other)}")
    for x, y in other[:a.n]:
        left = f"{x[0]:04X} {x[2]}" if x else ""
        right = f"{y[0]:04X} {y[2]}" if y else ""
        print(f"    {left:<44} | {right}")
        out["other"].append([left, right])
    if len(other) > a.n:
        print(f"    ... {len(other) - a.n} more (-n)")
    bad = [g for g in sorted(set(res.reloc_key.values()))
           if [s for s in res.relocs_expected if res.reloc_key.get(s) == g]
           != [s for s in res.relocs_candidate if res.reloc_key.get(s) == g]]
    if bad and sorted(res.relocs_expected) == sorted(res.relocs_candidate):
        print(f"within-group relocation order differs in {len(bad)} group(s): {', '.join(bad[:6])} "
              "(record breaks: see tools/records.py)")
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("func", help="registered function name or UNIT:SEG:OFF")
    ap.add_argument("source", help="candidate C file (whole module draft)")
    ap.add_argument("--module", help="module key (default: the module owning FUNC)")
    ap.add_argument("--profile")
    ap.add_argument("--flags", nargs="*")
    ap.add_argument("--placement", action="append", default=[], help="SEG=SSSS:OOOO[:SIZE]")
    ap.add_argument("--listing", choices=("fc", "fa"), default="fc")
    ap.add_argument("--sbs", action="store_true", help="full side-by-side with slot names")
    ap.add_argument("--all", action="store_true", help="also list slots that map to themselves")
    ap.add_argument("-n", type=int, default=40, help="non-BP differences to print (default 40)")
    ap.add_argument("--json", type=Path, help="write the correspondence as JSON (under build/)")
    a = ap.parse_args(argv)
    modctx.check_arg(a.func, "FUNC")
    f = fnmod.get(a.func.replace(";", ":"))
    ctx = modctx.resolve(module=a.module, source=a.source, func=f["name"] if not a.module else None,
                         profile=a.profile, flags=a.flags, placements=a.placement)
    r = modctx.compile_text(ctx, extra_flags=["/Fc" if a.listing == "fc" else "/Fa"], keep=True)
    try:
        if not r.ok:
            print(r.log[-1500:])
            return 2
        ext = ".COD" if a.listing == "fc" else ".ASM"
        lp = next((p for p in Path(r.workdir).iterdir() if p.suffix.upper() == ext), None)
        listing = lp.read_text(encoding="latin1") if lp else ""
    finally:
        shutil.rmtree(r.workdir, ignore_errors=True)
    obj = modctx.read_obj(r.obj)
    row = dict(f)
    res, prec = modctx.bind_function(ctx, obj, row)
    if res is None:
        print(f"candidate has no public for {f['name']}")
        return 2
    d = search.diagnose(res, f["off"])
    cand, orig = d["cand"], d["orig"]
    lst = parse_listing(listing, prec["name"])
    M, R, other, pairs, where = correspond(cand, orig)
    out = report(f["name"], a.source, ctx, res, cand, orig, lst, M, R, other, pairs, where, a)
    if a.sbs:
        names = {}
        for off, lst_names in lst["names"].items():
            names[off - prec["offset"] + f["off"]] = lst_names
        print("side by side (candidate | original):")
        for x, y in pairs:
            nm = ",".join(n for _, n in names.get(x[0], [])) if x else ""
            left = (f"{x[0]:04X} {x[2]}" + (f"  ;{nm}" if nm else "")) if x else ""
            right = f"{y[0]:04X} {y[2]}" if y else ""
            mark = " " if x and y and x[1] == y[1] else "!"
            print(f"{mark} {left:<52} | {right}")
    if a.json:
        p = modctx.under_build(a.json)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(modctx.dumps(out))
    return 0 if res.exact else 1


if __name__ == "__main__":
    raise SystemExit(main())
