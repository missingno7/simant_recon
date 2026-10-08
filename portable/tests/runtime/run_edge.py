"""Replay Quick Game edge scrolling and the seed-0 human freeze recording."""
from pathlib import Path
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import run as runtime

PROJECT = Path(__file__).resolve().parents[3]
FIXTURES = Path(__file__).resolve().parent


def run_case(args, build, executable, gdb, out, case):
    target = out / case
    target.mkdir()
    assets = target / 'a'
    shutil.copytree(build / 'runtime-assets', assets)
    script = FIXTURES / ('edge-user.txt' if case == 'user' else 'edge-scroll.txt')
    trace = FIXTURES / 'edge_trace.py'
    commands = target / 'gdb.txt'
    commands.write_text('set pagination off\nset confirm off\nset auto-solib-add off\n'
                        'python exec(compile(open(' + repr(str(trace)) + ').read(), '
                        + repr(str(trace)) + ", 'exec'))\nrun\n")
    command = [str(gdb), '--batch', '-q', '-x', str(commands), '--args', str(executable),
               '--headless', '--smoke-ms', '20000' if case == 'user' else '37000',
               '--frame', str(target / 'frame.bmp'), '--assets', str(assets),
               '--seed', '0', '--input-script', str(script)]
    if args.deterministic:
        command.append('--deterministic')
    process = subprocess.Popen(command, cwd=args.project,
                               env=dict(os.environ, SIMANT_TRACE_OUT=str(target / 'events.jsonl')),
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    timed_out = False
    try:
        stdout, stderr = process.communicate(timeout=70)
    except subprocess.TimeoutExpired:
        timed_out = True
        # GDB's Windows debug object kills its inferior on debugger exit.
        process.kill()
        stdout, stderr = process.communicate(timeout=10)
    (target / 'stdout.txt').write_bytes(stdout)
    (target / 'stderr.txt').write_bytes(stderr)
    log = stderr.decode(errors='replace')
    actual = [line for line in log.splitlines()
              if line.startswith(('Replay SDL key ', 'Replay SDL pointer '))]
    event_path = target / 'events.jsonl'
    events = [json.loads(line) for line in event_path.read_text().splitlines()] if event_path.exists() else []
    frames = [event for event in events if event['event'] == 'present']
    scroll_frames = [event for event in frames if event['scroll_loop']]
    returns = [event for event in events if event['event'] == 'scroll-return']
    exits = [event for event in events if event['event'] == 'inferior-exit']
    loops = re.findall(r'outer game loop count=(\d+);', log)
    frame = runtime.frame_receipt(target / 'frame.bmp')
    checks = {
        'normal_smoke_exit': not timed_out and process.returncode == 0
            and len(exits) == 1 and exits[0].get('exit_code') == 0
            and 'Source-main smoke frame captured;' in log,
        'all_fixture_events_injected': actual == runtime.expected_replay(script),
        'continued_frames_inside_source_scroll_loop': len(scroll_frames) >= 2,
        'meaningful_VGA_frame_and_positive_outer_loops': bool(frame and frame['valid'])
            and bool(loops) and int(loops[-1]) > 0,
        'no_fault_or_unsafe_presentation': not any(event['event'] in
            ('trace-error', 'signal', 'unsafe-presentation') for event in events),
        'disposable_assets_unchanged': runtime.files(assets) == runtime.files(build / 'runtime-assets'),
    }
    if case == 'edges':
        positions = ([0, 200], [636, 200], [240, 0], [374, 476])
        checks['frames_at_each_held_screen_edge'] = all(
            sum(event['mouse'] == position for event in scroll_frames) >= 2 for position in positions)
        checks['scroll_returns_after_moving_away'] = sum(
            event['mouse'] == [240, 200] for event in returns) >= 4
        before = [event['outer_loops'] for event in frames if event['elapsed_ns'] < 20000000000]
        after = [event['outer_loops'] for event in frames if event['elapsed_ns'] > 34500000000]
        checks['outer_loop_resumes_after_holds'] = bool(before and after) and max(after) > max(before)
        # The DOS loop has no timer wait; native presentation paces each
        # redraw to one 59.94 Hz VGA refresh instead of host speed.
        held = [event for event in returns if event.get('held_seconds', 0) > 1]
        checks['scroll_steps_paced_by_VGA_refresh'] = len(held) >= 4 and all(
            event['steps'] <= 61 * event['held_seconds'] + 2 for event in held)
    else:
        checks['user_final_move_delivered_with_INT33_bounds'] = bool(frames) and frames[-1]['mouse'] == [374, 476]
    result = {'case': case, 'passed': all(checks.values()), 'checks': checks,
              'command': command, 'timed_out': timed_out, 'exit_code': process.returncode,
              'fixture_sha256': runtime.sha(script), 'trace_sha256': runtime.sha(trace),
              'events_sha256': runtime.sha(event_path) if event_path.exists() else None,
              'presentations': len(frames), 'scroll_presentations': len(scroll_frames),
              'scroll_returns': len(returns), 'outer_loops': int(loops[-1]) if loops else None,
              'frame': frame}
    (target / 'report.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'case': case, 'passed': result['passed'],
                      'failed_checks': [name for name, ok in checks.items() if not ok]}), flush=True)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--out', type=Path)
    parser.add_argument('--project', type=Path, default=PROJECT)
    parser.add_argument('--case', choices=('user', 'edges'))
    parser.add_argument('--deterministic', action='store_true')
    parser.add_argument('--gdb', default='C:/msys64/mingw64/bin/gdb.exe')
    args = parser.parse_args()
    args.project = args.project.resolve()
    report_path = args.report.resolve()
    report_hash = runtime.sha(report_path)
    report = json.loads(report_path.read_text())
    if (report.get('schema') != 'canonical-native-complete-attempt-v1'
            or not report.get('passed') or not report.get('input_stability', {}).get('at_end')):
        raise ValueError('successful stable current native build required')
    pins = report['input_pins']
    if runtime.mismatched_inputs(args.project, pins):
        raise ValueError('build inputs changed; rebuild')
    build = report_path.parent
    executable = Path(report['executable']['path']).resolve()
    if executable.parent != build or runtime.sha(executable) != report['executable']['sha256']:
        raise ValueError('executable differs from build report')
    gdb = Path(shutil.which(args.gdb) or args.gdb).resolve()
    if not gdb.is_file():
        raise ValueError('GDB with Python support required')
    platform = json.loads((args.project / 'portable/platform.json').read_text())
    resources = runtime.files(build / 'runtime-assets')
    expected = {name: pins['assets/' + name] for name in platform['runtime_assets']}
    expected.update({item['path']: item['sha256'] for item in platform.get('generated_runtime_resources', [])})
    if resources != expected:
        raise ValueError('build resources differ from pinned manifest')
    fonts = runtime.files(build / 'runtime-bios-fonts')
    original_assets = runtime.files(args.project / 'assets')
    fixture_pins = {str(path): runtime.sha(path) for path in
                    (Path(__file__), FIXTURES / 'edge_trace.py', FIXTURES / 'edge-user.txt',
                     FIXTURES / 'edge-scroll.txt', FIXTURES / 'run.py', gdb, build / 'SDL3.dll')}
    out = (args.out or args.project / 'build/current/edge').absolute()
    sys.path.insert(0, str(PROJECT / 'tools'))
    from workspace import prepare_output
    prepare_output(out, args.project / 'build/current/edge', args.project)
    results = [run_case(args, build, executable, gdb, out, case)
               for case in ((args.case,) if args.case else ('user', 'edges'))]
    checks = {
        'all_cases_passed': all(result['passed'] for result in results),
        'current_inputs_unchanged': not runtime.mismatched_inputs(args.project, pins),
        'build_report_unchanged': runtime.sha(report_path) == report_hash,
        'executable_unchanged': runtime.sha(executable) == report['executable']['sha256'],
        'build_resources_unchanged': runtime.files(build / 'runtime-assets') == resources,
        'BIOS_fonts_unchanged': runtime.files(build / 'runtime-bios-fonts') == fonts,
        'original_assets_unchanged': runtime.files(args.project / 'assets') == original_assets,
        'fixtures_and_support_unchanged': all(runtime.sha(Path(path)) == pin for path, pin in fixture_pins.items()),
    }
    receipt = {'schema': 'canonical-native-edge-scroll-replay-v1', 'passed': all(checks.values()),
               'checks': checks, 'deterministic': args.deterministic, 'runs': results,
               'build_report_sha256': report_hash, 'executable_sha256': report['executable']['sha256'],
               'fixture_pins': fixture_pins,
               'scope': 'Quick Game native scroll progress, frames while input is held, '
                        'source return after moving away, smoke exit and exact human replay. '
                        'No DOS pixel equality, CPU interrupt interleaving or simulation equality claim.'}
    (out / 'report.json').write_text(json.dumps(receipt, indent=2) + '\n')
    return int(not receipt['passed'])


if __name__ == '__main__':
    raise SystemExit(main())
