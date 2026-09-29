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
        # re-prove every changed module
        mapping = {o: n for o, n, _ in ren}
        for key, text in changed.items():
            m = man["modules"][key]
            claims = [dict(c, name=mapping.get(c["name"], c["name"])) for c in m["claims"]]
            res = modmod.verify_module(text, m, claims)
            bad = [n for n, c in res["claims"].items() if not c["exact"]]
            if not res["exact"]:
                raise SystemExit(f"{key}: rename breaks exactness ({bad or res.get('data') or res.get('extent')})")
            print(f"  {key}: {len(claims)} claims still exact")
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
        symmod.save(syms)
        with (ROOT / "evidence" / "promotions.jsonl").open("a") as fh:
            fh.write(json.dumps({"time": dt.datetime.now().isoformat(timespec="seconds"), "module": "RENAME",
                                 "new_claims": [], "renames": [[o, n] for o, n, _ in ren],
                                 "modules_reproven": sorted(changed)}) + "\n")
    print(f"RENAMED {len(ren)} symbols; {len(changed)} modules re-proven and rewritten")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
