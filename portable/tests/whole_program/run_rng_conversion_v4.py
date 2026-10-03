"""Build and exercise the whole-program root:0093 source conversion."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "src/root/m0093.c"
CONVERTER = ROOT / "portable/whole_program/conversions/rng.py"
PROBE = ROOT / "portable/tests/whole_program/rng_conversion_probe.c"
RNG_C = ROOT / "portable/game/simulation/rng.c"
RNG_H = ROOT / "portable/game/simulation/rng.h"
WORK = ROOT / "build/workers/whole_program_rng"
OUT = ROOT / "portable/tests/whole_program/evidence/rng-conversion-v4.json"
GCC = Path("C:/msys64/mingw64/bin/gcc.exe")
GENERATED = WORK / "m0093_converted_v4.c"
EXE = WORK / "rng_conversion_probe_v4.exe"
RUNNER = ROOT / "portable/tests/whole_program/run_rng_conversion_v4.py"
RNG_NATIVE_PROOF = ROOT / "portable/tests/rng/rng-dos-differential.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    if OUT.exists() or GENERATED.exists() or EXE.exists():
        raise FileExistsError("RNG conversion outputs are write-once; choose a new evidence version")
    WORK.mkdir(parents=True, exist_ok=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    import sys
    sys.path.insert(0, str(ROOT / "portable"))
    from whole_program.conversions.rng import adapt

    original = SOURCE.read_text(encoding="utf-8")
    converted, ledger = adapt(original)
    with GENERATED.open("x", encoding="utf-8", newline="") as stream:
        stream.write(converted)
    compiler_version = subprocess.run([str(GCC), "--version"], capture_output=True,
                                      text=True, check=True).stdout.splitlines()[0]
    inputs = [SOURCE, CONVERTER, PROBE, RNG_C, RNG_H, RNG_NATIVE_PROOF, RUNNER]
    before = {str(path.relative_to(ROOT)).replace("\\", "/"): sha(path) for path in inputs}
    command = [str(GCC), "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
               "-I", ".", "-o", str(EXE), str(GENERATED), str(RNG_C), str(PROBE)]
    built = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    if built.returncode:
        raise RuntimeError(f"RNG conversion compile failed:\n{built.stdout}\n{built.stderr}")
    ran = subprocess.run([str(EXE)], cwd=ROOT, capture_output=True, text=True)
    if ran.returncode:
        raise RuntimeError(f"RNG conversion probe failed ({ran.returncode}):\n{ran.stdout}\n{ran.stderr}")
    after = {str(path.relative_to(ROOT)).replace("\\", "/"): sha(path) for path in inputs}
    if before != after:
        raise RuntimeError("pinned source/converter/native-control inputs changed during test")
    report = {
        "schema": "whole-program-rng-conversion-test-v1",
        "status": "PASS",
        "conversion": ledger,
        "source_inputs": before,
        "compiler": {"path": str(GCC), "sha256": sha(GCC), "version": compiler_version,
                     "flags": ["-std=c11", "-O2", "-Wall", "-Wextra", "-Werror"]},
        "compile_command": command,
        "native_executable_sha256": sha(EXE),
        "probe": ran.stdout.strip(),
        "probe_stderr": ran.stderr,
        "coverage": {
            "mask_calls": 65536 * 8,
            "mask_functions": 8,
            "bounded_srand1_calls": 65536 * 7,
            "srand1_ranges": [1, 3, 7, 8, 255, 32767, 65535],
            "rrand_calls": 65536 * 3,
            "zero_divisor": "explicit _Noreturn host leaf observed once; seed update verified before fault",
            "get_rrand_seed": "host leaf observed physical 0x46c0 for DOS far pointer 046C:0000",
            "runtime_rand": "dos_crt_srand/dos_crt_rand test provider delegates to existing sim_rng_msc_rand in rng.c",
            "native_control_proof": {"path": "portable/tests/rng/rng-dos-differential.json",
                                     "sha256": sha(RNG_NATIVE_PROOF),
                                     "status": json.loads(RNG_NATIVE_PROOF.read_text(encoding="utf-8"))["status"]},
            "tick_and_get_rrand_seed_platform_hooks": "test shims only; conversion leaves those provider symbols unresolved",
        },
        "limits": [
            "The test fixture supplies TickCount, the physical-memory leaf, and the divide-fault leaf; production platform implementations remain unprovided.",
            "The test runtime provider delegates MSC rand to rng.c; no second production simulation-state owner was introduced.",
            "SRand1 range zero checks the explicit nonreturn fault boundary; no RRand zero-limit behavior is claimed.",
        ],
    }
    with OUT.open("x", encoding="utf-8", newline="") as stream:
        json.dump(report, stream, indent=2)
        stream.write("\n")
    print(json.dumps({"status": report["status"], "probe": report["probe"],
                      "report": str(OUT.relative_to(ROOT))}, indent=2))


if __name__ == "__main__":
    main()
