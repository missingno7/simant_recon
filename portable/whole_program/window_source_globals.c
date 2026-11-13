#include "window_source_globals.h"
#include "window_source_rects.h"

#include <string.h>

extern char gfx_display_mode;
extern int16_t win_numOfWindows;
extern int16_t win_numOfColors;
extern int16_t win_numOfGroups;
extern SimWindowSourceDrawHook win_drawHooks[SIM_WINDOW_SOURCE_SLOT_COUNT];
extern struct Rect win_offsets[SIM_WINDOW_SOURCE_SLOT_COUNT];
_Static_assert(sizeof(SimWindowSourceDrawHook) >= sizeof(void *),
               "draw hook table stores native callbacks");

void sim_window_source_set_profile(char profile)
{
    gfx_display_mode = profile;
}

void sim_window_source_clear_draw_hooks(SimWindowSourceDrawHook *hooks,
                                       size_t count)
{
    if (hooks != NULL) memset(hooks, 0, count * sizeof(*hooks));
}
