#include "dos_types.h"
#include "portable/whole_program/platform/dos_memory.h"
#include "portable/whole_program/platform/dos_io.h"
#include "portable/whole_program/platform/graphics_source_fields.h"
#include "source_bounded_additive.h"
#include "native_owners.h"
#pragma pack(push, 2)
/* Root module, code frame 0AD9: sowing, ant lions and the pill bug (pillar). */

extern int16_t  SRand1(int16_t range);
extern uint8_t  MapA[128][64];
extern uint8_t  SowTab[8];
extern int16_t  SRand4(void);
extern char  Dy8[8];
extern char  Dx8[8];
extern int16_t  IsValidA(int16_t x, int16_t y);
extern uint8_t  LifeA[128][64];
extern int16_t  LionIndex;
extern int16_t  IsClear3x3(int16_t plane, int16_t x, int16_t y);
extern int16_t  IsClearTile(int16_t plane, int16_t x, int16_t y);
extern void  SetMap(int16_t plane, int16_t x, int16_t y, int16_t value);
extern int16_t  GetMap(int16_t plane, int16_t x, int16_t y);
extern int16_t  IsThisPebble(int16_t plane, int16_t tile);
extern int16_t  IsThisFood(int16_t category, int16_t tile);
extern char  Dy9[9];
extern char  Dx9[9];
extern int16_t  IsYellowAnt(int16_t value);
extern int16_t  fd_50F6_0496;
extern int16_t  fd_50F6_04C2;
extern void  MoveMyLife(int16_t plane, int16_t x, int16_t y, int16_t type, int16_t dir);
extern void  YellowDeath(int16_t code);
extern int16_t  SRand8(void);
extern void  f_00DF_0164(int16_t, int16_t, int16_t, int16_t, int32_t, int16_t);
extern int16_t  FindInAList(int16_t x, int16_t y);
extern void  RemoveFromAList(int16_t index);
extern void  myBeginSound(int16_t sound, int16_t a, int16_t b);
extern void  PictStrnDialog(int16_t a, int16_t b, int16_t c);
extern int16_t  PillarState;
extern int16_t  PillarX;
extern int16_t  PillarY;
extern int16_t  TERRAINset;

void  InitSow(void);
void  DoSow(void);
void  InitAntLions(int16_t count);
void  AddRandAntLion(void);
void  AddAntLion(int16_t x, int16_t y);
void  DoAntLions(void);
void  SetAntLion(int16_t index);
int16_t  FindInLionList(int16_t x, int16_t y);
void  KillAntLion(int16_t index);
void  InitPillar(void);
void  DoPillar(void);
void  StorePillarMap(int16_t x, int16_t y);
void  ReplacePillarMap(int16_t x, int16_t y);
void  MakeAPill(void);
void  PlacePillTile(int16_t x, int16_t y, int16_t value);
int16_t  PillGetLife(int16_t x, int16_t y);
int16_t  IsPillDead(void);
void  MakePillFood(void);
void  PillFoodTile(int16_t x, int16_t y);

void  InitSow(void)
{
    int16_t i;
    int16_t x;
    int16_t y;

    i = 2;
    while (i) {
        x = SRand1(128);
        y = SRand1(64);
        if (MapA[x][y] < 16) {
            native_state_SowX.signed_values[i] = x;
            native_state_SowY.signed_values[i] = y;
            native_state_SowDir.signed_values[i] = SRand1(8);
            native_state_SowSave.signed_values[i] = MapA[x][y];
            MapA[x][y] = SowTab[native_state_SowDir.signed_values[i]];
            i--;
        }
    }
}

void  DoSow(void)
{
    int16_t i;
    int16_t newX;
    int16_t newY;
    int16_t terrain;

    for (i = 0; i < 3; i++) {
        if (SRand4() == 0)
            continue;
        if (SRand4() == 0) {
            native_state_SowDir.signed_values[i] = (native_state_SowDir.signed_values[i] + SRand1(3) - 1) & 7;
            MapA[native_state_SowX.signed_values[i]][native_state_SowY.signed_values[i]] = SowTab[native_state_SowDir.signed_values[i]];
        }
        newX = native_state_SowX.signed_values[i] + Dx8[native_state_SowDir.signed_values[i]];
        if (!IsValidA(newX, newY = native_state_SowY.signed_values[i] + Dy8[native_state_SowDir.signed_values[i]]))
            continue;
        if (LifeA[newX][newY] != 0)
            continue;
        terrain = MapA[newX][newY];
        if (terrain >= 0x10)
            continue;
        MapA[native_state_SowX.signed_values[i]][native_state_SowY.signed_values[i]] = native_state_SowSave.signed_values[i];
        native_state_SowSave.signed_values[i] = terrain;
        MapA[newX][newY] = SowTab[native_state_SowDir.signed_values[i]];
        native_state_SowX.signed_values[i] = newX;
        native_state_SowY.signed_values[i] = newY;
    }
}

void  InitAntLions(int16_t count)
{
    int16_t i;

    LionIndex = 0;
    native_state_AntsEatenByLions.signed_value = 0;
    if (count > 10)
        count = 10;
    for (i = 0; i < count; i++)
        AddRandAntLion();
    native_state_InitialLions.signed_value = count;
}

void  AddRandAntLion(void)
{
    int16_t tries;
    int16_t x;
    int16_t y;

    for (tries = 0; tries < 200; tries++) {
        x = SRand1(0x40) + SRand1(0x41);
        y = SRand1(0x20) + SRand1(0x21);
        if (IsClear3x3(1, x, y) == 1 || (IsClearTile(1, x, y) == 1 && tries >= 100)) {
            AddAntLion(x, y);
            return;
        }
    }
}

static uint8_t lionRing[8] = {1, 2, 4, 7, 6, 5, 3, 0};

void  AddAntLion(int16_t x, int16_t y)
{
    int16_t i;
    int16_t lx;
    int16_t ly;

    SetMap(1, x, y, 0x38);
    for (i = 0; i < 8; i++) {
        lx = x + Dx8[i];
        if (IsClearTile(1, lx, ly = y + Dy8[i]) == 1)
            SetMap(1, lx, ly, lionRing[i] + 0x30);
    }
    native_state_LionListX.values[LionIndex] = x;
    native_state_LionListY.values[LionIndex] = y;
    native_state_LionListM.values[LionIndex] = 0;
    native_state_LionListS.values[LionIndex] = 0;
    native_state_LionListT.values[LionIndex] = 0;
    if (LionIndex < 9)
        LionIndex++;
}

void  DoAntLions(void)
{
    int16_t i;
    int16_t dir;
    int16_t count;
    int16_t ny;
    int16_t nx;
    int16_t y;
    int16_t x;
    int16_t tile;
    int16_t k;
    int16_t j;
    int16_t d;

    if (LionIndex == 0 && native_state_InitialLions.signed_value > 0 && SRand1(0x400) == 0) {
        AddRandAntLion();
        return;
    }
    for (i = 0; i < LionIndex; i++) {
        switch (native_state_LionListM.values[i]) {
        case 0:
            x = native_state_LionListX.values[i];
            tile = GetMap(1, x, y = native_state_LionListY.values[i]);
            if (IsThisPebble(1, tile) == 1 || IsThisFood(1, tile) == 1) {
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
                    native_state_LionListS.values[i] = 0x19;
                    native_state_LionListM.values[i] = 1;
                    native_state_LionListT.values[i] = 1;
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
                    MoveMyLife(1, native_state_LionListX.values[i], native_state_LionListY.values[i], fd_50F6_04C2, fd_50F6_0496);
                    YellowDeath(2);
                } else {
                    if (SRand8() == 0)
                        f_00DF_0164(0x26, 0, 0, 0, 6000L, 10);
                    j = FindInAList(nx, ny);
                    if (j >= 0)
                        RemoveFromAList(j);
                    if ((tile & 0x80) == 0)
                        native_state_BAntsEaten.signed_value++;
                    else
                        native_state_RAntsEaten.signed_value++;
                }
                native_state_LionListS.values[i] = 0x32;
                native_state_LionListM.values[i] = 1;
                native_state_LionListT.values[i] = 1;
                SetAntLion(i);
                goto next;
            }
            continue;
        case 1:
            count = 0;
            for (dir = 0; dir < 8; dir++)
                if (LifeA[native_state_LionListX.values[i] + Dx8[dir]][native_state_LionListY.values[i] + Dy8[dir]] != 0)
                    count++;
            if (count >= 7) {
                PictStrnDialog(0, 0x2742, 0);
                KillAntLion(i);
                continue;
            }
            if (native_state_LionListT.values[i] < 4)
                native_state_LionListT.values[i]++;
            else if (native_state_LionListS.values[i] != 0) {
                native_state_LionListS.values[i]--;
                if (native_state_LionListS.values[i] & 1)
                    native_state_LionListT.values[i] = SRand1(4) + 3;
            } else {
                native_state_LionListM.values[i] = 2;
                native_state_LionListT.values[i] = 4;
            }
            SetAntLion(i);
            break;
        case 2:
            if (native_state_LionListT.values[i] != 0)
                native_state_LionListT.values[i]--;
            else {
                native_state_LionListM.values[i] = 0;
                native_state_AntsEatenByLions.signed_value++;
                if (LionIndex < 9 && (native_state_AntsEatenByLions.signed_value & 0xf) == 0xf)
                    AddRandAntLion();
            }
            SetAntLion(i);
            break;
        }
next:
        ;
    }
}

void  SetAntLion(int16_t index)
{
    SetMap(1, native_state_LionListX.values[index], native_state_LionListY.values[index], native_state_LionListT.values[index] + 0x38);
}

int16_t  FindInLionList(int16_t x, int16_t y)
{
    int16_t i;

    for (i = LionIndex - 1; i >= 0; i--)
        if (native_state_LionListX.values[i] == x && native_state_LionListY.values[i] == y)
            break;
    return i;
}

void  KillAntLion(int16_t index)
{
    int16_t i;

    SetMap(1, native_state_LionListX.values[index], native_state_LionListY.values[index], 0x3f);
    if (LionIndex > 0) {
        LionIndex--;
        for (i = index; i < LionIndex; i++) {
            native_state_LionListX.values[i] = native_state_LionListX.values[i + 1];
            native_state_LionListY.values[i] = native_state_LionListY.values[i + 1];
            native_state_LionListT.values[i] = native_state_LionListT.values[i + 1];
            native_state_LionListM.values[i] = native_state_LionListM.values[i + 1];
            native_state_LionListS.values[i] = native_state_LionListS.values[i + 1];
        }
    }
}

void  InitPillar(void)
{
    int16_t i;

    PillarState = 0;
    PillarX = 0;
    PillarY = 0;
    native_state_PillarSeg.signed_value = 0;
    native_state_PillDir.signed_value = 0;
    for (i = 0; i < 6; i++)
        native_state_PillarMap.signed_values[i] = 0;
    if (TERRAINset == 0)
        InitSow();
}

void  DoPillar(void)
{
    int16_t life;

    if (TERRAINset == 1)
        return;
    DoSow();
    if (PillarState == 0) {
        MakeAPill();
        PillarState = 1;
        native_state_PillarSeg.signed_value = 4;
        return;
    }
    switch (native_state_PillDir.signed_value) {
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
    if (--native_state_PillarSeg.signed_value == 4) {
        switch (native_state_PillDir.signed_value) {
        case 0:
            ReplacePillarMap(PillarX, native_state_PillarSeg.signed_value + PillarY + 1);
            break;
        case 1:
            ReplacePillarMap(PillarX - native_state_PillarSeg.signed_value - 1, PillarY);
            break;
        case 2:
            ReplacePillarMap(PillarX, PillarY - native_state_PillarSeg.signed_value - 1);
            break;
        case 3:
            ReplacePillarMap(native_state_PillarSeg.signed_value + PillarX + 1, PillarY);
            break;
        }
    } else {
        switch (native_state_PillDir.signed_value) {
        case 0:
            PlacePillTile(PillarX, native_state_PillarSeg.signed_value + PillarY + 1, 0x6d);
            break;
        case 1:
            PlacePillTile(PillarX - native_state_PillarSeg.signed_value - 1, PillarY, 0x69);
            break;
        case 2:
            PlacePillTile(PillarX, PillarY - native_state_PillarSeg.signed_value - 1, 0x6d);
            break;
        case 3:
            PlacePillTile(native_state_PillarSeg.signed_value + PillarX + 1, PillarY, 0x69);
            break;
        }
    }
    switch (native_state_PillDir.signed_value) {
    case 0:
        PlacePillTile(PillarX, native_state_PillarSeg.signed_value + PillarY, 0x6e);
        break;
    case 1:
        PlacePillTile(PillarX - native_state_PillarSeg.signed_value, PillarY, 0x6a);
        break;
    case 2:
        PlacePillTile(PillarX, PillarY - native_state_PillarSeg.signed_value, 0x6e);
        break;
    case 3:
        PlacePillTile(native_state_PillarSeg.signed_value + PillarX, PillarY, 0x6a);
        break;
    }
    if (native_state_PillarSeg.signed_value != 0)
        return;
    switch (native_state_PillDir.signed_value) {
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
    switch (native_state_PillDir.signed_value) {
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
    native_state_PillarSeg.signed_value = 5;
}

void  StorePillarMap(int16_t x, int16_t y)
{
    if (IsValidA(x, y) == 1) {
        if (native_state_PillDir.signed_value & 1)
            native_state_PillarMap.signed_values[x % 6] = MapA[x][y];
        else
            native_state_PillarMap.signed_values[y % 6] = MapA[x][y];
    }
}

void  ReplacePillarMap(int16_t x, int16_t y)
{
    if (IsValidA(x, y) == 1) {
        if (native_state_PillDir.signed_value & 1)
            MapA[x][y] = native_state_PillarMap.signed_values[x % 6];
        else
            MapA[x][y] = native_state_PillarMap.signed_values[y % 6];
    }
}

void  MakeAPill(void)
{
    switch (native_state_PillDir.signed_value = SRand1(4)) {
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

void  PlacePillTile(int16_t x, int16_t y, int16_t value)
{
    if (IsValidA(x, y) == 1)
        MapA[x][y] = value;
}

int16_t  PillGetLife(int16_t x, int16_t y)
{
    if (IsValidA(x, y) == 0)
        return 0;
    return LifeA[x][y];
}

int16_t  IsPillDead(void)
{
    int16_t x;
    int16_t y;
    int16_t count;

    count = 0;
    for (x = PillarX - 1; x < PillarX + 2; x++)
        for (y = PillarY - 1; y < PillarY + 2; y++)
            if (PillGetLife(x, y))
                count++;
    return count > 5;
}

void  MakePillFood(void)
{
    int16_t i;

    switch (native_state_PillDir.signed_value) {
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

void  PillFoodTile(int16_t x, int16_t y)
{
    if (IsValidA(x, y) == 1) {
        ReplacePillarMap(x, y);
        if (MapA[x][y] < 0x18)
            MapA[x][y] = 0x4b;
    }
}

#pragma pack(pop)
