"""Bounded original-main execution; a startup frame is not a gameplay proof."""
from pathlib import Path
import argparse
import hashlib
import json
import re
import subprocess
import time

ROOT = Path(__file__).resolve().parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def asset_identities(directory):
    return {p.name: sha(p) for p in sorted(directory.iterdir()) if p.is_file()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--application', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--milliseconds', type=int, default=5000)
    parser.add_argument('--seed', type=int, default=1)
    parser.add_argument('--vga', action='store_true')
    parser.add_argument('--input-script', type=Path)
    args = parser.parse_args()
    executable = (ROOT / args.application).resolve()
    output = (ROOT / args.out).resolve()
    if output.exists() or not output.is_relative_to(ROOT / 'build/workers'):
        raise ValueError('a new scratch output directory is required')
    if not 1 <= args.milliseconds <= 60000:
        raise ValueError('startup deadline must be within 1..60000 ms')
    link_report = executable.parent / 'report.json'
    linked = json.loads(link_report.read_text())
    if not linked['passed'] or linked['executable_sha256'] != sha(executable):
        raise ValueError('a verified whole-application executable is required')
    originals = asset_identities(ROOT / 'assets')
    runtime_directory = executable.parent / 'runtime-assets'
    if not runtime_directory.is_dir():
        runtime_directory = executable.parent
    runtime = asset_identities(runtime_directory)
    output.mkdir(parents=True)
    command = [str(executable), '--headless', '--smoke-ms', str(args.milliseconds),
               '--frame', str(output / 'frame.bmp'), '--seed', str(args.seed)]
    if args.vga:
        command.append('/dV')
    if args.input_script:
        replay = (ROOT / args.input_script).resolve()
        command.extend(['--input-script', str(replay)])
    began = time.monotonic()
    try:
        result = subprocess.run(command, cwd=ROOT, capture_output=True,
                                timeout=args.milliseconds / 1000 + 10)
        stdout, stderr, code, timed_out = result.stdout, result.stderr, result.returncode, False
    except subprocess.TimeoutExpired as exc:
        stdout, stderr, code, timed_out = exc.stdout or b'', exc.stderr or b'', None, True
    (output / 'stdout.txt').write_bytes(stdout)
    (output / 'stderr.txt').write_bytes(stderr)
    after_runtime = asset_identities(runtime_directory)
    unchanged = originals == asset_identities(ROOT / 'assets')
    frame = output / 'frame.bmp'
    loop_count = re.search(rb'outer game loop count=(-?\d+)', stderr)
    passed = code == 0 and frame.is_file() and unchanged and b'Native video driver: dummy' in stderr
    report = {
        'schema': 'simant-whole-source-main-startup-v1', 'passed': passed,
        'scope': 'Original main through a presented startup frame; no completed NewGame or full gameplay claim',
        'command': command, 'exit_code': code, 'timed_out': timed_out,
        'elapsed_seconds': time.monotonic() - began,
        'inputs': {executable.relative_to(ROOT).as_posix(): sha(executable),
                   link_report.relative_to(ROOT).as_posix(): sha(link_report),
                   Path(__file__).relative_to(ROOT).as_posix(): sha(Path(__file__))},
        'original_assets_unchanged': unchanged,
        'runtime_assets_directory': runtime_directory.relative_to(ROOT).as_posix(),
        'runtime_asset_changes': {name: {'before': runtime.get(name), 'after': after_runtime.get(name)}
                                  for name in sorted(set(runtime) | set(after_runtime))
                                  if runtime.get(name) != after_runtime.get(name)},
        'frame_sha256': sha(frame) if frame.is_file() else None,
        'original_outer_loop_count': int(loop_count[1]) if loop_count else None,
        'input_script': {'path': str(replay), 'sha256': sha(replay)} if args.input_script else None,
    }
    (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'passed': passed, 'exit_code': code, 'timed_out': timed_out,
                      'original_assets_unchanged': unchanged}))
    print(stderr.decode(errors='replace').encode('ascii', 'backslashreplace').decode())
    return int(not passed)


if __name__ == '__main__':
    raise SystemExit(main())
