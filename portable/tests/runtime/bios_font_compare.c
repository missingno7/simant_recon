#include "text_bitmap.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

enum {
    DOS_ROM_BYTES = 32768,
    DOS_FONT14_OFFSET = 0x09e9,
    FONT14_BYTES = 256 * 14,
    FIXED_OUTPUT_BYTES = 5 * 14
};

static int read_exact(const char *path, uint8_t *bytes, size_t size)
{
    FILE *file = fopen(path, "rb");
    int ok;
    if (file == NULL)
        return 0;
    ok = fread(bytes, 1, size, file) == size && fgetc(file) == EOF;
    if (fclose(file) != 0)
        ok = 0;
    return ok;
}

static size_t differing_bytes(const uint8_t *left, const uint8_t *right,
                              size_t size, size_t *first)
{
    size_t i;
    size_t count = 0;
    *first = size;
    for (i = 0; i < size; ++i) {
        if (left[i] != right[i]) {
            if (count == 0)
                *first = i;
            ++count;
        }
    }
    return count;
}

/* Test-owned stand-ins for the canonical text owners (g_5ABA/g_5ABC
 * dimensions, the 1040-byte g_5ABE pixel view, g_5ECE string, g_5F1D). */
typedef struct TestTextOwners {
    uint16_t width, height;
    uint8_t pixels[1040];
    uint8_t text[79];
    uint8_t terminator;
} TestTextOwners;

static int render(const uint8_t *font, TestTextOwners *state)
{
    PortableTextBitmapOwnerView owners = {
        &state->width, &state->height, state->pixels, sizeof(state->pixels),
        state->text, sizeof(state->text), &state->terminator};
    static const uint8_t text[] = " File";
    PortableTextBitmapInput input = {0};
    PortableTextBitmapResult result;
    input.hardware_profile = 8;
    input.character_width = 8;
    input.cell_height = 14;
    input.glyph_height = 14;
    input.glyph_rows = font;
    input.glyph_rows_size = FONT14_BYTES;
    input.text = text;
    input.text_size = sizeof(text);
    if (portable_text_bitmap_prepare(&input, &owners, &result) !=
        PORTABLE_TEXT_BITMAP_OK)
        return 0;
    return result.draw_kind == PORTABLE_TEXT_BITMAP_DRAW_BITMAP &&
           result.copied_characters == 5 && result.drawn_width == 40 &&
           result.drawn_height == 14 && result.stride_bytes == 5;
}

int main(int argc, char **argv)
{
    static const uint8_t text[] = " File";
    uint8_t dos_rom[DOS_ROM_BYTES];
    uint8_t dos_font[FONT14_BYTES];
    uint8_t current_font[FONT14_BYTES];
    uint8_t old_font[FONT14_BYTES];
    uint8_t expected_fixture[FIXED_OUTPUT_BYTES];
    uint8_t dos_expected[FIXED_OUTPUT_BYTES];
    static TestTextOwners current_state, old_state;
    size_t i, row, first_current, first_old;
    size_t current_diff, old_diff;
    if (argc != 5) {
        fprintf(stderr, "usage: bios-font-compare DOS_ROM CURRENT_FONT OLD_FONT EXPECTED\n");
        return 2;
    }
    if (!read_exact(argv[1], dos_rom, sizeof(dos_rom)) ||
        !read_exact(argv[2], current_font, sizeof(current_font)) ||
        !read_exact(argv[3], old_font, sizeof(old_font)) ||
        !read_exact(argv[4], expected_fixture, sizeof(expected_fixture))) {
        fputs("font regression fixture has an unexpected length or cannot be read\n",
              stderr);
        return 2;
    }
    memcpy(dos_font, dos_rom + DOS_FONT14_OFFSET, sizeof(dos_font));
    if (memcmp(current_font, dos_font, sizeof(dos_font)) != 0) {
        fputs("current provider table differs from captured DOSBox-X ROM bank\n",
              stderr);
        return 1;
    }
    for (row = 0, i = 0; row < 14; ++row) {
        size_t column;
        for (column = 0; column < 5; ++column)
            dos_expected[i++] = dos_font[(size_t)text[column] * 14u + row];
    }
    if (memcmp(dos_expected, expected_fixture, sizeof(dos_expected)) != 0) {
        fputs("fixed DOS capture rendering fixture is stale\n", stderr);
        return 1;
    }
    if (!render(current_font, &current_state) ||
        !render(old_font, &old_state)) {
        fputs("font_MakeImage projection rejected fixed VGA input\n", stderr);
        return 1;
    }
    current_diff = differing_bytes(current_state.pixels, expected_fixture,
                                   sizeof(expected_fixture), &first_current);
    old_diff = differing_bytes(old_state.pixels, expected_fixture,
                               sizeof(expected_fixture), &first_old);
    if (current_diff != 0) {
        fprintf(stderr, "native output differs from DOS capture at byte %zu (%zu bytes)\n",
                first_current, current_diff);
        return 1;
    }
    if (old_diff == 0) {
        fputs("negative control unexpectedly matches DOSBox-X capture\n", stderr);
        return 1;
    }
    printf("PASS text=\" File\" output_bytes=%u DOSBox-X_match=yes ",
           (unsigned)sizeof(expected_fixture));
    printf("old_Staging_negative_control=detected first_diff=%zu differing_bytes=%zu\n",
           first_old, old_diff);
    return 0;
}
