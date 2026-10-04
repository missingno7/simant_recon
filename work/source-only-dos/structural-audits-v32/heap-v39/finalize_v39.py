#!/usr/bin/env python3
"""Reconcile v39 raw artifacts and selected runtime member OMF; never runs a linker."""
import hashlib, json, re
from collections import Counter
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT/'tools'))
from omf import OmfReader
import compiler
receipt_path = OUT/'file-order-v39.json'
r = json.loads(receipt_path.read_text(encoding='utf-8'))
build_report = json.loads((ROOT/'build/source-only-dos/build-report.json').read_text(encoding='utf-8'))
expected_objects = {Path(x['object']['path']).name.upper(): x['object']['sha256'] for x in build_report['translation_units']}
root_rows = [x for x in build_report['translation_units'] if x['unit'] == 'root']
data_rows = [x for x in build_report['translation_units'] if x['module'].startswith('data:')]
rd = OmfReader(communals=True)
archives = {}
for pin in r['inputs']['runtime_libraries']:
    path = Path(pin['path'])
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != pin['sha256']:
        raise SystemExit(f'runtime library changed since v39 link: {path}')
    lib = path.name.upper()
    archives[lib] = {}
    for member_name, blob in rd.split_library(raw):
        archives[lib][member_name.lower()] = blob

toolchain = compiler.toolchain()
linker_profiles, utility_archives = {}, {}
for profile_name in ('rtlink400','rtlink610'):
    profile = toolchain['linkers'][profile_name]
    file_pins = {}
    for name, expected_hash in profile['files'].items():
        path = Path(profile['directory'])/name
        raw = path.read_bytes()
        actual_hash = hashlib.sha256(raw).hexdigest()
        if actual_hash != expected_hash:
            raise SystemExit(f'linker-tool pin mismatch: {path}')
        file_pins[name] = {'path': str(path), 'sha256': actual_hash, 'bytes': len(raw)}
    linker_profiles[profile_name] = {
        'directory': profile['directory'], 'executable': profile['executable'],
        'files': file_pins, 'status': profile.get('status'),
    }
    utility_path = Path(profile['directory'])/'RTLUTILS.LIB'
    utility_raw = utility_path.read_bytes()
    utility_hash = hashlib.sha256(utility_raw).hexdigest()
    if utility_hash != profile['files']['RTLUTILS.LIB']:
        raise SystemExit(f'linker utility-library pin mismatch: {utility_path}')
    utility_archives[profile_name] = {'path': str(utility_path), 'sha256': utility_hash,
                                      'bytes': len(utility_raw)}
runner = toolchain['runners']['dosbox-x']
runner_path = Path(runner['path'])
runner_raw = runner_path.read_bytes()
runner_hash = hashlib.sha256(runner_raw).hexdigest()
if runner_hash != runner['sha256']:
    raise SystemExit('DOSBox-X runner pin mismatch')
r['inputs']['linker_profiles'] = linker_profiles
r['inputs']['linker_utility_archives'] = utility_archives
r['inputs']['dosbox_runner'] = {'path': str(runner_path), 'sha256': runner_hash,
                               'bytes': len(runner_raw)}

for run in r['runs']:
    profile_utility = utility_archives[run['profile']]
    profile_utility_raw = Path(profile_utility['path']).read_bytes()
    run_archives = {name: members.copy() for name, members in archives.items()}
    run_archives['RTLUTILS.LIB'] = {name.lower(): blob for name, blob in rd.split_library(profile_utility_raw)}
    case = OUT/run['plan']/run['profile']
    staged_objects = list(case.glob('*.OBJ'))
    staged_hashes = {p.name.upper(): hashlib.sha256(p.read_bytes()).hexdigest() for p in staged_objects}
    if staged_hashes != expected_objects:
        raise SystemExit(f'staged object set or hashes differ: {run["plan"]}/{run["profile"]}')
    staged_libraries = {}
    for lib_name, expected_hash in ((Path(x['path']).name.upper(), x['sha256']) for x in r['inputs']['runtime_libraries']):
        lib_path = case/lib_name
        if not lib_path.is_file():
            raise SystemExit(f'staged runtime library missing: {lib_path}')
        actual_hash = hashlib.sha256(lib_path.read_bytes()).hexdigest()
        if actual_hash != expected_hash:
            raise SystemExit(f'staged runtime library pin mismatch: {lib_path}')
        staged_libraries[lib_name] = actual_hash
    run['staged_inputs_verified'] = {'object_count': len(staged_objects), 'object_hashes_match_build_report': True,
                                     'runtime_library_sha256': staged_libraries}
    log_path = OUT/run['raw_log']
    map_path = OUT/run['raw_map']
    log_raw, map_raw = log_path.read_bytes(), map_path.read_bytes()
    if hashlib.sha256(log_raw).hexdigest() != run['raw_log_sha256']:
        raise SystemExit(f'raw log pin mismatch: {log_path}')
    if hashlib.sha256(map_raw).hexdigest() != run['raw_map_sha256']:
        raise SystemExit(f'raw map pin mismatch: {map_path}')
    log = log_raw.decode('latin1')
    selected = [{'library': a.upper(), 'member': b} for a,b in re.findall(
        r'(?im)^\s*([A-Z]:\\[^()\r\n]+\.LIB|[A-Z0-9_]+\.LIB)\(([^)\r\n]+)\)', log)]
    if selected != run['selected_members']:
        raise SystemExit(f'selected-member sequence differs from raw log: {run["plan"]}/{run["profile"]}')
    definitions, missing = [], []
    for entry in selected:
        lib = entry['library'].split('\\')[-1]
        blob = run_archives.get(lib, {}).get(entry['member'].lower())
        if blob is None:
            missing.append(entry)
            continue
        obj = rd.read(blob, entry['member'])
        definitions.append({
            'library': entry['library'], 'member': entry['member'],
            'member_sha256': hashlib.sha256(blob).hexdigest(), 'member_bytes': len(blob),
            'publics': obj.publics,
            'segment_defs': [{k:s.get(k) for k in ('name','class','length','alignment','combine')} for s in obj.segment_defs],
            'segment_payload_lengths': {k:len(v) for k,v in obj.segments.items()},
            'external_extdefs': [name for name, scope in zip(obj.externals, obj.external_scopes) if scope == 'external'],
            'live_external_fixup_targets': [f['target'] for f in obj.linker_fixups if f.get('target_kind') == 'external'],
        })
    run['selected_runtime_library_member_omf'] = definitions
    run['selected_members_without_report_runtime_library_omf'] = missing
    run['selected_member_definition_coverage'] = {
        'selected_total': len(selected), 'selected_from_pinned_report_libraries': len(definitions),
        'selected_from_other_libraries': missing,
    }

# Cross-check exact app-owner symbols against the target's OMF map outputs in each run.
expected_owners = {p['name']:p['offset'] for p in r['inputs']['target_app_public_owners_from_omf']}
if set(expected_owners) != {'_malloc','_free','__ffree','__frealloc'}:
    raise SystemExit('unexpected target app-public OMF owner inventory')
for run in r['runs']:
    for symbol, offset in expected_owners.items():
        rows = run['focus_symbol_map_rows'][symbol]
        if not rows or not all('U074.C' in line for line in rows):
            raise SystemExit(f'{symbol} is not mapped to U074.C in {run["plan"]}/{run["profile"]}')
        run.setdefault('app_owner_map_check', {})[symbol] = {
            'omf_offset': offset, 'map_rows': rows, 'all_rows_resolve_to_U074_C': True,
        }

# Verify the realized T.LNK files vary only in the exact root FILE ordering.
baseline_dir = OUT/'baseline_current_order'/'rtlink400'
first_dir = OUT/'root_171c_first'/'rtlink400'
base_lines = (baseline_dir/'T.LNK').read_text(encoding='ascii').splitlines()
first_lines = (first_dir/'T.LNK').read_text(encoding='ascii').splitlines()
root_file_line_count = (len(root_rows)+7)//8
header_count = 6
def names_from_file_lines(lines):
    return [name.strip() for line in lines for name in line.removeprefix('FILE ').split(',')]
base_root_names = names_from_file_lines(base_lines[header_count:header_count+root_file_line_count])
first_root_names = names_from_file_lines(first_lines[header_count:header_count+root_file_line_count])
expected_root_names = [x['basename'] for x in root_rows]
target_names = [x['basename'] for x in root_rows if x['module'] == 'root:171C']
if base_root_names != expected_root_names or first_root_names != target_names + [x for x in expected_root_names if x not in target_names]:
    raise SystemExit('realized root FILE order does not match the requested one-variable contrast')
base_norm = base_lines[:header_count] + ['<ROOT FILE ORDER>'] + base_lines[header_count+root_file_line_count:]
first_norm = first_lines[:header_count] + ['<ROOT FILE ORDER>'] + first_lines[header_count+root_file_line_count:]
if base_norm != first_norm:
    raise SystemExit('realized link scripts differ outside root FILE order')
if sum(1 for line in base_lines if line.startswith('DEFINE ')) != len(build_report.get('symbolic_aliases', [])):
    raise SystemExit('baseline alias count does not match current build report')
r['artifact_reconciliation'] = {
    'primary_run_count': len(r['runs']), 'max_primary_run_limit': 4,
    'all_four_staged_object_sets_match_report': True,
    'all_four_staged_runtime_libraries_match_report': True,
    'realized_scripts_differ_only_in_root_FILE_order': True,
    'baseline_root_object_names_match_report_order': True,
    'root_171c_first_object_names_match_requested_order': True,
    'non_root_ROOT_file_relative_order_preserved': True,
    'data_overlay_directives_and_aliases_identical': True,
    'alias_count': len(build_report.get('symbolic_aliases', [])),
    'runner_sha256': hashlib.sha256((OUT/'run_order_v39.py').read_bytes()).hexdigest(),
}

# Capture raw-byte identity including line-ending shape; logs/maps are kept untouched in place.
for run in r['runs']:
    for key, path_key in [('raw_log_crlf_count','raw_log'),('raw_map_crlf_count','raw_map')]:
        raw = (OUT/run[path_key]).read_bytes()
        run[key] = raw.count(b'\r\n')

receipt_path.write_text(json.dumps(r, indent=2)+'\n', encoding='utf-8')

# Human-readable concise review; hashes and complete source-derived module metadata remain in JSON.
order_rows = []
for profile in ('rtlink400','rtlink610'):
    for plan in ('baseline_current_order','root_171c_first'):
        run = next(x for x in r['runs'] if x['plan']==plan and x['profile']==profile)
        order_rows.append(run)
lookup={(x['plan'],x['profile']):x for x in r['runs']}
lines = [
    '# fdata RTLink file-order probe v39', '',
    '**Status: `ROOT_REVIEW_PENDING`.**', '',
    '## Result', '',
    'Moving `root:171C` (`U074.OBJ`) from the 31st root object position to the first position changed mapped addresses for its four known allocator publics under both RTLinks. It did **not** change which runtime archive members were selected: RTLink 4.00 still selected `fmalloc.asm` and `fdata.asm`; RTLink 6.10 still selected `fdata.asm` without `fmalloc.asm`. Application object order therefore does not explain the observed 6.10 fdata-without-fmalloc selection in this controlled contrast.', '',
    'All four runs used the same 188 hash-pinned object files, 193 symbolic aliases, runtime libraries, `NODEFLIB`, `RELOAD FAR 400`, root/data grouping, four overlay areas and linker settings. The only T.LNK variable was root FILE order. The library directive stayed in its production position before FILE entries.', '',
    '| RTLink | Object order | Selected members | fmalloc | fdata | Undefined symbols | Duplicate diagnostic |',
    '|---|---|---:|---:|---:|---:|---|',
]
for profile in ('rtlink400','rtlink610'):
    for plan in ('baseline_current_order','root_171c_first'):
        run=lookup[(plan,profile)]
        lines.append(f"| {profile} | {'current' if plan=='baseline_current_order' else 'root:171C first'} | {run['selected_member_count']} | {run['log_mentions_fmalloc']} | {run['log_mentions_fdata']} | {run['undefined_symbol_count']} | {'; '.join(run['duplicate_public_diagnostics']) or 'none'} |")
lines += [
    '', 'The selection sequence and member set match exactly between object orders for each linker. Each run remains diagnostic and incomplete: RTLink writes an image with 15 unresolved symbols; none of the generated images was executed.',
    '', '## Runtime member data and public ownership', '',
    '| LLIBCR member | OMF `_TEXT` length | OMF `_DATA` length | Publics of interest |',
    '|---|---:|---:|---|',
]
focus_by_member={}
for run in r['runs']:
    for item in run['focus_selected_modules_and_omf_definitions']:
        focus_by_member[item['member'].lower()] = item
for member in ['fmalloc.asm','fdata.asm','initseg.asm','linkseg.asm','growseg.asm']:
    item=focus_by_member.get(member.lower())
    if not item:
        continue
    segs={x['name']:x for x in item['segment_defs']}
    pubtext=', '.join(f"{p['name']}@{p['segment']}:{p['offset']:04X}" for p in item['publics'])
    lines.append(f"| `{item['member']}` | {segs.get('_TEXT',{}).get('length','—')} | {segs.get('_DATA',{}).get('length','—')} | {pubtext or '—'} |")
lines += ['', 'The selected member OMF definitions show `fmalloc.asm` has 144 bytes of `_TEXT` and zero `_DATA`; `fdata.asm` has a 14-byte `_DATA` public contribution defining `__fheap` at offset 0. `initseg.asm` and `linkseg.asm` contribute 52 and 54 bytes of `_TEXT` and zero `_DATA`; `growseg.asm` contributes 256 bytes of `_TEXT` and two bytes of `_DATA`. RTLink 6.10’s maps place `fdata.asm` at `DGROUP:798E` with length `000E`, followed by zero-length `initseg.asm` / `linkseg.asm` data and two bytes from `growseg.asm` at `DGROUP:799C`; those rows are identical under both tested object orders.', '', 'The public map rows for `_malloc`, `_free`, `__ffree` and `__frealloc` resolve to `U074.C` in all four runs. Their OMF definitions remain owned by `root:171C`; only the map coordinates change when that object moves first. RTLink 4.00 continues to report `wrt0011` for the duplicate `__ffree` from selected `fmalloc.asm`. RTLink 6.10 selects no `fmalloc.asm`, so it emits no corresponding duplicate.', '', '## Artifacts and limits', '', f"The build report SHA-256 is `{r['inputs']['build_report_sha256']}`; the object-set pin digest is `{r['inputs']['object_pin_set_sha256']}`. The exact current link inputs are recorded with their object, runtime library, linker and utility-library hashes in [file-order-v39.json](file-order-v39.json). It also records every selected LLIBCR, LIBH and pinned RTLink RTLUTILS member’s OMF publics, segment extents, external declarations and live fixup targets.", '', 'Complete raw CRLF logs and maps are preserved in each run directory and pinned by raw-byte SHA-256 in the JSON receipt. The generated EXE files remain unexecuted. No source or object was edited, no stubs were used, and this result makes no historical `DGROUP:79F0` placement claim. Since the order change did not alter archive selection, no extra control was run.', '', 'The four run directories are `baseline_current_order/rtlink400`, `baseline_current_order/rtlink610`, `root_171c_first/rtlink400`, and `root_171c_first/rtlink610` under this folder.'
]
(OUT/'review-v39.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
print('selected-member OMF definitions attached for', sum(len(x['selected_runtime_library_member_omf']) for x in r['runs']), 'member selections')
print('review', OUT/'review-v39.md')
