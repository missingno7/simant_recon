#include "graphics_bitmap_source.h"

#include "graphics_source_clip.h"
#include "portable/whole_program/window_source_globals.h"

#include <stdint.h>
#include <stdlib.h>

SimGraphicsBitmapCallback g_914C;
SimGraphicsBitmapCallback g_9150;

extern void f_1D8E_07F6(char *port, int16_t x, int16_t y, char *bits,
                       int16_t width, int16_t height);

static SimGraphicsStatus draw_planar4(SimGraphicsDriver *graphics,
                                      int16_t x, int16_t y,
                                      const uint8_t *bits,
                                      int16_t width, int16_t height)
{
    size_t plane_row_bytes;
    size_t source_row_bytes;
    int32_t sx0, sx1;
    int32_t row, px;
    int16_t cut_left = fd_55B3_3DE6;
    int16_t cut_right = fd_55B3_3DE8;

    if (graphics == NULL || graphics->pixel_storage == NULL || bits == NULL ||
        width <= 0 || height <= 0)
        return SIM_GRAPHICS_INVALID_ARGUMENT;
    /* The admitted direct S00 source is its ordinary 4-plane EGA/VGA layout.
     * Other raster operations and odd color-depth profiles remain explicit debt. */
    if ((((uint8_t)g_5A97) & 1u) != 0 || graphics->g_3DD2 != 0)
        return SIM_GRAPHICS_UNSUPPORTED_MODE;
    if (cut_left < 0 || cut_right < 0 ||
        (int32_t)cut_left + (int32_t)cut_right > width)
        return SIM_GRAPHICS_INVALID_ARGUMENT;

    plane_row_bytes = ((size_t)(uint16_t)width + 7u) / 8u;
    source_row_bytes = plane_row_bytes * 4u;
    sx0 = cut_left;
    sx1 = (int32_t)width - cut_right;
    for (row = 0; row < height; ++row) {
        for (px = sx0; px < sx1; ++px) {
            size_t byte_in_plane = (size_t)px >> 3;
            unsigned bit_index = 7u - ((unsigned)px & 7u);
            uint8_t mask = (uint8_t)(1u << bit_index);
            uint8_t color = 0;
            unsigned plane;
            size_t row_start = (size_t)row * source_row_bytes;
            for (plane = 0; plane < 4; ++plane) {
                size_t offset = row_start + (size_t)plane * plane_row_bytes + byte_in_plane;
                if ((bits[offset] & mask) != 0)
                    color |= (uint8_t)(1u << plane);
            }
            portable_put_pixel(&graphics->framebuffer,
                               (int32_t)x + px, (int32_t)y + row, color);
        }
    }
    return SIM_GRAPHICS_OK;
}

static SimGraphicsDriver *require_bitmap_owner(void)
{
    SimGraphicsDriver *graphics = sim_graphics_source_clip_owner();
    if (graphics == NULL)
        abort();
    return graphics;
}

static void source_g9150_callback(int16_t x, int16_t y, char *bitmap,
                                  int16_t width, int16_t height)
{
    SimGraphicsDriver *graphics = require_bitmap_owner();
    graphics->last_status = draw_planar4(graphics, x, y,
                                         (const uint8_t *)bitmap,
                                         width, height);
}

static void source_g914C_callback(int16_t x, int16_t y, char *bitmap,
                                  int16_t width, int16_t height)
{
    SimGraphicsDriver *graphics = require_bitmap_owner();
    if (sim_graphics_source_clip_active()) {
        /* This is the live pointer-nullness branch corresponding to the high
         * segment word g5AAE in DOS; execute the real generated clip helper. */
        f_1D8E_07F6(NULL, x, y, bitmap, width, height);
        return;
    }
    fd_55B3_3DE6 = 0;
    fd_55B3_3DE8 = 0;
    graphics->last_status = draw_planar4(graphics, x, y,
                                         (const uint8_t *)bitmap,
                                         width, height);
}

SimGraphicsStatus sim_graphics_source_bitmap_bind(SimGraphicsDriver *graphics)
{
    SimGraphicsStatus status = sim_graphics_source_clip_bind(graphics);
    if (status != SIM_GRAPHICS_OK)
        return status;
    g_914C = source_g914C_callback;
    g_9150 = source_g9150_callback;
    return SIM_GRAPHICS_OK;
}

void sim_graphics_source_bitmap_unbind(void)
{
    if (sim_graphics_source_clip_owner() != NULL)
        sim_graphics_source_clip_unbind();
    g_914C = NULL;
    g_9150 = NULL;
}
