"""Original-DOS differential contracts for FindIndex and small sound helpers.

This suite executes the hash-pinned DOS EXE and a separately compiled whole-module
candidate in the shared Unicorn runner. It records observable pointers/globals and
actual OUT instructions. It does not assign a proof category.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import shutil
import struct
import sys
import time
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'layout/functions.json').is_file())

import behavior
import behavior_ledger

SUITE = "small_contracts_v1"
FIND_DB = "fd_50F6_3958"
FIND_LOW = "fd_50F6_3956"
FIND_PTR = "fd_50F6_3952"
DB_RECORD_BYTES = 124
DB_COUNT_OFF = 0x54
DB_INDEX_OFF = 0x50
ARRAY_SEG = 0xA000
ARRAY_OFF = 0x1000


def _range(name, size):
    return behavior.Range(name, behavior.symbol_address(name), size)


def _word(v):
    return struct.pack("<H", v & 0xFFFF)


def _far(off, seg):
    return struct.pack("<HH", off & 0xFFFF, seg & 0xFFFF)


def _s16(value):
    value &= 0xFFFF
    return value - 0x10000 if value & 0x8000 else value




def _record(entry):
    # IndexEntry: far data pointer, int id, byte kind, byte spare.
    if len(entry) == 3:
        data_ptr, ident, kind = entry
        spare = 0
    else:
        data_ptr, ident, kind, spare = entry
    return _far(data_ptr, 0xA000) + struct.pack("<HBB", ident & 0xFFFF, kind & 255, spare & 255)


def find_case(label, entries, query_id, query_kind, db=0, sentinel=None):
    """Entries follow unsigned byte kind, then signed 16-bit id ordering."""
    if list(entries) != sorted(entries, key=lambda e: (e[2] & 255, _s16(e[1]))):
        raise ValueError("FindIndex fixture must be sorted by unsigned kind and signed id")
    b = behavior
    rec = b.symbol_address(FIND_DB) + db * DB_RECORD_BYTES
    low, ptr = b.symbol_address(FIND_LOW), b.symbol_address(FIND_PTR)
    arr = ARRAY_SEG * 16 + ARRAY_OFF
    if sentinel is None:
        sentinel = (0, 0x1357, 0xD6, 0)
    slots = list(entries) + [sentinel]
    data = b"".join(_record(e) for e in slots)
    writes = [
        (rec + DB_INDEX_OFF, _far(ARRAY_OFF, ARRAY_SEG)),
        (rec + DB_COUNT_OFF, _word(len(entries))),
        (arr, data),
        (low, _word(0xBEEF)),
        (ptr, _far(0x4321, 0x9876)),
    ]
    return b.Case(
        label=label,
        args=[db, query_id, query_kind],
        writes=writes,
        observe=[_range(FIND_LOW, 2), _range(FIND_PTR, 4),
                 b.Range(f"db{db}_index_and_count", rec + DB_INDEX_OFF, 8)],
        return_kind="farptr",
        metadata={"suite": SUITE, "contract": "FindIndex return pointer, low cursor, and one-past sentinel read/result are observed without normalizing pointer behavior", "oracle_helpers": "none", "ordering": "original +0x79 JG compares zero-extended unsigned-byte entry.kind to signed int argument; +0x97 JL compares signed int entry.id to signed int argument", "domain_class": "diagnostic-out-of-contract" if not 0 <= query_kind <= 255 else "valid-query-domain", "lookahead_fixture": {"sentinel": list(sentinel), "sentinel_record_is_initialized": True}},
    )


def _lower_bound(entries, ident, kind):
    wanted = (kind & 0xFFFF, ident & 0xFFFF)
    lo, hi = 0, len(entries)
    while lo < hi:
        mid = (lo + hi) // 2
        e = entries[mid]
        if (e[2], e[1]) < wanted:
            lo = mid + 1
        else:
            hi = mid
    return lo


def find_cases(random_count=30000, seed=0xF1D1):
    """Exhaustive small tables, cardinality/duplicate/signed boundaries, then random cases."""
    # Exhaust every exact-key, gap, boundary and empty-table query for all
    # subsets of a compact ordered key space.
    keyspace = [(ident, kind) for kind in range(2) for ident in range(4)]
    cases = []
    cases.append(find_case("empty/negative", [], 0, 0))
    for mask in range(1 << len(keyspace)):
        # Enumerate every subset of this eight-key domain and query every key,
        # all adjacent gaps, and values beyond both ends.
        entries = [(0x1000 + i, ident, kind)
                   for i, (ident, kind) in enumerate(keyspace) if mask & (1 << i)]
        # Each possible key in the compact domain, plus just-outside and values
        # on both sides of each sorted key.
        queries = {(ident, kind) for ident, kind in keyspace}
        queries.update({(-1, 0), (4, 1), (0, -1), (0, 2), (0xFFFF, 0xFFFF)})
        for ident, kind in sorted(queries):
            cases.append(find_case(f"exhaustive/m{mask:04x}/id{ident}/k{kind}", entries, ident, kind))
    # Search topology depends on table cardinality. Cover every insertion rank
    # and exact hit at each listed size, including both sides of 64 and
    # progressively larger binary-search trees through 256 records.
    cardinalities = (1, 2, 3, 7, 8, 15, 16, 31, 32, 63, 64, 65, 127, 128, 255, 256)
    for count in cardinalities:
        entries = [(0x2000 + i, i * 2, 3) for i in range(count)]
        probes = {(ident, 3) for ident in range(-1, count * 2 + 1)}
        probes.update({(-1, 3), (count * 2 + 1, 3), (0, 2), (0, 4)})
        for ident, kind in sorted(probes):
            cases.append(find_case(f"cardinality/{count}/id{ident}/k{kind}", entries, ident, kind))
    # Duplicate keys are legal in a sorted index. Verify the lower-bound result
    # selects the first duplicate and that both signed id and unsigned kind
    # promotion boundaries match the original comparisons.
    duplicate_rows = [(0x3100 + i, ident, 0x80) for i, ident in enumerate((0x8000, 0xFFFF, 0, 0x7FFF))]
    duplicate_rows += [(0x3200 + i, 0xFFFF, 0x80) for i in range(1, 4)]
    duplicate_rows.sort(key=lambda e: (e[2], _s16(e[1])))
    for ident in (0x8000, 0x8001, 0xFFFF, 0, 1, 0x7FFF):
        cases.append(find_case(f"signed-id/duplicate/id{ident:04x}", duplicate_rows, ident, 0x80))
    signed_kind_rows = [(0x4000 + i, ident, kind)
                        for i, (kind, ident) in enumerate(
                            (kind, ident) for kind in (0, 127, 128, 255)
                            for ident in (0x8000, 0xFFFF, 0, 0x7FFF))]
    signed_kind_rows.sort(key=lambda e: (e[2], _s16(e[1])))
    for kind in (0xFFFF, 0, 1, 127, 128, 255, 256, 0x7FFF, 0x8000):
        for ident in (0x8000, 0xFFFF, 0, 0x7FFF):
            cases.append(find_case(f"signed-kind/k{kind:04x}/id{ident:04x}", signed_kind_rows, ident, kind))
    # FindIndex reads index[low] after the binary search when low==count. Keep
    # that record initialized and deliberately vary whether its signed id and
    # unsigned kind match the query. The returned pointer is compared verbatim.
    # Empty tables take the early-return path, so matching sentinel records
    # prove whether that read is skipped.
    for count in (0, 1, 2, 63, 256):
        entries = [(0x5000 + i, -32768 + i, 0) for i in range(count)]
        for match_sentinel in (False, True):
            for variant, (data_ptr, spare) in enumerate(((0x1111, 0x00), (0xA55A, 0xFF))):
                query_id, query_kind = 32767, 255
                sentinel = (data_ptr, query_id if match_sentinel else -32768,
                            query_kind if match_sentinel else 0, spare)
                cases.append(find_case(
                    f"lookahead/count{count}/match{int(match_sentinel)}/v{variant}",
                    entries, query_id, query_kind, sentinel=sentinel))
    # Larger binary-search trees include signed IDs throughout the full range
    # and every unsigned kind byte.  The maximum includes one initialized
    # one-past record and exactly fits the remaining A000 segment bytes.
    large_rng = random.Random(seed ^ 0x6A17)
    max_count = (0x10000 - ARRAY_OFF) // 8 - 1
    large_cardinalities = (511, 512, 1023, 1024, 4095, max_count)
    for count in large_cardinalities:
        encoded = sorted(large_rng.sample(range(1 << 24), count))
        entries = [(0x6000 + i, (key & 0xFFFF) - 0x8000, key >> 16)
                   for i, key in enumerate(encoded)]
        positions = sorted({0, 1, count // 4, count // 2, (3 * count) // 4, count - 2, count - 1})
        for rank, pos in enumerate(positions):
            ident, kind = entries[pos][1:]
            cases.append(find_case(f"large/{count}/hit/{rank}", entries, ident, kind,
                                   sentinel=(0x7000 + rank, 0x1234, 0xFE, rank)))
            # Insertion probes on either side of the sampled signed ID retain
            # the full byte kind while exercising exact lower-bound partitions.
            for delta in (-1, 1):
                adjacent = max(-32768, min(32767, _s16(ident) + delta))
                cases.append(find_case(f"large/{count}/neighbor/{rank}/{delta}", entries,
                                       adjacent, kind, sentinel=(0x7100 + rank, -2, 0xFD, rank)))
        for probe in range(7):
            query_key = large_rng.randrange(1 << 24)
            query_kind = query_key >> 16
            query_id = (query_key & 0xFFFF) - 0x8000
            cases.append(find_case(f"large/{count}/random/{probe}", entries, query_id, query_kind,
                                   sentinel=(0x7200 + probe, query_id, query_kind, probe)))
    rng = random.Random(seed)
    for i in range(random_count):
        count = rng.randrange(0, 65)
        # The key encoding spans all byte kinds and the full signed 16-bit ID
        # domain while preserving the original unsigned-kind/signed-ID order.
        keys = sorted(rng.sample(range(1 << 24), count))
        entries = [(rng.randrange(1 << 16), (key & 0xFFFF) - 0x8000, key >> 16)
                   for key in keys]
        # Independent random queries include hits, adjacent misses, and extremes.
        if entries and rng.randrange(2):
            ident, kind = rng.choice(entries)[1:]
            if rng.randrange(3) == 0:
                ident = max(-32768, min(32767, _s16(ident) + rng.choice([-1, 1])))
        else:
            ident, kind = rng.randrange(-32768, 32768), rng.randrange(256)
        cases.append(find_case(f"random/{seed:08x}/{i}", entries, ident, kind, db=i % 4))
    return cases


def midi_case(label, off, byte0, byte1):
    b = behavior
    seg_global = b.symbol_address("g_8DFC")
    # _based(g_8DFC) uses this word as a segment base.
    base = 0xA000 * 16
    return b.Case(
        label=label, args=[off & 0xFFFF],
        writes=[(seg_global, _word(0xA000)),
                (base + (off & 0xFFFF), bytes([byte0 & 255])),
                (base + (((off + 1) & 0xFFFF)), bytes([byte1 & 255]))],
        observe=[], return_kind="s16",
        metadata={"suite": SUITE, "contract": "return the big-endian MIDI word at the song segment offset", "oracle_helpers": "none", "offset_representation": "16-bit based pointer offset"},
    )


def midi_cases(random_count=10000, seed=0x0138):
    cases = []
    # Exercise every byte value in both high and low return lanes, plus byte
    # order edge patterns at segment-wrap offsets. Random runs cover combinations.
    for value in range(256):
        off = (value * 251 + 0xFF00) & 0xFFFF
        cases.append(midi_case(f"high-lane/{value:02x}", off, value, 0xA5))
        cases.append(midi_case(f"low-lane/{value:02x}", off, 0x5A, value))
    for off in (0, 1, 0xFFFD, 0xFFFE, 0xFFFF):
        for a, z in ((0, 0), (0xFF, 0xFF), (0x12, 0x34), (0x80, 0x01), (0x01, 0x80)):
            cases.append(midi_case(f"boundary/{off:04x}/{a:02x}{z:02x}", off, a, z))
    # At offset FFFF, distinguish 16-bit based-pointer wrap to A000:0000 from
    # linear carry to B000:0000 by placing a different decoy byte there.
    wrap = midi_case("wrap-proof/ffff", 0xFFFF, 0x12, 0x34)
    wrap.writes.append((0xB0000, b"\x56"))
    wrap.metadata["wrap_probe"] = "A000:FFFF + 1 must read A000:0000; B000:0000 contains decoy 0x56"
    cases.append(wrap)
    rng = random.Random(seed)
    for i in range(random_count):
        off = rng.choice([0, 1, 0xFFFD, 0xFFFE, 0xFFFF, rng.randrange(65536)])
        cases.append(midi_case(f"random/{seed:08x}/{i}", off, rng.randrange(256), rng.randrange(256)))
    return cases


def tandy_case(label, ignored, note, vol, chan):
    b = behavior
    valid_domain = 0 <= note <= 127 and 0 <= chan <= 2 and 0 <= vol <= 255
    return behavior.Case(
        label=label, args=[ignored & 0xFFFF, note & 0xFFFF, vol & 0xFFFF, chan & 0xFFFF],
        observe=[], callbacks={"f_29F0_002A": b.Callback(stack_words=2)},
        return_kind="void", io_reads={},
        metadata={"suite": SUITE, "contract": "ordered actual OUT port/width/value sequence from original f_29F0_002A helper plus each helper-call argument/state snapshot", "helper_policy": "callback observes entry and falls through to execute original helper and actual OUT; no modeled writes", "expected_writes": 3, "domain_class": "valid-caller-domain" if valid_domain else "diagnostic-out-of-contract", "caller_domain": {"raw_note": "0..127 MIDI data byte before header transpose", "velocity_argument": "caller scales an unsigned MIDI byte; full byte sweep is included", "channel": "0..2 from f_277E_034F type-3 channel initialization"}},
    )


def tandy_cases(random_count=20000, seed=0x29D6):
    cases = []
    # Caller audit: m295C routes the 7-bit MIDI note and velocity to the
    # selected voice; m277E_034F creates precisely three type-3 voices with
    # channel nums 0,1,2. Sweep all byte-sized velocity values for every note
    # and real Tandy channel (128*256*3 = 98,304 finite-domain cases).
    volumes = range(256)
    channels = range(3)
    for note in range(128):
        for vol in volumes:
            for chan in channels:
                ignored = (note * 257 + vol * 17 + chan) & 0xFFFF
                cases.append(tandy_case(f"grid/n{note}/v{vol}/c{chan}", ignored, note, vol, chan))
    # The song player adds a signed 16-bit header transpose to the 7-bit note
    # before dispatch. Probe octave-edge offsets around that normal MIDI range.
    for note in (-12, -1, 128, 139):
        for vol in (0, 1, 127, 128, 255):
            for chan in channels:
                cases.append(tandy_case(f"diagnostic-transpose-edge/n{note}/v{vol}/c{chan}", 0, note, vol, chan))
    rng = random.Random(seed)
    for i in range(random_count):
        # Include signed/overflow-sensitive but memory-safe notes only in the
        # raw caller note domain; channels are actual type-3 channels. Wider
        # volume inputs probe promotions and are tagged diagnostic-only.
        cases.append(tandy_case(f"random/{seed:08x}/{i}", rng.randrange(65536),
                                rng.randrange(128), rng.randrange(65536), rng.randrange(3)))
    return cases










