#include "water.h"

#include <stddef.h>

static void begin_trace(SimWaterTrace *trace)
{
    if (trace != NULL)
        trace->count = 0;
}

static SimWaterStatus emit(SimWaterTrace *trace, SimWaterIntentKind kind,
                           int16_t first, int16_t second, int16_t third)
{
    SimWaterIntent *intent;
    if (trace == NULL)
        return SIM_WATER_OK;
    if (trace->count >= SIM_WATER_MAX_INTENTS)
        return SIM_WATER_TRACE_FULL;
    intent = &trace->intents[trace->count++];
    intent->kind = kind;
    intent->first = first;
    intent->second = second;
    intent->third = third;
    return SIM_WATER_OK;
}

static int valid_row(int16_t y)
{
    return y >= 0 && y < SIM_NEST_HEIGHT;
}

static uint16_t s1(SimRng *rng, uint16_t range)
{
    uint16_t value = 0;
    (void)sim_rng_s1(rng, range, &value);
    return value;
}

static uint16_t rrand(SimRng *rng, uint16_t range)
{
    int16_t value = 0;
    (void)sim_rng_r(rng, (int16_t)range, &value);
    return (uint16_t)value;
}

static void drown_list(SimSmallAntList *list, int16_t y)
{
    int i;
    for (i = list->count; i > 0; ) {
        uint8_t type;
        int caste;
        --i;
        if (list->y[i] != (uint8_t)y)
            continue;
        type = list->type[i];
        if (type == 0)
            continue;
        caste = (type & 0x78u) >> 3;
        if (caste <= 0 || caste >= 12)
            continue;
        list->mode[i] = 0x11;
    }
}

static SimWaterStatus place_drop(SimGameWorld *world, SimRng *rng,
                                 SimWaterState *state, int16_t index)
{
    int x = (int)rrand(rng, 128);
    int y = (int)rrand(rng, 64);
    int px;
    int py;
    if (index < 0 || index >= SIM_WATER_DROP_CAPACITY)
        return SIM_WATER_INVALID_ARGUMENT;
    state->drop_x[index] = (uint8_t)x;
    state->drop_y[index] = (uint8_t)y;
    if (world->tiles.surface[x][y] >= 0x0e)
        return SIM_WATER_OK;

    world->tiles.surface[x][y] = 0x74;
    px = x >> 1;
    py = y >> 1;
    world->pheromone_aux[px][py] = 0;
    world->pheromone_a[px][py] = 0;
    if (world->pheromone_b_nest[px][py] >= 0x14)
        world->pheromone_b_nest[px][py] -= 0x14;
    else
        world->pheromone_b_nest[px][py] = 0;
    world->pheromone_b_trail[px][py] = 0;
    if (world->pheromone_r_nest[px][py] >= 0x14)
        world->pheromone_r_nest[px][py] -= 0x14;
    else
        world->pheromone_r_nest[px][py] = 0;
    world->pheromone_r_trail[px][py] = 0;
    return SIM_WATER_OK;
}

static SimWaterStatus add_row(SimGameWorld *world, SimWaterTrace *trace,
                              int16_t y)
{
    int x;
    if (!valid_row(y))
        return SIM_WATER_INVALID_ARGUMENT;
    drown_list(&world->ants_b, y);
    drown_list(&world->ants_r, y);
    for (x = 0; x < SIM_NEST_WIDTH; ++x) {
        uint8_t value = world->tiles.nest_b[x][y];
        world->tiles.nest_b[x][y] = value < 0x20 ? 0x4e : (uint8_t)(value + 0x2f);
        value = world->tiles.nest_r[x][y];
        world->tiles.nest_r[x][y] = value < 0x20 ? 0x4e : (uint8_t)(value + 0x2f);
        if (emit(trace, SIM_WATER_INTENT_MAP_INVALIDATION, 2, (int16_t)x, y) != SIM_WATER_OK ||
            emit(trace, SIM_WATER_INTENT_MAP_INVALIDATION, 3, (int16_t)x, y) != SIM_WATER_OK)
            return SIM_WATER_TRACE_FULL;
    }
    return SIM_WATER_OK;
}

static SimWaterStatus drop_row(SimGameWorld *world, SimRng *rng,
                               SimWaterTrace *trace, int16_t y)
{
    int x;
    if (!valid_row(y))
        return SIM_WATER_INVALID_ARGUMENT;
    for (x = 0; x < SIM_NEST_WIDTH; ++x) {
        uint8_t value = world->tiles.nest_b[x][y];
        world->tiles.nest_b[x][y] = value == 0x4e ? (uint8_t)s1(rng, 8) : (uint8_t)(value - 0x2f);
        value = world->tiles.nest_r[x][y];
        world->tiles.nest_r[x][y] = value == 0x4e ? (uint8_t)s1(rng, 8) : (uint8_t)(value - 0x2f);
        if (emit(trace, SIM_WATER_INTENT_MAP_INVALIDATION, 2, (int16_t)x, y) != SIM_WATER_OK ||
            emit(trace, SIM_WATER_INTENT_MAP_INVALIDATION, 3, (int16_t)x, y) != SIM_WATER_OK)
            return SIM_WATER_TRACE_FULL;
    }
    return SIM_WATER_OK;
}

SimWaterStatus sim_water_place_drop(SimGameWorld *world, SimRng *rng,
                                    SimWaterState *state, int16_t index,
                                    SimWaterTrace *trace)
{
    if (world == NULL || rng == NULL || state == NULL || index < 0 ||
        index >= SIM_WATER_DROP_CAPACITY)
        return SIM_WATER_INVALID_ARGUMENT;
    begin_trace(trace);
    return place_drop(world, rng, state, index);
}

SimWaterStatus sim_water_init(SimGameWorld *world, SimRng *rng,
                              SimWaterState *state, SimWaterTrace *trace)
{
    int i;
    if (world == NULL || rng == NULL || state == NULL)
        return SIM_WATER_INVALID_ARGUMENT;
    begin_trace(trace);
    for (i = 0; i < SIM_WATER_DROP_CAPACITY; ++i) {
        SimWaterStatus status = place_drop(world, rng, state, (int16_t)i);
        if (status != SIM_WATER_OK)
            return status;
    }
    return SIM_WATER_OK;
}

SimWaterStatus sim_water_add_row(SimGameWorld *world, SimRng *rng,
                                 SimWaterState *state, int16_t y,
                                 SimWaterTrace *trace)
{
    if (world == NULL || rng == NULL || state == NULL)
        return SIM_WATER_INVALID_ARGUMENT;
    begin_trace(trace);
    return add_row(world, trace, y);
}

SimWaterStatus sim_water_drop_row(SimGameWorld *world, SimRng *rng,
                                  SimWaterState *state, int16_t y,
                                  SimWaterTrace *trace)
{
    if (world == NULL || rng == NULL || state == NULL)
        return SIM_WATER_INVALID_ARGUMENT;
    begin_trace(trace);
    return drop_row(world, rng, trace, y);
}

SimWaterStatus sim_water_tick(SimGameWorld *world, SimRng *rng,
                              SimWaterState *state, int16_t rain_enabled,
                              SimWaterTrace *trace)
{
    int i;
    SimWaterStatus status;
    if (world == NULL || rng == NULL || state == NULL ||
        world->source_counter_0242 < 0 || world->source_counter_0242 > 64)
        return SIM_WATER_INVALID_ARGUMENT;
    begin_trace(trace);
    if (rain_enabled != 0 && world->tiles.terrain_set == 0) {
        if (s1(rng, 50) == 0) {
            status = emit(trace, SIM_WATER_INTENT_SOUND, 0x29, 0, 0x40);
            if (status != SIM_WATER_OK)
                return status;
        }
        state->drop_scan_transition = 1;
        if (s1(rng, 10) == 0 && world->source_counter_0242 > 4) {
            --world->source_counter_0242;
            status = add_row(world, trace, world->source_counter_0242);
            if (status != SIM_WATER_OK)
                return status;
        }
        for (i = 0; i < SIM_WATER_DROP_CAPACITY; ++i) {
            int x = state->drop_x[i];
            int y = state->drop_y[i];
            uint8_t value = world->tiles.surface[x][y];
            if (value >= 0x74 && value < 0x77)
                ++world->tiles.surface[x][y];
            else {
                if (value == 0x77)
                    world->tiles.surface[x][y] = (uint8_t)s1(rng, 14);
                status = place_drop(world, rng, state, (int16_t)i);
                if (status != SIM_WATER_OK)
                    return status;
            }
        }
    } else if (world->tiles.terrain_set == 0) {
        if (state->drop_scan_transition == 1) {
            state->drop_scan_transition = 0;
            for (i = 0; i < SIM_WATER_DROP_CAPACITY; ++i) {
                int x = state->drop_x[i];
                int y = state->drop_y[i];
                uint8_t value = world->tiles.surface[x][y];
                if (value >= 0x74 && value <= 0x77)
                    world->tiles.surface[x][y] = (uint8_t)s1(rng, 14);
            }
        }
        if (world->source_counter_0242 < 0x40 && s1(rng, 10) == 0) {
            status = drop_row(world, rng, trace, world->source_counter_0242);
            if (status != SIM_WATER_OK)
                return status;
            ++world->source_counter_0242;
        }
    }
    return SIM_WATER_OK;
}
