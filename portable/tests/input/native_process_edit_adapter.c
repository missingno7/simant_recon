#include "../../game/recovered/engine.h"
#include "../../game/session.h"

#include <stddef.h>
#include <stdint.h>
#include <string.h>

#define QUERY_CAPACITY 64

typedef struct SimEditBoundaryEvent {
    int32_t kind; /* 1=host query, 2=TickCount */
    int32_t id;
    int32_t argument_count;
    int32_t result;
    uintptr_t arguments[2];
} SimEditBoundaryEvent;

typedef struct SimEditProbeMeta {
    size_t recovered_size;
    int32_t engine_status;
    int32_t host_status;
    int32_t tick_start;
    int32_t tick_end;
    uint32_t query_count;
    uint32_t effect_count;
    uint32_t s_rng_before;
    uint32_t s_rng_after;
    uint32_t c_rng_before;
    uint32_t c_rng_after;
    int32_t query_ids[QUERY_CAPACITY];
    int16_t event_words[8];
    uint32_t boundary_count;
    SimEditBoundaryEvent boundary[QUERY_CAPACITY];
} SimEditProbeMeta;

typedef struct SimEditProbeHost {
    int32_t clock;
    uint32_t query_count;
    uint32_t effect_count;
    int32_t query_ids[QUERY_CAPACITY];
    SimEditProbeMeta *meta;
    PortableWindowRegistry *registry;
} SimEditProbeHost;

typedef struct SimEditFieldLayout {
    const char *name;
    size_t offset;
    size_t size;
} SimEditFieldLayout;

extern const SimEditFieldLayout *sim_edit_field_layout(size_t *count);

static int probe_tick(void *context, int32_t *value)
{
    SimEditProbeHost *host = (SimEditProbeHost *)context;
    *value = host->clock++;
    if (host->meta->boundary_count < QUERY_CAPACITY) {
        SimEditBoundaryEvent *event =
            &host->meta->boundary[host->meta->boundary_count++];
        memset(event, 0, sizeof *event);
        event->kind = 2;
        event->result = *value;
    }
    return 1;
}

static int probe_query(void *context, SimRecoveredQuery query,
                       const uintptr_t *arguments, uint8_t argument_count,
                       int32_t *value)
{
    SimEditProbeHost *host = (SimEditProbeHost *)context;
    SimEditBoundaryEvent *event = NULL;
    if (host->query_count < QUERY_CAPACITY)
        host->query_ids[host->query_count++] = (int32_t)query;
    if (host->meta->boundary_count < QUERY_CAPACITY) {
        event = &host->meta->boundary[host->meta->boundary_count++];
        memset(event, 0, sizeof *event);
        event->kind = 1;
        event->id = (int32_t)query;
        event->argument_count = argument_count > 2 ? 2 : argument_count;
        if (arguments != NULL)
            for (int i = 0; i < event->argument_count; ++i)
                event->arguments[i] = arguments[i];
    }
    switch (query) {
    case SIM_RECOVERED_QUERY_WINDOW_IN_FRONT:
        if (arguments == NULL || argument_count != 1)
            return 0;
        *value = 1;
        break;
    case SIM_RECOVERED_QUERY_GET_EVENT:
        if (arguments == NULL || argument_count != 1)
            return 0;
        *value = 0;
        break;
    case SIM_RECOVERED_QUERY_BUTTON:
    case SIM_RECOVERED_QUERY_STILL_DOWN:
        *value = 0;
        break;
    case SIM_RECOVERED_QUERY_DOS_KEYBOARD_FLAGS:
        *value = 0x03;
        break;
    case SIM_RECOVERED_QUERY_GET_OBJECT_RECT: {
        PortableWindowRect rect;
        uint16_t object;
        int16_t *out;
        if (arguments == NULL || argument_count != 2 || host->registry == NULL)
            return 0;
        object = (uint16_t)arguments[0];
        out = (int16_t *)arguments[1];
        if (out == NULL || portable_window_registry_get_object_rect(
                host->registry, object, &rect) != PORTABLE_WINDOW_REGISTRY_OK)
            return 0;
        out[0] = rect.left;
        out[1] = rect.top;
        out[2] = rect.right;
        out[3] = rect.bottom;
        *value = 1;
        break;
    }
    default:
        *value = 0;
        break;
    }
    if (event != NULL)
        event->result = *value;
    return 1;
}

static int probe_effect(void *context, const SimRecoveredEffect *effect)
{
    SimEditProbeHost *host = (SimEditProbeHost *)context;
    if (effect == NULL)
        return 0;
    ++host->effect_count;
    return 1;
}

static int probe_song_done(void *context)
{
    (void)context;
    return 1;
}

size_t sim_edit_probe_state_size(void)
{
    return sizeof(RecoveredState);
}

const SimEditFieldLayout *sim_edit_probe_fields(size_t *count)
{
    return sim_edit_field_layout(count);
}

int sim_native_process_edit_probe(int16_t map_plane,
                                  int16_t target_x, int16_t target_y,
                                  uint8_t *before, uint8_t *after,
                                  size_t state_capacity,
                                  SimEditProbeMeta *meta)
{
    static SimSession session;
    static SimRecoveredEngine engine;
    PortableDatabase window_database = { 0 };
    PortableWindowRegistry window_registry = { 0 };
    SimEditProbeHost host_state = { 0 };
    SimRecoveredHost host = { 0 };
    SimNestRequest nest_clock = { { 1000, 1001 }, 2 };
    SimRecoveredEvent event;
    SimRecoveredEngineInitStatus init_status;
    SimRecoveredEngineStatus call_status;
    SimNewGameConfig config = { 1, 0, 11, 8 };
    size_t state_size = sizeof(RecoveredState);
    int result = 0;

    if (before == NULL || after == NULL || meta == NULL ||
        state_capacity < state_size)
        return -1;
    memset(&session, 0, sizeof session);
    memset(&engine, 0, sizeof engine);
    memset(&host_state, 0, sizeof host_state);
    memset(meta, 0, sizeof *meta);
    host_state.clock = 100;

    if (portable_db_open(&window_database, "assets/HCEGANT") != PORTABLE_DB_OK)
        goto cleanup;
    if (portable_window_registry_init(&window_registry, &window_database, 0) !=
        PORTABLE_WINDOW_REGISTRY_OK)
        goto cleanup;
    host_state.registry = &window_registry;
    if (sim_session_init(&session, "assets", &window_database,
                         &window_registry) != SIM_SESSION_OK)
        goto cleanup;
    if (sim_session_seed_startup(&session, 0x5a31u, 0x12345678u) !=
        SIM_SESSION_OK)
        goto cleanup;
    if (sim_session_new_game(&session, &config) != SIM_SESSION_OK)
        goto cleanup;
    if (portable_window_registry_recalculate(&window_registry, 0, NULL) !=
        PORTABLE_WINDOW_REGISTRY_OK)
        goto cleanup;

    host.context = &host_state;
    host_state.meta = meta;
    host.tick_count = probe_tick;
    host.query = probe_query;
    host.effect = probe_effect;
    host.song_done = probe_song_done;
    host.audio_driver_ready = 1;
    host.screen_width = 640;
    host.hardware_profile = (uint8_t)window_registry.profile_id;
    init_status = sim_recovered_engine_init(&engine, &session, &host);
    if (init_status != SIM_RECOVERED_ENGINE_INIT_OK)
        goto cleanup;
    if (sim_recovered_engine_action(&engine, SIM_RECOVERED_ACTION_MAP_PLANE,
                                    map_plane, 0) != SIM_RECOVERED_ENGINE_OK)
        goto cleanup;
    host_state.query_count = 0;
    host_state.effect_count = 0;
    meta->boundary_count = 0;
    memset(meta->boundary, 0, sizeof meta->boundary);
    host_state.clock = 100;

    memcpy(before, &engine.recovered, state_size);
    meta->s_rng_before = session.rng.s_state;
    meta->c_rng_before = session.rng.c_state;
    event.what = 0;
    event.message = 0x0003;
    event.x4 = 0x0007;
    event.modifiers = 0x0201;
    event.h = (int16_t)(engine.recovered.fd_50F6_110C.left +
        (target_x - engine.recovered.fd_50F6_0508[0]) *
            engine.recovered.fd_55B3_19BE);
    event.v = (int16_t)(engine.recovered.fd_50F6_110C.top +
        (target_y - engine.recovered.fd_50F6_0508[1]) *
            engine.recovered.fd_55B3_19C0);
    event.code = 4;
    event.xE = 0x0101;
    meta->event_words[0] = event.what;
    meta->event_words[1] = event.message;
    meta->event_words[2] = event.x4;
    meta->event_words[3] = event.modifiers;
    meta->event_words[4] = event.h;
    meta->event_words[5] = event.v;
    meta->event_words[6] = event.code;
    meta->event_words[7] = event.xE;
    meta->tick_start = host_state.clock;
    call_status = sim_recovered_engine_process_edit_event(
        &engine, &event, &nest_clock);
    meta->tick_end = host_state.clock;
    memcpy(after, &engine.recovered, state_size);
    meta->s_rng_after = session.rng.s_state;
    meta->c_rng_after = session.rng.c_state;
    meta->engine_status = (int32_t)call_status;
    meta->host_status = (int32_t)engine.status;
    meta->recovered_size = state_size;
    meta->query_count = host_state.query_count;
    meta->effect_count = host_state.effect_count;
    memcpy(meta->query_ids, host_state.query_ids,
           sizeof meta->query_ids);
    result = call_status == SIM_RECOVERED_ENGINE_OK ? 0 : 1;

cleanup:
    if (session.shared_open || session.tileset_open)
        sim_session_close(&session);
    if (window_registry.initialized)
        portable_window_registry_destroy(&window_registry);
    if (window_database.index_file != NULL)
        portable_db_close(&window_database);
    return result;
}
