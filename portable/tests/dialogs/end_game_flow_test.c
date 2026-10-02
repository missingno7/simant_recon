#include "../../ui_model/dialogs/end_game_flow.h"

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#undef assert
#define assert(condition) do { \
    if (!(condition)) { \
        fprintf(stderr, "%s:%d: check failed: %s\n", __FILE__, __LINE__, \
                #condition); \
        exit(1); \
    } \
} while (0)

enum {
    OP_BEGIN_SONG = 1,
    OP_OPEN,
    OP_FONT,
    OP_SCENARIO_TEXT,
    OP_SCORE_TEXT,
    OP_LEVEL_TEXT,
    OP_WAIT_INIT,
    OP_WINDOW_OPEN,
    OP_WINDOW_EVENTS,
    OP_DIALOG_ABORT,
    OP_CLOSE,
    OP_SONG_DONE,
    OP_NEW_GAME,
    OP_MENU_QUIT
};

typedef struct MockHost {
    int operations[64];
    int32_t values[64];
    int16_t small_values[64];
    size_t operation_count;
    int open;
    int event_values[4];
    int abort_values[4];
    int song_done_value;
    unsigned event_index;
    unsigned abort_index;
    unsigned window_open_calls;
    unsigned song_done_calls;
    int16_t new_game_result;
    unsigned new_game_calls;
    unsigned menu_quit_calls;
} MockHost;

static void record(MockHost *mock, int operation, int32_t value,
                   int16_t small)
{
    assert(mock->operation_count < 64);
    mock->operations[mock->operation_count] = operation;
    mock->values[mock->operation_count] = value;
    mock->small_values[mock->operation_count] = small;
    ++mock->operation_count;
}

static int begin_song(void *context, int16_t song, int16_t argument)
{
    record(context, OP_BEGIN_SONG, song, argument);
    return 1;
}

static int open_window(void *context, int16_t window)
{
    MockHost *mock = context;
    record(mock, OP_OPEN, window, 0);
    mock->open = 1;
    return 1;
}

static int set_font(void *context, int16_t font)
{
    record(context, OP_FONT, font, 0);
    return 1;
}

static int set_resource_text(void *context, int16_t object,
                             int16_t resource_id, int16_t index)
{
    MockHost *mock = context;
    if (!((object == 0x402 && resource_id == 1001) ||
          (object == 0x404 && resource_id == 1900)))
        return 0;
    record(mock, object == 0x402 ? OP_SCENARIO_TEXT : OP_LEVEL_TEXT,
           resource_id, index);
    return 1;
}

static int set_score_text(void *context, int16_t object, int32_t score)
{
    if (object != 0x403)
        return 0;
    record(context, OP_SCORE_TEXT, score, object);
    return 1;
}

static int wait_init(void *context, int16_t seconds)
{
    record(context, OP_WAIT_INIT, seconds, 0);
    return 1;
}

static int window_is_open(void *context, int16_t window, int *is_open)
{
    MockHost *mock = context;
    if (window != 0x400 || is_open == NULL)
        return 0;
    record(mock, OP_WINDOW_OPEN, window, 0);
    ++mock->window_open_calls;
    *is_open = mock->open;
    return 1;
}

static int window_events(void *context, int *has_events)
{
    MockHost *mock = context;
    record(mock, OP_WINDOW_EVENTS, 0, 0);
    *has_events = mock->event_values[mock->event_index++];
    return 1;
}

static int dialog_abort(void *context, int *requested_close)
{
    MockHost *mock = context;
    record(mock, OP_DIALOG_ABORT, 0, 0);
    *requested_close = mock->abort_values[mock->abort_index++];
    return 1;
}

static int close_window(void *context, int16_t window)
{
    MockHost *mock = context;
    if (window != 0x400)
        return 0;
    record(mock, OP_CLOSE, window, 0);
    mock->open = 0;
    return 1;
}

static int song_done(void *context, int *is_done)
{
    MockHost *mock = context;
    record(mock, OP_SONG_DONE, 0, 0);
    ++mock->song_done_calls;
    *is_done = mock->song_done_value;
    return 1;
}

static int new_game(void *context, int16_t option, int16_t *result)
{
    MockHost *mock = context;
    if (option != 0 || result == NULL)
        return 0;
    record(mock, OP_NEW_GAME, option, 0);
    ++mock->new_game_calls;
    *result = mock->new_game_result;
    return 1;
}

static int menu_quit(void *context)
{
    MockHost *mock = context;
    record(mock, OP_MENU_QUIT, 0, 0);
    ++mock->menu_quit_calls;
    return 1;
}

static SimEndGameFlowHost make_host(MockHost *mock)
{
    SimEndGameFlowHost host;
    memset(&host, 0, sizeof(host));
    host.context = mock;
    host.begin_song = begin_song;
    host.open_window = open_window;
    host.set_font = set_font;
    host.set_resource_text = set_resource_text;
    host.set_score_text = set_score_text;
    host.dialog_wait_init = wait_init;
    host.window_is_open = window_is_open;
    host.window_events = window_events;
    host.dialog_abort_or_continue = dialog_abort;
    host.close_window = close_window;
    host.song_done = song_done;
    host.new_game = new_game;
    host.menu_quit = menu_quit;
    return host;
}

static SimGameOverInput game_over_input(void)
{
    SimGameOverInput input;
    memset(&input, 0, sizeof(input));
    input.health = 100;
    input.sound_enabled = 1;
    input.screen_width = 320;
    return input;
}

static void test_source_order_one_shot_and_new_game(void)
{
    SimGameOverInput input = game_over_input();
    SimEndGameFlow flow;
    SimRng rng = {0x1234, 0};
    SimRng expected_rng = rng;
    MockHost mock = {0};
    SimEndGameFlowHost host = make_host(&mock);
    size_t start;
    int16_t expected_song;

    mock.event_values[0] = 0;
    mock.event_values[1] = 1;
    mock.abort_values[0] = 0;
    mock.song_done_value = 1;
    mock.new_game_result = 2;
    expected_song = (int16_t)(0x2713 + sim_rng_s2(&expected_rng));

    assert(sim_end_game_flow_begin(&flow, &input, &rng, &host) ==
           SIM_END_GAME_FLOW_OK);
    assert(mock.operation_count == 8);
    assert(mock.operations[0] == OP_BEGIN_SONG && mock.values[0] == 0x271a);
    assert(mock.operations[1] == OP_OPEN && mock.values[1] == 0x400);
    assert(mock.operations[2] == OP_FONT && mock.values[2] == 2);
    assert(mock.operations[3] == OP_SCENARIO_TEXT &&
           mock.values[3] == 1001 && mock.small_values[3] == 0);
    assert(mock.operations[4] == OP_SCORE_TEXT && mock.small_values[4] == 0x403);
    assert(mock.operations[5] == OP_LEVEL_TEXT && mock.values[5] == 1900);
    assert(mock.operations[6] == OP_FONT && mock.values[6] == 0);
    assert(mock.operations[7] == OP_WAIT_INIT && mock.values[7] == 100);

    start = mock.operation_count;
    assert(sim_end_game_flow_step(&flow) == SIM_END_GAME_FLOW_OK);
    assert(mock.operations[start] == OP_WINDOW_OPEN);
    assert(mock.operations[start + 1] == OP_WINDOW_EVENTS);
    assert(mock.operations[start + 2] == OP_DIALOG_ABORT);
    assert(mock.operations[start + 3] == OP_SONG_DONE);
    assert(mock.operations[start + 4] == OP_BEGIN_SONG);
    assert(mock.values[start + 4] == expected_song);
    assert(flow.played_song_done_cue == 1);
    assert(rng.s_state == expected_rng.s_state);

    start = mock.operation_count;
    assert(sim_end_game_flow_step(&flow) == SIM_END_GAME_FLOW_OK);
    assert(mock.operations[start] == OP_WINDOW_OPEN);
    assert(mock.operations[start + 1] == OP_WINDOW_EVENTS);
    assert(mock.operations[start + 2] == OP_CLOSE);
    assert(mock.operations[start + 3] == OP_SONG_DONE);
    assert(mock.operations[start + 4] != OP_BEGIN_SONG);
    assert(mock.song_done_calls == 2);
    assert(mock.menu_quit_calls == 0);

    start = mock.operation_count;
    assert(sim_end_game_flow_step(&flow) == SIM_END_GAME_FLOW_DONE);
    assert(mock.operations[start] == OP_WINDOW_OPEN);
    assert(mock.operations[start + 1] == OP_NEW_GAME);
    assert(mock.new_game_calls == 1);
    assert(flow.outcome == SIM_END_GAME_FLOW_NEW_GAME_RETURNED);
}

static void test_audio_disabled_still_consumes_song_done_rng_and_quits(void)
{
    SimGameOverInput input = game_over_input();
    SimEndGameFlow flow;
    SimRng rng = {0xabcd, 0};
    SimRng expected_rng = rng;
    MockHost mock = {0};
    SimEndGameFlowHost host = make_host(&mock);
    size_t start;
    int16_t expected_song;

    input.sound_enabled = 0;
    mock.event_values[0] = 1;
    mock.song_done_value = 1;
    mock.new_game_result = -1;
    expected_song = (int16_t)(0x2713 + sim_rng_s2(&expected_rng));

    assert(sim_end_game_flow_begin(&flow, &input, &rng, &host) ==
           SIM_END_GAME_FLOW_OK);
    assert(mock.operations[0] == OP_OPEN); /* opening music gate is off */
    start = mock.operation_count;
    assert(sim_end_game_flow_step(&flow) == SIM_END_GAME_FLOW_OK);
    assert(mock.operations[start] == OP_WINDOW_OPEN);
    assert(mock.operations[start + 1] == OP_WINDOW_EVENTS);
    assert(mock.operations[start + 2] == OP_CLOSE);
    assert(mock.operations[start + 3] == OP_SONG_DONE);
    assert(mock.operations[start + 4] == OP_BEGIN_SONG);
    assert(mock.values[start + 4] == expected_song);
    assert(rng.s_state == expected_rng.s_state);

    start = mock.operation_count;
    assert(sim_end_game_flow_step(&flow) == SIM_END_GAME_FLOW_DONE);
    assert(mock.operations[start] == OP_WINDOW_OPEN);
    assert(mock.operations[start + 1] == OP_NEW_GAME);
    assert(mock.operations[start + 2] == OP_MENU_QUIT);
    assert(mock.new_game_result == -1);
    assert(mock.menu_quit_calls == 1);
    assert(flow.outcome == SIM_END_GAME_FLOW_MENU_QUIT_RETURNED);
}

static void test_missing_resource_service_fails_closed(void)
{
    SimGameOverInput input = game_over_input();
    SimEndGameFlow flow;
    SimRng rng = {1, 0};
    MockHost mock = {0};
    SimEndGameFlowHost host = make_host(&mock);
    host.set_resource_text = NULL;
    assert(sim_end_game_flow_begin(&flow, &input, &rng, &host) ==
           SIM_END_GAME_FLOW_UNSUPPORTED_SERVICE);
    assert(flow.phase == SIM_END_GAME_FLOW_FAILED);
    assert(strcmp(flow.failed_service, "scenario resource text") == 0);
    assert(mock.operation_count == 3); /* opening song, window, font */
}

int main(void)
{
    test_source_order_one_shot_and_new_game();
    test_audio_disabled_still_consumes_song_done_rng_and_quits();
    test_missing_resource_service_fails_closed();
    puts("end-game flow: source-order cases pass");
    return 0;
}
