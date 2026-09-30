"""The only route into canonical reconstructed source.

    python tools/promote.py CANDIDATE.c --module UNIT:SEG[@OFF] --claim NAME [--claim NAME ...]
        [--profile msc600] [--flags /AL /Os] [--placement CONST=55B3:7E28:2]
        [--code-data START:END] [--extent START:END]
        [--steered "construct -> decision it steers"] [--verify-only]
    python tools/promote.py CANDIDATE.c --module data:FRAME --placement SEG=FRAME:OFF:SIZE [...]
        --link-after KEY|FIRST [--verify-only]

CANDIDATE.c is the complete proposed content of the module file
``src/<unit>/m<SEG>.c`` (``m<SEG>_<OFF>.c|.asm`` for a later object ``UNIT:SEG@OFF``
of a frame that LINK built from several objects; see tools/modules.py).
Address ranges ``START:END`` (``--extent``, ``--code-data``) are linear hex with END
*exclusive* (the first byte after the range), e.g. ``--extent 28BC0:290DD`` for a module
whose last byte is 290DC.
``--code-data START:END`` claims code-segment bytes that are data (a buffer or table
assembled into the code segment, linear hex) as kind DATA_IN_CODE: they come from
the candidate object and are compared with the oracle like code.
``--module data:FRAME`` promotes a data-only translation unit (far data, no code) into
``src/data/dFRAME.c``: placements only, zero claims, and ``--link-after`` names the module
whose far data precedes it in the link (FIRST = the first far data of the program).  Any
module may be promoted with placements and zero claims; validate.py reports such modules as
data only, never as recovered code.
Promotion freshly compiles it and requires every already-claimed function of that
module *and* every new claim to be strictly exact (see tools/match.py).  It refuses:
  * claims outside the module frame, unknown functions, double ownership;
  * any regression of an existing claim (bytes, fixups, relocation order);
  * claims inside the SCAFFOLD block;
  * a canonical file that changed while the promotion ran;
  * source-content violations (tools/modules.py source_lint: `_emit`, db/dw/dd inside a proc,
    `org`, asm `include`, numeric branch targets, `#include` traversal);
  * an extent that is not one object placement or does not reach the object's boundaries
    (modules.verify_extent), a new ``UNIT:SEG@OFF`` key without ``--origin-evidence``;
  * ``--unsteer`` when the module source did not change.
Provenance recorded in the manifest: ``--source-origin`` ("hand-written C", "hand-written asm",
"asm-transcribed: <generator path>@<sha256>"; required for .asm modules), ``--mark-steered
NAME=WHY`` (an existing claim whose source holds a steering construct: a dummy construct
with no plausible original purpose), ``--layout-inferred NAME=WHY`` (formatting, labels or
declaration order chosen to satisfy relocation-order or identifier-count evidence; NAME may
be the module key for a module-wide note).
On success it writes the source, updates layout/manifest.json and appends a
proof record to evidence/promotions.jsonl, all under an exclusive lock.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import exe as exemod  # noqa: E402
import functions as fnmod  # noqa: E402
import modules as modmod  # noqa: E402

ROOT = exemod.ROOT
LOCK = ROOT / "build" / "promote.lock"
JOURNAL = ROOT / "evidence" / "promotions.jsonl"


from lockfile import CanonicalLock as Lock  # noqa: E402


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def module_path(unit: str, seg: int, origin: int | None, lang: str) -> Path:
    return ROOT / modmod.module_source(unit, seg, origin, lang)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("candidate", type=Path)
    ap.add_argument("--module", required=True,
                    help="UNIT:SEG, e.g. root:00F8 or S05:35F5; UNIT:SEG@OFF for a later object of a frame")
    ap.add_argument("--claim", action="append", default=[])
    ap.add_argument("--profile")
    ap.add_argument("--flags", nargs="*")
    ap.add_argument("--placement", action="append", default=[], help="SEGNAME=SEG:OFF:SIZE")
    ap.add_argument("--drop-placement", action="append", default=[], help="SEGNAME to remove (e.g. renamed segment)")
    ap.add_argument("--steered", default=None)
    ap.add_argument("--release", action="append", default=[],
                    help="NAME=WHY: drop a claim that belongs to another module (journaled)")
    ap.add_argument("--unsteer", action="append", default=[],
                    help="NAME=WHY: the steering construct of an existing claim was removed (kept as history)")
    ap.add_argument("--extent", help="START:END linear (hex), END exclusive (the first byte after the module): "
                                     "claim the complete module segment (exact TU)")
    ap.add_argument("--code-data", action="append", default=[],
                    help="START:END linear (hex), END exclusive: code-segment data (buffer/table) claimed as DATA_IN_CODE")
    ap.add_argument("--link-after", default=None,
                    help="data:FRAME modules: KEY of the module whose far data precedes this one in the "
                         "link, or FIRST (the program's first far data)")
    ap.add_argument("--asm-evidence", default=None,
                    help="required for .asm: why this code is genuine assembly (compiler experiments)")
    ap.add_argument("--source-origin", default=None,
                    help='"hand-written C" | "hand-written asm" | "asm-transcribed: <generator path>@<sha256>"')
    ap.add_argument("--origin-evidence", default=None,
                    help="UNIT:SEG@OFF modules: why a new object starts at OFF (odd-end 00 fill, relocation "
                         "frames, relocation-order break); required for a new @OFF key")
    ap.add_argument("--mark-steered", action="append", default=[],
                    help="NAME=WHY: an existing claim depends on a steering construct (declared later)")
    ap.add_argument("--asm-workaround", action="append", default=[],
                    help="NAME=WHY: this ASM claim reproduces code that was originally C (a matching "
                         "workaround, counted separately from genuine assembly); NAME=- clears it")
    ap.add_argument("--layout-inferred", action="append", default=[],
                    help="NAME=WHY (NAME = claim or the module key): formatting/label/declaration order "
                         "inferred from relocation-order or identifier-count evidence")
    ap.add_argument("--verify-only", action="store_true")
    a = ap.parse_args()

    unit, seg, origin = modmod.parse_key(a.module)   # also undoes MSYS path-list conversion
    key = modmod.module_key(unit, seg, origin)
    text = a.candidate.read_text(encoding="latin1")
    lang = "asm" if a.candidate.suffix.lower() == ".asm" else "c"
    if lang == "asm" and not a.asm_evidence and not (modmod.load_manifest()["modules"].get(key, {}).get("asm_evidence")):
        raise SystemExit("an .asm module needs --asm-evidence naming the experiments that exclude compiler output")
    if a.asm_evidence and modmod.evidence_path_reasons(a.asm_evidence):
        raise SystemExit("--asm-evidence: " + "; ".join(modmod.evidence_path_reasons(a.asm_evidence)))
    if a.source_origin is not None and modmod.source_origin_reasons(a.source_origin, lang):
        raise SystemExit("--source-origin: " + "; ".join(modmod.source_origin_reasons(a.source_origin, lang)))
    x = exemod.load()
    data_only_key = unit == modmod.DATA_UNIT
    if data_only_key and (a.claim or a.code_data or a.extent):
        raise SystemExit(f"{key}: a data-only module takes placements only (no --claim/--code-data/--extent)")
    if a.link_after is not None and not data_only_key:
        raise SystemExit("--link-after applies to data:FRAME modules")

    with Lock() if not a.verify_only else _NoLock():
        man = modmod.load_manifest()
        mod = man["modules"].get(key)
        old_claims = [dict(c) for c in mod["claims"]] if mod else []
        if origin is not None and mod is None and not (a.origin_evidence or "").strip():
            raise SystemExit(f"{key}: a new object UNIT:SEG@OFF needs --origin-evidence (why LINK started an "
                             f"object at {origin:04X}: odd-end 00 fill, relocation frames, relocation-order break)")
        if a.origin_evidence is not None and origin is None:
            raise SystemExit("--origin-evidence applies to UNIT:SEG@OFF modules")
        profile = a.profile or (mod["profile"] if mod else ("masm510" if lang == "asm" else fnmod.DEFAULT_PROFILE))
        flags = a.flags if a.flags is not None else (mod["flags"] if mod else fnmod.profile_flags(profile))
        placements = dict(mod.get("placements", {})) if mod else {}
        for n in a.drop_placement:
            # e.g. /Zi renumbers a module-defined far segment (UNIT5_DATA -> UNIT7_DATA); the
            # replacement placement is verified like any other before anything is written
            if placements.pop(n, None) is None:
                raise SystemExit(f"--drop-placement: {n} is not a placement of {key}")
        for p in a.placement:
            n, addr = p.split("=")
            s, o, z = addr.replace(";", ":").split(":")  # undo MSYS path-list conversion
            placements[n] = {"seg": int(s, 16), "off": int(o, 16), "size": int(z)}
        owned = {c["name"]: k for k, m in man["modules"].items() for c in m["claims"]}
        lo, hi = modmod.object_range(man, unit, seg, origin)
        for k, m in man["modules"].items():
            # objects of one frame own disjoint offset ranges: a new later object must not cut
            # into claims of an earlier one
            if k != key and m["unit"] == unit and m["seg"] == seg and (m.get("origin") or 0) < lo:
                if (any(c["off"] + c["size"] > lo for c in m["claims"])
                        or m.get("extent", {}).get("end", 0) > seg * 16 + lo):
                    raise SystemExit(f"{key}: module {k} has claims or extent beyond frame offset {lo:04X}")
        new_claims = []
        for name in a.claim:
            f = fnmod.get(name)
            if f["unit"] != unit or f["seg"] != seg or not lo <= f["off"] < hi:
                raise SystemExit(f"{name} is not in module {key} (frame offsets {lo:04X}-{hi - 1:04X})")
            if name in owned and owned[name] != key:
                raise SystemExit(f"{name} already owned by module {owned[name]}")
            if any(c["name"] == name for c in old_claims):
                continue
            orig = x.read(unit, f["seg"] * 16 + f["off"], f["size"])
            new_claims.append({"name": name, "unit": unit, "seg": f["seg"], "off": f["off"], "size": f["size"],
                               "target_sha256": sha(orig), "kind": "ASM" if lang == "asm" else "C",
                               "provenance": "EXACT_STEERED" if a.steered else "EXACT_NATURAL",
                               **({"steered": a.steered} if a.steered else {})})
        for spec in a.code_data:
            d0, d1 = (int(v, 16) for v in spec.replace(";", ":").split(":"))
            off = d0 - seg * 16
            if not (d0 < d1 and lo <= off and off + (d1 - d0) <= hi):
                raise SystemExit(f"--code-data {spec}: not inside module {key} (frame offsets {lo:04X}-{hi - 1:04X})")
            hidden = modmod.row_overlaps(unit, d0, d1 - d0)
            if hidden:
                raise SystemExit(f"--code-data {spec}: overlaps function table entries {hidden[:4]}")
            name = f"cd_{unit}_{seg:04X}_{off:04X}"
            if name in owned and owned[name] != key:
                raise SystemExit(f"{name} already owned by module {owned[name]}")
            prev = next((c for c in old_claims if c["name"] == name), None)
            if prev is not None:
                if prev["size"] != d1 - d0:
                    raise SystemExit(f"--code-data {spec}: {name} is already claimed with size {prev['size']}")
                continue
            new_claims.append({"name": name, "unit": unit, "seg": seg, "off": off, "size": d1 - d0,
                               "target_sha256": sha(x.read(unit, d0, d1 - d0)), "kind": modmod.DATA_KIND,
                               "provenance": "EXACT_STEERED" if a.steered else "EXACT_NATURAL",
                               **({"steered": a.steered} if a.steered else {})})
        # release claims that belong to another translation unit (e.g. a function mis-attributed
        # across a module boundary); the rest of the module is re-verified as usual and the release
        # is journaled.  The released function must then be claimed by its true module.
        released = []
        for spec in a.release:
            name, _, why = spec.partition("=")
            if not why:
                raise SystemExit("--release NAME=WHY: give the evidence")
            if not any(c["name"] == name for c in old_claims):
                raise SystemExit(f"--release {name}: not a claim of {key}")
            old_claims = [c for c in old_claims if c["name"] != name]
            released.append({"name": name, "why": why})
        claims = old_claims + new_claims
        # steering removed from the source: the claim becomes natural once this source re-verifies;
        # the old note is kept as history (the author asserts the steering construct is gone)
        data_new = text.replace("\r\n", "\n").encode("latin1")
        if a.unsteer and (mod is None or sha(data_new) == mod.get("source_sha256")):
            raise SystemExit("--unsteer: the module source is unchanged; remove the steering construct first")
        for spec in a.unsteer:
            name, _, why = spec.partition("=")
            c = next((c for c in claims if c["name"] == name), None)
            if c is None or c.get("provenance") != "EXACT_STEERED":
                raise SystemExit(f"--unsteer {name}: not a steered claim of {key}")
            if not why:
                raise SystemExit("--unsteer NAME=WHY: say what replaced the steering")
            c.setdefault("steered_history", []).append({"steered": c.pop("steered", ""), "cleared": why})
            c["provenance"] = "EXACT_NATURAL"
        # steering found later in an existing claim (a construct added only to move record breaks
        # or identifier counts), and layout inferred from relocation-order / identifier-count evidence
        marked = []
        for spec in a.mark_steered:
            name, _, why = spec.partition("=")
            c = next((c for c in claims if c["name"] == name), None)
            if c is None or not why.strip():
                raise SystemExit(f"--mark-steered {spec}: NAME=WHY with NAME a claim of {key}")
            if c.get("provenance") == "EXACT_STEERED":
                raise SystemExit(f"--mark-steered {name}: already steered ({c.get('steered')})")
            c["provenance"], c["steered"] = "EXACT_STEERED", why
            marked.append({"name": name, "steered": why})
        for spec in a.asm_workaround:
            name, _, why = spec.partition("=")
            c = next((c for c in claims if c["name"] == name), None)
            if c is None or c.get("kind") != "ASM":
                raise SystemExit(f"--asm-workaround {name}: not an ASM claim of {key}")
            if why.strip() == "-":
                c.pop("asm_workaround", None)
            elif why.strip():
                c["asm_workaround"] = why
            else:
                raise SystemExit("--asm-workaround NAME=WHY (or NAME=- to clear)")
        layout_notes = list(mod.get("layout_inferred", [])) if mod else []
        inferred = []
        for spec in a.layout_inferred:
            name, _, why = spec.partition("=")
            if not why.strip():
                raise SystemExit(f"--layout-inferred {spec}: NAME=WHY")
            if name in (key, a.module):
                layout_notes.append(why)
            else:
                c = next((c for c in claims if c["name"] == name), None)
                if c is None:
                    raise SystemExit(f"--layout-inferred {name}: not a claim of {key} (or the module key)")
                c["layout_inferred"] = why
            inferred.append({"name": name, "why": why})
        # extent overlap with every other claim in the program
        for k, m in man["modules"].items():
            for c in m["claims"]:
                for n in new_claims:
                    if c["unit"] == n["unit"] and c["name"] != n["name"]:
                        a0, a1 = c["seg"] * 16 + c["off"], c["seg"] * 16 + c["off"] + c["size"]
                        b0, b1 = n["seg"] * 16 + n["off"], n["seg"] * 16 + n["off"] + n["size"]
                        if a0 < b1 and b0 < a1:
                            raise SystemExit(f"{n['name']} overlaps owned {c['name']}")
        module = {"unit": unit, "seg": seg, "profile": profile, "flags": flags, "placements": placements,
                  "lang": lang}
        if origin is not None:
            module["origin"] = origin
            ev = a.origin_evidence or (mod or {}).get("origin_evidence")
            if ev:
                module["origin_evidence"] = ev
        origin_src = a.source_origin or (mod or {}).get("source_origin") or ("hand-written C" if lang == "c" else None)
        if modmod.source_origin_reasons(origin_src, lang):
            raise SystemExit(f"{key}: " + "; ".join(modmod.source_origin_reasons(origin_src, lang))
                             + " (--source-origin)")
        module["source_origin"] = origin_src
        if layout_notes:
            module["layout_inferred"] = layout_notes
        if data_only_key:
            la = a.link_after if a.link_after is not None else (mod or {}).get("link_after")
            if la is None:
                raise SystemExit(f"{key}: --link-after KEY|FIRST is required (link-order position of a data-only module)")
            la = "" if la.upper() == "FIRST" else la
            if la:
                la = modmod.module_key(*modmod.parse_key(la))
            module["link_after"] = la
            module["kind"] = "data"
        if not claims and not placements:
            raise SystemExit(f"{key}: nothing to promote (no claims and no placements)")
        if lang == "asm":
            module["asm_evidence"] = a.asm_evidence or mod.get("asm_evidence")
        if a.extent:
            s0, s1 = (int(v, 16) for v in a.extent.replace(";", ":").split(":"))
            if origin is not None and s0 != seg * 16 + origin:
                raise SystemExit(f"--extent {a.extent}: an object keyed {key} starts at {seg * 16 + origin:05X}")
            module["extent"] = {"start": s0, "end": s1}
        elif mod and mod.get("extent"):
            module["extent"] = mod["extent"]
        res = modmod.verify_module(text, module, claims, man=man)
        # manifest-level data rules: link position, and no two modules place the same bytes
        man_after = {**man, "modules": {**man["modules"], key: module}}
        mreasons = modmod.link_after_reasons(man_after, key, module)
        mreasons += modmod.placement_overlap_reasons(man_after, key)
        if mreasons:
            res.setdefault("module_reasons", []).extend(mreasons)
            res["exact"] = False
        mr = res.get("module_reasons", [])
        for r in mr[:8]:
            print(f"  module: FAIL {r}")
        if len(mr) > 8:
            print(f"  module: ... {len(mr) - 8} more")
        for n, r in res["claims"].items():
            print(f"  {n}: {'EXACT (reloc order ' + r.get('reloc_order', '?') + ')' if r['exact'] else 'FAIL ' + '; '.join(r['reasons'])}")
        for c in claims:
            r = res["claims"].get(c["name"], {})
            if r.get("exact"):
                c["reloc_order"] = r.get("reloc_order", "EXACT")
        for n, r in res.get("data", {}).items():
            print(f"  data {n}: {'EXACT' if r['exact'] else 'FAIL ' + '; '.join(r['reasons'])}"
                  + (f" ({r['size']} bytes, relocation order {r.get('reloc_order')})" if r["exact"] else ""))
        if res.get("extent"):
            e = res["extent"]
            print(f"  extent: {'EXACT' if e['exact'] else 'FAIL ' + '; '.join(e['reasons'])}, "
                  f"cross-function relocation order {e.get('reloc_order')}"
                  + (" (" + "; ".join(e.get("order_reasons", [])) + ")" if e.get("order_reasons") else ""))
        if not res["compile_ok"]:
            print(res["log"])
        if not res["exact"]:
            print("REFUSED: not every claim is exact (existing claims must not regress)")
            return 1
        if a.verify_only:
            print(f"VERIFY-ONLY OK: {len(claims)} claims in {key}"
                  + (f", {len(placements)} placement(s) (data only)" if not claims else ""))
            return 0
        path = module_path(unit, seg, origin, lang)
        before = path.read_bytes() if path.exists() else None
        if before is not None and mod and sha(before) != mod.get("source_sha256"):
            raise SystemExit(f"{path} differs from its manifest hash; refusing to overwrite unreviewed edits")
        path.parent.mkdir(parents=True, exist_ok=True)
        data = text.replace("\r\n", "\n").encode("latin1")
        path.write_bytes(data)
        man["modules"][key] = {**module, "source": str(path.relative_to(ROOT)).replace("\\", "/"),
                               "source_sha256": sha(data), "claims": claims,
                               "scaffold": res["scaffold"], "object_sha256": res.get("object_sha256")}
        man["modules"] = dict(sorted(man["modules"].items()))
        modmod.write_manifest(man)
        JOURNAL.parent.mkdir(parents=True, exist_ok=True)
        with JOURNAL.open("a") as fh:
            fh.write(json.dumps({"time": dt.datetime.now().isoformat(timespec="seconds"), "module": key,
                                 "new_claims": [c["name"] for c in new_claims], "profile": profile,
                                 "placements": sorted(placements),
                                 **({"released": released} if released else {}),
                                 **({"unsteered": a.unsteer} if a.unsteer else {}),
                                 **({"marked_steered": marked} if marked else {}),
                                 **({"layout_inferred": inferred} if inferred else {}),
                                 **({"source_origin": origin_src} if origin_src != (mod or {}).get("source_origin") else {}),
                                 **({"origin_evidence": module["origin_evidence"]}
                                    if module.get("origin_evidence") and module.get("origin_evidence") != (mod or {}).get("origin_evidence") else {}),
                                 "flags": flags, "source_sha256": sha(data),
                                 "object_sha256": res.get("object_sha256")}) + "\n")
        print(f"PROMOTED {len(new_claims)} new claim(s)"
              + (f", {len(placements)} placement(s)" if placements else "") + f" into {path.relative_to(ROOT)}")
    return 0


class _NoLock:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        pass


if __name__ == "__main__":
    raise SystemExit(main())
