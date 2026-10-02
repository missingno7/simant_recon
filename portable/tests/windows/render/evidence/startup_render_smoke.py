#!/usr/bin/env python3
"""Build and archive a source-pinned native startup-window render smoke."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parents[1]
OUT = HERE / "evidence" / "startup_render_smoke.json"
BUILD = ROOT / "build" / "workers" / "behavior_tutorial_menu" / "bios-font-provider-checks"
BIOS_DIR = ROOT / "build" / "bios-reference" / "dosbox-staging-v0.83.0"
BIOS_ID = "DOSBox Staging/v0.83.0/7b40053b7ac580843d0461eba8c36a47a990e66c"
CC = "gcc"
COMMON = [
    "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror", "-Iportable",
    "portable/ui_model/windows/render.c",
    "portable/ui_model/windows/window.c",
    "portable/game/resources/database.c",
    "portable/render/bitmap.c",
    "portable/render/font.c",
    "portable/render/primitives.c",
    "portable/game/resources/bios_fonts.c",
]
INPUTS = [
    "portable/ui_model/windows/render.h",
    "portable/ui_model/windows/render.c",
    "portable/ui_model/windows/window.h",
    "portable/ui_model/windows/window.c",
    "portable/game/resources/database.h",
    "portable/game/resources/database.c",
    "portable/render/bitmap.h",
    "portable/render/bitmap.c",
    "portable/render/font.h",
    "portable/render/font.c",
    "portable/render/primitives.h",
    "portable/render/primitives.c",
    "portable/tests/windows/render/test_startup_render.c",
    "portable/tests/windows/render/test_object_render_coverage.c",
    "portable/tests/windows/render/test_formatted_text_projection.c",
    "portable/tests/windows/render/test_bios_fonts_loader.c",
    "portable/game/resources/bios_fonts.h",
    "portable/game/resources/bios_fonts.c",
    "portable/tests/windows/render/BIOS_REFERENCE.md",
    "portable/tests/windows/render/evidence/fetch_bios_reference.py",
    "src/root/m21FA.c",
    "src/root/m24AB.c",
    "src/root/m1CE2.c",
    "src/root/m1B4E.asm",
    "assets/HCEGANT.NDX",
    "assets/HCEGANT.DAT",
    "assets/FONT1",
    "assets/FONT2",
    "assets/FONT3",
    "assets/FONT4",
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_case(name: str, sources: list[str], bios_args: list[str]) -> str:
    exe = BUILD / f"{name}.exe"
    command = [CC, *COMMON[:6], *sources, *COMMON[6:], "-o", str(exe)]
    subprocess.run(command, cwd=ROOT, check=True)
    result = subprocess.run([str(exe), str(ROOT / "assets"), *bios_args], cwd=ROOT,
                            check=True, text=True, capture_output=True)
    return result.stdout.strip()


def main() -> int:
    BUILD.mkdir(parents=True, exist_ok=True)
    bios_files = [BIOS_DIR / "font-8x8.bin", BIOS_DIR / "font-8x14.bin"]
    manifest_path = BIOS_DIR / "manifest.json"
    use_bios_reference = manifest_path.is_file() and all(path.is_file() for path in bios_files)
    bios_args = [str(path) for path in bios_files] + [BIOS_ID] if use_bios_reference else []
    startup = run_case("startup_render_smoke", [
        "portable/tests/windows/render/test_startup_render.c",
    ], bios_args)
    coverage = run_case("object_render_coverage", [
        "portable/tests/windows/render/test_object_render_coverage.c",
    ], bios_args)
    projection = run_case("formatted_text_projection", [
        "portable/tests/windows/render/test_formatted_text_projection.c",
    ], [str(ROOT / "assets" / "FONT1")])
    bios_loader = run_case("bios_fonts_loader", [
        "portable/tests/windows/render/test_bios_fonts_loader.c",
    ], [str(BIOS_DIR)])
    if "window=25 objects=22 pixels_sha_fnv1a=" not in startup:
        raise RuntimeError("the control window did not complete its full draw")
    expected_unsupported = 0 if use_bios_reference else 2
    if f"explicit_unsupported_objects={expected_unsupported}" not in coverage:
        raise RuntimeError("startup object coverage changed; inspect and update the evidence")
    if use_bios_reference and "window=18 objects=18 pixels_sha_fnv1a=" not in startup:
        raise RuntimeError("reference BIOS tables did not complete the startup window draw")
    report = {
        "schema": "native-startup-window-render-smoke-v1",
        "kind": "asset and renderer smoke; not DOS framebuffer equivalence",
        "compiler": CC,
        "flags": COMMON[:6],
        "source_files": COMMON[6:] + [
            "portable/tests/windows/render/test_startup_render.c",
            "portable/tests/windows/render/test_object_render_coverage.c",
        ],
        "input_sha256": {name: sha(ROOT / name) for name in INPUTS},
        "bios_reference": ({
            "provider_id": BIOS_ID,
            "manifest_sha256": sha(manifest_path),
            "font8x8_sha256": sha(bios_files[0]),
            "font8x14_sha256": sha(bios_files[1]),
            "status": "optional host reference tables; not proof of the original machine BIOS",
        } if use_bios_reference else {"status": "not available; DOS driver font objects remain unsupported"}),
        "startup_windows": [0, 1, 18, 19, 25],
        "full_render_stdout": startup,
        "isolated_object_coverage_stdout": coverage,
        "formatted_text_projection_stdout": projection,
        "bios_fonts_loader_stdout": bios_loader,
        "result": {
            "full_render_windows": ([0, 1, 18, 19, 25] if use_bios_reference else [0, 1, 25]),
            "full_render_blocked_windows": ({} if use_bios_reference else {
                "18": "object 1 type 18 selects BIOS font 0; no BIOS table provider was supplied",
                "19": "object 1 type 18 selects BIOS font 0; no BIOS table provider was supplied",
            }),
            "isolated_supported_objects": (97 if use_bios_reference else 95),
            "isolated_explicit_unsupported_objects": expected_unsupported,
            "unsupported_font_contract": {
                "source": "src/root/m24AB.c:f_24AB_02AD",
                "meaning": "font IDs 0 and 1 select the screen-width-dependent g_912C/g_9130 driver font; IDs 2..5 use FONT1..FONT4",
            },
            "pixel_equivalence": "not tested: the provider contract is source-differential for glyph selection/geometry, while the display-driver callback is native; DOSBox Staging font tables are a host reference and are not asserted authentic to the original target BIOS",
        },
    }
    OUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(OUT), "sha256": sha(OUT),
                      "complete_windows": report["result"]["full_render_windows"],
                      "unsupported": report["result"]["full_render_blocked_windows"]},
                     indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
