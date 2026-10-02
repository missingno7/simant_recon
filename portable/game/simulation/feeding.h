#ifndef SIMANT_GAME_SIMULATION_FEEDING_H
#define SIMANT_GAME_SIMULATION_FEEDING_H

#include <stdint.h>

#include "rng.h"
#include "../state/world.h"

typedef struct SimFeedingState {
    int16_t next_food_threshold; /* fd_3D57_0C1A */
} SimFeedingState;

typedef enum SimFeedingEffectKind {
    SIM_FEEDING_SOUND = 1
} SimFeedingEffectKind;

typedef struct SimFeedingEffect {
    uint16_t kind;
    int16_t arguments[3];
} SimFeedingEffect;

enum { SIM_FEEDING_EFFECT_CAPACITY = 4 };

typedef struct SimFeedingTrace {
    uint16_t count;
    uint8_t overflow;
    SimFeedingEffect events[SIM_FEEDING_EFFECT_CAPACITY];
} SimFeedingTrace;

typedef enum SimFeedingStatus {
    SIM_FEEDING_OK = 0,
    SIM_FEEDING_INVALID_ARGUMENT = 1,
    SIM_FEEDING_EFFECTS_FULL = 2
} SimFeedingStatus;

/* Source S08 AddFood and root FeedAnts. The sine table is the 64-word SHARED
 * resource used by fracSIN; sound is returned as an ordered host intent. */
SimFeedingStatus sim_food_add(SimGameWorld *world, SimRng *rng,
                              const int16_t sine_q15[64], int16_t count,
                              int16_t sound, SimFeedingTrace *trace);
SimFeedingStatus sim_feed_ants(SimGameWorld *world, SimRng *rng,
                               SimFeedingState *state,
                               const int16_t sine_q15[64],
                               SimFeedingTrace *trace);

#endif
