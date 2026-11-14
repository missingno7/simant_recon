"""Pure machine-rule vectors, paced canonical BIOS polling and spinning control."""
from pathlib import Path
import argparse
import json
import os
import subprocess

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--sdk', type=Path, default=ROOT/'build/deps/sdl3-sdk/SDL3-3.4.16/x86_64-w64-mingw32')
    args = parser.parse_args()
    out, sdk = args.out.resolve(), args.sdk.resolve()
    out.mkdir(parents=True, exist_ok=False)
    cc = 'C:/msys64/mingw64/bin/gcc.exe'
    base = [cc, '-std=c11', '-O0', '-g', '-Wall', '-Wextra', '-Werror', '-I'+str(ROOT)]
    common = [str(ROOT/'portable/whole_program/platform'/f) for f in ('input_time.c', 'pit_clock.c')]
    commands = [base + common + [str(HERE/'rule.c'), '-o', str(out/'rule.exe')],
                base + ['-I'+str(sdk/'include')] + common +
                [str(ROOT/'portable/whole_program/platform/sdl3'/f) for f in ('input_time_host.c', 'host.c')] +
                [str(HERE/'poll.c'), '-L'+str(sdk/'lib'), '-lSDL3', '-o', str(out/'poll.exe')]]
    env = dict(os.environ, PATH=str(sdk/'bin')+os.pathsep+os.environ.get('PATH',''))
    for command in commands:
        subprocess.run(command, check=True, timeout=60)
    results = []
    for command in ([str(out/'rule.exe')], [str(out/'poll.exe')], [str(out/'poll.exe'), '--spin']):
        run = subprocess.run(command, env=env, capture_output=True, text=True, timeout=15)
        results.append(dict(command=command, code=run.returncode, stdout=run.stdout, stderr=run.stderr))
        print(run.stdout+run.stderr, end='', flush=True)
    (out/'report.json').write_text(json.dumps(dict(build=commands, results=results), indent=2)+'\n')
    return int(any(r['code'] for r in results))

if __name__ == '__main__':
    raise SystemExit(main())
