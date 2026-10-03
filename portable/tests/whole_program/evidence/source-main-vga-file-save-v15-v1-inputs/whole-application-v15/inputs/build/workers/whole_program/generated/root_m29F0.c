#include "dos_types.h"
#include "portable/whole_program/platform/dos_memory.h"
#include "portable/whole_program/platform/dos_io.h"
#include "portable/whole_program/platform/graphics_source_fields.h"
#include "portable/whole_program/platform/audio_state.h"
#include "portable/whole_program/platform/audio.h"
#pragma pack(push, 2)

/*
 * Port and interrupt-flag helpers (root module, code frame 29F0; linear 0x29F0A-0x29F4C).
 * C functions whose bodies are MSC inline assembly.
 */

void  f_29F0_000A(void)
{
    dos_audio_host_interrupt_disable();
}

void  f_29F0_0012(void)
{
    dos_audio_host_interrupt_enable();
}

void  f_29F0_001A(void)
{
    dos_audio_host_interrupt_disable();
}

void  f_29F0_0022(void)
{
    dos_audio_host_interrupt_enable();
}

void  f_29F0_002A(int16_t port, int16_t value)
{
    dos_audio_host_out8((uint16_t)port, (uint8_t)value);
}

uint8_t  f_29F0_0038(int16_t port)
{
    return dos_audio_host_in8((uint16_t)port);
}

#pragma pack(pop)
