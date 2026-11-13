import re
from . import tokenizer as csrc
from . import scalar, lexical
RUNTIME_NAMES = {n: 'dos_' + n for n in ('open', 'read', 'write', 'lseek', 'close', 'access', 'chdir', 'getcwd', 'remove', 'stricmp', 'fopen', 'fread', 'fclose')}
RUNTIME_NAMES.update({'errno': 'dos_errno', 'malloc': 'dos_malloc', 'free': 'dos_free', '_ffree': 'dos_free', '_frealloc': 'dos_realloc', 'FILE': 'DosFileStream'})
TRIVIA = {'ws', 'nl', 'cmt', 'pp', 'asm'}


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

def menu_resource_view(text, rel):
    if rel == 'src/window/menu_setup.c':
        text = text.replace('g_6054 = portable_menu_source_record_tables(&g_menu_view);', 'g_6054 = (char ***)&g_menu_view.titles;')
    return text


def screen_clip_canonical_views(text, rel):
    if 'gfx_screen_clip_list' not in {t.text for t in csrc.tokenize(text) if t.kind == 'id'}:
        return text
    if rel == 'src/graphics/state/screen_clip.c':
        return text
    text = re.sub('extern\\s+(?:struct\\s+Rect\\s+gfx_screen_clip_list(?:\\s*\\[\\s*2\\s*\\])?|char\\s+gfx_screen_clip_list\\[\\s*\\])\\s*;', '', text)
    if rel.startswith('src/'):
        text = re.sub('struct\\s+Rect\\s*\\{\\s*int16_t\\s+left;\\s*int16_t\\s+top;\\s*int16_t\\s+right;\\s*int16_t\\s+bottom;\\s*\\};', '', text)
        text = '#include "portable/whole_program/platform/graphics_source_clip.h"\n' + text
        text = re.sub('extern\\s+(?:char|int16_t)\\s*\\*\\s*clip_active_list_offset\\s*;', 'extern struct Rect *clip_active_list_offset;', text)
        if rel == 'src/window/menu_tracking.c':
            text = re.sub('\\bchar\\s*\\*\\s*saved\\s*;', 'struct Rect *saved;', text)
        if rel in {'src/window/drawing.c', 'src/ui/yellow_commands.c'}:
            text = re.sub('\\bclip_active_list_offset\\s*\\[\\s*1\\s*\\]', 'clip_active_list_offset->top', text)
            text = re.sub('(clip_active_list_offset->top\\s*[!=]=\\s*)0x8000\\b', '\\1(int16_t)0x8000', text)
    edits = [(t.s, t.e) for t in csrc.tokenize(text) if t.kind == 'id' and t.text == 'gfx_screen_clip_list' and (not text[t.e:].lstrip().startswith('['))]
    for (lo, hi) in reversed(edits):
        text = text[:lo] + 'gfx_screen_clip_list[0]' + text[hi:]
    text = text.replace('return gfx_screen_clip_list[0];', 'return (char *)&gfx_screen_clip_list[0];')
    text = text.replace('clip_restrict_rect(gfx_screen_clip_list[0])', 'clip_restrict_rect((char *)&gfx_screen_clip_list[0])')
    return text

def callback_views(text, slots, types=None):
    return_types = {}
    for name in slots:
        declaration = re.search('extern\\s+(\\w+)\\s*\\(\\s*\\*\\s*' + re.escape(name) + '\\s*\\)\\s*\\(', text)
        if declaration and declaration.group(1) != 'void':
            return_types[name] = declaration.group(1)
    text = discard_callback_declarations(text, set(slots))
    mappings = {name: f'(*( {types[name]} *)(void *)&driver_callback_table[{slot}])' if types and name in types else f'(({return_types[name]} (*)())driver_callback_table[{slot}])' if name in return_types else f'driver_callback_table[{slot}]' for (name, slot) in slots.items()}
    text = lexical.rename(text, mappings)
    if any((name in text for name in ('driver_callback_table[', '&driver_callback_table['))):
        text = 'extern void (*driver_callback_table[25])();\n' + text
    return text

def translate_29d6_port_block(text):
    original = '    _asm {\n        mov dx, port\n        mov ax, freq\n        push ax\n        and ax, 0Fh\n        add ax, reg\n        mov bx, ax\n        pop ax\n        and ax, 3F0h\n        mov cx, 4\n        shr ax, cl\n        mov ah, al\n        mov al, bl\n        out dx, ax\n        xor ax, ax\n        mov ax, reg\n        add ax, 10h\n        add ax, val\n        out dx, al\n    }\n'
    converted = '    {\n        uint16_t reg_word = (uint16_t)(uint8_t)reg;\n        uint8_t high = (uint8_t)((freq & 0x03f0u) >> 4);\n        uint8_t low = (uint8_t)((freq & 0x000fu) + reg_word);\n        dos_audio_host_out16((uint16_t)port, (uint16_t)(((uint16_t)high << 8) | low));\n        snd_port_write_byte(port, (char)(reg_word + 0x10u + (uint16_t)val));\n    }\n'
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
    (text, n) = re.subn('\\bch_SetCacheHooks\\(res_lookup_dynamic_balloon\\);', 'ch_SetCacheHooks(res_lookup_dynamic_balloon, 0);', text)
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
    for (owner, ctype) in (('startup_config_strings', 'char'), ('HistGraphs', 'int16_t')):
        if owner == 'startup_config_strings':
            pattern = '(?m)^\\s*extern\\s+char\\s*\\*\\s*startup_config_strings\\s*;\\s*\\n'
            (text, n) = re.subn(pattern, '', text)
            if n:
                text = lexical.rename(text, {owner: owner + '[0]'})
                used = True
        else:
            (text, n) = re.subn('(?m)^\\s*extern\\s+int16_t\\s*\\*\\s*HistGraphs\\[\\s*\\]\\s*;\\s*\\n', '', text)
            used |= bool(n)
    for (owner, count) in (('GameSpeed', 14), ('NextFeed', 4)):
        definition = '\\buint8_t\\s+' + owner + '\\[' + str(count) + '\\]\\s*=\\s*(\\{[^{}]*\\});'
        (text, n) = re.subn(definition, 'union CanonicalWordBytes' + str(count) + ' ' + owner + ' = { .bytes = \\1 };', text, flags=re.S)
        used |= bool(n)
        scalar_decl = '(?m)^\\s*extern\\s+int16_t\\s+' + owner + '\\s*;\\s*\\n'
        (text, n) = re.subn(scalar_decl, '', text)
        if n:
            text = lexical.rename(text, {owner: owner + '.words[0]'})
            used = True
        byte_decl = '(?m)^\\s*extern\\s+uint8_t\\s+' + owner + '\\[\\s*\\]\\s*;\\s*\\n'
        (text, n) = re.subn(byte_decl, '', text)
        if n:
            text = lexical.rename(text, {owner: owner + '.bytes'})
            used = True
    aliases = {'game_speed_delay_table': '(&GameSpeed.words[1])', 'AltHistGraphs': '(&HistGraphs[10])', 'startup_low_memory_message': 'startup_config_strings[1]', 'startup_bad_switch_message': 'startup_config_strings[2]', 'startup_missing_config_message': 'startup_config_strings[3]', 'startup_config_path': 'startup_config_strings[4]'}
    for (name, expr) in aliases.items():
        (text, n) = re.subn('(?m)^\\s*extern\\s+[^;\\n]*\\b' + name + '\\b[^;\\n]*;\\s*\\n', '', text)
        if n:
            text = lexical.rename(text, {name: expr})
            used = True
    (text, n) = re.subn('(?m)^\\s*extern\\s+int16_t\\s+RedInitOn\\s*;\\s*\\n', '', text)
    if n:
        text = lexical.rename(text, {'RedInitOn': 'NextFeed.words[1]'})
        used = True
    (text, n) = re.subn('(?m)^\\s*extern\\s+uint8_t\\s+RedInitOn\\[\\s*\\]\\s*;\\s*\\n', '', text)
    if n:
        text = lexical.rename(text, {'RedInitOn': 'NextFeed.bytes[2]'})
        used = True
    screen = '(?m)^\\s*extern\\s+int16_t\\s+fd_55B3_5AA0\\[2\\]\\s*;\\s*\\n'
    (text, n) = re.subn(screen, 'extern struct Rect gfx_screen_clip_list[2];\n', text)
    if n:
        text = re.sub('\\bfd_55B3_5AA0\\[\\s*0\\s*\\]', 'gfx_screen_clip_list[0].right', text)
        text = re.sub('\\bfd_55B3_5AA0\\[\\s*1\\s*\\]', 'gfx_screen_clip_list[0].bottom', text)
    if used:
        text = '#include "canonical_data_views.h"\n' + text
    return text

def audio_overlap_views(text, rel):
    if rel == 'src/sound/midi_voices.c':
        text = re.sub('struct Snd\\s*\\{[^{}]*\\};', '', text, flags=re.S)
        text = re.sub('(?m)^\\s*extern\\s+PortableWholeAudioVoiceSlot\\s+fd_55B3_6B4E\\[\\s*\\]\\s*;\\s*\\n', '', text)
        text = re.sub('\\bstruct\\s+Snd\\b', 'PortableWholeAudioSample', text)
        text = text.replace('s->state', 's->loaded')
        text = re.sub('fd_55B3_6B4E\\[([^]]+)\\]\\.busy\\s*==\\s*0', 'snd_sample_channel_records[\\1].snd == NULL', text)
        text = re.sub('fd_55B3_6B4E\\[([^]]+)\\]\\.snd', 'snd_sample_channel_records[\\1].owner', text)
    if rel == 'src/sound/opl2_voices.c':
        text = re.sub('(?m)^\\s*extern\\s+int16_t\\s+snd_opl_volume_curve\\[\\s*\\]\\s*;\\s*\\n', '', text)
        text = re.sub('snd_opl_volume_curve\\[([^]]+)\\]', 'snd_opl_volume_curve[2 * (\\1)]', text)
    return text
GRAPHICS_SCALARS = ('gfx_screen_width_pixels', 'gfx_screen_height_pixels', 'gfx_screen_row_bytes', 'g_3DD2', 'gfx_font_glyph_stride', 'gfx_font_height_pixels', 'fontWidth', '_foreColor', 'g_3DE2', 'g_3DE4')

def graphics_canonical_views(text, rel):
    """Convert canonical TU declarations to typed views of canonical ASM data."""
    changed = False
    bitmap = '(?m)^\\s*extern\\s+char(?:\\s+far)?\\s+text_bitmap_pixels\\[\\]\\s*;\\s*\\n'
    (text, n) = re.subn(bitmap, '', text)
    if n:
        text = lexical.rename(text, {'text_bitmap_pixels': 'CANONICAL_TEXT_BITMAP_BITS'})
        changed = True
    scalar = '(?m)^\\s*extern\\s+int16_t\\s+gfx_text_pen_x\\s*;\\s*\\n'
    (text, n) = re.subn(scalar, '', text)
    if n:
        text = lexical.rename(text, {'gfx_text_pen_x': 'gfx_text_pen_x.x'})
        changed = True
    point = '(?m)^\\s*extern\\s+(?:struct\\s+\\w+|Point|Pnt)\\s+gfx_text_pen_x\\s*;\\s*\\n'
    (text, n) = re.subn(point, '', text)
    changed |= bool(n)
    for word in GRAPHICS_SCALARS:
        low_byte = '(?m)^\\s*extern\\s+char\\s+' + word + '\\s*;\\s*\\n'
        (text, n) = re.subn(low_byte, '', text)
        if n:
            text = lexical.rename(text, {word: '((int8_t)(uint8_t)' + word + ')'})
            changed = True
    if changed:
        text = '#include "canonical_graphics_data.h"\n' + text
    return text

def edit_cache_view(text):
    if re.search('(?m)^\\s*int16_t\\s+edit_cached_life_tiles\\[30\\]\\[40\\]\\s*;', text):
        text = re.sub('\\bint16_t\\s+edit_cached_life_tiles\\[30\\]\\[40\\]\\s*;', 'union CanonicalEditCache edit_cached_life_tiles;', text)
    else:
        (text, n) = re.subn('(?m)^\\s*extern\\s+int16_t\\s+edit_cached_life_tiles\\[30\\]\\[40\\]\\s*;\\s*\\n', '', text)
        if not n:
            return text
        text = lexical.rename(text, {'edit_cached_life_tiles': 'edit_cached_life_tiles.rows'})
        text = re.sub('edit_cached_life_tiles\\.rows\\[0\\]\\[([^]]+)\\]', 'edit_cached_life_tiles.linear[\\1]', text)
    return '#include "canonical_edit_cache.h"\n' + text

def centralize(text):
    text = lexical.rename(text, RUNTIME_NAMES)
    io = '|'.join(RUNTIME_NAMES.values())
    text = re.sub('(?m)^\\s*extern\\s+[^;]*\\b(?:' + io + '|_f(?:mem\\w+|str\\w+))\\s*\\([^;]*;', '', text)
    text = re.sub('\\btypedef\\s+struct\\s+_iobuf\\s+DosFileStream\\s*;', '', text)
    return text
