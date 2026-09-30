/* Root module, code frame 0BE8: ant counts, water, eggs, directions. */

extern int far SRand1(int range);
extern int far SRand2(void);
extern int far RRand(int range);
extern void far f_0E2E_000A(void);
extern void far f_0EC1_037B(int y);
extern void far f_0EC1_03D9(int y);
extern void far ZapEuMapAt(int plane, int x, int y);

extern void far myBeginSound(int a, int b, int c);

extern void far f_00DF_00B1(int id, int arg);
extern void far o14_384C_0B6A(int a, int b, int c);

extern int far fd_50F6_0AFA[6];
extern int far fd_50F6_0AEC[6];
extern int far fd_50F6_0EB6[32];
extern int far ListIndexA;
extern unsigned char far AlistT[];
extern int far ListIndexB;
extern unsigned char far BlistT[];
extern int far ListIndexR;
extern unsigned char far RlistT[];
extern int far fd_50F6_0A06;
extern int far fd_50F6_04E2;
extern int far fd_50F6_04C2;
extern int far fd_50F6_0354;
extern int far fd_50F6_0EAC;
extern int far fd_50F6_0376;
extern int far fd_50F6_0366;
extern int far fd_50F6_0400;
extern int far fd_50F6_07CA[2];
extern unsigned char far fd_3D57_0184[][16];
extern int far BpopT;
extern int far RpopT;
extern int far fd_50F6_0352;
extern int far TERRAINset;
extern int far fd_3D57_0C1E;
extern int far fd_50F6_0242;
extern unsigned char far fd_50F6_02C0[];
extern unsigned char far fd_50F6_0256[];
extern unsigned char far MapA[128][64];
extern unsigned char far PherMapA[64][32];
extern unsigned char far fd_3E1D_D89F[64][32];
extern unsigned char far PherMapBN[64][32];
extern unsigned char far PherMapBT[64][32];
extern unsigned char far PherMapRN[64][32];
extern unsigned char far PherMapRT[64][32];
extern unsigned char far MapB[64][64];
extern int far SRand16(void);
extern int far SRand8(void);
extern int far fd_50F6_1040;
extern int far FoodB;
extern int far FoodR;
extern int far fd_50F6_0F3A;
extern unsigned char near g_1B9A[];
extern unsigned char near g_1B9E[];
extern unsigned char far LifeB[64][64];
extern char far Dy8[8];
extern char far Dx8[8];
extern unsigned char far ExitMapB[64][64];
extern unsigned char far ExitMapR[64][64];
extern long far fd_50F6_0214;
extern int far fd_50F6_0228;
extern long far TickCount(void);
extern unsigned char far LifeR[64][64];
extern void far DigTileB(int x, int y);
extern void far DigTileR(int x, int y);
extern void far AddAntToBList(int x, int y, int life, int state, int dir);
extern void far AddAntToRList(int x, int y, int life, int state, int dir);
extern unsigned char far MapR[64][64];

void far f_0BE8_0002(void);
void far PlaceDrop(int i);
void far CountUpdate(void);
void far AddWater(int y);
void far DropWater(int y);
void far f_0BE8_08BD(int x, int y);
int far InNestBounds(int x, int y);

/* SCAFFOLD BEGIN: unrecovered f_0BE8_0002 kept in place for CONST order */
/* f_0BE8_0002 (CountAnts?): best draft, 13 bytes differ: operand order of the
   commutative far-memory sums (AEC[1], AFA[1], AFA[2], totals) depends on the
   compiler's symbol-table state (number/names of earlier declarations), not on
   source order; see REPORT.md (ORD-1 observation). */
void far f_0BE8_0002(void)
{
    int i;
    int n;
    int v;

    fd_50F6_0AFA[0] = 0;
    fd_50F6_0AEC[0] = 0;
    for (i = 0; i < 32; i++)
        fd_50F6_0EB6[i] = 0;
    for (n = ListIndexA; n > 0; ) {
        v = AlistT[--n];
        if (v)
            fd_50F6_0EB6[v >> 3]++;
    }
    for (n = ListIndexB; n > 0; ) {
        v = BlistT[--n];
        if (v)
            fd_50F6_0EB6[v >> 3]++;
    }
    for (n = ListIndexR; n > 0; ) {
        v = RlistT[--n];
        if (v)
            fd_50F6_0EB6[v >> 3]++;
    }
    if (fd_50F6_0A06 == 0) {
        if (fd_50F6_04E2 == 0)
            fd_50F6_0EB6[fd_50F6_04C2 >> 3]++;
        else
            fd_50F6_0EB6[(fd_50F6_04C2 | 0x80) >> 3]++;
    }
    fd_50F6_0AEC[0] = fd_50F6_0EB6[0];
    fd_50F6_0AEC[1] = fd_50F6_0EB6[1] + fd_50F6_0EB6[2] + fd_50F6_0EB6[3] + fd_50F6_0EB6[5];
    fd_50F6_0AEC[2] = fd_50F6_0EB6[6] + fd_50F6_0EB6[7] + fd_50F6_0EB6[9];
    fd_50F6_0AEC[3] = fd_50F6_0EB6[4];
    fd_50F6_0AEC[4] = fd_50F6_0EB6[8];
    if (fd_50F6_0AEC[5] && fd_50F6_0EB6[12] == 0 && fd_50F6_0354 == 0) {
        f_00DF_00B1(0x2b0c, 0x7e);
        o14_384C_0B6A(0, 0x271a, 1);
        if (fd_50F6_0EAC <= 1) {
            o14_384C_0B6A(0, 0x271b, 1);
            fd_50F6_0376 = 1;
            fd_50F6_0366 = 0;
        }
    }
    fd_50F6_0AEC[5] = fd_50F6_0EB6[12];
    fd_50F6_0AFA[0] = fd_50F6_0EB6[16];
    fd_50F6_0AFA[1] = fd_50F6_0EB6[18] + fd_50F6_0EB6[19] + fd_50F6_0EB6[21] + fd_50F6_0EB6[17];
    fd_50F6_0AFA[2] = fd_50F6_0EB6[23] + fd_50F6_0EB6[22] + fd_50F6_0EB6[25];
    fd_50F6_0AFA[3] = fd_50F6_0EB6[20];
    fd_50F6_0AFA[4] = fd_50F6_0EB6[24];
    if (fd_50F6_0AFA[5] && fd_50F6_0EB6[28] == 0 && fd_50F6_0354 == 0) {
        f_00DF_00B1(0x2b0d, 0x7e);
        o14_384C_0B6A(0, 0x271c, 1);
        if (fd_50F6_0EAC <= 1) {
            o14_384C_0B6A(0, 0x271d, 1);
            fd_50F6_0376 = 1;
            fd_50F6_0366 = 1;
        }
        if (fd_50F6_0EAC == 2 && fd_50F6_0400 == 1 && fd_50F6_07CA[0] == 0xb && fd_50F6_07CA[1] == 8)
            fd_3D57_0184[SRand1(6)][0] = 0x14;
    }
    BpopT = fd_50F6_0AEC[3] + fd_50F6_0AEC[1] + fd_50F6_0AEC[2] + fd_50F6_0AEC[4] + fd_50F6_0AEC[5];
    fd_50F6_0AFA[5] = fd_50F6_0EB6[28];
    RpopT = fd_50F6_0AFA[5] + fd_50F6_0AFA[4] + fd_50F6_0AFA[1] + fd_50F6_0AFA[3] + fd_50F6_0AFA[2];
    fd_50F6_0354 = 0;
}

/* SCAFFOLD END */

void far FullCount(void)
{
    f_0BE8_0002();
    CountUpdate();
}

void far CountUpdate(void)
{
    f_0E2E_000A();
}

void far f_0BE8_03AC(void)
{
    int i;
    int x;
    int y;
    int v;

    if (fd_50F6_0352 && !TERRAINset) {
        if (SRand1(50) == 0)
            myBeginSound(0x29, 0, 0x40);
        fd_3D57_0C1E = 1;
        if (SRand1(10) == 0 && fd_50F6_0242 > 4) {
            --fd_50F6_0242;
            AddWater(fd_50F6_0242);
        }
        for (i = 0; i < 100; i++) {
            x = fd_50F6_0256[i];
            y = fd_50F6_02C0[i];
            v = MapA[x][y];
            if (v >= 0x74 && v < 0x77)
                MapA[x][y]++;
            else {
                if (v == 0x77)
                    MapA[x][y] = SRand1(14);
                PlaceDrop(i);
            }
        }
    } else if (!TERRAINset) {
        if (fd_3D57_0C1E == 1) {
            fd_3D57_0C1E = 0;
            for (i = 0; i < 100; i++) {
                x = fd_50F6_0256[i];
                y = fd_50F6_02C0[i];
                v = MapA[x][y];
                if (v >= 0x74 && v <= 0x77)
                    MapA[x][y] = SRand1(14);
            }
        }
        if (fd_50F6_0242 < 0x40 && SRand1(10) == 0) {
            DropWater(fd_50F6_0242);
            fd_50F6_0242++;
        }
    }
}

void far PlaceDrop(int i)
{
    int x;
    int y;

    x = RRand(128);
    y = RRand(64);
    fd_50F6_0256[i] = x;
    fd_50F6_02C0[i] = y;
    if (MapA[x][y] < 0xe) {
        MapA[x][y] = 0x74;
        x >>= 1;
        y >>= 1;
        fd_3E1D_D89F[x][y] = PherMapA[x][y] = 0;
        if (PherMapBN[x][y] >= 0x14)
            PherMapBN[x][y] -= 0x14;
        else
            PherMapBN[x][y] = 0;
        PherMapBT[x][y] = 0;
        if (PherMapRN[x][y] >= 0x14)
            PherMapRN[x][y] -= 0x14;
        else
            PherMapRN[x][y] = 0;
        PherMapRT[x][y] = 0;
    }
}

void far InitWater(void)
{
    int i;

    for (i = 0; i < 100; ++i)
        PlaceDrop(i);
}

void far AddWater(int y)
{
    int x;
    int v;
    int t;

    f_0EC1_037B(y);
    f_0EC1_03D9(y);
    for (x = 0; x < 64; x++) {
        v = MapB[x][y];
        if (v < 0x20)
            t = 0x4e;
        else
            t = v + 0x2f;
        MapB[x][y] = t;
        v = MapR[x][y];
        if (v < 0x20)
            t = 0x4e;
        else
            t = v + 0x2f;
        MapR[x][y] = t;
        ZapEuMapAt(2, x, y);
        ZapEuMapAt(3, x, y);
    }
}

void far DropWater(int y)
{
    int x;
    int v;
    int t;

    for (x = 0; x < 64; x++) {
        v = MapB[x][y];
        if (v == 0x4e)
            t = SRand1(8);
        else
            t = v - 0x2f;
        MapB[x][y] = t;
        v = MapR[x][y];
        if (v == 0x4e)
            t = SRand1(8);
        else
            t = v - 0x2f;
        MapR[x][y] = t;
        ZapEuMapAt(2, x, y);
        ZapEuMapAt(3, x, y);
    }
}

void far f_0BE8_0798(int x, int y)
{
    int v;

    v = MapA[x][y];
    if (!TERRAINset) {
        if (v == 0x48)
            MapA[x][y] = SRand16();
        else
            MapA[x][y]--;
    } else {
        if (v % 4 == 0)
            MapA[x][y] = (v - 0x18) >> 2;
        else
            MapA[x][y]--;
    }
    if (fd_50F6_1040 > 0)
        fd_50F6_1040--;
}

int far f_0BE8_0812(int x, int y)
{
    int v;

    v = MapA[x][y];
    if (TERRAINset == 1) {
        if (v < 4) {
            MapA[x][y] = (v + 6) << 2;
            fd_50F6_1040++;
            return 1;
        }
        if (v >= 8 && v < 0x18) {
            v = (v - 8) >> 2;
            MapA[x][y] = (v + 6) << 2;
            fd_50F6_1040++;
            return 1;
        }
        if (v >= 0x18 && v < 0x27) {
            MapA[x][y]++;
            fd_50F6_1040++;
            return 1;
        }
        if (v < 0x40) {
            f_0BE8_08BD(x, y);
            return 1;
        }
    } else {
        if (v < 0x4b) {
            if (v >= 0x48) {
                MapA[x][y]++;
                fd_50F6_1040++;
                return 1;
            }
            MapA[x][y] = 0x48;
            fd_50F6_1040++;
            return 1;
        }
    }
    return 0;
}

void far f_0BE8_08BD(int a, int b)
{
    int v;
    int go;
    int x;
    int y;

    go = 1;
    x = a;
    y = b;
    while (go) {
        v = MapA[x][y];
        if (v < 4) {
            MapA[x][y] = (v + 6) << 2;
            fd_50F6_1040++;
            go = 0;
        }
        x += g_1B9A[fd_50F6_0F3A];
        y += g_1B9E[fd_50F6_0F3A];
        if (x < 0 || x > 0x7f)
            go = 0;
        if (y < 0 || y > 0x3f)
            go = 0;
    }
}

void far f_0BE8_094B(int x, int y)
{
    int v;
    int flag;

    flag = 0;
    v = MapB[x][y];
    if (v == 0x10) {
        MapB[x][y] = SRand8();
        flag = 1;
    } else if (v >= 0x11 && v <= 0x13) {
        MapB[x][y]--;
        flag = 1;
    }
    if (flag == 1 && FoodB > 0)
        FoodB--;
}

void far f_0BE8_09D3(int x, int y)
{
    int v;
    int flag;

    flag = 0;
    v = MapR[x][y];
    if (v == 0x10) {
        MapR[x][y] = SRand8();
        flag = 1;
    } else if (v >= 0x11 && v <= 0x13) {
        MapR[x][y]--;
        flag = 1;
    }
    if (flag == 1 && FoodR > 0)
        FoodR--;
}


void far PlaceEggB(int x, int y, int life)
{
    if (ListIndexB < 500 && InNestBounds(x, y)) {
        DigTileB(x, y);
        AddAntToBList(x, y, life, 8, 0);
        LifeB[x][y] = life;
    }
}

void far PlaceEggR(int x, int y, int life)
{
    if (ListIndexR < 500 && InNestBounds(x, y)) {
        DigTileR(x, y);
        AddAntToRList(x, y, life, 8, 0);
        LifeR[x][y] = life;
    }
}

int far GetDir(int x1, int y1, int x2, int y2)
{
    int dx;
    int dy;

    dy = y2 - y1;
    dx = x2 - x1;
    if (dx == 0) {
        if (dy == 0)
            return 0;
        if (dy < 0)
            return 1;
        return 5;
    }
    if (dx > 0) {
        if (dy < 0)
            return 2;
        if (dy == 0)
            return 3;
        return 4;
    }
    if (dy > 0)
        return 6;
    if (dy == 0)
        return 7;
    return 8;
}

long far GetDis(int x1, int y1, int x2, int y2)
{
    return (long)(y2 - y1) * (y2 - y1) + (long)(x2 - x1) * (x2 - x1);
}

int far InNestBounds(int x, int y)
{
    if (x >= 0 && x <= 0x3f && y >= 1 && y <= 0x3f)
        return 1;
    return 0;
}

int far IsItDirt(int value)
{
    if (value >= 0x20 && value <= 0x2e)
        return 1;
    return 0;
}

int far GetExitDirB(int x, int y, int dir)
{
    int back;
    int best;
    int bestValue;
    int i;
    int nx;
    int ny;
    int value;

    if (y == 1) {
        if (MapB[x][0] == 0x18)
            return 1;
        return SRand2() * 4 + 3;
    }
    back = dir ^ 4;
    best = 0;
    bestValue = 0;
    for (i = 0; i < 8; i++) {
        ny = Dy8[i] + y;
        nx = Dx8[i] + x;
        if (nx < 0 || nx > 63 || ny < 0 || ny > 63)
            continue;
        value = ExitMapB[nx][ny];
        if (value > bestValue && back != i) {
            bestValue = value;
            best = i + 1;
        }
    }
    return best;
}

int far GetExitDirR(int x, int y, int dir)
{
    int back;
    int best;
    int bestValue;
    int i;
    int nx;
    int ny;
    int value;

    if (y == 1) {
        if (MapR[x][0] == 0x18)
            return 1;
        return SRand2() * 4 + 3;
    }
    back = dir ^ 4;
    best = 0;
    bestValue = 0;
    for (i = 0; i < 8; i++) {
        ny = Dy8[i] + y;
        nx = Dx8[i] + x;
        if (nx < 0 || nx > 63 || ny < 0 || ny > 63)
            continue;
        value = ExitMapR[nx][ny];
        if (value > bestValue && back != i) {
            bestValue = value;
            best = i + 1;
        }
    }
    return best;
}

/* SCAFFOLD BEGIN: f_0BE8_0D67/f_0BE8_0E0F (GetEnterDirB/R) best drafts: target keeps ny in memory [bp-2] and
   value in DI, back/bestValue/best at [bp-6]/[bp-8]/[bp-A]. MSC gives DI to ny and puts
   value in memory (ny and value have disjoint live ranges and share storage); a struct
   {best,bestValue,back} fixes the slot order but not the DI choice. Tried: declaration orders,
   block-scoped locals, register keyword (ignored under /Og), nested-if and || forms,
   value-free expression form, 0..17 padding declarations */
int far f_0BE8_0D67(int x, int y, int dir)
{
    int back;
    int best;
    int bestValue;
    int i;
    int nx;
    int ny;
    int value;

    back = dir ^ 4;
    best = -1;
    bestValue = ExitMapB[x][y];
    for (i = 0; i < 8; i++) {
        if (back == i)
            continue;
        ny = Dy8[i] + y;
        nx = Dx8[i] + x;
        if (nx < 0 || nx > 63 || ny < 0 || ny > 63)
            continue;
        value = ExitMapB[nx][ny];
        if (value == 0)
            continue;
        if (bestValue < value)
            continue;
        if (bestValue <= value && SRand2() == 0)
            continue;
        bestValue = value;
        best = i;
    }
    return best;
}

int far f_0BE8_0E0F(int x, int y, int dir)
{
    int back;
    int best;
    int bestValue;
    int i;
    int nx;
    int ny;
    int value;

    back = dir ^ 4;
    best = -1;
    bestValue = ExitMapR[x][y];
    for (i = 0; i < 8; i++) {
        if (back == i)
            continue;
        ny = Dy8[i] + y;
        nx = Dx8[i] + x;
        if (nx < 0 || nx > 63 || ny < 0 || ny > 63)
            continue;
        value = ExitMapR[nx][ny];
        if (value == 0)
            continue;
        if (bestValue < value)
            continue;
        if (bestValue <= value && SRand2() == 0)
            continue;
        bestValue = value;
        best = i;
    }
    return best;
}

/* SCAFFOLD END */

void far TryAntTheme(void)
{
    if (TickCount() >= fd_50F6_0214 + 0x1c20) {
        fd_50F6_0214 = TickCount();
        if (++fd_50F6_0228 > 2)
            fd_50F6_0228 = 0;
        f_00DF_00B1(fd_50F6_0228 + 0x2713, 0x7e);
    }
}


