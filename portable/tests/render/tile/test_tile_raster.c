#include "../../../game/resources/database.h"
#include "../../../render/tile_raster.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void fail(const char *message)
{
    fprintf(stderr, "tile raster test failed: %s\n", message);
    exit(1);
}

static void synthetic_contract(void)
{
    uint8_t atlas[PORTABLE_EGA_TILE_SOURCE_BYTES];
    uint8_t life[PORTABLE_EGA_LIFE_FRAME_BYTES];
    uint8_t pixels[PORTABLE_EGA_TILE_PIXELS];
    unsigned plane, y;

    memset(atlas, 0, sizeof(atlas));
    memset(life, 0, sizeof(life));
    for (plane = 0; plane < 4u; ++plane) {
        unsigned row;
        for (row = 0; row < PORTABLE_EGA_TILE_HEIGHT; ++row)
            atlas[row * 8u + plane * 2u] = 0x80u;
        life[2u + plane * 2u] = (uint8_t)(0x80u >> (3u - plane));
    }
    life[0] = 0x80u; /* Replace only the first pixel. */

    if (portable_ega_tile_decode(atlas, sizeof(atlas), 0, pixels) != PORTABLE_RENDER_OK)
        fail("synthetic ground tile rejected");
    for (y = 0; y < PORTABLE_EGA_TILE_HEIGHT; ++y) {
        if (pixels[y * PORTABLE_EGA_TILE_WIDTH] != 15u ||
            pixels[y * PORTABLE_EGA_TILE_WIDTH + 1u] != 0u)
            fail("interleaved EGA plane unpack is wrong");
    }
    if (portable_ega_life_composite(pixels, life, sizeof(life), 0) != PORTABLE_RENDER_OK)
        fail("synthetic life frame rejected");
    if (pixels[0] != 8u || pixels[1] != 0u)
        fail("life mask did not replace exactly selected pixel");
    if (portable_ega_tile_decode(atlas, sizeof(atlas) - 1u, 0, pixels) !=
        PORTABLE_RENDER_TRUNCATED_DATA)
        fail("truncated ground span was accepted");
    if (portable_ega_life_composite(pixels, life, sizeof(life) - 1u, 0) !=
        PORTABLE_RENDER_TRUNCATED_DATA)
        fail("truncated life span was accepted");
}

static void actual_resource_contract(const char *asset_root)
{
    char root[1024];
    PortableDatabase db;
    int ground_id, life_id;

    if (snprintf(root, sizeof(root), "%s/HCEGANT", asset_root) < 0 ||
        strlen(root) >= sizeof(root))
        fail("asset path too long");
    if (portable_db_open(&db, root) != PORTABLE_DB_OK)
        fail("cannot open HCEGANT database");

    for (ground_id = 9; ground_id <= 10; ++ground_id) {
        PortableDbRecord record = {0};
        uint8_t pixels[PORTABLE_EGA_TILE_PIXELS];
        unsigned tile;
        if (portable_db_load(&db, (int16_t)ground_id, 9, &record) != PORTABLE_DB_OK)
            fail("cannot load ground atlas");
        if (record.size != 0x8000u)
            fail("ground atlas size differs from source copy contract");
        for (tile = 0; tile < 256u; ++tile) {
            unsigned pixel;
            if (portable_ega_tile_decode(record.data, record.size, (uint16_t)tile,
                                         pixels) != PORTABLE_RENDER_OK)
                fail("actual ground tile decode failed");
            for (pixel = 0; pixel < PORTABLE_EGA_TILE_PIXELS; ++pixel)
                if (pixels[pixel] > 15u)
                    fail("ground decoder emitted a non-EGA index");
        }
        portable_db_record_free(&record);
    }

    for (life_id = 15; life_id <= 20; ++life_id) {
        PortableDbRecord record = {0};
        uint8_t pixels[PORTABLE_EGA_TILE_PIXELS] = {0};
        size_t frame;
        if (portable_db_load(&db, (int16_t)life_id, 9, &record) != PORTABLE_DB_OK)
            fail("cannot load EMS life pages");
        if (record.size == 0 || record.size % PORTABLE_EGA_LIFE_FRAME_BYTES != 0)
            fail("life page size does not fit the source-derived frame stride");
        for (frame = 0; frame < record.size / PORTABLE_EGA_LIFE_FRAME_BYTES; ++frame)
            if (portable_ega_life_composite(pixels, record.data, record.size,
                                            (uint16_t)frame) != PORTABLE_RENDER_OK)
                fail("actual EMS life frame decode failed");
        portable_db_record_free(&record);
    }
    portable_db_close(&db);
}

int main(int argc, char **argv)
{
    if (argc != 2)
        fail("usage: test_tile_raster <asset-root>");
    synthetic_contract();
    actual_resource_contract(argv[1]);
    puts("tile raster tests passed");
    return 0;
}
