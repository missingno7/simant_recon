/* Root module, code frame 1383: colony strategy, recruiting, new modes and movement directions. */

extern int far ChaseSpid;
extern int far MePlane;
extern int far SRand1(int range);
extern int far MeLocX;
extern int far FuzLocX;
extern int far MeLocY;
extern int far FuzLocY;
extern int far fd_50F6_0F0C;
extern long far GetDis(int x1, int y1, int x2, int y2);
extern int far fd_50F6_0F12;
extern int far fd_50F6_0F34;
extern int far StrategicModeB;
extern int far fd_50F6_10A6;
extern int far HealthB;
extern int far fd_50F6_0330;
extern int far fd_50F6_036C;
extern int far fd_50F6_0224;
extern int far fd_50F6_0AEC[6];
extern int far IdealCaste[4];
extern int far CasteTabB[4];
extern int far fd_3D57_0C0E;
extern int far fd_50F6_0B12[6];
extern unsigned int far fd_50F6_049E[3];
extern int far ModeTabB[3];
extern int far ModeMe;
extern int far fd_50F6_08E8;
extern int far fd_50F6_0AFA[6];
extern int far fd_50F6_0504;
extern int far HealthR;
extern int far fd_50F6_035E;
extern int far fd_50F6_0232;
extern int far fd_50F6_0350;
extern int far SRand32(void);
extern int far SRand128(void);
extern void far f_00DF_00B1(int id, int arg);
extern void far * far * far AdviceStrs;
extern void far f_15D9_009C(void far *, long, int);
extern unsigned char far fd_3E1D_AD3B[];
extern unsigned char far fd_3E1D_A952[];
extern unsigned char far fd_3E1D_B124[];
extern unsigned char far fd_3E1D_A180[];
extern unsigned char far fd_3E1D_A569[];
extern unsigned char far MapA[128][64];
extern unsigned char far fd_3E1D_BAEC[];
extern unsigned char far fd_3E1D_B8F7[];
extern unsigned char far fd_3E1D_BCE1[];
extern int far ListIndexA;
extern int far fd_50F6_0DA8;
extern int far fd_50F6_0D40[20];
extern int far fd_50F6_0EAA;
extern unsigned char far fd_3E1D_C4B5[];
extern unsigned char far fd_3E1D_C2C0[];
extern int far fd_50F6_0378;
extern int far SRand8(void);
extern char far ModeTabWB[][8];
extern char far ModeTabSB[][8];
extern char far CasteModeTabB[];
extern unsigned char far fd_4DA7_0000[64][32];
extern unsigned char far fd_3E1D_E89F[64][32];
extern char far Dx8[8];
extern char far Dy8[8];
extern char far TurnTab[][8];
extern unsigned char far fd_3E1D_F09F[64][32];
extern unsigned char far fd_3E1D_E09F[64][32];
extern int far SRand2(void);
extern int far GetDir(int x1, int y1, int x2, int y2);
extern int far fd_3D57_02B0[2];
extern int far SRand4(void);
extern int far fd_3D57_02AC[2];
extern unsigned char far fd_3E1D_D09F[64][32];
extern int far RedPlane;
extern int far RedLocY;
extern int far RedLocX;
extern int far fd_50F6_0C2A[6];

int far GstrB(void);
void far SetCasteProd(void);
void far SetModeProd(void);
int far GstrR(void);
void far StartAttack(void);
int far GetNewModeB(int caste);
int far GetNewModeR(int caste);
int far GetNestDir(int x, int y, int dir, int type);
int far Bounce(int x, int y);

void far GetStrategy(void)
{
    int dis;

    ChaseSpid = 0;
    if (MePlane == 1) {
        FuzLocX = SRand1(5) + MeLocX - 2;
        FuzLocY = SRand1(5) + MeLocY - 2;
        if (FuzLocX < 0)
            FuzLocX = 0;
        if (FuzLocX > 127)
            FuzLocX = 127;
        if (FuzLocY < 0)
            FuzLocY = 0;
        if (FuzLocY > 63)
            FuzLocY = 63;
        if (fd_50F6_0F0C) {
            dis = (int)GetDis(fd_50F6_0F12 >> 4, fd_50F6_0F34 >> 4, MeLocX, MeLocY);
            if (dis < 100)
                ChaseSpid = 1;
        }
    }
    FuzLocX = MeLocX;
    StrategicModeB = GstrB();
    fd_50F6_10A6 = GstrR();
    SetCasteProd();
    SetModeProd();
}

int far GstrB(void)
{
    if (HealthB < 10 && (fd_50F6_0330 >> 1) > fd_50F6_0350 && fd_50F6_0350 > 0 && fd_50F6_036C > 0)
        return 0;
    if (HealthB < 30)
        return 5;
    if (HealthB < 50)
        return 4;
    if (fd_50F6_0224 < fd_50F6_0330)
        return 3;
    if (fd_50F6_0224 < fd_50F6_0330 * 2)
        return 2;
    if (fd_50F6_0330 > 100 && fd_50F6_0350 > 0 && fd_50F6_036C > 0 && fd_50F6_0330 / 3 > fd_50F6_0350)
        return 0;
    return 1;
}

void far SetCasteProd(void)
{
    int i;
    int diff;
    int pct[5];
    int want[5];

    {
        int total;
        int ideal;

        total = 0;
        ideal = 0;
        for (i = 0; i < 4; i++) {
            total += fd_50F6_0AEC[i + 1];
            ideal += IdealCaste[i];
        }
        for (i = 0; i < 4; i++) {
            if (total <= 0)
                pct[i] = 0;
            else
                pct[i] = 100L * fd_50F6_0AEC[i + 1] / total;
            if (ideal <= 0)
                want[i] = 0;
            else
                want[i] = 100L * IdealCaste[i] / ideal;
        }
    }
    {
        int best;
        int chosen;

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

void far SetModeProd(void)
{
    int scaled[6];
    int diff[6];
    int total;
    int i;
    int best;
    int max;

    total = 0;
    for (i = 0; i < 3; i++)
        total += fd_50F6_0B12[i];
    for (i = 0; i < 3; i++)
        scaled[i] = (unsigned long)fd_50F6_049E[i] * (long)total / 65535UL;
    for (i = 0; i < 3; i++)
        diff[i] = scaled[i] - fd_50F6_0B12[i];
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

int far GstrR(void)
{
    if (fd_50F6_08E8 == 0 && fd_50F6_0AFA[3] + fd_50F6_0AFA[4] > 20)
        fd_50F6_08E8 = 200;
    if (fd_50F6_0504) {
        fd_50F6_0504--;
        return 0;
    }
    if (HealthR < 10 && (fd_50F6_0350 >> 1) > fd_50F6_0330 && fd_50F6_0330 > 0 && fd_50F6_035E > 0) {
        StartAttack();
        return 0;
    }
    if (HealthR < 30)
        return 5;
    if (HealthR < 50)
        return 4;
    if (fd_50F6_0232 < fd_50F6_0350)
        return 3;
    if (fd_50F6_0232 < fd_50F6_0350 * 2)
        return 2;
    if (fd_50F6_0350 > 100 && fd_50F6_0330 > 0 && fd_50F6_035E > 0 && fd_50F6_0350 / 3 > fd_50F6_0330) {
        StartAttack();
        return 0;
    }
    if (SRand32() == 0 && fd_50F6_0350 > 20 && fd_50F6_0350 > fd_50F6_0330 && SRand128() == 0) {
        StartAttack();
        return 0;
    }
    return 1;
}

void far StartAttack(void)
{
    fd_50F6_0504 = SRand1(100) + 30;
    f_00DF_00B1(0x2b0a, 0x3f);
    f_15D9_009C(AdviceStrs[5], 120L, 0);
}

void far ForceModeA(int index, int caste, int mode)
{
    switch (caste) {
    case 1:
        fd_3E1D_AD3B[index] += 8;
        fd_3E1D_A952[index] = mode;
        fd_3E1D_B124[index] = 0;
        break;
    case 3:
    case 7:
        fd_3E1D_AD3B[index] -= 8;
        if (MapA[fd_3E1D_A180[index]][fd_3E1D_A569[index]] < 0x48)
            MapA[fd_3E1D_A180[index]][fd_3E1D_A569[index]] = 0x48;
    case 2:
    case 6:
        fd_3E1D_A952[index] = mode;
        fd_3E1D_B124[index] = 0;
        break;
    case 5:
    case 9:
        fd_3E1D_AD3B[index] -= 0x18;
        fd_3E1D_A952[index] = mode;
        fd_3E1D_B124[index] = 0;
        break;
    }
    if (mode == 6 && MePlane == 1)
        fd_3E1D_B124[index] = ((MeLocY & 0x3c) << 2) | (MeLocX >> 3);
}

void far ForceModeB(int index, int caste, int mode)
{
    switch (caste) {
    case 1:
        fd_3E1D_BAEC[index] += 8;
        fd_3E1D_B8F7[index] = mode;
        fd_3E1D_BCE1[index] = 0;
        break;
    case 3:
    case 7:
        fd_3E1D_BAEC[index] -= 8;
    case 2:
    case 6:
        fd_3E1D_B8F7[index] = mode;
        fd_3E1D_BCE1[index] = 0;
        break;
    case 5:
    case 9:
        fd_3E1D_BAEC[index] -= 0x18;
        fd_3E1D_B8F7[index] = mode;
        fd_3E1D_BCE1[index] = 0;
        break;
    }
    if (mode == 6 && MePlane == 1)
        fd_3E1D_BCE1[index] = ((MeLocY & 0x3c) << 2) | (MeLocX >> 3);
}

void far Recruit(int count)
{
    int i;
    int type;
    int n;
    int caste;

    n = count;
    i = ListIndexA;
    while (i > 0) {
        if (n <= 0)
            break;
        i--;
        type = fd_3E1D_AD3B[i];
        if (type != 0 && !(type & 0x80)) {
            caste = (type & 0x78) >> 3;
            if (caste == 2 || caste == 6) {
                if (fd_3E1D_A952[i] != 6) {
                    fd_3E1D_A952[i] = 6;
                    fd_3E1D_B124[i] = 0;
                    n--;
                }
            }
        }
    }
    i = fd_50F6_0DA8;
    while (i > 0) {
        if (n <= 0)
            break;
        i--;
        type = fd_3E1D_BAEC[i];
        if (type != 0 && !(type & 0x80)) {
            caste = (type & 0x78) >> 3;
            if (caste == 2 || caste == 6) {
                if (fd_3E1D_B8F7[i] != 6) {
                    fd_3E1D_B8F7[i] = 6;
                    fd_3E1D_BCE1[i] = 0;
                    n--;
                }
            }
        }
    }
}

void far UnRecruit(int all)
{
    int n;
    int i;
    int type;

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
        type = fd_3E1D_AD3B[i];
        if (type != 0 && !(type & 0x80) && fd_3E1D_A952[i] == 6) {
            fd_3E1D_A952[i] = 0;
            n--;
        }
    }
    i = fd_50F6_0DA8;
    while (i > 0) {
        if (n <= 0)
            break;
        i--;
        type = fd_3E1D_BAEC[i];
        if (type != 0 && !(type & 0x80) && fd_3E1D_B8F7[i] == 6) {
            fd_3E1D_B8F7[i] = 0;
            n--;
        }
    }
    i = fd_50F6_0EAA;
    while (i > 0) {
        if (n <= 0)
            break;
        i--;
        type = fd_3E1D_C4B5[i];
        if (type != 0 && !(type & 0x80) && fd_3E1D_C2C0[i] == 6) {
            fd_3E1D_C2C0[i] = 7;
            n--;
        }
    }
}

void far RecruitRed(int count)
{
    int cur;
    int need;
    int i;
    int type;
    int mode;

    need = count;
    i = ListIndexA;
    while (i > 0) {
        if (need <= 0)
            break;
        i--;
        type = fd_3E1D_AD3B[i];
        if (type != 0 && type > 0x7f) {
            cur = fd_3E1D_A952[i];
            mode = (type & 0x78) >> 3;
            if (mode == 2 || mode == 6) {
                if (cur != 0x13 && cur != 6) {
                    fd_3E1D_A952[i] = 6;
                    fd_3E1D_B124[i] = 0;
                    need--;
                }
            }
        }
    }
}

void far UnRecruitRed(void)
{
    int i;
    int type;

    i = ListIndexA;
    while (i > 0) {
        i--;
        type = fd_3E1D_AD3B[i];
        if (type != 0 && type > 0x7f && fd_3E1D_A952[i] == 6)
            fd_3E1D_A952[i] = 0;
    }
}

int far GetNewMode(int caste, int type)
{
    if (type & 0x80)
        return GetNewModeR(caste);
    return GetNewModeB(caste);
}

int far GetNewModeB(int caste)
{
    if (fd_50F6_0378 == 1) {
        if (caste == 2)
            return ModeTabWB[StrategicModeB][SRand8()];
        if (caste == 6)
            return ModeTabSB[StrategicModeB][SRand8()];
        return CasteModeTabB[caste];
    }
    if (caste == 2 || caste == 6)
        return ModeMe;
    return CasteModeTabB[caste];
}

int far GetNewModeR(int caste)
{
    if (caste == 2)
        return ModeTabWB[fd_50F6_10A6][SRand8()];
    if (caste == 6)
        return ModeTabSB[fd_50F6_10A6][SRand8()];
    return CasteModeTabB[caste];
}

int far GetForageDir(int x, int y, int dir, int attribute)
{
    int xCell;
    int yCell;
    int plane;
    int best;
    int bestDir;
    int i;
    int nx;
    int ny;
    int current;
    int value;

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
        current = fd_4DA7_0000[xCell][yCell];
    else
        current = fd_3E1D_E89F[xCell][yCell];

    best = 0;
    bestDir = SRand8();
    for (i = 0; i < 8; ++i) {
        nx = xCell + Dx8[i];
        nx &= 0x3f;
        ny = yCell + Dy8[i];
        ny &= 0x1f;
        if (plane)
            value = fd_4DA7_0000[nx][ny];
        else
            value = fd_3E1D_E89F[nx][ny];
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

int far GetNestDir(int x, int y, int dir, int type)
{
    int xCell;
    int yCell;
    int plane;
    int best;
    int bestDir;
    int i;
    int nx;
    int ny;
    int current;
    int value;

    xCell = x >> 1;
    yCell = y >> 1;
    plane = type >> 7;
    nx = Bounce(x, y);
    if (nx) return (nx - 1) & 7;
    if (plane)
        current = fd_3E1D_F09F[xCell][yCell];
    else
        current = fd_3E1D_E09F[xCell][yCell];
    if (current) {
        best = 0;
        bestDir = 0;
        for (i = 0; i < 8; ++i) {
            nx = xCell + Dx8[i];
            nx &= 0x3f;
            ny = yCell + Dy8[i];
            ny &= 0x1f;
            if (plane)
                value = fd_3E1D_F09F[nx][ny];
            else
                value = fd_3E1D_E09F[nx][ny];
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

int far GetAlarmDir(int x, int y, int dir)
{
    int xc;
    int yc;
    int r;
    int i;
    int best;
    int bestDir;
    int value;

    xc = x >> 1;
    yc = y >> 1;
    r = Bounce(x, y);
    if (r) return (r - 1) & 7;
    best = 0;
    bestDir = 0;
    for (i = 0; i < 8; i++) {
        value = fd_3E1D_D09F[(xc + Dx8[i]) & 0x3f][(yc + Dy8[i]) & 0x1f];
        if (value > best) {
            best = value;
            bestDir = i;
        }
    }
    if (best != 0) return TurnTab[dir][bestDir];
    return TurnTab[dir][SRand8()];
}

int far GetRandDir(int x, int y, int dir)
{
    int r;

    r = Bounce(x, y);
    if (r) return (r - 1) & 7;
    return TurnTab[dir][SRand8()];
}

int far GetDefendDir(int x, int y, int dir)
{
    int r;

    r = Bounce(x, y);
    if (r) return (r - 1) & 7;
    switch (MePlane) {
    case 1:
        if (ChaseSpid == 1)
            r = GetDir(x, y, fd_50F6_0F12 >> 4, fd_50F6_0F34 >> 4);
        else {
            r = GetDis(x, y, FuzLocX, FuzLocY);
            if (fd_50F6_0B12[5] >> 1 < r)
                r = GetDir(x, y, FuzLocX, FuzLocY);
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

int far GetRedDefendDir(int x, int y, int dir)
{
    int r;

    r = Bounce(x, y);
    if (r) return (r - 1) & 7;
    switch (RedPlane) {
    case 1:
        r = GetDis(x, y, RedLocX, RedLocY);
        if (fd_50F6_0C2A[5] >> 1 < r)
            r = GetDir(x, y, RedLocX, RedLocY);
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

int far Bounce(int x, int y)
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
