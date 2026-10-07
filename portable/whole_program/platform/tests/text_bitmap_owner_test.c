#include "canonical_graphics_data.h"
#include "font_blit.h"
#include "graphics.h"
#include "portable/whole_program/text_bitmap_bridge.h"

#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

void (*driver_callback_table[25])();
struct Bitmap fd_50F6_392C;

static SimGraphicsDriver graphics;
static uint8_t glyph_rows[256u * 14u];
static uint8_t sidecar[1280];
static char callback_bitmap_expected;
static int callback_seen;

SimGraphicsDriver *sim_graphics_source_owner(void)
{
    return &graphics;
}

SimGraphicsStatus sim_graphics_source_last_status(void)
{
    return graphics.last_status;
}

SimGraphicsStatus sim_graphics_f_1B4E_0081(
    SimGraphicsDriver *owner, int16_t x, int16_t y, const char *text)
{
    (void)owner;
    (void)x;
    (void)y;
    (void)text;
    return SIM_GRAPHICS_OK;
}

static void capture_bitmap(int16_t x, int16_t y, char *pixels,
                           int16_t width, int16_t height)
{
    (void)x;
    (void)y;
    assert(width == 8);
    assert(height == 14);
    assert((uint8_t *)pixels == CANONICAL_TEXT_BITMAP_PIXELS);
    callback_bitmap_expected = pixels[0];
    callback_seen = 1;
}

int16_t _font_StringWidth(uint8_t *text, struct Font *font)
{
    (void)text;
    (void)font;
    return 8;
}

struct Bitmap *sim_font_make_image_source(uint8_t *text, int16_t x,
                                          struct Font *font)
{
    (void)text;
    (void)x;
    (void)font;
    fd_50F6_392C.bits[0] = (char)0x5a;
    return &fd_50F6_392C;
}

static void install_bitmap_callback(void)
{
    union {
        SimGraphicsBitmapCallback typed;
        void (*raw)(void);
    } callback;
    callback.typed = capture_bitmap;
    driver_callback_table[11] = callback.raw;
}

static void test_f_1FBD_writes_canonical_owner(void)
{
    char text[] = "A";
    size_t row;

    memset(&g_5ABE, 0, sizeof(g_5ABE));
    memset(glyph_rows, 0, sizeof(glyph_rows));
    for (row = 0; row < 14; ++row)
        glyph_rows['A' * 14u + row] = (uint8_t)(0x80u >> (row & 7u));
    graphics.last_status = SIM_GRAPHICS_OK;
    graphics.glyph_source = glyph_rows;
    graphics.glyph_source_size = sizeof(glyph_rows);
    g_3DDA = 14;
    g_3DDC = 14;
    g_3DDE = 8;
    callback_seen = 0;
    install_bitmap_callback();

    assert(portable_text_bitmap_bind_source(1, NULL, 0) ==
           PORTABLE_TEXT_BITMAP_OK);
    f_1FBD_0000(0, 5, text);

    assert(portable_text_bitmap_source_status() == PORTABLE_TEXT_BITMAP_OK);
    assert(g_5ABA == 8);
    assert(g_5ABC == 14);
    assert(g_5ABE.aliases.g_5ABE[0] == 0x80);
    assert(g_5ABE.aliases.g_5ECE[0] == 'A');
    assert(g_5ABE.aliases.g_5F1D == 0);
    assert(g_5ECE[0] == 'A');
    assert(g_5F1D == 0);
    assert(callback_seen);
    assert((uint8_t)callback_bitmap_expected == g_5ABE.aliases.g_5ABE[0]);
    assert(g_3DA0.x == 8 && g_3DA0.y == 5);
}

static int test_font_make_image_writes_canonical_owner(int negative_control)
{
    char image[30] = {0};
    char text[] = "A";
    struct Font font;

    memset(&g_5ABE, 0, sizeof(g_5ABE));
    memset(sidecar, 0, sizeof(sidecar));
    memset(&font, 0, sizeof(font));
    font.fRectWidth = 8;
    font.fRectHeight = 15;
    font.rowWords = 1;
    font.image = image;
    fd_55B3_6770 = 1;
    fd_55B3_6772 = 1;
    sim_font_bitmap_bind();
    if (negative_control)
        fd_50F6_392C.bits = (char *)sidecar;

    if (font_MakeImage((uint8_t *)text, 0, &font) != &fd_50F6_392C)
        return 0;
    /* This check is the negative control: redirecting font_MakeImage to
     * duplicate backing must fail because canonical g_5ABE stays zero. */
    if (g_5ABE.clear_span[0] != 0x5a) {
        fprintf(stderr, "canonical owner check failed: g_5ABE[0] stayed zero\n");
        return 0;
    }
    return 1;
}

int main(int argc, char **argv)
{
    int negative_control = argc == 2 &&
        strcmp(argv[1], "--negative-control") == 0;
    test_f_1FBD_writes_canonical_owner();
    if (negative_control) {
        if (test_font_make_image_writes_canonical_owner(1))
            return 3;
        return 2;
    }
    assert(test_font_make_image_writes_canonical_owner(0));
    return 0;
}
