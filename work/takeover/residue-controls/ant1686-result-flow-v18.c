/* Overlay section S25, code frame 3BA4: yellow ant movement (DoAntMoveY unit).
 * Built /AL /Os /Oe /Og /Zi.  The order of the extern declarations is part of the
 * fingerprint: MSC 6.00A breaks some operand-order ties by symbol-table state
 * (ExitNest's MePlane/MeGoalPlane compare, GetMyDis' GetDis call order), and this
 * order (0D6C/0EF8 first, MeLastX/Y before MeGoalY, entrance arrays A4,B0,A8,AC)
 * reproduces them. */
extern int far fd_50F6_0D6C;
extern int far fd_50F6_0EF8;

extern int far fd_50F6_0AA0;
extern int far fd_50F6_0A8E;
extern int far fd_50F6_07C0;
extern int far fd_50F6_08DA;
extern int far f_10F7_005D(int list, int index, int far *x, int far *y,
                           int far *attr, int far *state, int far *dir);
extern int far fd_50F6_084E;
extern int far fd_50F6_048C;
extern int far fd_50F6_047C;
extern int far ABS(int value);
extern int far fd_50F6_0AD6;
extern int far fd_50F6_048A;
extern int far f_0BE8_0B21(int x1, int y1, int x2, int y2);
extern int far fd_50F6_0496;
extern void far DoEditUpdateDraw(void);
extern int far fd_50F6_08E2;
extern int far fd_50F6_09F0;
extern int far fd_50F6_0AB6;
extern int far fd_50F6_0AC6;
extern int far fd_50F6_0AE8;
extern int far fd_50F6_0AF8;
extern signed char far Dx9[];
extern signed char far Dy9[];
extern int far TryMyDropOrLift(int plane, int x, int y);
int far o25_3BA4_1A9F(int plane, int x, int y, int gplane, int gx, int gy);
extern signed char far fd_3D57_0008[];
extern int far fd_50F6_04C2;
extern signed char far fd_3D57_0000[];
extern void far f_10F7_0ACE(int plane, int x, int y, int type, int dir);
extern int far fd_50F6_0C3E;
extern int far fd_50F6_04C4;
extern int far fd_50F6_04E2;
extern void far f_1496_043C(int, int, int);
extern void far f_1496_0474(int, int, int);
extern int far fd_50F6_104E;
extern void far f_1496_034D(int, int, int);
extern void far f_14EE_0C9C(int x, int y);
extern void far f_14EE_0D71(int x, int y);
extern int far fd_3D57_0C24;
extern int far fd_50F6_10BE;
extern int far fd_3D57_0C18;
extern int far fd_50F6_0F78;
extern void far f_10F7_1DD3(int health);
extern int far f_0894_23BB(int, int);
extern void far f_10F7_0B40(void);
void far o25_3BA4_1035(void);
extern int far MapPlane;
extern int far fd_3D57_07A8[];
extern void far f_015B_06A2(void);
void far ExitNest(void);
extern int far GetMap(int plane, int x, int y);
extern void far f_10F7_09A8(int plane, int x, int y, int type, int dir);
extern void far f_10F7_0A44(int plane, int x, int y, int type, int dir, int code);
extern void far f_00DF_00E8(int sound, int a, int b);
extern void far * far * far fd_50F6_034C;
extern void far EditMessage(void far *, long, int);
extern int far fd_50F6_1058;
void far o25_3BA4_0DFB(int list, int index);
extern void far f_10F7_01B1(int list, int index, int x, int y,
                            int attr, int state, int dir);
extern void far f_10F7_05FE(int plane, int x, int y, int value);
extern void far f_10F7_1E71(int kind);
extern void far o22_39C7_07FD(int plane, int x, int y);
extern int far fd_50F6_0F24;
extern unsigned char far fd_3E1D_0180[128][64];
extern void far o22_39C7_0D21(int code);

/* DoAntMoveY: exact body and relocation evidence. The folded unsigned
 * attribute range check is STEERED: it reproduces the stack-slot use ranking,
 * but the eliminated expression in the original source is unknown. */
void far DoAntMoveY(void)
{
    int dir;
    int x;
    int result;
    int ty;
    int tattr;
    int tx;
    int tdir;
    int tstate;
    int y;
    int d;
    int dx;
    int dy;
    int tile;

    if (fd_50F6_0AA0 == 0)
        return;
    result = 0;
    if (fd_50F6_0A8E >= 3) {
        if (f_10F7_005D(fd_50F6_08DA, fd_50F6_07C0, &tx, &ty, &tattr, &tstate, &tdir) == 0
            || (((unsigned)tattr >= 0) && ((fd_50F6_084E ^ tattr) & 0xf0) != 0)) {
            result = -2;
            goto done;
        }
        if (fd_50F6_048C == fd_50F6_08DA) {
            dx = ABS(fd_50F6_047C - tx);
            dy = ABS(fd_50F6_048A - ty);
            if (dx <= 1 && dy <= 1) {
                d = f_0BE8_0B21(fd_50F6_047C, fd_50F6_048A, tx, ty) - 1;
                if (d >= 0)
                    fd_50F6_0496 = d;
                DoEditUpdateDraw();
                goto moved;
            }
        }
        fd_50F6_0AD6 = fd_50F6_08E2 = tx;
        fd_50F6_0AE8 = fd_50F6_09F0 = ty;
    }
    if (fd_50F6_0A8E == 1 && fd_50F6_0AF8 == fd_50F6_048C) {
        dir = f_0BE8_0B21(fd_50F6_047C, fd_50F6_048A, fd_50F6_0AD6, fd_50F6_0AE8);
        x = Dx9[dir] + fd_50F6_047C;
        y = Dy9[dir] + fd_50F6_048A;
        if (x < 0 || x > 0x7f)
            x = fd_50F6_047C;
        if (y < 0 || y > 0x3f)
            y = fd_50F6_048A;
        if (fd_50F6_0AD6 == x && fd_50F6_0AE8 == y) {
            if ((result = TryMyDropOrLift(fd_50F6_048C, x, y)) != 0) {
                result = (result == 1) ? -1 : -2;
                goto done;
            }
        }
    }
    d = o25_3BA4_1A9F(fd_50F6_048C, fd_50F6_047C, fd_50F6_048A,
                      fd_50F6_0AF8, fd_50F6_0AD6, fd_50F6_0AE8);
    if (d < 0) {
        result = d;
        goto done;
    }
    x = fd_3D57_0000[d] + fd_50F6_047C;
    y = fd_3D57_0008[d] + fd_50F6_048A;
    fd_50F6_0AB6 = fd_50F6_047C;
    fd_50F6_0AC6 = fd_50F6_048A;
    f_10F7_0ACE(fd_50F6_048C, x, y, fd_50F6_04C2, d);
    fd_50F6_0C3E++;
    if (fd_50F6_048C == 1) {
        if (fd_50F6_04C4 > 0 && (fd_50F6_04C2 == 0x18 || fd_50F6_04C2 == 0x38)) {
            if (fd_50F6_04E2 == 0)
                f_1496_043C(fd_50F6_047C, fd_50F6_048A, fd_50F6_04C4);
            else
                f_1496_0474(fd_50F6_047C, fd_50F6_048A, fd_50F6_04C4);
            if (fd_50F6_04C4 > 10)
                fd_50F6_04C4--;
        }
        if (fd_50F6_104E != 0)
            f_1496_034D(fd_50F6_047C, fd_50F6_048A, 50);
    } else if (fd_50F6_048C == 2)
        f_14EE_0C9C(fd_50F6_047C, fd_50F6_048A);
    else
        f_14EE_0D71(fd_50F6_047C, fd_50F6_048A);
    if (fd_50F6_0C3E & 1) {
        if (fd_50F6_04C2 == 0x40 && fd_3D57_0C24 == 0 && fd_50F6_10BE > 0 && fd_3D57_0C18 == 0)
            fd_50F6_10BE--;
        f_10F7_1DD3(fd_50F6_0F78 - 1);
    }
    if (fd_50F6_048C == 1) {
        if (f_0894_23BB(fd_50F6_047C, fd_50F6_048A) == 0)
            goto done;
        if (fd_50F6_0AF8 > 1 || (fd_50F6_0AF8 == fd_50F6_048C && fd_50F6_0AD6 == fd_50F6_047C
                                 && fd_50F6_0AE8 == fd_50F6_048A)) {
            f_10F7_0B40();
            d = fd_50F6_048C;
            o25_3BA4_1035();
            if (fd_50F6_0AF8 != d || fd_50F6_0AD6 != x || fd_50F6_0AE8 != y
                || fd_50F6_048C == MapPlane)
                goto done;
            if (fd_3D57_07A8[0] == 0)
                f_015B_06A2();
            goto moved;
        }
        goto done;
    }
    if (fd_50F6_048A == 0) {
        f_10F7_0B40();
        d = fd_50F6_048C;
        ExitNest();
        if (fd_50F6_0AF8 != d || fd_50F6_0AD6 != x || fd_50F6_0AE8 != y
            || fd_50F6_048C == MapPlane)
            goto done;
        if (fd_3D57_07A8[0] == 0)
            f_015B_06A2();
        goto moved;
    }
    if (GetMap(fd_50F6_048C, fd_50F6_0AD6, fd_50F6_0AE8) != 0x14)
        goto done;
    if (fd_50F6_04C2 == 0x60 || fd_50F6_0AD6 != fd_50F6_047C || fd_50F6_0AE8 != fd_50F6_048A)
        goto done;
    f_10F7_09A8(fd_50F6_048C, fd_50F6_047C, fd_50F6_048A, fd_50F6_04C2, fd_50F6_0496);
    if (fd_50F6_048C == 2)
        fd_50F6_048C = 3;
    else
        fd_50F6_048C = 2;
    f_10F7_0A44(fd_50F6_048C, fd_50F6_047C, fd_50F6_048A, fd_50F6_04C2, fd_50F6_0496, 0xff);
    f_00DF_00E8(1, 0, 0x7e);
    f_015B_06A2();
    if (fd_50F6_048C == 3)
        EditMessage(fd_50F6_034C[4], 360L, 0);
moved:
    result = -1;
done:
    if (fd_3D57_07A8[0] != 0)
        f_015B_06A2();
    if (result == 0 && fd_50F6_0AF8 == fd_50F6_048C && fd_50F6_0AD6 == fd_50F6_047C
        && fd_50F6_0AE8 == fd_50F6_048A && fd_50F6_0A8E == 0)
        result = -1;
    if (result == 0)
        return;
    if (result == -2) {
        f_00DF_00E8(1, 0, 0x7e);
        f_015B_06A2();
    } else if (fd_50F6_0A8E == 3) {
        fd_50F6_1058 = 1;
        o25_3BA4_0DFB(fd_50F6_08DA, fd_50F6_07C0);
        fd_50F6_1058 = 0;
    } else if (fd_50F6_0A8E == 4) {
        d = f_0BE8_0B21(tx, ty, fd_50F6_047C, fd_50F6_048A) - 1;
        if (d >= 0 && (tattr & 0x70) != 0x60) {
            tattr = (tattr & 0xf8) | d;
            f_10F7_01B1(fd_50F6_048C, fd_50F6_07C0, tx, ty, tattr, tstate, tdir);
            f_10F7_05FE(fd_50F6_048C, tx, ty, tattr);
            DoEditUpdateDraw();
        }
        f_10F7_1E71(1);
    }
    o22_39C7_07FD(fd_50F6_048C, fd_50F6_047C, fd_50F6_048A);
    if (fd_50F6_0F24 != 0 && fd_50F6_048C == 1) {
        tile = fd_3E1D_0180[fd_50F6_047C][fd_50F6_048A];
        if (tile == 0x76 || tile == 0x78)
            o22_39C7_0D21(10);
    }
}

extern int far fd_50F6_0A06;
extern unsigned char far fd_50F6_0F08;
extern int far f_0BE8_0BC1(int x, int y);
extern int far SRand128(void);
extern void far f_0BE8_0A5B(int x, int y, int type);
extern void far o25_39C7_15B4(void);
extern void far f_0BE8_0ABE(int x, int y, int type);
extern void far f_0F3F_143C(void);
extern int far fd_50F6_1006;

void far DoAntSimY(void)
{
    int newy, newx;
    int mapval;
    int bx;

    if (fd_50F6_0A06 != 0)
        return;

    f_10F7_0A44(fd_50F6_048C, fd_50F6_047C, fd_50F6_048A, fd_50F6_04C2, fd_50F6_0496, 0xff);

    if (!(fd_50F6_0F08 & 0x3f))
        f_10F7_1DD3(fd_50F6_0F78 - 1);

    if (fd_50F6_048C >= 2) {
        mapval = GetMap(fd_50F6_048C, fd_50F6_047C, fd_50F6_048A);
        if (mapval >= 0x4e)
            f_10F7_1DD3(fd_50F6_0F78 - 1);
    }

    if (fd_50F6_04C2 == 0x60 && fd_50F6_048C > 1 && !(fd_50F6_0F08 & 0xf)) {
        bx = fd_50F6_0496 ^ 4;
        newx = fd_50F6_047C + 2 * fd_3D57_0000[bx];
        newy = fd_50F6_048A + 2 * fd_3D57_0008[bx];
        if (f_0BE8_0BC1(newx, newy)) {
            if (SRand128() <= fd_50F6_0F78) {
                if (fd_50F6_04E2 == 0) {
                    f_0BE8_0A5B(newx, newy, 1);
                    o25_39C7_15B4();
                } else {
                    f_0BE8_0ABE(newx, newy, 1);
                    f_0F3F_143C();
                }
                f_10F7_1DD3(fd_50F6_0F78 - 5);
            }
        }
    }

    if (fd_50F6_0F78 <= 0) {
        if (++fd_50F6_1006 >= 100) {
            if (fd_50F6_048C >= 2 && mapval >= 0x4e)
                o22_39C7_0D21(7);
            else
                o22_39C7_0D21(8);
        }
    }
}

extern int _fastcall win_IsWinInFront(int v);
extern long far MacTickCount(void);
extern void far myDelay(long);
extern void far f_00DF_015C(void);
extern int far SRand2(void);
extern int far mySongIsDone(void);
extern void far f_10F7_08CE(int plane, int x, int y, int value);
extern int far SRand8(void);

void far o25_3BA4_0999(int plane, int x, int y, int dir, int type, int kind)
{
    long t;
    int count;
    int tile;
    int i;
    int n;
    int svY;
    int svType;
    int svDir;
    int svPlane;
    int svX;

    f_10F7_0A44(fd_50F6_048C, fd_50F6_047C, fd_50F6_048A, fd_50F6_04C2, fd_50F6_0496, 0xff);
    DoEditUpdateDraw();
    svPlane = plane;
    svX = x;
    svY = y;
    svType = fd_50F6_04C2;
    svDir = dir;
    if (kind == 0)
        count = 6;
    else if (win_IsWinInFront(0))
        count = fd_3D57_07A8[1] ? 0x40 : 0x20;
    else
        count = 8;
    if (kind == 10) {
        tile = fd_3E1D_0180[x][y];
        count = 0x20;
    }
    if (kind == 2)
        n = 3;
    t = MacTickCount();
    for (i = 0; i < count; i++) {
        while (MacTickCount() <= t)
            myDelay(1L);
        t = MacTickCount() + 6;
        f_00DF_015C();
        if (kind == 0 && SRand2())
            f_00DF_00E8(0x25, 0x32c8, 0x7e);
        if (kind == 10) {
            f_00DF_00E8(0x31, 0x55f0, 0x7f);
            fd_3E1D_0180[x][y] = SRand2() ? tile - 3 : tile;
        }
        if (kind != 0 && kind < 10 && fd_3D57_07A8[1] != 0 && mySongIsDone())
            break;
        if (kind == 2) {
            f_10F7_08CE(plane, x, y, n + 0x38);
            if (n < 5)
                n++;
            else if (n > 3)
                n--;
        }
        f_10F7_0ACE(plane, x, y, type, SRand8());
        DoEditUpdateDraw();
    }
    if (kind == 10)
        fd_3E1D_0180[x][y] = tile;
    f_10F7_09A8(plane, x, y, type, fd_50F6_0496);
    fd_50F6_048C = svPlane;
    fd_50F6_047C = svX;
    fd_50F6_048A = svY;
    fd_50F6_04C2 = svType;
    fd_50F6_0496 = svDir;
}

extern int far WinPrintf(char far *format, ...);
extern long far f_0BE8_0B83(int x1, int y1, int x2, int y2);
extern int far RRand(int range);
extern int far o25_39C7_0CBD(int plane, int x, int y, int gx, int gy);

void far o25_3BA4_0C01(int plane, int x, int y, int dir, int type)
{
    long t;
    int d;
    int i;
    int count;
    int svY;
    int svX;
    int svType;
    int svDir;
    int svPlane;

    WinPrintf("AnimYellowInsane");
    f_10F7_0A44(fd_50F6_048C, fd_50F6_047C, fd_50F6_048A, fd_50F6_04C2, fd_50F6_0496, 0xff);
    DoEditUpdateDraw();
    svPlane = plane;
    svX = x;
    svY = y;
    svType = fd_50F6_04C2;
    svDir = dir;
    count = win_IsWinInFront(0) ? 0x20 : 8;
    t = MacTickCount();
    for (i = 0; i < count; i++) {
        while (MacTickCount() <= t)
            myDelay(1L);
        t = MacTickCount() + 3;
        f_00DF_015C();
        if ((int)f_0BE8_0B83(x, y, svX, svY) == 0 && count - i - 1 != 0)
            d = o25_39C7_0CBD(plane, x, y, RRand(7) + x - 3, RRand(7) + y - 3);
        else
            d = o25_39C7_0CBD(plane, x, y, svX, svY);
        if (d >= 0) {
            x += fd_3D57_0000[d];
            y += fd_3D57_0008[d];
        } else
            d = SRand8();
        f_10F7_0ACE(plane, x, y, type, d);
        WinPrintf("2");
        DoEditUpdateDraw();
    }
    f_10F7_09A8(plane, x, y, type, fd_50F6_0496);
    fd_50F6_048C = svPlane;
    fd_50F6_047C = svX;
    fd_50F6_048A = svY;
    fd_50F6_04C2 = svType;
    fd_50F6_0496 = svDir;
    WinPrintf("3");
}

extern unsigned char far AlistX[];
extern unsigned char far AlistY[];
extern unsigned char far AlistT[];
extern unsigned char far BlistX[];
extern unsigned char far BlistY[];
extern unsigned char far BlistT[];
extern unsigned char far RlistX[];
extern unsigned char far RlistY[];
extern unsigned char far RlistT[];
extern void far ClearLife(int plane, int x, int y, int value);
extern int far f_0894_1E34(int a, int b);
extern void far DeadAntHere(int x, int y, int type);

void far o25_3BA4_0DFB(int list, int index)
{
    int type;
    unsigned char far *pl;
    unsigned char far *px;
    unsigned char far *py;

    if (list <= 1) {
        px = AlistX;
        py = AlistY;
        pl = AlistT;
    } else if (list == 2) {
        px = BlistX;
        py = BlistY;
        pl = BlistT;
    } else {
        px = RlistX;
        py = RlistY;
        pl = RlistT;
    }
    ClearLife(list, px[index], py[index], pl[index]);
    type = f_0894_1E34(fd_50F6_04C2, pl[index]);
    if (fd_50F6_04C2 != type)
        f_015B_06A2();
    o25_3BA4_0999(fd_50F6_048C, fd_50F6_047C, fd_50F6_048A, fd_50F6_0496, 0x70, 0);
    if (fd_50F6_04C2 == type) {
        f_10F7_0A44(fd_50F6_048C, fd_50F6_047C, fd_50F6_048A, fd_50F6_04C2, fd_50F6_0496, 0xff);
        if (list <= 1)
            DeadAntHere(px[index], py[index], pl[index] & 0x80);
        pl[index] = 0;
        if (fd_50F6_0A8E == 3 && fd_50F6_048C == fd_50F6_08DA && fd_50F6_07C0 == index)
            o22_39C7_07FD(fd_50F6_048C, fd_50F6_047C, fd_50F6_048A);
    } else {
        f_10F7_05FE(list, px[index], py[index], pl[index]);
        if (list <= 1)
            DeadAntHere(fd_50F6_047C, fd_50F6_048A, fd_50F6_04E2);
        o22_39C7_0D21(0);
    }
}

extern void far f_0BE8_0EB7(void);
extern void far o22_39C7_1A57(int state, int quiet);
extern void far DigMyTile(int plane, int x, int y);
extern unsigned char far fd_3D57_0224[];
extern void far MakeNewHoleB(int x);
extern unsigned char far fd_3D57_0264[];
extern void far f_14EE_0367(int x);
extern signed char far fd_3D57_006C[];
extern int far IsNotObstacle(int plane, int x, int y);

/* SCAFFOLD BEGIN: o25_3BA4_1035 (EnterNest) best draft: 3 bytes differ, the merged DigMyTile call loads &MeLocX via bx instead of si (register tie-break); the if/else with identical arms reproduces the dead "les bx,[bp-14h]" of the original */
void far o25_3BA4_1035(void)
{
    f_0BE8_0EB7();
    if (fd_50F6_104E != 0)
        o22_39C7_1A57(0, 1);
    f_10F7_09A8(fd_50F6_048C, fd_50F6_047C, fd_50F6_048A, fd_50F6_04C2, fd_50F6_0496);
    if (fd_50F6_047C > 0x40)
        fd_50F6_048C = 3;
    else
        fd_50F6_048C = 2;
    fd_50F6_047C = fd_50F6_048A;
    if (fd_50F6_04C2 == 0x60)
        fd_50F6_048A = 2;
    else
        fd_50F6_048A = 1;
    fd_50F6_0496 = 4;
    if (fd_50F6_048C == 2)
        DigMyTile(fd_50F6_048C, fd_50F6_047C, fd_50F6_048A);
    else
        DigMyTile(fd_50F6_048C, fd_50F6_047C, fd_50F6_048A);
    f_10F7_0A44(fd_50F6_048C, fd_50F6_047C, fd_50F6_048A, fd_50F6_04C2, fd_50F6_0496, 0xff);
}
/* SCAFFOLD END */

void far ExitNest(void)
{
    int step;
    int nx;
    int ny;
    int dir;
    int i;
    int d;

    f_0BE8_0EB7();
    f_10F7_0A44(fd_50F6_048C, fd_50F6_047C, fd_50F6_048A, fd_50F6_04C2, fd_50F6_0496, 0);
    fd_50F6_048A = fd_50F6_047C & 0x3f;
    if (fd_50F6_048C == 2) {
        if (fd_3D57_0224[fd_50F6_048A] == 0)
            MakeNewHoleB(fd_50F6_047C);
        fd_50F6_047C = fd_3D57_0224[fd_50F6_048A];
    } else {
        if (fd_3D57_0264[fd_50F6_048A] == 0)
            f_14EE_0367(fd_50F6_047C);
        fd_50F6_047C = fd_3D57_0264[fd_50F6_048A];
    }
    step = (fd_50F6_04C2 == 0x60) ? 2 : 1;
    if (fd_50F6_0AF8 == 1) {
        d = f_0BE8_0B21(fd_50F6_047C, fd_50F6_048A, fd_50F6_0AD6, fd_50F6_0AE8);
        if (d > 0)
            d--;
    } else if (fd_50F6_048C == fd_50F6_0AF8) {
        if (fd_50F6_047C < 0x40)
            d = 2;
        else
            d = 6;
    } else {
        d = o25_3BA4_1A9F(1, fd_50F6_047C, fd_50F6_048A, fd_50F6_0AF8, fd_50F6_0AD6, fd_50F6_0AE8);
        if (d < 0)
            d = SRand8();
    }
    i = 0;
    dir = d;
    for (; i < 8; i++) {
        d = (fd_3D57_006C[i] + dir) & 7;
        nx = fd_3D57_0000[d] * step + fd_50F6_047C;
        ny = fd_3D57_0008[d] * step + fd_50F6_048A;
        if (IsNotObstacle(1, nx, ny)) {
            fd_50F6_047C = nx;
            fd_50F6_048A = ny;
            fd_50F6_0496 = d;
            break;
        }
    }
    if (i == 8) {
        fd_50F6_0496 = dir;
        fd_50F6_047C = (fd_50F6_047C + step) & 0x7f;
    }
    f_10F7_0A44(fd_50F6_048C = 1, fd_50F6_047C, fd_50F6_048A, fd_50F6_04C2, fd_50F6_0496, 0xff);
}

extern int far fd_3D57_02A4[2];
extern int far fd_3D57_02B0[2];
extern int far fd_3D57_02A8[2];
extern int far fd_3D57_02AC[2];

int far o25_3BA4_13AB(int p1, int x1, int y1, int p2, int x2, int y2)
{
    if (p2 == p1)
        return f_0BE8_0B83(x1, y1, x2, y2);
    if (p1 == 1 && p2 > p1) {
        if (p2 == 2)
            return f_0BE8_0B83(x1, y1, fd_3D57_02AC[0], fd_3D57_02AC[1])
                 + f_0BE8_0B83(fd_3D57_02A4[0], fd_3D57_02A4[1], x2, y2);
        return f_0BE8_0B83(x1, y1, fd_3D57_02B0[0], fd_3D57_02B0[1])
             + f_0BE8_0B83(fd_3D57_02A4[0], fd_3D57_02A4[1], x2, y2);
    }
    if (p2 == 1) {
        if (p1 == 2)
            return f_0BE8_0B83(x1, y1, fd_3D57_02A4[0], fd_3D57_02A4[1])
                 + f_0BE8_0B83(fd_3D57_02AC[0], fd_3D57_02AC[1], x2, y2);
        return f_0BE8_0B83(x1, y1, fd_3D57_02A8[0], fd_3D57_02A8[1])
             + f_0BE8_0B83(fd_3D57_02B0[0], fd_3D57_02B0[1], x2, y2);
    }
    if (p1 == 2)
        return f_0BE8_0B83(x1, y1, fd_3D57_02A4[0], fd_3D57_02A4[1])
             + f_0BE8_0B83(fd_3D57_02AC[0], fd_3D57_02AC[1], fd_3D57_02B0[0], fd_3D57_02B0[1])
             + f_0BE8_0B83(fd_3D57_02A8[0], fd_3D57_02A8[1], x2, y2);
    return f_0BE8_0B83(x1, y1, fd_3D57_02A8[0], fd_3D57_02A8[1])
         + f_0BE8_0B83(fd_3D57_02B0[0], fd_3D57_02B0[1], fd_3D57_02AC[0], fd_3D57_02AC[1])
         + f_0BE8_0B83(fd_3D57_02A4[0], fd_3D57_02A4[1], x2, y2);
}

extern int far TileCanBeMovedOn(int plane, int x, int y, int fromPlane, int fromX, int fromY, int digging);
extern int far f_10F7_07C7(int plane, int x, int y);
extern int far f_10F7_04EC(int plane, int x, int y);

int far o25_3BA4_1581(int plane, int x, int y, int a, int b)
{
    int best;
    int fallback;
    int flag;
    int threshold;
    int dir;
    int nx;
    int ny;
    int dis;

    best = -1;
    threshold = f_0BE8_0B83(x, y, a, b);
    if (threshold > 0) {
        fallback = -2;
        flag = (fd_50F6_0A8E == 2) ? 1 : 0;
        for (dir = 0; dir < 8; dir++) {
            nx = fd_3D57_0000[dir] + x;
            ny = fd_3D57_0008[dir] + y;
            if (TileCanBeMovedOn(plane, nx, ny, fd_50F6_0AF8, fd_50F6_0AD6, fd_50F6_0AE8, flag) != 0) {
                dis = f_0BE8_0B83(nx, ny, a, b);
                if (dis < threshold) {
                    if (f_10F7_07C7(plane, nx, ny) > 0 || f_10F7_04EC(plane, nx, ny) == 0)
                        fallback = dir;
                    else
                        best = dir;
                    threshold = dis;
                }
            }
        }
        if (best < 0)
            best = fallback;
    }
    return best;
}

int far o25_3BA4_1686(int far *rot, int far *dir, int plane, int x, int y, int a, int b)
{
    int flag;
    int d;
    int left;
    int best;
    register int result;
    int threshold;
    char ok[8];
    int i;
    int right;
    int nx;
    int ny;
    int dis;

    result = -1;
    threshold = f_0BE8_0B83(x, y, a, b);
    if (threshold > 0) {
        best = -2;
        flag = (fd_50F6_0A8E == 2) ? 1 : 0;
        for (i = 0; i < 8; i++) {
            nx = fd_3D57_0000[i] + x;
            ny = fd_3D57_0008[i] + y;
            if ((nx != fd_50F6_0AB6 || ny != fd_50F6_0AC6)
                && TileCanBeMovedOn(plane, nx, ny, fd_50F6_0AF8, fd_50F6_0AD6, fd_50F6_0AE8, flag)) {
                best = i;
                ok[i] = 1;
            } else
                ok[i] = 0;
        }
        if (best < 0) { result = best; goto done; }
        best = -1;
        left = right = *dir;
        if (*rot == 0) {
            for (i = 0; i < 8; i++) {
                if (ok[right]) {
                    best = right;
                    *dir = f_0BE8_0B21(x, y, a, b) - 1;
                    *rot = 1;
                    break;
                }
                if (ok[left]) {
                    best = left;
                    *dir = f_0BE8_0B21(x, y, a, b) - 1;
                    *rot = -1;
                    break;
                }
                right = (right + 1) & 7;
                left = (left - 1) & 7;
            }
        } else {
            for (i = 0; i < 8; i++) {
                if (*rot > 0) {
                    if (ok[right]) {
                        d = right;
                        goto found;
                    }
                } else if (ok[left]) {
                    right = left;
                    goto found;
                }
                right = (right + 1) & 7;
                left = (left - 1) & 7;
            }
        }
        result = best;
    }
done:
    return result;
found:
    dis = f_0BE8_0B83(fd_3D57_0000[right] + x, fd_3D57_0008[right] + y, a, b);
    if (dis <= threshold) {
        *dir = f_0BE8_0B21(x, y, a, b) - 1;
        *rot = 0;
    }
    result = right;
    goto done;
}

int far o25_3BA4_188A(int far *steps, int plane, int x, int y, int a, int b)
{
    int nx;
    int ny;
    int count;
    int dir;

    count = 0;
    dir = o25_3BA4_1581(plane, x, y, a, b);
    if (dir >= 0) {
        nx = fd_3D57_0000[dir] + x;
        ny = fd_3D57_0008[dir] + y;
        while (dir >= 0 && count < 0x40) {
            dir = o25_3BA4_1581(plane, nx, ny, a, b);
            if (dir >= 0) {
                nx += fd_3D57_0000[dir];
                ny += fd_3D57_0008[dir];
            }
            count++;
        }
    }
    *steps = count;
    if (dir >= 0)
        dir = -1;
    return dir;
}

extern int far fd_50F6_0EFA;

int far o25_3BA4_1935(int plane, int x, int y, int a, int b)
{
    int dir;
    int steps;

    if (o25_3BA4_188A(&steps, plane, x, y, a, b) == -2)
        dir = o25_3BA4_1686(&fd_50F6_0EFA, &fd_50F6_0EF8, plane, x, y, a, b);
    else {
        fd_50F6_0D6C = -1;
        dir = o25_3BA4_1581(plane, x, y, a, b);
    }
    return dir;
}

int far o25_3BA4_19AD(int far *rot, int far *dir, int plane, int x, int y, int a, int b)
{
    fd_50F6_0EF8 = f_0BE8_0B21(x, y, a, b) - 1;
    fd_50F6_0D6C = 0x10;
    fd_50F6_0EFA = 0;
    o25_3BA4_1686(&fd_50F6_0EFA, &fd_50F6_0EF8, plane, x, y, a, b);
}

int far o25_3BA4_1A0D(int plane, int x, int y, int a, int b)
{
    int dir;

    if (fd_50F6_0D6C < 0) {
        dir = o25_3BA4_1581(plane, x, y, a, b);
        if (dir == -2 && fd_50F6_0D6C == -2)
            dir = o25_3BA4_19AD(&fd_50F6_0EFA, &fd_50F6_0EF8, plane, x, y, a, b);
    } else {
        dir = o25_3BA4_1935(plane, x, y, a, b);
        fd_50F6_0D6C--;
    }
    return dir;
}

/* The result goes through a local that MSC eliminates (value only returned); as a
 * register candidate it still takes SI first, so p1 lands in DI as in the original. */
int far o25_3BA4_1A9F(int p1, int x1, int y1, int p2, int x2, int y2)
{
    int r;

    if (p1 <= 1) {
        if (p2 <= 1)
            r = o25_3BA4_1A0D(p1, x1, y1, x2, y2);
        else if (p2 == 2)
            r = o25_3BA4_1A0D(p1, x1, y1, fd_3D57_02AC[0], fd_3D57_02AC[1]);
        else
            r = o25_3BA4_1A0D(p1, x1, y1, fd_3D57_02B0[0], fd_3D57_02B0[1]);
    } else if (p2 == p1)
        r = o25_3BA4_1A0D(p1, x1, y1, x2, y2);
    else if (p1 == 2)
        r = o25_3BA4_1A0D(p1, x1, y1, fd_3D57_02A4[0], fd_3D57_02A4[1]);
    else
        r = o25_3BA4_1A0D(p1, x1, y1, fd_3D57_02A8[0], fd_3D57_02A8[1]);
    return r;
}
