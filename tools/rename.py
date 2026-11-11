"""Re-prove a batch of canonical identifier renames before publishing it.

    python tools/rename.py OLD=NEW ... --kind descriptive --why "DOS evidence"
    python tools/rename.py --batch renames.json --verify-only

Provenance: starts from SimAnt 0eab5e5:tools/rename.py; token/literal separation
informed by duke1_recon/tools/rename.py, ordered before/after object checks and
rollback by gp_recon/tools/link/rename.py. No sibling compiler rules are used.

Uses the current promotion verifier, storage gate and canonical lock. A rename
is a lexical substitution, never a semantic revision or a new exact claim.
Comments change for code-quoted names, call notation, identifier-shaped names
(address names, underscores or mixed capitals), or explicit identifier references. Prose and
literals stay byte-for-byte. Each run owns build/scratch/rename-*/ (no shared
compile cache); compiler fan-out is capped at four. Publication is one locked,
optimistically pinned transaction with rollback on a failed file replacement.
"""
from __future__ import annotations

import argparse
import copy
from contextlib import contextmanager
from concurrent.futures import ThreadPoolExecutor
import datetime as dt
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import threading
import time

# A dry run must not even leave import bytecode outside its scratch directory.
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import canonical
import compiler
import csrc
import match
import modules
import symbols
from lockfile import CanonicalLock
from omf import OmfReader

ROOT = Path(__file__).resolve().parents[1]
SOURCE_SUFFIXES = {'.c', '.h', '.asm', '.inc'}
IDENT = re.compile(r'[A-Za-z_][A-Za-z0-9_]{0,30}\Z')
WORD = re.compile(r'(?<![A-Za-z0-9_$?@])[A-Za-z_$?@][A-Za-z0-9_$?@]*')
ASM_TOKEN = re.compile(
    r'(?P<cmt>;[^\n]*)|(?P<str>"(?:""|[^"\n])*"|\'(?:\'\'|[^\'\n])*\')'
    r'|(?P<num>[0-9][A-Za-z0-9]*)|(?P<id>[A-Za-z_$?@][A-Za-z0-9_$?@]*)|(?P<other>.)', re.S)
ADDRESS = re.compile(r'(?:f_[0-9A-F]{4}_[0-9A-F]{4}|o\d+_[0-9A-F]{4}_[0-9A-F]{4}'
                     r'|(?:fd|cd|d|b)_[A-Za-z0-9_]+)\Z')


def spellings(mapping: dict, registry: dict) -> dict:
    """C identifiers and actual OMF/ASM decorations, without guessing aliases."""
    out = dict(mapping)
    for old, new in mapping.items():
        out['_' + old] = '_' + new
        out['@' + old] = '@' + new
        if registry.get('code', {}).get(old, {}).get('convention') == 'pascal':
            out[old.upper()] = new.upper()
    return out


def words(text: str, mapping: dict) -> str:
    return WORD.sub(lambda m: mapping.get(m[0], m[0]), text)


def comment(text: str, mapping: dict) -> str:
    def replace(m):
        old = m[0]
        if old not in mapping:
            return old
        left, right = text[:m.start()], text[m.end():]
        quoted = any(left.endswith(q) and right.startswith(q) for q in ('`', "'", '"'))
        called = re.match(r'\s*\(', right)
        explicit = re.search(r'\b(?:function|symbol|variable|identifier|global|procedure)\s+$', left, re.I)
        identifier_shaped = '_' in old or re.search(r'[a-z][A-Z]|[A-Z].*[A-Z]', old)
        if quoted or called or explicit or identifier_shaped or ADDRESS.fullmatch(old.lstrip('_@')):
            return mapping[old]
        return old
    return WORD.sub(replace, text)


def asm_tokens(text: str):
    # MASM COMMENT delimiter blocks are documentation, not identifiers.
    blocked = False
    delimiter = ''
    offset = 0
    for line in text.splitlines(keepends=True):
        start = re.match(r'\s*comment\s+(\S)', line, re.I) if not blocked else None
        if blocked or start:
            yield 'cmt', line, offset, offset + len(line)
            if start:
                delimiter = start[1]
                blocked = delimiter not in line[start.end():]
            elif delimiter in line:
                blocked = False
        else:
            for t in ASM_TOKEN.finditer(line):
                yield t.lastgroup, t[0], offset + t.start(), offset + t.end()
        offset += len(line)


def lexical_tokens(text: str, lang: str):
    if lang == 'asm':
        yield from asm_tokens(text)
        return
    for t in csrc.tokenize(text):
        if t.kind == 'asm':
            for kind, value, start, end in asm_tokens(t.text):
                yield kind, value, t.s + start, t.s + end
        elif t.kind == 'pp':
            # The preprocessor line is opaque to csrc. Re-lex its contents,
            # protecting header names (including angle-bracket paths).
            include = re.match(r'\s*#\s*include\s*([<"][^>"\n]+[>"])', t.text)
            for p in csrc.TOKEN_RE.finditer(t.text):
                kind = p.lastgroup
                if include and include.start(1) <= p.start() < include.end(1):
                    kind = 'str'
                yield kind, p[0], t.s + p.start(), t.s + p.end()
        else:
            yield t.kind, t.text, t.s, t.e


def identifiers(text: str, lang: str) -> set:
    return {value for kind, value, _, _ in lexical_tokens(text, lang) if kind == 'id'}


def replace_tokens(text: str, mapping: dict, lang: str = 'c') -> str:
    return replace_spans(text, mapping, lexical_tokens(text, lang))


def replace_spans(text, mapping, tokens):
    edits = []
    for kind, value, start, end in tokens:
        new = mapping.get(value, value) if kind == 'id' else comment(value, mapping) if kind == 'cmt' else value
        if new != value:
            edits.append((start, end, new))
    parts, previous = [], 0
    for start, end, new in edits:
        parts.extend((text[previous:start], new))
        previous = end
    parts.append(text[previous:])
    return ''.join(parts)


def renamed(value, mapping, *, keys=False):
    """Symbol references and diagnostics; schema keys and evidence paths stay put.

    Only symbol-indexed maps have renamed keys. A game global named 'name' or
    'status' must never rename a JSON schema field with the same spelling.
    """
    if isinstance(value, str):
        return words(value, mapping)
    if isinstance(value, list):
        return [renamed(v, mapping) for v in value]
    if isinstance(value, tuple):
        return tuple(renamed(v, mapping) for v in value)
    if isinstance(value, dict):
        fixed = {'source', 'receipt', 'facts', 'path', 'library', 'member',
                 'schema', 'kind', 'status', 'lang', 'unit', 'module', 'key',
                 'profile', 'flags', 'segment', 'class', 'combine', 'alignment',
                 'frame_kind', 'target_kind', 'loc', 'convention', 'name_kind',
                 'current_proof', 'provenance'}
        return {(words(k, mapping) if keys else k):
                copy.deepcopy(v) if k in fixed else
                renamed(v, mapping, keys=k in ('claims', 'code_data_publics'))
                for k, v in value.items()}
    return value


@contextmanager
def binding(registry):
    # Both lookup paths matter: match.public_in also consults symbols.load.
    anchors = {'_' + n: {'kind': kind, **row}
               for kind in ('code', 'data') for n, row in registry.get(kind, {}).items()}
    for n, row in registry.get('runtime', {}).items():
        anchors.setdefault(n, {'kind': 'code', **row})
    original_match, original_load = match.symbols, symbols.load
    try:
        match.symbols = lambda: anchors
        symbols.load = lambda: registry
        yield
    finally:
        match.symbols, symbols.load = original_match, original_load


def registry_after(registry, rows, used):
    result = copy.deepcopy(registry)
    mapping = {r['old']: r['new'] for r in rows}
    for row in rows:
        old, new = row['old'], row['new']
        section = 'code' if old in result['code'] else 'data'
        record = result[section].pop(old)
        record.setdefault('history', []).append({'was': old, 'why': row['why']})
        record['name_kind'] = row['kind']
        result[section][new] = record
        if old in used or '_' + old in used or '@' + old in used:
            result[section][old] = {k: v for k, v in record.items() if k != 'history'} | {'alias_of': new}
    for section in ('code', 'data'):
        for record in result[section].values():
            if record.get('alias_of') in mapping:
                record['alias_of'] = mapping[record['alias_of']]
        result[section] = dict(sorted(result[section].items()))
    return result


def json_bytes(value, indent=2):
    return (json.dumps(value, indent=indent) + '\n').encode('utf8')


class RenameError(ValueError):
    pass


class Session:
    def __init__(self, scratch: Path, jobs=4):
        self.scratch = scratch
        self.jobs = min(4, max(1, jobs))
        self.pins = {}
        self.man = json.loads(self.read('layout/manifest.json'))
        program_raw = self.read('src/program.json')
        self.program = canonical.load()
        if self.program != json.loads(program_raw):
            raise RenameError('canonical inventory changed during rename')
        self.registry = json.loads(self.read('layout/symbols.json'))
        self.read('evidence/promotions.jsonl', optional=True)
        self.items = {m['key']: m for m in self.program['modules']}
        self.by_source = {m['source']: m for m in self.program['modules']}
        self.sources = {}
        self.lexed = {}
        for path in sorted((ROOT / 'src').rglob('*')):
            if path.suffix.lower() in SOURCE_SUFFIXES:
                rel = path.relative_to(ROOT).as_posix()
                raw = self.read(rel)
                lang = 'asm' if path.suffix.lower() in ('.asm', '.inc') else 'c'
                tokens = [(kind, value, start, end)
                          for kind, value, start, end in lexical_tokens(raw.decode('latin1'), lang)
                          if kind in ('id', 'cmt')]
                self.lexed[rel] = tokens
                self.sources[rel] = (raw, lang, {value for kind, value, _, _ in tokens if kind == 'id'})
        for item in self.items.values():
            raw = self.sources[item['source']][0]
            if canonical.sha(raw) != item['source_sha256']:
                raise RenameError('current canonical source pin differs: ' + item['key'])
            historical = self.man['modules'].get(item['key'])
            if historical:
                for field in ('source', 'source_sha256', 'lang', 'profile', 'flags'):
                    if historical[field] != item[field]:
                        raise RenameError('canonical/historical context differs: ' + item['key'] + ': ' + field)
        self.baseline = {}
        self.cache = {}

    def read(self, rel, optional=False):
        path = ROOT / rel
        if optional and not path.exists():
            raw = None
        else:
            raw = path.read_bytes()
        if rel in self.pins and self.pins[rel] != raw:
            raise RenameError('canonical input changed during rename: ' + rel)
        self.pins[rel] = raw
        return raw

    def receipt(self, rel):
        path = (ROOT / rel).resolve()
        if not path.is_relative_to((ROOT / 'evidence').resolve()):
            raise RenameError('receipt outside evidence: ' + rel)
        return json.loads(self.read(rel))

    def validate_rows(self, rows):
        if not isinstance(rows, list) or not rows:
            raise RenameError('a nonempty rename batch is required')
        old_names, new_names = set(), set()
        for row in rows:
            if not isinstance(row, dict) or set(row) != {'old', 'new', 'kind', 'why'}:
                raise RenameError('each rename requires exactly old, new, kind, why')
            old, new = row['old'], row['new']
            if not isinstance(old, str) or not IDENT.fullmatch(old) or not isinstance(new, str) or not IDENT.fullmatch(new):
                raise RenameError(f'bad identifier (maximum 31 characters): {old!r}={new!r}')
            if row['kind'] not in ('recovered', 'descriptive') or not isinstance(row['why'], str) or not row['why'].strip():
                raise RenameError(f'{old}: kind and nonempty evidence required')
            if old == new or old in old_names or new in new_names:
                raise RenameError(f'duplicate or identity rename: {old}={new}')
            old_names.add(old)
            new_names.add(new)
            record = self.registry['code'].get(old) or self.registry['data'].get(old)
            if record is None or record.get('alias_of'):
                raise RenameError(f'{old}: must be a registered primary game symbol')
            if new in csrc.KEYWORDS | csrc.QUALIFIERS | csrc.ASM_WORDS:
                raise RenameError('reserved identifier: ' + new)
            decorated = spellings({old: new}, self.registry)
            targets = set(decorated.values())
            occupied = set(self.registry.get('runtime', {}))
            for kind in ('code', 'data'):
                occupied.update(spellings({n: n for n in self.registry[kind]}, self.registry))
            # MASM and Pascal case folding can collide even when C differs.
            folded = record.get('convention') == 'pascal'
            if targets & occupied or (folded and {n.upper() for n in targets} & {n.upper() for n in occupied}):
                raise RenameError('registered name or runtime collision: ' + new)
        mapping = spellings({r['old']: r['new'] for r in rows}, self.registry)
        targets = set(mapping.values())
        if len(targets) != len(mapping):
            raise RenameError('batch has colliding decorated spellings')
        present = set().union(*(s[2] for s in self.sources.values()))
        for row in rows:
            variants = set(spellings({row['old']: row['new']}, self.registry))
            if not variants & present:
                raise RenameError(row['old'] + ': no canonical identifier occurrence')
        for rel, (_, lang, ids) in self.sources.items():
            if not ids & set(mapping):
                continue
            clash = ids & targets
            if lang == 'asm':
                clash |= {n for n in ids if n.upper() in {t.upper() for t in targets}}
            if clash:
                raise RenameError(f'{rel}: identifier collision: {sorted(clash)}')

    def prepare(self, rows):
        mapping = spellings({r['old']: r['new'] for r in rows}, self.registry)
        changed = {}
        for rel, (raw, lang, ids) in self.sources.items():
            # Comments may name an identifier even in a module without a use.
            new = replace_spans(raw.decode('latin1'), mapping, self.lexed[rel]).encode('latin1')
            if new != raw:
                if rel not in self.by_source:
                    # Current compiler's include policy admits include/, not src/
                    # headers. Refuse rather than silently publish unproved text.
                    raise RenameError('changed source has no recorded compiler context: ' + rel)
                changed[self.by_source[rel]['key']] = new
        program = copy.deepcopy(self.program)
        for item in program['modules']:
            for field in ('storage_contract', 'owned_code_references', 'data_frame_references', 'supported_domain'):
                if field in item:
                    item[field] = renamed(item[field], mapping)
            if item['key'] in changed:
                item['source_sha256'] = canonical.sha(changed[item['key']])
        program['aliases'] = renamed(program.get('aliases', []), mapping)
        if 'dos' in program:
            program['dos'] = renamed(program['dos'], mapping)
        man = copy.deepcopy(self.man)
        for key, module in man['modules'].items():
            for field in ('claims', 'scaffold', 'layout_inferred', 'steered', 'code_data_publics'):
                if field in module:
                    module[field] = renamed(module[field], mapping, keys=field == 'code_data_publics')
        used = {mapping.get(name, name) for _, _, ids in self.sources.values() for name in ids}
        registry = registry_after(self.registry, rows, used)
        return mapping, changed, program, man, registry

    def compile_one(self, key, raw, program, man):
        item = next(m for m in program['modules'] if m['key'] == key)
        text = raw.decode('latin1')
        collect = {}
        if key in man['modules']:
            module = man['modules'][key]
            result = modules.verify_module(text, module, module['claims'], collect=collect, man=man,
                code_references=item.get('owned_code_references'),
                data_frame_references=item.get('data_frame_references'))
            reasons = modules.link_after_reasons(man, key, module,
                {n: d.get('align') for n, d in result.get('data', {}).items()})
            reasons += modules.placement_overlap_reasons(man, key)
            if reasons:
                result.setdefault('module_reasons', []).extend(reasons)
                result['exact'] = False
        else:
            if not item.get('storage_contract'):
                raise RenameError(key + ': nonhistorical unit lacks a storage contract')
            lint = modules.source_lint(text, item['lang'])
            compiled = (compiler.assemble if item['lang'] == 'asm' else compiler.compile_c)(text, item['profile'], item['flags'])
            result = {'compile_ok': compiled.ok, 'exact': False, 'claims': {}, 'log': compiled.log if not compiled.ok else ''}
            if compiled.ok:
                collect['object'] = compiled.obj
                sys.path.insert(0, str(ROOT))
                from dos.build import verify_storage
                try:
                    verify_storage(OmfReader(communals=True).read(compiled.obj), item['storage_contract'])
                    result.update(exact=True, object_sha256=canonical.sha(compiled.obj))
                except ValueError as error:
                    result['module_reasons'] = ['storage: ' + str(error)]
            if lint['refused']:
                result.setdefault('module_reasons', []).extend(lint['refused'])
                result['exact'] = False
        return result, collect

    def compile_many(self, changed, program, man, registry):
        with binding(registry), ThreadPoolExecutor(max_workers=self.jobs) as pool:
            futures = {key: pool.submit(self.compile_one, key, raw, program, man) for key, raw in changed.items()}
            return {key: future.result() for key, future in futures.items()}

    def establish_baseline(self, keys):
        pending = {k: self.sources[self.items[k]['source']][0] for k in keys if k not in self.baseline}
        results = self.compile_many(pending, self.program, self.man, self.registry)
        for key, pair in results.items():
            result, _ = pair
            module = self.man['modules'].get(key, {})
            if module.get('canonical_admission'):
                admission = module['canonical_admission']
                self.receipt(admission['receipt'])
                errors = canonical.audit_context(key, result, admission)
                if errors:
                    raise RenameError(key + ': prior canonical admission differs: ' + '; '.join(errors))
            elif not result['exact']:
                raise RenameError(key + ': baseline does not verify: ' + json.dumps(canonical.observed(result)))
            for row in self.program.get('semantics', []):
                if row['module'] == key:
                    self.receipt(row['receipt'])
                    canonical.check_semantic_review(row, pending[key].decode('latin1'))
            self.baseline[key] = pair

    def evaluate(self, rows):
        cache_key = tuple(r['old'] for r in rows)
        if cache_key in self.cache:
            return self.cache[cache_key]
        mapping, changed, program, man, registry = self.prepare(rows)
        print(f'Checking {len(rows)} rename(s) across {len(changed)} module(s)', flush=True)
        self.establish_baseline(changed)
        results = self.compile_many(changed, program, man, registry)
        failures = {}
        for key, (result, collect) in results.items():
            module = man['modules'].get(key, {})
            reasons = []
            if module.get('canonical_admission'):
                prior_result, prior_collect = self.baseline[key]
                if canonical.observed(result) != renamed(canonical.observed(prior_result), mapping):
                    reasons.append('full historical comparison differs from reviewed context')
                # Contribution identity includes names. Change only those symbolic
                # fields in a copy of the predecessor; bytes/indices/order remain.
                if 'object' not in collect or 'object' not in prior_collect:
                    reasons.append('reviewed context lacks complete compiled contributions')
                else:
                    prior_obj = OmfReader(communals=True).read(prior_collect['object'])
                    after_obj = OmfReader(communals=True).read(collect['object'])
                    for field in ('publics', 'local_publics', 'linker_fixups', 'communals', 'externals'):
                        setattr(prior_obj, field, renamed(getattr(prior_obj, field), mapping))
                    if modules.contribution_sha256(prior_obj) != modules.contribution_sha256(after_obj):
                        reasons.append('live bytes/layout/ordered fixups differ from reviewed context')
            elif not result['exact']:
                reasons.append('not every claim, private datum and complete-unit extent is exact')
            if reasons:
                failures[key] = self.diagnostic(key, result, collect, mapping, reasons)
        outcome = {'mapping': mapping, 'changed': changed, 'program': program, 'man': man,
                   'registry': registry, 'results': results, 'failures': failures}
        self.cache[cache_key] = outcome
        return outcome

    def diagnostic(self, key, result, collect, mapping, reasons):
        details = list(reasons)
        details.extend(result.get('module_reasons', []))
        for name, claim in result.get('claims', {}).items():
            if not claim['exact']:
                details.append(name + ': ' + '; '.join(claim.get('reasons', [])))
        for name, data in result.get('data', {}).items():
            if not data['exact']:
                details.append('data ' + name + ': ' + '; '.join(data.get('reasons', [])))
        if result.get('extent') and not result['extent']['exact']:
            details.append('extent: ' + '; '.join(result['extent'].get('reasons', [])))
        if not result.get('compile_ok'):
            details.append(result.get('log', 'compile failed'))
        prior = self.baseline[key][1]
        old_code = {mapping.get(c['name'], c['name']): c for c in prior.get('code', [])}
        for current in collect.get('code', []):
            old = old_code.get(current['name'])
            if old:
                diff = first_difference(old['bytes'], current['bytes'])
                if diff:
                    details.append(current['name'] + ': first differing bytes ' + diff)
        for current in collect.get('data', []):
            old = next((d for d in prior.get('data', []) if d['segment'] == current['segment']), None)
            if old:
                diff = first_difference(old['bytes'], current['bytes'])
                if diff:
                    details.append('data ' + current['segment'] + ': first differing bytes ' + diff)
        # Missing publics or changed extents can prevent a bound function dump.
        before_segment, after_segment = prior.get('code_segment'), collect.get('code_segment')
        if before_segment and after_segment:
            diff = first_difference(before_segment['bytes'], after_segment['bytes'])
            if diff:
                details.append('unbound code segment: first differing bytes ' + diff)
        return details

    def stage_metadata(self, rows, outcome):
        mapping = outcome['mapping']
        program, man = outcome['program'], outcome['man']
        changes = {self.items[k]['source']: raw for k, raw in outcome['changed'].items()}
        receipts = {}
        def review(rel):
            if rel not in receipts:
                receipts[rel] = self.receipt(rel)
            return receipts[rel]
        for key, raw in outcome['changed'].items():
            if key not in man['modules']:
                continue
            result = outcome['results'][key][0]
            module = man['modules'][key]
            module.update(source_sha256=canonical.sha(raw), object_sha256=result['object_sha256'])
            module['scaffold'] = result.get('scaffold', [])
            for claim in module['claims']:
                proof = result.get('claims', {}).get(claim['name'], {})
                if proof.get('exact'):
                    claim['reloc_order'] = proof.get('reloc_order', 'EXACT')
            if module.get('canonical_admission'):
                receipt = review(module['canonical_admission']['receipt'])
                receipt['historical_comparisons'][key] = {
                    'object_sha256': result['object_sha256'],
                    'contribution_sha256': result['contribution_sha256'],
                    'comparison': canonical.observed(result)}
        for row in program.get('semantics', []):
            key = row['module']
            if key not in outcome['changed']:
                continue
            old = row['function']
            row['function'] = mapping.get(old, old)
            text = outcome['changed'][key].decode('latin1')
            pin = canonical.definition_sha(text, row['function'])
            if old != row['function'] or pin != row['definition_sha256']:
                receipt = review(row['receipt'])
                row['definition_sha256'] = pin
                receipt.update(function=row['function'], definition_sha256=pin)
        for rel, receipt in receipts.items():
            receipt.setdefault('renamed', []).append({'renames': rows,
                'note': 'Lexical identifier rename; semantic review unchanged.',
                'prior_receipt_sha256': canonical.sha(self.pins[rel])})
            changes[rel] = json_bytes(receipt)
        changes['layout/manifest.json'] = json_bytes(man, 1)
        changes['src/program.json'] = json_bytes(program)
        changes['layout/symbols.json'] = json_bytes(outcome['registry'], 1)
        record = {'time': dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'),
                  'module': 'RENAME', 'renames': rows, 'modules_reproven': sorted(outcome['changed']),
                  'prior_program_sha256': canonical.sha(self.pins['src/program.json']),
                  'program_sha256': canonical.sha(changes['src/program.json']),
                  'objects': {k: r[0].get('object_sha256') for k, r in outcome['results'].items()}}
        journal = self.pins['evidence/promotions.jsonl'] or b''
        changes['evidence/promotions.jsonl'] = journal + (b'\n' if journal and not journal.endswith(b'\n') else b'') + json_bytes(record, None)
        return changes

    def publish(self, changes):
        # No destination is touched until every proof and every optimistic pin
        # has passed. Stage bytes on the same volume for os.replace.
        staged, backups = {}, {}
        stage = self.scratch / 'publication'
        stage.mkdir()
        for i, (rel, raw) in enumerate(changes.items()):
            staged[rel] = stage / f'{i}.new'
            staged[rel].write_bytes(raw)
            old = self.pins[rel]
            if old is not None:
                backups[rel] = stage / f'{i}.old'
                backups[rel].write_bytes(old)
        with CanonicalLock():
            for rel, expected in self.pins.items():
                path = ROOT / rel
                actual = path.read_bytes() if path.exists() else None
                if actual != expected:
                    raise RenameError('canonical input changed during rename: ' + rel)
            current_sources = {p.relative_to(ROOT).as_posix() for p in (ROOT / 'src').rglob('*')
                               if p.suffix.lower() in SOURCE_SUFFIXES}
            if current_sources != set(self.sources):
                raise RenameError('canonical source inventory changed during rename')
            written = []
            try:
                for rel, path in staged.items():
                    (ROOT / rel).parent.mkdir(parents=True, exist_ok=True)
                    os.replace(path, ROOT / rel)
                    written.append(rel)
            except BaseException:
                for rel in reversed(written):
                    if rel in backups:
                        os.replace(backups[rel], ROOT / rel)
                    else:
                        (ROOT / rel).unlink(missing_ok=True)
                raise


def first_difference(before, after):
    at = next((i for i, (a, b) in enumerate(zip(before, after)) if a != b), None)
    if at is None:
        if len(before) == len(after):
            return None
        at = min(len(before), len(after))
    return (f'+0x{at:X}: before={before[at:at+12].hex() or "<end>"} '
            f'after={after[at:at+12].hex() or "<end>"} (length {len(before)} -> {len(after)})')


def minimal_failure(rows, fails):
    """Delta debugging: bisect subsets and complements, including interactions.

    The returned set is 1-minimal: removing any one member makes it pass.
    No monotonicity of compiler name sensitivity is assumed.
    """
    current, granularity = list(rows), 2
    while len(current) >= 2:
        chunks = [current[i * len(current) // granularity:(i + 1) * len(current) // granularity]
                  for i in range(granularity)]
        candidates = chunks + [[r for r in current if r not in chunk] for chunk in chunks]
        smaller = next((subset for subset in candidates if 0 < len(subset) < len(current) and fails(subset)), None)
        if smaller is not None:
            current = smaller
            granularity = min(len(current), max(2, granularity - 1))
        elif granularity == len(current):
            break
        else:
            granularity = min(len(current), granularity * 2)
    return current


def run(rows, *, verify_only=False, keep_going=False, jobs=4):
    started = time.perf_counter()
    scratch_root = ROOT / 'build/scratch'
    scratch_root.mkdir(parents=True, exist_ok=True)
    scratch = Path(tempfile.mkdtemp(prefix='rename-', dir=scratch_root))
    print('Scratch:', scratch, flush=True)
    previous_work = compiler.WORK
    previous_tree = compiler.pinned_tree
    tree_lock = threading.Lock()
    trees = {}
    def isolated_tree(profile):
        # DOSBox profiles otherwise stage their pinned tools in build/deps/.
        # Keep that side effect in this run too; DOS still sees the same D:\BIN.
        tag = canonical.sha(json_bytes(sorted(profile['files'].items())))[:16]
        with tree_lock:
            if tag not in trees:
                dest = scratch / 'dos-tools' / tag
                for rel, pin in profile['files'].items():
                    raw = (Path(profile['directory']) / rel).read_bytes()
                    if canonical.sha(raw) != pin:
                        raise compiler.CompileError('pinned DOSBox tool changed: ' + rel)
                    target = dest / rel
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(raw)
                trees[tag] = dest
            return trees[tag]
    try:
        compiler.WORK = scratch / 'cc'
        compiler.pinned_tree = isolated_tree
        session = Session(scratch, jobs)
        session.validate_rows(rows)
        remaining, refused = list(rows), []
        outcome = session.evaluate(remaining)
        while outcome['failures'] and remaining:
            culprit = minimal_failure(remaining, lambda subset: bool(session.evaluate(subset)['failures']))
            diagnosis = session.evaluate(culprit)['failures']
            excluded = culprit[-1:] if keep_going else culprit
            refused.append({'renames': excluded, 'failing_set': culprit, 'failures': diagnosis})
            print('REFUSED SET:', ', '.join(r['old'] + '=' + r['new'] for r in culprit), flush=True)
            for key, details in diagnosis.items():
                print(' ', key, '\n    ' + '\n    '.join(details), flush=True)
            if keep_going and len(culprit) > 1:
                print('  Excluding ' + excluded[0]['old'] + ' and checking the complete surviving batch', flush=True)
            remaining = [r for r in remaining if r not in excluded]
            outcome = session.evaluate(remaining) if remaining else None
            if outcome is None:
                break
        published = False
        if remaining and (not refused or keep_going):
            # Reuse only this run's already fresh proof for the final complete
            # surviving batch. Never publish independent singleton successes.
            changes = session.stage_metadata(remaining, outcome)
            for rel, raw in changes.items():
                proposal = scratch / 'proposed' / rel
                proposal.parent.mkdir(parents=True, exist_ok=True)
                proposal.write_bytes(raw)
            if not verify_only:
                session.publish(changes)
                published = True
            for key in outcome['changed']:
                label = 'REVIEWED CONTEXT PRESERVED' if session.man['modules'].get(key, {}).get('canonical_admission') else 'EXACT' if key in session.man['modules'] else 'STORAGE'
                print(' ', key + ':', label, flush=True)
        report = {'requested': len(rows), 'proven': remaining, 'refused': refused,
                  'verify_only': verify_only, 'published': published,
                  'modules_reproven': sorted(outcome['changed']) if outcome else [],
                  'comparisons': {k: canonical.observed(pair[0]) for k, pair in outcome['results'].items()} if outcome else {},
                  'objects': {k: pair[0].get('object_sha256') for k, pair in outcome['results'].items()} if outcome else {},
                  'seconds': round(time.perf_counter() - started, 3)}
        (scratch / 'result.json').write_bytes(json_bytes(report))
        if published:
            print(f'RENAMED {len(remaining)} identifiers. Next commands:\npython portable/refresh_pins.py\npython tools/validate.py')
        else:
            print(f'{"VERIFY-ONLY" if verify_only else "REFUSED"}: {len(remaining)} proven, '
                  f'{sum(len(x["renames"]) for x in refused)} refused; no publication')
        print(f'Elapsed: {report["seconds"]:.3f}s; report: {scratch / "result.json"}')
        return 1 if refused else 0
    finally:
        compiler.WORK = previous_work
        compiler.pinned_tree = previous_tree


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pairs', nargs='*')
    parser.add_argument('--kind', choices=('recovered', 'descriptive'))
    parser.add_argument('--why')
    parser.add_argument('--batch', type=Path)
    parser.add_argument('--verify-only', action='store_true')
    parser.add_argument('--keep-going', action='store_true')
    parser.add_argument('--jobs', type=int, choices=range(1, 5), default=4)
    args = parser.parse_args(argv)
    if args.batch:
        if args.pairs or args.kind or args.why:
            parser.error('--batch cannot be combined with pairs, --kind or --why')
        rows = json.loads(args.batch.read_text(encoding='utf-8-sig'))
    else:
        if not args.pairs or not args.kind or not args.why:
            parser.error('OLD=NEW requires --kind and --why')
        rows = []
        for pair in args.pairs:
            if pair.count('=') != 1:
                parser.error('expected OLD=NEW: ' + pair)
            old, new = pair.split('=')
            rows.append({'old': old, 'new': new, 'kind': args.kind, 'why': args.why})
    try:
        return run(rows, verify_only=args.verify_only, keep_going=args.keep_going, jobs=args.jobs)
    except (ValueError, OSError, compiler.CompileError) as error:
        print('REFUSED:', error, file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
