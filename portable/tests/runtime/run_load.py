"""Exercise current original-main Save then Load using ordinary SDL input.

Requires GDB with Python support. Read-only breakpoints corroborate the two
successful source returns and the complete SaveRec reads. No state equality
or DOS save compatibility claim is made by this bounded validation.
"""
from pathlib import Path
import argparse
import json
import os
import re
import shutil
import subprocess
import run as runtime

PROJECT = Path(__file__).resolve().parents[3]
FIXTURES = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--out', type=Path)
    parser.add_argument('--project', type=Path, default=PROJECT)
    parser.add_argument('--gdb', default='C:/msys64/mingw64/bin/gdb.exe'
                        if Path('C:/msys64/mingw64/bin/gdb.exe').is_file() else 'gdb')
    args = parser.parse_args()
    project, report_path = args.project.resolve(), args.report.resolve()
    report_hash = runtime.sha(report_path)
    build = report_path.parent
    build_report = json.loads(report_path.read_text())
    if (build_report.get('schema') != 'canonical-native-complete-attempt-v1'
            or not build_report.get('passed')
            or not build_report.get('input_stability', {}).get('at_end')):
        raise ValueError('complete stable current native build required')
    pins = build_report['input_pins']
    for name in ('src/program.json', 'portable/platform.json', 'portable/build.py',
                 'portable/whole_program/application.c'):
        if name not in pins:
            raise ValueError('build report lacks current program/platform inputs')
    changed = runtime.mismatched_inputs(project, pins)
    if changed:
        raise ValueError('current build inputs changed; rebuild: ' + str(changed))
    services = [service['source'] for service in build_report['native_services']]
    if any(source not in pins for source in services):
        raise ValueError('native service pin missing from build report')
    executable = Path(build_report['executable']['path']).resolve()
    executable_hash = build_report['executable']['sha256']
    if executable.parent != build or runtime.sha(executable) != executable_hash:
        raise ValueError('executable differs from the successful current build')
    platform = json.loads((project / 'portable/platform.json').read_text())
    expected_resources = {name: pins['assets/' + name] for name in platform['runtime_assets']}
    for resource in platform.get('generated_runtime_resources', []):
        expected_resources[resource['path']] = resource['sha256']
        if (build / 'runtime-assets' / resource['path']).stat().st_size != resource['bytes']:
            raise ValueError('generated runtime resource size differs from its manifest')
    resources = runtime.files(build / 'runtime-assets')
    if resources != expected_resources:
        raise ValueError('build resource copy differs from its current manifest pins')
    fonts = runtime.files(build / 'runtime-bios-fonts')
    expected_fonts = {name.removeprefix('portable/runtime/bios-reference/'): value
                      for name, value in pins.items()
                      if name.startswith('portable/runtime/bios-reference/')}
    if fonts != expected_fonts:
        raise ValueError('BIOS font resource copy differs from its current input pins')
    dll = build / 'SDL3.dll'
    dll_hash = runtime.sha(dll)
    original_assets = runtime.files(project / 'assets')
    gdb_found = shutil.which(args.gdb)
    if not gdb_found:
        raise ValueError('GDB with Python support is required; pass --gdb')
    gdb_path = Path(gdb_found).resolve()
    gdb_hash = runtime.sha(gdb_path)
    out = (args.out or project / 'build/native-runtime-load').resolve()
    if out.exists() or out in (project, project / 'build', build, FIXTURES):
        raise ValueError('fresh disposable output directory required')
    assets = out / 'a'
    if len(str(assets / 'a.ant')) > 67:
        raise ValueError('asset path exceeds original FileSelect domain; use a shorter --out')
    script, trace = FIXTURES / 'save-load-game.txt', FIXTURES / 'load_trace.py'
    fixture_pins = {path.name: runtime.sha(path) for path in
                    (script, trace, Path(__file__), FIXTURES / 'run.py')}
    expected_events = runtime.expected_replay(script)
    out.mkdir(parents=True)
    shutil.copytree(build / 'runtime-assets', assets)
    before = runtime.files(assets)
    commands = out / 'gdb.txt'
    trace_literal = repr(str(trace))
    commands.write_text('set pagination off\nset confirm off\npython exec(compile(open('
                        + trace_literal + ').read(), ' + trace_literal + ", 'exec'))\nrun\n")
    application_command = [str(executable), '--headless', '--smoke-ms', '35000',
                           '--frame', str(out / 'frame.bmp'), '--assets', str(assets),
                           '--seed', '1', '--input-script', str(script), '/dV']
    command = [str(gdb_path), '--batch', '-q', '-x', str(commands), '--args', *application_command]
    env = dict(os.environ, SIMANT_TRACE_OUT=str(out / 'events.jsonl'),
               SIMANT_TRACE_ASSETS=str(assets))
    timed_out = False
    try:
        result = subprocess.run(command, cwd=project, env=env, capture_output=True, timeout=70)
        stdout, stderr, exit_code = result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired as error:
        timed_out = True
        stdout, stderr, exit_code = error.stdout or b'', error.stderr or b'', None
    (out / 'stdout.txt').write_bytes(stdout)
    (out / 'stderr.txt').write_bytes(stderr)
    log = stderr.decode(errors='replace')
    actual_events = [line for line in log.splitlines()
                     if line.startswith(('Replay SDL key ', 'Replay SDL pointer '))]
    event_path = out / 'events.jsonl'
    events = [json.loads(line) for line in event_path.read_text().splitlines()] if event_path.is_file() else []
    saves = [event for event in events if event['event'] == 'o09_35F5_0188-return']
    loads = [event for event in events if event['event'] == 'LoadGame-return']
    selectors = [event for event in events if event['event'] == 'o09_35F5_03C6-return']
    reads = [event for event in events if event['event'] == 'LoadGame-read-entry']
    read_returns = {event['call']: event for event in events if event['event'] == 'LoadGame-read-return'}
    exits = [event for event in events if event['event'] == 'inferior-exit']
    loops = re.findall(r'Source-main smoke frame captured; outer game loop count=(\d+);', log)
    frame = runtime.frame_receipt(out / 'frame.bmp')
    after = runtime.files(assets)
    changes = {name: {'before': before.get(name), 'after': after.get(name)}
               for name in sorted(before.keys() | after.keys()) if before.get(name) != after.get(name)}
    saved_path = assets / 'a.ant'
    saved = {'path': str(saved_path), 'size': saved_path.stat().st_size,
             'sha256': runtime.sha(saved_path)} if saved_path.is_file() else None
    save_return_ok = len(saves) == 1 and saves[0].get('result') == 1
    load_return_ok = len(loads) == 1 and loads[0].get('result') == 1
    full_reads = (len(reads) == 307 and len(read_returns) == 307
                  and sum(event['requested'] for event in reads) == 48386
                  and all(read_returns.get(event['call'], {}).get('returned') == event['requested']
                          for event in reads))
    checks = {
        'process_completed': exit_code == 0 and not timed_out and len(exits) == 1 and exits[0]['exit_code'] == 0,
        'entered_original_main_vga': 'Entering reconstructed DOS main, seed=1, video=8' in log,
        'all_fixture_events_injected': actual_events == expected_events and bool(expected_events),
        'source_main_frame_and_positive_loops': bool(loops) and int(loops[-1]) > 0,
        'meaningful_vga_frame': bool(frame and frame['valid']),
        'source_SaveGame_returned_success': save_return_ok,
        'source_LoadGame_returned_success': load_return_ok,
        'both_source_FileSelect_paths_accepted': len(selectors) == 2
            and [(event['save'], event['result']) for event in selectors] == [(1, 1), (0, 1)]
            and all(event.get('selected_path') == str(saved_path) for event in selectors),
        'all_307_SaveRec_reads_complete': full_reads,
        'saved_file_unchanged_during_load': save_return_ok and load_return_ok and bool(saved)
            and saves[0].get('saved_file') == loads[0].get('saved_file') == saved and saved['size'] == 48386,
        'no_trace_errors': not any(event['event'] == 'trace-error' for event in events),
        'current_build_inputs_unchanged': not runtime.mismatched_inputs(project, pins),
        'build_report_unchanged': runtime.sha(report_path) == report_hash,
        'executable_unchanged': runtime.sha(executable) == executable_hash,
        'fixtures_and_driver_unchanged': all(runtime.sha(FIXTURES / name) == value
                                             for name, value in fixture_pins.items()),
        'build_resources_unchanged': resources == runtime.files(build / 'runtime-assets'),
        'runtime_support_unchanged': fonts == runtime.files(build / 'runtime-bios-fonts')
            and runtime.sha(dll) == dll_hash,
        'original_assets_unchanged': original_assets == runtime.files(project / 'assets'),
        'debugger_unchanged': runtime.sha(gdb_path) == gdb_hash,
        'only_expected_disposable_changes': set(changes) == {'a.ant'},
    }
    receipt = {
        'schema': 'canonical-native-save-load-replay-v1', 'passed': all(checks.values()),
        'checks': checks, 'build_report': str(report_path), 'build_report_sha256': report_hash,
        'verified_build_input_count': len(pins), 'verified_native_service_count': len(services),
        'current_program_sha256': pins['src/program.json'],
        'platform_manifest_sha256': pins['portable/platform.json'],
        'executable_sha256': executable_hash, 'SDL3_sha256': dll_hash,
        'resource_pins': resources, 'font_pins': fonts, 'fixture_and_driver_pins': fixture_pins,
        'GDB': {'path': str(gdb_path), 'sha256': gdb_hash}, 'command': command,
        'exit_code': exit_code, 'timed_out': timed_out, 'fixture_event_count': len(expected_events),
        'injected_event_count': len(actual_events), 'outer_loops': int(loops[-1]) if loops else None,
        'source_returns': saves + selectors + loads, 'load_read_calls': len(reads),
        'load_requested_bytes': sum(event['requested'] for event in reads),
        'load_returned_bytes': sum(event['returned'] for event in read_returns.values()),
        'frame': frame, 'saved_file': saved, 'changes': changes,
        'events_sha256': runtime.sha(event_path) if event_path.is_file() else None,
        'scope': 'Current original main and ordinary SDL UI create then load a disposable SaveRec file. '
                 'Read-only debugger observations establish successful source returns and complete reads. '
                 'No after-load state equivalence, DOS save compatibility, resave, fixed terrain-seed '
                 'or whole-game correctness claim.',
        'build_preview_limitations': build_report.get('preview_limitations', []),
    }
    (out / 'report.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt, indent=2))
    return int(not receipt['passed'])


if __name__ == '__main__':
    raise SystemExit(main())
