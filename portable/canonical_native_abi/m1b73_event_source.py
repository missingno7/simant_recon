from __future__ import annotations
import hashlib
import re
SOURCE_MODULES = {'src/S19/m384C.c', 'src/S10/m35F5.c'}
HEADER = '#include "portable/whole_program/platform/m1b73_event_enqueue.h"\n'

def _sha(source: str) -> str:
    return hashlib.sha256(source.encode('utf-8')).hexdigest()

def _skip_space_comments(source: str, pos: int) -> int:
    while pos < len(source):
        if source[pos].isspace():
            pos += 1
        elif source.startswith('//', pos):
            end = source.find('\n', pos + 2)
            return len(source) if end < 0 else _skip_space_comments(source, end + 1)
        elif source.startswith('/*', pos):
            end = source.find('*/', pos + 2)
            if end < 0:
                raise ValueError('unterminated C block comment')
            pos = end + 2
        else:
            break
    return pos

def _call_end_and_arity(source: str, open_pos: int) -> tuple[int, int]:
    depth = 0
    commas = 0
    saw_token = False
    i = open_pos
    while i < len(source):
        i = _skip_space_comments(source, i)
        if i >= len(source):
            break
        ch = source[i]
        if ch in '"\'':
            quote = ch
            saw_token = True
            i += 1
            while i < len(source):
                if source[i] == '\\':
                    i += 2
                elif source[i] == quote:
                    i += 1
                    break
                else:
                    i += 1
            continue
        if ch == '(':
            depth += 1
            if depth > 1:
                saw_token = True
        elif ch == ')':
            depth -= 1
            if depth == 0:
                return (i + 1, commas + (1 if saw_token else 0))
        elif depth == 1 and ch == ',':
            commas += 1
        elif depth == 1 and (not ch.isspace()):
            saw_token = True
        i += 1
    raise ValueError('unterminated f_1B73_030F call')

def _calls(source: str) -> list[tuple[int, int, int, int]]:
    result = []
    i = 0
    while i < len(source):
        if source.startswith('//', i):
            end = source.find('\n', i + 2)
            i = len(source) if end < 0 else end + 1
            continue
        if source.startswith('/*', i):
            end = source.find('*/', i + 2)
            if end < 0:
                raise ValueError('unterminated C block comment')
            i = end + 2
            continue
        if source[i] in '"\'':
            quote = source[i]
            i += 1
            while i < len(source):
                if source[i] == '\\':
                    i += 2
                elif source[i] == quote:
                    i += 1
                    break
                else:
                    i += 1
            continue
        if source.startswith('f_1B73_030F', i):
            before = source[i - 1] if i else ' '
            after_name = i + len('f_1B73_030F')
            after = source[after_name] if after_name < len(source) else ' '
            if (before.isalnum() or before == '_') or (after.isalnum() or after == '_'):
                i += 1
                continue
            open_pos = _skip_space_comments(source, after_name)
            if open_pos < len(source) and source[open_pos] == '(':
                (end, arity) = _call_end_and_arity(source, open_pos)
                result.append((i, after_name, end, arity))
                i = end
                continue
        i += 1
    return result

def adapt(source: str, source_path: str) -> tuple[str, dict[str, object]]:
    if source_path not in SOURCE_MODULES:
        raise ValueError(f'unsupported m1B73 event callsite source: {source_path}')
    digest = _sha(source)
    old_proto = re.compile('(?m)^extern\\s+void\\s+far\\s+f_1B73_030F\\s*\\(\\s*\\)\\s*;\\s*\\n')
    (source, proto_count) = old_proto.subn('', source, count=1)
    if proto_count != 1:
        raise ValueError('expected one old-style f_1B73_030F prototype')
    calls = _calls(source)
    expected_arities = [4, 5] if source_path == 'src/S19/m384C.c' else [4, 5, 4]
    if [arity for (_, _, _, arity) in calls] != expected_arities:
        raise ValueError(f'unexpected enqueue callsite arities: {[x[3] for x in calls]}')
    for (start, name_end, _, arity) in reversed(calls):
        if arity == 4:
            source = source[:start] + 'portable_m1b73_event_enqueue_four_word_command' + source[name_end:]
    if HEADER.strip() not in source:
        source = HEADER + source
    return (source, {'kind': 'SOURCE_M1B73_TYPED_EVENT_CALLS', 'source_path': source_path, 'input_sha256': digest, 'output_sha256': _sha(source), 'callsite_arities': expected_arities, 'four_word_calls': len([arity for arity in expected_arities if arity == 4]), 'five_word_calls': len([arity for arity in expected_arities if arity == 5]), 'normalization': 'four-word command calls use a separately named helper that supplies DX=0 for the consumer-unobserved Event.v field; five-word call passes every word explicitly'})
