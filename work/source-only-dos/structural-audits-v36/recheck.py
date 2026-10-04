"""Read-only byte preservation and recorded context; no semantic acceptance."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]

def matches(row):
    path = Path(row['path'])
    path = path if path.is_absolute() else ROOT / path
    return (path.is_file() and path.stat().st_size == row['size']
            and hashlib.sha256(path.read_bytes()).hexdigest() == row['sha256'])

preserved = json.loads((HERE / 'preservation-index.json').read_bytes())
accepted = json.loads((HERE / 'acceptance-index.json').read_bytes())
errors, drift = [], []
for row in preserved['files']:
    if (not matches(row['archived'])
            or row['original']['sha256'] != row['archived']['sha256']
            or row['original']['size'] != row['archived']['size']):
        errors.append(row['archived']['path'])
    if not matches(row['original']):
        drift.append(row['original']['path'])
for row in accepted['files']:
    if not matches(row):
        errors.append(row['path'])
context = json.loads((HERE / 'context.json').read_bytes())
assert (context['compiled_TUs'], context['source_providers'], context['unresolved_imports'],
        context['functional_data_bytes'], context['historical_data_bytes'],
        context['aliases'], context['open_layout_gates']) == (190, 63, 12, 44, 113, 193, 10)
assert context['strict_behavior_confirmed'] == 29
assert not any(context['original_build_bytes'].values())
assert context['guarded_reopen_denied_reads'] == []
assert not context['game_linked'] and not context['game_executed']
print(json.dumps(dict(status='FAIL' if errors else 'PASS',
    worker_copies_checked=len(preserved['files']), acceptance_pins_checked=len(accepted['files']),
    archive_errors=errors, later_local_observations=drift), indent=2))
raise SystemExit(bool(errors))
