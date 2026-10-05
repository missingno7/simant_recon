"""Read-only parser for the pinned DOS database corpus and SOUND song streams.

Resource-domain evidence only.  This file is intentionally self-contained rather than
importing the portable resource fixture helpers, so its parser can be compared
against their independently recorded corpus identity.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import struct

ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'src/program.json').is_file())
ASSETS = ROOT / "assets"
EXPECTED_CORPUS = (840, 205, 0x2CD5F2C76EE8A96E)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fnv64(data: bytes) -> int:
    value = 14695981039346656037
    for byte in data:
        value = ((value ^ byte) * 1099511628211) & 0xFFFFFFFFFFFFFFFF
    return value


def lzss(data: bytes, wanted: int) -> bytes:
    if wanted < 0:
        raise ValueError("negative LZSS output size")
    ring = bytearray(b" " * 4096)
    write = 4096 - 18
    cursor = 0
    flags = 0
    result = bytearray()
    while len(result) < wanted:
        flags >>= 1
        if not flags & 0x100:
            if cursor >= len(data):
                raise ValueError("truncated LZSS flag")
            flags = data[cursor] | 0xFF00
            cursor += 1
        if flags & 1:
            if cursor >= len(data):
                raise ValueError("truncated LZSS literal")
            value = data[cursor]
            cursor += 1
            result.append(value)
            ring[write] = value
            write = (write + 1) & 4095
        else:
            if cursor + 2 > len(data):
                raise ValueError("truncated LZSS back-reference")
            low, high = data[cursor], data[cursor + 1]
            cursor += 2
            read = low | ((high & 0xF0) << 4)
            length = (high & 0x0F) + 3
            for _ in range(length):
                if len(result) == wanted:
                    break
                value = ring[read]
                read = (read + 1) & 4095
                result.append(value)
                ring[write] = value
                write = (write + 1) & 4095
    return bytes(result)


def parse_ndx(raw: bytes, label: str) -> list[tuple[int, int, int, int]]:
    if len(raw) < 20:
        raise ValueError(f"{label}: short NDX header")
    count = struct.unpack_from("<H", raw, 0)[0]
    if len(raw) != 20 + (count + 32) * 8:
        raise ValueError(f"{label}: NDX size/count mismatch")
    rows = []
    for i in range(count + 32):
        pos = 20 + i * 8
        off = struct.unpack_from("<I", raw, pos)[0]
        ident = struct.unpack_from("<h", raw, pos + 4)[0]
        kind, flags = raw[pos + 6], raw[pos + 7]
        rows.append((off, ident, kind, flags))
        if i < count and i and (rows[i - 1][2], rows[i - 1][1]) > (kind, ident):
            raise ValueError(f"{label}: active key order decreases at row {i}")
    return rows


def parse_records(stem: str) -> tuple[int, list[dict]]:
    ndx = (ASSETS / f"{stem}.NDX").read_bytes()
    dat = (ASSETS / f"{stem}.DAT").read_bytes()
    rows = parse_ndx(ndx, stem)
    count = struct.unpack_from("<H", ndx, 0)[0]
    records = []
    for rowno, (relative, ident, kind, flags) in enumerate(rows[:count]):
        header = 14 + relative
        if header + 10 > len(dat):
            raise ValueError(f"{stem}[{rowno}]: record header outside DAT")
        stored_size = struct.unpack_from("<H", dat, header + 6)[0]
        start = header + 10
        stop = start + stored_size
        if stop > len(dat):
            raise ValueError(f"{stem}[{rowno}]: record payload outside DAT")
        stored = dat[start:stop]
        compressed = bool(stored_size and flags & 1 and not flags & 4)
        if not stored_size or not flags & 1:
            payload = stored
        elif flags & 4:
            payload = b"\xff\xff" + stored
        else:
            if len(stored) < 2:
                raise ValueError(f"{stem}[{rowno}]: missing decoded-size prefix")
            wanted = struct.unpack_from("<H", stored, 0)[0]
            payload = lzss(stored[2:], wanted)
        records.append({"row": rowno, "id": ident, "kind": kind, "flags": flags,
                        "offset": relative, "stored_size": stored_size,
                        "payload": payload, "compressed": compressed})
    return count, records


def vlq(buf: bytes, pos: int, end: int) -> tuple[int, int]:
    value = 0
    for _ in range(4):
        if pos >= end:
            raise ValueError("truncated variable-length quantity")
        byte = buf[pos]
        pos += 1
        value = (value << 7) | (byte & 0x7F)
        if not byte & 0x80:
            return value, pos
    raise ValueError("variable-length quantity exceeds four bytes")


def parse_track(track: bytes) -> dict:
    pos = 0
    running = None
    event_count = 0
    meta_count = 0
    ended = False
    while pos < len(track):
        _, pos = vlq(track, pos, len(track))  # delta time
        if pos >= len(track):
            raise ValueError("delta without following MIDI event")
        first = track[pos]
        if first & 0x80:
            status = first
            pos += 1
        elif running is not None:
            status = running
        else:
            raise ValueError("data byte without running status")

        if 0x80 <= status <= 0xEF:
            running = status
            ndata = 1 if (status & 0xF0) in (0xC0, 0xD0) else 2
            if pos + ndata > len(track):
                raise ValueError("truncated channel event")
            if any(byte & 0x80 for byte in track[pos:pos + ndata]):
                raise ValueError("status byte appears in channel data")
            pos += ndata
        elif status in (0xF0, 0xF7):
            running = None
            size, pos = vlq(track, pos, len(track))
            if pos + size > len(track):
                raise ValueError("truncated system-exclusive event")
            pos += size
        elif status == 0xFF:
            running = None
            if pos >= len(track):
                raise ValueError("truncated meta-event type")
            meta_type = track[pos]
            pos += 1
            size, pos = vlq(track, pos, len(track))
            if pos + size > len(track):
                raise ValueError("truncated meta-event payload")
            if meta_type == 0x2F:
                if size != 0 or pos + size != len(track):
                    raise ValueError("end-of-track is malformed or not final")
                ended = True
            pos += size
            meta_count += 1
        elif status in (0xF1, 0xF3):
            running = None
            if pos + 1 > len(track) or track[pos] & 0x80:
                raise ValueError("truncated system-common event")
            pos += 1
        elif status == 0xF2:
            running = None
            if pos + 2 > len(track) or any(x & 0x80 for x in track[pos:pos + 2]):
                raise ValueError("truncated system-common event")
            pos += 2
        elif status == 0xF6 or 0xF8 <= status <= 0xFE:
            if status < 0xF8:
                running = None
        else:
            raise ValueError(f"unsupported MIDI status 0x{status:02x}")
        event_count += 1
        if ended and pos != len(track):
            raise ValueError("bytes follow final end-of-track")
    if not ended:
        raise ValueError("missing end-of-track")
    return {"events": event_count, "meta_events": meta_count}


def parse_smf(raw: bytes) -> dict:
    if len(raw) < 14 or raw[:4] != b"MThd":
        raise ValueError("missing/truncated MThd header")
    hsize = struct.unpack_from(">I", raw, 4)[0]
    if hsize != 6:
        raise ValueError("unexpected SMF header length")
    fmt, declared, division = struct.unpack_from(">HHH", raw, 8)
    if fmt not in (0, 1, 2) or declared == 0:
        raise ValueError("invalid SMF format or zero track count")
    pos = 14
    tracks = []
    while pos < len(raw):
        if pos + 8 > len(raw):
            raise ValueError("truncated track chunk header")
        if raw[pos:pos + 4] != b"MTrk":
            raise ValueError("unexpected SMF chunk type")
        size = struct.unpack_from(">I", raw, pos + 4)[0]
        pos += 8
        end = pos + size
        if end > len(raw):
            raise ValueError("track chunk exceeds SMF payload")
        tracks.append(parse_track(raw[pos:end]))
        pos = end
    if pos != len(raw) or len(tracks) != declared:
        raise ValueError(f"declared track count {declared}, actual {len(tracks)}")
    if fmt == 0 and declared != 1:
        raise ValueError("format-0 SMF must declare one track")
    return {"format": fmt, "header_track_count": declared,
            "parsed_chunk_count": len(tracks), "division": division,
            "tracks": tracks}


def song_call_sites(song_ids: set[int]) -> tuple[list[dict], list[dict]]:
    rows = []
    source_hashes = {}
    dynamic_domains = {
        "SRand1(5) + 0x4e27": list(range(0x4E27, 0x4E2C)),
        "SRand2() + 0x2713": [0x2713, 0x2714],
        "fd_50F6_0228 + 0x2713": [0x2713, 0x2714, 0x2715],
        "song": [0x4E23, 0x4E24],
    }
    for path in sorted((ROOT / "src").rglob("*.c")):
        source = path.read_text(encoding="utf-8")
        rel = path.relative_to(ROOT).as_posix()
        for match in re.finditer(r"\b(myBeginSong|f_00DF_00B1)\s*\(\s*([^,\n]+)", source):
            line_start = source.rfind("\n", 0, match.start()) + 1
            line_end = source.find("\n", match.start())
            line_text = source[line_start:line_end if line_end >= 0 else len(source)]
            if re.search(r"\bextern\b|\bvoid\s+far\s+(?:myBeginSong|f_00DF_00B1)", line_text):
                continue
            expr = " ".join(match.group(2).strip().split())
            try:
                ids = [int(expr, 0)]
                evidence = "literal call argument"
            except ValueError:
                if expr not in dynamic_domains:
                    raise ValueError(f"unclassified song call argument {rel}: {expr}")
                ids = dynamic_domains[expr]
                evidence = {
                    "SRand1(5) + 0x4e27": "src/root/m0093.c:SRand1 returns the unsigned division remainder, 0..range-1",
                    "SRand2() + 0x2713": "src/root/m0093.c:SRand2 masks the generated word with 1",
                    "fd_50F6_0228 + 0x2713": "src/S08/m35F5.c:RandYard resets state to 0; src/root/m0BE8.c:TryAntTheme increments and wraps values >2 to 0",
                    "song": "src/S16/m384C.c:DrawSimPayoff initializes 0x4e23 and increments only while <0x4e25",
                }[expr]
            missing = [value for value in ids if value not in song_ids]
            if missing:
                raise AssertionError(f"song callsite reaches absent SOUND kind-18 ids: {rel}: {missing}")
            source_hashes[rel] = sha(path)
            rows.append({"source": rel, "line": source[:match.start()].count("\n") + 1,
                         "function": match.group(1), "argument": expr,
                         "resolved_song_ids": ids, "resolution_basis": evidence})
    if not rows:
        raise AssertionError("no source song callsites found")
    return rows, source_hashes


def must_reject(label: str, action) -> str:
    try:
        action()
    except (ValueError, struct.error) as exc:
        return f"rejected: {exc}"
    raise AssertionError(f"negative control unexpectedly accepted: {label}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True, help='Fresh output directory beneath build/')
    args = parser.parse_args()
    import sys
    sys.path.insert(0, str(ROOT / 'tools'))
    import modctx
    output = Path(args.out)
    OUT = modctx.under_build(output if output.is_absolute() else ROOT / output)
    OUT.mkdir(parents=True, exist_ok=False)
    corpus_records = 0
    compressed_records = 0
    aggregate = 14695981039346656037
    census = {}
    records_by_stem = {}
    for stem in ("HCEGANT", "SHARED", "SOUND"):
        count, records = parse_records(stem)
        records_by_stem[stem] = records
        kinds: dict[str, int] = {}
        signature_ids = []
        for rec in records:
            kinds[str(rec["kind"])] = kinds.get(str(rec["kind"]), 0) + 1
            if rec["payload"].startswith(b"MThd"):
                signature_ids.append({"id": rec["id"], "kind": rec["kind"]})
            if rec["kind"] in (18, 20) and stem != "SOUND":
                raise AssertionError(f"unexpected shipped song kind in {stem}: {rec['id']}/{rec['kind']}")
            aggregate ^= (fnv64(rec["payload"]) + ((rec["id"] & 0xFFFF) << 32) + rec["kind"]) & 0xFFFFFFFFFFFFFFFF
            aggregate = (aggregate * 1099511628211) & 0xFFFFFFFFFFFFFFFF
            corpus_records += 1
            compressed_records += int(rec["compressed"])
        census[stem] = {"ndx_count": count, "kind_counts": kinds,
                        "MThd_records": signature_ids}

    if (corpus_records, compressed_records, aggregate) != EXPECTED_CORPUS:
        raise AssertionError(f"corpus control mismatch: {corpus_records}, {compressed_records}, {aggregate:016x}")

    sound = records_by_stem["SOUND"]
    by_key = {(r["id"], r["kind"]): r for r in sound}
    song_meta = [r for r in sound if r["kind"] == 18]
    smfs = [r for r in sound if r["kind"] == 20]
    if len(song_meta) != 33 or len(smfs) != 30:
        raise AssertionError(f"unexpected SOUND kind-18/kind-20 census: {len(song_meta)}/{len(smfs)}")
    refs = []
    max_tracks = 0
    for meta in song_meta:
        if len(meta["payload"]) < 2:
            raise ValueError(f"short song metadata record {meta['id']}")
        stream_id = struct.unpack_from(">H", meta["payload"], 0)[0]
        target = by_key.get((stream_id, 20))
        if target is None:
            raise ValueError(f"metadata {meta['id']} points to absent SOUND kind-20 id {stream_id}")
        refs.append({"song_resource_id": meta["id"], "smf_record_id": stream_id})
    parsed_smfs = []
    for smf in smfs:
        parsed = parse_smf(smf["payload"])
        max_tracks = max(max_tracks, parsed["header_track_count"])
        parsed_smfs.append({"id": smf["id"], "length": len(smf["payload"]), **parsed})
    if {r["id"] for r in smfs} != {r["smf_record_id"] for r in refs}:
        raise AssertionError("kind-20 streams and kind-18 metadata references are not a closed set")
    calls, caller_source_hashes = song_call_sites({r["id"] for r in song_meta})

    # Independent malformed controls: table count/extent mismatch, altered
    # declared SMF count, truncated track data. A 19-track valid synthetic
    # stream is a positive contrast proving the parser does not impose 18/10.
    sound_ndx = (ASSETS / "SOUND.NDX").read_bytes()
    first_smf_payload = by_key[(smfs[0]["id"], 20)]["payload"]
    changed_count = first_smf_payload[:10] + b"\x00\x01" + first_smf_payload[12:]
    negative = {
        "NDX_count_extent_mismatch": must_reject(
            "NDX count extent", lambda: parse_ndx(struct.pack("<H", 121) + sound_ndx[2:], "negative-SOUND")),
        "SMF_declared_vs_chunk_count": must_reject(
            "SMF declared-count mismatch", lambda: parse_smf(changed_count)),
        "truncated_SMF_track": must_reject(
            "truncated track", lambda: parse_smf(by_key[(smfs[0]["id"], 20)]["payload"][:-1])),
    }
    # The first test must fail specifically because declared tracks and actual
    # chunks disagree; only 1 byte is altered in the header.
    synthetic = bytearray(b"MThd\x00\x00\x00\x06\x00\x01\x00\x13\x00\x60")
    for _ in range(19):
        synthetic.extend(b"MTrk\x00\x00\x00\x04\x00\xff\x2f\x00")
    synthetic_19 = parse_smf(bytes(synthetic))
    if synthetic_19["header_track_count"] != 19 or synthetic_19["parsed_chunk_count"] != 19:
        raise AssertionError("valid 19-track generic SMF control did not parse")

    pins = {}
    for name in ("SOUND.NDX", "SOUND.DAT", "HCEGANT.NDX", "HCEGANT.DAT", "SHARED.NDX", "SHARED.DAT"):
        path = ASSETS / name
        pins[name] = {"sha256": sha(path), "size": path.stat().st_size}
    oracle = json.loads((ROOT / "layout/oracle.lock.json").read_text(encoding="utf-8"))
    for name, pin in pins.items():
        locked = oracle["inputs"][name]
        if pin["sha256"] != locked["sha256"] or pin["size"] != locked["size"]:
            raise AssertionError(f"asset no longer matches layout/oracle.lock.json: {name}")
    source_pins = {}
    for name in sorted(set(caller_source_hashes) | {
            "src/root/m284A.c", "src/root/m0000.c", "src/root/m00DF.c",
            "src/root/m1A53.c", "src/root/m1959.asm", "src/root/m0093.c",
            "src/S20/m39F1.c", "src/root/m277E.c", "src/root/m293A.c",
            "src/root/m15F8.c", "src/root/m0BE8.c", "src/S08/m35F5.c",
            "src/S16/m384C.c"}):
        path = ROOT / name
        source_pins[name] = {"sha256": sha(path), "size": path.stat().st_size}
    result = {
        "evidence_kind": "independent parser run; pinned shipped asset corpus",
        "assets": pins,
        "assets_match_oracle_lock": True,
        "parser_sha256": sha(Path(__file__).resolve()),
        "source_inputs": source_pins,
        "resource_census": census,
        "independent_corpus_crosscheck": {
            "records": corpus_records, "lzss_records": compressed_records,
            "fnv1a64": f"{aggregate:016x}", "matches_existing_fixture_control": True},
        "song_metadata_reference_count": len(refs),
        "song_metadata_references": refs,
        "source_song_callsite_count": len(calls),
        "source_song_callsites": calls,
        "SMF_count": len(parsed_smfs),
        "SMF_track_counts": [{"id": r["id"], "track_count": r["header_track_count"],
                              "parsed_chunk_count": r["parsed_chunk_count"], "format": r["format"],
                              "division": r["division"], "bytes": r["length"]} for r in parsed_smfs],
        "resource_domain_max_header_tracks": max_tracks,
        "counterexamples_and_controls": {
            "negative": negative,
            "generic_parser_positive_outside_shipped_domain": synthetic_19,
            "interpretation": "10 is the maximum only in this complete hash-pinned shipped SOUND corpus; generic SMF syntax admits 19 and is not clamped by this parser."},
    }
    (OUT / "resource-validation.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"corpus_records": corpus_records, "compressed_records": compressed_records,
                      "fnv1a64": f"{aggregate:016x}", "songs": len(parsed_smfs),
                      "metadata": len(refs), "max_tracks": max_tracks,
                      "counts": [(r["id"], r["header_track_count"]) for r in parsed_smfs],
                      "negative_controls": negative, "positive_19": synthetic_19["header_track_count"]}, indent=2))


if __name__ == "__main__":
    main()
