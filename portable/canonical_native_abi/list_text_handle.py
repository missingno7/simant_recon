from __future__ import annotations
import re
from .lexical import mask_literals
EXPECTED_REPLACEMENTS = 20


def adapt(source: str) -> tuple[str, int]:
    pattern = re.compile('\\blist\\s*->\\s*text\\b')
    code = mask_literals(source)
    matches = list(pattern.finditer(code))
    if len(matches) != EXPECTED_REPLACEMENTS:
        raise ValueError(f'expected {EXPECTED_REPLACEMENTS} List.text sites, got {len(matches)}')
    replacement = '(*sim_window_list_text_slot(list))'
    adapted = source
    for match in reversed(matches):
        adapted = adapted[:match.start()] + replacement + adapted[match.end():]
    include = '#include "portable/whole_program/window_list_refs.h"\n'
    if include not in adapted:
        adapted = include + adapted
    return (adapted, len(matches))
