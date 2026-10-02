#include "../../../ui_model/windows/registry.h"

#include <string.h>

static PortableDatabase active_database;
static PortableWindowRegistry active_registry;
static int active;

__declspec(dllexport) int registry_open(const char *root, int16_t profile_id)
{
    PortableDbStatus db_status;
    PortableWindowRegistryStatus status;
    if (active) {
        portable_window_registry_destroy(&active_registry);
        portable_db_close(&active_database);
        active = 0;
    }
    memset(&active_database, 0, sizeof(active_database));
    memset(&active_registry, 0, sizeof(active_registry));
    db_status = portable_db_open(&active_database, root);
    if (db_status != PORTABLE_DB_OK) return 100 + (int)db_status;
    status = portable_window_registry_init(&active_registry, &active_database,
                                          profile_id);
    if (status != PORTABLE_WINDOW_REGISTRY_OK) {
        portable_db_close(&active_database);
        return (int)status + 20;
    }
    active = 1;
    return 0;
}

__declspec(dllexport) int registry_window_count(void)
{
    return active ? active_registry.window_count : -1;
}

__declspec(dllexport) int registry_preloaded_count(void)
{
    return active ? active_registry.preloaded_count : -1;
}

__declspec(dllexport) int registry_loaded(int16_t window_id)
{
    if (!active || window_id < 0 || window_id >= PORTABLE_WINDOW_REGISTRY_SLOTS)
        return 0;
    return active_registry.slots[window_id].loaded;
}

__declspec(dllexport) int registry_object_count(int16_t window_id)
{
    if (!active || window_id < 0 || window_id >= PORTABLE_WINDOW_REGISTRY_SLOTS ||
        !active_registry.slots[window_id].loaded)
        return -1;
    return active_registry.slots[window_id].window.count;
}

__declspec(dllexport) int registry_recalculate(int16_t window_id)
{
    return (int)portable_window_registry_recalculate(&active_registry,
                                                      window_id, 0);
}

__declspec(dllexport) int registry_object_rect(int16_t window_id,
                                               int16_t object_index,
                                               int16_t *rect)
{
    PortableWindowRect value;
    PortableWindowRegistryStatus status;
    if (!active || rect == 0 || window_id < 0 || window_id >= 45 ||
        object_index < 0 || object_index > 255)
        return 0;
    status = portable_window_registry_get_object_rect(
        &active_registry,
        (uint16_t)(((uint16_t)window_id << 8) | (uint16_t)object_index),
        &value);
    if (status != PORTABLE_WINDOW_REGISTRY_OK) return 0;
    rect[0] = value.left;
    rect[1] = value.top;
    rect[2] = value.right;
    rect[3] = value.bottom;
    return 1;
}

__declspec(dllexport) void registry_close(void)
{
    if (!active) return;
    portable_window_registry_destroy(&active_registry);
    portable_db_close(&active_database);
    active = 0;
}
