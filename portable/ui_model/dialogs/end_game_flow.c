#include "end_game_flow.h"

#include <string.h>

static SimEndGameFlowStatus fail(SimEndGameFlow *flow,
                                 SimEndGameFlowStatus status,
                                 const char *service)
{
    flow->phase = SIM_END_GAME_FLOW_FAILED;
    flow->failure = status;
    flow->failed_service = service;
    return status;
}

static int present_service(SimEndGameFlow *flow, int present,
                           const char *service)
{
    if (!present) {
        (void)fail(flow, SIM_END_GAME_FLOW_UNSUPPORTED_SERVICE, service);
        return 0;
    }
    return 1;
}

static int accepted_service(SimEndGameFlow *flow, int accepted,
                            const char *service)
{
    if (!accepted) {
        (void)fail(flow, SIM_END_GAME_FLOW_HOST_REJECTED, service);
        return 0;
    }
    return 1;
}

SimEndGameFlowStatus sim_end_game_flow_begin(
    SimEndGameFlow *flow, const SimGameOverInput *input, SimRng *rng,
    const SimEndGameFlowHost *host)
{
    SimEndGameFlow initial;
    SimGameOverStatus model_status;

    if (flow == NULL || input == NULL || rng == NULL || host == NULL)
        return SIM_END_GAME_FLOW_BAD_ARGUMENT;
    memset(&initial, 0, sizeof(initial));
    initial.host = *host;
    initial.rng = rng;
    initial.phase = SIM_END_GAME_FLOW_IDLE;
    model_status = sim_game_over_calculate(input, &initial.summary);
    if (model_status != SIM_GAME_OVER_OK)
        return SIM_END_GAME_FLOW_INVALID_STATE;
    *flow = initial;

    if (flow->summary.opening_sound_id != 0) {
        if (!present_service(flow, host->begin_song != NULL, "begin_song") ||
            !accepted_service(flow,
                host->begin_song(host->context,
                    flow->summary.opening_sound_id,
                    flow->summary.sound_argument), "begin_song"))
            return flow->failure;
    }
    if (!present_service(flow, host->open_window != NULL, "open_window") ||
        !accepted_service(flow, host->open_window(host->context,
            flow->summary.window_id), "open_window"))
        return flow->failure;
    if (!present_service(flow, host->set_font != NULL, "set_font") ||
        !accepted_service(flow, host->set_font(host->context,
            flow->summary.font_id), "set_font"))
        return flow->failure;
    if (!present_service(flow, host->set_resource_text != NULL,
                         "scenario resource text") ||
        !accepted_service(flow, host->set_resource_text(host->context,
            flow->summary.scenario_object_id,
            flow->summary.scenario_resource_id,
            flow->summary.scenario_index), "scenario resource text"))
        return flow->failure;
    if (!present_service(flow, host->set_score_text != NULL, "score text") ||
        !accepted_service(flow, host->set_score_text(host->context,
            flow->summary.score_object_id, flow->summary.score), "score text"))
        return flow->failure;
    if (!present_service(flow, host->set_resource_text != NULL,
                         "level resource text") ||
        !accepted_service(flow, host->set_resource_text(host->context,
            flow->summary.level_object_id,
            flow->summary.level_resource_id,
            flow->summary.level_index), "level resource text"))
        return flow->failure;
    if (!accepted_service(flow, host->set_font(host->context, 0),
                          "reset font"))
        return flow->failure;
    if (!present_service(flow, host->dialog_wait_init != NULL,
                         "DialogWaitInit") ||
        !accepted_service(flow, host->dialog_wait_init(host->context, 100),
                          "DialogWaitInit"))
        return flow->failure;

    flow->phase = SIM_END_GAME_FLOW_WAIT_WINDOW;
    return SIM_END_GAME_FLOW_OK;
}

static SimEndGameFlowStatus leave_modal(SimEndGameFlow *flow)
{
    int16_t new_game_result = 0;
    if (!present_service(flow, flow->host.new_game != NULL, "NewGame") ||
        !accepted_service(flow, flow->host.new_game(flow->host.context, 0,
                          &new_game_result), "NewGame"))
        return flow->failure;
    flow->new_game_result = new_game_result;
    if (new_game_result < 0) {
        if (!present_service(flow, flow->host.menu_quit != NULL, "MenuQuit") ||
            !accepted_service(flow, flow->host.menu_quit(flow->host.context),
                              "MenuQuit"))
            return flow->failure;
        flow->outcome = SIM_END_GAME_FLOW_MENU_QUIT_RETURNED;
    } else {
        flow->outcome = SIM_END_GAME_FLOW_NEW_GAME_RETURNED;
    }
    flow->phase = SIM_END_GAME_FLOW_COMPLETE;
    return SIM_END_GAME_FLOW_DONE;
}

SimEndGameFlowStatus sim_end_game_flow_step(SimEndGameFlow *flow)
{
    int is_open = 0;
    int has_events = 0;
    int requested_close = 0;
    int song_done = 0;

    if (flow == NULL)
        return SIM_END_GAME_FLOW_BAD_ARGUMENT;
    if (flow->phase == SIM_END_GAME_FLOW_COMPLETE)
        return SIM_END_GAME_FLOW_DONE;
    if (flow->phase == SIM_END_GAME_FLOW_FAILED)
        return flow->failure;
    if (flow->phase != SIM_END_GAME_FLOW_WAIT_WINDOW)
        return SIM_END_GAME_FLOW_INVALID_STATE;

    if (!present_service(flow, flow->host.window_is_open != NULL,
                         "window_is_open") ||
        !accepted_service(flow, flow->host.window_is_open(flow->host.context,
                          flow->summary.window_id, &is_open),
                          "window_is_open"))
        return flow->failure;
    if (!is_open)
        return leave_modal(flow);

    if (!present_service(flow, flow->host.window_events != NULL,
                         "win_Events") ||
        !accepted_service(flow, flow->host.window_events(flow->host.context,
                          &has_events), "win_Events"))
        return flow->failure;
    if (has_events) {
        requested_close = 1;
    } else {
        if (!present_service(flow,
                flow->host.dialog_abort_or_continue != NULL,
                "DialogAbortOrCont") ||
            !accepted_service(flow,
                flow->host.dialog_abort_or_continue(flow->host.context,
                    &requested_close), "DialogAbortOrCont"))
            return flow->failure;
    }
    if (requested_close) {
        if (!present_service(flow, flow->host.close_window != NULL,
                             "win_Close") ||
            !accepted_service(flow, flow->host.close_window(flow->host.context,
                              flow->summary.window_id), "win_Close"))
            return flow->failure;
    }

    if (!present_service(flow, flow->host.song_done != NULL, "mySongIsDone") ||
        !accepted_service(flow, flow->host.song_done(flow->host.context,
                          &song_done), "mySongIsDone"))
        return flow->failure;
    if (song_done && !flow->played_song_done_cue) {
        int16_t song = (int16_t)(0x2713 + sim_rng_s2(flow->rng));
        flow->played_song_done_cue = 1;
        if (!present_service(flow, flow->host.begin_song != NULL,
                             "myBeginSong") ||
            !accepted_service(flow, flow->host.begin_song(flow->host.context,
                              song, flow->summary.sound_argument),
                              "myBeginSong"))
            return flow->failure;
    }
    return SIM_END_GAME_FLOW_OK;
}

const char *sim_end_game_flow_status_string(SimEndGameFlowStatus status)
{
    switch (status) {
    case SIM_END_GAME_FLOW_OK: return "ok";
    case SIM_END_GAME_FLOW_DONE: return "done";
    case SIM_END_GAME_FLOW_BAD_ARGUMENT: return "bad argument";
    case SIM_END_GAME_FLOW_INVALID_STATE: return "invalid flow state";
    case SIM_END_GAME_FLOW_UNSUPPORTED_SERVICE: return "unsupported host service";
    case SIM_END_GAME_FLOW_HOST_REJECTED: return "host rejected service";
    }
    return "unknown end-game flow status";
}
