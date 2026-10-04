"""Differential text layout fixtures for S23's DOS renderer routines.

Font selection, font height, glyph width, string helpers, and the target code
execute from the original DOS image. Only the final glyph draw is a host
boundary; it records the exact ordered x/y/text request.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import struct
import sys
import time
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'layout/functions.json').is_file())

import behavior as b
from behavior_ledger import CaseLedger

FUNCTION = "win_PrintStyleTextInRect"
CARD_FUNCTION = "DisplayCard"
HISTORY_FUNCTION = "drawHistGraph"
FORMAT_CURSOR_PROOF = "evidence/canonical/runtime/format-cursors.json"
FORMAT_CURSOR_PROOF_SHA256 = "140c1d240cf48c5c868ccdd723b4651d71735f592b3d5baed1f4d552cbfbc628"
SUITE_BYTES = Path(__file__).read_bytes()
TEXT = (0x1000, 0xA000)
STYLES = (0x3000, 0xA000)
RECT = (0x4000, 0xA000)


def far(off, seg):
    return struct.pack("<HH", off, seg)




def style_record(pos, face, height=12, ascent=9, font=2, size=12):
    return struct.pack("<I8h", pos & 0xFFFFFFFF, height, ascent, font, face,
                       size, 0, 0, 0)


def _fixture_fonts():
    """Build valid, disjoint far-font records for original metric helpers.

    The raster-producing f_24AB_038D entry is still an explicit logical draw
    boundary, but the caller's font selection, height, string-width, and
    character-width helpers now read real Font records and tables in the VM.
    """
    segment = 0xA300
    records = []
    pointers = []
    specs = {
        # Proportional widths vary by glyph; '?' deliberately resolves through
        # the font's missing-glyph slot.
        2: {"proportional": 1, "kern": 0, "wid": 9, "height": 9,
            "leading": 2, "missing_char": ord("?")},
        # Negative kernMax selects the original helper's one-pixel bonus.
        3: {"proportional": 1, "kern": -1, "wid": 11, "height": 11,
            "leading": 1, "missing_char": ord("!")},
        # A valid fixed-width font with zero advance is a useful boundary case.
        4: {"proportional": 0, "kern": 1, "wid": 0, "height": 8,
            "leading": 0, "missing_char": None},
        5: {"proportional": 0, "kern": 2, "wid": 7, "height": 14,
            "leading": 3, "missing_char": None},
    }
    writes = []
    for slot, font_id in enumerate(range(2, 6)):
        spec = specs[font_id]
        base = 0x0100 + slot * 0x1000
        image_off, loc_off, ow_off = base + 0x100, base + 0x200, base + 0x500
        missing = 126 - 32 + 1
        words = [0, 32, 126, spec["wid"], spec["kern"], 0,
                 256, spec["height"], 0, spec["height"] - 2, 1,
                 spec["leading"], 16]
        record = (struct.pack("<13h", *words) + far(image_off, segment) +
                  far(loc_off, segment) + far(ow_off, segment) +
                  struct.pack("<2H", spec["proportional"], missing))
        if len(record) != 42:
            raise AssertionError("Font record must match the 42-byte DOS layout")
        pointers.append(far(base, segment))
        writes.append((segment * 16 + base, record))
        writes.append((segment * 16 + image_off, bytes(512)))
        loc = list(range(258))
        writes.append((segment * 16 + loc_off, struct.pack("<258H", *loc)))
        widths = [5 + (ch % 4) for ch in range(257)]
        widths[ord(" ")] = 3
        widths[ord("i")] = 2
        widths[ord("W")] = 9
        widths[ord("m")] = 7
        if spec["missing_char"] is not None:
            widths[spec["missing_char"]] = 0xFFFF
        widths[missing] = 4
        writes.append((segment * 16 + ow_off, struct.pack("<257H", *widths)))
        records.append({"font_id": font_id, "far_pointer": [base, segment],
            "proportional": spec["proportional"], "kernMax": spec["kern"],
            "widMax": spec["wid"], "fRectHeight": spec["height"],
            "leading": spec["leading"], "missing_index": missing,
            "missing_character": spec["missing_char"],
            "width_samples": {str(ch): widths[ch] for ch in
                               (ord(" "), ord("i"), ord("W"), ord("m"))}})
    table = b.symbol_address("fd_50F6_4A1A")
    writes.append((table, b"".join(pointers)))
    return writes, records


def render_project(machine, args):
    off, seg = args[2], args[3]
    raw = bytearray()
    for i in range(2048):
        c = machine.read(seg * 16 + off + i, 1)[0]
        if c == 0:
            break
        raw.append(c)
    else:
        raise AssertionError("unterminated renderer text")
    return {"x": args[0], "y": args[1], "text_hex": bytes(raw).hex()}


def draw(machine, args):
    machine.state.setdefault("draws", []).append(machine.trace[-1]["args"])
    v = machine.state["volatile"]
    for reg in ("ax", "bx", "cx", "dx", "es"):
        machine.set_reg(reg, v)


def make_case(label, text, rect, styles=(), first_line=0, record=0,
              volatile=0xA55A, font1=2, font2=5):
    if b"\0" in text:
        raise ValueError("embedded NUL in text")
    style_rows = []
    for style in styles:
        if len(style) == 2:
            pos, face = style
            font = 2
        else:
            pos, face, font = style
        style_rows.append(style_record(pos, face, font=font))
    style_bytes = struct.pack("<H", len(styles)) + b"".join(style_rows)
    args = [TEXT[0], TEXT[1], *(STYLES if styles else (0, 0)),
            RECT[0], RECT[1], first_line, font1, font2, record]
    font_writes, font_records = _fixture_fonts()
    writes = [(TEXT[1] * 16 + TEXT[0], text + b"\0"),
              (RECT[1] * 16 + RECT[0], struct.pack("<4h", *rect)),
              # Other display state is kept explicit; active font metrics come
              # from the four valid far Font records below.
              (b.symbol_address("g_3DB2"), struct.pack("<H", 320)),
              (b.symbol_address("g_3DDC"), struct.pack("<b", 12)),
              (b.symbol_address("g_3DDE"), struct.pack("<b", 8)),
              *font_writes]
    if styles:
        writes.append((STYLES[1] * 16 + STYLES[0], style_bytes))
    return b.Case(label, args=args, writes=writes,
        # The static hot-spot arrays/counter are private to the S23 module and
        # intentionally lack public oracle symbols. The VM compares every
        # nonstack byte written by either side, including those private writes.
        observe=[],
        callbacks={"f_24AB_038D": b.Callback(4, draw, project=render_project)},
        return_kind="void", callee_pop=0,
        state={"draws": [], "volatile": volatile},
        metadata={"rect": list(rect), "styles": [list(s) for s in styles],
                  "first_line": first_line, "record": record,
                  "text_hex": text.hex(), "volatile": volatile,
                  "font_records": font_records,
                  "metrics": "original f_24AB_02AD/030B/0329/0367 and MSC far-string helpers over four valid VM Font records: proportional variable widths, proportional negative-kern bonus and missing glyphs, fixed zero width, and fixed width 7; raster remains the logical f_24AB_038D draw-request boundary"})


def cases(count, seed):
    fixed_texts = [b"", b"A", b"short words wrap here", b"a\tb  c\r\nnext",
                   b"(x), [y]! z? {w}-q.", b"one two three four five six"]
    rects = [(0, 0, 320, 200), (-20, 7, 28, 47), (4, -13, 19, 29),
             (100, 50, 101, 51), (0, 0, 640, 480)]
    stylesets = [(), ((0, 0x100, 2),), ((0, 0, 3), (4, 0x100, 4), (10, 0, 5)),
                 ((0, 0x100, 5), (2, 0, 2), (8, 0x100, 3))]
    for ti, text in enumerate(fixed_texts):
        for ri, rect in enumerate(rects):
            for si, styles in enumerate(stylesets):
                for first in (0, 1, 4):
                    yield "directed", make_case(
                        f"grid/{ti}/{ri}/{si}/{first}", text, rect, styles,
                        first, int(bool(styles) and si % 2 == 1))
    rng = random.Random(seed)
    alphabet = b" abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!?,.-()[]{}\r\n\t"
    for i in range(count):
        length = rng.randrange(1, 96)
        text = bytes(rng.choice(alphabet) for _ in range(length))
        rect = tuple(rng.randrange(-80, 641) for _ in range(4))
        # Keep widths/heights in the useful font-measurement domain while
        # retaining signed and inverted rectangle contrasts.
        if i % 3 == 0:
            rect = (rect[0], rect[1], rect[0] + rng.randrange(1, 180),
                    rect[1] + rng.randrange(1, 100))
        styles = () if rng.randrange(3) == 0 else tuple(
            (rng.randrange(0, length + 1), rng.choice((0, 0x100)),
             rng.choice((2, 3, 4, 5)))
            for _ in range(rng.randrange(1, 4)))
        styles = tuple(sorted(styles, key=lambda s: s[0]))
        yield "randomized", make_case(f"random/{seed}/{i}", text, rect, styles,
            rng.randrange(5), rng.randrange(2), rng.randrange(65536))


def be_words(*values):
    return struct.pack(">" + "H" * len(values), *(v & 0xFFFF for v in values))


def _resource_case(label, scenario, volatile=0xA55A, seed=0x5A23):
    """Card records use the DOS resource's big-endian word representation."""
    card_id = 0x80
    resources = []
    lookups = {}

    def add_resource(obj, kind, data, slot):
        handle = (0x500 + slot * 8, 0xA000)
        pointer = (0x0100 + slot * 0x100, 0xA200)
        item = {"object": obj, "kind": kind, "handle": handle,
                "pointer": pointer, "size": len(data), "data": data}
        resources.append(item)
        lookups[f"{obj}/{kind}"] = slot

    if scenario == "missing-card":
        pass
    elif scenario == "unknown-record":
        add_resource(card_id, 0x11, b"HEADX???", 0)
    elif scenario == "bitmap-link":
        # Prefix, P, one big-endian PicRec and one big-endian HotSpot.
        data = (b"HEAD" + b"P\0\0\0" + be_words(0x321, 3, 5, 23, 17, 1) +
                be_words(2, 4, 18, 22, 0x44))
        add_resource(card_id, 0x11, data, 0)
    elif scenario == "plain-text":
        card = b"HEAD" + b"T\0\0\0" + be_words(2, 3, 102, 58, 1) + be_words(0x91)
        add_resource(card_id, 0x11, card, 0)
        add_resource(0x91, 10, b"alpha beta\0    \0", 1)
    elif scenario == "styled-text":
        card = b"HEAD" + b"T\0\0\0" + be_words(2, 3, 142, 78, 1) + be_words(0x92)
        add_resource(card_id, 0x11, card, 0)
        add_resource(0x92, 10, b"CHITIN and brood\0    \0", 1)
        # Serialized style count and StyleRun words are big-endian. The DOS
        # routine applies FlipWords then XFlipLong to restore native fields.
        style = be_words(1) + struct.pack(">I8H", 0, 12, 9, 2, 0x100, 12, 0, 0, 0)
        add_resource(0x92, 0x15, style, 2)
    elif scenario == "randomized":
        rng = random.Random(seed)
        alphabet = b" ant brood chitin queen larva forage.\t-!?"
        card = bytearray(b"HEAD")
        slot = 0
        next_rez = 0x100 + (seed & 0x3FFF)
        picture_count = text_count = button_count = 0
        record_count = rng.randrange(1, 9)
        for rec_index in range(record_count):
            if rng.randrange(2) == 0:
                nlinks = rng.randrange(0, min(7, 65 - button_count))
                card.extend(b"P\0\0\0")
                card.extend(be_words(rng.randrange(1, 65536), rng.randrange(0, 50),
                    rng.randrange(0, 50), rng.randrange(100, 200),
                    rng.randrange(100, 260), nlinks))
                for _ in range(nlinks):
                    x0, y0 = rng.randrange(0, 260), rng.randrange(0, 160)
                    x1, y1 = x0 + rng.randrange(1, 40), y0 + rng.randrange(1, 25)
                    card.extend(be_words(x0, y0, x1, y1, rng.randrange(1, 65536)))
                picture_count += 1
                button_count += nlinks
            else:
                nframes = rng.randrange(1, 5)
                left, top = rng.randrange(0, 60), rng.randrange(0, 40)
                width, height = rng.randrange(40, 230), rng.randrange(32, 130)
                card.extend(b"T\0\0\0")
                card.extend(be_words(left, top, left + width, top + height, nframes))
                for frame in range(nframes):
                    rez = next_rez
                    next_rez = (next_rez + 1) & 0xFFFF
                    card.extend(be_words(rez))
                    text_len = rng.randrange(3, 36)
                    text = bytes(rng.choice(alphabet) for _ in range(text_len)).replace(b"\0", b" ")
                    add_resource(rez, 10, text + b"\0    \0", slot)
                    slot += 1
                    text_count += 1
                    if rng.randrange(2):
                        run_count = rng.randrange(1, 5)
                        positions = sorted(rng.randrange(0, text_len + 1) for _ in range(run_count))
                        style = bytearray(be_words(run_count))
                        for pos in positions:
                            style.extend(struct.pack(">I8H", pos, rng.randrange(8, 20),
                                rng.randrange(6, 16), rng.choice((2, 3, 5)),
                                rng.choice((0, 0x100)), rng.randrange(8, 24),
                                rng.randrange(65536), rng.randrange(65536), rng.randrange(65536)))
                        add_resource(rez, 0x15, bytes(style), slot)
                        slot += 1
        add_resource(card_id, 0x11, bytes(card), slot)
        random_summary = {"card_records": record_count, "pictures": picture_count,
                          "text_frames": text_count, "hotspot_links": button_count}
    else:
        raise ValueError(scenario)

    memory_writes = []
    for item in resources:
        off, seg = item["pointer"]
        memory_writes.append((seg * 16 + off, item["data"]))
    dg = b.match.DGROUP_SEG * 16
    memory_writes.extend([
        (dg + 0x3DB2, struct.pack("<H", 320)),
        (dg + 0x3DDC, struct.pack("<b", 12)),
        (dg + 0x3DDE, struct.pack("<b", 8)),
    ])

    rect = (10, 20, 310, 190)
    def res(machine, args):
        key = f"{args[0]}/{args[1]}"
        machine.state.setdefault("resource_requests", []).append(
            {"object": args[0], "kind": args[1], "type": args[2]})
        slot = machine.state["lookups"].get(key)
        if slot is None:
            return (0, 0)
        return tuple(machine.state["resources"][slot]["handle"])

    def by_handle(machine, args):
        off, seg = args[:2]
        for item in machine.state["resources"]:
            if item["handle"] == [off, seg] or tuple(item["handle"]) == (off, seg):
                return item
        raise b.ExecutionError(f"unknown resource handle {seg:04x}:{off:04x}")

    def lock(machine, args):
        item = by_handle(machine, args)
        machine.state.setdefault("resource_locks", []).append(item["kind"])
        return tuple(item["pointer"])

    def size(machine, args):
        return (by_handle(machine, args)["size"], 0)

    def unlock(machine, args):
        item = by_handle(machine, args)
        machine.state.setdefault("resource_unlocks", []).append(item["kind"])

    def purge(machine, args):
        machine.state.setdefault("purges", []).append(list(args))

    def print_log(machine, args):
        machine.state.setdefault("log_formats", []).append(machine.trace[-1]["args"])

    def get_rect(machine, args):
        machine.write((args[2] * 16 + args[1]), struct.pack("<4h", *machine.state["window_rect"]))

    def get_rect_input(machine, args):
        off, seg = args[:2]
        return {"rect": list(struct.unpack("<4h", machine.read(seg * 16 + off, 8)))}

    def simple(machine, args):
        machine.state.setdefault("commands", []).append({"name": machine.trace[-1]["name"],
                                                           "args": machine.trace[-1]["args"]})
        for reg in ("ax", "bx", "cx", "dx", "es"):
            machine.set_reg(reg, machine.state["volatile"])

    def bitmap(machine, args):
        machine.state.setdefault("bitmaps", []).append(list(args))
        for reg in ("ax", "bx", "cx", "dx", "es"):
            machine.set_reg(reg, machine.state["volatile"])
        return 1

    callbacks = {
        "f_1A53_00F0": b.Callback(3, res),
        "f_171C_1B84": b.Callback(2, lock),
        "f_171C_1C1C": b.Callback(2, size),
        "f_171C_1BBA": b.Callback(2, unlock),
        "db_PurgeObject": b.Callback(2, purge),
        "WinPrintf": b.Callback(0, print_log, ("ax",)),
        "f_22BF_059A": b.Callback(3, simple),
        "win_GetObjRect": b.Callback(2, get_rect, ("ax",), pop=4,
                                      project=lambda m, a: {"window": a[0],
                                          "destination": "caller rectangle",
                                          "result_rect": list(m.state["window_rect"])}),
        "clip_SetWin": b.Callback(1, simple),
        "clip_SubInclude": b.Callback(2, simple, project=get_rect_input),
        "win_SetColorFromObjNum": b.Callback(0, simple, ("ax",)),
        "win_DrawBitMap": b.Callback(0, bitmap, ("ax", "dx", "bx")),
        "f_24AB_038D": b.Callback(4, draw, project=render_project),
    }
    return b.Case(label, args=[card_id], writes=memory_writes, callbacks=callbacks,
        return_kind="void", callee_pop=0,
        state={"resources": resources, "lookups": lookups, "window_rect": rect,
               "volatile": volatile, "commands": [], "bitmaps": [], "draws": [],
               "resource_requests": [], "resource_locks": [], "resource_unlocks": [],
               "purges": [], "log_formats": []},
        metadata={"scenario": scenario, "card_id": card_id,
            "contract": "card resource fetch/lock/parse/draw/unlock/purge order; projected text and rectangle values",
            "boundary": "resource lookup, resource-handle lock/size/unlock and window geometry/clip/color/bitmap/raster services are modeled; card/text/style bytes and all parsing, transforms, string operations and layout execute in DOS/candidate code",
            "window_rect": list(rect), "random_summary": locals().get("random_summary", {}), "resources": [
                {"object": x["object"], "kind": x["kind"], "data_hex": x["data"].hex()} for x in resources]})


def card_cases(count=500, seed=0x5A23):
    for scenario in ("missing-card", "unknown-record", "bitmap-link", "plain-text", "styled-text"):
        yield "directed", _resource_case(scenario, scenario)
    rng = random.Random(seed)
    for i in range(count):
        case_seed = rng.randrange(1 << 32)
        yield "randomized", _resource_case(f"random/{seed:08x}/{i}", "randomized",
                                             volatile=rng.randrange(65536), seed=case_seed)


def _history_case(label, graph, hilite, slot, start, count, rect, seed,
                  array_mode="random"):
    x = b.exe.load()
    data_ptrs = []
    table_index = (graph & 1) * 5 + (graph >> 1)
    for table_name in ("fd_3D57_082A", "fd_3D57_0852"):
        table = b.symbol_address(table_name)
        raw = x.sections[27].data
        offset = b.symbol(table_name)["off"] + table_index * 4
        first = struct.unpack_from("<HH", raw, offset)
        data_ptrs.append(first)
    rng = random.Random(seed)
    arrays = []
    for array_index, (off, seg) in enumerate(data_ptrs):
        if array_mode == "zero":
            values = [0] * 64
        elif array_mode == "maximum":
            values = [120] * 64
        elif array_mode == "ramp":
            values = [i * 120 // 63 for i in range(64)]
        else:
            values = [rng.randrange(0, 121) for _ in range(64)]
        arrays.append((seg * 16 + off, struct.pack("<64h", *values)))
    line_fn = b.symbol("win_DrawBitMap")
    color_fn = b.symbol("win_SetColorFromObjNum")
    line_draw_ptr = (line_fn["off"], line_fn["seg"])
    color_ptr = (color_fn["off"], color_fn["seg"])
    writes = arrays + [
        (b.symbol_address("g_916C"), far(*line_draw_ptr)),
        (b.symbol_address("g_9128"), far(*color_ptr)),
        (b.symbol_address("fd_50F6_04F4"), struct.pack("<h", start)),
        (b.symbol_address("fd_3D57_0828"), struct.pack("<h", count)),
        (b.symbol_address("g_3DB2"), struct.pack("<H", 320)),
        (b.symbol_address("g_3DDC"), struct.pack("<b", 12)),
        (b.symbol_address("g_3DDE"), struct.pack("<b", 8)),
    ]
    def rectangle(machine, args):
        machine.write(args[2] * 16 + args[1], struct.pack("<4h", *machine.state["rect"]))
    def line(machine, args):
        machine.state.setdefault("segments", []).append(list(args))
    def color(machine, args):
        machine.state.setdefault("color_calls", []).append(list(args))
    def box(machine, args):
        machine.state.setdefault("boxes", []).append(list(args))
    def label_draw(machine, args):
        machine.state.setdefault("draws", []).append(machine.trace[-1]["args"])
    callbacks = {
        "win_GetObjRect": b.Callback(2, rectangle, ("ax",), pop=4,
            project=lambda m, a: {"window": a[0], "destination": "caller rectangle",
                                  "result_rect": list(m.state["rect"])}),
        "win_DrawBitMap": b.Callback(5, line),
        "win_SetColorFromObjNum": b.Callback(3, color),
        "f_24AB_038D": b.Callback(4, label_draw, project=render_project),
        "f_1CE2_01F8": b.Callback(5, box),
    }
    return b.Case(label, args=[graph, hilite, slot], writes=writes,
        callbacks=callbacks, return_kind="void", callee_pop=0,
        format_cursor_views=([b.FormatCursorView("sprintf-output-stream", 0x5E936,
            FORMAT_CURSOR_PROOF, FORMAT_CURSOR_PROOF_SHA256)] if hilite else []),
        state={"rect": rect, "volatile": (seed ^ 0xA55A) & 0xFFFF,
               "segments": [], "color_calls": [], "boxes": [], "draws": []},
        metadata={"graph": graph, "hilite": hilite, "slot": slot, "start": start,
            "sample_count": count, "window_rect": list(rect),
            "history_arrays": [p.hex() for _, p in arrays],
            "array_mode": array_mode,
            "contract": "graph sample scaling, ordered line segments, label and border; original table pointers select the two history arrays",
            "boundary": "window rectangle and line/color/text/border raster commands are modeled; history arrays and graph code execute directly; font helper calls use original DOS code with explicit fallback globals"})


def history_cases(random_count=2000, seed=0xD15EA5E):
    for graph in range(4):
        for hilite in (0, 1):
            for count, start, mode in ((0, 0, "zero"), (1, 1, "maximum"),
                                       (8, 8, "ramp"), (64, 63, "random"),
                                       (64, 0, "maximum"), (17, 63, "zero")):
                yield "directed", _history_case(
                    f"grid/{graph}/{hilite}/{count}/{start}", graph, hilite,
                    graph, start, count, (0, 0, 320, 200),
                    0x39C7032C + graph * 101 + hilite * 7 + count, mode)
    rng = random.Random(seed)
    for i in range(random_count):
        graph = rng.randrange(4)
        hilite = rng.randrange(2)
        slot = rng.randrange(4)
        start = rng.randrange(64)
        count = rng.randrange(65)
        left = rng.randrange(0, 33)
        top = rng.randrange(0, 25)
        width = rng.randrange(128, 641)
        height = rng.randrange(120, 481)
        rect = (left, top, left + width, top + height)
        mode = rng.choices(("random", "zero", "maximum", "ramp"),
                           weights=(88, 4, 4, 4), k=1)[0]
        case_seed = rng.randrange(1 << 32)
        yield "randomized", _history_case(
            f"random/{seed:08x}/{i}", graph, hilite, slot, start, count,
            rect, case_seed, mode)








