#include "dos_types.h"
#include "portable/whole_program/platform/dos_memory.h"
#include "portable/whole_program/platform/dos_io.h"
#include "portable/whole_program/platform/graphics_source_fields.h"
#pragma pack(push, 2)
/* Root module 078E: pointer allocation helpers (memory-manager handles dereferenced). */

typedef char  *  *Handle;

extern void  Punt(char  *message);
extern Handle  f_171C_13CA(int32_t size, int16_t flags, char  *name);

char  *  f_078E_000C(int32_t size, char  *name)
{
    if (size > 0xffffL)
        Punt("NewPtr argument too large");
    return *f_171C_13CA(size, 0, name);
}


char  *  f_078E_0053(int32_t size, char  *name)
{
    Handle h;

    _fmemset(*(h = f_171C_13CA(size, 0, name)), 0, (uint16_t)size);
    return *h;
}

#pragma pack(pop)
