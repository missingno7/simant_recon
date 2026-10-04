"""Preserve the finished validation boundary and its earlier pinned-document failure."""
import hashlib
import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'work/source-only-dos/structural-audits-v32'
log = ROOT / 'build/source-only-dos-validation-v32-final.log'
text = log.read_text()
assert text.rstrip().endswith('VALIDATION PASS')
assert 'OK (skipped=2)' in text and 'VALIDATION FAILED' not in text
assert 'codegen rules reproduced: 48' in text
suite = unittest.defaultTestLoader.discover(str(ROOT/'tests'))
assert suite.countTestCases() == 375
copies = []
def pin(path):
    raw = path.read_bytes()
    return dict(path=path.relative_to(ROOT).as_posix(), size=len(raw), sha256=hashlib.sha256(raw).hexdigest())

for source, name in ((log, 'validation-final.log'),
        (ROOT/'build/source-only-dos-validation-v32.log', 'validation-pinned-document-error.log'),
        (ROOT/'build/source-only-dos-focused-doc-pin-v32.log', 'focused-restored-document.log'),
        (Path(__file__), 'preserve_boundary.py')):
    target = OUT/'root-review'/name
    if target.exists(): assert target.read_bytes() == source.read_bytes()
    else: target.write_bytes(source.read_bytes())
    copies.append(dict(original=pin(source), archived=pin(target)))

# validate.py writes generated progress documents. Preserve the new observation,
# then retain the old frozen evidence input when only its date would change.
progress_path = ROOT/'docs/progress.json'
current = json.loads(progress_path.read_bytes())
frozen_json = subprocess.run(['git','-c','safe.directory=D:/Prog/simant_recon','show',
    'HEAD:docs/progress.json'], cwd=ROOT, check=True, capture_output=True).stdout
frozen = json.loads(frozen_json)
assert current['validation'] == frozen['validation'] == 'PASS'
current_comparison = dict(current, generated=frozen['generated'])
assert current_comparison == frozen, 'Generated progress changed beyond date: preserve and review before restoring'
metadata = []
for name in ('progress.json', 'progress.md'):
    source = ROOT/'docs'/name
    target = OUT/'root-review'/('validated-'+name)
    raw = source.read_bytes()
    if target.exists(): assert target.read_bytes() == raw
    else: target.write_bytes(raw)
    metadata.append(pin(target))
    original = subprocess.run(['git','-c','safe.directory=D:/Prog/simant_recon',
        'show','HEAD:docs/'+name], cwd=ROOT, check=True, capture_output=True).stdout
    source.write_bytes(original)

receipt = dict(schema='simant-v32-validation-boundary', validation='PASS',
    repository_tests=375, skipped=2, codegen_rules=48,
    canonical_manifest_sha256=hashlib.sha256((ROOT/'layout/manifest.json').read_bytes()).hexdigest(),
    source_or_layout_admission=False, historical_or_functional_debt_discharged=0,
    failed_run_preserved=True, old_evidence_pins_refreshed=False,
    generated_progress_observation_preserved=True, frozen_progress_inputs_retained=True)
(OUT/'boundary.json').write_bytes((json.dumps(receipt, indent=2)+'\n').encode())
(OUT/'boundary-preservation-index.json').write_bytes((json.dumps(dict(copies=copies,
    archive_only=metadata+[pin(OUT/'boundary.json')]), indent=2)+'\n').encode())
print('v32 boundary PASS: 375 tests/2 skips, 48 codegen rules, historical validation; old pinned inputs retained')
