"""FAR_BSS accounting: far communals allocated by the linker (frame 50F6).

    python tools/farbss.py              # region check and per-variable size evidence
    python tools/farbss.py --list       # also list every variable with its evidence

MSC 6 turns a public far variable without initialiser into a COMDEF far communal (rule
FARSEG-1): the object carries its name and size, no bytes.  LINK allocates the far
communals after all FAR_DATA segments (class FAR_BSS) in order of first appearance and,
because DGROUP follows in section 27, writes them into the image as zero bytes.  They are
linker zero fill, not reconstructed data, and are accounted as follows:

* the region [50F6:0000, DGROUP) must be entirely zero and contain no placement;
* registered data symbols of frame 50F6 must start at offset 0; each variable's size is
  the distance to the next registered variable (the last one runs to DGROUP), so the
  variables tile the region;
* size evidence per variable, strongest first:
    comdef       a COMDEF in a freshly compiled accepted module (the defining declaration);
    declaration  an ``extern`` declaration with complete dimensions in an accepted source;
    save_table   S09's save/load table (frame 4E4B, 307 x {int count; int size; void far *p}),
                 count*size bytes at p (program data, read from the image);
  a size equal to the gap *verifies* the variable (comdef) or makes it *consistent*
  (declaration, save_table); evidence larger than the gap is a conflict (the variable would
  overlap the next registered one).  A COMDEF conflict fails validation; the others are
  reported for review.  Variables without evidence stay unverified.

Communal *order* (first appearance in the link) needs the historical link and is not checked.
"""
from __future__ import annotations

import argparse
import re
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import exe as exemod  # noqa: E402
import match  # noqa: E402

ROOT = exemod.ROOT
# Evidence (build/workers/data/s27_map.md): 50F6:0000-4BCF is all zero, the last far frame
# before DGROUP, referenced only through external symbols by every module (58 modules use
# per-symbol relocation groups), i.e. no object defines it: the linker's FAR_BSS.
FAR_BSS_SEG = 0x50F6
SAVE_TABLE = (0x4E4B, 0, 307)        # frame, offset, entries of 8 bytes
TYPE_SIZE = {"char": 1, "unsigned char": 1, "signed char": 1, "int": 2, "unsigned": 2,
             "unsigned int": 2, "short": 2, "unsigned short": 2, "long": 4, "unsigned long": 4}
DECL_RE = re.compile(r"^\s*extern\s+((?:unsigned\s+|signed\s+)?(?:char|int|short|long)|unsigned)\s+"
                     r"(far\s*\*\s*)?far\s+(\w+)\s*((?:\[[^\]]*\])*)\s*;", re.M)


def _dims(text: str) -> int | None:
    n = 1
    for d in re.findall(r"\[([^\]]*)\]", text):
        d = d.strip()
        if not re.fullmatch(r"[0-9A-Fa-fxX*+ ()]+", d or "?"):
            return None
        try:
            n *= int(eval(d, {"__builtins__": {}}))   # noqa: S307 (digits and operators only)
        except Exception:  # noqa: BLE001
            return None
    return n


def declared_sizes(sources: dict[str, str]) -> dict[str, list[tuple[int, str]]]:
    """C name -> [(bytes, module)] from extern declarations with complete dimensions."""
    out: dict[str, list[tuple[int, str]]] = {}
    for key, text in sources.items():
        for m in DECL_RE.finditer(text):
            base, ptr, name, dims = m.groups()
            n = _dims(dims) if dims else 1
            if n is None:
                continue
            elem = 4 if ptr else TYPE_SIZE.get(" ".join(base.split()))
            if elem:
                out.setdefault(name, []).append((n * elem, key))
    return out


def save_table_sizes() -> dict[int, int]:
    """FAR_BSS offset -> count*size from S09's save table (program data)."""
    x = exemod.load()
    frame, off, n = SAVE_TABLE
    out = {}
    for i in range(n):
        cnt, size, poff, pseg = struct.unpack_from("<HHHH", x.read("S27", frame * 16 + off + 8 * i, 8))
        if pseg == FAR_BSS_SEG:
            out.setdefault(poff, cnt * size)
    return out


def account(sources: dict[str, str] | None = None, comdefs: dict[str, list[tuple[int, str]]] | None = None,
            placements: list[tuple[int, int]] | None = None) -> dict:
    """``sources``: module key -> source text; ``comdefs``: C name -> [(bytes, module)] from
    freshly compiled accepted objects; ``placements``: (linear, size) of every placed segment."""
    x = exemod.load()
    start, end = FAR_BSS_SEG * 16, match.DGROUP_SEG * 16
    region = x.read("S27", start, end - start)
    failures, warnings = [], []
    if any(region):
        failures.append(f"FAR_BSS region {start:05X}-{end:05X} is not all zero")
    for a, n in placements or []:
        if a < end and start < a + n:
            failures.append(f"a placement ({a:05X}+{n}) lies inside FAR_BSS")
    names: dict[int, str] = {}
    import symbols as symmod
    for n, r in symmod.load()["data"].items():
        if r["seg"] == FAR_BSS_SEG and not r.get("alias_of"):
            if r["off"] not in names or names[r["off"]].startswith("fd_"):
                names[r["off"]] = n
    offs = sorted(names)
    if not offs or offs[0] != 0:
        failures.append("registered FAR_BSS variables do not start at offset 0")
    gaps = {o: (offs[i + 1] if i + 1 < len(offs) else end - start) - o for i, o in enumerate(offs)}
    decl = declared_sizes(sources or {})
    comd = comdefs or {}
    save = save_table_sizes()
    rows = []
    tot = {"verified": 0, "consistent": 0, "unverified": 0}
    for o in offs:
        n, gap = names[o], gaps[o]
        aliases = {n} | {a for a, r in symmod.load()["data"].items()
                         if r["seg"] == FAR_BSS_SEG and r["off"] == o}
        ev = []
        for a in aliases:
            ev += [("comdef", z, k) for z, k in comd.get(a, [])]
            ev += [("declaration", z, k) for z, k in decl.get(a, [])]
        if o in save:
            ev.append(("save_table", save[o], "S27:4E4B"))
        status = "unverified"
        for kind, z, k in ev:
            if z > gap:
                msg = f"{n} (50F6:{o:04X}): {kind} size {z} in {k} exceeds the gap {gap} to the next variable"
                (failures if kind == "comdef" else warnings).append(msg)
            elif z == gap:
                if kind == "comdef":
                    status = "verified"
                elif status == "unverified":
                    status = "consistent"
        tot[status] += gap
        rows.append({"name": n, "off": o, "size": gap, "status": status,
                     "evidence": [f"{kind}:{z}@{k}" for kind, z, k in ev]})
    return {"start": start, "size": end - start, "variables": len(offs), "accounted": not failures,
            "bytes_verified": tot["verified"], "bytes_consistent": tot["consistent"],
            "bytes_unverified": tot["unverified"], "failures": failures, "warnings": warnings, "rows": rows}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    import modules as modmod
    man = modmod.load_manifest()
    sources = {k: (ROOT / m["source"]).read_text(encoding="latin1") for k, m in man["modules"].items()
               if m.get("lang", "c") == "c"}
    r = account(sources)
    print(f"FAR_BSS {r['start']:05X}+{r['size']}: {r['variables']} variables; sizes verified {r['bytes_verified']}, "
          f"consistent {r['bytes_consistent']}, unverified {r['bytes_unverified']} bytes "
          f"(COMDEF evidence is added by validate.py from fresh objects)")
    for f in r["failures"]:
        print("  FAIL", f)
    for w in r["warnings"]:
        print("  warn", w)
    if a.list:
        for row in r["rows"]:
            print(f"  50F6:{row['off']:04X} {row['size']:6d} {row['status']:<10} {row['name']:<24} {' '.join(row['evidence'])}")
    return 0 if r["accounted"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
