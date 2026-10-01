from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent

result_files = ("results.json", "direct-results.json", "cursor-results.json")
groups = []
for filename in result_files:
    data = json.loads((OUT / filename).read_text(encoding="utf-8"))
    rows = data["rows"]
    groups.append({
        "file": filename,
        "count": len(rows),
        "compiled": sum(bool(row.get("compile_ok")) for row in rows),
        "target_exact": sum(bool(row.get("exact")) for row in rows),
        "module_all_exact": sum(bool(row.get("all_exact")) for row in rows),
        "peer_data_preserved": sum(bool(row.get("peer_data_preserved")) for row in rows),
        "distinct_machine_hashes": len({row.get("fhash") for row in rows}),
        "best_score": min((row.get("score", [9, 9, 9, 9]) for row in rows), default=None),
        "base_score": data["base"].get("score"),
        "base_length": data["base"].get("length"),
        "base_sha256": data["base"]["sha256"],
    })

search_runs = json.loads((OUT / "search-results.json").read_text(encoding="utf-8"))
artifacts = [
    "run_invert.py", "run_invert_direct.py", "run_cursor.py", "capture_search.py",
    "finalize_report.py", "canonical-S13-m384C.c", "base.c", "variants.json", "results.json",
    "direct-variants.json", "direct-results.json", "cursor-canonical-S12-m384C.c",
    "cursor-base.c", "cursor-variants.json", "cursor-results.json", "search-results.json",
    "search-invert.log", "search-cursor.log",
]
for pattern in ("m320-*.c", "direct-m320-*.c", "scale-*.c"):
    artifacts.extend(str(path.relative_to(OUT)) for path in sorted(OUT.glob(pattern)))
artifacts = sorted(set(artifacts))
hashes = {path: hashlib.sha256((OUT / path).read_bytes()).hexdigest() for path in artifacts}
manifest = {"worker": "ptr_map", "new_variant_count": sum(g["count"] for g in groups),
            "groups": groups, "search_runs": search_runs, "artifacts_sha256": hashes}

def fmt_group(group: dict) -> str:
    return (f"{group['count']} variants; {group['compiled']} compiled; "
            f"{group['target_exact']} target exact; {group['peer_data_preserved']} preserve all accepted "
            f"peers/data; {group['distinct_machine_hashes']} distinct emitted bodies; "
            f"base score {group['base_score']}, base length {group['base_length']}")

report = f"""# PTR-1 pointer-form controls: map cursor and InvertPatch

Work stayed in `build/workers/ptr_map/`. The frozen whole-module source for S13 is
`base.c` (SHA-256 `{groups[0]['base_sha256']}`); the S12 base is `cursor-base.c`
(SHA-256 `{groups[2]['base_sha256']}`). Canonical sources, manifest, evidence and promotion
journal were not edited.

The S13 listing at `S13:384C:128D` shows both resolution loops using a common `i * 4`
offset to read adjacent words from `g_2A42` and write the local `pts` members at
`BP + SI - 0x16` and `BP + SI - 0x14`; the call passes the array base with `LEA`.
Prior residue controls covered coordinate algebra, local stages, products, registers,
and prototypes. These new controls tested a used `struct Pt *point` set by `pts + i`
or `&pts[i]`, then a second form with direct `(pts + i)->field` and
`(&pts[i])->field` writes. Horizontal/vertical store order varied independently in
the two loops.

The S12 control used the local Win16 `DrawMapCursor` semantic source, whose formulas
scale `MapPnt.y` and `MapPnt.x` by `mapYsize` and `mapXsize`. Its DOS listing reads the
corresponding far scale words at `50F6:050A` and `50F6:0508`. Four controls assigned a
real `int far *scale` by `fd_50F6_0508 + index` or `&fd_50F6_0508[index]` separately for
the vertical and horizontal computations.

Results:

- `results.json` (S13 used member pointer): {fmt_group(groups[0])}.
- `direct-results.json` (S13 direct member pointer): {fmt_group(groups[1])}.
- `cursor-results.json` (S12 far scale pointer): {fmt_group(groups[2])}.
- Total new variants: **{sum(g['count'] for g in groups)} / 40**. No variant matched, so
  `promote.py --verify-only` was not applicable.
- Every generated module variant compiled and preserved every other accepted claim and
  private data placement in its module. Changing only `pts + i` to `&pts[i]` emitted the
  same body in the used-pointer S13 controls; the direct S13 member forms also emitted
  the same body for both address expressions. Reversing stores changed the S13 body but
  did not close its residue. All four S12 pointer-initializer combinations emitted the
  same body.
- `search-invert.log` and `search-cursor.log` retain target-only aligned diagnostics for
  each frozen base and a representative pointer variant. Both searches returned 1
  because neither target was exact. The S13 base remains 260 bytes for the 261-byte
  target and has a five-vs-five but mismatched relocation set. Failed matches are
  compiler diagnostics only; they do not establish compiler exclusion.

Generators: `run_invert.py`, `run_invert_direct.py`, and `run_cursor.py`. `variants.json`,
`direct-variants.json`, and `cursor-variants.json` retain source hashes and factor settings;
`hashes.json` records SHA-256 for every generator, frozen source, generated variant,
gate result, search transcript, and this report.
"""
(OUT / "REPORT.md").write_text(report, encoding="utf-8", newline="\n")
hashes["REPORT.md"] = hashlib.sha256((OUT / "REPORT.md").read_bytes()).hexdigest()
manifest["artifacts_sha256"] = hashes
(OUT / "hashes.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
print(f"report={OUT / 'REPORT.md'} variants={manifest['new_variant_count']} hashes={len(hashes)}")
