/* Overlay section S22, code frame 39C7: editor mouse dispatch and the yellow ant
 * (processEdit..YellowHelp; Win16 SIMANT unit processEdit..YellowHelp). */

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
extern int _fastcall f_22BF_0A22(int win);
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
extern int far f_10F7_2548(int plane, int x, int y);
extern int far f_00F8_02AC(void);
extern void far AntMenu(struct Event far *ev);
extern int far GetLife(int plane, int x, int y);
extern void far f_015B_0653(void);
extern int far fd_50F6_032E;
extern int far o05_35F5_025C(int x, int y, int plane);
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
    if (!shift && f_22BF_0A22(0)) {
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
    if (fd_50F6_0F44)
        fd_50F6_0F44 = 0;
    switch (fd_50F6_105E) {
    case -1:
        if (!shift) {
            if (f_10F7_2548(fd_50F6_048C, x, y) == 1) {
                if (f_00F8_02AC() == 1) {
                    AntMenu(ePtr);
                    return;
                }
                if (GetLife(fd_50F6_048C, x, y) != 0xfe)
                    f_015B_0653();
                return;
            }
            if (f_00F8_02AC() == 1 && o05_35F5_025C(x, y, fd_50F6_032E) >= 0)
                return;
        } else if (fd_50F6_0A06 == 0 && (life = GetLife(fd_50F6_032E, x, y)) >= 0
                   && (life & 0x7f) >= 8 && !IsYellowAnt(life)) {
            if ((fd_50F6_07C0 = FindAntIndex(fd_50F6_032E, x, y, life)) < 0)
                return;
            fd_50F6_0A8E = ((fd_50F6_04E2 ^ life) & 0x80) ? 3 : 4;
            fd_50F6_084E = life;
            if (fd_50F6_032E == 0)
                fd_50F6_08DA = 1;
            else
                fd_50F6_08DA = fd_50F6_032E;
            fd_50F6_08E2 = x;
            fd_50F6_09F0 = y;
            SetGoalsY(fd_50F6_032E, x, y);
            fd_50F6_0AA0 = 1;
            return;
        }
        WinPrintf("\nMapPlane=%d", fd_50F6_032E);
        if (fd_50F6_032E <= 1) {
            if (fd_50F6_0A06 == 1) {
                processSpider(x, y, shift);
                return;
            }
            fd_50F6_0A8E = shift;
        } else {
            if (fd_50F6_0A06 != 0)
                return;
            if (shift == 1) {
                if (IsItDigable(fd_50F6_032E, x, y) == 1
                    || (fd_50F6_048C >= 2 && y <= 0
                        && IsThisGrass(fd_50F6_032E, GetMap(fd_50F6_032E, x, y)) == 1))
                    fd_50F6_0A8E = 2;
                else if ((fd_50F6_04C2 & 8) || IsLiftable(fd_50F6_032E, x, y))
                    fd_50F6_0A8E = 1;
                else
                    fd_50F6_0A8E = 2;
            } else
                fd_50F6_0A8E = 0;
        }
        SetGoalsY(fd_50F6_032E, x, y);
        fd_50F6_0AA0 = 1;
        return;
    case 10:
        ExchangeLives(fd_50F6_032E == 0 ? 1 : fd_50F6_032E, x, y);
        return;
    case 11:
        if (fd_50F6_032E <= 1 && fd_50F6_0A06 == 1)
            processSpider(x, y, shift);
        return;
    }
}

extern void far myBeginSound(int a, int b, int c);
extern char near g_5A97;
extern void far f_1E57_0DAA(void);
extern int _fastcall win_IsWinOpen(int win);
extern void far f_1E57_0174(int win);
extern int far * near g_5AAC;
extern void far f_0250_5058(void);
extern int far f_1B4E_000D(int color);
extern void (far * near g_916C)(int x0, int y0, int x1, int y1, int color);
extern void (far * near g_9134)(int x0, int y0, int x1, int y1, int color);
extern void far f_0250_0E15(void);
extern void far f_1E57_0773(struct Rect far *rect);
extern int far fd_50F6_3856;
extern struct Rect far fd_50F6_10D2;
extern int far fd_50F6_3858;
extern int far fd_55B3_29A2;
extern void far f_1E57_0EB9(void);

void far DoLaserFire(int x1, int y1, int x2, int y2)
{
    int sx;
    int sy;
    int ex;
    int ey;
    int originX;
    int originY;

    myBeginSound(0x37, 0x8265, 0x3f);
    if (fd_50F6_032E == 1) {
        if (g_5A97 == 2) {
            x2 = (3 * x2) / 4;
            y2 = (3 * y2) / 4;
            x1 = (3 * x1) / 4;
            y1 = (3 * y1) / 4;
        }
        f_1E57_0DAA();
        if (win_IsWinOpen(0)) {
            f_1E57_0174(0);
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
            f_1E57_0174(0x100);
            f_1E57_0773(&fd_50F6_10D2);
            sx = (x2 / fd_55B3_19BE) * fd_50F6_3856 + fd_50F6_10D2.left;
            sy = (y2 / fd_55B3_19C0) * fd_50F6_3858 + fd_50F6_10D2.top;
            ex = (x1 / fd_55B3_19BE) * fd_50F6_3856 + fd_50F6_10D2.left;
            ey = (y1 / fd_55B3_19C0) * fd_50F6_3858 + fd_50F6_10D2.top;
            g_916C(ex, ey, sx, sy, f_1B4E_000D(3));
            g_916C(ex + 1, ey + 1, sx + 1, sy + 1, f_1B4E_000D(3));
            g_9134(sx, sy, sx + 2, sy + 2, f_1B4E_000D(1) | 0x20);
            fd_55B3_29A2 = 1;
        }
        f_1E57_0EB9();
    }
}

extern int far fd_50F6_0FFC;
extern int far fd_50F6_10AE;
extern int far fd_50F6_0FB8;
extern int far fd_50F6_0F42;
extern int far fd_50F6_0F7E;
extern unsigned char far LifeA[64][64];
extern int far fd_50F6_06AC;
extern void far EndTargetMode(void);

void far processSpider(int x, int y, int mode)
{
    int life;
    int idx;

    if (mode < 1 && fd_50F6_105E != 11) {
        fd_50F6_0FFC = -2;
        fd_50F6_10AE = -1;
        fd_50F6_0FB8 = 0;
        fd_50F6_0F42 = x;
        fd_50F6_0F7E = y;
        fd_50F6_0A8E = mode;
        return;
    }
    life = LifeA[x][y];
    if (life != 0) {
        idx = FindAntIndex(1, x, y, life);
        if (idx >= 0) {
            fd_50F6_10AE = life;
            fd_50F6_0FFC = idx;
            fd_50F6_0FB8 = 2;
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
    fd_50F6_0FFC = -2;
    fd_50F6_10AE = -1;
    fd_50F6_0FB8 = 0;
    fd_50F6_0F42 = x;
    fd_50F6_0F7E = y;
    fd_50F6_0A8E = mode;
}

extern int far fd_50F6_0AF8;
extern int far fd_50F6_047C;
extern int far fd_50F6_0AB6;
extern int far fd_50F6_0AD6;
extern int far fd_50F6_048A;
extern int far fd_50F6_0AC6;
extern int far fd_50F6_0AE8;
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

extern int far fd_3D57_07AC;
extern int far fd_50F6_0502;
extern int far fd_50F6_0496;
extern void far SetMyLife(int plane, int x, int y, int type, int dir, int code);
extern void far ClearMyLife(int plane, int x, int y, int type, int dir);
extern void far f_015B_06A2(void);
extern void far DoEditAndMapUpdateDraw(void);
extern void far f_00DF_00B1(unsigned int id, unsigned int arg);
extern int far f_00DF_0138(void);
extern int far win_Events(void);
extern void far f_00F8_0265(long ticks);
extern void far SetLife(int plane, int x, int y, int value);
extern void far win_FlushEvents(void);
extern int far fd_3D57_0C24;
extern void far SetMyHealth(int health);
extern long far f_00F8_02BE(void);
extern void far f_0250_0E91(void);
extern void far MakeBlkQueen(int x, int y, int dir);
extern int far fd_50F6_0AEC[6];
extern void far MakeRedQueen(int x, int y, int dir);
extern int far fd_50F6_0AFA[6];
extern int far fd_50F6_0330;
extern int far fd_50F6_0350;
extern int far f_00DF_012D(void);
extern void far f_00F8_02DF(int a);
void far YellowDialog(int bitmap, int promptIndex);

void far YellowBirth(int plane, int x, int y, int type, int mode)
{
    long t;
    int save;
    int oldType;
    int i;

    save = fd_3D57_07AC;
    oldType = fd_50F6_04C2;
    fd_3D57_07AC = 0;
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
        f_00DF_00B1(0x4e20, 0x7e);
        t = TickCount() + 300;
        while (!f_00DF_0138()) {
            if (TickCount() >= t || win_Events())
                break;
            f_00F8_0265(1L);
        }
        SetLife(plane, x, y, 1);
        DoEditAndMapUpdateDraw();
    }
    win_FlushEvents();
    fd_3D57_07AC = save;
    myBeginSound(0x1c, 0, 0x7e);
    f_00F8_0265(45L);
    ResetYellowVars(fd_50F6_048C, fd_50F6_047C, fd_50F6_048A);
    fd_3D57_0C24 = 1;
    SetMyHealth(100);
    if (mode == 0)
        fd_50F6_0496 = oldType == 0x60 ? 2 : 6;
    for (i = 2; i <= 7; i++) {
        t = f_00F8_02BE() + 10;
        if (mode == 0) {
            fd_50F6_0502 = i;
            SetMyLife(fd_50F6_048C, fd_50F6_047C, fd_50F6_048A, 0, fd_50F6_0496, 0xff);
        } else
            SetLife(fd_50F6_048C, x, y, i);
        f_0250_0E91();
        while (f_00F8_02BE() < t && !win_Events())
            f_00F8_0265(1L);
    }
    win_FlushEvents();
    if (mode != 0)
        while (!f_00DF_0138())
            f_00F8_0265(5L);
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
            fd_50F6_0330++;
        } else {
            fd_50F6_0AFA[1]++;
            fd_50F6_0AFA[4]--;
            fd_50F6_0350++;
        }
    }
    f_0250_0E91();
    while (!f_00DF_012D())
        f_00F8_0265(5L);
    if (mode != 0)
        f_00DF_00B1(0x4e21, 0x7e);
    else
        f_00DF_00B1(0x2afd, 0x7e);
    f_00F8_02DF(0);
    YellowDialog(0x238d, mode + 1);
}

/* SCAFFOLD BEGIN: unrecovered same-module callees */
void far YellowDeath(void) { }
void far SpecialXfer(void) { }
void far LionDialog(void) { }
void far YellowDialog(int bitmap, int promptIndex) { }
void far DoTroph(int x, int y, int index) { }
void far SetAlarmDropState(int state, int quiet) { }
void far YellowCommandKey(void) { }
void far YellowCommand(void) { }
void far YellowHelp(void) { }
/* SCAFFOLD END */
