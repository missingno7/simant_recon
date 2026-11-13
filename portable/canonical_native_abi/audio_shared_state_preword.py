from __future__ import annotations
import hashlib
import re
from typing import Callable
HEADER = '#include "portable/whole_program/platform/audio_state.h"\n'
SOURCE_MODULES = {'src/sound/sample_voices.c', 'src/sound/opl2_voices.c', 'src/sound/midi_player.c', 'src/sound/psg_voices.c', 'src/platform/port_io.c', 'src/sound/device_channels.c', 'src/sound/instruments.c', 'src/sound/midi_voices.c', 'src/sound/device_probe.c', 'src/sound/resource_loading.c'}
_AUDIO_TUS = {'src/sound/opl2_voices.c', 'src/sound/resource_loading.c', 'src/sound/psg_voices.c', 'src/sound/device_channels.c', 'src/sound/sample_voices.c', 'src/sound/midi_voices.c', 'src/platform/port_io.c', 'src/sound/midi_player.c', 'src/sound/device_probe.c'}

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
    source = _remove_then_tag(source, 'Sample', 'struct Sample { char far * far *data; unsigned len; unsigned loop; char looped; unsigned char octave; int tune; int loaded; char name[15]; int object; };', 9)
    source = _remove_then_tag(source, 'Instr', 'struct Instr { int kind; void far *p; };', 1)
    (source, _) = _code_sub(source, 'snd_instrument_descriptors\\[song->instrument\\[i\\]\\]\\.p', lambda _m: 'portable_whole_audio_sample(&snd_instrument_descriptors[song->instrument[i]])', label='m0000 bank sample payload', expected=3)
    (source, _) = _code_sub(source, 'snd_instrument_descriptors\\[i\\]\\.p', lambda _m: 'portable_whole_audio_sample(&snd_instrument_descriptors[i])', label='m0000 cleanup sample payload', expected=1)
    return source

def _m277e(source: str) -> str:
    source = _remove_then_tag(source, 'Chan', 'struct Chan { unsigned char type; unsigned char num; unsigned char priority; unsigned char instrument; unsigned char note; unsigned char age; };', 1)
    source = _remove_then_tag(source, 'Voice', 'struct Voice { int a; void *b; };', 10)
    for (old, new, expected) in (('snd_instrument_descriptors[i].a', 'snd_instrument_descriptors[i].kind', 1), ('snd_instrument_descriptors[i].b', 'snd_instrument_descriptors[i].payload', 1), ('src[i].a', 'src[i].kind', 1), ('src[i].b', 'src[i].payload', 1)):
        (source, _) = _code_sub(source, re.escape(old), lambda _m, value=new: value, label=f'm277E {old}', expected=expected)
    return source

def _m2815(source: str) -> str:
    source = _remove_then_tag(source, 'Instr', 'struct Instr { int kind; void far *p; };', 1)
    (source, _) = _code_sub(source, 'snd_instrument_descriptors\\[instr\\]\\.p', lambda _m: 'portable_whole_audio_patch_bytes(&snd_instrument_descriptors[instr])', label='m2815 patch pointer', expected=2)
    return source

def _m290d(source: str) -> str:
    source = _remove_then_tag(source, 'Sample', 'struct Sample { char far * far *data; unsigned len; unsigned loop; char looped; unsigned char octave; int tune; int loaded; char name[15]; int object; };', 9)
    source = _remove_then_tag(source, 'SndChan', 'struct SndChan { unsigned pos; PortableWholeAudioSample far *snd; unsigned end; unsigned start; unsigned step; unsigned voltab; unsigned char frac; unsigned char flags; PortableWholeAudioSample far *owner; };', 2)
    source = _remove_then_tag(source, 'Instr', 'struct Instr { int kind; void far *p; };', 1)
    (source, _) = _code_sub(source, 'snd_instrument_descriptors\\[instr\\]\\.p', lambda _m: 'portable_whole_audio_sample(&snd_instrument_descriptors[instr])', label='m290D sample pointer', expected=1)
    return source

def _m295c(source: str) -> str:
    source = _remove_then_tag(source, 'Chan', 'struct Chan { unsigned char type; unsigned char num; unsigned char priority; unsigned char instrument; unsigned char note; unsigned char age; };', 3)
    source = _remove_then_tag(source, 'Drv', 'struct Drv { int count; int far *info; };', 1)
    source = _remove_then_tag(source, 'Slot', 'struct Slot { long busy; int w4; int w6; int w8; int wA; int wC; struct Snd far *snd; int w12; };', 1)
    (source, _) = _code_sub(source, 'snd_instrument_descriptors\\[dev\\]\\.count', lambda _m: 'snd_instrument_descriptors[dev].kind', label='m295C driver kind', expected=2)
    (source, _) = _code_sub(source, 'snd_instrument_descriptors\\[dev\\]\\.info', lambda _m: 'portable_whole_audio_driver_info(&snd_instrument_descriptors[dev])', label='m295C driver info', expected=6)
    return source

def _data_b8(source: str) -> str:
    source = _remove_then_tag(source, 'Sample', 'struct Sample { char far * far *data; unsigned len; unsigned loop; char looped; unsigned char octave; int tune; int loaded; char name[15]; int object; };', 58)
    source = _remove_then_tag(source, 'Instr', 'struct Instr { int kind; void far *p; };', 9)
    return source
_SHARED_EXTERN_COUNTS: dict[str, dict[str, int]] = {'src/sound/resource_loading.c': {'snd_sample_release_list': 1, 'snd_instrument_descriptors': 1, 'snd_driver_capabilities': 1}, 'src/sound/device_channels.c': {'snd_driver_probe_table': 1, 'snd_sample_channel_count': 1, 'snd_voice_build_index': 1, 'snd_driver_capabilities': 1, 'snd_voice_slots': 1, 'snd_instrument_descriptors': 1, 'fd_50F6_4A4A': 1, 'snd_device_io_base': 1, 'snd_dac_io_base': 1, 'snd_speaker_output_pointer': 1, 'snd_sample_output_routine': 1, 'snd_sample_volume_bias': 1, 'snd_based_dac_output_pointer': 1, 'snd_port200_output_pointer': 1, 'snd_adlib_output_pointer': 1, 'snd_opl_volume_bias': 1, 'snd_sb_io_base': 1, 'snd_sb_dsp_write_port': 1, 'snd_sb_output_pointer': 1, 'fd_50F6_4A46': 1, 'snd_port222_output_pointer': 1, 'snd_lpt_output_pointer': 1}, 'src/sound/opl2_voices.c': {'snd_instrument_descriptors': 1, 'snd_opl_volume_bias': 1, 'snd_opl_volume_curve': 1}, 'src/sound/midi_player.c': {'midi_song_data_handle': 1, 'midi_song_data_bytes': 1, 'midi_service_countdown': 1, 'midi_channel_instruments': 1, 'midi_channel_priorities': 1, 'midi_header_division': 1, 'midi_track_event_ticks': 1, 'midi_track_status': 1, 'midi_tick_delay_scale': 1}, 'src/sound/sample_voices.c': {'snd_sample_channel_records': 1, 'snd_instrument_descriptors': 1}, 'src/sound/device_probe.c': {'snd_driver_capabilities': 1, 'snd_device_io_base': 1}, 'src/sound/midi_voices.c': {'snd_voice_slots': 1, 'fd_55B3_6B4E': 1, 'snd_instrument_descriptors': 1}, 'src/sound/psg_voices.c': {'snd_device_io_base': 1}}
_TRANSFORMS: dict[str, Callable[[str], str]] = {'src/sound/resource_loading.c': _m0000, 'src/sound/device_channels.c': _m277e, 'src/sound/opl2_voices.c': _m2815, 'src/sound/sample_voices.c': _m290d, 'src/sound/midi_voices.c': _m295c, 'src/sound/instruments.c': _data_b8}

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
    if rel == 'src/sound/resource_loading.c' and re.search('snd_instrument_descriptors\\s*\\[[^]]+\\]\\s*\\.\\s*p\\b', _lexical_mask(output)[0]):
        raise AssertionError('m0000 direct Sample view remains')
    if rel == 'src/sound/opl2_voices.c' and re.search('snd_instrument_descriptors\\s*\\[[^]]+\\]\\s*\\.\\s*p\\b', _lexical_mask(output)[0]):
        raise AssertionError('m2815 direct patch pointer remains')
    if rel == 'src/sound/midi_voices.c' and re.search('snd_instrument_descriptors\\s*\\[[^]]+\\]\\s*\\.\\s*info\\b', _lexical_mask(output)[0]):
        raise AssertionError('m295C direct driver-info pointer remains')
    return (output, {'status': 'SOURCE_SHARED_AUDIO_STATE' if transform is not None else 'SOURCE_SHARED_AUDIO_DECLARATIONS', 'original_sha256': actual_sha, 'transformed_input_sha256': _sha(source.encode('utf-8')), 'output_sha256': _sha(output.encode('utf-8')), 'owner_header': 'portable/whole_program/platform/audio_state.h', 'state_ownership': {'pointer_tables_records': 'canonical C/ASM providers with shared native representation types', 'existing_scalar_aliases': 'canonical source providers; no second definitions introduced'}, 'centralized_externs_removed': removed_externs, 'deferred_scalar_externs_retained': retained_scalar_externs, 'lexical_contract': 'Only code tokens and exact complete struct blocks changed; comments and literals are protected by offset-preserving lexer.'})
