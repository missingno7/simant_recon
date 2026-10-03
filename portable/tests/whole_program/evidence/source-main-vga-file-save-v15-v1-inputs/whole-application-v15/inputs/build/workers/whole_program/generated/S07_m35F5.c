#include "portable/whole_program/state/startup_globals_v1.h"
#include "dos_types.h"
#include "portable/whole_program/platform/dos_memory.h"
#include "portable/whole_program/platform/dos_io.h"
#include "portable/whole_program/platform/graphics_source_fields.h"
#include "native_owners.h"
#pragma pack(push, 2)
/* Overlay section S07, code frame 35F5: cheat key handler. */

extern int16_t  fd_3D57_06DE;

extern char  fd_3D57_067E[][4];
extern int16_t  MeLocY;
extern int16_t  MeLocX;
extern char  Dy8[];
extern char  Dx8[];
extern int16_t  fd_3D57_0C18;
extern int16_t  fd_3D57_0C14;
extern int16_t  fd_3D57_0C12;
extern uint8_t  fd_3D57_00A4[12][16];
extern uint8_t  fd_3D57_0164[12][16];
extern int16_t  fd_3D57_0C16;

extern void  WinPrintf(char  *fmt, ...);
extern void  myBeginSound(int16_t sound, int16_t a, int16_t b);
extern void  f_00DF_00E0(int16_t a);
extern void  SetMyHealth(int16_t health);
extern void  PictStrnDialog(int16_t a, int16_t b, int16_t c);
extern void  UpdateEverything(void);
extern void  SetSimCursor(int16_t a);
extern void  InvalQueenStorageDisp(void);
extern void  MakeNewHoleB(int16_t x);
extern void  MakeNewHoleR(int16_t x);
extern void  MakeBlkQueen(int16_t x, int16_t y, int16_t dir);
extern void  MakeRedQueen(int16_t x, int16_t y, int16_t dir);
extern int16_t  RRand(int16_t range);
extern int16_t  SRand2(void);
extern int16_t  SRand8(void);
extern void  PlaceEggB(int16_t x, int16_t y, int16_t type);
extern void  PlaceEggR(int16_t x, int16_t y, int16_t type);
extern void  DrawSimPayoff(void);

void  CheatKeys(int16_t key)
{
    int16_t i, j, k;
    char  *p;

    fd_50F6_0B0A[fd_3D57_06DE] = ~key;
    fd_3D57_06DE++;
    for (i = 0; fd_3D57_067E[i][0] != 0; i++) {
        p = fd_3D57_067E[i];
        for (j = 0; j < fd_3D57_06DE; j++)
            if (p[j] != fd_50F6_0B0A[j])
                break;
        if (j == fd_3D57_06DE)
            break;
    }
    if (fd_3D57_067E[i][0] == 0) {
        for (k = fd_3D57_06DE = 0; k < 4; k++)
            fd_50F6_0B0A[k] = 0;
        return;
    }
    if (fd_3D57_06DE < 4)
        return;
    for (k = fd_3D57_06DE = 0; k < 4; k++)
        fd_50F6_0B0A[k] = 0;
    WinPrintf("CHEAT %d", i);
    switch (i) {
    case 0:
        myBeginSound(10, 0, 0x7e);
        native_state_fd_50F6_0850.signed_value += 10;
        break;
    case 1:
        myBeginSound(1, 0, 0x7e);
        SetMyHealth(100);
        break;
    case 2:
        myBeginSound(1, 0, 0x7e);
        SetMyHealth(1);
        break;
    case 3:
        PictStrnDialog(0, 0x2724, 0);
        break;
    case 4:
        PictStrnDialog(0, 0x2726, 0);
        UpdateEverything();
        SetSimCursor(6);
        f_00DF_00E0(0);
        SetSimCursor(0);
        PictStrnDialog(0, 0x2728, 0);
        break;
    case 5:
        for (i = 0; i < 64; i++)
            MakeNewHoleB(i);
        break;
    case 6:
        for (i = 0; i < 64; i++)
            MakeNewHoleR(i);
        break;
    case 7:
        MakeBlkQueen(MeLocX + 2, MeLocY, 2);
        break;
    case 8:
        MakeRedQueen(MeLocX + 2, MeLocY, 2);
        break;
    case 9:
        for (i = 0; i < 16; i++)
            PlaceEggB(Dx8[SRand8()] + MeLocX, Dy8[SRand8()] + MeLocY, RRand(6) + 1);
        break;
    case 10:
        for (i = 0; i < 16; i++)
            PlaceEggR(Dx8[SRand8()] + MeLocX, Dy8[SRand8()] + MeLocY, RRand(6) + 0x81);
        break;
    case 11:
        native_state_HealthB.signed_value = 100;
        break;
    case 12:
        native_state_HealthR.signed_value = 100;
        break;
    case 13:
        native_state_HealthR.signed_value = 0;
        break;
    case 14:
        fd_3D57_0C18 = 0;
        native_state_HealthB.signed_value = 0;
        break;
    case 15:
        native_state_fd_50F6_07C8.signed_value += 10;
        InvalQueenStorageDisp();
        myBeginSound(0x29, 0, 0x7e);
        break;
    case 16:
        fd_3D57_0C14 = !fd_3D57_0C14;
        if (fd_3D57_0C14)
            myBeginSound(2, 0, 0x7e);
        else
            myBeginSound(1, 0, 0x7e);
        break;
    case 17:
        fd_3D57_0C12 = !fd_3D57_0C12;
        if (fd_3D57_0C12)
            myBeginSound(2, 0, 0x7e);
        else
            myBeginSound(1, 0, 0x7e);
        break;
    case 18:
        myBeginSound(2, 0, 0x7e);
        for (i = 0; i < 12; i++)
            for (j = 0; j < 16; j++) {
                fd_3D57_00A4[i][j] += 4;
                native_state_fd_50F6_0A90.signed_value++;
            }
        break;
    case 19:
        myBeginSound(1, 0, 0x7e);
        for (i = 0; i < 12; i++)
            for (j = 0; j < 16; j++) {
                if (SRand2() == 0) {
                    fd_3D57_00A4[i][j]++;
                    native_state_fd_50F6_0A90.signed_value++;
                } else {
                    fd_3D57_0164[i][j]++;
                    native_state_fd_50F6_0AC4.signed_value++;
                }
            }
        break;
    case 20:
        DrawSimPayoff();
        break;
    case 21:
        fd_3D57_0C16 = !fd_3D57_0C16;
        if (fd_3D57_0C16) {
            native_state_MeHealth.signed_value = 100;
            myBeginSound(2, 0, 0x7e);
        } else
            myBeginSound(1, 0, 0x7e);
        break;
    case 22:
        fd_3D57_0C18 = !fd_3D57_0C18;
        if (fd_3D57_0C18) {
            native_state_HealthB.signed_value = 100;
            myBeginSound(2, 0, 0x7e);
        } else
            myBeginSound(1, 0, 0x7e);
        break;
    }
}

#pragma pack(pop)
