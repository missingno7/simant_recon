#!/usr/bin/env python3
"""Bounded physical SDL exercise of the source History graph window."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
PROFILE = "build/workers/recovered_source_next10/generated"
HISTORY_PAIR = ROOT / "portable/tests/history_event_lowering/comparison_report_closure_next10.json"
HISTORY_ABI = ROOT / "portable/tests/history_event_lowering/history_adapter_report.json"
MENU_PAIR = ROOT / "portable/tests/menus/evidence/procmenu-next7-dos-differential-adapter-complete-closure-20261002.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", required=True, type=Path,
                        help="new report path; the runner refuses to overwrite")
    parser.add_argument("--timeout", type=int, default=90,
                        help="bounded live-process timeout in seconds")
    args = parser.parse_args()
    report_path = args.report.resolve()
    if not report_path.parent.is_dir():
        print(f"evidence directory missing: {report_path.parent}", file=sys.stderr)
        return 2
    stem = report_path.stem
    event_path = report_path.with_name(f"{stem}-events.json")
    progress_path = report_path.with_name(f"{stem}-progress.json")
    geometry_path = report_path.with_name(f"{stem}-geometry.json")
    engine_trace_path = report_path.with_name(f"{stem}-engine-events.jsonl")
    pointer_trace_path = report_path.with_name(f"{stem}-pointer-events.jsonl")
    host_trace_path = report_path.with_name(f"{stem}-host-events.jsonl")
    menu_trace_path = report_path.with_name(f"{stem}-menu-events.jsonl")
    state_base = report_path.with_name(f"{stem}-state")
    stats_path = Path(str(state_base) + ".stats.json")
    screenshot = report_path.with_name(f"{stem}-frame.bmp")
    source_exe = ROOT / "build/portable/simant-sdl3.exe"
    receipt_path = source_exe.with_suffix(".build.json")
    sdl_dll = ROOT / "build/portable/SDL3.dll"
    injector = ROOT / "portable/tests/live_history/history_injector.c"
    runner = Path(__file__).resolve()
    assets = [ROOT / "assets/SHARED.NDX", ROOT / "assets/SHARED.DAT",
              ROOT / "assets/HCEGANT.NDX", ROOT / "assets/HCEGANT.DAT"]
    required = (source_exe, receipt_path, sdl_dll, HISTORY_PAIR, HISTORY_ABI, MENU_PAIR,
                *assets)
    if not all(path.is_file() for path in required):
        print("production executable/receipt/SDL DLL, oracle receipts, or assets are missing",
              file=sys.stderr)
        return 2
    outputs = [report_path, event_path, progress_path, geometry_path, engine_trace_path,
               pointer_trace_path, stats_path, screenshot,
               host_trace_path,
               menu_trace_path,
               Path(str(state_base) + ".recovered.bin"),
               Path(str(state_base) + ".normalized.bin"),
               Path(str(state_base) + ".rng.bin")]
    if any(path.exists() for path in outputs):
        print("refusing to overwrite: " + ", ".join(str(p) for p in outputs if p.exists()),
              file=sys.stderr)
        return 2
    receipt_before_sha = sha(receipt_path)
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if receipt.get("recovered_core", {}).get("profile") != PROFILE:
        print("production receipt is not the stable Next10 profile", file=sys.stderr)
        return 2
    if receipt.get("executable_sha256") != sha(source_exe) or \
       receipt.get("sdl_library_sha256") != sha(sdl_dll):
        print("production executable/SDL DLL does not match the receipt", file=sys.stderr)
        return 2
    production_closure = {str(k): str(v) for k, v in receipt["inputs"].items()}
    production_before = {name: sha(ROOT / name) for name in production_closure}
    if production_before != production_closure:
        print("production input closure differs from the stable receipt", file=sys.stderr)
        return 2
    pair = json.loads(HISTORY_PAIR.read_text(encoding="utf-8"))
    abi = json.loads(HISTORY_ABI.read_text(encoding="utf-8"))
    menu = json.loads(MENU_PAIR.read_text(encoding="utf-8"))
    generated_s24 = ROOT / PROFILE / "S24_m39C7.c"
    scenarios = pair.get("dos_native_events", {})
    expected_scenarios = ("add_first", "add_to_partial_list",
                          "add_at_capacity_evict_oldest", "remove_first_slot",
                          "remove_middle_slot_1", "remove_middle_slot_2",
                          "remove_last_slot")
    pair_valid = (pair.get("status") == "PASS" and
                  pair.get("next10_generated_s24_sha256") == sha(generated_s24) and
                  all(name in scenarios for name in expected_scenarios) and
                  sum(len(scenarios[name].get("events", [])) for name in scenarios) == 29 and
                  all(row.get("source_state_equal") and row.get("callback_order_equal")
                      for scenario in scenarios.values() for row in scenario.get("events", [])))
    abi_valid = (abi.get("status") == "PASS" and
                 abi.get("dos_state_comparison", {}).get("event_count") == 29 and
                 abi.get("dos_state_comparison", {}).get("baseline_receipt_sha256") ==
                 sha(HISTORY_PAIR))
    menu_valid = (menu.get("status") == "PASS" and menu.get("case_count") == 84 and
                  menu.get("mismatch_count") == 0 and any(
                      row.get("title", "").lower() == "window" and
                      row.get("label", "").lower() == "history" and
                      row.get("menu_index") == 1 and
                      row.get("item_index") == 4 and
                      row.get("command_id") == 0x15
                      for row in menu.get("SHARED_menu_mapping", {}).get("actual_items", [])))
    test_inputs = [runner, injector, HISTORY_PAIR, HISTORY_ABI, MENU_PAIR, *assets]
    test_before = {str(path.relative_to(ROOT)): sha(path) for path in test_inputs}
    test_dir = ROOT / "build/portable/tests" / stem
    test_dir.mkdir(parents=True, exist_ok=False)
    test_exe = test_dir / "live-history.exe"
    command = list(receipt["command"])
    try:
        out_at = command.index("-o")
        command[out_at + 1] = str(test_exe)
        link_at = command.index("-L")
    except (ValueError, IndexError, KeyError):
        print("build receipt command cannot be reused for the diagnostic executable",
              file=sys.stderr)
        return 2
    command.insert(link_at, "-Wl,--wrap=host_poll_event")
    command.insert(link_at + 1, "-Wl,--wrap=sim_recovered_engine_history_event")
    command.insert(link_at + 2, "-Wl,--wrap=sim_recovered_engine_proc_menu_command")
    command.insert(link_at + 3, "-DSIMANT_LIVE_GAME_TEST_DIAGNOSTICS=1")
    command.insert(link_at + 4, str(injector))
    compiled = subprocess.run(command, cwd=ROOT, capture_output=True, text=True,
                              check=False)
    if compiled.returncode:
        print(compiled.stdout + compiled.stderr, file=sys.stderr)
        return compiled.returncode
    test_dll = test_dir / "SDL3.dll"
    shutil.copy2(sdl_dll, test_dll)
    env = dict(os.environ)
    env["SDL_VIDEODRIVER"] = "dummy"
    env["SIMANT_LIVE_HISTORY_GEOMETRY_REPORT"] = str(geometry_path)
    env["SIMANT_LIVE_HISTORY_EVENT_REPORT"] = str(event_path)
    env["SIMANT_LIVE_HISTORY_EVENT_PROGRESS"] = str(progress_path)
    env["SIMANT_LIVE_HISTORY_EVENT_TRACE"] = str(engine_trace_path)
    env["SIMANT_LIVE_CONTROL_INPUT_TRACE"] = str(pointer_trace_path)
    env["SIMANT_LIVE_HISTORY_HOST_TRACE"] = str(host_trace_path)
    env["SIMANT_LIVE_HISTORY_MENU_TRACE"] = str(menu_trace_path)
    env["SIMANT_LIVE_SMOKE_STATE_REPORT"] = str(state_base)
    timeout = args.timeout
    try:
        result = subprocess.run([str(test_exe), "--live-newgame", "--ticks", "32",
                                 "--screenshot", str(screenshot)], cwd=ROOT, env=env,
                                capture_output=True, text=True, timeout=timeout,
                                check=False)
        timed_out, return_code = False, result.returncode
        stdout, stderr = result.stdout, result.stderr
    except subprocess.TimeoutExpired as error:
        timed_out, return_code = True, None
        stdout = error.stdout.decode(errors="replace") if isinstance(error.stdout, bytes) else (error.stdout or "")
        stderr = error.stderr.decode(errors="replace") if isinstance(error.stderr, bytes) else (error.stderr or "")
    production_after = {name: sha(ROOT / name) for name in production_closure}
    receipt_after_sha = sha(receipt_path)
    production_stable = production_before == production_after and receipt_before_sha == receipt_after_sha
    test_after = {str(path.relative_to(ROOT)): sha(path) for path in test_inputs}
    test_stable = test_before == test_after
    geometry = json.loads(geometry_path.read_text(encoding="utf-8")) if geometry_path.is_file() else None
    events = json.loads(event_path.read_text(encoding="utf-8")) if event_path.is_file() else None
    progress = json.loads(progress_path.read_text(encoding="utf-8")) if progress_path.is_file() else None
    engine_events = jsonl(engine_trace_path) if engine_trace_path.is_file() else None
    pointer_events = jsonl(pointer_trace_path) if pointer_trace_path.is_file() else None
    host_events = jsonl(host_trace_path) if host_trace_path.is_file() else None
    menu_events = jsonl(menu_trace_path) if menu_trace_path.is_file() else None
    stats = json.loads(stats_path.read_text(encoding="utf-8")) if stats_path.is_file() else None
    expected_codes = [0x1503,0x1504,0x1505,0x1506,0x1507,0x1507,0x1505,0x1504,0x150E]
    engine_calls_valid = (engine_events is not None and
        [row.get("command") for row in engine_events] == expected_codes and
        all(row.get("result") == 0 and row.get("before", {}).get("ok") and
            row.get("after", {}).get("ok") and row.get("ticks", [1,2])[0] ==
            row.get("ticks", [1,2])[1] and row.get("source_pause") == [1,1] and
            row.get("rng", [1,2,3,4])[:2] ==
            row.get("rng", [1,2,3,4])[2:] for row in engine_events))
    menu_pause_sequence_valid = (menu_events is not None and
        [row.get("command") for row in menu_events] == [0xFD41,0xFD15,0xFD41] and
        all(row.get("status") == 0 and
            row.get("completed_ticks", [1,2])[0] == row.get("completed_ticks", [1,2])[1]
            for row in menu_events) and
        [row.get("source_pause") for row in menu_events] == [[0,1],[1,1],[1,0]])
    graph_snapshots = ([row.get("after", {}).get("shown_graphs") for row in engine_events[:8]]
                       if engine_events else [])
    expected_lists = [[0,-32768,-32768,-32768], [1,0,-32768,-32768],
                      [2,1,0,-32768], [3,2,1,0], [4,3,2,1],
                      [3,2,1,-32768], [3,1,-32768,-32768],
                      [3,-32768,-32768,-32768]]
    list_evolution_matches = graph_snapshots == expected_lists
    graph_hold = [row for row in (pointer_events or []) if row.get("kind") == "poll"]
    hold_drained = (len(graph_hold) >= 2 and
                    any(row.get("values", [0,0,0,0])[:2] ==
                        [events.get("graph_area", [0,0,0,0])[0] +
                         (events.get("graph_area", [0,0,0,0])[2] - events.get("graph_area", [0,0,0,0])[0]) // 2 + 8,
                         events.get("graph_area", [0,0,0,0])[1] +
                         (events.get("graph_area", [0,0,0,0])[3] - events.get("graph_area", [0,0,0,0])[1]) // 2]
                        and row.get("values", [0,0,0,0])[2] == 1 for row in graph_hold) and
                    any(row.get("values", [0,0,0,0])[2] == 0 for row in graph_hold))
    passed = (type(timed_out) is bool and not timed_out and return_code == 0 and
        production_stable and test_stable and pair_valid and abi_valid and menu_valid and
        "Native NewGame scenario=" in stdout and
        "Completed native simulation ticks: 32" in stdout and
        geometry is not None and geometry.get("schema") == "portable-live-history-geometry-v1" and
        geometry.get("front_window") == 0x1500 and
        all(any(obj.get("object_id") == object_id for obj in geometry.get("objects", []))
            for object_id in [*range(0x1503,0x150D),0x150E]) and
        events is not None and events.get("phase_count") == 14 and
        events.get("injection_failures") == 0 and events.get("pause_toggles") == 2 and
        events.get("history_command") == 0xFD15 and
        events.get("button_commands") == [0x1503,0x1504,0x1505,0x1506,
                                            0x1507,0x1507,0x1505,0x1504] and
        events.get("wrapped_history_events") == 9 and engine_calls_valid and
        menu_pause_sequence_valid and
        list_evolution_matches and hold_drained and stats is not None and
        stats.get("completed_ticks") == 32 and stats.get("source_pause") == 0 and
        stats.get("front_window") == 0x1500 and stats.get("paused_update_calls", 0) > 0 and
        screenshot.is_file())
    if type(passed) is not bool:
        raise AssertionError("history acceptance expression must return bool")
    report = {
        "schema": "portable-live-history-physical-test-v1",
        "status": "PASS" if passed else "FAIL",
        "claim": "Physical SDL menu and mouse input opened the source History window, toggled five graph buttons to exercise capacity eviction, removed first/middle/last shown graphs, then held and released the graph area while the source StillDown path drained host events.",
        "proof_boundary": "Finite SDL dummy-driver live integration under Next10: each actual engine history-event boundary records the source-owned private UI snapshot and unchanged RNG/tick counters. The ordered graph-list transition is compared against the existing 29-event original-DOS History corpus. No DOS calls occur in this physical sequence; no DOS-pixel or whole-game equivalence claim.",
        "limitations": ["The exact multi-step physical mouse sequence is native-only; its component source transitions are covered by the separately pinned 29-event DOS/native report.",
                        "Framebuffer pixels and host window-system behavior are outside this proof."],
        "production_profile": PROFILE,
        "paired_history_oracle": {"path": str(HISTORY_PAIR), "sha256": sha(HISTORY_PAIR),
            "status": pair.get("status"), "event_count": sum(len(row.get("events", [])) for row in scenarios.values()),
            "generated_s24_sha256": pair.get("next10_generated_s24_sha256"),
            "matches_current_s24": pair.get("next10_generated_s24_sha256") == sha(generated_s24)},
        "history_adapter_receipt": {"path": str(HISTORY_ABI), "sha256": sha(HISTORY_ABI),
            "status": abi.get("status"), "event_count": abi.get("dos_state_comparison", {}).get("event_count")},
        "menu_oracle": {"path": str(MENU_PAIR), "sha256": sha(MENU_PAIR),
            "status": menu.get("status"), "case_count": menu.get("case_count"),
            "mismatch_count": menu.get("mismatch_count")},
        "execution": {"arguments": ["--live-newgame", "--ticks", "32"],
            "sdl_video_driver": "dummy", "timeout_seconds": timeout,
            "timed_out": timed_out, "return_code": return_code,
            "stdout": stdout, "stderr": stderr},
        "geometry": geometry,
        "injected_events": events,
        "injection_progress": progress,
        "engine_history_event_trace": engine_events,
        "source_pointer_poll_trace": pointer_events,
        "host_event_poll_trace": host_events,
        "menu_proc_dispatch_trace": menu_events,
        "final_diagnostics": stats,
        "checks": {"engine_calls_and_rng_ticks": engine_calls_valid,
            "menu_pause_history_unpause_sequence": menu_pause_sequence_valid,
            "graph_list_evolution": list_evolution_matches,
            "graph_area_stilldown_drained_motion_and_release": hold_drained},
        "source_closure": {
            "receipt": {"path": str(receipt_path), "sha256_before": receipt_before_sha,
                "sha256_after": receipt_after_sha, "inputs_before": production_before,
                "inputs_after": production_after, "unchanged": production_stable},
            "production_executable_sha256": sha(source_exe),
            "production_sdl3_sha256": sha(sdl_dll),
            "test_executable": {"path": str(test_exe), "sha256": sha(test_exe)},
            "test_sdl3_dll_sha256": sha(test_dll),
            "test_inputs_before": test_before, "test_inputs_after": test_after,
            "test_sources_stable": test_stable, "compiler_command": command,
            "compiler_sha256": sha(Path(command[0])),
            "compiler_version": subprocess.run([command[0], "--version"],
                capture_output=True, text=True, check=False).stdout.splitlines()[0]},
        "artifacts": {"injection_progress": {"path": str(progress_path), "sha256": sha(progress_path)} if progress_path.is_file() else None,
            "history_geometry": {"path": str(geometry_path), "sha256": sha(geometry_path)} if geometry_path.is_file() else None,
            "injected_events": {"path": str(event_path), "sha256": sha(event_path)} if event_path.is_file() else None,
            "engine_history_events": {"path": str(engine_trace_path), "sha256": sha(engine_trace_path)} if engine_trace_path.is_file() else None,
            "source_pointer_polls": {"path": str(pointer_trace_path), "sha256": sha(pointer_trace_path)} if pointer_trace_path.is_file() else None,
            "host_event_polls": {"path": str(host_trace_path), "sha256": sha(host_trace_path)} if host_trace_path.is_file() else None,
            "menu_proc_dispatches": {"path": str(menu_trace_path), "sha256": sha(menu_trace_path)} if menu_trace_path.is_file() else None,
            "statistics": {"path": str(stats_path), "sha256": sha(stats_path)} if stats_path.is_file() else None,
            "screenshot": {"path": str(screenshot), "sha256": sha(screenshot)} if screenshot.is_file() else None},
        "passed": passed}
    if report_path.exists():
        raise FileExistsError(report_path)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "report": str(report_path),
        "events": events, "engine_calls_valid": engine_calls_valid,
        "graph_list_evolution_matches": list_evolution_matches,
        "graph_hold_drained": hold_drained, "return_code": return_code,
        "stdout": stdout, "stderr": stderr}, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
