/* Overlay section S25, code frame 39C7: black colony nest simulation (DoAntSimB unit).
 * Built /AL /Os /Oe /Og /Zi (like the sibling S25:3BA4): under /Zd 27 cross-function
 * relocation-order constraints are violated, under /Zi none.  Line layout: the seven
 * "map = list = value" stores are written as two statements (the file's own style, e.g.
 * "BlistT[..] = ..; fd_3E1D_8180[x][y] = BlistT[..];"); byte-identical either way, but the
 * extra /Zi line entries put the fourth 52-entry flush before GetBestDir's first GetDis
 * call, as its within-group relocation order requires (FORBID (0CDC,0D54]).
 * Worker resI: QueenMoveB (0DAF) writes its y<3 test as one condition (the nested form adds
 * references to dir, REG-3, and puts dir in SI); its final store is two statements like the
 * others, and TryMoveDirB (105B) tests its three trophallaxis conditions as nested ifs.  Both
 * are byte-identical to the one-line forms; their three extra /Zi line entries put the sixth
 * flush at 12FB (DoNestingB NEED (12E3,131E], FORBID (12FE,132D]) and the ninth outside
 * GetOutB's FORBID (1CFC,1DC0]. */

extern int far ListIndexB;
extern int far fd_50F6_0F18;
extern unsigned char far BlistX[];
extern unsigned char far BlistY[];
extern unsigned char far BlistT[];
void far o25_39C7_006D(int x, int y, int attr);

void far o25_39C7_0000(void)
{
    int x;
    int y;
    int attr;

    fd_50F6_0F18 = ListIndexB;
    while (fd_50F6_0F18 > 0) {
        --fd_50F6_0F18;
        x = BlistX[fd_50F6_0F18];
        y = BlistY[fd_50F6_0F18] & 0xff;
        attr = BlistT[fd_50F6_0F18];
        if (attr != 0)
            o25_39C7_006D(x, y, attr);
    }
}

extern unsigned char far BlistM[];
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
extern int far FindInBList(int x, int y, int life);
void far o25_39C7_0F30(int index);
extern long far fd_50F6_1000;
extern int far f_0894_1E34(int a, int b);
extern unsigned char far BlistS[];
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
        t = BlistM[fd_50F6_0F18];
        fd_50F6_0D40[t]++;
        if (SRand256() == 0 && t != 9 && SRand32() > fd_50F6_10BE) {
            BlistT[fd_50F6_0F18] = 0;
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
                BlistM[fd_50F6_0F18] = 0xf;
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
        task = BlistM[fd_50F6_0F18];
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
        if (caste > 0 && caste < 0x68 && (i = FindInBList(x, y, caste)) >= 0) {
            if (caste > 0x5f)
                o25_39C7_0F30(i);
            if (caste < 8) {
                BlistM[fd_50F6_0F18] = 3;
                BlistT[fd_50F6_0F18] |= 8;
                fd_3E1D_8180[x][y] = BlistT[fd_50F6_0F18];
                BlistT[i] = 0;
                fd_50F6_1000++;
            } else {
                t = f_0894_1E34(BlistT[i], attr);
                BlistT[fd_50F6_0F18] = 0;
                BlistS[i] = t;
                BlistT[i] = (t & 0x80) + 0x70;
                fd_3E1D_8180[x][y] = BlistT[i];
                BlistM[i] = 0xa;
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
extern int far GetEnterDirB(int x, int y, int dir);
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
        BlistM[fd_50F6_0F18] = 3;
        BlistT[fd_50F6_0F18] |= 8;
        fd_3E1D_8180[x][y] = BlistT[fd_50F6_0F18];
        return;
    }
    dir = (SRand1(3) + dirHint - 2) & 7;
    if (o25_39C7_105B(x, y, dir) != 0)
        return;
    dir = GetEnterDirB(x, y, dirHint & 7);
    if (dir < 0)
        dir = SRand1(8);
    if (o25_39C7_105B(x, y, dir) != 0)
        return;
    BlistM[fd_50F6_0F18] = 1;
    fd_3E1D_8180[x][y] = BlistT[fd_50F6_0F18];
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
            fd_3E1D_8180[x][y] = BlistT[fd_50F6_0F18];
    }
}

void far o25_39C7_04E5(int x, int y, int attacker)
{
    int type;

    if (o25_39C7_0853(x, y, attacker) == 1)
        return;
    fd_3E1D_8180[x][y] = BlistT[fd_50F6_0F18];
    if (SRand1(20) == 0) {
        type = BlistT[fd_50F6_0F18];
        BlistM[fd_50F6_0F18] = f_1383_0976((type & 0x78) >> 3, type);
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
        BlistM[fd_50F6_0F18] = f_1383_099B((attr & 0x78) >> 3);
        return;
    }
    attr = ((SRand1(3) + attr - 1) & 7) | (attr & 0xf8);
    BlistT[fd_50F6_0F18] = attr;
    fd_3E1D_8180[x][y] = BlistT[fd_50F6_0F18];
    if (SRand1(100) == 0) {
        fd_3E1D_8180[x][y] = 0;
        BlistT[fd_50F6_0F18] = fd_3E1D_8180[x][y];
        if (attr & 0x80)
            fd_50F6_0FBC++;
        else
            fd_50F6_0F30++;
    }
}

void far o25_39C7_0677(int x, int y, int attr, int caste)
{
    if (SRand32() == 0)
        BlistM[fd_50F6_0F18] = f_1383_099B(caste);
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
    BlistT[fd_50F6_0F18] = (BlistT[fd_50F6_0F18] & 0xf8) + SRand1(7);
    fd_3E1D_8180[x][y] = BlistT[fd_50F6_0F18];
    if (SRand16() == 0) {
        fd_3E1D_8180[x][y] = BlistS[fd_50F6_0F18];
        BlistT[fd_50F6_0F18] = fd_3E1D_8180[x][y];
        if ((BlistT[fd_50F6_0F18] & 0x78) == 0x60)
            o25_39C7_0EC2(fd_50F6_0F18);
        if (BlistT[fd_50F6_0F18] & 0x80)
            BlistM[fd_50F6_0F18] = 7;
        else
            BlistM[fd_50F6_0F18] = f_1383_0976((BlistT[fd_50F6_0F18] & 0x78) >> 3, BlistT[fd_50F6_0F18]);
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
    if (ant > 0x87 && ant < 0xe8 && (index = FindInBList(x, y, ant)) >= 0) {
        winner = f_0894_1E34(ant, attacker);
        BlistS[index] = winner;
        BlistT[index] = (winner & 0x80) + 0x70;
        fd_3E1D_8180[x][y] = BlistT[index];
        BlistM[index] = 0xa;
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
    if (BlistT[fd_50F6_0F18] & 8)
        BlistT[fd_50F6_0F18] -= 8;
    return result;
}

extern int far BpopT;
extern int far fd_50F6_0F08;
extern int far ModeAuto;
extern int far f_0093_002B(int range);
extern unsigned int far fd_50F6_04A2;
extern int far fd_3D57_0C0E;
extern void far f_0250_428A(int x, int y, int plane);

void far o25_39C7_0980(int x, int y)
{
    int attr;
    int mode;
    int mask;

    attr = BlistT[fd_50F6_0F18];
    mode = -1;
    if (BpopT <= 2)
        mask = 0x1f;
    else
        mask = 0x7f;
    if (!(fd_50F6_0F08 & mask)) {
        attr++;
        if ((attr & 0xf) == 8) {
            if (ModeAuto != 0 || (int)(fd_50F6_04A2 >> 7) >= f_0093_002B(255)) {
                mode = fd_3D57_0C0E;
                attr = (mode << 3) + 2;
                if (mode == 2)
                    BlistM[fd_50F6_0F18] = 1;
                else
                    BlistM[fd_50F6_0F18] = f_1383_099B(mode);
            } else {
                attr = 0;
                fd_50F6_1000++;
            }
        }
    }
    if (fd_3D57_07A8[5] != 0 && mode < 0)
        f_0250_428A(x, y, 2);
    fd_3E1D_8180[x][y] = attr;
    BlistT[fd_50F6_0F18] = attr;
    BlistS[fd_50F6_0F18] = 0;
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
                BlistT[fd_50F6_0F18] = 0;
                fd_3E1D_8180[x][y] = BlistT[fd_50F6_0F18];
                o14_384C_0B6A(0, 0x271f, 1);
                return;
            }
            if (o25_39C7_0DAF(x, y, attr) != 0)
                return;
        }
        t = BlistT[fd_50F6_0F18];
        if (o25_39C7_0FE7(x, y, t) != 0) {
            t = 0;
            BlistT[fd_50F6_0F18] = 0;
            fd_50F6_035E--;
        }
        fd_3E1D_8180[x][y] = t;
        if (fd_3D57_07A8[5] != 0)
            f_0250_437A(x, y, 2);
    } else if (caste == 13) {
        t = BlistT[fd_50F6_0F18];
        fd_3E1D_8180[x][y] = t;
        if (fd_50F6_035E > 0 && o25_39C7_0F76(x, y, t) != 0) {
            fd_50F6_035E--;
            BlistT[fd_50F6_0F18] = 0;
            fd_3E1D_8180[x][y] = BlistT[fd_50F6_0F18];
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

extern long far f_0BE8_0B83(int x1, int y1, int x2, int y2);
extern int far GetMap(int plane, int x, int y);
extern int far IsNotObstacle(int plane, int x, int y);
extern int far IsThisPebble(int plane, int tile);
extern int far f_10F7_07C7(int plane, int x, int y);
extern int far f_10F7_04EC(int plane, int x, int y);
extern int far fd_50F6_10C0;
extern int far fd_50F6_10B2;

int far o25_39C7_0CBD(int plane, int x, int y, int a, int b)
{
    int fallback;
    int best;
    int threshold;
    int dir;
    int nx;
    int ny;
    int tile;
    int dis;

    best = -1;
    threshold = f_0BE8_0B83(x, y, a, b);
    if (threshold <= 0)
        goto done;
    fallback = -2;
    for (dir = 0; dir < 8; dir++) {
        nx = fd_3D57_0000[dir] + x;
        ny = fd_3D57_0008[dir] + y;
        tile = GetMap(plane, nx, ny);
        if (IsNotObstacle(plane, nx, ny) != 1)
            continue;
        if (IsThisPebble(plane, tile) != 0)
            continue;
        dis = f_0BE8_0B83(nx, ny, a, b);
        if (dis >= threshold)
            continue;
        if (f_10F7_07C7(plane, nx, ny) <= 0 && f_10F7_04EC(plane, nx, ny) == 1)
            best = dir;
        else
            fallback = dir;
        threshold = dis;
    }
    if (best < 0)
        best = fallback;
done:
    return best;
}

int far o25_39C7_0DAF(int x, int y, int dirHint)
{
    int newRow;
    int newCol;
    int opp;
    int index;
    int dir;

    dir = o25_39C7_0CBD(2, x, y, fd_50F6_10B2, fd_50F6_10C0);
    if (dir < 0) {
        if (dir == -1)
            return 0;
        dir = SRand8();
    }
    if (y < 3 && (dir > 5 || dir < 3))
        return 0;
    if (o25_39C7_105B(x, y, dir) != 0) {
        opp = (dirHint ^ 0xfc) & 7;
        newCol = x + fd_3D57_0000[opp];
        newRow = y + fd_3D57_0008[opp];
        fd_3E1D_8180[newCol][newRow] = 0;
        index = FindInBList(newCol, newRow, (dirHint & 7) + 0x68);
        if (index >= 0 && BlistT[index] != 0) {
            BlistX[index] = x;
            BlistY[index] = y;
            BlistT[index] = dir + 0x68;
            fd_3E1D_8180[x][y] = BlistT[index];
        }
        return 1;
    }
    return 0;
}

extern void far f_0EC1_05D4(int x, int y, int type, int mode, int flag);

void far o25_39C7_0EC2(int index)
{
    unsigned char type;
    int direction;
    int life;
    int column;

    type = BlistT[index];
    direction = type & 7;
    direction ^= 4;
    life = BlistX[index] + fd_3D57_0000[direction];
    column = BlistY[index] + fd_3D57_0008[direction];
    f_0EC1_05D4(life, column, type + 8, 9, 0);
}

void far o25_39C7_0F30(int index)
{
    fd_3E1D_8180[BlistX[index]][BlistY[index]] = BlistT[index] = 0;
}

int far o25_39C7_0F76(int x, int y, int attr)
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
    cell = fd_3E1D_8180[newX][newY];
    if (cell == headMarker)
        return 0;
    if (FindInBList(newX, newY, headMarker) >= 0)
        return 0;
    return 1;
}

int far o25_39C7_0FE7(int x, int y, int attr)
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
    cell = fd_3E1D_8180[newX][newY];
    if (cell == tailMarker)
        return 0;
    if (FindInBList(newX, newY, tailMarker) >= 0)
        return 0;
    return 1;
}

int far o25_39C7_1C81(int x);
extern int far fd_50F6_1044;
extern void far o22_39C7_19E5(int x, int y, int dir);

int far o25_39C7_105B(int x, int y, int dir)
{
    int dy;
    int dx;

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
        return o25_39C7_1C81(x);
    if (fd_3E1D_2180[dx][dy] >= 0x1c)
        return 0;
    if (fd_3E1D_8180[dx][dy] == 0xff)
        if (fd_50F6_1044)
            if (BlistX[fd_50F6_0F18] < 0x80) {
                fd_3E1D_8180[x][y] = BlistT[fd_50F6_0F18] & 0xf8 | (unsigned char)dir;
                o22_39C7_19E5(x, y, dir);
            }
    fd_3E1D_8180[dx][dy] = BlistT[fd_50F6_0F18] & 0xf8 | (unsigned char)dir;
    fd_3E1D_8180[x][y] = 0;
    BlistX[fd_50F6_0F18] = (unsigned char)dx;
    BlistY[fd_50F6_0F18] = (unsigned char)dy;
    BlistT[fd_50F6_0F18] = fd_3E1D_8180[dx][dy];
    return 1;
}

void far o25_39C7_13EF(int x, int y);

/* SCAFFOLD BEGIN: DoNestingB best draft: 1 byte differs, mov si,cx (original) vs mov si,bx when loading the Tindex copy before f_1383_099B (register tie-break); record order is right with this layout */
void far DoNestingB(int x, int y, int attr, int caste)
{
    int dir;
    unsigned char food;
    int load;
    unsigned char cell;
    int index;

    dir = attr & 7;
    load = BlistS[fd_50F6_0F18] & 7;
    cell = fd_3E1D_8180[x][y];
    food = BlistS[fd_50F6_0F18] >> 3;
    switch (caste) {
    case 1:
        if (food == 0) {
            if ((dir = GetEnterDirB(x, y, attr & 7)) < 0)
                BlistS[fd_50F6_0F18] = load | 8;
            break;
        }
        if (cell == 0 || cell > 8) {
            BlistT[fd_50F6_0F18] += 8;
            f_0BE8_0A5B(x, y, load);
            fd_3E1D_8180[x][y] = BlistT[fd_50F6_0F18];
            BlistS[fd_50F6_0F18] = 8;
            BlistM[fd_50F6_0F18] = f_1383_099B(caste);
        }
        if ((dir = f_0BE8_0C0F(x, y, attr & 7)) != 0)
            dir--;
        else
            dir = SRand8();
        break;
    case 2:
        if (food != 0) {
            if (SRand8() == 0)
                BlistS[fd_50F6_0F18] = 0;
            if ((dir = f_0BE8_0C0F(x, y, attr & 7)) != 0)
                dir--;
            else
                dir = SRand8();
            break;
        }
        if (cell != 0 && cell < 8) {
            if ((index = FindInBList(x, y, cell)) >= 0) {
                BlistT[index] = 0;
                BlistT[fd_50F6_0F18] -= 8;
                BlistS[fd_50F6_0F18] = cell;
                return;
            }
        } else if (SRand1(100) > fd_50F6_10BE)
            o25_39C7_13EF(x, y);
        else if (SRand16() == 0)
            BlistM[fd_50F6_0F18] = f_1383_099B(caste);
        dir = attr & 7;
        break;
    default:
        if (SRand1(100) > fd_50F6_10BE)
            o25_39C7_13EF(x, y);
        if (SRand8() == 0)
            BlistM[fd_50F6_0F18] = f_1383_099B(caste);
        break;
    }
    if (o25_39C7_105B(x, y, dir) == 0)
        o25_39C7_105B(x, y, SRand8());
}
/* SCAFFOLD END */

extern int far fd_50F6_0AEC[6];
extern int far fd_50F6_0212;
extern int far fd_3D57_0C18;

void far o25_39C7_13EF(int x, int y)
{
    int threshold;
    int level;

    level = fd_3E1D_2180[x][y];
    if (level < 0x10 || level > 0x13)
        return;
    if (level == 0x10)
        fd_3E1D_2180[x][y] = SRand8();
    else
        fd_3E1D_2180[x][y]--;
    if (fd_50F6_1050 > 0)
        fd_50F6_1050--;
    threshold = (BpopT + fd_50F6_0AEC[2]) >> 4;
    fd_50F6_0212 += 5;
    if (threshold < fd_50F6_0212) {
        fd_50F6_0212 = 0;
        if (fd_50F6_10BE < 100)
            fd_50F6_10BE++;
    }
}

void far o25_39C7_14A8(int x, int y)
{
    if (fd_3E1D_2180[x][y] == 0x10)
        fd_3E1D_2180[x][y] = SRand8();
    else
        fd_3E1D_2180[x][y]--;
    if (fd_50F6_1050 > 0)
        fd_50F6_1050--;
    fd_50F6_0212 += 5;
    if ((BpopT + fd_50F6_0AEC[2]) >> 4 < fd_50F6_0212) {
        fd_50F6_0212 = 0;
        if (fd_50F6_10BE < 100)
            fd_50F6_10BE++;
    }
}

void far o25_39C7_154F(int x, int y)
{
    if (fd_3E1D_2180[x][y] == 0x10)
        fd_3E1D_2180[x][y] = SRand8();
    else
        fd_3E1D_2180[x][y]--;
    if (fd_50F6_1050 > 0)
        fd_50F6_1050--;
}

void far o25_39C7_15B4(void)
{
    --fd_50F6_0212;
    if (fd_50F6_0212 < 0) {
        fd_50F6_0212 = BpopT >> 5;
        if (fd_50F6_10BE > 0 && !fd_3D57_0C18)
            --fd_50F6_10BE;
    }
}


void far DoFoodInB(int x, int y, int attr)
{
    int nx;
    int dir;
    int newattr;
    int ny;

    if ((dir = GetEnterDirB(x, y, attr & 7)) >= 0 && SRand16() != 0) {
        newattr = (attr & 0xf8) | dir;
        BlistT[fd_50F6_0F18] = fd_3E1D_8180[x][y] = newattr;
        nx = fd_3D57_0000[dir] + x;
        ny = fd_3D57_0008[dir] + y;
        if (nx > 0x3f || nx < 0 || ny > 0x3f)
            return;
        if (ny < 1) {
            o25_39C7_1C81(x);
            return;
        }
        if (fd_3E1D_2180[nx][ny] >= 0x30)
            return;
        fd_3E1D_8180[x][y] = 0;
        if ((fd_3E1D_8180[nx][ny] & 0x80)
            && (!f_10F7_003A(fd_3E1D_8180[nx][ny]) || fd_50F6_04E2 != 0)
            && o25_39C7_0853(nx, ny, newattr))
            return;
        newattr = (BlistT[fd_50F6_0F18] & 0xf8) | dir;
        BlistT[fd_50F6_0F18] = newattr;
        fd_3E1D_8180[nx][ny] = newattr;
        BlistX[fd_50F6_0F18] = nx;
        BlistY[fd_50F6_0F18] = ny;
        return;
    }
    o25_39C7_090A(x, y);
    if (SRand1(100) > fd_50F6_10BE)
        o25_39C7_14A8(x, y);
    BlistM[fd_50F6_0F18] = f_1383_099B((attr & 0x78) >> 3);
}

extern int far IsItDirt(int value);
extern int far DigTileThemB(int x, int y);
extern void far f_00DF_00E8(int sound, int a, int b);
extern void far f_14EE_0C9C(int x, int y);
extern int far SRand4(void);

/* SCAFFOLD BEGIN: DoDigInB best draft: the original keeps the GetEnterDirB result in DI and copies it to [bp-4] after the y==0x3f test (mov [bp-4],di; mov cx,di); MSC keeps dir in memory here */
void far DoDigInB(int x, int y, int attr, int caste)
{
    int dir;
    int newattr;
    int nx;
    int ny;
    int tile;

    if (caste != 2 && caste != 6) {
        BlistM[fd_50F6_0F18] = f_1383_099B(caste);
        return;
    }
    if ((dir = GetEnterDirB(x, y, attr & 7)) < 0)
        dir = SRand8();
    newattr = (attr & 0xf8) | dir;
    BlistT[fd_50F6_0F18] = fd_3E1D_8180[x][y] = newattr;
    if (y == 0x3f) {
        BlistM[fd_50F6_0F18] = f_1383_099B(caste);
        return;
    }
    nx = fd_3D57_0000[dir] + x;
    ny = fd_3D57_0008[dir] + y;
    if (nx > 0x3f || nx < 0 || ny > 0x3f)
        return;
    if (ny < 1) {
        o25_39C7_1C81(x);
        return;
    }
    tile = fd_3E1D_2180[nx][ny];
    if (tile >= 0x30)
        return;
    if (IsItDirt(tile)) {
        if (!DigTileThemB(nx, ny)) {
            BlistM[fd_50F6_0F18] = f_1383_099B(caste);
            return;
        }
        BlistT[fd_50F6_0F18] += 0x18;
        BlistM[fd_50F6_0F18] = 5;
        f_00DF_00E8(0x11, 0, 0);
    }
    fd_3E1D_8180[x][y] = 0;
    if ((fd_3E1D_8180[nx][ny] & 0x80)
        && (!f_10F7_003A(fd_3E1D_8180[nx][ny]) || fd_50F6_04E2 != 0)
        && o25_39C7_0853(nx, ny, newattr))
        return;
    newattr = (BlistT[fd_50F6_0F18] & 0xf8) | dir;
    BlistT[fd_50F6_0F18] = newattr;
    fd_3E1D_8180[nx][ny] = newattr;
    BlistX[fd_50F6_0F18] = nx;
    BlistY[fd_50F6_0F18] = ny;
    if (SRand64() > fd_50F6_10BE)
        o25_39C7_13EF(nx, ny);
    if (SRand4() == 0)
        f_14EE_0C9C(nx, ny);
}
/* SCAFFOLD END */

extern int far f_0894_21C5(int dir);
extern unsigned char far fd_3E1D_4180[64][64];

void far DoDigOutB(int x, int y, int attr)
{
    int ny;
    int nx;
    int newattr;
    int dir;
    int caste;

    if ((dir = f_0BE8_0C0F(x, y, attr & 7)) > 0)
        dir--;
    else
        dir = f_0894_21C5(attr & 7);
    newattr = (attr & 0xf8) | dir;
    BlistT[fd_50F6_0F18] = fd_3E1D_8180[x][y] = newattr;
    nx = fd_3D57_0000[dir] + x;
    ny = fd_3D57_0008[dir] + y;
    if (nx < 0 || nx > 0x3f || ny > 0x3f)
        return;
    if (ny < 1) {
        o25_39C7_1C81(x);
        return;
    }
    if (fd_3E1D_2180[nx][ny] >= 0x30) {
        fd_3E1D_4180[x][y]--;
        caste = (attr & 0x78) >> 3;
        if (caste == 5 || caste == 9) {
            BlistT[fd_50F6_0F18] -= 0x18;
            BlistM[fd_50F6_0F18] = 4;
        }
        if (caste == 2 || caste == 6)
            BlistM[fd_50F6_0F18] = 4;
        return;
    }
    if (IsItDirt(fd_3E1D_2180[nx][ny]))
        return;
    fd_3E1D_8180[x][y] = 0;
    if ((fd_3E1D_8180[nx][ny] & 0x80)
        && (!f_10F7_003A(fd_3E1D_8180[nx][ny]) || fd_50F6_04E2 != 0)
        && o25_39C7_0853(nx, ny, newattr))
        return;
    BlistT[fd_50F6_0F18] = fd_3E1D_8180[nx][ny] = (BlistT[fd_50F6_0F18] & 0xf8) | dir;
    BlistX[fd_50F6_0F18] = nx;
    BlistY[fd_50F6_0F18] = ny;
    if (SRand64() > fd_50F6_10BE)
        o25_39C7_13EF(nx, ny);
}

extern unsigned char far fd_3D57_0224[];
extern void far MakeNewHoleB(int x);
extern int far ExitHole(int hole, int x, int dir, int mode, int state);
extern int far SRand2(void);

int far o25_39C7_1BBB(int x, int y)
{
    int dir;

    dir = BlistT[fd_50F6_0F18];
    BlistT[fd_50F6_0F18] = 0;
    if (fd_3D57_0224[x] == 0)
        MakeNewHoleB(x);
    if (ExitHole(fd_3D57_0224[x], x, SRand8() + (dir & 0xf8),
                    BlistM[fd_50F6_0F18], BlistS[fd_50F6_0F18])) {
        fd_3E1D_8180[x][y] = 0;
        return 1;
    }
    BlistT[fd_50F6_0F18] = dir;
    BlistM[fd_50F6_0F18] = 0;
    return 0;
}


int far o25_39C7_1C81(int x)
{
    int raw;

    if (fd_3E1D_2180[x][0] == 0x18) {
        raw = BlistT[fd_50F6_0F18];
        BlistT[fd_50F6_0F18] = 0;
        if (fd_3D57_0224[x] == 0)
            MakeNewHoleB(x);
        if (ExitHole(fd_3D57_0224[x], x, SRand8() + (raw & 0xf8),
                        BlistM[fd_50F6_0F18], BlistS[fd_50F6_0F18]) != 0) {
            fd_3E1D_8180[x][1] = 0;
            return 1;
        }
        BlistT[fd_50F6_0F18] = raw;
        BlistM[fd_50F6_0F18] = 0;
        return 0;
    }
    if (fd_3E1D_4180[x][0] != 0)
        fd_3E1D_4180[x][0]--;
    if (SRand2() != 0) {
        if (x > 0 && IsItDirt(fd_3E1D_2180[x - 1][1]) != 0)
            DigTileThemB(x - 1, 1);
    } else {
        if (x < 0x3f && IsItDirt(fd_3E1D_2180[x + 1][1]) != 0)
            DigTileThemB(x + 1, 1);
    }
    o25_39C7_105B(x, 1, SRand8());
    return 0;
}


