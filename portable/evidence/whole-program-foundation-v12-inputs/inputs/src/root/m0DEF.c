/* Root module 0DEF: red colony initiator ant (Win16 unit MakeRedInitiator,
 * DoRedInitiator, GetNewRedTask, GetRedBestDirs; SIMANT1 segment order). */

extern int far fd_3D57_0C1C;
extern int far BpopT;
extern int far ListIndexA;
extern unsigned char far AlistT[];
extern unsigned char far AlistM[];
extern unsigned char far AlistS[];
extern int far fd_50F6_04A4;

void far f_0DEF_0000(void)
{
    int index;

    fd_3D57_0C1C = 0;
    if (BpopT >= 30) {
        index = ListIndexA;
        while (index > 0) {
            --index;
            if (AlistT[index] > 0x7f) {
                AlistT[index] = 0xb0;
                AlistM[index] = 0x13;
                AlistS[index] = 0;
                fd_50F6_04A4 = 0;
                fd_3D57_0C1C = 1;
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
void far f_0DEF_0233(void);
extern int far MePlane;
extern int far FuzLocX;
extern int far fd_50F6_04E0;
extern int far FuzLocY;
extern int far fd_50F6_04F2;
int far f_0DEF_031F(int plane, int x, int y, int a, int b);
extern int far SRand1(int range);
extern signed char far Dy8[];
extern signed char far Dx8[];
extern unsigned char far LifeA[][64];
extern int far IsYellowAnt(int life);
extern void far o25_3BA4_0DFB(int a, int index);
extern int far RandTurn(int dir);

void far f_0DEF_006B(register int i)
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
    switch (fd_50F6_04A4) {
    case 0:
        f_0DEF_0233();
        break;
    case 2:
        if (MePlane == 1) {
            fd_50F6_04E0 = FuzLocX;
            fd_50F6_04F2 = FuzLocY;
        }
        break;
    }
    dir = f_0DEF_031F(1, RedLocX, RedLocY, fd_50F6_04E0, fd_50F6_04F2);
    if (dir < 0) {
        if (SRand1(10) == 0)
            fd_50F6_04A4 = 0;
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
            o25_3BA4_0DFB(1, i);
        } else if (life > 0x7f) {
            AlistT[i] = RandTurn(t & 7) | caste;
            LifeA[x][y] = AlistT[i];
        }
    }
}

extern int far MeLocX;
extern int far fd_3D57_02BC[];
extern int far fd_50F6_0B12[];
extern int far fd_50F6_0AFA[];
extern void far UnRecruitRed(void);
extern void far RecruitRed(int count);

void far f_0DEF_0233(void)
{
    int redPopulation;

    UnRecruitRed();
    if (MePlane == 1) {
        if (SRand1(32) + 0x40 < MeLocX) {
            if (SRand1(10) < fd_50F6_0B12[5]) {
                fd_50F6_04A4 = 2;
                RecruitRed(fd_50F6_0B12[5]);
                return;
            }
        }
    }
    fd_50F6_04F2 = fd_3D57_02BC[1];
    fd_50F6_04E0 = fd_3D57_02BC[0];
    if (fd_50F6_04E0 > 0x1e) {
        fd_50F6_04E0 -= 5;
    } else {
        if (fd_50F6_04F2 < 0x14)
            fd_50F6_04F2 += 5;
        else if (fd_50F6_04F2 > 0x28)
            fd_50F6_04F2 -= 5;
    }
    redPopulation = fd_50F6_0AFA[1] + fd_50F6_0AFA[2];
    if (redPopulation < 0x14)
        RecruitRed(redPopulation >> 2);
    else
        RecruitRed(redPopulation >> 3);
    fd_50F6_04A4 = 1;
}

extern int far GetDis(int x1, int y1, int x2, int y2);
extern int far TileCanBeMovedOn(int plane, int x, int y, int fromPlane, int fromX, int fromY, int digging);
extern int far GetLife(int plane, int x, int y);
extern int far IsClearTile(int plane, int x, int y);

int far f_0DEF_031F(int plane, int x, int y, int a, int b)
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
