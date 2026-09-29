/* Overlay section S08, code frame 35F5: world generation (RandWorld unit). */

extern int far fd_3D57_07CC;
extern int far fd_50F6_0FBA;
extern int far fd_50F6_0FFE;
extern int far fd_50F6_104C;
extern int far fd_50F6_073A;
extern int far fd_50F6_06AA;
extern int far fd_50F6_0850;
extern int far fd_50F6_07C8;

extern unsigned char far fd_3E1D_0180[128][64];
extern unsigned char far fd_3E1D_2180[64][64];
extern unsigned char far fd_3E1D_3180[64][64];
extern unsigned char far fd_3E1D_4180[64][64];
extern unsigned char far fd_3E1D_5180[64][64];
extern unsigned char far fd_3E1D_6180[128][64];
extern unsigned char far fd_3E1D_8180[64][64];
extern unsigned char far fd_3E1D_9180[64][64];
extern unsigned char far fd_3E1D_D09F[64][32];
extern unsigned char far fd_3E1D_D89F[64][32];
extern unsigned char far fd_3E1D_E09F[64][32];
extern unsigned char far fd_3E1D_E89F[64][32];
extern unsigned char far fd_3E1D_F09F[64][32];
extern unsigned char far fd_4DA7_0000[64][32];
extern unsigned char far fd_3D57_0224[64];
extern unsigned char far fd_3D57_0264[64];
extern int far fd_50F6_0F24;
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
extern int far fd_50F6_1050;
extern int far fd_50F6_1060;
extern int far fd_50F6_1040;
extern int far fd_50F6_10BE;
extern int far fd_50F6_01FE;
extern unsigned long far fd_50F6_0472;
extern int far fd_50F6_09FA;
extern int far fd_50F6_0A00;
extern int far fd_50F6_0F08;
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
extern int far f_0093_002B(int range);
extern void far MakeNewHoleB(int x);
extern void far f_14EE_0367(int x);
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
extern int far fd_50F6_048C;
extern int far fd_50F6_047C;
extern int far fd_50F6_048A;

extern void far o06_35F5_0000(void);
extern void far f_0798_0F0D(void);
extern int far RRand(int range);
extern unsigned char far fd_3D57_00A4[12][16];
extern unsigned char far fd_3D57_0164[12][16];
void far o08_35F5_1080(int count);
void far o08_35F5_1136(int count);
extern void far f_0BE8_038F(void);
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
extern char far fd_3D57_0000[];
extern char far fd_3D57_0008[];
extern int far DigTileThemB(int x, int y);
extern void far f_14EE_0519(int x, int y);
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
extern void far f_10F7_1DD3(int health);
extern int far * far fd_50F6_0B22;
extern int far fd_3D57_02BC[2];
extern int far fd_50F6_0D6A;
extern unsigned char far fd_3E1D_AD3B[1000];
extern unsigned char far fd_3E1D_A952[1000];
extern unsigned char far fd_3E1D_B124[1000];
extern unsigned char far fd_3E1D_BAEC[500];
extern unsigned char far fd_3E1D_B8F7[500];
extern unsigned char far fd_3E1D_BCE1[500];
extern unsigned char far fd_3E1D_C4B5[500];
extern unsigned char far fd_3E1D_C2C0[500];
extern unsigned char far fd_3E1D_C6AA[500];
extern void far f_0EC1_0557(int x, int y, int type, int kind, int a);
extern int far SRand128(void);
extern int far SRand256(void);
extern void far f_00DF_00E8(int sound, int a, int b);
extern void far f_0EC1_05D4(int x, int y, int type, int a, int b);
extern void far f_0EC1_0651(int x, int y, int type, int a, int b);
extern void far f_10F7_0A44(int plane, int x, int y, int type, int dir, int code);
extern void far o22_39C7_07FD(int plane, int x, int y);
extern void far f_14EE_0647(int x, int y);

void far DigOutBNest(int count);
/* DRAFT, not claimed (ClrArrays): only frame (4 vs 2) and a leading jmp to the first
 * outer-loop test differ. */
void far o08_35F5_1240(void);
void far o08_35F5_0923(int count);
void far o08_35F5_0A00(void);
void far PlaceBlackQueen(void);
void far o08_35F5_0C4C(int x, int y, int dir);
void far o08_35F5_0DA0(int x, int y, int dir);
void far o08_35F5_0D12(void);
/* DRAFT, not claimed (AddFood): register allocation differs (target keeps x in [bp-2],
 * y in DI, (long)r CSE in SI:DI, far address CSE at [bp-16h]); 414 vs 427 bytes. */
void far AddFood(int count, int sound);

void far o08_35F5_0000(void)
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

/* DRAFT, not claimed (RandWorld): MSC 6.00 reports C4203 'function too large for
 * global optimizations' for this body, so it compiles without /Oe/Og loop and register
 * shape.  The original was globally optimised (rotated loops, SI/DI, hoisted SEG). */
void far o08_35F5_0050(unsigned seed, int blackSize, int redSize, int mapWidth, int mapKind)
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
            fd_3E1D_2180[count][x] = 0x2e;
            fd_3E1D_3180[count][x] = 0x2e;
            fd_3E1D_4180[count][x] = 0;
            fd_3E1D_5180[count][x] = 0;
            fd_3E1D_8180[count][x] = 0;
            fd_3E1D_9180[count][x] = 0;
            fd_3E1D_6180[count][x] = 0;
            fd_3E1D_6180[count + 64][x] = 0;
        }
    }

    for (count = 0; count < 64; count++) {
        if (fd_50F6_0F24 == 0) {
            fd_3E1D_2180[count][y] = SRand4() + 0x1c;
            fd_3E1D_3180[count][y] = SRand4() + 0x1c;
        } else {
            if (mapKind > 3)
                fd_3E1D_2180[count][y] = SRand1(2) + 0x1c;
            else
                fd_3E1D_2180[count][y] = 0x1e;
            if (mapKind > 3)
                fd_3E1D_3180[count][y] = SRand1(2) + 0x1c;
            else
                fd_3E1D_3180[count][y] = 0x1e;
        }
        fd_3E1D_4180[count][y] = 0xff;
        fd_3E1D_5180[count][y] = 0xff;
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
        count = f_0093_002B(0x80);
        x = SRand64();
        if (fd_3E1D_0180[count][x] < 0x50) {
            if (fd_3E1D_6180[count][x] != 0) {
                tries++;
                if (tries < 50)
                    n++;
            } else {
                roll = SRand16();
                if (roll < lim1)
                    fd_3E1D_6180[count][x] = SRand8() + 0x10;
                else if (roll < lim2)
                    fd_3E1D_6180[count][x] = SRand8() + 0x30;
                else if (SRand2())
                    fd_3E1D_6180[count][x] = SRand8() + 0x20;
                else
                    fd_3E1D_6180[count][x] = SRand8() + 0x40;
            }
        }
    }

    tries = 0;
    lim1 = SRand1(6) + 7;
    lim2 = 15 - SRand2();
    n = redSize;
    while (n > 0) {
        n--;
        count = 0x7f - f_0093_002B(0x80);
        x = SRand64();
        if (fd_3E1D_0180[count][x] < 0x50) {
            if (fd_3E1D_6180[count][x] != 0) {
                tries++;
                if (tries < 50)
                    n++;
            } else {
                roll = SRand16();
                if (roll < lim1)
                    fd_3E1D_6180[count][x] = SRand8() - 0x70;
                else if (roll < lim2)
                    fd_3E1D_6180[count][x] = SRand8() - 0x50;
                else if (SRand2())
                    fd_3E1D_6180[count][x] = SRand8() - 0x60;
                else
                    fd_3E1D_6180[count][x] = SRand8() - 0x40;
            }
        }
    }

    for (x = 0; x < 64; x++) {
        fd_3D57_0224[x] = 0;
        fd_3D57_0264[x] = 0;
    }

    if (fd_50F6_0EAC != 2 || blackSize >= 1)
        MakeNewHoleB(0x20);
    if (redSize >= 1)
        f_14EE_0367(0x20);

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
        o08_35F5_0923(redSize << 4);

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
        o08_35F5_0D12();
    if (blackSize > 0)
        PlaceBlackQueen();
    o08_35F5_0A00();

    fd_50F6_1050 = 0;
    fd_50F6_1060 = 0;
    fd_50F6_1040 = 0;
    if (fd_50F6_0EAC != 3)
        AddFood(-1, 0);

    fd_50F6_10BE = 100;
    fd_50F6_01FE = 100;

    fd_50F6_0472 = 0;
    fd_50F6_09FA = 0;
    fd_50F6_0A00 = 0;
    fd_50F6_0F08 = 0;

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

void far o08_35F5_059B(void)
{
    int i;

    o08_35F5_1240();
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
        o08_35F5_0050(fd_3E1D_0000[*(fd_50F6_07CA + 1)][*fd_50F6_07CA], fd_3D57_0C24 = 0, 1, *fd_50F6_07BC, *(fd_50F6_07BC + 1));
    else
        o08_35F5_0050(fd_3E1D_0000[*(fd_50F6_07CA + 1)][*fd_50F6_07CA], fd_3D57_0C24 = 1, 1, *fd_50F6_07BC, *(fd_50F6_07BC + 1));

    if (fd_50F6_048C <= 1) {
        fd_50F6_0596[0] = fd_50F6_047C;
        fd_50F6_0596[1] = fd_50F6_048A;
    } else if (fd_50F6_048C == 2) {
        fd_50F6_06A6[0] = fd_50F6_047C;
        fd_50F6_06A6[1] = fd_50F6_048A;
    } else {
        fd_50F6_072E[0] = fd_50F6_047C;
        fd_50F6_072E[1] = fd_50F6_048A;
    }
}

void far o08_35F5_07C2(void)
{
    int i;

    fd_50F6_0EAC = 1;
    o08_35F5_059B();
    o08_35F5_1080(32);
    o08_35F5_1136(32);
    f_0BE8_038F();
    fd_50F6_0EAC = 2;
    f_015B_053C(fd_50F6_048C);
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
    f_14EE_0519(x, y);
    for (; count != 0; count--) {
        dir = (SRand1(5) + dir - 3) & 7;
        newX = x + fd_3D57_0000[dir];
        newY = y + fd_3D57_0008[dir];
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
            if (y == 1 && fd_3D57_0224[x] == 0)
                MakeNewHoleB(newX);
        }
    }
}

void far o08_35F5_0923(int count)
{
    int dir, y, x, newX, newY;

    dir = 4;
    y = 1;
    x = 0x20;
    f_14EE_0647(x, y);
    for (; count != 0; count--) {
        dir = (SRand1(5) + dir - 3) & 7;
        newX = x + fd_3D57_0000[dir];
        newY = y + fd_3D57_0008[dir];
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
            if (y == 1 && fd_3D57_0264[x] == 0)
                f_14EE_0367(newX);
        }
    }
}

void far o08_35F5_0A00(void)
{
    fd_50F6_049A = 0;
    fd_3D57_0C22 = 0xfd;
    if (fd_50F6_104E != 0) {
        fd_50F6_104E = 0;
        fd_3D57_07BE = -1;
    }
    f_10F7_1DD3(100);

    if (fd_50F6_0EAC != 3) {
        fd_50F6_04E2 = 0;
        fd_50F6_0A06 = 0;
        if (fd_50F6_0EAC != 2 || fd_3D57_0C24 != 0) {
            f_10F7_0A44(2, fd_50F6_0F0E, fd_50F6_0F26, 0x10, 2, 0xff);
        } else {
            int x, y;

            x = 0x40;
            y = 0x20;
            {
                int col, count, tries;

                for (tries = 0; tries < 100; tries++) {
                    count = SRand16() - SRand16() + 0x20;
                    col = SRand8() - SRand8() + 0x20;
                    if (fd_3E1D_0180[count][col] < 0x10) {
                        x = count;
                        y = col;
                        break;
                    }
                }
            }
            f_10F7_0A44(1, x, y, 0x40, 2, 0xff);
        }
        goto done;
    }
    fd_50F6_048C = 1;
    fd_50F6_04E2 = 0;
    fd_50F6_0A06 = 2;
    fd_50F6_047C = 0x40;
    fd_50F6_048A = 0x20;
    fd_50F6_04C2 = 0x10;

done:
    o22_39C7_07FD(fd_50F6_048C, fd_50F6_047C, fd_50F6_048A);
}

void far PlaceBlackQueen(void)
{
    int x, y, count, wobble;

    count = SRand4() + 7;
    wobble = 0;
    x = 0x20;
    for (y = 1; y < count; y++) {
        f_14EE_0519(x, y);
        if (SRand2() == 0)
            wobble = SRand1(3) - 1;
        if (wobble + x >= 8 && wobble + x <= 0x38)
            x += wobble;
    }
    for (count = 0; count < 2; count++) {
        f_14EE_0519(x, y);
        x++;
        y++;
    }
    f_14EE_0519(x, y);
    fd_3D57_02B4[0] = x;
    fd_3D57_02B4[1] = y;
    fd_50F6_0F0E = x;
    fd_50F6_0F26 = y;
    o08_35F5_0C4C(x + 2, y, 2);
}

void far o08_35F5_0C4C(int x, int y, int dir)
{
    int d;

    d = dir ^ 4;
    f_14EE_0519(x, y);
    f_14EE_0519(x + fd_3D57_0000[d], y + fd_3D57_0008[d]);
    f_14EE_0519(x + 2 * fd_3D57_0000[d], y + 2 * fd_3D57_0008[d]);
    f_0EC1_05D4(x, y, dir + 0x60, 9, 0);
    f_0EC1_05D4(x + fd_3D57_0000[d], y + fd_3D57_0008[d], dir + 0x68, 9, 0);
    fd_50F6_035E++;
}

void far o08_35F5_0D12(void)
{
    int x, y, count, wobble;

    count = SRand4() + 7;
    x = 0x20;
    for (y = 1; y < count; y++) {
        f_14EE_0647(x, y);
        wobble = SRand1(3) - 1;
        if (wobble + x >= 8 && wobble + x <= 0x38)
            x += wobble;
    }
    for (count = 0; count < 2; count++) {
        f_14EE_0647(x, y);
        x++;
        y++;
    }
    f_14EE_0647(x, y);
    fd_3D57_02B8[0] = x;
    fd_3D57_02B8[1] = y;
    o08_35F5_0DA0(x + 2, y, 2);
}

void far o08_35F5_0DA0(int x, int y, int dir)
{
    int d;

    d = dir ^ 4;
    f_14EE_0647(x, y);
    f_14EE_0647(x + fd_3D57_0000[d], y + fd_3D57_0008[d]);
    f_14EE_0647(x + 2 * fd_3D57_0000[d], y + 2 * fd_3D57_0008[d]);
    f_0EC1_0651(x, y, dir + 0xE0, 9, 0);
    f_0EC1_0651(x + fd_3D57_0000[d], y + fd_3D57_0008[d], dir + 0xE8, 9, 0);
    fd_50F6_036C++;
}

int far o08_35F5_0E67(int angle)
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

int far o08_35F5_0EBB(int angle)
{
    return o08_35F5_0E67(angle + 0x40);
}

void far AddFood(int count, int sound)
{
    int x, y, i, radius, r, angle, cx, cy;

    if (sound == 1)
        f_00DF_00E8(0x20, 0, 0x7e);
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
        x = (long)r * o08_35F5_0EBB(angle) / 0x7fffL + cx;
        y = (long)r * o08_35F5_0E67(angle) / 0x7fffL + cy;
        if (x < 0 || x > 0x7f || y < 0 || y > 0x3f)
            continue;
        if (fd_3E1D_6180[x][y] != 0)
            continue;
        angle = fd_3E1D_0180[x][y];
        if (fd_50F6_0F24 != 0) {
            if (angle < 0x18) {
                if (angle < 4)
                    fd_3E1D_0180[x][y] = (angle + 6) << 2;
                else
                    fd_3E1D_0180[x][y] = ((angle - 8) & 0xfc) + 0x18;
            } else if (angle < 0x28 && angle % 4 < 3)
                fd_3E1D_0180[x][y]++;
            else
                continue;
        } else {
            if (angle < 0x18)
                fd_3E1D_0180[x][y] = 0x48;
            else if (angle >= 0x48 && angle < 0x4b)
                fd_3E1D_0180[x][y]++;
            else
                continue;
        }
        fd_50F6_1040++;
    }
}

void far o08_35F5_1080(int count)
{
    int x;
    int y;
    int base;
    int kind;
    int type;

    for (x = 0; x < 64; x++) {
        for (y = 16; y < 48; y++) {
            if (fd_3E1D_0180[x][y] < 0x50 && fd_3E1D_6180[x][y] == 0) {
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
                fd_3E1D_6180[x][y] = type;
                f_0EC1_0557(x, y, type, kind, 0);
                if (--count <= 0)
                    return;
                if (fd_50F6_0D6A >= 1000)
                    return;
            }
        }
    }
}

void far o08_35F5_1136(int count)
{
    int x;
    int y;
    int base;
    int kind;
    int type;

    for (x = 127; x >= 64; x--) {
        for (y = 16; y < 48; y++) {
            if (fd_3E1D_0180[x][y] < 0x50 && fd_3E1D_6180[x][y] == 0) {
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
                fd_3E1D_6180[x][y] = type;
                f_0EC1_0557(x, y, type, kind, 0);
                if (--count <= 0)
                    return;
                if (fd_50F6_0D6A >= 1000)
                    return;
            }
        }
    }
}

/* DRAFT, not claimed: target puts col in BX and indexes with BX; ours copies to SI. */
int far o08_35F5_11F0(int x, int y)
{
    int col, row;

    col = x > 0x7f ? 0 : (x < 0 ? 0x7f : x);
    row = y > 0x3f ? 0 : (y < 0 ? 0x3f : y);
    return fd_3E1D_0180[col][row];
}

void far o08_35F5_1240(void)
{
    int x, y;

    for (x = 0; x < 128; x++) {
        for (y = 0; y < 64; y++) {
            fd_3E1D_0180[x][y] = 0;
            fd_3E1D_6180[x][y] = 0;
        }
    }
    for (x = 0; x < 64; x++) {
        for (y = 0; y < 64; y++) {
            fd_3E1D_2180[x][y] = 0;
            fd_3E1D_3180[x][y] = 0;
            fd_3E1D_4180[x][y] = 0;
            fd_3E1D_5180[x][y] = 0;
            fd_3E1D_8180[x][y] = 0;
            fd_3E1D_9180[x][y] = 0;
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
    for (x = 0; x < 12; x++) {
        for (y = 0; y < 16; y++) {
            fd_3D57_00A4[x][y] = 0;
            fd_3D57_0164[x][y] = 0;
        }
    }
}

/* SCAFFOLD BEGIN: context only, not reconstruction */
/* SCAFFOLD END */
