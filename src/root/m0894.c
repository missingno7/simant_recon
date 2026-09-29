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
extern unsigned char far fd_3E1D_F09F[64][32];
extern unsigned char far fd_3E1D_E09F[64][32];
extern int far fd_50F6_06AA;
extern int far fd_50F6_073A;
extern int far fd_50F6_07C8;
extern int far fd_50F6_0850;
extern unsigned char far fd_3E1D_0180[128][64];
extern int far fd_50F6_0480;
extern unsigned char far fd_3E1D_B124[];
extern int far fd_50F6_04E2;
extern int far fd_50F6_1044;
extern signed char far fd_3D57_0024[8][8];
extern unsigned char far fd_3E1D_D09F[64][32];
extern int far fd_50F6_0DA8;
extern unsigned char far fd_3D57_0224[];
extern int far fd_50F6_0EAA;
extern unsigned char far fd_3D57_0264[];
extern int far fd_3D57_0C14;
extern long far fd_50F6_0F3E;
extern int far fd_50F6_09FA;
extern long far fd_50F6_0EFC;
extern int far fd_50F6_0A00;
extern int far fd_50F6_0476;
extern unsigned char far fd_50F6_037C[100];
extern unsigned char far fd_50F6_0404[100];
extern int far fd_50F6_0F24;
extern int far fd_3D57_0074[16];
extern signed char far fd_3D57_0094[];

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
extern void far f_00F8_0395(void);
extern int far f_1383_0E89(int x, int y, int dir);
extern void far f_0BE8_0798(int x, int y);
extern void far f_1496_0404(int x, int y, int level);
extern void far f_1496_03CC(int x, int y, int level);
extern void far f_1496_04AC(int x, int y, int colour);
extern int far f_10F7_003A(int value);
extern void far o25_3BA4_0DFB(int a, int index);
extern void far o22_39C7_19E5(int x, int y, int dir);
extern int far f_1383_0976(int caste, int type);
extern int far f_1383_10A8(int x, int y);
extern int far f_1383_0C2A(int x, int y, int dir, int attribute);
extern int far f_1383_0DCC(int x, int y, int dir);
extern int far f_1383_0A95(int x, int y, int dir, int attribute);
extern int far f_1383_0FCE(int x, int y, int dir);
extern int far f_1383_0ECC(int x, int y, int dir);
extern void far f_0EC1_05D4(int x, int y, int type, int mode, int state);
extern void far f_0EC1_0651(int x, int y, int type, int mode, int state);
extern void far f_14EE_0519(int x, int y);
extern void far f_14EE_0647(int x, int y);
extern void far f_1496_0395(int x, int y, int level);
extern int far RRand(int range);
extern void far f_0250_4302(int x, int y, int plane);
extern int far f_10F7_2867(int x, int y);

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
int far f_0894_2423(int tile);
int far f_0894_21C5(int dir);
void far f_0894_1D89(int index, int x, int y, int nx, int ny);
int far f_0894_1E34(int a, int b);

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

void far f_0894_0751(int index)
{
    if (SRand2())
        f_0894_0CFD(index);
    else
        f_0894_1087(index);
    if (fd_3E1D_AD3B[index] & 0x80) {
        if (fd_50F6_08E8 > 100)
            fd_3E1D_A952[fd_50F6_0F18] = 0xf;
    } else {
        if (fd_50F6_08DC > 100)
            fd_3E1D_A952[fd_50F6_0F18] = 0xf;
    }
}

void far f_0894_07B3(int index)
{
    int scent;

    if (fd_3E1D_AD3B[index] & 0x80)
        scent = fd_3E1D_F09F[fd_3E1D_A180[index] >> 1][fd_3E1D_A569[index] >> 1];
    else
        scent = fd_3E1D_E09F[fd_3E1D_A180[index] >> 1][fd_3E1D_A569[index] >> 1];
    if (scent < 100)
        f_0894_1087(index);
    else
        f_0894_0CFD(index);
    if (fd_3E1D_AD3B[index] & 0x80) {
        if (fd_50F6_08E8 != 0 && (fd_50F6_08E8 == 1 || SRand1(fd_50F6_08E8) == 0))
            fd_3E1D_A952[fd_50F6_0F18] = 0x10;
    } else {
        if (fd_50F6_08DC != 0 && (fd_50F6_08DC == 1 || SRand1(fd_50F6_08DC) == 0))
            fd_3E1D_A952[fd_50F6_0F18] = 0x10;
    }
}

void far f_0894_0892(int index)
{
    int red;

    red = fd_3E1D_AD3B[index] & 0x80;
    if (SRand32() == 0) {
        if ((red == 0 && fd_50F6_06AA < 50) || (red != 0 && fd_50F6_073A < 50)) {
            fd_3E1D_AD3B[index] = 0;
            fd_3E1D_6180[fd_3E1D_A180[index]][fd_3E1D_A569[index]] = 0;
            if (fd_50F6_0EAC == 2) {
                if (red == 0)
                    fd_50F6_06AA++;
                else
                    fd_50F6_073A++;
                if (SRand16() == 0) {
                    if (red == 0) {
                        fd_50F6_07C8++;
                        f_00F8_0395();
                    } else
                        fd_50F6_0850++;
                }
            }
        }
    }
}

void far f_0894_0961(int index)
{
    int scent;

    if (fd_3E1D_AD3B[index] & 0x80)
        scent = fd_3E1D_F09F[fd_3E1D_A180[index] >> 1][fd_3E1D_A569[index] >> 1];
    else
        scent = fd_3E1D_E09F[fd_3E1D_A180[index] >> 1][fd_3E1D_A569[index] >> 1];
    if (scent < 0x6e)
        f_0894_1087(index);
    else
        f_0894_0CFD(index);
}


void far f_0894_09F4(int index)
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

    x = fd_3E1D_A180[index];
    y = fd_3E1D_A569[index];
    attribute = fd_3E1D_AD3B[index];
    if (f_0894_23BB(x, y)) {
        f_0894_1C6E(x, y, index);
        return;
    }
    flags = attribute & 0xf8;
    caste = (attribute & 0x78) >> 3;
    dir = f_1383_0E89(x, y, attribute & 7);
    nx = x + fd_3D57_0000[dir];
    ny = y + fd_3D57_0008[dir];
    tile = fd_3E1D_0180[nx][ny];
    if (f_0894_2423(tile) == 1) {
        if (caste == 6 || caste == 2) {
            fd_3E1D_AD3B[index] = dir | flags | 8;
            fd_3E1D_6180[x][y] = fd_3E1D_AD3B[index];
            fd_3E1D_A952[index] = 3;
            f_0BE8_0798(nx, ny);
            fd_3E1D_B124[index] = 200;
            return;
        }
    } else if (tile > fd_50F6_0480) {
        fd_3E1D_AD3B[index] = f_0894_21C5(attribute & 7) | flags;
        fd_3E1D_6180[x][y] = fd_3E1D_AD3B[index];
        return;
    }
    tile = fd_3E1D_6180[nx][ny];
    if (tile == 0) {
        fd_3E1D_AD3B[index] = fd_3E1D_6180[nx][ny] = dir | flags;
        fd_3E1D_6180[x][y] = 0;
        fd_3E1D_A180[index] = nx;
        fd_3E1D_A569[index] = ny;
        if (fd_3E1D_B124[index] != 0) {
            fd_3E1D_B124[index]--;
            if (attribute & 0x80)
                f_1496_0404(nx, ny, fd_3E1D_B124[index]);
            else
                f_1496_03CC(nx, ny, fd_3E1D_B124[index]);
        }
        f_1496_04AC(nx, ny, attribute & 0x80);
        if (SRand8() == 0 && (caste == 6 || caste == 2))
            fd_3E1D_A952[index] = 2;
        return;
    }
    if (f_10F7_003A(tile) == 1) {
        if ((fd_50F6_04E2 ^ attribute) & 0x80) {
            o25_3BA4_0DFB(1, index);
            return;
        }
        if (fd_50F6_1044 == 1) {
            fd_3E1D_AD3B[index] = dir | flags;
            fd_3E1D_6180[x][y] = fd_3E1D_AD3B[index];
            o22_39C7_19E5(x, y, dir);
        }
        fd_3E1D_AD3B[index] = f_0894_21C5(attribute & 7) | flags;
        fd_3E1D_6180[x][y] = fd_3E1D_AD3B[index];
        return;
    }
    if (((tile ^ attribute) & 0x80) == 0) {
        fd_3E1D_AD3B[index] = f_0894_21C5(attribute & 7) | flags;
        fd_3E1D_6180[x][y] = fd_3E1D_AD3B[index];
        fd_3E1D_A952[index] = f_1383_0976(caste, attribute);
        return;
    }
    f_0894_1D89(index, x, y, nx, ny);
}


void far f_0894_0CFD(int index)
{
    int x;
    int y;
    int tile;
    int attribute;
    int flags;
    int dir;
    int nx;
    int ny;


    x = fd_3E1D_A180[index];
    y = fd_3E1D_A569[index];
    attribute = fd_3E1D_AD3B[index];
    if (f_0894_23BB(x, y)) {
        f_0894_1C6E(x, y, index);
        return;
    }
    flags = attribute & 0xf8;
    dir = f_1383_0E89(x, y, attribute & 7);
    nx = x + fd_3D57_0000[dir];
    ny = y + fd_3D57_0008[dir];
    if (fd_3E1D_0180[nx][ny] > fd_50F6_0480) {
        fd_3E1D_AD3B[index] = f_0894_21C5(attribute & 7) | flags;
        fd_3E1D_6180[x][y] = fd_3E1D_AD3B[index];
        return;
    }
    tile = fd_3E1D_6180[nx][ny];
    if (tile == 0) {
        fd_3E1D_AD3B[index] = fd_3E1D_6180[nx][ny] = dir | flags;
        fd_3E1D_6180[x][y] = 0;
        fd_3E1D_A180[index] = nx;
        fd_3E1D_A569[index] = ny;
        return;
    }
    if (f_10F7_003A(tile) == 1) {
        if ((fd_50F6_04E2 ^ attribute) & 0x80) {
            o25_3BA4_0DFB(1, index);
            return;
        }
        fd_3E1D_AD3B[index] = f_0894_21C5(attribute & 7) | flags;
        fd_3E1D_6180[x][y] = fd_3E1D_AD3B[index];
        return;
    }
    if (((attribute ^ tile) & 0x80) == 0) {
        fd_3E1D_AD3B[index] = f_0894_21C5(attribute & 7) | flags;
        fd_3E1D_6180[x][y] = fd_3E1D_AD3B[index];
        return;
    }
    f_0894_1D89(index, x, y, nx, ny);
}


void far f_0894_0E8E(int index)
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

    x = fd_3E1D_A180[index];
    y = fd_3E1D_A569[index];
    attribute = fd_3E1D_AD3B[index];
    flags = attribute & 0xf8;
    digmode = (attribute & 0x78) >> 3;
    dirindex = fd_3D57_0024[attribute & 7][SRand8()];
    bdir = f_1383_10A8(x, y);
    if (bdir != 0)
        dirindex = (bdir - 1) & 7;
    nx = x + fd_3D57_0000[dirindex];
    ny = y + fd_3D57_0008[dirindex];
    if (digmode != 5 && digmode != 9) {
        fd_3E1D_A952[index] = f_1383_0976(digmode, attribute);
        fd_3E1D_B124[index] = 0;
        return;
    }
    if (SRand8() == 0) {
        fd_3E1D_AD3B[index] -= 0x18;
        fd_3E1D_A952[index] = f_1383_0976(digmode, attribute);
        fd_3E1D_B124[index] = 0;
        fd_3E1D_6180[x][y] = fd_3E1D_AD3B[index];
        return;
    }
    if (fd_3E1D_0180[nx][ny] > fd_50F6_0480) {
        fd_3E1D_AD3B[index] = f_0894_21C5(attribute & 7) | flags;
        fd_3E1D_6180[x][y] = fd_3E1D_AD3B[index];
        return;
    }
    if (fd_3E1D_6180[nx][ny] == 0) {
        fd_3E1D_AD3B[index] = fd_3E1D_6180[nx][ny] = dirindex | flags;
        fd_3E1D_6180[x][y] = 0;
        fd_3E1D_A180[index] = nx;
        fd_3E1D_A569[index] = ny;
    } else {
        fd_3E1D_AD3B[index] = f_0894_21C5(attribute & 7) | flags;
        fd_3E1D_6180[x][y] = fd_3E1D_AD3B[index];
        return;
    }
    if (fd_3E1D_B124[index] != 0) {
        fd_3E1D_B124[index]--;
        if (attribute & 0x80)
            f_1496_0404(nx, ny, fd_3E1D_B124[index]);
        else
            f_1496_03CC(nx, ny, fd_3E1D_B124[index]);
    }
}


void far f_0894_1087(int index)
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

    x = fd_3E1D_A180[index];
    y = fd_3E1D_A569[index];
    attribute = fd_3E1D_AD3B[index];
    if (f_0894_23BB(x, y)) {
        f_0894_1C6E(x, y, index);
        return;
    }
    flags = attribute & 0xf8;
    caste = (attribute & 0x78) >> 3;
    dir = f_1383_0C2A(x, y, attribute & 7, attribute);
    nx = x + fd_3D57_0000[dir];
    ny = y + fd_3D57_0008[dir];
    tile = fd_3E1D_0180[nx][ny];
    if (f_0894_2423(tile) == 1) {
        if (caste == 6 || caste == 2) {
            fd_3E1D_AD3B[index] = dir | flags | 8;
            fd_3E1D_6180[x][y] = fd_3E1D_AD3B[index];
            fd_3E1D_A952[index] = 3;
            f_0BE8_0798(nx, ny);
            fd_3E1D_B124[index] = 200;
            return;
        }
    } else if (tile > fd_50F6_0480) {
        fd_3E1D_AD3B[index] = f_0894_21C5(attribute & 7) | flags;
        fd_3E1D_6180[x][y] = fd_3E1D_AD3B[index];
        return;
    }
    tile = fd_3E1D_6180[nx][ny];
    if (tile == 0) {
        fd_3E1D_AD3B[index] = fd_3E1D_6180[nx][ny] = dir | flags;
        fd_3E1D_6180[x][y] = 0;
        fd_3E1D_A180[index] = nx;
        fd_3E1D_A569[index] = ny;
        if (fd_3E1D_B124[index] != 0) {
            fd_3E1D_B124[index]--;
            if (attribute & 0x80)
                f_1496_0404(nx, ny, fd_3E1D_B124[index]);
            else
                f_1496_03CC(nx, ny, fd_3E1D_B124[index]);
        }
        return;
    }
    if (f_10F7_003A(tile) == 1) {
        if ((fd_50F6_04E2 ^ attribute) & 0x80) {
            o25_3BA4_0DFB(1, index);
            return;
        }
        if (fd_50F6_1044 == 1) {
            fd_3E1D_AD3B[index] = dir | flags;
            fd_3E1D_6180[x][y] = fd_3E1D_AD3B[index];
            o22_39C7_19E5(x, y, dir);
        }
        fd_3E1D_AD3B[index] = f_0894_21C5(attribute & 7) | flags;
        fd_3E1D_6180[x][y] = fd_3E1D_AD3B[index];
        return;
    }
    if (((tile ^ attribute) & 0x80) == 0) {
        fd_3E1D_AD3B[index] = f_0894_21C5(attribute & 7) | flags;
        fd_3E1D_6180[x][y] = fd_3E1D_AD3B[index];
        return;
    }
    f_0894_1D89(index, x, y, nx, ny);
}


void far f_0894_1315(int index)
{
    int x;
    int y;
    int tile;
    int attribute;
    int flags;
    int dir;
    int nx;
    int ny;

    x = fd_3E1D_A180[index];
    y = fd_3E1D_A569[index];
    attribute = fd_3E1D_AD3B[index];
    if (f_0894_23BB(x, y)) {
        f_0894_1C6E(x, y, index);
        return;
    }
    flags = attribute & 0xf8;
    if (fd_3E1D_D09F[x >> 1][y >> 1] == 0 && SRand4() == 0) {
        fd_3E1D_6180[x][y] = fd_3E1D_AD3B[index];
        fd_3E1D_A952[index] = f_1383_0976((attribute & 0x78) >> 3, attribute);
        return;
    }
    dir = f_1383_0DCC(x, y, attribute & 7);
    nx = x + fd_3D57_0000[dir];
    ny = y + fd_3D57_0008[dir];
    if (fd_3E1D_0180[nx][ny] > fd_50F6_0480) {
        fd_3E1D_AD3B[index] = f_0894_21C5(attribute & 7) | flags;
        fd_3E1D_6180[x][y] = fd_3E1D_AD3B[index];
        return;
    }
    tile = fd_3E1D_6180[nx][ny];
    if (tile == 0) {
        fd_3E1D_AD3B[index] = fd_3E1D_6180[nx][ny] = dir | flags;
        fd_3E1D_6180[x][y] = 0;
        fd_3E1D_A180[index] = nx;
        fd_3E1D_A569[index] = ny;
        return;
    }
    if (f_10F7_003A(tile) == 1) {
        if ((fd_50F6_04E2 ^ attribute) & 0x80) {
            o25_3BA4_0DFB(1, index);
            return;
        }
        fd_3E1D_AD3B[index] = f_0894_21C5(attribute & 7) | flags;
        fd_3E1D_6180[x][y] = fd_3E1D_AD3B[index];
        return;
    }
    if (((tile ^ attribute) & 0x80) == 0) {
        fd_3E1D_AD3B[index] = f_0894_21C5(attribute & 7) | flags;
        fd_3E1D_6180[x][y] = fd_3E1D_AD3B[index];
        return;
    }
    f_0894_1D89(index, x, y, nx, ny);
}


extern void far f_1496_0474(int x, int y, int level);
extern void far f_1496_043C(int x, int y, int level);

void far f_0894_1525(int index)
{
    int x;
    int y;
    int attribute;
    int flags;
    int ndir;
    int nx;
    int ny;

    x = fd_3E1D_A180[index];
    y = fd_3E1D_A569[index];
    attribute = fd_3E1D_AD3B[index];
    if (f_0894_23BB(x, y)) {
        f_0894_1C6E(x, y, index);
        return;
    }
    flags = attribute & 0xf8;
    ndir = f_1383_0C2A(x, y, attribute & 7, attribute);
    nx = x + fd_3D57_0000[ndir];
    ny = y + fd_3D57_0008[ndir];
    if (fd_3E1D_0180[nx][ny] > fd_50F6_0480) {
        fd_3E1D_AD3B[index] = f_0894_21C5(attribute & 7) | flags;
        fd_3E1D_6180[x][y] = fd_3E1D_AD3B[index];
        return;
    }
    fd_3E1D_AD3B[index] = fd_3E1D_6180[nx][ny] = ndir | flags;
    fd_3E1D_6180[x][y] = 0;
    fd_3E1D_A180[index] = nx;
    fd_3E1D_A569[index] = ny;
    if (fd_3E1D_B124[index] != 0) {
        fd_3E1D_B124[index]--;
        if (attribute & 0x80)
            f_1496_0474(nx, ny, fd_3E1D_B124[index]);
        else
            f_1496_043C(nx, ny, fd_3E1D_B124[index]);
    }
}

void far f_0894_16A5(int index)
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

    x = fd_3E1D_A180[index];
    y = fd_3E1D_A569[index];
    attribute = fd_3E1D_AD3B[index];
    if (f_0894_23BB(x, y)) {
        f_0894_1C6E(x, y, index);
        return;
    }
    if (SRand32() == 0) {
        fd_3E1D_A952[index] = 0xd;
        return;
    }
    flags = attribute & 0xf8;
    caste = (attribute & 0x78) >> 3;
    if (fd_3E1D_D09F[x >> 1][y >> 1] != 0) {
        fd_3E1D_A952[index] = 0xb;
        return;
    }
    if (caste != 6 && caste != 2) {
        fd_3E1D_A952[index] = f_1383_0976(caste, attribute);
        fd_3E1D_B124[index] = 0;
        return;
    }
    dir = f_1383_0A95(x, y, attribute & 7, attribute);
    if (dir < 0) {
        if (SRand8())
            fd_3E1D_A952[index] = 0;
        else
            fd_3E1D_A952[index] = f_1383_0976(caste, attribute);
        fd_3E1D_B124[index] = 0;
        f_1496_04AC(x >> 1, y >> 1, attribute & 0x80);
        return;
    }
    nx = x + fd_3D57_0000[dir];
    ny = y + fd_3D57_0008[dir];
    tile = fd_3E1D_0180[nx][ny];
    if (f_0894_2423(tile) == 1) {
        fd_3E1D_AD3B[index] = dir | flags | 8;
        fd_3E1D_6180[x][y] = fd_3E1D_AD3B[index];
        fd_3E1D_A952[index] = 3;
        f_0BE8_0798(nx, ny);
        fd_3E1D_B124[index] = 200;
        return;
    }
    if (tile > fd_50F6_0480) {
        fd_3E1D_AD3B[index] = f_0894_21C5(attribute & 7) | flags;
        fd_3E1D_6180[x][y] = fd_3E1D_AD3B[index];
        if (SRand16() == 0) {
            fd_3E1D_A952[index] = f_1383_0976(caste, attribute);
            fd_3E1D_B124[index] = 0;
        }
        return;
    }
    tile = fd_3E1D_6180[nx][ny];
    if (tile == 0) {
        fd_3E1D_AD3B[index] = fd_3E1D_6180[nx][ny] = dir | flags;
        fd_3E1D_6180[x][y] = 0;
        fd_3E1D_A180[index] = nx;
        fd_3E1D_A569[index] = ny;
        if (fd_3E1D_B124[index] != 0) {
            fd_3E1D_B124[index]--;
            if (attribute & 0x80)
                f_1496_0404(nx, ny, fd_3E1D_B124[index]);
            else
                f_1496_03CC(nx, ny, fd_3E1D_B124[index]);
        }
        f_1496_04AC(nx, ny, attribute & 0x80);
        return;
    }
    if (f_10F7_003A(tile) == 1) {
        if ((fd_50F6_04E2 ^ attribute) & 0x80) {
            o25_3BA4_0DFB(1, index);
            return;
        }
        if (fd_50F6_1044 == 1) {
            fd_3E1D_AD3B[index] = dir | flags;
            fd_3E1D_6180[x][y] = fd_3E1D_AD3B[index];
            o22_39C7_19E5(x, y, dir);
        }
        fd_3E1D_AD3B[index] = f_0894_21C5(attribute & 7) | flags;
        fd_3E1D_6180[x][y] = fd_3E1D_AD3B[index];
        return;
    }
    if (((tile ^ attribute) & 0x80) == 0) {
        fd_3E1D_AD3B[index] = f_0894_21C5(attribute & 7) | flags;
        fd_3E1D_6180[x][y] = fd_3E1D_AD3B[index];
        return;
    }
    f_0894_1D89(index, x, y, nx, ny);
}

void far f_0894_1A28(int index)
{
    int x;
    int y;
    int tile;
    int attribute;
    int flags;
    int dir;
    int nx;
    int ny;

    x = fd_3E1D_A180[index];
    y = fd_3E1D_A569[index];
    attribute = fd_3E1D_AD3B[index];
    if (f_0894_23BB(x, y)) {
        f_0894_1C6E(x, y, index);
        return;
    }
    flags = attribute & 0xf8;
    if (fd_3E1D_D09F[x >> 1][y >> 1] != 0)
        dir = f_1383_0DCC(x, y, attribute & 7);
    else if (attribute > 0x7f)
        dir = f_1383_0FCE(x, y, attribute & 7);
    else
        dir = f_1383_0ECC(x, y, attribute & 7);
    nx = x + fd_3D57_0000[dir];
    ny = y + fd_3D57_0008[dir];
    if (fd_3E1D_0180[nx][ny] > fd_50F6_0480) {
        fd_3E1D_AD3B[index] = SRand8() | flags;
        fd_3E1D_6180[x][y] = fd_3E1D_AD3B[index];
        return;
    }
    tile = fd_3E1D_6180[nx][ny];
    if (tile == 0) {
        fd_3E1D_AD3B[index] = fd_3E1D_6180[nx][ny] = dir | flags;
        fd_3E1D_6180[x][y] = 0;
        fd_3E1D_A180[index] = nx;
        fd_3E1D_A569[index] = ny;
        return;
    }
    if (f_10F7_003A(tile)) {
        if ((fd_50F6_04E2 ^ attribute) & 0x80) {
            o25_3BA4_0DFB(1, index);
            return;
        }
        if (fd_50F6_1044) {
            fd_3E1D_AD3B[index] = dir | flags;
            fd_3E1D_6180[x][y] = fd_3E1D_AD3B[index];
            o22_39C7_19E5(x, y, dir);
        }
        fd_3E1D_AD3B[index] = f_0894_21C5(attribute & 7) | flags;
        fd_3E1D_6180[x][y] = fd_3E1D_AD3B[index];
        return;
    }
    if (((tile ^ attribute) & 0x80) == 0) {
        fd_3E1D_AD3B[index] = f_0894_21C5(attribute & 7) | flags;
        fd_3E1D_6180[x][y] = fd_3E1D_AD3B[index];
        return;
    }
    f_0894_1D89(index, x, y, nx, ny);
}

void far f_0894_1C6E(int x, int y, int index)
{
    if (x < 0x40) {
        if (fd_50F6_0DA8 >= 500)
            f_0EC1_0081();
        if (fd_50F6_0DA8 >= 500)
            return;
        f_0EC1_05D4(y, 1, (fd_3E1D_AD3B[index] & 0xf8) + 4, fd_3E1D_A952[index], fd_3E1D_B124[index]);
        if (fd_3D57_0224[y] != 0)
            f_14EE_0519(y, 1);
    } else {
        if (fd_50F6_0EAA >= 500)
            f_0EC1_0100();
        if (fd_50F6_0EAA >= 500)
            return;
        f_0EC1_0651(y, 1, (fd_3E1D_AD3B[index] & 0xf8) + 4, fd_3E1D_A952[index], fd_3E1D_B124[index]);
        if (fd_3D57_0264[y] != 0)
            f_14EE_0647(y, 1);
    }
    fd_3E1D_AD3B[index] = 0;
    fd_3E1D_6180[x][y] = 0;
}

void far f_0894_1D89(int ant, int x, int y, int nx, int ny)
{
    int loser;
    int type;
    int winner;

    type = fd_3E1D_AD3B[ant];
    fd_3E1D_AD3B[ant] = 0;
    fd_3E1D_6180[x][y] = 0;
    loser = f_0EC1_0291(nx, ny);
    if (loser >= 0) {
        winner = f_0894_1E34(fd_3E1D_AD3B[loser], type);
        fd_3E1D_AD3B[loser] = (winner & 0x80) + 0x70;
        fd_3E1D_6180[nx][ny] = (winner & 0x80) + 0x70;
        fd_3E1D_A952[loser] = 0xa;
        fd_3E1D_B124[loser] = winner;
        f_1496_0395(nx, ny, 0x28);
    }
}

static unsigned char near combatLevel[16] = {
    0, 0, 0, 0, 2, 0, 1, 1, 2, 1, 0, 0, 3, 3, 0, 0
};
static unsigned char near combatOdds[16] = {
    5, 2, 7, 3, 8, 5, 9, 4, 3, 1, 5, 2, 7, 6, 8, 5
};

int far f_0894_1E34(int a, int b)
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

void far f_0894_1F31(int index)
{
    int x;
    int y;

    x = fd_3E1D_A180[index];
    y = fd_3E1D_A569[index];
    fd_3E1D_AD3B[index] = (fd_3E1D_AD3B[index] & 0xf8) + SRand1(7);
    fd_3E1D_6180[x][y] = fd_3E1D_AD3B[index];
    if (SRand16() == 0) {
        fd_3E1D_6180[x][y] = fd_3E1D_B124[index];
        fd_3E1D_AD3B[index] = fd_3E1D_6180[x][y];
        fd_3E1D_A952[fd_50F6_0F18] = f_1383_0976((fd_3E1D_AD3B[index] & 0x78) >> 3, fd_3E1D_AD3B[index]);
        fd_3E1D_B124[index] = 0;
        DeadAntHere(x, y, fd_3E1D_AD3B[index] & 0x80);
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
    otile = fd_3E1D_0180[oldX][oldY];
    if (fd_50F6_0F24 == 0) {
        if (otile >= 0x10 && otile < 0x18)
            fd_3E1D_0180[oldX][oldY] = SRand16();
        fd_50F6_037C[fd_50F6_0476] = x;
        fd_50F6_0404[fd_50F6_0476] = y;
        if (fd_3E1D_0180[x][y] < 0x18) {
            if (type != 0)
                fd_3E1D_0180[x][y] = SRand4() + 0x14;
            else
                fd_3E1D_0180[x][y] = SRand4() + 0x10;
        }
    } else {
        if (otile >= 8 && otile < 0x18)
            fd_3E1D_0180[oldX][oldY] = (otile - 8) >> 2;
        fd_50F6_037C[fd_50F6_0476] = x;
        fd_50F6_0404[fd_50F6_0476] = y;
        otile = fd_3E1D_0180[x][y];
        if (otile < 4) {
            if (type != 0)
                fd_3E1D_0180[x][y] = SRand1(2) + otile * 4 + 0xa;
            else
                fd_3E1D_0180[x][y] = SRand1(2) + (otile + 2) * 4;
        }
    }
    fd_3E1D_6180[x][y] = 0;
}

int far f_0894_21C5(int dir)
{
    return fd_3D57_0024[dir][SRand8()];
}

void far f_0894_21ED(int index)
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

    x = fd_3E1D_A180[index];
    y = fd_3E1D_A569[index];
    attribute = fd_3E1D_AD3B[index];
    if (f_0894_23BB(x, y)) {
        f_0894_1C6E(x, y, index);
        return;
    }
    caste = (attribute & 0x78) >> 3;
    if (fd_3D57_0074[caste] == 1)
        attribute = (fd_3D57_0094[caste] << 3) | (attribute & 0x87);
    flags = attribute & 0xf8;
    dir = f_1383_0C2A(x, y, attribute & 7, attribute ^ 0x80);
    nx = x + fd_3D57_0000[dir];
    ny = y + fd_3D57_0008[dir];
    if (fd_3E1D_0180[nx][ny] > fd_50F6_0480) {
        fd_3E1D_AD3B[index] = f_0894_21C5(attribute & 7) | flags;
        fd_3E1D_6180[x][y] = fd_3E1D_AD3B[index];
        return;
    }
    tile = fd_3E1D_6180[nx][ny];
    if (tile == 0) {
        fd_3E1D_AD3B[index] = fd_3E1D_6180[nx][ny] = dir | flags;
        fd_3E1D_6180[x][y] = 0;
        fd_3E1D_A180[index] = nx;
        fd_3E1D_A569[index] = ny;
        return;
    }
    if (f_10F7_003A(tile) == 1) {
        if ((fd_50F6_04E2 ^ attribute) & 0x80) {
            o25_3BA4_0DFB(1, index);
            return;
        }
        fd_3E1D_AD3B[index] = f_0894_21C5(attribute & 7) | flags;
        fd_3E1D_6180[x][y] = fd_3E1D_AD3B[index];
        return;
    }
    if (((tile ^ attribute) & 0x80) == 0) {
        fd_3E1D_AD3B[index] = f_0894_21C5(attribute & 7) | flags;
        fd_3E1D_6180[x][y] = fd_3E1D_AD3B[index];
        return;
    }
    f_0894_1D89(index, x, y, nx, ny);
}

int far f_0894_23BB(int x, int y)
{
    int tile;

    if (f_10F7_2867(x, y) == 0)
        return 0;
    if (fd_50F6_0F24 == 0) {
        if (fd_3E1D_0180[x][y] == 0x50)
            return 1;
        return 0;
    }
    tile = fd_3E1D_0180[x][y];
    if (tile < 0x80)
        return 0;
    if (tile > 0x8f)
        return 0;
    return 1;
}

int far f_0894_2423(int tile)
{
    if (fd_50F6_0F24 == 0) {
        if (tile < 0x48 || tile > 0x4b)
            return 0;
        return 1;
    }
    if (tile < 0x18 || tile > 0x27)
        return 0;
    return 1;
}
