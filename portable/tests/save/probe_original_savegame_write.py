"""Capture SaveGame's real DOS writes through controlled CRT file callbacks."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))
import behavior
import json as json_module

SOURCE = ROOT / "src/S09/m35F5.c"
OUT = ROOT / "build/workers/savegame_original_write"
OUT.mkdir(parents=True, exist_ok=True)
PAYLOAD = OUT / "captured-savegame.bin"

def main() -> None:
    writes: list[bytes] = []
    def write(machine, args):
        if len(args) != 4:
            raise RuntimeError(f"write DOS ABI expected fd/off/seg/count, got {args}")
        fd, off, seg, count = args
        if fd != 7:
            raise RuntimeError(f"unexpected controlled fd {fd}")
        writes.append(machine.read(seg * 16 + off, count))
        return count

    callbacks = {
        "open": behavior.Callback(3, handler=lambda machine, args: 7),
        "write": behavior.Callback(4, handler=write),
        "close": behavior.Callback(1, handler=lambda machine, args: 0),
        "f_1C62_0415": behavior.Callback(3, handler=lambda machine, args: 0),
        "f_1C62_00C0": behavior.Callback(2, handler=lambda machine, args: 0),
    }
    pair = behavior.PreparedPair("o09_35F5_0188", source=SOURCE,
                                 out="build/workers/savegame_original_write/prepared")
    name_at = behavior.symbol_address("fd_50F6_3862")
    dirty_at = behavior.symbol_address("fd_3D57_02C2")
    case = behavior.Case(
        "savegame/controlled-existing-file-write", args=[1],
        writes=[(name_at, b"DOSPROBE.ANT\0"), (dirty_at, b"\x01\x00")],
        callbacks=callbacks, return_kind="s16",
        observe=[behavior.Range("dirty", dirty_at, 2)])
    result = pair.original_machine.run(case)
    payload = b"".join(writes)
    table = json_module.loads((ROOT / "portable/tests/dialogs/evidence/savegame-format-source-inventory-v1/save-records.json").read_text(encoding="utf-8"))
    expected_lengths = [row["serialized_bytes"] for row in table["table"]["records"]]
    if len(writes) != len(expected_lengths) or [len(chunk) for chunk in writes] != expected_lengths:
        raise RuntimeError("original DOS writes do not match the pinned 307 SaveRec row extents/order")
    if len(payload) != 48386:
        raise RuntimeError(f"original DOS payload has {len(payload)} bytes, expected 48386")
    PAYLOAD.write_bytes(payload)
    report = {
        "schema": "simant-savegame-controlled-dos-write-v1",
        "status": "ORIGINAL_DOS_WRITE_CAPTURED",
        "function": "o09_35F5_0188",
        "source": "src/S09/m35F5.c",
        "source_sha256": behavior.digest(SOURCE.read_bytes()),
        "oracle_sha256": behavior.exe.load().sha256,
        "harness_sha256": behavior.digest(behavior.HARNESS_SOURCE),
        "pair_identity": pair.identity,
        "controlled_file_operations": {"open_returned": 7, "confirm_overwrite_returned": 0,
                                        "write_count": len(writes), "close_returned": 0},
        "row_byte_counts": [len(x) for x in writes],
        "payload_bytes": len(payload),
        "payload_sha256": hashlib.sha256(payload).hexdigest(),
        "dirty_after": result["ranges"]["dirty"],
        "dos_return": result["return"],
        "payload_path": str(PAYLOAD.relative_to(ROOT)).replace("\\", "/"),
        "limitations": ["This captures the actual DOS SaveGame record writes under controlled CRT open/write/close callbacks.",
                        "It does not perform a live filesystem write; the captured bytes remain ignored build evidence."]
    }
    (OUT / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status":report["status"], "write_count":len(writes),
                      "payload_bytes":len(payload), "payload_sha256":report["payload_sha256"],
                      "dirty_after":report["dirty_after"], "dos_return":report["dos_return"]}, indent=2))

if __name__ == "__main__":
    main()
