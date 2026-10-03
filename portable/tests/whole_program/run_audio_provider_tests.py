#!/usr/bin/env python3
"""Strict source-event and SDL3 dummy-backend tests for whole-program audio."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

SDK = ROOT / "build" / "sdl3-sdk" / "SDL3-3.4.16" / "x86_64-w64-mingw32"
OUT = ROOT / "build" / "workers" / "behavior_tutorial_menu"
REPORT = ROOT / "portable" / "whole_program" / "platform" / "evidence" / "audio-provider-v2.json"
SOURCES = [
    "portable/whole_program/platform/audio_events.c",
    "portable/whole_program/platform/whole_audio_provider.c",
    "portable/research/audio_voice_scheduler.c",
    "portable/research/audio_voice_admission.c",
]
INPUTS = SOURCES + [
    "portable/whole_program/platform/audio_events.h",
    "portable/whole_program/platform/whole_audio_provider.h",
    "portable/platform/sdl3/whole_audio_provider.c",
    "portable/platform/sdl3/whole_audio_provider.h",
    "portable/platform/sdl3/audio.c",
    "portable/platform/sdl3/audio.h",
    "portable/tests/whole_program/audio_events_test.c",
    "portable/tests/whole_program/sdl_whole_audio_test.c",
    "portable/tests/whole_program/run_audio_provider_tests.py",
    "portable/whole_program/conversions/audio.py",
    "portable/whole_program/platform/audio_events.md",
    "src/root/m290D.c",
    "src/root/m284A.c",
    "src/root/m28BC.asm",
    "src/root/m295C.c",
    "portable/tests/audio/evidence/voice-admission-v2/scheduler-report.json",
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(command: list[str], env: dict[str, str] | None = None) -> str:
    result = subprocess.run(command, cwd=ROOT, env=env, text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if result.returncode:
        raise RuntimeError(f"command failed ({result.returncode}): {command}\n{result.stdout}")
    return result.stdout.strip()


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    compiler = shutil.which("gcc") or "C:/msys64/mingw64/bin/gcc.exe"
    if not Path(compiler).exists() and shutil.which(compiler) is None:
        raise SystemExit("MinGW GCC is required")
    if not (SDK / "include" / "SDL3" / "SDL.h").exists():
        raise SystemExit("verified SDL3 SDK is missing at build/sdl3-sdk")

    common = ["-std=c11", "-Wall", "-Wextra", "-Werror", "-pedantic",
              "-I", str(ROOT / "portable/research"),
              "-I", str(ROOT / "portable/whole_program/platform")]
    direct_exe = OUT / "audio_events_test.exe"
    run([compiler, *common,
         str(ROOT / "portable/tests/whole_program/audio_events_test.c"),
         *(str(ROOT / src) for src in SOURCES), "-o", str(direct_exe)])
    direct_output = run([str(direct_exe)])

    sdl_exe = OUT / "sdl_whole_audio_test.exe"
    sdl_sources = [
        "portable/tests/whole_program/sdl_whole_audio_test.c",
        "portable/platform/sdl3/whole_audio_provider.c",
        "portable/platform/sdl3/audio.c",
        *SOURCES,
    ]
    run([compiler, *common,
         "-I", str(SDK / "include"),
         "-I", str(ROOT / "portable/platform/sdl3"),
         *(str(ROOT / src) for src in sdl_sources),
         "-L", str(SDK / "lib"), "-lSDL3", "-o", str(sdl_exe)])
    env = os.environ.copy()
    env["SDL_AUDIODRIVER"] = "dummy"
    env["PATH"] = str(SDK / "bin") + os.pathsep + env.get("PATH", "")
    sdl_output = run([str(sdl_exe)], env)

    spec = __import__("importlib.util", fromlist=["spec_from_file_location"])
    adapter_path = ROOT / "portable/whole_program/conversions/audio.py"
    adapter_spec = spec.spec_from_file_location("simant_audio_conversion", adapter_path)
    adapter = spec.module_from_spec(adapter_spec)
    adapter_spec.loader.exec_module(adapter)
    original = (ROOT / "src/root/m290D.c").read_text(encoding="utf-8")
    converted, ledger = adapter.adapt("src/root/m290D.c", original)
    if ("portable_whole_audio_sample_start" not in converted or
            "portable_whole_audio_sample_stop" not in converted or
            ledger["source"]["sha256"] != "eaec23e8d37bd606616dc44208c7bbcf82ced13e24abe0362ef767c5e4cc4fed"):
        raise SystemExit("source-identity or m290D event adapter control failed")

    source_pins = {
        "src/root/m290D.c": "eaec23e8d37bd606616dc44208c7bbcf82ced13e24abe0362ef767c5e4cc4fed",
        "src/root/m284A.c": "bad7d3701a853ba2de166e4f875ba3043f33ca136b7d0dcff41db8e5459f9fa5",
        "src/root/m28BC.asm": "361f33c1d86502fef4d43559cb7f424e350eee3fe8a31881ed3c21b4d865f7a5",
        "src/root/m295C.c": "d392b6ce886cfd664a192194b79569bb6a0d4dea8b0bc029ffa9e32ff44add89",
    }
    for relative, expected in source_pins.items():
        if sha(ROOT / relative) != expected:
            raise SystemExit(f"pinned DOS source changed: {relative}")

    report = {
        "schema": "whole-program-audio-provider-test-v2",
        "status": "PASS",
        "boundary": "Timestamped m290D sampled-DAC event records are applied in order to the frozen two-channel scheduler and queued through a real SDL3 mono-U8 stream; m284A's original sequencer can be bound at the source m28BC divider cadence.",
        "tests": [
            {"path": "portable/tests/whole_program/audio_events_test.c", "status": "PASS", "stdout": direct_output},
            {"path": "portable/tests/whole_program/sdl_whole_audio_test.c", "status": "PASS", "stdout": sdl_output, "device": "SDL_AUDIODRIVER=dummy"},
            {"path": "portable/whole_program/conversions/audio.py", "status": "PASS", "m290D_source_sha256": ledger["source"]["sha256"], "converted_sha256": ledger["output_sha256"]},
        ],
        "sdl": {"version": "3.4.16", "rate_hz": 11932, "format": "mono U8", "backend": "dummy test device; production stream is default SDL playback"},
        "source_pins": source_pins,
        "scheduler_reference_report_sha256": sha(ROOT / "portable/tests/audio/evidence/voice-admission-v2/scheduler-report.json"),
        "inputs": {path: sha(ROOT / path) for path in INPUTS},
        "limits": [
            "The bounded provider handles type-1 sampled-DAC voices. MIDI/OPL/type-2 hardware families and DOS device detection remain unsupported.",
            "This test binds a sequencer cadence callback but does not execute the generated f_284A_067F against a loaded song. The live application must bind that actual generated function after source state initialization.",
            "The separate 365-tick frozen DOS ISR differential covers scheduler cursor and register logic; this SDL test proves stream/device integration, not physical PC-speaker acoustics or a DOS-to-SDL end-to-end song comparison.",
        ],
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(REPORT.relative_to(ROOT).as_posix())
    print("PASS: direct provider, SDL dummy stream, source adapter, and frozen source pins")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
