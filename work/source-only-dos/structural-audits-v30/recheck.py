"""Read-only archive and static-input check; never repin historical observations."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent

def check(row):
    path = ROOT / row['path']
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    assert actual == row['sha256'], row['path']
    size = row.get('size', row.get('size_bytes'))
    if size is not None:
        assert path.stat().st_size == size, row['path']

def main():
    index = json.loads((HERE / 'archive-index.json').read_bytes())
    assert index['root_reviewed'] is True and index['production_admission'] is False
    for row in index['files']:
        check(row['preserved'])
        assert row['original']['sha256'] == row['preserved']['sha256']
    for row in index['root_reviews']:
        check(row)
    for row in index['intermediate_script_snapshots']:
        check(row['preserved'])
    ss = json.loads((HERE / 'mono-entry-ss-v32/receipt.json').read_bytes())
    correction = json.loads((HERE / 'mono-entry-ss-v32/correction-addendum-v1.json').read_bytes())
    check(dict(path=(HERE / 'mono-entry-ss-v32/receipt.json').relative_to(ROOT).as_posix(),
               sha256=correction['v32_receipt']['sha256']))
    assert correction['dispatch_direction']['call_edge'] == 'o12_384C_0B76 -> o12_384C_03D0'
    checked = set()
    drift = []
    def walk(value):
        if isinstance(value, dict):
            if 'path' in value and 'sha256' in value:
                key = (value['path'], value['sha256'])
                if key not in checked:
                    checked.add(key)
                    # Only local build/report observations can drift. The
                    # canonical/static source and admitted packet inputs stay
                    # actual hash checks at this review boundary.
                    if value['path'].replace('\\', '/').startswith('build/source-only-dos/'):
                        path = ROOT / value['path']
                        actual = hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None
                        if actual != value['sha256']:
                            drift.append(dict(path=value['path'], frozen=value['sha256'], current=actual))
                    else:
                        check(value)
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)
    walk(ss['evidence_pins'])
    walk(correction)
    data = json.loads((HERE / 'dgroup-56fe-v32/pins.json').read_bytes())
    walk(data['inputs'])
    frontier = json.loads((HERE / 'root-frontier-review.json').read_bytes())
    assert frontier['debt_discharged_bytes'] == 0 and frontier['new_provider_count'] == 0
    walk(frontier['effective_source_pins'])
    hotbox = json.loads((HERE / 'hotbox/root-semantic-review.json').read_bytes())
    assert hotbox['production_admission'] is False and hotbox['debt_discharged_bytes'] == 0
    assert hotbox['unexplained_field_bytes'] == 0 and sum(r['width'] for r in hotbox['fields']) == 18
    walk(hotbox['reopened_inputs'])
    print(json.dumps(dict(status='PASS', preserved_files=len(index['files']), checked_input_identities=len(checked),
                          historical_build_observation_drift=drift, debt_discharged_bytes=0,
                          production_admission=False), indent=2))

if __name__ == '__main__':
    main()
