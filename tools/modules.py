"""Module (translation-unit) sources and their strict verification.

Canonical game source is one C file per original code segment:
``src/<unit>/m<SEG>.c``.  A module file holds recovered functions in original
order; recovered functions are *claimed* in layout/manifest.json.

An explicitly delimited scaffold block may follow the recovered code:

    /* SCAFFOLD BEGIN: context only, not reconstruction */
    void far f_00DF_00E8(int a, int b, int c) { }
    /* SCAFFOLD END */

Scaffold functions exist only so MSC sees same-module callees as defined in the
TU (``push cs; call near``); they are never claimed and are reported as debt.
Claims inside the scaffold block are refused.

Module keys: ``UNIT:SEG`` is the (first) object of code frame SEG.  When LINK
combined several objects into one frame, every later object is its own module
``UNIT:SEG@OFF`` (OFF = the object's first byte as an offset in the frame, hex),
with source ``src/<unit>/m<SEG>_<OFF>.<ext>`` and ``"origin": OFF`` in the
manifest.  Its code must be linked at exactly that offset.

Code-segment data: a claim of kind ``DATA_IN_CODE`` covers bytes of the module's
code segment that are not a procedure (a buffer or table assembled into the code
segment).  Its bytes come from the candidate object at the module's placement
delta, its fixups are bound like code, and it is compared with the oracle; it
never lies inside a public's range and lets a complete TU tile such segments.

Data-only translation units: a file that defines far data and no code (e.g. the far
tables of frame 3D57) is the module ``data:FRAME`` (FRAME = its first far frame; a file
that MSC split at 64K into two segments stays one module), source ``src/data/dFRAME.c``.
It has placements and zero claims: every segment with bytes must be placed, it may not
contain code, every public must lie at its registered address, and ``link_after`` names
the module whose far data precedes it in the link ("" = the first far data of the
program).  A module with zero claims is reported as data only, never as recovered code.

Code addresses in data (rule DATAPTR-1, docs/exe-format.md): a far pointer or a near
offset (offset16) into the module's own code segment binds to the module frame at the
object's located origin (dispatch tables of S01-S03, near-proc tables of 16B5, 28BC,
S21); a far pointer to
a procedure of the same overlay section (or of the root) binds to its address, like a
same-section far call; into another overlay section it follows RTLink's vector when one
exists (the code binder's rule).  Several far segments of one module (FAR_DATA class) are
laid out in SEGDEF order and are contiguous up to paragraph link fill.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import compiler  # noqa: E402
import exe as exemod  # noqa: E402
import match  # noqa: E402
from omf import OmfReader  # noqa: E402

ROOT = exemod.ROOT
MANIFEST = ROOT / "layout" / "manifest.json"
SCAFFOLD_RE = re.compile(r"/\*\s*SCAFFOLD BEGIN.*?\*/(.*?)/\*\s*SCAFFOLD END\s*\*/", re.S)
FUNC_DEF_RE = re.compile(r"(?<![\w.])(?!(?:if|while|for|switch|return|sizeof)\b)([A-Za-z_]\w*)\s*\([^;{}()]*(?:\([^;{}()]*\)[^;{}()]*)*\)\s*\{", re.S)


KEY_RE = re.compile(r"^(\w+)[:;]([0-9A-Fa-f]{1,4})(?:@([0-9A-Fa-f]{1,4}))?$")
DATA_KIND = "DATA_IN_CODE"
DATA_UNIT = "data"          # data-only translation units: key data:FRAME
DEBUG_CLASSES = {"DEBSYM", "DEBTYP"}


def parse_key(s: str) -> tuple[str, int, int | None]:
    """``UNIT:SEG`` or ``UNIT:SEG@OFF`` -> (unit, seg, origin or None).  Git Bash may turn the
    colon into ';' (path-list conversion); that is undone here."""
    m = KEY_RE.match(s.strip())
    if not m:
        raise SystemExit(f"bad module key {s!r} (expected UNIT:SEG or UNIT:SEG@OFF)")
    origin = int(m.group(3), 16) if m.group(3) else None
    if m.group(1) == DATA_UNIT and m.group(3):
        raise SystemExit(f"module key {s!r}: a data-only module is keyed data:FRAME (its first far frame)")
    if origin == 0:
        raise SystemExit(f"module key {s!r}: the first object of a frame is keyed UNIT:SEG")
    return m.group(1), int(m.group(2), 16), origin


def module_key(unit: str, seg: int, origin: int | None = None) -> str:
    return f"{unit}:{seg:04X}" + (f"@{origin:04X}" if origin else "")


def module_source(unit: str, seg: int, origin: int | None, lang: str) -> str:
    """Canonical source path (relative to the repository root)."""
    if unit == DATA_UNIT:
        return f"src/data/d{seg:04X}" + (".asm" if lang == "asm" else ".c")
    return f"src/{unit}/m{seg:04X}" + (f"_{origin:04X}" if origin else "") + (".asm" if lang == "asm" else ".c")


def object_range(man: dict, unit: str, seg: int, origin: int | None) -> tuple[int, int]:
    """[lo, hi) frame offsets owned by the object ``unit:seg[@origin]``: from its origin to the
    origin of the next object of the same frame in the manifest."""
    lo = origin or 0
    later = [m.get("origin") or 0 for m in man["modules"].values()
             if m["unit"] == unit and m["seg"] == seg and (m.get("origin") or 0) > lo]
    return lo, min(later, default=0x10000)


def is_data_claim(c: dict) -> bool:
    return c.get("kind") == DATA_KIND


def is_data_module(m: dict) -> bool:
    """A data-only translation unit (key ``data:FRAME``)."""
    return m.get("unit") == DATA_UNIT


def segdef_length(sdef: dict) -> int:
    """SEGDEF length; a segment of exactly 64K has the B (big) bit and length field 0."""
    n = sdef.get("length") or 0
    return 0x10000 if sdef.get("big") and n == 0 else n


def segment_def(obj, segname: str) -> dict | None:
    return next((s for s in reversed(obj.segment_defs) if s["name"] == segname), None)


def segment_length(obj, segname: str) -> int:
    """True length of an object segment: its SEGDEF length (64K for big), at least its data."""
    sdef = segment_def(obj, segname)
    return max(len(obj.segments.get(segname, b"")), segdef_length(sdef) if sdef else 0)


def load_manifest() -> dict:
    if not MANIFEST.exists():
        return {"schema": "simant-manifest-v1", "oracle_sha256": exemod.EXPECTED_SHA256, "modules": {}}
    return json.loads(MANIFEST.read_text())


def scaffold_names(text: str) -> set[str]:
    names = set()
    for block in SCAFFOLD_RE.findall(text):
        names.update(FUNC_DEF_RE.findall(block))
    return names


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def verify_module(text: str, module: dict, claims: list[dict]) -> dict:
    """Compile ``text`` under the module profile and verify every claim strictly."""
    prof = module["profile"]
    flags = module["flags"]
    if module.get("lang") == "asm":
        r = compiler.assemble(text, prof, flags)
    else:
        r = compiler.compile_c(text, prof, flags)
    out = {"compile_ok": r.ok, "log": r.log[-600:] if not r.ok else "", "claims": {}, "exact": False}
    if not r.ok:
        return out
    obj = OmfReader(communals=True).read(r.obj)
    out["object_sha256"] = sha(r.obj)
    scaff = scaffold_names(text)
    placements = {k: {"seg": v["seg"], "off": v["off"]} for k, v in module.get("placements", {}).items()}
    all_ok = True
    x = exemod.load()
    site_key, site_index = {}, {}
    if is_data_module(module) and claims:
        # a data-only translation unit owns placements, never code or claims
        for c in claims:
            out["claims"][c["name"]] = {"exact": False, "reasons": ["a data-only module has no claims"]}
        all_ok = False
        claims = []
    # where the object lies in its frame: frame offset - object offset of each code claim
    located = {}
    for c in claims:
        if not is_data_claim(c) and c["name"] not in scaff:
            pub, prec = match.public_in(obj, c["name"])
            if prec is not None:
                located[c["name"]] = (pub, prec["segment"], c["off"] - prec["offset"])
    deltas = {(s, d) for _, s, d in located.values()}
    data_claims = [c for c in claims if is_data_claim(c)]
    stops, data_spans = {}, {}
    if data_claims:
        # code-segment data is located through the module placement: the origin of a later
        # object of a frame, otherwise the single (segment, delta) shared by the code claims
        segs_d = {s for s, _ in deltas}
        dset = {d for _, d in deltas} | ({module["origin"]} if module.get("origin") else set())
        if len(segs_d) != 1 or len(dset) != 1:
            for c in data_claims:
                out["claims"][c["name"]] = {"exact": False, "reasons": [
                    f"code-segment data needs one code segment and placement delta, have {sorted(deltas)}"]}
            all_ok = False
            data_claims = []
        else:
            dseg, delta = segs_d.pop(), dset.pop()
            for c in data_claims:
                data_spans[c["name"]] = (c["off"] - delta, c["off"] - delta + c["size"])
                stops.setdefault(dseg, []).append(c["off"] - delta)
    for c in claims:
        name = c["name"]
        if is_data_claim(c):
            continue
        if name in scaff:
            out["claims"][name] = {"exact": False, "reasons": ["claimed function is inside SCAFFOLD block"]}
            all_ok = False
            continue
        pub, prec = match.public_in(obj, name)
        seg = prec["segment"] if prec else None
        if seg is None:
            out["claims"][name] = {"exact": False, "reasons": [f"no public {pub}"]}
            all_ok = False
            continue
        if module.get("origin") is not None and located[name][2] != module["origin"]:
            out["claims"][name] = {"exact": False, "reasons": [
                f"object linked at frame offset {located[name][2]:04X}, module origin is {module['origin']:04X}"]}
            all_ok = False
            continue
        t = match.Target(c["unit"], c["seg"], c["off"], c["size"])
        res = match.Binder(t, obj, seg, pub, placements, stops=stops.get(seg)).bind()
        site_key.update(res.reloc_key)
        site_index.update(res.reloc_index)
        orig = x.read(c["unit"], t.linear, t.size)
        if (not res.exact and not module.get("extent") and res.reasons
                and all(r.startswith("relocation order inside a target group") for r in res.reasons)):
            # Partial module: record boundaries (hence within-group order) depend on the size of
            # earlier, not yet exact code.  Accept as a lower proof level; a complete-TU claim
            # (--extent) requires the exact within-group order.
            res.exact = True
            res.reloc_order = "WITHIN_GROUP_PENDING"
            res.reasons = []
        ok = res.exact and sha(orig) == c["target_sha256"]
        out["claims"][name] = {"exact": ok, "reasons": res.reasons, "fixups": len(res.fixups),
                               "relocations": len(res.relocs_expected), "reloc_order": res.reloc_order}
        all_ok &= ok
    for c in data_claims:
        # code-segment data (buffers, tables): the object's own bytes at the module placement,
        # fixups bound like code, compared with the oracle; never inside a public's range
        dseg = next(iter(stops))
        s0, s1 = data_spans[c["name"]]
        reasons = []
        inside = [p["name"] for p in obj.publics + getattr(obj, "local_publics", [])
                  if p["segment"] == dseg and s0 <= p["offset"] < s1]
        if inside:
            reasons.append(f"code-segment data covers publics {inside[:4]}")
        if s0 < 0 or s1 > len(obj.segments.get(dseg, b"")):
            reasons.append(f"code-segment data {s0:#x}-{s1:#x} outside the object segment")
        t = match.Target(c["unit"], c["seg"], c["off"], c["size"])
        res = match.Binder(t, obj, dseg, None, placements, span=(s0, s1)).bind() if not reasons else None
        if res is not None:
            site_key.update(res.reloc_key)
            site_index.update(res.reloc_index)
            if (not res.exact and not module.get("extent") and res.reasons
                    and all(r.startswith("relocation order inside a target group") for r in res.reasons)):
                res.exact, res.reloc_order, res.reasons = True, "WITHIN_GROUP_PENDING", []
            reasons += res.reasons
        orig = x.read(c["unit"], t.linear, t.size)
        if sha(orig) != c["target_sha256"]:
            reasons.append("oracle bytes differ from the claim's target hash")
        ok = not reasons and res.exact
        out["claims"][c["name"]] = {"exact": ok, "reasons": reasons, "kind": DATA_KIND,
                                    "fixups": len(res.fixups) if res else 0,
                                    "relocations": len(res.relocs_expected) if res else 0,
                                    "reloc_order": res.reloc_order if res else "?"}
        all_ok &= ok
    # the module's own code segments: a far pointer or near offset in its data to one of them
    # binds to the module frame at the located object origin (dispatch tables of the display
    # drivers, near-proc tables of 16B5/28BC/S21)
    own_code = {}
    for sname in {s for s, _ in deltas}:
        ds = {d for s, d in deltas if s == sname}
        if len(ds) == 1:
            own_code[sname] = {"seg": module["seg"], "off": ds.pop()}
    # private data placements must reproduce the oracle bytes they claim
    for segname, p in module.get("placements", {}).items():
        body = obj.segments.get(segname)
        sdef = segment_def(obj, segname)
        if body is None and sdef is not None and str(sdef.get("class", "")).upper() == "BSS":
            dres = verify_bss_placement(sdef, p)
            out.setdefault("data", {})[segname] = dres
            all_ok &= dres["exact"]
            continue
        if body is None and (sdef is None or not segdef_length(sdef)):
            out.setdefault("data", {})[segname] = {"exact": False, "reasons": ["segment absent"]}
            all_ok = False
            continue
        dres = verify_data_segment(obj, segname, p, placements, own_code=own_code, unit=module.get("unit"))
        if (not dres["exact"] and not module.get("extent") and dres["reasons"]
                and all(r.startswith("data relocation order inside target group") for r in dres["reasons"])):
            dres.update(exact=True, reasons=[], reloc_order="WITHIN_GROUP_PENDING")
        seglen = segment_length(obj, segname)
        if p.get("size", seglen) != seglen:
            dres["exact"] = False
            dres.setdefault("reasons", []).append(
                f"placement size {p.get('size')} != segment length {seglen} (claimed code could use unverified data)")
        out.setdefault("data", {})[segname] = dres
        all_ok &= dres["exact"]
    # module-level data rules: far segment order/contiguity, public addresses, data-only TUs
    mreasons = placement_order_reasons(obj, module.get("placements", {}))
    mreasons += public_address_reasons(obj, module.get("placements", {}), strict=is_data_module(module))
    if is_data_module(module):
        mreasons += data_module_reasons(obj, module, claims)
    elif not claims and not module.get("placements"):
        mreasons.append("a module without claims must have placements")
    out["data_only"] = not claims
    out["communals"] = [{"name": c["name"], "kind": c["kind"], "length": c["length"]}
                        for c in getattr(obj, "communals", [])]
    if mreasons:
        out["module_reasons"] = mreasons
        all_ok = False
    ext = module.get("extent")
    if ext:
        tres = verify_extent(obj, ext, claims, scaff, site_key, site_index)
        out["extent"] = tres
        all_ok &= tres["exact"]
    out["exact"] = all_ok
    out["scaffold"] = sorted(scaff)
    # functions compiled into the module that are neither claimed nor in a SCAFFOLD block
    # (e.g. drafts kept in place for data order): unverified code, reported as debt
    claimed = {c["name"] for c in claims}

    def undecorated(n: str) -> str:
        return n[1:] if n[:1] in ("_", "@") else n

    code_segs = {p["segment"] for p in obj.publics if undecorated(p["name"]) in claimed}
    out["inplace_drafts"] = sorted(undecorated(p["name"]) for p in obj.publics
                                   if p["segment"] in code_segs and undecorated(p["name"]) not in claimed
                                   and undecorated(p["name"]) not in scaff)
    return out


def verify_extent(obj, ext: dict, claims: list[dict], scaff: set, site_key: dict | None = None,
                  site_index: dict | None = None) -> dict:
    """Complete translation unit: the claims tile the whole original code segment.

    The compiled code segment must have exactly ``end - start`` bytes, contain no
    scaffold, and every byte must be covered by a (separately verified) claim -- a
    procedure or explicit code-segment data (DATA_IN_CODE) -- except a trailing MSC
    word-alignment pad that must equal the oracle byte.
    """
    reasons = []
    if scaff:
        reasons.append("scaffold present")
    start, end = ext["start"], ext["end"]
    names = {c["name"] for c in claims if not is_data_claim(c)}     # code-segment data has no public
    segs = {p["segment"] for p in obj.publics if p["name"][1:] in names}
    if len(segs) != 1:
        return {"exact": False, "reasons": reasons + [f"claims span segments {sorted(segs)}"]}
    seg = segs.pop()
    body = bytes(obj.segments.get(seg, b""))
    if len(body) != end - start:
        reasons.append(f"segment length {len(body)} != extent {end - start}")
    if {p["name"][1:] for p in obj.publics if p["segment"] == seg} != names:
        reasons.append("segment publics differ from claims")
    pos = start
    for a, b in sorted((c["seg"] * 16 + c["off"], c["seg"] * 16 + c["off"] + c["size"]) for c in claims):
        if a != pos:
            reasons.append(f"gap/overlap at {pos:05X}")
            break
        pos = b
    if pos != end:
        tail = exemod.load().read(claims[0]["unit"], pos, end - pos)
        if not (end - pos == 1 and body[-1:] == tail == bytes([0x90])):
            reasons.append(f"uncovered tail {pos:05X}-{end:05X}")
    # Cross-function relocation order is a separate proof level: bytes and per-function order are
    # already gated per claim; a complete TU whose record breaks between functions differ from the
    # original (e.g. a wrong /Zd-/Zi choice or source line layout) is reported, not hidden.
    reasons += extent_tail_reasons(claims[0]["unit"], end, claims[0]["seg"])
    order = extent_reloc_order(claims[0]["unit"], start, end, site_key or {}, site_index or {})
    if order["order"] == "SET_MISMATCH":
        reasons += order["reasons"]
    elif order["reasons"]:
        order["order"] = "CROSS_FUNCTION_PENDING"
    return {"exact": not reasons, "reasons": reasons, "reloc_order": order["order"],
            "order_reasons": order["reasons"]}


def extent_tail_reasons(unit: str, end: int, seg: int | None = None) -> list[str]:
    """The bytes between the extent end and the next known function must be link fill (00),
    so an extent cannot silently stop before a trailing function of the same frame (worker
    ovlB, S20).  When the next function belongs to another code frame, the gap is that
    module's leading bytes (e.g. 2650's mask table after 25E7) and is owned by its extent."""
    import functions as fnmod
    rows = sorted((r["seg"] * 16 + r["off"], r["seg"]) for r in fnmod.table()["functions"] if r["unit"] == unit)
    nxt, nseg = next(((a, s) for a, s in rows if a >= end), (None, None))
    if nxt is None or nxt == end:
        return []
    if seg is not None and nseg != seg:
        return []
    if nxt - end >= 16:
        return []          # a data/unknown gap, not module padding; the extent must be reviewed separately
    gap = exemod.load().read(unit, end, nxt - end)
    if any(gap):
        return [f"bytes after extent end {end:05X} up to next function {nxt:05X} are not fill: {gap.hex()}"]
    return []


def extent_reloc_order(unit: str, start: int, end: int, site_key: dict, site_index: dict) -> dict:
    """Relocation order of a complete TU across function boundaries.

    Per-claim checks see only the relocations inside one function.  RTLink groups relocations
    by target and keeps the object's FIXUPP order inside each group, so for a complete module
    the order inside every group must equal the object order over the whole segment (record
    breaks between functions, e.g. /Zd vs /Zi, show up only here)."""
    x = exemod.load()
    exp = [s * 16 + o for s, o in x.unit_relocs(unit) if start <= s * 16 + o < end]
    cand = sorted(site_index, key=lambda a: (site_index[a], a))
    if sorted(exp) != sorted(cand):
        return {"order": "SET_MISMATCH", "reasons": [f"extent relocation set differs ({len(cand)} vs {len(exp)})"]}
    if exp == cand:
        return {"order": "EXACT", "reasons": []}
    bad = [g for g in sorted(set(site_key.values()))
           if [a for a in exp if site_key.get(a) == g] != [a for a in cand if site_key.get(a) == g]]
    if bad:
        return {"order": "WITHIN_GROUP_MISMATCH",
                "reasons": [f"cross-function relocation order inside target group {g} differs" for g in bad[:4]]}
    return {"order": "GROUPED", "reasons": []}


def verify_bss_placement(sdef: dict, p: dict) -> dict:
    """A private _BSS placement has no file bytes to compare.  Require that it lies in
    DGROUP's uninitialised tail (beyond section 27's file data) and that its size is the
    SEGDEF length.  Its address is proven only by the code operands that bind to it; the
    placement within the BSS link order stays a hypothesis until the historical link."""
    x = exemod.load()
    s27 = x.sections[27]
    start = p["seg"] * 16 + p["off"]
    reasons = []
    if start < s27.load_linear + len(s27.data) - 3:
        reasons.append("BSS placement overlaps initialised data")
    if start + sdef["length"] > s27.load_linear + s27.mem_paras * 16:
        reasons.append("BSS placement beyond DGROUP memory")
    if p.get("size", sdef["length"]) != sdef["length"]:
        reasons.append(f"BSS size {sdef['length']} != placement {p.get('size')}")
    return {"exact": not reasons, "reasons": reasons, "size": sdef["length"], "kind": "BSS"}


def _data_target(f: dict, placements: dict, unit: str | None = None):
    """(frame, offset-in-frame) of a data fixup target, or None.

    Segment targets: the module's placed segments and its own code segments (``placements``
    carries both).  Code externals (rule DATAPTR-1): root and same-section procedures are
    addressed directly (the S00-S03 dispatch tables in DGROUP point into their own overlay
    frames; no S27 pointer addresses the vector table); a procedure of *another* overlay
    section goes through its RTLink vector when RTLink built one, else it is addressed
    directly, exactly like a far call in code (match.Binder)."""
    tk, tn = f["target_kind"], f["target"]
    if tk == "group" and tn == "DGROUP":
        return match.DGROUP_SEG, 0
    if tk == "segment":
        pl = placements.get(tn)
        if pl is None:
            return None
        return pl["seg"], pl["off"]
    s = match.obj_name_lookup(tn) if tk == "external" else None
    if s is None:
        return None
    if s["kind"] == "code" and s.get("unit", "root") not in ("root", unit):
        v = match.vector_for(s["unit"], s["seg"], s["off"])
        if v is not None:
            return exemod.MANAGER_SEG, v.offset
    return s["seg"], s["off"]


def verify_data_segment(obj, segname: str, p: dict, placements: dict | None = None,
                        own_code: dict | None = None, unit: str | None = None) -> dict:
    """Bind a private data segment (CONST/_DATA/far data) at its placement and compare with
    S27 bytes.

    Supported fixups: base16 (segment words), offset16 (near/DGROUP or in-frame offsets) and
    pointer32 (far pointers: code, far data, this module's own placed segments and its own
    code segments ``own_code`` {segname: {"seg": frame, "off": origin}}).  The segment length
    is its SEGDEF length (a 64K segment has the big bit and length 0); bytes the object does
    not initialise are the linker's zero fill."""
    placements = {**(own_code or {}), **(placements or {})}
    placements.setdefault(segname, p)
    x = exemod.load()
    s27 = x.sections[27]
    seglen = segment_length(obj, segname)
    body = bytearray(obj.segments.get(segname, b""))
    body += bytes(seglen - len(body))
    start = p["seg"] * 16 + p["off"]
    size = p.get("size", seglen)
    body = body[:size]
    relocs_c = []
    rkey = {}
    reasons = []
    sdef = segment_def(obj, segname) or {}
    if not (s27.load_linear <= start and start + size <= s27.load_linear + len(s27.data)):
        return {"exact": False, "reasons": [f"placement {start:05X}+{size} outside section 27's file data"],
                "size": size, "start": start}
    for f in obj.linker_fixups:
        if f["segment"] != segname or f["offset"] >= size:
            continue
        tgt = _data_target(f, placements, unit)
        if tgt is None or f["self_relative"]:
            reasons.append(f"unsupported data fixup {f['loc']} {f['target_kind']}:{f['target']}")
            continue
        frame, off = tgt
        addend = int.from_bytes(bytes.fromhex(f["encoded_addend"]), "little")
        disp = f.get("displacement") or 0
        if f["frame_kind"] == "group" and f["frame"] == "DGROUP":
            value = frame * 16 + off - match.DGROUP_SEG * 16
            base = match.DGROUP_SEG
        else:
            value = off
            base = frame
        at = f["offset"]
        key = f"{f['target_kind']}:{f['target']}"
        if f["loc"] == "base16":
            struct_pack(body, at, frame)
            relocs_c.append(start + at)
            rkey[start + at] = key
        elif f["loc"] == "offset16":
            struct_pack(body, at, (value + addend + disp) & 0xFFFF)
        elif f["loc"] == "pointer32":
            struct_pack(body, at, (value + addend + disp) & 0xFFFF)
            if at + 2 < size:
                struct_pack(body, at + 2, base)
            relocs_c.append(start + at + 2)
            rkey[start + at + 2] = key
        else:
            reasons.append(f"unsupported data fixup {f['loc']} {key}")
    orig = s27.data[start - s27.load_linear:start - s27.load_linear + size]
    exp = [sg * 16 + o for sg, o in s27.relocs if start <= sg * 16 + o < start + size]
    if bytes(body) != orig:
        reasons.append("data bytes differ")
    order = "EXACT"
    if sorted(exp) != sorted(relocs_c):
        reasons.append(f"data relocation set differs {len(relocs_c)} vs {len(exp)}")
    elif exp != relocs_c:
        # same RTLink grouping as code relocations: object order inside each target group
        # is required, the between-group order is a linker property (docs/exe-format.md)
        for g in set(rkey.values()):
            if [a for a in exp if rkey.get(a) == g] != [a for a in relocs_c if rkey.get(a) == g]:
                reasons.append(f"data relocation order inside target group {g} differs")
        order = "GROUPED"
    return {"exact": not reasons, "reasons": reasons, "size": size, "reloc_order": order, "start": start,
            "class": str(sdef.get("class", "")), "align": sdef.get("alignment"), "far": p["seg"] != match.DGROUP_SEG}


def _far_class(sdef: dict | None) -> bool:
    return sdef is not None and str(sdef.get("class", "")).upper() == "FAR_DATA"


def placement_order_reasons(obj, placements: dict) -> list[str]:
    """Far segments of one object (class FAR_DATA, e.g. UNIT7_DATA and UNIT8_DATA of a file MSC
    split at 64K) are laid out by the linker in SEGDEF order, each paragraph aligned right after
    the previous one: the gap may only be paragraph fill (zero bytes, checked by validate)."""
    far = [(sd["index"], sd["name"]) for sd in obj.segment_defs
           if sd["name"] in placements and _far_class(sd)]
    reasons = []
    prev = None
    for _, name in sorted(far):
        p = placements[name]
        start = p["seg"] * 16 + p["off"]
        if prev is not None:
            pname, pend = prev
            want = (pend + 15) & ~15
            if start != want:
                reasons.append(f"far segment {name} at {start:05X}: after {pname} (SEGDEF order) it must "
                               f"start at {want:05X} (segment order / contiguity)")
            elif any(exemod.load().read("S27", pend, start - pend)):
                reasons.append(f"bytes between far segments {pname} and {name} are not link fill")
        prev = (name, start + p.get("size", segment_length(obj, name)))
    return reasons


def public_address_reasons(obj, placements: dict, strict: bool = False) -> list[str]:
    """Publics defined in placed data segments define the addresses other modules bind to:
    a registered name must sit at its registered address.  ``strict`` (data-only modules):
    every such public must also be registered."""
    reasons = []
    for pb in obj.publics:
        p = placements.get(pb["segment"])
        if p is None:
            continue
        lin = p["seg"] * 16 + p["off"] + pb["offset"]
        s = match.obj_name_lookup(pb["name"])
        if s is None:
            if strict:
                reasons.append(f"public {pb['name']} at {lin:05X} is not a registered data symbol")
            continue
        if s["kind"] != "data" or s["seg"] * 16 + s["off"] != lin:
            reasons.append(f"public {pb['name']} at {lin:05X}, registered at {s['seg']:04X}:{s['off']:04X}")
    return reasons


def data_module_reasons(obj, module: dict, claims: list) -> list[str]:
    """A data-only translation unit: no claims, no code, every segment with bytes placed."""
    reasons = []
    if claims:
        reasons.append("a data-only module has no claims")
    places = module.get("placements", {})
    if not places:
        reasons.append("a data-only module needs placements")
    for sd in obj.segment_defs:
        n, cls = sd["name"], str(sd.get("class", "")).upper()
        if cls in DEBUG_CLASSES:
            continue
        length = segment_length(obj, n)
        if cls.endswith("CODE") and length:
            reasons.append(f"data-only module has code ({n}, {length} bytes)")
        elif length and n not in places:
            reasons.append(f"segment {n} ({cls}, {length} bytes) is not placed")
    if "link_after" not in module:
        reasons.append("a data-only module records its link position (link_after)")
    return reasons


def far_placements(module: dict) -> list[tuple[int, int, str]]:
    """(linear start, size, segname) of a manifest module's far (non-DGROUP) placements."""
    return sorted((p["seg"] * 16 + p["off"], p.get("size", 0), n)
                  for n, p in module.get("placements", {}).items() if p["seg"] != match.DGROUP_SEG)


def link_after_reasons(man: dict, key: str, module: dict) -> list[str]:
    """``link_after``: the module whose far data immediately precedes this module's first far
    segment in the link ("" = the first far data of the program, section 27's start).  The gap
    may only be paragraph fill.  This is the link-order position of a module without code."""
    if "link_after" not in module:
        return []
    la = module["link_after"]
    mine = far_placements(module)
    if not mine:
        return ["link_after is recorded but the module has no far placement"]
    x = exemod.load()
    s27 = x.sections[27]
    start = mine[0][0]
    if la == "":
        return [] if start == s27.load_linear else [
            f"first far data of the program must start at {s27.load_linear:05X}, not {start:05X}"]
    prev = man["modules"].get(la)
    if prev is None:
        return [f"link_after {la}: no such module in the manifest"]
    theirs = far_placements(prev)
    if not theirs:
        return [f"link_after {la}: that module has no far placement"]
    end = max(a + n for a, n, _ in theirs)
    if start != (end + 15) & ~15 or start < end:
        return [f"link_after {la}: its far data ends at {end:05X}, this module starts at {start:05X}"]
    gap = x.read("S27", end, start - end)
    if any(gap):
        return [f"link_after {la}: bytes between {end:05X} and {start:05X} are not link fill"]
    return []


def placement_overlap_reasons(man: dict, key: str) -> list[str]:
    """No two modules place the same bytes (every placement has one owner)."""
    mine = [(p["seg"] * 16 + p["off"], p.get("size", 0), n)
            for n, p in man["modules"][key].get("placements", {}).items()]
    reasons = []
    for k, m in man["modules"].items():
        if k == key:
            continue
        for n2, p in m.get("placements", {}).items():
            a0, a1 = p["seg"] * 16 + p["off"], p["seg"] * 16 + p["off"] + p.get("size", 0)
            for b0, size, n in mine:
                if a0 < b0 + size and b0 < a1:
                    reasons.append(f"placement {n} {b0:05X}+{size} overlaps {k} {n2} {a0:05X}+{a1 - a0}")
    return reasons


def struct_pack(buf: bytearray, at: int, v: int) -> None:
    buf[at:at + 2] = (v & 0xFFFF).to_bytes(2, "little")


def write_manifest(man: dict) -> None:
    """Atomic replace, so concurrent readers never see a partial manifest."""
    from lockfile import atomic_write_text
    atomic_write_text(MANIFEST, json.dumps(man, indent=1) + "\n")
