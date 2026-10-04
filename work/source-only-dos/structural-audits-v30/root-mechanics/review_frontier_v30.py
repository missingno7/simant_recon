"""Root read-only checks for partial static frontier results, never owner admission."""
from pathlib import Path
import hashlib
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
from omf import OmfReader

def pin(path):
    return dict(path=path.relative_to(ROOT).as_posix(), sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                size=path.stat().st_size)

def check(row):
    actual = pin(ROOT / row['path'])
    assert actual['sha256'] == row['sha256'], row['path']
    if 'size' in row:
        assert actual['size'] == row['size'], row['path']
    if 'size_bytes' in row:
        assert actual['size'] == row['size_bytes'], row['path']

def main():
    report_path = ROOT / 'build/source-only-dos/build-report.json'
    report = json.loads(report_path.read_bytes())
    assert len(report['translation_units']) == 188
    scan = []
    generated_pins = []
    for row in report['translation_units']:
        source = row['generated_source']
        check(source)
        generated_pins.append(source)
        for number, line in enumerate((ROOT / source['path']).read_text(encoding='latin1').splitlines(), 1):
            instruction = line.split(';', 1)[0] if row['lang'] == 'asm' else line
            if re.search(r'(?i)\b(?:mov\s+ss\s*,|pop\s+ss\b|lss\b)', instruction):
                scan.append(dict(module=row['module'], line=number, instruction=instruction.strip()))
    assert len(scan) == 12 and {r['module'] for r in scan} == {'root:1B73', 'root:28BC'}
    ss_path = ROOT / 'build/workers/dos_mono_8ed8_owner_v32/receipt.json'
    ss = json.loads(ss_path.read_bytes())
    for row in ss['evidence_pins']:
        check(row)
    data_path = ROOT / 'build/workers/dos_dgroup_56fe_owner_v32/pins.json'
    data = json.loads(data_path.read_bytes())
    for row in data['inputs'] + data.get('artifacts', []):
        check(row)
    objects = {}
    for module, expected_data_size in [('root:195A', 28), ('root:1E57', 806)]:
        row = next(r for r in report['translation_units'] if r['module'] == module)
        check(row['object'])
        obj = OmfReader(communals=True).read((ROOT / row['object']['path']).read_bytes())
        assert obj.segment_lengths['_DATA'] == expected_data_size
        if module == 'root:1E57':
            assert [p for p in obj.publics if p['name'] == '_g_5702'] == [dict(name='_g_5702', segment='_DATA', offset=0)]
        objects[module] = dict(object=row['object'], data_size=expected_data_size)
    result = dict(schema='simant-root-static-frontier-review-v30', root_reviewed=True,
        production_admission=False, new_provider_count=0, debt_discharged_bytes=0,
        current_report=pin(report_path), effective_source_count=len(generated_pins),
        effective_source_pins=generated_pins, ss_mutators=scan,
        ss_receipt=pin(ss_path), ss_input_count=len(ss['evidence_pins']),
        data_receipt=pin(data_path), data_input_count=len(data['inputs']), objects=objects,
        limits='Entry-SS proof is separate from the four ADD operand bindings, buffer extent and index bounds. '
               'The 56FE immediate EMS selector excludes that heuristic owner route, not computed pointers. '
               'The v32 arrow direction needs its disclosed correction before an entry-path admission.')
    out = ROOT / 'work/source-only-dos/structural-audits-v30/root-frontier-review.json'
    assert not out.exists()
    out.write_bytes((json.dumps(result, indent=2)+'\n').encode())
    print('ROOT FRONTIER REVIEW PASS:', len(generated_pins), 'effective sources;', len(scan), 'SS writes; no owner/debt admission')

if __name__ == '__main__':
    main()
