#include "game_view.h"

#include <limits.h>

static int16_t clamp_axis(int32_t origin, int16_t cells, int16_t limit)
{
    int32_t maximum = (int32_t)limit - cells;
    if (origin < 0) return 0;
    if (origin > maximum) return (int16_t)maximum;
    return (int16_t)origin;
}

static PortableRect intersect_clip(PortableRect a, PortableRect b)
{
    PortableRect result;
    result.left = a.left > b.left ? a.left : b.left;
    result.top = a.top > b.top ? a.top : b.top;
    result.right = a.right < b.right ? a.right : b.right;
    result.bottom = a.bottom < b.bottom ? a.bottom : b.bottom;
    if (result.right < result.left) result.right = result.left;
    if (result.bottom < result.top) result.bottom = result.top;
    return result;
}

PortableGameViewStatus portable_game_view_resolve(
    const PortableWindowRegistry *registry,
    const SimGameWorld *world,
    const PortableGameViewState *state,
    PortableGameView *view)
{
    const PortableWindowRegistrySlot *slot;
    const PortableWindowObject *object;
    PortableWindowRect rect;
    int32_t width, height, columns, rows;
    int16_t map_width;
    int32_t camera_x, camera_y;
    int16_t plane;

    if (registry == 0 || world == 0 || state == 0 || view == 0 ||
        !registry->initialized)
        return PORTABLE_GAME_VIEW_BAD_ARGUMENT;
    slot = &registry->slots[PORTABLE_GAME_VIEW_WINDOW_ID];
    if (!slot->loaded || !slot->recalculated ||
        slot->window.resource_id != PORTABLE_GAME_VIEW_WINDOW_ID ||
        slot->window.count <= PORTABLE_GAME_VIEW_OBJECT_INDEX)
        return PORTABLE_GAME_VIEW_WINDOW_NOT_READY;
    object = &slot->window.objects[PORTABLE_GAME_VIEW_OBJECT_INDEX];
    if (object->type != 1)
        return PORTABLE_GAME_VIEW_UNSUPPORTED_GEOMETRY;

    rect = object->rect;
    width = (int32_t)rect.right - rect.left;
    height = (int32_t)rect.bottom - rect.top;
    columns = width / PORTABLE_GAME_VIEW_CELL_SIZE;
    /* Source f_0250_0E15 deliberately includes the partial bottom row. */
    rows = height / PORTABLE_GAME_VIEW_CELL_SIZE + 1;
    if (width <= 0 || height < 0 || columns <= 0 || rows <= 0 ||
        columns > INT16_MAX || rows > INT16_MAX)
        return PORTABLE_GAME_VIEW_UNSUPPORTED_GEOMETRY;

    plane = world->selected_map_plane;
    if (plane < 0 || plane > 3 || state->pheromone_mode < -1 ||
        state->pheromone_mode > 4 ||
        (state->ega_profile != 0 && state->ega_profile != 8))
        return PORTABLE_GAME_VIEW_UNSUPPORTED_MAP_STATE;
    map_width = plane <= 1 ? SIM_WORLD_WIDTH : SIM_NEST_WIDTH;
    if (columns > map_width || rows > SIM_WORLD_HEIGHT)
        return PORTABLE_GAME_VIEW_UNSUPPORTED_GEOMETRY;

    /* SetDefaultWindows finishes with CenterEdit(MeLocX,MeLocY). That leaves
     * camera origin at player minus half the visible logical cell count. */
    camera_x = (int32_t)world->me_x - columns / 2;
    camera_y = (int32_t)world->me_y - rows / 2;
    camera_x = clamp_axis(camera_x, (int16_t)columns, map_width);
    camera_y = clamp_axis(camera_y, (int16_t)rows, SIM_WORLD_HEIGHT);

    view->viewport = rect;
    view->map.plane = plane;
    view->map.camera_x = (int16_t)camera_x;
    view->map.camera_y = (int16_t)camera_y;
    view->map.pheromone_mode = state->pheromone_mode;
    view->map.columns = (int16_t)columns;
    view->map.rows = (int16_t)rows;
    view->map.screen_left = rect.left;
    view->map.screen_top = rect.top;
    view->map.cell_step_x = PORTABLE_GAME_VIEW_CELL_SIZE;
    view->map.cell_step_y = PORTABLE_GAME_VIEW_CELL_SIZE;
    view->map.ega_profile = state->ega_profile;
    view->map.animation_base = state->animation_base;
    view->map.queen_frame = state->queen_frame;
    view->map.young_frame = state->young_frame;
    view->map.caste_frame = state->caste_frame;
    return PORTABLE_GAME_VIEW_OK;
}

PortableGameViewStatus portable_game_view_render(
    const SimGameWorld *world,
    const PortableGameView *view,
    const PortableTileSet *tileset,
    PortableFramebuffer *framebuffer,
    PortableGameViewRenderResult *result)
{
    PortableRect saved_clip;
    PortableRect viewport_clip;
    PortableGameViewRenderResult counts = {0, 0};
    int16_t row, column;
    if (world == 0 || view == 0 || tileset == 0 || framebuffer == 0 ||
        framebuffer->pixels == 0)
        return PORTABLE_GAME_VIEW_BAD_ARGUMENT;
    if (view->map.plane < 0 || view->map.plane > 3 ||
        view->map.columns <= 0 || view->map.rows <= 0 ||
        view->map.columns > (view->map.plane <= 1 ? SIM_WORLD_WIDTH : SIM_NEST_WIDTH) ||
        view->map.rows > SIM_WORLD_HEIGHT ||
        view->viewport.right <= view->viewport.left ||
        view->viewport.bottom < view->viewport.top)
        return PORTABLE_GAME_VIEW_UNSUPPORTED_GEOMETRY;
    saved_clip = framebuffer->clip;
    viewport_clip.left = view->viewport.left;
    viewport_clip.top = view->viewport.top;
    viewport_clip.right = view->viewport.right;
    viewport_clip.bottom = view->viewport.bottom;
    portable_framebuffer_set_clip(framebuffer,
                                  intersect_clip(saved_clip, viewport_clip));
    for (row = 0; row < view->map.rows; ++row) {
        for (column = 0; column < view->map.columns; ++column) {
            SimMapDrawCommand command;
            SimMapStatus status = sim_map_select_cell(world, &view->map,
                                                       column, row, &command);
            if (status != SIM_MAP_OK) {
                portable_framebuffer_set_clip(framebuffer, saved_clip);
                return PORTABLE_GAME_VIEW_UNSUPPORTED_MAP_STATE;
            }
            status = sim_map_render_cell(world, &view->map, column, row,
                                         tileset, framebuffer);
            if (status != SIM_MAP_OK) {
                portable_framebuffer_set_clip(framebuffer, saved_clip);
                return PORTABLE_GAME_VIEW_MAP_RENDER_FAILED;
            }
            ++counts.cells_drawn;
            if (command.life_present) ++counts.cells_with_life;
        }
    }
    portable_framebuffer_set_clip(framebuffer, saved_clip);
    if (result != 0) *result = counts;
    return PORTABLE_GAME_VIEW_OK;
}

const char *portable_game_view_status_string(PortableGameViewStatus status)
{
    switch (status) {
    case PORTABLE_GAME_VIEW_OK: return "ok";
    case PORTABLE_GAME_VIEW_BAD_ARGUMENT: return "bad argument";
    case PORTABLE_GAME_VIEW_WINDOW_NOT_READY:
        return "window 0 object 4 is not loaded and recalculated";
    case PORTABLE_GAME_VIEW_UNSUPPORTED_GEOMETRY:
        return "viewport geometry is unsupported";
    case PORTABLE_GAME_VIEW_UNSUPPORTED_MAP_STATE:
        return "map state is unsupported";
    case PORTABLE_GAME_VIEW_MAP_RENDER_FAILED:
        return "map tile or life resource is unsupported";
    }
    return "unknown game view error";
}
