/* Overlay section S22, code frame 39C7: editor mouse dispatch and the yellow ant
 * (processEdit..YellowHelp; Win16 SIMANT unit processEdit..YellowHelp).
 * Built /AL /Os /Oe /Og /Zi under MSC 6.00AX: 6.00A allocates CONST segment words for
 * far variables whose loads were all hoisted to immediate segments (YellowDeath), 6.00AX
 * does not.  /Zi (a code record per function) reproduces the original relocation order
 * across all 15 functions, /Zd cannot (SetGoalsY and YellowCommandKey start records).
 * The one-line ifs and the while loops in YellowDeath place the line-number record
 * breaks (every 52 entries) where the original has them.  The MapPnt/editTileRect
 * struct types decide the imul operand order in DoLaserFire; the fd_50F6_048A
 * declaration after 0AE8 decides the compare order in YellowCommandKey. */

struct Event {
    int what;
    int message;
    int x4;
    int modifiers;
    int h;
    int v;
    int code;
    int xE;
};

extern int far WinPrintf(char far *format, ...);
extern int _fastcall win_IsWinInFront(int win);
extern long far TickCount(void);
extern int _fastcall win_GetEvent(struct Event far *ev);
struct Rect {
    int left;
    int top;
    int right;
    int bottom;
};
struct Pt {
    int x;
    int y;
};

extern struct Rect far fd_50F6_110C;
extern int far fd_55B3_19BE;
extern struct Pt far fd_50F6_0508;
extern int far fd_55B3_19C0;
extern int far fd_50F6_0EAC;
extern void far processExp(int x, int y, int shift);
extern int far fd_50F6_0F44;
extern int far fd_50F6_105E;
extern int far fd_50F6_048C;
extern int far IsItYellow(int plane, int x, int y);
extern int far myButton(void);
extern void far AntMenu(struct Event far *ev);
extern int far GetLife(int plane, int x, int y);
extern void far f_015B_0653(void);
extern int far MapPlane;
extern int far MagnifyMenu(int x, int y, int plane);
extern int far fd_50F6_0A06;
extern int far IsYellowAnt(int life);
extern int far FindAntIndex(int plane, int x, int y, int life);
extern int far fd_50F6_07C0;
extern int far fd_50F6_04E2;
extern int far fd_50F6_0A8E;
extern int far fd_50F6_084E;
extern int far fd_50F6_08DA;
extern int far fd_50F6_08E2;
extern int far fd_50F6_09F0;
void far SetGoalsY(int plane, int x, int y);
extern int far fd_50F6_0AA0;
extern int far IsItDigable(int plane, int x, int y);
extern int far GetMap(int plane, int x, int y);
extern int far IsThisGrass(int plane, int tile);
extern int far fd_50F6_04C2;
extern int far IsLiftable(int plane, int x, int y);
extern void far ExchangeLives(int plane, int x, int y);
void far processSpider(int x, int y, int mode);

void far processEdit(struct Event far *ePtr)
{
    struct Event ev;
    long t;
    int shift;
    int x;
    int y;
    int life;

    if ((*(unsigned char far *)0x417L & 8) == 1)
        shift = 1;
    else
        shift = (ePtr->modifiers & 0x6000) != 0;
    WinPrintf("ePtr->mouse_flags=%x", ePtr->modifiers);
    if (!shift && win_IsWinInFront(0)) {
        t = TickCount() + 6;
        while (TickCount() < t) {
            if (win_GetEvent(&ev) == 1 && (ev.modifiers & 0x6000) && ev.code == ePtr->code) {
                ePtr = &ev;
                break;
            }
        }
        shift = (ePtr->modifiers & 0x6000) != 0;
    }
    x = (ePtr->h - fd_50F6_110C.left) / fd_55B3_19BE + fd_50F6_0508.x;
    y = (ePtr->v - fd_50F6_110C.top) / fd_55B3_19C0 + fd_50F6_0508.y;
    if (fd_50F6_0EAC == 3) {
        processExp(x, y, shift);
        return;
    }
    if (fd_50F6_0F44) fd_50F6_0F44 = 0;
    switch (fd_50F6_105E) {
    case -1:
        if (!shift) {
            if (IsItYellow(fd_50F6_048C, x, y) == 1) {
                if (myButton() == 1) {
                    AntMenu(ePtr);
                    return;
                }
                if (GetLife(fd_50F6_048C, x, y) != 0xfe) f_015B_0653();
                return;
            }
            if (myButton() == 1 && MagnifyMenu(x, y, MapPlane) >= 0)
                return;
        } else if (fd_50F6_0A06 == 0 && (life = GetLife(MapPlane, x, y)) >= 0
                   && (life & 0x7f) >= 8 && !IsYellowAnt(life)) {
            if ((fd_50F6_07C0 = FindAntIndex(MapPlane, x, y, life)) < 0)
                return;
            fd_50F6_0A8E = ((fd_50F6_04E2 ^ life) & 0x80) ? 3 : 4;
            fd_50F6_084E = life;
            if (MapPlane == 0)
                fd_50F6_08DA = 1;
            else
                fd_50F6_08DA = MapPlane;
            fd_50F6_08E2 = x;
            fd_50F6_09F0 = y;
            SetGoalsY(MapPlane, x, y);
            fd_50F6_0AA0 = 1;
            return;
        }
        WinPrintf("\nMapPlane=%d", MapPlane);
        if (MapPlane <= 1) {
            if (fd_50F6_0A06 == 1) {
                processSpider(x, y, shift);
                return;
            }
            fd_50F6_0A8E = shift;
        } else {
            if (fd_50F6_0A06 != 0)
                return;
            if (shift == 1) {
                if (IsItDigable(MapPlane, x, y) == 1
                    || (fd_50F6_048C >= 2 && y <= 0
                        && IsThisGrass(MapPlane, GetMap(MapPlane, x, y)) == 1))
                    fd_50F6_0A8E = 2;
                else if ((fd_50F6_04C2 & 8) || IsLiftable(MapPlane, x, y))
                    fd_50F6_0A8E = 1;
                else
                    fd_50F6_0A8E = 2;
            } else
                fd_50F6_0A8E = 0;
        }
        SetGoalsY(MapPlane, x, y);
        fd_50F6_0AA0 = 1;
        return;
    case 10:
        ExchangeLives(MapPlane == 0 ? 1 : MapPlane, x, y);
        return;
    case 11:
        if (MapPlane <= 1 && fd_50F6_0A06 == 1)
            processSpider(x, y, shift);
        return;
    }
}

extern void far myBeginSound(int a, int b, int c);
extern char near g_5A97;
extern void far clip_Push(void);
extern int _fastcall win_IsWinOpen(int win);
extern void far clip_SetWin(int win);
extern int far * near g_5AAC;
extern void far f_0250_5058(void);
extern int far f_1B4E_000D(int color);
extern void (far * near g_916C)(int x0, int y0, int x1, int y1, int color);
extern void (far * near g_9134)(int x0, int y0, int x1, int y1, int color);
extern void far f_0250_0E15(void);
extern void far clip_SubInclude(struct Rect far *rect);
extern int far fd_50F6_3856;
extern struct Rect far fd_50F6_10D2;
extern int far fd_50F6_3858;
extern int far fd_55B3_29A2;
extern void far clip_Pop(void);

void far DoLaserFire(int x1, int y1, int x2, int y2)
{
    int sx;
    int sy;
    int ex;
    int ey;
    int originX;
    int originY;

    myBeginSound(0x37, 0x8265, 0x3f);
    if (MapPlane == 1) {
        if (g_5A97 == 2) {
            x2 = (3 * x2) / 4;
            y2 = (3 * y2) / 4;
            x1 = (3 * x1) / 4;
            y1 = (3 * y1) / 4;
        }
        clip_Push();
        if (win_IsWinOpen(0)) {
            clip_SetWin(0);
            if (g_5AAC[1] != 0x8000) {
                f_0250_5058();
                originX = fd_50F6_0508.x * fd_55B3_19BE - fd_50F6_110C.left;
                originX = -originX;
                originY = fd_55B3_19C0 * fd_50F6_0508.y - fd_50F6_110C.top;
                originY = -originY;
                ex = originX + x1;
                ey = originY + y1;
                sx = originX + x2;
                sy = originY + y2;
                g_916C(ex, ey, sx, sy, f_1B4E_000D(3));
                g_916C(ex + 1, ey + 1, sx + 1, sy + 1, f_1B4E_000D(3));
                g_9134(sx, sy, sx + 2, sy + 2, f_1B4E_000D(2));
                f_0250_0E15();
            }
        }
        if (win_IsWinOpen(0x100)) {
            clip_SetWin(0x100);
            clip_SubInclude(&fd_50F6_10D2);
            sx = (x2 / fd_55B3_19BE) * fd_50F6_3856 + fd_50F6_10D2.left;
            sy = (y2 / fd_55B3_19C0) * fd_50F6_3858 + fd_50F6_10D2.top;
            ex = (x1 / fd_55B3_19BE) * fd_50F6_3856 + fd_50F6_10D2.left;
            ey = (y1 / fd_55B3_19C0) * fd_50F6_3858 + fd_50F6_10D2.top;
            g_916C(ex, ey, sx, sy, f_1B4E_000D(3));
            g_916C(ex + 1, ey + 1, sx + 1, sy + 1, f_1B4E_000D(3));
            g_9134(sx, sy, sx + 2, sy + 2, f_1B4E_000D(1) | 0x20);
            fd_55B3_29A2 = 1;
        }
        clip_Pop();
    }
}

extern int far Starg;
extern int far StargLife;
extern int far SMode;
extern int far SuserX;
extern int far SuserY;
extern unsigned char far LifeA[64][64];
extern int far fd_50F6_06AC;
extern void far EndTargetMode(void);

void far processSpider(int x, int y, int mode)
{
    int life;
    int idx;

    if (mode < 1 && fd_50F6_105E != 11) {
        Starg = -2;
        StargLife = -1;
        SMode = 0;
        SuserX = x;
        SuserY = y;
        fd_50F6_0A8E = mode;
        return;
    }
    life = LifeA[x][y];
    if (life != 0) {
        idx = FindAntIndex(1, x, y, life);
        if (idx >= 0) {
            StargLife = life;
            Starg = idx;
            SMode = 2;
            if (fd_50F6_105E == 11) {
                myBeginSound(0xf, 0, 0x7e);
                fd_50F6_06AC = 6;
                EndTargetMode();
            }
            return;
        }
    }
    if (fd_50F6_105E == 11) {
        myBeginSound(1, 0, 0x7e);
        return;
    }
    Starg = -2;
    StargLife = -1;
    SMode = 0;
    SuserX = x;
    SuserY = y;
    fd_50F6_0A8E = mode;
}

extern int far fd_50F6_0AF8;
extern int far fd_50F6_047C;
extern int far fd_50F6_0AB6;
extern int far fd_50F6_0AD6;
extern int far fd_50F6_0AC6;
extern int far fd_50F6_0AE8;
extern int far fd_50F6_048A;
extern int far fd_50F6_0B1E;
extern int far fd_50F6_0C38;
extern int far fd_50F6_0C3E;
extern int far fd_50F6_0D6C;

void far ResetYellowVars(int plane, int x, int y)
{
    fd_50F6_048C = plane;
    fd_50F6_0AF8 = plane;
    fd_50F6_047C = x;
    fd_50F6_0AB6 = x;
    fd_50F6_0AD6 = x;
    fd_50F6_048A = y;
    fd_50F6_0AC6 = y;
    fd_50F6_0AE8 = y;
    fd_50F6_0A8E = 0;
    fd_50F6_0AA0 = 0;
    fd_50F6_0B1E = 0;
    fd_50F6_0C38 = 0;
    fd_50F6_0C3E = 0;
    fd_50F6_0D6C = -2;
}

void far SetGoalsY(int plane, int x, int y)
{
    if (plane == 0)
        fd_50F6_0AF8 = 1;
    else
        fd_50F6_0AF8 = plane;
    fd_50F6_0AD6 = x;
    fd_50F6_0AE8 = y;
    fd_50F6_0D6C = -2;
    if (plane >= 2 && y < 2) {
        if (x <= 0)
            x = 1;
        else if (x >= 63)
            x = 62;
        fd_50F6_0AD6 = x;
    }
}

extern int far fd_3D57_07A8[];
extern int far fd_50F6_0502;
extern int far fd_50F6_0496;
extern void far SetMyLife(int plane, int x, int y, int type, int dir, int code);
extern void far ClearMyLife(int plane, int x, int y, int type, int dir);
extern void far f_015B_06A2(void);
extern void far DoEditAndMapUpdateDraw(void);
extern void far myBeginSong(unsigned int id, unsigned int arg);
extern int far mySongIsDone(void);
extern int far win_Events(void);
extern void far myDelay(long ticks);
extern void far SetLife(int plane, int x, int y, int value);
extern void far win_FlushEvents(void);
extern int far fd_3D57_0C24;
extern void far SetMyHealth(int health);
extern long far MacTickCount(void);
extern void far DoEditUpdateDraw(void);
extern void far MakeBlkQueen(int x, int y, int dir);
extern int far fd_50F6_0AEC[6];
extern void far MakeRedQueen(int x, int y, int dir);
extern int far fd_50F6_0AFA[6];
extern int far BpopT;
extern int far RpopT;
extern int far mySoundIsDone(void);
extern void far SetSimCursor(int a);
void far YellowDialog(int bitmap, int promptIndex);

void far YellowBirth(int plane, int x, int y, int type, int mode)
{
    long t;
    int save;
    int oldType;
    int i;

    save = fd_3D57_07A8[2];
    oldType = fd_50F6_04C2;
    fd_3D57_07A8[2] = 0;
    fd_50F6_0A06 = 0;
    if (mode == 0) {
        fd_50F6_0502 = 1;
        SetMyLife(plane, x, y, 0, fd_50F6_0496, 0xff);
    } else {
        ClearMyLife(fd_50F6_048C, fd_50F6_047C, fd_50F6_048A, fd_50F6_04C2, fd_50F6_0496);
        SetMyLife(fd_50F6_048C, fd_50F6_047C, fd_50F6_048A, 0x60, fd_50F6_0496, 0xff);
    }
    if (mode == 0)
        f_015B_06A2();
    DoEditAndMapUpdateDraw();
    if (mode != 0) {
        myBeginSong(0x4e20, 0x7e);
        t = TickCount() + 300;
        while (!mySongIsDone()) {
            if (TickCount() >= t || win_Events())
                break;
            myDelay(1L);
        }
        SetLife(plane, x, y, 1);
        DoEditAndMapUpdateDraw();
    }
    win_FlushEvents();
    fd_3D57_07A8[2] = save;
    myBeginSound(0x1c, 0, 0x7e);
    myDelay(45L);
    ResetYellowVars(fd_50F6_048C, fd_50F6_047C, fd_50F6_048A);
    fd_3D57_0C24 = 1;
    SetMyHealth(100);
    if (mode == 0)
        fd_50F6_0496 = oldType == 0x60 ? 2 : 6;
    for (i = 2; i <= 7; i++) {
        t = MacTickCount() + 10;
        if (mode == 0) {
            fd_50F6_0502 = i;
            SetMyLife(fd_50F6_048C, fd_50F6_047C, fd_50F6_048A, 0, fd_50F6_0496, 0xff);
        } else
            SetLife(fd_50F6_048C, x, y, i);
        DoEditUpdateDraw();
        while (MacTickCount() < t && !win_Events())
            myDelay(1L);
    }
    win_FlushEvents();
    if (mode != 0)
        while (!mySongIsDone())
            myDelay(5L);
    myBeginSound(0x31, 0, 0x7e);
    if (mode == 0) {
        SetMyLife(fd_50F6_048C, fd_50F6_047C, fd_50F6_048A, type, fd_50F6_0496, 0xff);
    } else {
        ClearMyLife(fd_50F6_048C, fd_50F6_047C, fd_50F6_048A, fd_50F6_04C2, fd_50F6_0496);
        if (fd_50F6_048C == 2) {
            MakeBlkQueen(fd_50F6_047C, fd_50F6_048A, fd_50F6_0496);
            fd_50F6_0AEC[5]++;
        } else {
            MakeRedQueen(fd_50F6_047C, fd_50F6_048A, fd_50F6_0496);
            fd_50F6_0AFA[5]++;
        }
        SetMyLife(fd_50F6_048C, x, y, type, fd_50F6_0496 ^ 4, 0xff);
        if (fd_50F6_04E2 == 0) {
            fd_50F6_0AEC[1]++;
            fd_50F6_0AEC[4]--;
            BpopT++;
        } else {
            fd_50F6_0AFA[1]++;
            fd_50F6_0AFA[4]--;
            RpopT++;
        }
    }
    DoEditUpdateDraw();
    while (!mySoundIsDone())
        myDelay(5L);
    if (mode != 0)
        myBeginSong(0x4e21, 0x7e);
    else
        myBeginSong(0x2afd, 0x7e);
    SetSimCursor(0);
    YellowDialog(0x238d, mode + 1);
}

extern void far SetDefaultWindPrompt(int mode);
extern int far DropMyObject(int plane, int x, int y, int tx, int ty);
extern signed char far fd_3D57_0094[];
extern void far o25_3BA4_0C01(int plane, int x, int y, int dir, int type, int cause);
extern int far SRand1(int range);
extern int far fd_50F6_1058;
extern void far PictStrnDialog(int pict, int strn, int flag);
extern void far SpiderDialog(void);
extern long far BAntsEaten;
extern void far o25_3BA4_0999(int plane, int x, int y, int dir, int type, int cause);
void far LionDialog(void);
extern long far fd_50F6_0EFC;
extern long far fd_50F6_0F30;
extern void far UpdateEverything(void);
extern void far UnRecruit(int all);
extern int far fd_50F6_104E;
void far SetAlarmDropState(int state, int quiet);
extern int far ListIndexB;
extern unsigned char far BlistT[];
extern unsigned char far BlistY[];
extern int far fd_50F6_0F26;
extern unsigned char far BlistX[];
extern int far fd_50F6_0F0E;
extern unsigned char far LifeB[64][64];
extern int far ListIndexA;
extern unsigned char far AlistT[];
extern unsigned char far AlistY[];
extern unsigned char far AlistX[];
extern int far ListIndexR;
extern unsigned char far RlistT[];
extern unsigned char far RlistY[];
extern unsigned char far RlistX[];
extern unsigned char far LifeR[64][64];
extern int far fd_50F6_0376;
extern int far fd_50F6_0366;
extern int far fd_50F6_03E2;
void far SpecialXfer(void);

void far YellowDeath(int cause)
{
    int save;
    int strn;
    int found;
    int i;
    int t;
    int life;

    SetSimCursor(6);
    SetDefaultWindPrompt(1);
    if (fd_50F6_0A06 == 0 && (fd_50F6_04C2 & 8)) {
        save = fd_3D57_07A8[2];
        fd_3D57_07A8[2] = 0;
        if (!DropMyObject(fd_50F6_048C, fd_50F6_047C, fd_50F6_048A, fd_50F6_047C, fd_50F6_048A))
            fd_50F6_04C2 = (fd_50F6_04C2 & 0x80) | (fd_3D57_0094[(fd_50F6_04C2 & 0x78) >> 3] << 3);
        fd_3D57_07A8[2] = save;
    }
    f_015B_06A2();
    DoEditAndMapUpdateDraw();
    if (cause >= 7 && cause < 10)
        o25_3BA4_0C01(fd_50F6_048C, fd_50F6_047C, fd_50F6_048A, fd_50F6_0496, fd_50F6_04C2, cause);
    SetSimCursor(0);
    switch (cause) {
    case 0:
        myBeginSong(SRand1(5) + 0x4e27, 0x7e);
        strn = fd_50F6_1058 ? 0x272e : 0x2730;
        if (fd_3D57_07A8[3]) PictStrnDialog(0x23c4, strn, 1);
        break;
    case 1:
        if (fd_3D57_07A8[3]) SpiderDialog();
        BAntsEaten++;
        myBeginSong(SRand1(5) + 0x4e27, 0x7e);
        o25_3BA4_0999(fd_50F6_048C, fd_50F6_047C, fd_50F6_048A, fd_50F6_0496, fd_50F6_04C2, cause);
        break;
    case 2:
        if (fd_3D57_07A8[3]) LionDialog();
        BAntsEaten++;
        myBeginSong(SRand1(5) + 0x4e27, 0x7e);
        o25_3BA4_0999(fd_50F6_048C, fd_50F6_047C, fd_50F6_048A, fd_50F6_0496, fd_50F6_04C2, cause);
        break;
    case 3:
        myBeginSound(1, 0, 0x7e);
        if (fd_3D57_07A8[3])
            PictStrnDialog(0, 0x272a, 1);
        fd_50F6_0EFC++;
        break;
    case 4:
        myBeginSound(1, 0, 0x7e);
        if (fd_3D57_07A8[3])
            PictStrnDialog(0, 0x272c, 1);
        fd_50F6_0EFC++;
        break;
    case 5:
        myBeginSong(SRand1(5) + 0x4e27, 0x7e);
        if (fd_3D57_07A8[3])
            PictStrnDialog(0x23c3, 0x2732, 1);
        fd_50F6_0EFC++;
        break;
    case 6:
        myBeginSong(SRand1(5) + 0x4e27, 0x7e);
        if (fd_3D57_07A8[3])
            PictStrnDialog(0x23c0, 0x2734, 1);
        fd_50F6_0EFC++;
        break;
    case 7:
        myBeginSong(SRand1(5) + 0x4e27, 0x7e);
        if (fd_3D57_07A8[3])
            PictStrnDialog(0x23be, 0x2736, 1);
        fd_50F6_0EFC++;
        break;
    case 8:
        myBeginSong(SRand1(5) + 0x4e27, 0x7e);
        if (fd_3D57_07A8[3])
            PictStrnDialog(0x23c2, 0x2738, 1);
        fd_50F6_0F30++;
        break;
    case 9:
        myBeginSong(SRand1(5) + 0x4e27, 0x7e);
        if (fd_3D57_07A8[3])
            PictStrnDialog(0x23bf, 0x273a, 1);
        fd_50F6_0EFC++;
        break;
    case 10:
        fd_50F6_0EFC++;
        o25_3BA4_0999(fd_50F6_048C, fd_50F6_047C, fd_50F6_048A, fd_50F6_0496, fd_50F6_04C2, 10);
        if (fd_3D57_07A8[3])
            PictStrnDialog(0x23c4, 0x273d, 1);
        break;
    }
    if (cause >= 1 && cause <= 2)
        YellowDialog(0x238c, 0);
    UpdateEverything();
    if (fd_50F6_0A06 == 0)
        ClearMyLife(fd_50F6_048C, fd_50F6_047C, fd_50F6_048A, fd_50F6_04C2, fd_50F6_0496);
    SetSimCursor(6);
    UnRecruit(1);
    if (fd_50F6_104E)
        SetAlarmDropState(0, 1);
    found = 0;
    i = ListIndexB;
    while (i >= 0) {
        t = BlistT[i];
        if (t != 0 && t < 8) {
            LifeB[fd_50F6_0F0E = BlistX[i]][fd_50F6_0F26 = BlistY[i]] = BlistT[i] = 0;
            found = 1;
            fd_50F6_048C = 2;
            break;
        }
        i--;
    }
    if (!found) {
        i = ListIndexB;
        while (i >= 0) {
            t = BlistT[i];
            if (t != 0 && t > 7 && t < 0x68) {
                LifeB[fd_50F6_0F0E = BlistX[i]][fd_50F6_0F26 = BlistY[i]] =
                    (life = BlistT[i], BlistT[i] = 0);
                found = 2;
                fd_50F6_048C = found;
                break;
            }
            i--;
        }
    }
    if (!found) {
        i = ListIndexA;
        while (i >= 0) {
            t = AlistT[i];
            if (t != 0 && t > 7 && t < 0x68) {
                LifeA[fd_50F6_0F0E = AlistX[i]][fd_50F6_0F26 = AlistY[i]] =
                    (life = AlistT[i], AlistT[i] = 0);
                found = 2;
                fd_50F6_048C = 1;
                break;
            }
            i--;
        }
    }
    if (!found) {
        i = ListIndexR;
        while (i >= 0) {
            t = RlistT[i];
            if (t != 0 && t > 7 && t < 0x68) {
                LifeR[fd_50F6_0F0E = RlistX[i]][fd_50F6_0F26 = RlistY[i]] =
                    (life = RlistT[i], RlistT[i] = 0);
                found = 2;
                fd_50F6_048C = 3;
                break;
            }
            i--;
        }
    }
    if (!found) {
        if (fd_50F6_0EAC <= 1) {
            fd_50F6_0376 = 1;
            fd_50F6_0366 = 0;
            return;
        } else if (fd_50F6_0EAC == 2) {
            if (fd_50F6_03E2 < 2) {
                fd_50F6_0376 = 1;
                fd_50F6_0366 = 0;
                PictStrnDialog(0, 0x2748, 1);
            } else {
                PictStrnDialog(0, 0x274a, 1);
                SpecialXfer();
            }
            return;
        }
    }
    if (found == 1) {
        if (fd_50F6_04C2 == 0x60)
            fd_50F6_04C2 = 0x10;
        YellowBirth(fd_50F6_048C, fd_50F6_0F0E, fd_50F6_0F26, fd_50F6_04C2, 0);
    } else {
        fd_50F6_0A06 = 0;
        SetMyLife(fd_50F6_048C, fd_50F6_0F0E, fd_50F6_0F26, life & 0xf8, fd_50F6_0496,
                  (life & 0xf8) + fd_50F6_0496);
        ResetYellowVars(fd_50F6_048C, fd_50F6_0F0E, fd_50F6_0F26);
        SetMyHealth(100);
        f_015B_06A2();
        DoEditAndMapUpdateDraw();
        PictStrnDialog(0, 0x274b, 1);
    }
}

extern int far fd_50F6_07CA[2];
extern unsigned char far fd_3D57_00A4[12][16];
extern void far MapToYard(void);
extern void _fastcall f_20E8_0725(int win);
extern void far f_015B_0273(int mode);
extern int far fd_3D57_0C20;
extern void far f_015B_053C(int plane);
extern void far * far * far fd_50F6_034C;
extern void far EditMessage(void far *msg, long ticks, int mode);
extern int near g_3DB2;
extern int far fd_55B3_2A42[2];
extern int far fd_50F6_07BC[2];
extern void far XferPatch(void);

void far SpecialXfer(void)
{
    struct Event ev;
    int done;
    int x;
    int y;

    fd_3D57_00A4[fd_50F6_07CA[0]][fd_50F6_07CA[1]] = 0;
    if (!win_IsWinInFront(0x1900)) {
        if (!win_IsWinOpen(0x1900))
            MapToYard();
        else
            f_20E8_0725(0x1900);
    }
    f_015B_0273(2);
    fd_3D57_0C20 = 1;
    f_015B_053C(0);
    EditMessage(fd_50F6_034C[20], -2L, 1);
    done = 0;
    while (!done) {
        if (!win_GetEvent(&ev))
            continue;
        if (!win_IsWinInFront(0x1900)) {
            if (!win_IsWinOpen(0x1900))
                MapToYard();
            else
                f_20E8_0725(0x1900);
        }
        y = ev.v - fd_50F6_10D2.top;
        x = ev.h - fd_50F6_10D2.left;
        if (g_3DB2 == 0x140) {
            x = (x + 2) * 2;
            y = (y - 8) * 2;
        }
        y = (y - fd_55B3_2A42[1]) / 10;
        x = (x - fd_55B3_2A42[0] + y * 10) / 28;
        if (x >= 0 && y >= 0 && x <= 11 && y <= 15) {
            if (fd_3D57_00A4[x][y]) {
                myBeginSong(0x2afb, 0x7e);
                fd_50F6_07BC[0] = x;
                fd_50F6_07BC[1] = y;
                XferPatch();
                done = 1;
            } else {
                myBeginSound(1, 0, 0x7e);
                EditMessage(fd_50F6_034C[19], 120L, 1);
            }
        } else {
            myBeginSound(1, 0, 0x7e);
            EditMessage(fd_50F6_034C[10], 120L, 1);
        }
    }
    EditMessage(0L, -2L, 1);
}

extern void _fastcall win_LockWin(int win);
extern void _fastcall win_SetObjBitmap(int obj, int bitmap);
extern void far win_Open(int win);
extern void _fastcall win_GetObjRect(int obj, struct Rect far *rect);
extern int _fastcall win_DrawBitMap(int x, int y, int id);
extern struct Pt far fd_3D57_0B14[];
extern void _fastcall win_UnlockWin(int win);
extern void _fastcall win_Close(int win);

void far LionDialog(void)
{
    struct Rect rect;
    long t1;
    long t2;
    int x0;
    int y0;
    int frame;

    if (fd_3D57_07A8[3] == 0)
        return;
    win_LockWin(0x1a00);
    win_SetObjBitmap(0x1a01, 0x23f0);
    win_Open(0x1a00);
    win_GetObjRect(0x1a01, &rect);
    y0 = rect.top;
    x0 = rect.left;
    myBeginSound(0x26, 0, 0x7e);
    while (!mySoundIsDone())
        ;
    frame = 1;
    t1 = MacTickCount() + 300;
    t2 = MacTickCount() + 30;
    win_FlushEvents();
    while (!win_Events()) {
        if (MacTickCount() >= t1)
            break;
        if (!win_IsWinOpen(0x1a00))
            break;
        if (MacTickCount() >= t2) {
            t2 = MacTickCount() + 30;
            if (g_3DB2 == 0x140)
                win_DrawBitMap(x0, y0, 0x23f0 + frame);
            else
                win_DrawBitMap(fd_3D57_0B14[frame].x + x0, fd_3D57_0B14[frame].y + y0, 0x23f0 + frame);
            if (frame & 1)
                myBeginSound(0x25, 0, 0x7e);
            frame++;
            if (frame > 3)
                frame = 2;
        }
    }
    win_FlushEvents();
    win_UnlockWin(0x1a00);
    win_Close(0x1a00);
}

extern void far win_PrintfAtObj(int obj, char far *fmt, ...);
extern struct Pt far fd_3D57_0B24;
extern int far f_1F58_0038(void);
extern void far DialogWaitInit(int mode);
extern int far DialogAbortOrCont(void);

void far YellowDialog(int bitmap, int promptIndex)
{
    struct Rect rect;
    int x0;
    int y0;

    if (fd_3D57_07A8[3] == 0)
        return;
    win_LockWin(0x1a00);
    win_SetObjBitmap(0x1a01, bitmap);
    win_Open(0x1a00);
    win_GetObjRect(0x1a01, &rect);
    y0 = rect.top;
    x0 = rect.left;
    switch (bitmap) {
    case 0x238c:
    case 0x238d:
        win_PrintfAtObj(0x1a02, fd_50F6_034C[promptIndex + 23]);
        myDelay(300L);
        break;
    case 0x2396:
        myBeginSound(0x2a, 0, 0x7e);
        myDelay(45L);
        if (g_3DB2 == 0x140) {
            fd_3D57_0B24.x = 0x28;
            fd_3D57_0B24.y = 0x23;
        }
        if (win_IsWinOpen(0x1a00))
            win_DrawBitMap(fd_3D57_0B24.x + x0, y0 + fd_3D57_0B24.y, 0x2397);
        myBeginSound(0x2d, 0, 0x7e);
        myDelay(45L);
        break;
    }
    if (!win_Events() && f_1F58_0038()) {
        DialogWaitInit(3);
        while (!DialogAbortOrCont() && !win_Events())
            ;
    }
    win_FlushEvents();
    win_UnlockWin(0x1a00);
    win_Close(0x1a00);
}

extern signed char far Dx8[8];
extern signed char far Dy8[8];
extern int far GetDir(int x1, int y1, int x2, int y2);
extern void far MoveMyLife(int plane, int x, int y, int type, int dir);
extern void far EatMyFood(int kind);

void far DoTroph(int x, int y, int index)
{
    int newX;
    int newY;

    newX = Dx8[index] + x;
    newY = Dy8[index] + y;
    MoveMyLife(fd_50F6_048C, newX, newY, fd_50F6_04C2, GetDir(newX, newY, x, y) - 1);
    DoEditUpdateDraw();
    EatMyFood(1);
}

extern int far fd_3D57_07BE;
extern void _fastcall win_SetObjSelectedState(int obj, int state);
extern int far fd_50F6_0FFA;
extern int far fd_50F6_0FB6;
extern void far InvalEuMap(int left, int top, int right, int bottom);

void far SetAlarmDropState(int state, int quiet)
{
    if (state) {
        if (fd_50F6_048C == 1 && fd_50F6_0A06 == 0) {
            fd_3D57_07BE = 0;
            win_SetObjSelectedState(0x10, state);
            fd_50F6_104E = 1;
            if (quiet == 0)
                myBeginSound(0xf, 0, 0x7e);
        } else if (quiet == 0)
            myBeginSound(1, 0, 0x7e);
    } else {
        fd_50F6_104E = 0;
        win_SetObjSelectedState(0x10, state);
        fd_3D57_07BE = -1;
        if (quiet == 0)
            myBeginSound(0xf, 0, 0x7e);
    }
    InvalEuMap(0, 0, fd_50F6_0FB6, fd_50F6_0FFA);
}

void far YellowCommand(int cmd);

int far YellowCommandKey(int key)
{
    int handled;

    handled = 1;
    switch (key) {
    case 0x30:
        YellowCommand(7);
        break;
    case 0x31:
        if (fd_50F6_0A06 == 0) {
            if (fd_50F6_04C2 == 0x40 && fd_3D57_0C24 == 0)
                YellowCommand(8);
            else
                YellowCommand(1);
        } else
            YellowCommand(10);
        break;
    case 0x32:
        if (fd_50F6_0A06 == 0) {
            if (fd_50F6_04C2 == 0x40 && fd_3D57_0C24 == 0)
                YellowCommand(9);
            else
                YellowCommand(2);
        } else
            YellowCommand(11);
        break;
    case 0x33:
        YellowCommand(4);
        break;
    case 0x34:
        YellowCommand(5);
        break;
    case 0x58:
    case 0x78:
        YellowCommand(6);
        break;
    case 0x88:
        if (*(unsigned char far *)0x417L & 3) {
            f_015B_06A2();
            break;
        }
        if (fd_50F6_0A06 == 0) {
            if (fd_50F6_0AA0)
                ResetYellowVars(fd_50F6_048C, fd_50F6_047C, fd_50F6_048A);
            else
                f_015B_0653();
        } else if (fd_50F6_0A06 == 1) {
            if (SuserX != fd_50F6_047C || SuserY != fd_50F6_048A) {
                SuserX = fd_50F6_047C;
                SuserY = fd_50F6_048A;
                SMode = 0;
            } else
                f_015B_0653();
        }
        break;
    case 0x824:
        if (fd_50F6_0A06 == 1)
            YellowCommand(12);
        break;
    case 0x847:
        myBeginSound(0xf, 0, 0x7e);
        f_015B_06A2();
        break;
    default:
        handled = 0;
        break;
    }
    return handled;
}

void far YellowHelp(void);
extern void far Recruit(int count);
extern void far StartLifeTransfer(void);
extern int far TryMyDropOrLift(int plane, int x, int y);
extern void far TargetAnt(void);

void far YellowCommand(int cmd)
{
    if (fd_50F6_0A06 > 1)
        return;
    switch (cmd) {
    case 0:
        YellowHelp();
        break;
    case 1:
        myBeginSong(0x2b05, 0x7e);
        Recruit(5);
        break;
    case 2:
        myBeginSong(0x2b06, 0x7e);
        Recruit(10);
        break;
    case 3:
        myBeginSong(0x2b07, 0x7e);
        Recruit(1000);
        break;
    case 4:
        myBeginSong(0x2b08, 0x7e);
        UnRecruit(0);
        break;
    case 5:
        myBeginSong(0x2b09, 0x7e);
        UnRecruit(1);
        break;
    case 6:
        StartLifeTransfer();
        break;
    case 7:
        SetAlarmDropState(!fd_50F6_104E, 0);
        break;
    case 8:
        if (fd_50F6_048C != 1 || TryMyDropOrLift(fd_50F6_048C, fd_50F6_047C, fd_50F6_048A) == -1)
            myBeginSound(1, 0, 0x7e);
        break;
    case 9:
        if (fd_50F6_048C == 2 && fd_50F6_048A >= 3) {
            SetSimCursor(6);
            YellowBirth(fd_50F6_048C, fd_50F6_047C + Dx8[fd_50F6_0496 ^ 4] * 2,
                        fd_50F6_048A + Dy8[fd_50F6_0496 ^ 4] * 2, 0x10, 1);
        } else
            myBeginSound(1, 0, 0x7e);
        break;
    case 10:
        TargetAnt();
        break;
    case 11:
        if (fd_50F6_06AC == 7) {
            fd_50F6_06AC = 0;
            myBeginSound(2, 0x56ee, 0x7e);
        } else {
            fd_50F6_06AC = 7;
            myBeginSound(2, 0x2b77, 0x7e);
        }
        break;
    case 12:
        if (fd_50F6_06AC == 8) {
            fd_50F6_06AC = 0;
            myBeginSound(2, 0x56ee, 0x7e);
        } else {
            fd_50F6_06AC = 8;
            myBeginSound(0x29, 0, 0x7e);
        }
        break;
    }
}

void far YellowHelp(void)
{
    struct Event ev;
    int bitmap;

    if (fd_50F6_0A06 == 0) {
        if (fd_50F6_04C2 == 0x40)
            bitmap = 0x1197;
        else
            bitmap = 0x1195;
    } else
        bitmap = 0x1199;
    win_LockWin(0x1a00);
    win_SetObjBitmap(0x1a01, bitmap);
    win_Open(0x1a00);
    DialogWaitInit(0x1e);
    while (win_IsWinOpen(0x1a01) && !DialogAbortOrCont()) {
        if (win_GetEvent(&ev) && (ev.code >> 8) == 0x1a)
            break;
    }
    win_UnlockWin(0x1a00);
    win_Close(0x1a00);
}

