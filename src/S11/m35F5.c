/* Overlay section S11, code frame 35F5: menu entry states (Win16 SetMenuEntries twin), pause
 * switch (Win16 PauseGame/SetPause twins) and the menu command dispatcher ProcMenu. */

extern int far fd_3D57_07CC;
extern void far f_1FD2_061E(int id, int state);
extern int far fd_50F6_047E;
extern void far f_1FD2_0135(int id, char far *text);
extern int far fd_3D57_07A8[];

void far o11_35F5_0000(void)
{
    int item;
    int i;

    for (item = 0x43; item <= 0x46; item++)
        f_1FD2_061E(item - 1, (fd_3D57_07CC == item - 0x43) ? 0x10 : 0x20);
    f_1FD2_0135(0x41, fd_50F6_047E ? " Unpause" : " Pause");
    for (i = 0, item = 0x31; item <= 0x36; i++, item++)
        f_1FD2_061E(item - 1, fd_3D57_07A8[i] ? 0x10 : 0x20);
}

void far o11_35F5_009E(int value);

void far o11_35F5_0088(int value)
{
    o11_35F5_009E(value);
}

extern int far fd_50F6_105E;
extern void far EndLifeTransferMode(void);
extern void far EndTargetMode(void);
extern char far * far * far fd_50F6_034C;
extern void far f_15D9_009C(void far *, long, int);
extern void far clip_SetWin(int win);
extern void _fastcall win_SetObjSelectedState(int obj, int state);
extern void far f_1E57_0362(void);

void far o11_35F5_009E(int value)
{
    if (value == 0) {
        if (fd_50F6_105E == 10)
            EndLifeTransferMode();
        else if (fd_50F6_105E == 11)
            EndTargetMode();
    }
    fd_50F6_047E = value;
    if (value != 0) {
        if (fd_50F6_105E == -1)
            f_15D9_009C(fd_50F6_034C[2], -2L, 1);
        else if (fd_50F6_105E == 10)
            f_15D9_009C(fd_50F6_034C[3], -2L, 1);
        else if (fd_50F6_105E == 11)
            f_15D9_009C(fd_50F6_034C[17], -2L, 1);
    } else
        f_15D9_009C(0L, -2L, 1);
    clip_SetWin(0);
    win_SetObjSelectedState(0xf, value);
    f_1E57_0362();
    o11_35F5_0000();
}

struct Event {
    int what;
    int where[2];
    int when[2];
    int modifiers;
    int message;
};

extern void far o16_384C_01E1(void);
extern void far f_00DF_00B1(int id, int arg);
extern int far o15_384C_03C6(int a);
extern int far fd_55B3_2CBC;
extern void far OpenEditWindow(void);
extern void far OpenMapYard(void);
extern void far OpenModeWindow(void);
extern void far OpenCasteWindow(void);
extern void far OpenHistoryWindow(void);
extern void far OpenInfoWindow(void);
extern void far ScoreDialog(void);
extern int far fd_50F6_035C;
extern void far SetYardMode(int newMode);
extern int far fd_50F6_032E;
extern void far SetMapPlane(int plane);
extern int _fastcall win_IsWinOpen(int win);
extern void far f_00F8_04C7(void);
extern void far StopSong(void);

void far ProcMenu(struct Event far *ev)
{
    int item;
    int n;

    item = ev->message & 0xff;
    switch (item) {
    
    case 1:
        o16_384C_01E1();
        break;
    case 3:
        f_00DF_00B1(0x2711, 0x7e);
        o15_384C_03C6(0);
        break;
    case 4:
    case 5:
    case 6:
    case 8:
        fd_55B3_2CBC = item;
        break;
    case 0x11:
        OpenEditWindow();
        break;
    case 0x12:
        OpenMapYard();
        break;
    case 0x13:
        OpenModeWindow();
        break;
    case 0x14:
        OpenCasteWindow();
        break;
    case 0x15:
        OpenHistoryWindow();
        break;
    case 0x16:
        OpenInfoWindow();
        break;
    case 0x17:
        ScoreDialog();
        break;
    case 0x21:
    case 0x22:
    case 0x23:
    case 0x24:
        n = item - 0x21;
        if (n != fd_50F6_035C)
            SetYardMode(n);
        if (fd_50F6_032E != 0)
            SetMapPlane(0);
        if (!win_IsWinOpen(0x1900))
            f_00F8_04C7();
        break;
    case 0x26:
        SetMapPlane(1);
        break;
    case 0x27:
        SetMapPlane(2);
        break;
    case 0x28:
        SetMapPlane(3);
        break;
    case 0x32:
        StopSong();
    toggle:
        fd_3D57_07A8[item - 0x31] = !fd_3D57_07A8[item - 0x31];
        o11_35F5_0000();
        break;
    case 0x41:
        fd_50F6_047E ^= 1;
        o11_35F5_009E(fd_50F6_047E);
        break;
    case 0x43:
        n = 0;
        goto speed;
    case 0x44:
        n = 1;
        goto speed;
    case 0x45:
        n = 2;
        goto speed;
    case 0x46:
        n = 3;
    speed:
        fd_3D57_07CC = n;
        o11_35F5_0000();
        break;
    default:
        if (item >= 0x31 && item <= 0x36)
            goto toggle;
        break;
    }
}
