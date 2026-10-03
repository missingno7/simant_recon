from __future__ import annotations

import hashlib
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))
import behavior

TARGET = "o19_384C_0383"
OUT = ROOT / "build/workers/event_word_switch/dos-directed"
EVENT_OFF = 0x2400
EVENT_SEG = 0xA000

def _capture(machine, args):
    return None


CALLBACKS = {
    "WinPrintf": behavior.Callback(stack_words=4, handler=_capture),
    "YardToMap": behavior.Callback(stack_words=0, handler=_capture),
    "f_1B73_030F": behavior.Callback(stack_words=5, handler=_capture),
    "YellowCommand": behavior.Callback(stack_words=1, handler=_capture),
    "YellowCommandKey": behavior.Callback(stack_words=1, handler=_capture),
    "DoTab": behavior.Callback(stack_words=0, handler=_capture),
}


def case(code: int, message: int, label: str):
    record = struct.pack("<8H", 0, message & 0xffff, 0x1234, 0,
                         11, 22, code & 0xffff, 0xABCD)
    address = EVENT_SEG * 16 + EVENT_OFF
    return behavior.Case(
        label=label, args=[EVENT_OFF, EVENT_SEG],
        writes=[(address, record)],
        observe=[behavior.Range("event", address, 16)],
        callbacks=CALLBACKS, return_kind="void",
        metadata={"event_code_u16": code & 0xffff,
                  "message_flags": message & 0xffff,
                  "source_event_layout": "8 DOS words; code at +12; message at +2"},
    )


def main() -> None:
    out = OUT
    out.mkdir(parents=True, exist_ok=True)
    pair = behavior.PreparedPair(TARGET, source=ROOT / "src/S19/m384C.c",
                                 out=out / "prepared-original-source")
    cases = []
    keys = [0xFA05, 0xFA06, 0xFA07, 0xFA08, 0xFA09, 0xFA0A,
            0xFA0B, 0xFA17, 0xFA23, 0xFA03, 0xFA0E, 0xFA0F,
            0xF905, 0xFB05, 0x00FA, 0x7A05, 0xFFFF, 0x8000,
            0x0000, 0xFA04, 0xFA10]
    flags = [0, 4, 8, 12]
    for key in keys:
        for message in flags:
            cases.append(case(key, message, f"code-{key:04x}-message-{message:04x}"))
    comparisons = [pair.compare(item) for item in cases]
    rows = []
    for item, result in zip(cases, comparisons):
        rows.append({"case": item.label, "event_code": item.metadata["event_code_u16"],
                     "message": item.metadata["message_flags"], "exact": result.equal,
                     "diff": result.diff, "original_trace": result.original.get("trace"),
                     "candidate_trace": result.candidate.get("trace")})
    report = {
        "schema": "dos-event-word-switch-directed-v1",
        "target": TARGET,
        "source_path": "src/S19/m384C.c",
        "source_sha256": hashlib.sha256((ROOT / "src/S19/m384C.c").read_bytes()).hexdigest(),
        "function_identity": pair.identity,
        "directed_case_count": len(rows),
        "mismatch_count": sum(not r["exact"] for r in rows),
        "cases": rows,
    }
    path = out / "report.json"
    if path.exists():
        raise SystemExit(f"refusing to overwrite {path}")
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"DOS directed: {len(rows)} cases, {report['mismatch_count']} differences")
    if report["mismatch_count"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
