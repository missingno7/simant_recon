#ifndef SIMANT_PORTABLE_UI_MODEL_WINDOWS_CONTROL_EVENTS_H
#define SIMANT_PORTABLE_UI_MODEL_WINDOWS_CONTROL_EVENTS_H

#include "../../game/simulation/setup.h"

#include <stdint.h>

typedef enum SimControlEventStatus {
    SIM_CONTROL_EVENT_OK = 0,
    SIM_CONTROL_EVENT_BAD_ARGUMENT,
    SIM_CONTROL_EVENT_UNSUPPORTED_CODE,
    SIM_CONTROL_EVENT_INVALID_SOURCE_STATE,
    SIM_CONTROL_EVENT_PROVIDER_MISSING,
    SIM_CONTROL_EVENT_PROVIDER_FAILED,
    SIM_CONTROL_EVENT_DRAG_LIMIT
} SimControlEventStatus;

typedef struct SimControlEventMessage {
    uint16_t code;
    SimSetupPoint point;
} SimControlEventMessage;

/* ProcModeEvent/ProcCasteEvent depend on DOS window, pointer, and clip
 * services. Each is an explicit host provider boundary. `draw_control` is
 * called with source flags=3 after the source state has been updated. */
typedef struct SimControlEventProvider {
    int (*clip_set_window)(void *context, uint16_t window_id);
    int (*clip_off)(void *context);
    int (*help)(void *context, uint16_t help_context);
    int (*set_group_visible)(void *context, uint16_t window_id,
                             uint8_t group_id, int visible);
    int (*select_object)(void *context, uint16_t object_id);
    int (*get_object_rect)(void *context, uint16_t object_id,
                           SimSetupRect *rect);
    int (*draw_control)(void *context, SimSetupControlKind kind,
                        uint16_t flags, const SimSetupControls *controls,
                        int16_t percent_mode);
    int (*pointer_poll)(void *context, SimSetupPoint *point);
    int (*still_down)(void *context, int *down);
    void *context;
    /* Optional host safety bound. Zero preserves the source's unbounded
     * pointer-poll loop; test providers may set a finite limit. */
    uint16_t max_drag_samples;
} SimControlEventProvider;

/* g_1B62 and g_1B64 live outside SimSetupControls. The owner supplies their
 * current values; they toggle for event codes 0x120f..0x1211 or
 * 0x130f..0x1311 (switch deltas 12, 13, and 14). */
typedef struct SimControlEventPrivateState {
    int16_t mode_percent;
    int16_t caste_percent;
    /* The source TU keeps one shared triWidth/triHeight/triWidthL set. The
     * last InitTriVars call owns these values (startup calls mode then caste).
     * Supply the current recovered values; do not infer them from the event's
     * own rectangle. */
    uint16_t triangle_width;
    uint16_t triangle_height;
    uint16_t triangle_width_left;
} SimControlEventPrivateState;

/* Execute one source event. Preset selector and four-row save/load ordering
 * are kept in SimSetupControls. A drag uses the supplied point for its first
 * sample, then calls pointer_poll and still_down in source order until up.
 * Provider failure stops at the failed boundary; partial source-state writes
 * before that boundary are retained. Mode events can write mode_auto,
 * mode_level, one prior mode_levels row, mode_current, mode_point through the
 * source draw/SetTriLatPoint operation, and mode_percent. Caste events write
 * the corresponding caste members and may also update ideal_caste after an
 * accepted drag. Shared TU triangle geometry is supplied through private_state
 * and is read-only here. No unrelated next4/TLS or engine fields are written. */
SimControlEventStatus sim_control_process_event(
    SimSetupControls *controls, SimControlEventPrivateState *private_state,
    SimSetupControlKind kind, const SimControlEventMessage *message,
    const SimControlEventProvider *provider);

const char *sim_control_event_status_string(SimControlEventStatus status);

#endif
