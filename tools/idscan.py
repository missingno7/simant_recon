"""Identifier-count scan: insert N dummy identifiers at one position, report per-claim exactness.

    python tools/idscan.py SOURCE [--module KEY] [--top | --at TEXT | --before FUNC]
                           [--kind extern|typedef] [--min 0] [--max 16] [--funcs NAME ...]
                           [--claims-only] [--jobs N] [--profile P] [--flags ...] [--placement ...]

ANALYSIS TOOL.  MSC 6.00's code generation depends on the *number* of identifiers entered in
the symbol table before a function (externs, typedef names, struct tags, named prototype
parameters, locals of earlier functions; periodic modulo 17, see docs/codegen-rules.md,
"Symbol-table count").  This tool measures that sensitivity: for N = MIN..MAX it inserts N
dummy declarations (``extern int idscan_pad0;`` ...) and checks every claim of the module --
plus its in-place drafts and ``--funcs`` -- with the same strict check as promote.py (one
compile per N, in parallel, via tools/variants.py).

A dummy-declaration count that makes a function exact is *steering*, never a reconstruction.
Use the scan to learn how many identifiers are missing and roughly where, then find the
natural declarations that supply them (an ``#include``, a struct tag or typedef, named
prototype parameters, a missing extern, declarations in first-use order).  If no natural form
exists, a steered result may only be promoted with ``promote.py --steered "construct ->
decision it steers"``.  Never promote the ``idscan_pad`` declarations themselves.

Position (default: before the first line that starts with ``extern``):
  --top            at the start of the file
  --at TEXT        before the first occurrence of TEXT (``\\n`` = newline)
  --before FUNC    before the line that starts FUNC's definition

Output: one row per N (status characters as in variants.py), then per function the N values
at which it is exact.  Variant sources and results.json go to build/helpers/idscan/<run>/.

Examples (Git Bash: ``export MSYS_NO_PATHCONV=1``):

    python tools/idscan.py build/workers/me/m2505.c --module root:2505
    python tools/idscan.py src/root/m1383.c --top --max 20 --funcs GetNestDir
    python tools/idscan.py draft.c --before o12_384C_0B76 --kind typedef --jobs 8
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import modctx  # noqa: E402
import variants  # noqa: E402

PAD = {"extern": "extern int idscan_pad{i};\n", "typedef": "typedef int idscan_pad{i};\n"}


def position(text: str, top: bool = False, at: str | None = None, before: str | None = None) -> int:
    """Character offset where the dummy declarations go (always a line start except --at)."""
    if top:
        return 0
    if at is not None:
        at = at.replace("\\n", "\n")
        i = text.find(at)
        if i < 0:
            raise modctx.HelperError(f"--at text not found: {at[:60]!r}")
        return i
    if before is not None:
        m = re.search(r"^[^\n;{}#]*\b%s\s*\([^;{}]*\)\s*\{" % re.escape(before), text, re.M)
        if not m:
            raise modctx.HelperError(f"no definition of {before} found")
        return m.start()
    m = re.search(r"^extern\b", text, re.M)
    return m.start() if m else 0


def padded(text: str, pos: int, n: int, kind: str = "extern") -> str:
    return text[:pos] + "".join(PAD[kind].format(i=i) for i in range(n)) + text[pos:]


def exact_ranges(ns: list[int]) -> str:
    out = []
    for n in sorted(ns):
        if out and n == out[-1][1] + 1:
            out[-1][1] = n
        else:
            out.append([n, n])
    return " ".join(f"{a}..{b}" if a != b else f"{a}" for a, b in out) or "none"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source", type=Path)
    ap.add_argument("--module")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--top", action="store_true")
    g.add_argument("--at")
    g.add_argument("--before", metavar="FUNC")
    ap.add_argument("--kind", choices=sorted(PAD), default="extern")
    ap.add_argument("--min", type=int, default=0)
    ap.add_argument("--max", type=int, default=16)
    ap.add_argument("--funcs", nargs="*", default=[])
    ap.add_argument("--claims-only", action="store_true")
    ap.add_argument("--no-extent", action="store_true")
    ap.add_argument("--jobs", type=int, default=min(6, os.cpu_count() or 2))
    ap.add_argument("--profile")
    ap.add_argument("--flags", nargs="*")
    ap.add_argument("--placement", action="append", default=[])
    ap.add_argument("--out", type=Path)
    a = ap.parse_args(argv)
    if a.at:
        modctx.check_arg(a.at, "--at")
    ctx = modctx.resolve(module=a.module, source=a.source, profile=a.profile, flags=a.flags,
                         placements=a.placement)
    for n in a.funcs:
        ctx.function(n)          # fail fast on a function outside the module
    pos = position(ctx.text, a.top, a.at, a.before)
    line = ctx.text.count("\n", 0, pos) + 1
    vs = [(f"N={n}", padded(ctx.text, pos, n, a.kind), "") for n in range(a.min, a.max + 1)]
    d = variants.out_dir_for("idscan", a.out)
    print(f"idscan: {a.kind} dummies inserted before line {line} of {a.source} "
          "(analysis only: replace any steering by natural declarations or promote with --steered)")
    rows = variants.run(ctx, vs, extra_funcs=a.funcs, claims_only=a.claims_only, jobs=a.jobs,
                        extent=not a.no_extent, out_dir=d)
    variants.table(rows, ctx, quiet=True)
    names = []
    for r in rows:
        names += [n for n in r["claims"] if n not in names]
    print("exact at N:")
    for n in sorted(names, key=lambda n: next((r["off"] for r in ctx.functions if r["name"] == n), 0x10000)):
        ns = [a.min + i for i, r in enumerate(rows) if (r["result"].get("claims", {}).get(n) or {}).get("exact")]
        print(f"  {n:<24} {exact_ranges(ns)}")
    (d / "results.json").write_text(modctx.dumps({"module": ctx.key, "position_line": line, "kind": a.kind,
                                                  "variants": rows}))
    print(f"variant sources and results.json in {d}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
