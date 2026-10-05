from __future__ import annotations
import hashlib
import re
from pathlib import Path
from typing import Any
PARAMETER_HEADER = 'portable/whole_program/window_parameters.h'
from . import window_parameter_abi_v1 as _base
SWAP_DECL = 'void win_Swap(int16_t from, int16_t to, int16_t supplied_count, int16_t p0, int16_t p1, int16_t p2, int16_t p3)'

def _sha(text: str) -> str:
    return hashlib.sha256(text.encode('latin1')).hexdigest()

def _replace_declarations(text: str) -> tuple[str, dict[str, int]]:
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

def adapt(source: str | bytes, rel: str) -> tuple[str | bytes, dict[str, Any] | None]:
    rel = Path(rel).as_posix()
    is_bytes = isinstance(source, bytes)
    text = source.decode('latin1') if is_bytes else source
    code = _base._mask_c(text)
    if not re.search('\\bwin_Swap\\b', code):
        return (source, None)
    if 'SIMANT_WHOLE_PROGRAM_WINDOW_SWAP_PARAMETER_ABI_V2' in text:
        raise ValueError(f'{rel}: window swap adapter was applied twice')
    before = _sha(text)
    (out, declarations) = _replace_declarations(text)
    body = None
    if rel == 'src/root/m20E8.c':
        if f'#include "{PARAMETER_HEADER}"' not in out:
            raise ValueError('root m20E8 must run v1 adapter first (parameter helper header absent)')
        (out, body) = _adapt_body(out)
    (out, calls) = _base._rewrite_calls(out, 'win_Swap', {2: _swap_call}, 7)
    if rel == 'src/root/m20E8.c' and body is None:
        raise ValueError('root m20E8 win_Swap definition was not converted')
    masked = _base._mask_c(out)
    if rel == 'src/root/m20E8.c' and re.search('\\(\\(int16_t\\s*\\*\\)\\(w\\s*\\+\\s*0x10\\)\\)\\[\\d+\\]\\s*=\\s*p[0-3]', masked):
        raise ValueError('root win_Swap retains direct optional-slot stores')
    if '(&from)[' in masked or '(&to)[' in masked:
        raise ValueError(f'{rel}: unsafe win_Swap stack read remains')
    ledger = {'kind': 'WINDOW_SWAP_PARAMETER_ABI_V2', 'source': rel, 'input_sha256': before, 'output_sha256': _sha(out), 'fixed_signature': SWAP_DECL, 'declarations': declarations, 'calls': calls, 'body': body, 'helper': 'sim_window_parameters_store_open', 'claim': 'The shipped two-argument win_Swap callers carry supplied_count=0 and four explicit zero words. The actual destination resource view must validate before its parameter slots are written or recalculated.'}
    return (out.encode('latin1') if is_bytes else out, ledger)
