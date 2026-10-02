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

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import behavior as b
from behavior_ledger import CaseLedger

FUNCTION = "win_PrintStyleTextInRect"
CARD_FUNCTION = "DisplayCard"
HISTORY_FUNCTION = "drawHistGraph"
FORMAT_CURSOR_PROOF = "evidence/behavior/runtime/format-cursors/format_cursor_proof.json"
FORMAT_CURSOR_PROOF_SHA256 = "140c1d240cf48c5c868ccdd723b4651d71735f592b3d5baed1f4d552cbfbc628"
SOURCE = ROOT / "build/workers/behavior_text_card/S23.c"
SUITE_BYTES = Path(__file__).read_bytes()
TEXT = (0x1000, 0xA000)
STYLES = (0x3000, 0xA000)
RECT = (0x4000, 0xA000)


def far(off, seg):
    return struct.pack("<HH", off, seg)


def _json_default(value):
    if isinstance(value, bytes):
        return {"bytes_hex": value.hex()}
    raise TypeError(type(value).__name__)


def style_record(pos, face, height=12, ascent=9, font=2, size=12):
    return struct.pack("<I8h", pos & 0xFFFFFFFF, height, ascent, font, face,
                       size, 0, 0, 0)


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
    style_bytes = struct.pack("<H", len(styles)) + b"".join(
        style_record(*s) for s in styles)
    args = [TEXT[0], TEXT[1], *(STYLES if styles else (0, 0)),
            RECT[0], RECT[1], first_line, font1, font2, record]
    writes = [(TEXT[1] * 16 + TEXT[0], text + b"\0"),
              (RECT[1] * 16 + RECT[0], struct.pack("<4h", *rect)),
              # Uninitialized DOS display fallback metrics are explicit host
              # inputs. Original font selection/height/width helpers still run.
              (b.symbol_address("g_3DB2"), struct.pack("<H", 320)),
              (b.symbol_address("g_3DDC"), struct.pack("<b", 12)),
              (b.symbol_address("g_3DDE"), struct.pack("<b", 8))]
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
                  "metrics": "original f_24AB_02AD/030B/0367 and MSC far-string helpers; explicit 12px/8px fallback globals because the DOS font driver is not initialized in the oracle VM"})


def cases(count, seed):
    fixed_texts = [b"", b"A", b"short words wrap here", b"a\tb  c\r\nnext",
                   b"(x), [y]! z? {w}-q.", b"one two three four five six"]
    rects = [(0, 0, 320, 200), (-20, 7, 28, 47), (4, -13, 19, 29),
             (100, 50, 101, 51), (0, 0, 640, 480)]
    stylesets = [(), ((0, 0x100),), ((0, 0), (4, 0x100), (10, 0)),
                 ((0, 0x100), (2, 0), (8, 0x100))]
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
            (rng.randrange(0, length + 1), rng.choice((0, 0x100)))
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


def run_history(out, random_count=2000, seed=0xD15EA5E):
    suite_digest = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()[:12]
    harness_digest = hashlib.sha256(b.HARNESS_SOURCE).hexdigest()[:12]
    out = out / "draw-history" / f"run-{suite_digest}-{harness_digest}"
    out.mkdir(parents=True, exist_ok=True)
    snapshot = out / "text_card_suite_snapshot.py"
    snapshot.write_bytes(Path(__file__).read_bytes())
    source = ROOT / "build/workers/behavior_text_card/S24.c"
    pair = b.PreparedPair(HISTORY_FUNCTION, source=source, out=out)
    ledger = CaseLedger(out / f"cases-{seed:08x}-{random_count}.jsonl.gz", pair,
        ["ordered line segments", "label text and border geometry",
         "history selection/scaling", "all raw nonstack bytes plus approved private formatter views",
         "return value and caller ABI"])
    totals = {"directed": 0, "randomized": 0}
    failures = []
    started = time.monotonic()
    for lane, case in history_cases(random_count, seed):
        try:
            result = pair.compare(case)
        except Exception as exc:
            failures.append({"case": case.metadata, "error": str(exc)})
            break
        totals[lane] += 1
        ledger.record(case, result, lane=lane)
        if not result.equal:
            failures.append({"case": case.metadata, "diff": result.diff})
            break
    source_text = source.read_text(encoding="latin1")
    anchor = "x = n * width / 64 + slot + r.left;"
    if source_text.count(anchor) != 1:
        raise RuntimeError("drawHistGraph negative-control anchor not unique")
    mutant = out / "negative.c"
    mutant.write_text(source_text.replace(anchor,
        "x = n * width / 64 + slot + r.left + 1;", 1), encoding="latin1")
    negative = b.PreparedPair(HISTORY_FUNCTION, source=mutant).compare(
        _history_case("negative/x-coordinate-plus-one", 0, 0, 0, 8, 8,
                      (0, 0, 320, 200), 0x39C7032C))
    label_anchor = 'sprintf(buf, "%d", data[j]);'
    if source_text.count(label_anchor) != 1:
        raise RuntimeError("drawHistGraph label negative-control anchor not unique")
    label_mutant = out / "negative-label.c"
    label_mutant.write_text(source_text.replace(label_anchor,
        'sprintf(buf, "%d", data[j] + 1);', 1), encoding="latin1")
    negative_label = b.PreparedPair(HISTORY_FUNCTION, source=label_mutant).compare(
        _history_case("negative/label-value-plus-one", 0, 1, 0, 0, 8,
                      (0, 0, 320, 200), 0x39C7032C, "ramp"))
    ledger_pin = ledger.finalize()
    report = {"schema": "behavior-suite-run-v1", "function": HISTORY_FUNCTION,
        "identity": pair.identity, "suite_sha256": hashlib.sha256(snapshot.read_bytes()).hexdigest(),
        "case_ledger": ledger_pin, "directed": totals["directed"],
        "randomized": totals["randomized"], "requested_randomized": random_count,
        "seed": seed,
        "mismatches": sum("diff" in f for f in failures),
        "errors": sum("error" in f for f in failures), "failures": failures,
        "negative_control": {"detected": not negative.equal,
            "changed_fields": sorted(negative.diff)},
        "label_negative_control": {"detected": not negative_label.equal,
            "changed_fields": sorted(negative_label.diff)},
        "compared": ["ordered line segments", "label rendering and border geometry",
            "private state and all nonstack writes", "caller ABI"],
        "domain": "graphs 0..3; both highlight paths; sample counts 0..64 and ring-buffer starts 0..63; valid 64-sample zero, maximum, ramp, and seeded 0..120 arrays; positive rectangles up to 640x480",
        "boundaries": "window rect and line/color/text/border raster callbacks; all graph reads/scaling, sprintf, font/string helpers execute in original/candidate code; the reviewed sprintf cursor view retains semantic advancement/count and raw observations",
        "status": "UNRESOLVED pending contract review",
        "elapsed_seconds": round(time.monotonic() - started, 3)}
    (out / "report.json").write_text(json.dumps(report, indent=2, default=_json_default) + "\n")
    if failures or negative.equal or negative_label.equal:
        raise AssertionError(f"drawHistGraph differential failure or negative control missed: {failures}")
    return report


def run(count, seed, out):
    suite_digest = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()[:12]
    harness_digest = hashlib.sha256(b.HARNESS_SOURCE).hexdigest()[:12]
    out = out / f"run-{seed:08x}-{count}-{suite_digest}-{harness_digest}"
    out.mkdir(parents=True, exist_ok=True)
    # Pin the exact suite source before any VM execution; ledger names encode
    # seed/count so exploratory runs remain separately auditable.
    snapshot = out / "text_card_suite_snapshot.py"
    snapshot.write_bytes(Path(__file__).read_bytes())
    pair = b.PreparedPair(FUNCTION, source=SOURCE, out=out)
    ledger = CaseLedger(out / f"cases-{seed:08x}-{count}.jsonl.gz", pair,
        ["ordered draw calls and pointed text", "font helper sequence and metrics",
         "hotspot writes and all nonstack memory", "return value and caller ABI"])
    totals = {"directed": 0, "randomized": 0}
    failures = []
    started = time.monotonic()
    for group, case in cases(count, seed):
        try:
            result = pair.compare(case)
        except Exception as exc:
            failures.append({"case": case.metadata, "error": str(exc)})
            break
        totals[group] += 1
        ledger.record(case, result, lane=group)
        if not result.equal:
            failures.append({"case": case.metadata, "diff": result.diff})
            break
    # A source mutation changes line origin while preserving all fixture inputs.
    source = SOURCE.read_text(encoding="latin1")
    anchor = "x = rect->left + 1;"
    if source.count(anchor) != 1:
        raise RuntimeError("negative-control anchor not unique")
    mutant = out / "negative.c"
    mutant.write_text(source.replace(anchor, "x = rect->left + 2;", 1), encoding="latin1")
    negative = b.PreparedPair(FUNCTION, source=mutant).compare(
        make_case("negative/x-origin-plus-one", b"negative probe", (0, 0, 120, 60)))
    ledger_pin = ledger.finalize()
    report = {"schema": "behavior-suite-run-v1", "function": FUNCTION,
        "identity": pair.identity, "suite_sha256": hashlib.sha256(snapshot.read_bytes()).hexdigest(),
        "case_ledger": ledger_pin,
        **totals, "seed": seed, "mismatches": sum("diff" in x for x in failures),
        "errors": sum("error" in x for x in failures), "failures": failures,
        "negative_control": {"detected": not negative.equal, "diff": negative.diff},
        "compared": ["ordered draw x/y/text", "font helper effects and call order",
            "recorded hotspot arrays and count", "all nonstack writes", "caller ABI"],
        "domain": "directed text/control/punctuation, style-run positions and faces, rectangle sizes/origins, first-line clipping and record mode; deterministic random strings and valid sorted styles; original font selection, line height and character width helpers",
        "boundaries": "only f_24AB_038D raster emission is modeled; projection reads the complete pointed-to NUL-terminated text; font and string helpers execute from the DOS image",
        "status": "UNRESOLVED pending contract review",
        "elapsed_seconds": round(time.monotonic() - started, 3)}
    (out / "report.json").write_text(json.dumps(report, indent=2, default=_json_default) + "\n")
    if failures or negative.equal:
        raise AssertionError(f"differential failure or ineffective negative control: {failures}")
    return report


def run_cards(out, count=500, seed=0x5A23):
    suite_digest = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()[:12]
    harness_digest = hashlib.sha256(b.HARNESS_SOURCE).hexdigest()[:12]
    out = out / "display-card" / f"run-{suite_digest}-{harness_digest}-{seed:08x}-{count}"
    out.mkdir(parents=True, exist_ok=True)
    snapshot = out / "text_card_suite_snapshot.py"
    snapshot.write_bytes(Path(__file__).read_bytes())
    pair = b.PreparedPair(CARD_FUNCTION, source=SOURCE, out=out)
    ledger = CaseLedger(out / f"cases-{seed:08x}-{count}.jsonl.gz", pair,
        ["resource request/lock/size/unlock/purge order",
         "ordered window, bitmap and text draw commands",
         "projected draw text and coordinates", "all nonstack memory", "caller ABI"])
    totals = {"directed": 0, "randomized": 0}
    failures = []
    started = time.monotonic()
    card_cases_for_negative = None
    for group, case in card_cases(count, seed):
        try:
            result = pair.compare(case)
        except Exception as exc:
            failures.append({"case": case.metadata, "error": str(exc)})
            break
        totals[group] += 1
        ledger.record(case, result, lane=group)
        if not result.equal:
            failures.append({"case": case.metadata, "diff": result.diff})
            break
        if case.metadata["scenario"] == "bitmap-link":
            card_cases_for_negative = case
    source = SOURCE.read_text(encoding="latin1")
    anchor = "win_DrawBitMap(pic.left + r.left, pic.top + r.top, pic.id);"
    if source.count(anchor) != 1:
        raise RuntimeError("DisplayCard negative-control anchor not unique")
    mutant = out / "negative.c"
    mutant.write_text(source.replace(anchor,
        "win_DrawBitMap(pic.left + r.left + 1, pic.top + r.top, pic.id);", 1),
        encoding="latin1")
    negative = b.PreparedPair(CARD_FUNCTION, source=mutant).compare(
        card_cases_for_negative or _resource_case("negative/bitmap", "bitmap-link"))
    ledger_pin = ledger.finalize()
    report = {"schema": "behavior-suite-run-v1", "function": CARD_FUNCTION,
        "identity": pair.identity,
        "suite_sha256": hashlib.sha256(snapshot.read_bytes()).hexdigest(),
        "case_ledger": ledger_pin, **totals,
        "mismatches": sum("diff" in f for f in failures),
        "errors": sum("error" in f for f in failures), "failures": failures,
        "negative_control": {"detected": not negative.equal,
            "changed_fields": sorted(negative.diff),
            "oracle_bitmaps": negative.original["state"].get("bitmaps", []),
            "candidate_bitmaps": negative.candidate["state"].get("bitmaps", [])},
        "compared": ["resource lifecycle calls", "bitmap/text draw call order and values",
            "card parser writes", "all nonstack memory", "caller ABI"],
        "seed": seed, "requested_randomized": count,
        "domain": "missing card resource; valid unknown-record card; one bitmap with one hotspot; one plain text frame; one styled CHITIN text frame; seeded valid card streams of 1..8 P/T records, 0..6 in-range hotspot links per P record, 1..4 text frames, 1..4 sorted style runs, text resources, variable positive rectangles, fixed valid window geometry, and explicit font fallback metrics",
        "boundaries": "resource lookup and handle lock/size/unlock, window rectangle/clipping/color, bitmap raster and text raster are deterministic host services; all resource bytes, card parsing, transforms, text cleanup, style conversion and line layout execute in the DOS VM",
        "status": "UNRESOLVED pending contract review",
        "elapsed_seconds": round(time.monotonic() - started, 3)}
    (out / "report.json").write_text(json.dumps(report, indent=2, default=_json_default) + "\n")
    if failures or negative.equal:
        raise AssertionError(f"DisplayCard differential failure or negative control missed: {failures}")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=1000)
    parser.add_argument("--history-count", type=int, default=2000)
    parser.add_argument("--seed", type=lambda s: int(s, 0), default=0x39C70092)
    parser.add_argument("--out", type=Path, default=ROOT / "build/workers/behavior_text_card/text")
    parser.add_argument("--target", choices=("text", "card", "history", "all"), default="text")
    args = parser.parse_args()
    results = {}
    if args.target in ("text", "all"):
        results["text"] = run(args.count, args.seed, args.out)
    if args.target in ("card", "all"):
        results["card"] = run_cards(args.out, args.count, args.seed ^ 0x5A23)
    if args.target in ("history", "all"):
        results["history"] = run_history(args.out, random_count=args.history_count,
                                         seed=args.seed)
    print(json.dumps(results, indent=2, default=_json_default))
