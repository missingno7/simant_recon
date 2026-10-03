#include "portable/whole_program/platform/graphics.h"

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define CHECK(condition) do { \
    if (!(condition)) { \
        fprintf(stderr, "CHECK failed at %s:%d: %s\n", __FILE__, __LINE__, #condition); \
        exit(1); \
    } \
} while (0)

static int mode_change_count;
static int32_t last_mode_width;
static int32_t last_mode_height;
static SimGraphicsStatus mode_callback_result = SIM_GRAPHICS_OK;

void graphics_source_fields_test(void);

static SimGraphicsStatus mode_changed(void *context, int32_t width, int32_t height)
{
    int *calls = (int *)context;
    ++*calls;
    if (mode_callback_result != SIM_GRAPHICS_OK)
        return mode_callback_result;
    last_mode_width = width;
    last_mode_height = height;
    return SIM_GRAPHICS_OK;
}

static void test_defaults_and_source_tables(void)
{
    SimGraphicsDriver gfx;
    size_t count = 0;
    const SimGraphicsSlotInfo *slots;
    const char *const *s01;
    CHECK(sim_graphics_init(&gfx) == SIM_GRAPHICS_OK);
    CHECK(gfx.g_3DB2 == 640 && gfx.g_3DB4 == 350 && gfx.g_3DB6 == 80);
    CHECK(gfx.framebuffer.width == 640 && gfx.framebuffer.height == 350);
    CHECK(gfx.framebuffer.stride == 640 && gfx.pixel_storage_size == 640u * 350u);
    slots = sim_graphics_driver_slots(&count);
    CHECK(slots != NULL && count == 25);
    CHECK(slots[SIM_GFX_ENTRY_G9128].provided == 1);
    CHECK(slots[SIM_GFX_ENTRY_G912C].provided == 1);
    CHECK(slots[SIM_GFX_ENTRY_G9130].provided == 1);
    CHECK(slots[SIM_GFX_ENTRY_G9134].provided == 1);
    CHECK(slots[SIM_GFX_ENTRY_G9138].provided == 1);
    CHECK(slots[SIM_GFX_ENTRY_G913C].provided == 1);
    CHECK(slots[SIM_GFX_ENTRY_G9154].provided == 1);
    CHECK(slots[SIM_GFX_ENTRY_G9158].provided == 1);
    CHECK(slots[SIM_GFX_ENTRY_G9170].provided == 1);
    CHECK(strcmp(slots[SIM_GFX_ENTRY_G9154].source_target, "o00_31AD_1206") == 0);
    CHECK(strcmp(slots[SIM_GFX_ENTRY_G9158].source_target, "o00_31AD_1213") == 0);
    CHECK(strcmp(slots[SIM_GFX_ENTRY_G9188].source_target, "o00_31AD_1950") == 0);
    CHECK(slots[SIM_GFX_ENTRY_G914C].provided == 0);
    CHECK(slots[SIM_GFX_ENTRY_G9188].source_target != NULL);
    CHECK(slots[SIM_GFX_ENTRY_G9188].provided == 0);
    CHECK(!sim_graphics_driver_entry_is_provided(SIM_GFX_ENTRY_G914C));
    s01 = sim_graphics_s01_source_targets(&count);
    CHECK(s01 != NULL && count == 25);
    CHECK(s01[0] != NULL && s01[24] != NULL);
    sim_graphics_destroy(&gfx);
}

static void test_color_attribute_and_fill_clip(void)
{
    SimGraphicsDriver gfx;
    PortableRect clip = {2, 1, 5, 4};
    uint8_t *pixels;
    size_t size;
    CHECK(sim_graphics_init(&gfx) == SIM_GRAPHICS_OK);
    gfx.color_map[3] = 11;
    CHECK((uint16_t)sim_graphics_f_1B4E_000D(&gfx, (int16_t)0x1233) == 0x123b);
    CHECK(sim_graphics_g9128(&gfx, 0x0105, 0x0202, 0x7777) == SIM_GRAPHICS_OK);
    CHECK(gfx.g_3DE0 == 5 && gfx.g_3DE2 == 2);
    CHECK(sim_graphics_clip_push(&gfx) == SIM_GRAPHICS_OK);
    CHECK(sim_graphics_clip_set(&gfx, clip) == SIM_GRAPHICS_OK);
    CHECK(sim_graphics_g9134(&gfx, 0, 0, 6, 5, 3) == SIM_GRAPHICS_OK);
    pixels = sim_graphics_pixels(&gfx, &size);
    CHECK(pixels != NULL && size == 640u * 350u);
    CHECK(pixels[1u * 640u + 2u] == 3);
    CHECK(pixels[3u * 640u + 4u] == 3);
    CHECK(pixels[0] == 0 && pixels[1u * 640u + 1u] == 0);
    CHECK(sim_graphics_clip_pop(&gfx) == SIM_GRAPHICS_OK);
    CHECK(sim_graphics_clip_pop(&gfx) == SIM_GRAPHICS_CLIP_STACK_UNDERFLOW);
    sim_graphics_destroy(&gfx);
}

static void test_glyph_and_text_pen(void)
{
    SimGraphicsDriver gfx;
    uint8_t glyphs[256] = {0};
    uint8_t *pixels;
    size_t size;
    /* Each 8x2 glyph occupies two bytes: A is 10100000/01010000. */
    glyphs[(size_t)'A' * 2u] = 0xa0;
    glyphs[(size_t)'A' * 2u + 1u] = 0x50;
    glyphs[(size_t)'B' * 2u] = 0x40;
    glyphs[(size_t)'B' * 2u + 1u] = 0x80;
    CHECK(sim_graphics_init(&gfx) == SIM_GRAPHICS_OK);
    CHECK(sim_graphics_g9128(&gfx, 7, 2, 0) == SIM_GRAPHICS_OK);
    CHECK(sim_graphics_set_glyph_source(&gfx, glyphs, sizeof(glyphs), 2, 8, 2) == SIM_GRAPHICS_OK);
    CHECK(gfx.g_3DDA == 2);
    CHECK(sim_graphics_f_1B4E_0110(&gfx, 10, 4, 'A') == SIM_GRAPHICS_OK);
    pixels = sim_graphics_pixels(&gfx, &size);
    CHECK(size == 640u * 350u);
    CHECK(pixels[4u * 640u + 10u] == 7);
    CHECK(pixels[4u * 640u + 11u] == 2);
    CHECK(pixels[5u * 640u + 11u] == 7);
    CHECK(sim_graphics_f_1B4E_0081(&gfx, 20, 9, "AB") == SIM_GRAPHICS_OK);
    CHECK(gfx.g_3DA0 == 36 && gfx.g_3DA2 == 9);
    CHECK(pixels[9u * 640u + 20u] == 7);
    CHECK(pixels[9u * 640u + 29u] == 7);
    {
        const uint8_t direct_bitmap[2] = {0x80, 0x00};
        CHECK(sim_graphics_g9154(&gfx, 40, 9, direct_bitmap,
                                 sizeof(direct_bitmap), 8, 2) == SIM_GRAPHICS_OK);
        CHECK(pixels[9u * 640u + 40u] == 7);
        CHECK(pixels[9u * 640u + 41u] == 2);
    }
    CHECK(sim_graphics_set_glyph_source(&gfx, glyphs, 2, 2, 8, 2) == SIM_GRAPHICS_OK);
    CHECK(sim_graphics_f_1B4E_0110(&gfx, 0, 0, 'A') == SIM_GRAPHICS_FONT_SPAN_INVALID);
    sim_graphics_destroy(&gfx);
}

static void test_six_pixel_fold_fails_explicitly(void)
{
    SimGraphicsDriver gfx;
    uint8_t glyphs[256 * 6] = {0};
    CHECK(sim_graphics_init(&gfx) == SIM_GRAPHICS_OK);
    CHECK(sim_graphics_set_glyph_source(&gfx, glyphs, sizeof(glyphs), 6, 6, 8) == SIM_GRAPHICS_OK);
    CHECK(sim_graphics_f_1B4E_0110(&gfx, 0, 0, 0x80) == SIM_GRAPHICS_UNSUPPORTED_GLYPH_FOLD);
    sim_graphics_destroy(&gfx);
}

static void test_source_abi_and_vga_mode(void)
{
    SimGraphicsDriver gfx;
    uint16_t source_g_5AAE = 0;
    char bitmap[] = {(char)0x80};
    uint8_t *pixels;
    size_t size;
    mode_change_count = 0;
    mode_callback_result = SIM_GRAPHICS_OK;
    last_mode_width = last_mode_height = 0;
    CHECK(sim_graphics_init(&gfx) == SIM_GRAPHICS_OK);
    CHECK(gfx.video_mode == SIM_GRAPHICS_MODE_EGA_640X350);
    CHECK(gfx.g_3DB2 == 640 && gfx.g_3DB4 == 350 && gfx.g_3DB6 == 80);
    sim_graphics_set_mode_changed_callback(&gfx, mode_changed, &mode_change_count);
    CHECK(sim_graphics_bind_source_abi(&gfx, &source_g_5AAE) == SIM_GRAPHICS_OK);
    CHECK(g_9128 != NULL && g_912C != NULL && g_9130 != NULL &&
          g_9134 != NULL && g_9138 != NULL && g_913C != NULL &&
          g_9154 != NULL && g_9158 != NULL && g_9170 != NULL);
    graphics_source_fields_test();
    g_9128(9, 4, 0x55aa);
    CHECK(gfx.g_3DE0 == 9 && gfx.g_3DE2 == 4);
    gfx.color_map[1] = 2;
    gfx.color_map[2] = 7; /* Non-involution detects a second palette remap. */
    g_9134(1, 2, 3, 4, f_1B4E_000D(1));
    pixels = sim_graphics_pixels(&gfx, &size);
    CHECK(pixels[2u * 640u + 1u] == 2);
    g_9134(1, 2, 3, 4, 1);
    CHECK(pixels[2u * 640u + 1u] == 1);
    gfx.g_3DD2 = 0x18;
    g_9134(1, 2, 3, 4, 1);
    CHECK(sim_graphics_source_last_status() == SIM_GRAPHICS_OK);
    CHECK(pixels[2u * 640u + 1u] == 0);
    gfx.g_3DD2 = 0;
    g_9170(20, 20, 23, 20, f_1B4E_000D(1));
    CHECK(sim_graphics_source_last_status() == SIM_GRAPHICS_OK);
    CHECK(pixels[20u * 640u + 20u] == 2);
    CHECK(pixels[20u * 640u + 21u] == 2);
    CHECK(pixels[20u * 640u + 22u] == 2);
    CHECK(pixels[20u * 640u + 23u] == 2);
    g_9170(320, 240, 329, 244, f_1B4E_000D(3));
    CHECK(sim_graphics_source_last_status() == SIM_GRAPHICS_OK);
    CHECK(pixels[240u * 640u + 320u] == 3);
    CHECK(pixels[240u * 640u + 321u] == 3);
    CHECK(pixels[241u * 640u + 322u] == 3);
    CHECK(pixels[241u * 640u + 323u] == 3);
    CHECK(pixels[242u * 640u + 324u] == 3);
    CHECK(pixels[242u * 640u + 325u] == 3);
    CHECK(pixels[243u * 640u + 326u] == 3);
    CHECK(pixels[243u * 640u + 327u] == 3);
    CHECK(pixels[244u * 640u + 328u] == 3);
    CHECK(pixels[244u * 640u + 329u] == 3);
    g_9170(329, 244, 320, 240, f_1B4E_000D(5));
    CHECK(sim_graphics_source_last_status() == SIM_GRAPHICS_OK);
    CHECK(pixels[240u * 640u + 320u] == 5);
    CHECK(pixels[244u * 640u + 329u] == 5);
    CHECK(sim_graphics_clip_push(&gfx) == SIM_GRAPHICS_OK);
    CHECK(sim_graphics_clip_set(&gfx, (PortableRect){324, 242, 327, 244}) == SIM_GRAPHICS_OK);
    g_9170(320, 240, 329, 244, f_1B4E_000D(9));
    CHECK(sim_graphics_source_last_status() == SIM_GRAPHICS_OK);
    CHECK(pixels[242u * 640u + 324u] == 9);
    CHECK(pixels[242u * 640u + 325u] == 9);
    CHECK(pixels[243u * 640u + 326u] == 9);
    CHECK(pixels[240u * 640u + 320u] == 5);
    CHECK(pixels[244u * 640u + 329u] == 5);
    CHECK(sim_graphics_clip_pop(&gfx) == SIM_GRAPHICS_OK);
    g_9154(10, 2, bitmap, 8, 1);
    CHECK(sim_graphics_source_last_status() == SIM_GRAPHICS_OK);
    CHECK(pixels[2u * 640u + 10u] == 9);
    source_g_5AAE = 1;
    g_9134(1, 2, 3, 4, 5);
    CHECK(sim_graphics_source_last_status() == SIM_GRAPHICS_UNSUPPORTED_MODE);
    g_9154(10, 3, bitmap, 8, 1);
    CHECK(sim_graphics_source_last_status() == SIM_GRAPHICS_UNSUPPORTED_MODE);
    g_9158(10, 3, bitmap, 8, 1);
    CHECK(sim_graphics_source_last_status() == SIM_GRAPHICS_OK);
    gfx.g_3DD2 = 0x20;
    CHECK(sim_graphics_g9170_line(&gfx, 0, 0, 1, 0, 3) == SIM_GRAPHICS_UNSUPPORTED_MODE);
    gfx.g_3DD2 = 0;
    CHECK(sim_graphics_g9170_line(&gfx, 0, 0, 8, 3, 3) == SIM_GRAPHICS_OK);
    CHECK(sim_graphics_g9170_line(&gfx, 0, 0, 640, 0, 3) == SIM_GRAPHICS_UNSUPPORTED_MODE);
    f_1B4E_015B(SIM_GRAPHICS_MODE_VGA_640X480);
    CHECK(sim_graphics_source_last_status() == SIM_GRAPHICS_OK);
    CHECK(gfx.video_mode == SIM_GRAPHICS_MODE_VGA_640X480);
    CHECK(gfx.g_3DB2 == 640 && gfx.g_3DB4 == 480 && gfx.g_3DB6 == 80);
    CHECK(gfx.framebuffer.width == 640 && gfx.framebuffer.height == 480);
    pixels = sim_graphics_pixels(&gfx, &size);
    CHECK(size == 640u * 480u);
    CHECK(last_mode_width == 640 && last_mode_height == 480 && mode_change_count == 1);
    mode_callback_result = SIM_GRAPHICS_NO_MEMORY;
    f_1B4E_015B(SIM_GRAPHICS_MODE_EGA_640X350);
    CHECK(sim_graphics_source_last_status() == SIM_GRAPHICS_NO_MEMORY);
    CHECK(gfx.video_mode == SIM_GRAPHICS_MODE_VGA_640X480);
    CHECK(gfx.g_3DB4 == 480 && gfx.framebuffer.height == 480);
    CHECK(last_mode_width == 640 && last_mode_height == 480);
    mode_callback_result = SIM_GRAPHICS_OK;
    f_1B4E_0228(0x1234);
    CHECK(gfx.overscan_color == 0x34);
    CHECK(f_1B4E_000D(0x1233) == 0x1233);
    f_1B4E_015B(0x13);
    CHECK(sim_graphics_source_last_status() == SIM_GRAPHICS_UNSUPPORTED_MODE);
    CHECK(sim_graphics_bind_source_abi(NULL, NULL) == SIM_GRAPHICS_OK);
    CHECK(g_9128 == NULL && g_912C == NULL && g_9130 == NULL &&
          g_9134 == NULL && g_9138 == NULL && g_913C == NULL &&
          g_9154 == NULL && g_9158 == NULL && g_9170 == NULL);
    sim_graphics_destroy(&gfx);
}

static void test_s00_pattern_rect_xor_and_font_slots(void)
{
    SimGraphicsDriver gfx;
    uint16_t source_g_5AAE = 0;
    uint8_t patterns[256] = {0};
    uint8_t bios8[256u * 8u] = {0};
    uint8_t bios14[256u * 14u] = {0};
    uint8_t custom[256u * 6u] = {0};
    uint8_t *pixels;
    size_t pixel_size;

    /* Two bytes per source pattern row; pattern 3 alternates distinct halves. */
    patterns[3u * 16u + 0u] = 0xaau;
    patterns[3u * 16u + 1u] = 0x55u;
    patterns[3u * 16u + 2u] = 0xccu;
    patterns[3u * 16u + 3u] = 0x33u;

    CHECK(sim_graphics_init(&gfx) == SIM_GRAPHICS_OK);
    CHECK(sim_graphics_bind_source_abi(&gfx, &source_g_5AAE) == SIM_GRAPHICS_OK);
    CHECK(g_912C != NULL && g_9130 != NULL && g_9138 != NULL && g_913C != NULL);
    CHECK(sim_graphics_set_bios_font_sources(&gfx, bios8, sizeof(bios8),
                                              bios14, sizeof(bios14)) == SIM_GRAPHICS_OK);
    CHECK(sim_graphics_set_custom_font_source(&gfx, custom, sizeof(custom)) == SIM_GRAPHICS_OK);

    /* Table-copy profile: slot1 is 8x8 and slot2 is 8x14. */
    g_912C();
    CHECK(sim_graphics_source_last_status() == SIM_GRAPHICS_OK);
    CHECK(gfx.g_3DDC == 8 && gfx.g_3DDE == 8 && gfx.g_3DDA == 8);
    g_9130();
    CHECK(sim_graphics_source_last_status() == SIM_GRAPHICS_OK);
    CHECK(gfx.g_3DDC == 14 && gfx.g_3DDE == 8 && gfx.g_3DDA == 14);

    /* The CGA initializer's two explicit writes change slot1/slot2 targets. */
    CHECK(sim_graphics_s00_apply_cga_font_overrides(&gfx) == SIM_GRAPHICS_OK);
    g_912C();
    CHECK(sim_graphics_source_last_status() == SIM_GRAPHICS_OK);
    CHECK(gfx.g_3DDC == 6 && gfx.g_3DDE == 4 && gfx.g_3DDA == 6);
    g_9130();
    CHECK(sim_graphics_source_last_status() == SIM_GRAPHICS_OK);
    CHECK(gfx.g_3DDC == 8 && gfx.g_3DDE == 8 && gfx.g_3DDA == 8);

    CHECK(sim_graphics_set_pattern_source(&gfx, patterns, sizeof(patterns)) == SIM_GRAPHICS_OK);
    CHECK(sim_graphics_g9128(&gfx, 5, 2, 0) == SIM_GRAPHICS_OK);
    CHECK(sim_graphics_g9138_pattern_rect(&gfx, 0, 0, 16, 2, 0x1233) ==
          SIM_GRAPHICS_OK);
    pixels = sim_graphics_pixels(&gfx, &pixel_size);
    CHECK(pixel_size == 640u * 350u);
    /* Pattern index is low nibble 3; source pattern x phase is screen aligned. */
    CHECK(pixels[0u * 640u + 0u] == 5); /* 0xAA bit 7 */
    CHECK(pixels[0u * 640u + 1u] == 2);
    CHECK(pixels[0u * 640u + 8u] == 2); /* second byte 0x55 bit 7 */
    CHECK(pixels[0u * 640u + 9u] == 5);
    CHECK(pixels[1u * 640u + 0u] == 5); /* row 1 begins with 0xCC */
    CHECK(pixels[1u * 640u + 1u] == 5);

    CHECK(sim_graphics_g913C_xor_rect(&gfx, 0, 0, 2, 1) == SIM_GRAPHICS_OK);
    CHECK(pixels[0u * 640u + 0u] == (uint8_t)(5u ^ 15u));
    CHECK(pixels[0u * 640u + 1u] == (uint8_t)(2u ^ 15u));

    source_g_5AAE = 1; /* unresolved overlay continuation remains fail-closed */
    g_9138(0, 0, 2, 1, 3);
    CHECK(sim_graphics_source_last_status() == SIM_GRAPHICS_UNSUPPORTED_MODE);
    g_913C(0, 0, 2, 1);
    CHECK(sim_graphics_source_last_status() == SIM_GRAPHICS_UNSUPPORTED_MODE);
    source_g_5AAE = 0;
    CHECK(sim_graphics_bind_source_abi(NULL, NULL) == SIM_GRAPHICS_OK);
    sim_graphics_destroy(&gfx);

    /* Missing real source views report debt instead of inventing BIOS bytes. */
    CHECK(sim_graphics_init(&gfx) == SIM_GRAPHICS_OK);
    CHECK(sim_graphics_bind_source_abi(&gfx, &source_g_5AAE) == SIM_GRAPHICS_OK);
    g_9138(0, 0, 2, 1, 3);
    CHECK(sim_graphics_source_last_status() == SIM_GRAPHICS_PATTERN_SOURCE_UNBOUND);
    g_9130();
    CHECK(sim_graphics_source_last_status() == SIM_GRAPHICS_FONT_UNBOUND);
    CHECK(gfx.g_3DDC == 14 && gfx.g_3DDA == 14);
    CHECK(sim_graphics_s00_apply_cga_font_overrides(&gfx) == SIM_GRAPHICS_OK);
    g_912C(); /* exact source no-op while its custom font pointer is null */
    CHECK(sim_graphics_source_last_status() == SIM_GRAPHICS_OK);
    CHECK(sim_graphics_bind_source_abi(NULL, NULL) == SIM_GRAPHICS_OK);
    sim_graphics_destroy(&gfx);
}

int main(void)
{
    test_defaults_and_source_tables();
    test_color_attribute_and_fill_clip();
    test_glyph_and_text_pen();
    test_six_pixel_fold_fails_explicitly();
    test_source_abi_and_vga_mode();
    test_s00_pattern_rect_xor_and_font_slots();
    puts("whole-program graphics contracts: PASS");
    return 0;
}
