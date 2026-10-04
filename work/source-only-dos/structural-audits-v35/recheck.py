"""Read-only archived byte identities; no compile/link/runtime acceptance."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
index = json.loads((HERE/'preservation-index.json').read_bytes())
def matches(row):
    path = ROOT/row['path']
    return (path.is_file() and path.stat().st_size == row['size']
            and hashlib.sha256(path.read_bytes()).hexdigest() == row['sha256'])
errors, drift = [], []
for row in index['copies']:
    if (not matches(row['archived'])
            or row['original']['sha256'] != row['archived']['sha256']):
        errors.append(row['archived']['path'])
    if not matches(row['original']): drift.append(row['original']['path'])
for row in index['archive_only']:
    if not matches(row): errors.append(row['path'])
for row in index['observations']:
    if not matches(row): drift.append(row['path'])
context = json.loads((HERE/'context.json').read_bytes())
assert (context['compiled_translation_units'],context['unresolved_imports'],
        context['functional_data_bytes'],context['historical_data_bytes'],
        context['open_layout_gates']) == (188,15,46,113,8)
assert context['function_dispositions']['BEHAVIOR_EXACT_CONFIRMED'] == 29
assert not any(context['original_exe_bytes_used'].values())
assert context['denied_oracle_reads'] == []
assert not context['new_source_admission'] and not context['new_layout_admission']
print(json.dumps(dict(status='FAIL' if errors else 'PASS',
    archive_pins_checked=len(index['copies'])+len(index['archive_only']),
    archive_errors=errors,later_local_observations=drift),indent=2))
raise SystemExit(bool(errors))
