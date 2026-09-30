/* Root module, code frame 1496: pheromone maps (nest holes, colony smell decay, alarm). */

extern unsigned char far HoleMapB[];
extern unsigned char far MapA[128][64];
extern unsigned char far PherMapBN[64][32];
extern unsigned char far HoleMapR[];
extern unsigned char far PherMapRN[64][32];
extern unsigned char far PherMapBT[64][32];
extern unsigned char far PherMapRT[64][32];
extern unsigned char far PherMapA[64][32];
extern unsigned char far fd_3E1D_C89F[64][32];
extern char far Dy8[8];
extern char far Dx8[8];

void far FillHolesBN(void)
{
    int y;

    for (y = 0; y < 64; y++) {
        if (HoleMapB[y]) {
            if ((MapA[HoleMapB[y]][y] == 0x51) == 0)
                PherMapBN[HoleMapB[y] >> 1][y >> 1] = 0xff;
            else
                PherMapBN[HoleMapB[y] >> 1][y >> 1] = 0;
        }
    }
}

void far FillHolesRN(void)
{
    int y;

    for (y = 0; y < 64; y++) {
        if (HoleMapR[y]) {
            if ((MapA[HoleMapR[y]][y] == 0x51) == 0)
                PherMapRN[HoleMapR[y] >> 1][y >> 1] = 0xff;
            else
                PherMapRN[HoleMapR[y] >> 1][y >> 1] = 0;
        }
    }
}

void far ColonySmellBN(void)
{
    int x;
    int y;

    for (x = 0; x < 64; x++) {
        for (y = 0; y < 32; y++) {
            if (PherMapBN[x][y] != 0)
                PherMapBN[x][y]--;
        }
    }
}

void far ColonySmellRN(void)
{
    int x;
    int y;

    for (x = 0; x < 64; x++) {
        for (y = 0; y < 32; y++) {
            if (PherMapRN[x][y] != 0)
                PherMapRN[x][y]--;
        }
    }
}

void far ColonySmellBT(void)
{
    int x;
    int y;
    int smell;

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

void far ColonySmellRT(void)
{
    int x;
    int y;
    int smell;

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

void far SmoothAlarm(void)
{
    int x;
    int y;
    int sum;
    int v;

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

void far AlarmHere(int x, int y, int level)
{
    int v;

    x >>= 1;
    y >>= 1;
    v = PherMapA[x][y] + level;
    if (v > 200)
        v = 200;
    PherMapA[x][y] = v;
}

void far AlarmHere2(int x, int y, int level)
{
    int v;

    x >>= 1;
    y >>= 1;
    v = PherMapA[x][y];
    if (v > level)
        return;
    PherMapA[x][y] = level;
}

void far JamScentBN(int x, int y, int scent)
{
    int v;

    v = PherMapBN[x >> 1][y >> 1];
    if (v < scent)
        PherMapBN[x >> 1][y >> 1] = scent;
}

void far JamScentRN(int x, int y, int scent)
{
    int v;

    v = PherMapRN[x >> 1][y >> 1];
    if (v < scent)
        PherMapRN[x >> 1][y >> 1] = scent;
}

void far JamScentBT(int x, int y, int scent)
{
    int v;

    v = PherMapBT[x >> 1][y >> 1];
    if (v < scent)
        PherMapBT[x >> 1][y >> 1] = scent;
}

void far JamScentRT(int x, int y, int scent)
{
    int v;

    v = PherMapRT[x >> 1][y >> 1];
    if (v < scent)
        PherMapRT[x >> 1][y >> 1] = scent;
}

void far DecTSmell(int x, int y, int red)
{
    int xh;
    int yh;

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

int far GetSmellT(int x, int y, int dir, int red)
{
    int nx;
    int ny;

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
