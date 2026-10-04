"""Preserve unresolved research as text, separately from production admission."""
from pathlib import Path
import hashlib
import json
import re
import sys
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
from omf import OmfReader
from reopen_screen import pin

def main():
    fheap = ROOT / 'build/workers/dos_fdata_selection_cause_v37a'
    report = json.loads((fheap / 'selection-cause-controls-v37a.json').read_bytes())
    for name, library in report['built_libraries'].items():
        path = fheap / 'controls-v37a-controls' / name
        assert pin(path)['sha256'] == library['sha256']
        members = OmfReader().split_library(path.read_bytes())
        assert [name for name, _ in members] == library['members']
        assert len(members) == 1 and hashlib.sha256(members[0][1]).hexdigest() == library['member_sha256']
        log = (path.parent / (path.stem + '.LOG')).read_text(encoding='latin1')
        assert log == report['librarian']['libraries'][name]['build_log']
        assert not re.search(r'\b(?:fatal|errors?|warnings?)\b', log, re.I)
        assert (path.parent / (path.stem + '.CHE')).read_bytes() == b''
    link_count = 0
    normalized_text_hashes = []
    for row in report['link_runs']:
        for kind, digest_key in [('link_log', 'link_log_sha256'), ('map', 'map_sha256')]:
            path = ROOT / row[kind]
            raw_pin = pin(path)
            normalized = path.read_text(encoding='latin1', errors='replace').encode('latin1', errors='replace')
            assert hashlib.sha256(normalized).hexdigest() == row[digest_key]
            normalized_text_hashes.append(dict(raw=raw_pin, historical_text_sha256=row[digest_key],
                interpretation='Frozen v37a field hashes universal-newline-normalized text, not file bytes.'))
        assert row['executable_executed'] is False
        log = (ROOT / row['link_log']).read_text(encoding='latin1')
        assert ('undefined' in log.lower()) == bool(row['undefined_symbols'])
        assert not re.search(r'\bfatal\b', log, re.I)
        link_count += 1
    base = ROOT / 'work/source-only-dos/structural-audits-v29'
    base.mkdir(exist_ok=True)
    groups = {
        'fheap-selection-v37a': fheap,
        'hotbox-v35': ROOT / 'build/workers/dos_unused_hotbox_owner_v35',
        'numeric-frames-v30': ROOT / 'build/workers/dos_numeric_frame_inventory_v30',
        'mono-owner-v31': ROOT / 'build/workers/dos_mono_8ed8_owner_v31',
    }
    allowed = {'.json', '.md', '.py', '.c', '.asm', '.log', '.map', '.rsp', '.bat', '.lnk', '.cfg', '.conf', '.che', '.txt'}
    files = []
    for group, source in groups.items():
        for path in sorted(source.rglob('*')):
            if not path.is_file() or path.suffix.lower() not in allowed or '__pycache__' in path.parts:
                continue
            destination = base / group / path.relative_to(source)
            destination.parent.mkdir(parents=True, exist_ok=True)
            if destination.exists():
                assert destination.read_bytes() == path.read_bytes(), destination
            else:
                destination.write_bytes(path.read_bytes())
            files.append(dict(original=pin(path), preserved=pin(destination)))
    index = dict(schema='simant-unresolved-structural-archive-v29', root_reviewed=True,
        production_admission=False, files=files,
        root_fheap_controls_review=dict(clean_librarian_libraries=3, reopened_link_maps=link_count,
            normalized_text_hashes=normalized_text_hashes,
            known_comdef_undefined_contrast=True, original_executable_used=False,
            historical_79f0_owner_and_app_specific_selection_trigger='OPEN'),
        limits='186-TU numeric baseline stays frozen; screen ownership is superseded only by separate v29 admission. '
            'Hot-box registration and 8ED8 extent/frame remain OPEN. Scripts retain original scratch paths; '
            'archive hashes preserve observations, not a runnable standalone game.')
    (base / 'archive-index.json').write_bytes((json.dumps(index, indent=2) + '\n').encode())
    print('STRUCTURAL ARCHIVE PASS:', len(files), 'text artifacts;', link_count, 'fheap link/map pairs reopened')

if __name__ == '__main__':
    main()
