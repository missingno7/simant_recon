/* Overlay section S06, code frame 35F5: back-yard simulation (SimYard unit). */

static char dogA[6] = { 3, 4, -3, -4, 0, 0 };  /* 2448 */
static char dogB[6] = { -3, 0, 3, 0, 0, 0 };  /* 244E */
static char dogC[4] = { 0, 1, 2, 1 };  /* 2454 */
static char dogD[6] = { 0, 3, 6, 9, 100, 102 };  /* 2458 */
static char nodeNext[22] = { 3, 3, 18, 18, 3, 3, 10, 10, 5, 5, 3, 3, 4, 4, 3, 3, 0, 0, 0, 0, 7, 4 };  /* 245E */
static unsigned char n1x[4] = { 4, 5, 4, 3 };  /* 2474 */
static unsigned char n1y[4] = { 135, 141, 147, 153 };  /* 2478 */
static unsigned char n1f[4] = { 60, 60, 60, 60 };  /* 247C */
static unsigned char n2x[4] = { 9, 10, 11, 10 };  /* 2480 */
static unsigned char n2y[4] = { 150, 144, 138, 132 };  /* 2484 */
static unsigned char n2f[4] = { 60, 60, 60, 60 };  /* 2488 */
static unsigned char n3x[20] = { 6, 7, 8, 7, 6, 7, 8, 7, 6, 7, 8, 7, 6, 7, 8, 7, 6, 7, 8, 0 };  /* 248C */
static unsigned char n3y[20] = { 154, 150, 147, 143, 140, 136, 133, 129, 126, 122, 119, 115, 111, 108, 104, 101, 97, 94, 91, 0 };  /* 24A0 */
static unsigned char n3f[20] = { 60, 64, 68, 72, 76, 80, 84, 88, 92, 96, 100, 104, 108, 112, 116, 120, 124, 128, 132, 0 };  /* 24B4 */
static unsigned char n4x[20] = { 0, 1, 2, 1, 0, 1, 2, 1, 0, 1, 2, 1, 0, 1, 2, 1, 0, 1, 2, 0 };  /* 24C8 */
static unsigned char n4y[20] = { 91, 94, 97, 101, 104, 108, 111, 115, 119, 122, 126, 129, 133, 136, 140, 143, 147, 150, 154, 0 };  /* 24DC */
static unsigned char n4f[20] = { 132, 128, 124, 120, 116, 112, 108, 104, 100, 96, 92, 88, 84, 80, 76, 72, 68, 64, 60, 0 };  /* 24F0 */
static unsigned char n5x[4] = { 4, 5, 4, 3 };  /* 2504 */
static unsigned char n5y[4] = { 65, 71, 77, 83 };  /* 2508 */
static unsigned char n5f[4] = { 130, 130, 130, 130 };  /* 250C */
static unsigned char n6x[4] = { 9, 10, 11, 10 };  /* 2510 */
static unsigned char n6y[4] = { 80, 74, 68, 62 };  /* 2514 */
static unsigned char n6f[4] = { 130, 130, 130, 130 };  /* 2518 */
static unsigned char n7x[12] = { 7, 6, 7, 8, 7, 6, 7, 8, 7, 9, 22, 0 };  /* 251C */
static unsigned char n7y[12] = { 84, 80, 76, 72, 68, 64, 60, 56, 52, 46, 44, 0 };  /* 2528 */
static unsigned char n7f[12] = { 134, 138, 142, 146, 150, 154, 158, 162, 166, 166, 166, 0 };  /* 2534 */
static unsigned char n8x[12] = { 22, 3, 0, 1, 2, 1, 0, 1, 2, 1, 0, 0 };  /* 2540 */
static unsigned char n8y[12] = { 44, 46, 52, 56, 60, 64, 69, 73, 78, 82, 86, 0 };  /* 254C */
static unsigned char n8f[12] = { 166, 166, 166, 162, 158, 154, 150, 146, 142, 138, 134, 0 };  /* 2558 */
static unsigned char n9x[6] = { 4, 5, 4, 3, 4, 5 };  /* 2564 */
static unsigned char n9y[6] = { 159, 165, 171, 177, 183, 189 };  /* 256A */
static unsigned char n9f[6] = { 60, 60, 60, 60, 60, 60 };  /* 2570 */
static unsigned char n10x[6] = { 10, 11, 10, 9, 10, 11 };  /* 2576 */
static unsigned char n10y[6] = { 189, 183, 177, 171, 165, 159 };  /* 257C */
static unsigned char n10f[6] = { 60, 60, 60, 60, 60, 60 };  /* 2582 */
static unsigned char n11x[4] = { 0, 1, 2, 1 };  /* 2588 */
static unsigned char n11y[4] = { 164, 168, 172, 176 };  /* 258C */
static unsigned char n11f[4] = { 56, 52, 48, 44 };  /* 2590 */
static unsigned char n12x[4] = { 6, 7, 8, 7 };  /* 2594 */
static unsigned char n12y[4] = { 176, 172, 168, 164 };  /* 2598 */
static unsigned char n12f[4] = { 44, 48, 52, 56 };  /* 259C */
static unsigned char n13x[6] = { 3, 4, 5, 4, 3, 0 };  /* 25A0 */
static unsigned char n13y[6] = { 182, 188, 194, 200, 206, 0 };  /* 25A6 */
static unsigned char n13f[6] = { 44, 44, 44, 44, 44, 0 };  /* 25AC */
static unsigned char n14x[6] = { 9, 10, 11, 10, 9, 0 };  /* 25B2 */
static unsigned char n14y[6] = { 206, 200, 194, 188, 182, 0 };  /* 25B8 */
static unsigned char n14f[6] = { 44, 44, 44, 44, 44, 0 };  /* 25BE */
static unsigned char n15x[4] = { 0, 1, 2, 1 };  /* 25C4 */
static unsigned char n15y[4] = { 196, 200, 204, 208 };  /* 25C8 */
static unsigned char n15f[4] = { 56, 52, 48, 44 };  /* 25CC */
static unsigned char n16x[4] = { 6, 7, 8, 7 };  /* 25D0 */
static unsigned char n16y[4] = { 208, 204, 200, 196 };  /* 25D4 */
static unsigned char n16f[4] = { 44, 48, 52, 56 };  /* 25D8 */
static int n17x[8] = { 6, 7, 8, 900, 901, 902, 6, 7 };  /* 25DC */
static unsigned char n17y[8] = { 192, 189, 186, 172, 172, 172, 174, 175 };  /* 25EC */
static unsigned char n17f[8] = { 60, 64, 68, 73, 73, 73, 93, 99 };  /* 25F4 */
static int n18x[5] = { 0, 903, 900, 1, 2 };  /* 25FC */
static unsigned char n18y[6] = { 172, 172, 172, 186, 189, 0 };  /* 2606 */
static unsigned char n18f[6] = { 93, 73, 73, 68, 64, 0 };  /* 260C */
static unsigned char nodeAlt1[22] = { 10, 30, 6, 1, 3, 31, 32, 5, 14, 2, 33, 1, 34, 33, 34, 20, 0, 0, 0, 0, 38, 14 };  /* 2612 */
static unsigned char nodeAlt2[22] = { 8, 30, 6, 10, 3, 31, 32, 3, 14, 1, 33, 2, 34, 11, 34, 20, 0, 0, 0, 0, 38, 14 };  /* 2628 */
static unsigned char nodeAlt3[22] = { 2, 30, 5, 8, 6, 31, 32, 3, 20, 10, 12, 8, 15, 12, 13, 9, 0, 0, 0, 0, 38, 14 };  /* 263E */
static int outX[9] = { -1, -1, 200, 20, 201, -1, 0, 0, 7 };  /* 2654 */
static unsigned char outY[10] = { 0, 0, 45, 176, 207, 0, 0, 0, 176, 0 };  /* 2666 */
static unsigned char outF[10] = { 0, 0, 166, 44, 47, 0, 0, 0, 104, 0 };  /* 2670 */
static unsigned char outChance[10] = { 40, 40, 35, 8, 8, 6, 0, 0, 10, 0 };  /* 267A */
static unsigned char outNext[10] = { 0, 4, 7, 12, 15, 14, 0, 0, 38, 0 };  /* 2684 */
static char nodeMsg[12] = { 0, 0, 0, 1, 1, 1, 2, 2, 2, 3, 3, 3 };  /* 268E */
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
extern int far fd_50F6_04BE;
extern int far fd_50F6_04C6;
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

/* SCAFFOLD BEGIN: unrecovered same-module functions */
void far SimKidInside(void) {}
void far FootFall(int x, int y) {}
void far o06_35F5_1CEA(int x, int y) {}
void far o06_35F5_11FF(void) {}
void far o06_35F5_14CC(void) {}
void far o06_35F5_1803(void) {}
void far o06_35F5_1E54(void) {}
/* SCAFFOLD END */
