#!/usr/bin/env python3
"""Compile and exercise the isolated native CRT boundary provider."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[4]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    gcc_name = shutil.which("gcc") or r"C:\msys64\mingw64\bin\gcc.exe"
    gcc = Path(gcc_name).resolve()
    if not gcc.is_file():
        raise SystemExit(f"GCC not found: {gcc}")
    with tempfile.TemporaryDirectory(prefix="simant-crt-abi-") as td:
        exe = Path(td) / "crt-abi-test.exe"
        command = [str(gcc), "-std=c11", "-O0", "-Wall", "-Wextra", "-Werror",
                   "-I", str(ROOT), str(ROOT / "portable/whole_program/platform/crt_abi.c"),
                   str(ROOT / "portable/tests/whole_program/platform/crt_abi_test.c"),
                   "-o", str(exe)]
        build = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=30)
        if build.returncode:
            raise SystemExit(build.stderr)
        positive = subprocess.run([str(exe)], cwd=ROOT, capture_output=True,
                                   text=True, timeout=10)
        if positive.returncode:
            raise SystemExit(f"positive CRT contract failed: {positive.returncode} {positive.stderr}")
        negative = subprocess.run([str(exe), "unsupported-ctype"], cwd=ROOT,
                                  capture_output=True, text=True, timeout=10)
        if negative.returncode == 0 or "non-ASCII" not in negative.stderr:
            raise SystemExit("unsupported ctype control did not fail closed")
        report = {
            "schema": "simant-native-crt-provider-unit-v1",
            "status": "PASS_BOUNDED_NATIVE_PROVIDER_CONTRACT",
            "oracle_equivalence_claim": None,
            "positive": {"returncode": positive.returncode, "stdout": positive.stdout,
                         "stderr": positive.stderr},
            "negative_unsupported_ctype": {"returncode": negative.returncode,
                                             "stderr": negative.stderr},
            "command": command,
            "compiler_sha256": sha(gcc),
            "inputs": {
                "portable/whole_program/platform/crt_abi.c": sha(ROOT / "portable/whole_program/platform/crt_abi.c"),
                "portable/whole_program/platform/crt_abi.h": sha(ROOT / "portable/whole_program/platform/crt_abi.h"),
                "portable/tests/whole_program/platform/crt_abi_test.c": sha(ROOT / "portable/tests/whole_program/platform/crt_abi_test.c"),
            },
        }
        out = ROOT / "build/workers/behavior_memory/crt-abi-unit-v1.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        if out.exists():
            raise SystemExit(f"refusing to overwrite {out}")
        out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"status": report["status"], "report": str(out)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
