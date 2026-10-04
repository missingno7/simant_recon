"""Append the disclosed worker pin correction and portable-path mechanics."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent

def pin(path):
    return dict(path=path.relative_to(ROOT).as_posix(),
                sha256=hashlib.sha256(path.read_bytes()).hexdigest(), size=path.stat().st_size)

def append(index_path, source, target):
    index = json.loads(index_path.read_bytes())
    assert not target.exists()
    target.write_bytes(source.read_bytes())
    index['files'].append(dict(original=pin(source), preserved=pin(target)))
    index_path.write_bytes((json.dumps(index, indent=2)+'\n').encode())

def main():
    base = ROOT / 'work/source-only-dos/structural-audits-v29'
    source = ROOT / 'build/workers/dos_mono_8ed8_owner_v31/pin-correction-addendum-v1.json'
    append(base / 'archive-index.json', source, base / 'mono-owner-v31' / source.name)
    mechanics = ROOT / 'work/source-only-dos/storage-admission-v29/root-mechanics'
    for name in ('portable_archive_paths.py', 'preserve_archive_addendum.py'):
        append(mechanics / 'index.json', HERE / name, mechanics / name)
    print('ARCHIVE ADDENDUM PRESERVATION PASS; original receipt unchanged')

if __name__ == '__main__':
    main()
