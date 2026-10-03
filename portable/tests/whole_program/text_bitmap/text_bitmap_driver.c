#include "portable/whole_program/text_bitmap.h"

#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int hex_value(char c)
{
    if (c >= '0' && c <= '9') return c - '0';
    if (c >= 'a' && c <= 'f') return c - 'a' + 10;
    if (c >= 'A' && c <= 'F') return c - 'A' + 10;
    return -1;
}

static int decode_hex(const char *text, uint8_t *out, size_t capacity,
                      size_t *length)
{
    size_t chars = strlen(text);
    size_t i;
    if ((chars & 1u) != 0 || chars / 2u > capacity) return 0;
    for (i = 0; i < chars / 2u; ++i) {
        int high = hex_value(text[i * 2u]);
        int low = hex_value(text[i * 2u + 1u]);
        if (high < 0 || low < 0) return 0;
        out[i] = (uint8_t)((high << 4) | low);
    }
    *length = chars / 2u;
    return 1;
}

static int parse_u32(const char *text, uint32_t *out)
{
    char *end = NULL;
    unsigned long value;
    errno = 0;
    value = strtoul(text, &end, 0);
    if (errno != 0 || end == text || *end != '\0' || value > UINT32_MAX)
        return 0;
    *out = (uint32_t)value;
    return 1;
}

static void print_hex(const uint8_t *bytes, size_t size)
{
    size_t i;
    for (i = 0; i < size; ++i) printf("%02x", bytes[i]);
}

int main(int argc, char **argv)
{
    uint8_t text[PORTABLE_TEXT_BITMAP_TEXT_CAPACITY];
    uint8_t glyphs[256u * 255u];
    uint8_t fold_window[256];
    uint8_t initial_pixels[PORTABLE_TEXT_BITMAP_CAPACITY];
    size_t text_size, glyphs_size, fold_window_size, initial_pixels_size;
    uint32_t values[6];
    size_t i;
    PortableTextBitmapInput input;
    PortableTextBitmapState state;
    PortableTextBitmapResult result;
    PortableTextBitmapStatus status;

    if (argc != 11) return 2;
    for (i = 0; i < 6; ++i)
        if (!parse_u32(argv[i + 1], &values[i]) || values[i] > 0xffffu)
            return 3;
    if (values[0] > 255u || values[1] > 255u || values[2] > 255u ||
        values[3] > 255u || !decode_hex(argv[7], text, sizeof(text), &text_size) ||
        !decode_hex(argv[8], glyphs, sizeof(glyphs), &glyphs_size) ||
        !decode_hex(argv[9], fold_window, sizeof(fold_window), &fold_window_size) ||
        fold_window_size != sizeof(fold_window) ||
        !decode_hex(argv[10], initial_pixels, sizeof(initial_pixels),
                    &initial_pixels_size) ||
        initial_pixels_size != sizeof(initial_pixels))
        return 4;

    memset(&state, 0xa5, sizeof(state));
    state.width = 0xcdefu;
    state.height = 0xabcdu;
    state.pen_x = 0x1234u;
    state.pen_y = 0x5678u;
    memcpy(state.pixels, initial_pixels, sizeof(state.pixels));

    input.hardware_profile = (uint8_t)values[0];
    input.character_width = (uint8_t)values[1];
    input.cell_height = (uint8_t)values[2];
    input.glyph_height = (uint16_t)values[3];
    input.glyph_rows = glyphs;
    input.glyph_rows_size = glyphs_size;
    input.fold_lookup_window = fold_window;
    input.fold_lookup_window_size = fold_window_size;
    input.text = text;
    input.text_size = text_size;
    input.x = (int16_t)values[4];
    input.y = (int16_t)values[5];

    status = portable_text_bitmap_prepare(&input, &state, &result);
    printf("{\"status\":%d,\"draw_kind\":%d,\"width\":%u,\"height\":%u,"
           "\"copied_characters\":%zu,\"drawn_width\":%u,"
           "\"drawn_height\":%u,\"stride\":%u,\"pen_x\":%u,"
           "\"pen_y\":%u,\"text_copy_hex\":\"",
           (int)status, (int)result.draw_kind, state.width, state.height,
           result.copied_characters, result.drawn_width, result.drawn_height,
           result.stride_bytes, state.pen_x, state.pen_y);
    print_hex(state.copied_text, 79);
    printf("%02x\",\"text_terminator\":%u,\"pixels_hex\":\"",
           state.copied_text_terminator, state.copied_text_terminator);
    print_hex(state.pixels, sizeof(state.pixels));
    printf("\",\"direct_text_hex\":\"");
    if (result.direct_text != NULL)
        print_hex(result.direct_text, result.direct_text_size);
    printf("\"}\n");
    return 0;
}
