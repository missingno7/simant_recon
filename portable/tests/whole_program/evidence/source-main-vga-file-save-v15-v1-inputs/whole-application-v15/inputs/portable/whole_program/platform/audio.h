#ifndef SIMANT_WHOLE_PROGRAM_PLATFORM_AUDIO_H
#define SIMANT_WHOLE_PROGRAM_PLATFORM_AUDIO_H

#include <stddef.h>
#include <stdint.h>

/* Native platform providers for the original root:29F0 port/interrupt calls.
 * These declarations express source intent; no DOS, BIOS, or ISA behavior is
 * supplied by this header. */
void dos_audio_host_interrupt_disable(void);
void dos_audio_host_interrupt_enable(void);
void dos_audio_host_out8(uint16_t port, uint8_t value);
void dos_audio_host_out16(uint16_t port, uint16_t value);
uint8_t dos_audio_host_in8(uint16_t port);

/* Host BIOS/memory capabilities consumed by the converted legacy device
 * predicates. Providers must report the queried host state; they must not
 * claim a device is present when the query is unavailable. Far pointers are
 * supplied as the original real-mode segment:offset pair for provenance and
 * mapping by the selected host. */
uint16_t dos_audio_host_bios_int1a_8100(void);
void dos_audio_host_bios_int15_c000(uint16_t *es_out, uint16_t *bx_out);
uint8_t dos_audio_host_read_far_u8(uint16_t segment, uint16_t offset);
uint16_t dos_audio_host_read_far_u16(uint16_t segment, uint16_t offset);

/* Bounds-check an offset into a locked song handle using the byte length
 * recorded by the original handle manager. Invalid source offsets are an
 * explicit host failure boundary; the platform must provide the fault leaf. */
uint8_t *dos_audio_song_span(uint8_t *base, size_t size,
                             uint16_t offset, size_t length);
_Noreturn void dos_audio_host_song_bounds_fault(uint16_t offset,
                                                size_t length,
                                                size_t song_size);

#endif
