"""Build and run the input/time SDL binding against SDL's dummy video driver."""
from __future__ import annotations

import argparse
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SDK = ROOT / "build/sdl3-sdk/SDL3-3.4.16/x86_64-w64-mingw32"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path,
                        default=ROOT / "build/workers/input_time_host_smoke.exe")
    args = parser.parse_args()
    output = args.output if args.output.is_absolute() else ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "gcc", "-std=c11", "-Wall", "-Wextra", "-Werror", "-pedantic",
        "-D__USE_MINGW_SETJMP_NON_SEH", "-I", str(SDK / "include"),
        "portable/tests/whole_program/input_time_host_smoke.c",
        "portable/whole_program/platform/sdl3/input_time_host.c",
        "portable/whole_program/platform/input_time.c",
        "portable/game/timing.c", "portable/platform/sdl3/host.c",
        "-L", str(SDK / "lib"), "-lSDL3", "-o", str(output),
    ]
    subprocess.run(command, cwd=ROOT, check=True)
    env = os.environ.copy()
    env["PATH"] = str(SDK / "bin") + os.pathsep + env.get("PATH", "")
    env["SDL_VIDEODRIVER"] = "dummy"
    subprocess.run([str(output)], cwd=ROOT, env=env, check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
