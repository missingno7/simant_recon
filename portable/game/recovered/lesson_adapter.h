#ifndef SIMANT_PORTABLE_GAME_RECOVERED_LESSON_ADAPTER_H
#define SIMANT_PORTABLE_GAME_RECOVERED_LESSON_ADAPTER_H

#include "../simulation/tick.h"
#include "../simulation/nest.h"

typedef enum SimLessonStatus {
    SIM_LESSON_OK = 0,
    SIM_LESSON_INVALID_ARGUMENT,
    SIM_LESSON_SERVICE_UNAVAILABLE,
    SIM_LESSON_MAP_COORDINATE_UNAVAILABLE
} SimLessonStatus;

/* Source values not yet owned by the typed simulation structures. Their names
 * retain the original globals so a recovered-state projection can populate
 * them without inventing new semantics. fd_50F6_1074 is mutable in lesson 54. */
typedef struct SimLessonState {
    int16_t fd_50F6_0AA0;
    int16_t fd_50F6_0B1E;
    int16_t fd_50F6_1074;
    int16_t fd_50F6_035C;
    int16_t modeLevels[3];
} SimLessonState;

typedef struct SimLessonServices {
    /* Source f_00F8_02BE / MacTickCount; signed source long return. */
    int32_t (*mac_tick_count)(void *context);
    /* Source fastcall f_22BF_0A22, AX = window ID; returns source AX. */
    int16_t (*window_is_in_front)(void *context, int16_t window_id);
    /* Source SetAlarmDropState(state, quiet), called only for lesson 30. */
    void (*set_alarm_drop_state)(void *context, int16_t state, int16_t quiet);
    void *context;
} SimLessonServices;

/* Evaluates the frozen source LessonDone body over typed state. Returns
 * SERVICE_UNAVAILABLE only when the reached source path requires a missing
 * host service. Map access is bounds-checked and reports unavailable rather
 * than reading outside the native 128x64 surface. */
SimLessonStatus sim_lesson_done(SimGameWorld *world, SimTickState *tick_state,
                                SimNestRuntime *nest_runtime,
                                SimLessonState *lesson_state,
                                const SimLessonServices *services,
                                int16_t lesson, int16_t *done);
const char *sim_lesson_status_string(SimLessonStatus status);

#endif
