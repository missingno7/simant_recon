#include "dos_types.h"
#include "portable/whole_program/platform/dos_memory.h"
#include "portable/whole_program/platform/dos_io.h"
#include "portable/whole_program/platform/graphics_source_fields.h"
#include "simulation_state_50f6_v7.h"
#include "source_bounded_additive.h"
#include "native_owners.h"
#pragma pack(push, 2)
/* Root module, code frame 1383: colony strategy, recruiting, new modes and movement directions. */

extern int16_t  MePlane;
extern int16_t  SRand1(int16_t range);
extern int16_t  MeLocX;
extern int16_t  MeLocY;
extern int32_t  GetDis(int16_t x1, int16_t y1, int16_t x2, int16_t y2);
extern int16_t  IdealCaste[4];
extern int16_t  CasteTabB[4];
extern int16_t  fd_3D57_0C0E;
extern int16_t  ModeTabB[3];
extern int16_t  ModeMe;
extern int16_t  SRand32(void);
extern int16_t  SRand128(void);
extern void  myBeginSong(int16_t id, int16_t arg);
extern void  *  *  AdviceStrs;
extern void  EditMessage(void  *, int32_t, int16_t);
extern uint8_t  AlistT[];
extern uint8_t  AlistM[];
extern uint8_t  AlistS[];
extern uint8_t  AlistX[];
extern uint8_t  AlistY[];
extern uint8_t  MapA[128][64];
extern uint8_t  BlistT[];
extern uint8_t  BlistM[];
extern uint8_t  BlistS[];
extern int16_t  ListIndexA;
extern uint8_t  RlistT[];
extern uint8_t  RlistM[];
extern int16_t  SRand8(void);
extern char  ModeTabWB[][8];
extern char  ModeTabSB[][8];
extern char  CasteModeTabB[];
extern uint8_t  PherMapRT[64][32];
extern uint8_t  PherMapBT[64][32];
extern char  Dx8[8];
extern char  Dy8[8];
extern char  TurnTab[][8];
extern uint8_t  PherMapRN[64][32];
extern uint8_t  PherMapBN[64][32];
extern int16_t  SRand2(void);
extern int16_t  GetDir(int16_t x1, int16_t y1, int16_t x2, int16_t y2);
extern int16_t  fd_3D57_02B0[2];
extern int16_t  SRand4(void);
extern int16_t  fd_3D57_02AC[2];
extern uint8_t  PherMapA[64][32];

int16_t  GstrB(void);
void  SetCasteProd(void);
void  SetModeProd(void);
int16_t  GstrR(void);
void  StartAttack(void);
int16_t  GetNewModeB(int16_t caste);
int16_t  GetNewModeR(int16_t caste);
int16_t  GetNestDir(int16_t x, int16_t y, int16_t dir, int16_t type);
int16_t  Bounce(int16_t x, int16_t y);

void  GetStrategy(void)
{
    int16_t dis;

    native_state_ChaseSpid.signed_value = 0;
    if (MePlane == 1) {
        native_state_FuzLocX.signed_value = SRand1(5) + MeLocX - 2;
        native_state_FuzLocY.signed_value = SRand1(5) + MeLocY - 2;
        if (native_state_FuzLocX.signed_value < 0)
            native_state_FuzLocX.signed_value = 0;
        if (native_state_FuzLocX.signed_value > 127)
            native_state_FuzLocX.signed_value = 127;
        if (native_state_FuzLocY.signed_value < 0)
            native_state_FuzLocY.signed_value = 0;
        if (native_state_FuzLocY.signed_value > 63)
            native_state_FuzLocY.signed_value = 63;
        if (native_state_fd_50F6_0F0C.signed_value) {
            dis = (int16_t)GetDis(native_state_fd_50F6_0F12.signed_value >> 4, native_state_fd_50F6_0F34.signed_value >> 4, MeLocX, MeLocY);
            if (dis < 100)
                native_state_ChaseSpid.signed_value = 1;
        }
    }
    native_state_FuzLocX.signed_value = MeLocX;
    native_state_StrategicModeB.signed_value = GstrB();
    native_state_fd_50F6_10A6.signed_value = GstrR();
    SetCasteProd();
    SetModeProd();
}

int16_t  GstrB(void)
{
    if (native_state_HealthB.signed_value < 10 && (native_state_BpopT.signed_value >> 1) > native_state_RpopT.signed_value && native_state_RpopT.signed_value > 0 && native_state_fd_50F6_036C.signed_value > 0)
        return 0;
    if (native_state_HealthB.signed_value < 30)
        return 5;
    if (native_state_HealthB.signed_value < 50)
        return 4;
    if (native_state_fd_50F6_0224.signed_value < native_state_BpopT.signed_value)
        return 3;
    if (native_state_fd_50F6_0224.signed_value < native_state_BpopT.signed_value * 2)
        return 2;
    if (native_state_BpopT.signed_value > 100 && native_state_RpopT.signed_value > 0 && native_state_fd_50F6_036C.signed_value > 0 && native_state_BpopT.signed_value / 3 > native_state_RpopT.signed_value)
        return 0;
    return 1;
}

void  SetCasteProd(void)
{
    int16_t i;
    int16_t diff;
    int16_t pct[5];
    int16_t want[5];

    {
        int16_t total;
        int16_t ideal;

        total = 0;
        ideal = 0;
        for (i = 0; i < 4; i++) {
            total += native_sim_state_fd_50F6_0AEC.signed_values[i + 1];
            ideal += IdealCaste[i];
        }
        for (i = 0; i < 4; i++) {
            if (total <= 0)
                pct[i] = 0;
            else
                pct[i] = 100L * native_sim_state_fd_50F6_0AEC.signed_values[i + 1] / total;
            if (ideal <= 0)
                want[i] = 0;
            else
                want[i] = 100L * IdealCaste[i] / ideal;
        }
    }
    {
        int16_t best;
        int16_t chosen;

        best = 0;
        chosen = best;
        for (i = 0; i < 4; i++) {
            diff = pct[i] - want[i];
            if (diff < best) {
                best = diff;
                chosen = i;
            }
        }
        fd_3D57_0C0E = CasteTabB[chosen];
    }
}

void  SetModeProd(void)
{
    int16_t scaled[6];
    int16_t diff[6];
    int16_t total;
    int16_t i;
    int16_t best;
    int16_t max;

    total = 0;
    for (i = 0; i < 3; i++)
        total += native_sim_state_fd_50F6_0B12.signed_values[i];
    for (i = 0; i < 3; i++)
        scaled[i] = (uint32_t)native_sim_state_modeLevels.unsigned_values[i] * (int32_t)total / 65535UL;
    for (i = 0; i < 3; i++)
        diff[i] = scaled[i] - native_sim_state_fd_50F6_0B12.signed_values[i];
    max = 0;
    best = 0;
    for (i = 0; i < 3; i++) {
        if (diff[i] > max) {
            max = diff[i];
            best = i;
        }
    }
    ModeMe = ModeTabB[best];
}

int16_t  GstrR(void)
{
    if (native_state_fd_50F6_08E8.signed_value == 0 && native_sim_state_fd_50F6_0AFA.signed_values[3] + native_sim_state_fd_50F6_0AFA.signed_values[4] > 20)
        native_state_fd_50F6_08E8.signed_value = 200;
    if (native_state_fd_50F6_0504.signed_value) {
        native_state_fd_50F6_0504.signed_value--;
        return 0;
    }
    if (native_state_HealthR.signed_value < 10 && (native_state_RpopT.signed_value >> 1) > native_state_BpopT.signed_value && native_state_BpopT.signed_value > 0 && native_state_fd_50F6_035E.signed_value > 0) {
        StartAttack();
        return 0;
    }
    if (native_state_HealthR.signed_value < 30)
        return 5;
    if (native_state_HealthR.signed_value < 50)
        return 4;
    if (native_state_TilesDugR.signed_value < native_state_RpopT.signed_value)
        return 3;
    if (native_state_TilesDugR.signed_value < native_state_RpopT.signed_value * 2)
        return 2;
    if (native_state_RpopT.signed_value > 100 && native_state_BpopT.signed_value > 0 && native_state_fd_50F6_035E.signed_value > 0 && native_state_RpopT.signed_value / 3 > native_state_BpopT.signed_value) {
        StartAttack();
        return 0;
    }
    if (SRand32() == 0 && native_state_RpopT.signed_value > 20 && native_state_RpopT.signed_value > native_state_BpopT.signed_value && SRand128() == 0) {
        StartAttack();
        return 0;
    }
    return 1;
}

void  StartAttack(void)
{
    native_state_fd_50F6_0504.signed_value = SRand1(100) + 30;
    myBeginSong(0x2b0a, 0x3f);
    EditMessage(AdviceStrs[5], 120L, 0);
}

void  ForceModeA(int16_t index, int16_t caste, int16_t mode)
{
    switch (caste) {
    case 1:
        AlistT[index] += 8;
        AlistM[index] = mode;
        AlistS[index] = 0;
        break;
    case 3:
    case 7:
        AlistT[index] -= 8;
        if (MapA[AlistX[index]][AlistY[index]] < 0x48)
            MapA[AlistX[index]][AlistY[index]] = 0x48;
    case 2:
    case 6:
        AlistM[index] = mode;
        AlistS[index] = 0;
        break;
    case 5:
    case 9:
        AlistT[index] -= 0x18;
        AlistM[index] = mode;
        AlistS[index] = 0;
        break;
    }
    if (mode == 6 && MePlane == 1)
        AlistS[index] = ((MeLocY & 0x3c) << 2) | (MeLocX >> 3);
}

void  ForceModeB(int16_t index, int16_t caste, int16_t mode)
{
    switch (caste) {
    case 1:
        BlistT[index] += 8;
        BlistM[index] = mode;
        BlistS[index] = 0;
        break;
    case 3:
    case 7:
        BlistT[index] -= 8;
    case 2:
    case 6:
        BlistM[index] = mode;
        BlistS[index] = 0;
        break;
    case 5:
    case 9:
        BlistT[index] -= 0x18;
        BlistM[index] = mode;
        BlistS[index] = 0;
        break;
    }
    if (mode == 6 && MePlane == 1)
        BlistS[index] = ((MeLocY & 0x3c) << 2) | (MeLocX >> 3);
}

void  Recruit(int16_t count)
{
    int16_t i;
    int16_t type;
    int16_t n;
    int16_t caste;

    n = count;
    i = ListIndexA;
    while (i > 0) {
        if (n <= 0)
            break;
        i--;
        type = AlistT[i];
        if (type != 0 && !(type & 0x80)) {
            caste = (type & 0x78) >> 3;
            if (caste == 2 || caste == 6) {
                if (AlistM[i] != 6) {
                    AlistM[i] = 6;
                    AlistS[i] = 0;
                    n--;
                }
            }
        }
    }
    i = native_state_ListIndexB.signed_value;
    while (i > 0) {
        if (n <= 0)
            break;
        i--;
        type = BlistT[i];
        if (type != 0 && !(type & 0x80)) {
            caste = (type & 0x78) >> 3;
            if (caste == 2 || caste == 6) {
                if (BlistM[i] != 6) {
                    BlistM[i] = 6;
                    BlistS[i] = 0;
                    n--;
                }
            }
        }
    }
}

void  UnRecruit(int16_t all)
{
    int16_t n;
    int16_t i;
    int16_t type;

    n = fd_50F6_0D40[6];
    if (all == 0)
        n = n / 2;
    else
        n += 100;
    i = ListIndexA;
    while (i > 0) {
        if (n <= 0)
            break;
        i--;
        type = AlistT[i];
        if (type != 0 && !(type & 0x80) && AlistM[i] == 6) {
            AlistM[i] = 0;
            n--;
        }
    }
    i = native_state_ListIndexB.signed_value;
    while (i > 0) {
        if (n <= 0)
            break;
        i--;
        type = BlistT[i];
        if (type != 0 && !(type & 0x80) && BlistM[i] == 6) {
            BlistM[i] = 0;
            n--;
        }
    }
    i = native_state_ListIndexR.signed_value;
    while (i > 0) {
        if (n <= 0)
            break;
        i--;
        type = RlistT[i];
        if (type != 0 && !(type & 0x80) && RlistM[i] == 6) {
            RlistM[i] = 7;
            n--;
        }
    }
}

void  RecruitRed(int16_t count)
{
    int16_t cur;
    int16_t need;
    int16_t i;
    int16_t type;
    int16_t mode;

    need = count;
    i = ListIndexA;
    while (i > 0) {
        if (need <= 0)
            break;
        i--;
        type = AlistT[i];
        if (type != 0 && type > 0x7f) {
            cur = AlistM[i];
            mode = (type & 0x78) >> 3;
            if (mode == 2 || mode == 6) {
                if (cur != 0x13 && cur != 6) {
                    AlistM[i] = 6;
                    AlistS[i] = 0;
                    need--;
                }
            }
        }
    }
}

void  UnRecruitRed(void)
{
    int16_t i;
    int16_t type;

    i = ListIndexA;
    while (i > 0) {
        i--;
        type = AlistT[i];
        if (type != 0 && type > 0x7f && AlistM[i] == 6)
            AlistM[i] = 0;
    }
}

int16_t  GetNewMode(int16_t caste, int16_t type)
{
    if (type & 0x80)
        return GetNewModeR(caste);
    return GetNewModeB(caste);
}

int16_t  GetNewModeB(int16_t caste)
{
    if (native_state_ModeAuto.signed_value == 1) {
        if (caste == 2)
            return ModeTabWB[native_state_StrategicModeB.signed_value][SRand8()];
        if (caste == 6)
            return ModeTabSB[native_state_StrategicModeB.signed_value][SRand8()];
        return CasteModeTabB[caste];
    }
    if (caste == 2 || caste == 6)
        return ModeMe;
    return CasteModeTabB[caste];
}

int16_t  GetNewModeR(int16_t caste)
{
    if (caste == 2)
        return ModeTabWB[native_state_fd_50F6_10A6.signed_value][SRand8()];
    if (caste == 6)
        return ModeTabSB[native_state_fd_50F6_10A6.signed_value][SRand8()];
    return CasteModeTabB[caste];
}

int16_t  GetForageDir(int16_t x, int16_t y, int16_t dir, int16_t attribute)
{
    int16_t xCell;
    int16_t yCell;
    int16_t plane;
    int16_t best;
    int16_t bestDir;
    int16_t i;
    int16_t nx;
    int16_t ny;
    int16_t current;
    int16_t value;

    if (x == 0) {
        if (y == 0) return 3;
        if (y == 63) return 1;
        return SRand1(3) + 1;
    }
    if (y == 0) {
        if (x == 127) return 5;
        return SRand1(3) + 3;
    }
    if (x == 127) {
        if (y == 63) return 7;
        return SRand1(3) + 5;
    }
    if (y == 63) return (SRand1(3) - 1) & 7;

    xCell = x >> 1;
    yCell = y >> 1;
    plane = attribute & 0x80;
    if (plane)
        current = PherMapRT[xCell][yCell];
    else
        current = PherMapBT[xCell][yCell];

    best = 0;
    bestDir = SRand8();
    for (i = 0; i < 8; ++i) {
        nx = xCell + Dx8[i];
        nx &= 0x3f;
        ny = yCell + Dy8[i];
        ny &= 0x1f;
        if (plane)
            value = PherMapRT[nx][ny];
        else
            value = PherMapBT[nx][ny];
        if (value > best) {
            best = value;
            bestDir = i;
        }
    }
    if (best > 0) {
        if (current > best) return -1;
        return TurnTab[dir][bestDir];
    }
    return TurnTab[dir][SRand8()];
}

int16_t  GetNestDir(int16_t x, int16_t y, int16_t dir, int16_t type)
{
    int16_t xCell;
    int16_t yCell;
    int16_t plane;
    int16_t best;
    int16_t bestDir;
    int16_t i;
    int16_t nx;
    int16_t ny;
    int16_t current;
    int16_t value;

    xCell = x >> 1;
    yCell = y >> 1;
    plane = type >> 7;
    nx = Bounce(x, y);
    if (nx) return (nx - 1) & 7;
    if (plane)
        current = PherMapRN[xCell][yCell];
    else
        current = PherMapBN[xCell][yCell];
    if (current) {
        best = 0;
        bestDir = 0;
        for (i = 0; i < 8; ++i) {
            nx = xCell + Dx8[i];
            nx &= 0x3f;
            ny = yCell + Dy8[i];
            ny &= 0x1f;
            if (plane)
                value = PherMapRN[nx][ny];
            else
                value = PherMapBN[nx][ny];
            if (value > best) {
                best = value;
                bestDir = i;
            }
        }
        if (SRand2())
            value = TurnTab[dir][bestDir];
        else
            value = dir;
        return TurnTab[value][bestDir];
    }
    if (plane) {
        nx = GetDir(x, y, fd_3D57_02B0[0], fd_3D57_02B0[1]);
        if (nx && SRand4()) return TurnTab[dir][nx - 1];
    } else {
        nx = GetDir(x, y, fd_3D57_02AC[0], fd_3D57_02AC[1]);
        if (nx == 0 || SRand4() == 0) return TurnTab[dir][SRand8()];
        return TurnTab[dir][nx - 1];
    }
    return TurnTab[dir][SRand8()];
}

int16_t  GetAlarmDir(int16_t x, int16_t y, int16_t dir)
{
    int16_t xc;
    int16_t yc;
    int16_t r;
    int16_t i;
    int16_t best;
    int16_t bestDir;
    int16_t value;

    xc = x >> 1;
    yc = y >> 1;
    r = Bounce(x, y);
    if (r) return (r - 1) & 7;
    best = 0;
    bestDir = 0;
    for (i = 0; i < 8; i++) {
        value = PherMapA[(xc + Dx8[i]) & 0x3f][(yc + Dy8[i]) & 0x1f];
        if (value > best) {
            best = value;
            bestDir = i;
        }
    }
    if (best != 0) return TurnTab[dir][bestDir];
    return TurnTab[dir][SRand8()];
}

int16_t  GetRandDir(int16_t x, int16_t y, int16_t dir)
{
    int16_t r;

    r = Bounce(x, y);
    if (r) return (r - 1) & 7;
    return TurnTab[dir][SRand8()];
}

int16_t  GetDefendDir(int16_t x, int16_t y, int16_t dir)
{
    int16_t r;

    r = Bounce(x, y);
    if (r) return (r - 1) & 7;
    switch (MePlane) {
    case 1:
        if (native_state_ChaseSpid.signed_value == 1)
            r = GetDir(x, y, native_state_fd_50F6_0F12.signed_value >> 4, native_state_fd_50F6_0F34.signed_value >> 4);
        else {
            r = GetDis(x, y, native_state_FuzLocX.signed_value, native_state_FuzLocY.signed_value);
            if (native_sim_state_fd_50F6_0B12.signed_values[5] >> 1 < r)
                r = GetDir(x, y, native_state_FuzLocX.signed_value, native_state_FuzLocY.signed_value);
            else
                r = SRand1(8) + 1;
        }
        break;
    case 2:
        return GetNestDir(x, y, dir, 0);
    case 3:
        return GetNestDir(x, y, dir, 0x80);
    }
    if (r) return TurnTab[dir][r - 1];
    return dir;
}

int16_t  GetRedDefendDir(int16_t x, int16_t y, int16_t dir)
{
    int16_t r;

    r = Bounce(x, y);
    if (r) return (r - 1) & 7;
    switch (native_state_RedPlane.signed_value) {
    case 1:
        r = GetDis(x, y, native_state_RedLocX.signed_value, native_state_RedLocY.signed_value);
        if (native_sim_state_fd_50F6_0C2A.signed_values[5] >> 1 < r)
            r = GetDir(x, y, native_state_RedLocX.signed_value, native_state_RedLocY.signed_value);
        else
            r = SRand1(8) + 1;
        break;
    case 2:
        return GetNestDir(x, y, dir, 0);
    case 3:
        return GetNestDir(x, y, dir, 0x80);
    }
    if (r) return TurnTab[dir][r - 1];
    return dir;
}

int16_t  Bounce(int16_t x, int16_t y)
{
    if (x == 0) {
        if (y == 0) return SRand1(3) + 3;
        if (y == 0x3f) return SRand1(3) + 1;
        return SRand1(5) + 1;
    }
    if (y == 0) {
        if (x == 0x7f) return SRand1(3) + 5;
        return SRand1(5) + 3;
    }
    if (x == 0x7f) {
        if (y == 0x3f) return SRand1(3) + 7;
        return SRand1(5) + 5;
    }
    if (y == 0x3f) return SRand1(5) + 7;
    return 0;
}

#pragma pack(pop)
