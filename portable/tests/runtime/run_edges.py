"""Ordinary SDL input replays across window and map edges, with read-only traces."""
from pathlib import Path
import argparse
import json
import os
import shutil
import signal
import subprocess
import sys
import run as runtime

PROJECT = Path(__file__).resolve().parents[3]
FIXTURES = Path(__file__).resolve().parent

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--case', choices=['window', 'left', 'map'], required=True)
    parser.add_argument('--gdb', default='C:/msys64/mingw64/bin/gdb.exe')
    args = parser.parse_args()
    report = json.loads(args.report.read_text())
    if not report.get('passed') or runtime.mismatched_inputs(PROJECT, report['input_pins']):
        raise ValueError('successful current build required')
    executable = Path(report['executable']['path'])
    if runtime.sha(executable) != report['executable']['sha256']:
        raise ValueError('executable hash changed')
    sys.path.insert(0, str(PROJECT / 'tools'))
    from workspace import prepare_output
    out = args.out.resolve()
    prepare_output(out, PROJECT / 'build/current/edges')
    script = FIXTURES / {'window':'window-edges.txt', 'left':'window-left.txt', 'map':'map-edges.txt'}[args.case]
    trace = FIXTURES / 'edges_trace.py'
    assets = out / 'a'
    shutil.copytree(args.report.resolve().parent / 'runtime-assets', assets)
    before = runtime.files(assets)
    commands = out / 'gdb.txt'
    commands.write_text('set pagination off\nset confirm off\nset auto-solib-add off\n'
        'python exec(compile(open(' + repr(str(trace)) + ').read(), ' + repr(str(trace))
        + ", 'exec'))\nrun\n")
    command = [args.gdb, '--batch', '-q', '-x', str(commands), '--args', str(executable),
        '--headless', '--smoke-ms', '38000' if args.case == 'map' else '22000', '--frame', str(out / 'frame.bmp'),
        '--assets', str(assets), '--seed', '1', '--input-script', str(script)]
    process = subprocess.Popen(command, cwd=PROJECT, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, env=dict(os.environ, SIMANT_TRACE_OUT=str(out / 'events.jsonl')))
    timeout = False
    try:
        stdout, stderr = process.communicate(timeout=90)
    except subprocess.TimeoutExpired:
        timeout = True
        # Windows tree enumeration may be denied in the worker sandbox. The
        # read-only debugger records the exact inferior PID from this launch.
        for line in (out / 'events.jsonl').read_text().splitlines():
            event = json.loads(line)
            if event['event'] == 'start':
                try:
                    os.kill(event['pid'], signal.SIGTERM)
                except OSError:
                    pass
        process.kill()
        stdout, stderr = process.communicate(timeout=10)
    (out / 'stdout.txt').write_bytes(stdout)
    (out / 'stderr.txt').write_bytes(stderr)
    events = [json.loads(line) for line in (out / 'events.jsonl').read_text().splitlines()]
    exits = [e for e in events if e['event'] == 'exit']
    actual = [l for l in stderr.decode(errors='replace').splitlines()
              if l.startswith(('Replay SDL key ', 'Replay SDL pointer '))]
    rectangles = [e['rectangle'] for e in events if e['event'] == 'window-return']
    frame = runtime.frame_receipt(out / 'frame.bmp')
    checks = {
        'normal_exit': not timeout and process.returncode == 0 and len(exits) == 1 and exits[0]['code'] == 0,
        'all_inputs_delivered': actual == runtime.expected_replay(script),
        'no_fault': not any(e['event'] in ('abort', 'signal', 'trace-error') for e in events),
        'meaningful_frame': bool(frame and frame['valid']),
        'assets_unchanged': before == runtime.files(assets),
        'current_inputs': not runtime.mismatched_inputs(PROJECT, report['input_pins']),
    }
    if args.case == 'window':
        checks['exterior_right_and_bottom_observed'] = any(r[2] > 640 and r[3] > 480 for r in rectangles)
        checks['exterior_tile_calls_observed'] = bool(exits and exits[0]['counts']['tile_exterior'])
    elif args.case == 'left':
        checks['exterior_left_observed'] = any(r[0] < 0 for r in rectangles)
        checks['exterior_tile_calls_observed'] = bool(exits and exits[0]['counts']['tile_exterior'])
    else:
        checks['map_scrolled'] = bool(exits and len(exits[0]['origins']) >= 3)
        checks['canonical_map_edge_observed'] = bool(exits and exits[0]['map_edges'])
        checks['sprite_row_offset_observed'] = bool(exits and exits[0]['counts']['sprite_offset'])
    receipt = {'passed': all(checks.values()), 'case': args.case, 'checks': checks,
        'command': command, 'timeout': timeout, 'executable_sha256': runtime.sha(executable),
        'script_sha256': runtime.sha(script), 'trace_sha256': runtime.sha(trace),
        'events_sha256': runtime.sha(out / 'events.jsonl'),
        'exit': exits, 'rectangles': rectangles, 'frame': frame}
    (out / 'report.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({'passed': receipt['passed'], 'checks': checks, 'exit': exits}))
    return int(not receipt['passed'])

if __name__ == '__main__':
    raise SystemExit(main())
