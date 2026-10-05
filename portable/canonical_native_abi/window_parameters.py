"""Explicit DOS optional word arguments for Open, ProxMenu and Swap.

One lowering pass shares lexical call handling. Omitted-slot normalization and
unsupported-domain guards remain explicit native exceptions, not DOS equality.
"""
from __future__ import annotations
import hashlib
import re
from .lexical import mask_literals
from pathlib import Path
from typing import Any
PARAMETER_HEADER = 'portable/whole_program/window_parameters.h'
RUNTIME_HEADER = 'portable/whole_program/window_runtime_owner.h'
OPEN_DECL = 'void win_Open(int16_t win, int16_t supplied_count, int16_t p0, int16_t p1, int16_t p2, int16_t p3)'
PROX_DECL = 'int16_t win_DoProxMenu(int16_t win, int16_t item, int16_t supplied_count, int16_t p0, int16_t p1)'

def _sha(text: str) -> str:
    return hashlib.sha256(text.encode('latin1')).hexdigest()


def _split_args(text: str, masked: str, open_at: int) -> tuple[list[str], int]:
    depth = 1
    args: list[str] = []
    start = open_at + 1
    i = start
    while i < len(masked):
        ch = masked[i]
        if ch == '(':
            depth += 1
        elif ch == ')':
            depth -= 1
            if depth == 0:
                tail = text[start:i].strip()
                if tail or args:
                    args.append(tail)
                return (args, i + 1)
        elif ch == ',' and depth == 1:
            args.append(text[start:i].strip())
            start = i + 1
        i += 1
    raise ValueError('unterminated function argument list')

def _is_declaration(masked: str, name_start: int) -> bool:
    before = masked[max(0, name_start - 160):name_start]
    return bool(re.search('\\b(?:void|int16_t)\\s+$', before))

def _rewrite_calls(text: str, name: str, arities: dict[int, Any], fixed_arity: int) -> tuple[str, list[dict[str, Any]]]:
    masked = mask_literals(text)
    token = re.compile(f'\\b{re.escape(name)}\\b\\s*\\(')
    edits: list[tuple[int, int, str, dict[str, Any]]] = []
    for match in token.finditer(masked):
        name_start = match.start()
        paren = masked.find('(', match.start(), match.end())
        if _is_declaration(masked, name_start):
            continue
        (args, end) = _split_args(text, masked, paren)
        if len(args) == fixed_arity:
            continue
        if len(args) not in arities:
            raise ValueError(f'{name}: unsupported source call arity {len(args)}')
        (converted, detail) = arities[len(args)](args)
        replacement = f'{name}(' + ', '.join(converted) + ')'
        edits.append((name_start, end, replacement, {'source_arity': len(args), **detail}))
    for (start, end, repl, _) in reversed(edits):
        text = text[:start] + repl + text[end:]
    return (text, [entry for (_, _, _, entry) in edits])

def _open_call(args: list[str]) -> tuple[list[str], dict[str, Any]]:
    count = len(args) - 1
    coords = args[1:]
    padded = coords + ['0'] * (4 - len(coords))
    return ([args[0], str(count), *padded], {'supplied_coordinate_words': count})

def _prox_call(args: list[str]) -> tuple[list[str], dict[str, Any]]:
    count = len(args) - 2
    coords = args[2:]
    padded = coords + ['0'] * (2 - len(coords))
    return ([args[0], args[1], str(count), *padded], {'supplied_coordinate_words': count})

def _replace_declarations(text: str) -> tuple[str, dict[str, int]]:
    counts = {'open_declarations': 0, 'open_definitions': 0, 'prox_declarations': 0, 'prox_definitions': 0}
    open_pattern = re.compile('(?m)^(?P<indent>\\s*)(?P<extern>extern\\s+)?void\\s+win_Open\\s*\\([^;{}\\n]*\\)\\s*(?P<end>[;{])')

    def open_sub(m: re.Match[str]) -> str:
        key = 'open_definitions' if m.group('end') == '{' else 'open_declarations'
        counts[key] += 1
        prefix = m.group('indent') + (m.group('extern') or '')
        return prefix + OPEN_DECL + ' ' + m.group('end')
    text = open_pattern.sub(open_sub, text)
    prox_pattern = re.compile('(?m)^(?P<indent>\\s*)(?P<extern>extern\\s+)?int16_t\\s+win_DoProxMenu\\s*\\([^;{}\\n]*\\)\\s*(?P<end>[;{])')

    def prox_sub(m: re.Match[str]) -> str:
        key = 'prox_definitions' if m.group('end') == '{' else 'prox_declarations'
        counts[key] += 1
        prefix = m.group('indent') + (m.group('extern') or '')
        return prefix + PROX_DECL + ' ' + m.group('end')
    text = prox_pattern.sub(prox_sub, text)
    return (text, counts)

def _adapt_open_body(text: str) -> tuple[str, dict[str, Any]]:
    pattern = re.compile('(?m)^[ \\t]*\\(\\(int16_t\\s+\\*\\)\\(w\\s*\\+\\s*0x10\\)\\)\\[0\\]\\s*=\\s*\\(&win\\)\\[1\\];\\s*\\n[ \\t]*\\(\\(int16_t\\s+\\*\\)\\(w\\s*\\+\\s*0x10\\)\\)\\[1\\]\\s*=\\s*\\(&win\\)\\[2\\];\\s*\\n[ \\t]*\\(\\(int16_t\\s+\\*\\)\\(w\\s*\\+\\s*0x10\\)\\)\\[2\\]\\s*=\\s*\\(&win\\)\\[3\\];\\s*\\n[ \\t]*\\(\\(int16_t\\s+\\*\\)\\(w\\s*\\+\\s*0x10\\)\\)\\[3\\]\\s*=\\s*\\(&win\\)\\[4\\];')
    replacement = '        parameter_status = sim_window_parameters_store_open(&sim_window_ref_registry, win, w, supplied_count, p0, p1, p2, p3);\n        if (parameter_status != SIM_WINDOW_PARAMETERS_OK) {\n            Punt("win_Open parameter contract: %s", sim_window_parameters_status_string(parameter_status));\n            win_UnlockWin(win);\n            return;\n        }'
    (out, count) = pattern.subn(replacement, text)
    if count != 1:
        raise ValueError(f'win_Open stack-copy block: expected one, found {count}')
    definition = re.compile('(?s)(void\\s+win_Open\\([^)]*\\)\\s*\\{)')
    (out, declarations) = definition.subn('\\1\\n    SimWindowParameterStatus parameter_status;', out, count=1)
    if declarations != 1:
        raise ValueError(f'win_Open local status declaration: expected one, found {declarations}')
    if '(&win)[' in out:
        raise ValueError('win_Open retains a read beyond its named parameters')
    return (out, {'unsafe_stack_copy_blocks_removed': count, 'failure_behavior': 'source-named Punt with status, then unlock/return fallback'})

def _adapt_prox_body(text: str) -> tuple[str, dict[str, Any]]:
    pattern = re.compile('win_Open\\(\\s*win\\s*,\\s*\\(&item\\)\\[1\\]\\s*,\\s*\\(&item\\)\\[2\\]\\s*\\)\\s*;')
    (out, count) = pattern.subn('win_Open(win, supplied_count, p0, p1, 0, 0);', text)
    if count > 1:
        raise ValueError(f'win_DoProxMenu stack-forwarding block duplicated: {count}')
    return (out, {'unsafe_optional_forwarders_removed': count})

def _adapt_open_prox(source: str | bytes, rel: str) -> tuple[str | bytes, dict[str, Any] | None]:
    rel = Path(rel).as_posix()
    is_bytes = isinstance(source, bytes)
    text = source.decode('latin1') if is_bytes else source
    code = mask_literals(text)
    if not re.search('\\b(?:win_Open|win_DoProxMenu)\\b', code):
        return (source, None)
    if f'#include "{PARAMETER_HEADER}"' in text:
        raise ValueError(f'{rel}: window parameter ABI adapter was applied twice')
    before = _sha(text)
    (out, declarations) = _replace_declarations(text)
    open_body = None
    prox_body = None
    if rel == 'src/root/m20E8.c':
        (out, open_body) = _adapt_open_body(out)
        out = f'#include "{RUNTIME_HEADER}"\n#include "{PARAMETER_HEADER}"\n' + out
    if rel == 'src/root/m22BF.c':
        (out, prox_body) = _adapt_prox_body(out)
    (out, open_calls) = _rewrite_calls(out, 'win_Open', {1: _open_call, 3: _open_call, 5: _open_call}, 6)
    (out, prox_calls) = _rewrite_calls(out, 'win_DoProxMenu', {2: _prox_call, 4: _prox_call}, 5)
    if rel == 'src/root/m20E8.c' and open_body is None:
        raise ValueError('root m20E8 adapter did not rewrite the source stack-copy body')
    if rel == 'src/root/m22BF.c' and prox_body is None:
        raise ValueError('root m22BF adapter did not inspect the prox-menu TU')
    if rel == 'src/root/m20E8.c' and f'#include "{PARAMETER_HEADER}"' not in out:
        out = f'#include "{PARAMETER_HEADER}"\n' + out
    remainder = mask_literals(out)
    if rel == 'src/root/m20E8.c' and re.search('\\(&\\s*win\\s*\\)\\s*\\[\\s*[1-9]', remainder):
        raise ValueError('unsafe win_Open argument-stack access remains')
    if rel == 'src/root/m22BF.c' and re.search('\\(&\\s*item\\s*\\)\\s*\\[\\s*[1-9]', remainder):
        raise ValueError('unsafe win_DoProxMenu argument-stack access remains')
    ledger = {'kind': 'WINDOW_PARAMETERS', 'source': rel, 'input_sha256': before, 'output_sha256': _sha(out), 'fixed_signatures': {'win_Open': OPEN_DECL, 'win_DoProxMenu': PROX_DECL}, 'declarations': declarations, 'win_Open_calls': open_calls, 'win_DoProxMenu_calls': prox_calls, 'open_body': open_body, 'prox_body': prox_body, 'helper_header': PARAMETER_HEADER, 'claim': 'No converted win_Open or win_DoProxMenu call relies on unprovided caller-stack words. Supplied source parameter count is explicit; mode-5 resource references must be present before the window parameter vector is changed or recalculated.'}
    return (out.encode('latin1') if is_bytes else out, ledger)

SWAP_DECL = 'void win_Swap(int16_t from, int16_t to, int16_t supplied_count, int16_t p0, int16_t p1, int16_t p2, int16_t p3)'

def _replace_swap_declarations(text: str) -> tuple[str, dict[str, int]]:
    counts = {'swap_declarations': 0, 'swap_definitions': 0}
    pattern = re.compile('(?m)^(?P<indent>\\s*)(?P<extern>extern\\s+)?void\\s+win_Swap\\s*\\([^;{}\\n]*\\)\\s*(?P<end>[;{])')

    def sub(match: re.Match[str]) -> str:
        key = 'swap_definitions' if match.group('end') == '{' else 'swap_declarations'
        counts[key] += 1
        return match.group('indent') + (match.group('extern') or '') + SWAP_DECL + ' ' + match.group('end')
    return (pattern.sub(sub, text), counts)

def _swap_call(args: list[str]) -> tuple[list[str], dict[str, Any]]:
    if len(args) != 2:
        raise ValueError(f'win_Swap expects its two observed source arguments, got {len(args)}')
    return ([args[0], args[1], '0', '0', '0', '0', '0'], {'source_optional_word_count': 0, 'explicit_zero_slots': 4})

def _adapt_body(text: str) -> tuple[str, dict[str, Any]]:
    assignment = re.compile('(?m)^[ \\t]*\\(\\(int16_t\\s+\\*\\)\\(w\\s*\\+\\s*0x10\\)\\)\\[0\\]\\s*=\\s*p0;\\s*\\n[ \\t]*\\(\\(int16_t\\s+\\*\\)\\(w\\s*\\+\\s*0x10\\)\\)\\[1\\]\\s*=\\s*p1;\\s*\\n[ \\t]*\\(\\(int16_t\\s+\\*\\)\\(w\\s*\\+\\s*0x10\\)\\)\\[2\\]\\s*=\\s*p2;\\s*\\n[ \\t]*\\(\\(int16_t\\s+\\*\\)\\(w\\s*\\+\\s*0x10\\)\\)\\[3\\]\\s*=\\s*p3;')
    replacement = '    parameter_status = sim_window_parameters_store_open(&sim_window_ref_registry, to, w, supplied_count, p0, p1, p2, p3);\n    if (parameter_status != SIM_WINDOW_PARAMETERS_OK) {\n        Punt("win_Swap parameter contract: %s", sim_window_parameters_status_string(parameter_status));\n        win_UnlockWin(to);\n        return;\n    }'
    (out, count) = assignment.subn(replacement, text)
    if count != 1:
        raise ValueError(f'win_Swap parameter stores: expected one four-word block, found {count}')
    definition = re.compile('(?s)(void\\s+win_Swap\\([^)]*\\)\\s*\\{)')
    (out, decls) = definition.subn('\\1\\n    SimWindowParameterStatus parameter_status;', out, count=1)
    if decls != 1:
        raise ValueError(f'win_Swap status local: expected one definition, found {decls}')
    return (out, {'parameter_store_blocks_replaced': count, 'failure_behavior': 'source-named Punt with status, unlock/return fallback'})

def _adapt_swap(source: str | bytes, rel: str) -> tuple[str | bytes, dict[str, Any] | None]:
    rel = Path(rel).as_posix()
    is_bytes = isinstance(source, bytes)
    text = source.decode('latin1') if is_bytes else source
    code = mask_literals(text)
    if not re.search('\\bwin_Swap\\b', code):
        return (source, None)
    if 'SIMANT_WINDOW_SWAP_PARAMETERS' in text:
        raise ValueError(f'{rel}: window swap adapter was applied twice')
    before = _sha(text)
    (out, declarations) = _replace_swap_declarations(text)
    body = None
    if rel == 'src/root/m20E8.c':
        if f'#include "{PARAMETER_HEADER}"' not in out:
            raise ValueError('root m20E8 must lower Open parameters first (parameter helper header absent)')
        (out, body) = _adapt_body(out)
    (out, calls) = _rewrite_calls(out, 'win_Swap', {2: _swap_call}, 7)
    if rel == 'src/root/m20E8.c' and body is None:
        raise ValueError('root m20E8 win_Swap definition was not converted')
    masked = mask_literals(out)
    if rel == 'src/root/m20E8.c' and re.search('\\(\\(int16_t\\s*\\*\\)\\(w\\s*\\+\\s*0x10\\)\\)\\[\\d+\\]\\s*=\\s*p[0-3]', masked):
        raise ValueError('root win_Swap retains direct optional-slot stores')
    if '(&from)[' in masked or '(&to)[' in masked:
        raise ValueError(f'{rel}: unsafe win_Swap stack read remains')
    ledger = {'kind': 'WINDOW_SWAP_PARAMETERS', 'source': rel, 'input_sha256': before, 'output_sha256': _sha(out), 'fixed_signature': SWAP_DECL, 'declarations': declarations, 'calls': calls, 'body': body, 'helper': 'sim_window_parameters_store_open', 'claim': 'The shipped two-argument win_Swap callers carry supplied_count=0 and four explicit zero words. The actual destination resource view must validate before its parameter slots are written or recalculated.'}
    return (out.encode('latin1') if is_bytes else out, ledger)


def adapt(source: str | bytes, rel: str):
    output, open_prox = _adapt_open_prox(source, rel)
    output, swap = _adapt_swap(output, rel)
    return output, {'open_prox': open_prox, 'swap': swap}
