"""Retained independent NDX parser and query partition test logic."""
from pathlib import Path
import struct

def le16(b: bytes, o: int) -> int:
    return struct.unpack_from("<h", b, o)[0]


def leu16(b: bytes, o: int) -> int:
    return struct.unpack_from("<H", b, o)[0]


def parse_index(path: Path) -> tuple[int, list[bytes], list[tuple[int, int, int, int]]]:
    raw = path.read_bytes()
    if len(raw) < 20:
        raise ValueError(f"{path.name}: truncated NDX header")
    count = leu16(raw, 0)
    if len(raw) != 20 + (count + 32) * 8:
        raise ValueError(f"{path.name}: NDX extent/count mismatch")
    rows = [raw[20 + 8 * i:28 + 8 * i] for i in range(count + 1)]
    decoded = []
    for i, row in enumerate(rows):
        off = struct.unpack_from("<I", row, 0)[0]
        ident = le16(row, 4)
        kind, flags = row[6], row[7]
        decoded.append((off, ident, kind, flags))
        if i < count and i and (decoded[i - 1][2], decoded[i - 1][1]) > (kind, ident):
            raise ValueError(f"{path.name}: active entries not sorted at {i}")
    return count, rows, decoded


def queries(count: int, decoded: list[tuple[int, int, int, int]]) -> list[tuple[int, int]]:
    keys = [(ident, kind) for _, ident, kind, _ in decoded[:count]]
    result: set[tuple[int, int]] = set(keys)
    for ident, kind in keys:
        if ident > -32768:
            result.add((ident - 1, kind))
        if ident < 32767:
            result.add((ident + 1, kind))
    kinds = sorted({kind for _, kind in keys})
    for kind in kinds:
        result.update({(-32768, kind), (-1, kind), (0, kind), (32767, kind)})
    result.update({(-32768, -1), (-1, -1), (0, -1), (32767, -1),
                   (-32768, 256), (-1, 256), (0, 256), (32767, 256)})
    # Expose the reserved row and the precise active_count one-past read.
    _, look_id, look_kind, _ = decoded[count]
    result.add((look_id, look_kind))
    last_id, last_kind = keys[-1]
    if last_id < 32767:
        result.add((last_id + 1, last_kind))
    elif last_kind < 255:
        result.add((-32768, last_kind + 1))
    return sorted(result)


def lower_bound(rows: list[tuple[int, int, int, int]], count: int,
                ident: int, kind: int) -> int:
    lo, hi = 0, count
    while lo < hi:
        mid = lo + (hi - lo) // 2
        row_kind, row_id = rows[mid][2], rows[mid][1]
        if row_kind < kind or (row_kind == kind and row_id < ident):
            lo = mid + 1
        else:
            hi = mid
    return lo


