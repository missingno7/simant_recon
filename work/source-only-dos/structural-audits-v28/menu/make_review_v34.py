from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "build" / "workers" / "dos_menu_resource_bound_v34"

SOURCE_PATHS = [
    "src/root/m1FD2.c",
    "src/S17/m384C.c",
    "src/S10/m35F5.c",
    "src/S20/m39F1.c",
    "src/root/m205F.c",
    "src/root/m1A53.c",
    "src/root/m1A28.c",
    "src/root/m1986.c",
    "src/root/m19A9.c",
    "src/root/m1B05.asm",
    "src/root/m15F8.c",
    "evidence/behavior/functions/o10_35F5_0384/contracts/host-service-v1/module.c",
    "evidence/behavior/functions/FindIndex/module.c",
    "build/workers/dos_delay_word_owner_v33/source-addendum-v33.json",
    "build/workers/dos_delay_word_owner_v33/source-addendum-v33.md",
]
REGISTRY_PATHS = [
    "layout/symbols.json",
    "layout/manifest.json",
    "layout/oracle.lock.json",
    "layout/functions.json",
    "work/source-only-dos/static-completeness/index-v1.json",
    "work/source-only-dos/static-completeness/FindIndex.json",
    "evidence/behavior/manifest.json",
    "evidence/behavior/functions/FindIndex/evidence.json",
]


def pin(path: str) -> dict[str, object]:
    p = ROOT / path
    b = p.read_bytes()
    return {"path": path, "bytes": len(b), "sha256": hashlib.sha256(b).hexdigest()}


def lzss_decode(src: bytes, expected: int) -> tuple[bytes, int]:
    """Decode the 4 KiB LZSS stream implemented symbolically in src/root/m1B05.asm."""
    ring = bytearray([0x20] * 4096)
    ring_pos = 0xFEE
    out = bytearray()
    i = 0
    while len(out) < expected:
        if i >= len(src):
            raise ValueError("truncated LZSS flag byte")
        flags = src[i]
        i += 1
        for bit in range(8):
            if len(out) >= expected:
                break
            if flags & (1 << bit):
                if i >= len(src):
                    raise ValueError("truncated LZSS literal")
                value = src[i]
                i += 1
                out.append(value)
                ring[ring_pos] = value
                ring_pos = (ring_pos + 1) & 0xFFF
            else:
                if i + 1 >= len(src):
                    raise ValueError("truncated LZSS match")
                lo, hi = src[i], src[i + 1]
                i += 2
                match_pos = lo | ((hi & 0xF0) << 4)
                match_len = (hi & 0x0F) + 3
                for j in range(match_len):
                    if len(out) >= expected:
                        break
                    value = ring[(match_pos + j) & 0xFFF]
                    out.append(value)
                    ring[ring_pos] = value
                    ring_pos = (ring_pos + 1) & 0xFFF
    return bytes(out), i


def relptr(data: bytes, at: int) -> tuple[int, int]:
    value = struct.unpack_from("<I", data, at)[0]
    return value & 0xFFFF, value >> 16


def pointer_table(data: bytes, at: int) -> list[int]:
    values: list[int] = []
    for i in range((len(data) - at) // 4):
        offset, segment = relptr(data, at + 4 * i)
        if offset == 0 and segment == 0:
            return values
        if segment != 0 or offset >= len(data):
            raise ValueError("resource pointer outside its expanded payload")
        values.append(offset)
    raise ValueError("resource pointer table has no null sentinel")


def inventory_index(ndx_path: Path, dat_path: Path) -> dict[str, object]:
    ix = ndx_path.read_bytes()
    count = struct.unpack_from("<H", ix, 0)[0]
    if 20 + count * 8 > len(ix):
        raise ValueError(f"index extent exceeds {ndx_path.name}")
    menu_rows = []
    all_rows = []
    for ordinal in range(count):
        offset, object_id, kind, flags = struct.unpack_from("<IhBB", ix, 20 + 8 * ordinal)
        all_rows.append((kind, object_id))
        if kind == 6:
            row: dict[str, object] = {
                "ordinal_zero_based": ordinal,
                "object_id": object_id,
                "kind": kind,
                "flags": flags,
                "record_offset": offset,
            }
            if offset + 24 <= dat_path.stat().st_size:
                db = dat_path.read_bytes()
                record_size = struct.unpack_from("<h", db, offset + 20)[0]
                row["record_packed_size"] = record_size
            menu_rows.append(row)
    return {
        "ndx": ndx_path.name,
        "dat": dat_path.name,
        "ndx_bytes": len(ix),
        "dat_bytes": dat_path.stat().st_size,
        "ndx_sha256": hashlib.sha256(ix).hexdigest(),
        "dat_sha256": hashlib.sha256(dat_path.read_bytes()).hexdigest(),
        "index_entry_count": count,
        "kind6_entries": menu_rows,
        "menu_id0_present": any(k == 6 and i == 0 for k, i in all_rows),
        "menu_id1_present": any(k == 6 and i == 1 for k, i in all_rows),
    }


pins = [pin(p) for p in SOURCE_PATHS]
registry_pins = [pin(p) for p in REGISTRY_PATHS]
asset_paths = sorted(p for p in (ROOT / "assets").glob("*") if p.is_file() and p.suffix.upper() in {".DAT", ".NDX"})
assets = []
for ndx in sorted((ROOT / "assets").glob("*.NDX")):
    dat = ndx.with_suffix(".DAT")
    if dat.exists():
        assets.append(inventory_index(ndx, dat))

shared = next((x for x in assets if x["ndx"] == "SHARED.NDX"), None)
if shared is None:
    raise ValueError("SHARED index is unavailable")
rows = [x for x in shared["kind6_entries"] if x["object_id"] == 0]
if len(rows) != 1:
    raise ValueError("expected exactly one SHARED kind-6 object 0")
row = rows[0]
dat = (ROOT / "assets" / "SHARED.DAT").read_bytes()
record_offset = int(row["record_offset"])
packed_size = int(row["record_packed_size"])
packed_record = dat[record_offset + 24: record_offset + 24 + packed_size]
if len(packed_record) != packed_size or packed_size < 2:
    raise ValueError("truncated SHARED menu record")
expanded_size = struct.unpack_from("<H", packed_record, 0)[0]
expanded, compressed_bytes_consumed = lzss_decode(packed_record[2:], expanded_size)
titles_offset, titles_segment = relptr(expanded, 0)
if titles_segment != 0:
    raise ValueError("unexpected nonzero segment in source resource pointer")
titles = pointer_table(expanded, titles_offset)
for string_offset in titles:
    if expanded.find(b"\0", string_offset) < 0:
        raise ValueError("unterminated title string in resource")
menu_tables: list[int] = []
for slot in range(17):
    offset, segment = relptr(expanded, slot * 4)
    if offset == 0 and segment == 0:
        break
    if segment != 0:
        raise ValueError("unexpected nonzero segment in MenuData table pointer")
    menu_tables.append(len(pointer_table(expanded, offset)))

resource = {
    "database": "SHARED",
    "object_id": 0,
    "kind": 6,
    "kind_name_from_src_root_m19A9": "MENU",
    "index_ordinal_zero_based": row["ordinal_zero_based"],
    "index_record_offset": record_offset,
    "index_flags": row["flags"],
    "packed_record_bytes": packed_size,
    "expanded_resource_bytes": len(expanded),
    "compressed_input_bytes_consumed": compressed_bytes_consumed,
    "expanded_resource_sha256": hashlib.sha256(expanded).hexdigest(),
    "menu_data_titles_pointer_offset": titles_offset,
    "nonnull_title_pointer_count": len(titles),
    "null_sentinel_present": True,
    "active_item_table_counts": menu_tables[1:],
    "raw_or_expanded_resource_bytes_embedded": False,
    "strings_embedded": False,
}

review = {
    "schema": "simant-dos-menu-resource-bound-v34",
    "status": "REVIEW_ONLY_GATE_OPEN",
    "existing_gate": {"name": "menu-table-cross-owner-layout", "status": "OPEN"},
    "scope": "bounded source and installed-resource inventory; no production source, manifest, gate, or promotion edits",
    "claims": {
        "array_views": {
            "xpos": "fd_50F6_46A8, int far[]",
            "widths": "fd_50F6_46BC, int far[]",
            "delay": "fd_50F6_46D0, signed int far word",
            "handle": "fd_50F6_46D2, excluded neighboring pointer/table storage",
            "aliases": [
                "widths[10] is 50F6:46D0 (delay)",
                "xpos[10] is 50F6:46BC (widths[0])",
                "xpos[20] is 50F6:46D0 (delay)",
            ],
        },
        "writer": {
            "function": "f_1FD2_0663",
            "loop_shape": "two uncapped null-sentinel passes over g_6054->titles",
            "first_pass": "writes widths[i] and only afterward records g_604C=i",
            "second_pass": "resets i and writes xpos[i]",
            "mode_resource_count_is_not_a_source_capacity": True,
        },
        "startup_selection": {
            "source": "src/S20/m39F1.c::IBMInitStuff",
            "condition": "if g_3DB2 == 320, try MENU object 1; if it is missing, try object 0; otherwise try object 0 directly",
            "failure": "Punt(\"Cannot load menu\") if the selected/fallback object cannot be loaded",
            "lookup": "db_LoadObject searches currently open db_handles in order and returns the first DBRecall hit",
            "open_database_order": "optional language, shared, optional lrshare for modes 2/4, then adapter/mode database; sound is opened later in main",
            "adapter_database_name": "f_205F_0004 appends \"nt\" to g_629A[g_5A97]",
        },
        "installed_resource_result": {
            "supplied_dat_ndx_pairs": [x["ndx"] for x in assets],
            "kind6_object_1_in_supplied_indices": any(x["menu_id1_present"] for x in assets),
            "kind6_object_0_locations": [x["ndx"] for x in assets if x["menu_id0_present"]],
            "bundled_menu_object_0": resource,
            "bundled_object_0_title_count_below_overlap": len(titles) < 10,
            "scope_limit": "This count is for the exact SHARED object 0 in the supplied assets. Optional language.dat, lrshare, and other adapter databases are not present here, so their first-hit resources and object-1 count are not established.",
        },
        "ownership_model": {
            "result": "resource/index-owned for the observed menu payload; the C loader selects and relocates the loaded pointer graph, while the resource count is carried by the loaded MENU object",
            "effective_index_source": {
                "path": "evidence/behavior/functions/FindIndex/module.c",
                "status": "BEHAVIOR_EXACT_CONFIRMED",
                "whole_module": True,
                "module": "root:1986",
                "preconditions": "sorted valid index arrays and valid database handles, as recorded by the strict review",
                "canonical_note": "src/root/m1986.c keeps a scaffolded historical draft, but the strict-effective source-only module supplies the complete FindIndex body; source-level lookup behavior is not open on that path",
                "historical_bytes": "behavioral closure does not claim historical byte identity",
            },
        },
        "gate_disposition": "KEEP OPEN: object 0 in SHARED is bounded at five titles, but object 1 and optional/mode-specific first-hit resources are not inventoried; no source cap exists, and the pointer arrays physically alias after ten entries. FindIndex lookup behavior is closed by its strict-effective whole-module source under documented preconditions, so the remaining frontier is missing resource coverage and count.",
    },
    "pins": {
        "current_source_files": pins,
        "current_registries": registry_pins,
        "installed_dat_ndx_pairs": assets,
        "oracle_executable_read": False,
    },
    "research_method": {
        "ndx_entry_format": "20-byte index header followed by 8-byte entries: 32-bit data offset, 16-bit object ID, 8-bit kind, 8-bit flags; this matches src/root/m1986.c and src/root/m19A9.c",
        "menu_kind": "kind 6 is MENU in src/root/m19A9.c::g_36F6",
        "resource_decode": "the SHARED object 0 payload was decoded in memory with the ring-buffer LZSS structure and parameters in src/root/m1B05.asm; output retained only expanded size, pointer counts, table counts and SHA-256",
        "original_asset_bytes_in_artifact": False,
    },
}

(OUT / "review-v34.json").write_text(json.dumps(review, indent=2) + "\n", encoding="utf-8")

lines = [
    "# DOS menu resource-bound review v34",
    "",
    "**Disposition: investigation only; `menu-table-cross-owner-layout` stays OPEN.** No production source or canonical ownership file was changed.",
    "",
    "The `f_1FD2_0663` source walks `g_6054->titles` twice with null sentinels and no cap. It writes `fd_50F6_46BC[i]` before recording `g_604C`, then resets `i` and writes `fd_50F6_46A8[i]`. The views alias at ten-entry offsets: `widths[10] == fd_50F6_46D0`, `xpos[10] == widths[0]`, and `xpos[20] == fd_50F6_46D0`. The neighboring `fd_50F6_46D2` table remains outside this review.",
    "",
    "`IBMInitStuff` selects the resource from screen width: at `g_3DB2 == 320`, it tries MENU object 1 and falls back to object 0; otherwise it loads object 0. `db_LoadObject` searches the currently open databases in order. The source opens optional `language`, then `shared`, optional `lrshare` in modes 2/4, then the adapter database; `sound` opens later. The adapter database name is the selected prefix plus `nt`.",
    "",
    "The supplied DAT/NDX pairs are HCEGANT, SHARED and SOUND. Their indexes contain no kind-6 object 1. SHARED contains kind-6 object 0. Using the LZSS decoder shape pinned in `src/root/m1B05.asm`, its MENU record expands to 514 bytes and has five non-null title pointers followed by a null sentinel; its five active item tables have counts 8, 7, 8, 6 and 6. The expanded payload is pinned by SHA-256 in the JSON. This establishes the bound for this exact object 0, whose five-title writer pass does not reach the alias offsets.",
    "",
    "The observed payload is resource/index-owned: C selects and relocates the loaded pointer graph, while the count comes from the database object. The canonical historical draft at `src/root/m1986.c` keeps a scaffold, but the effective source-only set registers `evidence/behavior/functions/FindIndex/module.c` as a strict, whole-module `BEHAVIOR_EXACT_CONFIRMED` source for `root:1986`; its lookup behavior is closed under the reviewed valid-index preconditions. Optional language and mode databases are absent from the supplied assets, so object 1's count and any first-hit resource in those databases remain open. The remaining gate is resource coverage and count, not unresolved lookup control flow.",
    "",
    "## Current source and registry pins",
    "",
    "Full SHA-256 values below pin the exact files reviewed; the JSON also records sizes and the DAT/NDX hashes.",
    "",
    "| File | SHA-256 |",
    "|---|---|",
]
for p in pins + registry_pins:
    lines.append(f"| `{p['path']}` | `{p['sha256']}` |")
lines += [
    "",
    "No executable or resource bytes, decoded strings, or resource dumps are embedded in this worker artifact. The resource parse was performed in memory and retained as hashes/counts only.",
]
(OUT / "review-v34.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"wrote {OUT / 'review-v34.md'} and {OUT / 'review-v34.json'}")
print(f"SHARED MENU id=0: {len(titles)} titles; item table counts {menu_tables[1:]}; expanded SHA-256 {resource['expanded_resource_sha256']}")
print(f"kind-6 object 1 present in supplied indices: {any(x['menu_id1_present'] for x in assets)}")
