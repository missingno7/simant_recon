#ifndef SIMANT_GAME_SIMULATION_SCENT_H
#define SIMANT_GAME_SIMULATION_SCENT_H

#include <stdint.h>

#include "../state/world.h"

typedef struct SimScentState {
    uint8_t smooth_alarm_work[SIM_PHEROMONE_WIDTH][SIM_PHEROMONE_HEIGHT];
    /* Exact source buffer fd_3E1D_C89F; separate from D89F/world.pheromone_aux. */
} SimScentState;

typedef enum SimScentStatus {
    SIM_SCENT_OK = 0,
    SIM_SCENT_INVALID_ARGUMENT = 1
} SimScentStatus;

/* Source-mapped pure pheromone operations from root m1496.c. They preserve
 * DOS x-major traversal and byte-width updates. These are children used by
 * DoSmells, not a claim that its list/count/history branches are implemented. */
SimScentStatus sim_scent_colony_smell_black_nest(SimGameWorld *world);
SimScentStatus sim_scent_colony_smell_red_nest(SimGameWorld *world);
SimScentStatus sim_scent_colony_smell_black_trail(SimGameWorld *world);
SimScentStatus sim_scent_colony_smell_red_trail(SimGameWorld *world);
SimScentStatus sim_scent_smooth_alarm(SimGameWorld *world,
                                      SimScentState *state);

#endif
