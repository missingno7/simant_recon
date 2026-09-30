/* Overlay section S08, code frame 35F5: world generation (RandWorld unit). */

extern int far fd_3D57_07CC;
extern int far fd_50F6_0FBA;
extern int far fd_50F6_0FFE;
extern int far fd_50F6_104C;
extern int far fd_50F6_073A;
extern int far fd_50F6_06AA;
extern int far fd_50F6_0850;
extern int far fd_50F6_07C8;

extern unsigned char far MapA[128][64];
extern unsigned char far MapB[64][64];
extern unsigned char far MapR[64][64];
extern unsigned char far ExitMapB[64][64];
extern unsigned char far ExitMapR[64][64];
extern unsigned char far LifeA[128][64];
extern unsigned char far LifeB[64][64];
extern unsigned char far LifeR[64][64];
extern unsigned char far fd_3E1D_D09F[64][32];
extern unsigned char far fd_3E1D_D89F[64][32];
extern unsigned char far fd_3E1D_E09F[64][32];
extern unsigned char far fd_3E1D_E89F[64][32];
extern unsigned char far fd_3E1D_F09F[64][32];
extern unsigned char far fd_4DA7_0000[64][32];
extern unsigned char far HoleMapB[64];
extern unsigned char far HoleMapR[64];
extern int far TERRAINset;
extern int far fd_50F6_0EAC;
extern long far fd_50F6_10A2;
extern long far fd_50F6_108E;
extern long far fd_50F6_1082;
extern long far fd_50F6_1068;
extern int far fd_50F6_0224;
extern int far fd_50F6_0232;
extern int far fd_50F6_020E;
extern int far fd_50F6_0200;
extern int far fd_50F6_10C0;
extern int far fd_50F6_10B2;
extern int far fd_50F6_0242;
extern int far fd_50F6_035E;
extern int far fd_50F6_036C;
extern int far fd_3D57_02B4[2];
extern int far fd_3D57_02B8[2];
extern int far FoodB;
extern int far FoodR;
extern int far fd_50F6_1040;
extern int far HealthB;
extern int far HealthR;
extern unsigned long far fd_50F6_0472;
extern int far fd_50F6_09FA;
extern int far fd_50F6_0A00;
extern int far Cycle;
extern int far fd_50F6_0FFA;
extern int far fd_50F6_0FB6;
extern int far fd_50F6_0508[2];
extern int far fd_50F6_0596[2];
extern int far fd_50F6_06A6[2];
extern int far fd_50F6_072E[2];

extern void far SetSRandSeed(unsigned long seed);
extern void far f_0CDB_0000(void);
extern void far o18_384C_0000(int width, int kind);
extern int far SRand1(int range);
extern int far SRand2(void);
extern int far SRand4(void);
extern int far SRand8(void);
extern int far SRand16(void);
extern int far SRand64(void);
extern int far SGRand(int range);
extern void far MakeNewHoleB(int x);
extern void far MakeNewHoleR(int x);
extern void far f_0EC1_0719(void);
extern void far f_0EC1_07C1(void);
extern void far f_0EC1_07D4(void);
extern void far o24_39C7_01B8(int a);
extern void far f_0BE8_0002(void);
extern void far f_0250_006E(int a, int b, int columns, int rows);

extern int far fd_50F6_07CA[2];
extern int far fd_50F6_07BC[2];
extern int far fd_50F6_105E;
extern unsigned long far fd_50F6_0214;
extern unsigned long far fd_50F6_0204;
extern int far fd_50F6_0228;
extern int far fd_50F6_0478;
extern int far fd_50F6_0504;
extern int far fd_50F6_0366;
extern int far fd_50F6_0376;
extern int far fd_3D57_0C44;
extern int far fd_3D57_0C18;
extern int far fd_3D57_0C16;
extern int far fd_3D57_0C14;
extern unsigned long far fd_50F6_0C26;
extern int far fd_50F6_032E;
extern int far fd_3D57_07C8;
extern int far fd_50F6_035C;
extern int far fd_3E1D_0000[16][12];
extern int far fd_3D57_0C24;
extern int far MePlane;
extern int far MeLocX;
extern int far MeLocY;

extern void far o06_35F5_0000(void);
extern void far f_0798_0F0D(void);
extern int far RRand(int range);
extern unsigned char far fd_3D57_00A4[12][16];
extern unsigned char far fd_3D57_0164[12][16];
void far AddBlackAnts(int count);
void far AddRedAnts(int count);
extern void far FullCount(void);
extern void far f_015B_053C(int plane);

static char tutorialX[30] = {
    0, 1, 2, 5, 7, 2, 2, 7, 8, 6, 3, 7, 7, 10, 11,
    6, 8, 10, 11, 9, 10, 11, 9, 10, 11, 9, 10, 10, 10, 11
};
static char tutorialY[30] = {
    0, 0, 0, 0, 0, 1, 2, 2, 2, 3, 4, 4, 5, 5, 5,
    6, 6, 6, 6, 7, 7, 7, 8, 8, 8, 9, 9, 10, 11, 11
};
static char tutorialBlack[30] = {
    2, 4, 6, 5, 7, 4, 2, 2, 3, 6, 1, 7, 4, 5, 3,
    1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 5, 0, 0, 0, 0
};
static char tutorialRed[30] = {
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 4, 6, 3, 4, 6, 5, 6, 3, 0, 4, 3, 2, 5
};
extern char far Dx8[];
extern char far Dy8[];
extern int far DigTileThemB(int x, int y);
extern void far DigTileB(int x, int y);
extern int far DigTileThemR(int x, int y);
extern int far fd_50F6_049A;
extern int far fd_3D57_0C22;
extern int far fd_50F6_104E;
extern int far fd_3D57_07BE;
extern int far fd_50F6_04E2;
extern int far fd_50F6_0A06;
extern int far fd_50F6_0F26;
extern int far fd_50F6_0F0E;
extern int far fd_50F6_04C2;
extern void far SetMyHealth(int health);
extern int far * far fd_50F6_0B22;
extern int far fd_3D57_02BC[2];
extern int far ListIndexA;
extern unsigned char far fd_3E1D_AD3B[1000];
extern unsigned char far fd_3E1D_A952[1000];
extern unsigned char far fd_3E1D_B124[1000];
extern unsigned char far fd_3E1D_BAEC[500];
extern unsigned char far fd_3E1D_B8F7[500];
extern unsigned char far fd_3E1D_BCE1[500];
extern unsigned char far fd_3E1D_C4B5[500];
extern unsigned char far fd_3E1D_C2C0[500];
extern unsigned char far fd_3E1D_C6AA[500];
extern void far AddAntToAList(int x, int y, int type, int kind, int a);
extern int far SRand128(void);
extern int far SRand256(void);
extern void far myBeginSound(int sound, int a, int b);
extern void far AddAntToBList(int x, int y, int type, int a, int b);
extern void far AddAntToRList(int x, int y, int type, int a, int b);
extern void far SetMyLife(int plane, int x, int y, int type, int dir, int code);
extern void far o22_39C7_07FD(int plane, int x, int y);
extern void far DigTileR(int x, int y);

void far DigOutBNest(int count);
void far ClrArrays(void);
void far DigOutRNest(int count);
void far InitYelloAnt(void);
void far PlaceBlackQueen(void);
void far MakeBlkQueen(int x, int y, int dir);
void far MakeRedQueen(int x, int y, int dir);
void far PlaceRedQueen(void);
void far AddFood(int count, int sound);

void far InitSimVars(void)
{
    fd_3D57_07CC = 1;
    fd_50F6_0FBA = 30;
    fd_50F6_0FFE = 30;
    fd_50F6_104C = 0;
    fd_50F6_073A = 0;
    fd_50F6_06AA = 0;
    fd_50F6_0850 = 0;
    fd_50F6_07C8 = 0;
}

/* DRAFT, not claimed (RandWorld).  MSC 6.00A and the bound C2L report C4203 for it
 * (1456 bytes, 0.70 similar).  Under 6.00AX /Oe /Og /Zi (worker big) this Win16-shaped text
 * is 1371 bytes (0.98): the dead store 'y = 0' stays (mov [bp-4],ax, y shares n's slot, which
 * is read) and loop 2 then keeps count<<6 in DI instead of the [bp-0Eh] temp, which stops the
 * cross-jump of the two MapR tails.  Without y ([count][0]) the whole function matches except
 * loop 1's entry: 'mov [bp-2],0 / mov di,[bp-2]' instead of the original 'sub ax,ax / mov di,ax'
 * (4 bytes).  With a single [count][y] use only the y store remains (3 bytes).  A store is
 * dropped only when its frame slot is never read (the y store vanishes in small functions),
 * so the original must have placed y in an unread slot; no source form tried does that. */
void far RandWorld(unsigned seed, int blackSize, int redSize, int mapWidth, int mapKind)
{
    int count, y, roll, tries, lim1, lim2, x, n;

    SetSRandSeed(seed);
    f_0CDB_0000();
    o18_384C_0000(mapWidth, mapKind);

    blackSize += blackSize >> 2;
    redSize += redSize >> 2;

    y = 0;
    for (count = 0; count < 64; count++) {
        for (x = 0; x < 64; x++) {
            MapB[count][x] = 0x2e;
            MapR[count][x] = 0x2e;
            ExitMapB[count][x] = 0;
            ExitMapR[count][x] = 0;
            LifeB[count][x] = 0;
            LifeR[count][x] = 0;
            LifeA[count][x] = 0;
            LifeA[count + 64][x] = 0;
        }
    }

    for (count = 0; count < 64; count++) {
        if (TERRAINset == 0) {
            MapB[count][y] = SRand4() + 0x1c;
            MapR[count][y] = SRand4() + 0x1c;
        } else {
            if (mapKind > 3)
                MapB[count][y] = SRand1(2) + 0x1c;
            else
                MapB[count][y] = 0x1e;
            if (mapKind > 3)
                MapR[count][y] = SRand1(2) + 0x1c;
            else
                MapR[count][y] = 0x1e;
        }
        ExitMapB[count][y] = 0xff;
        ExitMapR[count][y] = 0xff;
    }

    for (count = 0; count < 64; count++) {
        for (x = 0; x < 32; x++) {
            fd_3E1D_D89F[count][x] = 0;
            fd_3E1D_D09F[count][x] = 0;
            fd_3E1D_E09F[count][x] = 0;
            fd_3E1D_E89F[count][x] = 0;
            fd_3E1D_F09F[count][x] = 0;
            fd_4DA7_0000[count][x] = 0;
        }
    }

    tries = 0;
    lim1 = SRand1(6) + 7;
    lim2 = 15 - SRand2();
    n = blackSize;
    while (n > 0) {
        n--;
        count = SGRand(0x80);
        x = SRand64();
        if (MapA[count][x] < 0x50) {
            if (LifeA[count][x] != 0) {
                tries++;
                if (tries < 50)
                    n++;
            } else {
                roll = SRand16();
                if (roll < lim1)
                    LifeA[count][x] = SRand8() + 0x10;
                else if (roll < lim2)
                    LifeA[count][x] = SRand8() + 0x30;
                else if (SRand2())
                    LifeA[count][x] = SRand8() + 0x20;
                else
                    LifeA[count][x] = SRand8() + 0x40;
            }
        }
    }

    tries = 0;
    lim1 = SRand1(6) + 7;
    lim2 = 15 - SRand2();
    n = redSize;
    while (n > 0) {
        n--;
        count = 0x7f - SGRand(0x80);
        x = SRand64();
        if (MapA[count][x] < 0x50) {
            if (LifeA[count][x] != 0) {
                tries++;
                if (tries < 50)
                    n++;
            } else {
                roll = SRand16();
                if (roll < lim1)
                    LifeA[count][x] = SRand8() - 0x70;
                else if (roll < lim2)
                    LifeA[count][x] = SRand8() - 0x50;
                else if (SRand2())
                    LifeA[count][x] = SRand8() - 0x60;
                else
                    LifeA[count][x] = SRand8() - 0x40;
            }
        }
    }

    for (x = 0; x < 64; x++) {
        HoleMapB[x] = 0;
        HoleMapR[x] = 0;
    }

    if (fd_50F6_0EAC != 2 || blackSize >= 1)
        MakeNewHoleB(0x20);
    if (redSize >= 1)
        MakeNewHoleR(0x20);

    fd_50F6_10A2 = 0;
    fd_50F6_108E = 0;
    fd_50F6_1082 = 0;
    fd_50F6_1068 = 0;
    fd_50F6_0224 = 0;
    fd_50F6_0232 = 0;
    fd_50F6_020E = 0;
    fd_50F6_0200 = 0;
    fd_50F6_10C0 = 0;
    fd_50F6_10B2 = 0;
    fd_50F6_0242 = 0x40;

    if (blackSize > 1)
        DigOutBNest(blackSize << 4);
    if (redSize > 1)
        DigOutRNest(redSize << 4);

    f_0EC1_0719();
    f_0EC1_07C1();
    f_0EC1_07D4();

    fd_50F6_035E = 0;
    fd_50F6_036C = 0;
    fd_3D57_02B4[0] = -1;
    fd_3D57_02B4[1] = -1;
    fd_3D57_02B8[0] = -1;
    fd_3D57_02B8[1] = -1;

    if (redSize > 0)
        PlaceRedQueen();
    if (blackSize > 0)
        PlaceBlackQueen();
    InitYelloAnt();

    FoodB = 0;
    FoodR = 0;
    fd_50F6_1040 = 0;
    if (fd_50F6_0EAC != 3)
        AddFood(-1, 0);

    HealthB = 100;
    HealthR = 100;

    fd_50F6_0472 = 0;
    fd_50F6_09FA = 0;
    fd_50F6_0A00 = 0;
    Cycle = 0;

    o24_39C7_01B8(0);
    f_0BE8_0002();
    f_0250_006E(0, 0, fd_50F6_0FB6, fd_50F6_0FFA);

    fd_50F6_0508[0] = 0x40;
    fd_50F6_0596[0] = 0x40;
    fd_50F6_0508[1] = 0x20;
    fd_50F6_0596[1] = 0x20;
    fd_50F6_06A6[0] = 0x20;
    fd_50F6_072E[0] = 0x20;
    fd_50F6_06A6[1] = 1;
    fd_50F6_072E[1] = 1;
}

void far RandYard(void)
{
    int i;

    ClrArrays();
    o24_39C7_01B8(1);
    f_0798_0F0D();

    *fd_50F6_07CA = 11;
    *fd_50F6_07BC = 11;
    *(fd_50F6_07CA + 1) = 8;
    *(fd_50F6_07BC + 1) = 8;

    o06_35F5_0000();

    fd_50F6_105E = -1;
    fd_50F6_0214 = 0;
    fd_50F6_0204 = 0;
    fd_50F6_0228 = 0;
    fd_50F6_0478 = 0;
    fd_50F6_0504 = 0;
    fd_50F6_0366 = 0;
    fd_50F6_0376 = 0;
    fd_3D57_0C44 = 0;
    fd_3D57_0C18 = 0;
    fd_3D57_0C16 = 0;
    fd_3D57_0C14 = 0;
    fd_50F6_0C26 = 0L;

    if (fd_50F6_0EAC <= 1)
        fd_50F6_032E = 2;
    else
        fd_50F6_032E = 1;
    fd_3D57_07C8 = fd_50F6_032E;
    fd_50F6_035C = 0;

    for (i = 0; i < 192; i++)
        fd_3E1D_0000[0][i] = (RRand(0x7fff) - 0xc000) & 0x7fff;

    if (fd_50F6_0EAC == 2)
        RandWorld(fd_3E1D_0000[*(fd_50F6_07CA + 1)][*fd_50F6_07CA], fd_3D57_0C24 = 0, 1, *fd_50F6_07BC, *(fd_50F6_07BC + 1));
    else
        RandWorld(fd_3E1D_0000[*(fd_50F6_07CA + 1)][*fd_50F6_07CA], fd_3D57_0C24 = 1, 1, *fd_50F6_07BC, *(fd_50F6_07BC + 1));

    if (MePlane <= 1) {
        fd_50F6_0596[0] = MeLocX;
        fd_50F6_0596[1] = MeLocY;
    } else if (MePlane == 2) {
        fd_50F6_06A6[0] = MeLocX;
        fd_50F6_06A6[1] = MeLocY;
    } else {
        fd_50F6_072E[0] = MeLocX;
        fd_50F6_072E[1] = MeLocY;
    }
}

void far GenerateTutorial(void)
{
    int i;

    fd_50F6_0EAC = 1;
    RandYard();
    AddBlackAnts(32);
    AddRedAnts(32);
    FullCount();
    fd_50F6_0EAC = 2;
    f_015B_053C(MePlane);
    for (i = 0; i < 30; i++) {
        fd_3D57_00A4[tutorialX[i]][tutorialY[i]] = tutorialBlack[i] << 5;
        fd_3D57_0164[tutorialX[i]][tutorialY[i]] = tutorialRed[i] << 5;
    }
}

void far DigOutBNest(int count)
{
    int dir, y, x, newX, newY;

    dir = 4;
    y = 1;
    x = 0x20;
    DigTileB(x, y);
    for (; count != 0; count--) {
        dir = (SRand1(5) + dir - 3) & 7;
        newX = x + Dx8[dir];
        newY = y + Dy8[dir];
        if (newX < 1) {
            newX = 1;
            dir = 2;
        } else if (newX > 0x3e) {
            newX = 0x3e;
            dir = 6;
        }
        if (newY < 2) {
            newY = 1;
            dir = 4;
        } else if (newY > 0x3e) {
            newY = 0x3e;
            dir = 0;
        }
        if (DigTileThemB(newX, newY) == 1) {
            x = newX;
            y = newY;
            if (y == 1 && HoleMapB[x] == 0)
                MakeNewHoleB(newX);
        }
    }
}

void far DigOutRNest(int count)
{
    int dir, y, x, newX, newY;

    dir = 4;
    y = 1;
    x = 0x20;
    DigTileR(x, y);
    for (; count != 0; count--) {
        dir = (SRand1(5) + dir - 3) & 7;
        newX = x + Dx8[dir];
        newY = y + Dy8[dir];
        if (newX < 1) {
            newX = 1;
            dir = 2;
        } else if (newX > 0x3e) {
            newX = 0x3e;
            dir = 6;
        }
        if (newY < 2) {
            newY = 1;
            dir = 4;
        } else if (newY > 0x3e) {
            newY = 0x3e;
            dir = 0;
        }
        if (DigTileThemR(newX, newY) == 1) {
            x = newX;
            y = newY;
            if (y == 1 && HoleMapR[x] == 0)
                MakeNewHoleR(newX);
        }
    }
}

void far InitYelloAnt(void)
{
    fd_50F6_049A = 0;
    fd_3D57_0C22 = 0xfd;
    if (fd_50F6_104E != 0) {
        fd_50F6_104E = 0;
        fd_3D57_07BE = -1;
    }
    SetMyHealth(100);

    if (fd_50F6_0EAC != 3) {
        fd_50F6_04E2 = 0;
        fd_50F6_0A06 = 0;
        if (fd_50F6_0EAC != 2 || fd_3D57_0C24 != 0) {
            SetMyLife(2, fd_50F6_0F0E, fd_50F6_0F26, 0x10, 2, 0xff);
        } else {
            int x, y;

            x = 0x40;
            y = 0x20;
            {
                int col, count, tries;

                for (tries = 0; tries < 100; tries++) {
                    count = SRand16() - SRand16() + 0x20;
                    col = SRand8() - SRand8() + 0x20;
                    if (MapA[count][col] < 0x10) {
                        x = count;
                        y = col;
                        break;
                    }
                }
            }
            SetMyLife(1, x, y, 0x40, 2, 0xff);
        }
        goto done;
    }
    MePlane = 1;
    fd_50F6_04E2 = 0;
    fd_50F6_0A06 = 2;
    MeLocX = 0x40;
    MeLocY = 0x20;
    fd_50F6_04C2 = 0x10;

done:
    o22_39C7_07FD(MePlane, MeLocX, MeLocY);
}

void far PlaceBlackQueen(void)
{
    int x, y, count, wobble;

    count = SRand4() + 7;
    wobble = 0;
    x = 0x20;
    for (y = 1; y < count; y++) {
        DigTileB(x, y);
        if (SRand2() == 0)
            wobble = SRand1(3) - 1;
        if (wobble + x >= 8 && wobble + x <= 0x38)
            x += wobble;
    }
    for (count = 0; count < 2; count++) {
        DigTileB(x, y);
        x++;
        y++;
    }
    DigTileB(x, y);
    fd_3D57_02B4[0] = x;
    fd_3D57_02B4[1] = y;
    fd_50F6_0F0E = x;
    fd_50F6_0F26 = y;
    MakeBlkQueen(x + 2, y, 2);
}

void far MakeBlkQueen(int x, int y, int dir)
{
    int d;

    d = dir ^ 4;
    DigTileB(x, y);
    DigTileB(x + Dx8[d], y + Dy8[d]);
    DigTileB(x + 2 * Dx8[d], y + 2 * Dy8[d]);
    AddAntToBList(x, y, dir + 0x60, 9, 0);
    AddAntToBList(x + Dx8[d], y + Dy8[d], dir + 0x68, 9, 0);
    fd_50F6_035E++;
}

void far PlaceRedQueen(void)
{
    int x, y, count, wobble;

    count = SRand4() + 7;
    x = 0x20;
    for (y = 1; y < count; y++) {
        DigTileR(x, y);
        wobble = SRand1(3) - 1;
        if (wobble + x >= 8 && wobble + x <= 0x38)
            x += wobble;
    }
    for (count = 0; count < 2; count++) {
        DigTileR(x, y);
        x++;
        y++;
    }
    DigTileR(x, y);
    fd_3D57_02B8[0] = x;
    fd_3D57_02B8[1] = y;
    MakeRedQueen(x + 2, y, 2);
}

void far MakeRedQueen(int x, int y, int dir)
{
    int d;

    d = dir ^ 4;
    DigTileR(x, y);
    DigTileR(x + Dx8[d], y + Dy8[d]);
    DigTileR(x + 2 * Dx8[d], y + 2 * Dy8[d]);
    AddAntToRList(x, y, dir + 0xE0, 9, 0);
    AddAntToRList(x + Dx8[d], y + Dy8[d], dir + 0xE8, 9, 0);
    fd_50F6_036C++;
}

int far fracSIN(int angle)
{
    int index;
    int value;

    index = angle & 0x7f;
    if (index > 0x3f)
        index = 0x80 - index;

    if (index == 0x40)
        value = 0x7fff;
    else {
        index &= 0x3f;
        value = fd_50F6_0B22[index];
    }
    if ((angle & 0xff) > 0x7f)
        value = -value;

    return value;
}

int far fracCOS(int angle)
{
    return fracSIN(angle + 0x40);
}

void far AddFood(int count, int sound)
{
    int x, y, angle, r, i, radius, cx, cy;

    if (sound == 1)
        myBeginSound(0x20, 0, 0x7e);
    if (count < 0) {
        cx = 0x40;
        cy = SRand1(0x30) + 8;
        count = 200;
    } else {
        cx = SRand128();
        cy = SRand64();
    }
    fd_3D57_02BC[0] = cx;
    fd_3D57_02BC[1] = cy;
    radius = SRand8() + 5;
    for (i = 0; i < count; i++) {
        angle = SRand256();
        r = SRand1(radius);
        x = (long)r * fracCOS(angle) / 0x7fffL + cx;
        y = (long)r * fracSIN(angle) / 0x7fffL + cy;
        if (x >= 0 && x <= 0x7f && y >= 0 && y <= 0x3f && LifeA[x][y] == 0) {
            angle = MapA[x][y];
            if (TERRAINset != 0) {
                if (angle < 0x18) {
                    if (angle < 4)
                        MapA[x][y] = (angle + 6) << 2;
                    else
                        MapA[x][y] = ((angle - 8) & 0xfc) + 0x18;
                    fd_50F6_1040++;
                } else if (angle < 0x28 && angle % 4 < 3) {
                    MapA[x][y]++;
                    fd_50F6_1040++;
                }
            } else {
                if (angle < 0x18) {
                    MapA[x][y] = 0x48;
                    fd_50F6_1040++;
                } else if (angle >= 0x48 && angle < 0x4b) {
                    MapA[x][y]++;
                    fd_50F6_1040++;
                }
            }
        }
    }
}

void far AddBlackAnts(int count)
{
    int x;
    int y;
    int base;
    int kind;
    int type;

    for (x = 0; x < 64; x++) {
        for (y = 16; y < 48; y++) {
            if (MapA[x][y] < 0x50 && LifeA[x][y] == 0) {
                switch (SRand1(10)) {
                case 0:
                case 1:
                case 2:
                case 3:
                    base = 0x30;
                    kind = 2;
                    break;
                default:
                    base = 0x10;
                    kind = 4;
                    break;
                }
                type = SRand8() + base;
                LifeA[x][y] = type;
                AddAntToAList(x, y, type, kind, 0);
                if (--count <= 0)
                    return;
                if (ListIndexA >= 1000)
                    return;
            }
        }
    }
}

void far AddRedAnts(int count)
{
    int x;
    int y;
    int base;
    int kind;
    int type;

    for (x = 127; x >= 64; x--) {
        for (y = 16; y < 48; y++) {
            if (MapA[x][y] < 0x50 && LifeA[x][y] == 0) {
                switch (SRand1(10)) {
                case 0:
                case 1:
                case 2:
                case 3:
                    base = 0x30;
                    kind = 2;
                    break;
                default:
                    base = 0x10;
                    kind = 4;
                    break;
                }
                type = SRand8() + base + 0x80;
                LifeA[x][y] = type;
                AddAntToAList(x, y, type, kind, 0);
                if (--count <= 0)
                    return;
                if (ListIndexA >= 1000)
                    return;
            }
        }
    }
}

int far o08_35F5_11F0(int x, int y)
{
    int col, row;

    if (x > 0x7f)
        col = 0;
    else if (x < 0)
        col = 0x7f;
    else
        col = x;
    if (y > 0x3f)
        row = 0;
    else if (y < 0)
        row = 0x3f;
    else
        row = y;
    return MapA[col][row];
}

/* DRAFT, not claimed (ClrArrays): identical except the target's leading
 * 'jmp <outer test>' of the first loop (2 bytes; 379 vs 381). */
void far ClrArrays(void)
{
    int x, y;

    for (x = 0; x < 128; x++) {
        for (y = 0; y < 64; y++) {
            MapA[x][y] = 0;
            LifeA[x][y] = 0;
        }
    }
    for (x = 0; x < 64; x++) {
        for (y = 0; y < 64; y++) {
            MapB[x][y] = 0;
            MapR[x][y] = 0;
            ExitMapB[x][y] = 0;
            ExitMapR[x][y] = 0;
            LifeB[x][y] = 0;
            LifeR[x][y] = 0;
        }
    }
    for (x = 0; x < 64; x++) {
        for (y = 0; y < 32; y++) {
            fd_3E1D_D89F[x][y] = 0;
            fd_3E1D_D09F[x][y] = 0;
            fd_3E1D_E09F[x][y] = 0;
            fd_3E1D_E89F[x][y] = 0;
            fd_3E1D_F09F[x][y] = 0;
            fd_4DA7_0000[x][y] = 0;
        }
    }
    for (y = 0; y < 1000; y++) {
        fd_3E1D_AD3B[y] = 0;
        fd_3E1D_A952[y] = 0;
        fd_3E1D_B124[y] = 0;
    }
    for (y = 0; y < 500; y++) {
        fd_3E1D_BAEC[y] = 0;
        fd_3E1D_B8F7[y] = 0;
        fd_3E1D_BCE1[y] = 0;
        fd_3E1D_C4B5[y] = 0;
        fd_3E1D_C2C0[y] = 0;
        fd_3E1D_C6AA[y] = 0;
    }
    for (y = 0; y < 12; y++) {
        for (x = 0; x < 16; x++) {
            fd_3D57_00A4[y][x] = 0;
            fd_3D57_0164[y][x] = 0;
        }
    }
}

/* SCAFFOLD BEGIN: context only, not reconstruction */
/* SCAFFOLD END */
