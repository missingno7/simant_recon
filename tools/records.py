"""OMF record breaks of a module build vs the record breaks the oracle's relocation order demands.

    python tools/records.py MODULE_OR_SOURCE [SOURCE] [--module KEY] [--profile P] [--flags ...]
                            [--placement SEG=SSSS:OOOO[:SIZE] ...] [--func NAME ...] [--all] [--obj]
                            [--records] [--lines] [--sim [FUNC]] [--plan] [--range R] [--period 52]
                            [--json OUT]

MODULE_OR_SOURCE is a module key (``root:1383``; ``root;1383`` from Git Bash is fine), which
uses the canonical source and the manifest options, or a draft path (module inferred from the
functions it defines, or ``--module``).  A second positional SOURCE checks a draft against the
named module.  The source is compiled once.

Why: RTLink groups a module's relocations by target symbol and keeps the object's FIXUPP order
inside each group; MSC writes the FIXUPPs of one LEDATA record in *descending* offset order.
So for two relocation sites a, b of one target group that appear in the oracle as a then b:

  * a < b  -> a and b lie in different records:  NEED   a record break q with a < q <= b
  * a > b  -> a and b lie in the same record:    FORBID any record break q with b < q <= a

Constraints come from consecutive sites of each group (candidate fixup keys, i.e. the same
target keys as tools/match.py; sites of functions whose candidate differs fall back to keys
read from the oracle bytes and are marked ``~``).  They are *within* one function or *cross*
function (the complete-TU order checked by modules.extent_reloc_order).

Output:
  * functions of the object (frame offsets) with the candidate length (``len!=`` means inner
    offsets do not correspond and the function's constraints are only reported, not checked);
  * ``--records``: the code LEDATA records (frame offset, object offset, length, cause:
    fn = function start, body = after the prologue, flush = line-number buffer flush, size =
    full record, other = label / CONST flush) and the LINNUM records (entries, counted index);
  * the constraints that the candidate violates (``--all``: every constraint; ``--obj`` adds
    the interval in object offsets, e.g. ``(0B72,0C0E] obj (0B70,0C0C]`` for root:1383, whose
    first function starts at frame offset 0002);
  * ``--lines``: line entries around each flush with their source lines;
  * ``--sim [FUNC]``: violations when d line entries (d = -R..R) are added before FUNC (default:
    file start).  Line entries do not change code; the flush every PERIOD (52) counted entries
    moves the flush record breaks (rules ZI-1/ZI-2);
  * ``--plan``: per flush, the admissible shift window and a greedy plan "add/remove N line
    entries between flush k-1 and flush k" with the violations that remain.

Examples (Git Bash: ``export MSYS_NO_PATHCONV=1``):

    python tools/records.py root:1383 --records
    python tools/records.py root:1383 build/workers/me/m1383.c --plan
    python tools/records.py S06:35F5 --func o06_35F5_14CC --func o06_35F5_1803 --all
    python tools/records.py build/workers/me/m35F5.c --sim o06_35F5_14CC

Model limits: the counted index of a LINNUM record's entries assumes that a record with
PERIOD-8..PERIOD stored entries was flushed by the count (entries merged at one offset are
counted but stored once); ``/Zd`` flushes at CONST words are shown as records but not
simulated.  Analysis only; acceptance is promote.py.
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import compiler  # noqa: E402
import exe as exemod  # noqa: E402
import modctx  # noqa: E402
from omf import OmfReader  # noqa: E402

LEDATA, LINNUM = 0xA0, 0x94   # OMF LEDATA16 / LINNUM16


@dataclass
class Rec:
    obj: int
    length: int
    frame: int | None
    cause: str = "other"
    func: str | None = None


@dataclass
class Entry:
    idx: int          # counted index (0-based) in the file's line-entry sequence
    line: int
    obj: int
    frame: int | None
    rec: int          # LINNUM record number


@dataclass
class Cons:
    kind: str         # NEED | FORBID
    lo: int
    hi: int
    key: str
    fa: str | None
    fb: str | None
    approx: bool      # key read from the oracle bytes and coarse (segment word): may merge groups
    okey: bool = False  # key read from the oracle bytes (candidate function differs)

    @property
    def scope(self) -> str:
        return "within" if self.fa == self.fb else "cross"

    def text(self, fm=None) -> str:
        where = self.fa if self.fa == self.fb else f"{self.fa}->{self.fb}"
        obj = ""
        if fm is not None:
            a, b = fm.to_obj(self.lo), fm.to_obj(self.hi)
            obj = f" obj ({a:04X},{b:04X}]" if a is not None and b is not None else " obj ?"
        return (f"{self.kind:<6} ({self.lo:04X},{self.hi:04X}]{obj} {'~' if self.approx else ' '}{self.key:<30} "
                f"{self.scope:<6} {where}")


def omf_stream(obj_bytes: bytes, code_index: int):
    """Code LEDATA records [(obj_off, len)] and LINNUM records [[(line, obj_off)]] in file order."""
    recs, lins = [], []
    for kind, body in OmfReader.records(obj_bytes):
        if kind == LEDATA:
            idx, at = OmfReader._index(body, 0)
            if idx == code_index:
                recs.append((int.from_bytes(body[at:at + 2], "little"), len(body) - at - 2))
        elif kind == LINNUM:
            _, at = OmfReader._index(body, 0)
            sidx, at = OmfReader._index(body, at)
            if sidx != code_index:
                continue
            ents = []
            while at + 4 <= len(body):
                ents.append((int.from_bytes(body[at:at + 2], "little"), int.from_bytes(body[at + 2:at + 4], "little")))
                at += 4
            lins.append(ents)
    return recs, lins


def oracle_key(x, unit: str, lin: int) -> str:
    """Target key read from the oracle bytes: a far call's target, else the segment word."""
    b = x.read(unit, lin - 3, 5)
    seg = int.from_bytes(b[3:5], "little")
    if b[0] == 0x9A:
        return f"far:{seg:04X}:{int.from_bytes(b[1:3], 'little'):04X}"
    return f"seg:{seg:04X}"


class Analysis:
    def __init__(self, ctx, period: int = 52):
        self.ctx, self.period = ctx, period
        r = modctx.compile_text(ctx)
        if not r.ok:
            raise modctx.HelperError("compile failed:\n" + r.log[-1500:])
        self.log = r.log
        self.obj = modctx.read_obj(r.obj)
        self.fm = modctx.FrameMap(ctx, self.obj)
        if self.fm.segment is None:
            raise modctx.HelperError(f"the candidate defines no function of {ctx.key}")
        cidx = modctx.code_segment_index(self.obj, self.fm.segment)
        raw_recs, lins = omf_stream(r.obj, cidx)
        self.pub_offs = {p["offset"] for p in self.obj.publics + getattr(self.obj, "local_publics", [])
                         if p["segment"] == self.fm.segment}
        # line entries with counted indices
        self.entries: list[Entry] = []
        start = 0
        for k, ents in enumerate(lins):
            for j, (ln, o) in enumerate(ents):
                self.entries.append(Entry(start + j, ln, o, self.fm.to_frame(o), k))
            n = len(ents)
            start += period if (k < len(lins) - 1 and period - 8 <= n <= period) else n
        self.flush_obj = {ents[0][1] for ents in lins[1:] if ents}
        self.recs = []
        prev = None
        for o, ln in raw_recs:
            rc = Rec(o, ln, self.fm.to_frame(o), func=self.fm.func_at_obj(o))
            if o in self.pub_offs:
                rc.cause = "fn"
            elif o in self.flush_obj:
                rc.cause = "flush"
            elif prev is not None and prev.cause == "fn" and o - prev.obj <= 0x20:
                rc.cause = "body"
            elif prev is not None and prev.length >= 0x3B0:
                rc.cause = "size"
            self.recs.append(rc)
            prev = rc
        self.fixed_breaks = sorted(rc.frame for rc in self.recs if rc.cause != "flush" and rc.frame is not None)
        self.flushes = [e for e in self.entries if e.idx > 0 and e.idx % period == 0]
        self.constraints = self._constraints()

    # -- oracle constraints -------------------------------------------------------------
    def _constraints(self) -> list[Cons]:
        ctx = self.ctx
        x = exemod.load()
        lo, hi = ctx.span
        base = ctx.seg * 16
        keys = {}
        self.results = {}
        for row in ctx.functions:
            res, _ = modctx.bind_function(ctx, self.obj, row)
            self.results[row["name"]] = res
            if res is None or not self.fm.exact_len.get(row["name"]):
                continue
            if sorted(res.relocs_expected) != sorted(res.relocs_candidate):
                continue
            keys.update(res.reloc_key)
        sites = [s * 16 + o for s, o in x.unit_relocs(ctx.unit) if base + lo <= s * 16 + o < base + hi]
        groups: dict = {}
        for lin in sites:
            k = keys.get(lin)
            approx = k is None
            if approx:
                k = oracle_key(x, ctx.unit, lin)
            groups.setdefault((k, approx), []).append(lin - base)
        out = []
        for (k, approx), offs in groups.items():
            for a, b in zip(offs, offs[1:]):
                fa, fb = self.func_at_frame(a), self.func_at_frame(b)
                coarse = approx and k.startswith("seg:")
                if a < b:
                    out.append(Cons("NEED", a, b, k, fa, fb, coarse, approx))
                else:
                    out.append(Cons("FORBID", b, a, k, fb, fa, coarse, approx))
        return sorted(out, key=lambda c: (c.lo, c.hi, c.kind))

    def func_at_frame(self, off: int) -> str | None:
        for r in self.ctx.functions:
            if r["off"] <= off < r["off"] + r["size"]:
                return r["name"]
        return None

    def checkable(self, c: Cons) -> bool:
        return bool(c.fa and c.fb and self.fm.exact_len.get(c.fa) and self.fm.exact_len.get(c.fb))

    def violated(self, c: Cons, breaks) -> bool:
        has = any(c.lo < q <= c.hi for q in breaks)
        return has != (c.kind == "NEED")

    def breaks_for(self, flush_frames) -> list[int]:
        return sorted(set(self.fixed_breaks) | {f for f in flush_frames if f is not None})

    def current_breaks(self) -> list[int]:
        return sorted(rc.frame for rc in self.recs if rc.frame is not None)

    def violations(self, breaks) -> list[Cons]:
        return [c for c in self.constraints if self.checkable(c) and self.violated(c, breaks)]

    # -- line-entry simulation ------------------------------------------------------------
    def flush_frames(self, shifts) -> list[int | None]:
        """Flush positions when flush k (1-based) sees cumulative shift shifts(k): the entry
        with original counted index period*k - shift becomes the first entry of a record."""
        by_idx = {e.idx: e for e in self.entries}
        last = self.entries[-1].idx if self.entries else -1
        out = []
        k = 1
        while True:
            s = shifts(k)
            i = self.period * k - s
            if i > last:
                break
            if i >= 0:
                e = by_idx.get(i) or next((e for e in self.entries if e.idx >= i), None)
                out.append(e.frame if e else None)
            k += 1
        return out

    def insert_point(self, func: str | None) -> int:
        if not func:
            return 0
        r = self.ctx.function(func)
        e = next((e for e in self.entries if e.frame is not None and e.frame >= r["off"]), None)
        return e.idx if e else 0

    def sim(self, p0: int, d: int) -> list[int | None]:
        """Flush frames after adding d (<0: removing) line entries just before entry p0."""
        by_idx = {e.idx: e for e in self.entries}
        last = self.entries[-1].idx if self.entries else -1
        out = []
        k = 1
        while self.period * k <= last + max(d, 0):
            n = self.period * k
            if n < min(p0, p0 + d):
                i = n
            elif d > 0 and p0 <= n < p0 + d:
                i = p0
            else:
                i = n - d
            if 0 <= i <= last:
                e = by_idx.get(i) or next((e for e in self.entries if e.idx >= i), None)
                out.append(e.frame if e else None)
            k += 1
        return out


def fmt_func(a: Analysis, name: str) -> str:
    r = next(r for r in a.ctx.functions if r["name"] == name)
    anchor = next((x for x in a.fm.anchors if x[2] == name), None)
    cl = anchor[3] if anchor else None
    if cl is None:
        st = "absent"
    else:
        st = "len ok" if a.fm.exact_len.get(name) else f"len!= ({cl})"
    res = a.results.get(name)
    ex = "" if res is None else ("EXACT" if res.exact else res.reloc_order if not [
        s for s in res.reasons if "relocation order" not in s] else "MISMATCH")
    return f"  {r['off']:04X}-{r['off'] + r['size']:04X} {name:<24} {r['size']:5d}  {st:<12} {ex}"


def line_text(a: Analysis) -> list[str]:
    try:
        prof = compiler.verify_profile(a.ctx.profile)
        return compiler.expand_includes(a.ctx.text, prof).replace("\r\n", "\n").split("\n")
    except Exception:  # noqa: BLE001 - listing aid only
        return a.ctx.text.split("\n")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("target", help="module key or source path")
    ap.add_argument("source", nargs="?", help="draft to check against the module named by TARGET")
    ap.add_argument("--module")
    ap.add_argument("--profile")
    ap.add_argument("--flags", nargs="*")
    ap.add_argument("--placement", action="append", default=[])
    ap.add_argument("--func", action="append", default=[], help="restrict constraint listing to function(s)")
    ap.add_argument("--all", action="store_true", help="list every constraint, not only violations")
    ap.add_argument("--records", action="store_true", help="list LEDATA/LINNUM records")
    ap.add_argument("--obj", action="store_true", help="also print constraint intervals in object offsets")
    ap.add_argument("--lines", action="store_true", help="line entries around each flush")
    ap.add_argument("--sim", nargs="?", const="", default=None, metavar="FUNC",
                    help="violations for d = -R..R line entries added before FUNC (default: file start)")
    ap.add_argument("--plan", action="store_true", help="per-flush windows and a greedy add/remove plan")
    ap.add_argument("--range", type=int, default=26, dest="rng")
    ap.add_argument("--period", type=int, default=52)
    ap.add_argument("--json", type=Path)
    a = ap.parse_args(argv)
    if a.source:
        ctx = modctx.resolve(module=a.module or a.target, source=a.source, profile=a.profile, flags=a.flags,
                             placements=a.placement)
    else:
        ctx = modctx.resolve(module=a.module, target=a.target, profile=a.profile, flags=a.flags,
                             placements=a.placement)
    an = Analysis(ctx, a.period)
    print(f"{ctx.key}  {ctx.source}  {ctx.profile} {' '.join(ctx.flags)}  span {ctx.span[0]:04X}-{ctx.span[1]:04X}"
          + ("  (extent)" if ctx.extent else ""))
    print("functions (frame offsets):")
    for r in ctx.functions:
        print(fmt_func(an, r["name"]))
    nfl = sum(1 for rc in an.recs if rc.cause == "flush")
    real = {rc.frame for rc in an.recs if rc.cause == "flush"}
    model = {e.frame for e in an.flushes}
    if real != model - {rc.frame for rc in an.recs if rc.cause != "flush"}:
        print(f"WARNING: the {an.period}-entry flush model does not reproduce this object's flush records "
              f"(object {sorted('%04X' % f for f in real if f is not None)}, model "
              f"{sorted('%04X' % f for f in model if f is not None)}); --sim/--plan are unreliable here")
    print(f"code records: {len(an.recs)} ({nfl} flush); line entries: {len(an.entries)} counted "
          f"{an.entries[-1].idx + 1 if an.entries else 0}, LINNUM records {len({e.rec for e in an.entries})}")
    if a.records:
        for i, rc in enumerate(an.recs):
            fr = f"{rc.frame:04X}" if rc.frame is not None else "----"
            print(f"  #{i:<3} frame {fr}  obj {rc.obj:04X}  len {rc.length:4X}  {rc.cause:<5} {rc.func or ''}")
        for k in sorted({e.rec for e in an.entries}):
            es = [e for e in an.entries if e.rec == k]
            print(f"  LINNUM {k}: {len(es)} entries, counted {es[0].idx}..{es[-1].idx}, "
                  f"lines {es[0].line}..{es[-1].line}, frame {es[0].frame or 0:04X}..{es[-1].frame or 0:04X}")
    breaks = an.current_breaks()
    cons = an.constraints
    if a.func:
        cons = [c for c in cons if c.fa in a.func or c.fb in a.func]
    nw = sum(1 for c in cons if c.scope == "within")
    viol = [c for c in cons if an.checkable(c) and an.violated(c, breaks)]
    unchecked = [c for c in cons if not an.checkable(c)]
    print(f"constraints: {len(cons)} ({sum(c.kind == 'NEED' for c in cons)} NEED, "
          f"{sum(c.kind == 'FORBID' for c in cons)} FORBID; {nw} within, {len(cons) - nw} cross; "
          f"{sum(c.okey for c in cons)} with oracle-byte keys, {sum(c.approx for c in cons)} of them coarse ~); "
          f"unchecked (len!=/absent): {len(unchecked)}")
    for c in cons:
        if a.all or c in viol:
            if not an.checkable(c):
                st = "unchecked"
            else:
                has = [q for q in breaks if c.lo < q <= c.hi]
                st = ("VIOLATED" if c in viol else "ok") + (f" breaks {' '.join('%04X' % q for q in has)}" if has else "")
            print(f"  {c.text(an.fm if a.obj else None):<90} {st}")
    print(f"violations: {len(viol)} ({sum(c.scope == 'within' for c in viol)} within, "
          f"{sum(c.scope == 'cross' for c in viol)} cross)")
    src = line_text(an) if (a.lines or a.plan) else []

    def where(fr):
        if fr is None:
            return "?"
        return f"{fr:04X} {an.func_at_frame(fr) or '?'}"

    if a.lines:
        for e in an.flushes:
            print(f"flush at counted entry {e.idx}: frame {where(e.frame)}")
            for f in an.entries:
                if e.idx - 2 <= f.idx <= e.idx + 1:
                    t = src[f.line - 1].strip()[:70] if 0 < f.line <= len(src) else ""
                    print(f"   {'*' if f.idx == e.idx else ' '}#{f.idx:<4} {f.frame or 0:04X} L{f.line}: {t}")
    out = {"module": ctx.key, "violations": [c.text(an.fm) for c in viol],
           "constraints": [dict(kind=c.kind, lo=c.lo, hi=c.hi, key=c.key, fa=c.fa, fb=c.fb, approx=c.approx,
                                scope=c.scope, checkable=an.checkable(c), violated=c in viol) for c in cons],
           "breaks": [dict(frame=rc.frame, obj=rc.obj, len=rc.length, cause=rc.cause) for rc in an.recs]}
    if a.sim is not None:
        p0 = an.insert_point(a.sim or None)
        print(f"simulation: d line entries added before counted entry {p0} ({a.sim or 'file start'}):")
        rows = []
        for d in range(-a.rng, a.rng + 1):
            v = an.violations(an.breaks_for(an.sim(p0, d)))
            rows.append((d, len(v)))
            fl = " ".join(sorted({c.fa or "?" for c in v}))[:80]
            print(f"  d={d:+3d}: {len(v):3d} violations  {fl}")
        out["sim"] = rows
    if a.plan:
        plan = make_plan(an, a.rng)
        print("plan (c_k = line entries added before flush k, cumulative; window/FIX = changes of c at this "
              "flush that add no / remove a violation near it):")
        prev = 0
        for k, (e, win, fix, c, fr) in enumerate(plan, 1):
            delta = c - prev
            print(f"  flush {k}: entry {e.idx if e else '?'} @ {where(e.frame if e else None)}  "
                  f"window {compress(win)}  FIX {compress(fix) or '-'}  -> c={c:+d} "
                  + (f"({'add' if delta > 0 else 'remove'} {abs(delta)} line entr{'y' if abs(delta) == 1 else 'ies'} "
                     + (f"between flush {k - 1} and flush {k}" if k > 1 else "before flush 1") + f") -> {where(fr)}"
                     if delta else "(unchanged)"))
            prev = c
        cs = [p[3] for p in plan]
        final = an.violations(an.breaks_for(an.flush_frames(lambda k: cs[k - 1] if k <= len(cs) else (cs[-1] if cs else 0))))
        print(f"plan result: {len(final)} violations (now {len(an.violations(an.current_breaks()))})")
        for c in final[:12]:
            print(f"    {c.text(an.fm if a.obj else None)}")
        out["plan"] = [{"flush": k, "shift": p[3]} for k, p in enumerate(plan, 1)]
    if a.json:
        p = modctx.under_build(a.json)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(modctx.dumps(out))
    return 0 if not viol else 1


def compress(ds) -> str:
    rng = []
    for d in sorted(ds):
        if rng and d == rng[-1][1] + 1:
            rng[-1][1] = d
        else:
            rng.append([d, d])
    return " ".join(f"{x:+d}..{y:+d}" if x != y else f"{x:+d}" for x, y in rng)


def make_plan(an: Analysis, rng: int):
    """Greedy: walk the flushes in order; flush k and all later ones take cumulative shift c
    (entries added between flush k-1 and flush k move every later flush too).  c is chosen to
    minimise the violations of the constraints that touch the region flush k can reach
    (entries period*k-rng-1 .. period*k+rng); ties go to the smallest change from c_{k-1}."""
    chosen: list[int] = []
    out = []
    by_idx = {e.idx: e for e in an.entries}
    frames = [e.frame for e in an.entries if e.frame is not None]
    for k in range(1, len(an.flushes) + 1):
        prev = chosen[-1] if chosen else 0
        n = an.period * k - prev
        lo_e = next((e for e in an.entries if e.idx >= n - rng - 1), None)
        hi_e = next((e for e in reversed(an.entries) if e.idx <= n + rng), None)
        f_lo = lo_e.frame if lo_e and lo_e.frame is not None else min(frames)
        f_hi = hi_e.frame if hi_e and hi_e.frame is not None else max(frames)
        local = [c for c in an.constraints if an.checkable(c) and c.lo < f_hi and c.hi > f_lo]

        def score(c):
            sh = chosen + [c]
            br = an.breaks_for(an.flush_frames(lambda j: sh[j - 1] if j <= len(sh) else c))
            return sum(1 for x in local if an.violated(x, br))

        cur = score(prev)
        cands = [(score(c), abs(c - prev), c) for c in range(prev - rng, prev + rng + 1)]
        best = min(cands)[2]
        win = [c - prev for s, _, c in cands if s <= cur]
        fix = [c - prev for s, _, c in cands if s < cur]
        chosen.append(best)
        tgt = by_idx.get(an.period * k - best)
        out.append((an.flushes[k - 1], win, fix, best, tgt.frame if tgt else None))
    return out


if __name__ == "__main__":
    raise SystemExit(main())
