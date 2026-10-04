"""Read-only extraction of the checked-in HCEGANT window 0 and offsets records.

This script reports only record/index metadata and decoded geometry fields. It
does not copy or emit resource payload bytes.
"""
from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def records(stem: str):
    idx = (ROOT / "assets" / f"{stem}.NDX").read_bytes()
    dat = (ROOT / "assets" / f"{stem}.DAT").read_bytes()
    count = struct.unpack_from("<H", idx, 0)[0]
    if len(idx) < 20 + count * 8:
        raise ValueError(f"{stem}: index shorter than OpenIndex count")
    rows = []
    for i in range(count):
        off, object_id, kind, flags = struct.unpack_from("<IHBB", idx, 20 + i * 8)
        rows.append((off, object_id, kind, flags))
    return idx, dat, rows


def resource(stem: str, object_id: int, kind: int):
    idx, dat, rows = records(stem)
    found = [r for r in rows if r[1:3] == (object_id, kind)]
    if len(found) != 1:
        raise ValueError(f"{stem} ({object_id:#x},{kind}) count={len(found)}")
    off, _, _, flags = found[0]
    header = struct.unpack_from("<HHHHH", dat, off + 14)
    size = header[3]
    payload = dat[off + 24 : off + 24 + size]
    if len(payload) != size:
        raise ValueError("truncated resource payload")
    return idx, dat, off, flags, header, payload


def rect4(payload: bytes, at: int):
    return struct.unpack_from("<4h", payload, at)


def object_fields(payload: bytes, number: int):
    at = struct.unpack_from("<H", payload, 0x2C + number * 4)[0]
    return {
        "offset": at,
        "rect": rect4(payload, at),
        "origin": rect4(payload, at + 8),
        "references": struct.unpack_from("<4h", payload, at + 16),
        "modes": struct.unpack_from("<4h", payload, at + 24),
        "type": payload[at + 0x21],
        "flags24": struct.unpack_from("<H", payload, at + 0x24)[0],
    }


idx, dat, win_off, win_flags, win_header, win = resource("HCEGANT", 0, 0)
_, _, layout_off, layout_flags, layout_header, layout = resource("HCEGANT", 0, 9)
obj0 = object_fields(win, 0)
obj1 = object_fields(win, 1)
obj3 = object_fields(win, 3)
obj4 = object_fields(win, 4)
win_count = struct.unpack_from("<H", win, 0x0C)[0]
window_flags = struct.unpack_from("<H", win, 0x1C)[0]
layout0 = rect4(layout, 0)

# Source-derived equations: win_LoadWindow copies layout0 into obj0+8 when
# layout0.left != 0x8000. win_Recalc applies obj0's {left=origin.x,
# top=origin.y, right=left+origin.width, bottom=top+origin.height}; obj3's
# right and bottom are constrained to its own left+width and root.bottom-3;
# obj4 is constrained to obj3.left+48, obj3.top, root.right-2, root.bottom-17.
root_rect = (
    layout0[0],
    layout0[1],
    layout0[0] + layout0[2],
    layout0[1] + layout0[3],
)
object3_rect = (root_rect[0] + 2, root_rect[1] + 19, root_rect[0] + 50, root_rect[3] - 3)
object4_rect = (object3_rect[0] + 48, object3_rect[1], root_rect[2] - 2, root_rect[3] - 17)
viewport_width = object4_rect[2] - object4_rect[0]
viewport_height = object4_rect[3] - object4_rect[1]

result = {
    "schema": "viewport-resource-observation-v30",
    "inputs": {
        "HCEGANT.NDX": {"size": len(idx), "sha256": hashlib.sha256(idx).hexdigest()},
        "HCEGANT.DAT": {"size": len(dat), "sha256": hashlib.sha256(dat).hexdigest()},
    },
    "index": {
        "header_count": struct.unpack_from("<H", idx, 0)[0],
        "source_offset": 20,
        "row_size": 8,
        "window0_kind0": {"record_offset": win_off, "flags": win_flags, "header": win_header, "payload_size": len(win)},
        "window0_kind9": {"record_offset": layout_off, "flags": layout_flags, "header": layout_header, "payload_size": len(layout)},
    },
    "window0_kind0": {
        "window_object_count": win_count,
        "window_flags": window_flags,
        "has_resize_flag_0x0008": bool(window_flags & 0x0008),
        "has_screen_clamp_flag_0x1000": bool(window_flags & 0x1000),
        "objects": {"0": obj0, "1": obj1, "3": obj3, "4": obj4},
    },
    "window0_kind9": {"first_win_offsets_rect": layout0},
    "source_recalc_observation": {
        "root_rect_after_kind9_override": root_rect,
        "object3_rect_after_recalc": object3_rect,
        "object4_rect_after_recalc": object4_rect,
        "object4_pixels": {"width": viewport_width, "height": viewport_height},
        "tile_counts_at_16px": {"width": viewport_width // 16, "height": viewport_height // 16 + 1},
        "tile_counts_at_12px": {"width": viewport_width // 12, "height": viewport_height // 12 + 1},
    },
}
print(json.dumps(result, indent=2))
