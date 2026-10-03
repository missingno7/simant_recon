#include "dos_types.h"
#include "portable/whole_program/platform/dos_memory.h"
#include "portable/whole_program/platform/dos_io.h"
#include "portable/whole_program/platform/graphics_source_fields.h"
#include "portable/whole_program/platform/m1b73_event_enqueue.h"
#pragma pack(push, 2)
#include "portable/whole_program/window_source_rects.h"
extern struct Rect *g_5AAC;
#include "portable/whole_program/platform/graphics_source_clip.h"
#include <stdarg.h>
#include <stdint.h>
extern int16_t dos_printf(const char *format, ...);
extern int16_t dos_sprintf(char *buffer, const char *format, ...);
extern int16_t dos_vsprintf(char *buffer, const char *format, va_list args);

/* Overlay section S10, code frame 35F5: pull-down menu bar. */

#include <stdio.h>
#include <string.h>
#include <ctype.h>
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

struct Pt {
    int16_t x;
    int16_t y;
};

static int16_t curMenu = -1;

extern void  f_1CE2_044D(struct Rect  *r, int16_t width);
extern void  f_1FBD_0000(int16_t x, int16_t y, char  *s);
extern void  f_1FD2_03EB(struct Rect  *r, int16_t v);

void  o10_35F5_0000(int16_t x, int16_t y, char  *s, int16_t v)
{
    int16_t len;
    struct Rect r;

    len = _fstrlen(s);
    r.left = x = (char)(x >> 8) + (x & 0xff) * SIM_GRAPHICS_SOURCE_g_3DDE;
    r.right = x + SIM_GRAPHICS_SOURCE_g_3DDE * len - 1;
    r.top = y = SIM_GRAPHICS_SOURCE_g_3DDC * (y & 0xff) + (char)(y >> 8) * SIM_GRAPHICS_SOURCE_g_3DDC / 14;
    r.bottom = y + SIM_GRAPHICS_SOURCE_g_3DDC - 1;
    f_1CE2_044D(&r, -3);
    (*g_9128)(SIM_GRAPHICS_SOURCE_g_3DE2, SIM_GRAPHICS_SOURCE_g_3DE0, SIM_GRAPHICS_SOURCE_g_3DE4);
    f_1CE2_044D(&r, -2);
    (*g_9128)(SIM_GRAPHICS_SOURCE_g_3DE2, SIM_GRAPHICS_SOURCE_g_3DE0, SIM_GRAPHICS_SOURCE_g_3DE4);
    f_1FBD_0000(x, y, s);
    f_1FD2_03EB(&r, v);
}

extern void  f_1B4E_0110(int16_t x, int16_t y, int16_t c);

void  o10_35F5_00D7(int16_t x, int16_t y, char  *s, int16_t v)
{
    int16_t len;
    struct Rect r;

    len = _fstrlen(s);
    r.left = x = (char)(x >> 8) + (x & 0xff) * SIM_GRAPHICS_SOURCE_g_3DDE;
    r.right = x + SIM_GRAPHICS_SOURCE_g_3DDE - 1;
    r.top = y = SIM_GRAPHICS_SOURCE_g_3DDC * (y & 0xff) + (char)(y >> 8) * SIM_GRAPHICS_SOURCE_g_3DDC / 14;
    r.bottom = y + SIM_GRAPHICS_SOURCE_g_3DDC * len - 1;
    f_1CE2_044D(&r, -5);
    (*g_9128)(SIM_GRAPHICS_SOURCE_g_3DE2, SIM_GRAPHICS_SOURCE_g_3DE0, SIM_GRAPHICS_SOURCE_g_3DE4);
    f_1CE2_044D(&r, -2);
    (*g_9128)(SIM_GRAPHICS_SOURCE_g_3DE2, SIM_GRAPHICS_SOURCE_g_3DE0, SIM_GRAPHICS_SOURCE_g_3DE4);
    while (*s) {
        f_1B4E_0110(x, y, *s);
        s++;
        y += SIM_GRAPHICS_SOURCE_g_3DDC;
    }
    f_1FD2_03EB(&r, v);
}

extern void ( *  g_9130)(void);
extern char ***fd_55B3_6054;
extern int16_t  StillDown(void);
extern int16_t  *fd_50F6_46A8;
extern void  f_1FD2_0008(int16_t x, int16_t y, int16_t mode, char  *s);
int16_t  o10_35F5_0384(char  *sel, char  *  *items);
extern int16_t  f_1F58_0038(void);
extern char  f_1F58_005A(void);
extern int16_t g_604C;
extern void  f_1B73_09E9(int16_t x, int16_t y);
extern void  f_1F58_007F(int16_t c);

int16_t  o10_35F5_01C3(struct Event  *ev)
{
    int16_t m;
    int16_t prev;
    char sel;
    char c;

    (*g_9130)();
    m = ev->code & 0xff;
    if (fd_55B3_6054[0][m][0] & 0x80)
        return 0;
    if ((!StillDown() && (char)(ev->modifiers >> 8)) || curMenu == m)
        return;
    if (curMenu != -1) {
again:
        f_1FD2_0008(fd_50F6_46A8[curMenu], 1, 1, fd_55B3_6054[0][curMenu]);
        curMenu = -1;
    }
    if (m >= 100)
        return;
    curMenu = m;
    f_1FD2_0008(fd_50F6_46A8[m], 1, 0, fd_55B3_6054[0][m]);
    if (!o10_35F5_0384(&sel, fd_55B3_6054[m + 1]))
        return;
    m = 0xff;
    if (!f_1F58_0038())
        goto again;
    if (f_1F58_005A())
        goto again;
    c = f_1F58_005A();
    prev = curMenu;
next:
    if (c == 0x4b) {
        if (prev)
            m = prev - 1;
        else
            m = g_604C - 1;
    } else if (c == 0x4d) {
        m = (prev + 1) % g_604C;
    } else {
        f_1F58_007F(c);
        f_1F58_007F(0);
        m = 0xff;
        goto again;
    }
    if (fd_55B3_6054[0][m][0] & 0x80) {
        prev = m;
        goto next;
    }
    f_1B73_09E9(fd_50F6_46A8[m] + SIM_GRAPHICS_SOURCE_g_3DDE * 3, SIM_GRAPHICS_SOURCE_g_3DDC / 2);
    goto again;
}

extern char  *  dos_malloc(uint16_t size);
extern void  f_1F80_0081(int16_t a);
extern void  f_1B73_0A40(void);
extern void  f_1FD2_04D0(struct Pt  *pt);
extern int16_t  *fd_50F6_46BC;
extern char  *  GSaveRect(struct Rect  *r);
extern void  f_1FD2_02B1(int16_t a);
extern void  Punt(char  *fmt, ...);
extern void  f_1FD2_02FF(void);
extern int16_t  f_1B73_032A(void);
extern void  f_1B73_032E(struct Event  *ev);
extern int16_t  f_1FD2_04E5(struct Pt  *pt, struct Rect  *r);
extern int16_t  f_1F58_0090(void);
extern void  f_1FD2_031A(void);
extern void  f_1B73_0A6C(void);
extern void  f_1CE2_056C(struct Rect  *r, char  *buf);
extern void  dos_free(char  *block);

/* SCAFFOLD BEGIN: o10_35F5_0384 (pull-down menu) best draft: logic and length close; block order of the key switch, local slot layout and the dead old=0 store differ */
int16_t  o10_35F5_0384(char  *sel, char  *  *items)
{
    int16_t j;
    int16_t t;
    int16_t key;
    int16_t old;
    int16_t cur;
    char  *p;
    int16_t nItems;
    int16_t maxLen;
    int16_t x;
    int16_t i;
    int16_t len;
    int16_t down;
    struct Pt last;
    struct Pt pt;
    struct Rect r;
    struct Rect saveR;
    int16_t k;
    int16_t d;
    int16_t result;
    char fmt[10];
    struct Event ev;
    char  *saveBuf;
    char  *buf;
    struct Rect *saved;
    int16_t c;

    cur = -1;
    result = down = 0;
    if (items == 0 || *items == 0)
        goto none;
    buf = dos_malloc(4000);
    saved = g_5AAC;
    g_5AAC = 0;
    last.x = last.y = -1;
    f_1F80_0081(1);
    f_1B73_0A40();
    t = curMenu == -1 ? 0 : 1;
    f_1FD2_04D0(&pt);
    old = maxLen = i = 0;
    for (; items[i] != 0; i++) {
        len = _fstrlen(items[i]);
        if (len > maxLen)
            maxLen = len;
    }
    maxLen += 1 - t;
    nItems = i;
    if (curMenu == -1) {
        r.left = (pt.x & ~7) + 16;
        r.top = SIM_GRAPHICS_SOURCE_g_3DDC * (1 - i) + pt.y - 3;
    } else {
        r.left = ((fd_50F6_46BC[curMenu] - maxLen) >> 1) * SIM_GRAPHICS_SOURCE_g_3DDE + fd_50F6_46A8[curMenu];
        if (r.left < 0)
            r.left = 0;
        r.top = SIM_GRAPHICS_SOURCE_g_3DDC + 1;
    }
    r.right = SIM_GRAPHICS_SOURCE_g_3DDE * maxLen + r.left + 16;
    if (r.right > g_5A9C.right) {
        d = r.right - g_5A9C.right;
        r.right -= d;
        r.left -= d;
    }
    if (SIM_GRAPHICS_SOURCE_g_3DDC + 5 > r.top)
        r.top = SIM_GRAPHICS_SOURCE_g_3DDC + 5;
    r.bottom = SIM_GRAPHICS_SOURCE_g_3DDC * i + r.top + 6;
    if (r.bottom > g_5A9C.bottom - 5) {
        d = r.bottom - g_5A9C.bottom + 5;
        r.top -= d;
        r.bottom -= d;
    }
    saveBuf = GSaveRect(&r);
    saveR = r;
    r.left += SIM_GRAPHICS_SOURCE_g_3DDE;
    r.right -= SIM_GRAPHICS_SOURCE_g_3DDE;
    r.top += 3;
    r.bottom -= 3;
    f_1FD2_02B1(1);
    f_1CE2_044D(&r, -3);
    f_1FD2_02B1(0);
    f_1CE2_044D(&r, -1);
    f_1FD2_02B1(1);
    x = r.left;
    j = r.top;
    if (t)
        dos_sprintf(fmt, "%%-%ds", maxLen);
    else
        dos_sprintf(fmt, "%%c%%-%ds", maxLen - 1);
    p = buf;
    for (i = 0; i < nItems; i++, j += SIM_GRAPHICS_SOURCE_g_3DDC) {
        if (items[i][1] == '-') {
            _fmemset(p + 1, '-', maxLen - 2);
            p[maxLen] = 0;
            p[maxLen - 1] = ' ';
            p[0] = ' ';
        } else if (t)
            dos_sprintf(p, fmt, items[i]);
        else
            dos_sprintf(p, fmt, i == *sel - 1 ? 16 : ' ', items[i]);
        f_1FD2_0008(x, j, 1, p);
        p[maxLen] = 0;
        p += maxLen + 1;
        if (p > buf + 4000)
            Punt("Menu data too long");
    }
    f_1FD2_02FF();
    if (!StillDown())
        down = 0;
    k = -1;
    for (;;) {
        if (down && !StillDown())
            goto done;
        if (StillDown() && !down)
            down = 1;
        if (f_1B73_032A()) {
            f_1B73_032E(&ev);
            if ((char)(ev.code >> 8) == -2 && (ev.code & 0xff) != curMenu)
                goto other;
        }
        if (down) {
            f_1FD2_04D0(&pt);
            if (_fmemcmp(&pt, &last, 4) == 0)
                continue;
            last = pt;
            if (f_1FD2_04E5(&pt, &r)) {
                k = (pt.y - r.top) / SIM_GRAPHICS_SOURCE_g_3DDC;
                if (k >= 0 && k < nItems &&
                    items[k][1] != '-' && !(items[k][0] & 0x80))
                    goto moved;
            }
            k = -1;
        } else if (f_1F58_0038()) {
            key = f_1F58_0090();
            if (!(key & 0x800) && islower(key))
                key -= 0x20;
            old = cur;
            j = 0;
            k = cur;
retry:
            switch (key) {
            case 10:
            case 13:
            case ' ':
            case 0x852:
            case 0x853:
                goto done;
            case 27:
                goto escape;
            default:
                old = k;
                if (key & 0x800)
                    goto flush;
                j = t = cur;
                if (!isalpha(key))
                    goto restore;
                k = t;
nextc:
                if (++k < nItems)
                    goto trych;
                k = -1;
                goto testc;
            case '+':
            case 0x850:
                k = (k + 1) % nItems;
                goto check;
            case '-':
            case 0x848:
                k = (k > 0 ? k : nItems) - 1;
check:
                if (items[k][1] != '-' && !(items[k][0] & 0x80))
                    goto warp;
                if (j <= 16) {
                    j++;
                    goto retry;
                }
                k = cur;
                break;
trych:
                c = items[k][1];
                if (islower(c))
                    c -= 0x20;
                if (c == key)
                    goto found;
testc:
                if (t != k)
                    goto nextc;
restore:
                k = old;
            }
        }
moved:
        if (cur == k)
            continue;
        if (cur != -1) {
            f_1FD2_0008(x, SIM_GRAPHICS_SOURCE_g_3DDC * cur + r.top, 1, buf + (maxLen + 1) * cur);
            cur = -1;
        }
        if (k == -1)
            continue;
        cur = k;
        f_1FD2_02B1(0);
        f_1FD2_0008(x, SIM_GRAPHICS_SOURCE_g_3DDC * k + r.top, 0, buf + (maxLen + 1) * k);
    }
found:
    old = k;
warp:
    f_1B73_09E9(SIM_GRAPHICS_SOURCE_g_3DDE * 4 + x, SIM_GRAPHICS_SOURCE_g_3DDC / 2 + SIM_GRAPHICS_SOURCE_g_3DDC * k + r.top);
    goto moved;
flush:
    f_1F58_007F(key & 0xff);
    f_1F58_007F(0);
escape:
    cur = -1;
done:
    if (!StillDown() && curMenu != -1) {
        if (cur != -1)
            portable_m1b73_event_enqueue_four_word_command((curMenu << 4) + cur - 0x2ff, 0, 0, 0);
        result = 1;
    }
    if (cur != -1)
        *sel = cur + 1;
    f_1FD2_031A();
    f_1B73_0A6C();
    f_1CE2_056C(&saveR, saveBuf);
    g_5AAC = saved;
    dos_free(buf);
    return result;
other:
    f_1B73_030F(ev.code, ev.xE, ev.h, ev.v, 0);
    goto done;
none:
    if (curMenu != -1)
        portable_m1b73_event_enqueue_four_word_command((curMenu - 0x30) << 4, 0, 0, 0);
    *sel = 0;
    return 1;
}
/* SCAFFOLD END */

extern void  f_1B73_0C80(int16_t item);

int16_t  o10_35F5_0A63(int16_t key, int16_t  *sel, int16_t count, int16_t base)
{
    int16_t i;

    i = *sel;
    if (key == '+') {
        if (++i >= count)
            i = 0;
    } else if (key == '-') {
        if (--i < 0)
            i = count - 1;
    } else
        return 0;
    f_1B73_0C80(i + base);
    *sel = i;
    return 1;
}

#pragma pack(pop)
