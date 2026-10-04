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

extern char far * far * far f_1A53_00F0(int object, int kind, int type);
extern void far Punt(char far *format, ...);
extern char far * far * near win_handles[];
extern void _fastcall win_LockWin(int win);
extern void _fastcall RepointObjects(int win);
extern struct Rect far win_offsets[];
extern void _fastcall win_UnlockWin(int win);

void far win_LoadWindow(int win)
{
    char far * far *h;
    char far *obj;
    int i;
    char far *w;

    h = f_1A53_00F0((char)(win >> 8), 0, 1);
    if (h == 0)
        Punt("CANNOT LOAD WINDOW %03x", win);
    win_handles[(char)(win >> 8)] = h;
    w = *h;
    win_LockWin(win);
    RepointObjects(win);
    obj = ((char far * far *)(w + 0x2c))[0];
    if (win_offsets[(char)(win >> 8)].left != (int)0x8000)
        *(struct Rect far *)(obj + 8) = win_offsets[(char)(win >> 8)];
    else
        win_offsets[(char)(win >> 8)] = *(struct Rect far *)(obj + 8);
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
    win_UnlockWin(win);
}


struct Rect g_635C = { (int)0x8000, (int)0x8000, (int)0x8000, (int)0x8000 };

extern void far font_InitFonts(void);
extern void far win_LockInit(void);
extern void (far * far win_drawHooks[])(int phase);
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
extern int far win_numOfWindows;
extern int far win_numOfColors;
extern int far win_numOfGroups;
extern char far win_colors[][6];
extern void far db_UnhookObject(int object, int kind);

int far win_LoadAllWindows(void)
{
    char purge[0x28];
    int i;
    char far * far *h;
    int far *p;
    char far *q;

    font_InitFonts();
    win_LockInit();
    _fmemset(win_drawHooks, 0, 0xb4);
    for (i = 0; i < 45; i++) win_offsets[i] = g_635C;
    h = db_LoadObject(g_5A97, 9);
    if (h) {
        _fmemcpy(win_offsets, f_171C_1B84(h), 0x140);
        f_171C_1BBA(h);
        db_PurgeObject(g_5A97, 9);
    }
    f_208F_0419(&fd_50F6_47DA, 0x6f);
    h = db_LoadObject(0x80, 0);
    if (h == 0) {
        Punt("Cannot load resource\nplease try another");
    } else {
        p = (int far *)*h;
        win_numOfWindows = p[0];
        win_numOfColors = p[1];
        win_numOfGroups = p[2];
        db_PurgeObject(0x80, 0);
    }
    h = db_LoadObject(0x81, 0);
    _fmemcpy(win_colors, *h, win_numOfColors * 6);
    db_PurgeObject(0x81, 0);
    h = db_LoadObject(0x83, 0);
    q = *h;
    if (h == 0)
        Punt("Could not load purge list");
    _fmemcpy(purge, q, 0x28);
    db_PurgeObject(0x83, 0);
    for (i = 0; i < win_numOfWindows; i++) {
        if (purge[i] == 0) {
            win_LoadWindow(i << 8);
            db_UnhookObject(i, 0);
        }
    }
    return 1;
}

extern char far * far f_2505_0006(int win);
extern int g_5702[];
extern void _fastcall f_2505_08EA(int win);
extern void far clip_KillWin(int win);
extern void _fastcall win_Recalc(int win);
extern void far f_1E57_00B1(int win);
extern void _fastcall f_2505_0831(int win);
extern void far clip_SetWin(int win);
extern void _fastcall win_DrawWindow(int win);
extern void far clip_Off(void);

void far win_Swap(int from, int to, int unused, int p0, int p1, int p2, int p3)
{
    char far *w;
    struct Rect origin;
    struct Rect rect;
    char far *obj;

    win_LockWin(from);
    w = f_2505_0006(from);
    origin = *(struct Rect far *)(((char far * far *)(w + 0x2c))[0] + 8);
    rect = *(struct Rect far *)w;
    if (g_5702[0] != 0)
        f_2505_08EA(g_5702[0]);
    if (*(int far *)(w + 0x1c) & 0x200) {
        (*g_62E4)();
        (*g_62F4)(from);
        clip_KillWin(from);
        *(int far *)(w + 0x1c) &= ~0x200;
        (*g_62E0)(from);
    }
    win_UnlockWin(from);
    win_LockWin(to);
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
    win_Recalc(to);
    (*g_62E0)(to);
    *(int far *)(f_2505_0006(to) + 0x1c) |= 0x200;
    if (g_5702[0] != (int)0x8000)
        f_2505_08EA(g_5702[0]);
    f_1E57_00B1(to);
    f_2505_0831(to);
    clip_SetWin(to);
    win_DrawWindow(to);
    (*g_62E8)();
    win_UnlockWin(to);
    clip_Off();
}

extern void _fastcall win_LockWinHigh(int win);
extern void _fastcall win_GetObjRect(int obj, struct Rect far *rect);
extern int near g_3DB4;
extern struct Rect far fd_50F6_393C;
extern int near g_3DB2;
extern void far win_FlushEvents(void);

void far win_Open(int win, ...)
{
    char far *w;
    int dx;
    int dy;
    struct Rect r;
    int far *origin;

    if (g_5702[0] != win) {
        win_LockWinHigh(win);
        (*g_62E4)();
        w = f_2505_0006(win);
        ((int far *)(w + 0x10))[0] = (&win)[1];
        ((int far *)(w + 0x10))[1] = (&win)[2];
        ((int far *)(w + 0x10))[2] = (&win)[3];
        ((int far *)(w + 0x10))[3] = (&win)[4];
        win_Recalc(win);
        w = f_2505_0006(win);
        if (*(int far *)(w + 0x1c) & 0x1000) {
            dx = dy = 0;
            win_GetObjRect(win, &r);
            if (r.bottom > g_3DB4)
                dy = g_3DB4 - r.bottom;
            else if (r.top <= fd_50F6_393C.bottom)
                dy = fd_50F6_393C.bottom - r.top;
            if (r.left < 0)
                dx = -r.left;
            else if (r.right >= g_3DB2)
                dx = g_3DB2 - r.right;
            origin = (int far *)(((char far * far *)(w + 0x2c))[0] + 8);
            win_offsets[win >> 8] = *(struct Rect far *)origin;
            origin[0] += dx;
            origin[1] += dy;
            win_Recalc(win);
        }
        (*g_62E0)(win);
        *(int far *)(f_2505_0006(win) + 0x1c) |= 0x200;
        if (g_5702[0] != (int)0x8000)
            f_2505_08EA(g_5702[0]);
        f_1E57_00B1(win);
        f_2505_0831(win);
        clip_SetWin(win);
        win_DrawWindow(win);
        (*g_62E8)();
        clip_Off();
        win_UnlockWin(win);
    }
    win_FlushEvents();
}

extern void _fastcall f_21FA_0B4B(struct Rect far *rect);

void _fastcall win_Close(int win)
{
    char far *w;
    struct Rect r;

    win_LockWin(win);
    w = f_2505_0006(win);
    if (*(int far *)(w + 0x1c) & 0x200) {
        (*g_62E4)();
        (*g_62F4)(win);
        if (g_5702[0] == win) {
            f_2505_08EA(win);
            clip_KillWin(win);
            if (g_5702[0] != (int)0x8000)
                f_2505_0831(g_5702[0]);
        } else {
            clip_KillWin(win);
        }
        *(int far *)(w + 0x1c) &= ~0x200;
        if (*(int far *)(w + 0x1c) & 0x1000)
            *(struct Rect far *)(((char far * far *)(w + 0x2c))[0] + 8) = win_offsets[(char)(win >> 8)];
        (*g_62E0)(win);
        r = *(struct Rect far *)w;
        win_UnlockWin(win);
        f_21FA_0B4B(&r);
        (*g_62E8)();
        clip_Off();
    } else {
        win_UnlockWin(win);
    }
}

extern char far * _fastcall win_WinAddr(int win);

void _fastcall f_20E8_0725(int win)
{
    int top;
    int flag;

    top = g_5702[0];
    if (top != win) {
        if (top != (int)0x8000) {
            win_LockWin(top);
            flag = *(int far *)(win_WinAddr(top) + 0x1c) & 1;
            win_UnlockWin(top);
            if (flag)
                win_Close(top);
        }
        win_Open(win);
    }
}

extern void far f_1E57_0052(int win);
extern void _fastcall f_21FA_0AD2(struct Rect far *rect);

void _fastcall f_20E8_0776(int win)
{
    int flag;
    char far *w;
    struct Rect r;

    win_LockWin(win);
    f_2505_0006(win);
    flag = *(int far *)(win_WinAddr(g_5702[0]) + 0x1c) & 1;
    win_UnlockWin(win);
    (*g_62E4)();
    if (g_5702[0] == win) {
        if (g_5702[1] != (int)0x8000) {
            if (flag) {
                win_Close(g_5702[0]);
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
    win_LockWin(win);
    w = f_2505_0006(win);
    *(int far *)(w + 0x1c) |= 0x200;
    r = *(struct Rect far *)w;
    win_UnlockWin(win);
    (*g_62E0)(win);
    f_21FA_0AD2(&r);
    (*g_62E8)();
    clip_Off();
}

void _fastcall win_SetWinDrawHook(int win, void (far *hook)(int phase))
{
    win_drawHooks[win >> 8] = hook;
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


extern int far * _fastcall win_ObjAddr(int obj);

extern int far f_2505_036E(void);
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
    win_LockWin(win);
    o = win_ObjAddr(obj);
    origin = o + 4;
    mode = o + 12;
    ref = o + 8;
    for (j = 0; j < 4; j++)
        origin[j] = 0;
    win_Recalc(win);
    for (i = 0; i < 4; i++) {
        if (mode[i] && mode[i] != 5 && ref[i] == obj)
            origin[i] = 0;
        else
            origin[i] = rect[i] - o[i];
    }
    win_Recalc(win);
    for (i = 0; i < 4; i++) {
        if (mode[i] && mode[i] != 5 && ref[i] == obj)
            origin[i] = rect[i] - o[i];
    }
    win_Recalc(win);
    win_UnlockWin(win);
}



extern int far f_2505_036E(void);

void far f_20E8_0A21(void)
{
    int top;

    top = g_5702[0];
    if (f_2505_036E()) {
        win_LockWin(top);
        if (*(int far *)(win_WinAddr(top) + 0x1c) & 1)
            win_Close(top);
        win_UnlockWin(top);
    }
}
