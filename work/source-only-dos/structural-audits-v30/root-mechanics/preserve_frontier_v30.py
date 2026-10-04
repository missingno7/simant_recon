"""Preserve bounded static results without any compiler-input admission."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
OUT = ROOT / 'work/source-only-dos/structural-audits-v30'

def pin(path):
    return dict(path=path.relative_to(ROOT).as_posix(), sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                size=path.stat().st_size)

def main():
    files = []
    for group, source in [('mono-entry-ss-v32', ROOT / 'build/workers/dos_mono_8ed8_owner_v32'),
                          ('dgroup-56fe-v32', ROOT / 'build/workers/dos_dgroup_56fe_owner_v32')]:
        for path in sorted(source.rglob('*')):
            if not path.is_file() or path.suffix.lower() not in ('.json', '.md', '.txt', '.py'):
                continue
            target = OUT / group / path.relative_to(source)
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists():
                assert target.read_bytes() == path.read_bytes()
            else:
                target.write_bytes(path.read_bytes())
            files.append(dict(original=pin(path), preserved=pin(target)))
    mechanics = OUT / 'root-mechanics'
    mechanics.mkdir(exist_ok=True)
    for name in ('hotbox_semantic_review.py', 'review_frontier_v30.py', 'preserve_frontier_v30.py'):
        source, target = HERE / name, mechanics / name
        # Root-authored preservation mechanics remain drafts until the v30
        # archive is committed. Worker receipts above are never overwritten.
        target.write_bytes(source.read_bytes())
        files.append(dict(original=pin(source), preserved=pin(target)))
    reviews = [pin(OUT / name) for name in ('root-frontier-review.json', 'hotbox/root-semantic-review.json')]
    intermediate = OUT / 'mono-entry-ss-v32/make-correction-addendum-intermediate.py'
    snapshots = []
    if intermediate.exists():
        snapshots.append(dict(original_path='build/workers/dos_mono_8ed8_owner_v32/make-correction-addendum.py',
            preserved=pin(intermediate), reason='Root captured this builder while the worker was still editing it. '
            'Its bytes remain separate from the final builder; no JSON receipt was changed.'))
    index = dict(schema='simant-static-frontier-preservation-v30', root_reviewed=True,
                 production_admission=False, files=files, root_reviews=reviews, intermediate_script_snapshots=snapshots,
                 claim_limit='Static entry-state and type interpretation only. No buffer/storage extent or registration '
                             'admission, debt discharge, game link, execution or human acceptance. Source/report pins '
                             'are frozen observations. Scripts retain original scratch paths.')
    (OUT / 'archive-index.json').write_bytes((json.dumps(index, indent=2)+'\n').encode())
    print('STATIC FRONTIER PRESERVATION PASS:', len(files), 'text artifacts')

if __name__ == '__main__':
    main()
