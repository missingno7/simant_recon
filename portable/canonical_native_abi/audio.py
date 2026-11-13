from __future__ import annotations
import hashlib
import re
from typing import Any
DEPENDENCY_ANCHORS = {'src/sound/midi_player.c': [{'path': 'src/sound/resource_loading.c', 'role': 'snd_load_song_resources obtains the song resource, locks its handle, and stores the handle in Song.data before m284A reads it'}, {'path': 'src/memory/ralloc.c', 'role': "mem_Size returns the handle size as long; m284A's own int declaration/store retain the low 16-bit source-visible bound"}], 'src/sound/device_channels.c': [{'path': 'src/sound/instruments.c', 'role': 'struct Instr declares void *p and the referenced 56-entry voice tables use that native pointer member'}], 'src/sound/sample_voices.c': [{'path': 'src/sound/resource_loading.c', 'role': 'snd_load_sample_resource stores the kind-5 decoded sample Handle in Sample.data; the native hardware ISR dereferences that canonical handle without copied voice state'}, {'path': 'src/sound/instruments.c', 'role': 'fd_55B3_0C42 and mode-specific sibling tables bind type-1 instrument entries to source Sample records consumed by snd_start_sample_note'}]}

def _sha(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def _replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count == 0:
        # Canonical purpose comments may now occur between ASM instructions.
        # Match the same tokens with only whitespace/comments between them.
        pattern = r'(?:\s|/\*.*?\*/)+'.join(re.escape(x) for x in old.split())
        matches = list(re.finditer(pattern, source, re.S))
        if len(matches) == 1:
            m = matches[0]
            return source[:m.start()] + new.strip() + source[m.end():]
    if count != 1:
        raise ValueError(f'{label}: expected one exact source form, found {count}')
    return source.replace(old, new, 1)

def _convert_29f0(source: str) -> tuple[str, dict[str, Any]]:
    if source.count('_asm') != 6:
        raise ValueError('m29F0: expected six original inline assembly bodies')
    forms = [('void far snd_sample_interrupts_disable(void)\n{\n    _asm cli\n}', 'void far snd_sample_interrupts_disable(void)\n{\n    dos_audio_host_interrupt_disable();\n}'), ('void far snd_sample_interrupts_enable(void)\n{\n    _asm sti\n}', 'void far snd_sample_interrupts_enable(void)\n{\n    dos_audio_host_interrupt_enable();\n}'), ('void far snd_control_interrupts_disable(void)\n{\n    _asm cli\n}', 'void far snd_control_interrupts_disable(void)\n{\n    dos_audio_host_interrupt_disable();\n}'), ('void far snd_control_interrupts_enable(void)\n{\n    _asm sti\n}', 'void far snd_control_interrupts_enable(void)\n{\n    dos_audio_host_interrupt_enable();\n}'), ('void far snd_port_write_byte(int port, int value)\n{\n    _asm {\n        mov dx, port\n        mov al, byte ptr value\n        out dx, al\n    }\n}', 'void far snd_port_write_byte(int port, int value)\n{\n    dos_audio_host_out8((uint16_t)port, (uint8_t)value);\n}'), ('unsigned char far snd_port_read_byte(int port)\n{\n    unsigned char value;\n\n    _asm {\n        mov dx, port\n        in al, dx\n        mov value, al\n    }\n    return value;\n}', 'unsigned char far snd_port_read_byte(int port)\n{\n    return dos_audio_host_in8((uint16_t)port);\n}')]
    output = source
    for (old, new) in forms:
        output = _replace_once(output, old, new, 'm29F0 helper')
    if '_asm' in output:
        raise AssertionError('m29F0 assembly residue')
    output = '#include "portable/whole_program/platform/audio.h"\n\n' + output
    return (output, {'transformed_functions': ['snd_sample_interrupts_disable', 'snd_sample_interrupts_enable', 'snd_control_interrupts_disable', 'snd_control_interrupts_enable', 'snd_port_write_byte', 'snd_port_read_byte'], 'source_operations': {'cli': 'dos_audio_host_interrupt_disable()', 'sti': 'dos_audio_host_interrupt_enable()', 'out': 'DX receives the low word of port; AL receives the low byte of value; host call uses uint16_t/uint8_t', 'in': 'DX receives the low word of port; returned AL byte is provided by dos_audio_host_in8'}, 'leaves_unprovided': ['dos_audio_host_interrupt_disable', 'dos_audio_host_interrupt_enable', 'dos_audio_host_out8', 'dos_audio_host_in8']})

def _convert_284a(source: str) -> tuple[str, dict[str, Any]]:
    original_songp = source.count('SONGP(')
    if original_songp != 6:
        raise ValueError(f'm284A: expected six SONGP source forms, found {original_songp}')
    output = source
    output = _replace_once(output, '#define SONGP(off) ((unsigned char _based(g_8DFC) *)(off))\n#define SONG(off) (*SONGP(off))', '#define SONG(off) (*dos_audio_song_span((uint8_t *)g_8DFC, (size_t)(uint16_t)midi_song_data_bytes, (uint16_t)(off), 1u))', 'm284A based song macros')
    output = output.replace('SONGP(*midi_active_offset_pointer)[1]', '((SONG(*midi_active_offset_pointer + 1)))')
    output = output.replace('SONGP(pos)[0]', 'SONG(pos)')
    output = output.replace('SONGP(pos)[1]', 'SONG(pos + 1)')
    output = output.replace('SONGP(pos)[2]', 'SONG(pos + 2)')
    if 'SONGP(' in output:
        raise AssertionError('m284A SONGP access was not explicitly converted')
    output = _replace_once(output, 'static _segment g_8DFC;', 'static unsigned char *g_8DFC;', 'm284A song base')
    segment_assignment = 'g_8DFC = ((_segment far *)midi_song_data_handle)[1];'
    if output.count(segment_assignment) != 2:
        raise ValueError('m284A: expected two assignments from the locked handle segment')
    output = output.replace(segment_assignment, 'g_8DFC = (unsigned char *)(*midi_song_data_handle);')
    output = _replace_once(output, 'WinPrintf("Seg=%x, buf=%p, handle=%p", g_8DFC, *midi_song_data_handle, midi_song_data_handle);', 'WinPrintf("Song data=%p, handle=%p", g_8DFC, midi_song_data_handle);', 'm284A segment diagnostic')
    if '_segment' in output or '_based' in output:
        raise AssertionError('m284A segment-only pointer residue')
    output = '#include "portable/whole_program/platform/audio.h"\n\n' + output
    return (output, {'transformed_accesses': original_songp, 'handle_base': 'g_8DFC is the native pointer stored in *midi_song_data_handle after snd_load_song_resources locks the handle', 'record_bound': 'mem_Size returns long in m171C, but m284A declares the call as int and stores it in int midi_song_data_bytes; the source-visible bound is therefore the returned low 16 bits. The host span uses that same uint16_t size and checks each source offset at width 1.', 'invalid_offset_boundary': 'dos_audio_host_song_bounds_fault is called instead of dereferencing outside the recorded song allocation', 'leaves_unprovided': ['dos_audio_host_song_bounds_fault']})

def _convert_277e_pointer(source: str) -> tuple[str, dict[str, Any]]:
    output = _replace_once(source, 'struct Voice {\n    int a;\n    long b;\n};', 'struct Voice {\n    int a;\n    void *b;\n};', 'm277E voice table pointer')
    output = _replace_once(output, '    char far *bios;\n', '    uint8_t bios_signature;\n', 'm277E BIOS signature local')
    output = _replace_once(output, '    bios = (char far *)0xf000fffeL;\n', '', 'm277E far BIOS pointer')
    output = _replace_once(output, '    _asm {\n        mov ax, 8100h\n        int 1Ah\n        cmp ax, 0C4h\n        jne notandy\n        mov base, ax\n    }\n', '    {\n        uint16_t ax = dos_audio_host_bios_int1a_8100();\n        if (ax == 0x00c4)\n            base = (int)ax;\n    }\n', 'm277E BIOS int 1A query')
    output = _replace_once(output, 'notandy:\n', '', 'm277E inline-assembly branch target')
    output = _replace_once(output, '    if (*bios == 0xfc)\n', '    bios_signature = dos_audio_host_read_far_u8(0xf000, 0xfffe);\n    if (bios_signature == 0xfc)\n', 'm277E BIOS signature read')
    output = _replace_once(output, '    _asm {\n        sub bx, bx\n        mov es, bx\n        mov bx, 408h\n        mov ax, es:[bx]\n        mov snd_lpt_dac_port, ax\n        mov dx, snd_lpt_dac_port\n        add dx, 2\n        in al, dx\n        and al, 0F7h\n        out dx, al\n    }\n', '    {\n        uint16_t dx;\n        uint8_t value;\n        snd_lpt_dac_port = (int)dos_audio_host_read_far_u16(0x0040, 0x0008);\n        dx = (uint16_t)(snd_lpt_dac_port + 2);\n        value = dos_audio_host_in8(dx);\n        dos_audio_host_out8(dx, (uint8_t)(value & 0xf7));\n    }\n', 'm277E BIOS data area and timer port access')
    output = _replace_once(output, '    _asm {\n        in al, 61h\n        and al, 0FCh\n        out 61h, al\n    }\n', '    {\n        uint8_t value = dos_audio_host_in8(0x0061);\n        dos_audio_host_out8(0x0061, (uint8_t)(value & 0xfc));\n    }\n', 'm277E speaker gate sequence')
    output = _replace_once(output, '    _asm {\n        mov al, 5\n        out 0Ah, al\n        mov al, 0Fh\n        mov dx, 220h\n        out dx, al\n        mov al, 60h\n        inc dx\n        out dx, al\n    }\n', '    dos_audio_host_out8(0x000a, 0x05);\n    dos_audio_host_out8(0x0220, 0x0f);\n    dos_audio_host_out8(0x0221, 0x60);\n', 'm277E DMA/audio setup writes')
    if '_asm' in output:
        raise AssertionError('m277E hardware assembly residue')
    output = '#include "portable/whole_program/platform/audio.h"\n\n' + output
    return (output, {'field': 'Voice.b', 'source_basis': 'DATA fd_55B3_0C42 and sibling tables are arrays of {int kind, void *p}; m277E copies the second member verbatim in snd_copy_instrument_table and does not perform arithmetic on it', 'native_representation': 'void * in both the source table projection and copied runtime table; target int remains a 16-bit word after standard whole-program lowering', 'source_behavior_changed': False, 'hardware_services': ['dos_audio_host_bios_int1a_8100', 'dos_audio_host_read_far_u8', 'dos_audio_host_read_far_u16', 'dos_audio_host_in8', 'dos_audio_host_out8'], 'host_services_unprovided': True})

def _convert_29d6(source: str) -> tuple[str, dict[str, Any]]:
    output = _replace_once(source, '    int n;\n    int f;', '    int f;', 'm29D6 dead local')
    output = _replace_once(output, '    int tmp;\n', '', 'm29D6 dead temporary')
    output = _replace_once(output, '    reg = (char)ch + 0x80 & 0xe0;', '    reg = (char)(((char)ch + 0x80) & 0xe0);', 'm29D6 explicit channel mask precedence')
    output = _replace_once(output, '    tmp = 0;\n', '', 'm29D6 dead temporary assignment')
    output = _replace_once(output, '    _asm {\n        mov cl, 5\n        shl chan, cl\n    }\n', '    chan = (uint16_t)((uint16_t)chan << 5);\n', 'm29D6 channel shift')
    output = _replace_once(output, '    _asm {\n        mov dx, port\n        mov ax, freq\n        push ax\n        and ax, 0Fh\n        add ax, reg\n        mov bx, ax\n        pop ax\n        and ax, 3F0h\n        mov cx, 4\n        shr ax, cl\n        mov ah, al\n        mov al, bl\n        out dx, ax\n        xor ax, ax\n        mov ax, reg\n        add ax, 10h\n        add ax, val\n        out dx, al\n    }\n', '    {\n        uint16_t reg_word = (uint16_t)(uint8_t)reg;\n        uint8_t high = (uint8_t)((freq & 0x03f0u) >> 4);\n        uint8_t low = (uint8_t)((freq & 0x000fu) + reg_word);\n        uint16_t word_value = (uint16_t)(((uint16_t)high << 8) | low);\n        dos_audio_host_out16((uint16_t)port, word_value);\n        snd_port_write_byte(port, (char)(reg_word + 0x10u + (uint16_t)val));\n    }\n', 'm29D6 two-register frequency output')
    if '_asm' in output:
        raise AssertionError('m29D6 hardware assembly residue')
    output = '#include "portable/whole_program/platform/audio.h"\n\n' + output
    return (output, {'transformed_assembly': ['snd_ps1_set_note channel << 5', 'snd_tandy_set_note 16-bit and 8-bit register outputs'], 'frequency_output': 'snd_tandy_set_note preserves the original masked high-frequency byte, channel/register low byte, output word, then output byte order', 'host_services_unprovided': ['dos_audio_host_out16', 'dos_audio_host_out8']})

def _convert_293a(source: str) -> tuple[str, dict[str, Any]]:
    output = _replace_once(source, '    char far *p;\n    int base;\n\n', '', 'm293A BIOS query locals')
    output = _replace_once(output, '    _asm {\n        mov ah, 81h\n        int 1Ah\n        mov base, ax\n    }\n    p = (char far *)0xfc000000L;\n    return *p == 0x21 || base == 0xc4;\n', '    uint16_t base;\n    uint8_t signature;\n\n    base = dos_audio_host_bios_int1a_8100();\n    signature = dos_audio_host_read_far_u8(0xfc00, 0x0000);\n    return signature == 0x21 || base == 0x00c4;\n', 'm293A INT 1A and BIOS signature test')
    output = _replace_once(output, '    _asm {\n        push es\n        mov ax, 0C000h\n        int 15h\n        add bx, 2\n        mov ax, es:[bx]\n        pop es\n        cmp ax, 0BFCh\n        jne none\n        mov al, 2Fh\n        cli\n        out 70h, al\n        jmp short delay\n    delay:\n        in al, 71h\n        sti\n        test al, 10h\n        je none\n    }\n    return 1;\nnone:\n    return 0;\n', '    uint16_t es;\n    uint16_t bx;\n    uint16_t signature;\n    uint8_t cmos_value;\n\n    dos_audio_host_bios_int15_c000(&es, &bx);\n    bx = (uint16_t)(bx + 2);\n    signature = dos_audio_host_read_far_u16(es, bx);\n    if (signature != 0x0bfc)\n        return 0;\n    dos_audio_host_interrupt_disable();\n    dos_audio_host_out8(0x0070, 0x2f);\n    cmos_value = dos_audio_host_in8(0x0071);\n    dos_audio_host_interrupt_enable();\n    return (cmos_value & 0x10) != 0;\n', 'm293A BIOS descriptor and CMOS probe')
    if '_asm' in output:
        raise AssertionError('m293A hardware assembly residue')
    output = '#include "portable/whole_program/platform/audio.h"\n\n' + output
    return (output, {'transformed_assembly': ['snd_probe_tandy_sound INT 1A BIOS base and far signature read', 'snd_probe_ps1_sound INT 15 descriptor plus CMOS register 2F read'], 'result_policy': 'device predicates are returned only from the original BIOS/signature/CMOS host service results; no provider means unresolved service, never assumed success', 'host_services_unprovided': ['dos_audio_host_bios_int1a_8100', 'dos_audio_host_bios_int15_c000', 'dos_audio_host_read_far_u8', 'dos_audio_host_read_far_u16', 'dos_audio_host_interrupt_disable', 'dos_audio_host_interrupt_enable', 'dos_audio_host_out8', 'dos_audio_host_in8']})

def _convert_290d(source: str) -> tuple[str, dict[str, Any]]:
    # The source ISR projection consumes the canonical channel record directly.
    # No copied event/voice model or changes to the source start/stop algorithm.
    return (source, {'status': 'UNCHANGED_SOURCE_CHANNEL_COMMITS',
                     'consumer': 'portable/whole_program/platform/whole_audio_provider.c'})

def adapt(path: str, source: str) -> tuple[str, dict[str, Any]]:
    """Convert one canonical audio source using explicit ABI shape checks."""
    normalized = path.replace('\\', '/')
    source_sha = _sha(source)
    if normalized == 'src/platform/port_io.c':
        (output, change) = _convert_29f0(source)
    elif normalized == 'src/sound/midi_player.c':
        (output, change) = _convert_284a(source)
    elif normalized == 'src/sound/device_channels.c':
        (output, change) = _convert_277e_pointer(source)
    elif normalized == 'src/sound/psg_voices.c':
        (output, change) = _convert_29d6(source)
    elif normalized == 'src/sound/device_probe.c':
        (output, change) = _convert_293a(source)
    elif normalized == 'src/sound/sample_voices.c':
        (output, change) = _convert_290d(source)
    else:
        output = source
        change = {'status': 'UNCHANGED_PENDING_DEVICE_BOUNDARIES', 'source_scan': 'inline assembly contains BIOS interrupts, direct physical reads, device-status polling, or mixed-width port I/O; no simulator or detection result is substituted', 'host_capabilities': 'unprovided'}
    ledger = {'schema': 'whole-program-audio-conversion-v1', 'source': {'path': normalized, 'sha256': source_sha}, 'dependency_anchors': DEPENDENCY_ANCHORS.get(normalized, []), 'output_sha256': _sha(output), 'change': change}
    return (output, ledger)
