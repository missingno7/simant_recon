"""Read-only preservation check, not current compile/link/runtime acceptance."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]

def matches(row):
    path = ROOT / row['path']
    return path.is_file() and path.stat().st_size == row['size'] and hashlib.sha256(path.read_bytes()).hexdigest() == row['sha256']

index = json.loads((HERE / 'preservation-index.json').read_bytes())
errors, drift = [], []
for row in index['copies']:
    if not matches(row['archived']) or row['archived']['sha256'] != row['original']['sha256']:
        errors.append(row['archived']['path'])
    if not matches(row['original']):
        drift.append(row['original']['path'])
for row in index['archive_only']:
    if not matches(row):
        errors.append(row['path'])
for row in index['observations']:
    if not matches(row):
        drift.append(row['path'])
review = json.loads((HERE / 'root-review.json').read_bytes())
assert review['verified_view']['initialized_values'] == [0, 1, 1, 1, 1, 0]
assert review['existing_storage']['segment_length'] == 3162
assert not review['new_source_or_layout_admission']
for row in review['input_pins']:
    if not matches(row):
        drift.append(row['path'])
print(json.dumps(dict(status='FAIL' if errors else 'PASS', archive_pins_checked=6,
    archive_errors=errors, later_local_observations=sorted(set(drift)),
    scope='Archive integrity only; no new source, layout, compile/link or runtime acceptance.'), indent=2))
raise SystemExit(bool(errors))
