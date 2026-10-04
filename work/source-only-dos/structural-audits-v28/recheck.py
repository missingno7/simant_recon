"""Read-only root research recheck; never compile, link, or execute an image."""
from pathlib import Path
import hashlib
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'tools'))
from omf import OmfReader


def load(path):
    return json.loads(path.read_text(encoding='utf8'))


def check_pin(row):
    p = ROOT / row['path']
    assert p.is_file(), str(p)
    assert hashlib.sha256(p.read_bytes()).hexdigest() == row['sha256'], str(p)
    if 'size' in row:
        assert p.stat().st_size == row['size'], str(p)


def main():
    index = load(HERE / 'archive-index.json')
    assert not index['storage_or_data_admitted']
    for row in index['files']:
        check_pin(row)
    readonly = load(HERE / 'readonly-words/receipt-v33.json')
    for row in readonly['source_census']['files'] + readonly['evidence_files']:
        check_pin(row)
    menu = load(HERE / 'menu/review-v34.json')
    for row in menu['pins']['current_source_files'] + menu['pins']['current_registries']:
        check_pin(dict(row, size=row['bytes']))
    asset_checks = []
    for pair in menu['pins']['installed_dat_ndx_pairs']:
        for key in ('dat', 'ndx'):
            row = {'path': 'assets/' + pair[key],
                   'sha256': pair[key + '_sha256'], 'size': pair[key + '_bytes']}
            check_pin(row)
            asset_checks.append(row['path'])
    assert len(set(asset_checks)) == 6

    candidate = load(HERE / 'fheap/functional-fheap-owner-candidate-v36.json')
    archive = candidate['fdata_owner_evidence']
    library = Path(archive['archive'])
    assert hashlib.sha256(library.read_bytes()).hexdigest() == archive['archive_sha256']
    reader = OmfReader(communals=True)
    members = {name.lower(): reader.read(blob, name)
               for name, blob in reader.split_library(library.read_bytes())}
    providers = [name for name, obj in members.items()
                 if any(p['name'] == '__fheap' for p in obj.publics)]
    assert providers == ['fdata.asm'], providers
    owner = members[providers[0]]
    assert len(owner.segments['_DATA']) == 14
    assert not owner.externals and not owner.linker_fixups

    report = load(ROOT / 'build/source-only-dos/build-report.json')
    assert len(report['translation_units']) == 186
    for unit in report['translation_units']:
        check_pin(unit['object'])
    expected = ''.join(f'{phase} flags=3 links=111 changed=0\n' for phase in
                       ('entry', 'near-allocated', 'near-freed',
                        'far-allocated', 'far-freed'))
    expected += 'malloc=1 fmalloc=1 frealloc=1\n'
    family = {'__fheap', '__fmalloc', '__ffree', '__frealloc'}
    for profile in ('rtlink400', 'rtlink610'):
        control = HERE / 'fheap/links' / profile
        assert (control / 'OUTPUT.TXT').read_text(encoding='ascii') == expected
        assert (control / 'DONE.TXT').read_text(encoding='ascii').strip() == 'done'
        for fixture, image in (('links', 'PROBE'), ('api-only', 'APIONLY')):
            case = HERE / 'fheap' / fixture / profile
            log = (case / 'LINK.LOG').read_text(encoding='latin1')
            assert not re.search(r'warning|error|undefined|doubly defined', log, re.I)
            assert 'LLIBCR.LIB(fdata.asm)' in log
            assert re.search(r'^\s*[0-9A-Fa-f]+:[0-9A-Fa-f]+\s+__fheap\s',
                             (case / (image + '.MAP')).read_text(encoding='latin1'), re.M)
        partial = HERE / 'fheap/current186-partial' / profile
        log = (partial / 'LINK.LOG').read_text(encoding='latin1')
        selected = re.findall(r'LLIBCR\.LIB\(([^)]+)\)', log, re.I)
        importers = []
        for name in selected:
            obj = members[name.lower()]
            refs = set(obj.externals) | {f['target'] for f in obj.linker_fixups
                                        if f['target_kind'] == 'external'}
            if refs & family:
                importers.append((name, sorted(refs & family)))
        if profile == 'rtlink610':
            assert importers == [], importers
            assert 'fmalloc.asm' not in [n.lower() for n in selected]
        else:
            assert importers == [('fmalloc.asm', ['__fheap'])], importers
            assert "Public symbol '__ffree' doubly defined" in log
        assert re.search(r'^\s*[0-9A-Fa-f]+:[0-9A-Fa-f]+\s+Res\s+__fheap\s',
                         (partial / 'SOURCE.MAP').read_text(encoding='latin1'), re.M)
        assert 'wrt0022' in log
    print(f'PASS: {len(index["files"])} archived files, 183 readonly pins, '
          '6 assets, 186 current objects, real-runtime outputs and both partial import graphs')
    print('No data/storage admission; no compile/link/image execution')


if __name__ == '__main__':
    main()
