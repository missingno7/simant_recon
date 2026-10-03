#include "dos_types.h"
#include "portable/whole_program/platform/dos_memory.h"
#include "portable/whole_program/platform/dos_io.h"
#include "portable/whole_program/platform/graphics_source_fields.h"
#include "portable/whole_program/platform/audio_state.h"
#include "portable/whole_program/platform/audio.h"
#pragma pack(push, 2)

/* Root module 284A: MIDI song player. */

struct Song {
    int16_t program[14];
    int16_t bank[14];
    char  *  *data;
};

int16_t g_7566 = 0;
int32_t g_7568 = 0;
int16_t g_756C = 0;
int16_t g_756E = 0;
uint16_t g_7570 = 0x7f;
int16_t g_7572 = 0;
int16_t g_7574 = 0;
int16_t g_7576 = 0;
int16_t g_7578 = 0;

#define SONG(off) (*dos_audio_song_span((uint8_t *)g_8DFC, (size_t)(uint16_t)fd_50F6_4B2C, (uint16_t)(off), 1u))

extern void  f_0000_046F(void);

int16_t  f_284A_0004(void)
{
    f_0000_046F();
    return g_756E == 0;
}

void  StopSong(void);
extern struct Song  *  fd_55B3_00B4;
extern int16_t  f_0000_0193(struct Song  *song, int16_t number);
extern int16_t  WinPrintf(char  *format, ...);
extern void  f_29F0_001A(void);

static int16_t g_8DD8[18];
static uint8_t *g_8DFC;
extern int16_t  fd_50F6_4B2C;
extern int16_t  f_171C_1C1C(char  *  *handle);
void  f_284A_0256(void);
void  f_284A_02E4(void);



extern void  f_29F0_0022(void);

void  f_284A_0013(int16_t number)
{
    int16_t i;

    StopSong();
    if (f_0000_0193(fd_55B3_00B4, number) == -1) {
        WinPrintf("music failure\n");
        return;
    }
    f_29F0_001A();
    g_7572 = 0;
    fd_50F6_4B28 = fd_55B3_00B4->data;
    g_8DFC = (uint8_t *)(*fd_50F6_4B28);
    WinPrintf("Song data=%p, handle=%p", g_8DFC, fd_50F6_4B28);
    fd_50F6_4B2C = f_171C_1C1C(fd_50F6_4B28);
    f_284A_0256();
    f_284A_02E4();
    g_756E = 1;
    fd_55B3_6B42 = 5;
    for (i = 0; i < 14; i++) {
        fd_50F6_4B8E[i] = fd_55B3_00B4->bank[i];
        fd_50F6_4BAA[i] = fd_55B3_00B4->program[i];
    }
    f_29F0_0022();
}

extern void  f_0000_039B(struct Song  *song, int16_t number);
extern void  f_295C_0391(void);

void  StopSong(void)
{
    if (g_756E) {
        g_756E = 0;
        f_0000_039B(fd_55B3_00B4, g_7578);
        f_295C_0391();
    }
}

/* SCAFFOLD BEGIN: context only, not reconstruction.
 * f_284A_0138 (big-endian 16-bit read): the original zero-extends the first
 * byte into AX and builds the word with mov ch,al / mov ax,cx; no C spelling
 * tried reproduces it (mov ah,byte / or ax,cx instead). */
int16_t  f_284A_0138(int16_t off)
{
    return SONG(off) << 8 | SONG(off + 1);
}
/* SCAFFOLD END */

int32_t  f_284A_0151(int16_t off)
{
    int32_t v;
    int16_t i;

    v = 0;
    for (i = 0; i < 4; i++) {
        v = (v << 8) + SONG(off);
        off++;
    }
    return v;
}

void  f_284A_0199(int16_t count, int16_t off)
{
    int16_t i;
    int32_t len;

    for (i = 0; i < count; i++) {
        len = f_284A_0151(off + 4);
        g_8DD8[i] = off + 8;
        off += len + 8;
    }
}

static int16_t  *g_8DFE;

int32_t  f_284A_01D5(void)
{
    int32_t v;
    uint8_t c;
    int16_t pos;

    pos = *g_8DFE;
    if ((v = SONG(pos++)) & 0x80) {
        v &= 0x7f;
        do {
            c = SONG(pos++);
            v = (v << 7) + (c & 0x7f);
        } while (c & 0x80);
    }
    *g_8DFE = pos;
    return v;
}

void  f_284A_024B(uint16_t volume)
{
    g_7570 = volume;
}

extern int16_t  fd_50F6_4B2E;



void  f_284A_0256(void)
{
    int32_t len;
    int16_t i;

    len = f_284A_0151(4);
    g_7566 = f_284A_0138(10);
    fd_50F6_4B2E = f_284A_0138(12);
    f_284A_0199(g_7566, len + 8);
    for (i = 0; i < g_7566; i++) {
        g_8DFE = &g_8DD8[i];
        fd_50F6_4B42[i] = f_284A_01D5();
        fd_50F6_4B30[i] = SONG(*g_8DFE);
    }
}

static uint8_t  *g_8E02;
void  f_284A_0325(uint16_t division, int32_t tempo);

void  f_284A_02E4(void)
{
    g_7568 = 0;
    g_756C = 0;
    g_8DFE = g_8DD8;
    g_8E02 = fd_50F6_4B30;
    f_284A_0325(0x1e0, 500000L);
    fd_55B3_6B42 = 99;
}

void  f_284A_0324(void)
{
}

extern int32_t  fd_50F6_4B8A;

void  f_284A_0325(uint16_t division, int32_t tempo)
{
    int32_t v;

    if (division == 0)
        v = 0;
    else
        v = tempo / 1000 * 1194 / division;
    fd_50F6_4B8A = v / 13;
}

int16_t  f_284A_038F(void)
{
    int32_t delta;
    int32_t t;
    int16_t best;
    int16_t i;

    if (*g_8E02 != 0x2f) {
        delta = f_284A_01D5();
        fd_50F6_4B42[g_756C] += delta;
    } else
        fd_50F6_4B42[g_756C] = 0x7fffffffL;
    best = 0;
    for (i = 1; i < g_7566; i++)
        if (fd_50F6_4B42[best] > fd_50F6_4B42[i] && fd_50F6_4B30[i] != 0x2f)
            best = i;
    if (fd_50F6_4B30[best] != 0x2f) {
        t = fd_50F6_4B42[best];
        if (t != 0x7fffffffL) {
            delta = t - g_7568;
            g_7568 = t;
            g_8DFE = &g_8DD8[best];
            g_8E02 = &fd_50F6_4B30[best];
            g_756C = best;
            return (int16_t)(fd_50F6_4B8A * delta >> 8);
        }
    }
    g_756E = 2;
    f_284A_0324();
    return 0;
}

extern void  f_295C_02E8(int16_t program, int16_t note);
extern void  f_295C_01EC(int16_t bank, int16_t program, int16_t note, int16_t velocity);

void  f_284A_04C9(int16_t chan, int16_t note, uint16_t velocity)
{
    velocity = g_7570 * velocity >> 7;
    if (velocity == 0)
        f_295C_02E8(fd_50F6_4B8E[chan], note);
    else
        f_295C_01EC(fd_50F6_4BAA[chan], fd_50F6_4B8E[chan], note, velocity);
}

void  f_284A_0521(int16_t chan, int16_t program)
{
    fd_50F6_4B8E[chan] = program;
}

int16_t g_75A4[] = { 2, 2, 2, 2, 1, 1, 2 };

void  f_284A_0537(uint16_t status)
{
    int16_t type;
    int16_t chan;

    type = (status & 0x70) >> 4;
    chan = status & 0xf;
    if (chan < 14) {
        switch (type) {
        case 0:
            f_284A_04C9(chan, SONG(*g_8DFE) + g_7576, 0);
            break;
        case 1:
            f_284A_04C9(chan, SONG(*g_8DFE) + g_7576, ((SONG(*g_8DFE + 1))));
            break;
        case 12:
            f_284A_0521(chan, SONG(*g_8DFE));
            break;
        }
    }
    *g_8DFE += g_75A4[type];
}

void  f_284A_05C5(void)
{
    int32_t tempo;
    int16_t pos;

    if (SONG(*g_8DFE) == 0x2f) {
        *g_8E02 = SONG(*g_8DFE);
        (*g_8DFE)--;
    } else if (SONG(*g_8DFE) == 0x51) {
        *g_8DFE += 2;
        pos = *g_8DFE;
        tempo = ((((int32_t)SONG(pos) << 8) + SONG(pos + 1)) << 8) + SONG(pos + 2);
        *g_8DFE += 3;
        f_284A_0325(fd_50F6_4B2E, tempo);
    } else {
        (*g_8DFE)++;
        *g_8DFE += (int16_t)f_284A_01D5();
    }
}

void  f_284A_0673(uint8_t status)
{
    *g_8DFE += (int16_t)f_284A_01D5();
}

int16_t  f_284A_067F(void)
{
    int16_t r;

    if (g_756E != 1)
        return -1;
    g_7574 = 1;
    g_8DFC = (uint8_t *)(*fd_50F6_4B28);
    do {
        if (SONG(*g_8DFE) & 0x80) {
            *g_8E02 = SONG(*g_8DFE);
            (*g_8DFE)++;
        }
        if (*g_8E02 == 0xf7 || *g_8E02 == 0xf0)
            f_284A_0673(*g_8E02);
        else if (*g_8E02 == 0xff)
            f_284A_05C5();
        else
            f_284A_0537(*g_8E02);
        r = f_284A_038F();
    } while (r == 0 && g_756E != 2);
    g_7574 = 0;
    return r ? r : 1;
}

#pragma pack(pop)
