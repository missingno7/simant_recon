#include "dos_types.h"
#include "portable/whole_program/platform/dos_memory.h"
#include "portable/whole_program/platform/dos_io.h"
#include "portable/whole_program/platform/graphics_source_fields.h"
#pragma pack(push, 2)
/* Root module 29B8 (0x29B80-0x29BF7): sound card DSP reset and detection. */

int16_t fd_55B3_7564 = 0;

extern void  f_29F0_002A(int16_t port, char value);
extern uint8_t  f_29F0_0038(int16_t port);

int16_t  f_29B8_0000(void)
{
    int16_t i;
    uint8_t c;

    f_29F0_002A(fd_55B3_7564 + 6, 1);
    for (i = 0; i < 9999; i++)
        ;
    f_29F0_002A(fd_55B3_7564 + 6, 0);
    for (i = 0; i < 9999; i++)
        ;
    for (i = 0; i < 200 && !(c & 0x80); i++)
        c = f_29F0_0038(fd_55B3_7564 + 0xe);
    if (f_29F0_0038(fd_55B3_7564 + 0xa) == 0xaa)
        return 1;
    return 0;
}

#pragma pack(pop)
