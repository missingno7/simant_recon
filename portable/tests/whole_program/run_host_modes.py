"""Real SDL presentation controls for the original EGA and VGA geometries."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import subprocess

ROOT = Path(__file__).resolve().parents[3]

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="build/workers/whole_program/host-modes-v1")
    args = parser.parse_args()
    out = (ROOT / args.out).resolve()
    if not out.is_relative_to(ROOT / "build/workers"):
        raise ValueError("output must be scratch under build/workers")
    out.mkdir(parents=True, exist_ok=False)
    sdk = ROOT / "build/sdl3-sdk/SDL3-3.4.16/x86_64-w64-mingw32"
    paths = [ROOT / name for name in (
        "portable/tests/whole_program/run_host_modes.py",
        "portable/tests/whole_program/host_modes_probe.c",
        "portable/whole_program/platform/sdl3/host.c",
        "portable/whole_program/platform/sdl3/host_modes.h",
        "portable/platform/host.h",
        "portable/platform/sdl3/host.c",
        "src/S00/m31AD_2AB4.asm", "assets/SIMANT.CFG")]
    before = {p.relative_to(ROOT).as_posix(): sha(p) for p in paths}
    compiler = Path("C:/msys64/mingw64/bin/gcc.exe")
    executable = out / "probe.exe"
    command = [str(compiler), "-std=c11", "-Wall", "-Wextra", "-Werror",
        "-pedantic", "-I", str(sdk / "include"), str(paths[1]), str(paths[2]),
        "-L", str(sdk / "lib"), "-lSDL3", "-o", str(executable)]
    built = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    (out / "compile.txt").write_text(built.stdout + built.stderr)
    if built.returncode:
        raise RuntimeError(built.stderr)
    env = os.environ.copy()
    env["PATH"] = str(sdk / "bin") + os.pathsep + env.get("PATH", "")
    env["SDL_VIDEODRIVER"] = "dummy"
    run = subprocess.run([str(executable), str(out / "vga.bmp"), str(out / "ega.bmp")],
        cwd=ROOT, env=env, capture_output=True, text=True, timeout=30)
    stable = before == {p.relative_to(ROOT).as_posix(): sha(p) for p in paths}
    report = {"status": "PASS_NATIVE_SDL_CONTRACT" if run.returncode == 0 and stable else "FAIL",
        "claim": "Real SDL provider geometry, not DOS pixel or whole-game equivalence",
        "inputs": before, "inputs_stable": stable, "command": command,
        "compiler_sha256": sha(compiler), "sdl_dll_sha256": sha(sdk / "bin/SDL3.dll"),
        "executable_sha256": sha(executable), "returncode": run.returncode,
        "stdout": run.stdout, "stderr": run.stderr,
        "controls": ["640x480 frame/BMP", "640x350 frame/BMP", "mode switching",
            "invalid geometry preserves mode", "short stride rejected",
            "last-row palette error rejected", "legacy creation default preserved"]}
    (out / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    if report["status"] == "FAIL": raise RuntimeError(report)
    print(report["status"])

if __name__ == "__main__": main()
