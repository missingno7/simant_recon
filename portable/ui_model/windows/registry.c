#include "registry.h"

#include <string.h>

enum {
    WINDOW_CATALOG_ID = 0x80,
    WINDOW_PURGE_ID = 0x83,
    PROFILE_KIND = 9,
    WINDOW_KIND = 0,
    CATALOG_MIN_SIZE = 6,
    PURGE_BYTES = 0x28,
    PROFILE_BYTES = 0x140
};

static uint16_t read_le16(const uint8_t *p)
{
    return (uint16_t)((uint16_t)p[0] | ((uint16_t)p[1] << 8));
}

static int is_missing(PortableDbStatus status)
{
    return status == PORTABLE_DB_NOT_FOUND;
}

static void initialize_empty_profile(PortableWindowRegistry *registry)
{
    size_t i;
    for (i = 0; i < PORTABLE_WINDOW_REGISTRY_SLOTS; ++i) {
        registry->slots[i].window.rect = (PortableWindowRect){
            (int16_t)0x8000, (int16_t)0x8000,
            (int16_t)0x8000, (int16_t)0x8000
        };
    }
}

static PortableWindowRegistryStatus load_owned(PortableWindowRegistry *registry,
                                                int16_t id,
                                                int16_t kind,
                                                PortableDbRecord *record,
                                                int allow_missing)
{
    PortableDbStatus status = portable_db_load(registry->database, id, kind, record);
    if (status == PORTABLE_DB_OK) return PORTABLE_WINDOW_REGISTRY_OK;
    if (allow_missing && is_missing(status)) return PORTABLE_WINDOW_REGISTRY_NOT_FOUND;
    return PORTABLE_WINDOW_REGISTRY_DATABASE_ERROR;
}

static PortableWindowRegistryStatus initialize_window_slot(
    PortableWindowRegistry *registry,
    int16_t window_id,
    int count_as_preloaded)
{
    PortableWindowRegistrySlot *slot;
    PortableDbStatus db_status;
    PortableWindowStatus status;
    size_t i;

    if (window_id < 0 || window_id >= PORTABLE_WINDOW_REGISTRY_SLOTS)
        return PORTABLE_WINDOW_REGISTRY_NOT_FOUND;
    slot = &registry->slots[window_id];
    if (slot->loaded) return PORTABLE_WINDOW_REGISTRY_OK;

    db_status = portable_db_load(registry->database, window_id, WINDOW_KIND,
                                 &slot->record);
    if (db_status == PORTABLE_DB_NOT_FOUND)
        return PORTABLE_WINDOW_REGISTRY_NOT_FOUND;
    if (db_status != PORTABLE_DB_OK)
        return PORTABLE_WINDOW_REGISTRY_DATABASE_ERROR;

    status = portable_window_decode(&slot->record, &slot->window);
    if (status != PORTABLE_WINDOW_OK) {
        portable_db_record_free(&slot->record);
        return PORTABLE_WINDOW_REGISTRY_WINDOW_ERROR;
    }

    if (registry->profile_available) {
        status = portable_window_apply_origin_profile(
            &slot->window, registry->profile_record.data,
            registry->profile_record.size);
        if (status != PORTABLE_WINDOW_OK) {
            portable_window_release(&slot->window);
            portable_db_record_free(&slot->record);
            return PORTABLE_WINDOW_REGISTRY_WINDOW_ERROR;
        }
    }

    /* win_LoadWindow copies object zero's current rectangle into the header. */
    slot->window.rect = slot->window.objects[0].rect;

    /* Model win_LoadWindow's runtime pointer/state initialization in its owned
     * record copy. The trailing source strings are kept intact. */
    for (i = 0; i < slot->window.count; ++i) {
        PortableWindowObject *object = &slot->window.objects[i];
        uint8_t *runtime = (uint8_t *)object->resource_bytes;
        if (object->type == 4) {
            if (object->resource_size < 0x38u) {
                portable_window_release(&slot->window);
                portable_db_record_free(&slot->record);
                return PORTABLE_WINDOW_REGISTRY_WINDOW_ERROR;
            }
            memset(runtime + 0x2a, 0, 14);
        } else if (object->type == 16 || object->type == 17 ||
                   object->type == 18) {
            if (object->resource_size < 0x2eu) {
                portable_window_release(&slot->window);
                portable_db_record_free(&slot->record);
                return PORTABLE_WINDOW_REGISTRY_WINDOW_ERROR;
            }
            memset(runtime + 0x2a, 0, 4);
        }
    }

    slot->loaded = 1;
    if (count_as_preloaded) ++registry->preloaded_count;
    return PORTABLE_WINDOW_REGISTRY_OK;
}

PortableWindowRegistryStatus portable_window_registry_init(
    PortableWindowRegistry *registry,
    PortableDatabase *database,
    int16_t profile_id)
{
    PortableDbStatus db_status;
    PortableWindowRegistryStatus status;
    uint16_t i;

    if (registry == NULL || database == NULL || database->entries == NULL ||
        profile_id < 0)
        return PORTABLE_WINDOW_REGISTRY_BAD_ARGUMENT;
    memset(registry, 0, sizeof(*registry));
    registry->database = database;
    registry->profile_id = profile_id;
    initialize_empty_profile(registry);

    db_status = portable_db_load(database, WINDOW_CATALOG_ID, WINDOW_KIND,
                                 &registry->catalog_record);
    if (db_status != PORTABLE_DB_OK ||
        registry->catalog_record.size < CATALOG_MIN_SIZE) {
        portable_window_registry_destroy(registry);
        return db_status == PORTABLE_DB_OK
                   ? PORTABLE_WINDOW_REGISTRY_INVALID_CATALOG
                   : PORTABLE_WINDOW_REGISTRY_DATABASE_ERROR;
    }
    registry->window_count = read_le16(registry->catalog_record.data);
    registry->color_count = read_le16(registry->catalog_record.data + 2);
    registry->group_count = read_le16(registry->catalog_record.data + 4);
    if (registry->window_count > PURGE_BYTES ||
        registry->window_count > PORTABLE_WINDOW_REGISTRY_SLOTS) {
        portable_window_registry_destroy(registry);
        return PORTABLE_WINDOW_REGISTRY_INVALID_CATALOG;
    }

    db_status = portable_db_load(database, WINDOW_PURGE_ID, WINDOW_KIND,
                                 &registry->purge_record);
    if (db_status != PORTABLE_DB_OK ||
        registry->purge_record.size < PURGE_BYTES) {
        portable_window_registry_destroy(registry);
        return db_status == PORTABLE_DB_OK
                   ? PORTABLE_WINDOW_REGISTRY_INVALID_CATALOG
                   : PORTABLE_WINDOW_REGISTRY_DATABASE_ERROR;
    }

    status = load_owned(registry, profile_id, PROFILE_KIND,
                        &registry->profile_record, 1);
    if (status == PORTABLE_WINDOW_REGISTRY_OK) {
        if (registry->profile_record.size < PROFILE_BYTES) {
            portable_window_registry_destroy(registry);
            return PORTABLE_WINDOW_REGISTRY_INVALID_CATALOG;
        }
        registry->profile_available = 1;
    } else if (status != PORTABLE_WINDOW_REGISTRY_NOT_FOUND) {
        portable_window_registry_destroy(registry);
        return status;
    }

    registry->initialized = 1;
    for (i = 0; i < registry->window_count; ++i) {
        if (registry->purge_record.data[i] == 0) {
            status = initialize_window_slot(registry, (int16_t)i, 1);
            if (status != PORTABLE_WINDOW_REGISTRY_OK) {
                portable_window_registry_destroy(registry);
                return status;
            }
        }
    }
    return PORTABLE_WINDOW_REGISTRY_OK;
}

void portable_window_registry_destroy(PortableWindowRegistry *registry)
{
    size_t i;
    if (registry == NULL) return;
    for (i = 0; i < PORTABLE_WINDOW_REGISTRY_SLOTS; ++i) {
        PortableWindowRegistrySlot *slot = &registry->slots[i];
        if (slot->loaded) portable_window_release(&slot->window);
        portable_db_record_free(&slot->record);
    }
    portable_db_record_free(&registry->profile_record);
    portable_db_record_free(&registry->catalog_record);
    portable_db_record_free(&registry->purge_record);
    memset(registry, 0, sizeof(*registry));
}

PortableWindowRegistryStatus portable_window_registry_load(
    PortableWindowRegistry *registry,
    int16_t window_id)
{
    if (registry == NULL || !registry->initialized || window_id < 0 ||
        window_id >= PORTABLE_WINDOW_REGISTRY_SLOTS)
        return PORTABLE_WINDOW_REGISTRY_BAD_ARGUMENT;
    return initialize_window_slot(registry, window_id, 0);
}

PortableWindowRegistryStatus portable_window_registry_recalculate(
    PortableWindowRegistry *registry,
    int16_t window_id,
    const int16_t window_args[4])
{
    PortableWindowRegistryStatus load_status;
    PortableWindowStatus status;

    load_status = portable_window_registry_load(registry, window_id);
    if (load_status != PORTABLE_WINDOW_REGISTRY_OK) return load_status;
    status = portable_window_recalculate(&registry->slots[window_id].window,
                                         window_args);
    if (status == PORTABLE_WINDOW_UNSUPPORTED_CONSTRAINT)
        return PORTABLE_WINDOW_REGISTRY_UNSUPPORTED_GEOMETRY;
    if (status != PORTABLE_WINDOW_OK)
        return PORTABLE_WINDOW_REGISTRY_WINDOW_ERROR;
    registry->slots[window_id].recalculated = 1;
    return PORTABLE_WINDOW_REGISTRY_OK;
}

PortableWindowRegistryStatus portable_window_registry_get_object_rect(
    PortableWindowRegistry *registry,
    uint16_t object_id,
    PortableWindowRect *rect)
{
    int16_t window_id;
    uint8_t object_index;
    PortableWindowRegistryStatus status;
    PortableWindowRegistrySlot *slot;

    if (registry == NULL || !registry->initialized || rect == NULL)
        return PORTABLE_WINDOW_REGISTRY_BAD_ARGUMENT;
    window_id = (int16_t)(object_id >> 8);
    object_index = (uint8_t)object_id;
    status = portable_window_registry_load(registry, window_id);
    if (status != PORTABLE_WINDOW_REGISTRY_OK) return status;
    slot = &registry->slots[window_id];
    if (object_index >= slot->window.count)
        return PORTABLE_WINDOW_REGISTRY_OBJECT_OUT_OF_RANGE;
    *rect = slot->window.objects[object_index].rect;
    return PORTABLE_WINDOW_REGISTRY_OK;
}

const char *portable_window_registry_status_string(
    PortableWindowRegistryStatus status)
{
    switch (status) {
    case PORTABLE_WINDOW_REGISTRY_OK: return "ok";
    case PORTABLE_WINDOW_REGISTRY_BAD_ARGUMENT: return "bad argument";
    case PORTABLE_WINDOW_REGISTRY_DATABASE_ERROR: return "database load failed";
    case PORTABLE_WINDOW_REGISTRY_INVALID_CATALOG: return "invalid window catalog";
    case PORTABLE_WINDOW_REGISTRY_WINDOW_ERROR: return "invalid window resource";
    case PORTABLE_WINDOW_REGISTRY_NOT_FOUND: return "window resource not found";
    case PORTABLE_WINDOW_REGISTRY_NOT_LOADED: return "window resource not loaded";
    case PORTABLE_WINDOW_REGISTRY_OBJECT_OUT_OF_RANGE: return "window object out of range";
    case PORTABLE_WINDOW_REGISTRY_UNSUPPORTED_GEOMETRY:
        return "window geometry requires an unsupported DOS dependency";
    }
    return "unknown window registry error";
}
