#ifndef SIMANT_GRAPHICS_MISC_SOURCE_H
#define SIMANT_GRAPHICS_MISC_SOURCE_H
#include "graphics.h"

typedef void (*SimGraphicsScreenCopyCallback)(int16_t, int16_t, int16_t,
                                              int16_t, int16_t, int16_t);
typedef void (*SimGraphicsRetireDisplay)(void *context);
extern SimGraphicsLineCallback g_916C;
extern SimGraphicsPatternRectCallback g_9174;
extern SimGraphicsFontCallback g_9178;
extern SimGraphicsScreenCopyCallback g_9188;

/* Retirement replaces the original switch to BIOS text mode 3. */
SimGraphicsStatus sim_graphics_source_misc_bind(SimGraphicsDriver *graphics,
    SimGraphicsRetireDisplay retire_display, void *context);
void sim_graphics_source_misc_unbind(void);
SimGraphicsStatus sim_graphics_s00_masked_rect(SimGraphicsDriver *graphics,
    int16_t left, int16_t top, int16_t right, int16_t bottom, int16_t pattern);
SimGraphicsStatus sim_graphics_s00_screen_copy(SimGraphicsDriver *graphics,
    int16_t left, int16_t top, int16_t right, int16_t bottom,
    int16_t destination_x, int16_t destination_y);
#endif
