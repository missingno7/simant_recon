/*
 * Draws and updates the detailed ant view, including tiles, the spider, speech balloons and
 * graphs. It also contains tile loading, EMS tile cache setup and editor event handling.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS: resident code; segment 0250; partial original translation unit.
 * Windows: mixed (ANTEDIT, _TEXT), from recorded function pairs.
 * Functions not yet exact: DoCalcTile, DrawBalloons.
 * Steered functions: edit_redraw_changed_tile.
 */

struct Event {
    int what;
    int message;
    int x4;
    int modifiers;
    int h;
    int v;
    int code;
    int xE;
};

typedef char far * far *Handle;

extern int far TileIsVisible(int plane, int x, int y);
extern int far fd_50F6_10E0;
extern int far fd_50F6_10DE;
extern int far edit_cached_life_tiles[30][40];

int g_19BE = 16;
int g_19C0 = 16;
int g_19C2 = 13;
int g_19C4 = 7;
char far *g_19C6 = 0;
long g_19CA = 0;
int g_19CE = 1;
int g_19D0 = 0;
int g_19D2[8] = { 0, 0, 1, 1, 2, 2, 3, 3 };
int g_19E2[8] = { 4, 0, 5, 1, 6, 2, 7, 3 };

void far ZapEuMapAt(int plane, int x, int y)
{
    int h;
    int v;

    if (TileIsVisible(plane, x, y) == 1) {
        h = x;
        if (h >= 0 && h < fd_50F6_10E0) {
            v = y;
            if (v >= 0 && v < fd_50F6_10DE)
                edit_cached_life_tiles[v][h] = -1;
        }
    }
}

void far InvalEuMap(int left, int top, int right, int bottom)
{
    int x;
    int i;
    int y;

    if (left < 0)
        left = 0;
    else if (right > 127)
        right = 127;
    if (top < 0)
        top = 0;
    else if (bottom > 63)
        bottom = 63;
    for (y = top; y <= bottom; y++) {
        i = y * 40 + left;
        for (x = left; x <= right; x++, i++)
            if (x >= 0 && x < fd_50F6_10E0 && y >= 0 && y < fd_50F6_10DE)
                edit_cached_life_tiles[0][i] = -1;
    }
}

extern void far ems_free_handle(int handle);

void far edit_free_tile_ems(void)
{
    if (g_19D0)
        ems_free_handle(g_19D0);
}

extern int far ems_initialize(void);
extern char far ems_version;
extern int far WinPrintf(char far *format, ...);
extern void far ems_query_page_counts(void);
extern int far ems_total_page_count;
extern int far ems_free_page_count;
extern void far ems_query_page_frame(void);
extern int far ems_allocate_pages(int pages);
extern void far ems_set_handle_name(int handle, char far *name);
extern int far atexit(void (far *func)(void));

/*C*/
int far edit_alloc_tile_ems(void)
{
    int ok;

    if (g_19D0 != 0)
        return 1;
    if (ems_initialize() && ems_version >= 0x40) {
        WinPrintf("\nEMS version: %x", ems_version);
        ems_query_page_counts();
        WinPrintf("\ntotal pages: %d", ems_total_page_count);
        WinPrintf("\nfree  pages: %d", ems_free_page_count);
        if (ems_free_page_count >= 8) {
            ems_query_page_frame();
            g_19D0 = ems_allocate_pages(8);
            ems_set_handle_name(g_19D0, "TILESXXX");
            atexit(edit_free_tile_ems);
            return 1;
        }
    }
    return 0;
}

extern Handle far edit_life_alt_tiles_handle;
extern void far db_ReleaseHandle(Handle handle);
extern Handle far edit_life_tiles_handle;

void far edit_release_life_tiles(void)
{
    if (edit_life_alt_tiles_handle) {
        db_ReleaseHandle(edit_life_alt_tiles_handle);
        edit_life_alt_tiles_handle = 0;
    }
    if (edit_life_tiles_handle) {
        db_ReleaseHandle(edit_life_tiles_handle);
        edit_life_tiles_handle = 0;
    }
}

static int g_1A2E = -1;

extern int far TERRAINset;
extern char near gfx_display_mode;
extern Handle far res_load_firm_object(int object, int kind);
extern Handle far edit_uploaded_tiles_handle;
extern void far gfx_planar_upload_tiles(char far *p, unsigned seg, int n);
extern void far gfx_planar_upload_plane(char far *p, unsigned seg, int page, unsigned n);
extern void far db_PurgeObject(int object, int kind);
extern Handle far edit_terrain_tiles_handle;
extern void far mem_Free(Handle h);
extern void far db_UnhookObject(int object, int kind);

void far edit_load_terrain_tiles(int set)
{
    int i;

    if (g_1A2E == set)
        return;
    g_1A2E = set;
    TERRAINset = set;
    if ((gfx_display_mode & 1) || gfx_display_mode == 2) {
        if (edit_terrain_tiles_handle)
            mem_Free(edit_terrain_tiles_handle);
        edit_terrain_tiles_handle = res_load_firm_object(10 - set, 9);
        db_UnhookObject(10 - set, 9);
    } else {
        if (g_19D0 == 0)
            edit_release_life_tiles();
        edit_uploaded_tiles_handle = res_load_firm_object(10 - set, 9);
        gfx_planar_upload_tiles(*edit_uploaded_tiles_handle, 0xa000, 0x100);
        for (i = 0; i < 4; i++)
            gfx_planar_upload_plane(*edit_uploaded_tiles_handle + (i << 13), 0xc000, i, 0x2000);
        db_PurgeObject(10 - set, 9);
    }
}

extern int far Barrier;

void far OverlayTileSet(int type, int id)
{
    if (type == 0) {
        if (id == 0x3e9) {
            edit_load_terrain_tiles(1);
            Barrier = 0x90;
        } else if (id == 0x3e8) {
            edit_load_terrain_tiles(0);
            Barrier = 0x50;
        }
    }
}

extern int far edit_tile_renderer_kind;
extern Handle far res_load_with_alloc_type(int object, int kind, int type);
extern long far mem_Size(Handle h);
extern int far mem_handle_above_ems_boundary(Handle h);
extern Handle far Ralloc(long size, int flags, char far *name);
extern char far * far mem_Lock(Handle h);
extern void far * far _fmemcpy(void far *dest, void far *src, unsigned n);
extern void far ems_save_handle_map(int handle);
extern void far ems_map_multiple_pages(int handle, int n, int far *map);
extern char far * far ems_page_frame_pointer;
extern void far ems_restore_handle_map(int handle);
extern Handle far mem_Unlock(Handle h);

void far LoadTiles(void)
{
    int i;
    unsigned n;
    Handle h;
    char far *p;

    edit_life_alt_tiles_handle = 0;
    edit_life_tiles_handle = 0;
    edit_terrain_tiles_handle = 0;
    edit_load_terrain_tiles(0);
    switch (gfx_display_mode) {
    case 0:
    case 8:
        edit_alloc_tile_ems();
    case 4:
        edit_tile_renderer_kind = 1;
        if (g_19D0) {
            for (i = 0; i < 6; i++) {
                edit_life_tiles_handle = res_load_with_alloc_type(i + 15, 9, 1);
                n = mem_Size(edit_life_tiles_handle);
                if (mem_handle_above_ems_boundary(edit_life_tiles_handle)) {
                    h = Ralloc((long)n, 9, "emstiles");
                    p = mem_Lock(h);
                    _fmemcpy(p, mem_Lock(edit_life_tiles_handle), n);
                } else {
                    h = 0;
                    p = mem_Lock(edit_life_tiles_handle);
                }
                ems_save_handle_map(g_19D0);
                ems_map_multiple_pages(g_19D0, 4, i < 3 ? g_19D2 : g_19E2);
                _fmemcpy(ems_page_frame_pointer + i % 3 * 0x5000, p, n);
                ems_restore_handle_map(g_19D0);
                mem_Unlock(edit_life_tiles_handle);
                if (h) {
                    mem_Unlock(h);
                    mem_Free(h);
                }
                db_PurgeObject(i + 15, 9);
            }
            edit_life_tiles_handle = 0;
        }
        break;
    case 2:
        g_19BE = g_19C0 = 12;
        edit_tile_renderer_kind = 2;
        break;
    case 3:
    case 5:
    case 7:
        edit_tile_renderer_kind = 3;
        break;
    }
}

extern void far * far _fmemset(void far *dest, int c, unsigned n);

void far edit_invalidate_life_cache(void)
{
    _fmemset(edit_cached_life_tiles, -1, 0x960);
}

extern int far MapPlane;

void far edit_map_tile_ems_for_plane(void)
{
    if (g_19D0) {
        ems_save_handle_map(g_19D0);
        if (MapPlane < 2)
            ems_map_multiple_pages(g_19D0, 4, g_19D2);
        else
            ems_map_multiple_pages(g_19D0, 4, g_19E2);
    }
}

void far edit_restore_tile_ems_map(void)
{
    if (g_19D0)
        ems_restore_handle_map(g_19D0);
}

void far edit_prepare_life_tiles(int which)
{
    if (g_19D0 == 0) {
        if (which == 1) {
            if (edit_life_alt_tiles_handle) {
                db_ReleaseHandle(edit_life_alt_tiles_handle);
                edit_life_alt_tiles_handle = 0;
            }
            if (edit_life_tiles_handle == 0)
                edit_life_tiles_handle = res_load_firm_object(13, 9);
        } else {
            if (edit_life_tiles_handle) {
                db_ReleaseHandle(edit_life_tiles_handle);
                edit_life_tiles_handle = 0;
            }
            if (edit_life_alt_tiles_handle == 0)
                edit_life_alt_tiles_handle = res_load_firm_object(14, 9);
        }
    } else
        edit_map_tile_ems_for_plane();
}

extern unsigned char near edit_current_terrain_tile;
extern void far Punt(char far *format, ...);
extern unsigned near edit_current_life_tile;
extern void far gfx_planar_draw_life_ems(int x, int y, int col, int row, char far *p);
extern void far gfx_planar_draw_life_320(int x, int y, int col, int row, char far *p, int mask);
extern void far gfx_planar_draw_life_hires(int x, int y, int col, int row, char far *p, int mask);
extern void far gfx_tandy_draw_life_tile(int x, int y, char far *tile, char far *life, int mask);
extern void far gfx_mono_draw_life_tile(int x, int y, char far *tile, char far *life, int n);

void far edit_draw_life_and_ground_tile(int x, int y)
{
    static int masks[3] = { 0, 3, 1 };
    int row;
    int col;
    int flip;
    int mask;
    char far *base;

    row = edit_current_terrain_tile >> 6;
    col = ((edit_current_terrain_tile & 0x3f) - 0x80) << 7;
    if (edit_current_terrain_tile >= 0x100)
        Punt("Tile >= 256 in PutLifeAndTile");
    if (edit_current_life_tile >= 0x380) {
        edit_current_life_tile -= 0x280;
        flip = 0;
    } else if (edit_current_life_tile >= 0x300) {
        edit_current_life_tile -= 0x200;
        flip = 1;
    } else if (edit_current_life_tile >= 0x200) {
        edit_current_life_tile -= 0x200;
        flip = 1;
    } else {
        edit_current_life_tile -= 0x100;
        flip = 0;
    }
    if (g_19D0 && edit_tile_renderer_kind == 1) {
        gfx_planar_draw_life_ems(x & ~0xf, y, col, row, ems_page_frame_pointer + edit_current_life_tile * 0xa0);
        return;
    }
    base = *(flip == 1 ? edit_life_tiles_handle : edit_life_alt_tiles_handle);
    if (edit_current_life_tile >= 0xf0 && edit_current_life_tile <= 0xff)
        mask = masks[0];
    else
        mask = masks[edit_current_life_tile >> 7];
    if (edit_tile_renderer_kind == 1) {
        if (gfx_display_mode == 4)
            gfx_planar_draw_life_320(x & ~0xf, y, col, row, base + (edit_current_life_tile & 0x7f) * 0xc0, mask);
        else
            gfx_planar_draw_life_hires(x & ~0xf, y, col, row, base + (edit_current_life_tile & 0x7f) * 0xc0, mask);
    } else if (edit_tile_renderer_kind == 2)
        gfx_tandy_draw_life_tile(x & ~1, y, *edit_terrain_tiles_handle + edit_current_terrain_tile * 0x48, base + (edit_current_life_tile & 0x7f) * 0x48, mask);
    else if (edit_tile_renderer_kind == 3)
        gfx_mono_draw_life_tile(x & ~7, y, *edit_terrain_tiles_handle + (edit_current_terrain_tile << 5), base + (edit_current_life_tile << 5), 0x3000 - ((edit_current_life_tile >> 7) << 12));
}

extern void far gfx_planar_compose_life_ems(int col, int row, char far *p);
extern void far gfx_planar_compose_life_320(int col, int row, char far *p, int mask);
extern void far gfx_planar_compose_life_hires(int col, int row, char far *p, int mask);
extern void far gfx_tandy_compose_life_tile(char far *tile, char far *life, int mask);
extern void far gfx_mono_compose_life_tile(char far *tile, char far *life, int n);

void far edit_compose_life_tile(void)
{
    static int masks[3] = { 0, 3, 1 };
    int row;
    int col;
    int flip;
    int mask;
    char far *base;

    row = edit_current_terrain_tile >> 6;
    col = ((edit_current_terrain_tile & 0x3f) - 0x80) << 7;
    if (edit_current_terrain_tile >= 0x100)
        Punt("Tile >= 256 in PutLifeAndTile");
    if (edit_current_life_tile >= 0x380) {
        edit_current_life_tile -= 0x280;
        flip = 0;
    } else if (edit_current_life_tile >= 0x300) {
        edit_current_life_tile -= 0x200;
        flip = 1;
    } else if (edit_current_life_tile >= 0x200) {
        edit_current_life_tile -= 0x200;
        flip = 1;
    } else {
        edit_current_life_tile -= 0x100;
        flip = 0;
    }
    if (g_19D0 && edit_tile_renderer_kind == 1) {
        gfx_planar_compose_life_ems(col, row, ems_page_frame_pointer + edit_current_life_tile * 0xa0);
        return;
    }
    base = *(flip == 1 ? edit_life_tiles_handle : edit_life_alt_tiles_handle);
    if (edit_current_life_tile >= 0xf0 && edit_current_life_tile <= 0xff)
        mask = masks[0];
    else
        mask = masks[edit_current_life_tile >> 7];
    if (edit_tile_renderer_kind == 1) {
        if (gfx_display_mode == 4)
            gfx_planar_compose_life_320(col, row, base + (edit_current_life_tile & 0x7f) * 0xc0, mask);
        else
            gfx_planar_compose_life_hires(col, row, base + (edit_current_life_tile & 0x7f) * 0xc0, mask);
    } else if (edit_tile_renderer_kind == 2)
        gfx_tandy_compose_life_tile(*edit_terrain_tiles_handle + edit_current_terrain_tile * 0x48, base + (edit_current_life_tile & 0x7f) * 0x48, mask);
    else if (edit_tile_renderer_kind == 3)
        gfx_mono_compose_life_tile(*edit_terrain_tiles_handle + (edit_current_terrain_tile << 5), base + (edit_current_life_tile << 5), 0x3000 - ((edit_current_life_tile >> 7) << 12));
}

extern void (far * near g_917C)(int x, int y, int offset);
extern void (far * near gfx_put_picture_hook)(int x, int y, char far *p, int w, int h);

void far edit_draw_ground_tile(int x, int y)
{
    if (edit_current_terrain_tile >= 0x100)
        Punt("PutTile grndTile > 0x100");
    switch (edit_tile_renderer_kind) {
    case 1:
        (*g_917C)(x, y, (edit_current_terrain_tile - 0x300) << 5);
        break;
    case 2:
        (*gfx_put_picture_hook)(x & ~1, y, *edit_terrain_tiles_handle + edit_current_terrain_tile * 0x48, 12, 12);
        break;
    case 3:
        (*gfx_put_picture_hook)(x & ~0xf, y, *edit_terrain_tiles_handle + (edit_current_terrain_tile << 5), 16, 16);
        break;
    }
}

extern void far gfx_planar_read_tile_plane(int row, int col);
extern char near gfx_row_scratch[];

void far edit_copy_ground_tile(void)
{
    switch (edit_tile_renderer_kind) {
    case 1:
        gfx_planar_read_tile_plane(edit_current_terrain_tile >> 6, ((edit_current_terrain_tile & 0x3f) - 0x80) << 7);
        break;
    case 2:
        _fmemcpy(gfx_row_scratch, *edit_terrain_tiles_handle + edit_current_terrain_tile * 0x48, 0x48);
        break;
    case 3:
        _fmemcpy(gfx_row_scratch, *edit_terrain_tiles_handle + (edit_current_terrain_tile << 5), 0x20);
        break;
    }
}

extern void far clip_SetWin(int win);
extern void far processEdit(struct Event far *event);
extern void far OpenMiniMapWin(void);
extern void far DoWinHelp(int mode);
extern void far EditToolsMenu(void);
extern void far SetMapPlane(int plane);
extern void far GotoMyAnt(void);
extern void far GotoSpider(void);
extern void far GotoBQueen(void);
extern void far GotoRQueen(void);
extern int far GamePaused;
extern void far SetPause(int pause);
extern void far EditScentMenu(void);
extern void far DoHealthSetY(struct Event far *event);
extern void far DoWarnSetB(struct Event far *event);
extern void far clip_Off(void);

void far ProcEditEvent(struct Event far *event)
{
    clip_SetWin(0);
    switch (event->code) {
    case 4:
    case 21:
        processEdit(event);
        break;
    case 5:
        OpenMiniMapWin();
        break;
    case 6:
        DoWinHelp(2);
        break;
    case 7:
        EditToolsMenu();
        break;
    case 8:
        SetMapPlane(1);
        break;
    case 9:
        SetMapPlane(2);
        break;
    case 10:
        SetMapPlane(3);
        break;
    case 11:
        GotoMyAnt();
        break;
    case 12:
        GotoSpider();
        break;
    case 13:
        GotoBQueen();
        break;
    case 14:
        GotoRQueen();
        break;
    case 15:
        SetPause(GamePaused == 0);
        break;
    case 16:
        EditScentMenu();
        break;
    case 17:
        DoHealthSetY(event);
        break;
    case 18:
        DoWarnSetB(event);
        break;
    }
    clip_Off();
}

int far edit_scroll_and_redraw(int a, int b);

void far edit_scroll_delta(int a, int b)
{
    edit_scroll_and_redraw(a, b);
}

typedef struct {
    int x;
    int y;
} Pnt;

void far BoundEditPosition(void);
void far UpdateEdit(void);

struct Rect {
    int left;
    int top;
    int right;
    int bottom;
};

extern struct Rect far editTileRect;
extern void _fastcall win_GetObjRect(int obj, struct Rect far *rect);
extern Pnt far MapPnt;

int far edit_scroll_and_redraw(int dx, int dy)
{
    unsigned long error;
    int i;
    unsigned long fraction;
    int unused;
    int yStep;
    int xStep;
    int xDistance;
    int yDistance;

    if (dx == 0) {
        if (dy == 0)
            return 0;
    }
    xDistance = dx;
    xStep = 1;
    yStep = 1;
    yDistance = dy;
    error = 0;
    if (xDistance < 0) {
        xDistance = -xDistance;
        xStep = -1;
    }
    if (yDistance < 0) {
        yDistance = -yDistance;
        yStep = -1;
    }
    if (yDistance >= xDistance) {
        fraction = ((unsigned long)xDistance << 16) / yDistance;
        for (i = 0; i < yDistance; i++) {
            MapPnt.y += yStep;
            error += fraction;
            if ((error >> 16) & 1) {
                MapPnt.x += xStep;
                error ^= 0x10000L;
            }
        }
        BoundEditPosition();
        UpdateEdit();
        return 1;
    } else {
        fraction = ((unsigned long)yDistance << 16) / xDistance;
        for (i = 0; i < xDistance; i++) {
            MapPnt.x += xStep;
            error += fraction;
            if ((error >> 16) & 1) {
                MapPnt.y += yStep;
                error ^= 0x10000L;
            }
        }
        BoundEditPosition();
        UpdateEdit();
        return 1;
    }
}

void far win_EditChanged(void)
{
    win_GetObjRect(4, &editTileRect);
    fd_50F6_10E0 = (editTileRect.right - editTileRect.left) / g_19BE;
    fd_50F6_10DE = (editTileRect.bottom - editTileRect.top) / g_19C0 + 1;
    edit_invalidate_life_cache();
    g_19CE = 1;
    BoundEditPosition();
}

extern void far win_Open(int win, ...);

void far OpenEditWindow(void)
{
    win_Open(0);
}

void far ForceUpdateEdit(void)
{
    edit_invalidate_life_cache();
    UpdateEdit();
}

void far DoEditUpdateDraw(void)
{
    ForceUpdateEdit();
}

extern int _fastcall win_IsWinOpen(int win);
void far edit_render_viewport(void);
void far DrawEditGraphs(void);

void far UpdateEdit(void)
{
    if (win_IsWinOpen(0)) {
        clip_SetWin(0);
        edit_render_viewport();
        DrawEditGraphs();
        clip_Off();
    }
}

void far UpdateEditWindow(void)
{
    UpdateEdit();
}

void far f_0250_0ED2(void)
{
}

extern int far CurGameType;
extern int far CurExpTool;
extern void _fastcall win_SetColorFromObjNum(int obj);
extern void _fastcall win_DrawBitMapAtObjNum(int obj, int id);

void far win_DrawEditWindow(int flags)
{
    int id;

    if (flags & 2) {
        win_EditChanged();
        edit_render_viewport();
        win_EditChanged();
        if (CurGameType == 3)
            id = CurExpTool + 0x13ec;
        else
            id = 0x13f3;
        win_SetColorFromObjNum(7);
        win_DrawBitMapAtObjNum(7, id);
    }
}

void far BoundEditPosition(void)
{
    int limit;
    int ylimit;

    ylimit = 0x40;
    switch (MapPlane) {
    case 0:
    case 1:
        limit = 0x80;
        break;
    default:
        limit = 0x40;
    }
    if (MapPnt.x < 0)
        MapPnt.x = 0;
    else if (MapPnt.x + fd_50F6_10E0 > limit)
        MapPnt.x = limit - fd_50F6_10E0;
    if (MapPnt.y < 0)
        MapPnt.y = 0;
    else if (MapPnt.y + fd_50F6_10DE > ylimit)
        MapPnt.y = ylimit - fd_50F6_10DE;
}

void far CenterEdit(int x, int y)
{
    int width;

    switch (MapPlane) {
    case 0:
    case 1:
        width = 0x80;
        break;
    default:
        width = 0x40;
    }
    edit_scroll_delta(x - fd_50F6_10E0 / 2 - MapPnt.x, y - fd_50F6_10DE / 2 - MapPnt.y);
    BoundEditPosition();
}

extern int far ELayerMode;
extern unsigned char far PherMapA[64][32];
extern unsigned char far PherMapBN[64][32];
extern unsigned char far PherMapBT[64][32];
extern unsigned char far PherMapRN[64][32];
extern unsigned char far PherMapRT[64][32];
extern unsigned char far MapA[128][64];
extern unsigned char far LifeA[128][64];
extern int far MeBase;
extern int far MeType;
extern int far MeEgg;
extern int far MeDir;
extern unsigned char far MapB[64][64];
extern unsigned char far LifeB[64][64];
extern unsigned char far MapR[64][64];
extern unsigned char far LifeR[64][64];

/* OPEN (unclaimed draft, kept in place for CONST/_DATA order and identifier counts):
 * residue: the original keeps the tile value v in [bp-2] (memory) and mx/my in SI/DI with a
 * 4-byte frame; here v wins SI.  Taking &v reproduces the allocation (not adopted).  The
 * sums fd_049A+fd_04C2(+fd_0496) load in the original order only with one declaration
 * between fd_049A and fd_04C2 (mod-17 symbol order). */
extern void (far * far gfx_mask_to_buffer_hook)(char far *src, char far *dst, int x, int y);


extern int far FootX;
extern int far FootY;

void far DoCalcTile(int x, int y)
{
    int v;
    int mx;
    int my;

    mx = MapPnt.x + x;
    my = MapPnt.y + y;
    if (my > 0x3f) {
        mx += 0x40;
        my &= 0x3f;
    }
    edit_current_terrain_tile = 0;
    edit_current_life_tile = 0;
    switch (MapPlane) {
    case 0:
    case 1:
        mx &= 0x7f;
        switch (ELayerMode) {
        case 0:
            v = PherMapA[mx >> 1][my >> 1];
            break;
        case 1:
            v = PherMapBN[mx >> 1][my >> 1];
            break;
        case 2:
            v = PherMapBT[mx >> 1][my >> 1];
            break;
        case 3:
            v = PherMapRN[mx >> 1][my >> 1];
            break;
        case 4:
            v = PherMapRT[mx >> 1][my >> 1];
            break;
        default:
            goto noscent;
        }
        if (v > 0x10)
            edit_current_terrain_tile = ((v >> 4) & 0x1f) - 0x10;
        else
            edit_current_terrain_tile = 0;
noscent:
        if (edit_current_terrain_tile == 0)
            edit_current_terrain_tile = MapA[mx][my];
        v = LifeA[mx][my];
        if (v == 0)
            return;
        if (v == 0xff) {
            edit_current_life_tile = MeBase + MeType + 0x380;
            if (MeType < 8)
                edit_current_life_tile += MeEgg;
            else
                edit_current_life_tile += MeDir;
        } else if (v == 0xfe)
            edit_current_life_tile = MeBase + MeDir + MeType + 0x388;
        else
            edit_current_life_tile = v + 0x100;
        break;
    case 2:
        mx &= 0x3f;
        edit_current_terrain_tile = MapB[mx][my] - 0x70;
        v = LifeB[mx][my];
        if (v == 0)
            return;
        switch (v) {
        case 0xfe:
            edit_current_life_tile = MeBase + MeDir + MeType + 0x308;
            break;
        case 0xff:
            edit_current_life_tile = MeBase + MeType + 0x300;
            if (MeType < 8)
                edit_current_life_tile += MeEgg;
            else
                edit_current_life_tile += MeDir;
            break;
        default:
            edit_current_life_tile = v + 0x200;
        }
        break;
    case 3:
        mx &= 0x3f;
        edit_current_terrain_tile = MapR[mx][my] - 0x70;
        v = LifeR[mx][my];
        if (v == 0)
            return;
        switch (v) {
        case 0xfe:
            edit_current_life_tile = MeBase + MeDir + MeType + 0x308;
            break;
        case 0xff:
            edit_current_life_tile = MeBase + MeType + 0x300;
            if (MeType < 8)
                edit_current_life_tile += MeEgg;
            else
                edit_current_life_tile += MeDir;
            break;
        default:
            edit_current_life_tile = v + 0x200;
        }
        break;
    }
}


extern unsigned char far edit_cached_terrain_tiles[30 * 40];

/* STEERED: the point retains two frame words though only y is read.
 * Copying y through i selects the early DI load; original locals are unknown. */

void far edit_redraw_changed_tile(int x, int y)
{
    Pnt absolute;
    int i;
    int row;

    i = y;
    row = i;
    absolute.y = MapPnt.y + row;
    if (x < 0 || row < 0 || x >= 40 || row >= 30)
        return;
    if (absolute.y > 0x3f)
        Punt("Y>MAXAY");
    DoCalcTile(x, row);
    i = row * 40 + x;
    if (edit_cached_life_tiles[0][i] == -2) {
        edit_cached_life_tiles[0][i]++;
        return;
    }
    if (edit_cached_life_tiles[0][i] != edit_current_life_tile || edit_cached_terrain_tiles[i] != edit_current_terrain_tile || (row == 0 && g_19CE != 0)) {
        if (edit_current_life_tile)
            edit_draw_life_and_ground_tile(g_19BE * x + editTileRect.left, g_19C0 * row + editTileRect.top);
        else
            edit_draw_ground_tile(g_19BE * x + editTileRect.left, row * g_19C0 + editTileRect.top);
        edit_cached_life_tiles[0][i] = edit_current_life_tile;
        edit_cached_terrain_tiles[i] = edit_current_terrain_tile;
    }
}


extern void far clip_Push(void);
void far edit_set_viewport_clip(void);
extern long far TickCount(void);
extern void _fastcall win_SetColorNum(int color);
extern void far ui_draw_centered_clipped_text(char far *msg, struct Rect far *rect, int y);
void far PreDrawSpider(void);
void far PreDrawBalloons(void);
extern int far fd_50F6_37D2;
void far DrawSpider(void);
void far DrawBalloons(void);
extern int far fd_50F6_37D4;
extern void far GPutPic(int x, int y, char far *image);
extern Pnt far spider_composite_bitmap;
extern struct Rect far spider_composite_rect;

static struct Rect balTileRect;
static struct Rect balloonRect;
static Handle balBufHandle;
static Pnt edPenPos;
static char far *balBufPtr;

extern void far clip_Pop(void);

/* px and py are never read: their stepping keeps the dead loads of editRect.left/top (and of
 * g_19C0) alive.  The px step constant is not decided by the bytes (px += 16 is a hypothesis;
 * px++ compiles identically).  balloon = spider = 0 stores spider first (worker resG). */
void far edit_render_viewport(void)
{
    int spider;
    int balloon;
    int x;
    int y;
    int px;
    int py;

    balloon = spider = 0;
    clip_Push();
    edit_set_viewport_clip();
    if (g_19C6) {
        if (TickCount() > g_19CA) {
            if (g_19C6)
                g_19CE = 1;
            g_19C6 = 0;
        } else {
            win_SetColorNum(3);
            ui_draw_centered_clipped_text(g_19C6, &editTileRect, editTileRect.top + 4);
        }
    }
    PreDrawSpider();
    PreDrawBalloons();
    if (fd_50F6_37D2 != 500)
        DrawSpider();
    DrawBalloons();
    edit_prepare_life_tiles(MapPlane / 2);
    py = editTileRect.top;
    for (y = 0; y < fd_50F6_10DE; y++, py += g_19C0) {
        px = editTileRect.left;
        for (x = 0; x < fd_50F6_10E0; x++, px += 16) {
            if (x >= balTileRect.left && x < balTileRect.right && y >= balTileRect.top && y < balTileRect.bottom)
                goto drawballoon;
            if ((y >= fd_50F6_37D4 && y < fd_50F6_37D4 + 7 && x >= fd_50F6_37D2 && x < fd_50F6_37D2 + 7)
                || (y == fd_50F6_10DE - 1 && x == fd_50F6_10E0 - 1)) {
                if (spider)
                    continue;
                GPutPic(spider_composite_rect.left, spider_composite_rect.top, (char far *)&spider_composite_bitmap);
                spider = 1;
                if (balTileRect.left == 500)
                    continue;
            drawballoon:
                if (balloon)
                    continue;
                GPutPic(balloonRect.left, balloonRect.top, balBufPtr);
                balloon = 1;
                continue;
            }
            edit_redraw_changed_tile(x, y);
        }
    }
    edit_restore_tile_ems_map();
    if (balTileRect.left != 500) {
        mem_Unlock(balBufHandle);
        mem_Free(balBufHandle);
    }
    clip_Pop();
    g_19CE = 0;
}

extern int far MeHealth;
extern int far HealthB;
extern int far HealthR;
extern int near _foreColor;
extern void far GRectFill(struct Rect far *rect, int color);
extern void (far * near gfx_set_attributes_hook)(int a, int b, int c);
extern void far GRectOutline(struct Rect far *rect, int width);
extern int near g_3DE2;
extern int far MeWarnHealth;
extern int far ConvColor(int color);
extern int far BlkWarnHealth;
extern void far GRectInv(struct Rect far *rect);

/* h is computed from r before top is copied: /Og then sinks h = r.bottom - r.top into the
 * __aFlmul argument list (after the 0x10000L and frac pushes) as in the original.  The three
 * vals[] stores share one source line: the /Zi line-entry flush must fall after 16BA
 * (records.py FORBID (1680,16BA]); line layout is a hypothesis (worker resG). */
void far DrawEditGraphs(void)
{
    static int objs[3] = { 0x11, 0x12, 0x13 };
    int obj;
    int h;
    long frac;
    struct Rect r;
    int far *vals[3];
    int i;
    int top;

    vals[0] = &MeHealth; vals[1] = &HealthB; vals[2] = &HealthR;
    for (i = 0; i < 3; i++) {
        obj = objs[i];
        frac = ((long)*vals[i] << 16) / 100;
        win_SetColorFromObjNum(obj);
        win_GetObjRect(obj, &r);
        h = r.bottom - r.top;
        top = r.top;
        r.top = r.bottom - (int)(h * frac / 0x10000L);
        if (r.top < r.bottom) {
            GRectFill(&r, _foreColor);
            if ((gfx_display_mode & 1) && i == 0) {
                (*gfx_set_attributes_hook)(0, 0, 0);
                GRectOutline(&r, 1);
                win_SetColorFromObjNum(obj);
            }
        }
        if (r.top > top) {
            r.bottom = r.top;
            r.top = top;
            GRectFill(&r, g_3DE2);
        }
        if (i == 0) {
            r.top = (100 - MeWarnHealth) * h / 100 + top;
            r.bottom = r.top + 1;
            GRectFill(&r, ConvColor(15));
        }
        if (i == 1) {
            r.top = (100 - BlkWarnHealth) * h / 100 + top;
            r.bottom = r.top + 1;
            GRectInv(&r);
        }
    }
}

extern char far * far _fstrcpy(char far *dest, char far *src);
extern char far * far * far MiscStrs;
extern char far * far _fstrcat(char far *dest, char far *src);
extern char far * far * far ScenarioNameStrs;
extern void far win_SetObjFormatStr(int obj, char far *text);
extern void _fastcall win_DrawTitle(int obj);

void far SetEditWinTitle(void)
{
    char buf[80];

    _fstrcpy(buf, "SimAnt");
    _fstrcat(buf, MiscStrs[15]);
    _fstrcat(buf, ScenarioNameStrs[CurGameType]);
    win_SetObjFormatStr(1, buf);
    if (win_IsWinOpen(0)) {
        clip_Push();
        clip_SetWin(0);
        win_DrawTitle(1);
        clip_Pop();
    }
}

extern int far SpidOn;
extern int far SpidX;
extern int far SpidY;

void far PreDrawSpider(void)
{
    int x, y, px, py;
    int sx, sy;

    spider_composite_rect.top = 0x8000;
    fd_50F6_37D2 = 500;
    fd_50F6_37D4 = 500;
    if (!SpidOn)
        return;
    y = MapPnt.y;
    x = MapPnt.x;
    px = x * g_19BE;
    py = y * g_19C0;
    sx = SpidX;
    sy = SpidY;
    if (gfx_display_mode == 2) {
        sx = sx * 3 / 4;
        sy = sy * 3 / 4;
    }
    if (MapPlane != 1)
        return;
    if (px > sx)
        return;
    if (fd_50F6_10E0 * g_19BE + px < sx)
        return;
    if (py > sy)
        return;
    if (fd_50F6_10DE * g_19C0 + py < sy)
        return;
    spider_composite_bitmap.x = 7 * g_19BE;
    spider_composite_bitmap.y = 7 * g_19C0;
    fd_50F6_37D2 = SpidX / 16 - x - 3;
    fd_50F6_37D4 = SpidY / 16 - y - 3;
}

extern void far anim_bitmap_to_buffer(int x, int y, Pnt far *buf, int id);
void far DrawLegs(int x, int y, int dir, int frame);
void far DrawPalps(int x, int y, int dir);
extern void (far * far gfx_scratch_to_buffer_hook)(char far *p, int stride);
extern void far gfx_buffer_line_target(Pnt far *buf, int mode);
extern int far SMode;
extern int far Scycle;
extern char far DBodX[];
extern char far DBodY[];
extern int far SpidDir;
extern char far BodX[];
extern char far BodY[];
extern int far fd_3D57_07B2;
extern long far SpidBalloonTicks;
extern int far SRand64(void);
extern int far SRand2(void);
extern int far WantSpiderBalloon;
extern int far spider_message_variant;
extern int far LastSMode;
extern char far * far * far SpiderMsgs;
extern char far Dy8[8];
extern char far Dx8[8];
extern int far SRand32(void);
void far AddMsgBalloon(int x, int y, int plane, int style, char far *msg);

/*sx,sy,mx,my,l,t*/
/* OPEN: residue register/slot allocation (px in SI, lx/ly in [bp-2]/[bp-4]), statement
 * scheduling of the SpidX/SpidY block and TickCount()/fd_098E compare operand order.
 * NOTE: its local identifier count is load-bearing for later claims (keep 18). */
void far DrawSpider(void)
{
    int py;
    int top;
    int left;
    int ty;
    int j;
    int skip;
    int modx;
    int mody;
    int i;
    int w;
    char far *p;
    int sx;
    int lx;
    int ly;
    int px;

    px = MapPnt.x * g_19BE;
    py = MapPnt.y * g_19C0;
    if (gfx_display_mode == 2) {
        sx = SpidX * 3 / 4;
        modx = sx % 12;
        mody = (SpidY * 3 / 4) % 12;
        left = sx - modx + editTileRect.left - px - 0x24;
        top = SpidY * 3 / 4 - mody + editTileRect.top - py - 0x24;
    } else {
        modx = SpidX & 0xf;
        mody = SpidY & 0xf;
        left = SpidX - modx + editTileRect.left - px - 0x30;
        top = SpidY - mody + editTileRect.top - py - 0x30;
    }
    spider_composite_rect.left = left;
    spider_composite_rect.top = top;
    spider_composite_rect.bottom = top + spider_composite_bitmap.y;
    spider_composite_rect.right = left + spider_composite_bitmap.x;
    edit_prepare_life_tiles(MapPlane / 2);
    w = 2;
    switch (edit_tile_renderer_kind) {
    case 2:
        w = 6;
    case 1:
        skip = 2;
        break;
    case 3:
        skip = 8;
        break;
    }
    skip = g_19C0 / skip * spider_composite_bitmap.x - w * 7;
    p = (char far *)&spider_composite_bitmap + 4;
    for (j = 0, ty = fd_50F6_37D4; j < 7; j++, ty++, p += skip) {
        int tx;
        int n;
        int idx;

        for (idx = ty * 40 + (tx = fd_50F6_37D2), n = 0; n < 7; n++, tx++, p += w, idx++) {
            DoCalcTile(tx, ty);
            if (idx >= 0 && idx < 1200)
                edit_cached_life_tiles[0][idx] = -1;
            if (edit_current_life_tile)
                edit_compose_life_tile();
            else
                edit_copy_ground_tile();
            (*gfx_scratch_to_buffer_hook)(p, spider_composite_bitmap.x);
        }
    }
    edit_restore_tile_ems_map();
    (gfx_display_mode & 1) ? gfx_buffer_line_target(&spider_composite_bitmap, 0) : (gfx_display_mode == 2 ? gfx_buffer_line_target(&spider_composite_bitmap, 1) : gfx_buffer_line_target(&spider_composite_bitmap, 2));
    if (SMode == 5) {
        lx = DBodX[Scycle] + 0x30;
        ly = DBodY[Scycle] + 0x30;
        if (gfx_display_mode == 2) {
            lx = lx * 3 / 4 + modx;
            ly = ly * 3 / 4 + mody;
        } else {
            lx += modx;
            ly += mody;
        }
        anim_bitmap_to_buffer(lx, ly, &spider_composite_bitmap, Scycle + 0x41a);
    } else {
        lx = BodX[SpidDir] + 0x30;
        ly = BodY[SpidDir] + 0x30;
        if (gfx_display_mode == 2) {
            anim_bitmap_to_buffer(lx = lx * 3 / 4 + modx, ly = ly * 3 / 4 + mody, &spider_composite_bitmap, SpidDir + 1000);
            DrawLegs((modx + 0x24) * 4 / 3, (mody + 0x24) * 4 / 3, SpidDir, Scycle & 7);
            DrawPalps((modx + 0x24) * 4 / 3, (mody + 0x24) * 4 / 3, SpidDir);
        } else {
            anim_bitmap_to_buffer(modx + lx, mody + ly, &spider_composite_bitmap, SpidDir + 1000);
            DrawLegs(modx + 0x30, mody + 0x30, SpidDir, Scycle & 7);
            DrawPalps(modx + 0x30, mody + 0x30, SpidDir);
        }
    }
    if (fd_3D57_07B2) {
        if (GamePaused == 0 && SpidBalloonTicks < TickCount()) {
            SpidBalloonTicks = TickCount() + SRand64() + 180;
            if (SRand2() == 0) {
                WantSpiderBalloon = 1;
                if (++spider_message_variant >= 5)
                    spider_message_variant = 0;
            } else
                WantSpiderBalloon = 0;
        }
        if (SMode == LastSMode && SMode <= 4) {
            if (WantSpiderBalloon)
                AddMsgBalloon((Dx8[SpidDir] << 3) + SpidX, (Dy8[SpidDir] << 3) + SpidY, 1, 10,
                              SpiderMsgs[SMode * 5 + spider_message_variant]);
        } else {
            SpidBalloonTicks = TickCount() + SRand32() + 30;
            WantSpiderBalloon = 0;
            LastSMode = SMode;
        }
    }
}

extern void (far * near gfx_fill_rect_hook)(int x0, int y0, int x1, int y1, int color);
extern int far BoyDir;
extern int far BoyHere;
extern int far MowX;
extern int far MowY;

/* OPEN: residue commutative operand order MapPnt.x + EditColumns (original loads the
 * MapPnt member first) - structural, not changed by names or preceding declaration counts. */
void far edit_draw_foot_mower_overlays(void)
{
    int x;
    int y;
    int t;

    if (MapPnt.x + fd_50F6_10E0 >= FootX && FootX + 15 >= MapPnt.x
        && MapPnt.y + fd_50F6_10DE >= FootY && FootY + 15 >= MapPnt.y) {
        x = (FootX - MapPnt.x) * g_19BE + editTileRect.left;
        y = (FootY - MapPnt.y) * g_19C0 + editTileRect.top;
        (*gfx_fill_rect_hook)(x, y, 15 * g_19BE + x, 15 * g_19C0 + y, g_19C4 | 0x10);
        x = FootX - MapPnt.x;
        y = FootY - MapPnt.y;
        if (BoyDir & 1)
            InvalEuMap(x, y, x + 16, y + 6);
        else
            InvalEuMap(x, y, x + 6, y + 16);
        if (BoyHere == 3 || BoyHere == 4) {
            if (MapPnt.x + fd_50F6_10E0 >= MowX && MowX + 0x1b >= MapPnt.x
                && MapPnt.y + fd_50F6_10DE >= MowY && MowY + 0x1b >= MapPnt.x) {
                x = (MowX - MapPnt.x) * g_19BE + editTileRect.left;
                y = (MowY - MapPnt.y) * g_19C0 + editTileRect.top;
                (*gfx_fill_rect_hook)(x, y, 15 * g_19BE + x, 15 * g_19C0 + y, g_19C4 | 0x20);
                x = MowX - MapPnt.x;
                y = MowY - MapPnt.y;
                InvalEuMap(x, y, x + 0x1b, y + 0x1b);
            }
        }
    }
}

void far ed_MoveTo(int x, int y)
{
    if (gfx_display_mode == 2) {
        x = x * 3 / 4;
        y = y * 3 / 4;
    }
    edPenPos.x = x;
    edPenPos.y = y;
}

extern void far gfx_buffer_line(int x0, int y0, int x1, int y1, int color);

void far ed_LineTo(int x, int y)
{
    if (gfx_display_mode == 2) {
        x = x * 3 / 4;
        y = y * 3 / 4;
    }
    gfx_buffer_line(edPenPos.x, edPenPos.y, x, y, _foreColor);
    edPenPos.x = x;
    edPenPos.y = y;
}

extern int far MeSMode;
extern int far SRand1(int range);
extern int far MeMode;
extern char far PyT[4];
extern char far PxT[4];
extern char far PyT2[4];
extern char far PxT2[4];
extern char far PyD[4];
extern char far PxD[4];
extern char far PyD2[4];
extern char far PxD2[4];
void far DrawPalps(int x, int y, int dir)
{
    int r;

    if (SMode <= 1 && MeSMode < 6)
        r = 0;
    else
        r = SRand1(4);
    if (MeMode == 1)
        (*gfx_set_attributes_hook)(ConvColor(1), 0, 0);
    else
        (*gfx_set_attributes_hook)(ConvColor(15), 0, 0);
    switch (dir) {
    case 0:
        ed_MoveTo(x + 4, y - 10);
        ed_LineTo(x + PxT[r], y + PyT[r]);
        ed_LineTo(x + PxT2[r], y + PyT2[r]);
        ed_MoveTo(x - 4, y - 10);
        ed_LineTo(x - PxT[r], y + PyT[r]);
        ed_LineTo(x - PxT2[r], y + PyT2[r]);
        break;
    case 1:
        ed_MoveTo(x + 10, y - 3);
        ed_LineTo(x + PxD[r], y + PyD[r]);
        ed_LineTo(x + PxD2[r], y + PyD2[r]);
        ed_MoveTo(x + 3, y - 10);
        ed_LineTo(x - PyD[r], y - PxD[r]);
        ed_LineTo(x - PyD2[r], y - PxD2[r]);
        break;
    case 2:
        ed_MoveTo(x + 10, y - 4);
        ed_LineTo(x - PyT[r], y - PxT[r]);
        ed_LineTo(x - PyT2[r], y - PxT2[r]);
        ed_MoveTo(x + 10, y + 4);
        ed_LineTo(x - PyT[r], y + PxT[r]);
        ed_LineTo(x - PyT2[r], y + PxT2[r]);
        break;
    case 3:
        ed_MoveTo(x + 10, y + 3);
        ed_LineTo(x + PxD[r], y - PyD[r]);
        ed_LineTo(x + PxD2[r], y - PyD2[r]);
        ed_MoveTo(x + 3, y + 10);
        ed_LineTo(x - PyD[r], y + PxD[r]);
        ed_LineTo(x - PyD2[r], y + PxD2[r]);
        break;
    case 4:
        ed_MoveTo(x + 4, y + 10);
        ed_LineTo(x + PxT[r], y - PyT[r]);
        ed_LineTo(x + PxT2[r], y - PyT2[r]);
        ed_MoveTo(x - 4, y + 10);
        ed_LineTo(x - PxT[r], y - PyT[r]);
        ed_LineTo(x - PxT2[r], y - PyT2[r]);
        break;
    case 5:
        ed_MoveTo(x - 10, y + 3);
        ed_LineTo(x - PxD[r], y - PyD[r]);
        ed_LineTo(x - PxD2[r], y - PyD2[r]);
        ed_MoveTo(x - 3, y + 10);
        ed_LineTo(x + PyD[r], y + PxD[r]);
        ed_LineTo(x + PyD2[r], y + PxD2[r]);
        break;
    case 6:
        ed_MoveTo(x - 10, y - 4);
        ed_LineTo(x + PyT[r], y - PxT[r]);
        ed_LineTo(x + PyT2[r], y - PxT2[r]);
        ed_MoveTo(x - 10, y + 4);
        ed_LineTo(x + PyT[r], y + PxT[r]);
        ed_LineTo(x + PyT2[r], y + PxT2[r]);
        break;
    case 7:
        ed_MoveTo(x - 10, y - 3);
        ed_LineTo(x - PxD[r], y + PyD[r]);
        ed_LineTo(x - PxD2[r], y + PyD2[r]);
        ed_MoveTo(x - 3, y - 10);
        ed_LineTo(x + PyD[r], y - PxD[r]);
        ed_LineTo(x + PyD2[r], y - PxD2[r]);
        break;
    }
}

extern char far Ly[4];
extern char far Lx[4];
extern char far L1yA[8];
extern char far L1xA[8];
extern char far L1yB[8];
extern char far L1xB[8];
extern char far L2yA[8];
extern char far L2xA[8];
extern char far L2yB[8];
extern char far L2xB[8];
extern char far L3yA[8];
extern char far L3xA[8];
extern char far L3yB[8];
extern char far L3xB[8];
extern char far L4yA[8];
extern char far L4xA[8];
extern char far L4yB[8];
extern char far L4xB[8];
extern char far Dy[4];
extern char far fd_3D57_0A8C[4];
extern char far D1yA[8];
extern char far D1xA[8];
extern char far D1yB[8];
extern char far D1xB[8];
extern char far D2yA[8];
extern char far D2xA[8];
extern char far D2yB[8];
extern char far D2xB[8];
extern char far D3yA[8];
extern char far D3xA[8];
extern char far D3yB[8];
extern char far D3xB[8];
extern char far D4yA[8];
extern char far D4xA[8];
extern char far D4yB[8];
extern char far D4xB[8];
void far DrawLegs(int x, int y, int dir, int frame)
{
    int other;

    other = (frame + 4) & 7;
    (*gfx_set_attributes_hook)(ConvColor(15), 0, 0);
    switch (dir) {
    case 0:
        ed_MoveTo(x + Lx[0], y + Ly[0]);
        ed_LineTo(x + L1xA[frame], y + L1yA[frame]);
        ed_LineTo(x + L1xB[frame], y + L1yB[frame]);
        ed_MoveTo(x + Lx[1], y + Ly[1]);
        ed_LineTo(x + L2xA[frame], y + L2yA[frame]);
        ed_LineTo(x + L2xB[frame], y + L2yB[frame]);
        ed_MoveTo(x + Lx[2], y + Ly[2]);
        ed_LineTo(x + L3xA[frame], y + L3yA[frame]);
        ed_LineTo(x + L3xB[frame], y + L3yB[frame]);
        ed_MoveTo(x + Lx[3], y + Ly[3]);
        ed_LineTo(x + L4xA[frame], y + L4yA[frame]);
        ed_LineTo(x + L4xB[frame], y + L4yB[frame]);
        ed_MoveTo(x - Lx[0], y + Ly[0]);
        ed_LineTo(x - L1xA[other], y + L1yA[other]);
        ed_LineTo(x - L1xB[other], y + L1yB[other]);
        ed_MoveTo(x - Lx[1], y + Ly[1]);
        ed_LineTo(x - L2xA[other], y + L2yA[other]);
        ed_LineTo(x - L2xB[other], y + L2yB[other]);
        ed_MoveTo(x - Lx[2], y + Ly[2]);
        ed_LineTo(x - L3xA[other], y + L3yA[other]);
        ed_LineTo(x - L3xB[other], y + L3yB[other]);
        ed_MoveTo(x - Lx[3], y + Ly[3]);
        ed_LineTo(x - L4xA[other], y + L4yA[other]);
        ed_LineTo(x - L4xB[other], y + L4yB[other]);
        break;
    case 1:
        ed_MoveTo(x + fd_3D57_0A8C[0], y + Dy[0]);
        ed_LineTo(x + D1xA[frame], y + D1yA[frame]);
        ed_LineTo(x + D1xB[frame], y + D1yB[frame]);
        ed_MoveTo(x + fd_3D57_0A8C[1], y + Dy[1]);
        ed_LineTo(x + D2xA[frame], y + D2yA[frame]);
        ed_LineTo(x + D2xB[frame], y + D2yB[frame]);
        ed_MoveTo(x + fd_3D57_0A8C[2], y + Dy[2]);
        ed_LineTo(x + D3xA[frame], y + D3yA[frame]);
        ed_LineTo(x + D3xB[frame], y + D3yB[frame]);
        ed_MoveTo(x + fd_3D57_0A8C[3], y + Dy[3]);
        ed_LineTo(x + D4xA[frame], y + D4yA[frame]);
        ed_LineTo(x + D4xB[frame], y + D4yB[frame]);
        ed_MoveTo(x - Dy[0], y - fd_3D57_0A8C[0]);
        ed_LineTo(x - D1yA[other], y - D1xA[other]);
        ed_LineTo(x - D1yB[other], y - D1xB[other]);
        ed_MoveTo(x - Dy[1], y - fd_3D57_0A8C[1]);
        ed_LineTo(x - D2yA[other], y - D2xA[other]);
        ed_LineTo(x - D2yB[other], y - D2xB[other]);
        ed_MoveTo(x - Dy[2], y - fd_3D57_0A8C[2]);
        ed_LineTo(x - D3yA[other], y - D3xA[other]);
        ed_LineTo(x - D3yB[other], y - D3xB[other]);
        ed_MoveTo(x - Dy[3], y - fd_3D57_0A8C[3]);
        ed_LineTo(x - D4yA[other], y - D4xA[other]);
        ed_LineTo(x - D4yB[other], y - D4xB[other]);
        break;
    case 2:
        ed_MoveTo(x - Ly[0], y + Lx[0]);
        ed_LineTo(x - L1yA[frame], y + L1xA[frame]);
        ed_LineTo(x - L1yB[frame], y + L1xB[frame]);
        ed_MoveTo(x - Ly[1], y + Lx[1]);
        ed_LineTo(x - L2yA[frame], y + L2xA[frame]);
        ed_LineTo(x - L2yB[frame], y + L2xB[frame]);
        ed_MoveTo(x - Ly[2], y + Lx[2]);
        ed_LineTo(x - L3yA[frame], y + L3xA[frame]);
        ed_LineTo(x - L3yB[frame], y + L3xB[frame]);
        ed_MoveTo(x - Ly[3], y + Lx[3]);
        ed_LineTo(x - L4yA[frame], y + L4xA[frame]);
        ed_LineTo(x - L4yB[frame], y + L4xB[frame]);
        ed_MoveTo(x - Ly[0], y - Lx[0]);
        ed_LineTo(x - L1yA[other], y - L1xA[other]);
        ed_LineTo(x - L1yB[other], y - L1xB[other]);
        ed_MoveTo(x - Ly[1], y - Lx[1]);
        ed_LineTo(x - L2yA[other], y - L2xA[other]);
        ed_LineTo(x - L2yB[other], y - L2xB[other]);
        ed_MoveTo(x - Ly[2], y - Lx[2]);
        ed_LineTo(x - L3yA[other], y - L3xA[other]);
        ed_LineTo(x - L3yB[other], y - L3xB[other]);
        ed_MoveTo(x - Ly[3], y - Lx[3]);
        ed_LineTo(x - L4yA[other], y - L4xA[other]);
        ed_LineTo(x - L4yB[other], y - L4xB[other]);
        break;
    case 3:
        ed_MoveTo(x + fd_3D57_0A8C[0], y - Dy[0]);
        ed_LineTo(x + D1xA[frame], y - D1yA[frame]);
        ed_LineTo(x + D1xB[frame], y - D1yB[frame]);
        ed_MoveTo(x + fd_3D57_0A8C[1], y - Dy[1]);
        ed_LineTo(x + D2xA[frame], y - D2yA[frame]);
        ed_LineTo(x + D2xB[frame], y - D2yB[frame]);
        ed_MoveTo(x + fd_3D57_0A8C[2], y - Dy[2]);
        ed_LineTo(x + D3xA[frame], y - D3yA[frame]);
        ed_LineTo(x + D3xB[frame], y - D3yB[frame]);
        ed_MoveTo(x + fd_3D57_0A8C[3], y - Dy[3]);
        ed_LineTo(x + D4xA[frame], y - D4yA[frame]);
        ed_LineTo(x + D4xB[frame], y - D4yB[frame]);
        ed_MoveTo(x - Dy[0], y + fd_3D57_0A8C[0]);
        ed_LineTo(x - D1yA[other], y + D1xA[other]);
        ed_LineTo(x - D1yB[other], y + D1xB[other]);
        ed_MoveTo(x - Dy[1], y + fd_3D57_0A8C[1]);
        ed_LineTo(x - D2yA[other], y + D2xA[other]);
        ed_LineTo(x - D2yB[other], y + D2xB[other]);
        ed_MoveTo(x - Dy[2], y + fd_3D57_0A8C[2]);
        ed_LineTo(x - D3yA[other], y + D3xA[other]);
        ed_LineTo(x - D3yB[other], y + D3xB[other]);
        ed_MoveTo(x - Dy[3], y + fd_3D57_0A8C[3]);
        ed_LineTo(x - D4yA[other], y + D4xA[other]);
        ed_LineTo(x - D4yB[other], y + D4xB[other]);
        break;
    case 4:
        ed_MoveTo(x - Lx[0], y - Ly[0]);
        ed_LineTo(x - L1xA[frame], y - L1yA[frame]);
        ed_LineTo(x - L1xB[frame], y - L1yB[frame]);
        ed_MoveTo(x - Lx[1], y - Ly[1]);
        ed_LineTo(x - L2xA[frame], y - L2yA[frame]);
        ed_LineTo(x - L2xB[frame], y - L2yB[frame]);
        ed_MoveTo(x - Lx[2], y - Ly[2]);
        ed_LineTo(x - L3xA[frame], y - L3yA[frame]);
        ed_LineTo(x - L3xB[frame], y - L3yB[frame]);
        ed_MoveTo(x - Lx[3], y - Ly[3]);
        ed_LineTo(x - L4xA[frame], y - L4yA[frame]);
        ed_LineTo(x - L4xB[frame], y - L4yB[frame]);
        ed_MoveTo(x + Lx[0], y - Ly[0]);
        ed_LineTo(x + L1xA[other], y - L1yA[other]);
        ed_LineTo(x + L1xB[other], y - L1yB[other]);
        ed_MoveTo(x + Lx[1], y - Ly[1]);
        ed_LineTo(x + L2xA[other], y - L2yA[other]);
        ed_LineTo(x + L2xB[other], y - L2yB[other]);
        ed_MoveTo(x + Lx[2], y - Ly[2]);
        ed_LineTo(x + L3xA[other], y - L3yA[other]);
        ed_LineTo(x + L3xB[other], y - L3yB[other]);
        ed_MoveTo(x + Lx[3], y - Ly[3]);
        ed_LineTo(x + L4xA[other], y - L4yA[other]);
        ed_LineTo(x + L4xB[other], y - L4yB[other]);
        break;
    case 5:
        ed_MoveTo(x - fd_3D57_0A8C[0], y - Dy[0]);
        ed_LineTo(x - D1xA[frame], y - D1yA[frame]);
        ed_LineTo(x - D1xB[frame], y - D1yB[frame]);
        ed_MoveTo(x - fd_3D57_0A8C[1], y - Dy[1]);
        ed_LineTo(x - D2xA[frame], y - D2yA[frame]);
        ed_LineTo(x - D2xB[frame], y - D2yB[frame]);
        ed_MoveTo(x - fd_3D57_0A8C[2], y - Dy[2]);
        ed_LineTo(x - D3xA[frame], y - D3yA[frame]);
        ed_LineTo(x - D3xB[frame], y - D3yB[frame]);
        ed_MoveTo(x - fd_3D57_0A8C[3], y - Dy[3]);
        ed_LineTo(x - D4xA[frame], y - D4yA[frame]);
        ed_LineTo(x - D4xB[frame], y - D4yB[frame]);
        ed_MoveTo(x + Dy[0], y + fd_3D57_0A8C[0]);
        ed_LineTo(x + D1yA[other], y + D1xA[other]);
        ed_LineTo(x + D1yB[other], y + D1xB[other]);
        ed_MoveTo(x + Dy[1], y + fd_3D57_0A8C[1]);
        ed_LineTo(x + D2yA[other], y + D2xA[other]);
        ed_LineTo(x + D2yB[other], y + D2xB[other]);
        ed_MoveTo(x + Dy[2], y + fd_3D57_0A8C[2]);
        ed_LineTo(x + D3yA[other], y + D3xA[other]);
        ed_LineTo(x + D3yB[other], y + D3xB[other]);
        ed_MoveTo(x + Dy[3], y + fd_3D57_0A8C[3]);
        ed_LineTo(x + D4yA[other], y + D4xA[other]);
        ed_LineTo(x + D4yB[other], y + D4xB[other]);
        break;
    case 6:
        ed_MoveTo(x + Ly[0], y - Lx[0]);
        ed_LineTo(x + L1yA[frame], y - L1xA[frame]);
        ed_LineTo(x + L1yB[frame], y - L1xB[frame]);
        ed_MoveTo(x + Ly[1], y - Lx[1]);
        ed_LineTo(x + L2yA[frame], y - L2xA[frame]);
        ed_LineTo(x + L2yB[frame], y - L2xB[frame]);
        ed_MoveTo(x + Ly[2], y - Lx[2]);
        ed_LineTo(x + L3yA[frame], y - L3xA[frame]);
        ed_LineTo(x + L3yB[frame], y - L3xB[frame]);
        ed_MoveTo(x + Ly[3], y - Lx[3]);
        ed_LineTo(x + L4yA[frame], y - L4xA[frame]);
        ed_LineTo(x + L4yB[frame], y - L4xB[frame]);
        ed_MoveTo(x + Ly[0], y + Lx[0]);
        ed_LineTo(x + L1yA[other], y + L1xA[other]);
        ed_LineTo(x + L1yB[other], y + L1xB[other]);
        ed_MoveTo(x + Ly[1], y + Lx[1]);
        ed_LineTo(x + L2yA[other], y + L2xA[other]);
        ed_LineTo(x + L2yB[other], y + L2xB[other]);
        ed_MoveTo(x + Ly[2], y + Lx[2]);
        ed_LineTo(x + L3yA[other], y + L3xA[other]);
        ed_LineTo(x + L3yB[other], y + L3xB[other]);
        ed_MoveTo(x + Ly[3], y + Lx[3]);
        ed_LineTo(x + L4yA[other], y + L4xA[other]);
        ed_LineTo(x + L4yB[other], y + L4xB[other]);
        break;
    case 7:
        ed_MoveTo(x - fd_3D57_0A8C[0], y + Dy[0]);
        ed_LineTo(x - D1xA[frame], y + D1yA[frame]);
        ed_LineTo(x - D1xB[frame], y + D1yB[frame]);
        ed_MoveTo(x - fd_3D57_0A8C[1], y + Dy[1]);
        ed_LineTo(x - D2xA[frame], y + D2yA[frame]);
        ed_LineTo(x - D2xB[frame], y + D2yB[frame]);
        ed_MoveTo(x - fd_3D57_0A8C[2], y + Dy[2]);
        ed_LineTo(x - D3xA[frame], y + D3yA[frame]);
        ed_LineTo(x - D3xB[frame], y + D3yB[frame]);
        ed_MoveTo(x - fd_3D57_0A8C[3], y + Dy[3]);
        ed_LineTo(x - D4xA[frame], y + D4yA[frame]);
        ed_LineTo(x - D4xB[frame], y + D4yB[frame]);
        ed_MoveTo(x + Dy[0], y - fd_3D57_0A8C[0]);
        ed_LineTo(x + D1yA[other], y - D1xA[other]);
        ed_LineTo(x + D1yB[other], y - D1xB[other]);
        ed_MoveTo(x + Dy[1], y - fd_3D57_0A8C[1]);
        ed_LineTo(x + D2yA[other], y - D2xA[other]);
        ed_LineTo(x + D2yB[other], y - D2xB[other]);
        ed_MoveTo(x + Dy[2], y - fd_3D57_0A8C[2]);
        ed_LineTo(x + D3yA[other], y - D3xA[other]);
        ed_LineTo(x + D3yB[other], y - D3xB[other]);
        ed_MoveTo(x + Dy[3], y - fd_3D57_0A8C[3]);
        ed_LineTo(x + D4yA[other], y - D4xA[other]);
        ed_LineTo(x + D4yB[other], y - D4xB[other]);
        break;
    }
}

void far edit_invalidate_spider_area(void)
{
    InvalEuMap((SpidX - MapPnt.x * g_19BE) / g_19BE - 3,
                (SpidY - MapPnt.y * g_19C0) / g_19C0 - 3,
                (SpidX - MapPnt.x * g_19BE) / g_19BE + 3,
                (SpidY - MapPnt.y * g_19C0) / g_19C0 + 3);
}

/* OPEN: residue as edit_draw_foot_mower_overlays: original keeps MapPnt.x in AX after the compare and adds
 * EditColumns; this compiles to load EditColumns then add the [bp-2] CSE temp. */
int far BalloonIsVisible(int plane, int x, int y)
{
    if (plane != MapPlane)
        return 0;
    if (x < MapPnt.x || x >= MapPnt.x + fd_50F6_10E0)
        return 0;
    if (y - 3 < MapPnt.y || y >= MapPnt.y + fd_50F6_10DE)
        return 0;
    return 1;
}

extern int far EggBalloonCnt;
extern Pnt far CurEggPnt;
extern int far CurEggPlane;
extern Pnt far LastEggPnt;
extern int far LastEggPlane;

void far EggBalloons(int x, int y, int plane)
{
    if (EggBalloonCnt != 0)
        return;
    if (!BalloonIsVisible(plane, x, y))
        return;
    if (CurEggPnt.x == x && CurEggPnt.y == y && CurEggPlane == plane) {
        EggBalloonCnt++;
        return;
    }
    LastEggPnt.x = x;
    LastEggPnt.y = y;
    LastEggPlane = plane;
}

extern int far FightBalloonCnt;
extern Pnt far CurFightPnt;
extern int far CurFightPlane;
extern Pnt far LastFightPnt;
extern int far LastFightPlane;

void far FightBalloons(int x, int y, int plane)
{
    if (FightBalloonCnt != 0)
        return;
    if (!BalloonIsVisible(plane, x, y))
        return;
    if (CurFightPnt.x == x && CurFightPnt.y == y && CurFightPlane == plane) {
        FightBalloonCnt++;
        return;
    }
    LastFightPnt.x = x;
    LastFightPnt.y = y;
    LastFightPlane = plane;
}

extern int far QueenBalloonCnt;
extern Pnt far CurQueenPnt;
extern int far CurQueenPlane;
extern Pnt far LastQueenPnt;
extern int far LastQueenPlane;

void far QueenBalloons(int x, int y, int plane)
{
    if (QueenBalloonCnt != 0)
        return;
    if (!BalloonIsVisible(plane, x, y))
        return;
    if (CurQueenPnt.x == x && CurQueenPnt.y == y && CurQueenPlane == plane) {
        QueenBalloonCnt++;
        return;
    }
    LastQueenPnt.x = x;
    LastQueenPnt.y = y;
    LastQueenPlane = plane;
}

extern int far RestBalloonCnt;
extern Pnt far CurRestPnt;
extern int far CurRestPlane;
extern Pnt far LastRestPnt;
extern int far LastRestPlane;

void far RestBalloons(int x, int y, int plane)
{
    if (RestBalloonCnt != 0)
        return;
    if (!BalloonIsVisible(plane, x, y))
        return;
    if (CurRestPnt.x == x && CurRestPnt.y == y && CurRestPlane == plane) {
        RestBalloonCnt++;
        return;
    }
    LastRestPnt.x = x;
    LastRestPnt.y = y;
    LastRestPlane = plane;
}

extern int far message_balloon_count;
extern Pnt far CurBalloonPnts[];
extern int far CurBalloonPlane[];
extern int far CurBalloonFlags[];
extern char far * far CurBalloonMsgs[];

void far AddMsgBalloon(int x, int y, int plane, int style, char far *msg)
{
    int tx;
    int ty;

    if (style == 10) {
        tx = x / g_19BE;
        ty = y / g_19C0;
    } else {
        tx = x;
        ty = y;
    }
    if (message_balloon_count >= 6)
        return;
    if (!BalloonIsVisible(plane, tx, ty))
        return;
    CurBalloonPnts[message_balloon_count].x = style == 10 ? x : g_19BE * x + 8;
    CurBalloonPnts[message_balloon_count].y = style == 10 ? y : g_19C0 * y + 8;
    CurBalloonPlane[message_balloon_count] = plane;
    CurBalloonFlags[message_balloon_count] = style;
    CurBalloonMsgs[message_balloon_count] = msg;
    message_balloon_count++;
}

extern int far WantBFightBalloon;
extern int far BFightBalloonIndex;
extern char far * far * far BFightMsgs;
extern int far WantRFightBalloon;
extern int far RFightBalloonIndex;
extern char far * far * far RFightMsgs;
extern int far WantEggBalloon;
extern long far BFightBalloonTicks;
extern long far RFightBalloonTicks;
extern long far EggBalloonTicks;
extern long far QueenBalloonTicks;
extern int far SRand4(void);
extern int far fd_50F6_0F7A;
extern char far * far * far EggMsgs;
extern int far WantQueenBalloon;
extern int far QueenBalloonIndex;
extern char far * far * far QueenMsgs;
extern int far WantRestBalloon;
extern int far RestBalloonIndex;
extern char far * far * far RestMsgs;
extern void far font_SetFont(int font);
extern Handle far MakeBalloon(char far *msg, int flags);
extern long far RestBalloonTicks;
extern Handle far mem_Alloc(long size, int flags, char far *name);
extern void (far * far gfx_buffer_intersection_hook)(void far *a, void far *b, void far *c, void far *d);

/* OPEN: residue only the operand order of the five TickCount() vs long-timer compares
 * (original: cmp mem,dx / cmp mem,ax).  A declaration order of the timer externs was found
 * that fixes all five in a different DrawSpider state; it is count-coupled with DrawSpider. */
void far DrawCurBalloons(void)
{
    if (!fd_3D57_07B2 || ELayerMode != -1)
        return;
    if (FightBalloonCnt == 0 && LastFightPnt.x >= 0 && LastFightPnt.y >= 0) {
        CurFightPnt = LastFightPnt;
        CurFightPlane = LastFightPlane;
        FightBalloonCnt++;
        RFightBalloonTicks = 0;
        BFightBalloonTicks = 0;
    }
    if (FightBalloonCnt > 0) {
        if (GamePaused == 0) {
            if (BFightBalloonTicks < TickCount()) {
                BFightBalloonTicks = TickCount() + SRand32() + 60;
                if (SRand2() == 0) {
                    WantBFightBalloon = 1;
                    if (BFightMsgs[++BFightBalloonIndex] == 0)
                        BFightBalloonIndex = 0;
                } else
                    WantBFightBalloon = 0;
            }
            if (RFightBalloonTicks < TickCount()) {
                RFightBalloonTicks = TickCount() + SRand32() + 60;
                if (SRand2() == 0) {
                    WantRFightBalloon = 1;
                    if (RFightMsgs[++RFightBalloonIndex] == 0)
                        RFightBalloonIndex = 0;
                } else
                    WantRFightBalloon = 0;
            }
        }
        if (WantBFightBalloon)
            AddMsgBalloon(CurFightPnt.x, CurFightPnt.y, CurFightPlane, 0, BFightMsgs[BFightBalloonIndex]);
        if (WantRFightBalloon)
            AddMsgBalloon(CurFightPnt.x, CurFightPnt.y, CurFightPlane, 1, RFightMsgs[RFightBalloonIndex]);
    }
    if (EggBalloonCnt == 0 && LastEggPnt.x >= 0 && LastEggPnt.y >= 0) {
        CurEggPnt = LastEggPnt;
        CurEggPlane = LastEggPlane;
        EggBalloonCnt++;
        EggBalloonTicks = 0;
        WantEggBalloon = 0;
    }
    if (EggBalloonCnt > 0) {
        if (GamePaused == 0 && EggBalloonTicks < TickCount()) {
            EggBalloonTicks = TickCount() + SRand32() + 170;
            if (SRand4() == 0) {
                WantEggBalloon = 1;
                if (EggMsgs[++fd_50F6_0F7A] == 0)
                    fd_50F6_0F7A = 0;
            } else
                WantEggBalloon = 0;
        }
        if (WantEggBalloon)
            AddMsgBalloon(CurEggPnt.x, CurEggPnt.y, CurEggPlane, 2, EggMsgs[fd_50F6_0F7A]);
    }
    if (QueenBalloonCnt == 0 && LastQueenPnt.x >= 0 && LastQueenPnt.y >= 0) {
        CurQueenPnt = LastQueenPnt;
        CurQueenPlane = LastQueenPlane;
        QueenBalloonCnt++;
        QueenBalloonTicks = 0;
        WantQueenBalloon = 0;
    }
    if (QueenBalloonCnt > 0) {
        if (GamePaused == 0 && QueenBalloonTicks < TickCount()) {
            QueenBalloonTicks = TickCount() + SRand32() + 180;
            if (SRand4() == 0) {
                WantQueenBalloon = 1;
                if (QueenMsgs[++QueenBalloonIndex] == 0)
                    QueenBalloonIndex = 0;
            } else
                WantQueenBalloon = 0;
        }
        if (WantQueenBalloon)
            AddMsgBalloon(CurQueenPnt.x, CurQueenPnt.y, CurQueenPlane, 2, QueenMsgs[QueenBalloonIndex]);
    }
    if (RestBalloonCnt == 0 && LastRestPnt.x >= 0 && LastRestPnt.y >= 0) {
        CurRestPnt = LastRestPnt;
        CurRestPlane = LastRestPlane;
        RestBalloonCnt++;
        RestBalloonTicks = 0;
        WantRestBalloon = 0;
    }
    if (RestBalloonCnt > 0) {
        if (GamePaused == 0 && RestBalloonTicks < TickCount()) {
            RestBalloonTicks = TickCount() + SRand64() + 120;
            if (SRand2() == 0) {
                WantRestBalloon = 1;
                if (RestMsgs[++RestBalloonIndex] == 0)
                    RestBalloonIndex = 0;
            } else
                WantRestBalloon = 0;
        }
        if (WantRestBalloon)
            AddMsgBalloon(CurRestPnt.x, CurRestPnt.y, CurRestPlane, 2, RestMsgs[RestBalloonIndex]);
    }
}

void far EditMsgBalloon(int x, int y, int plane, int style, char far *msg)
{
    char line1[256];
    char line2[256];

    if (BalloonIsVisible(plane, (x >> 4) + MapPnt.x, (y >> 4) + MapPnt.y) && msg != 0) {
        line2[0] = 0;
        line1[0] = 0;
    }
}

void far PreDrawBalloons(void)
{
    DrawCurBalloons();
}


/* OPEN: residue frame layout (0x58), i in DI, pic pointer in memory; logic complete. */

void far DrawBalloons(void)
{
    int idx;
    int tx;
    int col;
    int ty;
    int wt;
    int wpix;
    int skip;
    int ht;
    int bpp;
    int rowbytes;
    int div;
    int by;
    int bx;
    int saved;
    int shown;
    Pnt pos;
    Handle hs[1];
    char far *dst;
    char far *bufp;
    int far *pic;
    Handle h;
    int i;
    int row;
    unsigned n; /* low-word byte count retained for _fmemset */

    font_SetFont(2);
    bpp = 2;
    rowbytes = 0x80;
    switch (edit_tile_renderer_kind) {
    case 2:
        bpp = 6;
        rowbytes = 0x48;
    case 1:
        div = 2;
        break;
    case 3:
        div = 8;
        rowbytes = 0x20;
        break;
    }
    if (fd_50F6_37D2 == 500)
        edit_set_viewport_clip();
    balTileRect.left = 500;
    for (i = 0, shown = 0; i < message_balloon_count; i++) {
        if (shown >= 1 || CurBalloonMsgs[i] == 0)
            break;
        pos = CurBalloonPnts[i];
        if (!BalloonIsVisible(CurBalloonPlane[i], pos.x / g_19BE, pos.y / g_19C0))
            continue;
        WinPrintf("Vis message %s at %d,%d", CurBalloonMsgs[i], pos.x, pos.y);
        shown++;
        hs[i] = h = MakeBalloon(CurBalloonMsgs[i], 0);
        pic = (int far *)mem_Lock(h);
        by = pos.y - pic[5] - 4;
        bx = pos.x + 4;
        wt = (bx % g_19BE + pic[4] + g_19BE - 1) / g_19BE;
        ht = (by % g_19C0 + pic[5] + g_19C0 - 1) / g_19C0;
        balTileRect.top = by / g_19C0 - MapPnt.y;
        balTileRect.left = bx / g_19BE - MapPnt.x;
        balTileRect.bottom = ht + balTileRect.top;
        balTileRect.right = balTileRect.left + wt;
        wpix = g_19BE * wt;
        n = ht * wt * rowbytes;
        /* Original CWD-sign-extends the 16-bit allocation sum; keep n unsigned for _fmemset. */
        balBufHandle = mem_Alloc((long)(int)(n + 4), 9, "balbuf");
        balBufPtr = mem_Lock(balBufHandle);
        bufp = balBufPtr;
        ((int far *)bufp)[0] = g_19BE * wt;
        ((int far *)bufp)[1] = g_19C0 * ht;
        skip = g_19C0 / div * ((int far *)bufp)[0] - wt * bpp;
        dst = bufp + 4;
        _fmemset(dst, 0, n);
        balloonRect.left = g_19BE * balTileRect.left + editTileRect.left;
        balloonRect.top = g_19C0 * balTileRect.top + editTileRect.top;
        balloonRect.bottom = balloonRect.top + ((int far *)bufp)[1];
        balloonRect.right = balloonRect.left + ((int far *)bufp)[0];
        edit_prepare_life_tiles(MapPlane / 2);
        saved = i;
        for (row = 0, ty = balTileRect.top; row < ht; row++, ty++, dst += skip) {
            idx = ty * 40 + balTileRect.left;
            for (tx = balTileRect.left, col = 0; col < wt; col++, tx++, dst += bpp, idx++) {
                DoCalcTile(tx, ty);
                if (edit_current_life_tile)
                    edit_compose_life_tile();
                else
                    edit_copy_ground_tile();
                (*gfx_scratch_to_buffer_hook)(dst, wpix);
                if (idx >= 0 && idx < 1200)
                    edit_cached_life_tiles[0][idx] = -1;
            }
        }
        edit_restore_tile_ems_map();
        if (fd_50F6_37D2 != 500)
            (*gfx_buffer_intersection_hook)(&spider_composite_rect, &spider_composite_bitmap, &balloonRect, bufp);
        (*gfx_mask_to_buffer_hook)((char far *)pic + 8, bufp, bx % g_19BE, by % g_19C0);
        if (fd_50F6_37D2 != 500)
            (*gfx_buffer_intersection_hook)(&balloonRect, bufp, &spider_composite_rect, &spider_composite_bitmap);
        mem_Unlock(h);
        mem_Free(h);
        i = saved;
    }
    font_SetFont(0);
    message_balloon_count = 0;
}


extern struct Rect far fd_50F6_1104;
extern void far clip_intersect_rect_list(struct Rect far *rects);

void far edit_set_viewport_clip(void)
{
    struct Rect rects[3];

    win_GetObjRect(0x15, &fd_50F6_1104);
    rects[0] = editTileRect;
    rects[1] = fd_50F6_1104;
    rects[2].top = 0x8000;
    clip_intersect_rect_list(rects);
}
