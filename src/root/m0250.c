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

void far f_0250_0D10(int a, int b);

void far f_0250_0CF6(int a, int b)
{
    f_0250_0D10(a, b);
}

/* SCAFFOLD BEGIN: context only, not reconstruction */
void far f_0250_0D10(int a, int b) { }
/* SCAFFOLD END */
