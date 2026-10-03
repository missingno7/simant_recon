"""Project the proven AX result of root:m00F8 f_00F8_02EF into its C type.

The historical source calls this an empty `void` function, but initStuff's
source declaration consumes its AX result. Original DOS execution shows that
the compiler-emitted stack-check prologue returns AX=0. This post-word adapter
expresses that native ABI result without changing src/ or guessing from C's
void semantics.
"""
from __future__ import annotations

import re

from portable.whole_program.conversions.load_string_ant import _mask_noncode


_FUNCTION = re.compile(
    r"\bvoid(?P<space>\s+)f_00F8_02EF(?P<signature>\s*\(\s*void\s*\)\s*)\{"
)
_NATIVE = re.compile(
    r"\bint16_t\s+f_00F8_02EF\s*\(\s*void\s*\)\s*\{\s*return\s+0\s*;\s*\}"
)


def adapt(source: str, rel: str = "") -> tuple[str, int]:
    """Convert only the empty generated f_00F8_02EF body to its AX=0 ABI."""
    if rel and not rel.replace("\\", "/").endswith("root_m00F8.c"):
        return source, 0
    code = _mask_noncode(source)
    matches = list(_FUNCTION.finditer(code))
    already = list(_NATIVE.finditer(code))
    if len(matches) != 1 or already:
        raise ValueError("expected exactly one unadapted empty f_00F8_02EF definition")
    match = matches[0]
    open_brace = code.find("{", match.start(), match.end())
    depth = 1
    close_brace = open_brace + 1
    while close_brace < len(code) and depth:
        if code[close_brace] == "{":
            depth += 1
        elif code[close_brace] == "}":
            depth -= 1
        close_brace += 1
    if depth:
        raise ValueError("f_00F8_02EF body is unterminated")
    close_brace -= 1
    if code[open_brace + 1:close_brace].strip():
        raise ValueError("f_00F8_02EF is no longer the proven empty body")
    replacement = (
        "int16_t" + match.group("space") + "f_00F8_02EF" +
        match.group("signature") + "{\n    return 0;\n}"
    )
    return source[:match.start()] + replacement + source[close_brace + 1:], 1
