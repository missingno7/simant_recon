#include "tiles.h"

#include <stdio.h>
#include <string.h>

enum {
    TILE_KIND = 9,
    INDEXED_OBJECT_FIRST_SET = 10,
    EMS_OBJECT_FIRST = 15,
    INDEXED_RESOURCE_BYTES = 0x8000,
    EMS_CHUNK_BYTES = 0x5000
};

static void set_error(PortableTileSet *tileset, const char *message)
{
    if (tileset == NULL) return;
    if (message == NULL) message = "";
    (void)snprintf(tileset->error, sizeof(tileset->error), "%s", message);
}

static PortableDbStatus load_resource(PortableDatabase *db,
                                      int16_t id,
                                      PortableTileResource *resource,
                                      size_t expected_size)
{
    PortableDbStatus status = portable_db_load(db, id, TILE_KIND, &resource->record);
    if (status != PORTABLE_DB_OK) return status;
    if (resource->record.size != expected_size) {
        portable_db_record_free(&resource->record);
        return PORTABLE_DB_FORMAT_ERROR;
    }
    return PORTABLE_DB_OK;
}

PortableDbStatus portable_tileset_load(PortableDatabase *db,
                                       int16_t set_index,
                                       PortableTileSet *tileset)
{
    PortableDbStatus status;
    int i;
    int16_t indexed_id;
    int16_t ems_first_id;

    if (tileset == NULL || db == NULL) return PORTABLE_DB_FORMAT_ERROR;
    memset(tileset, 0, sizeof(*tileset));
    if (set_index < 0 || set_index > 1) {
        set_error(tileset, "ground selection must be 0 or 1");
        return PORTABLE_DB_FORMAT_ERROR;
    }
    tileset->ground_selection = set_index;
    indexed_id = (int16_t)(INDEXED_OBJECT_FIRST_SET - set_index);

    status = load_resource(db, indexed_id, &tileset->ground_resource,
                           INDEXED_RESOURCE_BYTES);
    if (status != PORTABLE_DB_OK) {
        set_error(tileset, "cannot load indexed terrain tile resource");
        goto fail;
    }
    for (i = 0; i < 3; ++i) {
        ems_first_id = (int16_t)(EMS_OBJECT_FIRST + i);
        status = load_resource(db, ems_first_id, &tileset->ems_surface[i], EMS_CHUNK_BYTES);
        if (status != PORTABLE_DB_OK) {
            set_error(tileset, "cannot load EMS surface chunk");
            goto fail;
        }
        status = load_resource(db, (int16_t)(ems_first_id + 3),
                               &tileset->ems_nest[i], EMS_CHUNK_BYTES);
        if (status != PORTABLE_DB_OK) {
            set_error(tileset, "cannot load EMS nest chunk");
            goto fail;
        }
    }
    set_error(tileset, "");
    return PORTABLE_DB_OK;

fail:
    portable_tileset_free(tileset);
    /* free clears the structure, so retain the diagnostic after cleanup. */
    set_error(tileset, status == PORTABLE_DB_FORMAT_ERROR
                       ? "terrain tile resource has an unexpected byte length"
                       : "terrain tile resource lookup failed");
    return status;
}

void portable_tileset_free(PortableTileSet *tileset)
{
    int i;
    if (tileset == NULL) return;
    portable_db_record_free(&tileset->ground_resource.record);
    for (i = 0; i < 3; ++i)
        portable_db_record_free(&tileset->ems_surface[i].record);
    for (i = 0; i < 3; ++i)
        portable_db_record_free(&tileset->ems_nest[i].record);
    memset(tileset, 0, sizeof(*tileset));
}

const char *portable_tileset_error(const PortableTileSet *tileset)
{
    return tileset == NULL ? "invalid tile set" : tileset->error;
}
