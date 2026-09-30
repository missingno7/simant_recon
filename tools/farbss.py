"""FAR_BSS accounting: far communals allocated by the linker (frame 50F6).

    python tools/farbss.py              # region check and per-variable size evidence
    python tools/farbss.py --list       # also list every variable with its evidence
    python tools/farbss.py --probe      # measure the canonical declarations with the compiler

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
    pinned       the declared size, measured by the compiler, on which the byte-exact code of an
                 accepted module depends (``probe_declarations``, below);
    declaration  an ``extern`` declaration with complete dimensions in an accepted source
                 (measured by the compiler when probed, else read by a simple parser);
    save_table   S09's save/load table (frame 4E4B, 307 x {int count; int size; void far *p}),
                 count*size bytes at p (program data, read from the image);
  a size equal to the gap *verifies* the variable (comdef), *pins* it (pinned) or makes it
  *consistent* (declaration, save_table); evidence larger than the gap is a conflict (the
  variable would overlap the next registered one).  A COMDEF or pinned conflict fails
  validation; the others are reported for review.  Variables without evidence stay unverified.

Declarations are never turned into definitions.  ``probe_declarations`` compiles the canonical
source of each accepted C module twice, off the record: (1) with one appended
``unsigned near __fbss_probe_N = sizeof(NAME);`` per declared FAR_BSS name, which measures the
declaration with the pinned compiler (types, typedefs, macros and all); (2) with the first
dimension of every complete array declaration of those names enlarged by one element.  When
(2) changes the module's code or data bytes or fixups, the byte-exact accepted code depends on
the declared size (e.g. ``sizeof`` in a ``memset`` or a loop bound), so the original code was
compiled with the same size: the names responsible (found by one compile per name) are
*pinned*.  A module whose object does not change says nothing about the outer dimension.

Communal *order* (first appearance in the link) needs the historical link and is not checked.
"""
from __future__ import annotations

import argparse
import json
import re
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import exe as exemod  # noqa: E402
import match  # noqa: E402

ROOT = exemod.ROOT
# Evidence (work/data/s27_map.md): 50F6:0000-4BCF is all zero, the last far frame
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


EXTERN_RE = re.compile(r"\bextern\b[^;{}()]*(?:\([^;{}()]*\)[^;{}()]*)*;")


TYPE_WORDS = {"void", "char", "int", "short", "long", "unsigned", "signed", "float", "double", "far", "near",
              "huge", "const", "volatile", "_far", "_near", "_huge", "__far", "__near", "extern", "static",
              "_cdecl", "_pascal", "_fastcall", "cdecl", "pascal", "_interrupt", "_loadds", "_saveregs"}


def _no_parameters(decl: str) -> str:
    """A declaration without its parameter lists (their names are not declared variables);
    declarator parentheses, e.g. ``void (far * far p)(int x)``, keep their contents."""
    while True:
        def one(m):
            pre = decl[:m.start()].rstrip()
            prev = re.search(r"(\w+)$", pre)
            if pre.endswith((")", "\x01")) or (prev and prev.group(1) not in TYPE_WORDS):
                return "\x01"                                  # a parameter list
            return " " + m.group(1) + " "                       # a declarator group
        new = re.sub(r"\(([^()]*)\)", one, decl)
        if new == decl:
            return decl
        decl = new


def _declared_names(text: str, names: set[str]) -> dict[str, str | None]:
    """name -> first dimension text of its extern declaration in ``text`` (None for a scalar,
    "" for an incomplete array), for the given FAR_BSS names."""
    out = {}
    text = re.sub(r"/\*.*?\*/|//[^\n]*", " ", text, flags=re.S)
    for m in EXTERN_RE.finditer(text):
        decl = _no_parameters(m.group(0))
        for n in names & set(re.findall(r"\b\w+\b", decl)):
            d = re.search(r"\b" + re.escape(n) + r"\s*\[([^\]]*)\]", m.group(0))
            if n not in out or out[n] is None:
                out[n] = d.group(1).strip() if d else None
    return out


def _enlarge(text: str, names: set[str]) -> str:
    """The first dimension of every extern declaration of ``names`` enlarged by one element."""
    def one(m):
        s = m.group(0)
        for n in names:
            s = re.sub(r"(\b" + re.escape(n) + r"\s*\[)([^\]]+)(\])", r"\1(\2)+1\3", s)
        return s
    return EXTERN_RE.sub(one, text)


def _object_image(obj) -> tuple:
    """Code/data bytes and fixups of an object, without debug information."""
    import modules as modmod
    segs = {sd["name"] for sd in obj.segment_defs if str(sd.get("class", "")).upper() not in modmod.DEBUG_CLASSES}
    return (sorted((n, bytes(b)) for n, b in obj.segments.items() if n in segs),
            sorted(json.dumps(f, sort_keys=True) for f in obj.linker_fixups if f["segment"] in segs))


def probe_declarations(man: dict, sources: dict[str, str], jobs: int = 8) -> dict:
    """Compiler evidence for the FAR_BSS declarations of accepted C modules (module docstring).
    Returns {"declaration": {name: [(bytes, module)]}, "pinned": {name: [(bytes, module)]},
    "failures": [...]} (C names)."""
    import compiler
    from concurrent.futures import ThreadPoolExecutor
    from omf import OmfReader
    import symbols as symmod
    names = {n for n, r in symmod.load()["data"].items() if r["seg"] == FAR_BSS_SEG}

    def compile_(text, m):
        flags = [f for f in m["flags"] if f.upper() != "/ZI"]
        r = compiler.compile_c(text, m["profile"], flags)
        return (OmfReader(communals=True).read(r.obj) if r.ok else None), r.log

    def one(key):
        m, text = man["modules"][key], sources[key]
        decl = _declared_names(text, names)
        measurable = sorted(n for n, d in decl.items() if d != "")
        res = {"declaration": [], "pinned": [], "failures": []}
        if not measurable:
            return res
        body = text.rstrip("\n") + "\n"
        first = body.count("\n") + 1                          # line number of the first probe line
        for _ in range(3):                                       # drop probe lines the compiler rejects
            lines = [f"unsigned near __fbss_probe_{i} = sizeof({n});" for i, n in enumerate(measurable)]
            obj, log = compile_(body + "\n".join(lines) + "\n", m)
            bad = {int(v) - first for v in re.findall(r"UNIT\.C\((\d+)\) : error", log)}
            if obj is not None or not bad or not all(0 <= i < len(measurable) for i in bad):
                break
            res["failures"].append(f"{key}: not measurable: {[measurable[i] for i in sorted(bad)]}")
            measurable = [n for i, n in enumerate(measurable) if i not in bad]
        if obj is None:
            res["failures"].append(f"{key}: size probe does not compile ({log.strip().splitlines()[-1:]})")
            return res
        pubs = {p["name"]: p for p in obj.publics}
        sizes = {}
        for i, n in enumerate(measurable):
            pb = pubs.get(f"___fbss_probe_{i}")
            if pb is not None:
                sizes[n] = struct.unpack_from("<H", obj.segments[pb["segment"]], pb["offset"])[0]
                res["declaration"].append((n, sizes[n]))
        arrays = {n for n in measurable if decl[n]}
        if not arrays:
            return res
        base, _ = compile_(text, m)
        big, _ = compile_(_enlarge(text, arrays), m)
        if base is None or big is None:
            res["failures"].append(f"{key}: enlarged-declaration probe does not compile")
            return res
        if _object_image(base) == _object_image(big):
            return res
        for n in sorted(arrays):
            one_big, _ = compile_(_enlarge(text, {n}), m)
            if one_big is not None and _object_image(one_big) != _object_image(base) and n in sizes:
                res["pinned"].append((n, sizes[n]))
        return res

    keys = sorted(k for k, m in man["modules"].items()
                  if m.get("lang", "c") == "c" and k in sources and _declared_names(sources[k], names))
    out = {"declaration": {}, "pinned": {}, "failures": [], "modules": len(keys)}
    with ThreadPoolExecutor(max_workers=jobs) as ex:
        for key, res in zip(keys, ex.map(one, keys)):
            for kind in ("declaration", "pinned"):
                for n, z in res[kind]:
                    out[kind].setdefault(n, []).append((z, key))
            out["failures"] += res["failures"]
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
            placements: list[tuple[int, int]] | None = None, probed: dict | None = None) -> dict:
    """``sources``: module key -> source text; ``comdefs``: C name -> [(bytes, module)] from
    freshly compiled accepted objects; ``placements``: (linear, size) of every placed segment;
    ``probed``: probe_declarations() (compiler-measured declarations replace the parser's)."""
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
    decl = probed["declaration"] if probed else declared_sizes(sources or {})
    pinned = (probed or {}).get("pinned", {})
    comd = comdefs or {}
    save = save_table_sizes()
    rows = []
    tot = {"verified": 0, "pinned": 0, "consistent": 0, "unverified": 0}
    for o in offs:
        n, gap = names[o], gaps[o]
        aliases = {n} | {a for a, r in symmod.load()["data"].items()
                         if r["seg"] == FAR_BSS_SEG and r["off"] == o}
        ev = []
        for a in aliases:
            ev += [("comdef", z, k) for z, k in comd.get(a, [])]
            ev += [("pinned", z, k) for z, k in pinned.get(a, [])]
            ev += [("declaration", z, k) for z, k in decl.get(a, [])]
        if o in save:
            ev.append(("save_table", save[o], "S27:4E4B"))
        status = "unverified"
        for kind, z, k in ev:
            if z > gap:
                msg = f"{n} (50F6:{o:04X}): {kind} size {z} in {k} exceeds the gap {gap} to the next variable"
                (failures if kind in ("comdef", "pinned") else warnings).append(msg)
            elif z == gap:
                if kind == "comdef":
                    status = "verified"
                elif kind == "pinned" and status != "verified":
                    status = "pinned"
                elif status == "unverified":
                    status = "consistent"
        tot[status] += gap
        rows.append({"name": n, "off": o, "size": gap, "status": status,
                     "evidence": [f"{kind}:{z}@{k}" for kind, z, k in ev]})
    return {"start": start, "size": end - start, "variables": len(offs), "accounted": not failures,
            "bytes_verified": tot["verified"], "bytes_pinned": tot["pinned"], "bytes_consistent": tot["consistent"],
            "bytes_unverified": tot["unverified"], "failures": failures, "warnings": warnings, "rows": rows}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--probe", action="store_true", help="measure declarations with the compiler (probe_declarations)")
    ap.add_argument("--jobs", type=int, default=8)
    a = ap.parse_args()
    import modules as modmod
    man = modmod.load_manifest()
    sources = {k: (ROOT / m["source"]).read_text(encoding="latin1") for k, m in man["modules"].items()
               if m.get("lang", "c") == "c"}
    probed = probe_declarations(man, sources, a.jobs) if a.probe else None
    r = account(sources, probed=probed)
    for f in (probed or {}).get("failures", []):
        print("  probe:", f)
    print(f"FAR_BSS {r['start']:05X}+{r['size']}: {r['variables']} variables; sizes verified {r['bytes_verified']}, "
          f"pinned {r['bytes_pinned']}, consistent {r['bytes_consistent']}, unverified {r['bytes_unverified']} bytes "
          f"(COMDEF evidence is added by validate.py from fresh objects"
          + ("; declarations measured by the compiler)" if probed else "; declarations parsed, --probe measures them)"))
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
