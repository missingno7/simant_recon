#!/usr/bin/env python3
"""Run generated m284A/m295C/m290D song flow over the shipped SOUND records."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
GENERATED = ROOT / "build/workers/whole_program/generated"
OUT = ROOT / "build/workers/behavior_tutorial_menu"
REPORT = ROOT / "portable/tests/whole_program/evidence/generated-song-run-v2.json"
HARNESS = "portable/tests/whole_program/generated_song_harness.c"
RUNNER = "portable/tests/whole_program/run_generated_song_harness.py"
GENERATED_INPUTS = [
    "root_m284A.c", "root_m290D.c", "root_m295C.c",
    "data_d55B3_0064.c", "data_d55B3_00B8.c",
]
PORTABLE_INPUTS = [
    HARNESS,
    RUNNER,
    "portable/game/resources/database.c",
    "portable/game/resources/database.h",
    "portable/audio/intent.c",
    "portable/audio/intent.h",
    "portable/audio/dac_mixer.c",
    "portable/whole_program/platform/audio.c",
    "portable/whole_program/platform/audio_events.c",
    "portable/whole_program/platform/audio_events.h",
    "portable/whole_program/platform/whole_audio_provider.c",
    "portable/whole_program/platform/whole_audio_provider.h",
    "portable/research/audio_voice_scheduler.c",
    "portable/research/audio_voice_scheduler.h",
    "portable/research/audio_voice_admission.c",
    "src/root/m284A.c", "src/root/m290D.c", "src/root/m295C.c",
    "src/data/d55B3_0064.c", "src/data/d55B3_00B8.c",
    "assets/SOUND.NDX", "assets/SOUND.DAT",
]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def file_pin(path: Path) -> dict[str, object]:
    return {"path": path.relative_to(ROOT).as_posix(),
            "size": path.stat().st_size, "sha256": digest(path)}


def run(command: list[str]) -> str:
    result = subprocess.run(command, cwd=ROOT, text=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT)
    if result.returncode:
        raise RuntimeError(f"exit {result.returncode}: {command}\n{result.stdout}")
    return result.stdout.strip()


def main() -> int:
    if REPORT.exists():
        raise SystemExit(f"refusing to overwrite immutable receipt: {REPORT}")
    missing = [str(GENERATED / name) for name in GENERATED_INPUTS
               if not (GENERATED / name).is_file()]
    if missing:
        raise SystemExit("generated whole-program modules are missing: " +
                         ", ".join(missing))
    OUT.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    compiler = shutil.which("gcc") or "C:/msys64/mingw64/bin/gcc.exe"
    if not Path(compiler).is_file() and shutil.which(compiler) is None:
        raise SystemExit("MinGW GCC is required")

    executable = OUT / "generated_song_harness.exe"
    portable_sources = [str(ROOT / p) for p in PORTABLE_INPUTS
                       if p.startswith("portable/") and p.endswith(".c") and
                       p != HARNESS]
    generated_sources = [str(GENERATED / name) for name in GENERATED_INPUTS]
    command = [
        compiler, "-std=c11", "-O0", "-Wall", "-Wextra", "-Werror",
        "-Wno-unused-parameter", "-Wno-incompatible-pointer-types",
        "-Wno-type-limits", "-Wno-unused-variable",
        "-ffunction-sections", "-fdata-sections",
        "-I", str(ROOT), "-I", str(ROOT / "portable/whole_program/platform"),
        "-I", str(ROOT / "portable/research"),
        str(ROOT / HARNESS), *generated_sources, *portable_sources,
        "-Wl,--gc-sections", "-o", str(executable),
    ]
    compile_stdout = run(command)
    output = run([str(executable), str(ROOT / "assets/SOUND"), "715920"])
    generated_pins = [file_pin(GENERATED / name) for name in GENERATED_INPUTS]
    input_pins = [file_pin(ROOT / name) for name in PORTABLE_INPUTS]
    receipt = {
        "schema": "generated-source-song-run-v1",
        "status": "PASS",
        "result": output,
        "compile_stdout": compile_stdout,
        "compile_command": command,
        "generated_module_inputs": generated_pins,
        "test_and_runtime_inputs": input_pins,
        "host_boundary": {
            "f_0000_0193": "test host implementation loads the actual SOUND kind-18 and kind-20 records, sets Song.data/song resource identity/transpose, and attaches actual kind-5 PCM to the selected source DAC-bank samples; this source loader itself is not the oracle under test",
            "mode1_selection": "test seeds the actual mode-1 DATA voice table and the source two-channel mode-1 channel topology; hardware autodetection/device setup is outside this harness",
            "critical_sections_and_timer_interrupt": "synchronous no-op service boundary; the portable provider advances the source sequencer at the original fd_55B3_6B42 divider cadence and captures m290D events at deterministic sample deadlines",
            "unselected_instrument_families": "FM/PSG/MIDI-device handlers remain unavailable and are not selected by the mode-1 DAC table",
        },
        "coverage": [
            "generated f_284A_0013 initializes the selected original song record",
            "generated f_284A_067F is called by the provider timer cadence until source end state",
            "generated f_284A MIDI parser merges the original kind-20 tracks and dispatches notes through generated m295C voice allocation",
            "generated f_290D selects actual DATA sample objects and emits ordered start/stop events",
            "actual SOUND kind-5 PCM resources are decoded and mixed by the native scheduler",
        ],
        "limitations": [
            "not a DOS-vs-C timing or audible waveform equivalence claim",
            "does not test f_0000_0193's DOS handle allocation/unhook lifetime implementation",
            "does not claim OPL/FM/PSG or external MIDI output support",
            "the SDL dummy-device smoke remains the separate provider bridge test; this run validates generated-source song playback into the provider scheduler",
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
