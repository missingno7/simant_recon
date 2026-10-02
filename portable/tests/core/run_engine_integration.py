#!/usr/bin/env python3
"""Link the diagnostic recovered profile to the actual native session path."""
from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import hashlib
import tempfile

ROOT = Path(__file__).resolve().parents[3]
PORT = ROOT / "portable"
PROFILE = ROOT / "build/workers/recovered_source_next2/generated"


def input_hash(paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(set(paths), key=lambda value: value.as_posix()):
        digest.update(path.as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


def main() -> None:
    compiler = os.environ.get("SIMANT_CC") or shutil.which("gcc")
    if not compiler:
        fallback = Path("C:/msys64/mingw64/bin/gcc.exe")
        compiler = str(fallback) if fallback.exists() else None
    if not compiler:
        raise SystemExit("Native C compiler missing; set SIMANT_CC")
    if not (PROFILE / "provenance.json").is_file():
        raise SystemExit(f"Generated diagnostic profile is missing: {PROFILE}")

    native_sources = sorted([
        *PORT.joinpath("game").glob("*.c"),
        PORT / "platform/memory.c",
        *(p for folder in (
            "game/simulation", "game/state", "game/resources", "game/render",
            "render", "ui_model", "audio")
          for p in PORT.joinpath(folder).rglob("*.c")),
    ])
    recovered_sources = [
        PORT / "game/recovered/engine.c",
        PORT / "game/recovered/session_bridge.c",
        PORT / "game/recovered/audio_adapter.c",
        PORT / "game/recovered/memory_adapter.c",
        PORT / "game/recovered/nest_adapter.c",
    ]
    generated_inputs = sorted(
        path for path in PROFILE.iterdir()
        if path.is_file() and path.suffix in (".c", ".h", ".o", ".json")
    )
    generated_objects = [path for path in generated_inputs if path.suffix == ".o"]
    if not generated_objects:
        raise SystemExit(f"No generated object files in {PROFILE}")

    test_source = PORT / "tests/core/engine_integration.c"
    headers = sorted(PORT.rglob("*.h"))
    source_pins = [test_source, *native_sources, *recovered_sources,
                   *headers, Path(__file__).resolve()]
    pinned_inputs = [*source_pins, *generated_inputs]
    source_hash_before = input_hash(source_pins)
    profile_hash_before = input_hash(generated_inputs)
    provenance = PROFILE / "provenance.json"
    provenance_hash = hashlib.sha256(provenance.read_bytes()).hexdigest()

    with tempfile.TemporaryDirectory(prefix="engine-integration-",
                                     dir=ROOT / "build/portable/tests") as tmp:
        output = Path(tmp) / "engine-integration.exe"
        command = [
            compiler, "-std=c11", "-O0", "-Wall", "-Wextra", "-Werror",
            "-I", str(PORT), "-I", str(PROFILE),
            str(test_source),
            *(str(p) for p in native_sources + recovered_sources),
            *(str(p) for p in generated_objects), "-o", str(output),
        ]
        print("Linking actual-session recovered-core integration harness",
              flush=True)
        try:
            linked = subprocess.run(command, cwd=ROOT, text=True,
                                    capture_output=True, timeout=120)
        except subprocess.TimeoutExpired as error:
            raise SystemExit(f"integration build timed out: {error}")
        if linked.returncode:
            print(linked.stdout + linked.stderr, end="")
            raise SystemExit(linked.returncode)
        try:
            executed = subprocess.run([str(output)], cwd=ROOT, text=True,
                                      capture_output=True, timeout=60)
        except subprocess.TimeoutExpired as error:
            raise SystemExit(f"integration executable timed out: {error}")
        print(executed.stdout, end="")
        print(executed.stderr, end="")
        if executed.returncode:
            raise SystemExit(executed.returncode)

    source_hash_after = input_hash(source_pins)
    profile_hash_after = input_hash(generated_inputs)
    print(f"source_input_sha256={source_hash_before}")
    print(f"profile_input_sha256={profile_hash_before}")
    print(f"profile_provenance_sha256={provenance_hash}")
    if (source_hash_after != source_hash_before or
            profile_hash_after != profile_hash_before):
        raise SystemExit("integration source/profile inputs changed during run")


if __name__ == "__main__":
    main()
