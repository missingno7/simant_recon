#ifndef SIMANT_WHOLE_PROGRAM_PLATFORM_GRAPHICS_ENTRY_SOURCE_H
#define SIMANT_WHOLE_PROGRAM_PLATFORM_GRAPHICS_ENTRY_SOURCE_H

#include "portable/whole_program/platform/graphics.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef void (*SimGraphicsLogicOperationCallback)(int16_t mode);
typedef int (*SimGraphicsPaletteWholeCallback)(void *context,
                                               const uint8_t palette17[17]);
typedef int (*SimGraphicsPaletteRangeCallback)(void *context, uint16_t first,
                                               uint16_t count,
                                               const uint8_t *rgb6_triplets);

typedef struct SimGraphicsPaletteServices {
    void *context;
    SimGraphicsPaletteWholeCallback set_attribute_palette;
    SimGraphicsPaletteRangeCallback set_dac_range;
} SimGraphicsPaletteServices;

/* Cursor renderer logic slots from S00 DispatchS00. Their writes target the
 * source driver's one g_3DD2 word through its existing graphics owner. */
extern SimGraphicsFontCallback g_915C;
extern SimGraphicsFontCallback g_9160;
extern SimGraphicsFontCallback g_9164;
extern SimGraphicsFontCallback g_9168;
extern SimGraphicsLogicOperationCallback g_9184;

SimGraphicsStatus sim_graphics_source_entry_bind(SimGraphicsDriver *graphics);
void sim_graphics_source_entry_unbind(void);
SimGraphicsStatus sim_graphics_source_palette_bind(
    const SimGraphicsPaletteServices *services);
void sim_graphics_source_palette_unbind(void);

/* Source public m1B4E wrappers. Image pointers address source 4-byte
 * [width,height] headers followed by the native S00 source bitmap format. */
void f_1B4E_003B(int16_t x, int16_t y, char *image);
void f_1B4E_005E(int16_t x, int16_t y, char *image);
void f_1B4E_0110(int16_t x, int16_t y, int16_t character);
void f_1B4E_01A1(char *palette17, int16_t count);
void f_1B4E_01AE(char *rgb_palette, int16_t count);

#ifdef __cplusplus
}
#endif
#endif
