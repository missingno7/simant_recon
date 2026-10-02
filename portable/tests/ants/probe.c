#include "../../game/simulation/ants.h"

#include <string.h>

typedef struct SimAntProbeResult {
    int16_t count;
    int16_t success;
    uint8_t x, y, type, mode, state, life;
} SimAntProbeResult;

typedef struct SimPlayerProbeResult {
    int16_t x, y, plane, type, direction, health;
    uint8_t life, tail_life, warning, death;
} SimPlayerProbeResult;

typedef struct SimAntRebuildResult {
    int16_t count;
    uint8_t x[SIM_A_ANT_CAPACITY];
    uint8_t y[SIM_A_ANT_CAPACITY];
    uint8_t type[SIM_A_ANT_CAPACITY];
    uint8_t mode[SIM_A_ANT_CAPACITY];
    uint8_t state[SIM_A_ANT_CAPACITY];
} SimAntRebuildResult;

typedef struct SimAntClearResult {
    int16_t count_a, count_b, count_r;
    uint8_t marker_a, marker_b, marker_r;
} SimAntClearResult;

void sim_ant_probe_add(int16_t which, int16_t count, int16_t x, int16_t y,
                       uint8_t type, uint8_t mode, uint8_t state,
                       SimAntProbeResult *result)
{
    SimGameWorld world;
    uint16_t slot;

    memset(&world, 0, sizeof world);
    memset(result, 0, sizeof *result);
    if (which == 0) {
        world.ants_a.count = count;
        slot = count >= 0 && count <= SIM_A_ANT_CAPACITY ? (uint16_t)count : 0;
        world.ants_a.x[slot] = 0xa1;
        world.ants_a.y[slot] = 0xa2;
        world.ants_a.type[slot] = 0xa3;
        world.ants_a.mode[slot] = 0xa4;
        world.ants_a.state[slot] = 0xa5;
        if (x >= 0 && x < SIM_WORLD_WIDTH && y >= 0 && y < SIM_WORLD_HEIGHT)
            world.life_a[x][y] = 0xa6;
        result->success = sim_ant_add_a(&world, x, y, type, mode, state);
        result->count = world.ants_a.count;
        result->x = world.ants_a.x[slot]; result->y = world.ants_a.y[slot];
        result->type = world.ants_a.type[slot]; result->mode = world.ants_a.mode[slot];
        result->state = world.ants_a.state[slot];
        if (x >= 0 && x < SIM_WORLD_WIDTH && y >= 0 && y < SIM_WORLD_HEIGHT)
            result->life = world.life_a[x][y];
    } else if (which == 1) {
        world.ants_b.count = count;
        slot = count >= 0 && count <= SIM_B_ANT_CAPACITY ? (uint16_t)count : 0;
        world.ants_b.x[slot] = 0xa1;
        world.ants_b.y[slot] = 0xa2;
        world.ants_b.type[slot] = 0xa3;
        world.ants_b.mode[slot] = 0xa4;
        world.ants_b.state[slot] = 0xa5;
        if (x >= 0 && x < SIM_NEST_WIDTH && y >= 0 && y < SIM_NEST_HEIGHT)
            world.life_b[x][y] = 0xa6;
        result->success = sim_ant_add_b(&world, x, y, type, mode, state);
        result->count = world.ants_b.count;
        result->x = world.ants_b.x[slot]; result->y = world.ants_b.y[slot];
        result->type = world.ants_b.type[slot]; result->mode = world.ants_b.mode[slot];
        result->state = world.ants_b.state[slot];
        if (x >= 0 && x < SIM_NEST_WIDTH && y >= 0 && y < SIM_NEST_HEIGHT)
            result->life = world.life_b[x][y];
    } else {
        world.ants_r.count = count;
        slot = count >= 0 && count <= SIM_R_ANT_CAPACITY ? (uint16_t)count : 0;
        world.ants_r.x[slot] = 0xa1;
        world.ants_r.y[slot] = 0xa2;
        world.ants_r.type[slot] = 0xa3;
        world.ants_r.mode[slot] = 0xa4;
        world.ants_r.state[slot] = 0xa5;
        if (x >= 0 && x < SIM_NEST_WIDTH && y >= 0 && y < SIM_NEST_HEIGHT)
            world.life_r[x][y] = 0xa6;
        result->success = sim_ant_add_r(&world, x, y, type, mode, state);
        result->count = world.ants_r.count;
        result->x = world.ants_r.x[slot]; result->y = world.ants_r.y[slot];
        result->type = world.ants_r.type[slot]; result->mode = world.ants_r.mode[slot];
        result->state = world.ants_r.state[slot];
        if (x >= 0 && x < SIM_NEST_WIDTH && y >= 0 && y < SIM_NEST_HEIGHT)
            result->life = world.life_r[x][y];
    }
}

void sim_ant_probe_set_life(int16_t plane, int16_t x, int16_t y,
                            int16_t type, int16_t direction, int16_t value,
                            SimPlayerProbeResult *result)
{
    SimGameWorld world;

    memset(&world, 0, sizeof world);
    memset(result, 0, sizeof *result);
    world.me_x = -7;
    world.me_y = -8;
    world.current_ant_plane = 3;
    world.me_type = 0x20;
    world.me_direction = 5;
    if (plane <= 1 && x >= 0 && x < SIM_WORLD_WIDTH && y >= 0 && y < SIM_WORLD_HEIGHT)
        world.life_a[x][y] = 0x6e;
    if (type == 0x60 && direction >= 0 && direction < 8) {
        static const int8_t init_dx[8] = { 0, 1, 1, 1, 0, -1, -1, -1 };
        static const int8_t init_dy[8] = { -1, -1, 0, 1, 1, 1, 0, -1 };
        int16_t d = (int16_t)((uint16_t)direction ^ 4u);
        int16_t tx = (int16_t)(x + init_dx[d]), ty = (int16_t)(y + init_dy[d]);
        if (plane <= 1 && tx >= 0 && tx < SIM_WORLD_WIDTH && ty >= 0 && ty < SIM_WORLD_HEIGHT)
            world.life_a[tx][ty] = 0x7d;
    }
    sim_set_my_life(&world, plane, x, y, type, direction, value);
    result->x = world.me_x; result->y = world.me_y;
    result->plane = world.current_ant_plane; result->type = world.me_type;
    result->direction = world.me_direction; result->health = world.me_health;
    if (plane <= 1 && x >= 0 && x < SIM_WORLD_WIDTH && y >= 0 && y < SIM_WORLD_HEIGHT)
        result->life = world.life_a[x][y];
    if (type == 0x60 && direction >= 0 && direction < 8 && plane <= 1) {
        static const int8_t dx[8] = { 0, 1, 1, 1, 0, -1, -1, -1 };
        static const int8_t dy[8] = { -1, -1, 0, 1, 1, 1, 0, -1 };
        int16_t d = (int16_t)((uint16_t)direction ^ 4u);
        int16_t tx = (int16_t)(x + dx[d]), ty = (int16_t)(y + dy[d]);
        if (tx >= 0 && tx < SIM_WORLD_WIDTH && ty >= 0 && ty < SIM_WORLD_HEIGHT)
            result->tail_life = world.life_a[tx][ty];
    }
}

void sim_ant_probe_set_health(int16_t health, int16_t threshold,
                              uint8_t force_full, uint8_t death,
                              SimPlayerProbeResult *result)
{
    SimGameWorld world;

    memset(&world, 0, sizeof world);
    memset(result, 0, sizeof *result);
    world.health_warning_threshold = threshold;
    world.health_force_full = force_full;
    world.health_death = death;
    sim_set_my_health(&world, health);
    result->health = world.me_health;
    result->warning = world.health_warning;
    result->death = world.health_death;
}

void sim_ant_probe_rebuild_a(const uint8_t *life, SimAntRebuildResult *result)
{
    SimGameWorld world;

    memset(&world, 0, sizeof world);
    memcpy(world.life_a, life, sizeof world.life_a);
    world.ants_a.count = -17;
    sim_ants_rebuild_a(&world);
    result->count = world.ants_a.count;
    memcpy(result->x, world.ants_a.x, sizeof result->x);
    memcpy(result->y, world.ants_a.y, sizeof result->y);
    memcpy(result->type, world.ants_a.type, sizeof result->type);
    memcpy(result->mode, world.ants_a.mode, sizeof result->mode);
    memcpy(result->state, world.ants_a.state, sizeof result->state);
}

void sim_ant_probe_clear(int16_t which, int16_t count_a, int16_t count_b,
                         int16_t count_r, SimAntClearResult *result)
{
    SimGameWorld world;

    memset(&world, 0, sizeof world);
    world.ants_a.count = count_a;
    world.ants_b.count = count_b;
    world.ants_r.count = count_r;
    world.ants_a.type[0] = 0xa1;
    world.ants_b.type[0] = 0xb2;
    world.ants_r.type[0] = 0xc3;
    if (which == 0)
        sim_ants_clear_b(&world);
    else
        sim_ants_clear_r(&world);
    result->count_a = world.ants_a.count;
    result->count_b = world.ants_b.count;
    result->count_r = world.ants_r.count;
    result->marker_a = world.ants_a.type[0];
    result->marker_b = world.ants_b.type[0];
    result->marker_r = world.ants_r.type[0];
}
