/* Generated from frozen src/root/m0798.c by extract_m0798.py. */
#include "source_control_events.h"

/* Extracted ProcCasteEvent; source lines 129-191; original-body-sha256 963e177d43be2d44d78d4717986a399b99d69b528a391e47084c790015bc3416. */
#include <stdint.h>
#include <stddef.h>


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
        _fmemcpy(&fd_3D57_07F2[g_1B4E], &casteLevels, 6);
        g_1B4E = msg->code - 0x1306;
        _fmemcpy(&casteLevels, &fd_3D57_07F2[g_1B4E], 6);
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
                GetTriLatDist(&casteLevels, &fd_50F6_3822, &msg->pt);
                win_DrawCasteWindow(3);
            }
            f_1FD2_04D0(&msg->pt);
        } while (StillDown());
        _fmemcpy(&fd_3D57_07F2[g_1B4E], &casteLevels, 6);
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

/* Extracted ProcModeEvent; source lines 197-258; original-body-sha256 fb675afb7b3dd9eb37f6b338d479517da36238883195a53fa05a431b25eebc24. */
#include <stdint.h>
#include <stddef.h>


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
        if (ModeAuto == 0) {
            ModeAuto = 1;
            win_MakeGroupInvisible(0x1200, 4);
        }
        break;
    case 3:
    case 4:
    case 5:
        win_MakeObjSelected(0x1205);
        _fmemcpy(&fd_3D57_0810[g_1B50], &modeLevels, 6);
        g_1B50 = msg->code - 0x1206;
        _fmemcpy(&modeLevels, &fd_3D57_0810[g_1B50], 6);
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
                GetTriLatDist(&modeLevels, &fd_50F6_3816, &msg->pt);
                win_DrawModeWindow(3);
            }
            f_1FD2_04D0(&msg->pt);
        } while (StillDown());
        _fmemcpy(&fd_3D57_0810[g_1B50], &modeLevels, 6);
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

/* Extracted IsPointInIsoTri; source lines 260-284; original-body-sha256 a119fab8fce93f66907a4e304284bce29c5103c78099918a1a989a49894230a7. */
#include <stdint.h>
#include <stddef.h>


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

/* Extracted BoundPointToTri; source lines 286-318; original-body-sha256 4436012b9ca61e93ca828afe99f086c4ce3ccaaed7c9c91a644ebfe4426828fe. */
#include <stdint.h>
#include <stddef.h>


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

/* Extracted cvtLevels2IdealCaste; source lines 459-465; original-body-sha256 60ad8198da395da748aae45fbcad46d05ff647ae7b9df8cda86dcd725681707a. */
#include <stdint.h>
#include <stddef.h>


void  cvtLevels2IdealCaste(int16_t  *ideal)
{
    ideal[0] = (100UL * (&casteLevels.frac)[1] + 0x3fff) / 0xffff;
    ideal[1] = (100UL * (&casteLevels.frac)[2] + 0x3fff) / 0xffff;
    ideal[2] = (50UL * (&casteLevels.frac)[0] + 0x3fff) / 0xffff;
    ideal[3] = (50UL * (&casteLevels.frac)[0] + 0x3fff) / 0xffff;
}

/* Extracted GetTriLatDist; source lines 467-493; original-body-sha256 726868fc3d68d5b221221c97a6761b775b29747ed4d0ad961cdfd7f658890aa3. */
#include <stdint.h>
#include <stddef.h>


void  GetTriLatDist(struct TriLevel  *level, struct TriPoints  *tri, struct Pt  *pt)
{
    int16_t dx;
    int16_t dy;
    int16_t row;
    uint16_t w;

    dx = pt->x - tri->leftX;
    dy = pt->y - tri->apexY;
    if ((uint16_t)dy > triHeight - 2)
        level->frac = 0;
    else
        level->frac = (int32_t)(triHeight - dy - 2) * 0xffffL / (int32_t)(triHeight - 2);
    w = (uint32_t)level->frac * triWidthL / 0xffffUL;
    row = triWidth - w * 2;
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

/* Extracted SetTriLatPoint; source lines 495-507; original-body-sha256 2e1ca1430a19c064d1a0e9fedddcf7ddac0dc4da3938864439bef66206349540. */
#include <stdint.h>
#include <stddef.h>


void  SetTriLatPoint(struct TriLevel  *level, struct TriPoints  *tri, struct Pt  *out)
{
    uint16_t w;
    int16_t row;

    out->y = (triHeight - 2) * (0xffffUL - level->frac) / 0xffffUL + tri->apexY;
    w = (uint32_t)triWidthL * level->frac / 0xffffUL;
    row = triWidth - w * 2;
    if (level->frac == 0xffff || row < 3)
        out->x = tri->apexX + 2;
    else
        out->x = (int32_t)(row - 3) * level->weight / (int32_t)(0xffffU - level->frac) + tri->leftX + w + 2;
}
