"""Link actual whole-TU RNG with the real native CRT state owner.

This is an integration control. It inherits the separately pinned DOS RNG
algorithm evidence; it does not count its model checks as fresh DOS comparisons.
"""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[3]

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="build/workers/whole_program/runtime-rng")
    args = parser.parse_args()
    out = (ROOT / args.out).resolve()
    if not out.is_relative_to(ROOT / "build/workers"):
        raise ValueError("test output must be scratch under build/workers")
    out.mkdir(parents=True, exist_ok=False)
    paths = [ROOT / rel for rel in [
        "portable/tests/whole_program/run_runtime_rng.py",
        "portable/tests/whole_program/runtime_rng_probe.c",
        "build/workers/whole_program/generated/root_m0093.c",
        "build/workers/whole_program/generated/dos_types.h",
        "portable/whole_program/platform/crt_rng.c",
        "portable/whole_program/platform/crt_rng.h",
        "portable/whole_program/platform/dos_memory.h",
        "portable/game/simulation/rng.c", "portable/game/simulation/rng.h",
        "portable/tests/rng/rng-dos-differential.json"]]
    before = {p.relative_to(ROOT).as_posix(): sha(p) for p in paths}
    compiler = Path("C:/msys64/mingw64/bin/gcc.exe")
    executable = out / "probe.exe"
    command = [str(compiler), "-std=c11", "-O2", "-fsigned-char", "-ffunction-sections",
        "-fdata-sections", "-I", str(ROOT), "-Wl,--gc-sections", "-o", str(executable),
        str(paths[1]), str(paths[2]), str(paths[4]), str(paths[7])]
    built = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    (out / "compile.txt").write_text(built.stdout + built.stderr)
    if built.returncode:
        raise RuntimeError(built.stderr)
    result = subprocess.run([str(executable)], capture_output=True, text=True, check=True)
    stable = before == {p.relative_to(ROOT).as_posix(): sha(p) for p in paths}
    if not stable: raise RuntimeError("source changed during integration check")
    report = {"status": "PASS_NATIVE_INTEGRATION", "claim": "No fresh DOS equivalence or acceptance claim",
        "inputs": before, "inputs_stable": stable, "compiler_sha256": sha(compiler),
        "command": command, "native_executable_sha256": sha(executable),
        "output": result.stdout, "streams": 8192,
        "boundary": "Real source RRand and private SRand owner linked to actual native CRT runtime owner; scripted TickCount only",
        "excluded": "Physical GetRRandSeed and divide-fault boundaries use abort-only link traps; never reached in this suite and never supply a result"}
    (out / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(result.stdout.strip())

if __name__ == "__main__": main()
