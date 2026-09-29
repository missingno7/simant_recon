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
FUNC_DEF_RE = re.compile(r"\b(?:far|near)\s+(?:_loadds\s+)?(?:__?cdecl\s+|_pascal\s+)?([A-Za-z_]\w*)\s*\([^;{]*\)\s*\{", re.S)


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
    for c in claims:
        name = c["name"]
        if name in scaff:
            out["claims"][name] = {"exact": False, "reasons": ["claimed function is inside SCAFFOLD block"]}
            all_ok = False
            continue
        pub = "_" + name
        seg = next((p["segment"] for p in obj.publics + getattr(obj, "local_publics", []) if p["name"] == pub), None)
        if seg is None:
            out["claims"][name] = {"exact": False, "reasons": [f"no public {pub}"]}
            all_ok = False
            continue
        t = match.Target(c["unit"], c["seg"], c["off"], c["size"])
        res = match.Binder(t, obj, seg, pub, placements).bind()
        orig = x.read(c["unit"], t.linear, t.size)
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
        dres = verify_data_segment(obj, segname, p)
        out.setdefault("data", {})[segname] = dres
        all_ok &= dres["exact"]
    ext = module.get("extent")
    if ext:
        tres = verify_extent(obj, ext, claims, scaff)
        out["extent"] = tres
        all_ok &= tres["exact"]
    out["exact"] = all_ok
    out["scaffold"] = sorted(scaff)
    return out


def verify_extent(obj, ext: dict, claims: list[dict], scaff: set) -> dict:
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
    return {"exact": not reasons, "reasons": reasons}


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


def verify_data_segment(obj, segname: str, p: dict) -> dict:
    """Bind a private data segment (CONST/_DATA) at its placement and compare with S27 bytes."""
    x = exemod.load()
    s27 = x.sections[27]
    body = bytearray(obj.segments[segname])
    start = p["seg"] * 16 + p["off"]
    size = p.get("size", len(body))
    body = body[:size]
    relocs_c = []
    reasons = []
    for f in obj.linker_fixups:
        if f["segment"] != segname or f["offset"] >= size:
            continue
        s = match.obj_name_lookup(f["target"]) if f["target_kind"] == "external" else None
        if f["loc"] == "base16" and s is not None:
            struct_pack(body, f["offset"], s["seg"])
            relocs_c.append(start + f["offset"])
        elif f["loc"] == "offset16" and s is not None:
            if f["frame_kind"] == "group":
                v = s["seg"] * 16 + s["off"] - match.DGROUP_SEG * 16
            else:
                v = s["off"]
            addend = int.from_bytes(bytes.fromhex(f["encoded_addend"]), "little")
            struct_pack(body, f["offset"], (v + addend) & 0xFFFF)
        else:
            reasons.append(f"unsupported data fixup {f['loc']} {f['target_kind']}:{f['target']}")
    orig = s27.data[start - s27.load_linear:start - s27.load_linear + size]
    exp = [sg * 16 + o for sg, o in s27.relocs if start <= sg * 16 + o < start + size]
    if bytes(body) != orig:
        reasons.append("data bytes differ")
    if exp != relocs_c:
        reasons.append(f"data relocations differ {len(relocs_c)} vs {len(exp)}")
    return {"exact": not reasons, "reasons": reasons, "size": size}


def struct_pack(buf: bytearray, at: int, v: int) -> None:
    buf[at:at + 2] = (v & 0xFFFF).to_bytes(2, "little")
