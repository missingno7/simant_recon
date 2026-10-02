#ifndef SIMANT_GAME_SIMULATION_POPULATION_H
#define SIMANT_GAME_SIMULATION_POPULATION_H

#include <stdint.h>

#include "rng.h"
#include "../state/world.h"

typedef enum SimPopulationEffectKind {
    SIM_POPULATION_MUSIC = 1,
    SIM_POPULATION_REPORT = 2
} SimPopulationEffectKind;

typedef struct SimPopulationEffect {
    uint16_t kind;
    int16_t values[3];
} SimPopulationEffect;

#define SIM_POPULATION_EFFECT_CAPACITY 8

typedef struct SimPopulationEffects {
    uint16_t count;
    uint8_t overflow;
    SimPopulationEffect events[SIM_POPULATION_EFFECT_CAPACITY];
} SimPopulationEffects;

typedef enum SimPopulationStatus {
    SIM_POPULATION_OK = 0,
    SIM_POPULATION_INVALID_ARGUMENT = 1,
    SIM_POPULATION_INVALID_STATE = 2,
    SIM_POPULATION_EFFECTS_FULL = 3,
    SIM_POPULATION_RNG_ERROR = 4
} SimPopulationStatus;

/* These requests preserve the DOS call order while leaving audio and report
 * presentation to the host adapter. Events append to the caller's queue. */
void sim_population_effects_reset(SimPopulationEffects *effects);

/* Recomputes the 32 raw bins, both six-caste populations, and totals. It also
 * processes queen-loss notifications and their scenario-specific selection
 * or lifetime-graph state. The queue and RNG must be explicit caller inputs. */
SimPopulationStatus sim_population_count_ants(SimGameWorld *world, SimRng *rng,
                                              SimPopulationEffects *effects);

#endif
