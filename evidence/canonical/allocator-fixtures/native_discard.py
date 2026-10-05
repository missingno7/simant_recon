"""Validate bounded discarded-size/restoration semantics in the whole native provider.

Compile current source and two source mutants with actual native build flags.
The adjacent original-instruction receipt supplies the DOS contrast. Host budget,
failure and live-resize controls do not establish complete DOS equality.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re
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
    original = fixture.parent / 'receipt.json'
    original_receipt = json.loads(original.read_text(encoding='utf-8'))
    for row in original_receipt['inputs']:
        if sha(ROOT / row['path']) != row['sha256']:
            raise ValueError('original proof input changed: ' + row['path'])
    dos = original_receipt['original_discarded_resize']
    if (dos['original_discarded_sizes'] != [0, 0]
            or dos['original_resize_return'] != dos['first_handle']
            or dos['resize_size_bytes'] != 100 or dos['resized_block_type'] != 1
            or dos['other_handle_type_after'] != 5 or dos['other_handle_discard_status_after'] != 1):
        raise ValueError('original bounded resize contrast missing')
    pins = {str(p): sha(p) for p in (report_path, source, header, fixture, original,
                                   Path(__file__).resolve(), gcc)}
    expected = set(re.findall(r'CHECK\("([^"]+)"', fixture.read_text(encoding='utf-8')))
    text = source.read_text(encoding='utf-8')
    edits = {
        'retained_size': [('oldest->size = oldest->charged = 0;', 'oldest->charged = 0;'),
                          ('s->size = s->charged = 0;\n s->type = SIM_HANDLE_DISCARDED;',
                           's->charged = 0;\n s->type = SIM_HANDLE_DISCARDED;')],
        'resize_rejected': [('was_discarded = s->type == SIM_HANDLE_DISCARDED;',
                            'was_discarded = s->type == SIM_HANDLE_DISCARDED;\n'
                            '    if (was_discarded) return set_status(m, SIM_HANDLE_DISCARDED_DATA);')]
    }
    out.mkdir(parents=True)
    runs = {}
    for name in ('current', *edits):
        provider = source
        if name != 'current':
            mutant = text
            for old, new in edits[name]:
                if mutant.count(old) != 1:
                    raise ValueError('unique negative control edit required: ' + name)
                mutant = mutant.replace(old, new)
            provider = out / (name + '.c')
            provider.write_text(mutant, encoding='utf-8')
        commands, objects = [], []
        for label, path in (('provider', provider), ('fixture', fixture)):
            obj = out / (name + '-' + label + '.o')
            command = [str(gcc), *flags, '-I', str(header.parent), '-c', str(path), '-o', str(obj)]
            ran = subprocess.run(command, capture_output=True, text=True)
            commands.append({'command': command, 'exit_code': ran.returncode})
            if ran.returncode:
                raise ValueError(ran.stderr)
            objects.append(obj)
        executable = out / (name + '.exe')
        command = [str(gcc), *map(str, objects), '-o', str(executable)]
        linked = subprocess.run(command, capture_output=True, text=True)
        commands.append({'command': command, 'exit_code': linked.returncode})
        if linked.returncode:
            raise ValueError(linked.stderr)
        ran = subprocess.run([str(executable)], capture_output=True, text=True)
        rows = re.findall(r'^check,([^,]+),([01])$', ran.stdout, re.M)
        checks = {label: value == '1' for label, value in rows}
        if set(checks) != expected or len(rows) != len(expected):
            raise ValueError('complete unique control ledger required: ' + name)
        runs[name] = {'exit_code': ran.returncode, 'checks': checks, 'stdout': ran.stdout,
                      'commands': commands, 'provider_sha256': sha(provider),
                      'provider_object_sha256': sha(objects[0]), 'executable_sha256': sha(executable)}
    checks = {'current_all_controls': runs['current']['exit_code'] == 0
                  and all(runs['current']['checks'].values()),
              'retained_size_negative_distinguished': runs['retained_size']['exit_code'] != 0
                  and not runs['retained_size']['checks']['public-discarded-sizes-zero']
                  and not runs['retained_size']['checks']['budget-discarded-sizes-zero'],
              'resize_rejection_negative_distinguished': runs['resize_rejected']['exit_code'] != 0
                  and not runs['resize_rejected']['checks']['public-resurrect-same-master'],
              'inputs_unchanged': all(sha(Path(p)) == pin for p, pin in pins.items())}
    receipt = {'schema': 'simant-native-discard-repair-v1', 'passed': all(checks.values()),
               'checks': checks, 'input_pins': pins, 'build_input_count': len(report['input_pins']),
               'original_bounded_observation': dos, 'control_count': len(expected), 'runs': runs,
               'scope': 'Zero public discarded size and same-slot restoration are corroborated. '
                        'Host budget/failure and existing live-resize controls are native regression checks. '
                        'No full heap-history, shared metadata, flags, paragraph-copy, DOS failure-policy '
                        'or ordinary gameplay reachability equivalence claim.'}
    (out / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'passed': receipt['passed'], 'checks': checks, 'control_count': len(expected)}))
    return int(not receipt['passed'])


if __name__ == '__main__':
    raise SystemExit(main())
