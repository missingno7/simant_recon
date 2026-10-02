#include "map.h"
#include "../../render/tile_raster.h"

#include <limits.h>

static int valid_view(const SimMapView *view)
{
    return view != 0 && view->plane >= 0 && view->plane <= 3 &&
           view->pheromone_mode >= -1 && view->pheromone_mode <= 4 &&
           view->columns > 0 && view->rows > 0 &&
           view->camera_x >= 0 && view->camera_y >= 0;
}

static uint16_t wrap_u16(int32_t value)
{
    return (uint16_t)((uint32_t)value & 0xffffu);
}

static const uint8_t *selected_pheromone(const SimGameWorld *world, int mode)
{
    switch (mode) {
    case 0: return &world->pheromone_a[0][0];
    case 1: return &world->pheromone_b_nest[0][0];
    case 2: return &world->pheromone_b_trail[0][0];
    case 3: return &world->pheromone_r_nest[0][0];
    case 4: return &world->pheromone_r_trail[0][0];
    default: return 0;
    }
}

static uint16_t surface_life_frame(const SimMapView *view, uint8_t life)
{
    if (life == 0xff) {
        int32_t frame = view->animation_base + view->caste_frame + 0x380;
        frame += view->caste_frame < 8 ? view->young_frame : view->queen_frame;
        return wrap_u16(frame);
    }
    if (life == 0xfe)
        return wrap_u16((int32_t)view->animation_base + view->queen_frame +
                        view->caste_frame + 0x388);
    return wrap_u16((int32_t)life + 0x100);
}

static uint16_t nest_life_frame(const SimMapView *view, uint8_t life)
{
    if (life == 0xfe)
        return wrap_u16((int32_t)view->animation_base + view->queen_frame +
                        view->caste_frame + 0x308);
    if (life == 0xff) {
        int32_t frame = view->animation_base + view->caste_frame + 0x300;
        frame += view->caste_frame < 8 ? view->young_frame : view->queen_frame;
        return wrap_u16(frame);
    }
    return wrap_u16((int32_t)life + 0x200);
}

SimMapStatus sim_map_select_cell(const SimGameWorld *world,
                                 const SimMapView *view,
                                 int16_t column, int16_t row,
                                 SimMapDrawCommand *command)
{
    int32_t mx, my, screen_x, screen_y;
    uint8_t tile, life, has_pheromone = 0;
    const uint8_t *pheromone;
    if (world == 0 || command == 0)
        return SIM_MAP_INVALID_ARGUMENT;
    if (!valid_view(view) || column < 0 || row < 0 ||
        column >= view->columns || row >= view->rows)
        return SIM_MAP_INVALID_VIEW;

    mx = (int32_t)view->camera_x + column;
    my = (int32_t)view->camera_y + row;
    /* Source f_0250_1018 performs one 64-row camera wrap, shifting x by 64. */
    if (my > 0x3f) {
        mx += 0x40;
        my &= 0x3f;
    }
    if (view->plane <= 1) {
        mx &= 0x7f;
        if (view->pheromone_mode >= 0) {
            pheromone = selected_pheromone(world, view->pheromone_mode);
            tile = pheromone[(mx >> 1) * SIM_PHEROMONE_HEIGHT + (my >> 1)];
            if (tile > 0x10) {
                tile = (uint8_t)(((tile >> 4) & 0x1f) - 0x10);
                has_pheromone = 1;
            } else {
                tile = 0;
            }
        } else {
            tile = 0;
        }
        if (tile == 0) {
            tile = world->tiles.surface[mx][my];
            has_pheromone = 0;
        }
        life = world->life_a[mx][my];
    } else {
        mx &= 0x3f;
        if (view->plane == 2) {
            tile = (uint8_t)(world->tiles.nest_b[mx][my] - 0x70);
            life = world->life_b[mx][my];
        } else {
            tile = (uint8_t)(world->tiles.nest_r[mx][my] - 0x70);
            life = world->life_r[mx][my];
        }
    }

    screen_x = (int32_t)view->screen_left + (int32_t)view->cell_step_x * column;
    screen_y = (int32_t)view->screen_top + (int32_t)view->cell_step_y * row;
    if (screen_x < INT16_MIN || screen_x > INT16_MAX ||
        screen_y < INT16_MIN || screen_y > INT16_MAX)
        return SIM_MAP_INVALID_VIEW;

    command->screen_x = (int16_t)screen_x;
    command->screen_y = (int16_t)screen_y;
    command->map_x = (int16_t)mx;
    command->map_y = (int16_t)my;
    command->plane = (uint8_t)view->plane;
    command->ground_tile = tile;
    command->life_present = life != 0;
    command->life_overlay = life != 0;
    command->life_frame = life == 0 ? 0 :
        (view->plane <= 1 ? surface_life_frame(view, life) : nest_life_frame(view, life));
    if (command->life_frame >= 0x380)
        command->life_resource_frame = (uint16_t)(command->life_frame - 0x280);
    else if (command->life_frame >= 0x300)
        command->life_resource_frame = (uint16_t)(command->life_frame - 0x200);
    else if (command->life_frame >= 0x200)
        command->life_resource_frame = (uint16_t)(command->life_frame - 0x200);
    else if (command->life_frame >= 0x100)
        command->life_resource_frame = (uint16_t)(command->life_frame - 0x100);
    else
        command->life_resource_frame = life == 0 ? 0 : UINT16_MAX;
    command->resource_family = view->plane <= 1 ? SIM_MAP_RESOURCE_SURFACE : SIM_MAP_RESOURCE_NEST;
    command->pheromone_tile = has_pheromone;
    return SIM_MAP_OK;
}

static const PortableTileResource *life_resource_group(const PortableTileSet *tileset,
                                                        int plane,
                                                        unsigned chunk)
{
    if (plane <= 1)
        return &tileset->ems_surface[chunk];
    return &tileset->ems_nest[chunk];
}

SimMapStatus sim_map_render_cell(const SimGameWorld *world,
                                 const SimMapView *view,
                                 int16_t column, int16_t row,
                                 const PortableTileSet *tileset,
                                 PortableFramebuffer *framebuffer)
{
    SimMapDrawCommand command;
    uint8_t pixels[PORTABLE_EGA_TILE_PIXELS];
    const PortableTileResource *resource;
    const uint8_t *frames;
    size_t frames_size;
    unsigned chunk, frame_in_chunk;
    PortableRenderStatus render_status;

    if (tileset == 0 || framebuffer == 0 || framebuffer->pixels == 0)
        return SIM_MAP_INVALID_ARGUMENT;
    if (sim_map_select_cell(world, view, column, row, &command) != SIM_MAP_OK)
        return SIM_MAP_INVALID_VIEW;
    if (view->ega_profile != 0 && view->ega_profile != 8)
        return SIM_MAP_UNSUPPORTED_VIEW;
    if (view->cell_step_x != 16 || view->cell_step_y != 16)
        return SIM_MAP_UNSUPPORTED_VIEW;
    if (tileset->ground_resource.record.data == 0 ||
        tileset->ground_resource.record.size < 0x8000u)
        return SIM_MAP_INVALID_TILESET;

    render_status = portable_ega_tile_decode(tileset->ground_resource.record.data,
                                              tileset->ground_resource.record.size,
                                              command.ground_tile, pixels);
    if (render_status != PORTABLE_RENDER_OK)
        return SIM_MAP_INVALID_TILESET;
    if (command.life_present) {
        if (command.life_resource_frame == UINT16_MAX)
            return SIM_MAP_INVALID_TILESET;
        chunk = command.life_resource_frame / 128u;
        frame_in_chunk = command.life_resource_frame % 128u;
        if (chunk >= 3u)
            return SIM_MAP_INVALID_TILESET;
        resource = life_resource_group(tileset, command.plane, chunk);
        frames = resource->record.data;
        frames_size = resource->record.size;
        if (frames == 0 || frames_size < 0x5000u)
            return SIM_MAP_INVALID_TILESET;
        render_status = portable_ega_life_composite(pixels, frames, frames_size,
                                                     (uint16_t)frame_in_chunk);
        if (render_status != PORTABLE_RENDER_OK)
            return SIM_MAP_INVALID_TILESET;
    }
    portable_blit_indexed(framebuffer, command.screen_x, command.screen_y, pixels,
                          sizeof pixels, PORTABLE_EGA_TILE_WIDTH,
                          PORTABLE_EGA_TILE_HEIGHT, PORTABLE_EGA_TILE_WIDTH, 0, 0);
    return SIM_MAP_OK;
}

SimMapStatus sim_map_compose(const SimGameWorld *world,
                             const SimMapView *view,
                             SimMapDrawCommand *commands,
                             size_t capacity,
                             size_t *command_count)
{
    size_t needed;
    int16_t row, column;

    if (command_count == 0)
        return SIM_MAP_INVALID_ARGUMENT;
    *command_count = 0;
    if (world == 0 || commands == 0)
        return SIM_MAP_INVALID_ARGUMENT;
    if (!valid_view(view))
        return SIM_MAP_INVALID_VIEW;
    needed = (size_t)view->columns * (size_t)view->rows;
    if (needed > capacity)
        return SIM_MAP_OUTPUT_TOO_SMALL;
    for (row = 0; row < view->rows; ++row) {
        for (column = 0; column < view->columns; ++column) {
            SimMapStatus status = sim_map_select_cell(world, view, column, row,
                                                      &commands[*command_count]);
            if (status != SIM_MAP_OK) {
                *command_count = 0;
                return status;
            }
            ++*command_count;
        }
    }
    return SIM_MAP_OK;
}
