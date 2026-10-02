#include "../../game/simulation/water.h"

#include <stddef.h>
#include <string.h>

enum {
    SURFACE_BYTES = 128 * 64,
    NEST_BYTES = 64 * 64,
    PHEROMONE_BYTES = 64 * 32,
    SMALL_ANT_BYTES = 500,
    HEADER_BYTES = 16,
    OP_BYTES = 5,
    MAX_OPS = 16,
    SNAPSHOT_BYTES = SURFACE_BYTES + 4 * NEST_BYTES + 6 * PHEROMONE_BYTES +
                     2 * (2 + 5 * SMALL_ANT_BYTES) +
                     2 * SIM_WATER_DROP_CAPACITY + 10,
    MAX_OUTPUT = MAX_OPS * (1 + 2 + SIM_WATER_MAX_INTENTS * 8 + SNAPSHOT_BYTES)
};

static uint16_t get16(const uint8_t *bytes)
{
    return (uint16_t)(bytes[0] | ((uint16_t)bytes[1] << 8));
}

static uint32_t get32(const uint8_t *bytes)
{
    return (uint32_t)get16(bytes) | ((uint32_t)get16(bytes + 2) << 16);
}

static void put16(uint8_t **cursor, uint16_t value)
{
    *(*cursor)++ = (uint8_t)value;
    *(*cursor)++ = (uint8_t)(value >> 8);
}

static void copy_in(uint8_t **cursor, void *destination, size_t size)
{
    memcpy(destination, *cursor, size);
    *cursor += size;
}

static void copy_out(uint8_t **cursor, const void *source, size_t size)
{
    memcpy(*cursor, source, size);
    *cursor += size;
}

static void read_small_list(uint8_t **cursor, SimSmallAntList *list)
{
    list->count = (int16_t)get16(*cursor);
    *cursor += 2;
    copy_in(cursor, list->type, SMALL_ANT_BYTES);
    copy_in(cursor, list->x, SMALL_ANT_BYTES);
    copy_in(cursor, list->y, SMALL_ANT_BYTES);
    copy_in(cursor, list->mode, SMALL_ANT_BYTES);
    copy_in(cursor, list->state, SMALL_ANT_BYTES);
}

static void write_small_list(uint8_t **cursor, const SimSmallAntList *list)
{
    put16(cursor, (uint16_t)list->count);
    copy_out(cursor, list->type, SMALL_ANT_BYTES);
    copy_out(cursor, list->x, SMALL_ANT_BYTES);
    copy_out(cursor, list->y, SMALL_ANT_BYTES);
    copy_out(cursor, list->mode, SMALL_ANT_BYTES);
    copy_out(cursor, list->state, SMALL_ANT_BYTES);
}

static void write_snapshot(uint8_t **out, const SimGameWorld *world,
                           const SimWaterState *water, const SimRng *rng)
{
    copy_out(out, world->tiles.surface, SURFACE_BYTES);
    copy_out(out, world->tiles.nest_b, NEST_BYTES);
    copy_out(out, world->tiles.nest_r, NEST_BYTES);
    copy_out(out, world->life_b, NEST_BYTES);
    copy_out(out, world->life_r, NEST_BYTES);
    copy_out(out, world->pheromone_a, PHEROMONE_BYTES);
    copy_out(out, world->pheromone_aux, PHEROMONE_BYTES);
    copy_out(out, world->pheromone_b_nest, PHEROMONE_BYTES);
    copy_out(out, world->pheromone_b_trail, PHEROMONE_BYTES);
    copy_out(out, world->pheromone_r_nest, PHEROMONE_BYTES);
    copy_out(out, world->pheromone_r_trail, PHEROMONE_BYTES);
    write_small_list(out, &world->ants_b);
    write_small_list(out, &world->ants_r);
    copy_out(out, water->drop_x, SIM_WATER_DROP_CAPACITY);
    copy_out(out, water->drop_y, SIM_WATER_DROP_CAPACITY);
    put16(out, (uint16_t)water->drop_scan_transition);
    put16(out, (uint16_t)world->source_counter_0242);
    put16(out, rng->s_state);
    put16(out, (uint16_t)rng->c_state);
    put16(out, (uint16_t)(rng->c_state >> 16));
}

int sim_water_probe(const uint8_t *input, size_t input_size,
                    uint8_t *output, size_t output_size)
{
    SimGameWorld world;
    SimRng rng;
    SimWaterState water;
    SimWaterTrace trace;
    uint16_t op_count;
    uint16_t i;
    uint8_t *in;
    uint8_t *out;

    if (input == NULL || output == NULL || input_size < HEADER_BYTES)
        return SIM_WATER_INVALID_ARGUMENT;
    memset(&world, 0, sizeof world);
    memset(&water, 0, sizeof water);
    memset(&trace, 0, sizeof trace);
    rng.s_state = 0;
    rng.c_state = 0;
    rng.s_state = (uint16_t)get32(input) ^ 0x3751u;
    /* SeedRRand casts TickCount's 32-bit result to 16-bit unsigned int before
     * calling the MSC srand runtime. */
    rng.c_state = (uint16_t)get32(input + 4);
    {
        uint16_t warmup = sim_rng_s128(&rng);
        while (warmup-- != 0)
            (void)sim_rng_msc_rand(&rng);
    }
    world.tiles.terrain_set = (int16_t)get16(input + 8);
    world.source_counter_0242 = (int16_t)get16(input + 10);
    water.drop_scan_transition = (int16_t)get16(input + 12);
    op_count = get16(input + 14);
    if (op_count > MAX_OPS || input_size < HEADER_BYTES + (size_t)op_count * OP_BYTES)
        return SIM_WATER_INVALID_ARGUMENT;

    in = (uint8_t *)(input + HEADER_BYTES + (size_t)op_count * OP_BYTES);
    copy_in(&in, world.tiles.surface, SURFACE_BYTES);
    copy_in(&in, world.tiles.nest_b, NEST_BYTES);
    copy_in(&in, world.tiles.nest_r, NEST_BYTES);
    copy_in(&in, world.life_b, NEST_BYTES);
    copy_in(&in, world.life_r, NEST_BYTES);
    copy_in(&in, world.pheromone_a, PHEROMONE_BYTES);
    copy_in(&in, world.pheromone_aux, PHEROMONE_BYTES);
    copy_in(&in, world.pheromone_b_nest, PHEROMONE_BYTES);
    copy_in(&in, world.pheromone_b_trail, PHEROMONE_BYTES);
    copy_in(&in, world.pheromone_r_nest, PHEROMONE_BYTES);
    copy_in(&in, world.pheromone_r_trail, PHEROMONE_BYTES);
    copy_in(&in, water.drop_x, SIM_WATER_DROP_CAPACITY);
    copy_in(&in, water.drop_y, SIM_WATER_DROP_CAPACITY);
    read_small_list(&in, &world.ants_b);
    read_small_list(&in, &world.ants_r);
    if ((size_t)(in - input) != input_size)
        return SIM_WATER_INVALID_ARGUMENT;
    if (output_size < MAX_OUTPUT)
        return SIM_WATER_INVALID_ARGUMENT;

    out = output;
    for (i = 0; i < op_count; ++i) {
        const uint8_t *op = input + HEADER_BYTES + (size_t)i * OP_BYTES;
        uint8_t kind = op[0];
        int16_t arg = (int16_t)get16(op + 1);
        int16_t rain = (int16_t)get16(op + 3);
        SimWaterStatus status;
        switch (kind) {
        case 0:
            status = sim_water_tick(&world, &rng, &water, rain, &trace);
            break;
        case 1:
            status = sim_water_init(&world, &rng, &water, &trace);
            break;
        case 2:
            status = sim_water_place_drop(&world, &rng, &water, arg, &trace);
            break;
        case 3:
            status = sim_water_add_row(&world, &rng, &water, arg, &trace);
            break;
        case 4:
            status = sim_water_drop_row(&world, &rng, &water, arg, &trace);
            break;
        default:
            return SIM_WATER_INVALID_ARGUMENT;
        }
        *out++ = (uint8_t)status;
        uint16_t j;
        put16(&out, trace.count);
        for (j = 0; j < trace.count; ++j) {
            put16(&out, (uint16_t)trace.intents[j].kind);
            put16(&out, (uint16_t)trace.intents[j].first);
            put16(&out, (uint16_t)trace.intents[j].second);
            put16(&out, (uint16_t)trace.intents[j].third);
        }
        write_snapshot(&out, &world, &water, &rng);
    }
    return (int)(out - output);
}
