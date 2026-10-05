#ifndef SIMANT_WHOLE_PROGRAM_PLATFORM_GRAPHICS_BITMAP_SOURCE_H
#define SIMANT_WHOLE_PROGRAM_PLATFORM_GRAPHICS_BITMAP_SOURCE_H

#include "portable/whole_program/platform/graphics.h"

#ifdef __cplusplus
extern "C" {
#endif

/* Source driver table callbacks for S00 g914C/g9150. g914C dispatches through
 * the actual generated root f_1D8E_07F6 clipping body when g5AAC is non-null. */
SimGraphicsStatus sim_graphics_source_bitmap_bind(SimGraphicsDriver *graphics);
void sim_graphics_source_bitmap_unbind(void);

#ifdef __cplusplus
}
#endif
#endif
