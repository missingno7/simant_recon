#include "portable/whole_program/platform/graphics_capture_source.h"
#include "portable/whole_program/platform/graphics_entry_source.h"
#include "portable/whole_program/platform/graphics_source_clip.h"
#include "portable/whole_program/platform/m1b73_mouse_state.h"

#include <stdint.h>
#include <stdio.h>
#include <string.h>

uint16_t g_3DD4;
char *g_3DA8;

SimGraphicsStatus sim_source_font_bind_driver_view_v1(SimGraphicsDriver *graphics)
{
    (void)graphics;
    return SIM_GRAPHICS_FONT_UNBOUND;
}

void f_1D8E_0384(SimGraphicsPatternRectCallback callback, int16_t unused1,
                 int16_t unused2, int16_t left, int16_t top, int16_t right,
                 int16_t bottom, int16_t pattern)
{
    (void)callback; (void)unused1; (void)unused2; (void)left; (void)top;
    (void)right; (void)bottom; (void)pattern;
}

void f_1D8E_070E(char *port, int16_t x, int16_t y, char *bits,
                 int16_t width, int16_t height)
{
    (void)port; (void)x; (void)y; (void)bits; (void)width; (void)height;
}

void f_1D8E_07F6(char *port, int16_t x, int16_t y, char *bits,
                 int16_t width, int16_t height)
{
    (void)port; (void)x; (void)y; (void)bits; (void)width; (void)height;
}

static uint8_t source_pixel(int x, int y)
{
    return (uint8_t)((x * 3 + y * 5 + (x >> 2) + (y >> 1)) & 15);
}

int main(void)
{
    SimGraphicsDriver graphics;
    uint8_t save_under[2596];
    uint8_t other[2596];
    uint8_t pixel;
    size_t needed = 0;
    int x, y, plane, bit;

    memset(&graphics, 0, sizeof(graphics));
    if (sim_graphics_init(&graphics) != SIM_GRAPHICS_OK ||
        sim_graphics_set_mode(&graphics, SIM_GRAPHICS_MODE_VGA_640X480) !=
            SIM_GRAPHICS_OK ||
        sim_graphics_bind_source_abi(&graphics,
                                     sim_graphics_source_clip_slot()) !=
            SIM_GRAPHICS_OK ||
        sim_graphics_source_capture_bind(&graphics) != SIM_GRAPHICS_OK)
        return 2;
    for (y = 0; y < 480; ++y)
        for (x = 0; x < 640; ++x)
            graphics.pixel_storage[(size_t)y * 640u + (size_t)x] =
                source_pixel(x, y);

    /* Generic checked captures stay bounded even when the source cursor can
     * capture a padded save-under rectangle beyond the viewport. */
    if (sim_graphics_s00_capture_size_checked(&graphics, 632, 478,
            655, 510, &needed) != SIM_GRAPHICS_INVALID_ARGUMENT ||
        sim_graphics_s00_capture_rect(&graphics, 632, 478, 655, 510,
            save_under, sizeof(save_under)) != SIM_GRAPHICS_INVALID_ARGUMENT)
        return 3;

    memset(save_under, 0xa5, sizeof(save_under));
    if (sim_graphics_source_capture_cursor_buffer(save_under,
            sizeof(save_under)) != SIM_GRAPHICS_OK ||
        sim_graphics_source_capture_cursor_buffer(other,
            sizeof(other)) == SIM_GRAPHICS_OK)
        return 4;
    g_4333 = 1; /* source cursor-update lock suppresses unrelated callbacks */
    g_3DD4 = UINT16_C(0x5a07);
    g_9148(632, 478, 655, 510, (char *)save_under);
    sim_graphics_source_capture_cursor_buffer_clear(other);
    if (sim_graphics_source_last_status() != SIM_GRAPHICS_OK ||
        g_3DD4 != UINT16_C(0x5a07) ||
        save_under[0] != 24 || save_under[1] != 0 ||
        save_under[2] != 32 || save_under[3] != 0)
        return 5;

    /* The source buffer is 24x32, while only [632,640)x[478,480) is visible.
     * Compare every visible plane bit, then require deterministic zero padding
     * for pixels that cannot reach the destination through the full-screen
     * source clip list. */
    for (y = 0; y < 32; ++y) {
        for (plane = 0; plane < 4; ++plane) {
            for (x = 0; x < 3; ++x) {
                uint8_t expected = 0;
                for (bit = 0; bit < 8; ++bit) {
                    int px = 632 + x * 8 + bit;
                    int py = 478 + y;
                    if (px < 640 && py < 480 &&
                        (source_pixel(px, py) & (1u << plane)) != 0)
                        expected |= (uint8_t)(0x80u >> bit);
                }
                pixel = save_under[4u + (size_t)y * 12u +
                                   (size_t)plane * 3u + (size_t)x];
                if (pixel != expected)
                    return 6;
            }
        }
    }
    sim_graphics_source_capture_cursor_buffer_clear(save_under);
    sim_graphics_source_capture_unbind();
    sim_graphics_bind_source_abi(NULL, NULL);
    sim_graphics_destroy(&graphics);
    puts("cursor edge save-under: full size, visible bits, safe padding passed");
    return 0;
}
