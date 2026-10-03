#!/usr/bin/env python3
"""Exercise generated-source song cancellation/restart through an SDL3 dummy stream."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
GENERATED = ROOT / "build/workers/whole_program/generated"
SDK = ROOT / "build/sdl3-sdk/SDL3-3.4.16/x86_64-w64-mingw32"
OUT = ROOT / "build/workers/behavior_tutorial_menu"
REPORT = ROOT / "portable/tests/whole_program/evidence/generated-song-sdl-run-v2.json"
HARNESS = "portable/tests/whole_program/generated_song_sdl_harness.c"
DIRECT_HARNESS = "portable/tests/whole_program/generated_song_harness.c"
RUNNER = "portable/tests/whole_program/run_generated_song_sdl_harness.py"
GENERATED_INPUTS = [
    "root_m284A.c", "root_m290D.c", "root_m295C.c",
    "data_d55B3_0064.c", "data_d55B3_00B8.c",
]
PORTABLE_INPUTS = [
    HARNESS, DIRECT_HARNESS, RUNNER,
    "portable/game/resources/database.c",
    "portable/game/resources/database.h",
    "portable/audio/intent.c", "portable/audio/intent.h",
    "portable/audio/dac_mixer.c", "portable/audio/dac_mixer.h",
    "portable/whole_program/platform/audio.c",
    "portable/whole_program/platform/audio_events.c",
    "portable/whole_program/platform/audio_events.h",
    "portable/whole_program/platform/whole_audio_provider.c",
    "portable/whole_program/platform/whole_audio_provider.h",
    "portable/research/audio_voice_scheduler.c",
    "portable/research/audio_voice_scheduler.h",
    "portable/research/audio_voice_admission.c",
    "portable/platform/sdl3/audio.c", "portable/platform/sdl3/audio.h",
    "portable/platform/sdl3/whole_audio_provider.c",
    "portable/platform/sdl3/whole_audio_provider.h",
    "src/root/m284A.c", "src/root/m290D.c", "src/root/m295C.c",
    "src/data/d55B3_0064.c", "src/data/d55B3_00B8.c",
    "assets/SOUND.NDX", "assets/SOUND.DAT",
]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pin(path: Path) -> dict[str, object]:
    return {"path": path.relative_to(ROOT).as_posix(),
            "size": path.stat().st_size, "sha256": digest(path)}


def run(command: list[str], env: dict[str, str] | None = None) -> str:
    result = subprocess.run(command, cwd=ROOT, env=env, text=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT)
    if result.returncode:
        raise RuntimeError(f"exit {result.returncode}: {command}\n{result.stdout}")
    return result.stdout.strip()


def main() -> int:
    if REPORT.exists():
        raise SystemExit(f"refusing to overwrite immutable receipt: {REPORT}")
    if not (SDK / "include/SDL3/SDL.h").is_file():
        raise SystemExit(f"SDL3 3.4.16 SDK missing at {SDK}")
    missing = [str(GENERATED / name) for name in GENERATED_INPUTS
               if not (GENERATED / name).is_file()]
    if missing:
        raise SystemExit("generated whole-program modules are missing: " +
                         ", ".join(missing))
    compiler = shutil.which("gcc") or "C:/msys64/mingw64/bin/gcc.exe"
    if not Path(compiler).is_file() and shutil.which(compiler) is None:
        raise SystemExit("MinGW GCC is required")
    OUT.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    executable = OUT / "generated_song_sdl_harness.exe"
    generated_sources = [str(GENERATED / name) for name in GENERATED_INPUTS]
    portable_sources = [str(ROOT / name) for name in PORTABLE_INPUTS
                        if name.startswith("portable/") and name.endswith(".c") and
                        name not in (HARNESS, DIRECT_HARNESS)]
    command = [
        compiler, "-std=c11", "-O0", "-Wall", "-Wextra", "-Werror",
        "-Wno-unused-parameter", "-Wno-incompatible-pointer-types",
        "-Wno-type-limits", "-Wno-unused-variable",
        "-ffunction-sections", "-fdata-sections",
        "-I", str(ROOT), "-I", str(ROOT / "portable/whole_program/platform"),
        "-I", str(ROOT / "portable/research"),
        "-I", str(ROOT / "portable/platform/sdl3"),
        "-I", str(SDK / "include"),
        str(ROOT / HARNESS), *generated_sources, *portable_sources,
        "-L", str(SDK / "lib"), "-lSDL3", "-Wl,--gc-sections",
        "-o", str(executable),
    ]
    compile_output = run(command)
    env = os.environ.copy()
    env["SDL_AUDIODRIVER"] = "dummy"
    env["PATH"] = str(SDK / "bin") + os.pathsep + env.get("PATH", "")
    output = run([str(executable), str(ROOT / "assets/SOUND")], env)
    receipt = {
        "schema": "generated-source-song-sdl-run-v1",
        "status": "PASS",
        "result": output,
        "sdl_audio_driver": "dummy",
        "compile_stdout": compile_output,
        "compile_command": command,
        "generated_module_inputs": [pin(GENERATED / name)
                                     for name in GENERATED_INPUTS],
        "test_and_runtime_inputs": [pin(ROOT / name)
                                    for name in PORTABLE_INPUTS],
        "coverage": [
            "generated f_284A_0013 starts the actual SOUND song and initializes the source timer divider",
            "generated f_284A_067F is invoked at the bound source divider cadence while SDL3 queues actual mono U8 frames",
            "generated f_295C_01EC / f_295C_02E8 allocate and stop source sampled-DAC voices through generated m290D event hooks",
            "original StopSong cancels an active song note, with the timestamped stop event consumed as SDL playback advances",
            "the same source song restarts and reaches the original end state through the SDL3 dummy playback stream",
        ],
        "host_boundary": {
            "resource_loading_and_mode_selection": "test host loads actual SOUND kind-18, kind-20, and kind-5 resources and seeds the actual mode-1 voice table/two-channel topology; device detection and f_0000_0193 allocator/unhook lifetime are outside this harness",
            "clock": "SDL monotonic time plus queued SDL frames for asynchronous event deadlines; deterministic provider sample cursor while the source tick callback is running",
            "unselected_instrument_families": "FM/PSG/external MIDI services are not selected by the mode-1 DAC voice table and remain explicit unprovided services",
        },
        "limitations": [
            "dummy SDL output confirms stream plumbing but cannot establish audible acoustic quality",
            "no DOS hardware detection, BIOS/port/MPU/OPL emulation, or DOS-vs-C waveform equivalence claim",
        ],
    }
    REPORT.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(output)
    print(f"receipt={REPORT.relative_to(ROOT).as_posix()}")
    print(f"receipt_sha256={digest(REPORT)}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as error:
        print(error, file=sys.stderr)
        raise SystemExit(1)
