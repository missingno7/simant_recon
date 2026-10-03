#include "portable/game/resources/source_graphics_resources.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define CHECK(expr) do { \
    if (!(expr)) { \
        fprintf(stderr, "CHECK failed at %s:%d: %s\n", __FILE__, __LINE__, #expr); \
        return 1; \
    } \
} while (0)

static int read_fixture(const char *path, uint8_t expected[272])
{
    FILE *file = fopen(path, "rb");
    size_t count;
    if (file == NULL) return 0;
    count = fread(expected, 1, 272, file);
    if (fgetc(file) != EOF) count = 0;
    fclose(file);
    return count == 272;
}

static int test_empty_pattern_source(void)
{
    SimGraphicsDriver graphics = {0};
    CHECK(sim_graphics_init(&graphics) == SIM_GRAPHICS_OK);
    CHECK(sim_graphics_g9138_pattern_rect(&graphics, 0, 0, 8, 8, 0) ==
          SIM_GRAPHICS_PATTERN_SOURCE_UNBOUND);
    CHECK(sim_graphics_set_pattern_source(&graphics,
          portable_source_graphics_pattern_bytes(NULL), 255) == SIM_GRAPHICS_INVALID_ARGUMENT);
    CHECK(sim_graphics_g9138_pattern_rect(&graphics, 0, 0, 8, 8, 0) ==
          SIM_GRAPHICS_PATTERN_SOURCE_UNBOUND);
    sim_graphics_destroy(&graphics);
    return 0;
}

static int test_missing_font_directory(void)
{
    SimGraphicsDriver graphics = {0};
    PortableSourceGraphicsResources resources = {0};
    uint8_t old_pattern[256] = {0};
    CHECK(sim_graphics_init(&graphics) == SIM_GRAPHICS_OK);
    graphics.pattern_source = old_pattern;
    graphics.pattern_source_size = sizeof(old_pattern);
    portable_source_graphics_resources_init(&resources);
    CHECK(portable_source_graphics_resources_bind(&resources, &graphics,
          "build/no-such-bios-font-directory") ==
          PORTABLE_SOURCE_GRAPHICS_RESOURCES_FONT_LOAD_FAILED);
    CHECK(graphics.pattern_source == old_pattern);
    CHECK(graphics.pattern_source_size == sizeof(old_pattern));
    CHECK(graphics.bios_8x8_source == NULL && graphics.bios_8x14_source == NULL);
    CHECK(portable_source_graphics_bios_font_provider(&resources) == NULL);
    portable_source_graphics_resources_destroy(&resources);
    sim_graphics_destroy(&graphics);
    return 0;
}

static int test_real_bind_and_calls(const char *font_directory,
                                    const char *pattern_fixture)
{
    SimGraphicsDriver graphics = {0};
    PortableSourceGraphicsResources resources = {0};
    uint8_t old_pattern[256];
    uint8_t old_font8[2048];
    uint8_t old_font14[3584];
    uint8_t old_glyphs[64];
    uint8_t expected[272];
    const PortableBiosFontProvider *provider;
    const uint8_t *patterns;
    const uint8_t *pixels;
    size_t pattern_size, pixels_size;
    unsigned pattern, y, x;
    const int x8 = 20, y8 = 24, x14 = 40, y14 = 24;

    memset(old_pattern, 0xa5, sizeof(old_pattern));
    memset(old_font8, 0x38, sizeof(old_font8));
    memset(old_font14, 0x5a, sizeof(old_font14));
    memset(old_glyphs, 0x7c, sizeof(old_glyphs));
    CHECK(read_fixture(pattern_fixture, expected));
    CHECK(sim_graphics_init(&graphics) == SIM_GRAPHICS_OK);
    graphics.pattern_source = old_pattern;
    graphics.pattern_source_size = sizeof(old_pattern);
    graphics.bios_8x8_source = old_font8;
    graphics.bios_8x8_source_size = sizeof(old_font8);
    graphics.bios_8x14_source = old_font14;
    graphics.bios_8x14_source_size = sizeof(old_font14);
    graphics.glyph_source = old_glyphs;
    graphics.glyph_source_size = sizeof(old_glyphs);
    graphics.glyph_bytes_per_character = 7;
    graphics.glyph_width = 5;
    graphics.glyph_height = 6;
    graphics.font_is_bound = 1;
    graphics.g_3DDA = 7;
    graphics.g_3DDC = 6;
    graphics.g_3DDE = 5;
    for (x = 0; x < 16; ++x) graphics.color_map[x] = (uint8_t)(15u - x);
    portable_source_graphics_resources_init(&resources);
    CHECK(portable_source_graphics_resources_bind(&resources, &graphics,
          font_directory) == PORTABLE_SOURCE_GRAPHICS_RESOURCES_OK);
    CHECK(portable_source_graphics_resources_bind(&resources, &graphics,
          font_directory) == PORTABLE_SOURCE_GRAPHICS_RESOURCES_ALREADY_BOUND);

    patterns = portable_source_graphics_pattern_bytes(&pattern_size);
    CHECK(pattern_size == 256 && graphics.pattern_source == patterns);
    CHECK(graphics.pattern_source_size == 256);
    CHECK(memcmp(graphics.color_map, expected, 16) == 0);
    CHECK(memcmp(graphics.pattern_source, expected + 16, 256) == 0);
    provider = portable_source_graphics_bios_font_provider(&resources);
    CHECK(provider != NULL);
    CHECK(graphics.bios_8x8_source == resources.bios_fonts.font_8x8);
    CHECK(graphics.bios_8x14_source == resources.bios_fonts.font_8x14);
    CHECK(graphics.bios_8x8_source_size == 2048);
    CHECK(graphics.bios_8x14_source_size == 3584);
    CHECK(provider->font_8x8.glyph_rows == graphics.bios_8x8_source);
    CHECK(provider->font_8x14.glyph_rows == graphics.bios_8x14_source);
    CHECK(provider->font_8x8.glyph_height == 8);
    CHECK(provider->font_8x14.glyph_height == 14);
    CHECK(strstr(provider->font_8x8.provider_id, "DOSBox Staging/v0.83.0/") ==
          provider->font_8x8.provider_id);

    graphics.g_3DE0 = 11;
    graphics.g_3DE2 = 3;
    for (pattern = 0; pattern < 16; ++pattern) {
        CHECK(sim_graphics_g9138_pattern_rect(&graphics, 0, 0, 16, 8,
              (int16_t)pattern) == SIM_GRAPHICS_OK);
        pixels = sim_graphics_pixels(&graphics, &pixels_size);
        CHECK(pixels != NULL && pixels_size == 640u * 350u);
        for (y = 0; y < 8; ++y) {
            for (x = 0; x < 16; ++x) {
                uint8_t row_bits = patterns[pattern * 16u + y * 2u + x / 8u];
                uint8_t bit = (uint8_t)((row_bits >> (7u - (x & 7u))) & 1u);
                CHECK(pixels[y * 640u + x] == (bit ? 11u : 3u));
            }
        }
    }

    CHECK(sim_graphics_g9130_select_bios_8x8(&graphics) == SIM_GRAPHICS_OK);
    CHECK(graphics.g_3DDA == 8 && graphics.g_3DDC == 8);
    CHECK(sim_graphics_f_1B4E_0110(&graphics, x8, y8, 'A') == SIM_GRAPHICS_OK);
    pixels = sim_graphics_pixels(&graphics, &pixels_size);
    for (y = 0; y < 8; ++y) {
        uint8_t bits = provider->font_8x8.glyph_rows[(size_t)'A' * 8u + y];
        for (x = 0; x < 8; ++x)
            CHECK(pixels[(size_t)(y8 + (int)y) * 640u + (size_t)(x8 + (int)x)] ==
                  ((bits & (uint8_t)(0x80u >> x)) ? 11u : 3u));
    }
    CHECK(sim_graphics_g9130_select_bios_8x14(&graphics) == SIM_GRAPHICS_OK);
    CHECK(graphics.g_3DDA == 14 && graphics.g_3DDC == 14);
    CHECK(sim_graphics_f_1B4E_0110(&graphics, x14, y14, 'B') == SIM_GRAPHICS_OK);
    for (y = 0; y < 14; ++y) {
        uint8_t bits = provider->font_8x14.glyph_rows[(size_t)'B' * 14u + y];
        for (x = 0; x < 8; ++x)
            CHECK(pixels[(size_t)(y14 + (int)y) * 640u + (size_t)(x14 + (int)x)] ==
                  ((bits & (uint8_t)(0x80u >> x)) ? 11u : 3u));
    }
    CHECK(sim_graphics_f_1B4E_000D(&graphics, (int16_t)0x12a5) == (int16_t)0x12a5);

    CHECK(portable_source_graphics_resources_unbind(&resources) ==
          PORTABLE_SOURCE_GRAPHICS_RESOURCES_OK);
    CHECK(graphics.pattern_source == old_pattern &&
          graphics.pattern_source_size == sizeof(old_pattern));
    CHECK(graphics.bios_8x8_source == old_font8 &&
          graphics.bios_8x8_source_size == sizeof(old_font8));
    CHECK(graphics.bios_8x14_source == old_font14 &&
          graphics.bios_8x14_source_size == sizeof(old_font14));
    CHECK(graphics.glyph_source == old_glyphs && graphics.glyph_source_size == sizeof(old_glyphs));
    CHECK(graphics.glyph_bytes_per_character == 7 && graphics.glyph_width == 5 &&
          graphics.glyph_height == 6 && graphics.font_is_bound == 1);
    CHECK(graphics.g_3DDA == 7 && graphics.g_3DDC == 6 && graphics.g_3DDE == 5);
    for (x = 0; x < 16; ++x) CHECK(graphics.color_map[x] == (uint8_t)(15u - x));
    CHECK(portable_source_graphics_bios_font_provider(&resources) == NULL);
    portable_source_graphics_resources_destroy(&resources);
    sim_graphics_destroy(&graphics);
    return 0;
}

int main(int argc, char **argv)
{
    if (argc != 3) return 2;
    if (test_empty_pattern_source() != 0) return 3;
    if (test_missing_font_directory() != 0) return 4;
    if (test_real_bind_and_calls(argv[1], argv[2]) != 0) return 5;
    puts("PASS: source m1B4E patterns, verified BIOS tables, actual graphics calls, cleanup");
    return 0;
}
