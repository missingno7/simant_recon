"""Controlled compiler experiments (evidence for docs/codegen-rules.md).

    python tools/probe.py evidence/codegen/SPEC.json            # run and print
    python tools/probe.py evidence/codegen/SPEC.json --record   # also write SPEC.result.json

SPEC:
  {"id": "RULE-ID", "question": "...", "header": "common C text",
   "variants": {"name": "C text", ...},
   # A variant may instead be {"source": "...", "language": "asm",
   # "toolchain": {"profile": "masm510", "flags": ["/Mx"]}} for a symbolic ASM contrast.
   "profiles": [{"profile": "msc600", "flags": ["/AL", "/Os"]}, ...],
   "expect": {"variant@profileindex": "exact disassembly substring", ...},   (optional)
   "expect_segments": {"variant@profileindex": {                              (optional)
        "SEGNAME": {"class": "FAR_DATA", "align": "paragraph", "length": 20, "combine": "public"},
        "OTHER_SEG": null,                      # the object must not define this segment
        "communals": {"_ga": 8} or ["_ga"]}}}   # far/near COMDEF names (and sizes)
   # expect_bindings uses the same variant@profileindex keys. Fields are exact
   # live fixup-target counts, ordered CONST fixups, external scopes or data publics.

Each variant is compiled freshly under each pinned profile; the code segment is
disassembled with fixup fields left as emitted.  Segment expectations compare the
object's SEGDEFs (class, alignment, combine, length -- 64K for a big segment with length
field 0) and its COMDEF communals, so data layout rules (FARSEG-1) are probes too.
--record stores the bytes, disassembly and tool identities so the rule can be re-checked
by validate.py.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import sys
from pathlib import Path

try:
    import capstone  # noqa: F401
except ImportError:  # sandboxed users cannot see the per-user site-packages
    import sys as _sys
    _sys.path.insert(0, "C:/tools/capstone-5.0.3")
from capstone import Cs, CS_ARCH_X86, CS_MODE_16

sys.path.insert(0, str(Path(__file__).resolve().parent))
import compiler  # noqa: E402
from omf import OmfReader  # noqa: E402

md = Cs(CS_ARCH_X86, CS_MODE_16)


def run(spec: dict) -> dict:
    out = {"id": spec["id"], "question": spec.get("question"), "results": []}
    for pi, p in enumerate(spec["profiles"]):
        for name, body in spec["variants"].items():
            config = {**p, **(body.get("toolchain", {}) if isinstance(body, dict) else {})}
            lang = body.get("language", "c") if isinstance(body, dict) else "c"
            if lang not in ("c", "asm"):
                raise ValueError(f"unsupported probe language {lang!r}")
            src = spec.get("header", "") + (body["source"] if isinstance(body, dict) else body) + "\n"
            compile_source = compiler.assemble if lang == "asm" else compiler.compile_c
            r = compile_source(src, config["profile"], config["flags"])
            row = {"variant": name, "profile_index": pi, "profile": config["profile"], "flags": config["flags"],
                   "source_sha256": hashlib.sha256(src.encode()).hexdigest()}
            if not r.ok:
                row["error"] = r.log[-400:]
            else:
                obj = OmfReader(communals=True).read(r.obj)
                code = b"".join(bytes(v) for k, v in obj.segments.items() if k.endswith("_TEXT"))
                row["bytes"] = code.hex()
                row["disasm"] = "; ".join(f"{i.mnemonic} {i.op_str}".strip() for i in md.disasm(code, 0))
                row["segments"] = segment_summary(obj)
                row["communals"] = {c["name"]: c["length"] for c in getattr(obj, "communals", [])}
                row["bindings"] = binding_summary(obj)
            out["results"].append(row)
    checks = []
    for key, needle in spec.get("expect", {}).items():
        v, pi = key.split("@")
        row = next(r for r in out["results"] if r["variant"] == v and r["profile_index"] == int(pi))
        want_absent = needle.startswith("!")
        n = needle[1:] if want_absent else needle
        ok = (n not in row.get("disasm", "")) if want_absent else (n in row.get("disasm", ""))
        checks.append({"check": key, "needle": needle, "ok": ok})
    for key, want in spec.get("expect_segments", {}).items():
        v, pi = key.split("@")
        row = next(r for r in out["results"] if r["variant"] == v and r["profile_index"] == int(pi))
        checks += segment_checks(key, row, want)
    for key, want in spec.get("expect_bindings", {}).items():
        v, pi = key.split("@")
        row = next(r for r in out["results"] if r["variant"] == v and r["profile_index"] == int(pi))
        checks += binding_checks(key, row, want)
    out["checks"] = checks
    out["all_checks_pass"] = all(c["ok"] for c in checks)
    return out


def binding_summary(obj) -> dict:
    """Keep allocation scope separate from the fixup's target spelling.

    Tentative far definitions still target external names. COMDEF and the
    parsed external scope, rather than a segment-target assumption, identify
    their allocation contribution. Debug fixups are outside this live view.
    """
    live = {sd['name'] for sd in obj.segment_defs
            if str(sd.get('class', '')).upper() not in ('DEBSYM', 'DEBTYP')}
    fixes = [f for f in obj.linker_fixups if f['segment'] in live]
    fields = ('offset', 'width', 'loc', 'target_kind', 'target', 'target_method',
              'frame_kind', 'frame', 'frame_method', 'encoded_addend')
    return {
        'fixup_target_counts': dict(Counter('|'.join((f['segment'], f['loc'],
                                                     f['target_kind'], f['target'])) for f in fixes)),
        'ordered_const_fixups': [{k: f[k] for k in fields} for f in fixes if f['segment'] == 'CONST'],
        'external_scopes': dict(zip(obj.externals, obj.external_scopes)),
        'data_publics': [p for p in obj.publics if p['segment'] in live
                         and not p['segment'].endswith('_TEXT')],
    }


def binding_checks(key: str, row: dict, want: dict) -> list[dict]:
    allowed = {'fixup_target_counts', 'ordered_const_fixups', 'external_scopes', 'data_publics'}
    if set(want) - allowed:
        raise ValueError('unsupported binding expectation: ' + str(sorted(set(want) - allowed)))
    actual = row.get('bindings', {})
    return [{'check': key, 'needle': 'bindings.' + field,
             'ok': actual.get(field) == expected} for field, expected in want.items()]


def segdef_length(sd: dict) -> int:
    n = sd.get("length") or 0
    return 0x10000 if sd.get("big") and n == 0 else n


def segment_summary(obj) -> dict:
    """Non-debug SEGDEFs of an object: class, alignment, combine, true length, big bit."""
    return {sd["name"]: {"class": sd.get("class"), "align": sd.get("alignment"), "combine": sd.get("combine"),
                         "length": segdef_length(sd), "big": bool(sd.get("big"))}
            for sd in obj.segment_defs if str(sd.get("class", "")).upper() not in ("DEBSYM", "DEBTYP")}


def segment_checks(key: str, row: dict, want: dict) -> list[dict]:
    segs, comm = row.get("segments"), row.get("communals")
    if segs is None:
        return [{"check": key, "needle": "segments", "ok": False}]
    out = []
    for name, exp in want.items():
        if name == "communals":
            items = exp.items() if isinstance(exp, dict) else ((n, None) for n in exp)
            for n, size in items:
                ok = n in comm and (size is None or comm[n] == size)
                out.append({"check": key, "needle": f"communal {n}" + (f" {size}" if size is not None else ""), "ok": ok})
            continue
        if exp is None:
            out.append({"check": key, "needle": f"no segment {name}", "ok": name not in segs})
            continue
        got = segs.get(name)
        for field, val in exp.items():
            if field not in ("class", "align", "length", "combine", "big"):
                continue                  # notes and other annotations
            out.append({"check": key, "needle": f"{name}.{field}={val}", "ok": got is not None and got.get(field) == val})
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("spec", type=Path)
    ap.add_argument("--record", action="store_true")
    a = ap.parse_args()
    spec = json.loads(a.spec.read_text())
    res = run(spec)
    for r in res["results"]:
        print(f"[{r['variant']} @ {r['profile']} {' '.join(r['flags'])}] {r.get('disasm', r.get('error'))}")
    for c in res["checks"]:
        print(f"  check {c['check']} '{c['needle']}': {'OK' if c['ok'] else 'FAIL'}")
    if a.record:
        a.spec.with_suffix(".result.json").write_text(json.dumps(res, indent=1) + "\n")
    return 0 if res["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
