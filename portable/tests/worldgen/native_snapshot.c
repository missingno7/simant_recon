#include "../../game/simulation/worldgen.h"

#include <stddef.h>
#include <stdint.h>
#include <string.h>

typedef struct Writer {
    uint8_t *data;
    size_t capacity;
    size_t used;
    int failed;
} Writer;

static void write_bytes(Writer *writer, const void *data, size_t size)
{
    if (writer->failed || size > writer->capacity - writer->used) {
        writer->failed = 1;
        return;
    }
    memcpy(writer->data + writer->used, data, size);
    writer->used += size;
}

static void write_i16(Writer *writer, int16_t value)
{
    write_bytes(writer, &value, sizeof value);
}

static void write_u32(Writer *writer, uint32_t value)
{
    write_bytes(writer, &value, sizeof value);
}

#define WRITE_ARRAY(writer, value) write_bytes((writer), (value), sizeof(value))
#define WRITE_LIST(writer, list, field, count) \
    write_bytes((writer), (list).field, (count))

/* Test-only adapter: initialize the valid scenario-2 RandWorld contract and
 * serialize its observable state in the matching order documented by the
 * Python runner. No SDL or DOS emulator code is used on the native side. */
size_t sim_worldgen_native_snapshot(uint16_t seed, int16_t scenario,
                                    int16_t terrain_set, int16_t black_size,
                                    int16_t red_size, uint8_t *output,
                                    size_t output_capacity)
{
    SimGameWorld world;
    SimRng rng = { 0, 0 };
    SimSetupState setup_state;
    SimSpiderState spider;
    SimNestRuntime nest_runtime;
    SimNestTrace nest_trace;
    SimWorldgenEffects effects;
    SimPopulationEffects population_effects;
    SimRandWorldContext context;
    SimWorldgenStatus status;
    Writer writer = { output, output_capacity, 0, 0 };

    if (output == NULL)
        return 0;
    /* Poison unrelated/preexisting state so source-owned resets and deliberate
     * preservation are tested instead of being hidden by calloc defaults. */
    memset(&world, 0xa5, sizeof world);
    memset(&setup_state, 0, sizeof setup_state);
    memset(&spider, 0, sizeof spider);
    memset(&nest_runtime, 0, sizeof nest_runtime);
    memset(&nest_trace, 0, sizeof nest_trace);
    memset(&effects, 0, sizeof effects);
    memset(&population_effects, 0, sizeof population_effects);
    world.tiles.terrain_set = terrain_set;
    world.scenario = scenario;
    world.world_kind = 0;
    world.player_mode = 0;
    world.player_caste_type = 0x10;
    world.player_death_plane = 0;
    world.population_new_game = 1;
    world.lifetime_graph_preset[0] = 11;
    world.lifetime_graph_preset[1] = 8;
    world.health_warning_threshold = 30;
    world.player_spawn_x = 0;
    world.player_spawn_y = 0;
    world.source_state_049a = 0x4567;
    world.source_state_0c22 = 0x4567;
    world.source_state_104e = 1;
    world.source_state_07be = 0x2345;
    world.source_state_04c4 = (int16_t)0xa5a5;
    world.player_update_code = -1;
    world.source_state_0214 = 0;
    world.source_state_0204 = 0;
    world.source_state_0228 = 0;
    world.source_state_0478 = 0;
    world.source_state_0504 = 0;
    world.source_state_0c44 = 0;
    world.source_state_0c18 = 0;
    world.source_state_0c14 = 0;
    world.health_force_full = 0;
    world.world_ticks = 0;
    world.population_selection_colony = 0;
    world.population_selection_pending = 0;
    world.current_ground_tile_id = 0;
    world.drop_direction = 0;
    world.overlay_width = 0;
    world.overlay_resource_set = 0;
    world.food_center_x = 0;
    world.food_center_y = 0;
    memset(world.ant_lions, 0, sizeof world.ant_lions);
    world.ant_lion_count = 0;
    world.initial_ant_lions = 0;
    world.ants_eaten_by_lions = 0;
    memset(world.sow_x, 0, sizeof world.sow_x);
    memset(world.sow_y, 0, sizeof world.sow_y);
    memset(world.sow_direction, 0, sizeof world.sow_direction);
    memset(world.sow_saved_tile, 0, sizeof world.sow_saved_tile);
    memset(world.pillar_map, 0, sizeof world.pillar_map);
    world.pillar_state = world.pillar_x = world.pillar_y = 0;
    world.pillar_segment = world.pillar_direction = 0;
    world.ants_a.count = 17;
    world.ants_b.count = 3;
    world.ants_r.count = 2;
    sim_world_clear_arrays(&world);
    sim_spider_init(&spider, &world);
    context.setup_state = &setup_state;
    context.spider = &spider;
    context.nest_runtime = &nest_runtime;
    context.nest_trace = &nest_trace;
    context.sine_q15 = spider.sine_q15;
    context.effects = &effects;
    context.population_effects = &population_effects;

    status = sim_worldgen_rand_world(&world, &rng, seed, black_size, red_size, 11, 8,
                                     &context);
    write_i16(&writer, (int16_t)status);
    write_i16(&writer, (int16_t)rng.s_state);
    write_u32(&writer, rng.c_state);

    WRITE_ARRAY(&writer, world.tiles.surface);
    WRITE_ARRAY(&writer, world.tiles.nest_b);
    WRITE_ARRAY(&writer, world.tiles.nest_r);
    WRITE_ARRAY(&writer, world.exit_b);
    WRITE_ARRAY(&writer, world.exit_r);
    WRITE_ARRAY(&writer, world.life_a);
    WRITE_ARRAY(&writer, world.life_b);
    WRITE_ARRAY(&writer, world.life_r);
    WRITE_ARRAY(&writer, world.pheromone_aux);
    WRITE_ARRAY(&writer, world.pheromone_a);
    WRITE_ARRAY(&writer, world.pheromone_b_nest);
    WRITE_ARRAY(&writer, world.pheromone_b_trail);
    WRITE_ARRAY(&writer, world.pheromone_r_nest);
    WRITE_ARRAY(&writer, world.pheromone_r_trail);
    WRITE_ARRAY(&writer, world.hole_b);
    WRITE_ARRAY(&writer, world.hole_r);
    WRITE_LIST(&writer, world.ants_a, x, SIM_A_ANT_CAPACITY);
    WRITE_LIST(&writer, world.ants_a, y, SIM_A_ANT_CAPACITY);
    WRITE_LIST(&writer, world.ants_a, mode, SIM_A_ANT_CAPACITY);
    WRITE_LIST(&writer, world.ants_a, type, SIM_A_ANT_CAPACITY);
    WRITE_LIST(&writer, world.ants_a, state, SIM_A_ANT_CAPACITY);
    WRITE_LIST(&writer, world.ants_b, x, SIM_B_ANT_CAPACITY);
    WRITE_LIST(&writer, world.ants_b, y, SIM_B_ANT_CAPACITY);
    WRITE_LIST(&writer, world.ants_b, mode, SIM_B_ANT_CAPACITY);
    WRITE_LIST(&writer, world.ants_b, type, SIM_B_ANT_CAPACITY);
    WRITE_LIST(&writer, world.ants_b, state, SIM_B_ANT_CAPACITY);
    WRITE_LIST(&writer, world.ants_r, x, SIM_R_ANT_CAPACITY);
    WRITE_LIST(&writer, world.ants_r, y, SIM_R_ANT_CAPACITY);
    WRITE_LIST(&writer, world.ants_r, mode, SIM_R_ANT_CAPACITY);
    WRITE_LIST(&writer, world.ants_r, type, SIM_R_ANT_CAPACITY);
    WRITE_LIST(&writer, world.ants_r, state, SIM_R_ANT_CAPACITY);
    write_i16(&writer, world.ants_a.count);
    write_i16(&writer, world.ants_b.count);
    write_i16(&writer, world.ants_r.count);

    write_i16(&writer, world.source_counter_0242);
    write_u32(&writer, world.source_counter_0472);
    write_i16(&writer, world.source_counter_09fa);
    write_i16(&writer, world.source_counter_0a00);
    write_i16(&writer, world.queens_black);
    write_i16(&writer, world.queens_red);
    write_i16(&writer, world.food_black);
    write_i16(&writer, world.food_red);
    write_i16(&writer, world.food_added_terrain);
    write_i16(&writer, world.health_black);
    write_i16(&writer, world.health_red);
    write_i16(&writer, world.cycle);
    write_u32(&writer, (uint16_t)world.map_view_x |
                       ((uint32_t)(uint16_t)world.map_view_y << 16));
    write_u32(&writer, (uint16_t)world.map_focus[0][0] |
                       ((uint32_t)(uint16_t)world.map_focus[0][1] << 16));
    write_u32(&writer, (uint16_t)world.map_focus[1][0] |
                       ((uint32_t)(uint16_t)world.map_focus[1][1] << 16));
    write_u32(&writer, (uint16_t)world.map_focus[2][0] |
                       ((uint32_t)(uint16_t)world.map_focus[2][1] << 16));
    write_i16(&writer, world.player_spawn_x);
    write_i16(&writer, world.player_spawn_y);
    write_i16(&writer, world.current_ant_plane);
    write_i16(&writer, world.me_x);
    write_i16(&writer, world.me_y);
    write_i16(&writer, world.me_type);
    write_i16(&writer, world.me_direction);
    write_i16(&writer, world.source_state_04c4);
    write_bytes(&writer, world.population_red, sizeof world.population_red);
    write_bytes(&writer, world.population_black, sizeof world.population_black);
    write_bytes(&writer, world.ants_by_type, sizeof world.ants_by_type);
    write_i16(&writer, world.total_population_black);
    write_i16(&writer, world.total_population_red);
    write_i16(&writer, world.population_new_game);
    write_i16(&writer, world.population_selection_colony);
    write_i16(&writer, world.population_selection_pending);
    write_i16(&writer, world.player_update_code);
    write_u32(&writer, world.source_state_0214);
    write_u32(&writer, world.source_state_0204);
    write_i16(&writer, world.source_state_0228);
    write_i16(&writer, world.source_state_0478);
    write_i16(&writer, world.source_state_0504);
    write_i16(&writer, world.source_state_0c44);
    write_i16(&writer, world.source_state_0c18);
    write_i16(&writer, world.health_force_full);
    write_i16(&writer, world.source_state_0c14);
    write_u32(&writer, world.world_ticks);
    write_i16(&writer, world.source_state_049a);
    write_i16(&writer, world.source_state_0c22);
    write_i16(&writer, world.source_state_104e);
    write_i16(&writer, world.source_state_07be);
    write_i16(&writer, world.food_center_x);
    write_i16(&writer, world.food_center_y);
    write_i16(&writer, world.current_ground_tile_id);
    write_i16(&writer, world.drop_direction);
    write_i16(&writer, world.overlay_width);
    write_i16(&writer, world.tiles.terrain_set);
    write_i16(&writer, world.overlay_resource_set);
    write_i16(&writer, world.ant_lion_count);
    write_i16(&writer, world.initial_ant_lions);
    write_i16(&writer, world.ants_eaten_by_lions);
    for (size_t i = 0; i < 10; ++i) write_bytes(&writer, &world.ant_lions[i].x, 1);
    for (size_t i = 0; i < 10; ++i) write_bytes(&writer, &world.ant_lions[i].y, 1);
    for (size_t i = 0; i < 10; ++i) write_bytes(&writer, &world.ant_lions[i].mode, 1);
    for (size_t i = 0; i < 10; ++i) write_bytes(&writer, &world.ant_lions[i].seconds, 1);
    for (size_t i = 0; i < 10; ++i) write_bytes(&writer, &world.ant_lions[i].timer, 1);
    WRITE_ARRAY(&writer, world.sow_x);
    WRITE_ARRAY(&writer, world.sow_y);
    WRITE_ARRAY(&writer, world.sow_direction);
    WRITE_ARRAY(&writer, world.sow_saved_tile);
    write_i16(&writer, world.pillar_state);
    write_i16(&writer, world.pillar_x);
    write_i16(&writer, world.pillar_y);
    write_i16(&writer, world.pillar_segment);
    write_i16(&writer, world.pillar_direction);
    WRITE_ARRAY(&writer, world.pillar_map);
    write_i16(&writer, world.total_population_black);
    write_i16(&writer, world.total_population_red);
    write_i16(&writer, (int16_t)nest_runtime.dug_b_x_sum);
    write_i16(&writer, (int16_t)nest_runtime.dug_b_y_sum);
    write_i16(&writer, nest_runtime.dug_b_count);
    write_i16(&writer, nest_runtime.dug_b_x_average);
    write_i16(&writer, nest_runtime.dug_b_y_average);
    write_i16(&writer, (int16_t)nest_runtime.dug_r_x_sum);
    write_i16(&writer, (int16_t)nest_runtime.dug_r_y_sum);
    write_i16(&writer, nest_runtime.dug_r_count);
    write_i16(&writer, nest_runtime.dug_r_x_average);
    write_i16(&writer, nest_runtime.dug_r_y_average);
    write_i16(&writer, effects.count);
    write_i16(&writer, population_effects.count);
    return writer.failed ? 0 : writer.used;
}
