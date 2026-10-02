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
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
from contextlib import redirect_stdout

ROOT = Path(__file__).resolve().parents[3]
PORT = ROOT / "portable"
PROFILE = ROOT / "build/workers/recovered_source_next7/generated"
CAPTURE_DIR = ROOT / "build/workers/core_proof_next2"
OUTPUT_DIR = ROOT / "build/workers/core_proof_next7"
RUNNER_PATH = PORT / "tests/core/run_native_tick_fixture.py"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_closure() -> dict[str, str]:
    profile = PROFILE.resolve()
    provenance = json.loads((profile / "provenance.json").read_text(encoding="utf-8"))
    sources = [ROOT / item["generated"] for item in provenance["modules"]]
    sources += [ROOT / provenance["recovered_state"]["source_path"],
                ROOT / provenance["native_adapter_compile"]["path"]]
    sources += [ROOT / value for value in (
        "portable/game/simulation/rng.c",
        "portable/game/simulation/movement.c",
        "portable/game/simulation/nest.c",
        "portable/game/state/world.c",
        "portable/platform/memory.c",
        "portable/game/recovered/memory_adapter.c",
        "portable/game/recovered/nest_adapter.c",
        "portable/game/recovered/audio_adapter.c",
        "portable/audio/intent.c",
        "portable/game/recovered/balloon_adapter.c",
        "portable/ui_model/balloons/balloons.c",
    )]
    compiler = shutil.which("gcc") or "C:/msys64/mingw64/bin/gcc.exe"
    dependencies = {path.resolve() for path in sources}
    for source in sources:
        result = subprocess.run([
            compiler, "-MM", f"-I{ROOT}", f"-I{profile}", f"-I{PORT}",
            str(source),
        ], cwd=ROOT, text=True, capture_output=True, check=False, timeout=30)
        if result.returncode:
            raise SystemExit(f"dependency scan failed for {source}: {result.stderr}")
        line = result.stdout.replace("\\\n", " ")
        if ": " not in line:
            raise SystemExit(f"unparseable dependency output for {source}: {result.stdout}")
        dependencies.update(Path(value).resolve()
                            for value in line.split(": ", 1)[1].split())
    dependencies.update((ROOT / value).resolve() for value in (
        "portable/tests/core/run_native_tick_fixture.py",
        "portable/tests/core/next7_subset_replay.py",
    ))
    dependencies.add((profile / "provenance.json").resolve())
    return {path.relative_to(ROOT).as_posix(): sha(path)
            for path in sorted(dependencies) if path.is_file()}


def main() -> int:
    runner_sha_before = sha(RUNNER_PATH)
    harness_sha_before = sha(Path(__file__))
    input_hashes_before = source_closure()
    capture_hashes_before = {}
    for filename in ("sequence-5a31-0.json", "sequence-1234-1.json",
                     "sequence-5a31-2.json"):
        report_path = CAPTURE_DIR / filename
        original = json.loads(report_path.read_text(encoding="utf-8"))
        capture_hashes_before[filename] = {
            "descriptor_sha256": sha(report_path),
            "snapshot_sha256": sha(ROOT / original["snapshot_file"]),
        }
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
            '    printf("NEXT7_BALLOON_CALLS egg=%u fight=%u queen=%u rest=%u\\n", '
            'next3_balloon_calls[1], next3_balloon_calls[0], '
            'next3_balloon_calls[2], next3_balloon_calls[3]);\n'
            '    printf("NEXT7_UNCAPTURED_CUE_FIELDS egg_xy=%d,%d egg_planes=%d,%d '
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
        # NEXT5/NEXT7's genuine controls TU carries its own source typedef. The
        # baseline runner's forced Handle compatibility declaration conflicts
        # with that TU and is unnecessary in it.
        if any(Path(value).name == "root_m0798_controls.c" for value in actual):
            actual = [value for value in actual if not value.startswith("-include")]
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

    next5_provenance = json.loads(
        (ROOT / "build/workers/recovered_source_next5/generated/provenance.json")
        .read_text(encoding="utf-8"))
    next7_provenance = json.loads((PROFILE / "provenance.json").read_text(
        encoding="utf-8"))
    old_fields = {row["name"]: row for row in next5_provenance["recovered_state"]["fields"]}
    new_fields = {row["name"]: row for row in next7_provenance["recovered_state"]["fields"]}
    if old_fields != new_fields:
        raise SystemExit("NEXT7 changed the 411-field NEXT5 state descriptor")
    module_hashes = {item["name"]: item["generated_sha256"]
                     for item in next7_provenance["modules"]}
    old_module_hashes = {item["name"]: item["generated_sha256"]
                         for item in next5_provenance["modules"]}
    changed_modules = sorted(name for name, digest in module_hashes.items()
                             if old_module_hashes.get(name) != digest)
    if changed_modules != ["S08_m35F5", "root_m0AD9"]:
        raise SystemExit(f"unexpected NEXT7 changed game-body TUs: {changed_modules}")

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
        report["comparison_profile"] = "build/workers/recovered_source_next7/generated"
        report["captured_dos_header_sha256"] = old_header
        profile_fields = sorted(set(new_fields) - set(report["source_globals"]))
        report["comparison_field_scope"] = {
            "captured_original_dos_field_count": len(report["source_globals"]),
            "captured_original_dos_fields": report["source_globals"],
            "next7_state_field_count_including_pointer_descriptors": len(new_fields),
            "compared_fields": "all 370 fields in the preserved DOS capture; their descriptors match the inherited next5 state profile",
            "excluded_fields": profile_fields,
            "excluded_field_reason": "These 41 NEXT7 fields are outside the 370-field DOS capture: 12 balloon cue fields, 22 control-state fields (one is pointer-valued), and 7 additional pre-existing pointer descriptors. No values are asserted for them.",
            "generated_game_body_modules_changed_from_next5": changed_modules,
            "generated_module_hashes": module_hashes,
            "cue_entrypoints": "The four source-compatible cue entrypoints are bound to the actual NEXT7 portable/game/recovered/balloon_adapter.c implementation; no fail-closed cue stub is used.",
        }
        report["next7_actual_balloon_adapter"] = True
        fixture_out = OUTPUT_DIR / filename
        fixture_out.parent.mkdir(parents=True, exist_ok=True)
        fixture_out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        runner_output = io.StringIO()
        with redirect_stdout(runner_output):
            code = runner.run_sequence_mode(report)
        output = execution_output.get("stdout", "")
        result_rows.append({
            "fixture": filename,
            "status": "PASS 256/256 captured-370 subset" if code == 0 else f"FAIL exit={code}",
            "exit_code": code,
            "runner_verification_line": runner_output.getvalue().strip(),
            "comparison_header_sha256": comparison_header,
            "comparison_provenance_sha256": comparison_provenance,
            "descriptor_sha256": sha(fixture_out),
            "source_report_sha256": sha(CAPTURE_DIR / filename),
            "snapshot_sha256": source_report["snapshot_sha256"],
            "native_output_sha256": hashlib.sha256(output.encode("utf-8")).hexdigest(),
            "native_output_line_count": len(output.splitlines()),
            "balloon_call_line": next((line for line in output.splitlines()
                                        if line.startswith("NEXT7_BALLOON_CALLS ")), None),
            "uncaptured_cue_line": next((line for line in output.splitlines()
                                          if line.startswith("NEXT7_UNCAPTURED_CUE_FIELDS ")), None),
            "success_line": next((line for line in output.splitlines()
                                  if line.startswith("SEQUENCE_STATE_RNG_PASS ")), None),
        })
        scratch_inputs = OUTPUT_DIR / "sequence-native"
        generated_inputs = [scratch_inputs / value for value in (
            "fixture_sequence.c", "tick_sequence_runtime.c", "compat.h",
            "fail_closed.c", "native-sequence.exe",
        )]
        result_rows[-1]["generated_compile_inputs"] = {
            path.name: sha(path) for path in generated_inputs if path.is_file()
        }
        result_rows[-1]["object_hashes"] = {
            path.name: sha(path) for path in sorted(scratch_inputs.glob("obj-*.o"))
        }
        tape = OUTPUT_DIR / "tapes" / filename.replace(".json", ".native.txt")
        tape.parent.mkdir(parents=True, exist_ok=True)
        tape.write_text(output, encoding="utf-8")
        result_rows[-1]["native_tape"] = str(tape.relative_to(ROOT)).replace("\\", "/")
        result_rows[-1]["native_tape_sha256"] = sha(tape)
        if code != 0:
            return code

    input_hashes_after = source_closure()
    changed_inputs = {name: {"before": input_hashes_before.get(name),
                             "after": input_hashes_after.get(name)}
                      for name in sorted(set(input_hashes_before) | set(input_hashes_after))
                      if input_hashes_before.get(name) != input_hashes_after.get(name)}
    capture_hashes_after = {}
    for filename in capture_hashes_before:
        report_path = CAPTURE_DIR / filename
        original = json.loads(report_path.read_text(encoding="utf-8"))
        capture_hashes_after[filename] = {
            "descriptor_sha256": sha(report_path),
            "snapshot_sha256": sha(ROOT / original["snapshot_file"]),
        }
    capture_stable = capture_hashes_before == capture_hashes_after
    harness_stable = (sha(RUNNER_PATH) == runner_sha_before and
                      sha(Path(__file__)) == harness_sha_before)
    if changed_inputs or not harness_stable or not capture_stable:
        raise SystemExit(f"replay input changed during run: sources={changed_inputs}; captures_stable={capture_stable}")
    pinned = {
        "schema": "next7-captured370-static-replay-v1",
        "scope": "370 captured DOS fields only; 41 other NEXT7 state fields are explicitly excluded from DOS assertion",
        "source_stability": {
            "source_hashes_pre": input_hashes_before,
            "source_hashes_post": input_hashes_after,
            "source_inputs_stable": not changed_inputs,
            "changed_source_inputs": changed_inputs,
            "preserved_capture_hashes_pre": capture_hashes_before,
            "preserved_capture_hashes_post": capture_hashes_after,
            "preserved_captures_stable": capture_stable,
            "runner_sha256_pre_post": runner_sha_before,
            "producer_sha256_pre_post": harness_sha_before,
            "closure_method": "GCC -MM transitive include closure for the exact runner-compiled generated modules, state/support and native helpers, plus actual balloon adapter/model. Production engine files outside the direct DoAntSim replay graph are excluded.",
        },
        "profile": "build/workers/recovered_source_next7/generated",
        "profile_delta_from_next5": {
            "changed_generated_TUs": changed_modules,
            "changed_entrypoints": ["AddRandAntLion", "InitYelloAnt"],
            "source_change_claim": "The versioned NEXT7 profile changes the RNG expression sequence in these two source-backed functions only; all other 23 generated module hashes match NEXT5.",
            "rng_claim": "The replay compares actual original DOS and native RNG state at all 768 captured boundaries; it does not infer expected C RNG state from an advancement formula.",
        },
        "profile_hashes": {
            "recovered_state.h": comparison_header,
            "recovered_state.c": sha(PROFILE / "recovered_state.c"),
            "recovered_native_adapters.c": sha(PROFILE / "recovered_native_adapters.c"),
            "provenance.json": comparison_provenance,
        },
        "capture_reuse": "Three preserved DOS captures reused; zero fresh original DOS executions.",
        "original_capture_producer_hashes": {
            "portable/research/core-proof/original_256_tick_probe.py": sha(PORT / "research/core-proof/original_256_tick_probe.py"),
            "portable/research/core-proof/original_tick_probe.py": sha(PORT / "research/core-proof/original_tick_probe.py"),
        },
        "capture_and_tape_hashes": {
            "sequence-5a31-0.json": {"descriptor_sha256": "9ef00c230da38e9e7fed3ef27b64ef7fa0c401954b0865437f6d9d6f815612c8", "snapshot_sha256": "7aa0f4c37147cb66c19a3fa820a9d91b7d78d3953cf21cf298991a90967bed21"},
            "sequence-1234-1.json": {"descriptor_sha256": "ea9825d82fa6c7fc5c3120b6094adcc5ca5d7a4012186fac161bc05095d16758", "snapshot_sha256": "d67a3c32c8357c6de8fa4d0be9874e0c7eb87ab27d6e87d4dc17b713c1f67b50"},
            "sequence-5a31-2.json": {"descriptor_sha256": "68e6878e82a10a5ad15e049ba55e7104e009c46838584fe83a10e350cecb6c8e", "snapshot_sha256": "c9de2a6697037534aec4f89c546330a6efe72b0c8a0c942385f91908a36e4452"},
        },
        "clock_boundary": "Preserved static request SimNestRequest{{0,0},2}; TickCount and MacTickCount return captured source tick values. Not live-clock evidence.",
        "ui_boundary": "No UI/full-service equivalence claim; any unresolved game helper remains fail-closed. Actual four balloon cue wrappers are bound to the native adapter.",
        "native_build": {
            "compiler": str(shutil.which("gcc") or "C:/msys64/mingw64/bin/gcc.exe"),
            "compiler_version": subprocess.run([shutil.which("gcc") or "C:/msys64/mingw64/bin/gcc.exe", "--version"], cwd=ROOT, text=True, capture_output=True, check=False, timeout=10).stdout.splitlines()[0],
            "compile_flags": ["-std=c11", "-ffunction-sections", "-fdata-sections", "-include compat.h", "-Wl,--gc-sections"],
            "timeout_seconds": 10,
            "compatibility_exception": "The runner's forced Handle typedef is omitted only for the generated root_m0798_controls.c TU because that source defines its own Handle type; the generated TU is otherwise compiled unchanged.",
        },
        "next7_state_field_count": len(new_fields),
        "next7_uncaptured_fields": sorted(set(new_fields) - set(json.loads((CAPTURE_DIR / "sequence-5a31-0.json").read_text(encoding="utf-8"))["source_globals"])),
        "excluded_field_breakdown": {
            "balloon_cue_fields": 12,
            "additional_control_state_fields": 22,
            "preexisting_pointer_descriptors_not_in_dos_capture": 7,
            "total_excluded_next7_fields": 41,
        },
        "generated_game_body_modules_changed_from_next5": changed_modules,
        "actual_balloon_adapter_objects": [str(path.relative_to(ROOT))
                                            for path in adapter_objects],
        "cases": result_rows,
        "runner_sha256_stable": harness_stable,
    }
    evidence = PORT / "research/core-proof/original-256-tick-summary-next7-captured370-20261002.json"
    evidence.write_text(json.dumps(pinned, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(pinned, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
