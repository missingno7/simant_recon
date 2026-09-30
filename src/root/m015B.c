/* Root module, code frame 015B: map/yard mode control and ant-list commands
 * (Win16 unit AddSomeAnts .. MysteryButton). */

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
extern unsigned char far fd_3E1D_AD3B[];
extern void far DeadAntHere(int x, int y, int type);
extern unsigned char far fd_3E1D_A569[];
extern unsigned char far fd_3E1D_A180[];
extern int far f_10F7_2548(int level, int x, int y);

void far KillSomeAnts(int mode)
{
    int i;
    int n;
    int type;

    CompactListA();
    FullCount();
    n = 0;
    for (i = ListIndexA - 1; i >= 0; i--) {
        type = fd_3E1D_AD3B[i];
        if (mode == 1) {
            if (!(type & 0x80)) {
                DeadAntHere(fd_3E1D_A180[i], fd_3E1D_A569[i], 0);
                fd_3E1D_AD3B[i] = 0;
                if (++n > 50)
                    break;
            }
        } else {
            if (type & 0x80) {
                if (!f_10F7_2548(1, fd_3E1D_A180[i], fd_3E1D_A569[i])) {
                    DeadAntHere(fd_3E1D_A180[i], fd_3E1D_A569[i], 1);
                    fd_3E1D_AD3B[i] = 0;
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
extern int far fd_50F6_1040;

void far SubtractFood(void)
{
    int row, column;

    for (row = 0; row < 0x80; row++)
        for (column = 0; column < 0x40; column++)
            if (IsItFood(MapA[row][column]) == 1)
                MapA[row][column] = SRand16();
    fd_50F6_1040 = 0;
}

extern int far fd_50F6_0D70;

void far f_015B_01B8(int value)
{
    fd_50F6_0D70 = value;
}

static int g_1960[5] = { 0x109, 0x10a, 0x10c, 0x10d, 0x10b };

extern int far fd_3D57_07C8;
extern int far fd_50F6_035C;
void far SetYardMode(int newMode);
extern int far fd_50F6_032E;
void far SetMapPlane(int plane);
extern void far f_00F8_00D8(void);
extern void _fastcall win_MakeObjSelected(int obj);
extern void _fastcall win_MakeGroupUnselected(int win, int group);

void far SetMapModeAnt(int mode)
{
    if (fd_3D57_07C8 == mode && mode >= 4 && mode <= 8)
        mode = 1;
    switch (mode) {
    case 0:
        fd_3D57_07C8 = mode;
        SetYardMode(fd_50F6_035C);
        break;
    case 4:
    case 5:
    case 6:
    case 7:
    case 8:
        if (fd_50F6_032E != 1)
            SetMapPlane(1);
    case 1:
    case 2:
    case 3:
        fd_3D57_07C8 = mode;
        f_00F8_00D8();
        if (mode >= 4 && mode <= 8)
            win_MakeObjSelected(g_1960[mode - 4]);
        else
            win_MakeGroupUnselected(0x100, 2);
        break;
    }
}

static int g_1984[4] = { 0x1908, 0x1908, 0x1909, 0x190a };

extern int far fd_50F6_0332;
extern int far WinPrintf(char far *format, ...);
extern void _fastcall win_LockWin(int win);
extern void _fastcall win_MakeObjInvisible(int obj);
extern int near g_3DB2;
extern void _fastcall win_UnlockWin(int win);
extern void far f_00F8_0002(void);
extern void _fastcall win_MakeObjVisible(int obj);
extern void _fastcall win_SetObjBitmap(int obj, int bitmap);
extern int _fastcall win_IsWinOpen(int win);
extern void far f_1E57_0DAA(void);
extern void far f_1E57_0174(int win);
extern void _fastcall win_DrawObjectNum(int objNum);
extern void far f_1E57_0EB9(void);
extern void far win_Swap(int from, int to);
extern void far DrawYard(void);

void far SetYardMode(int newMode)
{
    if (newMode == 4) {
        SetMapPlane(fd_50F6_0332);
    } else {
        WinPrintf("\nYardmode=%d, newMode=%d", fd_50F6_035C, newMode);
        if (newMode != 0 && newMode != 1) {
            fd_50F6_035C = newMode;
            win_LockWin(0x1900);
            win_MakeObjInvisible(0x1903);
            if (g_3DB2 != 0x140)
                win_MakeObjInvisible(0x190f);
            win_UnlockWin(0x1900);
            f_00F8_0002();
        } else {
            fd_50F6_035C = newMode;
            win_LockWin(0x1900);
            win_MakeObjVisible(0x1903);
            if (g_3DB2 != 0x140)
                win_MakeObjVisible(0x190f);
            win_UnlockWin(0x1900);
            f_00F8_0002();
            win_SetObjBitmap(0x1903, newMode + 7000);
            if (win_IsWinOpen(0x1900)) {
                f_1E57_0DAA();
                f_1E57_0174(0x1900);
                win_DrawObjectNum(0x1903);
                if (g_3DB2 != 0x140)
                    win_DrawObjectNum(0x190f);
                f_1E57_0EB9();
            }
        }
        if (!win_IsWinOpen(0x1900) && win_IsWinOpen(0x100))
            win_Swap(0x100, 0x1900);
        f_1E57_0DAA();
        f_1E57_0174(0x1900);
        win_MakeObjSelected(g_1984[fd_50F6_035C]);
        f_1E57_0EB9();
        DrawYard();
    }
    f_00F8_00D8();
}

typedef struct {
    int x;
    int y;
} Point;

extern int far fd_50F6_0FFA;
extern int far fd_50F6_0FB6;
extern void far f_0250_006E(int left, int top, int right, int bottom);
extern int far fd_50F6_0F36;
extern void far f_0250_0FC4(int x, int y);
extern void far f_0250_0E9D(void);
extern void far f_0250_0ED2(void);
extern Point far fd_50F6_07CA;
extern Point far fd_50F6_07BC;
extern void far f_1E57_0362(void);

void far SetMapPlaneLocation(int plane, int x, int y)
{
    int win, obj;

    if (plane != 0)
        f_0250_006E(0, 0, fd_50F6_0FB6, fd_50F6_0FFA);
    else
        fd_50F6_0332 = fd_50F6_032E;
    fd_50F6_032E = plane;
    if (plane == 1)
        fd_50F6_0F36 = 0x80 - fd_50F6_0FB6;
    else
        fd_50F6_0F36 = 0x40 - fd_50F6_0FB6;
    if (fd_50F6_032E != 0) {
        f_0250_0FC4(x, y);
        f_0250_0E9D();
        f_0250_0ED2();
    } else {
        fd_50F6_07BC = fd_50F6_07CA;
    }
    SetMapModeAnt(fd_50F6_032E);
    win = obj = 0;
    switch (fd_50F6_032E) {
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
        f_1E57_0174(0);
        win_MakeObjSelected(win);
        f_1E57_0362();
    }
    if (obj) {
        f_1E57_0174(0x100);
        win_MakeObjSelected(obj);
        win_MakeGroupUnselected(0x100, 2);
        f_1E57_0362();
    }
}

extern int far fd_50F6_0AA6;

void far GotoMapPoint(int plane, int x, int y)
{
    if (fd_50F6_032E == plane && plane > 0) {
        f_0250_0FC4(x, y);
        fd_50F6_0AA6 = 0;
    } else {
        SetMapPlaneLocation(plane, x, y);
    }
}

extern int far fd_3D57_07C0[];
extern Point far fd_50F6_0596;
extern Point far fd_50F6_06A6;
extern Point far fd_50F6_072E;

void far SetMapPlane(int plane)
{
    Point pt;

    if (plane != 0)
        f_0250_006E(0, 0, fd_50F6_0FB6, fd_50F6_0FFA);
    else
        fd_50F6_0332 = fd_50F6_032E;
    fd_50F6_032E = plane;
    if (plane == 1)
        fd_50F6_0F36 = 0x80 - fd_50F6_0FB6;
    else
        fd_50F6_0F36 = 0x40 - fd_50F6_0FB6;
    f_015B_01B8(fd_3D57_07C0[fd_50F6_032E]);
    switch (fd_50F6_032E) {
    case 0:
        pt = fd_50F6_07BC;
        break;
    case 1:
        pt = fd_50F6_0596;
        break;
    case 2:
        pt = fd_50F6_06A6;
        break;
    case 3:
        pt = fd_50F6_072E;
        break;
    }
    SetMapPlaneLocation(plane, pt.x, pt.y);
    if (fd_50F6_032E != 0)
        f_0250_0FC4(pt.x, pt.y);
    SetMapModeAnt(fd_50F6_032E);
    f_0250_0E9D();
}

extern int far fd_50F6_1074;
extern int far MePlane;
extern int far MeLocY;
extern int far MeLocX;

void far CenterAnt(void)
{
    fd_50F6_1074 = 1;
    if (MePlane != fd_50F6_032E)
        SetMapPlane(MePlane);
    f_0250_0FC4(MeLocX, MeLocY);
}

extern int far fd_50F6_0EAC;
extern void far myBeginSound(int a, int b, int c);

void far GotoMyAnt(void)
{
    fd_50F6_1074 = 1;
    if (fd_50F6_0EAC == 3)
        myBeginSound(1, 0, 0x7e);
    else
        GotoMapPoint(MePlane, MeLocX, MeLocY);
}

extern int far fd_50F6_0F0C;
extern int far fd_50F6_0F34;
extern int far fd_50F6_0F12;

void far GotoSpider(void)
{
    if (fd_50F6_0F0C == 0)
        myBeginSound(1, 0, 0x7e);
    else
        GotoMapPoint(1, fd_50F6_0F12 >> 4, fd_50F6_0F34 >> 4);
}

extern Point far fd_3D57_02B4;

void far f_015B_073E(void)
{
    GotoMapPoint(2, fd_3D57_02B4.x, fd_3D57_02B4.y);
}

extern Point far fd_3D57_02B8;

void far f_015B_075F(void)
{
    GotoMapPoint(3, fd_3D57_02B8.x, fd_3D57_02B8.y);
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

extern int far fd_50F6_03E2;
extern int far fd_50F6_0330;
extern void far PictStrnDialog(int a, int b, int c);
extern unsigned char far fd_3D57_00A4[][16];
extern int far fd_50F6_04C2;
extern int far fd_3D57_0C24;
extern void far f_00DF_00B1(int id, int arg);
extern void far o12_384C_100A(void);
extern int far fd_50F6_0354;
extern int far fd_50F6_07C8;
extern int far fd_50F6_0850;
extern int far fd_50F6_06AA;
extern int far fd_50F6_073A;
extern void far f_00F8_0395(void);
extern int far fd_3E1D_0000[][12];
extern unsigned char far fd_3D57_0164[][16];
extern void far RandWorld(unsigned seed, int blackSize, int redSize, int x, int y);
extern int far HealthR;

void far f_015B_0798(void)
{
    int x, y;

    y = fd_50F6_07BC.y;
    x = fd_50F6_07BC.x;
    if (x == fd_50F6_07CA.x && fd_50F6_07CA.y == y)
        return;
    if (fd_50F6_0EAC != 2) {
        myBeginSound(1, 0, 0x7e);
        PictStrnDialog(0, 0x2710, 1);
    } else if (fd_50F6_03E2 <= 1 && fd_50F6_0330 <= 1) {
        myBeginSound(1, 0, 0x7e);
        PictStrnDialog(0, 0x2712, 1);
    } else if (fd_3D57_00A4[x][y] < 1 && (fd_50F6_04C2 != 0x40 || fd_3D57_0C24 != 0)) {
        myBeginSound(1, 0, 0x7e);
        PictStrnDialog(0, 0x2714, 1);
    } else {
        f_00DF_00B1(0x2afa, 0x7e);
        fd_50F6_07CA.x = x;
        fd_50F6_07CA.y = y;
        o12_384C_100A();
        fd_50F6_0354 = 1;
        fd_50F6_07C8 = 0;
        fd_50F6_0850 = 0;
        fd_50F6_06AA = 0;
        fd_50F6_073A = 0;
        f_00F8_0395();
        fd_3D57_0C24 = 1;
        RandWorld(fd_3E1D_0000[y][x], fd_3D57_00A4[x][y], fd_3D57_0164[x][y], x, y);
        if (fd_3D57_0164[x][y] == 0)
            HealthR = 0;
        if ((x << 4) + y > 0x24)
            PictStrnDialog(0, 0x2716, 0);
        else
            PictStrnDialog(0, 0x2717, 0);
    }
}
