"""Source-identity-checked mechanical conversion for DOS audio TUs.

Only host boundary spelling and pointer representation change here. Hardware
providers remain declarations, never simulated devices. The sound-device
modules with additional BIOS/port sequences are audited but intentionally
left unchanged for a later bounded conversion.
"""
from __future__ import annotations

import hashlib
import re
from typing import Any

SOURCE_HASHES = {
    "src/root/m29F0.c": "2787050f6b809856cde2d2a60fe120357a195041d396bb55caf7dd1b8084e302",
    "src/root/m284A.c": "bad7d3701a853ba2de166e4f875ba3043f33ca136b7d0dcff41db8e5459f9fa5",
    "src/root/m277E.c": "4e928689c743f473c5a007bbbbb5287cdf8728d12e9cae5652b1cb55debf09ee",
    "src/root/m29D6.c": "55476efe4ad6d0cd853cd794f731ff8f33df921577e092fc3e80e9b322b4c388",
    "src/root/m293A.c": "601b4e4e9e8b9d128cc97cca3da7dcf0ad863dbb5c6df587c601530cbe4ec5e6",
    "src/root/m290D.c": "eaec23e8d37bd606616dc44208c7bbcf82ced13e24abe0362ef767c5e4cc4fed",
}

DEPENDENCY_PINS = {
    "src/root/m284A.c": [
        {
            "path": "src/root/m0000.c",
            "sha256": "d9ccffbb69c4fdcae55eef918bf420cff81ead6849f67298271c2844e04199f9",
            "role": "f_0000_0193 obtains the song resource, locks its handle, and stores the handle in Song.data before m284A reads it",
        },
        {
            "path": "src/root/m171C.c",
            "sha256": "31bd9caa243220db2bd1ba940ac8fae7f5d189b2ec95f1662918e9ca2160b10e",
            "role": "f_171C_1C1C returns the handle size as long; m284A's own int declaration/store retain the low 16-bit source-visible bound",
        },
    ],
    "src/root/m277E.c": [
        {
            "path": "src/data/d55B3_00B8.c",
            "sha256": "d04646a28691ff05ad93a50c5e7142405ab64932f875f2d2a4d10d04a4566f3d",
            "role": "struct Instr declares void *p and the referenced 56-entry voice tables use that native pointer member",
        },
    ],
    "src/root/m290D.c": [
        {
            "path": "src/root/m0000.c",
            "sha256": "d9ccffbb69c4fdcae55eef918bf420cff81ead6849f67298271c2844e04199f9",
            "role": "f_0000_0090 stores the kind-5 decoded sample Handle in Sample.data; the native sample event dereferences that handle exactly once to borrow decoded PCM before copying it",
        },
        {
            "path": "src/data/d55B3_00B8.c",
            "sha256": "d04646a28691ff05ad93a50c5e7142405ab64932f875f2d2a4d10d04a4566f3d",
            "role": "fd_55B3_0C42 and mode-specific sibling tables bind type-1 instrument entries to source Sample records consumed by f_290D_0193",
        },
    ],
}


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise ValueError(f"{label}: expected one exact source form, found {count}")
    return source.replace(old, new, 1)


def _convert_29f0(source: str) -> tuple[str, dict[str, Any]]:
    if source.count("_asm") != 6:
        raise ValueError("m29F0: expected six original inline assembly bodies")
    forms = [
        ("void far f_29F0_000A(void)\n{\n    _asm cli\n}",
         "void far f_29F0_000A(void)\n{\n    dos_audio_host_interrupt_disable();\n}"),
        ("void far f_29F0_0012(void)\n{\n    _asm sti\n}",
         "void far f_29F0_0012(void)\n{\n    dos_audio_host_interrupt_enable();\n}"),
        ("void far f_29F0_001A(void)\n{\n    _asm cli\n}",
         "void far f_29F0_001A(void)\n{\n    dos_audio_host_interrupt_disable();\n}"),
        ("void far f_29F0_0022(void)\n{\n    _asm sti\n}",
         "void far f_29F0_0022(void)\n{\n    dos_audio_host_interrupt_enable();\n}"),
        ("void far f_29F0_002A(int port, int value)\n{\n    _asm {\n        mov dx, port\n        mov al, byte ptr value\n        out dx, al\n    }\n}",
         "void far f_29F0_002A(int port, int value)\n{\n    dos_audio_host_out8((uint16_t)port, (uint8_t)value);\n}"),
        ("unsigned char far f_29F0_0038(int port)\n{\n    unsigned char value;\n\n    _asm {\n        mov dx, port\n        in al, dx\n        mov value, al\n    }\n    return value;\n}",
         "unsigned char far f_29F0_0038(int port)\n{\n    return dos_audio_host_in8((uint16_t)port);\n}"),
    ]
    output = source
    for old, new in forms:
        output = _replace_once(output, old, new, "m29F0 helper")
    if "_asm" in output:
        raise AssertionError("m29F0 assembly residue")
    output = '#include "portable/whole_program/platform/audio.h"\n\n' + output
    return output, {
        "transformed_functions": ["f_29F0_000A", "f_29F0_0012", "f_29F0_001A",
                                  "f_29F0_0022", "f_29F0_002A", "f_29F0_0038"],
        "source_operations": {
            "cli": "dos_audio_host_interrupt_disable()",
            "sti": "dos_audio_host_interrupt_enable()",
            "out": "DX receives the low word of port; AL receives the low byte of value; host call uses uint16_t/uint8_t",
            "in": "DX receives the low word of port; returned AL byte is provided by dos_audio_host_in8",
        },
        "leaves_unprovided": ["dos_audio_host_interrupt_disable", "dos_audio_host_interrupt_enable",
                              "dos_audio_host_out8", "dos_audio_host_in8"],
    }


def _convert_284a(source: str) -> tuple[str, dict[str, Any]]:
    original_songp = source.count("SONGP(")
    if original_songp != 6:
        raise ValueError(f"m284A: expected six SONGP source forms, found {original_songp}")
    output = source
    output = _replace_once(output,
        "#define SONGP(off) ((unsigned char _based(g_8DFC) *)(off))\n#define SONG(off) (*SONGP(off))",
        "#define SONG(off) (*dos_audio_song_span((uint8_t *)g_8DFC, (size_t)(uint16_t)fd_50F6_4B2C, (uint16_t)(off), 1u))",
        "m284A based song macros")
    output = output.replace("SONGP(*g_8DFE)[1]", "((SONG(*g_8DFE + 1)))")
    output = output.replace("SONGP(pos)[0]", "SONG(pos)")
    output = output.replace("SONGP(pos)[1]", "SONG(pos + 1)")
    output = output.replace("SONGP(pos)[2]", "SONG(pos + 2)")
    if "SONGP(" in output:
        raise AssertionError("m284A SONGP access was not explicitly converted")
    output = _replace_once(output, "static _segment g_8DFC;",
                           "static unsigned char *g_8DFC;", "m284A song base")
    segment_assignment = "g_8DFC = ((_segment far *)fd_50F6_4B28)[1];"
    if output.count(segment_assignment) != 2:
        raise ValueError("m284A: expected two assignments from the locked handle segment")
    output = output.replace(segment_assignment,
                            "g_8DFC = (unsigned char *)(*fd_50F6_4B28);")
    output = _replace_once(output,
        'WinPrintf("Seg=%x, buf=%p, handle=%p", g_8DFC, *fd_50F6_4B28, fd_50F6_4B28);',
        'WinPrintf("Song data=%p, handle=%p", g_8DFC, fd_50F6_4B28);',
        "m284A segment diagnostic")
    if "_segment" in output or "_based" in output:
        raise AssertionError("m284A segment-only pointer residue")
    output = '#include "portable/whole_program/platform/audio.h"\n\n' + output
    return output, {
        "transformed_accesses": original_songp,
        "handle_base": "g_8DFC is the native pointer stored in *fd_50F6_4B28 after f_0000_0193 locks the handle",
        "record_bound": "f_171C_1C1C returns long in m171C, but m284A declares the call as int and stores it in int fd_50F6_4B2C; the source-visible bound is therefore the returned low 16 bits. The host span uses that same uint16_t size and checks each source offset at width 1.",
        "invalid_offset_boundary": "dos_audio_host_song_bounds_fault is called instead of dereferencing outside the recorded song allocation",
        "leaves_unprovided": ["dos_audio_host_song_bounds_fault"],
    }


def _convert_277e_pointer(source: str) -> tuple[str, dict[str, Any]]:
    output = _replace_once(source, "struct Voice {\n    int a;\n    long b;\n};",
        "struct Voice {\n    int a;\n    void *b;\n};", "m277E voice table pointer")
    output = _replace_once(output, "    char far *bios;\n", "    uint8_t bios_signature;\n",
                           "m277E BIOS signature local")
    output = _replace_once(output, "    bios = (char far *)0xF000FFFEL;\n", "",
                           "m277E far BIOS pointer")
    output = _replace_once(output, """    _asm {
        mov ax, 8100h
        int 1Ah
        cmp ax, 0C4h
        jne notandy
        mov base, ax
    }
""", """    {
        uint16_t ax = dos_audio_host_bios_int1a_8100();
        if (ax == 0x00c4)
            base = (int)ax;
    }
""", "m277E BIOS int 1A query")
    output = _replace_once(output, "notandy:\n", "", "m277E inline-assembly branch target")
    output = _replace_once(output, "    if (*bios == 0xfc)\n", "    bios_signature = dos_audio_host_read_far_u8(0xf000, 0xfffe);\n    if (bios_signature == 0xfc)\n",
                           "m277E BIOS signature read")
    output = _replace_once(output, """    _asm {
        sub bx, bx
        mov es, bx
        mov bx, 408h
        mov ax, es:[bx]
        mov g_693C, ax
        mov dx, g_693C
        add dx, 2
        in al, dx
        and al, 0F7h
        out dx, al
    }
""", """    {
        uint16_t dx;
        uint8_t value;
        g_693C = (int)dos_audio_host_read_far_u16(0x0040, 0x0008);
        dx = (uint16_t)(g_693C + 2);
        value = dos_audio_host_in8(dx);
        dos_audio_host_out8(dx, (uint8_t)(value & 0xf7));
    }
""", "m277E BIOS data area and timer port access")
    output = _replace_once(output, """    _asm {
        in al, 61h
        and al, 0FCh
        out 61h, al
    }
""", """    {
        uint8_t value = dos_audio_host_in8(0x0061);
        dos_audio_host_out8(0x0061, (uint8_t)(value & 0xfc));
    }
""", "m277E speaker gate sequence")
    output = _replace_once(output, """    _asm {
        mov al, 5
        out 0Ah, al
        mov al, 0Fh
        mov dx, 220h
        out dx, al
        mov al, 60h
        inc dx
        out dx, al
    }
""", """    dos_audio_host_out8(0x000a, 0x05);
    dos_audio_host_out8(0x0220, 0x0f);
    dos_audio_host_out8(0x0221, 0x60);
""", "m277E DMA/audio setup writes")
    if "_asm" in output:
        raise AssertionError("m277E hardware assembly residue")
    output = '#include "portable/whole_program/platform/audio.h"\n\n' + output
    return output, {
        "field": "Voice.b",
        "source_basis": "DATA fd_55B3_0C42 and sibling tables are arrays of {int kind, void *p}; m277E copies the second member verbatim in f_277E_010A and does not perform arithmetic on it",
        "native_representation": "void * in both the source table projection and copied runtime table; target int remains a 16-bit word after standard whole-program lowering",
        "source_behavior_changed": False,
        "hardware_services": ["dos_audio_host_bios_int1a_8100", "dos_audio_host_read_far_u8",
                              "dos_audio_host_read_far_u16", "dos_audio_host_in8",
                              "dos_audio_host_out8"],
        "host_services_unprovided": True,
    }


def _convert_29d6(source: str) -> tuple[str, dict[str, Any]]:
    output = _replace_once(source, "    int n;\n    int f;", "    int f;", "m29D6 dead local")
    output = _replace_once(output, "    int tmp;\n", "", "m29D6 dead temporary")
    output = _replace_once(output, "    reg = (char)ch + 0x80 & 0xe0;",
                           "    reg = (char)(((char)ch + 0x80) & 0xe0);",
                           "m29D6 explicit channel mask precedence")
    output = _replace_once(output, "    tmp = 0;\n", "", "m29D6 dead temporary assignment")
    output = _replace_once(output, """    _asm {
        mov cl, 5
        shl chan, cl
    }
""", "    chan = (uint16_t)((uint16_t)chan << 5);\n",
        "m29D6 channel shift")
    output = _replace_once(output, """    _asm {
        mov dx, port
        mov ax, freq
        push ax
        and ax, 0Fh
        add ax, reg
        mov bx, ax
        pop ax
        and ax, 3F0h
        mov cx, 4
        shr ax, cl
        mov ah, al
        mov al, bl
        out dx, ax
        xor ax, ax
        mov ax, reg
        add ax, 10h
        add ax, val
        out dx, al
    }
""", """    {
        uint16_t reg_word = (uint16_t)(uint8_t)reg;
        uint8_t high = (uint8_t)((freq & 0x03f0u) >> 4);
        uint8_t low = (uint8_t)((freq & 0x000fu) + reg_word);
        uint16_t word_value = (uint16_t)(((uint16_t)high << 8) | low);
        dos_audio_host_out16((uint16_t)port, word_value);
        f_29F0_002A(port, (char)(reg_word + 0x10u + (uint16_t)val));
    }
""", "m29D6 two-register frequency output")
    if "_asm" in output:
        raise AssertionError("m29D6 hardware assembly residue")
    output = '#include "portable/whole_program/platform/audio.h"\n\n' + output
    return output, {
        "transformed_assembly": ["f_29D6_000A channel << 5", "f_29D6_00D9 16-bit and 8-bit register outputs"],
        "frequency_output": "f_29D6_00D9 preserves the original masked high-frequency byte, channel/register low byte, output word, then output byte order",
        "host_services_unprovided": ["dos_audio_host_out16", "dos_audio_host_out8"],
    }


def _convert_293a(source: str) -> tuple[str, dict[str, Any]]:
    output = _replace_once(source, "    char far *p;\n    int base;\n\n", "",
                           "m293A BIOS query locals")
    output = _replace_once(output, """    _asm {
        mov ah, 81h
        int 1Ah
        mov base, ax
    }
    p = (char far *)0xFC000000L;
    return *p == 0x21 || base == 0xc4;
""", """    uint16_t base;
    uint8_t signature;

    base = dos_audio_host_bios_int1a_8100();
    signature = dos_audio_host_read_far_u8(0xfc00, 0x0000);
    return signature == 0x21 || base == 0x00c4;
""", "m293A INT 1A and BIOS signature test")
    output = _replace_once(output, """    _asm {
        push es
        mov ax, 0C000h
        int 15h
        add bx, 2
        mov ax, es:[bx]
        pop es
        cmp ax, 0BFCh
        jne none
        mov al, 2Fh
        cli
        out 70h, al
        jmp short delay
    delay:
        in al, 71h
        sti
        test al, 10h
        je none
    }
    return 1;
none:
    return 0;
""", """    uint16_t es;
    uint16_t bx;
    uint16_t signature;
    uint8_t cmos_value;

    dos_audio_host_bios_int15_c000(&es, &bx);
    bx = (uint16_t)(bx + 2);
    signature = dos_audio_host_read_far_u16(es, bx);
    if (signature != 0x0bfc)
        return 0;
    dos_audio_host_interrupt_disable();
    dos_audio_host_out8(0x0070, 0x2f);
    cmos_value = dos_audio_host_in8(0x0071);
    dos_audio_host_interrupt_enable();
    return (cmos_value & 0x10) != 0;
""", "m293A BIOS descriptor and CMOS probe")
    if "_asm" in output:
        raise AssertionError("m293A hardware assembly residue")
    output = '#include "portable/whole_program/platform/audio.h"\n\n' + output
    return output, {
        "transformed_assembly": ["f_293A_002D INT 1A BIOS base and far signature read",
                                 "f_293A_0059 INT 15 descriptor plus CMOS register 2F read"],
        "result_policy": "device predicates are returned only from the original BIOS/signature/CMOS host service results; no provider means unresolved service, never assumed success",
        "host_services_unprovided": ["dos_audio_host_bios_int1a_8100", "dos_audio_host_bios_int15_c000",
                                     "dos_audio_host_read_far_u8", "dos_audio_host_read_far_u16",
                                     "dos_audio_host_interrupt_disable", "dos_audio_host_interrupt_enable",
                                     "dos_audio_host_out8", "dos_audio_host_in8"],
    }


def _convert_290d(source: str) -> tuple[str, dict[str, Any]]:
    output = _replace_once(source,
        "    f_29F0_0012();\n    f_28BC_03CC();\n}",
        """    {
        const uint8_t *sample_pcm =
            (const uint8_t *)(*(char far * far *)s->data);
        PortableWholeAudioEventStatus event_status = portable_whole_audio_sample_start(
            (unsigned)ch, sample_pcm, (uint16_t)s->len, (uint16_t)s->loop,
            (uint16_t)step, (unsigned)vol, s->looped != 0);
        if (event_status != PORTABLE_WHOLE_AUDIO_EVENT_OK)
            portable_whole_audio_event_fault(event_status);
    }
    f_29F0_0012();
    f_28BC_03CC();
}""", "m290D source DAC start event boundary")
    output = _replace_once(output,
        "    fd_55B3_6B4C[ch].snd = fd_55B3_6B4C[ch].owner = 0;\n    f_29F0_0012();",
        """    fd_55B3_6B4C[ch].snd = fd_55B3_6B4C[ch].owner = 0;
    {
        PortableWholeAudioEventStatus event_status =
            portable_whole_audio_sample_stop((unsigned)ch);
        if (event_status != PORTABLE_WHOLE_AUDIO_EVENT_OK)
            portable_whole_audio_event_fault(event_status);
    }
    f_29F0_0012();""", "m290D source DAC stop event boundary")
    output = '#include "portable/whole_program/platform/audio_events.h"\n\n' + output
    return output, {
        "transformed_source_boundaries": ["f_290D_0098 successful decoded-sample/channel commit", "f_290D_026C channel stop/owner clear"],
        "event_order": "The synchronous whole-program sequencer and source voice allocator call these original source functions in order; the event queue assigns one increasing sequence across starts and stops.",
        "sample_view": "f_0000_0090 stores a decoded kind-5 Handle in Sample.data. The callback dereferences that Handle once while its resource remains owned, and the queue copies exactly the low-16-bit Sample.len bytes before returning.",
        "source_parameters": "channel, decoded bytes, Sample.len, Sample.loop, computed 8.8 step, computed volume-table row, and looped flag are passed unchanged at the start commit; stop identifies the source channel.",
        "unbound_policy": "source event queue not bound, exhausted, or given invalid source sample state calls the explicit audio event fault; no silent success is reported",
        "leaves_unprovided": ["MIDI/OPL event backends for type-2 and other non-DAC channel families"],
    }


def adapt(path: str, source: str) -> tuple[str, dict[str, Any]]:
    """Convert one audited audio source path, rejecting stale source bytes."""
    normalized = path.replace("\\", "/")
    if normalized not in SOURCE_HASHES:
        raise ValueError(f"audio adapter does not recognize source path: {path}")
    source_sha = _sha(source)
    if source_sha != SOURCE_HASHES[normalized]:
        raise ValueError(f"unexpected {normalized} bytes: {source_sha}")
    if normalized == "src/root/m29F0.c":
        output, change = _convert_29f0(source)
    elif normalized == "src/root/m284A.c":
        output, change = _convert_284a(source)
    elif normalized == "src/root/m277E.c":
        output, change = _convert_277e_pointer(source)
    elif normalized == "src/root/m29D6.c":
        output, change = _convert_29d6(source)
    elif normalized == "src/root/m293A.c":
        output, change = _convert_293a(source)
    elif normalized == "src/root/m290D.c":
        output, change = _convert_290d(source)
    else:
        output = source
        change = {
            "status": "UNCHANGED_PENDING_DEVICE_BOUNDARIES",
            "source_scan": "inline assembly contains BIOS interrupts, direct physical reads, device-status polling, or mixed-width port I/O; no simulator or detection result is substituted",
            "host_capabilities": "unprovided",
        }
    ledger = {
        "schema": "whole-program-audio-conversion-v1",
        "source": {"path": normalized, "sha256": source_sha},
        "dependency_pins": DEPENDENCY_PINS.get(normalized, []),
        "output_sha256": _sha(output),
        "change": change,
    }
    return output, ledger
