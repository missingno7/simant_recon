/*
 * Implements the experiment tool menu. Its single function tracks submenu state and returns the
 * selected editing tool.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS: overlay section 5 (S05); segment 3663; complete original translation unit.
 * Windows: ANTEDIT, from recorded function pairs in the Windows symbol inventory.
 */

#include "events_ids.h"
#include "windows_ids.h"

#include "rect.h"

#include "pt.h"

#include "event.h"

static int subMenus[8] = { -1, WIN_WALL_TOOL_MENU, WIN_DIG_TOOL_MENU, WIN_ANT_TOOL_MENU, WIN_FOOD_TOOL_MENU, WIN_SCENT_TOOL_MENU, WIN_KILL_TOOL_MENU, -1 };

extern void far win_Open();
extern int far fd_50F6_104C;
extern void _fastcall _win_SetProxItem(int obj);
extern void far f_1FD2_057F(void);
extern int _fastcall win_IsWinOpen(int win);
extern int _fastcall win_IsWinInFront(int win);
extern void far GetMousePos(struct Pt far *pt);
extern void _fastcall win_GetObjRect(int obj, struct Rect far *rect);
extern int far PointInRect(struct Pt far *pt, struct Rect far *r);
extern void far WinPrintf(char far *fmt, ...);
extern void _fastcall win_Close(int win);
extern void _fastcall win_ObjInv(int obj);
extern int far kbd_poll_bios_key(void);
extern int far kbd_read_key_code(void);
extern int _fastcall win_GetEvent(struct Event far *ev);
extern int far win_GetProxEvent(void);
extern char far fd_3D57_07B6[];
extern int far clip_window_z_order;
extern void _fastcall win_GetObjSize(int obj, struct Pt far *size);
extern int near gfx_screen_width_pixels;
extern int far f_1FD2_0598(void);
extern void far f_1FD2_05EF(void);

int far DoExpMenu(int x, int y)
{
    int cur;
    int result;
    int openSub;
    struct Pt pt;
    struct Rect r;
    struct Pt size;
    struct Event ev;
    int i;
    int n;

    result = openSub = -1;
    win_Open(WIN_EXPERIMENT_TOOLS_MENU, x, y);
    _win_SetProxItem(fd_50F6_104C + OBJ_EXPERIMENT_TOOLS_MENU_FIRST_TOOL);
    cur = fd_50F6_104C;
    f_1FD2_057F();
    do {
    if (!win_IsWinOpen(WIN_EXPERIMENT_TOOLS_MENU))
        goto release;
    if (!win_IsWinInFront(WIN_EXPERIMENT_TOOLS_MENU)) {
        GetMousePos(&pt);
        for (i = OBJ_EXPERIMENT_TOOLS_MENU_FIRST_TOOL; i <= OBJ_EXPERIMENT_TOOLS_MENU_LAST_TOOL; i++) {
            win_GetObjRect(i, &r);
            if (PointInRect(&pt, &r) && cur + OBJ_EXPERIMENT_TOOLS_MENU_FIRST_TOOL != i) {
    WinPrintf("\nL: item=%x, openSub=%x", i, openSub);
    if (openSub != -1) {
        win_Close(openSub);
        win_ObjInv(cur + OBJ_EXPERIMENT_TOOLS_MENU_FIRST_TOOL);
        openSub = -1;
    }
    win_ObjInv(cur + OBJ_EXPERIMENT_TOOLS_MENU_FIRST_TOOL);
    cur = i - OBJ_EXPERIMENT_TOOLS_MENU_FIRST_TOOL;
    _win_SetProxItem(i);
    goto open;
            }
        }
    }
    if (kbd_poll_bios_key()) {
        switch (kbd_read_key_code()) {
        case 13:
            goto accept;
        case 27:
            goto cancel;
        }
    }
    if (!win_GetEvent(&ev))
        goto next;
    WinPrintf("\nE=%x, openSub=%x", ev.code, openSub);
    /* BYTE-1: read the event word through its low-byte lvalue. */
    if ((char)(openSub >> 8) == *(unsigned char *)&ev.code) {
        n = win_GetProxEvent() & 0xff;
        if (n >= 2)
            fd_3D57_07B6[cur] = n - 2;
        WinPrintf("\nLast sub state = %x", n);
    }
    if (ev.code == EVENT_DESKTOP_CLICK)
        goto accept;
    else {
        if ((ev.code & WIN_ID_MASK) == clip_window_z_order)
            goto proxy;
        if ((char)ev.code != 9)
            goto next;
        WinPrintf("..");
        cur = (win_GetProxEvent() & 0xff) - 2;
        if (subMenus[cur] == openSub)
            continue;
        WinPrintf("\nX: item=%x, openSub=%x", cur, openSub);
    open:
        if (cur < 0 || cur > 6)
            continue;
        if (openSub != -1) {
            win_Close(openSub);
            openSub = -1;
        }
        if (subMenus[cur] == -1 || subMenus[cur] == openSub)
            goto next;
        openSub = subMenus[cur];
        win_GetObjRect(cur + OBJ_EXPERIMENT_TOOLS_MENU_FIRST_TOOL, &r);
        i = subMenus[cur];
        win_GetObjSize(i, &size);
        if (size.x + r.right + 1 >= gfx_screen_width_pixels)
            win_Open(i, r.left - size.x, r.top);
        else
            win_Open(i, r.right, r.top);
        if (fd_3D57_07B6[cur] != -1)
            _win_SetProxItem(fd_3D57_07B6[cur] + openSub + 2);
    next:
        if (f_1FD2_0598())
            continue;
        result = cur;
        goto release;
    proxy:
        if (ev.code >= WIN_EXPERIMENT_TOOLS_MENU) {
            if (ev.code < WIN_QUICK_GAME_TOOLS_MENU) {
                if (ev.code >= OBJ_EXPERIMENT_TOOLS_MENU_FIRST_TOOL)
                    result = ev.code - OBJ_EXPERIMENT_TOOLS_MENU_FIRST_TOOL;
            } else
                result = cur;
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
        win_Close(WIN_EXPERIMENT_TOOLS_MENU);
        return result;
    }
    } while (1);
}
