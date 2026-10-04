"""Join the immutable v30 entry-state receipt to the current generated sources."""
from pathlib import Path
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'work/source-only-dos/mono-base-admission-v31'

def pin(path):
    return dict(path=path.relative_to(ROOT).as_posix(), sha256=hashlib.sha256(path.read_bytes()).hexdigest(), size=path.stat().st_size)

def main():
    original = json.loads((ROOT / 'work/source-only-dos/structural-audits-v30/root-frontier-review.json').read_bytes())
    report = json.loads((ROOT / 'build/source-only-dos/build-report.json').read_bytes())
    # Reopen every current source using the actual report's identity, then record
    # all explicit SS setters. This supplements, rather than repins, v30.
    setters, sources = [], []
    for row in report['translation_units']:
        source = row['generated_source']
        path = ROOT / source['path']
        identity = pin(path)
        assert identity['sha256'] == source['sha256'] and identity['size'] == source['size']
        text = path.read_text(encoding='latin1')
        text = re.sub(r'/\*.*?\*/|//[^\n]*|;[^\n]*', '', text, flags=re.S)
        for lineno, line in enumerate(text.splitlines(), 1):
            if re.search(r'\bmov\s+ss\s*,', line, re.I):
                setters.append(dict(module=row['module'], line=lineno, instruction=line.strip(), source=identity))
        sources.append(dict(module=row['module'], source=identity))
    assert len(sources) == 188 and len(setters) == 12
    assert {r['module'] for r in setters} == {'root:1B73', 'root:28BC'}
    prior_pins = []
    def walk(value):
        if isinstance(value, dict):
            if 'path' in value and 'sha256' in value: prior_pins.append(value)
            for v in value.values(): walk(v)
        elif isinstance(value, list):
            for v in value: walk(v)
    walk(original)
    prior_generated = {p['path'].replace('\\', '/'): p for p in prior_pins
                       if p['path'].replace('\\', '/').startswith('build/source-only-dos/sources/')}
    assert len(prior_generated) == 188
    changes = []
    for row in sources:
        p = row['source']
        prior = prior_generated[p['path']]
        if prior['sha256'] != p['sha256']:
            changes.append(dict(module=row['module'], prior=prior, current=p))
    assert len(changes) == 1 and changes[0]['module'] == 'S01:328E'
    receipt = dict(schema='simant-mono-current-entry-state-supplement-v31', root_reviewed=True,
                   original_receipt=pin(ROOT/'work/source-only-dos/structural-audits-v30/root-frontier-review.json'),
                   current_generated_sources=sources, current_explicit_ss_setters=setters, changed_sources=changes,
                   preservation='The v30 receipts and their original pins remain untouched. Its recheck fails against '
                                'the intentionally changed tools/source_only_dos.py. This is a new observation, not a repaired old hash.',
                   delta_proof='Only S01:328E changes. Its separate actual whole-TU proof permits exactly four ADD immediate '
                               'words to acquire DGROUP external fixups. No instruction, SS setter, call, branch or storage changes.',
                   contract=pin(ROOT/'work/source-only-dos/mono-base-contract-v1.json'),
                   claim_limit='Entry SS/frame reference proof only; no buffer owner/extent/index bound or game execution.')
    (OUT/'current-entry-state-supplement.json').write_bytes((json.dumps(receipt, indent=2)+'\n').encode())
    dest = OUT/'root-mechanics/current_entry_scan.py'
    dest.write_bytes(Path(__file__).read_bytes())
    print('CURRENT ENTRY SS PASS: 188 actual sources; 12 setters in the two audited handlers; only four-immediate S01 source delta')

if __name__ == '__main__': main()
