#include "portable/whole_program/platform/graphics_capture_source.h"
#include "portable/whole_program/platform/graphics_tile_upload.h"
#include "portable/whole_program/platform/handles.h"
#include "portable/whole_program/platform/m1b73_mouse_state.h"
#include "portable/whole_program/platform/graphics_source_clip.h"

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

char *g_3DA8;
SimGraphicsStatus sim_source_font_bind_driver_view_v1(SimGraphicsDriver *graphics)
{
    (void)graphics;
    return SIM_GRAPHICS_FONT_UNBOUND;
}

void f_1D8E_0384(SimGraphicsPatternRectCallback callback, int16_t unused1,
                 int16_t unused2, int16_t left, int16_t top, int16_t right,
                 int16_t bottom, int16_t pattern)
{
    (void)callback; (void)unused1; (void)unused2; (void)left; (void)top;
    (void)right; (void)bottom; (void)pattern;
}

void f_1D8E_070E(char *port, int16_t x, int16_t y, char *bits,
                 int16_t width, int16_t height)
{
    (void)port; (void)x; (void)y; (void)bits; (void)width; (void)height;
}

void f_1D8E_07F6(char *port, int16_t x, int16_t y, char *bits,
                 int16_t width, int16_t height)
{
    (void)port; (void)x; (void)y; (void)bits; (void)width; (void)height;
}

#define CHECK(x) do { if (!(x)) { \
    fprintf(stderr, "FAIL %d: %s\n", __LINE__, #x); return 1; \
} } while (0)

static uint8_t frame_pixel(int x, int y)
{
    return (uint8_t)((x * 3 + y * 5 + (x >> 2) + (y >> 1)) & 15);
}

static uint64_t fnv1a(const uint8_t *bytes, size_t size)
{
    uint64_t hash = UINT64_C(14695981039346656037);
    size_t i;
    for (i = 0; i < size; ++i) {
        hash ^= bytes[i];
        hash *= UINT64_C(1099511628211);
    }
    return hash;
}

static int compare_capture(const uint8_t *capture, int left, int top,
                           int right, int bottom,
                           const SimGraphicsDriver *graphics)
{
    const unsigned columns = (unsigned)(((right - 1) >> 3) - (left >> 3) + 1);
    const unsigned height = (unsigned)(bottom - top);
    const int aligned_left = (left >> 3) << 3;
    unsigned row, plane, byte_x, bit;
    if (capture[0] != columns * 8u || capture[1] != 0 ||
        capture[2] != height || capture[3] != 0)
        return 0;
    for (row = 0; row < height; ++row) {
        const int y = top + (int)row;
        for (plane = 0; plane < 4; ++plane) {
            for (byte_x = 0; byte_x < columns; ++byte_x) {
                uint8_t expected = 0;
                for (bit = 0; bit < 8; ++bit) {
                    const int x = aligned_left + (int)(byte_x * 8u + bit);
                    int set;
                    if (y < graphics->g_3DB4) {
                        set = (frame_pixel(x, y) & (1u << plane)) != 0;
                    } else {
                        size_t plane_size;
                        const uint8_t *source = sim_graphics_tile_upload_plane(
                            plane, &plane_size);
                        const size_t offset = (size_t)y *
                            (size_t)graphics->g_3DB6 + (size_t)x / 8u;
                        if (source == NULL || plane_size != 0x10000u)
                            return 0;
                        set = (source[offset] & (uint8_t)(0x80u >> (x & 7))) != 0;
                    }
                    if (set)
                        expected |= (uint8_t)(0x80u >> bit);
                }
                if (capture[4u + (size_t)row * columns * 4u +
                            (size_t)plane * columns + byte_x] != expected)
                    return 0;
            }
        }
    }
    return 1;
}

int main(void)
{
    SimGraphicsDriver graphics, wrong_owner;
    struct Rect *clip_list = NULL;
    char **handle;
    uint8_t *payload;
    uint8_t map_source[0x8000];
    uint8_t page_source[4][0x2000];
    uint8_t direct[4 + 3 * 10 * 4];
    uint8_t short_buffer[sizeof(direct)];
    size_t hidden_base = 350u * 80u;
    size_t output_size;
    unsigned plane;
    int x, y;

    memset(&graphics, 0, sizeof(graphics));
    CHECK(sim_graphics_init(&graphics) == SIM_GRAPHICS_OK);
    CHECK(sim_graphics_set_mode(&graphics, SIM_GRAPHICS_MODE_EGA_640X350) ==
          SIM_GRAPHICS_OK);
    CHECK(sim_graphics_bind_source_abi(&graphics, &clip_list) == SIM_GRAPHICS_OK);
    CHECK(sim_graphics_source_capture_bind(&graphics) == SIM_GRAPHICS_OK);
    CHECK(sim_graphics_tile_upload_bind(&graphics) == SIM_GRAPHICS_TILE_UPLOAD_OK);
    for (y = 0; y < graphics.g_3DB4; ++y)
        for (x = 0; x < graphics.g_3DB2; ++x)
            graphics.pixel_storage[(size_t)y * graphics.framebuffer.stride +
                                   (size_t)x] = frame_pixel(x, y);

    /* The source bind starts one shared four-plane aperture at zero. Then
     * cache/page uploads write nonzero off-display bytes into that same owner. */
    for (plane = 0; plane < 4; ++plane) {
        const uint8_t *source = sim_graphics_tile_upload_plane(plane, &output_size);
        CHECK(source != NULL && output_size == 0x10000u);
        CHECK(source[hidden_base + 53u] == 0);
    }
    for (y = 0; y < (int)sizeof(map_source); ++y)
        map_source[y] = (uint8_t)(0x43u ^ (unsigned)y * 29u);
    o00_31AD_18BA((char *)map_source, UINT16_C(0xa000), UINT16_C(0x0100));
    for (plane = 0; plane < 4; ++plane) {
        for (y = 0; y < (int)sizeof(page_source[plane]); ++y)
            page_source[plane][y] = (uint8_t)(0x81u ^ plane * 0x35u ^ (unsigned)y * 13u);
        o00_31AD_186A((char *)page_source[plane], UINT16_C(0xc000),
                      (int16_t)plane, UINT16_C(0x2000));
    }

    /* A rectangle crossing the 350-row display edge takes visible pixels
     * from the sole indexed framebuffer and hidden bytes from the same
     * 64 KiB planar backing. */
    CHECK(sim_graphics_s00_capture_rect_source_aperture(
              &graphics, 424, 345, 448, 355, direct, sizeof(direct)) ==
          SIM_GRAPHICS_OK);
    CHECK(compare_capture(direct, 424, 345, 448, 355, &graphics));
    CHECK(sim_graphics_s00_capture_rect_source_aperture(
              &graphics, 424, 510, 448, 516, direct, sizeof(direct)) ==
          SIM_GRAPHICS_OK);
    CHECK(compare_capture(direct, 424, 510, 448, 516, &graphics));
    CHECK(sim_graphics_s00_capture_rect_source_aperture(
              &graphics, 424, 614, 448, 616, direct, sizeof(direct)) ==
          SIM_GRAPHICS_OK);
    CHECK(compare_capture(direct, 424, 614, 448, 616, &graphics));
    CHECK(sim_graphics_s00_capture_size_checked(
              &graphics, 424, 345, 448, 355, &output_size) ==
          SIM_GRAPHICS_INVALID_ARGUMENT);
    CHECK(sim_graphics_s00_capture_rect_source_aperture(
              &graphics, 424, 345, 448, 355, short_buffer,
              sizeof(direct) - 1u) == SIM_GRAPHICS_INVALID_ARGUMENT);
    CHECK(sim_graphics_s00_capture_rect_source_aperture(
              &wrong_owner, 424, 345, 448, 355, direct, sizeof(direct)) ==
          SIM_GRAPHICS_INVALID_ARGUMENT);
    CHECK(sim_graphics_s00_capture_rect_source_aperture(
              &graphics, 424, 819, 432, 820, direct, sizeof(direct)) ==
          SIM_GRAPHICS_INVALID_ARGUMENT);

    /* Source g9148 gets an interior pointer into a real movable handle. Its
     * measured remaining span, not the allocation base, bounds the write. */
    CHECK(sim_handles_global_configure(4096u, 64u) == SIM_HANDLE_OK);
    handle = f_171C_1A9E(512, 1, "ega-capture");
    CHECK(handle != NULL);
    payload = (uint8_t *)f_171C_1B84(handle);
    CHECK(payload != NULL);
    memset(payload, 0xa5, 512u);
    g_4333 = 1; /* source lock suppresses independent cursor hooks */
    g_3DD4 = UINT16_C(0x5a07);
    g_9148(424, 345, 448, 355, (char *)(payload + 7u));
    CHECK(sim_graphics_source_last_status() == SIM_GRAPHICS_OK);
    CHECK(g_3DD4 == UINT16_C(0x5a07));
    CHECK(payload[6] == 0xa5 && payload[7u + sizeof(direct)] == 0xa5);
    CHECK(compare_capture(payload + 7u, 424, 345, 448, 355, &graphics));
    printf("capture-345-355=%016llx\n",
           (unsigned long long)fnv1a(payload + 7u, sizeof(direct)));
    g_9148(424, 431, 448, 445, (char *)(payload + 7u));
    CHECK(sim_graphics_source_last_status() == SIM_GRAPHICS_OK);
    CHECK(compare_capture(payload + 7u, 424, 431, 448, 445, &graphics));
    printf("capture-431-445=%016llx\n",
           (unsigned long long)fnv1a(payload + 7u, 4u + 3u * 14u * 4u));
    g_9148(424, 510, 448, 516, (char *)(payload + 7u));
    CHECK(sim_graphics_source_last_status() == SIM_GRAPHICS_OK);
    CHECK(compare_capture(payload + 7u, 424, 510, 448, 516, &graphics));
    printf("capture-510-516=%016llx\n",
           (unsigned long long)fnv1a(payload + 7u, 4u + 3u * 6u * 4u));
    g_9148(424, 614, 448, 616, (char *)(payload + 7u));
    CHECK(sim_graphics_source_last_status() == SIM_GRAPHICS_OK);
    CHECK(compare_capture(payload + 7u, 424, 614, 448, 616, &graphics));
    printf("capture-614-616=%016llx\n",
           (unsigned long long)fnv1a(payload + 7u, 4u + 3u * 2u * 4u));
    CHECK(f_171C_1BBA(handle) != NULL);
    sim_graphics_source_capture_unbind();
    sim_graphics_tile_upload_unbind();
    sim_graphics_bind_source_abi(NULL, NULL);
    sim_graphics_destroy(&graphics);
    puts("EGA source aperture capture: visible owner, hidden plane backing, bounds and interior handle passed");
    return 0;
}
