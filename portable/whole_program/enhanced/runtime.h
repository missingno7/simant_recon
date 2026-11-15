#ifndef SIMANT_ENHANCED_RUNTIME_H
#define SIMANT_ENHANCED_RUNTIME_H
#include "snapshot.h"

/* Engine-side only, never call from a paint/input callback. Opt-in contract
 * preview through SIMANT_ENHANCED_CONTRACTS=1; ordinary classic is inert. */
int enhanced_contracts_enabled(void);
/* Presentation-only switch; publication/execution remains independent. */
int enhanced_world_enabled(void);
void enhanced_publish(EnhancedSeam seam);
void enhanced_source_poll(void);
uint16_t enhanced_window_flags(int16_t owner);

#endif
