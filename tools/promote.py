"""The only route into canonical reconstructed source.

    python tools/promote.py CANDIDATE.c --module UNIT:SEG --claim NAME [--claim NAME ...]
        [--profile msc600] [--flags /AL /Os] [--placement CONST=55B3:7E28:2]
        [--steered "construct -> decision it steers"] [--verify-only]

CANDIDATE.c is the complete proposed content of the module file
``src/<unit>/m<SEG>.c``.  Promotion freshly compiles it and requires every
already-claimed function of that module *and* every new claim to be strictly
exact (see tools/match.py).  It refuses:
  * claims outside the module frame, unknown functions, double ownership;
  * any regression of an existing claim (bytes, fixups, relocation order);
  * claims inside the SCAFFOLD block;
  * a canonical file that changed while the promotion ran.
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


def module_path(unit: str, seg: int) -> Path:
    return ROOT / "src" / unit / f"m{seg:04X}.c"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("candidate", type=Path)
    ap.add_argument("--module", required=True, help="UNIT:SEG, e.g. root:00F8 or S05:35F5")
    ap.add_argument("--claim", action="append", default=[])
    ap.add_argument("--profile")
    ap.add_argument("--flags", nargs="*")
    ap.add_argument("--placement", action="append", default=[], help="SEGNAME=SEG:OFF:SIZE")
    ap.add_argument("--drop-placement", action="append", default=[], help="SEGNAME to remove (e.g. renamed segment)")
    ap.add_argument("--steered", default=None)
    ap.add_argument("--extent", help="START:END linear (hex): claim the complete module segment (exact TU)")
    ap.add_argument("--asm-evidence", default=None,
                    help="required for .asm: why this code is genuine assembly (compiler experiments)")
    ap.add_argument("--verify-only", action="store_true")
    a = ap.parse_args()

    unit, segs = a.module.replace(";", ":").split(":")  # undo MSYS path-list conversion
    seg = int(segs, 16)
    key = f"{unit}:{seg:04X}"
    text = a.candidate.read_text(encoding="latin1")
    lang = "asm" if a.candidate.suffix.lower() == ".asm" else "c"
    if lang == "asm" and not a.asm_evidence and not (modmod.load_manifest()["modules"].get(a.module, {}).get("asm_evidence")):
        raise SystemExit("an .asm module needs --asm-evidence naming the experiments that exclude compiler output")
    x = exemod.load()

    with Lock() if not a.verify_only else _NoLock():
        man = modmod.load_manifest()
        mod = man["modules"].get(key)
        old_claims = list(mod["claims"]) if mod else []
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
        new_claims = []
        for name in a.claim:
            f = fnmod.get(name)
            if f["unit"] != unit or f["seg"] != seg:
                raise SystemExit(f"{name} is not in module {key}")
            if name in owned and owned[name] != key:
                raise SystemExit(f"{name} already owned by module {owned[name]}")
            if any(c["name"] == name for c in old_claims):
                continue
            orig = x.read(unit, f["seg"] * 16 + f["off"], f["size"])
            new_claims.append({"name": name, "unit": unit, "seg": f["seg"], "off": f["off"], "size": f["size"],
                               "target_sha256": sha(orig), "kind": "ASM" if lang == "asm" else "C",
                               "provenance": "EXACT_STEERED" if a.steered else "EXACT_NATURAL",
                               **({"steered": a.steered} if a.steered else {})})
        claims = old_claims + new_claims
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
        if lang == "asm":
            module["asm_evidence"] = a.asm_evidence or mod.get("asm_evidence")
        if a.extent:
            s0, s1 = (int(v, 16) for v in a.extent.split(":"))
            module["extent"] = {"start": s0, "end": s1}
        elif mod and mod.get("extent"):
            module["extent"] = mod["extent"]
        res = modmod.verify_module(text, module, claims)
        for n, r in res["claims"].items():
            print(f"  {n}: {'EXACT (reloc order ' + r.get('reloc_order', '?') + ')' if r['exact'] else 'FAIL ' + '; '.join(r['reasons'])}")
        for c in claims:
            r = res["claims"].get(c["name"], {})
            if r.get("exact"):
                c["reloc_order"] = r.get("reloc_order", "EXACT")
        for n, r in res.get("data", {}).items():
            print(f"  data {n}: {'EXACT' if r['exact'] else 'FAIL ' + '; '.join(r['reasons'])}")
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
            print(f"VERIFY-ONLY OK: {len(claims)} claims in {key}")
            return 0
        path = module_path(unit, seg).with_suffix(".asm" if lang == "asm" else ".c")
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
                                 "flags": flags, "source_sha256": sha(data),
                                 "object_sha256": res.get("object_sha256")}) + "\n")
        print(f"PROMOTED {len(new_claims)} new claim(s) into {path.relative_to(ROOT)}")
    return 0


class _NoLock:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        pass


if __name__ == "__main__":
    raise SystemExit(main())
