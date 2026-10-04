from __future__ import annotations

import hashlib
import json
import random
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "build" / "workers" / "dos_menu_resource_bound_v34"


def pin(path: str) -> dict[str, object]:
    b = (ROOT / path).read_bytes()
    return {"path": path, "bytes": len(b), "sha256": hashlib.sha256(b).hexdigest()}


def decode_lzss(stream: bytes, expected: int, tail: bytes) -> dict[str, object]:
    if len(tail) != 18:
        raise ValueError("ring tail control must have exactly 18 bytes")
    # LZSS_DATA is 4113 zero-initialized bytes; f_1B05_0008 fills only
    # RingBuf[0:0xFEE] with spaces. The ring index is masked to 0xFFF,
    # so only tail[0:18] (ring indexes 0xFEE..0xFFF) can affect decoding.
    ring = bytearray(4096)
    ring[:0xFEE] = b" " * 0xFEE
    ring[0xFEE:0x1000] = tail
    ring_pos = 0xFEE
    written = bytearray(4096)
    first_write: dict[int, int] = {}
    prewrite_tail_reads: list[dict[str, int]] = []
    tail_read_count = 0
    out = bytearray()
    i = 0
    while len(out) < expected:
        if i >= len(stream):
            raise ValueError("truncated LZSS flag byte")
        flags = stream[i]
        i += 1
        for bit in range(8):
            if len(out) >= expected:
                break
            if flags & (1 << bit):
                if i >= len(stream):
                    raise ValueError("truncated LZSS literal")
                value = stream[i]
                i += 1
                out.append(value)
                if not written[ring_pos]:
                    first_write[ring_pos] = len(out) - 1
                written[ring_pos] = 1
                ring[ring_pos] = value
                ring_pos = (ring_pos + 1) & 0xFFF
            else:
                if i + 1 >= len(stream):
                    raise ValueError("truncated LZSS match")
                lo, hi = stream[i], stream[i + 1]
                i += 2
                match_pos = lo | ((hi & 0xF0) << 4)
                match_len = (hi & 0x0F) + 3
                for j in range(match_len):
                    if len(out) >= expected:
                        break
                    read_pos = (match_pos + j) & 0xFFF
                    if read_pos >= 0xFEE and not written[read_pos]:
                        tail_read_count += 1
                        prewrite_tail_reads.append({
                            "ring_index": read_pos,
                            "output_index": len(out),
                        })
                    value = ring[read_pos]
                    out.append(value)
                    if not written[ring_pos]:
                        first_write[ring_pos] = len(out) - 1
                    written[ring_pos] = 1
                    ring[ring_pos] = value
                    ring_pos = (ring_pos + 1) & 0xFFF
    return {
        "expanded": bytes(out),
        "compressed_bytes_consumed": i,
        "initial_tail_reads_before_local_write": prewrite_tail_reads,
        "initial_tail_read_count_before_local_write": tail_read_count,
        "tail_first_write_output_indexes": [first_write.get(p) for p in range(0xFEE, 0x1000)],
        "tail_written_before_end": all(written[p] for p in range(0xFEE, 0x1000)),
    }


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
            raise ValueError("resource pointer outside expanded payload")
        values.append(offset)
    raise ValueError("resource pointer table missing null sentinel")


def menu_shape(data: bytes) -> dict[str, object]:
    titles_offset, titles_segment = relptr(data, 0)
    if titles_segment != 0:
        raise ValueError("unexpected title-table segment")
    titles = pointer_table(data, titles_offset)
    for text_offset in titles:
        if data.find(b"\0", text_offset) < 0:
            raise ValueError("unterminated title string")
    item_counts: list[int] = []
    for slot in range(1, 17):
        offset, segment = relptr(data, slot * 4)
        if offset == 0 and segment == 0:
            break
        if segment != 0:
            raise ValueError("unexpected item-table segment")
        item_counts.append(len(pointer_table(data, offset)))
    return {
        "expanded_bytes": len(data),
        "titles_table_offset": titles_offset,
        "nonnull_title_count": len(titles),
        "title_null_sentinel_present": True,
        "active_item_table_counts": item_counts,
        "expanded_sha256": hashlib.sha256(data).hexdigest(),
        "resource_bytes_embedded": False,
        "strings_embedded": False,
    }


ndx_path = ROOT / "assets" / "SHARED.NDX"
dat_path = ROOT / "assets" / "SHARED.DAT"
ndx = ndx_path.read_bytes()
dat = dat_path.read_bytes()
count = struct.unpack_from("<H", ndx, 0)[0]
if 20 + count * 8 > len(ndx):
    raise ValueError("SHARED index is truncated")
rows = []
for ordinal in range(count):
    offset, object_id, kind, flags = struct.unpack_from("<IhBB", ndx, 20 + 8 * ordinal)
    if (object_id, kind) == (0, 6):
        rows.append({"ordinal_zero_based": ordinal, "offset": offset, "flags": flags})
if len(rows) != 1:
    raise ValueError("expected one SHARED MENU object 0 entry")
row = rows[0]
record_length = struct.unpack_from("<h", dat, row["offset"] + 20)[0]
if record_length < 2:
    raise ValueError("invalid DBRecordHeader.size")
record_end = row["offset"] + 24 + record_length
if record_end > len(dat):
    raise ValueError("DBRecall payload extent exceeds SHARED.DAT")

# This follows DBRecall exactly for this entry: bit 0 means packed; bit 2
# (the special already-expanded path) is clear. DBRecordHeader.size includes
# the two-byte expanded-size prefix, so DBRecall passes size-2 stream bytes.
if not (row["flags"] & 1) or (row["flags"] & 4):
    raise ValueError("SHARED object 0 does not use the expected DBRecall branch")
expanded_size = struct.unpack_from("<H", dat, row["offset"] + 24)[0]
stream = dat[row["offset"] + 26:record_end]
if len(stream) != record_length - 2:
    raise ValueError("DBRecall compressed stream length mismatch")

rng = random.Random(0x50F646D0)
random_tail = bytes(rng.randrange(256) for _ in range(18))
variants = {
    "fresh_static_zero_tail": bytes(18),
    "all_spaces_control": b" " * 18,
    "deterministic_random_tail_control": random_tail,
}
results: dict[str, object] = {}
for name, tail in variants.items():
    decoded = decode_lzss(stream, expanded_size, tail)
    shape = menu_shape(decoded["expanded"])
    results[name] = {
        "input_tail_sha256": hashlib.sha256(tail).hexdigest(),
        "compressed_bytes_consumed": decoded["compressed_bytes_consumed"],
        "initial_tail_read_count_before_local_write": decoded["initial_tail_read_count_before_local_write"],
        "initial_tail_reads_before_local_write": decoded["initial_tail_reads_before_local_write"],
        "tail_first_write_output_indexes": decoded["tail_first_write_output_indexes"],
        "tail_written_before_end": decoded["tail_written_before_end"],
        "menu_shape": shape,
    }

hashes = {x["menu_shape"]["expanded_sha256"] for x in results.values()}
counts = {x["menu_shape"]["nonnull_title_count"] for x in results.values()}
item_counts = {tuple(x["menu_shape"]["active_item_table_counts"]) for x in results.values()}
v34 = pin("build/workers/dos_menu_resource_bound_v34/review-v34.json")
v34_markdown = pin("build/workers/dos_menu_resource_bound_v34/review-v34.md")
v34_generator = pin("build/workers/dos_menu_resource_bound_v34/make_review_v34.py")
review = {
    "schema": "simant-dos-menu-decoder-control-addendum-v34a",
    "status": "APPEND_ONLY_DECODER_CONTROL",
    "frozen_v34_receipt_preserved": True,
    "scope": "Recheck only the SHARED MENU object 0 decode and ring-tail dependency; no production files changed.",
    "dbrecall_input": {
        "ndx_path": "assets/SHARED.NDX",
        "ndx_sha256": hashlib.sha256(ndx).hexdigest(),
        "dat_path": "assets/SHARED.DAT",
        "dat_sha256": hashlib.sha256(dat).hexdigest(),
        "index_entry_count": count,
        "object_id": 0,
        "kind": 6,
        "index_ordinal_zero_based": row["ordinal_zero_based"],
        "entry_offset": row["offset"],
        "entry_flags": row["flags"],
        "packed_flag_bit_0_set": bool(row["flags"] & 1),
        "special_unpacked_flag_bit_2_set": bool(row["flags"] & 4),
        "db_record_header_offset": row["offset"] + 14,
        "db_record_header_size_field_offset": row["offset"] + 20,
        "db_record_header_size": record_length,
        "expanded_size_prefix": expanded_size,
        "compressed_stream_offset": row["offset"] + 26,
        "compressed_stream_length_passed_to_decoder": record_length - 2,
        "decoded_input_bytes_consumed": [x["compressed_bytes_consumed"] for x in results.values()],
        "branch": "DBRecall flags&1 true, flags&4 false: read expanded-size word, then feed size-2 compressed bytes to LZSS",
    },
    "ring_model_from_src_root_m1B05_asm": {
        "static_far_data_allocation_bytes": 4113,
        "ring_access_domain_bytes": 4096,
        "every_call_explicitly_fills": 4078,
        "fill_value": 32,
        "retained_tail_ring_indexes": [4078, 4095],
        "fresh_static_initializer_tail_value": 0,
        "tail_reset_by_decoder_init": False,
        "tail_tracking": "A tail read is counted only if that ring slot has not yet been written by this decode call; write indexes are recorded by expanded-output position.",
    },
    "variants": results,
    "independence_result": {
        "all_three_expanded_sha256_equal": len(hashes) == 1,
        "all_three_title_counts_equal": len(counts) == 1,
        "all_three_item_table_counts_equal": len(item_counts) == 1,
        "no_initial_tail_slot_read_before_local_write_in_any_variant": all(x["initial_tail_read_count_before_local_write"] == 0 for x in results.values()),
        "observed_menu_result_independent_of_retained_tail": len(hashes) == 1 and all(x["initial_tail_read_count_before_local_write"] == 0 for x in results.values()),
        "menu_title_count": next(iter(counts)) if len(counts) == 1 else None,
        "item_table_counts": list(next(iter(item_counts))) if len(item_counts) == 1 else None,
        "expanded_sha256": next(iter(hashes)) if len(hashes) == 1 else None,
        "v34_expanded_sha256_matches": next(iter(hashes)) == "4b8b92a60651c809455189afff58c547eb34593f427aa35e1c8a855f51f732e4" if len(hashes) == 1 else False,
    },
    "pins": {
        "sources": [
            pin("src/root/m1B05.asm"),
            pin("src/root/m19A9.c"),
            pin("src/root/m1986.c"),
            pin("evidence/behavior/functions/FindIndex/module.c"),
            pin("work/source-only-dos/static-completeness/FindIndex.json"),
            pin("work/source-only-dos/static-completeness/index-v1.json"),
            pin("layout/oracle.lock.json"),
        ],
        "frozen_v34_review": v34,
        "frozen_v34_markdown": v34_markdown,
        "frozen_v34_generator": v34_generator,
        "decoder_control_script": pin("build/workers/dos_menu_resource_bound_v34/make_decoder_control_v34a.py"),
    },
    "original_bytes_embedded": False,
}
if not review["independence_result"]["observed_menu_result_independent_of_retained_tail"]:
    raise SystemExit("decoder tail dependence detected; review remains inconclusive")

(OUT / "decoder-control-v34a.json").write_text(json.dumps(review, indent=2) + "\n", encoding="utf-8")
lines = [
    "# Decoder control addendum v34a",
    "",
    "**Append-only follow-up.** The previously reported v34 review and JSON remain untouched. This addendum corrects the ring initialization model and checks whether it affects the SHARED MENU object 0 result.",
    "",
    "`DBRecall` finds SHARED kind-6 object 0 with entry flags `0x01`: the packed bit is set and the special bit `0x04` is clear. Its record header gives `size=455`. Following the actual branch, the decoder reads a two-byte expanded-size prefix (`514`) and receives `size-2 = 453` compressed bytes. The stream consumes all 453 bytes.",
    "",
    "`src/root/m1B05.asm` allocates a zero-initialized 4,113-byte ring region, but each decoder initialization fills only indexes 0 through 4,077 with spaces. The 4 KiB masked ring indexes 4,078 through 4,095 retain their prior contents until this decode writes them. The control ran the same pinned stream with a fresh zero tail, an all-space tail, and a deterministic random tail. It tracked every read of those 18 slots before the current decode's first write.",
    "",
    "All variants consumed the same input, made no pre-write reads from the retained tail, and produced the same 514-byte expanded payload hash, five-title sentinel count, and item-table counts 8, 7, 8, 6, 6. The expanded hash matches the v34 review. The observed menu result is independent of the previous contents of the final 18 ring slots.",
    "",
    "The JSON pins the source files, strict-effective FindIndex review, v34 receipt, and DAT/NDX hashes. It stores hashes and structural counts only; no executable or asset bytes or decoded strings are retained.",
]
(OUT / "decoder-control-v34a.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"tail read counts: {[x['initial_tail_read_count_before_local_write'] for x in results.values()]}")
print(f"expanded hashes: {[x['menu_shape']['expanded_sha256'] for x in results.values()]}")
print(f"menu title counts: {sorted(counts)}; item table counts: {sorted(item_counts)}")
