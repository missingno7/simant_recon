from __future__ import annotations
import hashlib
import re
SOURCE_PATH = 'src/window/menu_helpers.c'
HEADER = '#include "portable/whole_program/platform/m1b73_queue_source.h"\n'
QUEUE_SLOTS = {'fd_5071_0728': 3, 'fd_5071_03C4': 2, 'fd_5071_0060': 1}
QUEUE_OPS = {'hotbox_remove_id': 'extern\\s+void\\s+far\\s+hotbox_remove_id\\(int\\s+ticks,\\s*char\\s+far\\s*\\*slot\\);', 'hotbox_prepend': 'extern\\s+void\\s+far\\s+hotbox_prepend\\(struct\\s+Timer\\s+far\\s*\\*t,\\s*char\\s+far\\s*\\*slot\\);', 'hotbox_append': 'extern\\s+void\\s+far\\s+hotbox_append\\(struct\\s+Timer\\s+far\\s*\\*t,\\s*char\\s+far\\s*\\*slot\\);', 'hotbox_contains_pointer': 'extern\\s+void\\s+far\\s+hotbox_contains_pointer\\(int\\s+ticks,\\s*char\\s+far\\s*\\*slot\\);', 'hotbox_get_rect': 'extern\\s+int\\s+far\\s+hotbox_get_rect\\(int\\s+id,\\s*char\\s+far\\s*\\*slot,\\s*struct\\s+Rect\\s+far\\s*\\*out\\);'}

def _sha(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def _identifier_spans(source: str):
    """Yield identifier spans from C tokens, skipping comments and literals."""
    i = 0
    n = len(source)
    while i < n:
        ch = source[i]
        if ch == '"' or ch == "'":
            quote = ch
            i += 1
            while i < n:
                if source[i] == '\\':
                    i += 2
                elif source[i] == quote:
                    i += 1
                    break
                else:
                    i += 1
            continue
        if ch == '/' and i + 1 < n and (source[i + 1] == '/'):
            newline = source.find('\n', i + 2)
            i = n if newline < 0 else newline + 1
            continue
        if ch == '/' and i + 1 < n and (source[i + 1] == '*'):
            end = source.find('*/', i + 2)
            i = n if end < 0 else end + 2
            continue
        if ch == '_' or ch.isalpha():
            start = i
            i += 1
            while i < n and (source[i] == '_' or source[i].isalnum()):
                i += 1
            yield (start, i, source[start:i])
            continue
        i += 1

def _replace_identifier(source: str, old: str, new: str) -> tuple[str, int]:
    spans = [(start, end) for (start, end, token) in _identifier_spans(source) if token == old]
    for (start, end) in reversed(spans):
        source = source[:start] + new + source[end:]
    return (source, len(spans))

def _has_identifier(source: str, name: str) -> bool:
    return any((token == name for (_, _, token) in _identifier_spans(source)))

def adapt(source: str, module_path: str=SOURCE_PATH) -> tuple[str, dict[str, object]]:
    if module_path != SOURCE_PATH:
        raise ValueError(f'm1B73 queue adapter does not accept {module_path!r}')
    digest = _sha(source)
    changes: dict[str, object] = {}
    declarations = {'fd_5071_0728': '(?m)^extern\\s+char\\s+far\\s+fd_5071_0728\\[\\s*\\]\\s*;\\s*\\n', 'fd_5071_03C4': '(?m)^extern\\s+char\\s+far\\s+fd_5071_03C4\\[\\s*\\]\\s*;\\s*\\n', 'fd_5071_0060': '(?m)^extern\\s+char\\s+far\\s+fd_5071_0060\\[\\s*\\]\\s*;\\s*\\n'}
    for (name, pattern) in declarations.items():
        (source, count) = re.subn(pattern, '', source, count=1)
        if count != 1:
            raise ValueError(f'expected one source extern declaration for {name}')
        (source, uses) = _replace_identifier(source, name, f'portable_m1b73_queue_slot({QUEUE_SLOTS[name]})')
        changes[f'{name}_argument_views'] = uses
        if uses == 0 or _has_identifier(source, name):
            raise ValueError(f'unconverted source queue symbol {name}')
    for (name, pattern) in QUEUE_OPS.items():
        (source, count) = re.subn(f'(?m)^{pattern}\\s*\\n', '', source, count=1)
        if count != 1:
            raise ValueError(f'expected one source {name} prototype')
        changes[f'{name}_prototype'] = 'typed native queue view; source argument order preserved'
    byte_decl = '(?m)^extern\\s+unsigned\\s+char\\s+near\\s+mouse_button_state\\s*;\\s*\\n'
    (source, byte_count) = re.subn(byte_decl, '', source, count=1)
    if byte_count != 1:
        raise ValueError('expected one byte-view mouse_button_state declaration')
    (source, low_reads) = _replace_identifier(source, 'mouse_button_state', 'portable_m1b73_g9120_low_byte()')
    if low_reads != 1:
        raise ValueError(f'expected one C low-byte status read, found {low_reads}')
    changes['mouse_button_state'] = "one C byte read through the canonical uint16 owner's low-byte accessor"
    for name in ('mouse_x_pixels', 'mouse_y_pixels'):
        declaration = f'(?m)^extern\\s+int\\s+near\\s+{name}\\s*;\\s*\\n'
        (source, count) = re.subn(declaration, '', source, count=1)
        if count != 1:
            raise ValueError(f'expected one {name} declaration to share typed owner')
        if not re.search(f'\\b{name}\\b', source):
            raise ValueError(f'source coordinate owner {name} unexpectedly unused')
        changes[name] = 'uses the canonical int16_t mouse-state declaration'
    if HEADER.strip() not in source:
        source = HEADER + source
    for unresolved in [*QUEUE_SLOTS, 'extern unsigned char near mouse_button_state']:
        if _has_identifier(source, unresolved):
            raise ValueError(f'source adapter left unresolved declaration/token: {unresolved}')
    return (source, {'kind': 'SOURCE_M1B73_QUEUE_TYPED_VIEWS', 'source_path': SOURCE_PATH, 'timer_adapted_input_sha256': digest, 'output_sha256': _sha(source), 'queue_source_slots': {'Queue0': {'slot_index': 0, 'original_pointer_target': 'Queue0', 'native_capacity': 4, 'record_count': 5}, 'fd_5071_0060': {'slot_index': 1, 'native_capacity': 47, 'record_count': 48}, 'fd_5071_03C4': {'slot_index': 2, 'native_capacity': 47, 'record_count': 48}, 'fd_5071_0728': {'slot_index': 3, 'native_capacity': 9, 'record_count': 10}}, 'queue_operation_abi': {'hotbox_remove_id': 'source stack words: ticks, far slot; native typed int16_t + PortableM1B73Queue*', 'hotbox_prepend': 'source stack words: far Timer*, far slot; native Timer* + PortableM1B73Queue*', 'hotbox_append': 'source stack words: far Timer*, far slot; native Timer* + PortableM1B73Queue*', 'hotbox_contains_pointer': 'source stack words: ticks, far slot; declared void in C although ASM returns AX; caller ignores the result', 'hotbox_get_rect': "native typed ID + queue view + Rect*; canonical wrapper forwards its typed Rect output and int result unchanged", 'mouse_set_position': 'two signed words x/y; no queue pointer', 'input_enqueue_event_args': 'variadic callsites pass four or five words while ASM reads five words after the return address; remains explicitly outside this adapter'}, 'changes': changes, 'function_order_preserved': True, 'owner_model': 'all slot expressions are borrowed selectors into portable_m1b73_queue_set; no duplicate queue bytes or mouse_button_state/mouse_x_pixels/mouse_y_pixels globals'})
