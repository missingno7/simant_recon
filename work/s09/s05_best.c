/* Overlay section S05, code frame 3663: expansion tool menu (Win16 DoExpMenu). */

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

struct Event {
    int what;
    int message;
    int x4;
    int modifiers;
    int h;
    int v;
    unsigned code;
    int xE;
};

static int subMenus[8] = { -1, 0xc00, 0xf00, 0x1000, 0x1100, 0xd00, 0xe00, -1 };

extern void far win_Open();
extern int far fd_50F6_104C;
extern void _fastcall _win_SetProxItem(int obj);
extern void far f_1FD2_057F(void);
extern int _fastcall win_IsWinOpen(int win);
extern int _fastcall win_IsWinInFront(int win);
extern void far f_1FD2_04D0(struct Pt far *pt);
extern void _fastcall win_GetObjRect(int obj, struct Rect far *rect);
extern int far f_1FD2_04E5(struct Pt far *pt, struct Rect far *r);
extern void far WinPrintf(char far *fmt, ...);
extern void _fastcall win_Close(int win);
extern void _fastcall win_ObjInv(int obj);
extern int far f_1F58_0038(void);
extern int far f_1F58_0090(void);
extern int _fastcall win_GetEvent(struct Event far *ev);
extern int far win_GetProxEvent(void);
extern char far fd_3D57_07B6[];
extern int far g_5702;
extern void _fastcall win_GetObjSize(int obj, struct Pt far *size);
extern int near g_3DB2;
extern int far f_1FD2_0598(void);
extern void far f_1FD2_05EF(void);

int far DoExpMenu(int x, int y)
{
    int cur;
    int result;
    int openSub;
    struct Pt pt;
    struct Pt size;
    struct Rect r;
    struct Event ev;
    int i;
    int n;

    result = openSub = -1;
    win_Open(0x900, x, y);
    _win_SetProxItem(fd_50F6_104C + 0x902);
    cur = fd_50F6_104C;
    f_1FD2_057F();
top:
    if (win_IsWinOpen(0x900)) {
        if (!win_IsWinInFront(0x900)) {
            f_1FD2_04D0(&pt);
            for (i = 0x902; i <= 0x909; i++) {
                win_GetObjRect(i, &r);
                if (f_1FD2_04E5(&pt, &r) && cur + 0x902 != i)
                    goto found;
            }
        }
        goto keys;
    }
    goto release;
found:
    WinPrintf("\nL: item=%x, openSub=%x", i, openSub);
    if (openSub != -1) {
        win_Close(openSub);
        win_ObjInv(cur + 0x902);
        openSub = -1;
    }
    win_ObjInv(cur + 0x902);
    cur = i - 0x902;
    _win_SetProxItem(i);
    goto open;
keys:
    if (f_1F58_0038()) {
        switch (f_1F58_0090()) {
        case 13:
            goto accept;
        case 27:
            goto cancel;
        }
    }
    if (!win_GetEvent(&ev))
        goto next;
    WinPrintf("\nE=%x, openSub=%x", ev.code, openSub);
    if ((char)(openSub >> 8) == (ev.code & 0xff)) {
        n = win_GetProxEvent() & 0xff;
        if (n >= 2)
            fd_3D57_07B6[cur] = n - 2;
        WinPrintf("\nLast sub state = %x", n);
    }
    if (ev.code == 0xff00)
        goto accept;
    if ((ev.code & 0xff00) == g_5702)
        goto proxy;
    if ((char)ev.code != 9)
        goto next;
    WinPrintf("..");
    cur = (win_GetProxEvent() & 0xff) - 2;
    if (subMenus[cur] == openSub)
        goto top;
    WinPrintf("\nX: item=%x, openSub=%x", cur, openSub);
open:
    if (cur < 0 || cur > 6)
        goto top;
    if (openSub != -1) {
        win_Close(openSub);
        openSub = -1;
    }
    if (subMenus[cur] == -1 || subMenus[cur] == openSub)
        goto next;
    openSub = subMenus[cur];
    win_GetObjRect(cur + 0x902, &r);
    i = subMenus[cur];
    win_GetObjSize(i, &size);
    if (size.x + r.right + 1 >= g_3DB2)
        win_Open(i, r.left - size.x, r.top);
    else
        win_Open(i, r.right, r.top);
    if (fd_3D57_07B6[cur] != -1)
        _win_SetProxItem(fd_3D57_07B6[cur] + openSub + 2);
next:
    if (f_1FD2_0598())
        goto top;
    result = cur;
    goto release;
proxy:
    if (ev.code >= 0x900 && ev.code < 0xa00) {
        if (ev.code >= 0x902)
            result = ev.code - 0x902;
    } else
        result = cur;
    goto close;
accept:
    result = cur;
    goto close;
cancel:
    result = -1;
    goto close;
release:
    f_1FD2_05EF();
close:
    if (openSub != -1)
        win_Close(openSub);
    win_Close(0x900);
    return result;
}
