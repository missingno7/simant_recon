#include "feeding.h"

#include <stddef.h>

static int16_t frac_sin(const int16_t table[64], int16_t angle)
{
    unsigned value = (unsigned)(uint16_t)angle;
    unsigned index = value & 0x7fu;
    int16_t result;

    if (index > 0x3fu)
        index = 0x80u - index;
    if (index == 0x40u)
        result = 0x7fff;
    else
        result = table[index & 0x3fu];
    if ((value & 0xffu) > 0x7fu)
        result = (int16_t)-(int32_t)result;
    return result;
}

static int add_sound(SimFeedingTrace *trace)
{
    SimFeedingEffect *effect;
    if (trace->count >= SIM_FEEDING_EFFECT_CAPACITY) {
        trace->overflow = 1;
        return 0;
    }
    effect = &trace->events[trace->count++];
    effect->kind = SIM_FEEDING_SOUND;
    effect->arguments[0] = 0x20;
    effect->arguments[1] = 0;
    effect->arguments[2] = 0x7e;
    return 1;
}

SimFeedingStatus sim_food_add(SimGameWorld *world, SimRng *rng,
                              const int16_t sine_q15[64], int16_t count,
                              int16_t sound, SimFeedingTrace *trace)
{
    int16_t center_x, center_y;
    int16_t radius;
    int i, attempts;

    if (world == NULL || rng == NULL || sine_q15 == NULL || trace == NULL ||
        trace->count > SIM_FEEDING_EFFECT_CAPACITY || trace->overflow)
        return SIM_FEEDING_INVALID_ARGUMENT;
    if (sound == 1 && trace->count == SIM_FEEDING_EFFECT_CAPACITY) {
        trace->overflow = 1;
        return SIM_FEEDING_EFFECTS_FULL;
    }

    if (sound == 1)
        (void)add_sound(trace);
    if (count < 0) {
        uint16_t draw;
        if (!sim_rng_s1(rng, 0x30, &draw))
            return SIM_FEEDING_INVALID_ARGUMENT;
        center_x = 0x40;
        center_y = (int16_t)(draw + 8);
        attempts = 200;
    } else {
        center_x = (int16_t)sim_rng_s128(rng);
        center_y = (int16_t)sim_rng_s64(rng);
        attempts = count;
    }
    world->food_center_x = center_x;
    world->food_center_y = center_y;
    radius = (int16_t)(sim_rng_s8(rng) + 5);
    for (i = 0; i < attempts; ++i) {
        int16_t angle = (int16_t)sim_rng_s256(rng);
        uint16_t distance_value;
        int16_t x, y;
        uint8_t tile;

        if (!sim_rng_s1(rng, (uint16_t)radius, &distance_value))
            return SIM_FEEDING_INVALID_ARGUMENT;
        x = (int16_t)(((int32_t)distance_value *
                       frac_sin(sine_q15, (int16_t)(angle + 0x40))) /
                      0x7fffL + center_x);
        y = (int16_t)(((int32_t)distance_value * frac_sin(sine_q15, angle)) /
                      0x7fffL + center_y);
        if (x < 0 || x > 0x7f || y < 0 || y > 0x3f ||
            world->life_a[x][y] != 0)
            continue;

        tile = world->tiles.surface[x][y];
        if (world->tiles.terrain_set != 0) {
            if (tile < 0x18) {
                if (tile < 4)
                    world->tiles.surface[x][y] = (uint8_t)((tile + 6) << 2);
                else
                    world->tiles.surface[x][y] =
                        (uint8_t)(((tile - 8) & 0xfcu) + 0x18);
                world->food_added_terrain++;
            } else if (tile < 0x28 && tile % 4 < 3) {
                world->tiles.surface[x][y]++;
                world->food_added_terrain++;
            }
        } else if (tile < 0x18) {
            world->tiles.surface[x][y] = 0x48;
            world->food_added_terrain++;
        } else if (tile >= 0x48 && tile < 0x4b) {
            world->tiles.surface[x][y]++;
            world->food_added_terrain++;
        }
    }
    return SIM_FEEDING_OK;
}

static int16_t decrement_clamp_zero(int16_t value)
{
    int16_t decremented = (int16_t)(uint16_t)((uint16_t)value - 1u);
    return decremented < 0 ? 0 : decremented;
}

SimFeedingStatus sim_feed_ants(SimGameWorld *world, SimRng *rng,
                               SimFeedingState *state,
                               const int16_t sine_q15[64],
                               SimFeedingTrace *trace)
{
    SimFeedingStatus status;

    if (world == NULL || rng == NULL || state == NULL || sine_q15 == NULL ||
        trace == NULL)
        return SIM_FEEDING_INVALID_ARGUMENT;
    if (trace->count > SIM_FEEDING_EFFECT_CAPACITY || trace->overflow)
        return SIM_FEEDING_INVALID_ARGUMENT;
    if (world->scenario != 3 &&
        world->food_added_terrain < state->next_food_threshold &&
        trace->count == SIM_FEEDING_EFFECT_CAPACITY) {
        trace->overflow = 1;
        return SIM_FEEDING_EFFECTS_FULL;
    }
    if (world->source_state_0c18 == 0)
        world->health_black = decrement_clamp_zero(world->health_black);
    world->health_red = decrement_clamp_zero(world->health_red);
    if (world->scenario == 3 ||
        world->food_added_terrain >= state->next_food_threshold)
        return SIM_FEEDING_OK;

    status = sim_food_add(world, rng, sine_q15, 0x96, 1, trace);
    if (status != SIM_FEEDING_OK)
        return status;
    {
        uint16_t draw;
        if (!sim_rng_s1(rng, 0x32, &draw))
            return SIM_FEEDING_INVALID_ARGUMENT;
        state->next_food_threshold = (int16_t)(draw + 1);
    }
    return SIM_FEEDING_OK;
}
