#ifndef SIMANT_PORTABLE_RENDER_PALETTE_H
#define SIMANT_PORTABLE_RENDER_PALETTE_H
#include "primitives.h"

typedef struct PortablePalette {
    uint8_t ega_registers[16];
    uint8_t rgb[16][3];
} PortablePalette;

/* Root22BF win_SetPalette, EGA profile zero. RGB is the host presentation of
 * the source's six-bit EGA attribute-controller values. */
PortableRenderStatus portable_palette_load_ega(PortablePalette *palette,
                                               const uint8_t *bytes,size_t size);
#endif
