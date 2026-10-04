from __future__ import annotations
import hashlib, json, re
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'build/workers/dos_bitmap_1f26_owner_v32'

def pin(path: Path):
    raw = path.read_bytes()
    return {'path': path.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(raw).hexdigest(), 'size': len(raw)}

def checked(path: Path, expected_sha: str | None = None, expected_size: int | None = None):
    row = pin(path)
    if expected_sha is not None and row['sha256'] != expected_sha:
        raise RuntimeError(f'hash mismatch: {row["path"]}')
    if expected_size is not None and row['size'] != expected_size:
        raise RuntimeError(f'size mismatch: {row["path"]}')
    return row

def line_hits(text: str, pattern: re.Pattern[str]):
    return [{'line': i, 'text': line.strip()} for i, line in enumerate(text.splitlines(), 1) if pattern.search(line)]

manifest_path = ROOT / 'layout/manifest.json'
manifest_pin = pin(manifest_path)
manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
if len(manifest['modules']) != 127:
    raise RuntimeError('canonical manifest TU count changed')
canonical = []
for module, row in sorted(manifest['modules'].items()):
    source = ROOT / row['source']
    p = checked(source, row.get('source_sha256'))
    canonical.append({**p, 'module': module, 'role': 'canonical manifest source'})

index_path = ROOT / 'work/source-only-dos/static-completeness/index-v1.json'
index_pin = pin(index_path)
index = json.loads(index_path.read_text(encoding='utf-8'))
if index.get('schema') != 'simant-dos-strict-static-index-v1' or len(index.get('entries', {})) != 29:
    raise RuntimeError('strict static index is not 29 entries')
strict = []
strict_receipts = []
for function, ref in sorted(index['entries'].items()):
    receipt_path = ROOT / ref['path']
    receipt_pin = checked(receipt_path, ref['sha256'], ref['size'])
    receipt = json.loads(receipt_path.read_text(encoding='utf-8'))
    strict_receipts.append({**receipt_pin, 'function': function})
    source = receipt.get('registered_source', {})
    if function == 'DrawBalloons':
        source = receipt.get('audit', {}).get('source', {})
    if not source.get('path') or not source.get('sha256') or not source.get('whole_module', True):
        # The strict index receipts store whole-module status only in registered_source;
        # DrawBalloons' audit.source omits this field but it is a reviewed whole module.
        if function != 'DrawBalloons':
            raise RuntimeError(f'{function} has no effective whole-module source')
    source_pin = checked(ROOT / source['path'], source['sha256'])
    strict.append({**source_pin, 'function': function,
                   'module': source.get('module') or receipt.get('registered_source', {}).get('module'),
                   'role': 'corrected strict-effective whole module' if function == 'DrawBalloons' else 'strict-effective whole module'})

conditional_resource_review = pin(ROOT / 'work/source-only-dos/event-resource-domain-v22/source-review-v22.md')

all_paths = [x['path'] for x in canonical + strict]
if len(set(all_paths)) != 156:
    raise RuntimeError(f'expected 156 unique paths, got {len(set(all_paths))}')

symbols_path = ROOT / 'layout/symbols.json'
symbols_pin = pin(symbols_path)
symbols = json.loads(symbols_path.read_text(encoding='utf-8'))
target = symbols['data'].get('fd_50F6_1F26')
if not target or target.get('seg') != 0x50F6 or target.get('off') != 0x1F26:
    raise RuntimeError('registered target address changed')
exact_base_aliases = [{'name': name, **row} for name, row in symbols['data'].items()
                      if row.get('seg') == 0x50F6 and row.get('off') == 0x1F26]

callback_specs = [
    ('src/S00/m35A6.asm', '_o00_35A6_0406'),
    ('src/S01/m32B5.asm', '_o01_32B5_024F'),
    ('src/S03/m3258.asm', '_o03_3258_175F'),
]
callback_rows = []
for rel_path, proc in callback_specs:
    text = (ROOT / rel_path).read_text(encoding='latin1')
    match = re.search(r'(?ims)^' + re.escape(proc) + r'\s+proc\s+far\s*$([\s\S]*?)^' +
                      re.escape(proc) + r'\s+endp\s*$', text)
    if not match:
        raise RuntimeError(f'callback procedure missing: {proc}')
    body = match.group(1)
    callback_rows.append({
        **pin(ROOT / rel_path), 'procedure': proc,
        'movsw_count': len(re.findall(r'(?im)^\s*movsw\s*$', body)),
        'add_di_bx_count': len(re.findall(r'(?im)^\s*add\s+di,\s*bx\s*$', body)),
    })
callback_by_proc = {row['procedure']: row for row in callback_rows}
expected_callback_counts = {
    '_o00_35A6_0406': (64, 64),
    '_o01_32B5_024F': (16, 16),
    '_o03_3258_175F': (36, 12),
}
for proc, counts in expected_callback_counts.items():
    row = callback_by_proc[proc]
    if (row['movsw_count'], row['add_di_bx_count']) != counts:
        raise RuntimeError(f'callback instruction census changed: {proc}')

name_rx = re.compile(r'(?<![A-Za-z0-9_])_?fd_50F6_1F26(?![A-Za-z0-9_])', re.I)
# Numeric probes are reported with source context only; they are not automatically treated as aliases.
number_rx = re.compile(r'(?<![A-Za-z0-9_])(?:0x1f26[uUlL]*|1f26h|7974[uUlL]*)(?![A-Za-z0-9_])', re.I)
tag_rx = re.compile(r'image939', re.I)
mode_rx = re.compile(r'\b(?:g_19BE|g_19C0|fd_50F6_1102|g_5A97|fd_50F6_37E6)\b|o(?:00_35A6_0406|01_32B5_024F|03_3258_175F)', re.I)
source_hits = []
mode_hits = []
numeric_hits = []
allocation_tag_hits = []
for row in canonical + strict:
    path = ROOT / row['path']
    text = path.read_text(encoding='latin1')
    hits = line_hits(text, name_rx)
    if hits:
        source_hits.append({'path': row['path'], 'sha256': row['sha256'], 'roles': [row['role']], 'hits': hits})
    mh = line_hits(text, mode_rx)
    if mh:
        mode_hits.append({'path': row['path'], 'sha256': row['sha256'], 'hits': mh})
    nh = line_hits(text, number_rx)
    if nh:
        numeric_hits.append({'path': row['path'], 'sha256': row['sha256'], 'hits': nh})
    th = line_hits(text, tag_rx)
    if th:
        allocation_tag_hits.append({'path': row['path'], 'sha256': row['sha256'], 'hits': th})

receipt = {
  'schema': 'simant-fd-50f6-1f26-owner-audit-v1',
  'verdict': 'UNRESOLVED',
  'verdict_reason': 'The source census proves a 4-byte bitmap header and mode-dependent pixel writes, but contains no defining source object or complete buffer-capacity contract. Mode 1/6 selector handling and selected-resource bounds are open.',
  'inputs': [manifest_pin, index_pin, symbols_pin],
  'related_context_only': [{**conditional_resource_review,
                            'role': 'existing conditional resource research; not an owner/capacity proof'}],
  'canonical_source_count': len(canonical),
  'strict_effective_module_count': len(strict),
  'unique_source_path_count': len(set(all_paths)),
  'strict_receipt_pins': strict_receipts,
  'source_pins': sorted(canonical + strict, key=lambda x: (x['role'], x['path'], x.get('function',''))),
  'symbol': {'name': 'fd_50F6_1F26', 'seg': '50F6', 'off': '1F26', 'registered_exact_base_aliases': exact_base_aliases,
             'registry_grounding': target.get('grounding')},
  'source_identifier_hits': source_hits,
  'numeric_offset_token_hits_for_review': numeric_hits,
  'allocation_tag_token_hits_for_review': allocation_tag_hits,
  'pixel_mode_source_hits': mode_hits,
  'callback_instruction_census': callback_rows,
  'observed_source_facts': {
    'header': 'Pnt is two signed 16-bit int fields x,y (4 bytes) in src/root/m0250.c; PreDrawSpider writes x=7*g_19BE and y=7*g_19C0.',
    'payload_entry': 'DrawSpider passes (char far *)&fd_50F6_1F26 + 4 to the 7x7 tile raster loop and passes the base/header to f_1B4E_003B and f_16B5_0033.',
    'consumer': 'src/root/m1B4E.asm f_1B4E_003B loads words at offsets 0 and 2 as width/height and passes base+4 to g_914C; f_16B5_0033 likewise reads the two-word header.',
    'selector': 'LoadTiles assigns fd_50F6_1102=1 for modes 0/4/8, =2 for mode 2 (also sets cell dimensions 12x12), =3 for modes 3/5/7; dimensions begin 16x16. There is no source assignment for modes 1 or 6.',
    'raster_callback_shapes': 'The exact callback bodies copy 64 rows x 2 bytes for S00, 16 rows x 2 bytes for S01, or 12 rows x 6 bytes for S03; row placement uses the DrawSpider skip formula. The 7x7 tile writes require 6272 payload bytes in the {16x16, selector=1} source case, 3528 in {12x12, selector=2}, and 1568 in {16x16, selector=3}. Including the 4-byte header, those conditional ranges end at 6276, 3532, and 1572 bytes. These are required written extents for those source paths, not the recovered declared capacity.',
    'resource_overlay': 'DrawSpider subsequently calls f_2662_1120 with this buffer as destination. Source dispatches on the selected bitmap type through fd_50F6_37EA/fd_50F6_3B58; full destination extent depends on image headers and selectors outside this bounded source-only census.',
    'allocation_tag': 'The exact token image939 is absent from all 156 audited source inputs; it is not used as an owner name.'
  },
  'missing_frontier': [
    'No canonical or strict-effective source defines/owns fd_50F6_1F26 as a complete object; all target mentions are views/usages from root:0250.',
    'LoadTiles does not assign fd_50F6_1102 for source-reachable graphics selectors 1 and 6; DrawSpider consumes it without a local default.',
    'The full f_2662_1120 overlay extent needs complete selected type-2 resource dimensions for every supported graphics package plus restored selector state; existing HCEGANT normal-state evidence is conditional and does not establish a universal capacity.',
    'The actual historical communal declaration/source object shape, fixed capacity, and exact storage-owner endpoint are absent from the 156 source inputs; registry neighbors and zero gaps are not used as object bounds.'
  ],
  'source_fix_if_definition_is_recovered': 'Give the historical defining TU one named complete object type with the two-word header followed by its pixel storage, and make the consumer extern/callback view use a compatible header prefix. Do not promote a guessed tail length. If maintaining a source-only owner, first close the mode and resource write frontier, then size one data-only provider to the demonstrated complete extent.'
}
(OUT / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'verdict': receipt['verdict'], 'canonical': len(canonical), 'strict': len(strict),
                  'unique': len(set(all_paths)), 'target_hit_files': len(source_hits),
                  'target_hits': sum(len(x['hits']) for x in source_hits),
                  'numeric_hit_files': len(numeric_hits), 'strict_receipts': len(strict_receipts)}, indent=2))
