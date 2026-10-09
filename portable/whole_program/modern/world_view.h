#ifndef SIMANT_MODERN_WORLD_VIEW_H
#define SIMANT_MODERN_WORLD_VIEW_H

#include <stdint.h>

/* Read-only semantic views of the world shown by the Game Window (logical
 * window 0, the DOS edit view) and of the overview that indicates it (map
 * window 0x0100). Every value is read from canonical state; nothing here
 * draws, allocates, scrolls or consumes the game's RNG. See
 * docs/modern-frontend.md for the dependency map these views follow.
 *
 * Names follow the Win16 reconstruction where the pairing is proven by the
 * shared formulas (MapPnt = fd_50F6_0508, editWidth/editHeight =
 * fd_50F6_10E0/10DE, editTileRect = fd_50F6_110C, mapTileRect = fd_50F6_10D2,
 * mapXsize/mapYsize = fd_50F6_3856/3858, just = fd_50F6_38C0). */

enum { MODERN_TILE_SIZE = 16 };

typedef struct ModernRect { int16_t left, top, right, bottom; } ModernRect;

typedef struct ModernWorldView {
    int plane;               /* MapPlane: 0 yard (the edit view shows the surface),
                                1 surface, 2 black nest, 3 red nest */
    int columns, rows;       /* world tiles: 128x64 for planes 0/1, else 64x64 (f_0250_0F2C) */
    int tile_width, tile_height;   /* g_19BE/g_19C0: 16 in the supported EGA/VGA modes */
    int terrain_set;         /* TERRAINset (OverlayTileSet) */
    /* The canonical edit view: the game's camera. */
    int origin_x, origin_y;  /* MapPnt, in tiles */
    int view_columns, view_rows;   /* editWidth/editHeight (rows include a partial row) */
    ModernRect view_rect;    /* editTileRect, object 4, logical screen pixels */
} ModernWorldView;

void modern_world_view(ModernWorldView *view);

/* Canonical cell codes, as f_0250_1018 computes them for the edit view:
 * ground tile (g_94E4) and life code (g_9126: 0 none, +0x100 surface,
 * +0x200 nest, 0x300/0x380 bases for the player's ant). */
typedef struct ModernCell { uint8_t ground; uint16_t life; } ModernCell;
/* World tile (x, y), 0 <= y < 64, on the current plane. */
void modern_world_cell(int x, int y, ModernCell *cell);
/* 16x16 palette indices, row-major. Returns 0 when the resident tile cache
 * is not bound yet. A life code whose sprite bank is not loaded draws its
 * ground only (non-EMS DOS keeps one of objects 13/14 resident). */
int modern_world_cell_pixels(const ModernCell *cell, uint8_t pixels[256]);
/* Stable key for the pixels of a cell (cell codes plus sprite-bank presence). */
uint32_t modern_world_cell_key(const ModernCell *cell);

/* Edit-view cells the spider composite covered on the last canonical draw
 * (PreDrawSpider: 7x7 cells at fd_50F6_37D2/37D4, view-relative). */
int modern_world_spider_cells(int *left, int *top);

/* The edit view's status message (g_19C6, e.g. "Game Paused"), drawn by
 * f_0250_13A6 centred in editTileRect at top+4 until it expires; NULL when
 * none. It belongs to the view, not to the world. */
const char *modern_world_status_message(void);

/* The overview's transform (S12 DrawMapCursor): world tile (x, y) maps to
 * logical (left + pad + x*cell_width, top + y*cell_height). */
typedef struct ModernOverviewView {
    ModernRect tiles;        /* mapTileRect */
    int cell_width, cell_height;   /* mapXsize, mapYsize */
    int pad;                 /* just: nest planes sit 32 tiles in */
    int multiplier;          /* row width in tiles: 128 surface, 64 nests */
} ModernOverviewView;
void modern_overview_view(ModernOverviewView *view);

#endif
