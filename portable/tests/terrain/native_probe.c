#include "../../game/simulation/terrain.h"

#include <string.h>

enum { SIM_TERRAIN_PROBE_BYTES = 8192 + 14 + 6 + 50 + 24 + 22 + 2 };

int sim_terrain_probe(uint16_t seed, int16_t terrain_set, int16_t x, int16_t y,
                      uint8_t *output, size_t output_size)
{
    SimGameWorld world;
    SimRng rng;
    size_t at = 0;
    SimTerrainStatus status;

    if (output == 0 || output_size < SIM_TERRAIN_PROBE_BYTES)
        return SIM_TERRAIN_INVALID_ARGUMENT;
    memset(&world, 0, sizeof world);
    rng.s_state = seed;
    rng.c_state = 0;
    world.tiles.terrain_set = terrain_set;
    status = sim_terrain_build(&world, &rng, x, y);
    if (status != SIM_TERRAIN_OK)
        return status;

    memcpy(output + at, world.tiles.surface, sizeof world.tiles.surface);
    at += sizeof world.tiles.surface;
#define COPY_FIELD(field) do { memcpy(output + at, &(field), sizeof(field)); at += sizeof(field); } while (0)
    COPY_FIELD(world.current_ground_tile_id);
    COPY_FIELD(world.drop_direction);
    COPY_FIELD(world.tiles.terrain_set);
    COPY_FIELD(world.overlay_type);
    COPY_FIELD(world.overlay_id);
    COPY_FIELD(world.overlay_resource_set);
    COPY_FIELD(world.overlay_width);
    COPY_FIELD(world.ant_lion_count);
    COPY_FIELD(world.initial_ant_lions);
    COPY_FIELD(world.ants_eaten_by_lions);
    memcpy(output + at, world.ant_lions, sizeof world.ant_lions);
    at += sizeof world.ant_lions;
    COPY_FIELD(world.sow_x);
    COPY_FIELD(world.sow_y);
    COPY_FIELD(world.sow_direction);
    COPY_FIELD(world.sow_saved_tile);
    COPY_FIELD(world.pillar_state);
    COPY_FIELD(world.pillar_x);
    COPY_FIELD(world.pillar_y);
    COPY_FIELD(world.pillar_segment);
    COPY_FIELD(world.pillar_direction);
    COPY_FIELD(world.pillar_map);
    COPY_FIELD(rng.s_state);
#undef COPY_FIELD
    return at == SIM_TERRAIN_PROBE_BYTES ? SIM_TERRAIN_OK : -1;
}
