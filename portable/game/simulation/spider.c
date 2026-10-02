#include "spider.h"

#include <stddef.h>

/* SHARED object 0x3e8/type 9 after InitStuff's f_0244_0022 word swap. */
static const int16_t spider_sine_q15[64] = {
    0, 804, 1607, 2410, 3211, 4011, 4807, 5601,
    6392, 7179, 7961, 8739, 9511, 10278, 11038, 11792,
    12539, 13278, 14009, 14732, 15446, 16150, 16845, 17530,
    18204, 18867, 19519, 20159, 20787, 21402, 22004, 22594,
    23169, 23731, 24278, 24811, 25329, 25831, 26318, 26789,
    27244, 27683, 28105, 28510, 28897, 29268, 29621, 29955,
    30272, 30571, 30851, 31113, 31356, 31580, 31785, 31970,
    32137, 32284, 32412, 32520, 32609, 32678, 32727, 32757
};

const int16_t *sim_spider_sine_table(void)
{
    return spider_sine_q15;
}

void sim_spider_init(SimSpiderState *state, const SimGameWorld *world)
{
    if (state == NULL)
        return;
    state->burp_count = 10;
    state->eat_count = 0;
    state->corpse_base = 0;
    state->cycle = 0;
    state->cycle2 = 0;
    state->revenge = 0;
    state->state_flag = 0;
    state->direction = 0;
    state->target_mode = world != NULL && world->scenario != 0 ? 1 : 0;
    state->x16 = 0x0400;
    state->y16 = 0x0200;
    state->mode = 0;
    state->aux_mode = 0;
    state->target = -2;
    state->target_life = -1;
    state->user_x = 64;
    state->user_y = 64;
    state->sine_q15 = spider_sine_q15;
}

static int16_t frac_sin(const int16_t *table, int angle)
{
    unsigned index = (unsigned)angle & 0x7fu;
    int value;

    if (index > 0x3fu)
        index = 0x80u - index;
    value = index == 0x40u ? 0x7fff : table[index & 0x3fu];
    if (((unsigned)angle & 0xffu) > 0x7fu)
        value = -value;
    return (int16_t)value;
}

static uint8_t rand1(SimRng *rng, uint16_t range)
{
    uint16_t value = 0;
    (void)sim_rng_s1(rng, range, &value);
    return (uint8_t)value;
}

static int16_t find_a_ant(const SimAntList *ants, int x, int y, int life)
{
    int i;

    if (ants->count <= 0 || ants->count > SIM_A_ANT_CAPACITY)
        return -1;
    for (i = (int)ants->count - 1; i >= 0; --i) {
        if (ants->x[i] == (uint8_t)x && ants->y[i] == (uint8_t)y &&
            ants->type[i] == (uint8_t)life)
            return (int16_t)i;
    }
    return -1;
}

static void dead_ant_here(SimSpiderState *state, SimGameWorld *world,
                          SimRng *rng, int x, int y, int type)
{
    int old_x;
    int old_y;
    uint8_t old_tile;
    uint8_t tile;

    state->corpse_index++;
    if (state->corpse_index >= 100)
        state->corpse_index = 0;
    old_x = state->corpse_x[state->corpse_index];
    old_y = state->corpse_y[state->corpse_index];
    old_tile = world->tiles.surface[old_x][old_y];
    if (world->tiles.terrain_set == 0) {
        if (old_tile >= 0x10 && old_tile < 0x18)
            world->tiles.surface[old_x][old_y] = (uint8_t)sim_rng_s16(rng);
        state->corpse_x[state->corpse_index] = (uint8_t)x;
        state->corpse_y[state->corpse_index] = (uint8_t)y;
        tile = world->tiles.surface[x][y];
        if (tile < 0x18)
            world->tiles.surface[x][y] =
                (uint8_t)(sim_rng_s4(rng) + (type != 0 ? 0x14 : 0x10));
    } else {
        if (old_tile >= 8 && old_tile < 0x18)
            world->tiles.surface[old_x][old_y] =
                (uint8_t)((old_tile - 8) >> 2);
        state->corpse_x[state->corpse_index] = (uint8_t)x;
        state->corpse_y[state->corpse_index] = (uint8_t)y;
        tile = world->tiles.surface[x][y];
        if (tile < 4) {
            uint16_t draw = 0;
            (void)sim_rng_s1(rng, 2, &draw);
            if (type != 0)
                world->tiles.surface[x][y] = (uint8_t)(draw + tile * 4 + 0x0a);
            else
                world->tiles.surface[x][y] = (uint8_t)(draw + (tile + 2) * 4);
        }
    }
    world->life_a[x][y] = 0;
}

int16_t sim_spider_scan(SimSpiderState *state, SimGameWorld *world,
                        SimRng *rng, SimSpiderLaser *laser)
{
    int direction;
    int sx;
    int sy;
    int found = -1;
    int pass;
    int angle;

    if (laser != NULL) {
        laser->from_x16 = 0;
        laser->from_y16 = 0;
        laser->to_x16 = 0;
        laser->to_y16 = 0;
        laser->fired = 0;
    }
    if (state == NULL || world == NULL || rng == NULL || state->sine_q15 == NULL)
        return -1;

    direction = ((state->direction - 2) & 7) << 5;
    sx = state->x16 >> 4;
    sy = state->y16 >> 4;
    for (pass = 0; pass < 2; ++pass) {
        for (angle = direction - 32; angle < direction + 32; ++angle) {
            int radius = (int)rand1(rng, 12) + 1;
            int x = (int)((int32_t)frac_sin(state->sine_q15, angle + 0x40) * radius /
                          32767L) + sx;
            int y = (int)((int32_t)frac_sin(state->sine_q15, angle) * radius /
                          32767L) + sy;
            int life;

            if (x < 0 || x > 127 || y < 0 || y > 63)
                continue;
            life = world->life_a[x][y];
            if (life == 0)
                continue;
            found = find_a_ant(&world->ants_a, x, y, life);
            if (found < 0)
                continue;

            if (laser != NULL) {
                laser->from_x16 = state->x16;
                laser->from_y16 = state->y16;
                laser->to_x16 = (int16_t)((x << 4) + 7);
                laser->to_y16 = (int16_t)((y << 4) + 7);
                laser->fired = 1;
            }
            if (sim_rng_s4(rng) != 0) {
                world->life_a[x][y] = 0;
                world->ants_a.type[found] = 0;
                dead_ant_here(state, world, rng, x, y, life & 0x80);
            }
            return (int16_t)found;
        }
    }
    return (int16_t)found;
}
