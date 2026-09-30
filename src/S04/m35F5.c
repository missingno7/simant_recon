/* Overlay section S04, code frame 35F5: map window tools menu and mini map (Win16 ANTEDIT_MODULE map members). */

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
extern int far fd_50F6_0EAC;
extern void _fastcall win_GetObjSize(int obj, struct Pt far *size);
extern int far win_DoProxMenu();
extern void far SetExpTool(int tool);
extern int far fd_50F6_104C;
extern int far fd_50F6_0496;
extern int far fd_50F6_04C2;
extern int far MeLocY;
extern int far MeLocX;
extern int far MePlane;
extern void far ClearMyLife(int plane, int x, int y, int type, int dir);
extern int far fd_50F6_0A06;
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
extern struct Rect far fd_50F6_10D2;
extern int far f_1FD2_04E5(struct Pt far *pt, struct Rect far *r);
extern void far WinPrintf(char far *fmt, ...);
extern int far fd_50F6_3858;
extern int far fd_50F6_3856;
extern int far fd_50F6_0508[2];
extern int far fd_55B3_19BE;
extern int far fd_50F6_110C[2];
extern int far fd_55B3_19C0;
extern void far processEdit(struct Event far *ev);
extern int far fd_50F6_3854;
extern void far EraseMapCursor(void);
extern void far f_0250_0FC4(int x, int y);
extern void far f_0250_0E9D(void);
extern void far DrawMapCursor(void);
extern void far f_1FD2_04D0(struct Pt far *pt);
extern int far f_00F8_02AC(void);
extern void far OpenEditWindow(void);
extern char near g_5A97;
extern void far o00_3126_06A3(char far *src, char far *dst);
extern void far o00_3126_04D8(char far *src, char far *dst);
extern void far o03_3253_002F(char far *src, char far *dst, int mult);
extern void far o01_328E_01D5(char far *src, char far *dst, int y);
extern void far o01_328E_012C(char far *src, char far *dst, int y);
extern struct Rect far fd_50F6_3842;
extern int far fd_50F6_3852;
extern int far fd_55B3_2996;
extern char far * far f_171C_1A9E(long size, int flag, char far *name);
extern char far * far fd_50F6_385E;
extern char far * far fd_50F6_385A;
extern void far o12_384C_0432(void);
extern void far o12_384C_080E(void);
extern int near g_8BD2;
extern int far fd_3D57_07C8;
extern void far o12_384C_0706(unsigned char far *map);
extern unsigned char far PherMapBN[];
extern unsigned char far PherMapBT[];
extern unsigned char far PherMapRN[];
extern unsigned char far PherMapRT[];
extern unsigned char far PherMapA[];
extern int far f_1B4E_000D(int color);
extern void (far * near g_9134)(int left, int top, int right, int bottom, int color);
extern char far * far f_171C_1B84(char far *handle);
extern int near g_8BD4;
extern void (far * near g_914C)(int x, int y, char far *line, int width, int height);
extern void far f_171C_1BBA(char far *handle);
extern void far f_171C_1C0A(char far *handle);
extern void far win_Open();
extern void _fastcall win_Close(int win);
extern void far OpenMapYard(void);
extern int _fastcall win_GetEvent(struct Event far *);
extern void far win_FlushEvents(void);
extern struct Rect far fd_50F6_384A;
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

    if (!f_1FD2_04E5((struct Pt far *)&ev->h, &fd_50F6_10D2))
        return;
    last.x = (int)0x8000;
    WinPrintf("ePtr->mouse_flags=%x, MRPRESSED=%x", ev->modifiers, 0x800);
    if (ev->modifiers & 0x4800) {
        y = (ev->v - fd_50F6_10D2.top) / fd_50F6_3858;
        ev->h = ((ev->h - fd_50F6_10D2.left) / fd_50F6_3856 - fd_50F6_0508[0]) * fd_55B3_19BE + fd_50F6_110C[0];
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
            last = *(struct Pt far *)&ev->h;
            x = (ev->h - fd_50F6_10D2.left) / fd_50F6_3856;
            if (fd_50F6_3854 == 0x40)
                x -= 0x20;
            y = (ev->v - fd_50F6_10D2.top) / fd_50F6_3858;
            if (x >= 0 && x < fd_50F6_3854) {
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
        f_1FD2_04D0((struct Pt far *)&ev->h);
    } while (f_00F8_02AC());
}


void far Mini_MakeTable(char far *src, char far *dst, int y)
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


void far Mini_DrawMapI(void)
{
    char far *table;
    char far *line;
    int i;
    int y;
    int n;

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


void far OpenMiniMapWin(void)
{
    struct Pt pt;
    struct Event ev;
    int x;
    int y;

    if (g_5A97 & 1)
        g_8BD2 = g_8BD4 = 2;
    else
        g_8BD2 = g_8BD4 = 1;
    win_Open(0x1400);
    Mini_DrawMapI();
    DrawMiniMapCursor();
    if (f_00F8_02AC()) {
        while (f_00F8_02AC())
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
            !f_1FD2_04E5((struct Pt far *)&ev.h, &fd_50F6_3842))
            continue;
        pt.x = (int)0x8000;
        do {
            if (pt.x != ev.h || pt.y != ev.v) {
                pt = *(struct Pt far *)&ev.h;
                x = (ev.h - fd_50F6_3842.left) / g_8BD2;
                if (fd_50F6_3854 == 0x40)
                    x -= 0x20;
                y = (ev.v - fd_50F6_3842.top) / g_8BD4;
                if (x >= 0 && x < fd_50F6_3854) {
                    EraseMiniMapCursor();
                    EraseMapCursor();
                    f_0250_0FC4(x, y);
                    f_0250_0E9D();
                    DrawMapCursor();
                    DrawMiniMapCursor();
                }
            }
            f_1FD2_04D0((struct Pt far *)&ev.h);
        } while (f_00F8_02AC());
    }
    win_FlushEvents();
}


/* SCAFFOLD BEGIN: DrawMiniMapCursor best draft (148 vs 150 bytes): the original saves ES (segment of fd_50F6_384A) in CX after the left store and reuses it for the right store and the pushed rect segment; here left goes to CX and ES is reloaded from CONST. Not symbol-table state (worker resA: dummy identifiers before each referenced declaration, 1..16, no change); pointer, array, chained-assignment and operand-order forms tried; same residue as S12 DrawMapCursor */
void far DrawMiniMapCursor(void)
{
    fd_50F6_384A.top = fd_50F6_0508[1] * g_8BD4 + fd_50F6_3842.top;
    fd_50F6_384A.bottom = fd_50F6_384A.top + fd_50F6_10DE * g_8BD4;
    fd_50F6_384A.left = fd_50F6_0508[0] * g_8BD2 + fd_50F6_3842.left + fd_50F6_3852;
    fd_50F6_384A.right = fd_50F6_384A.left + fd_50F6_10E0 * g_8BD2;
    f_1CE2_0410(&fd_50F6_384A, 1);
    miniCursorOn = 1;
}
/* SCAFFOLD END */

void far EraseMiniMapCursor(void)
{
    f_1CE2_0410(&fd_50F6_384A, 1);
    miniCursorOn = 0;
}
