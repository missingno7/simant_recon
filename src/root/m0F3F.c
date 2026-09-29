/* Root module, code frame 0F3F: red colony nest ants (DoAntSimR, R-list ants).
 * MSC 6.00A /AL /Os /Oe /Og. */

extern int far fd_50F6_0F18;
extern int far fd_50F6_0EAA;
extern unsigned char far fd_3E1D_BED6[];
extern unsigned char far fd_3E1D_C0CB[];
extern unsigned char far fd_3E1D_C4B5[];
extern unsigned char far fd_3E1D_C2C0[];
extern int far fd_50F6_0D72[20];
extern int far SRand256(void);
extern int far SRand32(void);
extern int far fd_50F6_01FE;
extern unsigned char far fd_3E1D_9180[64][64];
extern long far fd_50F6_0FBC;
extern int far fd_50F6_08E8;
extern int far fd_50F6_0D40[20];
extern int far f_0EC1_032C(int x, int y, int ant);
extern int far f_0894_1E34(int a, int b);
extern unsigned char far fd_3E1D_C6AA[];
extern int far fd_50F6_048C;
extern unsigned char far fd_3E1D_3180[64][64];
extern int far SRand1(int range);
extern int far f_0BE8_0E0F(int x, int y, int dir);
extern int far f_0BE8_0CBB(int x, int y, int dir);
extern int far SRand8(void);
extern int far f_1383_0976(int caste, int type);
extern int far fd_3D57_07B2;
extern void far f_0250_43F2(int x, int y, int plane);
extern int far f_1383_0A30(int mode);
extern long far fd_50F6_0F30;
extern int far SRand16(void);
extern void far f_0250_4302(int x, int y, int plane);
extern int far f_10F7_003A(int value);
extern int far fd_50F6_04E2;
extern void far o25_3BA4_0DFB(int a, int index);
extern int far fd_50F6_1060;
extern int far fd_50F6_0350;
extern int far fd_50F6_0F08;
extern signed char far fd_3D57_0B36[];
extern int far fd_50F6_10A6;
extern void far f_0250_428A(int x, int y, int plane);
extern int far SRand64(void);
extern void far o14_384C_0B6A(int a, int b, int c);
extern int far fd_50F6_036C;
extern void far f_0250_437A(int x, int y, int plane);
extern signed char far fd_3D57_0000[8];
extern signed char far fd_3D57_0008[8];
extern int far f_0BE8_0BC1(int x, int y);
extern int far fd_3D57_02B8[2];
extern int far SRand128(void);
extern void far f_0BE8_0ABE(int x, int y, int life);
extern int far o25_39C7_0CBD(int kind, int x, int y, int tx, int ty);
extern int far fd_50F6_0200;
extern int far fd_50F6_020E;
extern void far f_0EC1_0651(int x, int y, int type, int mode, int state);
extern int far SRand4(void);
extern int far fd_50F6_0AFA[6];
extern int far fd_50F6_0226;
extern int far IsItDirt(int value);
extern int far DigTileThemR(int x, int y);
extern void far f_00DF_00E8(int a, int b, int c);
extern void far f_14EE_0D71(int x, int y);
extern void far f_0EC1_05D4(int x, int y, int type, int mode, int state);
extern unsigned char far fd_3E1D_8180[64][64];
extern int far f_0894_21C5(int dir);
extern unsigned char far fd_3E1D_5180[64][64];
extern unsigned char far fd_3D57_0264[];
extern void far f_14EE_0367(int x);
extern int far f_0EC1_0437(int hole, int x, int type, int mode, int state);
extern int far SRand2(void);



void far f_0F3F_0075(int x, int y, int attr);
void far f_0F3F_03B0(int x, int y, int dirHint);
void far f_0F3F_0481(int x, int y, int dirHint);
void far f_0F3F_0569(int x, int y, int attr);
void far f_0F3F_05EE(int x, int y, int attacker);
void far f_0F3F_069A(int x, int y, int attr);
void far f_0F3F_0781(int x, int y, int attr, int modeArg);
void far f_0F3F_07ED(int x, int y);
int far f_0F3F_08F6(int x, int y, int attacker);
void far f_0F3F_0A26(int x, int y);
void far f_0F3F_0B1F(int x, int y, int caste, int attr);
void far f_0F3F_0E30(int index);
void far f_0F3F_0E9E(int index);
int far f_0F3F_0FC9(int x, int y, int dir);
void far f_0F3F_10A1(int x, int y, int attr, int caste);
void far f_0F3F_13D7(int x, int y);
int far f_0F3F_0D1B(int x, int y, int dirHint);
int far f_0F3F_0EE4(int x, int y, int attr);
int far f_0F3F_0F55(int x, int y, int attr);
void far f_0F3F_1277(int y, int x);
void far f_0F3F_1330(int x, int y);
void far f_0F3F_143C(void);
int far f_0F3F_09B0(int x, int y);
int far f_0F3F_1A37(int x);
void far f_0F3F_1474(int x, int y, int attr);
void far DoDigInR(int x, int y, int attr, int caste);
void far f_0F3F_186B(int x, int y, int attr);

void far f_0F3F_0008(void)
{
    int x;
    int y;
    int attr;

    fd_50F6_0F18 = fd_50F6_0EAA;
    while (fd_50F6_0F18 > 0) {
        --fd_50F6_0F18;
        x = fd_3E1D_BED6[fd_50F6_0F18];
        y = fd_3E1D_C0CB[fd_50F6_0F18];
        attr = fd_3E1D_C4B5[fd_50F6_0F18];
        if (attr != 0)
            f_0F3F_0075(x, y, attr);
    }
}

/* SCAFFOLD BEGIN: f_0F3F_0075 (DoNestAntR) best draft, 1 byte differs: the red branch indexes
   TemRModePop with `mov bx,ax` where the original has `mov bx,si` (mode already copied to SI).
   Tried: ++/+=/embedded assignment, unsigned/char/register mode, per-branch mode variables,
   all 120 local declaration orders. */
void far f_0F3F_0075(int x, int y, int attr)
{
    int caste;
    int mode;
    int ant;
    int index;
    int winner;

    caste = (attr & 0x78) >> 3;
    if (attr & 0x80) {
        mode = fd_3E1D_C2C0[fd_50F6_0F18];
        fd_50F6_0D72[mode]++;
        if (SRand256() == 0 && mode != 9 && SRand32() > fd_50F6_01FE) {
            fd_3E1D_C4B5[fd_50F6_0F18] = 0;
            fd_3E1D_9180[x][y] = 0;
            fd_50F6_0FBC++;
            return;
        }
        switch (mode) {
        case 0:
            f_0F3F_0781(x, y, attr, caste);
            break;
        case 1:
            f_0F3F_10A1(x, y, attr, caste);
            break;
        case 2:
            f_0F3F_186B(x, y, attr);
            break;
        case 3:
            f_0F3F_1474(x, y, attr);
            break;
        case 4:
            DoDigInR(x, y, attr, caste);
            break;
        case 5:
        case 6:
        case 7:
            f_0F3F_186B(x, y, attr);
            break;
        case 8:
            f_0F3F_0A26(x, y);
            break;
        case 9:
            f_0F3F_0B1F(x, y, caste, attr);
            break;
        case 10:
            f_0F3F_07ED(x, y);
            break;
        case 11:
        case 12:
            f_0F3F_186B(x, y, attr);
            break;
        case 13:
            f_0F3F_05EE(x, y, attr);
            break;
        case 14:
            f_0F3F_0781(x, y, attr, caste);
            if (fd_50F6_08E8 > 100)
                fd_3E1D_C2C0[fd_50F6_0F18] = 0xf;
            break;
        case 15:
        case 16:
            f_0F3F_186B(x, y, attr);
            break;
        case 17:
            f_0F3F_069A(x, y, attr);
            break;
        default:
            f_0F3F_0781(x, y, attr, caste);
            break;
        }
        return;
    }
    mode = fd_3E1D_C2C0[fd_50F6_0F18];
    fd_50F6_0D40[mode]++;
    if (attr < 8) {
        fd_3E1D_C4B5[fd_50F6_0F18] = 0;
        fd_3E1D_9180[fd_3E1D_BED6[fd_50F6_0F18]][fd_3E1D_C0CB[fd_50F6_0F18]] = 0;
        return;
    }
    if (attr > 0x6f) {
        f_0F3F_07ED(x, y);
        return;
    }
    ant = fd_3E1D_9180[x][y];
    if (ant > 0x80 && ant < 0xe8 && (index = f_0EC1_032C(x, y, ant)) >= 0) {
        if (ant > 0xdf)
            f_0F3F_0E9E(index);
        if (ant < 0x88) {
            fd_3E1D_C2C0[fd_50F6_0F18] = 3;
            fd_3E1D_C4B5[fd_50F6_0F18] |= 8;
            fd_3E1D_9180[x][y] = fd_3E1D_C4B5[fd_50F6_0F18];
            fd_3E1D_C4B5[index] = 0;
            return;
        }
        winner = f_0894_1E34(fd_3E1D_C4B5[index], attr);
        fd_3E1D_C4B5[fd_50F6_0F18] = 0;
        fd_3E1D_C6AA[index] = winner;
        fd_3E1D_9180[x][y] = fd_3E1D_C4B5[index] = (winner & 0x80) + 0x70;
        fd_3E1D_C2C0[index] = 0xa;
        return;
    }
    switch (mode) {
    case 6:
        if (fd_50F6_048C == 3)
            f_0F3F_0481(x, y, attr);
        else
            f_0F3F_0569(x, y, attr);
        break;
    case 7:
        f_0F3F_03B0(x, y, attr);
        break;
    default:
        f_0F3F_0569(x, y, attr);
        break;
    }
}
/* SCAFFOLD END */

void far f_0F3F_03B0(int x, int y, int dirHint)
{
    int dir;

    if (fd_3E1D_3180[x][y] >= 0x10 && fd_3E1D_3180[x][y] <= 0x13) {
        f_0F3F_13D7(x, y);
        fd_3E1D_C2C0[fd_50F6_0F18] = 3;
        fd_3E1D_C4B5[fd_50F6_0F18] |= 8;
        fd_3E1D_9180[x][y] = fd_3E1D_C4B5[fd_50F6_0F18];
        return;
    }
    if (f_0F3F_0FC9(x, y, (SRand1(3) + dirHint - 2) & 7))
        return;
    dir = f_0BE8_0E0F(x, y, dirHint & 7);
    if (dir < 0)
        dir = SRand1(8);
    if (f_0F3F_0FC9(x, y, dir))
        return;
    fd_3E1D_C2C0[fd_50F6_0F18] = 1;
    fd_3E1D_9180[x][y] = fd_3E1D_C4B5[fd_50F6_0F18];
}

void far f_0F3F_0481(int x, int y, int dirHint)
{
    int dir;

    if (fd_3E1D_3180[x][y] >= 0x10 && fd_3E1D_3180[x][y] <= 0x13) {
        f_0F3F_13D7(x, y);
        fd_3E1D_C2C0[fd_50F6_0F18] = 3;
        fd_3E1D_C4B5[fd_50F6_0F18] |= 8;
        fd_3E1D_9180[x][y] = fd_3E1D_C4B5[fd_50F6_0F18];
        return;
    }
    dir = (SRand1(3) + dirHint - 2) & 7;
    fd_3E1D_C4B5[fd_50F6_0F18] = (fd_3E1D_C4B5[fd_50F6_0F18] & 0xf8) | dir;
    if (f_0F3F_0FC9(x, y, dir))
        return;
    dir = f_0BE8_0E0F(x, y, dirHint & 7);
    if (dir < 0)
        dir = SRand1(8);
    if (f_0F3F_0FC9(x, y, dir))
        return;
    fd_3E1D_9180[x][y] = fd_3E1D_C4B5[fd_50F6_0F18];
}

void far f_0F3F_0569(int x, int y, int attr)
{
    int dir;

    dir = f_0BE8_0CBB(x, y, 8);
    if (dir == 0)
        dir = SRand8();
    else
        dir--;
    if (f_0F3F_0FC9(x, y, dir) == 0) {
        if (f_0F3F_0FC9(x, y, SRand8()) == 0)
            fd_3E1D_9180[x][y] = fd_3E1D_C4B5[fd_50F6_0F18];
    }
}

void far f_0F3F_05EE(int x, int y, int attacker)
{
    int type;

    if (f_0F3F_08F6(x, y, attacker))
        return;
    fd_3E1D_9180[x][y] = fd_3E1D_C4B5[fd_50F6_0F18];
    if (SRand1(20) == 0) {
        type = fd_3E1D_C4B5[fd_50F6_0F18];
        fd_3E1D_C2C0[fd_50F6_0F18] = f_1383_0976((type & 0x78) >> 3, type);
        return;
    }
    if (fd_3D57_07B2 != 0)
        f_0250_43F2(x, y, 3);
}

void far f_0F3F_069A(int x, int y, int attr)
{
    if (fd_3E1D_3180[x][y] < 0x14) {
        fd_3E1D_C2C0[fd_50F6_0F18] = f_1383_0A30((attr & 0x78) >> 3);
        return;
    }
    attr = ((SRand1(3) + attr - 1) & 7) | (attr & 0xf8);
    fd_3E1D_C4B5[fd_50F6_0F18] = attr;
    fd_3E1D_9180[x][y] = attr;
    if (SRand1(100) == 0) {
        fd_3E1D_C4B5[fd_50F6_0F18] = fd_3E1D_9180[x][y] = 0;
        if (attr & 0x80)
            fd_50F6_0FBC++;
        else
            fd_50F6_0F30++;
    }
}

void far f_0F3F_0781(int x, int y, int attr, int modeArg)
{
    if (SRand32() == 0)
        fd_3E1D_C2C0[fd_50F6_0F18] = f_1383_0A30(modeArg);
    if (f_0F3F_08F6(x, y, attr))
        return;
    if (f_0F3F_0FC9(x, y, attr & 7))
        return;
    f_0F3F_0FC9(x, y, SRand8());
}

static unsigned char near nestFightMode[16] = {
    1, 1, 1, 3, 0, 5, 2, 3, 0, 5, 0, 0, 9, 9, 10, 0
};

void far f_0F3F_07ED(int x, int y)
{
    fd_3E1D_C4B5[fd_50F6_0F18] = (fd_3E1D_C4B5[fd_50F6_0F18] & 0xf8) + SRand1(7);
    fd_3E1D_9180[x][y] = fd_3E1D_C4B5[fd_50F6_0F18];
    if (SRand16() == 0) {
        fd_3E1D_C4B5[fd_50F6_0F18] = fd_3E1D_9180[x][y] = fd_3E1D_C6AA[fd_50F6_0F18];
        if ((fd_3E1D_C4B5[fd_50F6_0F18] & 0x78) == 0x60)
            f_0F3F_0E30(fd_50F6_0F18);
        if (!(fd_3E1D_C4B5[fd_50F6_0F18] & 0x80))
            fd_3E1D_C2C0[fd_50F6_0F18] = 7;
        else
            fd_3E1D_C2C0[fd_50F6_0F18] = nestFightMode[(fd_3E1D_C4B5[fd_50F6_0F18] & 0x78) >> 3];
    } else if (fd_3D57_07B2 != 0)
        f_0250_4302(x, y, 3);
}

int far f_0F3F_08F6(int x, int y, int attacker)
{
    int ant;
    int index;
    int winner;

    ant = fd_3E1D_9180[x][y];
    if (ant > 7 && ant < 0x68) {
        index = f_0EC1_032C(x, y, ant);
        if (index >= 0) {
            winner = f_0894_1E34(ant, attacker);
            fd_3E1D_C6AA[index] = winner;
            fd_3E1D_C4B5[index] = (winner & 0x80) + 0x70;
            fd_3E1D_9180[x][y] = (winner & 0x80) + 0x70;
            fd_3E1D_C2C0[index] = 0xa;
            return 1;
        }
    } else if (f_10F7_003A(ant) && fd_50F6_04E2 == 0) {
        o25_3BA4_0DFB(3, fd_50F6_0F18);
        return 1;
    }
    return 0;
}

int far f_0F3F_09B0(int x, int y)
{
    int level;
    int result;

    result = 0;
    level = fd_3E1D_3180[x][y];
    if (level < 16) {
        fd_3E1D_3180[x][y] = 16;
        result = 1;
    } else if (level < 19) {
        fd_3E1D_3180[x][y]++;
        result = 1;
    }
    ++fd_50F6_1060;
    if (fd_3E1D_C4B5[fd_50F6_0F18] & 8)
        fd_3E1D_C4B5[fd_50F6_0F18] -= 8;
    return result;
}

void far f_0F3F_0A26(int x, int y)
{
    int attr;
    int mode;
    int mask;

    attr = fd_3E1D_C4B5[fd_50F6_0F18];
    mode = -1;
    if (fd_50F6_0350 == 1)
        mask = 0x1f;
    else
        mask = 0x7f;
    if (!(fd_50F6_0F08 & mask)) {
        attr++;
        if ((attr & 0xf) == 8) {
            mode = fd_3D57_0B36[((fd_50F6_10A6 % 7) << 3) + SRand8()];
            attr = (mode << 3) + 0x82;
            fd_3E1D_C2C0[fd_50F6_0F18] = f_1383_0A30(mode);
        }
    }
    if (fd_3D57_07B2 != 0 && mode < 0)
        f_0250_428A(x, y, 3);
    fd_3E1D_9180[x][y] = attr;
    fd_3E1D_C4B5[fd_50F6_0F18] = attr;
    fd_3E1D_C6AA[fd_50F6_0F18] = 0;
}

void far f_0F3F_0B1F(int x, int y, int caste, int attr)
{
    int type;
    int nx;
    int ny;

    if (caste == 12) {
        if (SRand64() == 0) {
            if (fd_50F6_01FE == 0) {
                fd_3E1D_9180[x][y] = fd_3E1D_C4B5[fd_50F6_0F18] = 0;
                o14_384C_0B6A(0, 0x2720, 1);
                return;
            }
            if (f_0F3F_0D1B(x, y, attr))
                return;
        }
        type = fd_3E1D_C4B5[fd_50F6_0F18];
        if (f_0F3F_0F55(x, y, type)) {
            type = 0;
            fd_3E1D_C4B5[fd_50F6_0F18] = 0;
            fd_50F6_036C--;
        }
        fd_3E1D_9180[x][y] = type;
        if (fd_3D57_07B2 != 0)
            f_0250_437A(x, y, 3);
    } else if (caste == 13) {
        type = fd_3E1D_C4B5[fd_50F6_0F18];
        fd_3E1D_9180[x][y] = type;
        if (fd_50F6_036C > 0 && f_0F3F_0EE4(x, y, type)) {
            fd_50F6_036C--;
            fd_3E1D_9180[x][y] = fd_3E1D_C4B5[fd_50F6_0F18] = 0;
            return;
        }
        nx = x + fd_3D57_0000[(attr ^ 0xfc) & 7];
        ny = y + fd_3D57_0008[(attr ^ 0xfc) & 7];
        if (f_0BE8_0BC1(nx, ny)) {
            fd_3D57_02B8[0] = nx;
            fd_3D57_02B8[1] = ny;
            if ((fd_50F6_0F08 & 0xf) == 0 && SRand128() <= fd_50F6_01FE) {
                f_0BE8_0ABE(nx, ny, 0x81);
                f_0F3F_143C();
            }
        }
    }
}

int far f_0F3F_0D1B(int x, int y, int dirHint)
{
    int dir;
    int newRow;
    int newCol;
    int opp;
    int index;

    dir = o25_39C7_0CBD(3, x, y, fd_50F6_0200, fd_50F6_020E);
    if (dir < 0) {
        if (dir == -1)
            return 0;
        dir = SRand8();
    }
    if (y < 3 && (dir > 5 || dir < 3))
        return 0;
    if (f_0F3F_0FC9(x, y, dir) != 0) {
        opp = (dirHint ^ 0xfc) & 7;
        newCol = x + fd_3D57_0000[opp];
        newRow = y + fd_3D57_0008[opp];
        fd_3E1D_9180[newCol][newRow] = 0;
        index = f_0EC1_032C(newCol, newRow, (dirHint & 7) + 0xe8);
        if (index >= 0 && fd_3E1D_C4B5[index] != 0) {
            fd_3E1D_BED6[index] = x;
            fd_3E1D_C0CB[index] = y;
            fd_3E1D_C4B5[index] = dir - 0x18;
            fd_3E1D_9180[x][y] = dir - 0x18;
        }
        return 1;
    }
    return 0;
}

void far f_0F3F_0E30(int index)
{
    unsigned char type;
    int direction;
    int life;
    int column;

    type = fd_3E1D_C4B5[index];
    direction = type & 7;
    direction ^= 4;
    life = fd_3E1D_BED6[index] + fd_3D57_0000[direction];
    column = fd_3E1D_C0CB[index] + fd_3D57_0008[direction];
    f_0EC1_0651(life, column, type + 8, 9, 0);
}

void far f_0F3F_0E9E(int index)
{
    fd_3E1D_C4B5[index] = 0;
    fd_3E1D_9180[fd_3E1D_BED6[index]][fd_3E1D_C0CB[index]] = 0;
}

int far f_0F3F_0EE4(int x, int y, int attr)
{
    int dir;
    int newY;
    int headMarker;
    int newX;
    unsigned char cell;

    dir = attr & 7;
    newY = fd_3D57_0008[dir];
    newX = x + fd_3D57_0000[dir];
    newY += y;
    headMarker = attr - 8;
    cell = fd_3E1D_9180[newX][newY];
    if (cell == headMarker)
        return 0;
    if (f_0EC1_032C(newX, newY, headMarker) >= 0)
        return 0;
    return 1;
}

int far f_0F3F_0F55(int x, int y, int attr)
{
    int dir;
    int newY;
    int tailMarker;
    int newX;
    unsigned char cell;

    dir = (attr ^ 0xfc) & 7;
    newY = fd_3D57_0008[dir];
    newX = x + fd_3D57_0000[dir];
    newY += y;
    tailMarker = attr + 8;
    cell = fd_3E1D_9180[newX][newY];
    if (cell == tailMarker)
        return 0;
    if (f_0EC1_032C(newX, newY, tailMarker) >= 0)
        return 0;
    return 1;
}

int far f_0F3F_0FC9(int x, int y, int dir)
{
    int dx;
    int dy;

    if (dir < 0)
        return 0;
    dx = fd_3D57_0000[dir] + x;
    dy = fd_3D57_0008[dir] + y;
    if (dx > 0x3f)
        return 0;
    if (dx < 0)
        return 0;
    if (dy > 0x3f)
        return 0;
    if (dy < 1)
        return f_0F3F_1A37(x);
    if (fd_3E1D_3180[dx][dy] >= 0x1c)
        return 0;
    fd_3E1D_9180[dx][dy] = fd_3E1D_C4B5[fd_50F6_0F18] & 0xf8 | dir;
    fd_3E1D_9180[x][y] = 0;
    fd_3E1D_BED6[fd_50F6_0F18] = dx;
    fd_3E1D_C0CB[fd_50F6_0F18] = dy;
    fd_3E1D_C4B5[fd_50F6_0F18] = fd_3E1D_9180[dx][dy];
    return 1;
}

/* SCAFFOLD BEGIN: f_0F3F_10A1 (DoNestingR) best draft, 2 bytes differ (length 468 vs 470): in the
   caste==2 / SRand1(100)>HealthR else-path the original pushes caste from [bp+0Ch] for
   GetNewModeR, this draft reuses SI (caste's register region); tried nested/inverted/else-brace
   forms and all local declaration orders. */
void far f_0F3F_10A1(int x, int y, int attr, int caste)
{
    int dir;
    int ant;
    int index;

    dir = attr & 7;
    if (caste == 1) {
        if (SRand4() == 0 && fd_3E1D_3180[x][y] < 0x10) {
            fd_3E1D_C4B5[fd_50F6_0F18] += 8;
            fd_3E1D_9180[x][y] = fd_3E1D_C4B5[fd_50F6_0F18];
            f_0BE8_0ABE(x, y, 0x82);
            fd_3E1D_C6AA[fd_50F6_0F18] = 0;
            fd_3E1D_C2C0[fd_50F6_0F18] = f_1383_0A30(caste);
            return;
        }
        if (SRand4() == 0 || (dir = f_0BE8_0E0F(x, y, attr & 7)) < 0)
            dir = SRand8();
    } else if (caste == 2) {
        if (SRand4() == 0) {
            ant = fd_3E1D_9180[x][y];
            if (ant != 0 && (ant & 0x7f) < 8) {
                if ((index = f_0EC1_032C(x, y, ant)) >= 0) {
                    fd_3E1D_C4B5[index] = 0;
                    fd_3E1D_C4B5[fd_50F6_0F18] -= 8;
                    return;
                }
            } else if (SRand1(100) > fd_50F6_01FE)
                f_0F3F_1277(x, y);
            else
                fd_3E1D_C2C0[fd_50F6_0F18] = f_1383_0A30(caste);
        }
        if (SRand4() == 0)
            dir = SRand8();
        else
            dir = attr & 7;
    } else
        fd_3E1D_C2C0[fd_50F6_0F18] = f_1383_0A30(caste);
    if (f_0F3F_0FC9(x, y, dir) == 0)
        f_0F3F_0FC9(x, y, SRand8());
}
/* SCAFFOLD END */

void far f_0F3F_1277(int y, int x)
{
    int threshold;
    int level;

    level = fd_3E1D_3180[y][x];
    if (level < 0x10 || level > 0x13)
        return;
    if (level == 0x10)
        fd_3E1D_3180[y][x] = SRand8();
    else
        fd_3E1D_3180[y][x]--;
    if (fd_50F6_1060 > 0)
        fd_50F6_1060--;
    threshold = (fd_50F6_0350 + fd_50F6_0AFA[2]) >> 4;
    fd_50F6_0226 += 5;
    if (threshold < fd_50F6_0226) {
        fd_50F6_0226 = 0;
        if (fd_50F6_01FE < 100)
            fd_50F6_01FE++;
    }
}

void far f_0F3F_1330(int x, int y)
{
    if (fd_3E1D_3180[x][y] == 0x10)
        fd_3E1D_3180[x][y] = SRand8();
    else
        fd_3E1D_3180[x][y]--;
    if (fd_50F6_1060 > 0)
        fd_50F6_1060--;
    fd_50F6_0226 += 5;
    if ((fd_50F6_0350 + fd_50F6_0AFA[2]) >> 4 < fd_50F6_0226) {
        fd_50F6_0226 = 0;
        if (fd_50F6_01FE < 100)
            fd_50F6_01FE++;
    }
}

void far f_0F3F_13D7(int x, int y)
{
    if (fd_3E1D_3180[x][y] == 0x10)
        fd_3E1D_3180[x][y] = SRand8();
    else
        fd_3E1D_3180[x][y]--;
    if (fd_50F6_1060 > 0)
        fd_50F6_1060--;
}

void far f_0F3F_143C(void)
{
    --fd_50F6_0226;
    if (fd_50F6_0226 < 0) {
        fd_50F6_0226 = fd_50F6_0350 >> 5;
        if (fd_50F6_01FE > 0)
            --fd_50F6_01FE;
    }
}

void far f_0F3F_1474(int x, int y, int attr)
{
    int dir;
    int newattr;
    int nx;
    int ny;

    dir = f_0BE8_0E0F(x, y, attr & 7);
    if (dir < 0 || SRand16() == 0) {
        f_0F3F_09B0(x, y);
        if (SRand1(100) > fd_50F6_01FE)
            f_0F3F_1330(x, y);
        fd_3E1D_C2C0[fd_50F6_0F18] = f_1383_0A30((attr & 0x78) >> 3);
        return;
    }
    newattr = (attr & 0xf8) | dir;
    fd_3E1D_9180[x][y] = newattr;
    fd_3E1D_C4B5[fd_50F6_0F18] = newattr;
    nx = x + fd_3D57_0000[dir];
    ny = y + fd_3D57_0008[dir];
    if (nx > 0x3f || nx < 0 || ny > 0x3f)
        return;
    if (ny < 1) {
        f_0F3F_1A37(x);
        return;
    }
    if (fd_3E1D_3180[nx][ny] >= 0x30)
        return;
    fd_3E1D_9180[x][y] = 0;
    if (f_0F3F_08F6(nx, ny, newattr))
        return;
    newattr = (fd_3E1D_C4B5[fd_50F6_0F18] & 0xf8) | dir;
    fd_3E1D_C4B5[fd_50F6_0F18] = newattr;
    fd_3E1D_9180[nx][ny] = newattr;
    fd_3E1D_BED6[fd_50F6_0F18] = nx;
    fd_3E1D_C0CB[fd_50F6_0F18] = ny;
}

/* SCAFFOLD BEGIN: DoDigInR best draft, 3 bytes differ: the two arms of
   `(newattr & 0x7f) < 0x30 ? SRand8() + 0x90 : SRand8() + 0xb0` are laid out swapped (jl vs jge);
   the arm order flips together with the placement of the DigTileThemR()==0 `m = 0; return` block
   (then-return form places it inline, 621 bytes). Condition spellings, arm orders, goto forms and
   declaration orders do not change it. */
void far DoDigInR(int x, int y, int attr, int caste)
{
    int dir;
    int newattr;
    int nx;
    int ny;

    if (caste != 2 && caste != 6) {
        fd_3E1D_C2C0[fd_50F6_0F18] = f_1383_0A30(caste);
        return;
    }
    dir = f_0BE8_0E0F(x, y, attr & 7);
    if (dir < 0)
        dir = SRand8();
    newattr = (attr & 0xf8) | dir;
    fd_3E1D_9180[x][y] = newattr;
    fd_3E1D_C4B5[fd_50F6_0F18] = newattr;
    if (y == 0x3f) {
        fd_3E1D_C2C0[fd_50F6_0F18] = f_1383_0A30(caste);
        return;
    }
    ny = y + fd_3D57_0008[dir];
    nx = x + fd_3D57_0000[dir];
    if (nx > 0x3f || nx < 0 || ny > 0x3f)
        return;
    if (ny < 1) {
        f_0F3F_1A37(x);
        return;
    }
    if (fd_3E1D_3180[nx][ny] >= 0x30)
        return;
    if (IsItDirt(fd_3E1D_3180[nx][ny])) {
        if (DigTileThemR(nx, ny)) {
            fd_3E1D_C4B5[fd_50F6_0F18] += 0x18;
            fd_3E1D_C2C0[fd_50F6_0F18] = 5;
            f_00DF_00E8(0x12, 0, 0);
        } else {
            fd_3E1D_C2C0[fd_50F6_0F18] = 0;
            return;
        }
    }
    fd_3E1D_9180[x][y] = 0;
    if (f_0F3F_08F6(nx, ny, newattr))
        return;
    newattr = (fd_3E1D_C4B5[fd_50F6_0F18] & 0xf8) | dir;
    fd_3E1D_C4B5[fd_50F6_0F18] = newattr;
    fd_3E1D_9180[nx][ny] = newattr;
    fd_3E1D_BED6[fd_50F6_0F18] = nx;
    fd_3E1D_C0CB[fd_50F6_0F18] = ny;
    if (SRand64() > fd_50F6_01FE)
        f_0F3F_1277(x, y);
    if (SRand4() == 0)
        f_14EE_0D71(nx, ny);
    if (fd_3E1D_3180[nx][ny] == 0x14) {
        fd_3E1D_9180[nx][ny] = fd_3E1D_C4B5[fd_50F6_0F18] = 0;
        f_0EC1_05D4(nx, ny, newattr = (newattr & 0x7f) < 0x30 ? SRand8() + 0x90 : SRand8() + 0xb0, 3, 0);
        fd_3E1D_8180[nx][ny] = newattr;
    }
}
/* SCAFFOLD END */

void far f_0F3F_186B(int x, int y, int attr)
{
    int dir;
    int newattr;
    int nx;
    int ny;
    int caste;

    dir = f_0BE8_0CBB(x, y, attr & 7);
    if (dir > 0)
        dir--;
    else
        dir = f_0894_21C5(attr & 7);
    newattr = (attr & 0xf8) | dir;
    fd_3E1D_9180[x][y] = newattr;
    fd_3E1D_C4B5[fd_50F6_0F18] = newattr;
    nx = x + fd_3D57_0000[dir];
    ny = y + fd_3D57_0008[dir];
    if (nx < 0 || nx > 0x3f || ny > 0x3f)
        return;
    if (ny < 1) {
        f_0F3F_1A37(x);
        return;
    }
    if (fd_3E1D_3180[nx][ny] >= 0x30) {
        if (fd_3E1D_5180[x][y] != 0)
            fd_3E1D_5180[x][y]--;
        caste = (attr & 0x78) >> 3;
        if (caste == 5 || caste == 9) {
            fd_3E1D_C4B5[fd_50F6_0F18] -= 0x18;
            fd_3E1D_C2C0[fd_50F6_0F18] = 4;
        }
        if (caste == 2 || caste == 6)
            fd_3E1D_C2C0[fd_50F6_0F18] = 4;
        return;
    }
    if (IsItDirt(fd_3E1D_3180[nx][ny]))
        return;
    fd_3E1D_9180[x][y] = 0;
    if (f_0F3F_08F6(nx, ny, newattr))
        return;
    fd_3E1D_C4B5[fd_50F6_0F18] = fd_3E1D_9180[nx][ny] = (fd_3E1D_C4B5[fd_50F6_0F18] & 0xf8) | dir;
    fd_3E1D_BED6[fd_50F6_0F18] = nx;
    fd_3E1D_C0CB[fd_50F6_0F18] = ny;
    if (SRand64() > fd_50F6_01FE)
        f_0F3F_1277(x, y);
}

int far f_0F3F_1A37(int x)
{
    int raw;

    if (fd_3E1D_3180[x][0] == 0x18) {
        raw = fd_3E1D_C4B5[fd_50F6_0F18];
        fd_3E1D_C4B5[fd_50F6_0F18] = 0;
        if (fd_3D57_0264[x] == 0)
            f_14EE_0367(x);
        if (f_0EC1_0437(fd_3D57_0264[x], x, SRand8() + (raw & 0xf8),
                        fd_3E1D_C2C0[fd_50F6_0F18], fd_3E1D_C6AA[fd_50F6_0F18]) != 0) {
            fd_3E1D_9180[x][1] = 0;
            return 1;
        }
        fd_3E1D_C4B5[fd_50F6_0F18] = raw;
        fd_3E1D_C2C0[fd_50F6_0F18] = 0;
        return 0;
    }
    if (fd_3E1D_5180[x][0] != 0)
        fd_3E1D_5180[x][0]--;
    if (SRand2() != 0) {
        if (x > 0 && IsItDirt(fd_3E1D_3180[x - 1][1]) != 0)
            DigTileThemR(x - 1, 1);
    } else {
        if (x < 0x3f && IsItDirt(fd_3E1D_3180[x + 1][1]) != 0)
            DigTileThemR(x + 1, 1);
    }
    f_0F3F_0FC9(x, 1, SRand8());
    return 0;
}
