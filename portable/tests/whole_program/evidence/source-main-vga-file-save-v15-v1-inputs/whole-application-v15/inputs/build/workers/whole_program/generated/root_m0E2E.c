#include "dos_types.h"
#include "portable/whole_program/platform/dos_memory.h"
#include "portable/whole_program/platform/dos_io.h"
#include "portable/whole_program/platform/graphics_source_fields.h"
#include "simulation_state_50f6_v7.h"
#include "simulation_state_50f6.h"
#include "native_owners.h"
#pragma pack(push, 2)
/* Root module, code frame 0E2E: tutorial lessons and advice feedback
 * (Win16 unit Feedback, RunTutor, GiveLesson, LessonDone). */

typedef struct {
    int16_t x;
    int16_t y;
} Point;

void  Feedback(void);
void  RunTutor(void);
void  GiveLesson(int16_t lesson);
int16_t  LessonDone(int16_t lesson);

extern int16_t  fd_50F6_0EAC;
void  RunTutor(void);
extern int16_t  fd_3D57_07B0;
extern int16_t  fd_50F6_0A06;
extern void  *  *  AdviceStrs;
extern void  EditMessage(void  *, int32_t, int16_t);
extern int16_t  fd_3D57_0C24;
extern void  SetDefaultWindPrompt(int16_t);

void  Feedback(void)
{
    if (fd_50F6_0EAC == 0)
        RunTutor();
    if (fd_3D57_07B0 == 0)
        return;
    if (fd_50F6_0A06 == 0 && (native_state_fd_50F6_0FBA.signed_value > native_state_MeHealth.signed_value || native_state_MeHealth.signed_value < 10)) {
        if (native_state_MeHealth.signed_value < 10)
            EditMessage(AdviceStrs[0], 120L, 1);
        else
            EditMessage(AdviceStrs[1], 120L, 0);
    } else if (native_state_HealthB.signed_value < native_state_fd_50F6_0FFE.signed_value) {
        EditMessage(AdviceStrs[2], 120L, 0);
    } else if (native_state_BpopT.signed_value > native_state_fd_50F6_0224.signed_value) {
        if (fd_50F6_0A06 == 0 && fd_3D57_0C24 == 0 && native_state_fd_50F6_0224.signed_value == 0)
            EditMessage(AdviceStrs[3], 120L, 0);
        else
            EditMessage(AdviceStrs[4], 120L, 0);
    } else {
        SetDefaultWindPrompt(0);
    }
}

extern int16_t  fd_3D57_07A2;
extern int16_t  fd_3D57_07A6;
extern int16_t  fd_3D57_07A4;
void  GiveLesson(int16_t lesson);
int16_t  LessonDone(int16_t lesson);
extern int32_t  MacTickCount(void);
extern int32_t  fd_50F6_0204;

void  RunTutor(void)
{
    if (++fd_3D57_07A2 > 0x400)
        fd_3D57_07A2 = 0;
    if (fd_3D57_07A2 & 7)
        return;
    native_state_fd_50F6_10B8.signed_value++;
    if (fd_3D57_07A6 == 0) {
        GiveLesson(fd_3D57_07A4);
        fd_3D57_07A6 = 1;
        native_state_fd_50F6_10B8.signed_value = 0;
    } else if (LessonDone(fd_3D57_07A4)) {
        fd_3D57_07A4++;
        fd_3D57_07A6 = 0;
    } else if (native_state_fd_50F6_10B8.signed_value > 15 && MacTickCount() > fd_50F6_0204) {
        fd_3D57_07A6 = 0;
    }
}

extern void  PictStrnDialog(int16_t picture, int16_t object, int16_t force);
extern int16_t  MeLocY;
extern int16_t  MeLocX;
extern void  SetMyHealth(int16_t);
extern void  AddBlackAnts(int16_t count);
extern uint8_t  PherMapA[64][32];

void  GiveLesson(int16_t lesson)
{
    int16_t row, col;

    switch (lesson) {
    case 1:
        PictStrnDialog(0, 0x2af8, 1);
        break;
    case 2:
        PictStrnDialog(0x4268, 0x2afa, 1);
        break;
    case 3:
        PictStrnDialog(0, 0x2afc, 1);
        fd_50F6_0204 = native_state_fd_50F6_0224.signed_value + 2;
        break;
    case 4:
        PictStrnDialog(0, 0x2afe, 1);
        fd_50F6_0204 = native_state_fd_50F6_0224.signed_value + 10;
        break;
    case 5:
        PictStrnDialog(0x4269, 0x2b00, 1);
        break;
    case 6:
        PictStrnDialog(0, 0x2b02, 1);
        break;
    case 7:
        PictStrnDialog(0, 0x2b04, 1);
        native_state_fd_50F6_1074.signed_value = MeLocY + MeLocX;
        fd_50F6_0204 = MacTickCount() + 0x258L;
        break;
    case 8:
        PictStrnDialog(0, 0x2b06, 1);
        native_state_fd_50F6_1074.signed_value = 0;
        break;
    case 9:
        PictStrnDialog(0, 0x2b08, 1);
        native_state_fd_50F6_1074.signed_value = (*((Point *)native_sim_state_fd_50F6_0508.raw_bytes)).y + (*((Point *)native_sim_state_fd_50F6_0508.raw_bytes)).x;
        fd_50F6_0204 = MacTickCount() + 0x258L;
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
        native_state_fd_50F6_1074.signed_value = MeLocY + MeLocX;
        fd_50F6_0204 = MacTickCount() + 0x258L;
        break;
    case 27:
        PictStrnDialog(0, 0x2b2c, 1);
        native_state_fd_50F6_1074.signed_value = MeLocY + MeLocX;
        break;
    case 28:
        PictStrnDialog(0, 0x2b2e, 1);
        break;
    case 29:
        PictStrnDialog(0, 0x2b30, 1);
        break;
    case 30:
        PictStrnDialog(0, 0x2b32, 1);
        native_state_fd_50F6_1074.signed_value = 0;
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
        native_state_fd_50F6_1074.signed_value = native_sim_state_modeLevels.signed_values[1] + native_sim_state_modeLevels.signed_values[0];
        break;
    case 42:
        PictStrnDialog(0, 0x2b4a, 1);
        break;
    case 43:
        PictStrnDialog(0x4271, 0x2b4c, 1);
        native_state_fd_50F6_1074.signed_value = 0;
        break;
    case 44:
        PictStrnDialog(0x4271, 0x2b4e, 1);
        break;
    case 45:
        PictStrnDialog(0x4272, 0x2b50, 1);
        break;
    case 46:
        PictStrnDialog(0x4272, 0x2b52, 1);
        native_state_fd_50F6_1074.signed_value = 0;
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
        native_state_fd_50F6_1074.signed_value = 0;
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
        if (native_state_fd_50F6_1074.signed_value == 0)
            PictStrnDialog(0, 0x2b64, 1);
        else
            PictStrnDialog(0, 0x2b66, 1);
        break;
    case 56:
        PictStrnDialog(0, 0x2b68, 1);
        break;
    }
}

extern int16_t  MePlane;
extern uint8_t  MapA[128][64];
extern int16_t  win_IsWinInFront(int16_t);
extern int16_t  fd_50F6_04C2;
extern void  SetAlarmDropState(int16_t state, int16_t quiet);

/* SCAFFOLD BEGIN: LessonDone best draft (code shape differs: case-block placement of merged identical cases 5/20, 7/26, 19/22, 12/49) */
int16_t  LessonDone(int16_t lesson)
{
    switch (lesson) {
    case 1:
        return 1;
    case 2:
        return 1;
    case 3:
        if (native_state_fd_50F6_0224.signed_value > fd_50F6_0204 && native_state_fd_50F6_0AA0.signed_value == 0)
            return 1;
        break;
    case 4:
        if (native_state_fd_50F6_0224.signed_value > fd_50F6_0204 && native_state_fd_50F6_0AA0.signed_value == 0)
            return 1;
        break;
    case 5:
        return MePlane == 1;
    case 6:
        return 1;
    case 7:
        if (MeLocY + MeLocX != native_state_fd_50F6_1074.signed_value && native_state_fd_50F6_0B1E.signed_value == 0 && MacTickCount() > fd_50F6_0204)
            return 1;
        break;
    case 9:
        if ((*((Point *)native_sim_state_fd_50F6_0508.raw_bytes)).y + (*((Point *)native_sim_state_fd_50F6_0508.raw_bytes)).x != native_state_fd_50F6_1074.signed_value || MacTickCount() > fd_50F6_0204)
            return 1;
        break;
    case 10:
        return win_IsWinInFront(0x100) != 0;
    case 11:
        return 1;
    case 12:
        return win_IsWinInFront(0) != 0;
    case 13:
        if (MePlane == 1 && MapA[MeLocX][MeLocY] > 0x47)
            return 1;
        break;
    case 14:
        return native_state_MeHealth.signed_value > 0x5a;
    case 15:
        return 1;
    case 16:
        return fd_50F6_04C2 == 0x18;
    case 17:
        return 1;
    case 18:
        return MePlane == 2;
    case 19:
        return fd_50F6_04C2 == 0x10;
    case 20:
        return MePlane == 1;
    case 21:
        return fd_50F6_04C2 == 0x28;
    case 22:
        return fd_50F6_04C2 == 0x10;
    case 23:
        return 1;
    case 24:
        return native_sim_state_fd_50F6_0B12.signed_values[5] > 1;
    case 25:
        return 1;
    case 26:
        if (MeLocY + MeLocX != native_state_fd_50F6_1074.signed_value && native_state_fd_50F6_0B1E.signed_value == 0 && MacTickCount() > fd_50F6_0204)
            return 1;
        break;
    case 27:
        if (MeLocY + MeLocX != native_state_fd_50F6_1074.signed_value && native_state_fd_50F6_104E.signed_value != 0 && native_state_fd_50F6_0B1E.signed_value == 0)
            return 1;
        break;
    case 28:
        return 1;
    case 29:
        return 1;
    case 30:
        if (native_state_fd_50F6_104E.signed_value != 0)
            SetAlarmDropState(0, 1);
    case 8:
    case 43:
    case 46:
    case 50:
        return native_state_fd_50F6_1074.signed_value != 0;
    case 31:
        return 1;
    case 32:
        return win_IsWinInFront(0x100) != 0;
    case 33:
        return native_state_MapPlane.signed_value == 0;
    case 34:
        return 1;
    case 35:
        return 1;
    case 36:
        return native_state_YardMode.signed_value == 1;
    case 37:
        return 1;
    case 38:
        return native_state_MapPlane.signed_value == 1;
    case 39:
        return win_IsWinInFront(0x1200) != 0;
    case 40:
        return 1;
    case 41:
        return native_sim_state_modeLevels.signed_values[1] + native_sim_state_modeLevels.signed_values[0] != native_state_fd_50F6_1074.signed_value;
    case 42:
        return win_IsWinInFront(0x100) != 0;
    case 44:
        return 1;
    case 45:
        return 1;
    case 47:
        return win_IsWinInFront(0x1300) != 0;
    case 48:
        return 1;
    case 49:
        return win_IsWinInFront(0) != 0;
    case 51:
        return 1;
    case 52:
        return native_sim_state_fd_50F6_0B12.signed_values[5] > 0x28;
    case 53:
        return 1;
    case 54:
        if (MePlane == 3) {
            native_state_fd_50F6_1074.signed_value = 0;
            return 1;
        }
        if (MePlane == 2) {
            native_state_fd_50F6_1074.signed_value = 1;
            return 1;
        }
        break;
    case 55:
        return 1;
    case 56:
        return 1;
    }
    return 0;
}
/* SCAFFOLD END */

#pragma pack(pop)
