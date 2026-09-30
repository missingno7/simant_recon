/* Root module 00F8: map/yard window helpers, timing and small hooks. */

struct Rect {
    int left;
    int top;
    int right;
    int bottom;
};

typedef struct {
    int x;
    int y;
} Point;

typedef char far * far *Handle;

extern Handle far fd_50F6_10DA;
extern void far clip_Push(void);
extern void far clip_SetWin(int win);
extern void far hanim_RemoveAllAnimObjects(Handle);
extern void far hanim_RenderAnimSet(Handle);
extern void far hanim_RemoveAnimSet(Handle);
extern void far clip_Pop(void);
extern int _fastcall win_IsWinOpen(int win);
extern void _fastcall win_GetObjRect(int obj, struct Rect far *rect);
extern struct Rect far fd_50F6_10D2;
extern void far EraseYardCursor(void);

void far f_00F8_0002(void)
{
    if (fd_50F6_10DA) {
        clip_Push();
        clip_SetWin(0x1900);
        hanim_RemoveAllAnimObjects(fd_50F6_10DA);
        hanim_RenderAnimSet(fd_50F6_10DA);
        hanim_RemoveAnimSet(fd_50F6_10DA);
        clip_Pop();
        fd_50F6_10DA = 0;
    }
    if (win_IsWinOpen(0x1902)) {
        win_GetObjRect(0x1902, &fd_50F6_10D2);
        fd_50F6_10D2.left++;
        EraseYardCursor();
    }
}

extern void far EraseMapCursor(void);
extern int far fd_55B3_29A2;

void far f_00F8_00A4(void)
{
    if (win_IsWinOpen(0x100)) {
        EraseMapCursor();
        win_GetObjRect(0x102, &fd_50F6_10D2);
        fd_55B3_29A2 = 1;
    }
}

extern int far fd_3D57_07C8;
extern char far * far * far fd_50F6_046C;
extern void far win_SetObjFormatStr(int obj, ...);
extern int far fd_50F6_035C;
extern void _fastcall win_DrawTitle(int win);

void far f_00F8_00D8(void)
{
    win_SetObjFormatStr(0x101, fd_50F6_046C[fd_3D57_07C8]);
    win_SetObjFormatStr(0x1901, fd_50F6_046C[fd_50F6_035C + 9]);
    if (win_IsWinOpen(0x100)) {
        clip_Push();
        clip_SetWin(0x100);
        win_DrawTitle(0x101);
        clip_Pop();
    } else if (win_IsWinOpen(0x1900)) {
        clip_Push();
        clip_SetWin(0x1900);
        win_DrawTitle(0x1901);
        clip_Pop();
    }
}

static long g_8BA4;
extern int far WaitedEnough(long far *, int);
extern int far fd_55B3_2CBC;
extern char far fd_55B3_2CBA;
void far f_00F8_01BE(void);

void far f_00F8_017D(void)
{
    if (WaitedEnough(&g_8BA4, 2) && fd_55B3_2CBC == 0) {
        fd_55B3_2CBA = 1;
        f_00F8_01BE();
        fd_55B3_2CBA = 0;
    }
}

extern int far win_Events(void);
extern int far f_1F58_0038(void);
extern int far f_1B73_0A30(int);
extern void far o19_384C_0000(void);
extern int far f_1B73_0EEE(void);
extern int near g_9122;
extern int near g_3DB2;
extern int near g_9124;
extern int near g_3DB4;
extern int far f_0250_0D10(int dx, int dy);

void far f_00F8_01BE(void)
{
    int dx, dy;

    if (win_Events() || f_1F58_0038() || f_1B73_0A30(0x1d) || fd_55B3_2CBC)
        o19_384C_0000();
    do {
        dx = dy = 0;
        if (f_1B73_0EEE())
            break;
        if (g_9122 <= 1)
            dx = -1;
        else if (g_3DB2 - 4 <= g_9122)
            dx = 1;
        if (g_9124 < 1)
            dy = -1;
        else if (g_3DB4 - 4 <= g_9124)
            dy = 1;
        if (!dx && !dy)
            break;
    } while (f_0250_0D10(dx, dy));
}

extern void _fastcall win_MakeGroupUnselected(int win, int group);

void far f_00F8_0252(void)
{
    win_MakeGroupUnselected(0x100, 2);
}

extern unsigned long far TickCount(void);
int far f_00F8_05F2(void);

void far f_00F8_0265(unsigned ticks)
{
    long t;

    t = TickCount();
    while (!WaitedEnough(&t, ticks / 3) && !win_Events() && !f_00F8_05F2())
        ;
}

extern void far f_0000_046F(void);
extern int far f_1FD2_0542(void);

void far f_00F8_02AC(void)
{
    f_0000_046F();
    f_1FD2_0542();
}

long far f_00F8_02BE(void)
{
    return TickCount() * 3;
}

void far f_00F8_02D7(void)
{
}

void far f_00F8_02DF(void)
{
}

void far f_00F8_02E7(void)
{
}

void far f_00F8_02EF(void)
{
}

static long g_8BA8;
static int g_8BAC;
extern void far win_FlushEvents(void);

void far f_00F8_02F7(int secs)
{
    while (f_1FD2_0542())
        win_FlushEvents();
    g_8BA8 = TickCount();
    g_8BAC = secs * 18;
}

void far f_00F8_032A(void)
{
    g_8BA8 = TickCount();
    g_8BAC = 5400;
}

int far f_00F8_0344(void)
{
    return WaitedEnough(&g_8BA8, g_8BAC);
}

void far f_00F8_035D(void)
{
}

void far f_00F8_0365(void)
{
}

void far f_00F8_036D(void)
{
}

void far f_00F8_0375(void)
{
}

void far f_00F8_037D(void)
{
}

void far f_00F8_0385(void)
{
}

void far f_00F8_038D(void)
{
}

void far f_00F8_0395(void)
{
}

void far f_00F8_039D(void)
{
}

void far f_00F8_03A5(void)
{
}

extern int far fd_50F6_032E;
extern Point far fd_50F6_0508;
extern int far fd_50F6_10E0;
extern int far fd_50F6_10DE;

int far f_00F8_03AD(int plane, int x, int y)
{
    int r;

    r = fd_50F6_032E == plane && fd_50F6_0508.x <= x && fd_50F6_0508.x + fd_50F6_10E0 > x
        && fd_50F6_0508.y <= y && fd_50F6_0508.y + fd_50F6_10DE > y;
    return r;
}

extern int far f_1F58_0090(void);

int far f_00F8_040F(void)
{
    int k;

    if (f_1F58_0038() && (k = f_1F58_0090() == 0x1b) || k == 12)
        return 1;
    return 0;
}

void far f_00F8_044C(void)
{
    win_FlushEvents();
}

int far f_00F8_0459(int value)
{
    if (value < 0)
        return -value;
    return value;
}

void far f_00F8_0477(void)
{
}

extern void far SetMapPlane(int plane);
extern void far win_Swap(int from, int to);
extern void far win_Open(int win);

void far f_00F8_047F(void)
{
    f_00F8_0252();
    if (!win_IsWinOpen(0x100)) {
        if (win_IsWinOpen(0x1900)) {
            SetMapPlane(1);
            win_Swap(0x1900, 0x100);
        } else {
            win_Open(0x100);
        }
    }
}

void far f_00F8_04C7(void)
{
    if (!win_IsWinOpen(0x1900)) {
        if (win_IsWinOpen(0x100)) {
            SetMapPlane(0);
            win_Swap(0x100, 0x1900);
        } else {
            win_Open(0x1900);
        }
    }
}

extern void _fastcall f_20E8_0725(int win);

void far OpenMapYard(int unused)
{
    if (win_IsWinOpen(0x100))
        f_20E8_0725(0x100);
    else if (win_IsWinOpen(0x1900))
        f_20E8_0725(0x1900);
    else
        f_00F8_047F();
}

extern char far *far fd_55B3_2A36;
extern char far *far fd_55B3_2A3A;

char far * far f_00F8_0543(int object, int type)
{
    if (type == 2) {
        switch (object) {
        case 30000:
            return fd_55B3_2A36;
        case 30001:
            return fd_55B3_2A3A;
        }
    }
    return 0;
}

extern void far ch_SetCacheHooks(char far * (far *cache)(int object, int type));

void far f_00F8_0585(void)
{
    ch_SetCacheHooks(f_00F8_0543);
}

extern int far WinPrintf(char far *format, ...);
void far f_00F8_05B4(void);

void far f_00F8_059C(void)
{
    WinPrintf("\nUPDATEEVERYTHING!");
    f_00F8_05B4();
}

extern void _fastcall f_21FA_0AD2(struct Rect far *rect);
extern struct Rect far g_5A9C;

void far f_00F8_05B4(void)
{
    f_21FA_0AD2(&g_5A9C);
}

int far f_00F8_05C9(void)
{
    if (f_00F8_0344())
        return 1;
    if (f_1F58_0038() && f_1F58_0090() == 0x1b)
        return 1;
    return 0;
}

int far f_00F8_05F2(void)
{
    int r;

    if (f_00F8_0344()) {
        WinPrintf("WAIT YES");
        r = 1;
    } else if (f_1F58_0038()) {
        r = f_1F58_0090();
    } else {
        r = 0;
    }
    if (r == 0)
        WinPrintf("result=%d", r);
    return r;
}
