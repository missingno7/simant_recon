"""Modern multi-window presentation: logical windows hosted as native SDL windows.

Checks the new presentation responsibilities only: hosted windows are created
and shown by the game's own win_Open, carry complete (unoccluded) content, are
removed from the shared desktop, map window-local input to the game, apply the
background-click raise rule, and let two native windows drive one running game.
"""
from pathlib import Path
import argparse
import json
import shutil
import struct
import subprocess
import sys
import run as runtime

PROJECT = Path(__file__).resolve().parents[3]
FIXTURES = Path(__file__).resolve().parent
RED, GREY, DESKTOP = (223, 8, 4), (195, 195, 195), (0, 170, 235)  # RGB
CASES = (('raise', 'windows-raise.txt', '--windows', 13500),
         ('caste', 'windows-caste.txt', '--windows', 18500),
         ('four', 'windows-quick.txt', '--windows=0,100,1200,1300', 13500))


def pixels(path):
    data = path.read_bytes()
    offset = struct.unpack_from('<I', data, 10)[0]
    width, height = struct.unpack_from('<ii', data, 18)
    row = width * 4

    def at(x, y):
        o = offset + (y if height < 0 else abs(height) - 1 - y) * row + x * 4
        return data[o + 2], data[o + 1], data[o]
    return width, abs(height), at


def run_case(build, executable, out, name, script, option, smoke):
    target = out / name
    target.mkdir()
    assets = target / 'a'
    shutil.copytree(build / 'runtime-assets', assets)
    frame = target / 'frame.bmp'
    command = [str(executable), '--headless', option, '--smoke-ms', str(smoke), '--seed', '0',
               '--frame', str(frame), '--assets', str(assets), '--input-script', str(FIXTURES / script)]
    try:
        run = subprocess.run(command, capture_output=True, timeout=90)
        timed_out = False
    except subprocess.TimeoutExpired as expired:
        run, timed_out = expired, True
    log = (run.stderr or b'').decode(errors='replace')
    (target / 'stderr.txt').write_text(log)
    actual = [line for line in log.splitlines() if line.startswith(('Replay SDL key ', 'Replay SDL pointer '))]
    return {'exit': None if timed_out else run.returncode,
            'smoke': 'Source-main smoke frame captured;' in log,
            'replayed': actual == runtime.expected_replay(FIXTURES / script),
            'frame': frame, 'command': command}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    report_path = args.report.resolve()
    report = json.loads(report_path.read_text())
    if not report.get('passed') or not report.get('input_stability', {}).get('at_end'):
        raise ValueError('successful stable current native build required')
    if runtime.mismatched_inputs(PROJECT, report['input_pins']):
        raise ValueError('build inputs changed; rebuild')
    build = report_path.parent
    executable = Path(report['executable']['path']).resolve()
    if executable.parent != build or runtime.sha(executable) != report['executable']['sha256']:
        raise ValueError('executable differs from build report')
    out = (args.out or PROJECT / 'build/current/windows').absolute()
    sys.path.insert(0, str(PROJECT / 'tools'))
    from workspace import prepare_output
    prepare_output(out, PROJECT / 'build/current/windows', PROJECT)
    runs = {name: run_case(build, executable, out, name, script, option, smoke)
            for name, script, option, smoke in CASES}
    checks = {name + '_normal_exit_and_replay': r['exit'] == 0 and r['smoke'] and r['replayed']
              for name, r in runs.items()}

    def hosted(name, window):
        path = Path(str(runs[name]['frame']) + '.' + window + '.bmp')
        return pixels(path) if path.is_file() else None
    raise_caste, caste, behavior = hosted('raise', '1300'), hosted('caste', '1300'), hosted('caste', '1200')
    if raise_caste and caste and behavior:
        checks['hosted_windows_shown_at_logical_size'] = raise_caste[:2] == caste[:2] == (214, 192)
        # Win16 WM_MOUSEACTIVATE / DOS f_218D_0451: the first click on a background
        # window raises it; the click does not reach the Manual button.
        checks['background_click_only_raises'] = raise_caste[2](12, 49) == GREY and raise_caste[2](12, 32) == RED
        checks['second_click_reaches_game_object'] = caste[2](12, 49) == RED and caste[2](12, 32) == GREY
        checks['triangle_drag_changes_caste_display'] = any(
            raise_caste[2](x, y) != caste[2](x, y) for x in range(84, 132) for y in range(28, 46))
        checks['second_native_window_in_same_game'] = behavior[2](12, 49) == RED
    else:
        checks['hosted_frames_present'] = False
    root = pixels(runs['caste']['frame'])[2]
    # The control windows' logical area (bottom of the 640x480 desktop) is desktop.
    checks['hosted_windows_removed_from_desktop'] = root(100, 450) == DESKTOP and root(400, 450) == DESKTOP
    four = pixels(runs['four']['frame'])[2]
    checks['all_four_hosted_desktop_is_empty'] = all(
        four(x, y) == DESKTOP for x in range(0, 640, 37) for y in range(40, 480, 41))
    checks['four_hosted_frames_present'] = all(hosted('four', w) for w in ('0000', '0100', '1200', '1300'))
    result = {'passed': all(checks.values()), 'checks': checks,
              'executable_sha256': report['executable']['sha256'],
              'runs': {k: {**v, 'frame': str(v['frame'])} for k, v in runs.items()}}
    (out / 'report.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'passed': result['passed'],
                      'failed_checks': [k for k, v in checks.items() if not v]}))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    sys.exit(main())
