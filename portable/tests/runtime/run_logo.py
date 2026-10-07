"""Bounded logo-click release regression against an unchanged native build.

Ordinary SDL replays and read-only GDB startup observations. A timeout is failure,
not acceptance. The old cached scan-query implementation fails center-after.
"""
from pathlib import Path
import argparse
import json
import os
import shutil
import subprocess
import sys
import run as runtime

PROJECT = Path(__file__).resolve().parents[3]
FIXTURES = Path(__file__).resolve().parent
CASES = ('center-after', 'center-during', 'center-late', 'corner',
         'right-held', 'space-held', 'repeated')


def replay(case, source):
    if case == 'center-during':
        return source.replace('5500', '3000').replace('5550', '3050').replace('5750', '3250')
    if case == 'center-late':
        return source.replace('5500', '7500').replace('5550', '7550').replace('5750', '7750')
    if case == 'corner':
        return source.replace('320 240', '120 120')
    if case == 'right-held':
        return source.replace('Left', 'Right').replace('5750', '6550')
    if case == 'space-held':
        return ('5500 down Space\n6500 up Space\n' +
                '\n'.join(source.splitlines()[5:]) + '\n')
    if case == 'repeated':
        return source.replace('# Proceed',
            '6100 mouse-down Left 340 260\n6300 mouse-up Left 340 260\n'
            '6900 mouse-down Left 320 240\n7100 mouse-up Left 320 240\n# Proceed')
    return source


def run_case(args, executable, build, out, case, gdb):
    target = out / case
    target.mkdir()
    assets = target / 'a'
    shutil.copytree(build / 'runtime-assets', assets)
    before = runtime.files(assets)
    script = target / 'input.txt'
    script.write_text(replay(case, (FIXTURES / 'logo-click.txt').read_text()))
    expected = runtime.expected_replay(script)
    trace = FIXTURES / 'logo_trace.py'
    commands = target / 'gdb.txt'
    commands.write_text('set pagination off\nset confirm off\nset auto-solib-add off\npython exec(compile(open('
                        + repr(str(trace)) + ').read(), ' + repr(str(trace)) + ", 'exec'))\nrun\n")
    command = [str(gdb), '--batch', '-q', '-x', str(commands), '--args',
               str(executable), *([] if args.visible else ['--headless']),
               '--smoke-ms', '12500', '--frame', str(target / 'frame.bmp'),
               '--assets', str(assets), '--seed', '1', '--input-script', str(script)]
    env = dict(os.environ, SIMANT_TRACE_OUT=str(target / 'events.jsonl'))
    process = subprocess.Popen(command, cwd=args.project, env=env,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    timed_out = False
    try:
        stdout, stderr = process.communicate(timeout=45)
    except subprocess.TimeoutExpired:
        timed_out = True
        # Windows terminates the debuggee when its debugger exits (the default
        # debug-object kill-on-exit policy). Use our retained process handle;
        # process-tree enumeration is not available under restricted tokens.
        process.kill()
        stdout, stderr = process.communicate(timeout=10)
    (target / 'stdout.txt').write_bytes(stdout)
    (target / 'stderr.txt').write_bytes(stderr)
    log = stderr.decode(errors='replace')
    actual = [line for line in log.splitlines()
              if line.startswith(('Replay SDL key ', 'Replay SDL pointer '))]
    event_path = target / 'events.jsonl'
    events = [json.loads(line) for line in event_path.read_text().splitlines()] if event_path.exists() else []
    waits = [event for event in events if event['event'] == 'DialogWaitInit-entry']
    returns = {event['call']: event for event in events if event['event'] == 'DialogWaitInit-return'}
    held = [event for event in waits if event['mouse_status'] & 3 or
            event['space_down'] or event['insert_down'] or event['delete_down']]
    frame = runtime.frame_receipt(target / 'frame.bmp')
    checks = {
        'bounded_exit': process.returncode == 0 and not timed_out,
        'all_replay_events_injected': actual == expected and bool(expected),
        'source_intro_returned': any(e['event'] == 'ShowIntro-return' for e in events),
        'source_registration_returned': any(e['event'] == 'CustomerIDDialog-return' for e in events),
        'every_observed_wait_returned': bool(waits) and len(returns) == len(waits),
        'returns_have_no_held_buttons_or_source_keys': bool(returns) and all(
            not (e['mouse_status'] & 3 or e['space_down'] or e['insert_down'] or e['delete_down'])
            for e in returns.values()),
        'held_wait_exercised': bool(held) if case in ('center-after', 'center-late', 'right-held', 'space-held', 'repeated') else True,
        'smoke_deadline_and_frame': 'Source-main smoke frame captured;' in log and bool(frame and frame['valid']),
        'no_trace_errors': not any(e['event'] == 'trace-error' for e in events),
        'disposable_assets_unchanged': before == runtime.files(assets),
    }
    result = {'case': case, 'passed': all(checks.values()), 'checks': checks,
              'timed_out': timed_out, 'exit_code': process.returncode, 'command': command,
              'events': events, 'injected_events': len(actual), 'expected_events': len(expected),
              'frame': frame, 'replay_sha256': runtime.sha(script)}
    (target / 'report.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'case': case, 'passed': result['passed'],
                      'failed_checks': [name for name, ok in checks.items() if not ok]}), flush=True)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--out', type=Path)
    parser.add_argument('--project', type=Path, default=PROJECT)
    parser.add_argument('--case', choices=CASES, action='append')
    parser.add_argument('--repeat', type=int, default=1)
    parser.add_argument('--visible', action='store_true')
    parser.add_argument('--gdb', default='C:/msys64/mingw64/bin/gdb.exe')
    args = parser.parse_args()
    args.project = args.project.resolve()
    if not 1 <= args.repeat <= 10:
        parser.error('--repeat must be 1..10')
    report_path = args.report.resolve()
    report_hash = runtime.sha(report_path)
    report = json.loads(report_path.read_text())
    if (report.get('schema') != 'canonical-native-complete-attempt-v1' or
            not report.get('passed') or not report.get('input_stability', {}).get('at_end')):
        raise ValueError('successful stable current native build required')
    pins = report['input_pins']
    for name in ('src/program.json', 'portable/platform.json', 'portable/build.py',
                 'portable/whole_program/application.c',
                 'portable/whole_program/platform/m1b73_main_input.c'):
        if name not in pins:
            raise ValueError('build input pin missing: ' + name)
    if runtime.mismatched_inputs(args.project, pins):
        raise ValueError('build inputs changed; rebuild')
    executable = Path(report['executable']['path']).resolve()
    build = report_path.parent
    if executable.parent != build or runtime.sha(executable) != report['executable']['sha256']:
        raise ValueError('executable differs from the supplied build report')
    gdb = Path(shutil.which(args.gdb) or args.gdb).resolve()
    if not gdb.is_file():
        raise ValueError('GDB with Python support required')
    resources, fonts = runtime.files(build / 'runtime-assets'), runtime.files(build / 'runtime-bios-fonts')
    platform = json.loads((args.project / 'portable/platform.json').read_text())
    expected_resources = {name: pins['assets/' + name] for name in platform['runtime_assets']}
    expected_resources.update({item['path']: item['sha256'] for item in platform.get('generated_runtime_resources', [])})
    if resources != expected_resources:
        raise ValueError('build resources differ from pinned manifest')
    if fonts != {name.removeprefix('portable/runtime/bios-reference/'): value
                 for name, value in pins.items() if name.startswith('portable/runtime/bios-reference/')}:
        raise ValueError('build BIOS fonts differ from pinned inputs')
    originals = runtime.files(args.project / 'assets')
    support = {str(p): runtime.sha(p) for p in (build / 'SDL3.dll', gdb)}
    fixtures = {str(p): runtime.sha(p) for p in (Path(__file__), FIXTURES / 'logo_trace.py', FIXTURES / 'logo-click.txt', FIXTURES / 'run.py')}
    out = (args.out or args.project / 'build/current/logo').absolute()
    sys.path.insert(0, str(PROJECT / 'tools'))
    from workspace import prepare_output
    prepare_output(out, args.project / 'build/current/logo', args.project)
    results = []
    for number in range(args.repeat):
        generation = out / str(number + 1)
        generation.mkdir()
        for case in args.case or CASES:
            results.append(run_case(args, executable, build, generation, case, gdb))
    checks = {'all_cases_passed': all(item['passed'] for item in results),
              'build_inputs_unchanged': not runtime.mismatched_inputs(args.project, pins),
              'build_report_unchanged': runtime.sha(report_path) == report_hash,
              'executable_unchanged': runtime.sha(executable) == report['executable']['sha256'],
              'resources_unchanged': resources == runtime.files(build / 'runtime-assets') and fonts == runtime.files(build / 'runtime-bios-fonts'),
              'original_assets_unchanged': originals == runtime.files(args.project / 'assets'),
              'support_and_fixtures_unchanged': all(runtime.sha(Path(p)) == value for p, value in {**support, **fixtures}.items())}
    receipt = {'schema': 'canonical-native-logo-release-replay-v1', 'passed': all(checks.values()),
               'checks': checks, 'build_report': str(report_path), 'build_report_sha256': report_hash,
               'executable_sha256': report['executable']['sha256'], 'fixture_pins': fixtures,
               'support_pins': support, 'case_count': len(results), 'results': results,
               'scope': 'Bounded startup input release and source modal progress; no full gameplay or global DOS/native equivalence claim.'}
    (out / 'report.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({'passed': receipt['passed'], 'case_count': len(results), 'checks': checks}))
    return int(not receipt['passed'])


if __name__ == '__main__':
    raise SystemExit(main())
