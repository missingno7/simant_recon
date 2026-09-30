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
    for c in claims:
        name = c["name"]
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
        t = match.Target(c["unit"], c["seg"], c["off"], c["size"])
        res = match.Binder(t, obj, seg, pub, placements).bind()
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
    # private data placements must reproduce the oracle bytes they claim
    for segname, p in module.get("placements", {}).items():
        body = obj.segments.get(segname)
        sdef = next((s for s in obj.segment_defs if s["name"] == segname), None)
        if body is None and sdef is not None and str(sdef.get("class", "")).upper() == "BSS":
            dres = verify_bss_placement(sdef, p)
            out.setdefault("data", {})[segname] = dres
            all_ok &= dres["exact"]
            continue
        if body is None:
            out.setdefault("data", {})[segname] = {"exact": False, "reasons": ["segment absent"]}
            all_ok = False
            continue
        dres = verify_data_segment(obj, segname, p, placements)
        if (not dres["exact"] and not module.get("extent") and dres["reasons"]
                and all(r.startswith("data relocation order inside target group") for r in dres["reasons"])):
            dres.update(exact=True, reasons=[], reloc_order="WITHIN_GROUP_PENDING")
        if p.get("size", len(body)) != len(body):
            dres["exact"] = False
            dres.setdefault("reasons", []).append(
                f"placement size {p.get('size')} != segment length {len(body)} (claimed code could use unverified data)")
        out.setdefault("data", {})[segname] = dres
        all_ok &= dres["exact"]
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
    code_segs = {p["segment"] for p in obj.publics if p["name"].lstrip("_@") in claimed}
    out["inplace_drafts"] = sorted(p["name"].lstrip("_@") for p in obj.publics
                                   if p["segment"] in code_segs and p["name"].lstrip("_@") not in claimed
                                   and p["name"].lstrip("_@") not in scaff)
    return out


def verify_extent(obj, ext: dict, claims: list[dict], scaff: set, site_key: dict | None = None,
                  site_index: dict | None = None) -> dict:
    """Complete translation unit: the claims tile the whole original code segment.

    The compiled code segment must have exactly ``end - start`` bytes, contain no
    scaffold, and every byte must be covered by a (separately verified) claim,
    except a trailing MSC word-alignment pad that must equal the oracle byte.
    """
    reasons = []
    if scaff:
        reasons.append("scaffold present")
    start, end = ext["start"], ext["end"]
    names = {c["name"] for c in claims}
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
    reasons += extent_tail_reasons(claims[0]["unit"], end)
    order = extent_reloc_order(claims[0]["unit"], start, end, site_key or {}, site_index or {})
    if order["order"] == "SET_MISMATCH":
        reasons += order["reasons"]
    elif order["reasons"]:
        order["order"] = "CROSS_FUNCTION_PENDING"
    return {"exact": not reasons, "reasons": reasons, "reloc_order": order["order"],
            "order_reasons": order["reasons"]}


def extent_tail_reasons(unit: str, end: int) -> list[str]:
    """The bytes between the extent end and the next known function must be link fill (00),
    so an extent cannot silently stop before a trailing function (worker ovlB, S20)."""
    import functions as fnmod
    starts = sorted(r["seg"] * 16 + r["off"] for r in fnmod.table()["functions"] if r["unit"] == unit)
    nxt = next((a for a in starts if a >= end), None)
    if nxt is None or nxt == end:
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


def _data_target(f: dict, placements: dict):
    """(frame, offset-in-frame) of a data fixup target, or None."""
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
    if s["kind"] == "code" and s.get("unit", "root") != "root":
        v = match.vector_for(s["unit"], s["seg"], s["off"])
        if v is None:
            return None
        return exemod.MANAGER_SEG, v.offset
    return s["seg"], s["off"]


def verify_data_segment(obj, segname: str, p: dict, placements: dict | None = None) -> dict:
    """Bind a private data segment (CONST/_DATA) at its placement and compare with S27 bytes.

    Supported fixups: base16 (segment words), offset16 (near/DGROUP or in-frame offsets) and
    pointer32 (far pointers: code, far data, or this module's own placed segments)."""
    placements = dict(placements or {})
    placements.setdefault(segname, p)
    x = exemod.load()
    s27 = x.sections[27]
    body = bytearray(obj.segments[segname])
    start = p["seg"] * 16 + p["off"]
    size = p.get("size", len(body))
    body = body[:size]
    relocs_c = []
    rkey = {}
    reasons = []
    for f in obj.linker_fixups:
        if f["segment"] != segname or f["offset"] >= size:
            continue
        tgt = _data_target(f, placements)
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
    return {"exact": not reasons, "reasons": reasons, "size": size, "reloc_order": order}


def struct_pack(buf: bytearray, at: int, v: int) -> None:
    buf[at:at + 2] = (v & 0xFFFF).to_bytes(2, "little")


def write_manifest(man: dict) -> None:
    """Atomic replace, so concurrent readers never see a partial manifest."""
    from lockfile import atomic_write_text
    atomic_write_text(MANIFEST, json.dumps(man, indent=1) + "\n")
