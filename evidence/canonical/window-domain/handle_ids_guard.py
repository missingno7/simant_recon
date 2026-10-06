"""Function-scoped incoming-call census with mutation-tested negative controls."""
from __future__ import annotations
import hashlib, json, re, sys
from collections import defaultdict
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p/'src/program.json').is_file())
HERE = Path(__file__).resolve().parent
SPEC = json.loads((HERE / 'handle-id-review.json').read_text(encoding='utf-8'))
sys.path.insert(0, str(ROOT / 'tools'))
import csrc

PROGRAM = json.loads((ROOT / 'src/program.json').read_text(encoding='utf-8'))
REGISTRY = json.loads((ROOT / 'layout/symbols.json').read_text(encoding='utf-8'))['code']
SOURCES = {p.relative_to(ROOT).as_posix(): p.read_text(encoding='utf-8') for p in (ROOT / 'src').rglob('*.c')}
SOURCE_BYTES = {p.relative_to(ROOT).as_posix(): p.read_bytes() for p in (ROOT / 'src').rglob('*.c')}
ASSEMBLY = {p.relative_to(ROOT).as_posix(): p.read_text(encoding='utf-8', errors='replace') for p in (ROOT / 'src').rglob('*.asm')}
NAMES = set(SPEC['relevant_functions'])

def de_link(name):
    # Linker aliases lose exactly one leading decoration; C identifiers do not.
    return name[1:] if name.startswith(('_', '@')) else name

def compact(text, node):
    return ''.join(t.text for t in csrc.tokenize(text[node.s:node.e]) if t.kind not in ('ws', 'nl', 'cmt'))

def line_at(text, pos):
    return text.count('\n', 0, pos) + 1

def insert_in_function(source, function, statement):
    parsed = csrc.Source(source).functions()
    fn = next(x for x in parsed if x.name == function)
    pos = fn.body.e - 1
    return source[:pos] + '\n    ' + statement + '\n' + source[pos:]

def collect(overrides=None, program_aliases=None):
    """Return fresh facts without writing files; overrides map source paths to text."""
    overrides = overrides or {}
    texts = dict(SOURCES); texts.update({k: v for k, v in overrides.items() if k.endswith('.c')})
    asm_texts = dict(ASSEMBLY); asm_texts.update({k: v for k, v in overrides.items() if k.endswith('.asm')})
    alias_map = {}
    for row in PROGRAM.get('aliases', []) + list(program_aliases or []):
        if row.get('kind') == 'code':
            alias_map[de_link(row.get('alias', ''))] = de_link(row.get('target', ''))
    for name, row in REGISTRY.items():
        if isinstance(row, dict) and row.get('alias_of'):
            alias_map[name] = row['alias_of']

    def canon(name):
        cur, seen = name, set()
        while cur not in seen:
            seen.add(cur)
            if cur in alias_map:
                cur = alias_map[cur]
            elif cur not in REGISTRY and cur.startswith(('_', '@')) and de_link(cur) in alias_map:
                cur = de_link(cur)
            else:
                break
        return cur

    calls, defs, call_offsets, def_offsets = [], defaultdict(set), defaultdict(set), defaultdict(set)
    bare_refs, errors = [], []
    for rel, text in sorted(texts.items()):
        for token in csrc.tokenize(text):
            if token.kind == 'pp' and any(canon(name) in NAMES
                    for name in re.findall(r'[A-Za-z_][A-Za-z0-9_]*', token.text)):
                errors.append({'source': rel, 'error': 'unreviewed preprocessor function reference'})
        try:
            funcs = csrc.Source(text).functions()
        except Exception as exc:
            errors.append({'source': rel, 'error': str(exc)}); continue
        for fn in funcs:
            target_fn = canon(fn.name); defs[target_fn].add(rel)
            match = re.search(r'(?<![A-Za-z0-9_$])' + re.escape(fn.name) + r'\s*\(', text[fn.head_s:fn.params_e])
            if match: def_offsets[rel].add(fn.head_s + match.start())
            for node, _parent in csrc.walk_parents(fn.body):
                if not isinstance(node, csrc.Call) or not isinstance(node.f, csrc.Id): continue
                call_offsets[rel].add(node.f.s)
                callee = canon(node.f.name)
                if callee in NAMES:
                    args = [compact(text, arg) for arg in node.args]
                    calls.append({'source': rel, 'line': line_at(text, node.s), 'caller': fn.name,
                                  'written_callee': node.f.name, 'canonical_callee': callee,
                                  'argument_count': len(args), 'arguments': args})
        toks = [t for t in csrc.tokenize(text) if t.kind not in ('ws', 'nl', 'cmt')]
        depth, depth_at = 0, {}
        for t in toks:
            depth_at[t.s] = depth
            if t.text == '{': depth += 1
            elif t.text == '}': depth = max(0, depth - 1)
        for i, tok in enumerate(toks):
            if tok.kind != 'id' or canon(tok.text) not in NAMES: continue
            if tok.s in def_offsets[rel] or tok.s in call_offsets[rel]: continue
            if i + 1 < len(toks) and toks[i + 1].text == '(' and depth_at.get(tok.s, 0) == 0: continue
            bare_refs.append({'source': rel, 'line': line_at(text, tok.s), 'symbol': tok.text,
                              'canonical': canon(tok.text)})

    calls.sort(key=lambda x: (x['source'], x['line'], x['caller'], x['canonical_callee'],
                              x['written_callee'], x['arguments']))
    payload = json.dumps(calls, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')
    sources_by_name = {name: sorted(files) for name, files in sorted(defs.items()) if name in NAMES}
    pin_files = sorted({f for paths in sources_by_name.values() for f in paths})
    pin_hashes = {p: hashlib.sha256(overrides[p].encode('utf-8') if p in overrides
                                  else SOURCE_BYTES[p]).hexdigest()
                  for p in pin_files if p in texts}

    spellings = set(NAMES)
    for alias, target in alias_map.items():
        if canon(target) in NAMES: spellings.add(alias)
    spellings = {s for n in spellings for s in (n, '_' + n, '@' + n, '@_' + n)}
    asm_refs = []
    rx = re.compile(r'(?<![A-Za-z0-9_$])(?:' + '|'.join(re.escape(s) for s in sorted(spellings, key=len, reverse=True)) + r')(?![A-Za-z0-9_$])', re.I)
    for rel, text in sorted(asm_texts.items()):
        for line_no, line in enumerate(text.splitlines(), 1):
            for match in rx.finditer(line):
                asm_refs.append({'source': rel, 'line': line_no, 'symbol': match.group(0)})

    dormant = [{'function': row['function'], 'parameter_index': row['parameter_index'],
                'incoming_calls': sum(c['canonical_callee'] == canon(row['function']) for c in calls)}
               for row in SPEC['dormant_formals']]
    obligations = []
    for row in SPEC['abi_obligations']:
        matches = [c for c in calls if c['source'] == row['source'] and c['caller'] == row['caller']
                   and c['canonical_callee'] == canon(row['callee']) and c['argument_count'] == row['actual_arity']]
        obligations.append({'callee': row['callee'], 'call_matches': len(matches),
                            'target_definition_present': row['target_definition_source'] in defs.get(canon(row['callee']), set())})
    return {'calls': calls, 'call_count': len(calls), 'call_sha256': hashlib.sha256(payload).hexdigest(),
            'source_map': sources_by_name, 'pin_files': pin_files, 'pin_hashes': pin_hashes,
            'bare_refs': bare_refs, 'asm_refs': asm_refs, 'dormant': dormant,
            'abi_obligations': obligations, 'parse_errors': errors}

def check():
    base = collect()
    expected_callback_refs = sorted((r['source'], r['line'], r['symbol'])
                                    for h in SPEC['callback_refs'] for r in h['c_references'])
    actual_callback_refs = sorted((r['source'], r['line'], r['symbol']) for r in base['bare_refs']
                                  if r['canonical'] in {h['name'] for h in SPEC['callback_refs']})
    base_ok = (base['call_count'] == SPEC['incoming_direct_c_call_count'] and
               base['call_sha256'] == SPEC['incoming_direct_c_call_sha256'] and
               base['source_map'] == SPEC['function_sources'] and base['pin_files'] == SPEC['pinned_source_files'] and
               base['pin_hashes'] == SPEC['pinned_source_sha256'] and not base['parse_errors'])

    main_src = 'src/root/m15F8.c'
    bare = collect({'src/new-callback.c': 'void (*escape)(void) = f_2505_033C;'})
    asm_path = sorted(ASSEMBLY)[0]
    uppercase = collect({asm_path: ASSEMBLY[asm_path] + '\n call WIN_LOCKWIN\n'})
    new_call = collect({main_src: insert_in_function(SOURCES[main_src], 'main', 'win_LockWin(0x100);')})
    pinned = SPEC['pinned_source_files'][0]
    body = collect({pinned: SOURCES[pinned] + '\n/* source-body mutation probe */\n'})
    alias_row = {'alias': '_fixtureLockAlias', 'target': '_win_LockWin', 'kind': 'code'}
    alias = collect({main_src: insert_in_function(SOURCES[main_src], 'main', 'fixtureLockAlias(0x100);')}, [alias_row])
    negatives = {
        'new_dormant_bare_address': any(r['canonical'] == 'f_2505_033C' for r in bare['bare_refs']),
        'uppercase_asm_reference': len(uppercase['asm_refs']) > len(base['asm_refs']),
        'new_direct_call': new_call['call_sha256'] != base['call_sha256'],
        'pinned_source_body_mutation': body['pin_hashes'].get(pinned) != base['pin_hashes'].get(pinned),
        'new_alias_to_existing_target': (alias['call_sha256'] != base['call_sha256'] and
                                         any(c['written_callee'] == 'fixtureLockAlias' for c in alias['calls'])),
    }
    callback_count_ok = (len(base['bare_refs']) == 7 and len(actual_callback_refs) == 7
                         and actual_callback_refs == expected_callback_refs)
    dormant_ok = len(base['dormant']) == 18 and all(x['incoming_calls'] == 0 for x in base['dormant'])
    abi_ok = len(base['abi_obligations']) == 2 and all(x['call_matches'] == 1 and x['target_definition_present'] for x in base['abi_obligations'])
    result = {'pass': base_ok and callback_count_ok and not base['asm_refs'] and dormant_ok and abi_ok and all(negatives.values()),
              'base_matches_spec': base_ok, 'function_count': len(NAMES), 'call_edge_count': base['call_count'],
              'call_edge_sha256': base['call_sha256'], 'pinned_source_file_count': len(base['pin_files']),
              'pinned_source_hash_count': len(base['pin_hashes']), 'bare_reference_count': len(base['bare_refs']),
              'callback_reference_count': len(actual_callback_refs), 'asm_reference_count': len(base['asm_refs']),
              'dormant_formal_count': len(base['dormant']), 'abi_obligation_count': len(base['abi_obligations']),
              'negative_controls': negatives, 'parse_errors': base['parse_errors']}
    return result

if __name__ == '__main__':
    result = check()
    print(json.dumps(result, indent=2))
    if not result['pass']: raise SystemExit(1)
