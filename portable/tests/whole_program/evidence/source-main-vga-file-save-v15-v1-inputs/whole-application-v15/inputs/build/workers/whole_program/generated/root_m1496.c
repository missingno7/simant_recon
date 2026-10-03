#include "dos_types.h"
#include "portable/whole_program/platform/dos_memory.h"
#include "portable/whole_program/platform/dos_io.h"
#include "portable/whole_program/platform/graphics_source_fields.h"
#pragma pack(push, 2)
/* Root module, code frame 1496: pheromone maps (nest holes, colony smell decay, alarm). */

extern uint8_t  HoleMapB[];
extern uint8_t  MapA[128][64];
extern uint8_t  PherMapBN[64][32];
extern uint8_t  HoleMapR[];
extern uint8_t  PherMapRN[64][32];
extern uint8_t  PherMapBT[64][32];
extern uint8_t  PherMapRT[64][32];
extern uint8_t  PherMapA[64][32];
extern uint8_t  fd_3E1D_C89F[64][32];
extern char  Dy8[8];
extern char  Dx8[8];

void  FillHolesBN(void)
{
    int16_t y;

    for (y = 0; y < 64; y++) {
        if (HoleMapB[y]) {
            if ((MapA[HoleMapB[y]][y] == 0x51) == 0)
                PherMapBN[HoleMapB[y] >> 1][y >> 1] = 0xff;
            else
                PherMapBN[HoleMapB[y] >> 1][y >> 1] = 0;
        }
    }
}

void  FillHolesRN(void)
{
    int16_t y;

    for (y = 0; y < 64; y++) {
        if (HoleMapR[y]) {
            if ((MapA[HoleMapR[y]][y] == 0x51) == 0)
                PherMapRN[HoleMapR[y] >> 1][y >> 1] = 0xff;
            else
                PherMapRN[HoleMapR[y] >> 1][y >> 1] = 0;
        }
    }
}

void  ColonySmellBN(void)
{
    int16_t x;
    int16_t y;

    for (x = 0; x < 64; x++) {
        for (y = 0; y < 32; y++) {
            if (PherMapBN[x][y] != 0)
                PherMapBN[x][y]--;
        }
    }
}

void  ColonySmellRN(void)
{
    int16_t x;
    int16_t y;

    for (x = 0; x < 64; x++) {
        for (y = 0; y < 32; y++) {
            if (PherMapRN[x][y] != 0)
                PherMapRN[x][y]--;
        }
    }
}

void  ColonySmellBT(void)
{
    int16_t x;
    int16_t y;
    int16_t smell;

    for (x = 0; x < 64; x++) {
        for (y = 0; y < 32; y++) {
            smell = PherMapBT[x][y];
            if (smell < 8)
                PherMapBT[x][y] = 0;
            else
                PherMapBT[x][y] = smell - (smell >> 1);
        }
    }
}

void  ColonySmellRT(void)
{
    int16_t x;
    int16_t y;
    int16_t smell;

    for (x = 0; x < 64; x++) {
        for (y = 0; y < 32; y++) {
            smell = PherMapRT[x][y];
            if (smell <= 0)
                continue;
            if (smell < 8)
                PherMapRT[x][y] = 0;
            else
                PherMapRT[x][y] -= smell >> 1;
        }
    }
}

void  SmoothAlarm(void)
{
    int16_t x;
    int16_t y;
    int16_t sum;
    int16_t v;

    for (x = 0; x < 64; x++)
        for (y = 0; y < 32; y++)
            fd_3E1D_C89F[x][y] = PherMapA[x][y];
    for (x = 0; x < 64; x++) {
        for (y = 0; y < 32; y++) {
            sum = 0;
            if (x > 0)
                sum += fd_3E1D_C89F[x - 1][y];
            if (y > 0)
                sum += fd_3E1D_C89F[x][y - 1];
            if (x < 63)
                sum += fd_3E1D_C89F[x + 1][y];
            if (y < 31)
                sum += fd_3E1D_C89F[x][y + 1];
            v = (fd_3E1D_C89F[x][y] + (sum >> 2)) >> 1;
            if (v > 8)
                PherMapA[x][y] = v;
            else
                PherMapA[x][y] = 0;
        }
    }
}

void  AlarmHere(int16_t x, int16_t y, int16_t level)
{
    int16_t v;

    x >>= 1;
    y >>= 1;
    v = PherMapA[x][y] + level;
    if (v > 200)
        v = 200;
    PherMapA[x][y] = v;
}

void  AlarmHere2(int16_t x, int16_t y, int16_t level)
{
    int16_t v;

    x >>= 1;
    y >>= 1;
    v = PherMapA[x][y];
    if (v > level)
        return;
    PherMapA[x][y] = level;
}

void  JamScentBN(int16_t x, int16_t y, int16_t scent)
{
    int16_t v;

    v = PherMapBN[x >> 1][y >> 1];
    if (v < scent)
        PherMapBN[x >> 1][y >> 1] = scent;
}

void  JamScentRN(int16_t x, int16_t y, int16_t scent)
{
    int16_t v;

    v = PherMapRN[x >> 1][y >> 1];
    if (v < scent)
        PherMapRN[x >> 1][y >> 1] = scent;
}

void  JamScentBT(int16_t x, int16_t y, int16_t scent)
{
    int16_t v;

    v = PherMapBT[x >> 1][y >> 1];
    if (v < scent)
        PherMapBT[x >> 1][y >> 1] = scent;
}

void  JamScentRT(int16_t x, int16_t y, int16_t scent)
{
    int16_t v;

    v = PherMapRT[x >> 1][y >> 1];
    if (v < scent)
        PherMapRT[x >> 1][y >> 1] = scent;
}

void  DecTSmell(int16_t x, int16_t y, int16_t red)
{
    int16_t xh;
    int16_t yh;

    xh = x >> 1;
    yh = y >> 1;
    if (red) {
        if (PherMapRT[xh][yh] != 0)
            PherMapRT[xh][yh]--;
    } else {
        if (PherMapBT[xh][yh] != 0)
            PherMapBT[xh][yh]--;
    }
}

int16_t  GetSmellT(int16_t x, int16_t y, int16_t dir, int16_t red)
{
    int16_t nx;
    int16_t ny;

    nx = x + Dx8[dir];
    ny = y + Dy8[dir];
    if (nx < 0)
        return 0;
    if (nx > 63)
        return 0;
    if (ny < 0)
        return 0;
    if (ny > 31)
        return 0;
    if (red)
        return PherMapRT[nx][ny];
    return PherMapBT[nx][ny];
}

#pragma pack(pop)
