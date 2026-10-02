#!/usr/bin/env python3
"""Exercise S11 ProcMenu through the resource-backed NEXT7 engine boundary."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[3]
PORT = ROOT / "portable"
PROFILE = ROOT / "build/workers/recovered_source_next7/generated"
HARNESS = PORT / "tests/menus/engine_procmenu.c"
EVIDENCE = PORT / "tests/menus/evidence/engine-procmenu-next7-complete-closure-20261002.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def digest_paths(paths: list[Path]) -> tuple[str, dict[str, str]]:
    hashes = {path.relative_to(ROOT).as_posix(): sha(path)
              for path in sorted(set(paths), key=lambda p: p.as_posix())}
    digest = hashlib.sha256()
    for name, value in hashes.items():
        digest.update(name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(bytes.fromhex(value))
    return digest.hexdigest(), hashes


def binary_metadata(path: Path) -> dict[str, object]:
    data = path.read_bytes()
    if data[:2] != b"MZ" or len(data) < 0x40:
        raise RuntimeError("engine integration output is not a PE executable")
    pe_offset = int.from_bytes(data[0x3c:0x40], "little")
    if data[pe_offset:pe_offset + 4] != b"PE\0\0":
        raise RuntimeError("engine integration output has no PE signature")
    machine = int.from_bytes(data[pe_offset + 4:pe_offset + 6], "little")
    section_count = int.from_bytes(data[pe_offset + 6:pe_offset + 8], "little")
    optional_magic = int.from_bytes(data[pe_offset + 24:pe_offset + 26], "little")
    return {"path": path.relative_to(ROOT).as_posix(), "sha256": sha(path),
            "size_bytes": len(data), "pe_machine": f"0x{machine:04x}",
            "pe_sections": section_count,
            "optional_header_magic": f"0x{optional_magic:04x}"}


def native_sources() -> list[Path]:
    native = [*PORT.joinpath("game").glob("*.c"),
              PORT / "platform/memory.c"]
    for folder in ("game/simulation", "game/state", "game/resources",
                   "game/render", "render", "ui_model", "audio"):
        native.extend(path for path in PORT.joinpath(folder).rglob("*.c")
                      if path.name not in {"control_events.c", "history_render.c"})
    native.extend(PORT / "game/recovered" / name for name in (
        "engine.c", "session_bridge.c", "audio_adapter.c",
        "memory_adapter.c", "nest_adapter.c", "menu_adapter.c"))
    return sorted(set(path.resolve() for path in native))


def generated_objects() -> list[Path]:
    return sorted(path.resolve() for path in PROFILE.glob("*.o")
                   if path.name not in {"root_m0798_controls.o",
                                        "root_m384C_newgame.o"})


def compiler_dependencies(compiler: str, sources: list[Path]) -> list[Path]:
    found: set[Path] = set()
    for source in sources:
        result = subprocess.run([
            compiler, "-std=c11", "-MM", "-I", str(ROOT), "-I", str(PORT),
            "-I", str(PROFILE), str(source),
        ], cwd=ROOT, text=True, capture_output=True, check=True, timeout=20)
        dependency_text = result.stdout.split(":", 1)[1]
        dependency_text = dependency_text.replace("\\\r\n", " ").replace("\\\n", " ")
        for token in dependency_text.split():
            path = Path(token)
            if not path.is_absolute(): path = ROOT / path
            found.add(path.resolve())
        found.add(source.resolve())
    return sorted(found)


def source_inputs(compiler: str, compiled_sources: list[Path],
                  objects: list[Path]) -> tuple[list[Path], list[Path]]:
    generated_sources = [PROFILE / f"{path.stem}.c" for path in objects
                         if (PROFILE / f"{path.stem}.c").is_file()]
    c_sources = sorted(set([*compiled_sources, HARNESS.resolve(),
                            *(path.resolve() for path in generated_sources)]))
    dependencies = compiler_dependencies(compiler, c_sources)
    provenance = json.loads((PROFILE / "provenance.json").read_text(encoding="utf-8"))
    linked_names = {path.stem for path in generated_sources}
    original_sources = [ROOT / module["source"] for module in provenance["modules"]
                        if Path(module["generated"]).stem in linked_names]
    assets = [path for stem in ("HCEGANT", "SHARED")
              for path in ROOT.glob(f"assets/{stem}.*") if path.is_file()]
    profile_pins = [*objects, PROFILE / "recovered_state.h",
                     PROFILE / "provenance.json", *generated_sources,
                     *original_sources]
    exact_inputs = sorted(set([*dependencies, *profile_pins, *assets,
                               Path(__file__).resolve()]))
    return exact_inputs, c_sources


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, default=EVIDENCE,
                        help="distinct receipt path; existing receipts are preserved")
    args = parser.parse_args()
    evidence_path = args.report.resolve()
    if not evidence_path.is_relative_to(ROOT):
        raise SystemExit("receipt must stay within the workspace")
    if evidence_path.exists():
        raise SystemExit(f"refusing to overwrite receipt: {evidence_path}")
    compiler = os.environ.get("SIMANT_CC") or shutil.which("gcc")
    if not compiler:
        fallback = Path("C:/msys64/mingw64/bin/gcc.exe")
        if not fallback.is_file():
            raise SystemExit("Native C compiler not found; set SIMANT_CC")
        compiler = str(fallback)
    provenance = PROFILE / "provenance.json"
    if not provenance.is_file() or not HARNESS.is_file():
        raise SystemExit("NEXT7 profile or ProcMenu engine harness is missing")
    compiled_sources = native_sources()
    # The integration engine intentionally supplies fail-closed NewGame and
    # initControls boundaries. Those unrelated whole-TU objects redefine them
    # and are not in ProcMenu's call closure for the exercised command set.
    objects = generated_objects()
    if not objects:
        raise SystemExit("NEXT7 generated object files are missing")
    inputs, c_sources = source_inputs(compiler, compiled_sources, objects)
    before, hashes_before = digest_paths(inputs)
    scratch = ROOT / "build/workers/procmenu_engine_next7"
    scratch.mkdir(parents=True, exist_ok=True)
    executable = scratch / "engine-procmenu-next7.exe"
    suppressions = [
        "-Wno-missing-braces", "-Wno-unused-parameter", "-Wno-unused-variable",
        "-Wno-unused-but-set-variable", "-Wno-unused-but-set-parameter",
        "-Wno-parentheses", "-Wno-type-limits", "-Wno-implicit-fallthrough",
        "-Wno-tautological-compare", "-Wno-char-subscripts", "-Wno-sign-compare",
        "-Wno-builtin-declaration-mismatch",
    ]
    command = [compiler, "-std=c11", "-O0", "-Wall", "-Wextra", "-Werror",
               *suppressions, "-I", str(ROOT), "-I", str(PORT), "-I", str(PROFILE),
               str(HARNESS), *(str(p) for p in compiled_sources),
               *(str(p) for p in objects), "-o", str(executable)]
    try:
        built = subprocess.run(command, cwd=ROOT, text=True, capture_output=True,
                               timeout=180, check=False)
    except subprocess.TimeoutExpired as error:
        raise SystemExit(f"engine ProcMenu build timed out: {error}")
    if built.returncode:
        print(built.stdout + built.stderr, end="")
        raise SystemExit(built.returncode)
    try:
        ran = subprocess.run([str(executable)], cwd=ROOT, text=True,
                             capture_output=True, timeout=45, check=False)
    except subprocess.TimeoutExpired as error:
        raise SystemExit(f"engine ProcMenu executable timed out: {error}")
    print(ran.stdout, end="")
    print(ran.stderr, end="")
    after, hashes_after = digest_paths(inputs)
    if before != after or hashes_before != hashes_after:
        raise SystemExit("source/profile inputs changed while the integration test ran")
    if ran.returncode:
        raise SystemExit(ran.returncode)
    compiler_version = subprocess.run([compiler, "--version"], cwd=ROOT,
        text=True, capture_output=True, check=True, timeout=10).stdout.splitlines()[0]

    records = []
    for line in ran.stdout.splitlines():
        pieces = line.split("|")
        if pieces[0] == "CASE":
            records.append({"name": pieces[1], "status_code": int(pieces[2]),
                "completed_ticks_before": int(pieces[3]),
                "completed_ticks_after": int(pieces[4]),
                "rng_unchanged": pieces[5] == "1",
                "host_effect_count": int(pieces[6]),
                "recovered_binding_clean_after_return": pieces[7] == "1",
                "reentrant_status_code": int(pieces[8]), "effects": []})
        elif pieces[0] == "EFFECT":
            row = next(item for item in reversed(records) if item["name"] == pieces[1])
            row["effects"].append({"kind": int(pieces[2]),
                "arguments": [int(value) for value in pieces[3:8]]})
    gap_lines = [line for line in ran.stdout.splitlines() if line.startswith("GAP|")]
    guard_lines = [line for line in ran.stdout.splitlines()
                   if line.startswith("GUARD|")]
    summary_lines = [line for line in ran.stdout.splitlines()
                     if line.startswith("SUMMARY|")]
    expected_names = {
        *(f"speed-{value:02x}" for value in range(0x43, 0x47)),
        *(f"pending-{value:02x}" for value in (4, 5, 6, 8)),
        "unknown-77", "pause-tool--1", "pause-tool-10", "pause-tool-11",
        "unpause-tool-10", "unpause-tool-11", "unpause-idle",
        "option-31", "option-33", "option-34", "option-35", "option-36",
        "option-32",
    }
    if {row["name"] for row in records} != expected_names or len(records) != 21:
        raise SystemExit("engine harness did not report the expected command matrix")
    for row in records:
        expected_status = 5 if row["name"] == "option-32" else 0
        expected_effects = (30 if row["name"].startswith("unpause-tool-") else
            15 if row["name"].startswith("pause-tool-") or row["name"] == "unpause-idle" else
            11 if row["name"].startswith("speed-") or
                 row["name"].startswith("option-") and row["name"] != "option-32" else 0)
        expected_reentrant = 1 if row["name"] == "speed-43" else 0
        if (row["status_code"] != expected_status or
                row["completed_ticks_before"] != 1 or
                row["completed_ticks_after"] != 1 or
                not row["rng_unchanged"] or
                not row["recovered_binding_clean_after_return"] or
                row["host_effect_count"] != expected_effects or
                row["reentrant_status_code"] != expected_reentrant):
            raise SystemExit(f"engine invariant failed in case {row['name']}: {row}")
    if (not guard_lines or not any(line == "GUARD|faulted-followup|8"
                                   for line in guard_lines) or
            not any(line == "GAP|option-32|StopSong|source stops song before toggling sound option"
                    for line in gap_lines) or
            not summary_lines or not summary_lines[-1].startswith("SUMMARY|PASS|completed_ticks=1|")):
        raise SystemExit("engine harness omitted required guard/gap/baseline receipts")
    output = {
        "schema": "resource-backed-engine-procmenu-integration-v1",
        "status": "PASS",
        "profile": "NEXT7 generated recovered source",
        "claim": "A resource-backed SimSession initialized from shipped game assets reaches one actual DoAntSim tick, then exercises the public engine ProcMenu command bridge with active recovered-state/RNG/audio/nest scopes.",
        "scope": "Speed commands FD43..FD46; pause FD41 with idle/life-transfer/target tool states; option toggles FD31 and FD33..FD36; pending words FD04/05/06/08; unknown FD77 no-op; invalid, reentrant, and terminal fault guards.",
        "expected_source_gap": "FD32 reaches the actual source StopSong call before its option-state toggle. The engine correctly fails closed with UNSUPPORTED_CALL and failed_service StopSong; the toggle is therefore not committed.",
        "baseline_tick": "One actual generated DoAntSim tick with deterministic nest TickCount samples [1000,1001]; all subsequent menu actions leave completed_ticks unchanged.",
        "host_boundary": "Typed UI effects are synchronously recorded and acknowledged; all windows are explicitly reported closed, DOS keyboard flags are zero, audio driver is disabled, and no SDL rendering or modal UI flow is claimed.",
        "cases": records,
        "gap": gap_lines,
        "guards": guard_lines,
        "summary": summary_lines,
        "effect_kind_codes": {"2": "EDIT_MESSAGE", "7": "WINDOW_OPERATION"},
        "window_operation_codes": {"1": "CLIP_OFF", "4": "CLIP_SET",
            "18": "SET_SELECTED_STATE", "35": "SET_MENU_ITEM_STATE",
            "36": "SET_MENU_ITEM_TEXT"},
        "linked_profile_scope": {
            "whole_generated_profile_object_count": len(list(PROFILE.glob("*.o"))),
            "linked_generated_object_count": len(objects),
            "excluded_generated_objects": ["root_m0798_controls.o", "root_m384C_newgame.o"],
            "reason": "Their unrelated initControls/NewGame definitions conflict with the engine's deliberate fail-closed fallbacks and those entry points are not reached by this command matrix.",
        },
        "compiler": compiler,
        "compiler_version": compiler_version,
        "compiler_dependency_method": "GCC -MM non-system transitive dependencies for each directly compiled native/recovered/harness TU and each linked generated profile TU; exact generated source/object pair and provenance, original source anchors, and HCEGANT/SHARED asset files are hash-pinned.",
        "compiled_translation_units": [path.relative_to(ROOT).as_posix()
                                       for path in c_sources],
        "inputs": hashes_after,
        "input_hash_sha256": after,
        "inputs_stable_before_after": True,
        "generated_profile_provenance_sha256": sha(provenance),
        "runner_sha256": sha(Path(__file__)),
        "harness_sha256": sha(HARNESS),
        "executable": binary_metadata(executable),
    }
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8", newline="")
    print(json.dumps({"status": output["status"], "cases": len(records),
        "expected_gaps": len(gap_lines), "evidence": evidence_path.relative_to(ROOT).as_posix()},
        indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
