#include "portable/whole_program/platform/m1b73_countdown.h"
#include "dos_types.h"
#include "portable/whole_program/platform/dos_memory.h"
#include "portable/whole_program/platform/dos_io.h"
#include "portable/whole_program/platform/graphics_source_fields.h"
#include "portable/whole_program/window_source_globals.h"
#pragma pack(push, 2)
#include <stdarg.h>
#include <stdint.h>
extern int16_t dos_printf(const char *format, ...);
extern int16_t dos_sprintf(char *buffer, const char *format, ...);
extern int16_t dos_vsprintf(char *buffer, const char *format, va_list args);

/* Root module 208F: window-object text and bitmap helpers, resource loading, delays.
   Built without /Zi: the cross-function relocation order forbids per-function record
   breaks (e.g. none between 0x0074 and 0x0245); /Zd is equally consistent. */

struct Rect {
    int16_t left;
    int16_t top;
    int16_t right;
    int16_t bottom;
};

typedef struct {
    int16_t x;
    int16_t y;
} Point;

int16_t g_62BE = 0xa000;
int16_t g_62C0 = 5;

extern void  win_GetObjRect(int16_t obj, struct Rect  *rect);
extern void  f_1CE2_0430(struct Rect  *rect);

void  f_208F_0008(int16_t obj)
{
    struct Rect r;

    win_GetObjRect(obj, &r);
    f_1CE2_0430(&r);
}


void  f_208F_002B(int16_t obj, int16_t col)
{
    struct Rect r;

    win_GetObjRect(obj, &r);
    SIM_GRAPHICS_SOURCE_g_3DA0 = SIM_GRAPHICS_SOURCE_g_3DDE * col + r.left;
    SIM_GRAPHICS_SOURCE_g_3DA2 = r.top;
}

extern void  win_SetColorFromObjNum(int16_t obj);
extern void  f_24AB_038D(int16_t x, int16_t y, char  *text);

void  f_208F_005B(int16_t obj, char  *text, int16_t dx, int16_t dy)
{
    struct Rect r;

    win_GetObjRect(obj, &r);
    win_SetColorFromObjNum(obj);
    f_24AB_038D(r.left + dx, r.top + dy, text);
}

extern int16_t  f_24AB_0329(char  *text);
extern int16_t  f_24AB_030B(void);

void  f_208F_0093(struct Rect  *rect, char  *text)
{
    struct Rect r;
    int16_t w;
    int16_t x;

    r = *rect;
    w = f_24AB_0329(text);
    x = (r.right - w + r.left) / 2;
    if (x < r.left)
        x = r.left;
    r.left = x;
    r.right = x + w;
    r.top += (r.bottom - f_24AB_030B() - r.top) / 2;
    r.bottom = f_24AB_030B() + r.top;
    f_24AB_038D(r.left, r.top, text);
}


void  f_208F_011F(struct Rect  *rect, char  *text)
{
    struct Rect r;
    int16_t w;
    int16_t x;

    r = *rect;
    w = f_24AB_0329(text);
    x = (r.right - w + r.left) / 2;
    if (x < r.left)
        x = r.left;
    r.left = x;
    r.right = x + w;
    r.top += (r.bottom - f_24AB_030B() - r.top) / 2;
    r.bottom = f_24AB_030B() + r.top;
    f_24AB_038D(r.left, r.top, text);
    if (rect->left < r.left)
        g_9134(rect->left, r.top, r.left, r.bottom, SIM_GRAPHICS_SOURCE_g_3DE2);
    if (rect->right > r.right)
        g_9134(r.right, r.top, rect->right, r.bottom, SIM_GRAPHICS_SOURCE_g_3DE2);
}

void  f_208F_01ED(int16_t obj, char  *text)
{
    struct Rect r;

    win_SetColorFromObjNum(obj);
    win_GetObjRect(obj, &r);
    f_208F_0093(&r, text);
}

void  f_208F_021B(int16_t obj, char  *text)
{
    struct Rect r;

    win_SetColorFromObjNum(obj);
    win_GetObjRect(obj, &r);
    f_24AB_038D(r.left, r.top, text);
}

extern void  f_1CE2_044D(struct Rect  *rect, int16_t width);

void  f_208F_024B(int16_t obj, int16_t color, int16_t width)
{
    struct Rect r;

    win_GetObjRect(obj, &r);
    g_9128(color, color, color);
    f_1CE2_044D(&r, width);
}


extern void ( *  g_917C)(int16_t x, int16_t y, int16_t offset);
extern char  *  *  fd_50F6_46D2;
extern void ( *  g_914C)(int16_t x, int16_t y, char  *p, int16_t w, int16_t h);

void  f_208F_027F(int16_t obj, int16_t n)
{
    struct Rect r;

    win_GetObjRect(obj, &r);
    if (!(((uint8_t)g_5A97) & 1)) {
        if (((uint8_t)g_5A97) & 2)
            g_914C(r.left, r.top, *fd_50F6_46D2 + (n << 5), 8, 8);
        else
            g_917C(r.left, r.top, (n << g_62C0) + g_62BE);
    } else
        g_914C(r.left, r.top, *fd_50F6_46D2 + (n << 5), 16, 16);
}

/* Two separate mode tests with identical calls: the 8x8 call of mode 6 is laid out inline
   and cross-jumped into the 16x16 tail; `==6 || ==2` places the shared block last. */
void  f_208F_02F0(int16_t x, int16_t y, int16_t n)
{
    if (!(((uint8_t)g_5A97) & 1)) {
        if (((uint8_t)g_5A97) == 6)
            g_914C(x, y, *fd_50F6_46D2 + (n << 5), 8, 8);
        else if (((uint8_t)g_5A97) == 2)
            g_914C(x, y, *fd_50F6_46D2 + (n << 5), 8, 8);
        else
            g_917C(x, y, (n << g_62C0) + g_62BE);
    } else
        g_914C(x, y, *fd_50F6_46D2 + (n << 5), 16, 16);
}

extern char  *  db_LoadObject(int16_t object, int16_t kind);
extern void  Punt(char  *format, ...);

char  *  f_208F_0357(int16_t kind, int16_t object)
{
    char  *p;

    p = db_LoadObject(object, kind);
    if (p == 0)
        Punt("\aCouldn't load resource %x,%x", object, kind);
    return p;
}
extern void  f_24AB_040C(char  *text);

void  f_208F_038E(char  *format, ...)
{
    va_list _dos_va_args;
    va_start(_dos_va_args, format);

    char buf[100];

    dos_vsprintf(buf, format, _dos_va_args);
    f_24AB_040C(buf);

    va_end(_dos_va_args);
}

void  f_208F_03BC(int16_t obj, char  *format, ...)
{
    va_list _dos_va_args;
    va_start(_dos_va_args, format);

    struct Rect r;
    char buf[100];

    win_SetColorFromObjNum(obj);
    win_GetObjRect(obj, &r);
    dos_vsprintf(buf, format, _dos_va_args);
    f_24AB_038D(r.left, r.top, buf);

    va_end(_dos_va_args);
}

void  f_208F_0403(void)
{
}

void  f_208F_0404(void)
{
}

extern void  db_PurgeHandle(char  *handle);

void  f_208F_0405(char  *handle)
{
    db_PurgeHandle(handle);
}

extern char  *  f_171C_1B84(char  *h);
extern void  f_1B05_0008(char  *packed, int16_t length);
extern uint16_t  f_1B05_0046(char  *dest, uint16_t length);
extern void  f_171C_1BBA(char  *h);
extern void  db_ReleaseObject(uint16_t object, int16_t kind);

int16_t  f_208F_0419(Point  *size, int16_t object)
{
    char  *h;
    int16_t  *p;
    int16_t hdr[6];

    h = db_LoadObject(object, 2);
    if (h == 0) {
        size->x = size->y = 1;
        return 0;
    }
    p = (int16_t  *)f_171C_1B84(h);
    if (p[0] == -1) {
        f_1B05_0008((char  *)(p + 2), p[1]);
        f_1B05_0046((char  *)hdr, 12);
        size->x = hdr[4];
        size->y = hdr[5];
    } else {
        size->x = p[4];
        size->y = p[5];
    }
    f_171C_1BBA(h);
    db_ReleaseObject(object, 2);
    return 1;
}

static int32_t g_8CE8;
extern int16_t  fd_50F6_46D0;
extern uint32_t  TickCount(void);

void  f_208F_04D0(int16_t delay)
{
    g_8CE8 = TickCount();
    fd_50F6_46D0 = delay;
}

extern int16_t  f_1F58_0038(void);
extern int16_t  f_1F58_0090(void);
extern int16_t  WaitedEnough(int32_t  *timer, int16_t delay);

int16_t  f_208F_04EE(void)
{
    int16_t key;

    if ((key = f_1F58_0038()) != 0) {
        key = f_1F58_0090();
        if (key != 13 && key != 27)
            key = 0;
    }
    return WaitedEnough(&g_8CE8, fd_50F6_46D0) || key;
}



void  f_208F_0530(int16_t ticks)
{
    portable_m1b73_source_countdown_wait(ticks);
}

void  f_208F_054B(int16_t ticks)
{
    portable_m1b73_source_countdown_write(ticks);
}

int16_t  f_208F_055B(void)
{
    return portable_m1b73_source_countdown_is_zero();
}

int16_t  f_208F_056A(void)
{
    while (f_1F58_0038())
        if (f_1F58_0090() == 0x1b)
            return 1;
    return 0;
}

int16_t  f_208F_058B(void)
{
    return 3;
}

#pragma pack(pop)
