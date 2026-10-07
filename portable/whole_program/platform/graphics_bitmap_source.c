#include "canonical_graphics_data.h"
extern void (*driver_callback_table[25])();
#include "graphics_bitmap_source.h"

#include "graphics_source_clip.h"
#include "graphics_source_cursor_effects.h"
#include "portable/whole_program/window_source_globals.h"

#include <stdint.h>
#include <stdlib.h>
#include <string.h>
extern void f_1D8E_07F6(char *port, int16_t x, int16_t y, char *bits,
                       int16_t width, int16_t height);

static int16_t source_word_add(int16_t left, int16_t right)
{
    uint16_t bits = (uint16_t)((uint16_t)left + (uint16_t)right);
    int16_t result;
    memcpy(&result, &bits, sizeof(result));
    return result;
}

static int16_t source_word_sub(int16_t left, int16_t right)
{
    uint16_t bits = (uint16_t)((uint16_t)left - (uint16_t)right);
    int16_t result;
    memcpy(&result, &bits, sizeof(result));
    return result;
}

static SimGraphicsStatus draw_planar4(SimGraphicsDriver *graphics,
                                      int16_t x, int16_t y,
                                      const uint8_t *bits,
                                      int16_t width, int16_t height)
{
    size_t plane_row_bytes;
    size_t source_row_bytes;
    int32_t sx0, sx1;
    int32_t row, px;
    uint8_t operation;
    int16_t cut_left = fd_55B3_3DE6;
    int16_t cut_right = fd_55B3_3DE8;

    if (graphics == NULL || graphics->pixel_storage == NULL || bits == NULL ||
        width <= 0 || height <= 0)
        return SIM_GRAPHICS_INVALID_ARGUMENT;
    /* The admitted S00 planar source supports replace plus the three DOS
     * logic operations selected by f_1B4E's driver-entry callbacks. */
    operation = (uint8_t)g_3DD2;
    if ((((uint8_t)g_5A97) & 1u) != 0 ||
        (operation != 0 && operation != 0x08u && operation != 0x10u &&
         operation != 0x18u))
        return SIM_GRAPHICS_UNSUPPORTED_MODE;
    if (cut_left < 0 || cut_right < 0 ||
        (int32_t)cut_left + (int32_t)cut_right > width)
        return SIM_GRAPHICS_INVALID_ARGUMENT;

    plane_row_bytes = ((size_t)(uint16_t)width + 7u) / 8u;
    source_row_bytes = plane_row_bytes * 4u;
    sx0 = cut_left;
    sx1 = (int32_t)width - cut_right;
    if (!sim_graphics_source_cursor_effects_begin(
            source_word_add(x, cut_left), y,
            source_word_sub(source_word_add(x, width), cut_right),
            source_word_add(y, height)))
        return SIM_GRAPHICS_UNSUPPORTED_MODE;
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
            if (operation != 0) {
                uint8_t old = sim_graphics_vga_get(graphics, (int32_t)x + px, (int32_t)y + row);
                color = operation == 8 ? (old & color) : operation == 16 ? (old | color) : (old ^ color);
            }
            sim_graphics_vga_put(graphics,
                               (int32_t)x + px, (int32_t)y + row, color);
        }
    }
    if (!sim_graphics_source_cursor_effects_end())
        return SIM_GRAPHICS_UNSUPPORTED_MODE;
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
    (*( SimGraphicsBitmapCallback *)(void *)&driver_callback_table[9]) = source_g914C_callback;
    (*( SimGraphicsBitmapCallback *)(void *)&driver_callback_table[10]) = source_g9150_callback;
    return SIM_GRAPHICS_OK;
}

void sim_graphics_source_bitmap_unbind(void)
{
    if (sim_graphics_source_clip_owner() != NULL)
        sim_graphics_source_clip_unbind();
    (*( SimGraphicsBitmapCallback *)(void *)&driver_callback_table[9]) = NULL;
    (*( SimGraphicsBitmapCallback *)(void *)&driver_callback_table[10]) = NULL;
}
