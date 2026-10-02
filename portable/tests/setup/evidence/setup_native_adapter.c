#include "../../../game/simulation/setup.h"
#include "../../../render/bitmap.h"
#include "../../../ui_model/windows/registry.h"

#include <string.h>

static PortableDatabase database;
static PortableWindowRegistry registry;
static SimSetupControls controls;
static int ready;
static int events[8];
static size_t event_count;

static int append_event(int value)
{
    if (event_count < sizeof(events) / sizeof(events[0]))
        events[event_count++] = value;
    return 1;
}

static int resource_size(void *context, uint16_t object_id, uint16_t kind,
                         int16_t *width, int16_t *height)
{
    PortableDbRecord record;
    PortableBitmap bitmap;
    PortableDbStatus db_status;
    PortableRenderStatus render_status;
    uint8_t *decoded = NULL;
    size_t decoded_size = 0;
    const uint8_t *bytes;
    size_t size;
    int ok = 0;
    (void)context;

    append_event(0x10000 | ((int)object_id << 8) | kind);
    db_status = portable_db_load(&database, (int16_t)object_id,
                                 (int16_t)kind, &record);
    if (db_status != PORTABLE_DB_OK) return 0;
    bytes = record.data;
    size = record.size;
    if (size >= 2 && (bytes[0] == 0xff || bytes[0] == 0x00) &&
        (bytes[1] == 0xff || bytes[1] == 0x80)) {
        render_status = portable_bitmap_decode_packed(bytes, size,
                                                       &decoded, &decoded_size);
        if (render_status != PORTABLE_RENDER_OK) goto done;
        bytes = decoded;
        size = decoded_size;
    }
    render_status = portable_bitmap_view(bytes, size, &bitmap);
    if (render_status == PORTABLE_RENDER_OK && bitmap.width <= 32767 &&
        bitmap.height <= 32767) {
        *width = (int16_t)bitmap.width;
        *height = (int16_t)bitmap.height;
        ok = 1;
    }
done:
    portable_bitmap_release_decoded(decoded);
    portable_db_record_free(&record);
    return ok;
}

static int get_object_rect(void *context, uint16_t object_id,
                           SimSetupRect *rect)
{
    PortableWindowRect source;
    PortableWindowRegistryStatus status;
    (void)context;
    append_event(0x20000 | object_id);
    status = portable_window_registry_get_object_rect(&registry, object_id,
                                                       &source);
    if (status != PORTABLE_WINDOW_REGISTRY_OK) return 0;
    rect->left = source.left;
    rect->top = source.top;
    rect->right = source.right;
    rect->bottom = source.bottom;
    return 1;
}

static int refresh_control(void *context, SimSetupControlKind kind,
                           const SimSetupControls *value)
{
    (void)context;
    (void)value;
    append_event(0x30000 | (int)kind);
    return 1;
}

__declspec(dllexport) int setup_native_init(const char *root, int16_t profile_id)
{
    SimSetupHooks hooks;
    PortableDbStatus db_status;
    PortableWindowRegistryStatus registry_status;
    SimSetupStatus setup_status;
    if (ready) {
        portable_window_registry_destroy(&registry);
        portable_db_close(&database);
        ready = 0;
    }
    memset(&database, 0, sizeof(database));
    memset(&registry, 0, sizeof(registry));
    memset(&controls, 0, sizeof(controls));
    sim_setup_controls_init_data(&controls);
    event_count = 0;
    db_status = portable_db_open(&database, root);
    if (db_status != PORTABLE_DB_OK) return 100 + (int)db_status;
    registry_status = portable_window_registry_init(&registry, &database,
                                                    profile_id);
    if (registry_status != PORTABLE_WINDOW_REGISTRY_OK) {
        portable_db_close(&database);
        return 200 + (int)registry_status;
    }
    ready = 1;
    hooks.resource_size = resource_size;
    hooks.get_object_rect = get_object_rect;
    hooks.refresh_control = refresh_control;
    hooks.context = NULL;
    setup_status = sim_setup_init_controls(&controls, &hooks);
    return (int)setup_status;
}

/* Mutated-state lane for the repeated source initControls contract. values:
 * defaults[0..5], selectors[6..7], then three remaining mode and caste rows
 * (frac/mid/weight each). */
__declspec(dllexport) int setup_native_mutate_reinit(const int32_t *values)
{
    SimSetupHooks hooks;
    unsigned i;
    unsigned at = 8;
    if (!ready || values == NULL || !controls.source_data_initialized)
        return SIM_SETUP_INVALID_ARGUMENT;
    controls.mode_defaults = (SimSetupTriangle){
        (uint16_t)values[0], (uint16_t)values[1], (uint16_t)values[2] };
    controls.caste_defaults = (SimSetupTriangle){
        (uint16_t)values[3], (uint16_t)values[4], (uint16_t)values[5] };
    controls.mode_current = (int16_t)values[6];
    controls.caste_current = (int16_t)values[7];
    for (i = 1; i < 4; ++i, at += 3)
        controls.mode_levels[i] = (SimSetupTriangle){
            (uint16_t)values[at], (uint16_t)values[at + 1],
            (uint16_t)values[at + 2] };
    for (i = 1; i < 4; ++i, at += 3)
        controls.caste_levels[i] = (SimSetupTriangle){
            (uint16_t)values[at], (uint16_t)values[at + 1],
            (uint16_t)values[at + 2] };
    event_count = 0;
    hooks.resource_size = resource_size;
    hooks.get_object_rect = get_object_rect;
    hooks.refresh_control = refresh_control;
    hooks.context = NULL;
    return (int)sim_setup_init_controls(&controls, &hooks);
}

__declspec(dllexport) size_t setup_native_snapshot(int32_t *values,
                                                  size_t capacity)
{
    size_t n = 0;
    size_t i;
#define PUSH(v) do { if (n < capacity && values != NULL) values[n] = (int32_t)(v); ++n; } while (0)
#define PUSH_RECT(r) do { PUSH((r).left); PUSH((r).top); PUSH((r).right); PUSH((r).bottom); } while (0)
#define PUSH_TRI(t) do { PUSH((t).frac); PUSH((t).mid); PUSH((t).weight); } while (0)
    if (!ready) return 0;
    PUSH(controls.knob_width); PUSH(controls.knob_height);
    PUSH(controls.mode_auto); PUSH(controls.caste_auto);
    PUSH(controls.mode_enabled); PUSH(controls.caste_enabled);
    PUSH(controls.mode_current); PUSH(controls.caste_current);
    PUSH(controls.state_0370); PUSH(controls.state_024e);
    PUSH_TRI(controls.mode_level); PUSH_TRI(controls.caste_level);
    for (i = 0; i < 4; ++i) PUSH_TRI(controls.mode_levels[i]);
    for (i = 0; i < 4; ++i) PUSH_TRI(controls.caste_levels[i]);
    for (i = 0; i < 4; ++i) PUSH(controls.ideal_caste[i]);
    PUSH_RECT(controls.mode_rect); PUSH_RECT(controls.caste_rect);
    PUSH(controls.mode_point.x); PUSH(controls.mode_point.y);
    PUSH(controls.caste_point.x); PUSH(controls.caste_point.y);
    PUSH(controls.mode_width); PUSH(controls.mode_height); PUSH(controls.mode_slope);
    PUSH(controls.caste_width); PUSH(controls.caste_height); PUSH(controls.caste_slope);
#undef PUSH_TRI
#undef PUSH_RECT
#undef PUSH
    return n;
}

__declspec(dllexport) size_t setup_native_event_count(void)
{
    return event_count;
}

__declspec(dllexport) int setup_native_event(size_t index)
{
    if (index >= event_count) return -1;
    return events[index];
}

__declspec(dllexport) void setup_native_close(void)
{
    if (!ready) return;
    portable_window_registry_destroy(&registry);
    portable_db_close(&database);
    ready = 0;
}
