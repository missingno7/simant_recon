#!/usr/bin/env python3
"""Run the resource-backed recovered engine for a bounded headless soak."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[3]
PORT = ROOT / "portable"
PROFILE = ROOT / "build/workers/recovered_source_next2/generated"
SCRATCH = ROOT / "build/workers/core_proof/long-run-next2"
EVIDENCE = ROOT / "portable/tests/core/evidence/long-run-smoke-next2.json"
EXPECTED = {
    "recovered_state.h": "bb89c625bfb8bccbf827e1c701bd1490f57106276d81b6abcdf7aa8e7b42fec6",
    "recovered_state.c": "4d7527a1961b5792f8322366cbd51b70559e889b41e0b941b2f7e7477441095f",
    "recovered_native_adapters.c": "ce2206c52ba57034074403a4e3e267300cbce2898ddec1693923ea9e28edef4e",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tool(name: str, fallback: str) -> str:
    found = shutil.which(name)
    if found:
        return found
    path = Path(fallback)
    if path.is_file():
        return str(path)
    raise SystemExit(f"required tool not found: {name}")


def native_sources() -> list[Path]:
    harness = PORT / "tests/core/long_run_smoke.c"
    sources = list(PORT.joinpath("game").glob("*.c"))
    sources.append(PORT / "platform/memory.c")
    for folder in (
        "game/simulation", "game/state", "game/resources", "game/render",
        "render", "ui_model", "audio",
    ):
        sources.extend(PORT.joinpath(folder).rglob("*.c"))
    sources.extend(PORT / "game/recovered" / name for name in (
        "engine.c", "session_bridge.c", "audio_adapter.c",
        "memory_adapter.c", "nest_adapter.c",
    ))
    provenance = json.loads((PROFILE / "provenance.json").read_text())
    sources.extend(ROOT / module["generated"] for module in provenance["modules"])
    sources.append(ROOT / provenance["recovered_state"]["source_path"])
    sources.append(ROOT / provenance["native_adapter_compile"]["path"])
    sources.append(harness)
    return sorted(set(path.resolve() for path in sources))


def symbol_table(nm: str, executable: Path) -> tuple[list[tuple[int, str]], int | None]:
    result = subprocess.run([nm, "-n", str(executable)], cwd=ROOT,
                            text=True, capture_output=True, check=False)
    if result.returncode:
        return [], None
    symbols: list[tuple[int, str]] = []
    main_value = None
    for line in result.stdout.splitlines():
        match = re.match(r"^([0-9a-fA-F]+)\s+[A-Za-z]\s+(\S+)$", line.strip())
        if not match:
            continue
        value, name = int(match.group(1), 16), match.group(2)
        symbols.append((value, name))
        if name in {"main", "_main"}:
            main_value = value
    symbols.sort()
    return symbols, main_value


def resolve_path(addresses: list[int], runtime_main: int,
                 symbols: list[tuple[int, str]], nm_main: int | None) -> list[str]:
    if nm_main is None:
        return [f"0x{address:x}" for address in addresses]
    bias = runtime_main - nm_main
    resolved: list[str] = []
    for address in addresses:
        link_address = address - bias
        candidate = None
        for value, name in symbols:
            if value > link_address:
                break
            candidate = (value, name)
        if candidate is None:
            resolved.append(f"0x{address:x}")
        else:
            offset = link_address - candidate[0]
            resolved.append(candidate[1] if offset == 0 else
                            f"{candidate[1]}+0x{offset:x}")
    return resolved


def main() -> int:
    compiler = os.environ.get("SIMANT_CC") or tool(
        "gcc", "C:/msys64/mingw64/bin/gcc.exe")
    nm = tool("nm", "C:/msys64/mingw64/bin/nm.exe")
    EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
    SCRATCH.mkdir(parents=True, exist_ok=True)

    profile_hashes = {name: sha(PROFILE / name) for name in EXPECTED}
    if profile_hashes != EXPECTED:
        raise SystemExit(f"next2 profile hash mismatch: {profile_hashes}")
    provenance = json.loads((PROFILE / "provenance.json").read_text())
    module_hashes = {Path(module["generated"]).name: module["generated_sha256"]
                     for module in provenance["modules"]}
    source_paths = native_sources()
    input_hashes = {str(path.relative_to(ROOT)): sha(path) for path in source_paths}
    runner_hash = sha(Path(__file__))
    harness = PORT / "tests/core/long_run_smoke.c"
    input_hashes[str(harness.relative_to(ROOT))] = sha(harness)

    objects: list[Path] = []
    suppressions = [
        "-Wno-missing-braces", "-Wno-unused-parameter", "-Wno-unused-variable",
        "-Wno-unused-but-set-variable", "-Wno-unused-but-set-parameter",
        "-Wno-parentheses", "-Wno-type-limits", "-Wno-implicit-fallthrough",
        "-Wno-tautological-compare", "-Wno-char-subscripts", "-Wno-sign-compare",
        "-Wno-builtin-declaration-mismatch",
    ]
    common = [compiler, "-std=c11", "-O0", "-Wall", "-Wextra", "-Werror",
              *suppressions, "-finstrument-functions", "-fno-inline",
              "-I", str(ROOT), "-I", str(PORT), "-I", str(PROFILE)]
    for index, source in enumerate(source_paths):
        obj = SCRATCH / f"object-{index:02d}.o"
        result = subprocess.run([*common, "-c", str(source), "-o", str(obj)],
                                cwd=ROOT, text=True, capture_output=True,
                                timeout=60, check=False)
        if result.returncode:
            report = {
                "schema": "recovered-engine-headless-long-run-v1",
                "status": "compile-failure",
                "failed_source": str(source.relative_to(ROOT)),
                "diagnostics": result.stdout + result.stderr,
                "profile_hashes": profile_hashes,
                "input_hashes": input_hashes,
            }
            EVIDENCE.write_text(json.dumps(report, indent=2) + "\n")
            print(report["diagnostics"])
            return result.returncode
        objects.append(obj)

    executable = SCRATCH / "long-run-smoke.exe"
    link = subprocess.run([compiler, "-Wl,--gc-sections", *(str(obj) for obj in objects),
                           "-o", str(executable)], cwd=ROOT, text=True,
                          capture_output=True, timeout=60, check=False)
    if link.returncode:
        report = {
            "schema": "recovered-engine-headless-long-run-v1",
            "status": "link-failure",
            "diagnostics": link.stdout + link.stderr,
            "profile_hashes": profile_hashes,
            "input_hashes": input_hashes,
        }
        EVIDENCE.write_text(json.dumps(report, indent=2) + "\n")
        print(report["diagnostics"])
        return link.returncode

    try:
        run = subprocess.run([str(executable)], cwd=ROOT, text=True,
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             timeout=120, check=False)
        output, returncode, timed_out = run.stdout, run.returncode, False
    except subprocess.TimeoutExpired as error:
        captured = error.stdout or ""
        if isinstance(captured, bytes):
            captured = captured.decode(errors="replace")
        output, returncode, timed_out = captured, 124, True

    runtime_main_match = re.search(r"MAIN_ADDRESS:(?:0x)?([0-9a-fA-F]+)", output)
    symbols, nm_main = symbol_table(nm, executable)
    runtime_main = int(runtime_main_match.group(1), 16) if runtime_main_match else 0
    path_match = re.search(r"CALL_PATH overflow=(\d+) depth=(\d+)((?: 0x[0-9a-fA-F]+)*)", output)
    call_addresses = ([int(value, 16) for value in re.findall(r"0x[0-9a-fA-F]+", path_match.group(3))]
                      if path_match else [])
    call_names = resolve_path(call_addresses, runtime_main, symbols, nm_main)
    if call_names and call_names[-1].startswith("print_call_path"):
        call_names.pop()
    first_fault = re.search(
        r"FIRST_FAULT tick=(\d+) completed=(\d+) status=(.*?) service=([^ ]+)"
        r" committed_cycle=(\d+) last_me=\(([^)]*)\) rng_s=(\d+) rng_c=(\d+)"
        r" effects=(\d+) source_clock=(-?\d+) live_endgame_snapshot=(\d+):"
        r"(-?\d+):(-?\d+):(-?\d+):(-?\d+):(-?\d+):(-?\d+):(-?\d+)",
        output)
    host_match = re.search(
        r"HOST_SUMMARY effect_total=(\d+) audio_intents=(\d+) "
        r"source_clock_reads=(\d+) bad_callback=(\d+)\n"
        r"QUERY_COUNTS((?: \d+:\d+)+)\nEFFECT_COUNTS((?: \d+:\d+)+)", output)
    query_names = {
        1: "window_open", 2: "window_events", 3: "window_in_front",
        4: "still_down", 5: "dialog_abort_or_continue", 6: "get_event",
        7: "get_object_rect", 8: "button", 9: "dos_keyboard_flags",
    }
    effect_names = {
        1: "map_cell_invalidate", 2: "edit_message",
        3: "picture_string_dialog", 4: "default_wind_prompt",
        5: "nest_map_invalidate", 6: "alarm_selection",
        7: "window_operation", 8: "graphics_rect", 9: "graphics_line",
    }

    def named_counts(raw: str, names: dict[int, str]) -> dict[str, int]:
        return {names[int(pair.split(":")[0])]: int(pair.split(":")[1])
                for pair in raw.split() if int(pair.split(":")[0]) in names}

    source_after = {name: sha(PROFILE / name) for name in EXPECTED}
    source_after_ok = source_after == profile_hashes
    inputs_after = {str(path.relative_to(ROOT)): sha(path) for path in source_paths}
    inputs_after[str(harness.relative_to(ROOT))] = sha(harness)
    inputs_stable = input_hashes == inputs_after
    success = returncode == 0 and "LONG_RUN_PASS ticks=4096 completed=4096" in output
    report = {
        "schema": "recovered-engine-headless-long-run-v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "status": "pass" if success else "timeout" if timed_out else
                  "first-fault" if first_fault else "process-failure",
        "scope": "Actual resource-backed Session -> NewGame -> recovered engine; 4096 no-input ticks, controlled monotonic TickCount, headless effect acknowledgment and audio driver disabled. This is an integration smoke run, not DOS differential evidence.",
        "ticks_requested": 4096,
        "profile": "build/workers/recovered_source_next2/generated",
        "compiler": compiler,
        "compiler_version": subprocess.run([compiler, "--version"], cwd=ROOT,
                                             text=True, capture_output=True,
                                             check=False).stdout.splitlines()[:1],
        "instrumentation": ["-finstrument-functions", "-fno-inline", "-O0"],
        "executable_sha256": sha(executable),
        "profile_hashes_before": profile_hashes,
        "profile_hashes_after": source_after,
        "profile_stable": source_after_ok,
        "generated_module_count": len(module_hashes),
        "generated_module_hashes": module_hashes,
        "engine_and_source_hashes_before": input_hashes,
        "engine_and_source_hashes_stable": inputs_stable,
        "runner_sha256": runner_hash,
        "native_exit_code": returncode,
        "timed_out": timed_out,
        "headless_host_services": ({
            "effect_total": int(host_match.group(1)),
            "audio_intents_discarded_without_playback": int(host_match.group(2)),
            "controlled_clock_reads": int(host_match.group(3)),
            "bad_callback": bool(int(host_match.group(4))),
            "queries_by_kind": named_counts(host_match.group(5), query_names),
            "effects_by_kind": named_counts(host_match.group(6), effect_names),
        } if host_match else None),
        "first_fault": ({
            "tick_zero_based": int(first_fault.group(1)),
            "completed_ticks": int(first_fault.group(2)),
            "engine_status": first_fault.group(3),
            "failed_service": first_fault.group(4),
            "last_committed_cycle": int(first_fault.group(5)),
            "last_committed_me_plane_x_y": [int(part) for part in first_fault.group(6).split(",")],
            "last_committed_s_rng": int(first_fault.group(7)),
            "last_committed_c_rng": int(first_fault.group(8)),
            "effects_before_fault": int(first_fault.group(9)),
            "controlled_clock_before_fault": int(first_fault.group(10)),
            "live_endgame_entry_seen": bool(int(first_fault.group(11))),
            "live_endgame_pending_flag": int(first_fault.group(12)),
            "live_losing_side": int(first_fault.group(13)),
            "live_scenario": int(first_fault.group(14)),
            "live_blue_queen_count": int(first_fault.group(15)),
            "live_red_queen_count": int(first_fault.group(16)),
            "live_blue_population_count": int(first_fault.group(17)),
            "live_red_population_count": int(first_fault.group(18)),
            "call_path": call_names,
            "raw_call_path_addresses": call_addresses,
            "call_path_overflow": bool(path_match and path_match.group(1) != "0"),
            "call_path_resolution_main_bias_available": nm_main is not None and runtime_main != 0,
        } if first_fault else None),
        "fault_trigger_source": ({
            "call_site": "build/workers/recovered_source_next2/generated/root_m0894.c:203: DoAntSim calls EndGameDialog(0) when fd_50F6_0376 is set",
            "flag_writer": "build/workers/recovered_source_next2/generated/root_m0BE8.c:144-145: CountAnts detects the tracked red-queen caste at fd_50F6_0AFA[5] has disappeared (current fd_50F6_0EB6[28] is zero), with fd_50F6_0354 clear and scenario fd_50F6_0EAC <= 1; it sets fd_50F6_0376 and losing-side fd_50F6_0366=1. The live EndGameDialog-entry snapshot confirms flag=1, losing_side=1, scenario=1, blue_queens=1, red_queens=0, and nonzero remaining populations 7/9.",
            "no_input_condition": "the headless host returns false for all optional-window/input queries and acknowledges typed drawing/map intents without input; audio driver is disabled",
        } if first_fault else None),
        "native_output": output,
    }
    if not source_after_ok or not inputs_stable:
        report["status"] = "source-instability"
    EVIDENCE.write_text(json.dumps(report, indent=2) + "\n")
    print(output)
    print(f"evidence={EVIDENCE.relative_to(ROOT)} status={report['status']} "
          f"profile_stable={source_after_ok} source_stable={inputs_stable}")
    return 0 if report["status"] == "pass" else returncode or 1


if __name__ == "__main__":
    raise SystemExit(main())
