"""The active program inventory and reviewed whole-TU publication.

Published checkpoints live in Git. Builds consume only src/program.json and
its canonical sources; evidence is never a source replacement mechanism.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROGRAM = ROOT / 'src/program.json'


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def load() -> dict:
    program = json.loads(PROGRAM.read_text())
    if program['schema'] != 'simant-canonical-program-v1':
        raise ValueError('unsupported canonical program schema')
    paths = [m['source'] for m in program['modules']]
    keys = [m['key'] for m in program['modules']]
    if len(paths) != len(set(paths)) or len(keys) != len(set(keys)):
        raise ValueError('duplicate canonical translation unit')
    for m in program['modules']:
        path = (ROOT / m['source']).resolve()
        if not path.is_relative_to(ROOT / 'src'):
            raise ValueError('canonical source outside src: ' + m['source'])
    return program


def check_owned_code_references(contract: dict, obj) -> int:
    """Require linker-owned offsets, even when an old literal matches history.

    This checks ordinary OMF references to reconstructed code-data objects
    and callback entries anchored by existing publics. It creates no storage and changes neither bytes nor fixups.
    """
    count = 0
    for owner in contract['owners']:
        segment, start, size = owner['segment'], owner['start'], owner['size']
        if not (isinstance(start, int) and isinstance(size, int) and
                0 <= start < start + size <= obj.segment_lengths.get(segment, 0)):
            raise ValueError('owned code-data extent is outside its segment')
        if 'anchor_public' in owner:
            anchors = [p for p in obj.publics if p['name'] == owner['anchor_public']]
            if (len(anchors) != 1 or anchors[0]['segment'] != segment or
                    anchors[0]['offset'] + owner['anchor_delta'] != start):
                raise ValueError('owned callback entry differs from its public anchor')
        for site in owner['references']:
            publics = [p for p in obj.publics if p['name'] == site['public']]
            if len(publics) != 1 or publics[0]['segment'] != segment:
                raise ValueError('owned code reference has no unique same-segment public')
            offset = publics[0]['offset'] + site['operand_offset']
            target_offset = site['owner_offset']
            if not 0 <= target_offset < size:
                raise ValueError('owned code reference exceeds its object')
            fixups = [f for f in obj.linker_fixups
                      if f['segment'] == segment and f['offset'] == offset]
            expected = {'width': 2, 'loc': 'offset16', 'self_relative': False,
                        'target_kind': 'segment', 'target': segment,
                        'frame_kind': 'segment', 'frame': segment,
                        'displacement': start + target_offset,
                        'encoded_addend': '0000'}
            if len(fixups) != 1 or any(fixups[0].get(k) != v for k, v in expected.items()):
                raise ValueError(f'owned code reference at {segment}:{offset:04X} '
                                 'is missing or has the wrong frame/target')
            if 'segment_operand_offset' in site:
                segment_offset = publics[0]['offset'] + site['segment_operand_offset']
                segment_fixups = [f for f in obj.linker_fixups
                                  if f['segment'] == segment and f['offset'] == segment_offset]
                segment_expected = dict(expected, loc='base16', displacement=0)
                if (len(segment_fixups) != 1 or
                        any(segment_fixups[0].get(k) != v for k, v in segment_expected.items())):
                    raise ValueError(f'owned code reference at {segment}:{offset:04X} '
                                     'has the wrong paired segment word')
            count += 1
    return count


def check_data_frame_references(contract: dict, obj) -> int:
    """Require reviewed group-relative offsets to a module's private data.

    Historical placement can hide a segment-relative frame error. These sites
    are anchored to existing procedure publics and checked before any link.
    """
    segment, group = contract['target_segment'], contract['frame_group']
    if not any(g['name'] == group and segment in g['segments'] for g in obj.groups):
        raise ValueError('data frame target is outside its group')
    sites = contract['sites']
    if not sites:
        raise ValueError('data frame contract has no references')
    seen = set()
    for site in sites:
        publics = [p for p in obj.publics if p['name'] == site['public']]
        if len(publics) != 1:
            raise ValueError('data frame reference has no unique procedure public')
        public = publics[0]
        offset = public['offset'] + site['operand_offset']
        target = site['displacement']
        if not (isinstance(site['operand_offset'], int) and site['operand_offset'] >= 0
                and isinstance(target, int) and
                0 <= target < obj.segment_lengths.get(segment, 0)):
            raise ValueError('data frame reference is outside its source or target')
        location = (public['segment'], offset)
        if location in seen:
            raise ValueError('duplicate data frame reference')
        seen.add(location)
        fixups = [f for f in obj.linker_fixups
                  if (f['segment'], f['offset']) == location]
        expected = {'width': 2, 'loc': 'offset16', 'self_relative': False,
                    'target_kind': 'segment', 'target': segment,
                    'frame_kind': 'group', 'frame': group,
                    'displacement': target, 'encoded_addend': '0000'}
        if len(fixups) != 1 or any(fixups[0].get(k) != v for k, v in expected.items()):
            raise ValueError(f'data frame reference at {location[0]}:{offset:04X} '
                             'is missing or has the wrong frame/target')
    return len(seen)


def tokens(text: str) -> str:
    import csrc
    return ' '.join(t.text for t in csrc.tokenize(text)
                    if t.kind not in ('ws', 'nl', 'cmt'))


def definition_sha(text: str, name: str) -> str:
    import csrc
    function = csrc.Source(text).function(name)
    return sha(tokens(text[function.head_s:function.body.e]).encode('utf8'))


def observed(result: dict) -> dict:
    """Full historical comparison, including failures; no byte masks."""
    return {k: v for k, v in result.items()
            if k not in ('log', 'object_sha256', 'contribution_sha256')}


def audit_context(key: str, result: dict, admission: dict) -> list[str]:
    """Accept a reviewed compiler-context change separately from exact claims.

    A receipt pins the entire rebuilt object and complete comparison result.
    An unexpected new difference fails. This does not make a failing historical
    comparison exact or change its result.
    """
    failures = []
    receipt = json.loads((ROOT / admission['receipt']).read_text())
    entry = receipt['historical_comparisons'][key]
    if result.get('contribution_sha256') != entry['contribution_sha256']:
        failures.append('rebuilt live contributions differ from reviewed canonical admission')
    if observed(result) != entry['comparison']:
        failures.append('historical comparison differs from reviewed canonical admission')
    return failures


import copy
import json


def semantic_context_sha(text: str) -> str:
    """Declarations, initializers, signatures and all preprocessor directives.

    Exact helper-body improvements may preserve a caller contract. Changes to
    its types, macros, globals or signatures require a new whole-TU review.
    """
    import csrc
    spans = [(f.body.s, f.body.e) for f in csrc.Source(text).functions()]
    significant = (t for t in csrc.tokenize(text) if t.kind not in ('ws', 'nl', 'cmt'))
    return sha(' '.join(t.text for t in significant if t.kind == 'pp' or
                       not any(start <= t.s < end for start, end in spans)).encode('utf8'))


def check_semantic_review(row: dict, text: str) -> dict:
    """Check a current canonical definition against its complete static review."""
    path = (ROOT / row['receipt']).resolve()
    if not path.is_relative_to((ROOT / 'evidence').resolve()):
        raise ValueError('semantic receipt outside evidence: ' + row['function'])
    review = json.loads(path.read_text())
    pin = definition_sha(text, row['function'])
    if (review.get('schema') != 'simant-canonical-semantic-review-v1' or
            review.get('function') != row['function'] or review.get('module') != row['module'] or
            review.get('status') != 'BEHAVIOR_EXACT_CONFIRMED' or
            row.get('status') != 'BEHAVIOR_EXACT_CONFIRMED' or
            row.get('definition_sha256') != pin or review.get('definition_sha256') != pin):
        raise ValueError('canonical semantic definition/review differs: ' + row['function'])
    audit = review.get('audit', {})
    root = review.get('root_review', {})
    if (audit.get('status') != 'BEHAVIOR_EXACT_CONFIRMED' or
            audit.get('unexplained_semantic_differences') != [] or
            root.get('reviewer') != 'root' or
            any(root.get(axis) is not True for axis in
                ('complete_cfg', 'complete_data_widths', 'complete_calls_effects', 'codegen_only_residue'))):
        raise ValueError('incomplete canonical semantic review: ' + row['function'])
    return review


def exact_inventory(program: dict, key: str, module: dict, raw: bytes,
                    previous: dict | None, *, source: str) -> dict:
    """Prepare metadata for an already exact promotion, without writing files.

    A normal exact promotion cannot replace a registered behavioral definition
    or its declaration context. Those changes use a reviewed canonical plan.
    """
    after = copy.deepcopy(program)
    items = {m['key']: m for m in after['modules']}
    item = items.get(key)
    if previous is not None:
        if item is None:
            raise ValueError('historical module absent from canonical inventory: ' + key)
        for field in ('source', 'source_sha256', 'lang', 'profile', 'flags'):
            if item[field] != previous[field]:
                raise ValueError('canonical/historical context differs: ' + key + ': ' + field)
        old_raw = (ROOT / item['source']).read_bytes()
        if sha(old_raw) != item['source_sha256']:
            raise ValueError('current canonical source pin differs: ' + key)
        if source != item['source']:
            raise ValueError('source path/language replacement requires a canonical plan: ' + key)
        old_text, text = old_raw.decode('latin1'), raw.decode('latin1')
        registered = [s for s in program.get('semantics', []) if s['module'] == key]
        for semantic in registered:
            check_semantic_review(semantic, old_text)
            check_semantic_review(semantic, text)
        compiler_changed = any(module[field] != item[field] for field in ('lang', 'profile', 'flags'))
        if registered and (compiler_changed or semantic_context_sha(old_text) != semantic_context_sha(text)):
            raise ValueError('registered semantic declaration context changed; use a reviewed canonical plan: ' + key)
        if item.get('storage_contract'):
            raise ValueError('provider storage changes require a canonical plan: ' + key)
    elif item is not None or (ROOT / source).exists():
        raise ValueError('new historical module conflicts with an existing canonical source: ' + key)
    else:
        item = {'key': key}
        after['modules'].append(item)
    item.update({'source': source, 'source_sha256': sha(raw), 'unit': module['unit'],
                 'lang': module['lang'], 'profile': module['profile'], 'flags': list(module['flags'])})
    after['modules'].sort(key=lambda m: m['key'])
    return after


def check_semantic_publication(program: dict, payloads: dict, previous: dict | None,
                               prior_program_sha256: str | None) -> None:
    """Allow reviewed revisions, bound to the unchanged current predecessor.

    A fresh receipt's supersedes record pins prior program, whole TU, accepted
    definition and receipt. A new definition and changed surrounding context
    both retain complete static/root review requirements.
    """
    rows = program.get('semantics', [])
    names = [r['function'] for r in rows]
    if len(names) != len(set(names)):
        raise ValueError('duplicate canonical semantic registration')
    modules = {m['key']: m for m in program['modules']}
    old_rows = {s['function']: s for s in (previous or {}).get('semantics', [])}
    old_modules = {m['key']: m for m in (previous or {}).get('modules', [])}
    if old_rows.keys() - set(names):
        raise ValueError('canonical plan drops accepted semantic registrations')
    for row in rows:
        key = row['module']
        if key not in modules or modules[key]['lang'] != 'c':
            raise ValueError('semantic registration requires canonical C TU: ' + row['function'])
        text = payloads[key].decode('latin1')
        review = check_semantic_review(row, text)
        prior = old_rows.get(row['function'])
        if prior is None:
            continue
        if key != prior['module']:
            raise ValueError('semantic owner relocation requires a separate ownership review: ' + row['function'])
        old_item = old_modules[key]
        old_raw = (ROOT / old_item['source']).read_bytes()
        if sha(old_raw) != old_item['source_sha256']:
            raise ValueError('current canonical source pin differs: ' + key)
        old_text = old_raw.decode('latin1')
        old_review = check_semantic_review(prior, old_text)
        compiler_changed = any(modules[key][field] != old_item[field] for field in ('lang', 'profile', 'flags'))
        revised = (row != prior or compiler_changed or definition_sha(text, row['function']) != prior['definition_sha256'] or
                   semantic_context_sha(text) != semantic_context_sha(old_text))
        if not revised:
            continue
        expected = {'program_sha256': prior_program_sha256,
                    'source_sha256': old_item['source_sha256'],
                    'definition_sha256': prior['definition_sha256'],
                    'receipt_sha256': sha((ROOT / prior['receipt']).read_bytes())}
        if (review == old_review or review.get('supersedes') != expected or
                review.get('root_review', {}).get('source_correction_reviewed') is not True):
            raise ValueError('semantic revision lacks a fresh review pinned to prior canonical context: ' + row['function'])


def publish(plan_path: Path, verify_only: bool) -> int:
    """Publish a reviewed set of whole TUs through promote.py's sole writer.

    The migration plan is an input to this operation, never a build dependency.
    Current exact proofs are checked without masking. Explicit context changes
    carry the whole comparison and retain their historical authority in Git.
    """
    import modules
    import compiler
    import symbols
    from lockfile import CanonicalLock, atomic_write_text
    from omf import OmfReader
    import sys
    sys.path.insert(0, str(ROOT))
    from dos.build import verify_storage

    plan = json.loads(plan_path.read_text())
    man = modules.load_manifest()
    prior_program_sha256 = sha(PROGRAM.read_bytes()) if PROGRAM.exists() else None
    previous = load() if prior_program_sha256 else None
    if previous and plan.get('prior_program_sha256') != prior_program_sha256:
        raise ValueError('canonical publication plan has a stale or missing program pin')
    if previous:
        old_modules = {m['key']: m for m in previous['modules']}
        if old_modules.keys() - {m['key'] for m in plan['program']['modules']}:
            raise ValueError('canonical publication cannot silently drop live modules')
        for item in plan['files']:
            old = old_modules.get(item['key'])
            if old and (item['source'] != old['source'] or item.get('prior_sha256') != old['source_sha256']):
                raise ValueError('publication does not pin current canonical source: ' + item['key'])
    if sha(modules.MANIFEST.read_bytes()) != plan['prior_manifest_sha256']:
        raise ValueError('canonical publication plan has a stale manifest')
    payloads = {}
    for item in plan['files']:
        raw = (ROOT / item['candidate']).read_bytes()
        if sha(raw) != item['sha256']:
            raise ValueError('changed reviewed candidate: ' + item['candidate'])
        dest = ROOT / item['source']
        if not dest.resolve().is_relative_to(ROOT / 'src'):
            raise ValueError('publication destination outside src')
        if item.get('prior_sha256') and sha(dest.read_bytes()) != item['prior_sha256']:
            raise ValueError('canonical source changed during review: ' + item['source'])
        payloads[item['key']] = raw.replace(b'\r\n', b'\n')
        item['sha256'] = sha(payloads[item['key']])
        next(m for m in plan['program']['modules'] if m['key'] == item['key'])['source_sha256'] = item['sha256']

    # A storage admission need not republish every unchanged game TU. Still
    # verify the entire program, loading omitted TUs only from the pinned
    # current authority; omission cannot smuggle a source/context change.
    changed_keys = set(payloads)
    for item in plan['program']['modules']:
        if item['key'] in payloads:
            continue
        old = old_modules.get(item['key']) if previous else None
        if old != item:
            raise ValueError('omitted module differs from current canonical inventory: ' + item['key'])
        raw = (ROOT / item['source']).read_bytes()
        if sha(raw) != item['source_sha256']:
            raise ValueError('omitted canonical source pin differs: ' + item['key'])
        payloads[item['key']] = raw

    check_semantic_publication(plan['program'], payloads, previous, prior_program_sha256)
    review_paths = {row['receipt'] for data in (previous or {}, plan['program'])
                    for row in data.get('semantics', [])}
    review_pins = {path: sha((ROOT / path).read_bytes()) for path in review_paths}

    # Grounded data views, not new allocation. The registry writer publishes
    # these only after all source/object checks pass.
    syms = symbols.load()
    for item in plan['anchors']:
        old = syms['data'].get(item['name'])
        row = {'seg': item['seg'], 'off': item['off'], 'grounding': item['grounding']}
        if old and (old['seg'], old['off']) != (row['seg'], row['off']):
            raise ValueError('conflicting reviewed anchor: ' + item['name'])
        syms['data'][item['name']] = row
    original_symbols_load = symbols.load
    symbols.load = lambda: syms
    # Binder lookup caches are process-local; build them from reviewed anchors.
    import match
    original_match_symbols = match.symbols
    anchors = {('_' + name): {'kind': kind, **row}
               for kind in ('code', 'data') for name, row in syms[kind].items()}
    anchors.update({name: {'kind': 'code', **row} for name, row in syms.get('runtime', {}).items()
                    if name not in anchors})
    match.symbols = lambda: anchors
    for key, pubs in plan.get('code_data_publics', {}).items():
        man['modules'][key]['code_data_publics'] = pubs
    receipt = plan['receipt']
    receipt['historical_comparisons'] = {}
    allowed = set(plan['reviewed_context_changes'])
    failures = []
    try:
        from concurrent.futures import ThreadPoolExecutor
        def compile_item(item):
            text = payloads[item['key']].decode('latin1')
            if item['key'] in man['modules']:
                module = {**man['modules'][item['key']],
                          'lang': item['lang'], 'profile': item['profile'], 'flags': item['flags']}
                return modules.verify_module(text, module, module['claims'], man=man,
                    code_references=item.get('owned_code_references'),
                    data_frame_references=item.get('data_frame_references'))
            return compiler.compile_c(text, item['profile'], item['flags'])
        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(compile_item, plan['program']['modules']))
        for item, result in zip(plan['program']['modules'], results):
            key = item['key']
            text = payloads[key].decode('latin1')
            lint = modules.source_lint(text, item['lang'])
            if lint['refused']:
                failures.append(f'{key}: {lint["refused"]}')
                continue
            if key in man['modules']:
                module = man['modules'][key]
                print(key, 'EXACT' if result['exact'] else 'REVIEWED CONTEXT' if key in allowed else 'FAIL', flush=True)
                if not result['exact'] and key not in allowed:
                    failures.append(f'{key}: unexpected historical comparison failure {observed(result)}')
                if key in allowed:
                    expected = plan['reviewed_context_changes'][key]
                    bad = sorted(n for n, c in result['claims'].items() if not c['exact'])
                    dbad = sorted(n for n, c in result.get('data', {}).items() if not c['exact'])
                    if bad != sorted(expected['claims']) or dbad != sorted(expected['data']) or result.get('module_reasons'):
                        failures.append(f'{key}: unexpected reviewed differences: {bad}, {dbad}, {result.get("module_reasons")}')
                if key in changed_keys:
                    receipt['historical_comparisons'][key] = {
                        'object_sha256': result.get('object_sha256'),
                        'contribution_sha256': result.get('contribution_sha256'),
                        'comparison': observed(result)}
            else:
                compiled = result
                if not compiled.ok:
                    failures.append(f'{key}: storage compile failed {compiled.log}')
                    continue
                obj = OmfReader(communals=True).read(compiled.obj)
                try:
                    verify_storage(obj, item['storage_contract'])
                except ValueError as exc:
                    failures.append(f'{key}: canonical storage contract differs: {exc}')
                print(key, 'STORAGE', flush=True)
    finally:
        symbols.load = original_symbols_load
        match.symbols = original_match_symbols
    if failures:
        raise ValueError('\n'.join(failures))
    if verify_only:
        print('VERIFY-ONLY OK: canonical publication, historical comparisons preserved')
        return 0
    with CanonicalLock():
        if previous and sha(PROGRAM.read_bytes()) != prior_program_sha256:
            raise ValueError('canonical inventory changed during publication')
        for path, pin in review_pins.items():
            if sha((ROOT / path).read_bytes()) != pin:
                raise ValueError('semantic review changed during publication: ' + path)
        if sha(modules.MANIFEST.read_bytes()) != plan['prior_manifest_sha256']:
            raise ValueError('manifest changed during publication')
        for item in plan['program']['modules']:
            if item['key'] not in changed_keys and sha((ROOT / item['source']).read_bytes()) != item['source_sha256']:
                raise ValueError('omitted canonical source changed during publication: ' + item['key'])
        for file in plan['files']:
            dest = ROOT / file['source']
            if file.get('prior_sha256') and sha(dest.read_bytes()) != file['prior_sha256']:
                raise ValueError('source changed during publication')
        results_by_key = dict(zip((item['key'] for item in plan['program']['modules']), results))
        inventory_by_key = {item['key']: item for item in plan['program']['modules']}
        for file in plan['files']:
            dest = ROOT / file['source']
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(payloads[file['key']])
            if file['key'] in man['modules']:
                module = man['modules'][file['key']]
                item = inventory_by_key[file['key']]
                result = results_by_key[file['key']]
                module.update({field: item[field] for field in ('source', 'source_sha256', 'lang', 'profile', 'flags')})
                module['object_sha256'] = result.get('object_sha256')
                module['scaffold'] = result['scaffold']
                for claim in module['claims']:
                    claim.pop('current_proof', None)
                if file['key'] not in allowed:
                    module.pop('canonical_admission', None)
                if file['key'] in allowed:
                    module['canonical_admission'] = {'receipt': plan['receipt_path'],
                        'historical_checkpoint': receipt['prior_commit'],
                        'current_byte_exact': False,
                        'reason': plan['reviewed_context_changes'][file['key']]['reason']}
                    for claim in module['claims']:
                        if claim['name'] in plan['reviewed_context_changes'][file['key']]['claims']:
                            claim['current_proof'] = 'HISTORICAL_EXACT_SOURCE_REBUILT'
        symbols.save(syms)
        modules.write_manifest(man)
        atomic_write_text(PROGRAM, json.dumps(plan['program'], indent=2) + '\n', newline='\n')
        path = ROOT / plan['receipt_path']
        path.parent.mkdir(parents=True, exist_ok=True)
        atomic_write_text(path, json.dumps(receipt, indent=2) + '\n')
        journal = ROOT / 'evidence/promotions.jsonl'
        with journal.open('a') as stream:
            stream.write(json.dumps({'canonical_publication': plan['receipt_path'],
                'sources': len(changed_keys), 'prior_manifest_sha256': plan['prior_manifest_sha256']}) + '\n')
    print(f'PROMOTED {len(changed_keys)} canonical translation units; verified {len(payloads)}')
    return 0
