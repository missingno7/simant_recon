#include "dos_types.h"
#include "portable/whole_program/platform/dos_memory.h"
#include "portable/whole_program/platform/dos_io.h"
#pragma pack(push, 2)
#include "portable/whole_program/platform/graphics_source_fields.h"
/* Overlay section S04, code frame 35F5: map window tools menu and mini map (Win16 ANTEDIT_MODULE map members). */

struct Rect {
    int16_t left;
    int16_t top;
    int16_t right;
    int16_t bottom;
};

struct Pt {
    int16_t x;
    int16_t y;
};

struct Event {
    int16_t what;
    int16_t message;
    int16_t x4;
    int16_t modifiers;
    int16_t h;
    int16_t v;
    int16_t code;
    int16_t xE;
};

static int16_t miniCursorOn = 0;
static int16_t subMenus[8] = { -1, 0xc00, 0xf00, 0x1000, 0x1100, 0xd00, 0xe00, -1 };


extern void  win_GetObjRect(int16_t obj, struct Rect  *rect);
extern int16_t  fd_50F6_0EAC;
extern void  win_GetObjSize(int16_t obj, struct Pt  *size);
extern int16_t  win_DoProxMenu();
extern void  SetExpTool(int16_t tool);
extern int16_t  fd_50F6_104C;
extern int16_t  fd_50F6_0496;
extern int16_t  fd_50F6_04C2;
extern int16_t  MeLocY;
extern int16_t  MeLocX;
extern int16_t  MePlane;
extern void  ClearMyLife(int16_t plane, int16_t x, int16_t y, int16_t type, int16_t dir);
extern int16_t  fd_50F6_0A06;
extern void  InitSpider(void);
extern void  SetEditWinTitle();
extern void  myBeginSound(int16_t sound, int16_t a, int16_t b);
extern int16_t  DoExpMenu(int16_t x, int16_t y);
extern void  InitYelloAnt(void);
extern int16_t  fd_50F6_032E;
extern void  SetMyLife(int16_t plane, int16_t x, int16_t y, int16_t type, int16_t dir, int16_t code);
extern void  myBeginSong(int16_t id, int16_t arg);
extern int16_t  win_IsWinOpen(int16_t win);
extern void  clip_Push(void);
extern void  clip_SetWin(int16_t win);
extern void  win_SetColorFromObjNum(int16_t obj);
extern void  win_DrawBitMapAtObjNum(int16_t obj, int16_t id);
extern void  clip_Pop(void);
extern struct Rect  fd_50F6_10D2;
extern int16_t  f_1FD2_04E5(struct Pt  *pt, struct Rect  *r);
extern void  WinPrintf(char  *fmt, ...);
extern int16_t  fd_50F6_3858;
extern int16_t  fd_50F6_3856;
extern int16_t  fd_50F6_0508[2];
extern int16_t  g_19BE;
extern int16_t  fd_50F6_110C[2];
extern int16_t  fd_55B3_19C0;
extern void  processEdit(struct Event  *ev);
extern int16_t  fd_50F6_3854;
extern void  EraseMapCursor(void);
extern void  CenterEdit(int16_t x, int16_t y);
extern void  UpdateEdit(void);
extern void  DrawMapCursor(void);
extern void  f_1FD2_04D0(struct Pt  *pt);
extern int16_t  myButton(void);
extern void  OpenEditWindow(void);
extern char  g_5A97;
extern void  o00_3126_06A3(char  *src, char  *dst);
extern void  o00_3126_04D8(char  *src, char  *dst);
extern void  o03_3253_002F(char  *src, char  *dst, int16_t mult);
extern void  o01_328E_01D5(char  *src, char  *dst, int16_t y);
extern void  o01_328E_012C(char  *src, char  *dst, int16_t y);
extern struct Rect  fd_50F6_3842;
extern int16_t  fd_50F6_3852;
extern int16_t  fd_55B3_2996;
extern char  *  f_171C_1A9E(int32_t size, int16_t flag, char  *name);
extern char  *  fd_50F6_385E;
extern char  *  fd_50F6_385A;
extern void  o12_384C_0432(void);
extern void  o12_384C_080E(void);
extern int16_t  g_8BD2;
extern int16_t  fd_3D57_07C8;
extern void  o12_384C_0706(uint8_t  *map);
extern uint8_t  PherMapBN[];
extern uint8_t  PherMapBT[];
extern uint8_t  PherMapRN[];
extern uint8_t  PherMapRT[];
extern uint8_t  PherMapA[];
extern char  *  f_171C_1B84(char  *handle);
extern int16_t  g_8BD4;
extern void ( *  g_914C)(int16_t x, int16_t y, char  *line, int16_t width, int16_t height);
extern void  f_171C_1BBA(char  *handle);
extern void  f_171C_1C0A(char  *handle);
extern void  win_Open();
extern void  win_Close(int16_t win);
extern void  OpenMapYard(void);
extern int16_t  win_GetEvent(struct Event  *);
extern void  win_FlushEvents(void);
extern struct Rect  fd_50F6_384A;
extern int16_t  fd_50F6_10DE;
extern int16_t  fd_50F6_10E0;
extern void  GRectInvOutline(struct Rect  *r, int16_t width);

void  MapToolsMenu(void);
void  MapAreaEvent(struct Event  *);
void  Mini_MakeTable(char  *, char  *, int16_t);
void  Mini_DrawMapI(void);
void  OpenMiniMapWin(void);
void  DrawMiniMapCursor(void);
void  EraseMiniMapCursor(void);

void  MapToolsMenu(void)
{
    struct Rect r;
    struct Pt size;
    int16_t item;

    win_GetObjRect(0x117, &r);
    switch (fd_50F6_0EAC) {
    case 1:
        win_GetObjSize(0xa00, &size);
        if (win_DoProxMenu(0xa00, -1, (r.right - size.x + r.left) / 2, r.top - size.y - 4) < 0)
            break;
        SetExpTool(fd_50F6_104C);
        fd_50F6_0EAC = 3;
        ClearMyLife(MePlane, MeLocX, MeLocY, fd_50F6_04C2, fd_50F6_0496);
        fd_50F6_0A06 = 2;
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
            fd_50F6_0EAC = 1;
            InitYelloAnt();
            if (fd_50F6_032E == 1)
                SetMyLife(MePlane, MeLocX, MeLocY, fd_50F6_04C2, fd_50F6_0496, 0xff);
            SetEditWinTitle(0, 0);
            myBeginSong(0x2afb, 0x7e);
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


void  MapAreaEvent(struct Event  *ev)
{
    struct Pt last;
    int16_t x;
    int16_t y;

    if (!f_1FD2_04E5((struct Pt  *)&ev->h, &fd_50F6_10D2))
        return;
    last.x = (int16_t)0x8000;
    WinPrintf("ePtr->mouse_flags=%x, MRPRESSED=%x", ev->modifiers, 0x800);
    if (ev->modifiers & 0x4800) {
        y = (ev->v - fd_50F6_10D2.top) / fd_50F6_3858;
        ev->h = ((ev->h - fd_50F6_10D2.left) / fd_50F6_3856 - fd_50F6_0508[0]) * g_19BE + fd_50F6_110C[0];
        ev->v = (y - fd_50F6_0508[1]) * fd_55B3_19C0 + fd_50F6_110C[1];
        if (ev->modifiers & 0x4000)
            ev->modifiers = 0x2000;
        else
            ev->modifiers = 0x200;
        processEdit(ev);
        return;
    }
    do {
        if (last.x != ev->h || last.y != ev->v) {
            last = *(struct Pt  *)&ev->h;
            x = (ev->h - fd_50F6_10D2.left) / fd_50F6_3856;
            if (fd_50F6_3854 == 0x40)
                x -= 0x20;
            y = (ev->v - fd_50F6_10D2.top) / fd_50F6_3858;
            if (x >= 0 && x < fd_50F6_3854) {
                EraseMapCursor();
                CenterEdit(x, y);
                UpdateEdit();
                DrawMapCursor();
            }
        }
        if (ev->modifiers & 0x6000) {
            OpenEditWindow();
            return;
        }
        f_1FD2_04D0((struct Pt  *)&ev->h);
    } while (myButton());
}


void  Mini_MakeTable(char  *src, char  *dst, int16_t y)
{
    switch (g_5A97) {
    case 0:
    case 4:
    case 8:
        if (fd_50F6_3854 == 0x40)
            o00_3126_06A3(src, dst);
        else
            o00_3126_04D8(src, dst);
        break;
    case 2:
        o03_3253_002F(src, dst, fd_50F6_3854);
        break;
    case 3:
    case 5:
    case 7:
        if (fd_50F6_3854 == 0x40)
            o01_328E_01D5(src, dst, y);
        else
            o01_328E_012C(src, dst, y);
        break;
    }
}


void  Mini_DrawMapI(void)
{
    char  *table;
    char  *line;
    int16_t i;
    int16_t y;
    int16_t n;

    win_GetObjRect(0x1401, &fd_50F6_3842);
    fd_50F6_3854 = 0x80;
    fd_50F6_3852 = 0;
    if (fd_55B3_2996 == 0) {
        fd_50F6_385E = f_171C_1A9E(0x400L, 1, "Map window image");
        fd_50F6_385A = f_171C_1A9E(0x2000L, 1, "Generated map window");
    }
    if (fd_50F6_032E < 2)
        o12_384C_0432();
    if (fd_50F6_032E > 1 && fd_50F6_032E < 4) {
        o12_384C_080E();
        fd_50F6_3854 = 0x40;
        fd_50F6_3852 = g_8BD2 << 5;
    }
    switch (fd_3D57_07C8) {
    case 4:
        o12_384C_0706(PherMapBN);
        break;
    case 5:
        o12_384C_0706(PherMapBT);
        break;
    case 6:
        o12_384C_0706(PherMapRN);
        break;
    case 7:
        o12_384C_0706(PherMapRT);
        break;
    case 8:
        o12_384C_0706(PherMapA);
        break;
    }
    (*g_9134)(fd_50F6_3842.left, fd_50F6_3842.top, fd_50F6_3842.left + fd_50F6_3852,
              fd_50F6_3842.bottom, f_1B4E_000D(15));
    (*g_9134)(fd_50F6_3842.right - fd_50F6_3852 - 1, fd_50F6_3842.top, fd_50F6_3842.right,
              fd_50F6_3842.bottom, f_1B4E_000D(15));
    table = f_171C_1B84(fd_50F6_385A);
    line = f_171C_1B84(fd_50F6_385E);
    n = 64;
    y = fd_50F6_3842.top;
    for (i = 0; i < n; i++, y += g_8BD4) {
        Mini_MakeTable(table + fd_50F6_3854 * i, line, y);
        (*g_914C)(fd_50F6_3842.left + fd_50F6_3852, y, line, fd_50F6_3854 * g_8BD2, g_8BD4);
    }
    f_171C_1BBA(fd_50F6_385E);
    f_171C_1BBA(fd_50F6_385A);
    if (fd_55B3_2996 == 0) {
        f_171C_1C0A(fd_50F6_385E);
        f_171C_1C0A(fd_50F6_385A);
    }
}


void  OpenMiniMapWin(void)
{
    struct Pt pt;
    struct Event ev;
    int16_t x;
    int16_t y;

    if (g_5A97 & 1)
        g_8BD2 = g_8BD4 = 2;
    else
        g_8BD2 = g_8BD4 = 1;
    win_Open(0x1400);
    Mini_DrawMapI();
    DrawMiniMapCursor();
    if (myButton()) {
        while (myButton())
            ;
        f_1FD2_04D0(&pt);
        if (f_1FD2_04E5(&pt, &fd_50F6_3842)) {
            win_Close(0x1400);
            OpenMapYard();
            return;
        }
    }
    while (win_IsWinOpen(0x1400)) {
        if (!win_GetEvent(&ev) || !win_IsWinOpen(0x1400) ||
            !f_1FD2_04E5((struct Pt  *)&ev.h, &fd_50F6_3842))
            continue;
        pt.x = (int16_t)0x8000;
        do {
            if (pt.x != ev.h || pt.y != ev.v) {
                pt = *(struct Pt  *)&ev.h;
                x = (ev.h - fd_50F6_3842.left) / g_8BD2;
                if (fd_50F6_3854 == 0x40)
                    x -= 0x20;
                y = (ev.v - fd_50F6_3842.top) / g_8BD4;
                if (x >= 0 && x < fd_50F6_3854) {
                    EraseMiniMapCursor();
                    EraseMapCursor();
                    CenterEdit(x, y);
                    UpdateEdit();
                    DrawMapCursor();
                    DrawMiniMapCursor();
                }
            }
            f_1FD2_04D0((struct Pt  *)&ev.h);
        } while (myButton());
    }
    win_FlushEvents();
}


void  DrawMiniMapCursor(void)
{
    fd_50F6_384A.left = fd_50F6_0508[0] * g_8BD2 + fd_50F6_3842.left + fd_50F6_3852;
    fd_50F6_384A.top = fd_50F6_0508[1] * g_8BD4 + fd_50F6_3842.top;
    fd_50F6_384A.bottom = fd_50F6_384A.top + fd_50F6_10DE * g_8BD4;
    fd_50F6_384A.right = fd_50F6_384A.left + fd_50F6_10E0 * g_8BD2;
    GRectInvOutline(&fd_50F6_384A, 1);
    miniCursorOn = 1;
}

void  EraseMiniMapCursor(void)
{
    GRectInvOutline(&fd_50F6_384A, 1);
    miniCursorOn = 0;
}

#pragma pack(pop)
