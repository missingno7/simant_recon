#include "dos_types.h"
#include "portable/whole_program/platform/dos_memory.h"
#include "portable/whole_program/platform/dos_io.h"
#include "portable/whole_program/menu_globals.h"
#include "portable/whole_program/platform/graphics_source_fields.h"
#include "portable/whole_program/platform/m1b73_queue_source.h"
#include "portable/whole_program/types/timer.h"
#include "portable/whole_program/state/menu_bar_rect.h"
#pragma pack(push, 2)
#include <stddef.h>
#include <stdarg.h>
#include <stdint.h>
extern int16_t dos_printf(const char *format, ...);
extern int16_t dos_sprintf(char *buffer, const char *format, ...);
extern int16_t dos_vsprintf(char *buffer, const char *format, va_list args);

/* Root module 1FD2: menu bar, menu item states, timers and small input helpers. */

typedef struct {
    int16_t x;
    int16_t y;
} Point;

struct MenuData {
    char  *  *titles;
    char  *  *items[16];
};

struct Event {
    int16_t what;
    int16_t message;
    int16_t x4;
    char modLo;
    char modHi;
    int16_t h;
    int16_t v;
    int16_t code;
    int16_t xE;
};

extern void  f_1B73_030F();
extern void  f_1B73_0D4B();

int16_t g_5FE6 = 0x707;
int16_t g_5FE8 = 0x707;
int16_t g_5FEA = 0x101;
int16_t g_5FEC = 0xb0b;
int16_t g_5FEE = 0xf0f;
int16_t g_5FF0 = 7;
struct Timer g_5FF2 = { { 0, 0, 0, 0xff }, 0, (int16_t)0x91b0, 5, 0, 10, 0 };
struct Timer g_6004 = { { 0, 0, 100, 100 }, f_1B73_030F, 1, 1, 1, 0, 10 };
struct Timer g_6016 = { { 0, 0, 100, 100 }, f_1B73_0D4B, 1, 1, 1, 0, -1 };
struct Timer g_6028 = { { 0, 0, 100, 100 }, f_1B73_0D4B, 1, 1, 1, 0, -1 };
struct Timer g_603A = { { 0, 0, 0x27f, 0x10 }, f_1B73_030F, 0, 0, 0, 0, 0x1f };
int16_t g_604C = 0;
int16_t g_604E = 0x100;
int16_t g_6050 = 0;
int16_t g_6052 = 0;

void  f_1FD2_02B1(int16_t mode);
extern void  f_1FBD_0000(int16_t x, int16_t y, char  *text);

void  f_1FD2_0008(int16_t x, int16_t y, int16_t color, char  *format, ...)
{
    va_list _dos_va_args;
    va_start(_dos_va_args, format);

    char buf[32];

    dos_vsprintf(buf, format, _dos_va_args);
    if (buf[0] & 0x80) {
        f_1FD2_02B1(color + 2);
        buf[0] &= 0x7f;
    } else {
        f_1FD2_02B1(color);
    }
    f_1FBD_0000(x, y, buf);

    va_end(_dos_va_args);
}

void  f_1FD2_0198(int16_t id);
void  f_1FD2_021B(int16_t id);

void  f_1FD2_0059(int16_t id, int16_t on)
{
    if (on)
        f_1FD2_0198(id);
    else
        f_1FD2_021B(id);
}

void  f_1FD2_0077(int16_t id)
{
    char  *p;

    if (!(id & 15))
        p = g_menu_view.titles[id >> 4];
    else
        p = g_menu_view.items[id >> 4][(id - 1) & 15];
    *p = (*p & 0x80) + 0x10;
}

void  f_1FD2_00D6(int16_t id)
{
    char  *p;

    if (!(id & 15))
        p = g_menu_view.titles[id >> 4];
    else
        p = g_menu_view.items[id >> 4][(id - 1) & 15];
    *p = (*p & 0x80) + 0x20;
}


void  f_1FD2_0135(int16_t id, char  *text)
{
    char  *p;

    if (!(id & 15))
        p = g_menu_view.titles[id >> 4];
    else
        p = g_menu_view.items[id >> 4][(id - 1) & 15];
    _fstrcpy(p, text);
}

extern int16_t  *fd_50F6_46A8;
extern int16_t sim_source_runtime_reserve_menu_titles(size_t count);

void  f_1FD2_0198(int16_t id)
{
    char  *p;
    int16_t menu;

    if (!(id & 15)) {
        menu = id >> 4;
        p = g_menu_view.titles[menu];
        *p &= 0x7f;
        f_1FD2_0008(fd_50F6_46A8[menu], 1, 1, p);
    } else {
        p = g_menu_view.items[id >> 4][(id - 1) & 15];
        *p &= 0x7f;
    }
}

void  f_1FD2_021B(int16_t id)
{
    char  *p;
    int16_t menu;

    if (!(id & 15)) {
        menu = id >> 4;
        p = g_menu_view.titles[menu];
        *p = (*p & 0x7f) + 0x80;
        f_1FD2_0008(fd_50F6_46A8[menu], 1, 1, p);
    } else {
        p = g_menu_view.items[id >> 4][(id - 1) & 15];
        *p = (*p & 0x7f) + 0x80;
    }
}


void  f_1FD2_02B1(int16_t mode)
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

extern struct Rect  *  f_1CE2_000C(void);
void  f_1FD2_032F(struct Rect  *r, void ( *fn)(), int16_t ticks);

void  f_1FD2_02FF(void)
{
    f_1FD2_032F(f_1CE2_000C(), f_1B73_0D4B, 100);
}

void  f_1FD2_031A(void)
{
    f_1B73_0B5B(100, portable_m1b73_queue_slot(3));
}

void  f_1FD2_032F(struct Rect  *r, void ( *fn)(), int16_t ticks)
{
    g_6016.r.left = r->left;
    g_6016.r.top = r->top;
    g_6016.r.right = r->right;
    g_6016.r.bottom = r->bottom;
    g_6016.ticks = ticks;
    g_6016.fn = fn;
    f_1B73_0B00(&g_6016, portable_m1b73_queue_slot(3));
}

void  f_1FD2_0379(int16_t ticks)
{
    f_1B73_0B5B(ticks, portable_m1b73_queue_slot(3));
}

void  f_1FD2_0390(struct Rect  *r, void ( *fn)(), int16_t ticks)
{
    g_6016.r.left = r->left;
    g_6016.r.top = r->top;
    g_6016.r.right = r->right;
    g_6016.r.bottom = r->bottom;
    g_6016.ticks = ticks;
    g_6016.fn = fn;
    f_1B73_0B5B(ticks, portable_m1b73_queue_slot(3));
    f_1B73_0AC3(&g_6016, portable_m1b73_queue_slot(3));
}

void  f_1FD2_03EB(struct Rect  *r, int16_t ticks)
{
    g_6004.r.left = r->left;
    g_6004.r.top = r->top;
    g_6004.r.right = r->right;
    g_6004.r.bottom = r->bottom;
    g_6004.ticks = ticks;
    f_1B73_0B5B(ticks, portable_m1b73_queue_slot(2));
    f_1B73_0B00(&g_6004, portable_m1b73_queue_slot(2));
}

void  f_1FD2_0438(int16_t ticks)
{
    f_1B73_0B5B(ticks, portable_m1b73_queue_slot(2));
}

void  f_1FD2_044F(struct Rect  *r, int16_t ticks)
{
    g_603A.r.left = r->left;
    g_603A.r.top = r->top;
    g_603A.r.right = r->right;
    g_603A.r.bottom = r->bottom;
    g_603A.ticks = ticks;
    f_1B73_0B5B(ticks, portable_m1b73_queue_slot(1));
    f_1B73_0B00(&g_603A, portable_m1b73_queue_slot(1));
}

void  f_1FD2_049C(int16_t ticks)
{
    f_1B73_0B5B(ticks, portable_m1b73_queue_slot(1));
}

int16_t  f_1FD2_04B3(int16_t a, PortableM1B73Rect *r)
{
    return f_1B73_0C42((int16_t)a, portable_m1b73_queue_slot(2), r);
}

void  f_1FD2_04D0(Point  *pt)
{
    pt->x = g_9122;
    pt->y = g_9124;
}

int16_t  f_1FD2_04E5(Point  *pt, struct Rect  *r)
{
    if (r->right > pt->x && r->left <= pt->x && r->top <= pt->y && pt->y < r->bottom)
        return 1;
    return 0;
}

void  f_1FD2_052B(int16_t ticks)
{
    f_1B73_0BC5(ticks, portable_m1b73_queue_slot(2));
}

extern int16_t  f_1B73_0A30(int16_t key);

int16_t  StillDown(void)
{
    int16_t mods;

    mods = portable_m1b73_g9120_low_byte() & 3;
    if (f_1B73_0A30(0x52) || f_1B73_0A30(0x39))
        mods |= 1;
    if (f_1B73_0A30(0x53))
        mods |= 2;
    return mods;
}

static int32_t lastTick;
static int16_t shiftHeld;
static int16_t countdown;
extern uint32_t  TickCount(void);

void  ButtonHeldInit(void)
{
    lastTick = TickCount();
    countdown = 2;
    shiftHeld = 0;
}

int16_t  ButtonHeld(void)
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

extern void  win_FlushEvents(void);

void  ButtonHeldEnd(void)
{
    while (StillDown())
        ;
    win_FlushEvents();
}

extern void  f_1CE2_0951(struct Rect  *r, int16_t fore, int16_t back);
int16_t  f_1FD2_0663(int16_t draw);

void  f_1FD2_05FD(void)
{
    f_1CE2_0951(f_1CE2_000C(), g_5FE6, g_5FE8);
    f_1FD2_0663(1);
}

extern void  Punt(char  *format, ...);

void  SetMenuItemState(int16_t id, char state)
{
    if (fd_55B3_6054 == NULL)
        Punt("Attempt to SetMenuItemState with no menu loaded!");
    *g_menu_view.items[id >> 4][id & 15] = state;
}

extern void ( *  g_9130)(void);
extern void  f_1CE2_046D(struct Rect  *rect, int16_t color);

extern int16_t  *fd_50F6_46BC;

int16_t  f_1FD2_0663(int16_t draw)
{
    int16_t i;
    int16_t total;
    int16_t menuCount;
    int16_t x;
    char  *  *t;

    if (fd_55B3_6054 == NULL)
        return 0;
    g_9130();
    fd_50F6_393C = *f_1CE2_000C();
    fd_50F6_393C.bottom = SIM_GRAPHICS_SOURCE_g_3DDC + fd_50F6_393C.top + 3;
    f_1FD2_02B1(1);
    if (draw)
        f_1CE2_046D(&fd_50F6_393C, SIM_GRAPHICS_SOURCE_g_3DE2 | SIM_GRAPHICS_SOURCE_g_3DE4);
    menuCount = 0;
    for (t = g_menu_view.titles; *t; t++)
        menuCount++;
    if (!sim_source_runtime_reserve_menu_titles((size_t)menuCount))
        Punt("Cannot allocate menu title geometry");
    i = 0;
    total = 0;
    for (t = g_menu_view.titles; *t; t++) {
        fd_50F6_46BC[i] = _fstrlen(*t);
        total += fd_50F6_46BC[i];
        i++;
    }
    g_604C = i;
    if (i > 1) {
        g_6050 = (SIM_GRAPHICS_SOURCE_g_3DB2 / SIM_GRAPHICS_SOURCE_g_3DDE - total) / (i - 1);
        if (g_6050 > 3)
            g_6050 = 3;
        else if (g_6050 < 1)
            g_6050 = 1;
        i = x = 0;
        for (t = g_menu_view.titles; *t; t++, i++) {
            fd_50F6_46A8[i] = x;
            if (draw)
                f_1FD2_0008(x, 1, 1, *t);
            x += (fd_50F6_46BC[i] + g_6050) * SIM_GRAPHICS_SOURCE_g_3DDE;
        }
    }
    return 1;
}

extern void  f_1B73_09E9(int16_t x, int16_t y);
extern int16_t  o10_35F5_01C3(struct Event  *ev);

void  f_1FD2_07CB(int16_t menu)
{
    struct Event ev;
    int16_t x;

    x = SIM_GRAPHICS_SOURCE_g_3DDE * 4 + fd_50F6_46A8[menu];
    ev.code = menu;
    ev.modHi = 0;
    f_1B73_09E9(x, 1);
    o10_35F5_01C3(&ev);
}

extern int16_t  f_1B73_032A(void);
extern void  f_1B73_032E(struct Event  *ev);

void  f_1FD2_080D(void)
{
    struct Event ev;

    while (f_1B73_032A())
        f_1B73_032E(&ev);
}

extern int16_t  f_1F58_0038(void);
extern int16_t  f_1F58_0090(void);

int16_t  f_1FD2_082E(void)
{
    while (f_1F58_0038())
        if (f_1F58_0090() == 13)
            return 1;
    return 0;
}

extern int16_t  win_GetEvent(struct Event  *ev);

int16_t  f_1FD2_084F(struct Event  *ev)
{
    while (!win_GetEvent(ev))
        if (f_1F58_0038() && f_1F58_0090() == 0x1b)
            return 0;
    ButtonHeldEnd();
    return 1;
}

extern int16_t  f_208F_0419(Point  *size, int16_t object);

void  f_1FD2_0883(int16_t x, int16_t y, int16_t object, int16_t ticks, int16_t show)
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

#pragma pack(pop)
