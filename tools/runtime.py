"""Verify authentic historical runtime library members (HISTORICAL_RUNTIME ownership).

    python tools/runtime.py                   # verify pinned historical members; never publishes

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
* REGISTERED_PUBLICS: at least two independently grounded data publics in the symbol
  registry agree on the segment start after subtracting their library PUBDEF offsets.
  This also admits a data-only library member referenced by game code, e.g. syserr.c;
  a single public or conflicting public anchors cannot place the segment.
* DOSSEG_BEGDATA: class BEGDATA (the NULL segment) is the first segment of DGROUP (offset 0);
* CLASS_SEQUENCE: the MSG class is laid out by the linker rule: segments in order of first
  appearance in member link order (= code order in _TEXT), public contributions concatenated
  at their alignment, common ones (PAD/EPAD) overlaid; the sequence is anchored by a
  REFERENCED contribution (nmsghdr's HDR) and every anchor must agree.
* BRACKETED: a member (crt0dat) declares the empty segments ``SB``, ``S``, ``SE`` (e.g. XPB, XP,
  XPE) in this order; the contributions of ``S`` of the code members are concatenated in member
  link order at their alignment from ``SB``, and must end exactly at ``SE``.  Both bounds are
  derived placements (REFERENCED) of the bracketing member, so the concatenation is checked by
  two independent anchors (e.g. _cflush's XP ``dd _flushall`` between XPB and XPE).

Fixup targets in runtime data that no placement above covers:

* ENDCODE: a segment of class ENDCODE (crt0's C_ETEXT, length 0) follows the last CODE-class
  segment of the program; its frame is the first paragraph after the code areas of the layout
  model (the root image and the overlay areas of the RTLink section table), which must be
  section 27's load frame (3D57).  Never taken from the fixup's value.
* COMDEF_ANCHORS: a near communal of a member (COMDEF, class c_common in DGROUP, e.g. _file.c's
  ``__bufin``, 512 bytes) is placed where at least two data fixups of placed runtime data
  segments agree it lies (the original operands minus the fixup addend); it must lie in
  DGROUP's uninitialised part.  Reported as derived, with its anchors (``communal_placements``).

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


def verify_all():
    """Compare pinned runtime members, bound fixups and relocation ordering."""
    x = exemod.load()
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
        for seg, start in placed.items():
          body = bytearray(obj.segments.get(seg, b""))
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
              elif tk == "segment" and tn in placed:
                  frame, off = frame_of[tn], placed[tn] - frame_of[tn] * 16
              elif s is not None and s["kind"] == "code":
                  frame, off = s["seg"], s["off"]
              elif s is not None and s["kind"] == "data" and not s.get("library"):
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
          seg_rows.append((seg, start, len(body)))
        row = {"library": m["library"], "member": m["member"], "module_index": m["module_index"],
               "linear": m["linear"], "size": seg_rows[0][2], "segment": seg0,
               "extra_segments": [{"segment": sg, "linear": st, "size": n} for sg, st, n in seg_rows[1:]],
               "member_sha256": sha(blob), "reasons": reasons,
               "publics": sorted(p["name"] for p in obj.publics if p["segment"] in placed),
               "public_addresses": {p["name"]: [frame_of[p["segment"]],
                                                placed[p["segment"]] - frame_of[p["segment"]] * 16 + p["offset"]]
                                    for p in obj.publics if p["segment"] in placed},
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
    for n, s in match.symbols().items():
        # a registered runtime data public must sit where every reference places it
        if s.get("kind") == "data" and s.get("library"):
            for k in (f"ext::{n}:DGROUP", f"ext::{n}:{n}"):
                if k in derived and set(derived[k]) != {s["off"]}:
                    conflicts[k] = {**{hex(v): len(u) for v, u in derived[k].items()}, "registered": hex(s["off"])}
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


def segment_def_of(obj, name: str) -> dict | None:
    return next((sd for sd in obj.segment_defs if sd["name"] == name), None)


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
    # Game references are already grounded in the data registry.  Runtime-only code
    # analysis cannot see them (syserr.c has no runtime caller in this game).
    for name, defs in idx.items():
        s = match.obj_name_lookup(name)
        if s is not None and s.get("kind") == "data" and len(defs) == 1:
            d = defs[0]
            if d[3] != "ABSOLUTE" and not d[3].upper().endswith("CODE") and (d[0], d[1]) not in located:
                wanted.add((d[0], d[1]))
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
            elif not got:
                registered = []
                for pb in obj.publics:
                    s = match.obj_name_lookup(pb["name"])
                    if pb["segment"] == sn and s is not None and s.get("kind") == "data" and s["seg"] == DGROUP:
                        registered.append((pb["name"], dgbase + s["off"] - pb["offset"]))
                starts = {a for _, a in registered}
                if len({name for name, _ in registered}) >= 2 and len(starts) == 1:
                    place[(mem, sn)] = (starts.pop(), "REGISTERED_PUBLICS")
    code_members = [m for m in members if m["code"]]
    # rule BRACKETED: SB <= S <= SE (crt0dat's XPB/XP/XPE, ...); the S contributions are
    # concatenated in member link order from SB and must end exactly at SE (two derived anchors)
    for m in code_members:
        names = [sd["name"] for sd in m["obj"].segment_defs]
        for i in range(len(names) - 2):
            b, s, e = names[i:i + 3]
            if b != s + "B" or e != s + "E":
                continue
            # SB and SE are empty: their placements are the derived ones (references to them)
            lo = _single(derived, f"seg:{m['row']['member']}:{b}:DGROUP")
            hi = _single(derived, f"seg:{m['row']['member']}:{e}:DGROUP")
            if lo is None or hi is None:
                continue
            # contributions in link order: code members by their code position; a data-only
            # member has no known position, so it may only be the single contribution
            contrib = [c for c in members if segment_def_of(c["obj"], s) is not None
                       and _seglen(c["obj"], segment_def_of(c["obj"], s))]
            if len(contrib) > 1 and not all(c["code"] for c in contrib):
                continue
            pos, rel = DGROUP * 16 + lo, {}
            for c in contrib:
                sd = segment_def_of(c["obj"], s)
                al = ALIGN.get(sd.get("alignment"), 1)
                pos = (pos + al - 1) // al * al
                rel[(c["row"]["member"], s)] = pos
                pos += _seglen(c["obj"], sd)
            if rel and pos == DGROUP * 16 + hi and all(place.get(k, (v,))[0] == v for k, v in rel.items()):
                for k, v in rel.items():
                    place.setdefault(k, (v, "BRACKETED"))
    # the MSG class: relative layout by the linker rule, anchored by REFERENCED contributions
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


def endcode_linear(x=None) -> tuple[int, list[str]]:
    """Rule ENDCODE: (linear address of an ENDCODE-class segment, reasons).  It is the first
    paragraph after the last CODE-class segment: the end of the root image's code and of the
    overlay areas (RTLink section table: load paragraph + memory paragraphs), which must be
    where section 27 (far data, DGROUP) is loaded."""
    x = x or exemod.load()
    ends = [len(x.image)] + [s.load_linear + s.mem_paras * 16 for s in x.sections[:27]]
    end = (max(ends) + 15) & ~15
    s27 = x.sections[27].load_linear
    return end, ([] if end == s27 else [f"ENDCODE: code ends at {end:05X}, section 27 loads at {s27:05X}"])


def communal_placements(members, place, x=None) -> dict:
    """Rule COMDEF_ANCHORS (module docstring): name -> {"linear", "size", "member", "anchors",
    "exact", "reasons"} for the near communals that fixups of placed runtime data segments
    reference.  The anchors are the original operands of those fixups."""
    x = x or exemod.load()
    s27 = x.sections[27]
    comm = {}
    for m in members:
        for c in getattr(m["obj"], "communals", []):
            if c.get("kind") == "near":
                comm.setdefault(c["name"], (m["row"]["member"], c["length"], m["row"]["library"]))
    anchors = defaultdict(lambda: defaultdict(list))
    for m in members:
        mem, obj = m["row"]["member"], m["obj"]
        for f in obj.linker_fixups:
            if (f["target_kind"] != "external" or f["target"] not in comm or (mem, f["segment"]) not in place
                    or f["loc"] not in ("offset16", "pointer32") or f["self_relative"]):
                continue
            site = place[(mem, f["segment"])][0] + f["offset"]
            addend = int.from_bytes(bytes.fromhex(f["encoded_addend"]), "little") + (f.get("displacement") or 0)
            v = (struct.unpack_from("<H", x.read("S27", site, 2))[0] - addend) & 0xFFFF
            anchors[f["target"]][v].append(f"{mem} {f['segment']}+{f['offset']:#x}")
    out = {}
    for name, vals in anchors.items():
        mem, size, lib = comm[name]
        reasons = []
        if len(vals) != 1:
            reasons.append(f"anchors disagree: {sorted(hex(v) for v in vals)}")
        if sum(len(u) for u in vals.values()) < 2:
            reasons.append("single anchor (at least two agreeing data fixups are required)")
        lin = DGROUP * 16 + next(iter(vals))
        if lin < s27.load_linear + len(s27.data) - 3 or lin + size > s27.load_linear + s27.mem_paras * 16:
            reasons.append(f"{lin:05X}+{size} is not in DGROUP's uninitialised part")
        out[name] = {"linear": lin, "size": size, "member": mem, "library": lib, "rule": "COMDEF_ANCHORS",
                     "anchors": [a for u in vals.values() for a in u], "exact": not reasons, "reasons": reasons}
    return out


def verify_data(results=None, derived=None, communals: dict | None = None) -> list[dict]:
    """Place and verify the runtime members' DGROUP data segments (module docstring).
    ``communals`` (dict), when given, receives communal_placements."""
    x = exemod.load()
    s27 = x.sections[27]
    if results is None:
        results, derived, _, _ = verify_all()
    members = _data_members(results, derived)
    place = _place_data(members, derived)
    comm = communal_placements(members, place, x)
    if communals is not None:
        communals.update(comm)
    commons = {n: c["linear"] - DGROUP * 16 for n, c in comm.items() if c["exact"]}
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
                   "member_sha256": m["row"]["member_sha256"], "align": sd.get("alignment")}
            if (mem, sn) not in place:
                row.update(exact=False, reasons=["no symbolic placement (no reference anchors this segment)"])
                rows.append(row)
                continue
            start, rule = place[(mem, sn)]
            row.update(linear=start, rule=rule)
            row.update(bind_data_segment(obj, sn, n, start, mem, place, code_place, derived, x, s27,
                                         commons=commons))
            if row["exact"]:
                row["public_addresses"] = {p["name"]: [DGROUP, start - dgbase + p["offset"]]
                                           for p in obj.publics if p["segment"] == sn}
            rows.append(row)
    return rows


def bind_data_segment(obj, sn, n, start, mem, place, code_place, derived, x, s27,
                      commons: dict | None = None) -> dict:
    """Bind one runtime data segment and compare bytes and relocations with S27."""
    dgbase = DGROUP * 16
    reasons = []
    body = bytearray(obj.segments.get(sn, b""))
    body += bytes(n - len(body))
    relocs_c, rkey = [], {}
    for f in obj.linker_fixups:
        if f["segment"] != sn:
            continue
        tk, tn, loc = f["target_kind"], f["target"], f["loc"]
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
        elif tk == "segment" and tn in code_place:
            frame, off = code_place[tn]
        elif tk == "segment" and _single(derived, f"seg:{mem}:{tn}:DGROUP") is not None:
            frame, off = DGROUP, _single(derived, f"seg:{mem}:{tn}:DGROUP")   # e.g. a BSS segment
        elif tk == "segment" and str((segment_def_of(obj, tn) or {}).get("class", "")).upper() == "ENDCODE":
            lin, why = endcode_linear(x)                  # rule ENDCODE (layout model)
            if why:
                reasons += why
                continue
            frame, off = lin >> 4, lin & 15
        elif tk == "external" and tn in (commons or {}) and match.obj_name_lookup(tn) is None:
            frame, off = DGROUP, commons[tn]              # rule COMDEF_ANCHORS
        elif tk == "external":
            s = match.obj_name_lookup(tn)
            if s is not None:
                frame, off = s["seg"], s["off"]
            else:
                w = _single(derived, f"ext::{tn}:DGROUP")
                w = w if w is not None else _single(derived, f"ext::{tn}:{tn}")
                if w is not None:
                    frame, off = DGROUP, w
        if frame is None:
            reasons.append(f"unbound data fixup {loc} {tk}:{tn}")
            continue
        grp = f["frame_kind"] == "group" and f["frame"] == "DGROUP"
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
    out = ROOT / "build" / "current" / "runtime" / "verify.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"results": results, "conflicts": conflicts, "data": verify_data(results, derived),
                               "placements": {k: {hex(v): [f"{m}@{s:05X}" for m, s in u] for v, u in vals.items()}
                                              for k, vals in derived.items()}}, indent=1))
    comm = {}
    data_rows = verify_data(results, derived, communals=comm)
    dok = [d for d in data_rows if d["exact"]]
    print(f"DGROUP data segments {len(data_rows)}: exact {len(dok)} ({sum(d['size'] for d in dok)} bytes; "
          f"{sum(1 for d in dok if not d['code_member'])} of data-only members)")
    for d in data_rows:
        if not d["exact"]:
            print(f"  data {d['member']} {d['segment']}: {'; '.join(d['reasons'][:2])}")
    for n, c in sorted(comm.items()):
        print(f"  near communal {n} ({c['member']}, {c['size']} bytes) at DGROUP:{c['linear'] - DGROUP * 16:04X}: "
              f"{'derived from ' + str(len(c['anchors'])) + ' agreeing anchors' if c['exact'] else 'NOT PLACED'} "
              f"({', '.join(c['anchors'][:4])}){'; ' + '; '.join(c['reasons']) if c['reasons'] else ''}")
    return 0 if len(ok) == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
