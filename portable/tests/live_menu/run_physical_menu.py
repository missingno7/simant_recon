#!/usr/bin/env python3
"""Bounded live SDL check of source SHARED title and row drag/release input."""
from __future__ import annotations

import hashlib
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
PRODUCTION_DLL = ROOT / "build/portable/SDL3.dll"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", required=True, type=Path,
                        help="new evidence receipt path; existing paths are never overwritten")
    args = parser.parse_args()
    source_exe = ROOT / "build/portable/simant-sdl3.exe"
    receipt_path = source_exe.with_suffix(".build.json")
    injector = ROOT / "portable/tests/live_menu/physical_menu_injector.c"
    geometry_probe = ROOT / "portable/tests/live_menu/menu_geometry_probe.c"
    runner = Path(__file__).resolve()
    assets = [ROOT / "assets/SHARED.NDX", ROOT / "assets/SHARED.DAT"]
    report_path = args.report.resolve()
    if not report_path.parent.is_dir():
        print(f"evidence directory missing: {report_path.parent}", file=sys.stderr)
        return 2
    artifact_stem = report_path.stem
    run_path = report_path.with_name(f"{artifact_stem}-events.json")
    geometry_path = report_path.with_name(f"{artifact_stem}-geometry.json")
    state_base = report_path.with_name(f"{artifact_stem}-state")
    state_paths = [Path(str(state_base) + suffix) for suffix in
                   (".recovered.bin", ".normalized.bin", ".rng.bin", ".stats.json")]
    frame_path = report_path.with_name(f"{artifact_stem}-frame.bmp")
    test_dir = ROOT / "build/portable/tests" / artifact_stem
    out = test_dir / "live-menu-physical.exe"
    if not source_exe.is_file() or not receipt_path.is_file() or not PRODUCTION_DLL.is_file():
        print("Next8 executable, build receipt, or SDL3.dll is missing", file=sys.stderr)
        return 2
    planned_outputs = [report_path, run_path, geometry_path, frame_path,
                      *state_paths, out, test_dir / "SDL3.dll"]
    existing_outputs = [str(path) for path in planned_outputs if path.exists()]
    if existing_outputs:
        print("refusing to overwrite evidence or test outputs: " +
              ", ".join(existing_outputs), file=sys.stderr)
        return 2
    receipt_bytes_before = sha(receipt_path)
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    profile = receipt.get("recovered_core", {}).get("profile")
    if profile != "build/workers/recovered_source_next8/generated":
        print(f"unexpected recovered-core profile: {profile!r}", file=sys.stderr)
        return 2
    expected_exe = receipt.get("executable_sha256")
    expected_dll = receipt.get("sdl_library_sha256")
    if sha(source_exe) != expected_exe or sha(PRODUCTION_DLL) != expected_dll:
        print("production executable or SDL3.dll does not match its receipt", file=sys.stderr)
        return 2
    pins = {str(path): expected for path, expected in receipt["inputs"].items()}
    before = {path: sha(ROOT / path) for path in pins}
    mismatched_before = [path for path, expected in pins.items()
                         if before[path] != expected]
    if mismatched_before:
        print("production compiler closure differs from receipt: " +
              ", ".join(mismatched_before[:8]), file=sys.stderr)
        return 2
    input_paths = [runner, injector, geometry_probe, *assets]
    test_source_before = {str(path.relative_to(ROOT)): sha(path)
                          for path in input_paths}
    test_dir.mkdir(parents=True, exist_ok=False)
    command = list(receipt["command"])
    try:
        output_index = command.index("-o")
        command[output_index + 1] = str(out)
        library_index = command.index("-L")
    except (ValueError, IndexError, KeyError):
        print("production build receipt lacks reusable command", file=sys.stderr)
        return 2
    command.insert(library_index, "-DSIMANT_LIVE_GAME_TEST_DIAGNOSTICS=1")
    command.insert(library_index + 1, str(injector))
    linked = subprocess.run(command, cwd=ROOT, text=True,
                            capture_output=True, check=False)
    if linked.returncode != 0:
        print(linked.stdout + linked.stderr, file=sys.stderr)
        return linked.returncode
    test_dll = test_dir / "SDL3.dll"
    shutil.copy2(PRODUCTION_DLL, test_dll)
    env = dict(os.environ)
    env["SDL_VIDEODRIVER"] = "dummy"
    env["SIMANT_LIVE_SMOKE_EVENT_REPORT"] = str(run_path)
    env["SIMANT_LIVE_SMOKE_STATE_REPORT"] = str(state_base)
    env["SIMANT_LIVE_MENU_GEOMETRY_REPORT"] = str(geometry_path)
    timeout = 90
    try:
        result = subprocess.run([str(out), "--live-newgame", "--ticks", "32",
                                 "--screenshot", str(frame_path)], cwd=ROOT,
                                env=env, text=True, capture_output=True,
                                timeout=timeout, check=False)
        timed_out = False
        stdout, stderr, return_code = result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired as error:
        timed_out = True
        stdout = error.stdout.decode(errors="replace") if isinstance(error.stdout, bytes) else (error.stdout or "")
        stderr = error.stderr.decode(errors="replace") if isinstance(error.stderr, bytes) else (error.stderr or "")
        return_code = None

    after = {path: sha(ROOT / path) for path in pins}
    receipt_hash_after = sha(receipt_path)
    closure_unchanged = before == after and receipt_bytes_before == receipt_hash_after
    state_ready = all(path.is_file() for path in state_paths)
    stats = json.loads(state_paths[3].read_text(encoding="utf-8")) if state_ready else None
    events = json.loads(run_path.read_text(encoding="utf-8")) if run_path.is_file() else None
    geometry = json.loads(geometry_path.read_text(encoding="utf-8")) if geometry_path.is_file() else None
    passed = (not timed_out and return_code == 0 and closure_unchanged and
              "Native NewGame scenario=" in stdout and
              "Completed native simulation ticks: 32" in stdout and
              stats is not None and stats["completed_ticks"] == 32 and
              stats["source_speed"] == 0 and
              stats["speed_action_calls"] == [0, 0, 0, 0] and
              stats["pause_action_calls"] == 0 and stats["source_pause"] == 0 and
              stats["paused_update_calls"] > 0 and stats["menu_item_state_calls"] == 30 and
              stats["menu_item_text_calls"] == 3 and
              events is not None and events["interaction_count"] == 3 and
              events["pushed_event_count"] == 9 and events["injection_failures"] == 0 and
              events["paused_window_ns"] >= 500_000_000 and
              geometry is not None and frame_path.is_file())
    report = {
        "schema": "portable-live-physical-menu-test-v1",
        "status": "PASS" if passed else "FAIL",
        "claim": "A test-only SDL timer selected the actual resource-backed Speed title, dragged to its Slow row, then dragged to the actual Pause/Unpause row twice; the original S11 ProcMenu actions ran in a bounded native NewGame session.",
        "proof_boundary": "Finite live SDL host integration only; does not claim DOS state equivalence or framebuffer equivalence.",
        "production_profile": profile,
        "execution": {"arguments": ["--live-newgame", "--ticks", "32"],
                      "sdl_video_driver": "dummy", "timeout_seconds": timeout,
                      "timed_out": timed_out, "return_code": return_code,
                      "stdout": stdout, "stderr": stderr},
        "source_resource_geometry": geometry,
        "injected_events": events,
        "final_diagnostics": stats,
        "source_closure": {
            "build_receipt": {"path": str(receipt_path),
                              "sha256_before": receipt_bytes_before,
                              "sha256_after": receipt_hash_after,
                              "inputs_before": before, "inputs_after": after,
                              "unchanged": closure_unchanged},
            "production_executable": {"path": str(source_exe),
                                      "sha256": sha(source_exe)},
            "production_sdl3_dll": {"path": str(PRODUCTION_DLL),
                                    "sha256": sha(PRODUCTION_DLL)},
            "test_executable": {"path": str(out), "sha256": sha(out)},
            "test_sdl3_dll": {"path": str(test_dll), "sha256": sha(test_dll)},
            "test_inputs_before": test_source_before,
            "test_inputs_after": {str(path.relative_to(ROOT)): sha(path)
                                  for path in input_paths},
            "compiler_command": command,
        },
        "final_artifacts": {
            "event_report": ({"path": str(run_path), "sha256": sha(run_path)}
                             if run_path.is_file() else None),
            "geometry_report": ({"path": str(geometry_path), "sha256": sha(geometry_path)}
                                if geometry_path.is_file() else None),
            "state_files": {
                name: {"path": str(path), "sha256": sha(path)}
                for name, path in zip(("recovered", "normalized", "rng", "statistics"),
                                      state_paths) if path.is_file()},
            "screenshot": ({"path": str(frame_path), "sha256": sha(frame_path)}
                           if frame_path.is_file() else None),
        },
        "passed": passed,
    }
    if report_path.exists():
        raise FileExistsError(f"refusing to overwrite evidence receipt: {report_path}")
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "report": str(report_path),
                      "events": events, "diagnostics": stats,
                      "return_code": return_code, "stdout": stdout,
                      "stderr": stderr}, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
