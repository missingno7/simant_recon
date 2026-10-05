"""Contrast the missing Event.v stack word in the hash-pinned DOS executable.

Original instructions are comparison inputs only. This is neither a native
normalization policy nor a proof that a particular game input reaches an observer.
"""
from pathlib import Path
from types import SimpleNamespace
import hashlib
import json
import struct
import sys

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src/program.json").is_file())
sys.path.insert(0, str(ROOT / "tools"))
import behavior as b
import exe
import functions


def words(*values):
    return struct.pack("<" + "H" * len(values), *(v & 65535 for v in values))


image = exe.load()
assert image.sha256 == "aa0596c6766322a8229ee3c36e57048c92adc82d50fbe2ef37afb8b85fcf4f11"
entry = functions.get("f_1B73_030F")
queue = b.symbol("input_queue")
queue_address = queue["seg"] * 16 + queue["off"]
capacity, count, write, read = (b.symbol_address(n) for n in
                             ("g_5FF0", "g_5FF2", "g_5FF4", "g_5FF6"))
queue_pointer = b.symbol_address("g_5FFE")
vectors = {exe.MANAGER_SEG * 16 + v.offset: v for v in image.vectors}
ss, sp = b.match.DGROUP_SEG, 0xA400


def run(label, argc, ambient):
    initialization = [(capacity, words(7)), (count, words(0)),
                      (write, words(0)), (read, words(0)),
                      (queue_pointer, words(queue["off"])),
                      (queue_address, b"\xCC" * 16),
                      (0x417, words(0)), (0x46C, words(0x1234))]
    # Contrast memory beyond the four supplied words. The five-word control
    # supplies its own zero at this position and receives the same contrast
    # beyond its complete argument frame.
    initialization.append((ss * 16 + sp + 4 + 2 * argc, words(ambient)))
    machine = b.Machine(SimpleNamespace(function=entry, vectors=vectors))
    result = machine.run(b.Case(
        label=label, args=[0xFD01, 0, 0, 0] + ([0] if argc == 5 else []),
        writes=initialization,
        observe=[b.Range("event", queue_address, 16), b.Range("queue", count, 6)],
        return_kind="void", registers={"ss": ss, "sp": sp}))
    record = bytes.fromhex(result["ranges"]["event"])
    queued = struct.unpack("<HHH", bytes.fromhex(result["ranges"]["queue"]))
    v = struct.unpack_from("<H", record, 10)[0]
    code = struct.unpack_from("<H", record, 12)[0]
    assert v == (ambient if argc == 4 else 0), (label, v)
    assert code == 0xFD01 and queued == (1, 1, 0), (label, code, queued)
    return {"label": label, "argc": argc, "ambient": ambient,
            "event_v": v, "event_code": code, "event_hex": record.hex(),
            "queue_count_write_read": list(queued)}


runs = [run("four-word-1212", 4, 0x1212), run("four-word-abcd", 4, 0xABCD),
        run("five-word-zero-1212", 5, 0x1212), run("five-word-zero-abcd", 5, 0xABCD)]
assert runs[0]["event_v"] != runs[1]["event_v"]
assert runs[2]["event_hex"] == runs[3]["event_hex"]
pins = {rel: hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() for rel in
        ("src/root/m1B73.asm", "src/S10/m35F5.c", "src/S19/m384C.c",
         "src/S04/m35F5.c", "src/root/m218D.c", "tools/behavior.py")}
print(json.dumps({
    "schema": "simant-original-event-omitted-word-contrast-v1",
    "status": "PASS_COUNTEREXAMPLE_TO_ZERO_NORMALIZATION",
    "oracle_sha256": image.sha256, "source_pins": pins,
    "entry": {k: entry[k] for k in ("name", "unit", "seg", "off", "size") if k in entry},
    "event_v_offset": 10, "event_code_offset": 12, "runs": runs,
    "scope": "Original enqueue instructions with explicit synthetic caller frames; no whole-game interleaving or human-playtest causal claim.",
    "disposition": "Keep native-event-omitted-word open; zero is not an equivalent raw-state lowering."
}, indent=2))
