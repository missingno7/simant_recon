#include "../../ui_model/dialogs/game_over.h"
#include "../../game/resources/database.h"

#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#undef assert
#define assert(condition) do { \
    if (!(condition)) { \
        fprintf(stderr, "%s:%d: check failed: %s\n", __FILE__, __LINE__, \
                #condition); \
        exit(1); \
    } \
} while (0)

static SimGameOverInput empty_input(void)
{
    SimGameOverInput input;
    memset(&input, 0, sizeof(input));
    input.health = 100;
    input.sound_enabled = 1;
    input.screen_width = 320;
    return input;
}

static void test_empty_scenario_score_and_presentation(void)
{
    SimGameOverInput input = empty_input();
    SimGameOverResult result;
    assert(sim_game_over_calculate(&input, &result) == SIM_GAME_OVER_OK);
    assert(result.components[0] == 0);
    assert(result.components[1] == 0);
    assert(result.components[2] == 100);
    assert(result.components[3] == 100);
    assert(result.components[4] == 0 && result.components[5] == 0);
    assert(result.components[6] == 0 && result.components[7] == 0);
    assert(result.score == 15157);
    assert(result.rank_score == 15157);
    assert(result.level_index == 5);
    assert(result.opening_sound_id == 0x271a);
    assert(result.sound_argument == 0x7e);
    assert(result.font_id == 2);
    assert(result.scenario_index == 0);
    assert(result.scenario_resource_id == 1001);
    assert(result.level_resource_id == 1900);
    assert(result.window_id == 0x400);
    assert(result.scenario_object_id == 0x402);
    assert(result.score_object_id == 0x403);
    assert(result.level_object_id == 0x404);

    input.losing_side = 1;
    input.sound_enabled = 0;
    input.screen_width = 640;
    assert(sim_game_over_calculate(&input, &result) == SIM_GAME_OVER_OK);
    assert(result.level_index == 0);
    assert(result.opening_sound_id == 0);
    assert(result.font_id == 4);
}

static void test_wrapped_history_and_scenario_three_components(void)
{
    SimGameOverInput input = empty_input();
    SimGameOverResult result;
    input.history_cursor = 1;
    input.history_count = 3;
    input.health_history[62] = 10;
    input.health_history[63] = 20;
    input.health_history[0] = 30;
    input.blue_food_history[62] = 20;
    input.blue_food_history[63] = 30;
    input.blue_food_history[0] = 50;
    input.red_food_history[62] = 10;
    input.red_food_history[63] = 10;
    input.red_food_history[0] = 40;
    input.food_total = 1000;
    input.food_used = 250;
    input.blue_workers = 3;
    input.red_workers = 1;
    input.scenario = 3;
    input.blue_colony_score = 60;
    input.colony_score_a = 40;
    input.colony_score_b = 90;
    memset(input.tutorial_marks, 1, sizeof(input.tutorial_marks));

    assert(sim_game_over_calculate(&input, &result) == SIM_GAME_OVER_OK);
    assert(result.components[0] == 20);
    assert(result.components[1] == 62);
    assert(result.components[2] == 75);
    assert(result.components[3] == 75);
    assert(result.components[4] == 60);
    assert(result.components[5] == 40);
    assert(result.components[6] == 100);
    assert(result.components[7] == 100);
    assert(result.scenario_index == 3);
    assert(result.opening_sound_id == 0x271a);
}

static void test_scenario_two_rank_scaling_and_boundaries(void)
{
    int32_t rank_score;
    uint8_t level;
    assert(sim_game_over_level(214219, 0, 1, &rank_score, &level) ==
           SIM_GAME_OVER_OK);
    assert(rank_score == 214219 && level == 0);
    assert(sim_game_over_level(214220, 0, 1, &rank_score, &level) ==
           SIM_GAME_OVER_OK);
    assert(rank_score == 214220 && level == 1);
    assert(sim_game_over_level(428440, 0, 1, &rank_score, &level) ==
           SIM_GAME_OVER_OK && level == 2);
    assert(sim_game_over_level(642660, 0, 1, &rank_score, &level) ==
           SIM_GAME_OVER_OK && level == 3);
    assert(sim_game_over_level(856880, 0, 1, &rank_score, &level) ==
           SIM_GAME_OVER_OK && level == 4);
    assert(sim_game_over_level(1071100, 2, 0, &rank_score, &level) ==
           SIM_GAME_OVER_OK);
    assert(rank_score == 214220 && level == 6);
}

static void test_source_word_sized_accumulator_and_product(void)
{
    SimGameOverInput input = empty_input();
    SimGameOverResult result;
    input.history_cursor = 2;
    input.history_count = 2;
    input.health_history[0] = 30000;
    input.health_history[1] = 10000;
    input.blue_workers = 1000;
    input.red_workers = 1000;
    assert(sim_game_over_calculate(&input, &result) == SIM_GAME_OVER_OK);
    assert(result.components[0] == -12768);
    assert(result.components[3] == -15);
}

static void test_invalid_input_is_transactional(void)
{
    SimGameOverInput input = empty_input();
    SimGameOverResult result, before;
    memset(&result, 0xa5, sizeof(result));
    before = result;
    input.history_count = 64;
    assert(sim_game_over_calculate(&input, &result) ==
           SIM_GAME_OVER_INVALID_STATE);
    assert(memcmp(&result, &before, sizeof(result)) == 0);
    assert(sim_game_over_calculate(NULL, &result) ==
           SIM_GAME_OVER_BAD_ARGUMENT);
    assert(strcmp(sim_game_over_status_string(SIM_GAME_OVER_OK), "ok") == 0);
}

static void test_actual_endgame_string_tables(void)
{
    PortableDatabase database = {0};
    const int16_t resource_ids[] = {1001, 1900};
    const size_t minimum_counts[] = {4, 10};
    size_t table_index;
    assert(portable_db_open(&database, "assets/SHARED") == PORTABLE_DB_OK);
    for (table_index = 0; table_index < 2; ++table_index) {
        PortableDbRecord record = {0};
        size_t cursor = 2;
        size_t item;
        uint8_t count;
        assert(portable_db_load(&database, resource_ids[table_index], 4,
                                &record) == PORTABLE_DB_OK);
        assert(record.id == resource_ids[table_index] && record.kind == 4);
        assert(record.size >= 2);
        count = record.data[1];
        assert(count >= minimum_counts[table_index]);
        for (item = 0; item < count; ++item) {
            size_t length;
            assert(cursor < record.size);
            length = record.data[cursor++];
            assert(length <= record.size - cursor);
            cursor += length;
        }
        portable_db_record_free(&record);
    }
    portable_db_close(&database);
}

int main(void)
{
    test_empty_scenario_score_and_presentation();
    test_wrapped_history_and_scenario_three_components();
    test_scenario_two_rank_scaling_and_boundaries();
    test_source_word_sized_accumulator_and_product();
    test_invalid_input_is_transactional();
    test_actual_endgame_string_tables();
    puts("game-over score model: source cases pass");
    return 0;
}
