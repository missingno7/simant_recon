#include "dos_types.h"
#include "portable/whole_program/platform/dos_memory.h"
#include "portable/whole_program/platform/dos_io.h"
#include "portable/whole_program/platform/graphics_source_fields.h"
#include "native_owners.h"
#pragma pack(push, 2)
/* Root module, code frame 14EE: nest holes and tunnel digging. */

extern int16_t  SRand1(int16_t range);
extern int16_t  SRand8(void);
extern int16_t  IsClear3x3(int16_t plane, int16_t x, int16_t y);
extern int16_t  IsItDigable(int16_t colony, int16_t x, int16_t y);

extern int16_t  TERRAINset;
extern uint8_t  MapA[128][64];
extern uint8_t  HoleMapB[];
extern int16_t  fd_3D57_02AC[2];
extern int16_t  fd_3D57_02A4[2];
extern uint8_t  HoleMapR[];
extern int16_t  fd_3D57_02B0[2];
extern int16_t  fd_3D57_02A8[2];
extern uint8_t  MapB[64][64];
extern uint8_t  MapR[64][64];
extern char  Dy8[8];
extern char  Dx8[8];
uint8_t g_1BB2[8] = { 0x19, 0x1A, 0x1C, 0x1F, 0x1E, 0x1D, 0x1B, 0x18 };
extern int16_t  IsItDirt(int16_t value);
extern uint8_t  ExitMapB[64][64];
extern uint8_t  ExitMapR[64][64];

void  CreateNewHole(int16_t x, int16_t y);
void  MakeNewHoleB(int16_t x);
int16_t  CanBeHouseHole(int16_t v);
void  MakeNewHoleR(int16_t x);
void  HoleBorder(int16_t x, int16_t y);
void  DigTileB(int16_t x, int16_t y);
void  DigTileR(int16_t x, int16_t y);
void  SmoothEdgesB(int16_t x, int16_t y);
void  SmoothEdgesR(int16_t x, int16_t y);
int16_t  RIsItDirt(int16_t v);
void  f_14EE_0C9C(int16_t x, int16_t y);
void  f_14EE_0D71(int16_t x, int16_t y);

int16_t  DigMyNewHole(int16_t x, int16_t y)
{
    int16_t result;

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

void  CreateNewHole(int16_t x, int16_t y)
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

void  DigMyTile(int16_t colony, int16_t x, int16_t y)
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

void  MakeNewHoleB(int16_t x)
{
    int16_t i;
    int16_t v;
    int16_t y;
    int16_t start;

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

int16_t  CanBeHouseHole(int16_t v)
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

void  MakeNewHoleR(int16_t x)
{
    int16_t i;
    int16_t v;
    int16_t y;
    int16_t start;

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

void  HoleBorder(int16_t x, int16_t y)
{
    int16_t i;
    int16_t nx;
    int16_t ny;

    for (i = 0; i < 8; i++) {
        ny = Dy8[i] + y;
        nx = Dx8[i] + x;
        if (nx < 0 || nx > 127 || ny < 0 || ny > 63)
            continue;
        if (MapA[nx][ny] < 0x50)
            MapA[nx][ny] = g_1BB2[i];
    }
}

void  DigTileB(int16_t x, int16_t y)
{
    if (IsItDirt(MapB[x][y])) {
        MapB[x][y] = SRand8();
        native_state_fd_50F6_1068.signed_value += x;
        native_state_fd_50F6_1082.signed_value += y;
        native_state_fd_50F6_0224.signed_value++;
        if (native_state_fd_50F6_0224.signed_value > 0) {
            native_state_fd_50F6_10B2.signed_value = native_state_fd_50F6_1068.signed_value / native_state_fd_50F6_0224.signed_value;
            native_state_fd_50F6_10C0.signed_value = native_state_fd_50F6_1082.signed_value / native_state_fd_50F6_0224.signed_value;
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
    f_14EE_0C9C(x, y);
}

void  DigTileR(int16_t x, int16_t y)
{
    if (IsItDirt(MapR[x][y])) {
        MapR[x][y] = SRand8();
        native_state_fd_50F6_108E.signed_value += x;
        native_state_fd_50F6_10A2.signed_value += y;
        native_state_TilesDugR.signed_value++;
        if (native_state_TilesDugR.signed_value > 0) {
            native_state_fd_50F6_0200.signed_value = native_state_fd_50F6_108E.signed_value / native_state_TilesDugR.signed_value;
            native_state_fd_50F6_020E.signed_value = native_state_fd_50F6_10A2.signed_value / native_state_TilesDugR.signed_value;
        }
    }
    SmoothEdgesR(x, y - 1);
    SmoothEdgesR(x + 1, y);
    SmoothEdgesR(x, y + 1);
    SmoothEdgesR(x - 1, y);
    f_14EE_0D71(x, y);
}

int16_t  DigTileThemB(int16_t x, int16_t y)
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
    native_state_fd_50F6_1068.signed_value += x;
    native_state_fd_50F6_1082.signed_value += y;
    native_state_fd_50F6_0224.signed_value++;
    if (native_state_fd_50F6_0224.signed_value > 0) {
        native_state_fd_50F6_10B2.signed_value = native_state_fd_50F6_1068.signed_value / native_state_fd_50F6_0224.signed_value;
        native_state_fd_50F6_10C0.signed_value = native_state_fd_50F6_1082.signed_value / native_state_fd_50F6_0224.signed_value;
    }
    SmoothEdgesB(x, y - 1);
    SmoothEdgesB(x + 1, y);
    SmoothEdgesB(x, y + 1);
    SmoothEdgesB(x - 1, y);
    f_14EE_0C9C(x, y);
    return 1;
}

int16_t  DigTileThemR(int16_t x, int16_t y)
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
    native_state_fd_50F6_108E.signed_value += x;
    native_state_fd_50F6_10A2.signed_value += y;
    native_state_TilesDugR.signed_value++;
    if (native_state_TilesDugR.signed_value > 0) {
        native_state_fd_50F6_0200.signed_value = native_state_fd_50F6_108E.signed_value / native_state_TilesDugR.signed_value;
        native_state_fd_50F6_020E.signed_value = native_state_fd_50F6_10A2.signed_value / native_state_TilesDugR.signed_value;
    }
    SmoothEdgesR(x, y - 1);
    SmoothEdgesR(x + 1, y);
    SmoothEdgesR(x, y + 1);
    SmoothEdgesR(x - 1, y);
    f_14EE_0D71(x, y);
    return 1;
}

void  SmoothEdgesB(int16_t x, int16_t y)
{
    int16_t v;
    int16_t bits;

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


int16_t  RIsItDirt(int16_t v)
{
    if (v < 0x20)
        return 0;
    if (v > 0x2f && v < 0x4f)
        return 0;
    return 1;
}

void  SmoothEdgesR(int16_t x, int16_t y)
{
    int16_t v;
    int16_t bits;

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
void  f_14EE_0C9C(int16_t x, int16_t y)
{
    int16_t i;
    int16_t nx;
    int16_t ny;
    int16_t best;

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
void  f_14EE_0D71(int16_t x, int16_t y)
{
    int16_t i;
    int16_t nx;
    int16_t ny;
    int16_t best;

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


void  f_14EE_0E46(void)
{
    int16_t x;
    int16_t y;
    int16_t v;

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

#pragma pack(pop)
