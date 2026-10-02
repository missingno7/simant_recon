#!/usr/bin/env python3
"""Compile and run the pure source-derived game-over score model tests."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[3]
PORT = ROOT / "portable"
MODEL = PORT / "ui_model/dialogs/game_over.c"
DATABASE = PORT / "game/resources/database.c"
TEST = PORT / "tests/dialogs/game_over_test.c"
RUNNER = Path(__file__).resolve()


def digest(paths: list[Path]) -> str:
    sha = hashlib.sha256()
    for path in sorted(paths, key=lambda item: item.as_posix()):
        sha.update(path.as_posix().encode("utf-8"))
        sha.update(b"\0")
        sha.update(hashlib.sha256(path.read_bytes()).digest())
    return sha.hexdigest()


def main() -> None:
    compiler = os.environ.get("SIMANT_CC") or shutil.which("gcc")
    if not compiler:
        fallback = Path("C:/msys64/mingw64/bin/gcc.exe")
        compiler = str(fallback) if fallback.exists() else None
    if not compiler:
        raise SystemExit("Native C compiler missing; set SIMANT_CC")

    inputs = [MODEL, DATABASE, TEST, RUNNER,
              PORT / "ui_model/dialogs/game_over.h",
              PORT / "game/resources/database.h"]
    source_hash = digest(inputs)
    temporary_root = ROOT / "build/portable/tests"
    temporary_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="game-over-",
                                     dir=temporary_root) as temporary:
        executable = Path(temporary) / "game-over-test.exe"
        command = [compiler, "-std=c11", "-O0", "-Wall", "-Wextra",
                   "-Werror", str(MODEL), str(DATABASE), str(TEST),
                   "-o", str(executable)]
        try:
            built = subprocess.run(command, cwd=ROOT, capture_output=True,
                                   text=True, timeout=30)
        except subprocess.TimeoutExpired as error:
            raise SystemExit(f"game-over test build timed out: {error}")
        if built.returncode != 0:
            print(built.stdout, end="")
            print(built.stderr, end="")
            raise SystemExit(built.returncode)
        try:
            ran = subprocess.run([str(executable)], cwd=ROOT,
                                 capture_output=True, text=True, timeout=10)
        except subprocess.TimeoutExpired as error:
            if error.stdout:
                print(error.stdout.decode() if isinstance(error.stdout, bytes)
                      else error.stdout, end="")
            if error.stderr:
                print(error.stderr.decode() if isinstance(error.stderr, bytes)
                      else error.stderr, end="")
            raise SystemExit(f"game-over test timed out: {error}")
        print(ran.stdout, end="")
        print(ran.stderr, end="")
        if ran.returncode != 0:
            raise SystemExit(ran.returncode)
    if digest(inputs) != source_hash:
        raise SystemExit("game-over test inputs changed during execution")
    print(f"test_input_sha256={source_hash}")


if __name__ == "__main__":
    main()
