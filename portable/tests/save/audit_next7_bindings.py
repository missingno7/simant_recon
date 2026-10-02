"""Compare S09's saved-state rows with the diagnostic Next7 state header."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
INVENTORY = ROOT / "portable/tests/dialogs/evidence/savegame-format-source-inventory-v1/save-records.json"
SOURCE = ROOT / "src/S09/m35F5.c"
DEFAULT_HEADER = ROOT / "build/workers/recovered_source_next7/generated/recovered_state.h"
DEFAULT_PROVENANCE = ROOT / "build/workers/recovered_source_next7/generated/provenance.json"
DEFAULT_OUTPUT = ROOT / "portable/tests/save/evidence/legacy-save-codec-v1/next7-binding-audit.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def header_fields(header: str) -> dict[str, tuple[str, int]]:
    fields: dict[str, tuple[str, int]] = {}
    in_state = False
    for line in header.splitlines():
        if "typedef struct RecoveredState {" in line:
            in_state = True
            continue
        if in_state and line.strip() == "} RecoveredState;":
            break
        if not in_state:
            continue
        match = re.match(r"\s*(.*?)\s+([A-Za-z_]\w*)\s*((?:\[[^]]+\])*)\s*;", line)
        if not match:
            continue
        ctype, name, dims_text = match.groups()
        dims = [int(n) for n in re.findall(r"\[(\d+)\]", dims_text)]
        if "int32_t" in ctype or "uint32_t" in ctype:
            width = 4
        elif "int16_t" in ctype or "uint16_t" in ctype:
            width = 2
        elif "int8_t" in ctype or "uint8_t" in ctype or "char" in ctype:
            width = 1
        else:
            width = None
        extent = None if width is None else width
        if extent is not None:
            for dim in dims:
                extent *= dim
        fields[name] = (ctype + dims_text, extent)
    return fields


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--header", type=Path, default=DEFAULT_HEADER)
    parser.add_argument("--provenance", type=Path, default=DEFAULT_PROVENANCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    fields = header_fields(args.header.read_text(encoding="utf-8"))
    rows = []
    missing = []
    for row in inventory["table"]["records"]:
        expr = row["pointer_expression"]
        match = re.fullmatch(r"&([A-Za-z_]\w*)", expr)
        entry = {
            "index": row["index"],
            "source_expression": expr,
            "serialized_bytes": row["serialized_bytes"],
            "payload_offset": sum(x["serialized_bytes"] for x in inventory["table"]["records"][:row["index"]]),
        }
        if match:
            name = match.group(1)
            entry["candidate_field"] = name
            if name in fields:
                ctype, extent = fields[name]
                entry["candidate_type"] = ctype
                entry["candidate_extent_bytes"] = extent
                entry["status"] = "bound-name-and-extent" if extent is not None and extent >= row["serialized_bytes"] else "extent-unresolved-or-too-small"
            else:
                entry["status"] = "field-absent"
        elif expr == "(fd_3D57_087A + 20)":
            entry["candidate_field"] = "fd_3D57_087A"
            entry["interior_offset_bytes"] = 20
            entry["status"] = "interior-base-field-absent"
        else:
            entry["status"] = "expression-unresolved"
        rows.append(entry)
        if entry["status"] != "bound-name-and-extent":
            missing.append(entry)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    result = {
        "schema": "simant-save-next7-binding-audit-v1",
        "status": "DIAGNOSTIC_ONLY_NOT_PRODUCTION_BINDING",
        "source_table": {"path": "src/S09/m35F5.c", "sha256": sha(SOURCE)},
        "inventory": {"path": "portable/tests/dialogs/evidence/savegame-format-source-inventory-v1/save-records.json", "sha256": sha(INVENTORY)},
        "candidate": {
            "name": "Next7 diagnostic RecoveredState candidate",
            "header_path": str(args.header.relative_to(ROOT)).replace("\\", "/"),
            "header_sha256": sha(args.header),
            "provenance_path": str(args.provenance.relative_to(ROOT)).replace("\\", "/"),
            "provenance_sha256": sha(args.provenance),
            "warning": "This generated candidate is diagnostic and is not a production state binding. Missing rows remain explicit; they are not zero-filled.",
        },
        "record_count": len(rows),
        "bound_name_and_extent_count": len(rows) - len(missing),
        "unresolved_count": len(missing),
        "unresolved": missing,
        "records": rows,
    }
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"rows={len(rows)} bound={len(rows)-len(missing)} unresolved={len(missing)}")
    for row in missing:
        print(f"{row['index']}: {row['source_expression']} ({row['serialized_bytes']} bytes): {row['status']}")


if __name__ == "__main__":
    main()
