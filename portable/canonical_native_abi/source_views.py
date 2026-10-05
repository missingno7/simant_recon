import re
from . import tokenizer as csrc
from . import scalar
RUNTIME_NAMES = {n: 'dos_' + n for n in ('open', 'read', 'write', 'lseek', 'close', 'access', 'chdir', 'getcwd', 'remove', 'stricmp', 'fopen', 'fread', 'fclose')}
RUNTIME_NAMES.update({'errno': 'dos_errno', 'malloc': 'dos_malloc', 'free': 'dos_free', '_ffree': 'dos_free', '_frealloc': 'dos_realloc', 'FILE': 'DosFileStream'})
TRIVIA = {'ws', 'nl', 'cmt', 'pp', 'asm'}

def rename(text, mapping):
    edits = [(t.s, t.e, mapping[t.text]) for t in csrc.tokenize(text) if t.kind == 'id' and t.text in mapping]
    for (lo, hi, new) in reversed(edits):
        text = text[:lo] + new + text[hi:]
    return text

def top_level_statements(text):
    """Whole declaration spans, excluding function definitions."""
    result = []
    depth = 0
    start = 0
    function = False
    sig = []
    for t in csrc.tokenize(text):
        if t.kind in TRIVIA:
            continue
        if t.text == '{' and depth == 0:
            function = bool(sig and sig[-1] == ')' and ('=' not in sig) and ('typedef' not in sig))
        if t.text == '{':
            depth += 1
        elif t.text == '}':
            depth -= 1
            if depth == 0 and function:
                start = t.e
                sig = []
                function = False
        elif t.text == ';' and depth == 0:
            result.append((start, t.e))
            start = t.e
            sig = []
        if depth == 0:
            sig.append(t.text)
    return result


def discard_callback_declarations(text, names):
    for name in names:
        text = re.sub('(?m)^\\s*(?:extern\\s+)?\\w+Callback\\s+' + re.escape(name) + '\\s*;\\s*\\n', '', text)
        text = re.sub('(?ms)^\\s*extern\\s+[^;\\n]+\\(\\s*\\*\\s*' + re.escape(name) + '\\s*\\)\\s*\\([^;]*\\)\\s*;\\s*\\n', '', text)
    for (lo, hi) in reversed(top_level_statements(text)):
        part = text[lo:hi]
        ts = csrc.tokenize(part)
        initializer = next((t.s for t in ts if t.text == '='), len(part))
        ids = {t.text for t in ts if t.kind == 'id' and t.s < initializer}
        if not ids & names or 'typedef' in ids:
            continue
        first = next((t for t in ts if t.kind not in TRIVIA))
        text = text[:lo] + part[:first.s] + text[hi:]
    return text

def menu_native_memory(text, rel):
    if rel == 'src/S17/m384C.c':
        text = text.replace('g_6054 = portable_menu_source_record_tables(&g_menu_view);', 'g_6054 = (char ***)&g_menu_view.titles;')
    if rel == 'src/root/m1FD2.c':
        for name in ('fd_50F6_46A8', 'fd_50F6_46BC'):
            (text, n) = re.subn('extern\\s+int16_t\\s+' + name + '\\s*\\[\\s*\\]\\s*;', 'extern int16_t *' + name + ';', text)
            if n != 1:
                raise ValueError('canonical root menu view declaration differs: ' + name)
        marker = '    i = 0;\n    total = 0;\n'
        reserve = '    /* Host memory service for the live title count. The original owner\n     * capacity remains unproved; both views borrow one overlapping arena. */\n    {\n        size_t native_title_count = 0;\n        for (t = g_6054->titles; *t; ++t) ++native_title_count;\n        if (!sim_source_runtime_reserve_menu_titles(native_title_count))\n            return 0;\n    }\n'
        if text.count(marker) != 1:
            raise ValueError('menu title traversal shape differs')
        text = text.replace(marker, reserve + marker)
        text = 'extern int16_t sim_source_runtime_reserve_menu_titles(size_t);\n' + text
    return text


def screen_clip_canonical_views(text, rel):
    if 'g_5A9C' not in {t.text for t in csrc.tokenize(text) if t.kind == 'id'}:
        return text
    if rel == 'src/state/screen-clip-list.c':
        return text
    text = re.sub('extern\\s+(?:struct\\s+Rect\\s+g_5A9C(?:\\s*\\[\\s*2\\s*\\])?|char\\s+g_5A9C\\[\\s*\\])\\s*;', '', text)
    if rel.startswith('src/'):
        text = re.sub('struct\\s+Rect\\s*\\{\\s*int16_t\\s+left;\\s*int16_t\\s+top;\\s*int16_t\\s+right;\\s*int16_t\\s+bottom;\\s*\\};', '', text)
        text = '#include "portable/whole_program/platform/graphics_source_clip.h"\n' + text
        text = re.sub('extern\\s+(?:char|int16_t)\\s*\\*\\s*g_5AAC\\s*;', 'extern struct Rect *g_5AAC;', text)
        if rel == 'src/S10/m35F5.c':
            text = re.sub('\\bchar\\s*\\*\\s*saved\\s*;', 'struct Rect *saved;', text)
        if rel in {'src/root/m21FA.c', 'src/S22/m39C7.c'}:
            text = re.sub('\\bg_5AAC\\s*\\[\\s*1\\s*\\]', 'g_5AAC->top', text)
            text = re.sub('(g_5AAC->top\\s*[!=]=\\s*)0x8000\\b', '\\1(int16_t)0x8000', text)
    edits = [(t.s, t.e) for t in csrc.tokenize(text) if t.kind == 'id' and t.text == 'g_5A9C' and (not text[t.e:].lstrip().startswith('['))]
    for (lo, hi) in reversed(edits):
        text = text[:lo] + 'g_5A9C[0]' + text[hi:]
    text = text.replace('return g_5A9C[0];', 'return (char *)&g_5A9C[0];')
    text = text.replace('f_1E57_0A9C(g_5A9C[0])', 'f_1E57_0A9C((char *)&g_5A9C[0])')
    return text

def callback_views(text, slots, types=None):
    return_types = {}
    for name in slots:
        declaration = re.search('extern\\s+(\\w+)\\s*\\(\\s*\\*\\s*' + re.escape(name) + '\\s*\\)\\s*\\(', text)
        if declaration and declaration.group(1) != 'void':
            return_types[name] = declaration.group(1)
    text = discard_callback_declarations(text, set(slots))
    mappings = {name: f'(*( {types[name]} *)(void *)&driver_callback_table[{slot}])' if types and name in types else f'(({return_types[name]} (*)())driver_callback_table[{slot}])' if name in return_types else f'driver_callback_table[{slot}]' for (name, slot) in slots.items()}
    text = rename(text, mappings)
    if any((name in text for name in ('driver_callback_table[', '&driver_callback_table['))):
        text = 'extern void (*driver_callback_table[25])();\n' + text
    return text

def translate_29d6_port_block(text):
    original = '    _asm {\n        mov dx, port\n        mov ax, freq\n        push ax\n        and ax, 0Fh\n        add ax, reg\n        mov bx, ax\n        pop ax\n        and ax, 3F0h\n        mov cx, 4\n        shr ax, cl\n        mov ah, al\n        mov al, bl\n        out dx, ax\n        xor ax, ax\n        mov ax, reg\n        add ax, 10h\n        add ax, val\n        out dx, al\n    }\n'
    converted = '    {\n        uint16_t reg_word = (uint16_t)(uint8_t)reg;\n        uint8_t high = (uint8_t)((freq & 0x03f0u) >> 4);\n        uint8_t low = (uint8_t)((freq & 0x000fu) + reg_word);\n        dos_audio_host_out16((uint16_t)port, (uint16_t)(((uint16_t)high << 8) | low));\n        f_29F0_002A(port, (char)(reg_word + 0x10u + (uint16_t)val));\n    }\n'
    if text.count(original) != 1:
        raise ValueError('canonical 29D6 inline port block shape changed')
    return '#include "portable/whole_program/platform/audio.h"\n' + text.replace(original, converted)


def unused_cache_release_argument(text):
    (text, n) = re.subn('void\\s+OpenMapYard\\(int16_t unused\\)', 'void OpenMapYard(void)', text)
    if n != 1:
        raise ValueError('unused map entry word shape changed')
    pattern = 'extern void\\s+ch_SetCacheHooks\\(char\\s*\\*\\s*\\(\\s*\\*cache\\)\\(int16_t object, int16_t type\\)\\);'
    (text, n) = re.subn(pattern, 'extern void ch_SetCacheHooks(char *(*cache)(int16_t object, int16_t type), char *(*release)(int16_t object, int16_t type));', text)
    if n != 1:
        raise ValueError('canonical cache callback prototype shape changed')
    (text, n) = re.subn('\\bch_SetCacheHooks\\(f_00F8_0543\\);', 'ch_SetCacheHooks(f_00F8_0543, 0);', text)
    if n != 1:
        raise ValueError('canonical unused release callback call shape changed')
    return text

def canonical_interior_views(text):
    """Direct owner fields/elements; no exported or macro old-name aliases.

    The two byte/word unions are compatible native views of exactly the
    canonical byte-array extents, retaining their actual byte initializers.
    A union provides word lvalues without incompatible pointer aliasing.
    """
    used = False
    for (owner, ctype) in (('fd_55B3_1CD4', 'char'), ('fd_3D57_082A', 'int16_t')):
        if owner == 'fd_55B3_1CD4':
            pattern = '(?m)^\\s*extern\\s+char\\s*\\*\\s*fd_55B3_1CD4\\s*;\\s*\\n'
            (text, n) = re.subn(pattern, '', text)
            if n:
                text = rename(text, {owner: owner + '[0]'})
                used = True
        else:
            (text, n) = re.subn('(?m)^\\s*extern\\s+int16_t\\s*\\*\\s*fd_3D57_082A\\[\\s*\\]\\s*;\\s*\\n', '', text)
            used |= bool(n)
    for (owner, count) in (('fd_3D57_07CC', 14), ('fd_3D57_0C1A', 4)):
        definition = '\\buint8_t\\s+' + owner + '\\[' + str(count) + '\\]\\s*=\\s*(\\{[^{}]*\\});'
        (text, n) = re.subn(definition, 'union CanonicalWordBytes' + str(count) + ' ' + owner + ' = { .bytes = \\1 };', text, flags=re.S)
        used |= bool(n)
        scalar_decl = '(?m)^\\s*extern\\s+int16_t\\s+' + owner + '\\s*;\\s*\\n'
        (text, n) = re.subn(scalar_decl, '', text)
        if n:
            text = rename(text, {owner: owner + '.words[0]'})
            used = True
        byte_decl = '(?m)^\\s*extern\\s+uint8_t\\s+' + owner + '\\[\\s*\\]\\s*;\\s*\\n'
        (text, n) = re.subn(byte_decl, '', text)
        if n:
            text = rename(text, {owner: owner + '.bytes'})
            used = True
    aliases = {'fd_3D57_07CE': '(&fd_3D57_07CC.words[1])', 'fd_3D57_0852': '(&fd_3D57_082A[10])', 'fd_55B3_1CD8': 'fd_55B3_1CD4[1]', 'fd_55B3_1CDC': 'fd_55B3_1CD4[2]', 'fd_55B3_1CE0': 'fd_55B3_1CD4[3]', 'fd_55B3_1CE4': 'fd_55B3_1CD4[4]'}
    for (name, expr) in aliases.items():
        (text, n) = re.subn('(?m)^\\s*extern\\s+[^;\\n]*\\b' + name + '\\b[^;\\n]*;\\s*\\n', '', text)
        if n:
            text = rename(text, {name: expr})
            used = True
    (text, n) = re.subn('(?m)^\\s*extern\\s+int16_t\\s+fd_3D57_0C1C\\s*;\\s*\\n', '', text)
    if n:
        text = rename(text, {'fd_3D57_0C1C': 'fd_3D57_0C1A.words[1]'})
        used = True
    (text, n) = re.subn('(?m)^\\s*extern\\s+uint8_t\\s+fd_3D57_0C1C\\[\\s*\\]\\s*;\\s*\\n', '', text)
    if n:
        text = rename(text, {'fd_3D57_0C1C': 'fd_3D57_0C1A.bytes[2]'})
        used = True
    screen = '(?m)^\\s*extern\\s+int16_t\\s+fd_55B3_5AA0\\[2\\]\\s*;\\s*\\n'
    (text, n) = re.subn(screen, 'extern struct Rect g_5A9C[2];\n', text)
    if n:
        text = re.sub('\\bfd_55B3_5AA0\\[\\s*0\\s*\\]', 'g_5A9C[0].right', text)
        text = re.sub('\\bfd_55B3_5AA0\\[\\s*1\\s*\\]', 'g_5A9C[0].bottom', text)
    if used:
        text = '#include "canonical_data_views.h"\n' + text
    return text

def audio_overlap_views(text, rel):
    if rel == 'src/root/m295C.c':
        text = re.sub('struct Snd\\s*\\{[^{}]*\\};', '', text, flags=re.S)
        text = re.sub('(?m)^\\s*extern\\s+PortableWholeAudioVoiceSlot\\s+fd_55B3_6B4E\\[\\s*\\]\\s*;\\s*\\n', '', text)
        text = re.sub('\\bstruct\\s+Snd\\b', 'PortableWholeAudioSample', text)
        text = text.replace('s->state', 's->loaded')
        text = re.sub('fd_55B3_6B4E\\[([^]]+)\\]\\.busy\\s*==\\s*0', 'fd_55B3_6B4C[\\1].snd == NULL', text)
        text = re.sub('fd_55B3_6B4E\\[([^]]+)\\]\\.snd', 'fd_55B3_6B4C[\\1].owner', text)
    if rel == 'src/root/m2815.c':
        text = re.sub('(?m)^\\s*extern\\s+int16_t\\s+fd_55B3_6BA4\\[\\s*\\]\\s*;\\s*\\n', '', text)
        text = re.sub('fd_55B3_6BA4\\[([^]]+)\\]', 'fd_55B3_6BA4[2 * (\\1)]', text)
    return text
GRAPHICS_SCALARS = ('g_3DB2', 'g_3DB4', 'g_3DB6', 'g_3DD2', 'g_3DDA', 'g_3DDC', 'g_3DDE', 'g_3DE0', 'g_3DE2', 'g_3DE4')

def graphics_canonical_views(text, rel):
    """Convert canonical TU declarations to typed views of canonical ASM data."""
    changed = False
    scalar = '(?m)^\\s*extern\\s+int16_t\\s+g_3DA0\\s*;\\s*\\n'
    (text, n) = re.subn(scalar, '', text)
    if n:
        text = rename(text, {'g_3DA0': 'g_3DA0.x'})
        changed = True
    point = '(?m)^\\s*extern\\s+(?:struct\\s+\\w+|Point|Pnt)\\s+g_3DA0\\s*;\\s*\\n'
    (text, n) = re.subn(point, '', text)
    changed |= bool(n)
    for word in GRAPHICS_SCALARS:
        low_byte = '(?m)^\\s*extern\\s+char\\s+' + word + '\\s*;\\s*\\n'
        (text, n) = re.subn(low_byte, '', text)
        if n:
            text = rename(text, {word: '((int8_t)(uint8_t)' + word + ')'})
            changed = True
    if changed:
        text = '#include "canonical_graphics_data.h"\n' + text
    return text

def edit_cache_view(text):
    if re.search('(?m)^\\s*int16_t\\s+fd_50F6_15C4\\[30\\]\\[40\\]\\s*;', text):
        text = re.sub('\\bint16_t\\s+fd_50F6_15C4\\[30\\]\\[40\\]\\s*;', 'union CanonicalEditCache fd_50F6_15C4;', text)
    else:
        (text, n) = re.subn('(?m)^\\s*extern\\s+int16_t\\s+fd_50F6_15C4\\[30\\]\\[40\\]\\s*;\\s*\\n', '', text)
        if not n:
            return text
        text = rename(text, {'fd_50F6_15C4': 'fd_50F6_15C4.rows'})
        text = re.sub('fd_50F6_15C4\\.rows\\[0\\]\\[([^]]+)\\]', 'fd_50F6_15C4.linear[\\1]', text)
    return '#include "canonical_edit_cache.h"\n' + text

def centralize(text):
    text = rename(text, RUNTIME_NAMES)
    io = '|'.join(RUNTIME_NAMES.values())
    text = re.sub('(?m)^\\s*extern\\s+[^;]*\\b(?:' + io + '|_f(?:mem\\w+|str\\w+))\\s*\\([^;]*;', '', text)
    text = re.sub('\\btypedef\\s+struct\\s+_iobuf\\s+DosFileStream\\s*;', '', text)
    return text
