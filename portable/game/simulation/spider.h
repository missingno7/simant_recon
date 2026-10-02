#ifndef SIMANT_GAME_SIMULATION_SPIDER_H
#define SIMANT_GAME_SIMULATION_SPIDER_H

#include <stdint.h>

#include "rng.h"
#include "../state/world.h"

typedef struct SimSpiderState {
    int16_t direction;
    int16_t x16;
    int16_t y16;
    int16_t burp_count;
    int16_t eat_count;
    int16_t corpse_base;
    int16_t cycle;
    int16_t cycle2;
    int16_t revenge;
    int16_t state_flag;
    int16_t target_mode;
    int16_t mode;
    int16_t aux_mode;
    int16_t target;
    int16_t target_life;
    int16_t user_x;
    int16_t user_y;
    int16_t corpse_index; /* fd_50F6_0476: DeadAntHere's ring cursor */
    uint8_t corpse_x[100];
    uint8_t corpse_y[100];
    const int16_t *sine_q15;
} SimSpiderState;

typedef struct SimSpiderLaser {
    int16_t from_x16;
    int16_t from_y16;
    int16_t to_x16;
    int16_t to_y16;
    uint8_t fired;
} SimSpiderLaser;

/* InitSpider initializes only spider-owned globals. The corpse history arrays
 * are retained, matching the original initializer's SCorpseBase-only reset. */
void sim_spider_init(SimSpiderState *state, const SimGameWorld *world);
const int16_t *sim_spider_sine_table(void);

/* Runs one scan. `sine_q15` must point to the 64 values loaded from the game's
 * sine resource; laser coordinates are reported as a logical event. */
int16_t sim_spider_scan(SimSpiderState *state, SimGameWorld *world,
                        SimRng *rng, SimSpiderLaser *laser);

#endif
