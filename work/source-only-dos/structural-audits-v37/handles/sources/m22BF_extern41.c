/* Root module 22BF: window object attribute and drawing helpers. */

struct Pt {
    int x;
    int y;
};

struct Rect {
    int left;
    int top;
    int right;
    int bottom;
};

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

extern int far f_24AB_0329(char far *text);
extern int far f_24AB_030B(void);
extern void _fastcall win_LockWin(int win);
extern char far * far f_2505_0006(int win);
extern void _fastcall win_UnlockWin(int win);
extern char far * _fastcall win_ObjAddr(int obj);
extern int g_5702[];
extern void far f_1FD2_03EB(char far *obj, int objNum);
extern void far f_1FD2_0438(int objNum);
extern void far f_1CE2_0430(char far *rect);
int _fastcall win_IsWinOpen(int win);
extern void _fastcall win_DrawBitMapAtObj(int id, char far *obj);
extern void _fastcall win_DrawObject(char far *obj);
void _fastcall win_SetGroupSelectedState(int win, int group, int selected);
extern char far * far _fstrrchr(char far *s, int c);
extern char far * far _fstrcpy(char far *dst, char far *src);
extern int far vsprintf(char far *buffer, char far *format, char far *args);
extern int far WinPrintf(char far *format, ...);
extern unsigned int far _fstrlen(char far *s);
extern char far * far * far f_171C_18A6(char far * far *handle, long size, int flags);
extern char far * far * far f_171C_13CA(long size, int flags, char far *name);
extern char far * far f_171C_1B84(char far * far *handle);
extern void far f_171C_1BBA(char far * far *handle);
extern void _fastcall win_SetColorFromObjNum(int obj);
extern void _fastcall win_GetObjRect(int obj, struct Rect far *rect);
extern void far clip_Push(void);
extern void far clip_SubInclude(struct Rect far *rect);
extern void far f_208F_011F(struct Rect far *rect, char far *text);
extern void far clip_Pop(void);
extern void far f_24AB_02AD(int font);
extern char far * far * far db_LoadObject(int object, int kind);
extern char near g_5A97;
extern void far f_1B4E_01A1(char far *pal, int count);
extern void far f_1B4E_01AE(char far *pal, int count);
extern void far db_ReleaseObject(int object, int kind);
extern void far Punt(char far *format, ...);
extern char far * far * near win_handles[41];
extern void far win_Open(int win, int p0, int p1);
extern void _fastcall _win_SetProxItem(int obj);
extern void far ButtonHeldInit(void);
extern int far ButtonHeld(void);
extern int far win_GetProxEvent(void);
extern int _fastcall win_GetEvent(struct Event far *ev);
extern void _fastcall win_Close(int win);
extern char far win_colors[][6];
extern struct Pt g_3DA0;
extern void (far * near g_9134)(int left, int top, int right, int bottom, int color);
extern void far f_1CE2_046D(struct Rect far *rect, int color);
extern int near g_3DE0;
extern int near g_3DE2;
extern void _fastcall win_Recalc(int win);

struct Pt _fastcall win_StringSize(char far *);
void _fastcall win_GetObjSize(int, struct Pt far *);
void _fastcall f_22BF_00AA(int, struct Rect far *);
void _fastcall f_22BF_00DD(int, struct Rect far *);
void _fastcall win_SetObjSelectableState(int, int);
void _fastcall win_MakeObjSelectable(int);
void _fastcall win_MakeObjUnselectable(int);
void _fastcall win_SetGroupSelectableState(int, int, int);
void _fastcall win_MakeGroupSelectable(int, int);
void _fastcall win_MakeGroupUnselectable(int, int);
void _fastcall win_ObjInv(int);
void _fastcall win_SetObjSelectedStateI(int, int);
void _fastcall win_SetObjSelectedState(int, int);
void _fastcall win_MakeObjSelected(int);
void _fastcall win_MakeObjUnselected(int);
void _fastcall win_SetGroupSelectedState(int, int, int);
void _fastcall win_MakeGroupSelected(int, int);
void _fastcall win_MakeGroupUnselected(int, int);
void _fastcall win_SetObjVisibleState(int, int);
void _fastcall win_MakeObjVisible(int);
void _fastcall win_MakeObjInvisible(int);
void _fastcall win_SetGroupVisibleState(int, int, int);
void _fastcall win_MakeGroupVisible(int, int);
void _fastcall win_MakeGroupInvisible(int, int);
void _fastcall f_22BF_0555(int, char far *);
void far win_SetObjFormatStr(int, ...);
void far win_CenterStrAtObj(int, char far *);
void far win_ObjFormatPrint(int, ...);
int _fastcall win_SetPalette(int);
void _fastcall f_22BF_094F(int, int);
void _fastcall win_SetObjBitmap(int, int);
int _fastcall win_IsWinOpen(int);
int _fastcall win_IsWinInFront(int);
int _fastcall f_22BF_0A34(int);
int _fastcall f_22BF_0A65(int);
int _fastcall f_22BF_0A97(int);
int _fastcall f_22BF_0AC5(int);
int _fastcall f_22BF_0AEF(int);
int _fastcall f_22BF_0B25(int);
void _fastcall f_22BF_0B5B(struct Rect far *, struct Rect far *, int, int, int, int);
int far win_DoProxMenu(int, int, ...);
void far f_22BF_0C38(int);
void far f_22BF_0CDD(int);
void far win_PrintfAtObj(int, char far *, ...);
void far win_DrawHBar(int, long);
void far win_DrawVBar(int, long);
void far f_22BF_0E83(int, int);

struct Pt _fastcall win_StringSize(char far *text)
{
    struct Pt size;

    size.x = f_24AB_0329(text);
    size.y = f_24AB_030B();
    return size;
}

void _fastcall win_GetObjSize(int obj, struct Pt far *size)
{
    char far *w;
    struct Rect r;

    win_LockWin(obj);
    w = f_2505_0006(obj);
    r = *((struct Rect far * far *)(w + 0x2c))[obj & 0xff];
    size->x = r.right - r.left;
    size->y = r.bottom - r.top;
    win_UnlockWin(obj);
}

void _fastcall f_22BF_00AA(int obj, struct Rect far *r)
{
    win_LockWin(obj);
    *r = *(struct Rect far *)(win_ObjAddr(obj) + 8);
    win_UnlockWin(obj);
}

void _fastcall f_22BF_00DD(int obj, struct Rect far *r)
{
    win_LockWin(obj);
    *(struct Rect far *)(win_ObjAddr(obj) + 8) = *r;
    win_UnlockWin(obj);
}

void _fastcall win_SetObjSelectableState(int obj, int state)
{
    unsigned char far *o;

    win_LockWin(obj);
    o = (unsigned char far *)win_ObjAddr(obj);
    if (g_5702[0] == (obj & 0xff00)) {
        if (state == 1) {
            if (!(o[0x24] & 2))
                f_1FD2_03EB((char far *)o, obj);
        } else if (o[0x24] & 2) {
            f_1FD2_0438(obj);
        }
    }
    *(unsigned far *)(o + 0x24) ^= (o[0x24] ^ (state << 1)) & 2;
    win_UnlockWin(obj);
}

void _fastcall win_MakeObjSelectable(int obj)
{
    win_SetObjSelectableState(obj, 1);
}

void _fastcall win_MakeObjUnselectable(int obj)
{
    win_SetObjSelectableState(obj, 0);
}

void _fastcall win_SetGroupSelectableState(int win, int group, int state)
{
    char far *w;
    int i;
    int objNum;
    unsigned char far *o;

    win_LockWin(win);
    objNum = win & 0xff00;
    w = f_2505_0006(win);
    for (i = 0; i < *(int far *)(w + 0xc); i++, objNum++) {
        o = ((unsigned char far * far *)(w + 0x2c))[i];
        if (o[0x20] == group) {
            if (g_5702[0] == win) {
                if (state == 1) {
                    if (!(o[0x24] & 2))
                        f_1FD2_03EB((char far *)o, objNum);
                } else if (o[0x24] & 2) {
                    f_1FD2_0438(objNum);
                }
            }
            *(unsigned far *)(o + 0x24) ^= (o[0x24] ^ (state << 1)) & 2;
        }
    }
    win_UnlockWin(win);
}

void _fastcall win_MakeGroupSelectable(int win, int group)
{
    win_SetGroupSelectableState(win, group, 1);
}

void _fastcall win_MakeGroupUnselectable(int win, int group)
{
    win_SetGroupSelectableState(win, group, 0);
}

void _fastcall win_ObjInv(int obj)
{
    char far *w;

    win_LockWin(obj);
    w = f_2505_0006(obj);
    f_1CE2_0430(((char far * far *)(w + 0x2c))[obj & 0xff]);
    win_UnlockWin(obj);
}

void _fastcall win_SetObjSelectedStateI(int obj, int selected)
{
    char far *o;

    win_LockWin(obj);
    o = win_ObjAddr(obj);
    if (win_IsWinOpen(obj) && ((*(unsigned far *)(o + 0x24) & 4) >> 2) != selected) {
        *(unsigned far *)(o + 0x24) ^= (*(unsigned far *)(o + 0x24) ^ (selected << 2)) & 4;
        if (*(unsigned far *)(o + 0x24) & 1) {
            if (o[0x21] == 13)
                win_DrawBitMapAtObj(*(int far *)(o + 0x26 + ((*(unsigned far *)(o + 0x24) & 4) == 0 ? 4 : 2)), o);
            else if (o[0x21] == 5 || o[0x21] == 17)
                win_DrawObject(o);
            else
                f_1CE2_0430(o);
        }
    }
    *(unsigned far *)(o + 0x24) ^= (*(unsigned far *)(o + 0x24) ^ (selected << 2)) & 4;
    win_UnlockWin(obj);
}

void _fastcall win_SetObjSelectedState(int obj, int selected)
{
    unsigned char far *o;

    win_LockWin(obj);
    o = (unsigned char far *)win_ObjAddr(obj);
    if (o[0x24] & 0x20)
        win_SetGroupSelectedState(obj, o[0x20], 0);
    win_SetObjSelectedStateI(obj, selected);
    win_UnlockWin(obj);
}

void _fastcall win_MakeObjSelected(int obj)
{
    win_SetObjSelectedState(obj, 1);
}

void _fastcall win_MakeObjUnselected(int obj)
{
    win_SetObjSelectedState(obj, 0);
}

void _fastcall win_SetGroupSelectedState(int win, int group, int selected)
{
    char far *w;
    int i;
    int objNum;

    win_LockWin(win);
    w = f_2505_0006(win);
    objNum = win & 0xff00;
    for (i = 0; i < *(int far *)(w + 0xc); i++, objNum++) {
        if (((unsigned char far * far *)(w + 0x2c))[i][0x20] == group)
            win_SetObjSelectedStateI(objNum, selected);
    }
    win_UnlockWin(win);
}

void _fastcall win_MakeGroupSelected(int win, int group)
{
    win_SetGroupSelectedState(win, group, 1);
}

void _fastcall win_MakeGroupUnselected(int win, int group)
{
    win_SetGroupSelectedState(win, group, 0);
}

void _fastcall win_SetObjVisibleState(int obj, int visible)
{
    unsigned char far *o;

    o = (unsigned char far *)win_ObjAddr(obj);
    if ((o[0x24] & 1) != visible) {
        *(unsigned far *)(o + 0x24) ^= (o[0x24] ^ visible) & 1;
        if ((o[0x24] & 4) && o[0x21] == 1)
            f_1CE2_0430((char far *)o);
    }
}

void _fastcall win_MakeObjVisible(int obj)
{
    win_SetObjVisibleState(obj, 1);
}

void _fastcall win_MakeObjInvisible(int obj)
{
    win_SetObjVisibleState(obj, 0);
}

void _fastcall win_SetGroupVisibleState(int win, int group, int visible)
{
    char far *w;
    int i;
    int objNum;
    unsigned char far *o;

    win_LockWin(win);
    w = f_2505_0006(win);
    objNum = win;
    for (i = 0; i < *(int far *)(w + 0xc); i++, objNum++) {
        o = ((unsigned char far * far *)(w + 0x2c))[i];
        if (o[0x20] == group && (o[0x24] & 1) != visible) {
            *(unsigned far *)(o + 0x24) ^= (o[0x24] ^ visible) & 1;
            if ((o[0x24] & 4) && o[0x21] != 13 && o[0x21] != 5)
                f_1CE2_0430((char far *)o);
        }
    }
    win_UnlockWin(win);
}

void _fastcall win_MakeGroupVisible(int win, int group)
{
    win_SetGroupVisibleState(win, group, 1);
}

void _fastcall win_MakeGroupInvisible(int win, int group)
{
    win_SetGroupVisibleState(win, group, 0);
}

void _fastcall f_22BF_0555(int obj, char far *text)
{
    char far *p;

    p = _fstrrchr(win_ObjAddr(obj) + 0x28, ' ');
    if (p)
        _fstrcpy(p + 1, text);
}

void far win_SetObjFormatStr(int obj, ...)
{
    char far *o;
    char buf[100];
    int len;
    char far * far *rec;

    win_LockWin(obj);
    vsprintf(buf, (o = win_ObjAddr(obj)) + 0x2e, (char far *)(&obj + 1));
    WinPrintf("\n= %s", (char far *)buf);
    vsprintf(buf, o + 0x2e, (char far *)(&obj + 1));
    len = _fstrlen(buf) + 1;
    if ((rec = *(char far * far * far *)(o + 0x2a)) != 0) {
        if (_fstrlen(*rec) + 1 < len) {
            rec = f_171C_18A6(rec, (long)(len + 4), 1);
            *(char far * far * far *)(o + 0x2a) = rec;
        }
    } else {
        rec = f_171C_13CA((long)(len + 8), 1, "formatStr");
        *(char far * far * far *)(o + 0x2a) = rec;
    }
    _fstrcpy(f_171C_1B84(rec), buf);
    f_171C_1BBA(rec);
    win_UnlockWin(obj);
}

void far win_CenterStrAtObj(int obj, char far *text)
{
    struct Rect r;

    win_SetColorFromObjNum(obj);
    win_GetObjRect(obj, &r);
    clip_Push();
    clip_SubInclude(&r);
    f_208F_011F(&r, text);
    clip_Pop();
}

void far win_ObjFormatPrint(int obj, ...)
{
    char far *o;
    char buf[100];
    int len;
    char far * far *rec;

    win_LockWin(obj);
    vsprintf(buf, (o = win_ObjAddr(obj)) + 0x2e, (char far *)(&obj + 1));
    WinPrintf("\n= %s", (char far *)buf);
    vsprintf(buf, o + 0x2e, (char far *)(&obj + 1));
    len = _fstrlen(buf) + 1;
    if ((rec = *(char far * far * far *)(o + 0x2a)) != 0) {
        if (_fstrlen(*rec) + 2 < len) {
            rec = f_171C_18A6(rec, (long)(len + 4), 1);
            *(char far * far * far *)(o + 0x2a) = rec;
        }
    } else {
        rec = f_171C_13CA((long)(len + 8), 1, "formatStr");
        *(char far * far * far *)(o + 0x2a) = rec;
    }
    _fstrcpy(f_171C_1B84(rec), buf);
    f_24AB_02AD(o[0x28]);
    win_CenterStrAtObj(obj, buf);
    f_24AB_02AD(0);
    f_171C_1BBA(rec);
    win_UnlockWin(obj);
}

int _fastcall win_SetPalette(int id)
{
    char far * far *h;
    char far *p;
    char far *q;
    int i;
    char pal[18];

    h = db_LoadObject(id, 0xf);
    if (h == 0)
        return 0;
    p = *h;
    switch (p[1]) {
    case 0:
        if (g_5A97 == 0) {
            q = p + 2;
            for (i = 0; i < 16; q += 3, i++)
                pal[i] = ((((q[0] & 0x10) | ((((q[1] & 0x10) | ((q[2] & 0x10) >> 1)) >> 1) | (q[2] & 0x20))) >> 1 | (q[1] & 0x20)) >> 1) | (q[0] & 0x20);
            pal[17] = 0;
            f_1B4E_01A1(pal, p[0]);
        } else if (g_5A97 == 8) {
            f_1B4E_01AE(p + 2, p[0]);
        }
        break;
    case 1:
        f_1B4E_01A1(p + 2, p[0]);
        break;
    }
    db_ReleaseObject(id, 0xf);
}

void _fastcall f_22BF_094F(int obj, int color)
{
    win_ObjAddr(obj)[0x26] = color;
}

void _fastcall win_SetObjBitmap(int obj, int bitmap)
{
    char far *o;

    win_LockWin(obj);
    o = win_ObjAddr(obj);
    if (o[0x21] != 6)
        Punt("Attempt to set bitmap on non-bitmap object");
    *(int far *)(o + 0x28) = bitmap;
    win_UnlockWin(obj);
}

int _fastcall win_IsWinOpen(int win)
{
    int open;
    char far * far *h;
    char far *w;

    open = 0;
    if ((h = win_handles[win >> 8]) != 0) {
        if ((w = f_171C_1B84(h)) != 0) {
            open = (*(unsigned far *)(w + 0x1c) & 0x200) >> 9;
            f_171C_1BBA(h);
        } else {
            win_handles[win >> 8] = 0;
        }
    }
    return open;
}

int _fastcall win_IsWinInFront(int win)
{
    if (g_5702[0] == win)
        return 1;
    return 0;
}

int _fastcall f_22BF_0A34(int win)
{
    int r;

    win_LockWin(win);
    r = (*(unsigned far *)(f_2505_0006(win) + 0x1c) & 0x40) >> 6;
    win_UnlockWin(win);
    return r;
}

int _fastcall f_22BF_0A65(int win)
{
    int r;

    win_LockWin(win);
    r = (*(unsigned far *)(f_2505_0006(win) + 0x1c) & 0x80) >> 7;
    win_UnlockWin(win);
    return r;
}

int _fastcall f_22BF_0A97(int obj)
{
    int r;

    win_LockWin(obj);
    r = (*(unsigned far *)(win_ObjAddr(obj) + 0x24) & 2) >> 1;
    win_UnlockWin(obj);
    return r;
}

int _fastcall f_22BF_0AC5(int win)
{
    int n;

    win_LockWin(win);
    n = *(int far *)(f_2505_0006(win) + 0xc);
    win_UnlockWin(win);
    return n;
}

int _fastcall f_22BF_0AEF(int win)
{
    char far *w;
    int r;

    win_LockWin(win);
    w = f_2505_0006(win);
    r = (*(unsigned far *)(w + 0x1c) & 0x40) >> 6;
    *(unsigned far *)(w + 0x1c) |= 0x40;
    win_UnlockWin(win);
    return r;
}

int _fastcall f_22BF_0B25(int win)
{
    char far *w;
    int r;

    win_LockWin(win);
    w = f_2505_0006(win);
    r = (*(unsigned far *)(w + 0x1c) & 0x40) >> 6;
    *(unsigned far *)(w + 0x1c) &= ~0x40;
    win_UnlockWin(win);
    return r;
}

void _fastcall f_22BF_0B5B(struct Rect far *dst, struct Rect far *src, int l, int t, int r, int b)
{
    dst->left = src->left + l;
    dst->right = src->right + r;
    dst->top = src->top + t;
    dst->bottom = src->bottom + b;
}

int far win_DoProxMenu(int win, int item, ...)
{
    int result;
    int last;
    struct Event ev;

    result = -1;
    win_Open(win, (&item)[1], (&item)[2]);
    if (item != -1)
        _win_SetProxItem(win + item + 2);
    ButtonHeldInit();
    last = -1;
    for (;;) {
        if (!win_IsWinOpen(win))
            break;
        if (!ButtonHeld())
            ev.code = win_GetProxEvent();
        else if (!win_GetEvent(&ev))
            continue;
        if ((unsigned)ev.code < (unsigned)win || (unsigned)win + 0x100 <= (unsigned)ev.code)
            continue;
        if ((unsigned)win + 2 <= (unsigned)ev.code)
            result = ev.code - win - 2;
        break;
    }
    win_Close(win);
    return result;
}

void far f_22BF_0C38(int obj)
{
    struct Rect r;
    int c;
    int top;
    int left;

    win_LockWin(obj);
    win_GetObjRect(obj, &r);
    c = win_ObjAddr(obj)[0x26];
    if (g_5A97 & 1)
        c = win_colors[c][3];
    else
        c = win_colors[c][2];
    c = (c << 8) | (c & 0xff);
    top = g_3DA0.y;
    if (top < r.top)
        top = r.top;
    if (r.bottom > top && (left = g_3DA0.x) >= r.left && r.right > left)
        (*g_9134)(left, top, r.right, r.bottom, c);
    win_UnlockWin(obj);
}

void far f_22BF_0CDD(int obj)
{
    struct Rect r;
    int c;

    win_LockWin(obj);
    win_GetObjRect(obj, &r);
    c = win_ObjAddr(obj)[0x26];
    c = win_colors[c][2];
    c = (c & 0xf) | (((c & 0xf) << 4) | (c << 8));
    (*g_9134)(r.left, r.top, r.right, r.bottom, c);
    win_UnlockWin(obj);
}

void far win_PrintfAtObj(int obj, char far *format, ...)
{
    char buf[100];

    vsprintf(buf, format, (char far *)(&format + 1));
    win_CenterStrAtObj(obj, buf);
}

/* The label below is inferred from the relocation order (ZI-2): the original has a
   record break at 0DDD.  More counted line entries before it would explain it too. */
void far win_DrawHBar(int obj, long fraction)
{
    struct Rect r;
    int right;

    win_SetColorFromObjNum(obj);
    win_GetObjRect(obj, &r);
    {
        int end = r.right;
        long extent = (long)(end - r.left);
        right = end;
        r.right = r.left + (int)((extent * fraction) / 65536L);
    }
    if (r.right <= r.left)
        goto rest;
    f_1CE2_046D(&r, g_3DE0);
rest:
    if (r.right < right) {
        r.left = r.right;
        r.right = right;
        f_1CE2_046D(&r, g_3DE2);
    }
}

void far win_DrawVBar(int obj, long fraction)
{
    struct Rect r;
    int top;

    win_SetColorFromObjNum(obj);
    win_GetObjRect(obj, &r);
    {
        int end = r.bottom;
        int start = r.top;
        int height = end - start;
        top = start;
        r.top = end - (int)(((long)height * fraction) / 65536L);
    }
    if (r.top < r.bottom)
        f_1CE2_046D(&r, g_3DE0);
    if (r.top > top) {
        r.bottom = r.top;
        r.top = top;
        f_1CE2_046D(&r, g_3DE2);
    }
}

void far f_22BF_0E83(int src, int dst)
{
    int far *o;
    struct Rect r;

    win_LockWin(src);
    win_LockWin(dst);
    o = (int far *)(win_ObjAddr(dst) + 8);
    r = *(struct Rect far *)(win_ObjAddr(src) + 8);
    o[0] = r.left;
    o[1] = r.top;
    win_Recalc(dst);
    win_UnlockWin(src);
    win_UnlockWin(dst);
}
