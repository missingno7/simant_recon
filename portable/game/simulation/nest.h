#ifndef SIMANT_GAME_SIMULATION_NEST_H
#define SIMANT_GAME_SIMULATION_NEST_H

#include <stdint.h>

#include "rng.h"
#include "../state/world.h"

typedef struct SimNestRuntime {
    int16_t alarm_drop_state;
    int16_t alarm_indicator;
    int16_t theme_index;
    int32_t theme_last_tick;
    int16_t invalidate_right;
    int16_t invalidate_bottom;
    int32_t dug_b_x_sum;
    int32_t dug_b_y_sum;
    int32_t dug_r_x_sum;
    int32_t dug_r_y_sum;
    int16_t dug_b_count;
    int16_t dug_r_count;
    int16_t dug_b_x_average;
    int16_t dug_b_y_average;
    int16_t dug_r_x_average;
    int16_t dug_r_y_average;
    int16_t entrance_b_surface_x;
    int16_t entrance_b_surface_y;
    int16_t entrance_r_surface_x;
    int16_t entrance_r_surface_y;
    int16_t entrance_b_nest_x;
    int16_t entrance_b_nest_y;
    int16_t entrance_r_nest_x;
    int16_t entrance_r_nest_y;
} SimNestRuntime;

typedef enum SimNestEventKind {
    SIM_NEST_TICK = 1,
    SIM_NEST_SONG = 2,
    SIM_NEST_ALARM_CLEAR = 3,
    SIM_NEST_ALARM_SELECTION = 4,
    SIM_NEST_MAP_INVALIDATE = 5,
    SIM_NEST_SOUND = 6,
    SIM_NEST_TRY_THEME = 7,
    SIM_NEST_CLEAR_LIFE = 8,
    SIM_NEST_SET_LIFE = 9,
    SIM_NEST_DIG_TILE = 10,
    SIM_NEST_SRAND1 = 11
} SimNestEventKind;

typedef struct SimNestEvent {
    uint16_t kind;
    uint16_t argument_count;
    int32_t arguments[6];
} SimNestEvent;

/* A nonzero sink result accepts the source-ordered event. Returning zero
 * rejects it and stops the native transition with SIM_NEST_EVENT_REJECTED. */
typedef int (*SimNestEventSink)(void *context, const SimNestEvent *event);

#define SIM_NEST_EVENT_CAPACITY 256

typedef struct SimNestRequest {
    /* Two entries cover the original TryAntTheme conditional read and its
     * second tick read when the old theme has expired. */
    int32_t tick_values[2];
    uint8_t tick_count;
} SimNestRequest;

/* Optional source-clock boundary. It is called at each original TickCount
 * read, rather than sampled up front, so synchronous effects between reads
 * can advance the clock. A zero return reports provider failure. */
typedef int (*SimNestTickCountProvider)(void *context, int32_t *value);

typedef struct SimNestTrace {
    uint16_t count;
    uint8_t overflow;
    SimNestEvent events[SIM_NEST_EVENT_CAPACITY];
} SimNestTrace;

typedef enum SimNestStatus {
    SIM_NEST_OK = 0,
    SIM_NEST_INVALID_ARGUMENT = 1,
    SIM_NEST_TICK_INPUT_EXHAUSTED = 2,
    SIM_NEST_TRACE_OVERFLOW = 3,
    SIM_NEST_EVENT_REJECTED = 4,
    SIM_NEST_TICK_PROVIDER_FAILED = 5
} SimNestStatus;

/* Executes the source-level nest transition over native arrays and state.
 * Tick values are explicit inputs; returned trace entries carry logical sound,
 * song, alarm-selection, and map-invalidation requests for the host layer. */
SimNestStatus sim_enter_nest(SimGameWorld *world, SimRng *rng,
                             SimNestRuntime *runtime,
                             const SimNestRequest *request,
                             SimNestTrace *trace);

/* Sink-aware variant for host adapters. Events are still copied into trace,
 * then synchronously offered to the optional sink in source append order.
 * Returning zero aborts this transition with SIM_NEST_EVENT_REJECTED. */
SimNestStatus sim_enter_nest_with_sink(SimGameWorld *world, SimRng *rng,
                                       SimNestRuntime *runtime,
                                       const SimNestRequest *request,
                                       SimNestTrace *trace,
                                       SimNestEventSink event_sink,
                                       void *event_context);

/* Same transition with an on-demand host TickCount provider. When nonnull,
 * this takes precedence over request samples; the legacy/static entry points
 * remain unchanged for differential fixtures. */
SimNestStatus sim_enter_nest_with_tick_provider(
    SimGameWorld *world, SimRng *rng, SimNestRuntime *runtime,
    const SimNestRequest *request, SimNestTrace *trace,
    SimNestEventSink event_sink, void *event_context,
    SimNestTickCountProvider tick_provider, void *tick_context);

/* Shared source-derived nest/map operations for world generation and queen
 * placement. Planes must be 2 (black) or 3 (red); traces preserve RNG/dig
 * operation order for differential review. */
SimNestStatus sim_nest_dig_tile(SimGameWorld *world, SimRng *rng,
                                SimNestRuntime *runtime, SimNestTrace *trace,
                                int16_t plane, int16_t x, int16_t y);
SimNestStatus sim_nest_make_new_hole(SimGameWorld *world, SimRng *rng,
                                     SimNestRuntime *runtime, SimNestTrace *trace,
                                     int16_t plane, int16_t nest_x);
SimNestStatus sim_nest_dig_my_tile(SimGameWorld *world, SimRng *rng,
                                   SimNestRuntime *runtime, SimNestTrace *trace,
                                   int16_t plane, int16_t x, int16_t y);

#endif
