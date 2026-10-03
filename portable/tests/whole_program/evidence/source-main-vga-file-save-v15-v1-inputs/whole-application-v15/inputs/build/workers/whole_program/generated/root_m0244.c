#include "dos_types.h"
#include "portable/whole_program/platform/dos_memory.h"
#include "portable/whole_program/platform/dos_io.h"
#include "portable/whole_program/platform/graphics_source_fields.h"
#include "native_owners.h"
#pragma pack(push, 2)
/* Root module 0244: block move, a debug byte-swap dump, and the barrier level setters. */


void  BlockMove(void  *src, void  *dst, uint16_t n)
{
    _fmemcpy(dst, src, n);
}

extern int32_t  f_171C_16EA(void  *  *h);
extern int16_t  WinPrintf(char  *format, ...);

void  f_0244_0022(uint16_t  *  *h)
{
    uint16_t  *p;
    int16_t n;
    int16_t i;
    uint16_t w;

    n = f_171C_16EA(h) / 2L;
    p = *h;
    for (i = 0; i < n; i++, p++) {
        w = *p;
        WinPrintf("\ni=%d, j=%x", i, w);
        *p = (w >> 8) | (w << 8);
        WinPrintf("  = %x", *p);
    }
}


void  f_0244_00A7(void)
{
    native_state_Barrier.signed_value = 0x50;
}

void  f_0244_00BA(void)
{
    native_state_Barrier.signed_value = 0x90;
}

#pragma pack(pop)
