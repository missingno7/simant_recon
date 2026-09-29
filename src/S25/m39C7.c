/* Overlay section S25, code frame 39C7: black colony nest simulation (DoAntSimB unit). */

extern int far fd_50F6_0DA8;
extern int far fd_50F6_0F18;
extern unsigned char far fd_3E1D_B50D[];
extern unsigned char far fd_3E1D_B702[];
extern unsigned char far fd_3E1D_BAEC[];
void far o25_39C7_006D(int x, int y, int attr);

void far o25_39C7_0000(void)
{
    int x;
    int y;
    int attr;

    fd_50F6_0F18 = fd_50F6_0DA8;
    while (fd_50F6_0F18 > 0) {
        --fd_50F6_0F18;
        x = fd_3E1D_B50D[fd_50F6_0F18];
        y = fd_3E1D_B702[fd_50F6_0F18] & 0xff;
        attr = fd_3E1D_BAEC[fd_50F6_0F18];
        if (attr != 0)
            o25_39C7_006D(x, y, attr);
    }
}

extern unsigned char far fd_3E1D_B8F7[];
extern int far fd_50F6_0D40[];
extern int far SRand256(void);
extern int far SRand32(void);
extern int far fd_50F6_10BE;
extern unsigned char far fd_3E1D_8180[64][64];
extern long far fd_50F6_0F30;
void far o25_39C7_0677(int x, int y, int attr, int caste);
void far DoNestingB(int x, int y, int attr, int caste);
void far DoFoodInB(int x, int y, int attr);
void far DoDigInB(int x, int y, int attr, int caste);
void far o25_39C7_06E2(int x, int y, int attr);
void far o25_39C7_0980(int x, int y);
void far o25_39C7_0AB0(int x, int y, int caste, int attr);
void far o25_39C7_0746(int x, int y);
void far o25_39C7_04E5(int x, int y, int attr);
extern int far fd_50F6_08DC;
void far DoDigOutB(int x, int y, int attr);
void far o25_39C7_0590(int x, int y, int attr);
extern int far fd_50F6_0D72[];
extern int far f_10F7_003A(int value);
extern int far fd_50F6_04E2;
extern void far o25_3BA4_0DFB(int list, int index);
extern int far f_0EC1_02DD(int x, int y, int life);
void far o25_39C7_0F30(int index);
extern long far fd_50F6_1000;
extern int far f_0894_1E34(int a, int b);
extern unsigned char far fd_3E1D_BCE1[];
void far o25_39C7_038F(int x, int y, int attr);
void far o25_39C7_0460(int x, int y, int attr);

void far o25_39C7_006D(int x, int y, int attr)
{
    int caste;
    int task;
    int i;
    int t;

    caste = (attr & 0x78) >> 3;
    if (!(attr & 0x80)) {
        t = fd_3E1D_B8F7[fd_50F6_0F18];
        fd_50F6_0D40[t]++;
        if (SRand256() == 0 && t != 9 && SRand32() > fd_50F6_10BE) {
            fd_3E1D_BAEC[fd_50F6_0F18] = 0;
            fd_3E1D_8180[x][y] = 0;
            fd_50F6_0F30++;
            return;
        }
        switch (t) {
        case 0:
            o25_39C7_0677(x, y, attr, caste);
            break;
        case 1:
            DoNestingB(x, y, attr, caste);
            break;
        case 2:
            DoDigOutB(x, y, attr);
            break;
        case 3:
            DoFoodInB(x, y, attr);
            break;
        case 4:
            DoDigInB(x, y, attr, caste);
            break;
        case 5:
            DoDigOutB(x, y, attr);
            break;
        case 6:
            o25_39C7_06E2(x, y, attr);
            break;
        case 7:
            DoDigOutB(x, y, attr);
            break;
        case 8:
            o25_39C7_0980(x, y);
            break;
        case 9:
            o25_39C7_0AB0(x, y, caste, attr);
            break;
        case 10:
            o25_39C7_0746(x, y);
            break;
        case 11:
        case 12:
            DoDigOutB(x, y, attr);
            break;
        case 13:
            o25_39C7_04E5(x, y, attr);
            break;
        case 14:
            o25_39C7_0677(x, y, attr, caste);
            if (fd_50F6_08DC > 100)
                fd_3E1D_B8F7[fd_50F6_0F18] = 0xf;
            break;
        case 15:
        case 16:
            DoDigOutB(x, y, attr);
            break;
        case 17:
            o25_39C7_0590(x, y, attr);
            break;
        default:
            o25_39C7_0677(x, y, attr, caste);
            break;
        }
    } else {
        task = fd_3E1D_B8F7[fd_50F6_0F18];
        fd_50F6_0D72[task]++;
        if (attr > 0xef) {
            o25_39C7_0746(x, y);
            return;
        }
        caste = fd_3E1D_8180[x][y];
        if (f_10F7_003A(caste) == 1 && fd_50F6_04E2 == 0) {
            o25_3BA4_0DFB(2, fd_50F6_0F18);
            return;
        }
        if (caste > 0 && caste < 0x68 && (i = f_0EC1_02DD(x, y, caste)) >= 0) {
            if (caste > 0x5f)
                o25_39C7_0F30(i);
            if (caste < 8) {
                fd_3E1D_B8F7[fd_50F6_0F18] = 3;
                fd_3E1D_BAEC[fd_50F6_0F18] |= 8;
                fd_3E1D_8180[x][y] = fd_3E1D_BAEC[fd_50F6_0F18];
                fd_3E1D_BAEC[i] = 0;
                fd_50F6_1000++;
            } else {
                t = f_0894_1E34(fd_3E1D_BAEC[i], attr);
                fd_3E1D_BAEC[fd_50F6_0F18] = 0;
                fd_3E1D_BCE1[i] = t;
                fd_3E1D_8180[x][y] = fd_3E1D_BAEC[i] = (t & 0x80) + 0x70;
                fd_3E1D_B8F7[i] = 0xa;
            }
            return;
        }
        switch (task) {
        case 7:
            o25_39C7_038F(x, y, attr);
            break;
        default:
            o25_39C7_0460(x, y, attr);
            break;
        }
    }
}

extern unsigned char far fd_3E1D_2180[64][64];
void far o25_39C7_154F(int x, int y);
extern int far SRand1(int range);
int far o25_39C7_105B(int x, int y, int dir);
extern int far f_0BE8_0D67(int x, int y, int dir);
extern int far f_0BE8_0C0F(int x, int y, int limit);
extern int far SRand8(void);
int far o25_39C7_0853(int x, int y, int attacker);
extern int far f_1383_0976(int caste, int type);
extern int far fd_3D57_07A8[];
extern void far f_0250_43F2(int x, int y, int plane);

void far o25_39C7_038F(int x, int y, int dirHint)
{
    int dir;

    if (fd_3E1D_2180[x][y] >= 0x10 && fd_3E1D_2180[x][y] <= 0x13) {
        o25_39C7_154F(x, y);
        fd_3E1D_B8F7[fd_50F6_0F18] = 3;
        fd_3E1D_BAEC[fd_50F6_0F18] |= 8;
        fd_3E1D_8180[x][y] = fd_3E1D_BAEC[fd_50F6_0F18];
        return;
    }
    dir = (SRand1(3) + dirHint - 2) & 7;
    if (o25_39C7_105B(x, y, dir) != 0)
        return;
    dir = f_0BE8_0D67(x, y, dirHint & 7);
    if (dir < 0)
        dir = SRand1(8);
    if (o25_39C7_105B(x, y, dir) != 0)
        return;
    fd_3E1D_B8F7[fd_50F6_0F18] = 1;
    fd_3E1D_8180[x][y] = fd_3E1D_BAEC[fd_50F6_0F18];
}

void far o25_39C7_0460(int x, int y, int attr)
{
    int dir;

    dir = f_0BE8_0C0F(x, y, 8);
    if (dir == 0)
        dir = SRand8();
    else
        dir--;
    if (o25_39C7_105B(x, y, dir) == 0) {
        if (o25_39C7_105B(x, y, SRand8()) == 0)
            fd_3E1D_8180[x][y] = fd_3E1D_BAEC[fd_50F6_0F18];
    }
}

void far o25_39C7_04E5(int x, int y, int attacker)
{
    int type;

    if (o25_39C7_0853(x, y, attacker) == 1)
        return;
    fd_3E1D_8180[x][y] = fd_3E1D_BAEC[fd_50F6_0F18];
    if (SRand1(20) == 0) {
        type = fd_3E1D_BAEC[fd_50F6_0F18];
        fd_3E1D_B8F7[fd_50F6_0F18] = f_1383_0976((type & 0x78) >> 3, type);
        return;
    }
    if (fd_3D57_07A8[5] == 1)
        f_0250_43F2(x, y, 2);
}

extern int far f_1383_099B(int caste);
extern long far fd_50F6_0FBC;
extern int far fd_50F6_048C;

void far o25_39C7_0590(int x, int y, int attr)
{
    if (fd_3E1D_2180[x][y] < 0x14) {
        fd_3E1D_B8F7[fd_50F6_0F18] = f_1383_099B((attr & 0x78) >> 3);
        return;
    }
    attr = ((SRand1(3) + attr - 1) & 7) | (attr & 0xf8);
    fd_3E1D_8180[x][y] = fd_3E1D_BAEC[fd_50F6_0F18] = attr;
    if (SRand1(100) == 0) {
        fd_3E1D_BAEC[fd_50F6_0F18] = fd_3E1D_8180[x][y] = 0;
        if (attr & 0x80)
            fd_50F6_0FBC++;
        else
            fd_50F6_0F30++;
    }
}

void far o25_39C7_0677(int x, int y, int attr, int caste)
{
    if (SRand32() == 0)
        fd_3E1D_B8F7[fd_50F6_0F18] = f_1383_099B(caste);
    if (o25_39C7_0853(x, y, attr) == 1)
        return;
    if (o25_39C7_105B(x, y, attr & 7) != 0)
        return;
    o25_39C7_105B(x, y, SRand8());
}

void far o25_39C7_06E2(int x, int y, int attr)
{
    if (fd_50F6_048C != 2) {
        DoDigOutB(x, y, attr);
        return;
    }
    if (o25_39C7_0853(x, y, attr) == 1)
        return;
    if (o25_39C7_105B(x, y, attr & 7) != 0)
        return;
    o25_39C7_105B(x, y, SRand8());
}

extern int far SRand16(void);
void far o25_39C7_0EC2(int index);
extern void far f_0250_4302(int x, int y, int plane);
extern int far fd_50F6_1050;

void far o25_39C7_0746(int x, int y)
{
    fd_3E1D_BAEC[fd_50F6_0F18] = (fd_3E1D_BAEC[fd_50F6_0F18] & 0xf8) + SRand1(7);
    fd_3E1D_8180[x][y] = fd_3E1D_BAEC[fd_50F6_0F18];
    if (SRand16() == 0) {
        fd_3E1D_BAEC[fd_50F6_0F18] = fd_3E1D_8180[x][y] = fd_3E1D_BCE1[fd_50F6_0F18];
        if ((fd_3E1D_BAEC[fd_50F6_0F18] & 0x78) == 0x60)
            o25_39C7_0EC2(fd_50F6_0F18);
        if (fd_3E1D_BAEC[fd_50F6_0F18] & 0x80)
            fd_3E1D_B8F7[fd_50F6_0F18] = 7;
        else
            fd_3E1D_B8F7[fd_50F6_0F18] = f_1383_0976((fd_3E1D_BAEC[fd_50F6_0F18] & 0x78) >> 3, fd_3E1D_BAEC[fd_50F6_0F18]);
    } else if (fd_3D57_07A8[5] == 1)
        f_0250_4302(x, y, 2);
}

int far o25_39C7_0853(int x, int y, int attacker)
{
    int ant;
    int index;
    int winner;

    ant = fd_3E1D_8180[x][y];
    if (f_10F7_003A(ant) == 1 && fd_50F6_04E2 != 0) {
        o25_3BA4_0DFB(2, fd_50F6_0F18);
        return 1;
    }
    if (ant > 0x87 && ant < 0xe8 && (index = f_0EC1_02DD(x, y, ant)) >= 0) {
        winner = f_0894_1E34(ant, attacker);
        fd_3E1D_BCE1[index] = winner;
        fd_3E1D_8180[x][y] = fd_3E1D_BAEC[index] = (winner & 0x80) + 0x70;
        fd_3E1D_B8F7[index] = 0xa;
        return 1;
    }
    return 0;
}

int far o25_39C7_090A(int x, int y)
{
    int result;
    int food;

    result = 0;
    food = fd_3E1D_2180[x][y];
    if (food < 0x10) {
        fd_3E1D_2180[x][y] = 0x10;
        result = 1;
    } else if (food < 0x13) {
        fd_3E1D_2180[x][y]++;
        result = 1;
    }
    fd_50F6_1050++;
    if (fd_3E1D_BAEC[fd_50F6_0F18] & 8)
        fd_3E1D_BAEC[fd_50F6_0F18] -= 8;
    return result;
}

extern int far fd_50F6_0330;
extern int far fd_50F6_0F08;
extern int far fd_50F6_0378;
extern int far f_0093_002B(int range);
extern unsigned int far fd_50F6_04A2;
extern int far fd_3D57_0C0E;
extern void far f_0250_428A(int x, int y, int plane);

void far o25_39C7_0980(int x, int y)
{
    int attr;
    int mode;
    int mask;

    attr = fd_3E1D_BAEC[fd_50F6_0F18];
    mode = -1;
    if (fd_50F6_0330 <= 2)
        mask = 0x1f;
    else
        mask = 0x7f;
    if (!(fd_50F6_0F08 & mask)) {
        attr++;
        if ((attr & 0xf) == 8) {
            if (fd_50F6_0378 != 0 || (int)(fd_50F6_04A2 >> 7) >= f_0093_002B(255)) {
                mode = fd_3D57_0C0E;
                attr = (mode << 3) + 2;
                if (mode == 2)
                    fd_3E1D_B8F7[fd_50F6_0F18] = 1;
                else
                    fd_3E1D_B8F7[fd_50F6_0F18] = f_1383_099B(mode);
            } else {
                attr = 0;
                fd_50F6_1000++;
            }
        }
    }
    if (fd_3D57_07A8[5] != 0 && mode < 0)
        f_0250_428A(x, y, 2);
    fd_3E1D_8180[x][y] = attr;
    fd_3E1D_BAEC[fd_50F6_0F18] = attr;
    fd_3E1D_BCE1[fd_50F6_0F18] = 0;
}

extern int far SRand64(void);
extern void far o14_384C_0B6A(int a, int b, int c);
int far o25_39C7_0DAF(int x, int y, int dirHint);
int far o25_39C7_0FE7(int x, int y, int attr);
extern int far fd_50F6_035E;
extern void far f_0250_437A(int x, int y, int plane);
int far o25_39C7_0F76(int x, int y, int attr);
extern signed char far fd_3D57_0008[];
extern signed char far fd_3D57_0000[];
extern int far f_0BE8_0BC1(int x, int y);
extern int far fd_3D57_02B4[2];
extern int far SRand128(void);
extern void far f_0BE8_0A5B(int x, int y, int type);
void far o25_39C7_15B4(void);
extern long far fd_50F6_0FC2;

void far o25_39C7_0AB0(int x, int y, int caste, int attr)
{
    int t;
    int nx;
    int ny;

    if (caste == 12) {
        if (SRand64() == 0) {
            if (fd_50F6_10BE == 0) {
                fd_3E1D_8180[x][y] = fd_3E1D_BAEC[fd_50F6_0F18] = 0;
                o14_384C_0B6A(0, 0x271f, 1);
                return;
            }
            if (o25_39C7_0DAF(x, y, attr) != 0)
                return;
        }
        t = fd_3E1D_BAEC[fd_50F6_0F18];
        if (o25_39C7_0FE7(x, y, t) != 0) {
            t = 0;
            fd_3E1D_BAEC[fd_50F6_0F18] = 0;
            fd_50F6_035E--;
        }
        fd_3E1D_8180[x][y] = t;
        if (fd_3D57_07A8[5] != 0)
            f_0250_437A(x, y, 2);
    } else if (caste == 13) {
        t = fd_3E1D_BAEC[fd_50F6_0F18];
        fd_3E1D_8180[x][y] = t;
        if (fd_50F6_035E > 0 && o25_39C7_0F76(x, y, t) != 0) {
            fd_50F6_035E--;
            fd_3E1D_8180[x][y] = fd_3E1D_BAEC[fd_50F6_0F18] = 0;
            return;
        }
        nx = fd_3D57_0000[(attr ^ 4) & 7] + x;
        ny = fd_3D57_0008[(attr ^ 4) & 7] + y;
        if (f_0BE8_0BC1(nx, ny)) {
            fd_3D57_02B4[0] = nx;
            fd_3D57_02B4[1] = ny;
            if (!(fd_50F6_0F08 & 0xf) && SRand128() <= fd_50F6_10BE) {
                f_0BE8_0A5B(nx, ny, 1);
                o25_39C7_15B4();
                fd_50F6_0FC2++;
            }
        }
    }
}

/* SCAFFOLD BEGIN: unrecovered same-module callees */
void far o25_39C7_0F30(int index) { }
void far DoNestingB(int x, int y, int attr, int caste) { }
void far DoFoodInB(int x, int y, int attr) { }
void far DoDigInB(int x, int y, int attr, int caste) { }
void far DoDigOutB(int x, int y, int attr) { }
void far o25_39C7_154F(int x, int y) { }
int far o25_39C7_105B(int x, int y, int dir) { return 0; }
void far o25_39C7_0EC2(int index) { }
int far o25_39C7_0DAF(int x, int y, int dirHint) { return 0; }
int far o25_39C7_0FE7(int x, int y, int attr) { return 0; }
int far o25_39C7_0F76(int x, int y, int attr) { return 0; }
void far o25_39C7_15B4(void) { }
/* SCAFFOLD END */
