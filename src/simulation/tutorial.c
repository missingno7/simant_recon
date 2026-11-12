/*
 * Runs tutorial lessons and advice feedback. It selects the next lesson and delivers the
 * corresponding instructions.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS: resident code; segment 0E2E; partial original translation unit.
 * Windows: SIMTWO, from recorded function pairs in the Windows symbol inventory.
 */

typedef struct {
    int x;
    int y;
} Point;

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
        PictStrnDialog(0, 0x2af8, 1);
        break;
    case 2:
        PictStrnDialog(0x4268, 0x2afa, 1);
        break;
    case 3:
        PictStrnDialog(0, 0x2afc, 1);
        TimeTemp = TilesDugB + 2;
        break;
    case 4:
        PictStrnDialog(0, 0x2afe, 1);
        TimeTemp = TilesDugB + 10;
        break;
    case 5:
        PictStrnDialog(0x4269, 0x2b00, 1);
        break;
    case 6:
        PictStrnDialog(0, 0x2b02, 1);
        break;
    case 7:
        PictStrnDialog(0, 0x2b04, 1);
        LessonTemp = MeLocY + MeLocX;
        TimeTemp = MacTickCount() + 0x258L;
        break;
    case 8:
        PictStrnDialog(0, 0x2b06, 1);
        LessonTemp = 0;
        break;
    case 9:
        PictStrnDialog(0, 0x2b08, 1);
        LessonTemp = MapPnt.y + MapPnt.x;
        TimeTemp = MacTickCount() + 0x258L;
        break;
    case 10:
        PictStrnDialog(0, 0x2b0a, 1);
        break;
    case 11:
        PictStrnDialog(0x4276, 0x2b0c, 1);
        break;
    case 12:
        PictStrnDialog(0, 0x2b0e, 1);
        break;
    case 13:
        PictStrnDialog(0x426a, 0x2b10, 1);
        break;
    case 14:
        PictStrnDialog(0x426a, 0x2b12, 1);
        SetMyHealth(8);
        break;
    case 15:
        PictStrnDialog(0, 0x2b14, 1);
        break;
    case 16:
        PictStrnDialog(0, 0x2b16, 1);
        break;
    case 17:
        PictStrnDialog(0x4275, 0x2b18, 1);
        break;
    case 18:
        PictStrnDialog(0x426b, 0x2b1a, 1);
        break;
    case 19:
        PictStrnDialog(0, 0x2b1c, 1);
        break;
    case 20:
        PictStrnDialog(0, 0x2b1e, 1);
        break;
    case 21:
        PictStrnDialog(0x426c, 0x2b20, 1);
        break;
    case 22:
        PictStrnDialog(0, 0x2b22, 1);
        break;
    case 23:
        AddBlackAnts(10);
        PictStrnDialog(0, 0x2b24, 1);
        break;
    case 24:
        PictStrnDialog(0, 0x2b26, 1);
        break;
    case 25:
        PictStrnDialog(0, 0x2b28, 1);
        break;
    case 26:
        PictStrnDialog(0, 0x2b2a, 1);
        LessonTemp = MeLocY + MeLocX;
        TimeTemp = MacTickCount() + 0x258L;
        break;
    case 27:
        PictStrnDialog(0, 0x2b2c, 1);
        LessonTemp = MeLocY + MeLocX;
        break;
    case 28:
        PictStrnDialog(0, 0x2b2e, 1);
        break;
    case 29:
        PictStrnDialog(0, 0x2b30, 1);
        break;
    case 30:
        PictStrnDialog(0, 0x2b32, 1);
        LessonTemp = 0;
        break;
    case 31:
        PictStrnDialog(0, 0x2b34, 1);
        break;
    case 32:
        PictStrnDialog(0, 0x2b36, 1);
        break;
    case 33:
        PictStrnDialog(0x426d, 0x2b38, 1);
        break;
    case 34:
        PictStrnDialog(0, 0x2b3a, 1);
        break;
    case 35:
        PictStrnDialog(0, 0x2b3c, 1);
        break;
    case 36:
        PictStrnDialog(0x426e, 0x2b3e, 1);
        break;
    case 37:
        PictStrnDialog(0, 0x2b40, 1);
        break;
    case 38:
        PictStrnDialog(0x426f, 0x2b42, 1);
        break;
    case 39:
        PictStrnDialog(0x4270, 0x2b44, 1);
        break;
    case 40:
        PictStrnDialog(0x4270, 0x2b46, 1);
        break;
    case 41:
        PictStrnDialog(0x4270, 0x2b48, 1);
        LessonTemp = modeLevels[1] + modeLevels[0];
        break;
    case 42:
        PictStrnDialog(0, 0x2b4a, 1);
        break;
    case 43:
        PictStrnDialog(0x4271, 0x2b4c, 1);
        LessonTemp = 0;
        break;
    case 44:
        PictStrnDialog(0x4271, 0x2b4e, 1);
        break;
    case 45:
        PictStrnDialog(0x4272, 0x2b50, 1);
        break;
    case 46:
        PictStrnDialog(0x4272, 0x2b52, 1);
        LessonTemp = 0;
        break;
    case 47:
        PictStrnDialog(0x4273, 0x2b54, 1);
        break;
    case 48:
        PictStrnDialog(0x4273, 0x2b56, 1);
        break;
    case 49:
        PictStrnDialog(0, 0x2b58, 1);
        AddBlackAnts(0x50);
        for (row = 0; row < 64; row++)
            for (col = 0; col < 32; col++)
                PherMapA[row][col] = 0;
        break;
    case 50:
        PictStrnDialog(0x4274, 0x2b5a, 1);
        LessonTemp = 0;
        break;
    case 51:
        PictStrnDialog(0, 0x2b5c, 1);
        break;
    case 52:
        PictStrnDialog(0, 0x2b5e, 1);
        break;
    case 53:
        PictStrnDialog(0, 0x2b60, 1);
        break;
    case 54:
        PictStrnDialog(0, 0x2b62, 1);
        break;
    case 55:
        if (LessonTemp == 0)
            PictStrnDialog(0, 0x2b64, 1);
        else
            PictStrnDialog(0, 0x2b66, 1);
        break;
    case 56:
        PictStrnDialog(0, 0x2b68, 1);
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
    case 10: if (win_IsWinInFront(0x100) != 0)
            return 1;
        break;
    case 11: return 1;
    case 12: if (win_IsWinInFront(0) != 0)
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
    case 32: if (win_IsWinInFront(0x100) != 0)
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
    case 39: if (win_IsWinInFront(0x1200) != 0)
            return 1;
        break;
    case 40: return 1;
    case 41: if (modeLevels[1] + modeLevels[0] != LessonTemp)
            return 1;
        break;
    case 42: if (win_IsWinInFront(0x100) != 0)
            return 1;
        break;
    case 44: return 1;
    case 45: return 1;
    case 47: if (win_IsWinInFront(0x1300) != 0)
            return 1;
        break;
    case 48: return 1;
    case 49: if (win_IsWinInFront(0) != 0)
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

