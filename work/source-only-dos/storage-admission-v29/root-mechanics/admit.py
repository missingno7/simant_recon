"""Root admission after independent literal, raw and fresh-object reviews."""
from pathlib import Path
import json
import sys
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
import dos_source_bindings as bindings
import dos_storage_policies_v29 as policies
import dos_storage_contracts as gate
from reopen_screen import pin

SCREEN = ROOT / 'build/workers/dos_screen_list_initializer_v35'
SPECS = {
    'screen': ('screen-clip-list', 'screen_clip_list_contract',
        SCREEN / 'storage-contract-candidate-v2.json', SCREEN / 'probe-v3.py'),
}

def write(path, value):
    path.write_bytes((json.dumps(value, indent=2) + '\n').encode())

def copy(path, destination):
    if destination.exists():
        assert destination.read_bytes() == path.read_bytes(), destination
    else:
        destination.write_bytes(path.read_bytes())
    return pin(destination)

def main():
    words_candidate = Path(sys.argv[1])
    SPECS['words'] = ('remaining-far-state-words', 'remaining_far_state_words_contract',
        words_candidate, ROOT / 'build/workers/dos_readonly_word_owners_v35/word-owners-v35.py')
    base = ROOT / 'work/source-only-dos'
    archive = base / 'storage-admission-v29'
    archive.mkdir(exist_ok=True)
    screen_candidate = json.loads(SPECS['screen'][2].read_bytes())
    sources = screen_candidate['accepted_source_census']['files']
    assert len(sources) == 156
    for label, (short, key, candidate_path, probe_path) in SPECS.items():
        module = 'source-owned:' + short
        candidate = json.loads(candidate_path.read_bytes())
        assert candidate['root_reviewed'] is False
        raw_review_path = Path(__file__).parent / (label + '-raw-review.json')
        raw_review = json.loads(raw_review_path.read_bytes())
        assert raw_review['candidate'] == pin(candidate_path) and raw_review['root_reviewed'] is True
        fresh_path = Path(__file__).parent / ('fresh-' + label) / 'compile-receipt.json'
        fresh = json.loads(fresh_path.read_bytes())
        descriptor = fresh['provider']
        assert descriptor['module'] == module
        directory = archive / label
        directory.mkdir(exist_ok=True)
        evidence = [copy(candidate_path, directory / 'worker-candidate.json'),
            copy(raw_review_path, directory / 'root-raw-review.json'),
            copy(Path(__file__).parent / (label + '-literal-policy.json'), directory / 'independent-literal-policy.json'),
            copy(fresh_path, directory / 'fresh-compile.json'),
            copy(probe_path, directory / 'historical-probe.py')]
        if label == 'words':
            for source in (
                ROOT / 'build/workers/dos_readonly_word_closure_v34/review-v34.md',
                ROOT / 'build/workers/dos_readonly_word_closure_v34/receipt-v34.json',
                ROOT / 'build/workers/dos_readonly_word_closure_v34/frame-sweep-v34.json',
                candidate_path.parent / 'runs/20261004T111916Z_f8ef4adc/addendum-v35.md',
                candidate_path.parent / 'runs/20261004T111916Z_f8ef4adc/storage-contract.json'):
                evidence.append(copy(source, directory / source.name))
        provider = base / 'providers' / (short + '.c')
        descriptor['source'] = copy(ROOT / descriptor['source']['path'], provider)
        evidence.append(descriptor['source'])
        bindings.review_provider_source(provider.read_text(encoding='ascii'), descriptor,
            json.loads((ROOT / 'layout/symbols.json').read_bytes()))
        contract = {k: candidate[k] for k in ('module', 'communals', 'required_cases', 'inputs',
            'cases', 'compiler_controls', 'save_rec_pointer_fixups')}
        contract.update(schema='simant-root-source-storage-contract-v29', root_reviewed=True,
            all_required_checks_pass=True, admitted=True,
            historical_producer_or_placement_claimed=False, game_lifecycle_claimed=False,
            original_game_bytes_used=0, raw_candidate=evidence[0])
        # The probe pin is explicit; the provider pin above is a separate input.
        contract['probe_source'] = pin(directory / 'historical-probe.py')
        contract['compiler_controls'] = {name: dict(facts['shape'], object_pin=facts['pin'])
            for name, facts in raw_review['actual_controls'].items()}
        for row in contract['cases']:
            row['passed'] = (row['expected'] == row['actual'] == contract['required_cases'][row['case']]
                and row['runner_exit'] == 0 and row['timed_out'] is False and row['clean'] is True
                and row['linker_diagnostics'] == [] and row['linker_produced_executable'] is True
                and row['linker_produced_map'] is True)
        if label == 'screen':
            contract['public_DATA'] = bindings.initialized_publics(module)
        gate.validate(contract, policies.policy(module))
        acceptance = dict(schema='simant-root-storage-acceptance-v29', root_reviewed=True,
            module=module, provider=descriptor, fresh_whole_object=fresh['verification'],
            raw_review=evidence[1], literal_policy=evidence[2], source_census=sources,
            original_game_bytes_used=0, historical_data_debt_modified=False,
            source_extent_basis=(
                'Four signed Rect fields; eight-byte stepping; first screen record and copied full sentinel; '
                'source consumers and approved semantic initial values. Symbolic g574E handle and +4/+6 word views.'
                if label == 'screen' else
                'Five complete signed-word access paths; full original/current direct/frame review, '
                'source-bound neighboring arrays and counters, no containing SaveRec/view owner. '
                'Natural mutable two-byte definitions preserve known zero startup; no guessed nonzero producer.'),
            scope_limit='Functional source objects/views only. Historical TU/order/placement, designer intent, '
                'arbitrary resource values, full-game clobber and first-use lifetime remain unclaimed; '
                'existing independent layout gates stay open.')
        write(directory / 'root-acceptance.json', acceptance)
        evidence.append(pin(directory / 'root-acceptance.json'))
        contract_path = base / (short + '-contract-v1.json')
        assert not contract_path.exists(), contract_path
        write(contract_path, contract)
        packet = dict(schema='simant-dos-reviewed-storage-bindings-v29',
            category='REVIEWED_SOURCE_STORAGE_BINDING', root_reviewed=True, bindings=[],
            providers=[descriptor], review_sources=evidence + sources,
            runtime_contract=pin(contract_path), runtime_contract_key=key)
        if label == 'screen':
            packet['initialized_aliases'] = bindings.SCREEN_LIST_ALIASES
        write(base / (short + '-bindings-v1.json'), packet)
        print(module, 'ADMITTED:', len(contract['cases']), 'raw controls; fresh whole object verified')

if __name__ == '__main__':
    main()
