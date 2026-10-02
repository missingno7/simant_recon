#ifndef SIMANT_TEST_YELLOW_NATIVE_ADAPTER_H
#define SIMANT_TEST_YELLOW_NATIVE_ADAPTER_H

#include "../../game/simulation/yellow.h"
#include "../../game/simulation/ants.h"
#include "../../game/simulation/exit_nest.h"

typedef struct SimYellowTestWorld {
    SimWorldTiles tiles;
    uint8_t exit_b[64][64];
    uint8_t exit_r[64][64];
    uint8_t life_a[128][64];
    uint8_t life_b[64][64];
    uint8_t life_r[64][64];
    uint8_t hole_b[64];
    uint8_t hole_r[64];
    SimAntList ants_a;
    SimSmallAntList ants_b;
    SimSmallAntList ants_r;
    int16_t current_ant_plane;
    int16_t me_x;
    int16_t me_y;
    int16_t me_type;
    int16_t me_direction;
    int16_t me_health;
    int16_t health_warning_threshold;
    uint8_t health_warning;
    uint8_t health_death;
    uint8_t health_force_full;
    uint8_t _padding;
    uint32_t source_counter_0472;
} SimYellowTestWorld;

int sim_yellow_test_run(SimYellowTestWorld *input_output, SimRng *rng,
                        SimNestRuntime *nest_runtime,
                        SimYellowState *state, SimYellowTrace *trace);
int sim_exit_nest_test_run(SimYellowTestWorld *input_output, SimRng *rng,
                           SimNestRuntime *nest_runtime,
                           SimExitNestContext *context,
                           SimMoveTrace *movement_trace,
                           SimNestTrace *nest_trace);

#endif
