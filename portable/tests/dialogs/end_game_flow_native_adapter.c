#include "../../ui_model/dialogs/end_game_flow.h"

#include <stdint.h>
#include <string.h>

enum { TRACE_CAPACITY = 256, INPUT_CAPACITY = 8 };

typedef enum TraceKind {
    TRACE_BEGIN_SONG = 1,
    TRACE_OPEN_WINDOW,
    TRACE_SET_FONT,
    TRACE_SCENARIO_TEXT,
    TRACE_SCORE_TEXT,
    TRACE_LEVEL_TEXT,
    TRACE_WAIT_INIT,
    TRACE_WINDOW_IS_OPEN,
    TRACE_WINDOW_EVENTS,
    TRACE_DIALOG_ABORT,
    TRACE_CLOSE_WINDOW,
    TRACE_SONG_DONE,
    TRACE_NEW_GAME,
    TRACE_MENU_QUIT
} TraceKind;

typedef struct SimEndGameControlConfig {
    SimGameOverInput input;
    uint16_t s_seed;
    uint32_t c_seed;
    int16_t start_open_after_open;
    int16_t new_game_result;
    uint16_t event_count;
    int16_t events[INPUT_CAPACITY];
    uint16_t abort_count;
    int16_t aborts[INPUT_CAPACITY];
    uint16_t song_done_count;
    int16_t song_done[INPUT_CAPACITY];
} SimEndGameControlConfig;

typedef struct SimEndGameControlEvent {
    int16_t kind;
    int16_t argc;
    int32_t args[4];
} SimEndGameControlEvent;

typedef struct SimEndGameControlResult {
    int16_t status;
    int16_t phase;
    int16_t outcome;
    int16_t new_game_result;
    uint16_t s_before;
    uint16_t s_after;
    uint32_t c_before;
    uint32_t c_after;
    uint16_t event_count;
    SimEndGameControlEvent events[TRACE_CAPACITY];
} SimEndGameControlResult;

typedef struct HostState {
    const SimEndGameControlConfig *config;
    SimEndGameControlResult *result;
    uint16_t event_index;
    uint16_t abort_index;
    uint16_t song_done_index;
    int open;
    int overflow;
} HostState;

static void record(HostState *host, TraceKind kind, int argc,
                   int32_t a, int32_t b, int32_t c, int32_t d)
{
    SimEndGameControlEvent *event;
    if (host->result->event_count >= TRACE_CAPACITY) {
        host->overflow = 1;
        return;
    }
    event = &host->result->events[host->result->event_count++];
    event->kind = (int16_t)kind;
    event->argc = (int16_t)argc;
    event->args[0] = a;
    event->args[1] = b;
    event->args[2] = c;
    event->args[3] = d;
}

static int host_begin_song(void *opaque, int16_t song, int16_t argument)
{
    record(opaque, TRACE_BEGIN_SONG, 2, song, argument, 0, 0);
    return 1;
}

static int host_open_window(void *opaque, int16_t window)
{
    HostState *host = opaque;
    host->open = host->config->start_open_after_open != 0;
    record(host, TRACE_OPEN_WINDOW, 1, window, 0, 0, 0);
    return 1;
}

static int host_set_font(void *opaque, int16_t font)
{
    record(opaque, TRACE_SET_FONT, 1, font, 0, 0, 0);
    return 1;
}

static int host_set_resource_text(void *opaque, int16_t object,
                                  int16_t resource, int16_t index)
{
    HostState *host = opaque;
    TraceKind kind = object == SIM_GAME_OVER_SCENARIO_OBJECT ?
        TRACE_SCENARIO_TEXT : TRACE_LEVEL_TEXT;
    record(host, kind, 3, object, resource, index, 0);
    return 1;
}

static int host_set_score_text(void *opaque, int16_t object, int32_t score)
{
    record(opaque, TRACE_SCORE_TEXT, 2, object, score, 0, 0);
    return 1;
}

static int host_wait_init(void *opaque, int16_t seconds)
{
    record(opaque, TRACE_WAIT_INIT, 1, seconds, 0, 0, 0);
    return 1;
}

static int host_window_is_open(void *opaque, int16_t window, int *is_open)
{
    HostState *host = opaque;
    *is_open = host->open;
    record(host, TRACE_WINDOW_IS_OPEN, 2, window, *is_open, 0, 0);
    return 1;
}

static int host_window_events(void *opaque, int *has_events)
{
    HostState *host = opaque;
    *has_events = host->event_index < host->config->event_count ?
        host->config->events[host->event_index++] : 0;
    record(host, TRACE_WINDOW_EVENTS, 1, *has_events, 0, 0, 0);
    return 1;
}

static int host_dialog_abort(void *opaque, int *requested_close)
{
    HostState *host = opaque;
    *requested_close = host->abort_index < host->config->abort_count ?
        host->config->aborts[host->abort_index++] : 0;
    record(host, TRACE_DIALOG_ABORT, 1, *requested_close, 0, 0, 0);
    return 1;
}

static int host_close_window(void *opaque, int16_t window)
{
    HostState *host = opaque;
    host->open = 0;
    record(host, TRACE_CLOSE_WINDOW, 1, window, 0, 0, 0);
    return 1;
}

static int host_song_done(void *opaque, int *is_done)
{
    HostState *host = opaque;
    *is_done = host->song_done_index < host->config->song_done_count ?
        host->config->song_done[host->song_done_index++] : 0;
    record(host, TRACE_SONG_DONE, 1, *is_done, 0, 0, 0);
    return 1;
}

static int host_new_game(void *opaque, int16_t option, int16_t *result)
{
    HostState *host = opaque;
    *result = host->config->new_game_result;
    record(host, TRACE_NEW_GAME, 2, option, *result, 0, 0);
    return 1;
}

static int host_menu_quit(void *opaque)
{
    record(opaque, TRACE_MENU_QUIT, 0, 0, 0, 0, 0);
    return 1;
}

int sim_end_game_flow_run_control(const SimEndGameControlConfig *config,
                                  SimEndGameControlResult *result)
{
    SimRng rng;
    SimEndGameFlow flow;
    SimEndGameFlowHost host;
    HostState host_state;
    SimEndGameFlowStatus status;
    unsigned steps;

    if (config == NULL || result == NULL ||
        config->event_count > INPUT_CAPACITY ||
        config->abort_count > INPUT_CAPACITY ||
        config->song_done_count > INPUT_CAPACITY)
        return 0;
    memset(result, 0, sizeof(*result));
    memset(&host_state, 0, sizeof(host_state));
    memset(&host, 0, sizeof(host));
    host_state.config = config;
    host_state.result = result;
    rng.s_state = config->s_seed;
    rng.c_state = config->c_seed;
    result->s_before = rng.s_state;
    result->c_before = rng.c_state;

    host.context = &host_state;
    host.begin_song = host_begin_song;
    host.open_window = host_open_window;
    host.set_font = host_set_font;
    host.set_resource_text = host_set_resource_text;
    host.set_score_text = host_set_score_text;
    host.dialog_wait_init = host_wait_init;
    host.window_is_open = host_window_is_open;
    host.window_events = host_window_events;
    host.dialog_abort_or_continue = host_dialog_abort;
    host.close_window = host_close_window;
    host.song_done = host_song_done;
    host.new_game = host_new_game;
    host.menu_quit = host_menu_quit;

    status = sim_end_game_flow_begin(&flow, &config->input, &rng, &host);
    for (steps = 0; status == SIM_END_GAME_FLOW_OK && steps < 64; ++steps)
        status = sim_end_game_flow_step(&flow);
    result->status = (int16_t)status;
    result->phase = (int16_t)flow.phase;
    result->outcome = (int16_t)flow.outcome;
    result->new_game_result = flow.new_game_result;
    result->s_after = rng.s_state;
    result->c_after = rng.c_state;
    return status == SIM_END_GAME_FLOW_DONE && !host_state.overflow;
}
