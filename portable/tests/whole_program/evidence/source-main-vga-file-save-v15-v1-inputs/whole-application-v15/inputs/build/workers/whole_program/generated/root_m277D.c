#include "dos_types.h"
#include "portable/whole_program/platform/dos_memory.h"
#include "portable/whole_program/platform/dos_io.h"
#include "portable/whole_program/platform/graphics_source_fields.h"
#pragma pack(push, 2)
/*
 * Module at root frame 277D: six empty far functions (6 bytes, one RETF each).
 * The Win16 build implements WinPrintf and sibling debug formatters; in this
 * DOS release they compile to empty bodies.  Only WinPrintf is named (xver HIGH);
 * the siblings keep address names until independent evidence identifies them.
 * Compiled with /Gs: with stack checking each would be an 8-byte frame.
 */

int16_t  WinPrintf(char  *format, ...)
{
}

void  f_277D_000B(void)
{
}

void  f_277D_000C(void)
{
}

void  f_277D_000D(void)
{
}

void  f_277D_000E(void)
{
}

void  f_277D_000F(void)
{
}

#pragma pack(pop)
