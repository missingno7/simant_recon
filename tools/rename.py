"""Re-prove a batch of canonical identifier renames before publishing it.

    python tools/rename.py OLD=NEW ... --kind descriptive --why "DOS evidence"
    python tools/rename.py --batch renames.json --verify-only
    python tools/rename.py --headers headers.json --verify-only
    python tools/rename.py --move root:0250=src/render/pixels.c S12:384C=src/map.c --why "inferred"

Batches accept {old,new,kind,why}, {address:"SSSS:OOOO",new,kind,why}, or
{module,path,kind,why}. An address row may give old (an unregistered source
identifier), field_of (a registered containing object), and size (reviewed bytes).
Absent old, an existing address-spelled fd_SSSS_OOOO / g_OOOO is recognized;
otherwise registration adds only a name, never source storage or a guessed owner.
Moves preserve file bytes, module order and the compiler's UNIT basename. The
recorded manifest source is authoritative; source_name_kind labels the filename.
Header batches contain {module,header,summary,windows_group,kind,why} and optional
evidence and source_sha256 (an optional predecessor pin). Header is plain
comment text, already merged with any still-valid old
header evidence. Only the leading comment region is replaced; no line directives
or line-count compensation are inserted. Every runtime contribution and ordered
fixup must remain identical as well as retaining the historical proof result.
Historical modules receive summary/windows_group/file_header in their manifest
record. Source-owned storage receives the same metadata in source_annotations,
outside modules: annotation must not invent a historical module or its owner.
Both kinds also carry those facts in the canonical program inventory.

Live behavior tools and tests receive whole-identifier substitutions in quoted
names and fixtures too; behavior_suites/archive is excluded. Only affected unit
methods (or a module with affected shared fixtures) run, in a scratch copy with
host writes prohibited. Moves stage reconstruction path references and current
path/hash pairs, while reporting port references/pins without changing them.

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
import ast
import copy
from contextlib import contextmanager
from concurrent.futures import ThreadPoolExecutor
import datetime as dt
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
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
MASM_RESERVED = set(('ax bx cx dx al ah bl bh cl ch dl dh si di sp bp cs ds es ss '
    'eax ebx ecx edx esi edi esp ebp cr0 cr2 cr3 dr0 dr1 dr2 dr3 dr6 dr7 '
    'byte word dword qword tbyte ptr near far short offset seg dup this type length size '
    'proc endp segment ends group assume public extrn extern label equ org db dw dd dq dt '
    'include includelib end model code data const stack mov push pop call ret retf retn '
    'jmp je jne jz jnz ja jb jae jbe jg jl jge jle loop add sub mul imul div idiv '
    'inc dec neg not and or xor test cmp shl shr sar sal rol ror rcl rcr xchg lea '
    'lds les int iret in out cli sti cld std rep repe repne movs movsb movsw stos stosb '
    'stosw lods lodsb lodsw cmps cmpsb cmpsw scas scasb scasw nop wait hlt').split())


def c_mapping(rows):
    return {r['old']: r['new'] for r in rows if 'old' in r}


def comparison_after(result, mapping, objmap):
    out = copy.deepcopy(result)
    out['claims'] = {mapping.get(n, n): renamed(v, objmap) for n, v in result.get('claims', {}).items()}
    for field in ('scaffold', 'inplace_drafts'):
        if field in out:
            out[field] = [mapping.get(n, n) for n in out[field]]
    for field in ('communals', 'data', 'extent', 'module_reasons'):
        if field in out:
            out[field] = renamed(out[field], objmap)
    if 'opaque_data' in out:
        out['opaque_data'] = renamed(out['opaque_data'], mapping)
    return out


def header_comparison_before(result, before, after):
    """Translate source-lint locations by the proven leading-comment edit.

    These are source lines in opaque-data diagnostics, not OMF LINNUM entries.
    No compiled bytes, fixups, relocation verdicts or diagnostic content are
    removed or normalized. The runtime contribution check is independent.
    """
    out = copy.deepcopy(result)
    delta = after.count(b'\n') - before.count(b'\n')
    for datum in out.get('opaque_data', []):
        datum['line'] += delta
    return out


def operation_label(row):
    return (row.get('old', row.get('address', row.get('module', '?'))) + '=' +
            row.get('new', row.get('path', 'header' if 'header' in row else '?')))


def leading_comments(text, lang='c'):
    """Return (end, plain text) for adjacent leading comments and whitespace.

    Stop before the first non-comment token. In particular a function comment
    after an include/declaration is not a file header. Preserve evidence text
    when preparing a replacement; the writer never guesses which facts to drop.
    """
    pos, parts = 0, []
    while True:
        start = pos
        while pos < len(text) and text[pos].isspace():
            pos += 1
        if lang == 'c' and text.startswith('/*', pos):
            end = text.find('*/', pos + 2)
            if end < 0:
                raise RenameError('unterminated leading C comment')
            body = text[pos + 2:end]
            parts.append('\n'.join(re.sub(r'^\s*\* ?', '', line).rstrip()
                                   for line in body.splitlines()).strip())
            pos = end + 2
        elif text.startswith(';' if lang == 'asm' else '//', pos):
            end = text.find('\n', pos)
            end = len(text) if end < 0 else end
            parts.append(text[pos + (1 if lang == 'asm' else 2):end].strip())
            pos = end
        elif lang == 'asm' and (match_ := re.match(r'comment\s+(\S)', text[pos:], re.I)):
            body_start = pos + match_.end()
            end = text.find(match_[1], body_start)
            if end < 0:
                raise RenameError('unterminated leading MASM COMMENT')
            parts.append(text[body_start:end].strip())
            pos = end + 1
        else:
            return pos, '\n'.join(parts)
        if pos == start:
            raise RenameError('leading comment parser made no progress')


def replace_header(text, header, lang='c'):
    if (not isinstance(header, str) or not header.strip() or
            any(ord(c) > 126 or (ord(c) < 32 and c not in '\n\r\t') for c in header) or
            '/*' in header or '*/' in header):
        raise RenameError('header must be nonempty plain ASCII comment text without delimiters')
    newline = '\r\n' if '\r\n' in text else '\n'
    lines = header.replace('\r\n', '\n').splitlines()
    block = (['/*'] + [(' * ' + line).rstrip() for line in lines] + [' */']
             if lang == 'c' else [('; ' + line).rstrip() for line in lines])
    end, _ = leading_comments(text, lang)
    return newline.join(block) + newline + newline + text[end:]


def replace_paths(text, mapping):
    """Replace full path tokens, including Windows and JSON-escaped spellings."""
    variants = {}
    for old, new in mapping.items():
        for separator in ('/', '\\', '\\\\'):
            variants[old.replace('/', separator)] = new.replace('/', separator)
    if not variants:
        return text
    pattern = re.compile(r'(?<![A-Za-z0-9_.-])(?:' + '|'.join(re.escape(p) for p in sorted(variants, key=len, reverse=True)) + r')(?![A-Za-z0-9_.-])')
    return pattern.sub(lambda m: variants[m[0]], text)


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
                yield 'inline_id' if kind == 'id' else kind, value, t.s + start, t.s + end
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
    return {value for kind, value, _, _ in lexical_tokens(text, lang) if kind in ('id', 'inline_id')}


def replace_tokens(text: str, mapping: dict, lang: str = 'c') -> str:
    return replace_spans(text, mapping, lexical_tokens(text, lang))


def replace_spans(text, mapping, tokens):
    edits = []
    for kind, value, start, end in tokens:
        new = mapping.get(value, value) if kind in ('id', 'inline_id') else comment(value, mapping) if kind == 'cmt' else value
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
    mapping = c_mapping(rows)
    for row in rows:
        if 'module' in row:
            continue
        new = row['new']
        if 'address' in row:
            seg, off = (int(v, 16) for v in row['address'].split(':'))
            record = {'seg': seg, 'off': off, 'grounding': row['why'], 'name_kind': row['kind']}
            for field in ('field_of', 'size'):
                if field in row:
                    record[field] = row[field]
            if 'field_of' in record:
                record['field_of'] = mapping.get(record['field_of'], record['field_of'])
                parent = registry['data'][row['field_of']]
                record['alias_of'] = record['field_of']
                record['alias_offset'] = seg * 16 + off - parent['seg'] * 16 - parent['off']
            if 'old' in row:
                record['history'] = [{'was': row['old'], 'why': row['why']}]
            result['data'][new] = record
            continue
        old = row['old']
        section = 'code' if old in result['code'] else 'data'
        record = result[section].pop(old)
        record.setdefault('history', []).append({'was': old, 'why': row['why']})
        record['name_kind'] = row['kind']
        result[section][new] = record
        if (old in used['c'] or '_' + old in used['object'] or '@' + old in used['object']
                or (record.get('convention') == 'pascal' and old.upper() in used['object'])):
            result[section][old] = {k: v for k, v in record.items() if k != 'history'} | {'alias_of': new}
    for section in ('code', 'data'):
        for record in result[section].values():
            if record.get('alias_of') in mapping:
                record['alias_of'] = mapping[record['alias_of']]
            if record.get('field_of') in mapping:
                record['field_of'] = mapping[record['field_of']]
        result[section] = dict(sorted(result[section].items()))
    return result


def json_bytes(value, indent=2):
    return (json.dumps(value, indent=indent) + '\n').encode('utf8')


class RenameError(ValueError):
    pass


def repository_files(root):
    """Current files only; ignored output and originals are never rewrite inputs."""
    for directory, dirs, files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in {'.git', 'build', 'to_delete', 'assets', '__pycache__', '.venv', 'node_modules'})
        for name in sorted(files):
            path = Path(directory) / name
            if path.suffix.lower() in {'.py', '.json', '.jsonl', '.md', '.txt', '.toml', '.c', '.h', '.asm', '.inc', '.yaml', '.yml', '.csv'}:
                yield path.relative_to(root).as_posix()


def external_identifier_file(rel):
    return (rel in ('tools/canonical_behavior.py', 'tools/behavior.py') or rel.startswith('tests/') or
            (rel.startswith('tools/behavior_suites/') and 'archive' not in Path(rel).parts))


def port_reference_file(rel, raw):
    """Port outputs/pins can live in evidence as well as under portable/."""
    if (rel.startswith('portable/') or rel.startswith(('docs/port-', 'docs/native-')) or
            rel == 'evidence/canonical/native-word-intermediates/contracts.json'):
        # The last file is the WORDS port pin declared in portable/refresh_pins.py.
        return True
    if rel.startswith('evidence/') and rel.endswith('.json'):
        data = json.loads(raw)
        if isinstance(data, dict):
            schema = data.get('schema', '').lower()
            return schema.startswith(('native-', 'canonical-native-', 'simant-native-', 'portable-', 'simant-portable-'))
    return False


def selected_unit_tests(rel, text, needles):
    """Select methods directly affected, or their module when a shared fixture changes."""
    if not rel.startswith('tests/') or not rel.endswith('.py'):
        return []
    # Tests of the working DOS build and the port are outside the reconstruction gate
    # (tools/validate.py UPPER_LAYER_TESTS); the upper layers may be stale.
    import validate
    if rel.removeprefix('tests/').removesuffix('.py') in validate.UPPER_LAYER_TESTS:
        return []
    tree = ast.parse(text, filename=rel)
    lines = text.splitlines(keepends=True)
    methods = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) and child.name.startswith('test'):
                    methods.append((node.name + '.' + child.name, child.lineno, child.end_lineno))
    module = rel.removeprefix('tests/').removesuffix('.py').replace('/', '.')
    hit = lambda s: any(re.search(r'(?<![A-Za-z0-9_])' + re.escape(needle) + r'(?![A-Za-z0-9_])', s) for needle in needles)
    shared = ''.join(line for i, line in enumerate(lines, 1) if not any(lo <= i <= hi for _, lo, hi in methods))
    if methods and hit(shared):
        return [module]
    return [module + '.' + name for name, lo, hi in methods if hit(''.join(lines[lo-1:hi]))]


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
        self.reference_files = list(repository_files(ROOT))
        for path in sorted((ROOT / 'src').rglob('*')):
            if path.suffix.lower() in SOURCE_SUFFIXES:
                rel = path.relative_to(ROOT).as_posix()
                raw = self.read(rel)
                lang = 'asm' if path.suffix.lower() in ('.asm', '.inc') else 'c'
                tokens = [(kind, value, start, end)
                          for kind, value, start, end in lexical_tokens(raw.decode('latin1'), lang)
                          if kind in ('id', 'inline_id', 'cmt')]
                self.lexed[rel] = tokens
                self.sources[rel] = (raw, lang, {value for kind, value, _, _ in tokens if kind in ('id', 'inline_id')})
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
        self.fastcall_names = {m[1] for raw, lang, _ in self.sources.values() if lang == 'c'
            for m in re.finditer(r'\b_?_fastcall\s+(?:far\s+)?([A-Za-z_]\w*)\s*\(', raw.decode('latin1'))}

    def object_mapping(self, mapping):
        out = {}
        for old, new in mapping.items():
            convention = self.registry['code'].get(old, {}).get('convention')
            if convention == 'pascal':
                out[old.upper()] = new.upper()
            else:
                prefix = '@' if old in self.fastcall_names else '_'
                out[prefix + old] = prefix + new
        return out

    def data_extents(self):
        """Known sizes only: recorded sizes, accepted COMDEFs, simple sized arrays.

        Never equate the gap to the next registration with an object's size.
        """
        sizes = {n: rec['size'] for n, rec in self.registry['data'].items() if isinstance(rec.get('size'), int)}
        for item in self.items.values():
            for communal in item.get('storage_contract', {}).get('communals', []):
                if communal['name'].startswith('_'):
                    sizes[communal['name'][1:]] = communal['length']
        declaration = re.compile(r'(?m)^\s*(?:(?:extern|static)\s+)?(?:unsigned\s+|signed\s+)?'
            r'(char|int|short|long)\s+(?:far\s+)?([A-Za-z_]\w*)\s*((?:\[\s*(?:0x[0-9A-Fa-f]+|\d+)\s*\])*)\s*(?:=|;)', re.M)
        declared = {}
        for raw, lang, _ in self.sources.values():
            if lang != 'c':
                continue
            for match_ in declaration.finditer(raw.decode('latin1')):
                width = {'char': 1, 'int': 2, 'short': 2, 'long': 4}[match_[1]]
                for count in re.findall(r'0x[0-9A-Fa-f]+|\d+', match_[3]):
                    width *= int(count, 16 if count.lower().startswith('0x') else 10)
                declared[match_[2]] = max(declared.get(match_[2], 0), width)
        for name, width in declared.items():
            sizes.setdefault(name, width)
        return [(n, rec['seg'] * 16 + rec['off'], sizes[n]) for n, rec in self.registry['data'].items()
                if n in sizes and not rec.get('alias_of')]

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
        rows = copy.deepcopy(rows)
        if any(isinstance(r, dict) and 'header' in r for r in rows):
            seen = set()
            required = {'module', 'header', 'summary', 'windows_group', 'kind', 'why'}
            for row in rows:
                if (not isinstance(row, dict) or not required <= row.keys() or
                        set(row) - required - {'evidence', 'source_sha256'} or row['module'] not in self.items or
                        row['module'] in seen):
                    raise RenameError('header batch requires unique known modules and header/summary/windows_group/kind/why')
                if row['kind'] not in ('recovered', 'descriptive') or any(
                        not isinstance(row[f], str) or not row[f].strip()
                        for f in ('summary', 'why', 'windows_group')):
                    raise RenameError('header summary, group and naming evidence must be nonempty text')
                if row['windows_group'] not in ('SIMANT', 'SIMANT1', 'SIMONE', 'SIMTWO', 'ANTEDIT',
                                                 'GR', '_TEXT', 'mixed', 'none (DOS only)', 'unknown'):
                    raise RenameError('invalid Windows group')
                if 'evidence' in row and not isinstance(row['evidence'], list):
                    raise RenameError('header evidence must be a list')
                item = self.items[row['module']]
                if 'source_sha256' in row and row['source_sha256'] != item['source_sha256']:
                    raise RenameError('header predecessor source pin differs: ' + row['module'])
                prior_kind = self.man['modules'].get(row['module'], {}).get('source_name_kind')
                if prior_kind and prior_kind != row['kind']:
                    raise RenameError('header cannot change established filename kind')
                replace_header(self.sources[item['source']][0].decode('latin1'), row['header'], item['lang'])
                normalized = lambda value: ' '.join(value.split())
                if normalized(row['summary']) not in normalized(row['header']) or row['windows_group'] not in row['header']:
                    raise RenameError('header text must contain the recorded summary and Windows group')
                seen.add(row['module'])
            return rows
        old_names, new_names, destinations, moved = set(), set(), set(), set()
        c_names = set(self.registry['code']) | set(self.registry['data'])
        obj_names = set(self.object_mapping({n: n for n in c_names})) | set(self.registry.get('runtime', {}))
        present = set().union(*(s[2] for s in self.sources.values()))
        extents = self.data_extents()
        addresses = set()
        batch_objects = set()
        for row in rows:
            if not isinstance(row, dict):
                raise RenameError('each operation must be an object')
            if row.get('kind') not in ('recovered', 'descriptive') or not isinstance(row.get('why'), str) or not row['why'].strip():
                raise RenameError('kind and nonempty evidence required')
            if 'module' in row:
                if set(row) != {'module', 'path', 'kind', 'why'} or row['module'] not in self.items:
                    raise RenameError('move requires a known module, path, kind, why')
                item = self.items[row['module']]
                path = row['path'].replace('\\', '/')
                target = ROOT / path
                if (not path.startswith('src/') or ':' in path or '..' in Path(path).parts
                        or Path(path).suffix != Path(item['source']).suffix
                        or not target.resolve().is_relative_to((ROOT / 'src').resolve())):
                    raise RenameError('move destination must be a same-language file under src/: ' + path)
                if row['module'] in moved or path.casefold() in destinations or target.exists() or any(
                        p.casefold() == path.casefold() for p in self.sources):
                    raise RenameError('move destination/module collision: ' + path)
                if any(parent.is_file() for parent in target.parents if parent.is_relative_to(ROOT)):
                    raise RenameError('move destination has a file as parent: ' + path)
                row['path'] = path
                moved.add(row['module'])
                destinations.add(path.casefold())
                self.read(path, optional=True)
                continue
            allowed = {'old', 'new', 'kind', 'why'} | ({'address', 'field_of', 'size'} if 'address' in row else set())
            if set(row) - allowed or not {'new', 'kind', 'why'} <= row.keys() or ('old' not in row and 'address' not in row):
                raise RenameError('rename requires old/new or address/new, kind and why')
            new = row['new']
            if not isinstance(new, str) or not IDENT.fullmatch(new):
                raise RenameError(f'bad identifier (maximum 31 characters): {new!r}')
            if 'address' in row:
                if not re.fullmatch(r'[0-9A-Fa-f]{4}:[0-9A-Fa-f]{4}', row['address']):
                    raise RenameError('data address must be SSSS:OOOO')
                seg, off = (int(v, 16) for v in row['address'].split(':'))
                linear = seg * 16 + off
                if linear in addresses:
                    raise RenameError('duplicate data address in batch: ' + row['address'])
                addresses.add(linear)
                parent = row.get('field_of')
                hits = [(n, start, size) for n, start, size in extents if start <= linear < start + size]
                same = [n for n, r in self.registry['data'].items() if r['seg'] * 16 + r['off'] == linear]
                if (hits or same) and not parent:
                    raise RenameError(f'{row["address"]} lies inside registered object(s) {same or [h[0] for h in hits]}; field_of is required')
                if parent and not any(n == parent for n, _, _ in hits):
                    raise RenameError('field_of has no proven containing extent: ' + str(parent))
                if 'size' in row and (not isinstance(row['size'], int) or row['size'] <= 0 or
                        (parent and any(linear + row['size'] > start + size for n, start, size in hits if n == parent))):
                    raise RenameError('invalid field/object size')
                if not parent and 'size' in row and any(linear < start + size and start < linear + row['size'] for _, start, size in extents):
                    raise RenameError('new data extent overlaps a registered object')
                if 'size' in row and any(linear < rec['seg'] * 16 + rec['off'] < linear + row['size']
                                         for rec in self.registry['data'].values()):
                    raise RenameError('new data extent contains another registered object')
                if 'old' not in row:
                    candidates = [f'fd_{seg:04X}_{off:04X}']
                    if seg == match.DGROUP_SEG:
                        candidates.append(f'g_{off:04X}')
                    candidates = [n for n in candidates if n in present and n not in c_names]
                    if len(candidates) > 1:
                        raise RenameError('ambiguous unregistered source identifier; supply old explicitly')
                    if candidates:
                        row['old'] = candidates[0]
                if not hits and not parent and 'old' not in row:
                    preceding = [(rec['off'], name) for name, rec in self.registry['data'].items()
                                 if rec['seg'] == seg and rec['off'] < off and not rec.get('alias_of')]
                    previous = max(preceding)[1] if preceding else None
                    if previous and not any(name == previous for name, _, _ in extents):
                        raise RenameError(f'{row["address"]}: cannot exclude an interior address of {previous}; its extent is unknown')
                record = {}
            else:
                record = self.registry['code'].get(row['old']) or self.registry['data'].get(row['old'])
                if record is None or (record.get('alias_of') and not record.get('field_of')):
                    raise RenameError(f'{row["old"]}: must be a registered primary game symbol')
            old = row.get('old')
            if 'address' in row and old in c_names:
                raise RenameError('address registration cannot redirect an existing registered identifier: ' + old)
            if old is not None and (not isinstance(old, str) or not IDENT.fullmatch(old)):
                raise RenameError('bad old identifier')
            if (old == new and 'address' not in row) or (old and old in old_names) or new in new_names:
                raise RenameError(f'duplicate or identity rename: {old}={new}')
            if old:
                old_names.add(old)
            new_names.add(new)
            if new in csrc.KEYWORDS | csrc.QUALIFIERS | csrc.ASM_WORDS:
                raise RenameError('reserved identifier: ' + new)
            targets = set(self.object_mapping({old: new}).values()) if old else {'_' + new}
            if new in c_names or targets & (obj_names | batch_objects):
                raise RenameError('registered name or runtime collision: ' + new)
            batch_objects.update(targets)
        mapping = c_mapping(rows)
        objmap = self.object_mapping(mapping)
        for row in rows:
            if ('module' not in row and 'old' in row and row['old'] not in present
                    and not self.registry['data'].get(row['old'], {}).get('field_of')
                    and not set(self.object_mapping({row['old']: row['new']})) & present):
                raise RenameError(row['old'] + ': no canonical identifier occurrence')
        for rel, (_, lang, ids) in self.sources.items():
            actual = {**mapping, **objmap} if lang == 'asm' else mapping
            if not ids & set(actual):
                continue
            clash = ids & (set(actual.values()) - set(actual))
            if lang == 'asm':
                clash |= {n for n in ids if n.upper() in {t.upper() for t in actual.values()} and n not in actual}
            for kind, name, _, _ in self.lexed[rel]:
                if name in actual and actual[name].lower() in MASM_RESERVED and (lang == 'asm' or kind == 'inline_id'):
                    raise RenameError(f'{rel}: MASM-reserved identifier: {actual[name]}')
            if clash:
                raise RenameError(f'{rel}: identifier collision: {sorted(clash)}')
        return rows

    def prepare(self, rows):
        if rows and 'header' in rows[0]:
            program, man = copy.deepcopy(self.program), copy.deepcopy(self.man)
            changed = {}
            items = {m['key']: m for m in program['modules']}
            for row in rows:
                key = row['module']
                item = items[key]
                changed[key] = replace_header(self.sources[item['source']][0].decode('latin1'),
                                              row['header'], item['lang']).encode('latin1')
                metadata = {'summary': row['summary'], 'windows_group': row['windows_group'],
                            'file_header': {'text': row['header'], 'name_kind': row['kind'],
                                            'why': row['why'], 'evidence': row.get('evidence', [])}}
                item.update(copy.deepcopy(metadata), source_sha256=canonical.sha(changed[key]))
                target = (man['modules'][key] if key in man['modules'] else
                          man.setdefault('source_annotations', {}).setdefault(key, {'source': item['source']}))
                target.update(copy.deepcopy(metadata))
            return {}, changed, program, man, copy.deepcopy(self.registry)
        mapping = c_mapping(rows)
        objmap = self.object_mapping(mapping)
        changed = {}
        for rel, (raw, lang, ids) in self.sources.items():
            # Comments may name an identifier even in a module without a use.
            actual = {**mapping, **objmap} if lang == 'asm' else mapping
            new = replace_spans(raw.decode('latin1'), actual, self.lexed[rel]).encode('latin1')
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
                    item[field] = renamed(item[field], mapping if field == 'supported_domain' else objmap)
            if item['key'] in changed:
                item['source_sha256'] = canonical.sha(changed[item['key']])
        program['aliases'] = renamed(program.get('aliases', []), objmap)
        for row in rows:
            if row.get('field_of'):
                seg, off = (int(v, 16) for v in row['address'].split(':'))
                parent = self.registry['data'][row['field_of']]
                target = '_' + row['field_of']
                program['aliases'].append({'alias': '_' + row['new'], 'target': objmap.get(target, target),
                    'offset': seg * 16 + off - parent['seg'] * 16 - parent['off'], 'kind': 'data',
                    'reason': row['why'], 'view': {'kind': 'field_of', 'rule': 'Reviewed interior name; adds no storage.'}})
        if 'dos' in program:
            program['dos'] = renamed(program['dos'], {**objmap, **mapping})
        man = copy.deepcopy(self.man)
        for key, module in man['modules'].items():
            for field in ('claims', 'scaffold', 'layout_inferred', 'steered', 'code_data_publics'):
                if field in module:
                    module[field] = renamed(module[field], mapping, keys=field == 'code_data_publics')
        used = {'c': set(), 'object': set()}
        for _, lang, ids in self.sources.values():
            actual = {**mapping, **objmap} if lang == 'asm' else mapping
            used['object' if lang == 'asm' else 'c'].update(actual.get(name, name) for name in ids)
        registry = registry_after(self.registry, rows, used)
        for row in rows:
            if 'module' in row:
                key = row['module']
                changed[key] = self.sources[self.items[key]['source']][0]
                next(m for m in program['modules'] if m['key'] == key)['source'] = row['path']
                if key in man['modules']:
                    man['modules'][key]['source'] = row['path']
                    man['modules'][key]['source_name_kind'] = row['kind']
                    man['modules'][key].setdefault('source_path_history', []).append({'was': self.items[key]['source'], 'why': row['why']})
            elif 'address' in row:
                seg, off = (int(v, 16) for v in row['address'].split(':'))
                linear = seg * 16 + off
                for key, module in man['modules'].items():
                    owner_used = row.get('field_of') in self.sources[self.items[key]['source']][2]
                    if owner_used or any(p['seg'] * 16 + p['off'] <= linear < p['seg'] * 16 + p['off'] + p.get('size', 0)
                                         for p in module.get('placements', {}).values()):
                        changed.setdefault(key, self.sources[self.items[key]['source']][0])
        return mapping, changed, program, man, registry

    def external_changes(self, rows, mapping):
        objmap = self.object_mapping(mapping)
        registered = set(self.registry['code']) | set(self.registry['data'])
        references = {**{k: v for k, v in objmap.items() if k not in registered}, **mapping}
        paths = {self.items[r['module']]['source']: r['path'] for r in rows if 'path' in r}
        changes, tests, port = {}, set(), []
        for rel in self.reference_files:
            if rel.startswith('src/') or rel in ('layout/manifest.json', 'layout/symbols.json', 'layout/oracle.lock.json', 'src/program.json', 'evidence/promotions.jsonl'):
                continue
            if not paths and not external_identifier_file(rel):
                continue
            raw = (ROOT / rel).read_bytes()
            text = raw.decode('latin1')
            relocated = replace_paths(text, paths)
            if port_reference_file(rel, raw):
                if relocated != text:
                    port.append(rel)
                continue
            changed = words(relocated, references) if external_identifier_file(rel) else relocated
            if changed != text:
                self.read(rel)
                changes[rel] = changed.encode('latin1')
                needles = list(references) if external_identifier_file(rel) else []
                tests.update(selected_unit_tests(rel, raw.decode('utf-8-sig'), needles + list(paths)))
        return changes, sorted(tests), sorted(port)

    def repin_path_references(self, changes):
        """Update explicit current path/hash pairs, never historical or oracle pins.

        Source bytes of a move are unchanged. Receipt text can change, so an
        active receipt index may need a new content pin as well. Only a pin
        equal to that file's snapshotted predecessor can be advanced.
        """
        documents = {}
        for rel in self.reference_files:
            if not rel.endswith('.json') or rel.startswith('src/') or rel == 'layout/oracle.lock.json':
                continue
            raw = changes.get(rel, (ROOT / rel).read_bytes())
            if raw is not None and not port_reference_file(rel, raw):
                documents[rel] = json.loads(raw)
        for _ in range(len(documents) + 1):
            advanced = False
            for rel, doc in documents.items():
                touched = False
                def walk(value, historical=False):
                    nonlocal touched
                    if isinstance(value, list):
                        for item in value:
                            walk(item, historical)
                    elif isinstance(value, dict):
                        historical |= any(k in value for k in ('git_commit', 'base_commit', 'prior_commit'))
                        if not historical:
                            for path_field, pin_field in (('path', 'sha256'), ('source', 'source_sha256'), ('receipt', 'receipt_sha256')):
                                target = value.get(path_field)
                                if not isinstance(target, str) or target not in changes or changes[target] is None:
                                    continue
                                before = self.pins.get(target)
                                if before is not None and value.get(pin_field) == canonical.sha(before):
                                    after = canonical.sha(changes[target])
                                    if after != value[pin_field]:
                                        value[pin_field] = after
                                        touched = True
                        for key, item in value.items():
                            walk(item, historical or key in ('supersedes', 'history', 'renamed', 'moved'))
                walk(doc)
                if touched:
                    if rel not in self.pins:
                        self.read(rel)
                    changes[rel] = json_bytes(doc)
                    advanced = True
            if not advanced:
                return
        raise RenameError('cyclic receipt content pins cannot be advanced by a path-only transaction')

    def verify_selected_tests(self, changes, tests):
        if not tests:
            return {'selected': [], 'passed': True}
        overlay = Path(tempfile.mkdtemp(prefix='tests-', dir=self.scratch))
        for rel in self.reference_files:
            target = overlay / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((ROOT / rel).read_bytes())
        if (ROOT / 'assets').exists():
            shutil.copytree(ROOT / 'assets', overlay / 'assets')
        dependency = ROOT / 'build/deps/unicorn'
        if dependency.exists():
            shutil.copytree(dependency, overlay / 'build/deps/unicorn')
        for rel, raw in changes.items():
            path = overlay / rel
            if raw is None:
                path.unlink(missing_ok=True)
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
        # The guard is inherited by Python subprocesses too. Test outputs must
        # remain in this overlay, including hard-coded accidental host writes.
        guard = overlay / '_test_guard'
        guard.mkdir()
        (guard / 'sitecustomize.py').write_text(
            'import os,sys\nfrom pathlib import Path\n'
            'root=Path(os.environ["SIMANT_RENAME_TEST_ROOT"]).resolve()\n'
            'def audit(event,args):\n'
            '    paths=[]\n'
            '    if event=="open" and isinstance(args[0],(str,bytes,os.PathLike)) and '
            '(isinstance(args[1],str) and any(c in args[1] for c in "wax+") or '
            'isinstance(args[2],int) and args[2] & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC)):\n'
            '        paths=[args[0]]\n'
            '    elif event in ("os.mkdir","os.remove","os.rmdir"):\n'
            '        paths=[args[0]]\n'
            '    elif event in ("os.rename","os.link","os.symlink"):\n'
            '        paths=args[:2]\n'
            '    for value in paths:\n'
            '        if not Path(os.fsdecode(value)).resolve().is_relative_to(root):\n'
            '            raise PermissionError("rename test attempted a write outside scratch: "+str(value))\n'
            'sys.addaudithook(audit)\n', encoding='utf8')
        runner = overlay / '_run_selected.py'
        runner.write_text('import sys,unittest\nfrom pathlib import Path\n'
            'root=Path(__file__).resolve().parent\n'
            'sys.path[:0]=[str(root/"tests"),str(root/"tools"),str(root)]\n'
            'import threading\n'
            'gate=threading.BoundedSemaphore(4)\n'
            'def bounded(function):\n'
            '    def run(*a,**k):\n'
            '        with gate: return function(*a,**k)\n'
            '    return run\n'
            'if (root/"tools/compiler.py").exists():\n'
            '    import compiler\n'
            '    compiler.compile_c=bounded(compiler.compile_c)\n'
            '    compiler.assemble=bounded(compiler.assemble)\n'
            'suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(n) for n in sys.argv[1:])\n'
            'result=unittest.TextTestRunner(verbosity=2).run(suite)\n'
            'raise SystemExit(not result.wasSuccessful())\n', encoding='utf8')
        env = os.environ.copy()
        env.update(PYTHONDONTWRITEBYTECODE='1', PYTHONPATH=str(guard),
                   SIMANT_RENAME_TEST_ROOT=str(overlay), TEMP=str(overlay), TMP=str(overlay))
        result = subprocess.run([sys.executable, '-B', str(runner), *tests], cwd=overlay, env=env,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=600,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        log = overlay / 'selected-tests.log'
        log.write_bytes(result.stdout)
        return {'selected': tests, 'passed': result.returncode == 0, 'log': str(log)}

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
                    result.update(exact=True, object_sha256=canonical.sha(compiled.obj),
                                  contribution_sha256=modules.contribution_sha256(OmfReader(communals=True).read(compiled.obj)))
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
        cache_key = json.dumps(rows, sort_keys=True)
        if cache_key in self.cache:
            return self.cache[cache_key]
        mapping, changed, program, man, registry = self.prepare(rows)
        objmap = self.object_mapping(mapping)
        print(f'Checking {len(rows)} operation(s) across {len(changed)} module(s)', flush=True)
        self.establish_baseline(changed)
        results = self.compile_many(changed, program, man, registry)
        failures = {}
        for key, (result, collect) in results.items():
            module = man['modules'].get(key, {})
            reasons = []
            prior_observed = canonical.observed(self.baseline[key][0])
            if rows and 'header' in rows[0]:
                prior_observed = header_comparison_before(prior_observed,
                    self.sources[self.items[key]['source']][0], changed[key])
            if module.get('canonical_admission'):
                prior_result, prior_collect = self.baseline[key]
                if canonical.observed(result) != comparison_after(prior_observed, mapping, objmap):
                    reasons.append('full historical comparison differs from reviewed context')
                # Contribution identity includes names. Change only those symbolic
                # fields in a copy of the predecessor; bytes/indices/order remain.
                if 'object' not in collect or 'object' not in prior_collect:
                    reasons.append('reviewed context lacks complete compiled contributions')
                else:
                    prior_obj = OmfReader(communals=True).read(prior_collect['object'])
                    after_obj = OmfReader(communals=True).read(collect['object'])
                    for field in ('publics', 'local_publics', 'linker_fixups', 'communals', 'externals'):
                        setattr(prior_obj, field, renamed(getattr(prior_obj, field), objmap))
                    if modules.contribution_sha256(prior_obj) != modules.contribution_sha256(after_obj):
                        reasons.append('live bytes/layout/ordered fixups differ from reviewed context')
            elif not result['exact']:
                reasons.append('not every claim, private datum and complete-unit extent is exact')
            if any(r.get('module') == key for r in rows) and (
                    canonical.observed(result) != prior_observed or
                    result.get('contribution_sha256') != self.baseline[key][0].get('contribution_sha256')):
                reasons.append('header or source move changed the historical comparison or live compiler contributions')
            if reasons:
                failures[key] = self.diagnostic(key, result, collect, mapping, reasons)
        outcome = {'mapping': mapping, 'changed': changed, 'program': program, 'man': man,
                   'registry': registry, 'results': results, 'failures': failures}
        external, tests, port = self.external_changes(rows, mapping)
        outcome.update(external=external, selected_tests=tests, port_references=port)
        if not failures:
            changes = self.stage_metadata(rows, outcome)
            outcome['publication'] = changes
            test_result = self.verify_selected_tests(changes, tests)
            outcome['unit_tests'] = test_result
            if not test_result['passed']:
                failures['unit-tests'] = ['affected unit tests failed; see ' + test_result['log']]
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
        items = {m['key']: m for m in program['modules']}
        changes = dict(outcome.get('external', {}))
        paths = {self.items[r['module']]['source']: r['path'] for r in rows if 'path' in r}
        headers = bool(rows and 'header' in rows[0])
        for key, raw in outcome['changed'].items():
            changes[items[key]['source']] = raw
            if self.items[key]['source'] != items[key]['source']:
                changes[self.items[key]['source']] = None
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
            receipt.setdefault('annotated' if headers else 'moved' if paths and not mapping else 'renamed', []).append({'operations': rows,
                'note': 'Leading comments changed; live contributions and semantic review unchanged.' if headers else
                        'Source path move; bytes unchanged.' if paths and not mapping else 'Lexical identifier rename; semantic review unchanged.',
                'prior_receipt_sha256': canonical.sha(self.pins[rel])})
            changes[rel] = json_bytes(receipt)
        changes['layout/manifest.json'] = json_bytes(man, 1)
        changes['src/program.json'] = json_bytes(program)
        changes['layout/symbols.json'] = json_bytes(outcome['registry'], 1)
        for rel, raw in list(changes.items()):
            if raw is None or (rel.startswith('src/') and rel != 'src/program.json'):
                continue
            if rel == 'layout/manifest.json':
                # The prior path is historical provenance, not an active reference.
                history = {k: copy.deepcopy(m.get('source_path_history')) for k, m in man['modules'].items()}
                doc = json.loads(replace_paths(raw.decode('utf8'), paths))
                for key, value in history.items():
                    if value is not None:
                        doc['modules'][key]['source_path_history'] = value
                changes[rel] = json_bytes(doc, 1)
            else:
                changes[rel] = replace_paths(raw.decode('latin1'), paths).encode('latin1')
        if paths:
            self.repin_path_references(changes)
        record = {'time': dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'),
                  'module': 'ANNOTATE' if headers else 'RENAME', 'renames': rows, 'modules_reproven': sorted(outcome['changed']),
                  'files_changed': sorted(changes), 'port_references_unmodified': outcome.get('port_references', []),
                  'prior_program_sha256': canonical.sha(self.pins['src/program.json']),
                  'program_sha256': canonical.sha(changes['src/program.json']),
                  'objects': {k: r[0].get('object_sha256') for k, r in outcome['results'].items()}}
        journal = self.pins['evidence/promotions.jsonl'] or b''
        journal = replace_paths(journal.decode('latin1'), paths).encode('latin1')
        changes['evidence/promotions.jsonl'] = journal + (b'\n' if journal and not journal.endswith(b'\n') else b'') + json_bytes(record, None)
        return changes

    def check_pins(self):
        for rel, expected in self.pins.items():
            path = ROOT / rel
            actual = path.read_bytes() if path.exists() else None
            if actual != expected:
                raise RenameError('canonical input changed during rename: ' + rel)
        current_sources = {p.relative_to(ROOT).as_posix() for p in (ROOT / 'src').rglob('*')
                           if p.suffix.lower() in SOURCE_SUFFIXES}
        if current_sources != set(self.sources):
            raise RenameError('canonical source inventory changed during rename')

    def publish(self, changes):
        # No destination is touched until every proof and every optimistic pin
        # has passed. Stage bytes on the same volume for os.replace.
        staged, backups = {}, {}
        stage = self.scratch / 'publication'
        stage.mkdir()
        for i, (rel, raw) in enumerate(changes.items()):
            staged[rel] = stage / f'{i}.new'
            if raw is not None:
                staged[rel].write_bytes(raw)
            old = self.pins[rel]
            if old is not None:
                backups[rel] = stage / f'{i}.old'
                backups[rel].write_bytes(old)
        with CanonicalLock():
            self.check_pins()
            written = []
            try:
                for rel, path in staged.items():
                    (ROOT / rel).parent.mkdir(parents=True, exist_ok=True)
                    if changes[rel] is None:
                        (ROOT / rel).unlink()
                    else:
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


def run(rows, *, verify_only=False, keep_going=False, jobs=4, scratch_parent=None):
    started = time.perf_counter()
    scratch_root = (Path(scratch_parent) if scratch_parent is not None else ROOT / 'build/scratch').resolve()
    if not scratch_root.resolve().is_relative_to((ROOT / 'build').resolve()):
        raise RenameError('scratch parent must be under build/')
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
        rows = session.validate_rows(rows)
        remaining, refused = list(rows), []
        outcome = session.evaluate(remaining)
        header_observations = {}
        if rows and 'header' in rows[0]:
            for key, (after, collect) in outcome['results'].items():
                before, prior_collect = session.baseline[key]
                destination = scratch / 'objects' / key.replace(':', '_').replace('@', '_')
                destination.mkdir(parents=True)
                for name, pair in (('before', prior_collect), ('after', collect)):
                    if pair.get('object') is not None:
                        (destination / (name + '.obj')).write_bytes(pair['object'])
                (destination / ('draft.' + session.items[key]['lang'])).write_bytes(outcome['changed'][key])
                header_observations[key] = {
                    'before_object_sha256': before.get('object_sha256'),
                    'after_object_sha256': after.get('object_sha256'),
                    'before_contribution_sha256': before.get('contribution_sha256'),
                    'after_contribution_sha256': after.get('contribution_sha256'),
                    'before_comparison': canonical.observed(before),
                    'after_comparison': canonical.observed(after),
                    'source_line_delta': outcome['changed'][key].count(b'\n') -
                                         session.sources[session.items[key]['source']][0].count(b'\n'),
                    'objects': str(destination.relative_to(scratch)),
                    'failures': outcome['failures'].get(key, [])}
        while outcome['failures'] and remaining:
            if all('header' in r for r in remaining) and set(outcome['failures']) <= {r['module'] for r in remaining}:
                # Header rows are independent: no identifier, interface or path changes.
                # Keep every failure from the complete run, without quadratic recompilation.
                for row in remaining:
                    if row['module'] in outcome['failures']:
                        diagnosis = {row['module']: outcome['failures'][row['module']]}
                        refused.append({'renames': [row], 'failing_set': [row], 'failures': diagnosis})
                        print('REFUSED SET:', operation_label(row), diagnosis, flush=True)
                remaining = [r for r in remaining if r['module'] not in outcome['failures']]
                outcome = session.evaluate(remaining) if remaining else None
                break
            culprit = minimal_failure(remaining, lambda subset: bool(session.evaluate(subset)['failures']))
            diagnosis = session.evaluate(culprit)['failures']
            excluded = culprit[-1:] if keep_going else culprit
            refused.append({'renames': excluded, 'failing_set': culprit, 'failures': diagnosis})
            print('REFUSED SET:', ', '.join(operation_label(r) for r in culprit), flush=True)
            for key, details in diagnosis.items():
                print(' ', key, '\n    ' + '\n    '.join(details), flush=True)
            if keep_going and len(culprit) > 1:
                print('  Excluding ' + operation_label(excluded[0]) + ' and checking the complete surviving batch', flush=True)
            remaining = [r for r in remaining if r not in excluded]
            outcome = session.evaluate(remaining) if remaining else None
            if outcome is None:
                break
        published = False
        if remaining and (not refused or keep_going):
            # Reuse only this run's already fresh proof for the final complete
            # surviving batch. Never publish independent singleton successes.
            changes = outcome['publication']
            if verify_only:
                session.check_pins()
            for rel, raw in changes.items():
                if raw is None:
                    continue
                proposal = scratch / 'proposed' / rel
                proposal.parent.mkdir(parents=True, exist_ok=True)
                proposal.write_bytes(raw)
            if not verify_only:
                session.publish(changes)
                published = True
            for key in outcome['changed']:
                label = 'REVIEWED CONTEXT PRESERVED' if session.man['modules'].get(key, {}).get('canonical_admission') else 'EXACT' if key in session.man['modules'] else 'STORAGE'
                print(' ', key + ':', label, flush=True)
            for rel in outcome.get('external', {}):
                print('  reference:', rel, flush=True)
            for rel in outcome.get('port_references', []):
                print('  port reference (unchanged):', rel, flush=True)
            if outcome.get('selected_tests'):
                print('  unit tests:', ', '.join(outcome['selected_tests']), flush=True)
        report = {'requested': len(rows), 'proven': remaining, 'refused': refused,
                  'verify_only': verify_only, 'published': published,
                  'modules_reproven': sorted(outcome['changed']) if outcome else [],
                  'comparisons': {k: canonical.observed(pair[0]) for k, pair in outcome['results'].items()} if outcome else {},
                  'objects': {k: pair[0].get('object_sha256') for k, pair in outcome['results'].items()} if outcome else {},
                  'live_contributions': {k: {'before': session.baseline[k][0].get('contribution_sha256'),
                                             'after': pair[0].get('contribution_sha256')}
                                         for k, pair in outcome['results'].items()} if outcome else {},
                  'header_observations': header_observations,
                  'files_changed': sorted(outcome.get('publication', {})) if outcome else [],
                  'unit_tests': outcome.get('unit_tests', {}) if outcome else {},
                  'port_references_unmodified': outcome.get('port_references', []) if outcome else [],
                  'deleted_sources': sorted(rel for rel, raw in outcome.get('publication', {}).items() if raw is None) if outcome else [],
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
    parser.add_argument('--headers', type=Path, help='replace leading comments and stage module annotations')
    parser.add_argument('--scratch-parent', type=Path)
    parser.add_argument('--move', nargs='+', action='append', default=[], metavar='KEY=NEW_PATH')
    parser.add_argument('--verify-only', action='store_true')
    parser.add_argument('--keep-going', action='store_true')
    parser.add_argument('--jobs', type=int, choices=range(1, 5), default=4)
    args = parser.parse_args(argv)
    if args.headers:
        if args.batch or args.pairs or args.move or args.kind or args.why:
            parser.error('--headers cannot be combined with renames or moves')
        rows = json.loads(args.headers.read_text(encoding='utf-8-sig'))
    elif args.batch:
        if args.pairs or args.move or args.kind or args.why:
            parser.error('--batch cannot be combined with pairs, --kind or --why')
        rows = json.loads(args.batch.read_text(encoding='utf-8-sig'))
    elif args.move:
        if args.pairs or not args.why:
            parser.error('--move requires --why and cannot be combined with identifier pairs')
        rows = []
        for move in [pair for group in args.move for pair in group]:
            if move.count('=') != 1:
                parser.error('expected KEY=NEW_PATH: ' + move)
            key, path = move.split('=')
            rows.append({'module': key.replace(';', ':'), 'path': path,
                         'kind': args.kind or 'descriptive', 'why': args.why})
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
        options = {'scratch_parent': args.scratch_parent} if args.scratch_parent is not None else {}
        return run(rows, verify_only=args.verify_only, keep_going=args.keep_going, jobs=args.jobs, **options)
    except (ValueError, OSError, compiler.CompileError) as error:
        print('REFUSED:', error, file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
