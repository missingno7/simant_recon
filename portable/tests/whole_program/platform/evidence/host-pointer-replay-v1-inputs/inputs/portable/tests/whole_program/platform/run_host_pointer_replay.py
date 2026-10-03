"""Verify replay pointer events round-trip through SDL logical presentation."""
from pathlib import Path
import hashlib, json, subprocess

ROOT = Path(__file__).resolve().parents[4]

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    out = ROOT / 'build/workers/whole_program/host-pointer-replay-receipt-v1'
    report = ROOT / 'portable/tests/whole_program/platform/evidence/host-pointer-replay-v1.json'
    if out.exists() or report.exists():
        raise ValueError('write-once output already exists')
    out.mkdir(parents=True)
    compiler = Path('C:/msys64/mingw64/bin/gcc.exe')
    sdk = ROOT / 'build/sdl3-sdk/SDL3-3.4.16/x86_64-w64-mingw32'
    inputs = [ROOT / name for name in (
        'portable/tests/whole_program/platform/host_pointer_replay_test.c',
        'portable/tests/whole_program/platform/run_host_pointer_replay.py',
        'portable/whole_program/platform/sdl3/host.c',
        'portable/whole_program/platform/sdl3/host_modes.h', 'portable/platform/host.h')]
    before = {p.relative_to(ROOT).as_posix(): sha(p) for p in inputs}
    command = [str(compiler), '-std=c11', '-Wall', '-Wextra', '-Werror', '-Wpedantic',
        '-I', str(ROOT), '-I', str(sdk / 'include'), str(inputs[0]), str(inputs[2]),
        str(sdk / 'lib/libSDL3.dll.a'), '-o', str(out / 'test.exe')]
    compiled = subprocess.run(command, capture_output=True, text=True)
    import shutil
    shutil.copyfile(sdk / 'bin/SDL3.dll', out / 'SDL3.dll')
    run = subprocess.run([str(out / 'test.exe')], capture_output=True, text=True, timeout=10) if compiled.returncode == 0 else None
    changed = [p.relative_to(ROOT).as_posix() for p in inputs if sha(p) != before[p.relative_to(ROOT).as_posix()]]
    passed = compiled.returncode == 0 and run.returncode == 0 and not changed
    receipt = {'schema': 'simant-host-pointer-replay-v1', 'passed': passed,
        'claim': 'Six pointer transitions round-trip through actual SDL event polling at 640x350 and 640x480; invalid kind and button are rejected. No game-state or DOS equivalence claim.',
        'inputs': before, 'changed_inputs': changed, 'command': command,
        'compiler_sha256': sha(compiler), 'sdl3_dll_sha256': sha(sdk / 'bin/SDL3.dll'),
        'compile_output': compiled.stdout + compiled.stderr,
        'run_output': run.stdout + run.stderr if run else None,
        'executable_sha256': sha(out / 'test.exe') if run else None}
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({'passed': passed, 'changed_inputs': changed}))
    return int(not passed)

if __name__ == '__main__':
    raise SystemExit(main())
