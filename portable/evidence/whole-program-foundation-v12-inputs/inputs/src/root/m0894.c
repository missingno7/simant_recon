/* Root module, code frame 0894: ant colony simulation (DoAntSim, A-list ants).
 * MSC 6.00A /AL /Os /Oe /Og.  The set/order of declarations (externs and locals, also of
 * earlier functions) decides commutative operand order under /Og (e.g. tile ^ attribute),
 * so declarations are kept exactly as verified. */

extern int far SRand1(int range);
extern int far SRand2(void);
extern int far SRand4(void);
extern int far SRand8(void);
extern int far SRand16(void);
extern int far SRand32(void);
extern int far SRand256(void);

extern int far Cycle;
extern unsigned long far fd_50F6_0C26;
extern int far fd_3D57_07B2;
extern int far fd_50F6_0F06;
extern int far fd_50F6_0F2E;
extern int far fd_50F6_0F10;
extern int far fd_50F6_0EF6;
typedef struct {
    int v;
    int h;
} Point;

extern Point far fd_50F6_08EC;
extern Point far fd_50F6_0AA2;
extern Point far fd_50F6_0A02;
extern Point far fd_50F6_0852;
extern int far fd_50F6_0376;
extern int far fd_3D57_02C2;
extern int far fd_50F6_0D40[20];
extern int far fd_50F6_0D72[20];
extern int far fd_50F6_08DC;
extern int far fd_50F6_08E8;
extern int far fd_50F6_0B12[6];
extern int far fd_50F6_0C2A[6];
extern int far fd_3D57_0C18;
extern int far HealthB;
extern int far HealthR;
extern int far fd_50F6_0EAC;
extern int far fd_3D57_0C1A;
extern int far fd_50F6_1040;
extern int far ListIndexA;
extern int far Tindex;
extern unsigned char far AlistT[];
extern unsigned char far AlistY[];
extern unsigned char far AlistX[];
extern long far fd_50F6_0F30;
extern unsigned char far AlistM[];
extern unsigned char far LifeA[128][64];
extern char far Dy8[8];
extern char far Dx8[8];
extern unsigned char far PherMapRN[64][32];
extern unsigned char far PherMapBN[64][32];
extern int far fd_50F6_06AA;
extern int far fd_50F6_073A;
extern int far fd_50F6_07C8;
extern int far fd_50F6_0850;
extern unsigned char far MapA[128][64];
extern int far Barrier;
extern unsigned char far AlistS[];
extern int far fd_50F6_04E2;
extern int far fd_50F6_1044;
extern signed char far TurnTab[8][8];
extern unsigned char far PherMapA[64][32];
extern int far ListIndexB;
extern unsigned char far HoleMapB[];
extern int far ListIndexR;
extern unsigned char far HoleMapR[];
extern int far fd_3D57_0C14;
extern long far fd_50F6_0F3E;
extern int far fd_50F6_09FA;
extern long far fd_50F6_0EFC;
extern int far fd_50F6_0A00;
extern int far fd_50F6_0476;
extern unsigned char far fd_50F6_037C[100];
extern unsigned char far fd_50F6_0404[100];
extern int far TERRAINset;
extern int far fd_3D57_0074[16];
extern signed char far fd_3D57_0094[];

extern void far o06_35F5_0173(void);
extern void far DoWater(void);
extern void far f_0AD9_03D3(void);
extern void far f_0CDB_00B3(void);
extern void far f_0AD9_093C(void);
extern void far f_1383_0002(void);
extern void far o25_39C7_0000(void);
extern void far DoAntSimR(void);
extern void far DoAntSimY(void);
extern void far DoAntMoveY(void);
extern void far f_0E2E_000A(void);
extern void far o14_384C_0DE5(int a);
extern void far f_0EC1_0002(void);
extern void far FullCount(void);
extern void far o24_39C7_0608(void);
extern void far f_1496_025E(void);
extern void far f_0EC1_0081(void);
extern void far f_1496_0006(void);
extern void far f_1496_010C(void);
extern void far f_1496_019A(void);
extern void far f_0EC1_0100(void);
extern void far f_1496_0089(void);
extern void far f_1496_0153(void);
extern void far f_1496_01FE(void);
extern void far f_0DEF_0000(void);
extern void far AddFood(int count, int sound);
extern void far f_0DEF_006B(int index);
extern int far f_0EC1_0291(int x, int y);
extern void far f_0250_43F2(int x, int y, int a);
extern void far InvalQueenStorageDisp(void);
extern int far f_1383_0E89(int x, int y, int dir);
extern void far PickupFoodA(int x, int y);
extern void far f_1496_0404(int x, int y, int level);
extern void far f_1496_03CC(int x, int y, int level);
extern void far f_1496_04AC(int x, int y, int colour);
extern int far IsYellowAnt(int value);
extern void far o25_3BA4_0DFB(int a, int index);
extern void far o22_39C7_19E5(int x, int y, int dir);
extern int far f_1383_0976(int caste, int type);
extern int far f_1383_10A8(int x, int y);
extern int far f_1383_0C2A(int x, int y, int dir, int attribute);
extern int far f_1383_0DCC(int x, int y, int dir);
extern int far f_1383_0A95(int x, int y, int dir, int attribute);
extern int far f_1383_0FCE(int x, int y, int dir);
extern int far f_1383_0ECC(int x, int y, int dir);
extern void far AddAntToBList(int x, int y, int type, int mode, int state);
extern void far AddAntToRList(int x, int y, int type, int mode, int state);
extern void far DigTileB(int x, int y);
extern void far DigTileR(int x, int y);
extern void far f_1496_0395(int x, int y, int level);
extern int far RRand(int range);
extern void far f_0250_4302(int x, int y, int plane);
extern int far IsValidA(int x, int y);

void far DoSmells(void);
void far ClrModePop(void);
void far TallyModePop(void);
void far FeedAnts(void);
void far DoAntSimA(void);
void far SimEggA(int index);
void far SimQueenA(int index);
int far LostHeadA(int x, int y, int life);
void far DoRestAnt(int index);
void far DoRepoLoit(int index);
void far DoRepoExit(int index);
void far DoRepoFly(int index);
void far DoDefendNest(int index);
void far DoRandAntA(int index);
void far DoRandAntAA(int index);
void far DoDigOutAntA(int index);
void far DoToNestAnt(int index);
void far DoToAlarm(int index);
void far DoReturnFoodAnt(int index);
void far DoForageAnt(int index);
void far DoRecruitAnt(int index);
void far GoInNest(int x, int y, int index);
void far DoFightA(int index);
void far DeadAntHere(int x, int y, int type);
void far DoAttackAnt(int index);
int far IsItHole(int x, int y);
int far IsItFood(int tile);
int far RandTurn(int dir);
void far StartFightA(int index, int x, int y, int nx, int ny);
int far GetWinner(int a, int b);

void far DoAntSim(void)
{
    if (++Cycle > 0x1000)
        Cycle = 0;
    fd_50F6_0C26++;
    if (fd_3D57_07B2 == 1) {
        fd_50F6_0F06 = 0;
        fd_50F6_0F2E = 0;
        fd_50F6_0F10 = 0;
        fd_50F6_0EF6 = 0;
        fd_50F6_08EC.h = -1;
        fd_50F6_08EC.v = -1;
        fd_50F6_0AA2 = fd_50F6_08EC;
        fd_50F6_0A02 = fd_50F6_08EC;
        fd_50F6_0852 = fd_50F6_08EC;
    }
    if ((Cycle & 0x3f) == 0)
        FeedAnts();
    if ((Cycle & 0x1f) == 0)
        DoSmells();
    o06_35F5_0173();
    DoWater();
    f_0AD9_03D3();
    f_0CDB_00B3();
    if (Cycle & 1)
        f_0AD9_093C();
    f_1383_0002();
    ClrModePop();
    DoAntSimA();
    o25_39C7_0000();
    DoAntSimR();
    DoAntSimY();
    TallyModePop();
    DoAntMoveY();
    f_0E2E_000A();
    if (fd_50F6_0376)
        o14_384C_0DE5(0);
    fd_3D57_02C2 = 1;
}

void far DoSmells(void)
{
    switch ((Cycle & 0x60) >> 5) {
    case 0:
        f_0EC1_0002();
        FullCount();
        o24_39C7_0608();
        f_1496_025E();
        break;
    case 1:
        f_0EC1_0081();
        f_1496_0006();
        f_1496_010C();
        f_1496_019A();
        break;
    case 2:
        FullCount();
        o24_39C7_0608();
        f_1496_025E();
        break;
    case 3:
        f_0EC1_0100();
        f_1496_0089();
        f_1496_0153();
        f_1496_01FE();
        break;
    }
}

void far ClrModePop(void)
{
    int i;

    for (i = 0; i < 20; i++) {
        fd_50F6_0D40[i] = 0;
        fd_50F6_0D72[i] = 0;
    }
    if (fd_50F6_08DC)
        --fd_50F6_08DC;
    if (fd_50F6_08E8)
        --fd_50F6_08E8;
}

void far TallyModePop(void)
{
    fd_50F6_0B12[0] = fd_50F6_0D40[2] + fd_50F6_0D40[3];
    fd_50F6_0B12[1] = fd_50F6_0D40[4] + fd_50F6_0D40[5];
    fd_50F6_0B12[2] = fd_50F6_0D40[1];
    fd_50F6_0B12[3] = fd_50F6_0D40[7];
    fd_50F6_0B12[4] = fd_50F6_0D40[12];
    fd_50F6_0B12[5] = fd_50F6_0D40[6];
    fd_50F6_0C2A[0] = fd_50F6_0D72[2] + fd_50F6_0D72[3];
    fd_50F6_0C2A[1] = fd_50F6_0D72[4] + fd_50F6_0D72[5];
    fd_50F6_0C2A[2] = fd_50F6_0D72[1];
    fd_50F6_0C2A[3] = fd_50F6_0D72[7];
    fd_50F6_0C2A[4] = fd_50F6_0D72[12];
    fd_50F6_0C2A[5] = fd_50F6_0D72[6];
    if (fd_50F6_0D72[19] < 1)
        f_0DEF_0000();
}

void far FeedAnts(void)
{
    if (fd_3D57_0C18 == 0) {
        if (--HealthB < 0)
            HealthB = 0;
    }
    if (--HealthR < 0)
        HealthR = 0;
    if (fd_50F6_0EAC == 3)
        return;
    if (fd_50F6_1040 >= fd_3D57_0C1A)
        return;
    AddFood(0x96, 1);
    fd_3D57_0C1A = SRand1(0x32) + 1;
}

void far DoAntSimA(void)
{
    int t;
    int mode;

    Tindex = ListIndexA;
    while (Tindex > 0) {
        Tindex--;
        if (SRand256() == 0) {
            t = AlistT[Tindex];
            if (t) {
                if (t & 0x80)
                    t = HealthR;
                else
                    t = HealthB;
                if (SRand32() > t) {
                    DeadAntHere(AlistX[Tindex], AlistY[Tindex],
                                AlistT[Tindex] & 0x80);
                    AlistT[Tindex] = 0;
                    fd_50F6_0F30++;
                }
            }
        }
        t = AlistT[Tindex];
        if (t == 0)
            continue;
        mode = AlistM[Tindex];
        if (t & 0x80)
            fd_50F6_0D72[mode]++;
        else
            fd_50F6_0D40[mode]++;
        switch (mode) {
        case 0:
            DoRandAntA(Tindex);
            break;
        case 1:
        case 4:
            DoToNestAnt(Tindex);
            break;
        case 2:
            DoForageAnt(Tindex);
            break;
        case 3:
            DoReturnFoodAnt(Tindex);
            break;
        case 5:
            DoDigOutAntA(Tindex);
            break;
        case 6:
            DoRecruitAnt(Tindex);
            break;
        case 7:
            DoAttackAnt(Tindex);
            break;
        case 8:
            SimEggA(Tindex);
            break;
        case 9:
            SimQueenA(Tindex);
            break;
        case 10:
            DoFightA(Tindex);
            break;
        case 11:
            DoToAlarm(Tindex);
            break;
        case 12:
            DoDefendNest(Tindex);
            break;
        case 13:
            DoRestAnt(Tindex);
            break;
        case 14:
            DoRepoLoit(Tindex);
            break;
        case 15:
            DoRepoExit(Tindex);
            break;
        case 16:
            DoRepoFly(Tindex);
            break;
        case 19:
            f_0DEF_006B(Tindex);
            break;
        }
    }
}

void far SimEggA(int index)
{
    int x;
    int y;
    unsigned char type;

    x = AlistX[index];
    y = AlistY[index];
    type = AlistT[index];
    LifeA[x][y] = type;
    if (SRand1(200) == 0) {
        AlistT[index] = 0;
        LifeA[x][y] = 0;
    }
}

void far SimQueenA(int index)
{
    int x;
    int y;
    int type;

    x = AlistX[index];
    y = AlistY[index];
    type = AlistT[index];
    LifeA[x][y] = type;
    if ((type & 0x7f) > 0x67) {
        if (LostHeadA(x, y, type)) {
            LifeA[x][y] = 0;
            AlistT[index] = 0;
        }
    }
}

int far LostHeadA(int x, int y, int life)
{
    int row;
    int column;

    row = x + Dx8[life & 7];
    column = y + Dy8[life & 7];
    if (LifeA[row][column] - life == -8)
        return 0;
    if (f_0EC1_0291(row, column) >= 0)
        return 0;
    return 1;
}

void far DoRestAnt(int index)
{
    int x;
    int y;

    x = AlistX[index];
    y = AlistY[index];
    if (IsItHole(x, y) == 1)
        GoInNest(x, y, index);
    else if (SRand4() == 0)
        AlistM[index] = 2;
    else if (fd_3D57_07B2 == 1)
        f_0250_43F2(x, y, 1);
}

void far DoRepoLoit(int index)
{
    if (SRand2())
        DoRandAntAA(index);
    else
        DoToNestAnt(index);
    if (AlistT[index] & 0x80) {
        if (fd_50F6_08E8 > 100)
            AlistM[Tindex] = 0xf;
    } else {
        if (fd_50F6_08DC > 100)
            AlistM[Tindex] = 0xf;
    }
}

void far DoRepoExit(int index)
{
    int scent;

    if (AlistT[index] & 0x80)
        scent = PherMapRN[AlistX[index] >> 1][AlistY[index] >> 1];
    else
        scent = PherMapBN[AlistX[index] >> 1][AlistY[index] >> 1];
    if (scent < 100)
        DoToNestAnt(index);
    else
        DoRandAntAA(index);
    if (AlistT[index] & 0x80) {
        if (fd_50F6_08E8 != 0 && (fd_50F6_08E8 == 1 || SRand1(fd_50F6_08E8) == 0))
            AlistM[Tindex] = 0x10;
    } else {
        if (fd_50F6_08DC != 0 && (fd_50F6_08DC == 1 || SRand1(fd_50F6_08DC) == 0))
            AlistM[Tindex] = 0x10;
    }
}

void far DoRepoFly(int index)
{
    int red;

    red = AlistT[index] & 0x80;
    if (SRand32() == 0) {
        if ((red == 0 && fd_50F6_06AA < 50) || (red != 0 && fd_50F6_073A < 50)) {
            AlistT[index] = 0;
            LifeA[AlistX[index]][AlistY[index]] = 0;
            if (fd_50F6_0EAC == 2) {
                if (red == 0)
                    fd_50F6_06AA++;
                else
                    fd_50F6_073A++;
                if (SRand16() == 0) {
                    if (red == 0) {
                        fd_50F6_07C8++;
                        InvalQueenStorageDisp();
                    } else
                        fd_50F6_0850++;
                }
            }
        }
    }
}

void far DoDefendNest(int index)
{
    int scent;

    if (AlistT[index] & 0x80)
        scent = PherMapRN[AlistX[index] >> 1][AlistY[index] >> 1];
    else
        scent = PherMapBN[AlistX[index] >> 1][AlistY[index] >> 1];
    if (scent < 0x6e)
        DoToNestAnt(index);
    else
        DoRandAntAA(index);
}


void far DoRandAntA(int index)
{
    int x;
    int y;
    int attribute;
    int tile;
    int flags;
    int caste;
    int dir;
    int nx;
    int ny;

    x = AlistX[index];
    y = AlistY[index];
    attribute = AlistT[index];
    if (IsItHole(x, y)) {
        GoInNest(x, y, index);
        return;
    }
    flags = attribute & 0xf8;
    caste = (attribute & 0x78) >> 3;
    dir = f_1383_0E89(x, y, attribute & 7);
    nx = x + Dx8[dir];
    ny = y + Dy8[dir];
    tile = MapA[nx][ny];
    if (IsItFood(tile) == 1) {
        if (caste == 6 || caste == 2) {
            AlistT[index] = dir | flags | 8;
            LifeA[x][y] = AlistT[index];
            AlistM[index] = 3;
            PickupFoodA(nx, ny);
            AlistS[index] = 200;
            return;
        }
    } else if (tile > Barrier) {
        AlistT[index] = RandTurn(attribute & 7) | flags;
        LifeA[x][y] = AlistT[index];
        return;
    }
    tile = LifeA[nx][ny];
    if (tile == 0) {
        AlistT[index] = LifeA[nx][ny] = dir | flags;
        LifeA[x][y] = 0;
        AlistX[index] = nx;
        AlistY[index] = ny;
        if (AlistS[index] != 0) {
            AlistS[index]--;
            if (attribute & 0x80)
                f_1496_0404(nx, ny, AlistS[index]);
            else
                f_1496_03CC(nx, ny, AlistS[index]);
        }
        f_1496_04AC(nx, ny, attribute & 0x80);
        if (SRand8() == 0 && (caste == 6 || caste == 2))
            AlistM[index] = 2;
        return;
    }
    if (IsYellowAnt(tile) == 1) {
        if ((fd_50F6_04E2 ^ attribute) & 0x80) {
            o25_3BA4_0DFB(1, index);
            return;
        }
        if (fd_50F6_1044 == 1) {
            AlistT[index] = dir | flags;
            LifeA[x][y] = AlistT[index];
            o22_39C7_19E5(x, y, dir);
        }
        AlistT[index] = RandTurn(attribute & 7) | flags;
        LifeA[x][y] = AlistT[index];
        return;
    }
    if (((tile ^ attribute) & 0x80) == 0) {
        AlistT[index] = RandTurn(attribute & 7) | flags;
        LifeA[x][y] = AlistT[index];
        AlistM[index] = f_1383_0976(caste, attribute);
        return;
    }
    StartFightA(index, x, y, nx, ny);
}


void far DoRandAntAA(int index)
{
    int x;
    int y;
    int tile;
    int attribute;
    int flags;
    int dir;
    int nx;
    int ny;


    x = AlistX[index];
    y = AlistY[index];
    attribute = AlistT[index];
    if (IsItHole(x, y)) {
        GoInNest(x, y, index);
        return;
    }
    flags = attribute & 0xf8;
    dir = f_1383_0E89(x, y, attribute & 7);
    nx = x + Dx8[dir];
    ny = y + Dy8[dir];
    if (MapA[nx][ny] > Barrier) {
        AlistT[index] = RandTurn(attribute & 7) | flags;
        LifeA[x][y] = AlistT[index];
        return;
    }
    tile = LifeA[nx][ny];
    if (tile == 0) {
        AlistT[index] = LifeA[nx][ny] = dir | flags;
        LifeA[x][y] = 0;
        AlistX[index] = nx;
        AlistY[index] = ny;
        return;
    }
    if (IsYellowAnt(tile) == 1) {
        if ((fd_50F6_04E2 ^ attribute) & 0x80) {
            o25_3BA4_0DFB(1, index);
            return;
        }
        AlistT[index] = RandTurn(attribute & 7) | flags;
        LifeA[x][y] = AlistT[index];
        return;
    }
    if (((attribute ^ tile) & 0x80) == 0) {
        AlistT[index] = RandTurn(attribute & 7) | flags;
        LifeA[x][y] = AlistT[index];
        return;
    }
    StartFightA(index, x, y, nx, ny);
}


void far DoDigOutAntA(int index)
{
    int x;
    int y;
    int attribute;
    int flags;
    int digmode;
    int dirindex;
    int bdir;
    int nx;
    int ny;

    x = AlistX[index];
    y = AlistY[index];
    attribute = AlistT[index];
    flags = attribute & 0xf8;
    digmode = (attribute & 0x78) >> 3;
    dirindex = TurnTab[attribute & 7][SRand8()];
    bdir = f_1383_10A8(x, y);
    if (bdir != 0)
        dirindex = (bdir - 1) & 7;
    nx = x + Dx8[dirindex];
    ny = y + Dy8[dirindex];
    if (digmode != 5 && digmode != 9) {
        AlistM[index] = f_1383_0976(digmode, attribute);
        AlistS[index] = 0;
        return;
    }
    if (SRand8() == 0) {
        AlistT[index] -= 0x18;
        AlistM[index] = f_1383_0976(digmode, attribute);
        AlistS[index] = 0;
        LifeA[x][y] = AlistT[index];
        return;
    }
    if (MapA[nx][ny] > Barrier) {
        AlistT[index] = RandTurn(attribute & 7) | flags;
        LifeA[x][y] = AlistT[index];
        return;
    }
    if (LifeA[nx][ny] == 0) {
        AlistT[index] = LifeA[nx][ny] = dirindex | flags;
        LifeA[x][y] = 0;
        AlistX[index] = nx;
        AlistY[index] = ny;
    } else {
        AlistT[index] = RandTurn(attribute & 7) | flags;
        LifeA[x][y] = AlistT[index];
        return;
    }
    if (AlistS[index] != 0) {
        AlistS[index]--;
        if (attribute & 0x80)
            f_1496_0404(nx, ny, AlistS[index]);
        else
            f_1496_03CC(nx, ny, AlistS[index]);
    }
}


void far DoToNestAnt(int index)
{
    int x;
    int y;
    int attribute;
    int tile;
    int flags;
    int caste;
    int dir;
    int nx;
    int ny;

    x = AlistX[index];
    y = AlistY[index];
    attribute = AlistT[index];
    if (IsItHole(x, y)) {
        GoInNest(x, y, index);
        return;
    }
    flags = attribute & 0xf8;
    caste = (attribute & 0x78) >> 3;
    dir = f_1383_0C2A(x, y, attribute & 7, attribute);
    nx = x + Dx8[dir];
    ny = y + Dy8[dir];
    tile = MapA[nx][ny];
    if (IsItFood(tile) == 1) {
        if (caste == 6 || caste == 2) {
            AlistT[index] = dir | flags | 8;
            LifeA[x][y] = AlistT[index];
            AlistM[index] = 3;
            PickupFoodA(nx, ny);
            AlistS[index] = 200;
            return;
        }
    } else if (tile > Barrier) {
        AlistT[index] = RandTurn(attribute & 7) | flags;
        LifeA[x][y] = AlistT[index];
        return;
    }
    tile = LifeA[nx][ny];
    if (tile == 0) {
        AlistT[index] = LifeA[nx][ny] = dir | flags;
        LifeA[x][y] = 0;
        AlistX[index] = nx;
        AlistY[index] = ny;
        if (AlistS[index] != 0) {
            AlistS[index]--;
            if (attribute & 0x80)
                f_1496_0404(nx, ny, AlistS[index]);
            else
                f_1496_03CC(nx, ny, AlistS[index]);
        }
        return;
    }
    if (IsYellowAnt(tile) == 1) {
        if ((fd_50F6_04E2 ^ attribute) & 0x80) {
            o25_3BA4_0DFB(1, index);
            return;
        }
        if (fd_50F6_1044 == 1) {
            AlistT[index] = dir | flags;
            LifeA[x][y] = AlistT[index];
            o22_39C7_19E5(x, y, dir);
        }
        AlistT[index] = RandTurn(attribute & 7) | flags;
        LifeA[x][y] = AlistT[index];
        return;
    }
    if (((tile ^ attribute) & 0x80) == 0) {
        AlistT[index] = RandTurn(attribute & 7) | flags;
        LifeA[x][y] = AlistT[index];
        return;
    }
    StartFightA(index, x, y, nx, ny);
}


void far DoToAlarm(int index)
{
    int x;
    int y;
    int tile;
    int attribute;
    int flags;
    int dir;
    int nx;
    int ny;

    x = AlistX[index];
    y = AlistY[index];
    attribute = AlistT[index];
    if (IsItHole(x, y)) {
        GoInNest(x, y, index);
        return;
    }
    flags = attribute & 0xf8;
    if (PherMapA[x >> 1][y >> 1] == 0 && SRand4() == 0) {
        LifeA[x][y] = AlistT[index];
        AlistM[index] = f_1383_0976((attribute & 0x78) >> 3, attribute);
        return;
    }
    dir = f_1383_0DCC(x, y, attribute & 7);
    nx = x + Dx8[dir];
    ny = y + Dy8[dir];
    if (MapA[nx][ny] > Barrier) {
        AlistT[index] = RandTurn(attribute & 7) | flags;
        LifeA[x][y] = AlistT[index];
        return;
    }
    tile = LifeA[nx][ny];
    if (tile == 0) {
        AlistT[index] = LifeA[nx][ny] = dir | flags;
        LifeA[x][y] = 0;
        AlistX[index] = nx;
        AlistY[index] = ny;
        return;
    }
    if (IsYellowAnt(tile) == 1) {
        if ((fd_50F6_04E2 ^ attribute) & 0x80) {
            o25_3BA4_0DFB(1, index);
            return;
        }
        AlistT[index] = RandTurn(attribute & 7) | flags;
        LifeA[x][y] = AlistT[index];
        return;
    }
    if (((tile ^ attribute) & 0x80) == 0) {
        AlistT[index] = RandTurn(attribute & 7) | flags;
        LifeA[x][y] = AlistT[index];
        return;
    }
    StartFightA(index, x, y, nx, ny);
}


extern void far f_1496_0474(int x, int y, int level);
extern void far f_1496_043C(int x, int y, int level);

void far DoReturnFoodAnt(int index)
{
    int x;
    int y;
    int attribute;
    int flags;
    int ndir;
    int nx;
    int ny;

    x = AlistX[index];
    y = AlistY[index];
    attribute = AlistT[index];
    if (IsItHole(x, y)) {
        GoInNest(x, y, index);
        return;
    }
    flags = attribute & 0xf8;
    ndir = f_1383_0C2A(x, y, attribute & 7, attribute);
    nx = x + Dx8[ndir];
    ny = y + Dy8[ndir];
    if (MapA[nx][ny] > Barrier) {
        AlistT[index] = RandTurn(attribute & 7) | flags;
        LifeA[x][y] = AlistT[index];
        return;
    }
    AlistT[index] = LifeA[nx][ny] = ndir | flags;
    LifeA[x][y] = 0;
    AlistX[index] = nx;
    AlistY[index] = ny;
    if (AlistS[index] != 0) {
        AlistS[index]--;
        if (attribute & 0x80)
            f_1496_0474(nx, ny, AlistS[index]);
        else
            f_1496_043C(nx, ny, AlistS[index]);
    }
}

void far DoForageAnt(int index)
{
    int x;
    int y;
    int attribute;
    int tile;
    int flags;
    int caste;
    int dir;
    int nx;
    int ny;

    x = AlistX[index];
    y = AlistY[index];
    attribute = AlistT[index];
    if (IsItHole(x, y)) {
        GoInNest(x, y, index);
        return;
    }
    if (SRand32() == 0) {
        AlistM[index] = 0xd;
        return;
    }
    flags = attribute & 0xf8;
    caste = (attribute & 0x78) >> 3;
    if (PherMapA[x >> 1][y >> 1] != 0) {
        AlistM[index] = 0xb;
        return;
    }
    if (caste != 6 && caste != 2) {
        AlistM[index] = f_1383_0976(caste, attribute);
        AlistS[index] = 0;
        return;
    }
    dir = f_1383_0A95(x, y, attribute & 7, attribute);
    if (dir < 0) {
        if (SRand8())
            AlistM[index] = 0;
        else
            AlistM[index] = f_1383_0976(caste, attribute);
        AlistS[index] = 0;
        f_1496_04AC(x >> 1, y >> 1, attribute & 0x80);
        return;
    }
    nx = x + Dx8[dir];
    ny = y + Dy8[dir];
    tile = MapA[nx][ny];
    if (IsItFood(tile) == 1) {
        AlistT[index] = dir | flags | 8;
        LifeA[x][y] = AlistT[index];
        AlistM[index] = 3;
        PickupFoodA(nx, ny);
        AlistS[index] = 200;
        return;
    }
    if (tile > Barrier) {
        AlistT[index] = RandTurn(attribute & 7) | flags;
        LifeA[x][y] = AlistT[index];
        if (SRand16() == 0) {
            AlistM[index] = f_1383_0976(caste, attribute);
            AlistS[index] = 0;
        }
        return;
    }
    tile = LifeA[nx][ny];
    if (tile == 0) {
        AlistT[index] = LifeA[nx][ny] = dir | flags;
        LifeA[x][y] = 0;
        AlistX[index] = nx;
        AlistY[index] = ny;
        if (AlistS[index] != 0) {
            AlistS[index]--;
            if (attribute & 0x80)
                f_1496_0404(nx, ny, AlistS[index]);
            else
                f_1496_03CC(nx, ny, AlistS[index]);
        }
        f_1496_04AC(nx, ny, attribute & 0x80);
        return;
    }
    if (IsYellowAnt(tile) == 1) {
        if ((fd_50F6_04E2 ^ attribute) & 0x80) {
            o25_3BA4_0DFB(1, index);
            return;
        }
        if (fd_50F6_1044 == 1) {
            AlistT[index] = dir | flags;
            LifeA[x][y] = AlistT[index];
            o22_39C7_19E5(x, y, dir);
        }
        AlistT[index] = RandTurn(attribute & 7) | flags;
        LifeA[x][y] = AlistT[index];
        return;
    }
    if (((tile ^ attribute) & 0x80) == 0) {
        AlistT[index] = RandTurn(attribute & 7) | flags;
        LifeA[x][y] = AlistT[index];
        return;
    }
    StartFightA(index, x, y, nx, ny);
}

void far DoRecruitAnt(int index)
{
    int x;
    int y;
    int tile;
    int attribute;
    int flags;
    int dir;
    int nx;
    int ny;

    x = AlistX[index];
    y = AlistY[index];
    attribute = AlistT[index];
    if (IsItHole(x, y)) {
        GoInNest(x, y, index);
        return;
    }
    flags = attribute & 0xf8;
    if (PherMapA[x >> 1][y >> 1] != 0)
        dir = f_1383_0DCC(x, y, attribute & 7);
    else if (attribute > 0x7f)
        dir = f_1383_0FCE(x, y, attribute & 7);
    else
        dir = f_1383_0ECC(x, y, attribute & 7);
    nx = x + Dx8[dir];
    ny = y + Dy8[dir];
    if (MapA[nx][ny] > Barrier) {
        AlistT[index] = SRand8() | flags;
        LifeA[x][y] = AlistT[index];
        return;
    }
    tile = LifeA[nx][ny];
    if (tile == 0) {
        AlistT[index] = LifeA[nx][ny] = dir | flags;
        LifeA[x][y] = 0;
        AlistX[index] = nx;
        AlistY[index] = ny;
        return;
    }
    if (IsYellowAnt(tile)) {
        if ((fd_50F6_04E2 ^ attribute) & 0x80) {
            o25_3BA4_0DFB(1, index);
            return;
        }
        if (fd_50F6_1044) {
            AlistT[index] = dir | flags;
            LifeA[x][y] = AlistT[index];
            o22_39C7_19E5(x, y, dir);
        }
        AlistT[index] = RandTurn(attribute & 7) | flags;
        LifeA[x][y] = AlistT[index];
        return;
    }
    if (((tile ^ attribute) & 0x80) == 0) {
        AlistT[index] = RandTurn(attribute & 7) | flags;
        LifeA[x][y] = AlistT[index];
        return;
    }
    StartFightA(index, x, y, nx, ny);
}

void far GoInNest(int x, int y, int index)
{
    if (x < 0x40) {
        if (ListIndexB >= 500)
            f_0EC1_0081();
        if (ListIndexB >= 500)
            return;
        AddAntToBList(y, 1, (AlistT[index] & 0xf8) + 4, AlistM[index], AlistS[index]);
        if (HoleMapB[y] != 0)
            DigTileB(y, 1);
    } else {
        if (ListIndexR >= 500)
            f_0EC1_0100();
        if (ListIndexR >= 500)
            return;
        AddAntToRList(y, 1, (AlistT[index] & 0xf8) + 4, AlistM[index], AlistS[index]);
        if (HoleMapR[y] != 0)
            DigTileR(y, 1);
    }
    AlistT[index] = 0;
    LifeA[x][y] = 0;
}

void far StartFightA(int ant, int x, int y, int nx, int ny)
{
    int loser;
    int type;
    int winner;

    type = AlistT[ant];
    AlistT[ant] = 0;
    LifeA[x][y] = 0;
    loser = f_0EC1_0291(nx, ny);
    if (loser >= 0) {
        winner = GetWinner(AlistT[loser], type);
        AlistT[loser] = (winner & 0x80) + 0x70;
        LifeA[nx][ny] = (winner & 0x80) + 0x70;
        AlistM[loser] = 0xa;
        AlistS[loser] = winner;
        f_1496_0395(nx, ny, 0x28);
    }
}

static unsigned char near combatLevel[16] = {
    0, 0, 0, 0, 2, 0, 1, 1, 2, 1, 0, 0, 3, 3, 0, 0
};
static unsigned char near combatOdds[16] = {
    5, 2, 7, 3, 8, 5, 9, 4, 3, 1, 5, 2, 7, 6, 8, 5
};

int far GetWinner(int a, int b)
{
    int levelA;
    int levelB;
    int threshold;

    if (fd_3D57_0C14 == 1) {
        fd_50F6_0F3E++;
        if (a & 0x80)
            return b;
        return a;
    }
    levelA = combatLevel[(a & 0x78) >> 3];
    levelB = combatLevel[(b & 0x78) >> 3];
    threshold = combatOdds[(levelA << 2) + levelB];
    if (RRand(10) < threshold) {
        if (a & 0x80) {
            fd_50F6_09FA++;
            fd_50F6_0EFC++;
        } else {
            fd_50F6_0A00++;
            fd_50F6_0F3E++;
        }
        return a;
    }
    if (b & 0x80) {
        fd_50F6_09FA++;
        fd_50F6_0EFC++;
    } else {
        fd_50F6_0A00++;
        fd_50F6_0F3E++;
    }
    return b;
}

void far DoFightA(int index)
{
    int x;
    int y;

    x = AlistX[index];
    y = AlistY[index];
    AlistT[index] = (AlistT[index] & 0xf8) + SRand1(7);
    LifeA[x][y] = AlistT[index];
    if (SRand16() == 0) {
        LifeA[x][y] = AlistS[index];
        AlistT[index] = LifeA[x][y];
        AlistM[Tindex] = f_1383_0976((AlistT[index] & 0x78) >> 3, AlistT[index]);
        AlistS[index] = 0;
        DeadAntHere(x, y, AlistT[index] & 0x80);
    } else if (fd_3D57_07B2 == 1)
        f_0250_4302(x, y, 1);
}

void far DeadAntHere(int x, int y, int type)
{
    int oldX;
    int oldY;
    int otile;

    if (++fd_50F6_0476 >= 100)
        fd_50F6_0476 = 0;
    oldX = fd_50F6_037C[fd_50F6_0476];
    oldY = fd_50F6_0404[fd_50F6_0476];
    otile = MapA[oldX][oldY];
    if (TERRAINset == 0) {
        if (otile >= 0x10 && otile < 0x18)
            MapA[oldX][oldY] = SRand16();
        fd_50F6_037C[fd_50F6_0476] = x;
        fd_50F6_0404[fd_50F6_0476] = y;
        if (MapA[x][y] < 0x18) {
            if (type != 0)
                MapA[x][y] = SRand4() + 0x14;
            else
                MapA[x][y] = SRand4() + 0x10;
        }
    } else {
        if (otile >= 8 && otile < 0x18)
            MapA[oldX][oldY] = (otile - 8) >> 2;
        fd_50F6_037C[fd_50F6_0476] = x;
        fd_50F6_0404[fd_50F6_0476] = y;
        otile = MapA[x][y];
        if (otile < 4) {
            if (type != 0)
                MapA[x][y] = SRand1(2) + otile * 4 + 0xa;
            else
                MapA[x][y] = SRand1(2) + (otile + 2) * 4;
        }
    }
    LifeA[x][y] = 0;
}

int far RandTurn(int dir)
{
    return TurnTab[dir][SRand8()];
}

void far DoAttackAnt(int index)
{
    int x;
    int y;
    int tile;
    int attribute;
    int caste;
    int flags;
    int dir;
    int nx;
    int ny;

    x = AlistX[index];
    y = AlistY[index];
    attribute = AlistT[index];
    if (IsItHole(x, y)) {
        GoInNest(x, y, index);
        return;
    }
    caste = (attribute & 0x78) >> 3;
    if (fd_3D57_0074[caste] == 1)
        attribute = (fd_3D57_0094[caste] << 3) | (attribute & 0x87);
    flags = attribute & 0xf8;
    dir = f_1383_0C2A(x, y, attribute & 7, attribute ^ 0x80);
    nx = x + Dx8[dir];
    ny = y + Dy8[dir];
    if (MapA[nx][ny] > Barrier) {
        AlistT[index] = RandTurn(attribute & 7) | flags;
        LifeA[x][y] = AlistT[index];
        return;
    }
    tile = LifeA[nx][ny];
    if (tile == 0) {
        AlistT[index] = LifeA[nx][ny] = dir | flags;
        LifeA[x][y] = 0;
        AlistX[index] = nx;
        AlistY[index] = ny;
        return;
    }
    if (IsYellowAnt(tile) == 1) {
        if ((fd_50F6_04E2 ^ attribute) & 0x80) {
            o25_3BA4_0DFB(1, index);
            return;
        }
        AlistT[index] = RandTurn(attribute & 7) | flags;
        LifeA[x][y] = AlistT[index];
        return;
    }
    if (((tile ^ attribute) & 0x80) == 0) {
        AlistT[index] = RandTurn(attribute & 7) | flags;
        LifeA[x][y] = AlistT[index];
        return;
    }
    StartFightA(index, x, y, nx, ny);
}

int far IsItHole(int x, int y)
{
    int tile;

    if (IsValidA(x, y) == 0)
        return 0;
    if (TERRAINset == 0) {
        if (MapA[x][y] == 0x50)
            return 1;
        return 0;
    }
    tile = MapA[x][y];
    if (tile < 0x80)
        return 0;
    if (tile > 0x8f)
        return 0;
    return 1;
}

int far IsItFood(int tile)
{
    if (TERRAINset == 0) {
        if (tile < 0x48 || tile > 0x4b)
            return 0;
        return 1;
    }
    if (tile < 0x18 || tile > 0x27)
        return 0;
    return 1;
}
