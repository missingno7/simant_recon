#ifndef SIMANT_PORTABLE_UI_MODEL_WINDOWS_REGISTRY_H
#define SIMANT_PORTABLE_UI_MODEL_WINDOWS_REGISTRY_H

#include "window.h"

#include <stdint.h>

enum { PORTABLE_WINDOW_REGISTRY_SLOTS = 45 };

typedef enum PortableWindowRegistryStatus {
    PORTABLE_WINDOW_REGISTRY_OK = 0,
    PORTABLE_WINDOW_REGISTRY_BAD_ARGUMENT,
    PORTABLE_WINDOW_REGISTRY_DATABASE_ERROR,
    PORTABLE_WINDOW_REGISTRY_INVALID_CATALOG,
    PORTABLE_WINDOW_REGISTRY_WINDOW_ERROR,
    PORTABLE_WINDOW_REGISTRY_NOT_FOUND,
    PORTABLE_WINDOW_REGISTRY_NOT_LOADED,
    PORTABLE_WINDOW_REGISTRY_OBJECT_OUT_OF_RANGE,
    PORTABLE_WINDOW_REGISTRY_UNSUPPORTED_GEOMETRY
} PortableWindowRegistryStatus;

typedef struct PortableWindowRegistrySlot {
    PortableDbRecord record;
    PortableWindowResource window;
    uint8_t loaded;
    uint8_t recalculated;
} PortableWindowRegistrySlot;

/*
 * Startup registry matching root win_LoadAllWindows:
 *  - borrows `database`, which must outlive this registry;
 *  - owns every loaded record and decoded window until destroy;
 *  - preloads purge-list zero entries and applies the selected kind-9 profile;
 *  - get_object_rect lazily loads a requested valid window, then returns its
 *    current loaded coordinates (it does not implicitly call win_Recalc);
 *  - recalculate is an explicit win_Recalc equivalent and reports unsupported
 *    autosize/cross-window constraints instead of inventing dimensions.
 */
typedef struct PortableWindowRegistry {
    PortableDatabase *database; /* Borrowed. */
    PortableDbRecord profile_record;
    PortableDbRecord catalog_record;
    PortableDbRecord purge_record;
    PortableWindowRegistrySlot slots[PORTABLE_WINDOW_REGISTRY_SLOTS];
    uint16_t window_count;
    uint16_t color_count;
    uint16_t group_count;
    uint16_t preloaded_count;
    int16_t profile_id;
    uint8_t profile_available;
    uint8_t initialized;
} PortableWindowRegistry;

PortableWindowRegistryStatus portable_window_registry_init(
    PortableWindowRegistry *registry,
    PortableDatabase *database,
    int16_t profile_id);
void portable_window_registry_destroy(PortableWindowRegistry *registry);
PortableWindowRegistryStatus portable_window_registry_load(
    PortableWindowRegistry *registry,
    int16_t window_id);
PortableWindowRegistryStatus portable_window_registry_recalculate(
    PortableWindowRegistry *registry,
    int16_t window_id,
    const int16_t window_args[4]);
PortableWindowRegistryStatus portable_window_registry_get_object_rect(
    PortableWindowRegistry *registry,
    uint16_t object_id,
    PortableWindowRect *rect);
const char *portable_window_registry_status_string(
    PortableWindowRegistryStatus status);

#endif
