#ifndef SIMANT_WHOLE_PROGRAM_GRAPHICS_S00_MAP_TABLES_H
#define SIMANT_WHOLE_PROGRAM_GRAPHICS_S00_MAP_TABLES_H

#include <stddef.h>
#include <stdint.h>

#include "portable/whole_program/state/map_render_selectors.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef enum SimS00MapTableStatus {
    SIM_S00_MAP_TABLE_OK = 0,
    SIM_S00_MAP_TABLE_BAD_ARGUMENT,
    SIM_S00_MAP_TABLE_BAD_SPAN,
    SIM_S00_MAP_TABLE_UNSUPPORTED_COLOR,
    SIM_S00_MAP_TABLE_RENDERER_UNBOUND,
    SIM_S00_MAP_TABLE_RENDERER_FAILED
} SimS00MapTableStatus;

typedef enum SimS00MapTableProfile {
    SIM_S00_MAP_TABLE_640 = 0,
    SIM_S00_MAP_TABLE_320 = 1
} SimS00MapTableProfile;

struct SimGraphicsDriver;
typedef enum SimS00MapTableTransform {
    SIM_S00_TRANSFORM_0000 = 0,
    SIM_S00_TRANSFORM_0137,
    SIM_S00_TRANSFORM_026A,
    SIM_S00_TRANSFORM_03A9,
    SIM_S00_TRANSFORM_04D8,
    SIM_S00_TRANSFORM_06A3
} SimS00MapTableTransform;

/* Native byte-span equivalents of the six readable S00 m3126 transforms.
 * Source colors are limited to the indices 0..24 represented by the original
 * dither rules. Destinations are plane-major DOS planar buffers. */
SimS00MapTableStatus sim_s00_map_0000(const uint8_t *source, size_t source_size,
                                      uint8_t *destination, size_t destination_size);
SimS00MapTableStatus sim_s00_map_0137(const uint8_t *source, size_t source_size,
                                      uint8_t *destination, size_t destination_size);
SimS00MapTableStatus sim_s00_map_026A(const uint8_t *source, size_t source_size,
                                      uint8_t *destination, size_t destination_size);
SimS00MapTableStatus sim_s00_map_03A9(const uint8_t *source, size_t source_size,
                                      uint8_t *destination, size_t destination_size);
SimS00MapTableStatus sim_s00_map_04D8(const uint8_t *source, size_t source_size,
                                      uint8_t *destination, size_t destination_size,
                                      SimS00MapTableProfile profile);
SimS00MapTableStatus sim_s00_map_06A3(const uint8_t *source, size_t source_size,
                                      uint8_t *destination, size_t destination_size,
                                      SimS00MapTableProfile profile);

/* Original S00 entry names, adapted to native flat pointers. The first four
 * procedures consume fixed source spans; the two minimap procedures select
 * their table from the active application's g_3DB2 mode. */
void o00_3126_0000(char *source, char *destination, int16_t source_width, int16_t count);
void o00_3126_0137(char *source, char *destination, int16_t source_width, int16_t count);
void o00_3126_026A(char *source, char *destination, int16_t source_width, int16_t count);
void o00_3126_03A9(char *source, char *destination, int16_t source_width, int16_t count);
void o00_3126_04D8(char *source, char *destination);
void o00_3126_06A3(char *source, char *destination);

/* Convert then send the result through the already-bound source g914C renderer
 * into the application's one SimGraphicsDriver framebuffer. */
SimS00MapTableStatus sim_s00_map_transform_draw(
    struct SimGraphicsDriver *graphics, SimS00MapTableTransform transform,
    int16_t x, int16_t y, const uint8_t *source, size_t source_size);

#ifdef __cplusplus
}
#endif
#endif
