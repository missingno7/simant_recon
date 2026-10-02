#!/usr/bin/env python3
"""Regenerate the reviewed inventory of residual game-data byte spans."""
from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import exe  # noqa: E402

OUT_JSON = ROOT / "work/takeover/behavioral-oracle/data-debt.json"
OUT_MD = ROOT / "work/takeover/behavioral-oracle/data-debt.md"

# Source-level anchors are intentionally conservative. The original bytes and
# provenance ranges are derived below; these fields only summarize reviewed use.
REVIEW = {
    "far_data": {
        "classification": "PARAGRAPH_ALIGNMENT_CANDIDATE",
        "purpose": "12 zero bytes immediately before the FAR_BSS frame at 50F6; linear range ends on the next paragraph.",
        "references": ["build/link/provenance.json: debt:far_data at section-27 file range",
                       "work/data/s27_map.md: FAR_BSS 50F6 and paragraph-fill accounting"],
        "ownership": "No game symbol or function reads/writes this gap in the current ownership evidence.",
        "next_step": "Confirm the original linker record/SEGDEF alignment rule before reclassifying as generated fill.",
    },
    "dgroup_2100": {
        "classification": "MEANINGFUL_GRAPHICS_TABLES_OWNER_SPLIT_UNRESOLVED",
        "purpose": "First 8 bytes are pixel bit masks; next 16 bytes are a byte lookup copied as eight words.",
        "references": ["layout/symbols.json:data.g_2100", "layout/symbols.json:data.g_2108",
                       "src/S00/m31AD.asm:2884,3606-3608", "src/S01/m3126.asm:1711",
                       "work/data/s27_map.md: 2100-2117 S00 object split ambiguity"],
        "ownership": "Original source anchors establish both tables and consumers. Exact defining object split S00A/S00B is unresolved; do not assign the data to a convenient module without a relocation/order proof.",
        "next_step": "Try natural symbolic table definitions in the historically correct S00 object split; retain S01 as an external reference and verify all existing claims/data order.",
    },
    "dgroup_2328": {
        "classification": "MEANINGFUL_LOW_NIBBLE_LOOKUP_EXACTLY_OWNED",
        "purpose": "16-byte low-nibble colour lookup paired with the 16-byte high-nibble table at DGROUP:2318.",
        "references": ["src/S03/m3253.asm:53,61-63", "layout/symbols.json:data.g_2318",
                       "build/workers/behavior_data/m3253.asm", "work/data/s27_map.md: S03:3253 private DATA"],
        "ownership": "o03_3253_002F starts from 2318, advances BX by 10h for the second XLAT, then restores it. The symbolic 16-byte contribution was promoted through the strict gate; the resulting module retains both existing ASM claims, 48 private DATA bytes, and TU-order checks.",
        "next_step": "Closed by the exact S03:3253 data contribution. Preserve its separate historical exact proof; this audit does not reclassify any remaining span.",
    },
    "dgroup_56fe": {
        "classification": "ZERO_DATA_OWNER_HINT_NO_FIELD_SEMANTICS",
        "purpose": "Four zero bytes directly before the placed word g_5702.",
        "references": ["work/data/s27_map.json: DGROUP:56FE owner root:195A; adjacent 5702 is root:1E57/_DATA",
                       "layout/symbols.json:data.g_5702"],
        "ownership": "The map associates this extent with root:195A, but no field-level symbol or typed source declaration establishes what the four bytes represent.",
        "next_step": "Inspect root:195A operands and original allocation/object order; keep the four bytes explicit until a field/owner is established.",
    },
    "dgroup_5a28": {
        "classification": "PARTLY_ANCHORED_STATE_RECORD_LEADING_WORD_UNKNOWN",
        "purpose": "First two bytes of the 10-byte root:1F58 range; the next eight bytes are named keyboard/interrupt state.",
        "references": ["work/data/s27_map.json: DGROUP:5A28 owner root:1F58, extent 10 bytes",
                       "layout/symbols.json:data.g_5A2A,g_5A2C,g_5A2E,g_5A30"],
        "ownership": "Known fields at 5A2A/5A2C are pending key words; 5A2E/5A30 save the INT 23h vector. The two leading zeros have no identified read/write or name.",
        "next_step": "Review root:1F58 initialization/use of its 10-byte state block to identify the leading word; otherwise leave it unowned.",
    },
    "dgroup_5a96": {
        "classification": "PARTLY_TYPED_MULTI_MODULE_UI_STATE_BLOCK",
        "purpose": "First 26 bytes of a 1,360-byte unplaced UI/data region shared by multiple root modules.",
        "references": ["work/data/s27_map.json: DGROUP:5A96 owner root:1FBD,21FA,1D8E,1E57,1B73,1CE2",
                       "layout/symbols.json:data.g_5A97,g_5A9C,g_5AAC,g_5AAE",
                       "src/root/m1B73.asm:352-359,387-388", "src/root/m1FBD.asm:13-17,38,86,123"],
        "ownership": "Known byte g_5A97 selects a display path; 5A9C is passed as a far pointer; 5AAC/5AAE are saved cursor far-pointer words. The remaining leading bytes do not yet have complete field meanings. Source m1FBD provides typed text-bitmap fields starting at 5ABA, outside this 26-byte span, illustrating that the larger region is not one opaque blob.",
        "next_step": "Partition the entire 5A96-5FE5 area by source-level symbols, initialization, and module data-order evidence; do not assign all 1,360 bytes to one consumer.",
    },
    "dgroup_60b0": {
        "classification": "UNREFERENCED_UI_RECORD_WITH_FAR_RELOCATION",
        "purpose": "18-byte record, nine nonzero bytes, with one relocation at DGROUP:60BA (byte +10).",
        "references": ["work/data/s27_map.json: DGROUP:60B0 owner unreferenced, 18 bytes, one relocation",
                       "layout/manifest.json: following placement S20:39F1/_DATA begins at 60C2"],
        "ownership": "A relocated word proves a far-pointer-like field at +10, but no accepted source reference identifies its record type or intended owner. The pointer bytes alone do not establish semantics.",
        "next_step": "Resolve the relocated target and search original accesses to 60B0..60C1; keep all bytes explicit until an owning declaration is supported.",
    },
    "dgroup_68ac": {
        "classification": "MEANINGFUL_EDGE_MASK_TABLE_OWNER_UNRESOLVED",
        "purpose": "Ten nonzero edge/bit masks immediately before the nine-entry far dispatch table at 68B6.",
        "references": ["src/S01/m32B5.asm:120 (SS:[BX+68AC])",
                       "src/root/m277E.c:32,73 (g_68B6 dispatch table)",
                       "work/data/s27_map.json: DGROUP:68AC unplaced, 10 bytes"],
        "ownership": "The direct original operand establishes indexed consumption of the mask bytes. The following placed g_68B6 table starts at 68B6; a relocation at 68B8 belongs to that next table, not the ten-byte gap.",
        "next_step": "Identify the defining source module/object for the SS-indexed mask lookup and verify its data contribution/order.",
    },
    "dgroup_79f0": {
        "classification": "ZERO_DATA_RUNTIME_ADJACENCY_UNRESOLVED",
        "purpose": "Twelve zero bytes followed by 03 00, before the runtime ctype table at DGROUP:7A1E. This matches the candidate __fheap declaration in llibcr.lib fdata.asm, but library membership and source ownership are not proven.",
        "references": ["layout/symbols.json:data._ctype at 55B3:7A1E",
                       "work/data/s27_map.md: runtime DGROUP data begins at 7700"],
        "ownership": "The bytes lie in the runtime-DGROUP address interval adjacent to _ctype; no source/header field has been identified for 79F0-79FD. Zero values do not prove padding or harmlessness.",
        "next_step": "Compare runtime member SEGDEF/COMMON placement and original data refs around 79F0; separate runtime ownership from game data only with member evidence.",
    },
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def json_ref(root: Path, path: str) -> dict:
    p = root / path
    return {"path": path, "sha256": sha(p)}


def make_inventory() -> dict:
    x = exe.load()
    progress = json.loads((ROOT / "docs/progress.json").read_text(encoding="utf-8"))
    provenance = json.loads((ROOT / "build/link/provenance.json").read_text(encoding="utf-8"))
    data_map = json.loads((ROOT / "work/data/s27_map.json").read_text(encoding="utf-8"))
    section = x.sections[27]
    section_lo = section.data_file_offset
    section_hi = section_lo + len(section.data)
    debt_ranges = []
    for item in provenance["ranges"]:
        lo, hi = item["file"]
        a, b = max(lo, section_lo), min(hi, section_hi)
        if a < b and item["class"] in ("debt:far_data", "debt:dgroup_data"):
            debt_ranges.append((a, b, item))
    debt_ranges.sort()
    if len(debt_ranges) != 8 or sum(b - a for a, b, _ in debt_ranges) != 110:
        raise SystemExit(f"expected eight remaining literal debt spans totaling 110 bytes, found {len(debt_ranges)} / {sum(b-a for a,b,_ in debt_ranges)}")

    spans = []
    for start, end, prov in debt_ranges:
        linear_start = section.load_linear + (start - section_lo)
        linear_end = section.load_linear + (end - section_lo)
        if 0x55B30 <= linear_start < 0x5E5EC:
            frame, offset = "55B3", linear_start - 0x55B30
        else:
            frame, offset = None, None
        key = "far_data" if prov["class"] == "debt:far_data" else f"dgroup_{offset:04x}"
        if key not in REVIEW:
            raise SystemExit(f"missing reviewed classification for span {key}")
        data = x.raw[start:end]
        relocs = []
        for seg, off in section.relocs:
            site = seg * 16 + off
            if linear_start <= site < linear_end:
                relocs.append({"site": f"{seg:04X}:{off:04X}", "linear": f"{site:05X}",
                               "relative_offset": site - linear_start})
        spans.append({
            "id": key, "size": end - start,
            "original_exe_file_range": [start, end],
            "original_exe_file_range_hex": [f"0x{start:05X}", f"0x{end:05X}"],
            "section": "S27", "section_file_range": [start - section_lo, end - section_lo],
            "section_linear_range": [f"0x{linear_start:05X}", f"0x{linear_end:05X}"],
            "dgroup_frame": frame, "dgroup_offset": f"0x{offset:04X}" if offset is not None else None,
            "bytes_hex": data.hex(" "), "nonzero_bytes": sum(v != 0 for v in data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "provenance_class": prov["class"], "provenance_owner": prov["owner"],
            "relocations_inside": relocs, **REVIEW[key],
        })

    literal_total = sum(x["size"] for x in spans)
    # The progress residual includes three bytes that are the overlap of
    # debt:common_tail with the actual S27 section file extent, not another game span.
    tail_rows = []
    for item in provenance["ranges"]:
        lo, hi = item["file"]
        a, b = max(lo, section_lo), min(hi, section_hi)
        if a < b and item["class"] == "debt:common_tail":
            tail_rows.append({"file_range": [a, b], "bytes_hex": x.raw[a:b].hex(" "),
                              "class": item["class"], "owner": item["owner"],
                              "size": b - a})
    tail_size = sum(item["size"] for item in tail_rows)
    provenance_residual = literal_total + tail_size

    closed = {
        "id": "dgroup_2328", "status": "EXACT_DATA_OWNED", "size": 16,
        "dgroup_frame": "55B3", "dgroup_offset": "0x2328",
        "bytes_hex": "0f 0e 0c 04 0d 05 01 0b 0a 02 06 06 0f 07 08 00",
        **REVIEW["dgroup_2328"],
        "evidence": ["evidence/promotions.jsonl: S03:3253 record dated 2026-10-02",
                     "layout/manifest.json: current placement at DGROUP:2328",
                     "src/S03/m3253.asm: original second-XLAT reference"],
    }

    evidence_inputs = ["assets/SIMANT.EXE", "docs/progress.json", "build/link/provenance.json",
                       "work/data/s27_map.json", "layout/manifest.json", "layout/symbols.json",
                       "src/S00/m31AD.asm", "src/S01/m3126.asm", "src/S01/m32B5.asm",
                       "src/S03/m3253.asm", "src/root/m1B73.asm", "src/root/m1FBD.asm",
                       "evidence/promotions.jsonl",
                       "src/root/m277E.c"]
    return {
        "schema": "simant-behavior-data-debt-v1",
        "oracle_sha256": x.sha256,
        "section": {"index": 27, "load_segment": section.load_seg,
                    "load_segment_hex": f"{section.load_seg:04X}",
                    "data_file_offset": section.data_file_offset,
                    "data_size": len(section.data), "data_sha256": hashlib.sha256(section.data).hexdigest()},
        "source_pins": [json_ref(ROOT, f) for f in evidence_inputs],
        "progress": {"generated": progress["generated"],
                     "unresolved_data_bytes": progress["unresolved_data_bytes"],
                     "accepted_data_bytes": progress["data_bytes_accepted"],
                     "link_fill_data_bytes": progress["data_link_fill_bytes"],
                     "far_bss_bytes": progress["far_bss_zero_fill_bytes"]},
        "reconciliation": {"literal_debt_spans": len(spans), "literal_debt_bytes": literal_total,
                           "section27_common_tail_overlap_bytes": tail_size,
                           "provenance_residual": provenance_residual,
                           "progress_residual": progress["unresolved_data_bytes"],
                           "progress_matches_provenance": provenance_residual == progress["unresolved_data_bytes"],
                           "reconciliation_note": ("matches current progress" if provenance_residual == progress["unresolved_data_bytes"] else f"STALE PROGRESS: current provenance gives {provenance_residual} bytes, docs/progress.json reports {progress['unresolved_data_bytes']}"),
                           "rule": f"{provenance_residual} = {literal_total} bytes in {len(spans)} remaining far/DGROUP debt ranges + {tail_size} bytes of debt:common_tail overlapping S27 file extent; accepted LINK_FILL ({progress['data_link_fill_bytes']}) and FAR_BSS zero fill ({progress['far_bss_zero_fill_bytes']:,}) are already subtracted."},
        "literal_spans": spans,
        "closed_data_spans": [closed],
        "common_tail_overlap": tail_rows,
        "notes": [
            "The current executable's far paragraph bytes are linear 50F54-50F5F (12 zero bytes), inside S27 data file at 6E214-6E21F; do not confuse the linear address with physical file offset.",
            "The 2328-2337 bytes are meaningful table data: o03_3253_002F reads the high-nibble table at 2318, adds 10h to BX for the second XLAT, and restores BX. This 16-byte low-nibble table is now exactly owned by S03:3253 after strict promotion.",
            "Three common-tail overlap bytes are reported separately from game data. Their current provenance class is debt:common_tail; no semantic claim or harmless-padding claim is made.",
            "No unresolved zero bytes are classified as harmless solely because they are zero."
        ],
    }


def render_md(report: dict) -> str:
    lines = ["# Residual game-data byte audit", "",
             f"Oracle SHA-256: `{report['oracle_sha256']}`. Section 27 is `S27` at `{report['section']['load_segment_hex']}`, with {report['section']['data_size']:,} file bytes.", "",
             f"Current provenance gives **{report['reconciliation']['provenance_residual']} unresolved bytes**: **{report['reconciliation']['literal_debt_bytes']} bytes across {report['reconciliation']['literal_debt_spans']} remaining original data spans** plus **{report['reconciliation']['section27_common_tail_overlap_bytes']} bytes overlapping the section’s `debt:common_tail` end.** `docs/progress.json` reports {report['progress']['unresolved_data_bytes']} bytes. {report['reconciliation']['reconciliation_note']}. This is a provenance distinction, not a claim that the tail bytes are harmless or game-semantic.", "",
             "The 12-byte zero span at linear `50F54` is section-27 data-file range `6E214-6E220`; it ends at paragraph-aligned linear `50F60`. It remains tagged `debt:far_data`, so paragraph-fill origin still needs source/link-record proof.", "",
             "| Span | Original linear / DGROUP address | Size | Original bytes | Evidence-based reading | Ownership state |",
             "|---|---|---:|---|---|---|"]
    for s in report["literal_spans"]:
        addr = s["section_linear_range"][0]
        if s["dgroup_offset"]:
            addr += f" / 55B3:{s['dgroup_offset'][2:]}"
        lines.append(f"| `{s['id']}` | `{addr}` | {s['size']} | `{s['bytes_hex']}` | {s['purpose']} | {s['classification']} |")
    lines += ["", "## Per-span evidence and next work", ""]
    for s in report["literal_spans"]:
        lines += [f"### `{s['id']}`", "",
                  f"Original file range `{s['original_exe_file_range_hex'][0]}-{s['original_exe_file_range_hex'][1]}`; section-27 linear range `{s['section_linear_range'][0]}-{s['section_linear_range'][1]}`; SHA-256 `{s['sha256']}`.", "",
                  f"{s['ownership']} {s['next_step']}", "",
                  "Evidence: " + "; ".join(f"`{r}`" for r in s["references"]) + ".", ""]
    lines += ["## Separate three-byte tail overlap", "",
              "The 3 bytes at the file end are currently covered by provenance class `debt:common_tail`, not by one of the eight data spans. They are included in the residual arithmetic because the section-27 extent ends inside that common-tail range. The neighboring 253 bytes lie outside section 27. Their raw bytes and class are in `data-debt.json`; ownership is still unresolved at the linker/section-boundary level.", "",
              "## Evidence boundary", "",
              "This is an address, byte and reference inventory. It makes no behavioral equivalence claim. The 16-byte `2328` lookup table is now exactly owned by S03:3253 through strict promotion, recorded separately in `data-debt.json`. The `2100` masks and `2108` lookup are also meaningful, but their defining S00 object split is unresolved.", "",
              "All hashes and source pins are emitted in the JSON file.", ""]
    return "\n".join(lines)


def main() -> int:
    report = make_inventory()
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    OUT_MD.write_text(render_md(report), encoding="utf-8")
    print(json.dumps({"json": str(OUT_JSON), "markdown": str(OUT_MD),
                      "unresolved": report["reconciliation"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
