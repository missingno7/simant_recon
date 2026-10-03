#!/usr/bin/env python3
"""Convert selected m1B4E-style source globals to the bound graphics owner."""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys


FIELDS = (
    "g_3DA0", "g_3DA2", "g_3DB2", "g_3DB4", "g_3DB6", "g_3DD2", "g_3DDA",
    "g_3DDC", "g_3DDE", "g_3DE0", "g_3DE2", "g_3DE4",
)
FIELD_SET = set(FIELDS)
CALLBACKS = ("g_9128", "g_9134", "g_9154", "g_9158", "g_9170")
FUNCTIONS = ("f_1B4E_000D", "f_1B4E_015B", "f_1B4E_0228")
DECL_NAMES = FIELDS + CALLBACKS + FUNCTIONS
EXTERN_LINE = re.compile(r"^\s*extern\b(?P<body>[^;]*);\s*(?://.*)?$")


def replace_code_identifiers(text: str) -> str:
    """Replace identifier tokens outside C comments and string/char literals."""
    out: list[str] = []
    i = 0
    state = "code"
    while i < len(text):
        ch = text[i]
        nxt = text[i + 1] if i + 1 < len(text) else ""
        if state == "code":
            if ch == "/" and nxt == "/":
                out.extend((ch, nxt)); i += 2; state = "line_comment"; continue
            if ch == "/" and nxt == "*":
                out.extend((ch, nxt)); i += 2; state = "block_comment"; continue
            if ch == '"':
                out.append(ch); i += 1; state = "string"; continue
            if ch == "'":
                out.append(ch); i += 1; state = "char"; continue
            if ch.isalpha() or ch == "_":
                end = i + 1
                while end < len(text) and (text[end].isalnum() or text[end] == "_"):
                    end += 1
                name = text[i:end]
                member_owner = i - 1
                while member_owner >= 0 and text[member_owner].isspace():
                    member_owner -= 1
                member_access = (member_owner >= 0 and text[member_owner] == ".") or (
                    member_owner >= 1 and text[member_owner - 1:member_owner + 1] == "->"
                )
                source_point_macro = "SIM_GRAPHICS_SOURCE_g_3DA0"
                if (name == "g_3DA0" or name == source_point_macro) and not member_access:
                    member_start = end
                    while member_start < len(text) and text[member_start].isspace():
                        member_start += 1
                    if member_start < len(text) and text[member_start] == ".":
                        member_end = member_start + 1
                        while member_end < len(text) and text[member_end].isspace():
                            member_end += 1
                        member_stop = member_end
                        while member_stop < len(text) and (text[member_stop].isalnum() or text[member_stop] == "_"):
                            member_stop += 1
                        member = text[member_end:member_stop]
                        if member in ("x", "y"):
                            field = "g_3DA0" if member == "x" else "g_3DA2"
                            out.append(f"SIM_GRAPHICS_SOURCE_{field}")
                            i = member_stop
                            continue
                previous = i - 1
                while previous >= 0 and text[previous].isspace():
                    previous -= 1
                is_member = previous >= 0 and text[previous] == "."
                is_pointer_member = previous >= 1 and text[previous - 1:previous + 1] == "->"
                out.append(f"SIM_GRAPHICS_SOURCE_{name}"
                           if name in FIELD_SET and not (is_member or is_pointer_member)
                           else name)
                i = end
                continue
            out.append(ch); i += 1; continue
        if state == "line_comment":
            out.append(ch); i += 1
            if ch == "\n":
                state = "code"
            continue
        if state == "block_comment":
            out.append(ch); i += 1
            if ch == "*" and nxt == "/":
                out.append(nxt); i += 1; state = "code"
            continue
        out.append(ch); i += 1
        if ch == "\\" and i < len(text):
            out.append(text[i]); i += 1; continue
        if (state == "string" and ch == '"') or (state == "char" and ch == "'"):
            state = "code"
    return "".join(out)


def convert(text: str) -> tuple[str, tuple[str, ...]]:
    kept: list[str] = []
    removed: list[str] = []
    for line in text.splitlines(keepends=True):
        match = EXTERN_LINE.match(line.rstrip("\r\n"))
        if match:
            body = match.group("body")
            declared = [name for name in DECL_NAMES
                        if re.search(rf"\b{re.escape(name)}\b", body)]
            if len(declared) == 1:
                name = declared[0]
                variable_decl = (
                    name in FIELDS and re.search(rf"\b{re.escape(name)}\s*$", body) is not None
                ) or (
                    name in CALLBACKS and re.search(rf"\b{re.escape(name)}\s*\)\s*\(", body) is not None
                )
                function_decl = name in FUNCTIONS and re.search(
                    rf"\b{re.escape(name)}\s*\(", body
                ) is not None
                if variable_decl or function_decl:
                    removed.append(name)
                    continue
        kept.append(line)
    converted = replace_code_identifiers("".join(kept))
    include = '#include "portable/whole_program/platform/graphics_source_fields.h"\n'
    return include + converted, tuple(removed)


def self_test() -> None:
    sample = (
        "extern int16_t g_3DB4;\n"
        "extern uint8_t g_3DE0; // selected source global\n"
        "extern void (far * near g_9134)(int left, int top, int right, int bottom, int color);\n"
        "extern void far f_1B4E_0228(int color);\n"
        "void draw(void) { g_3DB4 = 480; g_3DE0 = 9; }\n"
        "void point_view(void) { g_3DA0.x = 1; g_3DA0.y = 2; }\n"
        "void lowered_point_view(void) { SIM_GRAPHICS_SOURCE_g_3DA0.x = 3; SIM_GRAPHICS_SOURCE_g_3DA0.y = 4; }\n"
        '/* g_3DB2 stays documentation */ const char *s = "g_3DB2";\n'
        "void member(void) { owner.g_3DB4 = 350; owner->g_3DA0 = 2; owner.g_3DA0.x = 3; }\n"
    )
    output, removed = convert(sample)
    assert removed == ("g_3DB4", "g_3DE0", "g_9134", "f_1B4E_0228")
    assert "SIM_GRAPHICS_SOURCE_g_3DB4 = 480" in output
    assert "SIM_GRAPHICS_SOURCE_g_3DE0 = 9" in output
    assert "SIM_GRAPHICS_SOURCE_g_3DA0 = 1" in output
    assert "SIM_GRAPHICS_SOURCE_g_3DA2 = 2" in output
    assert "SIM_GRAPHICS_SOURCE_g_3DA0 = 3" in output
    assert "SIM_GRAPHICS_SOURCE_g_3DA2 = 4" in output
    assert "extern uint8_t g_9134" not in output
    assert "extern void far f_1B4E_0228" not in output
    assert '/* g_3DB2 stays documentation */' in output
    assert '"g_3DB2"' in output
    assert "owner.g_3DB4 = 350" in output and "owner->g_3DA0 = 2" in output
    assert "owner.g_3DA0.x = 3" in output

    root = Path(__file__).resolve().parents[3]
    real_source = (root / "src/S20/m39F1.c").read_text(encoding="utf-8")
    converted_source, real_removed = convert(real_source)
    for symbol in ("g_3DB2", "g_3DB4", "g_9134", "f_1B4E_0228"):
        assert symbol in real_removed
    assert "SIM_GRAPHICS_SOURCE_g_3DB2" in converted_source
    assert "SIM_GRAPHICS_SOURCE_g_3DB4" in converted_source
    assert "extern void (far * near g_9134)" not in converted_source
    assert "extern void far f_1B4E_0228" not in converted_source

    real_source = (root / "src/S24/m39C7.c").read_text(encoding="utf-8")
    converted_source, real_removed = convert(real_source)
    assert "g_9128" in real_removed
    assert "extern void (far * near g_9128)" not in converted_source

    source_tus = sorted((root / "src").rglob("*.c"))
    assert len(source_tus) == 98, f"expected 98 source C TUs, got {len(source_tus)}"
    removed_total = 0
    for source_path in source_tus:
        source_text = source_path.read_text(encoding="utf-8")
        converted_text, removed_symbols = convert(source_text)
        removed_total += len(removed_symbols)
        for line in converted_text.splitlines():
            if not line.lstrip().startswith("extern"):
                continue
            if any(re.search(rf"\b{re.escape(name)}\b", line) for name in DECL_NAMES):
                raise AssertionError(f"selected graphics extern remains in {source_path}: {line}")
    for source_name in ("src/root/m208F.c", "src/root/m22BF.c", "src/root/m24AB.c"):
        source_text = (root / source_name).read_text(encoding="utf-8")
        converted_text, _ = convert(source_text)
        if "SIM_GRAPHICS_SOURCE_g_3DA0." in converted_text or "SIM_GRAPHICS_SOURCE_g_3DA2." in converted_text:
            raise AssertionError(f"unlowered graphics Point member in {source_name}")
        if "g_3DA0.x" in converted_text or "g_3DA0.y" in converted_text:
            raise AssertionError(f"unconverted graphics Point view in {source_name}")
    print(f"source C TU controls scanned: {len(source_tus)}; selected externs removed: {removed_total}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", nargs="?", type=Path)
    parser.add_argument("output", nargs="?", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        print("graphics source converter: PASS")
        return 0
    if args.input is None or args.output is None:
        parser.error("input and output are required unless --self-test is used")
    source = args.input.read_text(encoding="utf-8")
    converted, removed = convert(source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(converted, encoding="utf-8")
    print(f"removed selected externs: {', '.join(removed) if removed else '(none)'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
