#ifndef SIMANT_GAME_SIMULATION_ANTS_H
#define SIMANT_GAME_SIMULATION_ANTS_H

#include <stdbool.h>
#include <stdint.h>

#include "../state/world.h"

/* Add one source-style list entry and publish its Life grid byte. Coordinates
 * must be inside the selected plane; a full list or invalid coordinate leaves
 * the world unchanged and returns false. */
bool sim_ant_add_a(SimGameWorld *world, int16_t x, int16_t y,
                   uint8_t type, uint8_t mode, uint8_t state);
bool sim_ant_add_b(SimGameWorld *world, int16_t x, int16_t y,
                   uint8_t type, uint8_t mode, uint8_t state);
bool sim_ant_add_r(SimGameWorld *world, int16_t x, int16_t y,
                   uint8_t type, uint8_t mode, uint8_t state);

/* Reproduces the count resets in ClearListB/ClearListR. The surface list is
 * rebuilt from LifeA, as in BuildAntListA. Neither operation clears stale
 * slots beyond the new count. */
void sim_ants_reset_lists(SimGameWorld *world);
void sim_ants_rebuild_a(SimGameWorld *world);
void sim_ants_clear_b(SimGameWorld *world);
void sim_ants_clear_r(SimGameWorld *world);
int16_t sim_ants_count(const SimGameWorld *world);

/* Source-derived player helpers used by native InitYelloAnt/worldgen. They
 * accept signed source-sized parameters, reject locations outside the chosen
 * plane, and return whether the SetMyLife request had a valid location. */
bool sim_set_my_life(SimGameWorld *world, int16_t plane, int16_t x, int16_t y,
                     int16_t type, int16_t direction, int16_t value);
void sim_set_my_health(SimGameWorld *world, int16_t health);

#endif
