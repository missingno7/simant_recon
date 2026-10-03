#include "dos_types.h"
#include "portable/whole_program/platform/dos_memory.h"
#include "portable/whole_program/platform/dos_io.h"
#include "portable/whole_program/platform/graphics_source_fields.h"
#include "native_owners.h"
#pragma pack(push, 2)
#include <stdint.h>
extern uint8_t  ExpSubStates[];
/* Overlay section S05, code frame 3663: expansion tool menu (Win16 DoExpMenu). */

struct Rect {
    int16_t left;
    int16_t top;
    int16_t right;
    int16_t bottom;
};

struct Pt {
    int16_t x;
    int16_t y;
};

struct Event {
    int16_t what;
    int16_t message;
    int16_t x4;
    int16_t modifiers;
    int16_t h;
    int16_t v;
    uint16_t code;
    int16_t xE;
};

static int16_t subMenus[8] = { -1, 0xc00, 0xf00, 0x1000, 0x1100, 0xd00, 0xe00, -1 };

extern void win_Open(int16_t win, int16_t supplied_count, int16_t p0, int16_t p1, int16_t p2, int16_t p3) ;
extern void  _win_SetProxItem(int16_t obj);
extern void  ButtonHeldInit(void);
extern int16_t  win_IsWinOpen(int16_t win);
extern int16_t  win_IsWinInFront(int16_t win);
extern void  f_1FD2_04D0(struct Pt  *pt);
extern void  win_GetObjRect(int16_t obj, struct Rect  *rect);
extern int16_t  f_1FD2_04E5(struct Pt  *pt, struct Rect  *r);
extern void  WinPrintf(char  *fmt, ...);
extern void  win_Close(int16_t win);
extern void  win_ObjInv(int16_t obj);
extern int16_t  f_1F58_0038(void);
extern int16_t  f_1F58_0090(void);
extern int16_t  win_GetEvent(struct Event  *ev);
extern int16_t  win_GetProxEvent(void);
extern int16_t  g_5702;
extern void  win_GetObjSize(int16_t obj, struct Pt  *size);
extern int16_t  ButtonHeld(void);
extern void  ButtonHeldEnd(void);

int16_t  DoExpMenu(int16_t x, int16_t y)
{
    int16_t cur;
    int16_t result;
    int16_t openSub;
    struct Pt pt;
    struct Rect r;
    struct Pt size;
    struct Event ev;
    int16_t i;
    int16_t n;

    result = openSub = -1;
    win_Open(0x900, 2, x, y, 0, 0);
    _win_SetProxItem(native_state_CurExpTool.signed_value + 0x902);
    cur = native_state_CurExpTool.signed_value;
    ButtonHeldInit();
    do {
    if (!win_IsWinOpen(0x900))
        goto release;
    if (!win_IsWinInFront(0x900)) {
        f_1FD2_04D0(&pt);
        for (i = 0x902; i <= 0x909; i++) {
            win_GetObjRect(i, &r);
            if (f_1FD2_04E5(&pt, &r) && cur + 0x902 != i) {
    WinPrintf("\nL: item=%x, openSub=%x", i, openSub);
    if (openSub != -1) {
        win_Close(openSub);
        win_ObjInv(cur + 0x902);
        openSub = -1;
    }
    win_ObjInv(cur + 0x902);
    cur = i - 0x902;
    _win_SetProxItem(i);
    goto dos_open;
            }
        }
    }
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
    /* BYTE-1: read the event word through its low-byte lvalue. */
    if ((char)(openSub >> 8) == *(uint8_t *)&ev.code) {
        n = win_GetProxEvent() & 0xff;
        if (n >= 2)
            ((int8_t *)ExpSubStates)[cur] = n - 2;
        WinPrintf("\nLast sub state = %x", n);
    }
    if (ev.code == 0xff00)
        goto accept;
    else {
        if ((ev.code & 0xff00) == g_5702)
            goto proxy;
        if ((char)ev.code != 9)
            goto next;
        WinPrintf("..");
        cur = (win_GetProxEvent() & 0xff) - 2;
        if (subMenus[cur] == openSub)
            continue;
        WinPrintf("\nX: item=%x, openSub=%x", cur, openSub);
    dos_open:
        if (cur < 0 || cur > 6)
            continue;
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
        if (size.x + r.right + 1 >= SIM_GRAPHICS_SOURCE_g_3DB2)
            win_Open(i, 2, r.left - size.x, r.top, 0, 0);
        else
            win_Open(i, 2, r.right, r.top, 0, 0);
        if (((int8_t *)ExpSubStates)[cur] != -1)
            _win_SetProxItem(((int8_t *)ExpSubStates)[cur] + openSub + 2);
    next:
        if (ButtonHeld())
            continue;
        result = cur;
        goto release;
    proxy:
        if (ev.code >= 0x900) {
            if (ev.code < 0xa00) {
                if (ev.code >= 0x902)
                    result = ev.code - 0x902;
            } else
                result = cur;
        } else
            result = cur;
        goto dos_close;
    accept:
        result = cur;
        goto dos_close;
    cancel:
        result = -1;
        goto dos_close;
    release:
        ButtonHeldEnd();
    dos_close:
        if (openSub != -1)
            win_Close(openSub);
        win_Close(0x900);
        return result;
    }
    } while (1);
}

#pragma pack(pop)
