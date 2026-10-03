#include "portable/whole_program/state/main_loop_counter.h"
#include "dos_types.h"
#include "portable/whole_program/platform/dos_memory.h"
#include "portable/whole_program/platform/dos_io.h"
#include "portable/whole_program/platform/graphics_source_fields.h"
#include "simulation_grid_3e1d_v8.h"
#include "simulation_state_50f6_v7.h"
#include "simulation_state_50f6.h"
#include "native_owners.h"
#pragma pack(push, 2)
/* Overlay section S06, code frame 35F5: back-yard simulation (SimYard unit). */

static char dogA[6] = { 3, 4, -3, -4, 0, 0 };  /* 2448 */
static char dogB[6] = { -3, 0, 3, 0, 0, 0 };  /* 244E */
static char dogC[4] = { 0, 1, 2, 1 };  /* 2454 */
static char dogD[6] = { 0, 3, 6, 9, 100, 102 };  /* 2458 */
static char nodeLen[22] = { 3, 3, 18, 18, 3, 3, 10, 10, 5, 5, 3, 3, 4, 4, 3, 3, 0, 0, 0, 0, 7, 4 };  /* 245E */
static uint8_t kidF0[4] = { 4, 5, 4, 3 };  /* 2474 */
static uint8_t kidX0[4] = { 135, 141, 147, 153 };  /* 2478 */
static uint8_t kidY0[4] = { 60, 60, 60, 60 };  /* 247C */
static uint8_t kidF1[4] = { 9, 10, 11, 10 };  /* 2480 */
static uint8_t kidX1[4] = { 150, 144, 138, 132 };  /* 2484 */
static uint8_t kidY1[4] = { 60, 60, 60, 60 };  /* 2488 */
static uint8_t kidF2[20] = { 6, 7, 8, 7, 6, 7, 8, 7, 6, 7, 8, 7, 6, 7, 8, 7, 6, 7, 8, 0 };  /* 248C */
static uint8_t kidX2[20] = { 154, 150, 147, 143, 140, 136, 133, 129, 126, 122, 119, 115, 111, 108, 104, 101, 97, 94, 91, 0 };  /* 24A0 */
static uint8_t kidY2[20] = { 60, 64, 68, 72, 76, 80, 84, 88, 92, 96, 100, 104, 108, 112, 116, 120, 124, 128, 132, 0 };  /* 24B4 */
static uint8_t kidF3[20] = { 0, 1, 2, 1, 0, 1, 2, 1, 0, 1, 2, 1, 0, 1, 2, 1, 0, 1, 2, 0 };  /* 24C8 */
static uint8_t kidX3[20] = { 91, 94, 97, 101, 104, 108, 111, 115, 119, 122, 126, 129, 133, 136, 140, 143, 147, 150, 154, 0 };  /* 24DC */
static uint8_t kidY3[20] = { 132, 128, 124, 120, 116, 112, 108, 104, 100, 96, 92, 88, 84, 80, 76, 72, 68, 64, 60, 0 };  /* 24F0 */
static uint8_t kidF4[4] = { 4, 5, 4, 3 };  /* 2504 */
static uint8_t kidX4[4] = { 65, 71, 77, 83 };  /* 2508 */
static uint8_t kidY4[4] = { 130, 130, 130, 130 };  /* 250C */
static uint8_t kidF5[4] = { 9, 10, 11, 10 };  /* 2510 */
static uint8_t kidX5[4] = { 80, 74, 68, 62 };  /* 2514 */
static uint8_t kidY5[4] = { 130, 130, 130, 130 };  /* 2518 */
static uint8_t kidF6[12] = { 7, 6, 7, 8, 7, 6, 7, 8, 7, 9, 22, 0 };  /* 251C */
static uint8_t kidX6[12] = { 84, 80, 76, 72, 68, 64, 60, 56, 52, 46, 44, 0 };  /* 2528 */
static uint8_t kidY6[12] = { 134, 138, 142, 146, 150, 154, 158, 162, 166, 166, 166, 0 };  /* 2534 */
static uint8_t kidF7[12] = { 22, 3, 0, 1, 2, 1, 0, 1, 2, 1, 0, 0 };  /* 2540 */
static uint8_t kidX7[12] = { 44, 46, 52, 56, 60, 64, 69, 73, 78, 82, 86, 0 };  /* 254C */
static uint8_t kidY7[12] = { 166, 166, 166, 162, 158, 154, 150, 146, 142, 138, 134, 0 };  /* 2558 */
static uint8_t kidF8[6] = { 4, 5, 4, 3, 4, 5 };  /* 2564 */
static uint8_t kidX8[6] = { 159, 165, 171, 177, 183, 189 };  /* 256A */
static uint8_t kidY8[6] = { 60, 60, 60, 60, 60, 60 };  /* 2570 */
static uint8_t kidF9[6] = { 10, 11, 10, 9, 10, 11 };  /* 2576 */
static uint8_t kidX9[6] = { 189, 183, 177, 171, 165, 159 };  /* 257C */
static uint8_t kidY9[6] = { 60, 60, 60, 60, 60, 60 };  /* 2582 */
static uint8_t kidF10[4] = { 0, 1, 2, 1 };  /* 2588 */
static uint8_t kidX10[4] = { 164, 168, 172, 176 };  /* 258C */
static uint8_t kidY10[4] = { 56, 52, 48, 44 };  /* 2590 */
static uint8_t kidF11[4] = { 6, 7, 8, 7 };  /* 2594 */
static uint8_t kidX11[4] = { 176, 172, 168, 164 };  /* 2598 */
static uint8_t kidY11[4] = { 44, 48, 52, 56 };  /* 259C */
static uint8_t kidF12[6] = { 3, 4, 5, 4, 3, 0 };  /* 25A0 */
static uint8_t kidX12[6] = { 182, 188, 194, 200, 206, 0 };  /* 25A6 */
static uint8_t kidY12[6] = { 44, 44, 44, 44, 44, 0 };  /* 25AC */
static uint8_t kidF13[6] = { 9, 10, 11, 10, 9, 0 };  /* 25B2 */
static uint8_t kidX13[6] = { 206, 200, 194, 188, 182, 0 };  /* 25B8 */
static uint8_t kidY13[6] = { 44, 44, 44, 44, 44, 0 };  /* 25BE */
static uint8_t kidF14[4] = { 0, 1, 2, 1 };  /* 25C4 */
static uint8_t kidX14[4] = { 196, 200, 204, 208 };  /* 25C8 */
static uint8_t kidY14[4] = { 56, 52, 48, 44 };  /* 25CC */
static uint8_t kidF15[4] = { 6, 7, 8, 7 };  /* 25D0 */
static uint8_t kidX15[4] = { 208, 204, 200, 196 };  /* 25D4 */
static uint8_t kidY15[4] = { 44, 48, 52, 56 };  /* 25D8 */
static int16_t kidF20[8] = { 6, 7, 8, 900, 901, 902, 6, 7 };  /* 25DC */
static uint8_t kidX20[8] = { 192, 189, 186, 172, 172, 172, 174, 175 };  /* 25EC */
static uint8_t kidY20[8] = { 60, 64, 68, 73, 73, 73, 93, 99 };  /* 25F4 */
static int16_t kidF21[5] = { 0, 903, 900, 1, 2 };  /* 25FC */
static uint8_t kidX21[6] = { 172, 172, 172, 186, 189, 0 };  /* 2606 */
static uint8_t kidY21[6] = { 93, 73, 73, 68, 64, 0 };  /* 260C */
static uint8_t nodeNext0[22] = { 10, 30, 6, 1, 3, 31, 32, 5, 14, 2, 33, 1, 34, 33, 34, 20, 0, 0, 0, 0, 38, 14 };  /* 2612 */
static uint8_t nodeNext1[22] = { 8, 30, 6, 10, 3, 31, 32, 3, 14, 1, 33, 2, 34, 11, 34, 20, 0, 0, 0, 0, 38, 14 };  /* 2628 */
static uint8_t nodeNext2[22] = { 2, 30, 5, 8, 6, 31, 32, 3, 20, 10, 12, 8, 15, 12, 13, 9, 0, 0, 0, 0, 38, 14 };  /* 263E */
static int16_t outF[9] = { -1, -1, 200, 20, 201, -1, 0, 0, 7 };  /* 2654 */
static uint8_t outX[10] = { 0, 0, 45, 176, 207, 0, 0, 0, 176, 0 };  /* 2666 */
static uint8_t outY[10] = { 0, 0, 166, 44, 47, 0, 0, 0, 104, 0 };  /* 2670 */
static uint8_t outChance[10] = { 40, 40, 35, 8, 8, 6, 0, 0, 10, 0 };  /* 267A */
static uint8_t outNext[10] = { 0, 4, 7, 12, 15, 14, 0, 0, 38, 0 };  /* 2684 */
static uint8_t frameDir[12] = { 0, 0, 0, 1, 1, 1, 2, 2, 2, 3, 3, 3 };  /* 268E */
static char stepAnim[4] = { 0, 1, 2, 1 };  /* 269A */
static char dirFrame[4] = { 0, 3, 6, 9 };  /* 269E */
static int16_t footDx[4] = { -10, 25, -10, -33 };  /* 26A2 */
static int16_t footDy[4] = { -33, -10, 25, -10 };  /* 26AA */
static char kidDx[4] = { 0, 1, 0, -1 };  /* 26B2 */
static char kidDy[4] = { -1, 0, 1, 0 };  /* 26B6 */
static uint8_t PatchX[6] = { 0, 1, 0, 255, 0, 0 };  /* 26BA */
static uint8_t PatchY[6] = { 255, 0, 1, 0, 0, 0 };  /* 26C0 */


extern int32_t  MacTickCount(void);
extern int16_t  RRand(int16_t range);
extern int16_t  SRand1(int16_t range);
extern void  InitWater(void);
extern int16_t  SRand32(void);
void  SimKidInside(void);
void  o06_35F5_02B9(void);
void  o06_35F5_11FF(void);
void  o06_35F5_14CC(void);
void  o06_35F5_1803(void);
void  o06_35F5_020C(void);
void  o06_35F5_1E54(void);
int16_t  o06_35F5_0967(int16_t x, int16_t y);
void  o06_35F5_0A5F(void);
void  FootFall(int16_t x, int16_t y);
void  o06_35F5_1CEA(int16_t x, int16_t y);
int16_t  o06_35F5_0A32(int16_t x, int16_t y);
int16_t  o06_35F5_09F7(int16_t x, int16_t y);
/* Far data in first-use order (a header-like block: extern functions and
 * prototypes first, then the variables; this order decides the operand order of
 * two SimKidOutside comparisons). */
extern int16_t  fd_3D57_0C2C;
extern int16_t  fd_3D57_0C2E;
extern int16_t  fd_3D57_0C34;
extern int16_t  fd_3D57_0C2A;
extern int16_t  fd_3D57_0C30;
extern int16_t  fd_3D57_0C32;
extern int16_t  fd_3D57_0C28;
extern int16_t  fd_3D57_0C40;
extern int16_t  fd_3D57_0C46;
extern int16_t  fd_3D57_0C48;
extern int16_t  fd_3D57_0C3E;
extern int16_t  fd_3D57_0C42;
extern int16_t  fd_50F6_0364;
extern int16_t  fd_50F6_036E;
extern int16_t  fd_3D57_0C44;
extern int16_t  TERRAINset;
extern int16_t  fd_50F6_0B20;
extern int16_t  fd_50F6_0EAC;
extern char  fd_3D57_0C36[4];
extern char  fd_3D57_0C3A[4];
extern uint8_t  fd_3D57_00A4[12][16];
extern uint8_t  fd_3D57_0164[12][16];

/* InitSimYard */
void  o06_35F5_0000(void)
{
    native_state_fd_50F6_109C.signed_value = 0L;          /* BoyMsgCnt */
    fd_3D57_0C2C = 0xb4;        /* BoyX */
    fd_3D57_0C2E = 0x49;        /* BoyY */
    fd_3D57_0C34 = 0xc;         /* BoyTurnCnt */
    fd_3D57_0C2A = 0x14;        /* BoyWait */
    native_state_fd_50F6_107E.signed_value = 0L;          /* BirdDelay */
    native_state_fd_50F6_0220.signed_value = 0L;          /* CatDelay */
    native_state_fd_50F6_04BE.signed_value = 0xfa;        /* DogX */
    native_state_fd_50F6_04C6.signed_value = 0x96;        /* DogY */
    fd_3D57_0C30 = 2;           /* BoyDir */
    native_state_fd_50F6_0624.signed_value = 2;           /* DogTurnCnt */
    native_state_fd_50F6_10B0.signed_value = 0;           /* BoyMessOn */
    native_state_fd_50F6_0246.signed_value = 0;           /* BoyPx */
    native_state_fd_50F6_023E.signed_value = 0;           /* BoyPy */
    fd_3D57_0C32 = 0;           /* BoyFrame */
    fd_3D57_0C28 = 0;           /* BoyHere */
    fd_3D57_0C40 = 0;           /* BoyStandCnt */
    fd_3D57_0C46 = 0;           /* NodeCnt */
    fd_3D57_0C48 = 0;           /* NodeNum */
    native_state_fd_50F6_10A0.signed_value = 0;           /* BirdOn */
    native_state_fd_50F6_022C.signed_value = 0;           /* CatCycle */
    native_state_fd_50F6_0244.signed_value = 0;           /* CatFrame */
    native_state_fd_50F6_0254.signed_value = 0;           /* CatOn */
    native_state_fd_50F6_04E4.signed_value = 0;           /* DogFrame */
    native_state_fd_50F6_0506.signed_value = 0;           /* DogDir */
    fd_3D57_0C3E = 0;           /* FootHere */
    fd_3D57_0C42 = 0;           /* FootTog */
    native_state_fd_50F6_03E0.signed_value = 0;           /* FootX */
    native_state_fd_50F6_046A.signed_value = 0;           /* FootY */
    native_state_fd_50F6_0470.signed_value = 0;           /* MowX */
    native_state_fd_50F6_047A.signed_value = 0;           /* MowY */
    native_state_fd_50F6_0202.signed_value = 0;           /* BoyIsMowing */
    native_state_fd_50F6_0352.signed_value = 0;           /* RainOn */
    native_state_fd_50F6_105C.signed_value = 0;           /* SwarmDelayB */
    native_state_fd_50F6_1066.signed_value = 0;           /* SwarmDelayR */
    native_state_fd_50F6_108C.signed_value = 1;           /* BirdFrame */
    fd_50F6_0364 = 1;           /* LastColonyPopB */
    fd_50F6_036E = 1;           /* LastColonyPopR */
    native_state_fd_50F6_10BC.signed_value = -1;          /* BoyMsgOffset */
    native_state_fd_50F6_07C2.signed_value = -1;          /* YardCycle */
}



/* DoSimYard */
void  o06_35F5_0173(void)
{
    native_state_fd_50F6_07C2.signed_value++;
    if (native_state_fd_50F6_07C2.signed_value >= 0x400)
        native_state_fd_50F6_07C2.signed_value = 0;
    if (fd_3D57_0C48 < 0x26)
        SimKidInside();
    else
        o06_35F5_02B9();
    o06_35F5_11FF();
    o06_35F5_14CC();
    if (fd_3D57_0C44 == 0)      /* ForSaleState */
        o06_35F5_1803();
    o06_35F5_020C();
    o06_35F5_1E54();
}


/* SendBoyMsg */
void  o06_35F5_01CA(int16_t message)
{
    if (message <= 22) {
        native_state_fd_50F6_109C.signed_value = MacTickCount() + 300L;
        native_state_fd_50F6_10B0.signed_value = 1;
        native_state_fd_50F6_10BC.signed_value = message;
    }
}


/* SimRain */
void  o06_35F5_020C(void)
{
    if (TERRAINset != 1) {            /* TERRAINset */
        if (native_state_fd_50F6_0352.signed_value == 0) {
            if (fd_50F6_0B20 != 0xa8) { /* GlobalKey */
                if (RRand(32) != 0)
                    return;
                if (RRand(128) != 0)
                    return;
            }
            native_state_fd_50F6_0352.signed_value = 1;
            native_state_fd_50F6_0356.signed_value = SRand1(150) + 150;   /* RainCnt */
            InitWater();                      /* InitWater */
            o06_35F5_01CA(0);
            return;
        }
        if (native_state_fd_50F6_0356.signed_value > 0)
            native_state_fd_50F6_0356.signed_value--;
        if (native_state_fd_50F6_0356.signed_value < 1)
            native_state_fd_50F6_0352.signed_value = 0;
    }
}

/* SimKidOutside: the boy walks and mows the yard; the grass bytes of both
 * colonies under his mower lose a quarter (the second-to-last count goes to
 * fd_50F6_0A9E / fd_50F6_0AC8, Win16 BColoniesKilled / RColoniesKilled). */
void  o06_35F5_02B9(void)
{
     int16_t v;

    if (fd_3D57_0C3E != 0 && (native_state_fd_50F6_07C2.signed_value & 3) != 0)
        return;
    if (native_state_fd_50F6_0202.signed_value != 0) {
        if (native_state_fd_50F6_0488.signed_value != native_state_fd_50F6_0246.signed_value || native_state_fd_50F6_0492.signed_value != native_state_fd_50F6_023E.signed_value)
            fd_3D57_0C30 = o06_35F5_0967(native_state_fd_50F6_0246.signed_value, native_state_fd_50F6_023E.signed_value);
    } else if (--fd_3D57_0C34 < 0) {
        fd_3D57_0C30 = (SRand1(3) + fd_3D57_0C30 - 1) & 3;
        fd_3D57_0C34 = 4;
    }
    switch (fd_3D57_0C28) {
    case 1:
        if (SRand1(900) == 0) {
            o06_35F5_01CA(1);
            fd_3D57_0C28 = 2;
        } else if (SRand1(600) == 0 || fd_50F6_0EAC == 3 || fd_50F6_0EAC == 0) {
            o06_35F5_01CA(2);
            fd_3D57_0C28 = 5;
        } else {
            if (SRand1(200) == 0)
                o06_35F5_01CA(SRand1(8) + 7);
            if (native_state_fd_50F6_0352.signed_value != 0)
                fd_3D57_0C28 = 5;
        }
        break;
    case 2:
        if (native_state_fd_50F6_023E.signed_value < 12)
            fd_3D57_0C30 = 2;
        else if (native_state_fd_50F6_023E.signed_value > 12)
            fd_3D57_0C30 = 0;
        else if (native_state_fd_50F6_0246.signed_value > 3)
            fd_3D57_0C30 = 3;
        else {
            fd_3D57_0C28 = 3;
            native_state_fd_50F6_0488.signed_value = 3;
            native_state_fd_50F6_0492.signed_value = 13;
            native_state_fd_50F6_0202.signed_value = 1;
            o06_35F5_0A5F();
            fd_3D57_0C30 = 2;
            fd_3D57_0C2C = 0x7d;
            fd_3D57_0C2E = 0xaa;
        }
        break;
    case 3:
        if (SRand1(100) == 0)
            o06_35F5_01CA(SRand1(3) + 3);
        if (SRand1(200) == 0) {
            o06_35F5_01CA(6);
            fd_3D57_0C28 = 4;
        }
        native_state_fd_50F6_0488.signed_value = native_state_fd_50F6_0246.signed_value;
        native_state_fd_50F6_0492.signed_value = native_state_fd_50F6_023E.signed_value;
        native_state_fd_50F6_0202.signed_value = 1;
        break;
    case 4:
        if (native_state_fd_50F6_023E.signed_value < 12)
            fd_3D57_0C30 = 2;
        else if (native_state_fd_50F6_023E.signed_value > 12)
            fd_3D57_0C30 = 0;
        else if (native_state_fd_50F6_0246.signed_value > 3)
            fd_3D57_0C30 = 3;
        else {
            fd_3D57_0C28 = 5;
            native_state_fd_50F6_0202.signed_value = 0;
        }
        native_state_fd_50F6_0488.signed_value = native_state_fd_50F6_0246.signed_value;
        native_state_fd_50F6_0492.signed_value = native_state_fd_50F6_023E.signed_value;
        break;
    case 5:
        if (native_state_fd_50F6_023E.signed_value < 5)
            fd_3D57_0C30 = 2;
        else if (native_state_fd_50F6_023E.signed_value > 5)
            fd_3D57_0C30 = 0;
        else if (native_state_fd_50F6_0246.signed_value > 3)
            fd_3D57_0C30 = 3;
        else
            fd_3D57_0C28 = 1;
        break;
    }
    fd_3D57_0C32 = dirFrame[fd_3D57_0C30] + stepAnim[native_state_fd_50F6_07C2.signed_value & 3];
    if (native_state_fd_50F6_0202.signed_value != 0) {
        fd_3D57_0C32 += 100;
        fd_3D57_0C2C += fd_3D57_0C36[fd_3D57_0C30];
        fd_3D57_0C2E += fd_3D57_0C3A[fd_3D57_0C30];
    } else if (fd_3D57_0C40 == 0) {
        if (SRand32() == 0)
            fd_3D57_0C40 = 20;
        fd_3D57_0C2C += fd_3D57_0C36[fd_3D57_0C30];
        fd_3D57_0C2E += fd_3D57_0C3A[fd_3D57_0C30];
    } else {
        fd_3D57_0C40--;
        fd_3D57_0C32 = fd_3D57_0C30 + 20;
    }
    native_state_fd_50F6_0246.signed_value = (fd_3D57_0C2C + fd_3D57_0C2E - 200) / 28;
    native_state_fd_50F6_023E.signed_value = (fd_3D57_0C2E - 38) / 10;
    if (native_state_fd_50F6_023E.signed_value < 0)
        native_state_fd_50F6_023E.signed_value = 0;
    if (native_state_fd_50F6_023E.signed_value > 15)
        native_state_fd_50F6_023E.signed_value = 15;
    if (native_state_fd_50F6_0246.signed_value < 0)
        native_state_fd_50F6_0246.signed_value = 0;
    if (native_state_fd_50F6_0246.signed_value > 11)
        native_state_fd_50F6_0246.signed_value = 11;
    if (native_state_fd_50F6_0202.signed_value == 0) {
        if (native_state_fd_50F6_023E.signed_value < 1)
            fd_3D57_0C30 = 2;
        else if (native_state_fd_50F6_023E.signed_value > 14)
            fd_3D57_0C30 = 0;
        if (native_state_fd_50F6_0246.signed_value > 10)
            fd_3D57_0C30 = 3;
        else if (native_state_fd_50F6_023E.signed_value < 5) {
            if (native_state_fd_50F6_0246.signed_value < 4)
                fd_3D57_0C30 = 1;
        } else if (native_state_fd_50F6_0246.signed_value < 3) {
            fd_3D57_0C30 = 0;
            if (native_state_fd_50F6_023E.signed_value < 6) {
                if (fd_3D57_0C28 == 3)
                    fd_3D57_0C30 = 1;
                else
                    fd_3D57_0C48 = 21;
            }
        }
    }
    fd_3D57_0C3E = 0;
    fd_3D57_0C42 = !fd_3D57_0C42;
    if (native_state_fd_50F6_023E.signed_value == native_sim_state_fd_50F6_07CA.words[1] && native_state_fd_50F6_0246.signed_value == native_sim_state_fd_50F6_07CA.words[0]) {
        fd_3D57_0C3E = 1;
        native_state_fd_50F6_046A.signed_value = (fd_3D57_0C2E - 38) % 10;
        native_state_fd_50F6_03E0.signed_value = (fd_3D57_0C2C + fd_3D57_0C2E - 200) % 28;
        native_state_fd_50F6_03E0.signed_value = ((native_state_fd_50F6_03E0.signed_value << 2) + 6) & 0x7f;
        native_state_fd_50F6_046A.signed_value = ((native_state_fd_50F6_046A.signed_value + 1) * 6) & 0x3f;
        native_state_fd_50F6_0470.signed_value = native_state_fd_50F6_03E0.signed_value + footDx[fd_3D57_0C30 & 3];
        native_state_fd_50F6_047A.signed_value = native_state_fd_50F6_046A.signed_value + footDy[fd_3D57_0C30 & 3];
        if (fd_3D57_0C30 & 1) {
            if (fd_3D57_0C42 != 0)
                native_state_fd_50F6_046A.signed_value += 6;
            else
                native_state_fd_50F6_046A.signed_value -= 6;
        } else {
            if (fd_3D57_0C42 != 0)
                native_state_fd_50F6_03E0.signed_value += 6;
            else
                native_state_fd_50F6_03E0.signed_value -= 6;
        }
        FootFall(native_state_fd_50F6_03E0.signed_value, native_state_fd_50F6_046A.signed_value);
        if (native_state_fd_50F6_0202.signed_value != 0)
            o06_35F5_1CEA(native_state_fd_50F6_0470.signed_value, native_state_fd_50F6_047A.signed_value);
    } else if (native_state_fd_50F6_0202.signed_value != 0) {
        if ((v = fd_3D57_00A4[native_state_fd_50F6_0246.signed_value][native_state_fd_50F6_023E.signed_value]) != 0) {
            if ((v -= v >> 2) == 0)
                native_state_fd_50F6_0A9E.signed_value++;
            fd_3D57_00A4[native_state_fd_50F6_0246.signed_value][native_state_fd_50F6_023E.signed_value] = v;
        }
        if ((v = fd_3D57_0164[native_state_fd_50F6_0246.signed_value][native_state_fd_50F6_023E.signed_value]) != 0) {
            if ((v -= v >> 2) == 0)
                native_state_fd_50F6_0AC8.signed_value++;
            fd_3D57_0164[native_state_fd_50F6_0246.signed_value][native_state_fd_50F6_023E.signed_value] = v;
        }
    }
}

/* GetMowDir (Win16 unit order): direction toward an adjacent uncut grass cell */
int16_t  o06_35F5_0967(int16_t x, int16_t y)
{
    int16_t i, ny, nx;

    for (i = 3; i >= 0; i--) {
        nx = kidDx[i] + x;
        ny = kidDy[i] + y;
        if (o06_35F5_0A32(nx, ny) && o06_35F5_09F7(nx, ny))
            return i;
    }
    if (x > 10)
        return 0;
    if (y > 14)
        return 1;
    if (y < 1) {
        o06_35F5_01CA(6);
        fd_3D57_0C28 = 4;
        return 2;
    }
    return native_state_fd_50F6_07C2.signed_value & 3;
}


/* NotMowed (Win16 unit order): cut the grass bit of a yard cell */
int16_t  o06_35F5_09F7(int16_t x, int16_t y)
{
    int16_t bit;

    bit = 1 << y;
    if (native_sim_state_fd_50F6_0334.signed_values[x] & bit) {
        native_sim_state_fd_50F6_0334.signed_values[x] -= bit;
        return 1;
    }
    return 0;
}

/* IsValidYard */
int16_t  o06_35F5_0A32(int16_t x, int16_t y)
{
    if (x >= 0 && y >= 0 && x <= 11 && y <= 15)
        return 1;
    return 0;
}

/* InitGrassMap */
void  o06_35F5_0A5F(void)
{
    int16_t i;

    native_sim_state_fd_50F6_0334.signed_values[0] = 0;
    native_sim_state_fd_50F6_0334.signed_values[1] = 0;
    native_sim_state_fd_50F6_0334.signed_values[2] = 0;
    for (i = 3; i < 12; ++i)
        native_sim_state_fd_50F6_0334.signed_values[i] = -1;
}


/* SimKidInside (exact under 6.00AX /Oe /Og /Zi, worker resJ/s06).  The row division
 * fd_50F6_023E = (BoyY - 38) / 10 comes before the column division in the source; /Og schedules
 * the column store first, and only in this order is (BoyY - 38) kept as a global CSE temp
 * [bp-24h] across the early returns (in column-first order the local CSE of BoyY into CX blocks
 * it; micro contrast work/resJ/s06/m/m1.c vs m2.c).  Local names are byte-equivalent
 * hypotheses: the final loop counts with x (the kidX home [bp-2]) and draws the row into i (SI)
 * and the column into frame (DI); the else-if index (c48 - 30) is i. */
extern int16_t  fd_3D57_07C8;
extern int16_t  Tindex;
extern uint8_t  AlistT[];
extern int16_t  MePlane;
extern void  myBeginSound(int16_t sound, int16_t a, int16_t b);
extern int16_t  SRand128(void);
extern int16_t  SRand64(void);
extern int16_t  SRand4(void);
extern int16_t  FindInAList(int16_t x, int16_t y);
extern void  DeadAntHere(int16_t x, int16_t y, int16_t flag);
extern void  KillSpider(void);
extern void  YellowDeath(int16_t a);

/* SimKidInside: the boy's walk through the house, node by node */
void  SimKidInside(void)
{
    int16_t x, y, frame;
    int16_t i;

    if (fd_3D57_0C44 == 1)
        return;
    if (fd_3D57_0C48 < 30 && nodeLen[fd_3D57_0C48] < ++fd_3D57_0C46) {
        fd_3D57_0C46 = 0;
        switch (SRand1(3)) {
        case 0:
            frame = nodeNext0[fd_3D57_0C48];
            break;
        case 1:
            frame = nodeNext1[fd_3D57_0C48];
            break;
        case 2:
            frame = nodeNext2[fd_3D57_0C48];
            break;
        }
        fd_3D57_0C48 = frame;
        switch (frame) {
        case 6:
            o06_35F5_01CA(21);
            break;
        case 7:
            o06_35F5_01CA(22);
            break;
        case 14:
            o06_35F5_01CA(SRand1(3) + 15);
            break;
        case 16:
            o06_35F5_01CA(SRand1(2) + 18);
            break;
        case 33:
            o06_35F5_01CA(20);
            break;
        }
    }
    if (fd_3D57_0C48 < 30) {
        switch (fd_3D57_0C48) {
        case 0:
            frame = kidF0[fd_3D57_0C46];
            x = kidX0[fd_3D57_0C46];
            y = kidY0[fd_3D57_0C46];
            break;
        case 1:
            frame = kidF1[fd_3D57_0C46];
            x = kidX1[fd_3D57_0C46];
            y = kidY1[fd_3D57_0C46];
            break;
        case 2:
            frame = kidF2[fd_3D57_0C46];
            x = kidX2[fd_3D57_0C46];
            y = kidY2[fd_3D57_0C46];
            break;
        case 3:
            frame = kidF3[fd_3D57_0C46];
            x = kidX3[fd_3D57_0C46];
            y = kidY3[fd_3D57_0C46];
            break;
        case 4:
            frame = kidF4[fd_3D57_0C46];
            x = kidX4[fd_3D57_0C46];
            y = kidY4[fd_3D57_0C46];
            break;
        case 5:
            frame = kidF5[fd_3D57_0C46];
            x = kidX5[fd_3D57_0C46];
            y = kidY5[fd_3D57_0C46];
            break;
        case 6:
            frame = kidF6[fd_3D57_0C46];
            x = kidX6[fd_3D57_0C46];
            y = kidY6[fd_3D57_0C46];
            break;
        case 7:
            frame = kidF7[fd_3D57_0C46];
            x = kidX7[fd_3D57_0C46];
            y = kidY7[fd_3D57_0C46];
            break;
        case 8:
            frame = kidF8[fd_3D57_0C46];
            x = kidX8[fd_3D57_0C46];
            y = kidY8[fd_3D57_0C46];
            break;
        case 9:
            frame = kidF9[fd_3D57_0C46];
            x = kidX9[fd_3D57_0C46];
            y = kidY9[fd_3D57_0C46];
            break;
        case 10:
            frame = kidF10[fd_3D57_0C46];
            x = kidX10[fd_3D57_0C46];
            y = kidY10[fd_3D57_0C46];
            break;
        case 11:
            frame = kidF11[fd_3D57_0C46];
            x = kidX11[fd_3D57_0C46];
            y = kidY11[fd_3D57_0C46];
            break;
        case 12:
            frame = kidF12[fd_3D57_0C46];
            x = kidX12[fd_3D57_0C46];
            y = kidY12[fd_3D57_0C46];
            break;
        case 13:
            frame = kidF13[fd_3D57_0C46];
            x = kidX13[fd_3D57_0C46];
            y = kidY13[fd_3D57_0C46];
            break;
        case 14:
            frame = kidF14[fd_3D57_0C46];
            x = kidX14[fd_3D57_0C46];
            y = kidY14[fd_3D57_0C46];
            break;
        case 15:
            frame = kidF15[fd_3D57_0C46];
            x = kidX15[fd_3D57_0C46];
            y = kidY15[fd_3D57_0C46];
            break;
        case 20:
            frame = kidF20[fd_3D57_0C46];
            x = kidX20[fd_3D57_0C46];
            y = kidY20[fd_3D57_0C46];
            break;
        case 21:
            frame = kidF21[fd_3D57_0C46];
            x = kidX21[fd_3D57_0C46];
            y = kidY21[fd_3D57_0C46];
            break;
        }
    } else if (fd_3D57_0C48 < 39) {
        i = fd_3D57_0C48 - 30;
        frame = outF[i];
        x = outX[i];
        y = outY[i];
        if (SRand1(outChance[i]) == 0) {
            fd_3D57_0C48 = outNext[i];
            fd_3D57_0C46 = 0;
        }
    }
    fd_3D57_0C28 = 0;
    if (fd_3D57_0C48 == 38)
        fd_3D57_0C28 = fd_3D57_0C30 = 1;
    if (fd_3D57_0C48 == 20 && fd_3D57_0C46 > 2)
        fd_3D57_0C28 = 1;
    if (fd_3D57_0C48 == 21 && fd_3D57_0C46 < 3)
        fd_3D57_0C28 = 1;
    fd_3D57_0C2C = x;
    fd_3D57_0C2E = y;
    fd_3D57_0C32 = frame;
    if (fd_3D57_07C8 == 0 && native_state_YardMode.signed_value < 2) {
        if ((fd_3D57_0C46 == 3 && fd_3D57_0C48 == 20 && fd_3D57_0C32 == 900) ||
            (fd_3D57_0C46 == 1 && fd_3D57_0C48 == 21 && fd_3D57_0C32 == 903) ||
            (fd_3D57_0C46 == 6 && fd_3D57_0C48 == 20 && fd_3D57_0C32 == 6) ||
            (fd_3D57_0C46 == 3 && fd_3D57_0C48 == 21 && fd_3D57_0C32 == 1))
            myBeginSound(0x18, 0, 0);
    }
    native_state_fd_50F6_023E.signed_value = (fd_3D57_0C2E - 38) / 10;
    native_state_fd_50F6_0246.signed_value = (fd_3D57_0C2C + fd_3D57_0C2E - 200) / 28;
    fd_3D57_0C3E = 0;
    fd_3D57_0C42 = !fd_3D57_0C42;
    i = (native_sim_state_fd_50F6_07CA.words[0] << 4) + native_sim_state_fd_50F6_07CA.words[1];
    if (native_state_fd_50F6_023E.signed_value != native_sim_state_fd_50F6_07CA.words[1] || native_sim_state_fd_50F6_07CA.words[0] != native_state_fd_50F6_0246.signed_value)
        return;
    if (i == 0 || i == 1 || i == 16 || i == 32)
        return;
    if (fd_3D57_0C32 >= 0 && fd_3D57_0C32 < 12)
        fd_3D57_0C30 = frameDir[fd_3D57_0C32];
    else
        fd_3D57_0C30 = 2;
    fd_3D57_0C3E = 1;
    native_state_fd_50F6_046A.signed_value = (fd_3D57_0C2E - 38) % 10;
    native_state_fd_50F6_03E0.signed_value = (fd_3D57_0C2C + fd_3D57_0C2E - 200) % 28;
    native_state_fd_50F6_03E0.signed_value = ((native_state_fd_50F6_03E0.signed_value << 2) + 6) & 0x7f;
    native_state_fd_50F6_046A.signed_value = ((native_state_fd_50F6_046A.signed_value + 1) * 6) & 0x3f;
    if (fd_3D57_0C30 & 1) {
        if (fd_3D57_0C42 != 0)
            native_state_fd_50F6_046A.signed_value += 6;
        else
            native_state_fd_50F6_046A.signed_value -= 6;
    } else {
        if (fd_3D57_0C42 != 0)
            native_state_fd_50F6_03E0.signed_value += 6;
        else
            native_state_fd_50F6_03E0.signed_value -= 6;
    }
    FootFall(native_state_fd_50F6_03E0.signed_value, native_state_fd_50F6_046A.signed_value);
    myBeginSound(9, 0, 0x7e);
    for (x = 0; x < (native_state_BpopT.signed_value + native_state_RpopT.signed_value) << 3; x++) {
        i = SRand128();
        frame = SRand64();
        if (native_sim_grid_fd_3E1D_6180.cells[i][frame] != 0) {
            Tindex = FindInAList(i, frame);
            if (Tindex >= 0) {
                DeadAntHere(i, frame, AlistT[Tindex] & 0x80);
                native_sim_grid_fd_3E1D_6180.cells[i][frame] = AlistT[Tindex] = 0;
            }
        }
        if ((native_state_fd_50F6_0F12.signed_value >> 4) == i && (native_state_fd_50F6_0F34.signed_value >> 4) == frame)
            KillSpider();
    }
    if (fd_50F6_0EAC == 2 && MePlane == 1 && SRand4() == 0)
        YellowDeath(9);
}

extern void  InvalQueenStorageDisp(void);
extern int16_t  SRand2(void);

/* SimBird (Win16 pair MEDIUM, unit order): the bird flies over the yard and eats swarms */
void  o06_35F5_11FF(void)
{
    int16_t d;
    int16_t step;
    int16_t oldY;
    int16_t soundValue;
    int32_t now;

    if (native_state_fd_50F6_10A0.signed_value != 0) {
        if (native_state_fd_50F6_10A0.signed_value == 1)
            native_state_fd_50F6_10AC.signed_value += 0x10;
        else
            native_state_fd_50F6_10AC.signed_value += 8;
        if (native_state_fd_50F6_10A0.signed_value == 1) {
            d = native_state_fd_50F6_0210.signed_value - native_state_fd_50F6_10BA.signed_value;
            if (d != 0) {
                if (((d >= 0) ? d : -d) >= 4)
                    native_state_fd_50F6_10BA.signed_value += d > 0 ? 4 : -4;
                else
                    native_state_fd_50F6_10BA.signed_value += d > 0 ? 1 : -1;
            }
        } else
            native_state_fd_50F6_10BA.signed_value -= 8;
        native_state_fd_50F6_108C.signed_value = (native_state_fd_50F6_108C.signed_value + 1) & 1;
        if (native_state_fd_50F6_10AC.signed_value < 0 || native_state_fd_50F6_10AC.signed_value > 0x1ff || native_state_fd_50F6_10BA.signed_value < 0 || native_state_fd_50F6_10BA.signed_value > 0xff) {
            native_state_fd_50F6_10A0.signed_value = 0;
            native_state_fd_50F6_107E.signed_value = fd_50F6_383A + 30L;
            return;
        }
        if (native_state_fd_50F6_10A0.signed_value != 1)
            return;
        if (native_state_fd_50F6_10AC.signed_value < native_state_fd_50F6_0208.signed_value || native_state_fd_50F6_10BA.signed_value < native_state_fd_50F6_0210.signed_value - 4 ||
            native_state_fd_50F6_10BA.signed_value > native_state_fd_50F6_0210.signed_value + 4)
            return;
        if (native_state_fd_50F6_06AA.signed_value > 0)
            native_state_fd_50F6_06AA.signed_value -= (native_state_fd_50F6_06AA.signed_value + 7) >> 3;
        if (native_state_fd_50F6_07C8.signed_value > 0) {
            native_state_fd_50F6_07C8.signed_value -= (native_state_fd_50F6_07C8.signed_value + 7) >> 3;
            InvalQueenStorageDisp();
        }
        if (native_state_fd_50F6_073A.signed_value > 0)
            native_state_fd_50F6_073A.signed_value -= (native_state_fd_50F6_073A.signed_value + 7) >> 3;
        if (native_state_fd_50F6_0850.signed_value > 0)
            native_state_fd_50F6_0850.signed_value -= (native_state_fd_50F6_0850.signed_value + 7) >> 3;
        if (fd_3D57_07C8 == 0 && native_state_YardMode.signed_value < 2) {
            if (SRand2() == 0)
                myBeginSound(7, 0, 6);
        }
        native_state_fd_50F6_10A0.signed_value = 2;
    } else if (fd_50F6_383A > native_state_fd_50F6_107E.signed_value) {
        native_state_fd_50F6_107E.signed_value = fd_50F6_383A + 20L;
        if (native_sim_state_fd_50F6_07CA.words[0] >= 5 && SRand2() == 0 &&
            (native_state_fd_50F6_06AA.signed_value > 0 || native_state_fd_50F6_073A.signed_value > 0)) {
            native_state_fd_50F6_0208.signed_value = native_sim_state_fd_50F6_07CA.words[0] * 0x1c - native_sim_state_fd_50F6_07CA.words[1] * 10 + 0xb2;
            native_state_fd_50F6_0210.signed_value = native_sim_state_fd_50F6_07CA.words[1] * 10 + 0x2e;
            native_state_fd_50F6_10A0.signed_value = 1;
            native_state_fd_50F6_10AC.signed_value = 0;
            native_state_fd_50F6_10BA.signed_value = SRand64() + 4;
            native_state_fd_50F6_108C.signed_value = 0;
        }
    }
}

extern char  Dx8[];
extern char  Dy8[];
extern int16_t  SRand16(void);
extern uint32_t  GetDis(int16_t x1, int16_t y1, int16_t x2, int16_t y2);

/* SimCat (Win16 pair MEDIUM, unit order) */
void  o06_35F5_14CC(void)
{
     int16_t newX;
     int16_t newY;

    if (native_state_fd_50F6_0254.signed_value != 0) {
        native_state_fd_50F6_022C.signed_value = (native_state_fd_50F6_022C.signed_value + 1) & 0xfff;
        if (native_state_fd_50F6_0254.signed_value == 1) {
            newX = native_state_fd_50F6_02BE.signed_value + Dx8[native_state_fd_50F6_0240.signed_value] * 4;
            newY = native_state_fd_50F6_032C.signed_value + Dy8[native_state_fd_50F6_0240.signed_value] * 4;
            if (SRand16() != 0 && newX >= 0xfc && newX <= 0x1ef) {
                native_state_fd_50F6_02BE.signed_value = newX;
                native_state_fd_50F6_032C.signed_value = newY;
                native_state_fd_50F6_0244.signed_value++;
                if (native_state_fd_50F6_0240.signed_value == 2) {
                    if (native_state_fd_50F6_0244.signed_value >= 3)
                        native_state_fd_50F6_0244.signed_value = 1;
                } else {
                    if (native_state_fd_50F6_0244.signed_value >= 6)
                        native_state_fd_50F6_0244.signed_value = 4;
                }
            } else if (native_state_fd_50F6_0240.signed_value == 2) {
                native_state_fd_50F6_0240.signed_value = 6;
                native_state_fd_50F6_0244.signed_value = 4;
            } else {
                native_state_fd_50F6_0240.signed_value = 2;
                native_state_fd_50F6_0244.signed_value = 1;
            }
            if (fd_3D57_07C8 == 0 && native_state_YardMode.signed_value < 2 && SRand64() == 0) {
                myBeginSound(0xd, 0, 5);
                return;
            }
            if (SRand16() == 0 && native_state_fd_50F6_022C.signed_value > 100 && native_state_fd_50F6_0506.signed_value == 2 && fd_3D57_0C28 == 0) {
                native_state_fd_50F6_0254.signed_value = 2;
                native_state_fd_50F6_022C.signed_value = 0;
                native_state_fd_50F6_0244.signed_value = 10;
                return;
            }
            if (native_state_fd_50F6_022C.signed_value > 50) {
                if (GetDis(native_state_fd_50F6_02BE.signed_value, native_state_fd_50F6_032C.signed_value, native_state_fd_50F6_04BE.signed_value, native_state_fd_50F6_04C6.signed_value) <= 0x960) {
                    native_state_fd_50F6_0254.signed_value = 3;
                    native_state_fd_50F6_0244.signed_value = 20;
                    if (fd_3D57_07C8 == 0 && native_state_YardMode.signed_value < 2)
                        myBeginSound(0xe, 0, 5);
                }
            }
        } else if (native_state_fd_50F6_0254.signed_value == 2) {
            if (++native_state_fd_50F6_0244.signed_value >= 13)
                native_state_fd_50F6_0244.signed_value = 11;
            if (++native_state_fd_50F6_022C.signed_value > 30) {
                native_state_fd_50F6_022C.signed_value = 0;
                native_state_fd_50F6_0254.signed_value = 1;
                native_state_fd_50F6_0244.signed_value = (native_state_fd_50F6_0240.signed_value == 2) ? 0 : 3;
            }
        } else {
            if (++native_state_fd_50F6_0244.signed_value >= 30) {
                native_state_fd_50F6_0244.signed_value = 0;
                native_state_fd_50F6_0254.signed_value = 0;
                native_state_fd_50F6_0220.signed_value = MacTickCount() + 600L;
            }
        }
    } else if (MacTickCount() > native_state_fd_50F6_0220.signed_value) {
        native_state_fd_50F6_0220.signed_value = MacTickCount() + 200L;
        if (SRand16() == 0 || fd_50F6_0B20 == 0x8d) {
            native_state_fd_50F6_0254.signed_value = 1;
            native_state_fd_50F6_02BE.signed_value = 0xfc;
            native_state_fd_50F6_032C.signed_value = 0x19;
            native_state_fd_50F6_0240.signed_value = 2;
            native_state_fd_50F6_0244.signed_value = 0;
            native_state_fd_50F6_022C.signed_value = 0;
        }
    }
}

int16_t  o06_35F5_1A0F(void);
int16_t  o06_35F5_1ABF(void);
void  o06_35F5_1B08(int16_t kind, int16_t level);

/* SimDog (Win16 unit order) */
void  o06_35F5_1803(void)
{
    if (--native_state_fd_50F6_0624.signed_value < 0) {
        if (native_state_fd_50F6_0254.signed_value != 0)
            native_state_fd_50F6_0506.signed_value = o06_35F5_1ABF();
        else if (fd_3D57_0C48 < 0x26)
            native_state_fd_50F6_0506.signed_value = (SRand1(3) + native_state_fd_50F6_0506.signed_value - 1) & 3;
        else
            native_state_fd_50F6_0506.signed_value = o06_35F5_1A0F();
        native_state_fd_50F6_0624.signed_value = 4;
    }
    if (native_state_fd_50F6_0506.signed_value == 1 && SRand1(10) == 0) {
        native_state_fd_50F6_0506.signed_value = SRand2() + 4;
        native_state_fd_50F6_0624.signed_value = 6;
    }
    if (native_state_fd_50F6_0506.signed_value > 3)
        native_state_fd_50F6_04E4.signed_value = dogD[native_state_fd_50F6_0506.signed_value] + (native_state_fd_50F6_07C2.signed_value & 1);
    else
        native_state_fd_50F6_04E4.signed_value = dogD[native_state_fd_50F6_0506.signed_value] + dogC[native_state_fd_50F6_07C2.signed_value & 3];
    native_state_fd_50F6_04C6.signed_value += dogB[native_state_fd_50F6_0506.signed_value];
    native_state_fd_50F6_059E.signed_value = (native_state_fd_50F6_04C6.signed_value - 38) / 10;
    native_state_fd_50F6_04BE.signed_value += dogA[native_state_fd_50F6_0506.signed_value];
    native_state_fd_50F6_0510.signed_value = (native_state_fd_50F6_04BE.signed_value + native_state_fd_50F6_04C6.signed_value - 200) / 28;
    if (native_state_fd_50F6_059E.signed_value < 0)
        native_state_fd_50F6_059E.signed_value = 0;
    if (native_state_fd_50F6_059E.signed_value > 15)
        native_state_fd_50F6_059E.signed_value = 15;
    if (native_state_fd_50F6_0510.signed_value < 0)
        native_state_fd_50F6_0510.signed_value = 0;
    if (native_state_fd_50F6_0510.signed_value > 11)
        native_state_fd_50F6_0510.signed_value = 11;
    if (native_state_fd_50F6_059E.signed_value < 1)
        native_state_fd_50F6_0506.signed_value = 2;
    else if (native_state_fd_50F6_059E.signed_value > 14)
        native_state_fd_50F6_0506.signed_value = 0;
    if (native_state_fd_50F6_0510.signed_value > 10)
        native_state_fd_50F6_0506.signed_value = 3;
    else if (native_state_fd_50F6_0510.signed_value < 4)
        native_state_fd_50F6_0506.signed_value = 1;
    if (native_state_fd_50F6_04E4.signed_value >= 100 && native_state_fd_50F6_04E4.signed_value <= 103 && SRand1(6) == 0)
        o06_35F5_1B08(SRand4(), 5);
}

/* FollowBoyDir (Win16 unit order): dog direction toward the boy */
int16_t  o06_35F5_1A0F(void)
{
     int16_t dy;
    int16_t dx;
     int16_t ady;
    int16_t adx;

    dy = native_state_fd_50F6_059E.signed_value - native_state_fd_50F6_023E.signed_value;
    dx = native_state_fd_50F6_0510.signed_value - native_state_fd_50F6_0246.signed_value;
    if (dx < 0)
        adx = -dx;
    else
        adx = dx;
    if (dy < 0)
        ady = -dy;
    else
        ady = dy;
    if (adx < 1 && ady < 1 && native_state_fd_50F6_0202.signed_value != 0)
        o06_35F5_1B08(1, 0x7f);
    if (adx < 2 && ady < 2)
        return native_state_fd_50F6_07C2.signed_value & 3;
    if (dy < 0)
        return 2;
    if (dy > 1)
        return 0;
    if (dx < 0)
        return 1;
    if (dx > 1)
        return 3;
    return native_state_fd_50F6_07C2.signed_value & 3;
}

/* FollowCatDir (Win16 unit order) */
int16_t  o06_35F5_1ABF(void)
{
    if (native_state_fd_50F6_0510.signed_value < 5)
        return 1;
    if (native_state_fd_50F6_0510.signed_value > 8)
        return 3;
    if (native_state_fd_50F6_059E.signed_value > 0)
        return 0;
    return native_state_fd_50F6_07C2.signed_value & 3;
}

/* MakeBark (Win16 unit order) */
void  o06_35F5_1B08(int16_t kind, int16_t level)
{
    if (fd_3D57_07C8 == 0 && native_state_YardMode.signed_value < 2 && MacTickCount() > native_state_fd_50F6_0736.signed_value) {
        switch (kind) {
        case 0:
        case 2:
            myBeginSound(0x17, 0, level);
            break;
        case 1:
            myBeginSound(0x15, 0, level);
            break;
        case 3:
            myBeginSound(0x16, 0, level);
            break;
        }
        native_state_fd_50F6_0736.signed_value = MacTickCount() + SRand1(30) + 60;
    }
}

extern int16_t  IsYellowAnt(int16_t a);
extern int16_t  fd_50F6_0A06;

/* FootFall: the boy's foot squashes ants under it */
void  FootFall(int16_t x, int16_t y)
{
    int16_t i, j, a, x2, y2;

    myBeginSound(0x23, 0, 0x14);
    if (fd_3D57_0C30 & 1) {
        x2 = x + 16;
        y2 = y + 6;
    } else {
        x2 = x + 6;
        y2 = y + 16;
    }
    for (i = x; i < x2; i++) {
        for (j = y; j < y2; j++) {
            if (i >= 0 && i <= 127 && j >= 0 && j <= 127) {
                if ((a = native_sim_grid_fd_3E1D_6180.cells[i][j]) != 0) {
                    if (IsYellowAnt(a) == 0) {
                        a = FindInAList(i, j);
                        if (a >= 0) {
                            DeadAntHere(i, j, AlistT[a] & 0x80);
                            AlistT[a] = 0;
                        }
                    } else
                        YellowDeath(5);
                }
            }
        }
    }
    if (native_state_SuserX.signed_value >= x && native_state_SuserX.signed_value < x2 && native_state_SuserY.signed_value >= y && native_state_SuserY.signed_value < y2) {
        KillSpider();
        if (fd_50F6_0A06 == 1)
            YellowDeath(5);
    }
}

extern int16_t  ListIndexA;
extern uint8_t  AlistX[];
extern uint8_t  AlistY[];

/* MowerFall (Win16 unit order): the mower kills ants in the yard */
void  o06_35F5_1CEA(int16_t x, int16_t y)
{
     int16_t i;

    if (fd_50F6_0EAC == 0)
        return;
    i = ListIndexA;
    while (i > 0) {
        i--;
        if (AlistT[i] != 0 && SRand4() != 0) {
            AlistT[i] = native_sim_grid_fd_3E1D_6180.cells[AlistX[i]][AlistY[i]] = 0;
        }
    }
    if (native_state_fd_50F6_0F0C.signed_value != 0 && SRand4() != 0)
        KillSpider();
    if (fd_50F6_0A06 <= 1 && MePlane == 1 && SRand4() != 0)
        YellowDeath(6);
}

/* MaintainSwarm (Win16 unit order) */
void  o06_35F5_1D9D(void)
{
     int16_t n;

    n = native_state_fd_50F6_06AA.signed_value;
    if (n > 0) {
        if (n >= 4)
            n = native_state_fd_50F6_06AA.signed_value - (native_state_fd_50F6_06AA.signed_value >> 2);
        else
            n = native_state_fd_50F6_06AA.signed_value - 1;
    }
    if (native_state_fd_50F6_07C8.signed_value > n)
        n = native_state_fd_50F6_07C8.signed_value;
    if (n > 50)
        n = 50;
    native_state_fd_50F6_06AA.signed_value = n;

    n = native_state_fd_50F6_073A.signed_value;
    if (n > 0) {
        if (n >= 4)
            n = native_state_fd_50F6_073A.signed_value - (native_state_fd_50F6_073A.signed_value >> 2);
        else
            n = native_state_fd_50F6_073A.signed_value - 1;
    }
    if (native_state_fd_50F6_0850.signed_value > n)
        n = native_state_fd_50F6_0850.signed_value;
    if (n > 50)
        n = 50;
    native_state_fd_50F6_073A.signed_value = n;
}

extern int16_t  fd_3D57_0C20;
extern int16_t  fd_3D57_02C0;
extern int16_t  SRand8(void);
extern void  myBeginSong(int16_t id, int16_t arg);
extern void  PictStrnDialog(int16_t a, int16_t b, int16_t c);
extern void  DrawSimPayoff(void);
int16_t  o06_35F5_2314(int16_t x, int16_t y);
void  o06_35F5_2381(int16_t x, int16_t y, int16_t colony);

/* SimColonies (Win16 unit order): yard colony growth, swarms and the for-sale scenario */
/* r also carries the two home-nest populations before the loops and b is read before r: both
 * decide the frame layout (r at [bp-8], b [bp-4], patches [bp-2]); the nested game-type test
 * keeps the /Zi line-entry count that places a LEDATA break in 229F..2309 (worker resB). */
void  o06_35F5_1E54(void)
{
    int16_t patches, b, y, r;
    int16_t x;

    if (native_state_fd_50F6_07C2.signed_value & 0x1f)
        return;
    fd_3D57_0C20 = 1;
    o06_35F5_1D9D();
    native_state_fd_50F6_03E2.signed_value = 0;
    native_state_fd_50F6_0400.signed_value = 0;
    native_state_fd_50F6_0478.signed_value = 0;
    if (native_state_BpopT.signed_value > 0)
        native_state_fd_50F6_03E2.signed_value = 1;
    if (native_state_RpopT.signed_value > 0)
        native_state_fd_50F6_0400.signed_value = 1;
    r = native_state_BpopT.signed_value & 0x3ff;
    if (r > 250)
        r = 250;
    fd_3D57_00A4[native_sim_state_fd_50F6_07CA.words[0]][native_sim_state_fd_50F6_07CA.words[1]] = r;
    r = native_state_RpopT.signed_value & 0x3ff;
    if (r > 250)
        r = 250;
    fd_3D57_0164[native_sim_state_fd_50F6_07CA.words[0]][native_sim_state_fd_50F6_07CA.words[1]] = r;
    for (x = 0; x < 12; x++) {
        for (y = 0; y < 16; y++) {
            if (native_sim_state_fd_50F6_07CA.words[0] == x && native_sim_state_fd_50F6_07CA.words[1] == y)
                continue;
            b = fd_3D57_00A4[x][y];
            r = fd_3D57_0164[x][y];
            if (b == 0 && r == 0)
                continue;
            if (fd_50F6_0EAC == 2)
                if (x < 2 || (x == 3 && y < 5))
                    native_state_fd_50F6_0478.signed_value++;
            patches = o06_35F5_2314(x, y);
            if (b != 0) {
                native_state_fd_50F6_03E2.signed_value++;
                if (patches != 0)
                    b += patches;
                else
                    b++;
                if (b <= 0) {
                    native_state_fd_50F6_0A9E.signed_value++;
                    fd_3D57_00A4[x][y] = 0;
                } else if (b < 250)
                    fd_3D57_00A4[x][y] = b;
                else {
                    fd_3D57_00A4[x][y] = 250;
                    if (SRand1(10) == 0)
                        o06_35F5_2381(x, y, 0);
                }
            }
            if (r != 0) {
                native_state_fd_50F6_0400.signed_value++;
                if (patches != 0)
                    r -= patches;
                else
                    r++;
                if (r <= 0) {
                    native_state_fd_50F6_0AC8.signed_value++;
                    fd_3D57_0164[x][y] = 0;
                    if (x == 11) {
                        y = 8;
                        fd_3D57_0164[SRand1(6) + 2][0] = 20;
                    }
                } else if (r < 250)
                    fd_3D57_0164[x][y] = r;
                else {
                    fd_3D57_0164[x][y] = 250;
                    if (SRand1(10) == 0)
                        o06_35F5_2381(x, y, 1);
                }
            }
        }
    }
    if (fd_3D57_02C0 == 1) {
        native_state_fd_50F6_105C.signed_value++;
        if (native_state_fd_50F6_105C.signed_value > SRand8() + 10) {
            native_state_fd_50F6_105C.signed_value = 0;
            while (native_state_fd_50F6_07C8.signed_value > 0) {
                o06_35F5_2381(native_sim_state_fd_50F6_07CA.words[0], native_sim_state_fd_50F6_07CA.words[1], 0);
                native_state_fd_50F6_07C8.signed_value--;
            }
        }
    }
    native_state_fd_50F6_1066.signed_value++;
    if (native_state_fd_50F6_1066.signed_value > SRand8() + 10) {
        native_state_fd_50F6_1066.signed_value = 0;
        while (native_state_fd_50F6_0850.signed_value > 0) {
            o06_35F5_2381(native_sim_state_fd_50F6_07CA.words[0], native_sim_state_fd_50F6_07CA.words[1], 1);
            native_state_fd_50F6_0850.signed_value--;
        }
    }
    if (fd_50F6_0EAC != 2)
        return;
    if (native_state_fd_50F6_0400.signed_value == 0 && fd_50F6_036E != 0) {
        myBeginSong(0x4e22, 0x7e);
        PictStrnDialog(0, 0x2744, 1);
        if (fd_3D57_0C44 == 0)
            PictStrnDialog(0, 0x2747, 1);
    }
    fd_50F6_0364 = native_state_fd_50F6_03E2.signed_value;
    fd_50F6_036E = native_state_fd_50F6_0400.signed_value;
    if (fd_3D57_0C44 == 0 && native_state_fd_50F6_0478.signed_value > 24) {
        fd_3D57_0C44 = 1;
        fd_3D57_0C48 = 0;
        fd_3D57_0C28 = 0;
        fd_3D57_0C32 = -1;
        myBeginSong(0x4e23, 0x7e);
        PictStrnDialog(0, 0x2746, 1);
        if (native_state_fd_50F6_0400.signed_value != 0)
            PictStrnDialog(0, 0x2745, 1);
    }
    if (fd_3D57_0C44 != 0 && native_state_fd_50F6_0400.signed_value == 0) {
        myBeginSong(0x4e25, 0x7e);
        PictStrnDialog(0, 0x2749, 1);
        native_state_fd_50F6_0376.signed_value = 1;
        native_state_fd_50F6_0366.signed_value = 1;
        DrawSimPayoff();
        return;
    }
    if (native_state_fd_50F6_03E2.signed_value < 2 && native_sim_state_fd_50F6_0AEC.signed_values[5] == 0 && native_sim_state_fd_50F6_0AEC.signed_values[0] == 0 &&
        native_sim_state_fd_50F6_0AEC.signed_values[3] == 0 && native_sim_state_fd_50F6_0AEC.signed_values[4] == 0) {
        native_state_fd_50F6_0376.signed_value = 1;
        native_state_fd_50F6_0366.signed_value = 0;
        PictStrnDialog(0, 0x2748, 1);
    }
}

/* GetNearbyPatches (Win16 unit order) */
int16_t  o06_35F5_2314(int16_t x, int16_t y)
{
    int16_t i, count, px, py;

    count = 0;
    for (i = 0; i < 6; i++) {
        px = PatchX[i] + x;
        py = PatchY[i] + y;
        if (px >= 0 && py >= 0 && px < 12 && py < 16) {
            if (fd_3D57_00A4[px][py] != 0)
                count += 3;
            if (fd_3D57_0164[px][py] != 0)
                count -= 3;
        }
    }
    return count;
}

extern int16_t  SGSRand(int16_t range);

/* grows a colony in a random neighbouring yard cell */
void  o06_35F5_2381(int16_t x, int16_t y, int16_t colony)
{
     int16_t nx;
     int16_t ny;

    nx = SGSRand(4) + x;
    ny = SGSRand(4) + y;
    if (nx < 0)
        nx = 0;
    if (nx > 11)
        nx = 11;
    if (ny < 0)
        ny = 0;
    if (ny > 15)
        ny = 15;
    if (x == nx && y == ny)
        return;
    if (colony != 0) {
        if (fd_3D57_0164[nx][ny] == 0)
            native_state_fd_50F6_0AC4.signed_value++;
        fd_3D57_0164[nx][ny]++;
    } else {
        if (fd_3D57_00A4[nx][ny] == 0)
            native_state_fd_50F6_0A90.signed_value++;
        fd_3D57_00A4[nx][ny]++;
    }
}

extern int16_t  fd_50F6_0402;
extern int16_t  fd_50F6_037A;

/* picks the source colony cell under a yard position */
void  o06_35F5_2433(int16_t x, int16_t y)
{
    fd_50F6_0402 = (y - 0x42) / 10;
    fd_50F6_037A = (x + y - 0xee) / 28;
    if (fd_50F6_037A < 0 || fd_50F6_0402 < 0 || fd_50F6_037A > 11 || fd_50F6_0402 > 15)
        fd_50F6_037A = -1;
    if (fd_3D57_00A4[fd_50F6_037A][fd_50F6_0402] == 0)
        fd_50F6_037A = -1;
}

/* moves half of the source colony to the yard cell under a position */
void  o06_35F5_24CA(int16_t x, int16_t y)
{
    int16_t sum, half;
     int16_t nx;
     int16_t ny;

    if (fd_50F6_037A < 0)
        return;
    ny = (y - 0x42) / 10;
    nx = (x + y - 0xee) / 28;
    if (nx < 0 || ny < 0 || nx > 11 || ny > 15)
        return;
    half = fd_3D57_00A4[fd_50F6_037A][fd_50F6_0402] >> 1;
    fd_3D57_00A4[fd_50F6_037A][fd_50F6_0402] -= half;
    sum = fd_3D57_00A4[nx][ny] + half;
    if (sum < 0xfb)
        fd_3D57_00A4[nx][ny] = sum;
    else
        fd_3D57_00A4[nx][ny] = 0xfa;
}

/* SCAFFOLD BEGIN: unrecovered same-module functions */
/* SCAFFOLD END */

#pragma pack(pop)
