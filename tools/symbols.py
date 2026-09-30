"""Maintain layout/symbols.json, the program-wide names registry.

Sections:
  code     C name -> {unit, seg, off, grounding}   game code (default ``f_SSSS_OOOO`` /
                                                    ``oNN_SSSS_OOOO`` until renamed)
  data     C name -> {seg, off, grounding}          DGROUP or far data
  runtime  OBJ name -> {unit, seg, off, library, member}   located historical library publics

Every address must be grounded: an inventory entry (far/near call, vector,
switch dispatch...) for code, an original instruction operand for data, or a
unique library-member location for runtime names.

    python tools/symbols.py bootstrap      # create from build/inventory + build/libmatch (refuses overwrite)
    python tools/symbols.py rename OLD NEW --why "evidence"
    python tools/symbols.py add-data NAME SEG OFF --why "anchor"
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import exe as exemod  # noqa: E402

ROOT = exemod.ROOT
SYMBOLS = ROOT / "layout" / "symbols.json"
IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,30}$")


def default_name(unit: str, seg: int, off: int) -> str:
    return f"f_{seg:04X}_{off:04X}" if unit == "root" else f"o{unit[1:]}_{seg:04X}_{off:04X}"


def load() -> dict:
    return json.loads(SYMBOLS.read_text())


def save(d: dict) -> None:
    for k in ("code", "data", "runtime"):
        d[k] = dict(sorted(d.get(k, {}).items()))
    # atomic replace: concurrent readers (modmap, context, search) never see a partial file
    tmp = SYMBOLS.with_suffix(f".tmp{os.getpid()}")
    tmp.write_text(json.dumps(d, indent=1) + "\n")
    os.replace(tmp, SYMBOLS)


def bootstrap() -> int:
    if SYMBOLS.exists():
        print("symbols.json exists; refusing to overwrite")
        return 1
    inv = json.loads((ROOT / "build/inventory/functions.json").read_text())
    code = {}
    for f in inv["functions"]:
        if f["region"] != "game_or_library":
            continue
        n = default_name(f["unit"], f["seg"], f["off"])
        code[n] = {"unit": f["unit"], "seg": f["seg"], "off": f["off"],
                   "grounding": "inventory:" + ",".join(sorted(f["evidence"]))}
    runtime = {}
    lm = json.loads((ROOT / "build/libmatch/msc600-large.json").read_text())
    for lib, rep in lm.items():
        for r in rep["rows"]:
            hits = r.get("hits") or []
            if len(hits) != 1:
                continue
            h = hits[0]
            for pub, off in r["publics"].items():
                lin = h["linear"] + off
                seg = 0x29F4 if h["unit"] == "root" and lin >= 0x29F40 else lin >> 4
                runtime[pub] = {"unit": h["unit"], "seg": seg, "off": lin - seg * 16,
                                "library": Path(lib).name, "member": r["module"]}
    save({"schema": "simant-symbols-v1", "code": code, "data": {}, "runtime": runtime})
    print(f"bootstrapped {len(code)} code, {len(runtime)} runtime names")
    return 0


def rename(old: str, new: str, why: str) -> int:
    from lockfile import CanonicalLock
    with CanonicalLock():
        return _rename(old, new, why)


def _rename(old: str, new: str, why: str) -> int:
    d = load()
    man = json.loads((ROOT / "layout" / "manifest.json").read_text())
    if any(c["name"] == old for m in man["modules"].values() for c in m["claims"]):
        raise SystemExit(f"{old} is claimed; claimed functions are renamed by the supervisor with their source")
    if not IDENT.match(new):
        raise SystemExit(f"bad identifier {new}")
    for sec in ("code", "data"):
        if old in d[sec]:
            if new in d["code"] or new in d["data"]:
                raise SystemExit(f"{new} already registered")
            rec = d[sec].pop(old)
            rec.setdefault("history", []).append({"was": old, "why": why})
            d[sec][new] = rec
            # keep the old name bound as an alias: accepted sources may still use it
            alias = {k: v for k, v in rec.items() if k not in ("history", "grounding")}
            alias["alias_of"] = new
            d[sec][old] = alias
            for r in d[sec].values():  # keep aliases flat: older names point at the newest
                if r.get("alias_of") == old:
                    r["alias_of"] = new
            save(d)
            print(f"renamed {old} -> {new}")
            return 0
    raise SystemExit(f"{old} not registered")


def remove(name: str, why: str) -> int:
    """Delete a mistaken registration: never a claimed function, an alias target, or a name
    still used by canonical sources.  The removal is journaled in evidence/symbol-removals.jsonl."""
    from lockfile import CanonicalLock
    with CanonicalLock():
        d = load()
        sec = next((s for s in ("code", "data") if name in d[s]), None)
        if sec is None:
            raise SystemExit(f"{name} not registered")
        man = json.loads((ROOT / "layout" / "manifest.json").read_text())
        if any(c["name"] == name for m in man["modules"].values() for c in m["claims"]):
            raise SystemExit(f"{name} is claimed")
        dependents = [r for r in d[sec].values() if r.get("alias_of") == name]
        if dependents and not d[sec][name].get("alias_of"):
            raise SystemExit(f"{name} is an alias target")
        for r in dependents:  # removing a middle alias: re-point to its own target
            r["alias_of"] = d[sec][name]["alias_of"]
        word = re.compile(r"\b" + re.escape(name) + r"\b")
        for f in (ROOT / "src").rglob("*"):
            if f.suffix.lower() in (".c", ".h", ".asm", ".inc") and word.search(f.read_text(errors="replace")):
                raise SystemExit(f"{name} is used by {f.relative_to(ROOT)}")
        rec = d[sec].pop(name)
        save(d)
        with open(ROOT / "evidence" / "symbol-removals.jsonl", "a", encoding="utf-8", newline="\n") as j:
            j.write(json.dumps({"name": name, "section": sec, "record": rec, "why": why}) + "\n")
        print(f"removed {name}")
        return 0


def add_data(name: str, seg: int, off: int, why: str) -> int:
    from lockfile import CanonicalLock
    with CanonicalLock():
        return _add_data(name, seg, off, why)


def _add_data(name: str, seg: int, off: int, why: str) -> int:
    d = load()
    if not IDENT.match(name):
        raise SystemExit(f"bad identifier {name}")
    if name in d["code"] or name in d["data"]:
        raise SystemExit(f"{name} already registered")
    for n, r in d["data"].items():
        if r["seg"] == seg and r["off"] == off:
            raise SystemExit(f"address already named {n}")
    d["data"][name] = {"seg": seg, "off": off, "grounding": why}
    save(d)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("bootstrap")
    r = sub.add_parser("rename"); r.add_argument("old"); r.add_argument("new"); r.add_argument("--why", required=True)
    a = sub.add_parser("add-data"); a.add_argument("name"); a.add_argument("seg"); a.add_argument("off")
    a.add_argument("--why", required=True)
    rm = sub.add_parser("remove"); rm.add_argument("name"); rm.add_argument("--why", required=True)
    args = ap.parse_args()
    if args.cmd == "bootstrap":
        return bootstrap()
    if args.cmd == "remove":
        return remove(args.name, args.why)
    if args.cmd == "rename":
        return rename(args.old, args.new, args.why)
    return add_data(args.name, int(args.seg, 16), int(args.off, 16), args.why)


if __name__ == "__main__":
    raise SystemExit(main())
