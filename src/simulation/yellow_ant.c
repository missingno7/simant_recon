/*
 * Advances the player yellow ant and chooses its movement directions. It handles nest exit,
 * fighting and fight animation.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS: overlay section 25 (S25); segment 3BA4; partial original translation unit.
 * Windows: SIMANT1, from recorded function pairs in the Windows symbol inventory.
 * Steered functions: DoAntSimY, AnimYellowFight, AnimYellowInsane, YellowFight, GetMyBestDirs,
 * CheckMyBestDirs, GetMyNextRandDirs, GetMyInitialRandDir, GetMyBestDir, ExitNest, GetMyDis,
 * DoAntMoveY.
 *
 * Built /AL /Os /Oe /Og /Zi.  The order of the extern declarations is part of the
 * fingerprint: MSC 6.00A breaks some operand-order ties by symbol-table state
 * (ExitNest's MePlane/MeGoalPlane compare, GetMyDis' GetDis call order), and this
 * order (0D6C/0EF8 first, MeLastX/Y before MeGoalY, entrance arrays A4,B0,A8,AC)
 * reproduces them.
 *
 * Line layout (inferred, not recovered): /Zi starts a new object record every 52 line
 * entries, and the original relocation order fixes where those breaks fall.  The layout
 * here is one that satisfies all 90 order constraints of the file; it is not unique.
 * Compared with the shortest spelling it has seven more line entries: the two goal
 * stores of DoAntMoveY are written as separate statements, three of its tests and the
 * target test of YellowFight are nested ifs instead of && chains, and GetMyDis tests
 * p1 and p2 in two ifs.  Every form compiles to the same instructions.  A nested if
 * also takes one declaration number (see docs/codegen-rules.md), so each one before a
 * later function is offset by a prototype without parameter names directly after it
 * (PlaceEggB, MakeNewHoleB, MakeNewHoleR); the original names and line structure are
 * unknown.
 */

extern int far MeCrazyCnt;
extern int far MeCrazyDir;

extern int far MeMoveMe;
extern int far MeCmd;
extern int far MeTargIndex;
extern int far MeTargLifePlane;
extern int far GetAntIndex(int list, int index, int far *x, int far *y,
                           int far *attr, int far *state, int far *dir);
extern int far MeTargLife;
extern int far MePlane;
extern int far MeLocX;
extern int far ABS(int value);
extern int far MeGoalX;
extern int far MeLocY;
extern int far GetDir(int x1, int y1, int x2, int y2);
extern int far MeDir;
extern void far DoEditUpdateDraw(void);
extern int far MeTargLifeX;
extern int far MeTargLifeY;
extern int far MeLastX;
extern int far MeLastY;
extern int far MeGoalY;
extern int far MeGoalPlane;
extern signed char far Dx9[];
extern signed char far Dy9[];
extern int far TryMyDropOrLift(int plane, int x, int y);
int far GetMyDir(int plane, int x, int y, int gplane, int gx, int gy);
extern signed char far Dy8[];
extern int far MeType;
extern signed char far Dx8[];
extern void far MoveMyLife(int plane, int x, int y, int type, int dir);
extern int far MeSteps;
extern int far MeScent;
extern int far MeColor;
extern void far JamScentBT(int, int, int);
extern void far JamScentRT(int, int, int);
extern int far MeDropAlarm;
extern void far AlarmHere(int, int, int);
extern void far FixExitMapB(int x, int y);
extern void far FixExitMapR(int x, int y);
extern int far MeNestStarted;
extern int far HealthB;
extern int far AlwaysHealthy;
extern int far MeHealth;
extern void far SetMyHealth(int health);
extern int far IsItHole(int, int);
extern void far DoEditAndMapUpdateDraw(void);
void far EnterNest(void);
extern int far MapPlane;
extern int far OptionStates[];
extern void far GotoMyAnt(void);
void far ExitNest(void);
extern int far GetMap(int plane, int x, int y);
extern void far ClearMyLife(int plane, int x, int y, int type, int dir);
extern void far SetMyLife(int plane, int x, int y, int type, int dir, int code);
extern void far myBeginSound(int sound, int a, int b);
extern void far * far * far WindPromptStrs;
extern void far EditMessage(void far *, long, int);
extern int far MeStartedFight;
void far YellowFight(int list, int index);
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

    if (MeMoveMe == 0)
        return;
    result = 0;
    if (MeCmd >= 3) {
        if (GetAntIndex(MeTargLifePlane, MeTargIndex, &tx, &ty, &tattr, &tstate, &tdir) == 0
            || (((unsigned)tattr >= 0) && ((MeTargLife ^ tattr) & 0xf0) != 0)) {
            result = -2;
            goto done;
        }
        if (MePlane == MeTargLifePlane) {
            dx = ABS(MeLocX - tx);
            dy = ABS(MeLocY - ty);
            if (dx <= 1)
            if (dy <= 1) {
                d = GetDir(MeLocX, MeLocY, tx, ty) - 1;
                if (d >= 0)
                    MeDir = d;
                DoEditUpdateDraw();
                goto moved;
            }
        }
        MeTargLifeX = tx;
        MeGoalX = MeTargLifeX;
        MeTargLifeY = ty;
        MeGoalY = MeTargLifeY;
    }
    if (MeCmd == 1)
    if (MeGoalPlane == MePlane) {
        dir = GetDir(MeLocX, MeLocY, MeGoalX, MeGoalY);
        x = Dx9[dir] + MeLocX;
        y = Dy9[dir] + MeLocY;
        if (x < 0 || x > 0x7f)
            x = MeLocX;
        if (y < 0 || y > 0x3f)
            y = MeLocY;
        if (MeGoalX == x)
        if (MeGoalY == y) {
            if ((result = TryMyDropOrLift(MePlane, x, y)) != 0) {
                result = (result == 1) ? -1 : -2;
                goto done;
            }
        }
    }
    d = GetMyDir(MePlane, MeLocX, MeLocY,
                      MeGoalPlane, MeGoalX, MeGoalY);
    if (d < 0) {
        result = d;
        goto done;
    }
    x = Dx8[d] + MeLocX;
    y = Dy8[d] + MeLocY;
    MeLastX = MeLocX;
    MeLastY = MeLocY;
    MoveMyLife(MePlane, x, y, MeType, d);
    MeSteps++;
    if (MePlane == 1) {
        if (MeScent > 0 && (MeType == 0x18 || MeType == 0x38)) {
            if (MeColor == 0)
                JamScentBT(MeLocX, MeLocY, MeScent);
            else
                JamScentRT(MeLocX, MeLocY, MeScent);
            if (MeScent > 10)
                MeScent--;
        }
        if (MeDropAlarm != 0)
            AlarmHere(MeLocX, MeLocY, 50);
    } else if (MePlane == 2)
        FixExitMapB(MeLocX, MeLocY);
    else
        FixExitMapR(MeLocX, MeLocY);
    if (MeSteps & 1) {
        if (MeType == 0x40 && MeNestStarted == 0 && HealthB > 0 && AlwaysHealthy == 0)
            HealthB--;
        SetMyHealth(MeHealth - 1);
    }
    if (MePlane == 1) {
        if (IsItHole(MeLocX, MeLocY) == 0)
            goto done;
        if (MeGoalPlane > 1 || (MeGoalPlane == MePlane && MeGoalX == MeLocX
                                 && MeGoalY == MeLocY)) {
            DoEditAndMapUpdateDraw();
            d = MePlane;
            EnterNest();
            if (MeGoalPlane != d || MeGoalX != x || MeGoalY != y
                || MePlane == MapPlane)
                goto done;
            if (OptionStates[0] == 0)
                GotoMyAnt();
            goto moved;
        }
        goto done;
    }
    if (MeLocY == 0) {
        DoEditAndMapUpdateDraw();
        d = MePlane;
        ExitNest();
        if (MeGoalPlane != d || MeGoalX != x || MeGoalY != y
            || MePlane == MapPlane)
            goto done;
        if (OptionStates[0] == 0)
            GotoMyAnt();
        goto moved;
    }
    if (GetMap(MePlane, MeGoalX, MeGoalY) != 0x14)
        goto done;
    if (MeType == 0x60 || MeGoalX != MeLocX || MeGoalY != MeLocY)
        goto done;
    ClearMyLife(MePlane, MeLocX, MeLocY, MeType, MeDir);
    if (MePlane == 2)
        MePlane = 3;
    else
        MePlane = 2;
    SetMyLife(MePlane, MeLocX, MeLocY, MeType, MeDir, 0xff);
    myBeginSound(1, 0, 0x7e);
    GotoMyAnt();
    if (MePlane == 3)
        EditMessage(WindPromptStrs[4], 360L, 0);
moved:
    result = -1;
done:
    if (OptionStates[0] != 0)
        GotoMyAnt();
    if (result == 0 && MeGoalPlane == MePlane && MeGoalX == MeLocX
        && MeGoalY == MeLocY && MeCmd == 0)
        result = -1;
    if (result == 0)
        return;
    if (result == -2) {
        myBeginSound(1, 0, 0x7e);
        GotoMyAnt();
    } else if (MeCmd == 3) {
        MeStartedFight = 1;
        YellowFight(MeTargLifePlane, MeTargIndex);
        MeStartedFight = 0;
    } else if (MeCmd == 4) {
        d = GetDir(tx, ty, MeLocX, MeLocY) - 1;
        if (d >= 0 && (tattr & 0x70) != 0x60) {
            tattr = (tattr & 0xf8) | d;
            SetAntIndex(MePlane, MeTargIndex, tx, ty, tattr, tstate, tdir);
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

extern int far MeMode;
extern unsigned char far Cycle;
extern int far InNestBounds(int x, int y);
extern int far SRand128(void);
extern void far PlaceEggB(int, int, int);
extern void far DecEatB(void);
extern void far PlaceEggR(int x, int y, int type);
extern void far DecEatR(void);
extern int far MeHealthCntDwn;

void far DoAntSimY(void)
{
    int newy, newx;
    int mapval;
    int bx;

    if (MeMode != 0)
        return;

    SetMyLife(MePlane, MeLocX, MeLocY, MeType, MeDir, 0xff);

    if (!(Cycle & 0x3f))
        SetMyHealth(MeHealth - 1);

    if (MePlane >= 2) {
        mapval = GetMap(MePlane, MeLocX, MeLocY);
        if (mapval >= 0x4e)
            SetMyHealth(MeHealth - 1);
    }

    if (MeType == 0x60 && MePlane > 1 && !(Cycle & 0xf)) {
        bx = MeDir ^ 4;
        newx = MeLocX + 2 * Dx8[bx];
        newy = MeLocY + 2 * Dy8[bx];
        if (InNestBounds(newx, newy)) {
            if (SRand128() <= MeHealth) {
                if (MeColor == 0) {
                    PlaceEggB(newx, newy, 1);
                    DecEatB();
                } else {
                    PlaceEggR(newx, newy, 1);
                    DecEatR();
                }
                SetMyHealth(MeHealth - 5);
            }
        }
    }

    if (MeHealth <= 0) {
        if (++MeHealthCntDwn >= 100) {
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

void far AnimYellowFight(int plane, int x, int y, int dir, int type, int kind)
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

    SetMyLife(MePlane, MeLocX, MeLocY, MeType, MeDir, 0xff);
    DoEditUpdateDraw();
    svPlane = plane;
    svX = x;
    svY = y;
    svType = MeType;
    svDir = dir;
    if (kind == 0)
        count = 6;
    else if (win_IsWinInFront(0))
        count = OptionStates[1] ? 0x40 : 0x20;
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
        if (kind != 0 && kind < 10 && OptionStates[1] != 0 && mySongIsDone())
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
    ClearMyLife(plane, x, y, type, MeDir);
    MePlane = svPlane;
    MeLocX = svX;
    MeLocY = svY;
    MeType = svType;
    MeDir = svDir;
}

extern int far WinPrintf(char far *format, ...);
extern long far GetDis(int x1, int y1, int x2, int y2);
extern int far RRand(int range);
extern int far GetBestDir(int plane, int x, int y, int gx, int gy);

void far AnimYellowInsane(int plane, int x, int y, int dir, int type)
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
    SetMyLife(MePlane, MeLocX, MeLocY, MeType, MeDir, 0xff);
    DoEditUpdateDraw();
    svPlane = plane;
    svX = x;
    svY = y;
    svType = MeType;
    svDir = dir;
    count = win_IsWinInFront(0) ? 0x20 : 8;
    t = MacTickCount();
    for (i = 0; i < count; i++) {
        while (MacTickCount() <= t)
            myDelay(1L);
        t = MacTickCount() + 3;
        f_00DF_015C();
        if ((int)GetDis(x, y, svX, svY) == 0 && count - i - 1 != 0)
            d = GetBestDir(plane, x, y, RRand(7) + x - 3, RRand(7) + y - 3);
        else
            d = GetBestDir(plane, x, y, svX, svY);
        if (d >= 0) {
            x += Dx8[d];
            y += Dy8[d];
        } else
            d = SRand8();
        MoveMyLife(plane, x, y, type, d);
        WinPrintf("2");
        DoEditUpdateDraw();
    }
    ClearMyLife(plane, x, y, type, MeDir);
    MePlane = svPlane;
    MeLocX = svX;
    MeLocY = svY;
    MeType = svType;
    MeDir = svDir;
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

void far YellowFight(int list, int index)
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
    type = GetWinner(MeType, pl[index]);
    if (MeType != type)
        GotoMyAnt();
    AnimYellowFight(MePlane, MeLocX, MeLocY, MeDir, 0x70, 0);
    if (MeType == type) {
        SetMyLife(MePlane, MeLocX, MeLocY, MeType, MeDir, 0xff);
        if (list <= 1)
            DeadAntHere(px[index], py[index], pl[index] & 0x80);
        pl[index] = 0;
        if (MeCmd == 3)
        if (MePlane == MeTargLifePlane)
        if (MeTargIndex == index)
            ResetYellowVars(MePlane, MeLocX, MeLocY);
    } else {
        SetLife(list, px[index], py[index], pl[index]);
        if (list <= 1)
            DeadAntHere(MeLocX, MeLocY, MeColor);
        YellowDeath(0);
    }
}

extern void far TryAntTheme(void);
extern void far SetAlarmDropState(int state, int quiet);
extern void far DigMyTile(int plane, int x, int y);
extern unsigned char far HoleMapB[];
extern void far MakeNewHoleB(int);
extern unsigned char far HoleMapR[];
extern void far MakeNewHoleR(int);
extern signed char far absSearchDirs[];
extern int far IsNotObstacle(int plane, int x, int y);


extern int far LastNewExitB[2];
extern int far LastNewHoleR[2];
extern int far LastNewExitR[2];
extern int far LastNewHoleB[2];
extern int far TileCanBeMovedOn(int plane, int x, int y, int fromPlane, int fromX, int fromY, int digging);
extern int far GetLife(int plane, int x, int y);
extern int far IsClearTile(int plane, int x, int y);
extern int far MeCrazyRot;
void far EnterNest(void)
{
    TryAntTheme();
    if (MeDropAlarm != 0)
        SetAlarmDropState(0, 1);
    ClearMyLife(MePlane, MeLocX, MeLocY, MeType, MeDir);
    if (MeLocX > 0x40)
        MePlane = 3;
    else
        MePlane = 2;
    MeLocX = MeLocY;
    if (MeType == 0x60)
        MeLocY = 2;
    else
        MeLocY = 1;
    MeDir = 4;
    if (MePlane == 2) {
        DigMyTile(MePlane, MeLocX, MeLocY);
        SetMyLife(MePlane, MeLocX, MeLocY, MeType, MeDir, 0xff);
    } else {
        DigMyTile(MePlane, MeLocX, MeLocY);
        SetMyLife(MePlane, MeLocX, MeLocY, MeType, MeDir, 0xff);
    }
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
    SetMyLife(MePlane, MeLocX, MeLocY, MeType, MeDir, 0);
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
    step = (MeType == 0x60) ? 2 : 1;
    if (MeGoalPlane == 1) {
        d = GetDir(MeLocX, MeLocY, MeGoalX, MeGoalY);
        if (d > 0)
            d--;
    } else if (MePlane == MeGoalPlane) {
        if (MeLocX < 0x40)
            d = 2;
        else
            d = 6;
    } else {
        d = GetMyDir(1, MeLocX, MeLocY, MeGoalPlane, MeGoalX, MeGoalY);
        if (d < 0)
            d = SRand8();
    }
    i = 0;
    dir = d;
    for (; i < 8; i++) {
        d = (absSearchDirs[i] + dir) & 7;
        nx = Dx8[d] * step + MeLocX;
        ny = Dy8[d] * step + MeLocY;
        if (IsNotObstacle(1, nx, ny)) {
            MeLocX = nx;
            MeLocY = ny;
            MeDir = d;
            break;
        }
    }
    if (i == 8) {
        MeDir = dir;
        MeLocX = (MeLocX + step) & 0x7f;
    }
    SetMyLife(MePlane = 1, MeLocX, MeLocY, MeType, MeDir, 0xff);
}

extern int far LastNewExitB[2];
extern int far LastNewHoleR[2];
extern int far LastNewExitR[2];
extern int far LastNewHoleB[2];

int far GetMyDis(int p1, int x1, int y1, int p2, int x2, int y2)
{
    if (p2 == p1)
        return GetDis(x1, y1, x2, y2);
    if (p1 == 1)
    if (p2 > p1) {
        if (p2 == 2)
            return GetDis(x1, y1, LastNewHoleB[0], LastNewHoleB[1])
                 + GetDis(LastNewExitB[0], LastNewExitB[1], x2, y2);
        return GetDis(x1, y1, LastNewHoleR[0], LastNewHoleR[1])
             + GetDis(LastNewExitB[0], LastNewExitB[1], x2, y2);
    }
    if (p2 == 1) {
        if (p1 == 2)
            return GetDis(x1, y1, LastNewExitB[0], LastNewExitB[1])
                 + GetDis(LastNewHoleB[0], LastNewHoleB[1], x2, y2);
        return GetDis(x1, y1, LastNewExitR[0], LastNewExitR[1])
             + GetDis(LastNewHoleR[0], LastNewHoleR[1], x2, y2);
    }
    if (p1 == 2)
        return GetDis(x1, y1, LastNewExitB[0], LastNewExitB[1])
             + GetDis(LastNewHoleB[0], LastNewHoleB[1], LastNewHoleR[0], LastNewHoleR[1])
             + GetDis(LastNewExitR[0], LastNewExitR[1], x2, y2);
    return GetDis(x1, y1, LastNewExitR[0], LastNewExitR[1])
         + GetDis(LastNewHoleR[0], LastNewHoleR[1], LastNewHoleB[0], LastNewHoleB[1])
         + GetDis(LastNewExitB[0], LastNewExitB[1], x2, y2);
}

extern int far TileCanBeMovedOn(int plane, int x, int y, int fromPlane, int fromX, int fromY, int digging);
extern int far GetLife(int plane, int x, int y);
extern int far IsClearTile(int plane, int x, int y);

int far GetMyBestDirs(int plane, int x, int y, int a, int b)
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
        flag = (MeCmd == 2) ? 1 : 0;
        for (dir = 0; dir < 8; dir++) {
            nx = Dx8[dir] + x;
            ny = Dy8[dir] + y;
            if (TileCanBeMovedOn(plane, nx, ny, MeGoalPlane, MeGoalX, MeGoalY, flag) != 0) {
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


/* Picks a step direction around (x, y) when the direct way to (a, b) is blocked.
 * ok[] marks the eight neighbours the ant may step on, excluding the tile it just
 * left. With *rot == 0 it searches outwards from *dir on both sides and records
 * the side taken in *rot (1 or -1); otherwise it keeps turning to that side, and
 * once the step is no farther from the goal than (x, y) it resets *dir and *rot.
 * Returns the direction, -1 if already at the goal or nothing found, -2 if no
 * neighbour is usable.
 * `right` is also the index of the neighbour scan and `result` its last usable
 * neighbour: the frame has no separate words for them (the Macintosh build keeps
 * the same pairs in one register each). */
int far GetMyRandDirs(int far *rot, int far *dir, int plane, int x, int y, int a, int b)
{
    int flag;
    int right;
    int left;
    int result;
    int threshold;
    char ok[8];
    int i;
    int nx;
    int ny;

    result = -1;
    threshold = GetDis(x, y, a, b);
    if (threshold > 0) {
        result = -2;
        flag = (MeCmd == 2) ? 1 : 0;
        for (right = 0; right < 8; right++) {
            nx = Dx8[right] + x;
            ny = Dy8[right] + y;
            if ((nx != MeLastX || ny != MeLastY)
                && TileCanBeMovedOn(plane, nx, ny, MeGoalPlane, MeGoalX, MeGoalY, flag)) {
                result = right;
                ok[right] = 1;
            } else
                ok[right] = 0;
        }
        if (result >= 0) {
            result = -1;
            left = right = *dir;
            if (*rot == 0) {
                for (i = 0; i < 8; i++) {
                    if (ok[right]) {
                        result = right;
                        *dir = GetDir(x, y, a, b) - 1;
                        *rot = 1;
                        break;
                    }
                    if (ok[left]) {
                        result = left;
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
                            result = right;
                            if ((int)GetDis(Dx8[right] + x, Dy8[right] + y, a, b) <= threshold) {
                                *dir = GetDir(x, y, a, b) - 1;
                                *rot = 0;
                            }
                            break;
                        }
                    } else if (ok[left]) {
                        result = left;
                        if ((int)GetDis(Dx8[left] + x, Dy8[left] + y, a, b) <= threshold) {
                            *dir = GetDir(x, y, a, b) - 1;
                            *rot = 0;
                        }
                        break;
                    }
                    right = (right + 1) & 7;
                    left = (left - 1) & 7;
                }
            }
        }
    }
    return result;
}


int far CheckMyBestDirs(int far *steps, int plane, int x, int y, int a, int b)
{
    int nx;
    int ny;
    int count;
    int dir;

    count = 0;
    dir = GetMyBestDirs(plane, x, y, a, b);
    if (dir >= 0) {
        nx = Dx8[dir] + x;
        ny = Dy8[dir] + y;
        while (dir >= 0 && count < 0x40) {
            dir = GetMyBestDirs(plane, nx, ny, a, b);
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

extern int far MeCrazyRot;

int far GetMyNextRandDirs(int plane, int x, int y, int a, int b)
{
    int dir;
    int steps;

    if (CheckMyBestDirs(&steps, plane, x, y, a, b) == -2)
        dir = GetMyRandDirs(&MeCrazyRot, &MeCrazyDir, plane, x, y, a, b);
    else {
        MeCrazyCnt = -1;
        dir = GetMyBestDirs(plane, x, y, a, b);
    }
    return dir;
}

int far GetMyInitialRandDir(int far *rot, int far *dir, int plane, int x, int y, int a, int b)
{
    MeCrazyDir = GetDir(x, y, a, b) - 1;
    MeCrazyCnt = 0x10;
    MeCrazyRot = 0;
    GetMyRandDirs(&MeCrazyRot, &MeCrazyDir, plane, x, y, a, b);
}

int far GetMyBestDir(int plane, int x, int y, int a, int b)
{
    int dir;

    if (MeCrazyCnt < 0) {
        dir = GetMyBestDirs(plane, x, y, a, b);
        if (dir == -2 && MeCrazyCnt == -2)
            dir = GetMyInitialRandDir(&MeCrazyRot, &MeCrazyDir, plane, x, y, a, b);
    } else {
        dir = GetMyNextRandDirs(plane, x, y, a, b);
        MeCrazyCnt--;
    }
    return dir;
}

/* The result goes through a local that MSC eliminates (value only returned); as a
 * register candidate it still takes SI first, so p1 lands in DI as in the original. */
int far GetMyDir(int p1, int x1, int y1, int p2, int x2, int y2)
{
    int r;

    if (p1 <= 1) {
        if (p2 <= 1)
            r = GetMyBestDir(p1, x1, y1, x2, y2);
        else if (p2 == 2)
            r = GetMyBestDir(p1, x1, y1, LastNewHoleB[0], LastNewHoleB[1]);
        else
            r = GetMyBestDir(p1, x1, y1, LastNewHoleR[0], LastNewHoleR[1]);
    } else if (p2 == p1)
        r = GetMyBestDir(p1, x1, y1, x2, y2);
    else if (p1 == 2)
        r = GetMyBestDir(p1, x1, y1, LastNewExitB[0], LastNewExitB[1]);
    else
        r = GetMyBestDir(p1, x1, y1, LastNewExitR[0], LastNewExitR[1]);
    return r;
}
