#include "graphics_s00_map_tables.h"

#include "graphics.h"
#include "graphics_bitmap_source.h"

#include <string.h>
#include <stdlib.h>

/* The original lookup rows are described here as visual dither tokens rather
 * than copied object bytes. A token selects the bit pattern contributed by a
 * source map color to one EGA plane. */
typedef enum SimDitherToken {
    DITHER_CLEAR = 0,
    DITHER_SOLID,
    DITHER_EVEN,
    DITHER_ODD
} SimDitherToken;

typedef struct SimDitherColor {
    SimDitherToken plane[4];
} SimDitherColor;

#define C(a,b,c,d) {{a,b,c,d}}
static const SimDitherColor s_table_640[25] = {
    C(DITHER_CLEAR,DITHER_CLEAR,DITHER_CLEAR,DITHER_CLEAR),
    C(DITHER_SOLID,DITHER_CLEAR,DITHER_CLEAR,DITHER_CLEAR),
    C(DITHER_CLEAR,DITHER_SOLID,DITHER_CLEAR,DITHER_CLEAR),
    C(DITHER_SOLID,DITHER_SOLID,DITHER_CLEAR,DITHER_CLEAR),
    C(DITHER_CLEAR,DITHER_CLEAR,DITHER_SOLID,DITHER_CLEAR),
    C(DITHER_SOLID,DITHER_CLEAR,DITHER_SOLID,DITHER_CLEAR),
    C(DITHER_CLEAR,DITHER_SOLID,DITHER_SOLID,DITHER_CLEAR),
    C(DITHER_SOLID,DITHER_SOLID,DITHER_SOLID,DITHER_CLEAR),
    C(DITHER_CLEAR,DITHER_CLEAR,DITHER_CLEAR,DITHER_SOLID),
    C(DITHER_SOLID,DITHER_CLEAR,DITHER_CLEAR,DITHER_SOLID),
    C(DITHER_CLEAR,DITHER_SOLID,DITHER_CLEAR,DITHER_SOLID),
    C(DITHER_SOLID,DITHER_SOLID,DITHER_CLEAR,DITHER_SOLID),
    C(DITHER_CLEAR,DITHER_CLEAR,DITHER_SOLID,DITHER_SOLID),
    C(DITHER_SOLID,DITHER_CLEAR,DITHER_SOLID,DITHER_SOLID),
    C(DITHER_CLEAR,DITHER_SOLID,DITHER_SOLID,DITHER_SOLID),
    C(DITHER_SOLID,DITHER_SOLID,DITHER_SOLID,DITHER_SOLID),
    C(DITHER_SOLID,DITHER_EVEN,DITHER_CLEAR,DITHER_EVEN),
    C(DITHER_SOLID,DITHER_EVEN,DITHER_CLEAR,DITHER_EVEN),
    C(DITHER_SOLID,DITHER_CLEAR,DITHER_CLEAR,DITHER_CLEAR),
    C(DITHER_EVEN,DITHER_ODD,DITHER_CLEAR,DITHER_CLEAR),
    C(DITHER_CLEAR,DITHER_SOLID,DITHER_CLEAR,DITHER_CLEAR),
    C(DITHER_ODD,DITHER_SOLID,DITHER_CLEAR,DITHER_CLEAR),
    C(DITHER_SOLID,DITHER_SOLID,DITHER_CLEAR,DITHER_CLEAR),
    C(DITHER_EVEN,DITHER_EVEN,DITHER_ODD,DITHER_CLEAR),
    C(DITHER_CLEAR,DITHER_CLEAR,DITHER_SOLID,DITHER_CLEAR)
};
static const SimDitherColor s_table_320[25] = {
    C(DITHER_SOLID,DITHER_SOLID,DITHER_SOLID,DITHER_SOLID),
    C(DITHER_CLEAR,DITHER_SOLID,DITHER_SOLID,DITHER_SOLID),
    C(DITHER_CLEAR,DITHER_CLEAR,DITHER_SOLID,DITHER_SOLID),
    C(DITHER_CLEAR,DITHER_CLEAR,DITHER_SOLID,DITHER_CLEAR),
    C(DITHER_SOLID,DITHER_CLEAR,DITHER_SOLID,DITHER_SOLID),
    C(DITHER_SOLID,DITHER_CLEAR,DITHER_SOLID,DITHER_CLEAR),
    C(DITHER_SOLID,DITHER_CLEAR,DITHER_CLEAR,DITHER_CLEAR),
    C(DITHER_SOLID,DITHER_SOLID,DITHER_CLEAR,DITHER_SOLID),
    C(DITHER_CLEAR,DITHER_SOLID,DITHER_CLEAR,DITHER_SOLID),
    C(DITHER_CLEAR,DITHER_SOLID,DITHER_CLEAR,DITHER_CLEAR),
    C(DITHER_CLEAR,DITHER_SOLID,DITHER_SOLID,DITHER_CLEAR),
    C(DITHER_CLEAR,DITHER_SOLID,DITHER_SOLID,DITHER_CLEAR),
    C(DITHER_SOLID,DITHER_SOLID,DITHER_SOLID,DITHER_SOLID),
    C(DITHER_SOLID,DITHER_SOLID,DITHER_SOLID,DITHER_CLEAR),
    C(DITHER_CLEAR,DITHER_CLEAR,DITHER_CLEAR,DITHER_SOLID),
    C(DITHER_CLEAR,DITHER_CLEAR,DITHER_CLEAR,DITHER_CLEAR),
    C(DITHER_CLEAR,DITHER_SOLID,DITHER_SOLID,DITHER_ODD),
    C(DITHER_CLEAR,DITHER_SOLID,DITHER_SOLID,DITHER_ODD),
    C(DITHER_CLEAR,DITHER_SOLID,DITHER_SOLID,DITHER_SOLID),
    C(DITHER_CLEAR,DITHER_EVEN,DITHER_SOLID,DITHER_SOLID),
    C(DITHER_CLEAR,DITHER_CLEAR,DITHER_SOLID,DITHER_SOLID),
    C(DITHER_CLEAR,DITHER_CLEAR,DITHER_SOLID,DITHER_EVEN),
    C(DITHER_CLEAR,DITHER_CLEAR,DITHER_SOLID,DITHER_CLEAR),
    C(DITHER_ODD,DITHER_CLEAR,DITHER_SOLID,DITHER_ODD),
    C(DITHER_SOLID,DITHER_CLEAR,DITHER_SOLID,DITHER_SOLID)
};
#undef C

static uint8_t dither_byte(SimDitherToken token)
{
    switch (token) {
    case DITHER_CLEAR: return 0x00;
    case DITHER_SOLID: return 0xff;
    case DITHER_EVEN: return 0x55;
    case DITHER_ODD: return 0xaa;
    default: return 0;
    }
}

static SimS00MapTableStatus check_spans(const uint8_t *source, size_t source_size,
                                        size_t need_source,
                                        uint8_t *destination, size_t destination_size,
                                        size_t need_destination)
{
    if (source == NULL || destination == NULL)
        return SIM_S00_MAP_TABLE_BAD_ARGUMENT;
    if (source_size != need_source || destination_size != need_destination)
        return SIM_S00_MAP_TABLE_BAD_SPAN;
    return SIM_S00_MAP_TABLE_OK;
}

static SimS00MapTableStatus expand_4lane(const uint8_t *source, size_t source_size,
                                         uint8_t *destination, size_t destination_size,
                                         const SimDitherColor *table,
                                         size_t source_pixels, size_t output_size)
{
    size_t i;
    size_t groups = source_pixels / 2u;
    SimS00MapTableStatus status = check_spans(source, source_size, source_pixels,
                                               destination, destination_size,
                                               output_size);
    if (status != SIM_S00_MAP_TABLE_OK)
        return status;
    for (i = 0; i < source_pixels; ++i) {
        if (source[i] >= 25)
            return SIM_S00_MAP_TABLE_UNSUPPORTED_COLOR;
    }
    memset(destination, 0, output_size);
    for (i = 0; i < groups; ++i) {
        unsigned lane;
        for (lane = 0; lane < 4; ++lane) {
            uint8_t first = dither_byte(table[source[2u * i]].plane[lane]);
            uint8_t second = dither_byte(table[source[2u * i + 1u]].plane[lane]);
            uint8_t first_rotated = (uint8_t)((first << 1) | (first >> 7));
            uint8_t second_rotated = (uint8_t)((second << 1) | (second >> 7));
            size_t offset = (size_t)lane * groups + i;
            size_t rotated_offset = 4u * groups + offset;
            destination[offset] = (uint8_t)((first & 0xf0u) | (second & 0x0fu));
            destination[rotated_offset] = (uint8_t)((first_rotated & 0xf0u) |
                                                    (second_rotated & 0x0fu));
            destination[8u * groups + offset] = destination[offset];
            destination[12u * groups + offset] = destination[rotated_offset];
        }
    }
    return SIM_S00_MAP_TABLE_OK;
}

static SimS00MapTableStatus expand_2bit(const uint8_t *source, size_t source_size,
                                        uint8_t *destination, size_t destination_size,
                                        const SimDitherColor *table,
                                        size_t source_pixels, size_t pixels_per_byte,
                                        size_t output_size)
{
    static const uint8_t masks[4] = {0xc0, 0x30, 0x0c, 0x03};
    size_t i;
    size_t groups = source_pixels / pixels_per_byte;
    SimS00MapTableStatus status = check_spans(source, source_size, source_pixels,
                                               destination, destination_size,
                                               output_size);
    if (status != SIM_S00_MAP_TABLE_OK)
        return status;
    for (i = 0; i < source_pixels; ++i) {
        if (source[i] >= 25)
            return SIM_S00_MAP_TABLE_UNSUPPORTED_COLOR;
    }
    memset(destination, 0, output_size);
    for (i = 0; i < groups; ++i) {
        size_t n;
        for (n = 0; n < pixels_per_byte; ++n) {
            unsigned plane;
            for (plane = 0; plane < 4; ++plane) {
                uint8_t pattern = dither_byte(table[source[i * pixels_per_byte + n]]
                                              .plane[plane]);
                size_t index = (size_t)plane * groups + i;
                destination[index] |= (uint8_t)(pattern & masks[n]);
            }
        }
        /* The assembly duplicates each generated horizontal row into the
         * second half of the destination image. */
        for (unsigned plane = 0; plane < 4; ++plane) {
            size_t offset = (size_t)plane * groups + i;
            destination[4u * groups + offset] = destination[offset];
        }
    }
    return SIM_S00_MAP_TABLE_OK;
}

static SimS00MapTableStatus map_four_plane(const uint8_t *source, size_t source_size,
                                           uint8_t *destination, size_t destination_size,
                                           int small)
{
    const SimDitherColor *table = s_table_640;
    /* Assembly's four-cell packer emits a pair of 4-plane rows. */
    return expand_4lane(source, source_size, destination, destination_size,
                        table, small ? 64u : 128u,
                        small ? 0x200u : 0x400u);
}

SimS00MapTableStatus sim_s00_map_0000(const uint8_t *source, size_t source_size,
                                      uint8_t *destination, size_t destination_size)
{
    return map_four_plane(source, source_size, destination, destination_size, 0);
}

SimS00MapTableStatus sim_s00_map_0137(const uint8_t *source, size_t source_size,
                                      uint8_t *destination, size_t destination_size)
{
    return map_four_plane(source, source_size, destination, destination_size, 1);
}

SimS00MapTableStatus sim_s00_map_026A(const uint8_t *source, size_t source_size,
                                      uint8_t *destination, size_t destination_size)
{
    return expand_2bit(source, source_size, destination, destination_size,
                       s_table_320, 128u, 4u, 0x100u);
}

SimS00MapTableStatus sim_s00_map_03A9(const uint8_t *source, size_t source_size,
                                      uint8_t *destination, size_t destination_size)
{
    return expand_2bit(source, source_size, destination, destination_size,
                       s_table_320, 64u, 4u, 0x80u);
}

static SimS00MapTableStatus expand_minimap(const uint8_t *source, size_t source_size,
                                           uint8_t *destination, size_t destination_size,
                                           SimS00MapTableProfile profile,
                                           size_t source_pixels, size_t columns,
                                           size_t output_size)
{
    static const uint8_t bit_masks[8] = {0x80,0x40,0x20,0x10,0x08,0x04,0x02,0x01};
    const SimDitherColor *table;
    size_t i;
    SimS00MapTableStatus status;
    if (profile == SIM_S00_MAP_TABLE_640)
        table = s_table_640;
    else if (profile == SIM_S00_MAP_TABLE_320)
        table = s_table_320;
    else
        return SIM_S00_MAP_TABLE_BAD_ARGUMENT;
    status = check_spans(source, source_size, source_pixels,
                         destination, destination_size, output_size);
    if (status != SIM_S00_MAP_TABLE_OK)
        return status;
    for (i = 0; i < source_pixels; ++i) {
        if (source[i] >= 25)
            return SIM_S00_MAP_TABLE_UNSUPPORTED_COLOR;
    }
    memset(destination, 0, output_size);
    for (i = 0; i < source_pixels; ++i) {
        size_t column = i / 8u;
        unsigned position = (unsigned)(i & 7u);
        unsigned plane;
        for (plane = 0; plane < 4; ++plane) {
            uint8_t pattern = dither_byte(table[source[i]].plane[plane]);
            destination[(size_t)plane * columns + column] |=
                (uint8_t)(pattern & bit_masks[position]);
        }
    }
    return SIM_S00_MAP_TABLE_OK;
}

SimS00MapTableStatus sim_s00_map_04D8(const uint8_t *source, size_t source_size,
                                      uint8_t *destination, size_t destination_size,
                                      SimS00MapTableProfile profile)
{
    return expand_minimap(source, source_size, destination, destination_size,
                          profile, 128u, 16u, 64u);
}

SimS00MapTableStatus sim_s00_map_06A3(const uint8_t *source, size_t source_size,
                                      uint8_t *destination, size_t destination_size,
                                      SimS00MapTableProfile profile)
{
    return expand_minimap(source, source_size, destination, destination_size,
                          profile, 64u, 8u, 32u);
}

SimS00MapTableStatus sim_s00_map_transform_draw(
    SimGraphicsDriver *graphics, SimS00MapTableTransform transform,
    int16_t x, int16_t y, const uint8_t *source, size_t source_size)
{
    uint8_t planar[0x400];
    size_t planar_size;
    int16_t width;
    int16_t height;
    SimS00MapTableStatus status;
    SimS00MapTableProfile profile;

    if (graphics == NULL || source == NULL)
        return SIM_S00_MAP_TABLE_BAD_ARGUMENT;
    if (g_914C == NULL || sim_graphics_source_owner() != graphics)
        return SIM_S00_MAP_TABLE_RENDERER_UNBOUND;
    profile = graphics->g_3DB2 == 320 ? SIM_S00_MAP_TABLE_320 :
                                        SIM_S00_MAP_TABLE_640;
    switch (transform) {
    case SIM_S00_TRANSFORM_0000:
        planar_size = 0x400; width = 512; height = 4;
        status = sim_s00_map_0000(source, source_size, planar, planar_size);
        break;
    case SIM_S00_TRANSFORM_0137:
        planar_size = 0x200; width = 256; height = 4;
        status = sim_s00_map_0137(source, source_size, planar, planar_size);
        break;
    case SIM_S00_TRANSFORM_026A:
        planar_size = 0x100; width = 256; height = 2;
        status = sim_s00_map_026A(source, source_size, planar, planar_size);
        break;
    case SIM_S00_TRANSFORM_03A9:
        planar_size = 0x80; width = 128; height = 2;
        status = sim_s00_map_03A9(source, source_size, planar, planar_size);
        break;
    case SIM_S00_TRANSFORM_04D8:
        planar_size = 0x40; width = 128; height = 1;
        status = sim_s00_map_04D8(source, source_size, planar, planar_size,
                                  profile);
        break;
    case SIM_S00_TRANSFORM_06A3:
        planar_size = 0x20; width = 64; height = 1;
        status = sim_s00_map_06A3(source, source_size, planar, planar_size,
                                  profile);
        break;
    default:
        return SIM_S00_MAP_TABLE_BAD_ARGUMENT;
    }
    if (status != SIM_S00_MAP_TABLE_OK)
        return status;
    g_914C(x, y, (char *)planar, width, height);
    return graphics->last_status == SIM_GRAPHICS_OK ? SIM_S00_MAP_TABLE_OK :
        SIM_S00_MAP_TABLE_RENDERER_FAILED;
}

static void require_transform(SimS00MapTableStatus status)
{
    if (status != SIM_S00_MAP_TABLE_OK)
        abort();
}

void o00_3126_0000(char *source, char *destination, int16_t source_width, int16_t count)
{
    (void)source_width;
    (void)count;
    require_transform(sim_s00_map_0000((const uint8_t *)source, 128,
                                        (uint8_t *)destination, 0x400));
}

void o00_3126_0137(char *source, char *destination, int16_t source_width, int16_t count)
{
    (void)source_width;
    (void)count;
    require_transform(sim_s00_map_0137((const uint8_t *)source, 64,
                                        (uint8_t *)destination, 0x200));
}

void o00_3126_026A(char *source, char *destination, int16_t source_width, int16_t count)
{
    (void)source_width;
    (void)count;
    require_transform(sim_s00_map_026A((const uint8_t *)source, 128,
                                        (uint8_t *)destination, 0x100));
}

void o00_3126_03A9(char *source, char *destination, int16_t source_width, int16_t count)
{
    (void)source_width;
    (void)count;
    require_transform(sim_s00_map_03A9((const uint8_t *)source, 64,
                                        (uint8_t *)destination, 0x80));
}

static SimS00MapTableProfile active_profile(void)
{
    SimGraphicsDriver *graphics = sim_graphics_source_owner();
    if (graphics == NULL)
        abort();
    return graphics->g_3DB2 == 320 ? SIM_S00_MAP_TABLE_320 :
                                     SIM_S00_MAP_TABLE_640;
}

void o00_3126_04D8(char *source, char *destination)
{
    require_transform(sim_s00_map_04D8((const uint8_t *)source, 128,
                                        (uint8_t *)destination, 64,
                                        active_profile()));
}

void o00_3126_06A3(char *source, char *destination)
{
    require_transform(sim_s00_map_06A3((const uint8_t *)source, 64,
                                        (uint8_t *)destination, 32,
                                        active_profile()));
}
