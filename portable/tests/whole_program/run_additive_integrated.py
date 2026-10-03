"""Run existing bounded consumer controls on the centrally selected V5 state.

The legacy diagnostic runners and their receipts remain unchanged. This run
uses the central generated source and exact emitted owner header/C, with no
second source conversion. Host callbacks remain controlled by those runners.
"""
from pathlib import Path
import argparse
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from portable.whole_program.conversions import source_bounded_additive as selected
from portable.whole_program.conversions import source_bounded_save_probe_v5 as save
from portable.whole_program.conversions import source_bounded_consumer_probe_v5 as lion


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    out = (ROOT / args.out).resolve()
    if not out.is_relative_to(ROOT / 'build/workers') or out.exists():
        raise ValueError('a new scratch output directory is required')
    gen = ROOT / 'build/workers/whole_program/generated'
    report = json.loads((gen / 'migration.json').read_text())
    if not report['inputs_stable'] or report['compile_pass_count'] != 97:
        raise ValueError('current complete mechanical source build required')
    for rel, digest in report['inputs'].items():
        if sha(ROOT / rel) != digest:
            raise ValueError(f'central input changed: {rel}')
    plan = selected.load_plan()
    header, source = selected.render_owners(plan)
    if header != (gen / 'source_bounded_additive.h').read_text() or \
            source != (gen / 'source_bounded_additive.c').read_text():
        raise ValueError('central additive owners do not reproduce selected proposal')
    out.mkdir(parents=True)
    # A second adaptation would both hide stale generation and rebind names.
    # Require the selected include, then pass the already adapted TU verbatim.
    def already_selected(text, rel, unused_plan):
        if '#include "source_bounded_additive.h"' not in text:
            raise ValueError(f'central V5 source not selected: {rel}')
        return text, None
    for runner, name in ((save, 'save'), (lion, 'lion')):
        runner.WORK = out / name
        runner.REPORT = out / (name + '.json')
        runner.adapt = already_selected
        runner.render_owners = selected.render_owners
        original_run = runner.run
        def run_with_current_crt(command, original_run=original_run):
            if '-Wl,--gc-sections' in command:
                command = [*command, str(ROOT / 'portable/whole_program/platform/crt_abi.c')]
            return original_run(command)
        runner.run = run_with_current_crt
        runner.main()
    inputs = {rel: sha(ROOT / rel) for rel in (
        'portable/tests/whole_program/run_additive_integrated.py',
        'portable/whole_program/conversions/source_bounded_additive.py',
        'portable/whole_program/conversions/source_bounded_save_probe_v5.py',
        'portable/whole_program/conversions/source_bounded_consumer_probe_v5.py',
        'portable/whole_program/platform/crt_abi.c',
        'portable/whole_program/platform/crt_abi.h')}
    summary = {'status': 'PASS_BOUNDED_CENTRAL_NATIVE_STATE',
        'claim': 'Actual centrally generated AddAntLion and SaveGame consumers use the same selected native owners',
        'inputs': inputs, 'migration_sha256': sha(gen / 'migration.json'),
        'receipts': {name: sha(out / (name + '.json')) for name in ('save', 'lion')},
        'limits': ['SaveRec table reduced to the 13 original V5 rows',
                  'Controlled file/dialog/map host boundaries',
                  'No full save/load or whole-game acceptance']}
    (out / 'report.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(summary['status'])


if __name__ == '__main__':
    main()
