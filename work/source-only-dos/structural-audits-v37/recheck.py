"""Read-only research byte integrity; no build/semantic acceptance."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
index=json.loads((HERE/'preservation-index.json').read_bytes())

def matches(row):
    path=Path(row['path'])
    path=path if path.is_absolute() else ROOT/path
    return path.is_file() and path.stat().st_size==row['size'] and hashlib.sha256(path.read_bytes()).hexdigest()==row['sha256']

errors,drift=[],[]
for row in index['copies']:
    if not matches(row['archived']) or row['original']['sha256']!=row['archived']['sha256']:
        errors.append(row['archived']['path'])
    if not matches(row['original']):drift.append(row['original']['path'])
for row in index['archive_only']:
    if not matches(row):errors.append(row['path'])
context=json.loads((HERE/'context.json').read_bytes())
assert not context['provider_admitted'] and not context['canonical_or_production_changed']
assert (context['compiled_TUs'],context['unresolved_imports'],context['functional_data_bytes'],
        context['historical_data_bytes'],context['open_layout_gates'])==(190,12,44,113,10)
print(json.dumps(dict(status='FAIL' if errors else 'PASS',copies_checked=len(index['copies']),
    archive_errors=errors,later_scratch_drift=drift),indent=2))
raise SystemExit(bool(errors))
