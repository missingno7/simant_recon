#ifndef SIMANT_GAME_SIMULATION_SETUP_H
#define SIMANT_GAME_SIMULATION_SETUP_H

#include <stdint.h>

typedef enum SimSetupStatus {
    SIM_SETUP_OK = 0,
    SIM_SETUP_UNSUPPORTED = 1,
    SIM_SETUP_INVALID_ARGUMENT = 2,
    SIM_SETUP_CALLBACK_FAILED = 3
} SimSetupStatus;

/* State owned by S24 ClearHistory / o24_39C7_01B8. The series order follows
 * the ten source arrays at 50F6:0516, 05A0, 0626, 06AE, 073C, 07CE, 0856,
 * 08F0, 0970, 0A0A. Long counters are explicitly 32-bit. */
typedef struct SimSetupState {
    int16_t history_series[10][64];
    int16_t history_start;       /* fd_50F6_04F4 */
    int16_t graph_selection;     /* fd_3D57_0828 */
    int32_t black_ants_eaten;    /* BAntsEaten */
    int32_t red_ants_eaten;      /* RAntsEaten */
    int32_t counter_0f30;        /* fd_50F6_0F30 */
    int32_t counter_0efc;        /* fd_50F6_0EFC */
    int32_t history_counter_0fbc;
    int32_t history_counter_0f3e;
    int32_t history_counter_0fc2;
    int32_t history_counter_1000;
    int32_t value_0ada;          /* fd_50F6_0ADA; only reset for newGame == 1 */
    int16_t value_0a90;          /* fd_50F6_0A90; only reset for newGame == 1 */
    int16_t value_0ac4;          /* fd_50F6_0AC4; only reset for newGame == 1 */
    int16_t value_0a9e;          /* fd_50F6_0A9E; only reset for newGame == 1 */
    int16_t value_0ac8;          /* fd_50F6_0AC8; only reset for newGame == 1 */
} SimSetupState;

typedef struct SimSetupPoint {
    int16_t x;
    int16_t y;
} SimSetupPoint;

typedef struct SimSetupRect {
    int16_t left;
    int16_t top;
    int16_t right;
    int16_t bottom;
} SimSetupRect;

typedef struct SimSetupTriangle {
    uint16_t frac;
    uint16_t mid;
    uint16_t weight;
} SimSetupTriangle;

typedef enum SimSetupControlKind {
    SIM_SETUP_MODE_CONTROL = 0,
    SIM_SETUP_CASTE_CONTROL = 1
} SimSetupControlKind;

typedef struct SimSetupControls {
    int16_t knob_width;
    int16_t knob_height;
    int16_t mode_auto;
    int16_t caste_auto;
    int16_t mode_enabled;
    int16_t caste_enabled;
    /* Existing g_1B50/g_1B4E selectors: initControls does not change them. */
    int16_t mode_current;
    int16_t caste_current;
    int16_t state_0370;          /* fd_50F6_0370; initControls sets -1. */
    int16_t state_024e;          /* fd_50F6_024E; initControls sets -1. */
    /* Mutable DATA triples at 3D57:080A (mode) and 3D57:07EC (caste).
     * The source initControls reads these on every invocation. */
    SimSetupTriangle mode_defaults;
    SimSetupTriangle caste_defaults;
    SimSetupTriangle mode_levels[4];
    SimSetupTriangle caste_levels[4];
    SimSetupTriangle mode_level;
    SimSetupTriangle caste_level;
    int16_t ideal_caste[4];
    SimSetupRect mode_rect;
    SimSetupRect caste_rect;
    SimSetupPoint mode_point;
    SimSetupPoint caste_point;
    int16_t mode_width;
    int16_t mode_height;
    int32_t mode_slope;           /* fd_50F6_382E is a source long. */
    int16_t caste_width;
    int16_t caste_height;
    int32_t caste_slope;
    /* Set only by sim_setup_controls_init_data; prevents zeroed host state
     * from silently substituting invented defaults at initControls time. */
    uint8_t source_data_initialized;
} SimSetupControls;

typedef struct SimSetupHooks {
    /* f_208F_0419 uses db_LoadObject(object_id, kind); success must provide
     * the decoded object dimensions. The source call is (0x578, 2). */
    int (*resource_size)(void *context, uint16_t object_id, uint16_t kind,
                         int16_t *width, int16_t *height);
    /* win_GetObjRect: initControls first queries 0x120d as an unused rect,
     * then mode refresh queries 0x120d and caste refresh queries 0x130d. */
    int (*get_object_rect)(void *context, uint16_t object_id,
                           SimSetupRect *rect);
    /* Represents win_ModeControlChanged / win_CasteControlChanged in order;
     * the host/UI model must consume the computed control model. */
    int (*refresh_control)(void *context, SimSetupControlKind kind,
                           const SimSetupControls *controls);
    void *context;
} SimSetupHooks;

/* Source-derived ClearHistory. Every call clears all ten 64-entry series and
 * shared counters; the five lifetime/mode fields reset only for argument 1. */
void sim_setup_clear_history(SimSetupState *state, int16_t new_game);

/* Source cvtLevels2IdealCaste: ideal[0..3] from mid, weight, frac, frac. */
void sim_setup_convert_ideal_caste(const SimSetupTriangle *level,
                                   int16_t ideal[4]);

/* Source-derived root initControls / f_0798_0F0D. The caller first applies
 * sim_setup_controls_init_data once for a fresh session, then initializes
 * mode_current/caste_current from their source-global initial/current values.
 * initControls rereads the mutable defaults into the current triples and row
 * zero, while preserving preset rows one through three and both selectors.
 * Required platform/resource
 * operations fail closed when absent; successful setup preserves resource,
 * rectangle-query, mode-refresh, caste-refresh ordering. */
SimSetupStatus sim_setup_init_controls(SimSetupControls *controls,
                                      const SimSetupHooks *hooks);

/* Apply the source DATA image once when a fresh SimSession is constructed.
 * This initializes the two mutable default triples and all four preset rows;
 * NewGame/initControls must not call it again. */
void sim_setup_controls_init_data(SimSetupControls *controls);

#endif
