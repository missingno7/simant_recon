#include "world_view.h"
#include "portable/whole_program/platform/graphics_tile_upload.h"

#include <string.h>

typedef char **Handle;
typedef struct { int16_t x, y; } ModernPoint;

/* Canonical owners (root m0250, m015B, m00F8, S12 m384C). */
extern int16_t MapPlane;
extern int16_t TERRAINset;
extern int16_t g_19BE, g_19C0;
extern ModernPoint fd_50F6_0508;              /* MapPnt */
extern int16_t fd_50F6_10E0, fd_50F6_10DE;    /* editWidth, editHeight */
extern ModernRect fd_50F6_110C;               /* editTileRect */
extern uint8_t g_94E4;                        /* edit-draw scratch: ground tile */
extern uint16_t g_9126;                       /* edit-draw scratch: life code */
extern Handle fd_50F6_10E6, fd_50F6_10EA;     /* life sprite banks: objects 13, 14 */
extern int16_t fd_50F6_37D2, fd_50F6_37D4;    /* spider cells, 500 = none */
extern char *g_19C6;                          /* edit view status message */
extern ModernRect fd_50F6_10D2;               /* mapTileRect */
extern int16_t fd_50F6_3856, fd_50F6_3858;    /* mapXsize, mapYsize */
extern int16_t fd_50F6_38C0;                  /* just */
extern int16_t fd_50F6_3854;                  /* multiplier */
extern void f_0250_1018(int16_t x, int16_t y);

void modern_world_view(ModernWorldView *view)
{
    view->plane = MapPlane;
    view->columns = MapPlane < 2 ? 128 : 64;
    view->rows = 64;
    view->tile_width = g_19BE;
    view->tile_height = g_19C0;
    view->terrain_set = TERRAINset;
    view->origin_x = fd_50F6_0508.x;
    view->origin_y = fd_50F6_0508.y;
    view->view_columns = fd_50F6_10E0;
    view->view_rows = fd_50F6_10DE;
    view->view_rect = fd_50F6_110C;
}

/* f_0250_1018 reads the plane's map, life and scent arrays and writes only
 * the edit-draw scratch pair g_94E4/g_9126 (m0250.c:891-992). Restoring the
 * pair makes the call read-only, also when a presentation runs between the
 * canonical decode and its compositor call. */
void modern_world_cell(int x, int y, ModernCell *cell)
{
    uint8_t ground = g_94E4;
    uint16_t life = g_9126;
    f_0250_1018((int16_t)(x - fd_50F6_0508.x), (int16_t)(y - fd_50F6_0508.y));
    cell->ground = g_94E4;
    cell->life = g_9126;
    g_94E4 = ground;
    g_9126 = life;
}

/* f_0250_0721's interpretation of a life code: sprite bank, record index
 * and recolouring mode (masks {0,3,1} by code>>7; 0xF0..0xFF use mode 0). */
static const uint8_t *life_record(unsigned code, int16_t *mask_mode)
{
    static const int16_t masks[3] = { 0, 3, 1 };
    Handle bank;
    if (code >= 0x380) { code -= 0x280; bank = fd_50F6_10EA; }
    else if (code >= 0x200) { code -= 0x200; bank = fd_50F6_10E6; }
    else { code -= 0x100; bank = fd_50F6_10EA; }
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
        /* EGA/VGA (g_5A97 0 and 8) composite with o00_31AD_303F. */
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
    view->tiles = fd_50F6_10D2;
    view->cell_width = fd_50F6_3856;
    view->cell_height = fd_50F6_3858;
    view->pad = fd_50F6_38C0;
    view->multiplier = fd_50F6_3854;
}
