#!/usr/bin/env python3
"""Compare the standalone native history command model with frozen DOS calls."""
from __future__ import annotations
import argparse
import ctypes as ct
import json
import random
import shutil
import struct
import subprocess
import sys
import tempfile
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PORT = ROOT / "portable"
sys.path.insert(0, str(ROOT / "tools/behavior_suites"))
sys.path.insert(0, str(ROOT / "tools"))
import text_card as suite
import behavior

HISTORY = PORT / "ui_model/windows/history_render.c"
HEADER = PORT / "ui_model/windows/history_render.h"
ORACLE_FIXTURE = Path(__file__).with_name("archive") / "oracle_S24_behavior_text_card.c"
CANONICAL_SOURCE = ROOT / "src/S24/m39C7.c"
ARCHIVED_RUNNER_SHA = "f8c576f04714c03aa3e34b6833f838fc831eb0a966248dff0c26854de79d81ad"
ARCHIVED_REPORT_SHA = "f815a6c558bea966640907e350467168926aa1adb01409f6e2498ffd0df63936"
ORACLE_FIXTURE_SHA = "764bcd8f1272b6f9655a1fe305cea71d98e95b9ad9c285f69dc944fbfe21d34c"
CANONICAL_SOURCE_SHA = "3de9615a57dbe35eacd073726b451478dc5b12396360501631d7553b6139e240"
NATIVE_C_SOURCES = [
    PORT / "ui_model/windows/history_render.c",
    PORT / "render/font.c",
    PORT / "render/primitives.c",
    PORT / "game/resources/database.c",
    PORT / "ui_model/windows/window.c",
    PORT / "ui_model/windows/registry.c",
]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def gcc_path():
    path = shutil.which("gcc")
    if path is None:
        raise RuntimeError("gcc not found on PATH")
    return Path(path).resolve()


def gcc_dependencies(compiler, sources):
    rows = []
    dependencies = set()
    for source in sources:
        command = [str(compiler), "-MM", "-std=c11", "-O2", "-Wall", "-Wextra",
                   "-Werror", "-I", str(PORT), str(source)]
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        if result.returncode:
            raise RuntimeError("gcc -MM failed for " + str(source) + ":\n" +
                               result.stdout + result.stderr)
        flattened = result.stdout.replace("\\\n", " ").replace("\\\r\n", " ")
        if ":" not in flattened:
            raise RuntimeError("gcc -MM returned no rule for " + str(source))
        found = []
        for token in flattened.split(":", 1)[1].split():
            candidate = Path(token)
            if not candidate.is_absolute():
                candidate = ROOT / candidate
            candidate = candidate.resolve()
            if not candidate.is_file():
                raise RuntimeError("gcc -MM dependency missing: " + str(candidate))
            dependencies.add(candidate)
            found.append(candidate)
        rows.append({"source": str(source.relative_to(ROOT)).replace("\\", "/"),
                     "command": command, "dependencies": sorted(
                         str(p.relative_to(ROOT)).replace("\\", "/") for p in found)})
    return rows, sorted(dependencies)


def python_closure():
    paths = {Path(__file__).resolve()}
    for module in tuple(sys.modules.values()):
        value = getattr(module, "__file__", None)
        if not value:
            continue
        path = Path(value).resolve()
        if path.suffix == ".py" and (path == ROOT or ROOT in path.parents):
            paths.add(path)
    return sorted(paths)


def ctypes_abi_layout():
    structs = (Rect, Input, WindowInput, Command, Providers)
    result = {}
    for struct_type in structs:
        result[struct_type.__name__] = {"sizeof": ct.sizeof(struct_type),
            "alignment": ct.alignment(struct_type),
            "fields": {name: {"offset": getattr(struct_type, name).offset,
                               "size": ct.sizeof(field_type)}
                       for name, field_type, *rest in struct_type._fields_}}
    return result


def canonical_anchors():
    lines = CANONICAL_SOURCE.read_text(encoding="latin1").splitlines()
    anchors = (
        "static int graphColors[4] = { 0x43, 0x46, 0x49, 0x45 };",
        "static int shownGraphs[4] = { (int)0x8000, (int)0x8000, (int)0x8000, (int)0x8000 };",
        "static int histColor[20];",
        "static char histShown[10];",
        "void far drawHistGraph(int graph, int hilite, int slot);",
        "void far win_DrawHistoryWindow(int flags);",
    )
    rows = []
    for anchor in anchors:
        indices = [index for index, line in enumerate(lines, 1) if line.strip() == anchor]
        if len(indices) != 1:
            raise RuntimeError(f"canonical S24 anchor expected once: {anchor}")
        rows.append({"line": indices[0], "text": anchor})
    return rows

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
    command = ["gcc", "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
        "-shared", "-I", str(PORT), *[str(p) for p in NATIVE_C_SOURCES],
        "-o", str(library_path)]
    subprocess.run(command, cwd=ROOT, check=True)
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
    return lib, fn, win_fn, temp, {"path": str(library_path),
        "sha256": sha(library_path.read_bytes()), "command": command}

def run_raster_smoke(temp):
    executable = Path(temp.name) / "history_raster_smoke.exe"
    raster_source = PORT / "tests/history_render/test_raster.c"
    command = ["gcc", "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
        "-I", str(PORT), str(raster_source),
        *[str(p) for p in NATIVE_C_SOURCES], "-o", str(executable)]
    subprocess.run(command, cwd=ROOT, check=True)
    result = subprocess.run([str(executable), str(ROOT / "assets/FONT2"),
        str(ROOT / "assets/HCEGANT"), str(ROOT / "assets/SHARED")],
        cwd=ROOT, check=True, text=True, capture_output=True)
    return {"stdout": result.stdout.strip(), "path": str(executable),
            "sha256": sha(executable.read_bytes()), "command": command}

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
    parser.add_argument("--random", type=int, default=400)
    parser.add_argument("--seed", type=lambda s: int(s, 0), default=0x39c7032c)
    parser.add_argument("--report", required=True,
        help="new receipt path; the runner refuses to overwrite an existing file")
    args = parser.parse_args()
    target = Path(args.report)
    if not target.is_absolute():
        target = ROOT / target
    target = target.resolve()
    packet_root = Path(__file__).resolve().parent
    if packet_root not in target.parents:
        raise RuntimeError("--report must remain inside portable/tests/history_render")
    if target.exists():
        raise FileExistsError(f"refusing to overwrite existing receipt: {target}")
    archived_runner = packet_root / "archive/compare_original.py"
    archived_report = packet_root / "archive/comparison_report.json"
    for path, expected, label in (
        (archived_runner, ARCHIVED_RUNNER_SHA, "archived original runner"),
        (archived_report, ARCHIVED_REPORT_SHA, "archived 448-case receipt"),
        (ORACLE_FIXTURE, ORACLE_FIXTURE_SHA, "archived DOS oracle fixture"),
        (CANONICAL_SOURCE, CANONICAL_SOURCE_SHA, "canonical S24 source")):
        if sha(path.read_bytes()) != expected:
            raise RuntimeError(f"pinned {label} changed: {path}")
    anchors = canonical_anchors()
    pair = behavior.PreparedPair(suite.HISTORY_FUNCTION, source=ORACLE_FIXTURE)
    compiler = gcc_path()
    version = subprocess.run([str(compiler), "--version"], cwd=ROOT,
        capture_output=True, text=True, check=True).stdout.splitlines()[0]
    c_sources = [*NATIVE_C_SOURCES, PORT / "tests/history_render/test_raster.c"]
    dependency_rows, c_dependencies = gcc_dependencies(compiler, c_sources)
    py_before = python_closure()
    base_inputs = set(c_dependencies) | set(py_before) | {
        archived_runner.resolve(), archived_report.resolve(), ORACLE_FIXTURE.resolve(),
        CANONICAL_SOURCE.resolve(), PORT / "tests/history_render/test_raster.c",
        ROOT / "assets/FONT2", ROOT / "assets/HCEGANT.NDX", ROOT / "assets/HCEGANT.DAT",
        ROOT / "assets/SHARED.NDX", ROOT / "assets/SHARED.DAT",
    }
    inputs_before = {str(p.resolve().relative_to(ROOT)).replace("\\", "/"):
                     sha(p.resolve().read_bytes()) for p in sorted(base_inputs)}
    compiler_before = sha(compiler.read_bytes())
    abi = ctypes_abi_layout()
    abi_bytes = json.dumps(abi, sort_keys=True, separators=(",", ":")).encode()
    lib, fn, win_fn, temp, native_binary = load_native()
    raster_build = run_raster_smoke(temp)
    raster_smoke = raster_build["stdout"]
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
    py_after = python_closure()
    dependency_rows_after, dependencies_after = gcc_dependencies(compiler, c_sources)
    if dependency_rows_after != dependency_rows or dependencies_after != c_dependencies:
        raise RuntimeError("gcc -MM dependency closure changed during the run")
    after_paths = set(c_dependencies) | set(py_after) | {
        archived_runner.resolve(), archived_report.resolve(), ORACLE_FIXTURE.resolve(),
        CANONICAL_SOURCE.resolve(), PORT / "tests/history_render/test_raster.c",
        ROOT / "assets/FONT2", ROOT / "assets/HCEGANT.NDX", ROOT / "assets/HCEGANT.DAT",
        ROOT / "assets/SHARED.NDX", ROOT / "assets/SHARED.DAT",
    }
    inputs_after = {str(p.resolve().relative_to(ROOT)).replace("\\", "/"):
                    sha(p.resolve().read_bytes()) for p in sorted(after_paths)}
    if inputs_after != inputs_before:
        before_keys, after_keys = set(inputs_before), set(inputs_after)
        raise RuntimeError("compiled-input pins changed during run; added=" +
            repr(sorted(after_keys - before_keys)) + " removed=" + repr(sorted(before_keys - after_keys)) +
            " changed=" + repr(sorted(k for k in before_keys & after_keys
                                       if inputs_before[k] != inputs_after[k])))
    compiler_after = sha(compiler.read_bytes())
    if compiler_after != compiler_before:
        raise RuntimeError("gcc compiler binary changed during run")
    if checked != len(directed) + args.random:
        failures.append({"reason": "not all planned cases were checked", "checked": checked})
    if len(directed) != 48 or args.random != 400:
        failures.append({"reason": "closure refresh must retain the 448-case comparison",
                         "directed": len(directed), "randomized": args.random})
    pixel_match = __import__("re").search(r"history raster: (\d+) pixels touched", raster_smoke)
    raster_source_text = (PORT / "tests/history_render/test_raster.c").read_text(encoding="latin1")
    if "assert(count==70 && commands[0].kind==PORTABLE_HISTORY_FILL_OBJECT)" not in raster_source_text:
        failures.append({"reason": "70-command resource-bound raster assertion changed"})
    if pixel_match is None or int(pixel_match.group(1)) != 361:
        failures.append({"reason": "resource-bound raster smoke did not retain 361 touched pixels",
                         "stdout": raster_smoke})
    pins = {"implementation_sha256": sha(HISTORY.read_bytes()),
            "header_sha256": sha(HEADER.read_bytes()),
            "ctypes_wrapper_sha256": sha(Path(__file__).read_bytes()),
            "ctypes_abi_layout_sha256": sha(abi_bytes),
            "raster_smoke_sha256": sha((PORT / "tests/history_render/test_raster.c").read_bytes()),
            "resource_font_renderer_sha256": sha((PORT / "render/font.c").read_bytes()),
            "framebuffer_primitives_sha256": sha((PORT / "render/primitives.c").read_bytes()),
            "database_decoder_sha256": sha((PORT / "game/resources/database.c").read_bytes()),
            "window_resource_decoder_sha256": sha((PORT / "ui_model/windows/window.c").read_bytes()),
            "window_registry_sha256": sha((PORT / "ui_model/windows/registry.c").read_bytes()),
            "behavior_harness_sha256": sha(Path(behavior.__file__).read_bytes()),
            "suite_source_sha256": sha(Path(suite.__file__).read_bytes()),
            "oracle_fixture_sha256": sha(ORACLE_FIXTURE.read_bytes()),
            "canonical_source_sha256": sha(CANONICAL_SOURCE.read_bytes()),
            "archived_runner_sha256": sha(archived_runner.read_bytes()),
            "archived_report_sha256": sha(archived_report.read_bytes()),
            "original_exe_sha256": pair.identity["oracle_sha256"]}
    result = {"schema": "history-render-transitive-closure-receipt-v1",
        "status": "FAIL" if failures else "PASS", "checked": checked,
        "directed": len(directed), "signed_randomized": args.random, "seed": args.seed,
        "forced_resource_labels": forced_labels,
        "wrapper_commands": window_commands,
        "resource_font_raster_smoke": raster_smoke,
        "resource_window_commands_asserted": 70,
        "resource_window_pixels_touched": int(pixel_match.group(1)) if pixel_match else None,
        "effective_address_alias_cases": aliased_cases,
        "effective_address_distinct_cases": nonaliased_cases,
        "archive": {"runner_path": str(archived_runner.relative_to(ROOT)).replace("\\", "/"),
            "runner_sha256": pins["archived_runner_sha256"],
            "original_448_case_receipt_path": str(archived_report.relative_to(ROOT)).replace("\\", "/"),
            "original_448_case_receipt_sha256": pins["archived_report_sha256"],
            "oracle_fixture_path": str(ORACLE_FIXTURE.relative_to(ROOT)).replace("\\", "/"),
            "oracle_fixture_sha256": pins["oracle_fixture_sha256"],
            "canonical_source_path": str(CANONICAL_SOURCE.relative_to(ROOT)).replace("\\", "/"),
            "canonical_source_sha256": pins["canonical_source_sha256"],
            "canonical_source_anchors": anchors,
            "anchor_scope": "Canonical anchors identify graph APIs and data declarations; the archived behavior fixture remains the frozen DOS oracle, and no body identity is implied."},
        "compiler": {"path": str(compiler), "sha256_before": compiler_before,
            "sha256_after": compiler_after, "version": version,
            "dependency_mode": "gcc -MM per compiled C translation unit; GCC -MM omits system headers"},
        "native_builds": {"ctypes_shared_library": native_binary,
            "resource_raster_executable": {"path": raster_build["path"],
                "sha256": raster_build["sha256"], "command": raster_build["command"]}},
        "ctypes_wrapper": {"path": str(Path(__file__).relative_to(ROOT)).replace("\\", "/"),
            "sha256": pins["ctypes_wrapper_sha256"], "abi_layout_sha256": pins["ctypes_abi_layout_sha256"],
            "abi_layout": abi},
        "compiled_dependency_closure": {"commands": dependency_rows,
            "files": [{"path": str(path.relative_to(ROOT)).replace("\\", "/"),
                       "sha256_before": inputs_before[str(path.relative_to(ROOT)).replace("\\", "/")],
                       "sha256_after": inputs_after[str(path.relative_to(ROOT)).replace("\\", "/")]}
                      for path in c_dependencies]},
        "python_oracle_resource_closure": {"files": [
                {"path": path, "sha256_before": inputs_before[path], "sha256_after": inputs_after[path]}
                for path in sorted(set(inputs_before) - {str(p.relative_to(ROOT)).replace("\\", "/") for p in c_dependencies})],
            "all_file_pins_unchanged_before_after": True, "pins": pins},
        "range": {"graph": "0..9", "hilite": "0..1", "slot": "0..3",
            "start": "0..63", "count": "0..64", "series": "int16 full range",
            "rectangle_width": "128..640", "rectangle_height": "120..480"},
        "provider_boundary": "rect, font height, and text width are explicit; DOS oracle values feed providers for each case; logical service requests compare against the original DOS trace",
        "pixel_boundary": "resource FONT2 raster helper is smoke-checked on a native framebuffer; no DOS pixels were compared or claimed",
        "failures": failures}
    if args.random and (aliased_cases == 0 or nonaliased_cases == 0):
        result["status"] = "FAIL"
        result["failures"].append({"reason": "random lane did not cover both alias and distinct far-pointer inputs"})
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("x", encoding="utf-8", newline="") as receipt:
        receipt.write(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    temp.cleanup()
    raise SystemExit(1 if failures else 0)

if __name__ == "__main__":
    main()

