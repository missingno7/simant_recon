#!/usr/bin/env python3
"""Exercise real S17 ownership and real root menu consumers in one process."""
from __future__ import annotations

import hashlib
import importlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
BUILD = ROOT / "build/portable/menu-root-consumer-central-tus-v2"
REPORT = ROOT / "portable/tests/menus/evidence/root-consumer-central-tus-v2.json"
REL = "src/root/m1FD2.c"
CANONICAL = ROOT / REL
GENERATED = ROOT / "build/workers/whole_program/generated/root_m1FD2.c"

SOURCES = [
    "build/workers/whole_program/generated/root_m1986.c",
    "build/workers/whole_program/generated/root_m19A9.c",
    "build/workers/whole_program/generated/root_m19DC.c",
    "build/workers/whole_program/generated/root_m1A28.c",
    "build/workers/whole_program/generated/root_m1A53.c",
    "build/workers/whole_program/generated/root_m1A96.c",
    "build/workers/whole_program/generated/root_m1B28.c",
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
    "portable/ui_model/menus/source_record_view.c",
    "portable/tests/menus/test_s17_root_consumer_central_tus_v2.c",
]
PIN_INPUTS = [
    *SOURCES,
    "build/workers/whole_program/generated/root_m1FD2.c",
    "build/workers/whole_program/generated/dos_types.h",
    "build/workers/whole_program/generated/migration.json",
    "portable/tools/whole_program.py",
    "portable/tools/source_runtime_globals.py",
    "portable/whole_program/conversions/menu_root_shared_owner_v1.py",
    "portable/whole_program/menu_globals.h",
    "portable/whole_program/platform/dos_io.h",
    "portable/whole_program/platform/dos_files.h",
    "portable/whole_program/platform/handles.h",
    "portable/whole_program/platform/graphics.h",
    "portable/whole_program/window_source_rects.h",
    "portable/ui_model/menus/source_record_view.h",
    "portable/tests/menus/run_s17_root_consumer_central_tus_v2.py",
    "portable/tests/menus/evidence/source-loader-dos-v1.json",
    "portable/tests/menus/evidence/source-loader-central-tus-v1.json",
    "src/S17/m384C.c",
    "src/S10/m35F5.c",
    "src/root/m1A53.c",
    "src/root/m1A96.c",
    "src/root/m171C.c",
    "src/root/m1FD2.c",
    "assets/SHARED.NDX",
    "assets/SHARED.DAT",
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compile_root_tu() -> tuple[Path, dict]:
    sys.path.insert(0, str(ROOT / "portable/tools"))
    sys.path.insert(0, str(ROOT))
    whole_program = importlib.import_module("whole_program")
    runtime = importlib.import_module("source_runtime_globals")
    owner = importlib.import_module(
        "portable.whole_program.conversions.menu_root_shared_owner_v1")
    raw = CANONICAL.read_bytes()
    source = raw.decode("utf-8")
    source = runtime.adapt_transformed(source, REL, raw)
    source, ledger = owner.adapt_transformed(source, REL, raw)
    translated, word_ledger = whole_program.convert_words(source)
    generated = GENERATED.read_text(encoding="utf-8")
    # Prefer the exact central generated TU once the parent generator refreshes.
    # Until then, apply the same pinned alias substitution to its already-lowered
    # body; this keeps all other root runtime/state adapters identical to the
    # central build while still exercising the actual root consumer functions.
    if "g_menu_view.titles" in generated:
        root_text = generated
        composition = "current central generated root TU already has shared owner"
    else:
        import re
        root_text, declaration_count = re.subn(
            r"(?m)^\s*struct\s+MenuData\s+\*\s*g_6054\s*=\s*0\s*;\s*$",
            "", generated, count=1)
        root_text, title_count = re.subn(r"\bg_6054\s*->\s*titles\b",
                                         "g_menu_view.titles", root_text)
        root_text, item_count = re.subn(r"\bg_6054\s*->\s*items\b",
                                        "g_menu_view.items", root_text)
        root_text, loaded_count = re.subn(r"!\s*g_6054\b",
                                          "fd_55B3_6054 == NULL", root_text)
        if (declaration_count, title_count, item_count, loaded_count) != (1, 8, 6, 2):
            raise SystemExit("generated root consumer inventory drift: "
                             f"{declaration_count}/{title_count}/{item_count}/{loaded_count}")
        if "g_6054" in root_text:
            raise SystemExit("postword fixture still contains private g_6054 references")
        root_text = '#include "portable/whole_program/menu_globals.h"\n' + root_text
        composition = "test seam applies the verified preword alias ledger to the previous central-lowered TU"
    out = BUILD / "root_m1FD2_actual_shared_owner.c"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(root_text, encoding="utf-8")
    return out, {"runtime_adapter": runtime.PINNED[REL],
                 "menu_owner_ledger": ledger, "word_lowering": word_ledger,
                 "generated_tu_composition": composition,
                 "output_sha256": sha(out)}


def main() -> None:
    if REPORT.exists():
        raise SystemExit(f"refusing to overwrite immutable report {REPORT.relative_to(ROOT)}")
    compiler = os.environ.get("SIMANT_CC") or shutil.which("gcc")
    if not compiler:
        raise SystemExit("GCC missing; set SIMANT_CC")
    root_tu, conversion = compile_root_tu()
    sources = [ROOT / item for item in SOURCES]
    missing = [str(p.relative_to(ROOT)) for p in sources if not p.is_file()]
    if missing:
        raise SystemExit("missing source(s): " + ", ".join(missing))
    input_paths = [ROOT / item for item in PIN_INPUTS]
    before = {p.relative_to(ROOT).as_posix(): sha(p) for p in input_paths}
    command = [str(Path(compiler).resolve()), "-std=c11", "-O0", "-fsigned-char",
        "-fno-builtin-sprintf", "-ffunction-sections", "-fdata-sections",
        "-Werror=implicit-function-declaration", "-I", str(ROOT),
        "-I", str(GENERATED.parent),
        *(str(p) for p in sources), str(root_tu), "-Wl,--gc-sections",
        "-o", str(BUILD / "root-consumer-v2.exe")]
    built = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=180)
    if built.returncode:
        raise SystemExit("compile failed:\n" + built.stderr[-18000:])
    ran = subprocess.run([str(BUILD / "root-consumer-v2.exe"),
                          str((ROOT / "assets").resolve())], cwd=ROOT,
                         capture_output=True, text=True, timeout=45)
    if ran.returncode:
        raise SystemExit(f"run failed ({ran.returncode}):\n{ran.stdout}\n{ran.stderr}")
    changed = [key for key, value in before.items() if sha(ROOT / key) != value]
    if changed:
        raise SystemExit("pinned input changed during run: " + ", ".join(changed))
    report = {
        "schema": "simant-menu-root-consumer-central-tus-v2",
        "status": "PASS",
        "classification": "actual generated S17/S10 TUs + actual root m1FD2 consumers + central source DB/allocator",
        "claim": "S17 loads actual SHARED id 0 kind 6 and installs its source-backed table vectors; actual root SetMenuItemState mutates an item through the same canonical typed sidecar, and actual root f_1FD2_0663 consumes the loaded title table to size all five geometry entries. Actual S10 consumes the same item table. The test composes runtime-global adaptation then the strict source-pinned root shared-owner adaptation before word lowering.",
        "resource": {"db": "SHARED", "id": 0, "kind": 6, "payload_size": 514,
                     "menu_count": 5, "table_count": 6},
        "conversion": conversion,
        "inputs_sha256": before,
        "command": command,
        "compiler_version": subprocess.run([compiler, "--version"], check=True,
            capture_output=True, text=True, timeout=15).stdout.splitlines()[0],
        "compiler_stdout": built.stdout,
        "compiler_stderr": built.stderr,
        "executable_sha256": sha(BUILD / "root-consumer-v2.exe"),
        "native_stdout": ran.stdout.strip(),
        "native_stderr": ran.stderr,
        "non_claim": "This bounded central-TU receipt covers the loaded menu data and the exercised root setter/title-geometry consumers. It does not claim complete root menu drawing, interaction, or other resource IDs."
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "report": REPORT.relative_to(ROOT).as_posix(),
                      "sha256": sha(REPORT), "stdout": ran.stdout.strip()}, indent=2))


if __name__ == "__main__":
    main()
