"""Root read-only recheck of the three preserved source-built owner cohorts."""
from pathlib import Path
import hashlib
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
from omf import OmfReader

CANDIDATES = {
 'strings': ('build/workers/dos_remaining_string_pointer_owners_v23/storage-contract-candidate-v23.json', '94736cc423e620781304d910f70f576b1f84e0b4508b4632a28b6e51b3926cb9'),
 'scalars': ('build/workers/dos_yard_init_scalars_v23/generic-contract-candidate-v23.json', '138bf8a8f3078708eff284ab839aa1e502f243927fb3b78d7caa1bd6674518bf'),
 'arrays': ('build/workers/dos_yard_reset_arrays_v23/yard-array-owner-contract-candidate-v23.json', '92873a1d25719ab75930a080db58553a445ee79f9bec63c1e1bef56789c40221'),
}
# Historical observations retain their old digests. These files are never
# compiler/linker/runtime identities and never become current build inputs.
MUTABLE = {'tools/source_only_dos.py', 'tools/dos_source_bindings.py',
           'build/source-only-dos/build-report.json', 'work/source-only-dos/current-intake.json'}

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def path_for(value):
    path = Path(value.replace('\\', '/'))
    return path if path.is_absolute() else ROOT / path

def pins(value):
    if isinstance(value, dict):
        if isinstance(value.get('path'), str) and isinstance(value.get('sha256'), str):
            yield value
        for item in value.values():
            yield from pins(item)
    elif isinstance(value, list):
        for item in value:
            yield from pins(item)

def public_sections(raw):
    sections = {'Name': {}, 'Value': {}}
    counts = {'Name': 0, 'Value': 0}
    section = None
    for line in raw.decode('latin1').splitlines():
        for name in sections:
            if 'Publics by ' + name in line:
                section = name
                counts[name] += 1
                break
        else:
            if section:
                match = re.match(r'^\s*([0-9a-fA-F]{4}:[0-9a-fA-F]{4})\s+(?:(Abs|Res|Ovl)\s+)?(\S+)\s*$', line)
                if match:
                    address, kind, name = match.groups()
                    assert name.lower() not in sections[section], (section, name)
                    sections[section][name.lower()] = address.upper()
    assert counts == {'Name': 1, 'Value': 1}, counts
    assert sections['Name'] and sections['Name'] == sections['Value']
    return sections, counts

def shape(obj):
    # Data-only fixtures carry full initializer bytes; consumer code is not
    # reproduced in this receipt. Its symbolic fixups remain inspectable.
    return {'module_name': obj.name, 'communals': obj.communals,
            'publics': obj.publics, 'externals': obj.externals,
            'segment_lengths': obj.segment_lengths,
            'linker_fixups': obj.linker_fixups,
            'initialized_data_hex': {k: v.hex() for k,v in obj.segments.items()
                if not any(s['name'] == k and s['class'] == 'CODE' for s in obj.segment_defs)}}

def review(label):
    name, expected = CANDIDATES[label]
    raw = (ROOT / name).read_bytes()
    assert digest(raw) == expected, name
    wrapper = json.loads(raw)
    contract = wrapper.get('contract', wrapper)
    assert contract['root_reviewed'] is False
    unique, drift, objects = {}, [], {}
    for row in pins(wrapper):
        path = path_for(row['path'])
        key = (str(path), row['sha256'])
        if key in unique:
            continue
        data = path.read_bytes()
        actual = digest(data)
        relative = path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else str(path)
        if actual != row['sha256']:
            assert relative in MUTABLE, (row['path'], row['sha256'], actual)
            drift.append({'historical_pin': row, 'current_sha256': actual,
                          'role': 'historical observation only, not repinned'})
        else:
            assert 'size' not in row or len(data) == row['size'], row['path']
        unique[key] = row
        if path.suffix.lower() == '.obj':
            objects[relative] = shape(OmfReader(communals=True).read(data))
    names = {c['name'].lower() for c in contract['communals']}
    cases = []
    for row in contract['cases'] + contract.get('diagnostic_cases', []):
        artifacts = row.get('artifact_pins', {})
        rp = row.get('run_log_pin', artifacts.get('run_log'))
        lp = row.get('link_log_pin', artifacts.get('link_log'))
        mp = row.get('map_input_pin', artifacts.get('map'))
        run = path_for(rp['path']).read_bytes()
        expected_raw = (row['expected'] + '\r\n').encode('ascii')
        assert run == expected_raw, (label, row['linker'], row['case'], run)
        link = path_for(lp['path']).read_bytes().decode('latin1')
        assert not re.search(r'\b(?:warnings?|errors?|fatal|undefined|unresolved|aborted)\b|cannot\s+open', link, re.I), lp
        matrix, counts = public_sections(path_for(mp['path']).read_bytes())
        assert names <= matrix['Name'].keys(), (label, row['case'])
        assert row['passed'] is True and row['timed_out'] is False
        cases.append({'linker': row['linker'], 'case': row['case'],
            'result': row['expected'], 'gating': row in contract['cases'],
            'raw': {'hex':run.hex(),'sha256':digest(run),'size':len(run),'artifact_pin':rp},
            'map_sections': {s: {'heading_present':True,'heading_count':counts[s],
                                'public_count':len(matrix[s])} for s in matrix},
            'public_address_matrix':matrix,'run_pin':rp,'link_pin':lp,'map_pin':mp})
    observed = {(r['linker'],r['case']) for r in cases if r['gating']}
    assert observed == {(p,c) for p in ('rtlink400','rtlink610') for c in contract['required_cases']}
    result = {'schema':'simant-root-raw-owner-review-v24','candidate':name,
        'candidate_sha256':expected,'module':wrapper['module'],
        'immutable_pin_count':len(unique)-len(drift),'historical_drift':drift,
        'cases':cases,'objects':objects,'claim':'Raw source-built evidence rechecked; admission separately required.'}
    output = ROOT / 'build/workers/dos_v24_preserved_raw_recheck'
    output.mkdir(parents=True, exist_ok=True)
    dest = output / (label+'-raw-review.json')
    dest.write_bytes((json.dumps(result,indent=2)+'\n').encode())
    print(label, 'PASS', len(unique)-len(drift), 'immutable pins;',len(cases),
          'full RUN/LINK/MAP pairs;', len(objects), 'actual OMF objects;', len(drift),'historical observations')

if __name__ == '__main__':
    for label in CANDIDATES:
        review(label)
