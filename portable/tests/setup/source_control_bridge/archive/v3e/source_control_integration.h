#ifndef SOURCE_CONTROL_INTEGRATION_DRAFT_H
#define SOURCE_CONTROL_INTEGRATION_DRAFT_H

#include "../recovered_source_next10/generated/recovered_state.h"
#include "portable/ui_model/windows/control_events.h"

#include <stdint.h>

struct CtlMsg { uint8_t pad[8]; struct Pt pt; int16_t code; };

int16_t IsPointInIsoTri(struct Pt *point, struct Rect *rect);
void BoundPointToTri(struct Pt *point, struct Rect *rect);
void ProcModeEvent(struct CtlMsg *message);
void ProcCasteEvent(struct CtlMsg *message);
void cvtLevels2IdealCaste(int16_t *ideal);

/* Called from an already-bound Next10 engine action. Selectors point directly
 * into SimSetupControls; percentages point directly into the caller's live
 * private-state owner. No persistent selector/percentage copy is created. */
SimControlEventStatus sim_recovered_source_control_event(
    SimSetupControls *controls, SimControlEventPrivateState *private_state,
    SimSetupControlKind kind, const SimControlEventMessage *message,
    const SimControlEventProvider *provider);

/* Required in the engine's outer abort/longjmp cleanup path. A host callback
 * that interrupts the enclosing recovered action can bypass this TU's local
 * setjmp cleanup; the caller must clear the borrowed binding before it ends
 * the RecoveredState binding frame. */
void sim_recovered_source_control_abort_cleanup(void);

/* Active per-call aliases used by mechanically extracted source bodies. */
extern _Thread_local int16_t *source_mode_selector;
extern _Thread_local int16_t *source_caste_selector;
extern _Thread_local int16_t *source_mode_percent;
extern _Thread_local int16_t *source_caste_percent;

void source_clip_set(int16_t window_id);
void source_clip_off(void);
void source_help(int16_t help_context);
void source_group_invisible(int16_t window_id, int16_t group_id);
void source_group_visible(int16_t window_id, int16_t group_id);
void source_select_object(int16_t object_id);
void source_get_rect(int16_t object_id, struct Rect *rect);
void source_draw_mode(int16_t flags);
void source_draw_caste(int16_t flags);
void source_pointer_update(struct Pt *point);
int16_t source_still_down(void);
void *source_copy_bytes(void *destination, const void *source, uint16_t count);
int16_t source_compare_bytes(const void *left, const void *right, uint16_t count);
void source_GetTriLatDist(uint16_t *level, struct TriPoints *tri, struct Pt *point);

#endif
