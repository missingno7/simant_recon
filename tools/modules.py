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
                               "relocations": len(res.relocs_expected)}
        all_ok &= ok
    # private data placements must reproduce the oracle bytes they claim
    for segname, p in module.get("placements", {}).items():
        body = obj.segments.get(segname)
        if body is None:
            out.setdefault("data", {})[segname] = {"exact": False, "reasons": ["segment absent"]}
            all_ok = False
            continue
        dres = verify_data_segment(obj, segname, p)
        out.setdefault("data", {})[segname] = dres
        all_ok &= dres["exact"]
    out["exact"] = all_ok
    out["scaffold"] = sorted(scaff)
    return out


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
