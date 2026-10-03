#!/usr/bin/env python3
"""Run fresh central S17/S10/menu consumers against a private asset copy.

Every file under assets/ is copied beneath a temporary scratch root. The DOS
file service receives only that copied root, and the process working
directory is a sibling scratch directory so RALLOC.DMP diagnostics cannot
overwrite either the repository asset or its input copy.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[3]
REPORT = ROOT / "portable/tests/menus/evidence/root-consumer-central-tus-v3-final.json"
GENERATED = ROOT / "build/workers/whole_program/generated"
LOCK = ROOT / "layout/oracle.lock.json"

SOURCES = [
    "build/workers/whole_program/generated/root_m1986.c",
    "build/workers/whole_program/generated/root_m19A9.c",
    "build/workers/whole_program/generated/root_m19DC.c",
    "build/workers/whole_program/generated/root_m1A28.c",
    "build/workers/whole_program/generated/root_m1A53.c",
    "build/workers/whole_program/generated/root_m1A96.c",
    "build/workers/whole_program/generated/root_m1B28.c",
    "build/workers/whole_program/generated/root_m1FD2.c",
    "build/workers/whole_program/generated/S17_m384C.c",
    "build/workers/whole_program/generated/S10_m35F5.c",
    "portable/whole_program/state/database.c",
    "portable/whole_program/conversions/pointer_globals.c",
    "portable/whole_program/platform/handles.c",
    "portable/whole_program/platform/dos_io.c",
    "portable/whole_program/platform/dos_format.c",
    "portable/whole_program/platform/dos_memory.c",
    "portable/whole_program/platform/crt_abi.c",
    "portable/platform/memory.c",
    "portable/whole_program/algorithms/lzss.c",
    "portable/whole_program/menu_globals.c",
    "portable/whole_program/platform/graphics_source_clip.c",
    "portable/ui_model/menus/source_record_view.c",
    "portable/tests/menus/test_s17_root_consumer_central_tus_v3.c",
]
PIN_INPUTS = [
    *SOURCES,
    "build/workers/whole_program/generated/dos_types.h",
    "build/workers/whole_program/generated/migration.json",
    "portable/tools/whole_program.py",
    "portable/whole_program/platform/handles.h",
    "portable/whole_program/platform/dos_io.h",
    "portable/whole_program/platform/dos_files.h",
    "portable/whole_program/platform/graphics.h",
    "portable/whole_program/platform/graphics_source_clip.h",
    "portable/whole_program/menu_globals.h",
    "portable/ui_model/menus/source_record_view.h",
    "portable/whole_program/window_source_rects.h",
    "portable/tests/menus/run_s17_root_consumer_central_tus_v3.py",
    "portable/tests/menus/test_s17_root_consumer_central_tus_v2.c",
    "layout/oracle.lock.json",
    "src/S17/m384C.c",
    "src/S10/m35F5.c",
    "src/root/m1A53.c",
    "src/root/m1A96.c",
    "src/root/m171C.c",
    "src/root/m1FD2.c",
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def locked_asset_hashes() -> dict[str, str]:
    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    return {name: item["sha256"] for name, item in lock["inputs"].items()}


def verify_locked_assets(expected: dict[str, str], label: str) -> dict[str, str]:
    observed: dict[str, str] = {}
    changed: list[str] = []
    for name, digest in expected.items():
        path = ROOT / "assets" / name
        if not path.is_file():
            changed.append(name + " (missing)")
            continue
        observed[name] = sha(path)
        if observed[name] != digest:
            changed.append(name)
    if changed:
        raise SystemExit(f"original assets do not match oracle lock ({label}): " +
                         ", ".join(changed))
    return observed


def copy_all_assets(destination: Path, locked: dict[str, str]) -> dict[str, str]:
    source = ROOT / "assets"
    shutil.copytree(source, destination)
    copied_names = sorted(path.name for path in destination.iterdir() if path.is_file())
    expected_names = sorted(path.name for path in source.iterdir() if path.is_file())
    if copied_names != expected_names:
        raise SystemExit("scratch asset copy does not contain every source asset")
    copied = {name: sha(destination / name) for name in copied_names}
    mismatched = [name for name, digest in locked.items()
                  if copied.get(name) != digest]
    if mismatched:
        raise SystemExit("scratch asset copy differs from oracle lock: " +
                         ", ".join(mismatched))
    return copied


def main() -> None:
    if REPORT.exists():
        raise SystemExit(f"refusing to overwrite immutable report {REPORT.relative_to(ROOT)}")
    compiler = os.environ.get("SIMANT_CC") or shutil.which("gcc")
    if not compiler:
        raise SystemExit("GCC missing; set SIMANT_CC")
    expected_assets = locked_asset_hashes()
    assets_before = verify_locked_assets(expected_assets, "before run")
    paths = [ROOT / item for item in PIN_INPUTS]
    missing = [str(path.relative_to(ROOT)) for path in paths if not path.is_file()]
    if missing:
        raise SystemExit("missing pinned input(s): " + ", ".join(missing))
    inputs_before = {path.relative_to(ROOT).as_posix(): sha(path) for path in paths}
    generated_sources = [ROOT / item for item in SOURCES
                         if item.startswith("build/workers/whole_program/generated/")]
    for name, source in (("S17", GENERATED / "S17_m384C.c"),
                         ("S10", GENERATED / "S10_m35F5.c"),
                         ("root menu", GENERATED / "root_m1FD2.c")):
        if not source.is_file():
            raise SystemExit(f"missing current central {name} TU: {source}")
    central_tus = {path.name: sha(path) for path in generated_sources}
    migration_hash = sha(GENERATED / "migration.json")

    with tempfile.TemporaryDirectory(prefix="simant-menu-consumer-v3-") as temp:
        scratch = Path(temp)
        asset_root = scratch / "assets"
        run_cwd = scratch / "run"
        run_cwd.mkdir()
        copied_assets = copy_all_assets(asset_root, expected_assets)
        exe = scratch / "menu-root-consumer-v3.exe"
        source_paths = [ROOT / item for item in SOURCES]
        command = [str(Path(compiler).resolve()), "-std=c11", "-O0", "-fsigned-char",
                   "-fno-builtin-sprintf", "-ffunction-sections", "-fdata-sections",
                   "-Werror=implicit-function-declaration", "-I", str(ROOT),
                   "-I", str(GENERATED), *(str(path) for path in source_paths),
                   "-Wl,--gc-sections", "-o", str(exe)]
        built = subprocess.run(command, cwd=scratch, capture_output=True,
                               text=True, timeout=180)
        if built.returncode:
            verify_locked_assets(expected_assets, "after compile failure")
            raise SystemExit("compile failed:\n" + built.stderr[-18000:])
        run_command = [str(exe), str(asset_root)]
        ran = subprocess.run(run_command, cwd=run_cwd, capture_output=True,
                             text=True, timeout=60)
        assets_after = verify_locked_assets(expected_assets, "after native run")
        if ran.returncode:
            raise SystemExit(f"run failed ({ran.returncode}):\n{ran.stdout}\n{ran.stderr}")
        if sha(asset_root / "RALLOC.DMP") != expected_assets["RALLOC.DMP"]:
            raise SystemExit("scratch asset RALLOC.DMP was unexpectedly modified")
        report = {
            "schema": "simant-menu-root-consumer-central-tus-v3",
            "status": "PASS",
            "classification": "actual fresh central S17/S10/root menu TUs + actual SHARED kind-6 resource from a complete scratch asset copy",
            "claim": "Current central S17 loads SHARED id 0 kind 6, root source consumers operate on the canonical shared typed owner and calculate all five title geometry entries, and current central S10 consumes the same actual item table. The runner copies every asset under assets/ before compilation/run and passes only the scratch copy as the DOS file root.",
            "central_generation": {
                "migration_sha256": migration_hash,
                "generated_tu_sha256": central_tus,
            },
            "resource": {"db": "SHARED", "id": 0, "kind": 6,
                         "payload_size": 514, "menu_count": 5,
                         "table_count": 6},
            "graphics_clip_owner": {
                "provider": "portable/whole_program/platform/graphics_source_clip.c",
                "type": "struct Rect[2]",
                "consumer_view": "graphics_source_clip.h maps g_5A9C to sim_source_screen_clip_list[0]",
                "test_fixture_defines_scalar_g_5A9C": False,
            },
            "asset_safety": {
                "oracle_lock_sha256": sha(LOCK),
                "original_assets_before_sha256": assets_before,
                "original_assets_after_sha256": assets_after,
                "original_assets_unchanged": assets_before == assets_after,
                "complete_scratch_asset_copy_sha256": copied_assets,
                "dos_file_root": "temporary scratch/assets",
                "process_cwd": "temporary scratch/run",
                "scratch_allocator_dump": "temporary scratch/run/ralloc.dmp if emitted by the selected build",
                "canonical_assets/RALLOC.DMP_written": False,
                "scratch_asset_copy/RALLOC.DMP_sha256_after_run": sha(asset_root / "RALLOC.DMP"),
            },
            "inputs_sha256": inputs_before,
            "command": command,
            "run_command": run_command,
            "compiler_version": subprocess.run([compiler, "--version"], check=True,
                capture_output=True, text=True, timeout=15).stdout.splitlines()[0],
            "compiler_stdout": built.stdout,
            "compiler_stderr": built.stderr,
            "executable_sha256": sha(exe),
            "native_stdout": ran.stdout.strip(),
            "native_stderr": ran.stderr,
            "non_claim": "This is bounded current-native source/resource integration, not a DOS differential, full menu-interaction proof, or evidence for resource IDs outside this case.",
        }

    inputs_after = {path.relative_to(ROOT).as_posix(): sha(path) for path in paths}
    if inputs_after != inputs_before:
        raise SystemExit("pinned code/source input changed while runner executed")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "report": REPORT.relative_to(ROOT).as_posix(),
                      "sha256": sha(REPORT), "stdout": report["native_stdout"],
                      "assets_unchanged": report["asset_safety"]["original_assets_unchanged"]},
                     indent=2))


if __name__ == "__main__":
    main()
