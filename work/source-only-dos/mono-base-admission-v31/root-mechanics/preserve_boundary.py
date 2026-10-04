"""Preserve finalized mechanics and validation logs without changing receipts."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
OUT = ROOT / 'work/source-only-dos/mono-base-admission-v31/root-validation'

def pin(path):
    return dict(path=path.relative_to(ROOT).as_posix(), sha256=hashlib.sha256(path.read_bytes()).hexdigest(), size=path.stat().st_size)

def main():
    OUT.mkdir(exist_ok=True)
    pairs = [(HERE/'check_mandatory_gates.py', OUT.parent/'root-mechanics/check_mandatory_gates.py'),
             (HERE/'plan.md', OUT.parent/'root-mechanics/plan.md'),
             (Path(__file__), OUT.parent/'root-mechanics/preserve_boundary.py')]
    names = ('source-only-dos-focused-mono-v31-final.log', 'source-only-dos-run-accepted-v31-final.log',
             'source-only-dos-tests-accepted-v31-final.log', 'source-only-dos-gates-accepted-v31.log',
             'source-only-dos-mono-recheck-v31.log', 'source-only-dos-entry-scan-v31.log',
             'source-only-dos-tests-v31-minimal-report-error.log', 'source-only-dos-static-frontier-recheck-after-v31.log')
    pairs += [(ROOT/'build'/n, OUT/n) for n in names]
    rows = []
    for source, target in pairs:
        if target.exists(): assert target.read_bytes() == source.read_bytes(), str(target)
        else: target.write_bytes(source.read_bytes())
        rows.append(dict(original=pin(source), preserved=pin(target)))
    receipt = dict(schema='simant-mono-boundary-preservation-v31', files=rows,
                   regression_history='The first 375-test boundary had one minimal-report KeyError, fixed by '
                                      'using the same optional-module lookup as other gates. Final full boundary is separate.',
                   historical_recheck='The immutable v30 recheck flags intentionally changed source-only tooling. '
                                      'Its old pins stay untouched. v31 entry scan proves the precise current source delta.',
                   scope='Validation/provenance preservation only; no storage/extent or game execution admission.')
    (OUT/'index.json').write_bytes((json.dumps(receipt, indent=2)+'\n').encode())
    print('BOUNDARY PRESERVATION PASS:', len(rows), 'files')

if __name__ == '__main__': main()
