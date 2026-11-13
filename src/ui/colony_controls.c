/*
 * Implements caste and activity mode control windows with triangular controls. It maps pointer
 * positions into control levels and draws the resulting production settings.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS: resident code; segment 0798; complete original translation unit.
 * Windows: SIMANT, from recorded function pairs in the Windows symbol inventory.
 * Build profile: msc600ax; /AL /Os /Oe /Og.
 */

#include "rect.h"

struct Pt {
    int x;
    int y;
};

struct TriPoints {
    int apexX;
    int apexY;
    int leftX;
    int leftY;
    int rightX;
    int rightY;
};

struct TriLevel {
    unsigned frac;
    unsigned mid;
    unsigned weight;
};

struct CtlMsg {
    char pad[8];
    struct Pt pt;
    int code;
};

typedef char far * far *Handle;

char g_1B46[4] = { 36, 38, 34, 0 };
char g_1B4A[4] = { 40, 43, 39, 0 };
int casteSet = 0;
int modeSet = 0;
int g_1B52[8] = { 0x8000, 0x8000, 0x8000, 0x8000, 0x8000, 0x8000, 0x8000, 0x8000 };
int g_1B62 = 1;
int g_1B64 = 1;

extern void _fastcall win_GetObjRect(int obj, struct Rect far *rect);
extern unsigned far triWidth;
extern unsigned far triWidthR;
extern unsigned far triWidthL;
extern unsigned far triHeight;
extern long far leftYSlope;

void far InitTriVars(int obj, struct TriPoints far *tri)
{
    struct Rect rect;
    unsigned half;

    win_GetObjRect(obj, &rect);
    triWidth = rect.right - rect.left;
    half = triWidth >> 1;
    triWidthR = half;
    triWidthL = half;
    triHeight = rect.bottom - rect.top;
    leftYSlope = ((long)half << 8) / (long)triHeight;
    tri->apexX = half + rect.left;
    tri->apexY = rect.top;
    tri->leftY = tri->rightY = rect.bottom;
    tri->leftX = rect.left;
    tri->rightX = rect.right;
}

extern struct TriPoints far casteVerts;
void far SetTriLatPoint(struct TriLevel far *level, struct TriPoints far *tri, struct Pt far *out);
extern struct TriLevel far casteLevels;
extern struct Pt far caste_knob_center;
void far win_CasteControlClosed(void);

void far win_CasteControlChanged(void)
{
    InitTriVars(0x130d, &casteVerts);
    SetTriLatPoint(&casteLevels, &casteVerts, &caste_knob_center);
    win_CasteControlClosed();
}

extern struct TriPoints far modeVerts;
extern struct TriLevel far modeLevels;
extern struct Pt far mode_knob_center;
void far win_ModeControlClosed(void);

void far win_ModeControlChanged(void)
{
    InitTriVars(0x120d, &modeVerts);
    SetTriLatPoint(&modeLevels, &modeVerts, &mode_knob_center);
    win_ModeControlClosed();
}

extern void far win_Open(int win);

void far OpenCasteWindow(void)
{
    win_CasteControlChanged();
    win_Open(0x1300);
}

void far OpenModeWindow(void)
{
    win_ModeControlChanged();
    win_Open(0x1200);
}

extern void far clip_SetWin(int win);
extern void far DoWinHelp(int context);
extern int far CasteAuto;
extern void _fastcall win_MakeGroupInvisible(int win, int group);
extern void _fastcall win_MakeObjSelected(int obj);
extern void far * far _fmemcpy(void far *dst, void far *src, unsigned n);
extern struct TriLevel far casteSetLevels[];
void far win_DrawCasteWindow(int flags);
int far IsPointInIsoTri(struct Pt far *pt, struct Rect far *r);
extern void _fastcall win_MakeGroupVisible(int win, int group);
extern int far _fmemcmp(void far *a, void far *b, unsigned n);
void far BoundPointToTri(struct Pt far *pt, struct Rect far *r);
void far GetTriLatDist(struct TriLevel far *level, struct TriPoints far *tri, struct Pt far *pt);
extern void far GetMousePos(struct Pt far *pt);
extern int far StillDown(void);
void far cvtLevels2IdealCaste(int far *ideal);
extern int far IdealCaste[4];
extern void far clip_Off(void);

void far ProcCasteEvent(struct CtlMsg far *msg)
{
    struct Rect rect;
    struct Pt last;

    clip_SetWin(0x1300);
    switch (msg->code - 0x1303) {
    case 0:
        DoWinHelp(0x130e);
        break;
    case 1:
        if (CasteAuto == 0) {
            CasteAuto = 1;
            win_MakeGroupInvisible(0x1300, 4);
        }
        break;
    case 3:
    case 4:
    case 5:
        win_MakeObjSelected(0x1305);
        _fmemcpy(&casteSetLevels[casteSet], &casteLevels, 6);
        casteSet = msg->code - 0x1306;
        _fmemcpy(&casteLevels, &casteSetLevels[casteSet], 6);
        clip_SetWin(0x1300);
        win_DrawCasteWindow(3);
    case 2:
        if (CasteAuto) {
            CasteAuto = 0;
            win_MakeGroupVisible(0x1300, 4);
        }
        break;
    case 10:
        win_GetObjRect(0x130d, &rect);
        if (!IsPointInIsoTri(&msg->pt, &rect))
            break;
        if (CasteAuto) {
            CasteAuto = 0;
            win_MakeObjSelected(0x1305);
            win_MakeGroupVisible(0x1300, 4);
        }
        last.x = -1;
        clip_SetWin(0x1300);
        do {
            if (_fmemcmp(&last, &msg->pt, 4)) {
                last = msg->pt;
                BoundPointToTri(&msg->pt, &rect);
                GetTriLatDist(&casteLevels, &casteVerts, &msg->pt);
                win_DrawCasteWindow(3);
            }
            GetMousePos(&msg->pt);
        } while (StillDown());
        _fmemcpy(&casteSetLevels[casteSet], &casteLevels, 6);
        cvtLevels2IdealCaste(IdealCaste);
        break;
    case 12:
    case 13:
    case 14:
        g_1B64 ^= 1;
        win_DrawCasteWindow(3);
        break;
    }
    clip_Off();
}

extern int far ModeAuto;
extern struct TriLevel far modeSetLevels[];
void far win_DrawModeWindow(int flags);

void far ProcModeEvent(struct CtlMsg far *msg)
{
    struct Rect rect;
    struct Pt last;

    clip_SetWin(0x1200);
    switch (msg->code - 0x1203) {
    case 0:
        DoWinHelp(0x120e);
        break;
    case 1:
        if (ModeAuto == 0) {
            ModeAuto = 1;
            win_MakeGroupInvisible(0x1200, 4);
        }
        break;
    case 3:
    case 4:
    case 5:
        win_MakeObjSelected(0x1205);
        _fmemcpy(&modeSetLevels[modeSet], &modeLevels, 6);
        modeSet = msg->code - 0x1206;
        _fmemcpy(&modeLevels, &modeSetLevels[modeSet], 6);
        clip_SetWin(0x1200);
        win_DrawModeWindow(3);
    case 2:
        if (ModeAuto) {
            ModeAuto = 0;
            win_MakeGroupVisible(0x1200, 4);
        }
        break;
    case 10:
        win_GetObjRect(0x120d, &rect);
        if (!IsPointInIsoTri(&msg->pt, &rect))
            break;
        if (ModeAuto) {
            ModeAuto = 0;
            win_MakeObjSelected(0x1205);
            win_MakeGroupVisible(0x1200, 4);
        }
        last.x = -1;
        clip_SetWin(0x1200);
        do {
            if (_fmemcmp(&last, &msg->pt, 4)) {
                last = msg->pt;
                BoundPointToTri(&msg->pt, &rect);
                GetTriLatDist(&modeLevels, &modeVerts, &msg->pt);
                win_DrawModeWindow(3);
            }
            GetMousePos(&msg->pt);
        } while (StillDown());
        _fmemcpy(&modeSetLevels[modeSet], &modeLevels, 6);
        break;
    case 12:
    case 13:
    case 14:
        g_1B62 ^= 1;
        win_DrawModeWindow(3);
        break;
    }
    clip_Off();
}

int far IsPointInIsoTri(struct Pt far *pt, struct Rect far *r)
{
    int top;
    int bottom;
    int right;
    int left;
    int mid;
    int x;
    int y;

    top = r->top;
    bottom = r->bottom;
    right = r->right;
    left = r->left;
    mid = (right + left) / 2;
    x = pt->x;
    y = pt->y;
    if (y >= bottom || y < top)
        return 0;
    if ((long)(left - mid) * (y - bottom) / (long)(bottom - top) + left > x)
        return 0;
    if ((long)(mid - right) * (y - top) / (long)(top - bottom) + mid < x)
        return 0;
    return 1;
}

void far BoundPointToTri(struct Pt far *pt, struct Rect far *r)
{
    int top;
    int bottom;
    int right;
    int left;
    int mid;
    int x;
    int y;
    int edge;

    top = r->top;
    bottom = r->bottom - 1;
    right = r->right;
    left = r->left;
    mid = (right + left) / 2;
    x = pt->x;
    y = pt->y;
    if (y > bottom)
        y = bottom;
    else if (y < top)
        y = top;
    edge = (long)(left - mid) * (y - bottom) / (long)(bottom - top) + left;
    if (edge > x)
        x = edge;
    else {
        edge = (long)(mid - right) * (y - top) / (long)(top - bottom) + mid;
        if (edge < x)
            x = edge;
    }
    pt->x = x;
    pt->y = y;
}

extern Handle far modeAnimHandle;
void far DrawControlLevels(int win, int unused, int percent);
extern Handle far hanim_MakeAnimSet(void);
extern struct Pt far knobSize;
extern int far hanim_AddAnimObject(Handle h, int x, int y, int pic, int pri);
extern int far mode_knob_anim_index;
extern void far hanim_SetObjectPos(int x, int y, int pic, Handle h, int id, int pri);
extern void far hanim_RenderAnimSet(Handle h);

void far win_DrawModeWindow(int flags)
{
    if (flags & 1) {
        if (!modeAnimHandle)
            clip_SetWin(0x1200);
    }
    if (!(flags & 2))
        return;
    DrawControlLevels(0x1200, 0, g_1B62);
    SetTriLatPoint(&modeLevels, &modeVerts, &mode_knob_center);
    if (!modeAnimHandle) {
        modeAnimHandle = hanim_MakeAnimSet();
        mode_knob_anim_index = hanim_AddAnimObject(modeAnimHandle, mode_knob_center.x - knobSize.x / 2,
                                   mode_knob_center.y - knobSize.y / 2, 0x578, 0);
    } else
        hanim_SetObjectPos(mode_knob_center.x - knobSize.x / 2, mode_knob_center.y - knobSize.y / 2,
                    0x8000, modeAnimHandle, mode_knob_anim_index, 0x8000);
    hanim_RenderAnimSet(modeAnimHandle);
}

extern void far hanim_RemoveAnimSet(Handle h);

void far win_ModeControlClosed(void)
{
    if (modeAnimHandle) {
        hanim_RemoveAnimSet(modeAnimHandle);
        modeAnimHandle = 0;
    }
}

extern Handle far casteAnimHandle;
extern int far fd_50F6_37FA;

void far win_DrawCasteWindow(int flags)
{
    if (flags & 1) {
        if (!casteAnimHandle)
            clip_SetWin(0x1300);
    }
    if (!(flags & 2))
        return;
    DrawControlLevels(0x1300, 0, g_1B64);
    SetTriLatPoint(&casteLevels, &casteVerts, &caste_knob_center);
    if (!casteAnimHandle) {
        casteAnimHandle = hanim_MakeAnimSet();
        fd_50F6_37FA = hanim_AddAnimObject(casteAnimHandle, caste_knob_center.x - knobSize.x / 2,
                                   caste_knob_center.y - knobSize.y / 2, 0x578, 0);
    } else
        hanim_SetObjectPos(caste_knob_center.x - knobSize.x / 2, caste_knob_center.y - knobSize.y / 2,
                    0x8000, casteAnimHandle, fd_50F6_37FA, 0x8000);
    hanim_RenderAnimSet(casteAnimHandle);
}

void far win_CasteControlClosed(void)
{
    if (casteAnimHandle) {
        hanim_RemoveAnimSet(casteAnimHandle);
        casteAnimHandle = 0;
    }
}

extern int near gfx_screen_width_pixels;
extern void far font_SetFont(int font);
extern int far ModePopB[6];
extern int far CastePopB;
extern void far win_PrintfAtObj(int obj, char far *format, ...);
extern void far win_ClearObjToEOL(int obj);
extern int far ConvColor(int color);
extern void far GRectFill(struct Rect far *r, int color);
extern void (far * near gfx_set_attributes_hook)(int fore, int back, int pattern);
extern void far GRectOutline(struct Rect far *r, int width);

void far DrawControlLevels(int win, int unused, int percent)
{
    struct Rect rect;
    struct Rect r;
    char far *colors;
    unsigned far *levels;
    int h;
    long total;
    int w;
    int i;
    int obj;
    long val;
    int color;

    font_SetFont(gfx_screen_width_pixels == 0x140 ? 0 : 4);
    win_GetObjRect((win & 0xff00) + 12, &rect);
    w = (rect.right - rect.left) / 5;
    h = rect.bottom - rect.top;
    if (win == 0x1200) {
        levels = (unsigned far *)&modeLevels;
        colors = g_1B4A;
        total = (long)ModePopB[2] + ModePopB[1] + ModePopB[0];
    } else {
        levels = (unsigned far *)&casteLevels;
        colors = g_1B46;
        total = CastePopB;
    }
    for (i = 0; i < 3; i++) {
        obj = (win & 0xff00) + i + 9;
        if (percent) {
            val = (100L * levels[i] + 0x3fff) / 0xffff;
            win_PrintfAtObj(obj, "%-ld%%", val);
        } else {
            val = (levels[i] * (unsigned long)total + 0x3fff) / 0xffff;
            win_PrintfAtObj(obj, "%-ld", val);
        }
        win_ClearObjToEOL(obj);
        r.left = w * i * 2 + rect.left;
        r.right = r.left + w;
        r.bottom = rect.bottom;
        r.top = (long)levels[i] * h / -65535L + rect.bottom;
        if (r.top + 1 < rect.bottom) {
            color = ConvColor(colors[i]);
            GRectFill(&r, color);
            (*gfx_set_attributes_hook)(ConvColor(15), ConvColor(15), 0);
            GRectOutline(&r, 1);
        } else
            r.top = rect.bottom;
        r.bottom = r.top;
        r.top = rect.top - 1;
        GRectFill(&r, ConvColor(0x40));
    }
    font_SetFont(0);
}

/* First declaration retained before the conversion/initialization helpers:
 * its function and parameter identifiers preserve GetTriLatDist's code.
 * This declaration placement is inferred, not a recovered header boundary. */
extern void far gr_BitMapSize(struct Pt far *size, int id);

void far cvtLevels2IdealCaste(int far *ideal)
{
    ideal[0] = (100UL * (&casteLevels.frac)[1] + 0x3fff) / 0xffff;
    ideal[1] = (100UL * (&casteLevels.frac)[2] + 0x3fff) / 0xffff;
    ideal[2] = (50UL * (&casteLevels.frac)[0] + 0x3fff) / 0xffff;
    ideal[3] = (50UL * (&casteLevels.frac)[0] + 0x3fff) / 0xffff;
}

void far GetTriLatDist(struct TriLevel far *level, struct TriPoints far *tri, struct Pt far *pt)
{
    int dx;
    int dy;
    int row;
    unsigned w;

    dx = pt->x - tri->leftX;
    dy = pt->y - tri->apexY;
    if ((unsigned)dy > triHeight - 2)
        level->frac = 0;
    else
        level->frac = (long)(triHeight - dy - 2) * 0xffffL / (long)(triHeight - 2);
    w = (unsigned long)level->frac * triWidthL / 0xffffUL;
    row = triWidth - w * 2;
    if (row <= 2) {
        level->weight = level->mid = 0;
        return;
    }
    if (dx - (int)w >= row - 2)
        level->weight = 0xffff - level->frac;
    else if (dx - (int)w <= 2)
        level->weight = 0;
    else
        level->weight = (0xffffL - level->frac) * (long)(dx - (int)w) / (long)(row - 2);
    level->mid = 0xffff - level->weight - level->frac;
}

void far SetTriLatPoint(struct TriLevel far *level, struct TriPoints far *tri, struct Pt far *out)
{
    unsigned w;
    int row;

    out->y = (triHeight - 2) * (0xffffUL - level->frac) / 0xffffUL + tri->apexY;
    w = (unsigned long)triWidthL * level->frac / 0xffffUL;
    row = triWidth - w * 2;
    if (level->frac == 0xffff || row < 3)
        out->x = tri->apexX + 2;
    else
        out->x = (long)(row - 3) * level->weight / (long)(0xffffU - level->frac) + tri->leftX + w + 2;
}

extern int far ShowPercentMode;
extern int far ShowPercentCaste;
extern int far modeButtonState;
extern int far casteButtonState;
extern int far modeLevelDefaults[3];
extern int far casteLevelDefaults[3];

void far initControls(void)
{
    struct Rect rect;
    int i;

    gr_BitMapSize(&knobSize, 0x578);
    win_GetObjRect(0x120d, &rect);
    ModeAuto = 1;
    CasteAuto = 1;
    ShowPercentMode = 1;
    ShowPercentCaste = 1;
    modeButtonState = -1;
    casteButtonState = -1;
    for (i = 0; i < 3; i++) {
        (&modeLevels.frac)[i] = modeLevelDefaults[i];
        (&modeSetLevels[0].frac)[i] = modeLevelDefaults[i];
        (&casteLevels.frac)[i] = casteLevelDefaults[i];
        (&casteSetLevels[0].frac)[i] = casteLevelDefaults[i];
    }
    win_ModeControlChanged();
    win_CasteControlChanged();
    cvtLevels2IdealCaste(IdealCaste);
}
