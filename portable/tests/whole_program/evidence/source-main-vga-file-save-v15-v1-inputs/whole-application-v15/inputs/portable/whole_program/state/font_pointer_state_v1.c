#include "font_pointer_state_v1.h"

#include "portable/whole_program/platform/handles.h"

#include <stddef.h>

/* Source ASM DATA writes four zero bytes at each adjacent font pointer slot.
 * Native pointers have host width; only their null initial logical value is
 * preserved here. The generated S20 source owns later assignments. */
char *g_3DA4 = NULL;
char *g_3DA8 = NULL;

SimGraphicsStatus sim_source_font_bind_driver_view_v1(SimGraphicsDriver *graphics)
{
    size_t remaining;

    if (graphics == NULL || g_3DA8 == NULL)
        return SIM_GRAPHICS_FONT_UNBOUND;
    if (!sim_handles_global_measure_payload(g_3DA8, &remaining) || remaining == 0)
        return SIM_GRAPHICS_FONT_UNBOUND;
    return sim_graphics_set_custom_font_source(
        graphics, (const uint8_t *)g_3DA8, remaining);
}
