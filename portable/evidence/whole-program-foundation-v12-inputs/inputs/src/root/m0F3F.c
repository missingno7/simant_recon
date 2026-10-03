/* Root module, code frame 0F3F: red colony nest ants (DoAntSimR, R-list ants).
 * MSC 6.00AX /AL /Os /Oe /Og /Zi. */

extern int far Tindex;
extern int far ListIndexR;
extern unsigned char far RlistX[];
extern unsigned char far RlistY[];
extern unsigned char far RlistT[];
extern unsigned char far RlistM[];
extern int far fd_50F6_0D72[20];
extern int far SRand256(void);
extern int far SRand32(void);
extern int far HealthR;
extern unsigned char far LifeR[64][64];
extern long far fd_50F6_0FBC;
extern int far fd_50F6_08E8;
extern int far fd_50F6_0D40[20];
extern int far f_0EC1_032C(int x, int y, int ant);
extern int far GetWinner(int a, int b);
extern unsigned char far RlistS[];
extern int far MePlane;
extern unsigned char far MapR[64][64];
extern int far SRand1(int range);
extern int far GetEnterDirR(int x, int y, int dir);
extern int far GetExitDirR(int x, int y, int dir);
extern int far SRand8(void);
extern int far f_1383_0976(int caste, int type);
extern int far fd_3D57_07B2;
extern void far f_0250_43F2(int x, int y, int plane);
extern int far f_1383_0A30(int mode);
extern long far fd_50F6_0F30;
extern int far SRand16(void);
extern void far f_0250_4302(int x, int y, int plane);
extern int far IsYellowAnt(int value);
extern int far fd_50F6_04E2;
extern void far o25_3BA4_0DFB(int a, int index);
extern int far FoodR;
extern int far RpopT;
extern int far Cycle;
extern signed char far fd_3D57_0B36[];
extern int far fd_50F6_10A6;
extern void far f_0250_428A(int x, int y, int plane);
extern int far SRand64(void);
extern void far o14_384C_0B6A(int a, int b, int c);
extern int far fd_50F6_036C;
extern void far f_0250_437A(int x, int y, int plane);
extern signed char far Dx8[8];
extern signed char far Dy8[8];
extern int far InNestBounds(int x, int y);
extern int far fd_3D57_02B8[2];
extern int far SRand128(void);
extern void far PlaceEggR(int x, int y, int life);
extern int far o25_39C7_0CBD(int kind, int x, int y, int tx, int ty);
extern int far fd_50F6_0200;
extern int far fd_50F6_020E;
extern void far AddAntToRList(int x, int y, int type, int mode, int state);
extern int far SRand4(void);
extern int far fd_50F6_0AFA[6];
extern int far fd_50F6_0226;
extern int far IsItDirt(int value);
extern int far DigTileThemR(int x, int y);
extern void far myBeginSound(int a, int b, int c);
extern void far f_14EE_0D71(int x, int y);
extern void far AddAntToBList(int x, int y, int type, int mode, int state);
extern unsigned char far LifeB[64][64];
extern int far RandTurn(int dir);
extern unsigned char far ExitMapR[64][64];
extern unsigned char far HoleMapR[];
extern void far MakeNewHoleR(int x);
extern int far f_0EC1_0437(int hole, int x, int type, int mode, int state);
extern int far SRand2(void);



void far DoNestAntR(int x, int y, int attr);
void far RaidInR(int x, int y, int dirHint);
void far StayInR(int x, int y, int dirHint);
void far RaidOutR(int x, int y, int attr);
void far DoRestR(int x, int y, int attacker);
void far DoDrownR(int x, int y, int attr);
void far DoRandR(int x, int y, int attr, int modeArg);
void far DoNestFightR(int x, int y);
int far CheckNestFightR(int x, int y, int attacker);
void far SimEggR(int x, int y);
void far SimQueenR(int x, int y, int caste, int attr);
void far MakeNewTailR(int index);
void far KillTailR(int index);
int far TryMoveDirR(int x, int y, int dir);
void far DoNestingR(int x, int y, int attr, int caste);
void far StealFoodR(int x, int y);
int far QueenMoveR(int x, int y, int dirHint);
int far LostHeadR(int x, int y, int attr);
int far LostTailR(int x, int y, int attr);
void far TryEatFoodR(int y, int x);
void far EatFoodR(int x, int y);
void far DecEatR(void);
int far DropFoodR(int x, int y);
int far GetOutR(int x);
void far DoFoodInR(int x, int y, int attr);
void far DoDigInR(int x, int y, int attr, int caste);
void far DoDigOutR(int x, int y, int attr);

void far DoAntSimR(void)
{
    int x;
    int y;
    int attr;

    Tindex = ListIndexR;
    while (Tindex > 0) {
        --Tindex;
        x = RlistX[Tindex];
        y = RlistY[Tindex];
        attr = RlistT[Tindex];
        if (attr != 0)
            DoNestAntR(x, y, attr);
    }
}

/* Locals follow the accepted black twin S25 o25_39C7_006D (caste reused for the cell value, t for
   the mode and the fight winner).  The grouping of the DoDigOutR case labels is only partly
   decided by the bytes: 5/6/7 and 11/12 merged with 15 and 16 separate is one of several forms
   that give `mov bx,si` for the mode index; the fully merged 15/16 form gives `mov bx,ax`
   (worker resG, work/resG/v8.py: 108 of 406 groupings are exact). */
void far DoNestAntR(int x, int y, int attr)
{
    int caste;
    int task;
    int i;
    int t;

    caste = (attr & 0x78) >> 3;
    if (attr & 0x80) {
        t = RlistM[Tindex];
        fd_50F6_0D72[t]++;
        if (SRand256() == 0 && t != 9 && SRand32() > HealthR) {
            RlistT[Tindex] = 0;
            LifeR[x][y] = 0;
            fd_50F6_0FBC++;
            return;
        }
        switch (t) {
        case 0:
            DoRandR(x, y, attr, caste);
            break;
        case 1:
            DoNestingR(x, y, attr, caste);
            break;
        case 2:
            DoDigOutR(x, y, attr);
            break;
        case 3:
            DoFoodInR(x, y, attr);
            break;
        case 4:
            DoDigInR(x, y, attr, caste);
            break;
        case 5:
        case 6:
        case 7:
            DoDigOutR(x, y, attr);
            break;
        case 8:
            SimEggR(x, y);
            break;
        case 9:
            SimQueenR(x, y, caste, attr);
            break;
        case 10:
            DoNestFightR(x, y);
            break;
        case 11:
        case 12:
            DoDigOutR(x, y, attr);
            break;
        case 13:
            DoRestR(x, y, attr);
            break;
        case 14:
            DoRandR(x, y, attr, caste);
            if (fd_50F6_08E8 > 100)
                RlistM[Tindex] = 0xf;
            break;
        case 15:
            DoDigOutR(x, y, attr);
            break;
        case 16:
            DoDigOutR(x, y, attr);
            break;
        case 17:
            DoDrownR(x, y, attr);
            break;
        default:
            DoRandR(x, y, attr, caste);
            break;
        }
    } else {
        task = RlistM[Tindex];
        fd_50F6_0D40[task]++;
        if (attr < 8) {
            RlistT[Tindex] = 0;
            LifeR[RlistX[Tindex]][RlistY[Tindex]] = 0;
            return;
        }
        if (attr > 0x6f) {
            DoNestFightR(x, y);
            return;
        }
        caste = LifeR[x][y];
        if (caste > 0x80 && caste < 0xe8 && (i = f_0EC1_032C(x, y, caste)) >= 0) {
            if (caste > 0xdf)
                KillTailR(i);
            if (caste < 0x88) {
                RlistM[Tindex] = 3;
                RlistT[Tindex] |= 8;
                LifeR[x][y] = RlistT[Tindex];
                RlistT[i] = 0;
            } else {
                t = GetWinner(RlistT[i], attr);
                RlistT[Tindex] = 0;
                RlistS[i] = t;
                LifeR[x][y] = RlistT[i] = (t & 0x80) + 0x70;
                RlistM[i] = 0xa;
            }
            return;
        }
        switch (task) {
        case 6:
            if (MePlane == 3)
                StayInR(x, y, attr);
            else
                RaidOutR(x, y, attr);
            break;
        case 7:
            RaidInR(x, y, attr);
            break;
        default:
            RaidOutR(x, y, attr);
            break;
        }
    }
}

void far RaidInR(int x, int y, int dirHint)
{
    int dir;

    if (MapR[x][y] >= 0x10 && MapR[x][y] <= 0x13) {
        StealFoodR(x, y);
        RlistM[Tindex] = 3;
        RlistT[Tindex] |= 8;
        LifeR[x][y] = RlistT[Tindex];
        return;
    }
    if (TryMoveDirR(x, y, (SRand1(3) + dirHint - 2) & 7))
        return;
    dir = GetEnterDirR(x, y, dirHint & 7);
    if (dir < 0)
        dir = SRand1(8);
    if (TryMoveDirR(x, y, dir))
        return;
    RlistM[Tindex] = 1;
    LifeR[x][y] = RlistT[Tindex];
}

void far StayInR(int x, int y, int dirHint)
{
    int dir;

    if (MapR[x][y] >= 0x10 && MapR[x][y] <= 0x13) {
        StealFoodR(x, y);
        RlistM[Tindex] = 3;
        RlistT[Tindex] |= 8;
        LifeR[x][y] = RlistT[Tindex];
        return;
    }
    dir = (SRand1(3) + dirHint - 2) & 7;
    RlistT[Tindex] = (RlistT[Tindex] & 0xf8) | dir;
    if (TryMoveDirR(x, y, dir))
        return;
    dir = GetEnterDirR(x, y, dirHint & 7);
    if (dir < 0)
        dir = SRand1(8);
    if (TryMoveDirR(x, y, dir))
        return;
    LifeR[x][y] = RlistT[Tindex];
}

void far RaidOutR(int x, int y, int attr)
{
    int dir;

    dir = GetExitDirR(x, y, 8);
    if (dir == 0)
        dir = SRand8();
    else
        dir--;
    if (TryMoveDirR(x, y, dir) == 0) {
        if (TryMoveDirR(x, y, SRand8()) == 0)
            LifeR[x][y] = RlistT[Tindex];
    }
}

void far DoRestR(int x, int y, int attacker)
{
    int type;

    if (CheckNestFightR(x, y, attacker))
        return;
    LifeR[x][y] = RlistT[Tindex];
    if (SRand1(20) == 0) {
        type = RlistT[Tindex];
        RlistM[Tindex] = f_1383_0976((type & 0x78) >> 3, type);
        return;
    }
    if (fd_3D57_07B2 != 0)
        f_0250_43F2(x, y, 3);
}

void far DoDrownR(int x, int y, int attr)
{
    if (MapR[x][y] < 0x14) {
        RlistM[Tindex] = f_1383_0A30((attr & 0x78) >> 3);
        return;
    }
    attr = ((SRand1(3) + attr - 1) & 7) | (attr & 0xf8);
    RlistT[Tindex] = attr;
    LifeR[x][y] = attr;
    if (SRand1(100) == 0) {
        RlistT[Tindex] = LifeR[x][y] = 0;
        if (attr & 0x80)
            fd_50F6_0FBC++;
        else
            fd_50F6_0F30++;
    }
}

void far DoRandR(int x, int y, int attr, int modeArg)
{
    if (SRand32() == 0)
        RlistM[Tindex] = f_1383_0A30(modeArg);
    if (CheckNestFightR(x, y, attr))
        return;
    if (TryMoveDirR(x, y, attr & 7))
        return;
    TryMoveDirR(x, y, SRand8());
}

static unsigned char near nestFightMode[16] = {
    1, 1, 1, 3, 0, 5, 2, 3, 0, 5, 0, 0, 9, 9, 10, 0
};

void far DoNestFightR(int x, int y)
{
    RlistT[Tindex] = (RlistT[Tindex] & 0xf8) + SRand1(7);
    LifeR[x][y] = RlistT[Tindex];
    if (SRand16() == 0) {
        RlistT[Tindex] = LifeR[x][y] = RlistS[Tindex];
        if ((RlistT[Tindex] & 0x78) == 0x60)
            MakeNewTailR(Tindex);
        if (!(RlistT[Tindex] & 0x80))
            RlistM[Tindex] = 7;
        else
            RlistM[Tindex] = nestFightMode[(RlistT[Tindex] & 0x78) >> 3];
    } else if (fd_3D57_07B2 != 0)
        f_0250_4302(x, y, 3);
}

int far CheckNestFightR(int x, int y, int attacker)
{
    int ant;
    int index;
    int winner;

    ant = LifeR[x][y];
    if (ant > 7 && ant < 0x68) {
        index = f_0EC1_032C(x, y, ant);
        if (index >= 0) {
            winner = GetWinner(ant, attacker);
            RlistS[index] = winner;
            RlistT[index] = (winner & 0x80) + 0x70;
            LifeR[x][y] = (winner & 0x80) + 0x70;
            RlistM[index] = 0xa;
            return 1;
        }
    } else if (IsYellowAnt(ant) && fd_50F6_04E2 == 0) {
        o25_3BA4_0DFB(3, Tindex);
        return 1;
    }
    return 0;
}

int far DropFoodR(int x, int y)
{
    int level;
    int result;

    result = 0;
    level = MapR[x][y];
    if (level < 16) {
        MapR[x][y] = 16;
        result = 1;
    } else if (level < 19) {
        MapR[x][y]++;
        result = 1;
    }
    ++FoodR;
    if (RlistT[Tindex] & 8)
        RlistT[Tindex] -= 8;
    return result;
}

void far SimEggR(int x, int y)
{
    int attr;
    int mode;
    int mask;

    attr = RlistT[Tindex];
    mode = -1;
    if (RpopT == 1)
        mask = 0x1f;
    else
        mask = 0x7f;
    if (!(Cycle & mask)) {
        attr++;
        if ((attr & 0xf) == 8) {
            mode = fd_3D57_0B36[((fd_50F6_10A6 % 7) << 3) + SRand8()];
            attr = (mode << 3) + 0x82;
            RlistM[Tindex] = f_1383_0A30(mode);
        }
    }
    if (fd_3D57_07B2 != 0 && mode < 0)
        f_0250_428A(x, y, 3);
    LifeR[x][y] = attr;
    RlistT[Tindex] = attr;
    RlistS[Tindex] = 0;
}

void far SimQueenR(int x, int y, int caste, int attr)
{
    int type;
    int nx;
    int ny;

    if (caste == 12) {
        if (SRand64() == 0) {
            if (HealthR == 0) {
                LifeR[x][y] = RlistT[Tindex] = 0;
                o14_384C_0B6A(0, 0x2720, 1);
                return;
            }
            if (QueenMoveR(x, y, attr))
                return;
        }
        type = RlistT[Tindex];
        if (LostTailR(x, y, type)) {
            type = 0;
            RlistT[Tindex] = 0;
            fd_50F6_036C--;
        }
        LifeR[x][y] = type;
        if (fd_3D57_07B2 != 0)
            f_0250_437A(x, y, 3);
    } else if (caste == 13) {
        type = RlistT[Tindex];
        LifeR[x][y] = type;
        if (fd_50F6_036C > 0 && LostHeadR(x, y, type)) {
            fd_50F6_036C--;
            LifeR[x][y] = RlistT[Tindex] = 0;
            return;
        }
        nx = x + Dx8[(attr ^ 0xfc) & 7];
        ny = y + Dy8[(attr ^ 0xfc) & 7];
        if (InNestBounds(nx, ny)) {
            fd_3D57_02B8[0] = nx;
            fd_3D57_02B8[1] = ny;
            if ((Cycle & 0xf) == 0 && SRand128() <= HealthR) {
                PlaceEggR(nx, ny, 0x81);
                DecEatR();
            }
        }
    }
}

int far QueenMoveR(int x, int y, int dirHint)
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
    if (TryMoveDirR(x, y, dir) != 0) {
        opp = (dirHint ^ 0xfc) & 7;
        newCol = x + Dx8[opp];
        newRow = y + Dy8[opp];
        LifeR[newCol][newRow] = 0;
        index = f_0EC1_032C(newCol, newRow, (dirHint & 7) + 0xe8);
        if (index >= 0 && RlistT[index] != 0) {
            RlistX[index] = x;
            RlistY[index] = y;
            RlistT[index] = dir - 0x18;
            LifeR[x][y] = dir - 0x18;
        }
        return 1;
    }
    return 0;
}

void far MakeNewTailR(int index)
{
    unsigned char type;
    int direction;
    int life;
    int column;

    type = RlistT[index];
    direction = type & 7;
    direction ^= 4;
    life = RlistX[index] + Dx8[direction];
    column = RlistY[index] + Dy8[direction];
    AddAntToRList(life, column, type + 8, 9, 0);
}

void far KillTailR(int index)
{
    RlistT[index] = 0;
    LifeR[RlistX[index]][RlistY[index]] = 0;
}

int far LostHeadR(int x, int y, int attr)
{
    int dir;
    int newY;
    int headMarker;
    int newX;
    unsigned char cell;

    dir = attr & 7;
    newY = Dy8[dir];
    newX = x + Dx8[dir];
    newY += y;
    headMarker = attr - 8;
    cell = LifeR[newX][newY];
    if (cell == headMarker)
        return 0;
    if (f_0EC1_032C(newX, newY, headMarker) >= 0)
        return 0;
    return 1;
}

int far LostTailR(int x, int y, int attr)
{
    int dir;
    int newY;
    int tailMarker;
    int newX;
    unsigned char cell;

    dir = (attr ^ 0xfc) & 7;
    newY = Dy8[dir];
    newX = x + Dx8[dir];
    newY += y;
    tailMarker = attr + 8;
    cell = LifeR[newX][newY];
    if (cell == tailMarker)
        return 0;
    if (f_0EC1_032C(newX, newY, tailMarker) >= 0)
        return 0;
    return 1;
}

int far TryMoveDirR(int x, int y, int dir)
{
    int dx;
    int dy;

    if (dir < 0)
        return 0;
    dx = Dx8[dir] + x;
    dy = Dy8[dir] + y;
    if (dx > 0x3f)
        return 0;
    if (dx < 0)
        return 0;
    if (dy > 0x3f)
        return 0;
    if (dy < 1)
        return GetOutR(x);
    if (MapR[dx][dy] >= 0x1c)
        return 0;
    LifeR[dx][dy] = RlistT[Tindex] & 0xf8 | dir;
    LifeR[x][y] = 0;
    RlistX[Tindex] = dx;
    RlistY[Tindex] = dy;
    RlistT[Tindex] = LifeR[dx][dy];
    return 1;
}

void far DoNestingR(int x, int y, int attr, int caste)
{
    int dir;
    int ant;
    int index;

    dir = attr & 7;
    if (caste == 1) {
        if (SRand4() == 0 && MapR[x][y] < 0x10) {
            RlistT[Tindex] += 8;
            LifeR[x][y] = RlistT[Tindex];
            PlaceEggR(x, y, 0x82);
            RlistS[Tindex] = 0;
            RlistM[Tindex] = f_1383_0A30(caste);
            return;
        }
        if (SRand4() == 0 || (dir = GetEnterDirR(x, y, attr & 7)) < 0)
            dir = SRand8();
    } else if (caste == 2) {
        if (SRand4() == 0) {
            ant = LifeR[x][y];
            if (ant != 0 && (ant & 0x7f) < 8) {
                if ((index = f_0EC1_032C(x, y, ant)) >= 0) {
                    RlistT[index] = 0;
                    RlistT[Tindex] -= 8;
                    return;
                }
            } else if (SRand1(100) > HealthR)
                TryEatFoodR(x, y);
            else
                RlistM[Tindex] = f_1383_0A30(caste);
        }
        if (SRand4() != 0)
            dir = attr & 7;
        else
            dir = SRand8();
    } else
        RlistM[Tindex] = f_1383_0A30(caste);
    if (TryMoveDirR(x, y, dir) == 0)
        TryMoveDirR(x, y, SRand8());
}

void far TryEatFoodR(int y, int x)
{
    int threshold;
    int level;

    level = MapR[y][x];
    if (level < 0x10 || level > 0x13)
        return;
    if (level == 0x10)
        MapR[y][x] = SRand8();
    else
        MapR[y][x]--;
    if (FoodR > 0)
        FoodR--;
    threshold = (RpopT + fd_50F6_0AFA[2]) >> 4;
    fd_50F6_0226 += 5;
    if (threshold < fd_50F6_0226) {
        fd_50F6_0226 = 0;
        if (HealthR < 100)
            HealthR++;
    }
}

void far EatFoodR(int x, int y)
{
    if (MapR[x][y] == 0x10)
        MapR[x][y] = SRand8();
    else
        MapR[x][y]--;
    if (FoodR > 0)
        FoodR--;
    fd_50F6_0226 += 5;
    if ((RpopT + fd_50F6_0AFA[2]) >> 4 < fd_50F6_0226) {
        fd_50F6_0226 = 0;
        if (HealthR < 100)
            HealthR++;
    }
}

void far StealFoodR(int x, int y)
{
    if (MapR[x][y] == 0x10)
        MapR[x][y] = SRand8();
    else
        MapR[x][y]--;
    if (FoodR > 0)
        FoodR--;
}

void far DecEatR(void)
{
    --fd_50F6_0226;
    if (fd_50F6_0226 < 0) {
        fd_50F6_0226 = RpopT >> 5;
        if (HealthR > 0)
            --HealthR;
    }
}

void far DoFoodInR(int x, int y, int attr)
{
    int dir;
    int newattr;
    int nx;
    int ny;

    dir = GetEnterDirR(x, y, attr & 7);
    if (dir < 0 || SRand16() == 0) {
        DropFoodR(x, y);
        if (SRand1(100) > HealthR)
            EatFoodR(x, y);
        RlistM[Tindex] = f_1383_0A30((attr & 0x78) >> 3);
        return;
    }
    newattr = (attr & 0xf8) | dir;
    LifeR[x][y] = newattr;
    RlistT[Tindex] = newattr;
    nx = x + Dx8[dir];
    ny = y + Dy8[dir];
    if (nx > 0x3f || nx < 0 || ny > 0x3f)
        return;
    if (ny < 1) {
        GetOutR(x);
        return;
    }
    if (MapR[nx][ny] >= 0x30)
        return;
    LifeR[x][y] = 0;
    if (CheckNestFightR(nx, ny, newattr))
        return;
    newattr = (RlistT[Tindex] & 0xf8) | dir;
    RlistT[Tindex] = newattr;
    LifeR[nx][ny] = newattr;
    RlistX[Tindex] = nx;
    RlistY[Tindex] = ny;
}

void far DoDigInR(int x, int y, int attr, int caste)
{
    int dir;
    int newattr;
    int nx;
    int ny;

    if (caste != 2 && caste != 6) {
        RlistM[Tindex] = f_1383_0A30(caste);
        return;
    }
    dir = GetEnterDirR(x, y, attr & 7);
    if (dir < 0)
        dir = SRand8();
    newattr = (attr & 0xf8) | dir;
    LifeR[x][y] = newattr;
    RlistT[Tindex] = newattr;
    if (y == 0x3f) {
        RlistM[Tindex] = f_1383_0A30(caste);
        return;
    }
    ny = y + Dy8[dir];
    nx = x + Dx8[dir];
    if (nx > 0x3f || nx < 0 || ny > 0x3f)
        return;
    if (ny < 1) {
        GetOutR(x);
        return;
    }
    if (MapR[nx][ny] >= 0x30)
        return;
    if (IsItDirt(MapR[nx][ny])) {
        if (DigTileThemR(nx, ny)) {
            RlistT[Tindex] += 0x18;
            RlistM[Tindex] = 5;
            myBeginSound(0x12, 0, 0);
        } else {
            RlistM[Tindex] = 0;
            return;
        }
    }
    LifeR[x][y] = 0;
    if (CheckNestFightR(nx, ny, newattr))
        return;
    newattr = (RlistT[Tindex] & 0xf8) | dir;
    RlistT[Tindex] = newattr;
    LifeR[nx][ny] = newattr;
    RlistX[Tindex] = nx;
    RlistY[Tindex] = ny;
    if (SRand64() > HealthR)
        TryEatFoodR(x, y);
    if (SRand4() == 0)
        f_14EE_0D71(nx, ny);
    if (MapR[nx][ny] == 0x14) {
        LifeR[nx][ny] = RlistT[Tindex] = 0;
        /* constant-left comparison: `(newattr & 0x7f) < 0x30 ? ...` lays the 0xb0 arm out first
           (jl), `0x30 > (newattr & 0x7f)` gives the original jge / 0x90-arm-first layout */
        AddAntToBList(nx, ny, newattr = 0x30 > (newattr & 0x7f) ? SRand8() + 0x90 : SRand8() + 0xb0, 3, 0);
        LifeB[nx][ny] = newattr;
    }
}

void far DoDigOutR(int x, int y, int attr)
{
    int dir;
    int newattr;
    int nx;
    int ny;
    int caste;

    dir = GetExitDirR(x, y, attr & 7);
    if (dir > 0)
        dir--;
    else
        dir = RandTurn(attr & 7);
    newattr = (attr & 0xf8) | dir;
    LifeR[x][y] = newattr;
    RlistT[Tindex] = newattr;
    nx = x + Dx8[dir];
    ny = y + Dy8[dir];
    if (nx < 0 || nx > 0x3f || ny > 0x3f)
        return;
    if (ny < 1) {
        GetOutR(x);
        return;
    }
    if (MapR[nx][ny] >= 0x30) {
        if (ExitMapR[x][y] != 0)
            ExitMapR[x][y]--;
        caste = (attr & 0x78) >> 3;
        if (caste == 5 || caste == 9) {
            RlistT[Tindex] -= 0x18;
            RlistM[Tindex] = 4;
        }
        if (caste == 2 || caste == 6)
            RlistM[Tindex] = 4;
        return;
    }
    if (IsItDirt(MapR[nx][ny]))
        return;
    LifeR[x][y] = 0;
    if (CheckNestFightR(nx, ny, newattr))
        return;
    RlistT[Tindex] = LifeR[nx][ny] = (RlistT[Tindex] & 0xf8) | dir;
    RlistX[Tindex] = nx;
    RlistY[Tindex] = ny;
    if (SRand64() > HealthR)
        TryEatFoodR(x, y);
}

int far GetOutR(int x)
{
    int raw;

    if (MapR[x][0] == 0x18) {
        raw = RlistT[Tindex];
        RlistT[Tindex] = 0;
        if (HoleMapR[x] == 0)
            MakeNewHoleR(x);
        if (f_0EC1_0437(HoleMapR[x], x, SRand8() + (raw & 0xf8),
                        RlistM[Tindex], RlistS[Tindex]) != 0) {
            LifeR[x][1] = 0;
            return 1;
        }
        RlistT[Tindex] = raw;
        RlistM[Tindex] = 0;
        return 0;
    }
    if (ExitMapR[x][0] != 0)
        ExitMapR[x][0]--;
    if (SRand2() != 0) {
        if (x > 0 && IsItDirt(MapR[x - 1][1]) != 0)
            DigTileThemR(x - 1, 1);
    } else {
        if (x < 0x3f && IsItDirt(MapR[x + 1][1]) != 0)
            DigTileThemR(x + 1, 1);
    }
    TryMoveDirR(x, 1, SRand8());
    return 0;
}
