/* Overlay section S06, code frame 35F5: back-yard simulation (SimYard unit). */

static char dogA[6] = { 3, 4, -3, -4, 0, 0 };  /* 2448 */
static char dogB[6] = { -3, 0, 3, 0, 0, 0 };  /* 244E */
static char dogC[4] = { 0, 1, 2, 1 };  /* 2454 */
static char dogD[6] = { 0, 3, 6, 9, 100, 102 };  /* 2458 */
static char nodeLen[22] = { 3, 3, 18, 18, 3, 3, 10, 10, 5, 5, 3, 3, 4, 4, 3, 3, 0, 0, 0, 0, 7, 4 };  /* 245E */
static unsigned char kidF0[4] = { 4, 5, 4, 3 };  /* 2474 */
static unsigned char kidX0[4] = { 135, 141, 147, 153 };  /* 2478 */
static unsigned char kidY0[4] = { 60, 60, 60, 60 };  /* 247C */
static unsigned char kidF1[4] = { 9, 10, 11, 10 };  /* 2480 */
static unsigned char kidX1[4] = { 150, 144, 138, 132 };  /* 2484 */
static unsigned char kidY1[4] = { 60, 60, 60, 60 };  /* 2488 */
static unsigned char kidF2[20] = { 6, 7, 8, 7, 6, 7, 8, 7, 6, 7, 8, 7, 6, 7, 8, 7, 6, 7, 8, 0 };  /* 248C */
static unsigned char kidX2[20] = { 154, 150, 147, 143, 140, 136, 133, 129, 126, 122, 119, 115, 111, 108, 104, 101, 97, 94, 91, 0 };  /* 24A0 */
static unsigned char kidY2[20] = { 60, 64, 68, 72, 76, 80, 84, 88, 92, 96, 100, 104, 108, 112, 116, 120, 124, 128, 132, 0 };  /* 24B4 */
static unsigned char kidF3[20] = { 0, 1, 2, 1, 0, 1, 2, 1, 0, 1, 2, 1, 0, 1, 2, 1, 0, 1, 2, 0 };  /* 24C8 */
static unsigned char kidX3[20] = { 91, 94, 97, 101, 104, 108, 111, 115, 119, 122, 126, 129, 133, 136, 140, 143, 147, 150, 154, 0 };  /* 24DC */
static unsigned char kidY3[20] = { 132, 128, 124, 120, 116, 112, 108, 104, 100, 96, 92, 88, 84, 80, 76, 72, 68, 64, 60, 0 };  /* 24F0 */
static unsigned char kidF4[4] = { 4, 5, 4, 3 };  /* 2504 */
static unsigned char kidX4[4] = { 65, 71, 77, 83 };  /* 2508 */
static unsigned char kidY4[4] = { 130, 130, 130, 130 };  /* 250C */
static unsigned char kidF5[4] = { 9, 10, 11, 10 };  /* 2510 */
static unsigned char kidX5[4] = { 80, 74, 68, 62 };  /* 2514 */
static unsigned char kidY5[4] = { 130, 130, 130, 130 };  /* 2518 */
static unsigned char kidF6[12] = { 7, 6, 7, 8, 7, 6, 7, 8, 7, 9, 22, 0 };  /* 251C */
static unsigned char kidX6[12] = { 84, 80, 76, 72, 68, 64, 60, 56, 52, 46, 44, 0 };  /* 2528 */
static unsigned char kidY6[12] = { 134, 138, 142, 146, 150, 154, 158, 162, 166, 166, 166, 0 };  /* 2534 */
static unsigned char kidF7[12] = { 22, 3, 0, 1, 2, 1, 0, 1, 2, 1, 0, 0 };  /* 2540 */
static unsigned char kidX7[12] = { 44, 46, 52, 56, 60, 64, 69, 73, 78, 82, 86, 0 };  /* 254C */
static unsigned char kidY7[12] = { 166, 166, 166, 162, 158, 154, 150, 146, 142, 138, 134, 0 };  /* 2558 */
static unsigned char kidF8[6] = { 4, 5, 4, 3, 4, 5 };  /* 2564 */
static unsigned char kidX8[6] = { 159, 165, 171, 177, 183, 189 };  /* 256A */
static unsigned char kidY8[6] = { 60, 60, 60, 60, 60, 60 };  /* 2570 */
static unsigned char kidF9[6] = { 10, 11, 10, 9, 10, 11 };  /* 2576 */
static unsigned char kidX9[6] = { 189, 183, 177, 171, 165, 159 };  /* 257C */
static unsigned char kidY9[6] = { 60, 60, 60, 60, 60, 60 };  /* 2582 */
static unsigned char kidF10[4] = { 0, 1, 2, 1 };  /* 2588 */
static unsigned char kidX10[4] = { 164, 168, 172, 176 };  /* 258C */
static unsigned char kidY10[4] = { 56, 52, 48, 44 };  /* 2590 */
static unsigned char kidF11[4] = { 6, 7, 8, 7 };  /* 2594 */
static unsigned char kidX11[4] = { 176, 172, 168, 164 };  /* 2598 */
static unsigned char kidY11[4] = { 44, 48, 52, 56 };  /* 259C */
static unsigned char kidF12[6] = { 3, 4, 5, 4, 3, 0 };  /* 25A0 */
static unsigned char kidX12[6] = { 182, 188, 194, 200, 206, 0 };  /* 25A6 */
static unsigned char kidY12[6] = { 44, 44, 44, 44, 44, 0 };  /* 25AC */
static unsigned char kidF13[6] = { 9, 10, 11, 10, 9, 0 };  /* 25B2 */
static unsigned char kidX13[6] = { 206, 200, 194, 188, 182, 0 };  /* 25B8 */
static unsigned char kidY13[6] = { 44, 44, 44, 44, 44, 0 };  /* 25BE */
static unsigned char kidF14[4] = { 0, 1, 2, 1 };  /* 25C4 */
static unsigned char kidX14[4] = { 196, 200, 204, 208 };  /* 25C8 */
static unsigned char kidY14[4] = { 56, 52, 48, 44 };  /* 25CC */
static unsigned char kidF15[4] = { 6, 7, 8, 7 };  /* 25D0 */
static unsigned char kidX15[4] = { 208, 204, 200, 196 };  /* 25D4 */
static unsigned char kidY15[4] = { 44, 48, 52, 56 };  /* 25D8 */
static int kidF20[8] = { 6, 7, 8, 900, 901, 902, 6, 7 };  /* 25DC */
static unsigned char kidX20[8] = { 192, 189, 186, 172, 172, 172, 174, 175 };  /* 25EC */
static unsigned char kidY20[8] = { 60, 64, 68, 73, 73, 73, 93, 99 };  /* 25F4 */
static int kidF21[5] = { 0, 903, 900, 1, 2 };  /* 25FC */
static unsigned char kidX21[6] = { 172, 172, 172, 186, 189, 0 };  /* 2606 */
static unsigned char kidY21[6] = { 93, 73, 73, 68, 64, 0 };  /* 260C */
static unsigned char nodeNext0[22] = { 10, 30, 6, 1, 3, 31, 32, 5, 14, 2, 33, 1, 34, 33, 34, 20, 0, 0, 0, 0, 38, 14 };  /* 2612 */
static unsigned char nodeNext1[22] = { 8, 30, 6, 10, 3, 31, 32, 3, 14, 1, 33, 2, 34, 11, 34, 20, 0, 0, 0, 0, 38, 14 };  /* 2628 */
static unsigned char nodeNext2[22] = { 2, 30, 5, 8, 6, 31, 32, 3, 20, 10, 12, 8, 15, 12, 13, 9, 0, 0, 0, 0, 38, 14 };  /* 263E */
static int outF[9] = { -1, -1, 200, 20, 201, -1, 0, 0, 7 };  /* 2654 */
static unsigned char outX[10] = { 0, 0, 45, 176, 207, 0, 0, 0, 176, 0 };  /* 2666 */
static unsigned char outY[10] = { 0, 0, 166, 44, 47, 0, 0, 0, 104, 0 };  /* 2670 */
static unsigned char outChance[10] = { 40, 40, 35, 8, 8, 6, 0, 0, 10, 0 };  /* 267A */
static unsigned char outNext[10] = { 0, 4, 7, 12, 15, 14, 0, 0, 38, 0 };  /* 2684 */
static unsigned char frameDir[12] = { 0, 0, 0, 1, 1, 1, 2, 2, 2, 3, 3, 3 };  /* 268E */
static char stepAnim[4] = { 0, 1, 2, 1 };  /* 269A */
static char dirFrame[4] = { 0, 3, 6, 9 };  /* 269E */
static int footDx[4] = { -10, 25, -10, -33 };  /* 26A2 */
static int footDy[4] = { -33, -10, 25, -10 };  /* 26AA */
static char kidDx[4] = { 0, 1, 0, -1 };  /* 26B2 */
static char kidDy[4] = { -1, 0, 1, 0 };  /* 26B6 */
static unsigned char PatchX[6] = { 0, 1, 0, 255, 0, 0 };  /* 26BA */
static unsigned char PatchY[6] = { 255, 0, 1, 0, 0, 0 };  /* 26C0 */


extern long far f_00F8_02BE(void);
extern int far RRand(int range);
extern int far SRand1(int range);
extern void far f_0BE8_063A(void);
extern int far SRand32(void);
void far SimKidInside(void);
void far o06_35F5_02B9(void);
void far o06_35F5_11FF(void);
void far o06_35F5_14CC(void);
void far o06_35F5_1803(void);
void far o06_35F5_020C(void);
void far o06_35F5_1E54(void);
int far o06_35F5_0967(int x, int y);
void far o06_35F5_0A5F(void);
void far FootFall(int x, int y);
void far o06_35F5_1CEA(int x, int y);
int far o06_35F5_0A32(int x, int y);
int far o06_35F5_09F7(int x, int y);
/* Far data in first-use order (a header-like block: extern functions and
 * prototypes first, then the variables; this order decides the operand order of
 * two SimKidOutside comparisons). */
extern long far fd_50F6_109C;
extern int far fd_3D57_0C2C;
extern int far fd_3D57_0C2E;
extern int far fd_3D57_0C34;
extern int far fd_3D57_0C2A;
extern long far fd_50F6_107E;
extern long far fd_50F6_0220;
extern int far fd_50F6_04C6;
extern int far fd_50F6_04BE;
extern int far fd_3D57_0C30;
extern int far fd_50F6_0624;
extern int far fd_50F6_10B0;
extern int far fd_50F6_0246;
extern int far fd_50F6_023E;
extern int far fd_3D57_0C32;
extern int far fd_3D57_0C28;
extern int far fd_3D57_0C40;
extern int far fd_3D57_0C46;
extern int far fd_3D57_0C48;
extern int far fd_50F6_10A0;
extern int far fd_50F6_022C;
extern int far fd_50F6_0244;
extern int far fd_50F6_0254;
extern int far fd_50F6_04E4;
extern int far fd_50F6_0506;
extern int far fd_3D57_0C3E;
extern int far fd_3D57_0C42;
extern int far fd_50F6_03E0;
extern int far fd_50F6_046A;
extern int far fd_50F6_0470;
extern int far fd_50F6_047A;
extern int far fd_50F6_0202;
extern int far fd_50F6_0352;
extern int far fd_50F6_105C;
extern int far fd_50F6_1066;
extern int far fd_50F6_108C;
extern int far fd_50F6_0364;
extern int far fd_50F6_036E;
extern int far fd_50F6_10BC;
extern int far fd_50F6_07C2;
extern int far fd_3D57_0C44;
extern int far fd_50F6_0F24;
extern int far fd_50F6_0B20;
extern int far fd_50F6_0356;
extern int far fd_50F6_0488;
extern int far fd_50F6_0492;
extern int far fd_50F6_0EAC;
extern char far fd_3D57_0C36[4];
extern char far fd_3D57_0C3A[4];
extern int far fd_50F6_07CA[2];
extern unsigned char far fd_3D57_00A4[12][16];
extern int far fd_50F6_0A9E;
extern unsigned char far fd_3D57_0164[12][16];
extern int far fd_50F6_0AC8;
extern int far fd_50F6_0334[12];

/* InitSimYard */
void far o06_35F5_0000(void)
{
    fd_50F6_109C = 0L;          /* BoyMsgCnt */
    fd_3D57_0C2C = 0xb4;        /* BoyX */
    fd_3D57_0C2E = 0x49;        /* BoyY */
    fd_3D57_0C34 = 0xc;         /* BoyTurnCnt */
    fd_3D57_0C2A = 0x14;        /* BoyWait */
    fd_50F6_107E = 0L;          /* BirdDelay */
    fd_50F6_0220 = 0L;          /* CatDelay */
    fd_50F6_04BE = 0xfa;        /* DogX */
    fd_50F6_04C6 = 0x96;        /* DogY */
    fd_3D57_0C30 = 2;           /* BoyDir */
    fd_50F6_0624 = 2;           /* DogTurnCnt */
    fd_50F6_10B0 = 0;           /* BoyMessOn */
    fd_50F6_0246 = 0;           /* BoyPx */
    fd_50F6_023E = 0;           /* BoyPy */
    fd_3D57_0C32 = 0;           /* BoyFrame */
    fd_3D57_0C28 = 0;           /* BoyHere */
    fd_3D57_0C40 = 0;           /* BoyStandCnt */
    fd_3D57_0C46 = 0;           /* NodeCnt */
    fd_3D57_0C48 = 0;           /* NodeNum */
    fd_50F6_10A0 = 0;           /* BirdOn */
    fd_50F6_022C = 0;           /* CatCycle */
    fd_50F6_0244 = 0;           /* CatFrame */
    fd_50F6_0254 = 0;           /* CatOn */
    fd_50F6_04E4 = 0;           /* DogFrame */
    fd_50F6_0506 = 0;           /* DogDir */
    fd_3D57_0C3E = 0;           /* FootHere */
    fd_3D57_0C42 = 0;           /* FootTog */
    fd_50F6_03E0 = 0;           /* FootX */
    fd_50F6_046A = 0;           /* FootY */
    fd_50F6_0470 = 0;           /* MowX */
    fd_50F6_047A = 0;           /* MowY */
    fd_50F6_0202 = 0;           /* BoyIsMowing */
    fd_50F6_0352 = 0;           /* RainOn */
    fd_50F6_105C = 0;           /* SwarmDelayB */
    fd_50F6_1066 = 0;           /* SwarmDelayR */
    fd_50F6_108C = 1;           /* BirdFrame */
    fd_50F6_0364 = 1;           /* LastColonyPopB */
    fd_50F6_036E = 1;           /* LastColonyPopR */
    fd_50F6_10BC = -1;          /* BoyMsgOffset */
    fd_50F6_07C2 = -1;          /* YardCycle */
}



/* DoSimYard */
void far o06_35F5_0173(void)
{
    fd_50F6_07C2++;
    if (fd_50F6_07C2 >= 0x400)
        fd_50F6_07C2 = 0;
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
void far o06_35F5_01CA(int message)
{
    if (message <= 22) {
        fd_50F6_109C = f_00F8_02BE() + 300L;
        fd_50F6_10B0 = 1;
        fd_50F6_10BC = message;
    }
}


/* SimRain */
void far o06_35F5_020C(void)
{
    if (fd_50F6_0F24 != 1) {            /* TERRAINset */
        if (fd_50F6_0352 == 0) {
            if (fd_50F6_0B20 != 0xa8) { /* GlobalKey */
                if (RRand(32) != 0)
                    return;
                if (RRand(128) != 0)
                    return;
            }
            fd_50F6_0352 = 1;
            fd_50F6_0356 = SRand1(150) + 150;   /* RainCnt */
            f_0BE8_063A();                      /* InitWater */
            o06_35F5_01CA(0);
            return;
        }
        if (fd_50F6_0356 > 0)
            fd_50F6_0356--;
        if (fd_50F6_0356 < 1)
            fd_50F6_0352 = 0;
    }
}

/* SimKidOutside: the boy walks and mows the yard; the grass bytes of both
 * colonies under his mower lose a quarter (the second-to-last count goes to
 * fd_50F6_0A9E / fd_50F6_0AC8, Win16 BColoniesKilled / RColoniesKilled). */
void far o06_35F5_02B9(void)
{
    register int v;

    if (fd_3D57_0C3E != 0 && (fd_50F6_07C2 & 3) != 0)
        return;
    if (fd_50F6_0202 != 0) {
        if (fd_50F6_0488 != fd_50F6_0246 || fd_50F6_0492 != fd_50F6_023E)
            fd_3D57_0C30 = o06_35F5_0967(fd_50F6_0246, fd_50F6_023E);
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
            if (fd_50F6_0352 != 0)
                fd_3D57_0C28 = 5;
        }
        break;
    case 2:
        if (fd_50F6_023E < 12)
            fd_3D57_0C30 = 2;
        else if (fd_50F6_023E > 12)
            fd_3D57_0C30 = 0;
        else if (fd_50F6_0246 > 3)
            fd_3D57_0C30 = 3;
        else {
            fd_3D57_0C28 = 3;
            fd_50F6_0488 = 3;
            fd_50F6_0492 = 13;
            fd_50F6_0202 = 1;
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
        fd_50F6_0488 = fd_50F6_0246;
        fd_50F6_0492 = fd_50F6_023E;
        fd_50F6_0202 = 1;
        break;
    case 4:
        if (fd_50F6_023E < 12)
            fd_3D57_0C30 = 2;
        else if (fd_50F6_023E > 12)
            fd_3D57_0C30 = 0;
        else if (fd_50F6_0246 > 3)
            fd_3D57_0C30 = 3;
        else {
            fd_3D57_0C28 = 5;
            fd_50F6_0202 = 0;
        }
        fd_50F6_0488 = fd_50F6_0246;
        fd_50F6_0492 = fd_50F6_023E;
        break;
    case 5:
        if (fd_50F6_023E < 5)
            fd_3D57_0C30 = 2;
        else if (fd_50F6_023E > 5)
            fd_3D57_0C30 = 0;
        else if (fd_50F6_0246 > 3)
            fd_3D57_0C30 = 3;
        else
            fd_3D57_0C28 = 1;
        break;
    }
    fd_3D57_0C32 = dirFrame[fd_3D57_0C30] + stepAnim[fd_50F6_07C2 & 3];
    if (fd_50F6_0202 != 0) {
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
    fd_50F6_0246 = (fd_3D57_0C2C + fd_3D57_0C2E - 200) / 28;
    fd_50F6_023E = (fd_3D57_0C2E - 38) / 10;
    if (fd_50F6_023E < 0)
        fd_50F6_023E = 0;
    if (fd_50F6_023E > 15)
        fd_50F6_023E = 15;
    if (fd_50F6_0246 < 0)
        fd_50F6_0246 = 0;
    if (fd_50F6_0246 > 11)
        fd_50F6_0246 = 11;
    if (fd_50F6_0202 == 0) {
        if (fd_50F6_023E < 1)
            fd_3D57_0C30 = 2;
        else if (fd_50F6_023E > 14)
            fd_3D57_0C30 = 0;
        if (fd_50F6_0246 > 10)
            fd_3D57_0C30 = 3;
        else if (fd_50F6_023E < 5) {
            if (fd_50F6_0246 < 4)
                fd_3D57_0C30 = 1;
        } else if (fd_50F6_0246 < 3) {
            fd_3D57_0C30 = 0;
            if (fd_50F6_023E < 6) {
                if (fd_3D57_0C28 == 3)
                    fd_3D57_0C30 = 1;
                else
                    fd_3D57_0C48 = 21;
            }
        }
    }
    fd_3D57_0C3E = 0;
    fd_3D57_0C42 = !fd_3D57_0C42;
    if (fd_50F6_023E == fd_50F6_07CA[1] && fd_50F6_0246 == fd_50F6_07CA[0]) {
        fd_3D57_0C3E = 1;
        fd_50F6_046A = (fd_3D57_0C2E - 38) % 10;
        fd_50F6_03E0 = (fd_3D57_0C2C + fd_3D57_0C2E - 200) % 28;
        fd_50F6_03E0 = ((fd_50F6_03E0 << 2) + 6) & 0x7f;
        fd_50F6_046A = ((fd_50F6_046A + 1) * 6) & 0x3f;
        fd_50F6_0470 = fd_50F6_03E0 + footDx[fd_3D57_0C30 & 3];
        fd_50F6_047A = fd_50F6_046A + footDy[fd_3D57_0C30 & 3];
        if (fd_3D57_0C30 & 1) {
            if (fd_3D57_0C42 != 0)
                fd_50F6_046A += 6;
            else
                fd_50F6_046A -= 6;
        } else {
            if (fd_3D57_0C42 != 0)
                fd_50F6_03E0 += 6;
            else
                fd_50F6_03E0 -= 6;
        }
        FootFall(fd_50F6_03E0, fd_50F6_046A);
        if (fd_50F6_0202 != 0)
            o06_35F5_1CEA(fd_50F6_0470, fd_50F6_047A);
    } else if (fd_50F6_0202 != 0) {
        if ((v = fd_3D57_00A4[fd_50F6_0246][fd_50F6_023E]) != 0) {
            if ((v -= v >> 2) == 0)
                fd_50F6_0A9E++;
            fd_3D57_00A4[fd_50F6_0246][fd_50F6_023E] = v;
        }
        if ((v = fd_3D57_0164[fd_50F6_0246][fd_50F6_023E]) != 0) {
            if ((v -= v >> 2) == 0)
                fd_50F6_0AC8++;
            fd_3D57_0164[fd_50F6_0246][fd_50F6_023E] = v;
        }
    }
}

/* GetMowDir (Win16 unit order): direction toward an adjacent uncut grass cell */
int far o06_35F5_0967(int x, int y)
{
    int i, ny, nx;

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
    return fd_50F6_07C2 & 3;
}


/* NotMowed (Win16 unit order): cut the grass bit of a yard cell */
int far o06_35F5_09F7(int x, int y)
{
    int bit;

    bit = 1 << y;
    if (fd_50F6_0334[x] & bit) {
        fd_50F6_0334[x] -= bit;
        return 1;
    }
    return 0;
}

/* IsValidYard */
int far o06_35F5_0A32(int x, int y)
{
    if (x >= 0 && y >= 0 && x <= 11 && y <= 15)
        return 1;
    return 0;
}

/* InitGrassMap */
void far o06_35F5_0A5F(void)
{
    int i;

    fd_50F6_0334[0] = 0;
    fd_50F6_0334[1] = 0;
    fd_50F6_0334[2] = 0;
    for (i = 3; i < 12; ++i)
        fd_50F6_0334[i] = -1;
}


/* SCAFFOLD BEGIN: SimKidInside draft.  Under MSC 6.00A (C2 and the bound C2L) it gets C4203
 * (2014 bytes, 0.76 similar).  Under 6.00AX /Oe /Og /Zi (worker big) everything but one global
 * CSE matches: the original keeps (fd_3D57_0C2E - 38) in a temp [bp-24h] from the '/ 10' to the
 * '% 10' across the early returns; here C2 recomputes it (length 1906 vs 1903, frame 2Eh vs 30h).
 * Minimal reproducer: evidence-free mini in build/workers/big/cse3.c (the local CSE of the shared
 * operand into CX blocks the second global CSE; without the (c2c + c2e - 200) CSE it forms).
 * Variable roles follow the original's frame and registers: the else-if index (c48 - 30) is i
 * (DI); the final loop counts with y and draws i (SI) and x (DI). */
extern int far fd_3D57_07C8;
extern int far fd_50F6_035C;
extern int far fd_50F6_0350;
extern int far fd_50F6_0330;
extern unsigned char far fd_3E1D_6180[128][64];
extern int far fd_50F6_0F18;
extern unsigned char far fd_3E1D_AD3B[];
extern int far fd_50F6_0F12;
extern int far fd_50F6_0F34;
extern int far fd_50F6_048C;
extern void far f_00DF_00E8(int sound, int a, int b);
extern int far SRand128(void);
extern int far SRand64(void);
extern int far SRand4(void);
extern int far f_0EC1_0291(int x, int y);
extern void far DeadAntHere(int x, int y, int flag);
extern void far f_0CDB_0DE0(void);
extern void far o22_39C7_0D21(int a);

/* SimKidInside: the boy's walk through the house, node by node */
void far SimKidInside(void)
{
    int x, y, frame;
    int i;

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
    if (fd_3D57_07C8 == 0 && fd_50F6_035C < 2) {
        if ((fd_3D57_0C46 == 3 && fd_3D57_0C48 == 20 && fd_3D57_0C32 == 900) ||
            (fd_3D57_0C46 == 1 && fd_3D57_0C48 == 21 && fd_3D57_0C32 == 903) ||
            (fd_3D57_0C46 == 6 && fd_3D57_0C48 == 20 && fd_3D57_0C32 == 6) ||
            (fd_3D57_0C46 == 3 && fd_3D57_0C48 == 21 && fd_3D57_0C32 == 1))
            f_00DF_00E8(0x18, 0, 0);
    }
    fd_50F6_0246 = (fd_3D57_0C2C + fd_3D57_0C2E - 200) / 28;
    fd_3D57_0C3E = 0;
    fd_3D57_0C42 = !fd_3D57_0C42;
    i = (fd_50F6_07CA[0] << 4) + fd_50F6_07CA[1];
    fd_50F6_023E = (fd_3D57_0C2E - 38) / 10;
    if (fd_50F6_023E != fd_50F6_07CA[1] || fd_50F6_07CA[0] != fd_50F6_0246)
        return;
    if (i == 0 || i == 1 || i == 16 || i == 32)
        return;
    if (fd_3D57_0C32 >= 0 && fd_3D57_0C32 < 12)
        fd_3D57_0C30 = frameDir[fd_3D57_0C32];
    else
        fd_3D57_0C30 = 2;
    fd_3D57_0C3E = 1;
    fd_50F6_046A = (fd_3D57_0C2E - 38) % 10;
    fd_50F6_03E0 = (fd_3D57_0C2C + fd_3D57_0C2E - 200) % 28;
    fd_50F6_03E0 = ((fd_50F6_03E0 << 2) + 6) & 0x7f;
    fd_50F6_046A = ((fd_50F6_046A + 1) * 6) & 0x3f;
    if (fd_3D57_0C30 & 1) {
        if (fd_3D57_0C42 != 0)
            fd_50F6_046A += 6;
        else
            fd_50F6_046A -= 6;
    } else {
        if (fd_3D57_0C42 != 0)
            fd_50F6_03E0 += 6;
        else
            fd_50F6_03E0 -= 6;
    }
    FootFall(fd_50F6_03E0, fd_50F6_046A);
    f_00DF_00E8(9, 0, 0x7e);
    for (y = 0; y < (fd_50F6_0330 + fd_50F6_0350) << 3; y++) {
        i = SRand128();
        x = SRand64();
        if (fd_3E1D_6180[i][x] != 0) {
            fd_50F6_0F18 = f_0EC1_0291(i, x);
            if (fd_50F6_0F18 >= 0) {
                DeadAntHere(i, x, fd_3E1D_AD3B[fd_50F6_0F18] & 0x80);
                fd_3E1D_6180[i][x] = fd_3E1D_AD3B[fd_50F6_0F18] = 0;
            }
        }
        if ((fd_50F6_0F12 >> 4) == i && (fd_50F6_0F34 >> 4) == x)
            f_0CDB_0DE0();
    }
    if (fd_50F6_0EAC == 2 && fd_50F6_048C == 1 && SRand4() == 0)
        o22_39C7_0D21(9);
}
/* SCAFFOLD END */

extern int far fd_50F6_10AC;
extern int far fd_50F6_0210;
extern int far fd_50F6_10BA;
extern int far fd_50F6_0208;
extern int far fd_50F6_06AA;
extern int far fd_50F6_07C8;
extern int far fd_50F6_073A;
extern int far fd_50F6_0850;
extern void far f_00F8_0395(void);
extern int far SRand2(void);
extern long far fd_50F6_383A;

/* SimBird (Win16 pair MEDIUM, unit order): the bird flies over the yard and eats swarms */
void far o06_35F5_11FF(void)
{
    int d;
    int step;
    int oldY;
    int soundValue;
    long now;

    if (fd_50F6_10A0 != 0) {
        if (fd_50F6_10A0 == 1)
            fd_50F6_10AC += 0x10;
        else
            fd_50F6_10AC += 8;
        if (fd_50F6_10A0 == 1) {
            d = fd_50F6_0210 - fd_50F6_10BA;
            if (d != 0) {
                if (((d >= 0) ? d : -d) >= 4)
                    fd_50F6_10BA += d > 0 ? 4 : -4;
                else
                    fd_50F6_10BA += d > 0 ? 1 : -1;
            }
        } else
            fd_50F6_10BA -= 8;
        fd_50F6_108C = (fd_50F6_108C + 1) & 1;
        if (fd_50F6_10AC < 0 || fd_50F6_10AC > 0x1ff || fd_50F6_10BA < 0 || fd_50F6_10BA > 0xff) {
            fd_50F6_10A0 = 0;
            fd_50F6_107E = fd_50F6_383A + 30L;
            return;
        }
        if (fd_50F6_10A0 != 1)
            return;
        if (fd_50F6_10AC < fd_50F6_0208 || fd_50F6_10BA < fd_50F6_0210 - 4 ||
            fd_50F6_10BA > fd_50F6_0210 + 4)
            return;
        if (fd_50F6_06AA > 0)
            fd_50F6_06AA -= (fd_50F6_06AA + 7) >> 3;
        if (fd_50F6_07C8 > 0) {
            fd_50F6_07C8 -= (fd_50F6_07C8 + 7) >> 3;
            f_00F8_0395();
        }
        if (fd_50F6_073A > 0)
            fd_50F6_073A -= (fd_50F6_073A + 7) >> 3;
        if (fd_50F6_0850 > 0)
            fd_50F6_0850 -= (fd_50F6_0850 + 7) >> 3;
        if (fd_3D57_07C8 == 0 && fd_50F6_035C < 2) {
            if (SRand2() == 0)
                f_00DF_00E8(7, 0, 6);
        }
        fd_50F6_10A0 = 2;
    } else if (fd_50F6_383A > fd_50F6_107E) {
        fd_50F6_107E = fd_50F6_383A + 20L;
        if (fd_50F6_07CA[0] >= 5 && SRand2() == 0 &&
            (fd_50F6_06AA > 0 || fd_50F6_073A > 0)) {
            fd_50F6_0208 = fd_50F6_07CA[0] * 0x1c - fd_50F6_07CA[1] * 10 + 0xb2;
            fd_50F6_0210 = fd_50F6_07CA[1] * 10 + 0x2e;
            fd_50F6_10A0 = 1;
            fd_50F6_10AC = 0;
            fd_50F6_10BA = SRand64() + 4;
            fd_50F6_108C = 0;
        }
    }
}

extern int far fd_50F6_0240;
extern char far fd_3D57_0000[];
extern int far fd_50F6_02BE;
extern int far fd_50F6_032C;
extern char far fd_3D57_0008[];
extern int far fd_50F6_0506;
extern int far SRand16(void);
extern unsigned long far f_0BE8_0B83(int x1, int y1, int x2, int y2);

/* SimCat (Win16 pair MEDIUM, unit order) */
void far o06_35F5_14CC(void)
{
    register int newX;
    register int newY;

    if (fd_50F6_0254 != 0) {
        fd_50F6_022C = (fd_50F6_022C + 1) & 0xfff;
        if (fd_50F6_0254 == 1) {
            newX = fd_50F6_02BE + fd_3D57_0000[fd_50F6_0240] * 4;
            newY = fd_50F6_032C + fd_3D57_0008[fd_50F6_0240] * 4;
            if (SRand16() != 0 && newX >= 0xfc && newX <= 0x1ef) {
                fd_50F6_02BE = newX;
                fd_50F6_032C = newY;
                fd_50F6_0244++;
                if (fd_50F6_0240 == 2) {
                    if (fd_50F6_0244 >= 3)
                        fd_50F6_0244 = 1;
                } else {
                    if (fd_50F6_0244 >= 6)
                        fd_50F6_0244 = 4;
                }
            } else if (fd_50F6_0240 == 2) {
                fd_50F6_0240 = 6;
                fd_50F6_0244 = 4;
            } else {
                fd_50F6_0240 = 2;
                fd_50F6_0244 = 1;
            }
            if (fd_3D57_07C8 == 0 && fd_50F6_035C < 2 && SRand64() == 0) {
                f_00DF_00E8(0xd, 0, 5);
                return;
            }
            if (SRand16() == 0 && fd_50F6_022C > 100 && fd_50F6_0506 == 2 && fd_3D57_0C28 == 0) {
                fd_50F6_0254 = 2;
                fd_50F6_022C = 0;
                fd_50F6_0244 = 10;
                return;
            }
            if (fd_50F6_022C > 50) {
                if (f_0BE8_0B83(fd_50F6_02BE, fd_50F6_032C, fd_50F6_04BE, fd_50F6_04C6) <= 0x960) {
                    fd_50F6_0254 = 3;
                    fd_50F6_0244 = 20;
                    if (fd_3D57_07C8 == 0 && fd_50F6_035C < 2)
                        f_00DF_00E8(0xe, 0, 5);
                }
            }
        } else if (fd_50F6_0254 == 2) {
            if (++fd_50F6_0244 >= 13)
                fd_50F6_0244 = 11;
            if (++fd_50F6_022C > 30) {
                fd_50F6_022C = 0;
                fd_50F6_0254 = 1;
                fd_50F6_0244 = (fd_50F6_0240 == 2) ? 0 : 3;
            }
        } else {
            if (++fd_50F6_0244 >= 30) {
                fd_50F6_0244 = 0;
                fd_50F6_0254 = 0;
                fd_50F6_0220 = f_00F8_02BE() + 600L;
            }
        }
    } else if (f_00F8_02BE() > fd_50F6_0220) {
        fd_50F6_0220 = f_00F8_02BE() + 200L;
        if (SRand16() == 0 || fd_50F6_0B20 == 0x8d) {
            fd_50F6_0254 = 1;
            fd_50F6_02BE = 0xfc;
            fd_50F6_032C = 0x19;
            fd_50F6_0240 = 2;
            fd_50F6_0244 = 0;
            fd_50F6_022C = 0;
        }
    }
}

extern long far fd_50F6_0736;
extern int far fd_50F6_059E;
extern int far fd_50F6_0510;
int far o06_35F5_1A0F(void);
int far o06_35F5_1ABF(void);
void far o06_35F5_1B08(int kind, int level);

/* SimDog (Win16 unit order) */
void far o06_35F5_1803(void)
{
    if (--fd_50F6_0624 < 0) {
        if (fd_50F6_0254 != 0)
            fd_50F6_0506 = o06_35F5_1ABF();
        else if (fd_3D57_0C48 < 0x26)
            fd_50F6_0506 = (SRand1(3) + fd_50F6_0506 - 1) & 3;
        else
            fd_50F6_0506 = o06_35F5_1A0F();
        fd_50F6_0624 = 4;
    }
    if (fd_50F6_0506 == 1 && SRand1(10) == 0) {
        fd_50F6_0506 = SRand2() + 4;
        fd_50F6_0624 = 6;
    }
    if (fd_50F6_0506 > 3)
        fd_50F6_04E4 = dogD[fd_50F6_0506] + (fd_50F6_07C2 & 1);
    else
        fd_50F6_04E4 = dogD[fd_50F6_0506] + dogC[fd_50F6_07C2 & 3];
    fd_50F6_04C6 += dogB[fd_50F6_0506];
    fd_50F6_059E = (fd_50F6_04C6 - 38) / 10;
    fd_50F6_04BE += dogA[fd_50F6_0506];
    fd_50F6_0510 = (fd_50F6_04BE + fd_50F6_04C6 - 200) / 28;
    if (fd_50F6_059E < 0)
        fd_50F6_059E = 0;
    if (fd_50F6_059E > 15)
        fd_50F6_059E = 15;
    if (fd_50F6_0510 < 0)
        fd_50F6_0510 = 0;
    if (fd_50F6_0510 > 11)
        fd_50F6_0510 = 11;
    if (fd_50F6_059E < 1)
        fd_50F6_0506 = 2;
    else if (fd_50F6_059E > 14)
        fd_50F6_0506 = 0;
    if (fd_50F6_0510 > 10)
        fd_50F6_0506 = 3;
    else if (fd_50F6_0510 < 4)
        fd_50F6_0506 = 1;
    if (fd_50F6_04E4 >= 100 && fd_50F6_04E4 <= 103 && SRand1(6) == 0)
        o06_35F5_1B08(SRand4(), 5);
}

/* FollowBoyDir (Win16 unit order): dog direction toward the boy */
int far o06_35F5_1A0F(void)
{
    register int dy;
    int dx;
    register int ady;
    int adx;

    dy = fd_50F6_059E - fd_50F6_023E;
    dx = fd_50F6_0510 - fd_50F6_0246;
    if (dx < 0)
        adx = -dx;
    else
        adx = dx;
    if (dy < 0)
        ady = -dy;
    else
        ady = dy;
    if (adx < 1 && ady < 1 && fd_50F6_0202 != 0)
        o06_35F5_1B08(1, 0x7f);
    if (adx < 2 && ady < 2)
        return fd_50F6_07C2 & 3;
    if (dy < 0)
        return 2;
    if (dy > 1)
        return 0;
    if (dx < 0)
        return 1;
    if (dx > 1)
        return 3;
    return fd_50F6_07C2 & 3;
}

/* FollowCatDir (Win16 unit order) */
int far o06_35F5_1ABF(void)
{
    if (fd_50F6_0510 < 5)
        return 1;
    if (fd_50F6_0510 > 8)
        return 3;
    if (fd_50F6_059E > 0)
        return 0;
    return fd_50F6_07C2 & 3;
}

/* MakeBark (Win16 unit order) */
void far o06_35F5_1B08(int kind, int level)
{
    if (fd_3D57_07C8 == 0 && fd_50F6_035C < 2 && f_00F8_02BE() > fd_50F6_0736) {
        switch (kind) {
        case 0:
        case 2:
            f_00DF_00E8(0x17, 0, level);
            break;
        case 1:
            f_00DF_00E8(0x15, 0, level);
            break;
        case 3:
            f_00DF_00E8(0x16, 0, level);
            break;
        }
        fd_50F6_0736 = f_00F8_02BE() + SRand1(30) + 60;
    }
}

extern int far f_10F7_003A(int a);
extern int far fd_50F6_0F42;
extern int far fd_50F6_0F7E;
extern int far fd_50F6_0A06;

/* FootFall: the boy's foot squashes ants under it */
void far FootFall(int x, int y)
{
    int i, j, a, x2, y2;

    f_00DF_00E8(0x23, 0, 0x14);
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
                if ((a = fd_3E1D_6180[i][j]) != 0) {
                    if (f_10F7_003A(a) == 0) {
                        a = f_0EC1_0291(i, j);
                        if (a >= 0) {
                            DeadAntHere(i, j, fd_3E1D_AD3B[a] & 0x80);
                            fd_3E1D_AD3B[a] = 0;
                        }
                    } else
                        o22_39C7_0D21(5);
                }
            }
        }
    }
    if (fd_50F6_0F42 >= x && fd_50F6_0F42 < x2 && fd_50F6_0F7E >= y && fd_50F6_0F7E < y2) {
        f_0CDB_0DE0();
        if (fd_50F6_0A06 == 1)
            o22_39C7_0D21(5);
    }
}

extern int far fd_50F6_0D6A;
extern unsigned char far fd_3E1D_A180[];
extern unsigned char far fd_3E1D_A569[];
extern int far fd_50F6_0F0C;

/* MowerFall (Win16 unit order): the mower kills ants in the yard */
void far o06_35F5_1CEA(int x, int y)
{
    register int i;

    if (fd_50F6_0EAC == 0)
        return;
    i = fd_50F6_0D6A;
    while (i > 0) {
        i--;
        if (fd_3E1D_AD3B[i] != 0 && SRand4() != 0) {
            fd_3E1D_AD3B[i] = fd_3E1D_6180[fd_3E1D_A180[i]][fd_3E1D_A569[i]] = 0;
        }
    }
    if (fd_50F6_0F0C != 0 && SRand4() != 0)
        f_0CDB_0DE0();
    if (fd_50F6_0A06 <= 1 && fd_50F6_048C == 1 && SRand4() != 0)
        o22_39C7_0D21(6);
}

/* MaintainSwarm (Win16 unit order) */
void far o06_35F5_1D9D(void)
{
    register int n;

    n = fd_50F6_06AA;
    if (n > 0) {
        if (n >= 4)
            n = fd_50F6_06AA - (fd_50F6_06AA >> 2);
        else
            n = fd_50F6_06AA - 1;
    }
    if (fd_50F6_07C8 > n)
        n = fd_50F6_07C8;
    if (n > 50)
        n = 50;
    fd_50F6_06AA = n;

    n = fd_50F6_073A;
    if (n > 0) {
        if (n >= 4)
            n = fd_50F6_073A - (fd_50F6_073A >> 2);
        else
            n = fd_50F6_073A - 1;
    }
    if (fd_50F6_0850 > n)
        n = fd_50F6_0850;
    if (n > 50)
        n = 50;
    fd_50F6_073A = n;
}

extern int far fd_3D57_0C20;
extern int far fd_50F6_03E2;
extern int far fd_50F6_0400;
extern int far fd_50F6_0478;
extern int far fd_3D57_02C0;
extern int far fd_50F6_0376;
extern int far fd_50F6_0366;
extern int far fd_50F6_0AEC[6];
extern int far SRand8(void);
extern void far f_00DF_00B1(int id, int arg);
extern void far o14_384C_0B6A(int a, int b, int c);
extern void far o16_384C_0000(void);
int far o06_35F5_2314(int x, int y);
void far o06_35F5_2381(int x, int y, int colony);

/* SimColonies (Win16 unit order): yard colony growth, swarms and the for-sale scenario */
void far o06_35F5_1E54(void)
{
    int patches, b, y, r;
    int x;
    register int n;

    if (fd_50F6_07C2 & 0x1f)
        return;
    fd_3D57_0C20 = 1;
    o06_35F5_1D9D();
    fd_50F6_03E2 = 0;
    fd_50F6_0400 = 0;
    fd_50F6_0478 = 0;
    if (fd_50F6_0330 > 0)
        fd_50F6_03E2 = 1;
    if (fd_50F6_0350 > 0)
        fd_50F6_0400 = 1;
    n = fd_50F6_0330 & 0x3ff;
    if (n > 250)
        n = 250;
    fd_3D57_00A4[fd_50F6_07CA[0]][fd_50F6_07CA[1]] = n;
    n = fd_50F6_0350 & 0x3ff;
    if (n > 250)
        n = 250;
    fd_3D57_0164[fd_50F6_07CA[0]][fd_50F6_07CA[1]] = n;
    for (x = 0; x < 12; x++) {
        for (y = 0; y < 16; y++) {
            if (fd_50F6_07CA[0] == x && fd_50F6_07CA[1] == y)
                continue;
            r = fd_3D57_0164[x][y];
            b = fd_3D57_00A4[x][y];
            if (b == 0 && r == 0)
                continue;
            if (fd_50F6_0EAC == 2 && (x < 2 || (x == 3 && y < 5)))
                fd_50F6_0478++;
            patches = o06_35F5_2314(x, y);
            if (b != 0) {
                fd_50F6_03E2++;
                if (patches != 0)
                    b += patches;
                else
                    b++;
                if (b <= 0) {
                    fd_50F6_0A9E++;
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
                fd_50F6_0400++;
                if (patches != 0)
                    r -= patches;
                else
                    r++;
                if (r <= 0) {
                    fd_50F6_0AC8++;
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
        fd_50F6_105C++;
        if (fd_50F6_105C > SRand8() + 10) {
            fd_50F6_105C = 0;
            while (fd_50F6_07C8 > 0) {
                o06_35F5_2381(fd_50F6_07CA[0], fd_50F6_07CA[1], 0);
                fd_50F6_07C8--;
            }
        }
    }
    fd_50F6_1066++;
    if (fd_50F6_1066 > SRand8() + 10) {
        fd_50F6_1066 = 0;
        while (fd_50F6_0850 > 0) {
            o06_35F5_2381(fd_50F6_07CA[0], fd_50F6_07CA[1], 1);
            fd_50F6_0850--;
        }
    }
    if (fd_50F6_0EAC != 2)
        return;
    if (fd_50F6_0400 == 0 && fd_50F6_036E != 0) {
        f_00DF_00B1(0x4e22, 0x7e);
        o14_384C_0B6A(0, 0x2744, 1);
        if (fd_3D57_0C44 == 0)
            o14_384C_0B6A(0, 0x2747, 1);
    }
    fd_50F6_0364 = fd_50F6_03E2;
    fd_50F6_036E = fd_50F6_0400;
    if (fd_3D57_0C44 == 0 && fd_50F6_0478 > 24) {
        fd_3D57_0C44 = 1;
        fd_3D57_0C48 = 0;
        fd_3D57_0C28 = 0;
        fd_3D57_0C32 = -1;
        f_00DF_00B1(0x4e23, 0x7e);
        o14_384C_0B6A(0, 0x2746, 1);
        if (fd_50F6_0400 != 0)
            o14_384C_0B6A(0, 0x2745, 1);
    }
    if (fd_3D57_0C44 != 0 && fd_50F6_0400 == 0) {
        f_00DF_00B1(0x4e25, 0x7e);
        o14_384C_0B6A(0, 0x2749, 1);
        fd_50F6_0376 = 1;
        fd_50F6_0366 = 1;
        o16_384C_0000();
        return;
    }
    if (fd_50F6_03E2 < 2 && fd_50F6_0AEC[5] == 0 && fd_50F6_0AEC[0] == 0 &&
        fd_50F6_0AEC[3] == 0 && fd_50F6_0AEC[4] == 0) {
        fd_50F6_0376 = 1;
        fd_50F6_0366 = 0;
        o14_384C_0B6A(0, 0x2748, 1);
    }
}

/* GetNearbyPatches (Win16 unit order) */
int far o06_35F5_2314(int x, int y)
{
    int index;
    int count;
    int offset;
    register int patchY;

    count = 0;
    for (index = 0; index < 6; ++index) {
        patchY = PatchY[index] + y;
        if ((PatchX[index] + x) >= 0 && patchY >= 0 && (PatchX[index] + x) < 12 && patchY < 16) {
            offset = ((PatchX[index] + x) << 4) + patchY;
            if (fd_3D57_00A4[0][offset] != 0)
                count += 3;
            if (fd_3D57_0164[0][offset] != 0)
                count -= 3;
        }
    }
    return count;
}

extern int far f_0093_0054(int range);
extern int far fd_50F6_0AC4;
extern int far fd_50F6_0A90;

/* grows a colony in a random neighbouring yard cell */
void far o06_35F5_2381(int x, int y, int colony)
{
    register int nx;
    register int ny;

    nx = f_0093_0054(4) + x;
    ny = f_0093_0054(4) + y;
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
            fd_50F6_0AC4++;
        fd_3D57_0164[nx][ny]++;
    } else {
        if (fd_3D57_00A4[nx][ny] == 0)
            fd_50F6_0A90++;
        fd_3D57_00A4[nx][ny]++;
    }
}

extern int far fd_50F6_0402;
extern int far fd_50F6_037A;

/* picks the source colony cell under a yard position */
void far o06_35F5_2433(int x, int y)
{
    fd_50F6_0402 = (y - 0x42) / 10;
    fd_50F6_037A = (x + y - 0xee) / 28;
    if (fd_50F6_037A < 0 || fd_50F6_0402 < 0 || fd_50F6_037A > 11 || fd_50F6_0402 > 15)
        fd_50F6_037A = -1;
    if (fd_3D57_00A4[fd_50F6_037A][fd_50F6_0402] == 0)
        fd_50F6_037A = -1;
}

/* moves half of the source colony to the yard cell under a position */
void far o06_35F5_24CA(int x, int y)
{
    int sum, half;
    register int nx;
    register int ny;

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
