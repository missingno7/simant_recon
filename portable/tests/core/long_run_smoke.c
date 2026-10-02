#include "../../game/session.h"
#include "../../game/recovered/engine.h"
#include "../../ui_model/windows/registry.h"

#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

enum { LONG_RUN_TICKS = 4096, CALL_DEPTH_CAPACITY = 512 };

extern void EndGameDialog(int16_t code);

typedef struct LongRunHost {
    int32_t source_clock;
    PortableWindowRegistry *windows;
    uint64_t queries[SIM_RECOVERED_QUERY_DOS_KEYBOARD_FLAGS + 1];
    uint64_t effects[SIM_RECOVERED_EFFECT_GRAPHICS_LINE + 1];
    uint64_t effect_total;
    uint64_t audio_intents;
    uint64_t source_ticks;
    uint8_t bad_callback;
} LongRunHost;

static uintptr_t call_path[CALL_DEPTH_CAPACITY];
static size_t call_depth;
static int call_path_overflow;
static int endgame_entry_seen;
static int16_t endgame_live_flag;
static int16_t endgame_live_losing_side;
static int16_t endgame_live_scenario;
static int16_t endgame_live_blue_queens;
static int16_t endgame_live_red_queens;
static int16_t endgame_live_blue_population;
static int16_t endgame_live_red_population;

void __attribute__((no_instrument_function))
__cyg_profile_func_enter(void *function, void *caller)
{
    (void)caller;
    if (call_depth < CALL_DEPTH_CAPACITY)
        call_path[call_depth++] = (uintptr_t)function;
    else
        call_path_overflow = 1;
    if (function == (void *)EndGameDialog) {
        endgame_entry_seen = 1;
        endgame_live_flag = fd_50F6_0376;
        endgame_live_losing_side = fd_50F6_0366;
        endgame_live_scenario = fd_50F6_0EAC;
        endgame_live_blue_queens = fd_50F6_0AEC[5];
        endgame_live_red_queens = fd_50F6_0AFA[5];
        endgame_live_blue_population = BpopT;
        endgame_live_red_population = RpopT;
    }
}

void __attribute__((no_instrument_function))
__cyg_profile_func_exit(void *function, void *caller)
{
    (void)function;
    (void)caller;
    if (call_depth != 0)
        --call_depth;
}

static int host_tick_count(void *context, int32_t *value)
{
    LongRunHost *host = context;
    if (host == NULL || value == NULL)
        return 0;
    *value = host->source_clock++;
    ++host->source_ticks;
    return 1;
}

static int host_query(void *context, SimRecoveredQuery query,
                      const uintptr_t *arguments, uint8_t argument_count,
                      int32_t *value)
{
    LongRunHost *host = context;
    if (host == NULL || value == NULL || query <= 0 ||
        query > SIM_RECOVERED_QUERY_DOS_KEYBOARD_FLAGS)
        return 0;
    ++host->queries[query];
    switch (query) {
    case SIM_RECOVERED_QUERY_WINDOW_OPEN:
    case SIM_RECOVERED_QUERY_WINDOW_IN_FRONT:
        if (arguments == NULL || argument_count != 1)
            goto invalid;
        /* This smoke host deliberately starts with every optional window
         * closed and provides no user input. */
        *value = 0;
        return 1;
    case SIM_RECOVERED_QUERY_WINDOW_EVENTS:
    case SIM_RECOVERED_QUERY_STILL_DOWN:
    case SIM_RECOVERED_QUERY_DIALOG_ABORT_OR_CONTINUE:
    case SIM_RECOVERED_QUERY_BUTTON:
    case SIM_RECOVERED_QUERY_DOS_KEYBOARD_FLAGS:
        if (argument_count != 0)
            goto invalid;
        *value = 0;
        return 1;
    case SIM_RECOVERED_QUERY_GET_EVENT:
        if (arguments == NULL || argument_count != 1)
            goto invalid;
        /* No event is available. The source-owned event object is untouched. */
        *value = 0;
        return 1;
    case SIM_RECOVERED_QUERY_GET_OBJECT_RECT: {
        PortableWindowRect rect;
        int16_t *source_rect;
        if (arguments == NULL || argument_count != 2 || host->windows == NULL)
            goto invalid;
        source_rect = (int16_t *)arguments[1];
        if (source_rect == NULL ||
            portable_window_registry_get_object_rect(host->windows,
                (uint16_t)arguments[0], &rect) != PORTABLE_WINDOW_REGISTRY_OK)
            goto invalid;
        source_rect[0] = rect.left;
        source_rect[1] = rect.top;
        source_rect[2] = rect.right;
        source_rect[3] = rect.bottom;
        *value = 1;
        return 1;
    }
    default:
        goto invalid;
    }
invalid:
    host->bad_callback = 1;
    return 0;
}

static int host_effect(void *context, const SimRecoveredEffect *effect)
{
    LongRunHost *host = context;
    if (host == NULL || effect == NULL || effect->kind <= 0 ||
        effect->kind > SIM_RECOVERED_EFFECT_GRAPHICS_LINE) {
        if (host != NULL)
            host->bad_callback = 1;
        return 0;
    }
    ++host->effects[effect->kind];
    ++host->effect_total;
    /* The headless surface acknowledges these typed synchronous intents;
     * rendering and modal interaction are intentionally absent. */
    return 1;
}

static int host_song_done(void *context)
{
    (void)context;
    return 1;
}

static void print_host_summary(const LongRunHost *host)
{
    unsigned index;
    printf("HOST_SUMMARY effect_total=%" PRIu64 " audio_intents=%" PRIu64
           " source_clock_reads=%" PRIu64 " bad_callback=%u\n",
           host->effect_total, host->audio_intents, host->source_ticks,
           (unsigned)host->bad_callback);
    printf("QUERY_COUNTS");
    for (index = 1; index <= SIM_RECOVERED_QUERY_DOS_KEYBOARD_FLAGS; ++index)
        printf(" %u:%" PRIu64, index, host->queries[index]);
    printf("\nEFFECT_COUNTS");
    for (index = 1; index <= SIM_RECOVERED_EFFECT_GRAPHICS_LINE; ++index)
        printf(" %u:%" PRIu64, index, host->effects[index]);
    fputc('\n', stdout);
}

static void print_call_path(void)
{
    size_t index;
    fprintf(stderr, "CALL_PATH overflow=%d depth=%zu", call_path_overflow,
            call_depth);
    for (index = 0; index < call_depth; ++index)
        fprintf(stderr, " 0x%" PRIxPTR, call_path[index]);
    fputc('\n', stderr);
}

int main(void)
{
    static SimSession session = SIM_SESSION_INITIALIZER;
    static SimRecoveredEngine engine;
    PortableDatabase window_database = { 0 };
    PortableWindowRegistry window_registry = { 0 };
    const SimNewGameConfig config = { 1, 0, 11, 8 };
    LongRunHost host_state = { 0 };
    SimRecoveredHost host = { 0 };
    SimRecoveredEngineInitStatus init_status;
    SimRecoveredEngineStatus status;
    uint64_t tick;

    printf("MAIN_ADDRESS:%p\n", (void *)&main);
    if (portable_db_open(&window_database, "assets/HCEGANT") != PORTABLE_DB_OK ||
        portable_window_registry_init(&window_registry, &window_database, 0) !=
            PORTABLE_WINDOW_REGISTRY_OK ||
        sim_session_init(&session, "assets", &window_database,
                         &window_registry) != SIM_SESSION_OK ||
        sim_session_seed_startup(&session, 0x5a31u, 0x12345678u) !=
            SIM_SESSION_OK ||
        sim_session_new_game(&session, &config) != SIM_SESSION_OK ||
        portable_window_registry_recalculate(&window_registry, 0, NULL) !=
            PORTABLE_WINDOW_REGISTRY_OK) {
        fprintf(stderr, "STARTUP_FAILURE resource-backed NewGame setup failed\n");
        return 2;
    }
    host_state.windows = &window_registry;
    host.context = &host_state;
    host.tick_count = host_tick_count;
    host.query = host_query;
    host.effect = host_effect;
    host.song_done = host_song_done;
    host.audio_driver_ready = 0;
    host.screen_width = 640;
    host.hardware_profile = (uint8_t)window_registry.profile_id;
    init_status = sim_recovered_engine_init(&engine, &session, &host);
    if (init_status != SIM_RECOVERED_ENGINE_INIT_OK) {
        fprintf(stderr, "ENGINE_INIT_FAILURE status=%d\n", init_status);
        return 3;
    }

    for (tick = 0; tick < LONG_RUN_TICKS; ++tick) {
        SimNestRequest nest_clock;
        PortableAudioIntent audio_intent;
        nest_clock.tick_values[0] = host_state.source_clock++;
        nest_clock.tick_values[1] = host_state.source_clock++;
        nest_clock.tick_count = 2;
        status = sim_recovered_engine_tick(&engine, &nest_clock);
        if (status != SIM_RECOVERED_ENGINE_OK) {
            fprintf(stderr,
                "FIRST_FAULT tick=%" PRIu64 " completed=%" PRIu64
                " status=%s service=%s committed_cycle=%u last_me=(%d,%d,%d)"
                " rng_s=%u rng_c=%u effects=%" PRIu64
                " source_clock=%" PRId32
                " live_endgame_snapshot=%d:%d:%d:%d:%d:%d:%d:%d\n",
                tick, engine.completed_ticks,
                sim_recovered_engine_status_string(status),
                engine.failed_service != NULL ? engine.failed_service : "unknown",
                (unsigned)engine.recovered.Cycle,
                session.world.map_plane, session.world.me_x, session.world.me_y,
                (unsigned)session.rng.s_state, (unsigned)session.rng.c_state,
                host_state.effect_total, host_state.source_clock,
                endgame_entry_seen, endgame_live_flag,
                endgame_live_losing_side, endgame_live_scenario,
                endgame_live_blue_queens, endgame_live_red_queens,
                endgame_live_blue_population, endgame_live_red_population);
            print_call_path();
            print_host_summary(&host_state);
            return 10;
        }
        while (sim_recovered_engine_next_audio(&engine, &audio_intent))
            ++host_state.audio_intents;
        if (host_state.bad_callback) {
            fprintf(stderr, "HEADLESS_CALLBACK_CONTRACT_FAILURE tick=%" PRIu64 "\n",
                    tick);
            return 11;
        }
    }

    printf("LONG_RUN_PASS ticks=%" PRIu64 " completed=%" PRIu64
           " source_clock=%" PRId32 " source_clock_reads=%" PRIu64
           " effects=%" PRIu64 " audio_intents=%" PRIu64
           " cycle=%u me=(%d,%d,%d) rng_s=%u rng_c=%u\n",
           tick, engine.completed_ticks, host_state.source_clock,
           host_state.source_ticks, host_state.effect_total,
           host_state.audio_intents, (unsigned)engine.recovered.Cycle,
           session.world.map_plane, session.world.me_x, session.world.me_y,
           (unsigned)session.rng.s_state, (unsigned)session.rng.c_state);
    print_host_summary(&host_state);
    sim_session_close(&session);
    portable_window_registry_destroy(&window_registry);
    portable_db_close(&window_database);
    return 0;
}
