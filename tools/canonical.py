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

    plan = json.loads(plan_path.read_text())
    man = modules.load_manifest()
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
                module = man['modules'][item['key']]
                return modules.verify_module(text, module, module['claims'], man=man)
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
                got = sorted((c['name'], c['kind'], c['length']) for c in obj.communals)
                want = sorted((c['name'], c['kind'], c['length']) for c in item['storage_contract']['communals'])
                if got != want:
                    failures.append(f'{key}: canonical storage shape differs')
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
        if sha(modules.MANIFEST.read_bytes()) != plan['prior_manifest_sha256']:
            raise ValueError('manifest changed during publication')
        for file in plan['files']:
            dest = ROOT / file['source']
            if file.get('prior_sha256') and sha(dest.read_bytes()) != file['prior_sha256']:
                raise ValueError('source changed during publication')
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(payloads[file['key']])
            if file['key'] in man['modules']:
                module = man['modules'][file['key']]
                module['source_sha256'] = file['sha256']
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
                'sources': len(payloads), 'prior_manifest_sha256': plan['prior_manifest_sha256']}) + '\n')
    print(f'PROMOTED {len(payloads)} canonical translation units')
    return 0
