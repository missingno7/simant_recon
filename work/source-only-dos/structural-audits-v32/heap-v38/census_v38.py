from __future__ import annotations
import hashlib, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'tools'))
from omf import OmfReader

REPORT = ROOT / 'build/source-only-dos/build-report.json'
LLIBCR = Path(r'C:\tools\msc-6.00\LIB\llibcr.lib')
EXPECTED_BUILD_TUS = 188
EXPECTED_COMMIT = 'e4227d5'
rd = OmfReader(communals=True)
report = json.loads(REPORT.read_text(encoding='utf-8'))
units = report['translation_units']
if len(units) != EXPECTED_BUILD_TUS:
    raise SystemExit(f'expected {EXPECTED_BUILD_TUS} translation units, found {len(units)}')

object_rows = []
for unit in units:
    pin = unit['object']
    path = ROOT / Path(pin['path'])
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != pin['sha256']:
        raise SystemExit(f'object hash mismatch: {pin["path"]}')
    obj = rd.read(raw, path.name)
    extdefs = [name for name, scope in zip(obj.externals, obj.external_scopes) if scope == 'external']
    extdef_upper = {name.upper() for name in extdefs}
    fixups = [
        {'symbol': f['target'], 'target_kind': f['target_kind'], 'segment': f['segment'],
         'offset': f['offset'], 'loc': f['loc'], 'displacement': f.get('displacement')}
        for f in obj.linker_fixups if f.get('target_kind') == 'external'
    ]
    object_rows.append({
        'module': unit['module'], 'basename': unit['basename'], 'lang': unit['lang'],
        'source_path': unit['source']['path'], 'object_path': pin['path'],
        'object_sha256': digest, 'object_bytes': len(raw),
        'external_extdef_count': len(extdefs), 'external_extdefs': extdefs,
        'live_external_fixup_count': len(fixups), 'live_external_fixups': fixups,
        'public_names': [p['name'] for p in obj.publics],
    })

lib_raw = LLIBCR.read_bytes()
lib_sha = hashlib.sha256(lib_raw).hexdigest()
archive = {name.lower(): (name, blob) for name, blob in rd.split_library(lib_raw)}
required = ['dos\\stdalloc.asm', 'malloc.asm', 'fmalloc.asm', 'fdata.asm']
chain = {}
for key in required:
    if key.lower() not in archive:
        raise SystemExit(f'missing runtime member: {key}')
    name, blob = archive[key.lower()]
    member = rd.read(blob, name)
    chain[name] = {
        'member_sha256': hashlib.sha256(blob).hexdigest(), 'member_bytes': len(blob),
        'publics': [{'name': p['name'], 'segment': p['segment'], 'offset': p['offset']} for p in member.publics],
        'external_extdefs': [n for n, scope in zip(member.externals, member.external_scopes) if scope == 'external'],
        'live_external_fixups': [
            {'symbol': f['target'], 'segment': f['segment'], 'offset': f['offset'], 'loc': f['loc']}
            for f in member.linker_fixups if f.get('target_kind') == 'external'
        ],
        'segment_lengths': {k: len(v) for k, v in member.segments.items()},
    }

fdata_name = next(name for name in chain if name.lower() == 'fdata.asm')
fdata_publics = [p['name'] for p in chain[fdata_name]['publics']]
fdata_set = {n.upper() for n in fdata_publics}
matching_extdefs = []
matching_live_fixups = []
for row in object_rows:
    for symbol in row['external_extdefs']:
        if symbol.upper() in fdata_set:
            matching_extdefs.append({'module': row['module'], 'object_path': row['object_path'], 'symbol': symbol,
                                     'also_has_live_fixup': any(f['symbol'].upper() == symbol.upper() for f in row['live_external_fixups'])})
    for fixup in row['live_external_fixups']:
        if fixup['symbol'].upper() in fdata_set:
            matching_live_fixups.append({'module': row['module'], 'object_path': row['object_path'], **fixup})

extdef_names = sorted({n.upper() for row in object_rows for n in row['external_extdefs']})
fixup_names = sorted({f['symbol'].upper() for row in object_rows for f in row['live_external_fixups']})
pin_material = '\n'.join(f"{r['object_path']} {r['object_sha256']}" for r in sorted(object_rows, key=lambda x:x['object_path']))
receipt = {
    'schema': 'simant-fdata-app-extdef-selection-census-v38',
    'status': 'ROOT_REVIEW_PENDING',
    'expected_parent_commit': EXPECTED_COMMIT,
    'question': 'Can an application OMF EXTDEF / unused assembler EXTRN matching a stock fdata.asm public trigger RTLink member extraction in the absence of a live fixup?',
    'input': {
        'build_report': str(REPORT.relative_to(ROOT)).replace('\\', '/'),
        'build_report_sha256': hashlib.sha256(REPORT.read_bytes()).hexdigest(),
        'build_report_status': report.get('status'), 'translation_unit_count': len(units),
        'expected_translation_unit_count': EXPECTED_BUILD_TUS,
        'object_hash_pins_verified': len(object_rows),
        'object_pin_set_sha256': hashlib.sha256(pin_material.encode('ascii')).hexdigest(),
        'library_path': str(LLIBCR), 'library_sha256': lib_sha,
    },
    'census': {
        'application_object_count': len(object_rows),
        'distinct_external_extdef_names_casefolded': len(extdef_names),
        'distinct_live_external_fixup_names_casefolded': len(fixup_names),
        'total_external_extdef_entries': sum(r['external_extdef_count'] for r in object_rows),
        'total_live_external_fixups': sum(r['live_external_fixup_count'] for r in object_rows),
        'fdata_publics': fdata_publics,
        'matching_application_extdefs': matching_extdefs,
        'matching_application_live_fixups': matching_live_fixups,
        'all_objects': object_rows,
    },
    'stock_runtime_chain': chain,
    'interpretation': {
        'app_specific_unused_extdef_trigger': 'UNSUPPORTED: no application object declares an EXTDEF matching any stock fdata.asm public' if not matching_extdefs else 'CANDIDATE_FOUND: matching EXTDEF(s) require isolated declaration-only linker controls',
        'app_live_fixup_to_fdata_public': 'NONE' if not matching_live_fixups else 'PRESENT',
        'negative_scope': 'This census rules out an app-object EXTDEF/EXTRN to a stock fdata.asm public as the cause in this pinned 188-object build. It does not explain the prior 186-object partial-link selection and does not establish historical DGROUP placement or library extraction behavior for unrelated symbols.',
        'dependency_chain': 'stdalloc.asm has live _malloc; malloc.asm has live __fmalloc; fmalloc.asm has live __fheap; fdata.asm defines __fheap.'
    },
    'execution': {'link_controls_run': False, 'reason': 'No candidate EXTDEF exists in the actual app objects; conditional controls are not applicable.', 'generated_exes_executed': False},
}
(OUT / 'extdef-census-v38.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')

lines = [
    '# fdata EXTDEF selection census v38', '',
    '**Status: `ROOT_REVIEW_PENDING`.**', '',
    f"The pinned source-only report contains {len(units)} translation units; every one of its object SHA-256 pins was verified before parsing.",
    f"Build report SHA-256: `{receipt['input']['build_report_sha256']}`. Expected parent commit: `{EXPECTED_COMMIT}`.", '',
    '## Result', '',
    f"Stock `fdata.asm` publics: {', '.join('`'+x+'`' for x in fdata_publics) or '(none)'}.",
    f"Application EXTDEF matches: {len(matching_extdefs)}. Application live external fixup matches: {len(matching_live_fixups)}.",
]
if matching_extdefs:
    lines += ['', '| Module | Symbol | Live fixup in object |', '|---|---|---|']
    lines += [f"| `{x['module']}` | `{x['symbol']}` | {x['also_has_live_fixup']} |" for x in matching_extdefs]
else:
    lines += ['', 'No application object declares an OMF EXTDEF matching a public defined by stock `fdata.asm`. Therefore an unused app-side assembler `EXTRN __fheap` (or another `fdata.asm` public) is absent from this 188-object build and cannot account for the partial link’s `fdata.asm` selection. No conditional link controls were run because the required candidate does not exist.']
lines += ['', '## Pinned stock CRT dependency chain', '', '| Member | Publics | Live external fixups |', '|---|---|---|']
for name, row in chain.items():
    pubs = ', '.join(p['name'] for p in row['publics']) or '—'
    refs = ', '.join(f['symbol'] for f in row['live_external_fixups']) or '—'
    lines.append(f"| `{name}` | {pubs} | {refs} |")
lines += ['', 'The natural CRT chain is `stdalloc.asm → malloc.asm → fmalloc.asm → fdata.asm`, with live edges `_malloc`, `__fmalloc`, and `__fheap` respectively. This chain describes ordinary runtime dependencies; the census found no matching fdata public in any app object.']
lines += ['', '## Scope', '', 'This is a negative result for app-object EXTDEF-driven extraction in the pinned 188-object build. It does not identify the cause of the earlier 186-object partial-link selection, and it says nothing about historical `DGROUP:79F0` placement. No linker control was run and no generated executable was run.', '', 'Machine-readable per-object EXTDEF and live-fixup inventories are in [extdef-census-v38.json](extdef-census-v38.json).']
(OUT / 'review-v38.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
print('objects', len(object_rows), 'app EXTDEF matches', len(matching_extdefs), 'app live fixup matches', len(matching_live_fixups))
print('fdata publics', fdata_publics)
print('chain members', list(chain))
print('build report sha256', receipt['input']['build_report_sha256'])
print('receipt', OUT / 'extdef-census-v38.json')
