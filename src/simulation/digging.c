/*
 * Creates nest entrances and digs or smooths tunnels. It updates both colony maps and fixes
 * their exit maps after terrain changes.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS: resident code; segment 14EE; complete original translation unit.
 * Windows: SIMONE, from recorded function pairs in the Windows symbol inventory.
 */

extern int far SRand1(int range);
extern int far SRand8(void);
extern int far IsClear3x3(int plane, int x, int y);
extern int far IsItDigable(int colony, int x, int y);

extern int far TERRAINset;
extern unsigned char far MapA[128][64];
extern unsigned char far HoleMapB[];
extern int far LastNewHoleB[2];
extern int far LastNewExitB[2];
extern unsigned char far HoleMapR[];
extern int far LastNewHoleR[2];
extern int far LastNewExitR[2];
extern unsigned char far MapB[64][64];
extern unsigned char far MapR[64][64];
extern char far Dy8[8];
extern char far Dx8[8];
/*
 * Surface hole-border tile values indexed by Dx8/Dy8 direction.
 */
unsigned char hole_border_tile_ids[8] = { 0x19, 0x1A, 0x1C, 0x1F, 0x1E, 0x1D, 0x1B, 0x18 };
extern int far IsItDirt(int value);
extern long far TileTotXB;
extern long far TileTotYB;
extern int far TilesDugB;
extern int far TileMassXB;
extern int far TileMassYB;
extern long far TileTotXR;
extern long far TileTotYR;
extern int far TilesDugR;
extern int far TileMassXR;
extern int far TileMassYR;
extern unsigned char far ExitMapB[64][64];
extern unsigned char far ExitMapR[64][64];

void far CreateNewHole(int x, int y);
void far MakeNewHoleB(int x);
int far CanBeHouseHole(int v);
void far MakeNewHoleR(int x);
void far HoleBorder(int x, int y);
void far DigTileB(int x, int y);
void far DigTileR(int x, int y);
void far SmoothEdgesB(int x, int y);
void far SmoothEdgesR(int x, int y);
int far RIsItDirt(int v);
void far FixExitMapB(int x, int y);
void far FixExitMapR(int x, int y);

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
        HoleBorder(x, y);
    }
    if (x < 0x40) {
        HoleMapB[y] = x;
        DigTileB(y, 1);
        LastNewHoleB[0] = x;
        LastNewHoleB[1] = y;
        LastNewExitB[0] = y;
        LastNewExitB[1] = 0;
    } else {
        HoleMapR[y] = x;
        DigTileR(y, 1);
        LastNewHoleR[0] = x;
        LastNewHoleR[1] = y;
        LastNewExitR[0] = y;
        LastNewExitR[1] = 0;
    }
}

void far DigMyTile(int colony, int x, int y)
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
                LastNewHoleB[0] = y;
                LastNewHoleB[1] = x;
                LastNewExitB[0] = x;
                LastNewExitB[1] = 0;
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
                LastNewHoleB[0] = y;
                LastNewHoleB[1] = x;
                LastNewExitB[0] = x;
                LastNewExitB[1] = 0;
                HoleBorder(y, x);
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
                LastNewHoleR[0] = y;
                LastNewHoleR[1] = x;
                LastNewExitR[0] = x;
                LastNewExitR[1] = 0;
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
                LastNewHoleR[0] = y;
                LastNewHoleR[1] = x;
                LastNewExitR[0] = x;
                LastNewExitR[1] = 0;
                HoleBorder(y, x);
                break;
            }
        }
        if (i == 34)
            return;
    }
    HoleMapR[x] = y;
    DigTileR(x, 1);
}

void far HoleBorder(int x, int y)
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
            MapA[nx][ny] = hole_border_tile_ids[i];
    }
}

void far DigTileB(int x, int y)
{
    if (IsItDirt(MapB[x][y])) {
        MapB[x][y] = SRand8();
        TileTotXB += x;
        TileTotYB += y;
        TilesDugB++;
        if (TilesDugB > 0) {
            TileMassXB = TileTotXB / TilesDugB;
            TileMassYB = TileTotYB / TilesDugB;
        }
        if (y > 0x35 && SRand1(64) == 0) {
            MapB[x][y] = 0x14;
            DigTileR(x, y);
            MapR[x][y] = 0x14;
        }
    }
    SmoothEdgesB(x, y - 1);
    SmoothEdgesB(x + 1, y);
    SmoothEdgesB(x, y + 1);
    SmoothEdgesB(x - 1, y);
    FixExitMapB(x, y);
}

void far DigTileR(int x, int y)
{
    if (IsItDirt(MapR[x][y])) {
        MapR[x][y] = SRand8();
        TileTotXR += x;
        TileTotYR += y;
        TilesDugR++;
        if (TilesDugR > 0) {
            TileMassXR = TileTotXR / TilesDugR;
            TileMassYR = TileTotYR / TilesDugR;
        }
    }
    SmoothEdgesR(x, y - 1);
    SmoothEdgesR(x + 1, y);
    SmoothEdgesR(x, y + 1);
    SmoothEdgesR(x - 1, y);
    FixExitMapR(x, y);
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
    TileTotXB += x;
    TileTotYB += y;
    TilesDugB++;
    if (TilesDugB > 0) {
        TileMassXB = TileTotXB / TilesDugB;
        TileMassYB = TileTotYB / TilesDugB;
    }
    SmoothEdgesB(x, y - 1);
    SmoothEdgesB(x + 1, y);
    SmoothEdgesB(x, y + 1);
    SmoothEdgesB(x - 1, y);
    FixExitMapB(x, y);
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
    TileTotXR += x;
    TileTotYR += y;
    TilesDugR++;
    if (TilesDugR > 0) {
        TileMassXR = TileTotXR / TilesDugR;
        TileMassYR = TileTotYR / TilesDugR;
    }
    SmoothEdgesR(x, y - 1);
    SmoothEdgesR(x + 1, y);
    SmoothEdgesR(x, y + 1);
    SmoothEdgesR(x - 1, y);
    FixExitMapR(x, y);
    return 1;
}

void far SmoothEdgesB(int x, int y)
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

void far SmoothEdgesR(int x, int y)
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


/* autosearch: exact after rules CSE-INLINE, STMT-SWAP */
void far FixExitMapB(int x, int y)
{
    int i;
    int nx;
    int ny;
    int best;

    if (y < 2) {
        if (MapB[x][y] == 0x18)
            ExitMapB[x][y] = 0xff;
        else
            ExitMapB[x][y] = 0xfe;
        return;
    }
    best = 0;
    for (i = 0; i < 8; i++) {
        nx = Dx8[i] + x;
        ny = Dy8[i] + y;
        if (nx < 0 || nx > 63 || ny < 0 || ny > 63)
            continue;
        if (ExitMapB[nx][ny] > best)
            best = ExitMapB[nx][ny];
    }
    if (best)
        ExitMapB[x][y] = best - 1;
    else
        ExitMapB[x][y] = 0;
}

/* autosearch: exact after rules CSE-INLINE, STMT-SWAP */
void far FixExitMapR(int x, int y)
{
    int i;
    int nx;
    int ny;
    int best;

    if (y < 2) {
        if (MapR[x][y] == 0x18)
            ExitMapR[x][y] = 0xff;
        else
            ExitMapR[x][y] = 0xfe;
        return;
    }
    best = 0;
    for (i = 0; i < 8; i++) {
        nx = Dx8[i] + x;
        ny = Dy8[i] + y;
        if (nx < 0 || nx > 63 || ny < 0 || ny > 63)
            continue;
        if (ExitMapR[nx][ny] > best)
            best = ExitMapR[nx][ny];
    }
    if (best)
        ExitMapR[x][y] = best - 1;
    else
        ExitMapR[x][y] = 0;
}


void far FloodNestB(void)
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
