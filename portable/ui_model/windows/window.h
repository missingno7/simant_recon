#ifndef SIMANT_PORTABLE_UI_MODEL_WINDOWS_WINDOW_H
#define SIMANT_PORTABLE_UI_MODEL_WINDOWS_WINDOW_H

#include "../../game/resources/database.h"

#include <stddef.h>
#include <stdint.h>

typedef struct PortableWindowRect {
    int16_t left, top, right, bottom;
} PortableWindowRect;

typedef struct PortableWindowObject {
    uint16_t resource_offset;
    uint16_t resource_size;
    PortableWindowRect rect;
    int16_t offsets[4]; /* Object origin/size terms at resource offset 0x08. */
    uint8_t group;
    uint8_t type;
    uint16_t flags;
    uint16_t value;
    int16_t indices[4]; /* Origin/size source indices at object offset 0x10. */
    int16_t modes[4];   /* Axis modes at object offset 0x18. */
    const uint8_t *resource_bytes; /* Borrowed from the immutable record. */
    int16_t bitmap_override; /* Mutable source +0x28 for type 6 only. */
    uint8_t has_bitmap_override;
} PortableWindowObject;

typedef struct PortableWindowResource {
    int16_t resource_id;
    uint16_t count;
    PortableWindowRect rect;
    uint16_t flags;
    const uint8_t *record_bytes; /* Borrowed. Caller retains PortableDbRecord. */
    size_t record_size;
    PortableWindowObject *objects;
} PortableWindowResource;

typedef enum PortableWindowStatus {
    PORTABLE_WINDOW_OK = 0,
    PORTABLE_WINDOW_BAD_ARGUMENT,
    PORTABLE_WINDOW_WRONG_RESOURCE,
    PORTABLE_WINDOW_TRUNCATED,
    PORTABLE_WINDOW_BAD_LAYOUT,
    PORTABLE_WINDOW_UNSUPPORTED_CONSTRAINT,
    PORTABLE_WINDOW_OUT_OF_MEMORY
} PortableWindowStatus;

typedef struct PortableWindowPoint { int16_t x, y; } PortableWindowPoint;

/* Parses kind-0 ordinary window resources; strings and bytes remain borrowed. */
PortableWindowStatus portable_window_decode(const PortableDbRecord *record,
                                             PortableWindowResource *window);
/* Native win_Recalc for same-window references and explicit open arguments. */
PortableWindowStatus portable_window_recalculate(PortableWindowResource *window,
                                                 const int16_t window_args[4]);
/* Apply win_LoadWindow's saved-origin row from win_offsets (8 bytes per ID). */
PortableWindowStatus portable_window_apply_origin_profile(
    PortableWindowResource *window, const uint8_t *profile, size_t profile_size);
void portable_window_release(PortableWindowResource *window);
const char *portable_window_status_string(PortableWindowStatus status);

/* DOS f_1FD2_04E5 containment: left/top inclusive, right/bottom exclusive. */
int portable_window_rect_contains(const PortableWindowRect *rect,
                                  PortableWindowPoint point);
/* DOS f_218D_052F order: first selectable hit, object zero is the frame. */
int portable_window_hit_test(const PortableWindowResource *window,
                             PortableWindowPoint point);
/* Source f_2505_0831 registration + f_1B73_0CEF mouse scan: selectable
 * objects are prepended in ascending registration order, so later (higher)
 * object indices win. Edges are inclusive. Frame chrome registration and
 * dynamic hotbox re-registration are outside this object-only helper. */
int portable_window_mouse_hit_test(const PortableWindowResource *window,
                                   PortableWindowPoint point);

typedef enum PortableWindowRenderStepKind {
    PORTABLE_WINDOW_HOOK_BEFORE = 0,
    PORTABLE_WINDOW_DRAW_OBJECT,
    PORTABLE_WINDOW_DRAW_FRAME,
    PORTABLE_WINDOW_HOOK_AFTER
} PortableWindowRenderStepKind;

typedef struct PortableWindowRenderStep {
    PortableWindowRenderStepKind kind;
    uint16_t object_index; /* Used only by DRAW_OBJECT. */
} PortableWindowRenderStep;

/* Ordered logical trace for win_DrawWindow; does not issue drawing calls. */
size_t portable_window_render_trace(const PortableWindowResource *window,
                                    int surface_ready,
                                    int draw_hook_enabled,
                                    PortableWindowRenderStep *steps,
                                    size_t capacity);

/* Object flag bits and window flag bits used by the original manager. */
enum {
    PORTABLE_WINDOW_OBJECT_VISIBLE = 0x0001,
    PORTABLE_WINDOW_OBJECT_SELECTABLE = 0x0002,
    PORTABLE_WINDOW_OBJECT_SELECTED = 0x0004,
    PORTABLE_WINDOW_OBJECT_DIRTY = 0x0010,
    PORTABLE_WINDOW_OBJECT_EXCLUSIVE_GROUP = 0x0020,
    PORTABLE_WINDOW_OPEN = 0x0200,
    PORTABLE_WINDOW_NO_CLOSE_ON_CLICK = 0x0040,
    PORTABLE_WINDOW_MOVABLE = 0x1000,
    PORTABLE_WINDOW_CLOSE_ON_SWITCH = 0x0001
};

/* Apply the same flag-only group state transitions as win_SetGroup*State. */
void portable_window_set_group_visible(PortableWindowResource *window,
                                       uint8_t group, int visible);
void portable_window_set_group_selectable(PortableWindowResource *window,
                                          uint8_t group, int selectable);
void portable_window_set_group_selected(PortableWindowResource *window,
                                        uint8_t group, int selected);

/* The key/event result table used by S15 o15_384C_0239, without UI labels. */
int portable_window_dialog_result(int16_t window_id,
                                  int event_code,
                                  uint8_t ascii_key,
                                  int *result);

typedef enum PortableScenarioAction {
    PORTABLE_SCENARIO_UNRECOGNIZED = 0,
    PORTABLE_SCENARIO_START,
    PORTABLE_SCENARIO_CANCEL,
    PORTABLE_SCENARIO_CONFIRM_TRANSFER
} PortableScenarioAction;

/* NewGame's result handling in S15 m384C; scenario values are source IDs. */
PortableScenarioAction portable_newgame_scenario_action(int result_code,
                                                        int *scenario_id);

/* Current mutable window state is kept separate from resource bytes. */
typedef struct PortableWindowState {
    PortableWindowRect origin;
    PortableWindowRect saved_origin;
    uint16_t flags;
    uint16_t lock_depth;
    uint8_t has_saved_origin;
} PortableWindowState;

void portable_window_lock(PortableWindowState *state);
int portable_window_unlock(PortableWindowState *state);
void portable_window_set_origin(PortableWindowState *state,
                               PortableWindowRect origin);
int portable_window_open(PortableWindowState *state);
int portable_window_close(PortableWindowState *state);

#endif
