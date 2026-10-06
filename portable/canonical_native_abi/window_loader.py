from __future__ import annotations
from dataclasses import dataclass, field
import re
from .lexical import mask_literals
HEADER = '#include "portable/whole_program/window_source_globals.h"\n'
RECT_HEADER = '#include "portable/whole_program/window_source_rects.h"\n'


def _rewrite_code_identifier(source: str, name: str, replacement: str) -> str:
    mask = mask_literals(source)
    matches = list(re.finditer('\\b' + re.escape(name) + '\\b', mask))
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
    (text, counts['signed_profile_declaration']) = re.subn('extern\\s+char\\s+(?:(?:far|near)\\s+)?g_5A97\\s*;', '', text)
    (text, counts['unsigned_profile_declaration']) = re.subn('extern\\s+(?:unsigned\\s+char|uint8_t)\\s+(?:(?:far|near)\\s+)?g_5A97\\s*;', '', text)
    if counts['unsigned_profile_declaration']:
        code = mask_literals(text)
        if re.search('(?:&\\s*g_5A97|\\bg_5A97\\s*(?:\\+\\+|--|[+\\-*/%&|^]=|=(?!=))|(?:\\+\\+|--)\\s*g_5A97)', code):
            unresolved.append('unsigned g_5A97 consumer has a non-read use')
        else:
            text = _rewrite_code_identifier(text, 'g_5A97', '((uint8_t)g_5A97)')
    for symbol in ('win_numOfWindows', 'win_numOfColors', 'win_numOfGroups'):
        (text, counts['shared_' + symbol]) = re.subn('extern\\s+(?:int16_t|int)\\s+(?:(?:far|near)\\s+)?' + symbol + '\\s*;', '', text)
    (text, counts['typed_hook_declaration']) = re.subn('extern\\s+void\\s*\\(\\s*(?:(?:far|near)\\s+)?\\*\\s*(?:(?:far|near)\\s+)?win_drawHooks\\s*\\[\\s*\\]\\s*\\)\\s*\\(\\s*(?:int16_t|int)\\s+phase\\s*\\)\\s*;', 'extern SimWindowSourceDrawHook win_drawHooks[SIM_WINDOW_SOURCE_SLOT_COUNT];', text)
    (text, counts['typed_offsets_declaration']) = re.subn('extern\\s+struct\\s+Rect\\s+(?:(?:far|near)\\s+)?win_offsets\\s*\\[\\s*\\]\\s*;', 'extern struct Rect win_offsets[SIM_WINDOW_SOURCE_SLOT_COUNT];', text)
    if re.search('extern\\s+struct\\s+Rect\\s+(?:far\\s+)?win_offsets\\s*\\[\\s*\\]', text) and (not counts['typed_offsets_declaration']):
        unresolved.append('win_offsets extern uses an unreviewed declaration spelling')
    if counts['typed_offsets_declaration']:
        (text, counts['shared_rect_definition']) = re.subn('struct\\s+Rect\\s*\\{\\s*(?:int16_t|int)\\s+left\\s*;\\s*(?:int16_t|int)\\s+top\\s*;\\s*(?:int16_t|int)\\s+right\\s*;\\s*(?:int16_t|int)\\s+bottom\\s*;\\s*\\}\\s*;', '', text, count=1)
        if counts['shared_rect_definition'] != 1:
            unresolved.append('window_offsets consumer lacked one audited four-word Rect definition')
        if RECT_HEADER not in text:
            text = RECT_HEADER + text
    if any((name in text for name in ('win_drawHooks', 'win_offsets', 'g_5A97', 'win_numOfWindows', 'win_numOfColors', 'win_numOfGroups'))) and HEADER not in text:
        text = HEADER + text
    return ConversionResult(text=text, replacements=counts, unresolved=unresolved)

def adapt(source: str, rel: str) -> ConversionResult:
    """Mechanical shared-global views and DOS copy width for window TUs.

    Call after `convert_window_source` and before the central word-width pass.
    `rel` identifies the loader for its pointer-sized clear and DOS copy width.
    Palette arrays retain ordinary canonical declarations and ownership.
    """
    globals_result = convert_window_global_declarations(source)
    text = globals_result.text
    counts = dict(globals_result.replacements)
    unresolved = list(globals_result.unresolved)
    (text, counts['typed_hook_clear']) = re.subn('sim_window_clear_draw_hooks\\(win_drawHooks,\\s*45\\)', 'sim_window_source_clear_draw_hooks(win_drawHooks, 45)', text)
    if counts['typed_hook_clear'] == 0 and 'win_drawHooks' in text and ('_fmemset(win_drawHooks' in text):
        (text, counts['typed_hook_clear']) = re.subn('_fmemset\\(\\s*win_drawHooks\\s*,\\s*0\\s*,\\s*0xb4\\s*\\)', 'sim_window_source_clear_draw_hooks(win_drawHooks, 45)', text)
    loader_name = rel.replace('\\', '/').rsplit('/', 1)[-1].lower()
    is_loader = loader_name in {'m20e8.c', 'root_m20e8.c'}
    if is_loader:
        (text, counts['dos_color_copy_width']) = re.subn('_fmemcpy\\(win_colors,\\s*\\*h,\\s*win_numOfColors\\s*\\*\\s*6\\s*\\)', '_fmemcpy(win_colors, *h, (uint16_t)(win_numOfColors * 6))', text)
        if counts['typed_hook_clear'] != 1:
            unresolved.append('loader must adapt exactly one source 45-hook clear')
        if counts['typed_offsets_declaration'] != 1 or counts.get('shared_rect_definition', 0) != 1:
            unresolved.append('loader must bind the one 45-entry source Rect table')
        if counts['dos_color_copy_width'] != 1:
            unresolved.append('source color copy width did not retain 16-bit DOS semantics')
    return ConversionResult(text=text, replacements=counts, unresolved=unresolved)
