#include "../../game/session.h"
#include "../../game/recovered/engine.h"

#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

#define EFFECT_CAPACITY 4096

typedef struct HeadlessHost {
    int32_t clock;
    PortableWindowRegistry *window_registry;
    SimRecoveredEffect effects[EFFECT_CAPACITY];
    size_t effect_count;
    unsigned query_count[SIM_RECOVERED_QUERY_DOS_KEYBOARD_FLAGS + 1];
    SimRecoveredEngine *engine;
    unsigned snapshot_count;
    unsigned changed_snapshot_count;
} HeadlessHost;

static int host_tick_count(void *context, int32_t *value)
{
    HeadlessHost *host = context;
    *value = host->clock++;
    return 1;
}

static int host_query(void *context, SimRecoveredQuery query,
                      const uintptr_t *arguments, uint8_t argument_count,
                      int32_t *value)
{
    HeadlessHost *host = context;
    if (query <= 0 || query > SIM_RECOVERED_QUERY_DOS_KEYBOARD_FLAGS)
        return 0;
    ++host->query_count[query];
    if (query == SIM_RECOVERED_QUERY_GET_OBJECT_RECT) {
        PortableWindowRect rect;
        uint16_t object;
        int16_t *source_rect;
        if (arguments == NULL || argument_count != 2 ||
            host->window_registry == NULL)
            return 0;
        object = (uint16_t)arguments[0];
        source_rect = (int16_t *)arguments[1];
        if (source_rect == NULL ||
            portable_window_registry_get_object_rect(host->window_registry,
                object, &rect) != PORTABLE_WINDOW_REGISTRY_OK)
            return 0;
        source_rect[0] = rect.left;
        source_rect[1] = rect.top;
        source_rect[2] = rect.right;
        source_rect[3] = rect.bottom;
        *value = 1;
        return 1;
    }
    if (query == SIM_RECOVERED_QUERY_GET_EVENT &&
        (arguments == NULL || argument_count != 1))
        return 0;
    if ((query == SIM_RECOVERED_QUERY_WINDOW_OPEN ||
         query == SIM_RECOVERED_QUERY_WINDOW_IN_FRONT) &&
        (arguments == NULL || argument_count != 1))
        return 0;
    /* The diagnostic starts with all optional UI windows closed and no input. */
    *value = 0;
    return 1;
}

static int host_effect(void *context, const SimRecoveredEffect *effect)
{
    HeadlessHost *host = context;
    static RecoveredState snapshot;
    if (host->effect_count >= EFFECT_CAPACITY)
        return 0;
    host->effects[host->effect_count++] = *effect;
    if (host->engine != NULL) {
        if (!sim_recovered_engine_snapshot(host->engine, &snapshot))
            return 0;
        ++host->snapshot_count;
        if (memcmp(&snapshot, &host->engine->recovered, sizeof snapshot) != 0)
            ++host->changed_snapshot_count;
    }
    /* The test host synchronously captures and acknowledges typed intents. It
     * intentionally provides no SDL rendering or real modal interaction. */
    return 1;
}

static int host_song_done(void *context)
{
    (void)context;
    return 1;
}

int main(void)
{
    static SimSession session = SIM_SESSION_INITIALIZER;
    static SimRecoveredEngine engine;
    PortableDatabase window_database = { 0 };
    PortableWindowRegistry window_registry = { 0 };
    const SimNewGameConfig config = { 1, 0, 11, 8 };
    HeadlessHost host_state = { 0 };
    SimRecoveredHost host = { 0 };
    SimNestRequest nest_clock = { { 1000, 1001 }, 2 };
    SimRecoveredEngineStatus engine_status;
    int16_t key_handled;
    unsigned tick;

    assert(portable_db_open(&window_database, "assets/HCEGANT") ==
           PORTABLE_DB_OK);
    assert(portable_window_registry_init(&window_registry, &window_database,
                                         0) == PORTABLE_WINDOW_REGISTRY_OK);
    host_state.window_registry = &window_registry;
    assert(sim_session_init(&session, "assets", &window_database,
                            &window_registry) == SIM_SESSION_OK);
    assert(sim_session_seed_startup(&session, 0x5a31u, 0x12345678u) ==
           SIM_SESSION_OK);
    assert(sim_session_new_game(&session, &config) == SIM_SESSION_OK);
    assert(portable_window_registry_recalculate(&window_registry, 0, NULL) ==
           PORTABLE_WINDOW_REGISTRY_OK);

    host.context = &host_state;
    host.tick_count = host_tick_count;
    host.query = host_query;
    host.effect = host_effect;
    host.song_done = host_song_done;
    host.audio_driver_ready = 1;
    host.screen_width = 640;
    host.hardware_profile = (uint8_t)window_registry.profile_id;
    {
        SimRecoveredEngineInitStatus init_status =
            sim_recovered_engine_init(&engine, &session, &host);
        if (init_status != SIM_RECOVERED_ENGINE_INIT_OK) {
            fprintf(stderr, "engine initialization failed: %d\n", init_status);
            sim_session_close(&session);
            portable_window_registry_destroy(&window_registry);
            portable_db_close(&window_database);
            return 1;
        }
    }
    host_state.engine = &engine;

    for (tick = 0; tick < 32; ++tick) {
        engine_status = sim_recovered_engine_tick(&engine, &nest_clock);
        if (engine_status != SIM_RECOVERED_ENGINE_OK) {
            fprintf(stderr, "engine stopped at tick %u: %s (%s)\n", tick,
                    sim_recovered_engine_status_string(engine_status),
                    engine.failed_service != NULL ? engine.failed_service :
                                                    "unknown");
            sim_session_close(&session);
            portable_window_registry_destroy(&window_registry);
            portable_db_close(&window_database);
            return 1;
        }
    }
    assert(engine.completed_ticks == 32);
    assert(session.new_game_ready);
    assert(sim_recovered_engine_action(&engine, SIM_RECOVERED_ACTION_SPEED,
                                      2, 0) == SIM_RECOVERED_ENGINE_OK);
    assert(engine.recovered.fd_3D57_07CC[0] == 2);
    engine_status = sim_recovered_engine_action(&engine,
                                      SIM_RECOVERED_ACTION_PAUSE, 1, 0);
    if (engine_status != SIM_RECOVERED_ENGINE_OK) {
        fprintf(stderr, "pause action failed: %s (%s)\n",
                sim_recovered_engine_status_string(engine_status),
                engine.failed_service != NULL ? engine.failed_service : "unknown");
        return 1;
    }
    assert(engine.recovered.fd_50F6_047E == 1);
    assert(sim_recovered_engine_action(&engine, SIM_RECOVERED_ACTION_PAN,
                                      session.world.me_x,
                                      session.world.me_y) ==
           SIM_RECOVERED_ENGINE_OK);
    /* The source's 16.16 DDA truncates the minor axis for this startup path. */
    assert(engine.recovered.fd_50F6_0508[0] == 20);
    assert(engine.recovered.fd_50F6_0508[1] == 3);
    engine_status = sim_recovered_engine_action(&engine,
                                      SIM_RECOVERED_ACTION_MAP_PLANE, 2, 0);
    if (engine_status != SIM_RECOVERED_ENGINE_OK) {
        fprintf(stderr, "map-plane action failed: %s (%s)\n",
                sim_recovered_engine_status_string(engine_status),
                engine.failed_service != NULL ? engine.failed_service : "unknown");
        return 1;
    }
    assert(engine.recovered.MapPlane == 2);
    assert(session.world.selected_map_plane == 2);
    {
        SimRecoveredEvent event = {
            0x0102, 1, 0x42, 0x2000, 0, 0, 0x0102, 0
        };
        event.h = (int16_t)(engine.recovered.fd_50F6_110C.left +
            (39 - engine.recovered.fd_50F6_0508[0]) *
                engine.recovered.fd_55B3_19BE);
        event.v = (int16_t)(engine.recovered.fd_50F6_110C.top +
            (18 - engine.recovered.fd_50F6_0508[1]) *
                engine.recovered.fd_55B3_19C0);
        engine_status = sim_recovered_engine_process_edit_event(
            &engine, &event, &nest_clock);
        if (engine_status != SIM_RECOVERED_ENGINE_OK) {
            fprintf(stderr, "processEdit failed: %s (%s)\n",
                    sim_recovered_engine_status_string(engine_status),
                    engine.failed_service != NULL ? engine.failed_service : "unknown");
            return 1;
        }
        assert(engine.recovered.fd_50F6_0AA0 == 1);
        assert(engine.recovered.fd_50F6_0A8E == 2);
        assert(engine.recovered.fd_50F6_0AD6 == 39);
        assert(engine.recovered.fd_50F6_0AE8 == 18);
        assert(engine.recovered.fd_50F6_0D6C == -2);
    }
    {
        size_t effect_count = host_state.effect_count;
        int16_t scroll_y = engine.recovered.fd_50F6_0508[1];
        assert(sim_recovered_engine_action(&engine,
                    SIM_RECOVERED_ACTION_SCROLL, 5, 0) ==
               SIM_RECOVERED_ENGINE_OK);
        assert(engine.recovered.fd_50F6_0508[0] == 25);
        assert(engine.recovered.fd_50F6_0508[1] == scroll_y);
        assert(host_state.effect_count == ++effect_count);
        assert(sim_recovered_engine_action(&engine,
                    SIM_RECOVERED_ACTION_SCROLL, 1, 0) ==
               SIM_RECOVERED_ENGINE_OK);
        assert(engine.recovered.fd_50F6_0508[0] == 26);
        assert(engine.recovered.fd_50F6_0508[1] == scroll_y);
        assert(host_state.effect_count == ++effect_count);
        assert(sim_recovered_engine_action(&engine,
                    SIM_RECOVERED_ACTION_SCROLL, 3, 5) ==
               SIM_RECOVERED_ENGINE_OK);
        assert(engine.recovered.fd_50F6_0508[0] == 28);
        assert(engine.recovered.fd_50F6_0508[1] == scroll_y + 5);
        assert(host_state.effect_count == ++effect_count);
        assert(sim_recovered_engine_action(&engine,
                    SIM_RECOVERED_ACTION_SCROLL, 0, 0) ==
               SIM_RECOVERED_ENGINE_OK);
        assert(engine.recovered.fd_50F6_0508[0] == 28);
        assert(engine.recovered.fd_50F6_0508[1] == scroll_y + 5);
        assert(host_state.effect_count == effect_count);
        assert(sim_recovered_engine_action(&engine,
                    SIM_RECOVERED_ACTION_SCROLL, 100, 100) ==
               SIM_RECOVERED_ENGINE_OK);
        assert(engine.recovered.fd_50F6_0508[0] ==
               64 - engine.recovered.fd_50F6_10E0);
        assert(engine.recovered.fd_50F6_0508[1] ==
               64 - engine.recovered.fd_50F6_10DE);
        assert(host_state.effect_count == ++effect_count);
    }
    engine_status = sim_recovered_engine_yellow_command_key(
        &engine, '0', &nest_clock, &key_handled);
    if (engine_status != SIM_RECOVERED_ENGINE_OK) {
        fprintf(stderr, "YellowCommandKey failed: %s (%s)\n",
                sim_recovered_engine_status_string(engine_status),
                engine.failed_service != NULL ? engine.failed_service : "unknown");
        return 1;
    }
    assert(key_handled == 1);
    assert(host_state.query_count[SIM_RECOVERED_QUERY_DOS_KEYBOARD_FLAGS] > 0);
    assert(host_state.snapshot_count != 0);
    assert(host_state.changed_snapshot_count != 0);
    printf("actual session/core integration: %u ticks, %zu captured effects, "
           "%u window-open queries, %u snapshots (%u in-flight), actions passed\n", tick,
           host_state.effect_count,
           host_state.query_count[SIM_RECOVERED_QUERY_WINDOW_OPEN],
           host_state.snapshot_count, host_state.changed_snapshot_count);

    sim_session_close(&session);
    portable_window_registry_destroy(&window_registry);
    portable_db_close(&window_database);
    return 0;
}
