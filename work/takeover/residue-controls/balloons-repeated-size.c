/* Module at root frame 0250 (large-model code segment). */

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
extern int far fd_50F6_15C4[30][40];

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
                fd_50F6_15C4[v][h] = -1;
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
                fd_50F6_15C4[0][i] = -1;
    }
}

extern void far f_195A_007D(int handle);

void far f_0250_0114(void)
{
    if (g_19D0)
        f_195A_007D(g_19D0);
}

extern int far f_195A_0260(void);
extern char far fd_55B3_360C;
extern int far WinPrintf(char far *format, ...);
extern void far f_195A_0035(void);
extern int far fd_55B3_3614;
extern int far fd_55B3_3612;
extern void far f_195A_001D(void);
extern int far f_195A_004B(int pages);
extern void far f_195A_01CB(int handle, char far *name);
extern int far atexit(void (far *func)(void));

/*C*/
int far f_0250_012D(void)
{
    int ok;

    if (g_19D0 != 0)
        return 1;
    if (f_195A_0260() && fd_55B3_360C >= 0x40) {
        WinPrintf("\nEMS version: %x", fd_55B3_360C);
        f_195A_0035();
        WinPrintf("\ntotal pages: %d", fd_55B3_3614);
        WinPrintf("\nfree  pages: %d", fd_55B3_3612);
        if (fd_55B3_3612 >= 8) {
            f_195A_001D();
            g_19D0 = f_195A_004B(8);
            f_195A_01CB(g_19D0, "TILESXXX");
            atexit(f_0250_0114);
            return 1;
        }
    }
    return 0;
}

extern Handle far fd_50F6_10EA;
extern void far db_ReleaseHandle(Handle handle);
extern Handle far fd_50F6_10E6;

void far f_0250_01E7(void)
{
    if (fd_50F6_10EA) {
        db_ReleaseHandle(fd_50F6_10EA);
        fd_50F6_10EA = 0;
    }
    if (fd_50F6_10E6) {
        db_ReleaseHandle(fd_50F6_10E6);
        fd_50F6_10E6 = 0;
    }
}

static int g_1A2E = -1;

extern int far fd_50F6_0F24;
extern char near g_5A97;
extern Handle far f_1A53_00BA(int object, int kind);
extern Handle far fd_50F6_37DE;
extern void far o00_31AD_18BA(char far *p, unsigned seg, int n);
extern void far o00_31AD_186A(char far *p, unsigned seg, int page, unsigned n);
extern void far db_PurgeObject(int object, int kind);
extern Handle far fd_50F6_10EE;
extern void far f_171C_1C0A(Handle h);
extern void far db_UnhookObject(int object, int kind);

void far f_0250_0256(int set)
{
    int i;

    if (g_1A2E == set)
        return;
    g_1A2E = set;
    fd_50F6_0F24 = set;
    if ((g_5A97 & 1) || g_5A97 == 2) {
        if (fd_50F6_10EE)
            f_171C_1C0A(fd_50F6_10EE);
        fd_50F6_10EE = f_1A53_00BA(10 - set, 9);
        db_UnhookObject(10 - set, 9);
    } else {
        if (g_19D0 == 0)
            f_0250_01E7();
        fd_50F6_37DE = f_1A53_00BA(10 - set, 9);
        o00_31AD_18BA(*fd_50F6_37DE, 0xa000, 0x100);
        for (i = 0; i < 4; i++)
            o00_31AD_186A(*fd_50F6_37DE + (i << 13), 0xc000, i, 0x2000);
        db_PurgeObject(10 - set, 9);
    }
}

extern int far fd_50F6_0480;

void far OverlayTileSet(int type, int id)
{
    if (type == 0) {
        if (id == 0x3e9) {
            f_0250_0256(1);
            fd_50F6_0480 = 0x90;
        } else if (id == 0x3e8) {
            f_0250_0256(0);
            fd_50F6_0480 = 0x50;
        }
    }
}

extern int far fd_50F6_1102;
extern Handle far f_1A53_00F0(int object, int kind, int type);
extern long far f_171C_1C1C(Handle h);
extern int far f_171C_1E9A(Handle h);
extern Handle far f_171C_13CA(long size, int flags, char far *name);
extern char far * far f_171C_1B84(Handle h);
extern void far * far _fmemcpy(void far *dest, void far *src, unsigned n);
extern void far f_195A_00F8(int handle);
extern void far f_195A_0122(int handle, int n, int far *map);
extern char far * far fd_55B3_360E;
extern void far f_195A_010D(int handle);
extern Handle far f_171C_1BBA(Handle h);

void far LoadTiles(void)
{
    int i;
    unsigned n;
    Handle h;
    char far *p;

    fd_50F6_10EA = 0;
    fd_50F6_10E6 = 0;
    fd_50F6_10EE = 0;
    f_0250_0256(0);
    switch (g_5A97) {
    case 0:
    case 8:
        f_0250_012D();
    case 4:
        fd_50F6_1102 = 1;
        if (g_19D0) {
            for (i = 0; i < 6; i++) {
                fd_50F6_10E6 = f_1A53_00F0(i + 15, 9, 1);
                n = f_171C_1C1C(fd_50F6_10E6);
                if (f_171C_1E9A(fd_50F6_10E6)) {
                    h = f_171C_13CA((long)n, 9, "emstiles");
                    p = f_171C_1B84(h);
                    _fmemcpy(p, f_171C_1B84(fd_50F6_10E6), n);
                } else {
                    h = 0;
                    p = f_171C_1B84(fd_50F6_10E6);
                }
                f_195A_00F8(g_19D0);
                f_195A_0122(g_19D0, 4, i < 3 ? g_19D2 : g_19E2);
                _fmemcpy(fd_55B3_360E + i % 3 * 0x5000, p, n);
                f_195A_010D(g_19D0);
                f_171C_1BBA(fd_50F6_10E6);
                if (h) {
                    f_171C_1BBA(h);
                    f_171C_1C0A(h);
                }
                db_PurgeObject(i + 15, 9);
            }
            fd_50F6_10E6 = 0;
        }
        break;
    case 2:
        g_19BE = g_19C0 = 12;
        fd_50F6_1102 = 2;
        break;
    case 3:
    case 5:
    case 7:
        fd_50F6_1102 = 3;
        break;
    }
}

extern void far * far _fmemset(void far *dest, int c, unsigned n);

void far f_0250_05CB(void)
{
    _fmemset(fd_50F6_15C4, -1, 0x960);
}

extern int far MapPlane;

void far f_0250_05EB(void)
{
    if (g_19D0) {
        f_195A_00F8(g_19D0);
        if (MapPlane < 2)
            f_195A_0122(g_19D0, 4, g_19D2);
        else
            f_195A_0122(g_19D0, 4, g_19E2);
    }
}

void far f_0250_062A(void)
{
    if (g_19D0)
        f_195A_010D(g_19D0);
}

void far f_0250_0643(int which)
{
    if (g_19D0 == 0) {
        if (which == 1) {
            if (fd_50F6_10EA) {
                db_ReleaseHandle(fd_50F6_10EA);
                fd_50F6_10EA = 0;
            }
            if (fd_50F6_10E6 == 0)
                fd_50F6_10E6 = f_1A53_00BA(13, 9);
        } else {
            if (fd_50F6_10E6) {
                db_ReleaseHandle(fd_50F6_10E6);
                fd_50F6_10E6 = 0;
            }
            if (fd_50F6_10EA == 0)
                fd_50F6_10EA = f_1A53_00BA(14, 9);
        }
    } else
        f_0250_05EB();
}

extern unsigned char near g_94E4;
extern void far Punt(char far *format, ...);
extern unsigned near g_9126;
extern void far o00_31AD_2FDA(int x, int y, int col, int row, char far *p);
extern void far o00_31AD_1B49(int x, int y, int col, int row, char far *p, int mask);
extern void far o00_31AD_300B(int x, int y, int col, int row, char far *p, int mask);
extern void far o03_3258_0690(int x, int y, char far *tile, char far *life, int mask);
extern void far o01_3126_1343(int x, int y, char far *tile, char far *life, int n);

void far f_0250_0721(int x, int y)
{
    static int masks[3] = { 0, 3, 1 };
    int row;
    int col;
    int flip;
    int mask;
    char far *base;

    row = g_94E4 >> 6;
    col = ((g_94E4 & 0x3f) - 0x80) << 7;
    if (g_94E4 >= 0x100)
        Punt("Tile >= 256 in PutLifeAndTile");
    if (g_9126 >= 0x380) {
        g_9126 -= 0x280;
        flip = 0;
    } else if (g_9126 >= 0x300) {
        g_9126 -= 0x200;
        flip = 1;
    } else if (g_9126 >= 0x200) {
        g_9126 -= 0x200;
        flip = 1;
    } else {
        g_9126 -= 0x100;
        flip = 0;
    }
    if (g_19D0 && fd_50F6_1102 == 1) {
        o00_31AD_2FDA(x & ~0xf, y, col, row, fd_55B3_360E + g_9126 * 0xa0);
        return;
    }
    base = *(flip == 1 ? fd_50F6_10E6 : fd_50F6_10EA);
    if (g_9126 >= 0xf0 && g_9126 <= 0xff)
        mask = masks[0];
    else
        mask = masks[g_9126 >> 7];
    if (fd_50F6_1102 == 1) {
        if (g_5A97 == 4)
            o00_31AD_1B49(x & ~0xf, y, col, row, base + (g_9126 & 0x7f) * 0xc0, mask);
        else
            o00_31AD_300B(x & ~0xf, y, col, row, base + (g_9126 & 0x7f) * 0xc0, mask);
    } else if (fd_50F6_1102 == 2)
        o03_3258_0690(x & ~1, y, *fd_50F6_10EE + g_94E4 * 0x48, base + (g_9126 & 0x7f) * 0x48, mask);
    else if (fd_50F6_1102 == 3)
        o01_3126_1343(x & ~7, y, *fd_50F6_10EE + (g_94E4 << 5), base + (g_9126 << 5), 0x3000 - ((g_9126 >> 7) << 12));
}

extern void far o00_31AD_2B1A(int col, int row, char far *p);
extern void far o00_31AD_1B7D(int col, int row, char far *p, int mask);
extern void far o00_31AD_303F(int col, int row, char far *p, int mask);
extern void far o03_3258_0F04(char far *tile, char far *life, int mask);
extern void far o01_3126_14B6(char far *tile, char far *life, int n);

void far f_0250_0915(void)
{
    static int masks[3] = { 0, 3, 1 };
    int row;
    int col;
    int flip;
    int mask;
    char far *base;

    row = g_94E4 >> 6;
    col = ((g_94E4 & 0x3f) - 0x80) << 7;
    if (g_94E4 >= 0x100)
        Punt("Tile >= 256 in PutLifeAndTile");
    if (g_9126 >= 0x380) {
        g_9126 -= 0x280;
        flip = 0;
    } else if (g_9126 >= 0x300) {
        g_9126 -= 0x200;
        flip = 1;
    } else if (g_9126 >= 0x200) {
        g_9126 -= 0x200;
        flip = 1;
    } else {
        g_9126 -= 0x100;
        flip = 0;
    }
    if (g_19D0 && fd_50F6_1102 == 1) {
        o00_31AD_2B1A(col, row, fd_55B3_360E + g_9126 * 0xa0);
        return;
    }
    base = *(flip == 1 ? fd_50F6_10E6 : fd_50F6_10EA);
    if (g_9126 >= 0xf0 && g_9126 <= 0xff)
        mask = masks[0];
    else
        mask = masks[g_9126 >> 7];
    if (fd_50F6_1102 == 1) {
        if (g_5A97 == 4)
            o00_31AD_1B7D(col, row, base + (g_9126 & 0x7f) * 0xc0, mask);
        else
            o00_31AD_303F(col, row, base + (g_9126 & 0x7f) * 0xc0, mask);
    } else if (fd_50F6_1102 == 2)
        o03_3258_0F04(*fd_50F6_10EE + g_94E4 * 0x48, base + (g_9126 & 0x7f) * 0x48, mask);
    else if (fd_50F6_1102 == 3)
        o01_3126_14B6(*fd_50F6_10EE + (g_94E4 << 5), base + (g_9126 << 5), 0x3000 - ((g_9126 >> 7) << 12));
}

extern void (far * near g_917C)(int x, int y, int offset);
extern void (far * near g_914C)(int x, int y, char far *p, int w, int h);

void far f_0250_0ADB(int x, int y)
{
    if (g_94E4 >= 0x100)
        Punt("PutTile grndTile > 0x100");
    switch (fd_50F6_1102) {
    case 1:
        (*g_917C)(x, y, (g_94E4 - 0x300) << 5);
        break;
    case 2:
        (*g_914C)(x & ~1, y, *fd_50F6_10EE + g_94E4 * 0x48, 12, 12);
        break;
    case 3:
        (*g_914C)(x & ~0xf, y, *fd_50F6_10EE + (g_94E4 << 5), 16, 16);
        break;
    }
}

extern void far o00_31AD_1A8F(int row, int col);
extern char near g_3D20[];

void far f_0250_0B86(void)
{
    switch (fd_50F6_1102) {
    case 1:
        o00_31AD_1A8F(g_94E4 >> 6, ((g_94E4 & 0x3f) - 0x80) << 7);
        break;
    case 2:
        _fmemcpy(g_3D20, *fd_50F6_10EE + g_94E4 * 0x48, 0x48);
        break;
    case 3:
        _fmemcpy(g_3D20, *fd_50F6_10EE + (g_94E4 << 5), 0x20);
        break;
    }
}

extern void far clip_SetWin(int win);
extern void far processEdit(struct Event far *event);
extern void far o04_35F5_075F(void);
extern void far DoWinHelp(int mode);
extern void far EditToolsMenu(void);
extern void far f_015B_053C(int plane);
extern void far f_015B_06A2(void);
extern void far f_015B_06F5(void);
extern void far GotoBQueen(void);
extern void far GotoRQueen(void);
extern int far fd_50F6_047E;
extern void far SetPause(int pause);
extern void far o05_35F5_0000(void);
extern void far o05_35F5_0684(struct Event far *event);
extern void far o05_35F5_0642(struct Event far *event);
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
        o04_35F5_075F();
        break;
    case 6:
        DoWinHelp(2);
        break;
    case 7:
        EditToolsMenu();
        break;
    case 8:
        f_015B_053C(1);
        break;
    case 9:
        f_015B_053C(2);
        break;
    case 10:
        f_015B_053C(3);
        break;
    case 11:
        f_015B_06A2();
        break;
    case 12:
        f_015B_06F5();
        break;
    case 13:
        GotoBQueen();
        break;
    case 14:
        GotoRQueen();
        break;
    case 15:
        SetPause(fd_50F6_047E == 0);
        break;
    case 16:
        o05_35F5_0000();
        break;
    case 17:
        o05_35F5_0684(event);
        break;
    case 18:
        o05_35F5_0642(event);
        break;
    }
    clip_Off();
}

int far f_0250_0D10(int a, int b);

void far f_0250_0CF6(int a, int b)
{
    f_0250_0D10(a, b);
}

typedef struct {
    int x;
    int y;
} Pnt;

void far f_0250_0F2C(void);
void far UpdateEdit(void);

struct Rect {
    int left;
    int top;
    int right;
    int bottom;
};

extern struct Rect far fd_50F6_110C;
extern void _fastcall win_GetObjRect(int obj, struct Rect far *rect);
extern Pnt far fd_50F6_0508;

int far f_0250_0D10(int dx, int dy)
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
            fd_50F6_0508.y += yStep;
            error += fraction;
            if ((error >> 16) & 1) {
                fd_50F6_0508.x += xStep;
                error ^= 0x10000L;
            }
        }
        f_0250_0F2C();
        UpdateEdit();
        return 1;
    } else {
        fraction = ((unsigned long)yDistance << 16) / xDistance;
        for (i = 0; i < xDistance; i++) {
            fd_50F6_0508.x += xStep;
            error += fraction;
            if ((error >> 16) & 1) {
                fd_50F6_0508.y += yStep;
                error ^= 0x10000L;
            }
        }
        f_0250_0F2C();
        UpdateEdit();
        return 1;
    }
}

void far f_0250_0E15(void)
{
    win_GetObjRect(4, &fd_50F6_110C);
    fd_50F6_10E0 = (fd_50F6_110C.right - fd_50F6_110C.left) / g_19BE;
    fd_50F6_10DE = (fd_50F6_110C.bottom - fd_50F6_110C.top) / g_19C0 + 1;
    f_0250_05CB();
    g_19CE = 1;
    f_0250_0F2C();
}

extern void far f_20E8_04B6(int win, ...);

void far OpenEditWindow(void)
{
    f_20E8_04B6(0);
}

void far ForceUpdateEdit(void)
{
    f_0250_05CB();
    UpdateEdit();
}

void far DoEditUpdateDraw(void)
{
    ForceUpdateEdit();
}

extern int _fastcall f_22BF_09B0(int win);
void far f_0250_13A6(void);
void far DrawEditGraphs(void);
void far f_0250_13A6(void);
void far DrawEditGraphs(void);

void far UpdateEdit(void)
{
    if (f_22BF_09B0(0)) {
        clip_SetWin(0);
        f_0250_13A6();
        DrawEditGraphs();
        clip_Off();
    }
}

void far f_0250_0EC6(void)
{
    UpdateEdit();
}

void far f_0250_0ED2(void)
{
}

extern int far fd_50F6_0EAC;
extern int far CurExpTool;
extern void _fastcall win_SetColorFromObjNum(int obj);
extern void _fastcall win_DrawBitMapAtObjNum(int obj, int id);

void far f_0250_0EDA(int flags)
{
    int id;

    if (flags & 2) {
        f_0250_0E15();
        f_0250_13A6();
        f_0250_0E15();
        if (fd_50F6_0EAC == 3)
            id = CurExpTool + 0x13ec;
        else
            id = 0x13f3;
        win_SetColorFromObjNum(7);
        win_DrawBitMapAtObjNum(7, id);
    }
}

void far f_0250_0F2C(void)
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
    if (fd_50F6_0508.x < 0)
        fd_50F6_0508.x = 0;
    else if (fd_50F6_0508.x + fd_50F6_10E0 > limit)
        fd_50F6_0508.x = limit - fd_50F6_10E0;
    if (fd_50F6_0508.y < 0)
        fd_50F6_0508.y = 0;
    else if (fd_50F6_0508.y + fd_50F6_10DE > ylimit)
        fd_50F6_0508.y = ylimit - fd_50F6_10DE;
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
    f_0250_0CF6(x - fd_50F6_10E0 / 2 - fd_50F6_0508.x, y - fd_50F6_10DE / 2 - fd_50F6_0508.y);
    f_0250_0F2C();
}

extern int far fd_3D57_07BE;
extern unsigned char far PherMapA[64][32];
extern unsigned char far PherMapBN[64][32];
extern unsigned char far PherMapBT[64][32];
extern unsigned char far PherMapRN[64][32];
extern unsigned char far PherMapRT[64][32];
extern unsigned char far MapA[128][64];
extern unsigned char far LifeA[128][64];
extern int far fd_50F6_049A;
extern int far fd_50F6_04C2;
extern int far fd_50F6_0502;
extern int far fd_50F6_0496;
extern unsigned char far MapB[64][64];
extern unsigned char far LifeB[64][64];
extern unsigned char far MapR[64][64];
extern unsigned char far LifeR[64][64];

/* OPEN (unclaimed draft, kept in place for CONST/_DATA order and identifier counts):
 * residue: the original keeps the tile value v in [bp-2] (memory) and mx/my in SI/DI with a
 * 4-byte frame; here v wins SI.  Taking &v reproduces the allocation (not adopted).  The
 * sums fd_049A+fd_04C2(+fd_0496) load in the original order only with one declaration
 * between fd_049A and fd_04C2 (mod-17 symbol order). */
extern void (far * far fd_50F6_37EA)(char far *src, char far *dst, int x, int y);

/* SCAFFOLD BEGIN: unclaimed f_0250_1018; retained whole-module context */
extern int far fd_50F6_03E0;
extern int far fd_50F6_046A;

void far f_0250_1018(int x, int y)
{
    int v;
    int mx;
    int my;

    mx = fd_50F6_0508.x + x;
    my = fd_50F6_0508.y + y;
    if (my > 0x3f) {
        mx += 0x40;
        my &= 0x3f;
    }
    g_94E4 = 0;
    g_9126 = 0;
    switch (MapPlane) {
    case 0:
    case 1:
        mx &= 0x7f;
        switch (fd_3D57_07BE) {
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
            g_94E4 = ((v >> 4) & 0x1f) - 0x10;
        else
            g_94E4 = 0;
noscent:
        if (g_94E4 == 0)
            g_94E4 = MapA[mx][my];
        v = LifeA[mx][my];
        if (v == 0)
            return;
        if (v == 0xff) {
            g_9126 = fd_50F6_049A + fd_50F6_04C2 + 0x380;
            if (fd_50F6_04C2 < 8)
                g_9126 += fd_50F6_0502;
            else
                g_9126 += fd_50F6_0496;
        } else if (v == 0xfe)
            g_9126 = fd_50F6_049A + fd_50F6_0496 + fd_50F6_04C2 + 0x388;
        else
            g_9126 = v + 0x100;
        break;
    case 2:
        mx &= 0x3f;
        g_94E4 = MapB[mx][my] - 0x70;
        v = LifeB[mx][my];
        if (v == 0)
            return;
        switch (v) {
        case 0xfe:
            g_9126 = fd_50F6_049A + fd_50F6_0496 + fd_50F6_04C2 + 0x308;
            break;
        case 0xff:
            g_9126 = fd_50F6_049A + fd_50F6_04C2 + 0x300;
            if (fd_50F6_04C2 < 8)
                g_9126 += fd_50F6_0502;
            else
                g_9126 += fd_50F6_0496;
            break;
        default:
            g_9126 = v + 0x200;
        }
        break;
    case 3:
        mx &= 0x3f;
        g_94E4 = MapR[mx][my] - 0x70;
        v = LifeR[mx][my];
        if (v == 0)
            return;
        switch (v) {
        case 0xfe:
            g_9126 = fd_50F6_049A + fd_50F6_0496 + fd_50F6_04C2 + 0x308;
            break;
        case 0xff:
            g_9126 = fd_50F6_049A + fd_50F6_04C2 + 0x300;
            if (fd_50F6_04C2 < 8)
                g_9126 += fd_50F6_0502;
            else
                g_9126 += fd_50F6_0496;
            break;
        default:
            g_9126 = v + 0x200;
        }
        break;
    }
}
/* SCAFFOLD END */

extern unsigned char far fd_50F6_1114[30 * 40];

/* OPEN: residue 2 extra frame words ([bp-2],[bp-4]) and SI/DI swapped (y param in DI,
 * index in SI in the original). */
/* SCAFFOLD BEGIN: unclaimed f_0250_129E; retained whole-module context */
void far f_0250_129E(int x, int y)
{
    int ay;
    int i;
    int far *p;

    ay = fd_50F6_0508.y + y;
    if (x < 0 || y < 0 || x >= 40 || y >= 30)
        return;
    if (ay > 0x3f)
        Punt("Y>MAXAY");
    f_0250_1018(x, y);
    i = y * 40 + x;
    if (fd_50F6_15C4[0][i] == -2) {
        fd_50F6_15C4[0][i]++;
        return;
    }
    p = &fd_50F6_15C4[0][i];
    if (*p != g_9126 || fd_50F6_1114[i] != g_94E4 || (y == 0 && g_19CE != 0)) {
        if (g_9126)
            f_0250_0721(g_19BE * x + fd_50F6_110C.left, g_19C0 * y + fd_50F6_110C.top);
        else
            f_0250_0ADB(g_19BE * x + fd_50F6_110C.left, y * g_19C0 + fd_50F6_110C.top);
        *p = g_9126;
        fd_50F6_1114[i] = g_94E4;
    }
}
/* SCAFFOLD END */

extern void far clip_Push(void);
void far f_0250_5058(void);
extern long far TickCount(void);
extern void _fastcall f_21FA_00EE(int color);
extern void far f_15D9_0006(char far *msg, struct Rect far *rect, int y);
void far PreDrawSpider(void);
void far PreDrawBalloons(void);
extern int far fd_50F6_37D2;
void far DrawSpider(void);
void far DrawBalloons(void);
extern int far fd_50F6_37D4;
extern void far f_1B4E_003B(int x, int y, char far *image);
extern Pnt far fd_50F6_1F26;
extern struct Rect far fd_50F6_37D6;

static struct Rect balTileRect;
static struct Rect balloonRect;
static Handle balBufHandle;
static Pnt edPenPos;
static char far *balBufPtr;

extern void far clip_Pop(void);

/* px and py are never read: their stepping keeps the dead loads of editRect.left/top (and of
 * g_19C0) alive.  The px step constant is not decided by the bytes (px += 16 is a hypothesis;
 * px++ compiles identically).  balloon = spider = 0 stores spider first (worker resG). */
void far f_0250_13A6(void)
{
    int spider;
    int balloon;
    int x;
    int y;
    int px;
    int py;

    balloon = spider = 0;
    clip_Push();
    f_0250_5058();
    if (g_19C6) {
        if (TickCount() > g_19CA) {
            if (g_19C6)
                g_19CE = 1;
            g_19C6 = 0;
        } else {
            f_21FA_00EE(3);
            f_15D9_0006(g_19C6, &fd_50F6_110C, fd_50F6_110C.top + 4);
        }
    }
    PreDrawSpider();
    PreDrawBalloons();
    if (fd_50F6_37D2 != 500)
        DrawSpider();
    DrawBalloons();
    f_0250_0643(MapPlane / 2);
    py = fd_50F6_110C.top;
    for (y = 0; y < fd_50F6_10DE; y++, py += g_19C0) {
        px = fd_50F6_110C.left;
        for (x = 0; x < fd_50F6_10E0; x++, px += 16) {
            if (x >= balTileRect.left && x < balTileRect.right && y >= balTileRect.top && y < balTileRect.bottom)
                goto drawballoon;
            if ((y >= fd_50F6_37D4 && y < fd_50F6_37D4 + 7 && x >= fd_50F6_37D2 && x < fd_50F6_37D2 + 7)
                || (y == fd_50F6_10DE - 1 && x == fd_50F6_10E0 - 1)) {
                if (spider)
                    continue;
                f_1B4E_003B(fd_50F6_37D6.left, fd_50F6_37D6.top, (char far *)&fd_50F6_1F26);
                spider = 1;
                if (balTileRect.left == 500)
                    continue;
            drawballoon:
                if (balloon)
                    continue;
                f_1B4E_003B(balloonRect.left, balloonRect.top, balBufPtr);
                balloon = 1;
                continue;
            }
            f_0250_129E(x, y);
        }
    }
    f_0250_062A();
    if (balTileRect.left != 500) {
        f_171C_1BBA(balBufHandle);
        f_171C_1C0A(balBufHandle);
    }
    clip_Pop();
    g_19CE = 0;
}

extern int far fd_50F6_0F78;
extern int far fd_50F6_10BE;
extern int far fd_50F6_01FE;
extern int near g_3DE0;
extern void far f_1CE2_046D(struct Rect far *rect, int color);
extern void (far * near g_9128)(int a, int b, int c);
extern void far f_1CE2_044D(struct Rect far *rect, int width);
extern int near g_3DE2;
extern int far fd_50F6_0FBA;
extern int far f_1B4E_000D(int color);
extern int far fd_50F6_0FFE;
extern void far f_1CE2_0430(struct Rect far *rect);

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

    vals[0] = &fd_50F6_0F78; vals[1] = &fd_50F6_10BE; vals[2] = &fd_50F6_01FE;
    for (i = 0; i < 3; i++) {
        obj = objs[i];
        frac = ((long)*vals[i] << 16) / 100;
        win_SetColorFromObjNum(obj);
        win_GetObjRect(obj, &r);
        h = r.bottom - r.top;
        top = r.top;
        r.top = r.bottom - (int)(h * frac / 0x10000L);
        if (r.top < r.bottom) {
            f_1CE2_046D(&r, g_3DE0);
            if ((g_5A97 & 1) && i == 0) {
                (*g_9128)(0, 0, 0);
                f_1CE2_044D(&r, 1);
                win_SetColorFromObjNum(obj);
            }
        }
        if (r.top > top) {
            r.bottom = r.top;
            r.top = top;
            f_1CE2_046D(&r, g_3DE2);
        }
        if (i == 0) {
            r.top = (100 - fd_50F6_0FBA) * h / 100 + top;
            r.bottom = r.top + 1;
            f_1CE2_046D(&r, f_1B4E_000D(15));
        }
        if (i == 1) {
            r.top = (100 - fd_50F6_0FFE) * h / 100 + top;
            r.bottom = r.top + 1;
            f_1CE2_0430(&r);
        }
    }
}

extern char far * far _fstrcpy(char far *dest, char far *src);
extern char far * far * far fd_50F6_0368;
extern char far * far _fstrcat(char far *dest, char far *src);
extern char far * far * far fd_50F6_0324;
extern void far f_22BF_059A(int obj, char far *text);
extern void _fastcall f_21FA_0AA7(int obj);

void far SetEditWinTitle(void)
{
    char buf[80];

    _fstrcpy(buf, "SimAnt");
    _fstrcat(buf, fd_50F6_0368[15]);
    _fstrcat(buf, fd_50F6_0324[fd_50F6_0EAC]);
    f_22BF_059A(1, buf);
    if (f_22BF_09B0(0)) {
        clip_Push();
        clip_SetWin(0);
        f_21FA_0AA7(1);
        clip_Pop();
    }
}

extern int far fd_50F6_0F0C;
extern int far fd_50F6_0F12;
extern int far fd_50F6_0F34;

void far PreDrawSpider(void)
{
    int x, y, px, py;
    int sx, sy;

    fd_50F6_37D6.top = 0x8000;
    fd_50F6_37D2 = 500;
    fd_50F6_37D4 = 500;
    if (!fd_50F6_0F0C)
        return;
    y = fd_50F6_0508.y;
    x = fd_50F6_0508.x;
    px = x * g_19BE;
    py = y * g_19C0;
    sx = fd_50F6_0F12;
    sy = fd_50F6_0F34;
    if (g_5A97 == 2) {
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
    fd_50F6_1F26.x = 7 * g_19BE;
    fd_50F6_1F26.y = 7 * g_19C0;
    fd_50F6_37D2 = fd_50F6_0F12 / 16 - x - 3;
    fd_50F6_37D4 = fd_50F6_0F34 / 16 - y - 3;
}

void far DrawEditGraphs(void);
extern void far f_2662_1120(int x, int y, Pnt far *buf, int id);
void far DrawLegs(int x, int y, int dir, int frame);
void far DrawPalps(int x, int y, int dir);
extern void (far * far fd_50F6_37E6)(char far *p, int stride);
extern void far f_16B5_0033(Pnt far *buf, int mode);
extern int far SMode;
extern int far Scycle;
extern char far fd_3D57_09CC[];
extern char far fd_3D57_09D0[];
extern int far fd_50F6_1004;
extern char far fd_3D57_09BC[];
extern char far fd_3D57_09C4[];
extern int far fd_3D57_07B2;
extern long far fd_3D57_098E;
extern int far SRand64(void);
extern int far SRand2(void);
extern int far fd_50F6_0D6E;
extern int far fd_3D57_0992;
extern int far fd_50F6_0EB4;
extern char far * far * far fd_50F6_10B4;
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

    px = fd_50F6_0508.x * g_19BE;
    py = fd_50F6_0508.y * g_19C0;
    if (g_5A97 == 2) {
        sx = fd_50F6_0F12 * 3 / 4;
        modx = sx % 12;
        mody = (fd_50F6_0F34 * 3 / 4) % 12;
        left = sx - modx + fd_50F6_110C.left - px - 0x24;
        top = fd_50F6_0F34 * 3 / 4 - mody + fd_50F6_110C.top - py - 0x24;
    } else {
        modx = fd_50F6_0F12 & 0xf;
        mody = fd_50F6_0F34 & 0xf;
        left = fd_50F6_0F12 - modx + fd_50F6_110C.left - px - 0x30;
        top = fd_50F6_0F34 - mody + fd_50F6_110C.top - py - 0x30;
    }
    fd_50F6_37D6.left = left;
    fd_50F6_37D6.top = top;
    fd_50F6_37D6.bottom = top + fd_50F6_1F26.y;
    fd_50F6_37D6.right = left + fd_50F6_1F26.x;
    f_0250_0643(MapPlane / 2);
    w = 2;
    switch (fd_50F6_1102) {
    case 2:
        w = 6;
    case 1:
        skip = 2;
        break;
    case 3:
        skip = 8;
        break;
    }
    skip = g_19C0 / skip * fd_50F6_1F26.x - w * 7;
    p = (char far *)&fd_50F6_1F26 + 4;
    for (j = 0, ty = fd_50F6_37D4; j < 7; j++, ty++, p += skip) {
        int tx;
        int n;
        int idx;

        for (idx = ty * 40 + (tx = fd_50F6_37D2), n = 0; n < 7; n++, tx++, p += w, idx++) {
            f_0250_1018(tx, ty);
            if (idx >= 0 && idx < 1200)
                fd_50F6_15C4[0][idx] = -1;
            if (g_9126)
                f_0250_0915();
            else
                f_0250_0B86();
            (*fd_50F6_37E6)(p, fd_50F6_1F26.x);
        }
    }
    f_0250_062A();
    (g_5A97 & 1) ? f_16B5_0033(&fd_50F6_1F26, 0) : (g_5A97 == 2 ? f_16B5_0033(&fd_50F6_1F26, 1) : f_16B5_0033(&fd_50F6_1F26, 2));
    if (SMode == 5) {
        lx = fd_3D57_09CC[Scycle] + 0x30;
        ly = fd_3D57_09D0[Scycle] + 0x30;
        if (g_5A97 == 2) {
            lx = lx * 3 / 4 + modx;
            ly = ly * 3 / 4 + mody;
        } else {
            lx += modx;
            ly += mody;
        }
        f_2662_1120(lx, ly, &fd_50F6_1F26, Scycle + 0x41a);
    } else {
        lx = fd_3D57_09BC[fd_50F6_1004] + 0x30;
        ly = fd_3D57_09C4[fd_50F6_1004] + 0x30;
        if (g_5A97 == 2) {
            f_2662_1120(lx = lx * 3 / 4 + modx, ly = ly * 3 / 4 + mody, &fd_50F6_1F26, fd_50F6_1004 + 1000);
            DrawLegs((modx + 0x24) * 4 / 3, (mody + 0x24) * 4 / 3, fd_50F6_1004, Scycle & 7);
            DrawPalps((modx + 0x24) * 4 / 3, (mody + 0x24) * 4 / 3, fd_50F6_1004);
        } else {
            f_2662_1120(modx + lx, mody + ly, &fd_50F6_1F26, fd_50F6_1004 + 1000);
            DrawLegs(modx + 0x30, mody + 0x30, fd_50F6_1004, Scycle & 7);
            DrawPalps(modx + 0x30, mody + 0x30, fd_50F6_1004);
        }
    }
    if (fd_3D57_07B2) {
        if (fd_50F6_047E == 0 && fd_3D57_098E < TickCount()) {
            fd_3D57_098E = TickCount() + SRand64() + 180;
            if (SRand2() == 0) {
                fd_50F6_0D6E = 1;
                if (++fd_3D57_0992 >= 5)
                    fd_3D57_0992 = 0;
            } else
                fd_50F6_0D6E = 0;
        }
        if (SMode == fd_50F6_0EB4 && SMode <= 4) {
            if (fd_50F6_0D6E)
                AddMsgBalloon((Dx8[fd_50F6_1004] << 3) + fd_50F6_0F12, (Dy8[fd_50F6_1004] << 3) + fd_50F6_0F34, 1, 10,
                              fd_50F6_10B4[SMode * 5 + fd_3D57_0992]);
        } else {
            fd_3D57_098E = TickCount() + SRand32() + 30;
            fd_50F6_0D6E = 0;
            fd_50F6_0EB4 = SMode;
        }
    }
}

extern void (far * near g_9134)(int x0, int y0, int x1, int y1, int color);
extern int far fd_3D57_0C30;
extern int far fd_3D57_0C28;
extern int far fd_50F6_0470;
extern int far fd_50F6_047A;

/* OPEN: residue commutative operand order MapPnt.x + EditColumns (original loads the
 * MapPnt member first) - structural, not changed by names or preceding declaration counts. */
void far f_0250_1E80(void)
{
    int x;
    int y;
    int t;

    if (fd_50F6_0508.x + fd_50F6_10E0 >= fd_50F6_03E0 && fd_50F6_03E0 + 15 >= fd_50F6_0508.x
        && fd_50F6_0508.y + fd_50F6_10DE >= fd_50F6_046A && fd_50F6_046A + 15 >= fd_50F6_0508.y) {
        x = (fd_50F6_03E0 - fd_50F6_0508.x) * g_19BE + fd_50F6_110C.left;
        y = (fd_50F6_046A - fd_50F6_0508.y) * g_19C0 + fd_50F6_110C.top;
        (*g_9134)(x, y, 15 * g_19BE + x, 15 * g_19C0 + y, g_19C4 | 0x10);
        x = fd_50F6_03E0 - fd_50F6_0508.x;
        y = fd_50F6_046A - fd_50F6_0508.y;
        if (fd_3D57_0C30 & 1)
            InvalEuMap(x, y, x + 16, y + 6);
        else
            InvalEuMap(x, y, x + 6, y + 16);
        if (fd_3D57_0C28 == 3 || fd_3D57_0C28 == 4) {
            if (fd_50F6_0508.x + fd_50F6_10E0 >= fd_50F6_0470 && fd_50F6_0470 + 0x1b >= fd_50F6_0508.x
                && fd_50F6_0508.y + fd_50F6_10DE >= fd_50F6_047A && fd_50F6_047A + 0x1b >= fd_50F6_0508.x) {
                x = (fd_50F6_0470 - fd_50F6_0508.x) * g_19BE + fd_50F6_110C.left;
                y = (fd_50F6_047A - fd_50F6_0508.y) * g_19C0 + fd_50F6_110C.top;
                (*g_9134)(x, y, 15 * g_19BE + x, 15 * g_19C0 + y, g_19C4 | 0x20);
                x = fd_50F6_0470 - fd_50F6_0508.x;
                y = fd_50F6_047A - fd_50F6_0508.y;
                InvalEuMap(x, y, x + 0x1b, y + 0x1b);
            }
        }
    }
}

void far ed_MoveTo(int x, int y)
{
    if (g_5A97 == 2) {
        x = x * 3 / 4;
        y = y * 3 / 4;
    }
    edPenPos.x = x;
    edPenPos.y = y;
}

extern void far f_16B5_0008(int x0, int y0, int x1, int y1, int color);

void far ed_LineTo(int x, int y)
{
    if (g_5A97 == 2) {
        x = x * 3 / 4;
        y = y * 3 / 4;
    }
    f_16B5_0008(edPenPos.x, edPenPos.y, x, y, g_3DE0);
    edPenPos.x = x;
    edPenPos.y = y;
}

extern int far fd_50F6_06AC;
extern int far SRand1(int range);
extern int far fd_50F6_0A06;
extern char far fd_3D57_09E8[4];
extern char far fd_3D57_09E4[4];
extern char far fd_3D57_09F0[4];
extern char far fd_3D57_09EC[4];
extern char far fd_3D57_09F8[4];
extern char far fd_3D57_09F4[4];
extern char far fd_3D57_0A00[4];
extern char far fd_3D57_09FC[4];
void far DrawPalps(int x, int y, int dir)
{
    int r;

    if (SMode <= 1 && fd_50F6_06AC < 6)
        r = 0;
    else
        r = SRand1(4);
    if (fd_50F6_0A06 == 1)
        (*g_9128)(f_1B4E_000D(1), 0, 0);
    else
        (*g_9128)(f_1B4E_000D(15), 0, 0);
    switch (dir) {
    case 0:
        ed_MoveTo(x + 4, y - 10);
        ed_LineTo(x + fd_3D57_09E4[r], y + fd_3D57_09E8[r]);
        ed_LineTo(x + fd_3D57_09EC[r], y + fd_3D57_09F0[r]);
        ed_MoveTo(x - 4, y - 10);
        ed_LineTo(x - fd_3D57_09E4[r], y + fd_3D57_09E8[r]);
        ed_LineTo(x - fd_3D57_09EC[r], y + fd_3D57_09F0[r]);
        break;
    case 1:
        ed_MoveTo(x + 10, y - 3);
        ed_LineTo(x + fd_3D57_09F4[r], y + fd_3D57_09F8[r]);
        ed_LineTo(x + fd_3D57_09FC[r], y + fd_3D57_0A00[r]);
        ed_MoveTo(x + 3, y - 10);
        ed_LineTo(x - fd_3D57_09F8[r], y - fd_3D57_09F4[r]);
        ed_LineTo(x - fd_3D57_0A00[r], y - fd_3D57_09FC[r]);
        break;
    case 2:
        ed_MoveTo(x + 10, y - 4);
        ed_LineTo(x - fd_3D57_09E8[r], y - fd_3D57_09E4[r]);
        ed_LineTo(x - fd_3D57_09F0[r], y - fd_3D57_09EC[r]);
        ed_MoveTo(x + 10, y + 4);
        ed_LineTo(x - fd_3D57_09E8[r], y + fd_3D57_09E4[r]);
        ed_LineTo(x - fd_3D57_09F0[r], y + fd_3D57_09EC[r]);
        break;
    case 3:
        ed_MoveTo(x + 10, y + 3);
        ed_LineTo(x + fd_3D57_09F4[r], y - fd_3D57_09F8[r]);
        ed_LineTo(x + fd_3D57_09FC[r], y - fd_3D57_0A00[r]);
        ed_MoveTo(x + 3, y + 10);
        ed_LineTo(x - fd_3D57_09F8[r], y + fd_3D57_09F4[r]);
        ed_LineTo(x - fd_3D57_0A00[r], y + fd_3D57_09FC[r]);
        break;
    case 4:
        ed_MoveTo(x + 4, y + 10);
        ed_LineTo(x + fd_3D57_09E4[r], y - fd_3D57_09E8[r]);
        ed_LineTo(x + fd_3D57_09EC[r], y - fd_3D57_09F0[r]);
        ed_MoveTo(x - 4, y + 10);
        ed_LineTo(x - fd_3D57_09E4[r], y - fd_3D57_09E8[r]);
        ed_LineTo(x - fd_3D57_09EC[r], y - fd_3D57_09F0[r]);
        break;
    case 5:
        ed_MoveTo(x - 10, y + 3);
        ed_LineTo(x - fd_3D57_09F4[r], y - fd_3D57_09F8[r]);
        ed_LineTo(x - fd_3D57_09FC[r], y - fd_3D57_0A00[r]);
        ed_MoveTo(x - 3, y + 10);
        ed_LineTo(x + fd_3D57_09F8[r], y + fd_3D57_09F4[r]);
        ed_LineTo(x + fd_3D57_0A00[r], y + fd_3D57_09FC[r]);
        break;
    case 6:
        ed_MoveTo(x - 10, y - 4);
        ed_LineTo(x + fd_3D57_09E8[r], y - fd_3D57_09E4[r]);
        ed_LineTo(x + fd_3D57_09F0[r], y - fd_3D57_09EC[r]);
        ed_MoveTo(x - 10, y + 4);
        ed_LineTo(x + fd_3D57_09E8[r], y + fd_3D57_09E4[r]);
        ed_LineTo(x + fd_3D57_09F0[r], y + fd_3D57_09EC[r]);
        break;
    case 7:
        ed_MoveTo(x - 10, y - 3);
        ed_LineTo(x - fd_3D57_09F4[r], y + fd_3D57_09F8[r]);
        ed_LineTo(x - fd_3D57_09FC[r], y + fd_3D57_0A00[r]);
        ed_MoveTo(x - 3, y - 10);
        ed_LineTo(x + fd_3D57_09F8[r], y - fd_3D57_09F4[r]);
        ed_LineTo(x + fd_3D57_0A00[r], y - fd_3D57_09FC[r]);
        break;
    }
}

extern char far fd_3D57_0A08[4];
extern char far fd_3D57_0A04[4];
extern char far fd_3D57_0A4C[8];
extern char far fd_3D57_0A0C[8];
extern char far fd_3D57_0A54[8];
extern char far fd_3D57_0A14[8];
extern char far fd_3D57_0A5C[8];
extern char far fd_3D57_0A1C[8];
extern char far fd_3D57_0A64[8];
extern char far fd_3D57_0A24[8];
extern char far fd_3D57_0A6C[8];
extern char far fd_3D57_0A2C[8];
extern char far fd_3D57_0A74[8];
extern char far fd_3D57_0A34[8];
extern char far fd_3D57_0A7C[8];
extern char far fd_3D57_0A3C[8];
extern char far fd_3D57_0A84[8];
extern char far fd_3D57_0A44[8];
extern char far fd_3D57_0A90[4];
extern char far fd_3D57_0A8C[4];
extern char far fd_3D57_0A9C[8];
extern char far fd_3D57_0A94[8];
extern char far fd_3D57_0ADC[8];
extern char far fd_3D57_0AD4[8];
extern char far fd_3D57_0AAC[8];
extern char far fd_3D57_0AA4[8];
extern char far fd_3D57_0AEC[8];
extern char far fd_3D57_0AE4[8];
extern char far fd_3D57_0ABC[8];
extern char far fd_3D57_0AB4[8];
extern char far fd_3D57_0AFC[8];
extern char far fd_3D57_0AF4[8];
extern char far fd_3D57_0ACC[8];
extern char far fd_3D57_0AC4[8];
extern char far fd_3D57_0B0C[8];
extern char far fd_3D57_0B04[8];
void far DrawLegs(int x, int y, int dir, int frame)
{
    int other;

    other = (frame + 4) & 7;
    (*g_9128)(f_1B4E_000D(15), 0, 0);
    switch (dir) {
    case 0:
        ed_MoveTo(x + fd_3D57_0A04[0], y + fd_3D57_0A08[0]);
        ed_LineTo(x + fd_3D57_0A0C[frame], y + fd_3D57_0A4C[frame]);
        ed_LineTo(x + fd_3D57_0A14[frame], y + fd_3D57_0A54[frame]);
        ed_MoveTo(x + fd_3D57_0A04[1], y + fd_3D57_0A08[1]);
        ed_LineTo(x + fd_3D57_0A1C[frame], y + fd_3D57_0A5C[frame]);
        ed_LineTo(x + fd_3D57_0A24[frame], y + fd_3D57_0A64[frame]);
        ed_MoveTo(x + fd_3D57_0A04[2], y + fd_3D57_0A08[2]);
        ed_LineTo(x + fd_3D57_0A2C[frame], y + fd_3D57_0A6C[frame]);
        ed_LineTo(x + fd_3D57_0A34[frame], y + fd_3D57_0A74[frame]);
        ed_MoveTo(x + fd_3D57_0A04[3], y + fd_3D57_0A08[3]);
        ed_LineTo(x + fd_3D57_0A3C[frame], y + fd_3D57_0A7C[frame]);
        ed_LineTo(x + fd_3D57_0A44[frame], y + fd_3D57_0A84[frame]);
        ed_MoveTo(x - fd_3D57_0A04[0], y + fd_3D57_0A08[0]);
        ed_LineTo(x - fd_3D57_0A0C[other], y + fd_3D57_0A4C[other]);
        ed_LineTo(x - fd_3D57_0A14[other], y + fd_3D57_0A54[other]);
        ed_MoveTo(x - fd_3D57_0A04[1], y + fd_3D57_0A08[1]);
        ed_LineTo(x - fd_3D57_0A1C[other], y + fd_3D57_0A5C[other]);
        ed_LineTo(x - fd_3D57_0A24[other], y + fd_3D57_0A64[other]);
        ed_MoveTo(x - fd_3D57_0A04[2], y + fd_3D57_0A08[2]);
        ed_LineTo(x - fd_3D57_0A2C[other], y + fd_3D57_0A6C[other]);
        ed_LineTo(x - fd_3D57_0A34[other], y + fd_3D57_0A74[other]);
        ed_MoveTo(x - fd_3D57_0A04[3], y + fd_3D57_0A08[3]);
        ed_LineTo(x - fd_3D57_0A3C[other], y + fd_3D57_0A7C[other]);
        ed_LineTo(x - fd_3D57_0A44[other], y + fd_3D57_0A84[other]);
        break;
    case 1:
        ed_MoveTo(x + fd_3D57_0A8C[0], y + fd_3D57_0A90[0]);
        ed_LineTo(x + fd_3D57_0A94[frame], y + fd_3D57_0A9C[frame]);
        ed_LineTo(x + fd_3D57_0AD4[frame], y + fd_3D57_0ADC[frame]);
        ed_MoveTo(x + fd_3D57_0A8C[1], y + fd_3D57_0A90[1]);
        ed_LineTo(x + fd_3D57_0AA4[frame], y + fd_3D57_0AAC[frame]);
        ed_LineTo(x + fd_3D57_0AE4[frame], y + fd_3D57_0AEC[frame]);
        ed_MoveTo(x + fd_3D57_0A8C[2], y + fd_3D57_0A90[2]);
        ed_LineTo(x + fd_3D57_0AB4[frame], y + fd_3D57_0ABC[frame]);
        ed_LineTo(x + fd_3D57_0AF4[frame], y + fd_3D57_0AFC[frame]);
        ed_MoveTo(x + fd_3D57_0A8C[3], y + fd_3D57_0A90[3]);
        ed_LineTo(x + fd_3D57_0AC4[frame], y + fd_3D57_0ACC[frame]);
        ed_LineTo(x + fd_3D57_0B04[frame], y + fd_3D57_0B0C[frame]);
        ed_MoveTo(x - fd_3D57_0A90[0], y - fd_3D57_0A8C[0]);
        ed_LineTo(x - fd_3D57_0A9C[other], y - fd_3D57_0A94[other]);
        ed_LineTo(x - fd_3D57_0ADC[other], y - fd_3D57_0AD4[other]);
        ed_MoveTo(x - fd_3D57_0A90[1], y - fd_3D57_0A8C[1]);
        ed_LineTo(x - fd_3D57_0AAC[other], y - fd_3D57_0AA4[other]);
        ed_LineTo(x - fd_3D57_0AEC[other], y - fd_3D57_0AE4[other]);
        ed_MoveTo(x - fd_3D57_0A90[2], y - fd_3D57_0A8C[2]);
        ed_LineTo(x - fd_3D57_0ABC[other], y - fd_3D57_0AB4[other]);
        ed_LineTo(x - fd_3D57_0AFC[other], y - fd_3D57_0AF4[other]);
        ed_MoveTo(x - fd_3D57_0A90[3], y - fd_3D57_0A8C[3]);
        ed_LineTo(x - fd_3D57_0ACC[other], y - fd_3D57_0AC4[other]);
        ed_LineTo(x - fd_3D57_0B0C[other], y - fd_3D57_0B04[other]);
        break;
    case 2:
        ed_MoveTo(x - fd_3D57_0A08[0], y + fd_3D57_0A04[0]);
        ed_LineTo(x - fd_3D57_0A4C[frame], y + fd_3D57_0A0C[frame]);
        ed_LineTo(x - fd_3D57_0A54[frame], y + fd_3D57_0A14[frame]);
        ed_MoveTo(x - fd_3D57_0A08[1], y + fd_3D57_0A04[1]);
        ed_LineTo(x - fd_3D57_0A5C[frame], y + fd_3D57_0A1C[frame]);
        ed_LineTo(x - fd_3D57_0A64[frame], y + fd_3D57_0A24[frame]);
        ed_MoveTo(x - fd_3D57_0A08[2], y + fd_3D57_0A04[2]);
        ed_LineTo(x - fd_3D57_0A6C[frame], y + fd_3D57_0A2C[frame]);
        ed_LineTo(x - fd_3D57_0A74[frame], y + fd_3D57_0A34[frame]);
        ed_MoveTo(x - fd_3D57_0A08[3], y + fd_3D57_0A04[3]);
        ed_LineTo(x - fd_3D57_0A7C[frame], y + fd_3D57_0A3C[frame]);
        ed_LineTo(x - fd_3D57_0A84[frame], y + fd_3D57_0A44[frame]);
        ed_MoveTo(x - fd_3D57_0A08[0], y - fd_3D57_0A04[0]);
        ed_LineTo(x - fd_3D57_0A4C[other], y - fd_3D57_0A0C[other]);
        ed_LineTo(x - fd_3D57_0A54[other], y - fd_3D57_0A14[other]);
        ed_MoveTo(x - fd_3D57_0A08[1], y - fd_3D57_0A04[1]);
        ed_LineTo(x - fd_3D57_0A5C[other], y - fd_3D57_0A1C[other]);
        ed_LineTo(x - fd_3D57_0A64[other], y - fd_3D57_0A24[other]);
        ed_MoveTo(x - fd_3D57_0A08[2], y - fd_3D57_0A04[2]);
        ed_LineTo(x - fd_3D57_0A6C[other], y - fd_3D57_0A2C[other]);
        ed_LineTo(x - fd_3D57_0A74[other], y - fd_3D57_0A34[other]);
        ed_MoveTo(x - fd_3D57_0A08[3], y - fd_3D57_0A04[3]);
        ed_LineTo(x - fd_3D57_0A7C[other], y - fd_3D57_0A3C[other]);
        ed_LineTo(x - fd_3D57_0A84[other], y - fd_3D57_0A44[other]);
        break;
    case 3:
        ed_MoveTo(x + fd_3D57_0A8C[0], y - fd_3D57_0A90[0]);
        ed_LineTo(x + fd_3D57_0A94[frame], y - fd_3D57_0A9C[frame]);
        ed_LineTo(x + fd_3D57_0AD4[frame], y - fd_3D57_0ADC[frame]);
        ed_MoveTo(x + fd_3D57_0A8C[1], y - fd_3D57_0A90[1]);
        ed_LineTo(x + fd_3D57_0AA4[frame], y - fd_3D57_0AAC[frame]);
        ed_LineTo(x + fd_3D57_0AE4[frame], y - fd_3D57_0AEC[frame]);
        ed_MoveTo(x + fd_3D57_0A8C[2], y - fd_3D57_0A90[2]);
        ed_LineTo(x + fd_3D57_0AB4[frame], y - fd_3D57_0ABC[frame]);
        ed_LineTo(x + fd_3D57_0AF4[frame], y - fd_3D57_0AFC[frame]);
        ed_MoveTo(x + fd_3D57_0A8C[3], y - fd_3D57_0A90[3]);
        ed_LineTo(x + fd_3D57_0AC4[frame], y - fd_3D57_0ACC[frame]);
        ed_LineTo(x + fd_3D57_0B04[frame], y - fd_3D57_0B0C[frame]);
        ed_MoveTo(x - fd_3D57_0A90[0], y + fd_3D57_0A8C[0]);
        ed_LineTo(x - fd_3D57_0A9C[other], y + fd_3D57_0A94[other]);
        ed_LineTo(x - fd_3D57_0ADC[other], y + fd_3D57_0AD4[other]);
        ed_MoveTo(x - fd_3D57_0A90[1], y + fd_3D57_0A8C[1]);
        ed_LineTo(x - fd_3D57_0AAC[other], y + fd_3D57_0AA4[other]);
        ed_LineTo(x - fd_3D57_0AEC[other], y + fd_3D57_0AE4[other]);
        ed_MoveTo(x - fd_3D57_0A90[2], y + fd_3D57_0A8C[2]);
        ed_LineTo(x - fd_3D57_0ABC[other], y + fd_3D57_0AB4[other]);
        ed_LineTo(x - fd_3D57_0AFC[other], y + fd_3D57_0AF4[other]);
        ed_MoveTo(x - fd_3D57_0A90[3], y + fd_3D57_0A8C[3]);
        ed_LineTo(x - fd_3D57_0ACC[other], y + fd_3D57_0AC4[other]);
        ed_LineTo(x - fd_3D57_0B0C[other], y + fd_3D57_0B04[other]);
        break;
    case 4:
        ed_MoveTo(x - fd_3D57_0A04[0], y - fd_3D57_0A08[0]);
        ed_LineTo(x - fd_3D57_0A0C[frame], y - fd_3D57_0A4C[frame]);
        ed_LineTo(x - fd_3D57_0A14[frame], y - fd_3D57_0A54[frame]);
        ed_MoveTo(x - fd_3D57_0A04[1], y - fd_3D57_0A08[1]);
        ed_LineTo(x - fd_3D57_0A1C[frame], y - fd_3D57_0A5C[frame]);
        ed_LineTo(x - fd_3D57_0A24[frame], y - fd_3D57_0A64[frame]);
        ed_MoveTo(x - fd_3D57_0A04[2], y - fd_3D57_0A08[2]);
        ed_LineTo(x - fd_3D57_0A2C[frame], y - fd_3D57_0A6C[frame]);
        ed_LineTo(x - fd_3D57_0A34[frame], y - fd_3D57_0A74[frame]);
        ed_MoveTo(x - fd_3D57_0A04[3], y - fd_3D57_0A08[3]);
        ed_LineTo(x - fd_3D57_0A3C[frame], y - fd_3D57_0A7C[frame]);
        ed_LineTo(x - fd_3D57_0A44[frame], y - fd_3D57_0A84[frame]);
        ed_MoveTo(x + fd_3D57_0A04[0], y - fd_3D57_0A08[0]);
        ed_LineTo(x + fd_3D57_0A0C[other], y - fd_3D57_0A4C[other]);
        ed_LineTo(x + fd_3D57_0A14[other], y - fd_3D57_0A54[other]);
        ed_MoveTo(x + fd_3D57_0A04[1], y - fd_3D57_0A08[1]);
        ed_LineTo(x + fd_3D57_0A1C[other], y - fd_3D57_0A5C[other]);
        ed_LineTo(x + fd_3D57_0A24[other], y - fd_3D57_0A64[other]);
        ed_MoveTo(x + fd_3D57_0A04[2], y - fd_3D57_0A08[2]);
        ed_LineTo(x + fd_3D57_0A2C[other], y - fd_3D57_0A6C[other]);
        ed_LineTo(x + fd_3D57_0A34[other], y - fd_3D57_0A74[other]);
        ed_MoveTo(x + fd_3D57_0A04[3], y - fd_3D57_0A08[3]);
        ed_LineTo(x + fd_3D57_0A3C[other], y - fd_3D57_0A7C[other]);
        ed_LineTo(x + fd_3D57_0A44[other], y - fd_3D57_0A84[other]);
        break;
    case 5:
        ed_MoveTo(x - fd_3D57_0A8C[0], y - fd_3D57_0A90[0]);
        ed_LineTo(x - fd_3D57_0A94[frame], y - fd_3D57_0A9C[frame]);
        ed_LineTo(x - fd_3D57_0AD4[frame], y - fd_3D57_0ADC[frame]);
        ed_MoveTo(x - fd_3D57_0A8C[1], y - fd_3D57_0A90[1]);
        ed_LineTo(x - fd_3D57_0AA4[frame], y - fd_3D57_0AAC[frame]);
        ed_LineTo(x - fd_3D57_0AE4[frame], y - fd_3D57_0AEC[frame]);
        ed_MoveTo(x - fd_3D57_0A8C[2], y - fd_3D57_0A90[2]);
        ed_LineTo(x - fd_3D57_0AB4[frame], y - fd_3D57_0ABC[frame]);
        ed_LineTo(x - fd_3D57_0AF4[frame], y - fd_3D57_0AFC[frame]);
        ed_MoveTo(x - fd_3D57_0A8C[3], y - fd_3D57_0A90[3]);
        ed_LineTo(x - fd_3D57_0AC4[frame], y - fd_3D57_0ACC[frame]);
        ed_LineTo(x - fd_3D57_0B04[frame], y - fd_3D57_0B0C[frame]);
        ed_MoveTo(x + fd_3D57_0A90[0], y + fd_3D57_0A8C[0]);
        ed_LineTo(x + fd_3D57_0A9C[other], y + fd_3D57_0A94[other]);
        ed_LineTo(x + fd_3D57_0ADC[other], y + fd_3D57_0AD4[other]);
        ed_MoveTo(x + fd_3D57_0A90[1], y + fd_3D57_0A8C[1]);
        ed_LineTo(x + fd_3D57_0AAC[other], y + fd_3D57_0AA4[other]);
        ed_LineTo(x + fd_3D57_0AEC[other], y + fd_3D57_0AE4[other]);
        ed_MoveTo(x + fd_3D57_0A90[2], y + fd_3D57_0A8C[2]);
        ed_LineTo(x + fd_3D57_0ABC[other], y + fd_3D57_0AB4[other]);
        ed_LineTo(x + fd_3D57_0AFC[other], y + fd_3D57_0AF4[other]);
        ed_MoveTo(x + fd_3D57_0A90[3], y + fd_3D57_0A8C[3]);
        ed_LineTo(x + fd_3D57_0ACC[other], y + fd_3D57_0AC4[other]);
        ed_LineTo(x + fd_3D57_0B0C[other], y + fd_3D57_0B04[other]);
        break;
    case 6:
        ed_MoveTo(x + fd_3D57_0A08[0], y - fd_3D57_0A04[0]);
        ed_LineTo(x + fd_3D57_0A4C[frame], y - fd_3D57_0A0C[frame]);
        ed_LineTo(x + fd_3D57_0A54[frame], y - fd_3D57_0A14[frame]);
        ed_MoveTo(x + fd_3D57_0A08[1], y - fd_3D57_0A04[1]);
        ed_LineTo(x + fd_3D57_0A5C[frame], y - fd_3D57_0A1C[frame]);
        ed_LineTo(x + fd_3D57_0A64[frame], y - fd_3D57_0A24[frame]);
        ed_MoveTo(x + fd_3D57_0A08[2], y - fd_3D57_0A04[2]);
        ed_LineTo(x + fd_3D57_0A6C[frame], y - fd_3D57_0A2C[frame]);
        ed_LineTo(x + fd_3D57_0A74[frame], y - fd_3D57_0A34[frame]);
        ed_MoveTo(x + fd_3D57_0A08[3], y - fd_3D57_0A04[3]);
        ed_LineTo(x + fd_3D57_0A7C[frame], y - fd_3D57_0A3C[frame]);
        ed_LineTo(x + fd_3D57_0A84[frame], y - fd_3D57_0A44[frame]);
        ed_MoveTo(x + fd_3D57_0A08[0], y + fd_3D57_0A04[0]);
        ed_LineTo(x + fd_3D57_0A4C[other], y + fd_3D57_0A0C[other]);
        ed_LineTo(x + fd_3D57_0A54[other], y + fd_3D57_0A14[other]);
        ed_MoveTo(x + fd_3D57_0A08[1], y + fd_3D57_0A04[1]);
        ed_LineTo(x + fd_3D57_0A5C[other], y + fd_3D57_0A1C[other]);
        ed_LineTo(x + fd_3D57_0A64[other], y + fd_3D57_0A24[other]);
        ed_MoveTo(x + fd_3D57_0A08[2], y + fd_3D57_0A04[2]);
        ed_LineTo(x + fd_3D57_0A6C[other], y + fd_3D57_0A2C[other]);
        ed_LineTo(x + fd_3D57_0A74[other], y + fd_3D57_0A34[other]);
        ed_MoveTo(x + fd_3D57_0A08[3], y + fd_3D57_0A04[3]);
        ed_LineTo(x + fd_3D57_0A7C[other], y + fd_3D57_0A3C[other]);
        ed_LineTo(x + fd_3D57_0A84[other], y + fd_3D57_0A44[other]);
        break;
    case 7:
        ed_MoveTo(x - fd_3D57_0A8C[0], y + fd_3D57_0A90[0]);
        ed_LineTo(x - fd_3D57_0A94[frame], y + fd_3D57_0A9C[frame]);
        ed_LineTo(x - fd_3D57_0AD4[frame], y + fd_3D57_0ADC[frame]);
        ed_MoveTo(x - fd_3D57_0A8C[1], y + fd_3D57_0A90[1]);
        ed_LineTo(x - fd_3D57_0AA4[frame], y + fd_3D57_0AAC[frame]);
        ed_LineTo(x - fd_3D57_0AE4[frame], y + fd_3D57_0AEC[frame]);
        ed_MoveTo(x - fd_3D57_0A8C[2], y + fd_3D57_0A90[2]);
        ed_LineTo(x - fd_3D57_0AB4[frame], y + fd_3D57_0ABC[frame]);
        ed_LineTo(x - fd_3D57_0AF4[frame], y + fd_3D57_0AFC[frame]);
        ed_MoveTo(x - fd_3D57_0A8C[3], y + fd_3D57_0A90[3]);
        ed_LineTo(x - fd_3D57_0AC4[frame], y + fd_3D57_0ACC[frame]);
        ed_LineTo(x - fd_3D57_0B04[frame], y + fd_3D57_0B0C[frame]);
        ed_MoveTo(x + fd_3D57_0A90[0], y - fd_3D57_0A8C[0]);
        ed_LineTo(x + fd_3D57_0A9C[other], y - fd_3D57_0A94[other]);
        ed_LineTo(x + fd_3D57_0ADC[other], y - fd_3D57_0AD4[other]);
        ed_MoveTo(x + fd_3D57_0A90[1], y - fd_3D57_0A8C[1]);
        ed_LineTo(x + fd_3D57_0AAC[other], y - fd_3D57_0AA4[other]);
        ed_LineTo(x + fd_3D57_0AEC[other], y - fd_3D57_0AE4[other]);
        ed_MoveTo(x + fd_3D57_0A90[2], y - fd_3D57_0A8C[2]);
        ed_LineTo(x + fd_3D57_0ABC[other], y - fd_3D57_0AB4[other]);
        ed_LineTo(x + fd_3D57_0AFC[other], y - fd_3D57_0AF4[other]);
        ed_MoveTo(x + fd_3D57_0A90[3], y - fd_3D57_0A8C[3]);
        ed_LineTo(x + fd_3D57_0ACC[other], y - fd_3D57_0AC4[other]);
        ed_LineTo(x + fd_3D57_0B0C[other], y - fd_3D57_0B04[other]);
        break;
    }
}

void far f_0250_41CA(void)
{
    InvalEuMap((fd_50F6_0F12 - fd_50F6_0508.x * g_19BE) / g_19BE - 3,
                (fd_50F6_0F34 - fd_50F6_0508.y * g_19C0) / g_19C0 - 3,
                (fd_50F6_0F12 - fd_50F6_0508.x * g_19BE) / g_19BE + 3,
                (fd_50F6_0F34 - fd_50F6_0508.y * g_19C0) / g_19C0 + 3);
}

/* OPEN: residue as f_0250_1E80: original keeps MapPnt.x in AX after the compare and adds
 * EditColumns; this compiles to load EditColumns then add the [bp-2] CSE temp. */
int far BalloonIsVisible(int plane, int x, int y)
{
    if (plane != MapPlane)
        return 0;
    if (x < fd_50F6_0508.x || x >= fd_50F6_0508.x + fd_50F6_10E0)
        return 0;
    if (y - 3 < fd_50F6_0508.y || y >= fd_50F6_0508.y + fd_50F6_10DE)
        return 0;
    return 1;
}

extern int far fd_50F6_0EF6;
extern Pnt far fd_50F6_08DE;
extern int far fd_50F6_0AD8;
extern Pnt far fd_50F6_0852;
extern int far fd_50F6_0ACA;

void far EggBalloons(int x, int y, int plane)
{
    if (fd_50F6_0EF6 != 0)
        return;
    if (!BalloonIsVisible(plane, x, y))
        return;
    if (fd_50F6_08DE.x == x && fd_50F6_08DE.y == y && fd_50F6_0AD8 == plane) {
        fd_50F6_0EF6++;
        return;
    }
    fd_50F6_0852.x = x;
    fd_50F6_0852.y = y;
    fd_50F6_0ACA = plane;
}

extern int far fd_50F6_0F06;
extern Pnt far fd_50F6_09F2;
extern int far fd_50F6_0B06;
extern Pnt far fd_50F6_08EC;
extern int far fd_50F6_0AEA;

void far FightBalloons(int x, int y, int plane)
{
    if (fd_50F6_0F06 != 0)
        return;
    if (!BalloonIsVisible(plane, x, y))
        return;
    if (fd_50F6_09F2.x == x && fd_50F6_09F2.y == y && fd_50F6_0B06 == plane) {
        fd_50F6_0F06++;
        return;
    }
    fd_50F6_08EC.x = x;
    fd_50F6_08EC.y = y;
    fd_50F6_0AEA = plane;
}

extern int far fd_50F6_0F10;
extern Pnt far fd_50F6_0A8A;
extern int far fd_50F6_0C3A;
extern Pnt far fd_50F6_0A02;
extern int far fd_50F6_0B08;

void far QueenBalloons(int x, int y, int plane)
{
    if (fd_50F6_0F10 != 0)
        return;
    if (!BalloonIsVisible(plane, x, y))
        return;
    if (fd_50F6_0A8A.x == x && fd_50F6_0A8A.y == y && fd_50F6_0C3A == plane) {
        fd_50F6_0F10++;
        return;
    }
    fd_50F6_0A02.x = x;
    fd_50F6_0A02.y = y;
    fd_50F6_0B08 = plane;
}

extern int far fd_50F6_0F2E;
extern Pnt far fd_50F6_0AB2;
extern int far fd_50F6_0D9A;
extern Pnt far fd_50F6_0AA2;
extern int far fd_50F6_0D68;

void far RestBalloons(int x, int y, int plane)
{
    if (fd_50F6_0F2E != 0)
        return;
    if (!BalloonIsVisible(plane, x, y))
        return;
    if (fd_50F6_0AB2.x == x && fd_50F6_0AB2.y == y && fd_50F6_0D9A == plane) {
        fd_50F6_0F2E++;
        return;
    }
    fd_50F6_0AA2.x = x;
    fd_50F6_0AA2.y = y;
    fd_50F6_0D68 = plane;
}

extern int far fd_50F6_1092;
extern Pnt far fd_50F6_04C8[];
extern int far fd_50F6_04F6[];
extern int far fd_50F6_04E6[];
extern char far * far fd_50F6_04A6[];

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
    if (fd_50F6_1092 >= 6)
        return;
    if (!BalloonIsVisible(plane, tx, ty))
        return;
    fd_50F6_04C8[fd_50F6_1092].x = style == 10 ? x : g_19BE * x + 8;
    fd_50F6_04C8[fd_50F6_1092].y = style == 10 ? y : g_19C0 * y + 8;
    fd_50F6_04F6[fd_50F6_1092] = plane;
    fd_50F6_04E6[fd_50F6_1092] = style;
    fd_50F6_04A6[fd_50F6_1092] = msg;
    fd_50F6_1092++;
}

extern int far fd_50F6_1046;
extern int far fd_50F6_0F3C;
extern char far * far * far fd_50F6_020A;
extern int far fd_50F6_1064;
extern int far fd_50F6_0FF8;
extern char far * far * far fd_50F6_0218;
extern int far fd_50F6_104A;
extern long far fd_50F6_050C;
extern long far fd_50F6_0732;
extern long far fd_50F6_059A;
extern long far fd_50F6_0620;
extern int far SRand4(void);
extern int far fd_50F6_0F7A;
extern char far * far * far fd_50F6_021C;
extern int far fd_50F6_1062;
extern int far fd_50F6_0FC0;
extern char far * far * far fd_50F6_0234;
extern int far fd_50F6_107C;
extern int far fd_50F6_103A;
extern char far * far * far fd_50F6_023A;
extern void far f_24AB_02AD(int font);
extern Handle far f_1629_000C(char far *msg, int flags);
extern long far fd_50F6_07C4;
extern Handle far f_171C_1A9E(long size, int flags, char far *name);
extern void (far * far fd_50F6_37EE)(void far *a, void far *b, void far *c, void far *d);

/* OPEN: residue only the operand order of the five TickCount() vs long-timer compares
 * (original: cmp mem,dx / cmp mem,ax).  A declaration order of the timer externs was found
 * that fixes all five in a different DrawSpider state; it is count-coupled with DrawSpider. */
void far DrawCurBalloons(void)
{
    if (!fd_3D57_07B2 || fd_3D57_07BE != -1)
        return;
    if (fd_50F6_0F06 == 0 && fd_50F6_08EC.x >= 0 && fd_50F6_08EC.y >= 0) {
        fd_50F6_09F2 = fd_50F6_08EC;
        fd_50F6_0B06 = fd_50F6_0AEA;
        fd_50F6_0F06++;
        fd_50F6_0732 = 0;
        fd_50F6_050C = 0;
    }
    if (fd_50F6_0F06 > 0) {
        if (fd_50F6_047E == 0) {
            if (fd_50F6_050C < TickCount()) {
                fd_50F6_050C = TickCount() + SRand32() + 60;
                if (SRand2() == 0) {
                    fd_50F6_1046 = 1;
                    if (fd_50F6_020A[++fd_50F6_0F3C] == 0)
                        fd_50F6_0F3C = 0;
                } else
                    fd_50F6_1046 = 0;
            }
            if (fd_50F6_0732 < TickCount()) {
                fd_50F6_0732 = TickCount() + SRand32() + 60;
                if (SRand2() == 0) {
                    fd_50F6_1064 = 1;
                    if (fd_50F6_0218[++fd_50F6_0FF8] == 0)
                        fd_50F6_0FF8 = 0;
                } else
                    fd_50F6_1064 = 0;
            }
        }
        if (fd_50F6_1046)
            AddMsgBalloon(fd_50F6_09F2.x, fd_50F6_09F2.y, fd_50F6_0B06, 0, fd_50F6_020A[fd_50F6_0F3C]);
        if (fd_50F6_1064)
            AddMsgBalloon(fd_50F6_09F2.x, fd_50F6_09F2.y, fd_50F6_0B06, 1, fd_50F6_0218[fd_50F6_0FF8]);
    }
    if (fd_50F6_0EF6 == 0 && fd_50F6_0852.x >= 0 && fd_50F6_0852.y >= 0) {
        fd_50F6_08DE = fd_50F6_0852;
        fd_50F6_0AD8 = fd_50F6_0ACA;
        fd_50F6_0EF6++;
        fd_50F6_059A = 0;
        fd_50F6_104A = 0;
    }
    if (fd_50F6_0EF6 > 0) {
        if (fd_50F6_047E == 0 && fd_50F6_059A < TickCount()) {
            fd_50F6_059A = TickCount() + SRand32() + 170;
            if (SRand4() == 0) {
                fd_50F6_104A = 1;
                if (fd_50F6_021C[++fd_50F6_0F7A] == 0)
                    fd_50F6_0F7A = 0;
            } else
                fd_50F6_104A = 0;
        }
        if (fd_50F6_104A)
            AddMsgBalloon(fd_50F6_08DE.x, fd_50F6_08DE.y, fd_50F6_0AD8, 2, fd_50F6_021C[fd_50F6_0F7A]);
    }
    if (fd_50F6_0F10 == 0 && fd_50F6_0A02.x >= 0 && fd_50F6_0A02.y >= 0) {
        fd_50F6_0A8A = fd_50F6_0A02;
        fd_50F6_0C3A = fd_50F6_0B08;
        fd_50F6_0F10++;
        fd_50F6_0620 = 0;
        fd_50F6_1062 = 0;
    }
    if (fd_50F6_0F10 > 0) {
        if (fd_50F6_047E == 0 && fd_50F6_0620 < TickCount()) {
            fd_50F6_0620 = TickCount() + SRand32() + 180;
            if (SRand4() == 0) {
                fd_50F6_1062 = 1;
                if (fd_50F6_0234[++fd_50F6_0FC0] == 0)
                    fd_50F6_0FC0 = 0;
            } else
                fd_50F6_1062 = 0;
        }
        if (fd_50F6_1062)
            AddMsgBalloon(fd_50F6_0A8A.x, fd_50F6_0A8A.y, fd_50F6_0C3A, 2, fd_50F6_0234[fd_50F6_0FC0]);
    }
    if (fd_50F6_0F2E == 0 && fd_50F6_0AA2.x >= 0 && fd_50F6_0AA2.y >= 0) {
        fd_50F6_0AB2 = fd_50F6_0AA2;
        fd_50F6_0D9A = fd_50F6_0D68;
        fd_50F6_0F2E++;
        fd_50F6_07C4 = 0;
        fd_50F6_107C = 0;
    }
    if (fd_50F6_0F2E > 0) {
        if (fd_50F6_047E == 0 && fd_50F6_07C4 < TickCount()) {
            fd_50F6_07C4 = TickCount() + SRand64() + 120;
            if (SRand2() == 0) {
                fd_50F6_107C = 1;
                if (fd_50F6_023A[++fd_50F6_103A] == 0)
                    fd_50F6_103A = 0;
            } else
                fd_50F6_107C = 0;
        }
        if (fd_50F6_107C)
            AddMsgBalloon(fd_50F6_0AB2.x, fd_50F6_0AB2.y, fd_50F6_0D9A, 2, fd_50F6_023A[fd_50F6_103A]);
    }
}

void far EditMsgBalloon(int x, int y, int plane, int style, char far *msg)
{
    char line1[256];
    char line2[256];

    if (BalloonIsVisible(plane, (x >> 4) + fd_50F6_0508.x, (y >> 4) + fd_50F6_0508.y) && msg != 0) {
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

    f_24AB_02AD(2);
    bpp = 2;
    rowbytes = 0x80;
    switch (fd_50F6_1102) {
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
        f_0250_5058();
    balTileRect.left = 500;
    for (i = 0, shown = 0; i < fd_50F6_1092; i++) {
        if (shown >= 1 || fd_50F6_04A6[i] == 0)
            break;
        pos = fd_50F6_04C8[i];
        if (!BalloonIsVisible(fd_50F6_04F6[i], pos.x / g_19BE, pos.y / g_19C0))
            continue;
        WinPrintf("Vis message %s at %d,%d", fd_50F6_04A6[i], pos.x, pos.y);
        shown++;
        hs[i] = h = f_1629_000C(fd_50F6_04A6[i], 0);
        pic = (int far *)f_171C_1B84(h);
        by = pos.y - pic[5] - 4;
        bx = pos.x + 4;
        wt = (bx % g_19BE + pic[4] + g_19BE - 1) / g_19BE;
        ht = (by % g_19C0 + pic[5] + g_19C0 - 1) / g_19C0;
        balTileRect.top = by / g_19C0 - fd_50F6_0508.y;
        balTileRect.left = bx / g_19BE - fd_50F6_0508.x;
        balTileRect.bottom = ht + balTileRect.top;
        balTileRect.right = balTileRect.left + wt;
        wpix = g_19BE * wt;
        balBufHandle = f_171C_1A9E((long)(ht * wt * rowbytes + 4), 9, "balbuf");
        balBufPtr = f_171C_1B84(balBufHandle);
        bufp = balBufPtr;
        ((int far *)bufp)[0] = g_19BE * wt;
        ((int far *)bufp)[1] = g_19C0 * ht;
        skip = g_19C0 / div * ((int far *)bufp)[0] - wt * bpp;
        dst = bufp + 4;
        _fmemset(dst, 0, ht * wt * rowbytes);
        balloonRect.left = g_19BE * balTileRect.left + fd_50F6_110C.left;
        balloonRect.top = g_19C0 * balTileRect.top + fd_50F6_110C.top;
        balloonRect.bottom = balloonRect.top + ((int far *)bufp)[1];
        balloonRect.right = balloonRect.left + ((int far *)bufp)[0];
        f_0250_0643(MapPlane / 2);
        saved = i;
        for (row = 0, ty = balTileRect.top; row < ht; row++, ty++, dst += skip) {
            idx = ty * 40 + balTileRect.left;
            for (tx = balTileRect.left, col = 0; col < wt; col++, tx++, dst += bpp, idx++) {
                f_0250_1018(tx, ty);
                if (g_9126)
                    f_0250_0915();
                else
                    f_0250_0B86();
                (*fd_50F6_37E6)(dst, wpix);
                if (idx >= 0 && idx < 1200)
                    fd_50F6_15C4[0][idx] = -1;
            }
        }
        f_0250_062A();
        if (fd_50F6_37D2 != 500)
            (*fd_50F6_37EE)(&fd_50F6_37D6, &fd_50F6_1F26, &balloonRect, bufp);
        (*fd_50F6_37EA)((char far *)pic + 8, bufp, bx % g_19BE, by % g_19C0);
        if (fd_50F6_37D2 != 500)
            (*fd_50F6_37EE)(&balloonRect, bufp, &fd_50F6_37D6, &fd_50F6_1F26);
        f_171C_1BBA(h);
        f_171C_1C0A(h);
        i = saved;
    }
    f_24AB_02AD(0);
    fd_50F6_1092 = 0;
}

extern struct Rect far fd_50F6_1104;
extern void far f_1E57_08F5(struct Rect far *rects);

void far f_0250_5058(void)
{
    struct Rect rects[3];

    win_GetObjRect(0x15, &fd_50F6_1104);
    rects[0] = fd_50F6_110C;
    rects[1] = fd_50F6_1104;
    rects[2].top = 0x8000;
    f_1E57_08F5(rects);
}
