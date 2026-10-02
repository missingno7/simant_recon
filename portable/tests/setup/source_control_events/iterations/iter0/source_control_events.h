#ifndef SOURCE_CONTROL_EVENTS_H
#define SOURCE_CONTROL_EVENTS_H

#include <stdint.h>

/* Test-only fixed-width projection of the globals touched by root:m0798.c.
 * A fixture owns one instance for one event invocation, then copies only the
 * source-owned fields back to its comparison record. */
typedef struct SourceCtlResult {
    int16_t automatic, selector, percent;
    uint16_t current[3], presets[12];
    int16_t ideal_caste[4], point[2];
    int event_count;
    int32_t events[64][9];
} SourceCtlResult;

/* kind: 0=mode, 1=caste. rect[4], metrics[3], initial point, control point,
 * then staged cursor samples exactly as in dos-control-events.json. */
int source_control_event_run(int kind, uint16_t code, int16_t start_auto,
    int16_t start_selector, int16_t start_percent,
    const int16_t rect[4], const uint16_t metrics[3],
    const int16_t initial_point[2], const int16_t control_point[2],
    const int16_t *samples, int sample_count, SourceCtlResult *result);

#endif
