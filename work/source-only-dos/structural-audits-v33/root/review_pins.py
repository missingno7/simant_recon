"""Read-only input identity review; no evidence pin is refreshed."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
FILES = [
    'build/workers/dos_filename_owner_v34/receipt.json',
    'build/workers/dos_icon_handle_owner_v33/receipt-v33.json',
    'build/workers/dos_root_frontier_v33/current-frames.json',
    'build/workers/dos_root_frontier_v33/root-inbound.json',
    'build/workers/dos_sample_freelist_reachability_v33/sample-freelist-reachability-v33.json',
    'build/workers/dos_sample_freelist_reachability_v33/raw/index.json',
    'build/workers/dos_root_frontier_v33/option-gate-review.json',
]

def pins(value):
    if isinstance(value, dict):
        if 'path' in value and 'sha256' in value:
            yield value
        for item in value.values():
            yield from pins(item)
    elif isinstance(value, list):
        for item in value:
            yield from pins(item)

checked = {}
receipts = []
for name in FILES:
    path = ROOT / name
    raw = path.read_bytes()
    receipts.append(dict(path=name, sha256=hashlib.sha256(raw).hexdigest(), size=len(raw)))
    for row in pins(json.loads(raw)):
        target = Path(row['path'])
        if not target.is_absolute():
            target = ROOT / target
        content = target.read_bytes()
        digest = hashlib.sha256(content).hexdigest()
        assert digest == row['sha256'], row
        if 'size' in row:
            assert len(content) == row['size'], row
        checked[str(target)] = dict(path=row['path'], sha256=digest, size=len(content))
report_path = ROOT / 'build/source-only-dos/build-report.json'
assert hashlib.sha256(report_path.read_bytes()).hexdigest() == '0edcb3285074975704645520158975bd20a32a7cae542127812b54a9e78cffbf'
report = json.loads(report_path.read_bytes())
for row in report['inputs']:
    target = ROOT / row['path']
    content = target.read_bytes()
    assert len(content) == row['size']
    assert hashlib.sha256(content).hexdigest() == row['sha256'], row
    checked[str(target)] = row
assert (len(report['translation_units']), len(report['unresolved_symbols']),
        sum(row['size'] for row in report['unresolved_data']),
        sum(row['size'] for row in report['historical_data_debt']),
        sum(row['status'] == 'UNRESOLVED' for row in report['layout_dependencies'])) == (188, 15, 46, 113, 7)
assert report['function_dispositions']['BEHAVIOR_EXACT_CONFIRMED'] == 29
assert not any(report['original_exe_bytes_used'].values())
assert report['denied_oracle_reads'] == []
assert report['standalone_dos_executable'] is False
receipt = dict(status='PASS', root_reviewed=True, source_or_layout_admitted=False,
    receipt_pins=receipts, input_pins=list(checked.values()),
    scope='Frozen receipt and current preflight identities only. No compile, link, runtime or reachability acceptance.')
(OUT / 'root-pins.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
print(json.dumps(dict(status='PASS', receipts=len(receipts), input_identities=len(checked))))
