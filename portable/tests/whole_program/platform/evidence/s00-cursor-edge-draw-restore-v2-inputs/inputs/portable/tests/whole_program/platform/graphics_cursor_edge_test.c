#include "portable/whole_program/platform/graphics_bitmap_source.h"
#include "portable/whole_program/platform/graphics_capture_source.h"
#include "portable/whole_program/platform/graphics_cursor_source.h"
#include "portable/whole_program/platform/graphics_entry_source.h"
#include "portable/whole_program/platform/graphics_source_clip.h"
#include "portable/whole_program/platform/m1b73_mouse_state.h"

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

uint16_t g_3DD4;
char **g_3D10, **g_3D14, **g_3D18, **g_3D1C;
char g_5A97;
char *g_3DA8;

SimGraphicsStatus sim_source_font_bind_driver_view_v1(SimGraphicsDriver *graphics)
{
    (void)graphics;
    return SIM_GRAPHICS_FONT_UNBOUND;
}

typedef struct ResourceRecord {
    const uint8_t *data;
    size_t size;
} ResourceRecord;

static ResourceRecord resources[2];

static int measure_resource(void *context, const uint8_t *resource,
                            size_t *size_out)
{
    unsigned i;
    (void)context;
    if (size_out == NULL)
        return 0;
    for (i = 0; i < 2; ++i) {
        if (resources[i].data == resource) {
            *size_out = resources[i].size;
            return 1;
        }
    }
    return 0;
}

static int resolve_handle(void *context, const void *handle,
                          const uint8_t **bytes_out, size_t *size_out)
{
    const uint8_t *const *slot = (const uint8_t *const *)handle;
    (void)context;
    return slot != NULL && *slot != NULL &&
        measure_resource(context, *slot, size_out) &&
        ((*bytes_out = *slot) != NULL);
}

static void init_mask(uint8_t *bits, uint16_t width, uint16_t height)
{
    size_t row_bytes = ((size_t)width + 7u) / 8u;
    bits[0] = (uint8_t)width;
    bits[1] = (uint8_t)(width >> 8);
    bits[2] = (uint8_t)height;
    bits[3] = (uint8_t)(height >> 8);
    memset(bits + 4, 0xff, row_bytes * height);
}

static void init_image(uint8_t *bits, uint16_t width, uint16_t height)
{
    size_t row_bytes = ((size_t)width + 7u) / 8u;
    unsigned y, plane;
    bits[0] = (uint8_t)width;
    bits[1] = (uint8_t)(width >> 8);
    bits[2] = (uint8_t)height;
    bits[3] = (uint8_t)(height >> 8);
    for (y = 0; y < height; ++y)
        for (plane = 0; plane < 4; ++plane)
            memset(bits + 4u + (size_t)y * row_bytes * 4u +
                   (size_t)plane * row_bytes, 0xff, row_bytes);
}

static int run_edge_case(SimGraphicsDriver *graphics,
                         SimGraphicsCursorSource *cursor,
                         uint8_t *baseline, int16_t *source_ax,
                         int screen_clip)
{
    uint8_t *pixels = sim_graphics_pixels(graphics, NULL);
    int x, y;
    g_5A9C = (struct Rect){0, 0,
        (int16_t)(screen_clip ? 630 : 640),
        (int16_t)(screen_clip ? 470 : 480)};
    memcpy(baseline, pixels, 640u * 480u);
    if (!portable_m1b73_graphics_cursor_mode(cursor, 1, source_ax) ||
        sim_graphics_source_last_status() != SIM_GRAPHICS_OK)
        return 0;
    if (screen_clip) {
        if (memcmp(pixels, baseline, 640u * 480u) != 0)
            return 0;
    } else {
        for (y = 0; y < 480; ++y) {
            for (x = 0; x < 640; ++x) {
                uint8_t expected = baseline[(size_t)y * 640u + (size_t)x];
                if (x >= 632 && y == 479)
                    expected ^= 0x0f;
                if (pixels[(size_t)y * 640u + (size_t)x] != expected)
                    return 0;
            }
        }
    }
    if (!portable_m1b73_graphics_cursor_mode(cursor, 2, source_ax) ||
        sim_graphics_source_last_status() != SIM_GRAPHICS_OK ||
        memcmp(pixels, baseline, 640u * 480u) != 0)
        return 0;
    return 1;
}

int main(void)
{
    SimGraphicsDriver graphics;
    SimGraphicsCursorSource cursor;
    SimGraphicsCursorSourceBindings bindings;
    uint8_t mask[4u + 2u * 16u];
    uint8_t image[4u + 2u * 16u * 4u];
    uint8_t baseline[640u * 480u];
    const uint8_t *mask_view = mask;
    const uint8_t *image_view = image;
    uint8_t shift_state = 0;
    uint16_t hide_active = 0;
    int16_t hide_rect[4] = {0, 0, 0, 0};
    int16_t source_ax = -1;
    size_t i;

    memset(&graphics, 0, sizeof(graphics));
    memset(&cursor, 0, sizeof(cursor));
    if (sim_graphics_init(&graphics) != SIM_GRAPHICS_OK ||
        sim_graphics_set_mode(&graphics, SIM_GRAPHICS_MODE_VGA_640X480) !=
            SIM_GRAPHICS_OK ||
        sim_graphics_bind_source_abi(&graphics,
                                     sim_graphics_source_clip_slot()) !=
            SIM_GRAPHICS_OK ||
        sim_graphics_source_entry_bind(&graphics) != SIM_GRAPHICS_OK ||
        sim_graphics_source_bitmap_bind(&graphics) != SIM_GRAPHICS_OK ||
        sim_graphics_source_capture_bind(&graphics) != SIM_GRAPHICS_OK)
        return 2;

    init_mask(mask, 16, 16);      /* kind 7: one-plane AND mask */
    init_image(image, 16, 16);    /* kind 8: four-plane XOR image */
    resources[0] = (ResourceRecord){ mask, sizeof(mask) };
    resources[1] = (ResourceRecord){ image, sizeof(image) };
    *portable_m1b73_mouse_asm_state.cursor_image = mask;
    *portable_m1b73_mouse_asm_state.cursor_mask = image;
    *portable_m1b73_mouse_asm_state.x = 639;
    *portable_m1b73_mouse_asm_state.y = 479;
    *portable_m1b73_mouse_asm_state.cursor_update_lock = 1;
    *portable_m1b73_mouse_asm_state.cursor_show_level = 1;
    g_5A97 = 8;
    for (i = 0; i < sizeof(baseline); ++i)
        graphics.pixel_storage[i] = (uint8_t)((i * 13u + i / 640u) & 0x0fu);

    memset(&bindings, 0, sizeof(bindings));
    bindings.graphics = &graphics;
    bindings.source_shift_state = &shift_state;
    bindings.hide_rectangle_active = &hide_active;
    bindings.hide_rectangle = hide_rect;
    bindings.measure_active_resource = measure_resource;
    bindings.resolve_handle = resolve_handle;
    if (sim_graphics_source_cursor_bind(&cursor, &bindings) != SIM_GRAPHICS_OK)
        return 3;

    if (!run_edge_case(&graphics, &cursor, baseline, &source_ax, 0) ||
        *portable_m1b73_mouse_asm_state.cursor_right != 655 ||
        *portable_m1b73_mouse_asm_state.cursor_bottom != 495 ||
        portable_m1b73_cursor_save_under[0] != 24 ||
        portable_m1b73_cursor_save_under[1] != 0 ||
        portable_m1b73_cursor_save_under[2] != 16 ||
        portable_m1b73_cursor_save_under[3] != 0)
        return 4;
    if (!run_edge_case(&graphics, &cursor, baseline, &source_ax, 1))
        return 5;

    sim_graphics_source_cursor_unbind(&cursor);
    sim_graphics_source_capture_unbind();
    sim_graphics_source_bitmap_unbind();
    sim_graphics_source_entry_unbind();
    sim_graphics_bind_source_abi(NULL, NULL);
    sim_graphics_destroy(&graphics);
    puts("cursor edge draw/restore and negative full-screen clip passed");
    return 0;
}
