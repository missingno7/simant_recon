/* Overlay section S13, code frame 384C: yard window (yard events, animated yard objects, colonies). */

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

struct Pt {
    int h;
    int v;
};

static int g_2A2A = -1;
static int g_2A2C = -1;
static int g_2A2E = -1;
static int g_2A30 = -1;
static int g_2A32 = -1;
static int g_2A34 = -1;
static long g_2A36 = 0;
static long g_2A3A = 0;
static int g_2A3E = -1;
static int g_2A40 = -1;
static int g_2A42[8] = { 0xa9, 0x43, 0xc1, 0x43, 0xba, 0x4a, 0xa2, 0x4a };
static int g_2A52 = 0;
static int g_2A54 = -1;
static signed char kidX[12] = { 3, 3, 1, 0, 3, 0, 1, 4, 4, 3, 7, 2 };
static signed char kidY[44] = {
    2, 0, 2, 3, 2, 3, 2, 0, 2, 3, 2, 3, 4, 5, 4, 6, 0, 2, 0, 2, 0, 3,
    2, 1, 5, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 1, 0, 1, 1, 0, 1, 1, 0, 1
};
static signed char dogWalkX[12] = { 1, 0, 1, 2, 0, 1, 2, 2, 2, 1, 0, 1 };
static signed char dogWalkY[8] = { 0, 1, 0, 1, 2, 1, 2, 0 };
static signed char catOfs[40] = {
    0, 1, 2, 1, 2, 0, 2, 0, 1, 1, 3, 3, -10, -9, -10, -10, -21, -19, -18, 0,
    0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 0, -16, -23, -24, -22, -18, -10, -10, -4, -2
};
static int g_2ACA[4] = { 15, 31, 35, 72 };
static int g_2AD2[4] = { 15, 19, 35, 72 };

void far YardArea(struct Event far *ev);
extern void far f_00F8_047F(void);
extern int far fd_50F6_035C;
extern void far f_015B_0273(int mode);
extern int far fd_50F6_0EAC;
extern void far myBeginSound(int sound, int a, int b);
extern char far * far * far fd_50F6_034C;
extern void far f_15D9_009C(void far *text, long pos, int mode);
extern int far fd_50F6_0AEC[];
extern int far fd_50F6_04C2;
extern int far fd_50F6_08DC;
extern int far fd_3D57_02C0;
extern void _fastcall f_22BF_03BE(int obj);
extern void far f_015B_094A(void);
void far UpdateYard(void);
extern void _fastcall f_22BF_03C6(int obj);
extern void far DoWinHelp(int win);

void far ProcYardEvent(struct Event far *ev)
{
    int n;

    switch (ev->code) {
    case 0x1902:
        YardArea(ev);
        break;
    case 0x1907:
        f_00F8_047F();
        break;
    case 0x1908:
        if (fd_50F6_035C < 2)
            f_015B_0273(fd_50F6_035C ^ 1);
        else
            f_015B_0273(0);
        break;
    case 0x1909:
        f_015B_0273(2);
        break;
    case 0x190a:
        f_015B_0273(3);
        break;
    case 0x190b:
        if (fd_50F6_0EAC != 2) {
            myBeginSound(1, 0, 0x7e);
            f_15D9_009C(fd_50F6_034C[15], 180L, 1);
        } else {
            n = fd_50F6_0AEC[3] + fd_50F6_0AEC[4];
            if (fd_50F6_04C2 == 0x40 || fd_50F6_04C2 == 0x20)
                n--;
            if (n <= 0) {
                myBeginSound(1, 0, 0x7e);
                f_15D9_009C(fd_50F6_034C[5], 180L, 1);
            } else {
                fd_50F6_08DC = 200;
                f_15D9_009C(fd_50F6_034C[6], 180L, 1);
            }
        }
        break;
    case 0x190d:
        fd_3D57_02C0 = 1;
        break;
    case 0x190e:
        fd_3D57_02C0 = 0;
        break;
    case 0x1910:
        f_22BF_03BE(0x190e);
        f_22BF_03BE(0x1910);
        f_015B_094A();
        UpdateYard();
        f_22BF_03C6(0x1910);
        break;
    case 0x1911:
        DoWinHelp(0x1906);
        break;
    }
}

extern int far fd_50F6_07CA[2];
void far InvertPatch(int x, int y);

void far DrawYardCursor(void)
{
    if (!g_2A52) {
        InvertPatch(fd_50F6_07CA[0], fd_50F6_07CA[1]);
        g_2A52 = 1;
    }
}

void far EraseYardCursor(void)
{
    if (g_2A52) {
        InvertPatch(fd_50F6_07CA[0], fd_50F6_07CA[1]);
        g_2A52 = 0;
    }
}

extern long far fd_55B3_299A;
extern long far TickCount(void);
extern long far fd_55B3_299E;
extern int far fd_55B3_29A2;
extern void _fastcall f_21FA_00EE(int color);
extern struct Rect far fd_50F6_10D2;
extern void far f_15D9_0006(long msg, struct Rect far *rect, int y);

void far o13_384C_01E5(void)
{
    if (fd_55B3_299A) {
        if (TickCount() > fd_55B3_299E) {
            if (fd_55B3_299A)
                fd_55B3_29A2 = 1;
            fd_55B3_299A = 0;
        } else {
            f_21FA_00EE(3);
            if (fd_50F6_035C > 1)
                f_15D9_0006(fd_55B3_299A, &fd_50F6_10D2, fd_50F6_10D2.top + 4);
        }
    }
}

void far Draw_SimYard(int mode, int force);
extern int far fd_50F6_07C8;
extern void far f_22BF_0706(int obj, ...);
extern int far fd_50F6_03E2;
extern int far fd_50F6_0400;

void far o13_384C_027C(void)
{
    o13_384C_01E5();
    Draw_SimYard(fd_50F6_035C, 1);
    f_22BF_0706(0x190c, fd_50F6_07C8);
    f_22BF_0706(0x1912, fd_50F6_03E2);
    f_22BF_0706(0x1913, fd_50F6_0400);
}

extern int near g_3DB2;
extern char near g_5A97;
extern void _fastcall win_DrawObjectNum(int objNum);
extern void _fastcall win_GetObjRect(int obj, struct Rect far *rect);
extern int _fastcall win_DrawBitMap(int x, int y, int id);
extern void far f_208F_0419(struct Pt far *size, int id);
extern int far fd_55B3_2990;

void far win_DrawYardWindow(int flags)
{
    struct Rect r;
    struct Pt sz;
    int id, y;

    if (flags & 1) {
        EraseYardCursor();
        if (fd_50F6_035C > 1) {
            if (fd_50F6_035C > 2 || fd_55B3_29A2 || !(flags & 4) || fd_50F6_035C != g_2A54) {
                if (g_3DB2 != 320 && !(g_5A97 & 1)) {
                    o13_384C_01E5();
                    win_DrawObjectNum(0x1914);
                    win_GetObjRect(0x1914, &r);
                    y = r.bottom;
                    win_GetObjRect(0x1902, &r);
                    for (id = 0x1b6c; id <= 0x1b6e; id++) {
                        win_DrawBitMap(r.left, y, id);
                        f_208F_0419(&sz, id);
                        y += sz.v;
                    }
                    win_DrawObjectNum(0x1915);
                } else
                    win_DrawBitMap(fd_50F6_10D2.left - ((g_5A97 & 1) != 0), fd_50F6_10D2.top, 0x1b5a);
            }
        }
        g_2A54 = fd_50F6_035C;
    }
    if (flags & 2) {
        fd_55B3_2990 = 0;
        o13_384C_027C();
        fd_55B3_29A2 = fd_55B3_2990;
        DrawYardCursor();
    }
}

extern int _fastcall f_22BF_09B0(int win);
extern void far clip_SetWin(int win);
extern void far f_1E57_0362(void);

void far o13_384C_03F8(void)
{
    if (f_22BF_09B0(0x1900) && fd_55B3_29A2) {
        clip_SetWin(0x1900);
        EraseYardCursor();
        o13_384C_01E5();
        win_DrawObjectNum(0x1914);
        DrawYardCursor();
        f_1E57_0362();
        fd_55B3_29A2 = 0;
    }
}

void far DrawYard(void)
{
    if (f_22BF_09B0(0x1900)) {
        clip_SetWin(0x1900);
        win_DrawYardWindow(7);
        f_1E57_0362();
    }
}

void far UpdateYard(void)
{
    DrawYard();
}

typedef char far * far *Handle;
extern int far fd_3D57_0C2C;
extern int far fd_3D57_0C2E;
extern int far fd_3D57_0C32;
extern Handle far fd_50F6_10DA;
extern void far hanim_SetObjectPos(int x, int y, int pic, Handle h, int id, int pri);
extern int far hanim_AddAnimObject(Handle h, int x, int y, int pic, int pri);
extern int far fd_50F6_047E;
extern long far f_00F8_02BE(void);
extern long far fd_50F6_109C;
extern int far fd_50F6_10B0;
extern void far hanim_RemoveAnimObject(Handle h, int id);
extern void far f_171C_1C0A(long h);
extern void far f_24AB_02AD(int font);
extern long far f_1629_000C(char far *msg, int flags);
extern int far fd_50F6_10BC;
extern char far * far * far fd_50F6_10A8;

void far DrawSimKid(void)
{
    struct Pt sz;
    int x, y;

    x = fd_3D57_0C2C;
    y = fd_3D57_0C2E;
    if (fd_3D57_0C32 < 12) {
        x += kidX[fd_3D57_0C32];
        y += kidY[fd_3D57_0C32];
    } else if (fd_3D57_0C32 < 24) {
        x += kidX[fd_3D57_0C32 + 4];
        y += kidY[fd_3D57_0C32 - 4];
    } else if (fd_3D57_0C32 < 200) {
        x += kidX[fd_3D57_0C32 - 68];
        y += kidY[fd_3D57_0C32 - 68];
    }
    if (g_3DB2 == 320) {
        x = (x >> 1) + 5;
        y = (y >> 1) + 6;
    }
    x += fd_50F6_10D2.left;
    y += fd_50F6_10D2.top;
    if (g_2A2A != -1)
        hanim_SetObjectPos(x, y, fd_3D57_0C32 + 0x1f40, fd_50F6_10DA, g_2A2A, -1);
    else
        g_2A2A = hanim_AddAnimObject(fd_50F6_10DA, x, y, fd_3D57_0C32 + 0x1f40, -1);
    if (fd_50F6_047E == 0 && f_00F8_02BE() > fd_50F6_109C)
        fd_50F6_10B0 = 0;
    if (g_2A3E != -1) {
        hanim_RemoveAnimObject(fd_50F6_10DA, g_2A3E);
        g_2A3E = -1;
    }
    if (g_2A36) {
        f_171C_1C0A(g_2A36);
        g_2A36 = 0;
    }
    if (fd_50F6_10B0) {
        f_24AB_02AD(2);
        g_2A36 = f_1629_000C(fd_50F6_10A8[fd_50F6_10BC], 0);
        f_24AB_02AD(0);
        f_208F_0419(&sz, 30000);
        y = fd_3D57_0C2E;
        if (g_3DB2 == 320)
            y = (y >> 1) + 6;
        else
            x += 4;
        y += fd_50F6_10D2.top - sz.v;
        if (g_2A3E != -1)
            hanim_SetObjectPos(x, y, 30000, fd_50F6_10DA, g_2A3E, 999);
        else
            g_2A3E = hanim_AddAnimObject(fd_50F6_10DA, x, y, 30000, 999);
    }
}

extern int far fd_50F6_04BE;
extern int far fd_50F6_04C6;
extern int far fd_3D57_0C44;
extern int far fd_50F6_04E4;

void far DrawDog(void)
{
    int x, y;

    x = fd_50F6_04BE;
    y = fd_50F6_04C6;
    if (fd_3D57_0C44 == 0) {
        if (fd_50F6_04E4 < 12) {
            x += dogWalkX[fd_50F6_04E4];
            y += dogWalkY[fd_50F6_04E4];
        } else {
            x += kidX[fd_50F6_04E4 - 20];
            y += kidX[fd_50F6_04E4 - 16];
        }
        if (g_3DB2 == 320) {
            x = (x >> 1) + 5;
            y = (y >> 1) + 6;
        }
        x += fd_50F6_10D2.left;
        y += fd_50F6_10D2.top;
        if (g_2A30 != -1)
            hanim_SetObjectPos(x, y, fd_50F6_04E4 + 0x2134, fd_50F6_10DA, g_2A30, -1);
        else
            g_2A30 = hanim_AddAnimObject(fd_50F6_10DA, x, y, fd_50F6_04E4 + 0x2134, -1);
    }
}

extern int far fd_50F6_10AC;
extern int far fd_50F6_10BA;
extern int far fd_50F6_108C;

void far DrawSimBird(void)
{
    int x, y;

    x = fd_50F6_10AC - 10;
    y = fd_50F6_10BA - 3;
    if (fd_50F6_108C) {
        x++;
        y += 2;
    }
    if (g_3DB2 == 320) {
        x = (x >> 1) + 5;
        y = (y >> 1) + 6;
    }
    x += fd_50F6_10D2.left;
    y += fd_50F6_10D2.top;
    if (g_2A2E != -1)
        hanim_SetObjectPos(x, y, fd_50F6_108C + 0x4e2, fd_50F6_10DA, g_2A2E, -1);
    else
        g_2A2E = hanim_AddAnimObject(fd_50F6_10DA, x, y, fd_50F6_108C + 0x4e2, -1);
}

extern int far fd_50F6_02BE;
extern int far fd_50F6_032C;
extern int far fd_50F6_0244;

void far DrawSimCat(void)
{
    int x, y;

    x = fd_50F6_02BE;
    y = fd_50F6_032C;
    if (fd_50F6_0244 >= 10) {
        if (fd_50F6_0244 < 20) {
            x += catOfs[fd_50F6_0244 + 2];
            y += catOfs[fd_50F6_0244 + 6];
        } else {
            x += catOfs[fd_50F6_0244];
            y += catOfs[fd_50F6_0244 + 10];
        }
    }
    if (g_3DB2 == 320) {
        x = (x >> 1) + 5;
        y = (y >> 1) + 6;
    }
    x += fd_50F6_10D2.left;
    y += fd_50F6_10D2.top;
    if (g_2A2C != -1)
        hanim_SetObjectPos(x, y, fd_50F6_0244 + 0x514, fd_50F6_10DA, g_2A2C, -1);
    else
        g_2A2C = hanim_AddAnimObject(fd_50F6_10DA, x, y, fd_50F6_0244 + 0x514, -1);
}

void far DrawForSale(void)
{
    int x, y;

    x = 0xaa;
    y = 0xba;
    if (g_3DB2 == 320) {
        x = 0x5a;
        y = 0x63;
    }
    x += fd_50F6_10D2.left;
    y += fd_50F6_10D2.top;
    if (g_2A34 != -1)
        hanim_SetObjectPos(x, y, 0x4ec, fd_50F6_10DA, g_2A34, -1);
    else
        g_2A34 = hanim_AddAnimObject(fd_50F6_10DA, x, y, 0x4ec, -1);
}

extern int far fd_3D57_0C28;

/* SCAFFOLD BEGIN: DrawMower draft: x lives in SI/DI instead of BX (register allocation) */
void far DrawMower(void)
{
    int frame, x, y;

    frame = 0;
    if (fd_3D57_0C28 == 3 || fd_3D57_0C28 == 4) {
        if (fd_50F6_047E == 0)
            myBeginSound(0x24, 0, 0x40);
        switch (fd_3D57_0C32) {
        case 0x67:
        case 0x68:
        case 0x69:
            frame = 1;
            break;
        case 0x6d:
        case 0x6e:
        case 0x6f:
            frame = 2;
            break;
        default:
            if (g_2A32 != -1) {
                hanim_RemoveAnimObject(fd_50F6_10DA, g_2A32);
                g_2A32 = -1;
            }
            return;
        }
    }
    if (frame == 0) {
        x = 0x62;
        y = 0xb5;
    } else {
        if (frame == 1)
            x = fd_3D57_0C2C + 0x13;
        else
            x = fd_3D57_0C2C - 0xf;
        y = fd_3D57_0C2E + 0xf;
    }
    if (g_3DB2 == 320) {
        x = (x >> 1) + 5;
        y = (y >> 1) + 6;
    }
    x += fd_50F6_10D2.left;
    y += fd_50F6_10D2.top;
    if (g_2A32 != -1)
        hanim_SetObjectPos(x, y, frame + 0x2260, fd_50F6_10DA, g_2A32, -1);
    else
        g_2A32 = hanim_AddAnimObject(fd_50F6_10DA, x, y, frame + 0x2260, -1);
}

/* SCAFFOLD END */

extern Handle far hanim_MakeAnimSet(void);
extern int far fd_50F6_38CA[15];
extern int far fd_50F6_38E8[17];
extern int far fd_50F6_390A[17];

extern int far fd_50F6_0254;
extern int far fd_50F6_10A0;
extern int far fd_50F6_0352;
extern void far hanim_RenderAnimSet(Handle h);
extern int far fd_3D57_0C20;
void far DrawAnimYardMessage(void);
void far DrawRain(void);
void far DrawSwarm(void);
void far DrawSimColonies(int mode);
void far DrawColonyBars(int mode);

void far Draw_SimYard(int mode, int force)
{
    int i;

    EraseYardCursor();
    if (mode <= 1) {
        if (!fd_50F6_10DA) {
            fd_50F6_10DA = hanim_MakeAnimSet();
            _fmemset(fd_50F6_38CA, -1, 0x1e);
            _fmemset(fd_50F6_38E8, -1, 0x22);
            _fmemset(fd_50F6_390A, -1, 0x22);
            g_2A2A = -1;
            g_2A30 = -1;
            g_2A2E = -1;
            g_2A2C = -1;
            g_2A32 = -1;
            g_2A34 = -1;
            g_2A3E = -1;
            g_2A40 = -1;
        }
        if (fd_50F6_0254)
            DrawSimCat();
        else if (g_2A2C != -1) {
            hanim_RemoveAnimObject(fd_50F6_10DA, g_2A2C);
            g_2A2C = -1;
        }
        DrawDog();
        if ((mode || fd_3D57_0C28) && fd_3D57_0C32 >= 0)
            DrawSimKid();
        else {
            if (g_2A2A != -1) {
                hanim_RemoveAnimObject(fd_50F6_10DA, g_2A2A);
                g_2A2A = -1;
            }
            if (g_2A3E != -1) {
                hanim_RemoveAnimObject(fd_50F6_10DA, g_2A3E);
                g_2A3E = -1;
                f_171C_1C0A(g_2A36);
                g_2A36 = 0;
            }
        }
        DrawMower();
        if (fd_50F6_10A0)
            DrawSimBird();
        else if (g_2A2E != -1) {
            hanim_RemoveAnimObject(fd_50F6_10DA, g_2A2E);
            g_2A2E = -1;
        }
        if (fd_3D57_0C44)
            DrawForSale();
        if (fd_50F6_0352)
            DrawRain();
        else
            for (i = 0; i <= 14; i++)
                if (fd_50F6_38CA[i] != -1) {
                    hanim_RemoveAnimObject(fd_50F6_10DA, fd_50F6_38CA[i]);
                    fd_50F6_38CA[i] = -1;
                }
        DrawSwarm();
        DrawAnimYardMessage();
        hanim_RenderAnimSet(fd_50F6_10DA);
    } else {
        fd_3D57_0C20 = 0;
        if (mode == 2)
            DrawSimColonies(mode);
        else
            DrawColonyBars(mode);
    }
    DrawYardCursor();
}

extern long far f_24AB_0002(long text);
extern int far fd_50F6_392C;

void far DrawAnimYardMessage(void)
{
    if (g_2A40 != -1) {
        hanim_RemoveAnimObject(fd_50F6_10DA, g_2A40);
        g_2A40 = -1;
    }
    if (g_2A3A) {
        f_171C_1C0A(g_2A3A);
        g_2A3A = 0;
    }
    if (fd_55B3_299A) {
        f_24AB_02AD(2);
        g_2A3A = f_24AB_0002(fd_55B3_299A);
        f_24AB_02AD(0);
        g_2A40 = hanim_AddAnimObject(fd_50F6_10DA,
                             (fd_50F6_10D2.right - fd_50F6_392C + fd_50F6_10D2.left) / 2,
                             fd_50F6_10D2.top + 4, 0x7531, 999);
    }
}

extern int far SRand1(int range);

void far DrawRain(void)
{
    int x, y, i;

    i = 14;
    while (i--) {
        x = SRand1(400) + 50;
        y = SRand1(150);
        if (g_3DB2 == 320) {
            x = (x >> 1) + 5;
            y = (y >> 1) + 6;
        }
        x += fd_50F6_10D2.left;
        y += fd_50F6_10D2.top;
        if (fd_50F6_38CA[i] != -1)
            hanim_SetObjectPos(x, y, 0x1b5d, fd_50F6_10DA, fd_50F6_38CA[i], 0x8000);
        else
            fd_50F6_38CA[i] = hanim_AddAnimObject(fd_50F6_10DA, x, y, 0x1b5d, 1000);
    }
}

extern int far fd_3D57_07C8;
extern int far fd_50F6_1048;
extern int far fd_50F6_103C;
extern int far fd_50F6_06AA;
extern signed char far fd_50F6_0F46[];
extern signed char far fd_50F6_0F84[];
int far TooFar(int x, int y);
extern int far SRand16(void);
extern int far fd_50F6_073A;
extern int far fd_50F6_0850;
extern signed char far fd_50F6_0FC6[];
extern signed char far fd_50F6_1008[];

void far DrawSwarm(void)
{
    int i, x, y;

    if (fd_3D57_07C8 == 0) {
        fd_50F6_1048 = fd_50F6_07CA[1] * 10 + 0x2e;
        fd_50F6_103C = fd_50F6_07CA[0] * 28 - fd_50F6_07CA[1] * 10 + 0xb2;
        for (i = 0; i < fd_50F6_06AA; i++) {
            if (i >= 16 || fd_50F6_07C8 <= i)
                break;
            if (TooFar(fd_50F6_0F46[i], fd_50F6_0F84[i])) {
                fd_50F6_0F46[i] = SRand16() - 10;
                fd_50F6_0F84[i] = SRand16() - 10;
            }
            fd_50F6_0F46[i] += SRand1(3) - 1;
            x = fd_50F6_0F46[i] + fd_50F6_103C;
            fd_50F6_0F84[i] += SRand1(3) - 1;
            y = fd_50F6_0F84[i] + fd_50F6_1048;
            if (g_3DB2 == 320) {
                x = (x >> 1) + 5;
                y = (y >> 1) + 6;
            }
            x += fd_50F6_10D2.left;
            y += fd_50F6_10D2.top;
            if (fd_50F6_38E8[i] != -1)
                hanim_SetObjectPos(x, y, 0x1b5e, fd_50F6_10DA, fd_50F6_38E8[i], -1);
            else
                fd_50F6_38E8[i] = hanim_AddAnimObject(fd_50F6_10DA, x, y, 0x1b5e, -1);
        }
        for (; i < 16; i++)
            if (fd_50F6_38E8[i] != -1) {
                hanim_RemoveAnimObject(fd_50F6_10DA, fd_50F6_38E8[i]);
                fd_50F6_38E8[i] = -1;
            }
        for (i = 0; i < fd_50F6_073A; i++) {
            if (i >= 16 || fd_50F6_0850 <= i)
                break;
            if (TooFar(fd_50F6_0FC6[i], fd_50F6_1008[i]))
                fd_50F6_1008[i] = fd_50F6_0FC6[i] = 0;
            fd_50F6_0FC6[i] += SRand1(3) - 1;
            x = fd_50F6_0FC6[i] + fd_50F6_103C;
            fd_50F6_1008[i] += SRand1(3) - 1;
            y = fd_50F6_1008[i] + fd_50F6_1048;
            if (g_3DB2 == 320) {
                x = (x >> 1) + 5;
                y = (y >> 1) + 6;
            }
            x += fd_50F6_10D2.left;
            y += fd_50F6_10D2.top;
            if (fd_50F6_390A[i] != -1)
                hanim_SetObjectPos(x, y, 0x1b5f, fd_50F6_10DA, fd_50F6_390A[i], -1);
            else
                fd_50F6_390A[i] = hanim_AddAnimObject(fd_50F6_10DA, x, y, 0x1b5f, -1);
        }
        for (; i < 16; i++)
            if (fd_50F6_390A[i] != -1) {
                hanim_RemoveAnimObject(fd_50F6_10DA, fd_50F6_390A[i]);
                fd_50F6_390A[i] = -1;
            }
    }
}

int far TooFar(int x, int y)
{
    if (x > 15 || x < -15 || y > 15 || y < -15)
        return 1;
    return 0;
}

extern void far clip_Push(void);
extern void far f_1FAA_0006(struct Pt far *pts, int a, int b);
extern void far clip_Pop(void);

/* SCAFFOLD BEGIN: InvertPatch draft: one byte short, point arithmetic order */
void far InvertPatch(int x, int y)
{
    struct Pt pts[4];
    struct Pt org;
    int i, h, v;

    clip_Push();
    clip_SetWin(0x1900);
    org.h = x * 28 - y * 10 + fd_50F6_10D2.left;
    org.v = y * 10 + fd_50F6_10D2.top;
    h = x * 28 - y * 10;
    v = y * 10;
    if (g_3DB2 == 320) {
        h = (h >> 1) + fd_50F6_10D2.left + 4;
        v = (v >> 1) + fd_50F6_10D2.top + 10;
        org.h = h;
        org.v = v;
        for (i = 0; i < 4; i++) {
            pts[i].h = g_2A42[i * 2] / 2 + org.h;
            pts[i].v = g_2A42[i * 2 + 1] / 2 + v;
        }
    } else {
        h += fd_50F6_10D2.left;
        v += fd_50F6_10D2.top;
        org.h = h;
        org.v = v;
        for (i = 0; i < 4; i++) {
            pts[i].h = g_2A42[i * 2] + org.h;
            pts[i].v = g_2A42[i * 2 + 1] + v;
        }
    }
    f_1FAA_0006(pts, -1, -1);
    clip_Pop();
}

/* SCAFFOLD END */

extern unsigned char far fd_3D57_0164[12][16];
extern unsigned char far fd_3D57_00A4[12][16];
extern int far f_1B4E_000D(int color);

/* SCAFFOLD BEGIN: DrawSimColonies draft */
void far DrawSimColonies(int mode)
{
    struct Pt pts[4];
    struct Pt org;
    int x, y, i, c, color, h, v;

    if (mode == 2)
        for (x = 0; x < 12; x++)
            for (y = 0; y < 16; y++) {
                c = fd_3D57_0164[x][y];
                if (fd_3D57_00A4[x][y] == 0)
                    color = (c == 0) + 2;
                else
                    color = c != 0;
                h = x * 28 - y * 10;
                v = y * 10;
                if (g_3DB2 == 320) {
                    h >>= 1;
                    v >>= 1;
                    h += fd_50F6_10D2.left + 4;
                    v += fd_50F6_10D2.top + 10;
                    org.h = h;
                    for (i = 0; i < 4; i++) {
                        pts[i].h = (i >= 2 ? 0 : -1) + g_2A42[i * 2] / 2 + org.h;
                        pts[i].v = (i >= 2 ? -1 : 1) + g_2A42[i * 2 + 1] / 2 + v;
                    }
                } else {
                    h += fd_50F6_10D2.left;
                    v += fd_50F6_10D2.top;
                    org.h = h;
                    org.v = v;
                    for (i = 0; i < 4; i++) {
                        pts[i].h = g_2A42[i * 2] + org.h;
                        pts[i].v = g_2A42[i * 2 + 1] + v;
                    }
                }
                f_1FAA_0006(pts, f_1B4E_000D(g_2ACA[color]), f_1B4E_000D(g_2AD2[color]));
            }
}

/* SCAFFOLD END */

extern void far f_1CE2_046D(struct Rect far *rect, int color);

/* SCAFFOLD BEGIN: DrawColonyBars draft */
void far DrawColonyBars(int mode)
{
    struct Rect r;
    int x, y, h;

    for (x = 0; x < 12; x++)
        for (y = 0; y < 16; y++) {
            h = (fd_3D57_00A4[x][y] + 3) >> 2;
            if (h > 0) {
                if (g_3DB2 == 320) {
                    r.left = ((x + 6) * 28 - (y * 10 + 12)) / 2 + fd_50F6_10D2.left + 10;
                    r.bottom = (y * 10 + 12 + 0x47) / 2 + fd_50F6_10D2.top + 4;
                    r.top = r.bottom - h / 2;
                    r.right = r.left + 4;
                } else {
                    r.left = (x + 6) * 28 + fd_50F6_10D2.left - y * 10;
                    r.bottom = y * 10 + fd_50F6_10D2.top + 0x47;
                    r.top = r.bottom - h;
                    r.right = r.left + 9;
                }
                f_1CE2_046D(&r, f_1B4E_000D(15));
            }
            h = (fd_3D57_0164[x][y] + 3) >> 2;
            if (h > 0) {
                if (g_3DB2 == 320) {
                    r.left = (x * 28 - (y * 10 + 12) + 0xb4) / 2 + fd_50F6_10D2.left + 10;
                    r.bottom = (y * 10 + 12 + 0x47) / 2 + fd_50F6_10D2.top + 4;
                    r.top = r.bottom - h / 2;
                    r.right = r.left + 4;
                } else {
                    r.left = x * 28 + (fd_50F6_10D2.left - y * 10) + 0xb4;
                    r.bottom = y * 10 + fd_50F6_10D2.top + 0x47;
                    r.top = r.bottom - h;
                    r.right = r.left + 9;
                }
                f_1CE2_046D(&r, f_1B4E_000D(0x23));
            }
        }
}

/* SCAFFOLD END */

extern int far fd_50F6_07BC[2];
extern void far WinPrintf(char far *format, ...);
extern void far f_015B_0798(void);

void far YardArea(struct Event far *ev)
{
    int x, y;

    y = ev->v - fd_50F6_10D2.top;
    x = ev->h - fd_50F6_10D2.left;
    if (g_3DB2 == 320) {
        x = (x + 2) * 2;
        y = (y - 8) * 2;
    }
    y = (y - g_2A42[1]) / 10;
    x = (y * 10 - g_2A42[0] + x) / 28;
    WinPrintf("\nYARD AREA @ %d, %d  : %d, %d", x, y, 12, 16);
    if (x >= 0 && x < 12 && y >= 0 && y < 16) {
        EraseYardCursor();
        fd_50F6_07BC[0] = x;
        fd_50F6_07BC[1] = y;
        if (ev->modifiers & 0x6000)
            f_015B_0798();
        DrawYardCursor();
    }
}

