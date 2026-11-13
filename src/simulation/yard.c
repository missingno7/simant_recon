/*
 * Runs the back yard simulation, including the boy, bird, cat, dog, mower and rain. It also
 * advances yard colonies and swarms.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS: overlay section 6 (S06); segment 35F5; complete original translation unit.
 * Windows: SIMTWO, from recorded function pairs in the Windows symbol inventory.
 *
 * Line layout (inferred, not recovered): /Zi starts a new object record every 52 line
 * entries, and the original relocation order fixes where those breaks fall.  This layout
 * satisfies all order constraints of the file and is not unique.  It differs from the
 * usual spelling in white space only: every "else if" has the "if" on its own line, the
 * four dog position clamps of SimDog and the single-statement tests of FollowBoyDir and
 * FollowCatDir are written on one line, and SimColonies tests CurGameType in a nested if.
 */

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


extern long far MacTickCount(void);
extern int far RRand(int range);
extern int far SRand1(int range);
extern void far f_0BE8_063A(void);
extern int far SRand32(void);
void far SimKidInside(void);
void far SimKidOutside(void);
void far SimBird(void);
void far SimCat(void);
void far SimDog(void);
void far SimRain(void);
void far SimColonies(void);
int far GetMowDir(int x, int y);
void far InitGrassMap(void);
void far FootFall(int x, int y);
void far MowerFall(int x, int y);
int far IsValidYard(int x, int y);
int far NotMowed(int x, int y);
/* Far data in first-use order (a header-like block: extern functions and
 * prototypes first, then the variables; this order decides the operand order of
 * two SimKidOutside comparisons). */
extern long far BoyMsgCnt;
extern int far BoyX;
extern int far BoyY;
extern int far BoyTurnCnt;
extern int far BoyWait;
extern long far BirdDelay;
extern long far CatDelay;
extern int far DogY;
extern int far DogX;
extern int far BoyDir;
extern int far DogTurnCnt;
extern int far BoyMessOn;
extern int far BoyPx;
extern int far BoyPy;
extern int far BoyFrame;
extern int far BoyHere;
extern int far BoyStandCnt;
extern int far NodeCnt;
extern int far NodeNum;
extern int far BirdOn;
extern int far CatCycle;
extern int far CatFrame;
extern int far CatOn;
extern int far DogFrame;
extern int far DogDir;
extern int far FootHere;
extern int far FootTog;
extern int far FootX;
extern int far FootY;
extern int far MowX;
extern int far MowY;
extern int far BoyIsMowing;
extern int far RainOn;
extern int far SwarmDelayB;
extern int far SwarmDelayR;
extern int far BirdFrame;
extern int far LastColonyPopB;
extern int far LastColonyPopR;
extern int far BoyMsgOffset;
extern int far YardCycle;
extern int far ForSaleState;
extern int far fd_50F6_0F24;
extern int far GlobalKey;
extern int far RainCnt;
extern int far LastMowX;
extern int far LastMowY;
extern int far CurGameType;
extern char far BxTab[4];
extern char far ByTab[4];
extern int far CurYardPnt[2];
extern unsigned char far YMapPopB[12][16];
extern int far BColoniesKilled;
extern unsigned char far YMapPopR[12][16];
extern int far RColoniesKilled;
extern int far GrassMap[12];

/* InitSimYard */
void far InitSimYard(void)
{
    BoyMsgCnt = 0L;          /* BoyMsgCnt */
    BoyX = 0xb4;        /* BoyX */
    BoyY = 0x49;        /* BoyY */
    BoyTurnCnt = 0xc;         /* BoyTurnCnt */
    BoyWait = 0x14;        /* BoyWait */
    BirdDelay = 0L;          /* BirdDelay */
    CatDelay = 0L;          /* CatDelay */
    DogX = 0xfa;        /* DogX */
    DogY = 0x96;        /* DogY */
    BoyDir = 2;           /* BoyDir */
    DogTurnCnt = 2;           /* DogTurnCnt */
    BoyMessOn = 0;           /* BoyMessOn */
    BoyPx = 0;           /* BoyPx */
    BoyPy = 0;           /* BoyPy */
    BoyFrame = 0;           /* BoyFrame */
    BoyHere = 0;           /* BoyHere */
    BoyStandCnt = 0;           /* BoyStandCnt */
    NodeCnt = 0;           /* NodeCnt */
    NodeNum = 0;           /* NodeNum */
    BirdOn = 0;           /* BirdOn */
    CatCycle = 0;           /* CatCycle */
    CatFrame = 0;           /* CatFrame */
    CatOn = 0;           /* CatOn */
    DogFrame = 0;           /* DogFrame */
    DogDir = 0;           /* DogDir */
    FootHere = 0;           /* FootHere */
    FootTog = 0;           /* FootTog */
    FootX = 0;           /* FootX */
    FootY = 0;           /* FootY */
    MowX = 0;           /* MowX */
    MowY = 0;           /* MowY */
    BoyIsMowing = 0;           /* BoyIsMowing */
    RainOn = 0;           /* RainOn */
    SwarmDelayB = 0;           /* SwarmDelayB */
    SwarmDelayR = 0;           /* SwarmDelayR */
    BirdFrame = 1;           /* BirdFrame */
    LastColonyPopB = 1;           /* LastColonyPopB */
    LastColonyPopR = 1;           /* LastColonyPopR */
    BoyMsgOffset = -1;          /* BoyMsgOffset */
    YardCycle = -1;          /* YardCycle */
}



/* DoSimYard */
void far DoSimYard(void)
{
    YardCycle++;
    if (YardCycle >= 0x400)
        YardCycle = 0;
    if (NodeNum < 0x26)
        SimKidInside();
    else
        SimKidOutside();
    SimBird();
    SimCat();
    if (ForSaleState == 0)      /* ForSaleState */
        SimDog();
    SimRain();
    SimColonies();
}


/* SendBoyMsg */
void far SendBoyMsg(int message)
{
    if (message <= 22) {
        BoyMsgCnt = MacTickCount() + 300L;
        BoyMessOn = 1;
        BoyMsgOffset = message;
    }
}


/* SimRain */
void far SimRain(void)
{
    if (fd_50F6_0F24 != 1) {            /* TERRAINset */
        if (RainOn == 0) {
            if (GlobalKey != 0xa8) { /* GlobalKey */
                if (RRand(32) != 0)
                    return;
                if (RRand(128) != 0)
                    return;
            }
            RainOn = 1;
            RainCnt = SRand1(150) + 150;   /* RainCnt */
            f_0BE8_063A();                      /* InitWater */
            SendBoyMsg(0);
            return;
        }
        if (RainCnt > 0)
            RainCnt--;
        if (RainCnt < 1)
            RainOn = 0;
    }
}

/* SimKidOutside: the boy walks and mows the yard; the grass bytes of both
 * colonies under his mower lose a quarter (the second-to-last count goes to
 * BColoniesKilled / RColoniesKilled, Win16 BColoniesKilled / RColoniesKilled). */
void far SimKidOutside(void)
{
    register int v;

    if (FootHere != 0 && (YardCycle & 3) != 0)
        return;
    if (BoyIsMowing != 0) {
        if (LastMowX != BoyPx || LastMowY != BoyPy)
            BoyDir = GetMowDir(BoyPx, BoyPy);
    } else
        if (--BoyTurnCnt < 0) {
            BoyDir = (SRand1(3) + BoyDir - 1) & 3;
            BoyTurnCnt = 4;
        }
    switch (BoyHere) {
    case 1:
        if (SRand1(900) == 0) {
            SendBoyMsg(1);
            BoyHere = 2;
        } else
            if (SRand1(600) == 0 || CurGameType == 3 || CurGameType == 0) {
                SendBoyMsg(2);
                BoyHere = 5;
            } else {
                if (SRand1(200) == 0)
                    SendBoyMsg(SRand1(8) + 7);
                if (RainOn != 0)
                    BoyHere = 5;
            }
        break;
    case 2:
        if (BoyPy < 12)
            BoyDir = 2;
        else
            if (BoyPy > 12)
                BoyDir = 0;
            else
                if (BoyPx > 3)
                    BoyDir = 3;
                else {
                    BoyHere = 3;
                    LastMowX = 3;
                    LastMowY = 13;
                    BoyIsMowing = 1;
                    InitGrassMap();
                    BoyDir = 2;
                    BoyX = 0x7d;
                    BoyY = 0xaa;
                }
        break;
    case 3:
        if (SRand1(100) == 0)
            SendBoyMsg(SRand1(3) + 3);
        if (SRand1(200) == 0) {
            SendBoyMsg(6);
            BoyHere = 4;
        }
        LastMowX = BoyPx;
        LastMowY = BoyPy;
        BoyIsMowing = 1;
        break;
    case 4:
        if (BoyPy < 12)
            BoyDir = 2;
        else
            if (BoyPy > 12)
                BoyDir = 0;
            else
                if (BoyPx > 3)
                    BoyDir = 3;
                else {
                    BoyHere = 5;
                    BoyIsMowing = 0;
                }
        LastMowX = BoyPx;
        LastMowY = BoyPy;
        break;
    case 5:
        if (BoyPy < 5)
            BoyDir = 2;
        else
            if (BoyPy > 5)
                BoyDir = 0;
            else
                if (BoyPx > 3)
                    BoyDir = 3;
                else
                    BoyHere = 1;
        break;
    }
    BoyFrame = dirFrame[BoyDir] + stepAnim[YardCycle & 3];
    if (BoyIsMowing != 0) {
        BoyFrame += 100;
        BoyX += BxTab[BoyDir];
        BoyY += ByTab[BoyDir];
    } else
        if (BoyStandCnt == 0) {
            if (SRand32() == 0)
                BoyStandCnt = 20;
            BoyX += BxTab[BoyDir];
            BoyY += ByTab[BoyDir];
        } else {
            BoyStandCnt--;
            BoyFrame = BoyDir + 20;
        }
    BoyPx = (BoyX + BoyY - 200) / 28;
    BoyPy = (BoyY - 38) / 10;
    if (BoyPy < 0)
        BoyPy = 0;
    if (BoyPy > 15)
        BoyPy = 15;
    if (BoyPx < 0)
        BoyPx = 0;
    if (BoyPx > 11)
        BoyPx = 11;
    if (BoyIsMowing == 0) {
        if (BoyPy < 1)
            BoyDir = 2;
        else
            if (BoyPy > 14)
                BoyDir = 0;
        if (BoyPx > 10)
            BoyDir = 3;
        else
            if (BoyPy < 5) {
                if (BoyPx < 4)
                    BoyDir = 1;
            } else
                if (BoyPx < 3) {
                    BoyDir = 0;
                    if (BoyPy < 6) {
                        if (BoyHere == 3)
                            BoyDir = 1;
                        else
                            NodeNum = 21;
                    }
                }
    }
    FootHere = 0;
    FootTog = !FootTog;
    if (BoyPy == CurYardPnt[1] && BoyPx == CurYardPnt[0]) {
        FootHere = 1;
        FootY = (BoyY - 38) % 10;
        FootX = (BoyX + BoyY - 200) % 28;
        FootX = ((FootX << 2) + 6) & 0x7f;
        FootY = ((FootY + 1) * 6) & 0x3f;
        MowX = FootX + footDx[BoyDir & 3];
        MowY = FootY + footDy[BoyDir & 3];
        if (BoyDir & 1) {
            if (FootTog != 0)
                FootY += 6;
            else
                FootY -= 6;
        } else {
            if (FootTog != 0)
                FootX += 6;
            else
                FootX -= 6;
        }
        FootFall(FootX, FootY);
        if (BoyIsMowing != 0)
            MowerFall(MowX, MowY);
    } else
        if (BoyIsMowing != 0) {
            if ((v = YMapPopB[BoyPx][BoyPy]) != 0) {
                if ((v -= v >> 2) == 0)
                    BColoniesKilled++;
                YMapPopB[BoyPx][BoyPy] = v;
            }
            if ((v = YMapPopR[BoyPx][BoyPy]) != 0) {
                if ((v -= v >> 2) == 0)
                    RColoniesKilled++;
                YMapPopR[BoyPx][BoyPy] = v;
            }
        }
}

/* GetMowDir (Win16 unit order): direction toward an adjacent uncut grass cell */
int far GetMowDir(int x, int y)
{
    int i, ny, nx;

    for (i = 3; i >= 0; i--) {
        nx = kidDx[i] + x;
        ny = kidDy[i] + y;
        if (IsValidYard(nx, ny) && NotMowed(nx, ny))
            return i;
    }
    if (x > 10)
        return 0;
    if (y > 14)
        return 1;
    if (y < 1) {
        SendBoyMsg(6);
        BoyHere = 4;
        return 2;
    }
    return YardCycle & 3;
}


/* NotMowed (Win16 unit order): cut the grass bit of a yard cell */
int far NotMowed(int x, int y)
{
    int bit;

    bit = 1 << y;
    if (GrassMap[x] & bit) {
        GrassMap[x] -= bit;
        return 1;
    }
    return 0;
}

/* IsValidYard */
int far IsValidYard(int x, int y)
{
    if (x >= 0 && y >= 0 && x <= 11 && y <= 15)
        return 1;
    return 0;
}

/* InitGrassMap */
void far InitGrassMap(void)
{
    int i;

    GrassMap[0] = 0;
    GrassMap[1] = 0;
    GrassMap[2] = 0;
    for (i = 3; i < 12; ++i)
        GrassMap[i] = -1;
}


/* SimKidInside (exact under 6.00AX /Oe /Og /Zi, worker resJ/s06).  The row division
 * BoyPy = (BoyY - 38) / 10 comes before the column division in the source; /Og schedules
 * the column store first, and only in this order is (BoyY - 38) kept as a global CSE temp
 * [bp-24h] across the early returns (in column-first order the local CSE of BoyY into CX blocks
 * it; micro contrast work/resJ/s06/m/m1.c vs m2.c).  Local names are byte-equivalent
 * hypotheses: the final loop counts with x (the kidX home [bp-2]) and draws the row into i (SI)
 * and the column into frame (DI); the else-if index (c48 - 30) is i. */
extern int far MapMode;
extern int far YardMode;
extern int far RpopT;
extern int far BpopT;
extern unsigned char far fd_3E1D_6180[128][64];
extern int far fd_50F6_0F18;
extern unsigned char far AlistT[];
extern int far SpidX;
extern int far SpidY;
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

    if (ForSaleState == 1)
        return;
    if (NodeNum < 30 && nodeLen[NodeNum] < ++NodeCnt) {
        NodeCnt = 0;
        switch (SRand1(3)) {
        case 0:
            frame = nodeNext0[NodeNum];
            break;
        case 1:
            frame = nodeNext1[NodeNum];
            break;
        case 2:
            frame = nodeNext2[NodeNum];
            break;
        }
        NodeNum = frame;
        switch (frame) {
        case 6:
            SendBoyMsg(21);
            break;
        case 7:
            SendBoyMsg(22);
            break;
        case 14:
            SendBoyMsg(SRand1(3) + 15);
            break;
        case 16:
            SendBoyMsg(SRand1(2) + 18);
            break;
        case 33:
            SendBoyMsg(20);
            break;
        }
    }
    if (NodeNum < 30) {
        switch (NodeNum) {
        case 0:
            frame = kidF0[NodeCnt];
            x = kidX0[NodeCnt];
            y = kidY0[NodeCnt];
            break;
        case 1:
            frame = kidF1[NodeCnt];
            x = kidX1[NodeCnt];
            y = kidY1[NodeCnt];
            break;
        case 2:
            frame = kidF2[NodeCnt];
            x = kidX2[NodeCnt];
            y = kidY2[NodeCnt];
            break;
        case 3:
            frame = kidF3[NodeCnt];
            x = kidX3[NodeCnt];
            y = kidY3[NodeCnt];
            break;
        case 4:
            frame = kidF4[NodeCnt];
            x = kidX4[NodeCnt];
            y = kidY4[NodeCnt];
            break;
        case 5:
            frame = kidF5[NodeCnt];
            x = kidX5[NodeCnt];
            y = kidY5[NodeCnt];
            break;
        case 6:
            frame = kidF6[NodeCnt];
            x = kidX6[NodeCnt];
            y = kidY6[NodeCnt];
            break;
        case 7:
            frame = kidF7[NodeCnt];
            x = kidX7[NodeCnt];
            y = kidY7[NodeCnt];
            break;
        case 8:
            frame = kidF8[NodeCnt];
            x = kidX8[NodeCnt];
            y = kidY8[NodeCnt];
            break;
        case 9:
            frame = kidF9[NodeCnt];
            x = kidX9[NodeCnt];
            y = kidY9[NodeCnt];
            break;
        case 10:
            frame = kidF10[NodeCnt];
            x = kidX10[NodeCnt];
            y = kidY10[NodeCnt];
            break;
        case 11:
            frame = kidF11[NodeCnt];
            x = kidX11[NodeCnt];
            y = kidY11[NodeCnt];
            break;
        case 12:
            frame = kidF12[NodeCnt];
            x = kidX12[NodeCnt];
            y = kidY12[NodeCnt];
            break;
        case 13:
            frame = kidF13[NodeCnt];
            x = kidX13[NodeCnt];
            y = kidY13[NodeCnt];
            break;
        case 14:
            frame = kidF14[NodeCnt];
            x = kidX14[NodeCnt];
            y = kidY14[NodeCnt];
            break;
        case 15:
            frame = kidF15[NodeCnt];
            x = kidX15[NodeCnt];
            y = kidY15[NodeCnt];
            break;
        case 20:
            frame = kidF20[NodeCnt];
            x = kidX20[NodeCnt];
            y = kidY20[NodeCnt];
            break;
        case 21:
            frame = kidF21[NodeCnt];
            x = kidX21[NodeCnt];
            y = kidY21[NodeCnt];
            break;
        }
    } else
        if (NodeNum < 39) {
            i = NodeNum - 30;
            frame = outF[i];
            x = outX[i];
            y = outY[i];
            if (SRand1(outChance[i]) == 0) {
                NodeNum = outNext[i];
                NodeCnt = 0;
            }
        }
    BoyHere = 0;
    if (NodeNum == 38)
        BoyHere = BoyDir = 1;
    if (NodeNum == 20 && NodeCnt > 2)
        BoyHere = 1;
    if (NodeNum == 21 && NodeCnt < 3)
        BoyHere = 1;
    BoyX = x;
    BoyY = y;
    BoyFrame = frame;
    if (MapMode == 0 && YardMode < 2) {
        if ((NodeCnt == 3 && NodeNum == 20 && BoyFrame == 900) ||
            (NodeCnt == 1 && NodeNum == 21 && BoyFrame == 903) ||
            (NodeCnt == 6 && NodeNum == 20 && BoyFrame == 6) ||
            (NodeCnt == 3 && NodeNum == 21 && BoyFrame == 1))
            f_00DF_00E8(0x18, 0, 0);
    }
    BoyPy = (BoyY - 38) / 10;
    BoyPx = (BoyX + BoyY - 200) / 28;
    FootHere = 0;
    FootTog = !FootTog;
    i = (CurYardPnt[0] << 4) + CurYardPnt[1];
    if (BoyPy != CurYardPnt[1] || CurYardPnt[0] != BoyPx)
        return;
    if (i == 0 || i == 1 || i == 16 || i == 32)
        return;
    if (BoyFrame >= 0 && BoyFrame < 12)
        BoyDir = frameDir[BoyFrame];
    else
        BoyDir = 2;
    FootHere = 1;
    FootY = (BoyY - 38) % 10;
    FootX = (BoyX + BoyY - 200) % 28;
    FootX = ((FootX << 2) + 6) & 0x7f;
    FootY = ((FootY + 1) * 6) & 0x3f;
    if (BoyDir & 1) {
        if (FootTog != 0)
            FootY += 6;
        else
            FootY -= 6;
    } else {
        if (FootTog != 0)
            FootX += 6;
        else
            FootX -= 6;
    }
    FootFall(FootX, FootY);
    f_00DF_00E8(9, 0, 0x7e);
    for (x = 0; x < (BpopT + RpopT) << 3; x++) {
        i = SRand128();
        frame = SRand64();
        if (fd_3E1D_6180[i][frame] != 0) {
            fd_50F6_0F18 = f_0EC1_0291(i, frame);
            if (fd_50F6_0F18 >= 0) {
                DeadAntHere(i, frame, AlistT[fd_50F6_0F18] & 0x80);
                fd_3E1D_6180[i][frame] = AlistT[fd_50F6_0F18] = 0;
            }
        }
        if ((SpidX >> 4) == i && (SpidY >> 4) == frame)
            f_0CDB_0DE0();
    }
    if (CurGameType == 2 && fd_50F6_048C == 1 && SRand4() == 0)
        o22_39C7_0D21(9);
}

extern int far BirdX;
extern int far BirdGoalY;
extern int far BirdY;
extern int far BirdGoalX;
extern int far SwarmCntB;
extern int far QueenStorageB;
extern int far SwarmCntR;
extern int far QueenStorageR;
extern void far InvalQueenStorageDisp(void);
extern int far SRand2(void);
extern long far fd_50F6_383A;

/* SimBird (Win16 pair MEDIUM, unit order): the bird flies over the yard and eats swarms */
void far SimBird(void)
{
    int d;
    int step;
    int oldY;
    int soundValue;
    long now;

    if (BirdOn != 0) {
        if (BirdOn == 1)
            BirdX += 0x10;
        else
            BirdX += 8;
        if (BirdOn == 1) {
            d = BirdGoalY - BirdY;
            if (d != 0) {
                if (((d >= 0) ? d : -d) >= 4)
                    BirdY += d > 0 ? 4 : -4;
                else
                    BirdY += d > 0 ? 1 : -1;
            }
        } else
            BirdY -= 8;
        BirdFrame = (BirdFrame + 1) & 1;
        if (BirdX < 0 || BirdX > 0x1ff || BirdY < 0 || BirdY > 0xff) {
            BirdOn = 0;
            BirdDelay = fd_50F6_383A + 30L;
            return;
        }
        if (BirdOn != 1)
            return;
        if (BirdX < BirdGoalX || BirdY < BirdGoalY - 4 ||
            BirdY > BirdGoalY + 4)
            return;
        if (SwarmCntB > 0)
            SwarmCntB -= (SwarmCntB + 7) >> 3;
        if (QueenStorageB > 0) {
            QueenStorageB -= (QueenStorageB + 7) >> 3;
            InvalQueenStorageDisp();
        }
        if (SwarmCntR > 0)
            SwarmCntR -= (SwarmCntR + 7) >> 3;
        if (QueenStorageR > 0)
            QueenStorageR -= (QueenStorageR + 7) >> 3;
        if (MapMode == 0 && YardMode < 2) {
            if (SRand2() == 0)
                f_00DF_00E8(7, 0, 6);
        }
        BirdOn = 2;
    } else
        if (fd_50F6_383A > BirdDelay) {
            BirdDelay = fd_50F6_383A + 20L;
            if (CurYardPnt[0] >= 5 && SRand2() == 0 &&
                (SwarmCntB > 0 || SwarmCntR > 0)) {
                BirdGoalX = CurYardPnt[0] * 0x1c - CurYardPnt[1] * 10 + 0xb2;
                BirdGoalY = CurYardPnt[1] * 10 + 0x2e;
                BirdOn = 1;
                BirdX = 0;
                BirdY = SRand64() + 4;
                BirdFrame = 0;
            }
        }
}

extern int far CatDir;
extern char far fd_3D57_0000[];
extern int far CatX;
extern int far CatY;
extern char far fd_3D57_0008[];
extern int far DogDir;
extern int far SRand16(void);
extern unsigned long far f_0BE8_0B83(int x1, int y1, int x2, int y2);

/* SimCat (Win16 pair MEDIUM, unit order) */
void far SimCat(void)
{
    register int newX;
    register int newY;

    if (CatOn != 0) {
        CatCycle = (CatCycle + 1) & 0xfff;
        if (CatOn == 1) {
            newX = CatX + fd_3D57_0000[CatDir] * 4;
            newY = CatY + fd_3D57_0008[CatDir] * 4;
            if (SRand16() != 0 && newX >= 0xfc && newX <= 0x1ef) {
                CatX = newX;
                CatY = newY;
                CatFrame++;
                if (CatDir == 2) {
                    if (CatFrame >= 3)
                        CatFrame = 1;
                } else {
                    if (CatFrame >= 6)
                        CatFrame = 4;
                }
            } else
                if (CatDir == 2) {
                    CatDir = 6;
                    CatFrame = 4;
                } else {
                    CatDir = 2;
                    CatFrame = 1;
                }
            if (MapMode == 0 && YardMode < 2 && SRand64() == 0) {
                f_00DF_00E8(0xd, 0, 5);
                return;
            }
            if (SRand16() == 0 && CatCycle > 100 && DogDir == 2 && BoyHere == 0) {
                CatOn = 2;
                CatCycle = 0;
                CatFrame = 10;
                return;
            }
            if (CatCycle > 50) {
                if (f_0BE8_0B83(CatX, CatY, DogX, DogY) <= 0x960) {
                    CatOn = 3;
                    CatFrame = 20;
                    if (MapMode == 0 && YardMode < 2)
                        f_00DF_00E8(0xe, 0, 5);
                }
            }
        } else
            if (CatOn == 2) {
                if (++CatFrame >= 13)
                    CatFrame = 11;
                if (++CatCycle > 30) {
                    CatCycle = 0;
                    CatOn = 1;
                    CatFrame = (CatDir == 2) ? 0 : 3;
                }
            } else {
                if (++CatFrame >= 30) {
                    CatFrame = 0;
                    CatOn = 0;
                    CatDelay = MacTickCount() + 600L;
                }
            }
    } else
        if (MacTickCount() > CatDelay) {
            CatDelay = MacTickCount() + 200L;
            if (SRand16() == 0 || GlobalKey == 0x8d) {
                CatOn = 1;
                CatX = 0xfc;
                CatY = 0x19;
                CatDir = 2;
                CatFrame = 0;
                CatCycle = 0;
            }
        }
}

extern long far DogBarkDelay;
extern int far DogPy;
extern int far DogPx;
int far FollowBoyDir(void);
int far FollowCatDir(void);
void far MakeBark(int kind, int level);

/* SimDog (Win16 unit order) */
void far SimDog(void)
{
    if (--DogTurnCnt < 0) {
        if (CatOn != 0)
            DogDir = FollowCatDir();
        else
            if (NodeNum < 0x26)
                DogDir = (SRand1(3) + DogDir - 1) & 3;
            else
                DogDir = FollowBoyDir();
        DogTurnCnt = 4;
    }
    if (DogDir == 1 && SRand1(10) == 0) {
        DogDir = SRand2() + 4;
        DogTurnCnt = 6;
    }
    if (DogDir > 3)
        DogFrame = dogD[DogDir] + (YardCycle & 1);
    else
        DogFrame = dogD[DogDir] + dogC[YardCycle & 3];
    DogY += dogB[DogDir];
    DogPy = (DogY - 38) / 10;
    DogX += dogA[DogDir];
    DogPx = (DogX + DogY - 200) / 28;
    if (DogPy < 0) DogPy = 0;
    if (DogPy > 15) DogPy = 15;
    if (DogPx < 0) DogPx = 0;
    if (DogPx > 11) DogPx = 11;
    if (DogPy < 1)
        DogDir = 2;
    else
        if (DogPy > 14)
            DogDir = 0;
    if (DogPx > 10)
        DogDir = 3;
    else
        if (DogPx < 4)
            DogDir = 1;
    if (DogFrame >= 100 && DogFrame <= 103 && SRand1(6) == 0)
        MakeBark(SRand4(), 5);
}

/* FollowBoyDir (Win16 unit order): dog direction toward the boy */
int far FollowBoyDir(void)
{
    register int dy;
    int dx;
    register int ady;
    int adx;

    dy = DogPy - BoyPy;
    dx = DogPx - BoyPx;
    if (dx < 0) adx = -dx;
    else adx = dx;
    if (dy < 0) ady = -dy;
    else ady = dy;
    if (adx < 1 && ady < 1 && BoyIsMowing != 0) MakeBark(1, 0x7f);
    if (adx < 2 && ady < 2) return YardCycle & 3;
    if (dy < 0) return 2;
    if (dy > 1) return 0;
    if (dx < 0) return 1;
    if (dx > 1) return 3;
    return YardCycle & 3;
}

/* FollowCatDir (Win16 unit order) */
int far FollowCatDir(void)
{
    if (DogPx < 5) return 1;
    if (DogPx > 8) return 3;
    if (DogPy > 0) return 0;
    return YardCycle & 3;
}

/* MakeBark (Win16 unit order) */
void far MakeBark(int kind, int level)
{
    if (MapMode == 0 && YardMode < 2 && MacTickCount() > DogBarkDelay) {
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
        DogBarkDelay = MacTickCount() + SRand1(30) + 60;
    }
}

extern int far f_10F7_003A(int a);
extern int far SuserX;
extern int far SuserY;
extern int far MeMode;

/* FootFall: the boy's foot squashes ants under it */
void far FootFall(int x, int y)
{
    int i, j, a, x2, y2;

    f_00DF_00E8(0x23, 0, 0x14);
    if (BoyDir & 1) {
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
                            DeadAntHere(i, j, AlistT[a] & 0x80);
                            AlistT[a] = 0;
                        }
                    } else
                        o22_39C7_0D21(5);
                }
            }
        }
    }
    if (SuserX >= x && SuserX < x2 && SuserY >= y && SuserY < y2) {
        f_0CDB_0DE0();
        if (MeMode == 1)
            o22_39C7_0D21(5);
    }
}

extern int far fd_50F6_0D6A;
extern unsigned char far AlistX[];
extern unsigned char far AlistY[];
extern int far SpidOn;

/* MowerFall (Win16 unit order): the mower kills ants in the yard */
void far MowerFall(int x, int y)
{
    register int i;

    if (CurGameType == 0)
        return;
    i = fd_50F6_0D6A;
    while (i > 0) {
        i--;
        if (AlistT[i] != 0 && SRand4() != 0) {
            AlistT[i] = fd_3E1D_6180[AlistX[i]][AlistY[i]] = 0;
        }
    }
    if (SpidOn != 0 && SRand4() != 0)
        f_0CDB_0DE0();
    if (MeMode <= 1 && fd_50F6_048C == 1 && SRand4() != 0)
        o22_39C7_0D21(6);
}

/* MaintainSwarm (Win16 unit order) */
void far MaintainSwarm(void)
{
    register int n;

    n = SwarmCntB;
    if (n > 0) {
        if (n >= 4)
            n = SwarmCntB - (SwarmCntB >> 2);
        else
            n = SwarmCntB - 1;
    }
    if (QueenStorageB > n)
        n = QueenStorageB;
    if (n > 50)
        n = 50;
    SwarmCntB = n;

    n = SwarmCntR;
    if (n > 0) {
        if (n >= 4)
            n = SwarmCntR - (SwarmCntR >> 2);
        else
            n = SwarmCntR - 1;
    }
    if (QueenStorageR > n)
        n = QueenStorageR;
    if (n > 50)
        n = 50;
    SwarmCntR = n;
}

extern int far ColonyUpdateFlag;
extern int far ColonyTotalBlack;
extern int far ColonyTotalRed;
extern int far HouseColonies;
extern int far LayDownQueenMode;
extern int far IsGameOver;
extern int far BlackWon;
extern int far CastePopB[6];
extern int far SRand8(void);
extern void far myBeginSong(int id, int arg);
extern void far o14_384C_0B6A(int a, int b, int c);
extern void far DrawSimPayoff(void);
int far GetNearbyPatches(int x, int y);
void far Reproduce(int x, int y, int colony);

/* SimColonies (Win16 unit order): yard colony growth, swarms and the for-sale scenario */
/* r also carries the two home-nest populations before the loops and b is read before r: both
 * decide the frame layout (r at [bp-8], b [bp-4], patches [bp-2]). */
void far SimColonies(void)
{
    int patches, b, y, r;
    int x;

    if (YardCycle & 0x1f)
        return;
    ColonyUpdateFlag = 1;
    MaintainSwarm();
    ColonyTotalBlack = 0;
    ColonyTotalRed = 0;
    HouseColonies = 0;
    if (BpopT > 0)
        ColonyTotalBlack = 1;
    if (RpopT > 0)
        ColonyTotalRed = 1;
    r = BpopT & 0x3ff;
    if (r > 250)
        r = 250;
    YMapPopB[CurYardPnt[0]][CurYardPnt[1]] = r;
    r = RpopT & 0x3ff;
    if (r > 250)
        r = 250;
    YMapPopR[CurYardPnt[0]][CurYardPnt[1]] = r;
    for (x = 0; x < 12; x++) {
        for (y = 0; y < 16; y++) {
            if (CurYardPnt[0] == x && CurYardPnt[1] == y)
                continue;
            b = YMapPopB[x][y];
            r = YMapPopR[x][y];
            if (b == 0 && r == 0)
                continue;
            if (CurGameType == 2)
                if (x < 2 || (x == 3 && y < 5))
                    HouseColonies++;
            patches = GetNearbyPatches(x, y);
            if (b != 0) {
                ColonyTotalBlack++;
                if (patches != 0)
                    b += patches;
                else
                    b++;
                if (b <= 0) {
                    BColoniesKilled++;
                    YMapPopB[x][y] = 0;
                } else
                    if (b < 250)
                        YMapPopB[x][y] = b;
                    else {
                        YMapPopB[x][y] = 250;
                        if (SRand1(10) == 0)
                            Reproduce(x, y, 0);
                    }
            }
            if (r != 0) {
                ColonyTotalRed++;
                if (patches != 0)
                    r -= patches;
                else
                    r++;
                if (r <= 0) {
                    RColoniesKilled++;
                    YMapPopR[x][y] = 0;
                    if (x == 11) {
                        y = 8;
                        YMapPopR[SRand1(6) + 2][0] = 20;
                    }
                } else
                    if (r < 250)
                        YMapPopR[x][y] = r;
                    else {
                        YMapPopR[x][y] = 250;
                        if (SRand1(10) == 0)
                            Reproduce(x, y, 1);
                    }
            }
        }
    }
    if (LayDownQueenMode == 1) {
        SwarmDelayB++;
        if (SwarmDelayB > SRand8() + 10) {
            SwarmDelayB = 0;
            while (QueenStorageB > 0) {
                Reproduce(CurYardPnt[0], CurYardPnt[1], 0);
                QueenStorageB--;
            }
        }
    }
    SwarmDelayR++;
    if (SwarmDelayR > SRand8() + 10) {
        SwarmDelayR = 0;
        while (QueenStorageR > 0) {
            Reproduce(CurYardPnt[0], CurYardPnt[1], 1);
            QueenStorageR--;
        }
    }
    if (CurGameType != 2)
        return;
    if (ColonyTotalRed == 0 && LastColonyPopR != 0) {
        myBeginSong(0x4e22, 0x7e);
        o14_384C_0B6A(0, 0x2744, 1);
        if (ForSaleState == 0)
            o14_384C_0B6A(0, 0x2747, 1);
    }
    LastColonyPopB = ColonyTotalBlack;
    LastColonyPopR = ColonyTotalRed;
    if (ForSaleState == 0 && HouseColonies > 24) {
        ForSaleState = 1;
        NodeNum = 0;
        BoyHere = 0;
        BoyFrame = -1;
        myBeginSong(0x4e23, 0x7e);
        o14_384C_0B6A(0, 0x2746, 1);
        if (ColonyTotalRed != 0)
            o14_384C_0B6A(0, 0x2745, 1);
    }
    if (ForSaleState != 0 && ColonyTotalRed == 0) {
        myBeginSong(0x4e25, 0x7e);
        o14_384C_0B6A(0, 0x2749, 1);
        IsGameOver = 1;
        BlackWon = 1;
        DrawSimPayoff();
        return;
    }
    if (ColonyTotalBlack < 2 && CastePopB[5] == 0 && CastePopB[0] == 0 &&
        CastePopB[3] == 0 && CastePopB[4] == 0) {
        IsGameOver = 1;
        BlackWon = 0;
        o14_384C_0B6A(0, 0x2748, 1);
    }
}

/* GetNearbyPatches (Win16 unit order) */
int far GetNearbyPatches(int x, int y)
{
    int i, count, px, py;

    count = 0;
    for (i = 0; i < 6; i++) {
        px = PatchX[i] + x;
        py = PatchY[i] + y;
        if (px >= 0 && py >= 0 && px < 12 && py < 16) {
            if (YMapPopB[px][py] != 0)
                count += 3;
            if (YMapPopR[px][py] != 0)
                count -= 3;
        }
    }
    return count;
}

extern int far SGSRand(int range);
extern int far RColoniesStarted;
extern int far BColoniesStarted;

/* grows a colony in a random neighbouring yard cell */
void far Reproduce(int x, int y, int colony)
{
    register int nx;
    register int ny;

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
        if (YMapPopR[nx][ny] == 0)
            RColoniesStarted++;
        YMapPopR[nx][ny]++;
    } else {
        if (YMapPopB[nx][ny] == 0)
            BColoniesStarted++;
        YMapPopB[nx][ny]++;
    }
}

extern int far MigrateY;
extern int far MigrateX;

/* picks the source colony cell under a yard position */
void far StartMigrate(int x, int y)
{
    MigrateY = (y - 0x42) / 10;
    MigrateX = (x + y - 0xee) / 28;
    if (MigrateX < 0 || MigrateY < 0 || MigrateX > 11 || MigrateY > 15)
        MigrateX = -1;
    if (YMapPopB[MigrateX][MigrateY] == 0)
        MigrateX = -1;
}

/* moves half of the source colony to the yard cell under a position */
void far EndMigrate(int x, int y)
{
    int sum, half;
    register int nx;
    register int ny;

    if (MigrateX < 0)
        return;
    ny = (y - 0x42) / 10;
    nx = (x + y - 0xee) / 28;
    if (nx < 0 || ny < 0 || nx > 11 || ny > 15)
        return;
    half = YMapPopB[MigrateX][MigrateY] >> 1;
    YMapPopB[MigrateX][MigrateY] -= half;
    sum = YMapPopB[nx][ny] + half;
    if (sum < 0xfb)
        YMapPopB[nx][ny] = sum;
    else
        YMapPopB[nx][ny] = 0xfa;
}



