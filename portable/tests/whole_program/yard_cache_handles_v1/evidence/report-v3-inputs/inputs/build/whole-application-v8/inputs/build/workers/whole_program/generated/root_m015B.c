#include "portable/whole_program/state/startup_globals_v1.h"
#include "dos_types.h"
#include "portable/whole_program/platform/dos_memory.h"
#include "portable/whole_program/platform/dos_io.h"
uint8_t dos_keyboard_modifiers(void);
#include "portable/whole_program/platform/graphics_source_fields.h"
#include "portable/whole_program/state/game_views.h"
#include "simulation_state_50f6.h"
#include "native_owners.h"
#pragma pack(push, 2)
/* Root module, code frame 015B: map/yard mode control and ant-list commands
 * (Win16 unit AddSomeAnts .. MysteryButton). */

extern int16_t  ListIndexA;
extern int16_t  fd_3D57_0798;
extern void  AddBlackAnts(int16_t count);
extern void  AddRedAnts(int16_t count);
extern void  FullCount(void);

void  AddSomeAnts(int16_t kind)
{
    int16_t count;

    count = ListIndexA;
    if (count < 1000) {
        if (fd_3D57_0798 == 1) {
            if (kind == 1)
                AddBlackAnts(1000 - count);
            else
                AddRedAnts(1000 - count);
        } else if (kind == 1) {
            AddBlackAnts(0x20);
        } else {
            AddRedAnts(0x20);
        }
    }
    FullCount();
}

extern void  CompactListA(void);
extern uint8_t  AlistT[];
extern void  DeadAntHere(int16_t x, int16_t y, int16_t type);
extern uint8_t  AlistY[];
extern uint8_t  AlistX[];
extern int16_t  IsItYellow(int16_t level, int16_t x, int16_t y);

void  KillSomeAnts(int16_t mode)
{
    int16_t i;
    int16_t n;
    int16_t type;

    CompactListA();
    FullCount();
    n = 0;
    for (i = ListIndexA - 1; i >= 0; i--) {
        type = AlistT[i];
        if (mode == 1) {
            if (!(type & 0x80)) {
                DeadAntHere(AlistX[i], AlistY[i], 0);
                AlistT[i] = 0;
                if (++n > 50)
                    break;
            }
        } else {
            if (type & 0x80) {
                if (!IsItYellow(1, AlistX[i], AlistY[i])) {
                    DeadAntHere(AlistX[i], AlistY[i], 1);
                    AlistT[i] = 0;
                    if (++n > 50)
                        break;
                }
            }
        }
    }
    CompactListA();
    FullCount();
}

extern uint8_t  MapA[128][64];
extern int16_t  IsItFood(int16_t tile);
extern int16_t  SRand16(void);

void  SubtractFood(void)
{
    int16_t row, column;

    for (row = 0; row < 0x80; row++)
        for (column = 0; column < 0x40; column++)
            if (IsItFood(MapA[row][column]) == 1)
                MapA[row][column] = SRand16();
    native_state_fd_50F6_1040.signed_value = 0;
}


void  SetEditMode(int16_t value)
{
    native_state_fd_50F6_0D70.signed_value = value;
}

static int16_t g_1960[5] = { 0x109, 0x10a, 0x10c, 0x10d, 0x10b };

extern int16_t  fd_3D57_07C8;
void  SetYardMode(int16_t newMode);
void  SetMapPlane(int16_t plane);
extern void  SetMapTitle(void);
extern void  win_MakeObjSelected(int16_t obj);
extern void  win_MakeGroupUnselected(int16_t win, int16_t group);

void  SetMapModeAnt(int16_t mode)
{
    if (fd_3D57_07C8 == mode && mode >= 4 && mode <= 8)
        mode = 1;
    switch (mode) {
    case 0:
        fd_3D57_07C8 = mode;
        SetYardMode(native_state_YardMode.signed_value);
        break;
    case 4:
    case 5:
    case 6:
    case 7:
    case 8:
        if (native_state_MapPlane.signed_value != 1)
            SetMapPlane(1);
    case 1:
    case 2:
    case 3:
        fd_3D57_07C8 = mode;
        SetMapTitle();
        if (mode >= 4 && mode <= 8)
            win_MakeObjSelected(g_1960[mode - 4]);
        else
            win_MakeGroupUnselected(0x100, 2);
        break;
    }
}

static int16_t g_1984[4] = { 0x1908, 0x1908, 0x1909, 0x190a };

extern int16_t  WinPrintf(char  *format, ...);
extern void  win_LockWin(int16_t win);
extern void  win_MakeObjInvisible(int16_t obj);
extern void  win_UnlockWin(int16_t win);
extern void  win_YardClosed(void);
extern void  win_MakeObjVisible(int16_t obj);
extern void  win_SetObjBitmap(int16_t obj, int16_t bitmap);
extern int16_t  win_IsWinOpen(int16_t win);
extern void  clip_Push(void);
extern void  clip_SetWin(int16_t win);
extern void  win_DrawObjectNum(int16_t objNum);
extern void  clip_Pop(void);
extern void  win_Swap(int16_t from, int16_t to);
extern void  DrawYard(void);

void  SetYardMode(int16_t newMode)
{
    if (newMode == 4) {
        SetMapPlane(native_state_fd_50F6_0332.signed_value);
    } else {
        WinPrintf("\nYardmode=%d, newMode=%d", native_state_YardMode.signed_value, newMode);
        if (newMode != 0 && newMode != 1) {
            native_state_YardMode.signed_value = newMode;
            win_LockWin(0x1900);
            win_MakeObjInvisible(0x1903);
            if (SIM_GRAPHICS_SOURCE_g_3DB2 != 0x140)
                win_MakeObjInvisible(0x190f);
            win_UnlockWin(0x1900);
            win_YardClosed();
        } else {
            native_state_YardMode.signed_value = newMode;
            win_LockWin(0x1900);
            win_MakeObjVisible(0x1903);
            if (SIM_GRAPHICS_SOURCE_g_3DB2 != 0x140)
                win_MakeObjVisible(0x190f);
            win_UnlockWin(0x1900);
            win_YardClosed();
            win_SetObjBitmap(0x1903, newMode + 7000);
            if (win_IsWinOpen(0x1900)) {
                clip_Push();
                clip_SetWin(0x1900);
                win_DrawObjectNum(0x1903);
                if (SIM_GRAPHICS_SOURCE_g_3DB2 != 0x140)
                    win_DrawObjectNum(0x190f);
                clip_Pop();
            }
        }
        if (!win_IsWinOpen(0x1900) && win_IsWinOpen(0x100))
            win_Swap(0x100, 0x1900);
        clip_Push();
        clip_SetWin(0x1900);
        win_MakeObjSelected(g_1984[native_state_YardMode.signed_value]);
        clip_Pop();
        DrawYard();
    }
    SetMapTitle();
}

typedef struct {
    int16_t x;
    int16_t y;
} Point;

extern int16_t  fd_50F6_0FFA;
extern int16_t  fd_50F6_0FB6;
extern void  InvalEuMap(int16_t left, int16_t top, int16_t right, int16_t bottom);
extern int16_t  fd_50F6_0F36;
extern void  CenterEdit(int16_t x, int16_t y);
extern void  UpdateEdit(void);
extern void  f_0250_0ED2(void);
extern void  clip_Off(void);

void  SetMapPlaneLocation(int16_t plane, int16_t x, int16_t y)
{
    int16_t win, obj;

    if (plane != 0)
        InvalEuMap(0, 0, fd_50F6_0FB6, fd_50F6_0FFA);
    else
        native_state_fd_50F6_0332.signed_value = native_state_MapPlane.signed_value;
    native_state_MapPlane.signed_value = plane;
    if (plane == 1)
        fd_50F6_0F36 = 0x80 - fd_50F6_0FB6;
    else
        fd_50F6_0F36 = 0x40 - fd_50F6_0FB6;
    if (native_state_MapPlane.signed_value != 0) {
        CenterEdit(x, y);
        UpdateEdit();
        f_0250_0ED2();
    } else {
        (*((Point *)native_sim_state_fd_50F6_07BC.raw_bytes)) = (*((Point *)native_sim_state_fd_50F6_07CA.raw_bytes));
    }
    SetMapModeAnt(native_state_MapPlane.signed_value);
    win = obj = 0;
    switch (native_state_MapPlane.signed_value) {
    case 0:
        obj = 0x105;
        break;
    case 1:
        win = 8;
        obj = 0x106;
        break;
    case 2:
        win = 9;
        obj = 0x107;
        break;
    case 3:
        win = 10;
        obj = 0x108;
        break;
    }
    if (win) {
        clip_SetWin(0);
        win_MakeObjSelected(win);
        clip_Off();
    }
    if (obj) {
        clip_SetWin(0x100);
        win_MakeObjSelected(obj);
        win_MakeGroupUnselected(0x100, 2);
        clip_Off();
    }
}

extern int16_t  fd_50F6_0AA6;

void  GotoMapPoint(int16_t plane, int16_t x, int16_t y)
{
    if (native_state_MapPlane.signed_value == plane && plane > 0) {
        CenterEdit(x, y);
        fd_50F6_0AA6 = 0;
    } else {
        SetMapPlaneLocation(plane, x, y);
    }
}

extern int16_t  fd_3D57_07C0[];

void  SetMapPlane(int16_t plane)
{
    Point pt;

    if (plane != 0)
        InvalEuMap(0, 0, fd_50F6_0FB6, fd_50F6_0FFA);
    else
        native_state_fd_50F6_0332.signed_value = native_state_MapPlane.signed_value;
    native_state_MapPlane.signed_value = plane;
    if (plane == 1)
        fd_50F6_0F36 = 0x80 - fd_50F6_0FB6;
    else
        fd_50F6_0F36 = 0x40 - fd_50F6_0FB6;
    SetEditMode(fd_3D57_07C0[native_state_MapPlane.signed_value]);
    switch (native_state_MapPlane.signed_value) {
    case 0:
        pt = (*((Point *)native_sim_state_fd_50F6_07BC.raw_bytes));
        break;
    case 1:
        pt = (*((Point *)native_sim_state_fd_50F6_0596.raw_bytes));
        break;
    case 2:
        pt = (*((Point *)native_sim_state_fd_50F6_06A6.raw_bytes));
        break;
    case 3:
        pt = (*((Point *)native_sim_state_fd_50F6_072E.raw_bytes));
        break;
    }
    SetMapPlaneLocation(plane, pt.x, pt.y);
    if (native_state_MapPlane.signed_value != 0)
        CenterEdit(pt.x, pt.y);
    SetMapModeAnt(native_state_MapPlane.signed_value);
    UpdateEdit();
}

extern int16_t  MePlane;
extern int16_t  MeLocY;
extern int16_t  MeLocX;

void  CenterAnt(void)
{
    native_state_fd_50F6_1074.signed_value = 1;
    if (MePlane != native_state_MapPlane.signed_value)
        SetMapPlane(MePlane);
    CenterEdit(MeLocX, MeLocY);
}

extern int16_t  fd_50F6_0EAC;
extern void  myBeginSound(int16_t a, int16_t b, int16_t c);

void  GotoMyAnt(void)
{
    native_state_fd_50F6_1074.signed_value = 1;
    if (fd_50F6_0EAC == 3)
        myBeginSound(1, 0, 0x7e);
    else
        GotoMapPoint(MePlane, MeLocX, MeLocY);
}


void  GotoSpider(void)
{
    if (native_state_fd_50F6_0F0C.signed_value == 0)
        myBeginSound(1, 0, 0x7e);
    else
        GotoMapPoint(1, native_state_fd_50F6_0F12.signed_value >> 4, native_state_fd_50F6_0F34.signed_value >> 4);
}

extern Point  fd_3D57_02B4;

void  GotoBQueen(void)
{
    GotoMapPoint(2, fd_3D57_02B4.x, fd_3D57_02B4.y);
}

extern Point  fd_3D57_02B8;

void  GotoRQueen(void)
{
    GotoMapPoint(3, fd_3D57_02B8.x, fd_3D57_02B8.y);
}

void  f_015B_0780(void)
{
}

void  f_015B_0788(void)
{
}

void  f_015B_0790(void)
{
}

extern void  PictStrnDialog(int16_t a, int16_t b, int16_t c);
extern uint8_t  fd_3D57_00A4[][16];
extern int16_t  fd_50F6_04C2;
extern int16_t  fd_3D57_0C24;
extern void  myBeginSong(int16_t id, int16_t arg);
extern void  o12_384C_100A(void);
extern int16_t  fd_50F6_0354;
extern void  InvalQueenStorageDisp(void);
extern int16_t  fd_3E1D_0000[][12];
extern uint8_t  fd_3D57_0164[][16];
extern void  RandWorld(uint16_t seed, int16_t blackSize, int16_t redSize, int16_t x, int16_t y);

void  XferPatch(void)
{
    int16_t x, y;

    y = (*((Point *)native_sim_state_fd_50F6_07BC.raw_bytes)).y;
    x = (*((Point *)native_sim_state_fd_50F6_07BC.raw_bytes)).x;
    if (x == (*((Point *)native_sim_state_fd_50F6_07CA.raw_bytes)).x && (*((Point *)native_sim_state_fd_50F6_07CA.raw_bytes)).y == y)
        return;
    if (fd_50F6_0EAC != 2) {
        myBeginSound(1, 0, 0x7e);
        PictStrnDialog(0, 0x2710, 1);
    } else if (native_state_fd_50F6_03E2.signed_value <= 1 && native_state_BpopT.signed_value <= 1) {
        myBeginSound(1, 0, 0x7e);
        PictStrnDialog(0, 0x2712, 1);
    } else if (fd_3D57_00A4[x][y] < 1 && (fd_50F6_04C2 != 0x40 || fd_3D57_0C24 != 0)) {
        myBeginSound(1, 0, 0x7e);
        PictStrnDialog(0, 0x2714, 1);
    } else {
        myBeginSong(0x2afa, 0x7e);
        (*((Point *)native_sim_state_fd_50F6_07CA.raw_bytes)).x = x;
        (*((Point *)native_sim_state_fd_50F6_07CA.raw_bytes)).y = y;
        o12_384C_100A();
        fd_50F6_0354 = 1;
        native_state_fd_50F6_07C8.signed_value = 0;
        native_state_fd_50F6_0850.signed_value = 0;
        native_state_fd_50F6_06AA.signed_value = 0;
        native_state_fd_50F6_073A.signed_value = 0;
        InvalQueenStorageDisp();
        fd_3D57_0C24 = 1;
        RandWorld(fd_3E1D_0000[y][x], fd_3D57_00A4[x][y], fd_3D57_0164[x][y], x, y);
        if (fd_3D57_0164[x][y] == 0)
            native_state_HealthR.signed_value = 0;
        if ((x << 4) + y > 0x24)
            PictStrnDialog(0, 0x2716, 0);
        else
            PictStrnDialog(0, 0x2717, 0);
    }
}

struct Rect {
    int16_t left;
    int16_t top;
    int16_t right;
    int16_t bottom;
};

struct Event {
    int16_t what;
    int16_t message;
    int16_t x4;
    int16_t modifiers;
    Point where;
    int16_t code;
    int16_t xE;
};

extern void  *  *  fd_50F6_034C;
extern void  EditMessage(void  *, int32_t, int16_t);
extern int16_t  fd_3D57_02C0;
extern int16_t  win_GetEvent(struct Event  *);
extern void  f_1FD2_04D0(Point  *);
extern int16_t  win_IsWinInFront(int16_t);

extern void  InvertPatch(int16_t, int16_t);
extern int16_t  fd_3D57_0C20;
extern void  MakeDMap(int16_t);
extern void  UpdateYard(void);
extern void  myDelay(int32_t);

void  PlaceQueenInYard(void)
{
    int16_t x, y;
    int16_t lastX, lastY;
    int16_t patchX, patchY;
    int16_t done;
    Point pt;
    struct Rect r;
    struct Event ev;

    patchX = -1;
    if (native_state_fd_50F6_07C8.signed_value < 1) {
        myBeginSound(1, 0, 0x7e);
        if (fd_50F6_0EAC != 2)
            EditMessage(fd_50F6_034C[16], 180L, 1);
        else
            EditMessage(fd_50F6_034C[7], 180L, 1);
        return;
    }
    if (fd_3D57_02C0 == 1)
        fd_3D57_02C0 = 0;
    r.left = (*((Point *)native_sim_state_fd_50F6_07CA.raw_bytes)).x - 3;
    r.right = (*((Point *)native_sim_state_fd_50F6_07CA.raw_bytes)).x + 3;
    r.top = (*((Point *)native_sim_state_fd_50F6_07CA.raw_bytes)).y - 3;
    r.bottom = (*((Point *)native_sim_state_fd_50F6_07CA.raw_bytes)).y + 3;
    if (r.left < 0)
        r.left = 0;
    else if (r.left > 11)
        r.left = 11;
    if (r.right < 0)
        r.right = 0;
    else if (r.right > 11)
        r.right = 11;
    if (r.top < 0)
        r.top = 0;
    else if (r.top > 15)
        r.top = 15;
    if (r.bottom < 0)
        r.bottom = 0;
    else if (r.bottom > 15)
        r.bottom = 15;
    do {
        EditMessage(fd_50F6_034C[8], -2L, 1);
        lastY = lastX = -1;
        done = 0;
        while (!done) {
            if (win_GetEvent(&ev) && ev.code == 0x1902) {
                pt = ev.where;
                done = 1;
            } else {
                f_1FD2_04D0(&pt);
            }
            if (!win_IsWinInFront(0x1900))
                goto out;
            y = pt.y - (*((Point *)native_game_fd_50F6_10D2.raw)).y;
            x = pt.x - (*((Point *)native_game_fd_50F6_10D2.raw)).x;
            if (SIM_GRAPHICS_SOURCE_g_3DB2 == 0x140) {
                x = (x + 2) * 2;
                y = (y - 8) * 2;
            }
            y = (y - fd_55B3_2A42[1]) / 10;
            x = (y * 10 - fd_55B3_2A42[0] + x) / 28;
            WinPrintf("\nYARD AREA @ %d, %d  : %d, %d", x, y, 12, 16);
            if (lastX != x || lastY != y) {
                lastX = x;
                lastY = y;
                if (patchX != -1) {
                    InvertPatch(patchX, patchY);
                    patchX = -1;
                }
                if (r.left <= x && r.right >= x && y >= r.top && y <= r.bottom) {
                    if ((*((Point *)native_sim_state_fd_50F6_07CA.raw_bytes)).x != x || (*((Point *)native_sim_state_fd_50F6_07CA.raw_bytes)).y != y) {
                        InvertPatch(x, y);
                        patchX = x;
                        patchY = y;
                    }
                    (*((Point *)native_sim_state_fd_50F6_07BC.raw_bytes)).x = x;
                    (*((Point *)native_sim_state_fd_50F6_07BC.raw_bytes)).y = y;
                }
            }
        }
        if (patchX != -1) {
            InvertPatch(patchX, patchY);
            patchX = -1;
        }
        if (r.left <= x && r.right >= x && y >= r.top && y <= r.bottom) {
            myBeginSong(0x2afb, 0x7e);
            native_state_fd_50F6_07C8.signed_value--;
            fd_3D57_00A4[x][y]++;
            native_state_fd_50F6_0A90.signed_value++;
            MakeDMap(fd_3D57_0C20 = 1);
            o12_384C_100A();
            EditMessage(fd_50F6_034C[9], 120L, 1);
            if (native_state_fd_50F6_07C8.signed_value <= 0)
                return;
            UpdateYard();
        } else {
            EditMessage(fd_50F6_034C[10], 120L, 1);
            myBeginSound(1, 0, 0x7e);
            if ((char)dos_keyboard_modifiers() & 3)
                myDelay(30L);
        }
    } while ((char)dos_keyboard_modifiers() & 3);
    return;
out:
    EditMessage(0L, -2L, 1);
}

extern int16_t  RRand(int16_t limit);
extern void  AddFood(int16_t count, int16_t sound);
extern void  myBeginSoundReverse(int16_t a, int16_t b, int16_t c);
extern void  f_00DF_00E0(int16_t a);
extern void  MakeNewHoleR(int16_t x);
extern void  MakeNewHoleB(int16_t x);
extern int16_t  fd_3D57_0C18;
extern int16_t  fd_3D57_0C14;
extern int16_t  fd_3D57_0C12;

void  MysteryButton(void)
{
    int16_t i;

    switch (RRand(15)) {
    case 0:
    case 1:
        AddSomeAnts(0);
        AddSomeAnts(0);
        break;
    case 2:
        AddSomeAnts(1);
        AddSomeAnts(1);
        break;
    case 3:
        KillSomeAnts(0);
        KillSomeAnts(0);
        break;
    case 4:
        KillSomeAnts(1);
        KillSomeAnts(1);
        break;
    case 5:
        AddFood(0x96, 1);
        break;
    case 6:
        myBeginSoundReverse(0x20, 0, 0x7e);
        SubtractFood();
        break;
    case 7:
        f_00DF_00E0(0);
        break;
    case 8:
        for (i = 0; i < 0x20; i++)
            MakeNewHoleR(i * 2);
        break;
    case 9:
        for (i = 0; i < 0x20; i++)
            MakeNewHoleB(i * 2);
        break;
    case 10:
        fd_3D57_0C18 = 0;
        native_state_HealthB.signed_value = 0;
        native_state_HealthR.signed_value = 0;
        break;
    case 11:
        if (fd_3D57_0C14 = !fd_3D57_0C14)
            myBeginSound(2, 0, 0x7e);
        else
            myBeginSound(1, 0, 0x7e);
        break;
    case 12:
        fd_3D57_0C12 = !fd_3D57_0C12;
        break;
    case 13:
        PictStrnDialog(0, 0x2726, 0);
        f_00DF_00E0(1);
        PictStrnDialog(0, 0x2728, 0);
        break;
    case 14:
        native_state_fd_50F6_06AC.signed_value = 8;
        myBeginSound(2, 0x2b77, 0x7e);
        break;
    }
}

#pragma pack(pop)
