#include "graphics_source_clip.h"

/* This is observed raw resident DGROUP state, not a claim that these are
 * initialized screen bounds. gfx_select_driver_resources is the source writer for right/bottom. */
extern struct Rect gfx_screen_clip_list[2] ;
extern struct Rect *clip_active_list_offset;
extern int16_t gfx_clip_left_pixels;
extern int16_t gfx_clip_right_pixels;

static SimGraphicsDriver *s_clip_graphics;

SimGraphicsStatus sim_graphics_source_clip_bind(SimGraphicsDriver *graphics)
{
    if (graphics == NULL || graphics->pixel_storage == NULL)
        return SIM_GRAPHICS_INVALID_ARGUMENT;
    s_clip_graphics = graphics;
    return SIM_GRAPHICS_OK;
}

void sim_graphics_source_clip_unbind(void)
{
    s_clip_graphics = NULL;
}

SimGraphicsDriver *sim_graphics_source_clip_owner(void)
{
    return s_clip_graphics;
}

int sim_graphics_source_clip_active(void)
{
    return clip_active_list_offset != NULL;
}

struct Rect *const *sim_graphics_source_clip_slot(void)
{
    return &clip_active_list_offset;
}
