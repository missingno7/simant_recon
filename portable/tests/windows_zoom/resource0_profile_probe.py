#!/usr/bin/env python3
"""Probe S26 zoom stack-residue dependence with the real HCEGANT window 0 resource."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    toggle = load_module("zoom_toggle_v1", ROOT / "portable/tests/windows_zoom/dos_toggle_diff.py")
    resource_helpers = load_module(
        "window_resource_helpers",
        ROOT / "portable/tests/windows/evidence/differential_window.py")
    payload, flags = resource_helpers.resource_payload("HCEGANT", 0, 0)
    count = struct.unpack_from("<H", payload, 0x0c)[0]
    min_width, min_height = struct.unpack_from("<hh", payload, 0x18)
    resource_flags = struct.unpack_from("<H", payload, 0x1c)[0]
    grid_x, grid_y = struct.unpack_from("<hh", payload, 0x20)
    frame_offset = struct.unpack_from("<H", payload, 0x2c)[0]
    frame_raw = struct.unpack_from("<4h", payload, frame_offset + 8)
    frame_visible = struct.unpack_from("<4h", payload, frame_offset)
    resource_win_rect = struct.unpack_from("<4h", payload, 0)

    # win_Open sets the open bit after win_LoadWindow copies this resource.
    # These dimensions and desktop top are explicit run inputs, not guessed
    # stack values. The stack bytes are swept independently below.
    runtime_flags = resource_flags | 0x0200
    base = {
        "window_rect": resource_win_rect,
        "frame": frame_raw,
        "object_rect": frame_visible,
        "min_width": min_width,
        "min_height": min_height,
        "flags": runtime_flags,
        "grid_x": grid_x,
        "grid_y": grid_y,
        "desktop_top": 24,
        "screen_right": 640,
        "screen_bottom": 350,
    }

    cases = []
    for poison in (0x00, 0x11, 0x33, 0x5a, 0x80, 0xa5, 0xff):
        scenario = {**base, "id": f"hcegant0-stack-{poison:02x}", "poison": poison}
        observation = toggle.setup_case(None, scenario, poison)
        cases.append({
            "id": scenario["id"],
            "stack_poison_byte": poison,
            "mode0_initial_rect": observation["mode0_initial_rect"],
            "uninitialized_saved_rect": observation["saved_rect"],
            "final_window_rect": observation["captured"]["window_rect"],
            "final_frame_geometry": observation["captured"]["frame_geometry"],
            "final_zoom_rect": observation["captured"]["zoom_rect"],
            "final_flags": observation["captured"]["flags"],
            "first_saved_rect_consumers": [
                {"service": event["service"], "args": event.get("args", []),
                 "rect": event.get("rect")}
                for event in observation["events"]
                if event["service"] in ("f_1E57_0D97", "f_1E57_0FDC")
            ],
            "dos_exit": observation["dos"],
        })

    geometry_fields = ("final_window_rect", "final_frame_geometry", "final_zoom_rect", "final_flags")
    geometry_invariant = all(
        all(case[field] == cases[0][field] for field in geometry_fields)
        for case in cases[1:])
    saved_values = {tuple(case["uninitialized_saved_rect"]) for case in cases}
    saved_rect_consumed = all(case["first_saved_rect_consumers"] for case in cases)
    report = {
        "schema": "portable-window-zoom-resource-profile-residue-v2",
        "status": "DEPENDENCY_FOUND" if len(saved_values) > 1 and saved_rect_consumed else "INCONCLUSIVE",
        "claim": "For HCEGANT window resource 0, final zoom geometry is invariant across the tested stack byte residues, but the uninitialized saved rectangle varies and is passed to f_1E57_0D97. Source f_1E57_0D97 delegates to f_1E57_0C2D, which intersects the supplied rectangle with the current clip list and replaces that list. Thus both the observed callback argument and source-defined clip-list result depend on saved-rectangle residue; geometry alone is invariant.",
        "boundary": "Original DOS o26_39C7_0000 and o26_39C7_022F execute. win_Lock/Unlock, Win pointer access, win_Recalc, clip/draw services, and the indirect callback are controlled leaves from dos_toggle_diff.setup_case. The runtime record is populated from the actual raw HCEGANT kind-0 resource fields, with win_Open's source-backed open bit applied. Source-level downstream clip effect is grounded in src/root/m1E57.c but the helper body is not executed in this profile probe. This is not an end-to-end NewGame execution.",
        "resource": {
            "database": "HCEGANT", "resource_id": 0, "kind": 0,
            "record_flags": flags,
            "payload_sha256": sha(payload), "payload_size": len(payload),
            "object_count": count,
            "runtime_flags_before_toggle": runtime_flags,
            "resource_window_rect": resource_win_rect,
            "frame_raw_xywh": frame_raw,
            "frame_resource_rect": frame_visible,
            "minimum_width_height": [min_width, min_height],
            "grid_xy": [grid_x, grid_y],
        },
        "bounds_inputs": {"desktop_top": 24, "screen_right": 640, "screen_bottom": 350,
                          "basis": "desktop_top is supplied as a profile input; screen dimensions are the HCEGANT profile's 640x350 mode."},
        "coverage": {"stack_poison_bytes": [0, 17, 51, 90, 128, 165, 255],
                     "case_count": len(cases),
                     "final_geometry_invariant": geometry_invariant,
                     "distinct_saved_rects": len(saved_values),
                     "saved_rect_observed_by_original_helpers": saved_rect_consumed},
        "pins": {
            "oracle_sha256": toggle.exe.load().sha256,
            "harness_sha256": sha(toggle.behavior.HARNESS_SOURCE),
            "zoom_source_sha256": sha((ROOT / "src/S26/m39C7.c").read_bytes()),
            "toggle_runner_sha256": sha((ROOT / "portable/tests/windows_zoom/dos_toggle_diff.py").read_bytes()),
            "resource_helper_sha256": sha((ROOT / "portable/tests/windows/evidence/differential_window.py").read_bytes()),
            "clip_source_sha256": sha((ROOT / "src/root/m1E57.c").read_bytes()),
            "hcegant_ndx_sha256": sha((ROOT / "assets/HCEGANT.NDX").read_bytes()),
            "hcegant_dat_sha256": sha((ROOT / "assets/HCEGANT.DAT").read_bytes()),
        },
        "cases": cases,
    }
    out = ROOT / "portable/tests/windows_zoom/evidence/resource0-profile-v2.json"
    if out.exists():
        raise SystemExit(f"refusing to overwrite {out}")
    out.write_text(json.dumps(report, indent=2) + "\n")
    print(f"{out}: {len(cases)} cases; geometry invariant={geometry_invariant}; distinct saved rects={len(saved_values)}")
    if report["status"] != "DEPENDENCY_FOUND":
        raise SystemExit("expected original saved-rectangle residue dependence was not observed")


if __name__ == "__main__":
    main()
