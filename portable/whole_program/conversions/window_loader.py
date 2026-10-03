"""Strict adaptation for the source-owned window-manager global ABI.

The original `win_LoadAllWindows` body remains responsible for loader order,
resource IDs, source field extraction, copies, purges, and per-window calls.
Only native storage declarations and the dynamic color allocation boundary are
adapted here.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import re


HEADER = '#include "portable/whole_program/window_source_globals.h"\n'
RECT_HEADER = '#include "portable/whole_program/window_source_rects.h"\n'


def _code_mask(source: str) -> str:
    """Return same-length text with comments and C literals blanked."""
    pattern = re.compile(
        r"//[^\r\n]*|/\*.*?\*/|\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*'",
        re.S)
    return pattern.sub(lambda m: "".join("\n" if c == "\n" else " " for c in m.group()),
                       source)


def _rewrite_code_identifier(source: str, name: str, replacement: str) -> str:
    mask = _code_mask(source)
    matches = list(re.finditer(r"\b" + re.escape(name) + r"\b", mask))
    for match in reversed(matches):
        source = source[:match.start()] + replacement + source[match.end():]
    return source


@dataclass
class ConversionResult:
    text: str
    replacements: dict[str, int] = field(default_factory=dict)
    unresolved: list[str] = field(default_factory=list)


def convert_window_global_declarations(source: str) -> ConversionResult:
    """Bind source extern spellings to the native shared global owner."""
    text = source
    counts: dict[str, int] = {}
    unresolved: list[str] = []

    # All source declarations refer to one plain-char profile byte. Explicit
    # unsigned-char consumers receive a value cast at each read site below;
    # the storage symbol itself is never multiply-declared with incompatible C
    # types across translation units.
    text, counts["signed_profile_declaration"] = re.subn(
        r"extern\s+char\s+(?:(?:far|near)\s+)?g_5A97\s*;", "", text)
    text, counts["unsigned_profile_declaration"] = re.subn(
        r"extern\s+(?:unsigned\s+char|uint8_t)\s+(?:(?:far|near)\s+)?g_5A97\s*;",
        "", text)
    if counts["unsigned_profile_declaration"]:
        code = _code_mask(text)
        if re.search(r"(?:&\s*g_5A97|\bg_5A97\s*(?:\+\+|--|[+\-*/%&|^]=|=(?!=))|"
                     r"(?:\+\+|--)\s*g_5A97)", code):
            unresolved.append("unsigned g_5A97 consumer has a non-read use")
        else:
            text = _rewrite_code_identifier(text, "g_5A97", "((uint8_t)g_5A97)")

    for symbol in ("win_numOfWindows", "win_numOfColors", "win_numOfGroups"):
        text, counts["shared_" + symbol] = re.subn(
            r"extern\s+(?:int16_t|int)\s+(?:(?:far|near)\s+)?" + symbol + r"\s*;",
            "", text)

    # Native pointer storage replaces the source's incomplete extern array.
    # Signed bytes preserve the original plain-char table interpretation.
    text, counts["dynamic_color_declaration"] = re.subn(
        r"extern\s+char\s+(?:(?:far|near)\s+)?win_colors\s*\[\s*\]\s*\[\s*6\s*\]\s*;",
        "extern int8_t (*win_colors)[SIM_WINDOW_SOURCE_COLOR_BYTES];",
        text)
    if re.search(r"extern\s+char\s+(?:(?:far|near)\s+)?win_colors\s*\[\s*\]\s*\[\s*\]", text):
        unresolved.append("win_colors has a non-six-byte source declaration")
    if re.search(r"extern\s+char\s+(?:(?:far|near)\s+)?win_colors\s*\[", text) and \
            counts["dynamic_color_declaration"] == 0 and \
            not re.search(r"extern\s+int8_t\s*\(\s*\*\s*win_colors\s*\)", text):
        unresolved.append("win_colors uses an unreviewed source extern shape")

    # Fixed-length native hook table; the callback parameters remain 16-bit.
    text, counts["typed_hook_declaration"] = re.subn(
        r"extern\s+void\s*\(\s*(?:(?:far|near)\s+)?\*\s*"
        r"(?:(?:far|near)\s+)?win_drawHooks\s*\[\s*\]\s*\)\s*"
        r"\(\s*(?:int16_t|int)\s+phase\s*\)\s*;",
        "extern SimWindowSourceDrawHook win_drawHooks[SIM_WINDOW_SOURCE_SLOT_COUNT];",
        text)

    # Window Rect remains its source four-word struct in each consumer TU,
    # while the declared bound now states the actual owner capacity.
    text, counts["typed_offsets_declaration"] = re.subn(
        r"extern\s+struct\s+Rect\s+(?:(?:far|near)\s+)?win_offsets\s*\[\s*\]\s*;",
        "extern struct Rect win_offsets[SIM_WINDOW_SOURCE_SLOT_COUNT];", text)
    if re.search(r"extern\s+struct\s+Rect\s+(?:far\s+)?win_offsets\s*\[\s*\]", text) and not counts["typed_offsets_declaration"]:
        unresolved.append("win_offsets extern uses an unreviewed declaration spelling")
    if counts["typed_offsets_declaration"]:
        # Use one shared native Rect tag for the global table and its source
        # consumers. Only the audited four-signed-word declaration is removed.
        text, counts["shared_rect_definition"] = re.subn(
            r"struct\s+Rect\s*\{\s*(?:int16_t|int)\s+left\s*;\s*"
            r"(?:int16_t|int)\s+top\s*;\s*(?:int16_t|int)\s+right\s*;\s*"
            r"(?:int16_t|int)\s+bottom\s*;\s*\}\s*;",
            "", text, count=1)
        if counts["shared_rect_definition"] != 1:
            unresolved.append("window_offsets consumer lacked one audited four-word Rect definition")
        if RECT_HEADER not in text:
            text = RECT_HEADER + text

    if any(name in text for name in (
            "win_colors", "win_drawHooks", "win_offsets", "g_5A97",
            "win_numOfWindows", "win_numOfColors", "win_numOfGroups")) and HEADER not in text:
        text = HEADER + text
    return ConversionResult(text=text, replacements=counts,
                            unresolved=unresolved)


def adapt(source: str, rel: str) -> ConversionResult:
    """Pre-word conversion hook for source plus window-sidecar converted TUs.

    Call after `convert_window_source` and before the central word-width pass.
    `rel` is retained for the replacement report and to make the loader-only
    resource-allocation boundary explicit; the adapter never edits the central
    generator or source files.
    """
    globals_result = convert_window_global_declarations(source)
    text = globals_result.text
    counts = dict(globals_result.replacements)
    unresolved = list(globals_result.unresolved)

    # The existing windows converter has already changed the fixed DOS memset
    # into this element-based helper. Replace its generic signature with the
    # owner's precise 16-bit callback table API.
    text, counts["typed_hook_clear"] = re.subn(
        r"sim_window_clear_draw_hooks\(win_drawHooks,\s*45\)",
        "sim_window_source_clear_draw_hooks(win_drawHooks, 45)", text)
    if counts["typed_hook_clear"] == 0 and "win_drawHooks" in text and "_fmemset(win_drawHooks" in text:
        text, counts["typed_hook_clear"] = re.subn(
            r"_fmemset\(\s*win_drawHooks\s*,\s*0\s*,\s*0xb4\s*\)",
            "sim_window_source_clear_draw_hooks(win_drawHooks, 45)", text)

    loader_name = rel.replace("\\", "/").rsplit("/", 1)[-1].lower()
    is_loader = loader_name in {"m20e8.c", "root_m20e8.c"}
    if is_loader:
        reserve_call = (
            "    if (!sim_window_source_reserve_colors(win_numOfColors)) {\n"
            '        Punt("window color table allocation failed");\n'
            "        return 0;\n"
            "    }\n")
        text, counts["color_reservation"] = re.subn(
            r"(db_PurgeObject\(0x80,\s*0\);\s*\}\s*\n)"
            r"(\s*h\s*=\s*db_LoadObject\(0x81,\s*0\);)",
            lambda m: m.group(1) + reserve_call + m.group(2), text)
        text, counts["dos_color_copy_width"] = re.subn(
            r"_fmemcpy\(win_colors,\s*\*h,\s*win_numOfColors\s*\*\s*6\s*\)",
            "_fmemcpy(win_colors, *h, (uint16_t)(win_numOfColors * 6))", text)
        if counts["dynamic_color_declaration"] != 1:
            unresolved.append("loader must adapt exactly one source win_colors declaration")
        if counts["typed_hook_clear"] != 1:
            unresolved.append("loader must adapt exactly one source 45-hook clear")
        if counts["typed_offsets_declaration"] != 1 or counts.get("shared_rect_definition", 0) != 1:
            unresolved.append("loader must bind the one 45-entry source Rect table")
        if counts["color_reservation"] != 1:
            unresolved.append("resource-0x80/0x81 color allocation boundary did not match once")
        if counts["dos_color_copy_width"] != 1:
            unresolved.append("source color copy width did not retain 16-bit DOS semantics")
    return ConversionResult(text=text, replacements=counts,
                            unresolved=unresolved)


def convert_window_loader(source: str) -> ConversionResult:
    globals_result = convert_window_global_declarations(source)
    text = globals_result.text
    counts: dict[str, int] = dict(globals_result.replacements)
    unresolved = list(globals_result.unresolved)

    # The earlier pointer conversion handles the source's 0xb4-byte DOS
    # memset. Bind it to this owner's typed 45-entry callback array helper.
    text, counts["typed_hook_clear"] = re.subn(
        r"sim_window_clear_draw_hooks\(win_drawHooks,\s*45\)",
        "sim_window_source_clear_draw_hooks(win_drawHooks, 45)", text)

    # The DOS source `int` is a 16-bit word. Make the copy-byte narrowing
    # explicit after native integer promotion so the call retains that ABI.
    text, counts["dos_color_copy_width"] = re.subn(
        r"_fmemcpy\(win_colors,\s*\*h,\s*win_numOfColors\s*\*\s*6\s*\)",
        "_fmemcpy(win_colors, *h, (uint16_t)(win_numOfColors * 6))", text)

    # Allocate only after resource 0x80 has supplied the color count, and
    # before the original resource 0x81 load/copy. All subsequent source
    # statements remain in their original order.
    reserve_call = (
        "    if (!sim_window_source_reserve_colors(win_numOfColors)) {\n"
        '        Punt("window color table allocation failed");\n'
        "        return 0;\n"
        "    }\n")
    text, counts["color_reservation"] = re.subn(
        r"(\s*db_PurgeObject\(0x80,\s*0\);\s*\}\s*\n)"
        r"(\s*h\s*=\s*db_LoadObject\(0x81,\s*0\);)",
        lambda m: m.group(1) + reserve_call + m.group(2), text)

    residue = re.sub(r"/\*.*?\*/|//[^\r\n]*", "", text, flags=re.S)
    if counts.get("dynamic_color_declaration", 0) != 1:
        unresolved.append("loader's dynamic color table declaration was not adapted exactly once")

    if counts["color_reservation"] != 1:
        counts.setdefault("color_reservation", 0)
        unresolved.append("resource-0x80 to 0x81 color allocation boundary did not match once")
    if "sim_window_clear_draw_hooks(win_drawHooks, 45)" in residue:
        unresolved.append("native hook clear helper was not rebound")
    if counts["dos_color_copy_width"] != 1:
        counts.setdefault("dos_color_copy_width", 0)
        unresolved.append("source color-copy word width was not narrowed exactly once")
    for key, needle in (("typed_hook_declaration", "win_drawHooks"),
                        ("typed_offsets_declaration", "win_offsets")):
        if needle in residue and counts.get(key, 0) != 1:
            unresolved.append("loader source " + needle + " declaration was not converted exactly once")
    if "win_LoadAllWindows" not in residue:
        unresolved.append("expected source win_LoadAllWindows function not found")
    if re.search(r"win_colors\s*\[\s*\]\s*\[\s*6\s*\]", residue):
        unresolved.append("incomplete native color table declaration remains")

    return ConversionResult(text=text, replacements=counts,
                            unresolved=unresolved)
