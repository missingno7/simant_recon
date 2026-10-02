#ifndef SIMANT_GAME_SIMULATION_WORLDGEN_H
#define SIMANT_GAME_SIMULATION_WORLDGEN_H

#include "rng.h"
#include "nest.h"
#include "spider.h"
#include "setup.h"
#include "yard.h"
#include "population.h"
#include "../state/world.h"

typedef enum SimWorldgenStatus {
    SIM_WORLDGEN_OK = 0,
    SIM_WORLDGEN_UNSUPPORTED = 1,
    SIM_WORLDGEN_INVALID_ARGUMENT = 2,
    SIM_WORLDGEN_RNG_ERROR = 3
} SimWorldgenStatus;

typedef struct SimNewGameConfig {
    int16_t scenario;
    int16_t difficulty;
    int16_t preset_x;
    int16_t preset_y;
} SimNewGameConfig;

typedef enum SimWorldgenEffectKind {
    SIM_WORLDGEN_PLAYER_SELECTION = 1,
    SIM_WORLDGEN_MAP_INVALIDATE = 2
} SimWorldgenEffectKind;

typedef struct SimWorldgenEffect {
    uint16_t kind;
    int16_t values[4];
} SimWorldgenEffect;

#define SIM_WORLDGEN_EFFECT_CAPACITY 16

typedef struct SimWorldgenEffects {
    uint16_t count;
    uint8_t overflow;
    SimWorldgenEffect events[SIM_WORLDGEN_EFFECT_CAPACITY];
} SimWorldgenEffects;

typedef struct SimRandWorldContext {
    SimSetupState *setup_state;
    SimSpiderState *spider;
    SimNestRuntime *nest_runtime;
    SimNestTrace *nest_trace;
    const int16_t *sine_q15; /* 64 values loaded from the game resource */
    SimWorldgenEffects *effects;
    SimPopulationEffects *population_effects;
} SimRandWorldContext;

typedef struct SimNativeWorldgenContext {
    SimSetupState *setup_state;
    SimSetupControls *setup_controls;
    const SimSetupHooks *setup_hooks;
    SimYardScene *yard_scene;
    SimRandWorldContext rand_world;
} SimNativeWorldgenContext;

/* Program startup only: inject the two original TickCount results used by
 * SeedRRand. A NewGame call must preserve and continue the existing streams. */
void sim_worldgen_seed_startup_rng(SimRng *rng, uint32_t lfsr_tick,
                                   uint32_t c_runtime_tick);

/* Source-derived RandWorld core. It directly calls the native terrain,
 * spider, ant-list, and nest helpers; the sine table is a required original
 * resource input. UI-facing player selection/music/invalidation are retained
 * as typed effects in the required output buffer. */
SimWorldgenStatus sim_worldgen_rand_world(
    SimGameWorld *world, SimRng *rng, uint16_t seed,
    int16_t black_size, int16_t red_size, int16_t map_width, int16_t map_kind,
    SimRandWorldContext *context);

/* Production native path: composes the recovered setup/control, yard scene,
 * terrain, ant, spider, nest, and world-generation modules without replacing
 * any game-rule operation with a generic callback. Required host resource and
 * UI geometry calls remain explicit in SimSetupHooks. */
SimWorldgenStatus sim_worldgen_start_new_game(
    SimGameWorld *world, SimRng *rng, const SimNewGameConfig *config,
    SimNativeWorldgenContext *context);

#endif
