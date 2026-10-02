#!/usr/bin/env python3
"""Project-local MinGW/SDL3 build. Historical inputs are read-only."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import shlex
import subprocess
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
VERSION = "3.4.16"
SDK_SHA = "9828bb735cf8a007bcf0ac5aa9f01f3fcb54b7ca67c932e775c905c5d5053a60"
SDK_URL = f"https://github.com/libsdl-org/SDL/releases/download/release-{VERSION}/SDL3-devel-{VERSION}-mingw.zip"


def sdk_path() -> Path:
    return ROOT / "build" / "sdl3-sdk" / f"SDL3-{VERSION}" / "x86_64-w64-mingw32"


def install_sdk() -> None:
    archive = ROOT / "build" / "sdl3-sdk" / f"SDL3-devel-{VERSION}-mingw.zip"
    archive.parent.mkdir(parents=True, exist_ok=True)
    if not archive.exists():
        urllib.request.urlretrieve(SDK_URL, archive)
    actual = hashlib.sha256(archive.read_bytes()).hexdigest()
    if actual != SDK_SHA:
        raise SystemExit(f"SDL3 SDK checksum mismatch: {actual}")
    with zipfile.ZipFile(archive) as z:
        for entry in z.infolist():
            target = (archive.parent / entry.filename).resolve()
            if not target.is_relative_to(archive.parent.resolve()):
                raise SystemExit("Unsafe SDK archive entry")
        z.extractall(archive.parent)
    print(f"Verified SDL3 {VERSION}: {actual}")


def build(main: Path, output: Path, sources: list[Path]) -> None:
    sdk = sdk_path()
    if not (sdk / "include" / "SDL3" / "SDL.h").exists():
        raise SystemExit("SDL3 SDK missing; run python portable/build.py --setup-sdk")
    compiler = os.environ.get("SIMANT_CC") or shutil.which("gcc")
    if not compiler:
        candidate = Path("C:/msys64/mingw64/bin/gcc.exe")
        compiler = str(candidate) if candidate.exists() else None
    if not compiler:
        raise SystemExit("MinGW-w64 GCC required; set SIMANT_CC")
    output.parent.mkdir(parents=True, exist_ok=True)
    command = [compiler, "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
               "-I", str(ROOT / "portable"), "-I", str(sdk / "include"),
               str(main), *(str(p) for p in sources),
               "-L", str(sdk / "lib"), "-lSDL3", "-o", str(output)]
    dependencies = subprocess.check_output(
        [compiler, "-std=c11", "-I", "portable", "-I", str(sdk / "include"),
         "-MM", "-MT", "SIMANT_DEP",
         *(p.relative_to(ROOT).as_posix() for p in [main, *sources])],
        text=True, cwd=ROOT)
    dependencies = dependencies.replace("\\\n", " ")
    inputs = {main, *sources, Path(__file__).resolve()}
    for block in dependencies.split("SIMANT_DEP:")[1:]:
        for token in shlex.split(block):
            dependency = (ROOT / token).resolve()
            if dependency.is_relative_to(ROOT / "portable"):
                inputs.add(dependency)
    input_hashes = {p.relative_to(ROOT).as_posix(): hashlib.sha256(
        p.read_bytes()).hexdigest() for p in sorted(inputs)}
    subprocess.run(command, check=True, cwd=ROOT)
    changed = [name for name,expected in input_hashes.items()
               if hashlib.sha256((ROOT / name).read_bytes()).hexdigest()!=expected]
    if changed:
        raise SystemExit(f"Sources changed during compilation; rebuild required: {changed}")
    shutil.copy2(sdk / "bin" / "SDL3.dll", output.parent / "SDL3.dll")
    receipt = {"sdl_version": VERSION, "sdl_sdk_sha256": SDK_SHA,
               "sdl_sdk_url": SDK_URL, "compiler": subprocess.check_output(
                   [compiler, "--version"], text=True).splitlines()[0],
               "oracle": subprocess.check_output(["git", "-c",
                   f"safe.directory={ROOT.as_posix()}", "rev-parse",
                   "dos-semantic-oracle-v1^{commit}"], text=True, cwd=ROOT).strip(),
               "command": command,
               "inputs": input_hashes,
               "sources_stable_during_build": True,
               "compiler_sha256":hashlib.sha256(Path(compiler).read_bytes()).hexdigest(),
               "sdl_library_sha256": hashlib.sha256((sdk / "bin/SDL3.dll").read_bytes()).hexdigest(),
               "executable_sha256": hashlib.sha256(output.read_bytes()).hexdigest()}
    output.with_suffix(".build.json").write_text(json.dumps(receipt, indent=2)+"\n")
    print(output)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--setup-sdk", action="store_true")
    parser.add_argument("--host-test", action="store_true")
    args = parser.parse_args()
    if args.setup_sdk:
        install_sdk()
        return
    if args.host_test:
        build(ROOT / "portable/tests/host/smoke.c",
              ROOT / "build/portable/host-smoke.exe",
              [ROOT / "portable/platform/sdl3/host.c"])
        return
    main_file = ROOT / "portable/main.c"
    if not main_file.exists():
        raise SystemExit("Native startup is still being integrated; --host-test builds the host boundary")
    sources = sorted(p for folder in ("game", "render", "ui_model", "audio", "platform")
                     for p in (ROOT / "portable" / folder).rglob("*.c")
                     if not p.is_relative_to(ROOT / "portable/game/recovered"))
    build(main_file, ROOT / "build/portable/simant-sdl3.exe", sources)


if __name__ == "__main__":
    main()
