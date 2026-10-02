#!/usr/bin/env python3
"""Compare menu dropdown draw-plan commands to original DOS draw sinks."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
PORT = ROOT / "portable"
BUILD = ROOT / "build/portable/menu-dropdown-render-trace"
FIXTURE = ROOT / "portable/tests/menus/dropdown_render_fixture.c"
REPORT = ROOT / "portable/tests/menus/evidence/dropdown-render-trace.json"
ASSET_TEST = ROOT / "portable/tests/menus/test_dropdown_assets.c"
SOURCE_PROOF_FILES = [
    ROOT / "src/root/m1FD2.c",
    ROOT / "src/root/m1CE2.c",
    ROOT / "src/root/m1B4E.asm",
    ROOT / "src/S00/m31AD.asm",
    ROOT / "src/S00/m3126.asm",
]
PLAN_SOURCES = [
    ROOT / "portable/ui_model/menus/dropdown_render.c",
    ROOT / "portable/ui_model/menus/interaction.c",
    ROOT / "portable/ui_model/menus/menu.c",
    ROOT / "portable/game/resources/database.c",
    ROOT / "portable/render/primitives.c",
    FIXTURE,
]
ASSET_SOURCES = [ASSET_TEST,
                 ]
SOURCES = PLAN_SOURCES + ASSET_SOURCES
sys.path.insert(0, str(ROOT / "tools"))
import behavior as b
from behavior_suites import tutorial_menu as source_fixtures


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def w(*values):
    import struct
    return struct.pack("<" + "H" * len(values), *(v & 0xffff for v in values))


def far_symbol(name: str) -> bytes:
    symbol = b.symbol(name)
    return w(symbol["off"], symbol["seg"])


def compile_fixture() -> Path:
    BUILD.mkdir(parents=True, exist_ok=True)
    exe = BUILD / "dropdown-render-fixture.exe"
    subprocess.run(["gcc", "-std=c11", "-O2", "-Wall", "-Wextra",
                    "-Wconversion", "-Werror", "-I", str(PORT),
                    *(str(p) for p in PLAN_SOURCES), "-o", str(exe)],
                   cwd=ROOT, check=True)
    return exe


def compile_asset_test() -> Path:
    exe = BUILD / "dropdown-assets.exe"
    subprocess.run(["gcc", "-std=c11", "-O2", "-Wall", "-Wextra",
                    "-Wconversion", "-Werror", "-I", str(PORT),
                    str(ASSET_TEST),
                    str(ROOT / "portable/ui_model/menus/dropdown_render.c"),
                    str(ROOT / "portable/ui_model/menus/interaction.c"),
                    str(ROOT / "portable/ui_model/menus/menu.c"),
                    str(ROOT / "portable/game/resources/database.c"),
                    str(ROOT / "portable/render/primitives.c"),
                    "-o", str(exe)], cwd=ROOT, check=True)
    return exe


def original_draw_case(pair, menu_index: int):
    items = [b" Alpha", b" -", b"\xc2eta", b" Gamma"]
    case = source_fixtures.menu_case(
        f"dropdown-render/menu-{menu_index}", [13], curmenu=menu_index,
        items=items, selected=1, width=640, height=400, line_height=12,
        char_width=8)
    case.state["draw_trace"] = []
    case.callbacks.pop("f_1FD2_02B1")

    def attribute_sink(machine, args):
        machine.state["draw_trace"].append(["mode", list(args)])
        machine.state["host_trace"].append(["draw-attribute", list(args)])
        for symbol_name, value in zip(("g_3DE0", "g_3DE2", "g_3DE4"), args):
            machine.write(b.symbol_address(symbol_name), bytes([value & 0xff]))

    def primitive_sink(machine, args):
        machine.state["draw_trace"].append(["rect", list(args)])
        machine.state["host_trace"].append(["draw-primitive", list(args)])
        machine.state["host_trace"].append(["dispatch-event", list(args)])

    def end_open_draw(machine, args):
        machine.state["host_trace"].append(["draw-plan-end"])

    case.callbacks["f_1B4E_0110"] = b.Callback(3, attribute_sink)
    case.callbacks["f_1B73_030F"] = b.Callback(5, primitive_sink)
    case.callbacks["f_1FD2_02FF"] = b.Callback(0, end_open_draw)
    case.writes += [
        (b.symbol_address("g_9128"), far_symbol("f_1B4E_0110")),
        (b.symbol_address("g_9134"), far_symbol("f_1B73_030F")),
    ]
    result = pair.original_machine.run(case)
    m = pair.original_machine
    title_x = int.from_bytes(m.read(b.symbol_address("fd_50F6_46A8") + 2 * menu_index,
                                    2), "little", signed=True)
    title_width = int.from_bytes(m.read(b.symbol_address("fd_50F6_46BC") + 2 * menu_index,
                                        2), "little", signed=True)
    return case, result, items, title_x, title_width


def native_draw(exe: Path, title_x: int, title_width: int):
    result = subprocess.run([str(exe), str(title_x), str(title_width)],
                            cwd=ROOT, check=True, capture_output=True, text=True)
    return json.loads(result.stdout)


def compare(case, result, native):
    expected_attrs = []
    expected_rects = []
    expected_text = []
    for command in native["commands"]:
        if command["kind"] == "mode":
            expected_attrs.append(command["attrs"])
        elif command["kind"] == "rect":
            expected_rects.append(command["rect"] + [command["color"]])
        elif command["kind"] == "text":
            text = bytes.fromhex(command["text_hex"])
            if command["clear"]:
                text = bytes([text[0] & 0x7f]) + text[1:]
            expected_text.append([command["x"], command["y"], text.hex()])
    draw_trace = []
    for row in result["state"]["host_trace"]:
        if row[0] == "draw-plan-end":
            break
        if row[0] in ("draw-attribute", "draw-primitive", "font-draw-text"):
            draw_trace.append(row)
    actual_attrs = [row[1] for row in draw_trace if row[0] == "draw-attribute"]
    actual_rects = [row[1] for row in draw_trace if row[0] == "draw-primitive"]
    actual_text = [[row[1], row[2], row[3]] for row in draw_trace
                   if row[0] == "font-draw-text"]
    # DOS `f_1FBD_0000` receives a C string, so remove only any bytes after its
    # first terminator; the target padded row text itself has no embedded NUL.
    actual_text = [[x, y, bytes.fromhex(raw).split(b"\0", 1)[0].hex()]
                   for x, y, raw in actual_text]
    actual_rect = next((row[1] for row in result["state"]["host_trace"]
                        if row[0] == "save-screen-rect"), None)
    return {
        "equal": (actual_attrs == expected_attrs and actual_rects == expected_rects and
                  actual_text == expected_text and actual_rect == native["saved_rect"]),
        "saved_rect": {"original": actual_rect, "native": native["saved_rect"]},
        "mode_count": {"original": len(actual_attrs), "native": len(expected_attrs)},
        "primitive_count": {"original": len(actual_rects), "native": len(expected_rects)},
        "text_count": {"original": len(actual_text), "native": len(expected_text)},
        "trace_match": {
            "attributes": actual_attrs == expected_attrs,
            "primitives": actual_rects == expected_rects,
            "text": actual_text == expected_text,
        },
        "original_trace": draw_trace,
        "native_commands": native["commands"],
    }


def main():
    exe = compile_fixture()
    asset_exe = compile_asset_test()
    font_root = ROOT / "build/bios-reference/dosbox-staging-v0.83.0"
    font_manifest = font_root / "manifest.json"
    font_8x14 = font_root / "font-8x14.bin"
    if (sha(font_manifest) != "ccfb943edb92e17108bb3a74fa326052ab940839f9199df743182ef6280a5aa9" or
        sha(font_8x14) != "657ca6588b6bf729f0ed71a3d3c781a465bd30cdfb11eb5fc7e27594c0717ea1"):
        raise RuntimeError("DOSBox Staging reference BIOS font is missing or does not match its pinned identity")
    asset_run = subprocess.run([str(asset_exe), str(ROOT / "assets"),
        str(font_root)],
        cwd=ROOT, check=True, capture_output=True, text=True)
    pair = b.PreparedPair("o10_35F5_0384", out=BUILD / "oracle")
    cases = []
    for menu_index in range(5):
        case, result, items, title_x, title_width = original_draw_case(pair, menu_index)
        native = native_draw(exe, title_x, title_width)
        comparison = compare(case, result, native)
        cases.append({"case": case.label, "menu_index": menu_index,
                      "title_x": title_x, "title_width_cells": title_width,
                      "equal": comparison["equal"], **comparison})
    report = {
        "schema": "portable-menu-dropdown-render-trace-v1",
        "status": "PASS" if all(row["equal"] for row in cases) else "FAIL",
        "target": "original DOS S10:o10_35F5_0384 calling original f_1FD2_02B1/f_1CE2_044D/f_1CE2_01F8/f_1FD2_0008; graphics sinks are explicit deterministic trace providers",
        "native_sources": {str(p.relative_to(ROOT)).replace("\\", "/"): sha(p)
                           for p in SOURCES},
        "source_anchors": {str(p.relative_to(ROOT)).replace("\\", "/"): sha(p)
                           for p in SOURCE_PROOF_FILES},
        "original": {"harness_sha256": pair.identity["harness_sha256"],
                     "manifest_sha256": pair.identity["manifest_sha256"],
                     "oracle_sha256": pair.identity["oracle_sha256"],
                     "target_source_sha256": pair.identity["source_sha256"],
                     "target_object_sha256": pair.identity["object_sha256"]},
        "cases": cases,
        "resource_smoke": {"executable_sha256": sha(asset_exe),
                           "reference_font_manifest_sha256": sha(font_manifest),
                           "reference_font_8x14_sha256": sha(font_8x14),
                           "observation": asset_run.stdout.strip()},
        "compared": ["saved dropdown rect", "exact ordered graphics attribute tuples",
                     "all eight negative-width primitive coordinate/color tuples",
                     "padded text sink bytes and coordinates"],
        "primitive_driver_contract": {
            "source": "S00 o00_31AD_16A9, selected by the fourth g_3DF8 driver entry; its entry swaps reversed endpoints using unsigned comparisons, then the shared body at 16FC/1702/1736 fills a half-open rect with color & 0x0f.",
            "executor": "portable_fill_rect normalizes the coordinates and performs a clipped half-open indexed fill.",
            "direct_DOS_framebuffer_comparison": False,
        },
        "glyph_color_contract": {
            "source": "S00 m31AD glyph path loads g_3DE0 and g_3DE2, uses their low four planes for foreground/background; the path does not reference g_3DE4.",
            "pattern_attributes": "The source mode tuples retain pattern values 0, 0xc0 and 0x30. They are not applied to glyph rasterization because the DOS glyph path does not read the fill-pattern byte.",
            "reference_font": "DOSBox Staging v0.83.0 reference 8x14 glyph table; host reference only, not evidence of the original machine BIOS contents.",
            "direct_DOS_framebuffer_comparison": False,
        },
        "boundaries": ["Original DOS code is compared for the exact ordered mode tuples, primitive call tuples, and padded text sink bytes/coordinates; those trace checks are not pixel-equality proof.",
                       "The actual SHARED kind-6 id 0 asset smoke executes the native indexed rasterizer for five enabled dropdowns and checks highlight plus saved-rectangle restoration.",
                       "Popup/context menus and SDL integration remain outside this renderer."],
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "cases": len(cases),
                      "mismatches": sum(not c["equal"] for c in cases),
                      "receipt": str(REPORT.relative_to(ROOT))}, indent=2))
    if report["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
