#!/usr/bin/env python3
"""Adapt generated source TUs to the one typed DGROUP clip/Rect owner.

This pass is intentionally narrow and fail-closed. It is not a generator and
does not alter source or historical files; whole_program.py can apply it to its
private generated draft before compile/link.
"""
from __future__ import annotations

import re

RECT_DEF = re.compile(
    r"(?m)^\s*struct\s+Rect\s*\{\s*"
    r"(?:int16_t|short)\s+left\s*;\s*"
    r"(?:int16_t|short)\s+top\s*;\s*"
    r"(?:int16_t|short)\s+right\s*;\s*"
    r"(?:int16_t|short)\s+bottom\s*;\s*\}\s*;\s*"
)
G5AAC_DECL = re.compile(r"(?m)^\s*extern\s+(?:struct\s+Rect|int16_t|char)\s*\*\s*g_5AAC\s*;\s*\n?")
G5A9C_STRUCT_DECL = re.compile(r"(?m)^\s*extern\s+struct\s+Rect\s+g_5A9C\s*;\s*\n?")
G5A9C_CHAR_DECL = re.compile(r"(?m)^\s*extern\s+char\s+g_5A9C\s*\[\s*\]\s*;\s*\n?")

MODULES = {
    "root_m00F8.c", "root_m1C62.c", "root_m1CE2.c", "root_m1D8E.c",
    "root_m1E57.c", "root_m205F.c", "root_m218D.c", "root_m21FA.c",
    "S10_m35F5.c", "S17_m384C.c", "S22_m39C7.c",
}


class ConversionError(ValueError):
    pass


def _insert_header(text: str) -> str:
    header = '#include "portable/whole_program/window_source_rects.h"\n'
    if header in text:
        return text
    marker = "#pragma pack(push, 2)\n"
    if marker not in text:
        raise ConversionError("source TU has no expected DOS packing boundary")
    return text.replace(marker, marker + header, 1)


def convert_source(name: str, text: str) -> str:
    """Return the adapted TU text or raise if its expected source view drifted."""
    if name not in MODULES:
        if "g_5AAC" in text or "g_5A9C" in text:
            raise ConversionError(f"unreviewed clip owner consumer: {name}")
        return text

    uses_5aac = "g_5AAC" in text
    uses_5a9c = "g_5A9C" in text
    if not (uses_5aac or uses_5a9c):
        raise ConversionError(f"listed module does not use source clip globals: {name}")

    rect_matches = list(RECT_DEF.finditer(text))
    if rect_matches:
        text, removed = RECT_DEF.subn("", text)
        if removed != 1:
            raise ConversionError(f"expected one local Rect declaration in {name}, saw {removed}")

    if uses_5aac:
        text, declarations = G5AAC_DECL.subn("", text)
        if declarations != 1:
            raise ConversionError(f"expected one g5AAC declaration in {name}, saw {declarations}")
        if name == "S10_m35F5.c":
            text, locals_changed = re.subn(r"(?m)^\s*char\s+\*\s*saved\s*;",
                                           "    struct Rect *saved;", text)
            if locals_changed != 1 or "saved = g_5AAC;" not in text:
                raise ConversionError("S10 g5AAC save/restore view changed")
        if name in ("root_m21FA.c", "S22_m39C7.c"):
            text, indices = re.subn(r"\bg_5AAC\s*\[\s*1\s*\]", "g_5AAC->top", text)
            if indices != 1:
                raise ConversionError(f"expected one top-word alias access in {name}, saw {indices}")
            text = re.sub(r"(g_5AAC->top\s*[!=]=\s*)0x8000\b",
                          r"\1(int16_t)0x8000", text)
        elif re.search(r"\bg_5AAC\s*\[", text):
            raise ConversionError(f"unmapped word-view access through g5AAC in {name}")

    if uses_5a9c:
        text, rect_decl = G5A9C_STRUCT_DECL.subn("", text)
        text, char_decl = G5A9C_CHAR_DECL.subn("", text)
        if rect_decl + char_decl != 1:
            raise ConversionError(f"expected one typed or raw g5A9C declaration in {name}, "
                                  f"saw {rect_decl + char_decl}")
        if name == "root_m1CE2.c":
            text, uses = re.subn(r"\breturn\s+g_5A9C\s*;",
                                 "return (char *)&g_5A9C;", text)
            if uses != 1:
                raise ConversionError("m1CE2 raw Rect address return changed")
        elif name == "root_m218D.c":
            text, uses = re.subn(r"\bf_1E57_0A9C\s*\(\s*g_5A9C\s*\)",
                                 "f_1E57_0A9C((char *)&g_5A9C)", text)
            if uses != 1:
                raise ConversionError("m218D raw Rect address use changed")
    text = _insert_header(text)
    declarations = []
    if uses_5aac:
        declarations.append("extern struct Rect *g_5AAC;")
    if uses_5a9c:
        declarations.append("extern struct Rect g_5A9C;")
    declaration_block = "\n".join(declarations) + "\n"
    text = text.replace('#include "portable/whole_program/window_source_rects.h"\n',
                        '#include "portable/whole_program/window_source_rects.h"\n' +
                        declaration_block, 1)
    if RECT_DEF.search(text):
        raise ConversionError(f"legacy duplicate storage view remains in {name}")
    return text


def self_test() -> None:
    rect = "struct Rect { int16_t left; int16_t top; int16_t right; int16_t bottom; };\n"
    base = "#pragma pack(push, 2)\n" + rect
    cases = {
        "root_m1D8E.c": base + "extern struct Rect *g_5AAC;\n",
        "root_m21FA.c": base + "extern int16_t *g_5AAC;\nvoid f(void) { if (g_5AAC != 0 && g_5AAC[1] == 0x8000) {} }\n",
        "S22_m39C7.c": base + "extern int16_t *g_5AAC;\nvoid f(void) { if (g_5AAC[1] != 0x8000) {} }\n",
        "S10_m35F5.c": base + "extern char *g_5AAC;\nvoid f(void) {\n    char *saved;\n    saved = g_5AAC; g_5AAC = 0; g_5AAC = saved;\n}\n",
        "root_m00F8.c": base + "extern struct Rect g_5A9C;\nvoid f(void) { (void)g_5A9C.right; }\n",
        "root_m1CE2.c": "#pragma pack(push, 2)\n" + rect +
            "extern char g_5A9C[];\nchar *f(void) { return g_5A9C; }\n",
        "root_m218D.c": "#pragma pack(push, 2)\n" + rect +
            "extern char g_5A9C[];\nvoid f(void) { f_1E57_0A9C(g_5A9C); }\n",
    }
    for name, content in cases.items():
        converted = convert_source(name, content)
        if "window_source_rects.h" not in converted:
            raise ConversionError(f"canonical Rect header missing for {name}")
    try:
        convert_source("unknown.c", "extern struct Rect *g_5AAC;\n")
    except ConversionError:
        pass
    else:
        raise ConversionError("unknown consumer negative control was accepted")


if __name__ == "__main__":
    self_test()
    print("graphics clip source-view converter controls: PASS")
