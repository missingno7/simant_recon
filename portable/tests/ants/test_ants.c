#include "../../game/simulation/ants.h"

#include <assert.h>
#include <stdio.h>
#include <string.h>

static void test_add_lists_and_limits(void)
{
    SimGameWorld world;
    int i;

    memset(&world, 0, sizeof world);
    assert(sim_ant_add_a(&world, 127, 63, 0x81, 3, 0x78));
    assert(world.ants_a.count == 1);
    assert(world.ants_a.x[0] == 127 && world.ants_a.y[0] == 63);
    assert(world.ants_a.type[0] == 0x81 && world.ants_a.mode[0] == 3);
    assert(world.ants_a.state[0] == 0x78 && world.life_a[127][63] == 0x81);
    assert(sim_ant_add_b(&world, 63, 62, 0x68, 9, 4));
    assert(world.ants_b.count == 1 && world.life_b[63][62] == 0x68);
    assert(world.ants_b.x[0] == 63 && world.ants_b.y[0] == 62);
    assert(sim_ant_add_r(&world, 0, 0, 0xe0, 7, 2));
    assert(world.ants_r.count == 1 && world.life_r[0][0] == 0xe0);

    assert(!sim_ant_add_a(&world, -1, 0, 1, 2, 3));
    assert(!sim_ant_add_a(&world, 128, 0, 1, 2, 3));
    assert(!sim_ant_add_b(&world, 64, 0, 1, 2, 3));
    assert(!sim_ant_add_r(&world, 0, 64, 1, 2, 3));
    assert(world.ants_a.count == 1 && world.ants_b.count == 1 && world.ants_r.count == 1);

    world.ants_b.type[0] = 0x68;
    world.ants_r.type[0] = 0xe0;
    sim_ants_clear_b(&world);
    assert(world.ants_b.count == 0 && world.ants_b.type[0] == 0x68);
    assert(world.ants_r.count == 1);
    sim_ants_clear_r(&world);
    assert(world.ants_r.count == 0 && world.ants_r.type[0] == 0xe0);
    sim_ants_reset_lists(&world);
    assert(sim_ants_count(&world) == 0);
    for (i = 0; i < SIM_A_ANT_CAPACITY; ++i)
        assert(sim_ant_add_a(&world, (int16_t)(i % SIM_WORLD_WIDTH),
                             (int16_t)(i / SIM_WORLD_WIDTH), 1, 2, 0));
    assert(world.ants_a.count == SIM_A_ANT_CAPACITY);
    assert(!sim_ant_add_a(&world, 0, 0, 2, 3, 4));
    for (i = 0; i < SIM_B_ANT_CAPACITY; ++i) {
        int16_t x = (int16_t)(i % SIM_NEST_WIDTH);
        int16_t y = (int16_t)(i / SIM_NEST_WIDTH);
        assert(sim_ant_add_b(&world, x, y, 2, 3, 4));
        assert(sim_ant_add_r(&world, x, y, 3, 5, 6));
    }
    assert(world.ants_b.count == SIM_B_ANT_CAPACITY);
    assert(world.ants_r.count == SIM_R_ANT_CAPACITY);
    assert(!sim_ant_add_b(&world, 0, 0, 2, 3, 4));
    assert(!sim_ant_add_r(&world, 0, 0, 2, 3, 4));
}

static void test_rebuild_surface_list(void)
{
    SimGameWorld world;

    memset(&world, 0, sizeof world);
    world.life_a[0][2] = 0x10;
    world.life_a[1][0] = 0xff;
    world.life_a[1][1] = 0xfe;
    world.life_a[1][2] = 0x81;
    sim_ants_rebuild_a(&world);
    assert(world.ants_a.count == 2);
    assert(world.ants_a.x[0] == 0 && world.ants_a.y[0] == 2);
    assert(world.ants_a.x[1] == 1 && world.ants_a.y[1] == 2);
    assert(world.ants_a.mode[0] == 2 && world.ants_a.mode[1] == 2);
    assert(world.ants_a.type[0] == 0x10 && world.ants_a.type[1] == 0x81);
    assert(world.ants_a.state[0] == 0 && world.ants_a.state[1] == 0);
}

static void test_set_my_life_boundaries(void)
{
    SimGameWorld world;

    memset(&world, 0, sizeof world);
    assert(sim_set_my_life(&world, 2, 20, 10, 0x60, 2, 0xff));
    assert(world.life_b[20][10] == 0xff);
    /* Direction 2 points northeast, so its opposite tail is west. */
    assert(world.life_b[19][10] == 0xfe);
    assert(world.current_ant_plane == 2 && world.me_x == 20 && world.me_y == 10);
    assert(world.me_type == 0x60 && world.me_direction == 2);

    assert(sim_set_my_life(&world, 1, 127, 63, 0x40, 0, 0));
    assert(world.life_a[127][63] == 0);
    assert(world.me_x == 20 && world.me_y == 10 && world.current_ant_plane == 2);
    assert(!sim_set_my_life(&world, 3, 64, 0, 0x40, 0, 0xff));
    assert(world.life_r[63][0] == 0);
}

static void test_set_my_health_boundaries(void)
{
    SimGameWorld world;

    memset(&world, 0, sizeof world);
    world.health_warning_threshold = 50;
    world.health_death = 1;
    sim_set_my_health(&world, 51);
    assert(world.me_health == 51 && world.health_death == 0 && world.health_warning == 0);
    sim_set_my_health(&world, 50);
    assert(world.me_health == 50 && world.health_warning == 1);
    sim_set_my_health(&world, -1);
    assert(world.me_health == 0 && world.health_warning == 1);
    sim_set_my_health(&world, 101);
    assert(world.me_health == 100 && world.health_warning == 0);
    world.health_force_full = 1;
    sim_set_my_health(&world, 0);
    assert(world.me_health == 100 && world.health_warning == 0);
}

int main(void)
{
    test_add_lists_and_limits();
    test_rebuild_surface_list();
    test_set_my_life_boundaries();
    test_set_my_health_boundaries();
    puts("ant list/player helper tests passed");
    return 0;
}
