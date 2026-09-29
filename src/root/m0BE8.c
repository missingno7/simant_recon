/* Root module, code frame 0BE8: ant counts, water, eggs, directions. */

extern int far SRand1(int range);
extern int far SRand2(void);
extern int far RRand(int range);
extern void far f_0E2E_000A(void);
extern void far f_0EC1_037B(int y);
extern void far f_0EC1_03D9(int y);
extern void far f_0250_000E(int plane, int x, int y);

extern void far f_00DF_00E8(int a, int b, int c);

extern void far f_00DF_00B1(int id, int arg);
extern void far o14_384C_0B6A(int a, int b, int c);

extern int far fd_50F6_0AFA[6];
extern int far fd_50F6_0AEC[6];
extern int far fd_50F6_0EB6[32];
extern int far fd_50F6_0D6A;
extern unsigned char far fd_3E1D_AD3B[];
extern int far fd_50F6_0DA8;
extern unsigned char far fd_3E1D_BAEC[];
extern int far fd_50F6_0EAA;
extern unsigned char far fd_3E1D_C4B5[];
extern int far fd_50F6_0A06;
extern int far fd_50F6_04E2;
extern int far fd_50F6_04C2;
extern int far fd_50F6_0354;
extern int far fd_50F6_0EAC;
extern int far fd_50F6_0376;
extern int far fd_50F6_0366;
extern int far fd_50F6_0400;
extern int far fd_50F6_07CA[2];
extern unsigned char far fd_3D57_0184[][16];
extern int far fd_50F6_0330;
extern int far fd_50F6_0350;
extern int far fd_50F6_0352;
extern int far fd_50F6_0F24;
extern int far fd_3D57_0C1E;
extern int far fd_50F6_0242;
extern unsigned char far fd_50F6_02C0[];
extern unsigned char far fd_50F6_0256[];
extern unsigned char far fd_3E1D_0180[128][64];
extern unsigned char far fd_3E1D_D09F[64][32];
extern unsigned char far fd_3E1D_D89F[64][32];
extern unsigned char far fd_3E1D_E09F[64][32];
extern unsigned char far fd_3E1D_E89F[64][32];
extern unsigned char far fd_3E1D_F09F[64][32];
extern unsigned char far fd_4DA7_0000[64][32];
extern unsigned char far fd_3E1D_2180[64][64];
extern int far SRand16(void);
extern int far SRand8(void);
extern int far fd_50F6_1040;
extern int far fd_50F6_1050;
extern int far fd_50F6_1060;
extern int far fd_50F6_0F3A;
extern unsigned char near g_1B9A[];
extern unsigned char near g_1B9E[];
extern unsigned char far fd_3E1D_8180[64][64];
extern char far fd_3D57_0008[8];
extern char far fd_3D57_0000[8];
extern unsigned char far fd_3E1D_4180[64][64];
extern unsigned char far fd_3E1D_5180[64][64];
extern long far fd_50F6_0214;
extern int far fd_50F6_0228;
extern long far TickCount(void);
extern unsigned char far fd_3E1D_9180[64][64];
extern void far f_14EE_0519(int x, int y);
extern void far f_14EE_0647(int x, int y);
extern void far f_0EC1_05D4(int x, int y, int life, int state, int dir);
extern void far f_0EC1_0651(int x, int y, int life, int state, int dir);
extern unsigned char far fd_3E1D_3180[64][64];

void far f_0BE8_0002(void);
void far f_0BE8_0554(int i);
void far f_0BE8_039F(void);
void far f_0BE8_0652(int y);
void far f_0BE8_06EE(int y);
void far f_0BE8_08BD(int x, int y);
int far f_0BE8_0BC1(int x, int y);

/* SCAFFOLD BEGIN: unrecovered f_0BE8_0002 kept in place for CONST order */
/* f_0BE8_0002 (CountAnts?): best draft, 13 bytes differ: operand order of the
   commutative far-memory sums (AEC[1], AFA[1], AFA[2], totals) depends on the
   compiler's symbol-table state (number/names of earlier declarations), not on
   source order; see REPORT.md (ORD-1 observation). */
void far f_0BE8_0002(void)
{
    int i;
    int n;
    int v;

    fd_50F6_0AFA[0] = 0;
    fd_50F6_0AEC[0] = 0;
    for (i = 0; i < 32; i++)
        fd_50F6_0EB6[i] = 0;
    for (n = fd_50F6_0D6A; n > 0; ) {
        v = fd_3E1D_AD3B[--n];
        if (v)
            fd_50F6_0EB6[v >> 3]++;
    }
    for (n = fd_50F6_0DA8; n > 0; ) {
        v = fd_3E1D_BAEC[--n];
        if (v)
            fd_50F6_0EB6[v >> 3]++;
    }
    for (n = fd_50F6_0EAA; n > 0; ) {
        v = fd_3E1D_C4B5[--n];
        if (v)
            fd_50F6_0EB6[v >> 3]++;
    }
    if (fd_50F6_0A06 == 0) {
        if (fd_50F6_04E2 == 0)
            fd_50F6_0EB6[fd_50F6_04C2 >> 3]++;
        else
            fd_50F6_0EB6[(fd_50F6_04C2 | 0x80) >> 3]++;
    }
    fd_50F6_0AEC[0] = fd_50F6_0EB6[0];
    fd_50F6_0AEC[1] = fd_50F6_0EB6[1] + fd_50F6_0EB6[2] + fd_50F6_0EB6[3] + fd_50F6_0EB6[5];
    fd_50F6_0AEC[2] = fd_50F6_0EB6[6] + fd_50F6_0EB6[7] + fd_50F6_0EB6[9];
    fd_50F6_0AEC[3] = fd_50F6_0EB6[4];
    fd_50F6_0AEC[4] = fd_50F6_0EB6[8];
    if (fd_50F6_0AEC[5] && fd_50F6_0EB6[12] == 0 && fd_50F6_0354 == 0) {
        f_00DF_00B1(0x2b0c, 0x7e);
        o14_384C_0B6A(0, 0x271a, 1);
        if (fd_50F6_0EAC <= 1) {
            o14_384C_0B6A(0, 0x271b, 1);
            fd_50F6_0376 = 1;
            fd_50F6_0366 = 0;
        }
    }
    fd_50F6_0AEC[5] = fd_50F6_0EB6[12];
    fd_50F6_0AFA[0] = fd_50F6_0EB6[16];
    fd_50F6_0AFA[1] = fd_50F6_0EB6[18] + fd_50F6_0EB6[19] + fd_50F6_0EB6[21] + fd_50F6_0EB6[17];
    fd_50F6_0AFA[2] = fd_50F6_0EB6[23] + fd_50F6_0EB6[22] + fd_50F6_0EB6[25];
    fd_50F6_0AFA[3] = fd_50F6_0EB6[20];
    fd_50F6_0AFA[4] = fd_50F6_0EB6[24];
    if (fd_50F6_0AFA[5] && fd_50F6_0EB6[28] == 0 && fd_50F6_0354 == 0) {
        f_00DF_00B1(0x2b0d, 0x7e);
        o14_384C_0B6A(0, 0x271c, 1);
        if (fd_50F6_0EAC <= 1) {
            o14_384C_0B6A(0, 0x271d, 1);
            fd_50F6_0376 = 1;
            fd_50F6_0366 = 1;
        }
        if (fd_50F6_0EAC == 2 && fd_50F6_0400 == 1 && fd_50F6_07CA[0] == 0xb && fd_50F6_07CA[1] == 8)
            fd_3D57_0184[SRand1(6)][0] = 0x14;
    }
    fd_50F6_0330 = fd_50F6_0AEC[3] + fd_50F6_0AEC[1] + fd_50F6_0AEC[2] + fd_50F6_0AEC[4] + fd_50F6_0AEC[5];
    fd_50F6_0AFA[5] = fd_50F6_0EB6[28];
    fd_50F6_0350 = fd_50F6_0AFA[5] + fd_50F6_0AFA[4] + fd_50F6_0AFA[1] + fd_50F6_0AFA[3] + fd_50F6_0AFA[2];
    fd_50F6_0354 = 0;
}

/* SCAFFOLD END */

void far f_0BE8_038F(void)
{
    f_0BE8_0002();
    f_0BE8_039F();
}

void far f_0BE8_039F(void)
{
    f_0E2E_000A();
}

void far f_0BE8_03AC(void)
{
    int i;
    int x;
    int y;
    int v;

    if (fd_50F6_0352 && !fd_50F6_0F24) {
        if (SRand1(50) == 0)
            f_00DF_00E8(0x29, 0, 0x40);
        fd_3D57_0C1E = 1;
        if (SRand1(10) == 0 && fd_50F6_0242 > 4) {
            --fd_50F6_0242;
            f_0BE8_0652(fd_50F6_0242);
        }
        for (i = 0; i < 100; i++) {
            x = fd_50F6_0256[i];
            y = fd_50F6_02C0[i];
            v = fd_3E1D_0180[x][y];
            if (v >= 0x74 && v < 0x77)
                fd_3E1D_0180[x][y]++;
            else {
                if (v == 0x77)
                    fd_3E1D_0180[x][y] = SRand1(14);
                f_0BE8_0554(i);
            }
        }
    } else if (!fd_50F6_0F24) {
        if (fd_3D57_0C1E == 1) {
            fd_3D57_0C1E = 0;
            for (i = 0; i < 100; i++) {
                x = fd_50F6_0256[i];
                y = fd_50F6_02C0[i];
                v = fd_3E1D_0180[x][y];
                if (v >= 0x74 && v <= 0x77)
                    fd_3E1D_0180[x][y] = SRand1(14);
            }
        }
        if (fd_50F6_0242 < 0x40 && SRand1(10) == 0) {
            f_0BE8_06EE(fd_50F6_0242);
            fd_50F6_0242++;
        }
    }
}

void far f_0BE8_0554(int i)
{
    int x;
    int y;

    x = RRand(128);
    y = RRand(64);
    fd_50F6_0256[i] = x;
    fd_50F6_02C0[i] = y;
    if (fd_3E1D_0180[x][y] < 0xe) {
        fd_3E1D_0180[x][y] = 0x74;
        x >>= 1;
        y >>= 1;
        fd_3E1D_D89F[x][y] = fd_3E1D_D09F[x][y] = 0;
        if (fd_3E1D_E09F[x][y] >= 0x14)
            fd_3E1D_E09F[x][y] -= 0x14;
        else
            fd_3E1D_E09F[x][y] = 0;
        fd_3E1D_E89F[x][y] = 0;
        if (fd_3E1D_F09F[x][y] >= 0x14)
            fd_3E1D_F09F[x][y] -= 0x14;
        else
            fd_3E1D_F09F[x][y] = 0;
        fd_4DA7_0000[x][y] = 0;
    }
}

void far f_0BE8_063A(void)
{
    int i;

    for (i = 0; i < 100; ++i)
        f_0BE8_0554(i);
}

void far f_0BE8_0652(int y)
{
    int x;
    int v;
    int t;

    f_0EC1_037B(y);
    f_0EC1_03D9(y);
    for (x = 0; x < 64; x++) {
        v = fd_3E1D_2180[x][y];
        if (v < 0x20)
            t = 0x4e;
        else
            t = v + 0x2f;
        fd_3E1D_2180[x][y] = t;
        v = fd_3E1D_3180[x][y];
        if (v < 0x20)
            t = 0x4e;
        else
            t = v + 0x2f;
        fd_3E1D_3180[x][y] = t;
        f_0250_000E(2, x, y);
        f_0250_000E(3, x, y);
    }
}

void far f_0BE8_06EE(int y)
{
    int x;
    int v;
    int t;

    for (x = 0; x < 64; x++) {
        v = fd_3E1D_2180[x][y];
        if (v == 0x4e)
            t = SRand1(8);
        else
            t = v - 0x2f;
        fd_3E1D_2180[x][y] = t;
        v = fd_3E1D_3180[x][y];
        if (v == 0x4e)
            t = SRand1(8);
        else
            t = v - 0x2f;
        fd_3E1D_3180[x][y] = t;
        f_0250_000E(2, x, y);
        f_0250_000E(3, x, y);
    }
}

void far f_0BE8_0798(int x, int y)
{
    int v;

    v = fd_3E1D_0180[x][y];
    if (!fd_50F6_0F24) {
        if (v == 0x48)
            fd_3E1D_0180[x][y] = SRand16();
        else
            fd_3E1D_0180[x][y]--;
    } else {
        if (v % 4 == 0)
            fd_3E1D_0180[x][y] = (v - 0x18) >> 2;
        else
            fd_3E1D_0180[x][y]--;
    }
    if (fd_50F6_1040 > 0)
        fd_50F6_1040--;
}

int far f_0BE8_0812(int x, int y)
{
    int v;

    v = fd_3E1D_0180[x][y];
    if (fd_50F6_0F24 == 1) {
        if (v < 4) {
            fd_3E1D_0180[x][y] = (v + 6) << 2;
            fd_50F6_1040++;
            return 1;
        }
        if (v >= 8 && v < 0x18) {
            v = (v - 8) >> 2;
            fd_3E1D_0180[x][y] = (v + 6) << 2;
            fd_50F6_1040++;
            return 1;
        }
        if (v >= 0x18 && v < 0x27) {
            fd_3E1D_0180[x][y]++;
            fd_50F6_1040++;
            return 1;
        }
        if (v < 0x40) {
            f_0BE8_08BD(x, y);
            return 1;
        }
    } else {
        if (v < 0x4b) {
            if (v >= 0x48) {
                fd_3E1D_0180[x][y]++;
                fd_50F6_1040++;
                return 1;
            }
            fd_3E1D_0180[x][y] = 0x48;
            fd_50F6_1040++;
            return 1;
        }
    }
    return 0;
}

void far f_0BE8_08BD(int a, int b)
{
    int v;
    int go;
    int x;
    int y;

    go = 1;
    x = a;
    y = b;
    while (go) {
        v = fd_3E1D_0180[x][y];
        if (v < 4) {
            fd_3E1D_0180[x][y] = (v + 6) << 2;
            fd_50F6_1040++;
            go = 0;
        }
        x += g_1B9A[fd_50F6_0F3A];
        y += g_1B9E[fd_50F6_0F3A];
        if (x < 0 || x > 0x7f)
            go = 0;
        if (y < 0 || y > 0x3f)
            go = 0;
    }
}

/* SCAFFOLD BEGIN: f_0BE8_094B/f_0BE8_09D3 best drafts, 8 bytes differ each: the tile load into the SI variable
   is `mov si,word es:[..]; and si,0FFh` here but `mov al,byte es:[..]; sub ah,ah; mov si,ax` in
   the target. Everything else (immediate SEG load of the map, flag home, trailing
   `mov cx,DGROUP; mov ds,cx`) is reproduced. Tried: unsigned/char/register v, cast,
   assignment inside the if, far pointer temp, extra temp local. Also needs a _DATA placement
   for the DGROUP fixup of `mov cx,DGROUP` */
void far f_0BE8_094B(int x, int y)
{
    int v;
    int flag;

    flag = 0;
    v = fd_3E1D_2180[x][y];
    if (v == 0x10) {
        fd_3E1D_2180[x][y] = SRand8();
        flag = 1;
    } else if (v >= 0x11 && v <= 0x13) {
        fd_3E1D_2180[x][y]--;
        flag = 1;
    }
    if (flag == 1 && fd_50F6_1050 > 0)
        fd_50F6_1050--;
}

void far f_0BE8_09D3(int x, int y)
{
    int v;
    int flag;

    flag = 0;
    v = fd_3E1D_3180[x][y];
    if (v == 0x10) {
        fd_3E1D_3180[x][y] = SRand8();
        flag = 1;
    } else if (v >= 0x11 && v <= 0x13) {
        fd_3E1D_3180[x][y]--;
        flag = 1;
    }
    if (flag == 1 && fd_50F6_1060 > 0)
        fd_50F6_1060--;
}

/* SCAFFOLD END */

void far f_0BE8_0A5B(int x, int y, int life)
{
    if (fd_50F6_0DA8 < 500 && f_0BE8_0BC1(x, y)) {
        f_14EE_0519(x, y);
        f_0EC1_05D4(x, y, life, 8, 0);
        fd_3E1D_8180[x][y] = life;
    }
}

void far f_0BE8_0ABE(int x, int y, int life)
{
    if (fd_50F6_0EAA < 500 && f_0BE8_0BC1(x, y)) {
        f_14EE_0647(x, y);
        f_0EC1_0651(x, y, life, 8, 0);
        fd_3E1D_9180[x][y] = life;
    }
}

int far f_0BE8_0B21(int x1, int y1, int x2, int y2)
{
    int dx;
    int dy;

    dy = y2 - y1;
    dx = x2 - x1;
    if (dx == 0) {
        if (dy == 0)
            return 0;
        if (dy < 0)
            return 1;
        return 5;
    }
    if (dx > 0) {
        if (dy < 0)
            return 2;
        if (dy == 0)
            return 3;
        return 4;
    }
    if (dy > 0)
        return 6;
    if (dy == 0)
        return 7;
    return 8;
}

long far f_0BE8_0B83(int x1, int y1, int x2, int y2)
{
    return (long)(y2 - y1) * (y2 - y1) + (long)(x2 - x1) * (x2 - x1);
}

int far f_0BE8_0BC1(int x, int y)
{
    if (x >= 0 && x <= 0x3f && y >= 1 && y <= 0x3f)
        return 1;
    return 0;
}

int far IsItDirt(int value)
{
    if (value >= 0x20 && value <= 0x2e)
        return 1;
    return 0;
}

int far f_0BE8_0C0F(int x, int y, int dir)
{
    int back;
    int best;
    int bestValue;
    int i;
    int nx;
    int ny;
    int value;

    if (y == 1) {
        if (fd_3E1D_2180[x][0] == 0x18)
            return 1;
        return SRand2() * 4 + 3;
    }
    back = dir ^ 4;
    best = 0;
    bestValue = 0;
    for (i = 0; i < 8; i++) {
        ny = fd_3D57_0008[i] + y;
        nx = fd_3D57_0000[i] + x;
        if (nx < 0 || nx > 63 || ny < 0 || ny > 63)
            continue;
        value = fd_3E1D_4180[nx][ny];
        if (value > bestValue && back != i) {
            bestValue = value;
            best = i + 1;
        }
    }
    return best;
}

int far f_0BE8_0CBB(int x, int y, int dir)
{
    int back;
    int best;
    int bestValue;
    int i;
    int nx;
    int ny;
    int value;

    if (y == 1) {
        if (fd_3E1D_3180[x][0] == 0x18)
            return 1;
        return SRand2() * 4 + 3;
    }
    back = dir ^ 4;
    best = 0;
    bestValue = 0;
    for (i = 0; i < 8; i++) {
        ny = fd_3D57_0008[i] + y;
        nx = fd_3D57_0000[i] + x;
        if (nx < 0 || nx > 63 || ny < 0 || ny > 63)
            continue;
        value = fd_3E1D_5180[nx][ny];
        if (value > bestValue && back != i) {
            bestValue = value;
            best = i + 1;
        }
    }
    return best;
}

/* SCAFFOLD BEGIN: f_0BE8_0D67/f_0BE8_0E0F (GetEnterDirB/R) best drafts: target keeps ny in memory [bp-2] and
   value in DI, back/bestValue/best at [bp-6]/[bp-8]/[bp-A]. MSC gives DI to ny and puts
   value in memory (ny and value have disjoint live ranges and share storage); a struct
   {best,bestValue,back} fixes the slot order but not the DI choice. Tried: declaration orders,
   block-scoped locals, register keyword (ignored under /Og), nested-if and || forms,
   value-free expression form, 0..17 padding declarations */
int far f_0BE8_0D67(int x, int y, int dir)
{
    int back;
    int best;
    int bestValue;
    int i;
    int nx;
    int ny;
    int value;

    back = dir ^ 4;
    best = -1;
    bestValue = fd_3E1D_4180[x][y];
    for (i = 0; i < 8; i++) {
        if (back == i)
            continue;
        ny = fd_3D57_0008[i] + y;
        nx = fd_3D57_0000[i] + x;
        if (nx < 0 || nx > 63 || ny < 0 || ny > 63)
            continue;
        value = fd_3E1D_4180[nx][ny];
        if (value == 0)
            continue;
        if (bestValue < value)
            continue;
        if (bestValue <= value && SRand2() == 0)
            continue;
        bestValue = value;
        best = i;
    }
    return best;
}

int far f_0BE8_0E0F(int x, int y, int dir)
{
    int back;
    int best;
    int bestValue;
    int i;
    int nx;
    int ny;
    int value;

    back = dir ^ 4;
    best = -1;
    bestValue = fd_3E1D_5180[x][y];
    for (i = 0; i < 8; i++) {
        if (back == i)
            continue;
        ny = fd_3D57_0008[i] + y;
        nx = fd_3D57_0000[i] + x;
        if (nx < 0 || nx > 63 || ny < 0 || ny > 63)
            continue;
        value = fd_3E1D_5180[nx][ny];
        if (value == 0)
            continue;
        if (bestValue < value)
            continue;
        if (bestValue <= value && SRand2() == 0)
            continue;
        bestValue = value;
        best = i;
    }
    return best;
}

/* SCAFFOLD END */

void far f_0BE8_0EB7(void)
{
    if (TickCount() >= fd_50F6_0214 + 0x1c20) {
        fd_50F6_0214 = TickCount();
        if (++fd_50F6_0228 > 2)
            fd_50F6_0228 = 0;
        f_00DF_00B1(fd_50F6_0228 + 0x2713, 0x7e);
    }
}


