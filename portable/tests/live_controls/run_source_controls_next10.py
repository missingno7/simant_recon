#!/usr/bin/env python3
"""Bounded SDL physical-input exercise of resource-backed Mode/Caste controls."""
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
DLL = ROOT / "build/portable/SDL3.dll"
PROFILE = "build/workers/recovered_source_next10/generated"
SOURCE_PAIR = ROOT / "portable/tests/setup/source_control_bridge/evidence/production-source-controls-v1-20261002.json"
CONVERSION = ROOT / "portable/game/recovered/source/control_events.json"
PAIRED = ROOT / "portable/tests/setup/control_events/evidence/paired-control-events.json"
MENU_DOS = ROOT / "portable/tests/menus/evidence/procmenu-next7-dos-differential-adapter-complete-closure-20261002.json"
PRESELECT_DOS = ROOT / "portable/tests/windows/control_preselect/evidence/control-preselect-dos-native-final-20261002.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", required=True, type=Path,
                        help="new report path; the runner refuses to overwrite")
    args = parser.parse_args()
    report_path = args.report.resolve()
    if not report_path.parent.is_dir():
        print(f"evidence directory missing: {report_path.parent}", file=sys.stderr)
        return 2
    stem = report_path.stem
    event_path = report_path.with_name(f"{stem}-events.json")
    geometry_path = report_path.with_name(f"{stem}-geometry.json")
    pointer_trace_path = report_path.with_name(f"{stem}-pointer-trace.jsonl")
    state_base = report_path.with_name(f"{stem}-state")
    stats_path = Path(str(state_base) + ".stats.json")
    endgame_path = Path(str(state_base) + ".endgame.json")
    screenshot = report_path.with_name(f"{stem}-frame.bmp")
    source_exe = ROOT / "build/portable/simant-sdl3.exe"
    receipt_path = source_exe.with_suffix(".build.json")
    injector = ROOT / "portable/tests/live_controls/physical_controls_injector.c"
    model_source = ROOT / "portable/tests/live_controls/expected_sequence.c"
    model_c = ROOT / "portable/ui_model/windows/control_events.c"
    model_h = ROOT / "portable/ui_model/windows/control_events.h"
    setup_c = ROOT / "portable/game/simulation/setup.c"
    setup_h = ROOT / "portable/game/simulation/setup.h"
    runner = Path(__file__).resolve()
    assets = [ROOT / "assets/SHARED.NDX", ROOT / "assets/SHARED.DAT",
              ROOT / "assets/HCEGANT.NDX", ROOT / "assets/HCEGANT.DAT"]
    if not all(p.is_file() for p in (source_exe, receipt_path, DLL, PAIRED,
                                      MENU_DOS, PRESELECT_DOS)):
        print("production executable/receipt/SDL DLL or paired control receipt is missing",
              file=sys.stderr)
        return 2
    outputs = [report_path, event_path, geometry_path, pointer_trace_path,
               stats_path, endgame_path, screenshot,
               Path(str(state_base) + ".recovered.bin"),
               Path(str(state_base) + ".normalized.bin"),
               Path(str(state_base) + ".rng.bin")]
    if any(path.exists() for path in outputs):
        print("refusing to overwrite: " + ", ".join(str(p) for p in outputs if p.exists()),
              file=sys.stderr)
        return 2
    receipt_hash_before = sha(receipt_path)
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if receipt.get("recovered_core", {}).get("profile") != PROFILE:
        print("production receipt does not identify the Next10 source profile", file=sys.stderr)
        return 2
    if receipt.get("executable_sha256") != sha(source_exe) or \
       receipt.get("sdl_library_sha256") != sha(DLL):
        print("production executable or SDL3.dll does not match its build receipt",
              file=sys.stderr)
        return 2
    closure = {str(k): str(v) for k, v in receipt["inputs"].items()}
    before = {name: sha(ROOT / name) for name in closure}
    if any(before[name] != expected for name, expected in closure.items()):
        print("production source closure differs from receipt", file=sys.stderr)
        return 2
    input_files = [runner, injector, model_source, model_c, model_h,
                   setup_c, setup_h, PAIRED, SOURCE_PAIR, CONVERSION,
                   MENU_DOS, PRESELECT_DOS, *assets]
    test_inputs_before = {str(p.relative_to(ROOT)): sha(p) for p in input_files}
    test_dir = ROOT / "build/portable/tests" / stem
    test_dir.mkdir(parents=True, exist_ok=False)
    test_exe = test_dir / "live-controls.exe"
    command = list(receipt["command"])
    try:
        output = command.index("-o")
        command[output + 1] = str(test_exe)
        library = command.index("-L")
    except (ValueError, IndexError, KeyError):
        print("build receipt has no reusable compiler command", file=sys.stderr)
        return 2
    command.insert(library, "-Wl,--wrap=host_poll_event")
    command.insert(library + 1, "-DSIMANT_LIVE_GAME_TEST_DIAGNOSTICS=1")
    command.insert(library + 2, str(injector))
    linked = subprocess.run(command, cwd=ROOT, capture_output=True, text=True,
                            check=False)
    if linked.returncode:
        print(linked.stdout + linked.stderr, file=sys.stderr)
        return linked.returncode
    test_dll = test_dir / "SDL3.dll"
    shutil.copy2(DLL, test_dll)
    env = dict(os.environ)
    env["SDL_VIDEODRIVER"] = "dummy"
    env["SIMANT_LIVE_CONTROL_EVENT_REPORT"] = str(event_path)
    env["SIMANT_LIVE_CONTROL_GEOMETRY_REPORT"] = str(geometry_path)
    env["SIMANT_LIVE_CONTROL_INPUT_TRACE"] = str(pointer_trace_path)
    env["SIMANT_LIVE_SMOKE_STATE_REPORT"] = str(state_base)
    timeout = 90
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
    after = {name: sha(ROOT / name) for name in closure}
    receipt_hash_after = sha(receipt_path)
    stable = before == after and receipt_hash_before == receipt_hash_after
    test_inputs_after = {str(p.relative_to(ROOT)): sha(p) for p in input_files}
    test_sources_stable = test_inputs_before == test_inputs_after
    geometry = json.loads(geometry_path.read_text(encoding="utf-8")) if geometry_path.is_file() else None
    events = json.loads(event_path.read_text(encoding="utf-8")) if event_path.is_file() else None
    stats = json.loads(stats_path.read_text(encoding="utf-8")) if stats_path.is_file() else None
    endgame = json.loads(endgame_path.read_text(encoding="utf-8")) if endgame_path.is_file() else None
    pointer_trace = ([json.loads(line) for line in pointer_trace_path.read_text(encoding="utf-8").splitlines()]
                     if pointer_trace_path.is_file() else None)
    paired = json.loads(PAIRED.read_text(encoding="utf-8"))
    menu_oracle = json.loads(MENU_DOS.read_text(encoding="utf-8"))
    preselect_oracle = json.loads(PRESELECT_DOS.read_text(encoding="utf-8"))
    source_pair = json.loads(SOURCE_PAIR.read_text())
    source_pair_matches = (source_pair.get("status") == "PASS" and
                           source_pair.get("case_count") == 34 and
                           source_pair.get("mismatch_count") == 0 and
                           all(sha(ROOT / name) == digest for name, digest in
                               source_pair["input_pins_before"]["files"].items()))
    paired_model_matches = (paired.get("native_model_sha256") == sha(model_c) and
                            paired.get("native_header_sha256") == sha(model_h) and
                            paired.get("status") == "PASS" and
                            paired.get("case_count") == 34 and
                            paired.get("mismatch_count") == 0)
    menu_oracle_matches = (menu_oracle.get("status") == "PASS" and
                           menu_oracle.get("case_count") == 84 and
                           menu_oracle.get("mismatch_count") == 0)
    preselect_oracle_matches = (preselect_oracle.get("status") == "PASS" and
                                preselect_oracle.get("case_count") == 65536 and
                                preselect_oracle.get("mismatch_count") == 0)
    expected = None
    expected_exe = test_dir / "expected-controls.exe"
    model_command = None
    if geometry is not None:
        windows = {row["window_id"]: row for row in geometry.get("windows", [])}
        def rect_of(window_id: int, object_id: int, source: bool = False) -> list[int]:
            window = windows[window_id]
            if source:
                return window["source_triangle_rect"]
            for obj in window["objects"]:
                if obj["object_id"] == object_id:
                    return obj["rect"]
            raise KeyError(f"missing loaded object {object_id:#x}")
        model_command = [str(receipt["command"][0]), "-std=c11", "-Wall", "-Wextra",
                         "-Werror", "-I", str(ROOT / "portable"), str(model_source),
                         str(model_c), str(setup_c), "-o", str(expected_exe)]
        compiled_model = subprocess.run(model_command, cwd=ROOT, capture_output=True,
                                        text=True, check=False)
        if compiled_model.returncode == 0:
            mode_rect = rect_of(0x1200, 0x120D)
            caste_rect = rect_of(0x1300, 0x130D)
            mode_source = rect_of(0x1200, 0x120D, True)
            caste_source = rect_of(0x1300, 0x130D, True)
            shared = geometry["shared_triangle"]
            mode_end = [(mode_rect[0] + mode_rect[2]) // 2, mode_rect[3] - 3]
            caste_end = [(caste_rect[0] + caste_rect[2]) // 2, caste_rect[3] - 3]
            model_args = [str(expected_exe), ",".join(map(str, mode_source)),
                          ",".join(map(str, mode_rect)), ",".join(map(str, caste_source)),
                          ",".join(map(str, caste_rect)), *map(str, mode_end),
                          *map(str, caste_end),
                          *map(str, shared)]
            model_run = subprocess.run(model_args, cwd=ROOT, capture_output=True,
                                       text=True, check=False)
            if model_run.returncode == 0:
                expected = json.loads(model_run.stdout)
            else:
                stderr += "\nexpected control model: " + model_run.stderr
        else:
            stderr += "\nexpected control model compile: " + compiled_model.stderr
    # These checks establish that the exact expected operations were dispatched.
    # Final numeric state validation is completed against the paired 34-case model below.
    passed = (not timed_out and return_code == 0 and stable and test_sources_stable and expected is not None and
              source_pair_matches and paired_model_matches and menu_oracle_matches and preselect_oracle_matches and
              "Native NewGame scenario=" in stdout and
              "Completed native simulation ticks: 32" in stdout and
              geometry is not None and geometry.get("front_window") == 0 and
              events is not None and events.get("phase_count") == 14 and
              events.get("pushed_event_count") == 34 and
              events.get("injection_failures") == 0 and
              events.get("operation_mask") == 1023 and
              events.get("mode_command") == 0xFD13 and
              events.get("caste_command") == 0xFD14 and
              events.get("pause_command") == 0xFD41 and
              events.get("pause_toggle_count") == 2 and
              events.get("converted_control_pointer_events") == [
                  {"kind": 3, "x": 191, "y": 264, "button": 1},
                  {"kind": 2, "x": 191, "y": 309, "button": 0},
                  {"kind": 4, "x": 191, "y": 309, "button": 1},
                  {"kind": 3, "x": 446, "y": 263, "button": 1},
                  {"kind": 2, "x": 446, "y": 308, "button": 0},
                  {"kind": 4, "x": 446, "y": 308, "button": 1}] and
              events.get("mode_menu_item") == "Behavior" and
              events.get("caste_menu_item") == "Caste" and
              events.get("control_action_order") == ["mode:auto-on", "mode:auto-off",
                  "mode:preset-3", "mode:percent", "mode:drag", "caste:auto-on",
                  "caste:auto-off", "caste:preset-3", "caste:percent", "caste:drag"] and
              events.get("window_menu_index") >= 0 and
              events.get("mode_row") >= 0 and events.get("caste_row") >= 0 and
              stats is not None and stats.get("completed_ticks") == 32 and
              stats.get("paused_update_calls", 0) > 0 and
              stats.get("front_window") == 0x1300 and
              stats.get("source_pause") == 0 and
              stats.get("control_event_calls") == 10 and
              stats.get("control_last_code") == 0x130D and
              stats.get("mode_auto") == 0 and stats.get("caste_auto") == 0 and
              stats.get("mode_selector") == 2 and stats.get("caste_selector") == 2 and
              stats.get("mode_percent") == 0 and stats.get("caste_percent") == 0 and
              pointer_trace is not None and len(pointer_trace) >= 10 and
              any(item.get("kind") == "rect" and item.get("values") == [136,216,247,312]
                  for item in pointer_trace) and
              any(item.get("kind") == "rect" and item.get("values") == [392,215,501,311]
                  for item in pointer_trace) and
              any(item.get("kind") == "poll" and item.get("values") == [191,309,1,1]
                  for item in pointer_trace) and
              any(item.get("kind") == "poll" and item.get("values") == [446,308,1,1]
                  for item in pointer_trace) and
              stats.get("mode_level") == expected.get("mode_level") and
              stats.get("caste_level") == expected.get("caste_level") and
              stats.get("mode_auto") == expected.get("mode_auto") and
              stats.get("caste_auto") == expected.get("caste_auto") and
              stats.get("mode_selector") == expected.get("mode_selector") and
              stats.get("caste_selector") == expected.get("caste_selector") and
              endgame is not None and not endgame.get("diagnostic_callback_invoked") and
              not endgame.get("opened") and not endgame.get("restart_boundary_reached") and
              endgame.get("error", "") == "" and
              screenshot.is_file())
    if type(passed) is not bool:
        raise AssertionError("physical-control acceptance expression must produce bool")
    loaded_triangles = None
    if geometry is not None:
        loaded_triangles = {}
        for window_id, object_id, name in ((0x1200, 0x120D, "mode"),
                                          (0x1300, 0x130D, "caste")):
            window = next(row for row in geometry["windows"]
                          if row["window_id"] == window_id)
            loaded_triangles[name] = next(row["rect"] for row in window["objects"]
                                          if row["object_id"] == object_id)
    def init_tri_vars(rect: list[int]) -> list[int]:
        width, height = rect[2] - rect[0], rect[3] - rect[1]
        return [width, height, width >> 1]
    report = {
        "schema": "portable-live-source-controls-next10-v1",
        "status": "PASS" if passed else "FAIL",
        "claim": "Physical SDL mouse input selected Mode and Caste through the resource-backed Windows menu, then exercised each control window's Auto on/off buttons, third preset, percent toggle, and triangle drag in a bounded NewGame session.",
        "proof_boundary": "Finite SDL dummy-driver host integration: pause the live source scheduler during physical control gestures, unpause to complete 32 bounded ticks, and check logical source control state against the separately paired 34-case DOS/model control corpus. Per-window triangle dimensions follow the original OpenModeWindow/OpenCasteWindow InitTriVars calls. No DOS-pixel or whole-game DOS equivalence claim.",
        "limitations": ["The final Auto/preset/percent/drag state is the independently compiled control model composed from source transitions that pass the paired 34-case DOS corpus; the exact multi-step mouse sequence is not itself replayed in DOS.",
                        "Framebuffer pixels and host window-system behavior are outside this proof."],
        "production_profile": PROFILE,
        "production_source_events": {"path": str(SOURCE_PAIR), "sha256": sha(SOURCE_PAIR),
                                     "unchanged_inputs": source_pair_matches,
                                     "conversion_sha256": sha(CONVERSION)},
        "paired_control_model": {"path": str(PAIRED), "sha256": sha(PAIRED),
                                 "case_count": paired.get("case_count"),
                                 "mismatch_count": paired.get("mismatch_count"),
                                 "status": paired.get("status"),
                                 "native_model_matches": paired_model_matches},
        "menu_and_preselection_oracles": {
            "proc_menu": {"path": str(MENU_DOS), "sha256": sha(MENU_DOS),
                          "case_count": menu_oracle.get("case_count"),
                          "mismatch_count": menu_oracle.get("mismatch_count"),
                          "status": menu_oracle.get("status")},
            "control_preselect": {"path": str(PRESELECT_DOS), "sha256": sha(PRESELECT_DOS),
                                  "case_count": preselect_oracle.get("case_count"),
                                  "mismatch_count": preselect_oracle.get("mismatch_count"),
                                  "status": preselect_oracle.get("status")}},
        "execution": {"arguments": ["--live-newgame", "--ticks", "32"],
                      "sdl_video_driver": "dummy", "timeout_seconds": timeout,
                      "timed_out": timed_out, "return_code": return_code,
                      "stdout": stdout, "stderr": stderr},
        "loaded_source_geometry": geometry,
        "expected_control_state_from_paired_model": expected,
        "triangle_parameter_context": {
            "source": "src/root/m0798.c: InitTriVars is called by win_ModeControlChanged and win_CasteControlChanged before the corresponding control window opens.",
            "mode_loaded_rect": loaded_triangles["mode"] if loaded_triangles else None,
            "caste_loaded_rect": loaded_triangles["caste"] if loaded_triangles else None,
            "effective_mode_triangle_width_height_half": init_tri_vars(loaded_triangles["mode"]) if loaded_triangles else None,
            "effective_caste_triangle_width_height_half": init_tri_vars(loaded_triangles["caste"]) if loaded_triangles else None},
        "injected_events": events,
        "source_control_input_trace": {
            "path": str(pointer_trace_path),
            "sha256": sha(pointer_trace_path) if pointer_trace_path.is_file() else None,
            "records": pointer_trace},
        "final_diagnostics": stats,
        "end_game_boundary": endgame,
        "source_closure": {
            "receipt": {"path": str(receipt_path), "sha256_before": receipt_hash_before,
                        "sha256_after": receipt_hash_after, "inputs_before": before,
                        "inputs_after": after, "unchanged": stable},
            "production_executable_sha256": sha(source_exe),
            "production_sdl3_sha256": sha(DLL),
            "test_executable": {"path": str(test_exe), "sha256": sha(test_exe)},
            "test_sdl3_dll_sha256": sha(test_dll),
            "test_inputs_before": test_inputs_before,
            "test_inputs_after": test_inputs_after,
            "test_sources_stable": test_sources_stable,
            "compiler_command": command,
            "expected_model_compiler_command": model_command,
            "expected_model_executable": {"path": str(expected_exe),
                                          "sha256": sha(expected_exe)} if expected_exe.is_file() else None},
        "artifacts": {"event_report": {"path": str(event_path), "sha256": sha(event_path)} if event_path.is_file() else None,
                      "geometry_report": {"path": str(geometry_path), "sha256": sha(geometry_path)} if geometry_path.is_file() else None,
                      "control_input_trace": {"path": str(pointer_trace_path), "sha256": sha(pointer_trace_path)} if pointer_trace_path.is_file() else None,
                      "statistics": {"path": str(stats_path), "sha256": sha(stats_path)} if stats_path.is_file() else None,
                      "end_game_boundary": {"path": str(endgame_path), "sha256": sha(endgame_path)} if endgame_path.is_file() else None,
                      "screenshot": {"path": str(screenshot), "sha256": sha(screenshot)} if screenshot.is_file() else None},
        "passed": passed}
    if report_path.exists():
        raise FileExistsError(report_path)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "report": str(report_path),
                      "events": events, "geometry": geometry, "diagnostics": stats,
                      "return_code": return_code, "stdout": stdout, "stderr": stderr}, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
