#include "process_edit_event_dto.h"

#include <string.h>

int sim_maparea_release_to_process_edit(const SimDosEvent8 *input,
                                        const SimEditClickGeometry *g,
                                        SimDosEvent8 *output)
{
    int32_t map_x, map_y;
    if (input == 0 || g == 0 || output == 0 || g->map_step_x == 0 ||
        g->map_step_y == 0 || g->edit_step_x == 0 || g->edit_step_y == 0)
        return 0;
    if (!(g->map_rect.right > input->h && g->map_rect.left <= input->h &&
          g->map_rect.top <= input->v && input->v < g->map_rect.bottom) ||
        (input->modifiers & 0x4800) == 0)
        return 0;

    *output = *input;
    map_x = ((int32_t)input->h - g->map_rect.left) / g->map_step_x - g->view_x;
    map_y = ((int32_t)input->v - g->map_rect.top) / g->map_step_y - g->view_y;
    output->h = (int16_t)(map_x * g->edit_step_x + g->edit_rect.left);
    output->v = (int16_t)(map_y * g->edit_step_y + g->edit_rect.top);
    output->modifiers = (input->modifiers & 0x4000) ? 0x2000 : 0x0200;
    return 1;
}
