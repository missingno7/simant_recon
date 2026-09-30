/* Root module, code frame 0EC1: ant lists (A = surface, B = black nest, R = red nest). */

extern int far ListIndexA;
extern unsigned char far AlistT[];
extern unsigned char far AlistX[];
extern unsigned char far AlistY[];
extern unsigned char far AlistM[];
extern unsigned char far AlistS[];
extern int far ListIndexB;
extern unsigned char far BlistT[];
extern unsigned char far BlistX[];
extern unsigned char far BlistY[];
extern unsigned char far BlistM[];
extern unsigned char far BlistS[];
extern int far ListIndexR;
extern unsigned char far RlistT[];
extern unsigned char far RlistX[];
extern unsigned char far RlistY[];
extern unsigned char far RlistM[];
extern unsigned char far RlistS[];
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

void far CompactListB(void)
{
    int i;
    int shift;
    int j;

    shift = 0;
    for (i = 0; i < ListIndexB; i++) {
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
    ListIndexB += shift;
}

void far CompactListR(void)
{
    int i;
    int shift;
    int j;

    shift = 0;
    for (i = 0; i < ListIndexR; i++) {
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
    ListIndexR += shift;
}

void far RemoveFromAList(int index)
{
    long count;
    int next;

    LifeA[AlistX[index]][AlistY[index]] = 0;
    if (ListIndexA > 0)
        ListIndexA--;
    count = ListIndexA - index;
    next = index + 1;
    f_0244_0000(&AlistX[next], &AlistX[index], count);
    f_0244_0000(&AlistY[next], &AlistY[index], count);
    f_0244_0000(&AlistM[next], &AlistM[index], count);
    f_0244_0000(&AlistT[next], &AlistT[index], count);
    f_0244_0000(&AlistS[next], &AlistS[index], count);
}

int far FindInAList(int x, int y)
{
    int i;

    i = ListIndexA;
    while (i > 0) {
        i--;
        if (AlistX[i] == x && AlistY[i] == y && AlistT[i] != 0)
            return i;
    }
    return -1;
}

int far FindInBList(int x, int y, int t)
{
    int i;

    i = ListIndexB;
    while (i > 0) {
        i--;
        if (BlistX[i] == x && BlistY[i] == y && BlistT[i] == t)
            return i;
    }
    return -1;
}

int far FindInRList(int x, int y, int t)
{
    int i;

    i = ListIndexR;
    while (i > 0) {
        i--;
        if (RlistX[i] == x && RlistY[i] == y && RlistT[i] == t)
            return i;
    }
    return -1;
}

void far DrownBList(int y)
{
    int i;
    int caste;

    i = ListIndexB;
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

void far DrownRList(int y)
{
    int i;
    int caste;

    i = ListIndexR;
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

void far AddAntToAList(int x, int y, int type, int mode, int stat)
{
    int n;

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

void far AddAntToBList(int x, int y, int type, int mode, int stat)
{
    int n;

    if (ListIndexB >= 500)
        return;
    n = ListIndexB;
    BlistX[n] = x;
    BlistY[n] = y;
    BlistM[n] = mode;
    BlistT[n] = type;
    BlistS[n] = stat;
    LifeB[x][y] = type;
    ListIndexB++;
}

void far AddAntToRList(int x, int y, int type, int mode, int stat)
{
    int n;

    if (ListIndexR >= 500)
        return;
    n = ListIndexR;
    RlistX[n] = x;
    RlistY[n] = y;
    RlistM[n] = mode;
    RlistT[n] = type;
    RlistS[n] = stat;
    LifeR[x][y] = type;
    ListIndexR++;
}

int far GetFromAlist(int colony)
{
    int i;
    int t;

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

void far ClearListB(void)
{
    ListIndexB = 0;
}

void far ClearListR(void)
{
    ListIndexR = 0;
}
