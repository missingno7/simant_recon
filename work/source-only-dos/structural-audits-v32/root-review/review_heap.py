"""Independent, read-only reopening of the v38/v39 heap investigations."""
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
from omf import OmfReader

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

report_path = ROOT / 'build/source-only-dos/build-report.json'
raw_report = report_path.read_bytes()
assert sha(raw_report) == '0edcb3285074975704645520158975bd20a32a7cae542127812b54a9e78cffbf'
report = json.loads(raw_report)
assert len(report['translation_units']) == 188
assert len(report['symbolic_aliases']) == 193
census_dir = ROOT / 'build/workers/dos_fdata_extdef_selection_v38'
order_dir = ROOT / 'build/workers/dos_fdata_file_order_v39'
census = json.loads((census_dir / 'extdef-census-v38.json').read_bytes())
orders = json.loads((order_dir / 'file-order-v39.json').read_bytes())
rd = OmfReader(communals=True)
ext_count = fix_count = 0
for row, recorded in zip(report['translation_units'], census['census']['all_objects']):
    raw = (ROOT / row['object']['path']).read_bytes()
    assert sha(raw) == row['object']['sha256'] == recorded['object_sha256']
    obj = rd.read(raw, row['basename'])
    ext = [n for n, scope in zip(obj.externals, obj.external_scopes) if scope == 'external']
    fix = [f for f in obj.linker_fixups if f['target_kind'] == 'external']
    assert ext == recorded['external_extdefs']
    assert [f['target'] for f in fix] == [f['symbol'] for f in recorded['live_external_fixups']]
    assert all(n.lower() != '__fheap' for n in ext)
    assert all(f['target'].lower() != '__fheap' for f in fix)
    ext_count += len(ext)
    fix_count += len(fix)
assert (ext_count, fix_count) == (5949, 22101)

libraries = {}
for pin in orders['inputs']['runtime_libraries']:
    raw = Path(pin['path']).read_bytes()
    assert sha(raw) == pin['sha256']
    libraries[Path(pin['path']).name.upper()] = {n.lower(): b for n, b in rd.split_library(raw)}
for profile, pin in orders['inputs']['linker_utility_archives'].items():
    raw = Path(pin['path']).read_bytes()
    assert sha(raw) == pin['sha256']
    libraries[profile] = {n.lower(): b for n, b in rd.split_library(raw)}
fdata = libraries['LLIBCR.LIB']['fdata.asm']
assert sha(fdata) == '7eb6a9bfcb257d6470b0bc9c9f7c6215052a7a78749e463a4a6ebaa2294e70ec'
obj = rd.read(fdata, 'fdata.asm')
assert [(p['name'], p['segment'], p['offset']) for p in obj.publics] == [('__fheap', '_DATA', 0)]
assert len(obj.segments['_DATA']) == 14 and not obj.linker_fixups

root_rows = [r for r in report['translation_units'] if r['unit'] == 'root']
root_names = [r['basename'] for r in root_rows]
assert root_names.index('U074') == 30
root_line_count = (len(root_names) + 7) // 8
by_case = {}
member_count = 0
for run in orders['runs']:
    case = order_dir / run['plan'] / run['profile']
    for key, pathkey in [('raw_log_sha256', 'raw_log'), ('raw_map_sha256', 'raw_map'),
                         ('link_script_sha256', 'link_script')]:
        assert sha((order_dir / run[pathkey]).read_bytes()) == run[key]
    for row in report['translation_units']:
        assert sha((case / (row['basename'] + '.OBJ')).read_bytes()) == row['object']['sha256']
    log = (order_dir / run['raw_log']).read_bytes().decode('latin1')
    selected = [{'library': a.upper(), 'member': b} for a, b in re.findall(
        r'(?im)^\s*([A-Z]:\\[^()\r\n]+\.LIB|[A-Z0-9_]+\.LIB)\(([^)\r\n]+)\)', log)]
    assert selected == run['selected_members']
    assert len(selected) == (112 if run['profile'] == 'rtlink400' else 115)
    names = [r['member'].lower() for r in selected]
    assert 'fdata.asm' in names
    assert ('fmalloc.asm' in names) == (run['profile'] == 'rtlink400')
    assert ('wrt0011' in log) == (run['profile'] == 'rtlink400')
    assert len(run['undefined_symbols']) == 15 and run['exe_executed'] is False
    assert run['selected_members_without_report_runtime_library_omf'] == []
    for entry in run['selected_runtime_library_member_omf']:
        lib = entry['library'].split('\\')[-1]
        archive = libraries[run['profile']] if lib == 'RTLUTILS.LIB' else libraries[lib]
        raw = archive[entry['member'].lower()]
        assert sha(raw) == entry['member_sha256']
        obj = rd.read(raw, entry['member'])
        assert obj.publics == entry['publics']
        assert {s: len(b) for s, b in obj.segments.items()} == entry['segment_payload_lengths']
        assert [f['target'] for f in obj.linker_fixups if f['target_kind'] == 'external'] == entry['live_external_fixup_targets']
        member_count += 1
    lines = (case / 'T.LNK').read_text().splitlines()
    block = lines[6:6 + root_line_count]
    actual = [n.strip() for line in block for n in line.removeprefix('FILE ').split(',')]
    expected = root_names if run['plan'] == 'baseline_current_order' else ['U074'] + [n for n in root_names if n != 'U074']
    assert actual == expected
    normalized = lines[:6] + ['<ROOT FILE ORDER>'] + lines[6 + root_line_count:]
    by_case[(run['plan'], run['profile'])] = (normalized, selected)
    map_text = (order_dir / run['raw_map']).read_bytes().decode('latin1')
    name_table, value_table = map_text.split('Publics by Name', 1)[1].split('Publics by Value', 1)
    value_table = value_table.split('Line numbers', 1)[0]
    for name in ('_malloc', '_free', '__ffree', '__frealloc'):
        for table in (name_table, value_table):
            hits = [line for line in table.splitlines() if re.search(r'\s' + re.escape(name) + r'\s', line)]
            assert len(hits) == 1 and 'U074.C' in hits[0]
for profile in ('rtlink400', 'rtlink610'):
    assert by_case[('baseline_current_order', profile)] == by_case[('root_171c_first', profile)]
print(json.dumps({'status': 'PASS', 'objects_reparsed': 188, 'extdefs': ext_count,
                  'live_external_fixups': fix_count, 'partial_links_reopened': 4,
                  'selected_member_models_reopened': member_count,
                  'unused_app_fheap_extdef': 'ABSENT', 'tested_file_order_cause': 'REJECTED',
                  'functional_or_historical_debt_discharged': 0,
                  'game_executed': False}, indent=2))
