"""Check the centrally converted clip stack against real native handles."""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'portable/tools'))
from whole_program import function_heads
from portable.whole_program.conversions.clip_stack_native import NEW


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    out = (ROOT / args.out).resolve()
    if out.exists() or not out.is_relative_to(ROOT / 'build/workers'):
        raise ValueError('new scratch directory required')
    generated = ROOT / 'build/workers/whole_program/generated/root_m1E57.c'
    source = generated.read_text()
    names = {'clip_Push', 'clip_Pop', 'f_1E57_0009'}
    heads = [h for h in function_heads(source) if h['name'] in names]
    if len(heads) != 3:
        raise ValueError('clip stack function membership changed')
    bodies = '\n\n'.join(source[h['start']:h['end']] for h in heads)
    anchor = NEW.replace('long', 'int32_t')
    if bodies.count(anchor) != 1:
        raise ValueError('central native header conversion is absent')
    inputs = [generated, Path(__file__), Path(__file__).with_name('clip_stack_native_test.c'),
        ROOT / 'portable/whole_program/platform/handles.c',
        ROOT / 'portable/whole_program/platform/handles.h',
        ROOT / 'portable/whole_program/window_source_rects.h',
        ROOT / 'portable/whole_program/conversions/clip_stack_native.py']
    before = {p.relative_to(ROOT).as_posix(): sha(p) for p in inputs}
    out.mkdir(parents=True)
    results = {}
    compiler = Path('C:/msys64/mingw64/bin/gcc.exe')
    for kind in ('native', 'old_header'):
        work = out / kind
        work.mkdir()
        test_bodies = bodies if kind == 'native' else bodies.replace(anchor,
            'f_171C_1A9E(size + 8L, 1, "clip_Push")', 1)
        (work / 'clip_stack_bodies.inc').write_text(test_bodies)
        exe = work / 'clip_stack.exe'
        command = [str(compiler), '-std=c11', '-g', '-Wall', '-Wextra', '-Werror',
            '-I', str(ROOT), '-I', str(work),
            str(Path(__file__).with_name('clip_stack_native_test.c')),
            str(ROOT / 'portable/whole_program/platform/handles.c'), '-o', str(exe)]
        compiled = subprocess.run(command, capture_output=True, text=True)
        (work / 'compile.txt').write_text(compiled.stdout + compiled.stderr)
        if compiled.returncode:
            raise RuntimeError(compiled.stderr)
        try:
            ran = subprocess.run([str(exe)] + (['old'] if kind == 'old_header' else []),
                capture_output=True, text=True, timeout=20)
        except subprocess.TimeoutExpired as failure:
            raise RuntimeError(f'clip control timed out: {failure.stderr!r}') from failure
        expected = 0 if kind == 'native' else 42
        if ran.returncode != expected:
            raise RuntimeError(f'{kind}: exit {ran.returncode}: {ran.stdout}{ran.stderr}')
        results[kind] = {'exit': ran.returncode, 'stdout': ran.stdout,
            'source_sha256': sha(work / 'clip_stack_bodies.inc')}
    if before != {p.relative_to(ROOT).as_posix(): sha(p) for p in inputs}:
        raise ValueError('clip test inputs changed')
    report = {'schema': 'simant-native-clip-stack-width-v1', 'status': 'PASS',
        'claim': 'actual converted Push/Pop bodies preserve nested clip payloads using real native handle APIs; original eight-byte header fails before an out-of-bounds write',
        'inputs': before, 'compiler_sha256': sha(compiler), 'results': results,
        'directed_pushes': 48, 'directed_pops': 48,
        'historical_claim': False}
    (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(results, indent=2))


if __name__ == '__main__':
    main()
