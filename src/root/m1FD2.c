/* Root module 1FD2: menu bar, menu item states, timers and small input helpers. */

struct Rect {
    int left;
    int top;
    int right;
    int bottom;
};

typedef struct {
    int x;
    int y;
} Point;

struct Timer {
    struct Rect r;
    void (far *fn)();
    int ticks;
    char a;
    char b;
    char c;
    char d;
};

struct MenuData {
    char far * far *titles;
    char far * far *items[16];
};

struct Event {
    int what;
    int message;
    int x4;
    char modLo;
    char modHi;
    int h;
    int v;
    int code;
    int xE;
};

extern void far f_1B73_030F();
extern void far f_1B73_0D4B();

int g_5FE6 = 0x707;
int g_5FE8 = 0x707;
int g_5FEA = 0x101;
int g_5FEC = 0xb0b;
int g_5FEE = 0xf0f;
struct Event near input_queue[7];
int g_5FF0 = 7;
struct Timer g_5FF2 = { { 0, 0, 0, 0xff }, 0, (int)(struct Event near *)input_queue, 5, 0, 10, 0 };
struct Timer g_6004 = { { 0, 0, 100, 100 }, f_1B73_030F, 1, 1, 1, 0, 10 };
struct Timer g_6016 = { { 0, 0, 100, 100 }, f_1B73_0D4B, 1, 1, 1, 0, -1 };
struct Timer g_6028 = { { 0, 0, 100, 100 }, f_1B73_0D4B, 1, 1, 1, 0, -1 };
struct Timer g_603A = { { 0, 0, 0x27f, 0x10 }, f_1B73_030F, 0, 0, 0, 0, 0x1f };
int g_604C = 0;
int g_604E = 0x100;
int g_6050 = 0;
int g_6052 = 0;
struct MenuData far *g_6054 = 0;

extern int far vsprintf(char far *buffer, char far *format, char far *args);
void far f_1FD2_02B1(int mode);
extern void far f_1FBD_0000(int x, int y, char far *text);

void far f_1FD2_0008(int x, int y, int color, char far *format, ...)
{
    char buf[32];

    vsprintf(buf, format, (char far *)(&format + 1));
    if (buf[0] & 0x80) {
        f_1FD2_02B1(color + 2);
        buf[0] &= 0x7f;
    } else {
        f_1FD2_02B1(color);
    }
    f_1FBD_0000(x, y, buf);
}

void far f_1FD2_0198(int id);
void far f_1FD2_021B(int id);

void far f_1FD2_0059(int id, int on)
{
    if (on)
        f_1FD2_0198(id);
    else
        f_1FD2_021B(id);
}

void far f_1FD2_0077(int id)
{
    char far *p;

    if (!(id & 15))
        p = g_6054->titles[id >> 4];
    else
        p = g_6054->items[id >> 4][(id - 1) & 15];
    *p = (*p & 0x80) + 0x10;
}

void far f_1FD2_00D6(int id)
{
    char far *p;

    if (!(id & 15))
        p = g_6054->titles[id >> 4];
    else
        p = g_6054->items[id >> 4][(id - 1) & 15];
    *p = (*p & 0x80) + 0x20;
}

extern char far * far _fstrcpy(char far *dest, char far *src);

void far f_1FD2_0135(int id, char far *text)
{
    char far *p;

    if (!(id & 15))
        p = g_6054->titles[id >> 4];
    else
        p = g_6054->items[id >> 4][(id - 1) & 15];
    _fstrcpy(p, text);
}

extern int far fd_50F6_46A8[];

void far f_1FD2_0198(int id)
{
    char far *p;
    int menu;

    if (!(id & 15)) {
        menu = id >> 4;
        p = g_6054->titles[menu];
        *p &= 0x7f;
        f_1FD2_0008(fd_50F6_46A8[menu], 1, 1, p);
    } else {
        p = g_6054->items[id >> 4][(id - 1) & 15];
        *p &= 0x7f;
    }
}

void far f_1FD2_021B(int id)
{
    char far *p;
    int menu;

    if (!(id & 15)) {
        menu = id >> 4;
        p = g_6054->titles[menu];
        *p = (*p & 0x7f) + 0x80;
        f_1FD2_0008(fd_50F6_46A8[menu], 1, 1, p);
    } else {
        p = g_6054->items[id >> 4][(id - 1) & 15];
        *p = (*p & 0x7f) + 0x80;
    }
}

extern void (far * near g_9128)(int a, int b, int c);

void far f_1FD2_02B1(int mode)
{
    switch (mode) {
    case 0:
        g_9128(g_5FEC, g_5FEA, 0);
        break;
    case 1:
        g_9128(g_5FEA, g_5FEC, 0xc0);
        break;
    case 2:
        g_9128(g_5FEE, g_5FEA, 0x30);
        break;
    case 3:
        g_9128(g_5FEE, g_5FEC, 0x30);
        break;
    }
}

extern struct Rect far * far f_1CE2_000C(void);
void far f_1FD2_032F(struct Rect far *r, void (far *fn)(), int ticks);

void far f_1FD2_02FF(void)
{
    f_1FD2_032F(f_1CE2_000C(), f_1B73_0D4B, 100);
}

extern char far fd_5071_0728[];
extern void far f_1B73_0B5B(int ticks, char far *slot);

void far f_1FD2_031A(void)
{
    f_1B73_0B5B(100, fd_5071_0728);
}

extern void far f_1B73_0B00(struct Timer far *t, char far *slot);

void far f_1FD2_032F(struct Rect far *r, void (far *fn)(), int ticks)
{
    g_6016.r.left = r->left;
    g_6016.r.top = r->top;
    g_6016.r.right = r->right;
    g_6016.r.bottom = r->bottom;
    g_6016.ticks = ticks;
    g_6016.fn = fn;
    f_1B73_0B00(&g_6016, fd_5071_0728);
}

void far f_1FD2_0379(int ticks)
{
    f_1B73_0B5B(ticks, fd_5071_0728);
}

extern void far f_1B73_0AC3(struct Timer far *t, char far *slot);

void far f_1FD2_0390(struct Rect far *r, void (far *fn)(), int ticks)
{
    g_6016.r.left = r->left;
    g_6016.r.top = r->top;
    g_6016.r.right = r->right;
    g_6016.r.bottom = r->bottom;
    g_6016.ticks = ticks;
    g_6016.fn = fn;
    f_1B73_0B5B(ticks, fd_5071_0728);
    f_1B73_0AC3(&g_6016, fd_5071_0728);
}

extern char far fd_5071_03C4[];

void far f_1FD2_03EB(struct Rect far *r, int ticks)
{
    g_6004.r.left = r->left;
    g_6004.r.top = r->top;
    g_6004.r.right = r->right;
    g_6004.r.bottom = r->bottom;
    g_6004.ticks = ticks;
    f_1B73_0B5B(ticks, fd_5071_03C4);
    f_1B73_0B00(&g_6004, fd_5071_03C4);
}

void far f_1FD2_0438(int ticks)
{
    f_1B73_0B5B(ticks, fd_5071_03C4);
}

extern char far fd_5071_0060[];

void far f_1FD2_044F(struct Rect far *r, int ticks)
{
    g_603A.r.left = r->left;
    g_603A.r.top = r->top;
    g_603A.r.right = r->right;
    g_603A.r.bottom = r->bottom;
    g_603A.ticks = ticks;
    f_1B73_0B5B(ticks, fd_5071_0060);
    f_1B73_0B00(&g_603A, fd_5071_0060);
}

void far f_1FD2_049C(int ticks)
{
    f_1B73_0B5B(ticks, fd_5071_0060);
}

extern void far f_1B73_0C42(int a, char far *slot, int b, int c);

void far f_1FD2_04B3(int a, int b, int c)
{
    f_1B73_0C42(a, fd_5071_03C4, b, c);
}

extern int near g_9122;
extern int near g_9124;

void far f_1FD2_04D0(Point far *pt)
{
    pt->x = g_9122;
    pt->y = g_9124;
}

int far f_1FD2_04E5(Point far *pt, struct Rect far *r)
{
    if (r->right > pt->x && r->left <= pt->x && r->top <= pt->y && pt->y < r->bottom)
        return 1;
    return 0;
}

extern void far f_1B73_0BC5(int ticks, char far *slot);

void far f_1FD2_052B(int ticks)
{
    f_1B73_0BC5(ticks, fd_5071_03C4);
}

extern unsigned char near g_9120;
extern int far f_1B73_0A30(int key);

int far StillDown(void)
{
    int mods;

    mods = g_9120 & 3;
    if (f_1B73_0A30(0x52) || f_1B73_0A30(0x39))
        mods |= 1;
    if (f_1B73_0A30(0x53))
        mods |= 2;
    return mods;
}

static long lastTick;
static int shiftHeld;
static int countdown;
extern unsigned long far TickCount(void);

void far ButtonHeldInit(void)
{
    lastTick = TickCount();
    countdown = 2;
    shiftHeld = 0;
}

int far ButtonHeld(void)
{
    if (countdown) {
        if (TickCount() != lastTick) {
            countdown--;
            lastTick = TickCount();
        }
    } else {
        if (shiftHeld || StillDown())
            shiftHeld = 1;
        else
            shiftHeld = 0;
        if (shiftHeld && !StillDown())
            return 0;
    }
    return 1;
}

extern void far win_FlushEvents(void);

void far ButtonHeldEnd(void)
{
    while (StillDown())
        ;
    win_FlushEvents();
}

extern void far f_1CE2_0951(struct Rect far *r, int fore, int back);
int far f_1FD2_0663(int draw);

void far f_1FD2_05FD(void)
{
    f_1CE2_0951(f_1CE2_000C(), g_5FE6, g_5FE8);
    f_1FD2_0663(1);
}

extern void far Punt(char far *format, ...);

void far SetMenuItemState(int id, char state)
{
    if (!g_6054)
        Punt("Attempt to SetMenuItemState with no menu loaded!");
    *g_6054->items[id >> 4][id & 15] = state;
}

extern void (far * near g_9130)(void);
extern struct Rect far fd_50F6_393C;
extern char near g_3DDC;
extern int near g_3DE4;
extern int near g_3DE2;
extern void far f_1CE2_046D(struct Rect far *rect, int color);
extern unsigned far _fstrlen(char far *s);
extern int far fd_50F6_46BC[];
extern char near g_3DDE;
extern int near g_3DB2;

int far f_1FD2_0663(int draw)
{
    int i;
    int total;
    int x;
    char far * far *t;

    if (!g_6054)
        return 0;
    g_9130();
    fd_50F6_393C = *f_1CE2_000C();
    fd_50F6_393C.bottom = g_3DDC + fd_50F6_393C.top + 3;
    f_1FD2_02B1(1);
    if (draw)
        f_1CE2_046D(&fd_50F6_393C, g_3DE2 | g_3DE4);
    i = 0;
    total = 0;
    for (t = g_6054->titles; *t; t++) {
        fd_50F6_46BC[i] = _fstrlen(*t);
        total += fd_50F6_46BC[i];
        i++;
    }
    g_604C = i;
    if (i > 1) {
        g_6050 = (g_3DB2 / g_3DDE - total) / (i - 1);
        if (g_6050 > 3)
            g_6050 = 3;
        else if (g_6050 < 1)
            g_6050 = 1;
        i = x = 0;
        for (t = g_6054->titles; *t; t++, i++) {
            fd_50F6_46A8[i] = x;
            if (draw)
                f_1FD2_0008(x, 1, 1, *t);
            x += (fd_50F6_46BC[i] + g_6050) * g_3DDE;
        }
    }
    return 1;
}

extern void far f_1B73_09E9(int x, int y);
extern int far o10_35F5_01C3(struct Event far *ev);

void far f_1FD2_07CB(int menu)
{
    struct Event ev;
    int x;

    x = g_3DDE * 4 + fd_50F6_46A8[menu];
    ev.code = menu;
    ev.modHi = 0;
    f_1B73_09E9(x, 1);
    o10_35F5_01C3(&ev);
}

extern int far f_1B73_032A(void);
extern void far f_1B73_032E(struct Event far *ev);

void far f_1FD2_080D(void)
{
    struct Event ev;

    while (f_1B73_032A())
        f_1B73_032E(&ev);
}

extern int far f_1F58_0038(void);
extern int far f_1F58_0090(void);

int far f_1FD2_082E(void)
{
    while (f_1F58_0038())
        if (f_1F58_0090() == 13)
            return 1;
    return 0;
}

extern int _fastcall win_GetEvent(struct Event far *ev);

int far f_1FD2_084F(struct Event far *ev)
{
    while (!win_GetEvent(ev))
        if (f_1F58_0038() && f_1F58_0090() == 0x1b)
            return 0;
    ButtonHeldEnd();
    return 1;
}

extern int far f_208F_0419(Point far *size, int object);

void far f_1FD2_0883(int x, int y, int object, int ticks, int show)
{
    Point size;
    struct Rect r;

    if (show) {
        f_208F_0419(&size, object);
        r.left = x;
        r.right = x + size.x;
        r.top = y;
        r.bottom = y + size.y;
        f_1FD2_03EB(&r, ticks);
    } else {
        f_1FD2_0438(ticks);
    }
}
