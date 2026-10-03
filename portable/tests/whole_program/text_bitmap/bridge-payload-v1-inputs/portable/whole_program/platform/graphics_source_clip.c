#include "graphics_source_clip.h"

/* This is observed raw resident DGROUP state, not a claim that these are
 * initialized screen bounds. f_205F_0004 is the source writer for right/bottom. */
struct Rect sim_source_screen_clip_list[2] = {
    { 0, 0, 349, 639 },
    { INT16_MIN, INT16_MIN, INT16_MIN, INT16_MIN }
};
struct Rect *g_5AAC;
int16_t fd_55B3_3DE6;
int16_t fd_55B3_3DE8;

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
    return g_5AAC != NULL;
}

struct Rect *const *sim_graphics_source_clip_slot(void)
{
    return &g_5AAC;
}
