"""Read-only preservation check; historical input drift never updates frozen pins."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent

def check_pin(row):
    path = ROOT / row['path']
    assert path.is_file(), row['path']
    assert hashlib.sha256(path.read_bytes()).hexdigest() == row['sha256'], row['path']
    if 'size' in row:
        assert path.stat().st_size == row['size'], row['path']

def main():
    index = json.loads((HERE / 'archive-index.json').read_bytes())
    assert index['root_reviewed'] is True and index['production_admission'] is False
    assert index['root_fheap_controls_review']['reopened_link_maps'] == 10
    preserved = {r['original']['path']: r['preserved'] for r in index['files']}
    for row in index['files']:
        check_pin(row['preserved'])
        assert row['original']['sha256'] == row['preserved']['sha256']
        assert Path(row['preserved']['path']).suffix.lower() not in {'.exe', '.obj', '.lib'}
    mechanics = json.loads((HERE.parent / 'storage-admission-v29/root-mechanics/index.json').read_bytes())
    assert mechanics['production_input'] is False
    for row in mechanics['files']:
        check_pin(row['preserved'])
        assert row['original']['sha256'] == row['preserved']['sha256']
    mono = json.loads((HERE / 'mono-owner-v31/receipt.json').read_bytes())
    assert mono['review_status'] == 'ROOT_FALSE_UNRESOLVED'
    assert mono['result']['extent_bytes'] is None and mono['result']['fixed_placement_admitted'] is False
    correction = json.loads((HERE / 'mono-owner-v31/pin-correction-addendum-v1.json').read_bytes())
    assert correction['status'] == 'ADDENDUM_ONLY_ORIGINAL_RECEIPT_UNCHANGED'
    assert correction['receipt']['sha256'] == preserved[correction['receipt']['path']]['sha256']
    corrected = {r['path']: r for r in correction['discrepancies'] if 'actual_sha256' in r}
    assert set(corrected) == {'work/source-only-dos/driver-ss-frame-bindings-v1.json'}
    historical_drift = []
    for row in mono['evidence_pins']:
        if row['path'] in preserved:
            assert row['sha256'] == preserved[row['path']]['sha256']
        elif row['path'] == 'work/source-only-dos/current-intake.json':
            path = ROOT / row['path']
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
            if actual != row['sha256']:
                historical_drift.append(dict(path=row['path'], frozen=row['sha256'], current=actual))
        elif row['path'] in corrected:
            fixed = corrected[row['path']]
            assert row['sha256'] == fixed['recorded_sha256'] and len(row['sha256']) == 63
            check_pin(dict(path=row['path'], sha256=fixed['actual_sha256']))
        else:
            check_pin(row)
    print(json.dumps(dict(status='PASS', archived_files=len(index['files']),
                          root_mechanics=len(mechanics['files']),
                          historical_observation_drift=historical_drift,
                          disclosed_pin_corrections=len(corrected),
                          production_admission=False), indent=2))

if __name__ == '__main__':
    main()
