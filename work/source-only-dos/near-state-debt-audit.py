import hashlib, json, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOKENS = ('g_5A97', 'g_8CCB', 'g_5A9C', 'fd_55B3_5AA0', 'fd_55B3_5AA2')
NUMS = ('5A97', '5A9C', '5AA0', '5AA2', '5AA4', '8CCA', '8CCB')

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def lines_for(path, tokens):
    text = path.read_text(encoding='utf-8', errors='replace')
    out = []
    for no, line in enumerate(text.splitlines(), 1):
        if any(re.search(r'(?<![A-Za-z0-9_])' + re.escape(tok) + r'(?![A-Za-z0-9_])', line) for tok in tokens):
            out.append({'line': no, 'text': line.strip()})
    return out

def numeric_lines(path):
    if path.suffix.lower() not in ('.c', '.asm'):
        return []
    out = []
    text = path.read_text(encoding='utf-8', errors='replace')
    for no, line in enumerate(text.splitlines(), 1):
        # Only literal spellings in symbolic ASM; comments are reported separately as source text.
        vals = []
        for key in NUMS:
            pats = (r'(?<![A-Za-z0-9_])0x' + key + r'(?![A-Za-z0-9_])',
                    r'(?<![A-Za-z0-9_])' + key + r'[hH](?![A-Za-z0-9_])')
            if any(re.search(p, line, re.I) for p in pats):
                vals.append(key)
        if vals:
            out.append({'line': no, 'hex_literals': vals, 'text': line.strip()})
    return out

manifest = json.loads((ROOT/'layout/manifest.json').read_text(encoding='utf-8'))
mods = manifest['modules']
canonical = {}
for key, mod in mods.items():
    p = ROOT/mod['source']
    if not p.is_file():
        raise SystemExit(f'manifest source missing: {mod["source"]}')
    actual = sha(p)
    if actual != mod['source_sha256']:
        raise SystemExit(f'manifest source hash mismatch: {mod["source"]}')
    hits = lines_for(p, TOKENS)
    nums = numeric_lines(p)
    if hits or nums:
        canonical[mod['source']] = {'module': key, 'sha256': actual, 'named_hits': hits, 'numeric_literals': nums}

bmanifest_path = ROOT/'evidence/behavior/manifest.json'
strict_index_path = ROOT/'work/source-only-dos/static-completeness/index-v1.json'
strict_index = json.loads(strict_index_path.read_text(encoding='utf-8'))
if len(strict_index.get('entries', {})) != 29:
    raise SystemExit('expected exactly 29 strict-effective entries')
if sha(bmanifest_path) != strict_index['registry']['sha256']:
    raise SystemExit('strict static index points to a different behavior registry')
strict_sources = {}
strict_hit_sources = {}
for name, row in strict_index['entries'].items():
    receipt_path = ROOT/row['path']
    if sha(receipt_path) != row['sha256']:
        raise SystemExit(f'strict receipt hash mismatch: {name}: {row["path"]}')
    receipt = json.loads(receipt_path.read_text(encoding='utf-8'))
    if receipt.get('status') != 'BEHAVIOR_EXACT_CONFIRMED':
        raise SystemExit(f'strict receipt is not confirmed: {name}')
    source = receipt.get('source_override') or receipt['registered_source']
    source_path = ROOT/source['path']
    actual = sha(source_path)
    if actual != source['sha256']:
        raise SystemExit(f'strict effective source hash mismatch: {name}: {source["path"]}')
    source_row = {'source': source['path'], 'source_sha256': actual,
                  'receipt_path': row['path'], 'receipt_sha256': row['sha256']}
    strict_sources[name] = source_row
    hits = lines_for(source_path, TOKENS)
    nums = numeric_lines(source_path)
    if hits or nums:
        strict_hit_sources[name] = {**source_row, 'named_hits': hits, 'numeric_literals': nums}

queue = json.loads((ROOT/'work/source-only-dos/queue-lifetime-contract-v1.json').read_text(encoding='utf-8'))
clear = queue['startup_clear']['clear_interval']
clear_start = int(clear['start_inclusive'], 16)
clear_end = int(clear['end_exclusive'], 16)
symbols = json.loads((ROOT/'layout/symbols.json').read_text(encoding='utf-8'))['data']
symbol_offsets = {name: symbols[name]['off'] for name in TOKENS}
result = {
    'schema': 'dos-near-state-debt-source-scan-v1',
    'policy': 'canonical inputs are exact sources in layout/manifest.json; strict effective inputs are the 29 root-confirmed source paths from the static completeness index; no initial-data bytes are read or emitted',
    'no_original_bytes_emitted': True,
    'pins': {
        p: sha(ROOT/p) for p in [
            'layout/manifest.json', 'layout/symbols.json',
            'evidence/behavior/manifest.json',
            'work/source-only-dos/static-completeness/index-v1.json',
            'work/source-only-dos/queue-lifetime-contract-v1.json',
            'work/source-only-dos/near-state-debt-audit.py',
            'work/source-only-dos/near-state-debt-runtime-scan.py']
    },
    'symbol_offsets': symbol_offsets,
    'crt_startup_clear': {
        'start': clear['start_inclusive'], 'end_exclusive': clear['end_exclusive'],
        'fill': clear['fill'], 'main_after_clear': queue['startup_clear']['main_call']['occurs_after_clear'],
        'contains_g_8CCB_byte': clear_start <= symbol_offsets['g_8CCB'] < clear_end,
        'contains_g_5A97_byte': clear_start <= symbol_offsets['g_5A97'] < clear_end,
        'contains_g_5A9C_Rect': clear_start <= symbol_offsets['g_5A9C'] and symbol_offsets['g_5A9C'] + 8 <= clear_end,
    },
    'canonical_hit_modules': canonical,
    'strict_effective_29_sources': strict_sources,
    'strict_effective_hit_sources': strict_hit_sources,
    'numeric_literal_scan': {
        'literals': list(NUMS),
        'canonical': {p: v['numeric_literals'] for p, v in canonical.items() if v['numeric_literals']},
        'strict_effective': {n: v['numeric_literals'] for n, v in strict_hit_sources.items() if v['numeric_literals']},
        'scope': 'all canonical and strict effective .c/.asm text; includes 8CCA and 8CCB so byte-at-(8CCA+1) aliases and word accesses beginning at 8CCA are visible',
    },
}
out = ROOT/'build/workers/dos_near_state_debt_review/source-scan.json'
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n', encoding='utf-8')
print(json.dumps({'canonical_modules_with_hits': len(canonical), 'strict_effective_source_count': len(strict_sources), 'strict_effective_sources_with_hits': len(strict_hit_sources), 'canonical_named_hit_count': sum(len(v['named_hits']) for v in canonical.values()), 'canonical_numeric_literal_count': sum(len(v['numeric_literals']) for v in canonical.values()), 'strict_effective_numeric_literal_count': sum(len(v['numeric_literals']) for v in strict_hit_sources.values()), 'report': str(out)}, indent=2), flush=True)

# One pinned entry point refreshes both source and selected-runtime receipts.
subprocess.run([sys.executable, str(ROOT/'work/source-only-dos/near-state-debt-runtime-scan.py')],
               cwd=ROOT, check=True)
