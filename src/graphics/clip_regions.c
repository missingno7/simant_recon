/*
 * Maintains window clip regions and their rectangle lists. It implements include, exclude and
 * push or pop operations on the clip stack.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS: resident code; segment 1E57; partial original translation unit.
 * Windows: ANTEDIT, from recorded function pairs in the Windows symbol inventory. Some pairs are
 * HIGH confidence, not confirmed.
 * Build profile: msc600ax; /AL /Os /Oe /Og /Gs /Zi.
 */

typedef char far * far *Handle;

struct Rect {
    int left;
    int top;
    int right;
    int bottom;
};

int g_5702[32] = { (int)0x8000 };
Handle g_5742 = 0;
Handle g_5746 = 0;
Handle g_574A = 0;
extern struct Rect far g_5A9C;
char far *g_574E = (char far *)&g_5A9C;
int g_5752[2] = { 0 };
int g_5756 = 0;
int g_5758 = 0;
int g_575A[12] = { 0 };

void far f_1E57_0006(int n, int kind)
{
}

void far f_1E57_0007(void)
{
}

extern void far mem_Free(Handle h);
extern struct Rect far * near g_5AAC;

void far clip_reset_temporary_state(void)
{
    if (g_5742) {
        mem_Free(g_5742);
        g_5742 = 0;
    }
    if (g_5746)
        g_5746 = 0;
    g_5AAC = 0;
}

void far win_raise_and_reclip(int win);

void far f_1E57_0043(int win)
{
    win_raise_and_reclip(win);
}

void far win_rebuild_visible_clips(void);

void far f_1E57_0052(int win)
{
    int i;
    int j;

    win &= 0xff00;
    for (i = j = 0; j < 31; i++, j++) {
        if (g_5702[i] == (int)0x8000)
            break;
        if (g_5702[j] == win)
            i++;
        g_5702[j] = g_5702[i];
    }
    g_5702[j] = win;
    g_5702[j + 1] = 0x8000;
    win_rebuild_visible_clips();
}

extern void far * far _fmemcpy(void far *dst, void far *src, unsigned n);

void far win_raise_and_reclip(int win)
{
    int buf[32];
    int i;
    int j;

    buf[0] = win &= 0xff00;
    for (i = 0, j = 1; j < 31; i++, j++) {
        if (g_5702[i] == (int)0x8000)
            break;
        buf[j] = g_5702[i];
        if (g_5702[i] == win)
            j--;
    }
    buf[j] = 0x8000;
    _fmemcpy(g_5702, buf, sizeof(buf));
    win_rebuild_visible_clips();
}

extern int far WinPrintf(char far *format, ...);

void far clip_KillWin(int win)
{
    int i;
    int j;

    win &= 0xff00;
    for (j = i = 0; i < 31; j++, i++) {
        if (g_5702[i] == (int)0x8000)
            break;
        if (g_5702[i] == win)
            j++;
        g_5702[i] = g_5702[j];
    }
    if (i >= 31)
        WinPrintf("\nWARNING: i>=MAXWINDOWS-1 in KillWin(%d)", win);
    win_rebuild_visible_clips();
}

extern int _fastcall win_IsWinOpen(int win);
extern Handle far fd_50F6_3B60[45];
extern void far Punt(char far *format, ...);
extern char far * far mem_Lock(Handle h);
extern struct Rect far fd_50F6_3C14[];
extern Handle far mem_Unlock(Handle h);

void far clip_SetWin(int win)
{
    struct Rect far *p;
    int size;

    clip_reset_temporary_state();
    win &= 0xff00;
    if (win_IsWinOpen(win)) {
        g_5746 = fd_50F6_3B60[win >> 8];
        if (!g_5746)
            Punt("SetWin: Window open but clip is NULL");
        p = (struct Rect far *)mem_Lock(g_5746);
        g_5AAC = p;
        for (size = 8; g_5AAC->top != (int)0x8000; size += 8, g_5AAC++)
            ;
        _fmemcpy(fd_50F6_3C14, p, size);
        mem_Unlock(g_5746);
        g_5AAC = fd_50F6_3C14;
    } else
        g_5AAC = 0;
}

int far f_1E57_0239(int win)
{
    Handle h;
    struct Rect far *p;
    int r;

    h = fd_50F6_3B60[win >> 8];
    p = (struct Rect far *)mem_Lock(h);
    if (h && p->top != (int)0x8000)
        r = 1;
    else
        r = 0;
    mem_Unlock(h);
    return r;
}

void far f_1E57_0296(void)
{
    struct Rect far *p;
    int size;

    clip_reset_temporary_state();
    if (g_574A == &g_574E) {
        g_5AAC = &g_5A9C;
        return;
    }
    g_5746 = g_574A;
    if (!g_5746)
        Punt("\n\aERROR MEMNULL winClipHandle");
    p = (struct Rect far *)mem_Lock(g_5746);
    if (p) {
        for (size = 8, g_5AAC = p; g_5AAC->top != (int)0x8000; size += 8, g_5AAC++)
            ;
        _fmemcpy(fd_50F6_3C14, p, size);
        g_5AAC = fd_50F6_3C14;
        mem_Unlock(g_5746);
    }
}

void far f_1E57_0351(void)
{
    clip_reset_temporary_state();
    g_5AAC = &g_5A9C;
}

void far clip_Off(void)
{
    clip_reset_temporary_state();
    g_5AAC = 0;
}

int far f_1E57_036F(struct Rect far *r)
{
    int n;

    for (n = 0; r->top != (int)0x8000; r++, n++)
        ;
    return n;
}

int s_584C = 0;

extern void far * far _fmemset(void far *dst, int c, unsigned n);
extern Handle far mem_Alloc(long size, int flags, char far *name);
extern void _fastcall win_GetObjRect(int obj, struct Rect far *rect);
extern struct Rect far * far f_1D8E_02BD(struct Rect far *c, struct Rect far *list,
                                         struct Rect far *in, struct Rect far *out);
extern Handle far mem_Realloc(Handle h, long size, int flags);


void far win_rebuild_visible_clips(void)
{
    int i;
    int next;
    int n;
    int win;
    struct Rect far *end;
    struct Rect far *list;
    struct Rect r;
    Handle tmpH;
    struct Rect far *tmp;

    clip_reset_temporary_state();
    if (!s_584C) {
        _fmemset(fd_50F6_3B60, 0, sizeof(fd_50F6_3B60));
        s_584C = 1;
    }
    if (g_574A && g_574A != &g_574E)
        mem_Free(g_574A);
    win = g_5702[0];
    if (win == (int)0x8000) {
        g_574A = &g_574E;
        return;
    }
    tmpH = mem_Alloc(256 * sizeof(struct Rect), 0, "tmprects");
    tmp = (struct Rect far *)mem_Lock(tmpH);
    g_574A = mem_Alloc(256 * sizeof(struct Rect), 0, "clipout");
    for (i = 0; i < 45; i++) {
        if (fd_50F6_3B60[i]) {
            mem_Free(fd_50F6_3B60[i]);
            fd_50F6_3B60[i] = 0;
        }
    }
    list = (struct Rect far *)mem_Lock(g_574A);
    *list = g_5A9C;
    list[1].top = 0x8000;
    win_GetObjRect(win, &r);
    fd_50F6_3B60[win >> 8] = mem_Alloc(n = (f_1D8E_02BD(&r, list, tmp, 0L) - tmp + 1) * sizeof(struct Rect), 1, "winClipList");
    _fmemcpy(mem_Lock(fd_50F6_3B60[win >> 8]), tmp, n);
    mem_Unlock(fd_50F6_3B60[win >> 8]);
    for (i = 1; i < 32; i++) {
        next = g_5702[i];
        if (next == (int)0x8000)
            break;
        win_GetObjRect(win, &r);
        end = f_1D8E_02BD(&r, list, 0L, tmp);
        if ((n = end - tmp) >= 256)
            Punt("C097: Clip overflow %d", (end - tmp));
        _fmemcpy(list, tmp, ((end - tmp) + 1) * sizeof(struct Rect));
        win_GetObjRect(next, &r);
        end = f_1D8E_02BD(&r, list, tmp, 0L);
        if ((n = end - tmp) >= 256)
            Punt("C098: Clip overflow %d", (end - tmp));
        f_1E57_0006(n, 0);
        fd_50F6_3B60[next >> 8] = mem_Alloc(n = (n + 1) * sizeof(struct Rect), 1, "winClipList");
        _fmemcpy(mem_Lock(fd_50F6_3B60[next >> 8]), tmp, n);
        mem_Unlock(fd_50F6_3B60[next >> 8]);
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
    mem_Unlock(g_574A);
    g_574A = mem_Realloc(g_574A, n, 1);
    mem_Unlock(tmpH);
    mem_Free(tmpH);
    f_1E57_0007();
}


extern struct Rect far * far clip_split_rect(struct Rect far *r, struct Rect far *c,
                                         struct Rect far *in, struct Rect far *out);

void far clip_SubInclude(struct Rect far *r)
{
    Handle h;
    struct Rect far *buf;
    struct Rect far *p;
    int n;

    if (r) {
        h = mem_Alloc(2048, 0, "subinclude");
        buf = (struct Rect far *)mem_Lock(h);
        p = buf;
        if (!g_5AAC) {
            n = 1;
            *p = *r;
        } else {
            for (; g_5AAC->top != (int)0x8000; g_5AAC++)
                p = clip_split_rect(g_5AAC, r, p, 0L);
            if ((n = p - buf) >= 256)
                Punt("CL074:Temp clip overflow in SubInclude");
        }
    } else
        Punt("Sub include NULL rect!!");
    buf[n].top = 0x8000;
    mem_Unlock(h);
    if (!(h = mem_Realloc(h, (long)(n + 1) << 3, 1)))
        Punt("Clip out of memory!!!");
    clip_reset_temporary_state();
    g_5AAC = fd_50F6_3C14;
    _fmemcpy(g_5AAC, mem_Lock(h), (n + 1) << 3);
    mem_Unlock(h);
    g_5742 = h;
    f_1E57_0006(n, 1);
}

void far f_1E57_08F5(struct Rect far *r)
{
    Handle h;
    struct Rect far *buf;
    struct Rect far *p;
    struct Rect far *c;
    int n;

    if (r) {
        h = mem_Alloc(2048, 0, "subinclude");
        buf = (struct Rect far *)mem_Lock(h);
        p = buf;
        if (!g_5AAC) {
            for (n = 0; r->top != (int)0x8000; p++, r++, n++)
                *p = *r;
        } else {
            for (; r->top != (int)0x8000; r++)
                for (c = g_5AAC; c->top != (int)0x8000; c++)
                    p = clip_split_rect(c, r, p, 0L);
            if ((n = p - buf) >= 256)
                Punt("CL074:Temp clip overflow in SubInclude");
        }
    } else
        Punt("Sub include NULL rect!!");
    buf[n].top = 0x8000;
    mem_Unlock(h);
    if (!(h = mem_Realloc(h, (long)(n + 1) << 3, 1)))
        Punt("Clip out of memory!!!");
    clip_reset_temporary_state();
    g_5AAC = fd_50F6_3C14;
    _fmemcpy(g_5AAC, mem_Lock(h), (n + 1) << 3);
    mem_Unlock(h);
    mem_Free(h);
    f_1E57_0006(n, 1);
}

void far clip_restrict_rect(struct Rect far *r)
{
    clip_SubInclude(r);
}

void far clip_SubExclude(struct Rect far *r)
{
    Handle h;
    struct Rect far *buf;
    struct Rect far *p;
    int n;

    if (r) {
        h = mem_Alloc(2048, 0, "subexclude");
        buf = (struct Rect far *)mem_Lock(h);
        if (!g_5AAC)
            g_5AAC = &g_5A9C;
        for (p = buf; g_5AAC->top != (int)0x8000; g_5AAC++)
            p = clip_split_rect(g_5AAC, r, 0L, p);
        if ((n = p - buf) >= 256)
            Punt("CL074:Temp clip overflow in SubExclude");
    } else
        Punt("Sub exclude NULL rect!!");
    f_1E57_0006(n, 1);
    buf[n].top = 0x8000;
    mem_Unlock(h);
    if (!(h = mem_Realloc(h, (long)(n + 1) << 3, 1)))
        Punt("Clip out of memory!!!");
    clip_reset_temporary_state();
    g_5AAC = fd_50F6_3C14;
    _fmemcpy(g_5AAC, mem_Lock(h), (n + 1) << 3);
    mem_Unlock(h);
    g_5742 = h;
}

void far f_1E57_0C1A(struct Rect far *r)
{
    clip_SubExclude(r);
}

void far f_1E57_0C2D(struct Rect far *r)
{
    Handle h;
    struct Rect far *buf;
    struct Rect far *p;
    struct Rect far *c;
    int n;

    if (r) {
        h = mem_Alloc(2048, 0, "include");
        buf = (struct Rect far *)mem_Lock(h);
        if (g_5AAC && g_5AAC->top != (int)0x8000) {
            for (c = g_5AAC, p = buf; c->top != (int)0x8000; c++, p++)
                *p = *c;
            for (; g_5AAC->top != (int)0x8000; g_5AAC++)
                p = clip_split_rect(r, g_5AAC, 0L, p);
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
    clip_reset_temporary_state();
    g_5AAC = fd_50F6_3C14;
    _fmemcpy(g_5AAC, buf, (n + 1) << 3);
    mem_Unlock(h);
    mem_Free(h);
}

void far f_1E57_0D97(struct Rect far *r)
{
    f_1E57_0C2D(r);
}

extern Handle far fd_50F6_3B5C;

void far clip_Push(void)
{
    struct Rect far *p;
    int size;
    Handle h;
    Handle far *node;

    size = 0;
    if ((p = g_5AAC) != 0) {
        for (; p->top != (int)0x8000; p++)
            ;
        size = (char far *)p - (char far *)g_5AAC + sizeof(struct Rect);
        g_5758 += size / (int)sizeof(struct Rect);
    }
    if (!(h = mem_Alloc(size + 8L, 1, "clip_Push")))
        Punt("Cannot allocate memory in clip_Push");
    node = (Handle far *)mem_Lock(h);
    if (size)
        _fmemcpy(node + 2, g_5AAC, size);
    node[0] = fd_50F6_3B5C;
    ((struct Rect far * far *)node)[1] = g_5AAC;
    fd_50F6_3B5C = h;
    if (++g_5756 > 20)
        Punt("Error CL98463: Pushed it too far");
    mem_Unlock(h);
}

void far clip_Pop(void)
{
    Handle far *node;
    struct Rect far *p;
    int size;

    if (!g_5756)
        Punt("Clip_Pop w/ nothing on the stack: E9073");
    clip_reset_temporary_state();
    g_5742 = fd_50F6_3B5C;
    node = (Handle far *)mem_Lock(g_5742);
    fd_50F6_3B5C = node[0];
    if (!((struct Rect far * far *)node)[1])
        g_5AAC = 0;
    else if ((p = g_5AAC = (struct Rect far *)(node + 2)) != 0) {
        for (; p->top != (int)0x8000; p++)
            ;
        size = (char far *)p - (char far *)g_5AAC + sizeof(struct Rect);
        _fmemcpy(fd_50F6_3C14, g_5AAC, size);
        g_5AAC = fd_50F6_3C14;
    }
    g_5756--;
    mem_Unlock(g_5742);
}

void far f_1E57_0F8E(struct Rect far *r)
{
    if (r->top >= g_5A9C.top && r->bottom <= g_5A9C.bottom &&
        r->left >= g_5A9C.left && r->right <= g_5A9C.right)
        clip_Off();
    else
        f_1E57_0351();
}


void far clip_set_screen_intersection(struct Rect far *r)
{
    if (r) {
        clip_reset_temporary_state();
        g_5AAC = fd_50F6_3C14;
        clip_split_rect(r, &g_5A9C, fd_50F6_3C14, 0L);
    }
}
