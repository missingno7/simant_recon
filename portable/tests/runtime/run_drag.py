"""Replay held window/triangle tracking and exterior SDL motion under GDB."""
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--out', type=Path)
    parser.add_argument('--project', type=Path, default=PROJECT)
    parser.add_argument('--repeat', type=int, default=1)
    parser.add_argument('--gdb', default='C:/msys64/mingw64/bin/gdb.exe')
    args = parser.parse_args()
    if not 1 <= args.repeat <= 5:
        parser.error('--repeat must be 1..5')
    project = args.project.resolve()
    report_path = args.report.resolve()
    report_hash = runtime.sha(report_path)
    report = json.loads(report_path.read_text())
    if (report.get('schema') != 'canonical-native-complete-attempt-v1'
            or not report.get('passed') or not report.get('input_stability', {}).get('at_end')):
        raise ValueError('successful stable current native build required')
    pins = report['input_pins']
    for path in ('src/program.json', 'portable/platform.json', 'portable/build.py',
                 'portable/whole_program/application.c',
                 'portable/whole_program/platform/m1b73_mouse.c'):
        if path not in pins:
            raise ValueError('build input pin missing: ' + path)
    if runtime.mismatched_inputs(project, pins):
        raise ValueError('build inputs changed; rebuild')
    build = report_path.parent
    executable = Path(report['executable']['path']).resolve()
    if executable.parent != build or runtime.sha(executable) != report['executable']['sha256']:
        raise ValueError('executable differs from build report')
    gdb = Path(shutil.which(args.gdb) or args.gdb).resolve()
    if not gdb.is_file():
        raise ValueError('GDB with Python support required')
    platform = json.loads((project / 'portable/platform.json').read_text())
    resources = runtime.files(build / 'runtime-assets')
    expected = {name: pins['assets/' + name] for name in platform['runtime_assets']}
    expected.update({item['path']: item['sha256'] for item in platform.get('generated_runtime_resources', [])})
    if resources != expected:
        raise ValueError('build resources differ from pinned manifest')
    fonts = runtime.files(build / 'runtime-bios-fonts')
    if fonts != {name.removeprefix('portable/runtime/bios-reference/'): value
                 for name, value in pins.items() if name.startswith('portable/runtime/bios-reference/')}:
        raise ValueError('build BIOS fonts differ from pinned inputs')
    original_assets = runtime.files(project / 'assets')
    script, trace = FIXTURES / 'drag-game.txt', FIXTURES / 'drag_trace.py'
    fixture_pins = {str(path): runtime.sha(path) for path in
                    (Path(__file__), script, trace, FIXTURES / 'run.py')}
    support_pins = {str(path): runtime.sha(path) for path in (gdb, build / 'SDL3.dll')}
    expected_events = runtime.expected_replay(script)
    out = (args.out or project / 'build/current/drag').absolute()
    sys.path.insert(0, str(PROJECT / 'tools'))
    from workspace import prepare_output
    prepare_output(out, project / 'build/current/drag', project)
    results = []
    for repetition in range(args.repeat):
        target = out / str(repetition + 1)
        target.mkdir()
        assets = target / 'a'
        shutil.copytree(build / 'runtime-assets', assets)
        commands = target / 'gdb.txt'
        commands.write_text('set pagination off\nset confirm off\nset auto-solib-add off\n'
                            'python exec(compile(open(' + repr(str(trace)) + ').read(), '
                            + repr(str(trace)) + ", 'exec'))\nrun\n")
        command = [str(gdb), '--batch', '-q', '-x', str(commands), '--args', str(executable),
                   '--headless', '--smoke-ms', '30000', '--frame', str(target / 'frame.bmp'),
                   '--assets', str(assets), '--seed', '1', '--input-script', str(script)]
        env = dict(os.environ, SIMANT_TRACE_OUT=str(target / 'events.jsonl'))
        process = subprocess.Popen(command, cwd=project, env=env,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        timed_out = False
        try:
            stdout, stderr = process.communicate(timeout=65)
        except subprocess.TimeoutExpired:
            timed_out = True
            process.kill()
            stdout, stderr = process.communicate(timeout=10)
        (target / 'stdout.txt').write_bytes(stdout)
        (target / 'stderr.txt').write_bytes(stderr)
        log = stderr.decode(errors='replace')
        actual = [line for line in log.splitlines()
                  if line.startswith(('Replay SDL key ', 'Replay SDL pointer '))]
        events = [json.loads(line) for line in (target / 'events.jsonl').read_text().splitlines()]
        tracks = [event for event in events if event['event'] == 'track-return']
        exits = [event for event in events if event['event'] == 'inferior-exit']
        exterior = [event for event in events if event['event'] == 'exterior-mouse-return']
        frame = runtime.frame_receipt(target / 'frame.bmp')
        loops = re.findall(r'outer game loop count=(\d+);', log)
        checks = {
            'normal_bounded_exit': not timed_out and process.returncode == 0
                and len(exits) == 1 and exits[0].get('exit_code') == 0,
            'all_fixture_events_injected': actual == expected_events and bool(expected_events),
            'window_triangle_resize_all_returned': all(any(t['kind'] == kind for t in tracks)
                for kind in ('window', 'triangle', 'resize'))
                and len(tracks) == sum(e['event'] == 'track-entry' for e in events),
            'frames_presented_during_each_held_drag': bool(tracks) and all(
                t['presentations'] >= 2 and t['active_clip_presentations'] >= 2
                and len(t['frames']) >= 2 for t in tracks),
            'exterior_motion_obeys_DOS_driver_limits': len(exterior) == 2 and
                [(e['source_x'], e['source_y']) for e in exterior] == [(270, 0), (636, 476)],
            'no_fault_or_unsafe_presentation': not any(e['event'] in
                ('signal', 'abnormal-exit', 'trace-error', 'unsafe-presentation') for e in events),
            'meaningful_VGA_frame_and_positive_outer_loops': bool(frame and frame['valid'])
                and bool(loops) and int(loops[-1]) > 0
                and 'Source-selected video profile=8 mode=12h logical=640x480' in log,
            'disposable_assets_unchanged': runtime.files(assets) == resources,
        }
        result = {'passed': all(checks.values()), 'checks': checks, 'command': command,
                  'exit_code': process.returncode, 'timed_out': timed_out,
                  'tracks': tracks, 'exterior_motion': exterior, 'frame': frame,
                  'events_sha256': runtime.sha(target / 'events.jsonl')}
        (target / 'report.json').write_text(json.dumps(result, indent=2) + '\n')
        results.append(result)
        print(json.dumps({'repetition': repetition + 1, 'passed': result['passed'],
                          'failed_checks': [key for key, ok in checks.items() if not ok]}), flush=True)
    checks = {
        'all_replays_passed': all(result['passed'] for result in results),
        'current_inputs_unchanged': not runtime.mismatched_inputs(project, pins),
        'build_report_unchanged': runtime.sha(report_path) == report_hash,
        'executable_unchanged': runtime.sha(executable) == report['executable']['sha256'],
        'build_resources_unchanged': runtime.files(build / 'runtime-assets') == resources,
        'BIOS_fonts_unchanged': runtime.files(build / 'runtime-bios-fonts') == fonts,
        'original_assets_unchanged': runtime.files(project / 'assets') == original_assets,
        'fixtures_and_support_unchanged': all(runtime.sha(Path(path)) == pin
            for path, pin in (fixture_pins | support_pins).items()),
    }
    receipt = {'schema': 'canonical-native-held-drag-replay-v1', 'passed': all(checks.values()),
               'checks': checks, 'build_report_sha256': report_hash,
               'executable_sha256': report['executable']['sha256'],
               'fixture_pins': fixture_pins, 'support_pins': support_pins, 'runs': results,
               'scope': 'Ordinary SDL replay and read-only debugger observations: frames during held '
                        'title/triangle/resize tracking, INT33 exterior coordinate limits and no fault. '
                        'Frame hashes include the cursor; no DOS pixel equality or whole-game claim.'}
    (out / 'report.json').write_text(json.dumps(receipt, indent=2) + '\n')
    return int(not receipt['passed'])


if __name__ == '__main__':
    raise SystemExit(main())
