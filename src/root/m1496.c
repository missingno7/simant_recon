/* Root module, code frame 1496: pheromone maps (nest holes, colony smell decay, alarm). */

extern unsigned char far HoleMapB[];
extern unsigned char far MapA[128][64];
extern unsigned char far fd_3E1D_E09F[64][32];
extern unsigned char far HoleMapR[];
extern unsigned char far fd_3E1D_F09F[64][32];
extern unsigned char far fd_3E1D_E89F[64][32];
extern unsigned char far fd_4DA7_0000[64][32];
extern unsigned char far fd_3E1D_D09F[64][32];
extern unsigned char far fd_3E1D_C89F[64][32];
extern char far Dy8[8];
extern char far Dx8[8];

void far FillHolesBN(void)
{
    int y;

    for (y = 0; y < 64; y++) {
        if (HoleMapB[y]) {
            if ((MapA[HoleMapB[y]][y] == 0x51) == 0)
                fd_3E1D_E09F[HoleMapB[y] >> 1][y >> 1] = 0xff;
            else
                fd_3E1D_E09F[HoleMapB[y] >> 1][y >> 1] = 0;
        }
    }
}

void far FillHolesRN(void)
{
    int y;

    for (y = 0; y < 64; y++) {
        if (HoleMapR[y]) {
            if ((MapA[HoleMapR[y]][y] == 0x51) == 0)
                fd_3E1D_F09F[HoleMapR[y] >> 1][y >> 1] = 0xff;
            else
                fd_3E1D_F09F[HoleMapR[y] >> 1][y >> 1] = 0;
        }
    }
}

void far ColonySmellBN(void)
{
    int x;
    int y;

    for (x = 0; x < 64; x++) {
        for (y = 0; y < 32; y++) {
            if (fd_3E1D_E09F[x][y] != 0)
                fd_3E1D_E09F[x][y]--;
        }
    }
}

void far ColonySmellRN(void)
{
    int x;
    int y;

    for (x = 0; x < 64; x++) {
        for (y = 0; y < 32; y++) {
            if (fd_3E1D_F09F[x][y] != 0)
                fd_3E1D_F09F[x][y]--;
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
            smell = fd_3E1D_E89F[x][y];
            if (smell < 8)
                fd_3E1D_E89F[x][y] = 0;
            else
                fd_3E1D_E89F[x][y] = smell - (smell >> 1);
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
            smell = fd_4DA7_0000[x][y];
            if (smell <= 0)
                continue;
            if (smell < 8)
                fd_4DA7_0000[x][y] = 0;
            else
                fd_4DA7_0000[x][y] -= smell >> 1;
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
            fd_3E1D_C89F[x][y] = fd_3E1D_D09F[x][y];
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
                fd_3E1D_D09F[x][y] = v;
            else
                fd_3E1D_D09F[x][y] = 0;
        }
    }
}

void far AlarmHere(int x, int y, int level)
{
    int v;

    x >>= 1;
    y >>= 1;
    v = fd_3E1D_D09F[x][y] + level;
    if (v > 200)
        v = 200;
    fd_3E1D_D09F[x][y] = v;
}

void far AlarmHere2(int x, int y, int level)
{
    int v;

    x >>= 1;
    y >>= 1;
    v = fd_3E1D_D09F[x][y];
    if (v > level)
        return;
    fd_3E1D_D09F[x][y] = level;
}

void far JamScentBN(int x, int y, int scent)
{
    int v;

    v = fd_3E1D_E09F[x >> 1][y >> 1];
    if (v < scent)
        fd_3E1D_E09F[x >> 1][y >> 1] = scent;
}

void far JamScentRN(int x, int y, int scent)
{
    int v;

    v = fd_3E1D_F09F[x >> 1][y >> 1];
    if (v < scent)
        fd_3E1D_F09F[x >> 1][y >> 1] = scent;
}

void far JamScentBT(int x, int y, int scent)
{
    int v;

    v = fd_3E1D_E89F[x >> 1][y >> 1];
    if (v < scent)
        fd_3E1D_E89F[x >> 1][y >> 1] = scent;
}

void far JamScentRT(int x, int y, int scent)
{
    int v;

    v = fd_4DA7_0000[x >> 1][y >> 1];
    if (v < scent)
        fd_4DA7_0000[x >> 1][y >> 1] = scent;
}

void far DecTSmell(int x, int y, int red)
{
    int xh;
    int yh;

    xh = x >> 1;
    yh = y >> 1;
    if (red) {
        if (fd_4DA7_0000[xh][yh] != 0)
            fd_4DA7_0000[xh][yh]--;
    } else {
        if (fd_3E1D_E89F[xh][yh] != 0)
            fd_3E1D_E89F[xh][yh]--;
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
        return fd_4DA7_0000[nx][ny];
    return fd_3E1D_E89F[nx][ny];
}
