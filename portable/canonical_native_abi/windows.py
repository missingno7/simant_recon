from __future__ import annotations
from dataclasses import dataclass, field
import re
REGISTRY = '&sim_window_ref_registry'

@dataclass
class ConversionResult:
    text: str
    replacements: dict[str, int] = field(default_factory=dict)
    unresolved: list[str] = field(default_factory=list)

def _replace(text: str, key: str, pattern: str, repl, flags: int=0) -> tuple[str, int]:
    (updated, count) = re.subn(pattern, repl, text, flags=flags)
    return (updated, count)

def convert_window_source(source: str, registry: str=REGISTRY) -> ConversionResult:
    """Convert audited root-window casts/fields to byte-backed sidecar APIs.

    The source `RepointObjects` loop stays present and ordered; only its
    four-byte destination table lvalue changes to the host sidecar table.
    """
    text = source
    counts: dict[str, int] = {}
    win_object_type = 'char'
    win_decl = re.search('struct\\s+Win\\s*\\{(?P<body>.*?)\\};', source, re.S)
    if win_decl:
        member = re.search('(?P<type>struct\\s+[A-Za-z_]\\w*|char)\\s+far\\s*\\*\\s*objs\\s*\\[\\s*1\\s*\\]', win_decl.group('body'))
        if member:
            win_object_type = member.group('type')
    header = '#include "portable/whole_program/window_refs.h"\n'
    if 'sim_window_ref_registry_' in text or 'struct Rect' in text or 'struct Win' in text:
        if header not in text:
            text = header + text
        if registry == REGISTRY and 'extern SimWindowRefRegistry sim_window_ref_registry;' not in text:
            text = text.replace(header, header + 'extern SimWindowRefRegistry sim_window_ref_registry;\n', 1)
    (text, counts['rect_int16_view']) = _replace(text, 'rect_int16_view', 'struct Rect\\s*\\{\\s*int left;\\s*int top;\\s*int right;\\s*int bottom;\\s*\\};', 'struct Rect { int16_t left; int16_t top; int16_t right; int16_t bottom; };', re.S)
    (text, counts['window_count_flags_int16']) = _replace(text, 'window_count_flags_int16', '(struct Win\\s*\\{.*?)(\\bint count;)(.*?\\bint flags;.*?\\};)', lambda m: m.group(1) + 'int16_t count;' + m.group(3).replace('int flags;', 'int16_t flags;', 1), re.S)
    (text, counts['window_wire_table_member']) = _replace(text, 'window_wire_table_member', '(?:char|struct\\s+[A-Za-z_]\\w*)\\s+far\\s*\\*\\s*objs\\s*\\[\\s*1\\s*\\]\\s*;', 'uint8_t object_table_wire[4];')
    (text, counts['object_wire_handle_members']) = _replace(text, 'object_wire_handle_members', 'char\\s+far\\s*\\*\\s*far\\s*\\*\\s*(h2a|h34)\\s*;', lambda m: 'uint8_t ' + m.group(1) + '_wire[4];')
    index_guard = '    int window_index;\n\n    window_index = (int)((uint16_t)win >> 8);\n    if (window_index >= 45) {\n        Punt("window sidecar index out of range");\n        return;\n    }\n'
    bind_line = '    if (sim_window_ref_registry_repoint_handle_signed(' + registry + ', (uint16_t)window_index, win_handles[window_index],\n            (int64_t)f_171C_1C1C(win_handles[window_index])) !=\n        SIM_WINDOW_REFS_OK) {\n        Punt("window object sidecar bind failed");\n        return;\n    }\n'
    (text, counts['repoint_owner_bind']) = _replace(text, 'repoint_owner_bind', '(void\\s+_fastcall\\s+RepointObjects\\s*\\(\\s*int\\s+win\\s*\\)\\s*\\{\\s*char\\s+far\\s*\\*w;\\s*int\\s+n;\\s*int\\s+i;\\s*char\\s+far\\s*\\*p;\\s*)(w\\s*=\\s*f_2505_0006\\(win\\);)', lambda m: m.group(1) + index_guard + m.group(2) + '\n' + bind_line, re.S)
    if counts['repoint_owner_bind']:
        decl = 'extern long far f_171C_1C1C(char far * far *handle);\n'
        if decl not in text:
            text = decl + text
    (text, counts['repoint_table_lvalue']) = _replace(text, 'repoint_table_lvalue', '\\(\\(char\\s+far\\s*\\*\\s*far\\s*\\*\\)\\s*\\(\\s*w\\s*\\+\\s*0x2c\\s*\\)\\s*\\)\\s*\\[\\s*i\\s*\\]\\s*=\\s*p\\s*;', 'sim_window_ref_registry_objects_for_buffer(' + registry + ', (char *)w)[i] = p;')
    (text, counts['window_struct_table_read']) = _replace(text, 'window_struct_table_read', '\\b(?P<window>[A-Za-z_]\\w*)\\s*->\\s*objs\\s*\\[\\s*(?P<index>[^\\]]+)\\s*\\]', lambda m: '((' + win_object_type + ' *)sim_window_ref_registry_objects_for_buffer(' + registry + ', (char *)' + m.group('window') + ')[' + m.group('index') + '])')
    table_item = re.compile('\\(\\(\\s*(?P<type>(?:unsigned\\s+char|char|int|struct\\s+[A-Za-z_]\\w*))\\s+far\\s*\\*\\s*far\\s*\\*\\s*\\)\\s*\\(\\s*(?P<base>(?:[A-Za-z_]\\w*|[A-Za-z_]\\w*\\([^()]*\\)))\\s*\\+\\s*0x2c\\s*\\)\\s*\\)\\s*\\[\\s*(?P<index>[^\\]]+)\\s*\\]')

    def replace_item(match: re.Match[str]) -> str:
        return '((' + match.group('type') + ' *)sim_window_ref_registry_objects_for_buffer(' + registry + ', (char *)' + match.group('base') + ')[' + match.group('index') + '])'
    (text, counts['wire_table_subscript']) = table_item.subn(replace_item, text)
    first_item = re.compile('\\(\\s*\\*\\s*\\(\\s*(?P<type>char|unsigned\\s+char)\\s+far\\s*\\*\\s*far\\s*\\*\\s*\\)\\s*\\(\\s*(?P<base>[A-Za-z_]\\w*)\\s*\\+\\s*0x2c\\s*\\)\\s*\\)\\s*\\[\\s*(?P<index>[^\\]]+)\\s*\\]')
    (text, counts['wire_first_object_bytes']) = first_item.subn(lambda m: 'sim_window_ref_registry_objects_for_buffer(' + registry + ', (char *)' + m.group('base') + ')[0][' + m.group('index') + ']', text)
    grouped_first_item = re.compile('\\(\\s*\\*\\s*\\(\\s*\\(\\s*(?P<type>char|unsigned\\s+char)\\s+far\\s*\\*\\s*far\\s*\\*\\s*\\)\\s*\\(\\s*(?P<base>[A-Za-z_]\\w*)\\s*\\+\\s*0x2c\\s*\\)\\s*\\)\\s*\\)\\s*\\[\\s*(?P<index>[^\\]]+)\\s*\\]')
    (text, grouped_count) = grouped_first_item.subn(lambda m: 'sim_window_ref_registry_objects_for_buffer(' + registry + ', (char *)' + m.group('base') + ')[0][' + m.group('index') + ']', text)
    counts['wire_first_object_bytes'] += grouped_count
    (text, counts['object_handle_addresses']) = _replace(text, 'object_handle_addresses', '&\\s*(?P<object>[A-Za-z_]\\w*)\\s*->\\s*(?P<field>h2a|h34)\\b', lambda m: 'sim_window_ref_registry_handle_slot_for_object(' + registry + ', (char *)' + m.group('object') + ', 0x' + ('2a' if m.group('field') == 'h2a' else '34') + ')')
    (text, counts['object_handle_dereferences']) = _replace(text, 'object_handle_dereferences', '\\*\\s*\\(\\s*char\\s+far\\s*\\*\\s*far\\s*\\*\\s*far\\s*\\*\\s*\\)\\s*\\(\\s*(?P<object>[A-Za-z_]\\w*)\\s*\\+\\s*0x(?P<offset>2a|34)\\s*\\)', lambda m: '*sim_window_ref_registry_handle_slot_for_object(' + registry + ', (char *)' + m.group('object') + ', 0x' + m.group('offset') + ')')
    (text, counts['object_data_word_handle_dereferences']) = _replace(text, 'object_data_word_handle_dereferences', '\\*\\s*\\(\\s*char\\s+far\\s*\\*\\s*far\\s*\\*\\s*far\\s*\\*\\s*\\)\\s*&\\s*(?P<object>[A-Za-z_]\\w*)\\s*->\\s*data\\s*\\[\\s*2\\s*\\]', lambda m: '*sim_window_ref_registry_handle_slot_for_object(' + registry + ', (char *)' + m.group('object') + ', 0x2a)')
    (text, counts['source_memset_handle_reset']) = _replace(text, 'source_memset_handle_reset', '_fmemset\\(\\s*(?P<object>[A-Za-z_]\\w*)\\s*\\+\\s*0x2a\\s*,\\s*0\\s*,\\s*14\\s*\\)', lambda m: 'if (sim_window_ref_registry_clear_runtime_for_object(' + registry + ', (char *)' + m.group('object') + ', 0x2a, 14) != SIM_WINDOW_REFS_OK)\n            { Punt("window type-4 runtime clear failed"); return; }')
    (text, counts['source_pointer_zero_reset']) = _replace(text, 'source_pointer_zero_reset', '\\*\\s*\\(\\s*char\\s+far\\s*\\*\\s*far\\s*\\*\\s*\\)\\s*\\(\\s*(?P<object>[A-Za-z_]\\w*)\\s*\\+\\s*0x2a\\s*\\)\\s*=\\s*0\\s*;', lambda m: 'if (sim_window_ref_registry_clear_runtime_for_object(' + registry + ', (char *)' + m.group('object') + ', 0x2a, 4) != SIM_WINDOW_REFS_OK)\n                { Punt("window text Handle clear failed"); return; }')
    (text, counts['unload_registry_detach']) = _replace(text, 'unload_registry_detach', '(win_offsets\\[n\\]\\s*=\\s*[^;]+;)', lambda m: m.group(1) + '\n                sim_window_ref_registry_detach(' + registry + ', (uint16_t)n);')
    (text, counts['unresolved_handle_guard']) = _replace(text, 'unresolved_handle_guard', '\\s+if\\s*\\(\\*p\\)', lambda _m: '\n                    if (p == NULL)\n                        { Punt("unresolved serialized window Handle"); return; }\n                    if (*p)')
    (text, counts['draw_hooks_native_clear']) = _replace(text, 'draw_hooks_native_clear', '_fmemset\\(\\s*win_drawHooks\\s*,\\s*0\\s*,\\s*0xb4\\s*\\)\\s*;', 'sim_window_clear_draw_hooks(win_drawHooks, 45);')
    (text, counts['source_count_word']) = _replace(text, 'source_count_word', '\\*\\s*\\(\\s*int\\s+far\\s*\\*\\s*\\)\\s*\\(\\s*w\\s*\\+\\s*0xc\\s*\\)', 'sim_window_wire_read_i16(w, 0x0c)')
    (text, counts['source_size_word']) = _replace(text, 'source_size_word', '\\*\\s*\\(\\s*int\\s+far\\s*\\*\\s*\\)\\s*\\(\\s*p\\s*\\+\\s*0x22\\s*\\)', 'sim_window_wire_read_i16(p, 0x22)')
    assertions = []
    if counts['rect_int16_view']:
        assertions.append('_Static_assert(sizeof(struct Rect) == 8, "DOS Rect width");')
    if counts['window_wire_table_member']:
        assertions.extend(['_Static_assert(offsetof(struct Win, count) == 0x0c, "Win count offset");', '_Static_assert(offsetof(struct Win, flags) == 0x1c, "Win flags offset");', '_Static_assert(offsetof(struct Win, object_table_wire) == 0x2c, "Win table offset");', '_Static_assert(sizeof(struct Win) == 0x30, "Win fixed header width");'])
    if counts['object_wire_handle_members']:
        assertions.extend(['_Static_assert(offsetof(struct Obj, type) == 0x21, "Obj type offset");', '_Static_assert(offsetof(struct Obj, h2a_wire) == 0x2a, "Obj h2a offset");', '_Static_assert(offsetof(struct Obj, h34_wire) == 0x34, "Obj h34 offset");', '_Static_assert(sizeof(struct Obj) == 0x38, "Obj fixed width");'])
    if counts['object_data_word_handle_dereferences']:
        assertions.append('_Static_assert(offsetof(struct WinObj, data) + 2 * sizeof(((struct WinObj *)0)->data[0]) == 0x2a, "WinObj data[2] Handle offset");')
    if assertions:
        text += '\n/* Native layout guards for the source byte offsets. */\n' + '\n'.join(assertions) + '\n'
    unresolved = []
    text_without_comments = re.sub('/\\*.*?\\*/|//[^\\r\\n]*', '', text, flags=re.S)
    if re.search('\\(\\s*(?:char|unsigned char|struct\\s+\\w+|int)\\s+far\\s*\\*\\s*far\\s*\\*\\s*\\)\\s*\\([^)]*\\+\\s*0x2c', text_without_comments):
        unresolved.append('raw far-pointer table cast at +0x2c')
    if re.search('(?:->|\\.)\\s*(?:h2a|h34)\\b', text_without_comments):
        unresolved.append('unconverted Obj Handle member reference')
    if re.search('\\(\\s*char\\s+far\\s*\\*\\s*far\\s*\\*\\s*far\\s*\\*\\s*\\)\\s*&\\s*\\w+\\s*->\\s*data', text_without_comments):
        unresolved.append('unconverted WinObj word-backed Handle read')
    if re.search('\\b(?:w|window)\\s*->\\s*objs\\b', text_without_comments):
        unresolved.append('unconverted native Obj pointer-table member')
    if re.search('_fmemset\\(\\s*win_drawHooks\\s*,\\s*0\\s*,\\s*0xb4', text_without_comments):
        unresolved.append('fixed DOS-byte clear remains on native draw-hook table')
    if re.search('\\*\\s*\\(\\s*int\\s+far\\s*\\*\\s*\\)\\s*\\(\\s*(?:w|p)\\s*\\+\\s*0x(?:c|22)', text_without_comments):
        unresolved.append('unconverted 16-bit wire scalar read')
    source_without_comments = re.sub('/\\*.*?\\*/|//[^\\r\\n]*', '', source, flags=re.S)
    has_repoint_definition = bool(re.search('\\bRepointObjects\\s*\\([^;]*\\)\\s*\\{', source_without_comments))
    if has_repoint_definition:
        if counts['repoint_owner_bind'] != 1:
            unresolved.append('RepointObjects source owner bind insertion did not match once')
        if counts['repoint_table_lvalue'] != 1:
            unresolved.append('RepointObjects source pointer-table assignment was not translated once')
        repoint_body = re.search('\\bRepointObjects\\s*\\([^;]*\\)\\s*\\{(?P<body>.*?)\\n\\}', text_without_comments, re.S)
        if repoint_body and re.search('\\*\\s*\\(\\s*int\\s+far\\s*\\*', repoint_body.group('body')):
            unresolved.append('unconverted RepointObjects scalar wire load')
        if counts['source_size_word'] == 0:
            unresolved.append('RepointObjects signed object-size advance was not translated')
    return ConversionResult(text=text, replacements=counts, unresolved=unresolved)
