from __future__ import annotations
import hashlib
import re
from typing import Any
_OLD_DECL = re.compile('(?m)^\\s*extern\\s+int\\s+far\\s+(?:v?printf|v?sprintf)\\s*\\([^;]*;\\s*\\n?')
_OLD_STACK = re.compile('\\(\\s*char\\s+far\\s*\\*\\s*\\)\\s*\\(\\s*&\\s*(\\w+)\\s*\\+\\s*1\\s*\\)')
_SIGNATURE = re.compile('(?m)^\\s*[^;{}\\n]*\\b([A-Za-z_]\\w*)\\s*\\(([^;{}]*\\.\\.\\.[^;{}]*)\\)\\s*\\{')
_PROMOTED_LAST_PARAM = {'win_SetObjFormatStr': {'source_name': 'obj', 'source_width': 'int16_t'}, 'win_ObjFormatPrint': {'source_name': 'obj', 'source_width': 'int16_t'}}

def _sha(value: str) -> str:
    return hashlib.sha256(value.encode('utf-8')).hexdigest()

def _matching_brace(text: str, opening: int) -> int:
    depth = 0
    state = 'code'
    i = opening
    while i < len(text):
        ch = text[i]
        nxt = text[i + 1] if i + 1 < len(text) else ''
        if state == 'code':
            if ch == '/' and nxt == '*':
                state = 'comment'
                i += 2
                continue
            if ch == '/' and nxt == '/':
                state = 'line'
                i += 2
                continue
            if ch == '"':
                state = 'string'
            elif ch == "'":
                state = 'char'
            elif ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    return i
        elif state == 'comment':
            if ch == '*' and nxt == '/':
                state = 'code'
                i += 2
                continue
        elif state == 'line':
            if ch == '\n':
                state = 'code'
        elif state in ('string', 'char'):
            if ch == '\\':
                i += 2
                continue
            if state == 'string' and ch == '"' or (state == 'char' and ch == "'"):
                state = 'code'
        i += 1
    raise ValueError('unterminated function body')

def _functions(text: str) -> list[tuple[str, str, int, int, int]]:
    found = []
    for match in _SIGNATURE.finditer(text):
        opening = text.find('{', match.start(), match.end())
        closing = _matching_brace(text, opening)
        params = match.group(2)
        named = [p.strip() for p in params.split(',') if p.strip() and p.strip() != '...']
        if not named:
            raise ValueError(f'variadic function has no named parameter: {match.group(1)}')
        last = re.search('([A-Za-z_]\\w*)\\s*$', named[-1])
        if not last:
            raise ValueError(f'cannot parse final named parameter in {match.group(1)}')
        found.append((match.group(1), last.group(1), match.start(), opening, closing))
    return found

def _replace_identifiers(text: str) -> str:
    """Rename only C identifiers outside comments and literals."""
    names = {'printf': 'dos_printf', 'sprintf': 'dos_sprintf', 'vsprintf': 'dos_vsprintf'}
    out = []
    i = 0
    state = 'code'
    while i < len(text):
        ch = text[i]
        nxt = text[i + 1] if i + 1 < len(text) else ''
        if state == 'code':
            if ch == '/' and nxt in ('*', '/'):
                state = 'comment' if nxt == '*' else 'line'
                out.extend((ch, nxt))
                i += 2
                continue
            if ch == '"':
                state = 'string'
                out.append(ch)
                i += 1
                continue
            if ch == "'":
                state = 'char'
                out.append(ch)
                i += 1
                continue
            if ch.isalpha() or ch == '_':
                end = i + 1
                while end < len(text) and (text[end].isalnum() or text[end] == '_'):
                    end += 1
                token = text[i:end]
                out.append(names.get(token, token))
                i = end
                continue
        elif state == 'comment':
            if ch == '*' and nxt == '/':
                state = 'code'
                out.extend((ch, nxt))
                i += 2
                continue
        elif state == 'line':
            if ch == '\n':
                state = 'code'
        elif state in ('string', 'char'):
            if ch == '\\' and i + 1 < len(text):
                out.extend((ch, text[i + 1]))
                i += 2
                continue
            if state == 'string' and ch == '"' or (state == 'char' and ch == "'"):
                state = 'code'
        out.append(ch)
        i += 1
    return ''.join(out)

def adapt(source: str, source_path: str='<memory>') -> tuple[str, dict[str, Any]]:
    """Lower every supported source stack cursor and DOS formatting reference.

    This does not guess around old cursor expressions: any remaining explicit
    `&parameter + 1` cast passed to a formatting call is an error.
    """
    original = source
    promoted_params: list[dict[str, str]] = []
    for (function_name, details) in _PROMOTED_LAST_PARAM.items():
        pattern = re.compile(f"(\\b{re.escape(function_name)}\\s*\\()\\s*(?:int16_t|int)(?:\\s+{re.escape(details['source_name'])})?\\s*,\\s*(\\.\\.\\.)")
        (source, count) = pattern.subn(f"\\1int32_t _dos_{details['source_name']}_wide, \\2", source)
        if count:
            promoted_params.append({'function': function_name, 'source_last_parameter': details['source_name'], 'native_last_parameter': f"_dos_{details['source_name']}_wide", 'declaration_count': str(count), 'source_value_local': f"{details['source_width']} {details['source_name']}"})
    funcs = _functions(source)
    stack_matches = list(_OLD_STACK.finditer(source))
    edits: list[tuple[int, int, str]] = []
    transformed_funcs = []
    for (index, (name, last_param, sig_start, opening, closing)) in enumerate(funcs):
        calls = [m for m in stack_matches if opening < m.start() < closing]
        if not calls:
            continue
        promoted = _PROMOTED_LAST_PARAM.get(name)
        source_last_param = promoted['source_name'] if promoted else last_param
        if any((m.group(1) != source_last_param for m in calls)):
            bad = next((m.group(1) for m in calls if m.group(1) != source_last_param))
            raise ValueError(f'{source_path}:{name}: stack cursor names {bad}, source final parameter is {source_last_param}')
        body = source[opening + 1:closing]
        if re.search('\\breturn\\b', body):
            raise ValueError(f'{source_path}:{name}: va_end lowering requires review for early return')
        count = len(calls)
        args_name = '_dos_va_args'
        copy_name = '_dos_va_copy'
        setup = '\n'
        if promoted:
            setup += f"    {promoted['source_width']} {promoted['source_name']} = ({promoted['source_width']})_dos_{promoted['source_name']}_wide;\n"
        setup += f'    va_list {args_name};\n    va_start({args_name}, {last_param});\n'
        if count > 1:
            setup += f'    va_list {copy_name};\n'
        edits.append((opening + 1, opening + 1, setup))
        for call in calls:
            if count > 1:
                call_start = source.rfind('vsprintf(', opening + 1, call.start())
                if call_start < 0:
                    raise ValueError(f'{source_path}:{name}: cannot find vsprintf call before stack cursor')
                edits.append((call_start, call_start, f'va_copy({copy_name}, {args_name});\n    '))
                edits.append((call.start(), call.end(), copy_name))
                close = source.find(');', call.end())
                if close < 0 or close > closing:
                    raise ValueError(f'{source_path}:{name}: cannot find end of vsprintf call')
                edits.append((close + 2, close + 2, f'\n    va_end({copy_name});'))
            else:
                edits.append((call.start(), call.end(), args_name))
        edits.append((closing, closing, f'\n    va_end({args_name});\n'))
        transformed_funcs.append({'name': name, 'last_named_parameter': last_param, 'stack_vararg_calls': count, 'uses_va_copy': count > 1, 'original_body_sha256': _sha(source[opening:closing + 1]), 'source_call_order': ['dos_vsprintf' for _ in calls]})
    for (start, end, replacement) in sorted(edits, key=lambda e: (e[0], e[1]), reverse=True):
        source = source[:start] + replacement + source[end:]
    if re.search('\\b(?:v?sprintf|printf)\\s*\\([^;]*&\\s*\\w+\\s*\\+\\s*1', source, re.DOTALL):
        raise ValueError(f'{source_path}: unhandled formatting stack cursor remains')
    (source, removed_decls) = _OLD_DECL.subn('', source)
    source = _replace_identifiers(source)
    if any((name in source for name in ('dos_printf(', 'dos_sprintf(', 'dos_vsprintf('))):
        declarations = '#include <stdarg.h>\n#include <stdint.h>\nextern int16_t dos_printf(const char *format, ...);\nextern int16_t dos_sprintf(char *buffer, const char *format, ...);\nextern int16_t dos_vsprintf(char *buffer, const char *format, va_list args);\n\n'
        if '#include <stdarg.h>' not in source:
            source = declarations + source
    if re.search('(?m)^\\s*extern\\s+.*\\b(?:v?sprintf|printf)\\s*\\(', source):
        raise ValueError(f'{source_path}: unhandled legacy formatting prototype remains')
    lowered_functions = _functions(source)
    for item in transformed_funcs:
        match = next((row for row in lowered_functions if row[0] == item['name']), None)
        if match is None:
            raise AssertionError(f"lowered variadic function disappeared: {item['name']}")
        item['lowered_body_sha256'] = _sha(source[match[3]:match[4] + 1])
    ledger = {'schema': 'whole-program-varargs-lowering-v1', 'source_path': source_path, 'source_sha256': _sha(original), 'output_sha256': _sha(source), 'removed_legacy_prototypes': removed_decls, 'lowered_variadic_functions': transformed_funcs, 'fixed_symbol_rewrites': {'printf': 'dos_printf', 'sprintf': 'dos_sprintf', 'vsprintf': 'dos_vsprintf', 'identifier_replacements_outside_comments_and_literals': True}, 'promoted_last_named_parameters': promoted_params, 'semantic_boundary': 'native va_list; no DOS stack-address cursor survives; 16-bit and 32-bit formatting is implemented by dos_format runtime'}
    return (source, ledger)
