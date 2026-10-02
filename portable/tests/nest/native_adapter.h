#ifndef SIMANT_TESTS_NEST_NATIVE_ADAPTER_H
#define SIMANT_TESTS_NEST_NATIVE_ADAPTER_H

#include <stdint.h>

#include "../../game/simulation/nest.h"

typedef struct SimNestTestWorld {
    uint8_t surface[128][64];
    uint8_t nest_b[64][64];
    uint8_t nest_r[64][64];
    uint8_t exit_b[64][64];
    uint8_t exit_r[64][64];
    uint8_t life_a[128][64];
    uint8_t life_b[64][64];
    uint8_t life_r[64][64];
    uint8_t hole_b[64];
    uint8_t hole_r[64];
    int16_t terrain_set;
    int16_t current_ant_plane;
    int16_t me_x;
    int16_t me_y;
    int16_t me_type;
    int16_t me_direction;
} SimNestTestWorld;

int sim_nest_test_run(SimNestTestWorld *input_output, SimRng *rng,
                      SimNestRuntime *runtime, const SimNestRequest *request,
                      SimNestTrace *trace);

#endif
