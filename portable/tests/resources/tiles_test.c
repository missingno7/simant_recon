#include "../../game/resources/tiles.h"

#include <stdio.h>
#include <string.h>

static int failures;
#define CHECK(expr) do { \
    if (!(expr)) { \
        fprintf(stderr, "FAIL %s:%d: %s\n", __FILE__, __LINE__, #expr); \
        ++failures; \
    } \
} while (0)

static void check_resource(const PortableTileResource *resource,
                           int id,
                           size_t expected_size)
{
    CHECK(resource->record.id == id);
    CHECK(resource->record.kind == 9);
    CHECK(resource->record.size == expected_size);
    CHECK(resource->record.data != NULL);
}

int main(int argc, char **argv)
{
    const char *asset_dir = argc > 1 ? argv[1] : "assets";
    char ndx[512];
    char dat[512];
    PortableDatabase db;
    PortableTileSet tileset;
    PortableDbStatus status;

    (void)snprintf(ndx, sizeof(ndx), "%s/HCEGANT.NDX", asset_dir);
    (void)snprintf(dat, sizeof(dat), "%s/HCEGANT.DAT", asset_dir);
    memset(&db, 0, sizeof(db));
    status = portable_db_open_files(&db, ndx, dat);
    CHECK(status == PORTABLE_DB_OK);
    if (status != PORTABLE_DB_OK) return 1;

    memset(&tileset, 0, sizeof(tileset));
    CHECK(portable_tileset_load(&db, 0, &tileset) == PORTABLE_DB_OK);
    CHECK(tileset.ground_selection == 0);
    check_resource(&tileset.ground_resource, 10, 0x8000);
    check_resource(&tileset.ems_surface[0], 15, 0x5000);
    check_resource(&tileset.ems_surface[1], 16, 0x5000);
    check_resource(&tileset.ems_surface[2], 17, 0x5000);
    check_resource(&tileset.ems_nest[0], 18, 0x5000);
    check_resource(&tileset.ems_nest[1], 19, 0x5000);
    check_resource(&tileset.ems_nest[2], 20, 0x5000);
    portable_tileset_free(&tileset);

    CHECK(portable_tileset_load(&db, 1, &tileset) == PORTABLE_DB_OK);
    CHECK(tileset.ground_selection == 1);
    check_resource(&tileset.ground_resource, 9, 0x8000);
    check_resource(&tileset.ems_surface[0], 15, 0x5000);
    check_resource(&tileset.ems_surface[1], 16, 0x5000);
    check_resource(&tileset.ems_surface[2], 17, 0x5000);
    check_resource(&tileset.ems_nest[0], 18, 0x5000);
    check_resource(&tileset.ems_nest[1], 19, 0x5000);
    check_resource(&tileset.ems_nest[2], 20, 0x5000);
    portable_tileset_free(&tileset);

    CHECK(portable_tileset_load(&db, 2, &tileset) == PORTABLE_DB_FORMAT_ERROR);
    CHECK(strcmp(portable_tileset_error(&tileset), "ground selection must be 0 or 1") == 0);
    portable_tileset_free(&tileset);
    portable_db_close(&db);

    if (failures != 0) {
        fprintf(stderr, "%d tile resource test(s) failed\n", failures);
        return 1;
    }
    puts("PASS ground_selections=2 ground_resources=2 surface_chunks=3 nest_chunks=3");
    return 0;
}
