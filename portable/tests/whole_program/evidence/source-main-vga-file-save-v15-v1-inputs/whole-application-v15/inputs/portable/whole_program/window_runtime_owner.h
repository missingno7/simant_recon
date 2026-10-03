#ifndef SIMANT_WHOLE_PROGRAM_WINDOW_RUNTIME_OWNER_H
#define SIMANT_WHOLE_PROGRAM_WINDOW_RUNTIME_OWNER_H

#include "window_refs.h"

/* The recovered source TUs refer to this one process-wide owner.  Its BSS
 * zero state is a valid empty registry before the first window is loaded. */
extern SimWindowRefRegistry sim_window_ref_registry;

/* Explicit cold-start entry for hosts/tests.  It refuses to reset live
 * bindings, so callers cannot silently orphan a window's native sidecars. */
int sim_window_runtime_owner_init(void);

#endif
