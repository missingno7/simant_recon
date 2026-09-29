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
DEFAULT_PROFILE = "msc600"


@lru_cache(maxsize=1)
def table() -> dict:
    return json.loads(TABLE.read_text())


@lru_cache(maxsize=1)
def by_address() -> dict:
    return {(r["unit"], r["seg"], r["off"]): r for r in table()["functions"]}


def name_of(unit: str, seg: int, off: int) -> str:
    syms = symmod.load()
    for n, s in syms["code"].items():
        if s["unit"] == unit and s["seg"] == seg and s["off"] == off:
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
        if p["name"] == public:
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


if __name__ == "__main__":
    if sys.argv[1:] == ["freeze"]:
        raise SystemExit(freeze())
    print(__doc__)
