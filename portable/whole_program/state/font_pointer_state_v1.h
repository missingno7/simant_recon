#ifndef SIMANT_FONT_POINTER_STATE_V1_H
#define SIMANT_FONT_POINTER_STATE_V1_H

#include "portable/whole_program/platform/graphics.h"

#include <stdint.h>

/* Native pointer slots for the source's DGROUP gfx_secondary_font and gfx_primary_font_offset far
 * pointers. Their null startup values are initialized in root:m1B4E.asm;
 * S20's generated loader bodies replace them with resource payload views. */
extern char *gfx_secondary_font;
extern char *gfx_primary_font_offset;

/* Refresh the driver's borrowed custom-font view from the currently selected
 * source payload pointer. No copy, new ownership, or resource-size guess. */
SimGraphicsStatus sim_source_font_bind_driver_view_v1(SimGraphicsDriver *graphics);

#endif
