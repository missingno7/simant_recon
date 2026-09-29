"""Locate historical library members in the oracle (diagnostic locator, not acceptance).

For each OMF library given, every module's CODE segment bytes are turned into a
pattern whose fixup fields are wildcards, then searched in every oracle unit
(root and RTLink sections).  A hit shows where an authentic library member very
probably sits; acceptance later requires symbolic binding of every fixup.

Usage:
    python tools/libmatch.py LIB [LIB ...] [--min-size N] [--json OUT]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import exe as exemod  # noqa: E402
from omf import OmfReader, MatchError  # noqa: E402


def module_patterns(lib_path: Path):
    reader = OmfReader()
    data = lib_path.read_bytes()
    for name, blob in reader.split_library(data):
        try:
            mod = reader.read(blob, name)
        except MatchError as e:
            yield name, None, None, f"unreadable: {e}"
            continue
        code_segs = [s for s in mod.segment_defs if str(s.get("class", "")).upper().endswith("CODE")]
        for sd in code_segs:
            seg = sd["name"]
            if seg not in mod.segments:
                continue
            body = bytes(mod.segments[seg])
            mask = bytearray(len(body))
            for f in mod.linker_fixups:
                if f["segment"] == seg:
                    for k in range(f["offset"], min(len(body), f["offset"] + f["width"])):
                        mask[k] = 1
            publics = {p["name"]: p["offset"] for p in mod.publics if p["segment"] == seg}
            yield name, seg, (body, bytes(mask), publics), None


def to_regex(body: bytes, mask: bytes) -> re.Pattern:
    parts = []
    for b, m in zip(body, mask):
        parts.append(b"." if m else re.escape(bytes([b])))
    return re.compile(b"".join(parts), re.DOTALL)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("libs", nargs="+", type=Path)
    ap.add_argument("--min-size", type=int, default=12)
    ap.add_argument("--json", type=Path)
    args = ap.parse_args()
    x = exemod.load()
    units = {u: x.unit_bytes(u) for u in x.units()}
    report = {}
    for lib in args.libs:
        rows = []
        hit_bytes = 0
        for name, seg, payload, err in module_patterns(lib):
            if payload is None:
                if err:
                    rows.append({"module": name, "error": err})
                continue
            body, mask, publics = payload
            if len(body) < args.min_size:
                continue
            rx = to_regex(body, mask)
            hits = []
            for u, (base, data) in units.items():
                for m in rx.finditer(data):
                    hits.append({"unit": u, "linear": base + m.start()})
            rows.append({"module": name, "segment": seg, "size": len(body),
                         "fixup_bytes": sum(mask), "publics": publics, "hits": hits})
            if len(hits) == 1:
                hit_bytes += len(body)
        matched = [r for r in rows if r.get("hits")]
        report[str(lib)] = {"modules_tested": len(rows), "modules_found": len(matched),
                            "unique_found_bytes": hit_bytes, "rows": rows}
        print(f"{lib}: {len(matched)}/{len(rows)} code contributions found, "
              f"{hit_bytes} bytes in unique hits")
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(report, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
