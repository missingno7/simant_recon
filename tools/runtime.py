"""Accept authentic historical runtime library members (HISTORICAL_RUNTIME ownership).

    python tools/runtime.py verify            # bind every located member, report
    python tools/runtime.py accept            # verify and record accepted members in layout/manifest.json

A member is the complete OMF module from a pinned library file (hash in
layout/toolchain.json "libraries").  Its code segment is compared at the location
found by tools/libmatch.py, with every fixup bound:

* every code segment of the member that has bytes is compared: the first at the member's
  location in _TEXT (frame 29F4), further ones (e.g. crt0dat's EMULATOR_TEXT) at the
  location recorded in runtime-location.json "segments" (frame = their own paragraph); an
  unlocated code segment fails the member;
* code targets (runtime publics, game code such as _main or the game's malloc/free) only
  through layout/symbols.json.  An external that a pinned library defines in a CODE segment,
  or that no pinned library defines (and that is not a linker-defined DGROUP symbol), must be
  registered; the original operand never supplies a code binding;
* absolute publics (ABSOLUTE) by their value, cross-checked against the library definition;
* DGROUP group frame -> 0x55B3;
* data targets (the member's own _DATA/CONST/_BSS/XI*/EMULATOR_DATA segments, runtime data
  publics such as __iob, linker-defined _edata/_end) are *link placements*: they are derived
  from the original operand of each reference and must agree across every reference in every
  member (a placement anchored by one reference only is reported as SINGLE_ANCHOR).

The member's bytes outside fixup fields, its fixup kinds/targets and the relocation set
are never derived from the oracle.

Runtime DGROUP data (``verify_data``): every non-empty DGROUP segment of an exact member
(NULL, _DATA, DBDATA, CDATA, XI*, HDR/MSG/PAD/EPAD; BSS and STACK have no file bytes) and
of the *data-only* members whose publics the code references (``_file.c`` __iob,
``ctype.asm`` __ctype) is placed by one of these rules, then its bytes, fixups and
relocations are verified against section 27 exactly like a game data placement:

* REFERENCED: the segment's derived link placement (references to the segment itself);
* REFERENCED_PUBLIC: a public of the segment is referenced (derived placement of the
  public minus its offset; all referenced publics of the segment must agree);
* DOSSEG_BEGDATA: class BEGDATA (the NULL segment) is the first segment of DGROUP (offset 0);
* CLASS_SEQUENCE: the MSG class is laid out by the linker rule: segments in order of first
  appearance in member link order (= code order in _TEXT), public contributions concatenated
  at their alignment, common ones (PAD/EPAD) overlaid; the sequence is anchored by a
  REFERENCED contribution (nmsghdr's HDR) and every anchor must agree.

``accept`` records the exact data segments per member ("data_segments") and the data-only
members ("data_members") in layout/manifest.json; validate.py re-verifies them.
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


# absolute publics: MSC huge-pointer constants (dos\diffhlp.asm) and the debugger swap
# signature (dos\crt0.asm).  Each value is cross-checked against the library's own PUBDEF.
ABSOLUTE = {"__AHINCR": 0x1000, "__AHSHIFT": 12, "__aDBdoswp": 0xD6D6}
# DGROUP symbols MS LINK defines itself under DOSSEG (no library defines them): placements
LINKER_DEFINED = {"_edata", "_end"}


def library_index() -> dict:
    """public name -> [(library, module, segment, class, value)] over the pinned libraries;
    class "ABSOLUTE" (value = PUBDEF offset) for publics without a base segment."""
    rd = OmfReader(communals=True)
    idx = defaultdict(list)
    for k, p in LIBS.items():
        for n, b in rd.split_library(Path(p).read_bytes()):
            obj = rd.read(b, n)
            cls = {sd["name"]: str(sd.get("class", "")) for sd in obj.segment_defs}
            for pb in obj.publics:
                c = cls.get(pb["segment"])
                idx[pb["name"]].append((k, n, pb["segment"], "ABSOLUTE" if c is None else c, pb["offset"]))
    return idx


def classify_unregistered(name: str, idx: dict) -> str | None:
    """None when an unregistered external may be a derived data placement, else the reason
    why it must be bound through layout/symbols.json."""
    defs = idx.get(name, [])
    if defs and all(not d[3].upper().endswith("CODE") and d[3] != "ABSOLUTE" for d in defs):
        return None                       # runtime data public (e.g. __iob in _file.c _DATA)
    if not defs and name in LINKER_DEFINED:
        return None
    if defs:
        where = ", ".join(sorted({f"{d[0]} {d[1]} {d[2]} ({d[3]})" for d in defs}))
        return (f"unregistered code external {name} (defined in {where}): register it in "
                f"layout/symbols.json (tools/symbols.py add-runtime, or name the game function)")
    return (f"unregistered external {name} (no pinned library defines it): register it in "
            f"layout/symbols.json")


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


def code_segments(obj) -> list[str]:
    """CODE-class segments of a member that carry bytes, in SEGDEF order."""
    out = []
    for sd in obj.segment_defs:
        if str(sd.get("class", "")).upper().endswith("CODE") and \
                max(len(obj.segments.get(sd["name"], b"")), sd.get("length") or 0) and sd["name"] not in out:
            out.append(sd["name"])
    return out


def verify_all(collect: dict | None = None):
    """``collect`` (whole-build harness, tools/link.py): when a dict is given, it receives per
    returned member ``(member, linear)`` its bound code segments with relocation sites and the
    fixup fields whose value is a link placement derived from the original operand.  It never
    changes a verdict."""
    x = exemod.load()
    bound_of = {}
    members = load_members()
    idx = library_index()
    abs_bad = [f"{n}={v:#x} but {d[0]} {d[1]} defines {d[4]:#x}" for n, v in ABSOLUTE.items()
               for d in idx.get(n, []) if d[3] == "ABSOLUTE" and d[4] != v]
    if abs_bad:
        raise SystemExit("ABSOLUTE table disagrees with the libraries: " + "; ".join(abs_bad))
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
        segs = code_segments(obj)
        seg0 = next((s for s in segs if s in obj.segments), None)
        extra = dict(m.get("segments") or {})
        reasons = []
        if seg0 in extra:
            reasons.append(f"location lists the first code segment {seg0} under segments")
        unlocated = [s for s in segs if s != seg0 and s not in extra]
        if unlocated:
            reasons.append("unlocated code segments " + ",".join(unlocated))
        placed = {seg0: m["linear"], **{k: v for k, v in extra.items() if k != seg0}}
        frame_of = {sn: (RUNTIME_FRAME if sn == seg0 else lin >> 4) for sn, lin in placed.items()}
        seg_rows = []
        bound = []
        for seg, start in placed.items():
          body = bytearray(obj.segments.get(seg, b""))
          cand_relocs = []
          rkey = {}
          derived_fields = []           # (site, width, key): value derived from the original operand
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
              elif tk == "segment" and tn in placed:
                  frame, off = frame_of[tn], placed[tn] - frame_of[tn] * 16
              elif s is not None and s["kind"] == "code":
                  frame, off = s["seg"], s["off"]
              elif s is not None and s["kind"] == "data":
                  frame, off = s["seg"], s["off"]
              elif tk == "external":
                  why = classify_unregistered(tn, idx)
                  if why:
                      reasons.append(why)
                      continue
              elif tk != "segment":
                  reasons.append(f"unsupported target {tk}:{tn}")
                  continue
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
                      derived_fields.append((site, 2, key))
                  if loc == "pointer32":
                      fr = frame if frame is not None else oracle_word(site + 2)
                      if frame is None:
                          derived[f"frame:{tn}"][fr].append((m["member"], site))
                          derived_fields.append((site + 2, 2, f"frame:{tn}"))
                      struct.pack_into("<H", body, f["offset"] + 2, fr)
                      cand_relocs.append(site + 2)
                      rkey[site + 2] = f"{tk}:{tn}"
              elif loc == "base16":
                  fr = frame if frame is not None else oracle_word(site)
                  if frame is None:
                      derived[f"frame:{tn}"][fr].append((m["member"], site))
                      derived_fields.append((site, 2, f"frame:{tn}"))
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
          seg_rows.append((seg, start, len(body)))
          bound.append({"segment": seg, "start": start, "frame": frame_of[seg], "bytes": bytes(body),
                        "relocs": [(a, rkey.get(a), i) for i, a in enumerate(cand_relocs)],
                        "derived": derived_fields})
        row = {"library": m["library"], "member": m["member"], "module_index": m["module_index"],
               "linear": m["linear"], "size": seg_rows[0][2], "segment": seg0,
               "extra_segments": [{"segment": sg, "linear": st, "size": n} for sg, st, n in seg_rows[1:]],
               "member_sha256": sha(blob), "reasons": reasons,
               "publics": sorted(p["name"] for p in obj.publics if p["segment"] in placed),
               "public_addresses": {p["name"]: [frame_of[p["segment"]],
                                                placed[p["segment"]] - frame_of[p["segment"]] * 16 + p["offset"]]
                                    for p in obj.publics if p["segment"] in placed},
               "alternatives": len(cands)}
        bound_of[id(row)] = bound
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
        if collect is not None:
            collect[(r["member"], r["linear"])] = bound_of.get(id(r), [])
    return results, derived, conflicts, anchors


NO_FILE_CLASSES = {"BSS", "STACK"}
ALIGN = {"byte": 1, "word": 2, "dword": 4, "paragraph": 16, "page": 256}


def _seglen(obj, sd: dict) -> int:
    return max(sd.get("length") or 0, len(obj.segments.get(sd["name"], b"")))


def _dgroup_segments(obj) -> list[dict]:
    """Non-empty DGROUP segments of a member that carry file bytes, in SEGDEF order."""
    dg = {s for g in obj.groups if g.get("name") == "DGROUP" for s in g.get("segments", [])}
    out, seen = [], set()
    for sd in obj.segment_defs:
        if sd["name"] in dg and sd["name"] not in seen and str(sd.get("class", "")).upper() not in NO_FILE_CLASSES \
                and _seglen(obj, sd):
            out.append(sd)
            seen.add(sd["name"])
    return out


def _single(derived: dict, key: str):
    vals = derived.get(key)
    if vals and len(vals) == 1:
        return next(iter(vals))
    return None


def _data_members(results, derived):
    """Exact code members in link order (their code order in _TEXT) plus the data-only library
    members whose data publics the code references."""
    idx = library_index()
    rd = OmfReader(communals=True)
    blobs = {}
    for k, p in LIBS.items():
        for i, (n, b) in enumerate(rd.split_library(Path(p).read_bytes())):
            blobs[(k, n, i)] = b
    members = []
    for r in sorted((r for r in results if r["exact"]), key=lambda r: r["linear"]):
        obj = rd.read(blobs[(r["library"], r["member"], r["module_index"])], r["member"])
        members.append({"row": r, "obj": obj, "code": True})
    located = {(m["row"]["library"], m["row"]["member"]) for m in members}
    wanted = set()
    for key in derived:
        if key.startswith("ext::"):
            name = key.split(":")[2]
            defs = [d for d in idx.get(name, []) if d[3] != "ABSOLUTE" and not d[3].upper().endswith("CODE")]
            if len(defs) == 1 and (defs[0][0], defs[0][1]) not in located:
                wanted.add((defs[0][0], defs[0][1]))
    for lib, name in sorted(wanted):
        hits = [(i, b) for (k, n, i), b in blobs.items() if k == lib and n == name]
        if len(hits) != 1:
            continue
        i, b = hits[0]
        obj = rd.read(b, name)
        if any(str(sd.get("class", "")).upper().endswith("CODE") and _seglen(obj, sd) for sd in obj.segment_defs):
            continue                      # has code: only located code members are placed
        members.append({"row": {"library": lib, "member": name, "module_index": i, "member_sha256": sha(b)},
                        "obj": obj, "code": False})
    return members


def _place_data(members, derived) -> dict:
    """(member, segname) -> (linear, rule) by the rules in the module docstring."""
    dgbase = DGROUP * 16
    place = {}
    for m in members:
        mem, obj = m["row"]["member"], m["obj"]
        for sd in _dgroup_segments(obj):
            sn = sd["name"]
            v = _single(derived, f"seg:{mem}:{sn}:DGROUP")
            if v is not None:
                place[(mem, sn)] = (dgbase + v, "REFERENCED")
                continue
            got = set()
            for pb in obj.publics:
                if pb["segment"] == sn:
                    for key in (f"ext::{pb['name']}:DGROUP", f"ext::{pb['name']}:{pb['name']}"):
                        w = _single(derived, key)
                        if w is not None:
                            got.add(dgbase + w - pb["offset"])
            if len(got) == 1:
                place[(mem, sn)] = (got.pop(), "REFERENCED_PUBLIC")
            elif str(sd.get("class", "")).upper() == "BEGDATA":
                place[(mem, sn)] = (dgbase, "DOSSEG_BEGDATA")
    # the MSG class: relative layout by the linker rule, anchored by REFERENCED contributions
    code_members = [m for m in members if m["code"]]
    for cls in ("MSG",):
        order, rel, pos = [], {}, 0
        for m in code_members:
            for sd in m["obj"].segment_defs:
                if str(sd.get("class", "")).upper() == cls and sd["name"] not in order:
                    order.append(sd["name"])
        for sn in order:
            common, csize = None, 0
            for m in code_members:
                sd = next((d for d in m["obj"].segment_defs
                           if d["name"] == sn and str(d.get("class", "")).upper() == cls), None)
                if sd is None:
                    continue
                n = _seglen(m["obj"], sd)
                if sd.get("combine") == "common":
                    common = pos if common is None else common
                    csize = max(csize, n)
                    rel[(m["row"]["member"], sn)] = common
                    continue
                al = ALIGN.get(sd.get("alignment"), 1)
                pos = (pos + al - 1) // al * al
                rel[(m["row"]["member"], sn)] = pos
                pos += n
            if common is not None:
                pos = common + csize
        anchors = {place[k][0] - r for k, r in rel.items() if k in place and place[k][1] == "REFERENCED"}
        if len(anchors) == 1:
            a0 = anchors.pop()
            for k, r in rel.items():
                if k not in place:
                    place[k] = (a0 + r, "CLASS_SEQUENCE")
    return place


def verify_data(results=None, derived=None, collect: list | None = None) -> list[dict]:
    """Place and verify the runtime members' DGROUP data segments (module docstring)."""
    x = exemod.load()
    s27 = x.sections[27]
    if results is None:
        results, derived, _, _ = verify_all()
    members = _data_members(results, derived)
    place = _place_data(members, derived)
    dgbase = DGROUP * 16
    rows = []
    for m in members:
        mem, obj = m["row"]["member"], m["obj"]
        code_place = {}
        if m["code"]:
            r = m["row"]
            code_place[r["segment"]] = (RUNTIME_FRAME, r["linear"] - RUNTIME_FRAME * 16)
            for e in r.get("extra_segments", []):
                code_place[e["segment"]] = (e["linear"] >> 4, e["linear"] & 15)
        for sd in _dgroup_segments(obj):
            sn = sd["name"]
            n = _seglen(obj, sd)
            row = {"library": m["row"]["library"], "member": mem, "module_index": m["row"]["module_index"],
                   "segment": sn, "class": str(sd.get("class", "")), "size": n, "code_member": m["code"],
                   "member_sha256": m["row"]["member_sha256"]}
            if (mem, sn) not in place:
                row.update(exact=False, reasons=["no symbolic placement (no reference anchors this segment)"])
                rows.append(row)
                continue
            start, rule = place[(mem, sn)]
            row.update(linear=start, rule=rule)
            row.update(bind_data_segment(obj, sn, n, start, mem, place, code_place, derived, x, s27, collect))
            rows.append(row)
    return rows


def bind_data_segment(obj, sn, n, start, mem, place, code_place, derived, x, s27, collect=None) -> dict:
    """Bind one runtime data segment at ``start`` and compare bytes and relocations with S27.
    ``collect`` (list, tools/link.py) receives the bound bytes, relocation sites and the fixup
    fields bound through a placement derived from original operands."""
    dgbase = DGROUP * 16
    reasons = []
    body = bytearray(obj.segments.get(sn, b""))
    body += bytes(n - len(body))
    relocs_c, rkey = [], {}
    derived_fields = []
    for f in obj.linker_fixups:
        if f["segment"] != sn:
            continue
        tk, tn, loc = f["target_kind"], f["target"], f["loc"]
        via_derived = False
        addend = int.from_bytes(bytes.fromhex(f["encoded_addend"]), "little")
        disp = f.get("displacement") or 0
        if f["self_relative"]:
            reasons.append(f"self-relative fixup in data {tn}")
            continue
        if tk == "external" and tn in ABSOLUTE and loc == "offset16":
            struct.pack_into("<H", body, f["offset"], (ABSOLUTE[tn] + addend + disp) & 0xFFFF)
            continue
        frame = off = None
        if tk == "group" and tn == "DGROUP":
            frame, off = DGROUP, 0
        elif tk == "segment" and (mem, tn) in place:
            frame, off = DGROUP, place[(mem, tn)][0] - dgbase
            via_derived = place[(mem, tn)][1] != "DOSSEG_BEGDATA"
        elif tk == "segment" and tn in code_place:
            frame, off = code_place[tn]
        elif tk == "segment" and _single(derived, f"seg:{mem}:{tn}:DGROUP") is not None:
            frame, off = DGROUP, _single(derived, f"seg:{mem}:{tn}:DGROUP")   # e.g. a BSS segment
            via_derived = True
        elif tk == "external":
            s = match.obj_name_lookup(tn)
            if s is not None:
                frame, off = s["seg"], s["off"]
            else:
                w = _single(derived, f"ext::{tn}:DGROUP")
                w = w if w is not None else _single(derived, f"ext::{tn}:{tn}")
                if w is not None:
                    frame, off = DGROUP, w
                    via_derived = True
        if frame is None:
            reasons.append(f"unbound data fixup {loc} {tk}:{tn}")
            continue
        grp = f["frame_kind"] == "group" and f["frame"] == "DGROUP"
        if via_derived and loc in ("offset16", "pointer32"):
            derived_fields.append((start + f["offset"], 2, f"{tk}:{tn}"))
        if loc in ("offset16", "pointer32"):
            v = frame * 16 + off - dgbase if grp else off
            struct.pack_into("<H", body, f["offset"], (v + addend + disp) & 0xFFFF)
            if loc == "pointer32":
                struct.pack_into("<H", body, f["offset"] + 2, DGROUP if grp else frame)
                relocs_c.append(start + f["offset"] + 2)
                rkey[start + f["offset"] + 2] = f"{tk}:{tn}"
        elif loc == "base16":
            struct.pack_into("<H", body, f["offset"], frame)
            relocs_c.append(start + f["offset"])
            rkey[start + f["offset"]] = f"{tk}:{tn}"
        else:
            reasons.append(f"unsupported data fixup {loc}")
    if not (s27.load_linear <= start and start + n <= s27.load_linear + len(s27.data)):
        return {"exact": False, "reasons": reasons + ["placement outside section 27's file data"]}
    if collect is not None:
        collect.append({"member": mem, "segment": sn, "start": start, "bytes": bytes(body),
                        "relocs": [(a, rkey.get(a), i) for i, a in enumerate(relocs_c)],
                        "derived": derived_fields})
    orig = x.read("S27", start, n)
    if bytes(body) != orig:
        i = next(i for i in range(n) if body[i] != orig[i])
        reasons.append(f"bytes differ at +{i:#x}")
    exp = [sg * 16 + o for sg, o in s27.relocs if start <= sg * 16 + o < start + n]
    if sorted(exp) != sorted(relocs_c):
        reasons.append(f"relocation set differs ({len(relocs_c)} vs {len(exp)})")
    else:
        for g in set(rkey.values()):
            if [a for a in exp if rkey.get(a) == g] != [a for a in relocs_c if rkey.get(a) == g]:
                reasons.append(f"relocation order inside target group {g} differs from the object")
    return {"exact": not reasons, "reasons": reasons}


def accepted_data_segments(man: dict) -> list[dict]:
    """Accepted runtime DGROUP data segments recorded in the manifest (members and data members)."""
    rt = man.get("runtime", {})
    return [{**d, "member": m["member"]} for m in rt.get("members", []) + rt.get("data_members", [])
            for d in m.get("data_segments", [])]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["verify", "accept"])
    a = ap.parse_args()
    results, derived, conflicts, anchors = verify_all()
    ok = [r for r in results if r["exact"]]
    extra = sum(e["size"] for r in ok for e in r["extra_segments"])
    print(f"members {len(results)}: exact {len(ok)} ({sum(r['size'] for r in ok) + extra} bytes"
          + (f", of which {extra} in {sum(len(r['extra_segments']) for r in ok)} further code segments)" if extra else ")"))
    for r in results:
        if not r["exact"]:
            print(f"  FAIL {r['member']}: {'; '.join(r['reasons'][:3])}")
    if conflicts:
        print("placement conflicts:", json.dumps(conflicts)[:600])
    single = [k for k, n in anchors.items() if n == 1]
    print(f"derived placements {len(derived)}, single-anchor {len(single)}")
    out = ROOT / "build" / "runtime" / "verify.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"results": results, "conflicts": conflicts, "data": verify_data(results, derived),
                               "placements": {k: {hex(v): [f"{m}@{s:05X}" for m, s in u] for v, u in vals.items()}
                                              for k, vals in derived.items()}}, indent=1))
    data_rows = verify_data(results, derived)
    dok = [d for d in data_rows if d["exact"]]
    print(f"DGROUP data segments {len(data_rows)}: exact {len(dok)} ({sum(d['size'] for d in dok)} bytes; "
          f"{sum(1 for d in dok if not d['code_member'])} of data-only members)")
    for d in data_rows:
        if not d["exact"]:
            print(f"  data {d['member']} {d['segment']}: {'; '.join(d['reasons'][:2])}")
    if a.cmd == "accept":
        from lockfile import CanonicalLock
        import modules as modmod
        with CanonicalLock():
            man = modmod.load_manifest()
            lost = {(m["member"], m["linear"]) for m in man.get("runtime", {}).get("members", [])} - \
                {(r["member"], r["linear"]) for r in ok}
            if lost:
                raise SystemExit(f"refusing to drop accepted members that no longer bind: {sorted(lost)}")
            data_ok = [d for d in data_rows if d["exact"]]
            lost_d = {(d["member"], d["segment"], d["linear"]) for d in accepted_data_segments(man)} - \
                {(d["member"], d["segment"], d["linear"]) for d in data_ok}
            if lost_d:
                raise SystemExit(f"refusing to drop accepted runtime data segments that no longer verify: {sorted(lost_d)}")

            def dsegs(member):
                return [{"segment": d["segment"], "linear": d["linear"], "size": d["size"], "rule": d["rule"]}
                        for d in data_ok if d["member"] == member]
            man["runtime"] = {"libraries": {k: {"path": p, "sha256": sha(Path(p).read_bytes())} for k, p in LIBS.items()},
                              "members": [{**{k: r[k] for k in ("library", "member", "module_index", "linear", "size",
                                                                "segment", "member_sha256")},
                                           **({"extra_segments": r["extra_segments"]} if r["extra_segments"] else {}),
                                           **({"data_segments": dsegs(r["member"])} if dsegs(r["member"]) else {})}
                                          for r in ok],
                              "data_members": [{"library": d["library"], "member": d["member"],
                                                "module_index": d["module_index"], "member_sha256": d["member_sha256"],
                                                "data_segments": dsegs(d["member"])}
                                               for d in {d["member"]: d for d in data_ok if not d["code_member"]}.values()]}
            modmod.write_manifest(man)
        print(f"accepted {len(ok)} runtime members into layout/manifest.json")
        return 0
    return 0 if len(ok) == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
