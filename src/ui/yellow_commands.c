/*
 * Dispatches editor mouse actions and yellow ant commands. It handles births, deaths, goals,
 * dialogs, alarm drops and special interactions such as laser fire.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS: overlay section 22 (S22); segment 39C7; complete original translation unit.
 * Windows: SIMANT, from recorded function pairs in the Windows symbol inventory. Some pairs are
 * HIGH confidence, not confirmed.
 *
 * (processEdit..YellowHelp; Win16 SIMANT unit processEdit..YellowHelp).
 * Built /AL /Os /Oe /Og /Zi under MSC 6.00AX: 6.00A allocates CONST segment words for
 * far variables whose loads were all hoisted to immediate segments (YellowDeath), 6.00AX
 * does not.  /Zi (a code record per function) reproduces the original relocation order
 * across all 15 functions, /Zd cannot (SetGoalsY and YellowCommandKey start records).
 * The one-line ifs and the while loops in YellowDeath place the line-number record
 * breaks (every 52 entries) where the original has them.  The MapPnt/editTileRect
 * struct types decide the imul operand order in DoLaserFire; the MeLocY
 * declaration after 0AE8 decides the compare order in YellowCommandKey.
 */

#include "audio_ids.h"
#include "events_ids.h"
#include "flags_ids.h"
#include "hardware_ids.h"
#include "pictures_ids.h"
#include "strings_ids.h"
#include "windows_ids.h"

#include "event.h"

extern int far WinPrintf(char far *format, ...);
extern int _fastcall win_IsWinInFront(int win);
extern long far TickCount(void);
extern int _fastcall win_GetEvent(struct Event far *ev);
#include "rect.h"
#include "pt.h"

extern struct Rect far editTileRect;
extern int far tileWidth;
extern struct Pt far MapPnt;
extern int far tileHeight;
extern int far CurGameType;
extern void far processExp(int x, int y, int shift);
extern int far YellowDied;
extern int far CurGameTool;
extern int far fd_50F6_048C;
extern int far IsItYellow(int plane, int x, int y);
extern int far myButton(void);
extern void far AntMenu(struct Event far *ev);
extern int far GetLife(int plane, int x, int y);
extern void far f_015B_0653(void);
extern int far MapPlane;
extern int far MagnifyMenu(int x, int y, int plane);
extern int far MeMode;
extern int far IsYellowAnt(int life);
extern int far FindAntIndex(int plane, int x, int y, int life);
extern int far MeTargIndex;
extern int far MeColor;
int far MeCmd;
extern int far MeTargLife;
extern int far MeTargLifePlane;
extern int far MeTargLifeX;
extern int far MeTargLifeY;
void far SetGoalsY(int plane, int x, int y);
int far MeMoveMe;
extern int far IsItDigable(int plane, int x, int y);
extern int far GetMap(int plane, int x, int y);
extern int far IsThisGrass(int plane, int tile);
extern int far MeType;
extern int far IsLiftable(int plane, int x, int y);
extern void far ExchangeLives(int plane, int x, int y);
void far processSpider(int x, int y, int mode);

void far processEdit(struct Event far *ePtr)
{
    struct Event ev;
    long t;
    int shift;
    int x;
    int y;
    int life;

    if ((*(unsigned char far *)BIOS_KEYBOARD_FLAGS_FARPTR & 8) == 1)
        shift = 1;
    else
        shift = (ePtr->modifiers & EVENT_MOD_DOUBLE_CLICK_MASK) != 0;
    WinPrintf("ePtr->mouse_flags=%x", ePtr->modifiers);
    if (!shift && win_IsWinInFront(WIN_EDIT)) {
        t = TickCount() + 6;
        while (TickCount() < t) {
            if (win_GetEvent(&ev) == 1 && (ev.modifiers & EVENT_MOD_DOUBLE_CLICK_MASK) && ev.code == ePtr->code) {
                ePtr = &ev;
                break;
            }
        }
        shift = (ePtr->modifiers & EVENT_MOD_DOUBLE_CLICK_MASK) != 0;
    }
    x = (ePtr->h - editTileRect.left) / tileWidth + MapPnt.x;
    y = (ePtr->v - editTileRect.top) / tileHeight + MapPnt.y;
    if (CurGameType == 3) {
        processExp(x, y, shift);
        return;
    }
    if (YellowDied) YellowDied = 0;
    switch (CurGameTool) {
    case -1:
        if (!shift) {
            if (IsItYellow(fd_50F6_048C, x, y) == 1) {
                if (myButton() == 1) {
                    AntMenu(ePtr);
                    return;
                }
                if (GetLife(fd_50F6_048C, x, y) != 0xfe) f_015B_0653();
                return;
            }
            if (myButton() == 1 && MagnifyMenu(x, y, MapPlane) >= 0)
                return;
        } else if (MeMode == 0 && (life = GetLife(MapPlane, x, y)) >= 0
                   && (life & 0x7f) >= 8 && !IsYellowAnt(life)) {
            if ((MeTargIndex = FindAntIndex(MapPlane, x, y, life)) < 0)
                return;
            MeCmd = ((MeColor ^ life) & 0x80) ? 3 : 4;
            MeTargLife = life;
            if (MapPlane == 0)
                MeTargLifePlane = 1;
            else
                MeTargLifePlane = MapPlane;
            MeTargLifeX = x;
            MeTargLifeY = y;
            SetGoalsY(MapPlane, x, y);
            MeMoveMe = 1;
            return;
        }
        WinPrintf("\nMapPlane=%d", MapPlane);
        if (MapPlane <= 1) {
            if (MeMode == 1) {
                processSpider(x, y, shift);
                return;
            }
            MeCmd = shift;
        } else {
            if (MeMode != 0)
                return;
            if (shift == 1) {
                if (IsItDigable(MapPlane, x, y) == 1
                    || (fd_50F6_048C >= 2 && y <= 0
                        && IsThisGrass(MapPlane, GetMap(MapPlane, x, y)) == 1))
                    MeCmd = 2;
                else if ((MeType & 8) || IsLiftable(MapPlane, x, y))
                    MeCmd = 1;
                else
                    MeCmd = 2;
            } else
                MeCmd = 0;
        }
        SetGoalsY(MapPlane, x, y);
        MeMoveMe = 1;
        return;
    case 10:
        ExchangeLives(MapPlane == 0 ? 1 : MapPlane, x, y);
        return;
    case 11:
        if (MapPlane <= 1 && MeMode == 1)
            processSpider(x, y, shift);
        return;
    }
}

extern void far myBeginSound(int a, int b, int c);
extern char near gfx_display_mode;
extern void far clip_Push(void);
extern int _fastcall win_IsWinOpen(int win);
extern void far clip_SetWin(int win);
extern int far * near clip_active_list_offset;
extern void far edit_set_viewport_clip(void);
extern int far ConvColor(int color);
extern void (far * near gfx_draw_line_hook)(int x0, int y0, int x1, int y1, int color);
extern void (far * near gfx_fill_rect_hook)(int x0, int y0, int x1, int y1, int color);
extern void far win_EditChanged(void);
extern void far clip_SubInclude(struct Rect far *rect);
extern int far mapXsize;
extern struct Rect far map_viewport_rect;
extern int far mapYsize;
extern int far map_yard_redraw_pending;
extern void far clip_Pop(void);

void far DoLaserFire(int x1, int y1, int x2, int y2)
{
    int sx;
    int sy;
    int ex;
    int ey;
    int originX;
    int originY;

    myBeginSound(SND_LASER, 0x8265, 0x3f);
    if (MapPlane == 1) {
        if (gfx_display_mode == 2) {
            x2 = (3 * x2) / 4;
            y2 = (3 * y2) / 4;
            x1 = (3 * x1) / 4;
            y1 = (3 * y1) / 4;
        }
        clip_Push();
        if (win_IsWinOpen(WIN_EDIT)) {
            clip_SetWin(WIN_EDIT);
            if (clip_active_list_offset[1] != 0x8000) {
                edit_set_viewport_clip();
                originX = MapPnt.x * tileWidth - editTileRect.left;
                originX = -originX;
                originY = tileHeight * MapPnt.y - editTileRect.top;
                originY = -originY;
                ex = originX + x1;
                ey = originY + y1;
                sx = originX + x2;
                sy = originY + y2;
                gfx_draw_line_hook(ex, ey, sx, sy, ConvColor(3));
                gfx_draw_line_hook(ex + 1, ey + 1, sx + 1, sy + 1, ConvColor(3));
                gfx_fill_rect_hook(sx, sy, sx + 2, sy + 2, ConvColor(2));
                win_EditChanged();
            }
        }
        if (win_IsWinOpen(WIN_MAP)) {
            clip_SetWin(WIN_MAP);
            clip_SubInclude(&map_viewport_rect);
            sx = (x2 / tileWidth) * mapXsize + map_viewport_rect.left;
            sy = (y2 / tileHeight) * mapYsize + map_viewport_rect.top;
            ex = (x1 / tileWidth) * mapXsize + map_viewport_rect.left;
            ey = (y1 / tileHeight) * mapYsize + map_viewport_rect.top;
            gfx_draw_line_hook(ex, ey, sx, sy, ConvColor(3));
            gfx_draw_line_hook(ex + 1, ey + 1, sx + 1, sy + 1, ConvColor(3));
            gfx_fill_rect_hook(sx, sy, sx + 2, sy + 2, ConvColor(1) | 0x20);
            map_yard_redraw_pending = 1;
        }
        clip_Pop();
    }
}

extern int far Starg;
extern int far StargLife;
extern int far SMode;
extern int far SuserX;
extern int far SuserY;
extern unsigned char far LifeA[64][64];
extern int far MeSMode;
extern void far EndTargetMode(void);

void far processSpider(int x, int y, int mode)
{
    int life;
    int idx;

    if (mode < 1 && CurGameTool != 11) {
        Starg = -2;
        StargLife = -1;
        SMode = 0;
        SuserX = x;
        SuserY = y;
        MeCmd = mode;
        return;
    }
    life = LifeA[x][y];
    if (life != 0) {
        idx = FindAntIndex(1, x, y, life);
        if (idx >= 0) {
            StargLife = life;
            Starg = idx;
            SMode = 2;
            if (CurGameTool == 11) {
                myBeginSound(SND_COMMAND_ACK, 0, 0x7e);
                MeSMode = 6;
                EndTargetMode();
            }
            return;
        }
    }
    if (CurGameTool == 11) {
        myBeginSound(SND_REJECT, 0, 0x7e);
        return;
    }
    Starg = -2;
    StargLife = -1;
    SMode = 0;
    SuserX = x;
    SuserY = y;
    MeCmd = mode;
}

extern int far MeGoalPlane;
extern int far fd_50F6_047C;
extern int far MeLastX;
extern int far MeGoalX;
extern int far MeLastY;
extern int far MeGoalY;
extern int far fd_50F6_048A;
int far MeDis;
int far MePrevDis;
int far MeSteps;
extern int far MeCrazyCnt;

void far ResetYellowVars(int plane, int x, int y)
{
    fd_50F6_048C = plane;
    MeGoalPlane = plane;
    fd_50F6_047C = x;
    MeLastX = x;
    MeGoalX = x;
    fd_50F6_048A = y;
    MeLastY = y;
    MeGoalY = y;
    MeCmd = 0;
    MeMoveMe = 0;
    MeDis = 0;
    MePrevDis = 0;
    MeSteps = 0;
    MeCrazyCnt = -2;
}

void far SetGoalsY(int plane, int x, int y)
{
    if (plane == 0)
        MeGoalPlane = 1;
    else
        MeGoalPlane = plane;
    MeGoalX = x;
    MeGoalY = y;
    MeCrazyCnt = -2;
    if (plane >= 2 && y < 2) {
        if (x <= 0)
            x = 1;
        else if (x >= 63)
            x = 62;
        MeGoalX = x;
    }
}

extern int far OptionStates[];
extern int far MeEgg;
extern int far MeDir;
extern void far SetMyLife(int plane, int x, int y, int type, int dir, int code);
extern void far ClearMyLife(int plane, int x, int y, int type, int dir);
extern void far f_015B_06A2(void);
extern void far DoEditAndMapUpdateDraw(void);
extern void far myBeginSong(unsigned int id, unsigned int arg);
extern int far mySongIsDone(void);
extern int far win_Events(void);
extern void far myDelay(long ticks);
extern void far SetLife(int plane, int x, int y, int value);
extern void far win_FlushEvents(void);
extern int far MeNestStarted;
extern void far SetMyHealth(int health);
extern long far MacTickCount(void);
extern void far DoEditUpdateDraw(void);
extern void far MakeBlkQueen(int x, int y, int dir);
extern int far CastePopB[6];
extern void far MakeRedQueen(int x, int y, int dir);
extern int far CastePopR[6];
extern int far BpopT;
extern int far RpopT;
extern int far mySoundIsDone(void);
extern void far SetSimCursor(int a);
void far YellowDialog(int bitmap, int promptIndex);

void far YellowBirth(int plane, int x, int y, int type, int mode)
{
    long t;
    int save;
    int oldType;
    int i;

    save = OptionStates[2];
    oldType = MeType;
    OptionStates[2] = 0;
    MeMode = 0;
    if (mode == 0) {
        MeEgg = 1;
        SetMyLife(plane, x, y, 0, MeDir, 0xff);
    } else {
        ClearMyLife(fd_50F6_048C, fd_50F6_047C, fd_50F6_048A, MeType, MeDir);
        SetMyLife(fd_50F6_048C, fd_50F6_047C, fd_50F6_048A, 0x60, MeDir, 0xff);
    }
    if (mode == 0)
        f_015B_06A2();
    DoEditAndMapUpdateDraw();
    if (mode != 0) {
        myBeginSong(SONG_YELLOW_BIRTH_INITIAL, 0x7e);
        t = TickCount() + 300;
        while (!mySongIsDone()) {
            if (TickCount() >= t || win_Events())
                break;
            myDelay(1L);
        }
        SetLife(plane, x, y, 1);
        DoEditAndMapUpdateDraw();
    }
    win_FlushEvents();
    OptionStates[2] = save;
    myBeginSound(SND_EGG_ACTION, 0, 0x7e);
    myDelay(45L);
    ResetYellowVars(fd_50F6_048C, fd_50F6_047C, fd_50F6_048A);
    MeNestStarted = 1;
    SetMyHealth(100);
    if (mode == 0)
        MeDir = oldType == 0x60 ? 2 : 6;
    for (i = 2; i <= 7; i++) {
        t = MacTickCount() + 10;
        if (mode == 0) {
            MeEgg = i;
            SetMyLife(fd_50F6_048C, fd_50F6_047C, fd_50F6_048A, 0, MeDir, 0xff);
        } else
            SetLife(fd_50F6_048C, x, y, i);
        DoEditUpdateDraw();
        while (MacTickCount() < t && !win_Events())
            myDelay(1L);
    }
    win_FlushEvents();
    if (mode != 0)
        while (!mySongIsDone())
            myDelay(5L);
    myBeginSound(SND_BIRTH_OR_FIGHT, 0, 0x7e);
    if (mode == 0) {
        SetMyLife(fd_50F6_048C, fd_50F6_047C, fd_50F6_048A, type, MeDir, 0xff);
    } else {
        ClearMyLife(fd_50F6_048C, fd_50F6_047C, fd_50F6_048A, MeType, MeDir);
        if (fd_50F6_048C == 2) {
            MakeBlkQueen(fd_50F6_047C, fd_50F6_048A, MeDir);
            CastePopB[5]++;
        } else {
            MakeRedQueen(fd_50F6_047C, fd_50F6_048A, MeDir);
            CastePopR[5]++;
        }
        SetMyLife(fd_50F6_048C, x, y, type, MeDir ^ 4, 0xff);
        if (MeColor == 0) {
            CastePopB[1]++;
            CastePopB[4]--;
            BpopT++;
        } else {
            CastePopR[1]++;
            CastePopR[4]--;
            RpopT++;
        }
    }
    DoEditUpdateDraw();
    while (!mySoundIsDone())
        myDelay(5L);
    if (mode != 0)
        myBeginSong(SONG_YELLOW_BIRTH_REPLACEMENT, 0x7e);
    else
        myBeginSong(SONG_YELLOW_BIRTH, 0x7e);
    SetSimCursor(0);
    YellowDialog(PIC_YELLOW_BIRTH_DIALOG, mode + 1);
}

extern void far SetDefaultWindPrompt(int mode);
extern int far DropMyObject(int plane, int x, int y, int tx, int ty);
extern signed char far UnCarryCaste[];
extern void far AnimYellowInsane(int plane, int x, int y, int dir, int type, int cause);
extern int far SRand1(int range);
extern int far MeStartedFight;
extern void far PictStrnDialog(int pict, int strn, int flag);
extern void far SpiderDialog(void);
extern long far BAntsEaten;
extern void far AnimYellowFight(int plane, int x, int y, int dir, int type, int cause);
void far LionDialog(void);
extern long far BAntsKilled;
extern long far BAntsExpired;
extern void far UpdateEverything(void);
extern void far UnRecruit(int all);
extern int far MeDropAlarm;
void far SetAlarmDropState(int state, int quiet);
extern int far ListIndexB;
extern unsigned char far BlistT[];
extern unsigned char far BlistY[];
extern int far RebornY;
extern unsigned char far BlistX[];
extern int far RebornX;
extern unsigned char far LifeB[64][64];
extern int far ListIndexA;
extern unsigned char far AlistT[];
extern unsigned char far AlistY[];
extern unsigned char far AlistX[];
extern int far ListIndexR;
extern unsigned char far RlistT[];
extern unsigned char far RlistY[];
extern unsigned char far RlistX[];
extern unsigned char far LifeR[64][64];
extern int far IsGameOver;
extern int far BlackWon;
extern int far ColonyTotalBlack;
void far SpecialXfer(void);

void far YellowDeath(int cause)
{
    int save;
    int strn;
    int found;
    int i;
    int t;
    int life;

    SetSimCursor(6);
    SetDefaultWindPrompt(1);
    if (MeMode == 0 && (MeType & 8)) {
        save = OptionStates[2];
        OptionStates[2] = 0;
        if (!DropMyObject(fd_50F6_048C, fd_50F6_047C, fd_50F6_048A, fd_50F6_047C, fd_50F6_048A))
            MeType = (MeType & 0x80) | (UnCarryCaste[(MeType & 0x78) >> 3] << 3);
        OptionStates[2] = save;
    }
    f_015B_06A2();
    DoEditAndMapUpdateDraw();
    if (cause >= 7 && cause < 10)
        AnimYellowInsane(fd_50F6_048C, fd_50F6_047C, fd_50F6_048A, MeDir, MeType, cause);
    SetSimCursor(0);
    switch (cause) {
    case 0:
        myBeginSong(SRand1(5) + SONG_DEATH_VARIATION_BASE, 0x7e);
        strn = MeStartedFight ? STR_DEATH_ATTACK_FAILED : STR_DEATH_ENEMY_ATTACK;
        if (OptionStates[3]) PictStrnDialog(PIC_DEATH_FIGHT_OR_ELECTROCUTION, strn, 1);
        break;
    case 1:
        if (OptionStates[3]) SpiderDialog();
        BAntsEaten++;
        myBeginSong(SRand1(5) + SONG_DEATH_VARIATION_BASE, 0x7e);
        AnimYellowFight(fd_50F6_048C, fd_50F6_047C, fd_50F6_048A, MeDir, MeType, cause);
        break;
    case 2:
        if (OptionStates[3]) LionDialog();
        BAntsEaten++;
        myBeginSong(SRand1(5) + SONG_DEATH_VARIATION_BASE, 0x7e);
        AnimYellowFight(fd_50F6_048C, fd_50F6_047C, fd_50F6_048A, MeDir, MeType, cause);
        break;
    case 3:
        myBeginSound(SND_REJECT, 0, 0x7e);
        if (OptionStates[3])
            PictStrnDialog(PIC_NONE, STR_DEATH_ANTS, 1);
        BAntsKilled++;
        break;
    case 4:
        myBeginSound(SND_REJECT, 0, 0x7e);
        if (OptionStates[3])
            PictStrnDialog(PIC_NONE, STR_DEATH_MADNESS, 1);
        BAntsKilled++;
        break;
    case 5:
        myBeginSong(SRand1(5) + SONG_DEATH_VARIATION_BASE, 0x7e);
        if (OptionStates[3])
            PictStrnDialog(PIC_DEATH_FOOT, STR_DEATH_FOOT, 1);
        BAntsKilled++;
        break;
    case 6:
        myBeginSong(SRand1(5) + SONG_DEATH_VARIATION_BASE, 0x7e);
        if (OptionStates[3])
            PictStrnDialog(PIC_DEATH_MOWER, STR_DEATH_MOWER, 1);
        BAntsKilled++;
        break;
    case 7:
        myBeginSong(SRand1(5) + SONG_DEATH_VARIATION_BASE, 0x7e);
        if (OptionStates[3])
            PictStrnDialog(PIC_DEATH_DROWNED, STR_DEATH_DROWNED, 1);
        BAntsKilled++;
        break;
    case 8:
        myBeginSong(SRand1(5) + SONG_DEATH_VARIATION_BASE, 0x7e);
        if (OptionStates[3])
            PictStrnDialog(PIC_DEATH_STARVED, STR_DEATH_STARVED, 1);
        BAntsExpired++;
        break;
    case 9:
        myBeginSong(SRand1(5) + SONG_DEATH_VARIATION_BASE, 0x7e);
        if (OptionStates[3])
            PictStrnDialog(PIC_DEATH_INSECTICIDE, STR_DEATH_INSECTICIDE, 1);
        BAntsKilled++;
        break;
    case 10:
        BAntsKilled++;
        AnimYellowFight(fd_50F6_048C, fd_50F6_047C, fd_50F6_048A, MeDir, MeType, 10);
        if (OptionStates[3])
            PictStrnDialog(PIC_DEATH_FIGHT_OR_ELECTROCUTION, STR_DEATH_ELECTROCUTED, 1);
        break;
    }
    if (cause >= 1 && cause <= 2)
        YellowDialog(PIC_YELLOW_DEATH_DIALOG, 0);
    UpdateEverything();
    if (MeMode == 0)
        ClearMyLife(fd_50F6_048C, fd_50F6_047C, fd_50F6_048A, MeType, MeDir);
    SetSimCursor(6);
    UnRecruit(1);
    if (MeDropAlarm)
        SetAlarmDropState(0, 1);
    found = 0;
    i = ListIndexB;
    while (i >= 0) {
        t = BlistT[i];
        if (t != 0 && t < 8) {
            LifeB[RebornX = BlistX[i]][RebornY = BlistY[i]] = BlistT[i] = 0;
            found = 1;
            fd_50F6_048C = 2;
            break;
        }
        i--;
    }
    if (!found) {
        i = ListIndexB;
        while (i >= 0) {
            t = BlistT[i];
            if (t != 0 && t > 7 && t < 0x68) {
                LifeB[RebornX = BlistX[i]][RebornY = BlistY[i]] =
                    (life = BlistT[i], BlistT[i] = 0);
                found = 2;
                fd_50F6_048C = found;
                break;
            }
            i--;
        }
    }
    if (!found) {
        i = ListIndexA;
        while (i >= 0) {
            t = AlistT[i];
            if (t != 0 && t > 7 && t < 0x68) {
                LifeA[RebornX = AlistX[i]][RebornY = AlistY[i]] =
                    (life = AlistT[i], AlistT[i] = 0);
                found = 2;
                fd_50F6_048C = 1;
                break;
            }
            i--;
        }
    }
    if (!found) {
        i = ListIndexR;
        while (i >= 0) {
            t = RlistT[i];
            if (t != 0 && t > 7 && t < 0x68) {
                LifeR[RebornX = RlistX[i]][RebornY = RlistY[i]] =
                    (life = RlistT[i], RlistT[i] = 0);
                found = 2;
                fd_50F6_048C = 3;
                break;
            }
            i--;
        }
    }
    if (!found) {
        if (CurGameType <= 1) {
            IsGameOver = 1;
            BlackWon = 0;
            return;
        } else if (CurGameType == 2) {
            if (ColonyTotalBlack < 2) {
                IsGameOver = 1;
                BlackWon = 0;
                PictStrnDialog(PIC_NONE, STR_NO_BLACK_BREEDERS, 1);
            } else {
                PictStrnDialog(PIC_NONE, STR_SELECT_ANOTHER_COLONY, 1);
                SpecialXfer();
            }
            return;
        }
    }
    if (found == 1) {
        if (MeType == 0x60)
            MeType = 0x10;
        YellowBirth(fd_50F6_048C, RebornX, RebornY, MeType, 0);
    } else {
        MeMode = 0;
        SetMyLife(fd_50F6_048C, RebornX, RebornY, life & 0xf8, MeDir,
                  (life & 0xf8) + MeDir);
        ResetYellowVars(fd_50F6_048C, RebornX, RebornY);
        SetMyHealth(100);
        f_015B_06A2();
        DoEditAndMapUpdateDraw();
        PictStrnDialog(PIC_NONE, STR_TRANSFERRED_TO_EXISTING_ANT, 1);
    }
}

extern int far CurYardPnt[2];
extern unsigned char far YMapPopB[12][16];
extern void far MapToYard(void);
extern void _fastcall win_ToTop(int win);
extern void far f_015B_0273(int mode);
extern int far ColonyUpdateFlag;
extern void far f_015B_053C(int plane);
extern void far * far * far WindPromptStrs;
extern void far EditMessage(void far *msg, long ticks, int mode);
extern int near gfx_screen_width_pixels;
extern int far yard_screen_origin[2];
extern int far YMapPnt[2];
extern void far XferPatch(void);

void far SpecialXfer(void)
{
    struct Event ev;
    int done;
    int x;
    int y;

    YMapPopB[CurYardPnt[0]][CurYardPnt[1]] = 0;
    if (!win_IsWinInFront(WIN_YARD)) {
        if (!win_IsWinOpen(WIN_YARD))
            MapToYard();
        else
            win_ToTop(WIN_YARD);
    }
    f_015B_0273(2);
    ColonyUpdateFlag = 1;
    f_015B_053C(0);
    EditMessage(WindPromptStrs[20], -2L, 1);
    done = 0;
    while (!done) {
        if (!win_GetEvent(&ev))
            continue;
        if (!win_IsWinInFront(WIN_YARD)) {
            if (!win_IsWinOpen(WIN_YARD))
                MapToYard();
            else
                win_ToTop(WIN_YARD);
        }
        y = ev.v - map_viewport_rect.top;
        x = ev.h - map_viewport_rect.left;
        if (gfx_screen_width_pixels == 0x140) {
            x = (x + 2) * 2;
            y = (y - 8) * 2;
        }
        y = (y - yard_screen_origin[1]) / 10;
        x = (x - yard_screen_origin[0] + y * 10) / 28;
        if (x >= 0 && y >= 0 && x <= 11 && y <= 15) {
            if (YMapPopB[x][y]) {
                myBeginSong(SONG_RETURN_TO_ANT, 0x7e);
                YMapPnt[0] = x;
                YMapPnt[1] = y;
                XferPatch();
                done = 1;
            } else {
                myBeginSound(SND_REJECT, 0, 0x7e);
                EditMessage(WindPromptStrs[19], 120L, 1);
            }
        } else {
            myBeginSound(SND_REJECT, 0, 0x7e);
            EditMessage(WindPromptStrs[10], 120L, 1);
        }
    }
    EditMessage(0L, -2L, 1);
}

extern void _fastcall win_LockWin(int win);
extern void _fastcall win_SetObjBitmap(int obj, int bitmap);
extern void far win_Open(int win);
extern void _fastcall win_GetObjRect(int obj, struct Rect far *rect);
extern int _fastcall win_DrawBitMap(int x, int y, int id);
extern struct Pt far LionTrapPnts[];
extern void _fastcall win_UnlockWin(int win);
extern void _fastcall win_Close(int win);

void far LionDialog(void)
{
    struct Rect rect;
    long t1;
    long t2;
    int x0;
    int y0;
    int frame;

    if (OptionStates[3] == 0)
        return;
    win_LockWin(WIN_ANIMATION_DIALOG);
    win_SetObjBitmap(OBJ_ANIMATION_DIALOG_PICTURE, PIC_ANT_LION_DIALOG_FRAME_BASE);
    win_Open(WIN_ANIMATION_DIALOG);
    win_GetObjRect(OBJ_ANIMATION_DIALOG_PICTURE, &rect);
    y0 = rect.top;
    x0 = rect.left;
    myBeginSound(SND_ANT_LION_DIALOG, 0, 0x7e);
    while (!mySoundIsDone())
        ;
    frame = 1;
    t1 = MacTickCount() + 300;
    t2 = MacTickCount() + 30;
    win_FlushEvents();
    while (!win_Events()) {
        if (MacTickCount() >= t1)
            break;
        if (!win_IsWinOpen(WIN_ANIMATION_DIALOG))
            break;
        if (MacTickCount() >= t2) {
            t2 = MacTickCount() + 30;
            if (gfx_screen_width_pixels == 0x140)
                win_DrawBitMap(x0, y0, PIC_ANT_LION_DIALOG_FRAME_BASE + frame);
            else
                win_DrawBitMap(LionTrapPnts[frame].x + x0, LionTrapPnts[frame].y + y0, PIC_ANT_LION_DIALOG_FRAME_BASE + frame);
            if (frame & 1)
                myBeginSound(SND_FIGHT, 0, 0x7e);
            frame++;
            if (frame > 3)
                frame = 2;
        }
    }
    win_FlushEvents();
    win_UnlockWin(WIN_ANIMATION_DIALOG);
    win_Close(WIN_ANIMATION_DIALOG);
}

extern void far win_PrintfAtObj(int obj, char far *fmt, ...);
extern struct Pt far YellowEatPnt;
extern int far kbd_poll_bios_key(void);
extern void far DialogWaitInit(int mode);
extern int far DialogAbortOrCont(void);

void far YellowDialog(int bitmap, int promptIndex)
{
    struct Rect rect;
    int x0;
    int y0;

    if (OptionStates[3] == 0)
        return;
    win_LockWin(WIN_ANIMATION_DIALOG);
    win_SetObjBitmap(OBJ_ANIMATION_DIALOG_PICTURE, bitmap);
    win_Open(WIN_ANIMATION_DIALOG);
    win_GetObjRect(OBJ_ANIMATION_DIALOG_PICTURE, &rect);
    y0 = rect.top;
    x0 = rect.left;
    switch (bitmap) {
    case PIC_YELLOW_DEATH_DIALOG:
    case PIC_YELLOW_BIRTH_DIALOG:
        win_PrintfAtObj(OBJ_ANIMATION_DIALOG_PROMPT, WindPromptStrs[promptIndex + 23]);
        myDelay(300L);
        break;
    case PIC_YELLOW_DIALOG_EATING:
        myBeginSound(SND_YELLOW_DIALOG_FIRST_EFFECT, 0, 0x7e);
        myDelay(45L);
        if (gfx_screen_width_pixels == 0x140) {
            YellowEatPnt.x = 0x28;
            YellowEatPnt.y = 0x23;
        }
        if (win_IsWinOpen(WIN_ANIMATION_DIALOG))
            win_DrawBitMap(YellowEatPnt.x + x0, y0 + YellowEatPnt.y, PIC_YELLOW_DIALOG_EATING_OVERLAY);
        myBeginSound(SND_SPIDER_DIALOG_EFFECT, 0, 0x7e);
        myDelay(45L);
        break;
    }
    if (!win_Events() && kbd_poll_bios_key()) {
        DialogWaitInit(3);
        while (!DialogAbortOrCont() && !win_Events())
            ;
    }
    win_FlushEvents();
    win_UnlockWin(WIN_ANIMATION_DIALOG);
    win_Close(WIN_ANIMATION_DIALOG);
}

extern signed char far Dx8[8];
extern signed char far Dy8[8];
extern int far GetDir(int x1, int y1, int x2, int y2);
extern void far MoveMyLife(int plane, int x, int y, int type, int dir);
extern void far EatMyFood(int kind);

void far DoTroph(int x, int y, int index)
{
    int newX;
    int newY;

    newX = Dx8[index] + x;
    newY = Dy8[index] + y;
    MoveMyLife(fd_50F6_048C, newX, newY, MeType, GetDir(newX, newY, x, y) - 1);
    DoEditUpdateDraw();
    EatMyFood(1);
}

extern int far ELayerMode;
extern void _fastcall win_SetObjSelectedState(int obj, int state);
extern int far EditRows;
extern int far EditColumns;
extern void far InvalEuMap(int left, int top, int right, int bottom);

void far SetAlarmDropState(int state, int quiet)
{
    if (state) {
        if (fd_50F6_048C == 1 && MeMode == 0) {
            ELayerMode = 0;
            win_SetObjSelectedState(0x10, state);
            MeDropAlarm = 1;
            if (quiet == 0)
                myBeginSound(SND_COMMAND_ACK, 0, 0x7e);
        } else if (quiet == 0)
            myBeginSound(SND_REJECT, 0, 0x7e);
    } else {
        MeDropAlarm = 0;
        win_SetObjSelectedState(0x10, state);
        ELayerMode = -1;
        if (quiet == 0)
            myBeginSound(SND_COMMAND_ACK, 0, 0x7e);
    }
    InvalEuMap(0, 0, EditColumns, EditRows);
}

void far YellowCommand(int cmd);

int far YellowCommandKey(int key)
{
    int handled;

    handled = 1;
    switch (key) {
    case 0x30:
        YellowCommand(7);
        break;
    case 0x31:
        if (MeMode == 0) {
            if (MeType == 0x40 && MeNestStarted == 0)
                YellowCommand(8);
            else
                YellowCommand(1);
        } else
            YellowCommand(10);
        break;
    case 0x32:
        if (MeMode == 0) {
            if (MeType == 0x40 && MeNestStarted == 0)
                YellowCommand(9);
            else
                YellowCommand(2);
        } else
            YellowCommand(11);
        break;
    case 0x33:
        YellowCommand(4);
        break;
    case 0x34:
        YellowCommand(5);
        break;
    case 0x58:
    case 0x78:
        YellowCommand(6);
        break;
    case 0x88:
        if (*(unsigned char far *)BIOS_KEYBOARD_FLAGS_FARPTR & 3) {
            f_015B_06A2();
            break;
        }
        if (MeMode == 0) {
            if (MeMoveMe)
                ResetYellowVars(fd_50F6_048C, fd_50F6_047C, fd_50F6_048A);
            else
                f_015B_0653();
        } else if (MeMode == 1) {
            if (SuserX != fd_50F6_047C || SuserY != fd_50F6_048A) {
                SuserX = fd_50F6_047C;
                SuserY = fd_50F6_048A;
                SMode = 0;
            } else
                f_015B_0653();
        }
        break;
    case 0x824:
        if (MeMode == 1)
            YellowCommand(12);
        break;
    case KEY_EXT_HOME:
        myBeginSound(SND_COMMAND_ACK, 0, 0x7e);
        f_015B_06A2();
        break;
    default:
        handled = 0;
        break;
    }
    return handled;
}

void far YellowHelp(void);
extern void far Recruit(int count);
extern void far StartLifeTransfer(void);
extern int far TryMyDropOrLift(int plane, int x, int y);
extern void far TargetAnt(void);

void far YellowCommand(int cmd)
{
    if (MeMode > 1)
        return;
    switch (cmd) {
    case 0:
        YellowHelp();
        break;
    case 1:
        myBeginSong(SONG_RECRUIT_FIVE, 0x7e);
        Recruit(5);
        break;
    case 2:
        myBeginSong(SONG_RECRUIT_TEN, 0x7e);
        Recruit(10);
        break;
    case 3:
        myBeginSong(SONG_RECRUIT_THOUSAND, 0x7e);
        Recruit(1000);
        break;
    case 4:
        myBeginSong(SONG_RELEASE_RECRUITS, 0x7e);
        UnRecruit(0);
        break;
    case 5:
        myBeginSong(SONG_RELEASE_ALL_RECRUITS, 0x7e);
        UnRecruit(1);
        break;
    case 6:
        StartLifeTransfer();
        break;
    case 7:
        SetAlarmDropState(!MeDropAlarm, 0);
        break;
    case 8:
        if (fd_50F6_048C != 1 || TryMyDropOrLift(fd_50F6_048C, fd_50F6_047C, fd_50F6_048A) == -1)
            myBeginSound(SND_REJECT, 0, 0x7e);
        break;
    case 9:
        if (fd_50F6_048C == 2 && fd_50F6_048A >= 3) {
            SetSimCursor(6);
            YellowBirth(fd_50F6_048C, fd_50F6_047C + Dx8[MeDir ^ 4] * 2,
                        fd_50F6_048A + Dy8[MeDir ^ 4] * 2, 0x10, 1);
        } else
            myBeginSound(SND_REJECT, 0, 0x7e);
        break;
    case 10:
        TargetAnt();
        break;
    case 11:
        if (MeSMode == 7) {
            MeSMode = 0;
            myBeginSound(SND_ACCEPT, 0x56ee, 0x7e);
        } else {
            MeSMode = 7;
            myBeginSound(SND_ACCEPT, 0x2b77, 0x7e);
        }
        break;
    case 12:
        if (MeSMode == 8) {
            MeSMode = 0;
            myBeginSound(SND_ACCEPT, 0x56ee, 0x7e);
        } else {
            MeSMode = 8;
            myBeginSound(SND_RAIN, 0, 0x7e);
        }
        break;
    }
}

void far YellowHelp(void)
{
    struct Event ev;
    int bitmap;

    if (MeMode == 0) {
        if (MeType == 0x40)
            bitmap = PIC_YELLOW_QUEEN_HELP;
        else
            bitmap = PIC_YELLOW_ANT_HELP;
    } else
        bitmap = PIC_SPIDER_HELP;
    win_LockWin(WIN_ANIMATION_DIALOG);
    win_SetObjBitmap(OBJ_ANIMATION_DIALOG_PICTURE, bitmap);
    win_Open(WIN_ANIMATION_DIALOG);
    DialogWaitInit(0x1e);
    while (win_IsWinOpen(OBJ_ANIMATION_DIALOG_PICTURE) && !DialogAbortOrCont()) {
        if (win_GetEvent(&ev) && (ev.code >> 8) == 0x1a)
            break;
    }
    win_UnlockWin(WIN_ANIMATION_DIALOG);
    win_Close(WIN_ANIMATION_DIALOG);
}

