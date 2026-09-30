/* Overlay section S05, code frame 35F5: editor tool and ant menus (Win16 ANTEDIT_MODULE run). */

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

extern int far fd_3D57_07BE;
extern int far win_DoProxMenu();
extern void far clip_SetWin(int win);
extern void _fastcall win_SetObjSelectedState(int obj, int state);
extern void far f_0250_0E81(void);

void far EditScentMenu(void)
{
    int r;

    r = win_DoProxMenu(0x600, fd_3D57_07BE + 1);
    if (r == -1)
        return;
    fd_3D57_07BE = r - 1;
    clip_SetWin(0);
    win_SetObjSelectedState(0x10, fd_3D57_07BE != -1);
    f_0250_0E81();
}

static int toolMenus[8] = { -1, 0xc00, 0xf00, 0x1000, 0x1100, 0xd00, 0xe00, -1 };

extern void _fastcall win_GetObjRect(int obj, struct Rect far *rect);
extern int far fd_50F6_0EAC;
extern int far fd_50F6_104C;
void far SetExpTool(int tool);
extern int far fd_50F6_0496;
extern int far fd_50F6_04C2;
extern int far MeLocY;
extern int far MeLocX;
extern int far MePlane;
extern void far ClearMyLife(int plane, int x, int y, int type, int dir);
extern int far fd_50F6_0A06;
extern void far InitSpider(void);
extern void far SetEditWinTitle();
extern void far myBeginSound(int sound, int a, int b);
extern int far DoExpMenu(int x, int y);
extern void far WinPrintf(char far *fmt, ...);
extern void far InitYelloAnt(void);
extern int far fd_50F6_032E;
extern void far SetMyLife(int plane, int x, int y, int type, int dir, int code);
extern void far f_00DF_00B1(int id, int arg);
extern void far clip_Push(void);
extern void _fastcall win_DrawBitMapAtObjNum(int obj, int id);
extern void far clip_Pop(void);
extern int _fastcall win_IsWinOpen(int win);

void far EditToolsMenu(void)
{
    struct Rect r;
    int item;

    win_GetObjRect(7, &r);
    switch (fd_50F6_0EAC) {
    case 1:
        if (win_DoProxMenu(0xa00, -1, r.right + 2, r.top) < 0)
            break;
        SetExpTool(fd_50F6_104C);
        fd_50F6_0EAC = 3;
        ClearMyLife(MePlane, MeLocX, MeLocY, fd_50F6_04C2, fd_50F6_0496);
        fd_50F6_0A06 = 2;
        InitSpider();
        SetEditWinTitle(0, 0);
        myBeginSound(2, 0, 0x7e);
        break;
    case 2:
        win_DoProxMenu(0xb00, -1, r.right + 2, r.top);
        break;
    case 3:
        WinPrintf("\nITEM=%x, startTool=%x", item = DoExpMenu(r.right + 2, r.top), 7);
        if (item == -1)
            break;
        if (item == 7) {
            fd_50F6_0EAC = 1;
            InitYelloAnt();
            if (fd_50F6_032E == 1)
                SetMyLife(MePlane, MeLocX, MeLocY, fd_50F6_04C2, fd_50F6_0496, 0xff);
            SetEditWinTitle(0, 0);
            f_00DF_00B1(0x2afb, 0x7e);
        }
        SetExpTool(item);
        clip_Push();
        clip_SetWin(0);
        win_DrawBitMapAtObjNum(7, fd_50F6_104C + 0x13ec);
        clip_Pop();
        if (win_IsWinOpen(0x100)) {
            clip_Push();
            clip_SetWin(0x100);
            win_DrawBitMapAtObjNum(0x117, fd_50F6_104C + 0x13ec);
            clip_Pop();
        }
        break;
    }
}

extern unsigned char far LifeA[128][64];
extern unsigned char far LifeB[64][64];
extern unsigned char far LifeR[64][64];
extern int far fd_50F6_0508[2];
extern int far fd_55B3_19BE;
extern int far fd_50F6_110C[2];
extern int far fd_55B3_19C0;
extern void _fastcall win_GetObjSize(int obj, struct Pt far *size);
extern int near g_3DB2;
extern int near g_3DB4;
extern void far win_Open();
extern char far * far * far fd_50F6_106E;
extern char far * far * far fd_50F6_1078;
extern void far f_24AB_02AD(int font);
extern void far win_PrintfAtObj(int obj, char far *format, ...);
extern int far FindInAList(int x, int y);
extern unsigned char far AlistM[];
extern int far FindInBList(int x, int y, int t);
extern unsigned char far BlistM[];
extern int far FindInRList(int x, int y, int t);
extern unsigned char far RlistM[];
extern char far * far * far fd_50F6_1086;
extern char far * far * far fd_50F6_1096;
extern void far f_1FD2_057F(void);
extern int far f_1FD2_0598(void);
extern void far f_1FD2_05EF(void);
extern void _fastcall win_Close(int win);

/* SCAFFOLD BEGIN: MagnifyMenu (examine window, Win16 win_DrawExamineWindow LOW) best draft: 2 bytes short; the original indexes fd_50F6_1086[k] via mov bx,di;shl bx,1;shl bx,1;les si (k kept in DI), MSC here shifts DI in place and uses les bx */
int far MagnifyMenu(int x, int y, int plane)
{
    int k;
    int caste;
    int t;
    char far *name;
    struct Pt size;
    int wx;
    int wy;
    int i;

    if (plane <= 1)
        t = LifeA[x][y];
    else if (plane == 2)
        t = LifeB[x][y];
    else
        t = LifeR[x][y];
    if (t == 0)
        return -1;
    wx = (x - fd_50F6_0508[0] + 1) * fd_55B3_19BE + fd_50F6_110C[0];
    wy = (y - fd_50F6_0508[1] - 1) * fd_55B3_19C0 + fd_50F6_110C[1];
    win_GetObjSize(0x1d00, &size);
    if (size.x + wx > g_3DB2)
        wx -= fd_55B3_19BE + size.x;
    if (size.y + wy > g_3DB4)
        wy = g_3DB4 - size.y;
    win_Open(0x1d00, wx, wy);
    caste = (t & 0x78) >> 3;
    if (caste == 0)
        name = fd_50F6_106E[t & 7];
    else
        name = fd_50F6_1078[caste];
    f_24AB_02AD(2);
    win_PrintfAtObj(0x1d02, name);
    switch (plane) {
    case 1:
        if ((i = FindInAList(x, y)) >= 0)
            k = AlistM[i];
        else
            k = 0;
        break;
    case 2:
        if ((i = FindInBList(x, y, LifeB[x][y])) >= 0)
            k = BlistM[i];
        else
            k = 0;
        break;
    case 3:
        if ((i = FindInRList(x, y, LifeR[x][y])) >= 0)
            k = RlistM[i];
        else
            k = 0;
        break;
    }
    win_PrintfAtObj(0x1d03, fd_50F6_1086[k]);
    win_PrintfAtObj(0x1d04, fd_50F6_1096[caste]);
    f_24AB_02AD(0);
    f_1FD2_057F();
    while (win_IsWinOpen(0x1d00) && f_1FD2_0598())
        ;
    f_1FD2_05EF();
    win_Close(0x1d00);
    WinPrintf("tileNum=%d", t);
    return t;
}
/* SCAFFOLD END */

extern int far fd_3D57_0C24;
extern int far fd_50F6_10E0;
extern int far fd_50F6_10DE;
extern void far YellowCommand(int cmd);

int far AntMenu(struct Event far *ev)
{
    static char antCmds[4] = { 8, 9, 0, 0 };
    static char nestCmds[6] = { 1, 2, 4, 5, 6, 0 };
    static char spiderCmds[4] = { 10, 11, 6, 0 };
    int n;
    int r;
    int cmd;
    int x, y;

    n = 5;
    if (fd_50F6_04C2 == 0x40 && fd_3D57_0C24 == 0)
        n = 2;
    /* Dead menu-placement test (x, y unused).  MSC eliminates the arithmetic but keeps
       the ES segment loads, the first compare of the || and the n = 5/2 setup; only
       those survive in the original, so the exact expressions are a hypothesis. */
    x = fd_50F6_0508[0] + fd_50F6_10E0;
    if (x < MeLocX)
        x = MeLocX;
    if (fd_50F6_0508[1] + 2 > MeLocY || MeLocY - fd_50F6_10DE < n)
        y = x;
    WinPrintf("ANTMENU");
    if (fd_50F6_0A06 == 0) {
        if (fd_50F6_04C2 == 0x40 && fd_3D57_0C24 == 0)
            r = win_DoProxMenu(0x800, -1, ev->h, ev->v);
        else
            r = win_DoProxMenu(0x700, -1, ev->h, ev->v);
    } else if (fd_50F6_0A06 == 1)
        r = win_DoProxMenu(0x2000, -1, ev->h, ev->v);
    else
        r = -1;
    if (r >= 0) {
        cmd = r;
        if (fd_50F6_0A06 == 1) {
            cmd = spiderCmds[cmd];
            if (cmd == 11 && (*(char far *)0x417L & 8))
                cmd = 12;
        } else if (fd_50F6_04C2 == 0x40 && fd_3D57_0C24 == 0)
            cmd = antCmds[cmd];
        else {
            cmd = nestCmds[cmd];
            if (cmd == 2 && (*(char far *)0x417L & 3))
                cmd = 3;
        }
        YellowCommand(cmd);
    }
    return r;
}

void far SetExpTool(int tool)
{
    fd_50F6_104C = tool;
}

extern int far fd_50F6_0FFE;
extern void far f_0250_0E9D(void);

void far DoWarnSetB(struct Event far *ev)
{
    struct Rect r;

    win_GetObjRect(0x12, &r);
    fd_50F6_0FFE = (r.bottom - ev->v) * 100 / (r.bottom - r.top);
    f_0250_0E9D();
}

extern int far fd_50F6_0FBA;

void far DoHealthSetY(struct Event far *ev)
{
    struct Rect r;

    win_GetObjRect(0x11, &r);
    fd_50F6_0FBA = (r.bottom - ev->v) * 100 / (r.bottom - r.top);
    f_0250_0E9D();
}

extern int _fastcall win_IsWinInFront(int win);
extern void far OpenMapYard(void);
extern void far OpenEditWindow(void);

void far DoTab(void)
{
    if (win_IsWinInFront(0))
        OpenMapYard();
    else
        OpenEditWindow();
}
