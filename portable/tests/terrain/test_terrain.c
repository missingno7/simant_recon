#include "../../game/simulation/terrain.h"

#include <assert.h>
#include <stdio.h>
#include <string.h>

static void test_invalid_call_is_inert(void)
{
    SimGameWorld world;
    SimRng rng = {0x4321, 0};
    SimGameWorld before;
    SimRng rng_before = rng;

    memset(&world, 0x5a, sizeof world);
    before = world;
    assert(sim_terrain_build(0, &rng, 0, 0) == SIM_TERRAIN_INVALID_ARGUMENT);
    assert(sim_terrain_build(&world, 0, 0, 0) == SIM_TERRAIN_INVALID_ARGUMENT);
    assert(sim_terrain_build(&world, &rng, -1, 0) == SIM_TERRAIN_INVALID_ARGUMENT);
    assert(sim_terrain_build(&world, &rng, 12, 0) == SIM_TERRAIN_INVALID_ARGUMENT);
    assert(sim_terrain_build(&world, &rng, 0, 16) == SIM_TERRAIN_INVALID_ARGUMENT);
    assert(memcmp(&world, &before, sizeof world) == 0);
    assert(memcmp(&rng, &rng_before, sizeof rng) == 0);
}

static void test_source_patch_selection_and_outputs(void)
{
    SimGameWorld world;
    SimRng rng = {0x2345, 0};
    int x, y;

    memset(&world, 0, sizeof world);
    world.tiles.terrain_set = 1;
    assert(sim_terrain_build(&world, &rng, 0, 0) == SIM_TERRAIN_OK);
    assert(world.drop_direction == 2);
    assert(world.tiles.surface[0][0] == 0x67);
    assert(world.tiles.surface[0x25][0x1a] == 0x53);
    assert(world.tiles.surface[0x3e][0x1d] == 0x4d);
    assert(world.tiles.surface[0x7f][0x17] == 0x68);

    memset(&world, 0, sizeof world);
    world.tiles.terrain_set = 1;
    assert(sim_terrain_build(&world, &rng, 0, 2) == SIM_TERRAIN_OK);
    assert(world.tiles.surface[1][1] == 1);
    assert(world.tiles.surface[1][17] == 0);
    assert(world.tiles.surface[17][1] == 0);
    assert(world.tiles.surface[17][17] == 1);
    assert(world.tiles.surface[0][0] == 0x5c);
    assert(world.tiles.surface[1][0] == 0x61);
    assert(world.drop_direction == 0);

    memset(&world, 0, sizeof world);
    world.tiles.terrain_set = 1;
    assert(sim_terrain_build(&world, &rng, 2, 5) == SIM_TERRAIN_OK);
    assert(world.drop_direction == 2);
    for (x = 0; x < 128; ++x)
        for (y = 0; y < 64; ++y)
            assert(world.tiles.surface[x][y] == 0);
}

static void test_carpet_random_draws_and_overlay_intent(void)
{
    SimGameWorld world;
    SimRng rng = {0x4567, 0};
    uint16_t before = rng.s_state;
    int x, y;

    memset(&world, 0, sizeof world);
    world.tiles.terrain_set = 1;
    assert(sim_terrain_build(&world, &rng, 0, 4) == SIM_TERRAIN_OK);
    assert(rng.s_state != before);
    assert(world.drop_direction == 1);
    assert(world.tiles.surface[2][0x19] == 0x53);
    assert(world.tiles.surface[0x7f][0x3f] == 3 ||
           world.tiles.surface[0x7f][0x3f] == 0x3e ||
           world.tiles.surface[0x7f][0x3f] == 0x3f);

    memset(&world, 0, sizeof world);
    world.tiles.terrain_set = 7;
    assert(sim_terrain_build(&world, &rng, 0, 2) == SIM_TERRAIN_OK);
    assert(world.current_ground_tile_id == 0x3e9);
    assert(world.overlay_type == 0 && world.overlay_id == 0x3e9);
    assert(world.overlay_resource_set == 1 && world.overlay_width == 0x90);
    for (x = 0; x < 128; ++x)
        for (y = 0; y < 64; ++y)
            assert(world.tiles.surface[x][y] < 0x80);
}

static void test_yard_state_and_overlay_intent(void)
{
    SimGameWorld world;
    SimRng rng = {0xACE1, 0};
    uint16_t before = rng.s_state;
    int x, y;
    int changed = 0;

    memset(&world, 0, sizeof world);
    world.tiles.terrain_set = 0;
    assert(sim_terrain_build(&world, &rng, 3, 6) == SIM_TERRAIN_OK);
    assert(rng.s_state != before);
    assert(world.current_ground_tile_id == 0);
    assert(world.ant_lion_count >= 0 && world.ant_lion_count <= 4);
    assert(world.initial_ant_lions >= 1 && world.initial_ant_lions <= 4);
    assert(world.pillar_state == 0 && world.pillar_x == 0 && world.pillar_y == 0);
    for (x = 0; x < 128; ++x)
        for (y = 0; y < 64; ++y)
            if (world.tiles.surface[x][y] != 0)
                changed = 1;
    assert(changed);
    assert(world.sow_x[0] == 0 && world.sow_y[0] == 0);
    assert(world.sow_x[1] >= 0 && world.sow_x[1] < 128);
    assert(world.sow_x[2] >= 0 && world.sow_x[2] < 128);
    assert(world.sow_y[1] >= 0 && world.sow_y[1] < 64);
    assert(world.sow_y[2] >= 0 && world.sow_y[2] < 64);
    assert(world.sow_direction[1] >= 0 && world.sow_direction[1] < 8);
    assert(world.sow_direction[2] >= 0 && world.sow_direction[2] < 8);
    assert(world.sow_saved_tile[1] < 16 && world.sow_saved_tile[2] < 16);

    memset(&world, 0, sizeof world);
    world.tiles.terrain_set = 2;
    assert(sim_terrain_build(&world, &rng, 3, 6) == SIM_TERRAIN_OK);
    assert(world.current_ground_tile_id == 0x3e8);
    assert(world.overlay_type == 0 && world.overlay_id == 0x3e8);
    assert(world.overlay_resource_set == 0 && world.overlay_width == 0x50);
    assert(world.tiles.terrain_set == 0);
}

int main(void)
{
    test_invalid_call_is_inert();
    test_source_patch_selection_and_outputs();
    test_carpet_random_draws_and_overlay_intent();
    test_yard_state_and_overlay_intent();
    puts("terrain source-semantics tests passed");
    return 0;
}
