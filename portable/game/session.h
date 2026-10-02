#ifndef SIMANT_PORTABLE_GAME_SESSION_H
#define SIMANT_PORTABLE_GAME_SESSION_H

#include "resources/database.h"
#include "resources/tiles.h"
#include "simulation/feeding.h"
#include "simulation/worldgen.h"
#include "../render/bitmap.h"
#include "../ui_model/windows/registry.h"

#include <stdint.h>

#define SIM_SESSION_INITIALIZER { 0 }

typedef enum SimSessionStatus {
    SIM_SESSION_OK = 0,
    SIM_SESSION_BAD_ARGUMENT,
    SIM_SESSION_DATABASE_ERROR,
    SIM_SESSION_RESOURCE_ERROR,
    SIM_SESSION_REGISTRY_ERROR,
    SIM_SESSION_SETUP_ERROR,
    SIM_SESSION_WORLDGEN_ERROR,
    SIM_SESSION_ALREADY_STARTED
} SimSessionStatus;

typedef struct SimSessionControlVisual {
    /* The host may attach an owned animation resource after the UI layer has
     * loaded one. initControls' source `...Closed` path releases it before
     * replacing the model. Startup owns no animation and therefore leaves
     * these pointers null. */
    void *animation_resource;
    void (*release_animation)(void *resource);
    SimSetupRect rectangle;
    SimSetupPoint point;
    uint32_t generation;
    uint8_t active;
} SimSessionControlVisual;

typedef struct SimSession {
    PortableDatabase shared_database;
    PortableDatabase *window_database; /* Borrowed from the host startup. */
    PortableWindowRegistry *window_registry; /* Borrowed; must outlive session. */
    PortableTileSet tileset;
    SimGameWorld world;
    SimRng rng;
    SimFeedingState feeding;
    SimFeedingTrace feeding_trace;
    SimSetupState setup_state;
    SimSetupControls setup_controls;
    SimSetupHooks setup_hooks;
    SimYardScene yard_scene;
    SimSpiderState spider;
    SimNestRuntime nest_runtime;
    SimNestTrace nest_trace;
    SimWorldgenEffects worldgen_effects;
    SimPopulationEffects population_effects;
    int16_t sine_q15[64];
    SimNativeWorldgenContext worldgen_context;
    SimSessionControlVisual controls[2];
    uint32_t startup_lfsr_tick;
    uint32_t startup_c_tick;
    uint8_t shared_open;
    uint8_t tileset_open;
    uint8_t resources_ready;
    uint8_t rng_seeded;
    uint8_t new_game_ready;
} SimSession;

/* Opens the actual SHARED database, loads the 0x03e8/kind-9 sine table and
 * HCEGANT-backed tileset, and borrows the host's already-open HCEGANT database
 * and initialized window registry for bitmap dimensions and object rectangles.
 * The borrowed objects must outlive the session. The session must be
 * zero-initialized or use SIM_SESSION_INITIALIZER. */
SimSessionStatus sim_session_init(SimSession *session,
                                  const char *assets_directory,
                                  PortableDatabase *window_database,
                                  PortableWindowRegistry *window_registry);
void sim_session_close(SimSession *session);

/* The two startup TickCount results are injected explicitly and consumed
 * exactly once. NewGame never reseeds either random stream. */
SimSessionStatus sim_session_seed_startup(SimSession *session,
                                          uint32_t lfsr_tick,
                                          uint32_t c_runtime_tick);

/* Runs source-derived setup and RandWorld with real resources/registry data.
 * No simulation, resource, or RNG operation is replaced by a stub. */
SimSessionStatus sim_session_new_game(SimSession *session,
                                      const SimNewGameConfig *config);

const char *sim_session_status_string(SimSessionStatus status);

#endif
