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

extern Handle far yardAnimHandle;
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

void far win_YardClosed(void)
{
    if (yardAnimHandle) {
        clip_Push();
        clip_SetWin(0x1900);
        hanim_RemoveAllAnimObjects(yardAnimHandle);
        hanim_RenderAnimSet(yardAnimHandle);
        hanim_RemoveAnimSet(yardAnimHandle);
        clip_Pop();
        yardAnimHandle = 0;
    }
    if (win_IsWinOpen(0x1902)) {
        win_GetObjRect(0x1902, &fd_50F6_10D2);
        fd_50F6_10D2.left++;
        EraseYardCursor();
    }
}

extern void far EraseMapCursor(void);
extern int far fd_55B3_29A2;

void far win_MapChanged(void)
{
    if (win_IsWinOpen(0x100)) {
        EraseMapCursor();
        win_GetObjRect(0x102, &fd_50F6_10D2);
        fd_55B3_29A2 = 1;
    }
}

extern int far MapMode;
extern char far * far * far MwinTitle;
extern void far win_SetObjFormatStr(int obj, ...);
extern int far YardMode;
extern void _fastcall win_DrawTitle(int win);

void far SetMapTitle(void)
{
    win_SetObjFormatStr(0x101, MwinTitle[MapMode]);
    win_SetObjFormatStr(0x1901, MwinTitle[YardMode + 9]);
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
void far ui_pump_events_edge_scroll(void);

void far f_00F8_017D(void)
{
    if (WaitedEnough(&g_8BA4, 2) && fd_55B3_2CBC == 0) {
        fd_55B3_2CBA = 1;
        ui_pump_events_edge_scroll();
        fd_55B3_2CBA = 0;
    }
}

extern int far win_Events(void);
extern int far kbd_poll_bios_key(void);
extern int far kbd_scan_state(int);
extern void far DoEvent(void);
extern int far kbd_scroll_lock_state(void);
extern int near g_9122;
extern int near g_3DB2;
extern int near g_9124;
extern int near g_3DB4;
extern int far edit_scroll_and_redraw(int dx, int dy);

void far ui_pump_events_edge_scroll(void)
{
    int dx, dy;

    if (win_Events() || kbd_poll_bios_key() || kbd_scan_state(0x1d) || fd_55B3_2CBC)
        DoEvent();
    do {
        dx = dy = 0;
        if (kbd_scroll_lock_state())
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
    } while (edit_scroll_and_redraw(dx, dy));
}

extern void _fastcall win_MakeGroupUnselected(int win, int group);

void far ClearMapScentButtons(void)
{
    win_MakeGroupUnselected(0x100, 2);
}

extern unsigned long far TickCount(void);
int far DialogAbortOrCont(void);

void far myDelay(unsigned ticks)
{
    long t;

    t = TickCount();
    while (!WaitedEnough(&t, ticks / 3) && !win_Events() && !DialogAbortOrCont())
        ;
}

extern void far snd_service_pending(void);
extern int far StillDown(void);

void far myButton(void)
{
    snd_service_pending();
    StillDown();
}

long far MacTickCount(void)
{
    return TickCount() * 3;
}

void far f_00F8_02D7(void)
{
}

void far SetSimCursor(void)
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

void far DialogWaitInit(int secs)
{
    while (StillDown())
        win_FlushEvents();
    g_8BA8 = TickCount();
    g_8BAC = secs * 18;
}

void far DialogClearWait(void)
{
    g_8BA8 = TickCount();
    g_8BAC = 5400;
}

int far DialogWait(void)
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

void far InvalQueenStorageDisp(void)
{
}

void far f_00F8_039D(void)
{
}

void far MakeDMap(void)
{
}

extern int far MapPlane;
extern Point far MapPnt;
extern int far fd_50F6_10E0;
extern int far fd_50F6_10DE;

int far TileIsVisible(int plane, int x, int y)
{
    int r;

    r = MapPlane == plane && MapPnt.x <= x && MapPnt.x + fd_50F6_10E0 > x
        && MapPnt.y <= y && MapPnt.y + fd_50F6_10DE > y;
    return r;
}

extern int far kbd_read_key_code(void);

int far f_00F8_040F(void)
{
    int k;

    if (kbd_poll_bios_key() && (k = kbd_read_key_code() == 0x1b) || k == 12)
        return 1;
    return 0;
}

void far f_00F8_044C(void)
{
    win_FlushEvents();
}

int far ABS(int value)
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

void far YardToMap(void)
{
    ClearMapScentButtons();
    if (!win_IsWinOpen(0x100)) {
        if (win_IsWinOpen(0x1900)) {
            SetMapPlane(1);
            win_Swap(0x1900, 0x100);
        } else {
            win_Open(0x100);
        }
    }
}

void far MapToYard(void)
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

extern void _fastcall win_ToTop(int win);

void far OpenMapYard(int unused)
{
    if (win_IsWinOpen(0x100))
        win_ToTop(0x100);
    else if (win_IsWinOpen(0x1900))
        win_ToTop(0x1900);
    else
        YardToMap();
}

extern char far *far yardBalloon;
extern char far *far fd_55B3_2A3A;

char far * far f_00F8_0543(int object, int type)
{
    if (type == 2) {
        switch (object) {
        case 30000:
            return yardBalloon;
        case 30001:
            return fd_55B3_2A3A;
        }
    }
    return 0;
}

extern void far ch_SetCacheHooks(char far * (far *cache)(int object, int type));

void far res_install_cache_hook(void)
{
    ch_SetCacheHooks(f_00F8_0543);
}

extern int far WinPrintf(char far *format, ...);
void far win_redraw_current_clip(void);

void far UpdateEverything(void)
{
    WinPrintf("\nUPDATEEVERYTHING!");
    win_redraw_current_clip();
}

extern void _fastcall f_21FA_0AD2(struct Rect far *rect);
extern struct Rect far g_5A9C;

void far win_redraw_current_clip(void)
{
    f_21FA_0AD2(&g_5A9C);
}

int far DialogAbort(void)
{
    if (DialogWait())
        return 1;
    if (kbd_poll_bios_key() && kbd_read_key_code() == 0x1b)
        return 1;
    return 0;
}

int far DialogAbortOrCont(void)
{
    int r;

    if (DialogWait()) {
        WinPrintf("WAIT YES");
        r = 1;
    } else if (kbd_poll_bios_key()) {
        r = kbd_read_key_code();
    } else {
        r = 0;
    }
    if (r == 0)
        WinPrintf("result=%d", r);
    return r;
}
