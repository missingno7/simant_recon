#ifndef SIMANT_GAME_SIMULATION_WATER_H
#define SIMANT_GAME_SIMULATION_WATER_H

#include <stdint.h>

#include "rng.h"
#include "../state/world.h"

enum { SIM_WATER_DROP_CAPACITY = 100, SIM_WATER_MAX_INTENTS = 256 };

typedef struct SimWaterState {
    uint8_t drop_x[SIM_WATER_DROP_CAPACITY]; /* fd_50F6_0256 */
    uint8_t drop_y[SIM_WATER_DROP_CAPACITY]; /* fd_50F6_02C0 */
    int16_t drop_scan_transition;            /* fd_3D57_0C1E */
} SimWaterState;

typedef enum SimWaterIntentKind {
    SIM_WATER_INTENT_SOUND = 1,
    SIM_WATER_INTENT_MAP_INVALIDATION = 2
} SimWaterIntentKind;

typedef struct SimWaterIntent {
    SimWaterIntentKind kind;
    int16_t first;
    int16_t second;
    int16_t third;
} SimWaterIntent;

typedef struct SimWaterTrace {
    uint16_t count;
    SimWaterIntent intents[SIM_WATER_MAX_INTENTS];
} SimWaterTrace;

typedef enum SimWaterStatus {
    SIM_WATER_OK = 0,
    SIM_WATER_INVALID_ARGUMENT = 1,
    SIM_WATER_TRACE_FULL = 2
} SimWaterStatus;

/* rain_enabled is the current SimYardScene.rain_on input. Water height is
 * world->source_counter_0242; neither is duplicated in SimWaterState. */
SimWaterStatus sim_water_init(SimGameWorld *world, SimRng *rng,
                              SimWaterState *state, SimWaterTrace *trace);
SimWaterStatus sim_water_tick(SimGameWorld *world, SimRng *rng,
                              SimWaterState *state, int16_t rain_enabled,
                              SimWaterTrace *trace);
SimWaterStatus sim_water_place_drop(SimGameWorld *world, SimRng *rng,
                                    SimWaterState *state, int16_t index,
                                    SimWaterTrace *trace);
SimWaterStatus sim_water_add_row(SimGameWorld *world, SimRng *rng,
                                 SimWaterState *state, int16_t y,
                                 SimWaterTrace *trace);
SimWaterStatus sim_water_drop_row(SimGameWorld *world, SimRng *rng,
                                  SimWaterState *state, int16_t y,
                                  SimWaterTrace *trace);

#endif
