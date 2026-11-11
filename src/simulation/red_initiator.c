/*
 * Creates and advances the red colony initiator ant. It selects new tasks and the best
 * directions for that ant.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS: resident code; segment 0DEF; complete original translation unit.
 * Windows: SIMANT1, from recorded function pairs in the Windows symbol inventory.
 */

extern int far RedInitOn;
extern int far BpopT;
extern int far ListIndexA;
extern unsigned char far AlistT[];
extern unsigned char far AlistM[];
extern unsigned char far AlistS[];
extern int far RedTask;

void far MakeRedInitiator(void)
{
    int index;

    RedInitOn = 0;
    if (BpopT >= 30) {
        index = ListIndexA;
        while (index > 0) {
            --index;
            if (AlistT[index] > 0x7f) {
                AlistT[index] = 0xb0;
                AlistM[index] = 0x13;
                AlistS[index] = 0;
                RedTask = 0;
                RedInitOn = 1;
                return;
            }
        }
    }
}

extern unsigned char far AlistY[];
extern unsigned char far AlistX[];
extern int far RedLocX;
extern int far RedLocY;
extern int far RedPlane;
void far GetNewRedTask(void);
extern int far MePlane;
extern int far FuzLocX;
extern int far RedDestX;
extern int far FuzLocY;
extern int far RedDestY;
int far GetRedBestDirs(int plane, int x, int y, int a, int b);
extern int far SRand1(int range);
extern signed char far Dy8[];
extern signed char far Dx8[];
extern unsigned char far LifeA[][64];
extern int far IsYellowAnt(int life);
extern void far YellowFight(int a, int index);
extern int far RandTurn(int dir);

void far DoRedInitiator(register int i)
{
    int y;
    int x;
    int t;
    int caste;
    int dir;
    int nx;
    int ny;
    int life;

    x = AlistX[i];
    y = AlistY[i];
    t = AlistT[i];
    caste = t & 0xf8;
    RedLocX = x;
    RedLocY = y;
    RedPlane = 1;
    switch (RedTask) {
    case 0:
        GetNewRedTask();
        break;
    case 2:
        if (MePlane == 1) {
            RedDestX = FuzLocX;
            RedDestY = FuzLocY;
        }
        break;
    }
    dir = GetRedBestDirs(1, RedLocX, RedLocY, RedDestX, RedDestY);
    if (dir < 0) {
        if (SRand1(10) == 0)
            RedTask = 0;
        LifeA[x][y] = AlistT[i];
    } else {
        nx = Dx8[dir] + x;
        ny = Dy8[dir] + y;
        if ((life = LifeA[nx][ny]) == 0) {
            AlistT[i] = LifeA[nx][ny] = caste | dir;
            LifeA[x][y] = 0;
            AlistX[i] = nx;
            AlistY[i] = ny;
        } else if (IsYellowAnt(life) == 1) {
            YellowFight(1, i);
        } else if (life > 0x7f) {
            AlistT[i] = RandTurn(t & 7) | caste;
            LifeA[x][y] = AlistT[i];
        }
    }
}

extern int far MeLocX;
extern int far LastFoodDrop[];
extern int far ModePopB[];
extern int far CastePopR[];
extern void far UnRecruitRed(void);
extern void far RecruitRed(int count);

void far GetNewRedTask(void)
{
    int redPopulation;

    UnRecruitRed();
    if (MePlane == 1) {
        if (SRand1(32) + 0x40 < MeLocX) {
            if (SRand1(10) < ModePopB[5]) {
                RedTask = 2;
                RecruitRed(ModePopB[5]);
                return;
            }
        }
    }
    RedDestY = LastFoodDrop[1];
    RedDestX = LastFoodDrop[0];
    if (RedDestX > 0x1e) {
        RedDestX -= 5;
    } else {
        if (RedDestY < 0x14)
            RedDestY += 5;
        else if (RedDestY > 0x28)
            RedDestY -= 5;
    }
    redPopulation = CastePopR[1] + CastePopR[2];
    if (redPopulation < 0x14)
        RecruitRed(redPopulation >> 2);
    else
        RecruitRed(redPopulation >> 3);
    RedTask = 1;
}

extern int far GetDis(int x1, int y1, int x2, int y2);
extern int far TileCanBeMovedOn(int plane, int x, int y, int fromPlane, int fromX, int fromY, int digging);
extern int far GetLife(int plane, int x, int y);
extern int far IsClearTile(int plane, int x, int y);

int far GetRedBestDirs(int plane, int x, int y, int a, int b)
{
    int best;
    int fallback;
    int threshold;
    int dir;
    int nx;
    int ny;
    int dis;

    best = -1;
    threshold = GetDis(x, y, a, b);
    if (threshold <= 0)
        goto done;
    fallback = -2;
    for (dir = 0; dir < 8; dir++) {
        nx = Dx8[dir] + x;
        ny = Dy8[dir] + y;
        if (TileCanBeMovedOn(plane, nx, ny, plane, a, b, 0) == 1) {
            dis = GetDis(nx, ny, a, b);
            if (dis < threshold) {
                if (GetLife(plane, nx, ny) > 0 || IsClearTile(plane, nx, ny) != 1)
                    fallback = dir;
                else
                    best = dir;
                threshold = dis;
            }
        }
    }
    if (best < 0)
        best = fallback;
done:
    return best;
}
