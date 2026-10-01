/* Root module, code frame 0E2E: tutorial lessons and advice feedback
 * (Win16 unit Feedback, RunTutor, GiveLesson, LessonDone). */

typedef struct {
    int x;
    int y;
} Point;

void far Feedback(void);
void far RunTutor(void);
void far GiveLesson(int lesson);
int far LessonDone(int lesson);

extern int far fd_50F6_0EAC;
void far RunTutor(void);
extern int far fd_3D57_07B0;
extern int far fd_50F6_0A06;
extern int far MeHealth;
extern int far fd_50F6_0FBA;
extern void far * far * far AdviceStrs;
extern void far f_15D9_009C(void far *, long, int);
extern int far fd_50F6_0FFE;
extern int far HealthB;
extern int far fd_50F6_0224;
extern int far fd_50F6_0330;
extern int far fd_3D57_0C24;
extern void far SetDefaultWindPrompt(int);

void far Feedback(void)
{
    if (fd_50F6_0EAC == 0)
        RunTutor();
    if (fd_3D57_07B0 == 0)
        return;
    if (fd_50F6_0A06 == 0 && (fd_50F6_0FBA > MeHealth || MeHealth < 10)) {
        if (MeHealth < 10)
            f_15D9_009C(AdviceStrs[0], 120L, 1);
        else
            f_15D9_009C(AdviceStrs[1], 120L, 0);
    } else if (HealthB < fd_50F6_0FFE) {
        f_15D9_009C(AdviceStrs[2], 120L, 0);
    } else if (fd_50F6_0330 > fd_50F6_0224) {
        if (fd_50F6_0A06 == 0 && fd_3D57_0C24 == 0 && fd_50F6_0224 == 0)
            f_15D9_009C(AdviceStrs[3], 120L, 0);
        else
            f_15D9_009C(AdviceStrs[4], 120L, 0);
    } else {
        SetDefaultWindPrompt(0);
    }
}

extern int far fd_3D57_07A2;
extern int far fd_50F6_10B8;
extern int far fd_3D57_07A6;
extern int far fd_3D57_07A4;
void far GiveLesson(int lesson);
int far LessonDone(int lesson);
extern long far f_00F8_02BE(void);
extern long far fd_50F6_0204;

void far RunTutor(void)
{
    if (++fd_3D57_07A2 > 0x400)
        fd_3D57_07A2 = 0;
    if (fd_3D57_07A2 & 7)
        return;
    fd_50F6_10B8++;
    if (fd_3D57_07A6 == 0) {
        GiveLesson(fd_3D57_07A4);
        fd_3D57_07A6 = 1;
        fd_50F6_10B8 = 0;
    } else if (LessonDone(fd_3D57_07A4)) {
        fd_3D57_07A4++;
        fd_3D57_07A6 = 0;
    } else if (fd_50F6_10B8 > 15 && f_00F8_02BE() > fd_50F6_0204) {
        fd_3D57_07A6 = 0;
    }
}

extern void far PictStrnDialog(int picture, int object, int force);
extern int far MeLocY;
extern int far MeLocX;
extern int far fd_50F6_1074;
extern Point far fd_50F6_0508;
extern void far SetMyHealth(int);
extern void far AddBlackAnts(int count);
extern int far modeLevels[3];
extern unsigned char far fd_3E1D_D09F[64][32];

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
        fd_50F6_0204 = fd_50F6_0224 + 2;
        break;
    case 4:
        PictStrnDialog(0, 0x2afe, 1);
        fd_50F6_0204 = fd_50F6_0224 + 10;
        break;
    case 5:
        PictStrnDialog(0x4269, 0x2b00, 1);
        break;
    case 6:
        PictStrnDialog(0, 0x2b02, 1);
        break;
    case 7:
        PictStrnDialog(0, 0x2b04, 1);
        fd_50F6_1074 = MeLocY + MeLocX;
        fd_50F6_0204 = f_00F8_02BE() + 0x258L;
        break;
    case 8:
        PictStrnDialog(0, 0x2b06, 1);
        fd_50F6_1074 = 0;
        break;
    case 9:
        PictStrnDialog(0, 0x2b08, 1);
        fd_50F6_1074 = fd_50F6_0508.y + fd_50F6_0508.x;
        fd_50F6_0204 = f_00F8_02BE() + 0x258L;
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
        fd_50F6_1074 = MeLocY + MeLocX;
        fd_50F6_0204 = f_00F8_02BE() + 0x258L;
        break;
    case 27:
        PictStrnDialog(0, 0x2b2c, 1);
        fd_50F6_1074 = MeLocY + MeLocX;
        break;
    case 28:
        PictStrnDialog(0, 0x2b2e, 1);
        break;
    case 29:
        PictStrnDialog(0, 0x2b30, 1);
        break;
    case 30:
        PictStrnDialog(0, 0x2b32, 1);
        fd_50F6_1074 = 0;
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
        fd_50F6_1074 = modeLevels[1] + modeLevels[0];
        break;
    case 42:
        PictStrnDialog(0, 0x2b4a, 1);
        break;
    case 43:
        PictStrnDialog(0x4271, 0x2b4c, 1);
        fd_50F6_1074 = 0;
        break;
    case 44:
        PictStrnDialog(0x4271, 0x2b4e, 1);
        break;
    case 45:
        PictStrnDialog(0x4272, 0x2b50, 1);
        break;
    case 46:
        PictStrnDialog(0x4272, 0x2b52, 1);
        fd_50F6_1074 = 0;
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
                fd_3E1D_D09F[row][col] = 0;
        break;
    case 50:
        PictStrnDialog(0x4274, 0x2b5a, 1);
        fd_50F6_1074 = 0;
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
        if (fd_50F6_1074 == 0)
            PictStrnDialog(0, 0x2b64, 1);
        else
            PictStrnDialog(0, 0x2b66, 1);
        break;
    default:
        return 0;
    case 56:
        PictStrnDialog(0, 0x2b68, 1);
        break;
    }
}

extern int far fd_50F6_0AA0;
extern int far MePlane;
extern int far fd_50F6_0B1E;
extern unsigned char far MapA[128][64];
extern int _fastcall f_22BF_0A22(int);
extern int far fd_50F6_04C2;
extern int far fd_50F6_0B12[6];
extern int far fd_50F6_104E;
extern void far SetAlarmDropState(int state, int quiet);
extern int far fd_50F6_032E;
extern int far fd_50F6_035C;

int far LessonDone(int lesson)
{
    switch (lesson) {
    case 1:
        return 1;
    case 2:
        return 1;
    case 3:
        if (fd_50F6_0224 > fd_50F6_0204 && fd_50F6_0AA0 == 0)
            return 1;
        break;
    case 4:
        if (fd_50F6_0224 > fd_50F6_0204 && fd_50F6_0AA0 == 0)
            return 1;
        break;
    case 5:
        if (MePlane == 1)
            return 1;
        break;
    case 6:
        return 1;
    case 7:
        if (MeLocY + MeLocX != fd_50F6_1074 && fd_50F6_0B1E == 0 && f_00F8_02BE() > fd_50F6_0204)
            return 1;
        break;
    case 8:
        if (fd_50F6_1074 != 0)
            return 1;
        break;
    case 9:
        if (fd_50F6_0508.y + fd_50F6_0508.x != fd_50F6_1074 || f_00F8_02BE() > fd_50F6_0204)
            return 1;
        break;
    case 10:
        if (f_22BF_0A22(0x100) != 0)
            return 1;
        break;
    case 11:
        return 1;
    case 12:
        if (f_22BF_0A22(0) != 0)
            return 1;
        break;
    case 13:
        if (MePlane == 1 && MapA[MeLocX][MeLocY] > 0x47)
            return 1;
        break;
    case 14:
        if (MeHealth > 0x5a)
            return 1;
        break;
    case 15:
        return 1;
    case 16:
        if (fd_50F6_04C2 == 0x18)
            return 1;
        break;
    case 17:
        return 1;
    case 18:
        if (MePlane == 2)
            return 1;
        break;
    case 19:
        if (fd_50F6_04C2 == 0x10)
            return 1;
        break;
    case 20:
        if (MePlane == 1)
            return 1;
        break;
    case 21:
        if (fd_50F6_04C2 == 0x28)
            return 1;
        break;
    case 22:
        if (fd_50F6_04C2 == 0x10)
            return 1;
        break;
    case 23:
        return 1;
    case 24:
        if (fd_50F6_0B12[5] > 1)
            return 1;
        break;
    case 25:
        return 1;
    case 26:
        if (MeLocY + MeLocX != fd_50F6_1074 && fd_50F6_0B1E == 0 && f_00F8_02BE() > fd_50F6_0204)
            return 1;
        break;
    case 27:
        if (MeLocY + MeLocX != fd_50F6_1074 && fd_50F6_104E != 0 && fd_50F6_0B1E == 0)
            return 1;
        break;
    case 28:
        return 1;
    case 29:
        return 1;
    case 30:
        if (fd_50F6_104E != 0)
            SetAlarmDropState(0, 1);
        if (fd_50F6_1074 != 0)
            return 1;
        break;
    case 31:
        return 1;
    case 32:
        if (f_22BF_0A22(0x100) != 0)
            return 1;
        break;
    case 33:
        if (fd_50F6_032E == 0)
            return 1;
        break;
    case 34:
        return 1;
    case 35:
        return 1;
    case 36:
        if (fd_50F6_035C == 1)
            return 1;
        break;
    case 37:
        return 1;
    case 38:
        if (fd_50F6_032E == 1)
            return 1;
        break;
    case 39:
        if (f_22BF_0A22(0x1200) != 0)
            return 1;
        break;
    case 40:
        return 1;
    case 41:
        if (modeLevels[1] + modeLevels[0] != fd_50F6_1074)
            return 1;
        break;
    case 42:
        if (f_22BF_0A22(0x100) != 0)
            return 1;
        break;
    case 43:
        if (fd_50F6_1074 != 0)
            return 1;
        break;
    case 44:
        return 1;
    case 45:
        return 1;
    case 46:
        if (fd_50F6_1074 != 0)
            return 1;
        break;
    case 47:
        if (f_22BF_0A22(0x1300) != 0)
            return 1;
        break;
    case 48:
        return 1;
    case 49:
        if (f_22BF_0A22(0) != 0)
            return 1;
        break;
    case 50:
        if (fd_50F6_1074 != 0)
            return 1;
        break;
    case 51:
        return 1;
    case 52:
        if (fd_50F6_0B12[5] > 0x28)
            return 1;
        break;
    case 53:
        return 1;
    case 54:
        if (MePlane == 3) {
            fd_50F6_1074 = 0;
            return 1;
        }
        if (MePlane == 2) {
            fd_50F6_1074 = 1;
            return 1;
        }
        return 0;
    case 55:
        return 1;
    case 56:
        return 1;
    }
    return 0;
}
