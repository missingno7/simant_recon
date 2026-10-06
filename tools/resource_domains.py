"""Exhaustively inspect the hash-pinned shipped resource domain (never a build provider).

Reuse the independently checked database/LZSS decoder from the audio proof. Emit
metadata only: resource bytes never become C, ASM, objects or an executable.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
DECODER = ROOT / "evidence/canonical/audio-track-owner/shipped_domain.py"


def decoder():
    spec = importlib.util.spec_from_file_location("shipped_database_decoder", DECODER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def offset_list(payload: bytes, start: int) -> tuple[list[int], int]:
    """Read a DOS serialized, zero-terminated array of 32-bit relative pointers."""
    if not 0 <= start < len(payload) or start % 4:
        raise ValueError("invalid pointer table start")
    values = []
    cursor = start
    while cursor + 4 <= len(payload):
        value = struct.unpack_from("<I", payload, cursor)[0]
        cursor += 4
        if value == 0:
            return values, cursor
        if value >= len(payload):
            raise ValueError("pointer target outside resource")
        values.append(value)
    raise ValueError("missing pointer-table sentinel")


def menu_domain(payload: bytes) -> dict:
    outer, stop = offset_list(payload, 0)
    if not outer:
        raise ValueError("menu has no title list")
    lists = []
    table_ranges = [(0, stop)]
    strings = []
    for start in outer:
        pointers, end = offset_list(payload, start)
        table_ranges.append((start, end))
        lengths = []
        second = []
        high = []
        for pointer in pointers:
            end = payload.find(b"\0", pointer)
            if end < 0:
                raise ValueError("unterminated menu string")
            strings.append((pointer, end + 1))
            text = payload[pointer:end]
            lengths.append(len(text))
            second.append(text[1] if len(text) > 1 else None)
            high.extend(sorted({x for x in text if x >= 128}))
        lists.append(dict(table_offset=start, string_offsets=pointers,
                          string_lengths=lengths, second_bytes=second,
                          high_bytes=sorted(set(high))))
    if len(lists) != len(lists[0]["string_offsets"]) + 1:
        raise ValueError("title and item-list counts disagree")
    # The shipped format tiles every byte with disjoint tables and strings.
    # This independently excludes pointers into tables or overlapping strings.
    cursor = 0
    for start, end in sorted(table_ranges + strings):
        if start != cursor:
            raise ValueError("overlap or gap in menu topology")
        cursor = end
    if cursor != len(payload):
        raise ValueError("unaccounted menu tail")
    return dict(title_count=len(lists[0]["string_offsets"]),
                item_counts=[len(x["string_offsets"]) for x in lists[1:]],
                lists=lists, completely_tiled=True)


def window_domain(payload: bytes) -> dict:
    if len(payload) < 44:
        raise ValueError("short window header")
    count = struct.unpack_from("<h", payload, 12)[0]
    cursor = 44 + 4 * count
    if count <= 0 or cursor > len(payload):
        raise ValueError("invalid window object count")
    objects = []
    for number in range(count):
        if cursor + 40 > len(payload):
            raise ValueError("short object header")
        size = struct.unpack_from("<h", payload, cursor + 34)[0]
        if size < 40 or cursor + size > len(payload):
            raise ValueError("invalid object extent")
        objects.append(dict(index=number, offset=cursor, size=size,
            group=payload[cursor + 32], type=payload[cursor + 33], flags=struct.unpack_from("<H", payload, cursor + 36)[0],
            normal_color=payload[cursor + 38], selected_color=payload[cursor + 39],
            modes=list(struct.unpack_from("<4h", payload, cursor + 24)),
            refs=list(struct.unpack_from("<4h", payload, cursor + 16))))
        cursor += size
    if cursor != len(payload):
        raise ValueError("window object extents do not tile payload")
    return dict(object_count=count, objects=objects)


PALETTE_CALL_NAMES = frozenset({"win_SetObjSelectedStateI", "win_SetObjSelectedState",
    "win_MakeObjSelected", "win_MakeObjUnselected", "win_SetGroupSelectedState",
    "win_MakeGroupSelected", "win_MakeGroupUnselected", "f_22BF_094F", "win_SetColorNum"})


MENU_CALL_NAMES = frozenset({"f_1B73_030F", "f_1B73_036E", "f_1B73_0AC3", "f_1B73_0B00",
    "f_1FD2_03EB", "f_1FD2_044F", "f_1FD2_0883", "f_1FD2_032F", "f_1FD2_0390", "o10_35F5_0000", "o10_35F5_00D7",
    "o10_35F5_01C3", "o10_35F5_0384", "f_1FD2_0059", "f_1FD2_0077", "f_1FD2_00D6",
    "f_1FD2_0135", "f_1FD2_0198", "f_1FD2_021B", "f_1FD2_0663", "f_1FD2_07CB",
    "o17_384C_0039", "o17_384C_0184", "SetMenuItemState", "f_19A9_000B"})


def direct_calls(names) -> list[dict]:
    """Complete parsed direct call set, with arguments; declarations are not calls."""
    import csrc
    rows = []
    for path in sorted((ROOT / "src").rglob("*.c")):
        if (ROOT / "src/state") in path.parents:
            continue
        text = path.read_text()
        if not any(name in text for name in names):
            continue
        # Parser errors deliberately propagate: a partial call census is not proof.
        for function in csrc.Source(text).functions():
            for node in csrc.walk(function.body):
                if isinstance(node, csrc.Call) and isinstance(node.f, csrc.Id) and node.f.name in names:
                    rows.append(dict(source=path.relative_to(ROOT).as_posix(), caller=function.name,
                        callee=node.f.name, arguments=[" ".join(token.text for token in
                            csrc.tokenize(text[arg.s:arg.e]) if token.kind not in ("ws", "nl", "cmt"))
                            for arg in node.args]))
    return rows


def palette_calls() -> list[dict]:
    return direct_calls(PALETTE_CALL_NAMES)


def menu_calls() -> list[dict]:
    return direct_calls(MENU_CALL_NAMES)


def collect() -> dict:
    module = decoder()
    locked = json.loads((ROOT / "layout/oracle.lock.json").read_text())
    records = {}
    assets = {}
    census = {}
    aggregate = 14695981039346656037
    total = compressed = 0
    for stem in ("HCEGANT", "SHARED", "SOUND"):
        for suffix in ("NDX", "DAT"):
            name = stem + "." + suffix
            raw = (ROOT / "assets" / name).read_bytes()
            identity = dict(size=len(raw), sha256=hashlib.sha256(raw).hexdigest())
            if identity != {key: locked["inputs"][name][key] for key in identity}:
                raise ValueError("resource identity differs from oracle lock: " + name)
            assets[name] = identity
        count, rows = module.parse_records(stem)
        records[stem] = rows
        kinds = {}
        for row in rows:
            kinds[str(row["kind"])] = kinds.get(str(row["kind"]), 0) + 1
            aggregate ^= (module.fnv64(row["payload"]) + ((row["id"] & 65535) << 32) + row["kind"]) & 0xffffffffffffffff
            aggregate = (aggregate * 1099511628211) & 0xffffffffffffffff
            total += 1
            compressed += int(row["compressed"])
        census[stem] = dict(records=count, kind_counts=kinds)
    if (total, compressed, aggregate) != module.EXPECTED_CORPUS:
        raise ValueError("independent decoded corpus control changed")
    menus = []
    windows = []
    controls = []
    high_text = []
    highlighted = []
    for stem, rows in records.items():
        for row in rows:
            payload = row["payload"]
            key = dict(database=stem, id=row["id"], kind=row["kind"],
                       payload_sha256=hashlib.sha256(payload).hexdigest())
            if row["kind"] == 6:
                menus.append({**key, **menu_domain(payload)})
            elif row["kind"] == 0:
                if 0 <= row["id"] < 128:
                    windows.append({**key, **window_domain(payload)})
                else:
                    controls.append({**key, "bytes": len(payload),
                                     "signed_words": list(struct.unpack("<" + "h" * (len(payload) // 2), payload))})
            elif row["kind"] == 10:
                # Record bytes before the first NUL, precisely the string input.
                text = payload.split(b"\0", 1)[0]
                high_text.append({**key, "text_bytes": len(text),
                                  "high_bytes": sorted({x for x in text if x >= 128}),
                                  "raw_high_bytes": sorted({x for x in payload if x >= 128})})
                paired = [r for r in rows if (r["id"], r["kind"]) == (row["id"], 21)]
                if paired:
                    if len(paired) != 1:
                        raise ValueError("duplicate style resource")
                    style = paired[0]["payload"]
                    n = struct.unpack_from(">H", style)[0]
                    if len(style) != 2 + 20 * n:
                        raise ValueError("style run extent mismatch")
                    runs = [struct.unpack_from(">I8H", style, 2 + 20 * i) for i in range(n)]
                    positions = [r[0] for r in runs]
                    if positions != sorted(positions) or any(p > len(payload) for p in positions):
                        raise ValueError("style positions outside ordered text domain")
                    for i, run in enumerate(runs):
                        if run[4] == 0x100:
                            end = runs[i + 1][0] if i + 1 < n else len(payload)
                            highlighted.append({**key, "start": run[0], "end": end,
                                "high_bytes": sorted({x for x in payload[run[0]:end] if x >= 128})})
    by_id = {(x["database"], x["id"]): x for x in controls}
    counts = by_id[("HCEGANT", 128)]["signed_words"][:3]
    nwin, ncolor, ngroup = counts
    palette = by_id[("HCEGANT", 129)]
    purge = by_id[("HCEGANT", 131)]
    purge_payload = next(r["payload"] for r in records["HCEGANT"]
                         if (r["id"], r["kind"]) == (131, 0))
    ids = sorted(x["id"] for x in windows if x["database"] == "HCEGANT")
    if nwin < 0 or ncolor < 0 or ids != list(range(nwin)):
        raise ValueError("window control count does not match complete resource set")
    if palette["bytes"] != ncolor * 6 or purge["bytes"] < nwin:
        raise ValueError("palette or purge extent insufficient for declared count")
    exceptional = []
    for window in windows:
        for obj in window["objects"]:
            if not (0 <= obj["normal_color"] < ncolor and 0 <= obj["selected_color"] < ncolor):
                exceptional.append(dict(database=window["database"], window=window["id"], **obj))
    # Pin all manually interpreted consumer contexts. This records dependencies;
    # it does not pretend a regex census is a complete indirect-call proof.
    sources = {}
    for name in ("src/S17/m384C.c", "src/S20/m39F1.c", "src/S10/m35F5.c", "src/S11/m35F5.c",
                 "src/root/m1FD2.c", "src/root/m20E8.c", "src/root/m21FA.c", "src/root/m22BF.c",
                 "src/root/m23AE.c", "src/root/m23E6.c", "src/root/m2505.c", "src/S23/m39C7.c"):
        sources[name] = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
    return dict(schema="simant-shipped-resource-domain-v1", assets=assets, sources=sources,
        census=census, corpus=dict(records=total, compressed=compressed, fnv1a64=f"{aggregate:016x}"),
        menus=menus, window_control=dict(windows=nwin, colors=ncolor, groups=ngroup,
            palette_bytes=palette["bytes"], purge_bytes=purge["bytes"], complete_window_ids=ids,
            preload_window_ids=[i for i in range(nwin) if purge_payload[i] == 0]),
        windows=windows, exceptional_palette_fields=exceptional, text_records=high_text,
        highlighted_style_intervals=highlighted,
        palette_direct_calls=palette_calls(),
        limitations=["Successful resource loads from this immutable shipped corpus only; no corrupt/replacement packages or allocation failure continuation.",
            "Counts establish operational minimum storage, not historical COMDEF capacity or allocator TU.",
            "A selected color 63 is present: resource enumeration alone cannot exclude its later activation.",
            "This is static corpus evidence, not an original-game execution trace or indirect-call reachability theorem."])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, help="fresh directory beneath build/")
    args = parser.parse_args()
    sys.path.insert(0, str(ROOT / "tools"))
    import modctx
    out = modctx.under_build(ROOT / args.out)
    report = collect()
    out.mkdir(parents=True, exist_ok=False)
    (out / "domains.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(dict(corpus=report["corpus"], menu_counts=[m["title_count"] for m in report["menus"]],
        windows=report["window_control"], exceptional_colors=len(report["exceptional_palette_fields"]),
        high_byte_text_records=sum(bool(x["high_bytes"]) for x in report["text_records"])), indent=2))


if __name__ == "__main__":
    main()
