"""Compile many source variants of one module in parallel and report per-claim exactness.

    python tools/variants.py SOURCE [SOURCE ...] [--module KEY] [options]
    python tools/variants.py --base BASE.c --spec VARIANTS.py|.json [--module KEY] [options]

options: [--profile P] [--flags /AL /Os ...] [--placement SEG=SSSS:OOOO[:SIZE] ...]
         [--funcs NAME ...] [--claims-only] [--no-extent] [--jobs N] [--show NAME ...]
         [--out DIR] [--quiet]

Every variant is compiled exactly once and checked with ``modules.verify_module`` -- the
same strict check promote.py runs -- against *all* claims of the module (manifest), plus
the module's functions that the variant defines outside its SCAFFOLD block (in-place drafts)
and ``--funcs``.  Private data placements and, for a complete TU, the extent (with its
cross-function relocation order) are checked too.  Nothing is promoted or written outside
the output directory (default ``build/helpers/variants/<run>/``), which receives every
variant source as ``NNN_<name>.c`` (the index keeps names unique on case-insensitive
Windows) and ``results.json``.

Variants from a spec: ``VARIANTS.py`` defines ``V = {name: [edit, ...]}`` (optionally
``MODULE``, ``FUNCS``); ``VARIANTS.json`` is ``{"variants": {name: [edit, ...]}, "module": ...,
"funcs": [...]}`` or just ``{name: [edit, ...]}``.  Edits apply in order to BASE:

    ["old text", "new text"]            replace the first occurrence (MISSING if absent)
    ["@@TOP@@", "text"]                 prepend text to the file
    ["@@RE@@", "pattern", "repl"]       re.sub over the whole file (MISSING if no match)

A variant named ``base`` (BASE unchanged) is always run first; the table marks claims whose
status differs from it.  Status characters: E exact, r bytes exact but within-group relocation
order pending (partial module), . mismatch, S claimed name inside SCAFFOLD, - not defined.

Examples (Git Bash: ``export MSYS_NO_PATHCONV=1``):

    python tools/variants.py build/workers/me/a.c build/workers/me/b.c --module root:218D
    python tools/variants.py --base src/root/m218D.c --spec build/workers/me/v.py --show f_218D_0656
    python tools/variants.py --base draft.c --spec v.json --module "S25;3BA4" --jobs 8

Warnings such as C4203 in a variant's compiler log are reported per variant.
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import datetime as dt
import json
import os
import re
import sys
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import compiler  # noqa: E402
import exe as exemod  # noqa: E402
import match  # noqa: E402
import modctx  # noqa: E402
import modules as modmod  # noqa: E402

_tls = threading.local()


class _LogTap:
    """Stands in for ``compiler`` inside tools/modules.py so the compiler log of each variant
    (warnings such as C4203) is visible; behaviour is unchanged."""

    def __getattr__(self, name):
        return getattr(compiler, name)

    def compile_c(self, *args, **kw):
        r = compiler.compile_c(*args, **kw)
        _tls.log = r.log
        return r

    def assemble(self, *args, **kw):
        r = compiler.assemble(*args, **kw)
        _tls.log = r.log
        return r


def apply_edits(text: str, edits) -> tuple[str | None, str]:
    """Apply spec edits; returns (text, "") or (None, reason)."""
    for e in edits:
        e = list(e)
        if e[0] == "@@TOP@@":
            text = e[1] + text
        elif e[0] == "@@RE@@":
            new, n = re.subn(e[1], e[2], text)
            if not n:
                return None, f"MISSING regex {e[1][:60]!r}"
            text = new
        else:
            old, new = e[0], e[1]
            if old not in text:
                return None, f"MISSING {old[:60]!r}"
            text = text.replace(old, new, 1)
    return text, ""


def load_spec(path: Path) -> dict:
    if not path.exists():
        raise modctx.HelperError(f"no such spec {path} (a Git Bash /d/... path is not converted under "
                                 "MSYS_NO_PATHCONV=1; use D:/... or a relative path)")
    if path.suffix.lower() == ".json":
        d = json.loads(path.read_text(encoding="latin1"))
        if "variants" not in d:
            d = {"variants": d}
        return {"variants": d["variants"], "module": d.get("module"), "funcs": d.get("funcs", [])}
    ns: dict = {}
    exec(compile(path.read_text(encoding="latin1"), str(path), "exec"), ns)  # the worker's own spec file
    if "V" not in ns:
        raise modctx.HelperError(f"{path} does not define V = {{name: [edits]}}")
    return {"variants": ns["V"], "module": ns.get("MODULE"), "funcs": list(ns.get("FUNCS", []))}


def safe_name(i: int, name: str) -> str:
    return f"{i:03d}_" + (re.sub(r"[^A-Za-z0-9_.-]+", "_", name)[:48] or "v")


def check_set(ctx, extra_funcs=(), claims_only: bool = False, text: str | None = None) -> list[dict]:
    """Claims to verify: manifest claims + in-place drafts defined in ``text`` + ``extra_funcs``."""
    claims = [dict(c) for c in ctx.claims]
    have = {c["name"] for c in claims}
    rows = {r["name"]: r for r in ctx.functions}
    wanted = list(extra_funcs)
    if not claims_only and text is not None:
        defined = set(modmod.FUNC_DEF_RE.findall(modmod.SCAFFOLD_RE.sub("", text)))
        wanted += [r["name"] for r in ctx.functions if r["name"] in defined]
    for n in wanted:
        if n in have:
            continue
        r = rows.get(n) or ctx.function(n)
        claims.append(modctx.claim_for(r))
        have.add(n)
    return sorted(claims, key=lambda c: (c["seg"], c["off"]))


def verify(ctx, text: str, claims: list[dict], extent: bool = True) -> dict:
    """One compile + modules.verify_module; adds the compiler warnings."""
    _tls.log = ""
    res = modmod.verify_module(text, ctx.module_dict(extent=extent), claims)
    res["warnings"] = [ln.strip() for ln in (getattr(_tls, "log", "") or "").splitlines()
                       if re.search(r"warning|C4203", ln, re.I)]
    return res


def run(ctx, variants: list[tuple[str, str | None, str]], extra_funcs=(), claims_only=False, jobs: int = 4,
        extent: bool = True, out_dir: Path | None = None) -> list[dict]:
    """variants: [(name, text or None, why-missing)] -> [{name, file, result, claims}] in order."""
    modmod.compiler = _LogTap()          # per-thread compiler logs (see _LogTap)
    exemod.load()
    match.symbols()
    if ctx.lang != "asm":
        compiler.verify_profile(ctx.profile)
    rows = []
    for i, (name, text, why) in enumerate(variants):
        f = None
        if out_dir is not None and text is not None:
            f = out_dir / (safe_name(i, name) + (".asm" if ctx.lang == "asm" else ".c"))
            f.write_bytes(text.encode("latin1"))
        rows.append({"name": name, "file": str(f) if f else None, "text": text, "why": why})

    def one(row):
        if row["text"] is None:
            return {"compile_ok": False, "log": row["why"], "claims": {}, "exact": False, "warnings": []}, []
        cl = []
        try:
            cl = check_set(ctx, extra_funcs, claims_only, row["text"])
            return verify(ctx, row["text"], cl, extent), cl
        except (Exception, SystemExit) as e:  # noqa: BLE001 - report per variant, keep the others
            return {"compile_ok": False, "log": f"{type(e).__name__}: {e}", "claims": {}, "exact": False,
                    "warnings": []}, cl

    with cf.ThreadPoolExecutor(max(1, jobs)) as ex:
        for row, (res, cl) in zip(rows, ex.map(one, rows)):
            row["result"], row["claims"] = res, [c["name"] for c in cl]
            del row["text"]
    return rows


def norm_warnings(ws) -> list[str]:
    """Warnings without line numbers, to compare variants with the base."""
    return [re.sub(r"\(\d+\)", "", w) for w in ws]


def table(rows: list[dict], ctx, show=(), quiet=False) -> None:
    names = []
    for r in rows:
        for n in r["claims"]:
            if n not in names:
                names.append(n)
    order = {r["name"]: (r["off"]) for r in ctx.functions}
    names.sort(key=lambda n: order.get(n, 0x10000))
    base = rows[0]["result"]["claims"] if rows else {}
    width = max([len(r["name"]) for r in rows] + [7])

    def chars(res):
        s = "".join(modctx.status_char(res["claims"].get(n)) for n in names)
        return " ".join(s[i:i + 10] for i in range(0, len(s), 10))

    print(f"{ctx.key}  {ctx.profile} {' '.join(ctx.flags)}  {len(names)} functions checked")
    print(f"{'variant':<{width}}  status (E exact, r order pending, . mismatch, S scaffold, - absent)")
    for r in rows:
        res = r["result"]
        if not res.get("compile_ok"):
            print(f"{r['name']:<{width}}  COMPILE/EDIT FAILED: {res.get('log', '')[-160:].strip()}")
            continue
        ne = sum(1 for n in names if (res["claims"].get(n) or {}).get("exact"))
        data = "".join("E" if d["exact"] else "." for d in res.get("data", {}).values())
        ext = res.get("extent")
        extent = "" if not ext else ("  extent " + ("EXACT" if ext["exact"] else "FAIL") + f" {ext.get('reloc_order')}")
        diff = [n for n in names if r is not rows[0] and
                modctx.status_char(res["claims"].get(n)) != modctx.status_char(base.get(n))]
        bw = set(norm_warnings(rows[0]["result"].get("warnings", []))) if r is not rows[0] else set()
        new = [w for w in res.get("warnings", [])
               if "C4203" in w or (r is not rows[0] and norm_warnings([w])[0] not in bw)]
        warn = (f"  warnings {len(res.get('warnings', []))}" if res.get("warnings") else "") +                (f": {'; '.join(new)[:140]}" if new else "")
        print(f"{r['name']:<{width}}  {chars(res)}  {ne}/{len(names)}" + (f"  data {data}" if data else "")
              + extent + (f"  changed: {' '.join(diff)}" if diff else "") + warn)
    if not quiet:
        print("functions: " + "  ".join(f"{i + 1}={n}" for i, n in enumerate(names)))
    for n in show:
        print(f"-- {n}")
        for r in rows:
            c = (r["result"].get("claims") or {}).get(n)
            if c is None:
                print(f"   {r['name']:<{width}}  (not checked)")
            else:
                print(f"   {r['name']:<{width}}  {'EXACT ' + c.get('reloc_order', '') if c['exact'] else '; '.join(c['reasons'])[:160]}")


def out_dir_for(tool: str, out: Path | None) -> Path:
    if out is not None:
        d = modctx.under_build(out)
    else:
        stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S") + f"-{os.getpid()}"
        d = modctx.BUILD / "helpers" / tool / stamp
    d.mkdir(parents=True, exist_ok=True)
    return d


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("sources", nargs="*", type=Path, help="complete variant files (one variant each)")
    ap.add_argument("--base", type=Path, help="base source for --spec")
    ap.add_argument("--spec", type=Path, help="VARIANTS.py (V = {...}) or .json")
    ap.add_argument("--module")
    ap.add_argument("--profile")
    ap.add_argument("--flags", nargs="*")
    ap.add_argument("--placement", action="append", default=[])
    ap.add_argument("--funcs", nargs="*", default=[], help="also check these (unclaimed) functions")
    ap.add_argument("--claims-only", action="store_true", help="only manifest claims and --funcs")
    ap.add_argument("--no-extent", action="store_true", help="skip the complete-TU extent check")
    ap.add_argument("--jobs", type=int, default=min(6, os.cpu_count() or 2))
    ap.add_argument("--show", action="append", default=[], help="print per-variant reasons for this function")
    ap.add_argument("--out", type=Path)
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args(argv)
    if bool(a.base) != bool(a.spec) or (not a.base and not a.sources):
        ap.error("give SOURCE files, or --base with --spec")
    variants = []
    spec = load_spec(a.spec) if a.spec else {"variants": {}, "module": None, "funcs": []}
    first = a.base or a.sources[0]
    ctx = modctx.resolve(module=a.module or spec["module"], source=first, profile=a.profile, flags=a.flags,
                         placements=a.placement)
    if a.base:
        variants.append(("base", ctx.text, ""))
        for name, edits in spec["variants"].items():
            t, why = apply_edits(ctx.text, edits)
            variants.append((str(name), t, why))
    else:
        for p in a.sources:
            modctx.check_arg(str(p), "source")
            variants.append((p.stem, p.read_text(encoding="latin1"), ""))
    for n in list(a.funcs) + list(spec["funcs"]):
        ctx.function(n)          # fail fast on a function outside the module
    d = out_dir_for("variants", a.out)
    rows = run(ctx, variants, extra_funcs=list(a.funcs) + list(spec["funcs"]), claims_only=a.claims_only,
               jobs=a.jobs, extent=not a.no_extent, out_dir=d)
    table(rows, ctx, a.show, a.quiet)
    (d / "results.json").write_text(json.dumps({"module": ctx.key, "profile": ctx.profile, "flags": ctx.flags,
                                                "variants": rows}, indent=1, default=str))
    print(f"variant sources and results.json in {d}")
    return 0 if any(r["result"].get("exact") for r in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
