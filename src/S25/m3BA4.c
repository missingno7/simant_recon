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
extern int far GetAntIndex(int list, int index, int far *x, int far *y,
                           int far *attr, int far *state, int far *dir);
extern int far fd_50F6_084E;
extern int far MePlane;
extern int far MeLocX;
extern int far ABS(int value);
extern int far fd_50F6_0AD6;
extern int far MeLocY;
extern int far GetDir(int x1, int y1, int x2, int y2);
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
extern signed char far Dy8[];
extern int far fd_50F6_04C2;
extern signed char far Dx8[];
extern void far MoveMyLife(int plane, int x, int y, int type, int dir);
extern int far fd_50F6_0C3E;
extern int far fd_50F6_04C4;
extern int far fd_50F6_04E2;
extern void far JamScentBT(int, int, int);
extern void far JamScentRT(int, int, int);
extern int far fd_50F6_104E;
extern void far AlarmHere(int, int, int);
extern void far f_14EE_0C9C(int x, int y);
extern void far f_14EE_0D71(int x, int y);
extern int far fd_3D57_0C24;
extern int far HealthB;
extern int far fd_3D57_0C18;
extern int far MeHealth;
extern void far SetMyHealth(int health);
extern int far IsItHole(int, int);
extern void far DoEditAndMapUpdateDraw(void);
void far o25_3BA4_1035(void);
extern int far MapPlane;
extern int far fd_3D57_07A8[];
extern void far GotoMyAnt(void);
void far ExitNest(void);
extern int far GetMap(int plane, int x, int y);
extern void far ClearMyLife(int plane, int x, int y, int type, int dir);
extern void far SetMyLife(int plane, int x, int y, int type, int dir, int code);
extern void far myBeginSound(int sound, int a, int b);
extern void far * far * far fd_50F6_034C;
extern void far EditMessage(void far *, long, int);
extern int far fd_50F6_1058;
void far o25_3BA4_0DFB(int list, int index);
extern void far SetAntIndex(int list, int index, int x, int y,
                            int attr, int state, int dir);
extern void far SetLife(int plane, int x, int y, int value);
extern void far EatMyFood(int kind);
extern void far ResetYellowVars(int plane, int x, int y);
extern int far TERRAINset;
extern unsigned char far MapA[128][64];
extern void far YellowDeath(int code);

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
        if (GetAntIndex(fd_50F6_08DA, fd_50F6_07C0, &tx, &ty, &tattr, &tstate, &tdir) == 0
            || (((unsigned)tattr >= 0) && ((fd_50F6_084E ^ tattr) & 0xf0) != 0)) {
            result = -2;
            goto done;
        }
        if (MePlane == fd_50F6_08DA) {
            dx = ABS(MeLocX - tx);
            dy = ABS(MeLocY - ty);
            if (dx <= 1 && dy <= 1) {
                d = GetDir(MeLocX, MeLocY, tx, ty) - 1;
                if (d >= 0)
                    fd_50F6_0496 = d;
                DoEditUpdateDraw();
                goto moved;
            }
        }
        fd_50F6_0AD6 = fd_50F6_08E2 = tx;
        fd_50F6_0AE8 = fd_50F6_09F0 = ty;
    }
    if (fd_50F6_0A8E == 1 && fd_50F6_0AF8 == MePlane) {
        dir = GetDir(MeLocX, MeLocY, fd_50F6_0AD6, fd_50F6_0AE8);
        x = Dx9[dir] + MeLocX;
        y = Dy9[dir] + MeLocY;
        if (x < 0 || x > 0x7f)
            x = MeLocX;
        if (y < 0 || y > 0x3f)
            y = MeLocY;
        if (fd_50F6_0AD6 == x && fd_50F6_0AE8 == y) {
            if ((result = TryMyDropOrLift(MePlane, x, y)) != 0) {
                result = (result == 1) ? -1 : -2;
                goto done;
            }
        }
    }
    d = o25_3BA4_1A9F(MePlane, MeLocX, MeLocY,
                      fd_50F6_0AF8, fd_50F6_0AD6, fd_50F6_0AE8);
    if (d < 0) {
        result = d;
        goto done;
    }
    x = Dx8[d] + MeLocX;
    y = Dy8[d] + MeLocY;
    fd_50F6_0AB6 = MeLocX;
    fd_50F6_0AC6 = MeLocY;
    MoveMyLife(MePlane, x, y, fd_50F6_04C2, d);
    fd_50F6_0C3E++;
    if (MePlane == 1) {
        if (fd_50F6_04C4 > 0 && (fd_50F6_04C2 == 0x18 || fd_50F6_04C2 == 0x38)) {
            if (fd_50F6_04E2 == 0)
                JamScentBT(MeLocX, MeLocY, fd_50F6_04C4);
            else
                JamScentRT(MeLocX, MeLocY, fd_50F6_04C4);
            if (fd_50F6_04C4 > 10)
                fd_50F6_04C4--;
        }
        if (fd_50F6_104E != 0)
            AlarmHere(MeLocX, MeLocY, 50);
    } else if (MePlane == 2)
        f_14EE_0C9C(MeLocX, MeLocY);
    else
        f_14EE_0D71(MeLocX, MeLocY);
    if (fd_50F6_0C3E & 1) {
        if (fd_50F6_04C2 == 0x40 && fd_3D57_0C24 == 0 && HealthB > 0 && fd_3D57_0C18 == 0)
            HealthB--;
        SetMyHealth(MeHealth - 1);
    }
    if (MePlane == 1) {
        if (IsItHole(MeLocX, MeLocY) == 0)
            goto done;
        if (fd_50F6_0AF8 > 1 || (fd_50F6_0AF8 == MePlane && fd_50F6_0AD6 == MeLocX
                                 && fd_50F6_0AE8 == MeLocY)) {
            DoEditAndMapUpdateDraw();
            d = MePlane;
            o25_3BA4_1035();
            if (fd_50F6_0AF8 != d || fd_50F6_0AD6 != x || fd_50F6_0AE8 != y
                || MePlane == MapPlane)
                goto done;
            if (fd_3D57_07A8[0] == 0)
                GotoMyAnt();
            goto moved;
        }
        goto done;
    }
    if (MeLocY == 0) {
        DoEditAndMapUpdateDraw();
        d = MePlane;
        ExitNest();
        if (fd_50F6_0AF8 != d || fd_50F6_0AD6 != x || fd_50F6_0AE8 != y
            || MePlane == MapPlane)
            goto done;
        if (fd_3D57_07A8[0] == 0)
            GotoMyAnt();
        goto moved;
    }
    if (GetMap(MePlane, fd_50F6_0AD6, fd_50F6_0AE8) != 0x14)
        goto done;
    if (fd_50F6_04C2 == 0x60 || fd_50F6_0AD6 != MeLocX || fd_50F6_0AE8 != MeLocY)
        goto done;
    ClearMyLife(MePlane, MeLocX, MeLocY, fd_50F6_04C2, fd_50F6_0496);
    if (MePlane == 2)
        MePlane = 3;
    else
        MePlane = 2;
    SetMyLife(MePlane, MeLocX, MeLocY, fd_50F6_04C2, fd_50F6_0496, 0xff);
    myBeginSound(1, 0, 0x7e);
    GotoMyAnt();
    if (MePlane == 3)
        EditMessage(fd_50F6_034C[4], 360L, 0);
moved:
    result = -1;
done:
    if (fd_3D57_07A8[0] != 0)
        GotoMyAnt();
    if (result == 0 && fd_50F6_0AF8 == MePlane && fd_50F6_0AD6 == MeLocX
        && fd_50F6_0AE8 == MeLocY && fd_50F6_0A8E == 0)
        result = -1;
    if (result == 0)
        return;
    if (result == -2) {
        myBeginSound(1, 0, 0x7e);
        GotoMyAnt();
    } else if (fd_50F6_0A8E == 3) {
        fd_50F6_1058 = 1;
        o25_3BA4_0DFB(fd_50F6_08DA, fd_50F6_07C0);
        fd_50F6_1058 = 0;
    } else if (fd_50F6_0A8E == 4) {
        d = GetDir(tx, ty, MeLocX, MeLocY) - 1;
        if (d >= 0 && (tattr & 0x70) != 0x60) {
            tattr = (tattr & 0xf8) | d;
            SetAntIndex(MePlane, fd_50F6_07C0, tx, ty, tattr, tstate, tdir);
            SetLife(MePlane, tx, ty, tattr);
            DoEditUpdateDraw();
        }
        EatMyFood(1);
    }
    ResetYellowVars(MePlane, MeLocX, MeLocY);
    if (TERRAINset != 0 && MePlane == 1) {
        tile = MapA[MeLocX][MeLocY];
        if (tile == 0x76 || tile == 0x78)
            YellowDeath(10);
    }
}

extern int far fd_50F6_0A06;
extern unsigned char far Cycle;
extern int far InNestBounds(int x, int y);
extern int far SRand128(void);
extern void far PlaceEggB(int x, int y, int type);
extern void far o25_39C7_15B4(void);
extern void far PlaceEggR(int x, int y, int type);
extern void far DecEatR(void);
extern int far fd_50F6_1006;

void far DoAntSimY(void)
{
    int newy, newx;
    int mapval;
    int bx;

    if (fd_50F6_0A06 != 0)
        return;

    SetMyLife(MePlane, MeLocX, MeLocY, fd_50F6_04C2, fd_50F6_0496, 0xff);

    if (!(Cycle & 0x3f))
        SetMyHealth(MeHealth - 1);

    if (MePlane >= 2) {
        mapval = GetMap(MePlane, MeLocX, MeLocY);
        if (mapval >= 0x4e)
            SetMyHealth(MeHealth - 1);
    }

    if (fd_50F6_04C2 == 0x60 && MePlane > 1 && !(Cycle & 0xf)) {
        bx = fd_50F6_0496 ^ 4;
        newx = MeLocX + 2 * Dx8[bx];
        newy = MeLocY + 2 * Dy8[bx];
        if (InNestBounds(newx, newy)) {
            if (SRand128() <= MeHealth) {
                if (fd_50F6_04E2 == 0) {
                    PlaceEggB(newx, newy, 1);
                    o25_39C7_15B4();
                } else {
                    PlaceEggR(newx, newy, 1);
                    DecEatR();
                }
                SetMyHealth(MeHealth - 5);
            }
        }
    }

    if (MeHealth <= 0) {
        if (++fd_50F6_1006 >= 100) {
            if (MePlane >= 2 && mapval >= 0x4e)
                YellowDeath(7);
            else
                YellowDeath(8);
        }
    }
}

extern int _fastcall win_IsWinInFront(int v);
extern long far MacTickCount(void);
extern void far myDelay(long);
extern void far f_00DF_015C(void);
extern int far SRand2(void);
extern int far mySongIsDone(void);
extern void far SetMap(int plane, int x, int y, int value);
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

    SetMyLife(MePlane, MeLocX, MeLocY, fd_50F6_04C2, fd_50F6_0496, 0xff);
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
        tile = MapA[x][y];
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
            myBeginSound(0x25, 0x32c8, 0x7e);
        if (kind == 10) {
            myBeginSound(0x31, 0x55f0, 0x7f);
            MapA[x][y] = SRand2() ? tile - 3 : tile;
        }
        if (kind != 0 && kind < 10 && fd_3D57_07A8[1] != 0 && mySongIsDone())
            break;
        if (kind == 2) {
            SetMap(plane, x, y, n + 0x38);
            if (n < 5)
                n++;
            else if (n > 3)
                n--;
        }
        MoveMyLife(plane, x, y, type, SRand8());
        DoEditUpdateDraw();
    }
    if (kind == 10)
        MapA[x][y] = tile;
    ClearMyLife(plane, x, y, type, fd_50F6_0496);
    MePlane = svPlane;
    MeLocX = svX;
    MeLocY = svY;
    fd_50F6_04C2 = svType;
    fd_50F6_0496 = svDir;
}

extern int far WinPrintf(char far *format, ...);
extern long far GetDis(int x1, int y1, int x2, int y2);
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
    SetMyLife(MePlane, MeLocX, MeLocY, fd_50F6_04C2, fd_50F6_0496, 0xff);
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
        if ((int)GetDis(x, y, svX, svY) == 0 && count - i - 1 != 0)
            d = o25_39C7_0CBD(plane, x, y, RRand(7) + x - 3, RRand(7) + y - 3);
        else
            d = o25_39C7_0CBD(plane, x, y, svX, svY);
        if (d >= 0) {
            x += Dx8[d];
            y += Dy8[d];
        } else
            d = SRand8();
        MoveMyLife(plane, x, y, type, d);
        WinPrintf("2");
        DoEditUpdateDraw();
    }
    ClearMyLife(plane, x, y, type, fd_50F6_0496);
    MePlane = svPlane;
    MeLocX = svX;
    MeLocY = svY;
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
extern int far GetWinner(int a, int b);
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
    type = GetWinner(fd_50F6_04C2, pl[index]);
    if (fd_50F6_04C2 != type)
        GotoMyAnt();
    o25_3BA4_0999(MePlane, MeLocX, MeLocY, fd_50F6_0496, 0x70, 0);
    if (fd_50F6_04C2 == type) {
        SetMyLife(MePlane, MeLocX, MeLocY, fd_50F6_04C2, fd_50F6_0496, 0xff);
        if (list <= 1)
            DeadAntHere(px[index], py[index], pl[index] & 0x80);
        pl[index] = 0;
        if (fd_50F6_0A8E == 3 && MePlane == fd_50F6_08DA && fd_50F6_07C0 == index)
            ResetYellowVars(MePlane, MeLocX, MeLocY);
    } else {
        SetLife(list, px[index], py[index], pl[index]);
        if (list <= 1)
            DeadAntHere(MeLocX, MeLocY, fd_50F6_04E2);
        YellowDeath(0);
    }
}

extern void far TryAntTheme(void);
extern void far SetAlarmDropState(int state, int quiet);
extern void far DigMyTile(int plane, int x, int y);
extern unsigned char far HoleMapB[];
extern void far MakeNewHoleB(int x);
extern unsigned char far HoleMapR[];
extern void far MakeNewHoleR(int x);
extern signed char far fd_3D57_006C[];
extern int far IsNotObstacle(int plane, int x, int y);


extern int far fd_3D57_02A4[2];
extern int far fd_3D57_02B0[2];
extern int far fd_3D57_02A8[2];
extern int far fd_3D57_02AC[2];
extern int far TileCanBeMovedOn(int plane, int x, int y, int fromPlane, int fromX, int fromY, int digging);
extern int far GetLife(int plane, int x, int y);
extern int far IsClearTile(int plane, int x, int y);
extern int far fd_50F6_0EFA;
void far o25_3BA4_1035(void)
{
    TryAntTheme();
    if (fd_50F6_104E != 0)
        SetAlarmDropState(0, 1);
    ClearMyLife(MePlane, MeLocX, MeLocY, fd_50F6_04C2, fd_50F6_0496);
    if (MeLocX > 0x40)
        MePlane = 3;
    else
        MePlane = 2;
    MeLocX = MeLocY;
    if (fd_50F6_04C2 == 0x60)
        MeLocY = 2;
    else
        MeLocY = 1;
    fd_50F6_0496 = 4;
    if (MePlane == 2)
        DigMyTile(MePlane, MeLocX, MeLocY);
    else
        DigMyTile(MePlane, MeLocX, MeLocY);
    SetMyLife(MePlane, MeLocX, MeLocY, fd_50F6_04C2, fd_50F6_0496, 0xff);
}


void far ExitNest(void)
{
    int step;
    int nx;
    int ny;
    int dir;
    int i;
    int d;

    TryAntTheme();
    SetMyLife(MePlane, MeLocX, MeLocY, fd_50F6_04C2, fd_50F6_0496, 0);
    MeLocY = MeLocX & 0x3f;
    if (MePlane == 2) {
        if (HoleMapB[MeLocY] == 0)
            MakeNewHoleB(MeLocX);
        MeLocX = HoleMapB[MeLocY];
    } else {
        if (HoleMapR[MeLocY] == 0)
            MakeNewHoleR(MeLocX);
        MeLocX = HoleMapR[MeLocY];
    }
    step = (fd_50F6_04C2 == 0x60) ? 2 : 1;
    if (fd_50F6_0AF8 == 1) {
        d = GetDir(MeLocX, MeLocY, fd_50F6_0AD6, fd_50F6_0AE8);
        if (d > 0)
            d--;
    } else if (MePlane == fd_50F6_0AF8) {
        if (MeLocX < 0x40)
            d = 2;
        else
            d = 6;
    } else {
        d = o25_3BA4_1A9F(1, MeLocX, MeLocY, fd_50F6_0AF8, fd_50F6_0AD6, fd_50F6_0AE8);
        if (d < 0)
            d = SRand8();
    }
    i = 0;
    dir = d;
    for (; i < 8; i++) {
        d = (fd_3D57_006C[i] + dir) & 7;
        nx = Dx8[d] * step + MeLocX;
        ny = Dy8[d] * step + MeLocY;
        if (IsNotObstacle(1, nx, ny)) {
            MeLocX = nx;
            MeLocY = ny;
            fd_50F6_0496 = d;
            break;
        }
    }
    if (i == 8) {
        fd_50F6_0496 = dir;
        MeLocX = (MeLocX + step) & 0x7f;
    }
    SetMyLife(MePlane = 1, MeLocX, MeLocY, fd_50F6_04C2, fd_50F6_0496, 0xff);
}

extern int far fd_3D57_02A4[2];
extern int far fd_3D57_02B0[2];
extern int far fd_3D57_02A8[2];
extern int far fd_3D57_02AC[2];

int far o25_3BA4_13AB(int p1, int x1, int y1, int p2, int x2, int y2)
{
    if (p2 == p1)
        return GetDis(x1, y1, x2, y2);
    if (p1 == 1 && p2 > p1) {
        if (p2 == 2)
            return GetDis(x1, y1, fd_3D57_02AC[0], fd_3D57_02AC[1])
                 + GetDis(fd_3D57_02A4[0], fd_3D57_02A4[1], x2, y2);
        return GetDis(x1, y1, fd_3D57_02B0[0], fd_3D57_02B0[1])
             + GetDis(fd_3D57_02A4[0], fd_3D57_02A4[1], x2, y2);
    }
    if (p2 == 1) {
        if (p1 == 2)
            return GetDis(x1, y1, fd_3D57_02A4[0], fd_3D57_02A4[1])
                 + GetDis(fd_3D57_02AC[0], fd_3D57_02AC[1], x2, y2);
        return GetDis(x1, y1, fd_3D57_02A8[0], fd_3D57_02A8[1])
             + GetDis(fd_3D57_02B0[0], fd_3D57_02B0[1], x2, y2);
    }
    if (p1 == 2)
        return GetDis(x1, y1, fd_3D57_02A4[0], fd_3D57_02A4[1])
             + GetDis(fd_3D57_02AC[0], fd_3D57_02AC[1], fd_3D57_02B0[0], fd_3D57_02B0[1])
             + GetDis(fd_3D57_02A8[0], fd_3D57_02A8[1], x2, y2);
    return GetDis(x1, y1, fd_3D57_02A8[0], fd_3D57_02A8[1])
         + GetDis(fd_3D57_02B0[0], fd_3D57_02B0[1], fd_3D57_02AC[0], fd_3D57_02AC[1])
         + GetDis(fd_3D57_02A4[0], fd_3D57_02A4[1], x2, y2);
}

extern int far TileCanBeMovedOn(int plane, int x, int y, int fromPlane, int fromX, int fromY, int digging);
extern int far GetLife(int plane, int x, int y);
extern int far IsClearTile(int plane, int x, int y);

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
    threshold = GetDis(x, y, a, b);
    if (threshold > 0) {
        fallback = -2;
        flag = (fd_50F6_0A8E == 2) ? 1 : 0;
        for (dir = 0; dir < 8; dir++) {
            nx = Dx8[dir] + x;
            ny = Dy8[dir] + y;
            if (TileCanBeMovedOn(plane, nx, ny, fd_50F6_0AF8, fd_50F6_0AD6, fd_50F6_0AE8, flag) != 0) {
                dis = GetDis(nx, ny, a, b);
                if (dis < threshold) {
                    if (GetLife(plane, nx, ny) > 0 || IsClearTile(plane, nx, ny) == 0)
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
    int threshold;
    char ok[8];
    int i;
    int right;
    int nx;
    int ny;
    int dis;

    best = -1;
    threshold = GetDis(x, y, a, b);
    if (threshold > 0) {
        best = -2;
        flag = (fd_50F6_0A8E == 2) ? 1 : 0;
        for (i = 0; i < 8; i++) {
            nx = Dx8[i] + x;
            ny = Dy8[i] + y;
            if ((nx != fd_50F6_0AB6 || ny != fd_50F6_0AC6)
                && TileCanBeMovedOn(plane, nx, ny, fd_50F6_0AF8, fd_50F6_0AD6, fd_50F6_0AE8, flag)) {
                best = i;
                ok[i] = 1;
            } else
                ok[i] = 0;
        }
        if (best < 0)
            return best;
        best = -1;
        right = left = *dir;
        if (*rot == 0) {
            for (i = 0; i < 8; i++) {
                if (ok[right]) {
                    best = right;
                    *dir = GetDir(x, y, a, b) - 1;
                    *rot = 1;
                    break;
                }
                if (ok[left]) {
                    best = left;
                    *dir = GetDir(x, y, a, b) - 1;
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
    }
    return best;
found:
    dis = GetDis(Dx8[right] + x, Dy8[right] + y, a, b);
    if (dis <= threshold) {
        *dir = GetDir(x, y, a, b) - 1;
        *rot = 0;
    }
    return right;
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
        nx = Dx8[dir] + x;
        ny = Dy8[dir] + y;
        while (dir >= 0 && count < 0x40) {
            dir = o25_3BA4_1581(plane, nx, ny, a, b);
            if (dir >= 0) {
                nx += Dx8[dir];
                ny += Dy8[dir];
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
    fd_50F6_0EF8 = GetDir(x, y, a, b) - 1;
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
