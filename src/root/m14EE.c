/* Root module, code frame 14EE: nest holes and tunnel digging. */

extern int far SRand1(int range);
extern int far SRand8(void);
extern int far IsClear3x3(int plane, int x, int y);
extern int far IsItDigable(int colony, int x, int y);

extern int far TERRAINset;
extern unsigned char far MapA[128][64];
extern unsigned char far HoleMapB[];
extern int far fd_3D57_02AC[2];
extern int far fd_3D57_02A4[2];
extern unsigned char far HoleMapR[];
extern int far fd_3D57_02B0[2];
extern int far fd_3D57_02A8[2];
extern unsigned char far MapB[64][64];
extern unsigned char far MapR[64][64];
extern char far Dy8[8];
extern char far Dx8[8];
extern unsigned char near g_1BB2[8];
extern int far IsItDirt(int value);
extern long far fd_50F6_1068;
extern long far fd_50F6_1082;
extern int far fd_50F6_0224;
extern int far fd_50F6_10B2;
extern int far fd_50F6_10C0;
extern long far fd_50F6_108E;
extern long far fd_50F6_10A2;
extern int far TilesDugR;
extern int far fd_50F6_0200;
extern int far fd_50F6_020E;
extern unsigned char far ExitMapB[64][64];
extern unsigned char far ExitMapR[64][64];

void far CreateNewHole(int x, int y);
void far MakeNewHoleB(int x);
int far CanBeHouseHole(int v);
void far MakeNewHoleR(int x);
void far f_14EE_04B5(int x, int y);
void far DigTileB(int x, int y);
void far DigTileR(int x, int y);
void far f_14EE_09F1(int x, int y);
void far f_14EE_0B5A(int x, int y);
int far RIsItDirt(int v);
void far f_14EE_0C9C(int x, int y);
void far f_14EE_0D71(int x, int y);

int far DigMyNewHole(int x, int y)
{
    int result;

    result = 0;
    if (x >= 1 && x <= 127 && y >= 1 && y <= 63) {
        if (TERRAINset) {
            if (MapA[x][y] < 0xc8)
                result = 1;
        } else {
            result = IsClear3x3(1, x, y);
        }
        if (result == 1)
            CreateNewHole(x, y);
    }
    return result;
}

void far CreateNewHole(int x, int y)
{
    if (x < 1 || x >= 0x7f || y < 1 || y >= 0x3f)
        return;
    if (TERRAINset)
        MapA[x][y] = 0x59;
    else {
        MapA[x][y] = 0x50;
        f_14EE_04B5(x, y);
    }
    if (x < 0x40) {
        HoleMapB[y] = x;
        DigTileB(y, 1);
        fd_3D57_02AC[0] = x;
        fd_3D57_02AC[1] = y;
        fd_3D57_02A4[0] = y;
        fd_3D57_02A4[1] = 0;
    } else {
        HoleMapR[y] = x;
        DigTileR(y, 1);
        fd_3D57_02B0[0] = x;
        fd_3D57_02B0[1] = y;
        fd_3D57_02A8[0] = y;
        fd_3D57_02A8[1] = 0;
    }
}

void far f_14EE_0151(int colony, int x, int y)
{
    if (IsItDigable(colony, x, y)) {
        if (colony == 2) {
            if (y <= 1) {
                MapB[x][0] = 0x18;
                MakeNewHoleB(x);
                if (y != 1)
                    return;
            }
            DigTileB(x, y);
        } else {
            if (y <= 1) {
                MapR[x][0] = 0x18;
                MakeNewHoleR(x);
                if (y != 1)
                    return;
            }
            DigTileR(x, y);
        }
    }
}

void far MakeNewHoleB(int x)
{
    int i;
    int v;
    int y;
    int start;

    start = SRand1(31);
    if (TERRAINset) {
        for (i = 0; i < 34; i++) {
            y = (start + i) % 32 + 2;
            v = CanBeHouseHole(MapA[y][x]);
            if (v) {
                MapA[y][x] = v;
                fd_3D57_02AC[0] = y;
                fd_3D57_02AC[1] = x;
                fd_3D57_02A4[0] = x;
                fd_3D57_02A4[1] = 0;
                break;
            }
        }
        if (i == 34)
            return;
    } else {
        for (i = 0; i < 34; i++) {
            y = (i + start) % 32 + 2;
            if (IsClear3x3(1, y, x)) {
                MapA[y][x] = 0x50;
                fd_3D57_02AC[0] = y;
                fd_3D57_02AC[1] = x;
                fd_3D57_02A4[0] = x;
                fd_3D57_02A4[1] = 0;
                f_14EE_04B5(y, x);
                break;
            }
        }
        if (i == 34)
            return;
    }
    HoleMapB[x] = y;
    DigTileB(x, 1);
}

int far CanBeHouseHole(int v)
{
    if (v == 0)
        return 0x86;
    if (v == 2)
        return 0x8a;
    if (v == 3)
        return 0x8a;
    if (v >= 0x5e) {
        if (v < 0x62)
            return v + 0x22;
        if (v == 0x66)
            return 0x85;
        if (v == 0x68)
            return 0x84;
    }
    return 0;
}

void far MakeNewHoleR(int x)
{
    int i;
    int v;
    int y;
    int start;

    start = SRand1(31);
    if (TERRAINset) {
        for (i = 0; i < 34; i++) {
            y = 0x7e - (start + i) % 32;
            v = CanBeHouseHole(MapA[y][x]);
            if (v) {
                MapA[y][x] = v;
                fd_3D57_02B0[0] = y;
                fd_3D57_02B0[1] = x;
                fd_3D57_02A8[0] = x;
                fd_3D57_02A8[1] = 0;
                break;
            }
        }
        if (i == 34)
            return;
    } else {
        for (i = 0; i < 34; i++) {
            y = 0x7e - (i + start) % 32;
            if (IsClear3x3(1, y, x)) {
                MapA[y][x] = 0x50;
                fd_3D57_02B0[0] = y;
                fd_3D57_02B0[1] = x;
                fd_3D57_02A8[0] = x;
                fd_3D57_02A8[1] = 0;
                f_14EE_04B5(y, x);
                break;
            }
        }
        if (i == 34)
            return;
    }
    HoleMapR[x] = y;
    DigTileR(x, 1);
}

void far f_14EE_04B5(int x, int y)
{
    int i;
    int nx;
    int ny;

    for (i = 0; i < 8; i++) {
        ny = Dy8[i] + y;
        nx = Dx8[i] + x;
        if (nx < 0 || nx > 127 || ny < 0 || ny > 63)
            continue;
        if (MapA[nx][ny] < 0x50)
            MapA[nx][ny] = g_1BB2[i];
    }
}

void far DigTileB(int x, int y)
{
    if (IsItDirt(MapB[x][y])) {
        MapB[x][y] = SRand8();
        fd_50F6_1068 += x;
        fd_50F6_1082 += y;
        fd_50F6_0224++;
        if (fd_50F6_0224 > 0) {
            fd_50F6_10B2 = fd_50F6_1068 / fd_50F6_0224;
            fd_50F6_10C0 = fd_50F6_1082 / fd_50F6_0224;
        }
        if (y > 0x35 && SRand1(64) == 0) {
            MapB[x][y] = 0x14;
            DigTileR(x, y);
            MapR[x][y] = 0x14;
        }
    }
    f_14EE_09F1(x, y - 1);
    f_14EE_09F1(x + 1, y);
    f_14EE_09F1(x, y + 1);
    f_14EE_09F1(x - 1, y);
    f_14EE_0C9C(x, y);
}

void far DigTileR(int x, int y)
{
    if (IsItDirt(MapR[x][y])) {
        MapR[x][y] = SRand8();
        fd_50F6_108E += x;
        fd_50F6_10A2 += y;
        TilesDugR++;
        if (TilesDugR > 0) {
            fd_50F6_0200 = fd_50F6_108E / TilesDugR;
            fd_50F6_020E = fd_50F6_10A2 / TilesDugR;
        }
    }
    f_14EE_0B5A(x, y - 1);
    f_14EE_0B5A(x + 1, y);
    f_14EE_0B5A(x, y + 1);
    f_14EE_0B5A(x - 1, y);
    f_14EE_0D71(x, y);
}

int far DigTileThemB(int x, int y)
{
    if (y < 0x3f && !IsItDirt(MapB[x][y + 1]))
        return 0;
    if (y > 2 && !IsItDirt(MapB[x][y - 1]))
        return 0;
    if (x == 0 || x > 0x3e)
        return 0;
    if (y == 0) {
        MapB[x][y] = 0x18;
        MakeNewHoleB(x);
    } else
        MapB[x][y] = SRand8();
    fd_50F6_1068 += x;
    fd_50F6_1082 += y;
    fd_50F6_0224++;
    if (fd_50F6_0224 > 0) {
        fd_50F6_10B2 = fd_50F6_1068 / fd_50F6_0224;
        fd_50F6_10C0 = fd_50F6_1082 / fd_50F6_0224;
    }
    f_14EE_09F1(x, y - 1);
    f_14EE_09F1(x + 1, y);
    f_14EE_09F1(x, y + 1);
    f_14EE_09F1(x - 1, y);
    f_14EE_0C9C(x, y);
    return 1;
}

int far DigTileThemR(int x, int y)
{
    if (y < 0x3f) {
        if (!IsItDirt(MapR[x][y + 1]))
            return 0;
    }
    if (y > 2) {
        if (!IsItDirt(MapR[x][y - 1]))
            return 0;
    }
    if (x == 0)
        return 0;
    if (x > 0x3e)
        return 0;
    if (y == 0) {
        MapR[x][y] = 0x18;
        MakeNewHoleR(x);
    } else
        MapR[x][y] = SRand8();
    fd_50F6_108E += x;
    fd_50F6_10A2 += y;
    TilesDugR++;
    if (TilesDugR > 0) {
        fd_50F6_0200 = fd_50F6_108E / TilesDugR;
        fd_50F6_020E = fd_50F6_10A2 / TilesDugR;
    }
    f_14EE_0B5A(x, y - 1);
    f_14EE_0B5A(x + 1, y);
    f_14EE_0B5A(x, y + 1);
    f_14EE_0B5A(x - 1, y);
    f_14EE_0D71(x, y);
    return 1;
}

void far f_14EE_09F1(int x, int y)
{
    int v;
    int bits;

    if (x < 0 || x > 63 || y > 63)
        return;
    if (y == 0) {
        if (MapB[x][y] < 0x30)
            MapB[x][y] = 0x18;
        return;
    }
    v = MapB[x][y];
    if (v < 0x20)
        return;
    if (v > 0x2f && v < 0x4f)
        return;
    v = v > 0x4d ? 0x2f : 0;
    bits = 0;
    if (y < 2)
        bits = 1;
    else if (RIsItDirt(MapB[x][y - 1]))
        bits = 1;
    if (x > 0x3e)
        bits |= 2;
    else if (RIsItDirt(MapB[x + 1][y]))
        bits |= 2;
    if (y > 0x3e)
        bits |= 4;
    else if (RIsItDirt(MapB[x][y + 1]))
        bits |= 4;
    if (x < 1)
        bits |= 8;
    else if (RIsItDirt(MapB[x - 1][y]))
        bits |= 8;
    if (bits)
        MapB[x][y] = bits + v + 0x1f;
    else if (v == 0)
        MapB[x][y] = SRand8();
    else
        MapB[x][y] = 0x4e;
}


int far RIsItDirt(int v)
{
    if (v < 0x20)
        return 0;
    if (v > 0x2f && v < 0x4f)
        return 0;
    return 1;
}

void far f_14EE_0B5A(int x, int y)
{
    int v;
    int bits;

    if (x < 0 || x > 63 || y > 63)
        return;
    if (y == 0) {
        if (MapR[x][y] < 0x30)
            MapR[x][y] = 0x18;
        return;
    }
    v = MapR[x][y];
    if (v < 0x20)
        return;
    if (v > 0x2f && v < 0x4f)
        return;
    v = v > 0x4d ? 0x2f : 0;
    bits = 0;
    if (y < 2)
        bits = 1;
    else if (RIsItDirt(MapR[x][y - 1]))
        bits = 1;
    if (x > 0x3e)
        bits |= 2;
    else if (RIsItDirt(MapR[x + 1][y]))
        bits |= 2;
    if (y > 0x3e)
        bits |= 4;
    else if (RIsItDirt(MapR[x][y + 1]))
        bits |= 4;
    if (x < 1)
        bits |= 8;
    else if (RIsItDirt(MapR[x - 1][y]))
        bits |= 8;
    if (bits)
        MapR[x][y] = bits + v + 0x1f;
    else if (v == 0)
        MapR[x][y] = SRand8();
    else
        MapR[x][y] = 0x4e;
}


/* SCAFFOLD BEGIN: f_14EE_0C9C/f_14EE_0D71 (FixExitMapB/R) best drafts: target frame 10 with i [bp-4], best
   [bp-6], ny in SI, nx in AX, and the final ExitMap store hoists `mov ax,SEG; mov es,ax` above
   the if/else. With an extra `value` local (as below) frame, loop and registers match but best
   lands in [bp-8] and the final ES load is not hoisted (57 bytes differ); all 120 declaration
   orders give the same result; without `value` DI is used for nx (198 bytes differ) */
void far f_14EE_0C9C(int x, int y)
{
    int i;
    int nx;
    int ny;
    int best;
    int value;

    if (y < 2) {
        if (MapB[x][y] == 0x18)
            ExitMapB[x][y] = 0xff;
        else
            ExitMapB[x][y] = 0xfe;
        return;
    }
    best = 0;
    for (i = 0; i < 8; i++) {
        ny = Dy8[i] + y;
        nx = Dx8[i] + x;
        if (nx < 0 || nx > 63 || ny < 0 || ny > 63)
            continue;
        value = ExitMapB[nx][ny];
        if (value > best)
            best = value;
    }
    if (best)
        ExitMapB[x][y] = best - 1;
    else
        ExitMapB[x][y] = 0;
}

void far f_14EE_0D71(int x, int y)
{
    int i;
    int nx;
    int ny;
    int best;
    int value;

    if (y < 2) {
        if (MapR[x][y] == 0x18)
            ExitMapR[x][y] = 0xff;
        else
            ExitMapR[x][y] = 0xfe;
        return;
    }
    best = 0;
    for (i = 0; i < 8; i++) {
        ny = Dy8[i] + y;
        nx = Dx8[i] + x;
        if (nx < 0 || nx > 63 || ny < 0 || ny > 63)
            continue;
        value = ExitMapR[nx][ny];
        if (value > best)
            best = value;
    }
    if (best)
        ExitMapR[x][y] = best - 1;
    else
        ExitMapR[x][y] = 0;
}

/* SCAFFOLD END */

void far f_14EE_0E46(void)
{
    int x;
    int y;
    int v;

    for (x = 0; x < 64; x++) {
        for (y = 3; y < 64; y++) {
            v = MapB[x][y];
            if (v >= 0x20 && v <= 0x2d)
                MapB[x][y] += 0x31;
            else if (MapB[x][y] <= 0x13)
                MapB[x][y] = 0x50;
        }
    }
}
