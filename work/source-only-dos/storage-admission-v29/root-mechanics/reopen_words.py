"""Independent raw recheck of the final five-word candidate, without reruns."""
from pathlib import Path
import json
import re
import sys
from reopen_screen import ROOT, pin, pins, path_for, public_sections, shape, OmfReader
from word_policy import policy
import dos_storage_contracts

def main():
    path = Path(sys.argv[1])
    candidate = json.loads(path.read_bytes())
    assert candidate['root_reviewed'] is False
    checked, drift = {}, []
    for item in pins(candidate):
        actual_path = path_for(item['path'])
        key = (str(actual_path), item['sha256'])
        if key in checked:
            continue
        actual = pin(actual_path)
        if actual['sha256'] != item['sha256']:
            assert actual['path'] in ('tools/source_only_dos.py', 'tools/dos_source_bindings.py'), item
            drift.append(dict(historical_pin=item, current_pin=actual))
        else:
            assert actual['size'] == item['size'], item
        checked[key] = actual
    controls = {}
    for name in policy()['compiler_controls']:
        row = candidate['compiler_controls'][name]
        actual_path = path_for(row['object_pin']['path'])
        obj = OmfReader(communals=True).read(actual_path.read_bytes())
        observed = shape(obj)
        core = {key: observed[key] for key in ('module_name', 'communals', 'publics',
            'externals', 'segment_lengths', 'initialized_data_hex', 'linker_fixups')}
        core['communals'] = [{key: item[key] for key in ('name', 'kind', 'count', 'element_size', 'length')}
            for item in observed['communals']]
        assert all(row.get(key) == value for key, value in core.items()), name
        assert not obj.local_publics and not obj.local_externals and not obj.fixups
        assert obj.external_scopes == ['communal'] * len(obj.communals)
        assert all(item['type_index'] == 0 for item in obj.communals)
        controls[name] = dict(pin=pin(actual_path), shape=observed)
    for row in candidate['cases']:
        raw = path_for(row['raw']['artifact_pin']['path']).read_bytes()
        assert raw.hex() == row['raw']['hex']
        link = path_for(row['link_pin']['path']).read_bytes().decode('latin1')
        assert not re.search(r'\b(?:warnings?|errors?|fatal|undefined|unresolved|aborted)\b|cannot\s+open', link, re.I)
        matrix, counts = public_sections(path_for(row['map_pin']['path']).read_bytes())
        recorded = {key: {name.casefold(): address.upper() for name, address in section.items()}
                    for key, section in row['public_address_matrix'].items()}
        assert matrix == recorded
        assert all(row['map_sections'][name]['public_count'] == len(matrix[name]) for name in counts)
    count = dos_storage_contracts.validate(dict(candidate, root_reviewed=True, all_required_checks_pass=True), policy())
    result = dict(schema='simant-root-far-words-raw-review-v29', root_reviewed=True, admitted=False,
        candidate=pin(path), independent_policy=pin(Path(__file__).parent / 'word_policy.py'),
        immutable_pin_count=len(checked) - len(drift), historical_observation_drift=drift,
        input_pins=list(checked.values()), case_count=count, actual_controls=controls,
        complete_raw_and_both_public_tables=True, original_executable_opened=False)
    (Path(__file__).parent / 'words-raw-review.json').write_bytes((json.dumps(result, indent=2) + '\n').encode())
    print('FAR WORD RAW REVIEW PASS:', len(checked) - len(drift), 'pins,', count, 'cases, 4 controls')

if __name__ == '__main__':
    main()
