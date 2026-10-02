#include "recovered_state.h"

extern void OpenCasteWindow(void);
extern void OpenModeWindow(void);
extern void SetEditWinTitle(char *title);
extern void f_015B_053C(int16_t plane);
extern int16_t win_IsWinOpen(int16_t win);
extern void YardToMap(void);
extern void SetMapTitle(void);
extern void OpenEditWindow(void);
extern int16_t DoScenario(int16_t flag);
extern int16_t o09_35F5_0000(int16_t a, int16_t b);
extern void EndLifeTransferMode(void);
extern void EndTargetMode(void);
extern void SetDefaultWindPrompt(int16_t value);
extern void RandYard(void);
extern int16_t WinPrintf(char *format, ...);
extern void win_Open(int16_t win);
extern int16_t f_22BF_0A65(void);
extern void o26_39C7_0000(void);
extern void CenterEdit(int16_t x, int16_t y);
extern void UpdateEdit(void);


void  SetDefaultWindows(void)
{
    OpenCasteWindow();
    OpenModeWindow();
    SetEditWinTitle(0L);
    f_015B_053C(MapPlane);
    if (!win_IsWinOpen(0x100))
        YardToMap();
    SetMapTitle();
    OpenEditWindow();
}


int16_t  NewGame(int16_t flag)
{
    int16_t r;

    fd_3D57_02C2[0] = 0;
    for (;;) {
        r = DoScenario(flag);
        if (r == 0x205)
            return -1;
        if (r == 0x207) {
            if (o09_35F5_0000(0, 0) == 0)
                continue;
            r = 1;
        } else {
            switch (r) {
            case 0x202:
                r = 1;
                break;
            case 0x203:
                r = 2;
                break;
            case 0x204:
                r = 3;
                break;
            case 0x206:
                r = 0;
                break;
            }
            if (r >= 0 && r < 4) {
                fd_50F6_0EAC = r;
                if (fd_50F6_105E == 10)
                    EndLifeTransferMode();
                else if (fd_50F6_105E == 11)
                    EndTargetMode();
                SetDefaultWindPrompt(1);
                SetEditWinTitle(0L);
                fd_50F6_0354 = 1;
                fd_50F6_07C8 = 0;
                RandYard();
                WinPrintf("MePLane=%d", MePlane);
                f_015B_053C(MePlane);
                if (fd_50F6_0EAC == 0) {
                    fd_3D57_07A4 = 1;
                    fd_3D57_07A6 = 0;
                    if (flag == 0)
                        win_Open(0);
                }
            }
        }
        break;
    }
    SetDefaultWindows();
    f_015B_053C(MePlane);
    if (r == 0 && !f_22BF_0A65())
        o26_39C7_0000();
    CenterEdit(MeLocX, MeLocY);
    UpdateEdit();
    fd_3D57_02C2[0] = 0;
    return r;
}
