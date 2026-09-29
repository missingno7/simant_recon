/* Root module, code frame 0894: ant colony simulation (DoAntSim, A-list ants). */

extern int far SRand1(int range);
extern int far SRand2(void);
extern int far SRand4(void);
extern int far SRand8(void);
extern int far SRand16(void);
extern int far SRand32(void);
extern int far SRand256(void);

extern int far fd_50F6_0F08;
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
extern int far fd_50F6_10BE;
extern int far fd_50F6_01FE;
extern int far fd_50F6_0EAC;
extern int far fd_3D57_0C1A;
extern int far fd_50F6_1040;
extern int far fd_50F6_0D6A;
extern int far fd_50F6_0F18;
extern unsigned char far fd_3E1D_AD3B[];
extern unsigned char far fd_3E1D_A569[];
extern unsigned char far fd_3E1D_A180[];
extern long far fd_50F6_0F30;
extern unsigned char far fd_3E1D_A952[];
extern unsigned char far fd_3E1D_6180[128][64];
extern char far fd_3D57_0008[8];
extern char far fd_3D57_0000[8];

extern void far o06_35F5_0173(void);
extern void far f_0BE8_03AC(void);
extern void far f_0AD9_03D3(void);
extern void far f_0CDB_00B3(void);
extern void far f_0AD9_093C(void);
extern void far f_1383_0002(void);
extern void far o25_39C7_0000(void);
extern void far f_0F3F_0008(void);
extern void far DoAntSimY(void);
extern void far DoAntMoveY(void);
extern void far f_0E2E_000A(void);
extern void far o14_384C_0DE5(int a);
extern void far f_0EC1_0002(void);
extern void far f_0BE8_038F(void);
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

void far f_0894_0138(void);
void far f_0894_019B(void);
void far f_0894_01E5(void);
void far f_0894_02D2(void);
void far f_0894_034B(void);
void far f_0894_0572(int index);
void far f_0894_05EE(int index);
int far f_0894_0671(int x, int y, int life);
void far f_0894_06D8(int index);
void far f_0894_0751(int index);
void far f_0894_07B3(int index);
void far f_0894_0892(int index);
void far f_0894_0961(int index);
void far f_0894_09F4(int index);
void far f_0894_0CFD(int index);
void far f_0894_0E8E(int index);
void far f_0894_1087(int index);
void far f_0894_1315(int index);
void far f_0894_1525(int index);
void far f_0894_16A5(int index);
void far f_0894_1A28(int index);
void far f_0894_1C6E(int x, int y, int index);
void far f_0894_1F31(int index);
void far DeadAntHere(int x, int y, int type);
void far f_0894_21ED(int index);
int far f_0894_23BB(int x, int y);

void far f_0894_000E(void)
{
    if (++fd_50F6_0F08 > 0x1000)
        fd_50F6_0F08 = 0;
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
    if ((fd_50F6_0F08 & 0x3f) == 0)
        f_0894_02D2();
    if ((fd_50F6_0F08 & 0x1f) == 0)
        f_0894_0138();
    o06_35F5_0173();
    f_0BE8_03AC();
    f_0AD9_03D3();
    f_0CDB_00B3();
    if (fd_50F6_0F08 & 1)
        f_0AD9_093C();
    f_1383_0002();
    f_0894_019B();
    f_0894_034B();
    o25_39C7_0000();
    f_0F3F_0008();
    DoAntSimY();
    f_0894_01E5();
    DoAntMoveY();
    f_0E2E_000A();
    if (fd_50F6_0376)
        o14_384C_0DE5(0);
    fd_3D57_02C2 = 1;
}

void far f_0894_0138(void)
{
    switch ((fd_50F6_0F08 & 0x60) >> 5) {
    case 0:
        f_0EC1_0002();
        f_0BE8_038F();
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
        f_0BE8_038F();
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

void far f_0894_019B(void)
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

void far f_0894_01E5(void)
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

void far f_0894_02D2(void)
{
    if (fd_3D57_0C18 == 0) {
        if (--fd_50F6_10BE < 0)
            fd_50F6_10BE = 0;
    }
    if (--fd_50F6_01FE < 0)
        fd_50F6_01FE = 0;
    if (fd_50F6_0EAC == 3)
        return;
    if (fd_50F6_1040 >= fd_3D57_0C1A)
        return;
    AddFood(0x96, 1);
    fd_3D57_0C1A = SRand1(0x32) + 1;
}

void far f_0894_034B(void)
{
    int t;
    int mode;

    fd_50F6_0F18 = fd_50F6_0D6A;
    while (fd_50F6_0F18 > 0) {
        fd_50F6_0F18--;
        if (SRand256() == 0) {
            t = fd_3E1D_AD3B[fd_50F6_0F18];
            if (t) {
                if (t & 0x80)
                    t = fd_50F6_01FE;
                else
                    t = fd_50F6_10BE;
                if (SRand32() > t) {
                    DeadAntHere(fd_3E1D_A180[fd_50F6_0F18], fd_3E1D_A569[fd_50F6_0F18],
                                fd_3E1D_AD3B[fd_50F6_0F18] & 0x80);
                    fd_3E1D_AD3B[fd_50F6_0F18] = 0;
                    fd_50F6_0F30++;
                }
            }
        }
        t = fd_3E1D_AD3B[fd_50F6_0F18];
        if (t == 0)
            continue;
        mode = fd_3E1D_A952[fd_50F6_0F18];
        if (t & 0x80)
            fd_50F6_0D72[mode]++;
        else
            fd_50F6_0D40[mode]++;
        switch (mode) {
        case 0:
            f_0894_09F4(fd_50F6_0F18);
            break;
        case 1:
        case 4:
            f_0894_1087(fd_50F6_0F18);
            break;
        case 2:
            f_0894_16A5(fd_50F6_0F18);
            break;
        case 3:
            f_0894_1525(fd_50F6_0F18);
            break;
        case 5:
            f_0894_0E8E(fd_50F6_0F18);
            break;
        case 6:
            f_0894_1A28(fd_50F6_0F18);
            break;
        case 7:
            f_0894_21ED(fd_50F6_0F18);
            break;
        case 8:
            f_0894_0572(fd_50F6_0F18);
            break;
        case 9:
            f_0894_05EE(fd_50F6_0F18);
            break;
        case 10:
            f_0894_1F31(fd_50F6_0F18);
            break;
        case 11:
            f_0894_1315(fd_50F6_0F18);
            break;
        case 12:
            f_0894_0961(fd_50F6_0F18);
            break;
        case 13:
            f_0894_06D8(fd_50F6_0F18);
            break;
        case 14:
            f_0894_0751(fd_50F6_0F18);
            break;
        case 15:
            f_0894_07B3(fd_50F6_0F18);
            break;
        case 16:
            f_0894_0892(fd_50F6_0F18);
            break;
        case 19:
            f_0DEF_006B(fd_50F6_0F18);
            break;
        }
    }
}

void far f_0894_0572(int index)
{
    int x;
    int y;
    unsigned char type;

    x = fd_3E1D_A180[index];
    y = fd_3E1D_A569[index];
    type = fd_3E1D_AD3B[index];
    fd_3E1D_6180[x][y] = type;
    if (SRand1(200) == 0) {
        fd_3E1D_AD3B[index] = 0;
        fd_3E1D_6180[x][y] = 0;
    }
}

void far f_0894_05EE(int index)
{
    int x;
    int y;
    int type;

    x = fd_3E1D_A180[index];
    y = fd_3E1D_A569[index];
    type = fd_3E1D_AD3B[index];
    fd_3E1D_6180[x][y] = type;
    if ((type & 0x7f) > 0x67) {
        if (f_0894_0671(x, y, type)) {
            fd_3E1D_6180[x][y] = 0;
            fd_3E1D_AD3B[index] = 0;
        }
    }
}

int far f_0894_0671(int x, int y, int life)
{
    int row;
    int column;

    row = x + fd_3D57_0000[life & 7];
    column = y + fd_3D57_0008[life & 7];
    if (fd_3E1D_6180[row][column] - life == -8)
        return 0;
    if (f_0EC1_0291(row, column) >= 0)
        return 0;
    return 1;
}

void far f_0894_06D8(int index)
{
    int x;
    int y;

    x = fd_3E1D_A180[index];
    y = fd_3E1D_A569[index];
    if (f_0894_23BB(x, y) == 1)
        f_0894_1C6E(x, y, index);
    else if (SRand4() == 0)
        fd_3E1D_A952[index] = 2;
    else if (fd_3D57_07B2 == 1)
        f_0250_43F2(x, y, 1);
}

/* SCAFFOLD BEGIN: unrecovered members, kept in place for push cs/call near */
void far f_0894_0751(int index) {}
void far f_0894_07B3(int index) {}
void far f_0894_0892(int index) {}
void far f_0894_0961(int index) {}
void far f_0894_09F4(int index) {}
void far f_0894_0CFD(int index) {}
void far f_0894_0E8E(int index) {}
void far f_0894_1087(int index) {}
void far f_0894_1315(int index) {}
void far f_0894_1525(int index) {}
void far f_0894_16A5(int index) {}
void far f_0894_1A28(int index) {}
void far f_0894_1C6E(int x, int y, int index) {}
void far f_0894_1D89(void) {}
void far f_0894_1E34(void) {}
void far f_0894_1F31(int index) {}
void far DeadAntHere(int x, int y, int type) {}
void far f_0894_21C5(void) {}
void far f_0894_21ED(int index) {}
int far f_0894_23BB(int x, int y) { return 0; }
void far f_0894_2423(void) {}
/* SCAFFOLD END */
