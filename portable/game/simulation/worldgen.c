#include "worldgen.h"

#include "setup.h"
#include "terrain.h"
#include "ants.h"
#include "spider.h"
#include "yard.h"

#include <stddef.h>
#include <string.h>

static int fill_seed_table(SimGameWorld *world, SimRng *rng)
{
    unsigned i;
    for (i = 0; i < 192; ++i) {
        int16_t draw;
        uint16_t wrapped;
        if (!sim_rng_r(rng, 0x7fff, &draw))
            return 0;
        /* Preserve 16-bit unsigned promotion/wrap from
         * (RRand(0x7fff) - 0xc000) & 0x7fff. */
        wrapped = (uint16_t)((uint16_t)draw - (uint16_t)0xc000u);
        world->random_seed_grid[i] = (uint16_t)(wrapped & 0x7fffu);
    }
    return 1;
}

void sim_worldgen_seed_startup_rng(SimRng *rng, uint32_t lfsr_tick,
                                   uint32_t c_runtime_tick)
{
    sim_rng_seed_startup(rng, lfsr_tick, c_runtime_tick);
}

static int effect_add(SimWorldgenEffects *effects, uint16_t kind,
                     int16_t a, int16_t b, int16_t c, int16_t d)
{
    SimWorldgenEffect *event;
    if (effects->count >= SIM_WORLDGEN_EFFECT_CAPACITY) {
        effects->overflow = 1;
        return 0;
    }
    event = &effects->events[effects->count++];
    event->kind = kind;
    event->values[0] = a;
    event->values[1] = b;
    event->values[2] = c;
    event->values[3] = d;
    return 1;
}

static int16_t sr1(SimRng *rng, uint16_t limit)
{
    uint16_t value = 0;
    (void)sim_rng_s1(rng, limit, &value);
    return (int16_t)value;
}

static int16_t frac_sin(const int16_t *table, int16_t angle)
{
    unsigned index = (unsigned)(uint16_t)angle & 0x7fu;
    int16_t value;
    if (index > 0x3fu)
        index = 0x80u - index;
    if (index == 0x40u)
        value = 0x7fff;
    else
        value = table[index & 0x3fu];
    if (((unsigned)(uint16_t)angle & 0xffu) > 0x7fu)
        value = (int16_t)-value;
    return value;
}

static void add_food(SimGameWorld *world, SimRng *rng,
                     const int16_t *sine_q15)
{
    int16_t center_x = 0x40;
    int16_t center_y;
    int16_t radius;
    int i;

    center_y = (int16_t)(sr1(rng, 0x30) + 8);
    world->food_center_x = center_x;
    world->food_center_y = center_y;
    radius = (int16_t)(sim_rng_s8(rng) + 5);
    for (i = 0; i < 200; ++i) {
        int16_t angle = (int16_t)sim_rng_s256(rng);
        int16_t distance = sr1(rng, (uint16_t)radius);
        int32_t x = ((int32_t)distance * frac_sin(sine_q15,
                        (int16_t)(angle + 0x40))) / 0x7fffL + center_x;
        int32_t y = ((int32_t)distance * frac_sin(sine_q15, angle)) /
                    0x7fffL + center_y;
        int tile;
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
}

static SimWorldgenStatus nest_status(SimNestStatus status)
{
    return status == SIM_NEST_OK ? SIM_WORLDGEN_OK : SIM_WORLDGEN_UNSUPPORTED;
}

static SimWorldgenStatus dig_out_nest(SimGameWorld *world, SimRng *rng,
                                      SimNestRuntime *runtime,
                                      SimNestTrace *trace, int16_t plane,
                                      int16_t tiles)
{
    static const int8_t dx[8] = { 0, 1, 1, 1, 0, -1, -1, -1 };
    static const int8_t dy[8] = { -1, -1, 0, 1, 1, 1, 0, -1 };
    int16_t direction = 4, x = 0x20, y = 1, remaining;
    SimNestStatus st = sim_nest_dig_tile(world, rng, runtime, trace,
                                         plane, x, y);
    if (st != SIM_NEST_OK) return nest_status(st);
    for (remaining = tiles; remaining != 0; --remaining) {
        int16_t turn = sr1(rng, 5);
        int16_t next_x, next_y;
        direction = (int16_t)(((uint16_t)(turn + direction - 3)) & 7u);
        next_x = (int16_t)(x + dx[direction]);
        next_y = (int16_t)(y + dy[direction]);
        if (next_x < 1) { next_x = 1; direction = 2; }
        else if (next_x > 0x3e) { next_x = 0x3e; direction = 6; }
        if (next_y < 2) { next_y = 1; direction = 4; }
        else if (next_y > 0x3e) { next_y = 0x3e; direction = 0; }
        st = sim_nest_dig_my_tile(world, rng, runtime, trace,
                                  plane, next_x, next_y);
        if (st != SIM_NEST_OK) return nest_status(st);
        /* DigTileThem returns one when this is an empty diggable tile. The
         * helper trace is the source-backed signal; inspect resulting map. */
        if ((plane == 2 ? world->tiles.nest_b[next_x][next_y]
                        : world->tiles.nest_r[next_x][next_y]) < 0x20) {
            x = next_x;
            y = next_y;
            if (y == 1) {
                const uint8_t hole = plane == 2 ? world->hole_b[x] : world->hole_r[x];
                if (hole == 0) {
                    st = sim_nest_make_new_hole(world, rng, runtime, trace,
                                                plane, x);
                    if (st != SIM_NEST_OK) return nest_status(st);
                }
            }
        }
    }
    return SIM_WORLDGEN_OK;
}

static SimWorldgenStatus place_queen(SimGameWorld *world, SimRng *rng,
                                    SimNestRuntime *runtime,
                                    SimNestTrace *trace, int16_t plane)
{
    int16_t count = (int16_t)(sim_rng_s4(rng) + 7);
    int16_t x = 0x20, y, wobble = 0;

    for (y = 1; y < count; ++y) {
        if (sim_nest_dig_tile(world, rng, runtime, trace,
                              plane, x, y) != SIM_NEST_OK)
            return SIM_WORLDGEN_UNSUPPORTED;
        if (plane == 2) {
            if (sim_rng_s2(rng) == 0)
                wobble = (int16_t)(sr1(rng, 3) - 1);
        } else {
            wobble = (int16_t)(sr1(rng, 3) - 1);
        }
        if (wobble + x >= 8 && wobble + x <= 0x38)
            x = (int16_t)(x + wobble);
    }
    for (count = 0; count < 2; ++count) {
        if (sim_nest_dig_tile(world, rng, runtime, trace,
                              plane, x, y) != SIM_NEST_OK)
            return SIM_WORLDGEN_UNSUPPORTED;
        ++x;
        ++y;
    }
    if (sim_nest_dig_tile(world, rng, runtime, trace,
                          plane, x, y) != SIM_NEST_OK)
        return SIM_WORLDGEN_UNSUPPORTED;
    if (plane == 2) {
        world->queen_black_x = x;
        world->queen_black_y = y;
        world->player_spawn_x = x;
        world->player_spawn_y = y;
        if (sim_nest_dig_tile(world, rng, runtime, trace, plane, x + 2, y) != SIM_NEST_OK ||
            sim_nest_dig_tile(world, rng, runtime, trace, plane, x + 1, y) != SIM_NEST_OK ||
            sim_nest_dig_tile(world, rng, runtime, trace, plane, x, y) != SIM_NEST_OK ||
            !sim_ant_add_b(world, x + 2, y, 0x62, 9, 0) ||
            !sim_ant_add_b(world, x + 1, y, 0x6a, 9, 0))
            return SIM_WORLDGEN_UNSUPPORTED;
        world->queens_black++;
    } else {
        world->queen_red_x = x;
        world->queen_red_y = y;
        if (sim_nest_dig_tile(world, rng, runtime, trace, plane, x + 2, y) != SIM_NEST_OK ||
            sim_nest_dig_tile(world, rng, runtime, trace, plane, x + 1, y) != SIM_NEST_OK ||
            sim_nest_dig_tile(world, rng, runtime, trace, plane, x, y) != SIM_NEST_OK ||
            !sim_ant_add_r(world, x + 2, y, 0xe2, 9, 0) ||
            !sim_ant_add_r(world, x + 1, y, 0xea, 9, 0))
            return SIM_WORLDGEN_UNSUPPORTED;
        world->queens_red++;
    }
    return SIM_WORLDGEN_OK;
}

static int pick_player_surface(SimGameWorld *world, SimRng *rng)
{
    int16_t x = 0x40, y = 0x20;
    int tries;
    for (tries = 0; tries < 100; ++tries) {
        int16_t row = (int16_t)(sim_rng_s16(rng) - sim_rng_s16(rng) + 0x20);
        int16_t col = (int16_t)(sim_rng_s8(rng) - sim_rng_s8(rng) + 0x20);
        if (world->tiles.surface[row][col] < 0x10) {
            x = row;
            y = col;
            break;
        }
    }
    return sim_set_my_life(world, 1, x, y, 0x40, 2, 0xff);
}

SimWorldgenStatus sim_worldgen_rand_world(
    SimGameWorld *world, SimRng *rng, uint16_t seed,
    int16_t black_size, int16_t red_size, int16_t map_width, int16_t map_kind,
    SimRandWorldContext *context)
{
    int16_t count, x, n, tries, limit1, limit2;
    SimWorldgenStatus status;

    if (world == NULL || rng == NULL || context == NULL ||
        context->setup_state == NULL || context->spider == NULL ||
        context->nest_runtime == NULL ||
        context->nest_trace == NULL ||
        context->effects == NULL || context->population_effects == NULL ||
        black_size < 0 || red_size < 0 ||
        map_width < 0 || map_width > 11 || map_kind < 0 || map_kind > 15)
        return SIM_WORLDGEN_INVALID_ARGUMENT;
    memset(context->effects, 0, sizeof *context->effects);
    memset(context->nest_trace, 0, sizeof *context->nest_trace);
    sim_rng_set_s_seed(rng, (int16_t)seed);
    sim_spider_init(context->spider, world);
    if (context->sine_q15 == NULL)
        context->sine_q15 = context->spider->sine_q15;
    if (sim_terrain_build(world, rng, map_width, map_kind) != SIM_TERRAIN_OK)
        return SIM_WORLDGEN_INVALID_ARGUMENT;

    black_size = (int16_t)(black_size + (black_size >> 2));
    red_size = (int16_t)(red_size + (red_size >> 2));
    /* Original unsigned seed's `seed < 0` initializer compiles to zero. */
    for (count = 0; count < 64; ++count) {
        for (x = 0; x < 64; ++x) {
            world->tiles.nest_b[count][x] = 0x2e;
            world->tiles.nest_r[count][x] = 0x2e;
            world->exit_b[count][x] = 0;
            world->exit_r[count][x] = 0;
            world->life_b[count][x] = 0;
            world->life_r[count][x] = 0;
            world->life_a[count][x] = 0;
            world->life_a[count + 64][x] = 0;
        }
    }
    for (count = 0; count < 64; ++count) {
        if (world->tiles.terrain_set == 0) {
            world->tiles.nest_b[count][0] = (uint8_t)(sim_rng_s4(rng) + 0x1c);
            world->tiles.nest_r[count][0] = (uint8_t)(sim_rng_s4(rng) + 0x1c);
        } else {
            world->tiles.nest_b[count][0] = map_kind > 3
                ? (uint8_t)(sr1(rng, 2) + 0x1c) : 0x1e;
            world->tiles.nest_r[count][0] = map_kind > 3
                ? (uint8_t)(sr1(rng, 2) + 0x1c) : 0x1e;
        }
        world->exit_b[count][0] = 0xff;
        world->exit_r[count][0] = 0xff;
    }
    memset(world->pheromone_aux, 0, sizeof world->pheromone_aux);
    memset(world->pheromone_a, 0, sizeof world->pheromone_a);
    memset(world->pheromone_b_nest, 0, sizeof world->pheromone_b_nest);
    memset(world->pheromone_b_trail, 0, sizeof world->pheromone_b_trail);
    memset(world->pheromone_r_nest, 0, sizeof world->pheromone_r_nest);
    memset(world->pheromone_r_trail, 0, sizeof world->pheromone_r_trail);

    tries = 0;
    limit1 = (int16_t)(sr1(rng, 6) + 7);
    limit2 = (int16_t)(15 - sim_rng_s2(rng));
    n = black_size;
    while (n > 0) {
        int16_t roll;
        --n;
        count = 0;
        (void)sim_rng_sg(rng, 0x80, &count);
        x = (int16_t)sim_rng_s64(rng);
        if (world->tiles.surface[count][x] >= 0x50)
            continue;
        if (world->life_a[count][x] != 0) {
            if (++tries < 50) ++n;
            continue;
        }
        roll = (int16_t)sim_rng_s16(rng);
        if (roll < limit1)
            world->life_a[count][x] = (uint8_t)(sim_rng_s8(rng) + 0x10);
        else if (roll < limit2)
            world->life_a[count][x] = (uint8_t)(sim_rng_s8(rng) + 0x30);
        else if (sim_rng_s2(rng))
            world->life_a[count][x] = (uint8_t)(sim_rng_s8(rng) + 0x20);
        else
            world->life_a[count][x] = (uint8_t)(sim_rng_s8(rng) + 0x40);
    }
    tries = 0;
    limit1 = (int16_t)(sr1(rng, 6) + 7);
    limit2 = (int16_t)(15 - sim_rng_s2(rng));
    n = red_size;
    while (n > 0) {
        int16_t roll;
        --n;
        count = (int16_t)(0x7f - 0);
        {
            int16_t low = 0;
            (void)sim_rng_sg(rng, 0x80, &low);
            count = (int16_t)(0x7f - low);
        }
        x = (int16_t)sim_rng_s64(rng);
        if (world->tiles.surface[count][x] >= 0x50)
            continue;
        if (world->life_a[count][x] != 0) {
            if (++tries < 50) ++n;
            continue;
        }
        roll = (int16_t)sim_rng_s16(rng);
        if (roll < limit1)
            world->life_a[count][x] = (uint8_t)(sim_rng_s8(rng) - 0x70);
        else if (roll < limit2)
            world->life_a[count][x] = (uint8_t)(sim_rng_s8(rng) - 0x50);
        else if (sim_rng_s2(rng))
            world->life_a[count][x] = (uint8_t)(sim_rng_s8(rng) - 0x60);
        else
            world->life_a[count][x] = (uint8_t)(sim_rng_s8(rng) - 0x40);
    }

    memset(world->hole_b, 0, sizeof world->hole_b);
    memset(world->hole_r, 0, sizeof world->hole_r);
    if (world->scenario != 2 || black_size >= 1) {
        status = nest_status(sim_nest_make_new_hole(world, rng,
            context->nest_runtime, context->nest_trace, 2, 0x20));
        if (status != SIM_WORLDGEN_OK) return status;
    }
    if (red_size >= 1) {
        status = nest_status(sim_nest_make_new_hole(world, rng,
            context->nest_runtime, context->nest_trace, 3, 0x20));
        if (status != SIM_WORLDGEN_OK) return status;
    }
    /* RandWorld resets the excavation aggregates after making the starting
     * entrances, then any optional DigOut pass accumulates on top. */
    context->nest_runtime->dug_b_x_sum = 0;
    context->nest_runtime->dug_b_y_sum = 0;
    context->nest_runtime->dug_r_x_sum = 0;
    context->nest_runtime->dug_r_y_sum = 0;
    context->nest_runtime->dug_b_count = 0;
    context->nest_runtime->dug_r_count = 0;
    context->nest_runtime->dug_b_x_average = 0;
    context->nest_runtime->dug_b_y_average = 0;
    context->nest_runtime->dug_r_x_average = 0;
    context->nest_runtime->dug_r_y_average = 0;
    world->source_counter_0242 = 0x40;
    world->queens_black = 0;
    world->queens_red = 0;
    world->food_black = 0;
    world->food_red = 0;
    world->food_added_terrain = 0;
    if (black_size > 1) {
        status = dig_out_nest(world, rng, context->nest_runtime,
                              context->nest_trace, 2,
                              (int16_t)(black_size << 4));
        if (status != SIM_WORLDGEN_OK) return status;
    }
    if (red_size > 1) {
        status = dig_out_nest(world, rng, context->nest_runtime,
                              context->nest_trace, 3,
                              (int16_t)(red_size << 4));
        if (status != SIM_WORLDGEN_OK) return status;
    }

    sim_ants_rebuild_a(world);
    sim_ants_clear_b(world);
    sim_ants_clear_r(world);
    world->queen_black_x = world->queen_black_y = -1;
    world->queen_red_x = world->queen_red_y = -1;
    if (red_size > 0) {
        status = place_queen(world, rng, context->nest_runtime,
                             context->nest_trace, 3);
        if (status != SIM_WORLDGEN_OK) return status;
    }
    if (black_size > 0) {
        status = place_queen(world, rng, context->nest_runtime,
                             context->nest_trace, 2);
        if (status != SIM_WORLDGEN_OK) return status;
    }

    world->player_flags = 0;
    world->player_needs_init = 0;
    world->player_caste_type = 0x10;
    world->source_state_049a = 0;
    world->source_state_0c22 = 0xfd;
    if (world->source_state_104e != 0) {
        world->source_state_104e = 0;
        world->source_state_07be = -1;
    }
    sim_set_my_health(world, 100);
    if (world->scenario != 3) {
        world->player_mode = 0;
        if (world->scenario != 2 || world->world_kind != 0) {
            int16_t spawn_x = world->player_spawn_x;
            int16_t spawn_y = world->player_spawn_y;
            if (!sim_set_my_life(world, 2, spawn_x, spawn_y,
                                 0x10, 2, 0xff))
                return SIM_WORLDGEN_INVALID_ARGUMENT;
        } else if (!pick_player_surface(world, rng)) {
            return SIM_WORLDGEN_INVALID_ARGUMENT;
        }
    } else {
        world->current_ant_plane = 1;
        world->player_mode = 2;
        world->me_x = 0x40;
        world->me_y = 0x20;
        world->me_direction = 2;
        world->me_type = 0x10;
    }
    world->player_selection_plane = world->current_ant_plane;
    world->player_selection_x = world->me_x;
    world->player_selection_y = world->me_y;
    if (!effect_add(context->effects, SIM_WORLDGEN_PLAYER_SELECTION,
                    world->current_ant_plane, world->me_x, world->me_y, 0))
        return SIM_WORLDGEN_UNSUPPORTED;

    world->food_black = 0;
    world->food_red = 0;
    if (world->scenario != 3)
        add_food(world, rng, context->sine_q15);
    world->health_black = 100;
    world->health_red = 100;
    world->source_counter_0472 = 0;
    world->source_counter_09fa = 0;
    world->source_counter_0a00 = 0;
    world->cycle = 0;
    world->health_death = 0;
    sim_setup_clear_history(context->setup_state, 0);
    if (sim_population_count_ants(world, rng,
                                  context->population_effects) != SIM_POPULATION_OK)
        return SIM_WORLDGEN_UNSUPPORTED;
    world->dirty_map.x = 0;
    world->dirty_map.y = 0;
    world->dirty_map.columns = SIM_WORLD_WIDTH;
    world->dirty_map.rows = SIM_WORLD_HEIGHT;
    world->dirty_map.valid = 1;
    if (!effect_add(context->effects, SIM_WORLDGEN_MAP_INVALIDATE,
                    0, 0, SIM_WORLD_WIDTH, SIM_WORLD_HEIGHT))
        return SIM_WORLDGEN_UNSUPPORTED;
    world->map_focus[0][0] = 0x40;
    world->map_focus[0][1] = 0x20;
    world->map_focus[1][0] = 0x20;
    world->map_focus[1][1] = 1;
    world->map_focus[2][0] = 0x20;
    world->map_focus[2][1] = 1;
    world->map_view_x = 0x40;
    world->map_view_y = 0x20;
    return context->nest_trace->overflow || context->effects->overflow
        ? SIM_WORLDGEN_UNSUPPORTED : SIM_WORLDGEN_OK;
}

SimWorldgenStatus sim_worldgen_start_new_game(
    SimGameWorld *world, SimRng *rng, const SimNewGameConfig *config,
    SimNativeWorldgenContext *context)
{
    SimSetupStatus setup_status;
    SimWorldgenStatus status;
    uint16_t seed;
    int16_t black_size;

    if (world == NULL || rng == NULL || config == NULL || context == NULL ||
        context->setup_state == NULL || context->setup_controls == NULL ||
        context->setup_hooks == NULL || context->yard_scene == NULL ||
        context->setup_hooks->resource_size == NULL ||
        context->setup_hooks->get_object_rect == NULL ||
        context->setup_hooks->refresh_control == NULL ||
        context->rand_world.setup_state != context->setup_state ||
        context->rand_world.spider == NULL ||
        context->rand_world.nest_runtime == NULL ||
        context->rand_world.nest_trace == NULL ||
        context->rand_world.effects == NULL ||
        context->rand_world.population_effects == NULL)
        return SIM_WORLDGEN_UNSUPPORTED;

    world->scenario = config->scenario;
    world->difficulty = config->difficulty;
    world->requested_preset_x = config->preset_x;
    world->requested_preset_y = config->preset_y;
    sim_world_clear_arrays(world);
    sim_setup_clear_history(context->setup_state, 1);
    setup_status = sim_setup_init_controls(context->setup_controls,
                                           context->setup_hooks);
    if (setup_status != SIM_SETUP_OK)
        return setup_status == SIM_SETUP_UNSUPPORTED
            ? SIM_WORLDGEN_UNSUPPORTED : SIM_WORLDGEN_INVALID_ARGUMENT;

    world->nest_preset_x[0] = 11;
    world->nest_preset_x[1] = 11;
    world->nest_preset_y[0] = 8;
    world->nest_preset_y[1] = 8;
    world->lifetime_graph_preset[0] = 11;
    world->lifetime_graph_preset[1] = 8;
    sim_yard_init_scene(context->yard_scene);
    world->player_update_code = -1;
    world->player_flags = 0;
    world->player_mode = 0;
    world->player_needs_init = 0;
    world->health_force_full = 0;
    world->source_state_0214 = 0;
    world->source_state_0204 = 0;
    world->source_state_0228 = 0;
    world->source_state_0478 = 0;
    world->source_state_0504 = 0;
    world->population_selection_colony = 0;
    world->population_selection_pending = 0;
    world->source_state_0c44 = 0;
    world->source_state_0c18 = 0;
    world->source_state_0c14 = 0;
    world->player_death_plane = 0;
    world->population_new_game = 1;
    sim_population_effects_reset(context->rand_world.population_effects);
    world->world_ticks = 0;
    world->cycle = 0;
    world->yard_mode = 0;
    world->map_plane = world->scenario <= 1 ? 2 : 1;
    world->selected_map_plane = world->map_plane;
    world->map_width = 11;
    world->world_kind = world->scenario == 2 ? 0 : 1;
    world->map_view_x = 0x40;
    world->map_view_y = 0x20;
    world->map_focus[0][0] = 0x40;
    world->map_focus[0][1] = 0x20;
    world->map_focus[1][0] = 0x20;
    world->map_focus[1][1] = 1;
    world->map_focus[2][0] = 0x20;
    world->map_focus[2][1] = 1;
    if (!fill_seed_table(world, rng))
        return SIM_WORLDGEN_RNG_ERROR;

    seed = world->random_seed_grid[8u * 12u + 11u];
    black_size = world->scenario == 2 ? 0 : 1;
    status = sim_worldgen_rand_world(world, rng, seed, black_size, 1, 11, 8,
                                     &context->rand_world);
    if (status != SIM_WORLDGEN_OK)
        return status;
    if (world->current_ant_plane <= 1) {
        world->map_focus[0][0] = world->me_x;
        world->map_focus[0][1] = world->me_y;
    } else if (world->current_ant_plane == 2) {
        world->map_focus[1][0] = world->me_x;
        world->map_focus[1][1] = world->me_y;
    } else {
        world->map_focus[2][0] = world->me_x;
        world->map_focus[2][1] = world->me_y;
    }
    return SIM_WORLDGEN_OK;
}

