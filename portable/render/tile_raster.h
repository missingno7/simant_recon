#ifndef SIMANT_PORTABLE_RENDER_TILE_RASTER_H
#define SIMANT_PORTABLE_RENDER_TILE_RASTER_H

#include "primitives.h"

#include <stddef.h>
#include <stdint.h>

enum {
    PORTABLE_EGA_TILE_WIDTH = 16,
    PORTABLE_EGA_TILE_HEIGHT = 16,
    PORTABLE_EGA_TILE_PIXELS = 256,
    PORTABLE_EGA_TILE_SOURCE_BYTES = 128,
    PORTABLE_EGA_LIFE_FRAME_BYTES = 160
};

/* Expand one source tile from the kind-9 ground atlas. Each scanline stores
 * two bytes for plane 0, then plane 1, plane 2, and plane 3. The output is
 * row-major palette indices 0..15. */
PortableRenderStatus portable_ega_tile_decode(const uint8_t *atlas,
                                               size_t atlas_size,
                                               uint16_t tile_index,
                                               uint8_t pixels[PORTABLE_EGA_TILE_PIXELS]);

/* Apply one EMS life frame to an already decoded indexed tile. Each of its 16
 * rows stores a two-byte MSB-first transparency mask followed by four
 * two-byte MSB-first color planes. Set mask bits replace the base pixel;
 * clear bits preserve it. */
PortableRenderStatus portable_ega_life_composite(uint8_t pixels[PORTABLE_EGA_TILE_PIXELS],
                                                 const uint8_t *frames,
                                                 size_t frames_size,
                                                 uint16_t frame_index);

PortableRenderStatus portable_ega_tile_draw(PortableFramebuffer *fb,
                                             int32_t x,
                                             int32_t y,
                                             const uint8_t *atlas,
                                             size_t atlas_size,
                                             uint16_t tile_index);

#endif
