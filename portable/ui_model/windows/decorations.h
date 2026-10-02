#ifndef SIMANT_PORTABLE_UI_MODEL_WINDOWS_DECORATIONS_H
#define SIMANT_PORTABLE_UI_MODEL_WINDOWS_DECORATIONS_H

#include "window.h"

#include <stddef.h>
#include <stdint.h>

enum { PORTABLE_WINDOW_DECORATION_MAX_STEPS = 16 };

typedef enum PortableWindowDecorationStepKind {
    PORTABLE_WINDOW_DECORATION_LOOKUP_SIZE = 1,
    PORTABLE_WINDOW_DECORATION_REGISTER = 2,
    PORTABLE_WINDOW_DECORATION_UNREGISTER = 3
} PortableWindowDecorationStepKind;

typedef struct PortableWindowDecorationMetrics {
    int16_t object_id;
    int16_t width;
    int16_t height;
} PortableWindowDecorationMetrics;

typedef struct PortableWindowDecorationStep {
    PortableWindowDecorationStepKind kind;
    int16_t object_id;
    int16_t mode; /* f_1FD2_0883 ticks/code argument, e.g. 0xF083. */
    int16_t x;
    int16_t y;
    PortableWindowRect hit_rect; /* Meaningful for REGISTER only. */
} PortableWindowDecorationStep;

typedef struct PortableWindowDecorationInput {
    PortableWindowRect window_rect;
    int16_t window_flags;
    int8_t margin;
    int16_t show;
    const PortableWindowDecorationMetrics *metrics;
    size_t metric_count;
} PortableWindowDecorationInput;

typedef enum PortableWindowDecorationStatus {
    PORTABLE_WINDOW_DECORATION_OK = 0,
    PORTABLE_WINDOW_DECORATION_BAD_ARGUMENT,
    PORTABLE_WINDOW_DECORATION_MISSING_METRIC,
    PORTABLE_WINDOW_DECORATION_COORDINATE_OVERFLOW,
    PORTABLE_WINDOW_DECORATION_CAPACITY
} PortableWindowDecorationStatus;

typedef struct PortableWindowDecorationHit {
    int16_t object_id;
    int16_t mode;
} PortableWindowDecorationHit;

/* Source model of root:m2505 f_2505_06B9 plus f_1FD2_0883's registration
 * rectangle construction. It models only this call's requested decoration
 * operations, not dynamic scanner-list lifetime or other registration sites. */
PortableWindowDecorationStatus portable_window_decorations_plan(
    const PortableWindowDecorationInput *input,
    PortableWindowDecorationStep *steps,
    size_t capacity,
    size_t *step_count);

/* Source f_1B73_0B00 prepends registrations; among this plan's active boxes,
 * the latest registration wins and edges are inclusive (f_1B73_0CEF). */
int portable_window_decoration_hit_test(
    const PortableWindowDecorationStep *steps,
    size_t step_count,
    PortableWindowPoint point,
    PortableWindowDecorationHit *hit);

#endif
