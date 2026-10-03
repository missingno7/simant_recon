#include "dos_types.h"
#include "portable/whole_program/platform/dos_memory.h"
#include "portable/whole_program/platform/dos_io.h"
#include "portable/whole_program/platform/graphics_source_fields.h"
#pragma pack(push, 2)
/* Module at root frame 00DF (large-model code segment): sound driver shell. */

int16_t g_1926 = 0;

extern int16_t g_610A;
extern int16_t  f_293A_0006(void);
extern int16_t  f_277E_0000(int16_t mode, int16_t flag);
extern void  WinPrintf(char *fmt, ...);
extern int16_t  *  fd_55B3_74FE;

void  f_00DF_0004(void)
{
    if (g_1926)
        return;
    if (g_610A == -1)
        f_277E_0000(f_293A_0006(), 0);
    else if (g_610A == 0)
        return;
    else
        f_277E_0000(g_610A, 0);
    WinPrintf("Sound Driver Shell (c) 1991  -- LIB link version\n");
    WinPrintf("Sound Driver reports driver: %d\n%d DAC channels\n%d FM channels\n%d TANDY PSG channels\n%d PS1 PSG channels\n%d COVOX PSG channels\nand %d MIDI channels\n",
              fd_55B3_74FE[0], fd_55B3_74FE[1], fd_55B3_74FE[2], fd_55B3_74FE[4],
              fd_55B3_74FE[3], fd_55B3_74FE[5], fd_55B3_74FE[6]);
    g_1926 = 1;
}

void  f_00DF_0089(void)
{
    WinPrintf("MUSIC INIT!");
}

void  f_00DF_009D(void)
{
    WinPrintf("BEEP");
}

extern int16_t  fd_3D57_07A8[];
extern void  f_0250_01E7(void);
extern void  f_284A_0013(int16_t song);

void  myBeginSong(int16_t song)
{
    if (g_1926 && fd_3D57_07A8[1]) {
        f_0250_01E7();
        f_284A_0013(song);
    }
}

void  f_00DF_00E0(void)
{
}

extern void  f_295C_0367(int16_t sound);

void  myBeginSound(int16_t a, int16_t b, int16_t c)
{
    if (g_1926 && fd_3D57_07A8[2])
        f_295C_0367(a);
}

void  myBeginSoundReverse(int16_t a, int16_t b, int16_t c)
{
    myBeginSound(a, b, c);
}

int16_t  mySoundIsDone(void)
{
    return 1;
}

extern int16_t  f_284A_0004(void);

int16_t  mySongIsDone(void)
{
    if (g_1926 && fd_3D57_07A8[1])
        return f_284A_0004();
    return 1;
}

void  f_00DF_015C(void)
{
}

void  f_00DF_0164(void)
{
}

void  f_00DF_016C(void)
{
    if (g_1926 && fd_3D57_07A8[1])
        f_295C_0367(1);
}

#pragma pack(pop)
