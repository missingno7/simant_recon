#include "dos_types.h"
#include "portable/whole_program/platform/dos_memory.h"
#include "portable/whole_program/platform/dos_io.h"
#include "portable/whole_program/platform/graphics_source_fields.h"
#include "portable/whole_program/platform/audio_state.h"
#pragma pack(push, 2)
/* Root module 2815 (code segment 0x2815A-0x283EA): AdLib (OPL2) voice control. */



char g_68FE[] = { 0, 1, 2, 6, 7, 8, 12, 13, 14 };
char g_6908[] = { 3, 4, 5, 9, 10, 11, 15, 16, 17 };
char g_6912[] = { 0, 1, 2, 3, 4, 5, 8, 9, 10, 11, 12, 13, 16, 17, 18, 19, 20, 21 };
int16_t g_6924[] = { 0x157, 0x16b, 0x181, 0x198, 0x1b0, 0x1ca, 0x1e5, 0x202, 0x220, 0x241, 0x263, 0x287 };

extern void  f_283E_000A(char reg, char value);

void  f_2815_000A(char  *p, int16_t voice)
{
    char op1;
    char op2;

    op1 = g_6912[g_68FE[voice]];
    op2 = g_6912[g_6908[voice]];
    f_283E_000A(op1 + 0x20, p[1]);
    f_283E_000A(op2 + 0x20, p[0]);
    f_283E_000A(op1 + 0x40, p[3]);
    f_283E_000A(op2 + 0x40, p[2]);
    f_283E_000A(op1 + 0x60, p[5]);
    f_283E_000A(op2 + 0x60, p[4]);
    f_283E_000A(op1 + 0x80, p[7]);
    f_283E_000A(op2 + 0x80, p[6]);
    f_283E_000A(op1 + 0xe0, p[10]);
    f_283E_000A(op2 + 0xe0, p[9]);
    f_283E_000A(voice + 0xc0, p[8]);
}

void  f_2815_0118(void)
{
    int16_t i;

    f_283E_000A(1, 0);
    f_283E_000A(4, 0x80);
    f_283E_000A(8, 0);
    f_283E_000A(0xbd, 0xc0);
    for (i = 0; i < 8; i++)
        f_283E_000A(i + 0xb0, 0);
}





/* SCAFFOLD BEGIN: unclaimed AdLib volume/pitch draft */
void  f_2815_0165(int16_t instr, int16_t note, int16_t vol, int16_t voice)
{
    uint8_t  *p;

    vol += fd_50F6_4B16;
    p = portable_whole_audio_patch_bytes(&fd_50F6_0000[instr]);
    vol += *(int16_t  *)(p + 0xd);
    if (vol < 0)
        vol = 0;
    if (vol > 0x7f)
        vol = 0x7f;
    f_283E_000A(g_6912[g_6908[voice]] + 0x40,
                ((uint16_t)(0x3f - (uint8_t)fd_55B3_6BA4[vol]) * ((p[2] & 0x3f) ^ 0x3f) >> 6 ^ 0x3f) | (p[2] & 0xc0));
    note += *(int16_t  *)(p + 0xb) * 12;
    if (note >= 0 && note <= 0x7f) {
        f_283E_000A(voice + 0xa0, g_6924[note % 12]);
        f_283E_000A(voice + 0xb0, ((note / 12 + 8) << 2) + (g_6924[note % 12] >> 8));
    }
}
/* SCAFFOLD END */

void  f_2815_024D(int16_t a, int16_t voice)
{
    f_283E_000A(voice + 0xa0, 0);
    f_283E_000A(voice + 0xb0, 0);
}

void  f_2815_0275(int16_t instr, int16_t voice)
{
    f_2815_000A(portable_whole_audio_patch_bytes(&fd_50F6_0000[instr]), voice);
}

#pragma pack(pop)
