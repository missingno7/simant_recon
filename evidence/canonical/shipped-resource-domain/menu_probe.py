"""Original menu geometry and mouse descriptor/event controls.

Executes the unmodified DOS bodies in the existing isolated oracle. Resources
are loaded at runtime, never embedded into reconstruction source or objects.
Geometry models only drawing/clip/font services. Mouse dispatch, descriptor
callback and event enqueue execute original instructions without callbacks.
"""
from pathlib import Path
from types import SimpleNamespace
import argparse
import hashlib
import json
import struct
import sys

sys.dont_write_bytecode = True
ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src/program.json").is_file())
sys.path.insert(0, str(ROOT / "tools"))
import behavior as b
import exe
import functions
import modctx
import resource_domains

DGROUP = 0x55b3
FARDATA = 0x50f6
MENUSEG = 0xa000


def pair(name):
    image = exe.load()
    return SimpleNamespace(function=functions.get(name),
        vectors={exe.MANAGER_SEG * 16 + v.offset: v for v in image.vectors},
        identity={"oracle_sha256": image.sha256})


def shipped_menu():
    return next(x["payload"] for x in resource_domains.decoder().parse_records("SHARED")[1]
                if (x["id"], x["kind"]) == (0, 6))


def relocated(raw):
    result = bytearray(raw)
    outer, _ = resource_domains.offset_list(raw, 0)
    for start in [0, *outer]:
        pointers, _ = resource_domains.offset_list(raw, start)
        for i, target in enumerate(pointers):
            struct.pack_into("<HH", result, start + 4 * i, target, MENUSEG)
    return bytes(result)


def geometry_case(raw):
    def strlen(machine, args):
        address = args[1] * 16 + args[0]
        return machine.read(address, len(raw)).index(0)
    no = lambda machine, args: None
    writes = [(MENUSEG * 16, relocated(raw)),
        (DGROUP * 16 + 0x6054, b.words(0, MENUSEG)),
        (DGROUP * 16 + 0x9130, b.words(functions.get("f_1FD2_05FD")["off"], 0x1fd2)),
        (DGROUP * 16 + 0x3db2, b.words(640)),
        (DGROUP * 16 + 0x3ddc, bytes([14])),
        (DGROUP * 16 + 0x3dde, bytes([7])),
        (FARDATA * 16 + 0x393c, b.words(0, 0, 640, 480)),
        (FARDATA * 16 + 0x46a8, b.words(*([0x7a7a] * 6))),
        (FARDATA * 16 + 0x46bc, b.words(*([0x7a7a] * 6)))]
    result = b.Machine(pair("f_1FD2_0663")).run(b.Case(label="menu-geometry", args=[0],
        writes=writes, observe=[b.Range("x", FARDATA * 16 + 0x46a8, 12),
            b.Range("width", FARDATA * 16 + 0x46bc, 12), b.Range("count", DGROUP * 16 + 0x604c, 2)],
        callbacks={"f_1FD2_05FD": b.Callback(0, no), "f_1FD2_02B1": b.Callback(1, no),
            "f_1CE2_000C": b.Callback(0, lambda m, a: (0x393c, FARDATA)),
            "__fstrlen": b.Callback(2, strlen)}))
    return {name: list(struct.unpack("<" + "H" * (len(value) // 4), bytes.fromhex(value)))
            for name, value in result["ranges"].items()}


def sixth_title_menu(raw):
    domain = resource_domains.menu_domain(raw)
    texts = [raw[p:raw.index(0, p) + 1] for p in domain["lists"][0]["string_offsets"]]
    texts.append(texts[0])
    text_start = 84
    offsets = []
    for text in texts:
        offsets.append(text_start)
        text_start += len(text)
    result = b"".join(struct.pack("<I", n) for n in
        [32, 60, 64, 68, 72, 76, 80, 0, *offsets, 0, *([0] * 6)]) + b"".join(texts)
    if resource_domains.menu_domain(result)["title_count"] != 6:
        raise ValueError("six-title contrast is not a structurally valid menu")
    return result


def mouse_case(index, *, outside=False):
    # Original descriptor layout: rect8, callback4, code2, extra2, mask2.
    xs = [0, 56, 126, 182, 259]
    lengths = [5, 7, 5, 8, 6]
    fn = functions.get("f_1B73_030F")
    records = b.words(5) + b"".join(b.words(x, 1, x + 7 * width, 15,
        fn["off"], fn["seg"], 0xfe00 + i, 0x0101, 0x0a00)
        for i, (x, width) in enumerate(zip(xs, lengths)))
    # The event queue pointer is the initialized near field at 5FFE. Redirect
    # that pointer to isolated DGROUP space; no oracle instruction is patched.
    writes = [(0x5071 * 16 + 2, b.words(0)), (0x5071 * 16 + 0x60, b.words(0)),
        (0x5071 * 16 + 0x3c4, records),
        (DGROUP * 16 + 0x5ff0, b.words(7, 0, 0, 0)),
        (DGROUP * 16 + 0x5ff8, bytes([0, 0x1f]) + b.words(0x0cb3, 0, 0xb000)),
        (DGROUP * 16 + 0xb000, bytes(16)),
        (DGROUP * 16 + 0x4365, bytes([0]))]
    machine = b.Machine(pair("f_1B73_0445"))
    result = machine.run(b.Case(label="menu-mouse-descriptor", writes=writes,
        registers={"ax": 2, "bx": 0, "cx": 639 if outside else xs[index] + 3, "dx": 3},
        observe=[b.Range("event", DGROUP * 16 + 0xb000, 16),
                 b.Range("count", DGROUP * 16 + 0x5ff2, 2)], return_kind="void"))
    event = bytes.fromhex(result["ranges"]["event"])
    count = int.from_bytes(bytes.fromhex(result["ranges"]["count"]), "little")
    outcome = dict(count=count, code=struct.unpack_from("<H", event, 12)[0], blocks=result["blocks"])
    if count:
        delivered = machine.run(b.Case(label="menu-window-event-delivery",
            args=[0, 0xa100], callee_pop=4,
            callbacks={"f_1B28_0069": b.Callback(0, lambda m, a: None),
                       "f_0000_046F": b.Callback(0, lambda m, a: None)},
            observe=[b.Range("event", 0xa100 * 16, 16)]),
            preserve=True, original_entry=functions.get("win_GetEvent"))
        outcome["delivered_code"] = struct.unpack_from("<H", bytes.fromhex(delivered["ranges"]["event"]), 12)[0]
    return outcome


def controls():
    raw = shipped_menu()
    actual = geometry_case(raw)
    # Structurally valid six-title menu, outside the pinned corpus domain.
    contrast = geometry_case(sixth_title_menu(raw))
    mouse = [mouse_case(i) for i in range(5)]
    miss = mouse_case(0, outside=True)
    if actual != {"x": [0, 56, 126, 182, 259, 0x7a7a], "width": [5, 7, 5, 8, 6, 0x7a7a], "count": [5]}:
        raise ValueError("shipped menu geometry/access footprint changed")
    if contrast["count"] != [6] or contrast["x"][5] == 0x7a7a or contrast["width"][5] == 0x7a7a:
        raise ValueError("sixth-title contrast failed to expose unsupported access")
    if [(x["count"], x["code"], x["delivered_code"]) for x in mouse] != [(1, 0xfe00 + i, 0xfe00 + i) for i in range(5)]:
        raise ValueError("original mouse callback/queue did not preserve registered title IDs")
    if miss["count"]:
        raise ValueError("mouse outside registered titles fabricated an event")
    return dict(actual=actual, sixth_title_contrast=contrast, mouse=mouse, outside_all_titles=miss)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    out = modctx.under_build(ROOT / args.out)
    out.mkdir(parents=True, exist_ok=False)
    report = dict(schema="simant-menu-supported-domain-oracle-v1", status="PASS",
        oracle_sha256=exe.load().sha256, results=controls(),
        model_boundaries=["geometry: drawing/clip/font callbacks", "isolated pointer/resource/descriptor state", "mouse: no callbacks"],
        inputs={p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in
            ("src/root/m1FD2.c", "src/root/m1B73.asm", "assets/SHARED.DAT", "assets/SHARED.NDX", "tools/behavior.py")})
    (out / "menu.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
