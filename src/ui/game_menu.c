/*
 * Updates game menu entries and handles menu commands. It also manages pause state and the Pause
 * or Unpause label.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS: overlay section 11 (S11); segment 35F5; complete original translation unit.
 * Windows: SIMANT, from recorded function pairs in the Windows symbol inventory.
 */

#include "audio_ids.h"
#include "events_ids.h"
#include "windows_ids.h"

extern int far GameSpeed;
extern void far SetMenuItemState(int id, int state);
extern int far GamePaused;
extern void far SetMenuOptionText(int id, char far *text);
extern int far OptionStates[];

void far SetMenuEntries(void)
{
    int item;
    int i;

    for (item = 0x43; item <= 0x46; item++)
        SetMenuItemState(item - 1, (GameSpeed == item - 0x43) ? 0x10 : 0x20);
    SetMenuOptionText(0x41, GamePaused ? " Unpause" : " Pause");
    for (i = 0, item = 0x31; item <= 0x36; i++, item++)
        SetMenuItemState(item - 1, OptionStates[i] ? 0x10 : 0x20);
}

void far SetPause(int value);

void far PauseGame(int value)
{
    SetPause(value);
}

extern int far CurGameTool;
extern void far EndLifeTransferMode(void);
extern void far EndTargetMode(void);
extern char far * far * far WindPromptStrs;
extern void far EditMessage(void far *, long, int);
extern void far clip_SetWin(int win);
extern void _fastcall win_SetObjSelectedState(int obj, int state);
extern void far clip_Off(void);

void far SetPause(int value)
{
    if (value == 0) {
        if (CurGameTool == 10)
            EndLifeTransferMode();
        else if (CurGameTool == 11)
            EndTargetMode();
    }
    GamePaused = value;
    if (value != 0) {
        if (CurGameTool == -1)
            EditMessage(WindPromptStrs[2], -2L, 1);
        else if (CurGameTool == 10)
            EditMessage(WindPromptStrs[3], -2L, 1);
        else if (CurGameTool == 11)
            EditMessage(WindPromptStrs[17], -2L, 1);
    } else
        EditMessage(0L, -2L, 1);
    clip_SetWin(WIN_EDIT);
    win_SetObjSelectedState(0xf, value);
    clip_Off();
    SetMenuEntries();
}

#include "event.h"

extern void far AboutDialog(void);
extern void far myBeginSong(int id, int arg);
extern int far NewGame(int a);
extern int far ui_pending_menu_item;
extern void far OpenEditWindow(void);
extern void far OpenMapYard(void);
extern void far OpenModeWindow(void);
extern void far OpenCasteWindow(void);
extern void far OpenHistoryWindow(void);
extern void far OpenInfoWindow(void);
extern void far ScoreDialog(void);
extern int far YardMode;
extern void far SetYardMode(int newMode);
extern int far MapPlane;
extern void far SetMapPlane(int plane);
extern int _fastcall win_IsWinOpen(int win);
extern void far MapToYard(void);
extern void far StopSong(void);

void far ProcMenu(struct Event far *ev)
{
    int item;
    int n;

    item = ev->code & 0xff;
    switch (item) {
    
    case MENU_CMD_ABOUT:
        AboutDialog();
        break;
    case MENU_CMD_NEW:
        myBeginSong(SONG_INTRO, 0x7e);
        NewGame(0);
        break;
    case MENU_CMD_LOAD:
    case MENU_CMD_SAVE:
    case MENU_CMD_SAVE_AS:
    case MENU_CMD_QUIT:
        ui_pending_menu_item = item;
        break;
    case MENU_CMD_EDIT:
        OpenEditWindow();
        break;
    case MENU_CMD_MAP:
        OpenMapYard();
        break;
    case MENU_CMD_BEHAVIOR:
        OpenModeWindow();
        break;
    case MENU_CMD_CASTE:
        OpenCasteWindow();
        break;
    case MENU_CMD_HISTORY:
        OpenHistoryWindow();
        break;
    case MENU_CMD_INFO:
        OpenInfoWindow();
        break;
    case MENU_CMD_STATUS:
        ScoreDialog();
        break;
    case MENU_CMD_YARD:
    case MENU_CMD_HOUSE:
    case MENU_CMD_STRATEGIC:
    case MENU_CMD_GRAPHIC:
        n = item - 0x21;
        if (n != YardMode)
            SetYardMode(n);
        if (MapPlane != 0)
            SetMapPlane(0);
        if (!win_IsWinOpen(WIN_YARD))
            MapToYard();
        break;
    case MENU_CMD_SURFACE:
        SetMapPlane(1);
        break;
    case MENU_CMD_BLACK_NEST:
        SetMapPlane(2);
        break;
    case MENU_CMD_RED_NEST:
        SetMapPlane(3);
        break;
    case MENU_CMD_MUSIC:
        StopSong();
    toggle:
        OptionStates[item - 0x31] = !OptionStates[item - 0x31];
        SetMenuEntries();
        break;
    case MENU_CMD_PAUSE:
        GamePaused ^= 1;
        SetPause(GamePaused);
        break;
    case MENU_CMD_SLOW:
        n = 0;
        goto speed;
    case MENU_CMD_NORMAL:
        n = 1;
        goto speed;
    case MENU_CMD_FAST:
        n = 2;
        goto speed;
    case MENU_CMD_ULTRA:
        n = 3;
    speed:
        GameSpeed = n;
        SetMenuEntries();
        break;
    default:
        if (item >= 0x31 && item <= 0x36)
            goto toggle;
        break;
    }
}
