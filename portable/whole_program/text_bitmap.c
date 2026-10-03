#include "text_bitmap.h"

#include <string.h>

static uint16_t wrap_add_i16(uint16_t left, uint16_t right)
{
    return (uint16_t)(left + right);
}

static size_t text_length_at_most_80(const uint8_t *text, size_t size,
                                     int *terminated)
{
    size_t limit = size < PORTABLE_TEXT_BITMAP_TEXT_CAPACITY
        ? size : PORTABLE_TEXT_BITMAP_TEXT_CAPACITY;
    size_t i;

    for (i = 0; i < limit; ++i) {
        if (text[i] == 0) {
            *terminated = 1;
            return i;
        }
    }
    *terminated = 0;
    return limit;
}

static uint8_t fold_character(const PortableTextBitmapInput *input,
                              uint8_t character)
{
    if (character < 0x80u) return character;
    return input->fold_lookup_window[character];
}

PortableTextBitmapStatus portable_text_bitmap_prepare(
    const PortableTextBitmapInput *input,
    PortableTextBitmapState *state,
    PortableTextBitmapResult *result)
{
    size_t source_length;
    size_t copy_length;
    size_t i;
    size_t stride;
    size_t required;
    uint16_t width;
    uint8_t character_width;
    int terminated;

    if (input == NULL || state == NULL || result == NULL ||
        input->text == NULL || input->text_size == 0)
        return PORTABLE_TEXT_BITMAP_INVALID_ARGUMENT;

    memset(result, 0, sizeof(*result));
    if (input->hardware_profile == 6u) {
        result->draw_kind = PORTABLE_TEXT_BITMAP_DRAW_DIRECT_TEXT;
        result->direct_text = input->text;
        result->direct_text_size = input->text_size;
        return PORTABLE_TEXT_BITMAP_OK;
    }

    /* Source assigns g5ABC before checking for an empty string. */
    state->height = input->cell_height;
    source_length = text_length_at_most_80(input->text, input->text_size,
                                           &terminated);
    if (!terminated && source_length < PORTABLE_TEXT_BITMAP_TEXT_CAPACITY)
        return PORTABLE_TEXT_BITMAP_UNTERMINATED_TEXT;
    copy_length = source_length < 79u ? source_length : 79u;
    if (source_length == 0) {
        state->copied_text[0] = 0;
        result->draw_kind = PORTABLE_TEXT_BITMAP_NO_DRAW;
        result->copied_characters = 0;
        return PORTABLE_TEXT_BITMAP_OK;
    }

    character_width = input->character_width;
    if (character_width == 0u ||
        (character_width != 8u && character_width != 4u))
        return PORTABLE_TEXT_BITMAP_UNSUPPORTED_FONT;
    if (input->glyph_height == 0u || input->glyph_height > 255u ||
        input->glyph_rows == NULL ||
        input->glyph_rows_size < (size_t)256u * input->glyph_height)
        return PORTABLE_TEXT_BITMAP_INVALID_ARGUMENT;

    if (character_width != 8u) {
        for (i = 0; i < copy_length; ++i) {
            if (input->text[i] >= 0x80u &&
                (input->fold_lookup_window == NULL ||
                 input->fold_lookup_window_size <= input->text[i]))
                return PORTABLE_TEXT_BITMAP_UNSUPPORTED_CHARACTER;
        }
    }

    width = (uint16_t)((uint16_t)character_width * (uint16_t)copy_length);
    stride = ((size_t)width + 7u) >> 3;
    required = stride * input->glyph_height;
    if (required > PORTABLE_TEXT_BITMAP_CAPACITY)
        return PORTABLE_TEXT_BITMAP_BUFFER_TOO_SMALL;

    state->width = width;
    memcpy(state->copied_text, input->text, copy_length);
    if (copy_length < 79u) state->copied_text[copy_length] = 0;
    /* The DOS copy terminator at byte 79 is also the separate g5F1D byte. */
    state->copied_text_terminator = 0;
    result->draw_kind = PORTABLE_TEXT_BITMAP_DRAW_BITMAP;
    result->copied_characters = copy_length;
    result->drawn_width = width;
    result->drawn_height = input->cell_height;
    result->stride_bytes = (uint16_t)stride;

    if (character_width == 8u) {
        for (i = 0; i < copy_length; ++i) {
            uint8_t character = input->text[i];
            size_t glyph_offset = (size_t)character * input->glyph_height;
            size_t row;
            for (row = 0; row < input->glyph_height; ++row)
                state->pixels[row * stride + i] =
                    input->glyph_rows[glyph_offset + row];
        }
    } else {
        size_t pair;
        size_t pair_count = (copy_length + 1u) >> 1;
        for (pair = 0; pair < pair_count; ++pair) {
            size_t first = pair * 2u;
            uint8_t left = fold_character(input, input->text[first]);
            size_t left_offset = (size_t)left * input->glyph_height;
            size_t row;
            for (row = 0; row < input->glyph_height; ++row) {
                size_t pixel = row * stride + pair;
                state->pixels[pixel] =
                    (uint8_t)(input->glyph_rows[left_offset + row] & 0xf0u);
            }
            if (first + 1u < copy_length) {
                uint8_t right = fold_character(input, input->text[first + 1u]);
                size_t right_offset = (size_t)right * input->glyph_height;
                for (row = 0; row < input->glyph_height; ++row) {
                    size_t pixel = row * stride + pair;
                    state->pixels[pixel] |= (uint8_t)(
                        input->glyph_rows[right_offset + row] >> 4);
                }
            }
        }
    }

    state->pen_x = wrap_add_i16((uint16_t)input->x, width);
    state->pen_y = (uint16_t)input->y;
    return PORTABLE_TEXT_BITMAP_OK;
}
