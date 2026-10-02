"""Trace source DrawMode/DrawCaste windows against a command-model plan.

The original DOS routines execute directly. Only graphics-driver and current
font/window-text sinks are normalized host callbacks; HCEGANT windows and the
knob record are loaded from the real database through the setup fixture.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "portable/tests/setup/evidence"))
import behavior  # noqa: E402
import functions  # noqa: E402
import setup_differential  # noqa: E402

OUT = ROOT / "portable/tests/setup/render_controls/evidence/control-window-render-trace.json"
MODEL_EXE = ROOT / "build/workers/controls-render/test.exe"
GCC = Path("C:/msys64/mingw64/bin/gcc.exe")
MODEL_SOURCE = ROOT / "portable/ui_model/windows/control_render/control_render.c"
MODEL_TEST = ROOT / "portable/tests/setup/render_controls/test_control_render.c"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def signed16(value: int) -> int:
    value &= 0xffff
    return value - 0x10000 if value & 0x8000 else value


def original_trace(window_id: int) -> tuple[list[dict], dict]:
    _, machine, fixture = setup_differential.original_run()
    # Select the source profile explicitly; the setup fixture loads real window
    # records but intentionally does not run the DOS graphics-driver selector.
    machine.write(behavior.symbol_address("g_5A97"), bytes((0,)))
    f = functions.get("f_1CE2_046D")
    machine.write(behavior.symbol_address("g_9128"),
                  behavior.words(f["off"], f["seg"]))
    events: list[dict] = []

    def handler(name, fn):
        def call(vm, args):
            event = fn(vm, args)
            if event is not None:
                events.append(event)
        return call

    def format_call(vm, args):
        obj, offset, segment, low, high = args
        address = segment * 16 + offset
        raw = bytearray()
        while len(raw) < 128:
            ch = vm.read(address + len(raw), 1)[0]
            if ch == 0:
                break
            raw.append(ch)
        fmt = raw.decode("ascii")
        value = signed16(low) | (high << 16)
        events.append({"op": "text", "object": obj, "value": value,
                       "percent": "%" in fmt})

    def fill_or_pattern(vm, args):
        if args[0] <= 15 and args[1] <= 15:
            return {"op": "pattern", "fore": args[0], "back": args[1],
                    "pattern": args[2]}
        offset, segment, color = args
        rect = list(struct.unpack("<4h", vm.read(segment * 16 + offset, 8)))
        return {"op": "fill", "rect": rect, "fore": color}

    def outline(vm, args):
        offset, segment, width = args
        rect = list(struct.unpack("<4h", vm.read(segment * 16 + offset, 8)))
        return {"op": "outline", "rect": rect, "width": width}

    def add_bitmap(vm, args):
        events.append({"op": "bitmap_add", "x": signed16(args[2]),
                       "y": signed16(args[3]), "bitmap": args[4],
                       "priority": args[5]})
        return 7

    callbacks = {
        "clip_SetWin": behavior.Callback(1, handler("clip", lambda _vm, a: {"op": "clip", "window": a[0]})),
        "f_24AB_02AD": behavior.Callback(1, handler("font", lambda _vm, a: {"op": "font", "font": a[0]})),
        "win_PrintfAtObj": behavior.Callback(5, format_call),
        "f_22BF_0C38": behavior.Callback(1, handler("draw-text", lambda _vm, a: {"op": "draw_text", "object": a[0]})),
        "f_1CE2_046D": behavior.Callback(3, handler("fill/pattern", fill_or_pattern)),
        "f_1CE2_044D": behavior.Callback(3, handler("outline", outline)),
        "hanim_MakeAnimSet": behavior.Callback(0, handler("anim-create", lambda _vm, _a: {"op": "anim_create"})),
        "hanim_AddAnimObject": behavior.Callback(6, add_bitmap),
        "hanim_RenderAnimSet": behavior.Callback(2, handler("anim-render", lambda _vm, _a: {"op": "anim_render"})),
    }
    result = machine.run(behavior.Case(
        f"controls/DrawWindow/{window_id:04x}", args=[3], callbacks=callbacks,
        return_kind="void", callee_pop=0, observe_at_calls=False),
        preserve=True, function="win_DrawModeWindow" if window_id == 0x1200
        else "win_DrawCasteWindow")
    if result["return"] is not None:
        raise AssertionError("void draw-window routine returned a value")
    segment = fixture["win18_seg"] if window_id == 0x1200 else fixture["win19_seg"]
    prefix = "mode" if window_id == 0x1200 else "caste"
    source_input = {
        "draw_rect_object_12": setup_differential.read_object_rect(machine, segment, 12),
        "triangle_rect_object_13": setup_differential.read_object_rect(machine, segment, 13),
        "levels": setup_differential.read_words(machine,
                    "modeLevels" if prefix == "mode" else "casteLevels", 3),
        "point": setup_differential.read_words(machine,
                    "fd_50F6_0358" if prefix == "mode" else "fd_50F6_022E", 2, signed=True),
        "knob_size": setup_differential.read_words(machine, "knobSize", 2),
        "label_formats_percent": all(event.get("percent", False)
                                      for event in events if event["op"] == "text"),
        "colors_in_draw_order": [event["fore"] for event in events
                                  if event["op"] == "fill"],
        "screen_width": setup_differential.read_words(machine, "g_3DB2", 1)[0],
        "hardware_profile": machine.read(behavior.symbol_address("g_5A97"), 1)[0],
    }
    return events, source_input


OP_NAMES = {
    0: "clip", 1: "font", 2: "text", 3: "draw_text", 4: "fill",
    5: "pattern", 6: "outline", 7: "anim_create", 8: "bitmap_add",
    9: "bitmap_move", 10: "anim_render",
}


def model_rows() -> list[dict]:
    subprocess.run([str(GCC), "-std=c11", "-Wall", "-Wextra", "-Werror",
                    "-I", str(ROOT / "portable"), str(MODEL_SOURCE),
                    str(MODEL_TEST), "-o", str(MODEL_EXE)],
                   cwd=ROOT, check=True)
    output = subprocess.run([str(MODEL_EXE)], cwd=ROOT, check=True,
                            text=True, capture_output=True).stdout
    rows = []
    for line in output.splitlines():
        if not line[:1].isdigit():
            continue
        value = [int(part) for part in line.split("\t")]
        if len(value) != 18:
            raise AssertionError(f"unexpected model row width: {line}")
        rows.append(value)
    return rows


def model_event(row: list[int]) -> dict:
    (op, win, obj, bitmap, flags, value, left, top, right, bottom, x, y,
     width, font, fore, back, pattern, priority) = row
    name = OP_NAMES[op]
    if name == "clip": return {"op": name, "window": win}
    if name == "font": return {"op": name, "font": font}
    if name == "text": return {"op": name, "object": obj, "value": value,
                                 "percent": bool(flags & 1)}
    if name == "draw_text": return {"op": name, "object": obj}
    if name == "fill": return {"op": name, "rect": [left, top, right, bottom], "fore": fore}
    if name == "pattern": return {"op": name, "fore": fore, "back": back, "pattern": pattern}
    if name == "outline": return {"op": name, "rect": [left, top, right, bottom], "width": width}
    if name == "bitmap_add": return {"op": name, "x": x, "y": y, "bitmap": bitmap, "priority": priority}
    if name == "bitmap_move": return {"op": name, "x": x, "y": y, "bitmap": bitmap,
                                      "object": obj, "priority": priority}
    if name == "anim_render": return {"op": name}
    return {"op": name}


def main() -> None:
    rows = model_rows()
    if len(rows) < 45:
        raise AssertionError(f"expected mode/caste model plans, got {len(rows)} commands")
    counts = (24, 21)
    at = 0
    reports = []
    for window_id, count in zip((0x1200, 0x1300), counts):
        expected = [model_event(row) for row in rows[at:at + count]]
        at += count
        actual, source_input = original_trace(window_id)
        if not source_input["label_formats_percent"] or source_input["screen_width"] != 640 or source_input["hardware_profile"] != 0:
            raise AssertionError(f"unexpected source control profile/state: {source_input}")
        if actual != expected:
            first = next((i for i, (a, b) in enumerate(zip(actual, expected)) if a != b),
                         min(len(actual), len(expected)))
            raise AssertionError(json.dumps({"window": hex(window_id), "first_difference": first,
                                             "actual_count": len(actual), "model_count": len(expected),
                                             "actual": actual[first:first + 4],
                                             "model": expected[first:first + 4]}, indent=2))
        reports.append({"window_id": window_id, "direct_original_calls": 1,
                        "command_count": len(actual), "commands": actual,
                        "source_operands": source_input,
                        "comparison": "exact ordered normalized DOS command trace"})
    report = {
        "schema": "portable-controls-window-original-command-trace-v1",
        "status": "PASS_BOUNDED_COMMAND_TRACE_NOT_PIXELS",
        "oracle_sha256": sha(ROOT / "assets/SIMANT.EXE"),
        "ndx_sha256": sha(ROOT / "assets/HCEGANT.NDX"),
        "dat_sha256": sha(ROOT / "assets/HCEGANT.DAT"),
        "source_sha256": sha(ROOT / "src/root/m0798.c"),
        "primitive_source_sha256": sha(ROOT / "src/root/m1CE2.c"),
        "color_translation_source_sha256": sha(ROOT / "src/root/m1B4E.asm"),
        "setup_fixture_source_sha256": sha(ROOT / "portable/tests/setup/evidence/setup_differential.py"),
        "window_resource_helper_sha256": sha(ROOT / "portable/tests/windows/evidence/differential_window.py"),
        "behavior_harness_sha256": sha(ROOT / "tools/behavior.py"),
        "function_map_sha256": sha(ROOT / "layout/functions.json"),
        "symbol_map_sha256": sha(ROOT / "layout/symbols.json"),
        "model_test_binary_sha256": sha(MODEL_EXE),
        "model_source_sha256": sha(MODEL_SOURCE),
        "model_header_sha256": sha(ROOT / "portable/ui_model/windows/control_render/control_render.h"),
        "test_source_sha256": sha(MODEL_TEST),
        "runner_sha256": sha(Path(__file__)),
        "inputs": {"mode_triangle_rect": [136, 344, 247, 440], "caste_triangle_rect": [392, 344, 501, 440],
                   "knob_bitmap_id": 0x578, "profile": "HCEGANT kind-0 windows 18/19; source g_5A97 profile 0; g_3DB2=640"},
        "host_boundary": "win_PrintfAtObj, f_24AB_02AD, f_22BF_0C38, clip_SetWin, f_1CE2_046D/f_1CE2_044D and hanim callbacks are captured at source call boundaries. g_9128 points to a named f_1CE2_046D sink callback for the pattern-state operation. No physical VGA/framebuffer claim.",
        "scope": "Actual win_DrawModeWindow(3) and win_DrawCasteWindow(3) DOS bodies, initialized by the existing HCEGANT setup fixture. Command order, numeric labels, bars, colors, rects, clip IDs and knob resource key/placement are compared. No interactive control changes or full UI composition claim.",
        "runs": reports,
    }
    OUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"PASS: {sum(x['command_count'] for x in reports)} ordered original/model commands across 2 control windows")


if __name__ == "__main__":
    main()
