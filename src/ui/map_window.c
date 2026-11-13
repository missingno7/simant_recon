/*
 * Handles map window events, view setup and map image generation. It draws map data and keeps
 * the view cursor aligned with the selected location.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS: overlay section 12 (S12); segment 384C; partial original translation unit.
 * Windows: ANTEDIT, from recorded function pairs in the Windows symbol inventory. Some pairs are
 * HIGH confidence, not confirmed.
 * Functions not yet exact: DrawMapCursor.
 */

#include <string.h>

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

struct Rect {
    int left;
    int top;
    int right;
    int bottom;
};

static int g_298E = 0;
int newMapForce = 0;
static int g_2992 = -1;
static int g_2994 = 0;
int g_2996 = 0;
static int g_2998 = -1;
long mapMessage = 0;
/*
 * Map/yard message expiry in TickCount units; LONG_MAX means indefinite.
 */
long map_message_deadline = 0;
/*
 * Forces map and yard refresh after message or view changes.
 */
int map_yard_redraw_pending = 0;
static int g_29A4 = 0;

void far DeinitMapFunctions(void)
{
}

extern long far RallocMemoryFree(void);
extern long far RallocMemorySoft(void);
extern void far WinPrintf(char far *format, ...);
extern char far * far * far mem_Alloc(long size, int kind, char far *name);
extern char far * far * far fd_50F6_10E2;
extern char near gfx_display_mode;
extern int far mapXsize;
extern int far mapYsize;
extern void (far * far map_wide_row_converter)();
extern void (far * far map_narrow_row_converter)();
extern void far gfx_planar_map128_pack2();
extern void far gfx_planar_map64_pack2();
extern void far gfx_tandy_map_duplicate_rows();
extern void far WindowsMono_MakeTable4x4a();
extern void far WindowsMono_MakeTable4x4b();
extern void far gfx_planar_map128_pack4();
extern void far gfx_planar_map64_pack4();

void far InitMapFunctions(void)
{
    WinPrintf("\nFREE+SOFT AT INITMAP=%ld", RallocMemoryFree() + RallocMemorySoft());
    fd_50F6_10E2 = mem_Alloc(0x2000L, 1, "Generated buffer window");
    switch (gfx_display_mode) {
    case 0:
    case 8:
        mapXsize = 4;
        mapYsize = 4;
        map_wide_row_converter = gfx_planar_map128_pack2;
        map_narrow_row_converter = gfx_planar_map64_pack2;
        break;
    case 2:
        mapXsize = 2;
        mapYsize = 2;
        map_wide_row_converter = gfx_tandy_map_duplicate_rows;
        map_narrow_row_converter = gfx_tandy_map_duplicate_rows;
        break;
    case 3:
    case 5:
    case 7:
        mapXsize = 4;
        mapYsize = 4;
        map_wide_row_converter = WindowsMono_MakeTable4x4a;
        map_narrow_row_converter = WindowsMono_MakeTable4x4b;
        break;
    case 4:
        mapXsize = 2;
        mapYsize = 2;
        map_wide_row_converter = gfx_planar_map128_pack4;
        map_narrow_row_converter = gfx_planar_map64_pack4;
        break;
    }
}

extern void far MapAreaEvent(struct Event far *ev);
extern void far MapToYard(void);
extern void far ClearMapScentButtons(void);
extern void far SetMapPlane(int plane);
extern void _fastcall win_ToTop(int win);
extern void far SetMapModeAnt(int mode);
extern void far OpenModeWindow(void);
void far MapToYellowAnt(struct Event far *ev);
extern void far OpenCasteWindow(void);
extern void far MysteryButton(void);
extern void far OpenHistoryWindow(void);
extern void far ScoreDialog(void);
extern void far OpenInfoWindow(void);
extern int far LessonTemp;
extern void far DoWinHelp(int win);
extern void far MapToolsMenu(void);
extern void far DrawCastePopUp(void);

void far ProcMapEvent(struct Event far *ev)
{
    switch (ev->code) {
    case 0x102: MapAreaEvent(ev); break;
    case 0x105: MapToYard(); break;
    case 0x106: ClearMapScentButtons(); SetMapPlane(1); break;
    case 0x107: ClearMapScentButtons(); SetMapPlane(2); break;
    case 0x108: ClearMapScentButtons(); SetMapPlane(3); win_ToTop(0x100); break;
    case 0x109: SetMapModeAnt(4); win_ToTop(0x100); break;
    case 0x10a: SetMapModeAnt(5); break;
    case 0x10b: SetMapModeAnt(8); break;
    case 0x10c: SetMapModeAnt(6); break;
    case 0x10d: SetMapModeAnt(7); break;
    case 0x10e: g_2994 = !g_2994; break;
    case 0x10f: OpenModeWindow(); break;
    case 0x110: MapToYellowAnt(ev); break;
    case 0x111: OpenCasteWindow(); break;
    case 0x112: MysteryButton(); break;
    case 0x113: OpenHistoryWindow(); break;
    case 0x114: ScoreDialog(); break;
    case 0x115: OpenInfoWindow(); break;
    case 0x116: LessonTemp = 1; DoWinHelp(0x103); break;
    case 0x117: MapToolsMenu(); break;
    case 0x118: DrawCastePopUp(); break;
    }
}

extern void far win_Open(int win, ...);

void far OpenMapWindow(void)
{
    win_Open(0x100);
}

extern int _fastcall win_IsWinOpen(int win);
extern void far clip_Push(void);
extern void far clip_SetWin(int win);
extern int far MapPnt[2];
extern struct Rect far map_viewport_rect;
extern struct Rect far mapCursorRect;
extern int far fd_50F6_10DE;
extern int far map_side_margin_pixels;
extern int far fd_50F6_10E0;
extern void far GRectInvOutline(struct Rect far *rect, int width);
extern void far clip_Pop(void);


extern int far multiplier;
extern void far win_MapChanged(void);
extern int far MapMode;
extern char far * far * far map_generated_image_handle;
extern char far * far mem_Lock(char far * far *handle);
extern void far mem_Unlock(char far * far *handle);
extern unsigned char far LifeA[128][64];
extern unsigned char far MapA[128][64];
extern int far TERRAINset;
extern unsigned char far LTab[];
extern unsigned char far HTab[];
extern unsigned char far CTab[];
extern unsigned char far bw_LTab[];
extern unsigned char far bw_HTab[];
extern unsigned char far bw_CTab[];
extern unsigned char far LifeR[64][64];
extern unsigned char far MapR[64][64];
extern unsigned char far LifeB[64][64];
extern unsigned char far MapB[64][64];
extern unsigned char far bw_CTabR[];
extern unsigned char far CTabR[];
extern int far BpopT;
extern int far RpopT;
extern int far HealthR;
extern int near gfx_screen_width_pixels;
extern void far font_SetFont(int font);
extern void far win_PrintfAtObj(int obj, char far *format, ...);
extern int far HealthB;
extern void far win_DrawHBar(int obj, long fraction);
extern char far * far * far map_scanline_image_handle;
extern void far Punt(char far *msg);
extern unsigned char far PherMapBN[];
extern unsigned char far PherMapBT[];
extern unsigned char far PherMapRN[];
extern unsigned char far PherMapRT[];
extern unsigned char far PherMapA[];
extern int far ConvColor(int color);
extern long far TickCount(void);
extern void _fastcall win_SetColorNum(int color);
extern void far ui_draw_centered_clipped_text(long msg, struct Rect far *rect, int y);
extern void far clip_SubInclude(struct Rect far *rect);
extern int far SpidOn;
extern int far MapPlane;
extern int far SpidX;
extern int far SpidY;
extern int far SpidDir;
extern void far mem_Free(char far * far *handle);
extern void far clip_Off(void);
extern int far CurGameType;
extern int far CurExpTool;
extern void _fastcall win_SetColorFromObjNum(int obj);
extern void _fastcall win_DrawBitMapAtObjNum(int obj, int id);
extern int _fastcall win_DrawBitMap(int x, int y, int id);
extern int far FootHere;
extern int far FootX;
extern int far FootY;
extern int far BoyDir;
extern int far BoyHere;
extern int far MowX;
extern int far MowY;
extern void far AddFood(int count, int sound);
extern void far myBeginSound(int sound, int a, int b);
extern void far KillSomeAnts(int side);
extern void far AddSomeAnts(int side);
extern void far SubtractFood(void);
extern void far GotoMyAnt(void);
extern void _fastcall win_GetObjRect(int obj, struct Rect far *rect);
void far DrawMapCursor(void)
{
    if (!win_IsWinOpen(0x100) || g_298E != 0)
        return;
    clip_Push();
    clip_SetWin(0x100);
    mapCursorRect.top = mapYsize * MapPnt[1] + map_viewport_rect.top;
    mapCursorRect.bottom = mapCursorRect.top + mapYsize * fd_50F6_10DE;
    mapCursorRect.left = mapXsize * MapPnt[0] + map_viewport_rect.left + map_side_margin_pixels;
    mapCursorRect.right = mapCursorRect.left + mapXsize * fd_50F6_10E0;
    GRectInvOutline(&mapCursorRect, 2);
    g_298E = 1;
    clip_Pop();
}



void far EraseMapCursor(void)
{
    if (!win_IsWinOpen(0x100) || g_298E != 1)
        return;
    clip_Push();
    clip_SetWin(0x100);
    GRectInvOutline(&mapCursorRect, 2);
    g_298E = 0;
    clip_Pop();
}

void far ToggleMapCursor(void)
{
    if (g_298E)
        EraseMapCursor();
    else
        DrawMapCursor();
}


/*
 * Dispatch the map bitmap operation according to whether its scale multiplier is 64.
 */
void far map_dispatch_scaled_bitmap(char far *src, char far *dst, int n)
{
    if (multiplier == 64)
        (*map_narrow_row_converter)(src, dst, multiplier, n);
    else
        (*map_wide_row_converter)(src, dst, multiplier, n);
}


/*
 * Notify the map-window change handler after map data changes.
 */
void far map_notify_view_changed(void)
{
    win_MapChanged();
}


void far map_generate_surface_colours(void)
{
    int fresh;
    unsigned char far *buf;
    unsigned char far *p;
    unsigned char far *q;
    int x, y, c;

    fresh = g_2994;
    if (MapMode != g_2992) {
        map_notify_view_changed();
        g_2992 = MapMode;
        fresh = 0;
    }
    buf = (unsigned char far *)mem_Lock(map_generated_image_handle);
    if (fresh) {
        _fmemcpy(buf, mem_Lock(fd_50F6_10E2), 0x2000);
        mem_Unlock(fd_50F6_10E2);
    }
    p = &LifeA[0][0];
    q = &MapA[0][0];
    if (!(gfx_display_mode & 1)) {
        if (TERRAINset == 1) {
            for (x = 0; x < 64; x++, p -= 0x1fff, q -= 0x1fff)
                for (y = 0; y < 128; y++, p += 64, q += 64) {
                    c = *p;
                    if (c) *buf++ = LTab[c >> 3]; else if (!fresh) *buf++ = HTab[*q]; else buf++;
                }
        } else {
            for (x = 0; x < 64; x++, p -= 0x1fff, q -= 0x1fff)
                for (y = 0; y < 128; y++, p += 64, q += 64) {
                    c = *p;
                    if (c) *buf++ = LTab[c >> 3]; else if (!fresh) *buf++ = CTab[*q]; else buf++;
                }
        }
    } else {
        if (TERRAINset == 1) {
            for (x = 0; x < 64; x++, p -= 0x1fff, q -= 0x1fff)
                for (y = 0; y < 128; y++, p += 64, q += 64) {
                    c = *p;
                    if (c) *buf++ = bw_LTab[c >> 3]; else if (!fresh) *buf++ = bw_HTab[*q]; else buf++;
                }
        } else {
            for (x = 0; x < 64; x++, p -= 0x1fff, q -= 0x1fff)
                for (y = 0; y < 128; y++, p += 64, q += 64) {
                    c = *p;
                    if (c) *buf++ = bw_LTab[c >> 3]; else if (!fresh) *buf++ = bw_CTab[*q]; else buf++;
                }
        }
    }
    mem_Unlock(map_generated_image_handle);
}


void far map_expand_scent_colours(unsigned char far *src)
{
    unsigned char far *buf;
    int x, y, i;
    unsigned char c;

    buf = (unsigned char far *)mem_Lock(map_generated_image_handle);
    g_2992 = MapMode;
    if (gfx_display_mode & 1) {
        for (x = 0; x < 32; x++)
            for (y = 0; y < 64; y++) {
                i = ((x << 7) + y) << 1;
                c = src[(y << 5) + x];
                c = c ? (c >> 4) + 0x2e : 0;
                buf[i] = c;
                buf[i + 1] = c;
                buf[i + 0x80] = c;
                buf[i + 0x81] = c;
            }
    } else {
        for (x = 0; x < 32; x++)
            for (y = 0; y < 64; y++) {
                i = ((x << 7) + y) << 1;
                c = src[(y << 5) + x];
                c = c ? (c >> 5) + 0x10 : 0xb;
                buf[i] = c; buf[i + 1] = c;
                buf[i + 0x80] = c; buf[i + 0x81] = c;
            }
    }
    mem_Unlock(map_generated_image_handle);
}


void far map_generate_nest_colours(void)
{
    int fresh;
    unsigned char far *buf;
    unsigned char far *p;
    unsigned char far *q;
    int x, y, c;

    fresh = g_2994;
    if (MapMode != g_2992) {
        map_notify_view_changed();
        g_2992 = MapMode;
        fresh = 0;
    }
    buf = (unsigned char far *)mem_Lock(map_generated_image_handle);
    if (fresh) {
        _fmemcpy(buf, mem_Lock(fd_50F6_10E2), 0x2000);
        mem_Unlock(fd_50F6_10E2);
    }
    if (MapMode == 3) {
        p = &LifeR[0][0];
        q = &MapR[0][0];
    } else {
        p = &LifeB[0][0];
        q = &MapB[0][0];
    }
    if (gfx_display_mode & 1) {
        for (x = 0; x < 64; x++, p -= 0xfff, q -= 0xfff)
            for (y = 0; y < 64; y++, p += 64, q += 64) {
                c = *p;
                switch (c) {
                case 0:
                    if (!fresh) *buf++ = bw_CTabR[*q >> 2]; else buf++;
                    break;
                case 0xfe:
                case 0xff:
                    *buf++ = 0x27;
                    break;
                default:
                    if (c & 0x80) *buf++ = 0x25; else *buf++ = 0x23;
                    break;
                }
            }
    } else {
        for (x = 0; x < 64; x++, p -= 0xfff, q -= 0xfff)
            for (y = 0; y < 64; y++, p += 64, q += 64) {
                c = *p;
                switch (c) {
                case 0:
                    if (!fresh) *buf++ = CTabR[*q >> 2]; else buf++;
                    break;
                case 0xfe:
                case 0xff:
                    *buf++ = 1;
                    break;
                default:
                    if (c & 0x80) *buf++ = 3; else *buf++ = 0xf;
                    break;
                }
            }
    }
    mem_Unlock(map_generated_image_handle);
}


void far DrawMapData(void)
{
    int popMax, redHealth;
    long maxPop;

    popMax = 1;
    if (BpopT > popMax)
        popMax = BpopT;
    if (RpopT > popMax)
        popMax = RpopT;
    redHealth = RpopT == 0 ? 0 : HealthR;
    font_SetFont(gfx_screen_width_pixels == 320 ? 0 : 3);
    win_PrintfAtObj(0x119, "%-d", BpopT);
    win_PrintfAtObj(0x11a, "%-d", RpopT);
    font_SetFont(0);
    win_DrawHBar(0x11b, ((long)HealthB << 16) / 100);
    maxPop = popMax;
    win_DrawHBar(0x11d, ((long)BpopT << 16) / maxPop);
    win_DrawHBar(0x11c, ((long)redHealth << 16) / 100);
    win_DrawHBar(0x11e, ((long)RpopT << 16) / maxPop);
}

extern void (far * near gfx_fill_rect_hook)(int left, int top, int right, int bottom, int color);
extern void (far * near gfx_put_picture_hook)(int x, int y, char far *image, int width, int height);
void far DrawMapSpider(int x, int y, int kind);
void far DrawMapFoot(void);

void far map_render_immediate(void)
{
    int n, row, off, y, sx, sy;
    char far *img;
    char far *gen;
    char far *old;

    if (MapMode == 0) {
        MapToYard();
        return;
    }
    multiplier = 0x80;
    map_side_margin_pixels = newMapForce = 0;
    map_scanline_image_handle = mem_Alloc(0x400L, 1, "Map window image");
    map_generated_image_handle = mem_Alloc(0x2000L, 1, "Generated map window");
    if (MapMode != g_2992)
        win_MapChanged();
    switch (MapMode) {
    case 0:
        Punt("Draw map - yard");
        break;
    case 1:
        map_generate_surface_colours();
        break;
    case 2:
    case 3:
        map_generate_nest_colours();
        multiplier = 0x40;
        map_side_margin_pixels = mapXsize << 5;
        break;
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
    n = (map_viewport_rect.bottom - map_viewport_rect.top) / mapYsize;
    if (n > 64)
        WinPrintf("\nYMAXCOUNT =%d!!!!!", n);
    n = 64;
    (*gfx_fill_rect_hook)(map_viewport_rect.left, map_viewport_rect.top, map_viewport_rect.left + map_side_margin_pixels,
              map_viewport_rect.bottom, ConvColor(15));
    (*gfx_fill_rect_hook)(map_viewport_rect.right - map_side_margin_pixels, map_viewport_rect.top, map_viewport_rect.right,
              map_viewport_rect.bottom, ConvColor(15));
    EraseMapCursor();
    if (mapMessage) {
        if (TickCount() > map_message_deadline) {
            if (mapMessage)
                g_29A4 = 1;
            mapMessage = 0;
        } else {
            win_SetColorNum(3);
            ui_draw_centered_clipped_text(mapMessage, &map_viewport_rect, map_viewport_rect.top + 4);
        }
    }
    clip_Push();
    clip_SubInclude(&map_viewport_rect);
    img = mem_Lock(map_generated_image_handle);
    gen = mem_Lock(map_scanline_image_handle);
    if (SpidOn && !g_2994 && MapPlane == 1) {
        sx = SpidX >> 4;
        sy = SpidY >> 4;
    } else
        sy = 0x7fff;
    old = mem_Lock(fd_50F6_10E2);
    y = map_viewport_rect.top;
    for (row = 0, off = 0; row < n; row++, y += mapYsize) {
        if (_fmemcmp(old + off, img + off, multiplier) || map_yard_redraw_pending || (row < 8 && g_29A4)) {
            _fmemcpy(old + off, img + off, multiplier);
            map_dispatch_scaled_bitmap(img + off, gen, y);
            (*gfx_put_picture_hook)(map_viewport_rect.left + map_side_margin_pixels, y, gen, multiplier * mapXsize, mapYsize);
        }
        off += multiplier;
        if (sy != 0x7fff && sy + 4 <= row) {
            DrawMapSpider(sx, sy, SpidDir);
            sy = 0x7fff;
        }
    }
    if (sy != 0x7fff)
        DrawMapSpider(sx, sy, SpidDir);
    mem_Unlock(fd_50F6_10E2);
    mem_Unlock(map_scanline_image_handle);
    mem_Unlock(map_generated_image_handle);
    mem_Free(map_scanline_image_handle);
    mem_Free(map_generated_image_handle);
    if (MapPlane == 1 && !g_2994)
        DrawMapFoot();
    DrawMapCursor();
    clip_Pop();
    map_yard_redraw_pending = newMapForce;
    g_29A4 = 0;
}



void far DrawMap(void)
{
    if (win_IsWinOpen(0x100)) {
        clip_SetWin(0x100);
        map_render_immediate();
        DrawMapData();
        clip_Off();
    }
}


void far win_DrawMapWindow(int flags)
{
    int id;

    if (flags & 2) {
        if (MapMode == 0)
            MapToYard();
        else {
            win_MapChanged();
            clip_SetWin(0x100);
            DrawMapData();
            map_render_immediate();
            id = CurGameType == 3 ? CurExpTool + 0x13ec : 0x13f3;
            win_SetColorFromObjNum(0x117);
            win_DrawBitMapAtObjNum(0x117, id);
        }
    }
}


void far DrawMapSpider(int x, int y, int kind)
{
    int ys;
    unsigned char far *p;

    if (gfx_screen_width_pixels == 320) {
        x = x * 2 - 3;
        ys = y * 2 - 3;
    } else {
        x = x * 4 - 3;
        ys = y * 4 - 3;
    }
    win_DrawBitMap(x + map_viewport_rect.left, ys + map_viewport_rect.top, kind + 0x44c);
    y -= 2;
    if (fd_50F6_10E2) {
        p = (unsigned char far *)mem_Lock(fd_50F6_10E2);
        p += multiplier * y;
        for (x = y + 5; y < x; y++, p += multiplier) {
            if (y >= 64)
                break;
            if (y >= 0)
                *p = 0xff;
        }
        mem_Unlock(fd_50F6_10E2);
    }
}


void far DrawMapFoot(void)
{
    int x, y, end;
    unsigned char far *p;

    if (FootHere == 0)
        return;
    x = FootX << 2;
    y = FootY << 2;
    if (gfx_screen_width_pixels == 320) {
        x >>= 1;
        y >>= 1;
    }
    win_DrawBitMap(x + map_viewport_rect.left, y + map_viewport_rect.top, BoyDir + 0x4b0);
    if (BoyHere == 3 || BoyHere == 4) {
        x = MowX << 2;
        y = MowY << 2;
        if (gfx_screen_width_pixels == 320) {
            x >>= 1;
            y >>= 1;
        }
        win_DrawBitMap(x + map_viewport_rect.left, y + map_viewport_rect.top, (BoyDir & 1) + 0x4ba);
    }
    y = FootY;
    if (fd_50F6_10E2) {
        p = (unsigned char far *)mem_Lock(fd_50F6_10E2);
        p += multiplier * y;
        for (end = y + 8; y < end; y++, p += multiplier) {
            if (y >= 64)
                break;
            if (y >= 0)
                *p = 0xff;
        }
        mem_Unlock(fd_50F6_10E2);
    }
    newMapForce = 1;
}


void far MapToYellowAnt(struct Event far *ev)
{
    struct Rect r;
    int side;

    if (*(unsigned char far *)0x00000417L & 4) {
        if (*(unsigned char far *)0x00000417L & 3) {
            win_GetObjRect(0x110, &r);
            side = (r.left + r.right) / 2;
            side = ev->h >= side ? 0 : 1;
            if (*(unsigned char far *)0x00000417L & 8)
                KillSomeAnts(side);
            else
                AddSomeAnts(side);
        } else if (*(unsigned char far *)0x00000417L & 8) {
            myBeginSound(0x20, 0, 0x7e);
            SubtractFood();
        } else
            AddFood(0x96, 1);
    } else
        GotoMyAnt();
}
