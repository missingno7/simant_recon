#ifndef SIMANT_GAME_SIMULATION_EXIT_NEST_H
#define SIMANT_GAME_SIMULATION_EXIT_NEST_H

#include <stdint.h>

#include "movement.h"
#include "nest.h"

typedef struct SimExitNestContext {
    int16_t target_plane;
    SimGridPos target;
    SimGridPos previous;
    int16_t movement_mode;
    int16_t rotation;
    int16_t preferred_direction;
    int16_t map_plane;
    int32_t tick_values[2];
    uint8_t tick_count;
} SimExitNestContext;

typedef enum SimExitNestStatus {
    SIM_EXIT_NEST_OK = 0,
    SIM_EXIT_NEST_INVALID_ARGUMENT = 1,
    SIM_EXIT_NEST_TICK_INPUT_EXHAUSTED = 2,
    SIM_EXIT_NEST_NEST_ERROR = 3,
    SIM_EXIT_NEST_TRACE_OVERFLOW = 4
} SimExitNestStatus;

/* Source-derived ExitNest transition. Host time is supplied explicitly for
 * TryAntTheme; map, Life, hole, RNG, and player mutations remain native. */
SimExitNestStatus sim_exit_nest(SimGameWorld *world, SimRng *rng,
                                SimNestRuntime *runtime,
                                SimExitNestContext *context,
                                SimMoveTrace *movement_trace,
                                SimNestTrace *nest_trace);

#endif
