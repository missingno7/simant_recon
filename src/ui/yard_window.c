/*
 * Handles yard window events and renders the yard. It draws animated people, animals, weather,
 * swarms and colony population bars.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS: overlay section 13 (S13); segment 384C; partial original translation unit.
 * Windows: ANTEDIT, from recorded function pairs in the Windows symbol inventory. Some pairs are
 * HIGH confidence, not confirmed.
 */

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
long g_2A36 = 0;
long g_2A3A = 0;
static int g_2A3E = -1;
static int g_2A40 = -1;
int g_2A42[8] = { 0xa9, 0x43, 0xc1, 0x43, 0xba, 0x4a, 0xa2, 0x4a };
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
extern void far YardToMap(void);
extern int far YardMode;
extern void far SetYardMode(int mode);
extern int far CurGameType;
extern void far myBeginSound(int sound, int a, int b);
extern char far * far * far WindPromptStrs;
extern void far EditMessage(void far *text, long pos, int mode);
extern int far CastePopB[];
extern int far MeType;
extern int far FlyAwayB;
extern int far LayDownQueenMode;
extern void _fastcall win_MakeObjSelected(int obj);
extern void far PlaceQueenInYard(void);
void far UpdateYard(void);
extern void _fastcall win_MakeObjUnselected(int obj);
extern void far DoWinHelp(int win);

void far ProcYardEvent(struct Event far *ev)
{
    int n;

    switch (ev->code) {
    case 0x1902:
        YardArea(ev);
        break;
    case 0x1907:
        YardToMap();
        break;
    case 0x1908:
        if (YardMode < 2)
            SetYardMode(YardMode ^ 1);
        else
            SetYardMode(0);
        break;
    case 0x1909:
        SetYardMode(2);
        break;
    case 0x190a:
        SetYardMode(3);
        break;
    case 0x190b:
        if (CurGameType != 2) {
            myBeginSound(1, 0, 0x7e);
            EditMessage(WindPromptStrs[15], 180L, 1);
        } else {
            n = CastePopB[3] + CastePopB[4];
            if (MeType == 0x40 || MeType == 0x20)
                n--;
            if (n <= 0) {
                myBeginSound(1, 0, 0x7e);
                EditMessage(WindPromptStrs[5], 180L, 1);
            } else {
                FlyAwayB = 200;
                EditMessage(WindPromptStrs[6], 180L, 1);
            }
        }
        break;
    case 0x190d:
        LayDownQueenMode = 1;
        break;
    case 0x190e:
        LayDownQueenMode = 0;
        break;
    case 0x1910:
        win_MakeObjSelected(0x190e);
        win_MakeObjSelected(0x1910);
        PlaceQueenInYard();
        UpdateYard();
        win_MakeObjUnselected(0x1910);
        break;
    case 0x1911:
        DoWinHelp(0x1906);
        break;
    }
}

extern int far CurYardPnt[2];
void far InvertPatch(int x, int y);

void far DrawYardCursor(void)
{
    if (!g_2A52) {
        InvertPatch(CurYardPnt[0], CurYardPnt[1]);
        g_2A52 = 1;
    }
}

void far EraseYardCursor(void)
{
    if (g_2A52) {
        InvertPatch(CurYardPnt[0], CurYardPnt[1]);
        g_2A52 = 0;
    }
}

extern long far mapMessage;
extern long far TickCount(void);
extern long far fd_55B3_299E;
extern int far fd_55B3_29A2;
extern void _fastcall win_SetColorNum(int color);
extern struct Rect far fd_50F6_10D2;
extern void far f_15D9_0006(long msg, struct Rect far *rect, int y);

void far yard_update_message(void)
{
    if (mapMessage) {
        if (TickCount() > fd_55B3_299E) {
            if (mapMessage)
                fd_55B3_29A2 = 1;
            mapMessage = 0;
        } else {
            win_SetColorNum(3);
            if (YardMode > 1)
                f_15D9_0006(mapMessage, &fd_50F6_10D2, fd_50F6_10D2.top + 4);
        }
    }
}

void far Draw_SimYard(int mode, int force);
extern int far QueenStorageB;
extern void far win_ObjFormatPrint(int obj, ...);
extern int far ColonyTotalBlack;
extern int far ColonyTotalRed;

void far yard_draw_content_totals(void)
{
    yard_update_message();
    Draw_SimYard(YardMode, 1);
    win_ObjFormatPrint(0x190c, QueenStorageB);
    win_ObjFormatPrint(0x1912, ColonyTotalBlack);
    win_ObjFormatPrint(0x1913, ColonyTotalRed);
}

extern int near g_3DB2;
extern char near g_5A97;
extern void _fastcall win_DrawObjectNum(int objNum);
extern void _fastcall win_GetObjRect(int obj, struct Rect far *rect);
extern int _fastcall win_DrawBitMap(int x, int y, int id);
extern void far gr_BitMapSize(struct Pt far *size, int id);
extern int far newMapForce;

void far win_DrawYardWindow(int flags)
{
    struct Rect r;
    struct Pt sz;
    int id, y;

    if (flags & 1) {
        EraseYardCursor();
        if (YardMode > 1) {
            if (YardMode > 2 || fd_55B3_29A2 || !(flags & 4) || YardMode != g_2A54) {
                if (g_3DB2 != 320 && !(g_5A97 & 1)) {
                    yard_update_message();
                    win_DrawObjectNum(0x1914);
                    win_GetObjRect(0x1914, &r);
                    y = r.bottom;
                    win_GetObjRect(0x1902, &r);
                    for (id = 0x1b6c; id <= 0x1b6e; id++) {
                        win_DrawBitMap(r.left, y, id);
                        gr_BitMapSize(&sz, id);
                        y += sz.v;
                    }
                    win_DrawObjectNum(0x1915);
                } else
                    win_DrawBitMap(fd_50F6_10D2.left - ((g_5A97 & 1) != 0), fd_50F6_10D2.top, 0x1b5a);
            }
        }
        g_2A54 = YardMode;
    }
    if (flags & 2) {
        newMapForce = 0;
        yard_draw_content_totals();
        fd_55B3_29A2 = newMapForce;
        DrawYardCursor();
    }
}

extern int _fastcall win_IsWinOpen(int win);
extern void far clip_SetWin(int win);
extern void far clip_Off(void);

void far yard_refresh_message_area(void)
{
    if (win_IsWinOpen(0x1900) && fd_55B3_29A2) {
        clip_SetWin(0x1900);
        EraseYardCursor();
        yard_update_message();
        win_DrawObjectNum(0x1914);
        DrawYardCursor();
        clip_Off();
        fd_55B3_29A2 = 0;
    }
}

void far DrawYard(void)
{
    if (win_IsWinOpen(0x1900)) {
        clip_SetWin(0x1900);
        win_DrawYardWindow(7);
        clip_Off();
    }
}

void far UpdateYard(void)
{
    DrawYard();
}

typedef char far * far *Handle;
extern int far BoyX;
extern int far BoyY;
extern int far BoyFrame;
extern Handle far yardAnimHandle;
extern void far hanim_SetObjectPos(int x, int y, int pic, Handle h, int id, int pri);
extern int far hanim_AddAnimObject(Handle h, int x, int y, int pic, int pri);
extern int far GamePaused;
extern long far MacTickCount(void);
extern long far BoyMsgCnt;
extern int far BoyMessOn;
extern void far hanim_RemoveAnimObject(Handle h, int id);
extern void far mem_Free(long h);
extern void far font_SetFont(int font);
extern long far MakeBalloon(char far *msg, int flags);
extern int far BoyMsgOffset;
extern char far * far * far BoyMsgs;

void far DrawSimKid(void)
{
    struct Pt sz;
    int x, y;

    x = BoyX;
    y = BoyY;
    if (BoyFrame < 12) {
        x += kidX[BoyFrame];
        y += kidY[BoyFrame];
    } else if (BoyFrame < 24) {
        x += kidX[BoyFrame + 4];
        y += kidY[BoyFrame - 4];
    } else if (BoyFrame < 200) {
        x += kidX[BoyFrame - 68];
        y += kidY[BoyFrame - 68];
    }
    if (g_3DB2 == 320) {
        x = (x >> 1) + 5;
        y = (y >> 1) + 6;
    }
    x += fd_50F6_10D2.left;
    y += fd_50F6_10D2.top;
    if (g_2A2A != -1)
        hanim_SetObjectPos(x, y, BoyFrame + 0x1f40, yardAnimHandle, g_2A2A, -1);
    else
        g_2A2A = hanim_AddAnimObject(yardAnimHandle, x, y, BoyFrame + 0x1f40, -1);
    if (GamePaused == 0 && MacTickCount() > BoyMsgCnt)
        BoyMessOn = 0;
    if (g_2A3E != -1) {
        hanim_RemoveAnimObject(yardAnimHandle, g_2A3E);
        g_2A3E = -1;
    }
    if (g_2A36) {
        mem_Free(g_2A36);
        g_2A36 = 0;
    }
    if (BoyMessOn) {
        font_SetFont(2);
        g_2A36 = MakeBalloon(BoyMsgs[BoyMsgOffset], 0);
        font_SetFont(0);
        gr_BitMapSize(&sz, 30000);
        y = BoyY;
        if (g_3DB2 == 320)
            y = (y >> 1) + 6;
        else
            x += 4;
        y += fd_50F6_10D2.top - sz.v;
        if (g_2A3E != -1)
            hanim_SetObjectPos(x, y, 30000, yardAnimHandle, g_2A3E, 999);
        else
            g_2A3E = hanim_AddAnimObject(yardAnimHandle, x, y, 30000, 999);
    }
}

extern int far DogX;
extern int far DogY;
extern int far ForSaleState;
extern int far DogFrame;

void far DrawDog(void)
{
    int x, y;

    x = DogX;
    y = DogY;
    if (ForSaleState == 0) {
        if (DogFrame < 12) {
            x += dogWalkX[DogFrame];
            y += dogWalkY[DogFrame];
        } else {
            x += kidX[DogFrame - 20];
            y += kidX[DogFrame - 16];
        }
        if (g_3DB2 == 320) {
            x = (x >> 1) + 5;
            y = (y >> 1) + 6;
        }
        x += fd_50F6_10D2.left;
        y += fd_50F6_10D2.top;
        if (g_2A30 != -1)
            hanim_SetObjectPos(x, y, DogFrame + 0x2134, yardAnimHandle, g_2A30, -1);
        else
            g_2A30 = hanim_AddAnimObject(yardAnimHandle, x, y, DogFrame + 0x2134, -1);
    }
}

extern int far BirdX;
extern int far BirdY;
extern int far BirdFrame;

void far DrawSimBird(void)
{
    int x, y;

    x = BirdX - 10;
    y = BirdY - 3;
    if (BirdFrame) {
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
        hanim_SetObjectPos(x, y, BirdFrame + 0x4e2, yardAnimHandle, g_2A2E, -1);
    else
        g_2A2E = hanim_AddAnimObject(yardAnimHandle, x, y, BirdFrame + 0x4e2, -1);
}

extern int far CatX;
extern int far CatY;
extern int far CatFrame;

void far DrawSimCat(void)
{
    int x, y;

    x = CatX;
    y = CatY;
    if (CatFrame >= 10) {
        if (CatFrame < 20) {
            x += catOfs[CatFrame + 2];
            y += catOfs[CatFrame + 6];
        } else {
            x += catOfs[CatFrame];
            y += catOfs[CatFrame + 10];
        }
    }
    if (g_3DB2 == 320) {
        x = (x >> 1) + 5;
        y = (y >> 1) + 6;
    }
    x += fd_50F6_10D2.left;
    y += fd_50F6_10D2.top;
    if (g_2A2C != -1)
        hanim_SetObjectPos(x, y, CatFrame + 0x514, yardAnimHandle, g_2A2C, -1);
    else
        g_2A2C = hanim_AddAnimObject(yardAnimHandle, x, y, CatFrame + 0x514, -1);
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
        hanim_SetObjectPos(x, y, 0x4ec, yardAnimHandle, g_2A34, -1);
    else
        g_2A34 = hanim_AddAnimObject(yardAnimHandle, x, y, 0x4ec, -1);
}

extern int far BoyHere;

/* DrawMower: the final position goes to separate h, v; x and y then die before the call and
 * x is allocated to BX (frame 8 keeps the h/v homes), as in the original (worker resF). */
void far DrawMower(void)
{
    int frame, x, y, h, v;

    frame = 0;
    if (BoyHere == 3 || BoyHere == 4) {
        if (GamePaused == 0)
            myBeginSound(0x24, 0, 0x40);
        switch (BoyFrame) {
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
                hanim_RemoveAnimObject(yardAnimHandle, g_2A32);
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
            x = BoyX + 0x13;
        else
            x = BoyX - 0xf;
        y = BoyY + 0xf;
    }
    if (g_3DB2 == 320) {
        x = (x >> 1) + 5;
        y = (y >> 1) + 6;
    }
    h = x + fd_50F6_10D2.left;
    v = y + fd_50F6_10D2.top;
    if (g_2A32 != -1)
        hanim_SetObjectPos(h, v, frame + 0x2260, yardAnimHandle, g_2A32, -1);
    else
        g_2A32 = hanim_AddAnimObject(yardAnimHandle, h, v, frame + 0x2260, -1);
}

extern Handle far hanim_MakeAnimSet(void);
extern int far fd_50F6_38CA[15];
extern int far fd_50F6_38E8[17];
extern int far fd_50F6_390A[17];

extern int far CatOn;
extern int far BirdOn;
extern int far RainOn;
extern void far hanim_RenderAnimSet(Handle h);
extern int far ColonyUpdateFlag;
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
        if (!yardAnimHandle) {
            yardAnimHandle = hanim_MakeAnimSet();
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
        if (CatOn)
            DrawSimCat();
        else if (g_2A2C != -1) {
            hanim_RemoveAnimObject(yardAnimHandle, g_2A2C);
            g_2A2C = -1;
        }
        DrawDog();
        if ((mode || BoyHere) && BoyFrame >= 0)
            DrawSimKid();
        else {
            if (g_2A2A != -1) {
                hanim_RemoveAnimObject(yardAnimHandle, g_2A2A);
                g_2A2A = -1;
            }
            if (g_2A3E != -1) {
                hanim_RemoveAnimObject(yardAnimHandle, g_2A3E);
                g_2A3E = -1;
                mem_Free(g_2A36);
                g_2A36 = 0;
            }
        }
        DrawMower();
        if (BirdOn)
            DrawSimBird();
        else if (g_2A2E != -1) {
            hanim_RemoveAnimObject(yardAnimHandle, g_2A2E);
            g_2A2E = -1;
        }
        if (ForSaleState)
            DrawForSale();
        if (RainOn)
            DrawRain();
        else
            for (i = 0; i <= 14; i++)
                if (fd_50F6_38CA[i] != -1) {
                    hanim_RemoveAnimObject(yardAnimHandle, fd_50F6_38CA[i]);
                    fd_50F6_38CA[i] = -1;
                }
        DrawSwarm();
        DrawAnimYardMessage();
        hanim_RenderAnimSet(yardAnimHandle);
    } else {
        ColonyUpdateFlag = 0;
        if (mode == 2)
            DrawSimColonies(mode);
        else
            DrawColonyBars(mode);
    }
    DrawYardCursor();
}

extern long far font_make_display_bitmap(long text);
extern int far out_buffer;

void far DrawAnimYardMessage(void)
{
    if (g_2A40 != -1) {
        hanim_RemoveAnimObject(yardAnimHandle, g_2A40);
        g_2A40 = -1;
    }
    if (g_2A3A) {
        mem_Free(g_2A3A);
        g_2A3A = 0;
    }
    if (mapMessage) {
        font_SetFont(2);
        g_2A3A = font_make_display_bitmap(mapMessage);
        font_SetFont(0);
        g_2A40 = hanim_AddAnimObject(yardAnimHandle,
                             (fd_50F6_10D2.right - out_buffer + fd_50F6_10D2.left) / 2,
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
            hanim_SetObjectPos(x, y, 0x1b5d, yardAnimHandle, fd_50F6_38CA[i], 0x8000);
        else
            fd_50F6_38CA[i] = hanim_AddAnimObject(yardAnimHandle, x, y, 0x1b5d, 1000);
    }
}

extern int far MapMode;
extern int far SwarmCentY;
extern int far SwarmCentX;
extern int far SwarmCntB;
extern signed char far fd_50F6_0F46[];
extern signed char far fd_50F6_0F84[];
int far TooFar(int x, int y);
extern int far SRand16(void);
extern int far SwarmCntR;
extern int far QueenStorageR;
extern signed char far fd_50F6_0FC6[];
extern signed char far fd_50F6_1008[];

void far DrawSwarm(void)
{
    int i, x, y;

    if (MapMode == 0) {
        SwarmCentY = CurYardPnt[1] * 10 + 0x2e;
        SwarmCentX = CurYardPnt[0] * 28 - CurYardPnt[1] * 10 + 0xb2;
        for (i = 0; i < SwarmCntB; i++) {
            if (i >= 16 || QueenStorageB <= i)
                break;
            if (TooFar(fd_50F6_0F46[i], fd_50F6_0F84[i])) {
                fd_50F6_0F46[i] = SRand16() - 10;
                fd_50F6_0F84[i] = SRand16() - 10;
            }
            fd_50F6_0F46[i] += SRand1(3) - 1;
            x = fd_50F6_0F46[i] + SwarmCentX;
            fd_50F6_0F84[i] += SRand1(3) - 1;
            y = fd_50F6_0F84[i] + SwarmCentY;
            if (g_3DB2 == 320) {
                x = (x >> 1) + 5;
                y = (y >> 1) + 6;
            }
            x += fd_50F6_10D2.left;
            y += fd_50F6_10D2.top;
            if (fd_50F6_38E8[i] != -1)
                hanim_SetObjectPos(x, y, 0x1b5e, yardAnimHandle, fd_50F6_38E8[i], -1);
            else
                fd_50F6_38E8[i] = hanim_AddAnimObject(yardAnimHandle, x, y, 0x1b5e, -1);
        }
        for (; i < 16; i++)
            if (fd_50F6_38E8[i] != -1) {
                hanim_RemoveAnimObject(yardAnimHandle, fd_50F6_38E8[i]);
                fd_50F6_38E8[i] = -1;
            }
        for (i = 0; i < SwarmCntR; i++) {
            if (i >= 16 || QueenStorageR <= i)
                break;
            if (TooFar(fd_50F6_0FC6[i], fd_50F6_1008[i]))
                fd_50F6_1008[i] = fd_50F6_0FC6[i] = 0;
            fd_50F6_0FC6[i] += SRand1(3) - 1;
            x = fd_50F6_0FC6[i] + SwarmCentX;
            fd_50F6_1008[i] += SRand1(3) - 1;
            y = fd_50F6_1008[i] + SwarmCentY;
            if (g_3DB2 == 320) {
                x = (x >> 1) + 5;
                y = (y >> 1) + 6;
            }
            x += fd_50F6_10D2.left;
            y += fd_50F6_10D2.top;
            if (fd_50F6_390A[i] != -1)
                hanim_SetObjectPos(x, y, 0x1b5f, yardAnimHandle, fd_50F6_390A[i], -1);
            else
                fd_50F6_390A[i] = hanim_AddAnimObject(yardAnimHandle, x, y, 0x1b5f, -1);
        }
        for (; i < 16; i++)
            if (fd_50F6_390A[i] != -1) {
                hanim_RemoveAnimObject(yardAnimHandle, fd_50F6_390A[i]);
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
extern void far TrapFill(struct Pt far *pts, int a, int b);
extern void far clip_Pop(void);


extern unsigned char far YMapPopR[12][16];
extern unsigned char far YMapPopB[12][16];
extern int far ConvColor(int color);
extern void far GRectFill(struct Rect far *rect, int color);
extern int far YMapPnt[2];
extern void far WinPrintf(char far *format, ...);
extern void far XferPatch(void);
/*
 * Inverts the highlight of yard patch (x, y): the four-corner outline g_2A42 placed at the
 * patch's projected offset (28*x - 10*y, 10*y) inside the yard rectangle. In the 320-wide mode
 * the offset and the outline are halved and the origin moves by (4, 10).
 *
 * pts[4] is one element past the array. The two stores fall on the frame words of h and v
 * (BP-6, BP-4), which both branches overwrite before the loops read them; see G12 in
 * docs/data-adjacency.md. Hypothesis: the bytes show stores of the full-scale origin to those two
 * words and nothing else; a fifth point is our spelling of them.
 *
 * STEERED (BLOCK-1): the original starts a new basic block between those stores and the raw
 * offsets (the two products are kept in frame words and reloaded). The test with the unused
 * assignment reproduces that boundary and leaves no code; the statement it stands for is unknown.
 * The Windows build has a real test at this point (YardMode < 2 moves the offset left by one).
 */
void far InvertPatch(int x, int y)
{
    struct Pt pts[4];
    int i, v, h;

    clip_Push();
    clip_SetWin(0x1900);
    pts[4].h = x * 28 - y * 10 + fd_50F6_10D2.left;
    pts[4].v = y * 10 + fd_50F6_10D2.top;
    if (g_3DB2 == 320)
        h = 0;
    h = x * 28 - y * 10;
    v = y * 10;
    if (g_3DB2 == 320) {
        h >>= 1;
        v >>= 1;
        h += fd_50F6_10D2.left + 4;
        v += fd_50F6_10D2.top + 10;
        for (i = 0; i < 4; i++) {
            pts[i].h = g_2A42[i * 2] / 2 + h;
            pts[i].v = g_2A42[i * 2 + 1] / 2 + v;
        }
    } else {
        h += fd_50F6_10D2.left;
        v += fd_50F6_10D2.top;
        for (i = 0; i < 4; i++) {
            pts[i].h = g_2A42[i * 2] + h;
            pts[i].v = g_2A42[i * 2 + 1] + v;
        }
    }
    TrapFill(pts, -1, -1);
    clip_Pop();
}



extern unsigned char far YMapPopR[12][16];
extern unsigned char far YMapPopB[12][16];
extern int far ConvColor(int color);

void far DrawSimColonies(int mode)
{
    struct Pt pts[4];
    int x, y, i, c, color, h, v;

    if (mode == 2)
        for (x = 0; x < 12; x++)
            for (y = 0; y < 16; y++) {
                c = YMapPopR[x][y];
                if (YMapPopB[x][y] == 0)
                    color = c == 0 ? 3 : 2;
                else
                    color = c != 0;
                h = x * 28 - y * 10;
                v = y * 10;
                if (g_3DB2 == 320) {
                    h >>= 1;
                    v >>= 1;
                    h += fd_50F6_10D2.left + 4;
                    v += fd_50F6_10D2.top + 10;
                    for (i = 0; i < 4; i++) {
                        pts[i].h = (i >= 2 ? 0 : -1) + g_2A42[i * 2] / 2 + h;
                        pts[i].v = (i >= 2 ? -1 : 1) + g_2A42[i * 2 + 1] / 2 + v;
                    }
                } else {
                    h += fd_50F6_10D2.left;
                    v += fd_50F6_10D2.top;
                    for (i = 0; i < 4; i++) {
                        pts[i].h = g_2A42[i * 2] + h;
                        pts[i].v = g_2A42[i * 2 + 1] + v;
                    }
                }
                TrapFill(pts, ConvColor(g_2ACA[color]), ConvColor(g_2AD2[color]));
            }
}


extern void far GRectFill(struct Rect far *rect, int color);

void far DrawColonyBars(int mode)
{
    struct Rect r;
    int x, y, h, l, t;
    int baseLeft;

    for (x = 0; x < 12; x++)
        for (y = 0; y < 16; y++) {
            h = (YMapPopB[x][y] + 3) >> 2;
            if (h > 0) {
                if (g_3DB2 == 320) {
                    t = y * 10 + 12;
                    l = ((x + 6) * 28 - t) / 2 + fd_50F6_10D2.left + 10;
                    r.bottom = (t + 0x47) / 2 + fd_50F6_10D2.top + 4;
                    r.left = l;
                    r.top = r.bottom - h / 2;
                    r.right = l + 4;
                } else {
                    r.left = (x + 6) * 28 + fd_50F6_10D2.left;
                    r.left -= y * 10;
                    r.bottom = y * 10 + fd_50F6_10D2.top + 0x47;
                    r.top = r.bottom - h;
                    r.right = r.left + 9;
                }
                GRectFill(&r, ConvColor(15));
            }
            h = (YMapPopR[x][y] + 3) >> 2;
            if (h > 0) {
                if (g_3DB2 == 320) {
                    t = y * 10 + 12;
                    l = (x * 28 - t + 0xb4) / 2 + fd_50F6_10D2.left + 10;
                    r.bottom = (t + 0x47) / 2 + fd_50F6_10D2.top + 4;
                    r.left = l;
                    r.top = r.bottom - h / 2;
                    r.right = l + 4;
                } else {
                    baseLeft = x * 28 + (fd_50F6_10D2.left - y * 10);
                    l = baseLeft + 0xb4;
                    r.left = l;
                    r.bottom = y * 10 + fd_50F6_10D2.top + 0x47;
                    r.top = r.bottom - h;
                    r.right = l + 9;
                }
                GRectFill(&r, ConvColor(0x23));
            }
        }
}


extern int far YMapPnt[2];
extern void far WinPrintf(char far *format, ...);
extern void far XferPatch(void);

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
        YMapPnt[0] = x;
        YMapPnt[1] = y;
        if (ev->modifiers & 0x6000)
            XferPatch();
        DrawYardCursor();
    }
}

