"""Preserve the root's review mechanics without build artifacts or new admissions."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
OUT = ROOT / 'work/source-only-dos/storage-admission-v29/root-mechanics'

def pin(path):
    return dict(path=path.relative_to(ROOT).as_posix(),
                sha256=hashlib.sha256(path.read_bytes()).hexdigest(), size=path.stat().st_size)

def main():
    OUT.mkdir(exist_ok=True)
    names = ('screen_policy.py', 'word_policy.py', 'install_policies.py',
             'reopen_screen.py', 'reopen_words.py', 'fresh_screen.py',
             'fresh_words.py', 'admit.py', 'check_mandatory_gates.py',
             'archive_research.py', 'preserve_mechanics.py')
    rows = []
    for name in names:
        source = HERE / name
        target = OUT / name
        if target.exists():
            assert target.read_bytes() == source.read_bytes(), name
        else:
            target.write_bytes(source.read_bytes())
        rows.append(dict(original=pin(source), preserved=pin(target)))
    receipt = dict(schema='simant-v29-root-review-mechanics-preservation', files=rows,
                   production_input=False,
                   limitation='Scripts retain original ignored scratch paths and parent-depth assumptions. '
                              'Preserved for review; not standalone replay tools. admit.py refuses existing contracts.')
    (OUT / 'index.json').write_bytes((json.dumps(receipt, indent=2)+'\n').encode())
    print('ROOT MECHANICS PRESERVATION PASS:', len(rows), 'source scripts')

if __name__ == '__main__':
    main()
