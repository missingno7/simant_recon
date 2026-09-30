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

extern int far f_00F8_03AD(int plane, int x, int y);
extern int far fd_50F6_10E0;
extern int far fd_50F6_10DE;
extern int far fd_50F6_15C4[30][40];

int g_19BE = 16;
int g_19C0 = 16;
int g_19C2 = 13;
int g_19C4 = 7;
int g_19C6 = 0;
int g_19C8 = 0;
int g_19CA = 0;
int g_19CC = 0;
int g_19CE = 1;
int g_19D0 = 0;
int g_19D2[8] = { 0, 0, 1, 1, 2, 2, 3, 3 };
int g_19E2[8] = { 4, 0, 5, 1, 6, 2, 7, 3 };

void far f_0250_000E(int plane, int x, int y)
{
    int h;
    int v;

    if (f_00F8_03AD(plane, x, y) == 1) {
        h = x;
        if (h >= 0 && h < fd_50F6_10E0) {
            v = y;
            if (v >= 0 && v < fd_50F6_10DE)
                fd_50F6_15C4[v][h] = -1;
        }
    }
}

void far f_0250_006E(int left, int top, int right, int bottom)
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

void far f_0250_036A(int type, int id)
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

void far f_0250_03B6(void)
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

extern int far fd_50F6_032E;

void far f_0250_05EB(void)
{
    if (g_19D0) {
        f_195A_00F8(g_19D0);
        if (fd_50F6_032E < 2)
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

extern void far f_1E57_0174(int win);
extern void far processEdit(struct Event far *event);
extern void far o04_35F5_075F(void);
extern void far DoWinHelp(int mode);
extern void far EditToolsMenu(void);
extern void far f_015B_053C(int plane);
extern void far f_015B_06A2(void);
extern void far f_015B_06F5(void);
extern void far f_015B_073E(void);
extern void far f_015B_075F(void);
extern int far fd_50F6_047E;
extern void far o11_35F5_009E(int pause);
extern void far o05_35F5_0000(void);
extern void far o05_35F5_0684(struct Event far *event);
extern void far o05_35F5_0642(struct Event far *event);
extern void far f_1E57_0362(void);

void far f_0250_0C0F(struct Event far *event)
{
    f_1E57_0174(0);
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
        f_015B_073E();
        break;
    case 14:
        f_015B_075F();
        break;
    case 15:
        o11_35F5_009E(fd_50F6_047E == 0);
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
    f_1E57_0362();
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

extern Pnt far fd_50F6_0508;
void far f_0250_0F2C(void);
void far f_0250_0E9D(void);
void far f_0250_0F2C(void);
void far f_0250_0E9D(void);

struct Rect {
    int left;
    int top;
    int right;
    int bottom;
};

extern struct Rect far fd_50F6_110C;
extern void _fastcall win_GetObjRect(int obj, struct Rect far *rect);

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
        f_0250_0E9D();
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
        f_0250_0E9D();
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

void far f_0250_0E70(void)
{
    f_20E8_04B6(0);
}

void far f_0250_0E81(void)
{
    f_0250_05CB();
    f_0250_0E9D();
}

void far f_0250_0E91(void)
{
    f_0250_0E81();
}

extern int _fastcall f_22BF_09B0(int win);
void far f_0250_13A6(void);
void far f_0250_1583(void);
void far f_0250_13A6(void);
void far f_0250_1583(void);

void far f_0250_0E9D(void)
{
    if (f_22BF_09B0(0)) {
        f_1E57_0174(0);
        f_0250_13A6();
        f_0250_1583();
        f_1E57_0362();
    }
}

void far f_0250_0EC6(void)
{
    f_0250_0E9D();
}

void far f_0250_0ED2(void)
{
}

extern int far fd_50F6_0EAC;
extern int far fd_50F6_104C;
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
            id = fd_50F6_104C + 0x13ec;
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
    switch (fd_50F6_032E) {
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

void far f_0250_0FC4(int x, int y)
{
    int width;

    switch (fd_50F6_032E) {
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
extern unsigned char far fd_3E1D_D09F[64][32];
extern unsigned char far fd_3E1D_E09F[64][32];
extern unsigned char far fd_3E1D_E89F[64][32];
extern unsigned char far fd_3E1D_F09F[64][32];
extern unsigned char far fd_4DA7_0000[64][32];
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
    switch (fd_50F6_032E) {
    case 0:
    case 1:
        mx &= 0x7f;
        switch (fd_3D57_07BE) {
        case 0:
            v = fd_3E1D_D09F[mx >> 1][my >> 1];
            break;
        case 1:
            v = fd_3E1D_E09F[mx >> 1][my >> 1];
            break;
        case 2:
            v = fd_3E1D_E89F[mx >> 1][my >> 1];
            break;
        case 3:
            v = fd_3E1D_F09F[mx >> 1][my >> 1];
            break;
        case 4:
            v = fd_4DA7_0000[mx >> 1][my >> 1];
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

extern unsigned char far fd_50F6_1114[30 * 40];

void far f_0250_129E(int x, int y)
{
    int ay;
    int i;

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
    if (fd_50F6_15C4[0][i] != g_9126 || fd_50F6_1114[i] != g_94E4 || (y == 0 && g_19CE != 0)) {
        if (g_9126)
            f_0250_0721(g_19BE * x + fd_50F6_110C.left, g_19C0 * y + fd_50F6_110C.top);
        else
            f_0250_0ADB(g_19BE * x + fd_50F6_110C.left, y * g_19C0 + fd_50F6_110C.top);
        fd_50F6_15C4[0][i] = g_9126;
        fd_50F6_1114[i] = g_94E4;
    }
}

/* SCAFFOLD BEGIN: context only, not reconstruction */
void far f_0250_13A6(void) { }
void far f_0250_1583(void) { }
/* SCAFFOLD END */
