"""Observe discarded-handle differences in the current whole native provider.

Passing this replay confirms the recorded discrepancy, not native equivalence.
No game/provider source is replaced and no original bytes are linked.
"""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess

ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'src/program.json').is_file())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--conversion', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    conversion = (ROOT / args.conversion).resolve()
    out = (ROOT / args.out).resolve()
    if out.exists() or out == ROOT / 'build' or not out.is_relative_to(ROOT / 'build'):
        raise ValueError('fresh output strictly beneath build required')
    report_path = conversion / 'report.json'
    report = json.loads(report_path.read_text(encoding='utf-8'))
    if not report.get('passed') or not report['input_stability']['at_end']:
        raise ValueError('successful stable current native build required')
    for name, expected in report['input_pins'].items():
        if sha(ROOT / name) != expected:
            raise ValueError('native build input changed: ' + name)
    service = next(r for r in report['native_services']
                   if r['source'] == 'portable/whole_program/platform/handles.c')
    source = (ROOT / service['source']).resolve()
    if not service['compile']['passed'] or Path(service['generated']).resolve() != source:
        raise ValueError('whole current native provider required')
    cmd = service['compile']['command']
    gcc, flags = Path(cmd[0]), cmd[1:cmd.index('-c')]
    fixture = Path(__file__).with_suffix('.c')
    header = ROOT / 'portable/whole_program/platform/handles.h'
    pins = {str(p): sha(p) for p in (report_path, source, header, fixture,
                                   Path(__file__).resolve(), gcc)}
    out.mkdir(parents=True)
    commands, objects = [], []
    for name, path in (('provider', source), ('fixture', fixture)):
        obj = out / (name + '.o')
        command = [str(gcc), *flags, '-c', str(path), '-o', str(obj)]
        ran = subprocess.run(command, capture_output=True, text=True)
        commands.append({'command': command, 'exit_code': ran.returncode})
        if ran.returncode:
            raise ValueError(ran.stderr)
        objects.append(obj)
    executable = out / 'native-discard.exe'
    command = [str(gcc), *map(str, objects), '-o', str(executable)]
    linked = subprocess.run(command, capture_output=True, text=True)
    commands.append({'command': command, 'exit_code': linked.returncode})
    if linked.returncode:
        raise ValueError(linked.stderr)
    ran = subprocess.run([str(executable)], capture_output=True, text=True)
    rows = ran.stdout.splitlines()
    checks = {'run_completed': ran.returncode == 0,
              'discarded_metadata_retained': rows[:1] == ['discarded,5,5,160,32'],
              'discarded_resize_refused': rows[1:] == ['resize,0,1,6,5'],
              'inputs_unchanged': all(sha(Path(p)) == pin for p, pin in pins.items())}
    receipt = {'schema': 'simant-native-discard-contrast-v1', 'passed': all(checks.values()),
               'checks': checks, 'observed_rows': rows, 'input_pins': pins,
               'build_input_count': len(report['input_pins']), 'commands': commands,
               'provider_object_sha256': sha(objects[0]), 'executable_sha256': sha(executable),
               'classification': 'SEMANTIC / PORT-BLOCKING',
               'scope': 'Current whole native provider retains discarded sizes and refuses resize. '
                        'Compare original bounded allocator history in the adjacent review. '
                        'Passing this discrepancy replay does not establish native equivalence '
                        'or ordinary gameplay reachability.'}
    (out / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'passed': receipt['passed'], 'checks': checks, 'rows': rows}))
    return int(not receipt['passed'])


if __name__ == '__main__':
    raise SystemExit(main())
