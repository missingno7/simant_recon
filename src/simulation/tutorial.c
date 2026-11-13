/*
 * Runs tutorial lessons and advice feedback. It selects the next lesson and delivers the
 * corresponding instructions.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS: resident code; segment 0E2E; complete original translation unit.
 * Windows: SIMTWO, from recorded function pairs in the Windows symbol inventory.
 */

#include "pictures_ids.h"
#include "strings_ids.h"
#include "windows_ids.h"

#include "point.h"
typedef struct Point Point;

/* These prototypes appear here and again before the functions that use them.  Both copies
 * are kept: removing either one changes the code of RunTutor and LessonDone (declaration
 * numbers, docs/codegen-rules.md).  A header with the prototypes plus local ones would give
 * this shape; the original file structure is unknown. */
void far Feedback(void);
void far RunTutor(void);
void far GiveLesson(int lesson);
int far LessonDone(int lesson);

extern int far CurGameType;
void far RunTutor(void);
extern int far fd_3D57_07B0;
extern int far MeMode;
extern int far MeHealth;
extern int far MeWarnHealth;
extern void far * far * far AdviceStrs;
extern void far EditMessage(void far *, long, int);
extern int far BlkWarnHealth;
extern int far HealthB;
extern int far TilesDugB;
extern int far BpopT;
extern int far MeNestStarted;
extern void far SetDefaultWindPrompt(int);

void far Feedback(void)
{
    if (CurGameType == 0)
        RunTutor();
    if (fd_3D57_07B0 == 0)
        return;
    if (MeMode == 0 && (MeWarnHealth > MeHealth || MeHealth < 10)) {
        if (MeHealth < 10)
            EditMessage(AdviceStrs[0], 120L, 1);
        else
            EditMessage(AdviceStrs[1], 120L, 0);
    } else if (HealthB < BlkWarnHealth) {
        EditMessage(AdviceStrs[2], 120L, 0);
    } else if (BpopT > TilesDugB) {
        if (MeMode == 0 && MeNestStarted == 0 && TilesDugB == 0)
            EditMessage(AdviceStrs[3], 120L, 0);
        else
            EditMessage(AdviceStrs[4], 120L, 0);
    } else {
        SetDefaultWindPrompt(0);
    }
}

extern int far TutorCnt;
extern int far TutHowLong;
extern int far TutGiven;
extern int far TutLesson;
void far GiveLesson(int lesson);
int far LessonDone(int lesson);
extern long far MacTickCount(void);
extern long far TimeTemp;

void far RunTutor(void)
{
    if (++TutorCnt > 0x400)
        TutorCnt = 0;
    if (TutorCnt & 7)
        return;
    TutHowLong++;
    if (TutGiven == 0) {
        GiveLesson(TutLesson);
        TutGiven = 1;
        TutHowLong = 0;
    } else if (LessonDone(TutLesson)) {
        TutLesson++;
        TutGiven = 0;
    } else if (TutHowLong > 15 && MacTickCount() > TimeTemp) {
        TutGiven = 0;
    }
}

extern void far PictStrnDialog(int picture, int object, int force);
extern int far MeLocY;
extern int far MeLocX;
extern int far LessonTemp;
extern Point far MapPnt;
extern void far SetMyHealth(int);
extern void far AddBlackAnts(int count);
extern unsigned int far modeLevels[3];
extern unsigned char far PherMapA[64][32];

void far GiveLesson(int lesson)
{
    int row, col;

    switch (lesson) {
    case 1:
        PictStrnDialog(PIC_NONE, STR_TUTORIAL_WELCOME, 1);
        break;
    case 2:
        PictStrnDialog(PIC_TUTORIAL_YELLOW_ANT, STR_TUTORIAL_YOU_ARE_YELLOW_ANT, 1);
        break;
    case 3:
        PictStrnDialog(PIC_NONE, STR_TUTORIAL_TRY_DIGGING, 1);
        TimeTemp = TilesDugB + 2;
        break;
    case 4:
        PictStrnDialog(PIC_NONE, STR_TUTORIAL_LEARNED_DIGGING, 1);
        TimeTemp = TilesDugB + 10;
        break;
    case 5:
        PictStrnDialog(PIC_TUTORIAL_GO_OUTSIDE, STR_TUTORIAL_GO_OUTSIDE, 1);
        break;
    case 6:
        PictStrnDialog(PIC_NONE, STR_TUTORIAL_SURFACE_VIEW, 1);
        break;
    case 7:
        PictStrnDialog(PIC_NONE, STR_TUTORIAL_MOVE_ON_SURFACE, 1);
        LessonTemp = MeLocY + MeLocX;
        TimeTemp = MacTickCount() + 0x258L;
        break;
    case 8:
        PictStrnDialog(PIC_NONE, STR_TUTORIAL_RECENTER_ON_ANT, 1);
        LessonTemp = 0;
        break;
    case 9:
        PictStrnDialog(PIC_NONE, STR_TUTORIAL_SCROLL_SCREEN, 1);
        LessonTemp = MapPnt.y + MapPnt.x;
        TimeTemp = MacTickCount() + 0x258L;
        break;
    case 10:
        PictStrnDialog(PIC_NONE, STR_TUTORIAL_OPEN_MAP, 1);
        break;
    case 11:
        PictStrnDialog(PIC_TUTORIAL_MAP_OVERVIEW, STR_TUTORIAL_MAP_OVERVIEW, 1);
        break;
    case 12:
        PictStrnDialog(PIC_NONE, STR_TUTORIAL_RETURN_TO_EDIT, 1);
        break;
    case 13:
        PictStrnDialog(PIC_TUTORIAL_FOOD, STR_TUTORIAL_REACH_FOOD, 1);
        break;
    case 14:
        PictStrnDialog(PIC_TUTORIAL_FOOD, STR_TUTORIAL_EAT_FOOD, 1);
        SetMyHealth(8);
        break;
    case 15:
        PictStrnDialog(PIC_NONE, STR_TUTORIAL_HEALTH_RESTORED, 1);
        break;
    case 16:
        PictStrnDialog(PIC_NONE, STR_TUTORIAL_PICK_UP_FOOD, 1);
        break;
    case 17:
        PictStrnDialog(PIC_TUTORIAL_HEALTH_SETPOINT, STR_TUTORIAL_FOOD_HEALTH_SETPOINT, 1);
        break;
    case 18:
        PictStrnDialog(PIC_TUTORIAL_RETURN_TO_NEST, STR_TUTORIAL_RETURN_TO_NEST, 1);
        break;
    case 19:
        PictStrnDialog(PIC_NONE, STR_TUTORIAL_DROP_FOOD, 1);
        break;
    case 20:
        PictStrnDialog(PIC_NONE, STR_TUTORIAL_RETURN_TO_SURFACE, 1);
        break;
    case 21:
        PictStrnDialog(PIC_TUTORIAL_PICK_UP_ROCK, STR_TUTORIAL_PICK_UP_ROCK, 1);
        break;
    case 22:
        PictStrnDialog(PIC_NONE, STR_TUTORIAL_DROP_ROCK, 1);
        break;
    case 23:
        AddBlackAnts(10);
        PictStrnDialog(PIC_NONE, STR_TUTORIAL_PEBBLE_WALLS, 1);
        break;
    case 24:
        PictStrnDialog(PIC_NONE, STR_TUTORIAL_RECRUIT_TEN, 1);
        break;
    case 25:
        PictStrnDialog(PIC_NONE, STR_TUTORIAL_RECRUITED_ANTS, 1);
        break;
    case 26:
        PictStrnDialog(PIC_NONE, STR_TUTORIAL_FOLLOWERS, 1);
        LessonTemp = MeLocY + MeLocX;
        TimeTemp = MacTickCount() + 0x258L;
        break;
    case 27:
        PictStrnDialog(PIC_NONE, STR_TUTORIAL_MOVE_WITH_ALARM, 1);
        LessonTemp = MeLocY + MeLocX;
        break;
    case 28:
        PictStrnDialog(PIC_NONE, STR_TUTORIAL_ALARM_SCENT, 1);
        break;
    case 29:
        PictStrnDialog(PIC_NONE, STR_TUTORIAL_EXCHANGE_INTRO, 1);
        break;
    case 30:
        PictStrnDialog(PIC_NONE, STR_TUTORIAL_SELECT_EXCHANGE, 1);
        LessonTemp = 0;
        break;
    case 31:
        PictStrnDialog(PIC_NONE, STR_TUTORIAL_NOW_CONTROL_OTHER_ANT, 1);
        break;
    case 32:
        PictStrnDialog(PIC_NONE, STR_TUTORIAL_RETURN_TO_MAP, 1);
        break;
    case 33:
        PictStrnDialog(PIC_TUTORIAL_OPEN_YARD, STR_TUTORIAL_OPEN_YARD, 1);
        break;
    case 34:
        PictStrnDialog(PIC_NONE, STR_TUTORIAL_CURRENT_PATCH, 1);
        break;
    case 35:
        PictStrnDialog(PIC_NONE, STR_TUTORIAL_YARD_REPRODUCTION, 1);
        break;
    case 36:
        PictStrnDialog(PIC_TUTORIAL_OPEN_HOUSE, STR_TUTORIAL_OPEN_HOUSE, 1);
        break;
    case 37:
        PictStrnDialog(PIC_NONE, STR_TUTORIAL_HOUSE_OBJECTIVE, 1);
        break;
    case 38:
        PictStrnDialog(PIC_TUTORIAL_RETURN_TO_PATCH, STR_TUTORIAL_RETURN_TO_PATCH, 1);
        break;
    case 39:
        PictStrnDialog(PIC_TUTORIAL_BEHAVIOR, STR_TUTORIAL_OPEN_BEHAVIOR, 1);
        break;
    case 40:
        PictStrnDialog(PIC_TUTORIAL_BEHAVIOR, STR_TUTORIAL_BEHAVIOR_WINDOW, 1);
        break;
    case 41:
        PictStrnDialog(PIC_TUTORIAL_BEHAVIOR, STR_TUTORIAL_DRAG_BEHAVIOR_KNOB, 1);
        LessonTemp = modeLevels[1] + modeLevels[0];
        break;
    case 42:
        PictStrnDialog(PIC_NONE, STR_TUTORIAL_RETURN_TO_MAP_AGAIN, 1);
        break;
    case 43:
        PictStrnDialog(PIC_TUTORIAL_HELP, STR_TUTORIAL_OPEN_HELP, 1);
        LessonTemp = 0;
        break;
    case 44:
        PictStrnDialog(PIC_TUTORIAL_HELP, STR_TUTORIAL_HELP_BUTTONS, 1);
        break;
    case 45:
        PictStrnDialog(PIC_TUTORIAL_COLONY_BARS, STR_TUTORIAL_COLONY_BARS, 1);
        break;
    case 46:
        PictStrnDialog(PIC_TUTORIAL_COLONY_BARS, STR_TUTORIAL_POPULATION_BREAKDOWN, 1);
        LessonTemp = 0;
        break;
    case 47:
        PictStrnDialog(PIC_TUTORIAL_CASTE, STR_TUTORIAL_OPEN_CASTE, 1);
        break;
    case 48:
        PictStrnDialog(PIC_TUTORIAL_CASTE, STR_TUTORIAL_CASTE_WINDOW, 1);
        break;
    case 49:
        PictStrnDialog(PIC_NONE, STR_TUTORIAL_RETURN_TO_EDIT_AGAIN, 1);
        AddBlackAnts(0x50);
        for (row = 0; row < 64; row++)
            for (col = 0; col < 32; col++)
                PherMapA[row][col] = 0;
        break;
    case 50:
        PictStrnDialog(PIC_TUTORIAL_CENTER_ON_ANT, STR_TUTORIAL_CENTER_ON_YELLOW_ANT, 1);
        LessonTemp = 0;
        break;
    case 51:
        PictStrnDialog(PIC_NONE, STR_TUTORIAL_ATTACK_RED_COLONY, 1);
        break;
    case 52:
        PictStrnDialog(PIC_NONE, STR_TUTORIAL_RECRUIT_FIFTY, 1);
        break;
    case 53:
        PictStrnDialog(PIC_NONE, STR_TUTORIAL_READY_TO_ATTACK, 1);
        break;
    case 54:
        PictStrnDialog(PIC_NONE, STR_TUTORIAL_FIND_RED_NEST, 1);
        break;
    case 55:
        if (LessonTemp == 0)
            PictStrnDialog(PIC_NONE, STR_TUTORIAL_ENTERED_RED_NEST, 1);
        else
            PictStrnDialog(PIC_NONE, STR_TUTORIAL_ATTACK_FAILED, 1);
        break;
    case 56:
        PictStrnDialog(PIC_NONE, STR_TUTORIAL_END, 1);
        break;
    }
}

extern int far MeMoveMe;
extern int far MePlane;
extern int far MeDis;
extern unsigned char far MapA[128][64];
extern int _fastcall win_IsWinInFront(int);
extern int far MeType;
extern int far ModePopB[6];
extern int far MeDropAlarm;
extern void far SetAlarmDropState(int state, int quiet);
extern int far MapPlane;
extern int far YardMode;


/* Tests the condition for the selected tutorial step; case 30 also clears the drop alarm.
 * MSC 6.00AX is sensitive to the newline after a case label: keep each first statement
 * on its label's line. This reproduces duplicate-body selection, not original formatting.
 * The marker test returns both outcomes here; other conditional cases share the final zero.
 */
int far LessonDone(int lesson)
{
    switch (lesson) {
    case 1: return 1;
    case 2: return 1;
    case 3: if (TilesDugB > TimeTemp && MeMoveMe == 0)
            return 1;
        break;
    case 4: if (TilesDugB > TimeTemp && MeMoveMe == 0)
            return 1;
        break;
    case 5: if (MePlane == 1)
            return 1;
        break;
    case 6: return 1;
    case 7: if (MeLocY + MeLocX != LessonTemp && MeDis == 0 && MacTickCount() > TimeTemp)
            return 1;
        break;
    case 9: if (MapPnt.y + MapPnt.x != LessonTemp || MacTickCount() > TimeTemp)
            return 1;
        break;
    case 10: if (win_IsWinInFront(WIN_MAP) != 0)
            return 1;
        break;
    case 11: return 1;
    case 12: if (win_IsWinInFront(WIN_EDIT) != 0)
            return 1;
        break;
    case 13: if (MePlane == 1 && MapA[MeLocX][MeLocY] > 0x47)
            return 1;
        break;
    case 14: if (MeHealth > 0x5a)
            return 1;
        break;
    case 15: return 1;
    case 16: if (MeType == 0x18)
            return 1;
        break;
    case 17: return 1;
    case 18: if (MePlane == 2)
            return 1;
        break;
    case 19: if (MeType == 0x10)
            return 1;
        break;
    case 20: if (MePlane == 1)
            return 1;
        break;
    case 21: if (MeType == 0x28)
            return 1;
        break;
    case 22: if (MeType == 0x10)
            return 1;
        break;
    case 23: return 1;
    case 24: if (ModePopB[5] > 1)
            return 1;
        break;
    case 25: return 1;
    case 26: if (MeLocY + MeLocX != LessonTemp && MeDis == 0 && MacTickCount() > TimeTemp)
            return 1;
        break;
    case 27: if (MeLocY + MeLocX != LessonTemp && MeDropAlarm != 0 && MeDis == 0)
            return 1;
        break;
    case 28: return 1;
    case 29: return 1;
    case 30: if (MeDropAlarm != 0)
            SetAlarmDropState(0, 1);
    case 8: case 43: case 46: case 50: if (LessonTemp != 0)
            return 1;
        return 0;
    case 31: return 1;
    case 32: if (win_IsWinInFront(WIN_MAP) != 0)
            return 1;
        break;
    case 33: if (MapPlane == 0)
            return 1;
        break;
    case 34: return 1;
    case 35: return 1;
    case 36: if (YardMode == 1)
            return 1;
        break;
    case 37: return 1;
    case 38: if (MapPlane == 1)
            return 1;
        break;
    case 39: if (win_IsWinInFront(WIN_BEHAVIOR) != 0)
            return 1;
        break;
    case 40: return 1;
    case 41: if (modeLevels[1] + modeLevels[0] != LessonTemp)
            return 1;
        break;
    case 42: if (win_IsWinInFront(WIN_MAP) != 0)
            return 1;
        break;
    case 44: return 1;
    case 45: return 1;
    case 47: if (win_IsWinInFront(WIN_CASTE) != 0)
            return 1;
        break;
    case 48: return 1;
    case 49: if (win_IsWinInFront(WIN_EDIT) != 0)
            return 1;
        break;
    case 51: return 1;
    case 52: if (ModePopB[5] > 0x28)
            return 1;
        break;
    case 53: return 1;
    case 54: if (MePlane == 3) {
            LessonTemp = 0;
            return 1;
        }
        if (MePlane == 2) {
            LessonTemp = 1;
            return 1;
        }
        break;
    case 55: return 1;
    case 56: return 1;
    }
    return 0;
}

