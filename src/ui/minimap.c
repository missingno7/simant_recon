/*
 * Handles the map tools menu and the small map window. It creates the map image table, draws the
 * view and maintains its cursor.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS: overlay section 4 (S04); segment 35F5; complete original translation unit.
 * Windows: ANTEDIT, from recorded function pairs in the Windows symbol inventory. Some pairs are
 * HIGH confidence, not confirmed.
 */

struct Rect {
    int left;
    int top;
    int right;
    int bottom;
};

struct Pt {
    int x;
    int y;
};

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

static int miniCursorOn = 0;
static int subMenus[8] = { -1, 0xc00, 0xf00, 0x1000, 0x1100, 0xd00, 0xe00, -1 };


extern void _fastcall win_GetObjRect(int obj, struct Rect far *rect);
extern int far CurGameType;
extern void _fastcall win_GetObjSize(int obj, struct Pt far *size);
extern int far win_DoProxMenu();
extern void far SetExpTool(int tool);
extern int far fd_50F6_104C;
extern int far MeDir;
extern int far MeType;
extern int far MeLocY;
extern int far MeLocX;
extern int far MePlane;
extern void far ClearMyLife(int plane, int x, int y, int type, int dir);
extern int far MeMode;
extern void far InitSpider(void);
extern void far SetEditWinTitle();
extern void far myBeginSound(int sound, int a, int b);
extern int far DoExpMenu(int x, int y);
extern void far InitYelloAnt(void);
extern int far fd_50F6_032E;
extern void far SetMyLife(int plane, int x, int y, int type, int dir, int code);
extern void far f_00DF_00B1(int id, int arg);
extern int _fastcall win_IsWinOpen(int win);
extern void far clip_Push(void);
extern void far clip_SetWin(int win);
extern void _fastcall win_SetColorFromObjNum(int obj);
extern void _fastcall win_DrawBitMapAtObjNum(int obj, int id);
extern void far clip_Pop(void);
extern struct Rect far map_viewport_rect;
extern int far PointInRect(struct Pt far *pt, struct Rect far *r);
extern void far WinPrintf(char far *fmt, ...);
extern int far mapYsize;
extern int far mapXsize;
extern int far MapPnt[2];
extern int far tileWidth;
extern int far editTileRect[2];
extern int far tileHeight;
extern void far processEdit(struct Event far *ev);
extern int far multiplier;
extern void far EraseMapCursor(void);
extern void far f_0250_0FC4(int x, int y);
extern void far f_0250_0E9D(void);
extern void far DrawMapCursor(void);
extern void far GetMousePos(struct Pt far *pt);
extern int far f_00F8_02AC(void);
extern void far OpenEditWindow(void);
extern char near gfx_display_mode;
extern void far gfx_planar_map64_pack8(char far *src, char far *dst);
extern void far gfx_planar_map128_pack8(char far *src, char far *dst);
extern void far Windows_MakeTable1x1(char far *src, char far *dst, int mult);
extern void far WindowsMono_MakeTable2x2b(char far *src, char far *dst, int y);
extern void far WindowsMono_MakeTable2x2a(char far *src, char far *dst, int y);
extern struct Rect far miniMapRect;
extern int far fd_50F6_3852;
extern int far mapMem;
extern char far * far mem_Alloc(long size, int flag, char far *name);
extern char far * far map_scanline_image_handle;
extern char far * far map_generated_image_handle;
extern void far map_generate_surface_colours(void);
extern void far map_generate_nest_colours(void);
extern int near minimap_x_scale;
extern int far MapMode;
extern void far map_expand_scent_colours(unsigned char far *map);
extern unsigned char far PherMapBN[];
extern unsigned char far PherMapBT[];
extern unsigned char far PherMapRN[];
extern unsigned char far PherMapRT[];
extern unsigned char far PherMapA[];
extern int far ConvColor(int color);
extern void (far * near gfx_fill_rect_hook)(int left, int top, int right, int bottom, int color);
extern char far * far mem_Lock(char far *handle);
extern int near minimap_y_scale;
extern void (far * near gfx_put_picture_hook)(int x, int y, char far *line, int width, int height);
extern void far mem_Unlock(char far *handle);
extern void far mem_Free(char far *handle);
extern void far win_Open();
extern void _fastcall win_Close(int win);
extern void far OpenMapYard(void);
extern int _fastcall win_GetEvent(struct Event far *);
extern void far win_FlushEvents(void);
extern struct Rect far miniMapCursorRect;
extern int far fd_50F6_10DE;
extern int far fd_50F6_10E0;
extern void far f_1CE2_0410(struct Rect far *r, int width);

void far MapToolsMenu(void);
void far MapAreaEvent(struct Event far *);
void far Mini_MakeTable(char far *, char far *, int);
void far Mini_DrawMapI(void);
void far OpenMiniMapWin(void);
void far DrawMiniMapCursor(void);
void far EraseMiniMapCursor(void);

void far MapToolsMenu(void)
{
    struct Rect r;
    struct Pt size;
    int item;

    win_GetObjRect(0x117, &r);
    switch (CurGameType) {
    case 1:
        win_GetObjSize(0xa00, &size);
        if (win_DoProxMenu(0xa00, -1, (r.right - size.x + r.left) / 2, r.top - size.y - 4) < 0)
            break;
        SetExpTool(fd_50F6_104C);
        CurGameType = 3;
        ClearMyLife(MePlane, MeLocX, MeLocY, MeType, MeDir);
        MeMode = 2;
        InitSpider();
        SetEditWinTitle(0, 0);
        myBeginSound(2, 0, 0x7e);
        break;
    case 2:
        win_GetObjSize(0xb00, &size);
        win_DoProxMenu(0xb00, -1, (r.right - size.x + r.left) / 2, r.top - size.y - 4);
        break;
    case 3:
        win_GetObjSize(0x900, &size);
        item = DoExpMenu((r.right - size.x + r.left) / 2, r.top - size.y - 4);
        if (item == -1)
            break;
        if (item == 7) {
            CurGameType = 1;
            InitYelloAnt();
            if (fd_50F6_032E == 1)
                SetMyLife(MePlane, MeLocX, MeLocY, MeType, MeDir, 0xff);
            SetEditWinTitle(0, 0);
            f_00DF_00B1(0x2afb, 0x7e);
        }
        SetExpTool(item);
        if (win_IsWinOpen(0x100)) {
            clip_Push();
            clip_SetWin(0x100);
            win_SetColorFromObjNum(0x117);
            win_DrawBitMapAtObjNum(0x117, fd_50F6_104C + 0x13ec);
            clip_Pop();
        }
        if (win_IsWinOpen(0)) {
            clip_Push();
            clip_SetWin(0);
            win_SetColorFromObjNum(7);
            win_DrawBitMapAtObjNum(7, fd_50F6_104C + 0x13ec);
            clip_Pop();
        }
        break;
    }
}


void far MapAreaEvent(struct Event far *ev)
{
    struct Pt last;
    int x;
    int y;

    if (!PointInRect((struct Pt far *)&ev->h, &map_viewport_rect))
        return;
    last.x = (int)0x8000;
    WinPrintf("ePtr->mouse_flags=%x, MRPRESSED=%x", ev->modifiers, 0x800);
    if (ev->modifiers & 0x4800) {
        y = (ev->v - map_viewport_rect.top) / mapYsize;
        ev->h = ((ev->h - map_viewport_rect.left) / mapXsize - MapPnt[0]) * tileWidth + editTileRect[0];
        ev->v = (y - MapPnt[1]) * tileHeight + editTileRect[1];
        if (ev->modifiers & 0x4000)
            ev->modifiers = 0x2000;
        else
            ev->modifiers = 0x200;
        processEdit(ev);
        return;
    }
    do {
        if (last.x != ev->h || last.y != ev->v) {
            last = *(struct Pt far *)&ev->h;
            x = (ev->h - map_viewport_rect.left) / mapXsize;
            if (multiplier == 0x40)
                x -= 0x20;
            y = (ev->v - map_viewport_rect.top) / mapYsize;
            if (x >= 0 && x < multiplier) {
                EraseMapCursor();
                f_0250_0FC4(x, y);
                f_0250_0E9D();
                DrawMapCursor();
            }
        }
        if (ev->modifiers & 0x6000) {
            OpenEditWindow();
            return;
        }
        GetMousePos((struct Pt far *)&ev->h);
    } while (f_00F8_02AC());
}


void far Mini_MakeTable(char far *src, char far *dst, int y)
{
    switch (gfx_display_mode) {
    case 0:
    case 4:
    case 8:
        if (multiplier == 0x40)
            gfx_planar_map64_pack8(src, dst);
        else
            gfx_planar_map128_pack8(src, dst);
        break;
    case 2:
        Windows_MakeTable1x1(src, dst, multiplier);
        break;
    case 3:
    case 5:
    case 7:
        if (multiplier == 0x40)
            WindowsMono_MakeTable2x2b(src, dst, y);
        else
            WindowsMono_MakeTable2x2a(src, dst, y);
        break;
    }
}


void far Mini_DrawMapI(void)
{
    char far *table;
    char far *line;
    int i;
    int y;
    int n;

    win_GetObjRect(0x1401, &miniMapRect);
    multiplier = 0x80;
    fd_50F6_3852 = 0;
    if (mapMem == 0) {
        map_scanline_image_handle = mem_Alloc(0x400L, 1, "Map window image");
        map_generated_image_handle = mem_Alloc(0x2000L, 1, "Generated map window");
    }
    if (fd_50F6_032E < 2)
        map_generate_surface_colours();
    if (fd_50F6_032E > 1 && fd_50F6_032E < 4) {
        map_generate_nest_colours();
        multiplier = 0x40;
        fd_50F6_3852 = minimap_x_scale << 5;
    }
    switch (MapMode) {
    case 4:
        map_expand_scent_colours(PherMapBN);
        break;
    case 5:
        map_expand_scent_colours(PherMapBT);
        break;
    case 6:
        map_expand_scent_colours(PherMapRN);
        break;
    case 7:
        map_expand_scent_colours(PherMapRT);
        break;
    case 8:
        map_expand_scent_colours(PherMapA);
        break;
    }
    (*gfx_fill_rect_hook)(miniMapRect.left, miniMapRect.top, miniMapRect.left + fd_50F6_3852,
              miniMapRect.bottom, ConvColor(15));
    (*gfx_fill_rect_hook)(miniMapRect.right - fd_50F6_3852 - 1, miniMapRect.top, miniMapRect.right,
              miniMapRect.bottom, ConvColor(15));
    table = mem_Lock(map_generated_image_handle);
    line = mem_Lock(map_scanline_image_handle);
    n = 64;
    y = miniMapRect.top;
    for (i = 0; i < n; i++, y += minimap_y_scale) {
        Mini_MakeTable(table + multiplier * i, line, y);
        (*gfx_put_picture_hook)(miniMapRect.left + fd_50F6_3852, y, line, multiplier * minimap_x_scale, minimap_y_scale);
    }
    mem_Unlock(map_scanline_image_handle);
    mem_Unlock(map_generated_image_handle);
    if (mapMem == 0) {
        mem_Free(map_scanline_image_handle);
        mem_Free(map_generated_image_handle);
    }
}


void far OpenMiniMapWin(void)
{
    struct Pt pt;
    struct Event ev;
    int x;
    int y;

    if (gfx_display_mode & 1)
        minimap_x_scale = minimap_y_scale = 2;
    else
        minimap_x_scale = minimap_y_scale = 1;
    win_Open(0x1400);
    Mini_DrawMapI();
    DrawMiniMapCursor();
    if (f_00F8_02AC()) {
        while (f_00F8_02AC())
            ;
        GetMousePos(&pt);
        if (PointInRect(&pt, &miniMapRect)) {
            win_Close(0x1400);
            OpenMapYard();
            return;
        }
    }
    while (win_IsWinOpen(0x1400)) {
        if (!win_GetEvent(&ev) || !win_IsWinOpen(0x1400) ||
            !PointInRect((struct Pt far *)&ev.h, &miniMapRect))
            continue;
        pt.x = (int)0x8000;
        do {
            if (pt.x != ev.h || pt.y != ev.v) {
                pt = *(struct Pt far *)&ev.h;
                x = (ev.h - miniMapRect.left) / minimap_x_scale;
                if (multiplier == 0x40)
                    x -= 0x20;
                y = (ev.v - miniMapRect.top) / minimap_y_scale;
                if (x >= 0 && x < multiplier) {
                    EraseMiniMapCursor();
                    EraseMapCursor();
                    f_0250_0FC4(x, y);
                    f_0250_0E9D();
                    DrawMapCursor();
                    DrawMiniMapCursor();
                }
            }
            GetMousePos((struct Pt far *)&ev.h);
        } while (f_00F8_02AC());
    }
    win_FlushEvents();
}


void far DrawMiniMapCursor(void)
{
    miniMapCursorRect.left = MapPnt[0] * minimap_x_scale + miniMapRect.left + fd_50F6_3852;
    miniMapCursorRect.top = MapPnt[1] * minimap_y_scale + miniMapRect.top;
    miniMapCursorRect.bottom = miniMapCursorRect.top + fd_50F6_10DE * minimap_y_scale;
    miniMapCursorRect.right = miniMapCursorRect.left + fd_50F6_10E0 * minimap_x_scale;
    f_1CE2_0410(&miniMapCursorRect, 1);
    miniCursorOn = 1;
}

void far EraseMiniMapCursor(void)
{
    f_1CE2_0410(&miniMapCursorRect, 1);
    miniCursorOn = 0;
}

/* Shows the minimap cursor if it is hidden and hides it if it is shown. No caller is
 * recorded in the DOS code (a menu or key handler may reach it through a table). */
void far ToggleMiniMapCursor(void)
{
    if (miniCursorOn)
        EraseMiniMapCursor();
    else
        DrawMiniMapCursor();
}
