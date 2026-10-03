#include "dos_types.h"
#include "portable/whole_program/platform/dos_memory.h"
#include "portable/whole_program/platform/dos_io.h"
#include "portable/whole_program/platform/graphics_source_fields.h"
#include "native_owners.h"
#pragma pack(push, 2)
extern int16_t  fd_3D57_07CC[];
/* Overlay section S11, code frame 35F5: menu entry states (Win16 SetMenuEntries twin), pause
 * switch (Win16 PauseGame/SetPause twins) and the menu command dispatcher ProcMenu. */

extern void  SetMenuItemState(int16_t id, int16_t state);
extern void  f_1FD2_0135(int16_t id, char  *text);
extern int16_t  fd_3D57_07A8[];

void  SetMenuEntries(void)
{
    int16_t item;
    int16_t i;

    for (item = 0x43; item <= 0x46; item++)
        SetMenuItemState(item - 1, ((fd_3D57_07CC[0]) == item - 0x43) ? 0x10 : 0x20);
    f_1FD2_0135(0x41, native_state_fd_50F6_047E.signed_value ? " Unpause" : " Pause");
    for (i = 0, item = 0x31; item <= 0x36; i++, item++)
        SetMenuItemState(item - 1, fd_3D57_07A8[i] ? 0x10 : 0x20);
}

void  SetPause(int16_t value);

void  PauseGame(int16_t value)
{
    SetPause(value);
}

extern void  EndLifeTransferMode(void);
extern void  EndTargetMode(void);
extern char  *  *  fd_50F6_034C;
extern void  EditMessage(void  *, int32_t, int16_t);
extern void  clip_SetWin(int16_t win);
extern void  win_SetObjSelectedState(int16_t obj, int16_t state);
extern void  clip_Off(void);

void  SetPause(int16_t value)
{
    if (value == 0) {
        if (native_state_fd_50F6_105E.signed_value == 10)
            EndLifeTransferMode();
        else if (native_state_fd_50F6_105E.signed_value == 11)
            EndTargetMode();
    }
    native_state_fd_50F6_047E.signed_value = value;
    if (value != 0) {
        if (native_state_fd_50F6_105E.signed_value == -1)
            EditMessage(fd_50F6_034C[2], -2L, 1);
        else if (native_state_fd_50F6_105E.signed_value == 10)
            EditMessage(fd_50F6_034C[3], -2L, 1);
        else if (native_state_fd_50F6_105E.signed_value == 11)
            EditMessage(fd_50F6_034C[17], -2L, 1);
    } else
        EditMessage(0L, -2L, 1);
    clip_SetWin(0);
    win_SetObjSelectedState(0xf, value);
    clip_Off();
    SetMenuEntries();
}

struct Event {
    int16_t what;
    int16_t where[2];
    int16_t when[2];
    int16_t modifiers;
    int16_t message;
};

extern void  AboutDialog(void);
extern void  myBeginSong(int16_t id, int16_t arg);
extern int16_t  NewGame(int16_t a);
extern int16_t  fd_55B3_2CBC;
extern void  OpenEditWindow(void);
extern void  OpenMapYard(void);
extern void  OpenModeWindow(void);
extern void  OpenCasteWindow(void);
extern void  OpenHistoryWindow(void);
extern void  OpenInfoWindow(void);
extern void  ScoreDialog(void);
extern void  SetYardMode(int16_t newMode);
extern void  SetMapPlane(int16_t plane);
extern int16_t  win_IsWinOpen(int16_t win);
extern void  MapToYard(void);
extern void  StopSong(void);

void  ProcMenu(struct Event  *ev)
{
    int16_t item;
    int16_t n;

    item = ev->message & 0xff;
    switch (item) {
    
    case 1:
        AboutDialog();
        break;
    case 3:
        myBeginSong(0x2711, 0x7e);
        NewGame(0);
        break;
    case 4:
    case 5:
    case 6:
    case 8:
        fd_55B3_2CBC = item;
        break;
    case 0x11:
        OpenEditWindow();
        break;
    case 0x12:
        OpenMapYard();
        break;
    case 0x13:
        OpenModeWindow();
        break;
    case 0x14:
        OpenCasteWindow();
        break;
    case 0x15:
        OpenHistoryWindow();
        break;
    case 0x16:
        OpenInfoWindow();
        break;
    case 0x17:
        ScoreDialog();
        break;
    case 0x21:
    case 0x22:
    case 0x23:
    case 0x24:
        n = item - 0x21;
        if (n != native_state_YardMode.signed_value)
            SetYardMode(n);
        if (native_state_MapPlane.signed_value != 0)
            SetMapPlane(0);
        if (!win_IsWinOpen(0x1900))
            MapToYard();
        break;
    case 0x26:
        SetMapPlane(1);
        break;
    case 0x27:
        SetMapPlane(2);
        break;
    case 0x28:
        SetMapPlane(3);
        break;
    case 0x32:
        StopSong();
    toggle:
        fd_3D57_07A8[item - 0x31] = !fd_3D57_07A8[item - 0x31];
        SetMenuEntries();
        break;
    case 0x41:
        native_state_fd_50F6_047E.signed_value ^= 1;
        SetPause(native_state_fd_50F6_047E.signed_value);
        break;
    case 0x43:
        n = 0;
        goto speed;
    case 0x44:
        n = 1;
        goto speed;
    case 0x45:
        n = 2;
        goto speed;
    case 0x46:
        n = 3;
    speed:
        (fd_3D57_07CC[0]) = n;
        SetMenuEntries();
        break;
    default:
        if (item >= 0x31 && item <= 0x36)
            goto toggle;
        break;
    }
}

#pragma pack(pop)
