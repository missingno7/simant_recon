/*
 * Changes map and yard modes and moves the view to ants, queens or the spider. It also applies
 * ant count, food and patch transfer commands.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS: resident code; segment 015B; complete original translation unit.
 * Windows: SIMANT, from recorded function pairs in the Windows symbol inventory. Some pairs are
 * HIGH confidence, not confirmed.
 */

extern int far ListIndexA;
extern int far fd_3D57_0798;
extern void far AddBlackAnts(int count);
extern void far AddRedAnts(int count);
extern void far FullCount(void);

void far AddSomeAnts(int kind)
{
    int count;

    count = ListIndexA;
    if (count < 1000) {
        if (fd_3D57_0798 == 1) {
            if (kind == 1)
                AddBlackAnts(1000 - count);
            else
                AddRedAnts(1000 - count);
        } else if (kind == 1) {
            AddBlackAnts(0x20);
        } else {
            AddRedAnts(0x20);
        }
    }
    FullCount();
}

extern void far CompactListA(void);
extern unsigned char far AlistT[];
extern void far DeadAntHere(int x, int y, int type);
extern unsigned char far AlistY[];
extern unsigned char far AlistX[];
extern int far IsItYellow(int level, int x, int y);

void far KillSomeAnts(int mode)
{
    int i;
    int n;
    int type;

    CompactListA();
    FullCount();
    n = 0;
    for (i = ListIndexA - 1; i >= 0; i--) {
        type = AlistT[i];
        if (mode == 1) {
            if (!(type & 0x80)) {
                DeadAntHere(AlistX[i], AlistY[i], 0);
                AlistT[i] = 0;
                if (++n > 50)
                    break;
            }
        } else {
            if (type & 0x80) {
                if (!IsItYellow(1, AlistX[i], AlistY[i])) {
                    DeadAntHere(AlistX[i], AlistY[i], 1);
                    AlistT[i] = 0;
                    if (++n > 50)
                        break;
                }
            }
        }
    }
    CompactListA();
    FullCount();
}

extern unsigned char far MapA[128][64];
extern int far IsItFood(int tile);
extern int far SRand16(void);
extern int far FoodA;

void far SubtractFood(void)
{
    int row, column;

    for (row = 0; row < 0x80; row++)
        for (column = 0; column < 0x40; column++)
            if (IsItFood(MapA[row][column]) == 1)
                MapA[row][column] = SRand16();
    FoodA = 0;
}

extern int far CurEditMode;

void far SetEditMode(int value)
{
    CurEditMode = value;
}

static int g_1960[5] = { 0x109, 0x10a, 0x10c, 0x10d, 0x10b };

extern int far MapMode;
extern int far YardMode;
void far SetYardMode(int newMode);
extern int far MapPlane;
void far SetMapPlane(int plane);
extern void far SetMapTitle(void);
extern void _fastcall win_MakeObjSelected(int obj);
extern void _fastcall win_MakeGroupUnselected(int win, int group);

void far SetMapModeAnt(int mode)
{
    if (MapMode == mode && mode >= 4 && mode <= 8)
        mode = 1;
    switch (mode) {
    case 0:
        MapMode = mode;
        SetYardMode(YardMode);
        break;
    case 4:
    case 5:
    case 6:
    case 7:
    case 8:
        if (MapPlane != 1)
            SetMapPlane(1);
    case 1:
    case 2:
    case 3:
        MapMode = mode;
        SetMapTitle();
        if (mode >= 4 && mode <= 8)
            win_MakeObjSelected(g_1960[mode - 4]);
        else
            win_MakeGroupUnselected(0x100, 2);
        break;
    }
}

static int g_1984[4] = { 0x1908, 0x1908, 0x1909, 0x190a };

extern int far OldMapPlane;
extern int far WinPrintf(char far *format, ...);
extern void _fastcall win_LockWin(int win);
extern void _fastcall win_MakeObjInvisible(int obj);
extern int near g_3DB2;
extern void _fastcall win_UnlockWin(int win);
extern void far win_YardClosed(void);
extern void _fastcall win_MakeObjVisible(int obj);
extern void _fastcall win_SetObjBitmap(int obj, int bitmap);
extern int _fastcall win_IsWinOpen(int win);
extern void far clip_Push(void);
extern void far clip_SetWin(int win);
extern void _fastcall win_DrawObjectNum(int objNum);
extern void far clip_Pop(void);
extern void far win_Swap(int from, int to);
extern void far DrawYard(void);

void far SetYardMode(int newMode)
{
    if (newMode == 4) {
        SetMapPlane(OldMapPlane);
    } else {
        WinPrintf("\nYardmode=%d, newMode=%d", YardMode, newMode);
        if (newMode != 0 && newMode != 1) {
            YardMode = newMode;
            win_LockWin(0x1900);
            win_MakeObjInvisible(0x1903);
            if (g_3DB2 != 0x140)
                win_MakeObjInvisible(0x190f);
            win_UnlockWin(0x1900);
            win_YardClosed();
        } else {
            YardMode = newMode;
            win_LockWin(0x1900);
            win_MakeObjVisible(0x1903);
            if (g_3DB2 != 0x140)
                win_MakeObjVisible(0x190f);
            win_UnlockWin(0x1900);
            win_YardClosed();
            win_SetObjBitmap(0x1903, newMode + 7000);
            if (win_IsWinOpen(0x1900)) {
                clip_Push();
                clip_SetWin(0x1900);
                win_DrawObjectNum(0x1903);
                if (g_3DB2 != 0x140)
                    win_DrawObjectNum(0x190f);
                clip_Pop();
            }
        }
        if (!win_IsWinOpen(0x1900) && win_IsWinOpen(0x100))
            win_Swap(0x100, 0x1900);
        clip_Push();
        clip_SetWin(0x1900);
        win_MakeObjSelected(g_1984[YardMode]);
        clip_Pop();
        DrawYard();
    }
    SetMapTitle();
}

typedef struct {
    int x;
    int y;
} Point;

extern int far EditRows;
extern int far EditColumns;
extern void far InvalEuMap(int left, int top, int right, int bottom);
extern int far hScrollMax;
extern void far CenterEdit(int x, int y);
extern void far UpdateEdit(void);
extern void far f_0250_0ED2(void);
extern Point far CurYardPnt;
extern Point far YMapPnt;
extern void far clip_Off(void);

void far SetMapPlaneLocation(int plane, int x, int y)
{
    int win, obj;

    if (plane != 0)
        InvalEuMap(0, 0, EditColumns, EditRows);
    else
        OldMapPlane = MapPlane;
    MapPlane = plane;
    if (plane == 1)
        hScrollMax = 0x80 - EditColumns;
    else
        hScrollMax = 0x40 - EditColumns;
    if (MapPlane != 0) {
        CenterEdit(x, y);
        UpdateEdit();
        f_0250_0ED2();
    } else {
        YMapPnt = CurYardPnt;
    }
    SetMapModeAnt(MapPlane);
    win = obj = 0;
    switch (MapPlane) {
    case 0:
        obj = 0x105;
        break;
    case 1:
        win = 8;
        obj = 0x106;
        break;
    case 2:
        win = 9;
        obj = 0x107;
        break;
    case 3:
        win = 10;
        obj = 0x108;
        break;
    }
    if (win) {
        clip_SetWin(0);
        win_MakeObjSelected(win);
        clip_Off();
    }
    if (obj) {
        clip_SetWin(0x100);
        win_MakeObjSelected(obj);
        win_MakeGroupUnselected(0x100, 2);
        clip_Off();
    }
}

extern int far fd_50F6_0AA6;

void far GotoMapPoint(int plane, int x, int y)
{
    if (MapPlane == plane && plane > 0) {
        CenterEdit(x, y);
        fd_50F6_0AA6 = 0;
    } else {
        SetMapPlaneLocation(plane, x, y);
    }
}

extern int far MapPlane2EditTab[];
extern Point far AMapPnt;
extern Point far BMapPnt;
extern Point far RMapPnt;

void far SetMapPlane(int plane)
{
    Point pt;

    if (plane != 0)
        InvalEuMap(0, 0, EditColumns, EditRows);
    else
        OldMapPlane = MapPlane;
    MapPlane = plane;
    if (plane == 1)
        hScrollMax = 0x80 - EditColumns;
    else
        hScrollMax = 0x40 - EditColumns;
    SetEditMode(MapPlane2EditTab[MapPlane]);
    switch (MapPlane) {
    case 0:
        pt = YMapPnt;
        break;
    case 1:
        pt = AMapPnt;
        break;
    case 2:
        pt = BMapPnt;
        break;
    case 3:
        pt = RMapPnt;
        break;
    }
    SetMapPlaneLocation(plane, pt.x, pt.y);
    if (MapPlane != 0)
        CenterEdit(pt.x, pt.y);
    SetMapModeAnt(MapPlane);
    UpdateEdit();
}

extern int far LessonTemp;
extern int far MePlane;
extern int far MeLocY;
extern int far MeLocX;

void far CenterAnt(void)
{
    LessonTemp = 1;
    if (MePlane != MapPlane)
        SetMapPlane(MePlane);
    CenterEdit(MeLocX, MeLocY);
}

extern int far CurGameType;
extern void far myBeginSound(int a, int b, int c);

void far GotoMyAnt(void)
{
    LessonTemp = 1;
    if (CurGameType == 3)
        myBeginSound(1, 0, 0x7e);
    else
        GotoMapPoint(MePlane, MeLocX, MeLocY);
}

extern int far SpidOn;
extern int far SpidY;
extern int far SpidX;

void far GotoSpider(void)
{
    if (SpidOn == 0)
        myBeginSound(1, 0, 0x7e);
    else
        GotoMapPoint(1, SpidX >> 4, SpidY >> 4);
}

extern Point far LastBlackEgg;

void far GotoBQueen(void)
{
    GotoMapPoint(2, LastBlackEgg.x, LastBlackEgg.y);
}

extern Point far LastRedEgg;

void far GotoRQueen(void)
{
    GotoMapPoint(3, LastRedEgg.x, LastRedEgg.y);
}

void far f_015B_0780(void)
{
}

void far f_015B_0788(void)
{
}

void far f_015B_0790(void)
{
}

extern int far ColonyTotalBlack;
extern int far BpopT;
extern void far PictStrnDialog(int a, int b, int c);
extern unsigned char far YMapPopB[][16];
extern int far MeType;
extern int far MeNestStarted;
extern void far myBeginSong(int id, int arg);
extern void far DrawMap(void);
extern int far JustXfered;
extern int far QueenStorageB;
extern int far QueenStorageR;
extern int far SwarmCntB;
extern int far SwarmCntR;
extern void far InvalQueenStorageDisp(void);
extern int far fd_3E1D_0000[][12];
extern unsigned char far YMapPopR[][16];
extern void far RandWorld(unsigned seed, int blackSize, int redSize, int x, int y);
extern int far HealthR;

void far XferPatch(void)
{
    int x, y;

    y = YMapPnt.y;
    x = YMapPnt.x;
    if (x == CurYardPnt.x && CurYardPnt.y == y)
        return;
    if (CurGameType != 2) {
        myBeginSound(1, 0, 0x7e);
        PictStrnDialog(0, 0x2710, 1);
    } else if (ColonyTotalBlack <= 1 && BpopT <= 1) {
        myBeginSound(1, 0, 0x7e);
        PictStrnDialog(0, 0x2712, 1);
    } else if (YMapPopB[x][y] < 1 && (MeType != 0x40 || MeNestStarted != 0)) {
        myBeginSound(1, 0, 0x7e);
        PictStrnDialog(0, 0x2714, 1);
    } else {
        myBeginSong(0x2afa, 0x7e);
        CurYardPnt.x = x;
        CurYardPnt.y = y;
        DrawMap();
        JustXfered = 1;
        QueenStorageB = 0;
        QueenStorageR = 0;
        SwarmCntB = 0;
        SwarmCntR = 0;
        InvalQueenStorageDisp();
        MeNestStarted = 1;
        RandWorld(fd_3E1D_0000[y][x], YMapPopB[x][y], YMapPopR[x][y], x, y);
        if (YMapPopR[x][y] == 0)
            HealthR = 0;
        if ((x << 4) + y > 0x24)
            PictStrnDialog(0, 0x2716, 0);
        else
            PictStrnDialog(0, 0x2717, 0);
    }
}

struct Rect {
    int left;
    int top;
    int right;
    int bottom;
};

struct Event {
    int what;
    int message;
    int x4;
    int modifiers;
    Point where;
    int code;
    int xE;
};

extern void far * far * far WindPromptStrs;
extern void far EditMessage(void far *, long, int);
extern int far LayDownQueenMode;
extern int _fastcall win_GetEvent(struct Event far *);
extern void far GetMousePos(Point far *);
extern int _fastcall win_IsWinInFront(int);
extern Point far fd_50F6_10D2;
extern Point far fd_55B3_2A42;
extern void far InvertPatch(int, int);
extern int far BColoniesStarted;
extern int far ColonyUpdateFlag;
extern void far MakeDMap(int);
extern void far UpdateYard(void);
extern void far myDelay(long);

void far PlaceQueenInYard(void)
{
    int x, y;
    int lastX, lastY;
    int patchX, patchY;
    int done;
    Point pt;
    struct Rect r;
    struct Event ev;

    patchX = -1;
    if (QueenStorageB < 1) {
        myBeginSound(1, 0, 0x7e);
        if (CurGameType != 2)
            EditMessage(WindPromptStrs[16], 180L, 1);
        else
            EditMessage(WindPromptStrs[7], 180L, 1);
        return;
    }
    if (LayDownQueenMode == 1)
        LayDownQueenMode = 0;
    r.left = CurYardPnt.x - 3;
    r.right = CurYardPnt.x + 3;
    r.top = CurYardPnt.y - 3;
    r.bottom = CurYardPnt.y + 3;
    if (r.left < 0)
        r.left = 0;
    else if (r.left > 11)
        r.left = 11;
    if (r.right < 0)
        r.right = 0;
    else if (r.right > 11)
        r.right = 11;
    if (r.top < 0)
        r.top = 0;
    else if (r.top > 15)
        r.top = 15;
    if (r.bottom < 0)
        r.bottom = 0;
    else if (r.bottom > 15)
        r.bottom = 15;
    do {
        EditMessage(WindPromptStrs[8], -2L, 1);
        lastY = lastX = -1;
        done = 0;
        while (!done) {
            if (win_GetEvent(&ev) && ev.code == 0x1902) {
                pt = ev.where;
                done = 1;
            } else {
                GetMousePos(&pt);
            }
            if (!win_IsWinInFront(0x1900))
                goto out;
            y = pt.y - fd_50F6_10D2.y;
            x = pt.x - fd_50F6_10D2.x;
            if (g_3DB2 == 0x140) {
                x = (x + 2) * 2;
                y = (y - 8) * 2;
            }
            y = (y - fd_55B3_2A42.y) / 10;
            x = (y * 10 - fd_55B3_2A42.x + x) / 28;
            WinPrintf("\nYARD AREA @ %d, %d  : %d, %d", x, y, 12, 16);
            if (lastX != x || lastY != y) {
                lastX = x;
                lastY = y;
                if (patchX != -1) {
                    InvertPatch(patchX, patchY);
                    patchX = -1;
                }
                if (r.left <= x && r.right >= x && y >= r.top && y <= r.bottom) {
                    if (CurYardPnt.x != x || CurYardPnt.y != y) {
                        InvertPatch(x, y);
                        patchX = x;
                        patchY = y;
                    }
                    YMapPnt.x = x;
                    YMapPnt.y = y;
                }
            }
        }
        if (patchX != -1) {
            InvertPatch(patchX, patchY);
            patchX = -1;
        }
        if (r.left <= x && r.right >= x && y >= r.top && y <= r.bottom) {
            myBeginSong(0x2afb, 0x7e);
            QueenStorageB--;
            YMapPopB[x][y]++;
            BColoniesStarted++;
            MakeDMap(ColonyUpdateFlag = 1);
            DrawMap();
            EditMessage(WindPromptStrs[9], 120L, 1);
            if (QueenStorageB <= 0)
                return;
            UpdateYard();
        } else {
            EditMessage(WindPromptStrs[10], 120L, 1);
            myBeginSound(1, 0, 0x7e);
            if (*(char far *)0x00000417L & 3)
                myDelay(30L);
        }
    } while (*(char far *)0x00000417L & 3);
    return;
out:
    EditMessage(0L, -2L, 1);
}

extern int far RRand(int limit);
extern void far AddFood(int count, int sound);
extern void far myBeginSoundReverse(int a, int b, int c);
extern void far f_00DF_00E0(int a);
extern void far MakeNewHoleR(int x);
extern void far MakeNewHoleB(int x);
extern int far AlwaysHealthy;
extern int far HealthB;
extern int far Invincible;
extern int far RevSpider;
extern int far MeSMode;

void far MysteryButton(void)
{
    int i;

    switch (RRand(15)) {
    case 0:
    case 1:
        AddSomeAnts(0);
        AddSomeAnts(0);
        break;
    case 2:
        AddSomeAnts(1);
        AddSomeAnts(1);
        break;
    case 3:
        KillSomeAnts(0);
        KillSomeAnts(0);
        break;
    case 4:
        KillSomeAnts(1);
        KillSomeAnts(1);
        break;
    case 5:
        AddFood(0x96, 1);
        break;
    case 6:
        myBeginSoundReverse(0x20, 0, 0x7e);
        SubtractFood();
        break;
    case 7:
        f_00DF_00E0(0);
        break;
    case 8:
        for (i = 0; i < 0x20; i++)
            MakeNewHoleR(i * 2);
        break;
    case 9:
        for (i = 0; i < 0x20; i++)
            MakeNewHoleB(i * 2);
        break;
    case 10:
        AlwaysHealthy = 0;
        HealthB = 0;
        HealthR = 0;
        break;
    case 11:
        if (Invincible = !Invincible)
            myBeginSound(2, 0, 0x7e);
        else
            myBeginSound(1, 0, 0x7e);
        break;
    case 12:
        RevSpider = !RevSpider;
        break;
    case 13:
        PictStrnDialog(0, 0x2726, 0);
        f_00DF_00E0(1);
        PictStrnDialog(0, 0x2728, 0);
        break;
    case 14:
        MeSMode = 8;
        myBeginSound(2, 0x2b77, 0x7e);
        break;
    }
}
