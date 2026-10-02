#!/usr/bin/env python3
"""Build and run the bounded natural game-over -> EndGame -> scenario 0x0202 SDL smoke.

This runner is intentionally fail-closed. It requires a current NEXT6 production build receipt, compiles an isolated diagnostics executable from that command, then requires a natural recovered EndGame callback, successful scenario continuation, and one resource-derived physical SDL click. It never requests the forced EndGame diagnostic action. The finite tick limit and subprocess timeout are mandatory.
"""
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
INJECTOR = Path(__file__).with_name("scenario_202_click_injector.c")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compile_inputs(command: list[str]) -> dict[str, str]:
    compiler = command[0]
    source_indices = [i for i, token in enumerate(command)
                      if token.endswith((".c", ".cpp"))]
    sources = [Path(command[i]).resolve() for i in source_indices]
    sources.append(INJECTOR.resolve())
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
    deps = [Path(token).resolve() for token in line.split(":", 1)[1].split()]
    paths = set(sources)
    paths.update(p for p in deps if p.suffix.lower() in (".c", ".cpp", ".h", ".hpp"))
    return {str(path): sha256(path) for path in sorted(paths, key=str)
            if path.is_file()}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", type=Path, default=PRODUCTION)
    parser.add_argument("--report", type=Path,
        default=ROOT / "portable/tests/live_game/evidence/natural-gameover-202-live-smoke.json")
    parser.add_argument("--timeout", type=float, default=58.0)
    args = parser.parse_args()
    if not (0 < args.timeout <= 60):
        print("smoke timeout must be between 0 and 60 seconds", file=sys.stderr)
        return 2
    production = args.exe.resolve()
    receipt_path = production.with_suffix(".build.json")
    if not production.is_file() or not receipt_path.is_file():
        print("live SDL executable or build receipt is missing", file=sys.stderr)
        return 2
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    command = list(receipt.get("command", []))
    if not receipt.get("recovered_core", {}).get("profile") or not command:
        print("production receipt lacks a recovered-core profile/command", file=sys.stderr)
        return 2
    command_text = " ".join(command)
    core_profile = str(receipt.get("recovered_core", {}).get("profile", ""))
    if ("SIMANT_ENABLE_NEW_GAME_NEXT5" not in command_text or
            "recovered_source_next7" not in core_profile):
        print("production receipt is not compiled with the guarded NEXT7 profile",
              file=sys.stderr)
        return 2
    try:
        out_index = command.index("-o")
        output = ROOT / "build/portable/tests/simant-live-natural-gameover-202-smoke.exe"
        command[out_index + 1] = str(output)
    except (ValueError, IndexError):
        print("production receipt has no reusable compiler command", file=sys.stderr)
        return 2
    if "end_game_flow.c" not in {Path(x).name for x in command if x.endswith(".c")}:
        command.insert(command.index("-L"),
                       str(ROOT / "portable/ui_model/dialogs/end_game_flow.c"))
    if "end_game_view.c" not in {Path(x).name for x in command if x.endswith(".c")}:
        command.insert(command.index("-L"),
                       str(ROOT / "portable/ui_model/dialogs/end_game_view.c"))
    library_index = command.index("-L")
    command.insert(library_index, "-DSIMANT_LIVE_GAME_TEST_DIAGNOSTICS=1")
    command.insert(library_index, "-DSIMANT_ENABLE_END_GAME_ACTION_DIAGNOSTIC=1")
    command.insert(library_index, str(INJECTOR))

    mismatches = []
    for name, expected in receipt.get("inputs", {}).items():
        path = Path(name)
        if not path.is_absolute(): path = ROOT / path
        if not path.is_file() or sha256(path) != expected:
            mismatches.append(str(path))
    if mismatches:
        print("production receipt has stale source inputs: " + ", ".join(mismatches),
              file=sys.stderr)
        return 2
    object_pins = {}
    for name, expected in receipt.get("recovered_core", {}).get("objects", {}).items():
        path = Path(name)
        if not path.is_absolute(): path = ROOT / path
        if not path.is_file() or sha256(path) != expected:
            print(f"recovered object does not match receipt: {path}", file=sys.stderr)
            return 2
        object_pins[str(path)] = expected
    before = compile_inputs(command)
    before.update(object_pins)
    exe_before, receipt_before = sha256(production), sha256(receipt_path)
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
    prefix = report.with_suffix("")
    endgame_ready = prefix.with_name(prefix.name + "-endgame-ready")
    ready = prefix.with_name(prefix.name + "-selector-ready")
    event_report = prefix.with_name(prefix.name + "-events.json")
    state_report = prefix.with_name(prefix.name + ".stats.json")
    newgame_report = prefix.with_name(prefix.name + ".newgame202.json")
    for path in (endgame_ready, ready, event_report, state_report,
                 newgame_report): path.unlink(missing_ok=True)
    env = dict(os.environ)
    # Make the no-forced-action boundary explicit even if the caller's shell
    # happens to retain variables from a prior forced smoke.
    env.pop("SIMANT_LIVE_NEWGAME_202_DIAGNOSTIC", None)
    env.update({
        "SDL_VIDEODRIVER": "dummy",
        "SIMANT_LIVE_GAME_TEST_DIAGNOSTICS": "1",
        "SIMANT_LIVE_NATURAL_GAMEOVER_202_DIAGNOSTIC": "1",
        "SIMANT_LIVE_ENDGAME_READY": str(endgame_ready),
        "SIMANT_LIVE_SCENARIO_READY": str(ready),
        "SIMANT_LIVE_SCENARIO_EVENT_REPORT": str(event_report),
        "SIMANT_LIVE_SMOKE_STATE_REPORT": str(prefix),
    })
    timed_out = False
    try:
        run = subprocess.run([str(output), "--live-newgame", "--ticks", "4096"],
                             cwd=ROOT, env=env, text=True, capture_output=True,
                             timeout=args.timeout, check=False)
        run_stdout, run_stderr, returncode = run.stdout, run.stderr, run.returncode
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        run_stdout = exc.stdout.decode(errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        run_stderr = exc.stderr.decode(errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        returncode = None
    after = compile_inputs(command)
    after.update({name: sha256(Path(name)) for name in object_pins
                  if Path(name).is_file()})
    production_stable = sha256(production) == exe_before
    receipt_stable = sha256(receipt_path) == receipt_before
    pins_stable = before == after
    event = json.loads(event_report.read_text(encoding="utf-8")) \
        if event_report.is_file() else {}
    state = json.loads(state_report.read_text(encoding="utf-8")) \
        if state_report.is_file() else {}
    continuation = json.loads(newgame_report.read_text(encoding="utf-8")) \
        if newgame_report.is_file() else {}
    callback_input = continuation.get("gameover_input", {})
    rng_before = continuation.get("rng_before", {})
    rng_after = continuation.get("rng_after", {})
    # The action stays false in natural mode: only the source-driven game-over
    # callback can publish a callback count and reach the real selector here.
    passed = (not timed_out and returncode == 0 and
              event.get("target_derived_from_resource") is True and
              event.get("endgame_key_events") == 2 and
              event.get("scenario_mouse_events") == 2 and
              event.get("pushed_event_count") == 4 and state_report.is_file() and
              continuation.get("diagnostic_action_called") is False and
              continuation.get("gameover_callback_count", 0) >= 1 and
              continuation.get("gameover_callback_completed") is True and
              callback_input.get("scenario") == 1 and
              callback_input.get("screen_width") == 640 and
              set(("s", "c")).issubset(rng_before) and
              set(("s", "c")).issubset(rng_after) and
              continuation.get("scenario_result_code") == 0x0202 and
              continuation.get("source_newgame_returned") is True and
              continuation.get("scenario_index_after") == 1 and
              continuation.get("completed_ticks_after", 0) >
                  continuation.get("gameover_entry_completed_ticks", 0) and
              production_stable and receipt_stable and pins_stable)
    result = {
        "schema": "portable-live-natural-gameover-202-smoke-v1",
        "status": "PASS" if passed else "TIMED_OUT" if timed_out else "FAIL",
        "claim": "bounded attempt to observe the natural NEXT7 EndGame-to-NewGame route under source-paced live simulation; PASS requires a recovered EndGame callback, selector result 0x0202, and continued source simulation",
        "natural_endgame_callback_observed":
            continuation.get("gameover_callback_count", 0) >= 1,
        "scenario_click_observed":
            event.get("scenario_mouse_events") == 2,
        "limits": [
            "requires a natural game-over callback; does not force the EndGame diagnostic action",
            "only scenario result 0x0202 is targeted",
            "does not claim tutorial, load, save, or MenuQuit routes",
            "time-bounded smoke; no full-playability claim",
        ],
        "command": [str(output), "--live-newgame", "--ticks", "4096"],
        "timeout_seconds": args.timeout,
        "production_build_receipt": receipt,
        "production_build_receipt_sha256_before": receipt_before,
        "production_build_receipt_sha256_after": sha256(receipt_path),
        "production_executable_sha256_before": exe_before,
        "production_executable_sha256_after": sha256(production),
        "source_and_transitive_header_sha256_before": before,
        "source_pins_stable": pins_stable,
        "recovered_core_object_sha256": object_pins,
        "smoke_executable_sha256": sha256(output),
        "event_driver_source": str(INJECTOR),
        "event_driver_sha256": sha256(INJECTOR),
        "physical_event_report": event,
        "native_state_report": state,
        "source_newgame_report": continuation,
        "timed_out": timed_out,
        "stdout": run_stdout,
        "stderr": run_stderr,
        "returncode": returncode,
    }
    report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
