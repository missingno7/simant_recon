from __future__ import annotations
import hashlib
from typing import Any
DEPENDENCY_ANCHORS = {'src/root/m284A.c': [{'path': 'src/root/m0000.c', 'role': 'f_0000_0193 obtains the song resource, locks its handle, and stores the handle in Song.data before m284A reads it'}, {'path': 'src/root/m171C.c', 'role': "f_171C_1C1C returns the handle size as long; m284A's own int declaration/store retain the low 16-bit source-visible bound"}], 'src/root/m277E.c': [{'path': 'src/data/d55B3_00B8.c', 'role': 'struct Instr declares void *p and the referenced 56-entry voice tables use that native pointer member'}], 'src/root/m290D.c': [{'path': 'src/root/m0000.c', 'role': 'f_0000_0090 stores the kind-5 decoded sample Handle in Sample.data; the native sample event dereferences that handle exactly once to borrow decoded PCM before copying it'}, {'path': 'src/data/d55B3_00B8.c', 'role': 'fd_55B3_0C42 and mode-specific sibling tables bind type-1 instrument entries to source Sample records consumed by f_290D_0193'}]}

def _sha(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def _replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise ValueError(f'{label}: expected one exact source form, found {count}')
    return source.replace(old, new, 1)

def _convert_29f0(source: str) -> tuple[str, dict[str, Any]]:
    if source.count('_asm') != 6:
        raise ValueError('m29F0: expected six original inline assembly bodies')
    forms = [('void far f_29F0_000A(void)\n{\n    _asm cli\n}', 'void far f_29F0_000A(void)\n{\n    dos_audio_host_interrupt_disable();\n}'), ('void far f_29F0_0012(void)\n{\n    _asm sti\n}', 'void far f_29F0_0012(void)\n{\n    dos_audio_host_interrupt_enable();\n}'), ('void far f_29F0_001A(void)\n{\n    _asm cli\n}', 'void far f_29F0_001A(void)\n{\n    dos_audio_host_interrupt_disable();\n}'), ('void far f_29F0_0022(void)\n{\n    _asm sti\n}', 'void far f_29F0_0022(void)\n{\n    dos_audio_host_interrupt_enable();\n}'), ('void far f_29F0_002A(int port, int value)\n{\n    _asm {\n        mov dx, port\n        mov al, byte ptr value\n        out dx, al\n    }\n}', 'void far f_29F0_002A(int port, int value)\n{\n    dos_audio_host_out8((uint16_t)port, (uint8_t)value);\n}'), ('unsigned char far f_29F0_0038(int port)\n{\n    unsigned char value;\n\n    _asm {\n        mov dx, port\n        in al, dx\n        mov value, al\n    }\n    return value;\n}', 'unsigned char far f_29F0_0038(int port)\n{\n    return dos_audio_host_in8((uint16_t)port);\n}')]
    output = source
    for (old, new) in forms:
        output = _replace_once(output, old, new, 'm29F0 helper')
    if '_asm' in output:
        raise AssertionError('m29F0 assembly residue')
    output = '#include "portable/whole_program/platform/audio.h"\n\n' + output
    return (output, {'transformed_functions': ['f_29F0_000A', 'f_29F0_0012', 'f_29F0_001A', 'f_29F0_0022', 'f_29F0_002A', 'f_29F0_0038'], 'source_operations': {'cli': 'dos_audio_host_interrupt_disable()', 'sti': 'dos_audio_host_interrupt_enable()', 'out': 'DX receives the low word of port; AL receives the low byte of value; host call uses uint16_t/uint8_t', 'in': 'DX receives the low word of port; returned AL byte is provided by dos_audio_host_in8'}, 'leaves_unprovided': ['dos_audio_host_interrupt_disable', 'dos_audio_host_interrupt_enable', 'dos_audio_host_out8', 'dos_audio_host_in8']})

def _convert_284a(source: str) -> tuple[str, dict[str, Any]]:
    original_songp = source.count('SONGP(')
    if original_songp != 6:
        raise ValueError(f'm284A: expected six SONGP source forms, found {original_songp}')
    output = source
    output = _replace_once(output, '#define SONGP(off) ((unsigned char _based(g_8DFC) *)(off))\n#define SONG(off) (*SONGP(off))', '#define SONG(off) (*dos_audio_song_span((uint8_t *)g_8DFC, (size_t)(uint16_t)fd_50F6_4B2C, (uint16_t)(off), 1u))', 'm284A based song macros')
    output = output.replace('SONGP(*g_8DFE)[1]', '((SONG(*g_8DFE + 1)))')
    output = output.replace('SONGP(pos)[0]', 'SONG(pos)')
    output = output.replace('SONGP(pos)[1]', 'SONG(pos + 1)')
    output = output.replace('SONGP(pos)[2]', 'SONG(pos + 2)')
    if 'SONGP(' in output:
        raise AssertionError('m284A SONGP access was not explicitly converted')
    output = _replace_once(output, 'static _segment g_8DFC;', 'static unsigned char *g_8DFC;', 'm284A song base')
    segment_assignment = 'g_8DFC = ((_segment far *)fd_50F6_4B28)[1];'
    if output.count(segment_assignment) != 2:
        raise ValueError('m284A: expected two assignments from the locked handle segment')
    output = output.replace(segment_assignment, 'g_8DFC = (unsigned char *)(*fd_50F6_4B28);')
    output = _replace_once(output, 'WinPrintf("Seg=%x, buf=%p, handle=%p", g_8DFC, *fd_50F6_4B28, fd_50F6_4B28);', 'WinPrintf("Song data=%p, handle=%p", g_8DFC, fd_50F6_4B28);', 'm284A segment diagnostic')
    if '_segment' in output or '_based' in output:
        raise AssertionError('m284A segment-only pointer residue')
    output = '#include "portable/whole_program/platform/audio.h"\n\n' + output
    return (output, {'transformed_accesses': original_songp, 'handle_base': 'g_8DFC is the native pointer stored in *fd_50F6_4B28 after f_0000_0193 locks the handle', 'record_bound': 'f_171C_1C1C returns long in m171C, but m284A declares the call as int and stores it in int fd_50F6_4B2C; the source-visible bound is therefore the returned low 16 bits. The host span uses that same uint16_t size and checks each source offset at width 1.', 'invalid_offset_boundary': 'dos_audio_host_song_bounds_fault is called instead of dereferencing outside the recorded song allocation', 'leaves_unprovided': ['dos_audio_host_song_bounds_fault']})

def _convert_277e_pointer(source: str) -> tuple[str, dict[str, Any]]:
    output = _replace_once(source, 'struct Voice {\n    int a;\n    long b;\n};', 'struct Voice {\n    int a;\n    void *b;\n};', 'm277E voice table pointer')
    output = _replace_once(output, '    char far *bios;\n', '    uint8_t bios_signature;\n', 'm277E BIOS signature local')
    output = _replace_once(output, '    bios = (char far *)0xF000FFFEL;\n', '', 'm277E far BIOS pointer')
    output = _replace_once(output, '    _asm {\n        mov ax, 8100h\n        int 1Ah\n        cmp ax, 0C4h\n        jne notandy\n        mov base, ax\n    }\n', '    {\n        uint16_t ax = dos_audio_host_bios_int1a_8100();\n        if (ax == 0x00c4)\n            base = (int)ax;\n    }\n', 'm277E BIOS int 1A query')
    output = _replace_once(output, 'notandy:\n', '', 'm277E inline-assembly branch target')
    output = _replace_once(output, '    if (*bios == 0xfc)\n', '    bios_signature = dos_audio_host_read_far_u8(0xf000, 0xfffe);\n    if (bios_signature == 0xfc)\n', 'm277E BIOS signature read')
    output = _replace_once(output, '    _asm {\n        sub bx, bx\n        mov es, bx\n        mov bx, 408h\n        mov ax, es:[bx]\n        mov g_693C, ax\n        mov dx, g_693C\n        add dx, 2\n        in al, dx\n        and al, 0F7h\n        out dx, al\n    }\n', '    {\n        uint16_t dx;\n        uint8_t value;\n        g_693C = (int)dos_audio_host_read_far_u16(0x0040, 0x0008);\n        dx = (uint16_t)(g_693C + 2);\n        value = dos_audio_host_in8(dx);\n        dos_audio_host_out8(dx, (uint8_t)(value & 0xf7));\n    }\n', 'm277E BIOS data area and timer port access')
    output = _replace_once(output, '    _asm {\n        in al, 61h\n        and al, 0FCh\n        out 61h, al\n    }\n', '    {\n        uint8_t value = dos_audio_host_in8(0x0061);\n        dos_audio_host_out8(0x0061, (uint8_t)(value & 0xfc));\n    }\n', 'm277E speaker gate sequence')
    output = _replace_once(output, '    _asm {\n        mov al, 5\n        out 0Ah, al\n        mov al, 0Fh\n        mov dx, 220h\n        out dx, al\n        mov al, 60h\n        inc dx\n        out dx, al\n    }\n', '    dos_audio_host_out8(0x000a, 0x05);\n    dos_audio_host_out8(0x0220, 0x0f);\n    dos_audio_host_out8(0x0221, 0x60);\n', 'm277E DMA/audio setup writes')
    if '_asm' in output:
        raise AssertionError('m277E hardware assembly residue')
    output = '#include "portable/whole_program/platform/audio.h"\n\n' + output
    return (output, {'field': 'Voice.b', 'source_basis': 'DATA fd_55B3_0C42 and sibling tables are arrays of {int kind, void *p}; m277E copies the second member verbatim in f_277E_010A and does not perform arithmetic on it', 'native_representation': 'void * in both the source table projection and copied runtime table; target int remains a 16-bit word after standard whole-program lowering', 'source_behavior_changed': False, 'hardware_services': ['dos_audio_host_bios_int1a_8100', 'dos_audio_host_read_far_u8', 'dos_audio_host_read_far_u16', 'dos_audio_host_in8', 'dos_audio_host_out8'], 'host_services_unprovided': True})

def _convert_29d6(source: str) -> tuple[str, dict[str, Any]]:
    output = _replace_once(source, '    int n;\n    int f;', '    int f;', 'm29D6 dead local')
    output = _replace_once(output, '    int tmp;\n', '', 'm29D6 dead temporary')
    output = _replace_once(output, '    reg = (char)ch + 0x80 & 0xe0;', '    reg = (char)(((char)ch + 0x80) & 0xe0);', 'm29D6 explicit channel mask precedence')
    output = _replace_once(output, '    tmp = 0;\n', '', 'm29D6 dead temporary assignment')
    output = _replace_once(output, '    _asm {\n        mov cl, 5\n        shl chan, cl\n    }\n', '    chan = (uint16_t)((uint16_t)chan << 5);\n', 'm29D6 channel shift')
    output = _replace_once(output, '    _asm {\n        mov dx, port\n        mov ax, freq\n        push ax\n        and ax, 0Fh\n        add ax, reg\n        mov bx, ax\n        pop ax\n        and ax, 3F0h\n        mov cx, 4\n        shr ax, cl\n        mov ah, al\n        mov al, bl\n        out dx, ax\n        xor ax, ax\n        mov ax, reg\n        add ax, 10h\n        add ax, val\n        out dx, al\n    }\n', '    {\n        uint16_t reg_word = (uint16_t)(uint8_t)reg;\n        uint8_t high = (uint8_t)((freq & 0x03f0u) >> 4);\n        uint8_t low = (uint8_t)((freq & 0x000fu) + reg_word);\n        uint16_t word_value = (uint16_t)(((uint16_t)high << 8) | low);\n        dos_audio_host_out16((uint16_t)port, word_value);\n        f_29F0_002A(port, (char)(reg_word + 0x10u + (uint16_t)val));\n    }\n', 'm29D6 two-register frequency output')
    if '_asm' in output:
        raise AssertionError('m29D6 hardware assembly residue')
    output = '#include "portable/whole_program/platform/audio.h"\n\n' + output
    return (output, {'transformed_assembly': ['f_29D6_000A channel << 5', 'f_29D6_00D9 16-bit and 8-bit register outputs'], 'frequency_output': 'f_29D6_00D9 preserves the original masked high-frequency byte, channel/register low byte, output word, then output byte order', 'host_services_unprovided': ['dos_audio_host_out16', 'dos_audio_host_out8']})

def _convert_293a(source: str) -> tuple[str, dict[str, Any]]:
    output = _replace_once(source, '    char far *p;\n    int base;\n\n', '', 'm293A BIOS query locals')
    output = _replace_once(output, '    _asm {\n        mov ah, 81h\n        int 1Ah\n        mov base, ax\n    }\n    p = (char far *)0xFC000000L;\n    return *p == 0x21 || base == 0xc4;\n', '    uint16_t base;\n    uint8_t signature;\n\n    base = dos_audio_host_bios_int1a_8100();\n    signature = dos_audio_host_read_far_u8(0xfc00, 0x0000);\n    return signature == 0x21 || base == 0x00c4;\n', 'm293A INT 1A and BIOS signature test')
    output = _replace_once(output, '    _asm {\n        push es\n        mov ax, 0C000h\n        int 15h\n        add bx, 2\n        mov ax, es:[bx]\n        pop es\n        cmp ax, 0BFCh\n        jne none\n        mov al, 2Fh\n        cli\n        out 70h, al\n        jmp short delay\n    delay:\n        in al, 71h\n        sti\n        test al, 10h\n        je none\n    }\n    return 1;\nnone:\n    return 0;\n', '    uint16_t es;\n    uint16_t bx;\n    uint16_t signature;\n    uint8_t cmos_value;\n\n    dos_audio_host_bios_int15_c000(&es, &bx);\n    bx = (uint16_t)(bx + 2);\n    signature = dos_audio_host_read_far_u16(es, bx);\n    if (signature != 0x0bfc)\n        return 0;\n    dos_audio_host_interrupt_disable();\n    dos_audio_host_out8(0x0070, 0x2f);\n    cmos_value = dos_audio_host_in8(0x0071);\n    dos_audio_host_interrupt_enable();\n    return (cmos_value & 0x10) != 0;\n', 'm293A BIOS descriptor and CMOS probe')
    if '_asm' in output:
        raise AssertionError('m293A hardware assembly residue')
    output = '#include "portable/whole_program/platform/audio.h"\n\n' + output
    return (output, {'transformed_assembly': ['f_293A_002D INT 1A BIOS base and far signature read', 'f_293A_0059 INT 15 descriptor plus CMOS register 2F read'], 'result_policy': 'device predicates are returned only from the original BIOS/signature/CMOS host service results; no provider means unresolved service, never assumed success', 'host_services_unprovided': ['dos_audio_host_bios_int1a_8100', 'dos_audio_host_bios_int15_c000', 'dos_audio_host_read_far_u8', 'dos_audio_host_read_far_u16', 'dos_audio_host_interrupt_disable', 'dos_audio_host_interrupt_enable', 'dos_audio_host_out8', 'dos_audio_host_in8']})

def _convert_290d(source: str) -> tuple[str, dict[str, Any]]:
    output = _replace_once(source, '    f_29F0_0012();\n    f_28BC_03CC();\n}', '    {\n        const uint8_t *sample_pcm =\n            (const uint8_t *)(*(char far * far *)s->data);\n        PortableWholeAudioEventStatus event_status = portable_whole_audio_sample_start(\n            (unsigned)ch, sample_pcm, (uint16_t)s->len, (uint16_t)s->loop,\n            (uint16_t)step, (unsigned)vol, s->looped != 0);\n        if (event_status != PORTABLE_WHOLE_AUDIO_EVENT_OK)\n            portable_whole_audio_event_fault(event_status);\n    }\n    f_29F0_0012();\n    f_28BC_03CC();\n}', 'm290D source DAC start event boundary')
    output = _replace_once(output, '    fd_55B3_6B4C[ch].snd = fd_55B3_6B4C[ch].owner = 0;\n    f_29F0_0012();', '    fd_55B3_6B4C[ch].snd = fd_55B3_6B4C[ch].owner = 0;\n    {\n        PortableWholeAudioEventStatus event_status =\n            portable_whole_audio_sample_stop((unsigned)ch);\n        if (event_status != PORTABLE_WHOLE_AUDIO_EVENT_OK)\n            portable_whole_audio_event_fault(event_status);\n    }\n    f_29F0_0012();', 'm290D source DAC stop event boundary')
    output = '#include "portable/whole_program/platform/audio_events.h"\n\n' + output
    return (output, {'transformed_source_boundaries': ['f_290D_0098 successful decoded-sample/channel commit', 'f_290D_026C channel stop/owner clear'], 'event_order': 'The synchronous whole-program sequencer and source voice allocator call these original source functions in order; the event queue assigns one increasing sequence across starts and stops.', 'sample_view': 'f_0000_0090 stores a decoded kind-5 Handle in Sample.data. The callback dereferences that Handle once while its resource remains owned, and the queue copies exactly the low-16-bit Sample.len bytes before returning.', 'source_parameters': 'channel, decoded bytes, Sample.len, Sample.loop, computed 8.8 step, computed volume-table row, and looped flag are passed unchanged at the start commit; stop identifies the source channel.', 'unbound_policy': 'source event queue not bound, exhausted, or given invalid source sample state calls the explicit audio event fault; no silent success is reported', 'leaves_unprovided': ['MIDI/OPL event backends for type-2 and other non-DAC channel families']})

def adapt(path: str, source: str) -> tuple[str, dict[str, Any]]:
    """Convert one canonical audio source using explicit ABI shape checks."""
    normalized = path.replace('\\', '/')
    source_sha = _sha(source)
    if normalized == 'src/root/m29F0.c':
        (output, change) = _convert_29f0(source)
    elif normalized == 'src/root/m284A.c':
        (output, change) = _convert_284a(source)
    elif normalized == 'src/root/m277E.c':
        (output, change) = _convert_277e_pointer(source)
    elif normalized == 'src/root/m29D6.c':
        (output, change) = _convert_29d6(source)
    elif normalized == 'src/root/m293A.c':
        (output, change) = _convert_293a(source)
    elif normalized == 'src/root/m290D.c':
        (output, change) = _convert_290d(source)
    else:
        output = source
        change = {'status': 'UNCHANGED_PENDING_DEVICE_BOUNDARIES', 'source_scan': 'inline assembly contains BIOS interrupts, direct physical reads, device-status polling, or mixed-width port I/O; no simulator or detection result is substituted', 'host_capabilities': 'unprovided'}
    ledger = {'schema': 'whole-program-audio-conversion-v1', 'source': {'path': normalized, 'sha256': source_sha}, 'dependency_anchors': DEPENDENCY_ANCHORS.get(normalized, []), 'output_sha256': _sha(output), 'change': change}
    return (output, ledger)
