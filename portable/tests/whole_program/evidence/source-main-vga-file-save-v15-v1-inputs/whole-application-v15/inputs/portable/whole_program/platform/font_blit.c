#include "font_blit.h"

#include "../algorithms/asm_utilities.h"

#include <stdint.h>
#include <stdlib.h>

struct Bitmap *sim_font_make_image_source(uint8_t *s, int16_t x, struct Font *font);
int16_t _font_StringWidth(uint8_t *s, struct Font *font);

char g_5ABE[SIM_FONT_BITMAP_CAPACITY];
int16_t fd_55B3_6770;
int16_t fd_55B3_6772;
static int g_blit_status;
static const uint8_t *g_source_begin;
static size_t g_source_size;
struct Bitmap fd_50F6_392C = {0, 0, g_5ABE};

struct Bitmap *sim_font_bitmap_bind(void)
{
    fd_50F6_392C.bits = g_5ABE;
    return &fd_50F6_392C;
}

void sim_font_blit_reset_status(void)
{
    g_blit_status = 0;
}

int sim_font_blit_last_status(void)
{
    return g_blit_status;
}

struct Bitmap *sim_font_make_image(uint8_t *text, int16_t x, struct Font *font)
{
    struct Bitmap *bitmap;
    int32_t string_width, stride;
    size_t image_extent, output_extent;
    if (!text || !font || x < 0 || !font->image || font->rowWords <= 0 ||
        font->fRectHeight <= 1 || font->fRectWidth <= 0 ||
        font->fRectHeight > 4096) {
        g_blit_status = 1;
        return NULL;
    }
    string_width = _font_StringWidth(text, font);
    if (string_width < 0 || string_width > INT16_MAX - x) {
        g_blit_status = 1;
        return NULL;
    }
    stride = (string_width + x + 7) / 8;
    if (stride < 1)
        stride = 1;
    output_extent = (size_t)stride * (size_t)(font->fRectHeight - 1);
    /* font_MakeImage clears the source-defined 80x16 canvas (1280 bytes). */
    if (output_extent > sizeof(g_5ABE) || 1280u > sizeof(g_5ABE)) {
        g_blit_status = 1;
        return NULL;
    }
    image_extent = (size_t)(uint16_t)font->rowWords * 2u * (uint16_t)font->fRectHeight;
    /* font_ReadFont requests this image with the source's uint16 size ABI. */
    if (image_extent == 0 || image_extent > UINT16_MAX ||
        (uint32_t)(uint16_t)font->rowWords * 2u > INT16_MAX) {
        g_blit_status = 1;
        return NULL;
    }
    g_source_begin = (const uint8_t *)font->image;
    g_source_size = image_extent;
    sim_font_blit_reset_status();
    bitmap = sim_font_make_image_source(text, x, font);
    g_source_begin = NULL;
    g_source_size = 0;
    if (g_blit_status != 0)
        return NULL;
    return bitmap;
}

struct Bitmap *font_MakeImage(uint8_t *text, int16_t x, struct Font *font)
{
    struct Bitmap *bitmap = sim_font_make_image(text, x, font);
    if (!bitmap)
        abort();
    return bitmap;
}

static int validate_rows(const char *source, const char *destination,
                         int16_t width, int16_t height,
                         int16_t source_x, int16_t destination_x)
{
    size_t source_stride, destination_stride;
    uint32_t sx, dx, row_bytes;
    size_t final_offset;
    if (!source || !destination || width < 0 || height <= 0 ||
        fd_55B3_6770 <= 0 || fd_55B3_6772 <= 0)
        return 0;
    if (width == 0)
        return 1;
    source_stride = (uint16_t)fd_55B3_6770;
    destination_stride = (uint16_t)fd_55B3_6772;
    sx = (uint16_t)source_x;
    dx = (uint16_t)destination_x;
    if (sx + (uint16_t)width > source_stride * 8u ||
        dx + (uint16_t)width > destination_stride * 8u)
        return 0;
    if (g_source_begin) {
        uintptr_t source_address = (uintptr_t)source;
        uintptr_t source_begin = (uintptr_t)g_source_begin;
        size_t required = (size_t)((uint16_t)height - 1u) * source_stride +
                          ((sx + (uint16_t)width + 7u) / 8u);
        if (source_address < source_begin || source_address - source_begin > g_source_size ||
            required > g_source_size - (size_t)(source_address - source_begin))
            return 0;
    }
    if (destination == g_5ABE) {
        row_bytes = (dx + (uint16_t)width + 7u) / 8u;
        final_offset = (size_t)((uint16_t)height - 1u) * destination_stride + row_bytes;
        if (final_offset > sizeof(g_5ABE))
            return 0;
    }
    return 1;
}

void f_2650_000F(char *source, char *destination, int16_t width,
                 int16_t height, int16_t source_x, int16_t destination_x)
{
    const uint8_t *src = (const uint8_t *)source;
    uint8_t *dst = (uint8_t *)destination;
    uint32_t sx = (uint16_t)source_x;
    uint32_t dx = (uint16_t)destination_x;
    uint32_t y, x;
    if (width == 0 && height > 0)
        return;
    if (!validate_rows(source, destination, width, height, source_x, destination_x)) {
        g_blit_status = 1;
        return;
    }
    for (y = 0; y < (uint16_t)height; ++y) {
        const uint8_t *source_row = src + (size_t)y * (uint16_t)fd_55B3_6770;
        uint8_t *destination_row = dst + (size_t)y * (uint16_t)fd_55B3_6772;
        for (x = 0; x < (uint16_t)width; ++x) {
            uint32_t source_bit = sx + x;
            uint32_t destination_bit = dx + x;
            uint8_t source_mask = (uint8_t)(0x80u >> (source_bit & 7u));
            uint8_t destination_mask = (uint8_t)(0x80u >> (destination_bit & 7u));
            if (source_row[source_bit >> 3] & source_mask)
                destination_row[destination_bit >> 3] |= destination_mask;
        }
    }
}
