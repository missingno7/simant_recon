/* root:10F7 draft: recovered prefix */
extern signed char far fd_3D57_0000[];
extern signed char far fd_3D57_0008[];
extern unsigned char far fd_3E1D_6180[128][64];
extern unsigned char far fd_3E1D_8180[64][64];
extern unsigned char far fd_3E1D_9180[64][64];
extern unsigned char far fd_3E1D_0180[128][64];
extern unsigned char far fd_3E1D_2180[64][64];
extern unsigned char far fd_3E1D_3180[64][64];
extern int far fd_50F6_047C;
extern int far fd_50F6_048A;
extern int far fd_50F6_0496;
extern int far fd_50F6_04C2;
extern int far fd_50F6_048C;
extern int far fd_50F6_105E;
extern int far fd_50F6_047E;
extern int far fd_50F6_048E;
extern int far fd_50F6_1074;
extern int far fd_50F6_0F34;
extern int far fd_50F6_0F12;
extern int far fd_3D57_0C22;
extern signed char far fd_3D57_0094[];
extern int far fd_50F6_04E2;
extern int far fd_50F6_0FFC;
extern int far fd_50F6_0F42;
extern int far fd_50F6_0F7E;
extern int far fd_50F6_0A06;
extern int far fd_50F6_0FB8;
extern int far fd_50F6_06AC;
extern int far fd_3D57_0798;
extern int far fd_50F6_049A;
extern int far fd_50F6_0502;
extern signed char far fd_3D57_006C[];
extern int far fd_50F6_1050;
extern int far fd_50F6_1060;
extern unsigned char far fd_3D57_0224[];
extern unsigned char far fd_3D57_0264[];
extern int far fd_50F6_0F24;
extern int far fd_3D57_0C16;
extern int far fd_50F6_0FBA;
extern int far fd_50F6_0F78;
extern int far fd_50F6_1006;
extern int far fd_50F6_1044;
extern long far fd_50F6_0472;
extern void far * far * far fd_50F6_034C;
extern int far fd_50F6_0330;
extern int far fd_50F6_10BE;
extern int far fd_3D57_0C26;
extern int far fd_50F6_1044;
extern int far fd_50F6_04C4;
extern int far fd_3D57_02AC[];
extern int far fd_50F6_0B1E;
extern int far fd_50F6_0C38;
extern int far fd_3D57_0C24;
extern int far fd_50F6_0D6A;
extern unsigned char far fd_3E1D_A180[];
extern unsigned char far fd_3E1D_A569[];
extern unsigned char far fd_3E1D_AD3B[];
extern unsigned char far fd_3E1D_A952[];
extern unsigned char far fd_3E1D_B124[];
extern int far fd_50F6_0DA8;
extern unsigned char far fd_3E1D_B50D[];
extern unsigned char far fd_3E1D_B702[];
extern unsigned char far fd_3E1D_BAEC[];
extern unsigned char far fd_3E1D_B8F7[];
extern unsigned char far fd_3E1D_BCE1[];
extern int far fd_50F6_0EAA;
extern unsigned char far fd_3E1D_BED6[];
extern unsigned char far fd_3E1D_C0CB[];
extern unsigned char far fd_3E1D_C4B5[];
extern unsigned char far fd_3E1D_C2C0[];
extern unsigned char far fd_3E1D_C6AA[];

int far f_10F7_2867(int, int);
int far f_10F7_04EC(int, int, int);
int far f_10F7_07C7(int, int, int);
int far GetMap(int, int, int);
void far f_10F7_05FE(int, int, int, int);
int far f_10F7_24EE(int, int, int);
void far f_0EC1_0557(int, int, int, int, int);
void far f_0EC1_05D4(int, int, int, int, int);
void far f_0EC1_0651(int, int, int, int, int);
void far f_14EE_0151(int, int, int);
void far f_00DF_00E8(int, int, int);
void far f_0250_000E(int, int, int);
int far f_0894_2423(int);
void far f_0250_0E91(void);
int far f_14EE_0002(int, int);
void far o25_3BA4_1035(void);
void far f_015B_06A2(void);
int far f_0894_23BB(int, int);
void far f_0BE8_0798(int, int);
unsigned long far f_0BE8_0B83(int, int, int, int);
int far IsItDirt(int);
int far f_10F7_2640(int);
int far f_10F7_2894(int, int);
void far f_1496_043C(int, int, int);
void far o14_384C_0ACD(int);
void far o22_39C7_188D(int, int);
void far f_15D9_009C(void far *, long, int);
int far SRand1(int);
int far SRand8(void);
int far SRand16(void);
int far f_10F7_2821(int, int, int);
int far f_0BE8_0B21(int, int, int, int);
void far f_0BE8_0812(int, int);
void far o11_35F5_0088(int);
void far f_10F7_0B8F(void);
void far f_10F7_0BEF(void);
int far f_10F7_0CA8(int, int, int);
int far f_00DF_012D(void);
void far f_00F8_0265(long);
void far f_00DF_00B1(unsigned int, unsigned int);
int far f_10F7_0766(int);
int far f_10F7_2894(int, int);

int far f_10F7_000E(int map, int index, int out)
{
    if (map <= 1)
        return f_10F7_2867(index, out);
    else
        return f_10F7_2894(index, out);
}

int far f_10F7_003A(int value)
{
    if (value != 0xff && value != 0xfe) return 0;
    return 1;
}

int far f_10F7_005D(int list, int index, int far *life, int far *column,
                    int far *attribute, int far *state, int far *direction)
{
    if (list <= 1) {
        if (index < 0 || index >= fd_50F6_0D6A)
            return 0;
        *life = fd_3E1D_A180[index];
        *column = fd_3E1D_A569[index];
        *attribute = fd_3E1D_AD3B[index];
        *state = fd_3E1D_A952[index];
        *direction = fd_3E1D_B124[index];
    } else if (list == 2) {
        if (index < 0 || index >= fd_50F6_0DA8)
            return 0;
        *life = fd_3E1D_B50D[index];
        *column = fd_3E1D_B702[index];
        *attribute = fd_3E1D_BAEC[index];
        *state = fd_3E1D_B8F7[index];
        *direction = fd_3E1D_BCE1[index];
    } else {
        if (index < 0 || index >= fd_50F6_0EAA)
            return 0;
        *life = fd_3E1D_BED6[index];
        *column = fd_3E1D_C0CB[index];
        *attribute = fd_3E1D_C4B5[index];
        *state = fd_3E1D_C2C0[index];
        *direction = fd_3E1D_C6AA[index];
    }
    return 1;
}

void far f_10F7_01B1(int list, int index, int life, int column,
                      int attribute, int state, int direction)
{
    if (list <= 1) {
        if (index < 0 || index >= fd_50F6_0D6A)
            return;
        fd_3E1D_A180[index] = (unsigned char)life;
        fd_3E1D_A569[index] = (unsigned char)column;
        fd_3E1D_AD3B[index] = (unsigned char)attribute;
        fd_3E1D_A952[index] = (unsigned char)state;
        fd_3E1D_B124[index] = (unsigned char)direction;
    } else if (list == 2) {
        if (index < 0 || index >= fd_50F6_0DA8)
            return;
        fd_3E1D_B50D[index] = (unsigned char)life;
        fd_3E1D_B702[index] = (unsigned char)column;
        fd_3E1D_BAEC[index] = (unsigned char)attribute;
        fd_3E1D_B8F7[index] = (unsigned char)state;
        fd_3E1D_BCE1[index] = (unsigned char)direction;
    } else {
        if (index < 0 || index >= fd_50F6_0EAA)
            return;
        fd_3E1D_BED6[index] = (unsigned char)life;
        fd_3E1D_C0CB[index] = (unsigned char)column;
        fd_3E1D_C4B5[index] = (unsigned char)attribute;
        fd_3E1D_C2C0[index] = (unsigned char)state;
        fd_3E1D_C6AA[index] = (unsigned char)direction;
    }
}

int far f_10F7_02D6(int list, int matchLife, int matchColumn, int low, int high, int mask)
{
    unsigned char far *lifeArr;
    unsigned char far *columnArr;
    unsigned char far *attrArr;
    int count;
    int i;
    int masked;

    if (list <= 1) {
        count = fd_50F6_0D6A;
        lifeArr = fd_3E1D_A180;
        columnArr = fd_3E1D_A569;
        attrArr = fd_3E1D_AD3B;
    } else if (list == 2) {
        count = fd_50F6_0DA8;
        lifeArr = fd_3E1D_B50D;
        columnArr = fd_3E1D_B702;
        attrArr = fd_3E1D_BAEC;
    } else {
        count = fd_50F6_0EAA;
        lifeArr = fd_3E1D_BED6;
        columnArr = fd_3E1D_C0CB;
        attrArr = fd_3E1D_C4B5;
    }
    for (i = count - 1; i >= 0; i--) {
        masked = attrArr[i] & mask;
        if (lifeArr[i] == matchLife && columnArr[i] == matchColumn &&
            masked >= low && masked <= high)
            break;
    }
    return i;
}

int far f_10F7_03B7(int list, int matchLife, int matchColumn, int attribute)
{
    unsigned char far *lifeArr;
    unsigned char far *columnArr;
    unsigned char far *attrArr;
    int count;
    int i;

    if (list <= 1) {
        count = fd_50F6_0D6A;
        lifeArr = fd_3E1D_A180;
        columnArr = fd_3E1D_A569;
        attrArr = fd_3E1D_AD3B;
    } else if (list == 2) {
        count = fd_50F6_0DA8;
        lifeArr = fd_3E1D_B50D;
        columnArr = fd_3E1D_B702;
        attrArr = fd_3E1D_BAEC;
    } else {
        count = fd_50F6_0EAA;
        lifeArr = fd_3E1D_BED6;
        columnArr = fd_3E1D_C0CB;
        attrArr = fd_3E1D_C4B5;
    }
    for (i = count - 1; i >= 0; i--) {
        if (lifeArr[i] == matchLife && columnArr[i] == matchColumn &&
            attrArr[i] == attribute)
            break;
    }
    return i;
}

int far f_10F7_048E(int type, int y, int x)
{
    register int index;

    if (f_10F7_04EC(type, y, x) == 1) {
        for (index = 0; index < 8; ++index) {
            if (!f_10F7_04EC(type, y + fd_3D57_0000[index], x + fd_3D57_0008[index]))
                return 0;
        }
        return 1;
    }
    return 0;
}

int far f_10F7_04EC(int plane, int x, int y)
{
    int result;
    int tile;
    int life;

    result = 0;
    tile = GetMap(plane, x, y);
    if (tile >= 0) {
        life = f_10F7_07C7(plane, x, y);
        if (life < 0 || f_10F7_003A(life) == 1) {
            if (plane <= 1) {
                if (tile < 16)
                    result = 1;
            } else {
                if (tile < 8)
                    result = 1;
            }
        }
    }
    return result;
}

int far f_10F7_054D(int plane, int x, int y, int type, int a, int b)
{
    int added;

    added = 0;
    if (plane <= 1) {
        if (fd_50F6_0D6A < 1000) {
            f_0EC1_0557(x, y, type, a, b);
            added = 1;
        }
    } else if (plane == 2) {
        if (fd_50F6_0DA8 < 500) {
            f_0EC1_05D4(x, y, type, a, b);
            added = 1;
        }
    } else if (fd_50F6_0EAA < 500) {
        f_0EC1_0651(x, y, type, a, b);
        added = 1;
    }
    if (added == 1)
        f_10F7_05FE(plane, x, y, type);
    return added;
}

void far f_10F7_05FE(int plane, int x, int y, int value)
{
    if (f_10F7_000E(plane, x, y) == 1) {
        switch (plane) {
        case 0:
        case 1:
            fd_3E1D_6180[x][y] = value;
            break;
        case 2:
            fd_3E1D_8180[x][y] = value;
            if (value > 0 && f_10F7_24EE(plane, x, y) == 1) {
                f_14EE_0151(plane, x, y);
                f_00DF_00E8(0x13, 0, 0x3f);
            }
            break;
        case 3:
            fd_3E1D_9180[x][y] = value;
            if (value > 0 && f_10F7_24EE(plane, x, y) == 1) {
                f_14EE_0151(plane, x, y);
                f_00DF_00E8(0x13, 0, 0x3f);
            }
            break;
        }
        f_0250_000E(plane, x, y);
    }
}

int far f_10F7_06BF(value)
unsigned char value;
{
    int normalized;
    normalized = value;
    normalized &= 0x7f;
    if (normalized >= 1 && normalized <= 7) return 1;
    return 0;
}

int far f_10F7_06E4(int category, int tile)
{
    if (category < 2)
        return 0;
    if (tile < 0x1c || tile > 0x1f)
        return 0;
    return 1;
}

int far f_10F7_070B(int category, int tile)
{
    if (category <= 1)
        return f_0894_2423(tile);
    return f_10F7_0766(tile);
}

int far f_10F7_0731(int plane, int tile)
{
    if (plane <= 1) {
        if (plane == 1 && tile >= 0x51 && tile <= 0x53)
            return 1;
        return 0;
    }
    if (tile >= 0x30 && tile <= 0x31)
        return 1;
    return 0;
}

int far f_10F7_0766(int value)
{
    if (value < 0x10 || value > 0x13) return 0;
    return 1;
}

int far f_10F7_0787(int plane, int x, int y)
{
    register int tile;

    tile = GetMap(plane, x, y);
    if (tile < 0)
        return 0;
    if (plane <= 1)
        return f_0894_2423(tile);
    return f_10F7_0766(tile);
}

int far f_10F7_07C7(int plane, int x, int y)
{
    int result;

    result = -1;
    if (f_10F7_000E(plane, x, y) == 1) {
        switch (plane) {
        case 0:
        case 1:
            result = fd_3E1D_6180[x][y];
            break;
        case 2:
            result = fd_3E1D_8180[x][y];
            break;
        case 3:
            result = fd_3E1D_9180[x][y];
            break;
        }
        if (result == 0)
            result = -1;
    }
    return result;
}

int far GetMap(int plane, int x, int y)
{
    int result;

    result = -1;
    if (f_10F7_000E(plane, x, y) == 1) {
        switch (plane) {
        case 0:
        case 1:
            result = fd_3E1D_0180[x][y];
            break;
        case 2:
            result = fd_3E1D_2180[x][y];
            break;
        case 3:
            result = fd_3E1D_3180[x][y];
            break;
        }
    }
    return result;
}

void far f_10F7_08CE(int plane, int x, int y, int value)
{
    if (f_10F7_000E(plane, x, y) == 1) {
        switch (plane) {
        case 0:
        case 1:
            fd_3E1D_0180[x][y] = value;
            break;
        case 2:
            fd_3E1D_2180[x][y] = value;
            break;
        case 3:
            fd_3E1D_3180[x][y] = value;
            break;
        }
        f_0250_000E(plane, x, y);
    }
}

void far f_10F7_0954(int plane, int x, int y, int value)
{
    if (f_10F7_000E(plane, x, y) == 1) {
        if (f_10F7_07C7(plane, x, y) == value)
            f_10F7_05FE(plane, x, y, 0);
        f_0250_000E(plane, x, y);
    }
}

void far f_10F7_09A8(int plane, int x, int y, int type, int dir)
{
    f_10F7_0954(plane, x, y, 0xff);
    if (type == 0x60)
        f_10F7_0954(plane, x + fd_3D57_0000[dir ^ 4], y + fd_3D57_0008[dir ^ 4], 0xfe);
}

void far f_10F7_09FC(int plane, int x, int y, int dir, int value)
{
    f_10F7_05FE(plane, x + fd_3D57_0000[dir ^ 4], y + fd_3D57_0008[dir ^ 4],
                (value == 0xff) ? 0xfe : value);
}

void far f_10F7_0A44(int plane, int x, int y, int type, int dir, int life)
{
    if (f_10F7_000E(plane, x, y) == 1) {
        f_10F7_05FE(plane, x, y, life);
        if (type == 0x60)
            f_10F7_09FC(plane, x, y, dir, life);
        if (life != 0) {
            fd_50F6_047C = x;
            fd_50F6_048A = y;
            fd_50F6_0496 = dir;
            fd_50F6_04C2 = type;
            fd_50F6_048C = plane;
        }
    }
}

void far f_10F7_0ACE(int plane, int x, int y, int type, int dir)
{
    f_10F7_09A8(fd_50F6_048C, fd_50F6_047C, fd_50F6_048A, fd_50F6_04C2, fd_50F6_0496);
    f_10F7_0A44(plane == 0 ? 1 : plane, x, y, type, dir, 0xff);
}

void far f_10F7_0B38(void)
{
}

void far f_10F7_0B40(void)
{
    f_10F7_0B38();
    f_0250_0E91();
}

void far f_10F7_0B51(void)
{
    if (fd_50F6_105E == 0xb) {
        f_10F7_0B8F();
        return;
    }
    fd_50F6_048E = fd_50F6_047E;
    fd_50F6_105E = 0xb;
    o11_35F5_0088(1);
}

void far f_10F7_0B8F(void)
{
    fd_50F6_105E = -1;
    o11_35F5_0088(fd_50F6_048E);
}

void far f_10F7_0BB1(void)
{
    if (fd_50F6_105E == 0xa) {
        f_10F7_0BEF();
        return;
    }
    fd_50F6_048E = fd_50F6_047E;
    fd_50F6_105E = 0xa;
    o11_35F5_0088(1);
}

void far f_10F7_0BEF(void)
{
    fd_50F6_105E = -1;
    o11_35F5_0088(fd_50F6_048E);
}

void far f_10F7_0C11(int a, int b, int c)
{
    fd_50F6_1074 = 1;
    if (f_10F7_0CA8(a, b, c) == 1) {
        f_10F7_0BEF();
        if (fd_50F6_04C2 == 0x60) {
            f_00DF_00E8(0xf, 0, 0x7e);
            f_0250_0E91();
            while (!f_00DF_012D())
                f_00F8_0265(5L);
            f_00DF_00B1(0x2afe, 0x7e);
        } else
            f_00DF_00E8(0xf, 0, 0x7e);
    } else
        f_00DF_00E8(1, 0, 0x7e);
}

/* SCAFFOLD BEGIN: f_10F7_0CA8 unrecovered; stub only reproduces its CONST word order. */
int far f_10F7_0CA8(int a, int b, int c)
{
    volatile int t;
    t = fd_50F6_0F34;
    t = fd_50F6_0F12;
    t = fd_3D57_0C22;
    t = fd_3D57_0094[a];
    t = fd_50F6_04E2;
    t = fd_50F6_0FFC;
    t = fd_50F6_0F42;
    t = fd_50F6_0F7E;
    t = fd_50F6_0A06;
    t = fd_50F6_0FB8;
    t = fd_50F6_06AC;
    t = fd_3D57_0798;
    t = fd_50F6_049A;
    t = fd_50F6_0502;
    return t;
}
/* SCAFFOLD END */

int far f_10F7_1396(int plane, int x, int y, int tx, int ty)
{
    int i;
    int dir;
    int done;
    int tile;
    int nx;
    int ny;
    int d;

    if (fd_50F6_04C2 != 0x18 && fd_50F6_04C2 != 0x38)
        return 0;
    done = 0;
    dir = f_0BE8_0B21(x, y, tx, ty);
    if (dir > 0)
        dir--;
    else
        dir = fd_50F6_0496;
    for (i = 0; !done; i++) {
        if (i >= 8)
            break;
        d = (fd_3D57_006C[i] + dir) & 7;
        nx = x + fd_3D57_0000[d];
        ny = y + fd_3D57_0008[d];
        if (f_10F7_000E(plane, nx, ny)) {
            if (f_10F7_07C7(plane, nx, ny) < 0) {
                tile = GetMap(plane, nx, ny);
                if (f_10F7_070B(plane, tile) && (tile & 3) < 3) {
                    tile++;
                    done = 1;
                } else if (f_10F7_04EC(plane, nx, ny) || tile == 0x38) {
                    tile = 0x10;
                    done = 1;
                }
            }
        }
    }
    if (!done) {
        d = dir;
        nx = x;
        ny = y;
        if (f_10F7_000E(plane, nx, ny)) {
            tile = GetMap(plane, nx, ny);
            if (f_10F7_070B(plane, tile) && (tile & 3) < 3) {
                tile++;
                done = 1;
            } else if (f_10F7_04EC(plane, nx, ny) || tile == 0x38) {
                tile = 0x10;
                done = 1;
            }
        }
    }
    if (done) {
        fd_50F6_0496 = d;
        if (plane <= 1)
            f_0BE8_0812(nx, ny);
        else {
            f_10F7_08CE(plane, nx, ny, tile);
            if (plane == 2)
                fd_50F6_1050++;
            else
                fd_50F6_1060++;
        }
        if (!((*(unsigned char far *)0x417L & 3) && (*(unsigned char far *)0x417L & 8)))
            fd_50F6_04C2 &= 0xf7;
        f_00DF_00E8(0x1d, 0, 0x7e);
    }
    return done;
}

void far f_10F7_15BC(int plane, int x, int y)
{
    int tile;

    if (plane <= 1) {
        if (f_10F7_2821(plane, x, y)) {
            if (x < 0x40 && fd_3D57_0224[y] == x)
                fd_3E1D_2180[y][0] = 0x31;
            else if (fd_3D57_0264[y] == x)
                fd_3E1D_3180[y][0] = 0x31;
        }
        tile = 0x51;
    } else if (f_10F7_2821(plane, x, y)) {
        fd_3E1D_0180[plane == 2 ? fd_3D57_0224[x] : fd_3D57_0264[x]][x] = 0x51;
        tile = 0x31;
    } else
        tile = 0x30;
    f_10F7_08CE(plane, x, y, tile);
}

int far f_10F7_1696(int plane, int x, int y, int tx, int ty)
{
    int tile;
    int i;
    int dir;
    int done;
    int ny;
    int nx;
    int d;

    if (fd_50F6_04C2 != 0x28 && fd_50F6_04C2 != 0x48)
        return 0;
    done = 0;
    dir = f_0BE8_0B21(x, y, tx, ty);
    if (dir > 0)
        dir--;
    else
        dir = fd_50F6_0496;
    for (i = 0; !done; i++) {
        if (i >= 8)
            break;
        d = (fd_3D57_006C[i] + dir) & 7;
        nx = x + fd_3D57_0000[d];
        ny = y + fd_3D57_0008[d];
        if (f_10F7_000E(plane, nx, ny)) {
            if (f_10F7_07C7(plane, nx, ny) < 0) {
                if (f_10F7_04EC(plane, nx, ny))
                    done = 1;
                else {
                    tile = GetMap(plane, nx, ny);
                    if (!f_10F7_070B(plane, tile) && !f_10F7_0731(plane, tile) &&
                        (f_10F7_2821(plane, nx, ny) || tile == 0x38))
                        done = 1;
                }
            }
        }
    }
    if (!done) {
        d = dir;
        nx = x;
        ny = y;
        if (f_10F7_000E(plane, nx, ny)) {
            if (f_10F7_04EC(plane, nx, ny))
                done = 1;
            else {
                tile = GetMap(plane, nx, ny);
                if (!f_10F7_070B(plane, tile) && !f_10F7_0731(plane, tile) &&
                    (f_10F7_2821(plane, nx, ny) || tile == 0x38))
                    done = 1;
            }
        }
    }
    if (done) {
        fd_50F6_0496 = d;
        f_10F7_15BC(plane, nx, ny);
        if (!((*(unsigned char far *)0x417L & 3) && (*(unsigned char far *)0x417L & 8))) {
            if (fd_50F6_04C2 == 0x28 || fd_50F6_04C2 == 0x48)
                fd_50F6_04C2 -= 0x18;
        }
        f_00DF_00E8(0x1e, 0, 0x7e);
    }
    return done;
}

int far f_10F7_18B0(int plane, int x, int y, int tx, int ty)
{
    int i;
    int done;
    int dir;
    int ny;
    int nx;
    int d;

    if (fd_50F6_04C2 != 8)
        return 0;
    done = 0;
    dir = f_0BE8_0B21(x, y, tx, ty);
    if (dir > 0)
        dir--;
    else
        dir = fd_50F6_0496;
    for (i = 0; !done; i++) {
        if (i >= 8)
            break;
        d = (fd_3D57_006C[i] + dir) & 7;
        nx = x + fd_3D57_0000[d];
        ny = y + fd_3D57_0008[d];
        if (f_10F7_000E(plane, nx, ny)) {
            if (f_10F7_07C7(plane, nx, ny) < 0) {
                if (f_10F7_04EC(plane, nx, ny) || GetMap(plane, nx, ny) == 0x38)
                    done = 1;
            }
        }
    }
    if (!done) {
        d = dir;
        nx = x;
        ny = y;
        if (f_10F7_000E(plane, nx, ny)) {
            if (f_10F7_04EC(plane, nx, ny) || GetMap(plane, nx, ny) == 0x38)
                done = 1;
        }
    }
    if (done)
        done = f_10F7_054D(plane, nx, ny, fd_3D57_0C22, 8, 0);
    if (done) {
        fd_50F6_0496 = d;
        if (!((*(unsigned char far *)0x417L & 3) && (*(unsigned char far *)0x417L & 8))) {
            fd_50F6_04C2 = 0x10;
            fd_3D57_0C22 = 0xfd;
        }
        f_10F7_0A44(fd_50F6_048C, fd_50F6_047C, fd_50F6_048A, fd_50F6_04C2, fd_50F6_0496, 0xff);
        f_00DF_00E8(0x1c, 0, 0x7e);
    }
    return done;
}

int far f_10F7_1AAE(int plane, int x, int y)
{
    int tile;
    int done;

    if (fd_50F6_04C2 != 0x10 && fd_50F6_04C2 != 0x30)
        return 0;
    done = 0;
    tile = GetMap(plane, x, y);
    if (plane <= 1) {
        if (f_10F7_0731(plane, tile)) {
            if (x < 0x40) {
                if (fd_3D57_0224[y] == x) {
                    fd_3E1D_2180[y][0] = 0x18;
                    done = 1;
                }
            } else if (fd_3D57_0264[y] == x) {
                fd_3E1D_3180[y][0] = 0x18;
                done = 1;
            }
            if (done) {
                if (fd_50F6_0F24 == 0)
                    fd_3E1D_0180[x][y] = 0x50;
                else
                    fd_3E1D_0180[x][y] = SRand1(7) + 0x59;
            } else {
                if (fd_50F6_0F24 == 0)
                    fd_3E1D_0180[x][y] = SRand16();
                else
                    fd_3E1D_0180[x][y] = 0;
                done = 1;
            }
        }
    } else if (tile == 0x30) {
        f_10F7_08CE(plane, x, y, SRand8());
        done = 1;
    } else if (tile == 0x31) {
        if (plane == 2) {
            fd_3E1D_2180[x][y] = 0x18;
            fd_3E1D_0180[fd_3D57_0224[x]][x] = 0x50;
        } else {
            fd_3E1D_3180[x][y] = 0x18;
            fd_3E1D_0180[fd_3D57_0264[x]][x] = 0x50;
        }
        done = 1;
    }
    if (done) {
        if (fd_50F6_04C2 == 0x10)
            fd_50F6_04C2 = 0x28;
        else
            fd_50F6_04C2 = 0x48;
        f_00DF_00E8(0x1e, 0, 0x7e);
    }
    return done;
}

int far f_10F7_1C84(int far *index, int plane, int x, int y)
{
    int i;
    int life;
    int direction;
    int state;
    int column;
    int lifeField;

    life = f_10F7_07C7(plane, x, y);
    if (f_10F7_06BF(life) && !f_10F7_003A(life)) {
        *index = f_10F7_03B7(plane, x, y, life);
        return life;
    }
    i = f_10F7_02D6(plane, x, y, 1, 7, 0x7f);
    if (i >= 0) {
        f_10F7_005D(plane, i, &lifeField, &column, &life, &state, &direction);
        *index = i;
        return life;
    }
    *index = -1;
    return -1;
}

int far f_10F7_1D31(int far *index, int plane, int x, int y)
{
    int i;
    int life;
    int direction;
    int state;
    int column;
    int lifeField;

    life = f_10F7_07C7(plane, x, y);
    if (life >= 0 && !f_10F7_003A(life)) {
        *index = f_10F7_03B7(plane, x, y, life);
        return life;
    }
    i = f_10F7_02D6(plane, x, y, 1, 0x7f, 0x7f);
    if (i >= 0) {
        f_10F7_005D(plane, i, &lifeField, &column, &life, &state, &direction);
        *index = i;
        return life;
    }
    *index = -1;
    return -1;
}

void far f_10F7_1DD3(int health)
{
    if (!fd_3D57_0C16)
        fd_50F6_0F78 = health;
    else
        fd_50F6_0F78 = 100;
    if (fd_50F6_0F78 > 0)
        fd_50F6_1006 = 0;
    if (fd_50F6_0F78 > 100)
        fd_50F6_0F78 = 100;
    else if (fd_50F6_0F78 < 0)
        fd_50F6_0F78 = 0;
    if (fd_50F6_0F78 > fd_50F6_0FBA && fd_50F6_0F78 >= 10)
        fd_50F6_1044 = 0;
    else
        fd_50F6_1044 = 1;
}

void far f_10F7_1E71(int kind)
{
    switch (kind) {
    case 0:
        f_00DF_00E8(0x2c, 0, 0x7e);
        o14_384C_0ACD(1);
        break;
    case 1:
        o22_39C7_188D(0x2396, -1);
        fd_50F6_0472 = 0L;
        f_15D9_009C(fd_50F6_034C[11], 120L, 0);
        break;
    case 2:
        f_15D9_009C(fd_50F6_034C[12], 120L, 0);
        break;
    case 3:
        f_00DF_00E8(0x2c, 0, 0x7e);
        while (!f_00DF_012D())
            f_00F8_0265(5L);
        f_00DF_00E8(10, 0, 0x7e);
        fd_50F6_0472 = 0L;
        f_15D9_009C(fd_50F6_034C[13], 180L, 0);
        break;
    }
    if (kind != 2) {
        if (fd_50F6_0F78 + 100 > 100 && kind != 1 && fd_50F6_0330 - 1 > 0) {
            fd_50F6_10BE += fd_50F6_0F78 / (fd_50F6_0330 - 1);
            if (fd_50F6_10BE > 100)
                fd_50F6_10BE = 100;
        }
        f_10F7_1DD3(100);
    } else if (fd_50F6_0F78 > 10)
        f_10F7_1DD3(fd_50F6_0F78 - 10);
}

int far f_10F7_1FDF(int plane, int x, int y)
{
    int egg;
    int index;

    if (fd_50F6_04C2 == 0x10 || fd_50F6_0F78 < 10) {
        fd_3D57_0C22 = 0xfd;
        egg = f_10F7_1C84(&index, plane, x, y);
        if (egg >= 0) {
            f_10F7_01B1(plane, index, 0, 0, 0, 0, 0);
            if (x != fd_50F6_047C || y != fd_50F6_048A)
                f_10F7_05FE(plane, x, y, 0);
            if (fd_50F6_0F78 >= 10) {
                f_00DF_00E8(0x1c, 0, 0x7e);
                fd_3D57_0C22 = egg;
                fd_50F6_04C2 = 8;
            } else
                fd_3D57_0C26 = 3;
            return 1;
        }
    }
    return 0;
}

int far f_10F7_20BF(int plane, int x, int y)
{
    int eat;
    int tile;

    if (!f_10F7_0787(plane, x, y))
        return 0;
    if (fd_50F6_1044)
        eat = 1;
    else if (fd_50F6_04C2 == 0x10 || fd_50F6_04C2 == 0x30)
        eat = 0;
    else
        return 0;
    if (plane <= 1) {
        f_0BE8_0798(x, y);
        if (!eat) {
            fd_50F6_04C4 = 200;
            fd_50F6_0B1E = f_0BE8_0B83(x, y, fd_3D57_02AC[0], fd_3D57_02AC[1]);
            fd_50F6_0C38 = fd_50F6_0B1E + 1;
            f_1496_043C(x, y, fd_50F6_04C4);
        }
    } else {
        tile = GetMap(plane, x, y);
        if (tile == 0x10)
            tile = SRand8();
        else
            tile--;
        f_10F7_08CE(plane, x, y, tile);
        if (plane == 2) {
            if (fd_50F6_1050 > 0)
                fd_50F6_1050--;
        } else if (fd_50F6_1060 > 0)
            fd_50F6_1060--;
    }
    if (eat)
        fd_3D57_0C26 = 0;
    else {
        f_00DF_00E8(0x1d, 0, 0x7e);
        fd_50F6_04C2 += 8;
    }
    return 1;
}

int far f_10F7_220C(int first, int second, int third, int fourth, int fifth)
{
    switch (fd_50F6_04C2) {
    case 8:
        return f_10F7_18B0(first, second, third, fourth, fifth);
    case 0x18:
    case 0x38:
        return f_10F7_1396(first, second, third, fourth, fifth);
    case 0x28:
    case 0x48:
        return f_10F7_1696(first, second, third, fourth, fifth);
    }
    return 0;
}

int far f_10F7_227A(int plane, int x, int y)
{
    int result;

    if (fd_50F6_04C2 & 8)
        return 0;
    result = f_10F7_1FDF(plane, x, y);
    if (result == 0) {
        result = f_10F7_1AAE(plane, x, y);
        if (result == 0)
            result = f_10F7_20BF(plane, x, y);
    }
    return result;
}

/* SCAFFOLD BEGIN: f_10F7_22CE unrecovered (adds no CONST words). */
int far f_10F7_22CE(int plane, int x, int y, int p4, int p5, int p6, int p7)
{
    return 0;
}
/* SCAFFOLD END */

int far f_10F7_245C(int x)
{
    if (!fd_50F6_0F24)
        return x <= 0x50;
    return x <= 0x5f;
}

int far f_10F7_2489(int plane, int x, int y)
{
    int tile;
    int ok;

    tile = GetMap(plane, x, y);
    if (tile < 0)
        ok = 0;
    else if (plane <= 1) {
        if (!fd_50F6_0F24)
            ok = tile <= 0x53;
        else
            ok = f_10F7_245C(tile);
    } else if (tile <= 0x18 || f_10F7_0731(plane, tile))
        ok = 1;
    else
        ok = 0;
    return ok;
}

int far f_10F7_24EE(int plane, int x, int y)
{
    int tile;

    if (plane >= 2 && f_10F7_2894(x, y)) {
        tile = GetMap(plane, x, y);
        if (IsItDirt(tile))
            return 1;
        if (f_10F7_06E4(plane, tile))
            return 1;
    }
    return 0;
}

int far f_10F7_2548(int plane, int x, int y)
{
    int life;

    if (!f_10F7_2640(plane))
        return 0;
    if (fd_50F6_0A06 == 1) {
        if (plane > 1)
            return 0;
        if (f_0BE8_0B83(x * 16 + 8, y * 16 + 8, fd_50F6_0F12, fd_50F6_0F34) < 0x200)
            return 1;
        return 0;
    }
    switch (plane) {
    case 0:
    case 1:
        life = fd_3E1D_6180[x][y];
        break;
    case 2:
        life = fd_3E1D_8180[x][y];
        break;
    case 3:
        life = fd_3E1D_9180[x][y];
        break;
    }
    return f_10F7_003A(life);
}

int far f_10F7_2613(int x)
{
    if (!fd_50F6_0F24)
        return x < 0x50;
    return x < 0x59;
}

int far f_10F7_2640(int plane)
{
    if (fd_50F6_048C == (plane == 0 ? 1 : plane))
        return 1;
    return 0;
}

int far f_10F7_266E(int plane, int x, int y)
{
    int tile;
    int eggIndex;
    int egg;

    egg = f_10F7_1C84(&eggIndex, plane, x, y);
    tile = GetMap(plane, x, y);
    return f_10F7_070B(plane, tile) || f_10F7_0731(plane, tile) || f_10F7_06BF(egg);
}

int far f_10F7_26D4(int plane, int x, int y)
{
    int dir;
    int result;

    if (fd_50F6_04C2 & 8)
        result = f_10F7_220C(plane, fd_50F6_047C, fd_50F6_048A, x, y) ? 1 : -1;
    else if (!f_10F7_227A(plane, x, y)) {
        if ((fd_3D57_0798 || (fd_50F6_04C2 == 0x40 && !fd_3D57_0C24)) &&
            fd_50F6_048C == 1 && fd_50F6_047C == x && fd_50F6_048A == y) {
            if (f_14EE_0002(x, y)) {
                o25_3BA4_1035();
                f_015B_06A2();
                result = 1;
            } else
                result = -1;
        } else
            result = 0;
    } else {
        dir = f_0BE8_0B21(fd_50F6_047C, fd_50F6_048A, x, y);
        if (dir > 0)
            f_10F7_0ACE(fd_50F6_048C, fd_50F6_047C, fd_50F6_048A, fd_50F6_04C2, dir - 1);
        f_0250_0E91();
        if (fd_3D57_0C26 >= 0) {
            f_10F7_1E71(fd_3D57_0C26);
            fd_3D57_0C26 = -1;
        }
        result = 1;
    }
    return result;
}

int far f_10F7_2821(int plane, int x, int y)
{
    if (plane <= 1)
        return f_0894_23BB(x, y);
    if (y > 0)
        return 0;
    if (GetMap(plane, x, y) == 0x18)
        return 1;
    return 0;
}

int far f_10F7_2867(int x, int y)
{
    if (x >= 0 && x <= 127 && y >= 0 && y <= 63)
        return 1;
    return 0;
}

int far f_10F7_2894(int x, int y)
{
    if (x >= 0 && x <= 63 && y >= 0 && y <= 63)
        return 1;
    return 0;
}
