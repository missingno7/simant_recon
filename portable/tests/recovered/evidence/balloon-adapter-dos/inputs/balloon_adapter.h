#ifndef SIMANT_GAME_RECOVERED_BALLOON_ADAPTER_H
#define SIMANT_GAME_RECOVERED_BALLOON_ADAPTER_H

#include <stdint.h>

#include "recovered_state.h"
#include "../../ui_model/balloons/balloons.h"

/* Source-state adapters for EggBalloons/FightBalloons/QueenBalloons/
 * RestBalloons. They operate on the active next3 recovered TLS binding and
 * retain no persistent balloon state of their own. Call only between
 * recovered_bind_begin/end. */
void sim_recovered_egg_balloons(int16_t x, int16_t y, int16_t plane);
void sim_recovered_fight_balloons(int16_t x, int16_t y, int16_t plane);
void sim_recovered_queen_balloons(int16_t x, int16_t y, int16_t plane);
void sim_recovered_rest_balloons(int16_t x, int16_t y, int16_t plane);

/* Exact DoAntSim mode-1 cue-field reset. The recovered source body currently
 * performs this reset directly; this adapter entry is useful to isolate and
 * test that source-state transition. */
void sim_recovered_balloons_simulation_reset(int16_t simulation_mode);

#endif
