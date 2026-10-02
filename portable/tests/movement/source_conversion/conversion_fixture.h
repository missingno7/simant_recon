#ifndef SOURCE_CONVERSION_FIXTURE_H
#define SOURCE_CONVERSION_FIXTURE_H

#include <stdint.h>
#include "portable/game/simulation/movement.h"

typedef SimWorldTiles SourceConversionWorld;

typedef struct SourceConversionCall {
    int16_t kind; /* 1 GetDir, 2 GetDis, 3 TileCanBeMovedOn */
    int16_t args[7];
} SourceConversionCall;

typedef struct SourceConversionResult {
    int16_t result;
    int16_t rot;
    int16_t direction;
    int16_t call_count;
    SourceConversionCall calls[32];
} SourceConversionResult;

void source_conversion_run(const SourceConversionWorld *world,
                           const int8_t *dx, const int8_t *dy,
                           int16_t mode, int16_t from_plane,
                           int16_t from_x, int16_t from_y,
                           int16_t previous_x, int16_t previous_y,
                           int16_t plane, int16_t x, int16_t y,
                           int16_t target_x, int16_t target_y,
                           int16_t initial_rot, int16_t initial_direction,
                           SourceConversionResult *result);

#endif
