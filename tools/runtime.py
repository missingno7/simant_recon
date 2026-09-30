"""Accept authentic historical runtime library members (HISTORICAL_RUNTIME ownership).

    python tools/runtime.py verify            # bind every located member, report
    python tools/runtime.py accept            # verify and record accepted members in layout/manifest.json

A member is the complete OMF module from a pinned library file (hash in
layout/toolchain.json "libraries").  Its code segment is compared at the location
found by tools/libmatch.py, with every fixup bound:

* code targets (runtime publics, game code such as _main) through layout/symbols.json;
* DGROUP group frame -> 0x55B3;
* data targets (the member's own _DATA/CONST/_BSS/XI* segments and runtime data publics
  such as __iob) are *link placements*: they are derived from the original operand of each
  reference and must agree across every reference in every member (a placement anchored by
  one reference only is reported as SINGLE_ANCHOR).  Initialised data segments are then
  compared byte for byte, with their own fixups bound, at the derived placement.

The member's bytes outside fixup fields, its fixup kinds/targets and the relocation set
are never derived from the oracle.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import exe as exemod  # noqa: E402
import match  # noqa: E402
from omf import OmfReader  # noqa: E402

ROOT = exemod.ROOT
DGROUP = match.DGROUP_SEG
RUNTIME_FRAME = 0x29F4
LIBS = {"llibcr.lib": "C:/tools/msc-6.00/LIB/llibcr.lib", "libh.lib": "C:/tools/msc-6.00/LIB/libh.lib"}


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


ABSOLUTE = {"__AHINCR": 0x1000, "__AHSHIFT": 12}   # MSC huge-pointer constants (absolute publics)


def load_members():
    """(location, object, blob) per located member.  Libraries hold several modules with the
    same THEADR name (e.g. near and far LIBH helpers, two hmemcpy.asm); the one whose code
    segment has the located size and public set is chosen."""
    rd = OmfReader(communals=True)
    mods = defaultdict(list)
    for k, p in LIBS.items():
        for i, (n, b) in enumerate(rd.split_library(Path(p).read_bytes())):
            mods[(k, n)].append((i, b))
    loc = json.loads((ROOT / "evidence" / "toolchain" / "runtime-location.json").read_text())["members"]
    out = []
    seen = set()
    for m in loc:
        if (m["linear"], m["size"]) in seen:
            continue                      # same code located twice under another module name
        seen.add((m["linear"], m["size"]))
        cands = []
        for (lib, name), lst in mods.items():
            if lib != m["library"]:
                continue
            for i, blob in lst:
                obj = rd.read(blob, name)
                code = [s for s in obj.segment_defs if str(s.get("class", "")).upper().endswith("CODE")
                        and s["name"] in obj.segments]
                if code and len(obj.segments[code[0]["name"]]) == m["size"]:
                    # same-name modules first; siblings of the same size (e.g. alrem located as
                    # aldiv, because the locator wildcards call targets) only as a fallback.
                    cands.append((0 if name == m["member"] else 1, i, (dict(m, member=name, module_index=i), obj, blob)))
        if not cands:
            raise SystemExit(f"no library module matches located {m['member']}")
        cands.sort(key=lambda c: (c[0], c[1]))
        out.append([c[2] for c in cands if c[0] == 0] + [c[2] for c in cands if c[0] == 1])
    return out


def verify_all():
    x = exemod.load()
    s27 = x.sections[27]
    members = load_members()
    root_relocs = set(x.reloc_sites("root"))
    s27_relocs = {sg * 16 + o for sg, o in s27.relocs}
    # derived link placements: key -> {value: [(member, site)]}
    derived = defaultdict(lambda: defaultdict(list))
    results = []

    def oracle_word(lin):
        return struct.unpack_from("<H", x.image, lin)[0]

    for cands in members:
      best = None
      preferred = cands[0]["member"] if False else None
      for m, obj, blob in cands:
        if best is not None and not best["reasons"] and m["member"] != best["member"] and \
                best["member"] == cands[0][0]["member"]:
            continue                      # an exact same-name module wins; siblings are not tried
        segs = [s for s in obj.segment_defs if str(s.get("class", "")).upper().endswith("CODE")]
        seg = next((s["name"] for s in segs if s["name"] in obj.segments), None)
        start = m["linear"]
        body = bytearray(obj.segments[seg])
        reasons = []
        cand_relocs = []
        rkey = {}
        for f in obj.linker_fixups:
            if f["segment"] != seg:
                continue
            site = start + f["offset"]
            addend = int.from_bytes(bytes.fromhex(f["encoded_addend"]), "little")
            disp = f.get("displacement") or 0
            tk, tn = f["target_kind"], f["target"]
            loc = f["loc"]
            if f["self_relative"]:
                s = match.obj_name_lookup(tn) if tk == "external" else None
                if tk == "segment" and tn == seg:
                    tgt = start + addend + disp
                elif s and s["kind"] == "code" and s["unit"] == "root":
                    tgt = s["seg"] * 16 + s["off"]
                else:
                    reasons.append(f"unbound self-relative {tn}")
                    continue
                struct.pack_into("<H", body, f["offset"], (tgt - (site + 2)) & 0xFFFF)
                continue
            # resolve target (frame, offset-in-frame)
            s = match.obj_name_lookup(tn) if tk == "external" else None
            frame = off = None
            if tk == "external" and tn in ABSOLUTE:
                if loc != "offset16":
                    reasons.append(f"absolute {tn} in {loc}")
                    continue
                struct.pack_into("<H", body, f["offset"], (ABSOLUTE[tn] + addend + disp) & 0xFFFF)
                continue
            if tk == "group" and tn == "DGROUP":
                frame, off = DGROUP, 0
            elif tk == "segment" and tn == seg:
                frame, off = RUNTIME_FRAME, start - RUNTIME_FRAME * 16
            elif s is not None and s["kind"] == "code":
                frame, off = s["seg"], s["off"]
            elif s is not None and s["kind"] == "data":
                frame, off = s["seg"], s["off"]
            if loc in ("offset16", "pointer32"):
                if frame is not None:
                    if f["frame_kind"] == "group" and f["frame"] == "DGROUP":
                        v = frame * 16 + off - DGROUP * 16
                    else:
                        v = off
                    struct.pack_into("<H", body, f["offset"], (v + addend + disp) & 0xFFFF)
                else:
                    # data placement derived from the original operand, checked for consistency
                    ov = oracle_word(site)
                    base = (ov - addend - disp) & 0xFFFF
                    key = f"{'seg' if tk == 'segment' else 'ext'}:{m['member'] if tk == 'segment' else ''}:{tn}:{f['frame']}"
                    derived[key][base].append((m["member"], site))
                    struct.pack_into("<H", body, f["offset"], ov)
                if loc == "pointer32":
                    fr = frame if frame is not None else oracle_word(site + 2)
                    if frame is None:
                        derived[f"frame:{tn}"][fr].append((m["member"], site))
                    struct.pack_into("<H", body, f["offset"] + 2, fr)
                    cand_relocs.append(site + 2)
                    rkey[site + 2] = f"{tk}:{tn}"
            elif loc == "base16":
                fr = frame if frame is not None else oracle_word(site)
                if frame is None:
                    derived[f"frame:{tn}"][fr].append((m["member"], site))
                struct.pack_into("<H", body, f["offset"], fr)
                cand_relocs.append(site)
                rkey[site] = f"{tk}:{tn}"
            else:
                reasons.append(f"unsupported {loc}")
        orig = x.image[start:start + len(body)]
        if bytes(body) != orig:
            n = next(i for i in range(len(body)) if body[i] != orig[i])
            reasons.append(f"bytes differ at +{n:#x}")
        exp_ordered = [sg * 16 + o for sg, o in x.relocs if start <= sg * 16 + o < start + len(body)]
        exp = sorted(exp_ordered)
        if exp != sorted(cand_relocs):
            reasons.append(f"relocation set differs ({len(cand_relocs)} vs {len(exp)})")
        else:
            for g in set(rkey.values()):
                if [a for a in exp_ordered if rkey.get(a) == g] != [a for a in cand_relocs if rkey.get(a) == g]:
                    reasons.append(f"relocation order inside target group {g} differs from the object")
        row = {"library": m["library"], "member": m["member"], "module_index": m["module_index"],
               "linear": start, "size": len(body), "segment": seg, "member_sha256": sha(blob), "reasons": reasons,
               "publics": sorted(p["name"] for p in obj.publics if p["segment"] == seg),
               "alternatives": len(cands)}
        if not reasons:
            if best is None or best["reasons"]:
                best = row
            else:
                best.setdefault("aliases", []).append({"member": row["member"], "module_index": row["module_index"],
                                                       "publics": row["publics"]})
        elif best is None:
            best = row
      results.append(best)
    # placement consistency
    conflicts = {k: {hex(v): len(u) for v, u in vals.items()} for k, vals in derived.items() if len(vals) > 1}
    anchors = {k: sum(len(u) for u in vals.values()) for k, vals in derived.items()}
    bad_members = set()
    for k in conflicts:
        for vals in derived[k].values():
            for mem, _ in vals:
                bad_members.add(mem)
    for r in results:
        if r["member"] in bad_members:
            r["reasons"].append("inconsistent derived placement")
        r["exact"] = not r["reasons"]
    return results, derived, conflicts, anchors


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["verify", "accept"])
    a = ap.parse_args()
    results, derived, conflicts, anchors = verify_all()
    ok = [r for r in results if r["exact"]]
    print(f"members {len(results)}: exact {len(ok)} ({sum(r['size'] for r in ok)} bytes)")
    for r in results:
        if not r["exact"]:
            print(f"  FAIL {r['member']}: {'; '.join(r['reasons'][:3])}")
    if conflicts:
        print("placement conflicts:", json.dumps(conflicts)[:600])
    single = [k for k, n in anchors.items() if n == 1]
    print(f"derived placements {len(derived)}, single-anchor {len(single)}")
    out = ROOT / "build" / "runtime" / "verify.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"results": results, "conflicts": conflicts,
                               "placements": {k: {hex(v): [f"{m}@{s:05X}" for m, s in u] for v, u in vals.items()}
                                              for k, vals in derived.items()}}, indent=1))
    if a.cmd == "accept":
        from lockfile import CanonicalLock
        import modules as modmod
        with CanonicalLock():
            man = modmod.load_manifest()
            man["runtime"] = {"libraries": {k: {"path": p, "sha256": sha(Path(p).read_bytes())} for k, p in LIBS.items()},
                              "members": [{k: r[k] for k in ("library", "member", "module_index", "linear", "size",
                                                             "segment", "member_sha256")}
                                          for r in ok]}
            modmod.write_manifest(man)
        print(f"accepted {len(ok)} runtime members into layout/manifest.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
