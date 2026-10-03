import hashlib, json, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tools'))
from omf import OmfReader

TARGET_OFFSETS = {0x8CCA, 0x8CCB}
NDISASM = Path(r'C:\msys64\usr\bin\ndisasm.exe')
NDISASM_SHA256 = '5789e415cc0a62b2211dd11c2bbd87225ce300ac45afb8e899f6dc8557bdcbbb'

def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()

def sha_file(path):
    return sha_bytes(Path(path).read_bytes())

if not NDISASM.is_file() or sha_file(NDISASM) != NDISASM_SHA256:
    raise SystemExit('pinned ndisasm.exe missing or hash mismatch')

def target_name_match(text):
    return bool(re.search(r'(?:g_?8cc[ab]|8cc[ab])', text, re.I))

def decode_numeric_refs(blob, module, segment):
    p = subprocess.run([str(NDISASM), '-b16', '-o0', '-'], input=blob,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    out = []
    for rawline in p.stdout.decode('utf-8', errors='replace').splitlines():
        parts = rawline.split(None, 2)
        if len(parts) < 3:
            continue
        instruction = parts[2]
        for offset in TARGET_OFFSETS:
            if re.search(r'(?<![0-9A-F])0x0*' + f'{offset:x}' + r'(?![0-9A-F])', instruction, re.I):
                out.append({'module': module, 'segment': segment, 'offset': parts[0],
                            'target_literal': f'0x{offset:04x}', 'instruction': instruction})
    return out

layout = json.loads((ROOT/'layout/manifest.json').read_text(encoding='utf-8'))
runtime = layout['runtime']
archive_bytes = {}
archive_members = {}
for lib, rec in runtime['libraries'].items():
    p = Path(rec['path'])
    data = p.read_bytes()
    actual = sha_bytes(data)
    if actual != rec['sha256']:
        raise SystemExit(f'pinned runtime library hash mismatch: {lib}')
    archive_bytes[lib] = data
    rows = list(OmfReader(communals=True).split_library(data))
    archive_members[lib] = rows

# Search public/external/COMDEF names in every OMF module in both pinned archives.
all_module_count = 0
parse_failures = []
symbol_name_hits = []
related_members = []
for lib, rows in archive_members.items():
    reader = OmfReader(communals=True)
    for index, (name, blob) in enumerate(rows):
        all_module_count += 1
        try:
            obj = reader.read(blob, name)
        except Exception as exc:
            parse_failures.append({'library': lib, 'module': name, 'index': index,
                                   'error': type(exc).__name__})
            continue
        named = []
        named.extend(('public', row['name']) for row in obj.publics)
        named.extend(('external', value) for value in obj.externals)
        named.extend(('communal', row.get('name', '')) for row in obj.communals)
        hits = [{'kind': kind, 'name': value} for kind, value in named if target_name_match(value)]
        if hits:
            symbol_name_hits.append({'library': lib, 'module': name, 'index': index, 'hits': hits})
        if any(k in name.lower() for k in ('harderr', 'doserr', 'crt0dat', 'syserr')):
            related_members.append({'library': lib, 'module': name, 'index': index,
                                    'sha256': sha_bytes(blob),
                                    'name_hits': hits,
                                    'segment_defs': [{'name': x['name'], 'class': x.get('class'),
                                                      'length': x.get('length')}
                                                     for x in obj.segment_defs],
                                    'publics': obj.publics,
                                    'externals': obj.externals,
                                    'communals': obj.communals,
                                    'fixups': [{'segment': f.get('segment'),
                                                'offset': f.get('offset'),
                                                'target_kind': f.get('target_kind'),
                                                'target': f.get('target'),
                                                'displacement': f.get('displacement'),
                                                'frame': f.get('frame'),
                                                'encoded_addend': f.get('encoded_addend')}
                                               for f in obj.linker_fixups]})

selected_rows = runtime['members'] + runtime.get('data_members', [])
selected_details = []
selected_code_segments = 0
selected_disasm_hits = []
selected_fixup_hits = []
for row in selected_rows:
    lib = row['library']
    index = row['module_index']
    name, blob = archive_members[lib][index]
    if name != row['member'] or sha_bytes(blob) != row['member_sha256']:
        raise SystemExit(f'selected runtime member identity mismatch: {lib}:{index}:{row["member"]}')
    obj = OmfReader(communals=True).read(blob, name)
    public_names = {p['name'] for p in obj.publics}
    external_names = set(obj.externals)
    communal_names = {p.get('name', '') for p in obj.communals}
    suspicious_names = sorted(x for x in public_names | external_names | communal_names if target_name_match(x))
    fixup_hits = []
    for f in obj.linker_fixups:
        displacement = f.get('displacement')
        if displacement in TARGET_OFFSETS:
            fixup_hits.append({k: f.get(k) for k in ('segment', 'offset', 'target_kind', 'target', 'displacement', 'frame')})
    selected_fixup_hits.extend({'library': lib, 'module': name, **h} for h in fixup_hits)
    for sd in obj.segment_defs:
        seg = sd['name']
        if seg not in obj.segments or not str(sd.get('class', '')).upper().endswith('CODE'):
            continue
        selected_code_segments += 1
        selected_disasm_hits.extend(decode_numeric_refs(obj.segments[seg], name, seg))
    selected_details.append({'library': lib, 'module': name, 'module_index': index,
                             'sha256': sha_bytes(blob), 'selected_by_runtime_manifest': True,
                             'segment_defs': [{'name': x['name'], 'class': x.get('class'),
                                               'length': x.get('length')}
                                              for x in obj.segment_defs],
                             'publics': obj.publics, 'externals': obj.externals,
                             'communals': obj.communals, 'suspicious_symbol_names': suspicious_names,
                             'runtime_data_placements': row.get('data_segments', []),
                             'fixup_target_offset_hits': fixup_hits})

# The DOS error helper is in the archive but was not selected into the accepted runtime set.
doserr_archive_only = [x for x in related_members if x['module'].lower() == 'dos\\doserr.c']
manifest_selected = {(x['library'], x['member']) for x in selected_rows}

result = {
    'schema': 'dos-near-state-runtime-omf-scan-v1',
    'policy': 'reads only the pinned MSC runtime archives and accepted runtime manifest; emits OMF names, lengths, fixup targets, and decoded numeric-reference text, never member bytes',
    'no_original_executable_read': True,
    'pins': {'layout_manifest_sha256': sha_file(ROOT/'layout/manifest.json'),
             'runtime_scan_script_sha256': sha_file(ROOT/'work/source-only-dos/near-state-debt-runtime-scan.py'),
             'ndisasm_sha256': sha_file(NDISASM),
             'ndisasm_path': str(NDISASM),
             'libraries': {lib: {'path': runtime['libraries'][lib]['path'],
                                 'sha256': runtime['libraries'][lib]['sha256']}
                           for lib in runtime['libraries']}},
    'archive_scan': {'module_count': all_module_count, 'parse_failures': parse_failures,
                     'target_symbol_name_hits': symbol_name_hits,
                     'related_member_summaries': related_members},
    'selected_runtime_scan': {'selected_member_count': len(selected_rows),
                              'code_segment_count': selected_code_segments,
                              'direct_8cca_8ccb_numeric_refs': selected_disasm_hits,
                              'fixup_displacements_8cca_8ccb': selected_fixup_hits,
                              'members': selected_details},
    'doserr_c': {'present_in_archive': bool(doserr_archive_only),
                 'selected_in_runtime_manifest': ('llibcr.lib', 'dos\\doserr.c') in manifest_selected,
                 'module_summary': doserr_archive_only},
}
out = ROOT/'build/workers/dos_near_state_debt_review/runtime-omf-scan.json'
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n', encoding='utf-8')
print(json.dumps({'archive_modules': all_module_count,
                  'archive_parse_failures': len(parse_failures),
                  'symbol_name_hits': len(symbol_name_hits),
                  'selected_runtime_members': len(selected_rows),
                  'selected_code_segments_scanned': selected_code_segments,
                  'direct_numeric_refs': len(selected_disasm_hits),
                  'fixup_target_offset_hits': len(selected_fixup_hits),
                  'doserr_selected': result['doserr_c']['selected_in_runtime_manifest'],
                  'report': str(out)}, indent=2))
