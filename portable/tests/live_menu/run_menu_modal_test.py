#!/usr/bin/env python3
"""Build and run the standalone SDL title-menu modal boundary test."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import shlex
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
PORT = ROOT / "portable"
SDK = ROOT / "build/sdl3-sdk/SDL3-3.4.16/x86_64-w64-mingw32"
BUILD = ROOT / "build/portable/tests/live-menu-modal"
REPORT = ROOT / "portable/tests/live_menu/evidence/menu-modal-sdl-test.json"

SOURCES = [
    ROOT / "portable/tests/live_menu/menu_modal_test.c",
    ROOT / "portable/platform/sdl3/menu_modal.c",
    ROOT / "portable/platform/sdl3/host.c",
    ROOT / "portable/ui_model/menus/menu.c",
    ROOT / "portable/ui_model/menus/interaction.c",
    ROOT / "portable/ui_model/menus/dropdown_render.c",
    ROOT / "portable/ui_model/input/input.c",
    ROOT / "portable/game/resources/database.c",
    ROOT / "portable/render/primitives.c",
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    compiler = os.environ.get("SIMANT_CC") or shutil.which("gcc")
    if not compiler:
        raise SystemExit("GCC missing; set SIMANT_CC")
    if not (SDK / "include/SDL3/SDL.h").is_file():
        raise SystemExit(f"SDL3 SDK is missing: {SDK}")
    BUILD.mkdir(parents=True, exist_ok=True)
    output = BUILD / "menu-modal-test.exe"
    command = [compiler, "-std=c11", "-O2", "-Wall", "-Wextra",
               "-Werror", "-I", str(PORT), "-I",
               str(SDK / "include"), *(str(source) for source in SOURCES),
               "-L", str(SDK / "lib"), "-lSDL3", "-o", str(output)]
    dependencies = subprocess.check_output(
        [compiler, "-std=c11", "-I", str(PORT), "-I", str(SDK / "include"),
         "-MM", "-MT", "MENU_DEP", *(str(source.relative_to(ROOT))
                                       for source in SOURCES)],
        cwd=ROOT, text=True).replace("\\\n", " ")
    input_paths = set(SOURCES)
    for block in dependencies.split("MENU_DEP:")[1:]:
        for token in shlex.split(block):
            path = (ROOT / token).resolve()
            if path.is_file():
                input_paths.add(path)
    hashes = {source.relative_to(ROOT).as_posix(): sha(source)
              for source in sorted(input_paths)}
    shared_inputs = [ROOT / "assets/SHARED.DAT", ROOT / "assets/SHARED.NDX"]
    hashes.update({source.relative_to(ROOT).as_posix(): sha(source)
                   for source in shared_inputs})
    linked = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    if linked.returncode:
        raise SystemExit(linked.stdout + linked.stderr)
    changed = [name for name, expected in hashes.items()
               if sha(ROOT / name) != expected]
    if changed:
        raise SystemExit(f"input changed during test build: {changed}")
    shutil.copy2(SDK / "bin/SDL3.dll", BUILD / "SDL3.dll")
    env = dict(os.environ)
    env["SDL_VIDEODRIVER"] = "dummy"
    ran = subprocess.run([str(output), str(ROOT / "assets/SHARED")], cwd=ROOT,
                         env=env, text=True, capture_output=True, timeout=20)
    changed = [name for name, expected in hashes.items()
               if sha(ROOT / name) != expected]
    if changed:
        raise SystemExit(f"inputs changed during modal test: {changed}")
    report = {
        "schema": "portable-sdl-title-menu-modal-test-v1",
        "status": "PASS" if ran.returncode == 0 else "FAIL",
        "scope": "actual SHARED menu with SDL key/pointer events and source-normalized event forwarding; not end-to-end ProcMenu dispatch",
        "command": command,
        "runner_sha256": sha(Path(__file__).resolve()),
        "inputs": hashes,
        "compiler": subprocess.check_output([compiler, "--version"],
                                             text=True).splitlines()[0],
        "compiler_sha256": sha(Path(compiler).resolve()),
        "test_executable_sha256": sha(output),
        "sdl_library_sha256": sha(SDK / "bin/SDL3.dll"),
        "environment": {"SDL_VIDEODRIVER": "dummy"},
        "exit_code": ran.returncode,
        "stdout": ran.stdout,
        "stderr": ran.stderr,
        "assertions": [
            "SHARED kind-6 menu id 0 is loaded and used",
            "physical Shift+= decodes to source '+' and Enter returns source command id",
            "physical left mouse press/release selects actual third row",
            "physical click on another title returns index and exact screen coordinates",
            "source-normalized FE event forwards event code/xE/h/v without SDL invention",
            "scaled 2x SDL window warps to and queries renderer-logical coordinates",
            "modal returns final pointer/button/modifier state and observed key-up clears scan cache",
            "popup rectangle pixels are restored byte-for-byte on each tested exit path"],
        "limits": [
            "physical title event is returned to caller because HostEvent does not include source xE",
            "ProcMenu command dispatch and title activation remain with the caller"]}
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in
                      ("status", "scope", "exit_code", "stdout", "stderr", "limits")},
                     indent=2))
    return ran.returncode


if __name__ == "__main__":
    raise SystemExit(main())
