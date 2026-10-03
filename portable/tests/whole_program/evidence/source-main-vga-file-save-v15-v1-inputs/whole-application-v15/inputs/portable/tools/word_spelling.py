"""Resolve implicit DOS word types before the pinned source transformer.

The existing generator intentionally remains unchanged. This optional conversion
is for a new, separately reviewed profile: it does not repair existing generated
files or establish equivalence of arithmetic under host integer promotions.
"""
from __future__ import annotations

import re


# Preserve comments and literal contents, including escaped quotes. This pass
# recognizes type spellings; it does not rename identifiers or reorder code.
PROTECTED = re.compile(
    r'("(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|/\*.*?\*/|//[^\n]*)',
    re.S,
)
BARE_UNSIGNED = re.compile(r"\bunsigned\b(?!\s+(?:char|short|int|long)\b)")


def explicit_unsigned_word(source: str) -> tuple[str, int]:
    """Replace bare ``unsigned`` with ``uint16_t``; return replacement count.

    Explicit unsigned char/short/int/long are left to the caller's existing
    conversion. Comments between a type specifier and its following specifier
    need a real token parser; fail rather than emit an invalid combination.
    """
    parts = PROTECTED.split(source)
    count = 0
    for i in range(0, len(parts), 2):
        code = parts[i]
        # A declaration such as unsigned /* note */ int must not become
        # uint16_t /* note */ int. Skip comments to inspect the next code token.
        if re.search(r"\bunsigned\s*$", code) and i + 2 < len(parts):
            following = i + 2
            while (following < len(parts) and not parts[following].strip()
                   and following + 2 < len(parts)
                   and parts[following + 1].startswith(("/*", "//"))):
                following += 2
            if re.match(r"\s*(?:char|short|int|long)\b", parts[following]):
                raise ValueError("comment-separated unsigned type needs token-aware conversion")
        parts[i], replacements = BARE_UNSIGNED.subn("uint16_t", code)
        count += replacements
    return "".join(parts), count
