"""Function table access (layout/functions.json) joined with the names registry.

    python tools/functions.py freeze    # write layout/functions.json from build/inventory (refuses overwrite)

layout/functions.json is tracked evidence: one row per code entry with unit,
frame, offset, recursive-descent extent and entry evidence.  Extents are
``DESCENT`` (all instructions reachable from the entry) unless reviewed.
"""
from __future__ import annotations

import json
import sys
from functools import lru_cache
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import exe as exemod  # noqa: E402
import symbols as symmod  # noqa: E402

ROOT = exemod.ROOT
TABLE = ROOT / "layout" / "functions.json"
DEFAULT_PROFILE = "msc600a"


@lru_cache(maxsize=1)
def table() -> dict:
    return json.loads(TABLE.read_text())


@lru_cache(maxsize=1)
def by_address() -> dict:
    return {(r["unit"], r["seg"], r["off"]): r for r in table()["functions"]}


def name_of(unit: str, seg: int, off: int) -> str:
    syms = symmod.load()
    for n, s in syms["code"].items():
        if s["unit"] == unit and s["seg"] == seg and s["off"] == off and not s.get("alias_of"):
            return n
    return symmod.default_name(unit, seg, off)


def get(func: str) -> dict:
    syms = symmod.load()
    if func in syms["code"]:
        s = syms["code"][func]
        key = (s["unit"], s["seg"], s["off"])
        name = func
    else:
        parts = func.split(":")
        if len(parts) != 3:
            raise SystemExit(f"unknown function {func}")
        key = (parts[0], int(parts[1], 16), int(parts[2], 16))
        name = name_of(*key)
    row = by_address().get(key)
    if row is None:
        raise SystemExit(f"no function table row for {func}")
    return {**row, "name": name}


def profile_flags(profile: str) -> list[str]:
    import compiler
    return list(compiler.toolchain()["profiles"][profile]["flags"])


def code_segment(obj_bytes: bytes, public: str) -> str:
    from omf import OmfReader
    obj = OmfReader(communals=True).read(obj_bytes)
    for p in obj.publics + getattr(obj, "local_publics", []):
        if p["name"] in (public, "@" + public.lstrip("_")):
            return p["segment"]
    return "UNIT_TEXT"


def freeze() -> int:
    if TABLE.exists():
        print("layout/functions.json exists; refusing to overwrite")
        return 1
    inv = json.loads((ROOT / "build/inventory/functions.json").read_text())
    rows = []
    for f in inv["functions"]:
        rows.append({"unit": f["unit"], "seg": f["seg"], "off": f["off"], "size": f["size"],
                     "region": f["region"], "extent": "DESCENT",
                     "evidence": sorted(f["evidence"]),
                     **({"jump_tables": f["jump_tables"]} if f.get("jump_tables") else {}),
                     **({"notes": ["overlaps " + ",".join(f["overlaps"])]} if f.get("overlaps") else {})})
    rows.sort(key=lambda r: (r["unit"] != "root", r["unit"], r["seg"] * 16 + r["off"]))
    TABLE.write_text(json.dumps({"schema": "simant-functions-v1",
                                 "source": "tools/inventory.py recursive descent",
                                 "functions": rows}, indent=0) + "\n")
    print(f"wrote {len(rows)} rows")
    return 0


def add(addr: str, size: int, why: str) -> int:
    """Add a reviewed function row (e.g. an unreferenced entry proven by layout)."""
    from lockfile import CanonicalLock
    with CanonicalLock():
        return _add(addr, size, why)


def resize(addr: str, size: int, why: str) -> int:
    """Correct the extent of an unclaimed function row (reviewed)."""
    from lockfile import CanonicalLock
    with CanonicalLock():
        unit, seg, off = addr.split(":")
        seg, off = int(seg, 16), int(off, 16)
        t = json.loads(TABLE.read_text())
        row = next((r for r in t["functions"] if r["unit"] == unit and r["seg"] == seg and r["off"] == off), None)
        if row is None:
            raise SystemExit("no such row")
        man = json.loads((ROOT / "layout" / "manifest.json").read_text())
        if any(c["unit"] == unit and c["seg"] == seg and c["off"] == off for m in man["modules"].values()
               for c in m["claims"]):
            raise SystemExit("row is claimed")
        lin = seg * 16 + off
        for r in t["functions"]:
            if r is not row and r["unit"] == unit and r["seg"] * 16 + r["off"] < lin + size \
                    and lin < r["seg"] * 16 + r["off"] + r["size"]:
                raise SystemExit(f"new extent overlaps {r}")
        row.setdefault("notes", []).append(f"resized {row['size']} -> {size}: {why}")
        row["size"] = size
        row["extent"] = "REVIEWED"
        TABLE.write_text(json.dumps(t, indent=0) + "\n")
        print("resized", addr, size)
        return 0


def reframe(addr: str, newseg: int, why: str) -> int:
    """Move an unclaimed row to another code frame (same linear address)."""
    from lockfile import CanonicalLock
    with CanonicalLock():
        unit, seg, off = addr.split(":")
        seg, off = int(seg, 16), int(off, 16)
        t = json.loads(TABLE.read_text())
        row = next((r for r in t["functions"] if r["unit"] == unit and r["seg"] == seg and r["off"] == off), None)
        if row is None:
            raise SystemExit("no such row")
        man = json.loads((ROOT / "layout" / "manifest.json").read_text())
        if any(c["unit"] == unit and c["seg"] == seg and c["off"] == off for m in man["modules"].values()
               for c in m["claims"]):
            raise SystemExit("row is claimed")
        lin = seg * 16 + off
        if not (newseg * 16 <= lin < newseg * 16 + 0x10000):
            raise SystemExit("new frame does not cover the address")
        row["seg"], row["off"] = newseg, lin - newseg * 16
        row.setdefault("notes", []).append(f"re-framed {seg:04X}:{off:04X} -> {newseg:04X}:{row['off']:04X}: {why}")
        TABLE.write_text(json.dumps(t, indent=0) + "\n")
        s = symmod.load()
        old = symmod.default_name(unit, seg, off)
        new = symmod.default_name(unit, newseg, row["off"])
        for sec in ("code",):
            for n, r in list(s[sec].items()):
                if r.get("unit") == unit and r["seg"] == seg and r["off"] == off:
                    r["seg"], r["off"] = newseg, row["off"]
                    if n == old:
                        s[sec].pop(n)
                        r.setdefault("history", []).append({"was": old, "why": "re-framed: " + why})
                        s[sec][new] = r
        symmod.save(s)
        print("re-framed", addr, "->", f"{unit}:{newseg:04X}:{row['off']:04X}")
        return 0


def _add(addr: str, size: int, why: str) -> int:
    unit, seg, off = addr.split(":")
    seg, off = int(seg, 16), int(off, 16)
    t = json.loads(TABLE.read_text())
    if any(r["unit"] == unit and r["seg"] == seg and r["off"] == off for r in t["functions"]):
        raise SystemExit("row exists")
    lin = seg * 16 + off
    for r in t["functions"]:
        if r["unit"] == unit and r["seg"] * 16 + r["off"] < lin + size and lin < r["seg"] * 16 + r["off"] + r["size"]:
            raise SystemExit(f"overlaps {r}")
    t["functions"].append({"unit": unit, "seg": seg, "off": off, "size": size, "region": "game_or_library",
                           "extent": "REVIEWED", "evidence": ["reviewed"], "notes": [why]})
    t["functions"].sort(key=lambda r: (r["unit"] != "root", r["unit"], r["seg"] * 16 + r["off"]))
    TABLE.write_text(json.dumps(t, indent=0) + "\n")
    s = symmod.load()
    s["code"][symmod.default_name(unit, seg, off)] = {"unit": unit, "seg": seg, "off": off, "grounding": "reviewed: " + why}
    symmod.save(s)
    print("added", addr)
    return 0


if __name__ == "__main__":
    if sys.argv[1:] == ["freeze"]:
        raise SystemExit(freeze())
    if len(sys.argv) >= 5 and sys.argv[1] == "add":
        raise SystemExit(add(sys.argv[2], int(sys.argv[3]), " ".join(sys.argv[4:])))
    if len(sys.argv) >= 5 and sys.argv[1] == "reframe":
        raise SystemExit(reframe(sys.argv[2], int(sys.argv[3], 16), " ".join(sys.argv[4:])))
    if len(sys.argv) >= 5 and sys.argv[1] == "resize":
        raise SystemExit(resize(sys.argv[2], int(sys.argv[3]), " ".join(sys.argv[4:])))
    print(__doc__)
