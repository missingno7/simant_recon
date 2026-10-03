#include "dos_types.h"
#include "portable/whole_program/platform/dos_memory.h"
#include "portable/whole_program/platform/dos_io.h"
#include "portable/whole_program/platform/graphics_source_fields.h"
#pragma pack(push, 2)
#include "portable/whole_program/window_source_rects.h"
extern struct Rect *g_5AAC;
#include "portable/whole_program/platform/graphics_source_clip.h"
#include <stddef.h>
/* Root module 1E57: window clip regions (clip lists, clip stack). */

typedef char  *  *Handle;
int16_t g_5702[32] = { (int16_t)0x8000 };
Handle g_5742 = 0;
Handle g_5746 = 0;
Handle g_574A = 0;
char  *g_574E = (char  *)&g_5A9C;
int16_t g_5752[2] = { 0 };
int16_t g_5756 = 0;
int16_t g_5758 = 0;
int16_t g_575A[12] = { 0 };

void  f_1E57_0006(int16_t n, int16_t kind)
{
}

void  f_1E57_0007(void)
{
}

extern void  f_171C_1C0A(Handle h);
void  f_1E57_0009(void)
{
    if (g_5742) {
        f_171C_1C0A(g_5742);
        g_5742 = 0;
    }
    if (g_5746)
        g_5746 = 0;
    g_5AAC = 0;
}

void  f_1E57_00B1(int16_t win);

void  f_1E57_0043(int16_t win)
{
    f_1E57_00B1(win);
}

void  f_1E57_038E(void);

void  f_1E57_0052(int16_t win)
{
    int16_t i;
    int16_t j;

    win &= 0xff00;
    for (i = j = 0; j < 31; i++, j++) {
        if (g_5702[i] == (int16_t)0x8000)
            break;
        if (g_5702[j] == win)
            i++;
        g_5702[j] = g_5702[i];
    }
    g_5702[j] = win;
    g_5702[j + 1] = 0x8000;
    f_1E57_038E();
}


void  f_1E57_00B1(int16_t win)
{
    int16_t buf[32];
    int16_t i;
    int16_t j;

    buf[0] = win &= 0xff00;
    for (i = 0, j = 1; j < 31; i++, j++) {
        if (g_5702[i] == (int16_t)0x8000)
            break;
        buf[j] = g_5702[i];
        if (g_5702[i] == win)
            j--;
    }
    buf[j] = 0x8000;
    _fmemcpy(g_5702, buf, sizeof(buf));
    f_1E57_038E();
}

extern int16_t  WinPrintf(char  *format, ...);

void  clip_KillWin(int16_t win)
{
    int16_t i;
    int16_t j;

    win &= 0xff00;
    for (j = i = 0; i < 31; j++, i++) {
        if (g_5702[i] == (int16_t)0x8000)
            break;
        if (g_5702[i] == win)
            j++;
        g_5702[i] = g_5702[j];
    }
    if (i >= 31)
        WinPrintf("\nWARNING: i>=MAXWINDOWS-1 in KillWin(%d)", win);
    f_1E57_038E();
}

extern int16_t  win_IsWinOpen(int16_t win);
extern Handle  fd_50F6_3B60[45];
extern void  Punt(char  *format, ...);
extern char  *  f_171C_1B84(Handle h);
extern struct Rect  *fd_50F6_3C14;
extern int16_t sim_source_runtime_reserve_clip_rects(size_t bytes);
extern Handle  f_171C_1BBA(Handle h);

void  clip_SetWin(int16_t win)
{
    struct Rect  *p;
    int16_t size;

    f_1E57_0009();
    win &= 0xff00;
    if (win_IsWinOpen(win)) {
        g_5746 = fd_50F6_3B60[win >> 8];
        if (!g_5746)
            Punt("SetWin: Window open but clip is NULL");
        p = (struct Rect  *)f_171C_1B84(g_5746);
        g_5AAC = p;
        for (size = 8; g_5AAC->top != (int16_t)0x8000; size += 8, g_5AAC++)
            ;
        if (size <= 0 || !sim_source_runtime_reserve_clip_rects((size_t)size))
            Punt("Cannot allocate clip rectangle snapshot");
        _fmemcpy(fd_50F6_3C14, p, size);
        f_171C_1BBA(g_5746);
        g_5AAC = fd_50F6_3C14;
    } else
        g_5AAC = 0;
}

int16_t  f_1E57_0239(int16_t win)
{
    Handle h;
    struct Rect  *p;
    int16_t r;

    h = fd_50F6_3B60[win >> 8];
    p = (struct Rect  *)f_171C_1B84(h);
    if (h && p->top != (int16_t)0x8000)
        r = 1;
    else
        r = 0;
    f_171C_1BBA(h);
    return r;
}

void  f_1E57_0296(void)
{
    struct Rect  *p;
    int16_t size;

    f_1E57_0009();
    if (g_574A == &g_574E) {
        g_5AAC = &g_5A9C;
        return;
    }
    g_5746 = g_574A;
    if (!g_5746)
        Punt("\n\aERROR MEMNULL winClipHandle");
    p = (struct Rect  *)f_171C_1B84(g_5746);
    if (p) {
        for (size = 8, g_5AAC = p; g_5AAC->top != (int16_t)0x8000; size += 8, g_5AAC++)
            ;
        if (size <= 0 || !sim_source_runtime_reserve_clip_rects((size_t)size))
            Punt("Cannot allocate clip rectangle snapshot");
        _fmemcpy(fd_50F6_3C14, p, size);
        g_5AAC = fd_50F6_3C14;
        f_171C_1BBA(g_5746);
    }
}

void  f_1E57_0351(void)
{
    f_1E57_0009();
    g_5AAC = &g_5A9C;
}

void  clip_Off(void)
{
    f_1E57_0009();
    g_5AAC = 0;
}

int16_t  f_1E57_036F(struct Rect  *r)
{
    int16_t n;

    for (n = 0; r->top != (int16_t)0x8000; r++, n++)
        ;
    return n;
}

int16_t s_584C = 0;

extern Handle  f_171C_1A9E(int32_t size, int16_t flags, char  *name);
extern void  win_GetObjRect(int16_t obj, struct Rect  *rect);
extern struct Rect  *  f_1D8E_02BD(struct Rect  *c, struct Rect  *list,
                                         struct Rect  *in, struct Rect  *out);
extern Handle  f_171C_1B2C(Handle h, int32_t size, int16_t flags);

/* SCAFFOLD BEGIN: f_1E57_038E (rebuild all window clip lists) best draft, 985 vs 997 bytes.
 * Control flow, calls and data match; the original frame is 0x32 with seven unused /Oe homes
 * (three far-pointer-sized) and keeps `next` in memory with TMP's offset cached in DI during
 * the window loop; this draft allocates `next` to DI.  The variable set is not recovered. */
void  f_1E57_038E(void)
{
    int16_t i;
    int16_t next;
    int16_t n;
    int16_t win;
    struct Rect  *end;
    struct Rect  *list;
    struct Rect r;
    Handle tmpH;
    struct Rect  *tmp;
    int16_t count;

    f_1E57_0009();
    if (!s_584C) {
        _fmemset(fd_50F6_3B60, 0, sizeof(fd_50F6_3B60));
        s_584C = 1;
    }
    if (g_574A && g_574A != &g_574E)
        f_171C_1C0A(g_574A);
    win = g_5702[0];
    if (win == (int16_t)0x8000) {
        g_574A = &g_574E;
        return;
    }
    tmpH = f_171C_1A9E(256 * sizeof(struct Rect), 0, "tmprects");
    tmp = (struct Rect  *)f_171C_1B84(tmpH);
    g_574A = f_171C_1A9E(256 * sizeof(struct Rect), 0, "clipout");
    for (i = 0; i < 45; i++) {
        if (fd_50F6_3B60[i]) {
            f_171C_1C0A(fd_50F6_3B60[i]);
            fd_50F6_3B60[i] = 0;
        }
    }
    list = (struct Rect  *)f_171C_1B84(g_574A);
    *list = g_5A9C;
    list[1].top = 0x8000;
    win_GetObjRect(win, &r);
    fd_50F6_3B60[win >> 8] = f_171C_1A9E(n = (f_1D8E_02BD(&r, list, tmp, 0L) - tmp + 1) * sizeof(struct Rect), 1, "winClipList");
    _fmemcpy(f_171C_1B84(fd_50F6_3B60[win >> 8]), tmp, n);
    f_171C_1BBA(fd_50F6_3B60[win >> 8]);
    for (i = 1; i < 32; i++) {
        next = g_5702[i];
        if (next == (int16_t)0x8000)
            break;
        win_GetObjRect(win, &r);
        end = f_1D8E_02BD(&r, list, 0L, tmp);
        count = end - tmp;
        if (count >= 256)
            Punt("C097: Clip overflow %d", count);
        _fmemcpy(list, tmp, (count + 1) * sizeof(struct Rect));
        win_GetObjRect(next, &r);
        end = f_1D8E_02BD(&r, list, tmp, 0L);
        n = count = end - tmp;
        if (count >= 256)
            Punt("C098: Clip overflow %d", count);
        f_1E57_0006(n, 0);
        fd_50F6_3B60[next >> 8] = f_171C_1A9E(n = (n + 1) * sizeof(struct Rect), 1, "winClipList");
        _fmemcpy(f_171C_1B84(fd_50F6_3B60[next >> 8]), tmp, n);
        f_171C_1BBA(fd_50F6_3B60[next >> 8]);
        win = next;
    }
    win_GetObjRect(win, &r);
    end = f_1D8E_02BD(&r, list, 0L, tmp);
    n = end - tmp;
    if (n >= 256)
        Punt("C099: Clip overflow %d", n);
    f_1E57_0006(n, 0);
    n = (n + 1) * sizeof(struct Rect);
    _fmemcpy(list, tmp, n);
    f_171C_1BBA(g_574A);
    g_574A = f_171C_1B2C(g_574A, n, 1);
    f_171C_1BBA(tmpH);
    f_171C_1C0A(tmpH);
    f_1E57_0007();
}
/* SCAFFOLD END */

extern struct Rect  *  f_1D8E_003F(struct Rect  *r, struct Rect  *c,
                                         struct Rect  *in, struct Rect  *out);

void  clip_SubInclude(struct Rect  *r)
{
    Handle h;
    struct Rect  *buf;
    struct Rect  *p;
    int16_t n;

    if (r) {
        h = f_171C_1A9E(2048, 0, "subinclude");
        buf = (struct Rect  *)f_171C_1B84(h);
        p = buf;
        if (!g_5AAC) {
            n = 1;
            *p = *r;
        } else {
            for (; g_5AAC->top != (int16_t)0x8000; g_5AAC++)
                p = f_1D8E_003F(g_5AAC, r, p, 0L);
            if ((n = p - buf) >= 256)
                Punt("CL074:Temp clip overflow in SubInclude");
        }
    } else
        Punt("Sub include NULL rect!!");
    buf[n].top = 0x8000;
    f_171C_1BBA(h);
    if (!(h = f_171C_1B2C(h, (int32_t)(n + 1) << 3, 1)))
        Punt("Clip out of memory!!!");
    f_1E57_0009();
    if (n < 0 || !sim_source_runtime_reserve_clip_rects(((size_t)n + 1u) * sizeof(struct Rect)))
        Punt("Cannot allocate clip rectangle output");
    g_5AAC = fd_50F6_3C14;
    _fmemcpy(g_5AAC, f_171C_1B84(h), (n + 1) << 3);
    f_171C_1BBA(h);
    g_5742 = h;
    f_1E57_0006(n, 1);
}

void  f_1E57_08F5(struct Rect  *r)
{
    Handle h;
    struct Rect  *buf;
    struct Rect  *p;
    struct Rect  *c;
    int16_t n;

    if (r) {
        h = f_171C_1A9E(2048, 0, "subinclude");
        buf = (struct Rect  *)f_171C_1B84(h);
        p = buf;
        if (!g_5AAC) {
            for (n = 0; r->top != (int16_t)0x8000; p++, r++, n++)
                *p = *r;
        } else {
            for (; r->top != (int16_t)0x8000; r++)
                for (c = g_5AAC; c->top != (int16_t)0x8000; c++)
                    p = f_1D8E_003F(c, r, p, 0L);
            if ((n = p - buf) >= 256)
                Punt("CL074:Temp clip overflow in SubInclude");
        }
    } else
        Punt("Sub include NULL rect!!");
    buf[n].top = 0x8000;
    f_171C_1BBA(h);
    if (!(h = f_171C_1B2C(h, (int32_t)(n + 1) << 3, 1)))
        Punt("Clip out of memory!!!");
    f_1E57_0009();
    if (n < 0 || !sim_source_runtime_reserve_clip_rects(((size_t)n + 1u) * sizeof(struct Rect)))
        Punt("Cannot allocate clip rectangle output");
    g_5AAC = fd_50F6_3C14;
    _fmemcpy(g_5AAC, f_171C_1B84(h), (n + 1) << 3);
    f_171C_1BBA(h);
    f_171C_1C0A(h);
    f_1E57_0006(n, 1);
}

void  f_1E57_0A9C(struct Rect  *r)
{
    clip_SubInclude(r);
}

void  clip_SubExclude(struct Rect  *r)
{
    Handle h;
    struct Rect  *buf;
    struct Rect  *p;
    int16_t n;

    if (r) {
        h = f_171C_1A9E(2048, 0, "subexclude");
        buf = (struct Rect  *)f_171C_1B84(h);
        if (!g_5AAC)
            g_5AAC = &g_5A9C;
        for (p = buf; g_5AAC->top != (int16_t)0x8000; g_5AAC++)
            p = f_1D8E_003F(g_5AAC, r, 0L, p);
        if ((n = p - buf) >= 256)
            Punt("CL074:Temp clip overflow in SubExclude");
    } else
        Punt("Sub exclude NULL rect!!");
    f_1E57_0006(n, 1);
    buf[n].top = 0x8000;
    f_171C_1BBA(h);
    if (!(h = f_171C_1B2C(h, (int32_t)(n + 1) << 3, 1)))
        Punt("Clip out of memory!!!");
    f_1E57_0009();
    if (n < 0 || !sim_source_runtime_reserve_clip_rects(((size_t)n + 1u) * sizeof(struct Rect)))
        Punt("Cannot allocate clip rectangle output");
    g_5AAC = fd_50F6_3C14;
    _fmemcpy(g_5AAC, f_171C_1B84(h), (n + 1) << 3);
    f_171C_1BBA(h);
    g_5742 = h;
}

void  f_1E57_0C1A(struct Rect  *r)
{
    clip_SubExclude(r);
}

void  f_1E57_0C2D(struct Rect  *r)
{
    Handle h;
    struct Rect  *buf;
    struct Rect  *p;
    struct Rect  *c;
    int16_t n;

    if (r) {
        h = f_171C_1A9E(2048, 0, "include");
        buf = (struct Rect  *)f_171C_1B84(h);
        if (g_5AAC && g_5AAC->top != (int16_t)0x8000) {
            for (c = g_5AAC, p = buf; c->top != (int16_t)0x8000; c++, p++)
                *p = *c;
            for (; g_5AAC->top != (int16_t)0x8000; g_5AAC++)
                p = f_1D8E_003F(r, g_5AAC, 0L, p);
            if ((n = p - buf) >= 256)
                Punt("CL174:Temp clip overflow in SubExclude");
        } else {
            n = 1;
            *buf = *r;
        }
    } else
        Punt("include NULL rect!!");
    f_1E57_0006(n, 1);
    buf[n].top = 0x8000;
    f_1E57_0009();
    if (n < 0 || !sim_source_runtime_reserve_clip_rects(((size_t)n + 1u) * sizeof(struct Rect)))
        Punt("Cannot allocate clip rectangle output");
    g_5AAC = fd_50F6_3C14;
    _fmemcpy(g_5AAC, buf, (n + 1) << 3);
    f_171C_1BBA(h);
    f_171C_1C0A(h);
}

void  f_1E57_0D97(struct Rect  *r)
{
    f_1E57_0C2D(r);
}

extern Handle  fd_50F6_3B5C;

void  clip_Push(void)
{
    struct Rect  *p;
    int16_t size;
    Handle h;
    Handle  *node;

    size = 0;
    if ((p = g_5AAC) != 0) {
        for (; p->top != (int16_t)0x8000; p++)
            ;
        size = (char  *)p - (char  *)g_5AAC + sizeof(struct Rect);
        g_5758 += size / (int16_t)sizeof(struct Rect);
    }
    if (!(h = f_171C_1A9E(size + (int32_t)(2 * sizeof(Handle)), 1, "clip_Push")))
        Punt("Cannot allocate memory in clip_Push");
    node = (Handle  *)f_171C_1B84(h);
    if (size)
        _fmemcpy(node + 2, g_5AAC, size);
    node[0] = fd_50F6_3B5C;
    ((struct Rect  *  *)node)[1] = g_5AAC;
    fd_50F6_3B5C = h;
    if (++g_5756 > 20)
        Punt("Error CL98463: Pushed it too far");
    f_171C_1BBA(h);
}

void  clip_Pop(void)
{
    Handle  *node;
    struct Rect  *p;
    int16_t size;

    if (!g_5756)
        Punt("Clip_Pop w/ nothing on the stack: E9073");
    f_1E57_0009();
    g_5742 = fd_50F6_3B5C;
    node = (Handle  *)f_171C_1B84(g_5742);
    fd_50F6_3B5C = node[0];
    if (!((struct Rect  *  *)node)[1])
        g_5AAC = 0;
    else if ((p = g_5AAC = (struct Rect  *)(node + 2)) != 0) {
        for (; p->top != (int16_t)0x8000; p++)
            ;
        size = (char  *)p - (char  *)g_5AAC + sizeof(struct Rect);
        if (size <= 0 || !sim_source_runtime_reserve_clip_rects((size_t)size))
            Punt("Cannot allocate clip rectangle snapshot");
        _fmemcpy(fd_50F6_3C14, g_5AAC, size);
        g_5AAC = fd_50F6_3C14;
    }
    g_5756--;
    f_171C_1BBA(g_5742);
}

void  f_1E57_0F8E(struct Rect  *r)
{
    if (r->top >= g_5A9C.top && r->bottom <= g_5A9C.bottom &&
        r->left >= g_5A9C.left && r->right <= g_5A9C.right)
        clip_Off();
    else
        f_1E57_0351();
}


void  f_1E57_0FDC(struct Rect  *r)
{
    if (r) {
        f_1E57_0009();
        if (!sim_source_runtime_reserve_clip_rects(5u * sizeof(struct Rect)))
            Punt("Cannot allocate clip rectangle output");
        g_5AAC = fd_50F6_3C14;
        f_1D8E_003F(r, &g_5A9C, fd_50F6_3C14, 0L);
    }
}

#pragma pack(pop)
