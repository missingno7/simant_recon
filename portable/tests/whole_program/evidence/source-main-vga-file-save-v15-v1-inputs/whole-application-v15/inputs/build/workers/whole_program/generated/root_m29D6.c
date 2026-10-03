#include "dos_types.h"
#include "portable/whole_program/platform/dos_memory.h"
#include "portable/whole_program/platform/dos_io.h"
#include "portable/whole_program/platform/graphics_source_fields.h"
#include "portable/whole_program/platform/audio_state.h"
#include "portable/whole_program/platform/audio.h"
#pragma pack(push, 2)

/* Root module 29D6 (0x29D6A-0x29F0A): note output for two further sound devices (port 205h; chip at 29BF). */

int16_t g_75E8[] = {
    0x1ddd, 0x1c31, 0x1a9c, 0x191b, 0x17b4, 0x165e, 0x151f, 0x13ee,
    0x12cf, 0x11c1, 0x10c1, 0xfd1
};
uint16_t g_7600[] = {
    0x3574, 0x3274, 0x2f9f, 0x2cf3, 0x2a6d, 0x280b, 0x25cc, 0x23ad,
    0x21ac, 0x1fc8, 0x1e00, 0x1c51, 0x1aba, 0x193a, 0x17cf, 0x1679,
    0x1536, 0x1406, 0x12e6, 0x11d6, 0x10d6, 0xfe4, 0xf00, 0xe28,
    0xd5d, 0xc9d, 0xbe8, 0xb3d, 0xa9b, 0xa03, 0x973, 0x8eb,
    0x86b, 0x7f2, 0x780, 0x714, 0x6ae, 0x64e, 0x5f4, 0x59e,
    0x54e, 0x501, 0x4b9, 0x476, 0x436, 0x3f9, 0x3c0, 0x38a,
    0x357, 0x327, 0x2fa, 0x2cf, 0x2a7, 0x281, 0x25d, 0x23b,
    0x21b, 0x1fd, 0x1e0, 0x1c5, 0x1ac, 0x194, 0x17d, 0x168,
    0x153, 0x140, 0x12e, 0x11d, 0x10d, 0xfe, 0xf0, 0xe3,
    0xd6, 0xca, 0xbe, 0xb4, 0xaa, 0xa0, 0x97, 0x8f,
    0x87, 0x7f, 0x78, 0x71, 0x6b, 0x65, 0x5f, 0x5a,
    0x55, 0x50, 0x4c, 0x47, 0x43, 0x40, 0x3c, 0x39,
    0x35, 0x32, 0x30, 0x2d, 0x2a, 0x28, 0x26, 0x24,
    0x22, 0x20, 0x1e, 0x1c, 0x1b, 0x19, 0x18, 0x16,
    0x15, 0x14, 0x13, 0x12, 0x11, 0x10, 0xf, 0xe,
    0xd, 0xd, 0xc, 0xb, 0xb, 0xa, 0x9, 0x9
};

extern void  f_29F0_002A(int16_t port, char value);

void  f_29D6_000A(int16_t a, int16_t note, int16_t vol, int16_t chan)
{
    int16_t f;

    chan <<= 5;
    f = g_75E8[note % 12] >> note / 12;
    f_29F0_002A(0x205, (f & 0xf) + ((char)chan + 0x80));
    f_29F0_002A(0x205, f >> 4);
    vol >>= 3;
    vol = 0xf - vol;
    f_29F0_002A(0x205, vol + ((char)chan + 0x80) + 0x10);
}

extern void  f_29BF_00E6(int16_t reg, int16_t value);

void  f_29D6_0082(int16_t a, int16_t note, int16_t vol, int16_t ch)
{
    int16_t f;

    vol = 0x1f;
    note -= 12;
    if (note < 0)
        note = 0;
    f = g_7600[note];
    f_29BF_00E6(ch * 2, f & 0xff);
    f_29BF_00E6(ch * 2 + 1, f >> 8);
    f_29BF_00E6(ch + 8, vol);
}

extern int16_t  fd_50F6_4B14;

void  f_29D6_00D9(int16_t a, int16_t note, int16_t vol, int16_t ch)
{
    uint16_t freq;
    char reg;
    int16_t port;
    int16_t val;

    ch <<= 5;
    reg = (char)(((char)ch + 0x80) & 0xe0);
    val = ~(vol >> 3) & 0xf;
    port = fd_50F6_4B14;
    freq = g_7600[note] >> 1;
    {
        uint16_t reg_word = (uint16_t)(uint8_t)reg;
        uint8_t high = (uint8_t)((freq & 0x03f0u) >> 4);
        uint8_t low = (uint8_t)((freq & 0x000fu) + reg_word);
        uint16_t word_value = (uint16_t)(((uint16_t)high << 8) | low);
        dos_audio_host_out16((uint16_t)port, word_value);
        f_29F0_002A(port, (char)(reg_word + 0x10u + (uint16_t)val));
    }
}

void  f_29D6_0148(int16_t note, int16_t ch)
{
    f_29D6_000A(0, note, 0, ch);
}

void  f_29D6_015D(int16_t a, int16_t ch)
{
    f_29BF_00E6(ch + 8, 0);
    f_29BF_00E6(ch * 2, 0);
    f_29BF_00E6(ch * 2 + 1, 0);
}

void  f_29D6_0197(int16_t a, int16_t ch)
{
    f_29D6_00D9(0, 0, 0, ch);
}

#pragma pack(pop)
