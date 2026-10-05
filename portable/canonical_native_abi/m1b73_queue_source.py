from __future__ import annotations
import hashlib
import re
SOURCE_PATH = 'src/root/m1FD2.c'
HEADER = '#include "portable/whole_program/platform/m1b73_queue_source.h"\n'
QUEUE_SLOTS = {'fd_5071_0728': 3, 'fd_5071_03C4': 2, 'fd_5071_0060': 1}
QUEUE_OPS = {'f_1B73_0B5B': 'extern\\s+void\\s+far\\s+f_1B73_0B5B\\(int\\s+ticks,\\s*char\\s+far\\s*\\*slot\\);', 'f_1B73_0B00': 'extern\\s+void\\s+far\\s+f_1B73_0B00\\(struct\\s+Timer\\s+far\\s*\\*t,\\s*char\\s+far\\s*\\*slot\\);', 'f_1B73_0AC3': 'extern\\s+void\\s+far\\s+f_1B73_0AC3\\(struct\\s+Timer\\s+far\\s*\\*t,\\s*char\\s+far\\s*\\*slot\\);', 'f_1B73_0BC5': 'extern\\s+void\\s+far\\s+f_1B73_0BC5\\(int\\s+ticks,\\s*char\\s+far\\s*\\*slot\\);', 'f_1B73_0C42': 'extern\\s+void\\s+far\\s+f_1B73_0C42\\(int\\s+a,\\s*char\\s+far\\s*\\*slot,\\s*int\\s+b,\\s*int\\s+c\\);'}

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
    output_wrapper = re.compile('void\\s+far\\s+f_1FD2_04B3\\s*\\(\\s*int\\s+a\\s*,\\s*int\\s+b\\s*,\\s*int\\s+c\\s*\\)\\s*\\{\\s*f_1B73_0C42\\(a,\\s*portable_m1b73_queue_slot\\(2\\),\\s*b,\\s*c\\);\\s*\\}')
    (source, wrapper_count) = output_wrapper.subn('int far f_1FD2_04B3(int a, PortableM1B73Rect *r)\n{\n    return f_1B73_0C42((int16_t)a, portable_m1b73_queue_slot(2), r);\n}', source, count=1)
    if wrapper_count != 1:
        raise ValueError('expected the original f_1FD2_04B3 split-pointer wrapper')
    changes['f_1FD2_04B3'] = 'native source callsite passes one Rect pointer; wrapper forwards it to typed 0C42, and returns the ASM lookup success value consumed by S26'
    byte_decl = '(?m)^extern\\s+unsigned\\s+char\\s+near\\s+g_9120\\s*;\\s*\\n'
    (source, byte_count) = re.subn(byte_decl, '', source, count=1)
    if byte_count != 1:
        raise ValueError('expected one byte-view g_9120 declaration')
    (source, low_reads) = _replace_identifier(source, 'g_9120', 'portable_m1b73_g9120_low_byte()')
    if low_reads != 1:
        raise ValueError(f'expected one C low-byte status read, found {low_reads}')
    changes['g_9120'] = "one C byte read through the canonical uint16 owner's low-byte accessor"
    for name in ('g_9122', 'g_9124'):
        declaration = f'(?m)^extern\\s+int\\s+near\\s+{name}\\s*;\\s*\\n'
        (source, count) = re.subn(declaration, '', source, count=1)
        if count != 1:
            raise ValueError(f'expected one {name} declaration to share typed owner')
        if not re.search(f'\\b{name}\\b', source):
            raise ValueError(f'source coordinate owner {name} unexpectedly unused')
        changes[name] = 'uses the canonical int16_t mouse-state declaration'
    if HEADER.strip() not in source:
        source = HEADER + source
    for unresolved in [*QUEUE_SLOTS, 'extern unsigned char near g_9120']:
        if _has_identifier(source, unresolved):
            raise ValueError(f'source adapter left unresolved declaration/token: {unresolved}')
    return (source, {'kind': 'SOURCE_M1B73_QUEUE_TYPED_VIEWS', 'source_path': SOURCE_PATH, 'timer_adapted_input_sha256': digest, 'output_sha256': _sha(source), 'queue_source_slots': {'Queue0': {'slot_index': 0, 'original_pointer_target': 'Queue0', 'native_capacity': 4, 'record_count': 5}, 'fd_5071_0060': {'slot_index': 1, 'native_capacity': 47, 'record_count': 48}, 'fd_5071_03C4': {'slot_index': 2, 'native_capacity': 47, 'record_count': 48}, 'fd_5071_0728': {'slot_index': 3, 'native_capacity': 9, 'record_count': 10}}, 'queue_operation_abi': {'f_1B73_0B5B': 'source stack words: ticks, far slot; native typed int16_t + PortableM1B73Queue*', 'f_1B73_0B00': 'source stack words: far Timer*, far slot; native Timer* + PortableM1B73Queue*', 'f_1B73_0AC3': 'source stack words: far Timer*, far slot; native Timer* + PortableM1B73Queue*', 'f_1B73_0BC5': 'source stack words: ticks, far slot; declared void in C although ASM returns AX; caller ignores the result', 'f_1B73_0C42': "native typed ID + queue view + Rect*; source wrapper normalizes historical offset/segment pair into the caller's one native pointer", 'f_1B73_09E9': 'two signed words x/y; no queue pointer', 'f_1B73_030F': 'variadic callsites pass four or five words while ASM reads five words after the return address; remains explicitly outside this adapter'}, 'changes': changes, 'function_order_preserved': True, 'owner_model': 'all slot expressions are borrowed selectors into portable_m1b73_queue_set; no duplicate queue bytes or g_9120/g_9122/g_9124 globals'})
