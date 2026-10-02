"""Differential fixtures for tutorial completion and DOS menu interaction.

The source remains the catalog's whole-module hard-tail seed. Cases initialize
the tutorial globals or valid far menu/string tables, execute the original DOS
helpers by default, and replace only host-facing input/presentation boundaries.
"""
from __future__ import annotations

import argparse
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

SUITE = "tutorial_menu_v1"
DG = b.match.DGROUP_SEG
DATA_SEG = 0xA000
SEL_OFF = 0x0800
ITEMS_OFF = 0x1000
STRINGS_OFF = 0x2000
SAVE_OFF = 0x7000
MENU_BUFFER_OFF = 0x8000
FORMAT_CURSOR_PROOF = "evidence/behavior/runtime/format-cursors/format_cursor_proof.json"
FORMAT_CURSOR_PROOF_SHA256 = "140c1d240cf48c5c868ccdd723b4651d71735f592b3d5baed1f4d552cbfbc628"
MENU_FORMAT_CURSOR_VIEWS = [
    b.FormatCursorView("sprintf-output-stream", DG * 16 + 0x8E06,
                       FORMAT_CURSOR_PROOF, FORMAT_CURSOR_PROOF_SHA256),
    b.FormatCursorView("vsprintf-output-stream", DG * 16 + 0x8E12,
                       FORMAT_CURSOR_PROOF, FORMAT_CURSOR_PROOF_SHA256),
]


def w(*values):
    return struct.pack("<" + "H" * len(values), *(v & 0xFFFF for v in values))


def far(off, seg=DATA_SEG):
    return w(off, seg)


def lin(off, seg=DATA_SEG):
    return seg * 16 + off


def addr(name):
    return b.symbol_address(name)


def _long(v):
    return struct.pack("<I", v & 0xFFFFFFFF)


def _jsonable(value):
    """Keep failure details serializable without losing byte-valued fixture data."""
    if isinstance(value, bytes): return {"bytes_hex": value.hex()}
    if isinstance(value, tuple): return [_jsonable(v) for v in value]
    if isinstance(value, list): return [_jsonable(v) for v in value]
    if isinstance(value, dict): return {str(k): _jsonable(v) for k,v in value.items()}
    return value


def _diff_summary(diff):
    summary={"fields":list(diff)}
    for key in ("return","ranges","state","io","preserved_registers","nonstack_memory"):
        if key in diff: summary[key]=_jsonable(diff[key])
    if "trace" in diff:
        oracle,candidate=diff["trace"]["oracle"],diff["trace"]["candidate"]
        entries=[]
        for i,(left,right) in enumerate(zip(oracle,candidate)):
            changed=[k for k in left if left[k]!=right.get(k)]
            if changed: entries.append({"index":i,"oracle_call":left.get("name"),
                "candidate_call":right.get("name"),"changed_fields":changed,
                "args":{"oracle":left.get("args"),"candidate":right.get("args")}
                if "args" in changed else None})
        summary["trace"]={"oracle_count":len(oracle),"candidate_count":len(candidate),
                           "differing_entries":entries[:20]}
    return summary


def tutorial_case(label, lesson, values, queries):
    """State uses named world facts; modeled game-query helpers are explicit."""
    names = {
        "MePlane": 2, "MeLocX": 2, "MeLocY": 2, "fd_50F6_0224": 2,
        "fd_50F6_0204": 2, "fd_50F6_0AA0": 2, "fd_50F6_0B1E": 2,
        "fd_50F6_1074": 2, "fd_50F6_104E": 2, "fd_50F6_04C2": 2,
        "fd_50F6_032E": 2, "fd_50F6_035C": 2,
        "fd_3D57_07BE": 2, "fd_50F6_0FB6": 2, "fd_50F6_0FFA": 2,
    }
    writes = [(addr(name), w(values.get(name, 0))) for name in names]
    writes += [(addr("fd_50F6_0508"), w(values.get("pt_y", 0), values.get("pt_x", 0))),
               (addr("modeLevels"), w(*values.get("modeLevels", (0, 0, 0)))),
               (addr("fd_50F6_0B12"), bytes(values.get("b12", bytes(12)))),
               (addr("MapA"), bytes(values.get("map", bytes(64 * 32))))]
    observe = [b.Range(name, addr(name), size) for name, size in names.items()]
    observe += [b.Range("lesson_point", addr("fd_50F6_0508"), 4),
                b.Range("mode_levels", addr("modeLevels"), 6),
                b.Range("tutorial_array", addr("fd_50F6_0B12"), 12),
                b.Range("tutorial_map", addr("MapA"), 64 * 32)]
    return b.Case(label=label, args=[lesson & 0xFFFF], writes=writes, observe=observe,
        callbacks={
            # These are world queries, not implementations of LessonDone: their
            # values and call order are part of the explicit case contract.
            "f_00F8_02BE": b.Callback(0, lambda m, a: tuple(m.state["clock"]),
                project=lambda m, a: {"world_fact": "simulation_clock"}),
            "f_22BF_0A22": b.Callback(1, lambda m, a: int(bool(m.state["completed"].get(a[0], False))),
                project=lambda m, a: {"objective": a[0]}),
            # SetAlarmDropState remains original. These two downstream effects
            # are the Win16 UI selection/invalidation sinks used by that helper.
            "win_SetObjSelectedState": b.Callback(0,
                lambda m,a:m.state["host_trace"].append(["object-selection",list(a)]),
                register_args=("ax","dx")),
            "InvalEuMap": b.Callback(4,
                lambda m,a:m.state["host_trace"].append(["invalidate-map",list(a)])),
        }, return_kind="s16", state={"clock": list(queries.get("clock", (0, 0))),
                                      "completed": dict(queries.get("completed", {})),
                                      "host_trace": []},
        metadata={"suite": SUITE, "contract": "LessonDone return, world-query order/arguments, and all touched tutorial state",
                  "abi": "fastcall AX=lesson; far return, no stack arguments",
                  "validity": "signed 16-bit lesson ids; initialized tutorial globals, map table, and point fields",
                  "modeled_boundary": "f_00F8_02BE supplies a deterministic 32-bit simulation clock; f_22BF_0A22 supplies deterministic completion flags keyed by objective; the original SetAlarmDropState executes with only win_SetObjSelectedState and InvalEuMap recorded at their Win16 UI boundaries; all other semantic helpers execute original DOS code",
                  "world": values, "queries": queries})


def tutorial_cases(random_count=600, seed=0x0E2E065E):
    out = []
    # Every switch case, neighboring unknown values, and values beyond the
    # recovered switch domain. Keep base state just below most thresholds.
    for lesson in list(range(-2, 60)) + [0x7FFF, -0x8000]:
        vals = {"MePlane": 1, "MeLocX": 4, "MeLocY": 5,
                "fd_50F6_0224": 9, "fd_50F6_0204": 10,
                "fd_50F6_1074": 9, "pt_y": 4, "pt_x": 5,
                "modeLevels": (3, 6, 0), "b12": w(0, 0, 0, 0, 0, 2)}
        mapdata = bytearray(64 * 32); mapdata[4 * 32 + 5] = 0x48; vals["map"] = bytes(mapdata)
        out.append(tutorial_case(f"directed/{lesson}", lesson, vals,
            {"clock": (11, 0), "completed": {0x100: True, 0x1200: False, 0x1300: True, 0: True}}))
        # Flip each condition-driving fact to exercise the opposite edge.
        for field, choices in (("MePlane", (0, 1, 2, 3)),
                               ("fd_50F6_0224", (9, 10, 11)),
                               ("fd_50F6_0204", (9, 10, 11)),
                               ("fd_50F6_0AA0", (0, 1)),
                               ("fd_50F6_0B1E", (0, 1)),
                               ("fd_50F6_1074", (8, 9, 10)),
                               ("fd_50F6_104E", (0, 1)),
                               ("fd_50F6_04C2", (0x10, 0x18, 0x28)),
                               ("fd_50F6_032E", (0, 1)),
                               ("fd_50F6_035C", (0, 1))):
            for value in choices:
                v = dict(vals); v[field] = value
                out.append(tutorial_case(f"grid/{lesson}/{field}/{value}", lesson, v,
                    {"clock": (10, 0), "completed": {0x100: value & 1, 0x1200: value & 1,
                                                        0x1300: value & 1, 0: value & 1}}))
    rng = random.Random(seed)
    for i in range(random_count):
        mapdata = bytearray(rng.randrange(256) for _ in range(64 * 32))
        vals = {"MePlane": rng.randrange(-2, 5), "MeLocX": rng.randrange(64),
                "MeLocY": rng.randrange(32), "fd_50F6_0224": rng.randrange(-50, 101),
                "fd_50F6_0204": rng.randrange(-50, 101), "fd_50F6_0AA0": rng.randrange(2),
                "fd_50F6_0B1E": rng.randrange(2), "fd_50F6_1074": rng.randrange(-100, 201),
                "fd_50F6_104E": rng.randrange(2), "fd_50F6_04C2": rng.randrange(64),
                "fd_50F6_032E": rng.randrange(2), "fd_50F6_035C": rng.randrange(2),
                "pt_y": rng.randrange(-100, 101), "pt_x": rng.randrange(-100, 101),
                "modeLevels": tuple(rng.randrange(-20, 21) for _ in range(3)),
                "b12": bytes(rng.randrange(256) for _ in range(12)), "map": bytes(mapdata)}
        out.append(tutorial_case(f"random/{seed:08x}/{i}", rng.randrange(-4, 64), vals,
            {"clock": (rng.randrange(65536), rng.randrange(65536)),
             "completed": {k: bool(rng.randrange(2)) for k in (0, 0x100, 0x1200, 0x1300)}}))
    return out


def _str_read(m, off, seg, limit=512):
    data = bytearray()
    for i in range(limit):
        c = m.read(seg * 16 + off + i, 1)[0]
        if not c: return bytes(data)
        data.append(c)
    raise b.ExecutionError("unterminated menu string")


def _rect(m, off, seg):
    return list(struct.unpack("<4h", m.read(seg * 16 + off, 8)))


def _menu_callbacks():
    def alloc(machine, args):
        size=args[0]
        if size != 4000: raise b.ExecutionError(f"unexpected menu allocation size {size}")
        machine.write(lin(MENU_BUFFER_OFF),bytes(size))
        machine.state["host_trace"].append(["menu-buffer-allocate",size,MENU_BUFFER_OFF,DATA_SEG])
        return MENU_BUFFER_OFF,DATA_SEG

    def release(machine, args):
        off,seg=args
        machine.state["host_trace"].append(["menu-buffer-release",off,seg])

    def tick_count(machine, args):
        # TickCount is backed by the asynchronous timer ISR. Advance one
        # deterministic timer tick per call so original delay/wait helpers can
        # execute without an interrupt scheduler in the VM.
        value=(machine.state.get("ticks",0)+1)&0xFFFFFFFF
        machine.state["ticks"]=value
        machine.state["host_trace"].append(["timer-tick",value])
        return value & 0xFFFF, value >> 16

    def delay_ticks(machine, args):
        ticks=args[0]
        if ticks < 0: raise b.ExecutionError(f"negative DOS delay request: {ticks}")
        machine.state["ticks"]=(machine.state.get("ticks",0)+ticks)&0xFFFFFFFF
        machine.state["host_trace"].append(["delay-ticks",ticks,machine.state["ticks"]])

    def point(machine, args):
        off, seg = args
        pt = machine.state["points"].pop(0) if machine.state["points"] else (0, 0)
        machine.write(seg * 16 + off, w(*pt))
        machine.state["host_trace"].append(["mouse-point", list(pt)])

    def still_down(machine, args):
        q = machine.state["down"]
        value = q.pop(0) if q else False
        machine.state["host_trace"].append(["button-state", bool(value)])
        return int(bool(value))

    def key_ready(machine, args):
        return int(bool(machine.state["keys"]))

    def key_read(machine, args):
        value = machine.state["keys"].pop(0)
        machine.state["host_trace"].append(["key-read", value])
        return value

    def event_ready(machine, args):
        return int(bool(machine.state["events"]))

    def event_read(machine, args):
        off, seg = args
        ev = machine.state["events"].pop(0)
        if len(ev) != 8:
            raise b.ExecutionError("DOS Event provider requires all eight recovered words")
        machine.write(seg * 16 + off, w(*ev))
        machine.state["host_trace"].append(["event-read", list(ev)])

    def draw_text(machine, args):
        x, y, attr, off, seg = args
        s = _str_read(machine, off, seg)
        machine.state["host_trace"].append(["draw-text", x, y, attr, s.hex()])

    def draw_font_text(machine,args):
        x,y,off,seg=args
        s=_str_read(machine,off,seg)
        machine.state["host_trace"].append(["font-draw-text",x,y,s.hex()])

    def draw_mode(machine, args):
        machine.state["host_trace"].append(["draw-mode", args[0]])

    def save_rect(machine, args):
        off, seg = args
        rect = _rect(machine, off, seg)
        machine.state["host_trace"].append(["save-screen-rect", rect])
        return (SAVE_OFF, DATA_SEG)

    def restore_rect(machine, args):
        roff, rseg, boff, bseg = args
        machine.state["host_trace"].append(["restore-screen-rect", _rect(machine, roff, rseg), boff, bseg])

    def warp(machine, args):
        machine.state["host_trace"].append(["warp-pointer", args[0], args[1]])

    def dispatch(machine, args):
        machine.state["host_trace"].append(["dispatch-event", list(args)])

    def key_flush(machine, args):
        machine.state["host_trace"].append(["flush-key", args[0]])

    def cleanup(machine, args):
        machine.state["host_trace"].append(["input-cleanup", "f_1FD2_031A"])

    def cursor_cleanup(machine, args):
        machine.state["host_trace"].append(["cursor-cleanup", "f_1B73_0A6C"])

    def mouse_setup(machine, args):
        # Original implementation queries INT 33h and initializes the DOS
        # mouse-driver cursor state. The fixture's mouse provider owns those
        # coordinates/buttons, so this records the host setup boundary.
        machine.state["host_trace"].append(["mouse-setup"])

    return {
        "malloc": b.Callback(1, alloc), "free": b.Callback(2, release),
        "f_1B73_0504": b.Callback(0, tick_count),
        "f_1F80_0081": b.Callback(1, delay_ticks), "f_1B73_0A40": b.Callback(0, mouse_setup),
        "f_1FD2_04D0": b.Callback(2, point, project=lambda m,a:{"destination":"logical-point"}),
        "f_1FD2_0542": b.Callback(0, still_down),
        "f_1F58_0038": b.Callback(0, key_ready), "f_1F58_0090": b.Callback(0, key_read),
        "f_1B73_032A": b.Callback(0, event_ready),
        "f_1B73_032E": b.Callback(2, event_read, project=lambda m,a:{"destination":"logical-event"}),
        "f_1FBD_0000": b.Callback(4,draw_font_text,project=lambda m,a:{"x":a[0],"y":a[1],
            "text":_str_read(m,a[2],a[3]).hex()}),
        "f_1FD2_02B1": b.Callback(1, draw_mode), "f_1FD2_02FF": b.Callback(0),
        "GSaveRect": b.Callback(2, save_rect, project=lambda m,a:{"rect":_rect(m,a[0],a[1])}),
        "f_1CE2_056C": b.Callback(4, restore_rect,
            project=lambda m,a:{"rect":_rect(m,a[0],a[1]),"surface":"saved-menu-rectangle"}),
        "f_1B73_09E9": b.Callback(2, warp), "f_1B73_030F": b.Callback(5, dispatch),
        "f_1F58_007F": b.Callback(1, key_flush), "f_1B73_0A6C": b.Callback(0, cursor_cleanup),
        "f_1FD2_031A": b.Callback(0, cleanup),
    }


def menu_case(label, keys, *, curmenu=-1, events=(), points=(), down=(), items=None,
              selected=1, width=640, height=400, line_height=12, char_width=8):
    """Build one valid far menu table; malloc/free and geometry helpers stay original."""
    if items is None: items = [b" Alpha", b" Beta", b" Gamma"]
    enc = []
    for item in items: enc.append(item + b"\0")
    table = bytearray()
    strings = bytearray()
    for i, s in enumerate(enc):
        off = STRINGS_OFF + len(strings)
        table += far(off)
        strings += s
    table += bytes(4)
    # Prime the real Ralloc heap for the original game's malloc(4000). The
    # routine remains original; this is the documented valid DOS heap state.
    old_stack_segment=b.STACK_SEG
    from behavior_suites import memory as memory_suite
    # memory.py configures its standalone allocator suite's private DS stack on
    # import; restore this task's historical CRT SS convention immediately.
    b.STACK_SEG=old_stack_segment
    old_paras=memory_suite.HEAP_PARAS
    old_dg=memory_suite.DG
    memory_suite.HEAP_PARAS=0x500
    memory_suite.DG=b.match.DGROUP_SEG
    try:
        heap=memory_suite.heap_case(label+"/heap",[(0x400,0x80)],contract="one valid free DOS Ralloc block for original malloc/free")
    finally:
        memory_suite.HEAP_PARAS=old_paras
        memory_suite.DG=old_dg
    writes = list(heap.writes) + [(lin(ITEMS_OFF), bytes(table)), (lin(STRINGS_OFF), bytes(strings)),
              (lin(SEL_OFF), bytes([selected & 255])),
              (addr("g_5AAC"), far(0x0300)),
              (DG * 16 + 0x608A, w(curmenu)),
              (DG * 16 + 0x3DDC, bytes([line_height & 255])),
              (DG * 16 + 0x3DDE, bytes([char_width & 255])),
              (addr("fd_55B3_5AA0"), w(width, height)),
              (addr("fd_50F6_46BC"), w(*([max(12, len(items) + 1)] * 100))),
              (addr("fd_50F6_46A8"), w(*[30 + 4 * i for i in range(100)])),
              (addr("fd_55B3_604C"), w(4))]
    observe = [b.Range("selection", lin(SEL_OFF), 1), b.Range("menu_saved_surface", addr("g_5AAC"), 4),
               b.Range("curMenu", DG * 16 + 0x608A, 2)]
    return b.Case(label=label,args=[SEL_OFF,DATA_SEG,ITEMS_OFF,DATA_SEG],writes=writes,observe=observe,
        callbacks=_menu_callbacks(),return_kind="s16",callee_pop=0,
        format_cursor_views=list(MENU_FORMAT_CURSOR_VIEWS),
        state={"keys":list(keys),"events":list(events),"points":list(points),"down":list(down),"host_trace":[],"ticks":0},
        metadata={"suite":SUITE,"contract":"menu return and selected byte, ordered input/draw/event commands and rectangle/string values, menu surface state, allocator effects, caller ABI",
            "abi":"far C routine: stack far char* selection, stack far far* items; caller cleanup 8 bytes",
            "validity":{"item_table":items,"sentinel":"null far pointer","initial_selection":selected,
                "current_menu":curmenu,"screen":[width,height],"line_height":line_height,"char_width":char_width},
            "modeled_boundary":"Host keyboard/mouse/event providers, display save/draw/restore/cursor commands, DOS mouse setup (INT 33h query), asynchronous TickCount, DOS f_1F80_0081 delay ticks, and one successful 4000-byte menu-buffer allocation are deterministic providers. f_1F80_0081 advances the deterministic timer by exactly its positive tick argument; TickCount advances one tick per call so original delay helpers run. The allocator returns a zeroed bounded scratch buffer and verifies the matching release. Original sprintf and f_1FD2_0008/vsprintf formatters execute; f_1FBD_0000 is projected as a C string at the actual renderer sink. Both runtime-proved cursor views retain cursor advancement and remaining capacity while abstracting only invocation-stack pointer homes; if a stream record points to the modeled menu heap, the record remains raw. Raw writes and traces remain in the evidence ledger. Sink projections, per-call snapshots, final globals, all final nonstack writes, strings, rectangles, and input consumption remain compared. Original rectangle adjustment/containment, strings, formatter, and all other semantic helpers run in DOS code.",
            "input":{"keys":list(keys),"events":list(events),"points":list(points),"down":list(down)}})


def menu_cases(random_count=80, seed=0x35F50384):
    cases=[]
    endings=(10,13,27,32,0x852,0x853)
    for curmenu in (-1,0,1):
        for end in endings:
            cases.append(menu_case(f"directed/menu{curmenu}/end{end:04x}",[end],curmenu=curmenu))
        for key in (ord('+'),ord('-'),0x850,0x848,ord('A'),ord('B'),ord('Z'),0x801):
            cases.append(menu_case(f"directed/menu{curmenu}/key{key:04x}",[key,13],curmenu=curmenu))
        cases.append(menu_case(f"directed/menu{curmenu}/separator-skip",[ord('+'),13],curmenu=curmenu,
                               items=[b" Alpha",b" -",b" Beta"]))
        cases.append(menu_case(f"directed/menu{curmenu}/disabled-skip",[ord('+'),13],curmenu=curmenu,
                               items=[b" Alpha",bytes([0x80])+b"Beta",b" Gamma"]))
    # S10 consumes the complete Event and forwards it only when the high code
    # byte is 0xFE and its low byte names a different current menu. Same-menu
    # and other event classes are ignored, so give those cases a following Enter.
    cases += [menu_case("none/empty",[13],items=[]),
              menu_case("event/other-menu",[],curmenu=0,
                  events=[(1,0x1234,0x2345,0x3456,11,12,0xFE01,13)]),
              menu_case("event/same-menu",[13],curmenu=1,
                  events=[(2,0x2234,0x3345,0x4456,21,22,0xFE01,23)]),
              menu_case("event/non-menu",[13],curmenu=0,
                  events=[(3,0x3234,0x4345,0x5456,31,32,0xFD00,33)]),
              menu_case("mouse-select",[],curmenu=0,points=[(0,0),(42,30)],down=[False,True,False])]
    rng=random.Random(seed)
    for i in range(random_count):
        n=rng.randrange(1,8)
        labels=[]
        for j in range(n):
            if rng.randrange(7)==0: labels.append(b" -")
            elif rng.randrange(6)==0: labels.append(bytes([0x80])+f"Item{j}".encode())
            else: labels.append((" "+chr(65+j)+"item"+str(i%17)).encode())
        cases.append(menu_case(f"random/{seed:08x}/{i}",[rng.choice(endings)],curmenu=rng.choice((-1,0,1,2,3)),
            items=labels,selected=rng.randrange(n+1),width=rng.choice((320,640,800)),
            height=rng.choice((200,400,600)),line_height=rng.randrange(8,20),char_width=rng.randrange(6,13)))
    return cases


def question_case(label, message, set_id, keys=(), events=(), flush_keys=(), line_height=12,
                  char_width=8, screen=(640,400)):
    if not 0 <= set_id <= 2: raise ValueError("question set must select Yes/No, Yes/No/Cancel, or Retry/Cancel")
    msg_off=0x3000
    data=bytes(message)+b"\0"
    writes=[(lin(msg_off),data),(addr("g_3DDC"),bytes([line_height&255])),
            (addr("g_3DDE"),bytes([char_width&255])),
            (addr("fd_55B3_5AA0"),w(*screen))]
    attr=b.symbol("f_1C62_0737")
    writes.append((addr("g_9128"),far(attr["off"],attr["seg"])))
    # Keep the original dialog's private labels and button tables in the
    # compiler object / oracle image; only the public input message is supplied.
    callbacks=_menu_callbacks()
    def flush_or_attribute(machine,args):
        if machine.state.get("dialog_attribute_pending",True):
            machine.state["dialog_attribute_pending"]=False
            for key in machine.state["flush_keys"]:
                machine.state["host_trace"].append(["discard-pending-key",key])
            machine.state["flush_keys"].clear()
        else:
            machine.state["host_trace"].append(["dialog-attribute",list(args)])
    callbacks["f_1C62_0737"]=b.Callback(3,flush_or_attribute)
    return b.Case(label=label,args=[msg_off,DATA_SEG,set_id],writes=writes,
        observe=[b.Range("question_message",lin(msg_off),len(data))],callbacks=callbacks,
        return_kind="s16",callee_pop=0,
        state={"keys":list(keys),"events":list(events),"points":[],"down":[],"host_trace":[],
               "ticks":0,"flush_keys":list(flush_keys),"dialog_attribute_pending":True},
        metadata={"suite":SUITE,"contract":"question dialog selected code, ordered button/message drawing commands, input consumption and full forwarded events",
            "abi":"far C: stack far message pointer then stack set id; far return without callee pop",
            "validity":{"set":set_id,"choices":(("Yes","No"),("Yes","No","Cancel"),("Retry","Cancel"))[set_id],
                "message_bytes":bytes(message).hex(),"driver_metrics":{"line_height":line_height,"character_width":char_width},
                "screen":list(screen)},
            "modeled_boundary":"Same explicit host keyboard/mouse/display/timer, positive f_1F80_0081 delay-tick, and menu-buffer contracts as the S10 menu. f_1C62_0737 consumes only the supplied pending-key prefix on direct entry; the fixture points g_9128 at that callback as a deterministic three-word DOS video attribute setter. Private choice tables, ctype, string/font measurements, original rectangle sizing/clipping and original menu/event dispatch execute from the original DOS image.",
            "input":{"keys":list(keys),"events":list(events),"pending_keys":list(flush_keys)}})


def question_cases(random_count=80,seed=0x1C620415):
    out=[]
    recognized={0:((13,ord('Y'),ord('y')),(27,ord('N'),ord('n'))),
                # The No label starts with NUL in the original table, but the
                # input loop explicitly requires c > 0 before matching labels.
                1:((13,ord('Y'),ord('y')),(ord('N'),ord('n')),(27,ord('C'),ord('c'))),
                2:((27,ord('R'),ord('r')),(27,ord('C'),ord('c')))}
    for set_id,options in recognized.items():
        for index,keys in enumerate(options):
            for key in keys:
                out.append(question_case(f"directed/set{set_id}/choice{index}/key{key:04x}",
                    b"Question?",set_id,[key]))
        for event in (0x0900,0x0901,0x0902,0x09ff):
            out.append(question_case(f"directed/set{set_id}/event{event:04x}",
                b"Continue?",set_id,keys=[ord('X')],
                events=[(1,0x1234,0x2345,0x3456,11,12,event,13)]))
        for key in (ord('X'),ord('7'),0x800+ord('Z'),0):
            out.append(question_case(f"directed/set{set_id}/ignored{key:04x}",
                b"Retry operation?",set_id,[key,options[0][0]],
                events=[(1,0x1234,0x2345,0x3456,11,12,0x0900,13)],flush_keys=[0x123]))
        for tag,message,metrics in (
            ("empty",b"",{}),
            ("two-lines",b"First line\nSecond line",{}),
            ("leading-newline",b"\nLeading line",{}),
            ("clipped-wide",b"W"*80,{"screen":(320,200),"char_width":12,"line_height":12}),
        ):
            out.append(question_case(f"directed/set{set_id}/message-{tag}",message,set_id,
                [options[0][0]],**metrics))
    rng=random.Random(seed)
    for i in range(random_count):
        set_id=rng.randrange(3)
        screen=rng.choice((320,640,800)),rng.choice((200,400,600))
        cw=rng.randrange(6,13)
        max_chars=max(1,min(48,(screen[0]-80)//cw))
        msg=bytes(rng.choice(b"ABCDEFGHIJKLMNOPQRSTUVWXYZ abcdefghijklmnopqrstuvwxyz0123456789.,?!")
                  for _ in range(rng.randrange(1,max_chars+1)))
        choose=rng.choice(recognized[set_id])
        key=rng.choice(choose)
        if rng.randrange(3)==0:
            key=rng.choice((ord('Q'),ord('8'),ord('X')))
            events=[(1,rng.randrange(65536),rng.randrange(65536),rng.randrange(65536),
                     rng.randrange(65536),rng.randrange(65536),0x0900+rng.randrange(4),rng.randrange(65536))]
            # Exercise the actual event path: the ignored key falls through,
            # then a recognized 0x09xx event terminates the original dialog.
            keys=[key]
        else: events=[]; keys=[key]
        out.append(question_case(f"random/{seed:08x}/{i}",msg,set_id,keys,events,
             flush_keys=[rng.randrange(256) for _ in range(rng.randrange(4))],
             line_height=rng.randrange(8,20),char_width=cw,screen=screen))
    return out


def _run_target(target, cases, out):
    pair=b.PreparedPair(target,out=out/target)
    failures=[]; errors=[]; start=time.monotonic()
    ledger=CaseLedger(out/(target+".jsonl.gz"),pair,["return","ordered host/helper calls","ordered input consumption",
        "pointed rectangles and strings","global and pointed writes","all nonstack writes","caller ABI"])
    for i,c in enumerate(cases):
        try: cmp=pair.compare(c)
        except Exception as exc:
            errors.append({"index":i,"label":c.label,"case":_jsonable(c.metadata),"error":str(exc)}); continue
        ledger.record(c,cmp,lane="randomized" if c.label.startswith("random/") else "directed")
        if not cmp.equal:
            failures.append({"index":i,"label":c.label,"case":_jsonable(c.metadata),
                             "diff":_diff_summary(cmp.diff)})
    ledger_pin=ledger.finalize()
    return {"target":target,"identity":pair.identity,"candidate_strict":pair.strict.get("claims",{}).get(target,{}),
        "cases_generated":len(cases),"cases_attempted":len(cases),
        "completed_comparisons":ledger_pin["row_count"],"execution_error_count":len(errors),
        "mismatches":len(failures),"execution_errors":errors,"failures":failures,
        "ledger":ledger_pin,"elapsed_seconds":round(time.monotonic()-start,3),
        "behavioral_status":"UNRESOLVED pending contract review"}


def negative_controls(out):
    results=[]
    src=(ROOT/"work/takeover/hardtail/seeds/root_0E2E_c611660dde4d.c").read_text(encoding="latin1")
    old="if (fd_50F6_0224 > fd_50F6_0204 && fd_50F6_0AA0 == 0)"
    if src.count(old)!=2: raise RuntimeError("LessonDone negative anchor changed")
    mutant=out/"negative"/"lesson-wrong-threshold.c"; mutant.parent.mkdir(parents=True,exist_ok=True)
    mutant.write_text(src.replace(old,"if (fd_50F6_0224 >= fd_50F6_0204 && fd_50F6_0AA0 == 0)",1),encoding="latin1")
    vals={"fd_50F6_0224":10,"fd_50F6_0204":10,"fd_50F6_0AA0":0}
    case=tutorial_case("negative/equal-threshold",3,vals,{"clock":(0,0),"completed":{}})
    baseline=b.PreparedPair("LessonDone",out=out/"negative"/"baseline-lesson")
    base_cmp=baseline.compare(case)
    p=b.PreparedPair("LessonDone",source=mutant,out=out/"negative"/"lesson")
    cmp=p.compare(case)
    results.append({"id":"lesson-strict-threshold","target":"LessonDone","mutation":"strict > changed to >= for lesson 3",
        "baseline_matches":base_cmp.equal,"detected":base_cmp.equal and not cmp.equal,"mutant_differs":not cmp.equal,
        "baseline_diff":base_cmp.diff,"diff":cmp.diff,"mutant_source":str(mutant),"mutant_identity":p.identity})
    src=(ROOT/"work/takeover/hardtail/seeds/S10_35F5_4b9dda15dbea.c").read_text(encoding="latin1")
    old="k = (k + 1) % nItems;"
    if src.count(old)!=1: raise RuntimeError("menu negative anchor changed")
    mutant=out/"negative"/"menu-wrong-next.c"
    mutant.write_text(src.replace(old,"k = (k + 2) % nItems;",1),encoding="latin1")
    case=menu_case("negative/next-skips-item",[ord('+'),13],curmenu=0)
    baseline=b.PreparedPair("o10_35F5_0384",out=out/"negative"/"baseline-menu")
    base_cmp=baseline.compare(case)
    p=b.PreparedPair("o10_35F5_0384",source=mutant,out=out/"negative"/"menu")
    cmp=p.compare(case)
    results.append({"id":"menu-next-option","target":"o10_35F5_0384","mutation":"next option advances by two",
        "baseline_matches":base_cmp.equal,"detected":base_cmp.equal and not cmp.equal,"mutant_differs":not cmp.equal,
        "baseline_diff":base_cmp.diff,"diff":cmp.diff,"mutant_source":str(mutant),"mutant_identity":p.identity})
    src=(ROOT/"work/takeover/hardtail/seeds/root_1C62_1a75da44054b.c").read_text(encoding="latin1")
    old="labels[i][0] == c || labels[i][1] == c"
    if src.count(old)!=1: raise RuntimeError("question negative anchor changed")
    mutant=out/"negative"/"question-wrong-hotkey.c"
    mutant.write_text(src.replace(old,"labels[i][0] == c",1),encoding="latin1")
    case=question_case("negative/second-byte-hotkey",b"Question?",0,[ord('Y')],
                       events=[(1,0x1234,0x2345,0x3456,11,12,0x0901,13)])
    baseline=b.PreparedPair("f_1C62_0415",out=out/"negative"/"baseline-question")
    base_cmp=baseline.compare(case)
    p=b.PreparedPair("f_1C62_0415",source=mutant,out=out/"negative"/"question")
    cmp=p.compare(case)
    results.append({"id":"question-second-byte-hotkey","target":"f_1C62_0415","mutation":"hotkey second-byte match removed",
        "baseline_matches":base_cmp.equal,"detected":base_cmp.equal and not cmp.equal,"mutant_differs":not cmp.equal,
        "baseline_diff":base_cmp.diff,"diff":cmp.diff,"mutant_source":str(mutant),"mutant_identity":p.identity})
    if any(not x["detected"] for x in results): raise AssertionError("source mutant escaped its contract or baseline")
    return results


def run(count=80,seed=0x35F50384,out=ROOT/"build/workers/behavior_tutorial_menu",negative=True):
    out.mkdir(parents=True,exist_ok=True)
    started=time.monotonic()
    reports=[_run_target("LessonDone",tutorial_cases(count*5,seed^0x0E2E065E),out),
             _run_target("o10_35F5_0384",menu_cases(count,seed),out),
             _run_target("f_1C62_0415",question_cases(count,seed^0x1C620415),out)]
    negatives=negative_controls(out) if negative else []
    report={"schema":"behavior-suite-run-v1","suite":SUITE,"suite_sha256":b.digest(Path(__file__).read_bytes()),
        "targets":reports,"negative_controls":negatives,"seed":seed,
        "elapsed_seconds":round(time.monotonic()-started,3),
        "scope":"Directed LessonDone switch and threshold partitions plus fixed-seed signed/unsigned world states; valid far-menu keyboard, separator/disabled-item, selected-menu, event, mouse, geometry and dimension partitions plus fixed-seed valid item tables.",
        "limits":"Finite bounded domains only. Tutorial world-query helpers and host input/presentation boundary contracts are modeled explicitly; other helpers execute original DOS code. Menu suite does not claim arbitrary RTLink, window manager or display-driver behavior.",
        "status":"UNRESOLVED pending independent review of fixture validity and boundary contracts"}
    (out/"report.json").write_text(json.dumps(report,indent=2)+"\n")
    if any(r["mismatches"] or r["execution_errors"] for r in reports): raise AssertionError(json.dumps(reports,indent=2))
    return report


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--count",type=int,default=80)
    p.add_argument("--seed",type=lambda s:int(s,0),default=0x35F50384)
    p.add_argument("--out",type=Path,default=ROOT/"build/workers/behavior_tutorial_menu")
    p.add_argument("--no-negative-controls",action="store_true")
    a=p.parse_args();print(json.dumps(run(a.count,a.seed,a.out,not a.no_negative_controls),indent=2))
