#include "font_pointer_state_v1.h"

#include "portable/whole_program/platform/handles.h"

#include <stddef.h>

/* Source ASM DATA writes four zero bytes at each adjacent font pointer slot.
 * Native pointers have host width; only their null initial logical value is
 * preserved here. The generated S20 source owns later assignments. */
extern char *gfx_secondary_font ;
extern char *gfx_primary_font_offset ;

SimGraphicsStatus sim_source_font_bind_driver_view_v1(SimGraphicsDriver *graphics)
{
    size_t remaining;

    if (graphics == NULL || gfx_primary_font_offset == NULL)
        return SIM_GRAPHICS_FONT_UNBOUND;
    if (!sim_handles_global_measure_payload(gfx_primary_font_offset, &remaining) || remaining == 0)
        return SIM_GRAPHICS_FONT_UNBOUND;
    return sim_graphics_set_custom_font_source(
        graphics, (const uint8_t *)gfx_primary_font_offset, remaining);
}
