#include "window_source_globals.h"
#include "window_source_rects.h"

#include <stdlib.h>
#include <string.h>

char g_5A97;
int16_t win_numOfWindows;
int16_t win_numOfColors;
int16_t win_numOfGroups;
SimWindowSourceDrawHook win_drawHooks[SIM_WINDOW_SOURCE_SLOT_COUNT];
struct Rect win_offsets[SIM_WINDOW_SOURCE_SLOT_COUNT];
int8_t (*win_colors)[SIM_WINDOW_SOURCE_COLOR_BYTES];

static size_t color_storage_bytes;

_Static_assert(sizeof(SimWindowSourceDrawHook) >= sizeof(void *),
               "draw hook table stores native callbacks");

int sim_window_source_reserve_colors(int16_t color_count)
{
    size_t count;
    size_t bytes;
    int8_t (*replacement)[SIM_WINDOW_SOURCE_COLOR_BYTES];

    if (color_count < 0) return 0;
    count = (size_t)(uint16_t)color_count;
    bytes = count * SIM_WINDOW_SOURCE_COLOR_BYTES;
    /* Keep a non-null destination for the source zero-byte memcpy case. */
    replacement = (int8_t (*)[SIM_WINDOW_SOURCE_COLOR_BYTES])
        malloc(bytes == 0 ? SIM_WINDOW_SOURCE_COLOR_BYTES : bytes);
    if (replacement == NULL) return 0;
    free(win_colors);
    win_colors = replacement;
    color_storage_bytes = bytes;
    return 1;
}

size_t sim_window_source_colors_size(void)
{
    return color_storage_bytes;
}

void sim_window_source_release_colors(void)
{
    free(win_colors);
    win_colors = NULL;
    color_storage_bytes = 0;
}

void sim_window_source_set_profile(char profile)
{
    g_5A97 = profile;
}

void sim_window_source_clear_draw_hooks(SimWindowSourceDrawHook *hooks,
                                       size_t count)
{
    if (hooks != NULL) memset(hooks, 0, count * sizeof(*hooks));
}
