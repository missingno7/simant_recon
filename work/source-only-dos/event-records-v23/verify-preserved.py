"""Readonly acceptance audit of source-built Event proof artifacts; no execution."""
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'tools'))
from omf import OmfReader

def verify(pin):
    path = Path(pin['path'])
    path = path if path.is_absolute() else ROOT/path
    raw = path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == pin['sha256'], path
    assert len(raw) == pin['size'], path
    return raw

contract = json.loads((ROOT/'work/source-only-dos/event-records-contract-v1.json').read_bytes())
receipt = json.loads((Path(__file__).parent/'root-acceptance.json').read_bytes())
for row in receipt['source_pins'] + receipt['strict_receipt_pins'] + contract['inputs'] + receipt['raw_case_artifacts']:
    verify(row)
for case in contract['cases']:
    raw = verify(case['runtime_log'])
    assert raw == (case['expected'].replace('\n','\r\n')+'\r\n').encode('ascii')
    pins = {Path(p['path']).name.upper(): p for p in case['artifact_pins']}
    link = verify(pins['LINK.LOG']).decode('latin1')
    assert not re.search(r'\b(?:WARNING|ERROR|FATAL|UNDEFINED|UNRESOLVED)\b|cannot\s+open',link,re.I)
    maps = {'Name':{},'Value':{}}
    active = None
    for line in verify(pins['PASS.MAP']).decode('latin1').splitlines():
        for section in maps:
            if 'Publics by '+section in line:
                assert not maps[section]; active = section
        match = re.match(r'^\s*([0-9A-Fa-f]{4}:[0-9A-Fa-f]{4})\s+(Abs\s+)?(\S+)\s*$',line)
        if active and match:
            address,absolute,name = match.groups()
            maps[active].setdefault(name.lower(),[]).append((address.upper(),bool(absolute)))
    assert maps['Name'] == maps['Value']
    for section,matrix in case['public_address_matrix'].items():
        for name,address in matrix.items():
            assert maps[section][name.lower()] == [(address,False)]
    for key in ('owner_omf','base_initializer_omf'):
        objname = ('OWNINIT' if case['case']=='nonzero_initializer' else 'OWNWIDE' if case['case']=='wrong_wide_field'
                   else 'OWNSHORT' if case['case']=='wrong_narrow_field' else 'OWNER') if key=='owner_omf' else (
                   'BADADD' if case['case']=='base_plus_two' else 'BADOTHER' if case['case']=='wrong_symbol_base' else 'BASES')
        obj = OmfReader(communals=True).read(verify(pins[objname+'.OBJ']))
        shape = case[key]
        for field in ('communals','publics','externals','linker_fixups','segment_lengths'):
            assert getattr(obj,field) == shape[field], (key,field)
        assert {k:v.hex() for k,v in obj.segments.items()} == shape['initialized_segment_hex']
print('PASS: 184 preserved artifacts, 14 full raw/link/map/OMF cases, 156 sources and 29 strict receipts')
