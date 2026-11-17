#ifndef SIMANT_ENHANCED_RUNTIME_H
#define SIMANT_ENHANCED_RUNTIME_H
#include "snapshot.h"
#include "portable/platform/host.h"

/* Engine-side only, never call from a paint/input callback. --windows enables
 * contracts unless SIMANT_ENHANCED_CONTRACTS=0; ordinary classic is inert. */
int enhanced_contracts_enabled(void);
/* Presentation-only switch; publication/execution remains independent. */
int enhanced_world_enabled(void);
void enhanced_publish(EnhancedSeam seam);
void enhanced_source_poll(void);
uint16_t enhanced_window_flags(int16_t owner);
/* Native device for the original proximity transaction, never a command handler. */
int enhanced_proximity_owner(void);
int enhanced_minimap_owner(void);
int enhanced_cancel_credits(void);
int enhanced_experiment_menu_active(void);
int enhanced_experiment_input(HostInputState *);
int enhanced_compatibility_owner(void);
int enhanced_game_ready(void);

#endif
