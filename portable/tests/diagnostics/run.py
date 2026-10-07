"""Child-process crash capture and debug input/capture/replay regressions."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
from workspace import prepare_output


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def field(text, key):
    return next(line.partition('=')[2] for line in text.splitlines()
                if line.startswith(key + '='))


def dump_exception(path):
    data = path.read_bytes()
    assert data[:4] == b'MDMP', 'invalid minidump header'
    count, directory = struct.unpack_from('<II', data, 8)
    for i in range(count):
        kind, size, offset = struct.unpack_from('<III', data, directory + i * 12)
        if kind == 6:
            assert size >= 168 and offset + size <= len(data)
            return struct.unpack_from('<I', data, offset)[0], struct.unpack_from('<I', data, offset + 8)[0]
    raise AssertionError('minidump has no fault-thread exception stream')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--out', type=Path, default=ROOT / 'build/current/tests/diagnostics')
    args = parser.parse_args()
    assert os.name == 'nt', 'Windows crash diagnostics require Windows'
    report_path = args.report.resolve()
    report = json.loads(report_path.read_text())
    assert report['passed'] and report['input_stability']['at_end']
    for name, pin in report['input_pins'].items():
        assert sha(ROOT / name) == pin, 'changed source; rebuild: ' + name
    exe = Path(report['executable']['path'])
    assert sha(exe) == report['executable']['sha256']
    out = prepare_output(args.out, ROOT / 'build/current/tests/diagnostics')
    diagnostic_root = out / 'sessions'
    results = []

    def run(*extra):
        previous = set(diagnostic_root.glob('simant-*'))
        command = [str(exe), '--headless', '--seed', '17',
                   f'--diagnostics-dir={diagnostic_root}', *extra]
        child = subprocess.run(command, cwd=ROOT, capture_output=True, timeout=30)
        sessions = set(diagnostic_root.glob('simant-*')) - previous
        assert len(sessions) == 1, 'launch must create exactly one new session'
        session = sessions.pop()
        log = (session / 'session.log').read_text(errors='replace')
        assert field(log, 'executable_sha256') == sha(exe)
        assert field(log, 'build_revision') == report['build_identity']['source_revision']
        assert field(log, 'seed') == '17'
        assert 'SIMANT.CFG contents begin' in log
        assert (exe.parent / 'runtime-assets/SIMANT.CFG').read_text().strip() in log
        results.append({'command': command, 'exit_code': child.returncode, 'session': str(session)})
        return child, session, log

    for switch, code in (('--test-crash', 0xC0000005), ('--test-crash-thread', 0xC0000005),
                         ('--test-abort', 0xE0000001)):
        child, session, log = run(switch)
        assert child.returncode != 0, 'deliberate fault unexpectedly returned'
        crash = (session / 'crash.txt').read_text(errors='replace')
        assert int(field(crash, 'exception_code'), 16) == code
        thread, dumped_code = dump_exception(session / 'crash.dmp')
        assert thread == int(field(crash, 'thread_id')) and dumped_code == code
        if code == 0xC0000005:
            assert thread == int(field(log, 'test_fault_thread')), 'dump names a different thread than the actual fault'
        assert 'minidump_written=yes' in crash
        assert sha(session / 'simant-crashed.exe') == sha(exe)
        assert 'last_input_events_begin' in crash and 'main_loop_counter=' in crash
        if switch == '--test-crash':
            assert any('simant_diagnostics_test_crash+' in line and line.startswith('stack_')
                       for line in crash.splitlines()), 'faulting frame is not symbolized'
            assert any(' main+' in line for line in crash.splitlines()), 'caller frames are not symbolized'
            assert sum(line.startswith('stack_0') for line in crash.splitlines()) >= 3
        assert field(log, 'stop_reason') == 'unhandled exception'
        assert not (session / 'input.txt').exists(), 'normal launch must not record unbounded input'

    child, session, log = run('--debug', '--test-input', '--smoke-ms', '1000')
    assert child.returncode == 0, child.stderr.decode(errors='replace')
    assert field(log, 'exit_status') == '0' and field(log, 'stop_reason') == 'smoke deadline'
    debug_log = (session / 'debug.log').read_text(errors='replace')
    assert 'Entering reconstructed DOS main' in debug_log
    assert 'SimAnt diagnostics SDL log regression' in debug_log
    recorded = session / 'input.txt'
    lines = [line for line in recorded.read_text().splitlines() if line and not line.startswith('#')]
    assert any(' move ' in line for line in lines)
    assert any(' down F12' in line for line in lines) and any(' up F12' in line for line in lines)
    assert any(' down Left Shift' in line for line in lines)
    assert any(' mouse-down Right ' in line for line in lines)
    assert any(' mouse-up Right ' in line for line in lines)
    captures = list(session.glob('capture-*'))
    assert len(captures) == 1, 'one F12 press should save exactly one capture'
    image = (captures[0] / 'screenshot.bmp').read_bytes()
    assert image[:2] == b'BM'
    assert struct.unpack_from('<ii', image, 18) == (640, 480)
    palette = (captures[0] / 'palette.txt').read_text()
    assert len([line for line in palette.splitlines() if not line.startswith('#')]) == 16
    colors = {bytes(int(v) for v in row.split()[1:])[::-1]
              for row in palette.splitlines() if not row.startswith('#')}
    offset = struct.unpack_from('<I', image, 10)[0]
    assert struct.unpack_from('<H', image, 28)[0] == 32
    assert {image[i:i + 3] for i in range(offset, len(image), 4)} <= colors, 'capture palette differs from the presented frame'
    assert 'main_loop_counter=' in (captures[0] / 'frame.txt').read_text()

    # Consume the actual recorded file through the production replay loader.
    child, replay_session, _ = run('--debug', '--input-script', str(recorded), '--smoke-ms', '1000')
    assert child.returncode == 0
    replay_log = (replay_session / 'debug.log').read_text(errors='replace')
    for line in lines:
        if line.split()[1] in ('down', 'up'):
            assert f'{line.split()[0]} ms ' + ' '.join(line.split()[1:]) in replay_log
    assert 'Replay SDL pointer' in replay_log and 'Replay SDL key' in replay_log
    replayed = (replay_session / 'input.txt').read_text()
    assert 'down F12' not in replayed, 'scripted input must not be re-recorded as physical input'

    # A real debug session readily exceeds the former 512-command fixed array.
    long_script = out / 'long-input.txt'
    long_script.write_text('0 checkpoint\n' * 600 + '0 up Left Shift\n')
    child, _, _ = run('--input-script', str(long_script), '--smoke-ms', '500')
    assert child.returncode == 0
    assert b'Replay SDL key 600:' in child.stderr

    # Normal F12 passes the host boundary without creating debug captures.
    child, normal, _ = run('--test-input', '--smoke-ms', '500')
    assert child.returncode == 0
    assert not list(normal.glob('capture-*')) and not (normal / 'input.txt').exists()
    child, late, log = run('--debug', '--test-input-crash', '--smoke-ms', '1000')
    assert child.returncode != 0
    crash = (late / 'crash.txt').read_text()
    tail = crash.split('last_input_events_begin\n')[1].split('last_input_events_end')[0].splitlines()
    assert len(tail) == 200, 'crash should retain only the latest 200 input events'
    assert tail[-1].endswith('up F12')
    assert int(field(crash, 'thread_id')) == int(field(log, 'test_fault_thread'))
    assert field(crash, 'last_source_boundary') == 'replay_input'
    result = {'passed': True, 'build_report_sha256': sha(report_path), 'runs': results,
              'scope': 'Windows fault-thread dump/symbolized frame, exact executable copy, SDL input capture/replay and presented-frame F12 capture.'}
    (out / 'report.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
