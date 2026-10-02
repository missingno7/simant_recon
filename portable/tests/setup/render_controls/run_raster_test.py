"""Build and exercise control command plans over current HCEGANT resources."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import re

ROOT = Path(__file__).resolve().parents[4]
GCC = Path("C:/msys64/mingw64/bin/gcc.exe")
OUT = ROOT / "build/workers/controls-render/raster-test.exe"
REPORT = ROOT / "portable/tests/setup/render_controls/evidence/control-window-raster.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    sources = [
        "portable/ui_model/windows/control_render/control_render.c",
        "portable/ui_model/windows/control_render/control_raster.c",
        "portable/ui_model/windows/control_render/control_input_from_session.c",
        "portable/ui_model/windows/registry.c",
        "portable/ui_model/windows/window.c",
        "portable/game/resources/database.c",
        "portable/game/resources/fonts.c",
        "portable/game/simulation/setup.c",
        "portable/render/bitmap.c",
        "portable/render/font.c",
        "portable/render/primitives.c",
        "portable/tests/setup/render_controls/test_control_raster.c",
    ]
    pinned_headers = [
        "portable/ui_model/windows/control_render/control_render.h",
        "portable/ui_model/windows/control_render/control_raster.h",
        "portable/ui_model/windows/control_render/control_input_from_session.h",
    ]
    subprocess.run([str(GCC), "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
                    "-I", str(ROOT / "portable"),
                    *[str(ROOT / source) for source in sources], "-o", str(OUT)],
                   cwd=ROOT, check=True)
    result = subprocess.run([str(OUT), str(ROOT / "assets")], cwd=ROOT,
                            check=True, text=True, capture_output=True)
    print(result.stdout, end="")
    runs = []
    provider_geometry = []
    for line in result.stdout.splitlines():
        geometry = re.fullmatch(
            r"geometry window=(\d+) object4=(-?\d+),(-?\d+),(-?\d+),(-?\d+) object12=(-?\d+),(-?\d+),(-?\d+),(-?\d+) object13=(-?\d+),(-?\d+),(-?\d+),(-?\d+)",
            line)
        if geometry:
            values = [int(value) for value in geometry.groups()]
            provider_geometry.append({
                "resource_window_id": values[0],
                "object4_rect": values[1:5],
                "object12_rect": values[5:9],
                "object13_rect": values[9:13],
            })
        match = re.fullmatch(
            r"window=(\d+) pixels=(\d+) hash=([0-9a-f]+) point=(-?\d+),(-?\d+) rect=(-?\d+),(-?\d+),(-?\d+),(-?\d+)",
            line)
        if match:
            window, count, image_hash, px, py, left, top, right, bottom = match.groups()
            runs.append({"resource_window_id": int(window), "nonzero_pixels": int(count),
                         "indexed_framebuffer_fnv1a64": image_hash,
                         "setup_point": [int(px), int(py)],
                         "object_12_rect": [int(left), int(top), int(right), int(bottom)]})
    if [run["resource_window_id"] for run in runs] != [18, 19] or \
            [item["resource_window_id"] for item in provider_geometry] != [18, 19]:
        raise AssertionError("raster test did not produce both control windows/providers")
    if "caller z-order clip preserved" not in result.stdout:
        raise AssertionError("caller z-order clip preservation was not verified")
    if "active animation identity/pointer validation PASS" not in result.stdout:
        raise AssertionError("active animation ownership identity was not checked")
    report = {
        "schema": "portable-controls-window-raster-v1",
        "status": "PASS_RESOURCE_BACKED_PLAN_RASTER_NO_DOS_PIXEL_CLAIM",
        "command_trace_report_sha256": sha(ROOT / "portable/tests/setup/render_controls/evidence/control-window-render-trace.json"),
        "source_sha256": {
            source: sha(ROOT / source) for source in [*sources, *pinned_headers]
        } | {"portable/tests/setup/render_controls/run_raster_test.py": sha(Path(__file__))},
        "binary_sha256": sha(OUT),
        "assets_sha256": {
            name: sha(ROOT / name) for name in (
                "assets/HCEGANT.NDX", "assets/HCEGANT.DAT",
                "assets/FONT4",
            )
        },
        "solid_fill_boundary": {
            "source_callback": "g_9134 resolves to the fourth slot of g_3DF8's driver-entry table; frozen source target S00 o00_31AD_16A9 swaps edge operands, then o00_31AD_1702/1736 selects the low EGA color nibble and fills the indexed plane.",
            "source_sha256": sha(ROOT / "src/S00/m31AD.asm"),
            "projection": "Source low nibble becomes the 0..15 palette index; high nibble/backend operation state is excluded from the indexed framebuffer projection.",
            "coordinate_scope": "Visible setup-window rects and computed setup points are nonnegative. The original fill compares coordinate words unsigned; the adapter rejects negative source rects and intersects window clip with caller clip.",
        },
        "input_contract": "Current SimSession setup_controls, control-visual ownership, current HCEGANT database and registry profile 0; current kind-0 windows 18/19 after recalculate; current kind-2 bitmap 0x578; real FONT4; current win_colors from HCEGANT kind 0x81; screen width from active renderer. The binder requires current g_1B62/g_1B64 plus mode fd_50F6_0B12[0..2] through SimControlRecoveredVisualState; it derives caste fd_50F6_0AEC[0] from session.world.population_black[0]. Source-immutable g_1B4A/g_1B46 arrays are supplied from their exact m0798.c initializers. Current g_3DE2 must be overridden in the binding if changed from source initial value 0.",
        "source_state_policy": {
            "private_control_globals_sha256": sha(ROOT / "src/root/m0798.c"),
            "session_world_mapping_sha256": sha(ROOT / "portable/game/recovered/session_bridge.c"),
            "percent_and_mode_total": "Explicit caller state; these DOS globals/counters are not members of SimSession.",
            "fixed_component_colors": "Source initializers {40,43,39} and {36,38,34}; source search shows no writes to either array. The builder copies them as immutable component colors.",
            "animation_identity_policy": "Bind handle/object ID only when the provider resource pointer exactly equals the currently owned SimSessionControlVisual.animation_resource; mismatch fails closed.",
        },
        "scope": "Rasterizes the initial source-derived control plan over an indexed framebuffer. It draws centered numeric text and its source background clearing, bars, separator bands, outlines, and resource-backed knob bitmap. Existing exact command-trace evidence is linked above.",
        "caller_clip_test": "PASS: raster intersects source window clipping with an existing caller occlusion clip and restores that clip after composition.",
        "active_animation_identity_test": "PASS: validates the live session animation resource pointer against caller-supplied set/object identity, and rejects mismatched identity.",
        "limitations": [
            "No direct DOS framebuffer/pixel comparison was run; only the normalized ordered DOS command stream is independently compared.",
            "The report covers the control overlay on a cleared framebuffer, not the complete Mode/Caste window background or application z-order.",
            "The animation resolver path requires a caller-supplied resolver tied to the active session; tests cover initial resource acquisition only.",
            "The caller must supply current g_3DE2 drawing state; this test uses its source initial value 0.",
        ],
        "runs": runs,
        "active_provider_geometry": provider_geometry,
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"PASS: rasterized initial controls using {len(sources)-1} C source files")


if __name__ == "__main__":
    main()
