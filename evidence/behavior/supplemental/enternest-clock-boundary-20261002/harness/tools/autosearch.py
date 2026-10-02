"""autosearch.py - rule-driven source-variant search for one open function (prototype tool).

    python tools/autosearch.py FUNC [--module KEY] [--base FILE] [--rules R,R] [--steer]
                         [--beam 6] [--depth 4] [--budget 1200] [--level-cap 400] [--jobs 16]
                         [--out DIR] [--promote] [--quiet]
    python tools/autosearch.py --list-rules

FUNC is an open function of a module (normally a SCAFFOLD draft in the canonical source).  The
base is the canonical module source with FUNC's SCAFFOLD block unwrapped in place (or --base,
a whole module file).  Moves are enumerated by the rule catalogue (rules.py; every rule is named
after its evidence in docs/codegen-rules.md / evidence/codegen), applied one at a time to the
whole module text, compiled in parallel and checked with modules.verify_module -- the check
promote.py runs -- against *every* claim of the module plus FUNC.

Score (lower is better): (not exact, differing instructions after alignment with branch targets
masked, differing bytes, |length difference|).  A variant that breaks another claim or a data
placement that the base keeps exact is rejected (never enters the beam).

Search: level 1 evaluates every single move of the base; later levels expand the beam (best
distinct-code states) with the moves that changed code at level 1 or are new at that state,
ranked by their level-1 score, until --depth, --budget or an exact result.

Nothing outside build/ is written unless --promote is given and the best variant is exact with
every module claim exact; then tools/promote.py runs (--verify-only first), the applied rules are
recorded as a source comment above the function, and --layout-inferred is added when only
declaration-category rules were applied.  Steering rules (--steer) are never promoted.
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import datetime as dt
import difflib
import hashlib
import json
import os
import re
import subprocess
import sys
import threading
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
SCRATCH = ROOT / "build" / "helpers" / "autosearch"

try:
    import capstone  # noqa: F401
except ImportError:
    sys.path.insert(0, "C:/tools/capstone-5.0.3")
from capstone import CS_ARCH_X86, CS_MODE_16, Cs  # noqa: E402

import compiler  # noqa: E402
import exe as exemod  # noqa: E402
import match  # noqa: E402
import modctx  # noqa: E402
import modules as modmod  # noqa: E402
import variants  # noqa: E402
from omf import OmfReader  # noqa: E402

import csrc as C  # noqa: E402
import srcrules as R  # noqa: E402

MD = Cs(CS_ARCH_X86, CS_MODE_16)
BRANCH_RE = re.compile(r"^(j\w+|loop\w*|jcxz|call)$")
_lock = threading.Lock()


# ------------------------------------------------------------------ base text


NL = chr(10)
SCAFF_BLOCK_RE = re.compile(r"/\*\s*SCAFFOLD BEGIN.*?\*/[ \t]*\n?(.*?)/\*\s*SCAFFOLD END\s*\*/[ \t]*\n?", re.S)


def unscaffold(text: str, fname: str) -> str:
    """Unwrap the SCAFFOLD block that defines fname (its body stays in place).  Other functions of
    the same block stay scaffolded, each in its own block, so a promotion never carries an
    unverified in-place draft."""
    for m in SCAFF_BLOCK_RE.finditer(text):
        inner = m.group(1)
        if fname not in modmod.FUNC_DEF_RE.findall(inner):
            continue
        try:
            fns = C.Source(inner).functions()
        except C.ParseError:
            fns = []
        out, pos = [], 0
        for fn in fns:
            if fn.name == fname:
                continue
            out.append(inner[pos:fn.head_s])
            out.append("/* SCAFFOLD BEGIN: (split from a shared block by autosearch) */" + NL)
            out.append(inner[fn.head_s:fn.e] + NL + "/* SCAFFOLD END */")
            pos = fn.e
        out.append(inner[pos:])
        return text[:m.start()] + "".join(out) + text[m.end():]
    return text


# ------------------------------------------------------------------ scoring


def insns(b: bytes):
    out = []
    for i in MD.disasm(b, 0):
        m = i.mnemonic
        out.append(m if BRANCH_RE.match(m) and not i.op_str.startswith(("word", "dword", "far")) else
                   f"{m} {i.op_str}")
    return out


def insn_distance(a: bytes, b: bytes) -> int:
    x, y = insns(a), insns(b)
    sm = difflib.SequenceMatcher(a=x, b=y, autojunk=False)
    return sum(max(i2 - i1, j2 - j1) for tag, i1, i2, j1, j2 in sm.get_opcodes() if tag != "equal")


def candidate_bytes(obj_bytes: bytes, row: dict, placements: dict) -> bytes | None:
    """The candidate function's full bytes (fixups bound as in match.Binder)."""
    obj = OmfReader(communals=True).read(obj_bytes)
    pub, prec = match.public_in(obj, row["name"])
    if prec is None:
        return None
    seg = prec["segment"]
    offs = sorted(p["offset"] for p in obj.publics + getattr(obj, "local_publics", []) if p["segment"] == seg)
    nxt = min((o for o in offs if o > prec["offset"]), default=len(obj.segments.get(seg, b"")))
    size = nxt - prec["offset"]
    t = match.Target(row["unit"], row["seg"], row["off"], size)
    try:
        res = match.Binder(t, obj, seg, pub, {k: {"seg": v["seg"], "off": v["off"]} for k, v in placements.items()}).bind()
    except Exception:  # noqa: BLE001 - reading past the unit end for a long candidate
        return bytes(obj.segments[seg][prec["offset"]:nxt])
    return res.candidate


class Evaluator:
    def __init__(self, ctx, fname: str, jobs: int, cache_dir: Path):
        self.ctx = ctx
        self.fname = fname
        self.jobs = jobs
        self.row = ctx.function(fname)
        x = exemod.load()
        self.orig = x.read(self.row["unit"], self.row["seg"] * 16 + self.row["off"], self.row["size"])
        self.claims = variants.check_set(ctx, [fname], claims_only=True)
        self.base_ok = None            # claim names exact in the base
        self.base_data = None
        cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = cache_dir / f"{ctx.key.replace(':', '_').replace('@', '_')}_{fname}.json"
        self.cache = {}
        if self.cache_file.exists():
            try:
                self.cache = json.loads(self.cache_file.read_text())
            except ValueError:
                self.cache = {}
        self.compiles = 0
        compiler.verify_profile(ctx.profile)
        exemod.load()
        match.symbols()
        # A cached verdict depends on the registries and the gate as well as the C text.
        # Invalidate it after a reframe, rename, toolchain change or acceptance-rule change.
        h = hashlib.sha256(self.orig)
        for rel in ("layout/functions.json", "layout/symbols.json", "layout/manifest.json",
                    "layout/oracle.lock.json", "layout/toolchain.json", "tools/modules.py",
                    "tools/match.py", "tools/compiler.py", "tools/omf.py", "tools/modctx.py"):
            h.update((ROOT / rel).read_bytes())
        self.cache_fingerprint = h.hexdigest()

    def key(self, text: str) -> str:
        h = hashlib.sha256()
        h.update(text.encode("latin1", "replace"))
        h.update(json.dumps([self.ctx.module_dict(extent=True), self.claims,
                             self.cache_fingerprint], sort_keys=True).encode())
        return h.hexdigest()

    def one(self, text: str) -> dict:
        k = self.key(text)
        with _lock:
            if k in self.cache:
                return self.cache[k]
        col = {}
        try:
            res = modmod.verify_module(text, self.ctx.module_dict(extent=True), self.claims, collect=col)
        except (Exception, SystemExit) as e:  # noqa: BLE001
            res = {"compile_ok": False, "log": f"{type(e).__name__}: {e}", "claims": {}}
        out = {"compile_ok": res.get("compile_ok", False), "claims": {}, "data": {}}
        if out["compile_ok"]:
            out["claims"] = {n: bool(r.get("exact")) for n, r in res["claims"].items()}
            out["order"] = {n: r.get("reloc_order") for n, r in res["claims"].items()}
            out["data"] = {n: bool(r.get("exact")) for n, r in res.get("data", {}).items()}
            out["module_reasons"] = res.get("module_reasons", [])
            t = res["claims"].get(self.fname, {})
            out["reasons"] = t.get("reasons", [])
            out["exact"] = bool(t.get("exact"))
            out["all_exact"] = bool(res.get("exact"))
            cb = candidate_bytes(col["object"], self.row, self.ctx.placements) if "object" in col else None
            if cb is None:
                out["score"] = [1, 10 ** 6, 10 ** 6, 10 ** 6]
                out["fhash"] = None
            else:
                n = min(len(cb), len(self.orig))
                bd = sum(1 for i in range(n) if cb[i] != self.orig[i]) + abs(len(cb) - len(self.orig))
                out["score"] = [0 if out["exact"] else 1, insn_distance(cb, self.orig), bd,
                                abs(len(cb) - len(self.orig))]
                out["fhash"] = hashlib.sha256(cb).hexdigest()[:16]
                out["length"] = len(cb)
        else:
            out["log"] = res.get("log", "")[-300:]
        with _lock:
            self.cache[k] = out
            self.compiles += 1
        return out

    def many(self, texts: list[str]) -> list[dict]:
        with cf.ThreadPoolExecutor(max(1, self.jobs)) as ex:
            return list(ex.map(self.one, texts))

    def save(self):
        with _lock:
            self.cache_file.write_text(json.dumps(self.cache))

    def set_base(self, r: dict):
        # Ownership comes from the manifest, never from a possibly stale draft's verdict.
        self.base_ok = {c['name'] for c in self.ctx.claims if c['name'] != self.fname}
        self.base_ok |= {n for n, ok in r["claims"].items() if ok and n != self.fname}
        self.base_data = set(r["data"])

    def regressions(self, r: dict) -> list[str]:
        if not r.get("compile_ok"):
            return ["compile failed"]
        out = [n for n in self.base_ok if not r["claims"].get(n)]
        out += ["data " + n for n in self.base_data if not r["data"].get(n)]
        return out


# ------------------------------------------------------------------ search


class State:
    def __init__(self, text: str, path: list, res: dict):
        self.text = text
        self.path = path          # [(rule, site, key)]
        self.res = res

    @property
    def score(self):
        return tuple(self.res.get("score", [1, 10 ** 6, 10 ** 6, 10 ** 6]))


def fmt_score(s) -> str:
    if s is None:
        return "-"
    return ("EXACT" if s[0] == 0 else f"insn {s[1]} bytes {s[2]} len {'+' if s[3] else ''}{s[3]}")


def pick_neutral(states, limit):
    """Round robin across rules: distinct source contexts can emit identical code."""
    groups = {}
    for state in sorted(states, key=lambda s: len(s.path)):
        groups.setdefault(state.path[-1][0], []).append(state)
    rules = sorted(groups, key=lambda r: (R.RULES[r].category != 'decl', r))
    picked = []
    for index in range(max((len(g) for g in groups.values()), default=0)):
        for rule in rules:
            if len(picked) >= limit:
                return picked
            if index < len(groups[rule]):
                picked.append(groups[rule][index])
    return picked


def search(ev: Evaluator, base_text: str, rule_ids, beam: int, depth: int, budget: int, level_cap: int,
           log=print, neutral_beam: int = 4) -> dict:
    fname = ev.fname
    base_res = ev.one(base_text)
    if not base_res.get("compile_ok"):
        return {"function": fname, "error": "base does not compile: " + base_res.get("log", "")}
    ev.set_base(base_res)
    base_losses = ev.regressions(base_res)
    if base_losses:
        return {"function": fname, "error": "base fails accepted ownership checks: " + ', '.join(base_losses),
                "base_res": base_res, "base_losses": base_losses}
    base = State(base_text, [], base_res)
    log(f"base: {fmt_score(base.score)}  {'; '.join(base_res.get('reasons', []))[:140]}")
    seen_text = {ev.key(base_text)}
    seen_code = {base_res.get("fhash")}
    best = base
    tried = []                 # (level, rule, site, score or None, regress)
    rule_stats = {}
    move_rank = {}             # key -> level-1 score (rank order for later levels)
    effective = set()
    frontier = [base]
    evals = 0
    for level in range(1, depth + 1):
        pool = []
        for si, st in enumerate(frontier):
            try:
                moves = R.enumerate_moves(st.text, fname, rule_ids)
            except (C.ParseError, KeyError) as e:
                log(f"  enumerate failed: {e}")
                continue
            per_rule = {}
            for mv in moves:
                if any(mv.key == p[2] for p in st.path):
                    continue
                if level == 1:
                    n = per_rule.get(mv.rule, 0)
                    per_rule[mv.rule] = n + 1
                    pool.append(((n, 0, 0), st, mv))          # round robin over rules
                else:
                    if mv.key in effective:
                        cls, rank = 0, move_rank.get(mv.key, (1, 0, 0, 0))
                    elif mv.key not in move_rank:
                        cls, rank = 1, (0, 0, 0, 0)
                    else:
                        cls, rank = 2, move_rank[mv.key]
                    pool.append(((cls, si, rank), st, mv))
        pool.sort(key=lambda c: c[0])
        cand = []
        cap = min(level_cap, budget - evals)
        for _, st, mv in pool:
            if len(cand) >= cap:
                break
            try:
                t = R.apply_move(st.text, mv)
            except ValueError:
                continue
            k = ev.key(t)
            if k in seen_text:
                continue
            seen_text.add(k)
            if not R.valid_variant(t, fname):
                continue
            cand.append((st, mv, t))
        if not cand:
            break
        log(f"level {level}: {len(cand)} variants from {len(frontier)} state(s)")
        results = ev.many([c[2] for c in cand])
        evals += len(cand)
        ev.save()
        nxt, neutral = [], []
        for (st, mv, t), r in zip(cand, results):
            reg = ev.regressions(r)
            sc = tuple(r["score"]) if r.get("compile_ok") and "score" in r else None
            tried.append((level, mv.rule, mv.site, sc, reg[:3]))
            rs = rule_stats.setdefault(mv.rule, {"tried": 0, "changed": 0, "better": 0, "regress": 0, "fail": 0})
            rs["tried"] += 1
            if sc is None:
                rs["fail"] += 1
                continue
            if reg:
                rs["regress"] += 1
                continue
            if r.get("fhash") != st.res.get("fhash"):
                rs["changed"] += 1
                if sc < st.score:
                    rs["better"] += 1
            if level == 1:
                move_rank[mv.key] = sc
                if r.get("fhash") != base_res.get("fhash"):
                    effective.add(mv.key)
            else:
                if r.get("fhash") != st.res.get("fhash"):
                    effective.add(mv.key)
                move_rank.setdefault(mv.key, sc)
            ns = State(t, st.path + [(mv.rule, mv.site, mv.key)], r)
            if sc < best.score:
                best = ns
                log(f"  better: {fmt_score(sc)}  via {' + '.join(p[0] + '[' + p[1][:40] + ']' for p in ns.path)}")
            if r.get("fhash") not in seen_code:
                seen_code.add(r.get("fhash"))
                nxt.append(ns)
            elif r.get("fhash") == st.res.get("fhash"):
                neutral.append(ns)
        if best.score[0] == 0:
            break
        # beam: best distinct-code states (ties broken by shorter paths)
        pool = sorted(nxt + frontier, key=lambda s: (s.score, len(s.path)))
        frontier, fh = [], set()
        for s in pool:
            if s.res.get("fhash") in fh:
                continue
            fh.add(s.res.get("fhash"))
            frontier.append(s)
            if len(frontier) >= beam:
                break
        # plus a few code-neutral states (declaration order, prototype spelling, statement forms):
        # their effect can appear only in combination with a later move
        if neutral_beam:
            frontier += pick_neutral(neutral, neutral_beam)
        if evals >= budget:
            break
    return {"function": fname, "module": ev.ctx.key, "base_score": list(base.score), "best_score": list(best.score),
            "best_path": best.path, "best_text": best.text, "best_res": best.res, "base_res": base_res,
            "evals": evals, "compiles": ev.compiles, "code_identities": len(seen_code),
            "neutral_beam": neutral_beam, "rule_stats": rule_stats, "tried": tried}


# ------------------------------------------------------------------ promotion


def annotate(text: str, fname: str, path) -> str:
    """Record the applied rules in a comment directly above the function definition."""
    src = C.Source(text)
    fn = src.function(fname)
    rules_txt = ", ".join(dict.fromkeys(p[0] for p in path))
    note = f"/* autosearch: exact after rules {rules_txt} */\n"
    b = text.rfind("\n", 0, fn.head_s) + 1
    return text[:b] + note + text[b:]


def promote(result: dict, out_dir: Path, log=print, dry_run: bool = False) -> bool:
    fname, key = result["function"], result["module"]
    cats = {R.RULES[p[0]].category for p in result["best_path"]}
    if "steer" in cats:
        log("not promoted: a steering rule was applied")
        return False
    text = annotate(result["best_text"], fname, result["best_path"])
    f = out_dir / f"promote_{fname}.c"
    f.write_text(text, encoding="latin1", newline="\n")
    env = dict(os.environ, MSYS_NO_PATHCONV="1", MSYS2_ARG_CONV_EXCL="*")
    cmd = [sys.executable, str(ROOT / "tools" / "promote.py"), str(f), "--module", key, "--claim", fname]
    if cats == {"decl"}:
        steps = " + ".join(f"{p[0]}[{p[1][:50]}]" for p in result["best_path"])
        cmd += ["--layout-inferred", f"{fname}=autosearch: declaration-only rules {steps}"]
    # a promotion that leaves no scaffold completes the module: claim it as one TU when the
    # extent (the object's function-table span) verifies
    if not modmod.scaffold_names(text):
        ctx = modctx.resolve(module=key)
        if not ctx.extent:
            lo, hi = ctx.span
            ext = f"{ctx.seg * 16 + lo:05X}:{ctx.seg * 16 + hi:05X}"
            r = subprocess.run(cmd + ["--extent", ext, "--verify-only"], cwd=ROOT, capture_output=True, text=True,
                               env=env)
            if r.returncode == 0:
                cmd += ["--extent", ext]
                log(f"complete TU: --extent {ext}")
    r = subprocess.run(cmd + ["--verify-only"], cwd=ROOT, capture_output=True, text=True, env=env)
    log(r.stdout[-1500:] + r.stderr[-500:])
    if r.returncode != 0:
        return False
    if dry_run:
        return True
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, env=env)
    log(r.stdout[-800:] + r.stderr[-500:])
    return r.returncode == 0


# ------------------------------------------------------------------ CLI


def run_one(fname: str, module: str | None = None, base: Path | None = None, rule_ids=None, beam=6, depth=4,
            budget=1200, level_cap=400, jobs=16, out: Path | None = None, do_promote=False, quiet=False,
            neutral_beam=4) -> dict:
    ctx = modctx.resolve(module=module, func=fname if module is None else None)
    text = base.read_text(encoding="latin1") if base else unscaffold(ctx.text, fname)
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    out = out or (SCRATCH / "runs" / f"{fname}-{stamp}")
    out.mkdir(parents=True, exist_ok=True)
    logf = (out / "log.txt").open("w")

    def log(msg):
        logf.write(msg + "\n")
        logf.flush()
        if not quiet:
            print(msg, flush=True)

    log(f"{fname} in {ctx.key} ({ctx.profile} {' '.join(ctx.flags)}), rules: {','.join(rule_ids or R.DEFAULT_RULES)}")
    ev = Evaluator(ctx, fname, jobs, SCRATCH / "cache")
    res = search(ev, text, rule_ids or R.DEFAULT_RULES, beam, depth, budget, level_cap, log, neutral_beam)
    if "error" in res:
        log(res["error"])
        (out / "result.json").write_text(json.dumps(res, indent=1, default=str))
        logf.close()
        return res
    (out / "best.c").write_text(res["best_text"], encoding="latin1", newline="\n")
    (out / "base.c").write_text(text, encoding="latin1", newline="\n")
    diff = "".join(difflib.unified_diff(text.splitlines(True), res["best_text"].splitlines(True), "base.c", "best.c"))
    (out / "best.diff").write_text(diff)
    summary = {k: v for k, v in res.items() if k not in ("best_text", "tried")}
    summary["tried_count"] = len(res["tried"])
    (out / "result.json").write_text(json.dumps(summary, indent=1, default=str))
    (out / "tried.json").write_text(json.dumps(res["tried"], default=str))
    log(f"best: {fmt_score(res['best_score'])} (base {fmt_score(res['base_score'])}) after {res['evals']} variants: "
        + (" + ".join(f"{p[0]}[{p[1][:50]}]" for p in res["best_path"]) or "(base)"))
    res["promoted"] = False
    if do_promote and res["best_score"][0] == 0:
        if res["best_res"].get("all_exact"):
            res["promoted"] = promote(res, out, log)
        else:
            log("exact but not every module check is exact: not promoted")
    res["out"] = str(out)
    logf.close()
    return res


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("func", nargs="?")
    ap.add_argument("--module")
    ap.add_argument("--base", type=Path)
    ap.add_argument("--rules", help="comma-separated rule ids (default: all non-steering rules)")
    ap.add_argument("--steer", action="store_true", help="also use steering rules (never promoted)")
    ap.add_argument("--beam", type=int, default=6)
    ap.add_argument("--neutral-beam", type=int, default=4,
                    help="source contexts retained despite identical emitted code (0 disables)")
    ap.add_argument("--depth", type=int, default=4)
    ap.add_argument("--budget", type=int, default=1200)
    ap.add_argument("--level-cap", type=int, default=400)
    ap.add_argument("--jobs", type=int, default=16)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--promote", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--list-rules", action="store_true")
    a = ap.parse_args(argv)
    if a.neutral_beam < 0:
        ap.error('--neutral-beam must be nonnegative')
    if a.list_rules:
        for r in R.RULES.values():
            print(f"{r.id:12s} {r.category:5s} {r.doc}\n{'':18s} evidence: {r.evidence}")
        return 0
    if not a.func:
        ap.error("FUNC required")
    ids = a.rules.split(",") if a.rules else list(R.DEFAULT_RULES)
    if a.steer:
        ids += [r for r in R.RULES if R.RULES[r].category == "steer" and r not in ids]
    res = run_one(a.func, a.module, a.base, ids, a.beam, a.depth, a.budget, a.level_cap, a.jobs, a.out,
                  a.promote, a.quiet, a.neutral_beam)
    return 0 if res.get("best_score", [1])[0] == 0 else 1


# ------------------------------------------------------------------ --all (every open function)

# per-function base overrides (a draft that is not a plain SCAFFOLD block of the canonical source)
BASES = {"DoAntMoveY": SCRATCH / "bases" / "S25_3BA4_DoAntMoveY.c"}


def targets(skip, only):
    manifest = json.loads((ROOT / "layout" / "manifest.json").read_text())
    man = manifest["modules"]
    owned = {c["name"] for m in man.values() for c in m["claims"]}
    out = []
    for k, m in sorted(man.items()):
        if k in skip or m.get("lang", "c") != "c" or m["unit"] == modmod.DATA_UNIT:
            continue
        definitions = set(modmod.FUNC_DEF_RE.findall((ROOT / m["source"]).read_text(encoding="latin1")))
        rows = modctx.module_rows(m["unit"], m["seg"], m.get("origin"), manifest)
        offsets = {r["off"] for r in rows}
        candidates = []
        for f in sorted(definitions - owned):
            try:
                row = modctx.fnmod.get(f)
            except SystemExit:
                continue
            if (row["unit"], row["seg"]) != (m["unit"], m["seg"]) or row["off"] not in offsets:
                continue
            # Source may still use a registered alias (S09's o09_35F5_03C6/FileSelect).
            # Keep that spelling: a registry's preferred name need not define the public.
            if only and f not in only and modctx.fnmod.name_of(row["unit"], row["seg"], row["off"]) not in only:
                continue
            candidates.append((row["off"], f))
        out += [(k, f) for _, f in sorted(candidates)]
    return out


def continuation_base(entry: dict, results_file: Path) -> Path | None:
    """Locate a previous best draft, including artifacts moved from build/ into work/."""
    if not (entry.get("out") and entry.get("best") and entry.get("base")
            and entry["best"] <= entry["base"]):
        return None
    old = Path(entry["out"])
    for p in (old / "best.c", results_file.parent / "runs" / old.name / "best.c"):
        if p.is_file():
            return p
    return None


def run_all_main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-module", action="append", default=[],
                    help="explicitly exclude a module; --all otherwise includes every open draft")
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--budget", type=int, default=800)
    ap.add_argument("--depth", type=int, default=4)
    ap.add_argument("--beam", type=int, default=6)
    ap.add_argument("--neutral-beam", type=int, default=4,
                    help="source contexts retained despite identical emitted code (0 disables)")
    ap.add_argument("--level-cap", type=int, default=300)
    ap.add_argument("--jobs", type=int, default=16)
    ap.add_argument("--promote", action="store_true")
    ap.add_argument("--steer", action="store_true")
    ap.add_argument("--table", type=Path, default=SCRATCH / "results.md")
    ap.add_argument("--continue-from", type=Path,
                    help="results .json of an earlier pass: start each function from its best.c there")
    a = ap.parse_args(argv)
    if a.neutral_beam < 0:
        ap.error('--neutral-beam must be nonnegative')
    ids = list(R.DEFAULT_RULES)
    if a.steer:
        ids += [r for r in R.RULES if R.RULES[r].category == "steer"]
    rows = []
    jfile = a.table.with_suffix(".json")
    jfile.parent.mkdir(parents=True, exist_ok=True)
    prev = json.loads(jfile.read_text()) if jfile.exists() else {}
    earlier = json.loads(a.continue_from.read_text()) if a.continue_from else {}
    for key, f in targets(a.skip_module, a.only):
        print(f"=== {key} {f}", flush=True)
        base = BASES.get(f) if BASES.get(f, Path("-")).exists() else None
        e = earlier.get(f, {})
        continued = continuation_base(e, a.continue_from) if a.continue_from else None
        if continued is not None:
            base = continued
            print(f"  continuing from {base}")
        elif e.get("out") and e.get("best", [1]) <= e.get("base", [0]):
            print("  previous best draft missing; using the current module draft")
        try:
            res = run_one(f, key, base, ids, a.beam,
                            a.depth, a.budget, a.level_cap, a.jobs, None, a.promote, quiet=True,
                            neutral_beam=a.neutral_beam)
        except (Exception, SystemExit) as e:  # noqa: BLE001
            print(f"  FAILED: {type(e).__name__}: {e}")
            prev[f] = {"module": key, "error": f"{type(e).__name__}: {e}"}
            continue
        if "error" in res:
            print("  " + res["error"][:200])
            prev[f] = {"module": key, "error": res["error"][:300]}
            continue
        row = {"module": key, "base": res["base_score"], "best": res["best_score"],
               "path": [p[:2] for p in res["best_path"]], "evals": res["evals"],
               "reasons": res["best_res"].get("reasons", []), "base_reasons": res["base_res"].get("reasons", []),
               "rule_stats": res["rule_stats"], "promoted": res.get("promoted"), "out": res.get("out"),
               "time": dt.datetime.now().isoformat(timespec="seconds")}
        prev[f] = row
        print(f"  base {fmt_score(res['base_score'])} -> best {fmt_score(res['best_score'])} "
              f"({res['evals']} variants) {' + '.join(p[0] for p in res['best_path'])}", flush=True)
        jfile.write_text(json.dumps(prev, indent=1))
        write_table(prev, a.table)
    jfile.write_text(json.dumps(prev, indent=1))
    write_table(prev, a.table)


def write_table(rows: dict, path: Path):
    L = ["# autosearch results", "",
         "Score = differing instructions (branch targets masked) / differing bytes / length difference.", "",
         "| module | function | base | best | variants | rules applied (best path) | rules that changed code (changed/tried) |",
         "|---|---|---|---|---|---|---|"]
    for f, r in sorted(rows.items(), key=lambda kv: (kv[1].get("module", ""), kv[0])):
        if "error" in r:
            L.append(f"| {r['module']} | {f} | error | {r['error'][:80]} | | | |")
            continue
        path_txt = "<br>".join(f"{p[0]} `{p[1][:60]}`" for p in r["path"]) or "(none better)"
        stats = ", ".join(f"{k} {v['changed']}/{v['tried']}" for k, v in sorted(r["rule_stats"].items())
                          if v["changed"] or v["better"])
        L.append(f"| {r['module']} | {f} | {fmt_score(r['base'])} | {fmt_score(r['best'])}"
                 f"{' PROMOTED' if r.get('promoted') else ''} | {r['evals']} | {path_txt} | {stats} |")
    path.write_text("\n".join(L) + "\n")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--all":
        raise SystemExit(run_all_main(sys.argv[2:]))
    raise SystemExit(main())
