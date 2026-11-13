/*
 * Handles yard window events and renders the yard. It draws animated people, animals, weather,
 * swarms and colony population bars.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS: overlay section 13 (S13); segment 384C; complete original translation unit.
 * Windows: ANTEDIT, from recorded function pairs in the Windows symbol inventory. Some pairs are
 * HIGH confidence, not confirmed.
 */

#include "audio_ids.h"
#include "flags_ids.h"
#include "pictures_ids.h"
#include "windows_ids.h"

#include <string.h>

#include "event.h"

#include "rect.h"

#include "pt.h"

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
    case OBJ_YARD_VIEWPORT:
        YardArea(ev);
        break;
    case OBJ_YARD_PATCH:
        YardToMap();
        break;
    case OBJ_YARD_YARD_HOUSE:
        if (YardMode < 2)
            SetYardMode(YardMode ^ 1);
        else
            SetYardMode(0);
        break;
    case OBJ_YARD_STRATEGIC:
        SetYardMode(2);
        break;
    case OBJ_YARD_GRAPHIC:
        SetYardMode(3);
        break;
    case OBJ_YARD_MATING:
        if (CurGameType != 2) {
            myBeginSound(SND_REJECT, 0, 0x7e);
            EditMessage(WindPromptStrs[15], 180L, 1);
        } else {
            n = CastePopB[3] + CastePopB[4];
            if (MeType == 0x40 || MeType == 0x20)
                n--;
            if (n <= 0) {
                myBeginSound(SND_REJECT, 0, 0x7e);
                EditMessage(WindPromptStrs[5], 180L, 1);
            } else {
                FlyAwayB = 200;
                EditMessage(WindPromptStrs[6], 180L, 1);
            }
        }
        break;
    case OBJ_YARD_DROP_QUEEN_MODE:
        LayDownQueenMode = 1;
        break;
    case OBJ_YARD_PLACE_QUEEN_MODE:
        LayDownQueenMode = 0;
        break;
    case OBJ_YARD_PLACE_QUEEN:
        win_MakeObjSelected(OBJ_YARD_PLACE_QUEEN_MODE);
        win_MakeObjSelected(OBJ_YARD_PLACE_QUEEN);
        PlaceQueenInYard();
        UpdateYard();
        win_MakeObjUnselected(OBJ_YARD_PLACE_QUEEN);
        break;
    case OBJ_YARD_HELP:
        DoWinHelp(OBJ_YARD_HELP_PICTURE);
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
extern long far map_message_deadline;
extern int far map_yard_redraw_pending;
extern void _fastcall win_SetColorNum(int color);
extern struct Rect far map_viewport_rect;
extern void far ui_draw_centered_clipped_text(long msg, struct Rect far *rect, int y);

void far yard_update_message(void)
{
    if (mapMessage) {
        if (TickCount() > map_message_deadline) {
            if (mapMessage)
                map_yard_redraw_pending = 1;
            mapMessage = 0;
        } else {
            win_SetColorNum(3);
            if (YardMode > 1)
                ui_draw_centered_clipped_text(mapMessage, &map_viewport_rect, map_viewport_rect.top + 4);
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
    win_ObjFormatPrint(OBJ_YARD_STORED_QUEENS, QueenStorageB);
    win_ObjFormatPrint(OBJ_YARD_BLACK_COLONIES, ColonyTotalBlack);
    win_ObjFormatPrint(OBJ_YARD_RED_COLONIES, ColonyTotalRed);
}

extern int near gfx_screen_width_pixels;
extern char near gfx_display_mode;
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
            if (YardMode > 2 || map_yard_redraw_pending || !(flags & 4) || YardMode != g_2A54) {
                if (gfx_screen_width_pixels != 320 && !(gfx_display_mode & 1)) {
                    yard_update_message();
                    win_DrawObjectNum(OBJ_YARD_MESSAGE);
                    win_GetObjRect(OBJ_YARD_MESSAGE, &r);
                    y = r.bottom;
                    win_GetObjRect(OBJ_YARD_VIEWPORT, &r);
                    for (id = 0x1b6c; id <= 0x1b6e; id++) {
                        win_DrawBitMap(r.left, y, id);
                        gr_BitMapSize(&sz, id);
                        y += sz.y;
                    }
                    win_DrawObjectNum(OBJ_YARD_MESSAGE_HORIZONTAL_FRAME);
                } else
                    win_DrawBitMap(map_viewport_rect.left - ((gfx_display_mode & 1) != 0), map_viewport_rect.top, PIC_YARD_DRAW_BACKGROUND);
            }
        }
        g_2A54 = YardMode;
    }
    if (flags & 2) {
        newMapForce = 0;
        yard_draw_content_totals();
        map_yard_redraw_pending = newMapForce;
        DrawYardCursor();
    }
}

extern int _fastcall win_IsWinOpen(int win);
extern void far clip_SetWin(int win);
extern void far clip_Off(void);

void far yard_refresh_message_area(void)
{
    if (win_IsWinOpen(WIN_YARD) && map_yard_redraw_pending) {
        clip_SetWin(WIN_YARD);
        EraseYardCursor();
        yard_update_message();
        win_DrawObjectNum(OBJ_YARD_MESSAGE);
        DrawYardCursor();
        clip_Off();
        map_yard_redraw_pending = 0;
    }
}

void far DrawYard(void)
{
    if (win_IsWinOpen(WIN_YARD)) {
        clip_SetWin(WIN_YARD);
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
    if (gfx_screen_width_pixels == 320) {
        x = (x >> 1) + 5;
        y = (y >> 1) + 6;
    }
    x += map_viewport_rect.left;
    y += map_viewport_rect.top;
    if (g_2A2A != -1)
        hanim_SetObjectPos(x, y, BoyFrame + PIC_YARD_HUMAN_FRAME_BASE, yardAnimHandle, g_2A2A, -1);
    else
        g_2A2A = hanim_AddAnimObject(yardAnimHandle, x, y, BoyFrame + PIC_YARD_HUMAN_FRAME_BASE, -1);
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
        gr_BitMapSize(&sz, PIC_HUMAN_BALLOON_BUFFER);
        y = BoyY;
        if (gfx_screen_width_pixels == 320)
            y = (y >> 1) + 6;
        else
            x += 4;
        y += map_viewport_rect.top - sz.y;
        if (g_2A3E != -1)
            hanim_SetObjectPos(x, y, PIC_HUMAN_BALLOON_BUFFER, yardAnimHandle, g_2A3E, 999);
        else
            g_2A3E = hanim_AddAnimObject(yardAnimHandle, x, y, PIC_HUMAN_BALLOON_BUFFER, 999);
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
        if (gfx_screen_width_pixels == 320) {
            x = (x >> 1) + 5;
            y = (y >> 1) + 6;
        }
        x += map_viewport_rect.left;
        y += map_viewport_rect.top;
        if (g_2A30 != -1)
            hanim_SetObjectPos(x, y, DogFrame + PIC_YARD_DOG_FRAME_BASE, yardAnimHandle, g_2A30, -1);
        else
            g_2A30 = hanim_AddAnimObject(yardAnimHandle, x, y, DogFrame + PIC_YARD_DOG_FRAME_BASE, -1);
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
    if (gfx_screen_width_pixels == 320) {
        x = (x >> 1) + 5;
        y = (y >> 1) + 6;
    }
    x += map_viewport_rect.left;
    y += map_viewport_rect.top;
    if (g_2A2E != -1)
        hanim_SetObjectPos(x, y, BirdFrame + PIC_YARD_BIRD_FRAME_BASE, yardAnimHandle, g_2A2E, -1);
    else
        g_2A2E = hanim_AddAnimObject(yardAnimHandle, x, y, BirdFrame + PIC_YARD_BIRD_FRAME_BASE, -1);
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
    if (gfx_screen_width_pixels == 320) {
        x = (x >> 1) + 5;
        y = (y >> 1) + 6;
    }
    x += map_viewport_rect.left;
    y += map_viewport_rect.top;
    if (g_2A2C != -1)
        hanim_SetObjectPos(x, y, CatFrame + PIC_YARD_CAT_FRAME_BASE, yardAnimHandle, g_2A2C, -1);
    else
        g_2A2C = hanim_AddAnimObject(yardAnimHandle, x, y, CatFrame + PIC_YARD_CAT_FRAME_BASE, -1);
}

void far DrawForSale(void)
{
    int x, y;

    x = 0xaa;
    y = 0xba;
    if (gfx_screen_width_pixels == 320) {
        x = 0x5a;
        y = 0x63;
    }
    x += map_viewport_rect.left;
    y += map_viewport_rect.top;
    if (g_2A34 != -1)
        hanim_SetObjectPos(x, y, PIC_YARD_FOR_SALE, yardAnimHandle, g_2A34, -1);
    else
        g_2A34 = hanim_AddAnimObject(yardAnimHandle, x, y, PIC_YARD_FOR_SALE, -1);
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
            myBeginSound(SND_MOWER, 0, 0x40);
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
    if (gfx_screen_width_pixels == 320) {
        x = (x >> 1) + 5;
        y = (y >> 1) + 6;
    }
    h = x + map_viewport_rect.left;
    v = y + map_viewport_rect.top;
    if (g_2A32 != -1)
        hanim_SetObjectPos(h, v, frame + PIC_YARD_MOWER_FRAME_BASE, yardAnimHandle, g_2A32, -1);
    else
        g_2A32 = hanim_AddAnimObject(yardAnimHandle, h, v, frame + PIC_YARD_MOWER_FRAME_BASE, -1);
}

extern Handle far hanim_MakeAnimSet(void);
extern int far yard_rain_anim_indices[15];
extern int far yard_black_swarm_anim_indices[17];
extern int far yard_red_swarm_anim_indices[17];

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
            _fmemset(yard_rain_anim_indices, -1, 0x1e);
            _fmemset(yard_black_swarm_anim_indices, -1, 0x22);
            _fmemset(yard_red_swarm_anim_indices, -1, 0x22);
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
                if (yard_rain_anim_indices[i] != -1) {
                    hanim_RemoveAnimObject(yardAnimHandle, yard_rain_anim_indices[i]);
                    yard_rain_anim_indices[i] = -1;
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
                             (map_viewport_rect.right - out_buffer + map_viewport_rect.left) / 2,
                             map_viewport_rect.top + 4, PIC_YARD_MESSAGE_BUFFER, 999);
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
        if (gfx_screen_width_pixels == 320) {
            x = (x >> 1) + 5;
            y = (y >> 1) + 6;
        }
        x += map_viewport_rect.left;
        y += map_viewport_rect.top;
        if (yard_rain_anim_indices[i] != -1)
            hanim_SetObjectPos(x, y, PIC_YARD_RAIN, yardAnimHandle, yard_rain_anim_indices[i], 0x8000);
        else
            yard_rain_anim_indices[i] = hanim_AddAnimObject(yardAnimHandle, x, y, PIC_YARD_RAIN, 1000);
    }
}

extern int far MapMode;
extern int far SwarmCentY;
extern int far SwarmCentX;
extern int far SwarmCntB;
extern signed char far SwarmXB[];
extern signed char far SwarmYB[];
int far TooFar(int x, int y);
extern int far SRand16(void);
extern int far SwarmCntR;
extern int far QueenStorageR;
extern signed char far SwarmXR[];
extern signed char far SwarmYR[];

void far DrawSwarm(void)
{
    int i, x, y;

    if (MapMode == 0) {
        SwarmCentY = CurYardPnt[1] * 10 + 0x2e;
        SwarmCentX = CurYardPnt[0] * 28 - CurYardPnt[1] * 10 + 0xb2;
        for (i = 0; i < SwarmCntB; i++) {
            if (i >= 16 || QueenStorageB <= i)
                break;
            if (TooFar(SwarmXB[i], SwarmYB[i])) {
                SwarmXB[i] = SRand16() - 10;
                SwarmYB[i] = SRand16() - 10;
            }
            SwarmXB[i] += SRand1(3) - 1;
            x = SwarmXB[i] + SwarmCentX;
            SwarmYB[i] += SRand1(3) - 1;
            y = SwarmYB[i] + SwarmCentY;
            if (gfx_screen_width_pixels == 320) {
                x = (x >> 1) + 5;
                y = (y >> 1) + 6;
            }
            x += map_viewport_rect.left;
            y += map_viewport_rect.top;
            if (yard_black_swarm_anim_indices[i] != -1)
                hanim_SetObjectPos(x, y, PIC_YARD_BLACK_SWARM, yardAnimHandle, yard_black_swarm_anim_indices[i], -1);
            else
                yard_black_swarm_anim_indices[i] = hanim_AddAnimObject(yardAnimHandle, x, y, PIC_YARD_BLACK_SWARM, -1);
        }
        for (; i < 16; i++)
            if (yard_black_swarm_anim_indices[i] != -1) {
                hanim_RemoveAnimObject(yardAnimHandle, yard_black_swarm_anim_indices[i]);
                yard_black_swarm_anim_indices[i] = -1;
            }
        for (i = 0; i < SwarmCntR; i++) {
            if (i >= 16 || QueenStorageR <= i)
                break;
            if (TooFar(SwarmXR[i], SwarmYR[i]))
                SwarmYR[i] = SwarmXR[i] = 0;
            SwarmXR[i] += SRand1(3) - 1;
            x = SwarmXR[i] + SwarmCentX;
            SwarmYR[i] += SRand1(3) - 1;
            y = SwarmYR[i] + SwarmCentY;
            if (gfx_screen_width_pixels == 320) {
                x = (x >> 1) + 5;
                y = (y >> 1) + 6;
            }
            x += map_viewport_rect.left;
            y += map_viewport_rect.top;
            if (yard_red_swarm_anim_indices[i] != -1)
                hanim_SetObjectPos(x, y, PIC_YARD_RED_SWARM, yardAnimHandle, yard_red_swarm_anim_indices[i], -1);
            else
                yard_red_swarm_anim_indices[i] = hanim_AddAnimObject(yardAnimHandle, x, y, PIC_YARD_RED_SWARM, -1);
        }
        for (; i < 16; i++)
            if (yard_red_swarm_anim_indices[i] != -1) {
                hanim_RemoveAnimObject(yardAnimHandle, yard_red_swarm_anim_indices[i]);
                yard_red_swarm_anim_indices[i] = -1;
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
    clip_SetWin(WIN_YARD);
    pts[4].x = x * 28 - y * 10 + map_viewport_rect.left;
    pts[4].y = y * 10 + map_viewport_rect.top;
    if (gfx_screen_width_pixels == 320)
        h = 0;
    h = x * 28 - y * 10;
    v = y * 10;
    if (gfx_screen_width_pixels == 320) {
        h >>= 1;
        v >>= 1;
        h += map_viewport_rect.left + 4;
        v += map_viewport_rect.top + 10;
        for (i = 0; i < 4; i++) {
            pts[i].x = g_2A42[i * 2] / 2 + h;
            pts[i].y = g_2A42[i * 2 + 1] / 2 + v;
        }
    } else {
        h += map_viewport_rect.left;
        v += map_viewport_rect.top;
        for (i = 0; i < 4; i++) {
            pts[i].x = g_2A42[i * 2] + h;
            pts[i].y = g_2A42[i * 2 + 1] + v;
        }
    }
    TrapFill(pts, -1, -1);
    clip_Pop();
}




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
                if (gfx_screen_width_pixels == 320) {
                    h >>= 1;
                    v >>= 1;
                    h += map_viewport_rect.left + 4;
                    v += map_viewport_rect.top + 10;
                    for (i = 0; i < 4; i++) {
                        pts[i].x = (i >= 2 ? 0 : -1) + g_2A42[i * 2] / 2 + h;
                        pts[i].y = (i >= 2 ? -1 : 1) + g_2A42[i * 2 + 1] / 2 + v;
                    }
                } else {
                    h += map_viewport_rect.left;
                    v += map_viewport_rect.top;
                    for (i = 0; i < 4; i++) {
                        pts[i].x = g_2A42[i * 2] + h;
                        pts[i].y = g_2A42[i * 2 + 1] + v;
                    }
                }
                TrapFill(pts, ConvColor(g_2ACA[color]), ConvColor(g_2AD2[color]));
            }
}



void far DrawColonyBars(int mode)
{
    struct Rect r;
    int x, y, h, l, t;
    int baseLeft;

    for (x = 0; x < 12; x++)
        for (y = 0; y < 16; y++) {
            h = (YMapPopB[x][y] + 3) >> 2;
            if (h > 0) {
                if (gfx_screen_width_pixels == 320) {
                    t = y * 10 + 12;
                    l = ((x + 6) * 28 - t) / 2 + map_viewport_rect.left + 10;
                    r.bottom = (t + 0x47) / 2 + map_viewport_rect.top + 4;
                    r.left = l;
                    r.top = r.bottom - h / 2;
                    r.right = l + 4;
                } else {
                    r.left = (x + 6) * 28 + map_viewport_rect.left;
                    r.left -= y * 10;
                    r.bottom = y * 10 + map_viewport_rect.top + 0x47;
                    r.top = r.bottom - h;
                    r.right = r.left + 9;
                }
                GRectFill(&r, ConvColor(15));
            }
            h = (YMapPopR[x][y] + 3) >> 2;
            if (h > 0) {
                if (gfx_screen_width_pixels == 320) {
                    t = y * 10 + 12;
                    l = (x * 28 - t + 0xb4) / 2 + map_viewport_rect.left + 10;
                    r.bottom = (t + 0x47) / 2 + map_viewport_rect.top + 4;
                    r.left = l;
                    r.top = r.bottom - h / 2;
                    r.right = l + 4;
                } else {
                    baseLeft = x * 28 + (map_viewport_rect.left - y * 10);
                    l = baseLeft + 0xb4;
                    r.left = l;
                    r.bottom = y * 10 + map_viewport_rect.top + 0x47;
                    r.top = r.bottom - h;
                    r.right = l + 9;
                }
                GRectFill(&r, ConvColor(0x23));
            }
        }
}



void far YardArea(struct Event far *ev)
{
    int x, y;

    y = ev->v - map_viewport_rect.top;
    x = ev->h - map_viewport_rect.left;
    if (gfx_screen_width_pixels == 320) {
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
        if (ev->modifiers & EVENT_MOD_DOUBLE_CLICK_MASK)
            XferPatch();
        DrawYardCursor();
    }
}

