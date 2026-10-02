#include "tile_raster.h"

#include <limits.h>

static uint8_t plane_bit(const uint8_t *plane, unsigned x)
{
    return (uint8_t)((plane[x >> 3] >> (7u - (x & 7u))) & 1u);
}

static int span_contains(size_t size, size_t offset, size_t length)
{
    return offset <= size && length <= size - offset;
}

PortableRenderStatus portable_ega_tile_decode(const uint8_t *atlas,
                                               size_t atlas_size,
                                               uint16_t tile_index,
                                               uint8_t pixels[PORTABLE_EGA_TILE_PIXELS])
{
    size_t tile_offset;
    unsigned y, x, plane;

    if (atlas == NULL || pixels == NULL || tile_index >= 256u)
        return PORTABLE_RENDER_INVALID_ARGUMENT;
    tile_offset = (size_t)tile_index * PORTABLE_EGA_TILE_SOURCE_BYTES;
    if (!span_contains(atlas_size, tile_offset, PORTABLE_EGA_TILE_SOURCE_BYTES))
        return PORTABLE_RENDER_TRUNCATED_DATA;

    for (y = 0; y < PORTABLE_EGA_TILE_HEIGHT; ++y) {
        const uint8_t *row = atlas + tile_offset + (size_t)y * 8u;
        for (x = 0; x < PORTABLE_EGA_TILE_WIDTH; ++x) {
            uint8_t color = 0;
            for (plane = 0; plane < 4u; ++plane)
                color |= (uint8_t)(plane_bit(row + plane * 2u, x) << plane);
            pixels[y * PORTABLE_EGA_TILE_WIDTH + x] = color;
        }
    }
    return PORTABLE_RENDER_OK;
}

PortableRenderStatus portable_ega_life_composite(uint8_t pixels[PORTABLE_EGA_TILE_PIXELS],
                                                 const uint8_t *frames,
                                                 size_t frames_size,
                                                 uint16_t frame_index)
{
    size_t frame_offset;
    unsigned y, x, plane;

    if (pixels == NULL || frames == NULL)
        return PORTABLE_RENDER_INVALID_ARGUMENT;
    frame_offset = (size_t)frame_index * PORTABLE_EGA_LIFE_FRAME_BYTES;
    if (!span_contains(frames_size, frame_offset, PORTABLE_EGA_LIFE_FRAME_BYTES))
        return PORTABLE_RENDER_TRUNCATED_DATA;

    for (y = 0; y < PORTABLE_EGA_TILE_HEIGHT; ++y) {
        const uint8_t *row = frames + frame_offset + (size_t)y * 10u;
        const uint8_t *mask = row;
        const uint8_t *colors = row + 2u;
        for (x = 0; x < PORTABLE_EGA_TILE_WIDTH; ++x) {
            if (plane_bit(mask, x) != 0u) {
                uint8_t color = 0;
                for (plane = 0; plane < 4u; ++plane)
                    color |= (uint8_t)(plane_bit(colors + plane * 2u, x) << plane);
                pixels[y * PORTABLE_EGA_TILE_WIDTH + x] = color;
            }
        }
    }
    return PORTABLE_RENDER_OK;
}

PortableRenderStatus portable_ega_tile_draw(PortableFramebuffer *fb,
                                             int32_t x,
                                             int32_t y,
                                             const uint8_t *atlas,
                                             size_t atlas_size,
                                             uint16_t tile_index)
{
    uint8_t pixels[PORTABLE_EGA_TILE_PIXELS];
    PortableRenderStatus status;
    unsigned py, px;

    if (fb == NULL || fb->pixels == NULL || x > INT32_MAX - 15 || y > INT32_MAX - 15)
        return PORTABLE_RENDER_INVALID_ARGUMENT;
    status = portable_ega_tile_decode(atlas, atlas_size, tile_index, pixels);
    if (status != PORTABLE_RENDER_OK)
        return status;
    for (py = 0; py < PORTABLE_EGA_TILE_HEIGHT; ++py)
        for (px = 0; px < PORTABLE_EGA_TILE_WIDTH; ++px)
            portable_put_pixel(fb, x + (int32_t)px, y + (int32_t)py,
                               pixels[py * PORTABLE_EGA_TILE_WIDTH + px]);
    return PORTABLE_RENDER_OK;
}
