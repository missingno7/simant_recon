/* Root module, code frame 0EC1: ant lists (A = surface, B = black nest, R = red nest). */

extern int far ListIndexA;
extern unsigned char far fd_3E1D_AD3B[];
extern unsigned char far fd_3E1D_A180[];
extern unsigned char far fd_3E1D_A569[];
extern unsigned char far fd_3E1D_A952[];
extern unsigned char far fd_3E1D_B124[];
extern int far fd_50F6_0DA8;
extern unsigned char far fd_3E1D_BAEC[];
extern unsigned char far fd_3E1D_B50D[];
extern unsigned char far fd_3E1D_B702[];
extern unsigned char far fd_3E1D_B8F7[];
extern unsigned char far fd_3E1D_BCE1[];
extern int far fd_50F6_0EAA;
extern unsigned char far fd_3E1D_C4B5[];
extern unsigned char far fd_3E1D_BED6[];
extern unsigned char far fd_3E1D_C0CB[];
extern unsigned char far fd_3E1D_C2C0[];
extern unsigned char far fd_3E1D_C6AA[];
extern unsigned char far LifeA[128][64];
extern void far f_0244_0000(unsigned char far *src, unsigned char far *dst, long count);
extern char far Dy8[8];
extern char far Dx8[8];
extern int far f_10F7_2867(int x, int y);
extern unsigned char far MapA[128][64];
extern unsigned char far LifeB[64][64];
extern unsigned char far LifeR[64][64];
extern int far IsYellowAnt(int value);

void far CompactListA(void)
{
    int i;
    int shift;
    int j;

    shift = 0;
    for (i = 0; i < ListIndexA; i++) {
        if (fd_3E1D_AD3B[i]) {
            if (shift) {
                j = shift + i;
                fd_3E1D_AD3B[j] = fd_3E1D_AD3B[i];
                fd_3E1D_A180[j] = fd_3E1D_A180[i];
                fd_3E1D_A569[j] = fd_3E1D_A569[i];
                fd_3E1D_A952[j] = fd_3E1D_A952[i];
                fd_3E1D_B124[j] = fd_3E1D_B124[i];
            }
        } else
            shift--;
    }
    ListIndexA += shift;
}

void far CompactListB(void)
{
    int i;
    int shift;
    int j;

    shift = 0;
    for (i = 0; i < fd_50F6_0DA8; i++) {
        if (fd_3E1D_BAEC[i]) {
            if (shift) {
                j = shift + i;
                fd_3E1D_BAEC[j] = fd_3E1D_BAEC[i];
                fd_3E1D_B50D[j] = fd_3E1D_B50D[i];
                fd_3E1D_B702[j] = fd_3E1D_B702[i];
                fd_3E1D_B8F7[j] = fd_3E1D_B8F7[i];
                fd_3E1D_BCE1[j] = fd_3E1D_BCE1[i];
            }
        } else
            shift--;
    }
    fd_50F6_0DA8 += shift;
}

void far CompactListR(void)
{
    int i;
    int shift;
    int j;

    shift = 0;
    for (i = 0; i < fd_50F6_0EAA; i++) {
        if (fd_3E1D_C4B5[i]) {
            if (shift) {
                j = shift + i;
                fd_3E1D_C4B5[j] = fd_3E1D_C4B5[i];
                fd_3E1D_BED6[j] = fd_3E1D_BED6[i];
                fd_3E1D_C0CB[j] = fd_3E1D_C0CB[i];
                fd_3E1D_C2C0[j] = fd_3E1D_C2C0[i];
                fd_3E1D_C6AA[j] = fd_3E1D_C6AA[i];
            }
        } else
            shift--;
    }
    fd_50F6_0EAA += shift;
}

void far RemoveFromAList(int index)
{
    long count;
    int next;

    LifeA[fd_3E1D_A180[index]][fd_3E1D_A569[index]] = 0;
    if (ListIndexA > 0)
        ListIndexA--;
    count = ListIndexA - index;
    next = index + 1;
    f_0244_0000(&fd_3E1D_A180[next], &fd_3E1D_A180[index], count);
    f_0244_0000(&fd_3E1D_A569[next], &fd_3E1D_A569[index], count);
    f_0244_0000(&fd_3E1D_A952[next], &fd_3E1D_A952[index], count);
    f_0244_0000(&fd_3E1D_AD3B[next], &fd_3E1D_AD3B[index], count);
    f_0244_0000(&fd_3E1D_B124[next], &fd_3E1D_B124[index], count);
}

int far FindInAList(int x, int y)
{
    int i;

    i = ListIndexA;
    while (i > 0) {
        i--;
        if (fd_3E1D_A180[i] == x && fd_3E1D_A569[i] == y && fd_3E1D_AD3B[i] != 0)
            return i;
    }
    return -1;
}

int far FindInBList(int x, int y, int t)
{
    int i;

    i = fd_50F6_0DA8;
    while (i > 0) {
        i--;
        if (fd_3E1D_B50D[i] == x && fd_3E1D_B702[i] == y && fd_3E1D_BAEC[i] == t)
            return i;
    }
    return -1;
}

int far FindInRList(int x, int y, int t)
{
    int i;

    i = fd_50F6_0EAA;
    while (i > 0) {
        i--;
        if (fd_3E1D_BED6[i] == x && fd_3E1D_C0CB[i] == y && fd_3E1D_C4B5[i] == t)
            return i;
    }
    return -1;
}

void far DrownBList(int y)
{
    int i;
    int caste;

    i = fd_50F6_0DA8;
    while (i > 0) {
        i--;
        if (fd_3E1D_B702[i] != y)
            continue;
        if (fd_3E1D_BAEC[i] == 0)
            continue;
        caste = (fd_3E1D_BAEC[i] & 0x78) >> 3;
        if (caste <= 0 || caste >= 12)
            continue;
        fd_3E1D_B8F7[i] = 0x11;
    }
}

void far DrownRList(int y)
{
    int i;
    int caste;

    i = fd_50F6_0EAA;
    while (i > 0) {
        i--;
        if (fd_3E1D_C0CB[i] != y)
            continue;
        if (fd_3E1D_C4B5[i] == 0)
            continue;
        caste = (fd_3E1D_C4B5[i] & 0x78) >> 3;
        if (caste <= 0 || caste >= 12)
            continue;
        fd_3E1D_C2C0[i] = 0x11;
    }
}

int far ExitHole(int x, int y, int type, int mode, int stat)
{
    int i;
    int nx;
    int ny;

    for (i = 0; i < 8; i++) {
        nx = x + Dx8[i];
        if (f_10F7_2867(nx, ny = y + Dy8[i]) == 1 && MapA[nx][ny] < 0x50)
            break;
    }
    if (i == 8)
        return 0;
    fd_3E1D_A180[ListIndexA] = nx;
    fd_3E1D_A569[ListIndexA] = ny;
    fd_3E1D_AD3B[ListIndexA] = type;
    fd_3E1D_A952[ListIndexA] = mode;
    if (mode == 6)
        fd_3E1D_B124[ListIndexA] = stat;
    else {
        fd_3E1D_B124[ListIndexA] = 0;
        if (mode != 3 && mode != 7) {
            if (type & 0x80) {
                if (x > 0x40)
                    fd_3E1D_B124[ListIndexA] = 0x78;
            } else {
                if (x < 0x40)
                    fd_3E1D_B124[ListIndexA] = 0x78;
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

void far AddAntToAList(int x, int y, int type, int mode, int stat)
{
    int n;

    if (ListIndexA >= 1000)
        return;
    n = ListIndexA;
    fd_3E1D_A180[n] = x;
    fd_3E1D_A569[n] = y;
    fd_3E1D_A952[n] = mode;
    fd_3E1D_AD3B[n] = type;
    fd_3E1D_B124[n] = stat;
    LifeA[x][y] = type;
    ListIndexA++;
}

void far AddAntToBList(int x, int y, int type, int mode, int stat)
{
    int n;

    if (fd_50F6_0DA8 >= 500)
        return;
    n = fd_50F6_0DA8;
    fd_3E1D_B50D[n] = x;
    fd_3E1D_B702[n] = y;
    fd_3E1D_B8F7[n] = mode;
    fd_3E1D_BAEC[n] = type;
    fd_3E1D_BCE1[n] = stat;
    LifeB[x][y] = type;
    fd_50F6_0DA8++;
}

void far AddAntToRList(int x, int y, int type, int mode, int stat)
{
    int n;

    if (fd_50F6_0EAA >= 500)
        return;
    n = fd_50F6_0EAA;
    fd_3E1D_BED6[n] = x;
    fd_3E1D_C0CB[n] = y;
    fd_3E1D_C2C0[n] = mode;
    fd_3E1D_C4B5[n] = type;
    fd_3E1D_C6AA[n] = stat;
    LifeR[x][y] = type;
    fd_50F6_0EAA++;
}

int far GetFromAlist(int colony)
{
    int i;
    int t;

    i = ListIndexA;
    while (i > 0) {
        i--;
        t = fd_3E1D_AD3B[i];
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

void far BuildAntListA(void)
{
    int x;
    int y;
    int ant;

    ListIndexA = 0;
    for (x = 0; x < 128; x++) {
        for (y = 0; y < 64; y++) {
            ant = LifeA[x][y];
            if (ant && IsYellowAnt(ant) != 1) {
                fd_3E1D_A180[ListIndexA] = x;
                fd_3E1D_A569[ListIndexA] = y;
                fd_3E1D_A952[ListIndexA] = 2;
                fd_3E1D_AD3B[ListIndexA] = ant;
                fd_3E1D_B124[ListIndexA] = 0;
                if (ListIndexA < 997)
                    ListIndexA++;
            }
        }
    }
}

void far ClearListB(void)
{
    fd_50F6_0DA8 = 0;
}

void far ClearListR(void)
{
    fd_50F6_0EAA = 0;
}
