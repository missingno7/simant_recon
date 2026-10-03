"""Compile and run the cooperative BIOS-key service boundary smoke."""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SDK = ROOT / "build/sdl3-sdk/SDL3-3.4.16/x86_64-w64-mingw32"
OUTPUT = ROOT / "build/workers/input_time_host_cooperative_smoke.exe"


def main() -> int:
    command = [
        "gcc", "-std=c11", "-Wall", "-Wextra", "-Werror", "-pedantic",
        "-D__USE_MINGW_SETJMP_NON_SEH", "-I", str(SDK / "include"),
        "portable/tests/whole_program/input_time_host_cooperative_smoke.c",
        "portable/whole_program/platform/sdl3/input_time_host.c",
        "portable/whole_program/platform/input_time.c",
        "portable/game/timing.c", "portable/platform/sdl3/host.c",
        "-L", str(SDK / "lib"), "-lSDL3", "-o", str(OUTPUT),
    ]
    subprocess.run(command, cwd=ROOT, check=True)
    env = os.environ.copy()
    env["PATH"] = str(SDK / "bin") + os.pathsep + env.get("PATH", "")
    env["SDL_VIDEODRIVER"] = "dummy"
    subprocess.run([str(OUTPUT)], cwd=ROOT, env=env, check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
