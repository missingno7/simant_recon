#ifndef SIMANT_PORTABLE_UI_MODEL_DIALOGS_END_GAME_FLOW_H
#define SIMANT_PORTABLE_UI_MODEL_DIALOGS_END_GAME_FLOW_H

#include "game_over.h"
#include "../../game/simulation/rng.h"

typedef enum SimEndGameFlowStatus {
    SIM_END_GAME_FLOW_OK = 0,
    SIM_END_GAME_FLOW_DONE,
    SIM_END_GAME_FLOW_BAD_ARGUMENT,
    SIM_END_GAME_FLOW_INVALID_STATE,
    SIM_END_GAME_FLOW_UNSUPPORTED_SERVICE,
    SIM_END_GAME_FLOW_HOST_REJECTED
} SimEndGameFlowStatus;

typedef enum SimEndGameFlowPhase {
    SIM_END_GAME_FLOW_IDLE = 0,
    SIM_END_GAME_FLOW_WAIT_WINDOW,
    SIM_END_GAME_FLOW_COMPLETE,
    SIM_END_GAME_FLOW_FAILED
} SimEndGameFlowPhase;

typedef enum SimEndGameFlowOutcome {
    SIM_END_GAME_FLOW_NO_OUTCOME = 0,
    SIM_END_GAME_FLOW_NEW_GAME_RETURNED,
    SIM_END_GAME_FLOW_MENU_QUIT_RETURNED
} SimEndGameFlowOutcome;

/* Each callback corresponds to a source operation. Resource text callbacks
 * must resolve the requested retained kind-4 table entry or reject the call;
 * this flow never substitutes labels. Callbacks return nonzero on success. */
typedef struct SimEndGameFlowHost {
    void *context;
    int (*begin_song)(void *context, int16_t song, int16_t source_argument);
    int (*open_window)(void *context, int16_t window);
    int (*set_font)(void *context, int16_t font);
    int (*set_resource_text)(void *context, int16_t object,
                             int16_t resource_id, int16_t index);
    int (*set_score_text)(void *context, int16_t object, int32_t score);
    int (*dialog_wait_init)(void *context, int16_t seconds);
    int (*window_is_open)(void *context, int16_t window, int *is_open);
    int (*window_events)(void *context, int *has_events);
    int (*dialog_abort_or_continue)(void *context, int *requested_close);
    int (*close_window)(void *context, int16_t window);
    /* Mirrors mySongIsDone: it may return true when audio is disabled. */
    int (*song_done)(void *context, int *is_done);
    /* Mirrors NewGame(0), returning its signed source result through result. */
    int (*new_game)(void *context, int16_t option, int16_t *result);
    /* Mirrors MenuQuit, including any source-owned save/confirmation path. */
    int (*menu_quit)(void *context);
} SimEndGameFlowHost;

typedef struct SimEndGameFlow {
    SimEndGameFlowHost host;
    SimRng *rng; /* Borrowed source RNG; SRand2 is consumed by this flow. */
    SimGameOverResult summary;
    SimEndGameFlowPhase phase;
    SimEndGameFlowOutcome outcome;
    SimEndGameFlowStatus failure;
    const char *failed_service;
    int16_t new_game_result;
    uint8_t played_song_done_cue;
} SimEndGameFlow;

/* Performs the synchronous source prefix through window initialization:
 * optional opening song, window/font/three objects/font reset, then
 * DialogWaitInit(100). Resource and window services are mandatory. */
SimEndGameFlowStatus sim_end_game_flow_begin(
    SimEndGameFlow *flow, const SimGameOverInput *input, SimRng *rng,
    const SimEndGameFlowHost *host);

/* Executes one source modal-loop pass. A closed window then invokes
 * NewGame(0); a negative return invokes MenuQuit before completion. The
 * DialogAbortOrCont poll is skipped when win_Events already returned true,
 * but SongDone is still queried once in that iteration. */
SimEndGameFlowStatus sim_end_game_flow_step(SimEndGameFlow *flow);

const char *sim_end_game_flow_status_string(SimEndGameFlowStatus status);

#endif
