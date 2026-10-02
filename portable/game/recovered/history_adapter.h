#ifndef SIMANT_GAME_RECOVERED_HISTORY_ADAPTER_H
#define SIMANT_GAME_RECOVERED_HISTORY_ADAPTER_H

#include <stdint.h>

#include "../../ui_model/windows/history_render.h"

/* Dispatch one source S24 event command. With the Next10 profile selected,
 * this constructs the original 16-byte Event record and calls ProcHistoryEvent.
 * Returns 1 when dispatched and 0 when the profile is unavailable.
 */
int sim_recovered_source_history_event(uint16_t command);

/* Copy S24's currently active private history UI arrays into the renderer
 * snapshot. shown_graph_count receives the non-sentinel count in [0,4].
 * Returns 1 on success and 0 for an invalid argument or unavailable profile.
 */
int sim_recovered_source_history_ui_snapshot(
    PortableHistoryUiSnapshot *ui, int16_t *shown_graph_count);

#endif
