"""Generate immutable input and extraction pins for the 56FE owner review."""
from __future__ import annotations

import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "build/workers/dos_dgroup_56fe_owner_v32/pins.json"

PIN_PATHS = [
    "build/source-only-dos/build-report.json",
    "work/data/s27_map.json",
    "work/takeover/behavioral-oracle/data-debt.json",
    "work/takeover/behavioral-oracle/debt-audit/reference-scan.json",
    "work/source-only-dos/data-debt-review-v22/worker-receipt.md",
    "work/source-only-dos/data-debt-review-v22/worker-pins.json",
    "layout/manifest.json",
    "layout/symbols.json",
    "src/root/m195A.asm",
    "src/root/m1E57.c",
    "tools/context.py",
    "tools/omf.py",
    "evidence/cross_version/simantw_correspondence.json",
    "build/source-only-dos/objects/U077.OBJ",
    "build/source-only-dos/objects/U091.OBJ",
    "build/workers/dos_dgroup_56fe_owner_v32/context-f_195A_0166.txt",
    "build/workers/dos_dgroup_56fe_owner_v32/context-f_1E57_0052.txt",
    "build/workers/dos_dgroup_56fe_owner_v32/context-f_1E57_00B1.txt",
    "build/workers/dos_dgroup_56fe_owner_v32/context-f_1E57_038E.txt",
    "build/workers/dos_dgroup_56fe_owner_v32/make_pins.py",
    "build/workers/dos_dgroup_56fe_owner_v32/receipt.md",
]


def pin(path: str) -> dict[str, object]:
    data = (ROOT / path).read_bytes()
    return {"path": path, "size": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def as_repo_path(path: str) -> Path:
    return ROOT / path.replace("\\", "/")


sys.path.insert(0, str(ROOT / "tools"))
from omf import OmfReader  # noqa: E402

build_path = ROOT / "build/source-only-dos/build-report.json"
build = json.loads(build_path.read_text(encoding="utf-8"))
manifest = json.loads((ROOT / "layout/manifest.json").read_text(encoding="utf-8"))
debt_map = json.loads((ROOT / "work/data/s27_map.json").read_text(encoding="utf-8"))
scan = json.loads(
    (ROOT / "work/takeover/behavioral-oracle/debt-audit/reference-scan.json").read_text(
        encoding="utf-8"
    )
)
xver = json.loads(
    (ROOT / "evidence/cross_version/simantw_correspondence.json").read_text(encoding="utf-8")
)

unresolved = next(x for x in build["unresolved_data"] if x.get("id") == "dgroup_56fe")
historical = next(x for x in build["historical_data_debt"] if x.get("id") == "dgroup_56fe")
map_span = next(
    x for x in debt_map["ranges"] if x.get("frame") == "55B3" and x.get("off") == "56FE"
)
map_neighbors = [
    x
    for x in debt_map["ranges"]
    if x.get("frame") == "55B3" and x.get("off") in {"56B4", "56FE", "5702"}
]
manifest_rows = {
    key: manifest["modules"][key]
    for key in ("root:1CE2", "root:195A", "root:1E57")
}
tu_rows = {x["module"]: x for x in build["translation_units"] if x.get("module") in manifest_rows}

omf_summary: dict[str, object] = {}
for module, row in tu_rows.items():
    obj_path = as_repo_path(row["object"]["path"])
    obj = OmfReader().read_file(obj_path)
    omf_summary[module] = {
        "object_path": row["object"]["path"],
        "object_sha256": hashlib.sha256(obj_path.read_bytes()).hexdigest(),
        "data_segment_length": obj.segment_length("_DATA"),
        "data_publics": [
            {"name": p["name"], "offset": p["offset"]}
            for p in obj.publics
            if p["segment"] == "_DATA"
        ],
    }

game_scan = scan["function_reference_scan"]
direct_refs = game_scan["direct_data_operands"]["dgroup_56fe"]
immediate_candidates = game_scan["immediate_address_candidates"]["dgroup_56fe"]
relevant_xver = [
    p
    for p in xver["pairs"]
    if p.get("dos") in {"f_195A_0166", "f_1E57_0052", "f_1E57_00B1", "f_1E57_038E"}
]

source_texts = []
for path in sorted((ROOT / "src").rglob("*")):
    if path.suffix.lower() in {".c", ".asm"}:
        source_texts.append((path.relative_to(ROOT).as_posix(), path.read_text(encoding="utf-8", errors="replace")))
literal_56fe = [
    {"path": path, "line": n, "text": line.strip()[:180]}
    for path, body in source_texts
    for n, line in enumerate(body.splitlines(), 1)
    if re.search(r"(?i)(?:0x|\b)56fe\b", line)
]
negative_g5702 = [
    {"path": path, "line": n, "text": line.strip()[:180]}
    for path, body in source_texts
    for n, line in enumerate(body.splitlines(), 1)
    if re.search(r"g_5702\s*\[\s*-", line)
]

payload = {
    "schema": "simant-dos-dgroup-56fe-owner-v32-pins-v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    "scope": {"frame": "55B3", "offset": "56FE", "size": 4},
    "admission": False,
    "runtime_acceptance": False,
    "human_acceptance": False,
    "inputs": [pin(path) for path in PIN_PATHS],
    "current_report": {
        "status": build.get("status"),
        "translation_units": len(build["translation_units"]),
        "unresolved_data": unresolved,
        "historical_data_debt": historical,
    },
    "historical_map": {
        "span": map_span,
        "neighboring_ranges": map_neighbors,
    },
    "original_disassembly_index": {
        "scan_scope": game_scan.get("scope"),
        "direct_data_operands": direct_refs,
        "immediate_address_candidates": immediate_candidates,
    },
    "manifest_data_placements": {
        key: {
            "_DATA": manifest_rows[key].get("placements", {}).get("_DATA"),
            "source": manifest_rows[key].get("source"),
        }
        for key in manifest_rows
    },
    "current_source_omf": omf_summary,
    "source_census": {
        "literal_56fe_tokens_in_c_or_asm": literal_56fe,
        "negative_g5702_array_indices": negative_g5702,
        "scope_note": "Text census only; it does not prove absence of computed aliases or dynamic pointer flow.",
    },
    "cross_version": {
        "correspondence_schema": xver.get("schema"),
        "pairs_for_relevant_dos_functions": relevant_xver,
        "data_symbol_correspondence": "not represented in this function-pair table",
    },
}
OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
print(f"wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size} bytes)")
