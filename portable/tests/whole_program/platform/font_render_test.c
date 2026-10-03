#include "portable/whole_program/platform/dos_io.h"
#include "portable/whole_program/platform/font_blit.h"
#include "portable/whole_program/algorithms/asm_utilities.h"
#include "portable/whole_program/platform/handles.h"
#include "portable/whole_program/types/fonts.h"
#include "portable/render/font.h"
#include "portable/render/primitives.h"
#include <assert.h>
#define CHECK(condition) do { if (!(condition)) { fprintf(stderr, "CHECK failed: %s (%s:%d)\n", #condition, __FILE__, __LINE__); exit(1); } } while (0)
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

struct Font *font_ReadFont(char *name);
struct Font *font_DumpFont(struct Font *font);

static uint32_t rng = 0x2650000Fu;
static uint32_t next_rand(void) { rng = rng * 1664525u + 1013904223u; return rng; }
static void set_bit(uint8_t *row, size_t bit) { row[bit >> 3] |= (uint8_t)(0x80u >> (bit & 7u)); }
static int get_bit(const uint8_t *row, size_t bit) { return (row[bit >> 3] & (uint8_t)(0x80u >> (bit & 7u))) != 0; }

static void helper_matrix(void)
{
    unsigned test;
    for (test = 0; test < 256; ++test) {
        uint8_t source[8 * 6], actual[10 * 6], expected[10 * 6];
        unsigned sx = test & 7u, dx = (test >> 3) & 7u;
        unsigned width = 1u + (next_rand() % 50u), height = 1u + (next_rand() % 6u);
        unsigned row, x;
        for (x = 0; x < sizeof(source); ++x) source[x] = (uint8_t)next_rand();
        for (x = 0; x < sizeof(actual); ++x) actual[x] = (uint8_t)next_rand();
        memcpy(expected, actual, sizeof(actual));
        for (row = 0; row < height; ++row)
            for (x = 0; x < width; ++x)
                if (get_bit(source + row * 8u, sx + x)) set_bit(expected + row * 10u, dx + x);
        fd_55B3_6770 = 8; fd_55B3_6772 = 10; sim_font_blit_reset_status();
        f_2650_000F((char *)source, (char *)actual, (int16_t)width,
                    (int16_t)height, (int16_t)sx, (int16_t)dx);
        CHECK(sim_font_blit_last_status() == 0);
        CHECK(memcmp(actual, expected, sizeof(actual)) == 0);
    }
    {
        char bytes[24]; unsigned i;
        memset(bytes, 0xA5, sizeof(bytes)); sim_font_blit_reset_status();
        f_2650_0107(bytes + 3, 13);
        for (i = 0; i < sizeof(bytes); ++i) {
            if (bytes[i] != ((i >= 3 && i < 16) ? 0 : (char)0xA5)) {
                fprintf(stderr, "clear mismatch %u=%02x\n", i, (unsigned char)bytes[i]);
                exit(1);
            }
        }
    }
    memset(g_5ABE, 0xA5, sizeof(g_5ABE));
    fd_55B3_6770 = 100; fd_55B3_6772 = 2000; sim_font_blit_reset_status();
    f_2650_000F(g_5ABE, g_5ABE, 80, 8, 0, 0);
    CHECK(sim_font_blit_last_status() == 1);
    for (unsigned i = 0; i < sizeof(g_5ABE); ++i) CHECK((uint8_t)g_5ABE[i] == 0xA5);
}

static uint8_t *read_asset(unsigned index, size_t *length)
{
    char path[16]; FILE *file; long size; uint8_t *bytes;
    snprintf(path, sizeof(path), "FONT%u", index + 1u);
    file = fopen(path, "rb"); CHECK(file && fseek(file, 0, SEEK_END) == 0);
    size = ftell(file); CHECK(size > 0); rewind(file);
    bytes = (uint8_t *)malloc((size_t)size); CHECK(bytes);
    CHECK(fread(bytes, 1, (size_t)size, file) == (size_t)size); fclose(file);
    *length = (size_t)size; return bytes;
}

static size_t source_clipped_text(const PortableFont *font, const uint8_t *text,
                                  int16_t *out_width)
{
    int32_t pen = 0, edge = 640 - font->metrics[6];
    size_t i = 0;
    while (text[i] && pen < edge) {
        uint8_t ch = text[i]; size_t index = ch;
        int32_t advance; uint16_t ow;
        if (index >= font->table_count || font->ow_table[index] == -1) index = font->missing_char;
        ow = (uint16_t)font->ow_table[index];
        advance = font->proportional ? (uint8_t)ow : font->metrics[3];
        if (font->metrics[4] < 0) ++advance;
        pen += advance; ++i;
    }
    *out_width = (int16_t)pen;
    return i;
}

static void compare_render(unsigned font_index, const char *text)
{
    char name[16]; size_t raw_size, text_len = strlen(text), stride, rows, bytes;
    uint8_t *raw, *text_copy; PortableFont parsed; struct Font *loaded; struct Bitmap *bitmap;
    PortableFramebuffer fb; uint8_t *pixels, *expected; int32_t end_x; size_t i, clipped_len; int16_t clipped_width;
    snprintf(name, sizeof(name), "FONT%u", font_index + 1u);
    raw = read_asset(font_index, &raw_size); portable_font_init(&parsed);
    CHECK(portable_font_load(&parsed, raw, raw_size) == PORTABLE_RENDER_OK);
    loaded = font_ReadFont(name); CHECK(loaded);
    CHECK(memcmp(loaded, parsed.metrics, sizeof(parsed.metrics)) == 0);
    text_copy = (uint8_t *)malloc(text_len + 1u); CHECK(text_copy);
    memcpy(text_copy, text, text_len + 1u);
    stride = ((size_t)portable_font_string_width(&parsed, text_copy, text_len) + 7u) / 8u;
    if (!stride) stride = 1;
    rows = (size_t)parsed.metrics[7] - 1u;
    bytes = stride * rows;
    CHECK(bytes <= SIM_FONT_BITMAP_CAPACITY);
    pixels = (uint8_t *)calloc(stride * 8u * rows, 1); expected = (uint8_t *)calloc(bytes, 1);
    CHECK(pixels && expected);
    CHECK(portable_framebuffer_init(&fb, (int32_t)(stride * 8u), (int32_t)rows,
                                     stride * 8u, pixels) == PORTABLE_RENDER_OK);
    fb.clip.right = 640;
    clipped_len = source_clipped_text(&parsed, text_copy, &clipped_width);
    CHECK(portable_font_draw(&fb, &parsed, 0, 0, text_copy, clipped_len, 1, &end_x) == PORTABLE_RENDER_OK);
    for (size_t y = 0; y < rows; ++y)
        for (size_t x = 0; x < stride * 8u; ++x)
            if (pixels[y * stride * 8u + x]) set_bit(expected + y * stride, x);
    memset(g_5ABE, 0, sizeof(g_5ABE)); sim_font_blit_reset_status();
    CHECK(sim_font_bitmap_bind() == &fd_50F6_392C && fd_50F6_392C.bits == g_5ABE);
    bitmap = font_MakeImage(text_copy, 0, loaded);
    CHECK(bitmap == &fd_50F6_392C && sim_font_blit_last_status() == 0);
    CHECK(bitmap->width == clipped_width);
    CHECK(bitmap->height == (int16_t)rows);
    CHECK(fd_55B3_6770 == parsed.metrics[12] * 2);
    CHECK(fd_55B3_6772 == (int16_t)stride);
    if (memcmp(g_5ABE, expected, bytes) != 0) {
        for (i = 0; i < bytes; ++i) if ((uint8_t)g_5ABE[i] != expected[i]) {
            fprintf(stderr, "raster mismatch font%u textlen%zu stride%zu row%zu byte%zu actual%02x expected%02x width%d\n",
                    font_index + 1u, text_len, stride, i / stride, i % stride,
                    (uint8_t)g_5ABE[i], expected[i], bitmap->width);
            break;
        }
        exit(1);
    }
    CHECK(font_DumpFont(loaded) == NULL);
    for (i = 0; i < bytes; ++i) CHECK((uint8_t)g_5ABE[i] == expected[i]);
    free(expected); free(pixels); free(text_copy); free(raw); portable_font_destroy(&parsed);
}

int main(void)
{
    static const char short_text[] = "SimAnt 123";
    char long_text[121]; unsigned i;
    CHECK(dos_files_set_root("assets") == 0); helper_matrix();
    memset(long_text, 'M', sizeof(long_text) - 1u); long_text[sizeof(long_text) - 1u] = 0;
    for (i = 0; i < 4; ++i) {
        compare_render(i, short_text);
        compare_render(i, long_text);
    }
    {
        struct Font *valid = font_ReadFont("FONT1");
        struct Font malformed;
        CHECK(valid != NULL);
        malformed = *valid;
        memset(g_5ABE, 0xA5, sizeof(g_5ABE));
        sim_font_blit_reset_status();
        malformed.rowWords = INT16_MAX;
        CHECK(sim_font_make_image((uint8_t *)short_text, 0, &malformed) == NULL);
        CHECK(sim_font_blit_last_status() == 1);
        for (i = 0; i < sizeof(g_5ABE); ++i) CHECK((uint8_t)g_5ABE[i] == 0xA5);
        CHECK(font_DumpFont(valid) == NULL);
    }
    dos_files_close_all();
    puts("generated font_MakeImage and source-shaped glyph blit passed on FONT1-FONT4 short/long text");
    return 0;
}

