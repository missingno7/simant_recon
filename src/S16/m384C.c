/* Overlay section S16, code frame 384C: payoff animation, credits and intro. */

typedef char far * far *Handle;

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

void far o16_384C_0000(void);
void far o16_384C_01E1(void);
void far ShowIntro(void);
void far LoadMonoPats(void);
void far o15_384C_0152(char far *msg, int flag);

static int g_2C2C[6][2] = {
    { 0x4a, 0x48 }, { 0x42, 0x57 }, { 0x40, 0xaf },
    { 0x42, 0xbf }, { 0x7a, 0x9f }, { 0x7c, 0xb3 }
};

extern void far f_00F8_04C7(void);
extern int far fd_50F6_035C;
extern void far f_015B_0273(int mode);
extern int far fd_50F6_032E;
extern void far f_015B_053C(int plane);
extern void far DrawYard(void);
extern void far f_00F8_0265(long ticks);
extern void _fastcall win_LockWin(int win);
extern void _fastcall win_SetObjBitmap(int obj, int bitmap);
extern int near g_3DB2;
extern void _fastcall f_22BF_00AA(int obj, struct Rect far *r);
extern int far fd_50F6_3942;
extern void _fastcall f_22BF_00DD(int obj, struct Rect far *r);
extern void far win_Open(int win);
extern void _fastcall win_GetObjRect(int obj, struct Rect far *rect);
extern void _fastcall win_UnlockWin(int win);
extern long far f_00F8_02BE(void);
extern void far f_00F8_02F7(int ticks);
extern int far f_00DF_0138(void);
extern void far f_00DF_00B1(int id, int arg);
extern int _fastcall win_DrawBitMap(int x, int y, int id);
extern int far f_00F8_05F2(void);
extern void _fastcall win_Close(int win);

void far o16_384C_0000(void)
{
    struct Rect rect;
    struct Rect saved;
    struct Rect bounds;
    long nextFrame;
    long deadline;
    int song;
    int row;
    int i;
    int x;
    int y;

    f_00F8_04C7();
    if (fd_50F6_035C)
        f_015B_0273(0);
    if (fd_50F6_032E)
        f_015B_053C(0);
    DrawYard();
    f_00F8_0265(0x96L);
    win_LockWin(0x1a00);
    win_SetObjBitmap(0x1a01, 0x3f48);
    if (g_3DB2 == 0x140) {
        f_22BF_00AA(0x1a01, &saved);
        bounds = saved;
        bounds.left = 4;
        bounds.top = fd_50F6_3942 + 3;
        f_22BF_00DD(0x1a01, &bounds);
    }
    win_Open(0x1a00);
    win_GetObjRect(0x1a01, &rect);
    win_UnlockWin(0x1a00);
    song = 0x4e23;
    row = 1;
    nextFrame = f_00F8_02BE() + 0x1eL;
    deadline = f_00F8_02BE() + 0x258L;
    f_00F8_02F7(10);
    while (!f_00F8_05F2()) {
        if (f_00F8_02BE() >= deadline)
            break;
        if (f_00DF_0138() && song < 0x4e25) {
            f_00DF_00B1(song, 0x7e);
            song++;
        }
        if (f_00F8_02BE() >= nextFrame) {
            nextFrame = f_00F8_02BE() + 8L;
            for (i = 0; i < 6; i++) {
                x = g_2C2C[i][1] + rect.left;
                y = g_2C2C[i][0] + rect.top;
                if (g_3DB2 == 0x140) {
                    x += 0x3f;
                    y -= 10;
                }
                win_DrawBitMap(x, y, row + 0x3f52);
            }
            if (++row >= 3)
                row = 0;
        }
    }
    f_00F8_0265(0x12cL);
    win_Close(0x1a00);
    if (g_3DB2 == 0x140)
        f_22BF_00DD(0x1a01, &saved);
}

extern char far * far * far f_075B_0242(int object);
extern unsigned long far TickCount(void);
extern void far f_00F8_032A(void);
extern int far WaitedEnough(long far *timer, int delay);
extern int far win_Events(void);
extern void far win_FlushEvents(void);
extern void _fastcall win_DrawObjectNum(int objNum);
extern void far f_1E57_0FDC(struct Rect far *r);
extern void _fastcall win_SetColorFromObjNum(int obj);
extern void far f_24AB_02AD(int font);
extern int far f_24AB_030B(void);
extern void (far * near g_9188)(int left, int top, int right, int bottom, int x, int y);
extern void _fastcall gr_JustifyStrInRect(int mode, struct Rect far *rect, char far *text);
extern int near g_3DE2;
extern int far g_3DA0;
extern void (far * near g_9134)(int x0, int y0, int x1, int y1, int color);
extern void far f_1E57_0362(void);
extern void far free(char far *p);
extern void far db_PurgeObject(int object, int kind);

void far o16_384C_01E1(void)
{
    long count;
    char far * far *list;
    int n;
    long timer;
    struct Rect rect;
    struct Rect box;
    int line;
    int pix;
    int drawn;
    int height;
    int y;
    int idx;

    count = 0;
    win_Open(0x1f00);
    list = f_075B_0242(0x6a4);
    for (n = 0; list[n] != 0; n++)
        ;
    for (;;) {
        timer = TickCount();
        f_00F8_032A();
        while (!WaitedEnough(&timer, 0x5a)) {
            if (f_00F8_05F2() || win_Events()) {
                if (count > 1)
                    goto out;
                win_FlushEvents();
                break;
            }
        }
        count++;
        win_GetObjRect(0x1f02, &rect);
        win_DrawObjectNum(0x1f01);
        f_1E57_0FDC(&rect);
        win_SetColorFromObjNum(0x1f02);
        line = 0;
        pix = 0;
        drawn = 0;
        while (line < n) {
            timer = TickCount();
            f_00F8_032A();
            while (!WaitedEnough(&timer, (line == 0 && pix == 1) ? 0x36 : 1)) {
                if (f_00F8_05F2() || win_Events()) {
                    if (count > 3)
                        goto out;
                    win_FlushEvents();
                    break;
                }
            }
            count++;
            f_24AB_02AD(4);
            height = f_24AB_030B();
            y = rect.top - pix;
            idx = line;
            if (drawn)
                (*g_9188)(rect.left, rect.top + 1, rect.right, rect.bottom, rect.left, rect.top);
            for (; y < rect.bottom; idx++, y += height) {
                if (idx < n && *list[idx] != 0) {
                    if (drawn && height + y < rect.bottom)
                        continue;
                    box.top = y;
                    box.bottom = height + y;
                    box.left = rect.left;
                    box.right = rect.right;
                    gr_JustifyStrInRect(3, &box, list[idx]);
                    (*g_9134)(g_3DA0, y, rect.right, height + y, g_3DE2);
                } else {
                    (*g_9134)(rect.left, y, rect.right, height + y, g_3DE2);
                }
            }
            if (++pix == height) {
                pix = 0;
                line++;
            }
            f_24AB_02AD(0);
            drawn = 1;
        }
        f_1E57_0362();
        win_DrawObjectNum(0x1f02);
    }
out:
    free((char far *)list);
    db_PurgeObject(0x6a4, 4);
    win_FlushEvents();
    win_Close(0x1f00);
}

extern Handle far fd_50F6_10CC[];
extern Handle far f_171C_1A9E(long size, int flags, char far *name);
extern Handle far fd_50F6_3836;
extern Handle far fd_50F6_3938;
extern Handle far fd_50F6_3934;
extern char far * far f_171C_1B84(Handle h);
extern void far * far _fmemcpy(void far *dest, void far *src, unsigned n);
extern Handle far f_171C_1BBA(Handle h);
extern void far f_171C_1C0A(Handle h);
extern int _fastcall win_IsWinOpen(int win);

void far ShowIntro(void)
{
    char far *p;
    char far *a;
    char far *b;
    int i;

    win_Open(0x300);
    f_00DF_00B1(0x2711, 0x7e);
    f_00F8_02F7(0x28);
    if (fd_50F6_10CC[0] != 0) {
        fd_50F6_3836 = f_171C_1A9E(0x28L, 1, "Malloc");
        fd_50F6_3938 = f_171C_1A9E(0x32L, 1, "Malloc");
        fd_50F6_3934 = f_171C_1A9E(0x1eL, 1, "Malloc");
        p = f_171C_1B84(fd_50F6_10CC[0]);
        a = f_171C_1B84(fd_50F6_3836);
        b = f_171C_1B84(fd_50F6_3938);
        _fmemcpy(a, p + 0x80, 0x1e);
        _fmemcpy(b, p + 0x9e, 0x1e);
        p = f_171C_1B84(fd_50F6_3934);
        for (i = 0; i < 0x100; i++) {
            a[i % 30] ^= (char)(i + 0x55);
            p[i % 8] = (a[i % 30] + p[i % 8] + i) % 10 + '0';
            b[i % 30] ^= (char)(i + 0x55);
        }
        p[8] = 0;
        f_171C_1BBA(fd_50F6_10CC[0]);
        f_171C_1C0A(fd_50F6_10CC[0]);
        fd_50F6_10CC[0] = 0;
        f_171C_1BBA(fd_50F6_3934);
        f_171C_1BBA(fd_50F6_3938);
        f_171C_1BBA(fd_50F6_3836);
    }
    while (win_IsWinOpen(0x300)) {
        if (win_Events() || f_00F8_05F2())
            win_Close(0x300);
    }
    win_FlushEvents();
}
