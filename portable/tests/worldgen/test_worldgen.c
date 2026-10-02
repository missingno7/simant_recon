#include "../../game/simulation/rng.h"
#include "../../game/simulation/worldgen.h"
#include "../../game/simulation/ants.h"
#include "../../game/simulation/spider.h"

#include <assert.h>
#include <stdio.h>
#include <string.h>

static uint16_t reference_s_next(uint16_t *seed)
{
    uint16_t v = (uint16_t)(*seed << 1);
    if (*seed & 0x8000u)
        v ^= 0x1bf5u;
    *seed = v;
    return v;
}

static uint16_t reference_c_rand(uint32_t *seed)
{
    *seed = *seed * 214013u + 2531011u;
    return (uint16_t)((*seed >> 16) & 0x7fffu);
}

static void test_lfsr_and_msc_rand(void)
{
    SimRng rng = { 0, 1 };
    uint16_t expected_s = 0x8001u;
    uint32_t expected_c = 1;
    uint16_t value;
    unsigned i;

    sim_rng_set_s_seed(&rng, (int16_t)0x8001u);
    for (i = 0; i < 10000; ++i) {
        uint16_t expected = reference_s_next(&expected_s);
        assert(sim_rng_s256(&rng) == (expected & 0xffu));
        assert(sim_rng_get_s_seed(&rng) == expected_s);
    }

    rng.c_state = 1;
    assert(sim_rng_msc_rand(&rng) == 41);
    expected_c = 1u * 214013u + 2531011u;
    for (i = 0; i < 10000; ++i)
        assert(sim_rng_msc_rand(&rng) == reference_c_rand(&expected_c));

    rng.s_state = 0x1234;
    assert(sim_rng_s1(&rng, 0, &value) == 0);
    assert(rng.s_state == 0x1234);
}

static void test_seed_warmup(void)
{
    SimRng rng = { 0, 0 };
    uint16_t expected_s = (uint16_t)(0x12345678u ^ 0x3751u);
    uint32_t expected_c = (uint16_t)0x89abcdefu;
    uint16_t warmup = (uint16_t)(reference_s_next(&expected_s) & 0x7fu);
    uint16_t i;

    for (i = 0; i < warmup; ++i)
        (void)reference_c_rand(&expected_c);
    sim_rng_seed_r(&rng, 0x12345678u, 0x89abcdefu);
    assert(rng.s_state == expected_s);
    assert(rng.c_state == expected_c);
}

static void test_historical_oracle_vectors(void)
{
    static const uint16_t lfsr_expected[8] = {
        52, 104, 221, 183, 109, 74, 148, 238
    };
    static const int16_t rrand_zero_ticks[12] = {
        16907, 21237, 23611, 12617, 12456, 867,
        29533, 6878, 28223, 17887, 31597, 20584
    };
    static const int16_t rrand_ticks[12] = {
        1294, 27160, 5119, 31079, 5444, 15649,
        29728, 8337, 20320, 27965, 184, 31554
    };
    SimRng rng = { 0, 0 };
    uint16_t got;
    unsigned i;

    /* Captured with tools/behavior.py by executing the original module
     * root:0093, including original SeedRRand + MSC rand() call sequence. */
    sim_rng_set_s_seed(&rng, 0x3751);
    for (i = 0; i < 8; ++i) {
        assert(sim_rng_s1(&rng, 0x101, &got));
        assert(got == lfsr_expected[i]);
    }

    sim_rng_seed_r(&rng, 0, 0);
    for (i = 0; i < 12; ++i) {
        int16_t got_r;
        assert(sim_rng_r(&rng, 0x7fff, &got_r));
        assert(got_r == rrand_zero_ticks[i]);
    }

    sim_rng_seed_r(&rng, 0x12345678u, 0x89abcdefu);
    for (i = 0; i < 12; ++i) {
        int16_t got_r;
        assert(sim_rng_r(&rng, 0x7fff, &got_r));
        assert(got_r == rrand_ticks[i]);
    }
}

static void test_source_initializers(void)
{
    SimGameWorld world;
    memset(&world, 0x5a, sizeof world);
    world.tiles.terrain_set = 7;
    world.ants_a.count = 19;
    world.ants_a.x[0] = 37;
    world.ants_a.type[0] = 0x41;
    world.ants_b.count = 8;
    world.ants_b.mode[0] = 3;
    sim_world_clear_arrays(&world);
    assert(world.tiles.surface[0][0] == 0);
    assert(world.tiles.nest_b[63][63] == 0);
    assert(world.life_a[127][63] == 0);
    assert(world.pheromone_r_trail[63][31] == 0);
    assert(world.ants_a.type[0] == 0 && world.ants_a.mode[0] == 0 &&
           world.ants_a.state[0] == 0);
    assert(world.ants_a.x[0] == 37 && world.ants_a.count == 19);
    assert(world.ants_b.mode[0] == 0 && world.ants_b.count == 8);
    assert(world.tiles.terrain_set == 7);

    sim_world_init_sim_vars(&world);
    assert(world.selected_map_plane == 0);
    assert(world.simulation_speed_index == 1);
    assert(world.health_warning_threshold == 30 &&
           world.colony_health_warning_threshold == 30);
    assert(world.current_experiment_tool == 0);
    assert(world.experience_flags[0] == 0 && world.experience_flags[1] == 0);
    assert(world.world_state_flag == 0);
}

static void test_native_rand_world_is_deterministic(void)
{
    SimGameWorld a, b;
    SimRng rng_a = { 0, 0x12345678u };
    SimRng rng_b = { 0, 0x12345678u };
    SimSpiderState spider_a, spider_b;
    SimSetupState setup_a = { 0 }, setup_b = { 0 };
    SimNestRuntime nest_a = { 0 }, nest_b = { 0 };
    SimNestTrace trace_a = { 0 }, trace_b = { 0 };
    SimWorldgenEffects effects_a = { 0 }, effects_b = { 0 };
    SimPopulationEffects population_a = { 0 }, population_b = { 0 };
    SimRandWorldContext ctx_a, ctx_b;
    memset(&a, 0, sizeof a);
    memset(&b, 0, sizeof b);
    a.scenario = b.scenario = 2;
    a.world_kind = b.world_kind = 0;
    a.health_warning_threshold = b.health_warning_threshold = 30;
    memset(&spider_a, 0, sizeof spider_a);
    memset(&spider_b, 0, sizeof spider_b);
    sim_spider_init(&spider_a, &a);
    sim_spider_init(&spider_b, &b);
    ctx_a.spider = &spider_a;
    ctx_a.setup_state = &setup_a;
    ctx_a.nest_runtime = &nest_a;
    ctx_a.nest_trace = &trace_a;
    ctx_a.sine_q15 = spider_a.sine_q15;
    ctx_a.effects = &effects_a;
    ctx_a.population_effects = &population_a;
    ctx_b.spider = &spider_b;
    ctx_b.setup_state = &setup_b;
    ctx_b.nest_runtime = &nest_b;
    ctx_b.nest_trace = &trace_b;
    ctx_b.sine_q15 = spider_b.sine_q15;
    ctx_b.effects = &effects_b;
    ctx_b.population_effects = &population_b;

    assert(sim_worldgen_rand_world(&a, &rng_a, 0x5a31, 0, 1, 11, 8,
                                   &ctx_a) == SIM_WORLDGEN_OK);
    assert(sim_worldgen_rand_world(&b, &rng_b, 0x5a31, 0, 1, 11, 8,
                                   &ctx_b) == SIM_WORLDGEN_OK);
    assert(memcmp(&a, &b, sizeof a) == 0);
    assert(memcmp(&rng_a, &rng_b, sizeof rng_a) == 0);
    assert(memcmp(&spider_a, &spider_b, sizeof spider_a) == 0);
    assert(memcmp(&setup_a, &setup_b, sizeof setup_a) == 0);
    assert(memcmp(&nest_a, &nest_b, sizeof nest_a) == 0);
    assert(memcmp(&trace_a, &trace_b, sizeof trace_a) == 0);
    assert(memcmp(&effects_a, &effects_b, sizeof effects_a) == 0);
    assert(memcmp(&population_a, &population_b, sizeof population_a) == 0);
    assert(a.ants_r.count == 2 && a.queens_red == 1);
    assert(a.current_ant_plane == 1);
    assert(a.map_focus[0][0] == 0x40 && a.map_focus[0][1] == 0x20);
    assert(a.map_focus[1][0] == 0x20 && a.map_focus[1][1] == 1);
    assert(a.dirty_map.valid && a.dirty_map.columns == SIM_WORLD_WIDTH &&
           a.dirty_map.rows == SIM_WORLD_HEIGHT);
    assert(sim_ants_count(&a) >= 2);
}

typedef struct NativeSetupFixture {
    unsigned sequence;
} NativeSetupFixture;

static int native_resource_size(void *context, uint16_t object_id,
                                uint16_t kind, int16_t *width,
                                int16_t *height)
{
    NativeSetupFixture *fixture = (NativeSetupFixture *)context;
    assert(fixture->sequence++ == 0);
    assert(object_id == 0x578 && kind == 2);
    *width = 12;
    *height = 8;
    return 1;
}

static int native_object_rect(void *context, uint16_t object_id,
                              SimSetupRect *rect)
{
    NativeSetupFixture *fixture = (NativeSetupFixture *)context;
    assert(object_id == (fixture->sequence == 4 ? 0x130d : 0x120d));
    assert(fixture->sequence == 1 || fixture->sequence == 2 ||
           fixture->sequence == 4);
    ++fixture->sequence;
    rect->left = 0;
    rect->top = 0;
    rect->right = 100;
    rect->bottom = 60;
    return 1;
}

static int native_refresh(void *context, SimSetupControlKind kind,
                          const SimSetupControls *controls)
{
    NativeSetupFixture *fixture = (NativeSetupFixture *)context;
    (void)controls;
    assert(fixture->sequence == 3 || fixture->sequence == 5);
    assert(kind == (fixture->sequence == 3 ? SIM_SETUP_MODE_CONTROL
                                          : SIM_SETUP_CASTE_CONTROL));
    ++fixture->sequence;
    return 1;
}

static void test_native_new_game_bootstrap(void)
{
    SimGameWorld world;
    SimRng rng = { 0, 0x12345678u };
    SimRng expected_rng;
    SimNewGameConfig config = { 2, 3, 5, 6 };
    SimSetupState setup_state = { 0 };
    SimSetupControls controls = { 0 };
    SimYardScene yard_scene = { 0 };
    SimSpiderState spider = { 0 };
    SimNestRuntime nest_runtime = { 0 };
    SimNestTrace nest_trace = { 0 };
    SimWorldgenEffects effects = { 0 };
    SimPopulationEffects population_effects = { 0 };
    NativeSetupFixture fixture = { 0 };
    SimSetupHooks setup_hooks = {
        native_resource_size, native_object_rect, native_refresh, &fixture
    };
    SimNativeWorldgenContext context;
    unsigned i;
    memset(&world, 0, sizeof world);
    memset(&context, 0, sizeof context);
    sim_setup_controls_init_data(&controls);
    sim_worldgen_seed_startup_rng(&rng, 0x2468ace0u, 0x13572468u);
    expected_rng = rng;
    for (i = 0; i < 192; ++i)
        (void)sim_rng_msc_rand(&expected_rng);
    context.setup_state = &setup_state;
    context.setup_controls = &controls;
    context.setup_hooks = &setup_hooks;
    context.yard_scene = &yard_scene;
    context.rand_world.setup_state = &setup_state;
    context.rand_world.spider = &spider;
    context.rand_world.nest_runtime = &nest_runtime;
    context.rand_world.nest_trace = &nest_trace;
    context.rand_world.effects = &effects;
    context.rand_world.population_effects = &population_effects;
    context.rand_world.sine_q15 = spider.sine_q15;
    assert(sim_worldgen_start_new_game(&world, &rng, &config,
                                       &context) == SIM_WORLDGEN_OK);
    assert(fixture.sequence == 6);
    assert(world.scenario == 2 && world.difficulty == 3);
    assert(world.current_ant_plane == 1);
    assert(world.map_focus[0][0] == world.me_x &&
           world.map_focus[0][1] == world.me_y);
    assert(rng.c_state == expected_rng.c_state);
    assert(effects.count == 2);
    assert(effects.events[0].kind == SIM_WORLDGEN_PLAYER_SELECTION);
    assert(effects.events[1].kind == SIM_WORLDGEN_MAP_INVALIDATE);
}

int main(void)
{
    test_lfsr_and_msc_rand();
    test_seed_warmup();
    test_historical_oracle_vectors();
    test_source_initializers();
    test_native_rand_world_is_deterministic();
    test_native_new_game_bootstrap();
    puts("worldgen/RNG tests passed");
    return 0;
}
