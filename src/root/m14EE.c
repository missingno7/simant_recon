/* Root module, code frame 14EE: nest holes and tunnel digging. */

extern int far SRand1(int range);
extern int far SRand8(void);
extern int far f_10F7_048E(int plane, int x, int y);
extern int far f_10F7_24EE(int colony, int x, int y);

extern int far fd_50F6_0F24;
extern unsigned char far fd_3E1D_0180[128][64];
extern unsigned char far fd_3D57_0224[];
extern int far fd_3D57_02AC[2];
extern int far fd_3D57_02A4[2];
extern unsigned char far fd_3D57_0264[];
extern int far fd_3D57_02B0[2];
extern int far fd_3D57_02A8[2];
extern unsigned char far fd_3E1D_2180[64][64];
extern unsigned char far fd_3E1D_3180[64][64];
extern char far fd_3D57_0008[8];
extern char far fd_3D57_0000[8];
extern unsigned char near g_1BB2[8];
extern int far IsItDirt(int value);
extern long far fd_50F6_1068;
extern long far fd_50F6_1082;
extern int far fd_50F6_0224;
extern int far fd_50F6_10B2;
extern int far fd_50F6_10C0;
extern long far fd_50F6_108E;
extern long far fd_50F6_10A2;
extern int far fd_50F6_0232;
extern int far fd_50F6_0200;
extern int far fd_50F6_020E;
extern unsigned char far fd_3E1D_4180[64][64];
extern unsigned char far fd_3E1D_5180[64][64];

void far f_14EE_0079(int x, int y);
void far MakeNewHoleB(int x);
int far f_14EE_0317(int v);
void far f_14EE_0367(int x);
void far f_14EE_04B5(int x, int y);
void far f_14EE_0519(int x, int y);
void far f_14EE_0647(int x, int y);
void far f_14EE_09F1(int x, int y);
void far f_14EE_0B5A(int x, int y);
int far f_14EE_0B33(int v);
void far f_14EE_0C9C(int x, int y);
void far f_14EE_0D71(int x, int y);

int far f_14EE_0002(int x, int y)
{
    int result;

    result = 0;
    if (x >= 1 && x <= 127 && y >= 1 && y <= 63) {
        if (fd_50F6_0F24) {
            if (fd_3E1D_0180[x][y] < 0xc8)
                result = 1;
        } else {
            result = f_10F7_048E(1, x, y);
        }
        if (result == 1)
            f_14EE_0079(x, y);
    }
    return result;
}

void far f_14EE_0079(int x, int y)
{
    if (x < 1 || x >= 0x7f || y < 1 || y >= 0x3f)
        return;
    if (fd_50F6_0F24)
        fd_3E1D_0180[x][y] = 0x59;
    else {
        fd_3E1D_0180[x][y] = 0x50;
        f_14EE_04B5(x, y);
    }
    if (x < 0x40) {
        fd_3D57_0224[y] = x;
        f_14EE_0519(y, 1);
        fd_3D57_02AC[0] = x;
        fd_3D57_02AC[1] = y;
        fd_3D57_02A4[0] = y;
        fd_3D57_02A4[1] = 0;
    } else {
        fd_3D57_0264[y] = x;
        f_14EE_0647(y, 1);
        fd_3D57_02B0[0] = x;
        fd_3D57_02B0[1] = y;
        fd_3D57_02A8[0] = y;
        fd_3D57_02A8[1] = 0;
    }
}

void far f_14EE_0151(int colony, int x, int y)
{
    if (f_10F7_24EE(colony, x, y)) {
        if (colony == 2) {
            if (y <= 1) {
                fd_3E1D_2180[x][0] = 0x18;
                MakeNewHoleB(x);
                if (y != 1)
                    return;
            }
            f_14EE_0519(x, y);
        } else {
            if (y <= 1) {
                fd_3E1D_3180[x][0] = 0x18;
                f_14EE_0367(x);
                if (y != 1)
                    return;
            }
            f_14EE_0647(x, y);
        }
    }
}

void far MakeNewHoleB(int x)
{
    int i;
    int v;
    int y;
    int start;

    start = SRand1(31);
    if (fd_50F6_0F24) {
        for (i = 0; i < 34; i++) {
            y = (start + i) % 32 + 2;
            v = f_14EE_0317(fd_3E1D_0180[y][x]);
            if (v) {
                fd_3E1D_0180[y][x] = v;
                fd_3D57_02AC[0] = y;
                fd_3D57_02AC[1] = x;
                fd_3D57_02A4[0] = x;
                fd_3D57_02A4[1] = 0;
                break;
            }
        }
        if (i == 34)
            return;
    } else {
        for (i = 0; i < 34; i++) {
            y = (i + start) % 32 + 2;
            if (f_10F7_048E(1, y, x)) {
                fd_3E1D_0180[y][x] = 0x50;
                fd_3D57_02AC[0] = y;
                fd_3D57_02AC[1] = x;
                fd_3D57_02A4[0] = x;
                fd_3D57_02A4[1] = 0;
                f_14EE_04B5(y, x);
                break;
            }
        }
        if (i == 34)
            return;
    }
    fd_3D57_0224[x] = y;
    f_14EE_0519(x, 1);
}

int far f_14EE_0317(int v)
{
    if (v == 0)
        return 0x86;
    if (v == 2)
        return 0x8a;
    if (v == 3)
        return 0x8a;
    if (v >= 0x5e) {
        if (v < 0x62)
            return v + 0x22;
        if (v == 0x66)
            return 0x85;
        if (v == 0x68)
            return 0x84;
    }
    return 0;
}

void far f_14EE_0367(int x)
{
    int i;
    int v;
    int y;
    int start;

    start = SRand1(31);
    if (fd_50F6_0F24) {
        for (i = 0; i < 34; i++) {
            y = 0x7e - (start + i) % 32;
            v = f_14EE_0317(fd_3E1D_0180[y][x]);
            if (v) {
                fd_3E1D_0180[y][x] = v;
                fd_3D57_02B0[0] = y;
                fd_3D57_02B0[1] = x;
                fd_3D57_02A8[0] = x;
                fd_3D57_02A8[1] = 0;
                break;
            }
        }
        if (i == 34)
            return;
    } else {
        for (i = 0; i < 34; i++) {
            y = 0x7e - (i + start) % 32;
            if (f_10F7_048E(1, y, x)) {
                fd_3E1D_0180[y][x] = 0x50;
                fd_3D57_02B0[0] = y;
                fd_3D57_02B0[1] = x;
                fd_3D57_02A8[0] = x;
                fd_3D57_02A8[1] = 0;
                f_14EE_04B5(y, x);
                break;
            }
        }
        if (i == 34)
            return;
    }
    fd_3D57_0264[x] = y;
    f_14EE_0647(x, 1);
}

void far f_14EE_04B5(int x, int y)
{
    int i;
    int nx;
    int ny;

    for (i = 0; i < 8; i++) {
        ny = fd_3D57_0008[i] + y;
        nx = fd_3D57_0000[i] + x;
        if (nx < 0 || nx > 127 || ny < 0 || ny > 63)
            continue;
        if (fd_3E1D_0180[nx][ny] < 0x50)
            fd_3E1D_0180[nx][ny] = g_1BB2[i];
    }
}

void far f_14EE_0519(int x, int y)
{
    if (IsItDirt(fd_3E1D_2180[x][y])) {
        fd_3E1D_2180[x][y] = SRand8();
        fd_50F6_1068 += x;
        fd_50F6_1082 += y;
        fd_50F6_0224++;
        if (fd_50F6_0224 > 0) {
            fd_50F6_10B2 = fd_50F6_1068 / fd_50F6_0224;
            fd_50F6_10C0 = fd_50F6_1082 / fd_50F6_0224;
        }
        if (y > 0x35 && SRand1(64) == 0) {
            fd_3E1D_2180[x][y] = 0x14;
            f_14EE_0647(x, y);
            fd_3E1D_3180[x][y] = 0x14;
        }
    }
    f_14EE_09F1(x, y - 1);
    f_14EE_09F1(x + 1, y);
    f_14EE_09F1(x, y + 1);
    f_14EE_09F1(x - 1, y);
    f_14EE_0C9C(x, y);
}

void far f_14EE_0647(int x, int y)
{
    if (IsItDirt(fd_3E1D_3180[x][y])) {
        fd_3E1D_3180[x][y] = SRand8();
        fd_50F6_108E += x;
        fd_50F6_10A2 += y;
        fd_50F6_0232++;
        if (fd_50F6_0232 > 0) {
            fd_50F6_0200 = fd_50F6_108E / fd_50F6_0232;
            fd_50F6_020E = fd_50F6_10A2 / fd_50F6_0232;
        }
    }
    f_14EE_0B5A(x, y - 1);
    f_14EE_0B5A(x + 1, y);
    f_14EE_0B5A(x, y + 1);
    f_14EE_0B5A(x - 1, y);
    f_14EE_0D71(x, y);
}

int far DigTileThemB(int x, int y)
{
    if (y < 0x3f && !IsItDirt(fd_3E1D_2180[x][y + 1]))
        return 0;
    if (y > 2 && !IsItDirt(fd_3E1D_2180[x][y - 1]))
        return 0;
    if (x == 0 || x > 0x3e)
        return 0;
    if (y == 0) {
        fd_3E1D_2180[x][y] = 0x18;
        MakeNewHoleB(x);
    } else
        fd_3E1D_2180[x][y] = SRand8();
    fd_50F6_1068 += x;
    fd_50F6_1082 += y;
    fd_50F6_0224++;
    if (fd_50F6_0224 > 0) {
        fd_50F6_10B2 = fd_50F6_1068 / fd_50F6_0224;
        fd_50F6_10C0 = fd_50F6_1082 / fd_50F6_0224;
    }
    f_14EE_09F1(x, y - 1);
    f_14EE_09F1(x + 1, y);
    f_14EE_09F1(x, y + 1);
    f_14EE_09F1(x - 1, y);
    f_14EE_0C9C(x, y);
    return 1;
}

int far DigTileThemR(int x, int y)
{
    if (y < 0x3f) {
        if (!IsItDirt(fd_3E1D_3180[x][y + 1]))
            return 0;
    }
    if (y > 2) {
        if (!IsItDirt(fd_3E1D_3180[x][y - 1]))
            return 0;
    }
    if (x == 0)
        return 0;
    if (x > 0x3e)
        return 0;
    if (y == 0) {
        fd_3E1D_3180[x][y] = 0x18;
        f_14EE_0367(x);
    } else
        fd_3E1D_3180[x][y] = SRand8();
    fd_50F6_108E += x;
    fd_50F6_10A2 += y;
    fd_50F6_0232++;
    if (fd_50F6_0232 > 0) {
        fd_50F6_0200 = fd_50F6_108E / fd_50F6_0232;
        fd_50F6_020E = fd_50F6_10A2 / fd_50F6_0232;
    }
    f_14EE_0B5A(x, y - 1);
    f_14EE_0B5A(x + 1, y);
    f_14EE_0B5A(x, y + 1);
    f_14EE_0B5A(x - 1, y);
    f_14EE_0D71(x, y);
    return 1;
}

/* SCAFFOLD BEGIN: f_14EE_09F1 best draft (SmoothEdgesB): 272 bytes differ. Target keeps x in DI, bits in SI
   (no home, frame 8) and y in memory; MSC here enregisters x (SI) and y (DI) and puts bits in
   memory (frame 10). `register` has no effect under /Og; declaration order, local copy of x,
   |=/+= spellings and a far pointer temp were tried */
void far f_14EE_09F1(int x, int y)
{
    int v;
    int bits;

    if (x < 0 || x > 63 || y > 63)
        return;
    if (y == 0) {
        if (fd_3E1D_2180[x][y] < 0x30)
            fd_3E1D_2180[x][y] = 0x18;
        return;
    }
    v = fd_3E1D_2180[x][y];
    if (v < 0x20)
        return;
    if (v > 0x2f && v < 0x4f)
        return;
    v = v > 0x4d ? 0x2f : 0;
    bits = 0;
    if (y < 2 || f_14EE_0B33(fd_3E1D_2180[x][y - 1]))
        bits = 1;
    if (x > 0x3e || f_14EE_0B33(fd_3E1D_2180[x + 1][y]))
        bits |= 2;
    if (y > 0x3e || f_14EE_0B33(fd_3E1D_2180[x][y + 1]))
        bits |= 4;
    if (x < 1 || f_14EE_0B33(fd_3E1D_2180[x - 1][y]))
        bits |= 8;
    if (bits)
        fd_3E1D_2180[x][y] = bits + v + 0x1f;
    else if (v == 0)
        fd_3E1D_2180[x][y] = SRand8();
    else
        fd_3E1D_2180[x][y] = 0x4e;
}

/* SCAFFOLD END */

int far f_14EE_0B33(int v)
{
    if (v < 0x20)
        return 0;
    if (v > 0x2f && v < 0x4f)
        return 0;
    return 1;
}

/* SCAFFOLD BEGIN: f_14EE_0B5A (SmoothEdgesR) mirror of f_14EE_09F1, same residue */
void far f_14EE_0B5A(int x, int y)
{
    int v;
    int bits;

    if (x < 0 || x > 63 || y > 63)
        return;
    if (y == 0) {
        if (fd_3E1D_3180[x][y] < 0x30)
            fd_3E1D_3180[x][y] = 0x18;
        return;
    }
    v = fd_3E1D_3180[x][y];
    if (v < 0x20)
        return;
    if (v > 0x2f && v < 0x4f)
        return;
    v = v > 0x4d ? 0x2f : 0;
    bits = 0;
    if (y < 2 || f_14EE_0B33(fd_3E1D_3180[x][y - 1]))
        bits = 1;
    if (x > 0x3e || f_14EE_0B33(fd_3E1D_3180[x + 1][y]))
        bits |= 2;
    if (y > 0x3e || f_14EE_0B33(fd_3E1D_3180[x][y + 1]))
        bits |= 4;
    if (x < 1 || f_14EE_0B33(fd_3E1D_3180[x - 1][y]))
        bits |= 8;
    if (bits)
        fd_3E1D_3180[x][y] = bits + v + 0x1f;
    else if (v == 0)
        fd_3E1D_3180[x][y] = SRand8();
    else
        fd_3E1D_3180[x][y] = 0x4e;
}

/* SCAFFOLD END */

/* SCAFFOLD BEGIN: f_14EE_0C9C/f_14EE_0D71 (FixExitMapB/R) best drafts: target frame 10 with i [bp-4], best
   [bp-6], ny in SI, nx in AX, and the final ExitMap store hoists `mov ax,SEG; mov es,ax` above
   the if/else. With an extra `value` local (as below) frame, loop and registers match but best
   lands in [bp-8] and the final ES load is not hoisted (57 bytes differ); all 120 declaration
   orders give the same result; without `value` DI is used for nx (198 bytes differ) */
void far f_14EE_0C9C(int x, int y)
{
    int i;
    int nx;
    int ny;
    int best;
    int value;

    if (y < 2) {
        if (fd_3E1D_2180[x][y] == 0x18)
            fd_3E1D_4180[x][y] = 0xff;
        else
            fd_3E1D_4180[x][y] = 0xfe;
        return;
    }
    best = 0;
    for (i = 0; i < 8; i++) {
        ny = fd_3D57_0008[i] + y;
        nx = fd_3D57_0000[i] + x;
        if (nx < 0 || nx > 63 || ny < 0 || ny > 63)
            continue;
        value = fd_3E1D_4180[nx][ny];
        if (value > best)
            best = value;
    }
    if (best)
        fd_3E1D_4180[x][y] = best - 1;
    else
        fd_3E1D_4180[x][y] = 0;
}

void far f_14EE_0D71(int x, int y)
{
    int i;
    int nx;
    int ny;
    int best;
    int value;

    if (y < 2) {
        if (fd_3E1D_3180[x][y] == 0x18)
            fd_3E1D_5180[x][y] = 0xff;
        else
            fd_3E1D_5180[x][y] = 0xfe;
        return;
    }
    best = 0;
    for (i = 0; i < 8; i++) {
        ny = fd_3D57_0008[i] + y;
        nx = fd_3D57_0000[i] + x;
        if (nx < 0 || nx > 63 || ny < 0 || ny > 63)
            continue;
        value = fd_3E1D_5180[nx][ny];
        if (value > best)
            best = value;
    }
    if (best)
        fd_3E1D_5180[x][y] = best - 1;
    else
        fd_3E1D_5180[x][y] = 0;
}

/* SCAFFOLD END */

void far f_14EE_0E46(void)
{
    int x;
    int y;
    int v;

    for (x = 0; x < 64; x++) {
        for (y = 3; y < 64; y++) {
            v = fd_3E1D_2180[x][y];
            if (v >= 0x20 && v <= 0x2d)
                fd_3E1D_2180[x][y] += 0x31;
            else if (fd_3E1D_2180[x][y] <= 0x13)
                fd_3E1D_2180[x][y] = 0x50;
        }
    }
}
