/* Overlay section S12, code frame 384C: map window (map functions, map image generation). */

#include <string.h>

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

static int g_298E = 0;
int fd_55B3_2990 = 0;
static int g_2992 = -1;
static int g_2994 = 0;
int g_2996 = 0;
static int g_2998 = -1;
long fd_55B3_299A = 0;
long fd_55B3_299E = 0;
int fd_55B3_29A2 = 0;
static int g_29A4 = 0;

void far DeinitMapFunctions(void)
{
}

extern long far f_171C_1750(void);
extern long far f_171C_1772(void);
extern void far WinPrintf(char far *format, ...);
extern char far * far * far f_171C_1A9E(long size, int kind, char far *name);
extern char far * far * far fd_50F6_10E2;
extern char near g_5A97;
extern int far fd_50F6_3856;
extern int far fd_50F6_3858;
extern void (far * far fd_50F6_38B8)();
extern void (far * far fd_50F6_38BC)();
extern void far o00_3126_0000();
extern void far o00_3126_0137();
extern void far o03_3253_0008();
extern void far o01_328E_000A();
extern void far o01_328E_009D();
extern void far o00_3126_026A();
extern void far o00_3126_03A9();

void far InitMapFunctions(void)
{
    WinPrintf("\nFREE+SOFT AT INITMAP=%ld", f_171C_1750() + f_171C_1772());
    fd_50F6_10E2 = f_171C_1A9E(0x2000L, 1, "Generated buffer window");
    switch (g_5A97) {
    case 0:
    case 8:
        fd_50F6_3856 = 4;
        fd_50F6_3858 = 4;
        fd_50F6_38B8 = o00_3126_0000;
        fd_50F6_38BC = o00_3126_0137;
        break;
    case 2:
        fd_50F6_3856 = 2;
        fd_50F6_3858 = 2;
        fd_50F6_38B8 = o03_3253_0008;
        fd_50F6_38BC = o03_3253_0008;
        break;
    case 3:
    case 5:
    case 7:
        fd_50F6_3856 = 4;
        fd_50F6_3858 = 4;
        fd_50F6_38B8 = o01_328E_000A;
        fd_50F6_38BC = o01_328E_009D;
        break;
    case 4:
        fd_50F6_3856 = 2;
        fd_50F6_3858 = 2;
        fd_50F6_38B8 = o00_3126_026A;
        fd_50F6_38BC = o00_3126_03A9;
        break;
    }
}

extern void far MapAreaEvent(struct Event far *ev);
extern void far MapToYard(void);
extern void far ClearMapScentButtons(void);
extern void far SetMapPlane(int plane);
extern void _fastcall f_20E8_0725(int win);
extern void far SetMapModeAnt(int mode);
extern void far OpenModeWindow(void);
void far o12_384C_12D3(struct Event far *ev);
extern void far OpenCasteWindow(void);
extern void far MysteryButton(void);
extern void far OpenHistoryWindow(void);
extern void far ScoreDialog(void);
extern void far OpenInfoWindow(void);
extern int far fd_50F6_1074;
extern void far DoWinHelp(int win);
extern void far MapToolsMenu(void);
extern void far DrawCastePopUp(void);

void far ProcMapEvent(struct Event far *ev)
{
    switch (ev->code) {
    case 0x102: MapAreaEvent(ev); break;
    case 0x105: MapToYard(); break;
    case 0x106: ClearMapScentButtons(); SetMapPlane(1); break;
    case 0x107: ClearMapScentButtons(); SetMapPlane(2); break;
    case 0x108: ClearMapScentButtons(); SetMapPlane(3); f_20E8_0725(0x100); break;
    case 0x109: SetMapModeAnt(4); f_20E8_0725(0x100); break;
    case 0x10a: SetMapModeAnt(5); break;
    case 0x10b: SetMapModeAnt(8); break;
    case 0x10c: SetMapModeAnt(6); break;
    case 0x10d: SetMapModeAnt(7); break;
    case 0x10e: g_2994 = !g_2994; break;
    case 0x10f: OpenModeWindow(); break;
    case 0x110: o12_384C_12D3(ev); break;
    case 0x111: OpenCasteWindow(); break;
    case 0x112: MysteryButton(); break;
    case 0x113: OpenHistoryWindow(); break;
    case 0x114: ScoreDialog(); break;
    case 0x115: OpenInfoWindow(); break;
    case 0x116: fd_50F6_1074 = 1; DoWinHelp(0x103); break;
    case 0x117: MapToolsMenu(); break;
    case 0x118: DrawCastePopUp(); break;
    }
}

extern void far win_Open(int win, ...);

void far OpenMapWindow(void)
{
    win_Open(0x100);
}

extern int _fastcall win_IsWinOpen(int win);
extern void far clip_Push(void);
extern void far clip_SetWin(int win);
extern int far fd_50F6_0508[2];
extern struct Rect far fd_50F6_10D2;
extern struct Rect far fd_50F6_38C2;
extern int far fd_50F6_10DE;
extern int far fd_50F6_38C0;
extern int far fd_50F6_10E0;
extern void far GRectInvOutline(struct Rect far *rect, int width);
extern void far clip_Pop(void);


extern int far fd_50F6_3854;
extern void far win_MapChanged(void);
extern int far fd_3D57_07C8;
extern char far * far * far fd_50F6_385A;
extern char far * far f_171C_1B84(char far * far *handle);
extern void far f_171C_1BBA(char far * far *handle);
extern unsigned char far LifeA[128][64];
extern unsigned char far MapA[128][64];
extern int far TERRAINset;
extern unsigned char far fd_3D57_046E[];
extern unsigned char far fd_3D57_039E[];
extern unsigned char far fd_3D57_030E[];
extern unsigned char far fd_3D57_061E[];
extern unsigned char far fd_3D57_054E[];
extern unsigned char far fd_3D57_04CE[];
extern unsigned char far LifeR[64][64];
extern unsigned char far MapR[64][64];
extern unsigned char far LifeB[64][64];
extern unsigned char far MapB[64][64];
extern unsigned char far fd_3D57_0656[];
extern unsigned char far fd_3D57_04A6[];
extern int far BpopT;
extern int far RpopT;
extern int far HealthR;
extern int near g_3DB2;
extern void far f_24AB_02AD(int font);
extern void far win_PrintfAtObj(int obj, char far *format, ...);
extern int far HealthB;
extern void far win_DrawHBar(int obj, long fraction);
extern char far * far * far fd_50F6_385E;
extern void far Punt(char far *msg);
extern unsigned char far PherMapBN[];
extern unsigned char far PherMapBT[];
extern unsigned char far PherMapRN[];
extern unsigned char far PherMapRT[];
extern unsigned char far PherMapA[];
extern int far f_1B4E_000D(int color);
extern long far TickCount(void);
extern void _fastcall win_SetColorNum(int color);
extern void far f_15D9_0006(long msg, struct Rect far *rect, int y);
extern void far clip_SubInclude(struct Rect far *rect);
extern int far fd_50F6_0F0C;
extern int far MapPlane;
extern int far fd_50F6_0F12;
extern int far fd_50F6_0F34;
extern int far fd_50F6_1004;
extern void far f_171C_1C0A(char far * far *handle);
extern void far clip_Off(void);
extern int far fd_50F6_0EAC;
extern int far CurExpTool;
extern void _fastcall win_SetColorFromObjNum(int obj);
extern void _fastcall win_DrawBitMapAtObjNum(int obj, int id);
extern int _fastcall win_DrawBitMap(int x, int y, int id);
extern int far fd_3D57_0C3E;
extern int far fd_50F6_03E0;
extern int far fd_50F6_046A;
extern int far fd_3D57_0C30;
extern int far fd_3D57_0C28;
extern int far fd_50F6_0470;
extern int far fd_50F6_047A;
extern void far AddFood(int count, int sound);
extern void far myBeginSound(int sound, int a, int b);
extern void far KillSomeAnts(int side);
extern void far AddSomeAnts(int side);
extern void far SubtractFood(void);
extern void far GotoMyAnt(void);
extern void _fastcall win_GetObjRect(int obj, struct Rect far *rect);
void far DrawMapCursor(void)
{
    if (!win_IsWinOpen(0x100) || g_298E != 0)
        return;
    clip_Push();
    clip_SetWin(0x100);
    fd_50F6_38C2.top = fd_50F6_3858 * fd_50F6_0508[1] + fd_50F6_10D2.top;
    fd_50F6_38C2.bottom = fd_50F6_38C2.top + fd_50F6_3858 * fd_50F6_10DE;
    fd_50F6_38C2.left = fd_50F6_3856 * fd_50F6_0508[0] + fd_50F6_10D2.left + fd_50F6_38C0;
    fd_50F6_38C2.right = fd_50F6_38C2.left + fd_50F6_3856 * fd_50F6_10E0;
    GRectInvOutline(&fd_50F6_38C2, 2);
    g_298E = 1;
    clip_Pop();
}



void far EraseMapCursor(void)
{
    if (!win_IsWinOpen(0x100) || g_298E != 1)
        return;
    clip_Push();
    clip_SetWin(0x100);
    GRectInvOutline(&fd_50F6_38C2, 2);
    g_298E = 0;
    clip_Pop();
}

void far ToggleMapCursor(void)
{
    if (g_298E)
        EraseMapCursor();
    else
        DrawMapCursor();
}

extern int far fd_50F6_3854;

void far o12_384C_03D0(char far *src, char far *dst, int n)
{
    if (fd_50F6_3854 == 64)
        (*fd_50F6_38BC)(src, dst, fd_50F6_3854, n);
    else
        (*fd_50F6_38B8)(src, dst, fd_50F6_3854, n);
}

extern void far win_MapChanged(void);

void far o12_384C_0425(void)
{
    win_MapChanged();
}

extern int far fd_3D57_07C8;
extern char far * far * far fd_50F6_385A;
extern char far * far f_171C_1B84(char far * far *handle);
extern void far f_171C_1BBA(char far * far *handle);
extern unsigned char far LifeA[128][64];
extern unsigned char far MapA[128][64];
extern int far TERRAINset;
extern unsigned char far fd_3D57_046E[];
extern unsigned char far fd_3D57_039E[];
extern unsigned char far fd_3D57_030E[];
extern unsigned char far fd_3D57_061E[];
extern unsigned char far fd_3D57_054E[];
extern unsigned char far fd_3D57_04CE[];

void far o12_384C_0432(void)
{
    int fresh;
    unsigned char far *buf;
    unsigned char far *p;
    unsigned char far *q;
    int x, y, c;

    fresh = g_2994;
    if (fd_3D57_07C8 != g_2992) {
        o12_384C_0425();
        g_2992 = fd_3D57_07C8;
        fresh = 0;
    }
    buf = (unsigned char far *)f_171C_1B84(fd_50F6_385A);
    if (fresh) {
        _fmemcpy(buf, f_171C_1B84(fd_50F6_10E2), 0x2000);
        f_171C_1BBA(fd_50F6_10E2);
    }
    p = &LifeA[0][0];
    q = &MapA[0][0];
    if (!(g_5A97 & 1)) {
        if (TERRAINset == 1) {
            for (x = 0; x < 64; x++, p -= 0x1fff, q -= 0x1fff)
                for (y = 0; y < 128; y++, p += 64, q += 64) {
                    c = *p;
                    if (c) *buf++ = fd_3D57_046E[c >> 3]; else if (!fresh) *buf++ = fd_3D57_039E[*q]; else buf++;
                }
        } else {
            for (x = 0; x < 64; x++, p -= 0x1fff, q -= 0x1fff)
                for (y = 0; y < 128; y++, p += 64, q += 64) {
                    c = *p;
                    if (c) *buf++ = fd_3D57_046E[c >> 3]; else if (!fresh) *buf++ = fd_3D57_030E[*q]; else buf++;
                }
        }
    } else {
        if (TERRAINset == 1) {
            for (x = 0; x < 64; x++, p -= 0x1fff, q -= 0x1fff)
                for (y = 0; y < 128; y++, p += 64, q += 64) {
                    c = *p;
                    if (c) *buf++ = fd_3D57_061E[c >> 3]; else if (!fresh) *buf++ = fd_3D57_054E[*q]; else buf++;
                }
        } else {
            for (x = 0; x < 64; x++, p -= 0x1fff, q -= 0x1fff)
                for (y = 0; y < 128; y++, p += 64, q += 64) {
                    c = *p;
                    if (c) *buf++ = fd_3D57_061E[c >> 3]; else if (!fresh) *buf++ = fd_3D57_04CE[*q]; else buf++;
                }
        }
    }
    f_171C_1BBA(fd_50F6_385A);
}


void far o12_384C_0706(unsigned char far *src)
{
    unsigned char far *buf;
    int x, y, i;
    unsigned char c;

    buf = (unsigned char far *)f_171C_1B84(fd_50F6_385A);
    g_2992 = fd_3D57_07C8;
    if (g_5A97 & 1) {
        for (x = 0; x < 32; x++)
            for (y = 0; y < 64; y++) {
                i = ((x << 7) + y) << 1;
                c = src[(y << 5) + x];
                c = c ? (c >> 4) + 0x2e : 0;
                buf[i] = c;
                buf[i + 1] = c;
                buf[i + 0x80] = c;
                buf[i + 0x81] = c;
            }
    } else {
        for (x = 0; x < 32; x++)
            for (y = 0; y < 64; y++) {
                i = ((x << 7) + y) << 1;
                c = src[(y << 5) + x];
                c = c ? (c >> 5) + 0x10 : 0xb;
                buf[i] = c; buf[i + 1] = c;
                buf[i + 0x80] = c; buf[i + 0x81] = c;
            }
    }
    f_171C_1BBA(fd_50F6_385A);
}

extern unsigned char far LifeR[64][64];
extern unsigned char far MapR[64][64];
extern unsigned char far LifeB[64][64];
extern unsigned char far MapB[64][64];
extern unsigned char far fd_3D57_0656[];
extern unsigned char far fd_3D57_04A6[];

void far o12_384C_080E(void)
{
    int fresh;
    unsigned char far *buf;
    unsigned char far *p;
    unsigned char far *q;
    int x, y, c;

    fresh = g_2994;
    if (fd_3D57_07C8 != g_2992) {
        o12_384C_0425();
        g_2992 = fd_3D57_07C8;
        fresh = 0;
    }
    buf = (unsigned char far *)f_171C_1B84(fd_50F6_385A);
    if (fresh) {
        _fmemcpy(buf, f_171C_1B84(fd_50F6_10E2), 0x2000);
        f_171C_1BBA(fd_50F6_10E2);
    }
    if (fd_3D57_07C8 == 3) {
        p = &LifeR[0][0];
        q = &MapR[0][0];
    } else {
        p = &LifeB[0][0];
        q = &MapB[0][0];
    }
    if (g_5A97 & 1) {
        for (x = 0; x < 64; x++, p -= 0xfff, q -= 0xfff)
            for (y = 0; y < 64; y++, p += 64, q += 64) {
                c = *p;
                switch (c) {
                case 0:
                    if (!fresh) *buf++ = fd_3D57_0656[*q >> 2]; else buf++;
                    break;
                case 0xfe:
                case 0xff:
                    *buf++ = 0x27;
                    break;
                default:
                    if (c & 0x80) *buf++ = 0x25; else *buf++ = 0x23;
                    break;
                }
            }
    } else {
        for (x = 0; x < 64; x++, p -= 0xfff, q -= 0xfff)
            for (y = 0; y < 64; y++, p += 64, q += 64) {
                c = *p;
                switch (c) {
                case 0:
                    if (!fresh) *buf++ = fd_3D57_04A6[*q >> 2]; else buf++;
                    break;
                case 0xfe:
                case 0xff:
                    *buf++ = 1;
                    break;
                default:
                    if (c & 0x80) *buf++ = 3; else *buf++ = 0xf;
                    break;
                }
            }
    }
    f_171C_1BBA(fd_50F6_385A);
}

extern int far BpopT;
extern int far RpopT;
extern int far HealthR;
extern int near g_3DB2;
extern void far f_24AB_02AD(int font);
extern void far win_PrintfAtObj(int obj, char far *format, ...);
extern int far HealthB;
extern void far win_DrawHBar(int obj, long fraction);

void far DrawMapData(void)
{
    int popMax, redHealth;
    long maxPop;

    popMax = 1;
    if (BpopT > popMax)
        popMax = BpopT;
    if (RpopT > popMax)
        popMax = RpopT;
    redHealth = RpopT == 0 ? 0 : HealthR;
    f_24AB_02AD(g_3DB2 == 320 ? 0 : 3);
    win_PrintfAtObj(0x119, "%-d", BpopT);
    win_PrintfAtObj(0x11a, "%-d", RpopT);
    f_24AB_02AD(0);
    win_DrawHBar(0x11b, ((long)HealthB << 16) / 100);
    maxPop = popMax;
    win_DrawHBar(0x11d, ((long)BpopT << 16) / maxPop);
    win_DrawHBar(0x11c, ((long)redHealth << 16) / 100);
    win_DrawHBar(0x11e, ((long)RpopT << 16) / maxPop);
}

extern void far MapToYard(void);
extern char far * far * far fd_50F6_385E;
extern void far Punt(char far *msg);
extern unsigned char far PherMapBN[];
extern unsigned char far PherMapBT[];
extern unsigned char far PherMapRN[];
extern unsigned char far PherMapRT[];
extern unsigned char far PherMapA[];
extern int far f_1B4E_000D(int color);
extern void (far * near g_9134)(int left, int top, int right, int bottom, int color);
extern long far TickCount(void);
extern void _fastcall win_SetColorNum(int color);
extern void far f_15D9_0006(long msg, struct Rect far *rect, int y);
extern void far clip_SubInclude(struct Rect far *rect);
extern int far fd_50F6_0F0C;
extern int far MapPlane;
extern int far fd_50F6_0F12;
extern int far fd_50F6_0F34;
extern void (far * near g_914C)(int x, int y, char far *image, int width, int height);
extern int far fd_50F6_1004;
void far o12_384C_10A5(int x, int y, int kind);
void far o12_384C_1181(void);
extern void far f_171C_1C0A(char far * far *handle);

void far o12_384C_0B76(void)
{
    int n, row, off, y, sx, sy;
    char far *img;
    char far *gen;
    char far *old;

    if (fd_3D57_07C8 == 0) {
        MapToYard();
        return;
    }
    fd_50F6_3854 = 0x80;
    fd_50F6_38C0 = fd_55B3_2990 = 0;
    fd_50F6_385E = f_171C_1A9E(0x400L, 1, "Map window image");
    fd_50F6_385A = f_171C_1A9E(0x2000L, 1, "Generated map window");
    if (fd_3D57_07C8 != g_2992)
        win_MapChanged();
    switch (fd_3D57_07C8) {
    case 0:
        Punt("Draw map - yard");
        break;
    case 1:
        o12_384C_0432();
        break;
    case 2:
    case 3:
        o12_384C_080E();
        fd_50F6_3854 = 0x40;
        fd_50F6_38C0 = fd_50F6_3856 << 5;
        break;
    case 4:
        o12_384C_0706(PherMapBN);
        break;
    case 5:
        o12_384C_0706(PherMapBT);
        break;
    case 6:
        o12_384C_0706(PherMapRN);
        break;
    case 7:
        o12_384C_0706(PherMapRT);
        break;
    case 8:
        o12_384C_0706(PherMapA);
        break;
    }
    n = (fd_50F6_10D2.bottom - fd_50F6_10D2.top) / fd_50F6_3858;
    if (n > 64)
        WinPrintf("\nYMAXCOUNT =%d!!!!!", n);
    n = 64;
    (*g_9134)(fd_50F6_10D2.left, fd_50F6_10D2.top, fd_50F6_10D2.left + fd_50F6_38C0,
              fd_50F6_10D2.bottom, f_1B4E_000D(15));
    (*g_9134)(fd_50F6_10D2.right - fd_50F6_38C0, fd_50F6_10D2.top, fd_50F6_10D2.right,
              fd_50F6_10D2.bottom, f_1B4E_000D(15));
    EraseMapCursor();
    if (fd_55B3_299A) {
        if (TickCount() > fd_55B3_299E) {
            if (fd_55B3_299A)
                g_29A4 = 1;
            fd_55B3_299A = 0;
        } else {
            win_SetColorNum(3);
            f_15D9_0006(fd_55B3_299A, &fd_50F6_10D2, fd_50F6_10D2.top + 4);
        }
    }
    clip_Push();
    clip_SubInclude(&fd_50F6_10D2);
    img = f_171C_1B84(fd_50F6_385A);
    gen = f_171C_1B84(fd_50F6_385E);
    if (fd_50F6_0F0C && !g_2994 && MapPlane == 1) {
        sx = fd_50F6_0F12 >> 4;
        sy = fd_50F6_0F34 >> 4;
    } else
        sy = 0x7fff;
    old = f_171C_1B84(fd_50F6_10E2);
    y = fd_50F6_10D2.top;
    for (row = 0, off = 0; row < n; row++, y += fd_50F6_3858) {
        if (_fmemcmp(old + off, img + off, fd_50F6_3854) || fd_55B3_29A2 || (row < 8 && g_29A4)) {
            _fmemcpy(old + off, img + off, fd_50F6_3854);
            o12_384C_03D0(img + off, gen, y);
            (*g_914C)(fd_50F6_10D2.left + fd_50F6_38C0, y, gen, fd_50F6_3854 * fd_50F6_3856, fd_50F6_3858);
        }
        off += fd_50F6_3854;
        if (sy != 0x7fff && sy + 4 <= row) {
            o12_384C_10A5(sx, sy, fd_50F6_1004);
            sy = 0x7fff;
        }
    }
    if (sy != 0x7fff)
        o12_384C_10A5(sx, sy, fd_50F6_1004);
    f_171C_1BBA(fd_50F6_10E2);
    f_171C_1BBA(fd_50F6_385E);
    f_171C_1BBA(fd_50F6_385A);
    f_171C_1C0A(fd_50F6_385E);
    f_171C_1C0A(fd_50F6_385A);
    if (MapPlane == 1 && !g_2994)
        o12_384C_1181();
    DrawMapCursor();
    clip_Pop();
    fd_55B3_29A2 = fd_55B3_2990;
    g_29A4 = 0;
}


extern void far clip_Off(void);

void far o12_384C_100A(void)
{
    if (win_IsWinOpen(0x100)) {
        clip_SetWin(0x100);
        o12_384C_0B76();
        DrawMapData();
        clip_Off();
    }
}

extern int far fd_50F6_0EAC;
extern int far CurExpTool;
extern void _fastcall win_SetColorFromObjNum(int obj);
extern void _fastcall win_DrawBitMapAtObjNum(int obj, int id);

void far o12_384C_1035(int flags)
{
    int id;

    if (flags & 2) {
        if (fd_3D57_07C8 == 0)
            MapToYard();
        else {
            win_MapChanged();
            clip_SetWin(0x100);
            DrawMapData();
            o12_384C_0B76();
            id = fd_50F6_0EAC == 3 ? CurExpTool + 0x13ec : 0x13f3;
            win_SetColorFromObjNum(0x117);
            win_DrawBitMapAtObjNum(0x117, id);
        }
    }
}

extern int _fastcall win_DrawBitMap(int x, int y, int id);

void far o12_384C_10A5(int x, int y, int kind)
{
    int ys;
    unsigned char far *p;

    if (g_3DB2 == 320) {
        x = x * 2 - 3;
        ys = y * 2 - 3;
    } else {
        x = x * 4 - 3;
        ys = y * 4 - 3;
    }
    win_DrawBitMap(x + fd_50F6_10D2.left, ys + fd_50F6_10D2.top, kind + 0x44c);
    y -= 2;
    if (fd_50F6_10E2) {
        p = (unsigned char far *)f_171C_1B84(fd_50F6_10E2);
        p += fd_50F6_3854 * y;
        for (x = y + 5; y < x; y++, p += fd_50F6_3854) {
            if (y >= 64)
                break;
            if (y >= 0)
                *p = 0xff;
        }
        f_171C_1BBA(fd_50F6_10E2);
    }
}

extern int far fd_3D57_0C3E;
extern int far fd_50F6_03E0;
extern int far fd_50F6_046A;
extern int far fd_3D57_0C30;
extern int far fd_3D57_0C28;
extern int far fd_50F6_0470;
extern int far fd_50F6_047A;

void far o12_384C_1181(void)
{
    int x, y, end;
    unsigned char far *p;

    if (fd_3D57_0C3E == 0)
        return;
    x = fd_50F6_03E0 << 2;
    y = fd_50F6_046A << 2;
    if (g_3DB2 == 320) {
        x >>= 1;
        y >>= 1;
    }
    win_DrawBitMap(x + fd_50F6_10D2.left, y + fd_50F6_10D2.top, fd_3D57_0C30 + 0x4b0);
    if (fd_3D57_0C28 == 3 || fd_3D57_0C28 == 4) {
        x = fd_50F6_0470 << 2;
        y = fd_50F6_047A << 2;
        if (g_3DB2 == 320) {
            x >>= 1;
            y >>= 1;
        }
        win_DrawBitMap(x + fd_50F6_10D2.left, y + fd_50F6_10D2.top, (fd_3D57_0C30 & 1) + 0x4ba);
    }
    y = fd_50F6_046A;
    if (fd_50F6_10E2) {
        p = (unsigned char far *)f_171C_1B84(fd_50F6_10E2);
        p += fd_50F6_3854 * y;
        for (end = y + 8; y < end; y++, p += fd_50F6_3854) {
            if (y >= 64)
                break;
            if (y >= 0)
                *p = 0xff;
        }
        f_171C_1BBA(fd_50F6_10E2);
    }
    fd_55B3_2990 = 1;
}

extern void far AddFood(int count, int sound);
extern void far myBeginSound(int sound, int a, int b);
extern void far KillSomeAnts(int side);
extern void far AddSomeAnts(int side);
extern void far SubtractFood(void);
extern void far GotoMyAnt(void);
extern void _fastcall win_GetObjRect(int obj, struct Rect far *rect);

void far o12_384C_12D3(struct Event far *ev)
{
    struct Rect r;
    int side;

    if (*(unsigned char far *)0x00000417L & 4) {
        if (*(unsigned char far *)0x00000417L & 3) {
            win_GetObjRect(0x110, &r);
            side = (r.left + r.right) / 2;
            side = ev->h >= side ? 0 : 1;
            if (*(unsigned char far *)0x00000417L & 8)
                KillSomeAnts(side);
            else
                AddSomeAnts(side);
        } else if (*(unsigned char far *)0x00000417L & 8) {
            myBeginSound(0x20, 0, 0x7e);
            SubtractFood();
        } else
            AddFood(0x96, 1);
    } else
        GotoMyAnt();
}
