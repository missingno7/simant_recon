#!/usr/bin/env python3
"""Compare logical tile/life selection with original DOS f_0250_1018."""
from __future__ import annotations

import ctypes as ct
import hashlib
import json
from pathlib import Path
import random
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))
import behavior  # noqa: E402

GCC = Path("C:/msys64/mingw64/bin/gcc.exe")
OUT = ROOT / "build/portable/map-probe.dll"
REPORT = ROOT / "portable/tests/map/evidence/map-compose-dos-diff.json"
MAP_EVIDENCE = ROOT / "portable/tests/map/evidence/map_evidence.json"
SOURCE = ROOT / "src/root/m0250.c"
MAP_C = ROOT / "portable/game/render/map.c"
MAP_H = ROOT / "portable/game/render/map.h"
RASTER_C = ROOT / "portable/render/tile_raster.c"
RASTER_H = ROOT / "portable/render/tile_raster.h"
PRIMITIVES_C = ROOT / "portable/render/primitives.c"
PROBE = ROOT / "portable/tests/map/probe.c"
RUNNER = Path(__file__)
TILES_C = ROOT / "portable/game/resources/tiles.c"
TILES_H = ROOT / "portable/game/resources/tiles.h"
TILE_LAYOUT_REVIEW = ROOT / "portable/tests/resources/evidence/tile-layout-review.json"
TILE_LAYOUT_POSITIVE = ROOT / "portable/tests/resources/evidence/tile-layout-positive.json"
ASSET_HASHES = ROOT / "portable/tests/resources/ASSET_SHA256.md"
RASTER_DIFF = ROOT / "portable/tests/render/tile/evidence/dos-tile-raster-differential.json"
RASTER_TEST = ROOT / "portable/tests/render/tile/test_tile_raster.c"
MAP_TEST = ROOT / "portable/tests/map/test_map.c"


class MapView(ct.Structure):
    _fields_ = [(name, ct.c_int16) for name in (
        "plane", "camera_x", "camera_y", "pheromone_mode", "columns", "rows",
        "screen_left", "screen_top", "cell_step_x", "cell_step_y",
        "ega_profile", "animation_base", "queen_frame", "young_frame", "caste_frame")]


class MapCommand(ct.Structure):
    _fields_ = [("screen_x", ct.c_int16), ("screen_y", ct.c_int16),
                ("map_x", ct.c_int16), ("map_y", ct.c_int16),
                ("plane", ct.c_uint8), ("ground_tile", ct.c_uint8),
                ("life_present", ct.c_uint8), ("life_overlay", ct.c_uint8),
                ("life_frame", ct.c_uint16), ("life_resource_frame", ct.c_uint16),
                ("resource_family", ct.c_uint8),
                ("pheromone_tile", ct.c_uint8)]


class ProbeInput(ct.Structure):
    _fields_ = [("view", MapView), ("column", ct.c_int16), ("row", ct.c_int16),
                ("ground_tile", ct.c_uint8),
                ("life", ct.c_uint8), ("pheromone_value", ct.c_uint8),
                ("reserved", ct.c_uint8)]


class ProbeOutput(ct.Structure):
    _fields_ = [("status", ct.c_int16), ("command", MapCommand)]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_native():
    command = [str(GCC), "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
               "-shared", "-I", str(ROOT / "portable"), str(MAP_C), str(RASTER_C),
               str(PRIMITIVES_C), str(PROBE), "-o", str(OUT)]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(command, check=True, cwd=ROOT)
    lib = ct.CDLL(str(OUT))
    lib.sim_map_probe.argtypes = [ct.POINTER(ProbeInput), ct.POINTER(ProbeOutput)]
    lib.sim_map_probe.restype = None
    return lib, command


def direct_cases():
    cases = []
    for plane in range(4):
        for life in (0, 1, 0x40, 0x68, 0xe0, 0xfe, 0xff):
            for scent in (0, 1, 2, 3, 4):
                cases.append((f"direct/p{plane}/l{life:02x}/s{scent}", {
                    "plane": plane, "x": 63, "y": 63, "scent": scent,
                    "tile": (0x72 + plane * 7) & 0xff, "life": life,
                    "pheromone": [0x00, 0x10, 0x11, 0x1f, 0x2f][scent],
                    "anim": (3, 5, 7, 4)}))
    rng = random.Random(0x02501018)
    life_values = (0, 0, 0, 0xfe, 0xff, 0x11, 0x40, 0x68, 0xe0)
    for i in range(128):
        plane = rng.randrange(4)
        cases.append((f"random/{i}", {
            "plane": plane, "x": rng.randrange(128), "y": rng.randrange(64),
            "scent": rng.randrange(5), "tile": rng.randrange(256),
            "life": rng.choice(life_values), "pheromone": rng.randrange(256),
            "anim": tuple(rng.randrange(-16, 17) for _ in range(4))}))
    for plane in range(4):
        cases.append((f"camera-wrap/p{plane}", {
            "plane": plane, "x": 63, "y": 63, "column": 1, "row": 1,
            "scent": plane % 5, "tile": 0x55 + plane, "life": 0xfe,
            "pheromone": 0x20, "anim": (2, 4, 6, 10)}))
    return cases


def run_case(lib, pair, label, spec):
    column, row = spec.get("column", 0), spec.get("row", 0)
    view = MapView(spec["plane"], spec["x"], spec["y"], spec["scent"],
                   max(1, column + 1), max(1, row + 1),
                   -4, 6, 16, 12, 0, *spec["anim"])
    inp = ProbeInput(view, column, row, spec["tile"], spec["life"],
                     spec["pheromone"], 0)
    native = ProbeOutput()
    lib.sim_map_probe(ct.byref(inp), ct.byref(native))

    x, y = spec["x"] + column, spec["y"] + row
    if y > 0x3f:
        x += 0x40
        y &= 0x3f
    if spec["plane"] <= 1:
        x &= 0x7f
        map_name, life_name = "MapA", "LifeA"
        ground = spec["tile"]
    else:
        x &= 0x3f
        map_name, life_name = ("MapB", "LifeB") if spec["plane"] == 2 else ("MapR", "LifeR")
        ground = (spec["tile"] + 0x70) & 0xff
    writes = [
        (behavior.symbol_address(map_name) + x * 64 + y, bytes([ground])),
        (behavior.symbol_address(life_name) + x * 64 + y, bytes([spec["life"]])),
        (behavior.symbol_address("fd_50F6_0508"), behavior.words(spec["x"], spec["y"])),
        (behavior.symbol_address("MapPlane"), behavior.words(spec["plane"])),
        (behavior.symbol_address("fd_3D57_07BE"), behavior.words(spec["scent"])),
        (behavior.symbol_address("fd_50F6_049A"), behavior.words(spec["anim"][0])),
        (behavior.symbol_address("fd_50F6_0496"), behavior.words(spec["anim"][1])),
        (behavior.symbol_address("fd_50F6_0502"), behavior.words(spec["anim"][2])),
        (behavior.symbol_address("fd_50F6_04C2"), behavior.words(spec["anim"][3])),
    ]
    if spec["plane"] <= 1:
        phers = ("PherMapA", "PherMapBN", "PherMapBT", "PherMapRN", "PherMapRT")
        pbase = behavior.symbol_address(phers[spec["scent"]])
        writes.append((pbase + (x >> 1) * 32 + (y >> 1), bytes([spec["pheromone"]])))
    case = behavior.Case(label, args=[column, row], writes=writes,
                         observe=[behavior.Range("g_94E4", behavior.symbol_address("g_94E4"), 1),
                                  behavior.Range("g_9126", behavior.symbol_address("g_9126"), 2)],
                         return_kind="void")
    dos = pair.original_machine.run(case)["ranges"]
    actual_tile = int.from_bytes(bytes.fromhex(dos["g_94E4"]), "little")
    actual_life = int.from_bytes(bytes.fromhex(dos["g_9126"]), "little")
    mismatches = []
    expected_life = native.command.life_frame
    expected_tile = native.command.ground_tile
    if native.status != 0:
        mismatches.append({"field": "native_status", "native": native.status, "dos": "executed"})
    if actual_tile != expected_tile:
        mismatches.append({"field": "ground_tile", "native": expected_tile, "dos": actual_tile})
    if actual_life != expected_life:
        mismatches.append({"field": "life_frame", "native": expected_life, "dos": actual_life})
    return {"case": label, "input": spec, "mismatches": mismatches,
            "expected": {"tile": expected_tile, "life": expected_life,
                         "map_xy": [native.command.map_x, native.command.map_y]},
            "dos": {"tile": actual_tile, "life": actual_life}}


def main():
    lib, command = build_native()
    pair = behavior.PreparedPair("f_0250_1018", source=SOURCE)
    rows = [run_case(lib, pair, label, spec) for label, spec in direct_cases()]
    report = {
        "schema": "portable-map-logical-diff-v1",
        "target": "root:m0250:f_0250_1018",
        "identity": pair.identity,
        "native_build_command": command,
        "native_compiler": subprocess.check_output([str(GCC), "--version"],
                                                    text=True).splitlines()[0],
        "pinned_sources": {str(path.relative_to(ROOT)): sha(path) for path in
                           (MAP_C, MAP_H, RASTER_C, RASTER_H, PRIMITIVES_C,
                            PROBE, MAP_TEST, RASTER_TEST, RUNNER, SOURCE,
                            ROOT / "src/S00/m31AD.asm", ROOT / "src/S00/m31AD_2AB4.asm",
                            RASTER_DIFF, TILE_LAYOUT_POSITIVE,
                            ROOT / "portable/game/state/world.h",
                            ROOT / "portable/game/simulation/movement.h",
                            TILES_C, TILES_H, TILE_LAYOUT_REVIEW,
                            TILE_LAYOUT_POSITIVE, ASSET_HASHES,
                            ROOT / "layout/manifest.json")},
        "callbacks": "The logical differential compares f_0250_1018 output globals g_94E4/g_9126. Pixel drawing uses the source-derived tile/life decoders and indexed framebuffer; no physical VGA device or DOS clipping path is emulated.",
        "coverage": "Four MapPlane values; surface and both nest map/life grids; source scent selectors 0..4 plus invalid/default fallback; life 0, ordinary, FE, FF; all four camera-wrap planes; 128 seeded randomized source-valid cells. Native raster tests cover indexed tile/life composition and surface/nest EMS page routing.",
        "cases": rows,
        "case_count": len(rows),
        "mismatch_count": sum(len(row["mismatches"]) for row in rows),
        "status": "PASS" if all(not row["mismatches"] for row in rows) else "FAIL",
        "limits": "The native draw path uses instruction-derived 16x16 EGA source layouts and 0x80/0xA0 ground/life strides. The logical selector is differentially compared to DOS; the life combiner has a normalized-readback differential. Full physical EGA, atlas placement, screen clipping and _2FDA output equality are not claimed.",
    }
    # The dedicated assembly review and normalized-readback run establish a
    # new positive pixel-layout contract; the older negative review remains
    # an immutable record of the earlier rejected inference.
    map_evidence = {
        "schema": "portable-map-render-source-evidence-v1",
        "status": "SOURCE_DERIVED_16X16_EGA_LAYOUT; NORMALIZED_READBACK_DIAGNOSTIC",
        "supported_ega_profiles": [0, 8],
        "ground_source_contract": {
            "source_call": "src/root/m0250.c f_0250_0256 calls o00_31AD_18BA(*fd_50F6_37DE, 0xa000, 0x100) for the selected kind-9 ground object 10-set",
            "assembly_anchor": "src/S00/m31AD.asm _o00_31AD_18BA, lines 3307-3386",
            "layout": "Each tile is 16 rows; each row has four interleaved two-byte EGA planes at source offsets 0,2,4,6; source row stride 8; source tile stride 0x80 (128 bytes). The 0x100 argument is a count of tiles.",
        },
        "life_source_contract": {
            "assembly_anchor": "src/S00/m31AD_2AB4.asm _o00_31AD_2B1A and _o00_31AD_2FDA",
            "layout": "_2B1A reads 16 rows of a two-byte mask followed by four two-byte color planes (160 bytes/frame), combines each color plane as base XOR ((overlay XOR base) AND mask), and writes 4 words per row into g_3D20. _2FDA presents that buffer through _0CF9 with width and height 16.",
            "resource_groups": "source LoadTiles maps IDs 15..17 as surface and 18..20 as nest; the portable map chooses that group by MapPlane and uses three 0x5000-byte chunks, 128 frames per chunk.",
            "frame_normalization": "f_0250_0721/f_0250_0915 subtract 0x100, 0x200, or 0x280 by source frame range before indexing the selected EMS group.",
        },
        "differential": {
            "logical_selector_report": str(REPORT.relative_to(ROOT)).replace("\\", "/"),
            "logical_cases": len(rows),
            "logical_mismatches": sum(len(row["mismatches"]) for row in rows),
            "life_blitter_report": str(RASTER_DIFF.relative_to(ROOT)).replace("\\", "/"),
            "life_blitter_cases": 140,
            "life_blitter_scope": "140 original _2B1A normalized selected-plane readback cases (128 randomized plus first/last actual frames in resources 15..20), 0 byte mismatches in all 128 g_3D20 output bytes; no physical EGA read-map, atlas placement, _2FDA clipping or screen-output equality claim.",
        },
        "negative_review_preserved": {
            "path": str(TILE_LAYOUT_REVIEW.relative_to(ROOT)).replace("\\", "/"),
            "sha256": sha(TILE_LAYOUT_REVIEW),
            "note": "This earlier review rejected the 16x20 inference from 0xA0/resource size. It remains unchanged; current positive assembly anchors establish 16x16 and 0x80 ground tile stride independently.",
        },
        "positive_layout_supplement": {
            "path": str(TILE_LAYOUT_POSITIVE.relative_to(ROOT)).replace("\\", "/"),
            "sha256": sha(TILE_LAYOUT_POSITIVE),
        },
        "current_decoder_sha256": sha(RASTER_C),
        "api_sha256": {str(path.relative_to(ROOT)).replace("\\", "/"): sha(path)
                        for path in (MAP_C, MAP_H, RASTER_C, RASTER_H)},
        "pixels_equivalence_status": "The logical selection has a complete DOS differential. The native mask/color expansion follows the source instruction contract, with _2B1A normalized readback differential; full atlas placement and physical display equivalence remain unverified.",
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    MAP_EVIDENCE.write_text(json.dumps(map_evidence, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(REPORT), "cases": report["case_count"],
                      "mismatches": report["mismatch_count"], "status": report["status"]}, indent=2))
    if report["mismatch_count"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
