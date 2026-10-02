#include "../../game/simulation/feeding.h"

#include <stddef.h>
#include <string.h>

enum { SURFACE_BYTES = 128 * 64, HEADER_BYTES = 22,
       INPUT_BYTES = HEADER_BYTES + 2 * SURFACE_BYTES + 128,
       OUTPUT_BYTES = 1 + 2 + SIM_FEEDING_EFFECT_CAPACITY * 8 + SURFACE_BYTES + 24 };

static uint16_t get16(const uint8_t *p)
{
    return (uint16_t)(p[0] | ((uint16_t)p[1] << 8));
}

static void put16(uint8_t **p, uint16_t value)
{
    *(*p)++ = (uint8_t)value;
    *(*p)++ = (uint8_t)(value >> 8);
}

int sim_feeding_probe(const uint8_t *input, size_t input_size,
                      uint8_t *output, size_t output_size)
{
    SimGameWorld world;
    SimRng rng;
    SimFeedingState state;
    SimFeedingTrace trace;
    int16_t sine[64];
    uint8_t *out;
    unsigned i;
    SimFeedingStatus status;

    if (input == NULL || output == NULL || input_size != INPUT_BYTES ||
        output_size < OUTPUT_BYTES)
        return SIM_FEEDING_INVALID_ARGUMENT;
    memset(&world, 0, sizeof world);
    memset(&trace, 0, sizeof trace);
    world.tiles.terrain_set = (int16_t)get16(input + 6);
    world.scenario = (int16_t)get16(input + 8);
    world.health_black = (int16_t)get16(input + 10);
    world.health_red = (int16_t)get16(input + 12);
    world.source_state_0c18 = (int16_t)get16(input + 14);
    state.next_food_threshold = (int16_t)get16(input + 16);
    world.food_added_terrain = (int16_t)get16(input + 18);
    rng.s_state = get16(input + 20);
    rng.c_state = 0;
    memcpy(world.tiles.surface, input + HEADER_BYTES, SURFACE_BYTES);
    memcpy(world.life_a, input + HEADER_BYTES + SURFACE_BYTES, SURFACE_BYTES);
    for (i = 0; i < 64; ++i)
        sine[i] = (int16_t)get16(input + HEADER_BYTES + 2 * SURFACE_BYTES + i * 2);

    if (get16(input) == 0) {
        status = sim_food_add(&world, &rng, sine, (int16_t)get16(input + 2),
                              (int16_t)get16(input + 4), &trace);
    } else if (get16(input) == 1) {
        status = sim_feed_ants(&world, &rng, &state, sine, &trace);
    } else {
        return SIM_FEEDING_INVALID_ARGUMENT;
    }

    out = output;
    *out++ = (uint8_t)status;
    put16(&out, trace.count);
    for (i = 0; i < trace.count; ++i) {
        put16(&out, trace.events[i].kind);
        put16(&out, (uint16_t)trace.events[i].arguments[0]);
        put16(&out, (uint16_t)trace.events[i].arguments[1]);
        put16(&out, (uint16_t)trace.events[i].arguments[2]);
    }
    memcpy(out, world.tiles.surface, SURFACE_BYTES);
    out += SURFACE_BYTES;
    put16(&out, (uint16_t)world.health_black);
    put16(&out, (uint16_t)world.health_red);
    put16(&out, (uint16_t)state.next_food_threshold);
    put16(&out, (uint16_t)world.food_added_terrain);
    put16(&out, (uint16_t)world.food_center_x);
    put16(&out, (uint16_t)world.food_center_y);
    put16(&out, rng.s_state);
    return (int)(out - output);
}
