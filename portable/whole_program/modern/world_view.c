#include "world_view.h"
#include "portable/whole_program/platform/graphics_tile_upload.h"

#include <string.h>

typedef char **Handle;
typedef struct { int16_t x, y; } ModernPoint;

/* Canonical owners (root m0250, m015B, m00F8, S12 m384C). */
extern int16_t MapPlane;
extern int16_t TERRAINset;
extern int16_t g_19BE, g_19C0;
extern ModernPoint MapPnt;              /* MapPnt */
extern int16_t fd_50F6_10E0, fd_50F6_10DE;    /* editWidth, editHeight */
extern ModernRect editTileRect;               /* editTileRect */
extern uint8_t edit_current_terrain_tile;                        /* edit-draw scratch: ground tile */
extern uint16_t edit_current_life_tile;                       /* edit-draw scratch: life code */
extern Handle edit_life_tiles_handle, edit_life_alt_tiles_handle;     /* life sprite banks: objects 13, 14 */
extern int16_t fd_50F6_37D2, fd_50F6_37D4;    /* spider cells, 500 = none */
extern char *g_19C6;                          /* edit view status message */
extern ModernRect map_viewport_rect;               /* mapTileRect */
extern int16_t mapXsize, mapYsize;    /* mapXsize, mapYsize */
extern int16_t map_side_margin_pixels;                  /* just */
extern int16_t multiplier;                  /* multiplier */
extern void DoCalcTile(int16_t x, int16_t y);

void modern_world_view(ModernWorldView *view)
{
    view->plane = MapPlane;
    view->columns = MapPlane < 2 ? 128 : 64;
    view->rows = 64;
    view->tile_width = g_19BE;
    view->tile_height = g_19C0;
    view->terrain_set = TERRAINset;
    view->origin_x = MapPnt.x;
    view->origin_y = MapPnt.y;
    view->view_columns = fd_50F6_10E0;
    view->view_rows = fd_50F6_10DE;
    view->view_rect = editTileRect;
}

/* DoCalcTile reads the plane's map, life and scent arrays and writes only
 * the edit-draw scratch pair edit_current_terrain_tile/edit_current_life_tile (m0250.c:891-992). Restoring the
 * pair makes the call read-only, also when a presentation runs between the
 * canonical decode and its compositor call. */
void modern_world_cell(int x, int y, ModernCell *cell)
{
    uint8_t ground = edit_current_terrain_tile;
    uint16_t life = edit_current_life_tile;
    DoCalcTile((int16_t)(x - MapPnt.x), (int16_t)(y - MapPnt.y));
    cell->ground = edit_current_terrain_tile;
    cell->life = edit_current_life_tile;
    edit_current_terrain_tile = ground;
    edit_current_life_tile = life;
}

/* edit_draw_life_and_ground_tile's interpretation of a life code: sprite bank, record index
 * and recolouring mode (masks {0,3,1} by code>>7; 0xF0..0xFF use mode 0). */
static const uint8_t *life_record(unsigned code, int16_t *mask_mode)
{
    static const int16_t masks[3] = { 0, 3, 1 };
    Handle bank;
    if (code >= 0x380) { code -= 0x280; bank = edit_life_alt_tiles_handle; }
    else if (code >= 0x200) { code -= 0x200; bank = edit_life_tiles_handle; }
    else { code -= 0x100; bank = edit_life_alt_tiles_handle; }
    if (bank == NULL || *bank == NULL || (code >> 7) > 2) return NULL;
    *mask_mode = code >= 0xf0 && code <= 0xff ? masks[0] : masks[code >> 7];
    return (const uint8_t *)*bank + (code & 0x7fu) * 0xc0u;
}

uint32_t modern_world_cell_key(const ModernCell *cell)
{
    int16_t mode;
    uint32_t loaded = cell->life && life_record(cell->life, &mode) != NULL;
    return (uint32_t)cell->ground | (uint32_t)cell->life << 8 | loaded << 24;
}

int modern_world_cell_pixels(const ModernCell *cell, uint8_t pixels[256])
{
    uint8_t ground[128], composed[128];
    const uint8_t *bits = ground, *record;
    int16_t mode = 0;
    unsigned row, x;
    if (!sim_graphics_tile_record(cell->ground, ground)) return 0;
    if (cell->life && (record = life_record(cell->life, &mode)) != NULL) {
        /* EGA/VGA (gfx_display_mode 0 and 8) composite with gfx_planar_compose_life_hires. */
        sim_graphics_tile_compose(ground, record, mode, SIM_GRAPHICS_TILE_COMPOSE_303F, composed);
        bits = composed;
    }
    /* Row-interleaved planar: per row, plane p's 16 pixels at bytes 2p, 2p+1. */
    for (row = 0; row < 16u; ++row)
        for (x = 0; x < 16u; ++x) {
            unsigned byte = x >> 3, bit = 7u - (x & 7u), plane, index = 0;
            for (plane = 0; plane < 4u; ++plane)
                index |= (unsigned)((bits[row * 8u + plane * 2u + byte] >> bit) & 1u) << plane;
            pixels[row * 16u + x] = (uint8_t)index;
        }
    return 1;
}

const char *modern_world_status_message(void)
{
    return g_19C6;
}

int modern_world_spider_cells(int *left, int *top)
{
    if (fd_50F6_37D2 == 500 || MapPlane != 1) return 0;
    *left = fd_50F6_37D2;
    *top = fd_50F6_37D4;
    return 1;
}

void modern_overview_view(ModernOverviewView *view)
{
    view->tiles = map_viewport_rect;
    view->cell_width = mapXsize;
    view->cell_height = mapYsize;
    view->pad = map_side_margin_pixels;
    view->multiplier = multiplier;
}
