/* root:10F7 draft: recovered prefix */
extern signed char far Dx8[];
extern signed char far Dy8[];
extern unsigned char far LifeA[128][64];
extern unsigned char far LifeB[64][64];
extern unsigned char far LifeR[64][64];
extern unsigned char far MapA[128][64];
extern unsigned char far MapB[64][64];
extern unsigned char far MapR[64][64];
extern int far MeLocX;
extern int far MeLocY;
extern int far fd_50F6_0496;
extern int far fd_50F6_04C2;
extern int far MePlane;
extern int far fd_50F6_105E;
extern int far fd_50F6_047E;
extern int far fd_50F6_048E;
extern int far fd_50F6_1074;
extern int far fd_50F6_0F34;
extern int far fd_50F6_0F12;
extern int far fd_3D57_0C22;
extern signed char far fd_3D57_0094[];
extern int far fd_50F6_04E2;
extern int far Starg;
extern int far SuserX;
extern int far SuserY;
extern int far fd_50F6_0A06;
extern int far SMode;
extern int far fd_50F6_06AC;
extern int far fd_3D57_0798;
extern int far fd_50F6_049A;
extern int far fd_50F6_0502;
extern signed char far fd_3D57_006C[];
extern int far FoodB;
extern int far FoodR;
extern unsigned char far HoleMapB[];
extern unsigned char far HoleMapR[];
extern int far TERRAINset;
extern int far fd_3D57_0C16;
extern int far fd_50F6_0FBA;
extern int far MeHealth;
extern int far fd_50F6_1006;
extern int far fd_50F6_1044;
extern long far fd_50F6_0472;
extern void far * far * far fd_50F6_034C;
extern int far BpopT;
extern int far HealthB;
extern int far fd_3D57_0C26;
extern int far fd_50F6_1044;
extern int far fd_50F6_04C4;
extern int far fd_3D57_02AC[];
extern int far fd_50F6_0B1E;
extern int far fd_50F6_0C38;
extern int far fd_3D57_0C24;
extern int far ListIndexA;
extern unsigned char far AlistX[];
extern unsigned char far AlistY[];
extern unsigned char far AlistT[];
extern unsigned char far AlistM[];
extern unsigned char far AlistS[];
extern int far ListIndexB;
extern unsigned char far BlistX[];
extern unsigned char far BlistY[];
extern unsigned char far BlistT[];
extern unsigned char far BlistM[];
extern unsigned char far BlistS[];
extern int far ListIndexR;
extern unsigned char far RlistX[];
extern unsigned char far RlistY[];
extern unsigned char far RlistT[];
extern unsigned char far RlistM[];
extern unsigned char far RlistS[];

int far IsValidA(int, int);
int far IsClearTile(int, int, int);
int far GetLife(int, int, int);
int far GetMap(int, int, int);
void far SetLife(int, int, int, int);
int far IsItDigable(int, int, int);
void far AddAntToAList(int, int, int, int, int);
void far AddAntToBList(int, int, int, int, int);
void far AddAntToRList(int, int, int, int, int);
void far DigMyTile(int, int, int);
void far myBeginSound(int, int, int);
void far ZapEuMapAt(int, int, int);
int far IsItFood(int);
void far DoEditUpdateDraw(void);
void far o22_39C7_07FD(int, int, int);
int far IsItYellow(int, int, int);
void far SetMyHealth(int);
int far DigMyNewHole(int, int);
void far o25_3BA4_1035(void);
void far f_015B_06A2(void);
int far IsItHole(int, int);
void far PickupFoodA(int, int);
unsigned long far GetDis(int, int, int, int);
int far IsItDirt(int);
int far IsSamePlane(int);
int far IsValidB(int, int);
void far f_1496_043C(int, int, int);
void far o14_384C_0ACD(int);
void far o22_39C7_188D(int, int);
void far EditMessage(void far *, long, int);
int far SRand1(int);
int far SRand8(void);
int far SRand16(void);
int far IsItAHole(int, int, int);
int far GetDir(int, int, int, int);
void far DropFoodA(int, int);
void far PauseGame(int);
void far EndTargetMode(void);
void far EndLifeTransferMode(void);
int far DoLifeExchange(int, int, int);
int far mySoundIsDone(void);
void far myDelay(long);
void far myBeginSong(unsigned int, unsigned int);
int far IsItNFood(int);
int far IsValidB(int, int);

int far IsValidLocation(int map, int index, int out)
{
    if (map <= 1)
        return IsValidA(index, out);
    else
        return IsValidB(index, out);
}

int far IsYellowAnt(int value)
{
    if (value != 0xff && value != 0xfe) return 0;
    return 1;
}

int far GetAntIndex(int list, int index, int far *life, int far *column,
                    int far *attribute, int far *state, int far *direction)
{
    if (list <= 1) {
        if (index < 0 || index >= ListIndexA)
            return 0;
        *life = AlistX[index];
        *column = AlistY[index];
        *attribute = AlistT[index];
        *state = AlistM[index];
        *direction = AlistS[index];
    } else if (list == 2) {
        if (index < 0 || index >= ListIndexB)
            return 0;
        *life = BlistX[index];
        *column = BlistY[index];
        *attribute = BlistT[index];
        *state = BlistM[index];
        *direction = BlistS[index];
    } else {
        if (index < 0 || index >= ListIndexR)
            return 0;
        *life = RlistX[index];
        *column = RlistY[index];
        *attribute = RlistT[index];
        *state = RlistM[index];
        *direction = RlistS[index];
    }
    return 1;
}

void far SetAntIndex(int list, int index, int life, int column,
                      int attribute, int state, int direction)
{
    if (list <= 1) {
        if (index < 0 || index >= ListIndexA)
            return;
        AlistX[index] = (unsigned char)life;
        AlistY[index] = (unsigned char)column;
        AlistT[index] = (unsigned char)attribute;
        AlistM[index] = (unsigned char)state;
        AlistS[index] = (unsigned char)direction;
    } else if (list == 2) {
        if (index < 0 || index >= ListIndexB)
            return;
        BlistX[index] = (unsigned char)life;
        BlistY[index] = (unsigned char)column;
        BlistT[index] = (unsigned char)attribute;
        BlistM[index] = (unsigned char)state;
        BlistS[index] = (unsigned char)direction;
    } else {
        if (index < 0 || index >= ListIndexR)
            return;
        RlistX[index] = (unsigned char)life;
        RlistY[index] = (unsigned char)column;
        RlistT[index] = (unsigned char)attribute;
        RlistM[index] = (unsigned char)state;
        RlistS[index] = (unsigned char)direction;
    }
}

int far FindLifeIndex(int list, int matchLife, int matchColumn, int low, int high, int mask)
{
    unsigned char far *lifeArr;
    unsigned char far *columnArr;
    unsigned char far *attrArr;
    int count;
    int i;
    int masked;

    if (list <= 1) {
        count = ListIndexA;
        lifeArr = AlistX;
        columnArr = AlistY;
        attrArr = AlistT;
    } else if (list == 2) {
        count = ListIndexB;
        lifeArr = BlistX;
        columnArr = BlistY;
        attrArr = BlistT;
    } else {
        count = ListIndexR;
        lifeArr = RlistX;
        columnArr = RlistY;
        attrArr = RlistT;
    }
    for (i = count - 1; i >= 0; i--) {
        masked = attrArr[i] & mask;
        if (lifeArr[i] == matchLife && columnArr[i] == matchColumn &&
            masked >= low && masked <= high)
            break;
    }
    return i;
}

int far FindAntIndex(int list, int matchLife, int matchColumn, int attribute)
{
    unsigned char far *lifeArr;
    unsigned char far *columnArr;
    unsigned char far *attrArr;
    int count;
    int i;

    if (list <= 1) {
        count = ListIndexA;
        lifeArr = AlistX;
        columnArr = AlistY;
        attrArr = AlistT;
    } else if (list == 2) {
        count = ListIndexB;
        lifeArr = BlistX;
        columnArr = BlistY;
        attrArr = BlistT;
    } else {
        count = ListIndexR;
        lifeArr = RlistX;
        columnArr = RlistY;
        attrArr = RlistT;
    }
    for (i = count - 1; i >= 0; i--) {
        if (lifeArr[i] == matchLife && columnArr[i] == matchColumn &&
            attrArr[i] == attribute)
            break;
    }
    return i;
}

int far IsClear3x3(int type, int y, int x)
{
    register int index;

    if (IsClearTile(type, y, x) == 1) {
        for (index = 0; index < 8; ++index) {
            if (!IsClearTile(type, y + Dx8[index], x + Dy8[index]))
                return 0;
        }
        return 1;
    }
    return 0;
}

int far IsClearTile(int plane, int x, int y)
{
    int result;
    int tile;
    int life;

    result = 0;
    tile = GetMap(plane, x, y);
    if (tile >= 0) {
        life = GetLife(plane, x, y);
        if (life < 0 || IsYellowAnt(life) == 1) {
            if (plane <= 1) {
                if (tile < 16)
                    result = 1;
            } else {
                if (tile < 8)
                    result = 1;
            }
        }
    }
    return result;
}

int far AddAntToList(int plane, int x, int y, int type, int a, int b)
{
    int added;

    added = 0;
    if (plane <= 1) {
        if (ListIndexA < 1000) {
            AddAntToAList(x, y, type, a, b);
            added = 1;
        }
    } else if (plane == 2) {
        if (ListIndexB < 500) {
            AddAntToBList(x, y, type, a, b);
            added = 1;
        }
    } else if (ListIndexR < 500) {
        AddAntToRList(x, y, type, a, b);
        added = 1;
    }
    if (added == 1)
        SetLife(plane, x, y, type);
    return added;
}

void far SetLife(int plane, int x, int y, int value)
{
    if (IsValidLocation(plane, x, y) == 1) {
        switch (plane) {
        case 0:
        case 1:
            LifeA[x][y] = value;
            break;
        case 2:
            LifeB[x][y] = value;
            if (value > 0 && IsItDigable(plane, x, y) == 1) {
                DigMyTile(plane, x, y);
                myBeginSound(0x13, 0, 0x3f);
            }
            break;
        case 3:
            LifeR[x][y] = value;
            if (value > 0 && IsItDigable(plane, x, y) == 1) {
                DigMyTile(plane, x, y);
                myBeginSound(0x13, 0, 0x3f);
            }
            break;
        }
        ZapEuMapAt(plane, x, y);
    }
}

int far IsThisEgg(value)
unsigned char value;
{
    int normalized;
    normalized = value;
    normalized &= 0x7f;
    if (normalized >= 1 && normalized <= 7) return 1;
    return 0;
}

int far IsThisGrass(int category, int tile)
{
    if (category < 2)
        return 0;
    if (tile < 0x1c || tile > 0x1f)
        return 0;
    return 1;
}

int far IsThisFood(int category, int tile)
{
    if (category <= 1)
        return IsItFood(tile);
    return IsItNFood(tile);
}

int far IsThisPebble(int plane, int tile)
{
    if (plane <= 1) {
        if (plane == 1 && tile >= 0x51 && tile <= 0x53)
            return 1;
        return 0;
    }
    if (tile >= 0x30 && tile <= 0x31)
        return 1;
    return 0;
}

int far IsItNFood(int value)
{
    if (value < 0x10 || value > 0x13) return 0;
    return 1;
}

int far IsItFoodAt(int plane, int x, int y)
{
    register int tile;

    tile = GetMap(plane, x, y);
    if (tile < 0)
        return 0;
    if (plane <= 1)
        return IsItFood(tile);
    return IsItNFood(tile);
}

int far GetLife(int plane, int x, int y)
{
    int result;

    result = -1;
    if (IsValidLocation(plane, x, y) == 1) {
        switch (plane) {
        case 0:
        case 1:
            result = LifeA[x][y];
            break;
        case 2:
            result = LifeB[x][y];
            break;
        case 3:
            result = LifeR[x][y];
            break;
        }
        if (result == 0)
            result = -1;
    }
    return result;
}

int far GetMap(int plane, int x, int y)
{
    int result;

    result = -1;
    if (IsValidLocation(plane, x, y) == 1) {
        switch (plane) {
        case 0:
        case 1:
            result = MapA[x][y];
            break;
        case 2:
            result = MapB[x][y];
            break;
        case 3:
            result = MapR[x][y];
            break;
        }
    }
    return result;
}

void far SetMap(int plane, int x, int y, int value)
{
    if (IsValidLocation(plane, x, y) == 1) {
        switch (plane) {
        case 0:
        case 1:
            MapA[x][y] = value;
            break;
        case 2:
            MapB[x][y] = value;
            break;
        case 3:
            MapR[x][y] = value;
            break;
        }
        ZapEuMapAt(plane, x, y);
    }
}

void far ClearLife(int plane, int x, int y, int value)
{
    if (IsValidLocation(plane, x, y) == 1) {
        if (GetLife(plane, x, y) == value)
            SetLife(plane, x, y, 0);
        ZapEuMapAt(plane, x, y);
    }
}

void far ClearMyLife(int plane, int x, int y, int type, int dir)
{
    ClearLife(plane, x, y, 0xff);
    if (type == 0x60)
        ClearLife(plane, x + Dx8[dir ^ 4], y + Dy8[dir ^ 4], 0xfe);
}

void far SetQueenTail(int plane, int x, int y, int dir, int value)
{
    SetLife(plane, x + Dx8[dir ^ 4], y + Dy8[dir ^ 4],
                (value == 0xff) ? 0xfe : value);
}

void far SetMyLife(int plane, int x, int y, int type, int dir, int life)
{
    if (IsValidLocation(plane, x, y) == 1) {
        SetLife(plane, x, y, life);
        if (type == 0x60)
            SetQueenTail(plane, x, y, dir, life);
        if (life != 0) {
            MeLocX = x;
            MeLocY = y;
            fd_50F6_0496 = dir;
            fd_50F6_04C2 = type;
            MePlane = plane;
        }
    }
}

void far MoveMyLife(int plane, int x, int y, int type, int dir)
{
    ClearMyLife(MePlane, MeLocX, MeLocY, fd_50F6_04C2, fd_50F6_0496);
    SetMyLife(plane == 0 ? 1 : plane, x, y, type, dir, 0xff);
}

void far DoMapUpdateDraw(void)
{
}

void far DoEditAndMapUpdateDraw(void)
{
    DoMapUpdateDraw();
    DoEditUpdateDraw();
}

void far TargetAnt(void)
{
    if (fd_50F6_105E == 0xb) {
        EndTargetMode();
        return;
    }
    fd_50F6_048E = fd_50F6_047E;
    fd_50F6_105E = 0xb;
    PauseGame(1);
}

void far EndTargetMode(void)
{
    fd_50F6_105E = -1;
    PauseGame(fd_50F6_048E);
}

void far StartLifeTransfer(void)
{
    if (fd_50F6_105E == 0xa) {
        EndLifeTransferMode();
        return;
    }
    fd_50F6_048E = fd_50F6_047E;
    fd_50F6_105E = 0xa;
    PauseGame(1);
}

void far EndLifeTransferMode(void)
{
    fd_50F6_105E = -1;
    PauseGame(fd_50F6_048E);
}

void far ExchangeLives(int a, int b, int c)
{
    fd_50F6_1074 = 1;
    if (DoLifeExchange(a, b, c) == 1) {
        EndLifeTransferMode();
        if (fd_50F6_04C2 == 0x60) {
            myBeginSound(0xf, 0, 0x7e);
            DoEditUpdateDraw();
            while (!mySoundIsDone())
                myDelay(5L);
            myBeginSong(0x2afe, 0x7e);
        } else
            myBeginSound(0xf, 0, 0x7e);
    } else
        myBeginSound(1, 0, 0x7e);
}

int far DoLifeExchange(int plane, int x, int y)
{
    int newLife;
    int t;
    int index;
    int caste;
    int x2;
    int y2;
    int index2;
    int egg;
    int life;
    int direction;
    int state;
    int attribute;
    int column;
    int lifeField;
    int u;

    life = GetLife(plane, x, y);
    if (life <= 0) {
        if (plane != 1)
            goto fail;
        if (GetDis(x * 16 + 8, y * 16 + 8, fd_50F6_0F12, fd_50F6_0F34) >= 0x200)
            goto fail;
        newLife = (fd_50F6_04C2 & 0x78) >> 3;
        egg = 0;
        if (fd_50F6_04C2 & 8) {
            if (newLife == 5 || newLife == 9)
                newLife = fd_3D57_0094[newLife];
            else if (newLife == 1)
                egg = fd_3D57_0C22;
        }
        life = (fd_50F6_04E2 & 0x80) | fd_50F6_0496 | (newLife << 3);
        if (fd_50F6_04C2 == 0x60)
            t = 9;
        else
            t = 0;
        if (!AddAntToList(MePlane, MeLocX, MeLocY, life, t, egg))
            goto fail;
        if (fd_50F6_04C2 == 0x60) {
            if (!AddAntToList(MePlane, MeLocX + Dx8[fd_50F6_0496 ^ 4],
                             MeLocY + Dy8[fd_50F6_0496 ^ 4], life + 8, t, 0))
                goto fail;
        }
        SetMyLife(MePlane, MeLocX, MeLocY, fd_50F6_04C2, fd_50F6_0496, 0);
        Starg = -2;
        SuserX = fd_50F6_0F12 >> 4;
        SuserY = fd_50F6_0F34 >> 4;
        fd_50F6_0A06 = 1;
        SMode = 0;
        fd_50F6_06AC = 0;
        fd_50F6_04E2 = 0;
        o22_39C7_07FD(plane, SuserX, SuserY);
        SetMyHealth(100);
        goto done;
    }
    if (IsItYellow(plane, x, y) || IsYellowAnt(life))
        goto done;
    caste = (life & 0x78) >> 3;
    if (caste == 0xc) {
        x2 = x + Dx8[(life ^ 4) & 7];
        y2 = y + Dy8[(life ^ 4) & 7];
        newLife = GetLife(plane, x2, y2);
    } else if (caste == 0xd) {
        x2 = x;
        y2 = y;
        newLife = life;
        x += Dx8[life & 7];
        y += Dy8[life & 7];
        life = GetLife(plane, x, y);
        caste = 0xc;
    }
    index = FindAntIndex(plane, x, y, life);
    if (caste == 0xc)
        index2 = FindAntIndex(plane, x2, y2, newLife);
    if (index < 0)
        goto fail;
    if (fd_50F6_0A06 == 0) {
        int c;

        u = (fd_50F6_04C2 & 0x78) >> 3;
        egg = 0;
        if (fd_50F6_04C2 & 8) {
            if (u == 5 || u == 9)
                u = fd_3D57_0094[u];
            else if (u == 1)
                egg = fd_3D57_0C22;
        }
        newLife = (u << 3) | fd_50F6_0496 | (life & 0x80);
        if (life & 0x80) {
            if (!(*(unsigned char far *)0x417L & 8) || !(*(unsigned char far *)0x417L & 3))
                goto fail;
        }
        c = (life & 0x78) >> 3;
        if (c <= 0 || c > 0xd || c == 0xa || c == 0xb) {
            if (!(*(unsigned char far *)0x417L & 8) || !(*(unsigned char far *)0x417L & 3) || !fd_3D57_0798)
                goto fail;
        }
        if (c == 5 || c == 9)
            life = (fd_3D57_0094[(life & 0x78) >> 3] << 3) | (life & 7);
        else if (c == 1) {
            GetAntIndex(plane, index, &lifeField, &column, &attribute, &state, &direction);
            fd_3D57_0C22 = direction;
        }
        t = (fd_50F6_04C2 == 0x60) ? 9 : 0;
        ZapEuMapAt(MePlane, MeLocX, MeLocY);
        if (t)
            ZapEuMapAt(MePlane, MeLocX + Dx8[fd_50F6_0496 ^ 4],
                        MeLocY + Dy8[fd_50F6_0496 ^ 4]);
        ZapEuMapAt(plane, x, y);
        if (caste == 0xc)
            ZapEuMapAt(plane, x2, y2);
        SetAntIndex(plane, index, 0, 0, 0, 0, 0);
        if (caste == 0xc)
            SetAntIndex(plane, index2, 0, 0, 0, 0, 0);
        if (!AddAntToList(MePlane, MeLocX, MeLocY, newLife, t, egg))
            goto fail;
        if (fd_50F6_04C2 == 0x60) {
            if (!AddAntToList(MePlane, MeLocX + Dx8[fd_50F6_0496 ^ 4],
                             MeLocY + Dy8[fd_50F6_0496 ^ 4], newLife + 8, t, 0))
                goto fail;
        }
    } else {
        int c;

        if (life & 0x80) {
            if (!(*(unsigned char far *)0x417L & 8) || !(*(unsigned char far *)0x417L & 3))
                goto fail;
        }
        c = (life & 0x78) >> 3;
        if (c <= 0 || c > 0xd || c == 0xa || c == 0xb) {
            if (!(*(unsigned char far *)0x417L & 8) || !(*(unsigned char far *)0x417L & 3) || !fd_3D57_0798)
                goto fail;
        }
        if (c == 5 || c == 9)
            life = (fd_3D57_0094[(life & 0x78) >> 3] << 3) | (life & 7);
        else if (c == 1) {
            GetAntIndex(plane, index, &lifeField, &column, &attribute, &state, &direction);
            fd_3D57_0C22 = direction;
        }
        SetAntIndex(plane, index, 0, 0, 0, 0, 0);
        if (caste == 0xc)
            SetAntIndex(plane, index2, 0, 0, 0, 0, 0);
    }
    fd_50F6_04E2 = life & 0x80;
    fd_50F6_049A = 0;
    fd_50F6_0A06 = 0;
    fd_50F6_06AC = 0;
    SetMyHealth(100);
    SetMyLife(plane, x, y, life & 0x78, life & 7, 0xff);
    if (fd_50F6_04C2 < 8)
        fd_50F6_0502 = fd_50F6_0496;
done:
    return 1;
fail:
    return 0;
}

int far DropMyFood(int plane, int x, int y, int tx, int ty)
{
    int i;
    int dir;
    int done;
    int tile;
    int nx;
    int ny;
    int d;

    if (fd_50F6_04C2 != 0x18 && fd_50F6_04C2 != 0x38)
        return 0;
    done = 0;
    dir = GetDir(x, y, tx, ty);
    if (dir > 0)
        dir--;
    else
        dir = fd_50F6_0496;
    for (i = 0; !done; i++) {
        if (i >= 8)
            break;
        d = (fd_3D57_006C[i] + dir) & 7;
        nx = x + Dx8[d];
        ny = y + Dy8[d];
        if (IsValidLocation(plane, nx, ny)) {
            if (GetLife(plane, nx, ny) < 0) {
                tile = GetMap(plane, nx, ny);
                if (IsThisFood(plane, tile) && (tile & 3) < 3) {
                    tile++;
                    done = 1;
                } else if (IsClearTile(plane, nx, ny) || tile == 0x38) {
                    tile = 0x10;
                    done = 1;
                }
            }
        }
    }
    if (!done) {
        d = dir;
        nx = x;
        ny = y;
        if (IsValidLocation(plane, nx, ny)) {
            tile = GetMap(plane, nx, ny);
            if (IsThisFood(plane, tile) && (tile & 3) < 3) {
                tile++;
                done = 1;
            } else if (IsClearTile(plane, nx, ny) || tile == 0x38) {
                tile = 0x10;
                done = 1;
            }
        }
    }
    if (done) {
        fd_50F6_0496 = d;
        if (plane <= 1)
            DropFoodA(nx, ny);
        else {
            SetMap(plane, nx, ny, tile);
            if (plane == 2)
                FoodB++;
            else
                FoodR++;
        }
        if (!((*(unsigned char far *)0x417L & 3) && (*(unsigned char far *)0x417L & 8)))
            fd_50F6_04C2 &= 0xf7;
        myBeginSound(0x1d, 0, 0x7e);
    }
    return done;
}

void far DropPebble(int plane, int x, int y)
{
    int tile;

    if (plane <= 1) {
        if (IsItAHole(plane, x, y)) {
            if (x < 0x40 && HoleMapB[y] == x)
                MapB[y][0] = 0x31;
            else if (HoleMapR[y] == x)
                MapR[y][0] = 0x31;
        }
        tile = 0x51;
    } else if (IsItAHole(plane, x, y)) {
        MapA[plane == 2 ? HoleMapB[x] : HoleMapR[x]][x] = 0x51;
        tile = 0x31;
    } else
        tile = 0x30;
    SetMap(plane, x, y, tile);
}

int far DropMyRock(int plane, int x, int y, int tx, int ty)
{
    int tile;
    int i;
    int dir;
    int done;
    int ny;
    int nx;
    int d;

    if (fd_50F6_04C2 != 0x28 && fd_50F6_04C2 != 0x48)
        return 0;
    done = 0;
    dir = GetDir(x, y, tx, ty);
    if (dir > 0)
        dir--;
    else
        dir = fd_50F6_0496;
    for (i = 0; !done; i++) {
        if (i >= 8)
            break;
        d = (fd_3D57_006C[i] + dir) & 7;
        nx = x + Dx8[d];
        ny = y + Dy8[d];
        if (IsValidLocation(plane, nx, ny)) {
            if (GetLife(plane, nx, ny) < 0) {
                if (IsClearTile(plane, nx, ny))
                    done = 1;
                else {
                    tile = GetMap(plane, nx, ny);
                    if (!IsThisFood(plane, tile) && !IsThisPebble(plane, tile) &&
                        (IsItAHole(plane, nx, ny) || tile == 0x38))
                        done = 1;
                }
            }
        }
    }
    if (!done) {
        d = dir;
        nx = x;
        ny = y;
        if (IsValidLocation(plane, nx, ny)) {
            if (IsClearTile(plane, nx, ny))
                done = 1;
            else {
                tile = GetMap(plane, nx, ny);
                if (!IsThisFood(plane, tile) && !IsThisPebble(plane, tile) &&
                    (IsItAHole(plane, nx, ny) || tile == 0x38))
                    done = 1;
            }
        }
    }
    if (done) {
        fd_50F6_0496 = d;
        DropPebble(plane, nx, ny);
        if (!((*(unsigned char far *)0x417L & 3) && (*(unsigned char far *)0x417L & 8))) {
            if (fd_50F6_04C2 == 0x28 || fd_50F6_04C2 == 0x48)
                fd_50F6_04C2 -= 0x18;
        }
        myBeginSound(0x1e, 0, 0x7e);
    }
    return done;
}

int far DropMyEgg(int plane, int x, int y, int tx, int ty)
{
    int i;
    int done;
    int dir;
    int ny;
    int nx;
    int d;

    if (fd_50F6_04C2 != 8)
        return 0;
    done = 0;
    dir = GetDir(x, y, tx, ty);
    if (dir > 0)
        dir--;
    else
        dir = fd_50F6_0496;
    for (i = 0; !done; i++) {
        if (i >= 8)
            break;
        d = (fd_3D57_006C[i] + dir) & 7;
        nx = x + Dx8[d];
        ny = y + Dy8[d];
        if (IsValidLocation(plane, nx, ny)) {
            if (GetLife(plane, nx, ny) < 0) {
                if (IsClearTile(plane, nx, ny) || GetMap(plane, nx, ny) == 0x38)
                    done = 1;
            }
        }
    }
    if (!done) {
        d = dir;
        nx = x;
        ny = y;
        if (IsValidLocation(plane, nx, ny)) {
            if (IsClearTile(plane, nx, ny) || GetMap(plane, nx, ny) == 0x38)
                done = 1;
        }
    }
    if (done)
        done = AddAntToList(plane, nx, ny, fd_3D57_0C22, 8, 0);
    if (done) {
        fd_50F6_0496 = d;
        if (!((*(unsigned char far *)0x417L & 3) && (*(unsigned char far *)0x417L & 8))) {
            fd_50F6_04C2 = 0x10;
            fd_3D57_0C22 = 0xfd;
        }
        SetMyLife(MePlane, MeLocX, MeLocY, fd_50F6_04C2, fd_50F6_0496, 0xff);
        myBeginSound(0x1c, 0, 0x7e);
    }
    return done;
}

int far PickupMyRock(int plane, int x, int y)
{
    int tile;
    int done;

    if (fd_50F6_04C2 != 0x10 && fd_50F6_04C2 != 0x30)
        return 0;
    done = 0;
    tile = GetMap(plane, x, y);
    if (plane <= 1) {
        if (IsThisPebble(plane, tile)) {
            if (x < 0x40) {
                if (HoleMapB[y] == x) {
                    MapB[y][0] = 0x18;
                    done = 1;
                }
            } else if (HoleMapR[y] == x) {
                MapR[y][0] = 0x18;
                done = 1;
            }
            if (done) {
                if (TERRAINset == 0)
                    MapA[x][y] = 0x50;
                else
                    MapA[x][y] = SRand1(7) + 0x59;
            } else {
                if (TERRAINset == 0)
                    MapA[x][y] = SRand16();
                else
                    MapA[x][y] = 0;
                done = 1;
            }
        }
    } else if (tile == 0x30) {
        SetMap(plane, x, y, SRand8());
        done = 1;
    } else if (tile == 0x31) {
        if (plane == 2) {
            MapB[x][y] = 0x18;
            MapA[HoleMapB[x]][x] = 0x50;
        } else {
            MapR[x][y] = 0x18;
            MapA[HoleMapR[x]][x] = 0x50;
        }
        done = 1;
    }
    if (done) {
        if (fd_50F6_04C2 == 0x10)
            fd_50F6_04C2 = 0x28;
        else
            fd_50F6_04C2 = 0x48;
        myBeginSound(0x1e, 0, 0x7e);
    }
    return done;
}

int far FindEggAt(int far *index, int plane, int x, int y)
{
    int i;
    int life;
    int direction;
    int state;
    int column;
    int lifeField;

    life = GetLife(plane, x, y);
    if (IsThisEgg(life) && !IsYellowAnt(life)) {
        *index = FindAntIndex(plane, x, y, life);
        return life;
    }
    i = FindLifeIndex(plane, x, y, 1, 7, 0x7f);
    if (i >= 0) {
        GetAntIndex(plane, i, &lifeField, &column, &life, &state, &direction);
        *index = i;
        return life;
    }
    *index = -1;
    return -1;
}

int far FindLifeAt(int far *index, int plane, int x, int y)
{
    int i;
    int life;
    int direction;
    int state;
    int column;
    int lifeField;

    life = GetLife(plane, x, y);
    if (life >= 0 && !IsYellowAnt(life)) {
        *index = FindAntIndex(plane, x, y, life);
        return life;
    }
    i = FindLifeIndex(plane, x, y, 1, 0x7f, 0x7f);
    if (i >= 0) {
        GetAntIndex(plane, i, &lifeField, &column, &life, &state, &direction);
        *index = i;
        return life;
    }
    *index = -1;
    return -1;
}

void far SetMyHealth(int health)
{
    if (!fd_3D57_0C16)
        MeHealth = health;
    else
        MeHealth = 100;
    if (MeHealth > 0)
        fd_50F6_1006 = 0;
    if (MeHealth > 100)
        MeHealth = 100;
    else if (MeHealth < 0)
        MeHealth = 0;
    if (MeHealth > fd_50F6_0FBA && MeHealth >= 10)
        fd_50F6_1044 = 0;
    else
        fd_50F6_1044 = 1;
}

void far EatMyFood(int kind)
{
    switch (kind) {
    case 0:
        myBeginSound(0x2c, 0, 0x7e);
        o14_384C_0ACD(1);
        break;
    case 1:
        o22_39C7_188D(0x2396, -1);
        fd_50F6_0472 = 0L;
        EditMessage(fd_50F6_034C[11], 120L, 0);
        break;
    case 2:
        EditMessage(fd_50F6_034C[12], 120L, 0);
        break;
    case 3:
        myBeginSound(0x2c, 0, 0x7e);
        while (!mySoundIsDone())
            myDelay(5L);
        myBeginSound(10, 0, 0x7e);
        fd_50F6_0472 = 0L;
        EditMessage(fd_50F6_034C[13], 180L, 0);
        break;
    }
    if (kind != 2) {
        if (MeHealth + 100 > 100 && kind != 1 && BpopT - 1 > 0) {
            HealthB += MeHealth / (BpopT - 1);
            if (HealthB > 100)
                HealthB = 100;
        }
        SetMyHealth(100);
    } else if (MeHealth > 10)
        SetMyHealth(MeHealth - 10);
}

int far PickupMyEgg(int plane, int x, int y)
{
    int egg;
    int index;

    if (fd_50F6_04C2 == 0x10 || MeHealth < 10) {
        fd_3D57_0C22 = 0xfd;
        egg = FindEggAt(&index, plane, x, y);
        if (egg >= 0) {
            SetAntIndex(plane, index, 0, 0, 0, 0, 0);
            if (x != MeLocX || y != MeLocY)
                SetLife(plane, x, y, 0);
            if (MeHealth >= 10) {
                myBeginSound(0x1c, 0, 0x7e);
                fd_3D57_0C22 = egg;
                fd_50F6_04C2 = 8;
            } else
                fd_3D57_0C26 = 3;
            return 1;
        }
    }
    return 0;
}

int far PickupMyFood(int plane, int x, int y)
{
    int eat;
    int tile;

    if (!IsItFoodAt(plane, x, y))
        return 0;
    if (fd_50F6_1044)
        eat = 1;
    else if (fd_50F6_04C2 == 0x10 || fd_50F6_04C2 == 0x30)
        eat = 0;
    else
        return 0;
    if (plane <= 1) {
        PickupFoodA(x, y);
        if (!eat) {
            fd_50F6_04C4 = 200;
            fd_50F6_0B1E = GetDis(x, y, fd_3D57_02AC[0], fd_3D57_02AC[1]);
            fd_50F6_0C38 = fd_50F6_0B1E + 1;
            f_1496_043C(x, y, fd_50F6_04C4);
        }
    } else {
        tile = GetMap(plane, x, y);
        if (tile == 0x10)
            tile = SRand8();
        else
            tile--;
        SetMap(plane, x, y, tile);
        if (plane == 2) {
            if (FoodB > 0)
                FoodB--;
        } else if (FoodR > 0)
            FoodR--;
    }
    if (eat)
        fd_3D57_0C26 = 0;
    else {
        myBeginSound(0x1d, 0, 0x7e);
        fd_50F6_04C2 += 8;
    }
    return 1;
}

int far DropMyObject(int first, int second, int third, int fourth, int fifth)
{
    switch (fd_50F6_04C2) {
    case 8:
        return DropMyEgg(first, second, third, fourth, fifth);
    case 0x18:
    case 0x38:
        return DropMyFood(first, second, third, fourth, fifth);
    case 0x28:
    case 0x48:
        return DropMyRock(first, second, third, fourth, fifth);
    }
    return 0;
}

int far PickupMyObject(int plane, int x, int y)
{
    int result;

    if (fd_50F6_04C2 & 8)
        return 0;
    result = PickupMyEgg(plane, x, y);
    if (result == 0) {
        result = PickupMyRock(plane, x, y);
        if (result == 0)
            result = PickupMyFood(plane, x, y);
    }
    return result;
}

int far TileCanBeMovedOn(int plane, int x, int y, int fromPlane, int fromX, int fromY, int digging)
{
    int dig;
    int ok;
    int tile;

    if (plane <= 1) {
        if (x >= 0 && x <= 127 && y >= 0 && y <= 63) {
            dig = MapA[x][y];
            if (!TERRAINset)
                ok = dig <= 0x53;
            else
                ok = dig <= 0x90;
        } else
            ok = 0;
    } else if (x >= 0 && x <= 63 && y >= 0 && y <= 63) {
        if (plane == 2)
            tile = MapB[x][y];
        else
            tile = MapR[x][y];
        if (tile <= 0x18 || (tile >= 0x30 && tile <= 0x31)) {
            ok = 1;
            dig = 0;
        } else if (digging && ((tile >= 0x20 && tile <= 0x2e) || (tile >= 0x1c && tile <= 0x1f))) {
            ok = 1;
            dig = 1;
        } else
            ok = 0;
        if (ok && y <= 1 && fromPlane == plane) {
            if (!digging) {
                if (y == 0) {
                    if (fromX != x || fromY != y)
                        ok = 0;
                } else if (fromX != x && !fromY)
                    ok = 0;
            } else if (dig) {
                if (fromX != x)
                    ok = 0;
                else if (y == 0) {
                    if (plane == 2)
                        tile = MapB[x][y + 1];
                    else
                        tile = MapR[x][y + 1];
                    if (tile >= 0x20 && tile <= 0x2e)
                        ok = 0;
                }
            } else if (y == 0 && (fromX != x || fromY != y))
                ok = 0;
        }
    } else
        ok = 0;
    return ok;
}

int far IsNotBarrier(int x)
{
    if (!TERRAINset)
        return x <= 0x50;
    return x <= 0x5f;
}

int far IsNotObstacle(int plane, int x, int y)
{
    int tile;
    int ok;

    tile = GetMap(plane, x, y);
    if (tile < 0)
        ok = 0;
    else if (plane <= 1) {
        if (!TERRAINset)
            ok = tile <= 0x53;
        else
            ok = IsNotBarrier(tile);
    } else if (tile <= 0x18 || IsThisPebble(plane, tile))
        ok = 1;
    else
        ok = 0;
    return ok;
}

int far IsItDigable(int plane, int x, int y)
{
    int tile;

    if (plane >= 2 && IsValidB(x, y)) {
        tile = GetMap(plane, x, y);
        if (IsItDirt(tile))
            return 1;
        if (IsThisGrass(plane, tile))
            return 1;
    }
    return 0;
}

int far IsItYellow(int plane, int x, int y)
{
    int life;

    if (!IsSamePlane(plane))
        return 0;
    if (fd_50F6_0A06 == 1) {
        if (plane > 1)
            return 0;
        if (GetDis(x * 16 + 8, y * 16 + 8, fd_50F6_0F12, fd_50F6_0F34) < 0x200)
            return 1;
        return 0;
    }
    switch (plane) {
    case 0:
    case 1:
        life = LifeA[x][y];
        break;
    case 2:
        life = LifeB[x][y];
        break;
    case 3:
        life = LifeR[x][y];
        break;
    }
    return IsYellowAnt(life);
}

int far IsLessThanHole(int x)
{
    if (!TERRAINset)
        return x < 0x50;
    return x < 0x59;
}

int far IsSamePlane(int plane)
{
    if (MePlane == (plane == 0 ? 1 : plane))
        return 1;
    return 0;
}

int far IsLiftable(int plane, int x, int y)
{
    int tile;
    int eggIndex;
    int egg;

    egg = FindEggAt(&eggIndex, plane, x, y);
    tile = GetMap(plane, x, y);
    return IsThisFood(plane, tile) || IsThisPebble(plane, tile) || IsThisEgg(egg);
}

int far TryMyDropOrLift(int plane, int x, int y)
{
    int dir;
    int result;

    if (fd_50F6_04C2 & 8)
        result = DropMyObject(plane, MeLocX, MeLocY, x, y) ? 1 : -1;
    else if (!PickupMyObject(plane, x, y)) {
        if ((fd_3D57_0798 || (fd_50F6_04C2 == 0x40 && !fd_3D57_0C24)) &&
            MePlane == 1 && MeLocX == x && MeLocY == y) {
            if (DigMyNewHole(x, y)) {
                o25_3BA4_1035();
                f_015B_06A2();
                result = 1;
            } else
                result = -1;
        } else
            result = 0;
    } else {
        dir = GetDir(MeLocX, MeLocY, x, y);
        if (dir > 0)
            MoveMyLife(MePlane, MeLocX, MeLocY, fd_50F6_04C2, dir - 1);
        DoEditUpdateDraw();
        if (fd_3D57_0C26 >= 0) {
            EatMyFood(fd_3D57_0C26);
            fd_3D57_0C26 = -1;
        }
        result = 1;
    }
    return result;
}

int far IsItAHole(int plane, int x, int y)
{
    if (plane <= 1)
        return IsItHole(x, y);
    if (y > 0)
        return 0;
    if (GetMap(plane, x, y) == 0x18)
        return 1;
    return 0;
}

int far IsValidA(int x, int y)
{
    if (x >= 0 && x <= 127 && y >= 0 && y <= 63)
        return 1;
    return 0;
}

int far IsValidB(int x, int y)
{
    if (x >= 0 && x <= 63 && y >= 0 && y <= 63)
        return 1;
    return 0;
}
