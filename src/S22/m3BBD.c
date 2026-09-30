/* Overlay section S22, code frame 3BBD: experiment-mode map editor tools (Win16
 * ANTEDIT run processExp..SetSM, same 23 members in the same order).
 * Built /AL /Os /Oe /Og /Zd.  Declaration placement is part of the fingerprint
 * (MSC 6.00A identifier-count sensitivity): the ExpAddAnt prototype ahead of
 * processExp fixes its compare order, the IsItWall/WallNeighbors prototypes ahead
 * of IncFoodHere fix its compares.  DropWall/ExpDig walk local copies of their
 * start point (the copies decide the SI/DI assignment).  IncFoodHere keeps the
 * original dangling else.  With /Zd the one-line "} else v++;" puts the LEDATA
 * record break inside ConnectAll where the original has it. */

struct Pt {
    int x;
    int y;
};

extern int far fd_50F6_032E;
extern int far fd_50F6_09FC[2];
extern int far f_10F7_000E(int plane, int x, int y);
void far DoTool(int x, int y);
void far ExpAddAnt(int x, int y);
void far ReDrawMapEdit(int flags);
extern int far f_00F8_02AC(void);
extern void far f_1FD2_04D0(struct Pt far *pt);
extern int far fd_50F6_0A9C;
extern int _fastcall f_22BF_0A22(int win);
extern int far fd_50F6_10D2[2];
extern int far fd_50F6_3856;
extern int far fd_50F6_3858;
extern int far fd_50F6_110C[2];
extern int far fd_55B3_19BE;
extern int far fd_50F6_0508[2];
extern int far fd_55B3_19C0;
extern int far fd_50F6_104C;
extern unsigned char far fd_50F6_106C;

void far processExp(int x, int y)
{
    int nx;
    int ny;
    int count;
    struct Pt pt;

    if (fd_50F6_032E) {
        count = 0;
        fd_50F6_09FC[0] = x;
        fd_50F6_09FC[1] = y;
        if (f_10F7_000E(fd_50F6_032E, x, y))
            DoTool(x, y);
        ReDrawMapEdit(count);
        while (f_00F8_02AC() == 1) {
            f_1FD2_04D0(&pt);
            fd_50F6_0A9C++;
            if (f_22BF_0A22(0x100)) {
                nx = (pt.x - fd_50F6_10D2[0]) / fd_50F6_3856;
                ny = (pt.y - fd_50F6_10D2[1]) / fd_50F6_3858;
                if (fd_50F6_032E > 1)
                    nx -= 32;
            } else {
                nx = (pt.x - fd_50F6_110C[0]) / fd_55B3_19BE + fd_50F6_0508[0];
                ny = (pt.y - fd_50F6_110C[1]) / fd_55B3_19C0 + fd_50F6_0508[1];
            }
            if (nx != x || ny != y) {
                fd_50F6_09FC[0] = x;
                fd_50F6_09FC[1] = y;
                x = nx;
                y = ny;
                if (f_10F7_000E(fd_50F6_032E, x, y))
                    DoTool(x, y);
            }
            if (fd_50F6_104C >= 5 && f_10F7_000E(fd_50F6_032E, nx, ny)) {
                DoTool(nx, ny);
                fd_50F6_106C ^= 1;
            }
            count = (count + 1) & 0x3f;
            ReDrawMapEdit(count);
        }
    }
}

extern int far GetLife(int plane, int x, int y);
extern void far o05_35F5_025C(int x, int y, int plane);
void far DropWall(int x, int y, int tx, int ty);
void far ExpDig(int x, int y, int tx, int ty);
void far ExpAddFood(int x, int y);
void far ExpIncSmell(int x, int y);
void far ExpKillAnts(int x, int y);

void far DoTool(int x, int y)
{
    switch (fd_50F6_104C) {
    case 0:
        if (GetLife(fd_50F6_032E, x, y))
            o05_35F5_025C(x, y, fd_50F6_032E);
        break;
    case 1:
        if (fd_50F6_032E == 1)
            DropWall(fd_50F6_09FC[0], fd_50F6_09FC[1], x, y);
        break;
    case 2:
        ExpDig(fd_50F6_09FC[0], fd_50F6_09FC[1], x, y);
        break;
    case 3:
        ExpAddAnt(x, y);
        break;
    case 4:
        ExpAddFood(x, y);
        break;
    case 5:
        ExpIncSmell(x, y);
        break;
    case 6:
        ExpKillAnts(x, y);
        break;
    }
}

extern void far f_0250_0E9D(void);
extern void far f_0250_0ED2(void);
extern int _fastcall f_22BF_09B0(int win);
extern void far f_00F8_03A5(int mode);
extern void far o12_384C_100A(void);

void far ReDrawMapEdit(int flags)
{
    if (f_22BF_0A22(0)) {
        f_0250_0E9D();
        f_0250_0ED2();
        if (!f_22BF_09B0(0x100))
            return;
        if (flags & 3)
            return;
        f_00F8_03A5(1);
        o12_384C_100A();
        return;
    }

    f_00F8_03A5(1);
    o12_384C_100A();
    if (!f_22BF_09B0(0))
        return;
    if (flags & 3)
        return;
    f_0250_0E9D();
    f_0250_0ED2();
}

extern int far f_10F7_2867(int x, int y);
extern unsigned char far MapA[128][64];
extern int far SRand1(int range);
void far ConnectAll(int x, int y);
extern char far fd_3D57_07B6[];
extern unsigned char far LifeA[128][64];
extern void far myBeginSound(int sound, int a, int b);
extern int far GetDir(int x1, int y1, int x2, int y2);
extern signed char far fd_3D57_0010[];
extern signed char far fd_3D57_001A[];

void far DropWall(int fromX, int fromY, int tx, int ty)
{
    int x;
    int y;
    int dir;

    x = fromX;
    y = fromY;

    while (f_10F7_2867(x, y)) {
        if (*(unsigned char far *)0x417L & 8) {
            if (MapA[x][y] > 0x50 && MapA[x][y] < 0x68)
                MapA[x][y] = SRand1(16);
            ConnectAll(x, y);
        } else if (fd_3D57_07B6[1] == 0) {
            if (MapA[x][y] < 0x50 && LifeA[x][y] == 0)
                MapA[x][y] = 0x60;
            ConnectAll(x, y);
            myBeginSound(0x28, 0, 0x7e);
        } else {
            if (MapA[x][y] < 0x50 && LifeA[x][y] == 0)
                MapA[x][y] = SRand1(3) + 0x51;
            myBeginSound(10, SRand1(10000) + 2000, 0x7e);
        }
        dir = GetDir(x, y, tx, ty);
        if (fd_3D57_0010[dir])
            x += fd_3D57_0010[dir];
        else
            y += fd_3D57_001A[dir];
        if (dir == 0)
            break;
    }
}

extern int far DigMyNewHole(int x, int y);
extern void far * far * far fd_50F6_034C;
extern void far f_15D9_009C(void far *msg, long ticks, int mode);
extern int far IsItDigable(int plane, int x, int y);
extern void far DigTileB(int x, int y);
extern void far MakeNewHoleB(int x);
extern void far DigTileR(int x, int y);
extern void far MakeNewHoleR(int x);
extern unsigned char far LifeB[64][64];
void far ClearLifeB(int x, int y);
void far FillDirtB(int x, int y);
extern unsigned char far LifeR[64][64];
void far ClearLifeR(int x, int y);
void far FillDirtR(int x, int y);

void far ExpDig(int fromX, int fromY, int tx, int ty)
{
    int x;
    int y;
    int fill;
    int dir;


    fill = fd_3D57_07B6[2];
    if (*(unsigned char far *)0x417L & 8)
        fill ^= 1;
    x = fromX;
    y = fromY;
    do {
        if (fill == 0) {
            switch (fd_50F6_032E) {
            case 1:
                if (DigMyNewHole(x, y)) {
                    myBeginSound(0x13, 0, 0x7e);
                } else {
                    myBeginSound(1, 0, 0x7e);
                    f_15D9_009C(fd_50F6_034C[22], 120L, 1);
                }
                break;
            case 2:
                if (!IsItDigable(2, x, y) || y == 0)
                    break;
                DigTileB(x, y);
                if (y == 1)
                    MakeNewHoleB(x);
                myBeginSound(0x13, 0, 0x7e);
                break;
            case 3:
                if (!IsItDigable(3, x, y) || y == 0)
                    break;
                DigTileR(x, y);
                if (y == 1)
                    MakeNewHoleR(x);
                myBeginSound(0x13, 0, 0x7e);
                break;
            }
        } else {
            switch (fd_50F6_032E) {
            case 1:
                myBeginSound(1, 0, 0x7e);
                f_15D9_009C(fd_50F6_034C[21], 180L, 1);
                break;
            case 2:
                if (IsItDigable(2, x, y) || y == 0)
                    break;
                if (LifeB[x][y])
                    ClearLifeB(x, y);
                FillDirtB(x, y);
                myBeginSound(0x12, 0, 0x7e);
                break;
            case 3:
                if (IsItDigable(3, x, y) || y == 0)
                    break;
                if (LifeR[x][y])
                    ClearLifeR(x, y);
                FillDirtR(x, y);
                myBeginSound(0x12, 0, 0x7e);
                break;
            }
        }
        dir = GetDir(x, y, tx, ty);
        x += fd_3D57_0010[dir];
        y += fd_3D57_001A[dir];
    } while (dir != 0);
}

extern int far fd_50F6_0DA8;
extern unsigned char far fd_3E1D_BAEC[];
extern unsigned char far fd_3E1D_B50D[];
extern unsigned char far fd_3E1D_B702[];

void far ClearLifeB(int x, int y)
{
    int i;

    i = fd_50F6_0DA8;
    while (i) {
        --i;
        if (fd_3E1D_BAEC[i] != 0 && fd_3E1D_B50D[i] == x && fd_3E1D_B702[i] == y)
            fd_3E1D_BAEC[i] = 0;
    }
    LifeB[x][y] = 0;
}

extern int far fd_50F6_0EAA;
extern unsigned char far fd_3E1D_C4B5[];
extern unsigned char far fd_3E1D_BED6[];
extern unsigned char far fd_3E1D_C0CB[];

void far ClearLifeR(int x, int y)
{
    int i;

    i = fd_50F6_0EAA;
    while (i) {
        --i;
        if (fd_3E1D_C4B5[i] != 0 && fd_3E1D_BED6[i] == x && fd_3E1D_C0CB[i] == y)
            fd_3E1D_C4B5[i] = 0;
    }
    LifeR[x][y] = 0;
}

extern int far IsClearTile(int plane, int x, int y);
extern void far AddAntToAList(int x, int y, int type, int a, int b);
extern unsigned char far MapB[64][64];
extern void far AddAntToBList(int x, int y, int type, int a, int b);
extern unsigned char far MapR[64][64];
extern void far AddAntToRList(int x, int y, int type, int a, int b);

void far ExpAddAnt(int x, int y)
{
    int amt;

    amt = SRand1(8) + 16;
    if (fd_3D57_07B6[3] == 1)
        amt += 0x80;

    switch (fd_50F6_032E) {
    case 1:
        if (IsClearTile(1, x, y))
            AddAntToAList(x, y, amt, 2, 0);
        else
            return;
        break;
    case 2:
        if (y == 0)
            return;
        if (MapB[x][y] >= 0x1c)
            DigTileB(x, y);
        if (amt > 0x80)
            AddAntToBList(x, y, amt, 7, 0);
        else
            AddAntToBList(x, y, amt, 2, 0);
        break;
    case 3:
        if (y == 0)
            return;
        if (MapR[x][y] >= 0x1c)
            DigTileR(x, y);
        if (amt > 0x80)
            AddAntToRList(x, y, amt, 2, 0);
        else
            AddAntToRList(x, y, amt, 7, 0);
        break;
    }

    myBeginSound(0x1c, 0, 0x7e);
}

int far IncFoodHere(int x, int y);

void far ExpAddFood(int x, int y)
{
    int i;
    int fx;
    int fy;

    if (fd_3D57_07B6[4] == 0) {
        if (IncFoodHere(x, y))
            myBeginSound(0x1d, 0, 0x7e);
    } else {
        myBeginSound(0x20, 0, 0x7e);
        for (i = 0; i < 20; i++) {
            fx = SRand1(9) + x - 4;
            fy = SRand1(9) + y - 4;
            if (f_10F7_000E(fd_50F6_032E, fx, fy))
                IncFoodHere(fx, fy);
        }
    }
}

int far GetSM(int x, int y);
void far SetSM(int x, int y, int val);
void far SmoothMany(int x, int y);

void far ExpIncSmell(int x, int y)
{
    int sx;
    int sy;
    int v;

    if (fd_50F6_032E == 1) {
        sx = x >> 1;
        sy = y >> 1;
        v = GetSM(sx, sy);
        if (*(unsigned char far *)0x417L & 8)
            v -= 40;
        else
            v += 70;
        if (v < 0)
            v = 0;
        if (v > 255)
            v = 255;
        SetSM(sx, sy, v);
        SmoothMany(sx, sy);
        myBeginSound(0x1b, 0, 0x7e);
    }
}

extern int far FindInAList(int x, int y);
extern int far Tindex;
extern unsigned char far fd_3E1D_AD3B[];
extern void far DeadAntHere(int x, int y, int type);
extern int far fd_50F6_0F12;
extern int far fd_50F6_0F34;
extern void far f_0CDB_0DE0(void);
extern int far FindInLionList(int x, int y);
extern void far KillAntLion(int index);
extern int far FindInBList(int x, int y, int life);
extern int far FindInRList(int x, int y, int life);

void far ExpKillAnts(int x, int y)
{
    int n;
    int i;
    int kx;
    int ky;
    int v;

    n = fd_3D57_07B6[6] == 0 ? 8 : 1;
    for (i = 0; i < 8; i++) {
        if (n == 1) {
            kx = x;
            ky = y;
            myBeginSound(9, 0, 0x7e);
        } else {
            kx = SRand1(9) + x - 4;
            ky = SRand1(9) + y - 4;
            myBeginSound(9, SRand1(1000) + 0x278f, 0x7e);
        }
        if (f_10F7_000E(fd_50F6_032E, kx, ky)) {
            switch (fd_50F6_032E) {
            case 1:
                if (LifeA[kx][ky]) {
                    Tindex = FindInAList(kx, ky);
                    if (Tindex >= 0) {
                        DeadAntHere(kx, ky, fd_3E1D_AD3B[Tindex] & 0x80);
                        fd_3E1D_AD3B[Tindex] = 0;
                        LifeA[kx][ky] = 0;
                    }
                }
                if ((fd_50F6_0F12 >> 4) == kx && (fd_50F6_0F34 >> 4) == ky)
                    f_0CDB_0DE0();
                v = MapA[kx][ky];
                if (v >= 0x38 && v <= 0x3e)
                    KillAntLion(FindInLionList(kx, ky));
                break;
            case 2:
                v = LifeB[kx][ky];
                if (v) {
                    Tindex = FindInBList(kx, ky, v);
                    if (Tindex >= 0) {
                        fd_3E1D_BAEC[Tindex] = 0;
                        LifeB[kx][ky] = 0;
                    }
                }
                break;
            case 3:
                v = LifeR[kx][ky];
                if (v) {
                    Tindex = FindInRList(kx, ky, v);
                    if (Tindex >= 0) {
                        fd_3E1D_C4B5[Tindex] = 0;
                        LifeR[kx][ky] = 0;
                    }
                }
                break;
            }
        }
    }
}

extern int far GetMap(int plane, int x, int y);
extern int far fd_50F6_1040;
extern int far FoodB;
extern int far FoodR;
extern void far SetMap(int plane, int x, int y, int value);

void far ConnectWall(int x, int y);
int far IsItWall(int value);
int far WallNeighbors(int x, int y, int plane);

int far IncFoodHere(int x, int y)
{
    int base;
    int v;

    if (fd_50F6_032E == 1)
        base = 0x48;
    else
        base = 0x10;
    v = GetMap(fd_50F6_032E, x, y);
    if (*(unsigned char far *)0x417L & 8) {
        if (base > v)
            return 0;
        if (base + 3 < v)
            return 0;
        v = SRand1(8);
        if (fd_50F6_032E == 1)
            if (fd_50F6_1040 > 0)
                fd_50F6_1040--;
        else if (fd_50F6_032E == 2)
            if (FoodB > 0)
                FoodB--;
        else
            if (FoodR > 0)
                FoodR--;
    } else {
        if (base + 2 < v)
            return 0;
        if (base > v) {
            if (v < 0x18)
                v = base;
        } else v++;
        if (fd_50F6_032E == 1)
            fd_50F6_1040++;
        else if (fd_50F6_032E == 2)
            FoodB++;
        else
            FoodR++;
    }
    SetMap(fd_50F6_032E, x, y, v);
    return 1;
}


void far ConnectAll(int x, int y)
{
    ConnectWall(x, y);
    if (f_10F7_2867(x, y - 1) == 1)
        ConnectWall(x, y - 1);
    if (f_10F7_2867(x + 1, y) == 1)
        ConnectWall(x + 1, y);
    if (f_10F7_2867(x, y + 1) == 1)
        ConnectWall(x, y + 1);
    if (f_10F7_2867(x - 1, y) == 1)
        ConnectWall(x - 1, y);
}

static unsigned char wallShape[16] = {
    0x60, 0x64, 0x65, 0x66, 0x62, 0x61, 0x62, 0x61,
    0x63, 0x63, 0x60, 0x60, 0x67, 0x67, 0x67, 0x67
};

void far ConnectWall(int x, int y)
{
    if (IsItWall(MapA[x][y]))
        MapA[x][y] = wallShape[WallNeighbors(x, y, 1)];
}

int far WallNeighbors(int x, int y, int plane)
{
    int n;

    n = 0;
    if (IsItWall(GetMap(plane, x - 1, y)) == 1)
        n++;
    n <<= 1;
    if (IsItWall(GetMap(plane, x, y + 1)) == 1)
        n++;
    n <<= 1;
    if (IsItWall(GetMap(plane, x + 1, y)) == 1)
        n++;
    n <<= 1;
    if (IsItWall(GetMap(plane, x, y - 1)) == 1)
        n++;
    return n;
}

int far IsItWall(int value)
{
    return value >= 0x60 && value <= 0x67;
}

extern int far fd_50F6_0224;
extern long far fd_50F6_1068;
extern long far fd_50F6_1082;
extern void far f_14EE_09F1(int x, int y);
extern unsigned char far ExitMapB[64][64];

void far FillDirtB(int x, int y)
{
    MapB[x][y] = '.';
    LifeB[x][y] = 0;

    if (fd_50F6_0224 > 1) {
        fd_50F6_1068 -= x;
        if (fd_50F6_1068 < 0)
            fd_50F6_1068 = 0;
        fd_50F6_1082 -= y;
        if (fd_50F6_1082 < 0)
            fd_50F6_1082 = 0;
        --fd_50F6_0224;
    }

    f_14EE_09F1(x, y - 1);
    f_14EE_09F1(x + 1, y);
    f_14EE_09F1(x, y + 1);
    f_14EE_09F1(x - 1, y);

    ExitMapB[x][y] = 0;
}

extern int far fd_50F6_0232;
extern long far fd_50F6_108E;
extern long far fd_50F6_10A2;
extern void far f_14EE_0B5A(int x, int y);
extern unsigned char far ExitMapR[64][64];

void far FillDirtR(int x, int y)
{
    MapR[x][y] = '.';
    LifeR[x][y] = 0;

    if (fd_50F6_0232 > 1) {
        fd_50F6_108E -= x;
        if (fd_50F6_108E < 0)
            fd_50F6_108E = 0;
        fd_50F6_10A2 -= y;
        if (fd_50F6_10A2 < 0)
            fd_50F6_10A2 = 0;
        --fd_50F6_0232;
    }

    f_14EE_0B5A(x, y - 1);
    f_14EE_0B5A(x + 1, y);
    f_14EE_0B5A(x, y + 1);
    f_14EE_0B5A(x - 1, y);

    ExitMapR[x][y] = 0;
}

void far SmoothACell(int x, int y);

void far SmoothMany(int x, int y)
{
    SmoothACell(x, y);
    SmoothACell(x, y - 1);
    SmoothACell(x + 1, y);
    SmoothACell(x, y + 1);
    SmoothACell(x - 1, y);
    SmoothACell(x, y);
}

void far SmoothACell(int x, int y)
{
    int v;

    v = GetSM(x, y - 1);
    v += GetSM(x + 1, y);
    v += GetSM(x, y + 1);
    v += GetSM(x - 1, y);
    v = (v / 4 + GetSM(x, y)) / 2;
    SetSM(x, y, v);
}

int far IsValidSLoc(int x, int y)
{
    if (x >= 0 && x <= 63 && y >= 0 && y <= 31)
        return 1;
    return 0;
}

extern unsigned char far fd_3E1D_E09F[64][32];
extern unsigned char far fd_3E1D_E89F[64][32];
extern unsigned char far fd_3E1D_F09F[64][32];
extern unsigned char far fd_4DA7_0000[64][32];
extern unsigned char far fd_3E1D_D09F[64][32];

int far GetSM(int x, int y)
{
    int v;

    if (!IsValidSLoc(x, y))
        return -1;
    switch (fd_3D57_07B6[5]) {
    case 0:
        v = fd_3E1D_E09F[x][y];
        break;
    case 1:
        v = fd_3E1D_E89F[x][y];
        break;
    case 2:
        v = fd_3E1D_F09F[x][y];
        break;
    case 3:
        v = fd_4DA7_0000[x][y];
        break;
    case 4:
        v = fd_3E1D_D09F[x][y];
        break;
    }
    return v;
}

void far SetSM(int x, int y, int val)
{
    if (IsValidSLoc(x, y)) {
        if (val > 255)
            val = 255;
        switch (fd_3D57_07B6[5]) {
        case 0:
            fd_3E1D_E09F[x][y] = val;
            break;
        case 1:
            fd_3E1D_E89F[x][y] = val;
            break;
        case 2:
            fd_3E1D_F09F[x][y] = val;
            break;
        case 3:
            fd_4DA7_0000[x][y] = val;
            break;
        case 4:
            fd_3E1D_D09F[x][y] = val;
            break;
        }
    }
}
