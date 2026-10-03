#include "dos_types.h"
#include "portable/whole_program/platform/dos_memory.h"
#include "portable/whole_program/platform/dos_io.h"
#include "portable/whole_program/platform/graphics_source_slots.h"
#include "portable/whole_program/platform/graphics_source_fields.h"
#include "simulation_state_50f6_v7.h"
#include "native_owners.h"
#include "triangle_dimensions_v1.h"
#include "portable/whole_program/state/tri_control_state.h"
#pragma pack(push, 2)
/* Root module 0798: caste/mode control triangles (Win16 InitTriVars .. initControls unit). */

struct Rect {
    int16_t left;
    int16_t top;
    int16_t right;
    int16_t bottom;
};

struct Pt {
    int16_t x;
    int16_t y;
};

struct TriPoints {
    int16_t apexX;
    int16_t apexY;
    int16_t leftX;
    int16_t leftY;
    int16_t rightX;
    int16_t rightY;
};

struct TriLevel {
    uint16_t frac;
    uint16_t mid;
    uint16_t weight;
};

struct CtlMsg {
    char pad[8];
    struct Pt pt;
    int16_t code;
};

typedef char  *  *Handle;

char g_1B46[4] = { 36, 38, 34, 0 };
char g_1B4A[4] = { 40, 43, 39, 0 };
int16_t g_1B4E = 0;
int16_t g_1B50 = 0;
int16_t g_1B52[8] = { 0x8000, 0x8000, 0x8000, 0x8000, 0x8000, 0x8000, 0x8000, 0x8000 };
int16_t g_1B62 = 1;
int16_t g_1B64 = 1;

extern void  win_GetObjRect(int16_t obj, struct Rect  *rect);
extern int32_t  fd_50F6_382E;

void  InitTriVars(int16_t obj, struct TriPoints  *tri)
{
    struct Rect rect;
    uint16_t half;

    win_GetObjRect(obj, &rect);
    native_triangle_triWidth_v1 = rect.right - rect.left;
    half = native_triangle_triWidth_v1 >> 1;
    native_triangle_triWidthR_v1 = half;
    native_triangle_triWidthL_v1 = half;
    native_triangle_triHeight_v1 = rect.bottom - rect.top;
    fd_50F6_382E = ((int32_t)half << 8) / (int32_t)native_triangle_triHeight_v1;
    tri->apexX = half + rect.left;
    tri->apexY = rect.top;
    tri->leftY = tri->rightY = rect.bottom;
    tri->leftX = rect.left;
    tri->rightX = rect.right;
}


void  SetTriLatPoint(struct TriLevel  *level, struct TriPoints  *tri, struct Pt  *out);
void  win_CasteControlClosed(void);

void  win_CasteControlChanged(void)
{
    InitTriVars(0x130d, &fd_50F6_3822);
    SetTriLatPoint(&(*((struct TriLevel *)native_sim_state_casteLevels.raw_bytes)), &fd_50F6_3822, &fd_50F6_022E);
    win_CasteControlClosed();
}



void  win_ModeControlClosed(void);

void  win_ModeControlChanged(void)
{
    InitTriVars(0x120d, &fd_50F6_3816);
    SetTriLatPoint(&(*((struct TriLevel *)native_sim_state_modeLevels.raw_bytes)), &fd_50F6_3816, &fd_50F6_0358);
    win_ModeControlClosed();
}

extern void  win_Open(int16_t win);

void  OpenCasteWindow(void)
{
    win_CasteControlChanged();
    win_Open(0x1300);
}

void  OpenModeWindow(void)
{
    win_ModeControlChanged();
    win_Open(0x1200);
}

extern void  clip_SetWin(int16_t win);
extern void  DoWinHelp(int16_t context);
extern int16_t  CasteAuto;
extern void  win_MakeGroupInvisible(int16_t win, int16_t group);
extern void  win_MakeObjSelected(int16_t obj);

extern struct TriLevel  fd_3D57_07F2[];
void  win_DrawCasteWindow(int16_t flags);
int16_t  IsPointInIsoTri(struct Pt  *pt, struct Rect  *r);
extern void  win_MakeGroupVisible(int16_t win, int16_t group);

void  BoundPointToTri(struct Pt  *pt, struct Rect  *r);
void  GetTriLatDist(struct TriLevel  *level, struct TriPoints  *tri, struct Pt  *pt);
extern void  f_1FD2_04D0(struct Pt  *pt);
extern int16_t  StillDown(void);
void  cvtLevels2IdealCaste(int16_t  *ideal);
extern int16_t  IdealCaste[4];
extern void  clip_Off(void);

void  ProcCasteEvent(struct CtlMsg  *msg)
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
        _fmemcpy(&fd_3D57_07F2[g_1B4E], &(*((struct TriLevel *)native_sim_state_casteLevels.raw_bytes)), 6);
        g_1B4E = msg->code - 0x1306;
        _fmemcpy(&(*((struct TriLevel *)native_sim_state_casteLevels.raw_bytes)), &fd_3D57_07F2[g_1B4E], 6);
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
                GetTriLatDist(&(*((struct TriLevel *)native_sim_state_casteLevels.raw_bytes)), &fd_50F6_3822, &msg->pt);
                win_DrawCasteWindow(3);
            }
            f_1FD2_04D0(&msg->pt);
        } while (StillDown());
        _fmemcpy(&fd_3D57_07F2[g_1B4E], &(*((struct TriLevel *)native_sim_state_casteLevels.raw_bytes)), 6);
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

extern struct TriLevel  fd_3D57_0810[];
void  win_DrawModeWindow(int16_t flags);

void  ProcModeEvent(struct CtlMsg  *msg)
{
    struct Rect rect;
    struct Pt last;

    clip_SetWin(0x1200);
    switch (msg->code - 0x1203) {
    case 0:
        DoWinHelp(0x120e);
        break;
    case 1:
        if (native_state_ModeAuto.signed_value == 0) {
            native_state_ModeAuto.signed_value = 1;
            win_MakeGroupInvisible(0x1200, 4);
        }
        break;
    case 3:
    case 4:
    case 5:
        win_MakeObjSelected(0x1205);
        _fmemcpy(&fd_3D57_0810[g_1B50], &(*((struct TriLevel *)native_sim_state_modeLevels.raw_bytes)), 6);
        g_1B50 = msg->code - 0x1206;
        _fmemcpy(&(*((struct TriLevel *)native_sim_state_modeLevels.raw_bytes)), &fd_3D57_0810[g_1B50], 6);
        clip_SetWin(0x1200);
        win_DrawModeWindow(3);
    case 2:
        if (native_state_ModeAuto.signed_value) {
            native_state_ModeAuto.signed_value = 0;
            win_MakeGroupVisible(0x1200, 4);
        }
        break;
    case 10:
        win_GetObjRect(0x120d, &rect);
        if (!IsPointInIsoTri(&msg->pt, &rect))
            break;
        if (native_state_ModeAuto.signed_value) {
            native_state_ModeAuto.signed_value = 0;
            win_MakeObjSelected(0x1205);
            win_MakeGroupVisible(0x1200, 4);
        }
        last.x = -1;
        clip_SetWin(0x1200);
        do {
            if (_fmemcmp(&last, &msg->pt, 4)) {
                last = msg->pt;
                BoundPointToTri(&msg->pt, &rect);
                GetTriLatDist(&(*((struct TriLevel *)native_sim_state_modeLevels.raw_bytes)), &fd_50F6_3816, &msg->pt);
                win_DrawModeWindow(3);
            }
            f_1FD2_04D0(&msg->pt);
        } while (StillDown());
        _fmemcpy(&fd_3D57_0810[g_1B50], &(*((struct TriLevel *)native_sim_state_modeLevels.raw_bytes)), 6);
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

int16_t  IsPointInIsoTri(struct Pt  *pt, struct Rect  *r)
{
    int16_t top;
    int16_t bottom;
    int16_t right;
    int16_t left;
    int16_t mid;
    int16_t x;
    int16_t y;

    top = r->top;
    bottom = r->bottom;
    right = r->right;
    left = r->left;
    mid = (right + left) / 2;
    x = pt->x;
    y = pt->y;
    if (y >= bottom || y < top)
        return 0;
    if ((int32_t)(left - mid) * (y - bottom) / (int32_t)(bottom - top) + left > x)
        return 0;
    if ((int32_t)(mid - right) * (y - top) / (int32_t)(top - bottom) + mid < x)
        return 0;
    return 1;
}

void  BoundPointToTri(struct Pt  *pt, struct Rect  *r)
{
    int16_t top;
    int16_t bottom;
    int16_t right;
    int16_t left;
    int16_t mid;
    int16_t x;
    int16_t y;
    int16_t edge;

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
    edge = (int32_t)(left - mid) * (y - bottom) / (int32_t)(bottom - top) + left;
    if (edge > x)
        x = edge;
    else {
        edge = (int32_t)(mid - right) * (y - top) / (int32_t)(top - bottom) + mid;
        if (edge < x)
            x = edge;
    }
    pt->x = x;
    pt->y = y;
}

void  DrawControlLevels(int16_t win, int16_t unused, int16_t percent);
extern Handle  hanim_MakeAnimSet(void);

extern int16_t  hanim_AddAnimObject(Handle h, int16_t x, int16_t y, int16_t pic, int16_t pri);
extern void  hanim_SetObjectPos(int16_t x, int16_t y, int16_t pic, Handle h, int16_t id, int16_t pri);
extern void  hanim_RenderAnimSet(Handle h);

void  win_DrawModeWindow(int16_t flags)
{
    if (flags & 1) {
        if (!fd_50F6_37F6)
            clip_SetWin(0x1200);
    }
    if (!(flags & 2))
        return;
    DrawControlLevels(0x1200, 0, g_1B62);
    SetTriLatPoint(&(*((struct TriLevel *)native_sim_state_modeLevels.raw_bytes)), &fd_50F6_3816, &fd_50F6_0358);
    if (!fd_50F6_37F6) {
        fd_50F6_37F6 = hanim_MakeAnimSet();
        fd_50F6_37FC = hanim_AddAnimObject(fd_50F6_37F6, fd_50F6_0358.x - knobSize.x / 2,
                                   fd_50F6_0358.y - knobSize.y / 2, 0x578, 0);
    } else
        hanim_SetObjectPos(fd_50F6_0358.x - knobSize.x / 2, fd_50F6_0358.y - knobSize.y / 2,
                    0x8000, fd_50F6_37F6, fd_50F6_37FC, 0x8000);
    hanim_RenderAnimSet(fd_50F6_37F6);
}

extern void  hanim_RemoveAnimSet(Handle h);

void  win_ModeControlClosed(void)
{
    if (fd_50F6_37F6) {
        hanim_RemoveAnimSet(fd_50F6_37F6);
        fd_50F6_37F6 = 0;
    }
}


void  win_DrawCasteWindow(int16_t flags)
{
    if (flags & 1) {
        if (!fd_50F6_37F2)
            clip_SetWin(0x1300);
    }
    if (!(flags & 2))
        return;
    DrawControlLevels(0x1300, 0, g_1B64);
    SetTriLatPoint(&(*((struct TriLevel *)native_sim_state_casteLevels.raw_bytes)), &fd_50F6_3822, &fd_50F6_022E);
    if (!fd_50F6_37F2) {
        fd_50F6_37F2 = hanim_MakeAnimSet();
        fd_50F6_37FA = hanim_AddAnimObject(fd_50F6_37F2, fd_50F6_022E.x - knobSize.x / 2,
                                   fd_50F6_022E.y - knobSize.y / 2, 0x578, 0);
    } else
        hanim_SetObjectPos(fd_50F6_022E.x - knobSize.x / 2, fd_50F6_022E.y - knobSize.y / 2,
                    0x8000, fd_50F6_37F2, fd_50F6_37FA, 0x8000);
    hanim_RenderAnimSet(fd_50F6_37F2);
}

void  win_CasteControlClosed(void)
{
    if (fd_50F6_37F2) {
        hanim_RemoveAnimSet(fd_50F6_37F2);
        fd_50F6_37F2 = 0;
    }
}

extern void  f_24AB_02AD(int16_t font);
extern void  win_PrintfAtObj(int16_t obj, char  *format, ...);
extern void  f_22BF_0C38(int16_t obj);
extern void  f_1CE2_046D(struct Rect  *r, int16_t color);
extern void  f_1CE2_044D(struct Rect  *r, int16_t width);

void  DrawControlLevels(int16_t win, int16_t unused, int16_t percent)
{
    struct Rect rect;
    struct Rect r;
    char  *colors;
    uint16_t  *levels;
    int16_t h;
    int32_t total;
    int16_t w;
    int16_t i;
    int16_t obj;
    int32_t val;
    int16_t color;
    int16_t x;      /* x, y, j: unused (identifier count, see promotion --steered) */
    int16_t y;
    int16_t j;

    f_24AB_02AD(SIM_GRAPHICS_SOURCE_g_3DB2 == 0x140 ? 0 : 4);
    win_GetObjRect((win & 0xff00) + 12, &rect);
    w = (rect.right - rect.left) / 5;
    h = rect.bottom - rect.top;
    if (win == 0x1200) {
        levels = (uint16_t  *)&(*((struct TriLevel *)native_sim_state_modeLevels.raw_bytes));
        colors = g_1B4A;
        total = (int32_t)native_sim_state_fd_50F6_0B12.signed_values[2] + native_sim_state_fd_50F6_0B12.signed_values[1] + native_sim_state_fd_50F6_0B12.signed_values[0];
    } else {
        levels = (uint16_t  *)&(*((struct TriLevel *)native_sim_state_casteLevels.raw_bytes));
        colors = g_1B46;
        total = native_sim_state_fd_50F6_0AEC.signed_values[0];
    }
    for (i = 0; i < 3; i++) {
        obj = (win & 0xff00) + i + 9;
        if (percent) {
            val = (100L * levels[i] + 0x3fff) / 0xffff;
            win_PrintfAtObj(obj, "%-ld%%", val);
        } else {
            val = (levels[i] * (uint32_t)total + 0x3fff) / 0xffff;
            win_PrintfAtObj(obj, "%-ld", val);
        }
        f_22BF_0C38(obj);
        r.left = w * i * 2 + rect.left;
        r.right = r.left + w;
        r.bottom = rect.bottom;
        r.top = (int32_t)levels[i] * h / -65535L + rect.bottom;
        if (r.top + 1 < rect.bottom) {
            color = f_1B4E_000D(colors[i]);
            f_1CE2_046D(&r, color);
            (*g_9128)(f_1B4E_000D(15), f_1B4E_000D(15), 0);
            f_1CE2_044D(&r, 1);
        } else
            r.top = rect.bottom;
        r.bottom = r.top;
        r.top = rect.top - 1;
        f_1CE2_046D(&r, f_1B4E_000D(0x40));
    }
    f_24AB_02AD(0);
}

void  cvtLevels2IdealCaste(int16_t  *ideal)
{
    ideal[0] = (100UL * (&(*((struct TriLevel *)native_sim_state_casteLevels.raw_bytes)).frac)[1] + 0x3fff) / 0xffff;
    ideal[1] = (100UL * (&(*((struct TriLevel *)native_sim_state_casteLevels.raw_bytes)).frac)[2] + 0x3fff) / 0xffff;
    ideal[2] = (50UL * (&(*((struct TriLevel *)native_sim_state_casteLevels.raw_bytes)).frac)[0] + 0x3fff) / 0xffff;
    ideal[3] = (50UL * (&(*((struct TriLevel *)native_sim_state_casteLevels.raw_bytes)).frac)[0] + 0x3fff) / 0xffff;
}

void  GetTriLatDist(struct TriLevel  *level, struct TriPoints  *tri, struct Pt  *pt)
{
    int16_t dx;
    int16_t dy;
    int16_t row;
    uint16_t w;

    dx = pt->x - tri->leftX;
    dy = pt->y - tri->apexY;
    if ((uint16_t)dy > native_triangle_triHeight_v1 - 2)
        level->frac = 0;
    else
        level->frac = (int32_t)(native_triangle_triHeight_v1 - dy - 2) * 0xffffL / (int32_t)(native_triangle_triHeight_v1 - 2);
    w = (uint32_t)level->frac * native_triangle_triWidthL_v1 / 0xffffUL;
    row = native_triangle_triWidth_v1 - w * 2;
    if (row <= 2) {
        level->weight = level->mid = 0;
        return;
    }
    if (dx - (int16_t)w >= row - 2)
        level->weight = 0xffff - level->frac;
    else if (dx - (int16_t)w <= 2)
        level->weight = 0;
    else
        level->weight = (0xffffL - level->frac) * (int32_t)(dx - (int16_t)w) / (int32_t)(row - 2);
    level->mid = 0xffff - level->weight - level->frac;
}

void  SetTriLatPoint(struct TriLevel  *level, struct TriPoints  *tri, struct Pt  *out)
{
    uint16_t w;
    int16_t row;

    out->y = (native_triangle_triHeight_v1 - 2) * (0xffffUL - level->frac) / 0xffffUL + tri->apexY;
    w = (uint32_t)native_triangle_triWidthL_v1 * level->frac / 0xffffUL;
    row = native_triangle_triWidth_v1 - w * 2;
    if (level->frac == 0xffff || row < 3)
        out->x = tri->apexX + 2;
    else
        out->x = (int32_t)(row - 3) * level->weight / (int32_t)(0xffffU - level->frac) + tri->leftX + w + 2;
}

extern void  f_208F_0419(struct Pt  *size, int16_t id);
extern int16_t  fd_3D57_07EA;
extern int16_t  fd_3D57_080A[3];
extern int16_t  fd_3D57_07EC[3];

void  initControls(void)
{
    struct Rect rect;
    int16_t i;

    f_208F_0419(&knobSize, 0x578);
    win_GetObjRect(0x120d, &rect);
    native_state_ModeAuto.signed_value = 1;
    CasteAuto = 1;
    native_state_fd_50F6_0468.signed_value = 1;
    fd_3D57_07EA = 1;
    native_state_fd_50F6_0370.signed_value = -1;
    native_state_fd_50F6_024E.signed_value = -1;
    for (i = 0; i < 3; i++) {
        (&(*((struct TriLevel *)native_sim_state_modeLevels.raw_bytes)).frac)[i] = fd_3D57_080A[i];
        (&fd_3D57_0810[0].frac)[i] = fd_3D57_080A[i];
        (&(*((struct TriLevel *)native_sim_state_casteLevels.raw_bytes)).frac)[i] = fd_3D57_07EC[i];
        (&fd_3D57_07F2[0].frac)[i] = fd_3D57_07EC[i];
    }
    win_ModeControlChanged();
    win_CasteControlChanged();
    cvtLevels2IdealCaste(IdealCaste);
}

#pragma pack(pop)
