/* Root module 2505: DOS window-object engine (partial). */

extern void far Punt(char far *format, ...);
extern int far WinPrintf(char far *format, ...);
extern unsigned int far _fstrlen(char far *s);
extern int _fastcall win_IsWinLocked(int win);
extern void _fastcall win_LockWin(int win);
extern void _fastcall win_UnlockWin(int win);

struct Rect {
    int left;
    int top;
    int right;
    int bottom;
};

struct Pt {
    int x;
    int y;
};

struct Win {
    struct Rect rect;
    char pad08[4];
    int count;
    char pad0E[0x1c - 0x0e];
    int flags;
    char pad1E[0x2c - 0x1e];
    char far *objs[1];
};

extern struct Pt _fastcall win_StringSize(char far *text);
extern void far f_208F_0419(struct Pt far *size, int id);

extern int g_6300;
extern int g_5702;
extern char far * far * far win_handles[];

char far * far f_2505_0006(int win)
{
    if (g_6300 == 0 && !win_IsWinLocked(win))
        Punt("\nWINDOW %x NOT LOCKED DURING CALL TO GETWINPTR!!", win);
    return *win_handles[win >> 8];
}

void _fastcall RepointObjects(int win)
{
    char far *w;
    int n;
    int i;
    char far *p;

    w = f_2505_0006(win);
    n = *(int far *)(w + 0xc);
    p = w + n * 4 + 0x2c;
    for (i = 0; i < n; i++) {
        ((char far * far *)(w + 0x2c))[i] = p;
        p += *(int far *)(p + 0x22);
    }
}

int _fastcall f_2505_00AA(int type)
{
    switch (type) {
    case 5:
    case 9:
    case 12:
    case 16:
    case 17:
    case 18:
        return 1;
    }
    return 0;
}

int _fastcall f_2505_00DD(char far *obj)
{
    int size;

    size = 0x28;
    switch (obj[0x21]) {
    case 0:
    case 2:
    case 15:
    case 19:
    case 20:
    case 21:
    case 22:
        size = 0x29;
        break;
    case 4:
        size = 0x38;
        break;
    case 5:
    case 9:
    case 12:
        size = _fstrlen(obj + 0x2a) + 0x2d;
        break;
    case 6:
    case 7:
    case 8:
        size = 0x2a;
        break;
    case 13:
        size = 0x2c;
        break;
    case 16:
    case 17:
    case 18:
        size = _fstrlen(obj + 0x2e) + 0x31;
        break;
    }
    return size;
}

struct Pt _fastcall win_AutoSize(char far *obj)
{
    static struct Pt size;

    switch (obj[0x21]) {
    default:
        size.x = *(int far *)(obj + 4) - *(int far *)obj;
        size.y = *(int far *)(obj + 6) - *(int far *)(obj + 2);
        break;
    case 5:
    case 12:
        size = win_StringSize(obj + 0x28);
        size.x += 8;
        size.y += 8;
        break;
    case 6:
    case 13:
        f_208F_0419(&size, *(int far *)(obj + 0x28));
        break;
    case 9:
        size = win_StringSize(obj + 0x28);
        break;
    case 16:
    case 18:
        size = win_StringSize(obj + 0x2c);
        break;
    case 17:
        size = win_StringSize(obj + 0x2c);
        size.x += 8;
        size.y += 8;
        break;
    }
    return size;
}

char far * _fastcall win_WinRectAddr(int win)
{
    if (!win_IsWinLocked(win))
        Punt("\nWINDOW %x NOT LOCKED DURING CALL TO win_WinRectAddr!!", win);
    return f_2505_0006(win);
}

void _fastcall win_GetObjRect(int obj, struct Rect far *rect)
{
    char far *w;

    win_LockWin(obj);
    w = f_2505_0006(obj);
    *rect = *((struct Rect far * far *)(w + 0x2c))[obj & 0xff];
    win_UnlockWin(obj);
}

char far * _fastcall win_ObjAddr(int obj)
{
    if (!win_IsWinLocked(obj))
        Punt("\nWINDOW %x NOT LOCKED DURING CALL TO win_ObjAddr!!", obj);
    if (*(int far *)(f_2505_0006(obj) + 0xc) <= (unsigned char)obj)
        Punt("Attempt to get obj address outsize window");
    return ((char far * far *)(f_2505_0006(obj) + 0x2c))[obj & 0xff];
}

char far * _fastcall f_2505_033C(int win, int obj)
{
    return win_ObjAddr((win & 0xff00) + obj);
}

char far * _fastcall win_WinAddr(int win)
{
    if (!win_IsWinLocked(win))
        WinPrintf("\nWINDOW %x NOT LOCKED DURING CALL TO win_WinAddr!!", win);
    return f_2505_0006(win);
}

int far f_2505_036E(void)
{
    if (g_5702 != (int)0x8000)
        return 1;
    return 0;
}

void _fastcall f_2505_0382(struct Pt far *center, struct Rect far *rect)
{
    center->x = (rect->right + rect->left) / 2;
    center->y = (rect->top + rect->bottom) / 2;
}

extern void far f_1F58_0090(void);
int _fastcall f_2505_0453(int obj, int kind);
int _fastcall f_2505_04D7(int win, int idx);

int _fastcall f_2505_03B9(int axis, int win, char far *obj)
{
    int v;
    int kind;

    switch (((int far *)(obj + 0x18))[axis]) {
    default:
        f_1F58_0090();
        return 1;
    case 0:
        v = 0;
        break;
    case 1:
        kind = 0;
        goto get;
    case 2:
        kind = 1;
        goto get;
    case 3:
        kind = 2;
        goto get;
    case 4:
        kind = 3;
    get:
        v = f_2505_0453(((int far *)(obj + 0x10))[axis], kind);
        break;
    case 5:
        v = f_2505_04D7(win, ((int far *)(obj + 0x10))[axis]);
        break;
    }
    if (v != (int)0x8000)
        return v + ((int far *)(obj + 8))[axis];
    return 0x8000;
}

extern int far win_numOfWindows;

extern char far * far f_171C_1B84(char far * far *handle);
extern void far f_171C_1BBA(char far * far *handle);
extern void far f_1FD2_0883(int x, int y, int id, int mode, int flag);
extern void far f_1FD2_03EB(char far *obj, int objNum);
extern void far f_1FD2_044F(char far *w, int id);
extern void far f_218D_01EB(void);
extern void far f_1FD2_0438(int objNum);
extern void far f_1FD2_049C(int id);
int _fastcall f_2505_0453(int obj, int kind)
{
    int win;
    int idx;
    char far *w;
    int far *r;

    win = obj & 0xff00;
    if ((win >> 8) < win_numOfWindows || win >= 0x2800) {
        win_LockWin(win);
        idx = obj & 0xff;
        w = f_2505_0006(win);
        if (*(int far *)(w + 0xc) > idx) {
            r = ((int far * far *)(w + 0x2c))[idx];
            win_UnlockWin(win);
            return r[kind];
        }
        win_UnlockWin(win);
    }
    return 0x8000;
}

int _fastcall f_2505_04D7(int win, int idx)
{
    if (win_numOfWindows <= (win >> 8) && win < 0x2800)
        return 0x8000;
    return ((int far *)(f_2505_0006(win) + 0x10))[idx];
}

void _fastcall f_2505_0511(struct Rect far *r)
{
    int t;

    t = r->left;
    if (t > r->right) {
        r->left = r->right;
        r->right = t;
    }
    t = r->top;
    if (t > r->bottom) {
        r->top = r->bottom;
        r->bottom = t;
    }
}

void _fastcall win_Recalc(int win);
void _fastcall f_2505_06B9(int flag, char far *w);
void _fastcall f_2505_0831(int win);
extern char far * far f_171C_1B84(char far * far *handle);
extern void far f_171C_1BBA(char far * far *handle);

void _fastcall win_Recalc(int win)
{
    char far * far *handle;
    char far *w;
    int n;
    int i;
    int changed;
    int unresolved;
    char far *obj;
    struct Pt size;
    int far *p;
    int k;
    int v;
    struct Rect far *r;

    handle = (char far * far *)win_handles[win >> 8];
    w = f_171C_1B84(handle);
    n = *(int far *)(w + 0xc);
    for (i = 0; i < n; i++) {
        r = ((struct Rect far * far *)(w + 0x2c))[i];
        r->left = r->right = r->top = r->bottom = 0x8000;
    }
    changed = 1;
    while (changed) {
        unresolved = 0;
        changed = 0;
        for (i = 0; i < n; i++) {
            obj = ((char far * far *)(w + 0x2c))[i];
            if (obj[0x24] & 0x40) {
                size = win_AutoSize(obj);
                ((int far *)obj)[6] = size.x;
                ((int far *)obj)[7] = size.y;
            }
            p = (int far *)obj;
            for (k = 0; k < 4; k++, p++) {
                v = f_2505_03B9(k, win, obj);
                if (*p != v) {
                    *p = v;
                    changed++;
                }
                if (v == (int)0x8000)
                    unresolved++;
            }
        }
    }
    for (i = 0; i < n; i++)
        f_2505_0511(((struct Rect far * far *)(w + 0x2c))[i]);
    *(struct Rect far *)w = *((struct Rect far * far *)(w + 0x2c))[0];
    f_171C_1BBA(handle);
}

extern void far f_1FD2_0883(int x, int y, int id, int mode, int flag);

void _fastcall f_2505_06B9(int flag, char far *w)
{
    int m;
    struct Pt size;
    struct Rect rect;

    rect = *(struct Rect far *)w;
    m = (*((char far * far *)(w + 0x2c)))[0x28];
    rect.left += m;
    rect.right -= m;
    rect.top += m;
    rect.bottom -= m;
    if (*(int far *)(w + 0x1c) & 4) {
        f_1FD2_0883(rect.left, rect.top, 0x64, 0xf083, flag);
        f_208F_0419(&size, 0x64);
        rect.left += size.x;
    }
    if (*(int far *)(w + 0x1c) & 8) {
        f_208F_0419(&size, 0x70);
        f_1FD2_0883(rect.right - size.x, rect.bottom - size.y, 0x70, 0xf084, flag);
    }
    if (*(int far *)(w + 0x1c) & 0x100) {
        if (*(int far *)(w + 0x1c) & 0x80) {
            f_208F_0419(&size, 0x66);
            f_1FD2_0883(rect.right -= size.x, rect.top, 0x66, 0xf085, flag);
        } else {
            f_208F_0419(&size, 0x67);
            f_1FD2_0883(rect.right -= size.x, rect.top, 0x67, 0xf085, flag);
        }
    }
    if (*(int far *)(w + 0x1c) & 0x10)
        f_1FD2_0883(rect.left, rect.top, 0x65, 0xf088, flag);
    if (*(int far *)(w + 0x1c) & 0x400) {
        f_208F_0419(&size, 0x69);
        f_1FD2_0883(rect.right -= size.x, rect.top, 0x69, 0xf082, flag);
    }
}

extern void far f_1FD2_03EB(char far *obj, int objNum);
extern void far f_1FD2_044F(char far *w, int id);
extern void far f_218D_01EB(void);

void _fastcall f_2505_0831(int win)
{
    struct Win far *w;
    char far *obj;
    int dirty;
    int n;
    int i;

    win &= 0xff00;
    win_LockWin(win);
    w = (struct Win far *)f_2505_0006(win);
    n = w->count;
    dirty = 0;
    for (i = 0; i < n; i++) {
        obj = w->objs[i];
        if (obj[0x24] & 2)
            f_1FD2_03EB(obj, win + i);
        if (obj[0x24] & 0x10)
            dirty = 1;
    }
    f_2505_06B9(1, (char far *)w);
    if (dirty)
        f_1FD2_044F((char far *)w, (win >> 8) - 0x500);
    f_218D_01EB();
    win_UnlockWin(win);
}

extern void far f_1FD2_0438(int objNum);
extern void far f_1FD2_049C(int id);

void _fastcall f_2505_08EA(int win)
{
    struct Win far *w;
    char far *obj;
    int dirty;
    int n;
    int i;

    win &= 0xff00;
    win_LockWin(win);
    w = (struct Win far *)f_2505_0006(win);
    n = w->count;
    for (i = 0; i < n; i++) {
        obj = w->objs[i];
        if (obj[0x24] & 2)
            f_1FD2_0438(win + i);
        if (obj[0x24] & 0x10)
            dirty = 1;
    }
    f_2505_06B9(0, (char far *)w);
    if (dirty)
        f_1FD2_049C((win >> 8) - 0x500);
    win_UnlockWin(win);
}
