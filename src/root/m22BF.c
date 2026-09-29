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

extern int far f_24AB_0329(char far *text);
extern int far f_24AB_030B(void);

struct Pt _fastcall f_22BF_000A(char far *text)
{
    struct Pt size;

    size.x = f_24AB_0329(text);
    size.y = f_24AB_030B();
    return size;
}

extern void _fastcall f_23AE_0377(int win);
extern char far * far f_2505_0006(int win);
extern void _fastcall f_23AE_01DB(int win);

void _fastcall f_22BF_0042(int obj, struct Pt far *size)
{
    char far *w;
    struct Rect r;

    f_23AE_0377(obj);
    w = f_2505_0006(obj);
    r = *((struct Rect far * far *)(w + 0x2c))[obj & 0xff];
    size->x = r.right - r.left;
    size->y = r.bottom - r.top;
    f_23AE_01DB(obj);
}

extern char far * _fastcall win_ObjAddr(int obj);

void _fastcall f_22BF_00AA(int obj, struct Rect far *r)
{
    f_23AE_0377(obj);
    *r = *(struct Rect far *)(win_ObjAddr(obj) + 8);
    f_23AE_01DB(obj);
}

void _fastcall f_22BF_00DD(int obj, struct Rect far *r)
{
    f_23AE_0377(obj);
    *(struct Rect far *)(win_ObjAddr(obj) + 8) = *r;
    f_23AE_01DB(obj);
}

extern int g_5702[];
extern void far f_1FD2_03EB(char far *obj, int objNum);
extern void far f_1FD2_0438(int objNum);

void _fastcall f_22BF_011F(int obj, int state)
{
    unsigned char far *o;

    f_23AE_0377(obj);
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
    f_23AE_01DB(obj);
}

void _fastcall f_22BF_01A9(int win, int group, int state)
{
    char far *w;
    int i;
    int objNum;
    unsigned char far *o;

    f_23AE_0377(win);
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
    f_23AE_01DB(win);
}

void _fastcall f_22BF_0262(int win, int group)
{
    f_22BF_01A9(win, group, 1);
}

void _fastcall f_22BF_026A(int win, int group)
{
    f_22BF_01A9(win, group, 0);
}

extern void far f_1CE2_0430(char far *rect);

/* SCAFFOLD BEGIN: f_22BF_0271 (win_ObjInv) draft.
   Residue: bytes exact only with 9, 12 or 13 more identifiers declared before it
   (symbol-table count): the index is then built as mov si,[bp-2]; and si,0FFh
   instead of mov bl,[bp-2]; sub bh,bh; ...; mov si,bx. */
void _fastcall f_22BF_0271(int obj)
{
    char far *w;

    f_23AE_0377(obj);
    w = f_2505_0006(obj);
    f_1CE2_0430(((char far * far *)(w + 0x2c))[obj & 0xff]);
    f_23AE_01DB(obj);
}
/* SCAFFOLD END */

int _fastcall f_22BF_09B0(int win);
extern void _fastcall win_DrawBitMapAtObj(int id, char far *obj);
extern void _fastcall f_21FA_0741(char far *obj);

void _fastcall f_22BF_02AF(int obj, int selected)
{
    char far *o;

    f_23AE_0377(obj);
    o = win_ObjAddr(obj);
    if (f_22BF_09B0(obj) && ((*(unsigned far *)(o + 0x24) & 4) >> 2) != selected) {
        *(unsigned far *)(o + 0x24) ^= (*(unsigned far *)(o + 0x24) ^ (selected << 2)) & 4;
        if (*(unsigned far *)(o + 0x24) & 1) {
            if (o[0x21] == 13)
                win_DrawBitMapAtObj(*(int far *)(o + 0x26 + ((*(unsigned far *)(o + 0x24) & 4) == 0 ? 4 : 2)), o);
            else if (o[0x21] == 5 || o[0x21] == 17)
                f_21FA_0741(o);
            else
                f_1CE2_0430(o);
        }
    }
    *(unsigned far *)(o + 0x24) ^= (*(unsigned far *)(o + 0x24) ^ (selected << 2)) & 4;
    f_23AE_01DB(obj);
}

void _fastcall f_22BF_03CD(int win, int group, int selected);

void _fastcall f_22BF_0375(int obj, int selected)
{
    unsigned char far *o;

    f_23AE_0377(obj);
    o = (unsigned char far *)win_ObjAddr(obj);
    if (o[0x24] & 0x20)
        f_22BF_03CD(obj, o[0x20], 0);
    f_22BF_02AF(obj, selected);
    f_23AE_01DB(obj);
}

void _fastcall f_22BF_03BE(int obj)
{
    f_22BF_0375(obj, 1);
}

void _fastcall f_22BF_03C6(int obj)
{
    f_22BF_0375(obj, 0);
}

void _fastcall f_22BF_03CD(int win, int group, int selected)
{
    char far *w;
    int i;
    int objNum;

    f_23AE_0377(win);
    w = f_2505_0006(win);
    objNum = win & 0xff00;
    for (i = 0; i < *(int far *)(w + 0xc); i++, objNum++) {
        if (((unsigned char far * far *)(w + 0x2c))[i][0x20] == group)
            f_22BF_02AF(objNum, selected);
    }
    f_23AE_01DB(win);
}

void _fastcall f_22BF_0440(int win, int group)
{
    f_22BF_03CD(win, group, 0);
}

void _fastcall f_22BF_0447(int obj, int visible)
{
    unsigned char far *o;

    o = (unsigned char far *)win_ObjAddr(obj);
    if ((o[0x24] & 1) != visible) {
        *(unsigned far *)(o + 0x24) ^= (o[0x24] ^ visible) & 1;
        if ((o[0x24] & 4) && o[0x21] == 1)
            f_1CE2_0430((char far *)o);
    }
}

void _fastcall f_22BF_0498(int obj)
{
    f_22BF_0447(obj, 1);
}

void _fastcall f_22BF_04A0(int obj)
{
    f_22BF_0447(obj, 0);
}

void _fastcall f_22BF_04A7(int win, int group, int visible)
{
    char far *w;
    int i;
    int objNum;
    unsigned char far *o;

    f_23AE_0377(win);
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
    f_23AE_01DB(win);
}

void _fastcall f_22BF_0546(int win, int group)
{
    f_22BF_04A7(win, group, 1);
}

void _fastcall f_22BF_054E(int win, int group)
{
    f_22BF_04A7(win, group, 0);
}

extern char far * far _fstrrchr(char far *s, int c);
extern char far * far _fstrcpy(char far *dst, char far *src);

void _fastcall f_22BF_0555(int obj, char far *text)
{
    char far *p;

    p = _fstrrchr(win_ObjAddr(obj) + 0x28, ' ');
    if (p)
        _fstrcpy(p + 1, text);
}

extern int far vsprintf(char far *buffer, char far *format, char far *args);
extern int far WinPrintf(char far *format, ...);
extern unsigned int far _fstrlen(char far *s);
extern char far * far * far f_171C_18A6(char far * far *handle, long size, int flags);
extern char far * far * far f_171C_13CA(long size, int flags, char far *name);
extern char far * far f_171C_1B84(char far * far *handle);
extern void far f_171C_1BBA(char far * far *handle);

void far f_22BF_059A(int obj, ...)
{
    char far *o;
    char buf[100];
    int len;
    char far * far *rec;

    f_23AE_0377(obj);
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
    f_23AE_01DB(obj);
}

extern void _fastcall win_SetColorFromObjNum(int obj);
extern void _fastcall win_GetObjRect(int obj, struct Rect far *rect);
extern void far f_1E57_0DAA(void);
extern void far f_1E57_0773(struct Rect far *rect);
extern void far f_208F_011F(struct Rect far *rect, char far *text);
extern void far f_1E57_0EB9(void);

void far f_22BF_06BE(int obj, char far *text)
{
    struct Rect r;

    win_SetColorFromObjNum(obj);
    win_GetObjRect(obj, &r);
    f_1E57_0DAA();
    f_1E57_0773(&r);
    f_208F_011F(&r, text);
    f_1E57_0EB9();
}

extern void far f_24AB_02AD(int font);

void far f_22BF_0706(int obj, ...)
{
    char far *o;
    char buf[100];
    int len;
    char far * far *rec;

    f_23AE_0377(obj);
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
    f_22BF_06BE(obj, buf);
    f_24AB_02AD(0);
    f_171C_1BBA(rec);
    f_23AE_01DB(obj);
}

extern char far * far * far db_LoadObject(int object, int kind);
extern char near g_5A97;
extern void far f_1B4E_01A1(char far *pal, int count);
extern void far f_1B4E_01AE(char far *pal, int count);
extern void far db_ReleaseObject(int object, int kind);

int _fastcall f_22BF_085A(int id)
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

extern void far Punt(char far *format, ...);

void _fastcall f_22BF_0967(int obj, int bitmap)
{
    char far *o;

    f_23AE_0377(obj);
    o = win_ObjAddr(obj);
    if (o[0x21] != 6)
        Punt("Attempt to set bitmap on non-bitmap object");
    *(int far *)(o + 0x28) = bitmap;
    f_23AE_01DB(obj);
}

extern char far * far * near g_9230[];

int _fastcall f_22BF_09B0(int win)
{
    int open;
    char far * far *h;
    char far *w;

    open = 0;
    if ((h = g_9230[win >> 8]) != 0) {
        if ((w = f_171C_1B84(h)) != 0) {
            open = (*(unsigned far *)(w + 0x1c) & 0x200) >> 9;
            f_171C_1BBA(h);
        } else {
            g_9230[win >> 8] = 0;
        }
    }
    return open;
}

int _fastcall f_22BF_0A22(int win)
{
    if (g_5702[0] == win)
        return 1;
    return 0;
}

int _fastcall f_22BF_0A34(int win)
{
    int r;

    f_23AE_0377(win);
    r = (*(unsigned far *)(f_2505_0006(win) + 0x1c) & 0x40) >> 6;
    f_23AE_01DB(win);
    return r;
}

int _fastcall f_22BF_0A65(int win)
{
    int r;

    f_23AE_0377(win);
    r = (*(unsigned far *)(f_2505_0006(win) + 0x1c) & 0x80) >> 7;
    f_23AE_01DB(win);
    return r;
}

int _fastcall f_22BF_0A97(int obj)
{
    int r;

    f_23AE_0377(obj);
    r = (*(unsigned far *)(win_ObjAddr(obj) + 0x24) & 2) >> 1;
    f_23AE_01DB(obj);
    return r;
}

int _fastcall f_22BF_0AC5(int win)
{
    int n;

    f_23AE_0377(win);
    n = *(int far *)(f_2505_0006(win) + 0xc);
    f_23AE_01DB(win);
    return n;
}

int _fastcall f_22BF_0AEF(int win)
{
    char far *w;
    int r;

    f_23AE_0377(win);
    w = f_2505_0006(win);
    r = (*(unsigned far *)(w + 0x1c) & 0x40) >> 6;
    *(unsigned far *)(w + 0x1c) |= 0x40;
    f_23AE_01DB(win);
    return r;
}

int _fastcall f_22BF_0B25(int win)
{
    char far *w;
    int r;

    f_23AE_0377(win);
    w = f_2505_0006(win);
    r = (*(unsigned far *)(w + 0x1c) & 0x40) >> 6;
    *(unsigned far *)(w + 0x1c) &= ~0x40;
    f_23AE_01DB(win);
    return r;
}

void _fastcall f_22BF_0B5B(struct Rect far *dst, struct Rect far *src, int l, int t, int r, int b)
{
    dst->left = src->left + l;
    dst->right = src->right + r;
    dst->top = src->top + t;
    dst->bottom = src->bottom + b;
}

extern void far f_20E8_04B6(int win, int p0, int p1);
extern void _fastcall f_218D_01F6(int obj);
extern void far f_1FD2_057F(void);
extern int far f_1FD2_0598(void);
extern int far f_218D_01F2(void);

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

extern int _fastcall f_218D_03F1(struct Event far *ev);
extern void _fastcall f_20E8_0635(int win);

/* SCAFFOLD BEGIN: f_22BF_0BAB draft (modal dialog loop).
   Residue: symbol-table count; with +12 identifiers before 0271, +5 before 04A7
   and +14 before this function the whole module is exact (result = -1 lives in DI,
   copied to [bp-2] before the loop). 144 vs 141 bytes as is. */
int far f_22BF_0BAB(int win, int item, int p0, int p1)
{
    int result;
    int last;
    struct Event ev;

    result = -1;
    f_20E8_04B6(win, p0, p1);
    if (item != -1)
        f_218D_01F6(win + item + 2);
    f_1FD2_057F();
    last = -1;
    for (;;) {
        if (!f_22BF_09B0(win))
            break;
        if (!f_1FD2_0598())
            ev.code = f_218D_01F2();
        else if (!f_218D_03F1(&ev))
            continue;
        if ((unsigned)ev.code < (unsigned)win || (unsigned)win + 0x100 <= (unsigned)ev.code)
            continue;
        if ((unsigned)win + 2 <= (unsigned)ev.code)
            result = ev.code - win - 2;
        break;
    }
    f_20E8_0635(win);
    return result;
}
/* SCAFFOLD END */

extern char far fd_50F6_46E2[][6];
extern struct Pt g_3DA0;
extern void (far * near g_9134)(int left, int top, int right, int bottom, int color);

void far f_22BF_0C38(int obj)
{
    struct Rect r;
    int c;
    int top;
    int left;

    f_23AE_0377(obj);
    win_GetObjRect(obj, &r);
    c = win_ObjAddr(obj)[0x26];
    if (g_5A97 & 1)
        c = fd_50F6_46E2[c][3];
    else
        c = fd_50F6_46E2[c][2];
    c = (c << 8) | (c & 0xff);
    top = g_3DA0.y;
    if (top < r.top)
        top = r.top;
    if (r.bottom > top && (left = g_3DA0.x) >= r.left && r.right > left)
        (*g_9134)(left, top, r.right, r.bottom, c);
    f_23AE_01DB(obj);
}

void far f_22BF_0CDD(int obj)
{
    struct Rect r;
    int c;

    f_23AE_0377(obj);
    win_GetObjRect(obj, &r);
    c = win_ObjAddr(obj)[0x26];
    c = fd_50F6_46E2[c][2];
    c = (c & 0xf) | (((c & 0xf) << 4) | (c << 8));
    (*g_9134)(r.left, r.top, r.right, r.bottom, c);
    f_23AE_01DB(obj);
}

void far f_22BF_0D53(int obj, char far *format, ...)
{
    char buf[100];

    vsprintf(buf, format, (char far *)(&format + 1));
    f_22BF_06BE(obj, buf);
}

extern void far f_1CE2_046D(struct Rect far *rect, int color);
extern int near g_3DE0;
extern int near g_3DE2;

void far f_22BF_0D81(int obj, long fraction)
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
    if (r.right > r.left)
        f_1CE2_046D(&r, g_3DE0);
    if (r.right < right) {
        r.left = r.right;
        r.right = right;
        f_1CE2_046D(&r, g_3DE2);
    }
}

void far f_22BF_0E01(int obj, long fraction)
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

extern void _fastcall f_2505_0545(int win);

void far f_22BF_0E83(int src, int dst)
{
    int far *o;
    struct Rect r;

    f_23AE_0377(src);
    f_23AE_0377(dst);
    o = (int far *)(win_ObjAddr(dst) + 8);
    r = *(struct Rect far *)(win_ObjAddr(src) + 8);
    o[0] = r.left;
    o[1] = r.top;
    f_2505_0545(dst);
    f_23AE_01DB(src);
    f_23AE_01DB(dst);
}
