#include "portable/whole_program/platform/graphics.h"
#include "portable/whole_program/platform/graphics_bitmap_source.h"
#include "portable/whole_program/platform/graphics_source_clip.h"
#include "portable/whole_program/window_source_globals.h"

#include <stdio.h>
#include <string.h>

#define CHECK(c) do { if (!(c)) { \
    fprintf(stderr, "FAIL line %d: %s\n", __LINE__, #c); return 1; \
} } while (0)

static uint8_t expected_pixel(const uint8_t *source, unsigned width,
                              unsigned x, unsigned y)
{
    size_t plane_row = (width + 7u) / 8u;
    size_t row_bytes = plane_row * 4u;
    uint8_t mask = (uint8_t)(1u << (7u - (x & 7u)));
    uint8_t color = 0;
    unsigned plane;
    for (plane = 0; plane < 4; ++plane) {
        size_t at = (size_t)y * row_bytes + plane * plane_row + (x >> 3);
        if (source[at] & mask)
            color |= (uint8_t)(1u << plane);
    }
    return color;
}

int main(void)
{
    SimGraphicsDriver graphics;
    uint8_t source[3u * 8u];
    uint8_t planes_112[112u * 14u * 4u];
    uint8_t *pixels;
    size_t size;
    struct Rect clips[3];
    unsigned y, x;

    for (y = 0; y < 3; ++y)
        for (x = 0; x < 8; ++x)
            source[y * 8u + x] = (uint8_t)(0x96u ^ (y * 37u) ^ (x * 19u));

    CHECK(sim_graphics_init(&graphics) == SIM_GRAPHICS_OK);
    CHECK(g_5AAC == NULL);
    CHECK(g_5A9C.left == 0 && g_5A9C.top == 0 &&
          g_5A9C.right == 349 && g_5A9C.bottom == 639);
    sim_window_source_set_profile(0);
    CHECK(sim_graphics_bind_source_abi(&graphics,
                                      sim_graphics_source_clip_slot()) == SIM_GRAPHICS_OK);
    CHECK(sim_graphics_source_bitmap_bind(&graphics) == SIM_GRAPHICS_OK);
    CHECK(g_914C != NULL && g_9150 != NULL);
    pixels = sim_graphics_pixels(&graphics, &size);
    CHECK(pixels != NULL && size == 640u * 350u);

    /* Match the dimensions and four synthetic plane-byte values from the
     * original DOS direct g914C probe (112 x 112, 6,272 source bytes). */
    for (y = 0; y < 112; ++y) {
        unsigned plane;
        for (plane = 0; plane < 4; ++plane) {
            unsigned b;
            uint8_t value = (uint8_t)(0x11u << plane);
            for (b = 0; b < 14; ++b)
                planes_112[(size_t)y * 56u + plane * 14u + b] = value;
        }
    }
    memset(pixels, 0, size);
    g_5AAC = NULL;
    fd_55B3_3DE6 = fd_55B3_3DE8 = 0;
    g_914C(100, 100, (char *)planes_112, 112, 112);
    CHECK(graphics.last_status == SIM_GRAPHICS_OK);
    for (y = 0; y < 112; ++y)
        for (x = 0; x < 112; ++x)
            CHECK(pixels[(100u + y) * 640u + 100u + x] ==
                  expected_pixel(planes_112, 112, x, y));

    /* Null clip pointer takes the native direct source entry. */
    memset(pixels, 0, size);
    g_5AAC = NULL;
    fd_55B3_3DE6 = fd_55B3_3DE8 = 0;
    g_914C(40, 30, (char *)source, 16, 3);
    CHECK(graphics.last_status == SIM_GRAPHICS_OK);
    for (y = 0; y < 3; ++y)
        for (x = 0; x < 16; ++x)
            CHECK(pixels[(30u + y) * 640u + 40u + x] ==
                  expected_pixel(source, 16, x, y));

    /* A non-null source pointer dispatches the actual generated root clipper.
     * Two disjoint half-open intersections exercise source offsets on both sides. */
    memset(pixels, 0, size);
    clips[0] = (struct Rect){ 42, 31, 47, 33 };
    clips[1] = (struct Rect){ 51, 30, 55, 32 };
    clips[2] = (struct Rect){ 0, (int16_t)0x8000, 0, 0 };
    g_5AAC = clips;
    fd_55B3_3DE6 = fd_55B3_3DE8 = 0;
    g_914C(40, 30, (char *)source, 16, 3);
    CHECK(graphics.last_status == SIM_GRAPHICS_OK);
    CHECK(fd_55B3_3DE6 == 0 && fd_55B3_3DE8 == 0);
    for (y = 0; y < 3; ++y) {
        for (x = 0; x < 16; ++x) {
            int visible = ((y >= 1 && y < 3 && x >= 2 && x < 7) ||
                           (y < 2 && x >= 11 && x < 15));
            uint8_t expected = visible ? expected_pixel(source, 16, x, y) : 0;
            CHECK(pixels[(30u + y) * 640u + 40u + x] == expected);
        }
    }
    g_5AAC = NULL;
    sim_graphics_source_bitmap_unbind();
    CHECK(sim_graphics_bind_source_abi(NULL, NULL) == SIM_GRAPHICS_OK);
    sim_graphics_destroy(&graphics);
    puts("PASS actual source g914C/g9150 direct and root clipping paths");
    return 0;
}
