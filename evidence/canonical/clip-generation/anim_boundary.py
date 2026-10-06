"""Execute one synthetic capacity-crossing clip_SubExclude call in the oracle."""
from __future__ import annotations

import hashlib
from pathlib import Path
import struct
import sys
import types

sys.dont_write_bytecode = True
ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src/program.json").is_file())
sys.path.insert(0, str(ROOT / "tools"))

import behavior as b
import exe
import functions

ORACLE_SHA256 = "aa0596c6766322a8229ee3c36e57048c92adc82d50fbe2ef37afb8b85fcf4f11"


def _far(address: int) -> tuple[int, int]:
    return address & 15, address >> 4


def _encoded(rectangles: list[list[int]]) -> bytes:
    return b"".join(struct.pack("<4h", *rect) for rect in rectangles) + struct.pack("<4h", 0, -32768, 0, 0)


def execute(fixture: dict) -> dict:
    """Run exactly the checked SubExclude boundary call from its rectangle fixture."""
    incoming = fixture["incoming_current_list"]
    excluded = fixture["excluded_rectangles"]
    if len(incoming) != 255 or len(excluded) != 1:
        raise ValueError("fixture must contain the reviewed 255-record list and one excluded rectangle")

    image = exe.load()
    if image.sha256 != ORACLE_SHA256 or hashlib.sha256(image.path.read_bytes()).hexdigest() != ORACLE_SHA256:
        raise ValueError("locked original executable differs")
    machine = b.Machine(types.SimpleNamespace(function=functions.get("clip_SubExclude"),
        vectors={exe.MANAGER_SEG * 16 + vector.offset: vector for vector in image.vectors}))
    allocations: dict[int, dict] = {}
    events: list[dict] = []
    stopped = False
    temporary_address = None
    context = {"loop": 2, "role": "swarm-old-1-1", "rect": excluded[0]}

    def allocate(m, args):
        nonlocal temporary_address
        size = args[0] | args[1] << 16
        slot = len(allocations)
        handle = 0x68000 + slot * 4
        address = 0x70000 + slot * 0x1000
        tag = m.read(args[4] * 16 + args[3], 40).split(b"\0", 1)[0].decode("ascii")
        allocations[handle] = {"address": address, "size": size, "tag": tag, "slot": slot}
        if tag == "subexclude":
            temporary_address = address
        m.write(address, b"\x7a" * (size + 16))
        m.write(handle, struct.pack("<HH", *_far(address)))
        return _far(handle)

    def lock(m, args):
        return _far(allocations[args[1] * 16 + args[0]]["address"])

    def release(m, args):
        return None

    def resize(m, args):
        return args[0], args[1]

    def copy(m, args):
        m.write(args[1] * 16 + args[0], m.read(args[3] * 16 + args[2], args[4]))
        return args[0], args[1]

    callbacks = {
        "f_171C_1A9E": b.Callback(5, allocate),
        "f_171C_1B84": b.Callback(2, lock),
        "f_171C_1BBA": b.Callback(2, lock),
        "f_171C_1C0A": b.Callback(2, release),
        "f_171C_1B2C": b.Callback(5, resize),
        "__fmemcpy": b.Callback(5, copy),
    }

    def code_hook(cpu, address, size, user):
        nonlocal stopped
        if address != b.symbol_address("Punt"):
            return
        stack = machine.reg("ss") * 16 + machine.reg("sp")
        message_offset, message_segment = struct.unpack("<2H", machine.read(stack + 4, 4))
        generated = None
        if temporary_address is not None:
            for index in range(512):
                top = struct.unpack("<h", machine.read(temporary_address + index * 8 + 2, 2))[0]
                if top == -32768:
                    generated = index
                    break
        events.append({"event": "Punt-entry",
            "message": machine.read(message_segment * 16 + message_offset, 80).split(b"\0", 1)[0].decode("ascii"),
            "generated_count_including_overflow_record": generated, **context})
        stopped = True
        cpu.emu_stop()

    def write_hook(cpu, access, address, size, value, user):
        for allocation in allocations.values():
            if allocation["tag"] == "subexclude" and allocation["address"] + 2048 <= address < allocation["address"] + 2064:
                events.append({"event": "scratch-overrun", "displacement": address - allocation["address"],
                    "bytes": size, "pc": "%04X:%04X" % (machine.reg("cs"), machine.reg("ip")), **context})

    machine.cpu.hook_add(b.uc.UC_HOOK_CODE, code_hook)
    machine.cpu.hook_add(b.uc.UC_HOOK_MEM_WRITE, write_hook)
    current = b.symbol_address("fd_50F6_3C14")
    cutter = 0x69000
    writes = [
        (current, _encoded(incoming)),
        (b.symbol_address("g_5AAC"), struct.pack("<HH", *_far(current))),
        (b.symbol_address("g_5742"), bytes(12)),
        (b.symbol_address("g_5756"), bytes(4)),
        (b.symbol_address("fd_50F6_3B5C"), bytes(4)),
        (cutter, struct.pack("<4h", *excluded[0])),
    ]
    case = b.Case("single_same_anchor-original-boundary", args=list(_far(cutter)), writes=writes,
        callbacks=callbacks, return_kind="void", max_instructions=2_000_000,
        max_blocks=400_000, observe_at_calls=False)
    try:
        machine.run(case, original_entry=functions.get("clip_SubExclude"))
    except b.ExecutionError:
        if not stopped:
            raise
    if machine.error:
        raise machine.error
    return {
        "label": "single_same_anchor-original-boundary",
        "starting_count": len(incoming),
        "events": events,
        "stopped_at_punt": stopped,
        "original_bodies": ["clip_SubExclude", "f_1E57_0009", "f_1D8E_003F", "f_1D8E_0002"],
        "modeled_services": ["heap allocation/resize/lock/unlock/free", "far memcpy"],
        "scope": "Synthetic same-anchor loop-2 rectangle fixture; one capacity-crossing clip_SubExclude call runs from original instructions. Heap services and far memcpy are explicit models.",
    }
