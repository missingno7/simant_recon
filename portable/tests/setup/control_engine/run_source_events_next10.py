#!/usr/bin/env python3
"""Test the source-converted event route through the actual Next10 engine."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[4]
PORT = ROOT / "portable"
HERE = Path(__file__).resolve().parent
PROFILE = ROOT / "build/workers/recovered_source_next10/generated"
OUTPUT_DIR = ROOT / "build/workers/control_engine_source_probe"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compiler() -> str:
    configured = os.environ.get("SIMANT_CC")
    result = configured or shutil.which("gcc")
    if result:
        return result
    fallback = Path("C:/msys64/mingw64/bin/gcc.exe")
    if fallback.exists():
        return str(fallback)
    raise SystemExit("Native C compiler missing; set SIMANT_CC")


def inputs() -> list[Path]:
    paths = [HERE / "test_control_engine.c", *PORT.glob("game/*.c"),
             PORT / "platform/memory.c"]
    for folder in ("game/simulation", "game/state", "game/resources", "game/render",
                   "render", "ui_model", "audio"):
        paths.extend(p for p in (PORT / folder).rglob("*.c")
                     if p.name not in ("interaction.c", "dac_mixer.c",
                                       "history_render.c", "decorations.c", "control_preselect.c") and
                     "control_render" not in p.parts)
    paths = [p for p in paths if "ui_model/menus" not in p.as_posix() and
             "ui_model/dialogs" not in p.as_posix()]
    paths.extend(PORT / "game/recovered" / name for name in (
        "engine.c", "session_bridge.c", "audio_adapter.c", "balloon_adapter.c",
        "memory_adapter.c", "nest_adapter.c", "menu_adapter.c", "control_adapter.c"))
    paths.extend(p for p in PROFILE.glob("*.o") if p.is_file() and
                 p.stem != "root_m384C_newgame")
    return sorted({p.resolve() for p in paths if p.is_file()})


def local_dependencies(cc: str, flags: list[str], include: list[str],
                       paths: list[Path]) -> list[Path]:
    sources = [str(p) for p in paths if p.suffix == ".c"]
    raw = subprocess.check_output([cc, *flags, *include, "-MM", *sources],
                                  cwd=ROOT, text=True).replace("\\\n", " ")
    found: set[Path] = set()
    for line in raw.splitlines():
        if ":" not in line:
            continue
        rhs = line.split(":", 1)[1]
        for token in rhs.split():
            path = Path(token)
            if not path.is_absolute():
                path = ROOT / path
            try:
                path = path.resolve()
                if path.is_file() and path.is_relative_to(ROOT):
                    found.add(path)
            except OSError:
                continue
    return sorted(found)


def main() -> int:
    cc = compiler()
    provenance = json.loads((PROFILE / "provenance.json").read_text())
    state = provenance["recovered_state"]
    if state.get("binding_status") != "COMPLETE" or state.get("source_data_initializer_mismatches"):
        raise SystemExit("Next9 profile state binding or source initializers are incomplete")
    if sha(PROFILE / "recovered_state.h") != state["header_sha256"] or \
       sha(PROFILE / "recovered_state.c") != state["source_sha256"]:
        raise SystemExit("Next9 generated state identity mismatch")
    from portable.tools.profile_next10 import validate_next10
    validate_next10(provenance)
    from portable.tools.convert_control_events import verify
    verify()
    paths = inputs()
    include = ["-I", str(ROOT), "-I", str(PORT), "-I", str(PROFILE),
               "-I", str(PORT / "game/recovered")]
    flags = ["-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
             "-D__USE_MINGW_SETJMP_NON_SEH",
             "-DSIMANT_ENABLE_CONTROL_INIT_NEXT4",
             "-DSIMANT_ENABLE_BALLOON_STATE_NEXT3"]
    dependencies = local_dependencies(cc, flags, include, paths)
    input_paths = sorted(set(paths + dependencies + [
        Path(__file__).resolve(), PROFILE / "provenance.json",
        PROFILE / "recovered_state.h", PROFILE / "recovered_state.c",
        ROOT / "portable/tools/profile_next10.py",
        ROOT / "portable/tools/recover_source_next10.py",
        ROOT / "portable/tools/convert_control_events.py",
        ROOT / "portable/tools/word_spelling.py",
        ROOT / "portable/tools/recover_source.py",
        ROOT / "portable/game/recovered/source/control_events.json",
        ROOT / "src/root/m0798.c",
        ROOT / "portable/tests/setup/control_events/evidence/paired-control-events.json",
        ROOT / "assets/SIMANT.EXE", ROOT / "assets/HCEGANT.NDX",
        ROOT / "assets/HCEGANT.DAT", ROOT / "assets/SHARED.NDX",
        ROOT / "assets/SHARED.DAT"]))
    before = {str(p.relative_to(ROOT)): sha(p) for p in input_paths if p.is_file()}
    compiler_path = Path(cc).resolve()
    compiler_sha_before = sha(compiler_path)
    output = OUTPUT_DIR / f"control-engine-probe-{os.getpid()}.exe"
    command = [cc, *flags, *include, *(str(p) for p in paths), "-o", str(output)]
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    compile_result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    if compile_result.returncode:
        print(compile_result.stdout, end="")
        print(compile_result.stderr, end="", file=sys.stderr)
        return compile_result.returncode
    executable_sha_before = sha(output)
    run = subprocess.run([str(output)], cwd=ROOT, text=True, capture_output=True)
    print(run.stdout, end="")
    print(run.stderr, end="", file=sys.stderr)
    after = {str(p.relative_to(ROOT)): sha(p) for p in input_paths if p.is_file()}
    compiler_sha_after = sha(compiler_path)
    executable_sha_after = sha(output)
    if before != after:
        raise SystemExit("A pinned control-engine input changed during compilation/execution")
    if compiler_sha_before != compiler_sha_after:
        raise SystemExit("Compiler binary changed during the probe run")
    if executable_sha_before != executable_sha_after:
        raise SystemExit("Built probe executable changed during execution")
    if run.returncode == 0:
        compiler_version = subprocess.check_output([cc, "--version"], text=True).splitlines()[0]
        report = {
            "schema": "simant-control-engine-source-next10-v1",
            "status": "PASS",
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "profile": "recovered_source_next10",
            "profile_state": {"header_sha256": state["header_sha256"],
                              "source_sha256": state["source_sha256"]},
            "scope": "Resource-backed HCEGANT NewGame, one actual DoAntSim tick, ten successful engine-bound setup-control events, actual source RandYard selector/percent lifetime, and invalid/reentrant/fault cleanup checks. This is an engine-boundary probe; the model-to-DOS paired event contract remains in ../control_events/evidence/paired-control-events.json.",
            "counts": {"engine_boundary_cases": 15,
                       "actual_do_antsim_ticks": 1,
                       "successful_engine_control_events": 10,
                       "invalid_direct_dispatch_cases": 3,
                       "nested_reentry_rejections": 10,
                       "both_windows_preset_auto_percent": True,
                       "both_windows_outside_and_repeated_drag": True,
                       "actual_randyard_lifetime_call": 1,
                       "provider_fault_recovery_engine": 1},
            "checks": {"all_non_control_recovered_state_bytes_unchanged_per_event": True,
                       "selected_source_state_matches_session_after_event": True,
                       "callback_snapshots_see_published_state": True,
                       "shared_triangle_geometry_read_only_per_event": True,
                       "event_rng_and_completed_tick_unchanged": True,
                       "host_query": "one DOS_KEYBOARD_FLAGS query, argc=0, controlled BIOS byte=0 per public event",
                       "session_selectors_and_caller_percent_words_survive_RandYard": True,
                       "invalid_kind_internal_action_and_unknown_action_rejected": True,
                       "nested_reentry_rejected": True,
                       "provider_failure_unbinds_and_fresh_engine_succeeds": True},
            "compile": {"compiler": cc, "version": compiler_version,
                        "compiler_binary_sha256": compiler_sha_before,
                        "command": command, "input_sha256_before": before,
                        "input_sha256_after": after,
                        "built_executable_sha256_before_run": executable_sha_before,
                        "built_executable_sha256_after_run": executable_sha_after,
                        "local_transitive_dependency_count": len(dependencies),
                        "local_transitive_dependencies": [str(p.relative_to(ROOT))
                                                           for p in dependencies]},
            "run": {"return_code": run.returncode, "stdout": run.stdout,
                    "stderr": run.stderr},
        }
        evidence = HERE / "evidence"
        evidence.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        report_path = evidence / f"control-engine-source-next10-{stamp}.json"
        suffix = 1
        while report_path.exists():
            report_path = evidence / f"control-engine-source-next10-{stamp}-{suffix}.json"
            suffix += 1
        encoded = json.dumps(report, indent=2, sort_keys=True) + "\n"
        report_path.write_text(encoded, encoding="utf-8")
        (report_path.with_suffix(".json.sha256")).write_text(
            hashlib.sha256(report_path.read_bytes()).hexdigest() + "  " +
            report_path.name + "\n", encoding="ascii")
        print(f"Immutable probe receipt: {report_path.relative_to(ROOT)}")
    elif run.returncode:
        print(f"Probe executable retained for failure diagnostics: {output.relative_to(ROOT)}",
              file=sys.stderr)
    return run.returncode


if __name__ == "__main__":
    raise SystemExit(main())
