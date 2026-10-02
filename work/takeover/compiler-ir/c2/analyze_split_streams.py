"""Test whether C2 PR/GS bytes follow split-pointer segment homes.

Run from the repository root with:
    python work/takeover/compiler-ir/c2/analyze_split_streams.py

Reads only saved /Fc summaries and ignored /B3 captures. It compares a
whitespace negative, two segment-home shifts, and the existing S15 base/extern
pair. Byte matches are reported as candidates; no PR/GS grammar is assumed.
"""
from __future__ import annotations

import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
CAPTURE_ROOT = ROOT / "build" / "workers" / "c2_observability" / "b3"
LISTINGS = json.loads((OUT / "split-far-listings.json").read_text(encoding="utf-8"))
S15 = json.loads((OUT / "s15-segment-context.json").read_text(encoding="utf-8"))
LABELS = {
    "split-far-base": "toy-split-far-base",
    "split-far-whitespace": "toy-split-far-whitespace",
    "split-far-extra-int": "toy-split-far-extra-int",
    "split-far-extra-long": "toy-split-far-extra-long",
}


def load_streams(case: str) -> dict:
    cap_label = LABELS[case]
    root = CAPTURE_ROOT / cap_label / "IR"
    return {name: (root / name).read_bytes() for name in ("000352PR", "000352GS")}


def find_all(data: bytes, needle: bytes) -> list[int]:
    out, start = [], 0
    while True:
        pos = data.find(needle, start)
        if pos < 0:
            return out
        out.append(pos)
        start = pos + 1


def contexts(data: bytes, positions: list[int], lo: int = 6, hi: int = 10) -> list[dict]:
    rows = []
    for pos in positions:
        left, right = max(0, pos - lo), min(len(data), pos + hi)
        rows.append({"offset": pos, "context_start": left, "context_hex": data[left:right].hex(" ")})
    return rows


def main() -> None:
    listing_by_case = {row["case"]: row for row in LISTINGS["normal_listings"]}
    raw = {case: load_streams(case) for case in LABELS}
    cases = {}
    relsets = {}
    gs_abssets = {}
    for case, files in raw.items():
        listing = listing_by_case[case]
        seg_home = listing["split_representation_check"]["segment_home_bp_offset"]
        seg_byte = struct.pack("<b", seg_home)
        local_slot = listing["slots"]["text"]
        ptr_byte = struct.pack("<b", local_slot)
        pr, gs = files["000352PR"], files["000352GS"]
        text_positions = find_all(pr, b"text")
        text_pos = text_positions[0] if text_positions else None
        segment_pr_positions = find_all(pr, seg_byte)
        segment_gs_positions = find_all(gs, seg_byte)
        pointer_field_pos = text_pos + 10 if text_pos is not None else None
        pointer_home_field_pos = text_pos + 9 if text_pos is not None else None
        pr_relative = [p - text_pos for p in segment_pr_positions
                       if text_pos is not None and text_pos - 16 <= p <= text_pos + 100]
        relsets[case] = set(pr_relative)
        gs_abssets[case] = set(segment_gs_positions)
        store_pattern = b"\x01\x02\x04" + seg_byte + b"\x05"
        load_pattern = b"\x01\x02\x01\x08\x04" + seg_byte + b"\x05"
        store_positions = find_all(pr, store_pattern)
        load_positions = find_all(pr, load_pattern)
        cases[case] = {
            "capture_label": LABELS[case],
            "source_sha256": listing["source_sha256"],
            "segment_home_bp_offset_from_listing": seg_home,
            "segment_home_candidate_byte_hex": seg_byte.hex(" "),
            "named_text_slot_start_from_listing": local_slot,
            "named_text_slot_candidate_byte_hex": ptr_byte.hex(" "),
            "pr_named_text_pointer_home_field_relative_offset": 9,
            "pr_named_text_pointer_home_field_hex": (
                pr[pointer_home_field_pos:pointer_home_field_pos + 2].hex(" ")
                if pointer_home_field_pos is not None else None
            ),
            "pr_named_text_pointer_home_low_byte_matches_listing": (
                pointer_home_field_pos is not None and pr[pointer_home_field_pos:pointer_home_field_pos + 1] == ptr_byte
            ),
            "pr_segment_store_operand_pattern_hex": store_pattern.hex(" "),
            "pr_segment_store_operand_pattern_offsets": store_positions,
            "pr_segment_reload_operand_pattern_hex": load_pattern.hex(" "),
            "pr_segment_reload_operand_pattern_offsets": load_positions,
            "pr_size": len(pr),
            "pr_sha256": __import__("hashlib").sha256(pr).hexdigest(),
            "pr_text_name_offsets": text_positions,
            "pr_text_record_relative_plus10_hex": (
                pr[pointer_field_pos:pointer_field_pos + 2].hex(" ")
                if pointer_field_pos is not None else None
            ),
            "pr_candidate_segment_byte_all_offsets": segment_pr_positions,
            "pr_candidate_segment_byte_offsets_near_text": pr_relative,
            "pr_candidate_segment_byte_contexts_near_text": contexts(
                pr, [text_pos + rel for rel in pr_relative], 5, 7
            ) if text_pos is not None else [],
            "gs_size": len(gs),
            "gs_sha256": __import__("hashlib").sha256(gs).hexdigest(),
            "gs_text_name_offsets": find_all(gs, b"text"),
            "gs_candidate_segment_byte_all_offsets": segment_gs_positions,
            "gs_candidate_segment_byte_contexts": contexts(gs, segment_gs_positions, 5, 7),
        }

    # A fixed PR byte relative to the named local is only a candidate record
    # field when it carries each home value and survives the whitespace control.
    common_pr_rel = set.intersection(*(relsets[c] for c in LABELS))
    common_gs_abs = set.intersection(*(gs_abssets[c] for c in LABELS))
    base_vs_whitespace = {
        stream: {
            "same_size": len(raw["split-far-base"][stream]) == len(raw["split-far-whitespace"][stream]),
            "byte_identical": raw["split-far-base"][stream] == raw["split-far-whitespace"][stream],
        }
        for stream in ("000352PR", "000352GS")
    }

    # S15: retain the named text record plus the candidate segment byte context.
    s15_context = {}
    for label, row in S15["listings"].items():
        cap_label = "s15-fleet-base" if label == "s15-fleet-base" else "s15-same-line-top-extern"
        cap_dir = CAPTURE_ROOT / cap_label
        pr = (cap_dir / "IR" / "000352PR").read_bytes()
        gs = (cap_dir / "IR" / "000352GS").read_bytes()
        text_positions = find_all(pr, b"text")
        text_pos = text_positions[0] if text_positions else None
        # The /Fc instruction sequence after f_171C_1B84 returns DX:AX is
        # retained as concrete segment-home evidence, without decoding PR/GS.
        instructions = row["all_proc_instructions"]
        call_i = next((i for i, line in enumerate(instructions) if "f_171C_1B84" in line), None)
        call_context = instructions[call_i:call_i + 8] if call_i is not None else []
        seg_home = None
        for line in call_context:
            if "mov\tWORD PTR [bp-" in line and line.endswith(",dx"):
                import re
                match = re.search(r"\[bp-([0-9a-f]+)\]", line, re.I)
                seg_home = -int(match.group(1), 16) if match else None
                break
        seg_byte = struct.pack("<b", seg_home) if seg_home is not None else None
        store_pattern = b"\x01\x02\x04" + seg_byte + b"\x05" if seg_byte else None
        load_pattern = b"\x01\x02\x01\x08\x04" + seg_byte + b"\x05" if seg_byte else None
        lo = max(0, text_pos - 16) if text_pos is not None else 0
        hi = min(len(pr), text_pos + 80) if text_pos is not None else 0
        name_home_pos = text_pos + 9 if text_pos is not None else None
        store_positions = find_all(pr, store_pattern) if store_pattern else []
        load_positions = find_all(pr, load_pattern) if load_pattern else []
        s15_context[label] = {
            "source_sha256_normalized": row["normalized_source_sha256"],
            "b3_capture_source_sha256": S15["existing_b3_captures"][cap_label]["capture_source_sha256"],
            "listing_text_local_slot": row["text_home"],
            "listing_registers": row["registers"],
            "listing_instructions_after_far_pointer_return": call_context,
            "listing_text_segment_store_home": seg_home,
            "segment_home_candidate_byte_hex": seg_byte.hex(" ") if seg_byte else None,
            "pr_size": len(pr),
            "pr_sha256": __import__("hashlib").sha256(pr).hexdigest(),
            "pr_text_name_offset": text_pos,
            "pr_text_record_window_start": lo,
            "pr_text_record_window_hex": pr[lo:hi].hex(" "),
            "pr_named_text_pointer_home_field_relative_offset": 9,
            "pr_named_text_pointer_home_field_hex": (
                pr[name_home_pos:name_home_pos + 2].hex(" ") if name_home_pos is not None else None
            ),
            "pr_named_text_pointer_home_low_byte_matches_listing": (
                name_home_pos is not None and pr[name_home_pos:name_home_pos + 1] == struct.pack("<b", row["text_home"])
            ),
            "pr_segment_store_operand_pattern_offsets": store_positions,
            "pr_segment_reload_operand_pattern_offsets": load_positions,
            "pr_segment_store_operand_patterns_near_text": [p for p in store_positions if text_pos is not None and text_pos <= p <= text_pos + 256],
            "pr_segment_reload_operand_patterns_near_text": [p for p in load_positions if text_pos is not None and text_pos <= p <= text_pos + 256],
            "pr_segment_store_operand_pattern_contexts": contexts(pr, store_positions, 6, 8),
            "pr_segment_reload_operand_pattern_contexts": contexts(pr, load_positions, 6, 8),
            "pr_target_bp6_store_pattern_hex": (b"\x01\x02\x04\xfa\x05").hex(" "),
            "pr_target_bp6_store_pattern_offsets": find_all(pr, b"\x01\x02\x04\xfa\x05"),
            "pr_target_bp6_store_pattern_offsets_near_text": [
                p for p in find_all(pr, b"\x01\x02\x04\xfa\x05")
                if text_pos is not None and text_pos <= p <= text_pos + 256
            ],
            "pr_target_bp6_reload_pattern_hex": (b"\x01\x02\x01\x08\x04\xfa\x05").hex(" "),
            "pr_target_bp6_reload_pattern_offsets": find_all(pr, b"\x01\x02\x01\x08\x04\xfa\x05"),
            "pr_segment_byte_occurrences": find_all(pr, seg_byte) if seg_byte else [],
            "pr_segment_byte_contexts_near_text": contexts(
                pr, [p for p in find_all(pr, seg_byte) if text_pos is not None and text_pos <= p <= text_pos + 256], 6, 8
            ) if seg_byte else [],
            "gs_size": len(gs),
            "gs_sha256": __import__("hashlib").sha256(gs).hexdigest(),
            "gs_text_name_offsets": find_all(gs, b"text"),
            "gs_segment_byte_occurrences": find_all(gs, seg_byte) if seg_byte else [],
        }

    # S15 pair is an unchanged-home diagnostic context, not a changed-home
    # positive: both source captures have equal local text records.
    s15_pair = {}
    for stream in ("000352PR", "000352GS"):
        a = (CAPTURE_ROOT / "s15-fleet-base" / "IR" / stream).read_bytes()
        b = (CAPTURE_ROOT / "s15-same-line-top-extern" / "IR" / stream).read_bytes()
        s15_pair[stream] = {
            "byte_differences": sum(x != y for x, y in zip(a, b)),
            "same_length": len(a) == len(b),
            "text_name_plus_home_field_equal": (
                s15_context["s15-fleet-base"]["pr_named_text_pointer_home_field_hex"]
                == s15_context["s15-same-line-top-extern"]["pr_named_text_pointer_home_field_hex"]
            ) if stream == "000352PR" else None,
            "actual_segment_store_pattern_offsets_equal": (
                s15_context["s15-fleet-base"]["pr_segment_store_operand_pattern_offsets"]
                == s15_context["s15-same-line-top-extern"]["pr_segment_store_operand_pattern_offsets"]
            ) if stream == "000352PR" else None,
            "target_bp6_store_pattern_offsets_near_text_equal": (
                s15_context["s15-fleet-base"]["pr_target_bp6_store_pattern_offsets_near_text"]
                == s15_context["s15-same-line-top-extern"]["pr_target_bp6_store_pattern_offsets_near_text"]
            ) if stream == "000352PR" else None,
        }

    output = {
        "method": "search expected signed8 segment-home bytes in pre-C3 PR/GS; compare record-relative positions and unchanged whitespace control; no record semantics assumed",
        "tiny_controls": cases,
        "negative_control_streams_base_vs_whitespace": base_vs_whitespace,
        "same_pr_relative_offsets_carrying_each_segment_home_byte": sorted(common_pr_rel),
        "same_gs_absolute_offsets_carrying_each_segment_home_byte": sorted(common_gs_abs),
        "s15_context": s15_context,
        "s15_base_vs_extern_context": s15_pair,
        "conclusion": "The tiny C3 listings show the offset remains in SI across barrier while DX is stored to and reloaded from a segment-word BP home (-2/-4/-6). The named `text` slot bases are -4/-6/-8 respectively, so the segment home is exactly the named pointer base+2; these controls do not prove an anonymous/CSE temporary. In C2 PR, two stable operand-like motifs carry the corresponding signed8 displacement: `01 02 04 FE|FC|FA 05` and `01 02 01 08 04 FE|FC|FA 05`; base and whitespace PR/GS are byte-identical. S15's candidate listing likewise stores returned DX at BP-2, with named whole-pointer slot base BP-4. Its PR has named-slot bytes FC 06 and a nearby `01 02 04 FE 05` motif; the same-line-top-extern capture preserves both. No matching FA store motif occurs near S15 text, and the exact tiny reload motif is absent there. This demonstrates the current candidate's segment-word reference displacement in pre-C3 PR, but does not decode PR semantics or show which earlier pass selected the home. GS literal scans do not rule out indirect references. Without original target C2/debug identity, target BP-6 cannot be identified as a whole-pointer base or segment half; the missing fact is where/how the historical split component receives and coalesces its home across C2→C3.",
    }
    path = OUT / "split-far-stream-analysis.json"
    path.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(path.relative_to(ROOT).as_posix())
    print(f"base/whitespace PR+GS identical: {base_vs_whitespace}")
    print(f"common PR relative home-byte positions: {sorted(common_pr_rel)}")
    print(f"common GS absolute home-byte positions: {sorted(common_gs_abs)}")
    print(f"S15: {json.dumps(s15_pair)}")


if __name__ == "__main__":
    main()
