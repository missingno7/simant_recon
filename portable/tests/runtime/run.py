"""Replay the current canonical SDL3 application in a fresh disposable directory.

The runner uses only this directory's fixtures and the supplied current build
report. It neither regenerates selected source bodies nor imports old evidence.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re
import shutil
import struct
import subprocess

PROJECT = Path(__file__).resolve().parents[3]
FIXTURES = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def files(path):
    return {p.relative_to(path).as_posix(): sha(p)
            for p in sorted(path.rglob('*')) if p.is_file()}


def mismatched_inputs(project, pins):
    changed = []
    for name, expected in pins.items():
        relative = Path(name)
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError('build report contains a non-project input path')
        path = project / relative
        if not path.is_file() or sha(path) != expected:
            changed.append(name)
    return changed


def expected_replay(script):
    expected = []
    kinds = {'move': 2, 'mouse-down': 3, 'mouse-up': 4}
    buttons = {'Left': 1, 'Middle': 2, 'Right': 3}
    for line in script.read_text().splitlines():
        if not line.strip() or line.startswith('#'):
            continue
        parts = line.split()
        index, milliseconds, operation = len(expected), int(parts[0]), parts[1]
        if operation in ('down', 'up'):
            expected.append(f'Replay SDL key {index}: {milliseconds} ms {operation} {parts[2]}')
        else:
            button = 0 if operation == 'move' else buttons[parts[2]]
            x, y = parts[-2:]
            expected.append(f'Replay SDL pointer {index}: {milliseconds} ms '
                            f'kind={kinds[operation]} button={button} ({x},{y})')
    return expected


def frame_receipt(path):
    if not path.is_file():
        return None
    data = path.read_bytes()
    if len(data) < 54 or data[:2] != b'BM':
        return {'path': str(path), 'size': len(data), 'sha256': sha(path), 'valid': False}
    offset = struct.unpack_from('<I', data, 10)[0]
    width, height, planes, bpp = struct.unpack_from('<iiHH', data, 18)
    colors = len({data[p:p + 3] for p in range(offset, len(data) - 3, 4)}) if bpp == 32 else 0
    valid = (width == 640 and abs(height) == 480 and planes == 1 and bpp == 32
             and len(data) - offset == 640 * 480 * 4 and colors > 4)
    return {'path': str(path), 'size': len(data), 'sha256': sha(path),
            'width': width, 'height': height, 'bits_per_pixel': bpp,
            'distinct_rgb_colors': colors, 'valid': valid}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--flow', choices=['vga', 'save'], required=True)
    parser.add_argument('--out', type=Path)
    parser.add_argument('--project', type=Path, default=PROJECT,
                        help='current source root; defaults to this runner\'s project')
    parser.add_argument('--assets-copy', type=Path,
                        help='optional fresh resource copy inside --out')
    args = parser.parse_args()
    project = args.project.resolve()
    report_path = args.report.resolve()
    build = report_path.parent
    report_hash = sha(report_path)
    build_report = json.loads(report_path.read_text())
    if (build_report.get('schema') != 'canonical-native-complete-attempt-v1'
            or not build_report.get('passed')
            or not build_report.get('input_stability', {}).get('at_end')):
        raise ValueError('complete stable current native build required')
    pins = build_report['input_pins']
    for required in ('src/program.json', 'portable/platform.json',
                     'portable/build.py', 'portable/whole_program/application.c'):
        if required not in pins:
            raise ValueError('build report lacks current program/platform inputs')
    changed = mismatched_inputs(project, pins)
    if changed:
        raise ValueError('build inputs differ from the current project; rebuild: ' + str(changed))
    service_sources = [service['source'] for service in build_report['native_services']]
    if any(source not in pins for source in service_sources):
        raise ValueError('build report lacks a native service input pin')
    executable = Path(build_report['executable']['path']).resolve()
    if executable.parent != build or sha(executable) != build_report['executable']['sha256']:
        raise ValueError('current executable differs from its successful build report')
    platform = json.loads((project / 'portable/platform.json').read_text())
    originals = files(build / 'runtime-assets')
    expected_assets = {name: pins['assets/' + name] for name in platform['runtime_assets']}
    for resource in platform.get('generated_runtime_resources', []):
        expected_assets[resource['path']] = resource['sha256']
        if (build / 'runtime-assets' / resource['path']).stat().st_size != resource['bytes']:
            raise ValueError('generated runtime resource size differs from the platform manifest')
    if originals != expected_assets:
        raise ValueError('build resources differ from the current pinned resource manifest')
    support_before = files(build / 'runtime-bios-fonts')
    expected_support = {name.removeprefix('portable/runtime/bios-reference/'): value
                        for name, value in pins.items()
                        if name.startswith('portable/runtime/bios-reference/')}
    if support_before != expected_support:
        raise ValueError('build BIOS font resources differ from their current input pins')
    dll = build / 'SDL3.dll'
    if not dll.is_file():
        raise ValueError('built application SDL3 runtime is missing')
    dll_hash = sha(dll)
    original_assets = files(project / 'assets')
    out = (args.out or project / ('build/native-runtime-' + args.flow)).resolve()
    assets = (args.assets_copy or out / 'a').resolve()
    if assets == out or not assets.is_relative_to(out):
        raise ValueError('disposable resource copy must be inside the fresh output directory')
    if out in (project, project / 'build', build, FIXTURES):
        raise ValueError('runtime output must be a fresh disposable directory')
    if out.exists() or assets.exists():
        raise ValueError('fresh output and disposable resource directory required')
    if args.flow == 'save' and len(str(assets / 'a.ant')) > 67:
        raise ValueError('asset path exceeds original FileSelect domain; use a shorter --out')
    script = FIXTURES / ('full-game-vga.txt' if args.flow == 'vga' else 'save-game.txt')
    input_hash = sha(script)
    expected_events = expected_replay(script)
    out.mkdir(parents=True)
    shutil.copytree(build / 'runtime-assets', assets)
    before = files(assets)
    command = [str(executable), '--headless', '--smoke-ms',
               '20000' if args.flow == 'vga' else '25000', '--frame', str(out / 'frame.bmp'),
               '--assets', str(assets), '--seed', '1', '--input-script', str(script), '/dV']
    timed_out = False
    try:
        run = subprocess.run(command, cwd=project, capture_output=True, timeout=40)
        stdout, stderr, exit_code = run.stdout, run.stderr, run.returncode
    except subprocess.TimeoutExpired as error:
        timed_out = True
        stdout, stderr, exit_code = error.stdout or b'', error.stderr or b'', None
    (out / 'stdout.txt').write_bytes(stdout)
    (out / 'stderr.txt').write_bytes(stderr)
    log = stderr.decode(errors='replace')
    actual_events = [line for line in log.splitlines()
                     if line.startswith(('Replay SDL key ', 'Replay SDL pointer '))]
    loops = re.findall(r'Source-main smoke frame captured; outer game loop count=(\d+);', log)
    frame = frame_receipt(out / 'frame.bmp')
    save = assets / 'a.ant'
    saved = {'path': str(save), 'size': save.stat().st_size, 'sha256': sha(save)} if save.is_file() else None
    after = files(assets)
    changes = {name: {'before': before.get(name), 'after': after.get(name)}
               for name in sorted(before.keys() | after.keys()) if before.get(name) != after.get(name)}
    inputs_unchanged = not mismatched_inputs(project, pins)
    resources_unchanged = originals == files(build / 'runtime-assets')
    support_unchanged = support_before == files(build / 'runtime-bios-fonts') and dll_hash == sha(dll)
    originals_unchanged = original_assets == files(project / 'assets')
    checks = {
        'process_completed': exit_code == 0 and not timed_out,
        'entered_original_main_vga': 'Entering reconstructed DOS main, seed=1, video=8' in log,
        'all_fixture_events_injected': actual_events == expected_events and bool(expected_events),
        'source_main_frame_and_positive_loops': bool(loops) and int(loops[-1]) > 0,
        'meaningful_vga_frame': bool(frame and frame['valid']),
        'current_build_inputs_unchanged': inputs_unchanged,
        'build_report_unchanged': sha(report_path) == report_hash,
        'executable_unchanged': sha(executable) == build_report['executable']['sha256'],
        'fixture_unchanged': sha(script) == input_hash,
        'build_resources_unchanged': resources_unchanged,
        'runtime_support_unchanged': support_unchanged,
        'original_assets_unchanged': originals_unchanged,
        'only_expected_disposable_changes': set(changes) == ({'a.ant'} if args.flow == 'save' else set()),
        'save_record_wire_size': args.flow != 'save' or bool(saved and saved['size'] == 48386),
    }
    result = {
        'schema': 'canonical-native-runtime-replay-v2', 'passed': all(checks.values()),
        'flow': args.flow, 'checks': checks, 'build_report': str(report_path),
        'build_report_sha256': report_hash, 'verified_build_input_count': len(pins),
        'verified_native_service_count': len(service_sources),
        'current_program_sha256': pins['src/program.json'],
        'platform_manifest_sha256': pins['portable/platform.json'],
        'executable_sha256': sha(executable), 'SDL3_sha256': dll_hash,
        'resource_pins': originals, 'font_pins': support_before,
        'command': command, 'exit_code': exit_code, 'timed_out': timed_out,
        'input_script_sha256': input_hash, 'fixture_event_count': len(expected_events),
        'injected_event_count': len(actual_events), 'outer_loops': int(loops[-1]) if loops else None,
        'frame': frame, 'saved_file': saved, 'changes': changes,
        'scope': 'Bounded current original main, ordinary SDL setup/menu input, VGA frame and SaveRec wire output. '
                 'Event injection alone is not menu behavior proof; save creation corroborates the Save path. '
                 'No DOS equality, fixed terrain-seed, simulation completeness or Load roundtrip claim.',
        'build_preview_limitations': build_report.get('preview_limitations', []),
    }
    (out / 'report.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
    return int(not result['passed'])


if __name__ == '__main__':
    raise SystemExit(main())
