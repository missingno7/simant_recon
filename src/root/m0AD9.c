/* Root module, code frame 0AD9: sowing, ant lions and the pill bug (pillar). */

extern int far SRand1(int range);
extern unsigned char far MapA[128][64];
extern int far SowX[3];
extern int far SowY[3];
extern int far SowDir[3];
extern int far SowSave[3];
extern unsigned char far SowTab[8];
extern int far SRand4(void);
extern char far Dy8[8];
extern char far Dx8[8];
extern int far f_10F7_2867(int x, int y);
extern unsigned char far LifeA[128][64];
extern int far LionIndex;
extern int far AntsEatenByLions;
extern int far InitialLions;
extern int far IsClear3x3(int plane, int x, int y);
extern int far IsClearTile(int plane, int x, int y);
extern void far SetMap(int plane, int x, int y, int value);
extern unsigned char far LionListX[];
extern unsigned char far LionListY[];
extern unsigned char far LionListM[];
extern unsigned char far LionListS[];
extern unsigned char far LionListT[];
extern int far GetMap(int plane, int x, int y);
extern int far f_10F7_0731(int plane, int tile);
extern int far IsThisFood(int category, int tile);
extern char far Dy9[9];
extern char far Dx9[9];
extern int far IsYellowAnt(int value);
extern int far fd_50F6_0496;
extern int far fd_50F6_04C2;
extern void far MoveMyLife(int plane, int x, int y, int type, int dir);
extern void far o22_39C7_0D21(int code);
extern int far SRand8(void);
extern void far f_00DF_0164(int, int, int, int, long, int);
extern int far FindInAList(int x, int y);
extern void far RemoveFromAList(int index);
extern long far BAntsEaten;
extern long far RAntsEaten;
extern void far myBeginSound(int sound, int a, int b);
extern void far PictStrnDialog(int a, int b, int c);
extern int far PillarState;
extern int far PillarX;
extern int far PillarY;
extern int far PillarSeg;
extern int far PillDir;
extern int far PillarMap[6];
extern int far TERRAINset;

void far InitSow(void);
void far DoSow(void);
void far InitAntLions(int count);
void far AddRandAntLion(void);
void far AddAntLion(int x, int y);
void far DoAntLions(void);
void far SetAntLion(int index);
int far FindInLionList(int x, int y);
void far KillAntLion(int index);
void far InitPillar(void);
void far DoPillar(void);
void far StorePillarMap(int x, int y);
void far ReplacePillarMap(int x, int y);
void far MakeAPill(void);
void far PlacePillTile(int x, int y, int value);
int far PillGetLife(int x, int y);
int far IsPillDead(void);
void far MakePillFood(void);
void far PillFoodTile(int x, int y);

void far InitSow(void)
{
    int i;
    int x;
    int y;

    i = 2;
    while (i) {
        x = SRand1(128);
        y = SRand1(64);
        if (MapA[x][y] < 16) {
            SowX[i] = x;
            SowY[i] = y;
            SowDir[i] = SRand1(8);
            SowSave[i] = MapA[x][y];
            MapA[x][y] = SowTab[SowDir[i]];
            i--;
        }
    }
}

void far DoSow(void)
{
    int i;
    int newX;
    int newY;
    int terrain;

    for (i = 0; i < 3; i++) {
        if (SRand4() == 0)
            continue;
        if (SRand4() == 0) {
            SowDir[i] = (SowDir[i] + SRand1(3) - 1) & 7;
            MapA[SowX[i]][SowY[i]] = SowTab[SowDir[i]];
        }
        newX = SowX[i] + Dx8[SowDir[i]];
        if (!f_10F7_2867(newX, newY = SowY[i] + Dy8[SowDir[i]]))
            continue;
        if (LifeA[newX][newY] != 0)
            continue;
        terrain = MapA[newX][newY];
        if (terrain >= 0x10)
            continue;
        MapA[SowX[i]][SowY[i]] = SowSave[i];
        SowSave[i] = terrain;
        MapA[newX][newY] = SowTab[SowDir[i]];
        SowX[i] = newX;
        SowY[i] = newY;
    }
}

void far InitAntLions(int count)
{
    int i;

    LionIndex = 0;
    AntsEatenByLions = 0;
    if (count > 10)
        count = 10;
    for (i = 0; i < count; i++)
        AddRandAntLion();
    InitialLions = count;
}

void far AddRandAntLion(void)
{
    int tries;
    int x;
    int y;

    for (tries = 0; tries < 200; tries++) {
        x = SRand1(0x40) + SRand1(0x41);
        y = SRand1(0x20) + SRand1(0x21);
        if (IsClear3x3(1, x, y) == 1 || (IsClearTile(1, x, y) == 1 && tries >= 100)) {
            AddAntLion(x, y);
            return;
        }
    }
}

static unsigned char lionRing[8] = {1, 2, 4, 7, 6, 5, 3, 0};

void far AddAntLion(int x, int y)
{
    int i;
    int lx;
    int ly;

    SetMap(1, x, y, 0x38);
    for (i = 0; i < 8; i++) {
        lx = x + Dx8[i];
        if (IsClearTile(1, lx, ly = y + Dy8[i]) == 1)
            SetMap(1, lx, ly, lionRing[i] + 0x30);
    }
    LionListX[LionIndex] = x;
    LionListY[LionIndex] = y;
    LionListM[LionIndex] = 0;
    LionListS[LionIndex] = 0;
    LionListT[LionIndex] = 0;
    if (LionIndex < 9)
        LionIndex++;
}

void far DoAntLions(void)
{
    int i;
    int dir;
    int count;
    int ny;
    int nx;
    int y;
    int x;
    int tile;
    int k;
    int j;
    int d;

    if (LionIndex == 0 && InitialLions > 0 && SRand1(0x400) == 0) {
        AddRandAntLion();
        return;
    }
    for (i = 0; i < LionIndex; i++) {
        switch (LionListM[i]) {
        case 0:
            x = LionListX[i];
            tile = GetMap(1, x, y = LionListY[i]);
            if (f_10F7_0731(1, tile) == 1 || IsThisFood(1, tile) == 1) {
                if (SRand1(0x200) == 0) {
                    d = SRand8();
                    for (k = 0; k < 8; k++, d = (d + 1) & 7) {
                        nx = x + Dx8[d] * 2;
                        if (IsClearTile(1, nx, ny = y + Dy8[d] * 2) == 1) {
                            SetMap(1, nx, ny, tile);
                            myBeginSound(0x1e, 0, 10);
                            break;
                        }
                    }
                    f_00DF_0164(0x26, 0, 0, 0, 6000L, 10);
                    LionListS[i] = 0x19;
                    LionListM[i] = 1;
                    LionListT[i] = 1;
                    SetAntLion(i);
                }
                continue;
            }
            for (count = 0, dir = 0; count < 2; ) {
                nx = Dx9[dir] + x;
                tile = LifeA[nx][ny = Dy9[dir] + y];
                if (tile == 0) {
                    count++;
                    dir = SRand1(8) + 1;
                    continue;
                }
                if (IsYellowAnt(tile) == 1) {
                    MoveMyLife(1, LionListX[i], LionListY[i], fd_50F6_04C2, fd_50F6_0496);
                    o22_39C7_0D21(2);
                } else {
                    if (SRand8() == 0)
                        f_00DF_0164(0x26, 0, 0, 0, 6000L, 10);
                    j = FindInAList(nx, ny);
                    if (j >= 0)
                        RemoveFromAList(j);
                    if ((tile & 0x80) == 0)
                        BAntsEaten++;
                    else
                        RAntsEaten++;
                }
                LionListS[i] = 0x32;
                LionListM[i] = 1;
                LionListT[i] = 1;
                SetAntLion(i);
                goto next;
            }
            continue;
        case 1:
            count = 0;
            for (dir = 0; dir < 8; dir++)
                if (LifeA[LionListX[i] + Dx8[dir]][LionListY[i] + Dy8[dir]] != 0)
                    count++;
            if (count >= 7) {
                PictStrnDialog(0, 0x2742, 0);
                KillAntLion(i);
                continue;
            }
            if (LionListT[i] < 4)
                LionListT[i]++;
            else if (LionListS[i] != 0) {
                LionListS[i]--;
                if (LionListS[i] & 1)
                    LionListT[i] = SRand1(4) + 3;
            } else {
                LionListM[i] = 2;
                LionListT[i] = 4;
            }
            SetAntLion(i);
            break;
        case 2:
            if (LionListT[i] != 0)
                LionListT[i]--;
            else {
                LionListM[i] = 0;
                AntsEatenByLions++;
                if (LionIndex < 9 && (AntsEatenByLions & 0xf) == 0xf)
                    AddRandAntLion();
            }
            SetAntLion(i);
            break;
        }
next:
        ;
    }
}

void far SetAntLion(int index)
{
    SetMap(1, LionListX[index], LionListY[index], LionListT[index] + 0x38);
}

int far FindInLionList(int x, int y)
{
    int i;

    for (i = LionIndex - 1; i >= 0; i--)
        if (LionListX[i] == x && LionListY[i] == y)
            break;
    return i;
}

void far KillAntLion(int index)
{
    int i;

    SetMap(1, LionListX[index], LionListY[index], 0x3f);
    if (LionIndex > 0) {
        LionIndex--;
        for (i = index; i < LionIndex; i++) {
            LionListX[i] = LionListX[i + 1];
            LionListY[i] = LionListY[i + 1];
            LionListT[i] = LionListT[i + 1];
            LionListM[i] = LionListM[i + 1];
            LionListS[i] = LionListS[i + 1];
        }
    }
}

void far InitPillar(void)
{
    int i;

    PillarState = 0;
    PillarX = 0;
    PillarY = 0;
    PillarSeg = 0;
    PillDir = 0;
    for (i = 0; i < 6; i++)
        PillarMap[i] = 0;
    if (TERRAINset == 0)
        InitSow();
}

void far DoPillar(void)
{
    int life;

    if (TERRAINset == 1)
        return;
    DoSow();
    if (PillarState == 0) {
        MakeAPill();
        PillarState = 1;
        PillarSeg = 4;
        return;
    }
    switch (PillDir) {
    case 0:
        life = PillGetLife(PillarX, PillarY - 1);
        break;
    case 1:
        life = PillGetLife(PillarX + 1, PillarY);
        break;
    case 2:
        life = PillGetLife(PillarX, PillarY + 1);
        break;
    case 3:
        life = PillGetLife(PillarX - 1, PillarY);
        break;
    }
    if (life) {
        if (IsPillDead() == 1) {
            PillarState = 0;
            MakePillFood();
        }
        return;
    }
    if (--PillarSeg == 4) {
        switch (PillDir) {
        case 0:
            ReplacePillarMap(PillarX, PillarSeg + PillarY + 1);
            break;
        case 1:
            ReplacePillarMap(PillarX - PillarSeg - 1, PillarY);
            break;
        case 2:
            ReplacePillarMap(PillarX, PillarY - PillarSeg - 1);
            break;
        case 3:
            ReplacePillarMap(PillarSeg + PillarX + 1, PillarY);
            break;
        }
    } else {
        switch (PillDir) {
        case 0:
            PlacePillTile(PillarX, PillarSeg + PillarY + 1, 0x6d);
            break;
        case 1:
            PlacePillTile(PillarX - PillarSeg - 1, PillarY, 0x69);
            break;
        case 2:
            PlacePillTile(PillarX, PillarY - PillarSeg - 1, 0x6d);
            break;
        case 3:
            PlacePillTile(PillarSeg + PillarX + 1, PillarY, 0x69);
            break;
        }
    }
    switch (PillDir) {
    case 0:
        PlacePillTile(PillarX, PillarSeg + PillarY, 0x6e);
        break;
    case 1:
        PlacePillTile(PillarX - PillarSeg, PillarY, 0x6a);
        break;
    case 2:
        PlacePillTile(PillarX, PillarY - PillarSeg, 0x6e);
        break;
    case 3:
        PlacePillTile(PillarSeg + PillarX, PillarY, 0x6a);
        break;
    }
    if (PillarSeg != 0)
        return;
    switch (PillDir) {
    case 0:
        PillarY--;
        break;
    case 1:
        PillarX++;
        break;
    case 2:
        PillarY++;
        break;
    case 3:
        PillarX--;
        break;
    }
    if (PillarX < -6 || PillarX > 0x86 || PillarY < -6 || PillarY > 0x45) {
        PillarState = 0;
        return;
    }
    StorePillarMap(PillarX, PillarY);
    switch (PillDir) {
    case 0:
        PlacePillTile(PillarX, PillarY, 0x6c);
        PlacePillTile(PillarX, PillarY + 1, 0x6d);
        break;
    case 1:
        PlacePillTile(PillarX, PillarY, 0x6b);
        PlacePillTile(PillarX - 1, PillarY, 0x69);
        break;
    case 2:
        PlacePillTile(PillarX, PillarY, 0x6f);
        PlacePillTile(PillarX, PillarY - 1, 0x6d);
        break;
    case 3:
        PlacePillTile(PillarX, PillarY, 0x68);
        PlacePillTile(PillarX + 1, PillarY, 0x69);
        break;
    }
    PillarSeg = 5;
}

void far StorePillarMap(int x, int y)
{
    if (f_10F7_2867(x, y) == 1) {
        if (PillDir & 1)
            PillarMap[x % 6] = MapA[x][y];
        else
            PillarMap[y % 6] = MapA[x][y];
    }
}

void far ReplacePillarMap(int x, int y)
{
    if (f_10F7_2867(x, y) == 1) {
        if (PillDir & 1)
            MapA[x][y] = PillarMap[x % 6];
        else
            MapA[x][y] = PillarMap[y % 6];
    }
}

void far MakeAPill(void)
{
    switch (PillDir = SRand1(4)) {
    case 0:
        PillarX = SRand1(128);
        PillarY = 63;
        StorePillarMap(PillarX, PillarY);
        PlacePillTile(PillarX, PillarY, 0x6c);
        break;
    case 1:
        PillarX = 0;
        PillarY = SRand1(64);
        StorePillarMap(PillarX, PillarY);
        PlacePillTile(PillarX, PillarY, 0x6b);
        break;
    case 2:
        PillarX = SRand1(128);
        PillarY = 0;
        StorePillarMap(PillarX, PillarY);
        PlacePillTile(PillarX, PillarY, 0x6f);
        break;
    case 3:
        PillarX = 127;
        PillarY = SRand1(64);
        StorePillarMap(PillarX, PillarY);
        PlacePillTile(PillarX, PillarY, 0x68);
        break;
    }
}

void far PlacePillTile(int x, int y, int value)
{
    if (f_10F7_2867(x, y) == 1)
        MapA[x][y] = value;
}

int far PillGetLife(int x, int y)
{
    if (f_10F7_2867(x, y) == 0)
        return 0;
    return LifeA[x][y];
}

int far IsPillDead(void)
{
    int x;
    int y;
    int count;

    count = 0;
    for (x = PillarX - 1; x < PillarX + 2; x++)
        for (y = PillarY - 1; y < PillarY + 2; y++)
            if (PillGetLife(x, y))
                count++;
    return count > 5;
}

void far MakePillFood(void)
{
    int i;

    switch (PillDir) {
    case 0:
        for (i = 0; i < 6; i++)
            PillFoodTile(PillarX, PillarY + i);
        break;
    case 1:
        for (i = 0; i < 6; i++)
            PillFoodTile(PillarX - i, PillarY);
        break;
    case 2:
        for (i = 0; i < 6; i++)
            PillFoodTile(PillarX, PillarY - i);
        break;
    case 3:
        for (i = 0; i < 6; i++)
            PillFoodTile(PillarX + i, PillarY);
        break;
    }
}

void far PillFoodTile(int x, int y)
{
    if (f_10F7_2867(x, y) == 1) {
        ReplacePillarMap(x, y);
        if (MapA[x][y] < 0x18)
            MapA[x][y] = 0x4b;
    }
}
