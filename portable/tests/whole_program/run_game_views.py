"""Test centrally generated cleanup and clip setup against native single owners."""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'portable/tools'))
from whole_program import function_heads
from portable.whole_program.conversions.game_view_state import load_plan, adapt


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out', required=True)
    out = (ROOT / ap.parse_args().out).resolve()
    if out.exists() or not out.is_relative_to(ROOT / 'build/workers'):
        raise ValueError('new scratch output required')
    plan = load_plan()
    sources = [('root_m00F8.c', 'win_YardClosed'), ('root_m0250.c', 'f_0250_5058')]
    gen = ROOT / 'build/workers/whole_program/generated'
    inputs = [Path(__file__), Path(__file__).with_name('game_views_test.c'),
        ROOT / 'portable/whole_program/state/game_views.c',
        ROOT / 'portable/whole_program/state/game_views.h',
        ROOT / 'portable/whole_program/conversions/game_view_state.py',
        ROOT / 'portable/research/game_view_state_v1.json',
        ROOT / 'portable/whole_program/platform/handles.c',
        ROOT / 'portable/whole_program/platform/handles.h']
    bodies = []
    for rel, name in sources:
        path = gen / rel
        text = path.read_text()
        heads = [h for h in function_heads(text) if h['name'] == name]
        if len(heads) != 1 or 'native_game_fd_50F6_' not in text:
            raise ValueError(f'central game-view conversion missing: {rel}')
        bodies.append(text[heads[0]['start']:heads[0]['end']])
        inputs.append(path)
    # A changed declaration must reject instead of silently leaving a second owner.
    original = (ROOT / 'src/root/m00F8.c').read_text()
    try:
        adapt(original.replace('extern Handle far fd_50F6_10DA;',
                               'extern Handle far fd_50F6_10DA[2];'), 'src/root/m00F8.c', plan)
    except ValueError:
        pass
    else:
        raise ValueError('declaration-drift negative failed')
    before = {p.relative_to(ROOT).as_posix(): sha(p) for p in inputs}
    out.mkdir(parents=True)
    (out / 'game_view_bodies.inc').write_text('\n'.join(bodies))
    compiler = Path('C:/msys64/mingw64/bin/gcc.exe')
    exe = out / 'game_views.exe'
    command = [str(compiler), '-std=c11', '-Wall', '-Wextra', '-Werror',
        '-I', str(ROOT), '-I', str(out), str(inputs[1]), str(inputs[2]),
        str(ROOT / 'portable/whole_program/platform/handles.c'), '-o', str(exe)]
    built = subprocess.run(command, capture_output=True, text=True)
    (out / 'compile.txt').write_text(built.stdout + built.stderr)
    if built.returncode: raise RuntimeError(built.stderr)
    ran = subprocess.run([str(exe)], capture_output=True, text=True, timeout=15)
    if ran.returncode: raise RuntimeError(f'{ran.returncode}: {ran.stdout}{ran.stderr}')
    if before != {p.relative_to(ROOT).as_posix(): sha(p) for p in inputs}:
        raise ValueError('inputs changed during control')
    report = {'schema': 'simant-native-game-view-control-v1', 'status': 'PASS',
        'claim': 'actual centrally converted source bodies with real native handle manager and controlled animation/window callbacks',
        'inputs': before, 'compiler_sha256': sha(compiler),
        'stdout': ran.stdout, 'declaration_drift_negative': 'REJECTED',
        'historical_claim': False, 'full_game_claim': False}
    (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(ran.stdout)


if __name__ == '__main__': main()
