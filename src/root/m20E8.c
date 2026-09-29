/* Root module 20E8: window loading and window-stack operations. */

struct Rect {
    int left;
    int top;
    int right;
    int bottom;
};

void far f_20E8_0000(void);

void (far *g_62E0)(int win) = f_20E8_0000;
void (far *g_62E4)(void) = f_20E8_0000;
void (far *g_62E8)(void) = f_20E8_0000;
void (far *g_62EC)(void) = f_20E8_0000;
void (far *g_62F0)(void) = f_20E8_0000;
void (far *g_62F4)(int win) = f_20E8_0000;
int g_62F8 = 0;
int g_62FA = -1;
int g_62FC = 0;
int g_62FE = 0;
int g_6300 = 0;

void far f_20E8_0000(void)
{
}

/* SCAFFOLD BEGIN: f_20E8_0001 (win_LoadWindow) best draft.
   Residue: case 4 of the object loop computes the _fmemset pointer with
   mov ax,bx; mov dx,es; add ax,2Ah - the original reuses DX (obj segment
   from the objs[i] load): mov ax,bx; add ax,2Ah; push dx. 322 vs 320 bytes. */
extern char far * far * far f_1A53_00F0(int object, int kind, int type);
extern void far Punt(char far *format, ...);
extern char far * far * near g_9230[];
extern void _fastcall f_23AE_0377(int win);
extern void _fastcall f_2505_0048(int win);
extern struct Rect far fd_50F6_4892[];
extern void _fastcall f_23AE_01DB(int win);

void far f_20E8_0001(int win)
{
    char far * far *h;
    char far *obj;
    int i;
    char far *w;

    h = f_1A53_00F0((char)(win >> 8), 0, 1);
    if (h == 0)
        Punt("CANNOT LOAD WINDOW %03x", win);
    g_9230[(char)(win >> 8)] = h;
    w = *h;
    f_23AE_0377(win);
    f_2505_0048(win);
    obj = ((char far * far *)(w + 0x2c))[0];
    if (fd_50F6_4892[(char)(win >> 8)].left != (int)0x8000)
        *(struct Rect far *)(obj + 8) = fd_50F6_4892[(char)(win >> 8)];
    else
        fd_50F6_4892[(char)(win >> 8)] = *(struct Rect far *)(obj + 8);
    for (i = 0; i < *(int far *)(w + 0xc); i++) {
        obj = ((char far * far *)(w + 0x2c))[i];
        if (i == 0)
            *(struct Rect far *)w = *(struct Rect far *)obj;
        switch (obj[0x21]) {
        case 4:
            _fmemset(obj + 0x2a, 0, 14);
            break;
        case 16:
        case 17:
        case 18:
            *(char far * far *)(obj + 0x2a) = 0;
            break;
        }
    }
    f_23AE_01DB(win);
}

/* SCAFFOLD END */

struct Rect g_635C = { (int)0x8000, (int)0x8000, (int)0x8000, (int)0x8000 };

extern void far font_InitFonts(void);
extern void far f_23AE_0022(void);
extern void (far * far fd_50F6_47DE[])(int phase);
extern char near g_5A97;
extern char far * far * far db_LoadObject(int object, int kind);
extern char far * far f_171C_1B84(char far * far *handle);
extern void far f_171C_1BBA(char far * far *handle);
extern void far db_PurgeObject(int object, int kind);
struct Pt {
    int x;
    int y;
};
extern void far f_208F_0419(struct Pt far *size, int id);
extern struct Pt far fd_50F6_47DA;
extern int far fd_50F6_47D8;
extern int far fd_50F6_47D6;
extern int far fd_50F6_47D4;
extern char far fd_50F6_46E2[][6];
extern void far f_1A53_034F(int object, int kind);

int far f_20E8_0141(void)
{
    char purge[0x28];
    int i;
    char far * far *h;
    int far *p;
    char far *q;

    font_InitFonts();
    f_23AE_0022();
    _fmemset(fd_50F6_47DE, 0, 0xb4);
    for (i = 0; i < 45; i++)
        fd_50F6_4892[i] = g_635C;
    h = db_LoadObject(g_5A97, 9);
    if (h) {
        _fmemcpy(fd_50F6_4892, f_171C_1B84(h), 0x140);
        f_171C_1BBA(h);
        db_PurgeObject(g_5A97, 9);
    }
    f_208F_0419(&fd_50F6_47DA, 0x6f);
    h = db_LoadObject(0x80, 0);
    if (h == 0) {
        Punt("Cannot load resource\nplease try another");
    } else {
        p = (int far *)*h;
        fd_50F6_47D8 = p[0];
        fd_50F6_47D6 = p[1];
        fd_50F6_47D4 = p[2];
        db_PurgeObject(0x80, 0);
    }
    h = db_LoadObject(0x81, 0);
    _fmemcpy(fd_50F6_46E2, *h, fd_50F6_47D6 * 6);
    db_PurgeObject(0x81, 0);
    h = db_LoadObject(0x83, 0);
    q = *h;
    if (h == 0)
        Punt("Could not load purge list");
    _fmemcpy(purge, q, 0x28);
    db_PurgeObject(0x83, 0);
    for (i = 0; i < fd_50F6_47D8; i++) {
        if (purge[i] == 0) {
            f_20E8_0001(i << 8);
            f_1A53_034F(i, 0);
        }
    }
    return 1;
}

extern char far * far f_2505_0006(int win);
extern int g_5702[];
extern void _fastcall f_2505_08EA(int win);
extern void far f_1E57_0115(int win);
extern void _fastcall f_2505_0545(int win);
extern void far f_1E57_00B1(int win);
extern void _fastcall f_2505_0831(int win);
extern void far f_1E57_0174(int win);
extern void _fastcall f_21FA_08E2(int win);
extern void far f_1E57_0362(void);

void far f_20E8_032F(int from, int to, int unused, int p0, int p1, int p2, int p3)
{
    char far *w;
    struct Rect origin;
    struct Rect rect;
    char far *obj;

    f_23AE_0377(from);
    w = f_2505_0006(from);
    origin = *(struct Rect far *)(((char far * far *)(w + 0x2c))[0] + 8);
    rect = *(struct Rect far *)w;
    if (g_5702[0] != 0)
        f_2505_08EA(g_5702[0]);
    if (*(int far *)(w + 0x1c) & 0x200) {
        (*g_62E4)();
        (*g_62F4)(from);
        f_1E57_0115(from);
        *(int far *)(w + 0x1c) &= ~0x200;
        (*g_62E0)(from);
    }
    f_23AE_01DB(from);
    f_23AE_0377(to);
    w = f_2505_0006(to);
    obj = ((char far * far *)(w + 0x2c))[0];
    *(int far *)(obj + 8) = origin.left;
    *(int far *)(obj + 0xa) = origin.top;
    *(struct Rect far *)w = rect;
    *(struct Rect far *)obj = *(struct Rect far *)w;
    ((int far *)(w + 0x10))[0] = p0;
    ((int far *)(w + 0x10))[1] = p1;
    ((int far *)(w + 0x10))[2] = p2;
    ((int far *)(w + 0x10))[3] = p3;
    f_2505_0545(to);
    (*g_62E0)(to);
    *(int far *)(f_2505_0006(to) + 0x1c) |= 0x200;
    if (g_5702[0] != (int)0x8000)
        f_2505_08EA(g_5702[0]);
    f_1E57_00B1(to);
    f_2505_0831(to);
    f_1E57_0174(to);
    f_21FA_08E2(to);
    (*g_62E8)();
    f_23AE_01DB(to);
    f_1E57_0362();
}

/* SCAFFOLD BEGIN: f_20E8_04B6 best draft.
   Residue: (1) the first w = f_2505_0006(win) is kept in BX (dead-store
   eliminated) where the original assigns SI/[bp-0Eh]; (2) near globals
   g_3DB4/g_3DB2 are compared as cmp [g],reg while the original loads the
   global into AX first (mov ax,[3DB4]; cmp [bp-12h],ax; jle) - 388 vs 383. */
extern void _fastcall f_23AE_036F(int win);
extern void _fastcall f_2505_0288(int obj, struct Rect far *rect);
extern int near g_3DB4;
extern int far fd_50F6_3942;
extern int near g_3DB2;
extern void far f_218D_042B(void);

void far f_20E8_04B6(int win, int p0, int p1, int p2, int p3)
{
    char far *w;
    int dx;
    int dy;
    struct Rect r;
    int far *origin;

    if (g_5702[0] != win) {
        f_23AE_036F(win);
        (*g_62E4)();
        w = f_2505_0006(win);
        ((int far *)(w + 0x10))[0] = p0;
        ((int far *)(w + 0x10))[1] = p1;
        ((int far *)(w + 0x10))[2] = p2;
        ((int far *)(w + 0x10))[3] = p3;
        f_2505_0545(win);
        w = f_2505_0006(win);
        if (*(int far *)(w + 0x1c) & 0x1000) {
            dx = dy = 0;
            f_2505_0288(win, &r);
            if (g_3DB4 < r.bottom)
                dy = g_3DB4 - r.bottom;
            else if (r.top <= fd_50F6_3942)
                dy = fd_50F6_3942 - r.top;
            if (r.left < 0)
                dx = -r.left;
            else if (g_3DB2 <= r.right)
                dx = g_3DB2 - r.right;
            origin = (int far *)(((char far * far *)(w + 0x2c))[0] + 8);
            fd_50F6_4892[win >> 8] = *(struct Rect far *)origin;
            origin[0] += dx;
            origin[1] += dy;
            f_2505_0545(win);
        }
        (*g_62E0)(win);
        *(int far *)(f_2505_0006(win) + 0x1c) |= 0x200;
        if (g_5702[0] != (int)0x8000)
            f_2505_08EA(g_5702[0]);
        f_1E57_00B1(win);
        f_2505_0831(win);
        f_1E57_0174(win);
        f_21FA_08E2(win);
        (*g_62E8)();
        f_1E57_0362();
        f_23AE_01DB(win);
    }
    f_218D_042B();
}

/* SCAFFOLD END */

extern void _fastcall f_21FA_0B4B(struct Rect far *rect);

void _fastcall f_20E8_0635(int win)
{
    char far *w;
    struct Rect r;

    f_23AE_0377(win);
    w = f_2505_0006(win);
    if (*(int far *)(w + 0x1c) & 0x200) {
        (*g_62E4)();
        (*g_62F4)(win);
        if (g_5702[0] == win) {
            f_2505_08EA(win);
            f_1E57_0115(win);
            if (g_5702[0] != (int)0x8000)
                f_2505_0831(g_5702[0]);
        } else {
            f_1E57_0115(win);
        }
        *(int far *)(w + 0x1c) &= ~0x200;
        if (*(int far *)(w + 0x1c) & 0x1000)
            *(struct Rect far *)(((char far * far *)(w + 0x2c))[0] + 8) = fd_50F6_4892[(char)(win >> 8)];
        (*g_62E0)(win);
        r = *(struct Rect far *)w;
        f_23AE_01DB(win);
        f_21FA_0B4B(&r);
        (*g_62E8)();
        f_1E57_0362();
    } else {
        f_23AE_01DB(win);
    }
}

extern char far * _fastcall f_2505_0345(int win);

void _fastcall f_20E8_0725(int win)
{
    int top;
    int flag;

    top = g_5702[0];
    if (top != win) {
        if (top != (int)0x8000) {
            f_23AE_0377(top);
            flag = *(int far *)(f_2505_0345(top) + 0x1c) & 1;
            f_23AE_01DB(top);
            if (flag)
                f_20E8_0635(top);
        }
        f_20E8_04B6(win);
    }
}

extern void far f_1E57_0052(int win);
extern void _fastcall f_21FA_0AD2(struct Rect far *rect);

void _fastcall f_20E8_0776(int win)
{
    int flag;
    char far *w;
    struct Rect r;

    f_23AE_0377(win);
    f_2505_0006(win);
    flag = *(int far *)(f_2505_0345(g_5702[0]) + 0x1c) & 1;
    f_23AE_01DB(win);
    (*g_62E4)();
    if (g_5702[0] == win) {
        if (g_5702[1] != (int)0x8000) {
            if (flag) {
                f_20E8_0635(g_5702[0]);
                return;
            }
            f_1E57_0052(win);
            if (g_5702[0] != win) {
                f_2505_08EA(win);
                f_2505_0831(g_5702[0]);
            }
        }
    } else {
        f_1E57_0052(win);
    }
    f_23AE_0377(win);
    w = f_2505_0006(win);
    *(int far *)(w + 0x1c) |= 0x200;
    r = *(struct Rect far *)w;
    f_23AE_01DB(win);
    (*g_62E0)(win);
    f_21FA_0AD2(&r);
    (*g_62E8)();
    f_1E57_0362();
}

void _fastcall f_20E8_0862(int win, void (far *hook)(int phase))
{
    fd_50F6_47DE[win >> 8] = hook;
}

void _fastcall f_20E8_088B(void (far *hook)(int win))
{
    g_62E0 = hook;
}

void _fastcall f_20E8_089F(void (far *hook)(int win))
{
    g_62F4 = hook;
}

void _fastcall f_20E8_08B3(void (far *hook)(void))
{
    g_62E4 = hook;
}

void _fastcall f_20E8_08C7(void (far *hook)(void))
{
    g_62E8 = hook;
}

void _fastcall f_20E8_08DB(void (far *hook)(void))
{
    g_62EC = hook;
}

void _fastcall f_20E8_08EF(void (far *hook)(void))
{
    g_62F0 = hook;
}

/* SCAFFOLD BEGIN: f_20E8_0903 best draft.
   Residue: loops 2/3 index with DI=i*2 and base in BX (les bx,[ptr];
   mov ax,es:[bx+di]); the original moves the index to BX and loads the far
   base into DI (mov bx,di; les di,[ptr]; ...) with a dead les bx,[bp-20h]
   before rect[i]-o[i]: 258 vs 286 bytes. */
extern int far * _fastcall f_2505_02D7(int obj);

void _fastcall f_20E8_0903(int obj, int far *rect)
{
    int j;
    int win;
    int far *o;
    int far *origin;
    int far *mode;
    int far *ref;
    int i;

    win = obj & 0xff00;
    f_23AE_0377(win);
    o = f_2505_02D7(obj);
    origin = o + 4;
    mode = o + 12;
    ref = o + 8;
    for (j = 0; j < 4; j++)
        origin[j] = 0;
    f_2505_0545(win);
    for (i = 0; i < 4; i++) {
        if (mode[i] && mode[i] != 5 && ref[i] == obj)
            origin[i] = 0;
        else
            origin[i] = rect[i] - o[i];
    }
    f_2505_0545(win);
    for (i = 0; i < 4; i++) {
        if (mode[i] && mode[i] != 5 && ref[i] == obj)
            origin[i] = rect[i] - o[i];
    }
    f_2505_0545(win);
    f_23AE_01DB(win);
}

/* SCAFFOLD END */

extern int far f_2505_036E(void);

void far f_20E8_0A21(void)
{
    int top;

    top = g_5702[0];
    if (f_2505_036E()) {
        f_23AE_0377(top);
        if (*(int far *)(f_2505_0345(top) + 0x1c) & 1)
            f_20E8_0635(top);
        f_23AE_01DB(top);
    }
}
