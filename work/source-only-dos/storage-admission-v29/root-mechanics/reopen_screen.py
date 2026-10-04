"""Root reopens saved test-owned screen artifacts against independent policy."""
from pathlib import Path
import hashlib
import json
import re
import sys
ROOT = Path(__file__).resolve().parents[3]
WORK = ROOT / 'build/workers/dos_screen_list_initializer_v35'
sys.path.insert(0, str(ROOT / 'tools'))
from omf import OmfReader
import dos_storage_contracts
from screen_policy import policy

def pin(path):
    path = path.resolve()
    raw = path.read_bytes()
    return dict(path=path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else str(path),
                sha256=hashlib.sha256(raw).hexdigest(), size=len(raw))

def pins(value):
    if isinstance(value, dict):
        if isinstance(value.get('path'), str) and isinstance(value.get('sha256'), str):
            yield value
        for child in value.values():
            yield from pins(child)
    elif isinstance(value, list):
        for child in value:
            yield from pins(child)

def path_for(value):
    path = Path(value)
    path = path if path.is_absolute() else ROOT / path
    assert not (path.is_relative_to(ROOT / 'assets') and path.suffix.lower() == '.exe'), path
    return path

def public_sections(raw):
    sections = {'Name': {}, 'Value': {}}
    counts = dict.fromkeys(sections, 0)
    current = None
    for line in raw.decode('latin1').splitlines():
        for name in sections:
            if 'Publics by ' + name in line:
                current = name
                counts[name] += 1
                break
        else:
            if current:
                match = re.match(r'^\s*([0-9a-fA-F]{4}:[0-9a-fA-F]{4})\s+(?:(?:Res|Abs|Ovl)\s+)?(\S+)\s*$', line)
                if match:
                    address, symbol = match.groups()
                    symbol = symbol.casefold()
                    assert symbol not in sections[current], symbol
                    sections[current][symbol] = address.upper()
    assert counts == {'Name': 1, 'Value': 1}
    assert sections['Name'] == sections['Value'] and sections['Name']
    return sections, counts

def shape(obj):
    return dict(module_name=obj.name, communals=obj.communals, publics=obj.publics,
        externals=obj.externals, segment_lengths=obj.segment_lengths,
        initialized_data_hex={name: raw.hex() for name, raw in obj.segments.items()},
        linker_fixups=obj.linker_fixups, groups=obj.groups, segment_defs=obj.segment_defs,
        external_scopes=obj.external_scopes, local_publics=obj.local_publics,
        local_externals=obj.local_externals, fixups=obj.fixups)

def main():
    candidate_path = Path(sys.argv[1])
    candidate = json.loads(candidate_path.read_bytes())
    literal = policy()
    assert candidate['root_reviewed'] is False
    checked = {}
    drift = []
    for row in pins(candidate):
        path = path_for(row['path'])
        key = (str(path), row['sha256'])
        if key in checked:
            continue
        actual = pin(path)
        if actual['sha256'] != row['sha256']:
            assert actual['path'] in ('tools/source_only_dos.py', 'tools/dos_source_bindings.py'), row
            drift.append(dict(historical_pin=row, current_pin=actual))
        else:
            assert 'size' not in row or row['size'] == actual['size'], row
        checked[key] = actual
    controls = {}
    for name, rule in literal['compiler_controls'].items():
        path = WORK / 'probe-run-v3/objects' / (rule['module_name'][:-2] + '.OBJ')
        obj = OmfReader(communals=True).read(path.read_bytes())
        observed = shape(obj)
        assert all(candidate['compiler_controls'][name].get(key) == value for key, value in observed.items()), name
        controls[name] = dict(pin=pin(path), shape=observed, groups=obj.groups, segments=obj.segment_defs)
    for row in candidate['cases']:
        run = path_for(row['raw']['artifact_pin']['path']).read_bytes()
        assert run.hex() == row['raw']['hex']
        link = path_for(row['link_pin']['path']).read_bytes().decode('latin1')
        assert not re.search(r'\b(?:warnings?|errors?|fatal|undefined|unresolved|aborted)\b|cannot\s+open', link, re.I)
        matrix, counts = public_sections(path_for(row['map_pin']['path']).read_bytes())
        recorded = {key: {name.casefold(): address.upper() for name, address in section.items()}
                    for key, section in row['public_address_matrix'].items()}
        assert matrix == recorded
        assert all(row['map_sections'][name]['public_count'] == len(matrix[name]) for name in counts)
    dos_storage_contracts.validate(dict(candidate, root_reviewed=True, all_required_checks_pass=True), literal)
    result = dict(schema='simant-root-screen-raw-review-v29', root_reviewed=True,
        admitted=False, candidate=pin(candidate_path), independent_policy=pin(Path(__file__).parent / 'screen_policy.py'),
        immutable_pin_count=len(checked), input_pins=list(checked.values()),
        historical_observation_drift=drift,
        case_count=len(candidate['cases']), actual_controls=controls,
        complete_raw_and_both_public_tables=True, original_executable_opened=False)
    out = Path(__file__).parent / 'screen-raw-review.json'
    out.write_bytes((json.dumps(result, indent=2) + '\n').encode())
    print('SCREEN RAW REVIEW PASS:', len(checked), 'pins,', len(candidate['cases']), 'cases,', len(controls), 'controls')

if __name__ == '__main__':
    main()
