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
    SIM_S00_MAP_TABLE_RENDERER_FAILED,
    SIM_S00_MAP_TABLE_LAYOUT_UNBOUND,
    SIM_S00_MAP_TABLE_UNSUPPORTED_LAYOUT
} SimS00MapTableStatus;

typedef enum SimS00MapTableProfile {
    SIM_S00_MAP_TABLE_640 = 0,
    SIM_S00_MAP_TABLE_320 = 1
} SimS00MapTableProfile;

/* Virtual DOS address facts, never native callback addresses. The reference
 * load is one observed machine, not a universal DOS allocation guarantee.
 * The working canonical layout is admitted only for differential controls;
 * its different raster segment remains link-layout debt. See
 * evidence/enhanced-mode/map-frozen-dirty-cells.md. */
typedef struct SimS00MapDosLayout {
    uint16_t raster_segment;       /* image-relative DispatchS00 slot 0 segment */
    uint16_t next_callback_offset; /* slot 1, gfx_planar_select_small_font */
    uint16_t load_paragraph;
} SimS00MapDosLayout;

extern const SimS00MapDosLayout sim_s00_map_original_reference;
SimS00MapTableStatus sim_s00_map_bind_dos_layout(const SimS00MapDosLayout *layout);
void sim_s00_map_unbind_dos_layout(void);

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
 * Source colors are 0..24, plus FF for 640-table consumers with an explicitly
 * bound DOS layout. FF's wrapped-AL lookup crosses into relocated DispatchS00
 * data. Other unsupported colors and 320 FF fail before any destination write.
 * Destinations are plane-major DOS planar buffers. */
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
 * their table from the active application's gfx_screen_width_pixels mode. */
void gfx_planar_map128_pack2(char *source, char *destination, int16_t source_width, int16_t count);
void gfx_planar_map64_pack2(char *source, char *destination, int16_t source_width, int16_t count);
void gfx_planar_map128_pack4(char *source, char *destination, int16_t source_width, int16_t count);
void gfx_planar_map64_pack4(char *source, char *destination, int16_t source_width, int16_t count);
void gfx_planar_map128_pack8(char *source, char *destination);
void gfx_planar_map64_pack8(char *source, char *destination);

/* Convert then send the result through the already-bound source g914C renderer
 * into the application's one SimGraphicsDriver framebuffer. */
SimS00MapTableStatus sim_s00_map_transform_draw(
    struct SimGraphicsDriver *graphics, SimS00MapTableTransform transform,
    int16_t x, int16_t y, const uint8_t *source, size_t source_size);

#ifdef __cplusplus
}
#endif
#endif
