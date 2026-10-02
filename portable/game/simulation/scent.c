#include "scent.h"

#include <stddef.h>

SimScentStatus sim_scent_colony_smell_black_nest(SimGameWorld *world)
{
    unsigned x, y;
    if (world == NULL)
        return SIM_SCENT_INVALID_ARGUMENT;
    for (x = 0; x < SIM_PHEROMONE_WIDTH; ++x) {
        for (y = 0; y < SIM_PHEROMONE_HEIGHT; ++y) {
            uint8_t value = world->pheromone_b_nest[x][y];
            if (value != 0)
                world->pheromone_b_nest[x][y] = (uint8_t)(value - 1u);
        }
    }
    return SIM_SCENT_OK;
}

SimScentStatus sim_scent_colony_smell_red_nest(SimGameWorld *world)
{
    unsigned x, y;
    if (world == NULL)
        return SIM_SCENT_INVALID_ARGUMENT;
    for (x = 0; x < SIM_PHEROMONE_WIDTH; ++x) {
        for (y = 0; y < SIM_PHEROMONE_HEIGHT; ++y) {
            uint8_t value = world->pheromone_r_nest[x][y];
            if (value != 0)
                world->pheromone_r_nest[x][y] = (uint8_t)(value - 1u);
        }
    }
    return SIM_SCENT_OK;
}

SimScentStatus sim_scent_colony_smell_black_trail(SimGameWorld *world)
{
    unsigned x, y;
    if (world == NULL)
        return SIM_SCENT_INVALID_ARGUMENT;
    for (x = 0; x < SIM_PHEROMONE_WIDTH; ++x) {
        for (y = 0; y < SIM_PHEROMONE_HEIGHT; ++y) {
            uint8_t value = world->pheromone_b_trail[x][y];
            if (value < 8)
                world->pheromone_b_trail[x][y] = 0;
            else
                world->pheromone_b_trail[x][y] =
                    (uint8_t)(value - (value >> 1));
        }
    }
    return SIM_SCENT_OK;
}

SimScentStatus sim_scent_colony_smell_red_trail(SimGameWorld *world)
{
    unsigned x, y;
    if (world == NULL)
        return SIM_SCENT_INVALID_ARGUMENT;
    for (x = 0; x < SIM_PHEROMONE_WIDTH; ++x) {
        for (y = 0; y < SIM_PHEROMONE_HEIGHT; ++y) {
            uint8_t value = world->pheromone_r_trail[x][y];
            if (value == 0)
                continue;
            if (value < 8)
                world->pheromone_r_trail[x][y] = 0;
            else
                world->pheromone_r_trail[x][y] =
                    (uint8_t)(value - (value >> 1));
        }
    }
    return SIM_SCENT_OK;
}

SimScentStatus sim_scent_smooth_alarm(SimGameWorld *world,
                                      SimScentState *state)
{
    unsigned x, y;
    if (world == NULL || state == NULL)
        return SIM_SCENT_INVALID_ARGUMENT;
    for (x = 0; x < SIM_PHEROMONE_WIDTH; ++x)
        for (y = 0; y < SIM_PHEROMONE_HEIGHT; ++y)
            state->smooth_alarm_work[x][y] = world->pheromone_a[x][y];

    for (x = 0; x < SIM_PHEROMONE_WIDTH; ++x) {
        for (y = 0; y < SIM_PHEROMONE_HEIGHT; ++y) {
            unsigned sum = 0;
            unsigned value;
            if (x > 0)
                sum += state->smooth_alarm_work[x - 1][y];
            if (y > 0)
                sum += state->smooth_alarm_work[x][y - 1];
            if (x < SIM_PHEROMONE_WIDTH - 1)
                sum += state->smooth_alarm_work[x + 1][y];
            if (y < SIM_PHEROMONE_HEIGHT - 1)
                sum += state->smooth_alarm_work[x][y + 1];
            value = (state->smooth_alarm_work[x][y] + (sum >> 2)) >> 1;
            world->pheromone_a[x][y] = value > 8 ? (uint8_t)value : 0;
        }
    }
    return SIM_SCENT_OK;
}
