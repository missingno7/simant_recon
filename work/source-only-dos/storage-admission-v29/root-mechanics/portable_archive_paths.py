"""Preserve empty DOS redirection artifacts under Windows-checkout-safe names."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / 'work/source-only-dos/structural-audits-v29'

def main():
    path = BASE / 'archive-index.json'
    index = json.loads(path.read_bytes())
    changes = []
    for row in index['files']:
        old = ROOT / row['preserved']['path']
        if old.stem.upper() != 'NUL':
            continue
        assert old.resolve().is_relative_to(BASE.resolve())
        assert row['preserved']['size'] == 0 and old.read_bytes() == b''
        new = old.with_name('redirected-null.txt')
        assert not new.exists()
        new.write_bytes(b'')
        changes.append(dict(original_preserved_path=row['preserved']['path'],
                            portable_preserved_path=new.relative_to(ROOT).as_posix(),
                            sha256=row['preserved']['sha256']))
        # Exact, nonrecursive removal of our own empty archive copy. Extended
        # Windows paths address the actual filename rather than the NUL device.
        physical = Path('\\\\?\\' + str(old.resolve()))
        assert physical.is_file() and physical.stat().st_size == 0
        physical.unlink()
        row['preserved']['path'] = new.relative_to(ROOT).as_posix()
        assert hashlib.sha256(new.read_bytes()).hexdigest() == row['preserved']['sha256']
    assert len(changes) == 20
    index['portable_path_adjustments'] = changes
    path.write_bytes((json.dumps(index, indent=2)+'\n').encode())
    print('PORTABLE ARCHIVE PATHS PASS:', len(changes), 'empty NUL.TXT snapshots renamed; original names/hashes retained')

if __name__ == '__main__':
    main()
