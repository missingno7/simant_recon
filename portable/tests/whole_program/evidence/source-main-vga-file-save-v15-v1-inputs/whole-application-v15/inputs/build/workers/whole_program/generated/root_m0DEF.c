#include "dos_types.h"
#include "portable/whole_program/platform/dos_memory.h"
#include "portable/whole_program/platform/dos_io.h"
#include "portable/whole_program/platform/graphics_source_fields.h"
#include "simulation_state_50f6_v7.h"
#include "native_owners.h"
#pragma pack(push, 2)
extern int16_t  fd_3D57_0C1A[];
/* Root module 0DEF: red colony initiator ant (Win16 unit MakeRedInitiator,
 * DoRedInitiator, GetNewRedTask, GetRedBestDirs; SIMANT1 segment order). */

extern int16_t  ListIndexA;
extern uint8_t  AlistT[];
extern uint8_t  AlistM[];
extern uint8_t  AlistS[];

void  f_0DEF_0000(void)
{
    int16_t index;

    (fd_3D57_0C1A[1]) = 0;
    if (native_state_BpopT.signed_value >= 30) {
        index = ListIndexA;
        while (index > 0) {
            --index;
            if (AlistT[index] > 0x7f) {
                AlistT[index] = 0xb0;
                AlistM[index] = 0x13;
                AlistS[index] = 0;
                native_state_fd_50F6_04A4.signed_value = 0;
                (fd_3D57_0C1A[1]) = 1;
                return;
            }
        }
    }
}

extern uint8_t  AlistY[];
extern uint8_t  AlistX[];
void  f_0DEF_0233(void);
extern int16_t  MePlane;
int16_t  f_0DEF_031F(int16_t plane, int16_t x, int16_t y, int16_t a, int16_t b);
extern int16_t  SRand1(int16_t range);
extern int8_t  Dy8[];
extern int8_t  Dx8[];
extern uint8_t  LifeA[][64];
extern int16_t  IsYellowAnt(int16_t life);
extern void  o25_3BA4_0DFB(int16_t a, int16_t index);
extern int16_t  RandTurn(int16_t dir);

void  f_0DEF_006B( int16_t i)
{
    int16_t y;
    int16_t x;
    int16_t t;
    int16_t caste;
    int16_t dir;
    int16_t nx;
    int16_t ny;
    int16_t life;

    x = AlistX[i];
    y = AlistY[i];
    t = AlistT[i];
    caste = t & 0xf8;
    native_state_RedLocX.signed_value = x;
    native_state_RedLocY.signed_value = y;
    native_state_RedPlane.signed_value = 1;
    switch (native_state_fd_50F6_04A4.signed_value) {
    case 0:
        f_0DEF_0233();
        break;
    case 2:
        if (MePlane == 1) {
            native_state_fd_50F6_04E0.signed_value = native_state_FuzLocX.signed_value;
            native_state_fd_50F6_04F2.signed_value = native_state_FuzLocY.signed_value;
        }
        break;
    }
    dir = f_0DEF_031F(1, native_state_RedLocX.signed_value, native_state_RedLocY.signed_value, native_state_fd_50F6_04E0.signed_value, native_state_fd_50F6_04F2.signed_value);
    if (dir < 0) {
        if (SRand1(10) == 0)
            native_state_fd_50F6_04A4.signed_value = 0;
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

extern int16_t  MeLocX;
extern int16_t  fd_3D57_02BC[];
extern void  UnRecruitRed(void);
extern void  RecruitRed(int16_t count);

void  f_0DEF_0233(void)
{
    int16_t redPopulation;

    UnRecruitRed();
    if (MePlane == 1) {
        if (SRand1(32) + 0x40 < MeLocX) {
            if (SRand1(10) < native_sim_state_fd_50F6_0B12.signed_values[5]) {
                native_state_fd_50F6_04A4.signed_value = 2;
                RecruitRed(native_sim_state_fd_50F6_0B12.signed_values[5]);
                return;
            }
        }
    }
    native_state_fd_50F6_04F2.signed_value = fd_3D57_02BC[1];
    native_state_fd_50F6_04E0.signed_value = fd_3D57_02BC[0];
    if (native_state_fd_50F6_04E0.signed_value > 0x1e) {
        native_state_fd_50F6_04E0.signed_value -= 5;
    } else {
        if (native_state_fd_50F6_04F2.signed_value < 0x14)
            native_state_fd_50F6_04F2.signed_value += 5;
        else if (native_state_fd_50F6_04F2.signed_value > 0x28)
            native_state_fd_50F6_04F2.signed_value -= 5;
    }
    redPopulation = native_sim_state_fd_50F6_0AFA.signed_values[1] + native_sim_state_fd_50F6_0AFA.signed_values[2];
    if (redPopulation < 0x14)
        RecruitRed(redPopulation >> 2);
    else
        RecruitRed(redPopulation >> 3);
    native_state_fd_50F6_04A4.signed_value = 1;
}

extern int16_t  GetDis(int16_t x1, int16_t y1, int16_t x2, int16_t y2);
extern int16_t  TileCanBeMovedOn(int16_t plane, int16_t x, int16_t y, int16_t fromPlane, int16_t fromX, int16_t fromY, int16_t digging);
extern int16_t  GetLife(int16_t plane, int16_t x, int16_t y);
extern int16_t  IsClearTile(int16_t plane, int16_t x, int16_t y);

int16_t  f_0DEF_031F(int16_t plane, int16_t x, int16_t y, int16_t a, int16_t b)
{
    int16_t best;
    int16_t fallback;
    int16_t threshold;
    int16_t dir;
    int16_t nx;
    int16_t ny;
    int16_t dis;

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

#pragma pack(pop)
