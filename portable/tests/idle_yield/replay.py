"""Run identical tick scripts twice, comparing bounded per-step state/frame traces."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    build, out = args.build.resolve(), args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    script = out/'ticks.txt'
    script.write_text('# clock: bios-ticks\n'
                      '91 down Return\n92 up Return\n'
                      '127 down Return\n128 up Return\n'
                      '164 down Return\n165 up Return\n'
                      '182 move 370 165\n186 mouse-down Left 370 165\n'
                      '190 mouse-up Left 370 165\n218 move 240 200\n')
    commands = out/'trace.gdb'
    commands.write_text('set pagination off\nset confirm off\nset auto-solib-add off\n'
                        'python exec(compile(open('+repr(str(HERE/'replay_trace.py'))+').read(), "trace", "exec"))\nrun\n')
    traces = []
    for i in (1, 2):
        assets = out/f'a{i}'
        shutil.copytree(build/'runtime-assets', assets)
        trace = out/f'trace{i}.jsonl'
        command = ['C:/msys64/mingw64/bin/gdb.exe', '--batch', '-q', '-x', str(commands), '--args',
                   str(build/'simant-canonical.exe'), '--headless', '--deterministic', '--seed', '1',
                   '--assets', str(assets), '--input-script', str(script), '--smoke-ms', '21000']
        with (out/f'run{i}.log').open('w') as log:
            run = subprocess.run(command, cwd=ROOT, env=dict(os.environ, SIMANT_IDLE_TRACE=str(trace)),
                                 stdout=log, stderr=log, timeout=180)
        assert run.returncode == 0
        rows = [json.loads(line) for line in trace.read_text().splitlines()]
        assert not any(r['kind']=='error' for r in rows), rows[:10]
        assert sum(r['kind']=='step' for r in rows) >= 20
        assert 'Source-main smoke frame captured;' in (out/f'run{i}.log').read_text()
        traces.append(rows)
    result = dict(equal=traces[0]==traces[1], steps=sum(r['kind']=='step' for r in traces[0]),
                  frames=sum(r['kind']=='frame' for r in traces[0]),
                  sha256=[hashlib.sha256((out/f'trace{i}.jsonl').read_bytes()).hexdigest() for i in (1,2)],
                  scope='maps, life arrays, ant lists, listed scalar/audio fields, indexed frame and palette; no pointer state')
    (out/'report.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result))
    return int(not result['equal'])

if __name__ == '__main__':
    raise SystemExit(main())
