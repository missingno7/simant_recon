"""Narrow source adapter for the root:m23E6 List.text object Handle field.

This remains separate from central whole-program generation until reviewed.
It adapts only this exact generated TU's direct `list->text` lvalue to the
native sidecar for the same source object's +0x34 Handle slot.
"""
from __future__ import annotations

import re

EXPECTED_REPLACEMENTS = 20


def _code_mask(text: str) -> str:
    """Mask C comments and literals while preserving byte offsets/newlines."""
    out = list(text)
    i = 0
    state = "code"
    while i < len(text):
        c = text[i]
        n = text[i + 1] if i + 1 < len(text) else ""
        if state == "code":
            if c == "/" and n == "*":
                out[i] = out[i + 1] = " "
                i += 2
                state = "block"
                continue
            if c == "/" and n == "/":
                out[i] = out[i + 1] = " "
                i += 2
                state = "line"
                continue
            if c == '"':
                out[i] = " "
                state = "string"
            elif c == "'":
                out[i] = " "
                state = "char"
        elif state == "block":
            if c == "*" and n == "/":
                out[i] = out[i + 1] = " "
                i += 2
                state = "code"
                continue
            if c != "\n": out[i] = " "
        elif state == "line":
            if c == "\n":
                state = "code"
            else:
                out[i] = " "
        else:
            quote = '"' if state == "string" else "'"
            if c == "\\":
                out[i] = " "
                if i + 1 < len(text):
                    if text[i + 1] != "\n": out[i + 1] = " "
                    i += 2
                    continue
            elif c == quote:
                out[i] = " "
                state = "code"
            elif c != "\n":
                out[i] = " "
        i += 1
    return "".join(out)


def adapt(source: str) -> tuple[str, int]:
    pattern = re.compile(r"\blist\s*->\s*text\b")
    code = _code_mask(source)
    matches = list(pattern.finditer(code))
    if len(matches) != EXPECTED_REPLACEMENTS:
        raise ValueError(f"expected {EXPECTED_REPLACEMENTS} List.text sites, got {len(matches)}")
    replacement = "(*sim_window_list_text_slot(list))"
    adapted = source
    for match in reversed(matches):
        adapted = adapted[:match.start()] + replacement + adapted[match.end():]
    include = '#include "portable/whole_program/window_list_refs.h"\n'
    if include not in adapted:
        adapted = include + adapted
    return adapted, len(matches)
