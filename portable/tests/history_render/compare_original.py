#!/usr/bin/env python3
"""Compare the standalone native history command model with frozen DOS calls."""
from __future__ import annotations
import argparse
import ctypes as ct
import json
import random
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PORT = ROOT / "portable"
sys.path.insert(0, str(ROOT / "tools/behavior_suites"))
sys.path.insert(0, str(ROOT / "tools"))
import text_card as suite
import behavior

HISTORY = PORT / "ui_model/windows/history_render.c"
HEADER = PORT / "ui_model/windows/history_render.h"

class Rect(ct.Structure):
    _fields_ = [(n, ct.c_int16) for n in ("left", "top", "right", "bottom")]

class Input(ct.Structure):
    _fields_ = [
        ("series", (ct.c_int16 * 64) * 10),
        ("history_color", ct.c_int16 * 10),
        ("graph_colors", ct.c_int16 * 4),
        ("labels", ct.POINTER(ct.c_char) * 10),
        ("label_sizes", ct.c_size_t * 10),
        ("start", ct.c_int16), ("count", ct.c_int16),
        ("graph", ct.c_int16), ("hilite", ct.c_int16), ("slot", ct.c_int16),
    ]

class WindowInput(ct.Structure):
    _fields_ = [("render", Input), ("flags", ct.c_int16),
                ("shown_graphs", ct.c_int16 * 4)]

class Command(ct.Structure):
    _fields_ = [("kind", ct.c_int), ("a", ct.c_int16), ("b", ct.c_int16),
        ("c", ct.c_int16), ("d", ct.c_int16), ("e", ct.c_int16),
        ("text_size", ct.c_uint16), ("text", ct.c_char * 256)]

RECT_CB = ct.CFUNCTYPE(ct.c_int, ct.c_void_p, ct.c_int16, ct.c_int16, ct.POINTER(Rect))
HEIGHT_CB = ct.CFUNCTYPE(ct.c_int, ct.c_void_p, ct.POINTER(ct.c_int16))
WIDTH_CB = ct.CFUNCTYPE(ct.c_int, ct.c_void_p, ct.POINTER(ct.c_char), ct.c_size_t,
                        ct.POINTER(ct.c_int16))
FILL_CB = ct.CFUNCTYPE(ct.c_int, ct.c_void_p, ct.c_int16, ct.POINTER(ct.c_int16))
class Providers(ct.Structure):
    _fields_ = [("context", ct.c_void_p), ("get_object_rect", RECT_CB),
        ("get_font_height", HEIGHT_CB), ("get_text_width", WIDTH_CB),
        ("get_fill_color", FILL_CB)]

KIND = {0: "set_color", 1: "set_font", 2: "line", 3: "text", 4: "outline",
        5: "fill_object", 6: "draw_graph"}

def signed_word(value):
    value &= 0xffff
    return value - 0x10000 if value >= 0x8000 else value

def load_native():
    temp = tempfile.TemporaryDirectory(prefix="simant-history-render-",
                                       ignore_cleanup_errors=True)
    library_path = Path(temp.name) / "history_render.dll"
    subprocess.run(["gcc", "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
        "-shared", "-I", str(PORT), str(HISTORY),
        str(PORT / "render/font.c"), str(PORT / "render/primitives.c"),
        str(PORT / "game/resources/database.c"),
        str(PORT / "ui_model/windows/window.c"),
        str(PORT / "ui_model/windows/registry.c"),
        "-o", str(library_path)],
        cwd=ROOT, check=True)
    lib = ct.CDLL(str(library_path))
    fn = lib.portable_history_render_graph
    fn.argtypes = [ct.POINTER(Input), ct.POINTER(Providers), ct.POINTER(Command),
                   ct.c_size_t, ct.POINTER(ct.c_size_t)]
    fn.restype = ct.c_int
    lib.portable_history_status_string.argtypes = [ct.c_int]
    lib.portable_history_status_string.restype = ct.c_char_p
    win_fn = lib.portable_history_render_window
    win_fn.argtypes = [ct.POINTER(WindowInput), ct.POINTER(Providers),
                       ct.POINTER(Command), ct.c_size_t, ct.POINTER(ct.c_size_t)]
    win_fn.restype = ct.c_int
    return lib, fn, win_fn, temp

def run_raster_smoke(temp):
    executable = Path(temp.name) / "history_raster_smoke.exe"
    subprocess.run(["gcc", "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
        "-I", str(PORT), str(PORT / "tests/history_render/test_raster.c"),
        str(HISTORY), str(PORT / "render/font.c"),
        str(PORT / "render/primitives.c"),
        str(PORT / "game/resources/database.c"),
        str(PORT / "ui_model/windows/window.c"),
        str(PORT / "ui_model/windows/registry.c"), "-o", str(executable)],
        cwd=ROOT, check=True)
    result = subprocess.run([str(executable), str(ROOT / "assets/FONT2"),
        str(ROOT / "assets/HCEGANT"), str(ROOT / "assets/SHARED")],
        cwd=ROOT, check=True, text=True, capture_output=True)
    return result.stdout.strip()

def model_input(case, series_pair, oracle_trace):
    meta = case.metadata
    graph = int(meta["graph"])
    table_index = (graph & 1) * 5 + (graph >> 1)
    inp = Input()
    index_a = (0,2,4,6,7,1,3,5,8,9)[table_index]
    index_b = (1,3,5,6,9,0,2,4,9,8)[table_index]
    for idx, value in enumerate(series_pair[0]):
        inp.series[index_a][idx] = value
    for idx, value in enumerate(series_pair[1]):
        inp.series[index_b][idx] = value
    inp.history_color[graph] = 0
    for i, color in enumerate((0x43, 0x46, 0x49, 0x45)):
        inp.graph_colors[i] = color
    inp.start = meta["start"]
    inp.count = meta["sample_count"]
    inp.graph = graph
    inp.hilite = meta["hilite"]
    inp.slot = meta["slot"]
    draw = next(x["args"] for x in oracle_trace if x["name"] == "f_24AB_038D")
    label = bytes.fromhex(draw["text_hex"])
    label_buf = ct.create_string_buffer(label + b"\0")
    inp.labels[table_index] = ct.cast(label_buf, ct.POINTER(ct.c_char))
    inp.label_sizes[table_index] = len(label)
    rect = Rect(*meta["window_rect"])
    border = next(x["args"] for x in oracle_trace if x["name"] == "f_1CE2_01F8")
    font_height = signed_word(border[3] - draw["y"] - 1)
    text_width = signed_word(border[2] - draw["x"] - 1)
    def get_rect(ctx, win, obj, out):
        out[0] = rect
        return int(win == 0x1500 and obj == 0x150e)
    def get_height(ctx, out):
        out[0] = font_height
        return 1
    def get_width(ctx, text, size, out):
        out[0] = text_width
        return 1
    providers = Providers(None, RECT_CB(get_rect), HEIGHT_CB(get_height),
                          WIDTH_CB(get_width), FILL_CB())
    return inp, providers, label_buf

def native_trace(fn, lib, inp, providers):
    out = (Command * 80)()
    count = ct.c_size_t()
    status = fn(ct.byref(inp), ct.byref(providers), out, len(out), ct.byref(count))
    if status:
        raise RuntimeError(lib.portable_history_status_string(status).decode())
    trace = []
    for c in out[:count.value]:
        item = {"kind": KIND[c.kind], "a": c.a, "b": c.b, "c": c.c,
                "d": c.d, "e": c.e}
        if c.kind == 3:
            item["text_hex"] = bytes(c.text[:c.text_size]).hex()
        trace.append(item)
    return trace

def check_window_wrapper(win_fn, lib, inp, providers):
    fill_cb = FILL_CB(lambda ctx, obj, out: (out.__setitem__(0, 2) or int(obj == 0x150e)))
    providers.get_fill_color = fill_cb
    window = WindowInput()
    window.render = inp
    commands = (Command * 300)()
    count = ct.c_size_t()
    window.flags = 0
    window.shown_graphs[:] = [inp.graph, -32768, -32768, -32768]
    status = win_fn(ct.byref(window), ct.byref(providers), commands, len(commands), ct.byref(count))
    if status or count.value:
        raise AssertionError("win_DrawHistoryWindow must emit nothing without flags & 2")
    window.flags = 2
    window.shown_graphs[:] = [inp.graph, -32768, inp.graph, -32768]
    status = win_fn(ct.byref(window), ct.byref(providers), commands, len(commands), ct.byref(count))
    if status:
        raise RuntimeError(lib.portable_history_status_string(status).decode())
    if (count.value != 139 or commands[0].kind != 5 or commands[0].a != 0x150e or
        commands[0].b != 2 or commands[1].kind != 6 or commands[1].a != inp.graph or
        commands[1].c != 0 or commands[70].kind != 6 or
        commands[70].a != inp.graph or commands[70].c != 2):
        raise AssertionError("win_DrawHistoryWindow fill/slot ordering differs from S24 source")
    return count.value

def oracle_projection(trace):
    result = []
    for x in trace:
        if x["name"] == "win_DrawBitMap":
            a = [signed_word(v) for v in x["args"]]
            result.append({"kind": "line", "a": a[0], "b": a[1], "c": a[2], "d": a[3], "e": a[4]})
        elif x["name"] == "win_SetColorFromObjNum":
            a = [signed_word(v) for v in x["args"]]
            result.append({"kind": "set_color", "a": a[0], "b": a[1], "c": a[2], "d": 0, "e": 0})
        elif x["name"] == "f_24AB_038D":
            a = x["args"]
            result.extend([{"kind": "set_font", "a": 3, "b": 0, "c": 0, "d": 0, "e": 0},
                {"kind": "text", "a": signed_word(a["x"]), "b": signed_word(a["y"]),
                 "c": 0, "d": 0, "e": 0, "text_hex": a["text_hex"]}])
        elif x["name"] == "f_1CE2_01F8":
            a = [signed_word(v) for v in x["args"]]
            result.append({"kind": "outline", "a": a[0], "b": a[1], "c": a[2], "d": a[3], "e": a[4]})
    result.append({"kind": "set_font", "a": 0, "b": 0, "c": 0, "d": 0, "e": 0})
    return result

def replace_arrays(case, arrays):
    writes = list(case.writes)
    packed = [struct.pack("<64h", *values) for values in arrays]
    writes[0] = (writes[0][0], packed[0])
    writes[1] = (writes[1][0], packed[1])
    case.writes = writes
    case.metadata["history_arrays"] = [p.hex() for p in packed]

def effective_arrays(case):
    # The frozen oracle case writes arrays by far pointer. If the game's two
    # selected table entries alias, the later write wins exactly as it does in
    # the DOS machine; pass that same effective data to the standalone model.
    memory = {address: data for address, data in case.writes[:2]}
    return [list(struct.unpack("<64h", memory[address]))
            for address, _ in case.writes[:2]]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--random", type=int, default=200)
    parser.add_argument("--seed", type=lambda s: int(s, 0), default=0x39c7032c)
    args = parser.parse_args()
    lib, fn, win_fn, temp = load_native()
    raster_smoke = run_raster_smoke(temp)
    pair = behavior.PreparedPair(suite.HISTORY_FUNCTION,
        source=ROOT / "build/workers/behavior_text_card/S24.c")
    failures = []
    checked = 0
    forced_labels = 0
    window_commands = 0
    aliased_cases = 0
    nonaliased_cases = 0
    directed = list(suite.history_cases(0))
    cases = [(label, case, None) for label, case in directed]
    rng = random.Random(args.seed)
    for i in range(args.random):
        graph, hilite, slot = rng.randrange(10), rng.randrange(2), rng.randrange(4)
        start, count = rng.randrange(64), rng.randrange(65)
        left, top = rng.randrange(33), rng.randrange(25)
        width, height = rng.randrange(128, 641), rng.randrange(120, 481)
        case = suite._history_case(f"signed/{args.seed:08x}/{i}", graph, hilite,
            slot, start, count, (left, top, left + width, top + height),
            rng.randrange(1 << 32), "zero")
        arrays = [[rng.randrange(-32768, 32768) for _ in range(64)] for _ in range(2)]
        cases.append(("signed", case, arrays))
    for lane, case, arrays in cases:
        if arrays is not None:
            replace_arrays(case, arrays)
        if case.metadata["hilite"] == 0 and checked % 7 == 0:
            initial = pair.original_machine.run(case)
            draw_raw = next(x["args"] for x in initial["raw_trace"]
                            if x["name"] == "f_24AB_038D")
            label = f"H{checked:03d}".encode("ascii")
            case.writes.append((draw_raw[3] * 16 + draw_raw[2], label + b"\0"))
            forced_labels += 1
        oracle = pair.original_machine.run(case)
        if case.writes[0][0] == case.writes[1][0]:
            aliased_cases += 1
        else:
            nonaliased_cases += 1
        arrays = effective_arrays(case)
        inp, providers, keepalive = model_input(case, arrays, oracle["trace"])
        got = native_trace(fn, lib, inp, providers)
        want = oracle_projection(oracle["trace"])
        if got != want:
            failures.append({"label": case.label, "lane": lane,
                "first_difference": next((i for i,(a,b) in enumerate(zip(got,want)) if a!=b), min(len(got),len(want))),
                "native_count": len(got), "oracle_count": len(want),
                "native": got[:3] + got[-4:], "oracle": want[:3] + want[-4:]})
            break
        if window_commands == 0:
            window_commands = check_window_wrapper(win_fn, lib, inp, providers)
        checked += 1
    pin = lambda path: __import__("hashlib").sha256(path.read_bytes()).hexdigest()
    result = {"status": "FAIL" if failures else "PASS", "checked": checked,
        "directed": len(directed), "signed_randomized": args.random, "seed": args.seed,
        "forced_resource_labels": forced_labels,
        "wrapper_commands": window_commands,
        "resource_font_raster_smoke": raster_smoke,
        "effective_address_alias_cases": aliased_cases,
        "effective_address_distinct_cases": nonaliased_cases,
        "pins": {"implementation_sha256": pin(HISTORY),
            "header_sha256": pin(HEADER),
            "comparison_harness_sha256": pin(Path(__file__)),
            "raster_smoke_sha256": pin(Path(__file__).with_name("test_raster.c")),
            "resource_font_renderer_sha256": pin(PORT / "render/font.c"),
            "framebuffer_primitives_sha256": pin(PORT / "render/primitives.c"),
            "database_decoder_sha256": pin(PORT / "game/resources/database.c"),
            "window_resource_decoder_sha256": pin(PORT / "ui_model/windows/window.c"),
            "window_registry_sha256": pin(PORT / "ui_model/windows/registry.c"),
            "font_asset_sha256": pin(ROOT / "assets/FONT2"),
            "windows_database_index_sha256": pin(ROOT / "assets/HCEGANT.NDX"),
            "windows_database_data_sha256": pin(ROOT / "assets/HCEGANT.DAT"),
            "shared_database_index_sha256": pin(ROOT / "assets/SHARED.NDX"),
            "shared_database_data_sha256": pin(ROOT / "assets/SHARED.DAT"),
            "behavior_module_sha256": pin(Path(behavior.__file__)),
            "behavior_harness_sha256": pair.identity["harness_sha256"],
            "suite_source_sha256": pin(Path(suite.__file__)),
            "suite_source_module_closure_sha256": {
                name: pin(ROOT / "tools" / f"{name}.py")
                for name in ("exe", "functions", "match", "modctx", "modules", "context")},
            "oracle_module_source_sha256": pin(ROOT / "build/workers/behavior_text_card/S24.c"),
            "original_exe_sha256": pair.identity["oracle_sha256"]},
        "range": {"graph": "0..9", "hilite": "0..1", "slot": "0..3",
            "start": "0..63", "count": "0..64", "series": "int16 full range",
            "rectangle_width": "128..640", "rectangle_height": "120..480"},
        "provider_boundary": "rect, font height, and text width are explicit; DOS oracle values feed providers for each case; logical service requests compare against the original DOS trace",
        "pixel_boundary": "resource FONT2 raster helper is smoke-checked on a native framebuffer; no DOS pixels were compared or claimed",
        "failures": failures}
    if args.random and (aliased_cases == 0 or nonaliased_cases == 0):
        result["status"] = "FAIL"
        result["failures"].append({"reason": "random lane did not cover both alias and distinct far-pointer inputs"})
    outdir = PORT / "tests/history_render"
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "comparison_report.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    temp.cleanup()
    raise SystemExit(1 if failures else 0)

if __name__ == "__main__":
    main()

