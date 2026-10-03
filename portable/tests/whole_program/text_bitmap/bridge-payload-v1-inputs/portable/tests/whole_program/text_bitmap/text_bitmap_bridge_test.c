#include "portable/whole_program/platform/graphics.h"
#include "portable/whole_program/platform/graphics_source_clip.h"
#include "portable/whole_program/state/font_pointer_state_v1.h"
#include "portable/whole_program/text_bitmap_bridge.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* This focused unit does not activate DOS clipped drawing or a custom font
 * handle. Keep those external generated boundaries fail-closed if a future
 * test accidentally reaches them. */
char *g_3DA8;

SimGraphicsStatus sim_source_font_bind_driver_view_v1(SimGraphicsDriver *graphics)
{
    (void)graphics;
    return SIM_GRAPHICS_FONT_UNBOUND;
}

void f_1D8E_0384(SimGraphicsPatternRectCallback callback,
                 int16_t unused1, int16_t unused2,
                 int16_t left, int16_t top, int16_t right,
                 int16_t bottom, int16_t color)
{
    (void)callback; (void)unused1; (void)unused2;
    (void)left; (void)top; (void)right; (void)bottom; (void)color;
    abort();
}

void f_1D8E_070E(char *port, int16_t x, int16_t y, char *bits,
                 int16_t width, int16_t height)
{
    (void)port; (void)x; (void)y; (void)bits; (void)width; (void)height;
    abort();
}

static int check(int condition, const char *message)
{
    if (!condition) {
        fprintf(stderr, "FAIL: %s\n", message);
        return 0;
    }
    return 1;
}

static SimGraphicsBitmapCallback saved_g9154;
static uint8_t captured_bitmap[PORTABLE_TEXT_BITMAP_CAPACITY];
static size_t captured_bitmap_size;
static int captured_bitmap_dimensions_ok;

static void capture_g9154(int16_t x, int16_t y, char *bitmap,
                          int16_t width, int16_t height)
{
    size_t stride = ((size_t)(uint16_t)width + 7u) / 8u;
    size_t byte_count = stride * (size_t)(uint16_t)height;

    captured_bitmap_size = 0;
    captured_bitmap_dimensions_ok = width > 0 && height > 0 &&
        byte_count <= sizeof(captured_bitmap) && bitmap != NULL;
    if (captured_bitmap_dimensions_ok) {
        memcpy(captured_bitmap, bitmap, byte_count);
        captured_bitmap_size = byte_count;
    }
    saved_g9154(x, y, bitmap, width, height);
}

int main(void)
{
    SimGraphicsDriver graphics;
    uint8_t glyphs[256u * 14u];
    uint8_t fold_window[256];
    const PortableTextBitmapState *state;
    size_t i;
    size_t pixel_count = 0;

    for (i = 0; i < sizeof(glyphs); ++i)
        glyphs[i] = (uint8_t)(0x81u ^ (uint8_t)(i * 29u));
    memset(fold_window, 0x20, sizeof(fold_window));
    fold_window[0x80] = 'A';
    fold_window[0xa7] = 'Z';

    if (!check(sim_graphics_init(&graphics) == SIM_GRAPHICS_OK,
               "graphics owner initializes")) return 1;
    if (!check(sim_graphics_set_glyph_source(&graphics, glyphs, sizeof(glyphs),
                                             14, 8, 14) == SIM_GRAPHICS_OK,
               "real source glyph owner binds")) return 1;
    if (!check(sim_graphics_bind_source_abi(&graphics,
                                             sim_graphics_source_clip_slot()) ==
               SIM_GRAPHICS_OK, "source graphics ABI binds")) return 1;
    if (!check(portable_text_bitmap_bind_source(0, NULL, 0) ==
               PORTABLE_TEXT_BITMAP_OK, "ASCII source context binds")) return 1;

    f_1FBD_0000(17, 21, "ASCII");
    state = portable_text_bitmap_source_state();
    if (!check(portable_text_bitmap_source_status() == PORTABLE_TEXT_BITMAP_OK,
               "actual source ABI call renders ASCII")) return 1;
    if (!check(state->width == 40 && state->height == 14,
               "source bitmap header geometry")) return 1;
    saved_g9154 = g_9154;
    captured_bitmap_size = 0;
    captured_bitmap_dimensions_ok = 0;
    g_9154 = capture_g9154;
    f_1FBD_0000(17, 21, "ASCII");
    state = portable_text_bitmap_source_state();
    g_9154 = saved_g9154;
    if (!check(captured_bitmap_dimensions_ok &&
               captured_bitmap_size == 5u * 14u &&
               memcmp(captured_bitmap, state->pixels, captured_bitmap_size) == 0,
               "g9154 receives exact monochrome payload bytes, without its width/height header"))
        return 1;
    {
        uint8_t old_header_first[4] = {40u, 0u, 14u, 0u};
        if (!check(memcmp(old_header_first, state->pixels,
                          sizeof(old_header_first)) != 0,
                   "negative control rejects passing the old header-prefixed pointer"))
            return 1;
    }
    if (!check(graphics.g_3DA0 == 57 && graphics.g_3DA2 == 21,
               "source text pen updated after draw")) return 1;
    for (i = 0; i < graphics.pixel_storage_size; ++i)
        if (graphics.pixel_storage[i] != 0) ++pixel_count;
    if (!check(pixel_count != 0, "bitmap sink draws into the owned framebuffer"))
        return 1;

    if (!check(sim_graphics_set_glyph_source(&graphics, glyphs, sizeof(glyphs),
                                             6, 4, 6) == SIM_GRAPHICS_OK,
               "source four-pixel glyph owner binds")) return 1;
    if (!check(portable_text_bitmap_bind_source(0, NULL, 0) ==
               PORTABLE_TEXT_BITMAP_OK, "four-pixel ASCII context binds")) return 1;
    f_1FBD_0000(5, 9, "AB");
    state = portable_text_bitmap_source_state();
    if (!check(portable_text_bitmap_source_status() == PORTABLE_TEXT_BITMAP_OK &&
               state->width == 8 && state->height == 6,
               "four-pixel ASCII uses paired source glyphs")) return 1;

    f_1FBD_0000(5, 9, "\x80");
    if (!check(portable_text_bitmap_source_status() ==
               PORTABLE_TEXT_BITMAP_UNSUPPORTED_CHARACTER,
               "unbound raw DGROUP fold span rejects high bytes")) return 1;
    if (!check(portable_text_bitmap_bind_source(0, fold_window,
                                                sizeof(fold_window)) ==
               PORTABLE_TEXT_BITMAP_OK, "live source-state span binds")) return 1;
    f_1FBD_0000(5, 9, "\x80\xa7");
    state = portable_text_bitmap_source_state();
    if (!check(portable_text_bitmap_source_status() == PORTABLE_TEXT_BITMAP_OK &&
               state->width == 8,
               "explicit raw source-state span supports non-ASCII indexes")) return 1;

    if (!check(portable_text_bitmap_bind_source(6, NULL, 0) ==
               PORTABLE_TEXT_BITMAP_OK, "profile-6 direct context binds")) return 1;
    if (!check(sim_graphics_set_glyph_source(&graphics, glyphs, sizeof(glyphs),
                                             6, 8, 6) == SIM_GRAPHICS_OK,
               "direct-text glyph geometry binds")) return 1;
    f_1FBD_0000(33, 12, "direct");
    if (!check(portable_text_bitmap_source_status() == PORTABLE_TEXT_BITMAP_OK &&
               graphics.g_3DA0 == 81 && graphics.g_3DA2 == 12,
               "profile-6 follows direct text sink path")) return 1;

    portable_text_bitmap_unbind_source();
    f_1FBD_0000(0, 0, "unbound");
    if (!check(portable_text_bitmap_source_status() ==
               PORTABLE_TEXT_BITMAP_INVALID_ARGUMENT,
               "unbound source context fails closed")) return 1;
    (void)sim_graphics_bind_source_abi(NULL, NULL);
    sim_graphics_destroy(&graphics);
    puts("PASS text bitmap ABI bridge");
    return 0;
}
