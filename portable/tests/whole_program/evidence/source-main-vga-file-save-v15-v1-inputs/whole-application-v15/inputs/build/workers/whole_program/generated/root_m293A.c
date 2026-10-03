#include "dos_types.h"
#include "portable/whole_program/platform/dos_memory.h"
#include "portable/whole_program/platform/dos_io.h"
#include "portable/whole_program/platform/graphics_source_fields.h"
#include "portable/whole_program/platform/audio_state.h"
#include "portable/whole_program/platform/audio.h"
#pragma pack(push, 2)

/* Root module 293A (0x293A6-0x295CA): sound device detection. */

int16_t  f_293A_0029(void);
int16_t  f_293A_002D(void);
int16_t  f_293A_0059(void);
int16_t  f_293A_0087(void);
int16_t  f_293A_0121(void);
int16_t  f_293A_015E(void);
int16_t  f_293A_017C(void);
int16_t  f_293A_017F(void);



int16_t ( *fd_55B3_74DA[])(void) = {
    f_293A_0029, f_293A_0029, f_293A_002D, f_293A_0059, f_293A_0087,
    f_293A_015E, f_293A_0121, f_293A_017C, f_293A_017F
};
int16_t  *fd_55B3_74FE = fd_50F6_01F0;

int16_t  f_293A_0006(void)
{
    int16_t i;
    int16_t found;

    found = 0;
    for (i = 8; i > 0; i--) {
        if (fd_55B3_74DA[i]()) {
            found = i;
            break;
        }
    }
    return found;
}

int16_t  f_293A_0029(void)
{
    return 1;
}

int16_t  f_293A_002D(void)
{
    uint16_t base;
    uint8_t signature;

    base = dos_audio_host_bios_int1a_8100();
    signature = dos_audio_host_read_far_u8(0xfc00, 0x0000);
    return signature == 0x21 || base == 0x00c4;
}

int16_t  f_293A_0059(void)
{
    uint16_t es;
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
}

extern void  f_283E_000A(char reg, char value);
extern uint8_t  f_29F0_0038(int16_t port);

int16_t  f_293A_0087(void)
{
    int16_t s1;
    uint16_t i;

    f_283E_000A(4, 0x60);
    f_283E_000A(4, 0x80);
    s1 = f_29F0_0038(0x388);
    f_283E_000A(2, 0xff);
    f_283E_000A(4, 0x21);
    for (i = 0; i < 200; i++)
        f_29F0_0038(0x388);
    i = f_29F0_0038(0x388);
    f_283E_000A(4, 0x60);
    f_283E_000A(4, 0x80);
    if ((s1 & 0xe0) == 0 && (i & 0xe0) == 0xc0)
        return 1;
    return 0;
}

extern uint16_t  fd_55B3_7564;
extern int16_t  f_29B8_0000(void);

int16_t  f_293A_0121(void)
{
    int16_t found;

    found = 0;
    fd_55B3_7564 = 0x200;
    while (!found) {
        if (fd_55B3_7564 >= 0x260)
            break;
        fd_55B3_7564 += 0x10;
        found = f_29B8_0000();
    }
    return found;
}

extern int16_t  f_29BF_0139(void);
extern int16_t  fd_50F6_4B14;

int16_t  f_293A_015E(void)
{
    int16_t port;

    if ((port = f_29BF_0139()) == 0)
        return 0;
    fd_50F6_4B14 = port;
    return 1;
}

int16_t  f_293A_017C(void)
{
    return 0;
}

extern void  f_29F0_002A(int16_t port, char value);

int16_t  f_293A_017F(void)
{
    int16_t i;
    int16_t tries;
    int16_t ok;
    int16_t ready;

    ok = 0;
    ready = 0;
    if (!(f_29F0_0038(0x331) & 0x80))
        f_29F0_0038(0x330);
    for (i = 0; i < 5000; i++) {
        if (!(f_29F0_0038(0x331) & 0x40)) {
            ok = 1;
            goto write_ready;
        }
    }
write_ready:
    if (ok) {
        f_29F0_002A(0x331, 0xff);
        for (tries = 0; tries < 3 && ((uint16_t)ok >= 0); tries++) {
            for (i = 0; i < 5000; i++) {
                if (!(f_29F0_0038(0x331) & 0x80)) {
                    ready = 1;
                    goto read_ready;
                }
            }
read_ready:
            if (ready) {
                if (f_29F0_0038(0x330) == 0xfe)
                    return 1;
                ready = 0;
            }
        }
    }
    return 0;
}

/* f_293A_017F is STEERED: the folded unsigned flag check retains the original
 * stack homes. The eliminated original expression is unknown; LIFE-1 keeps
 * the whole-module positive and negative controls. The two polling continuation
 * labels are inferred from relocation record boundaries (ZI-2). */

#pragma pack(pop)
