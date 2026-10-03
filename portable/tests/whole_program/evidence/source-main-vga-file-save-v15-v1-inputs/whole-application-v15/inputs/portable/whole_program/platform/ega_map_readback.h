#ifndef SIMANT_WHOLE_PROGRAM_PLATFORM_EGA_MAP_READBACK_H
#define SIMANT_WHOLE_PROGRAM_PLATFORM_EGA_MAP_READBACK_H

#include <stdint.h>

/* Source o00_31AD_1A8F selects one EGA read plane, then copies 128
 * consecutive bytes from DS:offset into the shared g_3D20 scratch row.
 * The DOS graphics-controller register access is supplied by this typed
 * read boundary; the host never receives DOS segment values. */
typedef int (*PortableEgaReadPlane)(void *context, uint8_t plane,
                                    uint16_t offset, uint8_t output[128]);

int portable_ega_map_readback_bind(PortableEgaReadPlane read_plane,
                                   void *context);
void portable_ega_map_readback_unbind(void);

/* Native replacement for S00:o00_31AD_1A8F. The source caller supplies a
 * plane selector in row and a 16-bit source offset in col. */
void o00_31AD_1A8F(int16_t row, int16_t col);

#endif
