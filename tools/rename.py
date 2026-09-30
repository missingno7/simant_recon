"""Rename symbols across canonical sources, manifest and registry (supervisor tool).

    python tools/rename.py OLD=NEW [OLD=NEW ...] --why "evidence" [--verify-only]
    python tools/rename.py --batch renames.json [--verify-only]     # [{"old","new","why"}, ...]

Identifiers are replaced as whole words in every canonical module file (src/**).  Every
module whose source changes is recompiled and must still be exact (names can influence
MSC's symbol-table state, so a rename is re-proven, not assumed).  Only then are the
sources, layout/manifest.json (claim names, source hashes), layout/symbols.json (with
rename history) and evidence/promotions.jsonl updated, under the canonical lock.
Apply renames between worker waves: in-flight drafts use the old names.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import modules as modmod  # noqa: E402
import symbols as symmod  # noqa: E402
from lockfile import CanonicalLock  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,30}$")


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("pairs", nargs="*")
    ap.add_argument("--why", default=None)
    ap.add_argument("--batch", type=Path)
    ap.add_argument("--verify-only", action="store_true")
    ap.add_argument("--skip-module", action="append", default=[],
                    help="UNIT:SEG modules to leave on the old names (e.g. being edited by a worker)")
    a = ap.parse_args()
    ren = []
    if a.batch:
        ren = [(r["old"], r["new"], r["why"]) for r in json.loads(a.batch.read_text())]
    for p in a.pairs:
        o, n = p.split("=")
        if not a.why:
            raise SystemExit("--why is required")
        ren.append((o, n, a.why))
    with CanonicalLock():
        syms = symmod.load()
        taken = set(syms["code"]) | set(syms["data"])
        olds = {o for o, _, _ in ren}
        for o, n, _ in ren:
            if not IDENT.match(n):
                raise SystemExit(f"bad identifier {n}")
            if o not in syms["code"] and o not in syms["data"]:
                raise SystemExit(f"{o} is not registered")
            if (syms["code"].get(o) or syms["data"].get(o) or {}).get("alias_of"):
                raise SystemExit(f"{o} is already an alias")
            if n in taken and n not in olds:
                raise SystemExit(f"{n} already registered")
        man = modmod.load_manifest()
        pat = {o: re.compile(r"\b" + re.escape(o) + r"\b") for o, _, _ in ren}
        changed = {}
        for key, m in man["modules"].items():
            path = ROOT / m["source"]
            text = path.read_text(encoding="latin1")
            new = text
            for o, n, _ in ren:
                new = pat[o].sub(n, new)
            if new != text:
                changed[key] = new
        # re-prove every changed module.  Identifier names can change MSC's code generation
        # (symbol-table hashing), so a module whose rewrite is not exact keeps the old
        # names: they stay registered as aliases of the new ones.
        mapping = {o: n for o, n, _ in ren}
        # bind the new names to the old addresses *before* re-proving (the registry is only
        # rewritten after every module verifies)
        import match as matchmod
        base = dict(matchmod.symbols())
        for o, n, _ in ren:
            rec = base.get("_" + o)
            if rec is not None:
                base["_" + n] = rec
        matchmod.symbols = lambda: base
        kept = {}
        for key in list(changed):
            if key in a.skip_module:
                kept[key] = "skipped (worker module)"
                del changed[key]
                continue
            text = changed[key]
            m = man["modules"][key]
            claims = [dict(c, name=mapping.get(c["name"], c["name"])) for c in m["claims"]]
            res = modmod.verify_module(text, m, claims)
            bad = [n for n, c in res["claims"].items() if not c["exact"]]
            if not res["exact"]:
                kept[key] = f"keeps old names: rename changes code of {bad[:5] or 'data/extent'}"
                del changed[key]
                continue
            print(f"  {key}: {len(claims)} claims still exact")
        for key, why in kept.items():
            print(f"  {key}: {why}")
        # a claimed function whose module keeps its old name cannot be renamed yet
        blocked = set()
        for key in kept:
            for c in man["modules"][key]["claims"]:
                if c["name"] in mapping:
                    blocked.add(c["name"])
        if blocked:
            print(f"  not renamed (claimed in a module that keeps old names): {sorted(blocked)}")
            ren = [r for r in ren if r[0] not in blocked]
            mapping = {o: n for o, n, _ in ren}
            for key in list(changed):
                text = (ROOT / man["modules"][key]["source"]).read_text(encoding="latin1")
                for o, n, _ in ren:
                    text = pat[o].sub(n, text)
                changed[key] = text
        if a.verify_only:
            print(f"VERIFY-ONLY OK: {len(ren)} renames, {len(changed)} modules re-proven")
            return 0
        for key, text in changed.items():
            m = man["modules"][key]
            data = text.replace("\r\n", "\n").encode("latin1")
            (ROOT / m["source"]).write_bytes(data)
            m["source_sha256"] = sha(data)
            for c in m["claims"]:
                c["name"] = mapping.get(c["name"], c["name"])
            m["scaffold"] = sorted(mapping.get(s, s) for s in m.get("scaffold", []))
        modmod.MANIFEST.write_text(json.dumps(man, indent=1) + "\n")
        for o, n, why in ren:
            sec = "code" if o in syms["code"] else "data"
            rec = syms[sec].pop(o)
            rec.setdefault("history", []).append({"was": o, "why": why})
            syms[sec][n] = rec
            # keep the old name bound to the same address so in-flight drafts still compile
            alias = {k: v for k, v in rec.items() if k not in ("history", "grounding")}
            alias["alias_of"] = n
            syms[sec][o] = alias
            for r in syms[sec].values():  # keep aliases flat: older names point at the newest
                if r.get("alias_of") == o:
                    r["alias_of"] = n
        symmod.save(syms)
        with (ROOT / "evidence" / "promotions.jsonl").open("a") as fh:
            fh.write(json.dumps({"time": dt.datetime.now().isoformat(timespec="seconds"), "module": "RENAME",
                                 "new_claims": [], "renames": [[o, n] for o, n, _ in ren],
                                 "modules_reproven": sorted(changed)}) + "\n")
    print(f"RENAMED {len(ren)} symbols; {len(changed)} modules re-proven and rewritten")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
