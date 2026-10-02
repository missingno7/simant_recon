#ifndef SIMANT_PORTABLE_UI_MODEL_DIALOGS_GAME_OVER_H
#define SIMANT_PORTABLE_UI_MODEL_DIALOGS_GAME_OVER_H

#include <stdint.h>

enum {
    SIM_GAME_OVER_HISTORY_CAPACITY = 64,
    SIM_GAME_OVER_SCORE_COMPONENTS = 8,
    SIM_GAME_OVER_TUTORIAL_ROWS = 12,
    SIM_GAME_OVER_TUTORIAL_COLUMNS = 16,
    SIM_GAME_OVER_WINDOW_ID = 0x0400,
    SIM_GAME_OVER_SCENARIO_OBJECT = 0x0402,
    SIM_GAME_OVER_SCORE_OBJECT = 0x0403,
    SIM_GAME_OVER_LEVEL_OBJECT = 0x0404,
    SIM_GAME_OVER_SCENARIO_STRINGS = 1001,
    SIM_GAME_OVER_LEVEL_STRINGS = 1900,
    SIM_GAME_OVER_STRING_KIND = 4
};

typedef enum SimGameOverStatus {
    SIM_GAME_OVER_OK = 0,
    SIM_GAME_OVER_BAD_ARGUMENT,
    SIM_GAME_OVER_INVALID_STATE
} SimGameOverStatus;

/* Source-valued inputs to S14:CalcScore and EndGameDialog. The comments name
 * the DOS globals so a future RecoveredState adapter can map them explicitly.
 */
typedef struct SimGameOverInput {
    int16_t history_cursor;       /* fd_50F6_04F4 */
    int16_t history_count;        /* fd_3D57_0828; source accepts 0..63 */
    int16_t health_history[SIM_GAME_OVER_HISTORY_CAPACITY]; /* 073C */
    int16_t blue_food_history[SIM_GAME_OVER_HISTORY_CAPACITY]; /* 0626 */
    int16_t red_food_history[SIM_GAME_OVER_HISTORY_CAPACITY]; /* 06AE */
    int32_t food_total;           /* fd_50F6_0FC2 */
    int32_t food_used;            /* fd_50F6_1000 */
    int16_t blue_workers;         /* fd_50F6_09FA */
    int16_t red_workers;          /* fd_50F6_0A00 */
    int16_t scenario;             /* fd_50F6_0EAC */
    int16_t blue_colony_score;    /* fd_50F6_0A90 */
    int16_t colony_score_a;       /* fd_50F6_0AC4 */
    int16_t colony_score_b;       /* fd_50F6_0A9E */
    uint8_t tutorial_marks[SIM_GAME_OVER_TUTORIAL_ROWS]
                            [SIM_GAME_OVER_TUTORIAL_COLUMNS]; /* 3D57:00A4 */
    int16_t health;               /* MeHealth */
    int32_t world_ticks;          /* fd_50F6_0C26 */
    int16_t losing_side;          /* fd_50F6_0366; zero is a win */
    uint8_t sound_enabled;        /* fd_3D57_07A8[1] / 07AA */
    uint16_t screen_width;        /* g_3DB2 */
} SimGameOverInput;

typedef struct SimGameOverResult {
    int16_t components[SIM_GAME_OVER_SCORE_COMPONENTS];
    int32_t score;                /* CalcScore return, also object 0x0403 */
    int32_t rank_score;           /* scenario 2 divides score by five */
    uint8_t level_index;          /* fd_50F6_0328[level], 0..9 */
    int16_t opening_sound_id;     /* zero when disabled; else 0x2718/0x271a */
    int16_t sound_argument;       /* source constant 0x7e */
    int16_t font_id;              /* 2 at 320px; 4 otherwise */
    int16_t scenario_index;       /* input scenario, index in resource 1001 */
    int16_t scenario_resource_id; /* LoadStringAnt(1001), kind 4 */
    int16_t level_resource_id;    /* LoadStringAnt(1900), kind 4 */
    int16_t window_id;            /* 0x0400 */
    int16_t scenario_object_id;   /* 0x0402 */
    int16_t score_object_id;      /* 0x0403 */
    int16_t level_object_id;      /* 0x0404 */
} SimGameOverResult;

/* Computes the source score, rank band, and initial presentation values.
 * History integer operations preserve the original 16-bit signed width, and
 * long arithmetic preserves 32-bit wrap. Resource strings and modal services
 * remain host-owned; this function performs no I/O or state mutation. The
 * source opens window 0x0400, writes scenario text from kind-4 table 1001 to
 * object 0x0402, the long score to 0x0403, and a label from kind-4 table 1900
 * to 0x0404. It waits until the window closes or the quit service fires,
 * then calls NewGame(0) (o15_384C_03C6); a negative result calls MenuQuit
 * (o15_384C_01EE). These aliases are confirmed in layout/symbols.json. */
SimGameOverStatus sim_game_over_calculate(const SimGameOverInput *input,
                                         SimGameOverResult *result);

/* Source EndGameDialog bands are strict upper bounds. The scenario-2 score is
 * divided by five before band selection; source winning-side value zero adds
 * five to the band for display. */
SimGameOverStatus sim_game_over_level(int32_t score, int16_t scenario,
                                     int16_t losing_side,
                                     int32_t *rank_score,
                                     uint8_t *level_index);

const char *sim_game_over_status_string(SimGameOverStatus status);

#endif
