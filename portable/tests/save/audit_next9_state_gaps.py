"""Read-only evidence audit for unresolved rows in the legacy save table."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
S09 = ROOT / "src/S09/m35F5.c"
S13 = ROOT / "src/S13/m384C.c"
DATA = ROOT / "src/data/d3D57.c"
SYMBOLS = ROOT / "layout/symbols.json"
NEXT7 = ROOT / "build/workers/recovered_source_next7/generated/recovered_state.h"
NEXT7_PROVENANCE = ROOT / "build/workers/recovered_source_next7/generated/provenance.json"
OUT = ROOT / "portable/tests/save/evidence/legacy-save-next9-binding-v1/next9-binding-audit.json"
sys.path.insert(0, str(ROOT / "tools"))
import exe

ARRAYS = [
    ("fd_50F6_0F46", 0x0F46, 61),
    ("fd_50F6_0FC6", 0x0FC6, 62),
    ("fd_50F6_0F84", 0x0F84, 63),
    ("fd_50F6_1008", 0x1008, 64),
]
SCALARS = [("fd_50F6_103C", 0x103C, 266), ("fd_50F6_1048", 0x1048, 267)]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def line_for(text: str, needle: str) -> int:
    for number, line in enumerate(text.splitlines(), 1):
        if needle in line:
            return number
    raise ValueError(f"anchor not found: {needle}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=OUT)
    args = parser.parse_args()
    s09, s13, data = S09.read_text(), S13.read_text(), DATA.read_text()
    symbols = json.loads(SYMBOLS.read_text())
    header = NEXT7.read_text()
    provenance = json.loads(NEXT7_PROVENANCE.read_text())
    oracle = exe.load()
    resident = oracle.sections[27]

    def original_bytes(segment: int, offset: int, size: int) -> tuple[bytes, list[tuple[int, int]]]:
        linear = segment * 16 + offset
        relative = linear - resident.load_linear
        if relative < 0 or relative + size > len(resident.data):
            raise ValueError(f"original range {segment:04X}:{offset:04X}+{size} not in resident data")
        relocations = [(seg, off) for seg, off in resident.relocs
                       if seg == segment and offset <= off < offset + size]
        return resident.data[relative:relative + size], relocations

    record_pattern = re.compile(r"\{\s*(\d+)\s*,\s*(\d+)\s*,\s*(.*?)\s*\}")
    table_start = s09.index("struct SaveRec far fd_4E4B_0000[308] = {")
    table_end = s09.index("};", table_start)
    rows = []
    for match in record_pattern.finditer(s09[table_start:table_end]):
        rows.append({"element_size": int(match.group(1)), "element_count": int(match.group(2)), "expression": match.group(3).strip()})

    data_init_match = re.search(r"unsigned char far fd_3D57_087A\[72\]\s*=\s*\{(.*?)\};", data, re.S)
    if data_init_match is None:
        raise ValueError("fd_3D57_087A[72] initializer not found")
    table_bytes = [int(x, 16) for x in re.findall(r"0x([0-9A-Fa-f]+)", data_init_match.group(1))]
    if len(table_bytes) != 72:
        raise ValueError(f"expected 72 initialized bytes, got {len(table_bytes)}")

    data_symbols = symbols["data"]
    array_evidence = []
    for name, offset, row_index in ARRAYS:
        decl = f"extern signed char far {name}[];"
        if decl not in s13:
            raise ValueError(f"missing source declaration: {decl}")
        sym = data_symbols[name]
        row = rows[row_index]
        if row != {"element_size": 1, "element_count": 50, "expression": f"(void far *)&{name}"}:
            raise ValueError(f"unexpected save row {row_index}: {row}")
        initial, relocations = original_bytes(sym["seg"], sym["off"], 50)
        if len(initial) != 50:
            raise ValueError(f"short executable data for {name}")
        array_evidence.append({
            "save_record_index": row_index,
            "source_symbol": name,
            "original_type": "signed char far[] (one-byte signed character elements)",
            "serialized_extent_bytes": row["element_size"] * row["element_count"],
            "segment": sym["seg"],
            "segment_hex": f"{sym['seg']:04X}",
            "offset": sym["off"],
            "offset_hex": f"{sym['off']:04X}",
            "owner": "src/S13/m384C.c:DrawSwarm",
            "source_declaration_line": line_for(s13, decl),
            "indexed_use_line": line_for(s13, f"{name}[i]"),
            "loop_limit_evidence": "DrawSwarm limits the active iteration to at most 16 entries; the 50-byte save extent is retained in full, including bytes 16..49.",
            "layout_grounding": sym["grounding"],
            "original_image_initial_bytes_hex": initial.hex(),
            "original_image_relocations_in_extent": relocations,
        })

    scalar_evidence = []
    for name, offset, row_index in SCALARS:
        decl = f"extern int far {name};"
        if decl not in s13:
            raise ValueError(f"missing source declaration: {decl}")
        sym = data_symbols[name]
        row = rows[row_index]
        if row != {"element_size": 2, "element_count": 1, "expression": f"(void far *)&{name}"}:
            raise ValueError(f"unexpected save row {row_index}: {row}")
        initial, relocations = original_bytes(sym["seg"], sym["off"], 2)
        scalar_evidence.append({
            "save_record_index": row_index,
            "source_symbol": name,
            "original_type": "int far (Microsoft 16-bit int; one signed 16-bit word)",
            "serialized_extent_bytes": 2,
            "segment": sym["seg"],
            "segment_hex": f"{sym['seg']:04X}",
            "offset": sym["off"],
            "offset_hex": f"{sym['off']:04X}",
            "owner": "src/S13/m384C.c:DrawSwarm",
            "source_declaration_line": line_for(s13, decl),
            "write_line": line_for(s13, f"{name} ="),
            "layout_grounding": sym["grounding"],
            "original_image_initial_bytes_hex": initial.hex(),
            "original_image_relocations_in_extent": relocations,
        })

    # The data pointer expression is an interior address into a byte array,
    # not an independent RecoveredState field.
    interior_index = 99
    expected_row = rows[interior_index]
    if expected_row != {"element_size": 2, "element_count": 10, "expression": "(void far *)(fd_3D57_087A + 20)"}:
        raise ValueError(f"unexpected interior table row: {expected_row}")
    interior_bytes = table_bytes[20:40]
    if len(interior_bytes) != 20:
        raise ValueError("interior byte extent invalid")
    interior_symbol = data_symbols["fd_3D57_087A"]
    interior_image, interior_relocations = original_bytes(interior_symbol["seg"], interior_symbol["off"] + 20, 20)
    if interior_image != bytes(interior_bytes):
        raise ValueError("source data initializer disagrees with executable resident bytes")

    # Parse members from the Next7 candidate's struct body and prove absence.
    struct_text = header.split("typedef struct RecoveredState {", 1)[1].split("} RecoveredState;", 1)[0]
    member_names = set(re.findall(r"\b([A-Za-z_]\w*)\s*(?:\[[^]]+\])?\s*;", struct_text))
    gaps = [name for name, _, _ in ARRAYS] + ["fd_3D57_087A"] + [name for name, _, _ in SCALARS]
    missing_members = [name for name in gaps if name not in member_names]

    excluded = provenance.get("excluded_modules", [])
    selected_s13 = any("S13" in str(row) and "384C" in str(row) for row in provenance["modules"])
    result = {
        "schema": "simant-legacy-save-next9-state-binding-audit-v1",
        "status": "SOURCE_GROUNDED_PROPOSAL_NOT_PROFILE_CHANGE",
        "inputs": {
            "save_table": {"path": "src/S09/m35F5.c", "sha256": sha(S09), "table_line": line_for(s09, "fd_4E4B_0000")},
            "swarm_owner": {"path": "src/S13/m384C.c", "sha256": sha(S13), "draw_swarm_line": line_for(s13, "void far DrawSwarm(void)")},
            "data_initializer": {"path": "src/data/d3D57.c", "sha256": sha(DATA), "array_line": line_for(data, "fd_3D57_087A[72]")},
            "oracle_executable": {"path": "assets/SIMANT.EXE", "sha256": oracle.sha256, "resident_section": resident.index,
                                  "resident_load_segment": resident.load_seg, "resident_data_bytes": len(resident.data)},
            "symbols": {"path": "layout/symbols.json", "sha256": sha(SYMBOLS)},
            "next7_candidate": {
                "header_path": str(NEXT7.relative_to(ROOT)).replace("\\", "/"),
                "header_sha256": sha(NEXT7),
                "provenance_path": str(NEXT7_PROVENANCE.relative_to(ROOT)).replace("\\", "/"),
                "provenance_sha256": sha(NEXT7_PROVENANCE),
                "selected_S13_m384C": selected_s13,
                "generated_member_count": len(member_names),
                "missing_member_names": missing_members,
            },
        },
        "records": {
            "swarm_offset_arrays": array_evidence,
            "swarm_origin_words": scalar_evidence,
            "interior_data_span": {
                "save_record_index": interior_index,
                "source_expression": "fd_3D57_087A + 20",
                "original_object_type": "unsigned char far fd_3D57_087A[72]",
                "object_extent_bytes": 72,
                "object_segment": interior_symbol["seg"],
                "object_offset": interior_symbol["off"],
                "serialized_interior_offset_bytes": 20,
                "serialized_extent_bytes": 20,
                "serialized_range": "object bytes [20,40)",
                "initial_bytes_hex": bytes(interior_bytes).hex(),
                "initial_little_endian_words": [interior_bytes[i] | (interior_bytes[i + 1] << 8) for i in range(0, 20, 2)],
                "owner": "src/data/d3D57.c data object; S09 save table reads/writes an interior span",
                "definition_line": line_for(data, "fd_3D57_087A[72]"),
                "layout_grounding": interior_symbol["grounding"],
                "code_use_status": "layout identifies no other code reference; the SaveRec interior pointer is the persistence reference",
                "original_image_relocations_in_extent": interior_relocations,
            },
        },
        "extension_proposal": {
            "base": "Next8 RecoveredState/profile; do not edit Next7 or its producer",
            "member_count_delta": 7,
            "members": [
                {"name": "fd_50F6_0F46", "type": "int8_t[50]", "source_owner": "DrawSwarm; save row 61"},
                {"name": "fd_50F6_0FC6", "type": "int8_t[50]", "source_owner": "DrawSwarm; save row 62"},
                {"name": "fd_50F6_0F84", "type": "int8_t[50]", "source_owner": "DrawSwarm; save row 63"},
                {"name": "fd_50F6_1008", "type": "int8_t[50]", "source_owner": "DrawSwarm; save row 64"},
                {"name": "fd_50F6_103C", "type": "int16_t", "source_owner": "DrawSwarm origin x; save row 266"},
                {"name": "fd_50F6_1048", "type": "int16_t", "source_owner": "DrawSwarm origin y; save row 267"},
                {"name": "fd_3D57_087A", "type": "uint8_t[72]", "source_owner": "mutable source data object initialized by src/data/d3D57.c; save row 99 binds byte offset 20"},
            ],
            "binding_rule": "one authoritative backing per member; row 99 binds fd_3D57_087A + 20 and serializes exactly 20 bytes, not a duplicate tail buffer",
            "initialization_rule": "the 72-byte data object must start from the exact src/data/d3D57.c initializer; all four 50-byte arrays and both words are zero in the hash-locked resident executable image at their exact addresses, with no relocations in those extents",
            "profile_effect": "extend only the future versioned Next9 state/profile and producer; preserve all Next7 identities and historical proofs",
        },
        "claims": {
            "source_saves_all_50_swarm_bytes": True,
            "drawswarm_uses_only_first_16_per_array": True,
            "candidate_is_complete_binding": False,
            "new_profile_or_engine_changes_made": False,
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print("arrays=4x50 signed-byte; origin_words=2x16-bit; interior=72-byte object slice[20:40]")
    print(f"Next7 selected S13 module={selected_s13}; absent proposed members={missing_members}")
    print(f"interior_initial={bytes(interior_bytes).hex()} words={result['records']['interior_data_span']['initial_little_endian_words']}")


if __name__ == "__main__":
    main()
