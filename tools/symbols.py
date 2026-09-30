"""Maintain layout/symbols.json, the program-wide names registry.

Sections:
  code     C name -> {unit, seg, off, grounding}   game code (default ``f_SSSS_OOOO`` /
                                                    ``oNN_SSSS_OOOO`` until renamed)
  data     C name -> {seg, off, grounding}          DGROUP or far data
  runtime  OBJ name -> {unit, seg, off, library, member}   located historical library publics
           (runtime data publics carry "kind": "data", unit S27; see add-runtime)

Every address must be grounded: an inventory entry (far/near call, vector,
switch dispatch...) for code, an original instruction operand for data, or a
unique library-member location for runtime names.

    python tools/symbols.py bootstrap      # create from build/inventory + build/libmatch (refuses overwrite)
    python tools/symbols.py rename OLD NEW --why "evidence"
    python tools/symbols.py add-data NAME SEG OFF --why "anchor"
    python tools/symbols.py add-runtime NAME SEG OFF --why "evidence"   # public of a located runtime member
    python tools/symbols.py add-runtime --batch FILE                    # [{"name","unit","seg","off","why"}]
    python tools/symbols.py set-convention NAME pascal --why "evidence" # (or cdecl to clear)

A code record may carry ``"convention": "pascal"``: only then does an upper-cased,
undecorated OBJ name (MSC pascal) bind to it (tools/match.py pascal_name).
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
    from lockfile import atomic_write_text
    atomic_write_text(SYMBOLS, json.dumps(d, indent=1) + "\n")


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


CONVENTIONS = ("pascal", "cdecl")


def set_convention(name: str, conv: str, why: str) -> int:
    """Record the calling convention of a registered code name (and its aliases).  ``pascal``
    lets upper-cased undecorated OBJ names bind to it; ``cdecl`` (the default) removes the
    field.  Evidence is required: the convention changes which declarations bind."""
    if conv not in CONVENTIONS:
        raise SystemExit(f"convention must be one of {CONVENTIONS}")
    if not why.strip():
        raise SystemExit("--why is required")
    from lockfile import CanonicalLock
    with CanonicalLock():
        d = load()
        rec = d["code"].get(name)
        if rec is None:
            raise SystemExit(f"{name} is not a registered code name")
        if rec.get("alias_of"):
            raise SystemExit(f"{name} is an alias of {rec['alias_of']}; set the convention there")
        if conv == "pascal":
            clash = [n for n, r in d["code"].items() if n != name and n.upper() == name.upper()
                     and r.get("convention") == "pascal" and r.get("alias_of") != name]
            if clash:
                raise SystemExit(f"{name}: pascal spelling {name.upper()} already used by {clash}")
        was = rec.get("convention", "cdecl")
        for n, r in d["code"].items():
            if n == name or r.get("alias_of") == name:
                if conv == "cdecl":
                    r.pop("convention", None)
                else:
                    r["convention"] = conv
        rec.setdefault("history", []).append({"convention": f"{was} -> {conv}", "why": why})
        save(d)
        print(f"{name}: convention {was} -> {conv}")
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


def add_runtime(entries: list[dict]) -> int:
    """Register publics of runtime members located in evidence/toolchain/runtime-location.json
    (e.g. one located below libmatch's minimum size).  Each name must be a public of a located
    member at exactly SEG:OFF, and that member must bind exactly under tools/runtime.py, so the
    address is grounded by the library member's own location, never by a referencing operand.

    Runtime *data* publics (e.g. ``__iob`` of _file.c, SEG 55B3) are accepted when they are
    publics of a runtime DGROUP data segment that tools/runtime.py places by a symbolic rule and
    verifies exactly (bytes, fixups, relocations), or near communals placed by COMDEF_ANCHORS
    (at least two agreeing data fixups).  They are recorded with ``"kind": "data"`` so that game
    modules bind them as data; the grounding names the rule and its anchors."""
    import runtime as rtmod
    from lockfile import CanonicalLock
    with CanonicalLock():
        results, derived, *_ = rtmod.verify_all()
        where = {}
        for r in results:
            for n, (seg, off) in r.get("public_addresses", {}).items():
                where.setdefault(n, []).append((r, seg, off))
        comm = {}
        data_where = {}
        for d in rtmod.verify_data(results, derived, communals=comm):
            for n, (seg, off) in d.get("public_addresses", {}).items():
                data_where.setdefault(n, []).append((d, seg, off, f"{d['segment']} placed by rule {d['rule']} at "
                                                                    f"{d['linear']:#x}, verifies exactly"))
        for n, c in comm.items():
            if c["exact"]:
                data_where.setdefault(n, []).append(
                    (c, rtmod.DGROUP, c["linear"] - rtmod.DGROUP * 16,
                     f"near communal ({c['size']} bytes) placed by rule COMDEF_ANCHORS: {', '.join(c['anchors'])}"))
        d = load()
        added = 0
        for e in entries:
            num = lambda v: int(v, 16) if isinstance(v, str) else int(v)   # noqa: E731  hex strings or ints
            name, unit, seg, off = e["name"], e.get("unit", "root"), num(e["seg"]), num(e["off"])
            if not e.get("why"):
                raise SystemExit(f"{name}: --why is required")
            dhits = [h for h in data_where.get(name, []) if h[1] == seg and h[2] == off]
            if dhits and not where.get(name):
                r, _, _, how = dhits[0]
                rec = {"kind": "data", "unit": "S27", "seg": seg, "off": off, "library": r["library"],
                       "member": r["member"], "grounding": f"runtime data: {r['library']} {r['member']} {how} "
                                                           f"(tools/runtime.py); {e['why']}"}
            else:
                rec = None
            hits = [(r, sg, of) for r, sg, of in where.get(name, []) if sg == seg and of == off]
            if rec is None and (unit != "root" or not hits):
                found = ([f"{r['member']} {sg:04X}:{of:04X}" for r, sg, of in where.get(name, [])]
                         + [f"{h[0]['member']} data {h[1]:04X}:{h[2]:04X}" for h in data_where.get(name, [])])
                raise SystemExit(f"{name} is not a public of a located runtime member at {unit}:{seg:04X}:{off:04X}"
                                 f" (located: {found or 'none'})")
            if rec is None:
                r = hits[0][0]
                if not r["exact"]:
                    raise SystemExit(f"{name}: member {r['member']} does not bind exactly: {r['reasons'][:3]}")
                rec = {"unit": unit, "seg": seg, "off": off, "library": r["library"], "member": r["member"],
                       "module_index": r["module_index"],
                       "grounding": f"runtime-location: {r['library']} {r['member']} located at {r['linear']:#x}, "
                                    f"binds exactly (tools/runtime.py); {e['why']}"}
            old = d["runtime"].get(name)
            if old is not None:
                if (old["seg"], old["off"]) != (rec["seg"], rec["off"]):
                    raise SystemExit(f"{name} already registered at {old['unit']}:{old['seg']:04X}:{old['off']:04X}")
                print(f"{name} already registered")
                continue
            cname = name[1:] if name.startswith("_") else None
            if name in d["code"] or name in d["data"] or (cname and (cname in d["code"] or cname in d["data"])):
                raise SystemExit(f"{name} clashes with a registered code/data name")
            d["runtime"][name] = rec
            added += 1
            print(f"registered runtime {rec.get('kind', 'code')} {name} = {rec['unit']}:{seg:04X}:{off:04X} "
                  f"({rec['member']})")
        save(d)
        print(f"added {added} runtime names")
        return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("bootstrap")
    r = sub.add_parser("rename"); r.add_argument("old"); r.add_argument("new"); r.add_argument("--why", required=True)
    a = sub.add_parser("add-data"); a.add_argument("name"); a.add_argument("seg"); a.add_argument("off")
    a.add_argument("--why", required=True)
    rm = sub.add_parser("remove"); rm.add_argument("name"); rm.add_argument("--why", required=True)
    rt = sub.add_parser("add-runtime"); rt.add_argument("name", nargs="?"); rt.add_argument("seg", nargs="?")
    rt.add_argument("off", nargs="?"); rt.add_argument("--why"); rt.add_argument("--batch", type=Path)
    sc = sub.add_parser("set-convention"); sc.add_argument("name"); sc.add_argument("convention", choices=CONVENTIONS)
    sc.add_argument("--why", required=True)
    args = ap.parse_args()
    if args.cmd == "set-convention":
        return set_convention(args.name, args.convention, args.why)
    if args.cmd == "add-runtime":
        if args.batch:
            return add_runtime(json.loads(args.batch.read_text()))
        if not (args.name and args.seg and args.off):
            raise SystemExit("add-runtime NAME SEG OFF --why ... or --batch FILE")
        return add_runtime([{"name": args.name, "seg": int(args.seg, 16), "off": int(args.off, 16), "why": args.why}])
    if args.cmd == "bootstrap":
        return bootstrap()
    if args.cmd == "remove":
        return remove(args.name, args.why)
    if args.cmd == "rename":
        return rename(args.old, args.new, args.why)
    return add_data(args.name, int(args.seg, 16), int(args.off, 16), args.why)


if __name__ == "__main__":
    raise SystemExit(main())
