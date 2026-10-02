#!/usr/bin/env python3
"""Bounded headless smoke for the source-backed one-tick live adapter."""
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
DEFAULT_EXE = ROOT / "build/portable/simant-sdl3.exe"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", type=Path, default=DEFAULT_EXE)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--ticks", type=int, default=32)
    parser.add_argument("--inject-tab", action="store_true",
                        help="link a test-only SDL timer that pushes unbound Tab")
    parser.add_argument("--inject-yellow-keys", action="store_true",
                        help="inject source-handled 0 and source-unhandled Tab keys")
    parser.add_argument("--inject-menu-keys", action="store_true",
                        help="inject source pause and all four speed shortcuts")
    parser.add_argument("--inject-camera", action="store_true",
                        help="inject a Control+numeric-keypad-right camera step")
    parser.add_argument("--inject-click", action="store_true",
                        help="inject one SDL left press/release in source Edit object 4")
    parser.add_argument("--inject-double-click", action="store_true",
                        help="inject a source-window double click in Edit object 4")
    parser.add_argument("--observe-overview", action="store_true",
                        help="capture the source map-window overview under diagnostics")
    args = parser.parse_args()
    if sum((args.inject_tab, args.inject_yellow_keys, args.inject_menu_keys, args.inject_camera,
            args.inject_click, args.inject_double_click, args.observe_overview)) > 1:
        print("choose one SDL test event driver", file=sys.stderr)
        return 2
    if args.ticks <= 0 or args.ticks > 256:
        print("smoke tick count must be in 1..256", file=sys.stderr)
        return 2
    source_exe = args.exe.resolve()
    if not source_exe.is_file():
        print(f"live-game executable missing: {source_exe}", file=sys.stderr)
        return 2
    receipt_path = source_exe.with_suffix(".build.json")
    if not receipt_path.is_file():
        print(f"build receipt missing: {receipt_path}", file=sys.stderr)
        return 2
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    profile = receipt.get("recovered_core", {}).get("profile")
    if not profile:
        print("executable is not pinned to a recovered-core profile", file=sys.stderr)
        return 2

    report_path = (args.report.resolve() if args.report is not None else
                   ROOT / "portable/tests/live_game/evidence/live-smoke.json")
    frame_path = report_path.with_name(f"{report_path.stem}-frame-{args.ticks}.bmp")
    exe = source_exe
    injector_name = ("yellow_key_injector.c" if args.inject_yellow_keys else
                     "menu_key_injector.c" if args.inject_menu_keys else
                     "camera_key_injector.c" if args.inject_camera else
                     "mouse_double_click_injector.c" if args.inject_double_click else
                     "mouse_click_injector.c" if args.inject_click else
                     "overview_observer.c" if args.observe_overview else
                     "modal_tab_injector.c")
    injector = ROOT / "portable/tests/live_game" / injector_name
    injector_report = report_path.with_name(f"{report_path.stem}-events-{args.ticks}.txt")
    state_base = report_path.with_name(f"{report_path.stem}-state-{args.ticks}")
    state_files = [Path(str(state_base) + suffix) for suffix in
                   (".recovered.bin", ".normalized.bin", ".rng.bin", ".stats.json")]
    if (args.inject_tab or args.inject_yellow_keys or args.inject_menu_keys or args.inject_camera or
            args.inject_click or args.inject_double_click or args.observe_overview):
        output_name = ("live-smoke-yellow-keys.exe" if args.inject_yellow_keys else
                       "live-smoke-menu-keys.exe" if args.inject_menu_keys else
                       "live-smoke-camera.exe" if args.inject_camera else
                       "live-smoke-double-click.exe" if args.inject_double_click else
                       "live-smoke-click.exe" if args.inject_click else
                       "live-smoke-overview.exe" if args.observe_overview else
                       "live-smoke-injected.exe")
        output_exe = ROOT / "build/portable/tests" / output_name
        output_exe.parent.mkdir(parents=True, exist_ok=True)
        command_line = list(receipt["command"])
        try:
            output_index = command_line.index("-o")
            command_line[output_index + 1] = str(output_exe)
        except (ValueError, IndexError, KeyError):
            print("build receipt has no reusable compiler command", file=sys.stderr)
            return 2
        library_index = next((i for i, token in enumerate(command_line)
                              if token == "-L"), output_index)
        command_line.insert(library_index, "-DSIMANT_LIVE_GAME_TEST_DIAGNOSTICS=1")
        library_index += 1
        command_line.insert(library_index, str(injector))
        linked = subprocess.run(command_line, cwd=ROOT, text=True,
                                capture_output=True, check=False)
        if linked.returncode != 0:
            print(linked.stdout + linked.stderr, file=sys.stderr)
            return linked.returncode
        dll = source_exe.parent / "SDL3.dll"
        if dll.is_file():
            shutil.copy2(dll, output_exe.parent / "SDL3.dll")
        exe = output_exe
        injector_report.unlink(missing_ok=True)
        for path in state_files:
            path.unlink(missing_ok=True)
    env = dict(os.environ)
    env["SDL_VIDEODRIVER"] = "dummy"
    if (args.inject_tab or args.inject_yellow_keys or args.inject_menu_keys or args.inject_camera or
            args.inject_click or args.inject_double_click or args.observe_overview):
        env["SIMANT_LIVE_SMOKE_EVENT_REPORT"] = str(injector_report)
        env["SIMANT_LIVE_SMOKE_STATE_REPORT"] = str(state_base)
    command = [str(exe), "--live-newgame", "--ticks", str(args.ticks),
               "--screenshot", str(frame_path)]
    timeout = max(20, min(180, 10 + args.ticks // 2))
    try:
        result = subprocess.run(command, cwd=ROOT, env=env, text=True,
                                capture_output=True, timeout=timeout, check=False)
        timed_out = False
    except subprocess.TimeoutExpired as error:
        result = error
        timed_out = True
    stdout = "" if timed_out else result.stdout
    stderr = "" if timed_out else result.stderr
    returncode = None if timed_out else result.returncode
    frame_ready = not timed_out and frame_path.is_file()
    state_ready = (args.inject_tab or args.inject_yellow_keys or args.inject_menu_keys or args.inject_camera or
                   args.inject_click or args.inject_double_click or args.observe_overview) and all(
        path.is_file() for path in state_files)
    state_stats = (json.loads(state_files[3].read_text(encoding="utf-8"))
                   if state_ready else None)
    event_driver_stats = None
    if injector_report.is_file():
        contents = injector_report.read_text(encoding="utf-8").strip()
        if args.inject_menu_keys:
            event_driver_stats = json.loads(contents)
        else:
            event_driver_stats = {"pushed_event_count": int(contents)}
    if state_stats is not None:
        state_stats["effect_calls_by_kind"] = dict(zip(
            ("map_cell_invalidate", "edit_message", "picture_string_dialog",
             "default_wind_prompt", "nest_map_invalidate", "alarm_selection",
             "window_operation", "graphics_rect", "graphics_line"),
            state_stats["effects"][1:]))
        state_stats["query_calls_by_kind"] = dict(zip(
            ("window_open", "window_events", "window_in_front", "still_down",
             "dialog_abort_or_continue", "get_event", "get_object_rect", "button"),
            state_stats["queries"][1:]))
        state_stats["picture_string_dialog_calls_observed"] = state_stats[
            "effect_calls_by_kind"]["picture_string_dialog"]
        state_stats["modal_dismissal_verified_by_this_smoke"] = False
    menu_keys_passed = (not args.inject_menu_keys or (state_stats is not None and
        state_stats["pause_action_calls"] == 2 and
        state_stats["speed_action_calls"] == [2, 1, 1, 1] and
        state_stats["source_pause"] == 0 and state_stats["source_speed"] == 0 and
        state_stats["menu_loaded"] is True and
        state_stats["menu_item_state_calls"] > 0 and
        state_stats["pause_duration_ns"] >= 50_000_000 and
        state_stats["paused_update_calls"] > 0 and
        state_stats["pause_start_ticks"] == state_stats["pause_end_ticks"] and
        event_driver_stats is not None and
        event_driver_stats["pause_hold_ns"] >= 150_000_000))
    yellow_keys_passed = (not args.inject_yellow_keys or (state_stats is not None and
        state_stats["yellow_key_calls"] == 2 and
        state_stats["yellow_key_handled_calls"] == 1 and
        state_stats["yellow_key_unhandled_calls"] == 1 and
        state_stats["yellow_key_unhandled_unchanged_calls"] == 1 and
        state_stats["yellow_key_last"] == 9 and
        state_stats["yellow_key_last_result"] == 0 and
        event_driver_stats is not None and
        event_driver_stats["pushed_event_count"] == 4))
    overview_passed = (not args.observe_overview or (state_stats is not None and
        state_stats["overview_render_calls"] > 0 and
        state_stats["overview_mode"] in (1, 2, 3) and
        state_stats["overview_image_rect"][2] > state_stats["overview_image_rect"][0] and
        state_stats["overview_image_rect"][3] > state_stats["overview_image_rect"][1] and
        state_stats["overview_cursor_rect"][2] > state_stats["overview_cursor_rect"][0] and
        state_stats["overview_cursor_rect"][3] > state_stats["overview_cursor_rect"][1] and
        event_driver_stats is not None and event_driver_stats["pushed_event_count"] == 0))
    camera_passed = (not args.inject_camera or (state_stats is not None and
        state_stats["scroll_action_calls"] == 1 and
        state_stats["camera_x"] == 26 and state_stats["camera_y"] == 2 and
        event_driver_stats is not None and
        event_driver_stats["pushed_event_count"] == 4))
    click_passed = (not args.inject_click or (state_stats is not None and
        state_stats["edit_hotbox_clicks"] == 1 and
        state_stats["edit_events_delivered"] == 1 and
        state_stats["edit_queue_remaining"] == 0 and
        state_stats["edit_double_clicks"] == 0 and
        state_stats["edit_object4_rect"] == [64, 41, 416, 330] and
        state_stats["edit_object4_flags"] & 2 != 0 and
        state_stats["edit_object4_type"] == 1 and
        state_stats["event_goal_active"] == 1 and
        state_stats["event_goal_mode"] == 0 and
        state_stats["event_goal_x"] == 27 and
        state_stats["event_goal_y"] == 5 and
        state_stats["event_left_down"] == 0 and
        state_stats["left_down"] == 0 and
        event_driver_stats is not None and
        event_driver_stats["pushed_event_count"] == 2))
    double_click_passed = (not args.inject_double_click or (state_stats is not None and
        state_stats["edit_hotbox_clicks"] == 2 and
        state_stats["edit_events_delivered"] == 2 and
        state_stats["edit_double_clicks"] == 1 and
        state_stats["edit_queue_remaining"] == 0 and
        state_stats["edit_object4_rect"] == [64, 41, 416, 330] and
        state_stats["edit_object4_flags"] & 2 != 0 and
        state_stats["edit_object4_type"] == 1 and
        state_stats["event_goal_active"] == 1 and
        state_stats["event_goal_mode"] == 2 and
        state_stats["event_goal_x"] == 27 and
        state_stats["event_goal_y"] == 5 and
        state_stats["event_goal_plane"] == 2 and
        state_stats["event_left_down"] == 1 and
        state_stats["left_down"] == 0 and
        event_driver_stats is not None and
        event_driver_stats["pushed_event_count"] == 4))
    passed = (not timed_out and returncode == 0 and
              "Native NewGame scenario=" in stdout and
              f"Completed native simulation ticks: {args.ticks}" in stdout and
              frame_ready and (not args.inject_tab or
                  (state_ready and state_stats["completed_ticks"] == args.ticks)) and
              (not args.inject_yellow_keys or (state_ready and
                  state_stats["completed_ticks"] == args.ticks and yellow_keys_passed)) and
              (not args.observe_overview or (state_ready and
                  state_stats["completed_ticks"] == args.ticks and overview_passed)) and
              (not args.inject_menu_keys or (state_ready and
                  state_stats["completed_ticks"] == args.ticks and menu_keys_passed)) and
              (not args.inject_camera or (state_ready and
                  state_stats["completed_ticks"] == args.ticks and camera_passed)) and
              (not args.inject_click or (state_ready and
                  state_stats["completed_ticks"] == args.ticks and click_passed)) and
              (not args.inject_double_click or (state_ready and
                  state_stats["completed_ticks"] == args.ticks and double_click_passed)))
    report = {
        "schema": "portable-live-game-smoke-v1",
        "claim": "a resource-backed NewGame scene completed the bounded source-scheduled tick count through the native SDL adapter",
        "scope": {
            "ticks": args.ticks,
            "user_input_events": 0,
            "test_injected_events": ("SDL Control+keypad-right down/up transitions"
                if args.inject_camera else
                "one SDL left press/release over the actual Edit object-4 rectangle"
                if args.inject_click else
                "two SDL left press/release transitions inside the source 10-tick double-click window"
                if args.inject_double_click else
                "SDL pause and four speed shortcuts with explicit Shift transitions"
                if args.inject_menu_keys else
                "SDL logical 0 source command and unhandled Tab key"
                if args.inject_yellow_keys else
                "no injected events; observe actual mode-selected map-window overview"
                if args.observe_overview else
                "periodic SDL Tab key-down/up pairs (unbound by the native input model)"
                if args.inject_tab else "none"),
            "sdl_video_driver": "dummy",
            "does_not_claim": [
                "long-run simulation equivalence",
                "mouse events outside the proven Edit object-4 left-press route",
                "complete recovered UI operation coverage",
                "audio playback"
            ]
        },
        "command": command,
        "harness_source": {"path": str(Path(__file__).resolve()),
                           "sha256": sha256(Path(__file__).resolve())},
        "executable": {"path": str(exe), "sha256": sha256(exe)},
        "production_executable": {"path": str(source_exe),
                                  "sha256": sha256(source_exe)},
        "build_receipt": {"path": str(receipt_path), "sha256": sha256(receipt_path),
                          "recovered_core_profile": profile},
        "test_event_driver": ({"kind": ("source_control_keypad_camera_step"
                                if args.inject_camera else
                                "source_yellow_command_key_and_unhandled_tab"
                                if args.inject_yellow_keys else
                                "source_menu_speed_pause_shortcut_sequence"
                                if args.inject_menu_keys else
                                "source_edit_object4_left_press"
                                if args.inject_click else
                                "source_edit_object4_double_click"
                                if args.inject_double_click else
                                "source_map_overview_observation"
                                if args.observe_overview else
                                "periodic_unbound_tab_key_pairs"),
                               "source_path": str(injector),
                               "source_sha256": sha256(injector),
                               "sequence": (["left-down", "left-up", "left-down",
                                             "left-up", "(100,100)"]
                                           if args.inject_double_click else
                                           ["left-down", "left-up", "(100,100)"]
                                           if args.inject_click else
                                           (["control-down", "keypad-right-down",
                                             "keypad-right-up", "control-up"]
                                            if args.inject_camera else
                                             ["logical-0-down", "logical-0-up",
                                              "Tab-down", "Tab-up"]
                                             if args.inject_yellow_keys else
                                            ["speed-0 (!)", "speed-1 (@)",
                                             "speed-2 (#)", "speed-3 ($)",
                                             "restore-speed-0 (!)", "pause-on ())",
                                             "pause-off ())"]
                                            if args.inject_menu_keys else None)),
                               **(event_driver_stats or {})}
                               if args.inject_tab or args.inject_yellow_keys or args.inject_menu_keys or args.inject_camera or args.inject_click or args.inject_double_click or args.observe_overview else None),
        "final_state": ({
            "recovered_state": {"path": str(state_files[0]),
                                "sha256": sha256(state_files[0])},
            "normalized_recovered_state": {"path": str(state_files[1]),
                                           "sha256": sha256(state_files[1]),
                                           "pointer_fields_zeroed": [
                                               "AdviceStrs", "fd_3D57_0852[40]",
                                               "fd_50F6_02BA", "fd_50F6_034C",
                                               "fd_50F6_0B22", "g_5AAC"]},
            "rng_state": {"path": str(state_files[2]),
                          "sha256": sha256(state_files[2])},
            "statistics": state_stats
        } if state_ready else None),
        "final_frame": ({"path": str(frame_path), "sha256": sha256(frame_path)}
                        if frame_ready else None),
        "timeout_seconds": timeout,
        "timed_out": timed_out,
        "exit_code": returncode,
        "stdout": stdout,
        "stderr": stderr,
        "passed": passed
    }
    if args.report is not None:
        output = report_path
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
