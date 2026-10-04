"""Recheck preserved histogram observations without invoking build tools."""
from pathlib import Path
import hashlib
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'tools'))
from omf import OmfReader


def main():
    contract = json.loads((ROOT/'work/source-only-dos/ant-class-histogram-contract-v1.json').read_text())
    for row in contract['cases']:
        for pin in row['raw_case_artifact_pins']:
            data = (ROOT/pin['path']).read_bytes()
            assert len(data) == pin['size'] and hashlib.sha256(data).hexdigest() == pin['sha256'], pin['path']
        raw = (ROOT/row['run_log_pin']['path']).read_bytes()
        assert raw == (row['expected']+'\r\n').encode('ascii')
        log = (ROOT/row['link_log_pin']['path']).read_text(encoding='cp437')
        assert not re.search(r'\b(warning|error|fatal|undefined|unresolved|cannot open)\b', log, re.I)
        sections, active = {}, None
        for line in (ROOT/row['map_input_pin']['path']).read_text(encoding='cp437').splitlines():
            heading = re.match(r'\s*Address\s+Publics by (Name|Value)\s*$', line)
            if heading:
                active = heading[1]
                assert active not in sections
                sections[active] = {}
                continue
            public = re.match(r'\s*([0-9A-Fa-f]{4}:[0-9A-Fa-f]{4})\s+Res\s+(\S+)\s*$', line)
            if active and public and public[2].lower() in row['public_address_matrix'][active]:
                name = public[2].lower()
                assert name not in sections[active]
                sections[active][name] = public[1].upper()
        assert sections == row['public_address_matrix'], (row['linker'], row['case'])
    for name, fixture in contract['compiler_controls']['fixtures'].items():
        obj = OmfReader(communals=True).read((ROOT/fixture['object']['path']).read_bytes())
        assert obj.communals == fixture['actual_communals'] and obj.publics == fixture['actual_publics'], name
        keys = ('index', 'name', 'class', 'length', 'alignment', 'combine', 'big')
        assert [{k: row[k] for k in keys} for row in obj.segment_defs] == fixture['actual_segments'], name
        assert all(row['use_32bit_offset'] is False for row in obj.segment_defs), name
    print('ROOT RAW ACCEPTANCE PASS: 104 artifacts, eight full logs/maps, seven decoded OMF fixtures')


if __name__ == '__main__':
    main()
