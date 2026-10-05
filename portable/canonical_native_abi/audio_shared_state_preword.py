from __future__ import annotations
import hashlib
import re
from typing import Callable
HEADER = '#include "portable/whole_program/platform/audio_state.h"\n'
SOURCE_MODULES = {'src/root/m290D.c', 'src/root/m2815.c', 'src/root/m284A.c', 'src/root/m29D6.c', 'src/root/m29F0.c', 'src/root/m277E.c', 'src/data/d55B3_00B8.c', 'src/root/m295C.c', 'src/root/m293A.c', 'src/root/m0000.c'}
_AUDIO_TUS = {f'src/root/{name}.c' for name in ('m0000', 'm277E', 'm2815', 'm284A', 'm290D', 'm293A', 'm295C', 'm29D6', 'm29F0')}

def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def _lexical_mask(source: str) -> tuple[str, bytearray]:
    """Blank comments/literals while preserving character offsets/newlines."""
    chars = list(source)
    protected = bytearray(len(source))
    state = 'code'
    i = 0
    while i < len(source):
        ch = source[i]
        nxt = source[i + 1] if i + 1 < len(source) else ''
        if state == 'code':
            if ch == '"':
                state = 'string'
            elif ch == "'":
                state = 'char'
            elif ch == '/' and nxt == '*':
                state = 'block_comment'
                protected[i] = protected[i + 1] = 1
                chars[i] = chars[i + 1] = ' '
                i += 1
            elif ch == '/' and nxt == '/':
                state = 'line_comment'
                protected[i] = protected[i + 1] = 1
                chars[i] = chars[i + 1] = ' '
                i += 1
        elif state in ('string', 'char'):
            protected[i] = 1
            if ch not in '\r\n':
                chars[i] = ' '
            if ch == '\\' and i + 1 < len(source):
                i += 1
                protected[i] = 1
                if source[i] not in '\r\n':
                    chars[i] = ' '
            elif state == 'string' and ch == '"' or (state == 'char' and ch == "'"):
                state = 'code'
        elif state == 'block_comment':
            protected[i] = 1
            if ch not in '\r\n':
                chars[i] = ' '
            if ch == '*' and nxt == '/':
                i += 1
                protected[i] = 1
                chars[i] = ' '
                state = 'code'
        else:
            protected[i] = 1
            if ch not in '\r\n':
                chars[i] = ' '
            if ch in '\r\n':
                state = 'code'
        i += 1
    if state in ('string', 'char', 'block_comment'):
        raise ValueError(f'unterminated C lexical region: {state}')
    return (''.join(chars), protected)

def _code_sub(source: str, pattern: str, replacement: str, *, label: str, expected: int) -> tuple[str, int]:
    (masked, protected) = _lexical_mask(source)
    matches = list(re.finditer(pattern, masked, flags=re.MULTILINE))
    if len(matches) != expected:
        raise ValueError(f'{label}: expected {expected} code occurrence(s), found {len(matches)}')
    result = source
    for match in reversed(matches):
        if any(protected[match.start():match.end()]):
            raise ValueError(f'{label}: attempted to cross comment/string/character content')
        result = result[:match.start()] + replacement(match) + result[match.end():]
    return (result, len(matches))

def _remove_struct(source: str, tag: str, expected_fields: str) -> tuple[str, int]:
    pattern = f'struct\\s+{re.escape(tag)}\\s*\\{{[^{{}}]*\\}}\\s*;'
    (masked, protected) = _lexical_mask(source)
    matches = list(re.finditer(pattern, masked, flags=re.MULTILINE))
    if len(matches) != 1:
        raise ValueError(f'{tag}: expected one complete struct definition, found {len(matches)}')
    match = matches[0]
    if any(protected[match.start():match.end()]):
        raise ValueError(f'{tag}: struct block contains comment/literal; refuse to erase it')
    found = re.sub('\\s+', ' ', masked[match.start():match.end()]).strip()
    wanted = re.sub('\\s+', ' ', expected_fields).strip()
    if found != wanted:
        raise ValueError(f'{tag}: canonical source struct fields changed: {found!r}')
    return (source[:match.start()] + source[match.end():], 1)

def _tag(source: str, old: str, new: str, expected: int) -> tuple[str, int]:
    return _code_sub(source, f'\\bstruct\\s+{re.escape(old)}\\b', lambda _m: new, label=f'struct {old} type use', expected=expected)
_CANONICAL_TYPE = {'Sample': 'PortableWholeAudioSample', 'Chan': 'PortableWholeAudioRuntimeChannel', 'Voice': 'PortableWholeAudioInstrumentEntry', 'Instr': 'PortableWholeAudioInstrumentEntry', 'SndChan': 'PortableWholeAudioRuntimeSample', 'Drv': 'PortableWholeAudioInstrumentEntry', 'Slot': 'PortableWholeAudioVoiceSlot'}

def _remove_then_tag(source: str, tag: str, fields: str, uses: int) -> str:
    (source, _) = _remove_struct(source, tag, fields)
    (source, _) = _tag(source, tag, _CANONICAL_TYPE[tag], uses)
    return source

def _m0000(source: str) -> str:
    source = _remove_then_tag(source, 'Sample', 'struct Sample { Handle data; unsigned len; unsigned loop; char looped; unsigned char octave; int tune; int loaded; char name[15]; int object; };', 6)
    source = _remove_then_tag(source, 'Instr', 'struct Instr { int kind; PortableWholeAudioSample far *sample; };', 1)
    (source, _) = _code_sub(source, 'fd_50F6_0000\\[song->bank\\[i\\]\\]\\.sample', lambda _m: 'portable_whole_audio_sample(&fd_50F6_0000[song->bank[i]])', label='m0000 bank sample payload', expected=3)
    (source, _) = _code_sub(source, 'fd_50F6_0000\\[i\\]\\.sample', lambda _m: 'portable_whole_audio_sample(&fd_50F6_0000[i])', label='m0000 cleanup sample payload', expected=1)
    return source

def _m277e(source: str) -> str:
    source = _remove_then_tag(source, 'Chan', 'struct Chan { char type; char num; char c2; char c3; char c4; char c5; };', 1)
    source = _remove_then_tag(source, 'Voice', 'struct Voice { int a; void *b; };', 10)
    for (old, new, expected) in (('fd_50F6_0000[i].a', 'fd_50F6_0000[i].kind', 1), ('fd_50F6_0000[i].b', 'fd_50F6_0000[i].payload', 1), ('src[i].a', 'src[i].kind', 1), ('src[i].b', 'src[i].payload', 1)):
        (source, _) = _code_sub(source, re.escape(old), lambda _m, value=new: value, label=f'm277E {old}', expected=expected)
    return source

def _m2815(source: str) -> str:
    source = _remove_then_tag(source, 'Instr', 'struct Instr { int a; unsigned char far *p; };', 1)
    (source, _) = _code_sub(source, 'fd_50F6_0000\\[instr\\]\\.p', lambda _m: 'portable_whole_audio_patch_bytes(&fd_50F6_0000[instr])', label='m2815 patch pointer', expected=2)
    return source

def _m290d(source: str) -> str:
    source = _remove_then_tag(source, 'Sample', 'struct Sample { char far *data; unsigned len; unsigned loop; char looped; unsigned char octave; int tune; int loaded; };', 9)
    source = _remove_then_tag(source, 'SndChan', 'struct SndChan { unsigned pos; PortableWholeAudioSample far *snd; unsigned end; unsigned start; unsigned step; unsigned voltab; unsigned char frac; unsigned char flags; PortableWholeAudioSample far *owner; };', 2)
    source = _remove_then_tag(source, 'Instr', 'struct Instr { int a; unsigned char far *p; };', 1)
    (source, _) = _code_sub(source, 'fd_50F6_0000\\[instr\\]\\.p', lambda _m: 'portable_whole_audio_sample(&fd_50F6_0000[instr])', label='m290D sample pointer', expected=1)
    return source

def _m295c(source: str) -> str:
    source = _remove_then_tag(source, 'Chan', 'struct Chan { unsigned char type; unsigned char num; unsigned char c2; unsigned char c3; unsigned char c4; unsigned char c5; };', 3)
    source = _remove_then_tag(source, 'Drv', 'struct Drv { int count; int far *info; };', 1)
    source = _remove_then_tag(source, 'Slot', 'struct Slot { long busy; int w4; int w6; int w8; int wA; int wC; struct Snd far *snd; int w12; };', 1)
    (source, _) = _code_sub(source, 'fd_50F6_0000\\[dev\\]\\.count', lambda _m: 'fd_50F6_0000[dev].kind', label='m295C driver kind', expected=2)
    (source, _) = _code_sub(source, 'fd_50F6_0000\\[dev\\]\\.info', lambda _m: 'portable_whole_audio_driver_info(&fd_50F6_0000[dev])', label='m295C driver info', expected=6)
    return source

def _data_b8(source: str) -> str:
    source = _remove_then_tag(source, 'Sample', 'struct Sample { Handle data; unsigned len; unsigned loop; char looped; unsigned char octave; int tune; int loaded; char name[15]; int object; };', 58)
    source = _remove_then_tag(source, 'Instr', 'struct Instr { int kind; void *p; };', 9)
    return source
_SHARED_EXTERN_COUNTS: dict[str, dict[str, int]] = {'src/root/m0000.c': {'fd_50F6_0150': 1, 'fd_50F6_0000': 1, 'fd_50F6_01F0': 1}, 'src/root/m277E.c': {'fd_55B3_74DA': 1, 'fd_50F6_4A48': 1, 'fd_50F6_4A4C': 1, 'fd_50F6_01F0': 1, 'fd_50F6_4A4E': 1, 'fd_50F6_0000': 1, 'fd_50F6_4A4A': 1, 'fd_50F6_4B14': 1, 'fd_55B3_6B4A': 1, 'fd_55B3_74AD': 1, 'fd_55B3_6B9C': 1, 'fd_55B3_74C0': 1, 'fd_55B3_74B9': 1, 'fd_55B3_74B3': 1, 'fd_55B3_74AF': 1, 'fd_50F6_4B16': 1, 'fd_55B3_7564': 1, 'fd_55B3_6BA0': 1, 'fd_55B3_74B5': 1, 'fd_50F6_4A46': 1, 'fd_55B3_74B7': 1, 'fd_55B3_74B1': 1}, 'src/root/m2815.c': {'fd_50F6_0000': 1, 'fd_50F6_4B16': 1, 'fd_55B3_6BA4': 1}, 'src/root/m284A.c': {'fd_50F6_4B28': 1, 'fd_50F6_4B2C': 1, 'fd_55B3_6B42': 1, 'fd_50F6_4B8E': 1, 'fd_50F6_4BAA': 1, 'fd_50F6_4B2E': 1, 'fd_50F6_4B42': 1, 'fd_50F6_4B30': 1, 'fd_50F6_4B8A': 1}, 'src/root/m290D.c': {'fd_55B3_6B4C': 1, 'fd_50F6_0000': 1}, 'src/root/m293A.c': {'fd_50F6_01F0': 1, 'fd_50F6_4B14': 1}, 'src/root/m295C.c': {'fd_50F6_4A4E': 1, 'fd_55B3_6B4E': 1, 'fd_50F6_0000': 1}, 'src/root/m29D6.c': {'fd_50F6_4B14': 1}}
_TRANSFORMS: dict[str, Callable[[str], str]] = {'src/root/m0000.c': _m0000, 'src/root/m277E.c': _m277e, 'src/root/m2815.c': _m2815, 'src/root/m290D.c': _m290d, 'src/root/m295C.c': _m295c, 'src/data/d55B3_00B8.c': _data_b8}

def adapt(path: str, source: str, original_source: str | bytes, *, deferred_scalar_externs: set[str] | frozenset[str]=frozenset()) -> tuple[str, dict[str, object]]:
    """Adapt one original-source-derived TU; original bytes are mandatory pins."""
    rel = path.replace('\\', '/')
    transform = _TRANSFORMS.get(rel)
    if transform is None and rel not in _AUDIO_TUS:
        return (source, {'status': 'UNCHANGED', 'reason': 'no shared audio-state view'})
    original = original_source if isinstance(original_source, bytes) else original_source.encode('utf-8')
    actual_sha = _sha(original)
    expected_symbols = _SHARED_EXTERN_COUNTS.get(rel, {})
    unknown_deferred = set(deferred_scalar_externs) - set(expected_symbols)
    if unknown_deferred:
        raise ValueError(f'{rel}: cannot defer non-shared scalar declaration(s): {sorted(unknown_deferred)}')
    if HEADER in source:
        raise ValueError(f'{rel}: common audio-state header was already injected')
    output = transform(source) if transform is not None else source
    removed_externs: dict[str, int] = {}
    retained_scalar_externs: dict[str, int] = {}
    for (symbol, expected) in _SHARED_EXTERN_COUNTS.get(rel, {}).items():
        pattern = f'(?m)^[ \\t]*extern\\b[^;\\r\\n]*\\b{re.escape(symbol)}\\b[^;\\r\\n]*;'
        if symbol in deferred_scalar_externs:
            (masked, _) = _lexical_mask(output)
            retained = len(re.findall(pattern, masked, flags=re.MULTILINE))
            if retained < 1:
                raise ValueError(f'{rel} shared scalar extern {symbol}: expected to retain {expected}, found {retained}')
            retained_scalar_externs[symbol] = retained
            continue
        (output, count) = _code_sub(output, pattern, lambda _m: '', label=f'{rel} shared extern {symbol}', expected=len(re.findall(pattern, _lexical_mask(output)[0], flags=re.MULTILINE)))
        removed_externs[symbol] = count
    output = HEADER + output
    if rel.endswith('m0000.c') and re.search('fd_50F6_0000\\s*\\[[^]]+\\]\\s*\\.\\s*sample', _lexical_mask(output)[0]):
        raise AssertionError('m0000 direct Sample view remains')
    if rel.endswith('m2815.c') and re.search('fd_50F6_0000\\s*\\[[^]]+\\]\\s*\\.\\s*p\\b', _lexical_mask(output)[0]):
        raise AssertionError('m2815 direct patch pointer remains')
    if rel.endswith('m295C.c') and re.search('fd_50F6_0000\\s*\\[[^]]+\\]\\s*\\.\\s*info\\b', _lexical_mask(output)[0]):
        raise AssertionError('m295C direct driver-info pointer remains')
    return (output, {'status': 'SOURCE_SHARED_AUDIO_STATE' if transform is not None else 'SOURCE_SHARED_AUDIO_DECLARATIONS', 'original_sha256': actual_sha, 'transformed_input_sha256': _sha(source.encode('utf-8')), 'output_sha256': _sha(output.encode('utf-8')), 'owner_header': 'portable/whole_program/platform/audio_state.h', 'state_ownership': {'pointer_tables_records': 'canonical C/ASM providers with shared native representation types', 'existing_scalar_aliases': 'canonical source providers; no second definitions introduced'}, 'centralized_externs_removed': removed_externs, 'deferred_scalar_externs_retained': retained_scalar_externs, 'lexical_contract': 'Only code tokens and exact complete struct blocks changed; comments and literals are protected by offset-preserving lexer.'})
