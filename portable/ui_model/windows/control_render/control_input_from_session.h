#ifndef SIMANT_UI_CONTROL_INPUT_FROM_SESSION_H
#define SIMANT_UI_CONTROL_INPUT_FROM_SESSION_H

#include "control_raster.h"
#include "../../../game/session.h"

typedef enum SimControlSessionInputStatus {
    SIM_CONTROL_SESSION_INPUT_OK = 0,
    SIM_CONTROL_SESSION_INPUT_BAD_ARGUMENT,
    SIM_CONTROL_SESSION_INPUT_INACTIVE_CONTROL,
    SIM_CONTROL_SESSION_INPUT_WINDOW_NOT_CURRENT,
    SIM_CONTROL_SESSION_INPUT_ANIMATION_MISMATCH
} SimControlSessionInputStatus;

/* The original TU-private globals g_1B62/g_1B64 and fd_50F6_0B12 are not
 * stored in SimSession. The live recovered-state owner supplies them here. */
typedef struct SimControlRecoveredVisualState {
    int16_t mode_percent;       /* Current g_1B62, not an assumed initializer. */
    int16_t caste_percent;      /* Current g_1B64, not an assumed initializer. */
    int16_t mode_population[3]; /* Current fd_50F6_0B12[0..2]. */
} SimControlRecoveredVisualState;

/* Handle/object identity is owned by the UI animation provider, not the
 * session's opaque animation_resource pointer. It must name that exact live
 * resource; it is never reconstructed from a copied or retired snapshot. */
typedef struct SimControlActiveAnimation {
    const void *resource;
    uint16_t animation_set_handle;
    uint16_t animation_object_id;
} SimControlActiveAnimation;

typedef struct SimControlRenderBinding {
    SimControlRenderInput input;
    SimControlRasterContext raster;
} SimControlRenderBinding;

/* Construct a one-frame binding from one current SimSession plus its live
 * recovered-private globals. `animation` and `resolve_animation_bitmap` are
 * required only when that session control currently owns an animation set.
 * Rebuild this borrowed binding immediately before each render. */
SimControlSessionInputStatus sim_control_render_binding_from_session(
    SimSession *session,
    const PortableWindowRenderer *active_renderer,
    SimSetupControlKind kind,
    uint16_t draw_flags,
    const SimControlRecoveredVisualState *recovered,
    const SimControlActiveAnimation *animation,
    SimControlAnimationBitmapResolver resolve_animation_bitmap,
    SimControlRenderBinding *binding);

#endif
