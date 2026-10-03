#include "dos_types.h"
#include "portable/whole_program/platform/dos_memory.h"
#include "portable/whole_program/platform/dos_io.h"
#include "portable/whole_program/platform/graphics_source_fields.h"
#pragma pack(push, 2)
/*
 * Overlay section S18, code frame 384C: house and yard map patches.
 * Same translation unit as the Win16 SIMONE_MODULE run MakeMap..AddRock3
 * (23 members, same order).  MakeMap picks the patch from the map cell;
 * cells above 37 get the random yard, the others one of the house floors.
 */

extern int16_t  TERRAINset;
extern int16_t  CurGndTileID;
extern void  OverlayTileSet(int16_t a, int16_t b);
extern void  InitAntLions(int16_t count);
extern void  InitPillar(void);
extern int16_t  DROPdir;
extern uint8_t  MapA[128][64];
extern int16_t  SRand1(int16_t range);
extern int16_t  SRand16(void);
extern int16_t  SRand4(void);
extern uint8_t  RT5[30][5];
extern uint8_t  RT3[18][3];

void  MakeMap(int16_t x, int16_t y);
void  MakeHousePatch(int16_t n);
void  FloorTiles(void);
void  CarpetFloorL(void);
void  MakeLint2(int16_t x1, int16_t x2, int16_t y1, int16_t y2);
void  CarpetFloorR(void);
void  MakeKitchenWall(void);
void  MakeSink(void);
void  TileFrame1(int16_t x1, int16_t x2, int16_t y1, int16_t y2);
void  TileFrame2(int16_t x1, int16_t x2, int16_t y1, int16_t y2);
void  MakeOutletV(int16_t x, int16_t y);
void  MakePlugV(int16_t x, int16_t y);
void  MakeOutletH(int16_t x, int16_t y);
void  MakePlugH(int16_t x, int16_t y);
void  MakeKnob(int16_t x, int16_t y);
void  MakePenny(int16_t x, int16_t y);
void  MakeClip(int16_t x, int16_t y);
void  FillMap(int16_t x1, int16_t x2, int16_t y1, int16_t y2, int16_t tile);
void  FillMapLegs(int16_t x1, int16_t x2, int16_t y1, int16_t y2, int16_t tile);
void  MakeYardPatch(void);
void  AddRocks(void);
void  AddRock5(int16_t x, int16_t y, int16_t shape);
void  AddRock3(int16_t x, int16_t y, int16_t shape);

void  MakeMap(int16_t x, int16_t y)
{
     int16_t n;

    n = (x << 4) + y;
    if (n > 0x25)
        MakeYardPatch();
    else
        MakeHousePatch(n);
}




void  MakeHousePatch(int16_t n)
{
    if (TERRAINset != 1) {
        CurGndTileID = 0x3e9;
        OverlayTileSet(0, 0x3e9);
    }
    InitAntLions(0);
    InitPillar();
    switch (n) {
    case 0:
        MakeKitchenWall();
        MakeSink();
        break;
    case 2: case 3: case 17: case 18: case 19: case 33: case 34: case 35:
        FloorTiles();
        break;
    case 4: case 10: case 11: case 13: case 14:
        CarpetFloorL();
        break;
    case 5:
        CarpetFloorL();
        FillMap(0x18, 0x46, 0x14, 0x3f, 2);
        MakePenny(0x28, 0x2d);
        break;
    case 6:
        CarpetFloorL();
        FillMap(0x18, 0x46, 0, 0x3f, 2);
        MakePenny(0x20, 0x14);
        MakeClip(0x26, 0x37);
        break;
    case 7:
        CarpetFloorL();
        FillMap(0x18, 0x46, 0, 0x14, 2);
        MakeClip(0x2a, 0x0a);
        break;
    case 8:
        CarpetFloorL();
        FillMapLegs(0x18, 0x36, 0x0f, 0x2d, 2);
        MakeClip(0x1c, 0x22);
        break;
    case 9:
        FillMap(0, 0x7f, 0, 0x3f, 3);
        DROPdir = 2;
        break;
    case 12:
        CarpetFloorL();
        FillMapLegs(0x2d, 0x5f, 8, 0x2e, 2);
        break;
    case 15:
        CarpetFloorL();
        FillMapLegs(0x32, 0x64, 0x0a, 0x2d, 2);
        MakePenny(0x4b, 0x22);
        break;
    case 20: case 21: case 22: case 23: case 24: case 25:
    case 26: case 27: case 28: case 29: case 30: case 31:
        CarpetFloorR();
        break;
    case 36: case 37:
        FillMap(0, 0x7f, 0, 0x3f, 0);
        DROPdir = 2;
        break;
    default:
        MakeKitchenWall();
        break;
    }
}


void  FloorTiles(void)
{
    int16_t x, y;

    for (x = 0; x < 128; x++)
        for (y = 0; y < 64; y++)
            if (((x >> 4) + (y >> 4)) & 1)
                MapA[x][y] = 0;
            else
                MapA[x][y] = 1;
    for (y = 0; y < 64; y += 16)
        for (x = 0; x < 128; x++)
            if ((x + y) & 0x10)
                MapA[x][y] = 0x60;
            else
                MapA[x][y] = 0x61;
    for (x = 0; x < 128; x += 16)
        for (y = 0; y < 64; y++)
            if (MapA[x][y] < 2) {
                if ((x + y) & 0x10)
                    MapA[x][y] = 0x5e;
                else
                    MapA[x][y] = 0x5f;
            } else {
                if ((x + y) & 0x10)
                    MapA[x][y] = 0x5d;
                else
                    MapA[x][y] = 0x5c;
            }
    DROPdir = 0;
}


void  CarpetFloorL(void)
{
    FillMap(0, 0x14, 0, 0x3f, 0x64);
    FillMap(0x15, 0x15, 0, 0x3f, 0x7a);
    FillMap(0x16, 0x17, 0, 0x3f, 0x7b);
    FillMap(0x17, 0x7f, 0, 0x3f, 3);
    MakeLint2(0x17, 0x7f, 0, 0x3f);
    MakeOutletH(2, 0x19);
    DROPdir = 1;
}


void  MakeLint2(int16_t x1, int16_t x2, int16_t y1, int16_t y2)
{
    int16_t x, y;

    for (x = x1; x <= x2; x++)
        for (y = y1; y <= y2; y++)
            if (SRand1(200) == 0)
                MapA[x][y] = SRand1(2) + 0x3e;
}

void  CarpetFloorR(void)
{
    FillMap(0, 0x69, 0, 0x3f, 3);
    MakeLint2(0, 0x69, 0, 0x3f);
    FillMap(0x6a, 0x6a, 0, 0x3f, 0x7c);
    FillMap(0x68, 0x69, 0, 0x3f, 0x7b);
    FillMap(0x6a, 0x7f, 0, 0x3f, 0x64);
    MakeOutletH(0x71, 0x23);
    DROPdir = 3;
}


void  MakeKitchenWall(void)
{
    int16_t x, y;

    FillMap(0, 0x7f, 0, 0x17, 0x62);
    FillMap(0, 0x7f, 0x18, 0x3f, 0);
    for (y = 0; y < 0x18; y += 8)
        for (x = 0; x < 128; x++)
            MapA[x][y] = 0x68;
    for (x = 0; x < 128; x += 8)
        for (y = 0; y < 0x18; y++)
            if (MapA[x][y] == 0x62)
                MapA[x][y] = 0x66;
            else
                MapA[x][y] = 0x67;
    for (x = 0; x < 128; x++)
        if (MapA[x][0x17] == 0x62)
            MapA[x][0x17] = 0x68;
        else
            MapA[x][0x17] = 0x69;
    MakeOutletV(0x24, 2);
    MakeOutletV(0x54, 2);
    DROPdir = 2;
}


void  MakeSink(void)
{
    FillMap(0x25, 0x5b, 0x1a, 0x38, 1);
    FillMap(0x29, 0x44, 0x21, 0x35, 0xc2);
    FillMap(0x2a, 0x44, 0x23, 0x35, 0xc1);
    TileFrame2(0x28, 0x44, 0x20, 0x35);
    FillMap(0x49, 0x58, 0x21, 0x35, 0xc2);
    FillMap(0x4a, 0x58, 0x23, 0x35, 0xc1);
    TileFrame2(0x48, 0x58, 0x20, 0x35);
    TileFrame1(0x25, 0x5b, 0x1a, 0x38);
    MakeKnob(0x2c, 0x1b);
    MakeKnob(0x3c, 0x1b);
    MapA[0x3e][0x1d] = 0x4d;
    MakeKnob(0x34, 0x1b);
    MakeKnob(0x34, 0x24);
    FillMap(0x34, 0x38, 0x1d, 0x26, 0x4e);
    FillMap(0x34, 0x34, 0x1d, 0x26, 0x43);
    FillMap(0x38, 0x38, 0x1d, 0x26, 0x44);
    MapA[0x34][0x28] = 0x45;
    MapA[0x38][0x28] = 0x48;
    FillMap(0x36, 0x38, 0x29, 0x2a, 0xc2);
    FillMap(0x39, 0x3a, 0x23, 0x2a, 0xc2);
}

void  TileFrame1(int16_t x1, int16_t x2, int16_t y1, int16_t y2)
{
    FillMap(x1, x2, y1, y1, 0x54);
    FillMap(x1, x2, y2, y2, 0x51);
    FillMap(x1, x1, y1, y2, 0x5a);
    FillMap(x2, x2, y1, y2, 0x5b);
    MapA[x1][y1] = 0x53;
    MapA[x2][y1] = 0x55;
    MapA[x1][y2] = 0x50;
    MapA[x2][y2] = 0x52;
}

void  TileFrame2(int16_t x1, int16_t x2, int16_t y1, int16_t y2)
{
    FillMap(x1, x2, y1, y1, 0x51);
    FillMap(x1, x2, y2, y2, 0x54);
    FillMap(x1, x1, y1, y2, 0x5b);
    FillMap(x2, x2, y1, y2, 0x5a);
    MapA[x1][y1] = 0x56;
    MapA[x2][y1] = 0x58;
    MapA[x1][y2] = 0x57;
    MapA[x2][y2] = 0x59;
}


void  MakeOutletV(int16_t x, int16_t y)
{
    FillMap(x, x + 8, y, y + 12, 0x63);
    TileFrame1(x, x + 8, y, y + 12);
    MakePlugV(x + 2, y + 2);
    MakePlugV(x + 2, y + 7);
    MapA[x + 4][y + 6] = 0x65;
}

static uint8_t plugV[4][5] = {
    0x6b, 0x6c, 0x6c, 0x6c, 0x6d,
    0x71, 0x78, 0x64, 0x78, 0x72,
    0x71, 0x79, 0x74, 0x79, 0x72,
    0x6e, 0x6f, 0x6f, 0x6f, 0x70
};

void  MakePlugV(int16_t x, int16_t y)
{
    int16_t i, j;

    for (i = 0; i < 5; i++)
        for (j = 0; j < 4; j++)
            MapA[x + i][y + j] = plugV[j][i];
}


void  MakeOutletH(int16_t x, int16_t y)
{
    FillMap(x, x + 12, y, y + 8, 0x63);
    TileFrame1(x, x + 12, y, y + 8);
    MakePlugH(x + 2, y + 2);
    MakePlugH(x + 7, y + 2);
    MapA[x + 6][y + 4] = 0x65;
}

static uint8_t plugH[5][4] = {
    0x6b, 0x6c, 0x6c, 0x6d,
    0x71, 0x76, 0x77, 0x72,
    0x71, 0x64, 0x64, 0x72,
    0x71, 0x76, 0x77, 0x72,
    0x6e, 0x6f, 0x6f, 0x70
};

void  MakePlugH(int16_t x, int16_t y)
{
    int16_t i, j;

    for (i = 0; i < 4; i++)
        for (j = 0; j < 5; j++)
            MapA[x + i][y + j] = plugH[j][i];
}

static uint8_t knob[5][5] = {
    0x40, 0x41, 0x41, 0x41, 0x42,
    0x43, 0x4e, 0x4e, 0x4e, 0x44,
    0x43, 0x4e, 0x4c, 0x4e, 0x44,
    0x43, 0x4e, 0x4e, 0x4e, 0x44,
    0x46, 0x47, 0x47, 0x47, 0x49
};

void  MakeKnob(int16_t x, int16_t y)
{
    int16_t i, j;

    for (i = 0; i < 5; i++)
        for (j = 0; j < 5; j++)
            MapA[x + i][y + j] = knob[j][i];
}

static uint8_t penny[3][3] = {
    0x28, 0x29, 0x2a,
    0x2b, 0x2c, 0x2d,
    0x2e, 0x2f, 0x30
};

void  MakePenny(int16_t x, int16_t y)
{
    int16_t i, j;

    for (i = 0; i < 3; i++)
        for (j = 0; j < 3; j++)
            MapA[x + i][y + j] = penny[j][i];
}

static uint8_t clip[3][3] = {
    0x00, 0x31, 0x32,
    0x33, 0x34, 0x35,
    0x36, 0x37, 0x00
};

void  MakeClip(int16_t x, int16_t y)
{
    int16_t i, j;

    for (i = 0; i < 3; i++)
        for (j = 0; j < 3; j++)
            if (clip[j][i])
                MapA[x + i][y + j] = clip[j][i];
}

void  FillMap(int16_t x1, int16_t x2, int16_t y1, int16_t y2, int16_t tile)
{
    int16_t x, y;

    for (x = x1; x <= x2; x++)
        for (y = y1; y <= y2; y++)
            MapA[x][y] = tile;
}

void  FillMapLegs(int16_t x1, int16_t x2, int16_t y1, int16_t y2, int16_t tile)
{
    int16_t x, y;

    FillMap(x1, x2, y1, y2, tile);
    for (x = x1; x <= x2; x++)
        for (y = y1; y <= y2; y++)
            if (SRand1(20) == 0)
                MapA[x][y] = SRand1(5) + 0x38;
    FillMap(x1, x1 + 3, y1, y1 + 3, 0xc0);
    FillMap(x2 - 3, x2, y1, y1 + 3, 0xc0);
    FillMap(x1, x1 + 3, y2 - 3, y2, 0xc0);
    FillMap(x2 - 3, x2, y2 - 3, y2, 0xc0);
}



void  MakeYardPatch(void)
{
    int16_t row, col, i, t;

    if (TERRAINset != 0) {
        CurGndTileID = 0x3e8;
        OverlayTileSet(0, 0x3e8);
    }
    for (row = 0; row < 128; row++)
        for (col = 0; col < 64; col++)
            MapA[row][col] = SRand16();
    AddRocks();
    InitAntLions(SRand4() + 1);
    InitPillar();
    for (i = 0; i < 20; i++) {
        row = SRand1(0x7d) + 1;
        col = SRand1(0x3d) + 1;
        if (MapA[row][col] < 0x18 && MapA[row + 1][col] < 0x18 &&
            MapA[row][col + 1] < 0x18 && MapA[row + 1][col + 1] < 0x18) {
            MapA[row][col] = 0x20;
            MapA[row + 1][col] = 0x21;
            MapA[row][col + 1] = 0x22;
            MapA[row + 1][col + 1] = 0x23;
        }
    }
    for (i = 0; i < 30; i++) {
        row = SRand1(0x7d) + 1;
        col = SRand1(0x3d) + 1;
        if (MapA[row][col] < 0x18 && MapA[row + 1][col] < 0x18) {
            t = (SRand1(2) + 0x12) << 1;
            MapA[row][col] = t;
            MapA[row + 1][col] = t + 1;
        }
    }
    for (i = 0; i < 100; i++) {
        row = SRand1(0x7d) + 1;
        col = SRand1(0x3d) + 1;
        if (MapA[row][col] < 0x18)
            MapA[row][col] = 0x28;
    }
    for (i = 0; i < 128; i++) {
        row = SRand1(0x7d) + 1;
        col = SRand1(0x3d) + 1;
        if (MapA[row][col] < 0x18)
            MapA[row][col] = 0x51;
    }
}


void  AddRocks(void)
{
    int16_t i, n;

    n = SRand1(3) + 2;
    for (i = 0; i < n; i++) {
        AddRock5(SRand1(0x7a), SRand1(0x3a), 0);
        AddRock5(SRand1(0x7a), SRand1(0x3a), 1);
        AddRock5(SRand1(0x7a), SRand1(0x3a), 2);
        AddRock5(SRand1(0x7a), SRand1(0x3a), 3);
        AddRock5(SRand1(0x7a), SRand1(0x3a), 4);
        AddRock5(SRand1(0x7a), SRand1(0x3a), 5);
    }
    for (i = 0; i < n * 2; i++) {
        AddRock3(SRand1(0x7c), SRand1(0x3c), 0);
        AddRock3(SRand1(0x7c), SRand1(0x3c), 1);
        AddRock3(SRand1(0x7c), SRand1(0x3c), 2);
        AddRock3(SRand1(0x7c), SRand1(0x3c), 3);
        AddRock3(SRand1(0x7c), SRand1(0x3c), 4);
        AddRock3(SRand1(0x7c), SRand1(0x3c), 5);
    }
}


void  AddRock5(int16_t x, int16_t y, int16_t shape)
{
    int16_t i, j, t, k;

    k = shape * 5;
    for (i = 0; i < 5; i++)
        for (j = 0; j < 5; j++)
            if (RT5[k + j][i] && MapA[x + i][y + j] > 0x10)
                return;
    for (i = 0; i < 5; i++)
        for (j = 0; j < 5; j++)
            if ((t = RT5[k + j][i]) != 0)
                MapA[x + i][y + j] = t;
}


void  AddRock3(int16_t x, int16_t y, int16_t shape)
{
    int16_t i, j, t, k;

    k = shape * 3;
    for (i = 0; i < 3; i++)
        for (j = 0; j < 3; j++)
            if (RT3[k + j][i] && MapA[x + i][y + j] > 0x10)
                return;
    for (i = 0; i < 3; i++)
        for (j = 0; j < 3; j++)
            if ((t = RT3[k + j][i]) != 0)
                MapA[x + i][y + j] = t;
}

#pragma pack(pop)
