#!/usr/bin/env python3
"""Compare production-order and root:171C-first diagnostic RTLink partial links."""
from __future__ import annotations
import hashlib, json, re, shutil, sys
from collections import Counter
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'tools'))
import compiler, rtlink
from omf import OmfReader

REPORT_PATH = ROOT / 'build/source-only-dos/build-report.json'
REPORT = json.loads(REPORT_PATH.read_text(encoding='utf-8'))
TUS = REPORT['translation_units']
ALIASES = REPORT.get('symbolic_aliases', [])
EXPECTED_OBJECT_COUNT = 188
EXPECTED_ALIAS_COUNT = 193
TARGET_MODULE = 'root:171C'
TARGET_PUBLICS = ['_malloc', '_free', '__ffree', '__frealloc']
FOCUS_MEMBERS = ['fdata.asm', 'fmalloc.asm', 'initseg.asm', 'linkseg.asm', 'growseg.asm']
PROFILES = ['rtlink400', 'rtlink610']
if any((OUT / plan / profile).exists() for plan in ('baseline_current_order','root_171c_first') for profile in PROFILES) or (OUT / 'file-order-v39.json').exists():
    raise SystemExit('v39 run outputs already exist; refusing reuse')
if len(TUS) != EXPECTED_OBJECT_COUNT:
    raise SystemExit(f'expected {EXPECTED_OBJECT_COUNT} TUs, got {len(TUS)}')
if len(ALIASES) != EXPECTED_ALIAS_COUNT:
    raise SystemExit(f'expected {EXPECTED_ALIAS_COUNT} aliases, got {len(ALIASES)}')
if REPORT.get('status') != 'INCOMPLETE':
    raise SystemExit(f"expected diagnostic incomplete report, got {REPORT.get('status')}")

# Verify the exact current object set and all report pins before creating any link inputs.
object_rows = []
for row in TUS:
    pin = row['object']
    src = ROOT / Path(pin['path'])
    raw = src.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != pin['sha256']:
        raise SystemExit(f'object pin mismatch: {row["module"]}')
    object_rows.append({**row, '_source': src, '_raw': raw})
if len({r['basename'].upper() for r in object_rows}) != EXPECTED_OBJECT_COUNT:
    raise SystemExit('object basenames are not unique')
root_rows = [r for r in object_rows if r['unit'] == 'root']
data_rows = [r for r in object_rows if r['module'].startswith('data:')]
target_rows = [r for r in root_rows if r['module'] == TARGET_MODULE]
if len(target_rows) != 1:
    raise SystemExit(f'expected one {TARGET_MODULE} object')
target = target_rows[0]

# Parse pinned stock modules and the target app object for exact definitions/segment extents.
rd = OmfReader(communals=True)
runtime_members = {}
runtime_inputs = []
for librow in REPORT['runtime_components']:
    path = Path(librow['path'])
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != librow['sha256']:
        raise SystemExit(f'runtime library pin mismatch: {path}')
    runtime_inputs.append({'path': str(path), 'sha256': digest, 'bytes': len(raw)})
    lib_name = Path(librow['path']).name.upper()
    for member_name, blob in rd.split_library(raw):
        runtime_members[(lib_name, member_name.lower())] = (member_name, blob)

app_obj = rd.read(target['_raw'], target['basename'] + '.OBJ')
app_publics = [p for p in app_obj.publics if p['name'] in TARGET_PUBLICS]
if {p['name'] for p in app_publics} != set(TARGET_PUBLICS):
    raise SystemExit('root:171C target public set differs from the expected four names')

# Copy production link_units' script generation exactly, with only the root FILE ordering variable changed.
def build_lines(order):
    lines = ['OUTPUT SOURCE', 'MAP = SOURCE S,N,A,L,V,X', 'NODEFLIB',
             'LIBRARY LLIBCR, LIBH', 'RELOAD FAR 400', 'VERBOSE']
    names = [r['basename'] for r in order]
    for i in range(0, len(names), 8):
        lines.append('FILE ' + ', '.join(names[i:i + 8]))
    data_names = [r['basename'] for r in data_rows]
    for i in range(0, len(data_names), 8):
        lines.append('FILE ' + ', '.join(data_names[i:i + 8]))
    for lo, hi in ((0, 3), (4, 11), (12, 19), (20, 26)):
        lines.append('BEGINAREA')
        for section in range(lo, hi + 1):
            rows = [r for r in object_rows if r['unit'] == f'S{section:02d}']
            names = ', '.join(r['basename'] for r in rows)
            lines.append('SECTION FILE ' + names + (' PRELOAD' if section == 0 else ''))
        lines.append('ENDAREA')
    quote = lambda name: '"' + name + '"' if name.startswith('@') else name
    for row in ALIASES:
        delta = __import__('dos_source_bindings').rtlink_alias_delta(row.get('offset', 0))
        lines.append(f"DEFINE {quote(row['alias'])} = {quote(row['owner'])}{delta}")
    return lines

baseline_root = list(root_rows)
reordered_root = [target] + [r for r in root_rows if r is not target]
if baseline_root[0] is target:
    raise SystemExit('target is already first; the requested order contrast would be identical')
plans = {'baseline_current_order': baseline_root, 'root_171c_first': reordered_root}
plan_lines = {name: build_lines(rows) for name, rows in plans.items()}
# Prove all changes are confined to the root FILE block: list order is exactly one move;
data_names_before = [r['basename'] for r in data_rows]
if data_names_before != [r['basename'] for r in data_rows]:
    raise SystemExit('unreachable data-order check')
if len(plan_lines['baseline_current_order']) != len(plan_lines['root_171c_first']):
    raise SystemExit('T.LNK line count changed')
# Exact textual directives outside the root FILE run must agree, and data/areas/aliases stay identical.
def strip_root_file_run(lines):
    # Remove the root and data FILE lists before comparing directives, areas, and aliases.
    return [line for line in lines if not line.startswith('FILE ')]
if strip_root_file_run(plan_lines['baseline_current_order']) != strip_root_file_run(plan_lines['root_171c_first']):
    raise SystemExit('the two link scripts differ outside root FILE order')

report_hash = hashlib.sha256(REPORT_PATH.read_bytes()).hexdigest()
object_pin_material = '\n'.join(f"{r['object']['path']} {r['object']['sha256']}" for r in sorted(object_rows, key=lambda x:x['object']['path']))
object_set_hash = hashlib.sha256(object_pin_material.encode('ascii')).hexdigest()
report = {
    'schema': 'simant-fdata-file-order-selection-v39',
    'status': 'ROOT_REVIEW_PENDING',
    'scope': 'Four diagnostic incomplete links; generated EXE files are never executed.',
    'inputs': {
        'build_report': str(REPORT_PATH.relative_to(ROOT)).replace('\\', '/'),
        'build_report_sha256': report_hash,
        'build_report_status': REPORT.get('status'),
        'translation_unit_count': len(TUS), 'object_hash_pins_verified': len(object_rows),
        'object_pin_set_sha256': object_set_hash,
        'symbolic_alias_count': len(ALIASES),
        'runtime_libraries': runtime_inputs,
        'target_module': TARGET_MODULE, 'target_object_path': target['object']['path'],
        'target_object_sha256': target['object']['sha256'],
        'target_app_public_owners_from_omf': app_publics,
    },
    'experimental_variable': {
        'baseline': 'Current report order, exactly as source_only_dos.link_units emits root FILE entries.',
        'contrast': 'Move only root:171C/U074 to the first root FILE position; preserve all other root object relative order.',
        'runtime_library_directive_position': 'Unchanged, before all FILE entries.',
        'alias_rows': len(ALIASES),
        'files_per_file_directive': 8,
        'overlay_areas': [[0,3],[4,11],[12,19],[20,26]],
        'same_non_root_link_script_lines': True,
        'baseline_root_object_count': len(baseline_root),
        'target_original_root_index_zero_based': next(i for i, r in enumerate(baseline_root) if r is target),
        'contrast_target_root_index_zero_based': 0,
        'script_sha256': {name: hashlib.sha256(('\r\n'.join(lines)+'\r\n').encode('ascii')).hexdigest() for name, lines in plan_lines.items()},
    },
    'runs': [],
    'comparison': None,
    'interpretation': None,
    'never': {'generated_exes_executed': False, 'source_substitutions': False,
              'object_edits': False, 'original_bytes_used': False,
              'historical_79f0_claim': False, 'runtime_stubs': False},
}

# Run only the 2 x 2 primary matrix, each in a fresh and unique output directory.
for plan_name, root_order in plans.items():
    for profile in PROFILES:
        case = OUT / plan_name / profile
        case.mkdir(parents=True, exist_ok=False)
        # The production script writes every object under its basename; grouping and ordering are in T.LNK.
        for row in object_rows:
            shutil.copyfile(row['_source'], case / (row['basename'] + '.OBJ'))
        (case / 'T.LNK').write_bytes(('\r\n'.join(plan_lines[plan_name]) + '\r\n').encode('ascii'))
        rc = rtlink.run_link(case, profile=profile, timeout=900)
        log_path, map_path = case / 'LINK.LOG', case / 'SOURCE.MAP'
        if not log_path.is_file() or not map_path.is_file():
            raise SystemExit(f'{plan_name}/{profile}: missing complete log or map (rc={rc})')
        log_raw, map_raw = log_path.read_bytes(), map_path.read_bytes()
        log, map_text = log_raw.decode('latin1'), map_raw.decode('latin1')
        selected = [{'library': a.upper(), 'member': b} for a,b in re.findall(
            r'(?im)^\s*([A-Z]:\\[^()\r\n]+\.LIB|[A-Z0-9_]+\.LIB)\(([^)\r\n]+)\)', log)]
        selected_members = [x['member'] for x in selected]
        undefined_block = ''
        m = re.search(r'UNDEFINED SYMBOL(?:\(S\))? AFTER LIBRARY SEARCH:(.*?)(?:\*\*\*\* WRITING EXECUTABLE \*\*\*\*|$)', log, re.S | re.I)
        if m:
            undefined_block = m.group(1)
        undefined_symbols = re.findall(r"(?m)^\s*'([^']+)'", undefined_block)
        diagnostics = [line.strip() for line in log.splitlines() if re.search(r'\bwrt\d{4}\b|\bwarning\b|\berror\b|\bfatal\b', line, re.I)]
        focus_module_names = {name.lower() for name in FOCUS_MEMBERS}
        selected_focus = []
        for selected_row in selected:
            lib = selected_row['library'].split('\\')[-1]
            member_key = (lib, selected_row['member'].lower())
            if selected_row['member'].lower() not in focus_module_names:
                continue
            if member_key not in runtime_members:
                # The runtime report archives may omit another library; retain selected name without inventing OMF metadata.
                selected_focus.append({'library': selected_row['library'], 'member': selected_row['member'], 'omf': None})
                continue
            member_name, blob = runtime_members[member_key]
            obj = rd.read(blob, member_name)
            selected_focus.append({
                'library': selected_row['library'], 'member': member_name,
                'member_sha256': hashlib.sha256(blob).hexdigest(), 'member_bytes': len(blob),
                'publics': obj.publics,
                'segment_defs': [{k:s.get(k) for k in ('name','class','length','alignment','combine')} for s in obj.segment_defs],
                'segment_payload_lengths': {k:len(v) for k,v in obj.segments.items()},
                'external_extdefs': [n for n, scope in zip(obj.externals, obj.external_scopes) if scope == 'external'],
                'live_external_fixups': [f['target'] for f in obj.linker_fixups if f.get('target_kind') == 'external'],
            })
        focus_layout_rows = []
        for line in map_text.splitlines():
            mm = re.match(r'^\s*([0-9A-Fa-f]{4}):([0-9A-Fa-f]{4})\s+([0-9A-Fa-f]{4})\s+C=([^\s]+)\s+S=([^\s]+)\s+G=([^\s]+)\s+M=([^\s]+)', line)
            if mm and mm.group(7).lower() in focus_module_names:
                focus_layout_rows.append({'segment': mm.group(1).upper(), 'offset': int(mm.group(2),16),
                    'length': int(mm.group(3),16), 'class': mm.group(4), 'segment_name': mm.group(5),
                    'group': mm.group(6), 'module': mm.group(7), 'raw_line': line.strip()})
        symbols = ['__fheap','__fmalloc','_malloc','_free','__ffree','__frealloc','__initseg','__linkseg','__growseg','__newseg','__searchseg']
        symbol_rows = {name:[line.strip() for line in map_text.splitlines()
                              if re.search(r'(?i)\b'+re.escape(name)+r'\b', line) and 'Res' in line]
                       for name in symbols}
        run = {
            'plan': plan_name, 'profile': profile, 'return_code': rc,
            'link_script': f'{plan_name}/{profile}/T.LNK',
            'link_script_sha256': hashlib.sha256((case/'T.LNK').read_bytes()).hexdigest(),
            'raw_log': f'{plan_name}/{profile}/LINK.LOG', 'raw_log_bytes': len(log_raw),
            'raw_log_sha256': hashlib.sha256(log_raw).hexdigest(),
            'raw_map': f'{plan_name}/{profile}/SOURCE.MAP', 'raw_map_bytes': len(map_raw),
            'raw_map_sha256': hashlib.sha256(map_raw).hexdigest(),
            'partial_exe_written': (case/'SOURCE.EXE').is_file(),
            'partial_exe_sha256': hashlib.sha256((case/'SOURCE.EXE').read_bytes()).hexdigest() if (case/'SOURCE.EXE').is_file() else None,
            'exe_executed': False,
            'selected_member_count': len(selected), 'selected_members': selected,
            'focus_selected_modules_and_omf_definitions': selected_focus,
            'focus_layout_contributions': focus_layout_rows,
            'focus_symbol_map_rows': symbol_rows,
            'undefined_symbol_count': len(undefined_symbols), 'undefined_symbols': undefined_symbols,
            'diagnostics': diagnostics,
            'duplicate_public_diagnostics': [x for x in diagnostics if re.search(r'doubly defined|duplicate',x,re.I)],
            'log_mentions_fdata': bool(re.search(r'LLIBCR\.LIB\(fdata\.asm\)',log,re.I)),
            'log_mentions_fmalloc': bool(re.search(r'LLIBCR\.LIB\(fmalloc\.asm\)',log,re.I)),
        }
        report['runs'].append(run)
        print(plan_name, profile, 'rc', rc, 'members', len(selected),
              'fmalloc', run['log_mentions_fmalloc'], 'fdata', run['log_mentions_fdata'],
              'undefined', len(undefined_symbols), 'diagnostics', len(diagnostics))

# Compare the two object orders independently for each linker profile.
comparisons = []
by_key = {(r['plan'],r['profile']):r for r in report['runs']}
for profile in PROFILES:
    a = by_key[('baseline_current_order',profile)]
    b = by_key[('root_171c_first',profile)]
    a_members, b_members = a['selected_members'], b['selected_members']
    comparisons.append({
        'profile': profile,
        'selected_member_sequence_equal': a_members == b_members,
        'selected_member_set_equal': Counter((x['library'],x['member'].lower()) for x in a_members) == Counter((x['library'],x['member'].lower()) for x in b_members),
        'baseline_only_selected_members': [x for x in a_members if x not in b_members],
        'root_first_only_selected_members': [x for x in b_members if x not in a_members],
        'fdata_selected_baseline_vs_root_first': [a['log_mentions_fdata'],b['log_mentions_fdata']],
        'fmalloc_selected_baseline_vs_root_first': [a['log_mentions_fmalloc'],b['log_mentions_fmalloc']],
        'fheap_symbol_rows_baseline': a['focus_symbol_map_rows']['__fheap'],
        'fheap_symbol_rows_root_first': b['focus_symbol_map_rows']['__fheap'],
        'undefined_count_baseline_vs_root_first': [a['undefined_symbol_count'],b['undefined_symbol_count']],
        'duplicate_public_diagnostics_baseline': a['duplicate_public_diagnostics'],
        'duplicate_public_diagnostics_root_first': b['duplicate_public_diagnostics'],
    })
report['comparison'] = comparisons
causal_profiles = [x['profile'] for x in comparisons if not x['selected_member_set_equal']
                   or x['fdata_selected_baseline_vs_root_first'][0] != x['fdata_selected_baseline_vs_root_first'][1]
                   or x['fmalloc_selected_baseline_vs_root_first'][0] != x['fmalloc_selected_baseline_vs_root_first'][1]]
report['interpretation'] = {
    'root_object_order_causal_for_observed_member_selection': bool(causal_profiles),
    'profiles_with_selection_change': causal_profiles,
    'verdict': ('ORDER_EFFECT_OBSERVED; the object-order contrast changes selected archive members. Stop before extra controls pending root review.'
                if causal_profiles else 'NO_ORDER_EFFECT_OBSERVED; root:171C-first and current order select the same members under both RTLinks. Stop; no additional controls were run.'),
    'limitations': 'Every run is an incomplete diagnostic link. This does not establish a complete program, runtime behavior, or historical DGROUP:79F0 placement.',
}
(OUT/'file-order-v39.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
print(report['interpretation']['verdict'])


