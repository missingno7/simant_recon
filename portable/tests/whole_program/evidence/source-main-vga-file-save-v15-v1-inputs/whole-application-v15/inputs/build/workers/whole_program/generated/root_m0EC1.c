#include "dos_types.h"
#include "portable/whole_program/platform/dos_memory.h"
#include "portable/whole_program/platform/dos_io.h"
#include "portable/whole_program/platform/graphics_source_fields.h"
#include "source_bounded_additive.h"
#pragma pack(push, 2)
/* Root module, code frame 0EC1: ant lists (A = surface, B = black nest, R = red nest). */

extern int16_t  ListIndexA;
extern uint8_t  AlistT[];
extern uint8_t  AlistX[];
extern uint8_t  AlistY[];
extern uint8_t  AlistM[];
extern uint8_t  AlistS[];
extern uint8_t  BlistT[];
extern uint8_t  BlistX[];
extern uint8_t  BlistY[];
extern uint8_t  BlistM[];
extern uint8_t  BlistS[];
extern uint8_t  RlistT[];
extern uint8_t  RlistX[];
extern uint8_t  RlistY[];
extern uint8_t  RlistM[];
extern uint8_t  RlistS[];
extern uint8_t  LifeA[128][64];
extern void  BlockMove(uint8_t  *src, uint8_t  *dst, int32_t count);
extern char  Dy8[8];
extern char  Dx8[8];
extern int16_t  IsValidA(int16_t x, int16_t y);
extern uint8_t  MapA[128][64];
extern uint8_t  LifeB[64][64];
extern uint8_t  LifeR[64][64];
extern int16_t  IsYellowAnt(int16_t value);

void  CompactListA(void)
{
    int16_t i;
    int16_t shift;
    int16_t j;

    shift = 0;
    for (i = 0; i < ListIndexA; i++) {
        if (AlistT[i]) {
            if (shift) {
                j = shift + i;
                AlistT[j] = AlistT[i];
                AlistX[j] = AlistX[i];
                AlistY[j] = AlistY[i];
                AlistM[j] = AlistM[i];
                AlistS[j] = AlistS[i];
            }
        } else
            shift--;
    }
    ListIndexA += shift;
}

void  CompactListB(void)
{
    int16_t i;
    int16_t shift;
    int16_t j;

    shift = 0;
    for (i = 0; i < native_state_ListIndexB.signed_value; i++) {
        if (BlistT[i]) {
            if (shift) {
                j = shift + i;
                BlistT[j] = BlistT[i];
                BlistX[j] = BlistX[i];
                BlistY[j] = BlistY[i];
                BlistM[j] = BlistM[i];
                BlistS[j] = BlistS[i];
            }
        } else
            shift--;
    }
    native_state_ListIndexB.signed_value += shift;
}

void  CompactListR(void)
{
    int16_t i;
    int16_t shift;
    int16_t j;

    shift = 0;
    for (i = 0; i < native_state_ListIndexR.signed_value; i++) {
        if (RlistT[i]) {
            if (shift) {
                j = shift + i;
                RlistT[j] = RlistT[i];
                RlistX[j] = RlistX[i];
                RlistY[j] = RlistY[i];
                RlistM[j] = RlistM[i];
                RlistS[j] = RlistS[i];
            }
        } else
            shift--;
    }
    native_state_ListIndexR.signed_value += shift;
}

void  RemoveFromAList(int16_t index)
{
    int32_t count;
    int16_t next;

    LifeA[AlistX[index]][AlistY[index]] = 0;
    if (ListIndexA > 0)
        ListIndexA--;
    count = ListIndexA - index;
    next = index + 1;
    BlockMove(&AlistX[next], &AlistX[index], count);
    BlockMove(&AlistY[next], &AlistY[index], count);
    BlockMove(&AlistM[next], &AlistM[index], count);
    BlockMove(&AlistT[next], &AlistT[index], count);
    BlockMove(&AlistS[next], &AlistS[index], count);
}

int16_t  FindInAList(int16_t x, int16_t y)
{
    int16_t i;

    i = ListIndexA;
    while (i > 0) {
        i--;
        if (AlistX[i] == x && AlistY[i] == y && AlistT[i] != 0)
            return i;
    }
    return -1;
}

int16_t  FindInBList(int16_t x, int16_t y, int16_t t)
{
    int16_t i;

    i = native_state_ListIndexB.signed_value;
    while (i > 0) {
        i--;
        if (BlistX[i] == x && BlistY[i] == y && BlistT[i] == t)
            return i;
    }
    return -1;
}

int16_t  FindInRList(int16_t x, int16_t y, int16_t t)
{
    int16_t i;

    i = native_state_ListIndexR.signed_value;
    while (i > 0) {
        i--;
        if (RlistX[i] == x && RlistY[i] == y && RlistT[i] == t)
            return i;
    }
    return -1;
}

void  DrownBList(int16_t y)
{
    int16_t i;
    int16_t caste;

    i = native_state_ListIndexB.signed_value;
    while (i > 0) {
        i--;
        if (BlistY[i] != y)
            continue;
        if (BlistT[i] == 0)
            continue;
        caste = (BlistT[i] & 0x78) >> 3;
        if (caste <= 0 || caste >= 12)
            continue;
        BlistM[i] = 0x11;
    }
}

void  DrownRList(int16_t y)
{
    int16_t i;
    int16_t caste;

    i = native_state_ListIndexR.signed_value;
    while (i > 0) {
        i--;
        if (RlistY[i] != y)
            continue;
        if (RlistT[i] == 0)
            continue;
        caste = (RlistT[i] & 0x78) >> 3;
        if (caste <= 0 || caste >= 12)
            continue;
        RlistM[i] = 0x11;
    }
}

int16_t  ExitHole(int16_t x, int16_t y, int16_t type, int16_t mode, int16_t stat)
{
    int16_t i;
    int16_t nx;
    int16_t ny;

    for (i = 0; i < 8; i++) {
        nx = x + Dx8[i];
        if (IsValidA(nx, ny = y + Dy8[i]) == 1 && MapA[nx][ny] < 0x50)
            break;
    }
    if (i == 8)
        return 0;
    AlistX[ListIndexA] = nx;
    AlistY[ListIndexA] = ny;
    AlistT[ListIndexA] = type;
    AlistM[ListIndexA] = mode;
    if (mode == 6)
        AlistS[ListIndexA] = stat;
    else {
        AlistS[ListIndexA] = 0;
        if (mode != 3 && mode != 7) {
            if (type & 0x80) {
                if (x > 0x40)
                    AlistS[ListIndexA] = 0x78;
            } else {
                if (x < 0x40)
                    AlistS[ListIndexA] = 0x78;
            }
        }
    }
    if (ListIndexA >= 1000) {
        CompactListA();
        if (ListIndexA >= 1000)
            return 1;
    }
    ListIndexA++;
    return 1;
}

void  AddAntToAList(int16_t x, int16_t y, int16_t type, int16_t mode, int16_t stat)
{
    int16_t n;

    if (ListIndexA >= 1000)
        return;
    n = ListIndexA;
    AlistX[n] = x;
    AlistY[n] = y;
    AlistM[n] = mode;
    AlistT[n] = type;
    AlistS[n] = stat;
    LifeA[x][y] = type;
    ListIndexA++;
}

void  AddAntToBList(int16_t x, int16_t y, int16_t type, int16_t mode, int16_t stat)
{
    int16_t n;

    if (native_state_ListIndexB.signed_value >= 500)
        return;
    n = native_state_ListIndexB.signed_value;
    BlistX[n] = x;
    BlistY[n] = y;
    BlistM[n] = mode;
    BlistT[n] = type;
    BlistS[n] = stat;
    LifeB[x][y] = type;
    native_state_ListIndexB.signed_value++;
}

void  AddAntToRList(int16_t x, int16_t y, int16_t type, int16_t mode, int16_t stat)
{
    int16_t n;

    if (native_state_ListIndexR.signed_value >= 500)
        return;
    n = native_state_ListIndexR.signed_value;
    RlistX[n] = x;
    RlistY[n] = y;
    RlistM[n] = mode;
    RlistT[n] = type;
    RlistS[n] = stat;
    LifeR[x][y] = type;
    native_state_ListIndexR.signed_value++;
}

int16_t  GetFromAlist(int16_t colony)
{
    int16_t i;
    int16_t t;

    i = ListIndexA;
    while (i > 0) {
        i--;
        t = AlistT[i];
        if (t == 0)
            continue;
        if ((t >> 7) == colony)
            break;
    }
    if (i) {
        RemoveFromAList(i);
        return 1;
    }
    return 0;
}

void  BuildAntListA(void)
{
    int16_t x;
    int16_t y;
    int16_t ant;

    ListIndexA = 0;
    for (x = 0; x < 128; x++) {
        for (y = 0; y < 64; y++) {
            ant = LifeA[x][y];
            if (ant && IsYellowAnt(ant) != 1) {
                AlistX[ListIndexA] = x;
                AlistY[ListIndexA] = y;
                AlistM[ListIndexA] = 2;
                AlistT[ListIndexA] = ant;
                AlistS[ListIndexA] = 0;
                if (ListIndexA < 997)
                    ListIndexA++;
            }
        }
    }
}

void  ClearListB(void)
{
    native_state_ListIndexB.signed_value = 0;
}

void  ClearListR(void)
{
    native_state_ListIndexR.signed_value = 0;
}

#pragma pack(pop)
