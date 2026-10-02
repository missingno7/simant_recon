#include "font.h"

#include <stdlib.h>
#include <string.h>

static uint16_t read_be16(const uint8_t *p)
{
    return (uint16_t)(((uint16_t)p[0] << 8) | p[1]);
}

static int16_t read_be_i16(const uint8_t *p)
{
    return (int16_t)read_be16(p);
}

static int packed_bit(const uint8_t *bytes, size_t row_bytes, size_t row, size_t bit)
{
    return (bytes[row * row_bytes + (bit >> 3)] >> (7u - (unsigned)(bit & 7u))) & 1;
}

void portable_font_destroy(PortableFont *font)
{
    if (font == NULL)
        return;
    free(font->image);
    free(font->loc_table);
    free(font->ow_table);
    memset(font, 0, sizeof(*font));
}

void portable_font_init(PortableFont *font)
{
    if (font != NULL)
        memset(font, 0, sizeof(*font));
}

PortableRenderStatus portable_font_load(PortableFont *font,
                                        const uint8_t *bytes,
                                        size_t size)
{
    PortableFont parsed;
    size_t image_size, tables_size, need, i;
    int32_t count;
    if (font == NULL || bytes == NULL)
        return PORTABLE_RENDER_INVALID_ARGUMENT;
    memset(&parsed, 0, sizeof(parsed));
    if (size < 26)
        return PORTABLE_RENDER_TRUNCATED_DATA;
    for (i = 0; i < 13; ++i)
        parsed.metrics[i] = read_be_i16(bytes + i * 2u);
    if (parsed.metrics[2] < parsed.metrics[1] || parsed.metrics[7] <= 0 ||
        parsed.metrics[12] <= 0)
        return PORTABLE_RENDER_INVALID_RESOURCE;
    if (parsed.metrics[7] > 16)
        return PORTABLE_RENDER_INVALID_RESOURCE;
    parsed.first_char = (uint16_t)parsed.metrics[1];
    parsed.last_char = (uint16_t)parsed.metrics[2];
    count = (int32_t)parsed.last_char - parsed.first_char + 3;
    if (count <= 0)
        return PORTABLE_RENDER_INVALID_RESOURCE;
    parsed.table_count = (size_t)count;
    parsed.missing_char = (uint16_t)(parsed.last_char - parsed.first_char + 1u);
    parsed.proportional = (parsed.metrics[0] & 0x2000) == 0;
    if ((size_t)parsed.metrics[12] > SIZE_MAX / ((size_t)parsed.metrics[7] * 2u))
        return PORTABLE_RENDER_INVALID_RESOURCE;
    image_size = (size_t)parsed.metrics[12] * (size_t)parsed.metrics[7] * 2u;
    if (parsed.table_count > SIZE_MAX / 4u)
        return PORTABLE_RENDER_INVALID_RESOURCE;
    tables_size = parsed.table_count * 4u;
    if (image_size > SIZE_MAX - 26u || tables_size > SIZE_MAX - 26u - image_size)
        return PORTABLE_RENDER_INVALID_RESOURCE;
    need = 26u + image_size + tables_size;
    if (need > size)
        return PORTABLE_RENDER_TRUNCATED_DATA;
    parsed.image = (uint8_t *)malloc(image_size);
    parsed.loc_table = (int16_t *)malloc(parsed.table_count * sizeof(*parsed.loc_table));
    parsed.ow_table = (int16_t *)malloc(parsed.table_count * sizeof(*parsed.ow_table));
    if (parsed.image == NULL || parsed.loc_table == NULL || parsed.ow_table == NULL) {
        portable_font_destroy(&parsed);
        return PORTABLE_RENDER_INVALID_RESOURCE;
    }
    memcpy(parsed.image, bytes + 26u, image_size);
    for (i = 0; i < parsed.table_count; ++i) {
        parsed.loc_table[i] = read_be_i16(bytes + 26u + image_size + i * 2u);
        parsed.ow_table[i] = read_be_i16(bytes + 26u + image_size +
                                               parsed.table_count * 2u + i * 2u);
    }
    parsed.image_size = image_size;
    portable_font_destroy(font);
    *font = parsed;
    return PORTABLE_RENDER_OK;
}

static size_t font_index(const PortableFont *font, uint8_t ch)
{
    if ((size_t)ch >= font->table_count || font->ow_table[ch] == -1)
        return font->missing_char < font->table_count ? font->missing_char : 0;
    return ch;
}

int32_t portable_font_char_width(const PortableFont *font, uint8_t ch)
{
    size_t index;
    int32_t width;
    if (font == NULL || font->ow_table == NULL)
        return 0;
    if (!font->proportional)
        return font->metrics[3];
    index = font_index(font, ch);
    width = (uint8_t)font->ow_table[index];
    if (font->metrics[4] < 0)
        ++width;
    return width;
}

int32_t portable_font_string_width(const PortableFont *font,
                                   const uint8_t *text,
                                   size_t length)
{
    size_t i;
    int64_t width = 0;
    if (font == NULL || (text == NULL && length != 0))
        return 0;
    if (!font->proportional)
        return length > (size_t)(INT32_MAX / (font->metrics[3] > 0 ? font->metrics[3] : 1))
                   ? INT32_MAX
                   : (int32_t)length * font->metrics[3];
    for (i = 0; i < length; ++i)
        width += portable_font_char_width(font, text[i]);
    return width > INT32_MAX ? INT32_MAX : (int32_t)width;
}

PortableRenderStatus portable_font_draw(PortableFramebuffer *fb,
                                        const PortableFont *font,
                                        int32_t x,
                                        int32_t y,
                                        const uint8_t *text,
                                        size_t length,
                                        uint8_t foreground,
                                        int32_t *end_x)
{
    size_t i;
    int64_t pen;
    size_t source_row_bytes;
    int32_t glyph_rows;
    if (fb == NULL || fb->pixels == NULL || font == NULL || font->image == NULL ||
        font->loc_table == NULL || font->ow_table == NULL ||
        (text == NULL && length != 0))
        return PORTABLE_RENDER_INVALID_ARGUMENT;
    source_row_bytes = (size_t)font->metrics[12] * 2u;
    glyph_rows = font->metrics[7] - 1;
    pen = x;
    for (i = 0; i < length; ++i) {
        size_t index = font_index(font, text[i]);
        int32_t sx = font->loc_table[index];
        int32_t ex = font->loc_table[index + 1u];
        int32_t width = ex - sx;
        int32_t advance = font->proportional ? (uint8_t)font->ow_table[index]
                                             : font->metrics[3];
        int32_t x_offset;
        int32_t row, col;
        if (sx < 0 || ex < sx || (size_t)ex > source_row_bytes * 8u ||
            (size_t)font->metrics[7] > font->image_size / source_row_bytes)
            return PORTABLE_RENDER_INVALID_RESOURCE;
        if (font->metrics[4] < 0) {
            x_offset = 0;
            ++advance;
        } else {
            x_offset = font->metrics[4] + ((uint16_t)font->ow_table[index] >> 8);
        }
        for (row = 0; row < glyph_rows; ++row)
            for (col = 0; col < width; ++col)
                /* font_MakeImage advances its source pointer by one full
                 * row before calling f_2650_000F. */
                if (packed_bit(font->image, source_row_bytes, (size_t)row + 1u,
                               (size_t)sx + (size_t)col)) {
                    int64_t dx = pen + x_offset + col;
                    int64_t dy = (int64_t)y + row;
                    if (dx >= INT32_MIN && dx <= INT32_MAX && dy >= INT32_MIN && dy <= INT32_MAX)
                        portable_put_pixel(fb, (int32_t)dx, (int32_t)dy, foreground);
                }
        pen += advance;
        if (pen > INT32_MAX)
            pen = INT32_MAX;
        else if (pen < INT32_MIN)
            pen = INT32_MIN;
    }
    if (end_x != NULL)
        *end_x = (int32_t)pen;
    return PORTABLE_RENDER_OK;
}
