#include "graphics_source_cursor_effects.h"

#include "canonical_graphics_data.h"
#include "graphics_cursor_hooks.h"
#include "graphics_tile_upload.h"
#include "m1b73_mouse_state.h"

static uint8_t *display_busy_byte(void)
{
    return (uint8_t *)&gfx_cursor_draw_lock;
}

static int cursor_intersects(int16_t left, int16_t top,
                             int16_t right, int16_t bottom)
{
    return top <= (int16_t)cursor_drawn_bottom && bottom >= (int16_t)cursor_drawn_top &&
           left <= (int16_t)cursor_drawn_right && right >= (int16_t)cursor_drawn_left;
}

int sim_graphics_source_cursor_effects_begin(int16_t left, int16_t top,
                                              int16_t right, int16_t bottom)
{
    uint8_t *display_busy = display_busy_byte();
    ++*display_busy;

    if (cursor_update_lock == 0 && cursor_intersects(left, top, right, bottom) &&
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

    if (cursor_update_lock == 0 &&
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

    if (cursor_update_lock == 0) {
        if (cursor_show_level != 0) {
            if (cursor_drawn_flag != 0)
                ok = sim_graphics_cursor_hooks_redraw_if_shown();
        } else if (g_4366 == 0) {
            ok = sim_graphics_cursor_hooks_update();
        }
    }

    --*display_busy;
    return ok;
}
