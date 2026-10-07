"""Compile actual input services and source-derived ASM cells against fixed hardware controls."""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
SERVICES = ('m1b73_queue_runtime.c', 'm1b73_events.c', 'm1b73_mouse.c',
            'm1b73_mouse_state.c', 'm1b73_queues.c', 'm1b73_queue_ops.c',
            'm1b73_main_input.c', 'm1b73_timer_view.c', 'input_time.c',
            'sdl3/input_time_host.c', 'pit_clock.c')

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build', type=Path, default=ROOT/'build/current/portable')
    p.add_argument('--out', type=Path, default=ROOT/'build/current/tests/input-irq')
    p.add_argument('--cc', default='C:/msys64/mingw64/bin/gcc.exe')
    a = p.parse_args()
    build, out = a.build.resolve(), a.out.resolve()
    report = json.loads((build/'report.json').read_text())
    if not report.get('passed'):
        raise ValueError('successful native build required for source-derived ASM owners')
    sources = [HERE/'fixture.c', build/'canonical_mouse_data.c'] + [
        ROOT/'portable/whole_program/platform'/name for name in SERVICES]
    for name in SERVICES:
        path = ROOT/'portable/whole_program/platform'/name
        rel = path.relative_to(ROOT).as_posix()
        if hashlib.sha256(path.read_bytes()).hexdigest() != report['input_pins'][rel]:
            raise ValueError('rebuild changed service: '+rel)
    sys.path.insert(0, str(ROOT/'tools'))
    from workspace import prepare_output
    prepare_output(out, ROOT/'build/current/tests/input-irq', ROOT)
    binary = out/'input-irq.exe'
    command = [a.cc, '-std=c11', '-Wall', '-Wextra', '-Werror',
               '-I'+str(ROOT), '-I'+str(build/'include'), '-I'+str(build),
               *map(str,sources), '-o', str(binary)]
    compile_result = subprocess.run(command, capture_output=True, text=True, timeout=60)
    (out/'compile.txt').write_text(compile_result.stdout+compile_result.stderr)
    if compile_result.returncode:
        print(compile_result.stderr)
        return compile_result.returncode
    run = subprocess.run([str(binary)], capture_output=True, text=True, timeout=15)
    (out/'run.txt').write_text(run.stdout+run.stderr)
    matrix = subprocess.run([str(binary),'--matrix'], capture_output=True, text=True, timeout=15)
    expected = json.loads((HERE/'oracle-matrix.json').read_text())
    raw = matrix.stdout.encode('utf-8')
    matrix_pass = (matrix.returncode == 0 and len(matrix.stdout.splitlines()) == expected['rows']
                   and len(raw) == expected['csv_bytes']
                   and hashlib.sha256(raw).hexdigest() == expected['csv_sha256']
                   and hashlib.sha256((ROOT/expected['source']).read_bytes()).hexdigest() == expected['source_sha256'])
    (out/'matrix.csv').write_bytes(raw)
    receipt = {'passed':run.returncode==0 and matrix_pass, 'command':command, 'exit_code':run.returncode,
               'output':run.stdout+run.stderr,
               'canonical_instruction_matrix':{'passed':matrix_pass,'rows':expected['rows'],
                   'sha256':hashlib.sha256(raw).hexdigest(),'expected_sha256':expected['csv_sha256']},
               'source_pins':{str(s):hashlib.sha256(s.read_bytes()).hexdigest() for s in sources},
               'scope':'Actual native IRQ projection, all five register words and ring headers; controlled hardware and interrupted register words. SDL/cycle interleavings are separate observations.'}
    (out/'report.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(run.stdout+run.stderr)
    print('Canonical 0747 matrix:', matrix_pass, expected['rows'], 'steps')
    return int(not receipt['passed'])

if __name__ == '__main__':
    raise SystemExit(main())
