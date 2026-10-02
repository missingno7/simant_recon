#include "../../game/session.h"
#include "../../game/recovered/engine.h"

#include <assert.h>
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

enum { EFFECT_CAPACITY = 512 };

typedef struct CapturedEffect {
    SimRecoveredEffectKind kind;
    int64_t args[5];
} CapturedEffect;

typedef struct MenuHost {
    int32_t clock;
    SimRecoveredEngine *engine;
    CapturedEffect effects[EFFECT_CAPACITY];
    size_t effect_count;
    unsigned queries[SIM_RECOVERED_QUERY_DOS_KEYBOARD_FLAGS + 1];
    int try_reentrant;
    int reject_effect;
    SimRecoveredEngineStatus nested_status;
} MenuHost;

static int host_tick(void *context, int32_t *value)
{
    MenuHost *host = context;
    *value = host->clock++;
    return 1;
}

static int host_query(void *context, SimRecoveredQuery query,
                      const uintptr_t *arguments, uint8_t argument_count,
                      int32_t *value)
{
    MenuHost *host = context;
    if (host == NULL || value == NULL || query <= 0 ||
        query > SIM_RECOVERED_QUERY_DOS_KEYBOARD_FLAGS)
        return 0;
    ++host->queries[query];
    if ((query == SIM_RECOVERED_QUERY_WINDOW_OPEN ||
         query == SIM_RECOVERED_QUERY_WINDOW_IN_FRONT) &&
        (arguments == NULL || argument_count != 1))
        return 0;
    if (query == SIM_RECOVERED_QUERY_GET_OBJECT_RECT &&
        (arguments == NULL || argument_count != 2))
        return 0;
    if (query == SIM_RECOVERED_QUERY_GET_EVENT &&
        (arguments == NULL || argument_count != 1))
        return 0;
    *value = 0; /* Explicit controlled headless state: closed/no input/flags=0. */
    return 1;
}

static int advice_slot(const void *message)
{
    int i;
    if (message == NULL || fd_50F6_034C == NULL) return -1;
    for (i = 0; i < 18; ++i)
        if (message == fd_50F6_034C[i]) return i;
    return -2;
}

static int menu_text_code(const char *text)
{
    if (text == NULL) return -1;
    if (strcmp(text, " Pause") == 0) return 1;
    if (strcmp(text, " Unpause") == 0) return 2;
    return -3;
}

static int host_effect(void *context, const SimRecoveredEffect *effect)
{
    MenuHost *host = context;
    CapturedEffect *row;
    unsigned i;
    if (host == NULL || effect == NULL || host->effect_count >= EFFECT_CAPACITY)
        return 0;
    if (host->try_reentrant) {
        host->try_reentrant = 0;
        host->nested_status = sim_recovered_engine_proc_menu_command(
            host->engine, 0xfd77u);
    }
    if (host->reject_effect) return 0;
    row = &host->effects[host->effect_count++];
    row->kind = effect->kind;
    for (i = 0; i < 5; ++i) row->args[i] = (int64_t)(intptr_t)effect->arguments[i];
    if (effect->kind == SIM_RECOVERED_EFFECT_EDIT_MESSAGE)
        row->args[0] = advice_slot((const void *)effect->arguments[0]);
    else if (effect->kind == SIM_RECOVERED_EFFECT_WINDOW_OPERATION &&
             effect->arguments[0] == SIM_RECOVERED_WINDOW_SET_MENU_ITEM_TEXT)
        row->args[2] = menu_text_code((const char *)effect->arguments[2]);
    return 1;
}

static int host_song_done(void *context)
{
    (void)context;
    return 1;
}

static void dump_case(const char *name, SimRecoveredEngineStatus status,
                      uint64_t ticks_before, int rng_same,
                      const MenuHost *host)
{
    size_t i;
    printf("CASE|%s|%d|%" PRIu64 "|%" PRIu64 "|%d|%zu|%u|%d\n",
           name, status, ticks_before, host->engine->completed_ticks,
           rng_same, host->effect_count,
           (unsigned)!host->engine->recovered_binding_active,
           host->nested_status);
    for (i = 0; i < host->effect_count; ++i) {
        const CapturedEffect *e = &host->effects[i];
        printf("EFFECT|%s|%d|%" PRId64 "|%" PRId64 "|%" PRId64
               "|%" PRId64 "|%" PRId64 "\n", name, e->kind,
               e->args[0], e->args[1], e->args[2], e->args[3], e->args[4]);
    }
}

static SimRecoveredEngineStatus command(MenuHost *host, const char *name,
                                         uint16_t word, int should_reenter)
{
    SimRng before = host->engine->session->rng;
    PortableAudioIntents audio_before = host->engine->audio_intents;
    uint64_t ticks = host->engine->completed_ticks;
    SimRecoveredEngineStatus status;
    host->effect_count = 0;
    host->try_reentrant = should_reenter;
    host->nested_status = SIM_RECOVERED_ENGINE_OK;
    status = sim_recovered_engine_proc_menu_command(host->engine, word);
    dump_case(name, status, ticks,
              memcmp(&before, &host->engine->session->rng, sizeof(before)) == 0,
              host);
    assert(host->engine->completed_ticks == ticks);
    assert(memcmp(&before, &host->engine->session->rng, sizeof(before)) == 0);
    assert(memcmp(&audio_before, &host->engine->audio_intents,
                  sizeof(audio_before)) == 0);
    assert(!host->engine->recovered_binding_active);
    if (should_reenter)
        assert(host->nested_status == SIM_RECOVERED_ENGINE_INVALID_ARGUMENT);
    return status;
}

static void reset_menu_observation(MenuHost *host)
{
    host->effect_count = 0;
    host->try_reentrant = 0;
}

int main(void)
{
    static SimSession session = SIM_SESSION_INITIALIZER;
    static SimRecoveredEngine engine;
    PortableDatabase window_database = {0};
    PortableWindowRegistry window_registry = {0};
    const SimNewGameConfig config = {1, 0, 11, 8};
    MenuHost host_state = {0};
    SimRecoveredHost host = {0};
    SimNestRequest request = {{1000, 1001}, 2};
    SimRecoveredEngineStatus status;
    unsigned i;

    if (portable_db_open(&window_database, "assets/HCEGANT") != PORTABLE_DB_OK ||
        portable_window_registry_init(&window_registry, &window_database, 0) !=
            PORTABLE_WINDOW_REGISTRY_OK ||
        sim_session_init(&session, "assets", &window_database,
                         &window_registry) != SIM_SESSION_OK ||
        sim_session_seed_startup(&session, 0x5a31u, 0x12345678u) != SIM_SESSION_OK ||
        sim_session_new_game(&session, &config) != SIM_SESSION_OK ||
        portable_window_registry_recalculate(&window_registry, 0, NULL) !=
            PORTABLE_WINDOW_REGISTRY_OK) {
        fprintf(stderr, "resource-backed session startup failed\n");
        return 2;
    }
    host_state.engine = &engine;
    host.context = &host_state;
    host.tick_count = host_tick;
    host.query = host_query;
    host.effect = host_effect;
    host.song_done = host_song_done;
    host.audio_driver_ready = 0;
    host.screen_width = 640;
    host.hardware_profile = (uint8_t)window_registry.profile_id;
    assert(sim_recovered_engine_init(&engine, &session, &host) ==
           SIM_RECOVERED_ENGINE_INIT_OK);
    status = sim_recovered_engine_tick(&engine, &request);
    if (status != SIM_RECOVERED_ENGINE_OK) {
        fprintf(stderr, "baseline source tick failed: %s (%s)\n",
                sim_recovered_engine_status_string(status),
                engine.failed_service != NULL ? engine.failed_service : "unknown");
        return 3;
    }
    reset_menu_observation(&host_state);
    assert(engine.completed_ticks == 1);

    assert(sim_recovered_engine_proc_menu_command(NULL, 0xfd77u) ==
           SIM_RECOVERED_ENGINE_INVALID_ARGUMENT);
    printf("GUARD|null-engine|%d\n", SIM_RECOVERED_ENGINE_INVALID_ARGUMENT);
    {
        SimRecoveredEngine uninitialized = {0};
        assert(sim_recovered_engine_proc_menu_command(&uninitialized, 0xfd77u) ==
               SIM_RECOVERED_ENGINE_INVALID_ARGUMENT);
    }
    assert(sim_recovered_engine_action(&engine, SIM_RECOVERED_ACTION_PROC_MENU,
                                       0x41, 1) == SIM_RECOVERED_ENGINE_INVALID_ARGUMENT);
    printf("GUARD|uninitialized-and-invalid-action|%d\n",
           SIM_RECOVERED_ENGINE_INVALID_ARGUMENT);

    /* Speed IDs 0x43..0x46 carry an FD high byte into the source wrapper. */
    for (i = 0; i < 4; ++i) {
        char name[32];
        int16_t previous = engine.recovered.fd_3D57_07CC[0];
        (void)snprintf(name, sizeof name, "speed-%02x", 0x43u + i);
        status = command(&host_state, name, (uint16_t)(0xfd43u + i), i == 0);
        assert(status == SIM_RECOVERED_ENGINE_OK);
        assert(engine.recovered.fd_3D57_07CC[0] == (int16_t)i);
        assert(session.world.simulation_speed_index == (int16_t)i);
        assert(previous != engine.recovered.fd_3D57_07CC[0] || i == 0);
        assert(host_state.effect_count == 11);
        assert(host_state.effects[0].kind == SIM_RECOVERED_EFFECT_WINDOW_OPERATION);
        assert(host_state.effects[0].args[0] == SIM_RECOVERED_WINDOW_SET_MENU_ITEM_STATE);
        assert(host_state.effects[0].args[1] == 0x42);
        assert(host_state.effects[0].args[2] == (i == 0 ? 0x10 : 0x20));
        assert(host_state.effects[4].args[0] == SIM_RECOVERED_WINDOW_SET_MENU_ITEM_TEXT);
        assert(host_state.effects[4].args[1] == 0x41);
        assert(host_state.effects[4].args[2] == 1);
    }

    /* Pending File commands only replace the source menu's selected word. */
    {
        static const uint16_t commands[] = {0xfd04u, 0xfd05u, 0xfd06u, 0xfd08u};
        static const int16_t expected[] = {4, 5, 6, 8};
        for (i = 0; i < 4; ++i) {
            char name[32];
            (void)snprintf(name, sizeof name, "pending-%02x", expected[i]);
            assert(command(&host_state, name, commands[i], 0) ==
                   SIM_RECOVERED_ENGINE_OK);
            assert(engine.recovered.fd_55B3_2CBC == expected[i]);
            assert(host_state.effect_count == 0);
        }
    }
    {
        RecoveredState before = engine.recovered;
        assert(command(&host_state, "unknown-77", 0xfd77u, 0) ==
               SIM_RECOVERED_ENGINE_OK);
        assert(memcmp(&before, &engine.recovered, sizeof before) == 0);
        assert(host_state.effect_count == 0);
    }

    /* Pause/unpause with idle, life-transfer, and target-tool source states. */
    for (i = 0; i < 3; ++i) {
        static const int16_t tools[] = {-1, 10, 11};
        static const int expected_slot[] = {2, 3, 17};
        char name[32];
        engine.recovered.fd_50F6_047E = 0;
        engine.recovered.fd_50F6_105E = tools[i];
        engine.recovered.fd_50F6_048E = 0;
        session.modal_mode_105e = tools[i];
        (void)snprintf(name, sizeof name, "pause-tool-%d", tools[i]);
        assert(command(&host_state, name, 0xfd41u, 0) ==
               SIM_RECOVERED_ENGINE_OK);
        assert(engine.recovered.fd_50F6_047E == 1);
        assert(host_state.effect_count >= 15);
        assert(host_state.effects[0].kind == SIM_RECOVERED_EFFECT_EDIT_MESSAGE);
        assert(host_state.effects[0].args[0] == expected_slot[i]);
    }
    for (i = 1; i < 3; ++i) {
        static const int16_t tools[] = {-1, 10, 11};
        char name[32];
        engine.recovered.fd_50F6_047E = 1;
        engine.recovered.fd_50F6_105E = tools[i];
        engine.recovered.fd_50F6_048E = 0;
        session.modal_mode_105e = tools[i];
        (void)snprintf(name, sizeof name, "unpause-tool-%d", tools[i]);
        assert(command(&host_state, name, 0xfd41u, 0) ==
               SIM_RECOVERED_ENGINE_OK);
        assert(engine.recovered.fd_50F6_047E == 0);
        assert(engine.recovered.fd_50F6_105E == -1);
        assert(session.modal_mode_105e == -1);
    }
    engine.recovered.fd_50F6_047E = 1;
    engine.recovered.fd_50F6_105E = -1;
    session.modal_mode_105e = -1;
    assert(command(&host_state, "unpause-idle", 0xfd41u, 0) ==
           SIM_RECOVERED_ENGINE_OK);
    assert(engine.recovered.fd_50F6_047E == 0);

    /* Five option switches run through actual SetMenuEntries. Command 0x32
     * is tested last because current engine StopSong is a deliberate fail-closed
     * game-service boundary and terminally faults the engine before its toggle. */
    for (i = 0; i < 6; ++i) {
        char name[32];
        if (i == 1) continue;
        engine.recovered.fd_3D57_07A8[i] = 0;
        (void)snprintf(name, sizeof name, "option-%02x", 0x31u + i);
        status = command(&host_state, name, (uint16_t)(0xfd31u + i), 0);
        assert(status == SIM_RECOVERED_ENGINE_OK);
        assert(engine.recovered.fd_3D57_07A8[i] == 1);
        assert(host_state.effect_count == 11);
        assert(host_state.effects[0].args[0] == SIM_RECOVERED_WINDOW_SET_MENU_ITEM_STATE);
    }
    engine.recovered.fd_3D57_07A8[1] = 0;
    status = command(&host_state, "option-32", 0xfd32u, 0);
    assert(status == SIM_RECOVERED_ENGINE_UNSUPPORTED_CALL);
    assert(engine.failed_service != NULL && strcmp(engine.failed_service, "StopSong") == 0);
    assert(engine.status == SIM_RECOVERED_ENGINE_UNSUPPORTED_CALL);
    assert(sim_recovered_engine_proc_menu_command(&engine, 0xfd31u) ==
           SIM_RECOVERED_ENGINE_FAULTED);
    printf("GUARD|faulted-followup|%d\n", SIM_RECOVERED_ENGINE_FAULTED);
    assert(engine.recovered.fd_3D57_07A8[1] == 0);
    printf("GAP|option-32|StopSong|source stops song before toggling sound option\n");

    printf("SUMMARY|PASS|completed_ticks=%" PRIu64 "|queries_flags=%u\n",
           engine.completed_ticks,
           host_state.queries[SIM_RECOVERED_QUERY_DOS_KEYBOARD_FLAGS]);
    sim_session_close(&session);
    portable_window_registry_destroy(&window_registry);
    portable_db_close(&window_database);
    return 0;
}
