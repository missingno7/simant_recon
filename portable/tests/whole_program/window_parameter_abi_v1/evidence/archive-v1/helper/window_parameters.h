#ifndef SIMANT_WHOLE_PROGRAM_WINDOW_PARAMETERS_H
#define SIMANT_WHOLE_PROGRAM_WINDOW_PARAMETERS_H

#include "window_refs.h"

typedef enum SimWindowParameterStatus {
    SIM_WINDOW_PARAMETERS_OK = 0,
    SIM_WINDOW_PARAMETERS_BAD_ARGUMENT,
    SIM_WINDOW_PARAMETERS_UNBOUND_WINDOW,
    SIM_WINDOW_PARAMETERS_STALE_BUFFER,
    SIM_WINDOW_PARAMETERS_BAD_SUPPLIED_COUNT,
    SIM_WINDOW_PARAMETERS_BAD_OBJECT_VIEW,
    SIM_WINDOW_PARAMETERS_MISSING_SOURCE_PARAMETER
} SimWindowParameterStatus;

/* Store the optional words which win_Open supplies to win_Recalc. Before
 * touching window+0x10, inspect the actual bound source object records. Every
 * coordinate axis using source mode 5 must reference one of the caller's
 * supplied words. Unused native slots are explicit zeros supplied by the
 * converted call sites; DOS stack contents are never consulted. */
SimWindowParameterStatus sim_window_parameters_store_open(
    SimWindowRefRegistry *registry, int16_t source_window,
    char *window_buffer, int16_t supplied_count,
    int16_t p0, int16_t p1, int16_t p2, int16_t p3);

const char *sim_window_parameters_status_string(SimWindowParameterStatus status);

#endif
