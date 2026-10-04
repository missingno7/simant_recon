"""Specific initialized option-view check; no storage/layout admission."""
import hashlib
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
from omf import OmfReader

def pin(name):
    path = ROOT / name
    raw = path.read_bytes()
    return dict(path=name, sha256=hashlib.sha256(raw).hexdigest(), size=len(raw))

data = (ROOT / 'src/data/d3D57.c').read_text()
menu = (ROOT / 'src/S11/m35F5.c').read_text()
sound = (ROOT / 'src/root/m00DF.c').read_text()
save = (ROOT / 'src/S09/m35F5.c').read_text()
assert 'unsigned char far fd_3D57_07A8[2] = { 0 };' in data
assert 'fd_3D57_07A8[item - 0x31] = !fd_3D57_07A8[item - 0x31];' in menu
assert 'if (item >= 0x31 && item <= 0x36)' in menu and 'goto toggle;' in menu
assert 'item <= 0x36' in menu and 'fd_3D57_07A8[i] ?' in menu
assert 'g_1926 && fd_3D57_07A8[2]' in sound
assert '{ 2, 6, (void far *)&fd_3D57_07A8 }' in save
report = json.loads((ROOT / 'build/source-only-dos/build-report.json').read_bytes())
row = next(row for row in report['translation_units'] if row['module'] == 'data:3D57')
assert row['source']['sha256'] == row['generated_source']['sha256']
path = ROOT / row['object']['path']
assert hashlib.sha256(path.read_bytes()).hexdigest() == row['object']['sha256']
obj = OmfReader(communals=True).read_file(path)
symbols = {row['name']: row for row in obj.publics}
base = symbols['_fd_3D57_07A8']
words = struct.unpack_from('<6h', obj.segments[base['segment']], base['offset'])
assert words == (0, 1, 1, 1, 1, 0)
aliases = []
for name, delta in [('_fd_3D57_07AA', 2), ('_fd_3D57_07AE', 6),
                    ('_fd_3D57_07B0', 8), ('_fd_3D57_07B2', 10)]:
    alias = symbols[name]
    assert alias['segment'] == base['segment'] and alias['offset'] == base['offset'] + delta
    aliases.append(dict(name=name, byte_offset=delta, word_index=delta // 2))
receipt = dict(schema='simant-option-gate-parent-correction-v33', status='PASS',
    root_reviewed=True, admitted=False,
    supersedes='Only the sample worker claim that no source write establishes a nonzero SFX gate.',
    facts=['The exact SetMenuEntries loop reads six 16-bit words.',
           'ProcMenu item 0x33 reaches the shared toggle and toggles word 2.',
           'The exact save descriptor specifies six two-byte entries.',
           'myBeginSound reads word 2 behind the driver-present condition.',
           'The accepted current OMF initializer gives word 2 value 1.'],
    initialized_words=list(words), current_alias_views=aliases,
    structural_gap='Current U039 defines the base as two unsigned bytes and leaves subsequent '
        'words in separate initialized declarations. Its consumers depend on those declarations '
        'remaining adjacent. The six-word typed owner, interior aliases and residual word at '
        '07B4 require independent admission; no canonical change or packet refresh here.',
    remaining_reachability='Driver selection, voice priorities, sample distinctness, actual song '
        'events, busy observations and timer/main-loop interleaving remain unproved. '
        'This correction neither proves count 39 nor discharges the free-list extent.',
    pins=[pin(name) for name in ['src/data/d3D57.c', 'src/S11/m35F5.c',
        'src/root/m00DF.c', 'src/S09/m35F5.c', 'tools/omf.py',
        'build/source-only-dos/build-report.json', row['object']['path'],
        'build/workers/dos_sample_freelist_reachability_v33/sample-freelist-reachability-v33.md',
        'build/workers/dos_sample_freelist_reachability_v33/sample-freelist-reachability-v33.json']])
Path(__file__).with_name('option-gate-review.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
print(json.dumps(dict(status='PASS', initialized_words=list(words), aliases=aliases)))
