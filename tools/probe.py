"""Controlled compiler experiments (evidence for docs/codegen-rules.md).

    python tools/probe.py evidence/codegen/SPEC.json            # run and print
    python tools/probe.py evidence/codegen/SPEC.json --record   # also write SPEC.result.json

SPEC:
  {"id": "RULE-ID", "question": "...", "header": "common C text",
   "variants": {"name": "C text", ...},
   "profiles": [{"profile": "msc600", "flags": ["/AL", "/Os"]}, ...],
   "expect": {"variant@profileindex": "exact disassembly substring", ...}}   (optional)

Each variant is compiled freshly under each pinned profile; the code segment is
disassembled with fixup fields left as emitted.  --record stores the bytes,
disassembly and tool identities so the rule can be re-checked by validate.py.
"""
from __future__ import annotations

import argparse
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
            src = spec.get("header", "") + body + "\n"
            r = compiler.compile_c(src, p["profile"], p["flags"])
            row = {"variant": name, "profile_index": pi, "profile": p["profile"], "flags": p["flags"],
                   "source_sha256": hashlib.sha256(src.encode()).hexdigest()}
            if not r.ok:
                row["error"] = r.log[-400:]
            else:
                obj = OmfReader(communals=True).read(r.obj)
                code = b"".join(bytes(v) for k, v in obj.segments.items() if k.endswith("_TEXT"))
                row["bytes"] = code.hex()
                row["disasm"] = "; ".join(f"{i.mnemonic} {i.op_str}".strip() for i in md.disasm(code, 0))
            out["results"].append(row)
    checks = []
    for key, needle in spec.get("expect", {}).items():
        v, pi = key.split("@")
        row = next(r for r in out["results"] if r["variant"] == v and r["profile_index"] == int(pi))
        want_absent = needle.startswith("!")
        n = needle[1:] if want_absent else needle
        ok = (n not in row.get("disasm", "")) if want_absent else (n in row.get("disasm", ""))
        checks.append({"check": key, "needle": needle, "ok": ok})
    out["checks"] = checks
    out["all_checks_pass"] = all(c["ok"] for c in checks)
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
