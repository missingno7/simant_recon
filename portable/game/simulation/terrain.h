#ifndef SIMANT_GAME_SIMULATION_TERRAIN_H
#define SIMANT_GAME_SIMULATION_TERRAIN_H

#include <stdint.h>

#include "rng.h"
#include "../state/world.h"

typedef enum SimTerrainStatus {
    SIM_TERRAIN_OK = 0,
    SIM_TERRAIN_INVALID_ARGUMENT = 1
} SimTerrainStatus;

/* Source MakeMap(x, y), called by RandWorld as (map_width, map_kind).
 * The recovered caller domain is x=0..11 and y=0..15. Grid writes, ant-lion,
 * sow/pillar state, and S-RNG draws are implemented natively. OverlayTileSet
 * resource intent is retained in typed SimGameWorld fields. */
SimTerrainStatus sim_terrain_build(SimGameWorld *world, SimRng *rng,
                                   int16_t x, int16_t y);

#endif
