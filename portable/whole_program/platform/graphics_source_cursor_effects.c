#include "graphics_source_cursor_effects.h"

#include "canonical_graphics_data.h"
#include "graphics_cursor_hooks.h"
#include "graphics_tile_upload.h"
#include "m1b73_mouse_state.h"

static uint8_t *display_busy_byte(void)
{
    return (uint8_t *)&g_3DD4;
}

static int cursor_intersects(int16_t left, int16_t top,
                             int16_t right, int16_t bottom)
{
    return top <= (int16_t)g_4344 && bottom >= (int16_t)g_4342 &&
           left <= (int16_t)g_4346 && right >= (int16_t)g_4340;
}

int sim_graphics_source_cursor_effects_begin(int16_t left, int16_t top,
                                              int16_t right, int16_t bottom)
{
    uint8_t *display_busy = display_busy_byte();
    ++*display_busy;

    if (g_4333 == 0 && cursor_intersects(left, top, right, bottom) &&
        !sim_graphics_cursor_hooks_hide()) {
        --*display_busy;
        return 0;
    }
    return 1;
}

int sim_graphics_source_cursor_effects_begin_pair(
    int16_t left, int16_t top, int16_t right, int16_t bottom,
    int16_t second_left, int16_t second_top,
    int16_t second_right, int16_t second_bottom)
{
    uint8_t *display_busy = display_busy_byte();
    ++*display_busy;

    if (g_4333 == 0 &&
        (cursor_intersects(left, top, right, bottom) ||
         cursor_intersects(second_left, second_top,
                           second_right, second_bottom)) &&
        !sim_graphics_cursor_hooks_hide()) {
        --*display_busy;
        return 0;
    }
    return 1;
}

int sim_graphics_source_cursor_effects_end(void)
{
    uint8_t *display_busy = display_busy_byte();
    int ok = 1;

    if (g_4333 == 0) {
        if (g_4365 != 0) {
            if (g_4331 != 0)
                ok = sim_graphics_cursor_hooks_redraw_if_shown();
        } else if (g_4366 == 0) {
            ok = sim_graphics_cursor_hooks_update();
        }
    }

    --*display_busy;
    return ok;
}
