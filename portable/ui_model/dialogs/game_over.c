#include "game_over.h"

#include <limits.h>
#include <string.h>

static const int16_t score_weights[SIM_GAME_OVER_SCORE_COMPONENTS] = {
    13, 17, 19, 23, 29, 31, 37, 41
};

static int16_t signed_i16(uint16_t bits)
{
    if (bits <= INT16_MAX)
        return (int16_t)bits;
    return (int16_t)((int32_t)bits - 65536);
}

static int16_t add_i16(int16_t left, int16_t right)
{
    return signed_i16((uint16_t)((uint16_t)left + (uint16_t)right));
}

static int16_t multiply_i16(int16_t left, int16_t right)
{
    return signed_i16((uint16_t)((uint32_t)(uint16_t)left *
                                 (uint32_t)(uint16_t)right));
}

static int32_t signed_i32(uint32_t bits)
{
    if (bits <= INT32_MAX)
        return (int32_t)bits;
    return (int32_t)((int64_t)bits - INT64_C(4294967296));
}

static int32_t add_i32(int32_t left, int32_t right)
{
    return signed_i32((uint32_t)left + (uint32_t)right);
}

static int32_t subtract_i32(int32_t left, int32_t right)
{
    return signed_i32((uint32_t)left - (uint32_t)right);
}

static int32_t multiply_i32(int32_t left, int32_t right)
{
    return signed_i32((uint32_t)((uint64_t)(uint32_t)left *
                                 (uint64_t)(uint32_t)right));
}

static int32_t divide_i32(int32_t numerator, int32_t denominator)
{
    return (int32_t)((int64_t)numerator / denominator);
}

static int16_t divide_i16(int16_t numerator, int16_t denominator)
{
    return signed_i16((uint16_t)((int32_t)numerator / denominator));
}

SimGameOverStatus sim_game_over_level(int32_t score, int16_t scenario,
                                     int16_t losing_side,
                                     int32_t *rank_score,
                                     uint8_t *level_index)
{
    int32_t ranked;
    uint8_t level;
    if (rank_score == NULL || level_index == NULL ||
        scenario < 0 || scenario > 3)
        return SIM_GAME_OVER_BAD_ARGUMENT;
    ranked = scenario == 2 ? score / 5 : score;
    if (ranked < 214220)
        level = 0;
    else if (ranked < 428440)
        level = 1;
    else if (ranked < 642660)
        level = 2;
    else if (ranked < 856880)
        level = 3;
    else
        level = 4;
    if (losing_side == 0)
        level = (uint8_t)(level + 5u);
    *rank_score = ranked;
    *level_index = level;
    return SIM_GAME_OVER_OK;
}

SimGameOverStatus sim_game_over_calculate(const SimGameOverInput *input,
                                         SimGameOverResult *result)
{
    SimGameOverResult computed;
    int16_t sum, sum2, divisor, n;
    int32_t score, q;
    int i, j, k, history_index, marked;

    if (input == NULL || result == NULL)
        return SIM_GAME_OVER_BAD_ARGUMENT;
    if (input->history_count < 0 || input->history_count > 63 ||
        input->history_cursor < 0 || input->history_cursor >= 64 ||
        input->scenario < 0 || input->scenario > 3)
        return SIM_GAME_OVER_INVALID_STATE;

    memset(&computed, 0, sizeof(computed));
    k = (input->history_cursor - input->history_count) & 0x3f;
    sum = 0;
    for (i = 0; i < input->history_count; ++i) {
        sum = add_i16(sum, input->health_history[k]);
        k = (k + 1) & 0x3f;
    }
    computed.components[0] = i > 0 ? divide_i16(sum, (int16_t)i) : 0;

    history_index = (input->history_cursor - input->history_count) & 0x3f;
    sum = 0;
    sum2 = 0;
    for (k = 0; k < input->history_count; ++k) {
        sum = add_i16(sum, input->blue_food_history[history_index]);
        sum2 = add_i16(sum2, input->red_food_history[history_index]);
        history_index = (history_index + 1) & 0x3f;
    }
    divisor = add_i16(sum2, sum);
    computed.components[1] = divisor > 0 ? signed_i16((uint16_t)(
        ((int32_t)sum * 100) / divisor)) : 0;

    if (input->food_total > 0) {
        int32_t remaining = subtract_i32(input->food_total, input->food_used);
        computed.components[2] = signed_i16((uint16_t)divide_i32(
            multiply_i32(remaining, 100), input->food_total));
    } else {
        computed.components[2] = 100;
    }

    n = add_i16(input->blue_workers, input->red_workers);
    if (n > 0)
        computed.components[3] = divide_i16(
            multiply_i16(input->blue_workers, 100), n);
    else
        computed.components[3] = 100;

    if (input->scenario == 2 || input->scenario == 3) {
        n = add_i16(input->colony_score_a, input->blue_colony_score);
        computed.components[4] = n > 0 ? signed_i16((uint16_t)divide_i32(
            multiply_i32(input->blue_colony_score, 100), n)) : 100;
        n = add_i16(input->colony_score_b, input->blue_colony_score);
        computed.components[5] = n > 0 ? signed_i16((uint16_t)divide_i32(
            multiply_i32(input->blue_colony_score, 100), n)) : 100;

        marked = 0;
        for (j = 0; j < 16; ++j) {
            for (k = j < 5 ? 3 : 2; k < 12; ++k) {
                if (input->tutorial_marks[k][j] != 0)
                    ++marked;
            }
        }
        computed.components[6] = marked > 0 ?
            (int16_t)(marked * 100 / 155) : 0;

        marked = 0;
        for (j = 0; j < 16; ++j) {
            for (k = 0; k < 2 || (j < 5 && k < 3); ++k) {
                if (input->tutorial_marks[k][j] != 0)
                    ++marked;
            }
        }
        computed.components[7] = marked > 0 ?
            (int16_t)(marked * 100 / 37) : 0;
    }

    score = input->health;
    for (k = 0; k < SIM_GAME_OVER_SCORE_COMPONENTS; ++k) {
        int32_t weighted = multiply_i32(computed.components[k],
                                        score_weights[k]);
        weighted = multiply_i32(weighted, 51);
        score = add_i32(score, weighted);
    }
    if (input->scenario != 2) {
        score = divide_i32(multiply_i32(score, 29), 10);
        if (input->world_ticks < 4100) {
            q = input->world_ticks / 100;
            if (q <= 0)
                q = 1;
            score = divide_i32(multiply_i32(q, score), 41);
        }
    } else {
        if (input->world_ticks < 8100) {
            q = input->world_ticks / 100;
            if (q <= 0)
                q = 1;
            score = divide_i32(multiply_i32(q, score), 81);
        }
        score = multiply_i32(score, 5);
    }

    computed.score = add_i32(input->world_ticks, score);
    if (sim_game_over_level(computed.score, input->scenario,
                            input->losing_side, &computed.rank_score,
                            &computed.level_index) != SIM_GAME_OVER_OK)
        return SIM_GAME_OVER_INVALID_STATE;
    computed.opening_sound_id = input->sound_enabled ?
        (input->losing_side == 0 ? 0x271a : 0x2718) : 0;
    computed.sound_argument = 0x7e;
    computed.font_id = input->screen_width == 320 ? 2 : 4;
    computed.scenario_index = input->scenario;
    computed.scenario_resource_id = SIM_GAME_OVER_SCENARIO_STRINGS;
    computed.level_resource_id = SIM_GAME_OVER_LEVEL_STRINGS;
    computed.window_id = SIM_GAME_OVER_WINDOW_ID;
    computed.scenario_object_id = SIM_GAME_OVER_SCENARIO_OBJECT;
    computed.score_object_id = SIM_GAME_OVER_SCORE_OBJECT;
    computed.level_object_id = SIM_GAME_OVER_LEVEL_OBJECT;
    *result = computed;
    return SIM_GAME_OVER_OK;
}

const char *sim_game_over_status_string(SimGameOverStatus status)
{
    switch (status) {
    case SIM_GAME_OVER_OK: return "ok";
    case SIM_GAME_OVER_BAD_ARGUMENT: return "bad argument";
    case SIM_GAME_OVER_INVALID_STATE: return "invalid game-over state";
    }
    return "unknown game-over status";
}
