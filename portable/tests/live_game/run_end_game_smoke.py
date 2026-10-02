#!/usr/bin/env python3
"""Inject one physical SDL Escape into the live source EndGame modal."""
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
PRODUCTION = ROOT / "build/portable/simant-sdl3.exe"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dependency_inputs(command: list[str], extra_sources: list[Path]) -> dict[str, str]:
    compiler = command[0]
    source_indices = [i for i, token in enumerate(command)
                      if token.endswith((".c", ".cpp"))]
    sources = [Path(command[i]).resolve() for i in source_indices]
    sources.extend(path.resolve() for path in extra_sources)
    first_source = min(source_indices)
    flags = command[1:first_source]
    dep_command = [compiler, *flags, "-MM", "-MT", "smoke-dependencies",
                   *(str(path) for path in sources)]
    result = subprocess.run(dep_command, cwd=ROOT, text=True, capture_output=True,
                            timeout=60, check=False)
    if result.returncode != 0:
        raise RuntimeError("dependency scan failed: " + result.stderr)
    line = result.stdout.replace("\\\n", " ")
    if ":" not in line:
        raise RuntimeError("dependency scanner returned malformed output")
    dependencies = [Path(token).resolve() for token in line.split(":", 1)[1].split()]
    all_paths = set(sources)
    all_paths.update(path for path in dependencies if path.suffix.lower() in (".h", ".hpp", ".c", ".cpp"))
    all_paths.add(Path(__file__).resolve())
    return {str(path): sha256(path) for path in sorted(all_paths, key=str)
            if path.is_file()}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", type=Path, default=PRODUCTION)
    parser.add_argument("--report", type=Path,
                        default=ROOT / "portable/tests/live_game/evidence/end-game-modal-smoke.json")
    args = parser.parse_args()
    production = args.exe.resolve()
    receipt_path = production.with_suffix(".build.json")
    if not production.is_file() or not receipt_path.is_file():
        print("live SDL executable or its build receipt is missing", file=sys.stderr)
        return 2
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if not receipt.get("recovered_core", {}).get("profile"):
        print("build is not pinned to a recovered-core profile", file=sys.stderr)
        return 2
    command = list(receipt["command"])
    production_before = sha256(production)
    receipt_before = sha256(receipt_path)
    output = ROOT / "build/portable/tests/simant-live-endgame-smoke.exe"
    try:
        output_index = command.index("-o")
        command[output_index + 1] = str(output)
    except (ValueError, IndexError):
        print("build receipt has no reusable compiler command", file=sys.stderr)
        return 2
    injector = Path(__file__).with_name("end_game_key_injector.c")
    library_index = command.index("-L")
    source_names = {Path(token).name for token in command if token.endswith((".c", ".cpp"))}
    for name in ("end_game_flow.c", "end_game_view.c"):
        if name not in source_names:
            source = ROOT / "portable/ui_model/dialogs" / name
            command.insert(library_index, str(source))
            library_index += 1
    command.insert(library_index, str(injector))
    command.insert(library_index, "-DSIMANT_LIVE_GAME_TEST_DIAGNOSTICS=1")
    pinned_inputs = dependency_inputs(command, [injector])
    receipt_inputs = receipt.get("inputs", {})
    receipt_mismatches = []
    for name, expected in receipt_inputs.items():
        path = Path(name)
        if not path.is_absolute(): path = ROOT / path
        if not path.is_file() or sha256(path) != expected:
            receipt_mismatches.append(str(path))
    core_objects = receipt.get("recovered_core", {}).get("objects", {})
    object_pins = {}
    for name, expected in core_objects.items():
        path = Path(name)
        if not path.is_absolute(): path = ROOT / path
        if not path.is_file() or sha256(path) != expected:
            print(f"recovered core object does not match build receipt: {path}",
                  file=sys.stderr)
            return 2
        object_pins[str(path)] = expected
    pinned_inputs.update(object_pins)
    pinned_inputs_before = dict(pinned_inputs)
    output.parent.mkdir(parents=True, exist_ok=True)
    linked = subprocess.run(command, cwd=ROOT, text=True, capture_output=True,
                             timeout=120, check=False)
    if linked.returncode != 0:
        print(linked.stdout + linked.stderr, file=sys.stderr)
        return linked.returncode
    dll = production.parent / "SDL3.dll"
    if dll.is_file(): shutil.copy2(dll, output.parent / "SDL3.dll")

    report = args.report.resolve()
    report.parent.mkdir(parents=True, exist_ok=True)
    state_base = report.with_suffix("")
    event_report = state_base.with_name(state_base.name + "-events.json")
    frame_report = state_base.with_name(state_base.name + "-modal.bmp")
    final_frame = state_base.with_name(state_base.name + "-closed.bmp")
    for path in (event_report, frame_report, final_frame):
        path.unlink(missing_ok=True)
    env = dict(os.environ)
    env.update({
        "SDL_VIDEODRIVER": "dummy",
        "SIMANT_LIVE_GAME_TEST_DIAGNOSTICS": "1",
        "SIMANT_LIVE_END_GAME_SMOKE": "1",
        "SIMANT_LIVE_END_GAME_FRAME_REPORT": str(frame_report),
        "SIMANT_LIVE_SMOKE_EVENT_REPORT": str(event_report),
        "SIMANT_LIVE_SMOKE_STATE_REPORT": str(state_base),
    })
    run = subprocess.run([str(output), "--live-newgame", "--ticks", "1",
                          "--screenshot", str(final_frame)], cwd=ROOT, env=env,
                         text=True, capture_output=True, timeout=40, check=False)
    pinned_inputs_after = dependency_inputs(command, [injector])
    pinned_inputs_after.update({
        name: sha256(Path(name)) for name in object_pins
        if Path(name).is_file()
    })
    production_after = sha256(production)
    receipt_after = sha256(receipt_path)
    details_path = state_base.with_name(state_base.name + ".endgame.json")
    state_path = state_base.with_name(state_base.name + ".stats.json")
    if not details_path.is_file() or not event_report.is_file():
        print(run.stdout + run.stderr + f"\nchild return code: {run.returncode}",
              file=sys.stderr)
        print("EndGame report was not emitted", file=sys.stderr)
        return 1
    details = json.loads(details_path.read_text(encoding="utf-8"))
    events = json.loads(event_report.read_text(encoding="utf-8"))
    passed = (run.returncode == 0 and details["diagnostic_callback_invoked"] and
              details["callback_result"] == 0 and details["opened"] and
              details["closed"] and details["restart_boundary_reached"] and
              details["boundary"] == "NewGame(option=0)" and
              details["window_rect"][2] > details["window_rect"][0] and
              details["window_rect"][3] > details["window_rect"][1] and
              details["text_object_rects"][1][2] > details["text_object_rects"][1][0] and
              details["logical_key"] == 27 and details["wait_delay_ticks"] == 1800 and
              details["modal_event_polls"] > 0 and details["song_done_polls"] > 0 and
              details["song_requests"] == 1 and details["audio_driver_ready"] == 0 and
              details["modal_frame_saved"] and details["rendered_modal_frames"] == 1 and
              events["pushed_event_count"] == 2 and frame_report.is_file() and
              final_frame.is_file() and state_path.is_file())
    stable_pins = (pinned_inputs_before == pinned_inputs_after and
                   production_before == production_after and
                   receipt_before == receipt_after)
    passed = passed and stable_pins and not receipt_mismatches
    result = {
        "schema": "portable-live-end-game-smoke-v1",
        "claim": "the live EndGame host opened and rendered the real resource, consumed an SDL Escape through the source dialog-key path, closed the window, and failed closed at NewGame(option=0)",
        "status": "PASS" if passed else "FAIL",
        "scope": {
            "test_input_isolated": True,
            "live_recovered_state_or_rng_mutated_by_test_hook": False,
            "restart_continuation": "unsupported and explicitly reported",
            "modal_key": "SDL Escape -> BIOS logical key 27",
            "timeout": "source DialogWaitInit(100) represented as 1800 BIOS TickCount ticks; smoke dismisses by key before timeout",
            "audio": "driver disabled; source mySongIsDone returns true and gated myBeginSong is called once",
            "does_not_claim": ["NewGame continuation", "MenuQuit continuation",
                               "100-second wall-time expiry", "audio playback",
                               "DOS pixel equivalence"]
        },
        "command": [str(output), "--live-newgame", "--ticks", "1"],
        "build_receipt_sha256": sha256(receipt_path),
        "production_build_receipt": receipt,
        "production_executable_sha256": sha256(production),
        "input_pins": {
            "production_build_receipt_sha256_before": receipt_before,
            "production_build_receipt_sha256_after": receipt_after,
            "production_executable_sha256_before": production_before,
            "production_executable_sha256_after": production_after,
            "production_receipt_inputs_match": not receipt_mismatches,
            "production_receipt_input_mismatches": receipt_mismatches,
            "source_and_transitive_header_sha256": pinned_inputs_before,
            "source_and_transitive_header_pins_stable":
                pinned_inputs_before == pinned_inputs_after,
            "recovered_core_object_sha256": object_pins,
        },
        "smoke_executable_sha256": sha256(output),
        "test_event_driver": {"source": str(injector),
                              "sha256": sha256(injector), **events},
        "details": details,
        "native_state": json.loads(state_path.read_text(encoding="utf-8")),
        "modal_frame": {"path": str(frame_report), "sha256": sha256(frame_report)},
        "closed_frame": {"path": str(final_frame), "sha256": sha256(final_frame)},
        "stdout": run.stdout,
        "stderr": run.stderr,
        "returncode": run.returncode,
    }
    report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
