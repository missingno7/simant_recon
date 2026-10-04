"""Targeted source-format research for the event decoder's 12 normal-state IDs.

Reads only the named asset indexes and their selected kind-2 DB records. It emits
hashes, row metadata, and the 12-byte typed Pic header; image payload bytes are
never emitted or copied. No compiler or game execution is involved.
"""

from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ASSETS = ROOT / "assets"
OUT = Path(__file__).with_name("resource-observations-v22.json")
IDS = list(range(0x3E8, 0x3F0)) + list(range(0x41A, 0x41E))
DBS = ("SHARED", "HCEGANT", "SOUND")
SOURCE_PINS = (
    "src/root/m0250.c",
    "src/root/m2662.c",
    "src/root/m259D.c",
    "src/root/m205F.c",
    "src/S20/m39F1.c",
    "src/root/m15F8.c",
    "src/root/m1986.c",
    "src/root/m19A9.c",
    "src/root/m1A53.c",
    "src/root/m277E.c",
    "src/root/m0000.c",
    "src/S09/m35F5.c",
    "src/S11/m35F5.c",
    "src/root/m0CDB.c",
    "src/root/m0BE8.c",
    "src/root/m0093.c",
    "src/data/d3D57.c",
    "src/S01/m32B5.asm",
    "src/S03/m3258.asm",
    "src/S00/m35A6.asm",
)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def parse_db(stem: str) -> dict:
    ndx_path = ASSETS / f"{stem}.NDX"
    dat_path = ASSETS / f"{stem}.DAT"
    if not ndx_path.is_file() or not dat_path.is_file():
        return {"present": False, "ndx_path": f"assets/{stem}.NDX", "dat_path": f"assets/{stem}.DAT"}

    ndx = ndx_path.read_bytes()
    count = struct.unpack_from("<h", ndx, 0)[0]
    table_start = 20
    table_end = table_start + count * 8
    if count < 0 or len(ndx) < table_end:
        raise ValueError(f"{stem}: source-readable prefix table is truncated")
    rows = []
    for i in range(count):
        offset, object_id, kind, flags = struct.unpack_from("<IhBB", ndx, table_start + i * 8)
        if object_id in IDS and kind == 2:
            rows.append((i, offset, object_id, flags))

    dat = dat_path.read_bytes()
    selected = []
    for row, offset, object_id, flags in rows:
        if offset + 24 > len(dat):
            raise ValueError(f"{stem}:{row}: DB header outside DAT")
        db_id, db_type, db_flags, size, extra = struct.unpack_from("<5h", dat, offset + 14)
        payload_start = offset + 24
        payload_end = payload_start + size
        if size < 12 or payload_end > len(dat):
            raise ValueError(f"{stem}:{row}: selected kind-2 payload is truncated or shorter than Pic header")
        pic_type, = struct.unpack_from("<h", dat, payload_start)
        mode = dat[payload_start + 2]
        pad = dat[payload_start + 3:payload_start + 8]
        width, height = struct.unpack_from("<hh", dat, payload_start + 8)
        selected.append({
            "row": row,
            "id": object_id,
            "id_hex": f"0x{object_id & 0xffff:04X}",
            "kind": 2,
            "index_flags": flags,
            "dat_record_offset": offset,
            "record_header_words": [db_id, db_type, db_flags, size, extra],
            "payload_size": size,
            "pic_header_hex_12_bytes": dat[payload_start:payload_start + 12].hex(),
            "pic_type_i16": pic_type,
            "pic_mode_u8": mode,
            "pic_pad_hex": pad.hex(),
            "width_i16": width,
            "height_i16": height,
            "height_positive": height > 0,
            "payload_within_dat": payload_end <= len(dat),
        })

    by_id = {r["id"]: r for r in selected}
    if len(by_id) != len(selected):
        raise ValueError(f"{stem}: duplicate selected kind-2 IDs")
    dims = [r for r in selected]
    return {
        "present": True,
        "ndx_path": f"assets/{stem}.NDX",
        "ndx_sha256": sha256(ndx_path),
        "ndx_size": len(ndx),
        "dat_path": f"assets/{stem}.DAT",
        "dat_sha256": sha256(dat_path),
        "dat_size": len(dat),
        "source_openindex_count": count,
        "source_openindex_table_start": table_start,
        "source_openindex_table_end": table_end,
        "ndx_trailing_bytes_after_source_read_prefix": len(ndx) - table_end,
        "selected_id_kind2_rows": selected,
        "selected_ids_missing_kind2": [f"0x{x:04X}" for x in IDS if x not in by_id],
        "selected_ids_with_nonpositive_height": [f"0x{x:04X}" for x in IDS if x in by_id and by_id[x]["height_i16"] <= 0],
        "selected_dimension_bounds": None if not dims else {
            "width_min": min(r["width_i16"] for r in dims),
            "width_max": max(r["width_i16"] for r in dims),
            "height_min": min(r["height_i16"] for r in dims),
            "height_max": max(r["height_i16"] for r in dims),
        },
    }


def main() -> None:
    asset_inputs = {stem: parse_db(stem) for stem in DBS}
    if asset_inputs["HCEGANT"]["selected_ids_missing_kind2"]:
        raise ValueError("HCEGANT supplied-bundle normal-state selector set is incomplete")
    if asset_inputs["HCEGANT"]["selected_ids_with_nonpositive_height"]:
        raise ValueError("HCEGANT supplied-bundle normal-state headers include nonpositive height")
    result = {
        "scope": "source-format read-only research for normal-state event picture IDs",
        "source_id_sets": {
            "nondeath_direction_0_to_7": [f"0x{x:04X}" for x in IDS[:8]],
            "death_cycle_0_to_3": [f"0x{x:04X}" for x in IDS[8:]],
        },
        "asset_inputs": asset_inputs,
        "source_sha256": {
            path: sha256(ROOT / path)
            for path in SOURCE_PINS
        },
        "read_limits": {
            "database_files": [f"assets/{stem}.{ext}" for stem in DBS for ext in ("NDX", "DAT") if (ASSETS / f"{stem}.{ext}").is_file()],
            "ndx_rows": "only count records beginning at the 20-byte source header offset",
            "dat_bytes_emitted": "selected record metadata and 12-byte Pic header only; no image payload bytes",
            "original_executable_or_oracle_read": False,
            "game_executed": False,
            "compiler_invoked": False,
        },
    }
    OUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(OUT)


if __name__ == "__main__":
    main()
