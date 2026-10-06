"""Supported sample free-list extent and shipped-song controls."""
from __future__ import annotations

import hashlib
import json
import re
import struct
import sys
import types
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents
            if (p / "src/program.json").is_file())
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "portable/tests/native_database"))
sys.dont_write_bytecode = True
import behavior as b
import canonical
import csrc
import exe
import functions
from index_fixture_logic import parse_index


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def significant_function(path: str, name: str) -> str:
    text = (ROOT / path).read_text(encoding="latin1")
    fn = csrc.Source(text).function(name)
    return " ".join(t.text for t in csrc.tokenize(text[fn.head_s:fn.body.e])
                    if t.kind not in {"ws", "nl", "cmt"})


def inventory():
    program = canonical.load()
    texts = {}
    for module in program["modules"]:
        raw = (ROOT / module["source"]).read_bytes()
        assert sha(raw) == module["source_sha256"]
        texts[module["source"]] = raw.decode("latin1")
    return texts, program


TARGETS = {
    "fd_50F6_0150", "g_181C", "g_7574", "f_0000_00DE", "f_0000_0149",
    "f_0000_039B", "f_0000_0429", "f_0000_046F", "f_284A_067F",
    "f_290D_0193", "f_290D_026C", "f_295C_0015", "f_295C_00C9",
    "f_277E_04E8",
}


def source_census(texts: dict[str, str]) -> list[list[object]]:
    rows = []
    for path, text in sorted(texts.items()):
        if path.endswith(".asm"):
            for line_no, line in enumerate(text.splitlines(), 1):
                code = line.split(";", 1)[0]
                for token in re.findall(r"[A-Za-z_@][A-Za-z_0-9]*", code):
                    if token.lstrip("_@") in TARGETS:
                        rows.append([path, line_no, token, code.strip()])
        else:
            for token in csrc.tokenize(text):
                if token.kind == "id" and token.text in TARGETS:
                    rows.append([path, text.count("\n", 0, token.s) + 1, token.text])
    return rows


class Boundary(Exception):
    pass


def machine(name: str):
    image = exe.load()
    return b.Machine(types.SimpleNamespace(function=functions.get(name),
        vectors={exe.MANAGER_SEG * 16 + v.offset: v for v in image.vectors}))


LIST = 0x50F60 + 0x0150
G_181C = 0x55B30 + 0x181C
G_7574 = 0x55B30 + 0x7574


def original_store_case(count: int, punt_returns: bool) -> dict:
    m = machine("f_0000_0149")
    punt_calls = []

    def punt(_cpu, _args):
        punt_calls.append("Punt")
        if not punt_returns:
            raise Boundary()

    case = b.Case(
        f"free-list-{count}-{'return' if punt_returns else 'stop'}",
        args=[0x1234, 0x5678], return_kind="void",
        callbacks={"Punt": b.Callback(4, punt)},
        writes=[
            (G_181C, b.words(count)),
            (G_7574, b.words(1)),
            (LIST, bytes(160)),
        ],
    )
    stopped = False
    try:
        m.run(case)
    except b.ExecutionError as exc:
        if not isinstance(exc.__cause__, Boundary):
            raise
        stopped = True
    slot = m.read(LIST + count * 4, 4)
    expected_store = count <= 38 or punt_returns
    assert (slot == b.words(0x1234, 0x5678)) == expected_store
    assert m.word(G_181C) == count + expected_store
    assert punt_calls == (["Punt"] if count > 38 else [])
    assert stopped == (count > 38 and not punt_returns)
    return {
        "incoming_count": count,
        "punt_returns": punt_returns,
        "Punt_calls": len(punt_calls),
        "store_completed": expected_store,
        "stored_index": count if expected_store else None,
        "count_after": count + expected_store,
    }


def vlq(raw: bytes, pos: int) -> tuple[int, int]:
    value = 0
    while True:
        byte = raw[pos]
        pos += 1
        value = (value << 7) | (byte & 0x7f)
        if not byte & 0x80:
            return value, pos


def sound_records() -> dict[tuple[int, int], bytes]:
    count, _, rows = parse_index(ROOT / "assets/SOUND.NDX")
    data = (ROOT / "assets/SOUND.DAT").read_bytes()
    result = {}
    for offset, ident, kind, _flags in rows[:count]:
        header = 14 + offset
        size = struct.unpack_from("<H", data, header + 6)[0]
        result[(ident, kind)] = data[header + 10:header + 10 + size]
    return result


def midi_tracks(midi: bytes) -> list[list[tuple[int, int, bytes]]]:
    assert midi[:4] == b"MThd" and struct.unpack_from(">I", midi, 4)[0] == 6
    count = struct.unpack_from(">H", midi, 10)[0]
    pos, result = 14, []
    for _ in range(count):
        assert midi[pos:pos + 4] == b"MTrk"
        length = struct.unpack_from(">I", midi, pos + 4)[0]
        raw = midi[pos + 8:pos + 8 + length]
        pos += 8 + length
        events, cursor, tick, running = [], 0, 0, None
        while cursor < len(raw):
            delta, cursor = vlq(raw, cursor)
            tick += delta
            status = raw[cursor]
            if status & 0x80:
                cursor += 1
                if status < 0xf0:
                    running = status
            else:
                assert running is not None
                status = running
            if status == 0xff:
                meta = raw[cursor]
                cursor += 1
                size, cursor = vlq(raw, cursor)
                payload = bytes([meta]) + raw[cursor:cursor + size]
                cursor += size
            elif status in (0xf0, 0xf7):
                size, cursor = vlq(raw, cursor)
                payload = raw[cursor:cursor + size]
                cursor += size
            else:
                size = 1 if status & 0xf0 in (0xc0, 0xd0) else 2
                payload = raw[cursor:cursor + size]
                cursor += size
            events.append((tick, status, payload))
        result.append(events)
    assert pos == len(midi)
    return result


def scheduled(tracks):
    cursors = [0] * len(tracks)
    while True:
        active = [(events[cursors[i]][0], i) for i, events in enumerate(tracks)
                  if cursors[i] < len(events)]
        if not active:
            return
        _, index = min(active)
        event = tracks[index][cursors[index]]
        cursors[index] += 1
        yield event


INITIAL_BANK = [0, 25, 53, 3, 54, 35, 46, 50, 51, 48, 0, 12, 43, 52]
MODE6_DAC = {1, 2, 4, 5, 6, 7, 8, 10, 11, 12, 13, 14, 20, 21, 22, 23,
             24, 26, 27, 28, 29, 31, 32, 33, 34, 36, 37, 38, 39, 40, 41, 42,
             43, 44, 45, 47, 49, 52}


def song_control() -> dict:
    records = sound_records()
    metadata, streams, dac_notes = 0, set(), 0
    max_tracks = 0
    for (request, kind), header in sorted(records.items()):
        if kind != 18:
            continue
        metadata += 1
        midi_id = struct.unpack_from(">H", header, 0)[0]
        midi = records[(midi_id, 20)]
        streams.add(midi_id)
        parsed = midi_tracks(midi)
        max_tracks = max(max_tracks, len(parsed))
        banks = INITIAL_BANK.copy()
        for _tick, status, payload in scheduled(parsed):
            channel = status & 0xf
            if channel >= 14:
                continue
            high = status & 0xf0
            if high == 0xc0:
                banks[channel] = payload[0]
            elif high == 0x90 and payload[1] and banks[channel] in MODE6_DAC:
                dac_notes += 1
    assert metadata == 33 and len(streams) == 30 and max_tracks == 10
    assert dac_notes == 0
    return {"metadata_records": metadata, "distinct_streams": len(streams),
            "max_tracks": max_tracks, "mode6_DAC_note_ons": dac_notes}


def collect() -> dict:
    texts, program = inventory()
    modules = {m["key"]: m for m in program["modules"]}
    provider = modules["source-owned:sample-free-list"]
    contract = provider["storage_contract"]
    expected = [{"name": "_fd_50F6_0150", "kind": "far", "length": 156,
                 "count": 39, "element_size": 4}]
    assert contract["communals"] == expected
    source = texts[provider["source"]]
    assert " ".join(t.text for t in csrc.tokenize(source)
                    if t.kind not in {"ws", "nl", "cmt"}) == \
           "struct Sample ; struct Sample far * far fd_50F6_0150 [ 39 ] ;"
    enqueue = significant_function("src/root/m0000.c", "f_0000_0149")
    assert "if ( g_181C > 38 ) Punt" in enqueue
    assert enqueue.index("if ( g_181C > 38 )") < enqueue.index("fd_50F6_0150 [ g_181C ++ ] = s")
    census = source_census(texts)
    controls = [original_store_case(0, False), original_store_case(38, False),
                original_store_case(39, False), original_store_case(39, True)]
    assert [c["store_completed"] for c in controls] == [True, True, False, True]
    return {
        "schema": "simant-sample-free-list-domain-v1",
        "scope": "Successful canonical lifetime through the first free-list fatal boundary; returning-Punt continuation, historical placement and original producer TU are excluded.",
        "oracle_sha256": exe.load().sha256,
        "program_sha256": sha((ROOT / "src/program.json").read_bytes()),
        "sound_assets": {
            "SOUND.DAT": sha((ROOT / "assets/SOUND.DAT").read_bytes()),
            "SOUND.NDX": sha((ROOT / "assets/SOUND.NDX").read_bytes()),
        },
        "function_definition_sha256": {"f_0000_0149": sha(enqueue.encode())},
        "source_census": {"rows": census,
                          "sha256": sha(json.dumps(census, separators=(",", ":")).encode())},
        "original_boundary_controls": controls,
        "song_control": song_control(),
        "owner": {"entries": 39, "element_bytes": 4, "extent_bytes": 156,
                  "initialization": "MSC far communal zero initialization"},
        "historical_extent": "UNCLAIMED",
    }


def check() -> dict:
    actual = collect()
    expected = json.loads((Path(__file__).parent / "facts.json").read_text())
    if actual != expected:
        raise ValueError("sample free-list proof differs from reviewed facts")
    return actual


if __name__ == "__main__":
    check()
    print("PASS: 39-entry sample free-list owner and boundary controls")
