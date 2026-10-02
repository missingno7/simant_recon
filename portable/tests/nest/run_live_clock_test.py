#!/usr/bin/env python3
"""Compile and run the focused lazy TickCount-provider contract checks."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[3]
PORT = ROOT / "portable"
SOURCES = [
    PORT / "tests/nest/live_clock_test.c",
    PORT / "game/simulation/nest.c",
    PORT / "game/simulation/rng.c",
    PORT / "game/simulation/movement.c",
    PORT / "game/simulation/movement.h",
    PORT / "game/simulation/nest.h",
    Path(__file__).resolve(),
]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    compiler = os.environ.get("SIMANT_CC") or shutil.which("gcc")
    if not compiler:
        fallback = Path("C:/msys64/mingw64/bin/gcc.exe")
        compiler = str(fallback) if fallback.exists() else None
    if not compiler:
        raise SystemExit("Native C compiler missing; set SIMANT_CC")

    before = {path.relative_to(ROOT).as_posix(): digest(path) for path in SOURCES}
    build_root = ROOT / "build/portable/tests"
    build_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="nest-live-clock-", dir=build_root) as tmp:
        suffix = ".exe" if os.name == "nt" else ""
        executable = Path(tmp) / f"nest-live-clock-test{suffix}"
        command = [compiler, "-std=c11", "-O0", "-Wall", "-Wextra", "-Werror",
                   "-I", str(PORT), str(SOURCES[0]), str(SOURCES[1]),
                   str(SOURCES[2]), str(SOURCES[3]), "-o", str(executable)]
        built = subprocess.run(command, cwd=ROOT, text=True, capture_output=True,
                               timeout=60)
        if built.returncode:
            raise SystemExit(built.stdout + built.stderr)
        ran = subprocess.run([str(executable)], cwd=ROOT, text=True,
                             capture_output=True, timeout=15)
        print(ran.stdout, end="")
        print(ran.stderr, end="")
        if ran.returncode:
            raise SystemExit(ran.returncode)

    after = {path.relative_to(ROOT).as_posix(): digest(path) for path in SOURCES}
    if before != after:
        raise SystemExit("source inputs changed during nest live-clock test")
    print("source_input_sha256=" + hashlib.sha256(
        "".join(k + v for k, v in sorted(after.items())).encode()).hexdigest())


if __name__ == "__main__":
    main()
