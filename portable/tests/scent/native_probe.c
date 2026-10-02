#include "../../game/simulation/scent.h"

#include <stddef.h>
#include <string.h>

enum { PHER_BYTES = SIM_PHEROMONE_WIDTH * SIM_PHEROMONE_HEIGHT,
       ARRAYS = 7, INPUT_BYTES = 2 + ARRAYS * PHER_BYTES,
       OUTPUT_BYTES = 1 + ARRAYS * PHER_BYTES };

int sim_scent_probe(const uint8_t *input, size_t input_size,
                    uint8_t *output, size_t output_size)
{
    SimGameWorld world;
    SimScentState state;
    const uint8_t *src;
    uint16_t op;
    SimScentStatus status;
    uint8_t *dst;

    if (input == NULL || output == NULL || input_size != INPUT_BYTES ||
        output_size < OUTPUT_BYTES)
        return SIM_SCENT_INVALID_ARGUMENT;
    memset(&world, 0, sizeof world);
    memset(&state, 0, sizeof state);
    op = (uint16_t)(input[0] | ((uint16_t)input[1] << 8));
    src = input + 2;
    memcpy(world.pheromone_a, src, PHER_BYTES); src += PHER_BYTES;
    memcpy(world.pheromone_b_nest, src, PHER_BYTES); src += PHER_BYTES;
    memcpy(world.pheromone_b_trail, src, PHER_BYTES); src += PHER_BYTES;
    memcpy(world.pheromone_r_nest, src, PHER_BYTES); src += PHER_BYTES;
    memcpy(world.pheromone_r_trail, src, PHER_BYTES); src += PHER_BYTES;
    memcpy(world.pheromone_aux, src, PHER_BYTES); src += PHER_BYTES;
    memcpy(state.smooth_alarm_work, src, PHER_BYTES);

    switch (op) {
    case 0: status = sim_scent_colony_smell_black_nest(&world); break;
    case 1: status = sim_scent_colony_smell_red_nest(&world); break;
    case 2: status = sim_scent_colony_smell_black_trail(&world); break;
    case 3: status = sim_scent_colony_smell_red_trail(&world); break;
    case 4: status = sim_scent_smooth_alarm(&world, &state); break;
    default: return SIM_SCENT_INVALID_ARGUMENT;
    }

    output[0] = (uint8_t)status;
    dst = output + 1;
    memcpy(dst, world.pheromone_a, PHER_BYTES); dst += PHER_BYTES;
    memcpy(dst, world.pheromone_b_nest, PHER_BYTES); dst += PHER_BYTES;
    memcpy(dst, world.pheromone_b_trail, PHER_BYTES); dst += PHER_BYTES;
    memcpy(dst, world.pheromone_r_nest, PHER_BYTES); dst += PHER_BYTES;
    memcpy(dst, world.pheromone_r_trail, PHER_BYTES); dst += PHER_BYTES;
    memcpy(dst, world.pheromone_aux, PHER_BYTES); dst += PHER_BYTES;
    memcpy(dst, state.smooth_alarm_work, PHER_BYTES);
    return OUTPUT_BYTES;
}
