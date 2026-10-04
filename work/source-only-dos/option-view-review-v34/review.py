"""Parent check of the existing initialized data object, not a new owner admission."""
import hashlib
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
from omf import OmfReader

def pin(name, expected=None):
    path = Path(name)
    if not path.is_absolute():
        path = ROOT / path
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if expected is not None:
        assert digest == expected, name
    label = path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else path.as_posix()
    return dict(path=label, sha256=digest, size=len(raw))

pins = [pin('build/workers/dos_option_state_owner_v34/ownership-receipt.md',
            'a82f3b4ff68ec7e747bca7f51fb6654657c7b3f19ae91eb5ab1f9ce01126c0c9'),
        pin('build/workers/dos_option_state_owner_v34/typed-owner-candidate.c',
            '2697735e951d7543ec73d62cb32eac5c0a736c5849d2c40b3c11d9648fe8c8d6'),
        pin('layout/manifest.json', '025a0a9255d910cae4b122ab5a3f3fb40888bb456d7fe42158db7c9e622fcf50'),
        pin('build/source-only-dos/build-report.json', '0edcb3285074975704645520158975bd20a32a7cae542127812b54a9e78cffbf'),
        pin('tools/omf.py'), pin(__file__)]
manifest = json.loads((ROOT / 'layout/manifest.json').read_bytes())['modules']['data:3D57']
assert manifest['placements']['UNIT7_DATA'] == dict(seg=0x3d57, off=0, size=3162)
report = json.loads((ROOT / 'build/source-only-dos/build-report.json').read_bytes())
rows = {row['module']: row for row in report['translation_units']}
for key in ('data:3D57', 'S11:35F5', 'S09:35F5', 'root:00DF'):
    row = rows[key]
    for kind in ('source', 'generated_source', 'object'):
        pins.append(pin(row[kind]['path'], row[kind]['sha256']))
    assert row['source']['sha256'] == row['generated_source']['sha256']
owner = rows['data:3D57']
assert owner['source']['sha256'] == manifest['source_sha256']
obj = OmfReader(communals=True).read_file(ROOT / owner['object']['path'])
publics = {row['name']: row for row in obj.publics}
base = publics['_fd_3D57_07A8']
assert len(obj.segments[base['segment']]) == 3162
assert base['offset'] == 0x7a8
for name, offset in [('07AA', 0x7aa), ('07AE', 0x7ae), ('07B0', 0x7b0), ('07B2', 0x7b2)]:
    public = publics['_fd_3D57_' + name]
    assert public['segment'] == base['segment'] and public['offset'] == offset
assert publics['_ExpSubStates']['segment'] == base['segment']
assert publics['_ExpSubStates']['offset'] == 0x7b6
words = struct.unpack_from('<7h', obj.segments[base['segment']], base['offset'])
assert words == (0, 1, 1, 1, 1, 0, 0)
menu = (ROOT / 'src/S11/m35F5.c').read_text()
save = (ROOT / 'src/S09/m35F5.c').read_text()
assert 'item <= 0x36' in menu and 'fd_3D57_07A8[i] ?' in menu
assert 'fd_3D57_07A8[item - 0x31] = !fd_3D57_07A8[item - 0x31]' in menu
assert '{ 2, 6, (void far *)&fd_3D57_07A8 }' in save
assert 'write(fd, p->data, p->count * p->size)' in save
assert 'read(fd, p->data, n = p->count * p->size)' in save
win_path = 'D:/Prog/simantw_recon/src/recovered/data_08a_controls-4d265af87b.c'
pins.append(pin(win_path, '4d265af87b4de8363e55d3648b582ca62b4e73c050e717f110a91fb2b3bd01de'))
assert 'OptionStates[7] = { 0, 1, 1, 1, 1, 0, 0 }' in Path(win_path).read_text()
receipt = dict(schema='simant-parent-option-view-v34', status='PASS', root_reviewed=True,
    new_source_or_layout_admission=False, canonical_or_production_changes=False,
    clarifies='v33 root/option-gate-review.json structural follow-up: this is an existing '
        'compiler-proven within-object view, not an unresolved original-link-order assumption.',
    verified_view=dict(type='six 16-bit int words', length=12, initialized_values=list(words[:6]),
                       sound_gate_word_index=2, sound_gate_initial_value=1),
    existing_storage=dict(module='data:3D57', segment=base['segment'], segment_length=3162,
                          current_public_offsets={name: publics[name]['offset'] for name in
                          ['_fd_3D57_07A8', '_fd_3D57_07AA', '_fd_3D57_07AE',
                           '_fd_3D57_07B0', '_fd_3D57_07B2', '_ExpSubStates']}),
    boundary='The two bytes at 07B4 are already within fd_3D57_07B2[4]. Their zero '
        'initializer is observed; their DOS semantic role and a seventh DOS option declaration '
        'are not established. No padding, reserve field or extra storage is proposed.',
    fragment='Explanatory extern declaration only, not a whole TU, build input or promotion candidate.',
    runtime='No link/runtime/game trace. Count-39 audio schedule remains unresolved.', input_pins=pins)
Path(__file__).with_name('root-review.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8', newline='\n')
print(json.dumps(dict(status='PASS', input_pins=len(pins), six_word_view=list(words[:6]),
                     same_object_segment_bytes=3162, new_layout_gate=False)))
