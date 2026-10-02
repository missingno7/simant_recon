#ifndef SIMANT_GAME_RECOVERED_SESSION_BRIDGE_H
#define SIMANT_GAME_RECOVERED_SESSION_BRIDGE_H

#include <stddef.h>
#include "recovered_state.h"
#include "../session.h"

typedef enum SimRecoveredBridgeStatus {
    SIM_RECOVERED_BRIDGE_OK = 0,
    SIM_RECOVERED_BRIDGE_INVALID_ARGUMENT = 1,
    SIM_RECOVERED_BRIDGE_INCONSISTENT_MIRROR = 2,
    SIM_RECOVERED_BRIDGE_VIEW_UNAVAILABLE = 3
} SimRecoveredBridgeStatus;

typedef struct SimRecoveredProjectionEntry {
    const char *source_symbol;
    const char *session_field;
    const char *recovered_view;
} SimRecoveredProjectionEntry;

/* Each listed row is a source-identity mapping. Aliases name one canonical
 * RecoveredState member and never allocate independent duplicate storage. */
const SimRecoveredProjectionEntry *sim_recovered_projection_manifest(size_t *count);

/* Explicitly reported NewGame-written source globals without a typed session
 * owner. Their source DATA initializer remains in force in RecoveredState. */
const char *const *sim_recovered_unmapped_new_game_writes(size_t *count);

/* Start from recovered DATA initializers, then overlay typed fields. After a
 * successful NewGame, a loaded/recalculated Edit viewport resource is required
 * to derive source map invalidation bounds; otherwise VIEW_UNAVAILABLE is
 * returned. No DOS addresses or resource capsules are imported. */
SimRecoveredBridgeStatus sim_recovered_state_from_session(
    RecoveredState *state, SimSession *session);

/* Export only mapped simulation state. Unmapped recovered fields and the
 * recovered object itself are left untouched. */
SimRecoveredBridgeStatus sim_session_from_recovered_state(
    SimSession *session, const RecoveredState *state);

/* RNG is native context state, not a serialized/global RecoveredState field.
 * Bind this pointer through recovered_rng_bind for the duration of a call. */
SimRng *sim_recovered_session_rng(SimSession *session);

#endif
