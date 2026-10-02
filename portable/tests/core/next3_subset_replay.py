#!/usr/bin/env python3
"""Run the original 370-field captures with next3's balloon cue state adapter.

This is deliberately a subset replay. The old DOS capture has no values for
the twelve next3-only balloon point/plane fields; these are source-BSS initialized
and remain outside the comparison. Every original captured field remains in
scope and must match.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
PORT = ROOT / "portable"
PROFILE = ROOT / "build/workers/recovered_source_next3/generated"
CAPTURE_DIR = ROOT / "build/workers/core_proof_next2"
OUTPUT_DIR = ROOT / "build/workers/core_proof_next3"
RUNNER_PATH = PORT / "tests/core/run_native_tick_fixture.py"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    runner_sha_before = sha(RUNNER_PATH)
    spec = importlib.util.spec_from_file_location("native_tick_fixture_runner",
                                                  RUNNER_PATH)
    if spec is None or spec.loader is None:
        raise SystemExit("cannot import the captured-fixture runner")
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    compiler = shutil.which("gcc") or "C:/msys64/mingw64/bin/gcc.exe"
    helper_scratch = OUTPUT_DIR / "balloon-adapter-objects"
    helper_scratch.mkdir(parents=True, exist_ok=True)
    adapter_objects: list[Path] = []
    for index, source in enumerate((
        PORT / "game/recovered/balloon_adapter.c",
        PORT / "ui_model/balloons/balloons.c",
    )):
        obj = helper_scratch / f"balloon-{index}.o"
        result = subprocess.run([
            compiler, "-std=c11", "-Wall", "-Wextra", "-Werror",
            "-I", str(ROOT), "-I", str(PORT), "-I", str(PROFILE),
            "-c", str(source), "-o", str(obj),
        ], cwd=ROOT, text=True, capture_output=True, check=False, timeout=30)
        if result.returncode:
            print(result.stdout + result.stderr)
            return result.returncode
        adapter_objects.append(obj)

    original_runtime = runner.create_sequence_runtime_c
    original_run = runner.run
    execution_output: dict[str, str] = {}

    def runtime_with_balloon_bindings(report: dict) -> str:
        source = original_runtime(report)
        injected = r'''
#include "portable/game/recovered/balloon_adapter.h"
static unsigned next3_balloon_calls[4];
void EggBalloons(int16_t x, int16_t y, int16_t plane)
{ ++next3_balloon_calls[1]; sim_recovered_egg_balloons(x, y, plane); }
void FightBalloons(int16_t x, int16_t y, int16_t plane)
{ ++next3_balloon_calls[0]; sim_recovered_fight_balloons(x, y, plane); }
void QueenBalloons(int16_t x, int16_t y, int16_t plane)
{ ++next3_balloon_calls[2]; sim_recovered_queen_balloons(x, y, plane); }
void RestBalloons(int16_t x, int16_t y, int16_t plane)
{ ++next3_balloon_calls[3]; sim_recovered_rest_balloons(x, y, plane); }
'''
        source = source.replace("int main(int argc,char **argv)",
                                injected + "\nint main(int argc,char **argv)")
        source = source.replace(
            '    printf("SEQUENCE_STATE_RNG_PASS ticks=',
            '    printf("NEXT3_BALLOON_CALLS egg=%u fight=%u queen=%u rest=%u\\n", '
            'next3_balloon_calls[1], next3_balloon_calls[0], '
            'next3_balloon_calls[2], next3_balloon_calls[3]);\n'
            '    printf("NEXT3_UNCAPTURED_CUE_FIELDS egg_xy=%d,%d egg_planes=%d,%d '
            'fight_xy=%d,%d fight_planes=%d,%d queen_xy=%d,%d queen_planes=%d,%d '
            'rest_xy=%d,%d rest_planes=%d,%d\\n", '
            'state.fd_50F6_08DE.x,state.fd_50F6_08DE.y,state.fd_50F6_0AD8,state.fd_50F6_0ACA,'
            'state.fd_50F6_09F2.x,state.fd_50F6_09F2.y,state.fd_50F6_0B06,state.fd_50F6_0AEA,'
            'state.fd_50F6_0A8A.x,state.fd_50F6_0A8A.y,state.fd_50F6_0C3A,state.fd_50F6_0B08,'
            'state.fd_50F6_0AB2.x,state.fd_50F6_0AB2.y,state.fd_50F6_0D9A,state.fd_50F6_0D68);\n'
            '    printf("SEQUENCE_STATE_RNG_PASS ticks=')
        return source

    def run_with_balloon_objects(command: list[str], *, capture: bool = False,
                                 timeout: float | None = None) -> subprocess.CompletedProcess[str]:
        actual = list(command)
        if "-Wl,--gc-sections" in actual:
            actual.extend(str(path) for path in adapter_objects)
        result = original_run(actual, capture=capture, timeout=timeout)
        if actual and Path(actual[0]).name.lower() == "native-sequence.exe":
            execution_output["stdout"] = result.stdout or ""
        return result

    runner.GENERATED = PROFILE.resolve()
    runner.SEQUENCE_SCRATCH = OUTPUT_DIR / "sequence-native"
    runner.create_sequence_runtime_c = runtime_with_balloon_bindings
    runner.run = run_with_balloon_objects

    next2_provenance = json.loads(
        (ROOT / "build/workers/recovered_source_next2/generated/provenance.json")
        .read_text(encoding="utf-8"))
    next3_provenance = json.loads((PROFILE / "provenance.json").read_text(
        encoding="utf-8"))
    old_fields = {row["name"]: row for row in next2_provenance["recovered_state"]["fields"]}
    new_fields = {row["name"]: row for row in next3_provenance["recovered_state"]["fields"]}
    if any(old_fields[name] != new_fields.get(name) for name in old_fields):
        raise SystemExit("next3 changed an existing recovered-state field descriptor")
    added = sorted(set(new_fields) - set(old_fields))
    expected_added = sorted((
        "fd_50F6_08DE", "fd_50F6_09F2", "fd_50F6_0A8A", "fd_50F6_0AB2",
        "fd_50F6_0ACA", "fd_50F6_0AD8", "fd_50F6_0AEA", "fd_50F6_0B06",
        "fd_50F6_0B08", "fd_50F6_0C3A", "fd_50F6_0D68", "fd_50F6_0D9A",
    ))
    if added != expected_added:
        raise SystemExit(f"unexpected next3 added fields: {added}")
    module_hashes = {item["name"]: item["generated_sha256"]
                     for item in next3_provenance["modules"]}
    old_module_hashes = {item["name"]: item["generated_sha256"]
                         for item in next2_provenance["modules"]}
    if module_hashes != old_module_hashes:
        raise SystemExit("next3 generated game-body modules differ from next2")

    comparison_header = sha(PROFILE / "recovered_state.h")
    comparison_provenance = sha(PROFILE / "provenance.json")
    old_header = sha(ROOT / "build/workers/recovered_source_next2/generated/recovered_state.h")
    result_rows = []
    for filename in ("sequence-5a31-0.json", "sequence-1234-1.json",
                     "sequence-5a31-2.json"):
        source_report = json.loads((CAPTURE_DIR / filename).read_text(encoding="utf-8"))
        report = json.loads(json.dumps(source_report))
        report["recovered_state_header_sha256"] = comparison_header
        report["comparison_provenance_sha256"] = comparison_provenance
        report["comparison_profile"] = "build/workers/recovered_source_next3/generated"
        report["captured_dos_header_sha256"] = old_header
        report["comparison_field_scope"] = {
            "captured_original_dos_field_count": len(report["source_globals"]),
            "captured_original_dos_fields": report["source_globals"],
            "next3_nonpointer_field_count": len(report["source_globals"]) + len(added),
            "compared_fields": "all 370 fields in the preserved DOS capture; each common next2/next3 descriptor is identical",
            "excluded_fields": added,
            "excluded_field_reason": "12 source-backed balloon cue point/plane fields were added to next3 after the DOS captures; the captures have no per-tick values for these fields. They remain initialized from next3 BSS and are reported but not asserted against DOS.",
            "generated_game_body_modules_identical": True,
            "generated_module_hashes": module_hashes,
            "cue_entrypoints": "The four source-compatible cue entrypoints are bound to the actual next3 portable/game/recovered/balloon_adapter.c implementation; no fail-closed cue stub is used.",
        }
        report["next3_actual_balloon_adapter"] = True
        fixture_out = OUTPUT_DIR / filename
        fixture_out.parent.mkdir(parents=True, exist_ok=True)
        fixture_out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        code = runner.run_sequence_mode(report)
        output = execution_output.get("stdout", "")
        result_rows.append({
            "fixture": filename,
            "status": "PASS 256/256 common-370 subset" if code == 0 else f"FAIL exit={code}",
            "exit_code": code,
            "comparison_header_sha256": comparison_header,
            "comparison_provenance_sha256": comparison_provenance,
            "descriptor_sha256": sha(fixture_out),
            "source_report_sha256": sha(CAPTURE_DIR / filename),
            "snapshot_sha256": source_report["snapshot_sha256"],
            "native_output_sha256": hashlib.sha256(output.encode("utf-8")).hexdigest(),
            "native_output_line_count": len(output.splitlines()),
            "balloon_call_line": next((line for line in output.splitlines()
                                        if line.startswith("NEXT3_BALLOON_CALLS ")), None),
            "uncaptured_cue_line": next((line for line in output.splitlines()
                                          if line.startswith("NEXT3_UNCAPTURED_CUE_FIELDS ")), None),
            "success_line": next((line for line in output.splitlines()
                                  if line.startswith("SEQUENCE_STATE_RNG_PASS ")), None),
        })
        if code != 0:
            return code

    if sha(RUNNER_PATH) != runner_sha_before:
        raise SystemExit("shared native replay runner changed during next3 subset run")
    pinned = {
        "scope": "370 captured DOS fields only; 12 new next3 cue fields are explicitly excluded from DOS assertion",
        "next3_added_uncaptured_fields": added,
        "generated_game_body_modules_identical_to_next2": len(module_hashes),
        "actual_balloon_adapter_objects": [str(path.relative_to(ROOT))
                                            for path in adapter_objects],
        "cases": result_rows,
        "runner_sha256_stable": runner_sha_before,
    }
    evidence = PORT / "research/core-proof/original-256-tick-summary-next3-common370-20261002.json"
    evidence.write_text(json.dumps(pinned, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(pinned, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
