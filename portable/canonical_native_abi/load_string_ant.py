from __future__ import annotations
import re
from .lexical import mask_literals
_FUNCTION = re.compile('\\bLoadStringAnt\\s*\\(\\s*int16_t\\s+object\\s*\\)\\s*\\{')
_DOS_BYTES = re.compile('\\(\\s*int32_t\\s*\\)\\s*\\(\\s*count\\s*\\+\\s*1\\s*\\)\\s*<<\\s*2')
_NATIVE_BYTES = '(int32_t)(count + 1) * (int32_t)sizeof(*list)'


def _function_span(source: str) -> tuple[int, int]:
    code = mask_literals(source)
    match = _FUNCTION.search(code)
    if match is None:
        raise ValueError('root:m075B LoadStringAnt(int16_t object) was not found')
    open_brace = code.find('{', match.start(), match.end())
    depth = 0
    for i in range(open_brace, len(code)):
        if code[i] == '{':
            depth += 1
        elif code[i] == '}':
            depth -= 1
            if depth == 0:
                return (match.start(), i + 1)
    raise ValueError('LoadStringAnt body is unterminated')

def adapt(source: str) -> tuple[str, int]:
    """Rewrite only LoadStringAnt's pointer-table allocation byte count."""
    (start, end) = _function_span(source)
    code = mask_literals(source)
    body_matches = list(_DOS_BYTES.finditer(code, start, end))
    already_native = list(re.finditer(re.escape(_NATIVE_BYTES), code[start:end]))
    if len(body_matches) != 1 or already_native:
        raise ValueError('expected exactly one unadapted DOS pointer-table allocation in LoadStringAnt')
    match = body_matches[0]
    adapted = source[:match.start()] + _NATIVE_BYTES + source[match.end():]
    return (adapted, 1)
