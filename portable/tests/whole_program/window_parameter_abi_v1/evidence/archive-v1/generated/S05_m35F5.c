#include "dos_types.h"
#include "portable/whole_program/platform/dos_memory.h"
#include "portable/whole_program/platform/dos_io.h"
uint8_t dos_keyboard_modifiers(void);
#include "portable/whole_program/platform/graphics_source_fields.h"
#include "portable/whole_program/state/game_views.h"
#include "simulation_state_50f6.h"
#include "native_owners.h"
#pragma pack(push, 2)
/* Overlay section S05, code frame 35F5: editor tool and ant menus (Win16 ANTEDIT_MODULE run). */

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
    int16_t code;
    int16_t xE;
};

extern int16_t  fd_3D57_07BE;
extern int16_t  win_DoProxMenu();
extern void  clip_SetWin(int16_t win);
extern void  win_SetObjSelectedState(int16_t obj, int16_t state);
extern void  ForceUpdateEdit(void);

void  EditScentMenu(void)
{
    int16_t r;

    r = win_DoProxMenu(0x600, fd_3D57_07BE + 1);
    if (r == -1)
        return;
    fd_3D57_07BE = r - 1;
    clip_SetWin(0);
    win_SetObjSelectedState(0x10, fd_3D57_07BE != -1);
    ForceUpdateEdit();
}

static int16_t toolMenus[8] = { -1, 0xc00, 0xf00, 0x1000, 0x1100, 0xd00, 0xe00, -1 };

extern void  win_GetObjRect(int16_t obj, struct Rect  *rect);
extern int16_t  fd_50F6_0EAC;
void  SetExpTool(int16_t tool);
extern int16_t  fd_50F6_0496;
extern int16_t  fd_50F6_04C2;
extern int16_t  MeLocY;
extern int16_t  MeLocX;
extern int16_t  MePlane;
extern void  ClearMyLife(int16_t plane, int16_t x, int16_t y, int16_t type, int16_t dir);
extern int16_t  fd_50F6_0A06;
extern void  InitSpider(void);
extern void  SetEditWinTitle();
extern void  myBeginSound(int16_t, int16_t, int16_t);
extern int16_t  DoExpMenu(int16_t x, int16_t y);
extern void  WinPrintf(char  *fmt, ...);
extern void  InitYelloAnt(void);
extern void  SetMyLife(int16_t, int16_t, int16_t, int16_t, int16_t, int16_t);
extern void  myBeginSong(int16_t id, int16_t arg);
extern void  clip_Push(void);
extern void  win_DrawBitMapAtObjNum(int16_t obj, int16_t id);
extern void  clip_Pop(void);
extern int16_t  win_IsWinOpen(int16_t win);

void  EditToolsMenu(void)
{
    struct Rect r;
    int16_t item;

    win_GetObjRect(7, &r);
    switch (fd_50F6_0EAC) {
    case 1:
        if (win_DoProxMenu(0xa00, -1, r.right + 2, r.top) < 0)
            break;
        SetExpTool(native_state_CurExpTool.signed_value);
        fd_50F6_0EAC = 3;
        ClearMyLife(MePlane, MeLocX, MeLocY, fd_50F6_04C2, fd_50F6_0496);
        fd_50F6_0A06 = 2;
        InitSpider();
        SetEditWinTitle(0, 0);
        myBeginSound(2, 0, 0x7e);
        break;
    case 2:
        win_DoProxMenu(0xb00, -1, r.right + 2, r.top);
        break;
    case 3:
        WinPrintf("\nITEM=%x, startTool=%x", item = DoExpMenu(r.right + 2, r.top), 7);
        if (item == -1)
            break;
        if (item == 7) {
            fd_50F6_0EAC = 1;
            InitYelloAnt();
            if (native_state_MapPlane.signed_value == 1)
                SetMyLife(MePlane, MeLocX, MeLocY, fd_50F6_04C2, fd_50F6_0496, 0xff);
            SetEditWinTitle(0, 0);
            myBeginSong(0x2afb, 0x7e);
        }
        SetExpTool(item);
        clip_Push();
        clip_SetWin(0);
        win_DrawBitMapAtObjNum(7, native_state_CurExpTool.signed_value + 0x13ec);
        clip_Pop();
        if (win_IsWinOpen(0x100)) {
            clip_Push();
            clip_SetWin(0x100);
            win_DrawBitMapAtObjNum(0x117, native_state_CurExpTool.signed_value + 0x13ec);
            clip_Pop();
        }
        break;
    }
}

extern uint8_t  LifeA[128][64];
extern uint8_t  LifeB[64][64];
extern uint8_t  LifeR[64][64];
extern int16_t  g_19BE;
extern int16_t  g_19C0;
extern void  win_GetObjSize(int16_t obj, struct Pt  *size);
extern void  win_Open();
extern char  *  *  fd_50F6_106E;
extern char  *  *  fd_50F6_1078;
extern void  f_24AB_02AD(int16_t font);
extern void  win_PrintfAtObj(int16_t obj, char  *format, ...);
extern int16_t  FindInAList(int16_t x, int16_t y);
extern uint8_t  AlistM[];
extern int16_t  FindInBList(int16_t x, int16_t y, int16_t t);
extern uint8_t  BlistM[];
extern int16_t  FindInRList(int16_t x, int16_t y, int16_t t);
extern uint8_t  RlistM[];
extern char  *  *  fd_50F6_1086;
/* AntMenu's externs are declared here, and SetMyLife/myBeginSound use unnamed
   parameters: the declaration layout reproduces the original's symbol-table state
   (register choices in MagnifyMenu and AntMenu depend on it). */
extern int16_t  fd_3D57_0C24;
extern int16_t  fd_50F6_10E0;
extern int16_t  fd_50F6_10DE;
extern void  YellowCommand(int16_t cmd);
extern char  *  *  fd_50F6_1096;
extern void  ButtonHeldInit(void);
extern int16_t  ButtonHeld(void);
extern void  ButtonHeldEnd(void);
extern void  win_Close(int16_t win);

int16_t  MagnifyMenu(int16_t x, int16_t y, int16_t plane)
{
    int16_t k;
    int16_t caste;
    int16_t t;
    char  *name;
    struct Pt size;
    int16_t wx;
    int16_t wy;
    int16_t i;

    if (plane <= 1)
        t = LifeA[x][y];
    else if (plane == 2)
        t = LifeB[x][y];
    else
        t = LifeR[x][y];
    if (t == 0)
        return -1;
    wx = (x - native_sim_state_fd_50F6_0508.words[0] + 1) * g_19BE + native_game_fd_50F6_110C.words[0];
    wy = (y - native_sim_state_fd_50F6_0508.words[1] - 1) * g_19C0 + native_game_fd_50F6_110C.words[1];
    win_GetObjSize(0x1d00, &size);
    if (size.x + wx > SIM_GRAPHICS_SOURCE_g_3DB2)
        wx -= g_19BE + size.x;
    if (size.y + wy > SIM_GRAPHICS_SOURCE_g_3DB4)
        wy = SIM_GRAPHICS_SOURCE_g_3DB4 - size.y;
    win_Open(0x1d00, wx, wy);
    caste = (t & 0x78) >> 3;
    if (caste == 0)
        name = fd_50F6_106E[t & 7];
    else
        name = fd_50F6_1078[caste];
    f_24AB_02AD(2);
    win_PrintfAtObj(0x1d02, name);
    switch (plane) {
    case 1:
        if ((i = FindInAList(x, y)) >= 0)
            k = AlistM[i];
        else
            k = 0;
        break;
    case 2:
        if ((i = FindInBList(x, y, LifeB[x][y])) >= 0)
            k = BlistM[i];
        else
            k = 0;
        break;
    case 3:
        if ((i = FindInRList(x, y, LifeR[x][y])) >= 0)
            k = RlistM[i];
        else
            k = 0;
        break;
    }
    win_PrintfAtObj(0x1d03, fd_50F6_1086[k]);
    win_PrintfAtObj(0x1d04, fd_50F6_1096[caste]);
    f_24AB_02AD(0);
    ButtonHeldInit();
    while (win_IsWinOpen(0x1d00) && ButtonHeld())
        ;
    ButtonHeldEnd();
    win_Close(0x1d00);
    WinPrintf("tileNum=%d", t);
    return t;
}


int16_t  AntMenu(struct Event  *ev)
{
    static char antCmds[4] = { 8, 9, 0, 0 };
    static char nestCmds[6] = { 1, 2, 4, 5, 6, 0 };
    static char spiderCmds[4] = { 10, 11, 6, 0 };
    int16_t n;
    int16_t r;
    int16_t cmd;
    int16_t x, y;

    n = 5;
    if (fd_50F6_04C2 == 0x40 && fd_3D57_0C24 == 0)
        n = 2;
    /* Dead menu-placement test (x, y unused).  MSC eliminates the arithmetic but keeps
       the ES segment loads, the first compare of the || and the n = 5/2 setup; only
       those survive in the original, so the exact expressions are a hypothesis. */
    x = native_sim_state_fd_50F6_0508.words[0] + fd_50F6_10E0;
    if (x < MeLocX)
        x = MeLocX;
    if (native_sim_state_fd_50F6_0508.words[1] + 2 > MeLocY || MeLocY - fd_50F6_10DE < n)
        y = x;
    WinPrintf("ANTMENU");
    if (fd_50F6_0A06 == 0) {
        if (fd_50F6_04C2 == 0x40 && fd_3D57_0C24 == 0)
            r = win_DoProxMenu(0x800, -1, ev->h, ev->v);
        else
            r = win_DoProxMenu(0x700, -1, ev->h, ev->v);
    } else if (fd_50F6_0A06 == 1)
        r = win_DoProxMenu(0x2000, -1, ev->h, ev->v);
    else
        r = -1;
    if (r >= 0) {
        cmd = r;
        if (fd_50F6_0A06 == 1) {
            cmd = spiderCmds[cmd];
            if (cmd == 11 && ((char)dos_keyboard_modifiers() & 8))
                cmd = 12;
        } else if (fd_50F6_04C2 == 0x40 && fd_3D57_0C24 == 0)
            cmd = antCmds[cmd];
        else {
            cmd = nestCmds[cmd];
            if (cmd == 2 && ((char)dos_keyboard_modifiers() & 3))
                cmd = 3;
        }
        YellowCommand(cmd);
    }
    return r;
}

void  SetExpTool(int16_t tool)
{
    native_state_CurExpTool.signed_value = tool;
}

extern void  UpdateEdit(void);

void  DoWarnSetB(struct Event  *ev)
{
    struct Rect r;

    win_GetObjRect(0x12, &r);
    native_state_fd_50F6_0FFE.signed_value = (r.bottom - ev->v) * 100 / (r.bottom - r.top);
    UpdateEdit();
}


void  DoHealthSetY(struct Event  *ev)
{
    struct Rect r;

    win_GetObjRect(0x11, &r);
    native_state_fd_50F6_0FBA.signed_value = (r.bottom - ev->v) * 100 / (r.bottom - r.top);
    UpdateEdit();
}

extern int16_t  win_IsWinInFront(int16_t win);
extern void  OpenMapYard(void);
extern void  OpenEditWindow(void);

void  DoTab(void)
{
    if (win_IsWinInFront(0))
        OpenMapYard();
    else
        OpenEditWindow();
}

#pragma pack(pop)
