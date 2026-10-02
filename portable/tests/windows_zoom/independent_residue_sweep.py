#!/usr/bin/env python3
"""Sweep independent first-call mode-0 Rect.right/bottom residues for HCEGANT 0."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    toggle = load("zoom_toggle_independent_v4", ROOT / "portable/tests/windows_zoom/dos_toggle_diff.py")
    values = (0, 1, 23, 24, 350, 640, 0x7fff, -0x8000)
    pairs = [(right, bottom) for right in values for bottom in values]
    original_machine = toggle.behavior.Machine
    active_index = [0]

    class ResidueMachine(original_machine):
        def __init__(self, pair):
            super().__init__(pair)
            target = toggle.functions.get("o26_39C7_022F")
            address = target["seg"] * 16 + target["off"]
            right, bottom = pairs[active_index[0]]

            def set_local_residue(uc, instruction_address, _size, _user):
                if instruction_address != address or uc.reg_read(toggle.behavior.REGS["dx"]) != 0:
                    return
                sp = uc.reg_read(toggle.behavior.REGS["sp"])
                ss = uc.reg_read(toggle.behavior.REGS["ss"])
                off, seg = struct.unpack("<2H", self.read(ss * 16 + sp + 4, 4))
                self.write(seg * 16 + off + 4, struct.pack("<2H", right & 0xffff, bottom & 0xffff))

            self.cpu.hook_add(toggle.behavior.uc.UC_HOOK_CODE, set_local_residue)

    toggle.behavior.Machine = ResidueMachine
    scenario = {
        "id": "hcegant0-independent-mode0-residue",
        "window_rect": (14, 22, 418, 379),
        "frame": (14, 22, 404, 357),
        "object_rect": (14, 22, 418, 379),
        "min_width": 252, "min_height": 280,
        "flags": 0x070e, "grid_x": 16, "grid_y": 16,
        "desktop_top": 24, "screen_right": 640, "screen_bottom": 350,
    }
    cases = []
    for index, (right, bottom) in enumerate(pairs):
        active_index[0] = index
        try:
            result = toggle.setup_case(None, scenario, 0xa5)
        except toggle.behavior.ExecutionError as exc:
            cases.append({"input": [right, bottom], "status": "BUDGET_EXCEEDED", "error": str(exc)})
            continue
        cases.append({
            "input_right_bottom": [right, bottom],
            "captured_mode0_initial_rect": result["mode0_initial_rect"],
            "final_window_rect": result["captured"]["window_rect"],
            "final_frame_geometry": result["captured"]["frame_geometry"],
            "final_zoom_rect": result["captured"]["zoom_rect"],
            "final_flags": result["captured"]["flags"],
            "uninitialized_saved_rect": result["saved_rect"],
            "status": "COMPARED",
        })

    compared = [case for case in cases if case["status"] == "COMPARED"]
    geometry = lambda case: (tuple(case["final_window_rect"]), tuple(case["final_frame_geometry"]),
                             tuple(case["final_zoom_rect"]), case["final_flags"])
    distinct_geometry = sorted({geometry(case) for case in compared})
    report = {
        "schema": "portable-window-zoom-independent-residue-sweep-v4",
        "status": "PASS" if len(compared) == len(pairs) and len(distinct_geometry) == 1 else "DEPENDENCY_OR_INCOMPLETE",
        "claim": "Across an independent 8-by-8 directed sweep of first-call uninitialized mode-0 right/bottom values, the original DOS converges to the same HCEGANT window-0 final geometry. The separate saved rectangle remains stack-residue-dependent as established in resource0-profile-v2; this sweep does not claim redraw/clip equivalence.",
        "scope": {
            "window_profile": "HCEGANT resource 0, opened flags 0x070e, min 252x280, grid 16x16",
            "original_executed": ["o26_39C7_0000", "o26_39C7_022F"],
            "controlled_leaves": "Same pointer, recalc, clipping, callback, and draw boundaries as dos_toggle_diff.setup_case.",
            "screen_inputs": {"desktop_top": 24, "right": 640, "bottom": 350},
            "residue_values_each_axis": list(values),
            "case_count": len(cases), "compared": len(compared),
            "budget_exceeded": len(cases) - len(compared),
            "distinct_final_geometries": len(distinct_geometry),
            "final_geometry": [list(v) if isinstance(v, tuple) else v for v in distinct_geometry[0]] if distinct_geometry else None,
        },
        "pins": {
            "oracle_sha256": toggle.exe.load().sha256,
            "harness_sha256": sha(toggle.behavior.HARNESS_SOURCE),
            "zoom_source_sha256": sha((ROOT / "src/S26/m39C7.c").read_bytes()),
            "toggle_runner_sha256": sha((ROOT / "portable/tests/windows_zoom/dos_toggle_diff.py").read_bytes()),
            "runner_sha256": sha(Path(__file__).read_bytes()),
        },
        "cases": cases,
    }
    out = ROOT / "portable/tests/windows_zoom/evidence/independent-residue-sweep-v4.json"
    if out.exists():
        raise SystemExit(f"refusing to overwrite {out}")
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"{out}: {len(compared)}/{len(cases)} cases; distinct final geometries={len(distinct_geometry)}")
    if report["status"] != "PASS":
        raise SystemExit("independent mode-0 residue sweep did not converge uniformly")


if __name__ == "__main__":
    main()
