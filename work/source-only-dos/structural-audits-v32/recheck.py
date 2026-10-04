"""Read-only archive integrity check; does not repeat historical tool execution."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]

def matches(pin):
    path = ROOT / pin['path']
    return path.is_file() and path.stat().st_size == pin['size'] and hashlib.sha256(path.read_bytes()).hexdigest() == pin['sha256']

index = json.loads((HERE / 'preservation-index.json').read_bytes())
tail = json.loads((HERE / 'tail-preservation-index.json').read_bytes())
index['copies'] += tail['copies']
index['archive_only'] += tail['archive_only']
boundary = json.loads((HERE / 'boundary-preservation-index.json').read_bytes())
index['copies'] += boundary['copies']
index['archive_only'] += boundary['archive_only']
errors, observations = [], []
for row in index['copies']:
    if not matches(row['archived']):
        errors.append(row['archived']['path'])
    if row['archived']['sha256'] != row['original']['sha256']:
        errors.append('copy identity differs: ' + row['archived']['path'])
    if not matches(row['original']):
        observations.append(row['original']['path'])
for pin in index['archive_only']:
    if not matches(pin):
        errors.append(pin['path'])
for pin in index['observations']:
    if not matches(pin):
        observations.append(pin['path'])
context = json.loads((HERE / 'context.json').read_bytes())
assert (len(context['translation_units']), context['unresolved_imports'],
        context['functional_data_bytes'], context['historical_data_bytes'],
        context['open_layout_gates']) == (188, 15, 46, 113, 7)
assert not any(context['original_exe_bytes_used'].values())
assert context['standalone_dos_executable'] is False
assert not context['new_source_admission'] and not context['new_layout_admission']
assert context['function_dispositions']['BEHAVIOR_EXACT_CONFIRMED'] == 29
print(json.dumps(dict(status='FAIL' if errors else 'PASS',
    archive_pins_checked=len(index['copies']) + len(index['archive_only']),
    archive_errors=errors, later_local_observations=observations,
    scope='Preserved evidence integrity only; no compiler/linker/runtime replay or current-build acceptance.'), indent=2))
raise SystemExit(bool(errors))
