extern int idscan_pad0;
extern int idscan_pad1;
extern int idscan_pad2;
extern int idscan_pad3;
extern int idscan_pad4;
extern int idscan_pad5;
extern int idscan_pad6;
extern int idscan_pad7;
/* Overlay section S15, code frame 384C: start-up and shut-down helpers
   (demo expiry, monochrome patterns, disk reset, fatal exit, quit dialog,
   default windows, new game). */

typedef char far * far *Handle;

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

struct Rect {
    int left;
    int top;
    int right;
    int bottom;
};

void far o15_384C_0152(char far *msg, int flag);

void far o15_384C_0000(void)
{
    o15_384C_0152("SimAnt IBM DEMO version has expired.  Please get an update.", 0);
}

extern Handle far db_LoadObject(int object, int kind);
extern void far Punt(char far *format, ...);
extern unsigned char near g_8EC0[];
extern void far db_PurgeObject(int object, int kind);
extern unsigned char near g_8ED8[];

void far LoadMonoPats(void)
{
    Handle h;
    unsigned char far *src;
    unsigned char far *dst;
    int n;
    int i;

    h = db_LoadObject(0x2710, 0x16);
    if (h == 0 || **(int far * far *)h != 0x300)
        Punt("Cannot load monochrome patterns.");
    src = (unsigned char far *)*h + 2;
    dst = g_8EC0;
    n = 0x18;
    for (i = 0; i < n; i++)
        *dst++ = ~*src++;
    db_PurgeObject(0x2710, 0x16);
    h = db_LoadObject(0x271a, 0x16);
    if (h == 0)
        Punt("Cannot load monochrome patterns.");
    n = (*h)[1] << 3;
    src = (unsigned char far *)*h + 2;
    dst = g_8ED8;
    for (i = 0; i < n; i++)
        *dst++ = ~*src++;
    db_PurgeObject(0x271a, 0x16);
}

void far o15_384C_0125(void)
{
    int drive;

    for (drive = 0; drive < 12; drive++) {
        _asm {
            mov dl, byte ptr drive
            or dl, 80h
            mov ah, 1
            int 13h
            jc skip
            mov ah, 0
            int 13h
        skip:
        }
    }
}

static int g_2BD4 = 1;

extern void far f_171C_0676(int flag);
extern void far f_277D_000B(char far *msg);
extern void far f_171C_030C(char far *msg);
extern int far fd_55B3_610A;
extern void far f_277E_0154(void);
extern void far f_1C62_00A1(void);
extern void far f_1C62_0090(void);
extern int far puts(char far *s);
extern void far pascal f_00DE_000A(int code);
extern void far exit(int code);

void far o15_384C_0152(char far *msg, int flag)
{
    f_171C_0676(0);
    switch (g_2BD4++) {
    case 0:
        g_2BD4 = 1;
        f_277D_000B(msg);
    case 1:
        g_2BD4 = 2;
        if (flag)
            f_171C_030C(msg);
    case 2:
        g_2BD4 = 3;
        if (fd_55B3_610A)
            f_277E_0154();
        f_1C62_00A1();
        f_1C62_0090();
        puts(msg);
    }
    if (flag)
        f_00DE_000A(1);
    exit(0);
}

extern int far fd_3D57_02C2;
int far o15_384C_0239(int which);
extern int far o09_35F5_0188(int flag);

int far MenuQuit(void)
{
    int r;

    if (fd_3D57_02C2) {
        do {
            r = o15_384C_0239(1);
            if (r == 2)
                return 0;
            if (r != 1)
                break;
        } while (o09_35F5_0188(0) == 0);
    }
    o15_384C_0152("SimAnt was brought to you by the people at MAXIS.  Thank you for playing.", 0);
}

extern void far win_Open(int win);
extern Handle far f_1A53_00F0(int object, int kind, int type);
extern char far * far f_171C_1B84(Handle h);
extern int near g_3DB2;
extern void far f_24AB_02AD(int font);
extern char near g_5A97;
extern void _fastcall win_GetObjRect(int obj, struct Rect far *rect);
extern void (far * near g_9128)(int a, int b, int c);
extern void far f_1CE2_044D(struct Rect far *rect, int width);
extern void _fastcall win_SetColorFromObjNum(int obj);
extern void _fastcall win_PrintTextInRect(int first, char far *text, struct Rect far *rect);
extern int far f_1F58_0038(void);
extern int far f_1F58_0090(void);
extern int _fastcall win_GetEvent(struct Event far *ev);
extern Handle far f_171C_1BBA(Handle h);
extern void far db_ReleaseHandle(Handle handle);
extern void _fastcall win_Close(int win);

int far o15_384C_0239(int which)
{
    struct Event ev;
    struct Rect r;
    Handle h;
    char far *text;
    int result;

    win_Open(0x2100);
    h = f_1A53_00F0((0x41 - which) * 2, 10, 1);
    text = f_171C_1B84(h);
    f_24AB_02AD(g_3DB2 == 0x140 ? 2 : 4);
    if (g_5A97 & 1) {
        win_GetObjRect(0x2100, &r);
        (*g_9128)(0, 0, 0);
        f_1CE2_044D(&r, 2);
    }
    win_GetObjRect(0x2101, &r);
    win_SetColorFromObjNum(0x2101);
    win_PrintTextInRect(0, text, &r);
    f_24AB_02AD(0);
    for (;;) {
        if (f_1F58_0038()) {
            switch (f_1F58_0090()) {
            case 0x0d:
            case 'D':
            case 'd':
                result = 0;
                goto done;
            case 'S':
            case 's':
                result = 1;
                goto done;
            case 0x1b:
            case 'C':
            case 'c':
                result = 2;
                goto done;
            }
        }
        if (win_GetEvent(&ev)) {
            switch (ev.code) {
            case 0x2103:
                result = 0;
                goto done;
            case 0x2104:
                result = 1;
                goto done;
            case 0x2105:
                result = 2;
                goto done;
            }
        }
    }
done:
    f_171C_1BBA(h);
    db_ReleaseHandle(h);
    win_Close(0x2100);
    return result;
}

extern void far OpenCasteWindow(void);
extern void far OpenModeWindow(void);
extern void far SetEditWinTitle(char far *title);
extern int far MapPlane;
extern void far f_015B_053C(int plane);
extern int _fastcall win_IsWinOpen(int win);
extern void far YardToMap(void);
extern void far SetMapTitle(void);
extern void far OpenEditWindow(void);

void far SetDefaultWindows(void)
{
    OpenCasteWindow();
    OpenModeWindow();
    SetEditWinTitle(0L);
    f_015B_053C(MapPlane);
    if (!win_IsWinOpen(0x100))
        YardToMap();
    SetMapTitle();
    OpenEditWindow();
}

extern int far DoScenario(int flag);
extern int far o09_35F5_0000(int a, int b);
extern int far fd_50F6_0EAC;
extern int far fd_50F6_105E;
extern void far EndLifeTransferMode(void);
extern void far EndTargetMode(void);
extern void far SetDefaultWindPrompt(int);
extern int far fd_50F6_0354;
extern int far fd_50F6_07C8;
extern void far RandYard(void);
extern int far MePlane;
extern int far WinPrintf(char far *format, ...);
extern int far fd_3D57_07A4;
extern int far fd_3D57_07A6;
extern int far f_22BF_0A65(void);
extern void far o26_39C7_0000(void);
extern int far MeLocY;
extern int far MeLocX;
extern void far CenterEdit(int x, int y);
extern void far UpdateEdit(void);

int far NewGame(int flag)
{
    int r;

    fd_3D57_02C2 = 0;
    for (;;) {
        r = DoScenario(flag);
        if (r == 0x205)
            return -1;
        if (r == 0x207) {
            if (o09_35F5_0000(0, 0) == 0)
                continue;
            r = 1;
        } else {
            switch (r) {
            case 0x202:
                r = 1;
                break;
            case 0x203:
                r = 2;
                break;
            case 0x204:
                r = 3;
                break;
            case 0x206:
                r = 0;
                break;
            }
            if (r >= 0 && r < 4) {
                fd_50F6_0EAC = r;
                if (fd_50F6_105E == 10)
                    EndLifeTransferMode();
                else if (fd_50F6_105E == 11)
                    EndTargetMode();
                SetDefaultWindPrompt(1);
                SetEditWinTitle(0L);
                fd_50F6_0354 = 1;
                fd_50F6_07C8 = 0;
                RandYard();
                WinPrintf("MePLane=%d", MePlane);
                f_015B_053C(MePlane);
                if (fd_50F6_0EAC == 0) {
                    fd_3D57_07A4 = 1;
                    fd_3D57_07A6 = 0;
                    if (flag == 0)
                        win_Open(0);
                }
            }
        }
        break;
    }
    SetDefaultWindows();
    f_015B_053C(MePlane);
    if (r == 0 && !f_22BF_0A65())
        o26_39C7_0000();
    CenterEdit(MeLocX, MeLocY);
    UpdateEdit();
    fd_3D57_02C2 = 0;
    return r;
}
