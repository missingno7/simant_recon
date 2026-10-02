#ifndef SIMANT_GAME_RECOVERED_ENGINE_H
#define SIMANT_GAME_RECOVERED_ENGINE_H

#include <stdint.h>

#include "audio_adapter.h"
#include "nest_adapter.h"
#include "session_bridge.h"
#include "../../ui_model/dialogs/game_over.h"
#include "../../ui_model/windows/control_events.h"

typedef enum SimRecoveredQuery {
    SIM_RECOVERED_QUERY_WINDOW_OPEN = 1,
    SIM_RECOVERED_QUERY_WINDOW_EVENTS,
    SIM_RECOVERED_QUERY_WINDOW_IN_FRONT,
    SIM_RECOVERED_QUERY_STILL_DOWN,
    SIM_RECOVERED_QUERY_DIALOG_ABORT_OR_CONTINUE,
    SIM_RECOVERED_QUERY_GET_EVENT,
    SIM_RECOVERED_QUERY_GET_OBJECT_RECT,
    SIM_RECOVERED_QUERY_BUTTON,
    /* Exact unsigned BIOS data-area byte at 0040:0017, not Event.modifiers. */
    SIM_RECOVERED_QUERY_DOS_KEYBOARD_FLAGS,
    /* Map a DOS color word through the active driver's low-nibble table. */
    SIM_RECOVERED_QUERY_DRIVER_COLOR
} SimRecoveredQuery;

typedef enum SimRecoveredEffectKind {
    SIM_RECOVERED_EFFECT_MAP_CELL_INVALIDATE = 1,
    SIM_RECOVERED_EFFECT_EDIT_MESSAGE,
    SIM_RECOVERED_EFFECT_PICTURE_STRING_DIALOG,
    SIM_RECOVERED_EFFECT_DEFAULT_WIND_PROMPT,
    SIM_RECOVERED_EFFECT_NEST_MAP_INVALIDATE,
    SIM_RECOVERED_EFFECT_ALARM_SELECTION,
    SIM_RECOVERED_EFFECT_WINDOW_OPERATION,
    SIM_RECOVERED_EFFECT_GRAPHICS_RECT,
    SIM_RECOVERED_EFFECT_GRAPHICS_LINE
} SimRecoveredEffectKind;

typedef enum SimRecoveredWindowOperation {
    SIM_RECOVERED_WINDOW_CLIP_OFF = 1,
    SIM_RECOVERED_WINDOW_CLIP_PUSH,
    SIM_RECOVERED_WINDOW_CLIP_POP,
    SIM_RECOVERED_WINDOW_CLIP_SET,
    SIM_RECOVERED_WINDOW_CLIP_INCLUDE,
    SIM_RECOVERED_WINDOW_CLIP_EXCLUDE,
    SIM_RECOVERED_WINDOW_CLIP_KILL,
    SIM_RECOVERED_WINDOW_DRAW_OBJECT,
    SIM_RECOVERED_WINDOW_FILL_OBJECT,
    SIM_RECOVERED_WINDOW_LOCK,
    SIM_RECOVERED_WINDOW_UNLOCK,
    SIM_RECOVERED_WINDOW_MAKE_SELECTED,
    SIM_RECOVERED_WINDOW_MAKE_UNSELECTED,
    SIM_RECOVERED_WINDOW_MAKE_VISIBLE,
    SIM_RECOVERED_WINDOW_MAKE_INVISIBLE,
    SIM_RECOVERED_WINDOW_UNSELECT_GROUP,
    SIM_RECOVERED_WINDOW_SET_BITMAP,
    SIM_RECOVERED_WINDOW_SET_SELECTED_STATE,
    SIM_RECOVERED_WINDOW_SWAP,
    SIM_RECOVERED_WINDOW_OPEN,
    SIM_RECOVERED_WINDOW_CLOSE,
    SIM_RECOVERED_WINDOW_FLUSH_EVENTS,
    SIM_RECOVERED_WINDOW_SET_MAP_TITLE,
    SIM_RECOVERED_WINDOW_YARD_CLOSED,
    SIM_RECOVERED_WINDOW_DRAW_YARD,
    SIM_RECOVERED_WINDOW_UPDATE_YARD,
    SIM_RECOVERED_WINDOW_DRAW_SIM_PAYOFF,
    SIM_RECOVERED_WINDOW_INVERT_PATCH,
    SIM_RECOVERED_WINDOW_DRAW_HISTORY_GRAPH,
    SIM_RECOVERED_WINDOW_UPDATE_EVERYTHING,
    SIM_RECOVERED_WINDOW_UPDATE_EDIT,
    SIM_RECOVERED_WINDOW_DO_WIN_HELP,
    SIM_RECOVERED_WINDOW_INVALIDATE_MAP,
    SIM_RECOVERED_WINDOW_OVERLAY_TILE_SET,
    SIM_RECOVERED_WINDOW_SET_MENU_ITEM_STATE,
    SIM_RECOVERED_WINDOW_SET_MENU_ITEM_TEXT,
    SIM_RECOVERED_WINDOW_UPDATE_EDIT_IF_OPEN,
    SIM_RECOVERED_WINDOW_DRAW_BITMAP,
    SIM_RECOVERED_WINDOW_PRINTF_AT_OBJECT,
    /* SetEditWinTitle's source DATA expression is "SimAnt" + fd_0368[15] +
     * fd_0324[scenario]; the host resolves that text from loaded resources. */
    SIM_RECOVERED_WINDOW_SET_EDIT_TITLE_FROM_SCENARIO,
    SIM_RECOVERED_WINDOW_DRAW_EDIT_TITLE_OBJECT
} SimRecoveredWindowOperation;

/* Source arguments are retained as machine-sized values. Pointer arguments
 * are borrowed only for the duration of the callback and must not be retained
 * as recovered-state storage. Effect callbacks must complete source-modal
 * work before returning; returning false interrupts and faults the tick. */
typedef struct SimRecoveredEffect {
    SimRecoveredEffectKind kind;
    uintptr_t arguments[5];
} SimRecoveredEffect;

typedef int (*SimRecoveredTickCountProvider)(void *context, int32_t *value);
typedef int (*SimRecoveredQueryProvider)(void *context,
                                        SimRecoveredQuery query,
                                        const uintptr_t *arguments,
                                        uint8_t argument_count,
                                        int32_t *value);
typedef int (*SimRecoveredEffectProvider)(void *context,
                                         const SimRecoveredEffect *effect);
/* Synchronous source EndGameDialog. The input is a snapshot of its current
 * TLS operands and the RNG is borrowed for the modal flow's SRand2 call.
 * Success includes NewGame(0) and any resulting MenuQuit continuation. */
typedef int (*SimRecoveredEndGameProvider)(void *context,
                                           const SimGameOverInput *input,
                                           SimRng *rng);
/* Synchronously runs the source DoScenario(flag) modal selector and returns
 * its raw DOS result code through dos_result. Return zero to reject/fail the
 * active recovered call; an absent provider fails as unsupported DoScenario. */
typedef int (*SimRecoveredScenarioSelectProvider)(void *context, int16_t flag,
                                                  int16_t *dos_result);

typedef struct SimRecoveredHost {
    void *context;
    SimRecoveredTickCountProvider tick_count;
    SimRecoveredQueryProvider query;
    SimRecoveredEffectProvider effect;
    SimRecoveredSongDoneProvider song_done;
    int audio_driver_ready;
    uint16_t screen_width; /* Source g_3DB2: 320 or 640. */
    uint8_t hardware_profile; /* Source g_5A97, supplied by the window host. */
    /* Optional until this host implements the entire source modal flow;
     * reaching EndGameDialog without it is an explicit terminal failure. */
    SimRecoveredEndGameProvider end_game;
    /* Required only when generated NewGame reaches DoScenario. */
    SimRecoveredScenarioSelectProvider scenario_select;
} SimRecoveredHost;

typedef enum SimRecoveredEngineStatus {
    SIM_RECOVERED_ENGINE_OK = 0,
    SIM_RECOVERED_ENGINE_INVALID_ARGUMENT,
    SIM_RECOVERED_ENGINE_SESSION_NOT_READY,
    SIM_RECOVERED_ENGINE_BRIDGE_ERROR,
    SIM_RECOVERED_ENGINE_HOST_REJECTED,
    SIM_RECOVERED_ENGINE_UNSUPPORTED_CALL,
    SIM_RECOVERED_ENGINE_NEST_ERROR,
    SIM_RECOVERED_ENGINE_AUDIO_BIND_ERROR,
    SIM_RECOVERED_ENGINE_FAULTED
} SimRecoveredEngineStatus;

typedef enum SimRecoveredAction {
    SIM_RECOVERED_ACTION_PAUSE = 1,
    SIM_RECOVERED_ACTION_SPEED,
    SIM_RECOVERED_ACTION_PAN, /* Target center cell, source CenterEdit. */
    SIM_RECOVERED_ACTION_SCROLL, /* Source f_0250_0D10 pixel-cell delta. */
    SIM_RECOVERED_ACTION_MAP_PLANE,
    /* Actual source RandYard, preserving the existing recovered state image.
     * a is the caller's scenario (0..3), b must be zero. Requires next4. */
    SIM_RECOVERED_ACTION_RAND_YARD,
    /* Actual S11 ProcMenu. a retains the command word, b must be zero. */
    SIM_RECOVERED_ACTION_PROC_MENU,
    /* Internal dispatcher slot; use the typed control-event API below. */
    SIM_RECOVERED_ACTION_CONTROL_EVENT,
    SIM_RECOVERED_ACTION_HISTORY_EVENT
#ifdef SIMANT_ENABLE_END_GAME_ACTION_DIAGNOSTIC
    /* Test executable only: invoke the source EndGame contract directly on
     * its dedicated session. This does not prove the natural trigger. */
    , SIM_RECOVERED_ACTION_DIAGNOSTIC_END_GAME
#endif
} SimRecoveredAction;

/* Source Event is eight packed 16-bit words. These offsets match
 * src/S22/m39C7.c's processEdit(Event*) and the DOS event-queue producer. */
typedef struct SimRecoveredEvent {
    int16_t what;
    int16_t message;
    int16_t x4;
    int16_t modifiers;
    int16_t h;
    int16_t v;
    int16_t code;
    int16_t xE;
} SimRecoveredEvent;

struct SimRecoveredControlRequest;
typedef struct SimRecoveredEngine {
    SimSession *session; /* Borrowed; must outlive the engine. */
    SimRecoveredHost host;
    RecoveredState recovered; /* Sole source-state authority between ticks. */
    RecoveredBindingFrame binding_frame; /* Stable across host error longjmp. */
    PortableAudioIntents audio_intents;
    SimRecoveredAudioBinding audio_binding;
    SimRecoveredNestBinding nest_binding;
    SimNestRequest nest_request;
    SimNestTrace nest_trace;
    SimRng rng_before_tick;
    PortableAudioIntents audio_before_tick;
    SimRecoveredEngineStatus status;
    const char *failed_service;
    uint64_t completed_ticks;
    uint8_t initialized;
    uint8_t recovered_binding_active;
    uint8_t end_game_modal_active;
    struct SimRecoveredControlRequest *control_request; /* synchronous only */
} SimRecoveredEngine;

typedef enum SimRecoveredEngineInitStatus {
    SIM_RECOVERED_ENGINE_INIT_OK = 0,
    SIM_RECOVERED_ENGINE_INIT_INVALID_ARGUMENT,
    SIM_RECOVERED_ENGINE_INIT_SESSION_NOT_READY,
    SIM_RECOVERED_ENGINE_INIT_BRIDGE_ERROR,
    SIM_RECOVERED_ENGINE_INIT_VIEW_UNAVAILABLE
} SimRecoveredEngineInitStatus;

/* Uses the actual resource-backed NewGame session as the starting projection.
 * The host callbacks are mandatory and must implement the named services,
 * including DOS_KEYBOARD_FLAGS with the live raw BIOS byte;
 * no implicit closed-window, empty-dialog, or clock values are supplied. The
 * generated RecoveredState profile must include its reviewed source DATA
 * initializers; this boundary never patches missing initializer bytes. */
SimRecoveredEngineInitStatus sim_recovered_engine_init(
    SimRecoveredEngine *engine, SimSession *session,
    const SimRecoveredHost *host);

/* Pass a request for deterministic/headless execution: its two TickCount
 * samples are consumed from the static seed lane. Pass NULL for live execution;
 * EnterNest then calls host.tick_count at each original conditional read, so
 * synchronous effects may advance the value before a possible second read.
 * Other TickCount/MacTickCount calls also use host.tick_count. An engine fault
 * is terminal; initialize a new engine from a newly prepared session before
 * trying again. */
SimRecoveredEngineStatus sim_recovered_engine_tick(
    SimRecoveredEngine *engine, const SimNestRequest *nest_clock);

/* Applies source-backed live input. PAUSE uses a=0/1; SPEED uses a=0..3;
 * PAN centers the viewport on logical map cell (a,b), matching CenterEdit;
 * SCROLL applies the original camera delta (a,b), matching f_0250_0D10;
 * MAP_PLANE uses a=0..3. Synchronous window/audio effects may be emitted. */
SimRecoveredEngineStatus sim_recovered_engine_action(
    SimRecoveredEngine *engine, SimRecoveredAction action,
    int16_t a, int16_t b);

/* Dispatches a DOS menu word through S11's distinct event ABI, under the
 * engine's recovered state, RNG, nest and host bindings. Unknown low-byte
 * commands retain the original no-action behavior. Unsupported services
 * fault through the same terminal boundary as other source actions. */
SimRecoveredEngineStatus sim_recovered_engine_proc_menu_command(
    SimRecoveredEngine *engine, uint16_t command);

/* S24 uses an eight-word Event with an unsigned command at byte twelve.
 * The reviewed Next10 profile preserves source private UI state ownership. */
SimRecoveredEngineStatus sim_recovered_engine_history_event(
    SimRecoveredEngine *engine, uint16_t command);

struct PortableHistoryUiSnapshot;
int sim_recovered_engine_history_ui_snapshot(const SimRecoveredEngine *engine,
    struct PortableHistoryUiSnapshot *ui, int16_t *shown_count);

/* Finite DOS-compared control model under the engine's state/RNG boundary.
 * Selector and percent ownership stays with the session/caller across NewGame.
 * Shared triangle geometry is supplied from active source TLS, not inferred
 * from the event's rectangle. No tick or RNG consumption is introduced. */
SimRecoveredEngineStatus sim_recovered_engine_control_event(
    SimRecoveredEngine *engine, SimSetupControlKind kind,
    const SimControlEventMessage *message,
    SimControlEventPrivateState *private_state,
    const SimControlEventProvider *provider);

/* Dispatches one already-translated native event through the original
 * processEdit(Event*) entry. A nonnull clock selects fixed headless samples;
 * NULL selects the live provider if this path enters the nest transition.
 * Event words are not inferred here. */
SimRecoveredEngineStatus sim_recovered_engine_process_edit_event(
    SimRecoveredEngine *engine, const SimRecoveredEvent *event,
    const SimNestRequest *nest_clock);

/* Dispatches an otherwise-unbound DOS logical key through the generated
 * YellowCommandKey. The engine queries the host's exact raw 0x417 flags before
 * entering recovered code and returns the original handled result. A nonnull
 * nest clock selects fixed headless samples; NULL selects the live provider. */
SimRecoveredEngineStatus sim_recovered_engine_yellow_command_key(
    SimRecoveredEngine *engine, int16_t key,
    const SimNestRequest *nest_clock, int16_t *handled);

/* Captures the active TLS-backed recovered state during a synchronous host
 * callback, including writes made earlier in the current recovered call. */
int sim_recovered_engine_snapshot(const SimRecoveredEngine *engine,
                                  RecoveredState *snapshot);

/* Synchronous EndGame continuation only. Calls the selected source NewGame
 * with the currently bound TLS/RNG/host services; never rebuilds or reseeds
 * the session. Other call sites are rejected. Source failures propagate to
 * the enclosing engine call's existing abort boundary. Requires next5. */
int sim_recovered_engine_new_game_from_modal(SimRecoveredEngine *engine,
                                             int16_t option, int16_t *result);

/* Audio requests produced by source calls remain queued as typed intents for
 * the host audio layer. */
int sim_recovered_engine_next_audio(SimRecoveredEngine *engine,
                                    PortableAudioIntent *intent);

const char *sim_recovered_engine_status_string(
    SimRecoveredEngineStatus status);

#endif
