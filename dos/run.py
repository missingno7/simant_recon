"""Separate pinned DOSBox-X executions for diagnostic source EXEs and the oracle.

Execution receipts never establish boot, VGA, interaction or closure by timeout.
Original executable bytes are permitted only with explicit --original mode;
diagnostic mode accepts only the hash-pinned product of dos/diagnostic.py.
"""
from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from dos import build, diagnostic

RESOURCES = ('FONT1', 'FONT2', 'FONT3', 'FONT4', 'HCEGANT.DAT', 'HCEGANT.NDX',
             'SHARED.DAT', 'SHARED.NDX', 'SOUND.DAT', 'SOUND.NDX', 'SIMANT.CFG', 'INSTALL.EXE')

# Deliberately only guest keyboard keys, from the pinned runner's AUTOTYPE -list.
# Host mapper actions cannot enter a game-input recipe.
KEYS = frozenset('abcdefghijklmnopqrstuvwxyz0123456789') | frozenset(
    'enter esc space tab bspace up down left right home end pageup pagedown '
    'insert delete lshift rshift lctrl rctrl lalt ralt minus equals comma period '
    'slash backslash semicolon quote lbracket rbracket grave'.split()) | frozenset(
    'f' + str(i) for i in range(1, 13)) | frozenset(
    'kp_' + str(i) for i in range(10)) | {','}


def keyboard_command(keys, delay, pace):
    if not keys:
        return None
    if (len(keys) > 128 or any(k not in KEYS for k in keys) or
            not math.isfinite(delay) or not 0 <= delay <= 30 or
            not math.isfinite(pace) or not 0 <= pace <= 10):
        raise ValueError('keyboard recipe requires at most 128 known keys, delay 0..30 and pace 0..10 seconds')
    return f'AUTOTYPE -w {delay:g} -p {pace:g} ' + ' '.join(keys) + ' > INPUT.LOG'


SCRIPT_COMMANDS = {'key', 'keydown', 'keyup', 'mouse_move', 'mouse_button', 'dump', 'exit'}


def input_script(path, out):
    """Validate an emulated-time input/observation script for the acceptance runner.

    Lines are `<emulated_ms> <command> ...`. Dump destinations are bare names
    rewritten into the fresh output directory; no other host path is allowed.
    """
    path = Path(path).resolve()
    if not path.is_relative_to(ROOT / 'dos/scenarios'):
        path = diagnostic.experimental_path(path)
    lines, last = [], -1
    for number, raw in enumerate(Path(path).read_text().splitlines(), 1):
        line = raw.split('#', 1)[0].strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) < 2 or not parts[0].isdigit() or parts[1] not in SCRIPT_COMMANDS:
            raise ValueError(f'input script line {number}: expected <ms> <command>')
        ms = int(parts[0])
        if ms < last:
            raise ValueError(f'input script line {number}: times must not decrease')
        last = ms
        if parts[1] in ('key', 'keydown', 'keyup') and (len(parts) != 3 or parts[2] not in KEYS - {','}):
            raise ValueError(f'input script line {number}: unknown key')
        if parts[1] == 'mouse_move' and (len(parts) != 4 or not all(re.fullmatch(r'-?\d{1,4}', v) for v in parts[2:])):
            raise ValueError(f'input script line {number}: mouse_move <dx> <dy>')
        if parts[1] == 'mouse_button' and (len(parts) != 4 or parts[2] not in '012' or parts[3] not in ('down', 'up')):
            raise ValueError(f'input script line {number}: mouse_button <0|1|2> down|up')
        if parts[1] == 'dump':
            if len(parts) != 5 or not re.fullmatch(r'[0-9A-Fa-f]{1,6}', parts[2]) or \
                    not re.fullmatch(r'[0-9A-Fa-f]{1,6}', parts[3]) or not re.fullmatch(r'[A-Za-z0-9_.-]{1,40}', parts[4]):
                raise ValueError(f'input script line {number}: dump <lin_hex> <len_hex> <name>')
            parts[4] = str(out / ('dump-' + parts[4]))
        if parts[1] == 'exit' and len(parts) != 2:
            raise ValueError(f'input script line {number}: exit takes no arguments')
        lines.append(' '.join(parts))
    if not lines:
        raise ValueError('input script is empty')
    return lines


def diagnostic_image(receipt):
    receipt = diagnostic.experimental_path(receipt)
    raw, identity = build.read_pin(receipt)
    report = json.loads(raw)
    if (report.get('schema') != 'simant-diagnostic-dos-build-v1' or
        report.get('target') != 'DIAGNOSTIC_DOS' or report.get('status') != 'DIAGNOSTIC_LINKED' or
        report.get('closure_eligible') is not False or report.get('errors') or
        any(report.get('original_exe_bytes_used', {}).values()) or
        set(report.get('original_exe_bytes_used', {})) != {'game_code', 'game_data', 'fallback_debt', 'executable_fragments'}):
        raise ValueError('execution requires a successful diagnostic build receipt with zero original bytes')
    log_pin = report['link']['log']
    log_path = diagnostic.experimental_path(ROOT / log_pin['path'])
    log_path.relative_to(receipt.parent / 'link')
    log_raw, log_identity = build.read_pin(log_path, log_pin['sha256'])
    if not log_raw.strip() or build.linker_diagnostics(log_raw.decode('latin1')):
        raise ValueError('execution requires a diagnostic link with no linker warnings or errors')
    candidate = report['link']['candidate_executable']
    path = diagnostic.experimental_path(ROOT / candidate['path'])
    path.relative_to(receipt.parent / 'link')
    raw, pin = build.read_pin(path, candidate['sha256'])
    if raw[:2] != b'MZ':
        raise ValueError('diagnostic image is not MZ')
    provenance = {field: report[field] for field in ('provisional_assumptions', 'canonical_blockers',
        'unproved_execution_contracts', 'unproved_initialized_data')}
    provenance['supported_execution_domain'] = report.get('supported_execution_domain')
    provenance['resolved_domain_contracts'] = report.get('resolved_domain_contracts', [])
    return path.name, raw, [identity, log_identity, pin], provenance


def pinned_resource(name, oracle):
    raw = (ROOT / 'assets' / name).read_bytes()
    expected = oracle['inputs'][name]
    if build.digest(raw) != expected['sha256'] or len(raw) != expected['size']:
        raise ValueError('runtime resource identity differs: ' + name)
    return raw, {'path': 'assets/' + name, 'sha256': build.digest(raw), 'size': len(raw)}


def saved_game_input(path):
    """Stage explicit runtime user data, never an executable/storage provider."""
    path = diagnostic.experimental_path(path)
    if not re.fullmatch(r'[A-Za-z0-9_]{1,8}\.ANT', path.name, re.I):
        raise ValueError('saved game must have a DOS 8.3 .ANT filename')
    raw, pin = build.read_pin(path)
    return path.name.upper(), raw, pin


def runtime_observations(raw, game_log=None):
    lines = raw.decode('latin1').splitlines()
    video = [line for line in lines if re.search(r'(?:set|setting).*video.*mode|640.*480', line, re.I)]
    reads = []
    for line in lines:
        match = re.search(r'Reading (\d+) bytes from (\S+)', line)
        if match and match[2].upper() in RESOURCES:
            reads.append({'file': match[2].upper(), 'bytes': int(match[1])})
    milestones = []
    kinds = {
        'unhandled_interrupt': [line for line in lines if re.search(r'\bERROR CPU:Illegal Unhandled Interrupt Called \d+\s*$', line)],
        'segment_limit': [line for line in lines if line.strip() == 'Segment limit violation'],
        'game_abort': [line for line in (game_log or '').splitlines() if line.strip() == 'FATAL ERROR: PROGRAM ABORTED'],
    }
    faults = [line for rows in kinds.values() for line in rows]
    mode = next((i for i, line in enumerate(lines) if re.search(r'INT10:Set Video Mode 12\s*$', line)), None)
    if mode is not None and any(re.search(r'VGA:640x480\b', line) for line in lines[mode+1:]):
        milestones.append({'id': 'VGA_640X480_ENTRY',
            'scope': 'Observed BIOS mode 12h followed by VGA 640x480; rendering, input and gameplay are unverified.'})
    return {'video_log_lines': video, 'resource_read_events': reads,
            'functional_milestones_verified': milestones,
            'runtime_faults': {'count': len(faults), 'first_lines': faults[:8],
                               'kind_counts': {kind: len(rows) for kind, rows in kinds.items()}}}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--build-report', type=Path)
    mode.add_argument('--original', action='store_true')
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--seconds', type=int, default=15)
    parser.add_argument('--argument', action='append', default=[])
    parser.add_argument('--prepare-only', action='store_true')
    parser.add_argument('--visible', action='store_true')
    parser.add_argument('--trace-runtime', action='store_true',
        help='enable documented DOSBox-X video/exec/file logs without guest instrumentation')
    parser.add_argument('--key', action='append', default=[], help='scheduled guest key; repeat for a sequence; comma adds a pace delay')
    parser.add_argument('--key-delay', type=float, default=5, help='seconds before scheduled keys begin (0..30)')
    parser.add_argument('--key-pace', type=float, default=2, help='seconds between scheduled keys (0..10)')
    parser.add_argument('--capture-video', action='store_true', help='record guest video through DOSBox-X DX-CAPTURE')
    parser.add_argument('--cycles', type=int, help='fixed emulated CPU cycles per ms (default: pinned runner value)')
    parser.add_argument('--input-script', type=Path,
                        help='emulated-time input/dump script for the pinned acceptance runner (exclusive with --key)')
    parser.add_argument('--fixed-clock', action='store_true', help='set guest DOS date/time to a fixed value before launch')
    parser.add_argument('--saved-game', type=Path, help='copy an explicit worker/scratch .ANT save into the guest drive')
    args = parser.parse_args(argv)
    # Scripted acceptance runs end with their own emulated-time `exit`; the
    # host limit is only a safety net there.
    if not 1 <= args.seconds <= (7200 if args.input_script else 60):
        parser.error('--seconds must be between 1 and 60 (7200 with --input-script)')
    if any(not re.fullmatch(r'[A-Za-z0-9_./:=+-]+', a) for a in args.argument):
        parser.error('DOS arguments must be single safe tokens')
    try:
        input_command = keyboard_command(args.key, args.key_delay, args.key_pace)
        saved_game = saved_game_input(args.saved_game) if args.saved_game else None
    except (ValueError, OSError) as error:
        parser.error(str(error))
    out = diagnostic.experimental_path(args.out)
    build.prepare_output(out, ROOT / 'build/current/dos-runtime')
    report = {'schema': 'simant-dos-execution-v1',
        'target': 'ORIGINAL_ORACLE' if args.original else 'DIAGNOSTIC_DOS',
        'closure_eligible': False, 'human_acceptance': False, 'functional_milestones_verified': [],
        'inputs': [], 'errors': [], 'seconds': args.seconds}
    try:
        oracle = json.loads((ROOT / 'layout/oracle.lock.json').read_text())
        if args.original:
            name = 'SIMANT.EXE'
            raw, pin = pinned_resource(name, oracle)
            report['inputs'].append(pin)
        else:
            name, raw, pins, provenance = diagnostic_image(args.build_report)
            report['inputs'] += pins
            report.update(provenance)
        domain = report.get('supported_execution_domain')
        if domain:
            report['domain_launch_matches'] = args.argument == domain['launch_arguments']
            report['domain_scope'] = 'Launch arguments and staged resource pins are checked; successful resource operations and valid runtime state remain proof premises, not facts inferred from a timeout.'
        (out / name).write_bytes(raw)
        for resource in RESOURCES:
            raw, pin = pinned_resource(resource, oracle)
            report['inputs'].append(pin)
            (out / resource).write_bytes(raw)
        if saved_game:
            save_name, save_raw, save_pin = saved_game
            (out / save_name).write_bytes(save_raw)
            report['inputs'].append(save_pin)
            report['staged_saved_game'] = {'source': save_pin, 'guest_name': save_name,
                'scope': 'Unmodified runtime user data. Staging does not establish successful Load or restored state equality.'}
        report['inert_runtime_file'] = {'path': 'INSTALL.EXE',
            'role': 'main opens this file five times to check DOS file-handle availability; never executed by the runner'}
        if args.input_script and args.key:
            raise ValueError('--input-script and --key are exclusive')
        runner = build.compiler.toolchain()['runners']['dosbox-x-acceptance' if args.input_script else 'dosbox-x']
        report['runner'] = build.read_pin(runner['path'], runner['sha256'])[1]
        if args.input_script:
            script = input_script(args.input_script, out)
            (out / 'INPUT.SCR').write_text('\n'.join(script) + '\n')
            report['input_script'] = {'source': str(args.input_script), 'events': len(script),
                'scope': 'Emulated-time scheduled input and memory dumps; deterministic for fixed cycles and guest clock.'}
        batch = ['@echo off']
        if args.fixed_clock:
            batch += ['date 01-01-1992', 'time 12:00:00']
            report['guest_clock'] = 'DATE 01-01-1992, TIME 12:00:00 set by the batch before input scheduling and launch'
        if input_command:
            batch.append(input_command)
            report['scheduled_keyboard'] = {'keys': args.key, 'delay_seconds': args.key_delay,
                'pace_seconds': args.key_pace, 'command': input_command,
                'scope': 'Scheduled emulator key events; scheduling alone does not prove game delivery or handling. Timing is not a state synchronization barrier.'}
        launch = name + ' ' + ' '.join(args.argument)
        if args.capture_video:
            launch = 'DX-CAPTURE /V /-A /-M ' + launch
            (out / 'capture').mkdir()
        batch += ['echo STARTED>STARTED.TXT', launch + ' > GAME.LOG']
        # DOSBox-X's COMMAND.COM does not expand %ERRORLEVEL%; IF ERRORLEVEL
        # is the DOS command contract used by the historical tools.
        batch += [f'if errorlevel {n} goto RC{n}' for n in range(255, -1, -1)]
        for n in range(256):
            batch += [f':RC{n}', f'echo {n}>GAME.RC', 'goto DONE']
        batch += [':DONE', 'echo RETURNED>RETURNED.TXT']
        (out / 'RUN.BAT').write_bytes(('\r\n'.join(batch) + '\r\n').encode('ascii'))
        conf = []
        for section, settings in runner['conf'].items():
            if section == 'cpu' and args.cycles is not None:
                if not 100 <= args.cycles <= 1000000:
                    raise ValueError('--cycles must be 100..1000000')
                settings = {**settings, 'cycles': f'fixed {args.cycles}'}
                report['cpu_cycles'] = settings['cycles']
            conf += ['[' + section + ']'] + [f'{k}={v}' for k, v in settings.items()]
            if section == 'dosbox' and args.input_script:
                conf += ['acceptance script=' + str(out / 'INPUT.SCR'), 'acceptance log=' + str(out / 'INPUT.LOG')]
            if section == 'dosbox' and args.capture_video:
                conf += ['captures=' + str(out / 'capture'), 'show recorded filename=false']
        if args.trace_runtime:
            conf += ['[log]', 'logfile=' + str(out / 'dosbox-runtime.log'),
                     'vga=debug', 'int10=debug', 'files=debug', 'exec=debug', 'fileio=true']
            report['trace_scope'] = 'DOSBox-X video mode, executable and DOS file I/O logs; no guest code changes'
        conf += ['[autoexec]', f'mount c "{out}"', 'c:', 'call RUN.BAT', 'exit']
        path = out / 'dosbox.conf'
        path.write_text('\n'.join(conf) + '\n')
        command = [runner['path'], '-conf', str(path), '-fastlaunch', '-exit', '-nomenu']
        report['command'] = command
        report['status'] = 'PREPARED'
        if not args.prepare_only:
            env = dict(os.environ)
            if not args.visible:
                env.update(SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy')
            with (out / 'host.log').open('wb') as log:
                try:
                    process = subprocess.run(command, cwd=out, env=env,
                        stdout=log, stderr=subprocess.STDOUT, timeout=args.seconds,
                        creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
                    report['host_exit_code'] = process.returncode
                    report['status'] = 'RETURNED' if (out / 'RETURNED.TXT').is_file() else 'EMULATOR_EXITED'
                except subprocess.TimeoutExpired:
                    report['status'] = 'TIME_LIMIT'
            report['guest_started'] = (out / 'STARTED.TXT').is_file()
            rc = out / 'GAME.RC'
            report['guest_exit_code'] = rc.read_text().strip() if rc.is_file() else None
            game_log = out / 'GAME.LOG'
            report['game_log'] = game_log.read_text(encoding='latin1') if game_log.is_file() else None
            if input_command:
                input_log = out / 'INPUT.LOG'
                report['keyboard_log'] = input_log.read_text(encoding='latin1') if input_log.is_file() else None
            if args.capture_video:
                report['video_captures'] = [build.read_pin(p)[1] for p in sorted((out / 'capture').glob('*.avi'))]
                report['video_scope'] = 'Guest video only; no audio recording. A time-limited emulator kill may leave an unfinalized AVI. Inspect decoded screen states; elapsed time is not gameplay equivalence.'
            trace = out / 'dosbox-runtime.log'
            raw = b''
            if args.trace_runtime and trace.is_file():
                raw = trace.read_bytes()
                report['runtime_log'] = {'path': trace.relative_to(ROOT).as_posix(),
                    'sha256': build.digest(raw), 'size': len(raw)}
            report.update(runtime_observations(raw, report['game_log']))
            if report['runtime_faults']['count']:
                report['status'] = 'GUEST_FAULT_OBSERVED'
    except (ValueError, OSError, KeyError, subprocess.SubprocessError) as error:
        report['status'] = 'FAILED'
        report['errors'].append(str(error))
    (out / 'execution-report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: report.get(k) for k in ('status', 'target', 'guest_started', 'guest_exit_code',
        'runtime_log', 'video_log_lines', 'functional_milestones_verified', 'runtime_faults', 'errors')}, indent=2))
    return 1 if report['status'] in ('FAILED', 'GUEST_FAULT_OBSERVED') else 0


if __name__ == '__main__':
    raise SystemExit(main())
