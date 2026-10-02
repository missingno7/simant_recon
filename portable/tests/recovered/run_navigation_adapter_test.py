#!/usr/bin/env python3
"""Build and run the bounded recovered navigation adapter state test."""
from __future__ import annotations

import subprocess
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
GCC = Path("C:/msys64/mingw64/bin/gcc.exe")
PROFILES = {
    "next": ROOT / "build/workers/recovered_source_next/generated",
    "current": ROOT / "build/workers/recovered_source/generated",
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", choices=PROFILES, default="next")
    profile = parser.parse_args().profile
    generated = PROFILES[profile]
    output = ROOT / f"build/portable/navigation-adapter-test-{profile}.exe"
    evidence = ROOT / f"portable/tests/recovered/evidence/navigation-adapter-{profile}-focused.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    command = [
        str(GCC), "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
        "-mconsole",
        "-I", str(ROOT / "portable/game/recovered"),
        "-I", str(generated),
        str(ROOT / "portable/tests/recovered/navigation_adapter_test.c"),
        str(ROOT / "portable/game/recovered/navigation_adapter.c"),
        str(generated / "recovered_state.c"),
        "-o", str(output),
    ]
    subprocess.run(command, check=True, cwd=ROOT)
    subprocess.run([str(output)], check=True, cwd=ROOT)
    components = [
        ROOT / "portable/game/recovered/navigation_adapter.c",
        ROOT / "portable/game/recovered/navigation_adapter.h",
        ROOT / "portable/tests/recovered/navigation_adapter_test.c",
        Path(__file__).resolve(),
        generated / "recovered_state.h",
    ]
    evidence.parent.mkdir(parents=True, exist_ok=True)
    evidence.write_text(json.dumps({
        "schema": "navigation-adapter-focused-test-v1",
        "profile": profile,
        "status": "PASS",
        "command": ["python", "portable/tests/recovered/run_navigation_adapter_test.py",
                    "--profile", profile],
        "binary_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
        "components": {
            str(path.relative_to(ROOT)).replace("\\", "/"):
                hashlib.sha256(path.read_bytes()).hexdigest()
            for path in components
        },
        "checks": [
            "GotoMyAnt updates the recovered view before synchronously delivering CENTER_VIEW",
            "tutorial GotoMyAnt emits myBeginSound(1, 0, 0x7e) and no navigation event",
            "a rejected synchronous event marks the binding failed without aborting",
        ],
        "scope": "Native adapter contract test; not an original-DOS differential proof.",
    }, indent=2) + "\n", encoding="utf-8")
    print(f"navigation adapter focused test ({profile} profile): PASS")


if __name__ == "__main__":
    main()
